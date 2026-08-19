from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools/contracts"
sys.path[:0] = [str(ROOT), str(TOOLS)]

import generate_task033_phase1_audits as generator  # noqa: E402
import validate_task033_phase1 as validator  # noqa: E402
import validator_core as core  # noqa: E402


class Task033Phase1AuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mutable = core.load_jsonl(
            ROOT / "catalog/reviews/task033-mutable-provider-audit-v1/entries.jsonl"
        )
        cls.juce = core.load_jsonl(
            ROOT / "catalog/reviews/task033-juce-dsp-audit-v1/headers.jsonl"
        )

    def test_committed_packets_are_closed_and_canonical(self) -> None:
        validator.validate()

    def test_mutable_audit_does_not_invent_host_support(self) -> None:
        self.assertEqual(56, len(self.mutable))
        self.assertEqual(56, len({item["implementation_id"] for item in self.mutable}))
        for item in self.mutable:
            host = next(row for row in item["target_matrix"] if row["target"] == "desktop-host")
            self.assertEqual("no-binding-or-eligibility", host["availability"])
            self.assertNotIn("eligible", item["readiness_states"])

    def test_juce_audit_is_not_an_object_import(self) -> None:
        self.assertEqual(39, len(self.juce))
        self.assertEqual(
            [item["portable_path"] for item in generator.JUCE_HEADER_SPECS],
            [item["source"]["portable_path"] for item in self.juce],
        )
        self.assertTrue(
            all(
                item["promotion_state"]
                == "candidate-only-not-imported-not-linked-not-eligible"
                for item in self.juce
            )
        )
        self.assertTrue(
            all(
                item["architecture_recommendation"]
                in {"native-schuss-algorithm", "later-juce-host-provider", "defer"}
                for item in self.juce
            )
        )


if __name__ == "__main__":
    unittest.main()
