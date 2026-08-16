#!/usr/bin/env python3
"""Validate the completed Task 021 corrective contract boundary."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / "docs/tasks/021-gills-dma-safe-oled-and-connected-device-evidence.md"

REQUIRED_SECTIONS = (
    "## Goal and why it exists",
    "## Dependencies",
    "## In scope",
    "## Out of scope",
    "## Inputs and deliverables",
    "## Acceptance tests",
    "## Decisions Task 021 may make",
    "## Decisions Task 021 must not make",
    "## Readiness state",
)

REQUIRED_ASSERTIONS = (
    "Task 018 is the immutable parent closure",
    "ADR 0013",
    "two-byte `.sram2` buffer",
    "mechanical instrument/coverage successors",
    "no implicit fallback",
    "schuss-record-set-000013@1",
    "six-reference producer-input closure",
    "e69155998e91c7c3af6b6e0aaebbac965f4cf822b67382f25de5776453af2928",
    "4f9bd68f5f71fc9d5bf70bd88988e7e20ff980fb46a886beff52f60c968874de",
    "b573ea36aaa29b5e213ca0e616b13e7e2131d7cad2a0ab29a5b5fe9eaa8b13e3",
    "Levels 7 and 8 remain `not-run`",
    "firmware flash, SD-card write",
    "Tasks 019 and 020 remain deferred",
)


def main() -> int:
    text = PATH.read_text(encoding="utf-8")
    missing_sections = [heading for heading in REQUIRED_SECTIONS if heading not in text]
    missing_assertions = [value for value in REQUIRED_ASSERTIONS if value not in text]
    acceptance_prefixes = tuple(f"{number}. " for number in range(1, 13))
    acceptance_tests = sum(
        1 for line in text.splitlines() if line.startswith(acceptance_prefixes)
    )
    invalid = (
        missing_sections
        or missing_assertions
        or acceptance_tests != 12
        or "Status: completed on 2026-08-16" not in text
    )
    summary = {
        "acceptance_tests": acceptance_tests,
        "implementation_status": "complete-local-level-5-separate-level-6",
        "missing_assertions": missing_assertions,
        "missing_sections": missing_sections,
        "parent_record_set": "schuss-record-set-000012@1",
        "record_set": "schuss-record-set-000013@1",
        "required_sections": len(REQUIRED_SECTIONS),
        "schema_version": "task021-contract-validator-v1",
        "status": "invalid" if invalid else "valid",
    }
    print(json.dumps(summary, sort_keys=True), file=sys.stderr if invalid else sys.stdout)
    return 1 if invalid else 0


if __name__ == "__main__":
    raise SystemExit(main())
