#!/usr/bin/env python3
"""Reproduce or authenticate Pamplist revision 0.5 objective evidence."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any
import wave


PROTOTYPE = Path(__file__).resolve().parents[1]
REPO_ROOT = PROTOTYPE.parents[2]
BUILD = REPO_ROOT / "build" / "pamplist-evidence-build"
EXPERIMENT = PROTOTYPE / "contract-r05" / "experiment.json"
EVIDENCE = PROTOTYPE / "contract-r05" / "evidence"
PREDECESSOR_AUDIO = PROTOTYPE / "contract-r04/evidence/PAMP_R04_DRY7/audio.wav"
PROPOSAL_SHA256 = "8c15dd3c38ca8a585c2603d219daccbba9446dff7a08156e0ba579fac25e1423"
PREDECESSOR_AUDIO_SHA256 = (
    "a07ed1a3d461f538349cd5c12678e732d1619efc6e8ec623dce30ffd31e47912"
)
CONDITION_ARTIFACTS = (
    "SHA256SUMS",
    "audio.wav",
    "controller-trace.json",
    "events.json",
    "manifest.json",
    "metrics.json",
    "snapshots.json",
    "surface.json",
)
MODEL_NAMES = [
    "Virtual Analog VCF",
    "Phase Distortion",
    "6-Op FM A",
    "6-Op FM B",
    "6-Op FM C",
    "Wave Terrain",
    "String Machine",
    "Chiptune",
    "Virtual Analog",
    "Waveshaping",
    "2-Op FM",
    "Granular Formant",
    "Harmonic / Additive",
    "Wavetable",
    "Chord",
    "Speech",
    "Swarm",
    "Noise",
    "Particle",
    "String",
    "Modal Resonator",
    "Bass Drum",
    "Snare Drum",
    "Hi-Hat",
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


def wav_chunks(path: Path, chunk_frames: int) -> list[bytes]:
    with wave.open(str(path), "rb") as stream:
        if (
            stream.getnchannels() != 2
            or stream.getframerate() != 48000
            or stream.getsampwidth() != 3
        ):
            raise RuntimeError(f"{path}: WAV format drifted")
        chunks: list[bytes] = []
        while stream.tell() < stream.getnframes():
            chunks.append(stream.readframes(chunk_frames))
        return chunks


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
            raise RuntimeError(f"{condition}: a surface slot lacks label/help")
    voice, motion, global_context = contexts
    if not all(slot["enabled"] for slot in voice["top_slots"] + voice["bottom_slots"]):
        raise RuntimeError(f"{condition}: Voice has a disabled semantic slot")
    if not all(slot["enabled"] for slot in motion["top_slots"] + motion["bottom_slots"]):
        raise RuntimeError(f"{condition}: Motion has a disabled semantic slot")
    for context in (voice, motion):
        semantics = [
            slot["semantic"]
            for slot in context["top_slots"] + context["bottom_slots"]
        ]
        if len(set(semantics)) != 16:
            raise RuntimeError(f"{condition}: lane context has duplicate targets")
    if [slot["semantic"] for slot in voice["bottom_slots"]] != [
        slot["semantic"] for slot in motion["bottom_slots"]
    ]:
        raise RuntimeError(f"{condition}: Sequencer row changed with lane context")
    trigger = motion["top_slots"][0]
    if (
        trigger["label"] != "TRIGGER"
        or trigger["minimum"] != 0
        or trigger["maximum"] != 1
        or trigger["interval"] != 1
    ):
        raise RuntimeError(f"{condition}: Trigger is not a binary surface slot")
    enabled_global_bottom = [slot["enabled"] for slot in global_context["bottom_slots"]]
    if enabled_global_bottom != [True, True, False, False, False, False, False, False]:
        raise RuntimeError(f"{condition}: Global disabled-slot contract drifted")


def phase_messages(trace: dict[str, Any], phase: str) -> list[dict[str, Any]]:
    return [message for message in trace["messages"] if message["phase"] == phase]


def validate_controller_trace(condition: str, directory: Path) -> None:
    trace = load_json(directory / "controller-trace.json")
    messages = trace["messages"]
    if not all(message["surface_slot_count"] == 16 for message in messages):
        raise RuntimeError(f"{condition}: controller trace lost the sixteen-slot surface")

    voice = phase_messages(trace, "voice-top")
    if not voice or any(message["lane_change_mask"] != 0 for message in voice):
        raise RuntimeError(f"{condition}: Voice top row changed Motion/Sequencer state")
    if any(message["voice_change_mask"] not in (0, 1) for message in voice):
        raise RuntimeError(f"{condition}: Voice top row changed a non-selected voice")

    motion = phase_messages(trace, "motion-top")
    if not motion or any(message["voice_change_mask"] != 0 for message in motion):
        raise RuntimeError(f"{condition}: Motion top row changed a base voice")
    if any(message["lane_change_mask"] not in (0, 1) for message in motion):
        raise RuntimeError(f"{condition}: Motion top row changed a non-selected lane")
    trigger = [message for message in motion if message["cc"] == 20]
    expected_trigger = {0: 0, 63: 0, 64: 1, 127: 1}
    if {message["value"]: message["continuous"] for message in trigger} != expected_trigger:
        raise RuntimeError(f"{condition}: Trigger controller boundary drifted")

    motion_bottom = phase_messages(trace, "sequencer-motion")
    voice_bottom = phase_messages(trace, "sequencer-voice")
    motion_transforms = {
        (message["cc"], message["value"]): (
            message["continuous"], message["discrete"], message["integer"]
        )
        for message in motion_bottom
    }
    voice_transforms = {
        (message["cc"], message["value"]): (
            message["continuous"], message["discrete"], message["integer"]
        )
        for message in voice_bottom
    }
    if motion_transforms != voice_transforms:
        raise RuntimeError(f"{condition}: Sequencer transforms depend on lane context")
    if any(message["voice_change_mask"] != 0 for message in motion_bottom + voice_bottom):
        raise RuntimeError(f"{condition}: Sequencer changed a voice record")

    by_phase = {message["phase"]: message for message in messages}
    toggle = by_phase["toggle-motion"]
    if not (
        toggle["status"] == "accepted-press"
        and toggle["before_lane_control_mode"] == 0
        and toggle["accepted_lane_control_mode"] == 1
        and toggle["lane_change_mask"] == 0
        and toggle["voice_change_mask"] == 0
    ):
        raise RuntimeError(f"{condition}: selected-lane mode toggle drifted")
    if by_phase["toggle-motion-hold"]["status"] != "accepted-hold":
        raise RuntimeError(f"{condition}: duplicate mode edge was not a hold")
    select_lane = by_phase["select-lane-2"]
    if not (
        select_lane["accepted_selected_page"] == 1
        and select_lane["accepted_lane_control_mode"] == 1
        and select_lane["lane_change_mask"] == 0
        and select_lane["voice_change_mask"] == 0
    ):
        raise RuntimeError(f"{condition}: lane selection did not preserve Motion")

    global_messages = phase_messages(trace, "global")
    if any(
        message["lane_change_mask"] != 0
        or message["voice_change_mask"] != 0
        or message["accepted_lane_control_mode"] != 1
        for message in global_messages
    ):
        raise RuntimeError(f"{condition}: Global changed lane/voice/mode state")
    enter = by_phase["enter-global"]
    clear = by_phase["clear-global"]
    if not (
        enter["accepted_selected_page"] == 7
        and enter["accepted_clear_generation"] == 0
        and clear["accepted_clear_generation"] == 1
        and by_phase["clear-global-hold"]["status"] == "accepted-hold"
    ):
        raise RuntimeError(f"{condition}: Global entry/Clear edge grammar drifted")
    returned = by_phase["return-lane-1"]
    if returned["accepted_selected_page"] != 0 or returned["accepted_lane_control_mode"] != 1:
        raise RuntimeError(f"{condition}: Motion did not survive Global excursion")
    if trace["diagnostics"]["ignored_global"] != 24:
        raise RuntimeError(f"{condition}: Global no-op count drifted")


def normalized_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(snapshot)
    result.pop("part", None)
    return result


def validate_condition(condition: str, directory: Path) -> dict[str, Any]:
    validate_local_manifest(directory)
    manifest = load_json(directory / "manifest.json")
    if manifest["model_names"] != MODEL_NAMES:
        raise RuntimeError(f"{condition}: source-order model names drifted")
    if manifest["proposal_sha256"] != PROPOSAL_SHA256:
        raise RuntimeError(f"{condition}: proposal fingerprint drifted")
    if manifest["predecessor_audio_sha256"] != PREDECESSOR_AUDIO_SHA256:
        raise RuntimeError(f"{condition}: predecessor comparator binding drifted")
    if manifest["renderer_revision"] != 5:
        raise RuntimeError(f"{condition}: renderer revision drifted")

    metrics = load_json(directory / "metrics.json")
    if metrics["finite_samples_percent"] != 100:
        raise RuntimeError(f"{condition}: non-finite sample tolerance failed")
    if metrics["peak_main_q27"] > 134217727 or metrics["peak_auxiliary_q27"] > 134217727:
        raise RuntimeError(f"{condition}: Q27 output bound failed")
    for field in (
        "saturated_frame_count",
        "diagnostic_saturated_sample_count",
        "effect_recovery_count",
    ):
        if metrics[field] != 0:
            raise RuntimeError(f"{condition}: nominal metric {field} is nonzero")
    if not 0 <= metrics["maximum_mode_frequency_hz"] < 21600:
        raise RuntimeError(f"{condition}: modal frequency guard failed")
    if not 0 <= metrics["maximum_mode_pole"] < 1:
        raise RuntimeError(f"{condition}: modal pole guard failed")

    snapshots = load_json(directory / "snapshots.json")["snapshots"]
    for snapshot in snapshots:
        diagnostics = snapshot["diagnostics"]
        for field in (
            "clamped_control_count",
            "effect_recovery_count",
            "invalid_control_count",
            "non_finite_source_count",
            "saturated_sample_count",
            "unsupported_process_count",
        ):
            if diagnostics[field] != 0:
                raise RuntimeError(f"{condition}: nominal diagnostic {field} is nonzero")

    validate_controller_trace(condition, directory)
    validate_surface(condition, directory)

    if condition == "PAMP_R05_AUDIO_CMP":
        if sha256(directory / "audio.wav") != PREDECESSOR_AUDIO_SHA256:
            raise RuntimeError("PAMP_R05_AUDIO_CMP: revision 0.4 audio parity failed")
        snapshot = snapshots[-1]
        if [voice["model"] for voice in snapshot["accepted"]["voices"]] != [
            0, 3, 6, 9, 12, 15, 21
        ]:
            raise RuntimeError("PAMP_R05_AUDIO_CMP: seven-model set drifted")
        if snapshot["accepted"]["lane_control_mode"] != 0:
            raise RuntimeError("PAMP_R05_AUDIO_CMP: accepted mode is not Voice")
        if snapshot["started_lane_mask"] != 0x7F:
            raise RuntimeError("PAMP_R05_AUDIO_CMP: not all voices started")
    elif condition == "PAMP_R05_TRIGGER":
        parts = metrics["parts"]
        if [part["part"] for part in parts] != [
            "trigger-cc0", "trigger-cc63", "trigger-cc64", "trigger-cc127"
        ]:
            raise RuntimeError("PAMP_R05_TRIGGER: part order drifted")
        for part in parts[:2]:
            if (
                part["nonzero_main"] != 0
                or part["nonzero_auxiliary"] != 0
                or part["trigger_count"] != 0
                or part["started_lane_mask"] != 0
            ):
                raise RuntimeError("PAMP_R05_TRIGGER: Off is not exact silence")
        for part in parts[2:]:
            if (
                part["nonzero_main"] == 0
                or part["nonzero_auxiliary"] == 0
                or part["trigger_count"] == 0
                or part["started_lane_mask"] != 1
            ):
                raise RuntimeError("PAMP_R05_TRIGGER: On is inactive")
        chunks = wav_chunks(directory / "audio.wav", 8192)
        if chunks[0] != chunks[1] or any(chunks[0]) or chunks[2] != chunks[3]:
            raise RuntimeError("PAMP_R05_TRIGGER: Off/On byte equivalence failed")
        accepted_triggers = [snapshot["accepted"]["lanes"][0]["routes"][0] for snapshot in snapshots]
        if accepted_triggers != [0, 0, 1, 1]:
            raise RuntimeError("PAMP_R05_TRIGGER: accepted Trigger states drifted")
        if normalized_snapshot(snapshots[2]) != normalized_snapshot(snapshots[3]):
            raise RuntimeError("PAMP_R05_TRIGGER: CC64 and CC127 state diverged")
        events = load_json(directory / "events.json")["events"]
        by_part: dict[str, list[dict[str, Any]]] = {}
        for event in events:
            normalized = dict(event)
            part = normalized.pop("part")
            by_part.setdefault(part, []).append(normalized)
        for part_events in by_part.values():
            if part_events:
                origin = part_events[0]["absolute_frame"]
                for event in part_events:
                    event["absolute_frame"] -= origin
        if by_part["trigger-cc64"] != by_part["trigger-cc127"]:
            raise RuntimeError("PAMP_R05_TRIGGER: CC64 and CC127 events diverged")
    elif condition == "PAMP_R05_SURFACE":
        chunks = wav_chunks(directory / "audio.wav", 16384)
        if len(chunks) != 2 or chunks[0] != chunks[1]:
            raise RuntimeError("PAMP_R05_SURFACE: Voice/Motion changed PCM")
        if [snapshot["accepted"]["lane_control_mode"] for snapshot in snapshots] != [0, 1]:
            raise RuntimeError("PAMP_R05_SURFACE: mode snapshots drifted")
    elif condition == "PAMP_R05_GLOBAL":
        chunks = wav_chunks(directory / "audio.wav", 16384)
        if len(chunks) != 2 or chunks[0] != chunks[1]:
            raise RuntimeError("PAMP_R05_GLOBAL: page selection changed PCM")
        if [snapshot["accepted"]["selected_page"] for snapshot in snapshots] != [0, 7]:
            raise RuntimeError("PAMP_R05_GLOBAL: selected-page snapshots drifted")
        if any(snapshot["accepted"]["lane_control_mode"] != 1 for snapshot in snapshots):
            raise RuntimeError("PAMP_R05_GLOBAL: Motion was not retained")
    else:
        raise RuntimeError(f"unknown revision 0.5 condition: {condition}")
    return metrics


def write_top_level_manifest(
    destination: Path,
    blocks: list[int],
    condition_names: list[str],
    hashes: dict[str, dict[str, str]],
    metrics: dict[str, dict[str, Any]],
) -> None:
    comparator_audio = hashes["PAMP_R05_AUDIO_CMP"]["audio.wav"]
    if comparator_audio != PREDECESSOR_AUDIO_SHA256:
        raise RuntimeError("revision 0.4 audio comparator did not match")
    manifest = {
        "comparator": {
            "audio_equal": True,
            "expected_sha256": PREDECESSOR_AUDIO_SHA256,
            "id": "PAMP_R05_AUDIO_CMP",
            "predecessor": "contract-r04/PAMP_R04_DRY7",
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
        "schema_version": "pamplist-render-evidence-v4",
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
        raise RuntimeError("missing retained Pamplist revision 0.5 evidence")
    if not PREDECESSOR_AUDIO.is_file() or sha256(PREDECESSOR_AUDIO) != PREDECESSOR_AUDIO_SHA256:
        raise RuntimeError("revision 0.4 predecessor audio is missing or drifted")
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
        validate_condition(condition, directory)
    if sha256(destination / "PAMP_R05_AUDIO_CMP/audio.wav") != sha256(PREDECESSOR_AUDIO):
        raise RuntimeError("retained revision 0.4 audio parity no longer holds")
    print(f"Pamplist retained revision 0.5 render evidence: valid ({destination})")


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
    with tempfile.TemporaryDirectory(prefix="pamplist-r05-render-") as temporary:
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
                        name
                        for name in CONDITION_ARTIFACTS
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
    print(f"Pamplist revision 0.5 render matrix reproduced: {destination}")


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
