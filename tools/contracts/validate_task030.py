#!/usr/bin/env python3
"""Read-only Task 030 completion validator."""

from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def run(*command: str) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    run("python3", "tools/contracts/validate_task030_contract.py")
    run("python3", "tools/contracts/generate_task030_records.py", "--check")
    run("python3", "tools/contracts/generate_task030_cli_golden.py", "--check")
    run(
        "python3",
        "-m",
        "unittest",
        "tools.contracts.tests.test_task030_complete_mutable_catalog",
    )
    run("python3", "tools/contracts/run_task030_fresh_root.py", "--check")
    print("Task 030 complete Mutable-derived catalog and object CLI: valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
