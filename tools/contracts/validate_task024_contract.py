#!/usr/bin/env python3
"""Read-only validator for the accepted Task 024 contract."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs/tasks/024-complete-catalog-coverage-and-deterministic-curation.md"


def validate() -> dict[str, object]:
    text = CONTRACT.read_text(encoding="utf-8")
    normalized = " ".join(text.split())
    sections = (
        "## Goal and why it exists",
        "## Dependencies and verified baseline",
        "## In scope",
        "## Out of scope",
        "## Inputs and deliverables",
        "## Current-source and curation rules",
        "## Task 025 selection boundary",
        "## Validation cadence",
        "## Acceptance tests",
        "## Decisions Task 024 may make",
        "## Decisions Task 024 must not make",
        "## Readiness and activation state",
    )
    assertions = (
        "accepted by the user and completed under the resumed overnight Tasks 024-026 goal",
        "primary candidate reference for Schuss catalog curation",
        "immutable provenance, lineage, and gap evidence",
        "668 `.axo` files, 835 normal definitions, 666 canonical base references, and 19 `.axs` compounds",
        "Twenty reviewed family records",
        "`schuss-family-000041` through `schuss-family-000060`",
        "schuss-implementation-000061",
        "schuss-implementation-000089",
        "schuss-catalog-000001@3",
        "schuss-catalog-selection-000001@2",
        "schuss-current-ksoloti-corpus-000001@1",
        "schuss-record-set-000016@1",
        "schuss-record-set-000015@1",
        "schuss-core-selection-000002@1",
        "exactly the eight contract references",
        "`prioritization-only` and non-authoritative for product backlog",
        "Levels 3-8 remain `not-run`",
        "final aggregate contract/inventory/catalog suite passes",
        "passed all fifteen revised acceptance tests",
        "Staging, commit, push, release",
    )
    acceptance = text.split("## Acceptance tests", 1)[1].split(
        "## Decisions Task 024 may make", 1
    )[0]
    missing_sections = [item for item in sections if item not in text]
    missing_assertions = [item for item in assertions if item not in normalized]
    tests = re.findall(r"^\d+\. ", acceptance, re.MULTILINE)
    valid = not missing_sections and not missing_assertions and len(tests) == 15
    return {
        "schema_version": "task024-contract-validator-v1",
        "status": "valid" if valid else "invalid",
        "implementation_status": "accepted-complete",
        "required_sections": len(sections),
        "missing_sections": missing_sections,
        "missing_assertions": missing_assertions,
        "acceptance_tests": len(tests),
        "frozen_observations": 3602,
        "additional_family_count": 20,
        "current_ksoloti_candidate_count": 685,
        "complete_variant_implementation_range": [61, 89],
        "reserved_family_range": [41, 60],
        "reserved_record_set": "schuss-record-set-000016@1",
        "compiler_or_build_authorized": False,
        "git_or_hardware_actions_authorized": False,
    }


def main() -> int:
    try:
        result = validate()
    except (OSError, UnicodeError, ValueError, IndexError) as exc:
        print("Task 024 contract validation failed: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True), file=sys.stdout if result["status"] == "valid" else sys.stderr)
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
