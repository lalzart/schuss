#!/usr/bin/env python3
"""Check or historically reproduce the frozen Task 028 evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/contracts"))

import validator_core as core  # noqa: E402
import historical_reproduction  # noqa: E402
import retained_evidence  # noqa: E402


MANIFEST_PATH = "contracts/record-sets/task028-direct-palette-v1.json"
SUMMARY_ARTIFACTS = (
    "evidence/task028-completion-v1/balanced-palette-summary.json",
    "evidence/task028-completion-v1/remaining-gaps.json",
    "evidence/task028-completion-v1/validation-summary.json",
)
EVIDENCE_ROOT = ROOT / "evidence/task028-completion-v1"
HISTORICAL_COMMIT = "5e57d29d729af8af36e90745bec9188256558680"


def _artifacts(root: Path) -> tuple[str, ...]:
    manifest = json.loads((root / MANIFEST_PATH).read_text(encoding="utf-8"))
    task_records = [item["portable_path"] for item in manifest["record_members"] if item["portable_path"].startswith("contracts/task028/")]
    task_schemas = [item["portable_path"] for item in manifest["schema_members"] if item["schema_version"] in {"task028-selection-packet-v0", "direct-operation-spec-v3", "palette-lowering-proof-v0"}]
    return tuple(sorted({MANIFEST_PATH, *SUMMARY_ARTIFACTS, *task_records, *task_schemas}))


def _hashes(root: Path) -> dict[str, str]:
    return {path: core.sha256_file(root / path) for path in _artifacts(root)}


def check_retained() -> dict[str, Any]:
    retained_evidence.check_closure(
        EVIDENCE_ROOT,
        repository_root=ROOT,
        anchor_commit=HISTORICAL_COMMIT,
    )
    path = EVIDENCE_ROOT / "fresh-root-reproduction.json"
    result = json.loads(path.read_text(encoding="utf-8"))
    if result.get("schema_version") != "task028-fresh-root-reproduction-v1" or result.get("status") != "passed" or result.get("run_count") != 2:
        raise ValueError("Task 028 retained fresh-root result is absent or stale")
    if result.get("safe_selectable_total") != 20:
        raise ValueError("Task 028 retained palette total is stale")
    forbidden = (
        "source_artifact_generation_performed", "arm_compile_or_link_performed",
        "java_or_legacy_axp_performed", "device_or_hardware_performed",
        "realtime_or_audible_performed", "git_or_publication_performed",
    )
    if any(result.get(key) is not False for key in forbidden):
        raise ValueError("Task 028 fresh-root evidence exceeds the task boundary")
    expected = _hashes(ROOT)
    runs = result.get("runs")
    if not isinstance(runs, list) or len(runs) != 2:
        raise ValueError("Task 028 fresh-root run list is invalid")
    if any(run.get("artifact_hashes") != expected or run.get("safe_selectable_total") != 20 for run in runs):
        raise ValueError("Task 028 fresh-root artifact evidence is stale")
    return result


def reproduce_historical() -> dict[str, Any]:
    return historical_reproduction.reproduce_summary(
        repository_root=ROOT,
        completion_commit=HISTORICAL_COMMIT,
        runner_path=Path("tools/contracts/run_task028_fresh_root.py"),
        retained_summary=check_retained(),
        report_schema_version="task028-historical-reproduction-v1",
        runner_arguments=(),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--reproduce", action="store_true")
    args = parser.parse_args()
    try:
        if args.check:
            result = check_retained()
        else:
            result = reproduce_historical()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print("Task 028 fresh-root reproduction failed: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
