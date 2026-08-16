#!/usr/bin/env python3
"""Validate the ready Task 018 contract boundary."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / "docs/tasks/018-full-gills-implementation-and-parameter-control-mapping.md"

REQUIRED_SECTIONS = (
    "## Goal and why it exists",
    "## Dependencies",
    "## In scope after the dependencies close",
    "## Out of scope",
    "## Inputs and deliverables",
    "## Acceptance tests",
    "## Decisions Task 018 may make",
    "## Decisions Task 018 must not make",
    "## Readiness state",
)

REQUIRED_ASSERTIONS = (
    "Tasks 016 and 017 are complete",
    "Task 017 must be complete before Task 018 may create",
    "Task 018 may not bypass either dependency",
    "ADR 0012",
    "two exact Task 017 reference instruments",
    "direct device-to-graph shortcuts fail closed",
    "At least one exact mapped Gills reference",
    "evidence level 5",
    "does not satisfy this executable promotion gate",
    "Levels 6-8 remain `not-run`",
    "No Task 018 implementation has occurred yet",
)


def main() -> int:
    text = PATH.read_text(encoding="utf-8")
    missing_sections = [heading for heading in REQUIRED_SECTIONS if heading not in text]
    missing_assertions = [assertion for assertion in REQUIRED_ASSERTIONS if assertion not in text]
    acceptance_prefixes = tuple(f"{number}. " for number in range(1, 14))
    acceptance_tests = sum(
        1 for line in text.splitlines() if line.startswith(acceptance_prefixes)
    )
    invalid = (
        missing_sections
        or missing_assertions
        or acceptance_tests != 13
        or "implementation is ready but not started" not in text
        or "semantic record, runtime code, mapping" not in text
    )
    summary = {
        "acceptance_tests": acceptance_tests,
        "dependency": "task-017-complete",
        "implementation_status": "ready-not-started",
        "missing_assertions": missing_assertions,
        "missing_sections": missing_sections,
        "promotion_gate": "mapped-level-5-required",
        "required_executable_reference_instruments": 1,
        "required_sections": len(REQUIRED_SECTIONS),
        "schema_version": "task018-contract-validator-v3",
        "semantic_records_created": 0,
        "status": "invalid" if invalid else "valid",
        "transitive_dependency": "task-016-complete",
    }
    stream = sys.stderr if invalid else sys.stdout
    print(json.dumps(summary, sort_keys=True), file=stream)
    return 1 if invalid else 0


if __name__ == "__main__":
    raise SystemExit(main())
