#!/usr/bin/env python3
"""Generate the exact Task 028 twenty-item direct-palette successor."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/contracts")]

from packages.schuss_core import catalog_projection  # noqa: E402
from packages.schuss_core.control_plane import load_repository_context  # noqa: E402
from packages.schuss_core.palette_direct_frontend import lower_palette  # noqa: E402

import generate_task017_records as task017  # noqa: E402
import record_set_rules  # noqa: E402
import target_backend_build_rules as target_rules  # noqa: E402
import validator_core as core  # noqa: E402


PARENT = ROOT / "contracts/record-sets/task027-mutable-catalog-v1.json"
OUTPUT = ROOT / "contracts/record-sets/task028-direct-palette-v1.json"
DECISION = ROOT / "contracts/task028/palette-curation-decision.md"
OBSERVATIONS = ROOT / "catalog/snapshots/legacy-resolved-catalog-v0/resolved/objects.jsonl"
SOURCE_LOCK = ROOT / "catalog/sources.lock.json"
BASELINE = (90, 91, 92, 93, 95)
TARGET_ID = "schuss-compute-target-000001"
BACKEND_ID = "schuss-backend-000002"
MANIFEST_SHA256 = "0e3f3cb763f634ce490195e2cd4665c2e1a41764cd54c6526e6e219f18e1e959"
MUTABLE_TAG = "mutable-instruments-derived"


CANDIDATES: tuple[dict[str, Any], ...] = (
    {"slug": "attack-decay", "source": 53, "variant": 113, "family": 33, "contract": 14, "native": 97, "operation": 15, "eligibility": 33, "level2": 45, "level3": 60, "name": "Attack-Decay Envelope", "category": "modulation-control", "opcode": "attack-decay-envelope-q27", "rate": "control", "dependencies": ["arm-fixed-point-runtime", "ksoloti-pitch-runtime"], "requirements": ["exact Q27 control facets", "retained fixed-point and pitch-runtime identities"], "exclusions": ["source artifact generation", "ARM/device timing equivalence"]},
    {"slug": "logic-toggle", "source": 49, "variant": 229, "family": 29, "contract": 10, "native": 98, "operation": 16, "eligibility": 34, "level2": 46, "level3": 61, "name": "Clocked Logic Toggle", "category": "timing-sequencing", "opcode": "rising-edge-toggle-bool32", "rate": "control", "dependencies": [], "requirements": ["exact Boolean control facets", "retained rising-edge state identity"], "exclusions": ["scheduler behavior outside the operation contract", "device timing"]},
    {"slug": "pseudo-euclidean", "source": 50, "variant": 1208, "family": 30, "contract": 11, "native": 99, "operation": 17, "eligibility": 35, "level2": 47, "level3": 62, "name": "Pseudo-Euclidean Gate Sequencer", "category": "timing-sequencing", "opcode": "pseudo-euclidean-gate-control", "rate": "control", "dependencies": ["ksoloti-runtime-random"], "requirements": ["exact control facets and attributes", "retained random-runtime identity"], "exclusions": ["statistical validation", "realtime scheduling"]},
    {"slug": "struck-drum", "source": 57, "variant": 527, "family": 37, "contract": 18, "native": 100, "operation": 18, "eligibility": 36, "level2": 48, "level3": 63, "name": "Struck Drum Voice", "category": "sound-sources", "opcode": "struck-drum-voice-q27", "rate": "audio", "dependencies": ["brds-digital-header"], "requirements": ["exact Q27 audio/control facets", "exact Braids header locator"], "exclusions": ["provenance-only support inference", "ARM/device/audible behavior"], "provenance": [MUTABLE_TAG]},
    {"slug": "struck-bell", "source": 58, "variant": 526, "family": 38, "contract": 19, "native": 101, "operation": 19, "eligibility": 37, "level2": 49, "level3": 64, "name": "Struck Bell Voice", "category": "sound-sources", "opcode": "struck-bell-voice-q27", "rate": "audio", "dependencies": ["brds-digital-header"], "requirements": ["exact Q27 audio/control facets", "exact Braids header locator"], "exclusions": ["provenance-only support inference", "ARM/device/audible behavior"], "provenance": [MUTABLE_TAG]},
    {"slug": "uniform-noise", "source": 8, "variant": 499, "family": 4, "contract": 22, "native": 102, "operation": 20, "eligibility": 38, "level2": 50, "level3": 65, "name": "Uniform Noise", "category": "sound-sources", "opcode": "uniform-noise-audio-q27", "rate": "audio", "dependencies": ["ksoloti-runtime-random"], "requirements": ["exact bipolar Q27 audio outlet", "retained random-runtime identity"], "exclusions": ["distribution measurement", "audible behavior"]},
    {"slug": "standard-adsr", "source": 11, "variant": 115, "family": 7, "contract": 23, "native": 103, "operation": 21, "eligibility": 39, "level2": 51, "level3": 66, "name": "Standard ADSR", "category": "modulation-control", "opcode": "adsr-envelope-control-q27", "rate": "control", "dependencies": ["arm-fixed-point-runtime", "ksoloti-pitch-runtime"], "requirements": ["exact gate/envelope facets", "exact four-parameter standard variant"], "exclusions": ["looping ADSR sibling", "ARM/device timing equivalence"]},
    {"slug": "sine-lfo", "source": 13, "variant": 208, "family": 8, "contract": 24, "native": 104, "operation": 22, "eligibility": 40, "level2": 52, "level3": 67, "name": "Standard Sine LFO", "category": "modulation-control", "opcode": "sine-lfo-control-q27", "rate": "control", "dependencies": ["ksoloti-pitch-runtime", "ksoloti-sine-table-runtime"], "requirements": ["exact bipolar Q27 control facets", "standard factory variant identity"], "exclusions": ["extended slow-range sibling", "rate accuracy measurement"]},
    {"slug": "decay-envelope", "source": 69, "variant": 123, "family": 49, "contract": 25, "native": 105, "operation": 23, "eligibility": 41, "level2": 53, "level3": 68, "name": "Decay Envelope", "category": "modulation-control", "opcode": "decay-envelope-control-q27", "rate": "control", "dependencies": ["arm-fixed-point-runtime", "ksoloti-pitch-runtime"], "requirements": ["exact trigger/envelope facets", "retained decay transfer identity"], "exclusions": ["host/device timing equivalence", "audible behavior"]},
    {"slug": "control-lowpass", "source": 64, "variant": 199, "family": 44, "contract": 26, "native": 106, "operation": 24, "eligibility": 42, "level2": 54, "level3": 69, "name": "Control Low-pass Filter", "category": "filters-resonators", "opcode": "control-lowpass-q27", "rate": "control", "dependencies": ["arm-fixed-point-runtime", "ksoloti-pitch-runtime"], "requirements": ["exact control-rate facets", "retained pitch/fixed-point identities"], "exclusions": ["audio-rate substitution", "frequency-response measurement"]},
    {"slug": "resonant-audio-lowpass", "source": 70, "variant": 162, "family": 50, "contract": 27, "native": 107, "operation": 25, "eligibility": 43, "level2": 55, "level3": 70, "name": "Two-pole Resonant Audio Low-pass", "category": "filters-resonators", "opcode": "two-pole-resonant-lowpass-audio-q27", "rate": "audio", "dependencies": ["ksoloti-biquad-runtime", "ksoloti-pitch-runtime"], "requirements": ["exact audio/pitch/resonance facets", "retained biquad and pitch-runtime identities"], "exclusions": ["stability/resource measurement", "frequency-response measurement"]},
    {"slug": "saturating-gain", "source": 78, "variant": 318, "family": 58, "contract": 28, "native": 108, "operation": 26, "eligibility": 44, "level2": 56, "level3": 71, "name": "Saturating Gain", "category": "shaping-dynamics", "opcode": "saturating-gain-audio-q27", "rate": "audio", "dependencies": ["arm-fixed-point-runtime"], "requirements": ["definition index 1 audio overload", "exact Q27 fixed-point identity"], "exclusions": ["control overload", "audible behavior"]},
    {"slug": "two-input-mixer", "source": 77, "variant": 421, "family": 57, "contract": 29, "native": 109, "operation": 27, "eligibility": 45, "level2": 57, "level3": 72, "name": "Two-input Audio Mixer", "category": "mixing-routing", "opcode": "two-input-mixer-audio-q27", "rate": "audio", "dependencies": ["arm-fixed-point-runtime"], "requirements": ["definition index 1 audio overload", "exact bus/two-input/gain facets"], "exclusions": ["other mixer arities", "control-rate variants"]},
    {"slug": "audio-addition", "source": 34, "variant": 255, "family": 23, "contract": 30, "native": 110, "operation": 28, "eligibility": 46, "level2": 58, "level3": 73, "name": "Audio-rate Addition", "category": "mixing-routing", "opcode": "addition-audio-q27", "rate": "audio", "dependencies": [], "requirements": ["definition index 1 audio overload", "exact two-input Q27 addition facets"], "exclusions": ["control-rate addition", "integer addition"]},
    {"slug": "triggered-value-latch", "source": 74, "variant": 224, "family": 54, "contract": 31, "native": 111, "operation": 29, "eligibility": 47, "level2": 59, "level3": 74, "name": "Triggered Value Latch", "category": "data-math-logic", "opcode": "triggered-value-latch-control-q27", "rate": "control", "dependencies": [], "requirements": ["exact fractional-control overload", "retained rising-edge latch state"], "exclusions": ["Boolean latch alternative", "integer latch alternative"]},
)


def _canonical_bytes(value: Any) -> bytes:
    return core.canonical_json(value).encode("utf-8") + b"\n"


def _record(value: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(value)
    result["content_hash"] = "sha256:" + "0" * 64
    errors = core.schema_errors(result, schema, schema)
    if errors:
        raise ValueError("; ".join(errors))
    result["content_hash"] = core.record_content_hash(result, schema)
    return result


def _ref(record: dict[str, Any], field: str) -> dict[str, Any]:
    return {field: record[field], "revision": record["revision"], "content_hash": record["content_hash"]}


def _semantic_ref(record: dict[str, Any], field: str) -> dict[str, Any]:
    return {"input_kind": "semantic-record", "stable_id": record[field], "revision": record["revision"], "content_hash": record["content_hash"]}


def _observations() -> dict[int, dict[str, Any]]:
    result = {item["variant_index"]: item for item in core.load_jsonl(OBSERVATIONS)}
    wanted = {item["variant"] for item in CANDIDATES}
    if not wanted <= set(result):
        raise ValueError("Task 028 exact source observation is absent")
    return {key: result[key] for key in wanted}


def _source_commits() -> dict[str, str]:
    lock = core.load_json(SOURCE_LOCK)
    return {item["id"]: item["commit"] for item in lock["sources"]}


def _source_identity(spec: dict[str, Any], observation: dict[str, Any], commits: dict[str, str]) -> dict[str, Any]:
    origin = observation["origin"]
    expected_ref = f"legacy-resolved-catalog-v0:object:{spec['variant']}"
    if origin["source_id"] not in commits or observation["variant_index"] != spec["variant"]:
        raise ValueError("Task 028 source lock/observation mismatch")
    return {
        "catalog_implementation_id": f"schuss-implementation-{spec['source']:06d}",
        "observation_reference": expected_ref,
        "variant_index": spec["variant"],
        "legacy_id": observation["legacy_id"],
        "legacy_uuid_sha256": "sha256:" + hashlib.sha256(observation["uuid"]["durable_value"].encode("utf-8")).hexdigest(),
        "source_id": origin["source_id"],
        "source_commit": commits[origin["source_id"]],
        "portable_path": origin["path"],
        "definition_index": origin["definition_index"],
        "byte_sha256": origin["sha256"],
        "canonical_observation_sha256": hashlib.sha256(core.canonical_json(observation).encode("utf-8")).hexdigest(),
        "provenance_tags": sorted(spec.get("provenance", [])),
    }


def _schemas() -> dict[str, dict[str, Any]]:
    content_hash = {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"}
    raw_sha = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
    string_set = {
        "type": "array", "x-schuss-array-kind": "set", "uniqueItems": True,
        "items": {"type": "string", "minLength": 1},
    }
    string_sequence = {
        "type": "array", "x-schuss-array-kind": "sequence", "minItems": 1,
        "items": {"type": "string", "minLength": 1},
    }

    def exact_ref(field: str, pattern: str) -> dict[str, Any]:
        return {
            "type": "object", "additionalProperties": False,
            "required": [field, "revision", "content_hash"],
            "properties": {
                field: {"type": "string", "pattern": pattern},
                "revision": {"type": "integer", "minimum": 1},
                "content_hash": content_hash,
            },
        }

    family_ref = exact_ref("family_id", "^schuss-family-[0-9]{6}$")
    contract_ref = exact_ref("component_contract_id", "^schuss-component-contract-[0-9]{6}$")
    binding_ref = exact_ref("implementation_id", "^schuss-implementation-[0-9]{6}$")
    eligibility_ref = exact_ref("binding_eligibility_id", "^schuss-binding-eligibility-[0-9]{6}$")
    operation_ref = exact_ref("direct_operation_spec_id", "^schuss-direct-operation-spec-[0-9]{6}$")
    evidence_ref = exact_ref("evidence_claim_id", "^schuss-evidence-claim-[0-9]{6}$")
    target_ref = exact_ref("compute_target_id", "^schuss-compute-target-[0-9]{6}$")
    backend_ref = exact_ref("backend_id", "^schuss-backend-[0-9]{6}$")
    packet_ref = exact_ref("selection_packet_id", "^schuss-core-selection-[0-9]{6}$")
    proof_ref = exact_ref("palette_lowering_proof_id", "^schuss-palette-lowering-proof-[0-9]{6}$")

    source_identity = {
        "type": "object", "additionalProperties": False,
        "required": [
            "catalog_implementation_id", "observation_reference", "variant_index",
            "legacy_id", "legacy_uuid_sha256", "source_id", "source_commit",
            "portable_path", "definition_index", "byte_sha256",
            "canonical_observation_sha256", "provenance_tags",
        ],
        "properties": {
            "catalog_implementation_id": {"type": "string", "pattern": "^schuss-implementation-[0-9]{6}$"},
            "observation_reference": {"type": "string", "pattern": "^legacy-resolved-catalog-v0:object:[0-9]+$"},
            "variant_index": {"type": "integer", "minimum": 0},
            "legacy_id": {"type": "string", "minLength": 1},
            "legacy_uuid_sha256": content_hash,
            "source_id": {"enum": ["axoloti-factory", "axoloti-contrib"]},
            "source_commit": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
            "portable_path": {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9._ +%-]*(?:/[A-Za-z0-9][A-Za-z0-9._ +%-]*)*$"},
            "definition_index": {"type": "integer", "minimum": 0},
            "byte_sha256": raw_sha,
            "canonical_observation_sha256": raw_sha,
            "provenance_tags": string_set,
        },
    }
    evidence_level = {
        "type": "object", "additionalProperties": False,
        "required": ["level", "status"],
        "properties": {
            "level": {"type": "integer", "minimum": 1, "maximum": 8},
            "status": {"enum": ["passed", "not-run"]},
        },
    }
    candidate = {
        "type": "object", "additionalProperties": False,
        "required": [
            "candidate_id", "display_name", "functional_category", "family_reference",
            "source_identity", "contract_reference", "native_binding_reference",
            "eligibility_reference", "operation_spec_reference", "level2_evidence_reference",
            "requirements", "exclusions", "evidence_gap",
        ],
        "properties": {
            "candidate_id": {"type": "string", "pattern": "^task028-candidate-[0-9]{6}$"},
            "display_name": {"type": "string", "minLength": 1},
            "functional_category": {"enum": [
                "sound-sources", "modulation-control", "filters-resonators",
                "shaping-dynamics", "mixing-routing", "timing-sequencing", "data-math-logic",
            ]},
            "family_reference": family_ref,
            "source_identity": source_identity,
            "contract_reference": contract_ref,
            "native_binding_reference": binding_ref,
            "eligibility_reference": eligibility_ref,
            "operation_spec_reference": operation_ref,
            "level2_evidence_reference": evidence_ref,
            "requirements": string_set,
            "exclusions": string_set,
            "evidence_gap": string_set,
        },
    }
    baseline_entry = {
        "type": "object", "additionalProperties": False,
        "required": ["native_binding_reference", "counting_basis"],
        "properties": {
            "native_binding_reference": binding_ref,
            "counting_basis": {"const": "task025-accepted-direct-promotion"},
        },
    }
    packet_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "task028-selection-packet-v0.schema.json",
        "title": "Schuss exact Task 028 fifteen-candidate palette selection packet v0",
        "type": "object", "additionalProperties": False,
        "required": [
            "schema_version", "canonical_profile", "selection_packet_id", "revision",
            "content_hash", "parent_record_set_reference", "catalog_reference",
            "target_reference", "backend_reference", "counting_rule", "baseline",
            "additions", "final_safe_selectable_total", "supporting_profile_not_counted",
            "retained_gates", "evidence_levels", "decision_record",
        ],
        "properties": {
            "schema_version": {"const": "task028-selection-packet-v0"},
            "canonical_profile": {"const": "schuss-canonical-json-v1"},
            "selection_packet_id": {"const": "schuss-core-selection-000003"},
            "revision": {"const": 1}, "content_hash": content_hash,
            "parent_record_set_reference": exact_ref("record_set_id", "^schuss-record-set-[0-9]{6}$"),
            "catalog_reference": exact_ref("catalog_id", "^schuss-catalog-[0-9]{6}$"),
            "target_reference": target_ref, "backend_reference": backend_ref,
            "counting_rule": {"const": "five-task025-promotions-plus-fifteen-task028-promotions-only"},
            "baseline": {"type": "array", "x-schuss-array-kind": "sequence", "minItems": 5, "maxItems": 5, "items": baseline_entry},
            "additions": {"type": "array", "x-schuss-array-kind": "sequence", "minItems": 15, "maxItems": 15, "items": candidate},
            "final_safe_selectable_total": {"const": 20},
            "supporting_profile_not_counted": {"type": "array", "x-schuss-array-kind": "set", "uniqueItems": True, "minItems": 7, "maxItems": 7, "items": binding_ref},
            "retained_gates": string_set,
            "evidence_levels": {"type": "array", "x-schuss-array-kind": "sequence", "minItems": 8, "maxItems": 8, "items": evidence_level},
            "decision_record": {
                "type": "object", "additionalProperties": False,
                "required": ["portable_path", "byte_sha256"],
                "properties": {
                    "portable_path": {"const": "contracts/task028/palette-curation-decision.md"},
                    "byte_sha256": raw_sha,
                },
            },
        },
    }

    operation_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "direct-operation-spec-v3.schema.json",
        "title": "Schuss exact Task 028 normalized direct operation specification v3",
        "type": "object", "additionalProperties": False,
        "required": [
            "schema_version", "canonical_profile", "direct_operation_spec_id", "revision",
            "content_hash", "opcode", "compatibility_mode", "rate_domain",
            "family_reference", "contract_reference", "native_binding_reference",
            "source_identity", "runtime_dependencies", "numeric_semantics",
            "state_semantics", "schedule_semantics", "requirements", "exclusions",
            "evidence_boundary",
        ],
        "properties": {
            "schema_version": {"const": "direct-operation-spec-v3"},
            "canonical_profile": {"const": "schuss-canonical-json-v1"},
            "direct_operation_spec_id": {"type": "string", "pattern": "^schuss-direct-operation-spec-0000(?:1[5-9]|2[0-9])$"},
            "revision": {"const": 1}, "content_hash": content_hash,
            "opcode": {"type": "string", "pattern": "^[a-z0-9]+(?:-[a-z0-9]+)*$"},
            "compatibility_mode": {"const": "exact-source-identity-normalized-lowering-task028-v1"},
            "rate_domain": {"enum": ["audio", "control"]},
            "family_reference": family_ref, "contract_reference": contract_ref,
            "native_binding_reference": binding_ref, "source_identity": source_identity,
            "runtime_dependencies": string_set, "numeric_semantics": string_sequence,
            "state_semantics": string_sequence, "schedule_semantics": string_sequence,
            "requirements": string_set, "exclusions": string_set,
            "evidence_boundary": {"const": "backend-lowering-ir-only-levels-1-through-3"},
        },
    }

    lowered_operation = {
        "type": "object", "additionalProperties": False,
        "required": [
            "candidate_id", "family_reference", "source_identity", "contract_reference",
            "native_binding_reference", "eligibility_reference", "operation_spec_reference",
            "selection_status", "opcode", "rate_domain", "facet_lowering",
            "runtime_dependencies", "state_semantics", "schedule_semantics", "exclusions",
        ],
        "properties": {
            "candidate_id": {"type": "string", "pattern": "^task028-candidate-[0-9]{6}$"},
            "family_reference": family_ref, "source_identity": source_identity,
            "contract_reference": contract_ref, "native_binding_reference": binding_ref,
            "eligibility_reference": eligibility_ref, "operation_spec_reference": operation_ref,
            "selection_status": {"const": "selected"},
            "opcode": {"type": "string", "pattern": "^[a-z0-9]+(?:-[a-z0-9]+)*$"},
            "rate_domain": {"enum": ["audio", "control"]},
            "facet_lowering": {
                "type": "array", "x-schuss-array-kind": "set", "uniqueItems": True, "minItems": 1,
                "items": {
                    "type": "object", "additionalProperties": False,
                    "required": ["facet_kind", "facet_id", "native_symbol"],
                    "properties": {
                        "facet_kind": {"enum": ["port", "parameter", "attribute", "action", "display"]},
                        "facet_id": {"type": "string", "pattern": "^component-(?:port|parameter|attribute|action|display)-[0-9]{6}$"},
                        "native_symbol": {"type": "string", "pattern": "^[A-Za-z_][A-Za-z0-9_:.-]*$"},
                    },
                },
            },
            "runtime_dependencies": string_set, "state_semantics": string_sequence,
            "schedule_semantics": string_sequence, "exclusions": string_set,
        },
    }
    proof_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "palette-lowering-proof-v0.schema.json",
        "title": "Schuss exact Task 028 palette selection/lowering proof v0",
        "type": "object", "additionalProperties": False,
        "required": [
            "schema_version", "canonical_profile", "palette_lowering_proof_id", "revision",
            "content_hash", "selection_packet_reference", "target_reference",
            "backend_reference", "lowering_boundary", "selection_count", "operations",
            "evidence_levels", "actions_performed",
        ],
        "properties": {
            "schema_version": {"const": "palette-lowering-proof-v0"},
            "canonical_profile": {"const": "schuss-canonical-json-v1"},
            "palette_lowering_proof_id": {"const": "schuss-palette-lowering-proof-000001"},
            "revision": {"const": 1}, "content_hash": content_hash,
            "selection_packet_reference": packet_ref, "target_reference": target_ref,
            "backend_reference": backend_ref,
            "lowering_boundary": {"const": "normalized-operation-ir-only"},
            "selection_count": {"const": 15},
            "operations": {"type": "array", "x-schuss-array-kind": "sequence", "minItems": 15, "maxItems": 15, "items": lowered_operation},
            "evidence_levels": {"type": "array", "x-schuss-array-kind": "sequence", "minItems": 8, "maxItems": 8, "items": evidence_level},
            "actions_performed": {
                "type": "object", "additionalProperties": False,
                "required": ["source_artifact_generation", "arm_compile_or_link", "java_or_legacy_axp", "device_or_hardware", "realtime_or_resource_measurement", "audible_listening", "git_or_publication"],
                "properties": {key: {"const": False} for key in (
                    "source_artifact_generation", "arm_compile_or_link", "java_or_legacy_axp",
                    "device_or_hardware", "realtime_or_resource_measurement",
                    "audible_listening", "git_or_publication",
                )},
            },
        },
    }
    return {
        "task028-selection-packet-v0.schema.json": packet_schema,
        "direct-operation-spec-v3.schema.json": operation_schema,
        "palette-lowering-proof-v0.schema.json": proof_schema,
    }


def _task028_parameter(index: int, key: str, label: str, kind: str, default: str) -> dict[str, Any]:
    value = task017._parameter(index, key, label, kind, default)
    domain = value.get("domain", {})
    if domain.get("status") == "unresolved":
        domain.update(
            {
                "owner": "task-028",
                "rationale": "The exact legacy parameter class is retained, but Task 028 proves only normalized local lowering and does not promote a target-independent transfer curve.",
                "question": "What later cross-target authoring domain preserves this exact legacy parameter transfer?",
            }
        )
    return value


def _new_contract_shape(slug: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    p = task017._port
    s = task017._state
    parameter = _task028_parameter
    if slug == "uniform-noise":
        return [p(1, "wave", "Wave", "outlet", "audio", False, "audio")], [], []
    if slug == "standard-adsr":
        return (
            [p(1, "gate", "Gate", "inlet", "clock", True, "gate"), p(2, "envelope", "Envelope", "outlet", "positive", False, "modulation")],
            [parameter(1, "attack", "Attack", "time", "0"), parameter(2, "decay", "Decay", "time", "0"), parameter(3, "sustain", "Sustain", "positive", "0.5"), parameter(4, "release", "Release", "time", "0")],
            [s(1, "stage"), s(2, "gate-history", "boolean"), s(3, "envelope-value")],
        )
    if slug == "sine-lfo":
        return (
            [p(1, "pitch", "Pitch", "inlet", "pitch", False, "modulation"), p(2, "wave", "Wave", "outlet", "control", False, "modulation")],
            [parameter(1, "base-pitch", "Pitch", "pitch", "-48")],
            [s(1, "phase")],
        )
    if slug == "decay-envelope":
        return (
            [p(1, "trigger", "Trigger", "inlet", "clock", True, "trigger"), p(2, "envelope", "Envelope", "outlet", "positive", False, "modulation")],
            [parameter(1, "decay", "Decay", "time", "0")],
            [s(1, "trigger-history", "boolean"), s(2, "envelope-value")],
        )
    if slug == "control-lowpass":
        return (
            [p(1, "input", "Input", "inlet", "control", True, "generic-signal"), p(2, "output", "Output", "outlet", "control", False, "generic-signal")],
            [parameter(1, "frequency", "Frequency", "pitch", "-48")],
            [s(1, "filtered-value")],
        )
    if slug == "resonant-audio-lowpass":
        return (
            [p(1, "audio-input", "Audio Input", "inlet", "audio", True, "audio"), p(2, "pitch", "Pitch", "inlet", "pitch", False, "modulation"), p(3, "resonance", "Resonance", "inlet", "positive", False, "modulation"), p(4, "audio-output", "Audio Output", "outlet", "audio", False, "audio")],
            [parameter(1, "base-pitch", "Pitch", "pitch", "0"), parameter(2, "base-resonance", "Resonance", "positive", "0")],
            [s(1, "biquad-state", "structured")],
        )
    if slug == "saturating-gain":
        return (
            [p(1, "audio-input", "Audio Input", "inlet", "audio", True, "audio"), p(2, "audio-output", "Audio Output", "outlet", "audio", False, "audio")],
            [parameter(1, "gain", "Gain", "time", "0")],
            [],
        )
    if slug == "two-input-mixer":
        return (
            [p(1, "bus-input", "Bus Input", "inlet", "audio", False, "audio"), p(2, "input-one", "Input 1", "inlet", "audio", True, "audio"), p(3, "input-two", "Input 2", "inlet", "audio", True, "audio"), p(4, "audio-output", "Audio Output", "outlet", "audio", False, "audio")],
            [parameter(1, "gain-one", "Gain 1", "positive", "0.5"), parameter(2, "gain-two", "Gain 2", "positive", "0.5")],
            [],
        )
    if slug == "audio-addition":
        return (
            [p(1, "input-one", "Input 1", "inlet", "audio", True, "audio"), p(2, "input-two", "Input 2", "inlet", "audio", True, "audio"), p(3, "audio-output", "Audio Output", "outlet", "audio", False, "audio")],
            [],
            [],
        )
    if slug == "triggered-value-latch":
        return (
            [p(1, "input", "Input", "inlet", "control", True, "generic-signal"), p(2, "trigger", "Trigger", "inlet", "clock", True, "trigger"), p(3, "output", "Output", "outlet", "control", False, "generic-signal")],
            [],
            [s(1, "latched-value"), s(2, "trigger-history", "boolean")],
        )
    raise KeyError(slug)


def _contracts(
    candidates: tuple[dict[str, Any], ...],
    family_references: dict[int, dict[str, Any]],
    parent_contracts: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    schema = core.load_json(ROOT / "schemas/component-contract-v1.schema.json")
    exact_parent = {
        (item["component_contract_id"], item["revision"], item["content_hash"]): item
        for item in parent_contracts
    }
    result: dict[str, dict[str, Any]] = {}
    for spec in candidates:
        identifier = f"schuss-component-contract-{spec['contract']:06d}"
        existing = [item for item in parent_contracts if item["component_contract_id"] == identifier and item["revision"] == 1]
        if spec["contract"] <= 21:
            if len(existing) != 1 or (identifier, 1, existing[0]["content_hash"]) not in exact_parent:
                raise ValueError(f"Task 028 exact reused contract is absent: {identifier}@1")
            result[spec["slug"]] = existing[0]
            continue
        if existing:
            raise ValueError(f"Task 028 component-contract allocation collides: {identifier}")
        ports, parameters, states = _new_contract_shape(spec["slug"])
        lifecycle = {
            "state_model": "declared-state" if states else "stateless",
            "initialization": "initialize-declared-state" if states else "none",
            "reset_behavior": "declared-per-state" if states else "not-applicable",
            "disposal": "none",
        }
        value = {
            "schema_version": "component-contract-v1", "canonical_profile": "schuss-canonical-json-v1",
            "component_contract_id": identifier, "revision": 1,
            "family_reference": family_references[spec["family"]], "display_name": spec["name"],
            "ports": ports, "parameters": parameters, "attributes": [], "actions": [], "displays": [],
            "state_declarations": states, "lifecycle": lifecycle,
            "binding_capabilities": {"parameter_input_ports": [], "action_inputs": []},
            "capability_requirements": [], "compound_interface": {"kind": "primitive", "mapping_keys": []},
            "compatibility_claims": [], "behavior_rules": [],
        }
        result[spec["slug"]] = _record(value, schema)
    return result


def _facet_pairs(contract: dict[str, Any]) -> list[tuple[str, str]]:
    values: list[tuple[str, str]] = []
    for collection, kind in (("ports", "port"), ("parameters", "parameter"), ("attributes", "attribute"), ("actions", "action"), ("displays", "display")):
        values.extend((kind, item["facet_id"]) for item in contract[collection])
    return values


def _private_state(spec: dict[str, Any], contract: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for state in contract["state_declarations"]:
        kind = {"integer": "integer", "boolean": "integer", "bytes": "bytes", "structured": "structured", "exact-decimal": "fixed-point"}[state["value_kind"]]
        result.append({"state_key": state["semantic_key"], "value_kind": kind})
    return result


def _native_binding(spec: dict[str, Any], contract: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    schema = core.load_json(ROOT / "schemas/implementation-binding-v1.schema.json")
    symbol = "schuss_direct_task028_" + spec["slug"].replace("-", "_")
    mappings = []
    for index, (kind, facet_id) in enumerate(_facet_pairs(contract), start=1):
        mappings.append(
            {
                "mapping_id": f"binding-map-{spec['native'] * 100 + index:06d}",
                "contract_facet": {"facet_kind": kind, "facet_id": facet_id},
                "implementation_seam": {"seam_kind": "native-symbol", "symbol": f"{symbol}_{facet_id.replace('-', '_')}"},
            }
        )
    evidence_ref = source["observation_reference"]
    return _record(
        {
            "schema_version": "implementation-binding-v1", "canonical_profile": "schuss-canonical-json-v1",
            "implementation_id": f"schuss-implementation-{spec['native']:06d}", "revision": 1,
            "contract_reference": _ref(contract, "component_contract_id"),
            "realization": {"form": "native-cpp", "portable_symbol": symbol},
            "facet_mappings": mappings,
            "observed_dependencies": [{"dependency_id": item, "evidence_ref": evidence_ref} for item in spec["dependencies"]],
            "private_state": _private_state(spec, contract),
            "selection_state": {
                "status": "not-evaluated", "owner": "task-007",
                "reason": "target-backend-contracts-not-yet-implemented",
                "rationale": "Task 028 supplies a separate exact eligibility record; this binding alone is not an implicit support decision.",
            },
            "evidence_refs": sorted([evidence_ref, "fixture:task028-palette-lowering"]),
        },
        schema,
    )


def _operation_spec(
    spec: dict[str, Any], contract: dict[str, Any], binding: dict[str, Any], source: dict[str, Any], schema: dict[str, Any]
) -> dict[str, Any]:
    states = [item["semantic_key"] for item in contract["state_declarations"]]
    return _record(
        {
            "schema_version": "direct-operation-spec-v3", "canonical_profile": "schuss-canonical-json-v1",
            "direct_operation_spec_id": f"schuss-direct-operation-spec-{spec['operation']:06d}", "revision": 1,
            "opcode": spec["opcode"],
            "compatibility_mode": "exact-source-identity-normalized-lowering-task028-v1",
            "rate_domain": spec["rate"],
            "family_reference": copy.deepcopy(contract["family_reference"]),
            "contract_reference": _ref(contract, "component_contract_id"),
            "native_binding_reference": _ref(binding, "implementation_id"),
            "source_identity": copy.deepcopy(source),
            "runtime_dependencies": sorted(spec["dependencies"]),
            "numeric_semantics": ["Q27 and Boolean facet representations remain those of the exact component contract.", *spec["requirements"]],
            "state_semantics": (["Component-instance state is explicit: " + ", ".join(states) + "."] if states else ["The normalized operation declares no component-instance state."]),
            "schedule_semantics": [f"One normalized {spec['rate']}-domain operation is emitted; scheduler and runtime execution are outside Task 028."],
            "requirements": sorted(spec["requirements"]), "exclusions": sorted(spec["exclusions"]),
            "evidence_boundary": "backend-lowering-ir-only-levels-1-through-3",
        },
        schema,
    )


def _evidence_claim(
    spec: dict[str, Any],
    level: int,
    subject: dict[str, Any],
    inputs: list[dict[str, Any]],
    schema: dict[str, Any],
) -> dict[str, Any]:
    number = spec["level2"] if level == 2 else spec["level3"]
    return _record(
        {
            "schema_version": "evidence-claim-v0", "canonical_profile": "schuss-canonical-json-v1",
            "evidence_claim_id": f"schuss-evidence-claim-{number:06d}", "revision": 1,
            "level": level,
            "level_name": "component-graph-resolution" if level == 2 else "backend-lowering",
            "subject_reference": {
                "subject_kind": "semantic-record",
                "stable_id": subject["implementation_id"], "revision": subject["revision"],
                "content_hash": subject["content_hash"],
                "stage": "target-independent-graph-validation" if level == 2 else "backend-lowering",
            },
            "method": "task028-exact-source-interface-and-binding-review" if level == 2 else "task028-independent-resolver-and-normalized-operation-ir",
            "outcome": "passed", "evidence_inputs": inputs,
            "limitations": sorted(
                [
                    "The claim stops at exact local component/binding resolution." if level == 2 else "The claim stops at normalized operation IR and emits no source artifact.",
                    "No ARM compile/link, Java, legacy AXP, device, realtime/resource, audible, Git, or publication evidence is established.",
                    "Catalog presence, source attribution, and retained Ksoloti behavior are not later-stage evidence.",
                ]
            ),
            "producer_identity": {
                "producer_kind": "validator", "producer_id": "schuss-task028-validator",
                "version": "task028-v1",
                "content_hash": "sha256:" + hashlib.sha256(b"schuss-task028-validator-v1").hexdigest(),
            },
        },
        schema,
    )


def _eligibility(
    spec: dict[str, Any], contract: dict[str, Any], binding: dict[str, Any],
    claim: dict[str, Any], compute_target: dict[str, Any], backend: dict[str, Any],
) -> dict[str, Any]:
    schema = core.load_json(ROOT / "schemas/binding-eligibility-v0.schema.json")
    evidence_reference = _ref(claim, "evidence_claim_id")
    dependencies = []
    if "brds-digital-header" in spec["dependencies"]:
        dependencies.append(
            {
                "dependency_id": "brds-digital-header",
                "portable_locator": "sha256/e132f0d876ea54c26f301e448f1c079243433aaa7acf7743a35c928e9c3d95c4",
                "state": {"status": "supported", "evidence_refs": [f"legacy-resolved-catalog-v0:object:{spec['variant']}"]},
            }
        )
    return _record(
        {
            "schema_version": "binding-eligibility-v0", "canonical_profile": "schuss-canonical-json-v1",
            "binding_eligibility_id": f"schuss-binding-eligibility-{spec['eligibility']:06d}", "revision": 1,
            "binding_reference": _ref(binding, "implementation_id"),
            "contract_reference": _ref(contract, "component_contract_id"),
            "allowed_pair": {
                "target_reference": _ref(compute_target, "compute_target_id"),
                "backend_reference": _ref(backend, "backend_id"),
                "state": {"status": "supported", "evidence_level": 2, "evidence_refs": [evidence_reference]},
            },
            "realization_form": "native-cpp",
            "capability_requirements": copy.deepcopy(backend["required_target_capabilities"]),
            "dependency_requirements": dependencies, "resource_requirements": [],
            "required_evidence_level": 2, "compatibility_evidence": [evidence_reference],
            "selection_policy": {
                "policy_id": f"schuss-selection-policy-{spec['eligibility']:06d}",
                "version": 1, "priority": 400, "ranking_rule": "higher-explicit-priority",
                "tie_behavior": "ambiguous", "implicit_fallback": False,
            },
            "unresolved_questions": [],
        },
        schema,
    )


def _packet(
    parent_manifest: dict[str, Any], catalog: dict[str, Any], compute_target: dict[str, Any],
    backend: dict[str, Any], baseline_bindings: list[dict[str, Any]],
    supporting_bindings: list[dict[str, Any]], candidates: list[dict[str, Any]],
    schema: dict[str, Any],
) -> dict[str, Any]:
    return _record(
        {
            "schema_version": "task028-selection-packet-v0", "canonical_profile": "schuss-canonical-json-v1",
            "selection_packet_id": "schuss-core-selection-000003", "revision": 1,
            "parent_record_set_reference": {key: parent_manifest[key] for key in ("record_set_id", "revision", "content_hash")},
            "catalog_reference": _ref(catalog, "catalog_id"),
            "target_reference": _ref(compute_target, "compute_target_id"),
            "backend_reference": _ref(backend, "backend_id"),
            "counting_rule": "five-task025-promotions-plus-fifteen-task028-promotions-only",
            "baseline": [
                {"native_binding_reference": _ref(item, "implementation_id"), "counting_basis": "task025-accepted-direct-promotion"}
                for item in baseline_bindings
            ],
            "additions": candidates,
            "final_safe_selectable_total": 20,
            "supporting_profile_not_counted": [_ref(item, "implementation_id") for item in supporting_bindings],
            "retained_gates": sorted(
                [
                    "Rings reverb source implementation 000056 remains unsupported and native allocation 000094 remains absent.",
                    "Extended physical resonator implementation 000096 remains catalogued-only without an exact direct binding.",
                    "Transparent compounds and all candidates outside the exact fifteen-entry cohort remain deferred.",
                    "Levels 4-8 remain not-run; no source artifact, ARM, device, realtime/resource, or audible claim is made.",
                ]
            ),
            "evidence_levels": [{"level": level, "status": "passed" if level <= 3 else "not-run"} for level in range(1, 9)],
            "decision_record": {"portable_path": "contracts/task028/palette-curation-decision.md", "byte_sha256": core.sha256_file(DECISION)},
        },
        schema,
    )


def _projection(parent_context: Any, parent_manifest: dict[str, Any]) -> dict[str, Any]:
    catalog = parent_context.records["catalog"][0]
    records = dict(parent_context.records)
    return catalog_projection.build_catalog_projection(
        corpus=copy.deepcopy(catalog),
        corpus_schema=core.load_json(ROOT / "schemas/catalog-corpus-v4.schema.json"),
        projection_schema=core.load_json(ROOT / "schemas/catalog-projection-v4.schema.json"),
        overlay=copy.deepcopy(parent_context.overlay),
        overlay_sha256=parent_context.overlay_sha256,
        observations=copy.deepcopy(parent_context.observations),
        records=records,
        record_set_reference={key: parent_manifest[key] for key in ("record_set_id", "revision", "content_hash")},
        core=core,
    )


def _projection_indexes(projection: dict[str, Any]) -> tuple[dict[int, dict[str, Any]], dict[int, tuple[dict[str, Any], dict[str, Any]]]]:
    families: dict[int, dict[str, Any]] = {}
    implementations: dict[int, tuple[dict[str, Any], dict[str, Any]]] = {}
    for family in projection["families"]:
        family_number = int(family["family_reference"]["family_id"].rsplit("-", 1)[1])
        families[family_number] = family["family_reference"]
        for implementation in family["implementations"]:
            number = int(implementation["implementation_id"].rsplit("-", 1)[1])
            implementations[number] = (family, implementation)
    return families, implementations


def _gap_ledger(
    projection: dict[str, Any], source_review: dict[str, Any]
) -> dict[str, Any]:
    counted_catalog = {51, 52, 54, 55, 59} | {item["source"] for item in CANDIDATES}
    all_implementations: list[dict[str, Any]] = []
    for family in projection["families"]:
        for implementation in family["implementations"]:
            all_implementations.append(
                {
                    "implementation_id": implementation["implementation_id"],
                    "family_id": family["family_reference"]["family_id"],
                    "display_name": implementation["display_name"],
                    "disposition": "backs-counted-direct-promotion" if int(implementation["implementation_id"].rsplit("-", 1)[1]) in counted_catalog else "not-in-bounded-palette",
                    "remaining_gaps": implementation["unresolved_facts"] or ["No Task 028 exact direct promotion was selected for this bounded palette."],
                }
            )
    remaining_review = []
    actually_selected = {
        entry["entry_id"]
        for entry in source_review["entries"]
        if entry["catalog_implementation_id"] in {
            "schuss-implementation-000057", "schuss-implementation-000058"
        }
    }
    if len(actually_selected) != 2:
        raise ValueError("Task 028 Task 027 provenance entries changed")
    # Use the exact discovered IDs rather than path spelling assumptions.
    remaining_review = [
        {
            "entry_id": entry["entry_id"], "disposition": entry["disposition"],
            "catalog_implementation_id": entry["catalog_implementation_id"], "gap": entry["disposition_rationale"],
        }
        for entry in source_review["entries"] if entry["entry_id"] not in actually_selected
    ]
    return {
        "schema_version": "task028-remaining-gaps-v1", "status": "complete",
        "catalog_implementation_count": len(all_implementations),
        "catalog_implementations_backing_counted_promotions": len(counted_catalog),
        "catalog_implementations_not_in_bounded_palette": len(all_implementations) - len(counted_catalog),
        "catalog_accounting": sorted(all_implementations, key=lambda item: item["implementation_id"]),
        "task027_source_review_count": len(source_review["entries"]),
        "task027_entries_selected_here": sorted(actually_selected),
        "task027_entries_remaining": len(remaining_review),
        "task027_remaining_accounting": sorted(remaining_review, key=lambda item: item["entry_id"]),
        "special_gates": [
            {"subject": "schuss-implementation-000056", "gate": "retained Rings reverb allocation contradiction and unsupported eligibility"},
            {"subject": "schuss-implementation-000094", "gate": "native allocation deliberately absent"},
            {"subject": "schuss-implementation-000096", "gate": "catalogued-only physical resonator lacks exact direct contract/binding/lowering evidence"},
            {"subject": "transparent-compounds", "gate": "deferred outside independently selectable primitive count"},
        ],
    }


def _exact(values: list[dict[str, Any]] | tuple[dict[str, Any], ...], field: str, identifier: str, revision: int) -> dict[str, Any]:
    matches = [item for item in values if item[field] == identifier and item["revision"] == revision]
    if len(matches) != 1:
        raise ValueError(f"Task 028 exact record did not resolve once: {identifier}@{revision}")
    return matches[0]


def generated() -> tuple[dict[str, bytes], bytes, dict[str, Any]]:
    parent_manifest = core.load_json(PARENT)
    if parent_manifest["record_set_id"] != "schuss-record-set-000020" or parent_manifest["revision"] != 1:
        raise ValueError("Task 028 exact Task 027 parent changed")
    parent_context = load_repository_context(record_set_path=PARENT)
    catalog = parent_context.records["catalog"][0]
    if catalog["schema_version"] != "catalog-corpus-v4" or catalog["revision"] != 4:
        raise ValueError("Task 028 parent does not select exact Task 027 catalog v4")
    projection = _projection(parent_context, parent_manifest)
    family_references, catalog_implementations = _projection_indexes(projection)
    observations = _observations()
    commits = _source_commits()
    schemas = _schemas()
    for name, schema in schemas.items():
        annotations = core.validate_schema_annotations(schema)
        if annotations:
            raise ValueError(f"Task 028 schema annotations invalid for {name}: {annotations}")

    for spec in CANDIDATES:
        family, implementation = catalog_implementations.get(spec["source"], (None, None))
        if family is None or implementation is None:
            raise ValueError(f"Task 028 source implementation absent from exact catalog projection: {spec['source']}")
        expected_family = f"schuss-family-{spec['family']:06d}"
        expected_observation = f"legacy-resolved-catalog-v0:object:{spec['variant']}"
        if family["family_reference"]["family_id"] != expected_family:
            raise ValueError(f"Task 028 source family mismatch: {spec['slug']}")
        if implementation["observation_references"] != [expected_observation]:
            raise ValueError(f"Task 028 source overload/observation mismatch: {spec['slug']}")
        if sorted(implementation.get("provenance_tags", [])) != sorted(spec.get("provenance", [])):
            raise ValueError(f"Task 028 source provenance mismatch: {spec['slug']}")

    contracts = _contracts(CANDIDATES, family_references, list(parent_context.records["contracts"]))
    source_identities = {
        spec["slug"]: _source_identity(spec, observations[spec["variant"]], commits)
        for spec in CANDIDATES
    }
    bindings = {
        spec["slug"]: _native_binding(spec, contracts[spec["slug"]], source_identities[spec["slug"]])
        for spec in CANDIDATES
    }
    operation_specs = {
        spec["slug"]: _operation_spec(
            spec, contracts[spec["slug"]], bindings[spec["slug"]],
            source_identities[spec["slug"]], schemas["direct-operation-spec-v3.schema.json"],
        )
        for spec in CANDIDATES
    }
    evidence_schema = core.load_json(ROOT / "schemas/evidence-claim-v0.schema.json")
    level2 = {
        spec["slug"]: _evidence_claim(
            spec, 2, bindings[spec["slug"]],
            [
                _semantic_ref(contracts[spec["slug"]], "component_contract_id"),
                _semantic_ref(bindings[spec["slug"]], "implementation_id"),
                _semantic_ref(operation_specs[spec["slug"]], "direct_operation_spec_id"),
            ],
            evidence_schema,
        )
        for spec in CANDIDATES
    }
    compute_target = _exact(parent_context.records["target"], "compute_target_id", TARGET_ID, 2)
    backend = _exact(parent_context.records["backend"], "backend_id", BACKEND_ID, 4)
    eligibilities = {
        spec["slug"]: _eligibility(
            spec, contracts[spec["slug"]], bindings[spec["slug"]], level2[spec["slug"]],
            compute_target, backend,
        )
        for spec in CANDIDATES
    }
    baseline_bindings = [
        _exact(parent_context.records["bindings"], "implementation_id", f"schuss-implementation-{number:06d}", 1)
        for number in BASELINE
    ]
    supporting_bindings = [
        _exact(parent_context.records["bindings"], "implementation_id", f"schuss-implementation-{number:06d}", 1)
        for number in range(42, 49)
    ]
    candidate_entries = []
    for index, spec in enumerate(CANDIDATES, start=1):
        source = source_identities[spec["slug"]]
        candidate_entries.append(
            {
                "candidate_id": f"task028-candidate-{index:06d}", "display_name": spec["name"],
                "functional_category": spec["category"],
                "family_reference": copy.deepcopy(contracts[spec["slug"]]["family_reference"]),
                "source_identity": copy.deepcopy(source),
                "contract_reference": _ref(contracts[spec["slug"]], "component_contract_id"),
                "native_binding_reference": _ref(bindings[spec["slug"]], "implementation_id"),
                "eligibility_reference": _ref(eligibilities[spec["slug"]], "binding_eligibility_id"),
                "operation_spec_reference": _ref(operation_specs[spec["slug"]], "direct_operation_spec_id"),
                "level2_evidence_reference": _ref(level2[spec["slug"]], "evidence_claim_id"),
                "requirements": sorted(spec["requirements"]), "exclusions": sorted(spec["exclusions"]),
                "evidence_gap": [
                    "Source artifact generation and ARM compilation/linking are not run.",
                    "Connected-device, realtime/resource, and audible behavior are not run.",
                    "The direct claim ends at exact independent selection and normalized operation IR.",
                ],
            }
        )
    packet = _packet(
        parent_manifest, catalog, compute_target, backend, baseline_bindings,
        supporting_bindings, candidate_entries,
        schemas["task028-selection-packet-v0.schema.json"],
    )
    capability_record = _exact(
        parent_context.records["capability"], "capability_vocabulary_id",
        backend["capability_vocabulary_reference"]["capability_vocabulary_id"],
        backend["capability_vocabulary_reference"]["revision"],
    )
    definitions = {item["key"]: item for item in capability_record["definitions"]}
    proof_raw = lower_palette(
        packet,
        operation_specs.values(),
        [*parent_context.records["contracts"], *[item for spec, item in ((s, contracts[s["slug"]]) for s in CANDIDATES) if spec["contract"] > 21]],
        [*parent_context.records["bindings"], *bindings.values()],
        [*parent_context.records["eligibility"], *eligibilities.values()],
        compute_target,
        backend,
        definitions,
    )
    proof = _record(proof_raw, schemas["palette-lowering-proof-v0.schema.json"])
    level3 = {
        spec["slug"]: _evidence_claim(
            spec, 3, bindings[spec["slug"]],
            [
                _semantic_ref(bindings[spec["slug"]], "implementation_id"),
                _semantic_ref(operation_specs[spec["slug"]], "direct_operation_spec_id"),
                _semantic_ref(proof, "palette_lowering_proof_id"),
            ],
            evidence_schema,
        )
        for spec in CANDIDATES
    }

    files: dict[str, bytes] = {
        f"schemas/{name}": _canonical_bytes(schema) for name, schema in schemas.items()
    }
    records: list[tuple[str, dict[str, Any], str, str]] = []
    for spec in CANDIDATES:
        slug = spec["slug"]
        if spec["contract"] > 21:
            path = f"contracts/task028/component-contract-{spec['contract']:06d}.json"
            records.append(("component-contract", contracts[slug], "component_contract_id", path))
        records.extend(
            [
                ("implementation-binding", bindings[slug], "implementation_id", f"contracts/task028/implementation-binding-{spec['native']:06d}.json"),
                ("direct-operation-spec", operation_specs[slug], "direct_operation_spec_id", f"contracts/task028/direct-operation-spec-{spec['operation']:06d}.json"),
                ("evidence", level2[slug], "evidence_claim_id", f"contracts/task028/evidence-claim-{spec['level2']:06d}.json"),
                ("eligibility", eligibilities[slug], "binding_eligibility_id", f"contracts/task028/binding-eligibility-{spec['eligibility']:06d}.json"),
                ("evidence", level3[slug], "evidence_claim_id", f"contracts/task028/evidence-claim-{spec['level3']:06d}.json"),
            ]
        )
    records.extend(
        [
            ("core-selection-packet", packet, "selection_packet_id", "contracts/task028/selection-packet.json"),
            ("palette-lowering-proof", proof, "palette_lowering_proof_id", "contracts/task028/palette-lowering-proof.json"),
        ]
    )
    for _, record, _, path in records:
        files[path] = _canonical_bytes(record)

    schema_members = copy.deepcopy(parent_manifest["schema_members"])
    prior_schema_versions = {item["schema_version"] for item in schema_members}
    for name in sorted(schemas):
        version = name.removesuffix(".schema.json")
        if version in prior_schema_versions:
            raise ValueError(f"Task 028 schema version collides with parent: {version}")
        path = f"schemas/{name}"
        schema_members.append({"schema_version": version, "portable_path": path, "byte_sha256": hashlib.sha256(files[path]).hexdigest()})

    record_members = copy.deepcopy(parent_manifest["record_members"])
    prior_id_revisions = {(item["stable_id"], item["revision"]) for item in record_members}
    for kind, record, field, path in records:
        key = (record[field], record["revision"])
        if key in prior_id_revisions:
            raise ValueError(f"Task 028 record allocation collides with parent: {key}")
        prior_id_revisions.add(key)
        record_members.append(
            {
                "record_kind": kind, "stable_id": record[field], "revision": record["revision"],
                "content_hash": record["content_hash"], "portable_path": path,
                "byte_sha256": hashlib.sha256(files[path]).hexdigest(),
            }
        )
    manifest_schema = core.load_json(ROOT / record_set_rules.RECORD_SET_SCHEMA)
    manifest = {
        "schema_version": "record-set-v0", "canonical_profile": "schuss-canonical-json-v1",
        "record_set_id": "schuss-record-set-000021", "revision": 1,
        "content_hash": "sha256:" + "0" * 64, "purpose": "prospective-task",
        "parent_reference": {"status": "included", **{key: parent_manifest[key] for key in ("record_set_id", "revision", "content_hash")}},
        "schema_members": sorted(schema_members, key=lambda item: (item["byte_sha256"], item["portable_path"])),
        "record_members": sorted(record_members, key=lambda item: (item["byte_sha256"], item["portable_path"])),
        "enforced_directories": sorted(set(parent_manifest["enforced_directories"]) | {"contracts/task028"}),
    }
    errors = core.schema_errors(manifest, manifest_schema, manifest_schema)
    if errors:
        raise ValueError("; ".join(errors))
    manifest["content_hash"] = core.record_content_hash(manifest, manifest_schema)

    gap_ledger = _gap_ledger(projection, parent_context.records["catalog_source_reviews"][0])
    balanced = {
        "schema_version": "task028-balanced-palette-summary-v1", "status": "complete",
        "counting_rule": packet["counting_rule"], "baseline_count": 5,
        "addition_count": 15, "final_safe_selectable_total": 20,
        "new_by_primary_function": {
            category: sum(item["category"] == category for item in CANDIDATES)
            for category in sorted({item["category"] for item in CANDIDATES})
        },
        "supporting_profile_binding_count_not_in_total": 7,
        "structurally_formable_examples": [
            "clocked percussion voices with envelopes, mixing, and output support",
            "saw, PWM, sine, or noise subtractive voices with filtering and VCA support",
            "ADSR, AD, decay, LFO, smoothing, latch, toggle, and sequenced modulation paths",
        ],
        "claim_boundary": "Structural and normalized local lowering only; no generated source, ARM, device, realtime/resource, or audible result.",
    }
    summary = {
        "schema_version": "task028-generation-summary-v1", "status": "valid",
        "record_set_reference": {key: manifest[key] for key in ("record_set_id", "revision", "content_hash")},
        "baseline_count": 5, "addition_count": len(CANDIDATES),
        "safe_selectable_total": 20, "independent_selection_count": proof["selection_count"],
        "level2_claim_count": len(level2), "level3_claim_count": len(level3),
        "evidence_levels": proof["evidence_levels"],
        "generated_record_count": len(records),
        "selection_packet_sha256": hashlib.sha256(files["contracts/task028/selection-packet.json"]).hexdigest(),
        "lowering_proof_sha256": hashlib.sha256(files["contracts/task028/palette-lowering-proof.json"]).hexdigest(),
        "source_artifact_generation_performed": False, "arm_compile_or_link_performed": False,
        "java_or_legacy_axp_performed": False, "device_or_hardware_performed": False,
        "realtime_or_audible_performed": False, "git_or_publication_performed": False,
    }
    files["evidence/task028-completion-v1/remaining-gaps.json"] = _canonical_bytes(gap_ledger)
    files["evidence/task028-completion-v1/balanced-palette-summary.json"] = _canonical_bytes(balanced)
    files["evidence/task028-completion-v1/validation-summary.json"] = _canonical_bytes(summary)
    return files, _canonical_bytes(manifest), summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        files, manifest, summary = generated()
        expected = {**files, OUTPUT.relative_to(ROOT).as_posix(): manifest}
        stale = [path for path, payload in expected.items() if not (ROOT / path).is_file() or (ROOT / path).read_bytes() != payload]
        if args.check and stale:
            raise ValueError("Task 028 generated outputs are stale: " + ", ".join(sorted(stale)))
        if not args.check:
            for relative, payload in expected.items():
                path = ROOT / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
    except (OSError, ValueError, KeyError, StopIteration, json.JSONDecodeError) as exc:
        print("Task 028 generation failed: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
