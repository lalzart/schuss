import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools/contracts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from packages.schuss_core import dispatch_operation, load_repository_context

import record_set_rules
import task009_prerequisite_rules as prerequisite
import validator_core as core
from tools.validation.profile import requires_profile


class Task009PrerequisiteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.accepted = record_set_rules.load_record_set(
            ROOT, record_set_rules.ACCEPTED_RECORD_SET
        )
        cls.prospective = record_set_rules.load_record_set(
            ROOT, prerequisite.PROSPECTIVE_RECORD_SET
        )
        cls.context = load_repository_context(ROOT)

    def one(self, kind):
        values = self.prospective.records[kind]
        self.assertEqual(1, len(values))
        return copy.deepcopy(values[0])

    def probe_values(self):
        return (
            self.one("conformance-probe-input"),
            self.one("conformance-probe-result"),
            self.one("conformance-probe-evidence"),
            self.one("conformance-probe-procedure"),
            self.one("prerequisite-environment"),
            prerequisite._record_registry(self.prospective),
        )

    def test_complete_prerequisite_summary_is_valid_and_deterministic(self):
        first = prerequisite.validate_task009_prerequisite(ROOT)
        second = prerequisite.validate_task009_prerequisite(ROOT)
        self.assertEqual("valid", first["status"])
        self.assertEqual([], first["diagnostics"])
        self.assertEqual(core.canonical_json(first), core.canonical_json(second))
        self.assertEqual("not-run", first["probe"]["overall_status"])
        self.assertTrue(
            all(item["status"] == "not-run" for item in first["environment"]["task009_evidence_levels"])
        )

    def test_default_and_prospective_views_are_explicit(self):
        self.assertEqual(self.accepted.reference, self.context.record_set_reference)
        prospective_context = load_repository_context(
            ROOT,
            record_set_path=ROOT / prerequisite.PROSPECTIVE_RECORD_SET,
        )
        self.assertEqual(self.prospective.reference, prospective_context.record_set_reference)
        self.assertNotEqual(self.context.record_set_reference, prospective_context.record_set_reference)

    @requires_profile("configured-sources")
    def test_accepted_view_preserves_operation_result_hashes(self):
        expected = {
            "records_validate": (4324, "cb0735df54a0baade54c8cc16807a94771c1e7cbbc93a6710291084fcb656543"),
            "graph_inspect": (7318, "88d5a4f52f4d3bfc31ff361ebe3a8835860e7b5890e9c9791be21cd86c179ee1"),
            "build_resolve": (1367, "643a063d1553ff000a4776fd2a4eb5b7d300c0ba34ccbb977f3babd78abf7de9"),
            "graph_transact_noop": (3964, "6def7986739604e807b3b95e26513fe6a9a41cd1d827ea4e417809b9027c48b8"),
        }
        fixtures = core.load_json(
            ROOT / "tools/contracts/tests/fixtures/task008-operation-requests.json"
        )
        from packages.schuss_core import canonical_result_bytes

        for name, (length, digest) in expected.items():
            value = canonical_result_bytes(
                dispatch_operation(copy.deepcopy(fixtures[name]), self.context),
                self.context,
            )
            self.assertEqual(length, len(value), name)
            self.assertEqual(digest, hashlib.sha256(value).hexdigest(), name)

    def test_probe_values_are_isolated_from_production_build_contracts(self):
        probe, result, _, _, _, _ = self.probe_values()
        request_schema = self.prospective.schemas["build-request-v0"]
        result_schema = self.prospective.schemas["build-result-v0"]
        self.assertTrue(core.schema_errors(probe, request_schema, request_schema))
        self.assertTrue(core.schema_errors(result, result_schema, result_schema))
        dispatched = dispatch_operation(probe, self.context)
        self.assertEqual("invalid", dispatched["status"])
        self.assertEqual("invalid-request", dispatched["operation"])
        self.assertIsNone(dispatched["value"])

    def test_probe_fixture_is_not_authorized_and_grants_no_selection(self):
        probe, result, evidence, procedure, environment, registry = self.probe_values()
        self.assertEqual("not-authorized", probe["execution_authorization"])
        self.assertFalse(probe["production_selection_authority"])
        self.assertFalse(result["production_selection_authority"])
        self.assertFalse(procedure["production_selection_authority"])
        self.assertEqual("not-run", evidence["outcome"])
        self.assertEqual(
            (),
            prerequisite.validate_probe_values(
                probe, result, evidence, procedure, environment, registry
            ),
        )

    def test_probe_stage_failures_fail_closed(self):
        probe, result, evidence, procedure, environment, registry = self.probe_values()
        result["stage_outcomes"][0]["status"] = "failed"
        result["stage_outcomes"][1]["status"] = "success"
        result["overall_status"] = "failed"
        evidence["outcome"] = "failed"
        diagnostics = prerequisite.validate_probe_values(
            probe, result, evidence, procedure, environment, registry
        )
        self.assertIn("PROBE_RESULT_AFTER_TERMINAL", {item.code for item in diagnostics})

    def test_successful_probe_maps_to_passed_evidence(self):
        probe, result, evidence, procedure, environment, registry = self.probe_values()
        for outcome in result["stage_outcomes"]:
            outcome["status"] = "success"
        result["overall_status"] = "success"
        evidence["outcome"] = "passed"
        self.assertEqual(
            (),
            prerequisite.validate_probe_values(
                probe, result, evidence, procedure, environment, registry
            ),
        )

    def test_not_run_stage_cannot_claim_outputs(self):
        probe, result, evidence, procedure, environment, registry = self.probe_values()
        result["stage_outcomes"][0]["diagnostic_ids"] = ["diagnostic-000001"]
        diagnostics = prerequisite.validate_probe_values(
            probe, result, evidence, procedure, environment, registry
        )
        codes = {item.code for item in diagnostics}
        self.assertIn("PROBE_NOT_RUN_OUTPUT_INVALID", codes)
        self.assertIn("PROBE_DIAGNOSTIC_REFERENCE_INVALID", codes)

    def test_probe_evidence_direction_is_acyclic(self):
        probe, result, evidence, procedure, environment, registry = self.probe_values()
        result["evidence_reference"] = {
            "conformance_probe_evidence_id": evidence["conformance_probe_evidence_id"],
            "revision": evidence["revision"],
            "content_hash": evidence["content_hash"],
        }
        diagnostics = prerequisite.validate_probe_values(
            probe, result, evidence, procedure, environment, registry
        )
        self.assertIn("PROBE_EVIDENCE_CYCLE", {item.code for item in diagnostics})
        result_schema = self.prospective.schemas["conformance-probe-result-v0"]
        self.assertTrue(core.schema_errors(result, result_schema, result_schema))

    def test_strictly_earlier_reference_fixture(self):
        self.assertEqual((), prerequisite.validate_strictly_earlier_fixture(ROOT))
        fixture = core.load_json(ROOT / prerequisite.STRICTLY_EARLIER_FIXTURE)
        self.assertEqual(
            fixture["later_eligibility_binding_reference"]["implementation_id"],
            fixture["evidence_closure_binding_reference"]["implementation_id"],
        )
        self.assertLess(
            fixture["evidence_closure_binding_reference"]["revision"],
            fixture["later_eligibility_binding_reference"]["revision"],
        )
        self.assertFalse(fixture["production_record"])

    def test_environment_evidence_is_exact_and_portable(self):
        environment = self.one("prerequisite-environment")
        self.assertEqual((), prerequisite.validate_environment_artifacts(ROOT, environment))
        for path in sorted((ROOT / prerequisite.EVIDENCE_ROOT).glob("*")):
            if path.is_file():
                value = path.read_text(encoding="utf-8", errors="replace")
                self.assertNotIn("/Users/", value)
                self.assertNotIn("/private/", value)
                self.assertNotIn("/tmp/", value)

    def _copy_record_set_inputs(self, root):
        shutil.copytree(ROOT / "schemas", root / "schemas")
        shutil.copytree(ROOT / "contracts", root / "contracts")

    def test_record_sets_fail_closed_on_missing_extra_and_hash_mismatch(self):
        cases = ("missing", "extra", "hash-mismatch")
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                self._copy_record_set_inputs(root)
                if case == "missing":
                    (root / "contracts/build-requests/blend-validation-v0.json").unlink()
                elif case == "extra":
                    (root / "contracts/build-requests/unlisted.json").write_text("{}\n", encoding="utf-8")
                else:
                    path = root / "contracts/build-requests/blend-validation-v0.json"
                    path.write_bytes(path.read_bytes() + b"\n")
                with self.assertRaises(record_set_rules.RecordSetError):
                    record_set_rules.load_record_set(root, record_set_rules.ACCEPTED_RECORD_SET)

    def test_record_sets_fail_closed_on_duplicate_member(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._copy_record_set_inputs(root)
            path = root / record_set_rules.ACCEPTED_RECORD_SET
            manifest = core.load_json(path)
            manifest["record_members"].append(copy.deepcopy(manifest["record_members"][0]))
            schema = core.load_json(root / record_set_rules.RECORD_SET_SCHEMA)
            manifest["content_hash"] = core.record_content_hash(manifest, schema)
            path.write_text(core.canonical_json(manifest) + "\n", encoding="utf-8")
            with self.assertRaises(record_set_rules.RecordSetError):
                record_set_rules.load_record_set(root, record_set_rules.ACCEPTED_RECORD_SET)

    def test_prerequisite_validator_cli_is_read_only_and_stable(self):
        command = [sys.executable, str(TOOLS / "validate_task009_prerequisite.py")]
        first = subprocess.run(command, cwd=ROOT, check=False, capture_output=True)
        second = subprocess.run(command, cwd=ROOT, check=False, capture_output=True)
        self.assertEqual(0, first.returncode)
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(b"", first.stderr)
        self.assertEqual("valid", json.loads(first.stdout)["status"])

    def test_no_production_revision_is_promoted_by_the_prerequisite(self):
        accepted_members = {
            item["portable_path"] for item in self.accepted.manifest["record_members"]
        }
        additions = {
            item["portable_path"]
            for item in self.prospective.manifest["record_members"]
            if item["portable_path"] not in accepted_members
        }
        self.assertEqual(
            {
                "contracts/prerequisite/task009/environment-v0.json",
                "contracts/prerequisite/task009/probe-evidence-v0.json",
                "contracts/prerequisite/task009/probe-input-v0.json",
                "contracts/prerequisite/task009/probe-result-v0.json",
                "contracts/prerequisite/task009/procedure-v0.json",
            },
            additions,
        )


if __name__ == "__main__":
    unittest.main()
