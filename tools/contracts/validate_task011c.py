#!/usr/bin/env python3
"""Validate retained Task 011C records and evidence without tool execution."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/contracts"))

import run_task011c
import validator_core as core


def main() -> int:
    try:
        summary = run_task011c.validate()
    except (OSError, ValueError) as error:
        print(f"task011c-validator-error: {error}", file=sys.stderr)
        return 2
    print(core.canonical_json(summary))
    return 0 if summary["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
