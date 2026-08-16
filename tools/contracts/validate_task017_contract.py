#!/usr/bin/env python3
"""Validate the retained Task 017 completion boundary."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
COMPLETION_PATH = ROOT / "evidence/task017-completion-v1/completion-report.md"
SUMMARY_PATH = ROOT / "evidence/task017-completion-v1/validation-summary.json"


def main() -> int:
    completion = COMPLETION_PATH.read_text(encoding="utf-8")
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    evidence_statuses = [
        item.get("status") for item in summary.get("evidence_levels", [])
    ]
    invalid = (
        summary.get("status") != "valid"
        or summary.get("selected_family_count") != 12
        or summary.get("reference_instrument_count") != 2
        or summary.get("direct_execution_performed") is not False
        or summary.get("record_set_reference", {}).get("record_set_id")
        != "schuss-record-set-000011"
        or evidence_statuses != ["passed"] * 2 + ["not-run"] * 6
        or "exactly two immutable" not in completion
        or "twelve families" not in completion
    )
    result = {
        "dependency": "task-016-complete",
        "evidence_status": "levels-1-through-2-passed",
        "implementation_status": "complete",
        "record_set": "schuss-record-set-000011@1",
        "reference_instruments": summary.get("reference_instrument_count"),
        "schema_version": "task017-contract-validator-v2",
        "selected_families": summary.get("selected_family_count"),
        "status": "invalid" if invalid else "valid",
    }
    print(json.dumps(result, sort_keys=True), file=sys.stderr if invalid else sys.stdout)
    return 1 if invalid else 0


if __name__ == "__main__":
    raise SystemExit(main())
