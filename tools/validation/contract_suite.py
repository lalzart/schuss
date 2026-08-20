#!/usr/bin/env python3
"""Run the current or compatibility partition of ordinary contract tests."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.validation import run as validation_run  # noqa: E402


def _leaf_tests(suite: unittest.TestSuite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _leaf_tests(item)
        else:
            yield item


def selected_suite(partition: str) -> unittest.TestSuite:
    manifest = validation_run._load_manifest()
    compatibility = set(manifest["compatibility_test_modules"])
    all_modules = {
        f"tools.contracts.tests.{path.stem}"
        for path in (ROOT / "tools/contracts/tests").glob("test_*.py")
        if path.is_file()
    }
    selected_modules = (
        compatibility if partition == "compatibility" else all_modules - compatibility
    )
    if not selected_modules:
        raise ValueError(f"no {partition} contract tests were selected")
    return unittest.defaultTestLoader.loadTestsFromNames(sorted(selected_modules))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--partition", required=True, choices=("current", "compatibility"))
    arguments = parser.parse_args(argv)
    result = unittest.TextTestRunner(verbosity=1).run(selected_suite(arguments.partition))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
