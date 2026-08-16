#!/usr/bin/env python3
"""Generate the exact Task 017 curated-core records and successor set."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/contracts")]

import record_set_rules  # noqa: E402
import validator_core as core  # noqa: E402


PARENT = ROOT / "contracts/record-sets/task016-complete-gills-direct-v1.json"
OUTPUT = ROOT / "contracts/record-sets/task017-curated-core-v1.json"
RECORD_ROOT = ROOT / "contracts/task017"
OBSERVATIONS_PATH = ROOT / "catalog/snapshots/legacy-resolved-catalog-v0/resolved/objects.jsonl"
GRAPHS_PATH = ROOT / "catalog/snapshots/legacy-resolved-catalog-v0/resolved/graphs.jsonl"
MANIFEST_SHA256 = "0e3f3cb763f634ce490195e2cd4665c2e1a41764cd54c6526e6e219f18e1e959"

TARGET_REFERENCE = {
    "compute_target_id": "schuss-compute-target-000001",
    "revision": 2,
    "content_hash": "sha256:d8a9652bd079d0f2a8806cc4922f2a380c8092549f267047d5a4a0360b4a6753",
}
DEVICE_REFERENCE = {
    "device_profile_id": "schuss-device-profile-000001",
    "revision": 1,
    "content_hash": "sha256:d6ad487f5444b1e39667ed8b4e43dde32ce7f06accac0be4fd5930c9b7eb82fe",
}


FAMILIES: tuple[dict[str, Any], ...] = (
    {
        "slug": "logic-toggle", "family": 29, "implementation": 49, "contract": 10,
        "variant": 229, "name": "Clocked Logic Toggle", "aliases": ["Trigger Toggle"],
        "category": "timing-sequencing", "tags": ["state", "clock-division"],
        "description": "Toggles a Boolean state on each rising clock edge.",
        "rationale": "A high-use, compact state primitive needed by sequencers and reusable compounds.",
        "semantics": ["initial output and trigger history are zero", "each rising trigger edge inverts the output", "a low trigger rearms edge detection"],
    },
    {
        "slug": "pseudo-euclidean", "family": 30, "implementation": 50, "contract": 11,
        "variant": 1208, "name": "Pseudo-Euclidean Gate Sequencer", "aliases": ["Euclidean Gate"],
        "category": "timing-sequencing", "tags": ["algorithmic-sequencing", "randomized-pattern"],
        "description": "Advances a bounded pseudo-Euclidean gate pattern from an incoming clock.",
        "rationale": "Adds a richer stateful sequencer even though raw frequency alone would rank it below interface utilities.",
        "semantics": ["active gates evaluation", "rising trigger advances the retained tx/ty recurrence", "reset clears recurrence and gate state", "pattern renewal calls the retained runtime random generator"],
    },
    {
        "slug": "saw-oscillator", "family": 31, "implementation": 51, "contract": 12,
        "variant": 547, "name": "Band-limited Saw Oscillator", "aliases": ["BLEP Saw"],
        "category": "sound-sources", "tags": ["oscillator", "pitched-voice"],
        "description": "Generates a band-limited sawtooth audio stream from pitch control.",
        "rationale": "Provides a common subtractive voice distinct from the accepted Sine family.",
        "semantics": ["pitch parameter and inlet sum at control rate", "retained BLEP voices and phase are instance state", "audio output is Q27"],
    },
    {
        "slug": "pwm-oscillator", "family": 32, "implementation": 52, "contract": 13,
        "variant": 543, "name": "Band-limited PWM Oscillator", "aliases": ["Pulse-width Oscillator"],
        "category": "sound-sources", "tags": ["oscillator", "pulse-width-modulation"],
        "description": "Generates a band-limited pulse audio stream with pitch and pulse-width control.",
        "rationale": "Adds a modulation-oriented oscillator with a public width inlet rather than another fixed waveform.",
        "semantics": ["pitch parameter and inlet sum at control rate", "zero pulse-width input means fifty-percent duty", "retained BLEP, phase, and pulse-width values are instance state"],
    },
    {
        "slug": "attack-decay", "family": 33, "implementation": 53, "contract": 14,
        "variant": 113, "name": "Attack-Decay Envelope", "aliases": ["AD Envelope"],
        "category": "modulation-control", "tags": ["envelope", "transient-modulation"],
        "description": "Produces a linear-attack, exponential-decay control envelope from rising triggers.",
        "rationale": "Adds a compact transient modulator for percussion and voice compounds.",
        "semantics": ["rising trigger starts attack", "attack saturates to full scale then enters decay", "decay uses the retained fixed-point multiplier", "legacy time transfer functions remain unresolved for direct lowering"],
    },
    {
        "slug": "exponential-smoother", "family": 34, "implementation": 54, "contract": 15,
        "variant": 362, "name": "Exponential Control Smoother", "aliases": ["Control Slew"],
        "category": "modulation-control", "tags": ["smoothing", "slew"],
        "description": "Smooths a control stream with a stateful exponential response.",
        "rationale": "Makes public parameter motion reusable inside graphs without assigning smoothing to a UI client.",
        "semantics": ["state initializes to zero", "one control-rate update applies retained ___SMMLA arithmetic", "legacy time transfer function remains unresolved for direct lowering"],
    },
    {
        "slug": "audio-soft-clip", "family": 35, "implementation": 55, "contract": 16,
        "variant": 109, "name": "Audio Soft Clipper", "aliases": ["Cubic Soft Saturation"],
        "category": "shaping-dynamics", "tags": ["distortion", "waveshaping"],
        "description": "Applies the reviewed audio-rate cubic soft-saturation variant.",
        "rationale": "Selects exact overload variant 109, keeping the distinct control-rate sibling visible rather than merging by name.",
        "semantics": ["input saturates to signed 28 bits", "inside the retained domain output uses 1.5*x minus 0.5*x cubed", "no oversampling or anti-aliasing is claimed"],
    },
    {
        "slug": "rings-reverb", "family": 36, "implementation": 56, "contract": 17,
        "variant": 174, "name": "Rings-derived Stereo Reverb", "aliases": ["Rings Reverb"],
        "category": "delay-reverb", "tags": ["stereo-effect", "reverberation"],
        "description": "Processes stereo audio through the retained Rings-derived reverb implementation.",
        "rationale": "Adds one richer effect with explicit GPL source declaration, include dependency, and SDRAM requirement.",
        "semantics": ["five normalized runtime parameters drive the retained reverb object", "initialization requests 32768 bytes from the SDRAM allocator", "Q27 audio converts through retained float helpers"],
    },
    {
        "slug": "struck-drum", "family": 37, "implementation": 57, "contract": 18,
        "variant": 527, "name": "Struck Drum Voice", "aliases": ["Braids Struck Drum"],
        "category": "sound-sources", "tags": ["percussion", "physical-modeling"],
        "description": "Generates a struck-drum audio voice with pitch, timbre, color, and strike control.",
        "rationale": "Provides an explicit percussion voice rather than treating provenance or generic oscillator ancestry as its function.",
        "semantics": ["pitch, timbre, and color combine parameters with inlets", "strike is rising-edge detected", "the retained Braids-derived state renders one 16-sample block"],
    },
    {
        "slug": "struck-bell", "family": 38, "implementation": 58, "contract": 19,
        "variant": 526, "name": "Struck Bell Voice", "aliases": ["Braids Struck Bell"],
        "category": "sound-sources", "tags": ["percussion", "feedback-fm"],
        "description": "Generates a struck-bell audio voice with pitch, timbre, color, and strike control.",
        "rationale": "Balances drum percussion with a metallic voice that shares a reusable public shape but remains a distinct family.",
        "semantics": ["pitch, timbre, and color combine parameters with inlets", "strike is rising-edge detected", "the retained feedback-FM state renders one 16-sample block"],
    },
    {
        "slug": "vca", "family": 39, "implementation": 59, "contract": 20,
        "variant": 178, "name": "Interpolated Audio VCA", "aliases": ["Voltage-controlled Amplifier"],
        "category": "shaping-dynamics", "tags": ["amplitude-modulation", "gain"],
        "description": "Applies a control-rate gain to audio with retained block interpolation.",
        "rationale": "The strongest non-interface usage signal in the batch and a reusable bridge between modulators and voices.",
        "semantics": ["previous gain is retained per instance", "one control-cycle step interpolates across 16 audio samples", "audio multiplication uses retained ___SMMUL arithmetic"],
    },
    {
        "slug": "dual-percussion-compound", "family": 40, "implementation": 60, "contract": 21,
        "variant": None, "name": "Dual Percussion Voice", "aliases": ["Euclidean Drum and Bell"],
        "category": "sound-sources", "tags": ["percussion", "transparent-compound", "reusable-voice"],
        "description": "An inspectable clocked compound combining sequencer, envelope, drum, bell, crossfade, and VCA components.",
        "rationale": "A Schuss-authored transparent compound proves reuse and hierarchy without hiding an opaque legacy subpatch.",
        "semantics": ["clock input remains externally visible", "all internal nodes and connections remain inspectable", "state remains owned by internal component instances"],
    },
)


EXPECTED_USAGE = {229: 83, 1208: 9, 547: 42, 543: 23, 113: 67, 362: 22, 109: 28, 174: 18, 527: 12, 526: 8, 178: 311}
EXCLUDED = (
    (663, 934, "string/c", "Message/string construction is a service utility, not a balanced musical-core priority."),
    (180, 349, "gpio/in/analog", "Physical GPIO evidence and the complete Gills control census are outside Task 017."),
    (77, 332, "disp/bool", "Display/UI work is outside Task 017."),
    (85, 200, "disp/i", "Display/UI work is outside Task 017."),
    (28, 197, "ctrl/dial p", "Legacy editor-control objects are not headless graph controls."),
    (183, 192, "gpio/in/digital", "Physical GPIO evidence is outside Task 017."),
    (382, 176, "midi/in/keyb note", "External MIDI behavior would consume the bounded batch without improving the requested category balance."),
    (269, 145, "math/*c", "The overloaded control/audio variants require a separate exact family split before promotion."),
)


def _record(value: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(value)
    result["content_hash"] = "sha256:" + "0" * 64
    errors = core.schema_errors(result, schema, schema)
    if errors:
        raise ValueError("; ".join(errors))
    result["content_hash"] = core.record_content_hash(result, schema)
    return result


def _child(value: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(value)
    result["content_hash"] = "sha256:" + hashlib.sha256(
        core.canonical_json({key: item for key, item in result.items() if key != "content_hash"}).encode("utf-8")
    ).hexdigest()
    return result


def _ref(record: dict[str, Any], field: str) -> dict[str, Any]:
    return {field: record[field], "revision": record["revision"], "content_hash": record["content_hash"]}


def _semantic_ref(record: dict[str, Any], field: str) -> dict[str, Any]:
    return {"input_kind": "semantic-record", "stable_id": record[field], "revision": record["revision"], "content_hash": record["content_hash"]}


def _schema_files() -> dict[str, dict[str, Any]]:
    binding = copy.deepcopy(core.load_json(ROOT / "schemas/implementation-binding-v1.schema.json"))
    binding["$id"] = "implementation-binding-v2.schema.json"
    binding["title"] = "Schuss implementation binding v2"
    binding["properties"]["schema_version"] = {"const": "implementation-binding-v2"}
    binding["$defs"]["legacyObservation"]["required"].remove("legacy_uuid")
    binding["$defs"]["legacyObservation"]["required"].append("legacy_uuid_sha256")
    del binding["$defs"]["legacyObservation"]["properties"]["legacy_uuid"]
    binding["$defs"]["legacyObservation"]["properties"]["legacy_uuid_sha256"] = {
        "type": "string", "pattern": "^sha256:[0-9a-f]{64}$"
    }

    catalog = copy.deepcopy(core.load_json(ROOT / "schemas/catalog-corpus-v1.schema.json"))
    catalog["$id"] = "catalog-corpus-v2.schema.json"
    catalog["title"] = "Schuss exact reviewed catalog corpus v2"
    catalog["required"].append("parent_corpus_reference")
    catalog["properties"]["schema_version"] = {"const": "catalog-corpus-v2"}
    catalog["properties"]["revision"] = {"const": 2}
    catalog["properties"]["projection_version"] = {"const": "schuss-catalog-projection-v2"}
    catalog["properties"]["parent_corpus_reference"] = {"$ref": "#/$defs/catalogReference"}
    catalog["properties"]["family_additions"]["minItems"] = 14
    catalog["properties"]["family_additions"]["maxItems"] = 14
    catalog["properties"]["implementation_additions"]["minItems"] = 15
    catalog["properties"]["implementation_additions"]["maxItems"] = 15
    catalog["$defs"]["catalogReference"] = {
        "type": "object", "additionalProperties": False,
        "required": ["catalog_id", "revision", "content_hash"],
        "properties": {
            "catalog_id": {"const": "schuss-catalog-000001"},
            "revision": {"const": 1},
            "content_hash": {"$ref": "#/$defs/contentHash"},
        },
    }
    catalog["$defs"]["sourceAuthority"] = {
        "oneOf": [
            {
                "type": "object", "additionalProperties": False,
                "required": ["kind", "observation"],
                "properties": {"kind": {"const": "legacy-observation"}, "observation": {"$ref": "#/$defs/observationSourceV2"}},
            },
            {
                "type": "object", "additionalProperties": False,
                "required": ["kind", "evidence_ref"],
                "properties": {
                    "kind": {"const": "schuss-transparent-compound"},
                    "evidence_ref": {"type": "string", "pattern": "^fixture:[a-z][a-z0-9-]*$"},
                },
            },
        ]
    }
    catalog["$defs"]["observationSourceV2"] = copy.deepcopy(catalog["$defs"]["observationSource"])
    catalog["$defs"]["observationSourceV2"]["required"].remove("legacy_uuid")
    catalog["$defs"]["observationSourceV2"]["required"].append("legacy_uuid_sha256")
    del catalog["$defs"]["observationSourceV2"]["properties"]["legacy_uuid"]
    catalog["$defs"]["observationSourceV2"]["properties"]["legacy_uuid_sha256"] = {
        "type": "string", "pattern": "^sha256:[0-9a-f]{64}$"
    }
    for definition_name in ("familyAddition", "implementationAddition"):
        definition = catalog["$defs"][definition_name]
        definition["properties"]["source_authority"] = {"$ref": "#/$defs/sourceAuthority"}
        definition["allOf"] = [{"oneOf": [
            {"required": ["source_observation"], "not": {"required": ["source_authority"]}},
            {"required": ["source_authority"], "not": {"required": ["source_observation"]}},
        ]}]
        definition["required"].remove("source_observation")
    catalog["$defs"]["familyAddition"]["properties"]["primary_category"] = {
        "enum": ["input-output", "sound-sources", "sampling-buffers", "modulation-control", "filters-resonators", "shaping-dynamics", "delay-reverb", "spectral-analysis", "mixing-routing", "pitch-notes", "timing-sequencing", "data-math-logic", "interface-system"]
    }
    catalog["$defs"]["familyAddition"]["properties"]["abstraction_level"] = {"enum": ["primitive", "compound"]}
    catalog["$defs"]["familyAddition"]["properties"]["review_status"] = {"enum": ["slice-reviewed", "task017-reviewed"]}
    catalog["$defs"]["implementationAddition"]["properties"]["form"]["enum"].append("transparent-compound")
    catalog["$defs"]["implementationAddition"]["properties"]["review_status"] = {"enum": ["slice-reviewed", "task017-reviewed"]}
    catalog["$defs"]["batchReview"] = {
        "type": "object", "additionalProperties": False,
        "required": ["review_id", "batch_limit", "selected_family_count", "balanced_categories", "direct_support_policy"],
        "properties": {
            "review_id": {"const": "schuss-core-review-000001"},
            "batch_limit": {"const": 12},
            "selected_family_count": {"const": 12},
            "balanced_categories": {"type": "array", "x-schuss-array-kind": "set", "uniqueItems": True, "minItems": 5, "items": {"type": "string", "minLength": 1}},
            "direct_support_policy": {"const": "exact-support-or-deterministic-unsupported-no-fallback"},
        },
    }
    catalog["properties"]["slice_review"] = {"$ref": "#/$defs/batchReview"}

    selector = {
        "$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "catalog-selection-v0.schema.json",
        "title": "Schuss exact catalog corpus selection v0", "type": "object", "additionalProperties": False,
        "required": ["schema_version", "canonical_profile", "catalog_selection_id", "revision", "content_hash", "corpus_reference", "rationale"],
        "properties": {
            "schema_version": {"const": "catalog-selection-v0"}, "canonical_profile": {"const": "schuss-canonical-json-v1"},
            "catalog_selection_id": {"type": "string", "pattern": "^schuss-catalog-selection-[0-9]{6}$"}, "revision": {"type": "integer", "minimum": 1},
            "content_hash": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
            "corpus_reference": {"type": "object", "additionalProperties": False, "required": ["catalog_id", "revision", "content_hash"], "properties": {"catalog_id": {"const": "schuss-catalog-000001"}, "revision": {"type": "integer", "minimum": 1}, "content_hash": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"}}},
            "rationale": {"type": "string", "minLength": 1},
        },
    }
    packet = _selection_packet_schema()
    projection = copy.deepcopy(core.load_json(ROOT / "schemas/catalog-projection-v1.schema.json"))
    projection["$id"] = "catalog-projection-v2.schema.json"
    projection["title"] = "Schuss derived catalog projection v2"
    projection["properties"]["schema_version"] = {"const": "catalog-projection-v2"}
    projection["properties"]["projection_version"] = {"const": "schuss-catalog-projection-v2"}
    projection["properties"]["families"]["minItems"] = 40
    projection["$defs"]["catalogReference"]["properties"]["revision"] = {"const": 2}
    return {"implementation-binding-v2.schema.json": binding, "catalog-corpus-v2.schema.json": catalog, "catalog-projection-v2.schema.json": projection, "catalog-selection-v0.schema.json": selector, "core-selection-packet-v0.schema.json": packet}


def _selection_packet_schema() -> dict[str, Any]:
    content = {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"}
    exact_ref = {
        "type": "object", "additionalProperties": False,
        "required": ["stable_id", "revision", "content_hash"],
        "properties": {"stable_id": {"type": "string", "pattern": "^schuss-[a-z0-9-]+-[0-9]{6}$"}, "revision": {"type": "integer", "minimum": 1}, "content_hash": content},
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "core-selection-packet-v0.schema.json",
        "title": "Schuss curated-core selection packet v0", "type": "object", "additionalProperties": False,
        "required": ["schema_version", "canonical_profile", "selection_packet_id", "revision", "content_hash", "accepted_parent_reference", "inventory_audit", "criteria", "included_families", "excluded_candidates", "reference_instruments", "evidence_boundaries"],
        "properties": {
            "schema_version": {"const": "core-selection-packet-v0"}, "canonical_profile": {"const": "schuss-canonical-json-v1"},
            "selection_packet_id": {"type": "string", "pattern": "^schuss-core-selection-[0-9]{6}$"}, "revision": {"type": "integer", "minimum": 1}, "content_hash": content,
            "accepted_parent_reference": {"$ref": "#/$defs/exactReference"},
            "inventory_audit": {"type": "object", "additionalProperties": False, "required": ["complete_graphs", "resolved_observations", "reviewed_families", "top_200_coverage", "frequency_policy"], "properties": {"complete_graphs": {"const": 348}, "resolved_observations": {"const": 3602}, "reviewed_families": {"const": 28}, "top_200_coverage": {"const": "84.15%"}, "frequency_policy": {"const": "prioritization-only"}}},
            "criteria": {"type": "array", "x-schuss-array-kind": "sequence", "minItems": 5, "items": {"type": "string", "minLength": 1}},
            "included_families": {"type": "array", "x-schuss-array-kind": "sequence", "minItems": 12, "maxItems": 12, "items": {"$ref": "#/$defs/included"}},
            "excluded_candidates": {"type": "array", "x-schuss-array-kind": "sequence", "minItems": 1, "items": {"$ref": "#/$defs/excluded"}},
            "reference_instruments": {"type": "array", "x-schuss-array-kind": "sequence", "minItems": 2, "maxItems": 2, "items": {"$ref": "#/$defs/referenceInstrument"}},
            "evidence_boundaries": {"type": "array", "x-schuss-array-kind": "sequence", "minItems": 8, "maxItems": 8, "items": {"$ref": "#/$defs/evidenceBoundary"}},
        },
        "$defs": {
            "exactReference": exact_ref,
            "included": {"type": "object", "additionalProperties": False, "required": ["family_reference", "implementation_reference", "primary_category", "complete_graph_reference_count", "selection_rationale", "semantic_summary", "license_observation", "compatibility_status", "direct_backend_status", "unresolved_facts"], "properties": {"family_reference": {"$ref": "#/$defs/exactReference"}, "implementation_reference": {"$ref": "#/$defs/exactReference"}, "primary_category": {"type": "string", "minLength": 1}, "complete_graph_reference_count": {"type": "integer", "minimum": 0}, "selection_rationale": {"type": "string", "minLength": 1}, "semantic_summary": {"type": "array", "x-schuss-array-kind": "sequence", "minItems": 1, "items": {"type": "string", "minLength": 1}}, "license_observation": {"enum": ["BSD", "GPL", "not-declared"]}, "compatibility_status": {"enum": ["structural-source-and-seam-reviewed", "transparent-compound-structural"]}, "direct_backend_status": {"enum": ["unsupported", "transparent-wrapper-supported-internals-unsupported"]}, "unresolved_facts": {"type": "array", "x-schuss-array-kind": "set", "uniqueItems": True, "minItems": 1, "items": {"type": "string", "minLength": 1}}}},
            "excluded": {"type": "object", "additionalProperties": False, "required": ["variant_index", "legacy_id", "complete_graph_reference_count", "rationale"], "properties": {"variant_index": {"type": "integer", "minimum": 0}, "legacy_id": {"type": "string", "minLength": 1}, "complete_graph_reference_count": {"type": "integer", "minimum": 0}, "rationale": {"type": "string", "minLength": 1}}},
            "referenceInstrument": {"type": "object", "additionalProperties": False, "required": ["instrument_reference", "graph_reference", "build_request_reference", "concept", "expected_plan_status"], "properties": {"instrument_reference": {"$ref": "#/$defs/exactReference"}, "graph_reference": {"$ref": "#/$defs/exactReference"}, "build_request_reference": {"$ref": "#/$defs/exactReference"}, "concept": {"type": "string", "minLength": 1}, "expected_plan_status": {"enum": ["invalid", "unsupported", "unresolved"]}}},
            "evidenceBoundary": {"type": "object", "additionalProperties": False, "required": ["level", "name", "status"], "properties": {"level": {"type": "integer", "minimum": 1, "maximum": 8}, "name": {"type": "string", "minLength": 1}, "status": {"enum": ["passed", "not-run"]}}},
        },
    }


def _observations() -> dict[int, dict[str, Any]]:
    return {value["variant_index"]: value for value in core.load_jsonl(OBSERVATIONS_PATH)}


def _usage_counts() -> Counter[int]:
    counts: Counter[int] = Counter()
    for graph in core.load_jsonl(GRAPHS_PATH):
        if graph["export_status"] != "complete":
            continue
        for instance in graph["instances"]:
            selected = instance.get("resolution", {}).get("legacy_selected")
            if isinstance(selected, dict) and selected.get("kind") == "catalog":
                counts[selected["variant_index"]] += 1
    return counts


def _source(observation: dict[str, Any]) -> dict[str, Any]:
    origin = observation["origin"]
    return {
        "evidence_ref": f"legacy-resolved-catalog-v0:object:{observation['variant_index']}",
        "canonical_observation_sha256": hashlib.sha256(core.canonical_json(observation).encode("utf-8")).hexdigest(),
        "source_id": origin["source_id"], "source_path": origin["path"], "source_sha256": origin["sha256"],
        "legacy_id": observation["legacy_id"],
        "legacy_uuid_sha256": "sha256:" + hashlib.sha256(observation["uuid"]["durable_value"].encode("utf-8")).hexdigest(),
    }


def _catalog(parent_corpus: dict[str, Any], observations: dict[int, dict[str, Any]], schema: dict[str, Any]) -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    corpus = copy.deepcopy(parent_corpus)
    corpus["schema_version"] = "catalog-corpus-v2"
    corpus["revision"] = 2
    corpus["projection_version"] = "schuss-catalog-projection-v2"
    corpus["parent_corpus_reference"] = _ref(parent_corpus, "catalog_id")
    families = {str(value["family_id"]): value for value in corpus["family_additions"]}
    implementations = {str(value["implementation_id"]): value for value in corpus["implementation_additions"]}
    for spec in FAMILIES:
        family_id = f"schuss-family-{spec['family']:06d}"
        implementation_id = f"schuss-implementation-{spec['implementation']:06d}"
        if spec["variant"] is None:
            authority = {"kind": "schuss-transparent-compound", "evidence_ref": "fixture:task017-dual-percussion"}
            form = "transparent-compound"
            confidence = "high"
        else:
            observation = observations[spec["variant"]]
            authority = {"kind": "legacy-observation", "observation": _source(observation)}
            form = "generated-object" if observation["origin"].get("generated_by") else "native-object"
            confidence = "high"
        family = _child({
            "family_id": family_id, "revision": 1, "content_hash": "sha256:" + "0" * 64,
            "display_name": spec["name"], "aliases": spec["aliases"], "description": spec["description"],
            "primary_category": spec["category"], "secondary_function_tags": spec["tags"],
            "abstraction_level": "compound" if spec["variant"] is None else "primitive",
            "review_status": "task017-reviewed", "classification_confidence": confidence,
            "classification_rationale": spec["rationale"], "source_authority": authority,
            "unresolved_questions": ["Direct Task 016 compatibility is not implied; exact unsupported diagnostics are retained until a separate direct semantic specification exists."],
        })
        implementation = _child({
            "implementation_id": implementation_id, "revision": 1, "content_hash": "sha256:" + "0" * 64,
            "family_reference": _ref(family, "family_id"), "display_name": spec["name"] + " implementation",
            "form": form, "source_authority": copy.deepcopy(authority), "review_status": "task017-reviewed",
            "membership_confidence": confidence, "membership_rationale": spec["rationale"],
            "compatibility_status": "not-evaluated",
            "unresolved_questions": ["Native direct DSP/runtime behavior and resource closure are not established by catalog membership."],
        })
        families[family_id] = family
        implementations[implementation_id] = implementation
    corpus["family_additions"] = list(families.values())
    corpus["implementation_additions"] = list(implementations.values())
    corpus["slice_review"] = {
        "review_id": "schuss-core-review-000001", "batch_limit": 12, "selected_family_count": 12,
        "balanced_categories": ["timing-sequencing", "sound-sources", "modulation-control", "shaping-dynamics", "delay-reverb", "percussion"],
        "direct_support_policy": "exact-support-or-deterministic-unsupported-no-fallback",
    }
    corpus = _record(corpus, schema)
    return corpus, {key: value for key, value in families.items() if int(key.rsplit("-", 1)[1]) >= 29}, {key: value for key, value in implementations.items() if int(key.rsplit("-", 1)[1]) >= 49}


def _type_templates() -> dict[str, dict[str, Any]]:
    lfo = core.load_json(ROOT / "contracts/task011b/component-contracts/lfo.json")
    sine = core.load_json(ROOT / "contracts/task011b/component-contracts/sine.json")
    mixed = core.load_json(ROOT / "contracts/component-contracts/crossfader-mixed-v0.json")
    control = core.load_json(ROOT / "contracts/component-contracts/crossfader-control-v0.json")
    return {
        "clock": copy.deepcopy(lfo["ports"][2]["port_type"]),
        "pitch": copy.deepcopy(next(port for port in sine["ports"] if port["semantic_key"] == "pitch")["port_type"]),
        "audio": copy.deepcopy(mixed["ports"][0]["port_type"]),
        "control": copy.deepcopy(control["ports"][0]["port_type"]),
        "positive": copy.deepcopy(mixed["ports"][2]["port_type"]),
    }


def _port_type(kind: str, *, direction: str, required: bool, role: str | None = None) -> dict[str, Any]:
    value = copy.deepcopy(_TYPE_TEMPLATES[kind])
    value["cardinality"] = {"minimum_connections": 1 if required else 0, "maximum_connections": 1 if direction == "inlet" else "unbounded"}
    value["optionality"] = ({"status": "required", "absence_behavior": "invalid"} if required else ({"status": "optional", "absence_behavior": "use-default", "default_value": "0"} if direction == "inlet" else {"status": "not-applicable"}))
    if role is not None:
        value["semantic_role"] = role
    return value


def _port(index: int, key: str, label: str, direction: str, kind: str, required: bool, role: str | None = None) -> dict[str, Any]:
    return {"facet_id": f"component-port-{index:06d}", "semantic_key": key, "display_label": label, "direction": direction, "port_type": _port_type(kind, direction=direction, required=required, role=role)}


def _parameter(index: int, key: str, label: str, kind: str, default: str) -> dict[str, Any]:
    if kind == "pitch":
        template = core.load_json(ROOT / "contracts/task011b/component-contracts/sine.json")["parameters"][0]
        result = copy.deepcopy(template)
        result.update({"facet_id": f"component-parameter-{index:06d}", "semantic_key": key, "display_label": label, "default": default})
        return result
    if kind == "positive":
        port_type = _TYPE_TEMPLATES["positive"]
        return {"facet_id": f"component-parameter-{index:06d}", "semantic_key": key, "display_label": label, "representation": copy.deepcopy(port_type["representation"]), "unit": "normalized", "domain": copy.deepcopy(port_type["valid_range"]), "default": default, "update_behavior": {"update_kind": "runtime", "stateful": True}}
    return {"facet_id": f"component-parameter-{index:06d}", "semantic_key": key, "display_label": label, "representation": copy.deepcopy(_TYPE_TEMPLATES["control"]["representation"]), "unit": "unitless", "domain": {"status": "unresolved", "code": "LEGACY_PARAMETER_TRANSFER_UNRESOLVED", "owner": "task-017", "rationale": "The frozen legacy parameter class is exact but its target-independent transfer domain is not promoted.", "question": "What exact target-independent authoring domain preserves this legacy time mapping?", "evidence_refs": []}, "default": default, "update_behavior": {"update_kind": "runtime", "stateful": True}}


def _state(index: int, key: str, kind: str = "integer") -> dict[str, Any]:
    return {"state_id": f"component-state-{index:06d}", "semantic_key": key, "value_kind": kind, "ownership": "component-instance", "persistence": "volatile", "reset_policy": "default-on-start"}


def _contract_shape(slug: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    ports: list[dict[str, Any]] = []
    parameters: list[dict[str, Any]] = []
    attributes: list[dict[str, Any]] = []
    displays: list[dict[str, Any]] = []
    states: list[dict[str, Any]] = []
    behavior: list[dict[str, Any]] = []
    compound = {"kind": "primitive", "mapping_keys": []}
    if slug == "logic-toggle":
        ports = [_port(1, "trigger", "Trigger", "inlet", "clock", True, "clock"), _port(2, "output", "Output", "outlet", "clock", False, "clock")]
        states = [_state(1, "trigger-history", "boolean"), _state(2, "latched-output", "boolean")]
    elif slug == "pseudo-euclidean":
        ports = [_port(1, "active", "Active", "inlet", "clock", False, "gate"), _port(2, "trigger", "Trigger", "inlet", "clock", True, "clock"), _port(3, "reset", "Reset", "inlet", "clock", False, "trigger"), _port(4, "wave", "Wave", "outlet", "positive", False, "crossfade-position"), _port(5, "gate", "Gate", "outlet", "clock", False, "clock")]
        attributes = [{"facet_id": "component-attribute-000001", "semantic_key": "steps", "display_label": "Steps", "value_kind": "integer", "default": "3"}, {"facet_id": "component-attribute-000002", "semantic_key": "hits", "display_label": "Hits", "value_kind": "integer", "default": "8"}]
        displays = [{"facet_id": "component-display-000001", "semantic_key": "bit", "display_label": "Bit", "value_kind": "integer", "access": "read-only"}]
        states = [_state(1, "recurrence", "structured"), _state(2, "trigger-history", "boolean"), _state(3, "reset-history", "boolean")]
    elif slug in {"saw-oscillator", "pwm-oscillator"}:
        ports = [_port(1, "pitch", "Pitch", "inlet", "pitch", False, "modulation")]
        if slug == "pwm-oscillator":
            ports.append(_port(2, "pulse-width", "Pulse Width", "inlet", "control", False, "modulation"))
        ports.append(_port(len(ports) + 1, "wave", "Wave", "outlet", "audio", False, "audio"))
        parameters = [_parameter(1, "base-pitch", "Pitch", "pitch", "-24")]
        states = [_state(1, "phase"), _state(2, "blep-voices", "structured")]
        if slug == "pwm-oscillator": states.append(_state(3, "pulse-width"))
        behavior = copy.deepcopy(core.load_json(ROOT / "contracts/task011b/component-contracts/sine.json")["behavior_rules"])
    elif slug == "attack-decay":
        ports = [_port(1, "trigger", "Trigger", "inlet", "clock", True, "clock"), _port(2, "envelope", "Envelope", "outlet", "positive", False, "modulation")]
        parameters = [_parameter(1, "attack", "Attack", "time", "0"), _parameter(2, "decay", "Decay", "time", "0")]
        states = [_state(1, "stage"), _state(2, "trigger-history", "boolean"), _state(3, "envelope-value")]
    elif slug == "exponential-smoother":
        ports = [_port(1, "input", "Input", "inlet", "positive", True, "modulation"), _port(2, "output", "Output", "outlet", "positive", False, "modulation")]
        parameters = [_parameter(1, "time", "Time", "time", "0")]
        states = [_state(1, "smoothed-value")]
    elif slug == "audio-soft-clip":
        ports = [_port(1, "input", "Input", "inlet", "audio", True, "audio"), _port(2, "output", "Output", "outlet", "audio", False, "audio")]
    elif slug == "rings-reverb":
        ports = [_port(1, "left-input", "Left Input", "inlet", "audio", True, "audio"), _port(2, "right-input", "Right Input", "inlet", "audio", True, "audio"), _port(3, "left-output", "Left Output", "outlet", "audio", False, "audio"), _port(4, "right-output", "Right Output", "outlet", "audio", False, "audio")]
        parameters = [_parameter(i, key, label, "positive", "0.5") for i, (key, label) in enumerate((("amount", "Amount"), ("time", "Time"), ("diffusion", "Diffusion"), ("gain", "Gain"), ("lowpass", "Lowpass")), 1)]
        states = [_state(1, "reverb-state", "structured"), _state(2, "sdram-buffer", "bytes")]
    elif slug in {"struck-drum", "struck-bell"}:
        ports = [_port(1, "pitch", "Pitch", "inlet", "pitch", False, "modulation"), _port(2, "timbre", "Timbre", "inlet", "positive", False, "modulation"), _port(3, "color", "Color", "inlet", "positive", False, "modulation"), _port(4, "strike", "Strike", "inlet", "clock", True, "clock"), _port(5, "wave", "Wave", "outlet", "audio", False, "audio")]
        parameters = [_parameter(1, "base-pitch", "Pitch", "pitch", "-24"), _parameter(2, "base-timbre", "Timbre", "positive", "1"), _parameter(3, "base-color", "Color", "positive", "0.5")]
        states = [_state(1, "voice-state", "structured"), _state(2, "strike-history", "boolean")]
        behavior = copy.deepcopy(core.load_json(ROOT / "contracts/task011b/component-contracts/sine.json")["behavior_rules"])
    elif slug == "vca":
        ports = [_port(1, "gain", "Gain", "inlet", "positive", True, "modulation"), _port(2, "audio-input", "Audio Input", "inlet", "audio", True, "audio"), _port(3, "audio-output", "Audio Output", "outlet", "audio", False, "audio")]
        states = [_state(1, "previous-gain"), _state(2, "interpolation-step")]
    elif slug == "dual-percussion-compound":
        ports = [_port(1, "clock", "Clock", "inlet", "clock", True, "clock"), _port(2, "voice-mix", "Voice Mix", "inlet", "positive", False, "crossfade-position"), _port(3, "audio-output", "Audio Output", "outlet", "audio", False, "audio")]
        states = [_state(1, "internal-component-state", "structured")]
        compound = {"kind": "transparent-compound", "mapping_keys": [{"mapping_key": "compound-mapping-key-000001", "facet_kind": "port", "facet_id": "component-port-000001"}, {"mapping_key": "compound-mapping-key-000002", "facet_kind": "port", "facet_id": "component-port-000003"}, {"mapping_key": "compound-mapping-key-000003", "facet_kind": "port", "facet_id": "component-port-000002"}]}
    else:
        raise KeyError(slug)
    capabilities = {"parameter_input_ports": ["component-port-000001"] if slug == "exponential-smoother" else [], "action_inputs": []}
    return ports, parameters, attributes, [], displays, states, compound, behavior


def _contracts(families: dict[str, dict[str, Any]], schema: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result = {}
    for spec in FAMILIES:
        ports, parameters, attributes, actions, displays, states, compound, behavior = _contract_shape(spec["slug"])
        lifecycle = {"state_model": "declared-state" if states else "stateless", "initialization": "initialize-declared-state" if states else "none", "reset_behavior": "declared-per-state" if states else "not-applicable", "disposal": "none"}
        contract = _record({
            "schema_version": "component-contract-v1", "canonical_profile": "schuss-canonical-json-v1",
            "component_contract_id": f"schuss-component-contract-{spec['contract']:06d}", "revision": 1, "content_hash": "sha256:" + "0" * 64,
            "family_reference": _ref(families[f"schuss-family-{spec['family']:06d}"], "family_id"), "display_name": spec["name"],
            "ports": ports, "parameters": parameters, "attributes": attributes, "actions": actions, "displays": displays,
            "state_declarations": states, "lifecycle": lifecycle,
            "binding_capabilities": {"parameter_input_ports": (["component-port-000001"] if spec["slug"] == "exponential-smoother" else (["component-port-000002"] if spec["slug"] == "dual-percussion-compound" else [])), "action_inputs": []},
            "capability_requirements": [], "compound_interface": compound, "compatibility_claims": [], "behavior_rules": behavior,
        }, schema)
        result[spec["slug"]] = contract
    return result


def _seams(spec: dict[str, Any], contract: dict[str, Any], observation: dict[str, Any]) -> list[dict[str, Any]]:
    facets = observation["facets"]
    mappings = []
    number = spec["implementation"] * 100
    for collection, kind, seam_kind, contract_collection in (("inlets", "port", "legacy-inlet", "ports"), ("outlets", "port", "legacy-outlet", "ports"), ("parameters", "parameter", "legacy-parameter", "parameters"), ("attributes", "attribute", "legacy-attribute", "attributes"), ("displays", "display", "legacy-display", "displays")):
        observed_values = facets[collection]
        if kind == "port":
            contract_values = [value for value in contract[contract_collection] if value["direction"] == ("inlet" if collection == "inlets" else "outlet")]
        else:
            contract_values = contract[contract_collection]
        if len(observed_values) != len(contract_values):
            raise ValueError(f"{spec['slug']} {collection} seam count differs")
        for observed, facet in zip(observed_values, contract_values):
            number += 1
            mappings.append({
                "mapping_id": f"binding-map-{number:06d}",
                "contract_facet": {"facet_kind": kind, "facet_id": facet["facet_id"]},
                "implementation_seam": {"seam_kind": seam_kind, "index": observed["index"], "name": observed["name"], "legacy_type": observed["legacy_type"], "data_type": observed.get("data_type")},
            })
    return mappings


def _dependencies(slug: str, evidence_ref: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    ids = {
        "pseudo-euclidean": ["ksoloti-runtime-random"], "saw-oscillator": ["ksoloti-blep-runtime", "ksoloti-pitch-runtime"], "pwm-oscillator": ["ksoloti-blep-runtime", "ksoloti-pitch-runtime"],
        "attack-decay": ["ksoloti-pitch-runtime", "arm-fixed-point-runtime"], "exponential-smoother": ["arm-fixed-point-runtime"], "audio-soft-clip": ["arm-fixed-point-runtime"],
        "rings-reverb": ["rings-fx-header", "sdram-allocator"], "struck-drum": ["brds-digital-header"], "struck-bell": ["brds-digital-header"], "vca": ["arm-fixed-point-runtime"],
    }.get(slug, [])
    observed = [{"dependency_id": value, "evidence_ref": evidence_ref} for value in ids]
    locators = {"rings-fx-header": "3da1acbf013cd4d7c2a105c95d99e19b0b1c173addc24dc2f79af85523d0a55b", "brds-digital-header": "e132f0d876ea54c26f301e448f1c079243433aaa7acf7743a35c928e9c3d95c4"}
    requirements = [
        {
            "dependency_id": value,
            "portable_locator": "sha256/" + locators[value],
            "state": {"status": "supported", "evidence_refs": [evidence_ref]},
        }
        for value in ids
        if value in locators
    ]
    resources = []
    if slug == "rings-reverb":
        resources.append({"requirement_id": "binding-resource-requirement-000001", "resource_kind": "data", "region_id": "target-memory-region-000005", "amount_bytes": 32768, "alignment_bytes": 4, "state": {"status": "not-evaluated", "code": "DIRECT_RESOURCE_NOT_EVALUATED", "rationale": "The legacy source requests 32768 bytes, but Task 017 does not prove a direct runtime allocation contract."}})
    return observed, requirements, resources


def _private_states(slug: str) -> list[dict[str, Any]]:
    return [{"state_key": key, "value_kind": kind} for key, kind in {
        "logic-toggle": [("trigger-history", "integer"), ("latched-output", "integer")],
        "pseudo-euclidean": [("recurrence", "structured"), ("trigger-history", "integer"), ("reset-history", "integer")],
        "saw-oscillator": [("phase", "integer"), ("blep-voices", "structured")], "pwm-oscillator": [("phase", "integer"), ("blep-voices", "structured"), ("pulse-width", "integer")],
        "attack-decay": [("stage", "integer"), ("trigger-history", "integer"), ("envelope-value", "fixed-point")], "exponential-smoother": [("smoothed-value", "fixed-point")],
        "rings-reverb": [("reverb-state", "structured"), ("sdram-buffer", "bytes")], "struck-drum": [("voice-state", "structured"), ("strike-history", "integer")],
        "struck-bell": [("voice-state", "structured"), ("strike-history", "integer")], "vca": [("previous-gain", "fixed-point"), ("interpolation-step", "fixed-point")],
    }.get(slug, [])]


def _legacy_binding(spec: dict[str, Any], contract: dict[str, Any], observation: dict[str, Any], revision: int, schema: dict[str, Any]) -> dict[str, Any]:
    evidence_ref = f"legacy-resolved-catalog-v0:object:{observation['variant_index']}"
    observed_dependencies, _, _ = _dependencies(spec["slug"], evidence_ref)
    form = "generated-legacy-object" if observation["origin"].get("generated_by") else "legacy-native-object"
    return _record({
        "schema_version": "implementation-binding-v2", "canonical_profile": "schuss-canonical-json-v1",
        "implementation_id": f"schuss-implementation-{spec['implementation']:06d}", "revision": revision, "content_hash": "sha256:" + "0" * 64,
        "contract_reference": _ref(contract, "component_contract_id"),
        "realization": {"form": form, "observation": {"snapshot_schema_version": "legacy-resolved-catalog-v0", "manifest_sha256": MANIFEST_SHA256, "evidence_ref": evidence_ref, "variant_index": observation["variant_index"], "legacy_uuid_sha256": "sha256:" + hashlib.sha256(observation["uuid"]["durable_value"].encode("utf-8")).hexdigest(), "source_id": observation["origin"]["source_id"], "source_sha256": observation["origin"]["sha256"]}},
        "facet_mappings": _seams(spec, contract, observation), "observed_dependencies": observed_dependencies, "private_state": _private_states(spec["slug"]),
        "evidence_refs": [evidence_ref], "selection_state": {"status": "not-evaluated", "owner": "task-007", "reason": "target-backend-contracts-not-yet-implemented", "rationale": "Task 017 authenticates source and seam structure without promoting unreviewed direct DSP/runtime behavior."},
    }, schema)


def _graph_record(value: dict[str, Any]) -> dict[str, Any]:
    return _record(value, core.load_json(ROOT / "schemas/dsp-graph-v0.schema.json"))


def _node(number: int, contract: dict[str, Any], parameters: list[tuple[int, str]] = (), attributes: list[tuple[int, str]] = ()) -> dict[str, Any]:
    return {"node_id": f"graph-node-{number:06d}", "contract_reference": _ref(contract, "component_contract_id"), "parameter_values": [{"facet_id": f"component-parameter-{index:06d}", "value": value} for index, value in parameters], "attribute_values": [{"facet_id": f"component-attribute-{index:06d}", "value": value} for index, value in attributes]}


def _connection(number: int, source_node: int, source_port: int, destination_node: int, destination_port: int) -> dict[str, Any]:
    return {"connection_id": f"graph-connection-{number:06d}", "source": {"node_id": f"graph-node-{source_node:06d}", "facet_id": f"component-port-{source_port:06d}"}, "destination": {"node_id": f"graph-node-{destination_node:06d}", "facet_id": f"component-port-{destination_port:06d}"}}


def _base_graph(graph_id: int, name: str, nodes: list[dict[str, Any]], connections: list[dict[str, Any]]) -> dict[str, Any]:
    return {"schema_version": "dsp-graph-v0", "canonical_profile": "schuss-canonical-json-v1", "graph_id": f"schuss-graph-{graph_id:06d}", "revision": 1, "content_hash": "sha256:" + "0" * 64, "display_name": name, "nodes": nodes, "connections": connections, "public_ports": [], "public_parameters": [], "public_actions": [], "public_displays": [], "public_port_exposures": [], "public_facet_exposures": [], "parameter_bindings": [], "compound_interface_mappings": [], "hierarchy_edges": []}


def _parameter_binding(number: int, graph_facet: int, node: int, facet_kind: str, facet: int, source_domain: dict[str, Any], destination_domain: dict[str, Any]) -> dict[str, Any]:
    return {"binding_id": f"graph-binding-{number:06d}", "binding_kind": "parameter-to-port" if facet_kind == "port" else "parameter-to-parameter", "source_graph_parameter_id": f"graph-facet-{graph_facet:06d}", "destination": {"node_id": f"graph-node-{node:06d}", "facet_kind": facet_kind, "facet_id": f"component-{facet_kind}-{facet:06d}"}, "source_domain": copy.deepcopy(source_domain), "destination_domain": copy.deepcopy(destination_domain), "transform": {"curve": "linear", "polarity": "direct", "points": [{"source": source_domain["minimum"], "destination": destination_domain["minimum"]}, {"source": source_domain["maximum"], "destination": destination_domain["maximum"]}]}, "update_boundary": "control-cycle", "smoothing": {"kind": "linear", "responsibility": "graph", "completion": "next-control-cycle"}, "driver_policy": "exclusive"}


def _graphs(contracts: dict[str, dict[str, Any]], accepted: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    euclid, toggle, drum, bell, ad, vca = (contracts[key] for key in ("pseudo-euclidean", "logic-toggle", "struck-drum", "struck-bell", "attack-decay", "vca"))
    crossfader = accepted["crossfader"]
    inner = _base_graph(5, "Dual percussion transparent implementation", [_node(1, euclid), _node(2, toggle), _node(3, drum, [(1, "-24")]), _node(4, bell, [(1, "-12")]), _node(5, ad), _node(6, crossfader), _node(7, vca)], [
        _connection(1, 1, 5, 2, 1), _connection(2, 1, 5, 3, 4), _connection(3, 1, 5, 5, 1), _connection(4, 2, 2, 4, 4),
        _connection(5, 3, 5, 6, 1), _connection(6, 4, 5, 6, 2), _connection(7, 1, 4, 6, 3), _connection(8, 5, 2, 7, 1), _connection(9, 6, 4, 7, 2),
    ])
    inner["public_ports"] = [{"facet_id": "graph-facet-000001", "semantic_key": "clock", "display_label": "Clock", "direction": "input"}, {"facet_id": "graph-facet-000002", "semantic_key": "audio-output", "display_label": "Audio Output", "direction": "output"}]
    normalized = {"status": "known", "minimum": "0", "maximum": "1", "minimum_inclusive": True, "maximum_inclusive": True, "overflow_policy": "reject", "unit": "normalized"}
    inner["public_port_exposures"] = [{"exposure_id": "graph-exposure-000001", "graph_facet_id": "graph-facet-000001", "node_port": {"node_id": "graph-node-000001", "facet_id": "component-port-000002"}}, {"exposure_id": "graph-exposure-000002", "graph_facet_id": "graph-facet-000002", "node_port": {"node_id": "graph-node-000007", "facet_id": "component-port-000003"}}]
    inner["compound_interface_mappings"] = [{"mapping_key": "compound-mapping-key-000001", "target": {"node_id": "graph-node-000001", "facet_kind": "port", "facet_id": "component-port-000002"}}, {"mapping_key": "compound-mapping-key-000002", "target": {"node_id": "graph-node-000007", "facet_kind": "port", "facet_id": "component-port-000003"}}, {"mapping_key": "compound-mapping-key-000003", "target": {"node_id": "graph-node-000006", "facet_kind": "port", "facet_id": "component-port-000003"}}]
    inner = _graph_record(inner)

    compound, lfo, output = contracts["dual-percussion-compound"], accepted["lfo"], accepted["output"]
    percussion = _base_graph(3, "Clocked dual-percussion reference graph", [_node(1, lfo), _node(2, compound), _node(3, output)], [_connection(1, 1, 3, 2, 1), _connection(2, 2, 3, 3, 1), _connection(3, 2, 3, 3, 2)])
    percussion["public_parameters"] = [{"facet_id": "graph-facet-000001", "semantic_key": "voice-mix", "display_label": "Voice Mix", "value_type": "exact-decimal", "domain": normalized, "default": "0.5", "update_behavior": {"update_kind": "runtime", "stateful": True}}]
    percussion["parameter_bindings"] = [_parameter_binding(1, 1, 2, "port", 2, normalized, normalized)]
    percussion = _graph_record(percussion)

    saw, pwm, soft, reverb, smooth = (contracts[key] for key in ("saw-oscillator", "pwm-oscillator", "audio-soft-clip", "rings-reverb", "exponential-smoother"))
    effects = _base_graph(4, "Modulated dual-oscillator effects reference graph", [_node(1, saw, [(1, "-24")]), _node(2, pwm, [(1, "-12")]), _node(3, soft), _node(4, reverb), _node(5, smooth), _node(6, crossfader), _node(7, vca), _node(8, output)], [
        _connection(1, 1, 2, 3, 1), _connection(2, 3, 2, 6, 1), _connection(3, 3, 2, 4, 1), _connection(4, 2, 3, 4, 2), _connection(5, 4, 3, 6, 2), _connection(6, 5, 2, 7, 1), _connection(7, 6, 4, 7, 2), _connection(8, 7, 3, 8, 1), _connection(9, 7, 3, 8, 2),
    ])
    effects["public_parameters"] = [{"facet_id": "graph-facet-000001", "semantic_key": "motion", "display_label": "Motion", "value_type": "exact-decimal", "domain": normalized, "default": "0.5", "update_behavior": {"update_kind": "runtime", "stateful": True}}, {"facet_id": "graph-facet-000002", "semantic_key": "blend", "display_label": "Blend", "value_type": "exact-decimal", "domain": normalized, "default": "0.5", "update_behavior": {"update_kind": "runtime", "stateful": True}}]
    smooth_domain = copy.deepcopy(smooth["ports"][0]["port_type"]["valid_range"]); smooth_domain["unit"] = smooth["ports"][0]["port_type"]["unit"]
    fade_domain = copy.deepcopy(crossfader["ports"][2]["port_type"]["valid_range"]); fade_domain["unit"] = crossfader["ports"][2]["port_type"]["unit"]
    effects["parameter_bindings"] = [_parameter_binding(1, 1, 5, "port", 1, normalized, smooth_domain), _parameter_binding(2, 2, 6, "port", 3, normalized, fade_domain)]
    effects = _graph_record(effects)
    return {"compound": inner, "percussion": percussion, "effects": effects}


def _compound_binding(spec: dict[str, Any], contract: dict[str, Any], graph: dict[str, Any], revision: int, schema: dict[str, Any]) -> dict[str, Any]:
    return _record({"schema_version": "implementation-binding-v2", "canonical_profile": "schuss-canonical-json-v1", "implementation_id": f"schuss-implementation-{spec['implementation']:06d}", "revision": revision, "content_hash": "sha256:" + "0" * 64, "contract_reference": _ref(contract, "component_contract_id"), "realization": {"form": "transparent-compound", "graph_reference": _ref(graph, "graph_id")}, "facet_mappings": [{"mapping_id": "binding-map-006001", "contract_facet": {"facet_kind": "port", "facet_id": "component-port-000001"}, "implementation_seam": {"seam_kind": "graph-mapping-key", "mapping_key": "compound-mapping-key-000001"}}, {"mapping_id": "binding-map-006002", "contract_facet": {"facet_kind": "port", "facet_id": "component-port-000003"}, "implementation_seam": {"seam_kind": "graph-mapping-key", "mapping_key": "compound-mapping-key-000002"}}, {"mapping_id": "binding-map-006003", "contract_facet": {"facet_kind": "port", "facet_id": "component-port-000002"}, "implementation_seam": {"seam_kind": "graph-mapping-key", "mapping_key": "compound-mapping-key-000003"}}], "observed_dependencies": [], "private_state": [{"state_key": "internal-component-state", "value_kind": "structured"}], "evidence_refs": ["fixture:task017-dual-percussion"], "selection_state": {"status": "not-evaluated", "owner": "task-007", "reason": "target-backend-contracts-not-yet-implemented", "rationale": "Task 017 validates the transparent graph and exact mappings; internal bindings remain independently eligible or unsupported."}}, schema)


def _evidence(spec: dict[str, Any], candidate: dict[str, Any], contract: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    number = 25 + list(FAMILIES).index(spec)
    method = "task017-transparent-compound-structural-validation" if spec["variant"] is None else "task017-pinned-source-and-exact-seam-review"
    return _record({"schema_version": "evidence-claim-v0", "canonical_profile": "schuss-canonical-json-v1", "evidence_claim_id": f"schuss-evidence-claim-{number:06d}", "revision": 1, "content_hash": "sha256:" + "0" * 64, "level": 2, "level_name": "component-graph-resolution", "subject_reference": {"subject_kind": "semantic-record", "stable_id": candidate["implementation_id"], "revision": candidate["revision"], "content_hash": candidate["content_hash"], "stage": "target-independent-graph-validation"}, "method": method, "outcome": "passed", "evidence_inputs": [_semantic_ref(candidate, "implementation_id"), _semantic_ref(contract, "component_contract_id")], "limitations": ["No Task 016 direct DSP/runtime compatibility is implied.", "No device, real-time, audible, UI, hardware, or publication evidence is established."], "producer_identity": {"producer_kind": "validator", "producer_id": "schuss-task017-validator", "version": "task017-v1", "content_hash": "sha256:" + hashlib.sha256(b"schuss-task017-validator-v1").hexdigest()}}, schema)


def _backend(schema: dict[str, Any]) -> dict[str, Any]:
    value = core.load_json(ROOT / "contracts/task016/direct-backend.json")
    value["revision"] = 2
    value["display_name"] = "Direct native Ksoloti runtime backend with transparent compounds"
    value["lowering_identity"]["contract_version"] = "direct-gills-task017-v1"
    value["supported_realization_forms"] = ["native-cpp", "transparent-compound"]
    value["target_pairings"][0]["rationale"] = "Task 017 adds only transparent compound elaboration; every native operation remains the accepted Task 016 legacy-equivalent realization."
    return _record(value, schema)


def _eligibility(spec: dict[str, Any], promoted: dict[str, Any], contract: dict[str, Any], evidence: dict[str, Any], backend: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    _, dependencies, resources = _dependencies(spec["slug"], f"legacy-resolved-catalog-v0:object:{spec['variant']}" if spec["variant"] is not None else "fixture:task017-dual-percussion")
    evidence_ref = _ref(evidence, "evidence_claim_id")
    supported = spec["variant"] is None
    state = ({"status": "supported", "evidence_level": 2, "evidence_refs": [evidence_ref]} if supported else {"status": "not-evaluated", "code": "DIRECT_OPERATION_UNSUPPORTED", "rationale": "Task 017 records exact legacy source and seams but does not create a direct operation specification or native realization."})
    backend_requirements = core.load_json(ROOT / "contracts/task016/binding-eligibility-output.json")["capability_requirements"]
    return _record({"schema_version": "binding-eligibility-v0", "canonical_profile": "schuss-canonical-json-v1", "binding_eligibility_id": f"schuss-binding-eligibility-{15 + list(FAMILIES).index(spec):06d}", "revision": 1, "content_hash": "sha256:" + "0" * 64, "binding_reference": _ref(promoted, "implementation_id"), "contract_reference": _ref(contract, "component_contract_id"), "allowed_pair": {"target_reference": copy.deepcopy(TARGET_REFERENCE), "backend_reference": _ref(backend, "backend_id"), "state": state}, "realization_form": promoted["realization"]["form"], "capability_requirements": backend_requirements, "dependency_requirements": dependencies, "resource_requirements": resources, "required_evidence_level": 2, "compatibility_evidence": [evidence_ref], "selection_policy": {"policy_id": f"schuss-selection-policy-{15 + list(FAMILIES).index(spec):06d}", "version": 1, "priority": 100, "ranking_rule": "higher-explicit-priority", "tie_behavior": "ambiguous", "implicit_fallback": False}, "unresolved_questions": ([] if supported else [{"question_id": f"eligibility-question-{15 + list(FAMILIES).index(spec):06d}", "code": "DIRECT_SEMANTICS_UNSPECIFIED", "owner": "backend-owner", "earliest_task": "task-017", "question": "What exact legacy-equivalent direct operation and runtime contract realizes this binding?", "rationale": "Source/seam review is not direct behavioral equivalence."}])}, schema)


def _carry_forward_eligibilities(backend: dict[str, Any], schema: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for path in sorted((ROOT / "contracts/task016").glob("binding-eligibility-*.json")):
        value = core.load_json(path)
        value["revision"] = 2
        value["allowed_pair"]["backend_reference"] = _ref(backend, "backend_id")
        result.append(_record(value, schema))
    return result


def _instrument(number: int, name: str, graph: dict[str, Any], parameters: list[tuple[str, str]], mapped_device_parameter: int, schema: dict[str, Any]) -> dict[str, Any]:
    normalized = {"minimum": "0", "maximum": "1", "unit": "normalized"}
    values = [{"facet_id": f"instrument-parameter-{index:06d}", "display_label": label, "value_type": "exact-decimal", "domain": normalized, "default": "0.5", "update_behavior": {"update_kind": "runtime", "smoothing_responsibility": "graph", "stateful": True}} for index, (_, label) in enumerate(parameters, 1)]
    graph_mappings = [{"mapping_id": f"graph-mapping-{index:06d}", "mapping_kind": "parameter-to-parameter", "direction": "instrument-to-graph", "source": {"facet_kind": "parameter", "facet_id": f"instrument-parameter-{index:06d}"}, "destination": {"facet_kind": "parameter", "facet_id": f"graph-facet-{index:06d}"}, "source_domain": normalized, "destination_domain": normalized, "transform": {"curve": "linear", "polarity": "direct", "points": [{"source": "0", "destination": "0"}, {"source": "1", "destination": "1"}]}} for index in range(1, len(parameters) + 1)]
    device_mapping = {"mapping_id": "device-mapping-000001", "mapping_kind": "parameter-control", "direction": "device-to-instrument", "source": {"facet_kind": "input-control", "slot_id": "device-input-000001"}, "destination": {"facet_kind": "parameter", "facet_id": f"instrument-parameter-{mapped_device_parameter:06d}"}, "source_domain": normalized, "destination_domain": normalized, "transform": {"curve": "linear", "polarity": "direct", "points": [{"source": "0", "destination": "0"}, {"source": "1", "destination": "1"}]}, "response": {"response_time": "control-update", "smoothing_responsibility": "graph"}, "pickup": {"mode": "soft", "responsibility": "instrument"}}
    return _record({"schema_version": "instrument-v0", "canonical_profile": "schuss-canonical-json-v1", "instrument_id": f"schuss-instrument-{number:06d}", "revision": 1, "content_hash": "sha256:" + "0" * 64, "display_name": name, "device_profile_reference": copy.deepcopy(DEVICE_REFERENCE), "graph_reference": {"status": "resolved", **_ref(graph, "graph_id")}, "parameters": values, "actions": [], "displays": [], "state_declarations": [{"state_id": "instrument-state-000001", "display_label": "Performance State", "value_kind": "boolean", "persistence": "volatile", "reset_policy": "default-on-start"}], "device_input_mappings": [device_mapping], "device_feedback_mappings": [], "graph_mappings": graph_mappings}, schema)


def _request(number: int, graph: dict[str, Any], instrument: dict[str, Any], backend: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    value = core.load_json(ROOT / "contracts/task016/four-step-dual-sine-direct-build-request-r3.json")
    value["build_request_id"] = f"schuss-build-request-{number:06d}"
    value["revision"] = 1
    value["graph_reference"] = _ref(graph, "graph_id")
    value["instrument_reference"] = {"status": "included", **_ref(instrument, "instrument_id")}
    value["backend_reference"] = _ref(backend, "backend_id")
    value["binding_overrides"] = []
    return _record(value, schema)


def generated() -> tuple[dict[str, bytes], bytes]:
    schemas = _schema_files()
    for name, schema in schemas.items():
        errors = core.validate_schema_annotations(schema)
        if errors: raise ValueError(f"{name}: {errors}")
    observations = _observations()
    usage = _usage_counts()
    if {key: usage[key] for key in EXPECTED_USAGE} != EXPECTED_USAGE:
        raise ValueError("complete-graph usage evidence changed")
    parent = core.load_json(PARENT)
    parent_corpus = core.load_json(ROOT / "contracts/catalog/task011a-corpus-v1.json")
    corpus, families, implementations = _catalog(parent_corpus, observations, schemas["catalog-corpus-v2.schema.json"])
    contracts = _contracts(families, core.load_json(ROOT / "schemas/component-contract-v1.schema.json"))
    accepted = {"lfo": core.load_json(ROOT / "contracts/task011b/component-contracts/lfo.json"), "crossfader": core.load_json(ROOT / "contracts/component-contracts/crossfader-mixed-v0.json"), "output": core.load_json(ROOT / "contracts/task011b/component-contracts/output.json")}
    graphs = _graphs(contracts, accepted)
    backend = _backend(core.load_json(ROOT / "schemas/backend-v0.schema.json"))
    candidate_bindings: dict[str, dict[str, Any]] = {}
    promoted_bindings: dict[str, dict[str, Any]] = {}
    evidence: dict[str, dict[str, Any]] = {}
    eligibilities: dict[str, dict[str, Any]] = {}
    binding_schema = schemas["implementation-binding-v2.schema.json"]
    evidence_schema = core.load_json(ROOT / "schemas/evidence-claim-v0.schema.json")
    eligibility_schema = core.load_json(ROOT / "schemas/binding-eligibility-v0.schema.json")
    for spec in FAMILIES:
        contract = contracts[spec["slug"]]
        if spec["variant"] is None:
            candidate = _compound_binding(spec, contract, graphs["compound"], 1, binding_schema)
            promoted = _compound_binding(spec, contract, graphs["compound"], 2, binding_schema)
        else:
            candidate = _legacy_binding(spec, contract, observations[spec["variant"]], 1, binding_schema)
            promoted = _legacy_binding(spec, contract, observations[spec["variant"]], 2, binding_schema)
        claim = _evidence(spec, candidate, contract, evidence_schema)
        eligibility = _eligibility(spec, promoted, contract, claim, backend, eligibility_schema)
        candidate_bindings[spec["slug"]], promoted_bindings[spec["slug"]], evidence[spec["slug"]], eligibilities[spec["slug"]] = candidate, promoted, claim, eligibility
    carried = _carry_forward_eligibilities(backend, eligibility_schema)
    instrument_schema = core.load_json(ROOT / "schemas/instrument-v0.schema.json")
    instruments = {"percussion": _instrument(3, "Clocked dual-percussion reference instrument", graphs["percussion"], [("voice-mix", "Voice Mix")], 1, instrument_schema), "effects": _instrument(4, "Modulated oscillator effects reference instrument", graphs["effects"], [("motion", "Motion"), ("blend", "Blend")], 1, instrument_schema)}
    request_schema = core.load_json(ROOT / "schemas/build-request-v0.schema.json")
    requests = {"percussion": _request(3, graphs["percussion"], instruments["percussion"], backend, request_schema), "effects": _request(4, graphs["effects"], instruments["effects"], backend, request_schema)}
    selector = _record({"schema_version": "catalog-selection-v0", "canonical_profile": "schuss-canonical-json-v1", "catalog_selection_id": "schuss-catalog-selection-000001", "revision": 1, "content_hash": "sha256:" + "0" * 64, "corpus_reference": _ref(corpus, "catalog_id"), "rationale": "The Task 017 exact record set explicitly selects corpus revision 2; revision 1 remains an immutable parent member."}, schemas["catalog-selection-v0.schema.json"])
    packet = _selection_packet(parent, families, implementations, graphs, instruments, requests, usage, schemas["core-selection-packet-v0.schema.json"])

    records: dict[str, tuple[str, dict[str, Any]]] = {"catalog-corpus-v2.json": ("catalog-corpus", corpus), "catalog-selection.json": ("catalog-selection", selector), "selection-packet.json": ("core-selection-packet", packet), "direct-backend-r2.json": ("backend", backend)}
    for spec in FAMILIES:
        slug = spec["slug"]
        records[f"component-contract-{slug}.json"] = ("component-contract", contracts[slug])
        records[f"implementation-binding-{slug}-candidate-r1.json"] = ("implementation-binding", candidate_bindings[slug])
        records[f"implementation-binding-{slug}-r2.json"] = ("implementation-binding", promoted_bindings[slug])
        records[f"compatibility-evidence-{slug}.json"] = ("evidence", evidence[slug])
        records[f"binding-eligibility-{slug}.json"] = ("eligibility", eligibilities[slug])
    for value in carried:
        records[f"carried-{value['binding_eligibility_id']}-r2.json"] = ("eligibility", value)
    for name, value in graphs.items(): records[f"graph-{name}.json"] = ("dsp-graph", value)
    for name, value in instruments.items(): records[f"instrument-{name}.json"] = ("instrument", value)
    for name, value in requests.items(): records[f"build-request-{name}.json"] = ("request", value)

    files: dict[str, bytes] = {f"schemas/{name}": core.canonical_json(value).encode("utf-8") + b"\n" for name, value in schemas.items()}
    files.update({f"contracts/task017/{name}": core.canonical_json(value).encode("utf-8") + b"\n" for name, (_, value) in records.items()})
    schema_members = copy.deepcopy(parent["schema_members"])
    for name, schema in schemas.items(): schema_members.append({"schema_version": schema["$id"].removesuffix(".schema.json"), "portable_path": f"schemas/{name}", "byte_sha256": hashlib.sha256(files[f"schemas/{name}"]).hexdigest()})
    record_members = copy.deepcopy(parent["record_members"])
    for name, (kind, record) in records.items():
        relative = f"contracts/task017/{name}"
        id_field = next(field for field in record_set_rules.ID_FIELDS if field in record)
        record_members.append({"record_kind": kind, "stable_id": record[id_field], "revision": record["revision"], "content_hash": record["content_hash"], "portable_path": relative, "byte_sha256": hashlib.sha256(files[relative]).hexdigest()})
    manifest_schema = core.load_json(ROOT / record_set_rules.RECORD_SET_SCHEMA)
    manifest = {"schema_version": "record-set-v0", "canonical_profile": "schuss-canonical-json-v1", "record_set_id": "schuss-record-set-000011", "revision": 1, "content_hash": "sha256:" + "0" * 64, "purpose": "prospective-task", "parent_reference": {"status": "included", **{key: parent[key] for key in ("record_set_id", "revision", "content_hash")}}, "schema_members": sorted(schema_members, key=lambda item: (item["schema_version"], item["portable_path"])), "record_members": sorted(record_members, key=lambda item: (item["byte_sha256"], item["portable_path"])), "enforced_directories": sorted(parent["enforced_directories"] + ["contracts/task017"])}
    manifest["content_hash"] = core.record_content_hash(manifest, manifest_schema)
    return files, core.canonical_json(manifest).encode("utf-8") + b"\n"


def _selection_packet(parent: dict[str, Any], families: dict[str, dict[str, Any]], implementations: dict[str, dict[str, Any]], graphs: dict[str, dict[str, Any]], instruments: dict[str, dict[str, Any]], requests: dict[str, dict[str, Any]], usage: Counter[int], schema: dict[str, Any]) -> dict[str, Any]:
    included = []
    observations = _observations()
    for spec in FAMILIES:
        unresolved = ["Connected-device, real-time, audible, UI, and publication evidence are absent."]
        if spec["variant"] is None:
            unresolved.append("Transparent wrapper support does not establish direct support for its internal legacy bindings.")
            license_observation = "not-declared"
        else:
            unresolved.append("No native direct operation is promoted for this family in Task 017.")
            license_observation = observations[spec["variant"]]["metadata"]["license"]
        if spec["slug"] == "rings-reverb":
            unresolved.append("The observed 32768-byte SDRAM request has no evaluated direct allocation contract.")
        included.append({"family_reference": {"stable_id": f"schuss-family-{spec['family']:06d}", "revision": 1, "content_hash": families[f"schuss-family-{spec['family']:06d}"]["content_hash"]}, "implementation_reference": {"stable_id": f"schuss-implementation-{spec['implementation']:06d}", "revision": 1, "content_hash": implementations[f"schuss-implementation-{spec['implementation']:06d}"]["content_hash"]}, "primary_category": spec["category"], "complete_graph_reference_count": usage[spec["variant"]] if spec["variant"] is not None else 0, "selection_rationale": spec["rationale"], "semantic_summary": spec["semantics"], "license_observation": license_observation, "compatibility_status": "transparent-compound-structural" if spec["variant"] is None else "structural-source-and-seam-reviewed", "direct_backend_status": "transparent-wrapper-supported-internals-unsupported" if spec["variant"] is None else "unsupported", "unresolved_facts": unresolved})
    refs = []
    for key, status, concept in (("percussion", "invalid", "Clocked transparent percussion compound"), ("effects", "unsupported", "Modulated oscillator and stereo-effects chain")):
        refs.append({"instrument_reference": {"stable_id": instruments[key]["instrument_id"], "revision": 1, "content_hash": instruments[key]["content_hash"]}, "graph_reference": {"stable_id": graphs[key]["graph_id"], "revision": 1, "content_hash": graphs[key]["content_hash"]}, "build_request_reference": {"stable_id": requests[key]["build_request_id"], "revision": 1, "content_hash": requests[key]["content_hash"]}, "concept": concept, "expected_plan_status": status})
    names = ("structural-schema", "component-graph-resolution", "backend-lowering", "source-artifact-generation", "arm-compile-link", "connected-device", "real-time-resource", "audible-listening")
    return _record({"schema_version": "core-selection-packet-v0", "canonical_profile": "schuss-canonical-json-v1", "selection_packet_id": "schuss-core-selection-000001", "revision": 1, "content_hash": "sha256:" + "0" * 64, "accepted_parent_reference": {"stable_id": parent["record_set_id"], "revision": parent["revision"], "content_hash": parent["content_hash"]}, "inventory_audit": {"complete_graphs": 348, "resolved_observations": 3602, "reviewed_families": 28, "top_200_coverage": "84.15%", "frequency_policy": "prioritization-only"}, "criteria": ["balanced functional coverage", "exact source and identity evidence", "headless graph utility", "state and modulation value", "license declaration retained without inference", "direct support must be exact or unsupported"], "included_families": included, "excluded_candidates": [{"variant_index": variant, "complete_graph_reference_count": count, "legacy_id": legacy, "rationale": rationale} for variant, count, legacy, rationale in EXCLUDED], "reference_instruments": refs, "evidence_boundaries": [{"level": index, "name": name, "status": "passed" if index <= 2 else "not-run"} for index, name in enumerate(names, 1)]}, schema)


_TYPE_TEMPLATES = _type_templates()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files, manifest = generated()
    files[OUTPUT.relative_to(ROOT).as_posix()] = manifest
    stale = [relative for relative, payload in files.items() if not (ROOT / relative).is_file() or (ROOT / relative).read_bytes() != payload]
    if args.check:
        if stale:
            print("Task 017 generated files are stale: " + ", ".join(sorted(stale)), file=sys.stderr)
            return 1
    else:
        for relative, payload in files.items():
            path = ROOT / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
    print("Task 017 records " + ("passed" if args.check else "generated") + f": files={len(files)} manifest_sha256={hashlib.sha256(manifest).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
