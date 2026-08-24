#!/usr/bin/env python3
"""Run one isolated relocated Instrument Lab Layerwell reproduction."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]


def main() -> int:
    command = [
        sys.executable,
        "tools/instrument_lab/reproduce.py",
        "--repo-root", str(ROOT),
        "--consumer-root", "research/prototypes/layerwell",
        "--cmake-arg=-DLAYERWELL_ENABLE_JUCE=OFF",
        "--ctest-regex=^layerwell_",
        "--reproduce",
    ]
    print("+", " ".join(command), flush=True)
    completed = subprocess.run(command, cwd=ROOT, check=False, text=True)
    if completed.returncode != 0:
        print("Layerwell relocated reproduction failed", file=sys.stderr)
        return completed.returncode
    print("Layerwell relocated Core reproduction passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
