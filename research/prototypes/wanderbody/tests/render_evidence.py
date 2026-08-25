#!/usr/bin/env python3
"""Reproduce Wanderbody's frozen ten-condition objective render matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
REPO_BUILD = (REPO_ROOT / "build").resolve()
BUILD = REPO_BUILD / "wanderbody-evidence-build"
EXPERIMENT = ROOT / "contract-r01" / "experiment.json"
EXPECTED = ROOT / "fixtures" / "expected-render-manifest.json"
RESULTS = ROOT / "results"
PROPOSAL = REPO_ROOT / "research" / "proposals" / "wanderbody-standalone-r01.md"
CONTRACT = ROOT / "contract-r01" / "implementation-contract.json"
CONTROL_MAP = ROOT / "contract-r01" / "control-map.json"
ARTIFACT_NAMES = ("audio.wav", "decisions.json", "metrics.json")
PARTITION_EXACT_NAMES = ARTIFACT_NAMES[:2]
TUPLE_FIELDS = (
    "position",
    "duration_seconds",
    "rate",
    "gain",
    "pan",
    "body_frequency_hz",
    "direction",
)


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


def tuple_value(event: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(event[field] for field in TUPLE_FIELDS)


def correlation(values: list[float]) -> float:
    if len(values) < 3:
        raise RuntimeError("correlation requires at least three observations")
    left = values[:-1]
    right = values[1:]
    left_mean = sum(left) / len(left)
    right_mean = sum(right) / len(right)
    covariance = sum(
        (first - left_mean) * (second - right_mean)
        for first, second in zip(left, right)
    )
    left_energy = sum((value - left_mean) ** 2 for value in left)
    right_energy = sum((value - right_mean) ** 2 for value in right)
    if left_energy == 0.0 or right_energy == 0.0:
        raise RuntimeError("correlation input has zero variance")
    return covariance / math.sqrt(left_energy * right_energy)


def independent_step_correlation(events: list[dict[str, Any]]) -> float:
    """Avoid the shared-middle-sample bias of overlapping IID differences."""
    positions = [event["position"] for event in events]
    non_overlapping_steps = [
        positions[index + 1] - positions[index]
        for index in range(0, len(positions) - 1, 2)
    ]
    return correlation(non_overlapping_steps)


def validate_condition(
    condition: str,
    directory: Path,
    tolerances: dict[str, Any],
) -> dict[str, Any]:
    metrics = load_json(directory / "metrics.json")
    trace = load_json(directory / "decisions.json")
    events = trace["events"]
    if trace["condition"] != condition or metrics["condition"] != condition:
        raise RuntimeError(f"{condition}: artifact identity mismatch")
    for field in (
        "non_finite_count",
        "voice_repair_count",
        "body_repair_count",
        "final_fault_count",
    ):
        if metrics[field] != tolerances["finite_failure_count"]:
            raise RuntimeError(f"{condition}: {field} must be zero")
    if metrics["diagnostic"] != "none":
        raise RuntimeError(f"{condition}: latched diagnostic is not clear")
    if not metrics["peak_absolute"] < tolerances["peak_absolute_exclusive_maximum"]:
        raise RuntimeError(f"{condition}: peak bound failed")
    if max(abs(metrics["mean_left"]), abs(metrics["mean_right"])) > tolerances["absolute_dc_mean_maximum"]:
        raise RuntimeError(f"{condition}: DC bound failed")

    if condition == "WB01_HOVER":
        resolved = [event for event in events if event["frame"] >= 96000]
        minimum = 0.56 - (0.01 + 0.47 * 0.18)
        maximum = 0.56 + (0.01 + 0.47 * 0.18)
        violations = sum(not minimum <= event["position"] <= maximum for event in resolved)
        if not resolved or violations != tolerances["field_violation_count"]:
            raise RuntimeError("WB01_HOVER: resolved Hover decisions left the field")
    elif condition in {"WB02_DRUNK", "WB10_UNCORRELATED"}:
        resolved = [event for event in events if event["frame"] >= 96960]
        minimum = 0.50 - (0.01 + 0.47 * 0.42)
        maximum = 0.50 + (0.01 + 0.47 * 0.42)
        if not resolved or any(not minimum <= event["position"] <= maximum for event in resolved):
            raise RuntimeError(f"{condition}: decision left the resolved field")
        measured = independent_step_correlation(resolved)
        if condition == "WB02_DRUNK":
            if measured < tolerances["drunk_lag1_step_correlation_minimum"]:
                raise RuntimeError(f"WB02_DRUNK: step correlation {measured} is too low")
            width = maximum - minimum
            boundary_count = sum(
                min(event["position"] - minimum, maximum - event["position"])
                <= width * 0.01
                for event in resolved
            )
            if boundary_count / len(resolved) > tolerances["drunk_boundary_fraction_maximum"]:
                raise RuntimeError("WB02_DRUNK: reflected motion sticks at a boundary")
        elif abs(measured) > tolerances["comparator_absolute_step_correlation_maximum"]:
            raise RuntimeError(f"WB10_UNCORRELATED: comparator correlation {measured} is too large")
    elif condition in {"WB03_LOCKED", "WB04_SHUFFLED", "WB05_MUTATED"}:
        fresh = [event for event in events if event["frame"] < 288000]
        recurrent = [event for event in events if event["frame"] >= 288000]
        history = [tuple_value(event) for event in fresh[-8:]]
        if len(history) != 8 or len(recurrent) < 16:
            raise RuntimeError(f"{condition}: insufficient recurrence evidence")
        if condition == "WB03_LOCKED":
            mismatches = sum(
                tuple_value(event) != history[event["history_index"]]
                or not event["replayed"]
                for event in recurrent
            )
            if mismatches != tolerances["locked_cycle_mismatch_count"]:
                raise RuntimeError("WB03_LOCKED: tuple cycle mismatch")
        elif condition == "WB04_SHUFFLED":
            first_cycle = [tuple_value(event) for event in recurrent[:8]]
            set_difference = len(set(first_cycle).symmetric_difference(history))
            if set_difference != tolerances["shuffled_tuple_set_difference_count"]:
                raise RuntimeError("WB04_SHUFFLED: tuple set changed")
            if first_cycle == history or any(not event["shuffled"] for event in recurrent):
                raise RuntimeError("WB04_SHUFFLED: order was not permuted")
            for offset, event in enumerate(recurrent[8:]):
                if tuple_value(event) != first_cycle[offset % 8]:
                    raise RuntimeError("WB04_SHUFFLED: permutation did not cycle exactly")
        else:
            distances: list[float] = []
            for event in recurrent:
                base = history[event["history_index"]]
                candidate = tuple_value(event)
                if candidate[3] != base[3] or candidate[6] != base[6] or not event["mutated"]:
                    raise RuntimeError("WB05_MUTATED: undeclared tuple field changed")
                distance = max(
                    abs(candidate[0] - base[0]),
                    abs(candidate[1] - base[1]) / 0.40,
                    abs(abs(candidate[2]) - abs(base[2])),
                    abs(candidate[4] - base[4]) / 2.0,
                )
                distances.append(distance)
            if min(distances) <= tolerances["mutated_normalized_distance_exclusive_minimum"]:
                raise RuntimeError("WB05_MUTATED: mutation made no measurable change")
            if max(distances) > tolerances["mutated_normalized_distance_inclusive_maximum"]:
                raise RuntimeError("WB05_MUTATED: normalized distance exceeded its bound")
    elif condition == "WB06_BODY":
        if metrics["body_mid_energy_over_bypass"] < tolerances["body_mid_energy_over_bypass_minimum"]:
            raise RuntimeError("WB06_BODY: modal response did not exceed bypass energy")
        if metrics["body_late_to_early_energy"] > tolerances["body_late_to_early_energy_maximum"]:
            raise RuntimeError("WB06_BODY: modal response did not decay")
        if metrics["stereo_difference_energy"] <= 0.0:
            raise RuntimeError("WB06_BODY: body did not retain stereo position")
    elif condition == "WB07_FREEZE_CLEAR":
        if metrics["freeze_hold_delta"] != 0 or metrics["freeze_count"] != 2:
            raise RuntimeError("WB07_FREEZE_CLEAR: Freeze changed capture time")
        if metrics["clear_count"] != 1 or metrics["capture_epoch"] < 3:
            raise RuntimeError("WB07_FREEZE_CLEAR: Clear did not invalidate capture")
    elif condition == "WB08_EXTREMES":
        if not events or metrics["reset_count"] != 1:
            raise RuntimeError("WB08_EXTREMES: stress/reset activity was not observed")
    elif condition == "WB09_SILENCE":
        pcm = (directory / "audio.wav").read_bytes()[44:]
        if events or metrics["peak_absolute"] != 0 or metrics["rms_stereo"] != 0 or any(pcm):
            raise RuntimeError("WB09_SILENCE: output is not exact zero PCM")
    return metrics


def replace_generated_tree(source: Path, destination: Path, expected_parent: Path) -> None:
    resolved = destination.resolve()
    if resolved.parent != expected_parent.resolve():
        raise RuntimeError(f"refusing to replace unexpected destination: {resolved}")
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
        "-DCMAKE_BUILD_TYPE=Release", "-DWANDERBODY_ENABLE_JUCE=OFF",
    ])
    run(["cmake", "--build", str(BUILD), "--target", "wanderbody-render", "--parallel"])
    renderer = BUILD / "wanderbody-render"
    REPO_BUILD.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="wanderbody-render-matrix-", dir=REPO_BUILD) as temporary:
        matrix_root = Path(temporary)
        retained = matrix_root / "retained"
        retained.mkdir()
        baseline_hashes: dict[str, dict[str, str]] = {}
        baseline_metrics: dict[str, dict[str, Any]] = {}
        canonical_block = 127
        execution_blocks = [canonical_block, *[block for block in blocks if block != canonical_block]]
        for block in execution_blocks:
            for condition in conditions:
                directory = matrix_root / f"block-{block}" / condition
                run([
                    str(renderer), "--condition", condition,
                    "--block", str(block), "--output", str(directory),
                ])
                metrics = validate_condition(condition, directory, experiment["tolerances"])
                hashes = {name: sha256(directory / name) for name in ARTIFACT_NAMES}
                if block == canonical_block:
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

        if baseline_hashes["WB02_DRUNK"]["decisions.json"] == baseline_hashes["WB10_UNCORRELATED"]["decisions.json"]:
            raise RuntimeError("Drunk trace did not differ from the independent comparator")
        manifest = {
            "canonical_block_frames": canonical_block,
            "conditions": {
                condition: {
                    "artifacts": baseline_hashes[condition],
                    "metrics": baseline_metrics[condition],
                }
                for condition in conditions
            },
            "fingerprints": {
                "control_map": sha256(CONTROL_MAP),
                "core_header": sha256(ROOT / "include" / "wanderbody" / "core.hpp"),
                "core_source": sha256(ROOT / "src" / "core.cpp"),
                "experiment": sha256(EXPERIMENT),
                "implementation_contract": sha256(CONTRACT),
                "proposal": sha256(PROPOSAL),
                "renderer_source": sha256(ROOT / "src" / "render.cpp"),
            },
            "sample_rate_hz": experiment["sample_rate_hz"],
            "schema_version": "wanderbody-render-evidence-v1",
            "seed": experiment["seed"],
            "supported_block_frames": blocks,
        }
        manifest_text = canonical(manifest)
        (retained / "manifest.json").write_text(manifest_text, encoding="utf-8")
        if args.update_expected:
            EXPECTED.parent.mkdir(parents=True, exist_ok=True)
            EXPECTED.write_text(manifest_text, encoding="utf-8")
            replace_generated_tree(retained, RESULTS, ROOT)
            print(f"updated {EXPECTED} and {RESULTS}")
        elif not EXPECTED.is_file() or EXPECTED.read_text(encoding="utf-8") != manifest_text:
            raise RuntimeError("frozen expected render manifest does not match")
        replace_generated_tree(retained, args.output, REPO_BUILD)
    print(f"Wanderbody render matrix: passed ({len(conditions)} conditions x {len(blocks)} block sizes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
