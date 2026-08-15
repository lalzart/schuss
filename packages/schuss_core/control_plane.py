"""Pure Task 008 Schuss operation dispatcher.

Repository loading is an adapter concern. Once an :class:`OperationContext`
exists, dispatch reads only its in-memory snapshot and never writes files,
invokes a compiler/backend, or accesses hardware.
"""

from __future__ import annotations

import copy
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_TOOLS = REPOSITORY_ROOT / "tools/contracts"
if str(CONTRACT_TOOLS) not in sys.path:
    sys.path.insert(0, str(CONTRACT_TOOLS))

import aggregate_validator as aggregate
import component_graph_rules as component
import device_instrument_rules as device
import record_set_rules
import target_backend_build_rules as target
import validator_core as core


REQUEST_SCHEMA_NAME = "operation-request-v1.schema.json"
RESULT_SCHEMA_NAME = "operation-result-v1.schema.json"
GRAPH_SCHEMA_NAME = component.GRAPH_SCHEMA_NAME

DOMAIN_GROUPS = (
    "families",
    "contracts",
    "bindings",
    "graphs",
    "devices",
    "instruments",
    *tuple(target.SCHEMA_SPECS),
)


def _stable_records(values: Iterable[dict[str, Any]]) -> tuple[dict[str, Any], ...]:
    return tuple(
        copy.deepcopy(item)
        for item in sorted(values, key=lambda item: core.canonical_json(item))
    )


@dataclass(frozen=True)
class OperationContext:
    """Immutable-by-contract in-memory snapshot used by every Task 008 client."""

    records: Mapping[str, tuple[dict[str, Any], ...]]
    schemas: Mapping[str, dict[str, Any]]
    overlay: dict[str, Any]
    overlay_sha256: str
    manifest_sha256: str
    observations: Mapping[str, dict[str, Any]]
    device_summary: dict[str, Any]
    component_summary: dict[str, Any]
    task006_summary: dict[str, Any]
    task007_summary: dict[str, Any]
    record_set_reference: dict[str, Any]

    def with_records(
        self, **groups: Iterable[dict[str, Any]]
    ) -> "OperationContext":
        """Return an isolated fixture context; cached summaries remain explicit inputs."""

        unknown = sorted(set(groups) - set(DOMAIN_GROUPS))
        if unknown:
            raise ValueError(f"unknown operation-context record groups {unknown}")
        updated = {
            name: _stable_records(values)
            for name, values in self.records.items()
        }
        for name, values in groups.items():
            updated[name] = _stable_records(values)
        return replace(self, records=updated)


def load_repository_context(
    repository_root: Path = REPOSITORY_ROOT,
    record_enumerator: Callable[[Path, str], Iterable[Path]] | None = None,
    record_set_path: Path = record_set_rules.ACCEPTED_RECORD_SET,
    parent_record_set_path: Path | None = None,
) -> OperationContext:
    """Read and validate one accepted repository snapshot before dispatch."""

    repository_root = repository_root.resolve()
    schema_root = repository_root / "schemas"
    contract_root = repository_root / "contracts"
    overlay_path = repository_root / component.OVERLAY_RELATIVE_PATH
    snapshot_root = repository_root / component.SNAPSHOT_RELATIVE_PATH
    manifest_path = snapshot_root / "manifest.json"

    selected = record_set_rules.load_record_set(
        repository_root,
        record_set_path,
        accepted_manifest_path=parent_record_set_path,
    )
    if record_enumerator is not None:
        known_directories = {
            member["portable_path"].split("/")[1]
            for member in selected.manifest["record_members"]
            if member["portable_path"].startswith("contracts/")
            and len(member["portable_path"].split("/")) == 3
        }
        for child in sorted(known_directories):
            actual = {
                Path(path).resolve()
                for path in record_enumerator(contract_root, child)
            }
            expected = {
                (repository_root / member["portable_path"]).resolve()
                for member in selected.manifest["record_members"]
                if member["portable_path"].startswith(f"contracts/{child}/")
            }
            if actual != expected:
                raise ValueError(
                    f"custom record enumerator changes explicit record-set membership for {child}"
                )

    records: dict[str, tuple[dict[str, Any], ...]] = {
        "families": _stable_records(selected.records.get("catalog-family", ())),
        "contracts": _stable_records(selected.records.get("component-contract", ())),
        "bindings": _stable_records(selected.records.get("implementation-binding", ())),
        "graphs": _stable_records(selected.records.get("dsp-graph", ())),
        "devices": _stable_records(selected.records.get("device-profile", ())),
        "instruments": _stable_records(selected.records.get("instrument", ())),
    }
    target_records = {
        kind: list(selected.records.get(kind, ()))
        for kind in target.SCHEMA_SPECS
    }
    records.update(
        {name: _stable_records(values) for name, values in target_records.items()}
    )

    schemas: dict[str, dict[str, Any]] = {
        "operation_request": selected.schemas["operation-request-v1"],
        "operation_result": selected.schemas["operation-result-v1"],
        "device": selected.schemas[device.DEVICE_SCHEMA_VERSION],
        "instrument": selected.schemas[device.INSTRUMENT_SCHEMA_VERSION],
        "family": selected.schemas[component.FAMILY_SCHEMA_VERSION],
        "contract": selected.schemas[component.CONTRACT_SCHEMA_VERSION],
        "binding": selected.schemas[component.BINDING_SCHEMA_VERSION],
        "graph": selected.schemas[component.GRAPH_SCHEMA_VERSION],
        **{
            kind: selected.schemas[specification[1]]
            for kind, specification in target.SCHEMA_SPECS.items()
        },
    }

    overlay = core.load_json(overlay_path)
    observations = component._observations(snapshot_root)
    component_result = component.validate_component_graph_values(
        list(records["families"]),
        list(records["contracts"]),
        list(records["bindings"]),
        list(records["graphs"]),
        {kind: schemas[kind] for kind in ("family", "contract", "binding", "graph")},
        overlay,
        core.sha256_file(overlay_path),
        core.sha256_file(manifest_path),
        observations,
    )
    device_summary = device.validate_contract_values(
        list(records["devices"]),
        list(records["instruments"]),
        schemas["device"],
        schemas["instrument"],
        component_result.graph_targets,
    )
    task006_summary = aggregate.combine_task006_summaries(
        component_result.summary,
        device_summary,
        len(records["devices"]),
        len(records["instruments"]),
    )
    task007_result = target.validate_target_backend_build_values(
        {kind: list(records[kind]) for kind in target.SCHEMA_SPECS},
        {kind: schemas[kind] for kind in target.SCHEMA_SPECS},
        {
            "families": list(records["families"]),
            "contracts": list(records["contracts"]),
            "bindings": list(records["bindings"]),
            "graphs": list(records["graphs"]),
            "devices": list(records["devices"]),
            "instruments": list(records["instruments"]),
        },
        repository_root,
        task006_summary,
        additional_semantic_records=[
            copy.deepcopy(record)
            for kind in (
                "conformance-probe-evidence",
                "conformance-probe-input",
                "conformance-probe-result",
                "conformance-probe-procedure",
                "prerequisite-environment",
            )
            for record in selected.records.get(kind, ())
        ],
    )

    return OperationContext(
        records=records,
        schemas=schemas,
        overlay=overlay,
        overlay_sha256=core.sha256_file(overlay_path),
        manifest_sha256=core.sha256_file(manifest_path),
        observations=observations,
        device_summary=copy.deepcopy(device_summary),
        component_summary=copy.deepcopy(component_result.summary),
        task006_summary=copy.deepcopy(task006_summary),
        task007_summary=copy.deepcopy(task007_result.summary),
        record_set_reference=copy.deepcopy(selected.reference),
    )


def _diagnostic(
    code: str,
    subject: str,
    location: str,
    message: str,
) -> dict[str, str]:
    return core.Diagnostic(code, "error", subject, location, message).as_dict()


def _result(
    operation: str,
    status: str,
    value: dict[str, Any] | None,
    diagnostics: Iterable[dict[str, str] | core.Diagnostic] = (),
) -> dict[str, Any]:
    normalized = [
        item.as_dict() if isinstance(item, core.Diagnostic) else copy.deepcopy(item)
        for item in diagnostics
    ]
    normalized.sort(key=core.diagnostic_sort_key)
    return {
        "schema_version": "schuss-operation-result-v1",
        "canonical_profile": "schuss-canonical-json-v1",
        "operation": operation,
        "status": status,
        "value": copy.deepcopy(value),
        "diagnostics": normalized,
    }


def canonical_result_bytes(
    result: dict[str, Any], context: OperationContext
) -> bytes:
    errors = core.schema_errors(
        result,
        context.schemas["operation_result"],
        context.schemas["operation_result"],
    )
    if errors:
        raise ValueError(f"operation result violates its public schema: {errors}")
    return core.canonical_json(result).encode("utf-8")


def _exact_registry(
    values: Iterable[dict[str, Any]], id_field: str
) -> dict[tuple[str, int, str], dict[str, Any]]:
    return {
        core.exact_key(item, id_field): item
        for item in sorted(values, key=lambda item: core.canonical_json(item))
    }


def _records_validate(context: OperationContext) -> dict[str, Any]:
    summaries = {
        "device_instrument_rules": copy.deepcopy(context.device_summary),
        "component_graph_rules": copy.deepcopy(context.component_summary),
        "target_backend_build_rules": copy.deepcopy(context.task007_summary),
        "aggregate_validator": copy.deepcopy(context.task006_summary),
    }
    invalid = any(
        summary.get("status") == "invalid" for summary in summaries.values()
    )
    diagnostics: list[dict[str, str]] = []
    for summary in summaries.values():
        diagnostics.extend(summary.get("diagnostics", []))
    return _result(
        "records.validate",
        "invalid" if invalid else "success",
        {"summaries": summaries},
        diagnostics,
    )


def _graph_inspect(payload: dict[str, Any], context: OperationContext) -> dict[str, Any]:
    graph_ref = payload["graph_reference"]
    graphs = _exact_registry(context.records["graphs"], "graph_id")
    graph = graphs.get(core.reference_key(graph_ref, "graph_id"))
    if graph is None:
        return _result(
            "graph.inspect",
            "invalid",
            None,
            [
                _diagnostic(
                    "OPERATION_REFERENCE_UNRESOLVED",
                    f"{graph_ref['graph_id']}@{graph_ref['revision']}",
                    "$.payload.graph_reference",
                    "the exact graph reference is absent from the operation context",
                )
            ],
        )

    contracts = _exact_registry(
        context.records["contracts"], "component_contract_id"
    )
    closure: list[dict[str, Any]] = []
    diagnostics: list[dict[str, str]] = []
    for node in sorted(graph["nodes"], key=lambda item: item["node_id"]):
        reference = node["contract_reference"]
        contract = contracts.get(
            core.reference_key(reference, "component_contract_id")
        )
        if contract is None:
            diagnostics.append(
                _diagnostic(
                    "OPERATION_REFERENCE_UNRESOLVED",
                    f"{graph['graph_id']}@{graph['revision']}",
                    f"$.nodes.{node['node_id']}.contract_reference",
                    "the node's exact component contract is absent",
                )
            )
        else:
            closure.append(copy.deepcopy(contract))
    if diagnostics:
        return _result("graph.inspect", "invalid", None, diagnostics)

    unique_contracts = {
        core.exact_key(item, "component_contract_id"): item for item in closure
    }
    value = {
        "graph": copy.deepcopy(graph),
        "component_contract_closure": [
            copy.deepcopy(unique_contracts[key]) for key in sorted(unique_contracts)
        ],
        "selection_status": "not-evaluated",
        "lowering_status": "not-run",
    }
    return _result("graph.inspect", "success", value)


def _validate_build_resolution_context(
    context: OperationContext,
) -> tuple[
    dict[str, list[dict[str, Any]]],
    dict[str, dict[tuple[str, int, str], dict[str, Any]]],
    dict[str, dict[str, Any]],
    tuple[core.Diagnostic, ...],
]:
    loaded = {
        kind: [copy.deepcopy(item) for item in context.records[kind]]
        for kind in target.SCHEMA_SPECS
    }
    diagnostics: list[core.Diagnostic] = []
    target_schemas = {
        kind: context.schemas[kind] for kind in target.SCHEMA_SPECS
    }
    valid = target._validate_structural(loaded, target_schemas, diagnostics)

    contracts = _exact_registry(
        context.records["contracts"], "component_contract_id"
    )
    bindings = _exact_registry(context.records["bindings"], "implementation_id")
    graphs = _exact_registry(context.records["graphs"], "graph_id")
    instruments = _exact_registry(context.records["instruments"], "instrument_id")
    capability_registry, definitions = target._capability_definitions(
        valid["capability"], diagnostics
    )
    environments = target._validate_environments(valid["environment"], diagnostics)
    targets = target._validate_targets(
        valid["target"],
        capability_registry,
        definitions,
        environments,
        diagnostics,
    )
    backends = target._validate_backends(
        valid["backend"],
        capability_registry,
        definitions,
        targets,
        environments,
        diagnostics,
    )
    evidence = _exact_registry(valid["evidence"], "evidence_claim_id")
    eligibility = target._validate_eligibility_records(
        valid["eligibility"],
        bindings,
        contracts,
        targets,
        backends,
        definitions,
        evidence,
        diagnostics,
    )
    requests = target._validate_build_requests(
        valid["request"],
        graphs,
        instruments,
        targets,
        backends,
        diagnostics,
    )
    registries = {
        "bindings": bindings,
        "graphs": graphs,
        "targets": targets,
        "backends": backends,
        "eligibility": eligibility,
        "requests": requests,
    }
    ordered = tuple(sorted(set(diagnostics), key=core.diagnostic_sort_key))
    return valid, registries, definitions, ordered


def _prepare_backend_invocation(
    request: dict[str, Any], traces: tuple[dict[str, Any], ...]
) -> dict[str, Any]:
    """Create the Task 009 data seam; no executable handler exists here."""

    return {
        "schema_version": "schuss-backend-invocation-input-v1",
        "status": "ready-for-backend-invocation",
        "accepted_build_request": copy.deepcopy(request),
        "resolution_traces": copy.deepcopy(list(traces)),
        "selected_bindings": [
            {
                "node_id": trace["node_id"],
                "binding_reference": copy.deepcopy(
                    trace["selected_binding_reference"]
                ),
            }
            for trace in traces
        ],
        "boundary": {
            "completed_stage": "implementation-resolution",
            "next_stage": "backend-lowering",
            "next_stage_status": "not-run",
            "executable_handler_status": "absent",
        },
    }


def _build_resolve(payload: dict[str, Any], context: OperationContext) -> dict[str, Any]:
    _, registries, definitions, diagnostics = _validate_build_resolution_context(
        context
    )
    request_ref = payload["build_request_reference"]
    request = registries["requests"].get(
        core.reference_key(request_ref, "build_request_id")
    )
    if diagnostics or request is None:
        values = list(diagnostics)
        if request is None:
            values.append(
                core.Diagnostic(
                    "OPERATION_REFERENCE_UNRESOLVED",
                    f"{request_ref['build_request_id']}@{request_ref['revision']}",
                    "$.payload.build_request_reference",
                    "the exact accepted build request is absent",
                )
            )
        return _result("build.resolve", "invalid", None, values)

    graph = registries["graphs"][
        core.reference_key(request["graph_reference"], "graph_id")
    ]
    target_record = registries["targets"][
        core.reference_key(request["compute_target_reference"], "compute_target_id")
    ]
    backend = registries["backends"][
        core.reference_key(request["backend_reference"], "backend_id")
    ]
    graph_for_resolution = copy.deepcopy(graph)
    graph_for_resolution["nodes"] = sorted(
        graph_for_resolution["nodes"], key=lambda item: item["node_id"]
    )
    traces = target.resolve_graph_bindings(
        graph_for_resolution,
        target_record,
        backend,
        registries["eligibility"].values(),
        registries["bindings"],
        definitions,
        request["binding_overrides"],
    )
    statuses = {trace["status"] for trace in traces}
    if statuses == {"selected"}:
        status = "success"
    elif "invalid-override" in statuses:
        status = "invalid"
    elif "ambiguous" in statuses:
        status = "ambiguous"
    elif "unresolved" in statuses:
        status = "unresolved"
    else:
        status = "unsupported"

    value = {
        "build_request_reference": copy.deepcopy(request_ref),
        "resolution_traces": copy.deepcopy(list(traces)),
        "backend_invocation": (
            _prepare_backend_invocation(request, traces)
            if status == "success"
            else None
        ),
    }
    return _result("build.resolve", status, value)


class _TransactionEditError(ValueError):
    pass


def _find_unique(
    values: list[dict[str, Any]], field: str, identifier: str
) -> dict[str, Any]:
    matches = [item for item in values if item.get(field) == identifier]
    if len(matches) != 1:
        raise _TransactionEditError(
            f"expected exactly one {field}={identifier!r}, found {len(matches)}"
        )
    return matches[0]


def _apply_edit(graph: dict[str, Any], edit: dict[str, Any]) -> None:
    kind = edit["edit"]
    if kind == "add-node":
        identifier = edit["node"]["node_id"]
        if any(item["node_id"] == identifier for item in graph["nodes"]):
            raise _TransactionEditError(f"node {identifier!r} already exists")
        graph["nodes"].append(copy.deepcopy(edit["node"]))
    elif kind == "remove-node":
        node = _find_unique(graph["nodes"], "node_id", edit["node_id"])
        graph["nodes"].remove(node)
    elif kind == "add-connection":
        identifier = edit["connection"]["connection_id"]
        if any(
            item["connection_id"] == identifier for item in graph["connections"]
        ):
            raise _TransactionEditError(f"connection {identifier!r} already exists")
        graph["connections"].append(copy.deepcopy(edit["connection"]))
    elif kind == "remove-connection":
        connection = _find_unique(
            graph["connections"], "connection_id", edit["connection_id"]
        )
        graph["connections"].remove(connection)
    elif kind in {"set-node-parameter", "set-node-attribute"}:
        node = _find_unique(graph["nodes"], "node_id", edit["node_id"])
        values_key = (
            "parameter_values"
            if kind == "set-node-parameter"
            else "attribute_values"
        )
        values = node[values_key]
        matches = [item for item in values if item["facet_id"] == edit["facet_id"]]
        if len(matches) > 1:
            raise _TransactionEditError(
                f"facet {edit['facet_id']!r} is not unique on node {edit['node_id']!r}"
            )
        replacement = {"facet_id": edit["facet_id"], "value": edit["value"]}
        if matches:
            values[values.index(matches[0])] = replacement
        else:
            values.append(replacement)
    else:
        raise _TransactionEditError(f"unsupported graph edit {kind!r}")


def _validate_transacted_graph(
    candidate: dict[str, Any], context: OperationContext
) -> tuple[component.CoreValidation, dict[str, Any]]:
    graphs = [copy.deepcopy(item) for item in context.records["graphs"]]
    graphs.append(copy.deepcopy(candidate))
    component_result = component.validate_component_graph_values(
        list(copy.deepcopy(context.records["families"])),
        list(copy.deepcopy(context.records["contracts"])),
        list(copy.deepcopy(context.records["bindings"])),
        graphs,
        {
            "family": context.schemas["family"],
            "contract": context.schemas["contract"],
            "binding": context.schemas["binding"],
            "graph": context.schemas["graph"],
        },
        copy.deepcopy(context.overlay),
        context.overlay_sha256,
        context.manifest_sha256,
        copy.deepcopy(dict(context.observations)),
    )
    device_summary = device.validate_contract_values(
        list(copy.deepcopy(context.records["devices"])),
        list(copy.deepcopy(context.records["instruments"])),
        context.schemas["device"],
        context.schemas["instrument"],
        component_result.graph_targets,
    )
    return component_result, device_summary


def _graph_transact(payload: dict[str, Any], context: OperationContext) -> dict[str, Any]:
    graph_ref = payload["graph_reference"]
    graph = _exact_registry(context.records["graphs"], "graph_id").get(
        core.reference_key(graph_ref, "graph_id")
    )
    if graph is None or payload["base_content_hash"] != graph.get("content_hash"):
        return _result(
            "graph.transact",
            "conflict",
            None,
            [
                _diagnostic(
                    "OPERATION_BASE_HASH_STALE",
                    f"{graph_ref['graph_id']}@{graph_ref['revision']}",
                    "$.payload.base_content_hash",
                    "the transaction base does not match the exact current graph",
                )
            ],
        )

    candidate = copy.deepcopy(graph)
    try:
        for index, edit in enumerate(payload["edits"]):
            try:
                _apply_edit(candidate, edit)
            except _TransactionEditError as exc:
                raise _TransactionEditError(f"edit {index}: {exc}") from exc
    except _TransactionEditError as exc:
        return _result(
            "graph.transact",
            "invalid",
            None,
            [
                _diagnostic(
                    "OPERATION_EDIT_INVALID",
                    f"{graph_ref['graph_id']}@{graph_ref['revision']}",
                    "$.payload.edits",
                    str(exc),
                )
            ],
        )

    candidate["revision"] = graph["revision"] + 1
    candidate["content_hash"] = core.record_content_hash(
        candidate, context.schemas["graph"]
    )
    component_result, device_summary = _validate_transacted_graph(candidate, context)
    diagnostics = list(component_result.summary["diagnostics"]) + list(
        device_summary["diagnostics"]
    )
    if diagnostics:
        return _result(
            "graph.transact",
            "invalid",
            None,
            diagnostics,
        )
    return _result(
        "graph.transact",
        "success",
        {
            "proposed_graph": candidate,
            "validation": {
                "component_graph": component_result.summary,
                "device_instrument": device_summary,
            },
            "persistence_status": "not-written",
        },
    )


def dispatch_operation(
    request: dict[str, Any], context: OperationContext
) -> dict[str, Any]:
    """Dispatch one parsed request through the public pure operation API."""

    operation = request.get("operation") if isinstance(request, dict) else None
    request_errors: list[str] = []
    try:
        core.assert_portable_json_value(request)
    except ValueError as exc:
        request_errors.append(str(exc))
    if isinstance(request, dict):
        request_errors.extend(
            core.schema_errors(
                request,
                context.schemas["operation_request"],
                context.schemas["operation_request"],
            )
        )
    else:
        request_errors.append("$: operation request must be an object")
    if request_errors:
        subject = operation if isinstance(operation, str) else "invalid-request"
        return _result(
            operation if operation in {
                "records.validate",
                "graph.inspect",
                "build.resolve",
                "graph.transact",
            } else "invalid-request",
            "invalid",
            None,
            [
                _diagnostic(
                    "OPERATION_REQUEST_INVALID",
                    subject,
                    "$",
                    error,
                )
                for error in sorted(set(request_errors))
            ],
        )

    handlers = {
        "records.validate": lambda payload: _records_validate(context),
        "graph.inspect": lambda payload: _graph_inspect(payload, context),
        "build.resolve": lambda payload: _build_resolve(payload, context),
        "graph.transact": lambda payload: _graph_transact(payload, context),
    }
    result = handlers[operation](request["payload"])
    canonical_result_bytes(result, context)
    return result
