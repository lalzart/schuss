#!/usr/bin/env python3
"""Configure, build, and run the focused Core-only structural suite."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
BUILD = REPO_ROOT / "build" / "generative-drum-machine-structural"


def run(command: list[str]) -> None:
    print("+ " + " ".join(command), flush=True)
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.parse_args()
    run(["python3", str(ROOT / "tools" / "generate_fixture.py"), "--check"])
    run(["python3", str(ROOT / "tools" / "generate_control_descriptors.py"), "--check"])
    run(["python3", "tools/instrument_lab/validate_task038_reuse.py"])
    run([
        "cmake", "-S", str(ROOT), "-B", str(BUILD),
        "-DCMAKE_BUILD_TYPE=Release",
    ])
    run(["cmake", "--build", str(BUILD), "--parallel"])
    run(["ctest", "--test-dir", str(BUILD), "--output-on-failure"])
    print("generative drum structural suite: passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
