#!/usr/bin/env python3
"""Validate the bounded Task 009 authenticated-environment prerequisite."""

from __future__ import annotations

import sys
from pathlib import Path

TOOLS_ROOT = Path(__file__).resolve().parent
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

import task009_prerequisite_rules as rules
import validator_core as core


def main() -> int:
    repository_root = Path(__file__).resolve().parents[2]
    try:
        summary = rules.validate_task009_prerequisite(repository_root)
    except (KeyError, OSError, ValueError) as exc:
        summary = {
            "schema_version": "task009-prerequisite-validation-summary-v0",
            "status": "invalid",
            "diagnostics": [
                core.Diagnostic(
                    "INPUT_READ_FAILED",
                    "error",
                    "task009-prerequisite",
                    "$",
                    str(exc),
                ).as_dict()
            ],
        }
    print(core.canonical_json(summary))
    return 0 if summary["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
