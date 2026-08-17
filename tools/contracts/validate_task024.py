#!/usr/bin/env python3
"""Validate the retained Task 024 completion boundary."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SUMMARY = ROOT / "evidence/task024-completion-v1/validation-summary.json"
REPORT = ROOT / "evidence/task024-completion-v1/completion-report.md"


def main() -> int:
    try:
        summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
        report = REPORT.read_text(encoding="utf-8")
        normalized_report = " ".join(report.split())
        valid = (
            summary.get("status") == "valid"
            and summary.get("frozen_observation_count") == 3602
            and summary.get("catalog_family_count") == 60
            and summary.get("additional_family_count") == 20
            and summary.get("current_ksoloti_candidate_count") == 685
            and summary.get("current_ksoloti_normal_definition_count") == 835
            and summary.get("current_ksoloti_compound_count") == 19
            and summary.get("complete_variant_implementation_count") == 29
            and summary.get("task025_subject_count") == 8
            and summary.get("compiler_or_build_performed") is False
            and summary.get("hardware_or_publication_performed") is False
            and [item.get("status") for item in summary.get("evidence_levels", ())] == ["passed", "passed"] + ["not-run"] * 6
            and "current Ksoloti first-party source corpus is now the primary candidate authority" in normalized_report
            and "Every frozen observation retains one deterministic disposition" in normalized_report
            and "not a product backlog" in normalized_report
            and "No compiler, build, project, UI, device, real-time, audible, Git, or publication action was performed" in normalized_report
        )
    except (OSError, UnicodeError, ValueError, KeyError) as exc:
        print("Task 024 completion validation failed: " + str(exc), file=sys.stderr)
        return 1
    result = {
        "schema_version": "task024-completion-validator-v1",
        "status": "valid" if valid else "invalid",
        "implementation_status": "complete" if valid else "incomplete",
        "record_set": "schuss-record-set-000016@1",
        "frozen_observations": summary.get("frozen_observation_count"),
        "catalog_families": summary.get("catalog_family_count"),
        "current_ksoloti_candidates": summary.get("current_ksoloti_candidate_count"),
        "complete_variant_implementations": summary.get("complete_variant_implementation_count"),
        "task025_subjects": summary.get("task025_subject_count"),
        "highest_evidence": "level-2" if valid else "not-established",
    }
    print(json.dumps(result, sort_keys=True), file=sys.stdout if valid else sys.stderr)
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
