#!/usr/bin/env python3
"""Generate Task 031A host-runtime contracts and exact semantic allocation."""

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

from packages.schuss_core.effects_profile_frontend import (  # noqa: E402
    DIRECT_BINDINGS,
    ROLE_CONTRACTS,
    ROLE_OPCODES,
    profile_reference,
)
from tools.contracts import record_set_rules  # noqa: E402
from tools.contracts import validator_core as core  # noqa: E402


PARENT = ROOT / "contracts/record-sets/ai-sonic-authoring-v1.json"
OUTPUT = ROOT / "contracts/record-sets/task031-desktop-host-runtime-v1.json"
TASK_DIR = ROOT / "contracts/task031"

TASK031_COMMIT = "ce3568d8316830ae1eee1814872f0c164921018a"
TASK031_CONTRACT_SHA256 = "22c4f484c263e326aa005f21a2ee954e1d309acbfbd559bf4e89f672f2ef97b0"
JUCE_TAG = "8.0.15"
JUCE_COMMIT = "91ad83ae34a81e0833b1a2b0866f54846370ae53"
JUCE_ARCHIVE_SHA256 = "04f8d5055382582c757be9da069ea98338005f98248facd9c2804435ac853e70"

HOST_TARGET_ID = "schuss-compute-target-000002"
HOST_BACKEND_ID = "schuss-backend-000003"
HOST_REQUEST_ID = "schuss-build-request-000006"
HOST_RECORD_SET_ID = "schuss-record-set-000027"

ROLE_ORDER = ("saw", "pwm", "soft", "smooth", "crossfade", "vca", "output")
HOST_BINDING_IDS = {
    role: f"schuss-implementation-{162 + index:06d}"
    for index, role in enumerate(ROLE_ORDER)
}
HOST_ELIGIBILITY_IDS = {
    role: f"schuss-binding-eligibility-{48 + index:06d}"
    for index, role in enumerate(ROLE_ORDER)
}
HOST_EVIDENCE_IDS = {
    role: f"schuss-evidence-claim-{75 + index:06d}"
    for index, role in enumerate(ROLE_ORDER)
}
HOST_FACTORY_IDS = {
    role: f"schuss.rt.{role.replace('_', '-')}-q27-v0" for role in ROLE_ORDER
}

SCHEMA_NAMES = (
    "application-capability-description-v7",
    "compute-target-v1",
    "host-engine-protocol-v0",
    "host-runtime-observation-v0",
    "host-runtime-package-v0",
    "operation-request-v14",
    "operation-result-v14",
    "third-party-source-lock-v0",
)


def _canonical_bytes(value: object) -> bytes:
    return (core.canonical_json(value) + "\n").encode("utf-8")


def _closed(required: Iterable[str], properties: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "type": "object",
        "required": list(required),
        "properties": dict(properties),
        "additionalProperties": False,
    }


def _content_hash_schema() -> dict[str, Any]:
    return {"type": "string", "pattern": r"^sha256:[0-9a-f]{64}$"}


def _raw_hash_schema() -> dict[str, Any]:
    return {"type": "string", "pattern": r"^[0-9a-f]{64}$"}


def _reference(id_field: str, id_pattern: str) -> dict[str, Any]:
    return _closed(
        (id_field, "revision", "content_hash"),
        {
            id_field: {"type": "string", "pattern": id_pattern},
            "revision": {"type": "integer", "minimum": 1},
            "content_hash": _content_hash_schema(),
        },
    )


def _compute_target_schema() -> dict[str, Any]:
    schema = core.load_json(ROOT / "schemas/compute-target-v0.schema.json")
    schema["$id"] = "compute-target-v1.schema.json"
    schema["title"] = "Schuss desktop host compute target v1"
    schema["properties"]["schema_version"] = {"const": "compute-target-v1"}
    schema["properties"]["target_kind"] = {"const": "desktop-audio-host"}
    schema["$defs"]["memoryRegion"]["properties"]["budget_kind"] = {
        "enum": ["linker-region-budget", "runtime-preallocation-budget"]
    }
    return schema


def _source_lock_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "third-party-source-lock-v0.schema.json",
        "title": "Schuss pinned third-party source lock v0",
        **_closed(
            (
                "schema_version",
                "canonical_profile",
                "third_party_source_lock_id",
                "revision",
                "content_hash",
                "dependency",
                "source",
                "modules",
                "use_boundary",
                "distribution_review_status",
            ),
            {
                "schema_version": {"const": "third-party-source-lock-v0"},
                "canonical_profile": {"const": "schuss-canonical-json-v1"},
                "third_party_source_lock_id": {
                    "type": "string",
                    "pattern": r"^schuss-third-party-source-lock-[0-9]{6}$",
                },
                "revision": {"type": "integer", "minimum": 1},
                "content_hash": _content_hash_schema(),
                "dependency": {"const": "juce"},
                "source": _closed(
                    ("repository_url", "tag", "commit", "archive_url", "archive_sha256"),
                    {
                        "repository_url": {"const": "https://github.com/juce-framework/JUCE.git"},
                        "tag": {"type": "string", "pattern": r"^[0-9]+\.[0-9]+\.[0-9]+$"},
                        "commit": {"type": "string", "pattern": r"^[0-9a-f]{40}$"},
                        "archive_url": {"type": "string", "pattern": r"^https://github\.com/juce-framework/JUCE/archive/[0-9a-f]{40}\.tar\.gz$"},
                        "archive_sha256": _raw_hash_schema(),
                    },
                ),
                "modules": {
                    "type": "array",
                    "x-schuss-array-kind": "set",
                    "minItems": 1,
                    "uniqueItems": True,
                    "items": {"enum": ["juce_audio_basics", "juce_audio_devices", "juce_audio_utils", "juce_core", "juce_data_structures", "juce_events"]},
                },
                "use_boundary": {"const": "private-personal-development-only"},
                "distribution_review_status": {"const": "required-before-distribution"},
            },
        ),
    }


def _runtime_package_schema() -> dict[str, Any]:
    node = _closed(
        (
            "node_id",
            "role",
            "contract_reference",
            "binding_reference",
            "factory_id",
            "input_buffers",
            "output_buffers",
            "parameters",
            "state_offset_bytes",
            "state_size_bytes",
        ),
        {
            "node_id": {"type": "string", "pattern": r"^graph-node-[0-9]{6}$"},
            "role": {"enum": list(ROLE_ORDER)},
            "contract_reference": _reference("component_contract_id", r"^schuss-component-contract-[0-9]{6}$"),
            "binding_reference": _reference("implementation_id", r"^schuss-implementation-[0-9]{6}$"),
            "factory_id": {"enum": sorted(HOST_FACTORY_IDS.values())},
            "input_buffers": {
                "type": "array",
                "x-schuss-array-kind": "sequence",
                "maxItems": 3,
                "items": {"type": "integer", "minimum": 0, "maximum": 31},
            },
            "output_buffers": {
                "type": "array",
                "x-schuss-array-kind": "sequence",
                "maxItems": 2,
                "items": {"type": "integer", "minimum": 0, "maximum": 31},
            },
            "parameters": {
                "type": "array",
                "x-schuss-array-kind": "set",
                "uniqueItems": True,
                "items": _closed(
                    ("facet_id", "value_q"),
                    {
                        "facet_id": {"type": "string", "pattern": r"^component-(?:parameter|port)-[0-9]{6}$"},
                        "value_q": {"type": "integer", "minimum": -(1 << 31), "maximum": (1 << 31) - 1},
                    },
                ),
            },
            "state_offset_bytes": {"type": "integer", "minimum": 0},
            "state_size_bytes": {"type": "integer", "minimum": 0, "maximum": 4096},
        },
    )
    connection = _closed(
        ("connection_id", "source", "destination", "buffer_index"),
        {
            "connection_id": {"type": "string", "pattern": r"^graph-connection-[0-9]{6}$"},
            "source": _closed(
                ("node_id", "facet_id"),
                {
                    "node_id": {"type": "string", "pattern": r"^graph-node-[0-9]{6}$"},
                    "facet_id": {"type": "string", "pattern": r"^component-port-[0-9]{6}$"},
                },
            ),
            "destination": _closed(
                ("node_id", "facet_id"),
                {
                    "node_id": {"type": "string", "pattern": r"^graph-node-[0-9]{6}$"},
                    "facet_id": {"type": "string", "pattern": r"^component-port-[0-9]{6}$"},
                },
            ),
            "buffer_index": {"type": "integer", "minimum": 0, "maximum": 31},
        },
    )
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "host-runtime-package-v0.schema.json",
        "title": "Schuss canonical derived host runtime package v0",
    }
    schema.update(
        _closed(
            (
                "schema_version",
                "canonical_profile",
                "derived",
                "authoritative",
                "content_hash",
                "runtime_abi",
                "engine_protocol_abi",
                "numeric_profile",
                "project_reference",
                "graph_reference",
                "instrument_reference",
                "host_build_request_reference",
                "compute_target_reference",
                "backend_reference",
                "semantic_profile_reference",
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
                "memory_plan",
                "nodes",
                "connections",
                "schedule",
                "outputs",
                "event_contract",
                "exclusions",
            ),
            {
                "schema_version": {"const": "host-runtime-package-v0"},
                "canonical_profile": {"const": "schuss-canonical-json-v1"},
                "derived": {"const": True},
                "authoritative": {"const": False},
                "content_hash": _content_hash_schema(),
                "runtime_abi": {"const": "schuss-rt-abi-v0"},
                "engine_protocol_abi": {"const": "schuss-audio-engine-protocol-v0"},
                "numeric_profile": {"const": "schuss-host-q27-reference-v0"},
                "project_reference": _reference("project_id", r"^schuss-project-[0-9]{6}$"),
                "graph_reference": _reference("graph_id", r"^schuss-graph-[0-9]{6}$"),
                "instrument_reference": _reference("instrument_id", r"^schuss-instrument-[0-9]{6}$"),
                "host_build_request_reference": _reference("build_request_id", r"^schuss-build-request-[0-9]{6}$"),
                "compute_target_reference": _reference("compute_target_id", r"^schuss-compute-target-[0-9]{6}$"),
                "backend_reference": _reference("backend_id", r"^schuss-backend-[0-9]{6}$"),
                "semantic_profile_reference": _closed(
                    ("profile_id", "version", "content_hash"),
                    {
                        "profile_id": {"type": "string", "pattern": r"^schuss-semantic-profile-[0-9]{6}$"},
                        "version": {"type": "integer", "minimum": 1},
                        "content_hash": _content_hash_schema(),
                    },
                ),
                "source_plan_sha256": _raw_hash_schema(),
                "sample_rate_hz": {"const": 48000},
                "max_block_frames": {"const": 512},
                "control_period_frames": {"const": 16},
                "block_policy": {"const": "bounded-variable-with-final-partial"},
                "input_channels": {"const": 0},
                "output_channels": {"const": 2},
                "latency_frames": {"type": "integer", "minimum": 0},
                "tail_frames": {"type": "integer", "minimum": 0},
                "seed": {"type": "integer", "minimum": 0, "maximum": 4294967295},
                "memory_plan": _closed(
                    ("state_bytes", "buffer_count", "buffer_frames", "buffer_bytes", "event_capacity"),
                    {
                        "state_bytes": {"type": "integer", "minimum": 1, "maximum": 65536},
                        "buffer_count": {"type": "integer", "minimum": 1, "maximum": 32},
                        "buffer_frames": {"const": 512},
                        "buffer_bytes": {"type": "integer", "minimum": 1, "maximum": 65536},
                        "event_capacity": {"type": "integer", "minimum": 1, "maximum": 4096},
                    },
                ),
                "nodes": {
                    "type": "array",
                    "x-schuss-array-kind": "sequence",
                    "minItems": 7,
                    "maxItems": 7,
                    "items": node,
                },
                "connections": {
                    "type": "array",
                    "x-schuss-array-kind": "set",
                    "minItems": 7,
                    "maxItems": 7,
                    "uniqueItems": True,
                    "items": connection,
                },
                "schedule": {
                    "type": "array",
                    "x-schuss-array-kind": "sequence",
                    "minItems": 7,
                    "maxItems": 7,
                    "uniqueItems": True,
                    "items": {"type": "string", "pattern": r"^graph-node-[0-9]{6}$"},
                },
                "outputs": _closed(
                    ("left_buffer", "right_buffer"),
                    {
                        "left_buffer": {"type": "integer", "minimum": 0, "maximum": 31},
                        "right_buffer": {"type": "integer", "minimum": 0, "maximum": 31},
                    },
                ),
                "event_contract": _closed(
                    ("capacity", "ordering", "accepted_kinds", "overflow_policy"),
                    {
                        "capacity": {"type": "integer", "minimum": 1, "maximum": 4096},
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
        )
    )
    return schema


def _runtime_observation_schema() -> dict[str, Any]:
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "host-runtime-observation-v0.schema.json",
        "title": "Schuss bounded host runtime observation v0",
    }
    schema.update(
        _closed(
            (
                "schema_version",
                "canonical_profile",
                "content_hash",
                "observation_kind",
                "status",
                "package_content_hash",
                "configuration",
                "device",
                "toolchain",
                "output",
                "metrics",
                "diagnostics",
                "evidence_boundary",
            ),
            {
                "schema_version": {"const": "host-runtime-observation-v0"},
                "canonical_profile": {"const": "schuss-canonical-json-v1"},
                "content_hash": _content_hash_schema(),
                "observation_kind": {"enum": ["offline-render", "local-real-time-smoke"]},
                "status": {"enum": ["success", "failed", "unavailable"]},
                "package_content_hash": _content_hash_schema(),
                "configuration": _closed(
                    ("sample_rate_hz", "block_frames", "render_frames", "output_channels"),
                    {
                        "sample_rate_hz": {"type": "integer", "minimum": 1},
                        "block_frames": {"type": "integer", "minimum": 1, "maximum": 512},
                        "render_frames": {"type": "integer", "minimum": 0},
                        "output_channels": {"const": 2},
                    },
                ),
                "device": {
                    "oneOf": [
                        _closed(("status",), {"status": {"const": "not-opened"}}),
                        _closed(
                            ("status", "audio_device_name", "midi_input_count"),
                            {
                                "status": {"const": "opened"},
                                "audio_device_name": {"type": "string", "minLength": 1},
                                "midi_input_count": {"type": "integer", "minimum": 0},
                            },
                        ),
                        _closed(
                            ("status", "reason"),
                            {
                                "status": {"const": "unavailable"},
                                "reason": {"type": "string", "minLength": 1},
                            },
                        ),
                    ]
                },
                "toolchain": _closed(
                    ("compiler_id", "compiler_version", "target_triple", "runtime_abi"),
                    {
                        "compiler_id": {"type": "string", "minLength": 1},
                        "compiler_version": {"type": "string", "minLength": 1},
                        "target_triple": {"type": "string", "minLength": 1},
                        "runtime_abi": {"const": "schuss-rt-abi-v0"},
                    },
                ),
                "output": _closed(
                    ("media_type", "byte_length", "byte_sha256"),
                    {
                        "media_type": {"const": "audio/wav"},
                        "byte_length": {"type": "integer", "minimum": 0},
                        "byte_sha256": _raw_hash_schema(),
                    },
                ),
                "metrics": _closed(
                    ("processed_frames", "midi_events_delivered", "queue_overflows", "xruns", "callback_cpu_ratio_max", "callback_duration_us_max"),
                    {
                        "processed_frames": {"type": "integer", "minimum": 0},
                        "midi_events_delivered": {"type": "integer", "minimum": 0},
                        "queue_overflows": {"type": "integer", "minimum": 0},
                        "xruns": {"type": "integer", "minimum": 0},
                        "callback_cpu_ratio_max": {"type": "string", "pattern": r"^[0-9]+(?:\.[0-9]+)?$"},
                        "callback_duration_us_max": {"type": "integer", "minimum": 0},
                    },
                ),
                "diagnostics": {
                    "type": "array",
                    "x-schuss-array-kind": "sequence",
                    "items": _closed(
                        ("code", "severity", "message"),
                        {
                            "code": {"type": "string", "pattern": r"^[A-Z][A-Z0-9_]+$"},
                            "severity": {"enum": ["error", "warning", "info"]},
                            "message": {"type": "string", "minLength": 1},
                        },
                    ),
                },
                "evidence_boundary": _closed(
                    ("host_execution_only", "real_time_level_7_promoted", "audible_level_8_promoted", "ksoloti_equivalence_claimed", "release_readiness_claimed"),
                    {
                        "host_execution_only": {"const": True},
                        "real_time_level_7_promoted": {"const": False},
                        "audible_level_8_promoted": {"const": False},
                        "ksoloti_equivalence_claimed": {"const": False},
                        "release_readiness_claimed": {"const": False},
                    },
                ),
            },
        )
    )
    return schema


def _engine_protocol_schema() -> dict[str, Any]:
    message_id = {"type": "string", "pattern": r"^engine-message-[0-9]{6}$"}
    common = {
        "schema_version": {"const": "host-engine-protocol-v0"},
        "protocol_abi": {"const": "schuss-audio-engine-protocol-v0"},
        "message_id": message_id,
    }
    variants: list[dict[str, Any]] = []
    for message_type, payload in (
        ("hello", _closed(("runtime_abi", "package_schema_version"), {"runtime_abi": {"const": "schuss-rt-abi-v0"}, "package_schema_version": {"const": "host-runtime-package-v0"}})),
        ("devices.inspect", _closed(("inspection_intent",), {"inspection_intent": {"const": "enumerate-local-audio-midi"}})),
        ("package.prepare", _closed(("package_path", "package_content_hash"), {"package_path": {"type": "string", "minLength": 1}, "package_content_hash": _content_hash_schema()})),
        ("session.start", _closed(("sample_rate_hz", "block_frames"), {"sample_rate_hz": {"type": "integer", "minimum": 1}, "block_frames": {"type": "integer", "minimum": 1, "maximum": 512}})),
        ("session.inspect", _closed((), {})),
        ("session.stop", _closed((), {})),
        ("shutdown", _closed((), {})),
    ):
        variants.append(
            _closed(
                ("schema_version", "protocol_abi", "message_id", "message_type", "payload"),
                {**common, "message_type": {"const": message_type}, "payload": payload},
            )
        )
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "host-engine-protocol-v0.schema.json",
        "title": "Schuss private audio engine protocol v0",
        "oneOf": variants,
    }


def _operation_request_schema() -> dict[str, Any]:
    common = {
        "schema_version": {"const": "schuss-operation-request-v14"},
        "canonical_profile": {"const": "schuss-canonical-json-v1"},
    }
    project_ref = _reference("project_id", r"^schuss-project-[0-9]{6}$")
    session_id = {"type": "string", "pattern": r"^(?:host-render|audio-session)-[0-9]{6}$"}
    variants = [
        ("host.render.start", _closed(("project_reference", "render_frames", "block_frames", "render_intent"), {"project_reference": project_ref, "render_frames": {"type": "integer", "minimum": 1, "maximum": 480000}, "block_frames": {"type": "integer", "minimum": 1, "maximum": 512}, "render_intent": {"const": "offline-render"}})),
        ("host.render.inspect", _closed(("render_session_id",), {"render_session_id": session_id})),
        ("audio.devices.inspect", _closed(("inspection_intent",), {"inspection_intent": {"const": "enumerate-local-audio-midi"}})),
        ("audio.session.start", _closed(("project_reference", "sample_rate_hz", "block_frames", "start_intent"), {"project_reference": project_ref, "sample_rate_hz": {"type": "integer", "minimum": 1}, "block_frames": {"type": "integer", "minimum": 1, "maximum": 512}, "start_intent": {"const": "start-local-audio-session"}})),
        ("audio.session.inspect", _closed(("audio_session_id",), {"audio_session_id": session_id})),
        ("audio.session.stop", _closed(("audio_session_id", "stop_intent"), {"audio_session_id": session_id, "stop_intent": {"const": "stop-local-audio-session"}})),
    ]
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "operation-request-v14.schema.json",
        "title": "Schuss host render and audio session operation request v14",
        "oneOf": [
            _closed(
                ("schema_version", "canonical_profile", "operation", "payload"),
                {**common, "operation": {"const": operation}, "payload": payload},
            )
            for operation, payload in variants
        ],
    }


def _operation_result_schema() -> dict[str, Any]:
    schema = core.load_json(ROOT / "schemas/operation-result-v13.schema.json")
    schema["$id"] = "operation-result-v14.schema.json"
    schema["title"] = "Schuss host render and audio session operation result v14"
    schema["properties"]["schema_version"] = {"const": "schuss-operation-result-v14"}
    schema["properties"]["operation"]["enum"] = [
        "audio.devices.inspect",
        "audio.session.inspect",
        "audio.session.start",
        "audio.session.stop",
        "host.render.inspect",
        "host.render.start",
        "invalid-request",
    ]
    return schema


def _application_schema() -> dict[str, Any]:
    schema = core.load_json(ROOT / "schemas/application-capability-description-v6.schema.json")
    schema["$id"] = "application-capability-description-v7.schema.json"
    schema["title"] = "Schuss application capability description v7"
    schema["properties"]["schema_version"] = {"const": "application-capability-description-v7"}
    schema["properties"]["description_version"] = {"const": "schuss-application-capability-description-v7"}
    operation = schema["$defs"]["operationCapability"]["properties"]
    operation["operation"]["enum"] = sorted(
        set(operation["operation"]["enum"])
        | {
            "audio.devices.inspect",
            "audio.session.inspect",
            "audio.session.start",
            "audio.session.stop",
            "host.render.inspect",
            "host.render.start",
        }
    )
    operation["request_schema_version"]["pattern"] = r"^schuss-operation-request-v(?:[1-9]|1[0-4])$"
    operation["result_schema_version"]["pattern"] = r"^schuss-operation-result-v(?:[1-9]|1[0-4])$"
    operation["effect_class"]["enum"] = sorted(
        set(operation["effect_class"]["enum"])
        | {"audio-device-control", "audio-device-read", "host-artifact-write"}
    )
    operation["availability"]["enum"] = sorted(
        set(operation["availability"]["enum"])
        | {"requires-audio-session-service", "requires-host-runtime-service"}
    )
    context = schema["$defs"]["contextSet"]["items"]["enum"]
    schema["$defs"]["contextSet"]["items"]["enum"] = sorted(
        set(context) | {"exact-project-snapshot", "process-local-audio-session-service", "process-local-host-runtime-service"}
    )
    gates = schema["$defs"]["gateSet"]["items"]["enum"]
    schema["$defs"]["gateSet"]["items"]["enum"] = sorted(
        set(gates) | {"audio-device-intent", "exact-package", "exact-session", "offline-render-intent"}
    )
    schema["properties"]["operations"]["minItems"] = 41
    schema["properties"]["operations"]["maxItems"] = 41
    return schema


def _schemas() -> dict[str, dict[str, Any]]:
    return {
        "application-capability-description-v7": _application_schema(),
        "compute-target-v1": _compute_target_schema(),
        "host-engine-protocol-v0": _engine_protocol_schema(),
        "host-runtime-observation-v0": _runtime_observation_schema(),
        "host-runtime-package-v0": _runtime_package_schema(),
        "operation-request-v14": _operation_request_schema(),
        "operation-result-v14": _operation_result_schema(),
        "third-party-source-lock-v0": _source_lock_schema(),
    }


def _source_evidence() -> dict[str, Any]:
    return {
        "source_id": "schuss",
        "commit": TASK031_COMMIT,
        "path": "docs/DESKTOP_HOST_RUNTIME_IMPLEMENTATION_CONTRACT.md",
        "byte_sha256": TASK031_CONTRACT_SHA256,
        "claim_kind": "source-declared",
    }


def _hash_record(record: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(record)
    value["content_hash"] = "sha256:" + "0" * 64
    value["content_hash"] = core.record_content_hash(value, schema)
    errors = core.schema_errors(value, schema, schema)
    if errors:
        raise ValueError("; ".join(errors))
    return value


def _exact_ref(record: Mapping[str, Any], id_field: str) -> dict[str, Any]:
    return {
        id_field: record[id_field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def _find_exact(values: Iterable[dict[str, Any]], reference: Mapping[str, Any], id_field: str) -> dict[str, Any]:
    matches = [
        value
        for value in values
        if _exact_ref(value, id_field) == dict(reference)
    ]
    if len(matches) != 1:
        raise ValueError(f"expected one exact {reference}, found {len(matches)}")
    return matches[0]


def _semantic_records(
    parent: record_set_rules.LoadedRecordSet,
    schemas: Mapping[str, dict[str, Any]],
) -> list[tuple[str, str, dict[str, Any]]]:
    evidence = _source_evidence()
    source_lock = _hash_record(
        {
            "schema_version": "third-party-source-lock-v0",
            "canonical_profile": "schuss-canonical-json-v1",
            "third_party_source_lock_id": "schuss-third-party-source-lock-000001",
            "revision": 1,
            "content_hash": "sha256:" + "0" * 64,
            "dependency": "juce",
            "source": {
                "repository_url": "https://github.com/juce-framework/JUCE.git",
                "tag": JUCE_TAG,
                "commit": JUCE_COMMIT,
                "archive_url": f"https://github.com/juce-framework/JUCE/archive/{JUCE_COMMIT}.tar.gz",
                "archive_sha256": JUCE_ARCHIVE_SHA256,
            },
            "modules": ["juce_audio_basics", "juce_audio_devices", "juce_core", "juce_events"],
            "use_boundary": "private-personal-development-only",
            "distribution_review_status": "required-before-distribution",
        },
        schemas["third-party-source-lock-v0"],
    )

    environment_schema = parent.schemas["build-environment-v0"]
    toolchain = _hash_record(
        {
            "schema_version": "build-environment-v0",
            "canonical_profile": "schuss-canonical-json-v1",
            "build_environment_id": "schuss-build-environment-000003",
            "revision": 1,
            "content_hash": "sha256:" + "0" * 64,
            "environment_kind": "toolchain",
            "identity": {
                "status": "not-evaluated",
                "required_identity_kind": "apple-clang-cxx17",
                "target_triple": "arm64-apple-darwin",
                "known_constraints": ["C++17", "CMake 3.22 or newer", "private local native build"],
                "code": "HOST_TOOLCHAIN_EXACT_IDENTITY_PENDING_NATIVE_BUILD",
                "owner": "backend-owner",
                "earliest_task": "task-031",
                "rationale": "031A fixes only the portable contract; 031B and 031C record the exact local compiler used.",
                "question": "Which exact compiler bytes build the accepted native runtime and renderer?",
                "evidence_refs": [evidence],
            },
        },
        environment_schema,
    )
    runtime_environment = _hash_record(
        {
            "schema_version": "build-environment-v0",
            "canonical_profile": "schuss-canonical-json-v1",
            "build_environment_id": "schuss-build-environment-000004",
            "revision": 1,
            "content_hash": "sha256:" + "0" * 64,
            "environment_kind": "firmware-runtime-abi",
            "identity": {
                "status": "not-evaluated",
                "required_identity_kind": "schuss-rt-abi-v0",
                "target_triple": "portable-desktop-host",
                "known_constraints": ["JUCE-independent public ABI", "preallocated processing path", "host-runtime-package-v0"],
                "code": "HOST_RUNTIME_ABI_IMPLEMENTATION_PENDING",
                "owner": "backend-owner",
                "earliest_task": "task-031",
                "rationale": "031A allocates the ABI without claiming that the native runtime has executed.",
                "question": "Does the 031B implementation satisfy the complete schuss-rt ABI contract?",
                "evidence_refs": [evidence],
            },
        },
        environment_schema,
    )

    capability = _find_exact(
        parent.records["capability"],
        {
            "capability_vocabulary_id": "schuss-capability-vocabulary-000001",
            "revision": 1,
            "content_hash": "sha256:37770109d3aff88a67ab031a6ee21c49eb4d301e2933c4659efd38c4496cca92",
        },
        "capability_vocabulary_id",
    )
    target = _hash_record(
        {
            "schema_version": "compute-target-v1",
            "canonical_profile": "schuss-canonical-json-v1",
            "compute_target_id": HOST_TARGET_ID,
            "revision": 1,
            "content_hash": "sha256:" + "0" * 64,
            "target_kind": "desktop-audio-host",
            "display_name": "Portable desktop audio host",
            "processor": {
                "family": "desktop-host",
                "core": "portable-cpp17",
                "instruction_set": "native",
                "fpu": "native",
                "evidence_refs": [evidence],
            },
            "abi_constraints": {
                "target_triple": "portable-desktop-host",
                "float_abi": "not-applicable",
                "endianness": {
                    "status": "unresolved",
                    "code": "HOST_ENDIANNESS_NOT_REQUIRED_BY_Q27_PACKAGE_ABI",
                    "owner": "target-owner",
                    "earliest_task": "task-031",
                    "rationale": "Package values are canonical JSON and runtime buffers use native int32_t behind the ABI.",
                    "question": "Which native endianness is observed by each supported host build?",
                    "evidence_refs": [evidence],
                },
                "evidence_refs": [evidence],
            },
            "runtime_assumptions": [
                {"key": "audio-sample-rate", "value": 48000, "unit": "hertz", "fact_kind": "source-declared-runtime-constant", "evidence_refs": [evidence]},
                {"key": "audio-block-frames", "value": 512, "unit": "frames", "fact_kind": "source-declared-runtime-constant", "evidence_refs": [evidence]},
            ],
            "memory_regions": [
                {
                    "region_id": "target-memory-region-000006",
                    "address_start": "0x00000000",
                    "length_bytes": 16777216,
                    "alignment_bytes": 64,
                    "budget_kind": "runtime-preallocation-budget",
                    "resource_kinds": ["asset", "code", "data", "heap", "read-only-data", "stack"],
                    "evidence_refs": [evidence],
                }
            ],
            "asset_storage_limits": [],
            "firmware_runtime_reference": _exact_ref(runtime_environment, "build_environment_id"),
            "capability_vocabulary_reference": _exact_ref(capability, "capability_vocabulary_id"),
            "capability_declarations": [
                {"capability_key": key, "state": {"status": "supported", "value": True, "evidence_level": 2, "evidence_refs": [evidence]}}
                for key in ("audio-stream-fixed-q27", "control-stream-fixed-q27")
            ],
            "unresolved_facts": [],
        },
        schemas["compute-target-v1"],
    )

    backend_schema = parent.schemas["backend-v0"]
    template_backend = _find_exact(
        parent.records["backend"],
        {
            "backend_id": "schuss-backend-000002",
            "revision": 4,
            "content_hash": "sha256:e30889d5a33fca838086a0f3f8aacdcd065826d64fea396f74bda8aa164ee9db",
        },
        "backend_id",
    )
    backend_value = copy.deepcopy(template_backend)
    backend_value.update(
        {
            "backend_id": HOST_BACKEND_ID,
            "revision": 1,
            "content_hash": "sha256:" + "0" * 64,
            "display_name": "Portable desktop host runtime backend",
            "lowering_identity": {"backend_kind": "desktop-host-runtime", "contract_version": "task031-host-q27-v0"},
            "supported_realization_forms": ["native-cpp"],
            "target_pairings": [{"target_reference": _exact_ref(target, "compute_target_id"), "contract_state": "declared", "rationale": "The Task 031 host backend consumes only the exact seven-node profile and fails closed for every other node."}],
            "artifact_declarations": [
                {"artifact_kind": "build-package", "media_type": "application/vnd.schuss.host-runtime-package+json", "producer_stage": "artifact-generation"},
                {"artifact_kind": "resolution-plan", "media_type": "application/vnd.schuss.resolution-plan+json", "producer_stage": "implementation-resolution"},
                {"artifact_kind": "source-map", "media_type": "application/vnd.schuss.source-map+json", "producer_stage": "artifact-generation"},
            ],
            "toolchain_reference": _exact_ref(toolchain, "build_environment_id"),
            "firmware_runtime_reference": _exact_ref(runtime_environment, "build_environment_id"),
            "bridge_boundary": {"kind": "portable-host-runtime", "location": "packages/schuss_rt", "legacy_boundary_artifact": "build-package", "execution_status": "not-run"},
        }
    )
    backend = _hash_record(backend_value, backend_schema)

    parent_eligibility = {
        role: next(
            value
            for value in parent.records["eligibility"]
            if value["binding_reference"]["implementation_id"] == DIRECT_BINDINGS[role][0]
            and value["binding_reference"]["revision"] == DIRECT_BINDINGS[role][1]
            and value["contract_reference"] == ROLE_CONTRACTS[role]
        )
        for role in ROLE_ORDER
    }
    binding_schema = parent.schemas["implementation-binding-v1"]
    claim_schema = parent.schemas["evidence-claim-v0"]
    eligibility_schema = parent.schemas["binding-eligibility-v0"]
    producer_hash = "sha256:" + hashlib.sha256(b"schuss-task031-contract-validator-v1").hexdigest()
    candidate_bindings: dict[str, dict[str, Any]] = {}
    bindings: dict[str, dict[str, Any]] = {}
    claims: dict[str, dict[str, Any]] = {}
    eligibilities: dict[str, dict[str, Any]] = {}
    for index, role in enumerate(ROLE_ORDER):
        source_ref = parent_eligibility[role]["binding_reference"]
        source_binding = _find_exact(parent.records["implementation-binding"], source_ref, "implementation_id")
        binding_value = copy.deepcopy(source_binding)
        binding_value.update(
            {
                "schema_version": "implementation-binding-v1",
                "implementation_id": HOST_BINDING_IDS[role],
                "revision": 1,
                "content_hash": "sha256:" + "0" * 64,
                "evidence_refs": ["fixture:task031-host-runtime-contract"],
                "observed_dependencies": [],
                "realization": {"form": "native-cpp", "portable_symbol": HOST_FACTORY_IDS[role].replace(".", "_").replace("-", "_")},
                "selection_state": {
                    "status": "not-evaluated",
                    "reason": "target-backend-contracts-not-yet-implemented",
                    "owner": "task-007",
                    "rationale": "The separate Task 031 eligibility companion owns exact desktop-host selection; the binding alone is not runtime evidence.",
                },
            }
        )
        for mapping_index, mapping in enumerate(binding_value["facet_mappings"], 1):
            mapping["mapping_id"] = f"binding-map-{(162 + index) * 100 + mapping_index:06d}"
            mapping["implementation_seam"] = {
                "seam_kind": "native-symbol",
                "symbol": f"{HOST_FACTORY_IDS[role].replace('.', '_').replace('-', '_')}_{mapping_index:02d}",
            }
        candidate_bindings[role] = _hash_record(binding_value, binding_schema)
        claims[role] = _hash_record(
            {
                "schema_version": "evidence-claim-v0",
                "canonical_profile": "schuss-canonical-json-v1",
                "evidence_claim_id": HOST_EVIDENCE_IDS[role],
                "revision": 1,
                "content_hash": "sha256:" + "0" * 64,
                "level": 2,
                "level_name": "component-graph-resolution",
                "subject_reference": {"subject_kind": "semantic-record", "stable_id": candidate_bindings[role]["implementation_id"], "revision": 1, "content_hash": candidate_bindings[role]["content_hash"], "stage": "target-independent-graph-validation"},
                "method": "task031-exact-host-binding-allocation",
                "outcome": "passed",
                "evidence_inputs": [
                    {"input_kind": "semantic-record", "stable_id": ROLE_CONTRACTS[role]["component_contract_id"], "revision": ROLE_CONTRACTS[role]["revision"], "content_hash": ROLE_CONTRACTS[role]["content_hash"]},
                    {"input_kind": "semantic-record", "stable_id": candidate_bindings[role]["implementation_id"], "revision": 1, "content_hash": candidate_bindings[role]["content_hash"]},
                ],
                "limitations": ["This structural selection claim does not assert native build, execution, real-time headroom, audible behavior, Ksoloti equivalence, or release readiness."],
                "producer_identity": {"producer_kind": "validator", "producer_id": "schuss-task031-contract-validator", "version": "task031a-v1", "content_hash": producer_hash},
            },
            claim_schema,
        )
        promoted_value = copy.deepcopy(candidate_bindings[role])
        promoted_value.update(
            {
                "revision": 2,
                "content_hash": "sha256:" + "0" * 64,
                "evidence_refs": ["fixture:task031-host-runtime-contract"],
            }
        )
        bindings[role] = _hash_record(promoted_value, binding_schema)
        claim_ref = _exact_ref(claims[role], "evidence_claim_id")
        eligibilities[role] = _hash_record(
            {
                "schema_version": "binding-eligibility-v0",
                "canonical_profile": "schuss-canonical-json-v1",
                "binding_eligibility_id": HOST_ELIGIBILITY_IDS[role],
                "revision": 1,
                "content_hash": "sha256:" + "0" * 64,
                "binding_reference": _exact_ref(bindings[role], "implementation_id"),
                "contract_reference": copy.deepcopy(ROLE_CONTRACTS[role]),
                "allowed_pair": {"target_reference": _exact_ref(target, "compute_target_id"), "backend_reference": _exact_ref(backend, "backend_id"), "state": {"status": "supported", "evidence_level": 2, "evidence_refs": [claim_ref]}},
                "realization_form": "native-cpp",
                "capability_requirements": copy.deepcopy(backend["required_target_capabilities"]),
                "dependency_requirements": [],
                "resource_requirements": [],
                "required_evidence_level": 2,
                "compatibility_evidence": [claim_ref],
                "selection_policy": {"policy_id": f"schuss-selection-policy-{48 + index:06d}", "version": 1, "priority": 500, "ranking_rule": "higher-explicit-priority", "tie_behavior": "ambiguous", "implicit_fallback": False},
                "unresolved_questions": [],
            },
            eligibility_schema,
        )

    request_schema = parent.schemas["build-request-v0"]
    template_request = _find_exact(
        parent.records["request"],
        {
            "build_request_id": "schuss-build-request-000005",
            "revision": 1,
            "content_hash": "sha256:8f40ac2f996f32f10f59b862da566f1d66f145cdf1780f29d786c9b2f42f03c2",
        },
        "build_request_id",
    )
    request_value = copy.deepcopy(template_request)
    request_value.update(
        {
            "build_request_id": HOST_REQUEST_ID,
            "revision": 1,
            "content_hash": "sha256:" + "0" * 64,
            "compute_target_reference": _exact_ref(target, "compute_target_id"),
            "backend_reference": _exact_ref(backend, "backend_id"),
            "requested_stopping_stage": "artifact-generation",
        }
    )
    host_request = _hash_record(request_value, request_schema)

    records: list[tuple[str, str, dict[str, Any]]] = [
        ("third-party-source-lock", "juce-source-lock.json", source_lock),
        ("environment", "host-toolchain-environment.json", toolchain),
        ("environment", "schuss-rt-environment.json", runtime_environment),
        ("target", "desktop-host-target.json", target),
        ("backend", "desktop-host-backend.json", backend),
        ("request", "effects-seven-host-request.json", host_request),
    ]
    for role in ROLE_ORDER:
        records.extend(
            [
                ("implementation-binding", f"host-binding-{role}-r1.json", candidate_bindings[role]),
                ("implementation-binding", f"host-binding-{role}-r2.json", bindings[role]),
                ("evidence", f"host-binding-evidence-{role}.json", claims[role]),
                ("eligibility", f"host-eligibility-{role}.json", eligibilities[role]),
            ]
        )
    return records


def generated() -> tuple[dict[str, bytes], bytes, dict[str, Any]]:
    schemas = _schemas()
    files = {
        f"schemas/{name}.schema.json": _canonical_bytes(schema)
        for name, schema in schemas.items()
    }
    parent_loaded = record_set_rules.load_record_set(ROOT, PARENT)
    records = _semantic_records(parent_loaded, schemas)
    for _, filename, record in records:
        files[f"contracts/task031/{filename}"] = _canonical_bytes(record)

    parent = parent_loaded.manifest
    schema_members = copy.deepcopy(parent["schema_members"])
    existing_schemas = {member["schema_version"] for member in schema_members}
    for name in sorted(SCHEMA_NAMES):
        if name in existing_schemas:
            raise ValueError(f"Task 031 schema collides with parent: {name}")
        path = f"schemas/{name}.schema.json"
        schema_members.append(
            {
                "schema_version": name,
                "portable_path": path,
                "byte_sha256": hashlib.sha256(files[path]).hexdigest(),
            }
        )

    record_members = copy.deepcopy(parent["record_members"])
    id_fields = record_set_rules.ID_FIELDS
    for kind, filename, record in records:
        ids = [field for field in id_fields if field in record]
        if len(ids) != 1:
            raise ValueError(f"Task 031 record {filename} has invalid stable ID fields {ids}")
        path = f"contracts/task031/{filename}"
        record_members.append(
            {
                "record_kind": kind,
                "stable_id": record[ids[0]],
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
        "record_set_id": HOST_RECORD_SET_ID,
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "purpose": "prospective-task",
        "parent_reference": {"status": "included", **parent_loaded.reference},
        "schema_members": sorted(schema_members, key=lambda item: (item["byte_sha256"], item["portable_path"])),
        "record_members": sorted(record_members, key=lambda item: (item["record_kind"], item["stable_id"], item["revision"], item["content_hash"])),
        "enforced_directories": sorted(set(parent["enforced_directories"]) | {"contracts/task031"}),
    }
    errors = core.schema_errors(manifest, manifest_schema, manifest_schema)
    if errors:
        raise ValueError("; ".join(errors))
    manifest["content_hash"] = core.record_content_hash(manifest, manifest_schema)
    summary = {
        "schema_version": "task031a-generation-summary-v1",
        "status": "valid",
        "record_set_reference": {key: manifest[key] for key in ("record_set_id", "revision", "content_hash")},
        "added_schema_versions": list(SCHEMA_NAMES),
        "semantic_records_added": len(records),
        "host_bindings_added": len(ROLE_ORDER),
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
        path = ROOT / relative
        if args.check:
            if not path.exists() or path.read_bytes() != data:
                stale.append(relative)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
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
