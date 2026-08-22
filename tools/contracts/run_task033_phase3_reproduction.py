#!/usr/bin/env python3
"""Reproduce Task 033 Phase 3 registry closure in two copied roots."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/contracts"))

from compiler_determinism_matrix import copy_current_tree  # noqa: E402


ARTIFACTS = (
    "contracts/task033/phase3/native-provider-registry-v1.json",
    "schemas/native-provider-registry-v1.schema.json",
    "packages/schuss_core/generated_native_registry.py",
    "packages/schuss_core/variable_host_runtime.py",
    "packages/schuss_rt/src/runtime_v1.cpp",
    "schemas/host-runtime-package-v1.schema.json",
    "schemas/host-runtime-observation-v1.schema.json",
)


def _hashes(root: Path) -> dict[str, str]:
    return {
        path: hashlib.sha256((root / path).read_bytes()).hexdigest()
        for path in ARTIFACTS
    }


def _checked_json(
    command: list[str], *, cwd: Path, environment: dict[str, str]
) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode:
        raise ValueError(
            f"fresh-root command failed ({' '.join(command)}): "
            + completed.stderr.strip()
        )
    return json.loads(completed.stdout)


def reproduce() -> dict[str, Any]:
    variants = (
        {"PYTHONHASHSEED": "1", "LC_ALL": "C", "TZ": "UTC"},
        {"PYTHONHASHSEED": "777", "LC_ALL": "C", "TZ": "Asia/Tokyo"},
    )
    runs = []
    with tempfile.TemporaryDirectory(prefix="schuss-task033-phase3-") as temporary:
        temporary_root = Path(temporary)
        for index, variant in enumerate(variants, start=1):
            copy_root = temporary_root / f"root-{index}"
            copy_current_tree(ROOT, copy_root, include_task009_capsule=False)
            environment = os.environ.copy()
            environment.update(variant)
            generation = _checked_json(
                [
                    sys.executable,
                    "tools/contracts/generate_task033_phase3_registry.py",
                    "--check",
                ],
                cwd=copy_root,
                environment=environment,
            )
            validation = _checked_json(
                [sys.executable, "tools/contracts/validate_task033_phase3.py"],
                cwd=copy_root,
                environment=environment,
            )
            runs.append(
                {
                    "variant": variant,
                    "artifact_hashes": _hashes(copy_root),
                    "generation_summary": generation,
                    "validation_summary": validation,
                }
            )
    for field in ("artifact_hashes", "generation_summary", "validation_summary"):
        if runs[0][field] != runs[1][field]:
            raise ValueError(f"Task 033 Phase 3 fresh-root {field} differs")
    if runs[0]["artifact_hashes"] != _hashes(ROOT):
        raise ValueError("Task 033 Phase 3 fresh-root artifacts differ from workspace")
    return {
        "schema_version": "task033-phase3-fresh-root-reproduction-v1",
        "status": "passed",
        "run_count": 2,
        "runs": runs,
        "local_source_mapping_used": False,
        "native_build_or_execution_performed": False,
        "semantic_record_provider_runtime_or_ui_mutation_performed": False,
        "device_or_publication_performed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reproduce", action="store_true", required=True)
    parser.parse_args()
    print(json.dumps(reproduce(), ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
