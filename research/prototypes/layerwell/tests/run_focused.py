#!/usr/bin/env python3
"""Configure and run the focused Release and sanitizer Layerwell closures."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "research/prototypes/layerwell"


def run(command: list[str], *, environment: dict[str, str] | None = None) -> None:
    print("+", " ".join(command), flush=True)
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        check=False,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"command failed ({completed.returncode}): {' '.join(command)}")


def closure(build: Path, *, sanitizer: bool) -> None:
    run([
        "cmake", "-S", str(SOURCE), "-B", str(build),
        f"-DCMAKE_BUILD_TYPE={'Debug' if sanitizer else 'Release'}",
        f"-DLAYERWELL_ENABLE_SANITIZERS={'ON' if sanitizer else 'OFF'}",
        "-DLAYERWELL_ENABLE_JUCE=OFF",
    ])
    run(["cmake", "--build", str(build), "--parallel"])
    environment = dict(os.environ)
    if sanitizer:
        environment.update({
            "ASAN_OPTIONS": "halt_on_error=1:abort_on_error=1",
            "UBSAN_OPTIONS": "halt_on_error=1:print_stacktrace=1",
        })
    run(
        [
            "ctest", "--test-dir", str(build), "--output-on-failure",
            "-R", "^layerwell_",
        ],
        environment=environment,
    )


def main() -> int:
    try:
        closure(ROOT / "build/layerwell-focused", sanitizer=False)
        closure(ROOT / "build/layerwell-sanitizers", sanitizer=True)
    except (OSError, RuntimeError) as exc:
        print(f"Layerwell focused validation failed: {exc}", file=sys.stderr)
        return 1
    print("Layerwell focused Release and ASan/UBSan closures passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
