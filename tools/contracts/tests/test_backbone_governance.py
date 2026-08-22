from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import unittest

from tools.validation.profile import requires_profile


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools/contracts"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import validate_backbone_governance as governance


FIXTURES = (
    ROOT
    / "tools/contracts/tests/fixtures/task035-backbone-governance-negative-fixtures.json"
)
VALIDATOR = ROOT / "tools/contracts/validate_backbone_governance.py"


class BackboneGovernanceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.documents, cls.task_filenames = governance.load_repository_documents(ROOT)
        cls.fixtures = json.loads(FIXTURES.read_text(encoding="utf-8"))

    @staticmethod
    def _replace_section(text, heading, body):
        marker = f"## {heading}"
        prefix, remainder = text.split(marker, 1)
        _section, separator, tail = remainder.partition("\n## ")
        suffix = "" if not separator else "\n## " + tail
        return prefix + marker + "\n\n" + body + "\n" + suffix

    def _documents_with_active_fixture(self):
        documents = copy.deepcopy(self.documents)
        state = json.loads(documents[governance.STATE])
        old_marker = governance.routing_marker(state)
        contract = "docs/tasks/035-validation-and-governance-consolidation.md"
        state["active_task"] = {
            "task_id": "999",
            "phase": None,
            "kind": "maintenance",
            "status": "in-progress",
            "contract": contract,
            "baseline_commit": "88788c5ed9b7acd5f1c19b675b2aa7afcdce0a81",
        }
        state["evidence_boundary"] = {
            key: False for key in state["evidence_boundary"]
        }
        new_marker = governance.routing_marker(state)
        documents[governance.STATE] = json.dumps(state, indent=2) + "\n"
        for path in (governance.STATUS, governance.ROADMAP, governance.TASKS_INDEX):
            documents[path] = documents[path].replace(old_marker, new_marker, 1)
        documents[governance.STATUS] = self._replace_section(
            documents[governance.STATUS],
            "Current work",
            "Task 999 is the only active task and is in progress.",
        )
        documents[governance.ROADMAP] = self._replace_section(
            documents[governance.ROADMAP],
            "Active maintenance",
            "Task 999 is in progress.",
        )
        documents[governance.TASKS_INDEX] = self._replace_section(
            documents[governance.TASKS_INDEX],
            "Active",
            "- Task 999, `035-validation-and-governance-consolidation.md`, is in progress.",
        )
        documents[contract] = """# Synthetic active maintenance contract

Status: explicitly authorized and implementation in progress.

## Goal and why it exists

Exercise generic active-state validation.

## In scope

Test-only governance state.

## Out of scope

Production changes.

## Inputs and deliverables

One synthetic document mapping.

## Acceptance tests

The generic validator accepts the coherent mapping.

## Decisions

No product decision.
"""
        return documents, state

    def test_live_repository_is_valid(self):
        summary = governance.validate_documents(self.documents, self.task_filenames)
        self.assertEqual("valid", summary["status"], summary["diagnostics"])
        self.assertEqual("backbone-governance-summary-v27", summary["schema_version"])
        self.assertEqual([], summary["diagnostics"])
        self.assertEqual(governance.STATE, summary["current_status_source"])
        state = json.loads(self.documents[governance.STATE])
        self.assertEqual(state["active_task"], summary["active_task"])
        self.assertEqual(state["next_candidate"], summary["next_candidate"])
        self.assertEqual(
            state["authoritative_decisions"], summary["authoritative_decisions"]
        )
        self.assertEqual(
            governance._derived_task_statuses(state), summary["task_statuses"]
        )

    def test_structured_negative_fixtures_fail_closed(self):
        self.assertEqual(
            "backbone-governance-negative-fixtures-v11",
            self.fixtures["schema_version"],
        )
        for fixture in self.fixtures["cases"]:
            with self.subTest(case=fixture["name"]):
                documents = copy.deepcopy(self.documents)
                path = fixture["path"]
                self.assertEqual(1, documents[path].count(fixture["old"]))
                documents[path] = documents[path].replace(
                    fixture["old"], fixture["new"], 1
                )
                summary = governance.validate_documents(
                    documents, self.task_filenames
                )
                self.assertEqual("invalid", summary["status"])
                self.assertIn(
                    fixture["expected_code"],
                    {item["code"] for item in summary["diagnostics"]},
                )

    def test_active_state_and_contract_shape_fail_closed_without_fixed_task_literals(self):
        documents, state = self._documents_with_active_fixture()
        active = state["active_task"]
        self.assertIsNotNone(active)

        invalid_state = copy.deepcopy(state)
        invalid_state["active_task"]["status"] = "complete-local"
        invalid_documents = copy.deepcopy(documents)
        invalid_documents[governance.STATE] = json.dumps(invalid_state, indent=2) + "\n"
        summary = governance.validate_documents(invalid_documents, self.task_filenames)
        self.assertIn(
            "ACTIVE_TASK_INVALID",
            {item["code"] for item in summary["diagnostics"]},
        )

        contract = active["contract"]
        self.assertEqual(1, documents[contract].count("## Acceptance tests"))
        documents[contract] = documents[contract].replace(
            "## Acceptance tests", "## Informal checks", 1
        )
        summary = governance.validate_documents(documents, self.task_filenames)
        self.assertIn(
            "TASK_CONTRACT_INCOMPLETE",
            {item["code"] for item in summary["diagnostics"]},
        )

    def test_active_phase_and_cross_field_work_units_are_structural(self):
        documents, state = self._documents_with_active_fixture()
        phased = copy.deepcopy(state)
        phased["active_task"]["phase"] = 3
        diagnostics = []
        governance._validate_state(phased, documents, diagnostics)
        self.assertNotIn("ACTIVE_TASK_INVALID", {item["code"] for item in diagnostics})

        active = state["active_task"]
        mutations = []
        duplicated_next = copy.deepcopy(state)
        duplicated_next["next_candidate"] = {
            "task_id": active["task_id"],
            "phase": active["phase"],
            "status": "not-activated",
        }
        mutations.append(duplicated_next)
        completed_active = copy.deepcopy(state)
        completed_active["recent_completed_milestones"].append(
            {
                "task_id": active["task_id"],
                "phase": active["phase"],
                "status": "complete-local",
                "commit": active["baseline_commit"],
            }
        )
        mutations.append(completed_active)
        deferred_active = copy.deepcopy(state)
        deferred_active["deferred_tasks"].append(active["task_id"])
        mutations.append(deferred_active)
        for mutated in mutations:
            with self.subTest(mutated=mutated):
                mutated_documents = copy.deepcopy(documents)
                mutated_documents[governance.STATE] = json.dumps(mutated, indent=2) + "\n"
                summary = governance.validate_documents(
                    mutated_documents, self.task_filenames
                )
                self.assertIn(
                    "WORK_UNIT_STATE_INVALID",
                    {item["code"] for item in summary["diagnostics"]},
                )

    def test_active_status_transition_requires_matching_status_prose(self):
        def replace_in_section(text, heading, old, new):
            marker = f"## {heading}"
            prefix, remainder = text.split(marker, 1)
            section, separator, tail = remainder.partition("\n## ")
            self.assertIn(old, section)
            section = section.replace(old, new, 1)
            suffix = "" if not separator else "\n## " + tail
            return prefix + marker + section + suffix

        documents, state = self._documents_with_active_fixture()
        old_marker = governance.routing_marker(state)
        live_status = state["active_task"]["status"]
        alternate_status = (
            "review-ready" if live_status == "in-progress" else "in-progress"
        )
        phrases = {"in-progress": "in progress", "review-ready": "review-ready"}
        state["active_task"]["status"] = alternate_status
        new_marker = governance.routing_marker(state)
        documents[governance.STATE] = json.dumps(state, indent=2) + "\n"
        for path in (governance.STATUS, governance.ROADMAP, governance.TASKS_INDEX):
            documents[path] = documents[path].replace(old_marker, new_marker, 1)
        contract = state["active_task"]["contract"]
        documents[contract], count = re.subn(
            re.escape(phrases[live_status]).replace(r"\ ", r"\s+"),
            phrases[alternate_status],
            documents[contract],
            count=1,
        )
        self.assertEqual(1, count)
        headings = {
            governance.STATUS: "Current work",
            governance.ROADMAP: "Active maintenance",
            governance.TASKS_INDEX: "Active",
        }
        for path, heading in headings.items():
            documents[path] = replace_in_section(
                documents[path],
                heading,
                phrases[live_status],
                phrases[alternate_status],
            )
        coherent = governance.validate_documents(documents, self.task_filenames)
        self.assertEqual("valid", coherent["status"], coherent["diagnostics"])

        stale_documents = copy.deepcopy(documents)
        stale_documents[governance.TASKS_INDEX] = replace_in_section(
            stale_documents[governance.TASKS_INDEX],
            headings[governance.TASKS_INDEX],
            phrases[alternate_status],
            phrases[live_status],
        )
        stale = governance.validate_documents(stale_documents, self.task_filenames)
        self.assertIn(
            "GOVERNANCE_INDEX_INVALID",
            {item["code"] for item in stale["diagnostics"]},
        )

    def test_no_active_task_transition_requires_clean_active_sections(self):
        documents, state = self._documents_with_active_fixture()
        old_marker = governance.routing_marker(state)
        state["active_task"] = None
        new_marker = governance.routing_marker(state)
        documents[governance.STATE] = json.dumps(state, indent=2) + "\n"
        for path in (governance.STATUS, governance.ROADMAP, governance.TASKS_INDEX):
            documents[path] = documents[path].replace(old_marker, new_marker, 1)
        documents[governance.STATUS] = self._replace_section(
            documents[governance.STATUS], "Current work", "There is no active task."
        )
        documents[governance.ROADMAP] = self._replace_section(
            documents[governance.ROADMAP],
            "Active maintenance",
            "There is no active task.",
        )
        documents[governance.TASKS_INDEX] = self._replace_section(
            documents[governance.TASKS_INDEX], "Active", "There is no active task."
        )
        summary = governance.validate_documents(documents, self.task_filenames)
        self.assertEqual("valid", summary["status"], summary["diagnostics"])

    def test_historical_aliases_and_new_archive_files_are_not_live_routing(self):
        documents = copy.deepcopy(self.documents)
        documents[governance.HISTORY] += (
            "\nHistorical note: Task 013A and B6 were superseded labels.\n"
        )
        summary = governance.validate_documents(
            documents, [*self.task_filenames, "research-note.md"]
        )
        self.assertEqual("valid", summary["status"], summary["diagnostics"])

    def test_missing_document_and_live_aliased_filename_fail_closed(self):
        documents = copy.deepcopy(self.documents)
        adr0012 = next(
            path for path in documents if path.startswith("docs/decisions/0012-")
        )
        documents.pop(adr0012)
        summary = governance.validate_documents(
            documents, [*self.task_filenames, "013a-reintroduced-task.md"]
        )
        codes = {item["code"] for item in summary["diagnostics"]}
        self.assertIn("AUTHORITATIVE_DECISION_INVALID", codes)
        self.assertIn("TASK_FILENAME_INVALID", codes)

    def test_in_process_summary_is_deterministic_and_read_only(self):
        governed_paths = [ROOT / path for path in self.documents]

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
        first = governance.summary_bytes(
            governance.validate_documents(self.documents, self.task_filenames)
        )
        second = governance.summary_bytes(
            governance.validate_documents(self.documents, self.task_filenames)
        )
        self.assertEqual(first, second)
        self.assertEqual(1, first.count(b"\n"))
        self.assertEqual("valid", json.loads(first)["status"])
        self.assertEqual(before, snapshot())

    @requires_profile("reproduction")
    def test_cli_summary_is_deterministic_across_working_directories(self):
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


if __name__ == "__main__":
    unittest.main()
