from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools/contracts"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import validate_backbone_governance as governance


FIXTURES = ROOT / "tools/contracts/tests/fixtures/backbone-governance-negative-fixtures.json"
VALIDATOR = ROOT / "tools/contracts/validate_backbone_governance.py"


class BackboneGovernanceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.documents, cls.task_filenames = governance.load_repository_documents(ROOT)
        cls.fixtures = json.loads(FIXTURES.read_text(encoding="utf-8"))

    def test_live_repository_is_valid(self):
        summary = governance.validate_documents(self.documents, self.task_filenames)
        self.assertEqual("valid", summary["status"])
        self.assertEqual("backbone-governance-summary-v22", summary["schema_version"])
        self.assertEqual([], summary["diagnostics"])
        self.assertEqual(
            [
                "ADR 0010", "ADR 0011", "ADR 0012", "ADR 0013", "ADR 0014",
                "ADR 0015", "ADR 0016",
            ],
            summary["authoritative_decisions"],
        )
        self.assertEqual(
            "unnumbered-desktop-workspace-shell-local-implementation-active",
            summary["active_product_task"],
        )
        self.assertEqual(
            "022-failed-diagnostic-promotion-stopped",
            summary["active_evidence_task"],
        )
        self.assertEqual(
            "task032-explicit-activation-required",
            summary["promotion_gate"],
        )
        self.assertEqual(
            [
                "013", "014", "015", "016", "017", "018", "019", "020",
                "021", "022", "023", "024", "025", "026", "027", "028",
                "029", "030", "031",
            ],
            summary["active_task_sequence"],
        )
        self.assertEqual(
            "032-variable-graph-host-runtime-proposed-not-started",
            summary["next_planned_task"],
        )
        self.assertEqual(
            ["032"],
            summary["planned_task_sequence"],
        )
        self.assertEqual("complete-mapped-local-level-5", summary["task_statuses"]["018"])
        self.assertEqual(
            "complete-corrected-connected-level-6",
            summary["task_statuses"]["021"],
        )
        self.assertEqual(
            "failed-connected-diagnostic-level-6-not-earned",
            summary["task_statuses"]["022"],
        )
        self.assertEqual(
            "complete-application-surface-cli-v2",
            summary["task_statuses"]["023"],
        )
        self.assertEqual(
            "complete-current-ksoloti-catalog-lineage-level-2",
            summary["task_statuses"]["024"],
        )
        self.assertEqual(
            "complete-fail-closed-partial-level-2",
            summary["task_statuses"]["025"],
        )
        self.assertEqual(
            "complete-reverb-free-authoring-level-5",
            summary["task_statuses"]["026"],
        )
        self.assertEqual(
            "complete-mutable-catalog-provenance-level-2",
            summary["task_statuses"]["027"],
        )
        self.assertEqual(
            "complete-twenty-item-direct-palette-level-3",
            summary["task_statuses"]["028"],
        )
        self.assertEqual(
            "complete-machine-inspection-level-1",
            summary["task_statuses"]["029"],
        )
        self.assertEqual(
            "complete-mutable-catalog-cohort-level-2-cli-v3",
            summary["task_statuses"]["030"],
        )
        self.assertEqual(
            "complete-desktop-host-bounded-observation-no-level7-or-audible-promotion",
            summary["task_statuses"]["031"],
        )
        self.assertEqual(
            "proposed-variable-graph-host-runtime-not-started",
            summary["task_statuses"]["032"],
        )
        self.assertEqual(
            "unnumbered-desktop-workspace-shell-implemented-locally-target-hardware-publication-gated",
            summary["ui_milestone_status"],
        )

    def test_negative_governance_fixtures_fail_closed(self):
        self.assertEqual(
            "backbone-governance-negative-fixtures-v7", self.fixtures["schema_version"]
        )
        for fixture in self.fixtures["cases"]:
            with self.subTest(case=fixture["name"]):
                documents = copy.deepcopy(self.documents)
                path = fixture["path"]
                self.assertEqual(1, documents[path].count(fixture["old"]))
                documents[path] = documents[path].replace(fixture["old"], fixture["new"], 1)
                summary = governance.validate_documents(documents, self.task_filenames)
                codes = {diagnostic["code"] for diagnostic in summary["diagnostics"]}
                self.assertEqual("invalid", summary["status"])
                self.assertIn(fixture["expected_code"], codes)

    def test_valid_history_does_not_trigger_alias_or_ui_diagnostics(self):
        history = " ".join(self.documents[governance.ADR_0009].split())
        self.assertIn("Task 012B becomes the immediate task", history)
        self.assertIn("Tasks 013A-013D and B6 remain planned", history)
        summary = governance.validate_documents(self.documents, self.task_filenames)
        codes = {diagnostic["code"] for diagnostic in summary["diagnostics"]}
        self.assertNotIn("LETTERED_TASK_ALIAS_PRESENT", codes)
        self.assertNotIn("INFORMAL_TASK_ALIAS_PRESENT", codes)
        self.assertNotIn("TASK_012B_UI_RESURRECTED", codes)

        documents = copy.deepcopy(self.documents)
        documents[governance.HISTORY] += (
            "\nHistorical note: Task 013A and B6 were superseded planning labels.\n"
        )
        summary = governance.validate_documents(documents, self.task_filenames)
        self.assertEqual("valid", summary["status"])

    def test_missing_document_and_aliased_filename_fail_closed(self):
        documents = copy.deepcopy(self.documents)
        documents.pop(governance.ADR_0012)
        summary = governance.validate_documents(
            documents, [*self.task_filenames, "013a-reintroduced-compiler-task.md"]
        )
        codes = {diagnostic["code"] for diagnostic in summary["diagnostics"]}
        self.assertIn("GOVERNANCE_DOCUMENT_MISSING", codes)
        self.assertIn("TASK_ARCHIVE_POLICY_VIOLATION", codes)

    def test_cli_summary_is_deterministic_one_line_and_read_only(self):
        governed_paths = [ROOT / path for path in governance.DOCUMENT_PATHS]

        def snapshot():
            return {
                str(path.relative_to(ROOT)): (
                    path.stat().st_mtime_ns,
                    path.stat().st_size,
                    hashlib.sha256(path.read_bytes()).hexdigest(),
                )
                for path in governed_paths
            }

        before = snapshot()
        environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        first = subprocess.run(
            [sys.executable, str(VALIDATOR)],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            check=False,
        )
        second = subprocess.run(
            [sys.executable, str(VALIDATOR)],
            cwd=ROOT.parent,
            env=environment,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, first.returncode, first.stderr.decode("utf-8"))
        self.assertEqual(b"", first.stderr)
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(1, first.stdout.count(b"\n"))
        self.assertEqual("valid", json.loads(first.stdout)["status"])
        self.assertEqual(before, snapshot())


if __name__ == "__main__":
    unittest.main()
