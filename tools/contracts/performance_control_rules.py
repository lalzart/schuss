#!/usr/bin/env python3
"""Semantic rules for Task 034 performance-control contracts."""

from __future__ import annotations

from collections import defaultdict, deque
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping

import validator_core as core


SCHEMA_VERSIONS = {
    "instruments_v1": "instrument-v1",
    "performance_control_contracts": "performance-control-contract-v0",
    "performance_control_graphs": "performance-control-graph-v0",
    "performance_configurations": "performance-configuration-v0",
}


def _diagnostic(
    diagnostics: list[core.Diagnostic],
    code: str,
    subject: str,
    location: str,
    message: str,
) -> None:
    core.add_diagnostic(diagnostics, code, subject, location, message)


def _subject(record: Mapping[str, Any]) -> str:
    for field in (
        "instrument_id",
        "performance_control_contract_id",
        "performance_control_graph_id",
        "performance_configuration_id",
        "device_profile_id",
        "graph_id",
    ):
        if field in record:
            return f"{record[field]}@{record.get('revision', '?')}"
    return "<unknown>"


def _exact_key(reference: Mapping[str, Any], id_field: str) -> tuple[str, int, str]:
    return (
        str(reference[id_field]),
        int(reference["revision"]),
        str(reference["content_hash"]),
    )


def _record_key(record: Mapping[str, Any], id_field: str) -> tuple[str, int, str]:
    return (
        str(record[id_field]),
        int(record["revision"]),
        str(record["content_hash"]),
    )


def _decimal(value: str) -> Decimal:
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError) as exc:
        raise ValueError(f"invalid exact decimal {value!r}") from exc


def _range_valid(value: Mapping[str, Any]) -> bool:
    return _decimal(str(value["minimum"])) < _decimal(str(value["maximum"]))


def _within(value: str, domain: Mapping[str, Any]) -> bool:
    parsed = _decimal(value)
    return _decimal(str(domain["minimum"])) <= parsed <= _decimal(
        str(domain["maximum"])
    )


def _unique(
    values: Iterable[tuple[str, str]],
    subject: str,
    location: str,
    diagnostics: list[core.Diagnostic],
) -> None:
    seen: dict[str, str] = {}
    for kind, identifier in values:
        prior = seen.get(identifier)
        if prior is not None:
            _diagnostic(
                diagnostics,
                "PERFORMANCE_DUPLICATE_LOCAL_ID",
                subject,
                location,
                f"{identifier!r} is reused by {prior} and {kind}",
            )
        else:
            seen[identifier] = kind


def _identity_collisions(
    records: Iterable[Mapping[str, Any]],
    id_field: str,
    diagnostics: list[core.Diagnostic],
) -> None:
    seen: dict[tuple[str, int], str] = {}
    for record in records:
        key = (str(record[id_field]), int(record["revision"]))
        content_hash = str(record["content_hash"])
        if key in seen:
            code = (
                "PERFORMANCE_ID_REVISION_COLLISION"
                if seen[key] != content_hash
                else "PERFORMANCE_DUPLICATE_RECORD"
            )
            _diagnostic(
                diagnostics,
                code,
                f"{key[0]}@{key[1]}",
                "$",
                "one stable-ID/revision pair must occur exactly once",
            )
        else:
            seen[key] = content_hash


def _forbidden_identity(value: Any) -> str | None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {
                "device_profile_reference",
                "device_input_mappings",
                "device_feedback_mappings",
                "graph_reference",
                "instrument_reference",
                "backend_reference",
                "factory_id",
            }:
                return key
            found = _forbidden_identity(item)
            if found is not None:
                return found
    elif isinstance(value, list):
        for item in value:
            found = _forbidden_identity(item)
            if found is not None:
                return found
    elif isinstance(value, str):
        lowered = value.lower()
        for prefix in (
            "schuss-device-profile-",
            "device-input-",
            "device-gesture-",
            "schuss-instrument-",
            "schuss-graph-",
            "graph-node-",
            "schuss-backend-",
            "schuss.rt.",
        ):
            if value.startswith(prefix):
                return value
        if "juce" in lowered:
            return value
    return None


def _validate_contract(
    record: dict[str, Any], diagnostics: list[core.Diagnostic]
) -> None:
    subject = _subject(record)
    _unique(
        [
            *(("input", item["facet_id"]) for item in record["inputs"]),
            *(("output", item["facet_id"]) for item in record["outputs"]),
            *(("parameter", item["parameter_id"]) for item in record["parameters"]),
            *(("state", item["state_id"]) for item in record["state_declarations"]),
        ],
        subject,
        "$",
        diagnostics,
    )
    found = _forbidden_identity(record)
    if found is not None:
        _diagnostic(
            diagnostics,
            "PERFORMANCE_CONTROL_LAYER_LEAKAGE",
            subject,
            "$",
            f"control contract contains forbidden adjacent-layer identity {found!r}",
        )
    for collection in ("inputs", "outputs"):
        for index, item in enumerate(record[collection]):
            shape = item["shape"]
            if shape["value_kind"] == "continuous" and not _range_valid(shape["domain"]):
                _diagnostic(
                    diagnostics,
                    "PERFORMANCE_RANGE_INVALID",
                    subject,
                    f"$.{collection}[{index}].shape.domain",
                    "range minimum must be less than maximum",
                )
    for index, parameter in enumerate(record["parameters"]):
        if not _range_valid(parameter["domain"]):
            _diagnostic(
                diagnostics,
                "PERFORMANCE_RANGE_INVALID",
                subject,
                f"$.parameters[{index}].domain",
                "range minimum must be less than maximum",
            )
        elif not _within(parameter["default"], parameter["domain"]):
            _diagnostic(
                diagnostics,
                "PERFORMANCE_DEFAULT_OUT_OF_RANGE",
                subject,
                f"$.parameters[{index}].default",
                "parameter default is outside its domain",
            )


def _validate_instrument(
    instrument: dict[str, Any],
    instruments_by_exact: Mapping[tuple[str, int, str], dict[str, Any]],
    dsp_graphs_by_exact: Mapping[tuple[str, int, str], dict[str, Any]],
    graph_targets: Mapping[tuple[str, int, str], dict[str, dict[str, Any]]],
    diagnostics: list[core.Diagnostic],
) -> None:
    subject = _subject(instrument)
    _unique(
        [
            *(("parameter", item["facet_id"]) for item in instrument["parameters"]),
            *(("action", item["facet_id"]) for item in instrument["actions"]),
            *(("display", item["facet_id"]) for item in instrument["displays"]),
            *(("event-input", item["facet_id"]) for item in instrument["event_inputs"]),
            *(("state", item["state_id"]) for item in instrument["state_declarations"]),
            *(("graph-mapping", item["mapping_id"]) for item in instrument["graph_mappings"]),
        ],
        subject,
        "$",
        diagnostics,
    )
    serialized = core.canonical_json(instrument)
    for forbidden in (
        "device_profile_reference",
        "device_input_mappings",
        "device_feedback_mappings",
        "schuss-device-profile-",
        "device-input-",
        "device-gesture-",
    ):
        if forbidden in serialized:
            _diagnostic(
                diagnostics,
                "PERFORMANCE_INSTRUMENT_DEVICE_LEAKAGE",
                subject,
                "$",
                f"device-independent instrument contains {forbidden!r}",
            )
    lineage = instrument["lineage"]
    if lineage["status"] == "successor":
        reference = lineage["predecessor_reference"]
        predecessor = instruments_by_exact.get(_exact_key(reference, "instrument_id"))
        if predecessor is None:
            _diagnostic(
                diagnostics,
                "PERFORMANCE_INSTRUMENT_PREDECESSOR_UNRESOLVED",
                subject,
                "$.lineage.predecessor_reference",
                "the exact predecessor instrument does not resolve",
            )
        elif (
            predecessor["instrument_id"] != instrument["instrument_id"]
            or predecessor["revision"] >= instrument["revision"]
        ):
            _diagnostic(
                diagnostics,
                "PERFORMANCE_INSTRUMENT_LINEAGE_INVALID",
                subject,
                "$.lineage.predecessor_reference",
                "a successor must keep its stable ID and advance the revision",
            )
    graph_reference = instrument["graph_reference"]
    if graph_reference["status"] != "resolved":
        _diagnostic(
            diagnostics,
            "PERFORMANCE_INSTRUMENT_GRAPH_DEFERRED",
            subject,
            "$.graph_reference",
            "Task 034 performance configurations require an exact DSP graph",
        )
        return
    graph_key = _exact_key(graph_reference, "graph_id")
    if graph_key not in dsp_graphs_by_exact or graph_key not in graph_targets:
        _diagnostic(
            diagnostics,
            "PERFORMANCE_INSTRUMENT_GRAPH_UNRESOLVED",
            subject,
            "$.graph_reference",
            "the exact DSP graph does not resolve through the validated registry",
        )
    parameter_map = {item["facet_id"]: item for item in instrument["parameters"]}
    action_map = {item["facet_id"]: item for item in instrument["actions"]}
    targets = graph_targets.get(graph_key, {})
    for index, mapping in enumerate(instrument["graph_mappings"]):
        source = mapping["source"]
        destination = mapping["destination"]
        source_map = parameter_map if source["facet_kind"] == "parameter" else action_map
        if source["facet_id"] not in source_map:
            _diagnostic(
                diagnostics,
                "PERFORMANCE_INSTRUMENT_MAPPING_SOURCE_UNKNOWN",
                subject,
                f"$.graph_mappings[{index}].source",
                "instrument-to-DSP source facet is unknown",
            )
        if destination["facet_id"] not in targets:
            _diagnostic(
                diagnostics,
                "PERFORMANCE_INSTRUMENT_MAPPING_DESTINATION_UNKNOWN",
                subject,
                f"$.graph_mappings[{index}].destination",
                "instrument-to-DSP destination facet is unknown",
            )


def _node_contract(
    node: Mapping[str, Any],
    contracts_by_exact: Mapping[tuple[str, int, str], dict[str, Any]],
) -> dict[str, Any] | None:
    return contracts_by_exact.get(
        _exact_key(node["contract_reference"], "performance_control_contract_id")
    )


def _validate_control_graph(
    graph: dict[str, Any],
    contracts_by_exact: Mapping[tuple[str, int, str], dict[str, Any]],
    diagnostics: list[core.Diagnostic],
) -> None:
    subject = _subject(graph)
    _unique(
        [
            *(("public-input", item["facet_id"]) for item in graph["public_inputs"]),
            *(("public-output", item["facet_id"]) for item in graph["public_outputs"]),
            *(("node", item["node_id"]) for item in graph["nodes"]),
            *(("connection", item["connection_id"]) for item in graph["connections"]),
        ],
        subject,
        "$",
        diagnostics,
    )
    found = _forbidden_identity(graph)
    if found is not None:
        _diagnostic(
            diagnostics,
            "PERFORMANCE_CONTROL_LAYER_LEAKAGE",
            subject,
            "$",
            f"control graph contains forbidden adjacent-layer identity {found!r}",
        )
    public_inputs = {item["facet_id"]: item for item in graph["public_inputs"]}
    public_outputs = {item["facet_id"]: item for item in graph["public_outputs"]}
    nodes = {item["node_id"]: item for item in graph["nodes"]}
    node_contracts: dict[str, dict[str, Any]] = {}
    for index, node in enumerate(graph["nodes"]):
        contract = _node_contract(node, contracts_by_exact)
        if contract is None:
            _diagnostic(
                diagnostics,
                "PERFORMANCE_CONTROL_CONTRACT_UNRESOLVED",
                subject,
                f"$.nodes[{index}].contract_reference",
                "the exact performance-control contract does not resolve",
            )
            continue
        node_contracts[node["node_id"]] = contract
        parameters = {item["parameter_id"]: item for item in contract["parameters"]}
        seen_parameters: set[str] = set()
        for value_index, value in enumerate(node["parameter_values"]):
            parameter = parameters.get(value["parameter_id"])
            if parameter is None:
                _diagnostic(
                    diagnostics,
                    "PERFORMANCE_CONTROL_PARAMETER_UNKNOWN",
                    subject,
                    f"$.nodes[{index}].parameter_values[{value_index}]",
                    "node parameter does not exist in its exact contract",
                )
            elif value["parameter_id"] in seen_parameters:
                _diagnostic(
                    diagnostics,
                    "PERFORMANCE_DUPLICATE_LOCAL_ID",
                    subject,
                    f"$.nodes[{index}].parameter_values",
                    "a node parameter may be assigned at most once",
                )
            elif not _within(value["value"], parameter["domain"]):
                _diagnostic(
                    diagnostics,
                    "PERFORMANCE_CONTROL_PARAMETER_OUT_OF_RANGE",
                    subject,
                    f"$.nodes[{index}].parameter_values[{value_index}].value",
                    "node parameter value is outside its contract domain",
                )
            seen_parameters.add(value["parameter_id"])

    def source_shape(endpoint: Mapping[str, Any]) -> dict[str, Any] | None:
        if endpoint["endpoint_kind"] == "graph-input":
            item = public_inputs.get(endpoint["facet_id"])
            return None if item is None else item["shape"]
        node = nodes.get(endpoint["node_id"])
        contract = None if node is None else node_contracts.get(node["node_id"])
        if contract is None:
            return None
        item = next(
            (item for item in contract["outputs"] if item["facet_id"] == endpoint["facet_id"]),
            None,
        )
        return None if item is None else item["shape"]

    def destination_shape(endpoint: Mapping[str, Any]) -> dict[str, Any] | None:
        if endpoint["endpoint_kind"] == "graph-output":
            item = public_outputs.get(endpoint["facet_id"])
            return None if item is None else item["shape"]
        node = nodes.get(endpoint["node_id"])
        contract = None if node is None else node_contracts.get(node["node_id"])
        if contract is None:
            return None
        item = next(
            (item for item in contract["inputs"] if item["facet_id"] == endpoint["facet_id"]),
            None,
        )
        return None if item is None else item["shape"]

    destinations: set[tuple[str, str, str]] = set()
    used_inputs: set[str] = set()
    adjacency: dict[str, set[str]] = defaultdict(set)
    indegree = {node_id: 0 for node_id in nodes}
    for index, connection in enumerate(graph["connections"]):
        source = connection["source"]
        destination = connection["destination"]
        source_value = source_shape(source)
        destination_value = destination_shape(destination)
        if source_value is None:
            _diagnostic(
                diagnostics,
                "PERFORMANCE_CONTROL_SOURCE_UNKNOWN",
                subject,
                f"$.connections[{index}].source",
                "connection source does not resolve",
            )
        if destination_value is None:
            _diagnostic(
                diagnostics,
                "PERFORMANCE_CONTROL_DESTINATION_UNKNOWN",
                subject,
                f"$.connections[{index}].destination",
                "connection destination does not resolve",
            )
        if source_value is not None and destination_value is not None and source_value != destination_value:
            _diagnostic(
                diagnostics,
                "PERFORMANCE_CONTROL_TYPE_MISMATCH",
                subject,
                f"$.connections[{index}]",
                "connection source and destination shapes differ",
            )
        destination_key = (
            destination["endpoint_kind"],
            str(destination.get("node_id", "")),
            destination["facet_id"],
        )
        if destination_key in destinations:
            _diagnostic(
                diagnostics,
                "PERFORMANCE_CONTROL_MULTIPLE_DRIVERS",
                subject,
                f"$.connections[{index}].destination",
                "a control destination may have only one driver",
            )
        destinations.add(destination_key)
        if source["endpoint_kind"] == "graph-input":
            used_inputs.add(source["facet_id"])
        if source["endpoint_kind"] == "node-output" and destination["endpoint_kind"] == "node-input":
            source_node = source["node_id"]
            destination_node = destination["node_id"]
            if destination_node not in adjacency[source_node]:
                adjacency[source_node].add(destination_node)
                indegree[destination_node] = indegree.get(destination_node, 0) + 1
    for facet_id in public_inputs:
        if facet_id not in used_inputs:
            _diagnostic(
                diagnostics,
                "PERFORMANCE_CONTROL_INPUT_UNUSED",
                subject,
                "$.public_inputs",
                f"public input {facet_id!r} is not connected",
            )
    required_destinations = {
        *(("graph-output", "", facet_id) for facet_id in public_outputs),
        *(
            ("node-input", node_id, port["facet_id"])
            for node_id, contract in node_contracts.items()
            for port in contract["inputs"]
        ),
    }
    for missing in sorted(required_destinations - destinations):
        _diagnostic(
            diagnostics,
            "PERFORMANCE_CONTROL_DESTINATION_UNDRIVEN",
            subject,
            "$.connections",
            f"required destination {missing!r} has no driver",
        )
    queue = deque(sorted(node_id for node_id, degree in indegree.items() if degree == 0))
    visited = 0
    while queue:
        node_id = queue.popleft()
        visited += 1
        for destination_node in sorted(adjacency.get(node_id, ())):
            indegree[destination_node] -= 1
            if indegree[destination_node] == 0:
                queue.append(destination_node)
    if visited != len(nodes):
        _diagnostic(
            diagnostics,
            "PERFORMANCE_CONTROL_CYCLE_UNSUPPORTED",
            subject,
            "$.connections",
            "performance-control graph contains a cycle",
        )


def _device_shape(
    device: Mapping[str, Any], selector: Mapping[str, Any]
) -> dict[str, Any] | None:
    if selector["selector_kind"] == "device-input":
        item = next(
            (item for item in device["input_controls"] if item["slot_id"] == selector["slot_id"]),
            None,
        )
        if item is None:
            return None
        if item["logical_range"]["unit"] == "boolean":
            return {"value_kind": "boolean"}
        return {"value_kind": "continuous", "domain": item["logical_range"]}
    item = next(
        (item for item in device["gestures"] if item["gesture_id"] == selector["gesture_id"]),
        None,
    )
    return None if item is None else {"value_kind": "trigger"}


def _instrument_facet_shape(
    instrument: Mapping[str, Any], destination: Mapping[str, Any]
) -> dict[str, Any] | None:
    kind = destination["facet_kind"]
    facet_id = destination["facet_id"]
    if kind == "parameter":
        item = next(
            (item for item in instrument["parameters"] if item["facet_id"] == facet_id),
            None,
        )
        return None if item is None else {"value_kind": "continuous", "domain": item["domain"]}
    if kind == "action":
        item = next(
            (item for item in instrument["actions"] if item["facet_id"] == facet_id),
            None,
        )
        if item is None:
            return None
        return {"value_kind": "trigger"} if item["payload_kind"] == "none" else {"value_kind": "continuous"}
    item = next(
        (item for item in instrument["event_inputs"] if item["facet_id"] == facet_id),
        None,
    )
    if item is None:
        return None
    return {
        "value_kind": {
            "trigger": "trigger",
            "note": "note-event",
            "clock": "clock-event",
            "transport": "transport-event",
        }[item["event_kind"]]
    }


def _validate_configuration(
    configuration: dict[str, Any],
    instruments_by_exact: Mapping[tuple[str, int, str], dict[str, Any]],
    control_graphs_by_exact: Mapping[tuple[str, int, str], dict[str, Any]],
    devices_by_exact: Mapping[tuple[str, int, str], dict[str, Any]],
    diagnostics: list[core.Diagnostic],
) -> None:
    subject = _subject(configuration)
    instrument = instruments_by_exact.get(
        _exact_key(configuration["instrument_reference"], "instrument_id")
    )
    graph = control_graphs_by_exact.get(
        _exact_key(
            configuration["performance_control_graph_reference"],
            "performance_control_graph_id",
        )
    )
    if instrument is None or instrument.get("schema_version") != "instrument-v1":
        _diagnostic(
            diagnostics,
            "PERFORMANCE_CONFIGURATION_INSTRUMENT_UNRESOLVED",
            subject,
            "$.instrument_reference",
            "the exact device-independent instrument-v1 does not resolve",
        )
    if graph is None:
        _diagnostic(
            diagnostics,
            "PERFORMANCE_CONFIGURATION_GRAPH_UNRESOLVED",
            subject,
            "$.performance_control_graph_reference",
            "the exact performance-control graph does not resolve",
        )
    source_ids: list[tuple[str, str]] = []
    binding_ids: list[tuple[str, str]] = []
    mapping_ids = [
        ("instrument-mapping", item["mapping_id"])
        for item in configuration["instrument_mappings"]
    ]
    for source in configuration["controller_sources"]:
        source_ids.append(("controller-source", source["controller_source_id"]))
        binding_ids.extend(("controller-binding", item["binding_id"]) for item in source["bindings"])
    _unique(source_ids + binding_ids + mapping_ids, subject, "$", diagnostics)
    if graph is None:
        return
    inputs = {item["facet_id"]: item for item in graph["public_inputs"]}
    outputs = {item["facet_id"]: item for item in graph["public_outputs"]}
    driven_inputs: set[str] = set()
    for source_index, source in enumerate(configuration["controller_sources"]):
        device = None
        if source["source_kind"] == "device-profile":
            device = devices_by_exact.get(
                _exact_key(source["device_profile_reference"], "device_profile_id")
            )
            if device is None:
                _diagnostic(
                    diagnostics,
                    "PERFORMANCE_CONTROLLER_DEVICE_UNRESOLVED",
                    subject,
                    f"$.controller_sources[{source_index}].device_profile_reference",
                    "the exact device profile does not resolve",
                )
        for binding_index, binding in enumerate(source["bindings"]):
            input_id = binding["destination_graph_input_id"]
            destination = inputs.get(input_id)
            if input_id in driven_inputs:
                _diagnostic(
                    diagnostics,
                    "PERFORMANCE_CONFIGURATION_MULTIPLE_DRIVERS",
                    subject,
                    f"$.controller_sources[{source_index}].bindings[{binding_index}]",
                    "a public control input may have only one controller driver",
                )
            driven_inputs.add(input_id)
            if destination is None:
                _diagnostic(
                    diagnostics,
                    "PERFORMANCE_CONFIGURATION_INPUT_UNKNOWN",
                    subject,
                    f"$.controller_sources[{source_index}].bindings[{binding_index}].destination_graph_input_id",
                    "controller binding destination is not a public graph input",
                )
                continue
            if source["source_kind"] == "device-profile":
                source_shape = None if device is None else _device_shape(device, binding["selector"])
                if source_shape is None:
                    _diagnostic(
                        diagnostics,
                        "PERFORMANCE_CONTROLLER_SELECTOR_UNKNOWN",
                        subject,
                        f"$.controller_sources[{source_index}].bindings[{binding_index}].selector",
                        "device selector does not resolve in the exact device profile",
                    )
            else:
                selector = binding["selector"]
                if not (
                    isinstance(selector["channel"], int)
                    and not isinstance(selector["channel"], bool)
                    and 1 <= selector["channel"] <= 16
                    and isinstance(selector["controller_number"], int)
                    and not isinstance(selector["controller_number"], bool)
                    and 0 <= selector["controller_number"] <= 127
                ):
                    _diagnostic(
                        diagnostics,
                        "PERFORMANCE_MIDI_SELECTOR_OUT_OF_RANGE",
                        subject,
                        f"$.controller_sources[{source_index}].bindings[{binding_index}].selector",
                        "MIDI channel must be 1..16 and controller number must be 0..127",
                    )
                source_shape = {
                    "value_kind": "continuous",
                    "domain": {"minimum": "0", "maximum": "1", "unit": "normalized"},
                }
            if source_shape is not None and source_shape != destination["shape"]:
                _diagnostic(
                    diagnostics,
                    "PERFORMANCE_CONTROLLER_TYPE_MISMATCH",
                    subject,
                    f"$.controller_sources[{source_index}].bindings[{binding_index}]",
                    "controller selector and graph input shapes differ",
                )
    for input_id in sorted(set(inputs) - driven_inputs):
        _diagnostic(
            diagnostics,
            "PERFORMANCE_CONFIGURATION_INPUT_UNDRIVEN",
            subject,
            "$.controller_sources",
            f"public control input {input_id!r} has no controller binding",
        )
    mapped_outputs: set[str] = set()
    for index, mapping in enumerate(configuration["instrument_mappings"]):
        output_id = mapping["source_graph_output_id"]
        output = outputs.get(output_id)
        if output_id in mapped_outputs:
            _diagnostic(
                diagnostics,
                "PERFORMANCE_CONFIGURATION_MULTIPLE_DRIVERS",
                subject,
                f"$.instrument_mappings[{index}]",
                "a public control output may be mapped only once",
            )
        mapped_outputs.add(output_id)
        if output is None:
            _diagnostic(
                diagnostics,
                "PERFORMANCE_CONFIGURATION_OUTPUT_UNKNOWN",
                subject,
                f"$.instrument_mappings[{index}].source_graph_output_id",
                "mapping source is not a public control-graph output",
            )
            continue
        destination_shape = (
            None
            if instrument is None
            else _instrument_facet_shape(instrument, mapping["destination"])
        )
        if destination_shape is None:
            _diagnostic(
                diagnostics,
                "PERFORMANCE_CONFIGURATION_FACET_UNKNOWN",
                subject,
                f"$.instrument_mappings[{index}].destination",
                "mapping destination is not a public instrument facet",
            )
        elif output["shape"] != destination_shape:
            _diagnostic(
                diagnostics,
                "PERFORMANCE_CONFIGURATION_TYPE_MISMATCH",
                subject,
                f"$.instrument_mappings[{index}]",
                "control-graph output and instrument facet shapes differ",
            )
    for output_id in sorted(set(outputs) - mapped_outputs):
        _diagnostic(
            diagnostics,
            "PERFORMANCE_CONFIGURATION_OUTPUT_UNMAPPED",
            subject,
            "$.instrument_mappings",
            f"public control output {output_id!r} has no instrument mapping",
        )
    serialized = core.canonical_json(configuration)
    for forbidden in ("graph-node-", "schuss-backend-", "factory_id", "juce"):
        if forbidden in serialized.lower():
            _diagnostic(
                diagnostics,
                "PERFORMANCE_CONFIGURATION_DSP_LEAKAGE",
                subject,
                "$",
                f"configuration contains forbidden DSP/runtime identity {forbidden!r}",
            )


def validate_values(
    records: Mapping[str, list[dict[str, Any]]],
    schemas: Mapping[str, dict[str, Any]],
    graph_targets: Mapping[tuple[str, int, str], dict[str, dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Validate one explicit performance-control closure deterministically."""

    diagnostics: list[core.Diagnostic] = []
    valid: dict[str, list[dict[str, Any]]] = {
        key: [] for key in SCHEMA_VERSIONS
    }
    for group, version in SCHEMA_VERSIONS.items():
        schema = schemas[version]
        for error in core.validate_schema_annotations(schema):
            _diagnostic(
                diagnostics,
                "PERFORMANCE_SCHEMA_INVALID",
                version,
                "$",
                error,
            )
        for record in records.get(group, []):
            subject = _subject(record)
            core.scan_portability(record, subject, diagnostics)
            errors = core.schema_errors(record, schema, schema)
            for error in errors:
                _diagnostic(
                    diagnostics,
                    "PERFORMANCE_SCHEMA_STRUCTURE_INVALID",
                    subject,
                    "$",
                    error,
                )
            if not errors and record.get("schema_version") == version:
                valid[group].append(record)
                expected_hash = core.record_content_hash(record, schema)
                if record["content_hash"] != expected_hash:
                    _diagnostic(
                        diagnostics,
                        "PERFORMANCE_CONTENT_HASH_MISMATCH",
                        subject,
                        "$.content_hash",
                        f"expected {expected_hash}",
                    )
    for group, id_field in (
        ("instruments_v1", "instrument_id"),
        ("performance_control_contracts", "performance_control_contract_id"),
        ("performance_control_graphs", "performance_control_graph_id"),
        ("performance_configurations", "performance_configuration_id"),
    ):
        _identity_collisions(valid[group], id_field, diagnostics)

    all_instruments = [
        *records.get("instruments_v0", []),
        *valid["instruments_v1"],
    ]
    instruments_by_exact = {
        _record_key(record, "instrument_id"): record for record in all_instruments
    }
    dsp_graphs_by_exact = {
        _record_key(record, "graph_id"): record for record in records.get("dsp_graphs", [])
    }
    devices_by_exact = {
        _record_key(record, "device_profile_id"): record
        for record in records.get("devices", [])
    }
    contracts_by_exact = {
        _record_key(record, "performance_control_contract_id"): record
        for record in valid["performance_control_contracts"]
    }
    control_graphs_by_exact = {
        _record_key(record, "performance_control_graph_id"): record
        for record in valid["performance_control_graphs"]
    }
    targets = graph_targets or {}
    for record in valid["performance_control_contracts"]:
        _validate_contract(record, diagnostics)
    for record in valid["instruments_v1"]:
        _validate_instrument(
            record,
            instruments_by_exact,
            dsp_graphs_by_exact,
            targets,
            diagnostics,
        )
    for record in valid["performance_control_graphs"]:
        _validate_control_graph(record, contracts_by_exact, diagnostics)
    for record in valid["performance_configurations"]:
        _validate_configuration(
            record,
            instruments_by_exact,
            control_graphs_by_exact,
            devices_by_exact,
            diagnostics,
        )

    diagnostics = sorted(set(diagnostics), key=core.diagnostic_sort_key)
    status = "invalid" if diagnostics else "valid"
    return {
        "schema_version": "performance-control-validation-summary-v0",
        "status": status,
        "record_counts": {
            "instrument_v1": len(records.get("instruments_v1", [])),
            "performance_control_contracts": len(
                records.get("performance_control_contracts", [])
            ),
            "performance_control_graphs": len(
                records.get("performance_control_graphs", [])
            ),
            "performance_configurations": len(
                records.get("performance_configurations", [])
            ),
        },
        "reference_resolution": {
            "instrument_predecessors_resolved": sum(
                item["lineage"]["status"] == "successor"
                and _exact_key(
                    item["lineage"]["predecessor_reference"], "instrument_id"
                )
                in instruments_by_exact
                for item in valid["instruments_v1"]
            ),
            "dsp_graphs_resolved": sum(
                item["graph_reference"]["status"] == "resolved"
                and _exact_key(item["graph_reference"], "graph_id") in dsp_graphs_by_exact
                for item in valid["instruments_v1"]
            ),
            "performance_control_contracts_resolved": sum(
                _node_contract(node, contracts_by_exact) is not None
                for graph in valid["performance_control_graphs"]
                for node in graph["nodes"]
            ),
            "performance_configurations_resolved": sum(
                _exact_key(item["instrument_reference"], "instrument_id")
                in instruments_by_exact
                and _exact_key(
                    item["performance_control_graph_reference"],
                    "performance_control_graph_id",
                )
                in control_graphs_by_exact
                for item in valid["performance_configurations"]
            ),
        },
        "boundary_assertions": {
            "controller_bindings_owned_by_configuration": status == "valid",
            "control_graph_has_no_device_or_dsp_identity": status == "valid",
            "instrument_v1_has_no_device_identity": status == "valid",
            "existing_v0_consumers_remain_separate": True,
        },
        "evidence_levels": [
            {"level": "structural-schema-and-reference", "status": "failed" if diagnostics else "passed"},
            {"level": "control-graph-execution", "status": "not-run"},
            {"level": "backend-lowering", "status": "not-run"},
            {"level": "native-build", "status": "not-run"},
            {"level": "physical-controller", "status": "not-run"},
            {"level": "real-time-resource", "status": "not-run"},
            {"level": "audible-listening", "status": "not-run"},
        ],
        "diagnostics": [item.as_dict() for item in diagnostics],
    }
