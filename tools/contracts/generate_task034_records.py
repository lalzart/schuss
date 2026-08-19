#!/usr/bin/env python3
"""Generate Task 034 performance-control contracts and exact allocation."""

from __future__ import annotations

import argparse
import copy
import hashlib
from pathlib import Path
import sys
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "tools/contracts") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools/contracts"))

from tools.contracts import record_set_rules  # noqa: E402
from tools.contracts import validator_core as core  # noqa: E402


PARENT = ROOT / "contracts/record-sets/task032-variable-host-runtime-v1.json"
OUTPUT = ROOT / "contracts/record-sets/task034-performance-control-v1.json"
TASK_DIR = ROOT / "contracts/task034"
RECORD_SET_ID = "schuss-record-set-000030"
SCHEMA_NAMES = (
    "application-capability-description-v10",
    "instrument-v1",
    "operation-request-v17",
    "operation-result-v17",
    "performance-configuration-v0",
    "performance-control-contract-v0",
    "performance-control-graph-v0",
)


def _canonical_bytes(value: object) -> bytes:
    return (core.canonical_json(value) + "\n").encode("utf-8")


def _closed(
    required: Iterable[str], properties: Mapping[str, Any]
) -> dict[str, Any]:
    return {
        "type": "object",
        "required": list(required),
        "properties": dict(properties),
        "additionalProperties": False,
    }


def _set(items: dict[str, Any], *, minimum: int = 0) -> dict[str, Any]:
    return {
        "type": "array",
        "x-schuss-array-kind": "set",
        "minItems": minimum,
        "uniqueItems": True,
        "items": items,
    }


def _content_hash() -> dict[str, Any]:
    return {"type": "string", "pattern": r"^sha256:[0-9a-f]{64}$"}


def _exact_decimal() -> dict[str, Any]:
    return {
        "type": "string",
        "pattern": r"^(?:0|-?(?:0\.[0-9]*[1-9]|[1-9][0-9]*(?:\.[0-9]*[1-9])?))$",
    }


def _label() -> dict[str, Any]:
    return {"type": "string", "minLength": 1}


def _semantic_key() -> dict[str, Any]:
    return {"type": "string", "pattern": r"^[a-z][a-z0-9-]*$"}


def _reference(id_field: str, pattern: str) -> dict[str, Any]:
    return _closed(
        (id_field, "revision", "content_hash"),
        {
            id_field: {"type": "string", "pattern": pattern},
            "revision": {"type": "integer", "minimum": 1},
            "content_hash": _content_hash(),
        },
    )


def _exact_range() -> dict[str, Any]:
    return _closed(
        ("minimum", "maximum", "unit"),
        {
            "minimum": _exact_decimal(),
            "maximum": _exact_decimal(),
            "unit": {"enum": ["normalized", "steps", "boolean"]},
        },
    )


def _value_shape() -> dict[str, Any]:
    return {
        "oneOf": [
            _closed(
                ("value_kind", "domain"),
                {"value_kind": {"const": "continuous"}, "domain": _exact_range()},
            ),
            _closed(("value_kind",), {"value_kind": {"const": "boolean"}}),
            _closed(("value_kind",), {"value_kind": {"const": "trigger"}}),
            _closed(("value_kind",), {"value_kind": {"const": "note-event"}}),
            _closed(("value_kind",), {"value_kind": {"const": "clock-event"}}),
            _closed(("value_kind",), {"value_kind": {"const": "transport-event"}}),
        ]
    }


def _record_identity(
    schema_version: str, id_field: str, id_pattern: str
) -> tuple[tuple[str, ...], dict[str, Any]]:
    return (
        (
            "schema_version",
            "canonical_profile",
            id_field,
            "revision",
            "content_hash",
            "display_name",
        ),
        {
            "schema_version": {"const": schema_version},
            "canonical_profile": {"const": "schuss-canonical-json-v1"},
            id_field: {"type": "string", "pattern": id_pattern},
            "revision": {"type": "integer", "minimum": 1},
            "content_hash": _content_hash(),
            "display_name": _label(),
        },
    )


def _instrument_schema() -> dict[str, Any]:
    schema = copy.deepcopy(core.load_json(ROOT / "schemas/instrument-v0.schema.json"))
    schema["$id"] = "instrument-v1.schema.json"
    schema["title"] = "Schuss device-independent instrument v1"
    schema["properties"]["schema_version"] = {"const": "instrument-v1"}
    removed = {
        "device_profile_reference",
        "device_input_mappings",
        "device_feedback_mappings",
    }
    schema["required"] = [item for item in schema["required"] if item not in removed]
    for item in removed:
        schema["properties"].pop(item)
    schema["required"].insert(6, "lineage")
    schema["required"].insert(schema["required"].index("graph_mappings"), "event_inputs")
    schema["properties"]["lineage"] = {
        "oneOf": [
            _closed(("status",), {"status": {"const": "new"}}),
            _closed(
                ("status", "predecessor_reference"),
                {
                    "status": {"const": "successor"},
                    "predecessor_reference": _reference(
                        "instrument_id", r"^schuss-instrument-[0-9]{6}$"
                    ),
                },
            ),
        ]
    }
    schema["properties"]["event_inputs"] = _set(
        _closed(
            ("facet_id", "semantic_key", "display_label", "event_kind"),
            {
                "facet_id": {
                    "type": "string",
                    "pattern": r"^instrument-event-input-[0-9]{6}$",
                },
                "semantic_key": _semantic_key(),
                "display_label": _label(),
                "event_kind": {
                    "enum": ["trigger", "note", "clock", "transport"]
                },
            },
        )
    )
    for name in (
        "deviceProfileId",
        "deviceProfileReference",
        "parameterControlMapping",
        "actionTriggerMapping",
        "deviceInputMapping",
        "deviceFeedbackMapping",
    ):
        schema["$defs"].pop(name)
    return schema


def _control_contract_schema() -> dict[str, Any]:
    required, properties = _record_identity(
        "performance-control-contract-v0",
        "performance_control_contract_id",
        r"^schuss-performance-control-contract-[0-9]{6}$",
    )
    port = _closed(
        ("facet_id", "semantic_key", "display_label", "shape"),
        {
            "facet_id": {
                "type": "string",
                "pattern": r"^performance-control-port-[0-9]{6}$",
            },
            "semantic_key": _semantic_key(),
            "display_label": _label(),
            "shape": _value_shape(),
        },
    )
    parameter = _closed(
        ("parameter_id", "semantic_key", "display_label", "domain", "default"),
        {
            "parameter_id": {
                "type": "string",
                "pattern": r"^performance-control-parameter-[0-9]{6}$",
            },
            "semantic_key": _semantic_key(),
            "display_label": _label(),
            "domain": _exact_range(),
            "default": _exact_decimal(),
        },
    )
    state = _closed(
        ("state_id", "semantic_key", "value_kind", "reset_policy"),
        {
            "state_id": {
                "type": "string",
                "pattern": r"^performance-control-state-[0-9]{6}$",
            },
            "semantic_key": _semantic_key(),
            "value_kind": {
                "enum": ["continuous", "boolean", "event-history"]
            },
            "reset_policy": {"const": "declared-default"},
        },
    )
    properties.update(
        {
            "function_key": _semantic_key(),
            "inputs": _set(port, minimum=1),
            "outputs": _set(port, minimum=1),
            "parameters": _set(parameter),
            "state_declarations": _set(state),
        }
    )
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "performance-control-contract-v0.schema.json",
        "title": "Schuss performance-control contract v0",
        **_closed(
            (*required, "function_key", "inputs", "outputs", "parameters", "state_declarations"),
            properties,
        ),
    }


def _control_graph_schema() -> dict[str, Any]:
    required, properties = _record_identity(
        "performance-control-graph-v0",
        "performance_control_graph_id",
        r"^schuss-performance-control-graph-[0-9]{6}$",
    )
    public_input = _closed(
        ("facet_id", "semantic_key", "display_label", "shape"),
        {
            "facet_id": {
                "type": "string",
                "pattern": r"^performance-control-input-[0-9]{6}$",
            },
            "semantic_key": _semantic_key(),
            "display_label": _label(),
            "shape": _value_shape(),
        },
    )
    public_output = copy.deepcopy(public_input)
    public_output["properties"]["facet_id"]["pattern"] = (
        r"^performance-control-output-[0-9]{6}$"
    )
    parameter_value = _closed(
        ("parameter_id", "value"),
        {
            "parameter_id": {
                "type": "string",
                "pattern": r"^performance-control-parameter-[0-9]{6}$",
            },
            "value": _exact_decimal(),
        },
    )
    node = _closed(
        ("node_id", "contract_reference", "parameter_values"),
        {
            "node_id": {
                "type": "string",
                "pattern": r"^performance-control-node-[0-9]{6}$",
            },
            "contract_reference": _reference(
                "performance_control_contract_id",
                r"^schuss-performance-control-contract-[0-9]{6}$",
            ),
            "parameter_values": _set(parameter_value),
        },
    )
    source = {
        "oneOf": [
            _closed(
                ("endpoint_kind", "facet_id"),
                {
                    "endpoint_kind": {"const": "graph-input"},
                    "facet_id": {
                        "type": "string",
                        "pattern": r"^performance-control-input-[0-9]{6}$",
                    },
                },
            ),
            _closed(
                ("endpoint_kind", "node_id", "facet_id"),
                {
                    "endpoint_kind": {"const": "node-output"},
                    "node_id": node["properties"]["node_id"],
                    "facet_id": {
                        "type": "string",
                        "pattern": r"^performance-control-port-[0-9]{6}$",
                    },
                },
            ),
        ]
    }
    destination = {
        "oneOf": [
            _closed(
                ("endpoint_kind", "node_id", "facet_id"),
                {
                    "endpoint_kind": {"const": "node-input"},
                    "node_id": node["properties"]["node_id"],
                    "facet_id": {
                        "type": "string",
                        "pattern": r"^performance-control-port-[0-9]{6}$",
                    },
                },
            ),
            _closed(
                ("endpoint_kind", "facet_id"),
                {
                    "endpoint_kind": {"const": "graph-output"},
                    "facet_id": {
                        "type": "string",
                        "pattern": r"^performance-control-output-[0-9]{6}$",
                    },
                },
            ),
        ]
    }
    connection = _closed(
        ("connection_id", "source", "destination"),
        {
            "connection_id": {
                "type": "string",
                "pattern": r"^performance-control-connection-[0-9]{6}$",
            },
            "source": source,
            "destination": destination,
        },
    )
    properties.update(
        {
            "public_inputs": _set(public_input, minimum=1),
            "public_outputs": _set(public_output, minimum=1),
            "nodes": _set(node, minimum=1),
            "connections": _set(connection, minimum=1),
        }
    )
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "performance-control-graph-v0.schema.json",
        "title": "Schuss performance-control graph v0",
        **_closed(
            (*required, "public_inputs", "public_outputs", "nodes", "connections"),
            properties,
        ),
    }


def _configuration_schema() -> dict[str, Any]:
    required, properties = _record_identity(
        "performance-configuration-v0",
        "performance_configuration_id",
        r"^schuss-performance-configuration-[0-9]{6}$",
    )
    graph_input_id = {
        "type": "string",
        "pattern": r"^performance-control-input-[0-9]{6}$",
    }
    binding_id = {
        "type": "string",
        "pattern": r"^controller-binding-[0-9]{6}$",
    }
    device_selector = {
        "oneOf": [
            _closed(
                ("selector_kind", "slot_id"),
                {
                    "selector_kind": {"const": "device-input"},
                    "slot_id": {
                        "type": "string",
                        "pattern": r"^device-input-[0-9]{6}$",
                    },
                },
            ),
            _closed(
                ("selector_kind", "gesture_id"),
                {
                    "selector_kind": {"const": "device-gesture"},
                    "gesture_id": {
                        "type": "string",
                        "pattern": r"^device-gesture-[0-9]{6}$",
                    },
                },
            ),
        ]
    }
    device_binding = _closed(
        ("binding_id", "selector", "destination_graph_input_id"),
        {
            "binding_id": binding_id,
            "selector": device_selector,
            "destination_graph_input_id": graph_input_id,
        },
    )
    midi_selector = _closed(
        ("message_kind", "channel", "controller_number"),
        {
            "message_kind": {"const": "control-change"},
            "channel": {"type": "integer", "minimum": 1, "maximum": 16},
            "controller_number": {
                "type": "integer",
                "minimum": 0,
                "maximum": 127,
            },
        },
    )
    midi_binding = _closed(
        ("binding_id", "selector", "destination_graph_input_id"),
        {
            "binding_id": binding_id,
            "selector": midi_selector,
            "destination_graph_input_id": graph_input_id,
        },
    )
    source_id = {
        "type": "string",
        "pattern": r"^controller-source-[0-9]{6}$",
    }
    controller_source = {
        "oneOf": [
            _closed(
                (
                    "controller_source_id",
                    "source_kind",
                    "device_profile_reference",
                    "bindings",
                ),
                {
                    "controller_source_id": source_id,
                    "source_kind": {"const": "device-profile"},
                    "device_profile_reference": _reference(
                        "device_profile_id", r"^schuss-device-profile-[0-9]{6}$"
                    ),
                    "bindings": _set(device_binding, minimum=1),
                },
            ),
            _closed(
                (
                    "controller_source_id",
                    "source_kind",
                    "protocol",
                    "endpoint_role",
                    "bindings",
                ),
                {
                    "controller_source_id": source_id,
                    "source_kind": {"const": "midi"},
                    "protocol": {"const": "midi-1.0-channel-voice"},
                    "endpoint_role": {"const": "controller-input"},
                    "bindings": _set(midi_binding, minimum=1),
                },
            ),
        ]
    }
    destination = _closed(
        ("facet_kind", "facet_id"),
        {
            "facet_kind": {"enum": ["parameter", "action", "event-input"]},
            "facet_id": {
                "type": "string",
                "pattern": r"^instrument-(?:parameter|action|event-input)-[0-9]{6}$",
            },
        },
    )
    instrument_mapping = _closed(
        ("mapping_id", "source_graph_output_id", "destination"),
        {
            "mapping_id": {
                "type": "string",
                "pattern": r"^performance-instrument-mapping-[0-9]{6}$",
            },
            "source_graph_output_id": {
                "type": "string",
                "pattern": r"^performance-control-output-[0-9]{6}$",
            },
            "destination": destination,
        },
    )
    properties.update(
        {
            "instrument_reference": _reference(
                "instrument_id", r"^schuss-instrument-[0-9]{6}$"
            ),
            "performance_control_graph_reference": _reference(
                "performance_control_graph_id",
                r"^schuss-performance-control-graph-[0-9]{6}$",
            ),
            "controller_sources": _set(controller_source, minimum=1),
            "instrument_mappings": _set(instrument_mapping, minimum=1),
        }
    )
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "performance-configuration-v0.schema.json",
        "title": "Schuss performance configuration v0",
        **_closed(
            (
                *required,
                "instrument_reference",
                "performance_control_graph_reference",
                "controller_sources",
                "instrument_mappings",
            ),
            properties,
        ),
    }


def _operation_request_schema() -> dict[str, Any]:
    payload = _closed(
        ("performance_configuration_reference",),
        {
            "performance_configuration_reference": _reference(
                "performance_configuration_id",
                r"^schuss-performance-configuration-[0-9]{6}$",
            )
        },
    )
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "operation-request-v17.schema.json",
        "title": "Schuss performance-control operation request v17",
        **_closed(
            ("schema_version", "canonical_profile", "operation", "payload"),
            {
                "schema_version": {"const": "schuss-operation-request-v17"},
                "canonical_profile": {"const": "schuss-canonical-json-v1"},
                "operation": {"const": "performance.inspect"},
                "payload": payload,
            },
        ),
    }


def _operation_result_schema() -> dict[str, Any]:
    source = copy.deepcopy(core.load_json(ROOT / "schemas/operation-result-v16.schema.json"))
    source["$id"] = "operation-result-v17.schema.json"
    source["title"] = "Schuss performance-control operation result v17"
    source["properties"]["schema_version"] = {
        "const": "schuss-operation-result-v17"
    }
    source["properties"]["operation"]["enum"] = [
        "invalid-request",
        "performance.inspect",
    ]
    return source


def _application_schema() -> dict[str, Any]:
    source = copy.deepcopy(
        core.load_json(ROOT / "schemas/application-capability-description-v9.schema.json")
    )
    source["$id"] = "application-capability-description-v10.schema.json"
    source["title"] = "Schuss application capability description v10"
    source["properties"]["schema_version"] = {
        "const": "application-capability-description-v10"
    }
    source["properties"]["description_version"] = {
        "const": "schuss-application-capability-description-v10"
    }
    operation = source["$defs"]["operationCapability"]["properties"]
    operation["operation"]["enum"] = sorted(
        set(operation["operation"]["enum"]) | {"performance.inspect"}
    )
    operation["domain_group"]["enum"] = sorted(
        set(operation["domain_group"]["enum"]) | {"performance"}
    )
    operation["request_schema_version"]["pattern"] = (
        r"^schuss-operation-request-v(?:[1-9]|1[0-7])$"
    )
    operation["result_schema_version"]["pattern"] = (
        r"^schuss-operation-result-v(?:[1-9]|1[0-7])$"
    )
    source["properties"]["operations"]["minItems"] = 45
    source["properties"]["operations"]["maxItems"] = 45
    return source


def _hash_record(record: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(record)
    result["content_hash"] = "sha256:" + "0" * 64
    result["content_hash"] = core.record_content_hash(result, schema)
    errors = core.schema_errors(result, schema, schema)
    if errors:
        raise ValueError("; ".join(errors))
    return result


def _exact_ref(record: Mapping[str, Any], id_field: str) -> dict[str, Any]:
    return {
        id_field: record[id_field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def _shape() -> dict[str, Any]:
    return {
        "value_kind": "continuous",
        "domain": {"minimum": "0", "maximum": "1", "unit": "normalized"},
    }


def _control_contracts(schema: dict[str, Any]) -> list[dict[str, Any]]:
    common = {
        "schema_version": "performance-control-contract-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "inputs": [
            {
                "facet_id": "performance-control-port-000001",
                "semantic_key": "input",
                "display_label": "Input",
                "shape": _shape(),
            }
        ],
        "outputs": [
            {
                "facet_id": "performance-control-port-000002",
                "semantic_key": "output",
                "display_label": "Output",
                "shape": _shape(),
            }
        ],
    }
    direct = {
        **copy.deepcopy(common),
        "performance_control_contract_id": "schuss-performance-control-contract-000001",
        "display_name": "Normalized direct control",
        "function_key": "normalized-direct",
        "parameters": [],
        "state_declarations": [],
    }
    slew = {
        **copy.deepcopy(common),
        "performance_control_contract_id": "schuss-performance-control-contract-000002",
        "display_name": "Normalized slew control",
        "function_key": "normalized-slew",
        "parameters": [
            {
                "parameter_id": "performance-control-parameter-000001",
                "semantic_key": "response",
                "display_label": "Response",
                "domain": {"minimum": "0", "maximum": "1", "unit": "normalized"},
                "default": "0.25",
            }
        ],
        "state_declarations": [
            {
                "state_id": "performance-control-state-000001",
                "semantic_key": "current-value",
                "value_kind": "continuous",
                "reset_policy": "declared-default",
            }
        ],
    }
    return [_hash_record(direct, schema), _hash_record(slew, schema)]


def _control_graph(
    schema: dict[str, Any], contracts: list[dict[str, Any]]
) -> dict[str, Any]:
    record = {
        "schema_version": "performance-control-graph-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "performance_control_graph_id": "schuss-performance-control-graph-000001",
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "display_name": "Motion and blend performance controls",
        "public_inputs": [
            {
                "facet_id": "performance-control-input-000001",
                "semantic_key": "motion-control",
                "display_label": "Motion Control",
                "shape": _shape(),
            },
            {
                "facet_id": "performance-control-input-000002",
                "semantic_key": "blend-control",
                "display_label": "Blend Control",
                "shape": _shape(),
            },
        ],
        "public_outputs": [
            {
                "facet_id": "performance-control-output-000001",
                "semantic_key": "motion",
                "display_label": "Motion",
                "shape": _shape(),
            },
            {
                "facet_id": "performance-control-output-000002",
                "semantic_key": "blend",
                "display_label": "Blend",
                "shape": _shape(),
            },
        ],
        "nodes": [
            {
                "node_id": "performance-control-node-000001",
                "contract_reference": _exact_ref(
                    contracts[0], "performance_control_contract_id"
                ),
                "parameter_values": [],
            },
            {
                "node_id": "performance-control-node-000002",
                "contract_reference": _exact_ref(
                    contracts[1], "performance_control_contract_id"
                ),
                "parameter_values": [
                    {
                        "parameter_id": "performance-control-parameter-000001",
                        "value": "0.25",
                    }
                ],
            },
        ],
        "connections": [
            {
                "connection_id": "performance-control-connection-000001",
                "source": {
                    "endpoint_kind": "graph-input",
                    "facet_id": "performance-control-input-000001",
                },
                "destination": {
                    "endpoint_kind": "node-input",
                    "node_id": "performance-control-node-000001",
                    "facet_id": "performance-control-port-000001",
                },
            },
            {
                "connection_id": "performance-control-connection-000002",
                "source": {
                    "endpoint_kind": "node-output",
                    "node_id": "performance-control-node-000001",
                    "facet_id": "performance-control-port-000002",
                },
                "destination": {
                    "endpoint_kind": "graph-output",
                    "facet_id": "performance-control-output-000001",
                },
            },
            {
                "connection_id": "performance-control-connection-000003",
                "source": {
                    "endpoint_kind": "graph-input",
                    "facet_id": "performance-control-input-000002",
                },
                "destination": {
                    "endpoint_kind": "node-input",
                    "node_id": "performance-control-node-000002",
                    "facet_id": "performance-control-port-000001",
                },
            },
            {
                "connection_id": "performance-control-connection-000004",
                "source": {
                    "endpoint_kind": "node-output",
                    "node_id": "performance-control-node-000002",
                    "facet_id": "performance-control-port-000002",
                },
                "destination": {
                    "endpoint_kind": "graph-output",
                    "facet_id": "performance-control-output-000002",
                },
            },
        ],
    }
    return _hash_record(record, schema)


def _instrument(
    schema: dict[str, Any], predecessor: dict[str, Any]
) -> dict[str, Any]:
    record = copy.deepcopy(predecessor)
    for field in (
        "device_profile_reference",
        "device_input_mappings",
        "device_feedback_mappings",
    ):
        record.pop(field)
    record.update(
        {
            "schema_version": "instrument-v1",
            "revision": 2,
            "content_hash": "sha256:" + "0" * 64,
            "lineage": {
                "status": "successor",
                "predecessor_reference": _exact_ref(predecessor, "instrument_id"),
            },
            "event_inputs": [],
        }
    )
    return _hash_record(record, schema)


def _configuration(
    *,
    schema: dict[str, Any],
    number: int,
    display_name: str,
    instrument: dict[str, Any],
    graph: dict[str, Any],
    source: dict[str, Any],
) -> dict[str, Any]:
    record = {
        "schema_version": "performance-configuration-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "performance_configuration_id": f"schuss-performance-configuration-{number:06d}",
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "display_name": display_name,
        "instrument_reference": _exact_ref(instrument, "instrument_id"),
        "performance_control_graph_reference": _exact_ref(
            graph, "performance_control_graph_id"
        ),
        "controller_sources": [source],
        "instrument_mappings": [
            {
                "mapping_id": "performance-instrument-mapping-000001",
                "source_graph_output_id": "performance-control-output-000001",
                "destination": {
                    "facet_kind": "parameter",
                    "facet_id": "instrument-parameter-000001",
                },
            },
            {
                "mapping_id": "performance-instrument-mapping-000002",
                "source_graph_output_id": "performance-control-output-000002",
                "destination": {
                    "facet_kind": "parameter",
                    "facet_id": "instrument-parameter-000002",
                },
            },
        ],
    }
    return _hash_record(record, schema)


def _records(
    schemas: Mapping[str, dict[str, Any]], parent: record_set_rules.LoadedRecordSet
) -> list[tuple[str, str, dict[str, Any]]]:
    predecessors = [
        record
        for record in parent.records["instrument"]
        if record["instrument_id"] == "schuss-instrument-000005"
        and record["revision"] == 1
        and record["schema_version"] == "instrument-v0"
    ]
    devices = [
        record
        for record in parent.records["device-profile"]
        if record["device_profile_id"] == "schuss-device-profile-000001"
        and record["revision"] == 2
    ]
    if len(predecessors) != 1 or len(devices) != 1:
        raise ValueError("Task 034 exact predecessor/device closure changed")
    contracts = _control_contracts(schemas["performance-control-contract-v0"])
    graph = _control_graph(schemas["performance-control-graph-v0"], contracts)
    instrument = _instrument(schemas["instrument-v1"], predecessors[0])
    gills_source = {
        "controller_source_id": "controller-source-000001",
        "source_kind": "device-profile",
        "device_profile_reference": _exact_ref(devices[0], "device_profile_id"),
        "bindings": [
            {
                "binding_id": "controller-binding-000001",
                "selector": {
                    "selector_kind": "device-input",
                    "slot_id": "device-input-000001",
                },
                "destination_graph_input_id": "performance-control-input-000001",
            },
            {
                "binding_id": "controller-binding-000002",
                "selector": {
                    "selector_kind": "device-input",
                    "slot_id": "device-input-000002",
                },
                "destination_graph_input_id": "performance-control-input-000002",
            },
        ],
    }
    midi_source = {
        "controller_source_id": "controller-source-000001",
        "source_kind": "midi",
        "protocol": "midi-1.0-channel-voice",
        "endpoint_role": "controller-input",
        "bindings": [
            {
                "binding_id": "controller-binding-000001",
                "selector": {
                    "message_kind": "control-change",
                    "channel": 1,
                    "controller_number": 1,
                },
                "destination_graph_input_id": "performance-control-input-000001",
            },
            {
                "binding_id": "controller-binding-000002",
                "selector": {
                    "message_kind": "control-change",
                    "channel": 1,
                    "controller_number": 2,
                },
                "destination_graph_input_id": "performance-control-input-000002",
            },
        ],
    }
    configurations = [
        _configuration(
            schema=schemas["performance-configuration-v0"],
            number=1,
            display_name="Gills motion and blend performance configuration",
            instrument=instrument,
            graph=graph,
            source=gills_source,
        ),
        _configuration(
            schema=schemas["performance-configuration-v0"],
            number=2,
            display_name="Portable MIDI CC motion and blend performance configuration",
            instrument=instrument,
            graph=graph,
            source=midi_source,
        ),
    ]
    result: list[tuple[str, str, dict[str, Any]]] = [
        ("instrument", "device-independent-effects-instrument.json", instrument),
        *(
            (
                "performance-control-contract",
                f"control-contract-{index:02d}.json",
                record,
            )
            for index, record in enumerate(contracts, start=1)
        ),
        ("performance-control-graph", "motion-blend-control-graph.json", graph),
        *(
            (
                "performance-configuration",
                f"performance-configuration-{index:02d}.json",
                record,
            )
            for index, record in enumerate(configurations, start=1)
        ),
    ]
    return result


def _stable_id(record: Mapping[str, Any]) -> str:
    for field in (
        "instrument_id",
        "performance_control_contract_id",
        "performance_control_graph_id",
        "performance_configuration_id",
    ):
        if field in record:
            return str(record[field])
    raise ValueError("Task 034 record has no stable ID")


def generated() -> tuple[dict[str, bytes], bytes, dict[str, Any]]:
    schemas = {
        "application-capability-description-v10": _application_schema(),
        "instrument-v1": _instrument_schema(),
        "operation-request-v17": _operation_request_schema(),
        "operation-result-v17": _operation_result_schema(),
        "performance-configuration-v0": _configuration_schema(),
        "performance-control-contract-v0": _control_contract_schema(),
        "performance-control-graph-v0": _control_graph_schema(),
    }
    files = {
        f"schemas/{name}.schema.json": _canonical_bytes(schema)
        for name, schema in schemas.items()
    }
    parent_loaded = record_set_rules.load_record_set(ROOT, PARENT)
    records = _records(schemas, parent_loaded)
    schema_for_record = {
        schema_version: schema for schema_version, schema in schemas.items()
    }
    for _, filename, record in records:
        schema = schema_for_record[record["schema_version"]]
        errors = core.schema_errors(record, schema, schema)
        if errors:
            raise ValueError(f"{filename}: {'; '.join(errors)}")
        files[f"contracts/task034/{filename}"] = _canonical_bytes(record)

    parent = parent_loaded.manifest
    schema_members = copy.deepcopy(parent["schema_members"])
    existing_schemas = {member["schema_version"] for member in schema_members}
    for name in sorted(SCHEMA_NAMES):
        if name in existing_schemas:
            raise ValueError(f"Task 034 schema collides with parent: {name}")
        path = f"schemas/{name}.schema.json"
        schema_members.append(
            {
                "schema_version": name,
                "portable_path": path,
                "byte_sha256": hashlib.sha256(files[path]).hexdigest(),
            }
        )

    record_members = copy.deepcopy(parent["record_members"])
    for kind, filename, record in records:
        path = f"contracts/task034/{filename}"
        record_members.append(
            {
                "record_kind": kind,
                "stable_id": _stable_id(record),
                "revision": record["revision"],
                "content_hash": record["content_hash"],
                "portable_path": path,
                "byte_sha256": hashlib.sha256(files[path]).hexdigest(),
            }
        )
    manifest_schema = core.load_json(ROOT / record_set_rules.RECORD_SET_SCHEMA)
    manifest = {
        "schema_version": "record-set-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "record_set_id": RECORD_SET_ID,
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "purpose": "prospective-task",
        "parent_reference": {"status": "included", **parent_loaded.reference},
        "schema_members": sorted(
            schema_members,
            key=lambda item: (item["byte_sha256"], item["portable_path"]),
        ),
        "record_members": sorted(
            record_members,
            key=lambda item: (
                item["record_kind"],
                item["stable_id"],
                item["revision"],
                item["content_hash"],
            ),
        ),
        "enforced_directories": sorted(
            set(parent["enforced_directories"]) | {"contracts/task034"}
        ),
    }
    errors = core.schema_errors(manifest, manifest_schema, manifest_schema)
    if errors:
        raise ValueError("; ".join(errors))
    manifest["content_hash"] = core.record_content_hash(manifest, manifest_schema)
    summary = {
        "schema_version": "task034-generation-summary-v1",
        "status": "valid",
        "record_set_reference": {
            key: manifest[key]
            for key in ("record_set_id", "revision", "content_hash")
        },
        "added_schema_versions": list(SCHEMA_NAMES),
        "semantic_records_added": len(records),
        "native_build_or_device_access_performed": False,
    }
    return files, _canonical_bytes(manifest), summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files, manifest, summary = generated()
    stale: list[str] = []
    for relative, data in sorted(files.items()):
        destination = ROOT / relative
        if args.check:
            if not destination.exists() or destination.read_bytes() != data:
                stale.append(relative)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_bytes() != manifest:
            stale.append(str(OUTPUT.relative_to(ROOT)))
        if stale:
            raise SystemExit("stale generated files: " + ", ".join(stale))
    else:
        OUTPUT.write_bytes(manifest)
    print(core.canonical_json(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
