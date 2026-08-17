#!/usr/bin/env python3
"""Run the frozen Task 028 generator in two copied roots and retain hashes."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/contracts"))

import validator_core as core  # noqa: E402


MANIFEST_PATH = "contracts/record-sets/task028-direct-palette-v1.json"
SUMMARY_ARTIFACTS = (
    "evidence/task028-completion-v1/balanced-palette-summary.json",
    "evidence/task028-completion-v1/remaining-gaps.json",
    "evidence/task028-completion-v1/validation-summary.json",
)


def _artifacts(root: Path) -> tuple[str, ...]:
    manifest = json.loads((root / MANIFEST_PATH).read_text(encoding="utf-8"))
    task_records = [item["portable_path"] for item in manifest["record_members"] if item["portable_path"].startswith("contracts/task028/")]
    task_schemas = [item["portable_path"] for item in manifest["schema_members"] if item["schema_version"] in {"task028-selection-packet-v0", "direct-operation-spec-v3", "palette-lowering-proof-v0"}]
    return tuple(sorted({MANIFEST_PATH, *SUMMARY_ARTIFACTS, *task_records, *task_schemas}))


def _hashes(root: Path) -> dict[str, str]:
    return {path: core.sha256_file(root / path) for path in _artifacts(root)}


def reproduce() -> dict[str, Any]:
    variants = (
        {"PYTHONHASHSEED": "1", "LC_ALL": "C", "TZ": "UTC"},
        {"PYTHONHASHSEED": "777", "LC_ALL": "C", "TZ": "Asia/Tokyo"},
    )
    runs = []
    with tempfile.TemporaryDirectory(prefix="schuss-task028-") as temporary:
        base = Path(temporary)
        for index, variant in enumerate(variants, start=1):
            copy_root = base / f"root-{index}"
            shutil.copytree(ROOT, copy_root, symlinks=True)
            environment = os.environ.copy()
            environment.update(variant)
            completed = subprocess.run(
                ["python3", "tools/contracts/generate_task028_records.py", "--check"],
                cwd=copy_root, env=environment, check=False,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            if completed.returncode != 0:
                raise ValueError(f"fresh-root Task 028 run {index} failed: {completed.stderr.strip()}")
            summary = json.loads(completed.stdout)
            runs.append({"variant": variant, "artifact_hashes": _hashes(copy_root), "record_set_reference": summary["record_set_reference"], "safe_selectable_total": summary["safe_selectable_total"]})
    if runs[0]["artifact_hashes"] != runs[1]["artifact_hashes"]:
        raise ValueError("Task 028 fresh-root artifact bytes differ")
    if runs[0]["record_set_reference"] != runs[1]["record_set_reference"]:
        raise ValueError("Task 028 fresh-root record-set references differ")
    return {
        "schema_version": "task028-fresh-root-reproduction-v1", "status": "passed", "run_count": 2,
        "runs": runs, "safe_selectable_total": 20,
        "source_artifact_generation_performed": False, "arm_compile_or_link_performed": False,
        "java_or_legacy_axp_performed": False, "device_or_hardware_performed": False,
        "realtime_or_audible_performed": False, "git_or_publication_performed": False,
    }


def check_retained() -> dict[str, Any]:
    path = ROOT / "evidence/task028-completion-v1/fresh-root-reproduction.json"
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        path = ROOT / "evidence/task028-completion-v1/fresh-root-reproduction.json"
        if args.check:
            result = check_retained()
        else:
            result = reproduce()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(core.canonical_json(result).encode("utf-8") + b"\n")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print("Task 028 fresh-root reproduction failed: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
