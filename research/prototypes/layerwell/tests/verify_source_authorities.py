#!/usr/bin/env python3
"""Verify Layerwell's frozen source, host, and surface authorities."""

from __future__ import annotations

import hashlib
import json
import subprocess
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
    "research/prototypes/pamplist/prototype-index.json":
        "25cef61387c088ebb7f721d2803202712cdbbe11f900167dee115a7e404a1cd3",
    "research/prototypes/pamplist/source-dependencies.json":
        "d7b82c51046bf96d68b726eba1ebbfc989e0d03fc4daab47f4e71f6fd71f5c38",
    "research/prototypes/pamplist/contract-r06/implementation-contract.json":
        "a0ae706d4943be17e290297f06a9587c40222a8cbe6f412184b52af9f57b971c",
    "research/prototypes/pamplist/contract-r06/source-equivalence.json":
        "1bb6d4406f7ed4ee4470a4a122565274a83c97f79488eeaf4a6d4e469b298dd7",
    "research/prototypes/pamplist/contract-r06/control-map.json":
        "d7a4a602ec55d27def522939eff47a75210412cdb1ec669f8ca0463e2c7285ab",
    "research/prototypes/pamplist/semantic-control-surface.json":
        "1944250974303b05e75059a4fa1d58d6c70d661d19ca6d60ca490b72d5b1015a",
    "research/prototypes/pamplist/THIRD_PARTY_NOTICES.md":
        "79a670e45ba454cfcc74a76c9aab84467fd145044b928e34e423efa5e21a1312",
    "research/prototype_support/instrument_lab/juce-8.0.15-source-tree.json":
        "db7daa7f6937fb8774b11784efa3977b5f8f91bb718a63cf262166c8d4115ac5",
    "research/prototype_support/controllers/novation-launch-control-3-regular-v1.json":
        "d69475e54e1bc0a3f441f0bcb5863084c73dbeff5d995670b17c8e894654510b",
}

SOURCE_TREES = {
    "Tide Pit": {
        "root": "research/prototypes/tide-pit-gills",
        "sha256": "f67ec79273c59c86557b18533aed254740992ed4846175e61d8b673f4d420252",
    },
    "Pamplist": {
        "root": "research/prototypes/pamplist",
        "sha256": "514c236f8070108710c4f52fa4133d4df44fa0b16a36a4634c2acd8d27e585bf",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    candidates = [root / "CMakeLists.txt", root / "include", root / "src"]
    paths: list[Path] = []
    for candidate in candidates:
        if candidate.is_file():
            paths.append(candidate)
        else:
            paths.extend(path for path in candidate.rglob("*") if path.is_file())
    for path in sorted(paths, key=lambda item: item.relative_to(ROOT).as_posix()):
        relative = path.relative_to(ROOT).as_posix().encode("utf-8")
        digest.update(relative + b"\0" + path.read_bytes() + b"\0")
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

    pamplist_cmake = (ROOT / "research/prototypes/pamplist/CMakeLists.txt").read_text()
    tide_cmake = (ROOT / "research/prototypes/tide-pit-gills/CMakeLists.txt").read_text()
    layerwell_cmake = (ROOT / "research/prototypes/layerwell/CMakeLists.txt").read_text()
    source_cmake_hashes = {
        "Pamplist": (pamplist_cmake, "5ce7457dc02b6556dc0f16344557943d58cd3663cb1d61d967da3685c9a5f219"),
        "Tide Pit": (tide_cmake, "cf305455847da80dbc56bce13d83922a1c30d18b41051328bf7af7bbc420dd75"),
    }
    for label, (content, expected) in source_cmake_hashes.items():
        actual = hashlib.sha256(content.encode("utf-8")).hexdigest()
        if actual != expected:
            failures.append(f"{label} standalone CMake drifted: {actual} != {expected}")

    required_snippets = (
        (layerwell_cmake, "add_subdirectory(\n    \"${CMAKE_CURRENT_SOURCE_DIR}/../tide-pit-gills\"", "unchanged Tide project inclusion"),
        (layerwell_cmake, "add_library(pamplist_macro_voice STATIC", "exact Pamplist Macro Voice composition target"),
        (layerwell_cmake, "add_library(pamplist_core STATIC", "exact Pamplist Core composition target"),
        (layerwell_cmake, "--source-root \"${PAMPLIST_PATCHER_ROOT}\"", "configured Pamplist source authentication"),
        (layerwell_cmake, "braids=tidepit_private_braids", "parent Tide Braids prefix"),
        (layerwell_cmake, "stmlib=tidepit_private_stmlib", "parent Tide stmlib prefix"),
        (layerwell_cmake, "PUBLIC SchussInstrumentLab::Core", "single Instrument Lab authority"),
    )
    for content, snippet, label in required_snippets:
        if snippet not in content:
            failures.append(f"missing composition guard: {label}")

    if "generative_drum_machine" in layerwell_cmake:
        failures.append("Generative Drums remains in Layerwell's composition graph")

    for label, authority in SOURCE_TREES.items():
        actual = source_tree_sha256(ROOT / authority["root"])
        if actual != authority["sha256"]:
            failures.append(
                f"{label} public source tree drifted: {actual} != {authority['sha256']}"
            )

    try:
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "research/prototypes/pamplist/tests/verify_source_authority.py"),
                "--json",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            failures.append(
                "Pamplist configured source authentication failed: "
                + (completed.stderr.strip() or completed.stdout.strip())
            )
        else:
            receipt = json.loads(completed.stdout)
            if receipt.get("revision") != "08d3e6e1e2b61230308c20a15ded58ffdaf4656c":
                failures.append("Pamplist configured source revision drifted")
            if receipt.get("subtree_git_tree") != "58917f3e2e46a30337cfb6292a3504845b1d5552":
                failures.append("Pamplist configured synthesis tree drifted")
    except (OSError, json.JSONDecodeError) as exc:
        failures.append(f"Pamplist configured source check failed: {exc}")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print(
        f"Layerwell source authorities passed ({len(EXPECTED)} exact files, "
        "2 exact public source trees, configured Pamplist source)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
