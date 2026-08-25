#!/usr/bin/env python3
"""Build the authenticated JUCE standalone without launching it."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]


def run(command: list[str]) -> None:
    print("+ " + " ".join(command), flush=True)
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-dir", type=Path, required=True)
    parser.add_argument("--juce-source-dir", type=Path, required=True)
    args = parser.parse_args()
    juce_source = args.juce_source_dir.resolve()
    if not (juce_source / "CMakeLists.txt").is_file():
        raise SystemExit(f"authenticated JUCE source prerequisite is missing: {juce_source}")
    build = args.build_dir.resolve()
    run([sys.executable, str(ROOT / "tests" / "verify_source_authorities.py")])
    run([
        "cmake", "-S", str(ROOT), "-B", str(build),
        "-DCMAKE_BUILD_TYPE=Release",
        "-DMURMUR_MAP_ENABLE_JUCE=ON",
        f"-DMURMUR_MAP_JUCE_SOURCE_DIR={juce_source}",
        "-DMURMUR_MAP_ALLOW_JUCE_FETCH=OFF",
    ])
    run(["cmake", "--build", str(build), "--config", "Release", "--parallel"])
    run(["ctest", "--test-dir", str(build), "--output-on-failure"])
    executable = (
        build / "murmur-map_artefacts" / "Release" / "Murmur Map.app"
        / "Contents" / "MacOS" / "Murmur Map"
    )
    if not executable.is_file():
        raise SystemExit(f"standalone executable was not produced: {executable}")
    run(["file", str(executable)])
    print(f"standalone executable sha256: {sha256(executable)}")
    print(f"standalone executable bytes: {executable.stat().st_size}")
    print("Murmur Map target build: passed (application not launched)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
