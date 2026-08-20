#!/usr/bin/env python3
"""Check or historically reproduce the frozen Task 017 evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tarfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/contracts")]

import historical_reproduction  # noqa: E402
import retained_evidence  # noqa: E402


EVIDENCE_ROOT = ROOT / "evidence/task017-completion-v1"
HISTORICAL_COMMIT = "b28c7b6bdc98a2e06e1a19180bc84ad01fab4ac7"


def check_retained() -> dict[str, Any]:
    return retained_evidence.check_summary(
        EVIDENCE_ROOT,
        repository_root=ROOT,
        anchor_commit=HISTORICAL_COMMIT,
        schema_version="task017-validation-summary-v1",
    )


def reproduce_historical() -> dict[str, Any]:
    """Run the accepted Task 017 generator at its immutable completion commit."""

    return historical_reproduction.reproduce_summary(
        repository_root=ROOT,
        completion_commit=HISTORICAL_COMMIT,
        runner_path=Path("tools/contracts/run_task017.py"),
        retained_summary=check_retained(),
        report_schema_version="task017-historical-reproduction-v1",
        timeout=300,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--reproduce", action="store_true")
    arguments = parser.parse_args()
    try:
        summary = check_retained() if arguments.check else reproduce_historical()
    except (OSError, ValueError, subprocess.SubprocessError, tarfile.TarError) as exc:
        print("Task 017 evidence failed: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
