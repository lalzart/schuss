#!/usr/bin/env python3
"""Run the one explicitly authorized bounded Task 031 local Mac smoke."""

from __future__ import annotations

import argparse
import hashlib
import platform
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/contracts")]

from packages.schuss_core.audio_sessions import AudioSessionService, SubprocessEngineTransport
from packages.schuss_core.control_plane import core
from packages.schuss_core.project_service import ProjectService


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", required=True, type=Path)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--block", type=int, default=128)
    parser.add_argument("--duration-ms", type=int, default=1000)
    value = parser.parse_args()
    if not 1 <= value.block <= 512:
        parser.error("--block must be from 1 through 512")
    if not 100 <= value.duration_ms <= 2000:
        parser.error("--duration-ms must be from 100 through 2000")
    return value


def compiler_version() -> str:
    completed = subprocess.run(
        ["/usr/bin/xcrun", "clang++", "--version"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if completed.returncode:
        return "unavailable"
    first = completed.stdout.splitlines()[0].strip()
    return first or "unavailable"


def main() -> int:
    option = arguments()
    project_service = ProjectService(option.workspace, repository_root=ROOT)
    loaded = project_service.load()
    project_reference = {
        "project_id": loaded.manifest["project_id"],
        "revision": loaded.manifest["revision"],
        "content_hash": loaded.manifest["content_hash"],
    }
    protocol_schema = loaded.context.schemas["host_engine_protocol"]
    service = AudioSessionService(
        project_service,
        lambda: SubprocessEngineTransport(option.engine, protocol_schema),
    )
    try:
        devices = service.inspect_devices(
            inspection_intent="enumerate-local-audio-midi"
        )
        started = service.start(
            project_reference=project_reference,
            sample_rate_hz=48000,
            block_frames=option.block,
            start_intent="start-local-audio-session",
        )
        time.sleep(option.duration_ms / 1000.0)
        inspected = service.inspect(started["audio_session_id"])
        stopped = service.stop(
            started["audio_session_id"],
            stop_intent="stop-local-audio-session",
        )
        if stopped["status"] != "stopped":
            raise RuntimeError("LOCAL_SMOKE_STOP_NOT_CONFIRMED")
    finally:
        service.close()

    engine = inspected["engine"]
    diagnostics = [
        {
            "code": "LOCAL_REAL_TIME_SMOKE_BOUNDED",
            "severity": "info",
            "message": "One bounded local Mac callback observation completed; no sustained headroom or listening claim is made.",
        }
    ]
    if engine["midi_inputs_open"] == 0:
        diagnostics.append(
            {
                "code": "LOCAL_MIDI_INPUT_UNAVAILABLE",
                "severity": "info",
                "message": "No physical Core MIDI input was available during this smoke; native queue behavior is covered by deterministic tests.",
            }
        )
    observation = {
        "schema_version": "host-runtime-observation-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "content_hash": "sha256:" + "0" * 64,
        "observation_kind": "local-real-time-smoke",
        "status": "success",
        "package_content_hash": inspected["package_content_hash"],
        "configuration": {
            "sample_rate_hz": engine["sample_rate_hz"],
            "block_frames": engine["block_frames"],
            "render_frames": engine["processed_frames"],
            "output_channels": 2,
        },
        "device": {
            "status": "opened",
            "audio_device_name": engine["device_name"],
            "midi_input_count": engine["midi_inputs_open"],
        },
        "toolchain": {
            "compiler_id": "AppleClang",
            "compiler_version": compiler_version(),
            "target_triple": f"{platform.machine()}-apple-darwin",
            "runtime_abi": "schuss-rt-abi-v0",
        },
        "output": {
            "media_type": "audio/wav",
            "byte_length": 0,
            "byte_sha256": hashlib.sha256(b"").hexdigest(),
        },
        "metrics": {
            "processed_frames": engine["processed_frames"],
            "midi_events_delivered": engine["midi_events_delivered"],
            "queue_overflows": engine["queue_overflows"],
            "xruns": engine["xruns"],
            "callback_cpu_ratio_max": engine["callback_cpu_ratio_max"],
            "callback_duration_us_max": engine["callback_duration_us_max"],
        },
        "diagnostics": diagnostics,
        "evidence_boundary": {
            "host_execution_only": True,
            "real_time_level_7_promoted": False,
            "audible_level_8_promoted": False,
            "ksoloti_equivalence_claimed": False,
            "release_readiness_claimed": False,
        },
    }
    schema = loaded.context.schemas["host_runtime_observation"]
    observation["content_hash"] = core.record_content_hash(observation, schema)
    errors = core.schema_errors(observation, schema, schema)
    if errors:
        raise RuntimeError("LOCAL_SMOKE_OBSERVATION_INVALID: " + "; ".join(errors))
    option.output.write_bytes(core.canonical_json(observation).encode("utf-8") + b"\n")
    print(
        core.canonical_json(
            {
                "audio_device_name": engine["device_name"],
                "block_frames": engine["block_frames"],
                "callback_duration_us_max": engine["callback_duration_us_max"],
                "package_content_hash": inspected["package_content_hash"],
                "processed_frames": engine["processed_frames"],
                "sample_rate_hz": engine["sample_rate_hz"],
                "status": "success",
                "xruns": engine["xruns"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
