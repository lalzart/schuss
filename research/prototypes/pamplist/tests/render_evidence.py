#!/usr/bin/env python3
"""Reproduce or authenticate Pamplist's frozen objective render matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any


PROTOTYPE = Path(__file__).resolve().parents[1]
REPO_ROOT = PROTOTYPE.parents[2]
BUILD = REPO_ROOT / "build" / "pamplist-evidence-build"
EXPERIMENT = PROTOTYPE / "contract" / "experiment.json"
EVIDENCE = PROTOTYPE / "contract" / "evidence"
CONDITION_ARTIFACTS = (
    "SHA256SUMS",
    "audio.wav",
    "controller-trace.json",
    "events.json",
    "manifest.json",
    "metrics.json",
    "snapshots.json",
)


def run(command: list[str]) -> None:
    print("+ " + " ".join(command), flush=True)
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical(document: Any) -> str:
    return json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def condition_hashes(directory: Path) -> dict[str, str]:
    return {name: sha256(directory / name) for name in CONDITION_ARTIFACTS}


def validate_local_manifest(directory: Path) -> None:
    expected: dict[str, str] = {}
    for line in (directory / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        fingerprint, name = line.split("  ", 1)
        expected[name] = fingerprint
    manifest_names = tuple(name for name in CONDITION_ARTIFACTS if name != "SHA256SUMS")
    if tuple(expected) != manifest_names:
        raise RuntimeError(f"{directory.name}: local SHA256SUMS names or order drifted")
    for name, fingerprint in expected.items():
        if sha256(directory / name) != fingerprint:
            raise RuntimeError(f"{directory.name}: local artifact drifted: {name}")


def validate_condition(condition: str, directory: Path) -> dict[str, Any]:
    validate_local_manifest(directory)
    metrics = load_json(directory / "metrics.json")
    if metrics["finite_samples_percent"] != 100:
        raise RuntimeError(f"{condition}: non-finite sample tolerance failed")
    if metrics["peak_main_q27"] > 134217727 or metrics["peak_auxiliary_q27"] > 134217727:
        raise RuntimeError(f"{condition}: Q27 output bound failed")
    if metrics["saturated_frame_count"] != 0:
        raise RuntimeError(f"{condition}: saturated output occurred")
    snapshots = load_json(directory / "snapshots.json")["snapshots"]
    for snapshot in snapshots:
        diagnostics = snapshot["diagnostics"]
        for field in (
            "clamped_control_count",
            "invalid_control_count",
            "non_finite_source_count",
            "saturated_sample_count",
            "unsupported_process_count",
        ):
            if diagnostics[field] != 0:
                raise RuntimeError(f"{condition}: nominal diagnostic {field} is nonzero")

    if condition == "PAMP_SILENCE":
        if metrics["peak_main_q27"] != 0 or metrics["peak_auxiliary_q27"] != 0:
            raise RuntimeError("PAMP_SILENCE: exact silence failed")
        if any(part["nonzero_main"] or part["nonzero_auxiliary"] for part in metrics["parts"]):
            raise RuntimeError("PAMP_SILENCE: a suppression subcase is nonzero")
    elif condition == "PAMP_24":
        if len(metrics["parts"]) != 24:
            raise RuntimeError("PAMP_24: engine sweep count is not 24")
        for index, part in enumerate(metrics["parts"]):
            if part["part"] != f"engine-{index:02d}":
                raise RuntimeError("PAMP_24: engine ordering drifted")
            if part["nonzero_main"] == 0 or part["nonzero_auxiliary"] == 0:
                raise RuntimeError(f"PAMP_24: engine {index} has a silent output channel")
    else:
        if metrics["peak_main_q27"] == 0 or metrics["peak_auxiliary_q27"] == 0:
            raise RuntimeError(f"{condition}: nominal render is silent")

    if condition == "PAMP_LOOP":
        decisions: dict[int, bool] = {}
        lane_zero_events = [
            event for event in load_json(directory / "events.json")["events"]
            if event["boundary_mask"] & 1
        ]
        if len(lane_zero_events) < 21:
            raise RuntimeError("PAMP_LOOP: too few lane-zero steps for three loop cycles")
        for event in lane_zero_events:
            address = event["addresses"][0]
            accepted = bool(event["accepted_mask"] & 1)
            if address in decisions and decisions[address] != accepted:
                raise RuntimeError("PAMP_LOOP: keyed decision changed at a repeated address")
            decisions[address] = accepted
        if set(decisions) != set(range(7)):
            raise RuntimeError("PAMP_LOOP: not all seven repeat addresses were observed")
    return metrics


def write_top_level_manifest(
    destination: Path,
    blocks: list[int],
    condition_names: list[str],
    hashes: dict[str, dict[str, str]],
    metrics: dict[str, dict[str, Any]],
) -> None:
    matrix_audio = hashes["PAMP_MATRIX"]["audio.wav"]
    comparator_audio = hashes["PAMP_CMP_PHASELESS"]["audio.wav"]
    matrix_events = hashes["PAMP_MATRIX"]["events.json"]
    comparator_events = hashes["PAMP_CMP_PHASELESS"]["events.json"]
    if matrix_audio == comparator_audio or matrix_events == comparator_events:
        raise RuntimeError("phaseless comparator did not diverge in both audio and trace")
    manifest = {
        "comparator": {
            "audio_diverged": True,
            "event_trace_diverged": True,
            "id": "PAMP_CMP_PHASELESS",
            "reference": "PAMP_MATRIX",
        },
        "conditions": {
            condition: {
                "artifacts": hashes[condition],
                "metrics": metrics[condition],
            }
            for condition in condition_names
        },
        "proposal_sha256": "bf110cd1bfe6b86e032bc993e0baf705d7459182c891d095a9a1a39ce1789af3",
        "sample_rate_hz": 48000,
        "schema_version": "pamplist-render-evidence-v1",
        "seed": 1346456912,
        "supported_block_frames": blocks,
    }
    (destination / "evidence-manifest.json").write_text(
        canonical(manifest), encoding="utf-8"
    )
    # Per-condition SHA256SUMS files are themselves retained and authenticated
    # by this top-level manifest. The top-level SHA256SUMS does not hash itself.
    relative_files = sorted(
        path.relative_to(destination).as_posix()
        for path in destination.rglob("*")
        if path.is_file() and path != destination / "SHA256SUMS"
    )
    text = "".join(
        f"{sha256(destination / name)}  {name}\n" for name in relative_files
    )
    (destination / "SHA256SUMS").write_text(text, encoding="utf-8")


def authenticate_retained(destination: Path) -> None:
    top_sums = destination / "SHA256SUMS"
    manifest_path = destination / "evidence-manifest.json"
    if not top_sums.is_file() or not manifest_path.is_file():
        raise RuntimeError("missing retained Pamplist evidence manifest")
    expected: dict[str, str] = {}
    for line in top_sums.read_text(encoding="utf-8").splitlines():
        fingerprint, name = line.split("  ", 1)
        expected[name] = fingerprint
    for name, fingerprint in expected.items():
        path = destination / name
        if not path.is_file() or sha256(path) != fingerprint:
            raise RuntimeError(f"retained Pamplist evidence drifted: {name}")
    actual_names = sorted(
        path.relative_to(destination).as_posix()
        for path in destination.rglob("*")
        if path.is_file() and path != top_sums
    )
    if list(expected) != actual_names:
        raise RuntimeError("retained Pamplist evidence file set or order drifted")
    manifest = load_json(manifest_path)
    experiment = load_json(EXPERIMENT)
    blocks = experiment["supported_block_frames"]
    conditions = [condition["id"] for condition in experiment["conditions"]]
    if manifest["supported_block_frames"] != blocks:
        raise RuntimeError("retained partition set drifted")
    if list(manifest["conditions"]) != sorted(conditions):
        raise RuntimeError("retained condition set drifted")
    metrics: dict[str, dict[str, Any]] = {}
    for condition in conditions:
        directory = destination / condition
        hashes = condition_hashes(directory)
        if hashes != manifest["conditions"][condition]["artifacts"]:
            raise RuntimeError(f"{condition}: retained manifest binding drifted")
        metrics[condition] = validate_condition(condition, directory)
    if sha256(destination / "PAMP_MATRIX" / "audio.wav") == sha256(
        destination / "PAMP_CMP_PHASELESS" / "audio.wav"
    ):
        raise RuntimeError("retained phaseless audio comparator no longer diverges")
    if sha256(destination / "PAMP_MATRIX" / "events.json") == sha256(
        destination / "PAMP_CMP_PHASELESS" / "events.json"
    ):
        raise RuntimeError("retained phaseless trace comparator no longer diverges")
    print(f"Pamplist retained render evidence: valid ({destination})")


def reproduce(destination: Path) -> None:
    if destination.exists():
        raise RuntimeError(f"refusing to overwrite existing evidence: {destination}")
    experiment = load_json(EXPERIMENT)
    blocks = experiment["supported_block_frames"]
    conditions = [condition["id"] for condition in experiment["conditions"]]
    run([
        "cmake", "-S", str(PROTOTYPE), "-B", str(BUILD),
        "-DCMAKE_BUILD_TYPE=Release",
    ])
    run(["cmake", "--build", str(BUILD), "--target", "pamplist-render", "--parallel"])
    renderer = BUILD / "pamplist-render"
    with tempfile.TemporaryDirectory(prefix="pamplist-render-matrix-") as temporary:
        root = Path(temporary)
        baseline_hashes: dict[str, dict[str, str]] = {}
        baseline_metrics: dict[str, dict[str, Any]] = {}
        for block in blocks:
            for condition in conditions:
                output = root / f"block-{block}" / condition
                run([
                    str(renderer),
                    "--condition", condition,
                    "--block", str(block),
                    "--output", str(output),
                ])
                hashes = condition_hashes(output)
                metrics = validate_condition(condition, output)
                if block == blocks[0]:
                    baseline_hashes[condition] = hashes
                    baseline_metrics[condition] = metrics
                elif hashes != baseline_hashes[condition]:
                    changed = sorted(
                        name for name in CONDITION_ARTIFACTS
                        if hashes[name] != baseline_hashes[condition][name]
                    )
                    raise RuntimeError(
                        f"{condition}: block {block} changed artifacts {changed}"
                    )
        baseline = root / f"block-{blocks[0]}"
        shutil.copytree(baseline, destination)
        write_top_level_manifest(
            destination,
            blocks,
            conditions,
            baseline_hashes,
            baseline_metrics,
        )
    authenticate_retained(destination)
    print(f"Pamplist render matrix reproduced: {destination}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--reproduce", action="store_true")
    parser.add_argument("--output", type=Path, default=EVIDENCE)
    arguments = parser.parse_args()
    try:
        if arguments.check:
            authenticate_retained(arguments.output.resolve())
        else:
            reproduce(arguments.output.resolve())
    except (OSError, KeyError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"Pamplist render evidence failed: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
