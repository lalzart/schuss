#!/usr/bin/env python3
"""Run Task 024/025 checks that require ignored local source locations."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LOCAL_SOURCES = ROOT / "catalog/sources.local.yml"
COMMAND = "python3 tools/contracts/validate_task024_025_configured_sources.py"
TEST_NAMES = (
    "tools.contracts.tests.test_task024_catalog_coverage."
    "Task024CatalogCoverageTest.test_generated_outputs_are_fresh_and_byte_deterministic",
    "tools.contracts.tests.test_task025_direct_core."
    "Task025DirectCoreTest.test_reverb_source_audit_and_absent_native_records_are_exact",
    "tools.contracts.tests.test_task025_direct_core."
    "Task025DirectCoreTest.test_generated_records_are_fresh_and_deterministic",
)


def main() -> int:
    if not LOCAL_SOURCES.is_file():
        print(
            "Configured Task 024/025 source validation not run: prerequisite "
            "catalog/sources.local.yml is absent. Configure existing pinned "
            f"source checkout locations, then run `{COMMAND}`.",
            file=sys.stderr,
        )
        return 2

    suite = unittest.defaultTestLoader.loadTestsFromNames(TEST_NAMES)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
