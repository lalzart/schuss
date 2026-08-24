#!/usr/bin/env python3
"""Verify Layerwell's frozen source, host, and surface authorities."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]

EXPECTED = {
    "research/prototypes/tide-pit-gills/prototype-index.json":
        "8056df4d779b077247d0829a371205a47f74e916fcf514207eff9faca69616e2",
    "research/prototypes/tide-pit-gills/implementation-contract.json":
        "81071c9cac8b76770eb4184d9afd07dda5bc47a1b0bfcdd6075d56a42e01b8c2",
    "research/prototypes/tide-pit-gills/source-equivalence.json":
        "2c661c07068d552a696cb222f78c37aea27c468939f386b3a793eac82b7cf747",
    "research/prototypes/tide-pit-gills/third_party/THIRD_PARTY_NOTICES.md":
        "4e198a537ca719925bc407a073350d7708ecb15d0152fe876478e565e23a98aa",
    "research/prototypes/generative-drum-machine/prototype-index.json":
        "ecfa9c33c60ba6e35ad61e34c245533ed5fb4515a9c6e53dbc1ae504f80f6d4e",
    "research/prototypes/generative-drum-machine/contract/implementation-contract.json":
        "79c4998fecbc9914c65cdaf89834e90b4c974af3521122ab42babd6e566211d2",
    "research/prototypes/generative-drum-machine/contract/source-dependencies.json":
        "d61e5973840024075f72b40f63f6b3f06ba4cfb834c0c21c74eed1f21111ba13",
    "packages/dsp_adapters/mutable_braids_v1/ADAPTER.json":
        "c0c56698d495cbc582671cb5414f77f603fa3cba81319e221fd2910965f6facd",
    "research/prototype_support/instrument_lab/juce-8.0.15-source-tree.json":
        "db7daa7f6937fb8774b11784efa3977b5f8f91bb718a63cf262166c8d4115ac5",
    "research/prototype_support/controllers/novation-launch-control-3-regular-v1.json":
        "d69475e54e1bc0a3f441f0bcb5863084c73dbeff5d995670b17c8e894654510b",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    failures: list[str] = []
    for relative, expected in sorted(EXPECTED.items()):
        path = ROOT / relative
        if not path.is_file():
            failures.append(f"missing authority: {relative}")
            continue
        actual = sha256(path)
        if actual != expected:
            failures.append(f"authority drift: {relative}: {actual} != {expected}")

    dependency_path = (
        ROOT / "research/prototypes/layerwell/source-dependencies.json"
    )
    try:
        dependency = json.loads(dependency_path.read_text(encoding="utf-8"))
        listed = {
            item["path"]: item["sha256"]
            for item in dependency["authorities"]
        }
        if listed != EXPECTED:
            failures.append("Layerwell source-dependencies authority set drifted")
        if any(dependency["claims"].values()):
            failures.append("Layerwell source-dependencies claims must remain false")
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        failures.append(f"invalid Layerwell source-dependencies: {exc}")

    gdm_cmake = (ROOT / "research/prototypes/generative-drum-machine/CMakeLists.txt").read_text()
    tide_cmake = (ROOT / "research/prototypes/tide-pit-gills/CMakeLists.txt").read_text()
    layerwell_cmake = (ROOT / "research/prototypes/layerwell/CMakeLists.txt").read_text()
    source_cmake_hashes = {
        "Generative Drums": (gdm_cmake, "0f6ec3714738215de4d1983ae61bea44cd6fd9538bebae5ffe6800a6270ca87b"),
        "Tide Pit": (tide_cmake, "cf305455847da80dbc56bce13d83922a1c30d18b41051328bf7af7bbc420dd75"),
    }
    for label, (content, expected) in source_cmake_hashes.items():
        actual = hashlib.sha256(content.encode("utf-8")).hexdigest()
        if actual != expected:
            failures.append(f"{label} standalone CMake drifted: {actual} != {expected}")

    required_snippets = (
        (layerwell_cmake, "add_subdirectory(\n    \"${CMAKE_CURRENT_SOURCE_DIR}/../tide-pit-gills\"", "unchanged Tide project inclusion"),
        (layerwell_cmake, "add_library(generative_drum_machine_core STATIC", "exact drum Core composition target"),
        (layerwell_cmake, "braids=tidepit_private_braids", "parent Tide Braids prefix"),
        (layerwell_cmake, "stmlib=tidepit_private_stmlib", "parent Tide stmlib prefix"),
        (layerwell_cmake, "PUBLIC SchussInstrumentLab::Core", "single Instrument Lab authority"),
    )
    for content, snippet, label in required_snippets:
        if snippet not in content:
            failures.append(f"missing composition guard: {label}")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print(f"Layerwell source authorities passed ({len(EXPECTED)} exact files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
