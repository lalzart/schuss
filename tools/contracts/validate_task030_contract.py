#!/usr/bin/env python3
"""Read-only validator for the active Task 030 contract and curation decision."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs/tasks/030-complete-mutable-catalog-and-object-cli.md"
DECISION = ROOT / "contracts/task030/mutable-catalog-curation.md"


def validate() -> dict[str, object]:
    text = CONTRACT.read_text(encoding="utf-8")
    decision = DECISION.read_text(encoding="utf-8")
    sections = (
        "## Goal and why it exists",
        "## Exact baseline",
        "## In scope",
        "## Out of scope",
        "## Inputs and deliverables",
        "## Curation rules",
        "## Validation cadence and acceptance tests",
        "## Decisions Task 030 may make",
        "## Decisions Task 030 must not make",
        "## Activation state",
    )
    assertions = (
        "56 Task 027 entries",
        "16 extended-library entries",
        "schuss-record-set-000022@1",
        "schuss-record-set-000023@1",
        "50 new catalog implementation records",
        "schuss-implementation-000112@1",
        "000161@1",
        "schuss-family-000061@1",
        "catalog.implementations.search",
        "schuss catalog objects",
        "levels 1-2 only",
        "one copied-root/fresh-process reproduction",
        "full contract/inventory/catalog aggregate runs once",
        "staging, commit, push",
    )
    normalized = " ".join(text.split())
    acceptance = text.split(
        "## Validation cadence and acceptance tests", 1
    )[1].split("## Decisions Task 030 may make", 1)[0]
    decision_assertions = (
        "six existing mappings",
        "remaining 50",
        "16 unattributed",
        "schuss-family-000010@1",
        "schuss-family-000031@1",
        "Families `000061`-`000070`",
        "Families `000092`-`000107`",
        "schuss-implementation-000112@1",
        "schuss-implementation-000161@1",
        "structural/catalog provenance evidence only",
    )
    missing_sections = [value for value in sections if value not in text]
    missing_assertions = [value for value in assertions if value not in normalized]
    missing_decision = [
        value for value in decision_assertions if value not in " ".join(decision.split())
    ]
    tests = re.findall(r"^\d+\. ", acceptance, re.MULTILINE)
    valid = (
        not missing_sections
        and not missing_assertions
        and not missing_decision
        and len(tests) == 15
    )
    return {
        "schema_version": "task030-contract-validator-v1",
        "status": "valid" if valid else "invalid",
        "implementation_status": "accepted-complete",
        "required_sections": len(sections),
        "missing_sections": missing_sections,
        "missing_assertions": missing_assertions,
        "missing_decision_assertions": missing_decision,
        "acceptance_tests": len(tests),
        "attributed_entry_count": 56,
        "new_implementation_count": 50,
        "compiler_build_hardware_or_publication_authorized": False,
    }


def main() -> int:
    try:
        result = validate()
    except (OSError, UnicodeError, ValueError, IndexError) as exc:
        print("Task 030 contract validation failed: " + str(exc), file=sys.stderr)
        return 1
    stream = sys.stdout if result["status"] == "valid" else sys.stderr
    print(json.dumps(result, sort_keys=True), file=stream)
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
