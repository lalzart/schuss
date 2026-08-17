#!/usr/bin/env python3
"""Generate Task 027 Mutable-related source review and catalog successors."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/contracts")]

from packages.schuss_core import catalog_projection  # noqa: E402
from packages.schuss_core.control_plane import load_repository_context  # noqa: E402

import record_set_rules  # noqa: E402
import validator_core as core  # noqa: E402


PARENT = ROOT / "contracts/record-sets/task026-authoring-workflow-v1.json"
OUTPUT = ROOT / "contracts/record-sets/task027-mutable-catalog-v1.json"
TASK024_CANDIDATES = ROOT / "catalog/reviews/task024-current-ksoloti-v1/candidates.jsonl"
DECISION = ROOT / "contracts/task027/mutable-curation-decision.md"
SOURCE_LOCK = ROOT / "catalog/sources.lock.json"
EXTENDED_ROOT = "ai/sdk/ksoloti-extended"
EXTENDED_OBJECT_ROOT = EXTENDED_ROOT + "/objects/extended"
EXTENDED_LICENSE = EXTENDED_ROOT + "/LICENSE.md"
PATCHER_COMMIT = "08d3e6e1e2b61230308c20a15ded58ffdaf4656c"
MUTABLE_TAG = "mutable-instruments-derived"

FUNCTION_CATEGORIES = (
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

EXTENDED_DECISIONS: dict[str, tuple[str, str, str]] = {
    "com.lalzart.ksoloti.extended.analysis.pitch-amdf": (
        "spectral-analysis", "inventory-only", "Exact library attribution does not identify Mutable Instruments-derived code or data."
    ),
    "com.lalzart.ksoloti.extended.control.keyframes-4": (
        "modulation-control", "inventory-only", "Exact library attribution does not identify Mutable Instruments-derived code or data."
    ),
    "com.lalzart.ksoloti.extended.effects.comb-network": (
        "filters-resonators", "inventory-only", "Exact library attribution does not identify Mutable Instruments-derived code or data."
    ),
    "com.lalzart.ksoloti.extended.effects.talkbox-lpc": (
        "spectral-analysis", "inventory-only", "Exact library attribution does not identify Mutable Instruments-derived code or data."
    ),
    "com.lalzart.ksoloti.extended.effects.waveset-repeat": (
        "sampling-buffers", "inventory-only", "Exact library attribution does not identify Mutable Instruments-derived code or data."
    ),
    "com.lalzart.ksoloti.extended.grain.clocked-delay": (
        "delay-reverb", "inventory-only", "Exact library attribution does not identify Mutable Instruments-derived code or data."
    ),
    "com.lalzart.ksoloti.extended.grain.seeded-scatter": (
        "sampling-buffers", "inventory-only", "Exact library attribution does not identify Mutable Instruments-derived code or data."
    ),
    "com.lalzart.ksoloti.extended.modulation.bounce": (
        "modulation-control", "inventory-only", "Exact library attribution does not identify Mutable Instruments-derived code or data."
    ),
    "com.lalzart.ksoloti.extended.modulation.poly-slope": (
        "modulation-control", "inventory-only", "Exact library attribution does not identify Mutable Instruments-derived code or data."
    ),
    "com.lalzart.ksoloti.extended.modulation.segment-6": (
        "modulation-control", "inventory-only", "Exact library attribution does not identify Mutable Instruments-derived code or data."
    ),
    "com.lalzart.ksoloti.extended.physical.drip-water": (
        "sound-sources", "inventory-only", "Exact library attribution does not identify Mutable Instruments-derived code or data."
    ),
    "com.lalzart.ksoloti.extended.physical.resonator": (
        "filters-resonators", "catalogued-new-implementation", "The exact license identifies a GPL wrapper around the MIT Rings DSP by Emilie Gillet; its excitation and configurable physical resonation match the reviewed family."
    ),
    "com.lalzart.ksoloti.extended.random.loop-mutate": (
        "modulation-control", "inventory-only", "Exact library attribution does not identify Mutable Instruments-derived code or data."
    ),
    "com.lalzart.ksoloti.extended.random.probability-router": (
        "timing-sequencing", "inventory-only", "Exact library attribution does not identify Mutable Instruments-derived code or data."
    ),
    "com.lalzart.ksoloti.extended.random.pulse-randomizer": (
        "timing-sequencing", "inventory-only", "Exact library attribution does not identify Mutable Instruments-derived code or data."
    ),
    "com.lalzart.ksoloti.extended.random.smooth": (
        "modulation-control", "inventory-only", "Exact library attribution does not identify Mutable Instruments-derived code or data."
    ),
    "com.lalzart.ksoloti.extended.sequencing.topographic-3": (
        "timing-sequencing", "tagged-candidate", "The exact license identifies pattern-map data derived from Grids by Emilie Gillet, but no reviewed family is equivalent to this three-channel rhythm-map sequencer."
    ),
    "com.lalzart.ksoloti.extended.synthesis.macro-voice": (
        "sound-sources", "tagged-candidate", "The exact license identifies a GPL wrapper around vendored MIT Plaits DSP by Emilie Gillet; no reviewed family is equivalent and the source manifest records build-failed."
    ),
    "com.lalzart.ksoloti.extended.timing.adaptive-clock": (
        "timing-sequencing", "inventory-only", "Exact library attribution does not identify Mutable Instruments-derived code or data."
    ),
}

FACTORY_CATALOGUED: dict[str, tuple[str, str, str]] = {
    "axoloti-factory:fx/clds/clds": ("schuss-implementation-000010", "schuss-family-000006", "sampling-buffers"),
    "axoloti-factory:fx/lmnts/lmnts": ("schuss-implementation-000016", "schuss-family-000010", "filters-resonators"),
    "axoloti-factory:fx/rngs/reverb": ("schuss-implementation-000056", "schuss-family-000036", "delay-reverb"),
    "axoloti-factory:osc/brds/struckdrum": ("schuss-implementation-000057", "schuss-family-000037", "sound-sources"),
    "axoloti-factory:osc/brds/struckbell": ("schuss-implementation-000058", "schuss-family-000038", "sound-sources"),
}


def _canonical_bytes(value: Any) -> bytes:
    return core.canonical_json(value).encode("utf-8") + b"\n"


def _child(value: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(value)
    result["content_hash"] = "sha256:" + hashlib.sha256(
        core.canonical_json(
            {key: item for key, item in result.items() if key != "content_hash"}
        ).encode("utf-8")
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


def _ref(record: dict[str, Any], id_field: str) -> dict[str, Any]:
    return {
        "stable_id": record[id_field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def _local_sources() -> dict[str, Path]:
    path = ROOT / "catalog/sources.local.yml"
    if not path.is_file():
        raise ValueError("Task 027 requires ignored catalog/sources.local.yml")
    result: dict[str, Path] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^  ([a-z0-9-]+):\s+(.+?)\s*$", line)
        if match:
            result[match.group(1)] = Path(match.group(2))
    return result


def _git_bytes(checkout: Path, source_path: str) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(checkout), "show", f"{PATCHER_COMMIT}:{source_path}"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        raise ValueError(
            f"pinned Task 027 source is unavailable: patcher@{PATCHER_COMMIT}:{source_path}"
        )
    return completed.stdout


def _git_paths(checkout: Path) -> list[str]:
    completed = subprocess.run(
        [
            "git", "-C", str(checkout), "ls-tree", "-r", "-z", "--name-only",
            PATCHER_COMMIT, "--", EXTENDED_ROOT,
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        raise ValueError("pinned Task 027 extended source tree is unavailable")
    return sorted(item.decode("utf-8") for item in completed.stdout.split(b"\0") if item)


def _source_lock() -> tuple[dict[str, Any], dict[str, Any]]:
    lock = core.load_json(SOURCE_LOCK)
    matches = [item for item in lock["sources"] if item["id"] == "patcher"]
    if len(matches) != 1 or matches[0]["commit"] != PATCHER_COMMIT:
        raise ValueError("Task 027 patcher source lock is absent or stale")
    return lock, matches[0]


def _source_review_schema() -> dict[str, Any]:
    content_hash = {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"}
    raw_sha = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
    portable_path = {
        "type": "string",
        "pattern": "^[A-Za-z0-9][A-Za-z0-9._ -]*(?:/[A-Za-z0-9][A-Za-z0-9._ -]*)*$",
    }
    string_set = {
        "type": "array", "x-schuss-array-kind": "set", "uniqueItems": True,
        "items": {"type": "string", "minLength": 1},
    }
    source_path = {
        "type": "object", "additionalProperties": False,
        "required": ["role", "portable_path", "byte_sha256"],
        "properties": {
            "role": {"enum": ["object", "manifest", "license", "upstream-attribution"]},
            "portable_path": portable_path,
            "byte_sha256": raw_sha,
        },
    }
    entry = {
        "type": "object", "additionalProperties": False,
        "required": [
            "entry_id", "source_kind", "source_id", "commit", "stable_source_id",
            "candidate_ref", "description", "author", "declared_license",
            "source_paths", "functional_category", "provenance_tags",
            "disposition", "disposition_rationale", "catalog_implementation_id",
            "source_manifest_metadata", "known_source_limitations",
        ],
        "properties": {
            "entry_id": {"type": "string", "minLength": 1},
            "source_kind": {"enum": ["factory-candidate", "extended-object"]},
            "source_id": {"enum": ["axoloti-factory", "patcher"]},
            "commit": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
            "stable_source_id": {"type": "string", "minLength": 1},
            "candidate_ref": {"type": "string", "minLength": 1},
            "description": {"type": "string", "minLength": 1},
            "author": {"type": "string"},
            "declared_license": {"type": "string", "minLength": 1},
            "source_paths": {
                "type": "array", "x-schuss-array-kind": "set", "uniqueItems": True,
                "minItems": 1, "items": source_path,
            },
            "functional_category": {
                "oneOf": [
                    {"type": "null"},
                    {"enum": list(FUNCTION_CATEGORIES)},
                ]
            },
            "provenance_tags": string_set,
            "disposition": {
                "enum": [
                    "inventory-only", "tagged-candidate",
                    "catalogued-existing-implementation",
                    "catalogued-new-implementation",
                ]
            },
            "disposition_rationale": {"type": "string", "minLength": 1},
            "catalog_implementation_id": {
                "oneOf": [
                    {"type": "null"},
                    {"type": "string", "pattern": "^schuss-implementation-[0-9]{6}$"},
                ]
            },
            "source_manifest_metadata": {
                "oneOf": [
                    {"type": "null"},
                    {
                        "type": "object", "additionalProperties": False,
                        "required": ["tier", "build_status", "tested_targets", "authority"],
                        "properties": {
                            "tier": {"type": "string", "minLength": 1},
                            "build_status": {"type": "string", "minLength": 1},
                            "tested_targets": string_set,
                            "authority": {"const": "source-declared-metadata-not-schuss-evidence"},
                        },
                    },
                ]
            },
            "known_source_limitations": string_set,
        },
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "catalog-source-review-v0.schema.json",
        "title": "Schuss exact Mutable-related catalog source review v0",
        "type": "object", "additionalProperties": False,
        "required": [
            "schema_version", "canonical_profile", "catalog_source_review_id",
            "revision", "content_hash", "tag_definition", "source_lock",
            "decision_record", "accepted_factory_corpus", "extended_source",
            "review_artifact", "entries", "counts", "evidence_levels",
        ],
        "properties": {
            "schema_version": {"const": "catalog-source-review-v0"},
            "canonical_profile": {"const": "schuss-canonical-json-v1"},
            "catalog_source_review_id": {"const": "schuss-catalog-source-review-000001"},
            "revision": {"const": 1},
            "content_hash": content_hash,
            "tag_definition": {
                "type": "object", "additionalProperties": False,
                "required": ["tag_id", "meaning", "non_implications"],
                "properties": {
                    "tag_id": {"const": MUTABLE_TAG},
                    "meaning": {"const": "Exact pinned source or license evidence explicitly identifies Mutable Instruments-derived code or data."},
                    "non_implications": string_set,
                },
            },
            "source_lock": {
                "type": "object", "additionalProperties": False,
                "required": ["portable_path", "byte_sha256"],
                "properties": {"portable_path": {"const": "catalog/sources.lock.json"}, "byte_sha256": raw_sha},
            },
            "decision_record": {
                "type": "object", "additionalProperties": False,
                "required": ["portable_path", "byte_sha256"],
                "properties": {"portable_path": {"const": "contracts/task027/mutable-curation-decision.md"}, "byte_sha256": raw_sha},
            },
            "accepted_factory_corpus": {
                "type": "object", "additionalProperties": False,
                "required": ["portable_path", "byte_sha256", "candidate_count", "tagged_variant_count"],
                "properties": {
                    "portable_path": {"const": "catalog/reviews/task024-current-ksoloti-v1/candidates.jsonl"},
                    "byte_sha256": raw_sha, "candidate_count": {"const": 685},
                    "tagged_variant_count": {"const": 53},
                },
            },
            "extended_source": {
                "type": "object", "additionalProperties": False,
                "required": ["source_id", "url", "commit", "root", "manifest_count", "axo_count", "license_path", "license_sha256"],
                "properties": {
                    "source_id": {"const": "patcher"}, "url": {"type": "string", "minLength": 1},
                    "commit": {"const": PATCHER_COMMIT}, "root": {"const": EXTENDED_ROOT},
                    "manifest_count": {"const": 19}, "axo_count": {"const": 19},
                    "license_path": {"const": EXTENDED_LICENSE}, "license_sha256": raw_sha,
                },
            },
            "review_artifact": {
                "type": "object", "additionalProperties": False,
                "required": ["portable_path", "byte_sha256", "record_count"],
                "properties": {
                    "portable_path": {"const": "catalog/reviews/task027-mutable-sources-v1/candidates.jsonl"},
                    "byte_sha256": raw_sha, "record_count": {"const": 72},
                },
            },
            "entries": {
                "type": "array", "x-schuss-array-kind": "set", "uniqueItems": True,
                "minItems": 72, "maxItems": 72, "items": entry,
            },
            "counts": {
                "type": "object", "additionalProperties": False,
                "required": ["total", "extended", "factory", "tagged", "inventory_only", "catalogued_implementations", "tagged_candidates"],
                "properties": {
                    "total": {"const": 72}, "extended": {"const": 19}, "factory": {"const": 53},
                    "tagged": {"const": 56}, "inventory_only": {"const": 16},
                    "catalogued_implementations": {"const": 6}, "tagged_candidates": {"const": 50},
                },
            },
            "evidence_levels": {
                "type": "array", "x-schuss-array-kind": "sequence", "minItems": 8, "maxItems": 8,
                "items": {
                    "type": "object", "additionalProperties": False,
                    "required": ["level", "status"],
                    "properties": {"level": {"type": "integer", "minimum": 1, "maximum": 8}, "status": {"enum": ["passed", "not-run"]}},
                },
            },
        },
    }


def _catalog_schemas() -> dict[str, dict[str, Any]]:
    corpus = copy.deepcopy(core.load_json(ROOT / "schemas/catalog-corpus-v3.schema.json"))
    corpus["$id"] = "catalog-corpus-v4.schema.json"
    corpus["title"] = "Schuss exact reviewed catalog corpus v4"
    corpus["properties"]["schema_version"] = {"const": "catalog-corpus-v4"}
    corpus["properties"]["revision"] = {"const": 4}
    corpus["properties"]["projection_version"] = {"const": "schuss-catalog-projection-v4"}
    corpus["properties"]["implementation_additions"].update({"minItems": 45, "maxItems": 45})
    corpus["$defs"]["catalogReference"]["properties"]["revision"] = {"const": 3}
    review_enum = corpus["$defs"]["implementationAddition"]["properties"]["review_status"]["enum"]
    if "task027-reviewed" not in review_enum:
        review_enum.append("task027-reviewed")
    corpus["$defs"]["sourceAuthority"]["oneOf"].append(
        {
            "type": "object", "additionalProperties": False,
            "required": [
                "kind", "source_id", "commit", "evidence_ref", "stable_source_id",
                "manifest_path", "manifest_sha256", "object_path", "object_sha256",
                "license_path", "license_sha256", "declared_license",
            ],
            "properties": {
                "kind": {"const": "pinned-source-object"}, "source_id": {"const": "patcher"},
                "commit": {"const": PATCHER_COMMIT},
                "evidence_ref": {"type": "string", "minLength": 1},
                "stable_source_id": {"type": "string", "minLength": 1},
                "manifest_path": {"$ref": "#/$defs/portablePath"}, "manifest_sha256": {"$ref": "#/$defs/rawSha256"},
                "object_path": {"$ref": "#/$defs/portablePath"}, "object_sha256": {"$ref": "#/$defs/rawSha256"},
                "license_path": {"$ref": "#/$defs/portablePath"}, "license_sha256": {"$ref": "#/$defs/rawSha256"},
                "declared_license": {"type": "string", "minLength": 1},
            },
        }
    )
    exact_reference = {
        "type": "object", "additionalProperties": False,
        "required": ["stable_id", "revision", "content_hash"],
        "properties": {
            "stable_id": {"type": "string", "pattern": "^schuss-[a-z0-9-]+-[0-9]{6}$"},
            "revision": {"type": "integer", "minimum": 1},
            "content_hash": {"$ref": "#/$defs/contentHash"},
        },
    }
    corpus["required"].append("mutable_instruments_review")
    corpus["properties"]["mutable_instruments_review"] = {
        "type": "object", "additionalProperties": False,
        "required": ["source_review_reference", "tag_policy", "implementation_tags"],
        "properties": {
            "source_review_reference": exact_reference,
            "tag_policy": {"const": "exact-source-attribution-only-no-path-or-inspiration-inference"},
            "implementation_tags": {
                "type": "array", "x-schuss-array-kind": "set", "uniqueItems": True,
                "minItems": 6, "maxItems": 6,
                "items": {
                    "type": "object", "additionalProperties": False,
                    "required": ["implementation_id", "tag_id", "source_entry_id"],
                    "properties": {
                        "implementation_id": {"$ref": "#/$defs/implementationId"},
                        "tag_id": {"const": MUTABLE_TAG},
                        "source_entry_id": {"type": "string", "minLength": 1},
                    },
                },
            },
        },
    }

    projection = copy.deepcopy(core.load_json(ROOT / "schemas/catalog-projection-v3.schema.json"))
    projection["$id"] = "catalog-projection-v4.schema.json"
    projection["title"] = "Schuss derived catalog projection v4"
    projection["properties"]["schema_version"] = {"const": "catalog-projection-v4"}
    projection["properties"]["projection_version"] = {"const": "schuss-catalog-projection-v4"}
    projection["$defs"]["catalogReference"]["properties"]["revision"] = {"const": 4}
    summary = projection["$defs"]["implementationSummary"]
    summary["required"].append("provenance_tags")
    summary["properties"]["provenance_tags"] = {"$ref": "#/$defs/stringSet"}
    return {
        "catalog-source-review-v0.schema.json": _source_review_schema(),
        "catalog-corpus-v4.schema.json": corpus,
        "catalog-projection-v4.schema.json": projection,
    }


def _factory_entries() -> list[dict[str, Any]]:
    source_lock, _ = _source_lock()
    factory_commit = next(item["commit"] for item in source_lock["sources"] if item["id"] == "axoloti-factory")
    candidates = core.load_jsonl(TASK024_CANDIDATES)
    if len(candidates) != 685:
        raise ValueError("accepted Task 024 factory candidate corpus count changed")
    entries: list[dict[str, Any]] = []
    for candidate in candidates:
        if candidate["library_id"] != "axoloti-factory":
            continue
        for variant in candidate["variants"]:
            description = variant["description"]
            if "mutable instruments" not in description.lower():
                continue
            if not variant["declared_license"]:
                raise ValueError(f"Mutable-attributed factory candidate lacks a license declaration: {variant['variant_ref']}")
            catalogued = FACTORY_CATALOGUED.get(candidate["base_ref"])
            limitations: list[str] = []
            if not variant["author"]:
                limitations.append("The exact factory object has no author field; Mutable ancestry comes from its source description only.")
            if candidate["base_ref"] == "axoloti-factory:fx/wrps/wrps":
                expected = "BUG: this will not currently link, due to axo firmware issue"
                if expected not in description:
                    raise ValueError("factory Warps link-failure statement changed")
                limitations.append(expected)
            if candidate["base_ref"] == "axoloti-factory:fx/wrps/vocoder":
                limitations.append("No reviewed Schuss family equivalence or implementation curation is established.")
            entries.append(
                {
                    "entry_id": "factory:" + variant["variant_ref"],
                    "source_kind": "factory-candidate", "source_id": "axoloti-factory",
                    "commit": factory_commit, "stable_source_id": variant["variant_ref"],
                    "candidate_ref": candidate["candidate_ref"],
                    "description": description, "author": variant["author"],
                    "declared_license": variant["declared_license"],
                    "source_paths": [
                        {"role": "object", "portable_path": variant["source_path"], "byte_sha256": variant["source_sha256"]}
                    ],
                    "functional_category": catalogued[2] if catalogued else None,
                    "provenance_tags": [MUTABLE_TAG],
                    "disposition": "catalogued-existing-implementation" if catalogued else "tagged-candidate",
                    "disposition_rationale": (
                        "The exact accepted catalog implementation and source observation establish membership; Mutable ancestry remains a separate provenance facet."
                        if catalogued
                        else "The exact source description supports the provenance tag, but no reviewed existing-family equivalence is established."
                    ),
                    "catalog_implementation_id": catalogued[0] if catalogued else None,
                    "source_manifest_metadata": None,
                    "known_source_limitations": sorted(limitations),
                }
            )
    if len(entries) != 53:
        raise ValueError(f"expected 53 exact factory Mutable-attributed variants, found {len(entries)}")
    return entries


def _extended_entries(checkout: Path) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    paths = _git_paths(checkout)
    manifests = [path for path in paths if path.startswith(EXTENDED_OBJECT_ROOT + "/") and path.endswith(".manifest.json")]
    objects = [path for path in paths if path.startswith(EXTENDED_OBJECT_ROOT + "/") and path.endswith(".axo")]
    if len(manifests) != 19 or len(objects) != 19:
        raise ValueError(f"expected 19 extended manifests and 19 .axo files, found {len(manifests)} and {len(objects)}")
    license_bytes = _git_bytes(checkout, EXTENDED_LICENSE)
    license_sha = hashlib.sha256(license_bytes).hexdigest()
    license_text = license_bytes.decode("utf-8")
    required_attribution = ("Physical resonator", "Topographic sequencer", "Complete macro voice")
    if any(text not in license_text for text in required_attribution):
        raise ValueError("exact extended license attribution sections changed")
    object_by_stem = {path.removesuffix(".axo"): path for path in objects}
    entries: list[dict[str, Any]] = []
    manifests_by_id: dict[str, dict[str, Any]] = {}
    uuids: set[str] = set()
    for manifest_path in manifests:
        raw = _git_bytes(checkout, manifest_path)
        manifest = core.load_json_bytes(raw, subject=f"patcher@{PATCHER_COMMIT}:{manifest_path}")
        stable_id = manifest["stable_id"]
        if stable_id not in EXTENDED_DECISIONS or stable_id in manifests_by_id:
            raise ValueError(f"unexpected or duplicate extended stable ID: {stable_id}")
        if manifest["uuid"] in uuids:
            raise ValueError(f"duplicate extended UUID: {manifest['uuid']}")
        uuids.add(manifest["uuid"])
        stem = manifest_path.removesuffix(".manifest.json")
        object_path = object_by_stem.get(stem)
        if object_path is None:
            raise ValueError(f"extended manifest has no paired .axo: {manifest_path}")
        object_bytes = _git_bytes(checkout, object_path)
        try:
            xml = ET.fromstring(object_bytes)
        except ET.ParseError as exc:
            raise ValueError(f"extended .axo is invalid: {object_path}: {exc}") from exc
        normal = next((item for item in xml if item.tag.rsplit("}", 1)[-1] == "obj.normal"), None)
        if normal is None or normal.attrib.get("id") != manifest["id"] or normal.attrib.get("uuid") != manifest["uuid"]:
            raise ValueError(f"extended manifest/.axo identity mismatch: {stable_id}")
        category, disposition, rationale = EXTENDED_DECISIONS[stable_id]
        tagged = disposition != "inventory-only"
        limitations: list[str] = []
        compatibility = manifest["compatibility"]
        if stable_id.endswith("synthesis.macro-voice"):
            if compatibility["tier"] != "h7-recommended" or compatibility["build_status"] != "build-failed":
                raise ValueError("macro voice source compatibility boundary changed")
            limitations.append("Source manifest records build-failed for ksoloti-core@1.1.0; Task 027 does not reproduce or promote that build result.")
        attribution_paths = [
            {"role": "manifest", "portable_path": manifest_path, "byte_sha256": hashlib.sha256(raw).hexdigest()},
            {"role": "object", "portable_path": object_path, "byte_sha256": hashlib.sha256(object_bytes).hexdigest()},
            {"role": "license", "portable_path": EXTENDED_LICENSE, "byte_sha256": license_sha},
        ]
        if stable_id.endswith("synthesis.macro-voice"):
            vendor_path = EXTENDED_OBJECT_ROOT + "/synthesis/vendor/README.md"
            vendor_bytes = _git_bytes(checkout, vendor_path)
            attribution_paths.append(
                {"role": "upstream-attribution", "portable_path": vendor_path, "byte_sha256": hashlib.sha256(vendor_bytes).hexdigest()}
            )
        entry = {
            "entry_id": "extended:" + stable_id,
            "source_kind": "extended-object", "source_id": "patcher", "commit": PATCHER_COMMIT,
            "stable_source_id": stable_id,
            "candidate_ref": f"patcher@{PATCHER_COMMIT}:{stable_id}",
            "description": manifest["description"], "author": manifest["author"],
            "declared_license": manifest["license"],
            "source_paths": sorted(attribution_paths, key=core.canonical_json),
            "functional_category": category,
            "provenance_tags": [MUTABLE_TAG] if tagged else [],
            "disposition": disposition, "disposition_rationale": rationale,
            "catalog_implementation_id": "schuss-implementation-000096" if disposition == "catalogued-new-implementation" else None,
            "source_manifest_metadata": {
                "tier": compatibility["tier"], "build_status": compatibility["build_status"],
                "tested_targets": sorted(compatibility["tested_targets"]),
                "authority": "source-declared-metadata-not-schuss-evidence",
            },
            "known_source_limitations": sorted(limitations),
        }
        entries.append(entry)
        manifests_by_id[stable_id] = {
            "manifest": manifest,
            "manifest_path": manifest_path,
            "manifest_sha256": hashlib.sha256(raw).hexdigest(),
            "object_path": object_path,
            "object_sha256": hashlib.sha256(object_bytes).hexdigest(),
            "license_sha256": license_sha,
        }
    if set(manifests_by_id) != set(EXTENDED_DECISIONS):
        raise ValueError("extended decision table does not cover the exact 19-object source tree")
    return entries, manifests_by_id


def _source_review(
    entries: list[dict[str, Any]],
    patcher_lock: dict[str, Any],
    license_sha: str,
    schema: dict[str, Any],
    review_bytes: bytes,
) -> dict[str, Any]:
    counts = Counter(item["source_kind"] for item in entries)
    dispositions = Counter(item["disposition"] for item in entries)
    tagged = sum(MUTABLE_TAG in item["provenance_tags"] for item in entries)
    if (counts["extended-object"], counts["factory-candidate"], tagged) != (19, 53, 56):
        raise ValueError("Task 027 source-review census changed")
    return _record(
        {
            "schema_version": "catalog-source-review-v0", "canonical_profile": "schuss-canonical-json-v1",
            "catalog_source_review_id": "schuss-catalog-source-review-000001", "revision": 1,
            "tag_definition": {
                "tag_id": MUTABLE_TAG,
                "meaning": "Exact pinned source or license evidence explicitly identifies Mutable Instruments-derived code or data.",
                "non_implications": sorted(
                    [
                        "audible quality or behavior", "catalog family identity or preference",
                        "compiler backend or target support", "connected-device or real-time behavior",
                        "component contract binding or eligibility",
                    ]
                ),
            },
            "source_lock": {"portable_path": "catalog/sources.lock.json", "byte_sha256": core.sha256_file(SOURCE_LOCK)},
            "decision_record": {"portable_path": "contracts/task027/mutable-curation-decision.md", "byte_sha256": core.sha256_file(DECISION)},
            "accepted_factory_corpus": {
                "portable_path": "catalog/reviews/task024-current-ksoloti-v1/candidates.jsonl",
                "byte_sha256": core.sha256_file(TASK024_CANDIDATES), "candidate_count": 685,
                "tagged_variant_count": 53,
            },
            "extended_source": {
                "source_id": "patcher", "url": patcher_lock["url"], "commit": PATCHER_COMMIT,
                "root": EXTENDED_ROOT, "manifest_count": 19, "axo_count": 19,
                "license_path": EXTENDED_LICENSE, "license_sha256": license_sha,
            },
            "review_artifact": {
                "portable_path": "catalog/reviews/task027-mutable-sources-v1/candidates.jsonl",
                "byte_sha256": hashlib.sha256(review_bytes).hexdigest(), "record_count": 72,
            },
            "entries": entries,
            "counts": {
                "total": 72, "extended": 19, "factory": 53, "tagged": 56,
                "inventory_only": dispositions["inventory-only"],
                "catalogued_implementations": dispositions["catalogued-existing-implementation"] + dispositions["catalogued-new-implementation"],
                "tagged_candidates": dispositions["tagged-candidate"],
            },
            "evidence_levels": [
                {"level": level, "status": "passed" if level <= 2 else "not-run"}
                for level in range(1, 9)
            ],
        },
        schema,
    )


def _catalog(
    parent: dict[str, Any],
    source_review: dict[str, Any],
    manifests: dict[str, dict[str, Any]],
    schema: dict[str, Any],
) -> dict[str, Any]:
    corpus = copy.deepcopy(parent)
    corpus.update(
        {
            "schema_version": "catalog-corpus-v4", "revision": 4,
            "projection_version": "schuss-catalog-projection-v4",
            "parent_corpus_reference": {
                "catalog_id": parent["catalog_id"], "revision": parent["revision"],
                "content_hash": parent["content_hash"],
            },
        }
    )
    source = manifests["com.lalzart.ksoloti.extended.physical.resonator"]
    manifest = source["manifest"]
    family = next(
        item for item in parent["family_companions"]
        if item["family_id"] == "schuss-family-000010"
    )
    authority = {
        "kind": "pinned-source-object", "source_id": "patcher", "commit": PATCHER_COMMIT,
        "evidence_ref": "extended:com.lalzart.ksoloti.extended.physical.resonator",
        "stable_source_id": manifest["stable_id"],
        "manifest_path": source["manifest_path"], "manifest_sha256": source["manifest_sha256"],
        "object_path": source["object_path"], "object_sha256": source["object_sha256"],
        "license_path": EXTENDED_LICENSE, "license_sha256": source["license_sha256"],
        "declared_license": manifest["license"],
    }
    addition = _child(
        {
            "implementation_id": "schuss-implementation-000096", "revision": 1,
            "family_reference": {
                "family_id": family["family_id"], "revision": family["revision"],
                "content_hash": family["content_hash"],
            },
            "display_name": "Extended Rings physical resonator",
            "form": "native-object", "review_status": "task027-reviewed",
            "membership_confidence": "high",
            "membership_rationale": "The exact source combines excitation and configurable modal/string physical resonation, matching the accepted Physical-model Resonator family without using ancestry as family identity.",
            "source_authority": authority, "compatibility_status": "not-evaluated",
            "unresolved_questions": sorted(
                [
                    "Source manifest compatibility and build fields are not Schuss compiler or target evidence.",
                    "No exact component contract, binding, backend eligibility, ARM result, device, real-time, or audible evidence is established by Task 027.",
                ]
            ),
        }
    )
    corpus["implementation_additions"].append(addition)
    corpus["implementation_additions"].sort(key=lambda item: item["implementation_id"])
    implementation_entries = {
        item["catalog_implementation_id"]: item
        for item in source_review["entries"]
        if item["catalog_implementation_id"] is not None
    }
    expected_ids = {
        "schuss-implementation-000010", "schuss-implementation-000016",
        "schuss-implementation-000056", "schuss-implementation-000057",
        "schuss-implementation-000058", "schuss-implementation-000096",
    }
    if set(implementation_entries) != expected_ids:
        raise ValueError("Task 027 tagged catalog implementation set changed")
    corpus["mutable_instruments_review"] = {
        "source_review_reference": _ref(source_review, "catalog_source_review_id"),
        "tag_policy": "exact-source-attribution-only-no-path-or-inspiration-inference",
        "implementation_tags": sorted(
            [
                {
                    "implementation_id": identifier, "tag_id": MUTABLE_TAG,
                    "source_entry_id": implementation_entries[identifier]["entry_id"],
                }
                for identifier in expected_ids
            ],
            key=core.canonical_json,
        ),
    }
    return _record(corpus, schema)


def generated() -> tuple[dict[str, bytes], bytes, dict[str, Any], dict[str, Any]]:
    parent_manifest = core.load_json(PARENT)
    if any(
        item["stable_id"] == "schuss-implementation-000096"
        for item in parent_manifest["record_members"]
    ):
        raise ValueError("Task 027 implementation ID 000096 collides with the exact parent")
    parent_context = load_repository_context(record_set_path=PARENT)
    parent_catalog = parent_context.records["catalog"][0]
    if parent_catalog["schema_version"] != "catalog-corpus-v3" or parent_catalog["revision"] != 3:
        raise ValueError("Task 027 parent does not select exact catalog v3")
    _, patcher_lock = _source_lock()
    patcher = _local_sources().get("patcher")
    if patcher is None or not patcher.is_dir():
        raise ValueError("Task 027 local patcher source mapping is absent")

    schemas = _catalog_schemas()
    for name, schema in schemas.items():
        annotations = core.validate_schema_annotations(schema)
        if annotations:
            raise ValueError(f"Task 027 schema annotations invalid for {name}: {annotations}")

    factory_entries = _factory_entries()
    extended_entries, manifests = _extended_entries(patcher)
    entries = sorted(factory_entries + extended_entries, key=lambda item: item["entry_id"])
    review_bytes = b"".join(_canonical_bytes(item) for item in entries)
    license_sha = manifests["com.lalzart.ksoloti.extended.physical.resonator"]["license_sha256"]
    source_review = _source_review(
        entries, patcher_lock, license_sha,
        schemas["catalog-source-review-v0.schema.json"], review_bytes,
    )
    catalog = _catalog(
        parent_catalog, source_review, manifests,
        schemas["catalog-corpus-v4.schema.json"],
    )
    selector = _record(
        {
            "schema_version": "catalog-selection-v0", "canonical_profile": "schuss-canonical-json-v1",
            "catalog_selection_id": "schuss-catalog-selection-000001", "revision": 3,
            "corpus_reference": {"catalog_id": catalog["catalog_id"], "revision": catalog["revision"], "content_hash": catalog["content_hash"]},
            "rationale": "Select the exact Task 027 sixty-family catalog successor with evidence-backed Mutable provenance tags and one extended resonator implementation.",
        },
        core.load_json(ROOT / "schemas/catalog-selection-v0.schema.json"),
    )

    files: dict[str, bytes] = {
        f"schemas/{name}": _canonical_bytes(schema) for name, schema in schemas.items()
    }
    records = {
        "contracts/task027/catalog-source-review.json": source_review,
        "contracts/task027/catalog-corpus-v4.json": catalog,
        "contracts/task027/catalog-selection-r3.json": selector,
    }
    files.update({path: _canonical_bytes(record) for path, record in records.items()})
    files["catalog/reviews/task027-mutable-sources-v1/candidates.jsonl"] = review_bytes

    schema_members = copy.deepcopy(parent_manifest["schema_members"])
    existing_schemas = {item["schema_version"] for item in schema_members}
    for name in sorted(schemas):
        version = name.removesuffix(".schema.json")
        if version in existing_schemas:
            raise ValueError(f"Task 027 schema version collides with parent: {version}")
        path = f"schemas/{name}"
        schema_members.append(
            {"schema_version": version, "portable_path": path, "byte_sha256": hashlib.sha256(files[path]).hexdigest()}
        )

    record_members = copy.deepcopy(parent_manifest["record_members"])
    for kind, record, field, path in (
        ("catalog-source-review", source_review, "catalog_source_review_id", "contracts/task027/catalog-source-review.json"),
        ("catalog-corpus", catalog, "catalog_id", "contracts/task027/catalog-corpus-v4.json"),
        ("catalog-selection", selector, "catalog_selection_id", "contracts/task027/catalog-selection-r3.json"),
    ):
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
        "record_set_id": "schuss-record-set-000020", "revision": 1,
        "content_hash": "sha256:" + "0" * 64, "purpose": "prospective-task",
        "parent_reference": {
            "status": "included",
            **{key: parent_manifest[key] for key in ("record_set_id", "revision", "content_hash")},
        },
        "schema_members": sorted(schema_members, key=lambda item: (item["byte_sha256"], item["portable_path"])),
        "record_members": sorted(record_members, key=lambda item: (item["byte_sha256"], item["portable_path"])),
        "enforced_directories": sorted(set(parent_manifest["enforced_directories"]) | {"contracts/task027"}),
    }
    errors = core.schema_errors(manifest, manifest_schema, manifest_schema)
    if errors:
        raise ValueError("; ".join(errors))
    manifest["content_hash"] = core.record_content_hash(manifest, manifest_schema)

    projection_records = dict(parent_context.records)
    projection_records["catalog_source_reviews"] = (source_review,)
    projection = catalog_projection.build_catalog_projection(
        corpus=copy.deepcopy(catalog),
        corpus_schema=schemas["catalog-corpus-v4.schema.json"],
        projection_schema=schemas["catalog-projection-v4.schema.json"],
        overlay=copy.deepcopy(parent_context.overlay),
        overlay_sha256=parent_context.overlay_sha256,
        observations=copy.deepcopy(parent_context.observations),
        records=projection_records,
        record_set_reference={key: manifest[key] for key in ("record_set_id", "revision", "content_hash")},
        core=core,
    )
    tagged_families = [
        item for item in projection["families"]
        if MUTABLE_TAG in item["provenance_facets"]
    ]
    summary = {
        "schema_version": "task027-generation-summary-v1", "status": "valid",
        "record_set_reference": {key: manifest[key] for key in ("record_set_id", "revision", "content_hash")},
        "source_review_count": len(entries), "extended_object_count": len(extended_entries),
        "factory_mutable_candidate_count": len(factory_entries),
        "mutable_tagged_candidate_count": sum(MUTABLE_TAG in item["provenance_tags"] for item in entries),
        "catalog_family_count": len(projection["families"]),
        "catalog_implementation_count": sum(len(item["implementations"]) for item in projection["families"]),
        "tagged_catalog_implementation_count": sum(
            MUTABLE_TAG in implementation.get("provenance_tags", [])
            for family in projection["families"] for implementation in family["implementations"]
        ),
        "tagged_catalog_family_count": len(tagged_families),
        "projection_sha256": hashlib.sha256(_canonical_bytes(projection)).hexdigest(),
        "evidence_levels": source_review["evidence_levels"],
        "compiler_or_build_performed": False, "java_or_legacy_axp_performed": False,
        "hardware_or_publication_performed": False,
    }
    files["evidence/task027-completion-v1/validation-summary.json"] = _canonical_bytes(summary)
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
            raise ValueError("Task 027 generated outputs are stale: " + ", ".join(sorted(stale)))
        if not args.check:
            for relative, payload in expected.items():
                path = ROOT / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
    except (OSError, ValueError, KeyError, StopIteration) as exc:
        print("Task 027 generation failed: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
