import copy
import hashlib
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools/contracts"
for path in (ROOT, TOOLS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from packages.schuss_core import dispatch_operation, load_repository_context

import record_set_rules
import run_task009
import run_task011c
import task009_backend
import task011c_backend as backend
import validator_core as core


class Task011CBackendTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.selected = record_set_rules.load_record_set(
            ROOT, run_task011c.SUCCESSOR_MANIFEST
        )
        cls.context = load_repository_context(
            ROOT, record_set_path=run_task011c.SUCCESSOR_MANIFEST
        )
        cls.request = next(
            record for record in cls.selected.records["request"]
            if record["build_request_id"] == "schuss-build-request-000002"
            and record["revision"] == 2
        )
        cls.production_artifacts = {
            record["artifact_kind"]: record
            for record in cls.selected.records["artifact"]
            if 22 <= int(record["artifact_id"].rsplit("-", 1)[1]) <= 28
        }

    def test_retained_validation_is_clean_and_deterministic(self):
        first = run_task011c.validate()
        second = run_task011c.validate()
        self.assertEqual(first, second)
        self.assertEqual("valid", first["status"])
        self.assertEqual([], first["diagnostics"])
        self.assertEqual(8, first["selected_node_count"])
        self.assertEqual([1, 2, 3, 4, 5], first["evidence_levels_passed"])
        self.assertEqual([6, 7, 8], first["evidence_levels_not_run"])

    def test_six_authorized_probes_are_non_production_successes(self):
        for name in run_task011c.ROLE_NAMES:
            probe = next(
                record for record in self.selected.records["conformance-probe-input"]
                if record["conformance_probe_id"] == run_task011c.PROBE_IDS[name]
                and record["revision"] == 2
            )
            result = next(
                record for record in self.selected.records["conformance-probe-result"]
                if record["conformance_probe_result_id"]
                == run_task011c.RESULT_IDS[name]
            )
            evidence = next(
                record for record in self.selected.records["conformance-probe-evidence"]
                if record["conformance_probe_evidence_id"]
                == run_task011c.PROBE_EVIDENCE_IDS[name]
            )
            self.assertEqual("conformance-probe-input-v1", probe["schema_version"])
            self.assertEqual("task-011c-authorized", probe["execution_authorization"])
            self.assertFalse(probe["production_selection_authority"])
            self.assertFalse(result["production_selection_authority"])
            self.assertEqual("success", result["overall_status"])
            self.assertEqual("passed", evidence["outcome"])
            self.assertEqual(5, evidence["evidence_level"])

    def test_each_promotion_uses_strictly_earlier_binding_revision(self):
        for name in run_task011c.ROLE_NAMES:
            claim = next(
                record for record in self.selected.records["evidence"]
                if record["evidence_claim_id"]
                == run_task011c.PROMOTION_CLAIM_IDS[name]
            )
            earlier = next(
                item for item in claim["evidence_inputs"]
                if item["stable_id"].startswith("schuss-implementation-")
            )
            promoted = next(
                record for record in self.selected.records["implementation-binding"]
                if record["implementation_id"]
                == earlier["stable_id"]
                and record["revision"] == 2
            )
            self.assertEqual(1, earlier["revision"])
            self.assertEqual(2, promoted["revision"])

    def test_ordinary_resolver_selects_exact_eight_node_binding_set(self):
        operation = {
            "schema_version": "schuss-operation-request-v1",
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": "build.resolve",
            "payload": {
                "build_request_reference": run_task011c._reference(
                    self.request, "build_request_id"
                )
            },
        }
        result = dispatch_operation(operation, self.context)
        self.assertEqual("success", result["status"])
        invocation = result["value"]["backend_invocation"]
        self.assertEqual(8, len(invocation["selected_bindings"]))
        sine = [
            value["binding_reference"]
            for value in invocation["selected_bindings"]
            if value["node_id"] in ("graph-node-000004", "graph-node-000005")
        ]
        self.assertEqual(2, len(sine))
        self.assertEqual(sine[0], sine[1])

    def test_handler_accepts_exact_invocation_and_rejects_stale(self):
        invocation = core.load_json(
            ROOT / "evidence/task-011c-v1/backend-invocation-input.json"
        )
        binding_refs = {
            value["binding_reference"]["implementation_id"]:
                value["binding_reference"]
            for value in invocation["selected_bindings"]
        }
        schema = core.load_json(
            ROOT / "schemas/backend-invocation-input-v1.schema.json"
        )
        request_schema = core.load_json(ROOT / "schemas/build-request-v0.schema.json")
        backend.validate_invocation_input(
            invocation, schema, request_schema, binding_refs, self.request
        )
        stale = copy.deepcopy(invocation)
        stale["accepted_build_request"]["content_hash"] = "sha256:" + "0" * 64
        with self.assertRaises(task009_backend.Task009BackendError):
            backend.validate_invocation_input(
                stale, schema, request_schema, binding_refs, self.request
            )

    def test_boundary_axp_has_exact_objects_and_logical_connections(self):
        value = backend.axp_bytes()
        descriptor = self.production_artifacts["legacy-boundary-patch"]
        self.assertEqual(descriptor["byte_sha256"], hashlib.sha256(value).hexdigest())
        self.assertEqual(9, value.count(b"<obj "))
        self.assertEqual(8, value.count(b"<net>"))
        self.assertEqual(10, value.count(b"<dest "))
        self.assertEqual(2, value.count(b'type="osc/sine"'))
        self.assertIn(b'name="schuss_blend"', value)

    def test_source_map_covers_all_nodes_connections_and_generated_regions(self):
        descriptor = self.production_artifacts["source-map"]
        path = run_task011c.ARTIFACT_STORE / descriptor["byte_sha256"]
        value = core.load_json_bytes(
            path.read_bytes(), str(path), require_final_lf=False
        )
        self.assertEqual(8, len(value["nodes"]))
        self.assertEqual(9, len(value["connections"]))
        self.assertEqual(9, len(value["generated_regions"]))
        self.assertEqual(
            10,
            sum(len(node["parameter_values"]) for node in value["nodes"]),
        )
        self.assertEqual([], value["diagnostic_ids"])

    def test_retained_artifacts_and_fresh_roots_are_exact(self):
        for artifact in self.selected.records["artifact"]:
            number = int(artifact["artifact_id"].rsplit("-", 1)[1])
            if number < 15:
                continue
            path = run_task011c.ARTIFACT_STORE / artifact["byte_sha256"]
            self.assertEqual(artifact["byte_length"], path.stat().st_size)
            self.assertEqual(artifact["byte_sha256"], core.sha256_file(path))
        production = core.load_json(
            ROOT / "evidence/task-011c-v1/production-fresh-root-equality.json"
        )
        self.assertEqual("passed", production["status"])
        self.assertTrue(production["command_vectors_equal"])
        self.assertTrue(production["bridge_results_equal"])
        self.assertTrue(production["resource_facts_equal"])

    def test_failure_injection_stops_later_stages(self):
        report = core.load_json(
            ROOT / "evidence/task-011c-v1/failure-injection.json"
        )
        self.assertEqual("passed", report["status"])
        for outcome in report["outcomes"]:
            statuses = dict(outcome["stage_statuses"])
            self.assertEqual("failed", statuses[outcome["stage"]])
            later = False
            for stage in backend.PROBE_STAGES:
                if stage == outcome["stage"]:
                    later = True
                elif later:
                    self.assertEqual("not-run", statuses[stage])

    def test_levels_six_through_eight_and_device_actions_are_not_run(self):
        levels = core.load_json(
            ROOT / "evidence/task-011c-v1/evidence-level-status.json"
        )
        self.assertEqual(
            ["not-run", "not-run", "not-run"],
            [item["status"] for item in levels["levels"] if item["level"] >= 6],
        )
        execution = core.load_json(
            ROOT / "evidence/task-011c-v1/production-execution.json"
        )
        self.assertEqual("unreachable", execution["bridge_result"]["device_actions"])

    def test_successor_preserves_exact_parent_and_task009(self):
        parent = record_set_rules.load_record_set(ROOT, run_task011c.PARENT_MANIFEST)
        self.assertEqual(
            {"status": "included", **parent.reference},
            self.selected.manifest["parent_reference"],
        )
        self.assertEqual("valid", run_task009.validate()["status"])


if __name__ == "__main__":
    unittest.main()
