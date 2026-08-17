#!/usr/bin/env python3
"""Read-only validator for the revised fail-closed Task 025 contract."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs/tasks/025-direct-compiler-core-library-tranche.md"
BOUNDARY = ROOT / "contracts/task025/reverb-allocation-boundary.md"


REQUIRED = (
    "## Goal and why it exists",
    "## Dependencies and exact authority",
    "## In scope",
    "## Out of scope",
    "## Inputs and deliverables",
    "## Semantic rules",
    "## Reverb unsupported rule",
    "## Diagnostics and evidence boundary",
    "## Validation cadence",
    "## Acceptance tests",
    "## Decisions Task 025 may make",
    "## Decisions Task 025 must not make",
    "## Readiness and activation state",
    "schuss-core-selection-000002@1",
    "schuss-record-set-000016@1",
    "schuss-record-set-000017@1",
    "schuss-graph-000004@1",
    "schuss-build-request-000004@3",
    "schuss-direct-operation-spec-000008",
    "schuss-direct-operation-spec-000012",
    "schuss-implementation-000090",
    "schuss-implementation-000094",
    "schuss-binding-eligibility-000027",
    "schuss-binding-eligibility-000032",
    "schuss-evidence-claim-000038",
    "schuss-evidence-claim-000043",
    "65,536-byte initialization span",
    "Levels 3-8 remain `not-run`",
    "Two fresh roots",
    "Java",
    "`.axp`",
    "fail closed",
    "must not make",
    "staging, commit, push",
)


def validate() -> dict[str, object]:
    text = CONTRACT.read_text(encoding="utf-8")
    boundary = BOUNDARY.read_text(encoding="utf-8")
    missing = [value for value in REQUIRED if value not in text]
    if missing:
        raise ValueError("missing Task 025 contract authority: " + ", ".join(missing))
    acceptance = text.split("## Acceptance tests", 1)[1].split(
        "## Decisions Task 025 may make", 1
    )[0]
    numbered = [line for line in acceptance.splitlines() if line[:1].isdigit()]
    if [line.split(".", 1)[0] for line in numbered] != [str(i) for i in range(1, 16)]:
        raise ValueError("Task 025 must define exactly fifteen ordered acceptance tests")
    if text.count("`schuss-implementation-000090`") < 1 or text.count(
        "`schuss-implementation-000095`"
    ) < 1:
        raise ValueError("Task 025 native implementation allocation is incomplete")
    boundary_required = (
        "sdram_malloc(32768)",
        "Initialization therefore clears 32,768 `uint16_t` elements",
        "or 65,536",
        "Task 025 must not create a native reverb realization",
        "The reverb path stays deterministically unsupported",
        "Task 026 cannot claim empty-workspace-to-ELF completion",
    )
    boundary_missing = [value for value in boundary_required if value not in boundary]
    if boundary_missing:
        raise ValueError(
            "missing Task 025 reverb boundary authority: "
            + ", ".join(boundary_missing)
        )
    prohibited_allocations = (
        "`schuss-direct-operation-spec-000013` through",
        "`schuss-implementation-000090` through `schuss-implementation-000095`",
        "Two fresh authenticated roots produce byte-identical portable",
    )
    present = [value for value in prohibited_allocations if value in text]
    if present:
        raise ValueError("stale all-eight-node authority remains: " + ", ".join(present))
    return {
        "schema_version": "task025-contract-validator-result-v2",
        "status": "valid",
        "acceptance_tests": len(numbered),
        "selected_subjects": 8,
        "new_direct_operations": 5,
        "supported_graph_subjects": 7,
        "unsupported_graph_subjects": 1,
        "fresh_builds_required": 0,
        "highest_evidence_level": 2,
        "task026_activation": "blocked-by-reverb-and-authored-graph-seam",
        "device_actions_authorized": False,
        "git_actions_authorized": False,
    }


def main() -> int:
    try:
        result = validate()
    except (OSError, ValueError) as exc:
        print("Task 025 contract validation failed: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
