#!/usr/bin/env python3
"""Configure, build, and run Murmur Map's focused Core-only checks."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
BUILD = REPO_ROOT / "build" / "murmur-map-structural"


def run(command: list[str]) -> None:
    print("+ " + " ".join(command), flush=True)
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.parse_args()
    run([sys.executable, str(ROOT / "tests" / "verify_source_authorities.py")])
    run([
        "cmake", "-S", str(ROOT), "-B", str(BUILD),
        "-DCMAKE_BUILD_TYPE=Release", "-DMURMUR_MAP_ENABLE_JUCE=OFF",
    ])
    run(["cmake", "--build", str(BUILD), "--parallel"])
    run(["ctest", "--test-dir", str(BUILD), "--output-on-failure"])
    run([
        sys.executable,
        "tools/instrument_lab/validate_prototype.py",
        "--repo-root", ".",
        "--consumer-root", str(ROOT.relative_to(REPO_ROOT)),
        "--check",
    ])
    print("Murmur Map structural suite: passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
