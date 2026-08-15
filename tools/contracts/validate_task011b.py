#!/usr/bin/env python3
"""Validate the exact Task 011B successor record set without executing it."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import validator_core as core
from task011b_rules import MANIFEST_PATH, validate_task011b


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=ROOT)
    parser.add_argument("--record-set", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()
    try:
        summary = validate_task011b(args.repository_root, args.record_set)
    except (OSError, ValueError) as exc:
        print(f"task011b-validator-error: {exc}", file=sys.stderr)
        return 2
    print(core.canonical_json(summary))
    return 0 if summary["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
