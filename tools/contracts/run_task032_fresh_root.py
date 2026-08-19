#!/usr/bin/env python3
"""Reproduce the final Task 032 larger graph in two isolated copied roots."""

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


EVIDENCE = ROOT / "evidence/task032-completion-v1/fresh-root-reproduction.json"
RECORD_SET = "contracts/record-sets/task032-variable-host-runtime-v1.json"
PACKAGE = "fixtures/task032/larger-host-package.json"
RETAINED_OBSERVATION = "fixtures/task032/larger-offline-observation.json"
RETAINED_WAV = "fixtures/task032/larger-output.wav"
ARTIFACTS = (
    RECORD_SET,
    PACKAGE,
    "fixtures/task032/larger-host-lowering.json",
    RETAINED_OBSERVATION,
    RETAINED_WAV,
    "schemas/application-capability-description-v9.schema.json",
    "schemas/host-engine-protocol-v1.schema.json",
    "schemas/host-runtime-observation-v1.schema.json",
    "schemas/host-runtime-package-v1.schema.json",
    "schemas/operation-request-v16.schema.json",
    "schemas/operation-result-v16.schema.json",
)
CPP_SOURCES = (
    "packages/schuss_rt/src/package_parser.cpp",
    "packages/schuss_rt/src/package_parser_v1.cpp",
    "packages/schuss_rt/src/runtime.cpp",
    "packages/schuss_rt/src/runtime_v1.cpp",
    "packages/schuss_rt/src/sha256.cpp",
    "apps/schuss_audio_engine/src/offline_main.cpp",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _artifact_hashes(root: Path) -> dict[str, str]:
    return {path: _sha256(root / path) for path in ARTIFACTS}


def _checked(command: list[str], *, cwd: Path, environment: dict[str, str]) -> str:
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
    return completed.stdout


def _run_once(
    copy_root: Path,
    environment: dict[str, str],
    variant: dict[str, str],
) -> dict[str, Any]:
    records = json.loads(
        _checked(
            [sys.executable, "tools/contracts/generate_task032_records.py", "--check"],
            cwd=copy_root,
            environment=environment,
        )
    )
    _checked(
        [sys.executable, "tools/contracts/generate_task032_fixtures.py", "--check"],
        cwd=copy_root,
        environment=environment,
    )
    executable = copy_root.parent / (copy_root.name + "-offline-render")
    _checked(
        [
            "/usr/bin/xcrun",
            "clang++",
            "-std=c++17",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Wpedantic",
            "-Werror",
            "-I",
            str(copy_root / "packages/schuss_rt/include"),
            *[str(copy_root / source) for source in CPP_SOURCES],
            "-o",
            str(executable),
        ],
        cwd=copy_root.parent,
        environment=environment,
    )
    package = core.load_json(copy_root / PACKAGE)
    wav = copy_root.parent / (copy_root.name + "-larger.wav")
    observation = copy_root.parent / (copy_root.name + "-larger-observation.json")
    _checked(
        [
            str(executable),
            "--package",
            str(copy_root / PACKAGE),
            "--package-hash",
            package["content_hash"],
            "--output",
            str(wav),
            "--observation",
            str(observation),
            "--frames",
            "48000",
            "--block",
            "127",
        ],
        cwd=copy_root.parent,
        environment=environment,
    )
    observed = core.load_json(observation)
    observation_schema = core.load_json(
        copy_root / "schemas/host-runtime-observation-v1.schema.json"
    )
    errors = core.schema_errors(observed, observation_schema, observation_schema)
    if errors or observed["content_hash"] != core.record_content_hash(
        observed, observation_schema
    ):
        raise ValueError("fresh-root observation is invalid: " + "; ".join(errors))
    if observed["package_content_hash"] != package["content_hash"]:
        raise ValueError("fresh-root observation selected another package")
    return {
        "variant": variant,
        "artifact_hashes": _artifact_hashes(copy_root),
        "record_set_reference": records["record_set_reference"],
        "package_content_hash": package["content_hash"],
        "wav_sha256": _sha256(wav),
        "observation_byte_sha256": _sha256(observation),
        "observation_content_hash": observed["content_hash"],
    }


def reproduce() -> dict[str, Any]:
    variants = (
        {"PYTHONHASHSEED": "1", "LC_ALL": "C", "TZ": "UTC"},
        {"PYTHONHASHSEED": "777", "LC_ALL": "C", "TZ": "Asia/Tokyo"},
    )
    runs = []
    with tempfile.TemporaryDirectory(prefix="schuss-task032-fresh-") as temporary:
        temporary_root = Path(temporary)
        for index, variant in enumerate(variants, start=1):
            copy_root = temporary_root / f"root-{index}"
            shutil.copytree(
                ROOT,
                copy_root,
                symlinks=True,
                ignore=shutil.ignore_patterns(
                    ".git",
                    "build",
                    "node_modules",
                    "target",
                    "sources.local.yml",
                    "__pycache__",
                    ".pytest_cache",
                    ".DS_Store",
                ),
            )
            environment = os.environ.copy()
            environment.update(variant)
            runs.append(_run_once(copy_root, environment, variant))
    comparable_fields = (
        "artifact_hashes",
        "record_set_reference",
        "package_content_hash",
        "wav_sha256",
        "observation_byte_sha256",
        "observation_content_hash",
    )
    for field in comparable_fields:
        if runs[0][field] != runs[1][field]:
            raise ValueError(f"Task 032 fresh-root {field} differs")
    if runs[0]["artifact_hashes"] != _artifact_hashes(ROOT):
        raise ValueError("Task 032 fresh-root artifacts differ from the workspace")
    return {
        "schema_version": "task032-fresh-root-reproduction-v1",
        "status": "passed",
        "run_count": 2,
        "runs": runs,
        "physical_audio_or_midi_performed": False,
        "ksoloti_or_hardware_performed": False,
        "realtime_level_7_promoted": False,
        "audible_level_8_promoted": False,
        "git_or_publication_performed": False,
    }


def check_retained() -> dict[str, Any]:
    if not EVIDENCE.is_file():
        raise ValueError("Task 032 fresh-root evidence is missing")
    result = core.load_json(EVIDENCE)
    if (
        result.get("schema_version") != "task032-fresh-root-reproduction-v1"
        or result.get("status") != "passed"
        or result.get("run_count") != 2
    ):
        raise ValueError("Task 032 fresh-root evidence header is stale")
    for field in (
        "physical_audio_or_midi_performed",
        "ksoloti_or_hardware_performed",
        "realtime_level_7_promoted",
        "audible_level_8_promoted",
        "git_or_publication_performed",
    ):
        if result.get(field) is not False:
            raise ValueError("Task 032 fresh-root evidence exceeds its boundary")
    runs = result.get("runs")
    if not isinstance(runs, list) or len(runs) != 2:
        raise ValueError("Task 032 fresh-root runs are missing")
    expected = _artifact_hashes(ROOT)
    if any(run.get("artifact_hashes") != expected for run in runs):
        raise ValueError("Task 032 fresh-root artifact evidence is stale")
    for field in (
        "record_set_reference",
        "package_content_hash",
        "wav_sha256",
        "observation_byte_sha256",
        "observation_content_hash",
    ):
        if runs[0].get(field) != runs[1].get(field):
            raise ValueError(f"Task 032 retained {field} differs")
    if runs[0].get("wav_sha256") != _sha256(ROOT / RETAINED_WAV):
        raise ValueError("Task 032 retained WAV evidence is stale")
    if runs[0].get("observation_byte_sha256") != _sha256(
        ROOT / RETAINED_OBSERVATION
    ):
        raise ValueError("Task 032 retained observation evidence is stale")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    option = parser.parse_args()
    try:
        result = check_retained() if option.check else reproduce()
        if not option.check:
            EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
            EVIDENCE.write_bytes(core.canonical_json(result).encode("utf-8") + b"\n")
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print("Task 032 fresh-root reproduction failed: " + str(error), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
