from __future__ import annotations

import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools/contracts"

import sys

sys.path[:0] = [str(ROOT), str(TOOLS)]

import compiler_determinism_matrix as matrix
from tools.validation.profile import requires_profile


class CompilerDeterminismMatrixTest(unittest.TestCase):
    def test_parent_semantic_snapshot_authenticates_task013_through_task015(self):
        first = matrix.parent_semantic_snapshot(ROOT)
        second = matrix.parent_semantic_snapshot(ROOT)
        self.assertEqual(first, second)
        self.assertEqual(144, first["record_count"])
        self.assertTrue(first["record_members_equal"])

    def test_leak_detector_classifies_paths_and_timestamps_without_echoing_them(self):
        value = b'{"path":"/tmp/private-output","when":"2026-08-16T03:04:05"}'
        self.assertEqual(
            ["absolute-path", "known-host-path", "timestamp"],
            matrix.find_leaks(value, ("/tmp/private-output",)),
        )

    @requires_profile("native")
    def test_forward_and_reverse_worker_facts_are_identical(self):
        before = matrix.parent_semantic_snapshot(ROOT)
        with tempfile.TemporaryDirectory() as temporary:
            scratch = Path(temporary)
            forward_root = scratch / "forward"
            reverse_root = scratch / "reverse"
            forward_root.mkdir()
            reverse_root.mkdir()
            forward = matrix.worker_result(
                ROOT, "forward", forward_root, execute_task014=False
            )
            reverse = matrix.worker_result(
                ROOT, "reverse", reverse_root, execute_task014=False
            )
        self.assertEqual(matrix.canonical_bytes(forward), matrix.canonical_bytes(reverse))
        self.assertEqual(before, matrix.parent_semantic_snapshot(ROOT))
        self.assertEqual("passed", forward["task015"]["host_compile"]["status"])
        self.assertEqual("passed", forward["leak_check"])


if __name__ == "__main__":
    unittest.main()
