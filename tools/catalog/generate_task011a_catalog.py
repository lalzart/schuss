#!/usr/bin/env python3
"""Generate the exact Task 011A catalog corpus and parent-preserving record set."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_TOOLS = ROOT / "tools/contracts"
if str(CONTRACT_TOOLS) not in sys.path:
    sys.path.insert(0, str(CONTRACT_TOOLS))

import validator_core as core


OVERLAY_PATH = ROOT / "catalog/overlays/phase-4a-semantic-catalog-v0/catalog.json"
OBJECTS_PATH = ROOT / "catalog/snapshots/legacy-resolved-catalog-v0/resolved/objects.jsonl"
CORPUS_PATH = ROOT / "contracts/catalog/task011a-corpus-v1.json"
CORPUS_SCHEMA_PATH = ROOT / "schemas/catalog-corpus-v1.schema.json"
PARENT_PATH = ROOT / "contracts/record-sets/task009-executed-prospective-v0.json"
RECORD_SET_PATH = ROOT / "contracts/record-sets/task011a-catalog-v1.json"
RECORD_SET_SCHEMA_PATH = ROOT / "schemas/prerequisite/record-set-v0.schema.json"


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(core.canonical_json(value) + "\n", encoding="utf-8")


def _child_hash(value: dict[str, Any]) -> str:
    material = copy.deepcopy(value)
    material.pop("content_hash", None)
    return "sha256:" + hashlib.sha256(
        core.canonical_json(material).encode("utf-8")
    ).hexdigest()


def _observations() -> dict[int, dict[str, Any]]:
    values: dict[int, dict[str, Any]] = {}
    with OBJECTS_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            values[record["variant_index"]] = record
    return values


def _observation_source(
    observations: dict[int, dict[str, Any]], index: int
) -> dict[str, Any]:
    record = observations[index]
    origin = record["origin"]
    return {
        "evidence_ref": f"legacy-resolved-catalog-v0:object:{index}",
        "canonical_observation_sha256": hashlib.sha256(
            core.canonical_json(record).encode("utf-8")
        ).hexdigest(),
        "source_id": origin["source_id"],
        "source_path": origin["path"],
        "source_sha256": origin["sha256"],
        "legacy_id": record["legacy_id"],
        "legacy_uuid": record["uuid"]["durable_value"],
    }


def _family_addition(
    observations: dict[int, dict[str, Any]],
    *,
    family_id: str,
    display_name: str,
    aliases: list[str],
    description: str,
    primary_category: str,
    tags: list[str],
    rationale: str,
    observation_index: int,
) -> dict[str, Any]:
    value = {
        "family_id": family_id,
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "display_name": display_name,
        "aliases": aliases,
        "description": description,
        "primary_category": primary_category,
        "secondary_function_tags": tags,
        "abstraction_level": "primitive",
        "review_status": "slice-reviewed",
        "classification_confidence": "high",
        "classification_rationale": rationale,
        "source_observation": _observation_source(observations, observation_index),
        "unresolved_questions": [
            "Target-independent component contract and backend compatibility remain unestablished."
        ],
    }
    value["content_hash"] = _child_hash(value)
    return value


def _implementation_addition(
    observations: dict[int, dict[str, Any]],
    *,
    implementation_id: str,
    family: dict[str, Any],
    display_name: str,
    form: str,
    observation_index: int,
    rationale: str,
    unresolved: list[str],
) -> dict[str, Any]:
    value = {
        "implementation_id": implementation_id,
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "family_reference": {
            "family_id": family["family_id"],
            "revision": family["revision"],
            "content_hash": family["content_hash"],
        },
        "display_name": display_name,
        "form": form,
        "source_observation": _observation_source(observations, observation_index),
        "review_status": "slice-reviewed",
        "membership_confidence": "high",
        "membership_rationale": rationale,
        "compatibility_status": "not-evaluated",
        "unresolved_questions": unresolved,
    }
    value["content_hash"] = _child_hash(value)
    return value


def build_corpus() -> dict[str, Any]:
    overlay = core.load_json(OVERLAY_PATH)
    observations = _observations()
    companions = []
    for family in overlay["families"]:
        if family["family_id"] == "schuss-family-000018":
            continue
        override = None
        changed = False
        rationale = (
            "The Task 011A companion adds an exact revision and content-hash "
            "envelope without changing the retained Phase 4A family member."
        )
        if family["family_id"] == "schuss-family-000022":
            override = {
                "display_name": "Pitch Step Sequencer",
                "aliases": ["16-step Pitch Sequencer", "Pitch Sequencer"],
                "description": (
                    "Selects parameterized pitch steps from an incoming integer "
                    "step index; reviewed realizations may expose different fixed "
                    "step counts."
                ),
            }
            changed = True
            rationale = (
                "The stable family continues to mean clock/index-driven pitch-step "
                "sequencing. The successor presentation removes the accidental "
                "sixteen-step realization count from the family name so the distinct "
                "four-step observation can join without reusing implementation identity."
            )
        entry = {
            "family_id": family["family_id"],
            "revision": 1,
            "content_hash": "sha256:" + "0" * 64,
            "canonical_member_sha256": hashlib.sha256(
                core.canonical_json(family).encode("utf-8")
            ).hexdigest(),
            "semantics_changed": changed,
            "presentation_override": override,
            "rationale": rationale,
        }
        entry["content_hash"] = _child_hash(entry)
        companions.append(entry)

    square = _family_addition(
        observations,
        family_id="schuss-family-000027",
        display_name="Square LFO",
        aliases=["Square Clock", "Low-frequency Square"],
        description="Generates a cyclic Boolean square wave for modulation or clocking.",
        primary_category="modulation-control",
        tags=["clock-generation", "low-frequency-modulation"],
        rationale=(
            "Observation 209 explicitly describes a Boolean-output square-wave LFO. "
            "Its primary discovery function is low-frequency modulation; clock use "
            "remains a controlled secondary technique."
        ),
        observation_index=209,
    )
    counter = _family_addition(
        observations,
        family_id="schuss-family-000028",
        display_name="Cyclic Counter",
        aliases=["Step Counter", "Up Counter"],
        description="Advances an integer count on rising triggers and wraps at a configured maximum.",
        primary_category="timing-sequencing",
        tags=["algorithmic-sequencing"],
        rationale=(
            "Observation 215 is explicitly a cyclic up counter driven by rising "
            "triggers; ordered step progression is its primary musical use."
        ),
        observation_index=215,
    )
    family_22 = next(
        entry for entry in companions if entry["family_id"] == "schuss-family-000022"
    )
    implementations = [
        _implementation_addition(
            observations,
            implementation_id="schuss-implementation-000039",
            family=square,
            display_name="Generated Boolean square LFO",
            form="generated-object",
            observation_index=209,
            rationale="The observation is the reviewed concrete square-LFO realization.",
            unresolved=[
                "Boolean edge semantics require an exact Task 011B component contract.",
                "Target/backend compatibility is not evaluated.",
            ],
        ),
        _implementation_addition(
            observations,
            implementation_id="schuss-implementation-000040",
            family=counter,
            display_name="Generated cyclic up counter",
            form="generated-object",
            observation_index=215,
            rationale="The observation is the reviewed concrete cyclic-counting realization.",
            unresolved=[
                "Counter bound and rising-edge semantics require an exact Task 011B component contract.",
                "Target/backend compatibility is not evaluated.",
            ],
        ),
        _implementation_addition(
            observations,
            implementation_id="schuss-implementation-000041",
            family=family_22,
            display_name="Community four-step pitch sequencer",
            form="native-object",
            observation_index=918,
            rationale=(
                "Observation 918 exposes an integer step selector, four pitch "
                "parameters, chain output, and pitch output. It shares the reviewed "
                "pitch-step-sequencing function but is not the sixteen-step realization."
            ),
            unresolved=[
                "The shared source file contains multiple distinct definitions; a later binding must pin definition index, UUID, and seams exactly.",
                "Target/backend compatibility is not evaluated.",
            ],
        ),
    ]
    roles = [
        (
            "Square LFO", "schuss-family-000027", "schuss-implementation-000039",
            209, "Allocated a new family and implementation after exact observation review."
        ),
        (
            "Cyclic Counter", "schuss-family-000028", "schuss-implementation-000040",
            215, "Allocated a new family and implementation after exact observation review."
        ),
        (
            "four-step Pitch Sequencer", "schuss-family-000022",
            "schuss-implementation-000041", 918,
            "Reused the pitch-step-sequencing family through an explicit successor presentation and allocated a distinct implementation."
        ),
        (
            "Sine Oscillator", "schuss-family-000003", "schuss-implementation-000007",
            549, "Reused the accepted Phase 4A family and implementation."
        ),
        (
            "Crossfader", "schuss-family-000018", "schuss-implementation-000028",
            460, "Reused the accepted Task 006/009 exact family, contract, binding, eligibility, and evidence chain."
        ),
        (
            "State-variable Filter", "schuss-family-000009",
            "schuss-implementation-000015", 159,
            "Reused the accepted Phase 4A family and implementation."
        ),
        (
            "stereo Audio Output", "schuss-family-000002",
            "schuss-implementation-000004", 9,
            "Reused the accepted Phase 4A family and implementation."
        ),
    ]
    corpus = {
        "schema_version": "catalog-corpus-v1",
        "canonical_profile": "schuss-canonical-json-v1",
        "catalog_id": "schuss-catalog-000001",
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "projection_version": "schuss-catalog-projection-v1",
        "match_algorithm": "schuss-catalog-match-v1",
        "overlay_source": {
            "overlay_id": overlay["overlay_id"],
            "schema_version": overlay["schema_version"],
            "portable_path": OVERLAY_PATH.relative_to(ROOT).as_posix(),
            "byte_sha256": core.sha256_file(OVERLAY_PATH),
            "legacy_manifest_sha256": overlay["legacy_evidence"]["manifest_sha256"],
        },
        "family_companions": companions,
        "family_additions": [square, counter],
        "implementation_additions": implementations,
        "slice_review": {
            "review_id": "schuss-gills-slice-review-000001",
            "roles": [
                {
                    "role": role,
                    "family_id": family_id,
                    "implementation_id": implementation_id,
                    "evidence_ref": f"legacy-resolved-catalog-v0:object:{index}",
                    "identity_decision": decision,
                    "later_binding_status": "not-established",
                }
                for role, family_id, implementation_id, index, decision in roles
            ],
            "observation_918_identity_warning": (
                "Observation 918 is the four-step realization and receives "
                "schuss-implementation-000041. schuss-implementation-000032 remains "
                "the distinct sixteen-step observation 920."
            ),
            "later_proof_gaps": [
                "Six target-independent component contracts and exact legacy seam maps remain Task 011B.",
                "The authoritative graph, minimal Gills instrument, and unresolved build closure remain Task 011B.",
                "Backend lowering, generated source, and ARM compile/link remain Task 011C.",
                "Connected-device, real-time, and audible evidence remain separately authorized later work.",
            ],
        },
    }
    schema = core.load_json(CORPUS_SCHEMA_PATH)
    corpus["content_hash"] = core.record_content_hash(corpus, schema)
    errors = core.schema_errors(corpus, schema, schema)
    if errors:
        raise ValueError("generated catalog corpus is invalid: " + "; ".join(errors))
    return corpus


def build_record_set(corpus: dict[str, Any]) -> dict[str, Any]:
    parent = core.load_json(PARENT_PATH)
    manifest = copy.deepcopy(parent)
    manifest.update(
        {
            "record_set_id": "schuss-record-set-000004",
            "revision": 1,
            "content_hash": "sha256:" + "0" * 64,
            "purpose": "prospective-task",
            "parent_reference": {
                "status": "included",
                "record_set_id": parent["record_set_id"],
                "revision": parent["revision"],
                "content_hash": parent["content_hash"],
            },
        }
    )
    new_schemas = [
        ROOT / "schemas/catalog-corpus-v1.schema.json",
        ROOT / "schemas/catalog-projection-v1.schema.json",
        ROOT / "schemas/operation-request-v2.schema.json",
        ROOT / "schemas/operation-result-v2.schema.json",
    ]
    schema_members = list(manifest["schema_members"])
    for path in new_schemas:
        schema = core.load_json(path)
        schema_members.append(
            {
                "schema_version": schema["$id"][:-len(".schema.json")],
                "portable_path": path.relative_to(ROOT).as_posix(),
                "byte_sha256": core.sha256_file(path),
            }
        )
    record_members = list(manifest["record_members"])
    record_members.append(
        {
            "record_kind": "catalog-corpus",
            "stable_id": corpus["catalog_id"],
            "revision": corpus["revision"],
            "content_hash": corpus["content_hash"],
            "portable_path": CORPUS_PATH.relative_to(ROOT).as_posix(),
            "byte_sha256": core.sha256_file(CORPUS_PATH),
        }
    )
    manifest["schema_members"] = schema_members
    manifest["record_members"] = record_members
    manifest["enforced_directories"] = list(manifest["enforced_directories"]) + [
        "contracts/catalog"
    ]
    schema = core.load_json(RECORD_SET_SCHEMA_PATH)
    manifest["content_hash"] = core.record_content_hash(manifest, schema)
    errors = core.schema_errors(manifest, schema, schema)
    if errors:
        raise ValueError("generated Task 011A record set is invalid: " + "; ".join(errors))
    return manifest


def main() -> int:
    corpus = build_corpus()
    _write_json(CORPUS_PATH, corpus)
    manifest = build_record_set(corpus)
    _write_json(RECORD_SET_PATH, manifest)
    print(
        core.canonical_json(
            {
                "catalog_content_hash": corpus["content_hash"],
                "record_set_content_hash": manifest["content_hash"],
                "family_count": 28,
                "implementation_count": 41,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
