#!/usr/bin/env python3
"""Validate the frozen Task 040 Phase 1 readiness and allocation gate."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BUNDLE = Path("contracts/task040/phase1/implementation-bundle")
ALLOCATION = Path("contracts/task040/phase1/allocation.json")
STATE = Path("docs/governance/current-state.json")
TASK = Path("docs/tasks/040-cinderwheel-canonical-vertical-slice.md")
CLOSEOUT = Path("contracts/task040/phase1/CLOSEOUT.md")

BASELINE = "b21a0c4aa88488adde04446f35a7fd1d91b06a38"
PHASE1_REVIEW_COMMIT = "955084e581ebf21e979f039fb7bba088787b8f71"
TASK033_ACCEPTED = "0bf22b67b03862b2efecd9fed377118501bf5f8d"
PARENT_RECORD_SET = {
    "stable_id": "schuss-record-set-000033",
    "revision": 1,
    "content_hash": "sha256:01dc913b0d637573adda283f84985e7196ee7162b6f2eaadf76b1d3a2890b786",
    "path": "contracts/record-sets/ui-desktop-instrument-library-v1.json",
}

AUTHORITY_HASHES = {
    "contracts/task040/phase1/approved-cinderwheel-proposal-r0.2.md":
        "d9b3a50cde3c25a4db6324bd8d20f1a65eaefcbd1ac8e9e7a42adc80713b5e84",
    "research/prototypes/cinderwheel/prototype-index.json":
        "a15365efdbd731137a2d4b6d715114b920ecdf787086ba096b60b20dd341ab80",
    "research/prototypes/cinderwheel/PROMOTION_NEEDS.json":
        "9abd9c3464885ab07541dfcdf6c65a5a8c19ee282d3299deb654762bce6e01fc",
    "research/prototypes/cinderwheel/dsp-topology.json":
        "dff93dc5025be7280d2c565f9c388572acbe9707b13d967413cf471f21dc0b78",
    "research/prototypes/cinderwheel/fixtures/launch-control-3-test-map-v0.json":
        "d5df5f569bf37ed0dbd3e356a9c2f42ac01ed8364c2dc2bc6b07da2243e390f8",
}

EXPECTED_SCHEMAS = {
    "catalog-corpus-v7",
    "catalog-projection-v7",
    "performance-control-contract-v1",
    "performance-control-graph-v1",
    "performance-configuration-v1",
    "performance-event-stream-v0",
    "schuss-operation-request-v20",
    "schuss-operation-result-v20",
    "application-capability-description-v13",
    "implementation-fusion-v0",
    "binding-eligibility-v1",
    "backend-v1",
    "implementation-provider-v1",
}

EXPECTED_RECORDS = {
    ("catalog-corpus", "schuss-catalog-000001", 7, 2),
    ("catalog-selection", "schuss-catalog-selection-000001", 6, 2),
    ("catalog-family", "schuss-family-000108", 1, 2),
    ("component-contract", "schuss-component-contract-000032", 1, 2),
    *(("component-contract", f"schuss-component-contract-{number:06d}", 1, 2)
      for number in range(33, 42)),
    ("implementation-binding", "schuss-implementation-000169", 1, 2),
    ("dsp-graph", "schuss-graph-000007", 1, 2),
    ("dsp-graph", "schuss-graph-000008", 1, 2),
    ("instrument", "schuss-instrument-000006", 1, 2),
    ("performance-control-contract", "schuss-performance-control-contract-000003", 1, 2),
    ("performance-control-graph", "schuss-performance-control-graph-000002", 1, 2),
    ("performance-configuration", "schuss-performance-configuration-000003", 1, 2),
    ("project", "schuss-project-000035", 1, 2),
    ("implementation-fusion", "schuss-implementation-fusion-000001", 1, 3),
    ("binding-eligibility", "schuss-binding-eligibility-000055", 1, 3),
    ("source-release", "schuss-source-release-000006", 2, 3),
    ("implementation-provider", "schuss-implementation-provider-000001", 2, 3),
    ("backend", "schuss-backend-000003", 2, 3),
    ("object-collection", "schuss-object-collection-000001", 2, 3),
    (
        "implementation-availability-policy",
        "schuss-implementation-availability-policy-000001",
        2,
        3,
    ),
    ("build-request", "schuss-build-request-000008", 1, 3),
    *(("evidence-claim", f"schuss-evidence-claim-{number:06d}", 1, 2 if number < 84 else 3)
      for number in range(82, 87)),
}

EXPECTED_MAXIMA = {
    "family": 107,
    "component_contract": 31,
    "implementation": 168,
    "binding_eligibility": 54,
    "graph": 6,
    "instrument": 5,
    "performance_control_contract": 2,
    "performance_control_graph": 1,
    "performance_configuration": 2,
    "build_request": 7,
    "evidence_claim": 81,
    "project": 34,
    "record_set": 33,
}


def _json(root: Path, relative: str | Path) -> Any:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _git_blob(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def _review_state(head: str, origin_main: str) -> str | None:
    return {
        (BASELINE, BASELINE): "baseline-with-phase1-worktree",
        (PHASE1_REVIEW_COMMIT, BASELINE): "local-phase1-review-commit",
        (PHASE1_REVIEW_COMMIT, PHASE1_REVIEW_COMMIT):
            "published-phase1-review-commit",
    }.get((head, origin_main))


def _contains_unresolved_value(value: Any) -> bool:
    if isinstance(value, str):
        return "UNRESOLVED" in value.upper()
    if isinstance(value, list):
        return any(_contains_unresolved_value(item) for item in value)
    if isinstance(value, dict):
        return any(_contains_unresolved_value(item) for item in value.values())
    return False


def _maximum(values: list[str], pattern: str) -> int:
    expression = re.compile(pattern)
    numbers = [
        int(match.group(1))
        for value in values
        if (match := expression.fullmatch(value)) is not None
    ]
    return max(numbers, default=0)


def _parent_maxima(root: Path, allocation: dict[str, Any]) -> dict[str, int]:
    parent = _json(root, PARENT_RECORD_SET["path"])
    members = parent["record_members"]
    stable_ids = [item["stable_id"] for item in members]
    catalog = _json(root, allocation["parent_closure"]["catalog"]["path"])

    fixture_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in (root / "fixtures").rglob("*")
        if path.is_file() and path.suffix in {".json", ".md"}
    )
    project_ids = re.findall(r"schuss-project-[0-9]{6}", fixture_text)

    return {
        "family": _maximum(
            [item["family_id"] for item in catalog["family_additions"]],
            r"schuss-family-([0-9]{6})",
        ),
        "component_contract": _maximum(
            stable_ids, r"schuss-component-contract-([0-9]{6})"
        ),
        "implementation": _maximum(
            [item["implementation_id"] for item in catalog["implementation_additions"]],
            r"schuss-implementation-([0-9]{6})",
        ),
        "binding_eligibility": _maximum(
            stable_ids, r"schuss-binding-eligibility-([0-9]{6})"
        ),
        "graph": _maximum(stable_ids, r"schuss-graph-([0-9]{6})"),
        "instrument": _maximum(stable_ids, r"schuss-instrument-([0-9]{6})"),
        "performance_control_contract": _maximum(
            stable_ids, r"schuss-performance-control-contract-([0-9]{6})"
        ),
        "performance_control_graph": _maximum(
            stable_ids, r"schuss-performance-control-graph-([0-9]{6})"
        ),
        "performance_configuration": _maximum(
            stable_ids, r"schuss-performance-configuration-([0-9]{6})"
        ),
        "build_request": _maximum(stable_ids, r"schuss-build-request-([0-9]{6})"),
        "evidence_claim": _maximum(
            stable_ids, r"schuss-evidence-claim-([0-9]{6})"
        ),
        "project": _maximum(project_ids, r"schuss-project-([0-9]{6})"),
        "record_set": int(PARENT_RECORD_SET["stable_id"].rsplit("-", 1)[1]),
    }


def validate(root: Path = ROOT) -> dict[str, Any]:
    root = root.resolve()
    errors: list[str] = []
    head_commit: str | None = None
    origin_main_commit: str | None = None
    review_state: str | None = None

    try:
        allocation = _json(root, ALLOCATION)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return {"status": "invalid", "errors": [f"allocation: {exc}"]}

    if allocation.get("schema_version") != "task040-phase1-allocation-v1":
        errors.append("allocation schema version differs")
    if allocation.get("status") != "ready-for-phase-2-review":
        errors.append("allocation is not review-ready")

    try:
        if _git(root, "branch", "--show-current") != "main":
            errors.append("live branch is not main")
        head_commit = _git(root, "rev-parse", "HEAD")
        origin_main_commit = _git(root, "rev-parse", "origin/main")
        review_state = _review_state(head_commit, origin_main_commit)
        if review_state is None:
            _git(root, "merge-base", "--is-ancestor", PHASE1_REVIEW_COMMIT, head_commit)
            _git(
                root,
                "merge-base",
                "--is-ancestor",
                PHASE1_REVIEW_COMMIT,
                origin_main_commit,
            )
            review_state = "phase1-review-retained-by-descendants"
        if _git(root, "diff", "--cached", "--name-only"):
            errors.append("staged work exists during the Phase 1 review gate")
        _git(root, "merge-base", "--is-ancestor", TASK033_ACCEPTED, BASELINE)
        _git(root, "merge-base", "--is-ancestor", BASELINE, PHASE1_REVIEW_COMMIT)
    except (OSError, subprocess.CalledProcessError) as exc:
        errors.append(f"git state check failed: {exc}")

    for relative, expected in AUTHORITY_HASHES.items():
        path = root / relative
        try:
            actual = _sha256(path)
        except OSError as exc:
            errors.append(f"authority missing: {relative}: {exc}")
            continue
        if actual != expected:
            errors.append(f"authority hash differs: {relative}")

    proposal = root / "contracts/task040/phase1/approved-cinderwheel-proposal-r0.2.md"
    if proposal.is_file() and _git_blob(proposal.read_bytes()) != (
        "c075035b9c844eedd29f7f172e557cc985ad6d48"
    ):
        errors.append("approved proposal Git blob differs")

    try:
        parent = allocation["parent_closure"]["record_set"]
        if parent != PARENT_RECORD_SET:
            errors.append("parent record-set allocation differs")
        parent_document = _json(root, parent["path"])
        if (
            parent_document.get("record_set_id") != parent["stable_id"]
            or parent_document.get("revision") != parent["revision"]
            or parent_document.get("content_hash") != parent["content_hash"]
        ):
            errors.append("parent record-set file differs")
        for name, reference in allocation["parent_closure"].items():
            document = _json(root, reference["path"])
            if document.get("content_hash") != reference["content_hash"]:
                errors.append(f"parent closure hash differs: {name}")
    except (KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
        errors.append(f"parent closure is invalid: {exc}")

    schemas = {
        item.get("schema_version")
        for item in allocation.get("schemas", [])
        if isinstance(item, dict)
    }
    if schemas != EXPECTED_SCHEMAS:
        errors.append("schema allocation differs")

    records = {
        (item.get("kind"), item.get("stable_id"), item.get("revision"), item.get("phase"))
        for item in allocation.get("records", [])
        if isinstance(item, dict)
    }
    if records != EXPECTED_RECORDS:
        errors.append("stable record allocation differs")
    if len(records) != len(allocation.get("records", [])):
        errors.append("duplicate stable record allocation exists")

    try:
        maxima = _parent_maxima(root, allocation)
        if maxima != EXPECTED_MAXIMA:
            errors.append(f"live parent maxima differ: {maxima}")
        if allocation.get("observed_parent_maxima") != EXPECTED_MAXIMA:
            errors.append("recorded parent maxima differ")
    except (KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
        errors.append(f"parent maxima audit failed: {exc}")

    expected_record_sets = [
        {
            "stable_id": "schuss-record-set-000034",
            "revision": 1,
            "phase": 2,
            "parent": "schuss-record-set-000033@1",
            "path": "contracts/record-sets/task040-cinderwheel-semantic-v1.json",
        },
        {
            "stable_id": "schuss-record-set-000035",
            "revision": 1,
            "phase": 3,
            "parent": "schuss-record-set-000034@1",
            "path": "contracts/record-sets/task040-cinderwheel-native-v1.json",
        },
    ]
    if allocation.get("record_sets") != expected_record_sets:
        errors.append("record-set successor allocation differs")

    if allocation.get("operations") != [
        {
            "operation": "performance.events.apply",
            "request_schema": "schuss-operation-request-v20",
            "result_schema": "schuss-operation-result-v20",
            "effect_class": "process-local-state-write",
            "required_gates": [
                "exact-record-set",
                "exact-project-snapshot",
                "exact-session",
                "execute-intent",
            ],
            "phase": 2,
        },
        {
            "operation": "instrument.state.inspect",
            "request_schema": "schuss-operation-request-v20",
            "result_schema": "schuss-operation-result-v20",
            "effect_class": "read-only",
            "required_gates": [
                "exact-record-set",
                "exact-project-snapshot",
                "exact-session",
            ],
            "phase": 2,
        },
    ]:
        errors.append("operation allocation differs")

    try:
        state = _json(root, STATE)
        milestones = {
            (
                item.get("task_id"),
                item.get("phase"),
                item.get("status"),
                item.get("commit"),
            )
            for item in state.get("recent_completed_milestones", [])
            if isinstance(item, dict)
        }
        parked = (
            state.get("active_task") is None
            and state.get("next_candidate") is None
            and "040" in state.get("deferred_tasks", [])
            and ("040", 1, "complete-published", "955084e") in milestones
        )
        if not parked:
            errors.append("governance does not expose the Task 040 Phase 1 closeout")
        task_text = (root / TASK).read_text(encoding="utf-8")
        leading = "\n".join(task_text.splitlines()[:8]).lower()
        if "closed after phase 1" not in leading or "deferred" not in leading:
            errors.append("Task 040 leading status differs")
        closeout_text = (root / CLOSEOUT).read_text(encoding="utf-8")
        for phrase in (
            "Phase 2 was never activated",
            "not live reservations",
            "fresh audit",
            "No successor task is activated",
        ):
            if phrase not in closeout_text:
                errors.append(f"Task 040 closeout phrase missing: {phrase}")
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"governance check failed: {exc}")

    required_bundle = {
        "implementation-contract.json",
        "source-equivalence.json",
        "experiment.json",
        "state-matrix.md",
        "control-map.json",
        "validation-plan.json",
        "RESULTS.md",
        "GAPS.md",
    }
    try:
        actual_bundle = {path.name for path in (root / BUNDLE).iterdir() if path.is_file()}
        if not required_bundle.issubset(actual_bundle):
            errors.append("implementation bundle is incomplete")
        for name in required_bundle:
            path = root / BUNDLE / name
            content = path.read_text(encoding="utf-8")
            if path.suffix == ".json":
                if _contains_unresolved_value(json.loads(content)):
                    errors.append(f"bundle marker remains: {name}")
            elif "UNRESOLVED" in content.upper():
                errors.append(f"bundle marker remains: {name}")

        contract = _json(root, BUNDLE / "implementation-contract.json")
        source = _json(root, BUNDLE / "source-equivalence.json")
        experiment = _json(root, BUNDLE / "experiment.json")
        control = _json(root, BUNDLE / "control-map.json")
        plan = _json(root, BUNDLE / "validation-plan.json")
        state_matrix = (root / BUNDLE / "state-matrix.md").read_text(encoding="utf-8")

        if contract.get("status") != "ready" or contract.get("work_type") != "new-design":
            errors.append("implementation contract is not ready new-design")
        if source.get("status") != "not-applicable" or not source.get(
            "not_applicable_rationale"
        ):
            errors.append("new-design source-equivalence boundary differs")
        condition_ids = [item.get("id") for item in experiment.get("conditions", [])]
        if condition_ids != [
            "01-baseline",
            "02-undertow-f3",
            "03-primary-wake-ember-zero",
            "04-rotor-medium-clean",
            "05-rotor-high-bloom",
            "06-rotor-medium-corroded",
            "07-fixed-round-robin-medium",
        ]:
            errors.append("experiment conditions differ")
        if experiment.get("comparator_condition_id") != "07-fixed-round-robin-medium":
            errors.append("experiment comparator differs")
        surface = control.get("surface_assignments", [])
        semantic = control.get("semantic_bindings", [])
        if len(surface) != 24 or len(semantic) != 24:
            errors.append("control-map assignment count differs")
        encoder_cc = sorted(
            item["cc"] for item in surface if item.get("surface_kind") == "encoder"
        )
        button_cc = sorted(
            item["cc"] for item in surface if item.get("surface_kind") == "button"
        )
        if encoder_cc != list(range(20, 36)) or button_cc != list(range(40, 48)):
            errors.append("control-map CC allocation differs")
        if plan.get("status") != "ready":
            errors.append("validation plan is not ready")
        if "> Status: ready" not in state_matrix:
            errors.append("state matrix is not ready")
        for operation in (
            "Initialization",
            "Reset",
            "Panic",
            "Freeze or capture",
            "Mode change",
            "State recall",
            "Disconnect/reconnect",
            "Non-finite recovery",
        ):
            if f"| {operation} |" not in state_matrix:
                errors.append(f"state-matrix row missing: {operation}")
    except (KeyError, TypeError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"bundle validation failed: {exc}")

    for forbidden in (
        root / "contracts/task040/phase2",
        root / "contracts/task040/phase3",
        root / "fixtures/task040",
    ):
        if forbidden.exists():
            errors.append(f"Phase 2 or 3 implementation exists: {forbidden.relative_to(root)}")

    return {
        "schema_version": "task040-phase1-validation-summary-v1",
        "status": "valid" if not errors else "invalid",
        "baseline_commit": BASELINE,
        "phase1_review_commit": PHASE1_REVIEW_COMMIT,
        "head_commit": head_commit,
        "origin_main_commit": origin_main_commit,
        "review_state": review_state,
        "parent_record_set": "schuss-record-set-000033@1",
        "allocated_semantic_record_set": "schuss-record-set-000034@1",
        "allocated_native_record_set": "schuss-record-set-000035@1",
        "internal_graph_node_count": 9,
        "control_assignment_count": 24,
        "experiment_condition_count": 7,
        "task_status": "deferred-after-phase1",
        "phase2_implemented": False,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    arguments = parser.parse_args()
    summary = validate(arguments.repo_root)
    print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    return 0 if summary["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
