#!/usr/bin/env python3
"""Task 011B exact closure and fail-closed operation rules."""

from __future__ import annotations

import copy
import hashlib
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

import component_graph_rules as component
import record_set_rules
import validator_core as core


GRAPH_ID = "schuss-graph-000002"
INSTRUMENT_ID = "schuss-instrument-000002"
REQUEST_ID = "schuss-build-request-000002"
PROCEDURE_ID = "schuss-procedure-000002"
MANIFEST_PATH = Path("contracts/record-sets/task011b-vertical-slice-v1.json")
PARENT_PATH = Path("contracts/record-sets/task011a-catalog-v1.json")

CONTRACT_IDS = {
    "lfo": "schuss-component-contract-000004",
    "counter": "schuss-component-contract-000005",
    "sequencer": "schuss-component-contract-000006",
    "sine": "schuss-component-contract-000007",
    "filter": "schuss-component-contract-000008",
    "output": "schuss-component-contract-000009",
}
BINDING_IDS = {
    "lfo": "schuss-implementation-000039",
    "counter": "schuss-implementation-000040",
    "sequencer": "schuss-implementation-000041",
    "sine": "schuss-implementation-000007",
    "filter": "schuss-implementation-000015",
    "output": "schuss-implementation-000004",
}
OBSERVATION_VARIANTS = {
    "lfo": 209,
    "counter": 215,
    "sequencer": 918,
    "sine": 549,
    "filter": 159,
    "output": 9,
}
NODE_CONTRACTS = {
    "graph-node-000001": CONTRACT_IDS["lfo"],
    "graph-node-000002": CONTRACT_IDS["counter"],
    "graph-node-000003": CONTRACT_IDS["sequencer"],
    "graph-node-000004": CONTRACT_IDS["sine"],
    "graph-node-000005": CONTRACT_IDS["sine"],
    "graph-node-000006": "schuss-component-contract-000003",
    "graph-node-000007": CONTRACT_IDS["filter"],
    "graph-node-000008": CONTRACT_IDS["output"],
}
CONNECTIONS = {
    ("graph-node-000001", "component-port-000003", "graph-node-000002", "component-port-000001"),
    ("graph-node-000002", "component-port-000003", "graph-node-000003", "component-port-000001"),
    ("graph-node-000003", "component-port-000003", "graph-node-000004", "component-port-000001"),
    ("graph-node-000003", "component-port-000003", "graph-node-000005", "component-port-000001"),
    ("graph-node-000004", "component-port-000004", "graph-node-000006", "component-port-000001"),
    ("graph-node-000005", "component-port-000004", "graph-node-000006", "component-port-000002"),
    ("graph-node-000006", "component-port-000004", "graph-node-000007", "component-port-000001"),
    ("graph-node-000007", "component-port-000006", "graph-node-000008", "component-port-000001"),
    ("graph-node-000007", "component-port-000006", "graph-node-000008", "component-port-000002"),
}
FIXED_VALUES = {
    "graph-node-000001": {"component-parameter-000001": "-48"},
    "graph-node-000002": {"component-parameter-000001": "4"},
    "graph-node-000003": {
        "component-parameter-000001": "0",
        "component-parameter-000002": "5",
        "component-parameter-000003": "7",
        "component-parameter-000004": "12",
    },
    "graph-node-000004": {"component-parameter-000001": "-24"},
    "graph-node-000005": {"component-parameter-000001": "-23.875"},
    "graph-node-000006": {},
    "graph-node-000007": {
        "component-parameter-000001": "24",
        "component-parameter-000002": "0.125",
    },
    "graph-node-000008": {},
}
BEHAVIOR_KINDS = {
    CONTRACT_IDS["lfo"]: Counter(
        {"parameter-input-sum": 1, "edge-triggered-transition": 1}
    ),
    CONTRACT_IDS["counter"]: Counter({"bounded-cyclic-counter": 1}),
    CONTRACT_IDS["sequencer"]: Counter({"indexed-parameter-selection": 1}),
    CONTRACT_IDS["sine"]: Counter({"parameter-input-sum": 1}),
    CONTRACT_IDS["filter"]: Counter({"parameter-input-sum": 2}),
    CONTRACT_IDS["output"]: Counter(),
}


def _add(
    diagnostics: list[core.Diagnostic], code: str, subject: str, location: str, message: str
) -> None:
    core.add_diagnostic(diagnostics, code, subject, location, message)


def _only(records: Iterable[dict[str, Any]], field: str, value: str) -> dict[str, Any] | None:
    matches = [record for record in records if record.get(field) == value]
    return matches[0] if len(matches) == 1 else None


def _ref(record: dict[str, Any], id_field: str) -> dict[str, Any]:
    return {
        id_field: record[id_field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def validate_graph_shape(
    graph: dict[str, Any], contracts: dict[str, dict[str, Any]]
) -> list[core.Diagnostic]:
    """Validate the exact Task 011B topology and adapter decisions in memory."""

    diagnostics: list[core.Diagnostic] = []
    subject = f"{graph.get('graph_id', '<unknown>')}@{graph.get('revision', '?')}"
    nodes = {item["node_id"]: item for item in graph.get("nodes", [])}
    actual_node_contracts = {
        node_id: node["contract_reference"]["component_contract_id"]
        for node_id, node in nodes.items()
    }
    if actual_node_contracts != NODE_CONTRACTS:
        _add(
            diagnostics,
            "TASK011B_TOPOLOGY_NODE_SET_MISMATCH",
            subject,
            "$.nodes",
            "the vertical-slice graph must contain exactly the reviewed eight-node contract map",
        )
    actual_connections = {
        (
            item["source"]["node_id"],
            item["source"]["facet_id"],
            item["destination"]["node_id"],
            item["destination"]["facet_id"],
        )
        for item in graph.get("connections", [])
    }
    if actual_connections != CONNECTIONS:
        _add(
            diagnostics,
            "TASK011B_TOPOLOGY_CONNECTION_SET_MISMATCH",
            subject,
            "$.connections",
            "the vertical-slice graph must contain exactly the reviewed nine connections",
        )
    actual_values = {
        node_id: {
            item["facet_id"]: item["value"]
            for item in node.get("parameter_values", [])
        }
        for node_id, node in nodes.items()
    }
    if actual_values != FIXED_VALUES:
        _add(
            diagnostics,
            "TASK011B_FIXED_VALUES_MISMATCH",
            subject,
            "$.nodes",
            "the vertical-slice fixed values differ from the reviewed Task 011B values",
        )
    if len(graph.get("public_parameters", [])) != 1 or graph["public_parameters"][0].get(
        "semantic_key"
    ) != "blend":
        _add(
            diagnostics,
            "TASK011B_BLEND_INTERFACE_MISMATCH",
            subject,
            "$.public_parameters",
            "the graph must expose exactly one normalized blend parameter",
        )
    bindings = graph.get("parameter_bindings", [])
    if len(bindings) != 1 or bindings[0].get("destination") != {
        "node_id": "graph-node-000006",
        "facet_kind": "port",
        "facet_id": "component-port-000003",
    }:
        _add(
            diagnostics,
            "TASK011B_BLEND_BINDING_MISMATCH",
            subject,
            "$.parameter_bindings",
            "graph blend must bind directly to the accepted mixed Crossfader fade inlet",
        )

    for identifier, expected in BEHAVIOR_KINDS.items():
        contract = contracts.get(identifier)
        actual = Counter(
            item["kind"] for item in contract.get("behavior_rules", [])
        ) if contract else Counter()
        if actual != expected:
            _add(
                diagnostics,
                "TASK011B_BEHAVIOR_RULE_SET_MISMATCH",
                f"{identifier}@1",
                "$.behavior_rules",
                "the contract behavior-rule kinds differ from the reviewed closure",
            )

    lfo = contracts.get(CONTRACT_IDS["lfo"])
    counter = contracts.get(CONTRACT_IDS["counter"])
    filter_contract = contracts.get(CONTRACT_IDS["filter"])
    output = contracts.get(CONTRACT_IDS["output"])
    if lfo and counter:
        lfo_clock = next(
            item for item in lfo["ports"] if item["facet_id"] == "component-port-000003"
        )
        counter_trigger = next(
            item
            for item in counter["ports"]
            if item["facet_id"] == "component-port-000001"
        )
        mismatches = component._port_type_mismatches(lfo_clock, counter_trigger)
        if mismatches:
            _add(
                diagnostics,
                "TASK011B_CLOCK_ADAPTER_REQUIRED",
                subject,
                "$.connections",
                "square clock transport is not exact: " + ",".join(mismatches),
            )
    if filter_contract and output:
        low_pass = next(
            item
            for item in filter_contract["ports"]
            if item["facet_id"] == "component-port-000006"
        )
        output_left = next(
            item
            for item in output["ports"]
            if item["facet_id"] == "component-port-000001"
        )
        mismatches = component._port_type_mismatches(low_pass, output_left)
        maximum = low_pass["port_type"]["cardinality"]["maximum_connections"]
        if mismatches or maximum != 2:
            _add(
                diagnostics,
                "TASK011B_MONO_STEREO_ADAPTER_REQUIRED",
                subject,
                "$.connections",
                "low-pass transport or two-consumer cardinality is not exact",
            )
    return sorted(
        set(diagnostics),
        key=lambda item: (item.severity, item.code, item.subject, item.location, item.message),
    )


def validate_task011b(
    repository_root: Path,
    manifest_path: Path = MANIFEST_PATH,
) -> dict[str, Any]:
    """Load the exact successor view and validate the Task 011B closure."""

    from packages.schuss_core.control_plane import (
        canonical_result_bytes,
        dispatch_operation,
        load_repository_context,
    )

    repository_root = repository_root.resolve()
    selected = record_set_rules.load_record_set(
        repository_root,
        manifest_path,
        accepted_manifest_path=PARENT_PATH,
    )
    context = load_repository_context(
        repository_root,
        record_set_path=manifest_path,
    )
    diagnostics: list[core.Diagnostic] = []
    if context.component_summary["status"] != "valid":
        _add(diagnostics, "TASK011B_COMPONENT_CONTEXT_INVALID", GRAPH_ID, "$", "mixed-version component/graph validation failed")
    if context.task007_summary["status"] != "valid":
        _add(diagnostics, "TASK011B_BUILD_CONTEXT_INVALID", REQUEST_ID, "$", "target/backend/build validation failed")

    graph = _only(context.records["graphs"], "graph_id", GRAPH_ID)
    instrument = _only(context.records["instruments"], "instrument_id", INSTRUMENT_ID)
    request = _only(context.records["request"], "build_request_id", REQUEST_ID)
    procedure = _only(
        selected.records["conformance-probe-procedure"], "procedure_id", PROCEDURE_ID
    )
    if graph is None or instrument is None or request is None or procedure is None:
        _add(diagnostics, "TASK011B_RECORD_CLOSURE_INCOMPLETE", "schuss-record-set-000005@1", "$.record_members", "graph, instrument, request, or procedure is missing or ambiguous")
        graph = graph or {}
    contracts = {
        item["component_contract_id"]: item for item in context.records["contracts"]
    }
    diagnostics.extend(validate_graph_shape(graph, contracts))

    new_bindings = {
        item["implementation_id"]: item
        for item in context.records["bindings"]
        if item["implementation_id"] in set(BINDING_IDS.values())
        and item["schema_version"] == "implementation-binding-v1"
    }
    for role, identifier in BINDING_IDS.items():
        binding = new_bindings.get(identifier)
        if (
            binding is None
            or binding["contract_reference"]["component_contract_id"] != CONTRACT_IDS[role]
            or binding["realization"]["observation"]["variant_index"]
            != OBSERVATION_VARIANTS[role]
        ):
            _add(diagnostics, "TASK011B_BINDING_CLOSURE_MISMATCH", identifier, "$", "binding identity, contract, or frozen observation differs from the reviewed closure")

    if instrument is not None:
        expected_graph_ref = {"status": "resolved", **_ref(graph, "graph_id")}
        if instrument["graph_reference"] != expected_graph_ref:
            _add(diagnostics, "TASK011B_INSTRUMENT_GRAPH_MISMATCH", INSTRUMENT_ID, "$.graph_reference", "instrument does not resolve the exact Task 011B graph")
        graph_mappings = instrument.get("graph_mappings", [])
        if len(graph_mappings) != 1 or graph_mappings[0]["destination"].get("facet_id") != "graph-facet-000001":
            _add(diagnostics, "TASK011B_INSTRUMENT_BLEND_MISMATCH", INSTRUMENT_ID, "$.graph_mappings", "instrument blend does not map to graph blend")
    if request is not None and (
        request["requested_stopping_stage"] != "artifact-generation"
        or request["graph_reference"] != _ref(graph, "graph_id")
        or request["instrument_reference"].get("instrument_id") != INSTRUMENT_ID
    ):
        _add(diagnostics, "TASK011B_BUILD_REQUEST_MISMATCH", REQUEST_ID, "$", "build request differs from the exact non-executable closure")

    eligibilities = [
        item for item in context.records["eligibility"]
        if item["binding_eligibility_id"] in {f"schuss-binding-eligibility-{number:06d}" for number in range(2, 8)}
    ]
    if len(eligibilities) != 6 or any(
        item["allowed_pair"]["state"]["status"] not in {"unsupported", "not-evaluated", "unresolved"}
        or item["compatibility_evidence"]
        for item in eligibilities
    ):
        _add(diagnostics, "TASK011B_ELIGIBILITY_PROMOTION_PROHIBITED", REQUEST_ID, "$.eligibility", "every new binding must remain unsupported or unresolved without compatibility evidence")

    probes = [
        item for item in selected.records["conformance-probe-input"]
        if item["conformance_probe_id"] in {f"schuss-conformance-probe-{number:06d}" for number in range(3, 9)}
    ]
    if len(probes) != 6 or any(
        item["execution_authorization"] != "not-authorized"
        or item["production_selection_authority"]
        or item["graph_reference"] != _ref(graph, "graph_id")
        or item["binding_reference"]["implementation_id"] not in set(BINDING_IDS.values())
        for item in probes
    ):
        _add(diagnostics, "TASK011B_PROBE_AUTHORITY_INVALID", PROCEDURE_ID, "$", "probe closure must name only the six new bindings and remain not authorized")
    if procedure is not None and procedure["production_selection_authority"]:
        _add(diagnostics, "TASK011B_PROBE_AUTHORITY_INVALID", PROCEDURE_ID, "$.production_selection_authority", "probe procedure cannot grant production selection authority")

    task_members = [
        item for item in selected.manifest["record_members"]
        if item["portable_path"].startswith("contracts/task011b/")
    ]
    task_counts = Counter(item["record_kind"] for item in task_members)
    expected_counts = Counter(
        {
            "component-contract": 6,
            "implementation-binding": 6,
            "eligibility": 6,
            "conformance-probe-input": 6,
            "dsp-graph": 1,
            "instrument": 1,
            "request": 1,
            "conformance-probe-procedure": 1,
        }
    )
    if task_counts != expected_counts:
        _add(diagnostics, "TASK011B_RECORD_KIND_SET_MISMATCH", "schuss-record-set-000005@1", "$.record_members", "Task 011B-owned record kinds or counts differ from the bounded closure")

    def operation(name: str, payload: dict[str, Any]) -> tuple[dict[str, Any], bytes]:
        result = dispatch_operation(
            {
                "schema_version": "schuss-operation-request-v1",
                "canonical_profile": "schuss-canonical-json-v1",
                "operation": name,
                "payload": payload,
            },
            context,
        )
        return result, canonical_result_bytes(result, context)

    inspect_result, inspect_bytes = operation(
        "graph.inspect", {"graph_reference": _ref(graph, "graph_id")}
    )
    resolve_result, resolve_bytes = operation(
        "build.resolve", {"build_request_reference": _ref(request, "build_request_id")}
    ) if request is not None else ({"status": "invalid", "value": None}, b"")
    if (
        inspect_result["status"] != "success"
        or len(inspect_result["value"]["graph"]["nodes"]) != 8
        or len(inspect_result["value"]["graph"]["connections"]) != 9
        or len(inspect_result["value"]["component_contract_closure"]) != 7
    ):
        _add(diagnostics, "TASK011B_GRAPH_INSPECTION_INVALID", GRAPH_ID, "$", "graph.inspect did not expose the exact eight-node seven-contract closure")
    expected_trace_status = {
        "graph-node-000001": "unresolved",
        "graph-node-000002": "unresolved",
        "graph-node-000003": "unsupported",
        "graph-node-000004": "unresolved",
        "graph-node-000005": "unresolved",
        "graph-node-000006": "selected",
        "graph-node-000007": "unresolved",
        "graph-node-000008": "unresolved",
    }
    trace_status = {
        item["node_id"]: item["status"]
        for item in (resolve_result.get("value") or {}).get("resolution_traces", [])
    }
    if (
        resolve_result["status"] != "unresolved"
        or (resolve_result.get("value") or {}).get("backend_invocation") is not None
        or trace_status != expected_trace_status
    ):
        _add(diagnostics, "TASK011B_BUILD_RESOLUTION_NOT_FAIL_CLOSED", REQUEST_ID, "$", "build.resolve must select only the promoted Crossfader and emit no backend invocation")

    diagnostics = sorted(
        set(diagnostics),
        key=lambda item: (item.severity, item.code, item.subject, item.location, item.message),
    )
    return {
        "schema_version": "task-011b-validation-summary-v0",
        "status": "invalid" if diagnostics else "valid",
        "record_set_reference": selected.reference,
        "owned_record_counts": dict(sorted(task_counts.items())),
        "graph": {
            "graph_id": graph.get("graph_id"),
            "nodes": len(graph.get("nodes", [])),
            "connections": len(graph.get("connections", [])),
            "contract_closure": (
                len(inspect_result["value"]["component_contract_closure"])
                if inspect_result.get("value") else 0
            ),
            "inspect_sha256": hashlib.sha256(inspect_bytes).hexdigest(),
        },
        "adapter_decisions": {
            "clock_to_counter": "direct-exact-transport-receiver-rising-edge",
            "low_pass_to_stereo": "two-explicit-connections-no-adapter",
        },
        "build_resolution": {
            "status": resolve_result["status"],
            "backend_invocation": (resolve_result.get("value") or {}).get("backend_invocation"),
            "trace_status": trace_status,
            "result_sha256": hashlib.sha256(resolve_bytes).hexdigest(),
        },
        "evidence_levels": {
            "structural": "passed" if not diagnostics else "failed",
            "component_graph_resolution": "passed" if not diagnostics else "failed",
            "backend_lowering": "not-run",
            "artifact_generation": "not-run",
            "arm_compile_link": "not-run",
            "connected_device": "not-run",
            "real_time": "not-run",
            "audible": "not-run",
        },
        "diagnostics": [item.as_dict() for item in diagnostics],
    }
