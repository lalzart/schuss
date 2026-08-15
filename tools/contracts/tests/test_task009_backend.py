import copy
import hashlib
import sys
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
import run_task009
import task009_backend as backend
import task009_prerequisite_rules as prerequisite
import validator_core as core


class Task009BackendTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.selected = record_set_rules.load_record_set(
            ROOT, run_task009.SUCCESSOR_MANIFEST
        )
        cls.context = load_repository_context(
            ROOT, record_set_path=run_task009.SUCCESSOR_MANIFEST
        )
        cls.request = next(
            item
            for item in cls.selected.records["request"]
            if item["revision"] == 2
        )
        cls.binding = next(
            item
            for item in cls.selected.records["implementation-binding"]
            if item["implementation_id"] == backend.BINDING_ID
            and item["revision"] == 2
        )
        cls.eligibility = next(
            item
            for item in cls.selected.records["eligibility"]
            if item["revision"] == 2
        )
        cls.result = cls.selected.records["result"][0]
        cls.artifacts = {
            item["artifact_kind"]: item
            for item in cls.selected.records["artifact"]
            if 8 <= int(item["artifact_id"].rsplit("-", 1)[1]) <= 14
        }

    def test_retained_validation_summary_is_clean_and_deterministic(self):
        first = run_task009.validate()
        second = run_task009.validate()
        self.assertEqual(first, second)
        self.assertEqual("valid", first["status"])
        self.assertEqual([], first["diagnostics"])
        self.assertEqual([1, 2, 3, 4, 5], first["evidence_levels_passed"])
        self.assertEqual([6, 7, 8], first["evidence_levels_not_run"])

    def test_revision_one_resolution_remains_exactly_unresolved(self):
        default = load_repository_context(ROOT)
        fixture = core.load_json(
            ROOT / "tools/contracts/tests/fixtures/task008-operation-requests.json"
        )["build_resolve"]
        value = dispatch_operation(fixture, default)
        self.assertEqual("unresolved", value["status"])
        self.assertIsNone(value["value"]["backend_invocation"])
        candidate = value["value"]["resolution_traces"][0]["candidates"][0]
        self.assertEqual(
            [
                "BINDING_TARGET_BACKEND_PAIR_NOT_EVALUATED",
                "CAPABILITY_UNRESOLVED:audio-stream-fixed-q27",
                "CAPABILITY_UNRESOLVED:control-stream-fixed-q27",
                "COMPATIBILITY_EVIDENCE_MISSING",
            ],
            sorted(candidate["exclusion_reasons"] + candidate["unresolved_reasons"]),
        )

    def test_authorized_probe_is_non_production_and_valid(self):
        probe = next(
            item
            for item in self.selected.records["conformance-probe-input"]
            if item["conformance_probe_id"] == "schuss-conformance-probe-000002"
        )
        result = next(
            item
            for item in self.selected.records["conformance-probe-result"]
            if item["conformance_probe_result_id"]
            == "schuss-conformance-probe-result-000002"
        )
        evidence = next(
            item
            for item in self.selected.records["conformance-probe-evidence"]
            if item["conformance_probe_evidence_id"]
            == "schuss-conformance-probe-evidence-000002"
        )
        registry = run_task009._probe_validation_registry(self.selected, [])
        self.assertEqual("task-009-authorized", probe["execution_authorization"])
        self.assertFalse(probe["production_selection_authority"])
        self.assertFalse(result["production_selection_authority"])
        self.assertEqual("success", result["overall_status"])
        self.assertEqual("passed", evidence["outcome"])
        self.assertEqual(
            (),
            prerequisite.validate_probe_values(
                probe,
                result,
                evidence,
                self.selected.records["conformance-probe-procedure"][0],
                self.selected.records["prerequisite-environment"][0],
                registry,
            ),
        )

    def test_strictly_earlier_promotion_chain_is_exact(self):
        claim_ref = self.eligibility["compatibility_evidence"][0]
        claim = next(
            item
            for item in self.selected.records["evidence"]
            if core.reference_key(claim_ref, "evidence_claim_id")
            == core.exact_key(item, "evidence_claim_id")
        )
        revisions = [
            item["revision"]
            for item in claim["evidence_inputs"]
            if item["stable_id"] == backend.BINDING_ID
        ]
        self.assertEqual([1], revisions)
        self.assertEqual(2, self.eligibility["binding_reference"]["revision"])

    def test_ordinary_resolution_selects_one_clean_promoted_binding(self):
        operation = {
            "schema_version": "schuss-operation-request-v1",
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": "build.resolve",
            "payload": {
                "build_request_reference": run_task009._reference(
                    self.request, "build_request_id"
                )
            },
        }
        value = dispatch_operation(operation, self.context)
        self.assertEqual("success", value["status"])
        trace = value["value"]["resolution_traces"][0]
        selected = [
            item
            for item in trace["candidates"]
            if item["binding_reference"]
            == run_task009._reference(self.binding, "implementation_id")
        ]
        self.assertEqual(1, len(selected))
        self.assertEqual([], selected[0]["exclusion_reasons"])
        self.assertEqual([], selected[0]["unresolved_reasons"])
        self.assertIsNotNone(value["value"]["backend_invocation"])

    def test_handler_accepts_exact_seam_and_rejects_stale_request(self):
        invocation = core.load_json(
            ROOT / "evidence/task-009-v1/backend-invocation-input.json"
        )
        schema = core.load_json(ROOT / "schemas/backend-invocation-input-v1.schema.json")
        request_schema = core.load_json(ROOT / "schemas/build-request-v0.schema.json")
        binding_ref = run_task009._reference(self.binding, "implementation_id")
        backend.validate_invocation_input(
            invocation, schema, request_schema, binding_ref, self.request
        )
        stale = copy.deepcopy(invocation)
        stale["accepted_build_request"]["content_hash"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(backend.Task009BackendError, "exact Task 009 closure mismatch"):
            backend.validate_invocation_input(
                stale, schema, request_schema, binding_ref, self.request
            )

    def test_deterministic_axp_is_boundary_only(self):
        axp = backend.axp_bytes()
        descriptor = self.artifacts["legacy-boundary-patch"]
        self.assertEqual(descriptor["byte_sha256"], hashlib.sha256(axp).hexdigest())
        self.assertEqual(5, axp.count(b"<obj "))
        self.assertEqual(4, axp.count(b"<net>"))
        self.assertIn(b'name="schuss_blend"', axp)
        graph = (ROOT / "contracts/graphs/blend-crossfader-v0.json").read_bytes()
        self.assertNotIn(b".axp", graph)
        self.assertNotIn(b"ksoloti", graph.lower())

    def test_source_map_covers_node_facets_and_generated_regions(self):
        descriptor = self.artifacts["source-map"]
        path = run_task009.ARTIFACT_STORE / descriptor["byte_sha256"]
        value = core.load_json_bytes(
            path.read_bytes(), str(path), require_final_lf=False
        )
        self.assertEqual("graph-node-000001", value["node_id"])
        self.assertEqual(4, len(value["contract_facets"]))
        self.assertEqual(5, len(value["axp_locations"]))
        self.assertEqual(5, len(value["generated_regions"]))
        self.assertEqual([], value["diagnostic_ids"])

    def test_all_retained_artifact_bytes_and_fresh_roots_match(self):
        for artifact in self.selected.records["artifact"]:
            path = run_task009.ARTIFACT_STORE / artifact["byte_sha256"]
            self.assertEqual(artifact["byte_length"], path.stat().st_size)
            self.assertEqual(artifact["byte_sha256"], core.sha256_file(path))
        for name in ("probe", "production"):
            equality = core.load_json(
                ROOT / f"evidence/task-009-v1/{name}-fresh-root-equality.json"
            )
            self.assertEqual("passed", equality["status"])
            self.assertTrue(equality["command_vectors_equal"])
            self.assertTrue(equality["bridge_results_equal"])
            self.assertTrue(equality["resource_facts_equal"])

    def test_failure_injection_stops_every_later_stage(self):
        report = core.load_json(
            ROOT / "evidence/task-009-v1/failure-injection.json"
        )
        self.assertEqual("passed", report["status"])
        for value in report["outcomes"]:
            statuses = dict(value["stage_statuses"])
            self.assertEqual("failed", statuses[value["stage"]])
            terminal = False
            for stage in backend.PROBE_STAGES:
                if stage == value["stage"]:
                    terminal = True
                elif terminal:
                    self.assertEqual("not-run", statuses[stage])

    def test_build_result_honors_stop_and_exact_output_closure(self):
        self.assertEqual("success", self.result["overall_status"])
        self.assertTrue(
            all(item["status"] == "success" for item in self.result["stage_outcomes"][:9])
        )
        self.assertEqual("not-run", self.result["stage_outcomes"][9]["status"])
        self.assertEqual(14 - 7, len(self.result["artifact_references"]))
        self.assertEqual(13, len(self.result["input_closure"]))
        self.assertEqual(
            run_task009._closure_hash(self.result["input_closure"]),
            self.result["input_closure_hash"],
        )

    def test_static_resources_are_not_real_time_evidence(self):
        report = self.selected.records["resource"][0]
        self.assertEqual(
            {"compiler-link-map-observation"},
            {item["observation_kind"] for item in report["observations"]},
        )
        self.assertEqual(
            {5}, {item["evidence_level"] for item in report["observations"]}
        )
        self.assertTrue(
            all(item["outcome"] == "within-budget" for item in report["budget_comparisons"])
        )
        self.assertNotIn(
            7, {item["level"] for item in self.selected.records["evidence"]}
        )

    def test_no_device_real_time_or_audible_claim_exists(self):
        levels = {item["level"] for item in self.selected.records["evidence"]}
        self.assertEqual({1, 2, 3, 4, 5}, levels)
        status = core.load_json(
            ROOT / "evidence/task-009-v1/evidence-level-status.json"
        )
        self.assertEqual(
            ["not-run", "not-run", "not-run"],
            [item["status"] for item in status["levels"][5:]],
        )

    def test_durable_json_evidence_has_no_machine_local_path(self):
        for path in sorted((ROOT / "evidence/task-009-v1").glob("*.json")):
            payload = path.read_bytes()
            self.assertNotIn(b"/Users/", payload, path.name)
            self.assertNotIn(b"/private/", payload, path.name)
            self.assertNotIn(b"/tmp/", payload, path.name)


if __name__ == "__main__":
    unittest.main()
