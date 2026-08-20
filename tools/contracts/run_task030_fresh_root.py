#!/usr/bin/env python3
"""Reproduce Task 030 artifacts and CLI bytes in two clean copied roots."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/contracts"))

import validator_core as core  # noqa: E402
from compiler_determinism_matrix import copy_current_tree  # noqa: E402


EVIDENCE = ROOT / "evidence/task030-completion-v1/fresh-root-reproduction.json"
TAG = "mutable-instruments-derived"
ARTIFACTS = (
    "catalog/reviews/task030-mutable-catalog-v1/entries.jsonl",
    "contracts/record-sets/task030-complete-mutable-catalog-v1.json",
    "contracts/task030/catalog-corpus-v5.json",
    "contracts/task030/catalog-selection-r4.json",
    "contracts/task030/catalog-source-review-r2.json",
    "evidence/task030-completion-v1/validation-summary.json",
    "schemas/application-capability-description-v3.schema.json",
    "schemas/catalog-corpus-v5.schema.json",
    "schemas/catalog-projection-v5.schema.json",
    "schemas/catalog-source-review-v1.schema.json",
    "schemas/operation-request-v10.schema.json",
    "schemas/operation-result-v10.schema.json",
    "tools/contracts/tests/fixtures/task030-cli-v3-golden-hashes.json",
)
COMMANDS = {
    "objects-json": (
        "catalog",
        "objects",
        "--provenance",
        TAG,
        "--json",
    ),
    "objects-human": (
        "catalog",
        "objects",
        "macro",
        "--provenance",
        TAG,
    ),
    "family-search-json": (
        "catalog",
        "search",
        "--provenance",
        TAG,
        "--json",
    ),
    "family-inspect-human": (
        "catalog",
        "inspect",
        "schuss-family-000062@1",
    ),
    "completion-bash": ("completion", "bash"),
    "completion-fish": ("completion", "fish"),
    "completion-zsh": ("completion", "zsh"),
}


def _hashes(root: Path) -> dict[str, str]:
    return {path: core.sha256_file(root / path) for path in ARTIFACTS}


def _run_cli(root: Path, command: tuple[str, ...], environment: dict[str, str]) -> bytes:
    completed = subprocess.run(
        [str(root / "bin/schuss"), *command],
        cwd=root.parent,
        env=environment,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        raise ValueError(
            f"fresh-root CLI failed for {' '.join(command)}: "
            + completed.stderr.decode("utf-8", errors="replace")
        )
    return completed.stdout


def reproduce() -> dict[str, Any]:
    variants = (
        {"PYTHONHASHSEED": "1", "LC_ALL": "C", "TZ": "UTC"},
        {"PYTHONHASHSEED": "777", "LC_ALL": "C", "TZ": "Asia/Tokyo"},
    )
    runs = []
    with tempfile.TemporaryDirectory(prefix="schuss-task030-") as temporary:
        base = Path(temporary)
        for index, variant in enumerate(variants, start=1):
            copy_root = base / f"root-{index}"
            copy_current_tree(
                ROOT, copy_root, include_task009_capsule=False
            )
            environment = os.environ.copy()
            environment.update(variant)
            generated = subprocess.run(
                ["python3", "tools/contracts/generate_task030_records.py", "--check"],
                cwd=copy_root,
                env=environment,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if generated.returncode != 0:
                raise ValueError(
                    f"fresh-root Task 030 generation {index} failed: "
                    + generated.stderr.strip()
                )
            golden = subprocess.run(
                ["python3", "tools/contracts/generate_task030_cli_golden.py", "--check"],
                cwd=copy_root,
                env=environment,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if golden.returncode != 0:
                raise ValueError(
                    f"fresh-root Task 030 CLI golden {index} failed: "
                    + golden.stderr.strip()
                )
            summary = json.loads(generated.stdout)
            outputs = {
                name: "sha256:" + hashlib.sha256(
                    _run_cli(copy_root, command, environment)
                ).hexdigest()
                for name, command in sorted(COMMANDS.items())
            }
            runs.append(
                {
                    "variant": variant,
                    "artifact_hashes": _hashes(copy_root),
                    "cli_output_hashes": outputs,
                    "projection_sha256": summary["projection_sha256"],
                    "record_set_reference": summary["record_set_reference"],
                }
            )
    first = runs[0]
    for run in runs[1:]:
        for field in (
            "artifact_hashes",
            "cli_output_hashes",
            "projection_sha256",
            "record_set_reference",
        ):
            if run[field] != first[field]:
                raise ValueError(f"Task 030 fresh-root {field} differs")
    return {
        "schema_version": "task030-fresh-root-reproduction-v1",
        "status": "passed",
        "run_count": 2,
        "ignored_local_source_mapping": True,
        "runs": runs,
        "compiler_or_build_performed": False,
        "project_or_machine_mutation_performed": False,
        "hardware_or_publication_performed": False,
    }


def check_retained() -> dict[str, Any]:
    if not EVIDENCE.is_file():
        raise ValueError("Task 030 fresh-root evidence is missing")
    result = core.load_json(EVIDENCE)
    if (
        result.get("schema_version") != "task030-fresh-root-reproduction-v1"
        or result.get("status") != "passed"
        or result.get("run_count") != 2
        or result.get("ignored_local_source_mapping") is not True
    ):
        raise ValueError("Task 030 fresh-root evidence boundary is stale")
    if any(
        result.get(field) is not False
        for field in (
            "compiler_or_build_performed",
            "project_or_machine_mutation_performed",
            "hardware_or_publication_performed",
        )
    ):
        raise ValueError("Task 030 fresh-root evidence exceeds the task boundary")
    expected_hashes = _hashes(ROOT)
    summary = core.load_json(
        ROOT / "evidence/task030-completion-v1/validation-summary.json"
    )
    runs = result.get("runs")
    if not isinstance(runs, list) or len(runs) != 2:
        raise ValueError("Task 030 fresh-root run list is invalid")
    for run in runs:
        if run.get("artifact_hashes") != expected_hashes:
            raise ValueError("Task 030 fresh-root artifact evidence is stale")
        if run.get("projection_sha256") != summary["projection_sha256"]:
            raise ValueError("Task 030 fresh-root projection evidence is stale")
        if run.get("record_set_reference") != summary["record_set_reference"]:
            raise ValueError("Task 030 fresh-root record-set evidence is stale")
    if runs[0].get("cli_output_hashes") != runs[1].get("cli_output_hashes"):
        raise ValueError("Task 030 fresh-root CLI evidence differs")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--reproduce", action="store_true")
    args = parser.parse_args()
    try:
        result = check_retained() if args.check else reproduce()
        if args.reproduce:
            payload = core.canonical_json(result).encode("utf-8") + b"\n"
            if not EVIDENCE.is_file() or EVIDENCE.read_bytes() != payload:
                raise ValueError("Task 030 reproduction differs from retained evidence")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print("Task 030 fresh-root reproduction failed: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
