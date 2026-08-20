#!/usr/bin/env python3
"""Compatibility entry point for all configured-source checks."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.validation import run as validation_run  # noqa: E402


def main() -> int:
    return validation_run.main(["--profile", "configured-sources"])


if __name__ == "__main__":
    raise SystemExit(main())
