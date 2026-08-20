#!/usr/bin/env python3
"""Reproduce frozen Task 027 output from its original Git commit."""

from __future__ import annotations

import argparse
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
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
HISTORICAL_COMMIT = "90704b234e2a418d64a71e0a34c2b9ca98d48420"
SOURCE_CONFIGURATION = Path("catalog/sources.local.yml")


def _hashes(root: Path) -> dict[str, str]:
    return {path: core.sha256_file(root / path) for path in ARTIFACTS}


def _materialize_historical_root(
    destination: Path, source_configuration: Path
) -> None:
    """Extract the accepted Task 027 tree and add only its ignored source map."""
    source_configuration = (
        source_configuration
        if source_configuration.is_absolute()
        else ROOT / source_configuration
    ).resolve()
    if not source_configuration.is_file():
        raise ValueError("Task 027 requires ignored catalog/sources.local.yml")
    completed = subprocess.run(
        ["git", "-C", str(ROOT), "archive", "--format=tar", HISTORICAL_COMMIT],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        diagnostic = completed.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(
            f"Task 027 historical commit {HISTORICAL_COMMIT} is unavailable: "
            f"{diagnostic}"
        )
    destination.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(completed.stdout), mode="r:") as archive:
        for member in archive.getmembers():
            path = Path(member.name)
            if path.is_absolute() or ".." in path.parts or member.issym() or member.islnk():
                raise ValueError("Task 027 historical archive contains an unsafe path")
        archive.extractall(destination)
    target_configuration = destination / SOURCE_CONFIGURATION
    target_configuration.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_configuration, target_configuration)


def reproduce(
    source_configuration: Path = SOURCE_CONFIGURATION,
) -> dict[str, Any]:
    variants = (
        {"PYTHONHASHSEED": "1", "LC_ALL": "C", "TZ": "UTC"},
        {"PYTHONHASHSEED": "777", "LC_ALL": "C", "TZ": "Asia/Tokyo"},
    )
    runs = []
    with tempfile.TemporaryDirectory(prefix="schuss-task027-") as temporary:
        base = Path(temporary)
        for index, variant in enumerate(variants, start=1):
            copy_root = base / f"root-{index}"
            _materialize_historical_root(copy_root, source_configuration)
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
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--reproduce", action="store_true")
    parser.add_argument(
        "--source-configuration",
        type=Path,
        help=(
            "existing ignored sources.local.yml to read during reproduction; "
            "defaults to this worktree"
        ),
    )
    args = parser.parse_args()
    if args.check and args.source_configuration is not None:
        parser.error("--source-configuration is valid only with --reproduce")
    try:
        path = ROOT / "evidence/task027-completion-v1/fresh-root-reproduction.json"
        if args.check:
            result = check_retained()
        else:
            result = reproduce(
                args.source_configuration or SOURCE_CONFIGURATION
            )
            payload = core.canonical_json(result).encode("utf-8") + b"\n"
            if not path.is_file() or path.read_bytes() != payload:
                raise ValueError("Task 027 reproduction differs from retained evidence")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print("Task 027 fresh-root reproduction failed: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
