#!/usr/bin/env python3
"""Reproduce or check the authenticated, unlaunched Layerwell JUCE build."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "research/prototypes/layerwell"
DEFAULT_BUILD = ROOT / "build/layerwell-juce-evidence"
RECEIPT = SOURCE / "contract/evidence/juce-build.json"
JUCE_MANIFEST = ROOT / "research/prototype_support/instrument_lab/juce-8.0.15-source-tree.json"
JUCE_MANIFEST_SHA256 = "db7daa7f6937fb8774b11784efa3977b5f8f91bb718a63cf262166c8d4115ac5"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def input_fingerprint() -> str:
    digest = hashlib.sha256()
    roots = [SOURCE / "CMakeLists.txt", SOURCE / "include", SOURCE / "src"]
    paths: list[Path] = []
    for candidate in roots:
        if candidate.is_file():
            paths.append(candidate)
        else:
            paths.extend(path for path in candidate.rglob("*") if path.is_file())
    paths.extend([
        ROOT / "research/prototypes/tide-pit-gills/CMakeLists.txt",
        ROOT / "research/prototypes/generative-drum-machine/CMakeLists.txt",
        JUCE_MANIFEST,
    ])
    for path in sorted(set(paths), key=lambda item: item.relative_to(ROOT).as_posix()):
        relative = path.relative_to(ROOT).as_posix().encode("utf-8")
        digest.update(relative + b"\0" + path.read_bytes() + b"\0")
    return digest.hexdigest()


def run(command: list[str]) -> None:
    print("+", " ".join(command), flush=True)
    completed = subprocess.run(command, cwd=ROOT, check=False, text=True)
    if completed.returncode != 0:
        raise RuntimeError(f"command failed ({completed.returncode}): {' '.join(command)}")


def app_binary(build: Path) -> Path:
    return build / "layerwell-instrument_artefacts/Release/Layerwell.app/Contents/MacOS/Layerwell"


def reproduce(build: Path, juce_source: Path) -> None:
    if not juce_source.is_dir():
        raise RuntimeError(f"JUCE source tree is missing: {juce_source}")
    run([
        sys.executable,
        str(ROOT / "tools/source_packages/validate_juce_source_tree.py"),
        "--repo-root", str(ROOT),
        "--source-tree", str(juce_source),
        "--check",
    ])
    run([
        "cmake", "-S", str(SOURCE), "-B", str(build),
        "-DCMAKE_BUILD_TYPE=Release",
        "-DLAYERWELL_ENABLE_JUCE=ON",
        f"-DLAYERWELL_JUCE_SOURCE_DIR={juce_source}",
        "-DLAYERWELL_ALLOW_JUCE_FETCH=OFF",
    ])
    run(["cmake", "--build", str(build), "--target", "layerwell-instrument", "--parallel"])
    binary = app_binary(build)
    if not binary.is_file():
        raise RuntimeError(f"built app binary is missing: {binary}")
    receipt = {
        "artifact": {
            "bytes": binary.stat().st_size,
            "path": binary.relative_to(ROOT).as_posix(),
            "sha256": sha256(binary),
        },
        "claims": {
            "app_launched": False,
            "audio_endpoint_opened": False,
            "midi_endpoint_opened": False,
            "target_built": True,
        },
        "input_fingerprint_sha256": input_fingerprint(),
        "juce_manifest": {
            "path": JUCE_MANIFEST.relative_to(ROOT).as_posix(),
            "sha256": sha256(JUCE_MANIFEST),
        },
        "schema_version": "layerwell-authenticated-juce-build-v1",
        "status": "passed",
        "target": "layerwell-instrument",
    }
    RECEIPT.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {RECEIPT.relative_to(ROOT)}")


def check() -> None:
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    if receipt.get("schema_version") != "layerwell-authenticated-juce-build-v1":
        raise RuntimeError("JUCE receipt schema drifted")
    if receipt.get("status") != "passed" or receipt.get("target") != "layerwell-instrument":
        raise RuntimeError("JUCE receipt does not record the named passing target")
    expected_claims = {
        "app_launched": False,
        "audio_endpoint_opened": False,
        "midi_endpoint_opened": False,
        "target_built": True,
    }
    if receipt.get("claims") != expected_claims:
        raise RuntimeError("JUCE receipt evidence claims drifted")
    if sha256(JUCE_MANIFEST) != JUCE_MANIFEST_SHA256:
        raise RuntimeError("JUCE authority manifest drifted")
    if receipt.get("juce_manifest", {}).get("sha256") != JUCE_MANIFEST_SHA256:
        raise RuntimeError("JUCE receipt manifest binding drifted")
    if receipt.get("input_fingerprint_sha256") != input_fingerprint():
        raise RuntimeError("JUCE build inputs changed after the retained build")
    artifact = receipt.get("artifact", {})
    binary = ROOT / artifact.get("path", "")
    if not binary.is_file():
        raise RuntimeError(f"retained JUCE app binary is missing: {binary}")
    if binary.stat().st_size != artifact.get("bytes") or sha256(binary) != artifact.get("sha256"):
        raise RuntimeError("retained JUCE app binary fingerprint drifted")
    print(
        "Layerwell authenticated JUCE build receipt passed; "
        "the app was not launched and no endpoint evidence is claimed"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--reproduce", action="store_true")
    parser.add_argument("--juce-source", type=Path)
    parser.add_argument("--build-dir", type=Path, default=DEFAULT_BUILD)
    args = parser.parse_args()
    try:
        if args.reproduce:
            if args.juce_source is None:
                raise RuntimeError("--juce-source is required with --reproduce")
            reproduce(args.build_dir.resolve(), args.juce_source.resolve())
        else:
            check()
    except (OSError, RuntimeError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"Layerwell JUCE build validation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
