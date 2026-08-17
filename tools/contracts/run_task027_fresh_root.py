#!/usr/bin/env python3
"""Run the frozen Task 027 generator in two copied roots and retain hashes."""

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


ARTIFACTS = (
    "catalog/reviews/task027-mutable-sources-v1/candidates.jsonl",
    "contracts/record-sets/task027-mutable-catalog-v1.json",
    "contracts/task027/catalog-corpus-v4.json",
    "contracts/task027/catalog-selection-r3.json",
    "contracts/task027/catalog-source-review.json",
    "evidence/task027-completion-v1/validation-summary.json",
    "schemas/catalog-corpus-v4.schema.json",
    "schemas/catalog-projection-v4.schema.json",
    "schemas/catalog-source-review-v0.schema.json",
)


def _hashes(root: Path) -> dict[str, str]:
    return {path: core.sha256_file(root / path) for path in ARTIFACTS}


def reproduce() -> dict[str, Any]:
    variants = (
        {"PYTHONHASHSEED": "1", "LC_ALL": "C", "TZ": "UTC"},
        {"PYTHONHASHSEED": "777", "LC_ALL": "C", "TZ": "Asia/Tokyo"},
    )
    runs = []
    with tempfile.TemporaryDirectory(prefix="schuss-task027-") as temporary:
        base = Path(temporary)
        for index, variant in enumerate(variants, start=1):
            copy_root = base / f"root-{index}"
            shutil.copytree(ROOT, copy_root, symlinks=True)
            environment = os.environ.copy()
            environment.update(variant)
            completed = subprocess.run(
                ["python3", "tools/contracts/generate_task027_records.py", "--check"],
                cwd=copy_root,
                env=environment,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if completed.returncode != 0:
                raise ValueError(
                    f"fresh-root Task 027 run {index} failed: {completed.stderr.strip()}"
                )
            summary = json.loads(completed.stdout)
            runs.append(
                {
                    "variant": variant,
                    "artifact_hashes": _hashes(copy_root),
                    "projection_sha256": summary["projection_sha256"],
                    "record_set_reference": summary["record_set_reference"],
                }
            )
    if runs[0]["artifact_hashes"] != runs[1]["artifact_hashes"]:
        raise ValueError("Task 027 fresh-root artifact bytes differ")
    if runs[0]["projection_sha256"] != runs[1]["projection_sha256"]:
        raise ValueError("Task 027 fresh-root derived projections differ")
    if runs[0]["record_set_reference"] != runs[1]["record_set_reference"]:
        raise ValueError("Task 027 fresh-root record-set references differ")
    return {
        "schema_version": "task027-fresh-root-reproduction-v1",
        "status": "passed", "run_count": 2,
        "source_authority": {
            "source_id": "patcher",
            "commit": "08d3e6e1e2b61230308c20a15ded58ffdaf4656c",
            "working_tree_bytes_used": False,
        },
        "runs": runs,
        "compiler_or_build_performed": False,
        "java_or_legacy_axp_performed": False,
        "hardware_or_publication_performed": False,
    }


def check_retained() -> dict[str, Any]:
    path = ROOT / "evidence/task027-completion-v1/fresh-root-reproduction.json"
    if not path.is_file():
        raise ValueError("Task 027 fresh-root evidence is missing")
    result = json.loads(path.read_text(encoding="utf-8"))
    if result.get("schema_version") != "task027-fresh-root-reproduction-v1":
        raise ValueError("Task 027 fresh-root evidence schema is stale")
    if result.get("status") != "passed" or result.get("run_count") != 2:
        raise ValueError("Task 027 fresh-root evidence did not retain two passing runs")
    authority = result.get("source_authority")
    if authority != {
        "source_id": "patcher",
        "commit": "08d3e6e1e2b61230308c20a15ded58ffdaf4656c",
        "working_tree_bytes_used": False,
    }:
        raise ValueError("Task 027 fresh-root source authority is stale")
    if any(
        result.get(flag) is not False
        for flag in (
            "compiler_or_build_performed",
            "java_or_legacy_axp_performed",
            "hardware_or_publication_performed",
        )
    ):
        raise ValueError("Task 027 fresh-root evidence exceeds the task boundary")
    expected_hashes = _hashes(ROOT)
    runs = result.get("runs")
    if not isinstance(runs, list) or len(runs) != 2:
        raise ValueError("Task 027 fresh-root run list is invalid")
    for run in runs:
        if run.get("artifact_hashes") != expected_hashes:
            raise ValueError("Task 027 fresh-root artifact evidence is stale")
    summary = json.loads(
        (ROOT / "evidence/task027-completion-v1/validation-summary.json").read_text(
            encoding="utf-8"
        )
    )
    expected_projection = summary["projection_sha256"]
    expected_record_set = summary["record_set_reference"]
    if any(run.get("projection_sha256") != expected_projection for run in runs):
        raise ValueError("Task 027 fresh-root projection evidence is stale")
    if any(run.get("record_set_reference") != expected_record_set for run in runs):
        raise ValueError("Task 027 fresh-root record-set evidence is stale")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        path = ROOT / "evidence/task027-completion-v1/fresh-root-reproduction.json"
        if args.check:
            result = check_retained()
        else:
            result = reproduce()
            payload = core.canonical_json(result).encode("utf-8") + b"\n"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print("Task 027 fresh-root reproduction failed: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
