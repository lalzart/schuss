from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools/contracts"
sys.path[:0] = [str(ROOT), str(TOOLS)]

import validate_task033_phase4 as validator  # noqa: E402


class Task033Phase4IntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = validator.validate(ROOT)

    def test_complete_phase4_handoff_is_valid(self) -> None:
        result = self.result
        self.assertEqual("valid", result["status"])
        self.assertEqual(1, result["selected_tranche_count"])
        self.assertEqual("040", result["selected_next_task"])
        self.assertEqual("new-design", result["selected_lane"])

    def test_audit_counts_and_runtime_boundary_are_retained(self) -> None:
        result = self.result
        self.assertEqual(56, result["mutable_audit_count"])
        self.assertEqual(39, result["juce_audit_count"])
        self.assertEqual(7, result["factory_count"])
        self.assertTrue(result["phase3_runtime_bytes_preserved"])

    def test_followup_allocates_no_phase4_semantics_or_ui(self) -> None:
        result = self.result
        self.assertFalse(result["ui_implemented"])
        self.assertFalse(
            result["semantic_record_provider_or_operation_allocated_in_phase4"]
        )
        self.assertFalse(
            result["device_realtime_listening_or_publication_performed"]
        )

    def test_unexpected_next_candidate_fails_closed(self) -> None:
        original_json = validator._json

        def changed_state(root: Path, path: Path):
            value = original_json(root, path)
            if path == validator.STATE:
                value = copy.deepcopy(value)
                value["next_candidate"] = {
                    "task_id": "041",
                    "phase": None,
                    "status": "not-activated",
                }
            return value

        with mock.patch.object(validator, "_json", side_effect=changed_state):
            with self.assertRaisesRegex(
                ValueError, "TASK033_PHASE4_GOVERNANCE_NEXT_STATE_INVALID"
            ):
                validator.validate(ROOT)

    def test_cinderwheel_authorities_are_exact(self) -> None:
        task = (ROOT / validator.TASK040).read_text()
        for expected in validator.PROTOTYPE_AUTHORITIES.values():
            self.assertIn(expected, task)


if __name__ == "__main__":
    unittest.main()
