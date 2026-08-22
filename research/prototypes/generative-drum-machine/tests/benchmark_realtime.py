#!/usr/bin/env python3
"""Build and reproduce the synthetic fixed-capacity callback-kernel benchmark."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform
import subprocess


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
BUILD = REPO_ROOT / "build" / "generative-drum-machine-structural"
EXECUTABLE = BUILD / "generative_drum_machine_realtime_benchmark"


def run(command: list[str]) -> None:
    print("+ " + " ".join(command), flush=True)
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reproduce", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    run([
        "cmake", "-S", str(ROOT), "-B", str(BUILD),
        "-DCMAKE_BUILD_TYPE=Release",
    ])
    run([
        "cmake", "--build", str(BUILD), "--target",
        "generative_drum_machine_realtime_benchmark", "--parallel",
    ])
    completed = subprocess.run(
        [str(EXECUTABLE)],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    document = json.loads(completed.stdout)
    if document.get("passed") is not True:
        raise RuntimeError("synthetic callback benchmark did not pass")
    document["host"] = {
        "machine": platform.machine(),
        "platform": platform.platform(),
        "processor": platform.processor(),
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(arguments.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
