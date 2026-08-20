#!/usr/bin/env python3
"""Reproduce Task 033 Phase 2 in two copied roots and fresh processes."""

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
    "contracts/record-sets/task033-phase2-collection-provider-v1.json",
    *(f"contracts/task033/phase2/source-release-{number:02d}.json" for number in range(1, 8)),
    *(f"contracts/task033/phase2/object-collection-{number:02d}.json" for number in range(1, 5)),
    "contracts/task033/phase2/catalog-corpus-v6.json",
    "contracts/task033/phase2/catalog-selection-r5.json",
    "contracts/task033/phase2/implementation-provider-01.json",
    "contracts/task033/phase2/implementation-availability-policy-01.json",
    "schemas/application-capability-description-v11.schema.json",
    "schemas/catalog-corpus-v6.schema.json",
    "schemas/catalog-projection-v6.schema.json",
    "schemas/collection-profile-v0.schema.json",
    "schemas/implementation-availability-policy-v0.schema.json",
    "schemas/implementation-provider-v0.schema.json",
    "schemas/object-collection-v0.schema.json",
    "schemas/operation-request-v18.schema.json",
    "schemas/operation-result-v18.schema.json",
    "schemas/source-release-v0.schema.json",
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
    with tempfile.TemporaryDirectory(prefix="schuss-task033-phase2-") as temporary:
        temporary_root = Path(temporary)
        for index, variant in enumerate(variants, start=1):
            copy_root = temporary_root / f"root-{index}"
            copy_current_tree(
                ROOT,
                copy_root,
                include_task009_capsule=False,
            )
            environment = os.environ.copy()
            environment.update(variant)
            generation = _checked_json(
                [
                    sys.executable,
                    "tools/contracts/generate_task033_phase2_records.py",
                    "--check",
                ],
                cwd=copy_root,
                environment=environment,
            )
            validation = _checked_json(
                [sys.executable, "tools/contracts/validate_task033_phase2.py"],
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
            raise ValueError(f"Task 033 Phase 2 fresh-root {field} differs")
    if runs[0]["artifact_hashes"] != _hashes(ROOT):
        raise ValueError("Task 033 Phase 2 fresh-root artifacts differ from the workspace")
    return {
        "schema_version": "task033-phase2-fresh-root-reproduction-v1",
        "status": "passed",
        "run_count": 2,
        "runs": runs,
        "local_source_mapping_used": False,
        "native_registry_refactor_performed": False,
        "project_graph_backend_ui_or_hardware_mutation_performed": False,
        "git_or_publication_performed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reproduce", action="store_true", required=True)
    parser.parse_args()
    print(json.dumps(reproduce(), ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
