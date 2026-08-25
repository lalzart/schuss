#!/usr/bin/env python3
"""Configure, build, and run Wanderbody's focused Core checks."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]


def run(command: list[str], environment: dict[str, str] | None = None) -> None:
    print("+ " + " ".join(command), flush=True)
    subprocess.run(command, cwd=REPO_ROOT, check=True, env=environment)


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--sanitizers", action="store_true")
    args = parser.parse_args()
    build_name = "wanderbody-sanitizers" if args.sanitizers else "wanderbody-structural"
    build = REPO_ROOT / "build" / build_name
    configure = [
        "cmake", "-S", str(ROOT), "-B", str(build),
        "-DCMAKE_BUILD_TYPE=Debug" if args.sanitizers else "-DCMAKE_BUILD_TYPE=Release",
        "-DWANDERBODY_ENABLE_JUCE=OFF",
        f"-DWANDERBODY_ENABLE_SANITIZERS={'ON' if args.sanitizers else 'OFF'}",
    ]
    run([sys.executable, str(ROOT / "tests" / "verify_provenance.py")])
    run(configure)
    run(["cmake", "--build", str(build), "--parallel"])
    environment = dict(os.environ)
    if args.sanitizers:
        environment["ASAN_OPTIONS"] = "detect_leaks=0:halt_on_error=1"
        environment["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1"
    run(["ctest", "--test-dir", str(build), "--output-on-failure"], environment)
    print(f"Wanderbody {'sanitizer' if args.sanitizers else 'structural'} suite: passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
