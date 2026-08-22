#!/usr/bin/env python3
"""Run the cheap Task 038 source-authority and reuse closure."""

from __future__ import annotations

import subprocess
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
COMMANDS = (
    ("tools/contracts/generate_task038_source_records.py", "--check"),
    ("tools/contracts/validate_task038_source_records.py",),
    ("tools/source_packages/generate_mutable_direct_v1.py", "--check"),
    (
        "tools/source_packages/validate_source_package.py",
        "packages/dsp_sources/mutable_eurorack_braids_v1",
    ),
    (
        "tools/source_packages/validate_source_package.py",
        "packages/dsp_sources/mutable_stmlib_v1",
    ),
    ("tools/instrument_lab/generate_task038_source_dependencies.py", "--check"),
    (
        "tools/instrument_lab/validate_prototype.py",
        "--repo-root", ".",
        "--consumer-root", "research/prototypes/generative-drum-machine",
        "--check",
    ),
)


def main() -> int:
    for arguments in COMMANDS:
        subprocess.run([sys.executable, *arguments], cwd=ROOT, check=True)
    print("Task 038 reusable source closure: valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
