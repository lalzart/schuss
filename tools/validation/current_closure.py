#!/usr/bin/env python3
"""Validate the newest semantic closure without replaying every task module."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/contracts")]

import validate_task033_phase2  # noqa: E402


def main() -> int:
    try:
        result = validate_task033_phase2.validate()
    except (OSError, ValueError) as exc:
        print(f"current closure invalid: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if result.get("status") == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
