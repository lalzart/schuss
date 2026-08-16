from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools/contracts"
for value in (ROOT, TOOLS):
    if str(value) not in sys.path:
        sys.path.insert(0, str(value))

import validate_task023
import validator_core as core


FIXTURE = ROOT / "tools/contracts/tests/fixtures/task023-smoke-cases.json"


class Task023ApplicationSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.before_fixture = FIXTURE.read_bytes()
        cls.result = validate_task023.validate(ROOT, fresh_roots=True)

    @classmethod
    def tearDownClass(cls) -> None:
        if FIXTURE.read_bytes() != cls.before_fixture:
            raise AssertionError("Task 023 smoke mutated its fixture")

    def test_smoke_crosses_the_exact_read_only_application_spine(self):
        smoke = self.result["smoke"]
        self.assertEqual("valid", self.result["status"])
        self.assertEqual("valid", smoke["status"])
        self.assertEqual("schuss-record-set-000015@1", smoke["record_set"])
        self.assertEqual(
            [
                "application.describe",
                "catalog.search",
                "catalog.inspect",
                "project.inspect",
                "project.validate",
                "graph.inspect",
                "build.plan",
                "gills.inspect",
            ],
            [item["operation"] for item in smoke["cases"]],
        )
        self.assertTrue(all(item["status"] == "success" for item in smoke["cases"]))

    def test_two_fresh_roots_processes_and_varied_environments_are_identical(self):
        self.assertEqual("identical", self.result["fresh_roots"])
        smoke = self.result["smoke"]
        self.assertTrue(smoke["direct_cli_application_match"])
        self.assertEqual(
            {"root-help", "completion-bash", "completion-fish", "completion-zsh"},
            set(smoke["presentations"]),
        )

    def test_build_capability_is_inspected_but_execution_is_not_run(self):
        smoke = self.result["smoke"]
        self.assertTrue(
            {
                "exact-handler",
                "execute-intent",
                "fresh-output-root",
            }.issubset(smoke["build_capability"]["explicit_gates"]),
        )
        self.assertEqual("build-output-write", smoke["build_capability"]["effect_class"])
        self.assertEqual("not-run", smoke["backend_execution"])
        self.assertEqual("not-run", smoke["project_write"])
        self.assertEqual("not-run", smoke["hardware_access"])
        self.assertTrue(smoke["filesystem_unchanged"])

    def test_smoke_fixture_rejects_a_mutating_route(self):
        fixture = core.load_json(FIXTURE)
        invalid = copy.deepcopy(fixture)
        invalid["cases"][0]["arguments"] = [
            "build",
            "execute",
            "schuss-build-request-000002@5",
            "--json",
        ]
        with mock.patch.object(validate_task023.core, "load_json", return_value=invalid):
            with self.assertRaisesRegex(
                validate_task023.Task023ValidationError, "mutating route"
            ):
                validate_task023._validated_fixture(ROOT)

    def test_validator_result_is_canonical_and_path_free(self):
        serialized = validate_task023._canonical_bytes(self.result)
        self.assertEqual(self.result, json.loads(serialized))
        for forbidden in (
            str(ROOT).encode("utf-8"),
            b"/Users/",
            b"/private/",
            b"/tmp/",
            b"task023-user-a",
            b"task023-user-b",
            b"task023-host-a",
            b"task023-host-b",
        ):
            self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
