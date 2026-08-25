#!/usr/bin/env python3
"""Run the unchanged standalone focused suites for both embedded sources."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]


def run(command: list[str]) -> None:
    print("+", " ".join(command), flush=True)
    completed = subprocess.run(command, cwd=ROOT, check=False, text=True)
    if completed.returncode != 0:
        raise RuntimeError(f"command failed ({completed.returncode}): {' '.join(command)}")


def build_and_test(source: str, build: str, cmake_args: list[str]) -> None:
    run([
        "cmake", "-S", source, "-B", build,
        "-DCMAKE_BUILD_TYPE=Release", *cmake_args,
    ])
    run(["cmake", "--build", build, "--parallel"])
    run(["ctest", "--test-dir", build, "--output-on-failure"])


def main() -> int:
    try:
        build_and_test(
            "research/prototypes/tide-pit-gills",
            "build/layerwell-regression-tide-pit",
            [
                "-DTIDE_PIT_ENABLE_JUCE=OFF",
            ],
        )
        build_and_test(
            "research/prototypes/pamplist",
            "build/layerwell-regression-pamplist",
            ["-DPAMPLIST_ENABLE_JUCE=OFF"],
        )
    except (OSError, RuntimeError) as exc:
        print(f"Layerwell source regression failed: {exc}", file=sys.stderr)
        return 1
    print("Layerwell affected-source regressions passed with standalone defaults")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
