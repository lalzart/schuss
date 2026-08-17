#!/usr/bin/env python3
"""Read-only validator for the accepted Task 027 contract and decision."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs/tasks/027-mutable-instruments-catalog-provenance.md"
DECISION = ROOT / "contracts/task027/mutable-curation-decision.md"
ADR = ROOT / "docs/decisions/0015-retarget-task-027-to-mutable-catalog-provenance.md"


def validate() -> dict[str, object]:
    text = CONTRACT.read_text(encoding="utf-8")
    decision = DECISION.read_text(encoding="utf-8")
    adr = ADR.read_text(encoding="utf-8")
    sections = (
        "## Goal and why it exists",
        "## Dependencies and verified baseline",
        "## In scope",
        "## Out of scope",
        "## Inputs and deliverables",
        "## Curation and provenance rules",
        "## Validation cadence",
        "## Acceptance tests",
        "## Decisions Task 027 may make",
        "## Decisions Task 027 must not make",
        "## Activation state",
    )
    assertions = (
        "accepted and complete on 2026-08-17",
        "All fifteen acceptance tests passed",
        "schuss-record-set-000019@1",
        "schuss-record-set-000020@1",
        "schuss-implementation-000096@1",
        "schuss-family-000010@1",
        "sixty reviewed catalog families",
        "thirteen function-first categories",
        "exactly fifty-three",
        "exactly the Rings physical resonator, Grids-derived",
        "mutable-instruments-derived",
        "Warps `wrps`",
        "build-failed",
        "levels 3-8 are `not-run`",
        "two copied fresh roots",
        "one final aggregate suite",
        "staging, commit, push",
    )
    acceptance = text.split("## Acceptance tests", 1)[1].split(
        "## Decisions Task 027 may make", 1
    )[0]
    missing_sections = [value for value in sections if value not in text]
    normalized = " ".join(text.split())
    missing_assertions = [value for value in assertions if value not in normalized]
    decision_assertions = (
        "nineteen extended objects",
        "fifty-three variants",
        "The other forty-eight remain tagged candidates",
        "does not currently link",
        "Compiler, ARM, connected-device, real-time, audible",
    )
    missing_decision = [value for value in decision_assertions if value not in " ".join(decision.split())]
    adr_assertions = (
        "Supersedes: ADR 0014 only for the unstarted Task 027 assignment",
        "application sessions, jobs, and diagnostics outcome is deferred",
        "preserve the sixty reviewed catalog families",
    )
    missing_adr = [value for value in adr_assertions if value not in " ".join(adr.split())]
    tests = re.findall(r"^\d+\. ", acceptance, re.MULTILINE)
    valid = not missing_sections and not missing_assertions and not missing_decision and not missing_adr and len(tests) == 15
    return {
        "schema_version": "task027-contract-validator-v1",
        "status": "valid" if valid else "invalid",
        "implementation_status": "accepted-complete",
        "required_sections": len(sections),
        "missing_sections": missing_sections,
        "missing_assertions": missing_assertions,
        "missing_decision_assertions": missing_decision,
        "missing_adr_assertions": missing_adr,
        "acceptance_tests": len(tests),
        "reviewed_family_count": 60,
        "extended_object_count": 19,
        "factory_mutable_candidate_count": 53,
        "compiler_or_build_authorized": False,
        "git_or_hardware_actions_authorized": False,
    }


def main() -> int:
    try:
        result = validate()
    except (OSError, UnicodeError, ValueError, IndexError) as exc:
        print("Task 027 contract validation failed: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True), file=sys.stdout if result["status"] == "valid" else sys.stderr)
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
