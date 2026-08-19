#!/usr/bin/env python3
"""Generate Task 032 variable-host-runtime contracts and exact allocation."""

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


PARENT = ROOT / "contracts/record-sets/ui-desktop-workspace-shell-v1.json"
OUTPUT = ROOT / "contracts/record-sets/task032-variable-host-runtime-v1.json"
TASK_DIR = ROOT / "contracts/task032"
RECORD_SET_ID = "schuss-record-set-000029"
HOST_REQUEST_ID = "schuss-build-request-000007"
FACTORY_IDS = (
    "schuss.rt.crossfade-q27-v0",
    "schuss.rt.output-q27-v0",
    "schuss.rt.pwm-q27-v0",
    "schuss.rt.saw-q27-v0",
    "schuss.rt.smooth-q27-v0",
    "schuss.rt.soft-q27-v0",
    "schuss.rt.vca-q27-v0",
)
ROLE_NAMES = ("crossfade", "output", "pwm", "saw", "smooth", "soft", "vca")
SCHEMA_NAMES = (
    "application-capability-description-v9",
    "host-engine-protocol-v1",
    "host-runtime-observation-v1",
    "host-runtime-package-v1",
    "operation-request-v16",
    "operation-result-v16",
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


def _content_hash() -> dict[str, Any]:
    return {"type": "string", "pattern": r"^sha256:[0-9a-f]{64}$"}


def _raw_hash() -> dict[str, Any]:
    return {"type": "string", "pattern": r"^[0-9a-f]{64}$"}


def _reference(id_field: str, pattern: str) -> dict[str, Any]:
    return _closed(
        (id_field, "revision", "content_hash"),
        {
            id_field: {"type": "string", "pattern": pattern},
            "revision": {"type": "integer", "minimum": 1},
            "content_hash": _content_hash(),
        },
    )


def _input_schema() -> dict[str, Any]:
    common = {
        "facet_id": {
            "type": "string",
            "pattern": r"^component-port-[0-9]{6}$",
        },
    }
    return {
        "oneOf": [
            _closed(
                ("facet_id", "source_kind", "buffer_index"),
                {
                    **common,
                    "source_kind": {"const": "buffer"},
                    "buffer_index": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 127,
                    },
                },
            ),
            _closed(
                ("facet_id", "source_kind", "value_q", "fractional_bits"),
                {
                    **common,
                    "source_kind": {"const": "constant"},
                    "value_q": {
                        "type": "integer",
                        "minimum": -(1 << 31),
                        "maximum": (1 << 31) - 1,
                    },
                    "fractional_bits": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 30,
                    },
                },
            ),
        ]
    }


def _runtime_package_schema() -> dict[str, Any]:
    reference_node = {
        "node_id": {"type": "string", "pattern": r"^graph-node-[0-9]{6}$"},
        "facet_id": {
            "type": "string",
            "pattern": r"^component-port-[0-9]{6}$",
        },
    }
    node = _closed(
        (
            "node_id",
            "role",
            "contract_reference",
            "binding_reference",
            "factory_id",
            "inputs",
            "outputs",
            "parameters",
            "state_offset_bytes",
            "state_size_bytes",
            "state_alignment_bytes",
        ),
        {
            "node_id": reference_node["node_id"],
            "role": {"enum": list(ROLE_NAMES)},
            "contract_reference": _reference(
                "component_contract_id", r"^schuss-component-contract-[0-9]{6}$"
            ),
            "binding_reference": _reference(
                "implementation_id", r"^schuss-implementation-[0-9]{6}$"
            ),
            "factory_id": {"enum": list(FACTORY_IDS)},
            "inputs": {
                "type": "array",
                "x-schuss-array-kind": "sequence",
                "maxItems": 3,
                "items": _input_schema(),
            },
            "outputs": {
                "type": "array",
                "x-schuss-array-kind": "sequence",
                "maxItems": 2,
                "items": _closed(
                    ("facet_id", "buffer_index"),
                    {
                        "facet_id": reference_node["facet_id"],
                        "buffer_index": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 127,
                        },
                    },
                ),
            },
            "parameters": {
                "type": "array",
                "x-schuss-array-kind": "set",
                "uniqueItems": True,
                "maxItems": 4,
                "items": _closed(
                    ("facet_id", "value_q"),
                    {
                        "facet_id": {
                            "type": "string",
                            "pattern": r"^component-parameter-[0-9]{6}$",
                        },
                        "value_q": {
                            "type": "integer",
                            "minimum": -(1 << 31),
                            "maximum": (1 << 31) - 1,
                        },
                    },
                ),
            },
            "state_offset_bytes": {"type": "integer", "minimum": 0},
            "state_size_bytes": {
                "type": "integer",
                "minimum": 0,
                "maximum": 4096,
            },
            "state_alignment_bytes": {"enum": [1, 4, 8, 16]},
        },
    )
    connection = _closed(
        ("connection_id", "source", "destination", "buffer_index"),
        {
            "connection_id": {
                "type": "string",
                "pattern": r"^graph-connection-[0-9]{6}$",
            },
            "source": _closed(("node_id", "facet_id"), reference_node),
            "destination": _closed(("node_id", "facet_id"), reference_node),
            "buffer_index": {
                "type": "integer",
                "minimum": 0,
                "maximum": 127,
            },
        },
    )
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "host-runtime-package-v1.schema.json",
        "title": "Schuss bounded variable host runtime package v1",
        **_closed(
            (
                "schema_version",
                "canonical_profile",
                "derived",
                "authoritative",
                "content_hash",
                "runtime_abi",
                "engine_protocol_abi",
                "factory_registry_version",
                "numeric_profile",
                "project_reference",
                "graph_reference",
                "instrument_reference",
                "host_build_request_reference",
                "compute_target_reference",
                "backend_reference",
                "source_plan_sha256",
                "sample_rate_hz",
                "max_block_frames",
                "control_period_frames",
                "block_policy",
                "input_channels",
                "output_channels",
                "latency_frames",
                "tail_frames",
                "seed",
                "limits",
                "memory_plan",
                "nodes",
                "connections",
                "schedule",
                "outputs",
                "event_contract",
                "exclusions",
            ),
            {
                "schema_version": {"const": "host-runtime-package-v1"},
                "canonical_profile": {"const": "schuss-canonical-json-v1"},
                "derived": {"const": True},
                "authoritative": {"const": False},
                "content_hash": _content_hash(),
                "runtime_abi": {"const": "schuss-rt-abi-v1"},
                "engine_protocol_abi": {
                    "const": "schuss-audio-engine-protocol-v1"
                },
                "factory_registry_version": {
                    "const": "schuss-rt-factory-registry-v1"
                },
                "numeric_profile": {"const": "schuss-host-q27-reference-v0"},
                "project_reference": _reference(
                    "project_id", r"^schuss-project-[0-9]{6}$"
                ),
                "graph_reference": _reference(
                    "graph_id", r"^schuss-graph-[0-9]{6}$"
                ),
                "instrument_reference": _reference(
                    "instrument_id", r"^schuss-instrument-[0-9]{6}$"
                ),
                "host_build_request_reference": _reference(
                    "build_request_id", r"^schuss-build-request-[0-9]{6}$"
                ),
                "compute_target_reference": _reference(
                    "compute_target_id", r"^schuss-compute-target-[0-9]{6}$"
                ),
                "backend_reference": _reference(
                    "backend_id", r"^schuss-backend-[0-9]{6}$"
                ),
                "source_plan_sha256": _raw_hash(),
                "sample_rate_hz": {"const": 48000},
                "max_block_frames": {"const": 512},
                "control_period_frames": {"const": 16},
                "block_policy": {"const": "bounded-variable-with-final-partial"},
                "input_channels": {"const": 0},
                "output_channels": {"const": 2},
                "latency_frames": {"const": 0},
                "tail_frames": {"const": 0},
                "seed": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 4294967295,
                },
                "limits": _closed(
                    (
                        "node_count",
                        "connection_count",
                        "buffer_count",
                        "state_bytes",
                        "parameter_count",
                        "event_count",
                        "schedule_length",
                    ),
                    {
                        "node_count": {"const": 64},
                        "connection_count": {"const": 192},
                        "buffer_count": {"const": 128},
                        "state_bytes": {"const": 65536},
                        "parameter_count": {"const": 256},
                        "event_count": {"const": 1024},
                        "schedule_length": {"const": 64},
                    },
                ),
                "memory_plan": _closed(
                    (
                        "state_bytes",
                        "state_alignment_bytes",
                        "buffer_count",
                        "buffer_frames",
                        "buffer_bytes",
                        "parameter_count",
                        "event_capacity",
                    ),
                    {
                        "state_bytes": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 65536,
                        },
                        "state_alignment_bytes": {"const": 16},
                        "buffer_count": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 128,
                        },
                        "buffer_frames": {"const": 512},
                        "buffer_bytes": {
                            "type": "integer",
                            "minimum": 2048,
                            "maximum": 262144,
                        },
                        "parameter_count": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 256,
                        },
                        "event_capacity": {"const": 1024},
                    },
                ),
                "nodes": {
                    "type": "array",
                    "x-schuss-array-kind": "sequence",
                    "minItems": 2,
                    "maxItems": 64,
                    "items": node,
                },
                "connections": {
                    "type": "array",
                    "x-schuss-array-kind": "set",
                    "minItems": 1,
                    "maxItems": 192,
                    "uniqueItems": True,
                    "items": connection,
                },
                "schedule": {
                    "type": "array",
                    "x-schuss-array-kind": "sequence",
                    "minItems": 2,
                    "maxItems": 64,
                    "uniqueItems": True,
                    "items": reference_node["node_id"],
                },
                "outputs": _closed(
                    ("node_id", "left_buffer", "right_buffer"),
                    {
                        "node_id": reference_node["node_id"],
                        "left_buffer": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 127,
                        },
                        "right_buffer": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 127,
                        },
                    },
                ),
                "event_contract": _closed(
                    ("capacity", "ordering", "accepted_kinds", "overflow_policy"),
                    {
                        "capacity": {"const": 1024},
                        "ordering": {"const": "frame-offset-then-sequence"},
                        "accepted_kinds": {
                            "type": "array",
                            "x-schuss-array-kind": "set",
                            "minItems": 2,
                            "maxItems": 2,
                            "uniqueItems": True,
                            "items": {"enum": ["midi-message", "parameter-q27"]},
                        },
                        "overflow_policy": {"const": "drop-newest-and-count"},
                    },
                ),
                "exclusions": {
                    "type": "array",
                    "x-schuss-array-kind": "set",
                    "minItems": 1,
                    "uniqueItems": True,
                    "items": {"type": "string", "minLength": 1},
                },
            },
        ),
    }


def _runtime_observation_schema() -> dict[str, Any]:
    source = core.load_json(ROOT / "schemas/host-runtime-observation-v0.schema.json")
    source["$id"] = "host-runtime-observation-v1.schema.json"
    source["title"] = "Schuss bounded variable host runtime observation v1"
    source["properties"]["schema_version"] = {
        "const": "host-runtime-observation-v1"
    }
    source["properties"]["toolchain"]["properties"]["runtime_abi"] = {
        "const": "schuss-rt-abi-v1"
    }
    graph_execution = _closed(
        (
            "node_count",
            "connection_count",
            "schedule_length",
            "buffer_count",
            "state_bytes",
            "factory_instance_counts",
        ),
        {
            "node_count": {"type": "integer", "minimum": 2, "maximum": 64},
            "connection_count": {
                "type": "integer",
                "minimum": 1,
                "maximum": 192,
            },
            "schedule_length": {
                "type": "integer",
                "minimum": 2,
                "maximum": 64,
            },
            "buffer_count": {
                "type": "integer",
                "minimum": 1,
                "maximum": 128,
            },
            "state_bytes": {
                "type": "integer",
                "minimum": 1,
                "maximum": 65536,
            },
            "factory_instance_counts": {
                "type": "array",
                "x-schuss-array-kind": "set",
                "uniqueItems": True,
                "items": _closed(
                    ("factory_id", "count"),
                    {
                        "factory_id": {"enum": list(FACTORY_IDS)},
                        "count": {"type": "integer", "minimum": 1, "maximum": 64},
                    },
                ),
            },
        },
    )
    source["required"].append("graph_execution")
    source["properties"]["graph_execution"] = graph_execution
    return source


def _engine_protocol_schema() -> dict[str, Any]:
    message_id = {"type": "string", "pattern": r"^engine-message-[0-9]{6}$"}
    session_id = {"type": "string", "pattern": r"^audio-session-[0-9]{6}$"}
    common = {
        "schema_version": {"const": "host-engine-protocol-v1"},
        "protocol_abi": {"const": "schuss-audio-engine-protocol-v1"},
        "message_id": message_id,
    }
    variants: list[dict[str, Any]] = []
    messages = (
        (
            "hello",
            _closed(
                ("runtime_abi", "package_schema_version"),
                {
                    "runtime_abi": {"const": "schuss-rt-abi-v1"},
                    "package_schema_version": {"const": "host-runtime-package-v1"},
                },
            ),
        ),
        (
            "devices.inspect",
            _closed(
                ("inspection_intent",),
                {"inspection_intent": {"const": "enumerate-local-audio-midi"}},
            ),
        ),
        (
            "package.prepare",
            _closed(
                ("package_path", "package_content_hash"),
                {
                    "package_path": {"type": "string", "minLength": 1},
                    "package_content_hash": _content_hash(),
                },
            ),
        ),
        (
            "session.start",
            _closed(
                ("sample_rate_hz", "block_frames"),
                {
                    "sample_rate_hz": {"const": 48000},
                    "block_frames": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 512,
                    },
                },
            ),
        ),
        ("session.inspect", _closed((), {})),
        ("session.stop", _closed((), {})),
        (
            "replacement.prepare",
            _closed(
                (
                    "audio_session_id",
                    "expected_engine_generation",
                    "expected_active_package_content_hash",
                    "successor_package_path",
                    "successor_package_content_hash",
                ),
                {
                    "audio_session_id": session_id,
                    "expected_engine_generation": {
                        "type": "integer",
                        "minimum": 1,
                    },
                    "expected_active_package_content_hash": _content_hash(),
                    "successor_package_path": {"type": "string", "minLength": 1},
                    "successor_package_content_hash": _content_hash(),
                },
            ),
        ),
        (
            "replacement.activate",
            _closed(
                (
                    "audio_session_id",
                    "expected_engine_generation",
                    "expected_active_package_content_hash",
                    "successor_package_content_hash",
                    "activation_policy",
                ),
                {
                    "audio_session_id": session_id,
                    "expected_engine_generation": {
                        "type": "integer",
                        "minimum": 1,
                    },
                    "expected_active_package_content_hash": _content_hash(),
                    "successor_package_content_hash": _content_hash(),
                    "activation_policy": {"const": "next-block-reset-state"},
                },
            ),
        ),
        (
            "replacement.cancel",
            _closed(
                (
                    "audio_session_id",
                    "expected_engine_generation",
                    "expected_active_package_content_hash",
                    "successor_package_content_hash",
                ),
                {
                    "audio_session_id": session_id,
                    "expected_engine_generation": {
                        "type": "integer",
                        "minimum": 1,
                    },
                    "expected_active_package_content_hash": _content_hash(),
                    "successor_package_content_hash": _content_hash(),
                },
            ),
        ),
        ("shutdown", _closed((), {})),
    )
    for message_type, payload in messages:
        variants.append(
            _closed(
                ("schema_version", "protocol_abi", "message_id", "message_type", "payload"),
                {**common, "message_type": {"const": message_type}, "payload": payload},
            )
        )
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "host-engine-protocol-v1.schema.json",
        "title": "Schuss private audio engine protocol v1",
        "oneOf": variants,
    }


def _operation_request_schema() -> dict[str, Any]:
    common = {
        "schema_version": {"const": "schuss-operation-request-v16"},
        "canonical_profile": {"const": "schuss-canonical-json-v1"},
    }
    project_ref = _reference("project_id", r"^schuss-project-[0-9]{6}$")
    request_ref = _reference(
        "build_request_id", r"^schuss-build-request-[0-9]{6}$"
    )
    session_id = {
        "type": "string",
        "pattern": r"^(?:host-render|audio-session)-[0-9]{6}$",
    }
    variants = (
        (
            "host.render.start",
            _closed(
                (
                    "project_reference",
                    "host_build_request_reference",
                    "render_frames",
                    "block_frames",
                    "render_intent",
                ),
                {
                    "project_reference": project_ref,
                    "host_build_request_reference": request_ref,
                    "render_frames": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 480000,
                    },
                    "block_frames": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 512,
                    },
                    "render_intent": {"const": "offline-render"},
                },
            ),
        ),
        (
            "host.render.inspect",
            _closed(("render_session_id",), {"render_session_id": session_id}),
        ),
        (
            "audio.devices.inspect",
            _closed(
                ("inspection_intent",),
                {"inspection_intent": {"const": "enumerate-local-audio-midi"}},
            ),
        ),
        (
            "audio.session.start",
            _closed(
                (
                    "project_reference",
                    "host_build_request_reference",
                    "sample_rate_hz",
                    "block_frames",
                    "start_intent",
                ),
                {
                    "project_reference": project_ref,
                    "host_build_request_reference": request_ref,
                    "sample_rate_hz": {"const": 48000},
                    "block_frames": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 512,
                    },
                    "start_intent": {"const": "start-local-audio-session"},
                },
            ),
        ),
        (
            "audio.session.inspect",
            _closed(("audio_session_id",), {"audio_session_id": session_id}),
        ),
        (
            "audio.session.stop",
            _closed(
                ("audio_session_id", "stop_intent"),
                {
                    "audio_session_id": session_id,
                    "stop_intent": {"const": "stop-local-audio-session"},
                },
            ),
        ),
        (
            "audio.session.replace",
            _closed(
                (
                    "audio_session_id",
                    "expected_engine_generation",
                    "expected_active_package_content_hash",
                    "successor_project_reference",
                    "successor_host_build_request_reference",
                    "replacement_intent",
                ),
                {
                    "audio_session_id": session_id,
                    "expected_engine_generation": {
                        "type": "integer",
                        "minimum": 1,
                    },
                    "expected_active_package_content_hash": _content_hash(),
                    "successor_project_reference": project_ref,
                    "successor_host_build_request_reference": request_ref,
                    "replacement_intent": {
                        "const": "prepare-and-activate-next-block-reset-state"
                    },
                },
            ),
        ),
    )
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "operation-request-v16.schema.json",
        "title": "Schuss variable host runtime operation request v16",
        "oneOf": [
            _closed(
                ("schema_version", "canonical_profile", "operation", "payload"),
                {**common, "operation": {"const": operation}, "payload": payload},
            )
            for operation, payload in variants
        ],
    }


def _operation_result_schema() -> dict[str, Any]:
    source = core.load_json(ROOT / "schemas/operation-result-v15.schema.json")
    source["$id"] = "operation-result-v16.schema.json"
    source["title"] = "Schuss variable host runtime operation result v16"
    source["properties"]["schema_version"] = {
        "const": "schuss-operation-result-v16"
    }
    source["properties"]["operation"]["enum"] = [
        "audio.devices.inspect",
        "audio.session.inspect",
        "audio.session.replace",
        "audio.session.start",
        "audio.session.stop",
        "host.render.inspect",
        "host.render.start",
        "invalid-request",
    ]
    return source


def _application_schema() -> dict[str, Any]:
    source = core.load_json(
        ROOT / "schemas/application-capability-description-v8.schema.json"
    )
    source["$id"] = "application-capability-description-v9.schema.json"
    source["title"] = "Schuss application capability description v9"
    source["properties"]["schema_version"] = {
        "const": "application-capability-description-v9"
    }
    source["properties"]["description_version"] = {
        "const": "schuss-application-capability-description-v9"
    }
    operation = source["$defs"]["operationCapability"]["properties"]
    operation["operation"]["enum"] = sorted(
        set(operation["operation"]["enum"]) | {"audio.session.replace"}
    )
    operation["request_schema_version"]["pattern"] = (
        r"^schuss-operation-request-v(?:[1-9]|1[0-6])$"
    )
    operation["result_schema_version"]["pattern"] = (
        r"^schuss-operation-result-v(?:[1-9]|1[0-6])$"
    )
    gate_enum = source["$defs"]["gateSet"]["items"]["enum"]
    source["$defs"]["gateSet"]["items"]["enum"] = sorted(
        set(gate_enum)
        | {
            "expected-active-package",
            "expected-engine-generation",
            "exact-successor-project",
            "reset-state-replacement-intent",
        }
    )
    source["properties"]["operations"]["minItems"] = 44
    source["properties"]["operations"]["maxItems"] = 44
    return source


def _hash_record(record: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(record)
    result["content_hash"] = "sha256:" + "0" * 64
    result["content_hash"] = core.record_content_hash(result, schema)
    errors = core.schema_errors(result, schema, schema)
    if errors:
        raise ValueError("; ".join(errors))
    return result


def generated() -> tuple[dict[str, bytes], bytes, dict[str, Any]]:
    schemas = {
        "application-capability-description-v9": _application_schema(),
        "host-engine-protocol-v1": _engine_protocol_schema(),
        "host-runtime-observation-v1": _runtime_observation_schema(),
        "host-runtime-package-v1": _runtime_package_schema(),
        "operation-request-v16": _operation_request_schema(),
        "operation-result-v16": _operation_result_schema(),
    }
    files = {
        f"schemas/{name}.schema.json": _canonical_bytes(schema)
        for name, schema in schemas.items()
    }
    parent_loaded = record_set_rules.load_record_set(ROOT, PARENT)
    parent = parent_loaded.manifest
    requests = [
        record
        for record in parent_loaded.records["request"]
        if record["build_request_id"] == "schuss-build-request-000006"
        and record["revision"] == 1
    ]
    if len(requests) != 1:
        raise ValueError("Task 032 requires one exact Task 031 host request")
    host_request = copy.deepcopy(requests[0])
    host_request["build_request_id"] = HOST_REQUEST_ID
    host_request = _hash_record(host_request, parent_loaded.schemas["build-request-v0"])
    request_path = "contracts/task032/variable-host-template-request.json"
    files[request_path] = _canonical_bytes(host_request)

    schema_members = copy.deepcopy(parent["schema_members"])
    existing_schemas = {member["schema_version"] for member in schema_members}
    for name in sorted(SCHEMA_NAMES):
        if name in existing_schemas:
            raise ValueError(f"Task 032 schema collides with parent: {name}")
        schema_path = f"schemas/{name}.schema.json"
        schema_members.append(
            {
                "schema_version": name,
                "portable_path": schema_path,
                "byte_sha256": hashlib.sha256(files[schema_path]).hexdigest(),
            }
        )

    record_members = copy.deepcopy(parent["record_members"])
    record_members.append(
        {
            "record_kind": "request",
            "stable_id": HOST_REQUEST_ID,
            "revision": 1,
            "content_hash": host_request["content_hash"],
            "portable_path": request_path,
            "byte_sha256": hashlib.sha256(files[request_path]).hexdigest(),
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
            set(parent["enforced_directories"]) | {"contracts/task032"}
        ),
    }
    errors = core.schema_errors(manifest, manifest_schema, manifest_schema)
    if errors:
        raise ValueError("; ".join(errors))
    manifest["content_hash"] = core.record_content_hash(manifest, manifest_schema)
    summary = {
        "schema_version": "task032-generation-summary-v1",
        "status": "valid",
        "record_set_reference": {
            key: manifest[key]
            for key in ("record_set_id", "revision", "content_hash")
        },
        "added_schema_versions": list(SCHEMA_NAMES),
        "semantic_records_added": 1,
        "new_target_backend_binding_or_evidence_records": 0,
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
