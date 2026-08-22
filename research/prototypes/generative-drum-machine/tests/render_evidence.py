#!/usr/bin/env python3
"""Reproduce and compare the frozen deterministic render matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
REPO_BUILD = (REPO_ROOT / "build").resolve()
BUILD = REPO_BUILD / "generative-drum-machine-evidence-build"
EXPERIMENT = ROOT / "contract" / "experiment.json"
EXPECTED = ROOT / "fixtures" / "expected-render-manifest.json"
ARTIFACT_NAMES = (
    "allocator-trace.json",
    "audio.wav",
    "event-trace.json",
    "manifest.json",
    "metrics.json",
)


def canonical(document: Any) -> str:
    return json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n"


def run(command: list[str]) -> None:
    print("+ " + " ".join(command), flush=True)
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_condition(condition: str, directory: Path, tolerances: dict[str, Any]) -> dict[str, Any]:
    metrics = load_json(directory / "metrics.json")
    if metrics["overflow_count"] != tolerances["integer_overflow_count"]:
        raise RuntimeError(f"{condition}: overflow tolerance failed")
    if metrics["clipped_sample_count"] != 0:
        raise RuntimeError(f"{condition}: hard clipping occurred")
    if metrics["peak_absolute_q27"] > tolerances["peak_absolute_q27_max"]:
        raise RuntimeError(f"{condition}: peak tolerance failed")
    if metrics["dc_mean_absolute_q27"] > tolerances["dc_mean_absolute_q27_max"]:
        raise RuntimeError(f"{condition}: DC tolerance failed")

    events = load_json(directory / "event-trace.json")["events"]
    static_phrase_frames = {
        "authored-static": 384000,
        "three-turn-static": 288000,
        "rolling-six-static": 288000,
    }
    if condition in static_phrase_frames:
        phrase_frames = static_phrase_frames[condition]
        normalized: list[list[tuple[Any, ...]]] = [[], [], []]
        for event in events:
            phrase = event["phrase"]
            normalized[phrase].append((
                event["frame"] - phrase * phrase_frames,
                event["lane"],
                event["source_ordinal"],
                event["velocity_u15"],
                event["articulation"],
                event["variation_group"],
            ))
        if not normalized[0] == normalized[1] == normalized[2]:
            raise RuntimeError(f"{condition}: phrase repetition is not exact")
        if any(event["variation_group"] != 0 for event in events):
            raise RuntimeError(f"{condition}: autonomous variation occurred at zero enthusiasm")
    if condition == "authored-phrase-variation":
        for phrase in range(3):
            groups = {
                event["variation_group"]
                for event in events
                if event["phrase"] == phrase
                and event["variation_group"] not in (0, 100)
            }
            if len(groups) > 1:
                raise RuntimeError(
                    f"authored-phrase-variation: incoherent groups in phrase {phrase}"
                )
        if not any(event["variation_group"] == 100 for event in events):
            raise RuntimeError("authored-phrase-variation: queued fill was not rendered")
    if condition == "allocator-stress":
        expected = {
            "event_count": 8,
            "dropped_hit_count": 2,
            "choked_voice_count": 2,
        }
        for field, value in expected.items():
            if metrics[field] != value:
                raise RuntimeError(f"allocator-stress: {field} != {value}")
    if condition == "five-across-shaped":
        trace = load_json(directory / "event-trace.json")
        if trace["meter"] != "5/4" or trace["rhythm_index"] != 3:
            raise RuntimeError("five-across-shaped: wrong rhythm provenance")
        if not any(event["variation_group"] == 100 for event in events):
            raise RuntimeError("five-across-shaped: queued quintuplet fill was not rendered")
    if condition == "samba-enredo-study":
        trace = load_json(directory / "event-trace.json")
        if trace["meter"] != "2/4" or trace["rhythm_index"] != 4:
            raise RuntimeError("samba-enredo-study: wrong rhythm provenance")
        if not events:
            raise RuntimeError("samba-enredo-study: empty event trace")
    return metrics


def safe_replace_output(source: Path, destination: Path) -> None:
    resolved = destination.resolve()
    try:
        relative = resolved.relative_to(REPO_BUILD)
    except ValueError as error:
        raise RuntimeError("evidence output must be below the repository build directory") from error
    if not relative.parts or relative.parts[0] != "generative-drum-machine-evidence":
        raise RuntimeError("refusing to replace an unexpected evidence directory")
    if resolved.exists():
        shutil.rmtree(resolved)
    shutil.copytree(source, resolved)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reproduce", action="store_true")
    parser.add_argument("--update-expected", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.reproduce and not args.update_expected:
        print("render evidence requires --reproduce or --update-expected")
        return 1
    experiment = load_json(EXPERIMENT)
    blocks = experiment["supported_block_frames"]
    conditions = [condition["id"] for condition in experiment["conditions"]]
    run(["cmake", "-S", str(ROOT), "-B", str(BUILD), "-DCMAKE_BUILD_TYPE=Release"])
    run(["cmake", "--build", str(BUILD), "--target", "generative-drum-machine-render", "--parallel"])
    renderer = BUILD / "generative-drum-machine-render"

    REPO_BUILD.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="gdm-render-matrix-", dir=REPO_BUILD) as temporary:
        matrix_root = Path(temporary)
        baseline_hashes: dict[str, dict[str, str]] = {}
        baseline_metrics: dict[str, dict[str, Any]] = {}
        baseline_root = matrix_root / f"block-{blocks[0]}"
        for block in blocks:
            for condition in conditions:
                directory = matrix_root / f"block-{block}" / condition
                run([
                    str(renderer), "--condition", condition,
                    "--output", str(directory),
                    "--block-frames", str(block),
                ])
                hashes = {name: sha256(directory / name) for name in ARTIFACT_NAMES}
                metrics = validate_condition(condition, directory, experiment["tolerances"])
                if block == blocks[0]:
                    baseline_hashes[condition] = hashes
                    baseline_metrics[condition] = metrics
                elif hashes != baseline_hashes[condition]:
                    changed = sorted(
                        name for name in ARTIFACT_NAMES
                        if hashes[name] != baseline_hashes[condition][name]
                    )
                    raise RuntimeError(
                        f"{condition}: block {block} changed artifacts {changed}"
                    )

        evidence = {
            "conditions": {
                condition: {
                    "artifacts": baseline_hashes[condition],
                    "metrics": baseline_metrics[condition],
                }
                for condition in conditions
            },
            "preset_fingerprint": load_json(
                baseline_root / conditions[0] / "event-trace.json"
            )["preset_fingerprint"],
            "sample_rate_hz": experiment["sample_rate_hz"],
            "schema_version": "schuss-generative-drum-evidence-manifest-v0",
            "supported_block_frames": blocks,
        }
        evidence_text = canonical(evidence)
        (baseline_root / "evidence-manifest.json").write_text(
            evidence_text, encoding="utf-8"
        )
        if args.update_expected:
            EXPECTED.write_text(evidence_text, encoding="utf-8")
            print(f"updated {EXPECTED}")
        elif not EXPECTED.is_file() or EXPECTED.read_text(encoding="utf-8") != evidence_text:
            raise RuntimeError("frozen expected render manifest does not match")
        safe_replace_output(baseline_root, args.output)
    print(f"generative drum render matrix: passed ({len(blocks)} block sizes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
