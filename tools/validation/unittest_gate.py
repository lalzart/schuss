#!/usr/bin/env python3
"""Run explicitly selected unit tests and reject an unexpected skip."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("tests", nargs="+")
    arguments = parser.parse_args(argv)
    suite = unittest.defaultTestLoader.loadTestsFromNames(arguments.tests)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():
        return 1
    if result.skipped:
        print(
            "explicit validation was skipped: "
            + "; ".join(reason for _test, reason in result.skipped),
            file=sys.stderr,
        )
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
