#!/usr/bin/env python3
"""Generate the bounded Task 011B schemas, records, and successor record set."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/contracts"))

import record_set_rules  # noqa: E402
import validator_core as core  # noqa: E402


ZERO_HASH = "sha256:" + "0" * 64
PARENT_PATH = ROOT / "contracts/record-sets/task011a-catalog-v1.json"
RECORD_SET_SCHEMA_PATH = ROOT / "schemas/prerequisite/record-set-v0.schema.json"
COMPONENT_V0_PATH = ROOT / "schemas/component-contract-v0.schema.json"
BINDING_V0_PATH = ROOT / "schemas/implementation-binding-v0.schema.json"
COMPONENT_V1_RELATIVE = "schemas/component-contract-v1.schema.json"
BINDING_V1_RELATIVE = "schemas/implementation-binding-v1.schema.json"
MANIFEST_RELATIVE = "contracts/record-sets/task011b-vertical-slice-v1.json"
TASK_ROOT = "contracts/task011b"


def _component_schema() -> dict[str, Any]:
    schema = copy.deepcopy(core.load_json(COMPONENT_V0_PATH))
    schema["$id"] = "component-contract-v1.schema.json"
    schema["title"] = "Schuss component contract v1"
    schema["properties"]["schema_version"] = {"const": "component-contract-v1"}
    schema["required"].append("behavior_rules")
    for definition in ("portType", "parameter"):
        schema["$defs"][definition]["properties"]["unit"]["enum"].append(
            "semitone-offset"
        )
    schema["properties"]["behavior_rules"] = {
        "type": "array",
        "x-schuss-array-kind": "set",
        "uniqueItems": True,
        "items": {"$ref": "#/$defs/behaviorRule"},
    }
    rule_id = {"type": "string", "pattern": "^component-behavior-[0-9]{6}$"}
    port_id = {"type": "string", "pattern": "^component-port-[0-9]{6}$"}
    parameter_id = {
        "type": "string",
        "pattern": "^component-parameter-[0-9]{6}$",
    }
    schema["$defs"]["edgeTriggeredTransition"] = {
        "type": "object",
        "required": ["rule_id", "kind", "input_port_id", "edge", "effect"],
        "properties": {
            "rule_id": rule_id,
            "kind": {"const": "edge-triggered-transition"},
            "input_port_id": port_id,
            "edge": {"enum": ["rising", "falling"]},
            "effect": {"enum": ["reset-phase", "reset-state"]},
        },
        "additionalProperties": False,
    }
    schema["$defs"]["parameterInputSum"] = {
        "type": "object",
        "required": [
            "rule_id",
            "kind",
            "parameter_id",
            "input_port_id",
            "operation",
            "result_unit",
            "result_domain",
            "range_policy",
            "evaluation",
        ],
        "properties": {
            "rule_id": rule_id,
            "kind": {"const": "parameter-input-sum"},
            "parameter_id": parameter_id,
            "input_port_id": port_id,
            "operation": {"const": "add"},
            "result_unit": {
                "enum": ["semitone-offset", "normalized", "unitless"]
            },
            "result_domain": {"$ref": "#/$defs/range"},
            "range_policy": {"enum": ["exact-sum", "clamp-to-result-domain"]},
            "evaluation": {"const": "control-cycle"},
        },
        "additionalProperties": False,
    }
    schema["$defs"]["indexedParameterSelection"] = {
        "type": "object",
        "required": [
            "rule_id",
            "kind",
            "input_port_id",
            "parameter_ids",
            "output_port_id",
            "out_of_range_value",
            "evaluation",
        ],
        "properties": {
            "rule_id": rule_id,
            "kind": {"const": "indexed-parameter-selection"},
            "input_port_id": port_id,
            "parameter_ids": {
                "type": "array",
                "x-schuss-array-kind": "sequence",
                "minItems": 1,
                "uniqueItems": True,
                "items": parameter_id,
            },
            "output_port_id": port_id,
            "out_of_range_value": {"$ref": "#/$defs/exactDecimal"},
            "evaluation": {"const": "control-cycle"},
        },
        "additionalProperties": False,
    }
    schema["$defs"]["boundedCyclicCounter"] = {
        "type": "object",
        "required": [
            "rule_id",
            "kind",
            "trigger_port_id",
            "reset_port_id",
            "maximum_parameter_id",
            "output_port_id",
            "carry_port_id",
            "trigger_edge",
            "reset_edge",
            "initial_value",
            "wrap_rule",
            "evaluation",
        ],
        "properties": {
            "rule_id": rule_id,
            "kind": {"const": "bounded-cyclic-counter"},
            "trigger_port_id": port_id,
            "reset_port_id": port_id,
            "maximum_parameter_id": parameter_id,
            "output_port_id": port_id,
            "carry_port_id": port_id,
            "trigger_edge": {"const": "rising"},
            "reset_edge": {"const": "rising"},
            "initial_value": {"$ref": "#/$defs/exactDecimal"},
            "wrap_rule": {"const": "next-count-greater-than-or-equal-maximum"},
            "evaluation": {"const": "control-cycle"},
        },
        "additionalProperties": False,
    }
    schema["$defs"]["behaviorRule"] = {
        "oneOf": [
            {"$ref": "#/$defs/edgeTriggeredTransition"},
            {"$ref": "#/$defs/parameterInputSum"},
            {"$ref": "#/$defs/indexedParameterSelection"},
            {"$ref": "#/$defs/boundedCyclicCounter"},
        ]
    }
    return schema


def _binding_schema() -> dict[str, Any]:
    schema = copy.deepcopy(core.load_json(BINDING_V0_PATH))
    schema["$id"] = "implementation-binding-v1.schema.json"
    schema["title"] = "Schuss implementation binding v1"
    schema["properties"]["schema_version"] = {"const": "implementation-binding-v1"}
    schema["$defs"]["legacyObservation"]["properties"]["legacy_uuid"][
        "pattern"
    ] = "^[0-9a-f]{39,42}$"
    data_type = schema["$defs"]["legacySeam"]["properties"]["data_type"]
    schema["$defs"]["legacySeam"]["properties"]["data_type"] = {
        "oneOf": [data_type, {"type": "null"}]
    }
    return schema


def _json_bytes(value: dict[str, Any]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _seal(value: dict[str, Any], schema: dict[str, Any]) -> tuple[dict[str, Any], bytes]:
    value = copy.deepcopy(value)
    structural = core.schema_errors(value, schema, schema)
    if structural:
        raise ValueError("; ".join(structural))
    value["content_hash"] = core.record_content_hash(value, schema)
    errors = core.schema_errors(value, schema, schema)
    if errors:
        raise ValueError("; ".join(errors))
    canonical = core.canonicalize_with_schema(value, schema, schema)
    return canonical, core.canonical_json(canonical).encode("utf-8") + b"\n"


def _ref(record: dict[str, Any], id_field: str) -> dict[str, Any]:
    return {
        id_field: record[id_field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def _q27() -> dict[str, Any]:
    return {
        "kind": "fixed-point",
        "signed": True,
        "width_bits": 32,
        "fractional_bits": 27,
        "encoding": "twos-complement-binary",
    }


def _q21() -> dict[str, Any]:
    return {
        "kind": "fixed-point",
        "signed": True,
        "width_bits": 32,
        "fractional_bits": 21,
        "encoding": "twos-complement-binary",
    }


def _int32() -> dict[str, Any]:
    return {
        "kind": "integer",
        "signed": True,
        "width_bits": 32,
        "encoding": "twos-complement-binary",
    }


def _bool32() -> dict[str, Any]:
    return {
        "kind": "boolean",
        "width_bits": 32,
        "encoding": "zero-false-nonzero-true",
    }


def _known(minimum: str, maximum: str, overflow: str = "reject") -> dict[str, Any]:
    return {
        "status": "known",
        "minimum": minimum,
        "maximum": maximum,
        "minimum_inclusive": True,
        "maximum_inclusive": True,
        "overflow_policy": overflow,
    }


def _port(
    number: int,
    key: str,
    label: str,
    direction: str,
    *,
    rate: str,
    role: str,
    representation: dict[str, Any],
    unit: str,
    minimum: str,
    maximum: str,
    required: bool = False,
    default: str = "0",
    maximum_connections: int | str = 1,
    overflow: str = "reject",
) -> dict[str, Any]:
    optionality = (
        {"status": "required", "absence_behavior": "invalid"}
        if required
        else (
            {
                "status": "optional",
                "absence_behavior": "use-default",
                "default_value": default,
            }
            if direction == "inlet"
            else {"status": "not-applicable"}
        )
    )
    return {
        "facet_id": f"component-port-{number:06d}",
        "semantic_key": key,
        "display_label": label,
        "direction": direction,
        "port_type": {
            "domain": "stream",
            "rate": rate,
            "channel_shape": {"kind": "fixed", "count": 1},
            "cardinality": {
                "minimum_connections": 1 if required else 0,
                "maximum_connections": maximum_connections,
            },
            "semantic_role": role,
            "representation": copy.deepcopy(representation),
            "unit": unit,
            "valid_range": _known(minimum, maximum, overflow),
            "optionality": optionality,
            "ownership": {
                "status": "defined",
                "owner": "scheduler",
                "mutability": "immutable-to-consumer",
                "borrowing": "borrowed",
                "lifetime": "audio-block" if rate == "audio" else "control-cycle",
                "capacity": "rate-defined" if rate == "audio" else "single-value",
                "synchronization": "single-scheduler",
                "aliasing": "read-only-aliases-allowed",
            },
        },
    }


def _parameter(
    number: int,
    key: str,
    label: str,
    representation: dict[str, Any],
    unit: str,
    minimum: str,
    maximum: str,
    default: str,
) -> dict[str, Any]:
    return {
        "facet_id": f"component-parameter-{number:06d}",
        "semantic_key": key,
        "display_label": label,
        "representation": copy.deepcopy(representation),
        "unit": unit,
        "domain": _known(minimum, maximum),
        "default": default,
        "update_behavior": {"update_kind": "runtime", "stateful": True},
    }


def _state(number: int, key: str, value_kind: str) -> dict[str, Any]:
    return {
        "state_id": f"component-state-{number:06d}",
        "semantic_key": key,
        "value_kind": value_kind,
        "ownership": "component-instance",
        "persistence": "volatile",
        "reset_policy": "default-on-start",
    }


def _contract(
    identifier: str,
    family: dict[str, Any],
    display_name: str,
    ports: list[dict[str, Any]],
    parameters: list[dict[str, Any]],
    states: list[dict[str, Any]],
    behaviors: list[dict[str, Any]],
    displays: list[dict[str, Any]] | None = None,
    parameter_inputs: list[str] | None = None,
) -> dict[str, Any]:
    declared_state = bool(states)
    return {
        "schema_version": "component-contract-v1",
        "canonical_profile": "schuss-canonical-json-v1",
        "component_contract_id": identifier,
        "revision": 1,
        "content_hash": ZERO_HASH,
        "family_reference": copy.deepcopy(family),
        "display_name": display_name,
        "ports": ports,
        "parameters": parameters,
        "attributes": [],
        "actions": [],
        "displays": displays or [],
        "state_declarations": states,
        "lifecycle": {
            "state_model": "declared-state" if declared_state else "stateless",
            "initialization": (
                "initialize-declared-state" if declared_state else "none"
            ),
            "reset_behavior": (
                "declared-per-state" if declared_state else "not-applicable"
            ),
            "disposal": "none",
        },
        "binding_capabilities": {
            "parameter_input_ports": parameter_inputs or [],
            "action_inputs": [],
        },
        "capability_requirements": [],
        "compound_interface": {"kind": "primitive", "mapping_keys": []},
        "compatibility_claims": [],
        "behavior_rules": behaviors,
    }


def _family_refs(corpus: dict[str, Any]) -> dict[str, dict[str, Any]]:
    refs: dict[str, dict[str, Any]] = {}
    for item in corpus["family_companions"] + corpus["family_additions"]:
        refs[item["family_id"]] = _ref(item, "family_id")
    return refs


def _contracts(
    component_schema: dict[str, Any], corpus: dict[str, Any]
) -> dict[str, tuple[dict[str, Any], bytes]]:
    families = _family_refs(corpus)
    full_min = "-16"
    full_max = "15.999999992549419403076171875"
    audio = _port(
        1,
        "audio-template",
        "Audio template",
        "outlet",
        rate="audio",
        role="audio",
        representation=_q27(),
        unit="normalized",
        minimum="-1",
        maximum="1",
    )["port_type"]

    values: dict[str, dict[str, Any]] = {}
    values["lfo"] = _contract(
        "schuss-component-contract-000004",
        families["schuss-family-000027"],
        "Square LFO",
        [
            _port(1, "pitch", "Pitch", "inlet", rate="control", role="modulation", representation=_q21(), unit="semitone-offset", minimum="-64", maximum="63.999999523162841796875"),
            _port(2, "reset", "Reset", "inlet", rate="control", role="trigger", representation=_bool32(), unit="boolean", minimum="0", maximum="1"),
            _port(3, "wave", "Wave", "outlet", rate="control", role="clock", representation=_bool32(), unit="boolean", minimum="0", maximum="1"),
        ],
        [_parameter(1, "base-pitch", "Base pitch", _q21(), "semitone-offset", "-64", "63.999999523162841796875", "-48")],
        [_state(1, "phase", "integer"), _state(2, "reset-arm", "boolean")],
        [
            {"rule_id": "component-behavior-000001", "kind": "parameter-input-sum", "parameter_id": "component-parameter-000001", "input_port_id": "component-port-000001", "operation": "add", "result_unit": "semitone-offset", "result_domain": _known("-128", "127.99999904632568359375"), "range_policy": "exact-sum", "evaluation": "control-cycle"},
            {"rule_id": "component-behavior-000002", "kind": "edge-triggered-transition", "input_port_id": "component-port-000002", "edge": "rising", "effect": "reset-phase"},
        ],
    )
    values["counter"] = _contract(
        "schuss-component-contract-000005",
        families["schuss-family-000028"],
        "Cyclic Counter",
        [
            _port(1, "trigger", "Trigger", "inlet", rate="control", role="clock", representation=_bool32(), unit="boolean", minimum="0", maximum="1", required=True),
            _port(2, "reset", "Reset", "inlet", rate="control", role="trigger", representation=_bool32(), unit="boolean", minimum="0", maximum="1"),
            _port(3, "count", "Count", "outlet", rate="control", role="generic-data", representation=_int32(), unit="unitless", minimum="0", maximum="65535"),
            _port(4, "carry", "Carry", "outlet", rate="control", role="trigger", representation=_bool32(), unit="boolean", minimum="0", maximum="1"),
        ],
        [_parameter(1, "maximum", "Maximum", _int32(), "unitless", "0", "65536", "4")],
        [_state(1, "count", "integer"), _state(2, "trigger-arm", "boolean"), _state(3, "reset-arm", "boolean")],
        [{"rule_id": "component-behavior-000001", "kind": "bounded-cyclic-counter", "trigger_port_id": "component-port-000001", "reset_port_id": "component-port-000002", "maximum_parameter_id": "component-parameter-000001", "output_port_id": "component-port-000003", "carry_port_id": "component-port-000004", "trigger_edge": "rising", "reset_edge": "rising", "initial_value": "0", "wrap_rule": "next-count-greater-than-or-equal-maximum", "evaluation": "control-cycle"}],
    )
    values["sequencer"] = _contract(
        "schuss-component-contract-000006",
        families["schuss-family-000022"],
        "Four-step Pitch Sequencer",
        [
            _port(1, "step", "Step", "inlet", rate="control", role="generic-data", representation=_int32(), unit="unitless", minimum="0", maximum="65535", required=True),
            _port(2, "chain", "Chain", "outlet", rate="control", role="generic-data", representation=_int32(), unit="unitless", minimum="-4", maximum="65531"),
            _port(3, "pitch", "Pitch", "outlet", rate="control", role="note", representation=_q21(), unit="semitone-offset", minimum="-64", maximum="63.999999523162841796875", maximum_connections=2),
        ],
        [_parameter(index, f"step-{index}", f"Step {index}", _q21(), "semitone-offset", "-64", "63.999999523162841796875", "0") for index in range(1, 5)],
        [],
        [{"rule_id": "component-behavior-000001", "kind": "indexed-parameter-selection", "input_port_id": "component-port-000001", "parameter_ids": [f"component-parameter-{index:06d}" for index in range(1, 5)], "output_port_id": "component-port-000003", "out_of_range_value": "0", "evaluation": "control-cycle"}],
    )
    sine_ports = [
        _port(1, "pitch", "Pitch", "inlet", rate="control", role="note", representation=_q21(), unit="semitone-offset", minimum="-64", maximum="63.999999523162841796875", required=True),
        _port(2, "frequency-modulation", "Frequency modulation", "inlet", rate="audio", role="modulation", representation=_q27(), unit="unitless", minimum=full_min, maximum=full_max),
        _port(3, "phase-modulation", "Phase modulation", "inlet", rate="audio", role="modulation", representation=_q27(), unit="unitless", minimum=full_min, maximum=full_max),
        _port(4, "wave", "Wave", "outlet", rate="audio", role="audio", representation=_q27(), unit="normalized", minimum="-1", maximum="1"),
    ]
    sine_ports[3]["port_type"] = copy.deepcopy(audio)
    values["sine"] = _contract(
        "schuss-component-contract-000007",
        families["schuss-family-000003"],
        "Sine Oscillator",
        sine_ports,
        [_parameter(1, "base-pitch", "Base pitch", _q21(), "semitone-offset", "-64", "63.999999523162841796875", "-24")],
        [_state(1, "phase", "integer")],
        [{"rule_id": "component-behavior-000001", "kind": "parameter-input-sum", "parameter_id": "component-parameter-000001", "input_port_id": "component-port-000001", "operation": "add", "result_unit": "semitone-offset", "result_domain": _known("-128", "127.99999904632568359375"), "range_policy": "exact-sum", "evaluation": "control-cycle"}],
    )
    filter_input = copy.deepcopy(audio)
    filter_input["cardinality"] = {"minimum_connections": 1, "maximum_connections": 1}
    filter_input["optionality"] = {"status": "required", "absence_behavior": "invalid"}
    filter_output = copy.deepcopy(audio)
    filter_output["valid_range"] = _known(full_min, full_max)
    values["filter"] = _contract(
        "schuss-component-contract-000008",
        families["schuss-family-000009"],
        "State-variable Filter",
        [
            {"facet_id": "component-port-000001", "semantic_key": "input", "display_label": "Input", "direction": "inlet", "port_type": filter_input},
            _port(2, "pitch", "Pitch", "inlet", rate="control", role="modulation", representation=_q21(), unit="semitone-offset", minimum="-64", maximum="63.999999523162841796875"),
            _port(3, "resonance", "Resonance", "inlet", rate="control", role="modulation", representation=_q27(), unit="normalized", minimum="-1", maximum="1"),
            {"facet_id": "component-port-000004", "semantic_key": "high-pass", "display_label": "High-pass", "direction": "outlet", "port_type": copy.deepcopy(filter_output)},
            {"facet_id": "component-port-000005", "semantic_key": "band-pass", "display_label": "Band-pass", "direction": "outlet", "port_type": copy.deepcopy(filter_output)},
            {"facet_id": "component-port-000006", "semantic_key": "low-pass", "display_label": "Low-pass", "direction": "outlet", "port_type": copy.deepcopy(filter_output)},
        ],
        [
            _parameter(1, "cutoff-pitch", "Cutoff pitch", _q21(), "semitone-offset", "-64", "63.999999523162841796875", "24"),
            _parameter(2, "base-resonance", "Base resonance", _q27(), "normalized", "0", "1", "0.125"),
        ],
        [_state(1, "low", "integer"), _state(2, "band", "integer")],
        [
            {"rule_id": "component-behavior-000001", "kind": "parameter-input-sum", "parameter_id": "component-parameter-000001", "input_port_id": "component-port-000002", "operation": "add", "result_unit": "semitone-offset", "result_domain": _known("-128", "127.99999904632568359375"), "range_policy": "exact-sum", "evaluation": "control-cycle"},
            {"rule_id": "component-behavior-000002", "kind": "parameter-input-sum", "parameter_id": "component-parameter-000002", "input_port_id": "component-port-000003", "operation": "add", "result_unit": "normalized", "result_domain": _known("0", "1", "clamp"), "range_policy": "clamp-to-result-domain", "evaluation": "control-cycle"},
        ],
    )
    values["filter"]["ports"][5]["port_type"]["cardinality"]["maximum_connections"] = 2
    endpoint_input = copy.deepcopy(filter_output)
    endpoint_input["cardinality"] = {"minimum_connections": 1, "maximum_connections": 1}
    endpoint_input["optionality"] = {"status": "required", "absence_behavior": "invalid"}
    values["output"] = _contract(
        "schuss-component-contract-000009",
        families["schuss-family-000002"],
        "Stereo Audio Output",
        [
            {"facet_id": "component-port-000001", "semantic_key": "left", "display_label": "Left", "direction": "inlet", "port_type": copy.deepcopy(endpoint_input)},
            {"facet_id": "component-port-000002", "semantic_key": "right", "display_label": "Right", "direction": "inlet", "port_type": copy.deepcopy(endpoint_input)},
        ],
        [],
        [],
        [],
        displays=[
            {"facet_id": "component-display-000001", "semantic_key": "left-level", "display_label": "Left level", "value_kind": "integer", "access": "read-only"},
            {"facet_id": "component-display-000002", "semantic_key": "right-level", "display_label": "Right level", "value_kind": "integer", "access": "read-only"},
        ],
    )
    return {key: _seal(value, component_schema) for key, value in values.items()}


def _observations() -> dict[int, dict[str, Any]]:
    path = ROOT / "catalog/snapshots/legacy-resolved-catalog-v0/resolved/objects.jsonl"
    wanted = {9, 159, 209, 215, 549, 918}
    return {
        item["variant_index"]: item
        for item in core.load_jsonl(path)
        if item["variant_index"] in wanted
    }


def _binding(
    identifier: str,
    contract: dict[str, Any],
    observation: dict[str, Any],
    form: str,
    mapping_specs: Iterable[tuple[str, str, str, int]],
    private_state: list[dict[str, str]],
    manifest_sha256: str,
) -> dict[str, Any]:
    seam_kinds = {
        "inlets": "legacy-inlet",
        "outlets": "legacy-outlet",
        "parameters": "legacy-parameter",
        "attributes": "legacy-attribute",
        "actions": "legacy-action",
        "displays": "legacy-display",
    }
    mappings = []
    for mapping_number, (facet_kind, facet_id, collection, index) in enumerate(
        mapping_specs, 1
    ):
        observed = observation["facets"][collection][index]
        mappings.append(
            {
                "mapping_id": f"binding-map-{mapping_number:06d}",
                "contract_facet": {"facet_kind": facet_kind, "facet_id": facet_id},
                "implementation_seam": {
                    "seam_kind": seam_kinds[collection],
                    "index": observed["index"],
                    "name": observed["name"],
                    "legacy_type": observed["legacy_type"],
                    "data_type": observed["data_type"],
                },
            }
        )
    origin = observation["origin"]
    evidence_ref = f"legacy-resolved-catalog-v0:object:{observation['variant_index']}"
    return {
        "schema_version": "implementation-binding-v1",
        "canonical_profile": "schuss-canonical-json-v1",
        "implementation_id": identifier,
        "revision": 1,
        "content_hash": ZERO_HASH,
        "contract_reference": _ref(contract, "component_contract_id"),
        "realization": {
            "form": form,
            "observation": {
                "snapshot_schema_version": "legacy-resolved-catalog-v0",
                "manifest_sha256": manifest_sha256,
                "evidence_ref": evidence_ref,
                "variant_index": observation["variant_index"],
                "legacy_uuid": observation["uuid"]["durable_value"],
                "source_id": origin["source_id"],
                "source_sha256": origin["sha256"],
            },
        },
        "facet_mappings": mappings,
        "observed_dependencies": [],
        "private_state": private_state,
        "selection_state": {
            "status": "not-evaluated",
            "owner": "task-007",
            "reason": "target-backend-contracts-not-yet-implemented",
            "rationale": "Task 011B maps exact seams only; its separate eligibility companion remains unresolved and grants no production selection authority.",
        },
        "evidence_refs": [evidence_ref],
    }


def _bindings(
    schema: dict[str, Any],
    contracts: dict[str, tuple[dict[str, Any], bytes]],
) -> dict[str, tuple[dict[str, Any], bytes]]:
    obs = _observations()
    manifest_sha = core.sha256_file(
        ROOT / "catalog/snapshots/legacy-resolved-catalog-v0/manifest.json"
    )
    specs = {
        "lfo": ("schuss-implementation-000039", 209, "generated-legacy-object", [("port", "component-port-000001", "inlets", 0), ("port", "component-port-000002", "inlets", 1), ("port", "component-port-000003", "outlets", 0), ("parameter", "component-parameter-000001", "parameters", 0)], [{"state_key": "phase", "value_kind": "integer"}, {"state_key": "reset-arm", "value_kind": "integer"}]),
        "counter": ("schuss-implementation-000040", 215, "generated-legacy-object", [("port", "component-port-000001", "inlets", 0), ("port", "component-port-000002", "inlets", 1), ("port", "component-port-000003", "outlets", 0), ("port", "component-port-000004", "outlets", 1), ("parameter", "component-parameter-000001", "parameters", 0)], [{"state_key": "count", "value_kind": "integer"}, {"state_key": "trigger-arm", "value_kind": "integer"}, {"state_key": "reset-arm", "value_kind": "integer"}]),
        "sequencer": ("schuss-implementation-000041", 918, "legacy-native-object", [("port", "component-port-000001", "inlets", 0), ("port", "component-port-000002", "outlets", 0), ("port", "component-port-000003", "outlets", 1), *[("parameter", f"component-parameter-{index:06d}", "parameters", index - 1) for index in range(1, 5)]], []),
        "sine": ("schuss-implementation-000007", 549, "generated-legacy-object", [("port", "component-port-000001", "inlets", 0), ("port", "component-port-000002", "inlets", 1), ("port", "component-port-000003", "inlets", 2), ("port", "component-port-000004", "outlets", 0), ("parameter", "component-parameter-000001", "parameters", 0)], [{"state_key": "phase", "value_kind": "integer"}]),
        "filter": ("schuss-implementation-000015", 159, "generated-legacy-object", [("port", "component-port-000001", "inlets", 0), ("port", "component-port-000002", "inlets", 1), ("port", "component-port-000003", "inlets", 2), ("port", "component-port-000004", "outlets", 0), ("port", "component-port-000005", "outlets", 1), ("port", "component-port-000006", "outlets", 2), ("parameter", "component-parameter-000001", "parameters", 0), ("parameter", "component-parameter-000002", "parameters", 1)], [{"state_key": "low", "value_kind": "integer"}, {"state_key": "band", "value_kind": "integer"}]),
        "output": ("schuss-implementation-000004", 9, "generated-legacy-object", [("port", "component-port-000001", "inlets", 0), ("port", "component-port-000002", "inlets", 1), ("display", "component-display-000001", "displays", 0), ("display", "component-display-000002", "displays", 1)], []),
    }
    result = {}
    for key, (identifier, variant, form, mapping_specs, private_state) in specs.items():
        value = _binding(identifier, contracts[key][0], obs[variant], form, mapping_specs, private_state, manifest_sha)
        result[key] = _seal(value, schema)
    return result


def _node(number: int, contract: dict[str, Any], values: list[tuple[int, str]]) -> dict[str, Any]:
    return {
        "node_id": f"graph-node-{number:06d}",
        "contract_reference": _ref(contract, "component_contract_id"),
        "parameter_values": [
            {"facet_id": f"component-parameter-{facet:06d}", "value": value}
            for facet, value in values
        ],
        "attribute_values": [],
    }


def _connection(number: int, source_node: int, source_port: int, destination_node: int, destination_port: int) -> dict[str, Any]:
    return {
        "connection_id": f"graph-connection-{number:06d}",
        "source": {"node_id": f"graph-node-{source_node:06d}", "facet_id": f"component-port-{source_port:06d}"},
        "destination": {"node_id": f"graph-node-{destination_node:06d}", "facet_id": f"component-port-{destination_port:06d}"},
    }


def _graph(
    schema: dict[str, Any], contracts: dict[str, tuple[dict[str, Any], bytes]]
) -> tuple[dict[str, Any], bytes]:
    crossfader = core.load_json(ROOT / "contracts/component-contracts/crossfader-mixed-v0.json")
    accepted = core.load_json(ROOT / "contracts/graphs/blend-crossfader-v0.json")
    graph = {
        "schema_version": "dsp-graph-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "graph_id": "schuss-graph-000002",
        "revision": 1,
        "content_hash": ZERO_HASH,
        "display_name": "Four-step dual-sine Gills graph",
        "public_ports": [],
        "public_parameters": copy.deepcopy(accepted["public_parameters"]),
        "public_actions": [],
        "public_displays": [],
        "nodes": [
            _node(1, contracts["lfo"][0], [(1, "-48")]),
            _node(2, contracts["counter"][0], [(1, "4")]),
            _node(3, contracts["sequencer"][0], [(1, "0"), (2, "5"), (3, "7"), (4, "12")]),
            _node(4, contracts["sine"][0], [(1, "-24")]),
            _node(5, contracts["sine"][0], [(1, "-23.875")]),
            _node(6, crossfader, []),
            _node(7, contracts["filter"][0], [(1, "24"), (2, "0.125")]),
            _node(8, contracts["output"][0], []),
        ],
        "connections": [
            _connection(1, 1, 3, 2, 1),
            _connection(2, 2, 3, 3, 1),
            _connection(3, 3, 3, 4, 1),
            _connection(4, 3, 3, 5, 1),
            _connection(5, 4, 4, 6, 1),
            _connection(6, 5, 4, 6, 2),
            _connection(7, 6, 4, 7, 1),
            _connection(8, 7, 6, 8, 1),
            _connection(9, 7, 6, 8, 2),
        ],
        "public_port_exposures": [],
        "public_facet_exposures": [],
        "parameter_bindings": copy.deepcopy(accepted["parameter_bindings"]),
        "compound_interface_mappings": [],
        "hierarchy_edges": [],
    }
    graph["parameter_bindings"][0]["destination"]["node_id"] = "graph-node-000006"
    return _seal(graph, schema)


def _instrument(schema: dict[str, Any], graph: dict[str, Any]) -> tuple[dict[str, Any], bytes]:
    value = copy.deepcopy(core.load_json(ROOT / "contracts/instruments/blend-reference-v0-r2.json"))
    value["instrument_id"] = "schuss-instrument-000002"
    value["revision"] = 1
    value["content_hash"] = ZERO_HASH
    value["display_name"] = "Four-step dual-sine instrument"
    value["graph_reference"] = {"status": "resolved", **_ref(graph, "graph_id")}
    return _seal(value, schema)


def _eligibility(
    schema: dict[str, Any],
    number: int,
    contract: dict[str, Any],
    binding: dict[str, Any],
    target: dict[str, Any],
    backend: dict[str, Any],
    requirements: list[str],
) -> tuple[dict[str, Any], bytes]:
    value = {
        "schema_version": "binding-eligibility-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "binding_eligibility_id": f"schuss-binding-eligibility-{number:06d}",
        "revision": 1,
        "content_hash": ZERO_HASH,
        "binding_reference": _ref(binding, "implementation_id"),
        "contract_reference": _ref(contract, "component_contract_id"),
        "allowed_pair": {
            "target_reference": _ref(target, "compute_target_id"),
            "backend_reference": _ref(backend, "backend_id"),
            "state": {
                "status": "not-evaluated",
                "code": "TASK011C_BINDING_EVIDENCE_REQUIRED",
                "rationale": "No strictly earlier evidence supports this exact binding revision on the promoted target/backend pair.",
            },
        },
        "realization_form": binding["realization"]["form"],
        "capability_requirements": [
            {"capability_key": key, "value": True, "comparison_rule": "exact"}
            for key in requirements
        ],
        "dependency_requirements": [],
        "resource_requirements": [],
        "required_evidence_level": 2,
        "compatibility_evidence": [],
        "selection_policy": {
            "policy_id": "schuss-selection-policy-000002",
            "version": 1,
            "priority": 100,
            "ranking_rule": "higher-explicit-priority",
            "tie_behavior": "ambiguous",
            "implicit_fallback": False,
        },
        "unresolved_questions": [
            {
                "question_id": f"eligibility-question-{number:06d}",
                "code": "TASK011C_BINDING_EVIDENCE_REQUIRED",
                "owner": "backend-owner",
                "earliest_task": "task-011",
                "question": "Does Task 011C prove this exact binding revision through the required lowering and compile/link stages?",
                "rationale": "Catalog membership and exact seam correspondence are not backend compatibility evidence.",
            }
        ],
    }
    return _seal(value, schema)


def _request(
    schema: dict[str, Any], graph: dict[str, Any], instrument: dict[str, Any], target: dict[str, Any], backend: dict[str, Any]
) -> tuple[dict[str, Any], bytes]:
    accepted = core.load_json(ROOT / "contracts/task009/blend-validation-v0-r2.json")
    value = copy.deepcopy(accepted)
    value["build_request_id"] = "schuss-build-request-000002"
    value["revision"] = 1
    value["content_hash"] = ZERO_HASH
    value["graph_reference"] = _ref(graph, "graph_id")
    value["instrument_reference"] = {"status": "included", **_ref(instrument, "instrument_id")}
    value["compute_target_reference"] = _ref(target, "compute_target_id")
    value["backend_reference"] = _ref(backend, "backend_id")
    value["asset_references"] = []
    value["binding_overrides"] = []
    value["requested_stopping_stage"] = "artifact-generation"
    return _seal(value, schema)


def _procedure(schema: dict[str, Any]) -> tuple[dict[str, Any], bytes]:
    value = copy.deepcopy(core.load_json(ROOT / "contracts/prerequisite/task009/procedure-v0.json"))
    value["procedure_id"] = "schuss-procedure-000002"
    value["revision"] = 1
    value["content_hash"] = ZERO_HASH
    return _seal(value, schema)


def _probe(
    schema: dict[str, Any],
    number: int,
    contract: dict[str, Any],
    binding: dict[str, Any],
    graph: dict[str, Any],
    procedure: dict[str, Any],
) -> tuple[dict[str, Any], bytes]:
    environment = core.load_json(ROOT / "contracts/prerequisite/task009/environment-v0.json")
    value = {
        "schema_version": "conformance-probe-input-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "conformance_probe_id": f"schuss-conformance-probe-{number:06d}",
        "revision": 1,
        "content_hash": ZERO_HASH,
        "candidate_state": "candidate-under-test",
        "binding_reference": _ref(binding, "implementation_id"),
        "contract_reference": _ref(contract, "component_contract_id"),
        "graph_reference": _ref(graph, "graph_id"),
        "environment_reference": _ref(environment, "prerequisite_environment_id"),
        "procedure_reference": _ref(procedure, "procedure_id"),
        "requested_stages": ["backend-lowering", "artifact-generation", "target-compile-link"],
        "execution_authorization": "not-authorized",
        "production_selection_authority": False,
    }
    return _seal(value, schema)


def _stable_id(record: dict[str, Any]) -> str:
    values = [record[field] for field in record_set_rules.ID_FIELDS if field in record]
    if len(values) != 1:
        raise ValueError("Task 011B record must expose exactly one stable ID")
    return values[0]


def _build_outputs() -> dict[str, bytes]:
    component_schema = _component_schema()
    binding_schema = _binding_schema()
    schema_errors = core.validate_schema_annotations(component_schema)
    schema_errors += core.validate_schema_annotations(binding_schema)
    if schema_errors:
        raise ValueError("; ".join(schema_errors))
    outputs: dict[str, bytes] = {
        COMPONENT_V1_RELATIVE: _json_bytes(component_schema),
        BINDING_V1_RELATIVE: _json_bytes(binding_schema),
    }
    corpus = core.load_json(ROOT / "contracts/catalog/task011a-corpus-v1.json")
    contracts = _contracts(component_schema, corpus)
    bindings = _bindings(binding_schema, contracts)
    graph_schema = core.load_json(ROOT / "schemas/dsp-graph-v0.schema.json")
    instrument_schema = core.load_json(ROOT / "schemas/instrument-v0.schema.json")
    eligibility_schema = core.load_json(ROOT / "schemas/binding-eligibility-v0.schema.json")
    request_schema = core.load_json(ROOT / "schemas/build-request-v0.schema.json")
    procedure_schema = core.load_json(ROOT / "schemas/prerequisite/conformance-probe-procedure-v0.schema.json")
    probe_schema = core.load_json(ROOT / "schemas/prerequisite/conformance-probe-input-v0.schema.json")
    graph = _graph(graph_schema, contracts)
    instrument = _instrument(instrument_schema, graph[0])
    target = core.load_json(ROOT / "contracts/task009/ksoloti-core-v0-r2.json")
    backend = core.load_json(ROOT / "contracts/task009/legacy-ksoloti-v0-r2.json")
    eligibilities = {}
    requirement_keys = {
        key: ["audio-stream-fixed-q27", "control-stream-fixed-q27"]
        for key in ("lfo", "counter", "sequencer", "sine", "filter", "output")
    }
    for number, key in enumerate(("lfo", "counter", "sequencer", "sine", "filter", "output"), 2):
        eligibilities[key] = _eligibility(eligibility_schema, number, contracts[key][0], bindings[key][0], target, backend, requirement_keys[key])
    request = _request(request_schema, graph[0], instrument[0], target, backend)
    procedure = _procedure(procedure_schema)
    probes = {
        key: _probe(probe_schema, number, contracts[key][0], bindings[key][0], graph[0], procedure[0])
        for number, key in enumerate(("lfo", "counter", "sequencer", "sine", "filter", "output"), 3)
    }

    record_specs: list[tuple[str, str, tuple[dict[str, Any], bytes]]] = []
    for key in ("lfo", "counter", "sequencer", "sine", "filter", "output"):
        record_specs.append(("component-contract", f"{TASK_ROOT}/component-contracts/{key}.json", contracts[key]))
        record_specs.append(("implementation-binding", f"{TASK_ROOT}/implementation-bindings/{key}.json", bindings[key]))
        record_specs.append(("eligibility", f"{TASK_ROOT}/binding-eligibility/{key}.json", eligibilities[key]))
        record_specs.append(("conformance-probe-input", f"{TASK_ROOT}/probe-inputs/{key}.json", probes[key]))
    record_specs.extend(
        [
            ("dsp-graph", f"{TASK_ROOT}/graphs/four-step-dual-sine.json", graph),
            ("instrument", f"{TASK_ROOT}/instruments/four-step-dual-sine.json", instrument),
            ("request", f"{TASK_ROOT}/build-requests/four-step-dual-sine.json", request),
            ("conformance-probe-procedure", f"{TASK_ROOT}/probe-procedures/task011b.json", procedure),
        ]
    )
    for _, relative, (_, data) in record_specs:
        outputs[relative] = data

    parent = core.load_json(PARENT_PATH)
    schema_members = copy.deepcopy(parent["schema_members"])
    for version, relative in (
        ("component-contract-v1", COMPONENT_V1_RELATIVE),
        ("implementation-binding-v1", BINDING_V1_RELATIVE),
    ):
        schema_members.append(
            {
                "schema_version": version,
                "portable_path": relative,
                "byte_sha256": hashlib.sha256(outputs[relative]).hexdigest(),
            }
        )
    record_members = copy.deepcopy(parent["record_members"])
    for kind, relative, (record, _) in record_specs:
        record_members.append(
            {
                "record_kind": kind,
                "stable_id": _stable_id(record),
                "revision": record["revision"],
                "content_hash": record["content_hash"],
                "portable_path": relative,
                "byte_sha256": hashlib.sha256(outputs[relative]).hexdigest(),
            }
        )
    manifest = {
        "schema_version": "record-set-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "record_set_id": "schuss-record-set-000005",
        "revision": 1,
        "content_hash": ZERO_HASH,
        "purpose": "prospective-task",
        "parent_reference": {
            "status": "included",
            "record_set_id": parent["record_set_id"],
            "revision": parent["revision"],
            "content_hash": parent["content_hash"],
        },
        "schema_members": schema_members,
        "record_members": record_members,
        "enforced_directories": parent["enforced_directories"]
        + sorted({str(Path(relative).parent) for _, relative, _ in record_specs}),
    }
    manifest_schema = core.load_json(RECORD_SET_SCHEMA_PATH)
    sealed_manifest, manifest_bytes = _seal(manifest, manifest_schema)
    del sealed_manifest
    outputs[MANIFEST_RELATIVE] = manifest_bytes
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = _build_outputs()
    changed = []
    for relative, data in sorted(outputs.items()):
        path = ROOT / relative
        if not path.is_file() or path.read_bytes() != data:
            changed.append(relative)
            if not args.check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
    if args.check and changed:
        for relative in changed:
            print(relative)
        return 1
    print(
        core.canonical_json(
            {
                "status": "current" if args.check else "generated",
                "files": len(outputs),
                "changed": len(changed),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
