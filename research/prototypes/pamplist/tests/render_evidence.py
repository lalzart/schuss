#!/usr/bin/env python3
"""Reproduce or authenticate Pamplist revision 0.6 objective evidence."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any
import wave


PROTOTYPE = Path(__file__).resolve().parents[1]
REPO_ROOT = PROTOTYPE.parents[2]
BUILD = REPO_ROOT / "build" / "pamplist-evidence-build"
EXPERIMENT = PROTOTYPE / "contract-r06" / "experiment.json"
EVIDENCE = PROTOTYPE / "contract-r06" / "evidence"
PREDECESSOR_AUDIO = (
    PROTOTYPE / "contract-r05/evidence/PAMP_R05_AUDIO_CMP/audio.wav"
)
PROPOSAL_SHA256 = (
    "a923b9665a6024d986a5ae8ac094aa9d41cd634de03c45c8ca954630ea43e917"
)
PREDECESSOR_AUDIO_SHA256 = (
    "a07ed1a3d461f538349cd5c12678e732d1619efc6e8ec623dce30ffd31e47912"
)
CONDITION_ARTIFACTS = (
    "SHA256SUMS",
    "activity.json",
    "audio.wav",
    "controller-trace.json",
    "events.json",
    "manifest.json",
    "metrics.json",
    "snapshots.json",
    "surface.json",
)
MODEL_NAMES = [
    "Virtual Analog VCF", "Phase Distortion", "6-Op FM A", "6-Op FM B",
    "6-Op FM C", "Wave Terrain", "String Machine", "Chiptune",
    "Virtual Analog", "Waveshaping", "2-Op FM", "Granular Formant",
    "Harmonic / Additive", "Wavetable", "Chord", "Speech", "Swarm",
    "Noise", "Particle", "String", "Modal Resonator", "Bass Drum",
    "Snare Drum", "Hi-Hat",
]


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
    names = tuple(name for name in CONDITION_ARTIFACTS if name != "SHA256SUMS")
    if tuple(expected) != names:
        raise RuntimeError(f"{directory.name}: local SHA256SUMS order drifted")
    for name, fingerprint in expected.items():
        if sha256(directory / name) != fingerprint:
            raise RuntimeError(f"{directory.name}: local artifact drifted: {name}")


def part_bytes(directory: Path, metrics: dict[str, Any]) -> dict[str, bytes]:
    with wave.open(str(directory / "audio.wav"), "rb") as stream:
        if (
            stream.getnchannels() != 2
            or stream.getframerate() != 48000
            or stream.getsampwidth() != 3
        ):
            raise RuntimeError(f"{directory.name}: WAV format drifted")
        raw = stream.readframes(stream.getnframes())
    result: dict[str, bytes] = {}
    offset = 0
    for part in metrics["parts"]:
        byte_count = part["frame_count"] * 6
        result[part["part"]] = raw[offset : offset + byte_count]
        offset += byte_count
    if offset != len(raw):
        raise RuntimeError(f"{directory.name}: part timeline does not cover WAV")
    return result


def pcm24(data: bytes) -> list[int]:
    values: list[int] = []
    for offset in range(0, len(data), 3):
        value = int.from_bytes(data[offset : offset + 3], "little")
        values.append(value - (1 << 24) if value & (1 << 23) else value)
    return values


def normalized_rms_difference(left: bytes, right: bytes) -> float:
    if len(left) != len(right):
        raise RuntimeError("RMS comparison lengths disagree")
    left_values = pcm24(left)
    right_values = pcm24(right)
    square = sum(
        (left_value - right_value) ** 2
        for left_value, right_value in zip(left_values, right_values)
    )
    return math.sqrt(square / len(left_values)) / float(1 << 23)


def validate_surface(condition: str, directory: Path) -> None:
    document = load_json(directory / "surface.json")
    if document["condition"] != condition:
        raise RuntimeError(f"{condition}: surface condition binding drifted")
    contexts = document["contexts"]
    if [context["context"] for context in contexts] != ["VOICE", "MOTION", "GLOBAL"]:
        raise RuntimeError(f"{condition}: surface context order drifted")
    for context in contexts:
        slots = context["top_slots"] + context["bottom_slots"]
        if context["rotary_slot_count"] != 16 or len(slots) != 16:
            raise RuntimeError(f"{condition}: surface is not exactly sixteen slots")
        if not context["top_group"] or not context["bottom_group"] or not context["guide"]:
            raise RuntimeError(f"{condition}: surface grouping/help is incomplete")
        if any(not slot["label"] or not slot["tooltip"] for slot in slots):
            raise RuntimeError(f"{condition}: a surface slot lacks semantic help")
    voice, motion, global_context = contexts
    for context in (voice, motion):
        semantics = [
            slot["semantic"]
            for slot in context["top_slots"] + context["bottom_slots"]
        ]
        if len(set(semantics)) != 16 or not all(
            slot["enabled"] for slot in context["top_slots"] + context["bottom_slots"]
        ):
            raise RuntimeError(f"{condition}: lane surface target contract drifted")
    if [slot["semantic"] for slot in voice["bottom_slots"]] != [
        slot["semantic"] for slot in motion["bottom_slots"]
    ]:
        raise RuntimeError(f"{condition}: Sequencer row changed with lane context")
    phase, shape, rotate = (
        voice["bottom_slots"][1], voice["bottom_slots"][2],
        voice["bottom_slots"][4],
    )
    if (
        "alignment" not in phase["tooltip"]
        or "Trigger On" not in shape["tooltip"]
        or "Hits 0 or 16" not in rotate["tooltip"]
    ):
        raise RuntimeError(f"{condition}: sequencer dependency help drifted")
    if "require Cohere above zero" not in global_context["guide"]:
        raise RuntimeError(f"{condition}: Global dependency help drifted")
    if [slot["enabled"] for slot in global_context["bottom_slots"]] != [
        True, True, False, False, False, False, False, False
    ]:
        raise RuntimeError(f"{condition}: Global reserved-slot contract drifted")


def phase_messages(trace: dict[str, Any], phase: str) -> list[dict[str, Any]]:
    return [message for message in trace["messages"] if message["phase"] == phase]


def validate_controller_trace(condition: str, directory: Path) -> None:
    trace = load_json(directory / "controller-trace.json")
    messages = trace["messages"]
    if not messages or any(message["surface_slot_count"] != 16 for message in messages):
        raise RuntimeError(f"{condition}: controller surface cardinality drifted")
    trigger = [
        message for message in phase_messages(trace, "motion-top")
        if message["cc"] == 20
    ]
    if {message["value"]: message["continuous"] for message in trigger} != {
        0: 0, 63: 0, 64: 1, 127: 1
    }:
        raise RuntimeError(f"{condition}: Trigger Off/On boundary drifted")
    by_phase = {message["phase"]: message for message in messages}
    if (
        by_phase["enter-global"]["accepted_selected_page"] != 7
        or by_phase["clear-global"]["accepted_clear_generation"] != 1
        or by_phase["clear-global-hold"]["status"] != "accepted-hold"
    ):
        raise RuntimeError(f"{condition}: Global entry/Clear edge grammar drifted")


def event_trigger_frames(
    events: list[dict[str, Any]], metrics: dict[str, Any]
) -> dict[str, list[int]]:
    offsets: dict[str, int] = {}
    cursor = 0
    for part in metrics["parts"]:
        offsets[part["part"]] = cursor
        cursor += part["frame_count"]
    result: dict[str, list[int]] = {name: [] for name in offsets}
    for event in events:
        if event["trigger_lane_mask"] & 1:
            result[event["part"]].append(
                event["absolute_frame"] - offsets[event["part"]]
            )
    return result


def validate_common(condition: str, directory: Path) -> tuple[
    dict[str, Any], list[dict[str, Any]], dict[str, Any]
]:
    validate_local_manifest(directory)
    manifest = load_json(directory / "manifest.json")
    if (
        manifest["condition"] != condition
        or manifest["model_names"] != MODEL_NAMES
        or manifest["proposal_sha256"] != PROPOSAL_SHA256
        or manifest["predecessor_audio_sha256"] != PREDECESSOR_AUDIO_SHA256
        or manifest["renderer_revision"] != 6
    ):
        raise RuntimeError(f"{condition}: renderer authority binding drifted")
    for name, fingerprint in manifest["files"].items():
        if sha256(directory / name) != fingerprint:
            raise RuntimeError(f"{condition}: manifest file binding drifted: {name}")

    metrics = load_json(directory / "metrics.json")
    if (
        metrics["finite_samples_percent"] != 100
        or metrics["peak_main_q27"] > 134217727
        or metrics["peak_auxiliary_q27"] > 134217727
    ):
        raise RuntimeError(f"{condition}: finite/Q27 bound failed")
    for field in (
        "saturated_frame_count", "diagnostic_saturated_sample_count",
        "effect_recovery_count",
    ):
        if metrics[field] != 0:
            raise RuntimeError(f"{condition}: nominal metric {field} is nonzero")
    if not 0 <= metrics["maximum_mode_frequency_hz"] < 21600:
        raise RuntimeError(f"{condition}: modal frequency guard failed")
    if not 0 <= metrics["maximum_mode_pole"] < 1:
        raise RuntimeError(f"{condition}: modal pole guard failed")

    snapshots = load_json(directory / "snapshots.json")["snapshots"]
    if len(snapshots) != len(metrics["parts"]):
        raise RuntimeError(f"{condition}: part/snapshot cardinality drifted")
    for snapshot in snapshots:
        diagnostics = snapshot["diagnostics"]
        for field in (
            "clamped_control_count", "effect_recovery_count",
            "invalid_control_count", "non_finite_source_count",
            "saturated_sample_count", "unsupported_process_count",
        ):
            if diagnostics[field] != 0:
                raise RuntimeError(
                    f"{condition}: nominal diagnostic {field} is nonzero"
                )
        if any(
            not math.isfinite(value) or value < 0
            for value in snapshot["lane_output_energy"]
        ):
            raise RuntimeError(f"{condition}: lane energy is invalid")

    activity = load_json(directory / "activity.json")
    if activity["condition"] != condition:
        raise RuntimeError(f"{condition}: activity condition binding drifted")
    validate_controller_trace(condition, directory)
    validate_surface(condition, directory)
    return metrics, snapshots, activity


def validate_dry(
    directory: Path, metrics: dict[str, Any], snapshots: list[dict[str, Any]]
) -> dict[str, Any]:
    if sha256(directory / "audio.wav") != PREDECESSOR_AUDIO_SHA256:
        raise RuntimeError("PAMP_R06_DRY_CMP: revision 0.5 dry parity failed")
    if len(metrics["parts"]) != 1 or len(snapshots) != 1:
        raise RuntimeError("PAMP_R06_DRY_CMP: comparator shape drifted")
    snapshot = snapshots[0]
    if (
        snapshot["accepted"]["cohesion"]["cohere"] != 0
        or snapshot["started_lane_mask"] != 0x7F
        or any(value <= 0 for value in snapshot["lane_output_energy"])
    ):
        raise RuntimeError("PAMP_R06_DRY_CMP: dry seven-lane state drifted")
    return {
        "audio_sha256": sha256(directory / "audio.wav"),
        "lane_output_energy": snapshot["lane_output_energy"],
    }


def validate_sequence(
    directory: Path, metrics: dict[str, Any], snapshots: list[dict[str, Any]]
) -> dict[str, Any]:
    expected = [
        "phase-0", "phase-64", "rotate-3", "trigger-only-triangle",
        "routed-pulse", "routed-triangle", "routed-sine", "routed-ramp",
        "routed-decay", "routed-hold", "routed-smooth",
    ]
    if [part["part"] for part in metrics["parts"]] != expected:
        raise RuntimeError("PAMP_R06_SEQUENCE: part order drifted")
    chunks = part_bytes(directory, metrics)
    events = load_json(directory / "events.json")["events"]
    triggers = event_trigger_frames(events, metrics)
    accepted = {snapshot["part"]: snapshot["accepted"] for snapshot in snapshots}
    base = accepted["phase-0"]["lanes"][0]
    if (
        triggers["phase-0"] == triggers["phase-64"]
        or base["hits"] != accepted["phase-64"]["lanes"][0]["hits"]
        or base["rate_index"] != accepted["phase-64"]["lanes"][0]["rate_index"]
    ):
        raise RuntimeError("PAMP_R06_SEQUENCE: Phase response/dependency failed")
    if (
        len(triggers["phase-0"]) != 5
        or len(triggers["rotate-3"]) != 5
        or triggers["phase-0"] == triggers["rotate-3"]
        or base["hits"] != accepted["rotate-3"]["lanes"][0]["hits"]
    ):
        raise RuntimeError("PAMP_R06_SEQUENCE: Rotate response/cardinality failed")
    if (
        chunks["phase-0"] != chunks["trigger-only-triangle"]
        or triggers["phase-0"] != triggers["trigger-only-triangle"]
    ):
        raise RuntimeError("PAMP_R06_SEQUENCE: trigger-only Shape parity failed")
    routed = [name for name in expected if name.startswith("routed-")]
    if len({hashlib.sha256(chunks[name]).digest() for name in routed}) != len(routed):
        raise RuntimeError("PAMP_R06_SEQUENCE: routed Shape PCM is not distinct")
    differences: dict[str, float] = {}
    for name in routed[1:]:
        difference = normalized_rms_difference(chunks["routed-pulse"], chunks[name])
        differences[name] = difference
        if difference <= 5e-4:
            raise RuntimeError(f"PAMP_R06_SEQUENCE: {name} response is too small")
        if triggers[name] != triggers["routed-pulse"]:
            raise RuntimeError(f"PAMP_R06_SEQUENCE: {name} changed trigger timing")
    return {
        "phase_0_trigger_frames": triggers["phase-0"],
        "phase_64_trigger_frames": triggers["phase-64"],
        "rotate_3_trigger_frames": triggers["rotate-3"],
        "routed_shape_rms_difference_from_pulse": differences,
        "trigger_only_shape_audio_equal": True,
    }


def validate_global(
    directory: Path, metrics: dict[str, Any], snapshots: list[dict[str, Any]]
) -> dict[str, Any]:
    parameters = ["drive", "root", "spread", "tail", "damping", "width", "duck"]
    chunks = part_bytes(directory, metrics)
    differences: dict[str, float] = {}
    for parameter in parameters:
        difference = normalized_rms_difference(
            chunks[f"{parameter}-low"], chunks[f"{parameter}-high"]
        )
        differences[parameter] = difference
        if difference < 5e-4:
            raise RuntimeError(
                f"PAMP_R06_GLOBAL: {parameter} response {difference:.9f} is too small"
            )
    tail_peak = max(abs(value) for value in pcm24(chunks["tail-before-clear"]))
    if tail_peak / float(1 << 23) < 5e-4:
        raise RuntimeError("PAMP_R06_GLOBAL: pre-Clear tail is too quiet")
    if any(chunks["after-clear"]) or not any(chunks["no-clear-continue"]):
        raise RuntimeError("PAMP_R06_GLOBAL: Clear exact-zero/reference failed")

    events = load_json(directory / "events.json")["events"]
    clear_events = [event for event in events if event["effect_cleared"]]
    if len(clear_events) != 1 or clear_events[0]["part"] != "after-clear":
        raise RuntimeError("PAMP_R06_GLOBAL: Clear provenance event drifted")
    by_part = {snapshot["part"]: snapshot for snapshot in snapshots}
    cleared = by_part["after-clear"]
    reference = by_part["no-clear-continue"]
    cleared_controls = copy.deepcopy(cleared["accepted"])
    cleared_controls["effect_clear_generation"] = reference["accepted"][
        "effect_clear_generation"
    ]
    if cleared_controls != reference["accepted"]:
        raise RuntimeError("PAMP_R06_GLOBAL: Clear changed accepted musical controls")
    for key in (
        "lane_addresses", "lane_phase_q32", "lane_remainders", "lane_steps",
        "master_phase_q32", "master_remainder", "resolved_levels",
        "resolved_models", "resolved_notes", "source_random_states",
        "started_lane_mask",
    ):
        if cleared[key] != reference[key]:
            raise RuntimeError(f"PAMP_R06_GLOBAL: Clear changed {key}")
    if (
        cleared["diagnostics"]["lane_trigger_count"]
        != reference["diagnostics"]["lane_trigger_count"]
        or cleared["diagnostics"]["effect_clear_count"] != 1
        or any(cleared["cohesion"]["mode_real"])
        or any(cleared["cohesion"]["mode_imaginary"])
        or cleared["cohesion"]["duck_envelope"] != 0
    ):
        raise RuntimeError("PAMP_R06_GLOBAL: Clear state isolation failed")
    return {
        "after_clear_nonzero_samples": sum(value != 0 for value in pcm24(chunks["after-clear"])),
        "global_parameter_rms_differences": differences,
        "no_clear_continue_nonzero_samples": sum(
            value != 0 for value in pcm24(chunks["no-clear-continue"])
        ),
        "tail_before_clear_peak_normalized": tail_peak / float(1 << 23),
    }


def validate_activity(
    metrics: dict[str, Any],
    snapshots: list[dict[str, Any]],
    activity: dict[str, Any],
) -> dict[str, Any]:
    if len(snapshots) != 202 or snapshots[-2]["part"] != "activity-clear":
        raise RuntimeError("PAMP_R06_ACTIVITY: frozen activity timeline drifted")
    running = snapshots[:-2]
    for previous, current in zip(running, running[1:]):
        if current["absolute_frame"] <= previous["absolute_frame"]:
            raise RuntimeError("PAMP_R06_ACTIVITY: frame telemetry is not monotone")
        if any(
            right < left
            for left, right in zip(
                previous["lane_output_energy"], current["lane_output_energy"]
            )
        ):
            raise RuntimeError("PAMP_R06_ACTIVITY: lane energy is not monotone")
    if any(value <= 0 for value in running[-1]["lane_output_energy"]):
        raise RuntimeError("PAMP_R06_ACTIVITY: an active lane has no energy")
    if (
        any(snapshots[-1]["lane_output_energy"])
        or snapshots[-1]["started_lane_mask"] != 0
    ):
        raise RuntimeError("PAMP_R06_ACTIVITY: unstarted rebase is not silent")

    samples = activity["samples"]
    if len(samples) != len(snapshots):
        raise RuntimeError("PAMP_R06_ACTIVITY: reducer sample count drifted")
    for sample in samples:
        values = sample["lane_levels"] + [sample["cohesion_level"]]
        if any(not math.isfinite(value) or not 0 <= value <= 1 for value in values):
            raise RuntimeError("PAMP_R06_ACTIVITY: display level escaped [0,1]")
    if not all(
        any(sample["lane_levels"][lane] > 0 for sample in samples)
        for lane in range(7)
    ):
        raise RuntimeError("PAMP_R06_ACTIVITY: a lane never reached the display")
    if not any(sample["cohesion_level"] > 0 for sample in samples):
        raise RuntimeError("PAMP_R06_ACTIVITY: cohesion field never became active")
    clear_samples = [sample for sample in samples if sample["effect_cleared"]]
    if len(clear_samples) != 1 or clear_samples[0]["part"] != "activity-clear":
        raise RuntimeError("PAMP_R06_ACTIVITY: Clear marker reduction drifted")
    reset = samples[-1]
    if (
        not reset["rebased"]
        or reset["frame_count"] != 0
        or reset["trigger_mask"] != 0
        or reset["effect_cleared"]
        or any(reset["lane_levels"])
    ):
        raise RuntimeError("PAMP_R06_ACTIVITY: reset produced false activity")
    history = activity["history"]
    if (
        history["capacity"] != 192
        or history["maximum_size"] != 192
        or history["size_before_rebase"] != 192
        or history["final_size"] != 0
    ):
        raise RuntimeError("PAMP_R06_ACTIVITY: fixed history contract drifted")
    if metrics["effect_clear_count"] != 1:
        raise RuntimeError("PAMP_R06_ACTIVITY: accepted Clear count drifted")
    return {
        "clear_marker_count": len(clear_samples),
        "final_active_lane_energy": running[-1]["lane_output_energy"],
        "history": history,
        "rebase_is_exact_zero": True,
    }


def validate_condition(condition: str, directory: Path) -> dict[str, Any]:
    metrics, snapshots, activity = validate_common(condition, directory)
    if condition == "PAMP_R06_DRY_CMP":
        observations = validate_dry(directory, metrics, snapshots)
    elif condition == "PAMP_R06_SEQUENCE":
        observations = validate_sequence(directory, metrics, snapshots)
    elif condition == "PAMP_R06_GLOBAL":
        observations = validate_global(directory, metrics, snapshots)
    elif condition == "PAMP_R06_ACTIVITY":
        observations = validate_activity(metrics, snapshots, activity)
    else:
        raise RuntimeError(f"unknown revision 0.6 condition: {condition}")
    result = copy.deepcopy(metrics)
    result["validated_observations"] = observations
    return result


def write_top_level_manifest(
    destination: Path,
    blocks: list[int],
    condition_names: list[str],
    hashes: dict[str, dict[str, str]],
    metrics: dict[str, dict[str, Any]],
) -> None:
    if hashes["PAMP_R06_DRY_CMP"]["audio.wav"] != PREDECESSOR_AUDIO_SHA256:
        raise RuntimeError("revision 0.5 audio comparator did not match")
    manifest = {
        "comparator": {
            "audio_equal": True,
            "expected_sha256": PREDECESSOR_AUDIO_SHA256,
            "id": "PAMP_R06_DRY_CMP",
            "predecessor": "contract-r05/PAMP_R05_AUDIO_CMP",
        },
        "conditions": {
            condition: {
                "artifacts": hashes[condition],
                "metrics": metrics[condition],
            }
            for condition in condition_names
        },
        "proposal_sha256": PROPOSAL_SHA256,
        "sample_rate_hz": 48000,
        "schema_version": "pamplist-render-evidence-v5",
        "seed": 1346456912,
        "supported_block_frames": blocks,
    }
    (destination / "evidence-manifest.json").write_text(
        canonical(manifest), encoding="utf-8"
    )
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
        raise RuntimeError("missing retained Pamplist revision 0.6 evidence")
    if (
        not PREDECESSOR_AUDIO.is_file()
        or sha256(PREDECESSOR_AUDIO) != PREDECESSOR_AUDIO_SHA256
    ):
        raise RuntimeError("revision 0.5 predecessor audio is missing or drifted")
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
    for condition in conditions:
        directory = destination / condition
        hashes = condition_hashes(directory)
        if hashes != manifest["conditions"][condition]["artifacts"]:
            raise RuntimeError(f"{condition}: retained manifest binding drifted")
        validated_metrics = validate_condition(condition, directory)
        if validated_metrics != manifest["conditions"][condition]["metrics"]:
            raise RuntimeError(f"{condition}: retained objective metrics drifted")
    if sha256(destination / "PAMP_R06_DRY_CMP/audio.wav") != sha256(
        PREDECESSOR_AUDIO
    ):
        raise RuntimeError("retained revision 0.5 dry parity no longer holds")
    print(f"Pamplist retained revision 0.6 render evidence: valid ({destination})")


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
    run([
        "cmake", "--build", str(BUILD), "--target", "pamplist-render",
        "--parallel",
    ])
    with tempfile.TemporaryDirectory(prefix="pamplist-r06-render-") as temporary:
        root = Path(temporary)
        baseline_hashes: dict[str, dict[str, str]] = {}
        baseline_metrics: dict[str, dict[str, Any]] = {}
        for block in blocks:
            for condition in conditions:
                output = root / f"block-{block}" / condition
                run([
                    str(BUILD / "pamplist-render"),
                    "--condition", condition,
                    "--block", str(block),
                    "--output", str(output),
                ])
                hashes = condition_hashes(output)
                condition_metrics = validate_condition(condition, output)
                if block == blocks[0]:
                    baseline_hashes[condition] = hashes
                    baseline_metrics[condition] = condition_metrics
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
            destination, blocks, conditions, baseline_hashes, baseline_metrics
        )
    authenticate_retained(destination)
    print(f"Pamplist revision 0.6 render matrix reproduced: {destination}")


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
    except (
        OSError, KeyError, ValueError, RuntimeError, subprocess.CalledProcessError
    ) as error:
        print(f"Pamplist render evidence failed: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
