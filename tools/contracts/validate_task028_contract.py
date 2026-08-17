#!/usr/bin/env python3
"""Read-only validator for the accepted Task 028 contract and decision."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs/tasks/028-twenty-item-direct-palette.md"
DECISION = ROOT / "contracts/task028/palette-curation-decision.md"


def validate() -> dict[str, object]:
    text = CONTRACT.read_text(encoding="utf-8")
    decision = DECISION.read_text(encoding="utf-8")
    sections = (
        "## Goal and why it exists", "## Dependencies and verified baseline", "## In scope",
        "## Out of scope", "## Inputs and deliverables", "## Exact counted palette",
        "## Evidence and lowering rules", "## Practical palette boundary",
        "## Validation cadence", "## Acceptance tests", "## Decisions Task 028 may make",
        "## Decisions Task 028 must not make", "## Activation state",
    )
    assertions = (
        "accepted and complete on 2026-08-17", "All fifteen acceptance tests pass",
        "exactly twenty", "fifteen safe promotions", "schuss-record-set-000020@1",
        "schuss-record-set-000021@1", "000097 through 000111", "000015 through 000029",
        "000033 through 000047", "000045 through 000059", "000060 through 000074",
        "component contracts 000022 through 000031", "backend `schuss-backend-000002@4`",
        "five Task 025", "seven already accepted", "levels 1-3 as `passed`",
        "levels 4-8 remain `not-run`", "two copied fresh-root reproductions",
        "staging, commit, or push", "Rings reverb", "000094", "000096",
    )
    normalized = " ".join(text.split())
    acceptance = text.split("## Acceptance tests", 1)[1].split("## Decisions Task 028 may make", 1)[0]
    decision_assertions = (
        "fifteen-item tranche", "000097", "000111", "The fixed baseline",
        "Mutable-derived", "Rings-derived reverb", "physical resonator 000096",
        "levels 1-3", "remain `not-run`",
    )
    missing_sections = [value for value in sections if value not in text]
    missing_assertions = [value for value in assertions if value not in normalized]
    missing_decision = [value for value in decision_assertions if value not in " ".join(decision.split())]
    tests = re.findall(r"^\d+\. ", acceptance, re.MULTILINE)
    valid = not missing_sections and not missing_assertions and not missing_decision and len(tests) == 15
    return {
        "schema_version": "task028-contract-validator-v1", "status": "valid" if valid else "invalid",
        "implementation_status": "accepted-complete", "required_sections": len(sections),
        "missing_sections": missing_sections, "missing_assertions": missing_assertions,
        "missing_decision_assertions": missing_decision, "acceptance_tests": len(tests),
        "baseline_count": 5, "addition_count": 15, "required_total": 20,
        "arm_java_axp_or_hardware_authorized": False, "git_or_publication_authorized": False,
    }


def main() -> int:
    try:
        result = validate()
    except (OSError, UnicodeError, ValueError, IndexError) as exc:
        print("Task 028 contract validation failed: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True), file=sys.stdout if result["status"] == "valid" else sys.stderr)
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
