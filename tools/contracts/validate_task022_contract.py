#!/usr/bin/env python3
"""Read-only validator for the Task 022 contract and approval gates."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs/tasks/022-connected-gills-control-panel-evidence.md"


def validate() -> dict[str, object]:
    text = CONTRACT.read_text(encoding="utf-8")
    normalized = " ".join(text.split())
    required_sections = (
        "## Goal and why it exists",
        "## Dependencies and exact parent boundary",
        "## In scope",
        "## Out of scope",
        "## Inputs and deliverables",
        "## Required diagnostic behavior",
        "## Required execution order and approval gates",
        "## Acceptance tests",
        "## Decisions Task 022 may make",
        "## Decisions Task 022 must not make",
        "## Completion and failure states",
    )
    missing_sections = [section for section in required_sections if section not in text]
    assertions = (
        "Running the task does not by itself authorize a device write",
        "schuss-record-set-000013@1",
        "Approval gate 1: diagnostic volatile-RAM upload",
        "Approval gate 2: immutable Task 021 product-binary upload",
        "exactly one approved diagnostic volatile-RAM upload",
        "POT_EVENT_FOCUS_UNSTABLE",
        "Approval gate 2 is closed",
        "No device command is permitted in Phase A.",
        "Pots 1-10",
        "Buttons 1-4",
        "all six LED runtime channels",
        "`SCHUSS`, `PANEL TEST`, `TASK022`, and `READY`",
        "Levels 7 and 8 remain `not-run`",
        "Staging, committing, tagging, pushing",
    )
    missing_assertions = [value for value in assertions if value not in normalized]
    acceptance = re.findall(r"^\d+\. ", text[text.index("## Acceptance tests") :], re.MULTILINE)
    status = "valid" if not missing_sections and not missing_assertions and len(acceptance) == 15 else "invalid"
    return {
        "schema_version": "task022-contract-validator-v1",
        "status": status,
        "implementation_status": "diagnostic-failed-promotion-stopped",
        "required_sections": len(required_sections),
        "missing_sections": missing_sections,
        "missing_assertions": missing_assertions,
        "acceptance_tests": len(acceptance),
        "approval_gates": 2,
        "parent_record_set": "schuss-record-set-000013@1",
        "device_actions_authorized_by_contract_creation": False,
    }


def main() -> int:
    try:
        result = validate()
    except (OSError, UnicodeError, ValueError) as exc:
        print("Task 022 contract validation failed: " + str(exc), file=sys.stderr)
        return 1
    stream = sys.stdout if result["status"] == "valid" else sys.stderr
    print(json.dumps(result, sort_keys=True), file=stream)
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
