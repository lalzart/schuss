#!/usr/bin/env python3
"""Generate the Task 030 complete Mutable catalog and object-search schemas."""

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

import record_set_rules  # noqa: E402
import validator_core as core  # noqa: E402


PARENT = ROOT / "contracts/record-sets/task029-gills-machines-v1.json"
OUTPUT = ROOT / "contracts/record-sets/task030-complete-mutable-catalog-v1.json"
TASK027_REVIEW = ROOT / "contracts/task027/catalog-source-review.json"
TASK024_CANDIDATES = ROOT / "catalog/reviews/task024-current-ksoloti-v1/candidates.jsonl"
DECISION = ROOT / "contracts/task030/mutable-catalog-curation.md"
MUTABLE_TAG = "mutable-instruments-derived"
PATCHER_COMMIT = "08d3e6e1e2b61230308c20a15ded58ffdaf4656c"


# One family per distinct reviewed function keeps individual objects visible.
# Only the three entries in REUSED_FAMILIES share an accepted family.
NEW_FAMILY_SPECS: tuple[dict[str, Any], ...] = (
    {"key": "com.lalzart.ksoloti.extended.sequencing.topographic-3", "id": 61, "name": "Topographic Rhythm Sequencer", "category": "timing-sequencing", "aliases": ["Grids-derived Three-channel Sequencer"], "tags": ["density-sequencing", "rhythm-map"], "description": "Generates three related rhythm and accent streams by navigating a two-dimensional pattern map."},
    {"key": "com.lalzart.ksoloti.extended.synthesis.macro-voice", "id": 62, "name": "Macro Voice", "category": "sound-sources", "aliases": ["24-engine Macro Voice"], "tags": ["multi-engine-synthesis", "voice"], "description": "Generates paired audio outputs from a selectable multi-engine voice with pitch, harmonics, timbre, morph, and trigger control."},
    {"key": "axoloti-factory:fx/clds/pitchshifter", "id": 63, "name": "Granular Pitch Shifter", "category": "pitch-notes", "aliases": ["Clouds-derived Pitch Shifter"], "tags": ["audio-pitch-shifting", "granular-processing"], "description": "Shifts the pitch of an audio signal with the reviewed granular pitch-shifting source object."},
    {"key": "axoloti-factory:fx/lmnts/diffuser", "id": 64, "name": "Diffusion Processor", "category": "delay-reverb", "aliases": ["Elements-derived Diffuser"], "tags": ["diffusion", "time-processing"], "description": "Diffuses an audio signal through the reviewed source effect."},
    {"key": "axoloti-factory:fx/lmnts/reverb", "id": 65, "name": "Stereo Diffusion Reverb", "category": "delay-reverb", "aliases": ["Elements-derived Reverb"], "tags": ["reverberation", "stereo-effect"], "description": "Processes audio with the reviewed Elements-derived reverb source object."},
    {"key": "axoloti-factory:fx/rngs/chorus", "id": 66, "name": "Chorus", "category": "delay-reverb", "aliases": ["Rings-derived Chorus"], "tags": ["chorus", "modulated-delay"], "description": "Applies the reviewed chorus effect to an audio signal."},
    {"key": "axoloti-factory:fx/rngs/ensemble", "id": 67, "name": "Ensemble", "category": "delay-reverb", "aliases": ["Rings-derived Ensemble"], "tags": ["ensemble", "modulated-delay"], "description": "Applies the reviewed ensemble effect to an audio signal."},
    {"key": "axoloti-factory:fx/strms/strms", "id": 68, "name": "Dynamics Control Generator", "category": "modulation-control", "aliases": ["Streams-like Control Processor"], "tags": ["dynamics-control", "gain-control"], "description": "Derives frequency and gain control values from the reviewed dynamics-processing source object; its outputs are not audio."},
    {"key": "axoloti-factory:fx/wrps/vocoder", "id": 69, "name": "Vocoder", "category": "spectral-analysis", "aliases": ["Warps-derived Vocoder"], "tags": ["cross-synthesis", "vocoder"], "description": "Processes carrier and modulator audio with the reviewed vocoder source object."},
    {"key": "axoloti-factory:fx/wrps/wrps", "id": 70, "name": "Cross-modulation Processor", "category": "shaping-dynamics", "aliases": ["Warps-like Processor"], "tags": ["cross-modulation", "waveshaping"], "description": "Processes paired audio through the reviewed cross-modulation source object; the retained source says it does not currently link."},
    {"key": "axoloti-factory:osc/brds/blown", "id": 71, "name": "Blown Physical Voice", "category": "sound-sources", "aliases": ["Braids Blown"], "tags": ["physical-modeling", "wind-voice"], "description": "Generates a blown physical-model voice with pitch, timbre, color, and strike control."},
    {"key": "axoloti-factory:osc/brds/bowed", "id": 72, "name": "Bowed Physical Voice", "category": "sound-sources", "aliases": ["Braids Bowed"], "tags": ["bowed-voice", "physical-modeling"], "description": "Generates a bowed physical-model voice with pitch, timbre, color, and strike control."},
    {"key": "axoloti-factory:osc/brds/buzz", "id": 73, "name": "Buzz Sine-fold Voice", "category": "sound-sources", "aliases": ["Braids Buzz"], "tags": ["sine-folding", "virtual-analog"], "description": "Generates the reviewed buzz and sine-fold audio voice."},
    {"key": "axoloti-factory:osc/brds/chaoticfeedbackfm", "id": 74, "name": "Chaotic Feedback FM Voice", "category": "sound-sources", "aliases": ["Braids Chaotic Feedback FM"], "tags": ["chaotic-modulation", "feedback-fm"], "description": "Generates the reviewed chaotic feedback-FM audio voice."},
    {"key": "axoloti-factory:osc/brds/clockednoise", "id": 75, "name": "Clocked Noise Voice", "category": "sound-sources", "aliases": ["Braids Clocked Noise"], "tags": ["clocked-noise", "noise"], "description": "Generates the reviewed clocked-noise audio voice."},
    {"key": "axoloti-factory:osc/brds/comb", "id": 76, "name": "Comb Swarm Voice", "category": "sound-sources", "aliases": ["Braids Comb"], "tags": ["comb-synthesis", "saw-swarm"], "description": "Generates the reviewed comb and saw-swarm audio voice."},
    {"key": "axoloti-factory:osc/brds/csaw sync", "id": 77, "name": "Synchronized CSAW Oscillator", "category": "sound-sources", "aliases": ["Braids CSAW Sync"], "tags": ["oscillator-sync", "virtual-analog"], "description": "Generates the reviewed synchronized CSAW virtual-analog waveform."},
    {"key": "axoloti-factory:osc/brds/csaw", "id": 78, "name": "CSAW Oscillator", "category": "sound-sources", "aliases": ["Braids CSAW"], "tags": ["csaw", "virtual-analog"], "description": "Generates the reviewed CSAW virtual-analog waveform."},
    {"key": "axoloti-factory:osc/brds/cymbal", "id": 79, "name": "Cymbal Voice", "category": "sound-sources", "aliases": ["Braids Cymbal"], "tags": ["cymbal", "percussion"], "description": "Generates the reviewed cymbal percussion voice."},
    {"key": "axoloti-factory:osc/brds/digitalmodulation", "id": 80, "name": "Digital Modulation Voice", "category": "sound-sources", "aliases": ["Braids Digital Modulation"], "tags": ["digital-modulation", "oscillator"], "description": "Generates the reviewed digitally modulated audio voice."},
    {"key": "axoloti-factory:osc/brds/feedbackfm", "id": 81, "name": "Feedback FM Voice", "category": "sound-sources", "aliases": ["Braids Feedback FM"], "tags": ["feedback-fm", "frequency-modulation"], "description": "Generates the reviewed feedback-FM audio voice."},
    {"key": "axoloti-factory:osc/brds/filtered", "id": 82, "name": "Digital Filter Voice", "category": "sound-sources", "aliases": ["Braids Digital Filter"], "tags": ["filtered-oscillator", "voice"], "description": "Generates the reviewed digital-filter audio voice."},
    {"key": "axoloti-factory:osc/brds/filterednoise", "id": 83, "name": "Filtered Noise Voice", "category": "sound-sources", "aliases": ["Braids Filtered Noise"], "tags": ["filtered-noise", "noise"], "description": "Generates the reviewed filtered-noise audio voice."},
    {"key": "axoloti-factory:osc/brds/fluted", "id": 84, "name": "Fluted Physical Voice", "category": "sound-sources", "aliases": ["Braids Fluted"], "tags": ["flute-voice", "physical-modeling"], "description": "Generates a fluted physical-model voice with pitch, timbre, color, and strike control."},
    {"key": "axoloti-factory:osc/brds/fm", "id": 85, "name": "FM Voice", "category": "sound-sources", "aliases": ["Braids FM"], "tags": ["frequency-modulation", "oscillator"], "description": "Generates the reviewed frequency-modulated audio voice."},
    {"key": "axoloti-factory:osc/brds/granularcloud", "id": 86, "name": "Granular Cloud Voice", "category": "sound-sources", "aliases": ["Braids Granular Cloud"], "tags": ["granular-synthesis", "noise-texture"], "description": "Generates the reviewed granular-cloud audio voice."},
    {"key": "axoloti-factory:osc/brds/harmonics", "id": 87, "name": "Harmonic Oscillator", "category": "sound-sources", "aliases": ["Braids Harmonics"], "tags": ["additive-synthesis", "harmonics"], "description": "Generates the reviewed harmonically structured audio voice."},
    {"key": "axoloti-factory:osc/brds/kick", "id": 88, "name": "Kick Voice", "category": "sound-sources", "aliases": ["Braids Kick"], "tags": ["kick", "percussion"], "description": "Generates the reviewed kick percussion voice."},
    {"key": "axoloti-factory:osc/brds/particlenoise", "id": 89, "name": "Particle Noise Voice", "category": "sound-sources", "aliases": ["Braids Particle Noise"], "tags": ["noise", "particle-texture"], "description": "Generates the reviewed particle-noise audio voice."},
    {"key": "axoloti-factory:osc/brds/plucked", "id": 90, "name": "Plucked Physical Voice", "category": "sound-sources", "aliases": ["Braids Plucked"], "tags": ["physical-modeling", "plucked-voice"], "description": "Generates a plucked physical-model voice with pitch, timbre, color, and strike control."},
    {"key": "axoloti-factory:osc/brds/questionmark", "id": 91, "name": "Question Mark Oscillator", "category": "sound-sources", "aliases": ["Braids Question Mark"], "tags": ["digital-oscillator", "voice"], "description": "Generates the reviewed Question Mark audio voice while retaining the source's opaque model name."},
    {"key": "axoloti-factory:osc/brds/sawswarm", "id": 92, "name": "Saw Swarm Voice", "category": "sound-sources", "aliases": ["Braids Saw Swarm"], "tags": ["saw-swarm", "virtual-analog"], "description": "Generates the reviewed detuned saw-swarm audio voice."},
    {"key": "axoloti-factory:osc/brds/sinefold", "id": 93, "name": "Sine-fold Oscillator", "category": "sound-sources", "aliases": ["Braids Sinefold"], "tags": ["sine-folding", "waveshaping"], "description": "Generates the reviewed sine-fold waveform."},
    {"key": "axoloti-factory:osc/brds/snare", "id": 94, "name": "Snare Voice", "category": "sound-sources", "aliases": ["Braids Snare"], "tags": ["percussion", "snare"], "description": "Generates the reviewed snare percussion voice."},
    {"key": "axoloti-factory:osc/brds/square", "id": 95, "name": "Square Oscillator", "category": "sound-sources", "aliases": ["Braids Square"], "tags": ["square-wave", "virtual-analog"], "description": "Generates the reviewed virtual-analog square waveform."},
    {"key": "axoloti-factory:osc/brds/toy", "id": 96, "name": "Toy Voice", "category": "sound-sources", "aliases": ["Braids Toy"], "tags": ["digital-oscillator", "toy-texture"], "description": "Generates the reviewed toy-oscillator audio voice."},
    {"key": "axoloti-factory:osc/brds/triangle", "id": 97, "name": "Triangle Oscillator", "category": "sound-sources", "aliases": ["Braids Triangle"], "tags": ["triangle-wave", "virtual-analog"], "description": "Generates the reviewed virtual-analog triangle waveform."},
    {"key": "axoloti-factory:osc/brds/trianglefold", "id": 98, "name": "Triangle-fold Oscillator", "category": "sound-sources", "aliases": ["Braids Triangle Fold"], "tags": ["triangle-folding", "waveshaping"], "description": "Generates the reviewed triangle-fold audio waveform; the retained source description calls it a square oscillator."},
    {"key": "axoloti-factory:osc/brds/tripleringmod", "id": 99, "name": "Triple Ring-modulation Voice", "category": "sound-sources", "aliases": ["Braids Triple Ring Mod"], "tags": ["ring-modulation", "voice"], "description": "Generates the reviewed triple ring-modulation audio voice."},
    {"key": "axoloti-factory:osc/brds/twinpeaksnoise", "id": 100, "name": "Twin-peaks Noise Voice", "category": "sound-sources", "aliases": ["Braids Twin Peaks Noise"], "tags": ["filtered-noise", "noise"], "description": "Generates the reviewed twin-peaks noise audio voice."},
    {"key": "axoloti-factory:osc/brds/vosim", "id": 101, "name": "VOSIM Voice", "category": "sound-sources", "aliases": ["Braids VOSIM"], "tags": ["formant-synthesis", "vosim"], "description": "Generates the reviewed VOSIM formant-synthesis audio voice."},
    {"key": "axoloti-factory:osc/brds/vowel", "id": 102, "name": "Vowel Voice", "category": "sound-sources", "aliases": ["Braids Vowel"], "tags": ["formant-synthesis", "vowel"], "description": "Generates the reviewed vowel audio voice."},
    {"key": "axoloti-factory:osc/brds/vowelfof", "id": 103, "name": "Vowel FOF Voice", "category": "sound-sources", "aliases": ["Braids Vowel FOF"], "tags": ["fof-synthesis", "formant-synthesis"], "description": "Generates the reviewed formant-wave-function vowel audio voice."},
    {"key": "axoloti-factory:osc/brds/vsaw", "id": 104, "name": "Variable Saw Oscillator", "category": "sound-sources", "aliases": ["Braids Variable Saw"], "tags": ["variable-saw", "virtual-analog"], "description": "Generates the reviewed variable-saw virtual-analog waveform."},
    {"key": "axoloti-factory:osc/brds/waveline", "id": 105, "name": "Waveline Voice", "category": "sound-sources", "aliases": ["Braids Waveline"], "tags": ["digital-oscillator", "waveline"], "description": "Generates the reviewed Waveline audio voice."},
    {"key": "axoloti-factory:osc/brds/wavemap", "id": 106, "name": "Wavemap Voice", "category": "sound-sources", "aliases": ["Braids Wavemap"], "tags": ["digital-oscillator", "wavemap"], "description": "Generates the reviewed Wavemap audio voice."},
    {"key": "axoloti-factory:osc/brds/wavetables", "id": 107, "name": "Wavetable Voice", "category": "sound-sources", "aliases": ["Braids Wavetables"], "tags": ["wavetable", "wavetable-synthesis"], "description": "Generates the reviewed wavetable audio voice."},
)

REUSED_FAMILIES = {
    "axoloti-factory:fx/lmnts/string": "schuss-family-000010",
    "axoloti-factory:fx/lmnts/tube": "schuss-family-000010",
    "axoloti-factory:osc/brds/saw": "schuss-family-000031",
}


def _canonical_bytes(value: Any) -> bytes:
    return core.canonical_json(value).encode("utf-8") + b"\n"


def _child(value: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(value)
    material = {key: item for key, item in result.items() if key != "content_hash"}
    result["content_hash"] = "sha256:" + hashlib.sha256(
        core.canonical_json(material).encode("utf-8")
    ).hexdigest()
    return result


def _record(value: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(value)
    result["content_hash"] = "sha256:" + "0" * 64
    errors = core.schema_errors(result, schema, schema)
    if errors:
        raise ValueError("; ".join(errors))
    result["content_hash"] = core.record_content_hash(result, schema)
    return result


def _generic_ref(record: dict[str, Any], field: str) -> dict[str, Any]:
    return {
        "stable_id": record[field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def _source_key(entry: dict[str, Any]) -> str:
    value = entry["stable_source_id"]
    return value.split("@", 1)[0] if value.startswith("axoloti-factory:") else value


def _family_specs() -> dict[str, dict[str, Any]]:
    result = {item["key"]: item for item in NEW_FAMILY_SPECS}
    expected_ids = list(range(61, 108))
    if len(result) != 47 or sorted(item["id"] for item in result.values()) != expected_ids:
        raise ValueError("Task 030 new-family allocation must be exact IDs 61-107")
    if set(result) & set(REUSED_FAMILIES):
        raise ValueError("Task 030 family allocation is duplicated")
    return result


def _candidate_variants() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for candidate in core.load_jsonl(TASK024_CANDIDATES):
        for variant in candidate["variants"]:
            result[variant["variant_ref"]] = variant
    return result


def _factory_authority(
    entry: dict[str, Any],
    variant: dict[str, Any],
    observations: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if entry["stable_source_id"] != variant["variant_ref"]:
        raise ValueError("Task 030 factory review identity is stale")
    if len(variant["frozen_lineage_refs"]) != 1:
        raise ValueError("Task 030 factory candidate must resolve one frozen observation")
    evidence_ref = variant["frozen_lineage_refs"][0]
    observation = observations.get(evidence_ref)
    if observation is None:
        raise ValueError("Task 030 factory observation is absent")
    origin = observation["origin"]
    object_path = next(item for item in entry["source_paths"] if item["role"] == "object")
    if (
        object_path["portable_path"] != variant["source_path"]
        or object_path["byte_sha256"] != variant["source_sha256"]
        or origin["path"] != variant["source_path"]
        or origin["sha256"] != variant["source_sha256"]
        or observation["uuid"]["durable_value"] != variant["legacy_uuid"]
    ):
        raise ValueError("Task 030 factory source closure is stale")
    source = {
        "evidence_ref": evidence_ref,
        "canonical_observation_sha256": hashlib.sha256(
            core.canonical_json(observation).encode("utf-8")
        ).hexdigest(),
        "source_id": origin["source_id"],
        "source_path": origin["path"],
        "source_sha256": origin["sha256"],
        "legacy_id": observation["legacy_id"],
        "legacy_uuid_sha256": "sha256:" + hashlib.sha256(
            observation["uuid"]["durable_value"].encode("utf-8")
        ).hexdigest(),
    }
    return {"kind": "legacy-observation", "observation": source}


def _extended_authority(entry: dict[str, Any]) -> dict[str, Any]:
    paths = {item["role"]: item for item in entry["source_paths"]}
    required = {"manifest", "object", "license"}
    if not required <= set(paths) or entry["commit"] != PATCHER_COMMIT:
        raise ValueError("Task 030 extended source closure is stale")
    return {
        "kind": "pinned-source-object",
        "source_id": "patcher",
        "commit": PATCHER_COMMIT,
        "evidence_ref": entry["entry_id"],
        "stable_source_id": entry["stable_source_id"],
        "manifest_path": paths["manifest"]["portable_path"],
        "manifest_sha256": paths["manifest"]["byte_sha256"],
        "object_path": paths["object"]["portable_path"],
        "object_sha256": paths["object"]["byte_sha256"],
        "license_path": paths["license"]["portable_path"],
        "license_sha256": paths["license"]["byte_sha256"],
        "declared_license": entry["declared_license"],
    }


def _source_authority(
    entry: dict[str, Any],
    variants: dict[str, dict[str, Any]],
    observations: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if entry["source_kind"] == "extended-object":
        return _extended_authority(entry)
    variant = variants.get(entry["stable_source_id"])
    if variant is None:
        raise ValueError("Task 030 factory candidate is absent")
    return _factory_authority(entry, variant, observations)


def _source_review_schema() -> dict[str, Any]:
    schema = copy.deepcopy(core.load_json(ROOT / "schemas/catalog-source-review-v0.schema.json"))
    schema["$id"] = "catalog-source-review-v1.schema.json"
    schema["title"] = "Schuss complete Mutable-derived catalog source review v1"
    properties = schema["properties"]
    properties["schema_version"]["const"] = "catalog-source-review-v1"
    properties["revision"]["const"] = 2
    properties["decision_record"]["properties"]["portable_path"]["const"] = "contracts/task030/mutable-catalog-curation.md"
    properties["review_artifact"]["properties"]["portable_path"]["const"] = "catalog/reviews/task030-mutable-catalog-v1/entries.jsonl"
    counts = properties["counts"]["properties"]
    counts["catalogued_implementations"]["const"] = 56
    counts["tagged_candidates"]["const"] = 0
    properties["parent_review_reference"] = {
        "type": "object",
        "additionalProperties": False,
        "required": ["stable_id", "revision", "content_hash"],
        "properties": {
            "stable_id": {"const": "schuss-catalog-source-review-000001"},
            "revision": {"const": 1},
            "content_hash": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
        },
    }
    properties["completion_policy"] = {
        "const": "all-exact-task027-attributed-entries-catalogued-no-support-inference"
    }
    schema["required"].extend(["parent_review_reference", "completion_policy"])
    return schema


def _catalog_schemas() -> tuple[dict[str, Any], dict[str, Any]]:
    corpus = copy.deepcopy(core.load_json(ROOT / "schemas/catalog-corpus-v4.schema.json"))
    corpus["$id"] = "catalog-corpus-v5.schema.json"
    corpus["title"] = "Schuss complete Mutable-derived catalog corpus v5"
    corpus["properties"]["schema_version"]["const"] = "catalog-corpus-v5"
    corpus["properties"]["revision"]["const"] = 5
    corpus["properties"]["projection_version"]["const"] = "schuss-catalog-projection-v5"
    corpus["$defs"]["catalogReference"]["properties"]["revision"]["const"] = 4
    corpus["properties"]["family_additions"]["minItems"] = 81
    corpus["properties"]["family_additions"]["maxItems"] = 81
    corpus["properties"]["implementation_additions"]["minItems"] = 95
    corpus["properties"]["implementation_additions"]["maxItems"] = 95
    for definition in ("familyAddition", "implementationAddition"):
        review_status = corpus["$defs"][definition]["properties"]["review_status"]
        if "enum" in review_status:
            review_status["enum"].append("task030-reviewed")
            review_status["enum"].sort()
    tags = corpus["properties"]["mutable_instruments_review"]["properties"]["implementation_tags"]
    tags["minItems"] = 56
    tags["maxItems"] = 56
    corpus["properties"]["mutable_instruments_review"]["properties"]["completion_state"] = {
        "const": "56-attributed-entries-catalogued"
    }
    corpus["properties"]["mutable_instruments_review"]["required"].append("completion_state")

    projection = copy.deepcopy(core.load_json(ROOT / "schemas/catalog-projection-v4.schema.json"))
    projection["$id"] = "catalog-projection-v5.schema.json"
    projection["title"] = "Schuss complete Mutable-derived catalog projection v5"
    projection["properties"]["schema_version"]["const"] = "catalog-projection-v5"
    projection["properties"]["projection_version"]["const"] = "schuss-catalog-projection-v5"
    projection["properties"]["catalog_reference"]["$ref"] = "#/$defs/catalogReference"
    projection["$defs"]["catalogReference"]["properties"]["revision"]["const"] = 5
    projection["properties"]["families"]["minItems"] = 107
    projection["properties"]["families"]["maxItems"] = 107
    return corpus, projection


def _operation_schemas() -> tuple[dict[str, Any], dict[str, Any]]:
    v2 = core.load_json(ROOT / "schemas/operation-request-v2.schema.json")
    request = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "operation-request-v10.schema.json",
        "title": "Schuss catalog implementation-object search request v10",
        "type": "object",
        "additionalProperties": False,
        "required": ["schema_version", "canonical_profile", "operation", "payload"],
        "properties": {
            "schema_version": {"const": "schuss-operation-request-v10"},
            "canonical_profile": {"const": "schuss-canonical-json-v1"},
            "operation": {"const": "catalog.implementations.search"},
            "payload": {
                "type": "object",
                "additionalProperties": False,
                "required": ["query", "filters"],
                "properties": {
                    "query": {"type": "string"},
                    "filters": {"$ref": "#/$defs/filters"},
                },
            },
        },
        "$defs": {
            "filters": copy.deepcopy(v2["$defs"]["filters"]),
            "stringSet": copy.deepcopy(v2["$defs"]["stringSet"]),
        },
    }
    result = copy.deepcopy(core.load_json(ROOT / "schemas/operation-result-v9.schema.json"))
    result["$id"] = "operation-result-v10.schema.json"
    result["title"] = "Schuss catalog implementation-object search result v10"
    result["properties"]["schema_version"]["const"] = "schuss-operation-result-v10"
    result["properties"]["operation"]["enum"] = [
        "catalog.implementations.search",
        "invalid-request",
    ]
    return request, result


def _application_schema() -> dict[str, Any]:
    schema = copy.deepcopy(core.load_json(ROOT / "schemas/application-capability-description-v2.schema.json"))
    schema["$id"] = "application-capability-description-v3.schema.json"
    schema["title"] = "Schuss application capability description v3"
    schema["properties"]["schema_version"]["const"] = "application-capability-description-v3"
    schema["properties"]["description_version"]["const"] = "schuss-application-capability-description-v3"
    operations = schema["properties"]["operations"]
    operations["minItems"] = 20
    operations["maxItems"] = 20
    capability = schema["$defs"]["operationCapability"]["properties"]
    capability["operation"]["enum"].append("catalog.implementations.search")
    capability["operation"]["enum"].sort()
    capability["request_schema_version"]["pattern"] = "^schuss-operation-request-v(?:[1-9]|10)$"
    capability["result_schema_version"]["pattern"] = "^schuss-operation-result-v(?:[1-9]|10)$"
    return schema


def schemas() -> dict[str, dict[str, Any]]:
    corpus, projection = _catalog_schemas()
    request, result = _operation_schemas()
    return {
        "catalog-source-review-v1": _source_review_schema(),
        "catalog-corpus-v5": corpus,
        "catalog-projection-v5": projection,
        "operation-request-v10": request,
        "operation-result-v10": result,
        "application-capability-description-v3": _application_schema(),
    }


def _successor_review(
    parent: dict[str, Any],
    candidates: list[dict[str, Any]],
    family_by_entry: dict[str, tuple[str, str]],
    implementation_by_entry: dict[str, str],
    schema: dict[str, Any],
) -> tuple[dict[str, Any], bytes]:
    entries = copy.deepcopy(parent["entries"])
    candidate_ids = {item["entry_id"] for item in candidates}
    for entry in entries:
        if entry["entry_id"] not in candidate_ids:
            continue
        family_id, category = family_by_entry[entry["entry_id"]]
        entry["functional_category"] = category
        entry["disposition"] = "catalogued-new-implementation"
        entry["disposition_rationale"] = (
            "Task 030 assigns one exact function-first family and catalog implementation; "
            "Mutable ancestry remains a separate provenance facet and establishes no support."
        )
        entry["catalog_implementation_id"] = implementation_by_entry[entry["entry_id"]]
        if family_id == "schuss-family-000010":
            entry["disposition_rationale"] = (
                "The exact Elements-derived string or tube source is a concrete physical-resonator "
                "variant of the accepted family; catalog membership establishes no support."
            )
        elif family_id == "schuss-family-000031":
            entry["disposition_rationale"] = (
                "The exact Braids saw source is a concrete band-limited audio-saw implementation "
                "of the accepted family; catalog membership establishes no support."
            )
    entries.sort(key=lambda item: item["entry_id"])
    review_bytes = b"".join(_canonical_bytes(item) for item in entries)
    result = copy.deepcopy(parent)
    result.update(
        {
            "schema_version": "catalog-source-review-v1",
            "revision": 2,
            "parent_review_reference": _generic_ref(parent, "catalog_source_review_id"),
            "completion_policy": "all-exact-task027-attributed-entries-catalogued-no-support-inference",
            "decision_record": {
                "portable_path": "contracts/task030/mutable-catalog-curation.md",
                "byte_sha256": core.sha256_file(DECISION),
            },
            "review_artifact": {
                "portable_path": "catalog/reviews/task030-mutable-catalog-v1/entries.jsonl",
                "byte_sha256": hashlib.sha256(review_bytes).hexdigest(),
                "record_count": 72,
            },
            "entries": entries,
            "counts": {
                "total": 72,
                "extended": 19,
                "factory": 53,
                "tagged": 56,
                "inventory_only": 16,
                "catalogued_implementations": 56,
                "tagged_candidates": 0,
            },
        }
    )
    result.pop("content_hash", None)
    return _record(result, schema), review_bytes


def _catalog(
    parent: dict[str, Any],
    parent_projection: dict[str, Any],
    parent_review: dict[str, Any],
    review: dict[str, Any],
    variants: dict[str, dict[str, Any]],
    observations: dict[str, dict[str, Any]],
    schema: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, tuple[str, str]], dict[str, str]]:
    candidates = [
        item for item in parent_review["entries"]
        if item["disposition"] == "tagged-candidate"
    ]
    candidates.sort(key=lambda item: item["entry_id"])
    if len(candidates) != 50:
        raise ValueError("Task 030 requires exactly 50 former tagged candidates")
    family_specs = _family_specs()
    candidate_keys = {_source_key(item) for item in candidates}
    if candidate_keys != set(family_specs) | set(REUSED_FAMILIES):
        raise ValueError("Task 030 family decision table does not cover the exact candidates")
    parent_family_refs = {
        item["family_reference"]["family_id"]: item["family_reference"]
        for item in parent_projection["families"]
    }
    family_records: dict[str, dict[str, Any]] = {}
    authority_by_entry = {
        item["entry_id"]: _source_authority(item, variants, observations)
        for item in candidates
    }
    for entry in candidates:
        key = _source_key(entry)
        spec = family_specs.get(key)
        if spec is None:
            continue
        rationale = (
            "The exact Task 027 source identity, description, and object signature support this "
            "function-first catalog family; Mutable ancestry remains provenance only."
        )
        family = _child(
            {
                "family_id": f"schuss-family-{spec['id']:06d}",
                "revision": 1,
                "display_name": spec["name"],
                "aliases": sorted(spec["aliases"]),
                "description": spec["description"],
                "primary_category": spec["category"],
                "secondary_function_tags": sorted(spec["tags"]),
                "abstraction_level": "primitive",
                "classification_confidence": "high",
                "classification_rationale": rationale,
                "source_authority": copy.deepcopy(authority_by_entry[entry["entry_id"]]),
                "review_status": "task030-reviewed",
                "unresolved_questions": [
                    "Catalog review does not establish a component contract, binding, compiler support, target compatibility, device behavior, real-time behavior, or audible behavior."
                ],
            }
        )
        family_records[key] = family

    family_by_entry: dict[str, tuple[str, str]] = {}
    implementation_by_entry: dict[str, str] = {}
    additions: list[dict[str, Any]] = []
    for offset, entry in enumerate(candidates, 112):
        key = _source_key(entry)
        if key in REUSED_FAMILIES:
            family_id = REUSED_FAMILIES[key]
            family_ref = parent_family_refs[family_id]
            category = next(
                item["primary_function"] for item in parent_projection["families"]
                if item["family_reference"]["family_id"] == family_id
            )
        else:
            family = family_records[key]
            family_id = family["family_id"]
            family_ref = {
                "family_id": family_id,
                "revision": family["revision"],
                "content_hash": family["content_hash"],
            }
            category = family_specs[key]["category"]
        implementation_id = f"schuss-implementation-{offset:06d}"
        family_by_entry[entry["entry_id"]] = (family_id, category)
        implementation_by_entry[entry["entry_id"]] = implementation_id
        display = (
            "Elements string resonator implementation"
            if key == "axoloti-factory:fx/lmnts/string"
            else "Elements tube resonator implementation"
            if key == "axoloti-factory:fx/lmnts/tube"
            else "Braids saw oscillator implementation"
            if key == "axoloti-factory:osc/brds/saw"
            else f"{family_specs[key]['name']} source implementation"
        )
        known = entry["known_source_limitations"]
        unresolved = [
            "No exact component contract, binding, backend eligibility, source artifact, ARM result, device, real-time, or audible evidence is established by Task 030."
        ]
        if known:
            unresolved.extend(f"Retained source limitation: {value}" for value in known)
        if entry["source_manifest_metadata"] is not None:
            unresolved.append(
                "Source manifest compatibility and build fields are not Schuss compiler or target evidence."
            )
        additions.append(
            _child(
                {
                    "implementation_id": implementation_id,
                    "revision": 1,
                    "family_reference": copy.deepcopy(family_ref),
                    "display_name": display,
                    "form": "native-object",
                    "review_status": "task030-reviewed",
                    "membership_confidence": "high",
                    "membership_rationale": (
                        "The exact source object is assigned to its reviewed function-first family; "
                        "provenance is neither family identity nor a support claim."
                    ),
                    "source_authority": copy.deepcopy(authority_by_entry[entry["entry_id"]]),
                    "compatibility_status": "not-evaluated",
                    "unresolved_questions": sorted(unresolved),
                }
            )
        )
    if sorted(implementation_by_entry.values()) != [
        f"schuss-implementation-{value:06d}" for value in range(112, 162)
    ]:
        raise ValueError("Task 030 implementation allocation is not exact")

    result = copy.deepcopy(parent)
    result.update(
        {
            "schema_version": "catalog-corpus-v5",
            "revision": 5,
            "projection_version": "schuss-catalog-projection-v5",
            "parent_corpus_reference": {
                "catalog_id": parent["catalog_id"],
                "revision": parent["revision"],
                "content_hash": parent["content_hash"],
            },
        }
    )
    result["family_additions"].extend(family_records.values())
    result["family_additions"].sort(key=lambda item: item["family_id"])
    result["implementation_additions"].extend(additions)
    result["implementation_additions"].sort(key=lambda item: item["implementation_id"])

    review_entries = {
        item["catalog_implementation_id"]: item
        for item in review["entries"]
        if MUTABLE_TAG in item["provenance_tags"]
    }
    if len(review_entries) != 56 or None in review_entries:
        raise ValueError("Task 030 successor review must map all 56 attributed entries")
    result["mutable_instruments_review"] = {
        "source_review_reference": _generic_ref(review, "catalog_source_review_id"),
        "tag_policy": "exact-source-attribution-only-no-path-or-inspiration-inference",
        "completion_state": "56-attributed-entries-catalogued",
        "implementation_tags": sorted(
            [
                {
                    "implementation_id": identifier,
                    "tag_id": MUTABLE_TAG,
                    "source_entry_id": entry["entry_id"],
                }
                for identifier, entry in review_entries.items()
            ],
            key=core.canonical_json,
        ),
    }
    result.pop("content_hash", None)
    return _record(result, schema), family_by_entry, implementation_by_entry


def generated() -> tuple[dict[str, bytes], bytes, dict[str, Any], dict[str, Any]]:
    parent_manifest = core.load_json(PARENT)
    parent_context = load_repository_context(record_set_path=PARENT)
    parent_catalog = parent_context.records["catalog"][0]
    if parent_catalog["schema_version"] != "catalog-corpus-v4":
        raise ValueError("Task 030 parent does not select exact catalog v4")
    parent_review = core.load_json(TASK027_REVIEW)
    candidates = [
        item for item in parent_review["entries"]
        if item["disposition"] == "tagged-candidate"
    ]
    variants = _candidate_variants()
    schema_values = schemas()
    for name, schema in schema_values.items():
        annotations = core.validate_schema_annotations(schema)
        if annotations:
            raise ValueError(f"Task 030 schema {name} is invalid: {annotations}")

    family_specs = _family_specs()
    family_by_entry: dict[str, tuple[str, str]] = {}
    implementation_by_entry: dict[str, str] = {}
    for offset, entry in enumerate(sorted(candidates, key=lambda item: item["entry_id"]), 112):
        key = _source_key(entry)
        if key in REUSED_FAMILIES:
            family_id = REUSED_FAMILIES[key]
            category = (
                "filters-resonators"
                if family_id == "schuss-family-000010"
                else "sound-sources"
            )
        else:
            family_id = f"schuss-family-{family_specs[key]['id']:06d}"
            category = family_specs[key]["category"]
        family_by_entry[entry["entry_id"]] = (family_id, category)
        implementation_by_entry[entry["entry_id"]] = (
            f"schuss-implementation-{offset:06d}"
        )
    review, review_bytes = _successor_review(
        parent_review,
        candidates,
        family_by_entry,
        implementation_by_entry,
        schema_values["catalog-source-review-v1"],
    )
    catalog, family_by_entry, implementation_by_entry = _catalog(
        parent_catalog,
        parent_context.catalog_projection,
        parent_review,
        review,
        variants,
        dict(parent_context.observations),
        schema_values["catalog-corpus-v5"],
    )
    selector = _record(
        {
            "schema_version": "catalog-selection-v0",
            "canonical_profile": "schuss-canonical-json-v1",
            "catalog_selection_id": "schuss-catalog-selection-000001",
            "revision": 4,
            "corpus_reference": {
                "catalog_id": catalog["catalog_id"],
                "revision": catalog["revision"],
                "content_hash": catalog["content_hash"],
            },
            "rationale": "Select the exact Task 030 catalog in which all 56 Task 027 attributed entries are catalogued without support inference.",
        },
        core.load_json(ROOT / "schemas/catalog-selection-v0.schema.json"),
    )

    files: dict[str, bytes] = {
        f"schemas/{name}.schema.json": _canonical_bytes(schema)
        for name, schema in schema_values.items()
    }
    records = {
        "contracts/task030/catalog-source-review-r2.json": review,
        "contracts/task030/catalog-corpus-v5.json": catalog,
        "contracts/task030/catalog-selection-r4.json": selector,
    }
    files.update({path: _canonical_bytes(record) for path, record in records.items()})
    files["catalog/reviews/task030-mutable-catalog-v1/entries.jsonl"] = review_bytes

    schema_members = copy.deepcopy(parent_manifest["schema_members"])
    existing_schemas = {item["schema_version"] for item in schema_members}
    for name in sorted(schema_values):
        if name in existing_schemas:
            raise ValueError(f"Task 030 schema version collides with parent: {name}")
        path = f"schemas/{name}.schema.json"
        schema_members.append(
            {
                "schema_version": name,
                "portable_path": path,
                "byte_sha256": hashlib.sha256(files[path]).hexdigest(),
            }
        )

    record_members = copy.deepcopy(parent_manifest["record_members"])
    for kind, record, field, path in (
        ("catalog-source-review", review, "catalog_source_review_id", "contracts/task030/catalog-source-review-r2.json"),
        ("catalog-corpus", catalog, "catalog_id", "contracts/task030/catalog-corpus-v5.json"),
        ("catalog-selection", selector, "catalog_selection_id", "contracts/task030/catalog-selection-r4.json"),
    ):
        record_members.append(
            {
                "record_kind": kind,
                "stable_id": record[field],
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
        "record_set_id": "schuss-record-set-000023",
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "purpose": "prospective-task",
        "parent_reference": {
            "status": "included",
            **{
                key: parent_manifest[key]
                for key in ("record_set_id", "revision", "content_hash")
            },
        },
        "schema_members": sorted(
            schema_members, key=lambda item: (item["byte_sha256"], item["portable_path"])
        ),
        "record_members": sorted(
            record_members, key=lambda item: (item["byte_sha256"], item["portable_path"])
        ),
        "enforced_directories": sorted(
            set(parent_manifest["enforced_directories"]) | {"contracts/task030"}
        ),
    }
    errors = core.schema_errors(manifest, manifest_schema, manifest_schema)
    if errors:
        raise ValueError("; ".join(errors))
    manifest["content_hash"] = core.record_content_hash(manifest, manifest_schema)

    projection_records = dict(parent_context.records)
    projection_records["catalog_source_reviews"] = tuple(
        [*parent_context.records.get("catalog_source_reviews", ()), review]
    )
    projection = catalog_projection.build_catalog_projection(
        corpus=copy.deepcopy(catalog),
        corpus_schema=schema_values["catalog-corpus-v5"],
        projection_schema=schema_values["catalog-projection-v5"],
        overlay=copy.deepcopy(parent_context.overlay),
        overlay_sha256=parent_context.overlay_sha256,
        observations=copy.deepcopy(parent_context.observations),
        records=projection_records,
        record_set_reference={
            key: manifest[key] for key in ("record_set_id", "revision", "content_hash")
        },
        core=core,
    )
    implementations = [
        implementation
        for family in projection["families"]
        for implementation in family["implementations"]
    ]
    tagged = [
        item for item in implementations
        if MUTABLE_TAG in item.get("provenance_tags", ())
    ]
    summary = {
        "schema_version": "task030-validation-summary-v1",
        "status": "valid",
        "record_set_reference": {
            key: manifest[key] for key in ("record_set_id", "revision", "content_hash")
        },
        "source_review_count": 72,
        "mutable_attributed_entry_count": 56,
        "unattributed_inventory_only_count": 16,
        "new_family_count": 47,
        "catalog_family_count": len(projection["families"]),
        "new_implementation_count": 50,
        "catalog_implementation_count": len(implementations),
        "mutable_catalog_implementation_count": len(tagged),
        "projection_sha256": hashlib.sha256(_canonical_bytes(projection)).hexdigest(),
        "evidence_levels": [
            {"level": level, "status": "passed" if level <= 2 else "not-run"}
            for level in range(1, 9)
        ],
        "compiler_or_build_performed": False,
        "project_or_machine_mutation_performed": False,
        "hardware_or_publication_performed": False,
    }
    if (
        summary["catalog_family_count"] != 107
        or summary["catalog_implementation_count"] != 133
        or summary["mutable_catalog_implementation_count"] != 56
    ):
        raise ValueError("Task 030 catalog completion counts are stale")
    files["evidence/task030-completion-v1/validation-summary.json"] = _canonical_bytes(summary)
    return files, _canonical_bytes(manifest), summary, projection


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        files, manifest, summary, _ = generated()
        expected = {**files, OUTPUT.relative_to(ROOT).as_posix(): manifest}
        stale = [
            path for path, payload in expected.items()
            if not (ROOT / path).is_file() or (ROOT / path).read_bytes() != payload
        ]
        if args.check and stale:
            raise ValueError("Task 030 generated outputs are stale: " + ", ".join(sorted(stale)))
        if not args.check:
            for relative, payload in expected.items():
                path = ROOT / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
    except (OSError, ValueError, KeyError, StopIteration) as exc:
        print("Task 030 generation failed: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
