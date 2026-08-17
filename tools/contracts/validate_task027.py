#!/usr/bin/env python3
"""Read-only Task 027 completion validator."""

from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def run(*command: str) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    run("python3", "tools/contracts/validate_task027_contract.py")
    run("python3", "tools/contracts/generate_task027_records.py", "--check")
    run("python3", "-m", "unittest", "tools.contracts.tests.test_task027_mutable_catalog")
    run("python3", "tools/contracts/run_task027_fresh_root.py", "--check")
    print("Task 027 Mutable-related catalog provenance: valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
