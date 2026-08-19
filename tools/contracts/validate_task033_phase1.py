#!/usr/bin/env python3
"""Validate the committed Task 033 Phase 1 audit packets without ambient sources."""

from __future__ import annotations

import copy
import hashlib
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/contracts")]

import generate_task033_phase1_audits as generator  # noqa: E402
import validator_core as core  # noqa: E402


def _canonical_bytes(value: Any) -> bytes:
    return core.canonical_json(value).encode("utf-8") + b"\n"


def _fact(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {"byte_length": len(data), "byte_sha256": hashlib.sha256(data).hexdigest()}


def _entries(path: Path) -> list[dict[str, Any]]:
    values = core.load_jsonl(path)
    if path.read_bytes() != b"".join(_canonical_bytes(value) for value in values):
        raise ValueError(f"non-canonical Task 033 JSONL: {path.relative_to(ROOT)}")
    for value in values:
        expected = value.get("entry_sha256")
        material = copy.deepcopy(value)
        material.pop("entry_sha256", None)
        actual = hashlib.sha256(_canonical_bytes(material)).hexdigest()
        if expected != actual:
            raise ValueError(f"stale Task 033 entry hash: {path.relative_to(ROOT)}")
    return values


def _validate_mutable() -> None:
    directory = ROOT / "catalog/reviews/task033-mutable-provider-audit-v1"
    entries_path = directory / "entries.jsonl"
    manifest_path = directory / "manifest.json"
    entries = _entries(entries_path)
    manifest = core.load_json(manifest_path)
    if manifest_path.read_bytes() != _canonical_bytes(manifest):
        raise ValueError("Task 033 Mutable manifest is not canonical")
    if _fact(entries_path) != {
        key: manifest["entries"][key] for key in ("byte_length", "byte_sha256")
    }:
        raise ValueError("Task 033 Mutable entry file fact is stale")
    source_path = ROOT / manifest["source_review"]["portable_path"]
    if _fact(source_path) != {
        key: manifest["source_review"][key] for key in ("byte_length", "byte_sha256")
    }:
        raise ValueError("Task 033 Mutable source review fact is stale")

    source = [
        item
        for item in core.load_jsonl(source_path)
        if generator.MUTABLE_TAG in item["provenance_tags"]
    ]
    expected_ids = sorted(item["catalog_implementation_id"] for item in source)
    actual_ids = [item["implementation_id"] for item in entries]
    if len(entries) != 56 or actual_ids != expected_ids or len(set(actual_ids)) != 56:
        raise ValueError("Task 033 Mutable exact 56-entry identity closure failed")
    source_by_id = {item["catalog_implementation_id"]: item for item in source}
    for item in entries:
        reviewed = source_by_id[item["implementation_id"]]
        if (
            item["source_review"]["entry_id"] != reviewed["entry_id"]
            or item["source_review"]["stable_source_id"] != reviewed["stable_source_id"]
            or item["source_review"]["source_paths"] != reviewed["source_paths"]
            or item["provenance_tags"] != [generator.MUTABLE_TAG]
        ):
            raise ValueError("Task 033 Mutable source/catalog closure failed")
        targets = {row["target"]: row for row in item["target_matrix"]}
        if set(targets) != {"desktop-host", "ksoloti-core"}:
            raise ValueError("Task 033 Mutable target matrix is not closed")
        if targets["desktop-host"]["availability"] != "no-binding-or-eligibility":
            raise ValueError("Task 033 invented Mutable desktop-host availability")
        if item["implementation_id"] in {
            "schuss-implementation-000056",
            "schuss-implementation-000057",
            "schuss-implementation-000058",
        }:
            if "contracted" not in item["readiness_states"]:
                raise ValueError("Task 033 lost an existing Mutable contract")
        elif item["readiness_states"] != ["catalogued-only", "unresolved"]:
            raise ValueError("Task 033 promoted a catalog-only Mutable entry")

    dispositions = Counter(item["disposition"] for item in entries)
    readiness = Counter(
        "contracted-bound" if "contracted" in item["readiness_states"] else "catalogued-only"
        for item in entries
    )
    target_counts = {
        target: dict(
            sorted(
                Counter(
                    next(row for row in item["target_matrix"] if row["target"] == target)["availability"]
                    for item in entries
                ).items()
            )
        )
        for target in ("desktop-host", "ksoloti-core")
    }
    expected_counts = {
        "total": 56,
        "dispositions": dict(sorted(dispositions.items())),
        "readiness": dict(sorted(readiness.items())),
        "targets": target_counts,
    }
    if manifest["counts"] != expected_counts:
        raise ValueError("Task 033 Mutable manifest counts are stale")
    if dispositions != Counter(
        {
            "contract-first-candidate": 51,
            "defer-known-source-failure": 2,
            "defer-retained-unsupported": 1,
            "resolve-existing-contract-first": 2,
        }
    ):
        raise ValueError("Task 033 Mutable disposition matrix drift")


def _validate_juce() -> None:
    directory = ROOT / "catalog/reviews/task033-juce-dsp-audit-v1"
    entries_path = directory / "headers.jsonl"
    manifest_path = directory / "manifest.json"
    entries = _entries(entries_path)
    manifest = core.load_json(manifest_path)
    if manifest_path.read_bytes() != _canonical_bytes(manifest):
        raise ValueError("Task 033 JUCE manifest is not canonical")
    if _fact(entries_path) != {
        key: manifest["entries"][key] for key in ("byte_length", "byte_sha256")
    }:
        raise ValueError("Task 033 JUCE entry file fact is stale")
    source_lock_path = ROOT / manifest["source_lock"]["portable_path"]
    if _fact(source_lock_path) != {
        key: manifest["source_lock"][key] for key in ("byte_length", "byte_sha256")
    }:
        raise ValueError("Task 033 JUCE source-lock fact is stale")

    expected_paths = [item["portable_path"] for item in generator.JUCE_HEADER_SPECS]
    if len(entries) != 39 or [item["source"]["portable_path"] for item in entries] != expected_paths:
        raise ValueError("Task 033 JUCE exact 39-header census failed")
    if [item["source"]["umbrella_include_line"] for item in entries] != list(range(266, 305)):
        raise ValueError("Task 033 JUCE umbrella source spans drift")
    for item, spec in zip(entries, generator.JUCE_HEADER_SPECS, strict=True):
        if (
            item["audit_classification"] != spec["audit_classification"]
            or item["architecture_recommendation"] != spec["architecture_recommendation"]
            or item["candidate_function"] != spec["candidate_function"]
            or item["promotion_state"] != "candidate-only-not-imported-not-linked-not-eligible"
            or item["module_requirements"]["current_schuss_source_lock_includes_module"]
        ):
            raise ValueError("Task 033 JUCE classification or evidence boundary drift")
        if len(item["source"]["byte_sha256"]) != 64 or item["source"]["line_count"] <= 0:
            raise ValueError("Task 033 JUCE exact source fact is malformed")

    classifications = Counter(item["audit_classification"] for item in entries)
    recommendations = Counter(item["architecture_recommendation"] for item in entries)
    if manifest["counts"] != {
        "total": 39,
        "classifications": dict(sorted(classifications.items())),
        "recommendations": dict(sorted(recommendations.items())),
    }:
        raise ValueError("Task 033 JUCE manifest counts are stale")
    if classifications != Counter(
        {
            "asset-dependent-processor": 1,
            "composition-helper": 5,
            "deferred-or-unsuitable": 1,
            "implementation-utility": 12,
            "musical-node-candidate": 20,
        }
    ):
        raise ValueError("Task 033 JUCE classification matrix drift")
    if recommendations != Counter(
        {"defer": 19, "later-juce-host-provider": 8, "native-schuss-algorithm": 12}
    ):
        raise ValueError("Task 033 JUCE recommendation matrix drift")
    if sum("host-service" in item["secondary_classifications"] for item in entries) != 1:
        raise ValueError("Task 033 JUCE host-service distinction drift")
    if (
        manifest["source_lock"]["source"]["archive_sha256"]
        != manifest["authenticated_archive"]["byte_sha256"]
        or not manifest["authenticated_archive"]["matches_source_lock"]
        or not manifest["authenticated_archive"]["reviewed_files_match_archive"]
        or manifest["module"]["present_in_current_schuss_source_lock"]
    ):
        raise ValueError("Task 033 JUCE archive/module boundary drift")


def validate() -> None:
    _validate_mutable()
    _validate_juce()
    task = (ROOT / "docs/tasks/033-object-collections-and-native-provider-architecture.md").read_text(
        encoding="utf-8"
    )
    adr = (
        ROOT
        / "docs/decisions/0017-separate-object-collections-from-implementation-providers.md"
    ).read_text(encoding="utf-8")
    normalized_task = " ".join(task.split())
    normalized_adr = " ".join(adr.split())
    for phrase in (
        "Phase 1 is implemented",
        "integrated into local `main` at commit `6010f29`",
        "Phase 2 has not started",
        "Task 033 has not yet reserved a stable ID",
        "accepted ADR 0017",
        "a canonical 56-entry Mutable audit",
        "a canonical 39-header JUCE audit",
    ):
        if phrase not in normalized_task:
            raise ValueError(f"Task 033 Phase 1 contract is stale: missing {phrase}")
    for phrase in (
        "- Status: accepted",
        "Schuss will model source releases, object collections, catalog",
        "An **object collection** is a curated, function-neutral set",
        "An **implementation provider** is an executable delivery boundary",
        "Task 033 does not add or link `juce_dsp`",
    ):
        if phrase not in normalized_adr:
            raise ValueError(f"ADR 0017 boundary is stale: missing {phrase}")
    paths = (
        ROOT / "catalog/reviews/task033-mutable-provider-audit-v1/entries.jsonl",
        ROOT / "catalog/reviews/task033-mutable-provider-audit-v1/manifest.json",
        ROOT / "catalog/reviews/task033-juce-dsp-audit-v1/headers.jsonl",
        ROOT / "catalog/reviews/task033-juce-dsp-audit-v1/manifest.json",
    )
    if any(b"/Users/" in path.read_bytes() or b"/tmp/" in path.read_bytes() for path in paths):
        raise ValueError("Task 033 audit outputs contain a host path")


def main() -> int:
    validate()
    print("Task 033 Phase 1 audit validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
