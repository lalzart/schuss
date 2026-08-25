#!/usr/bin/env python3
"""Reproduce or authenticate Pamplist's unlaunched JUCE target build."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


PROTOTYPE = Path(__file__).resolve().parents[1]
REPO_ROOT = PROTOTYPE.parents[2]
DEFAULT_BUILD = REPO_ROOT / "build" / "pamplist-juce"
RECEIPT = PROTOTYPE / "contract-r06" / "juce-build.json"
JUCE_MANIFEST = REPO_ROOT / "research/prototype_support/instrument_lab/juce-8.0.15-source-tree.json"
JUCE_MANIFEST_SHA256 = "db7daa7f6937fb8774b11784efa3977b5f8f91bb718a63cf262166c8d4115ac5"
SOURCE_VERIFIER = PROTOTYPE / "tests" / "verify_source_authority.py"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(command: list[str], capture: bool = False) -> subprocess.CompletedProcess[str]:
    print("+ " + " ".join(command), flush=True)
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=False,
        text=True,
        capture_output=capture,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(command)}\n{detail}"
        )
    return completed


def source_receipt() -> dict[str, Any]:
    completed = run([sys.executable, str(SOURCE_VERIFIER), "--json"], capture=True)
    return json.loads(completed.stdout)


def input_fingerprint() -> str:
    digest = hashlib.sha256()
    roots = [
        PROTOTYPE / "CMakeLists.txt",
        PROTOTYPE / "include",
        PROTOTYPE / "src",
        PROTOTYPE / "source-dependencies.json",
        PROTOTYPE / "contract-r06/control-map.json",
        PROTOTYPE / "contract-r06/implementation-contract.json",
        JUCE_MANIFEST,
    ]
    paths: list[Path] = []
    for candidate in roots:
        if candidate.is_file():
            paths.append(candidate)
        else:
            paths.extend(path for path in candidate.rglob("*") if path.is_file())
    for path in sorted(set(paths), key=lambda item: item.relative_to(REPO_ROOT).as_posix()):
        relative = path.relative_to(REPO_ROOT).as_posix().encode("utf-8")
        digest.update(relative + b"\0" + path.read_bytes() + b"\0")
    return digest.hexdigest()


def app_binary(build: Path) -> Path:
    return build / "pamplist_artefacts/Release/Pamplist.app/Contents/MacOS/Pamplist"


def validate_surface_source() -> None:
    header = (PROTOTYPE / "include/schuss/pamplist/ui_model.hpp").read_text(
        encoding="utf-8"
    )
    source = (PROTOTYPE / "src/juce_main.cpp").read_text(encoding="utf-8")
    activity_header = (
        PROTOTYPE / "include/schuss/pamplist/activity_model.hpp"
    ).read_text(encoding="utf-8")
    if "kSurfaceRotaryCount = 16U" not in header:
        raise RuntimeError("portable surface cardinality is not exactly sixteen")
    declaration = (
        "std::array<std::unique_ptr<SurfaceSlider>, pam::kSurfaceColumnCount>"
    )
    if (
        f"{declaration}\n        top_sliders_;" not in source
        or f"{declaration}\n        bottom_sliders_;" not in source
    ):
        raise RuntimeError("JUCE source does not declare exactly two eight-slider rows")
    for required in (
        "pam::surfaceModel(snapshot)",
        "VOICE SHAPE - direct lane sound",
        "SEQUENCER - timing, pattern, and motion shape",
        "pam::LaneControlMode::voice",
        "pam::LaneControlMode::motion",
        "class SurfaceSlider final : public juce::Slider",
        "getValue() >= 0.5 ? 0.0 : 1.0",
        "presentation == pam::PresentationKind::trigger_switch",
        "if (!slider.userGestureActive())",
        "class ImpactHistoryComponent final : public juce::Component",
        "pam::ActivityReducer reducer_",
        "pam::ImpactHistory history_",
        "sample.lane_levels[lane]",
        "sample.trigger_mask",
        "sample.cohesion_level",
        "sample.effect_cleared",
        "impact_history_.pushSnapshot(snapshot)",
        "std::array<juce::Colour, pam::kLaneCount>",
        "setSize(1280, 840)",
        'return "0.6.0"',
    ):
        if required not in source:
            raise RuntimeError(f"JUCE sixteen-control contract missing: {required}")
    for forbidden in ("primary_sliders_", "lane_sliders_"):
        if forbidden in source:
            raise RuntimeError(f"obsolete extra slider bank remains: {forbidden}")
    if "kImpactHistoryCapacity = 192U" not in activity_header:
        raise RuntimeError("ImpactHistory is not the frozen 192-sample value")


def reproduce(build: Path, juce_source: Path) -> None:
    if not juce_source.is_dir():
        raise RuntimeError(f"JUCE source tree is missing: {juce_source}")
    run([
        sys.executable,
        str(REPO_ROOT / "tools/source_packages/validate_juce_source_tree.py"),
        "--repo-root", str(REPO_ROOT),
        "--source-tree", str(juce_source),
        "--check",
    ])
    source = source_receipt()
    validate_surface_source()
    run([
        "cmake", "-S", str(PROTOTYPE), "-B", str(build),
        "-DCMAKE_BUILD_TYPE=Release",
        "-DPAMPLIST_ENABLE_JUCE=ON",
        f"-DPAMPLIST_JUCE_SOURCE_DIR={juce_source}",
        "-DPAMPLIST_ALLOW_JUCE_FETCH=OFF",
    ])
    run(["cmake", "--build", str(build), "--target", "pamplist", "--parallel"])
    binary = app_binary(build)
    if not binary.is_file():
        raise RuntimeError(f"built app binary is missing: {binary}")
    document = {
        "artifact": {
            "bytes": binary.stat().st_size,
            "path": binary.relative_to(REPO_ROOT).as_posix(),
            "sha256": sha256(binary),
        },
        "claims": {
            "app_launched": False,
            "audio_endpoint_opened": False,
            "impact_history_capacity": 192,
            "impact_history_rows": 7,
            "midi_endpoint_opened": False,
            "surface_rotary_controls": 16,
            "target_built": True,
        },
        "input_fingerprint_sha256": input_fingerprint(),
        "juce_manifest": {
            "path": JUCE_MANIFEST.relative_to(REPO_ROOT).as_posix(),
            "sha256": sha256(JUCE_MANIFEST),
        },
        "schema_version": "pamplist-authenticated-juce-build-v5",
        "source_authority": source,
        "status": "passed",
        "target": "pamplist",
    }
    RECEIPT.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {RECEIPT.relative_to(REPO_ROOT)}")


def check() -> None:
    document = json.loads(RECEIPT.read_text(encoding="utf-8"))
    if document.get("schema_version") != "pamplist-authenticated-juce-build-v5":
        raise RuntimeError("JUCE receipt schema drifted")
    if document.get("status") != "passed" or document.get("target") != "pamplist":
        raise RuntimeError("JUCE receipt does not record the named passing target")
    expected_claims = {
        "app_launched": False,
        "audio_endpoint_opened": False,
        "impact_history_capacity": 192,
        "impact_history_rows": 7,
        "midi_endpoint_opened": False,
        "surface_rotary_controls": 16,
        "target_built": True,
    }
    if document.get("claims") != expected_claims:
        raise RuntimeError("JUCE build evidence claims drifted")
    if sha256(JUCE_MANIFEST) != JUCE_MANIFEST_SHA256:
        raise RuntimeError("JUCE authority manifest drifted")
    if document.get("juce_manifest", {}).get("sha256") != JUCE_MANIFEST_SHA256:
        raise RuntimeError("JUCE receipt manifest binding drifted")
    if document.get("input_fingerprint_sha256") != input_fingerprint():
        raise RuntimeError("JUCE build inputs changed after the retained build")
    validate_surface_source()
    observed_source = source_receipt()
    if document.get("source_authority") != observed_source:
        raise RuntimeError("configured source authority changed after the retained build")
    artifact = document.get("artifact", {})
    binary = REPO_ROOT / artifact.get("path", "")
    if not binary.is_file():
        raise RuntimeError(f"retained Pamplist app binary is missing: {binary}")
    if binary.stat().st_size != artifact.get("bytes") or sha256(binary) != artifact.get("sha256"):
        raise RuntimeError("retained Pamplist app binary fingerprint drifted")
    print(
        "Pamplist authenticated JUCE build receipt passed; app launch and audio/MIDI endpoint access were not performed"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--reproduce", action="store_true")
    parser.add_argument("--juce-source", type=Path)
    parser.add_argument("--build-dir", type=Path, default=DEFAULT_BUILD)
    arguments = parser.parse_args()
    try:
        if arguments.reproduce:
            if arguments.juce_source is None:
                raise RuntimeError("--juce-source is required with --reproduce")
            reproduce(arguments.build_dir.resolve(), arguments.juce_source.resolve())
        else:
            check()
    except (OSError, KeyError, TypeError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        print(f"Pamplist JUCE build validation failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
