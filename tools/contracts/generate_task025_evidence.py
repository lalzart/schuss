#!/usr/bin/env python3
"""Generate deterministic retained evidence for the fail-closed Task 025 tranche."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/contracts")]

from packages.schuss_core.control_plane import (  # noqa: E402
    dispatch_operation,
    load_repository_context,
)

import validator_core as core  # noqa: E402


RECORD_SET = ROOT / "contracts/record-sets/task025-direct-core-v1.json"
EVIDENCE_ROOT = ROOT / "evidence/task025-completion-v1"


def _ref(record: dict[str, Any], field: str) -> dict[str, Any]:
    return {
        field: record[field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def generated() -> tuple[dict[str, bytes], dict[str, Any]]:
    context = load_repository_context(record_set_path=RECORD_SET)
    requests = [
        item for item in context.records["request"]
        if item["build_request_id"] == "schuss-build-request-000004"
        and item["revision"] == 3
    ]
    if len(requests) != 1:
        raise ValueError("Task 025 build request does not resolve exactly once")
    request = requests[0]
    operation = {
        "schema_version": "schuss-operation-request-v4",
        "canonical_profile": "schuss-canonical-json-v1",
        "operation": "build.plan",
        "payload": {"build_request_reference": _ref(request, "build_request_id")},
    }
    first = dispatch_operation(operation, context)
    second = dispatch_operation(operation, context)
    if core.canonical_json(first) != core.canonical_json(second):
        raise ValueError("Task 025 compiler plan is not deterministic")
    if first.get("status") != "unsupported" or first.get("value", {}).get("status") != "unsupported":
        raise ValueError("Task 025 compiler plan did not fail closed as unsupported")
    plan = first["value"]
    resolution_artifacts = [
        item for item in plan["artifacts"]
        if item["descriptor"]["artifact_kind"] == "resolution-plan"
    ]
    if len(resolution_artifacts) != 1 or len(plan["artifacts"]) != 1:
        raise ValueError("Task 025 plan emitted an artifact beyond the resolution plan")
    traces = resolution_artifacts[0]["payload"]["traces"]
    if [item["status"] for item in traces].count("selected") != 7:
        raise ValueError("Task 025 plan did not select exactly seven graph nodes")
    rejected = [item for item in traces if item["status"] == "unsupported"]
    if len(rejected) != 1 or rejected[0]["node_id"] != "graph-node-000004":
        raise ValueError("Task 025 reverb node is not the sole unsupported subject")
    evidence_statuses = [item["status"] for item in plan["evidence_levels"]]
    if evidence_statuses != ["passed", "failed"] + ["not-run"] * 6:
        raise ValueError("Task 025 compiler-plan evidence boundary differs")

    plan_bytes = core.canonical_json(first).encode("utf-8") + b"\n"
    record_set_bytes = RECORD_SET.read_bytes()
    golden_bytes = (EVIDENCE_ROOT / "semantic-goldens.json").read_bytes()
    summary = {
        "schema_version": "task025-completion-summary-v1",
        "status": "valid",
        "implementation_status": "complete-fail-closed-partial-tranche",
        "record_set_reference": context.record_set_reference,
        "parent_record_set": "schuss-record-set-000016@1",
        "selection_packet": "schuss-core-selection-000002@1",
        "source_graph": "schuss-graph-000004@1",
        "new_direct_operation_count": 5,
        "new_native_binding_count": 5,
        "selected_graph_subject_count": 7,
        "unsupported_graph_subject_count": 1,
        "passed_level2_promotion_claim_count": 5,
        "failed_level2_reverb_claim_count": 1,
        "compiler_plan_evidence_levels": plan["evidence_levels"],
        "compiler_plan_status": "unsupported",
        "sole_unsupported_node": "graph-node-000004",
        "record_set_byte_sha256": hashlib.sha256(record_set_bytes).hexdigest(),
        "semantic_goldens_byte_sha256": hashlib.sha256(golden_bytes).hexdigest(),
        "compiler_plan_byte_sha256": hashlib.sha256(plan_bytes).hexdigest(),
        "actions": {
            "ambient_discovery": False,
            "java": False,
            "legacy_axp": False,
            "build_handler": False,
            "backend_lowering": False,
            "generated_cpp": False,
            "arm_compile_link": False,
            "device": False,
            "real_time": False,
            "audible": False,
            "git_or_publication": False,
        },
    }
    report = """# Task 025 completion report

Task 025 completed the bounded fail-closed direct-semantics tranche. Five exact
source subjects now have target-independent operation specifications, distinct
native identities, semantic vectors, and passed level-2 promotion claims: saw,
PWM, exponential smoothing, audio soft clipping, and interpolated VCA. The
accepted Task 016 crossfader and audio-output realizations are reused, so the
ordinary compiler plan selects seven of the eight exact graph nodes.

The selected Rings-derived reverb remains in the immutable Task 024 packet and
Task 017 provenance. Its pinned wrapper allocates 32,768 bytes while its exact
header clears 32,768 `uint16_t` elements, or 65,536 bytes. Task 025 therefore
created no reverb operation, native realization, supported eligibility, build
handler, or ARM evidence. The exact compiler plan rejects only reverb at
implementation resolution and emits only a resolution-plan artifact.

Evidence remains deliberately split. The five component promotions pass level
2; the reverb claim fails level 2, so the complete graph records level 1 passed,
level 2 failed, and levels 3 through 8 not run. This is useful compiler-front-half
and semantic coverage, not an executable graph or a claim about device behavior,
resource safety, real-time behavior, stability, or sound.

No ambient discovery, Java, `.axp`, build handler, backend lowering, generated
C++, ARM compile/link, device, real-time, audible, Git, or publication action was
performed.
"""
    files = {
        "compiler-plan-result.json": plan_bytes,
        "validation-summary.json": core.canonical_json(summary).encode("utf-8") + b"\n",
        "completion-report.md": report.encode("utf-8"),
    }
    return files, summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        files, summary = generated()
        stale = [
            name for name, payload in files.items()
            if not (EVIDENCE_ROOT / name).is_file()
            or (EVIDENCE_ROOT / name).read_bytes() != payload
        ]
        if args.check and stale:
            raise ValueError("generated Task 025 evidence is stale: " + ", ".join(sorted(stale)))
        if not args.check:
            EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)
            for name, payload in files.items():
                (EVIDENCE_ROOT / name).write_bytes(payload)
    except (OSError, ValueError) as exc:
        print("Task 025 evidence generation failed: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
