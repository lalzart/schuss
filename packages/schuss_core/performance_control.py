"""Read-only Task 034 performance-control inspection operation."""

from __future__ import annotations

import copy
from typing import Any, Mapping

from .control_plane import OperationContext, canonical_result_bytes, core


def _diagnostic(code: str, subject: str, message: str) -> dict[str, str]:
    return {
        "code": code,
        "severity": "error",
        "subject": subject,
        "location": "$.payload",
        "message": message,
    }


def _result(
    operation: str,
    status: str,
    value: dict[str, Any] | None,
    diagnostics: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "schuss-operation-result-v17",
        "canonical_profile": "schuss-canonical-json-v1",
        "operation": operation,
        "status": status,
        "value": copy.deepcopy(value),
        "diagnostics": sorted(diagnostics or [], key=core.diagnostic_sort_key),
    }


def _exact(
    records: tuple[dict[str, Any], ...],
    reference: Mapping[str, Any],
    id_field: str,
) -> dict[str, Any]:
    matches = [
        record
        for record in records
        if record[id_field] == reference[id_field]
        and record["revision"] == reference["revision"]
        and record["content_hash"] == reference["content_hash"]
    ]
    if len(matches) != 1:
        raise ValueError(
            f"exact {id_field} reference must resolve exactly once"
        )
    return matches[0]


def inspect_performance_configuration(
    context: OperationContext, reference: Mapping[str, Any]
) -> dict[str, Any]:
    """Return the complete exact semantic closure for one configuration."""

    configuration = _exact(
        context.records["performance_configurations"],
        reference,
        "performance_configuration_id",
    )
    graph = _exact(
        context.records["performance_control_graphs"],
        configuration["performance_control_graph_reference"],
        "performance_control_graph_id",
    )
    instrument = _exact(
        context.records["performance_instruments"],
        configuration["instrument_reference"],
        "instrument_id",
    )
    dsp_graph = _exact(
        context.records["graphs"], instrument["graph_reference"], "graph_id"
    )
    contract_references = {
        (
            node["contract_reference"]["performance_control_contract_id"],
            node["contract_reference"]["revision"],
            node["contract_reference"]["content_hash"],
        ): node["contract_reference"]
        for node in graph["nodes"]
    }
    contracts = [
        _exact(
            context.records["performance_control_contracts"],
            contract_references[key],
            "performance_control_contract_id",
        )
        for key in sorted(contract_references)
    ]
    device_references = {
        (
            source["device_profile_reference"]["device_profile_id"],
            source["device_profile_reference"]["revision"],
            source["device_profile_reference"]["content_hash"],
        ): source["device_profile_reference"]
        for source in configuration["controller_sources"]
        if source["source_kind"] == "device-profile"
    }
    devices = [
        _exact(context.records["devices"], device_references[key], "device_profile_id")
        for key in sorted(device_references)
    ]
    return {
        "configuration": copy.deepcopy(configuration),
        "resolved_controller_device_profiles": copy.deepcopy(devices),
        "performance_control_graph": copy.deepcopy(graph),
        "performance_control_contracts": copy.deepcopy(contracts),
        "instrument": copy.deepcopy(instrument),
        "dsp_graph": copy.deepcopy(dsp_graph),
        "boundary_summary": {
            "controller_bindings_owner": "performance-configuration",
            "performance_graph_references_dsp_nodes": False,
            "instrument_references_device_profile": False,
            "authoritative_dsp_owner": "instrument-exact-graph-reference",
            "control_graph_execution": "not-run",
            "backend_lowering": "not-run",
            "physical_controller": "not-run",
            "audible_listening": "not-run",
        },
        "validation_summary": copy.deepcopy(context.performance_summary),
    }


def dispatch_performance_operation(
    request: dict[str, Any], context: OperationContext
) -> dict[str, Any]:
    """Validate and dispatch the read-only Task 034 operation."""

    request_schema = context.schemas.get("operation_request_v17")
    result_schema = context.schemas.get("operation_result_v17")
    operation = request.get("operation") if isinstance(request, dict) else None
    if request_schema is None or result_schema is None:
        raise ValueError("Task 034 operation schemas are unavailable")
    errors: list[str] = []
    try:
        core.assert_portable_json_value(request)
    except ValueError as error:
        errors.append(str(error))
    errors.extend(core.schema_errors(request, request_schema, request_schema))
    if errors:
        result = _result(
            "performance.inspect" if operation == "performance.inspect" else "invalid-request",
            "invalid",
            None,
            [
                _diagnostic(
                    "OPERATION_REQUEST_INVALID",
                    str(operation or "invalid-request"),
                    error,
                )
                for error in sorted(set(errors))
            ],
        )
        canonical_result_bytes(result, context)
        return result
    try:
        value = inspect_performance_configuration(
            context, request["payload"]["performance_configuration_reference"]
        )
        result = _result("performance.inspect", "success", value)
    except ValueError as error:
        result = _result(
            "performance.inspect",
            "invalid",
            None,
            [
                _diagnostic(
                    "PERFORMANCE_CONFIGURATION_REFERENCE_UNRESOLVED",
                    "performance.inspect",
                    str(error),
                )
            ],
        )
    canonical_result_bytes(result, context)
    return result
