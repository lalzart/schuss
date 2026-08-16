#!/usr/bin/env python3
"""Read-only validator for the Task 023 contract and activation boundary."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs/tasks/023-cli-v2-and-application-surface-consolidation.md"


def validate() -> dict[str, object]:
    text = CONTRACT.read_text(encoding="utf-8")
    normalized = " ".join(text.split())
    required_sections = (
        "## Goal and why it exists",
        "## Dependencies and verified baseline",
        "## In scope after contract acceptance",
        "## Out of scope",
        "## Inputs and deliverables",
        "## Required application-capability contract",
        "## Required CLI v2 surface",
        "## Child work packages and ownership",
        "## Acceptance tests",
        "## Decisions Task 023 may make",
        "## Decisions Task 023 must not make",
        "## Readiness and activation state",
    )
    required_assertions = (
        "accepted by the user and completed on 2026-08-16",
        "application.describe",
        "application-capability-description-v0",
        "operation-request-v7",
        "operation-result-v7",
        "schuss-record-set-000015@1",
        "schuss-record-set-000014@1",
        "Task 011A golden fixture remains byte-identical",
        "gills.inspect",
        "read-only smoke path",
        "Task 023A",
        "Task 023B",
        "Task 023C",
        "Tasks 023A and 023B may proceed as two implementation lanes",
        "Task 023C waits for both",
        "UI implementation",
        "hardware mutation",
        "explicitly accepted by the user",
        "passed all sixteen acceptance tests",
        "Staging, commit, push",
    )
    missing_sections = [value for value in required_sections if value not in text]
    missing_assertions = [
        value for value in required_assertions if value not in normalized
    ]
    acceptance_section = text.split("## Acceptance tests", 1)[1].split(
        "## Decisions Task 023 may make", 1
    )[0]
    acceptance_tests = re.findall(r"^\d+\. ", acceptance_section, re.MULTILINE)
    status = (
        "valid"
        if not missing_sections
        and not missing_assertions
        and len(acceptance_tests) == 16
        else "invalid"
    )
    return {
        "schema_version": "task023-contract-validator-v1",
        "status": status,
        "implementation_status": "accepted-complete",
        "required_sections": len(required_sections),
        "missing_sections": missing_sections,
        "missing_assertions": missing_assertions,
        "acceptance_tests": len(acceptance_tests),
        "declared_children": ["023A", "023B", "023C"],
        "parallel_children_after_acceptance": ["023A", "023B"],
        "integration_child": "023C",
        "reserved_record_set": "schuss-record-set-000015@1",
        "implementation_authorized_by_contract_creation": False,
        "git_or_hardware_actions_authorized": False,
    }


def main() -> int:
    try:
        result = validate()
    except (OSError, UnicodeError, ValueError, IndexError) as exc:
        print("Task 023 contract validation failed: " + str(exc), file=sys.stderr)
        return 1
    stream = sys.stdout if result["status"] == "valid" else sys.stderr
    print(json.dumps(result, sort_keys=True), file=stream)
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
