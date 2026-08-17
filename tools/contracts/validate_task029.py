#!/usr/bin/env python3
"""Validate the bounded Task 029 Gills machine layer without external checkouts."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/contracts")]

from packages.schuss_core.control_plane import dispatch_operation, load_repository_context  # noqa: E402

import generate_task029_records as generator  # noqa: E402
import generate_task029_viewer_fixtures as fixture_generator  # noqa: E402
import validator_core as core  # noqa: E402


RECORD_SET = ROOT / "contracts/record-sets/task029-gills-machines-v1.json"
PARENT_SET = ROOT / "contracts/record-sets/task028-direct-palette-v1.json"
EVIDENCE_ROOT = ROOT / "evidence/task029-completion-v1"


def _exact(values, field: str, identifier: str) -> dict:
    matches = [item for item in values if item[field] == identifier]
    if len(matches) != 1:
        raise ValueError(f"{identifier} did not resolve exactly")
    return matches[0]


def main() -> int:
    context = load_repository_context(record_set_path=RECORD_SET)
    manifest = core.load_json(RECORD_SET)
    parent = core.load_json(PARENT_SET)
    if manifest["parent_reference"] != {
        "status": "included",
        **{key: parent[key] for key in ("record_set_id", "revision", "content_hash")},
    }:
        raise ValueError("Task 029 parent record set differs")
    if context.machine_summary["status"] != "valid":
        raise ValueError("Task 029 machine layer is invalid")
    expected_counts = {
        "machine_source_reviews": 2,
        "panel_layouts": 1,
        "machine_presentations": 2,
        "machines": 0,
    }
    if context.machine_summary["record_counts"] != expected_counts:
        raise ValueError("Task 029 machine-layer counts differ")

    files, generated_manifest, generated_summary = generator.generated()
    stale = [path for path, data in files.items() if (ROOT / path).read_bytes() != data]
    if generated_manifest != RECORD_SET.read_bytes() or stale:
        raise ValueError("Task 029 records are stale: " + ", ".join(stale))
    fixture_outputs = fixture_generator.generated()
    stale_fixtures = [path.relative_to(ROOT).as_posix() for path, data in fixture_outputs.items() if path.read_bytes() != data]
    if stale_fixtures:
        raise ValueError("Task 029 Viewer fixtures are stale: " + ", ".join(stale_fixtures))

    reviews = {
        item["asserted_identity"]["display_name"]: item
        for item in context.records["machine_source_reviews"]
    }
    if set(reviews) != {"Palimpsest", "Tide Pit"}:
        raise ValueError("Task 029 reference-machine names differ")
    operation_results = []
    for name in sorted(reviews):
        review = reviews[name]
        result = dispatch_operation(
            {
                "schema_version": "schuss-operation-request-v9",
                "canonical_profile": "schuss-canonical-json-v1",
                "operation": "machine.inspect",
                "payload": {
                    "source_review_reference": {
                        key: review[key]
                        for key in (
                            "machine_source_review_id",
                            "revision",
                            "content_hash",
                        )
                    }
                },
            },
            context,
        )
        if result["status"] != "success" or result["value"]["inspection_state"] != "inspection-only":
            raise ValueError(f"{name} inspection failed closed incorrectly")
        operation_results.append(
            {
                "display_name": name,
                "entry_kind": result["value"]["entry_kind"],
                "source_declared_bytes": result["value"]["resources"]["source_declared_bytes"],
            }
        )

    packet = _exact(
        context.records["selection_packets"],
        "selection_packet_id",
        "schuss-core-selection-000003",
    )
    if packet["final_safe_selectable_total"] != 20:
        raise ValueError("Task 029 changed the accepted palette count")
    expected_reference = {
        key: manifest[key]
        for key in ("record_set_id", "revision", "content_hash")
    }
    validation_evidence = core.load_json(EVIDENCE_ROOT / "validation-summary.json")
    acceptance_matrix = core.load_json(EVIDENCE_ROOT / "acceptance-matrix.json")
    prerequisites = core.load_json(EVIDENCE_ROOT / "remaining-prerequisites.json")
    if validation_evidence["record_set_reference"] != expected_reference:
        raise ValueError("Task 029 validation evidence names a different record set")
    if acceptance_matrix["record_set_reference"] != expected_reference:
        raise ValueError("Task 029 acceptance matrix names a different record set")
    if prerequisites["catalog_policy"]["accepted_palette_count"] != 20:
        raise ValueError("Task 029 prerequisites change the accepted palette")
    if {prerequisites[name]["state"] for name in ("palimpsest", "tide_pit")} != {"inspection-only"}:
        raise ValueError("Task 029 prerequisites overstate machine completion")
    summary = {
        "schema_version": "task029-validation-result-v0",
        "status": "passed",
        "record_set": f'{manifest["record_set_id"]}@{manifest["revision"]}',
        "record_set_content_hash": manifest["content_hash"],
        "parent_record_set": f'{parent["record_set_id"]}@{parent["revision"]}',
        "accepted_palette_count": packet["final_safe_selectable_total"],
        "machine_layer": context.machine_summary,
        "reference_machine_inspections": operation_results,
        "generated_summary": generated_summary,
        "viewer_fixture_count": 2,
        "proof_limits": {
            "structural_level_1": "passed",
            "levels_2_through_8": "not-run",
            "task029_build_or_compiler_action": False,
            "hardware_or_device_action": False,
            "catalog_promotion": False,
        },
    }
    print(core.canonical_json(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
