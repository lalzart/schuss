from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools/contracts"
sys.path[:0] = [str(ROOT), str(TOOLS)]

import validate_task040_phase1 as validator  # noqa: E402


class Task040Phase1Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = validator.validate(ROOT)

    def test_retained_phase1_closeout_is_valid(self) -> None:
        self.assertEqual("valid", self.result["status"], self.result["errors"])
        self.assertIn(
            self.result["review_state"],
            {
                "published-phase1-review-commit",
                "phase1-review-retained-by-descendants",
            },
        )
        self.assertEqual("deferred-after-phase1", self.result["task_status"])
        self.assertFalse(self.result["phase2_implemented"])

    def test_exact_review_lineage_is_fail_closed(self) -> None:
        baseline = validator.BASELINE
        review = validator.PHASE1_REVIEW_COMMIT
        self.assertEqual(
            "baseline-with-phase1-worktree", validator._review_state(baseline, baseline)
        )
        self.assertEqual(
            "local-phase1-review-commit", validator._review_state(review, baseline)
        )
        self.assertEqual(
            "published-phase1-review-commit", validator._review_state(review, review)
        )
        self.assertIsNone(validator._review_state(baseline, review))
        self.assertIsNone(validator._review_state("f" * 40, review))

    def test_exact_allocation_and_phase2_stop_gate_are_retained(self) -> None:
        self.assertEqual("schuss-record-set-000033@1", self.result["parent_record_set"])
        self.assertEqual(
            "schuss-record-set-000034@1",
            self.result["allocated_semantic_record_set"],
        )
        self.assertEqual(
            "schuss-record-set-000035@1", self.result["allocated_native_record_set"]
        )
        self.assertEqual(9, self.result["internal_graph_node_count"])
        self.assertEqual(24, self.result["control_assignment_count"])
        self.assertEqual(7, self.result["experiment_condition_count"])


if __name__ == "__main__":
    unittest.main()
