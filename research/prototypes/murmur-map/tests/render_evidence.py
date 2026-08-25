#!/usr/bin/env python3
"""Reproduce Murmur Map's deterministic ten-condition render matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
REPO_BUILD = (REPO_ROOT / "build").resolve()
BUILD = REPO_BUILD / "murmur-map-evidence-build"
EXPERIMENT = ROOT / "contract" / "experiment.json"
EXPECTED = ROOT / "fixtures" / "expected-render-manifest.json"
PROPOSAL = REPO_ROOT / "research" / "proposals" / "modular-generative-juce-instrument-study.md"
CONTRACT = ROOT / "contract" / "implementation-contract.json"
CONTROL_MAP = ROOT / "contract" / "control-map.json"
SOURCE_DEPENDENCIES = ROOT / "source-dependencies.json"
ARTIFACT_NAMES = (
    "condition-stereo.wav",
    "condition-route.json",
    "condition-events.json",
    "condition-metrics.json",
)
PARTITION_EXACT_NAMES = ARTIFACT_NAMES[:3]


def canonical(document: Any) -> str:
    return json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run(command: list[str]) -> None:
    print("+ " + " ".join(command), flush=True)
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalized_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    result = dict(metrics)
    result.pop("block_frames", None)
    return result


def validate_condition(condition: str, directory: Path, tolerances: dict[str, Any]) -> dict[str, Any]:
    metrics = load_json(directory / "condition-metrics.json")
    for field in ("non_finite_count", "dropped_event_count", "repair_count", "clamp_count"):
        if metrics[field] != 0:
            raise RuntimeError(f"{condition}: {field} must be zero")
    if not metrics["peak_absolute"] < tolerances["peak_absolute_exclusive_maximum"]:
        raise RuntimeError(f"{condition}: peak bound failed")
    if max(abs(metrics["mean_left"]), abs(metrics["mean_right"])) > tolerances["absolute_dc_mean_maximum"]:
        raise RuntimeError(f"{condition}: DC bound failed")

    routes = load_json(directory / "condition-route.json")["events"]
    events = load_json(directory / "condition-events.json")["events"]
    lock_frame = 24 * 48000
    change_frame = 32 * 48000
    if condition in {"MM01_LOCKED", "MM05_MOVE_WAYPOINT"}:
        locked = [event["to"] for event in routes if event["frame"] >= lock_frame]
        if len(locked) < 32 or any(value != locked[index % 16] for index, value in enumerate(locked)):
            raise RuntimeError(f"{condition}: locked destination ring is not an exact 16-slot cycle")
    if condition == "MM02_SLOW_EROSION":
        replayed = sum(bool(event["replayed"]) for event in routes)
        if not 0 < replayed < len(routes):
            raise RuntimeError("MM02_SLOW_EROSION: expected both replay and replacement")
    if condition == "MM03_FRESH" and any(event["replayed"] for event in routes):
        raise RuntimeError("MM03_FRESH: MEMORY=0 replayed a route slot")
    if condition == "MM04_HOME_PULL":
        before = [event for event in routes if event["frame"] < change_frame and event["from"] != 0]
        after = [event for event in routes if event["frame"] >= change_frame and event["from"] != 0]
        before_rate = sum(event["to"] == 0 for event in before) / max(1, len(before))
        after_rate = sum(event["to"] == 0 for event in after) / max(1, len(after))
        if not after or not after_rate > before_rate:
            raise RuntimeError("MM04_HOME_PULL: HOME increase did not raise observed return rate")
    if condition == "MM06_CAPTURE_REPLACE":
        before = [event for event in events if event["lane"] == 1 and event["frame"] < change_frame]
        after = [event for event in events if event["lane"] == 1 and event["frame"] >= change_frame]
        if not before or not after:
            raise RuntimeError("MM06_CAPTURE_REPLACE: missing Thread evidence around capture")
        before_fields = {(e["timbre"], e["color"], e["decay_ms"], e["level_milli_db"], e["pan"]) for e in before}
        after_fields = {(e["timbre"], e["color"], e["decay_ms"], e["level_milli_db"], e["pan"]) for e in after}
        if before_fields == after_fields:
            raise RuntimeError("MM06_CAPTURE_REPLACE: capture did not change future event snapshots")
    if condition == "MM07_RESEED":
        after = [event for event in routes if event["frame"] >= change_frame]
        if len(after) < 2 or not any(event["from"] == 0 and not event["replayed"] for event in after[1:]):
            raise RuntimeError("MM07_RESEED: deferred reseed did not restart fresh from HOME")
    if condition == "MM08_EXTREMES" and (not routes or not events):
        raise RuntimeError("MM08_EXTREMES: stress condition produced no semantic activity")
    if condition == "MM09_EXACT_SILENCE":
        pcm = (directory / "condition-stereo.wav").read_bytes()[44:]
        if metrics["peak_absolute"] != 0 or metrics["rms_stereo"] != 0 or any(pcm):
            raise RuntimeError("MM09_EXACT_SILENCE: PCM is not exactly zero")
        if events or not routes:
            raise RuntimeError("MM09_EXACT_SILENCE: event or route boundary failed")
    if condition == "MM10_WHITE_SCENE" and (routes or not events):
        raise RuntimeError("MM10_WHITE_SCENE: comparator trace boundary failed")
    return metrics


def safe_replace_output(source: Path, destination: Path) -> None:
    resolved = destination.resolve()
    if resolved.parent != REPO_BUILD or resolved.name != "murmur-map-evidence":
        raise RuntimeError("evidence output must be exactly build/murmur-map-evidence")
    if resolved.exists():
        shutil.rmtree(resolved)
    shutil.copytree(source, resolved)


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--reproduce", action="store_true")
    mode.add_argument("--update-expected", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    experiment = load_json(EXPERIMENT)
    blocks = experiment["supported_block_frames"]
    conditions = [entry["id"] for entry in experiment["conditions"]]
    run([
        "cmake", "-S", str(ROOT), "-B", str(BUILD),
        "-DCMAKE_BUILD_TYPE=Release", "-DMURMUR_MAP_ENABLE_JUCE=OFF",
    ])
    run(["cmake", "--build", str(BUILD), "--target", "murmur-map-render", "--parallel"])
    renderer = BUILD / "murmur-map-render"
    REPO_BUILD.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="murmur-map-render-matrix-", dir=REPO_BUILD) as temporary:
        matrix_root = Path(temporary)
        retained = matrix_root / "retained"
        retained.mkdir()
        baseline_hashes: dict[str, dict[str, str]] = {}
        baseline_metrics: dict[str, dict[str, Any]] = {}
        for block in blocks:
            for condition in conditions:
                directory = matrix_root / f"block-{block}" / condition
                run([
                    str(renderer), "--condition", condition,
                    "--block", str(block), "--output", str(directory),
                ])
                metrics = validate_condition(condition, directory, experiment["tolerances"])
                hashes = {name: sha256(directory / name) for name in ARTIFACT_NAMES}
                if block == blocks[0]:
                    baseline_hashes[condition] = hashes
                    baseline_metrics[condition] = normalized_metrics(metrics)
                    shutil.move(str(directory), str(retained / condition))
                else:
                    changed = [
                        name for name in PARTITION_EXACT_NAMES
                        if hashes[name] != baseline_hashes[condition][name]
                    ]
                    if changed:
                        raise RuntimeError(f"{condition}: block {block} changed {changed}")
                    if normalized_metrics(metrics) != baseline_metrics[condition]:
                        raise RuntimeError(f"{condition}: block {block} changed objective metrics")
                    shutil.rmtree(directory)

        if baseline_hashes["MM02_SLOW_EROSION"]["condition-stereo.wav"] == baseline_hashes["MM10_WHITE_SCENE"]["condition-stereo.wav"]:
            raise RuntimeError("slow-erosion audio did not differ from the white-scene comparator")
        if baseline_hashes["MM02_SLOW_EROSION"]["condition-events.json"] == baseline_hashes["MM10_WHITE_SCENE"]["condition-events.json"]:
            raise RuntimeError("slow-erosion events did not differ from the white-scene comparator")

        manifest = {
            "conditions": {
                condition: {
                    "artifacts": baseline_hashes[condition],
                    "metrics": baseline_metrics[condition],
                }
                for condition in conditions
            },
            "fingerprints": {
                "control_map": sha256(CONTROL_MAP),
                "experiment": sha256(EXPERIMENT),
                "implementation_contract": sha256(CONTRACT),
                "proposal": sha256(PROPOSAL),
                "renderer": sha256(renderer),
                "source_dependencies": sha256(SOURCE_DEPENDENCIES),
            },
            "sample_rate_hz": experiment["sample_rate_hz"],
            "schema_version": "murmur-map-render-evidence-v1",
            "seed": experiment["seed"],
            "supported_block_frames": blocks,
        }
        manifest_text = canonical(manifest)
        (retained / "manifest.json").write_text(manifest_text, encoding="utf-8")
        if args.update_expected:
            EXPECTED.parent.mkdir(parents=True, exist_ok=True)
            EXPECTED.write_text(manifest_text, encoding="utf-8")
            print(f"updated {EXPECTED}")
        elif not EXPECTED.is_file() or EXPECTED.read_text(encoding="utf-8") != manifest_text:
            raise RuntimeError("frozen expected render manifest does not match")
        safe_replace_output(retained, args.output)
    print(f"Murmur Map render matrix: passed ({len(conditions)} conditions x {len(blocks)} block sizes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
