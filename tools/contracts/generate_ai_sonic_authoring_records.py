#!/usr/bin/env python3
"""Generate the additive sonic-first AI authoring contract surface."""

from __future__ import annotations

import argparse
import copy
import hashlib
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "tools/contracts") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools/contracts"))

from tools.contracts import record_set_rules  # noqa: E402
from tools.contracts import validator_core as core  # noqa: E402


PARENT = ROOT / "contracts/record-sets/ui-desktop-build-device-v1.json"
OUTPUT = ROOT / "contracts/record-sets/ai-sonic-authoring-v1.json"
SCHEMA_NAMES = (
    "application-capability-description-v6",
    "implementation-binding-v3",
    "native-kernel-v0",
    "operation-request-v13",
    "operation-result-v13",
    "project-object-definition-v0",
    "project-v1",
)
PRIMARY_FUNCTIONS = (
    "input-output",
    "sound-sources",
    "sampling-buffers",
    "modulation-control",
    "filters-resonators",
    "shaping-dynamics",
    "delay-reverb",
    "spectral-analysis",
    "mixing-routing",
    "pitch-notes",
    "timing-sequencing",
    "data-math-logic",
    "interface-system",
)


def _canonical_bytes(value: object) -> bytes:
    return (core.canonical_json(value) + "\n").encode("utf-8")


def _set_array(items: dict[str, Any], **extra: Any) -> dict[str, Any]:
    return {
        "type": "array",
        "x-schuss-array-kind": "set",
        "uniqueItems": True,
        "items": items,
        **extra,
    }


def _sequence(items: dict[str, Any], **extra: Any) -> dict[str, Any]:
    return {
        "type": "array",
        "x-schuss-array-kind": "sequence",
        "items": items,
        **extra,
    }


def _closed(required: list[str], properties: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "object",
        "required": required,
        "properties": properties,
        "additionalProperties": False,
    }


def _record_shell(id_field: str, id_pattern: str) -> dict[str, Any]:
    return _closed(
        ["schema_version", "canonical_profile", id_field, "revision", "content_hash"],
        {
            "schema_version": {"type": "string", "minLength": 1},
            "canonical_profile": {"const": "schuss-canonical-json-v1"},
            id_field: {"type": "string", "pattern": id_pattern},
            "revision": {"type": "integer", "minimum": 1},
            "content_hash": {"$ref": "#/$defs/contentHash"},
        },
    )


def _project_schema() -> dict[str, Any]:
    source = core.load_json(ROOT / "schemas/project-v0.schema.json")
    source["$id"] = "project-v1.schema.json"
    source["title"] = "Schuss durable project v1 with project-local objects"
    source["properties"]["schema_version"] = {"const": "project-v1"}
    for definition in ("memberReference", "ownedMember"):
        enum = source["$defs"][definition]["properties"]["record_kind"]["enum"]
        source["$defs"][definition]["properties"]["record_kind"]["enum"] = sorted(
            set(enum) | {"object-definition"}
        )
    return source


def _implementation_binding_schema() -> dict[str, Any]:
    source = core.load_json(ROOT / "schemas/implementation-binding-v2.schema.json")
    source["$id"] = "implementation-binding-v3.schema.json"
    source["title"] = "Schuss implementation binding v3 with project-local native kernels"
    source["properties"]["schema_version"] = {"const": "implementation-binding-v3"}
    source["$defs"]["nativeKernelReference"] = _closed(
        ["native_kernel_id", "revision", "content_hash"],
        {
            "native_kernel_id": {
                "type": "string",
                "pattern": "^schuss-native-kernel-[0-9]{6}$",
            },
            "revision": {"type": "integer", "minimum": 1},
            "content_hash": {"$ref": "#/$defs/contentHash"},
        },
    )
    source["$defs"]["nativeKernelRealization"] = _closed(
        ["form", "kernel_reference", "portable_symbol"],
        {
            "form": {"const": "native-kernel"},
            "kernel_reference": {"$ref": "#/$defs/nativeKernelReference"},
            "portable_symbol": {
                "type": "string",
                "pattern": "^[A-Za-z_][A-Za-z0-9_:]*$",
            },
        },
    )
    source["$defs"]["realization"]["oneOf"].append(
        {"$ref": "#/$defs/nativeKernelRealization"}
    )
    return source


def _native_kernel_schema() -> dict[str, Any]:
    value_source = {
        "oneOf": [
            _closed(["kind", "key"], {"kind": {"const": "input"}, "key": {"$ref": "#/$defs/key"}}),
            _closed(["kind", "key"], {"kind": {"const": "parameter"}, "key": {"$ref": "#/$defs/key"}}),
            _closed(
                ["kind", "instruction_id"],
                {
                    "kind": {"const": "instruction"},
                    "instruction_id": {"$ref": "#/$defs/instructionId"},
                },
            ),
            _closed(
                ["kind", "value"],
                {"kind": {"const": "literal"}, "value": {"$ref": "#/$defs/exactDecimal"}},
            ),
        ]
    }
    instruction = _closed(
        ["instruction_id", "operation", "inputs"],
        {
            "instruction_id": {"$ref": "#/$defs/instructionId"},
            "operation": {
                "enum": [
                    "abs",
                    "add",
                    "clamp",
                    "max",
                    "min",
                    "multiply",
                    "negate",
                    "noise",
                    "one-pole-lowpass",
                    "oscillator-saw",
                    "oscillator-sine",
                    "oscillator-square",
                    "soft-clip",
                    "subtract",
                    "tanh",
                    "wavefold",
                ]
            },
            "inputs": _sequence(value_source, maxItems=4),
        },
    )
    output = _closed(
        ["port_key", "source"],
        {"port_key": {"$ref": "#/$defs/key"}, "source": value_source},
    )
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "native-kernel-v0.schema.json",
        "title": "Schuss bounded declarative native DSP kernel v0",
        **_closed(
            [
                "schema_version",
                "canonical_profile",
                "native_kernel_id",
                "revision",
                "content_hash",
                "input_keys",
                "parameter_keys",
                "instructions",
                "outputs",
                "limits",
            ],
            {
                "schema_version": {"const": "native-kernel-v0"},
                "canonical_profile": {"const": "schuss-canonical-json-v1"},
                "native_kernel_id": {
                    "type": "string",
                    "pattern": "^schuss-native-kernel-[0-9]{6}$",
                },
                "revision": {"const": 1},
                "content_hash": {"$ref": "#/$defs/contentHash"},
                "input_keys": _set_array({"$ref": "#/$defs/key"}, maxItems=16),
                "parameter_keys": _set_array({"$ref": "#/$defs/key"}, maxItems=32),
                "instructions": _sequence(instruction, minItems=1, maxItems=128),
                "outputs": _set_array(output, minItems=1, maxItems=16),
                "limits": _closed(
                    ["maximum_instructions", "maximum_state_slots", "arbitrary_code"],
                    {
                        "maximum_instructions": {"const": 128},
                        "maximum_state_slots": {"const": 128},
                        "arbitrary_code": {"const": "prohibited"},
                    },
                ),
            },
        ),
        "$defs": {
            "contentHash": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
            "exactDecimal": {
                "type": "string",
                "pattern": "^(?:0|-?(?:0\\.[0-9]*[1-9]|[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$",
            },
            "key": {"type": "string", "pattern": "^[a-z][a-z0-9-]*$"},
            "instructionId": {
                "type": "string",
                "pattern": "^kernel-instruction-[0-9]{6}$",
            },
        },
    }


def _object_definition_schema() -> dict[str, Any]:
    family = _closed(
        [
            "family_id",
            "revision",
            "content_hash",
            "display_name",
            "aliases",
            "function",
            "desired_character",
            "provenance",
        ],
        {
            "family_id": {"type": "string", "pattern": "^schuss-family-[0-9]{6}$"},
            "revision": {"const": 1},
            "content_hash": {"$ref": "#/$defs/contentHash"},
            "display_name": {"type": "string", "minLength": 1, "maxLength": 160},
            "aliases": _set_array({"type": "string", "minLength": 1}, maxItems=16),
            "function": {"enum": list(PRIMARY_FUNCTIONS)},
            "desired_character": _set_array(
                {"type": "string", "pattern": "^[a-z][a-z0-9-]*$"}, maxItems=24
            ),
            "provenance": {"enum": ["ai-authored", "user-authored"]},
        },
    )
    host_artifact = _closed(
        [
            "sample_rate",
            "frame_count",
            "channel_count",
            "sample_format",
            "byte_length",
            "content_hash",
            "measurements",
        ],
        {
            "sample_rate": {"enum": [32000, 44100, 48000]},
            "frame_count": {"type": "integer", "minimum": 64, "maximum": 192000},
            "channel_count": {"const": 1},
            "sample_format": {"const": "signed-int16-little-endian"},
            "byte_length": {"type": "integer", "minimum": 44},
            "content_hash": {"$ref": "#/$defs/contentHash"},
            "measurements": _closed(
                [
                    "peak_absolute",
                    "rms",
                    "dc_mean",
                    "crest_factor",
                    "zero_crossing_count",
                ],
                {
                    "peak_absolute": {"$ref": "#/$defs/exactDecimal"},
                    "rms": {"$ref": "#/$defs/exactDecimal"},
                    "dc_mean": {"$ref": "#/$defs/exactDecimal"},
                    "crest_factor": {"$ref": "#/$defs/exactDecimal"},
                    "zero_crossing_count": {"type": "integer", "minimum": 0},
                },
            ),
        },
    )
    host_evaluation = {
        "oneOf": [
            _closed(["status"], {"status": {"const": "not-run"}}),
            _closed(["status"], {"status": {"const": "not-applicable"}}),
            _closed(
                [
                    "status",
                    "kernel_content_hash",
                    "audition_request_hash",
                    "artifact",
                ],
                {
                    "status": {"const": "passed"},
                    "kernel_content_hash": {"$ref": "#/$defs/contentHash"},
                    "audition_request_hash": {"$ref": "#/$defs/contentHash"},
                    "artifact": host_artifact,
                },
            ),
        ]
    }
    evidence = _closed(
        [
            "structural",
            "host_evaluation",
            "target_lowering",
            "arm_build",
            "connected_device",
            "real_time_resources",
            "audible_listening",
        ],
        {
            "structural": {"enum": ["passed", "failed"]},
            "host_evaluation": host_evaluation,
            "target_lowering": {"const": "not-run"},
            "arm_build": {"const": "not-run"},
            "connected_device": {"const": "not-run"},
            "real_time_resources": {"const": "not-evaluated"},
            "audible_listening": {"const": "not-run"},
        },
    )
    generic_contract = {
        "type": "object",
        "required": [
            "schema_version",
            "canonical_profile",
            "component_contract_id",
            "revision",
            "content_hash",
        ],
        "properties": _record_shell(
            "component_contract_id", "^schuss-component-contract-[0-9]{6}$"
        )["properties"],
        "additionalProperties": True,
        "x-schuss-domain-value": True,
        "x-schuss-external-schema": "component-contract-v1",
    }
    generic_binding = {
        "type": "object",
        "required": [
            "schema_version",
            "canonical_profile",
            "implementation_id",
            "revision",
            "content_hash",
        ],
        "properties": _record_shell(
            "implementation_id", "^schuss-implementation-[0-9]{6}$"
        )["properties"],
        "additionalProperties": True,
        "x-schuss-domain-value": True,
        "x-schuss-external-schema": "implementation-binding-v3",
    }
    generic_graph = {
        "type": "object",
        "required": [
            "schema_version",
            "canonical_profile",
            "graph_id",
            "revision",
            "content_hash",
        ],
        "properties": _record_shell("graph_id", "^schuss-graph-[0-9]{6}$")[
            "properties"
        ],
        "additionalProperties": True,
        "x-schuss-domain-value": True,
        "x-schuss-external-schema": "dsp-graph-v0",
    }
    generic_kernel = {
        "type": "object",
        "required": [
            "schema_version",
            "canonical_profile",
            "native_kernel_id",
            "revision",
            "content_hash",
        ],
        "properties": _record_shell(
            "native_kernel_id", "^schuss-native-kernel-[0-9]{6}$"
        )["properties"],
        "additionalProperties": True,
        "x-schuss-domain-value": True,
        "x-schuss-external-schema": "native-kernel-v0",
    }
    realization = {
        "oneOf": [
            _closed(
                ["form", "graph"],
                {"form": {"const": "transparent-compound"}, "graph": generic_graph},
            ),
            _closed(
                ["form", "kernel"],
                {"form": {"const": "native-kernel"}, "kernel": generic_kernel},
            ),
        ]
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "project-object-definition-v0.schema.json",
        "title": "Schuss project-local object definition v0",
        **_closed(
            [
                "schema_version",
                "canonical_profile",
                "object_definition_id",
                "revision",
                "content_hash",
                "family",
                "component_contract",
                "implementation_binding",
                "realization",
                "intent",
                "evidence",
            ],
            {
                "schema_version": {"const": "project-object-definition-v0"},
                "canonical_profile": {"const": "schuss-canonical-json-v1"},
                "object_definition_id": {
                    "type": "string",
                    "pattern": "^schuss-project-object-[0-9]{6}$",
                },
                "revision": {"const": 1},
                "content_hash": {"$ref": "#/$defs/contentHash"},
                "family": family,
                "component_contract": generic_contract,
                "implementation_binding": generic_binding,
                "realization": realization,
                "intent": {"$ref": "#/$defs/intent"},
                "evidence": evidence,
            },
        ),
        "$defs": {
            "contentHash": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
            "exactDecimal": {
                "type": "string",
                "pattern": "^(?:0|-?(?:0\\.[0-9]*[1-9]|[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$",
            },
            "intent": _intent_schema(),
        },
    }


def _intent_schema() -> dict[str, Any]:
    tag = {"type": "string", "pattern": "^[a-z][a-z0-9-]*$"}
    return _closed(
        [
            "objective",
            "function",
            "required_capabilities",
            "desired_character",
            "priorities",
            "novelty_preference",
        ],
        {
            "objective": {"type": "string", "minLength": 1, "maxLength": 1200},
            "function": {"enum": list(PRIMARY_FUNCTIONS)},
            "required_capabilities": _set_array(tag, maxItems=32),
            "desired_character": _set_array(tag, maxItems=24),
            "priorities": _closed(
                ["accuracy", "interest", "quality"],
                {
                    "accuracy": {"type": "integer", "minimum": 0, "maximum": 100},
                    "interest": {"type": "integer", "minimum": 0, "maximum": 100},
                    "quality": {"type": "integer", "minimum": 0, "maximum": 100},
                },
            ),
            "novelty_preference": {
                "enum": ["reuse-acceptable", "balanced", "prefer-distinctive"]
            },
        },
    )


def _interface_schema() -> dict[str, Any]:
    key = {"type": "string", "pattern": "^[a-z][a-z0-9-]*$"}
    port = _closed(
        ["key", "display_label", "direction", "rate", "semantic_role", "unit"],
        {
            "key": key,
            "display_label": {"type": "string", "minLength": 1, "maxLength": 80},
            "direction": {"enum": ["inlet", "outlet"]},
            "rate": {"enum": ["audio", "control", "event"]},
            "semantic_role": {
                "enum": [
                    "audio",
                    "clock",
                    "crossfade-position",
                    "gate",
                    "generic-signal",
                    "modulation",
                    "note",
                    "trigger",
                ]
            },
            "unit": {
                "enum": [
                    "boolean",
                    "hertz",
                    "midi-note",
                    "normalized",
                    "semitone-offset",
                    "unitless",
                ]
            },
        },
    )
    parameter = _closed(
        ["key", "display_label", "unit", "minimum", "maximum", "default"],
        {
            "key": key,
            "display_label": {"type": "string", "minLength": 1, "maxLength": 80},
            "unit": {
                "enum": [
                    "boolean",
                    "hertz",
                    "midi-note",
                    "normalized",
                    "semitone-offset",
                    "unitless",
                ]
            },
            "minimum": {"$ref": "#/$defs/exactDecimal"},
            "maximum": {"$ref": "#/$defs/exactDecimal"},
            "default": {"$ref": "#/$defs/exactDecimal"},
        },
    )
    return _closed(
        ["ports", "parameters"],
        {
            "ports": _sequence(port, minItems=1, maxItems=16),
            "parameters": _sequence(parameter, maxItems=32),
        },
    )


def _realization_input_schema() -> dict[str, Any]:
    key = {"type": "string", "pattern": "^[a-z][a-z0-9-]*$"}
    component_ref = _closed(
        ["component_contract_id", "revision", "content_hash"],
        {
            "component_contract_id": {
                "type": "string",
                "pattern": "^schuss-component-contract-[0-9]{6}$",
            },
            "revision": {"type": "integer", "minimum": 1},
            "content_hash": {"$ref": "#/$defs/contentHash"},
        },
    )
    facet_value = _closed(
        ["facet_id", "value"],
        {
            "facet_id": {
                "type": "string",
                "pattern": "^component-(?:parameter|attribute)-[0-9]{6}$",
            },
            "value": {"type": "string", "minLength": 1},
        },
    )
    node = _closed(
        ["node_key", "contract_reference", "parameter_values", "attribute_values"],
        {
            "node_key": key,
            "contract_reference": component_ref,
            "parameter_values": _set_array(facet_value, maxItems=32),
            "attribute_values": _set_array(facet_value, maxItems=32),
        },
    )
    endpoint = _closed(
        ["node_key", "facet_id"],
        {
            "node_key": key,
            "facet_id": {"type": "string", "pattern": "^component-port-[0-9]{6}$"},
        },
    )
    connection = _closed(
        ["source", "destination"],
        {"source": endpoint, "destination": endpoint},
    )
    mapping = _closed(
        ["public_kind", "public_key", "target"],
        {
            "public_kind": {"enum": ["port", "parameter"]},
            "public_key": key,
            "target": _closed(
                ["node_key", "facet_id"],
                {
                    "node_key": key,
                    "facet_id": {
                        "type": "string",
                        "pattern": "^component-(?:port|parameter)-[0-9]{6}$",
                    },
                },
            ),
        },
    )
    compact_source = {
        "oneOf": [
            _closed(["kind", "key"], {"kind": {"const": "input"}, "key": key}),
            _closed(["kind", "key"], {"kind": {"const": "parameter"}, "key": key}),
            _closed(
                ["kind", "instruction_id"],
                {
                    "kind": {"const": "instruction"},
                    "instruction_id": {
                        "type": "string",
                        "pattern": "^kernel-instruction-[0-9]{6}$",
                    },
                },
            ),
            _closed(
                ["kind", "value"],
                {"kind": {"const": "literal"}, "value": {"$ref": "#/$defs/exactDecimal"}},
            ),
        ]
    }
    instruction = _closed(
        ["instruction_id", "operation", "inputs"],
        {
            "instruction_id": {
                "type": "string",
                "pattern": "^kernel-instruction-[0-9]{6}$",
            },
            "operation": {
                "enum": [
                    "abs",
                    "add",
                    "clamp",
                    "max",
                    "min",
                    "multiply",
                    "negate",
                    "noise",
                    "one-pole-lowpass",
                    "oscillator-saw",
                    "oscillator-sine",
                    "oscillator-square",
                    "soft-clip",
                    "subtract",
                    "tanh",
                    "wavefold",
                ]
            },
            "inputs": _sequence(compact_source, maxItems=4),
        },
    )
    output = _closed(
        ["port_key", "source"],
        {"port_key": key, "source": compact_source},
    )
    return {
        "oneOf": [
            _closed(
                ["form", "nodes", "connections", "mappings"],
                {
                    "form": {"const": "transparent-compound"},
                    "nodes": _sequence(node, minItems=1, maxItems=128),
                    "connections": _sequence(connection, maxItems=256),
                    "mappings": _sequence(mapping, minItems=1, maxItems=48),
                },
            ),
            _closed(
                ["form", "instructions", "outputs"],
                {
                    "form": {"const": "native-kernel"},
                    "instructions": _sequence(instruction, minItems=1, maxItems=128),
                    "outputs": _sequence(output, minItems=1, maxItems=16),
                },
            ),
        ]
    }


def _operation(name: str, payload: dict[str, Any]) -> dict[str, Any]:
    return _closed(
        ["schema_version", "canonical_profile", "operation", "payload"],
        {
            "schema_version": {"const": "schuss-operation-request-v13"},
            "canonical_profile": {"const": "schuss-canonical-json-v1"},
            "operation": {"const": name},
            "payload": payload,
        },
    )


def _request_schema() -> dict[str, Any]:
    project_ref = _closed(
        ["project_id", "revision", "content_hash"],
        {
            "project_id": {"type": "string", "pattern": "^schuss-project-[0-9]{6}$"},
            "revision": {"type": "integer", "minimum": 1},
            "content_hash": {"$ref": "#/$defs/contentHash"},
        },
    )
    object_ref = _closed(
        ["object_definition_id", "revision", "content_hash"],
        {
            "object_definition_id": {
                "type": "string",
                "pattern": "^schuss-project-object-[0-9]{6}$",
            },
            "revision": {"type": "integer", "minimum": 1},
            "content_hash": {"$ref": "#/$defs/contentHash"},
        },
    )
    exact = {"$ref": "#/$defs/exactDecimal"}
    stimulus = _closed(
        ["port_key", "kind", "amplitude", "frequency_hz"],
        {
            "port_key": {"type": "string", "pattern": "^[a-z][a-z0-9-]*$"},
            "kind": {"enum": ["silence", "constant", "impulse", "sine"]},
            "amplitude": exact,
            "frequency_hz": exact,
        },
    )
    audition = _closed(
        ["sample_rate", "frame_count", "stimuli"],
        {
            "sample_rate": {"enum": [32000, 44100, 48000]},
            "frame_count": {"type": "integer", "minimum": 64, "maximum": 192000},
            "stimuli": _set_array(stimulus, maxItems=16),
        },
    )
    placement = {
        "oneOf": [
            _closed(["kind"], {"kind": {"const": "library-only"}}),
            _closed(
                ["kind", "parameter_values"],
                {
                    "kind": {"const": "add-node"},
                    "parameter_values": _set_array(
                        _closed(
                            ["parameter_key", "value"],
                            {
                                "parameter_key": {
                                    "type": "string",
                                    "pattern": "^[a-z][a-z0-9-]*$",
                                },
                                "value": exact,
                            },
                        ),
                        maxItems=32,
                    ),
                },
            ),
        ]
    }
    operations = [
        _operation(
            "sonic.intent.plan",
            _closed(
                ["intent", "maximum_existing_candidates"],
                {
                    "intent": {"$ref": "#/$defs/intent"},
                    "maximum_existing_candidates": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 20,
                    },
                },
            ),
        ),
        _operation(
            "authoring.draft.create",
            _closed(
                [
                    "expected_project_reference",
                    "display_name",
                    "aliases",
                    "intent",
                    "interface",
                    "realization",
                    "provenance",
                ],
                {
                    "expected_project_reference": project_ref,
                    "display_name": {"type": "string", "minLength": 1, "maxLength": 160},
                    "aliases": _set_array({"type": "string", "minLength": 1}, maxItems=16),
                    "intent": {"$ref": "#/$defs/intent"},
                    "interface": {"$ref": "#/$defs/interface"},
                    "realization": {"$ref": "#/$defs/realizationInput"},
                    "provenance": {"enum": ["ai-authored", "user-authored"]},
                },
            ),
        ),
        _operation(
            "authoring.draft.inspect",
            _closed(
                ["draft_id"],
                {"draft_id": {"type": "string", "pattern": "^authoring-draft-[0-9]{6}$"}},
            ),
        ),
        _operation(
            "authoring.draft.evaluate",
            _closed(
                ["draft_id", "audition"],
                {
                    "draft_id": {"type": "string", "pattern": "^authoring-draft-[0-9]{6}$"},
                    "audition": audition,
                },
            ),
        ),
        _operation(
            "authoring.change.preview",
            _closed(
                ["draft_id", "expected_project_reference", "placement"],
                {
                    "draft_id": {"type": "string", "pattern": "^authoring-draft-[0-9]{6}$"},
                    "expected_project_reference": project_ref,
                    "placement": placement,
                },
            ),
        ),
        _operation(
            "authoring.change.accept",
            _closed(
                [
                    "preview_id",
                    "expected_project_reference",
                    "confirmation_fingerprint",
                    "write_intent",
                ],
                {
                    "preview_id": {"type": "string", "pattern": "^authoring-preview-[0-9]{6}$"},
                    "expected_project_reference": project_ref,
                    "confirmation_fingerprint": {"$ref": "#/$defs/contentHash"},
                    "write_intent": {"const": "explicit"},
                },
            ),
        ),
        _operation("project.objects.list", _closed([], {})),
        _operation(
            "project.object.inspect",
            _closed(["object_reference"], {"object_reference": object_ref}),
        ),
    ]
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "operation-request-v13.schema.json",
        "title": "Schuss sonic-first AI authoring operation request v13",
        "oneOf": operations,
        "$defs": {
            "contentHash": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
            "exactDecimal": {
                "type": "string",
                "pattern": "^(?:0|-?(?:0\\.[0-9]*[1-9]|[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$",
            },
            "intent": _intent_schema(),
            "interface": _interface_schema(),
            "realizationInput": _realization_input_schema(),
        },
    }


def _result_schema() -> dict[str, Any]:
    source = core.load_json(ROOT / "schemas/operation-result-v12.schema.json")
    source["$id"] = "operation-result-v13.schema.json"
    source["title"] = "Schuss sonic-first AI authoring operation result v13"
    source["properties"]["schema_version"]["const"] = "schuss-operation-result-v13"
    source["properties"]["operation"]["enum"] = [
        "authoring.change.accept",
        "authoring.change.preview",
        "authoring.draft.create",
        "authoring.draft.evaluate",
        "authoring.draft.inspect",
        "project.object.inspect",
        "project.objects.list",
        "sonic.intent.plan",
        "invalid-request",
    ]
    source["properties"]["status"]["enum"] = sorted(
        set(source["properties"]["status"]["enum"]) | {"conflict"}
    )
    return source


def _capability_schema() -> dict[str, Any]:
    source = core.load_json(
        ROOT / "schemas/application-capability-description-v5.schema.json"
    )
    source["$id"] = "application-capability-description-v6.schema.json"
    source["title"] = "Schuss application capability description v6"
    source["properties"]["schema_version"]["const"] = (
        "application-capability-description-v6"
    )
    source["properties"]["description_version"]["const"] = (
        "schuss-application-capability-description-v6"
    )
    operations = source["properties"]["operations"]
    operations["minItems"] = 35
    operations["maxItems"] = 35
    entry = source["$defs"]["operationCapability"]["properties"]
    entry["domain_group"]["enum"] = sorted(
        set(entry["domain_group"]["enum"]) | {"authoring"}
    )
    entry["operation"]["enum"] = sorted(
        set(entry["operation"]["enum"])
        | {
            "authoring.change.accept",
            "authoring.change.preview",
            "authoring.draft.create",
            "authoring.draft.evaluate",
            "authoring.draft.inspect",
            "project.object.inspect",
            "project.objects.list",
            "sonic.intent.plan",
        }
    )
    entry["effect_class"]["enum"] = sorted(
        set(entry["effect_class"]["enum"])
        | {"authoring-draft", "workspace-cache-write"}
    )
    entry["availability"]["enum"] = sorted(
        set(entry["availability"]["enum"]) | {"requires-authoring-service"}
    )
    source["$defs"]["contextSet"]["items"]["enum"] = sorted(
        set(source["$defs"]["contextSet"]["items"]["enum"])
        | {"process-local-authoring-service"}
    )
    source["$defs"]["gateSet"]["items"]["enum"] = sorted(
        set(source["$defs"]["gateSet"]["items"]["enum"])
        | {
            "confirmation-fingerprint",
            "draft-handle",
            "preview-handle",
            "sonic-validity-gate",
        }
    )
    entry["request_schema_version"]["pattern"] = (
        "^schuss-operation-request-v(?:[1-9]|10|11|12|13)$"
    )
    entry["result_schema_version"]["pattern"] = (
        "^schuss-operation-result-v(?:[1-9]|10|11|12|13)$"
    )
    return source


def generated() -> tuple[dict[str, bytes], bytes, dict[str, object]]:
    schemas = {
        "application-capability-description-v6": _capability_schema(),
        "implementation-binding-v3": _implementation_binding_schema(),
        "native-kernel-v0": _native_kernel_schema(),
        "operation-request-v13": _request_schema(),
        "operation-result-v13": _result_schema(),
        "project-object-definition-v0": _object_definition_schema(),
        "project-v1": _project_schema(),
    }
    for name, schema in schemas.items():
        errors = core.validate_schema_annotations(schema)
        if errors:
            raise ValueError(f"{name}: " + "; ".join(errors))
    files = {
        f"schemas/{name}.schema.json": _canonical_bytes(schema)
        for name, schema in schemas.items()
    }
    parent = core.load_json(PARENT)
    schema_members = copy.deepcopy(parent["schema_members"])
    existing = {item["schema_version"] for item in schema_members}
    for name in sorted(SCHEMA_NAMES):
        if name in existing:
            raise ValueError(f"AI authoring schema collides with parent: {name}")
        path = f"schemas/{name}.schema.json"
        schema_members.append(
            {
                "schema_version": name,
                "portable_path": path,
                "byte_sha256": hashlib.sha256(files[path]).hexdigest(),
            }
        )
    manifest_schema = core.load_json(ROOT / record_set_rules.RECORD_SET_SCHEMA)
    manifest = {
        "schema_version": "record-set-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "record_set_id": "schuss-record-set-000026",
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "purpose": "prospective-task",
        "parent_reference": {
            "status": "included",
            **{
                key: parent[key]
                for key in ("record_set_id", "revision", "content_hash")
            },
        },
        "schema_members": sorted(
            schema_members,
            key=lambda item: (item["byte_sha256"], item["portable_path"]),
        ),
        "record_members": copy.deepcopy(parent["record_members"]),
        "enforced_directories": copy.deepcopy(parent["enforced_directories"]),
    }
    errors = core.schema_errors(manifest, manifest_schema, manifest_schema)
    if errors:
        raise ValueError("; ".join(errors))
    manifest["content_hash"] = core.record_content_hash(manifest, manifest_schema)
    summary = {
        "schema_version": "ai-sonic-authoring-generation-summary-v1",
        "status": "valid",
        "record_set_reference": {
            key: manifest[key]
            for key in ("record_set_id", "revision", "content_hash")
        },
        "added_schema_versions": list(SCHEMA_NAMES),
        "parent_record_members_preserved": len(manifest["record_members"]),
        "semantic_records_added": 0,
        "build_or_hardware_performed": False,
    }
    return files, _canonical_bytes(manifest), summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files, manifest, summary = generated()
    expected = {**files, OUTPUT.relative_to(ROOT).as_posix(): manifest}
    if args.check:
        stale = [
            path
            for path, payload in expected.items()
            if not (ROOT / path).is_file() or (ROOT / path).read_bytes() != payload
        ]
        if stale:
            raise SystemExit(
                "stale AI sonic authoring generated files: " + ", ".join(stale)
            )
    else:
        for path, payload in expected.items():
            destination = ROOT / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(payload)
    print(core.canonical_json(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
