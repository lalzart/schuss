#!/usr/bin/env python3
"""Validate the retained fail-closed Task 025 completion boundary."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_ROOT = ROOT / "evidence/task025-completion-v1"
SUMMARY = EVIDENCE_ROOT / "validation-summary.json"
PLAN = EVIDENCE_ROOT / "compiler-plan-result.json"
REPORT = EVIDENCE_ROOT / "completion-report.md"
FRESH = EVIDENCE_ROOT / "fresh-root-reproduction.json"
RECORD_SET = ROOT / "contracts/record-sets/task025-direct-core-v1.json"
GOLDENS = EVIDENCE_ROOT / "semantic-goldens.json"


def main() -> int:
    try:
        summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
        plan = json.loads(PLAN.read_text(encoding="utf-8"))
        fresh = json.loads(FRESH.read_text(encoding="utf-8"))
        report = " ".join(REPORT.read_text(encoding="utf-8").split())
        actions = summary.get("actions", {})
        valid = (
            summary.get("status") == "valid"
            and summary.get("implementation_status") == "complete-fail-closed-partial-tranche"
            and summary.get("record_set_reference", {}).get("record_set_id") == "schuss-record-set-000017"
            and summary.get("new_direct_operation_count") == 5
            and summary.get("new_native_binding_count") == 5
            and summary.get("selected_graph_subject_count") == 7
            and summary.get("unsupported_graph_subject_count") == 1
            and summary.get("passed_level2_promotion_claim_count") == 5
            and summary.get("failed_level2_reverb_claim_count") == 1
            and [item.get("status") for item in summary.get("compiler_plan_evidence_levels", ())]
            == ["passed", "failed"] + ["not-run"] * 6
            and summary.get("compiler_plan_status") == "unsupported"
            and summary.get("sole_unsupported_node") == "graph-node-000004"
            and not any(actions.values())
            and plan.get("status") == "unsupported"
            and plan.get("value", {}).get("status") == "unsupported"
            and [item.get("code") for item in plan.get("value", {}).get("diagnostics", ())]
            == ["COMPILER_BINDING_UNSUPPORTED"]
            and summary.get("record_set_byte_sha256") == hashlib.sha256(RECORD_SET.read_bytes()).hexdigest()
            and summary.get("semantic_goldens_byte_sha256") == hashlib.sha256(GOLDENS.read_bytes()).hexdigest()
            and summary.get("compiler_plan_byte_sha256") == hashlib.sha256(PLAN.read_bytes()).hexdigest()
            and fresh.get("status") == "identical"
            and fresh.get("fresh_root_count") == 2
            and fresh.get("record_set_byte_sha256") == summary.get("record_set_byte_sha256")
            and fresh.get("semantic_goldens_byte_sha256") == summary.get("semantic_goldens_byte_sha256")
            and fresh.get("compiler_plan_byte_sha256") == summary.get("compiler_plan_byte_sha256")
            and "five component promotions pass level 2" in report.lower()
            and "complete graph records level 1 passed, level 2 failed" in report.lower()
            and "No ambient discovery, Java, `.axp`, build handler" in report
        )
    except (OSError, UnicodeError, ValueError, KeyError) as exc:
        print("Task 025 completion validation failed: " + str(exc), file=sys.stderr)
        return 1
    result = {
        "schema_version": "task025-completion-validator-v1",
        "status": "valid" if valid else "invalid",
        "implementation_status": summary.get("implementation_status", "incomplete"),
        "record_set": "schuss-record-set-000017@1",
        "selected_graph_subjects": summary.get("selected_graph_subject_count"),
        "unsupported_graph_subjects": summary.get("unsupported_graph_subject_count"),
        "complete_graph_highest_passed_evidence": "level-1" if valid else "not-established",
        "task026_activation": "blocked-by-reverb-and-authored-graph-seam",
    }
    print(json.dumps(result, sort_keys=True), file=sys.stdout if valid else sys.stderr)
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
