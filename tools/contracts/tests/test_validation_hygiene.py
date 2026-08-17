from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools/contracts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from packages.schuss_core import (  # noqa: E402
    canonical_result_bytes,
    dispatch_operation,
    load_repository_context,
)
from packages.schuss_core.product_cli import render_human_result  # noqa: E402

import target_backend_build_rules as target_rules  # noqa: E402
import validator_core as core  # noqa: E402


AUDIT_PATH = (
    ROOT
    / "evidence/validation-hygiene-v1/historical-golden-hash-audit.json"
)
CONTRACT_PATH = ROOT / "docs/validation/VH-001-historical-golden-hash-audit.md"
PRESERVATION_PATH = (
    ROOT / "evidence/task-009-prerequisite-v0/pre-task-preservation.json"
)
CLI_GOLDEN_PATH = (
    ROOT / "tools/contracts/tests/fixtures/task010-cli-golden-hashes.json"
)
REQUESTS_PATH = (
    ROOT / "tools/contracts/tests/fixtures/task008-operation-requests.json"
)


def _identity(value: bytes) -> dict[str, object]:
    return {
        "byte_length": len(value),
        "byte_sha256": hashlib.sha256(value).hexdigest(),
    }


class HistoricalGoldenHashAuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))

    def test_contract_is_bounded_and_routed_outside_product_sequence(self) -> None:
        contract = CONTRACT_PATH.read_text(encoding="utf-8")
        for heading in (
            "## Goal and why it exists",
            "## In scope",
            "## Out of scope",
            "## Inputs and deliverables",
            "## Validation cadence and acceptance tests",
            "## Decisions VH-001 may make",
            "## Decisions VH-001 must not make",
            "## Completion result",
        ):
            self.assertIn(heading, contract)
        for boundary in (
            "not numbered product work",
            "Changing `catalog/sources.local.yml`",
            "Rewriting, deleting, bulk-normalizing, or re-baselining historical goldens",
            "No mismatch is a stale expected result or an actual behavioral regression",
            "No golden is updated",
        ):
            self.assertIn(boundary, contract)
        for index_path in (
            ROOT / "docs/STATUS.md",
            ROOT / "docs/HISTORY.md",
            ROOT / "docs/tasks/README.md",
        ):
            self.assertIn("VH-001", index_path.read_text(encoding="utf-8"))

    def test_decision_log_covers_exactly_five_retained_gates(self) -> None:
        self.assertEqual("historical-golden-hash-audit-v1", self.audit["schema_version"])
        self.assertEqual(5, self.audit["scope"]["mismatch_count"])
        self.assertFalse(self.audit["scope"]["configuration_behavior_changed"])
        self.assertFalse(self.audit["scope"]["configured_reproduction_performed"])
        self.assertFalse(self.audit["scope"]["goldens_updated"])
        decisions = self.audit["decisions"]
        self.assertEqual(
            {f"HGM-{index:03d}" for index in range(1, 6)},
            {item["decision_id"] for item in decisions},
        )
        self.assertEqual(
            {"invocation-fixture-environment"},
            {item["classification"] for item in decisions},
        )
        self.assertEqual(
            {"retained-configured-validation-gate"},
            {item["disposition"] for item in decisions},
        )
        self.assertTrue(all(not item["golden_updated"] for item in decisions))

    def test_original_configured_identities_remain_in_place(self) -> None:
        identities = self.audit["identities"]
        preservation = json.loads(PRESERVATION_PATH.read_text(encoding="utf-8"))
        cli_golden = json.loads(CLI_GOLDEN_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            identities["target_backend_validator_stdout"]["historical_configured"],
            preservation["validator_stdout"]["target_backend_build"],
        )
        self.assertEqual(
            identities["records_validate_canonical_result"]["historical_configured"],
            preservation["operation_result_bytes"]["records_validate"],
        )
        self.assertEqual(
            identities["records_validate_human_output"]["historical_configured"],
            cli_golden["human"]["validate-default"],
        )
        expected_hash = identities["records_validate_canonical_result"][
            "historical_configured"
        ]["byte_sha256"]
        for relative in (
            "tools/contracts/tests/test_task009_prerequisite.py",
            "tools/contracts/tests/test_task010_cli.py",
            "tools/contracts/tests/test_task011a_catalog.py",
        ):
            self.assertIn(expected_hash, (ROOT / relative).read_text(encoding="utf-8"))
        validator_hash = identities["target_backend_validator_stdout"][
            "historical_configured"
        ]["byte_sha256"]
        self.assertIn(
            validator_hash,
            (ROOT / "tools/contracts/tests/test_task008_control_plane.py").read_text(
                encoding="utf-8"
            ),
        )

    def test_one_unconfigured_count_delta_explains_all_identities(self) -> None:
        with mock.patch.object(target_rules, "_local_sources", return_value={}):
            context = load_repository_context(ROOT)
        summary = copy.deepcopy(context.task007_summary)
        boundary = self.audit["environment_boundary"]
        reference_resolution = summary["reference_resolution"]
        self.assertEqual(
            boundary["source_evidence_references"],
            reference_resolution["source_evidence_references"],
        )
        self.assertEqual(
            boundary["ordinary_unconfigured_local_verification_count"],
            reference_resolution["source_evidence_locally_verified"],
        )

        identities = self.audit["identities"]
        validator_bytes = (core.canonical_json(summary) + "\n").encode("utf-8")
        self.assertEqual(
            identities["target_backend_validator_stdout"]["ordinary_unconfigured"],
            _identity(validator_bytes),
        )
        configured_summary = copy.deepcopy(summary)
        configured_summary["reference_resolution"][
            "source_evidence_locally_verified"
        ] = boundary["historical_configured_local_verification_count"]
        self.assertEqual(
            identities["target_backend_validator_stdout"]["historical_configured"],
            _identity((core.canonical_json(configured_summary) + "\n").encode("utf-8")),
        )

        request = core.load_json(REQUESTS_PATH)["records_validate"]
        result = dispatch_operation(copy.deepcopy(request), context)
        self.assertEqual(
            identities["records_validate_canonical_result"]["ordinary_unconfigured"],
            _identity(canonical_result_bytes(result, context)),
        )
        self.assertEqual(
            identities["records_validate_human_output"]["ordinary_unconfigured"],
            _identity(render_human_result(result, context, request)),
        )

        configured_result = copy.deepcopy(result)
        configured_result["value"]["summaries"]["target_backend_build_rules"][
            "reference_resolution"
        ]["source_evidence_locally_verified"] = boundary[
            "historical_configured_local_verification_count"
        ]
        self.assertEqual(
            identities["records_validate_canonical_result"]["historical_configured"],
            _identity(canonical_result_bytes(configured_result, context)),
        )
        self.assertEqual(
            identities["records_validate_human_output"]["historical_configured"],
            _identity(render_human_result(configured_result, context, request)),
        )
        self.assertFalse(boundary["synthetic_substitution_is_provenance_evidence"])


if __name__ == "__main__":
    unittest.main()
