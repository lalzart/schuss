from __future__ import annotations

import sys
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/contracts")]

from packages.schuss_core.control_plane import dispatch_operation, load_repository_context  # noqa: E402
from packages.schuss_core import catalog_projection  # noqa: E402

import generate_task017_records as generator  # noqa: E402
import validator_core as core  # noqa: E402


RECORD_SET = ROOT / "contracts/record-sets/task017-curated-core-v1.json"
EVIDENCE = ROOT / "evidence/task017-completion-v1"


class Task017CuratedCoreTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = load_repository_context(record_set_path=RECORD_SET)
        cls.packet = core.load_json(ROOT / "contracts/task017/selection-packet.json")
        cls.graphs = {
            item["graph_id"]: item for item in cls.context.records["graphs"]
            if item["graph_id"] in {"schuss-graph-000003", "schuss-graph-000004", "schuss-graph-000005"}
        }

    def _plan(self, number: int) -> dict:
        request = next(
            item for item in self.context.records["request"]
            if item["build_request_id"] == f"schuss-build-request-{number:06d}"
            and item["revision"] == 1
        )
        reference = {key: request[key] for key in ("build_request_id", "revision", "content_hash")}
        return dispatch_operation(
            {
                "schema_version": "schuss-operation-request-v4",
                "canonical_profile": "schuss-canonical-json-v1",
                "operation": "build.plan",
                "payload": {"build_request_reference": reference},
            },
            self.context,
        )

    def test_exact_successor_and_structural_levels(self) -> None:
        self.assertEqual("valid", self.context.task007_summary["status"])
        self.assertEqual("schuss-record-set-000011", self.context.record_set_reference["record_set_id"])
        self.assertEqual(
            ["passed", "passed"] + ["not-run"] * 6,
            [item["status"] for item in self.context.task007_summary["evidence_levels"]],
        )

    def test_selection_is_bounded_balanced_and_not_frequency_only(self) -> None:
        self.assertEqual(12, len(self.packet["included_families"]))
        categories = Counter(item["primary_category"] for item in self.packet["included_families"])
        for category in ("timing-sequencing", "sound-sources", "modulation-control", "shaping-dynamics", "delay-reverb"):
            self.assertGreater(categories[category], 0)
        selected_counts = {item["complete_graph_reference_count"] for item in self.packet["included_families"]}
        excluded_counts = {item["complete_graph_reference_count"] for item in self.packet["excluded_candidates"]}
        self.assertLess(min(selected_counts), max(excluded_counts))
        self.assertEqual("prioritization-only", self.packet["inventory_audit"]["frequency_policy"])

    def test_every_family_has_exact_contract_binding_eligibility_and_evidence(self) -> None:
        contract_ids = {item["component_contract_id"] for item in self.context.records["contracts"]}
        binding_refs = {(item["implementation_id"], item["revision"]) for item in self.context.records["bindings"]}
        evidence_refs = {(item["evidence_claim_id"], item["revision"], item["content_hash"]) for item in self.context.records["evidence"]}
        for offset, selected in enumerate(self.packet["included_families"]):
            implementation_id = selected["implementation_reference"]["stable_id"]
            self.assertIn(f"schuss-component-contract-{10 + offset:06d}", contract_ids)
            self.assertIn((implementation_id, 1), binding_refs)
            self.assertIn((implementation_id, 2), binding_refs)
            eligibility = next(
                item for item in self.context.records["eligibility"]
                if item["binding_reference"]["implementation_id"] == implementation_id
                and item["binding_reference"]["revision"] == 2
                and item["allowed_pair"]["backend_reference"]["revision"] == 2
            )
            self.assertEqual(1, len(eligibility["compatibility_evidence"]))
            claim = eligibility["compatibility_evidence"][0]
            self.assertIn((claim["evidence_claim_id"], claim["revision"], claim["content_hash"]), evidence_refs)
            self.assertTrue(selected["unresolved_facts"])

    def test_direct_support_is_exact_or_fail_closed(self) -> None:
        task017_eligibilities = [
            item for item in self.context.records["eligibility"]
            if 15 <= int(item["binding_eligibility_id"].rsplit("-", 1)[1]) <= 26
        ]
        statuses = Counter(item["allowed_pair"]["state"]["status"] for item in task017_eligibilities)
        self.assertEqual({"not-evaluated": 11, "supported": 1}, dict(statuses))
        supported = next(item for item in task017_eligibilities if item["allowed_pair"]["state"]["status"] == "supported")
        self.assertEqual("transparent-compound", supported["realization_form"])

    def test_two_headless_instruments_exercise_graph_breadth(self) -> None:
        instruments = [
            item for item in self.context.records["instruments"]
            if item["instrument_id"] in {"schuss-instrument-000003", "schuss-instrument-000004"}
        ]
        self.assertEqual(2, len(instruments))
        self.assertTrue(all(not item["actions"] and not item["displays"] for item in instruments))
        self.assertTrue(all(item["graph_mappings"] for item in instruments))
        self.assertTrue(self.graphs["schuss-graph-000005"]["compound_interface_mappings"])
        fanout = Counter(
            (connection["source"]["node_id"], connection["source"]["facet_id"])
            for graph in self.graphs.values()
            for connection in graph["connections"]
        )
        self.assertGreaterEqual(max(fanout.values()), 2)

    def test_plans_are_stably_unsupported_without_fallback(self) -> None:
        first_percussion, second_percussion = self._plan(3), self._plan(3)
        self.assertEqual(core.canonical_json(first_percussion), core.canonical_json(second_percussion))
        self.assertEqual("invalid", first_percussion["status"])
        self.assertEqual({"COMPILER_COMPOUND_INTERNAL_BINDING_UNRESOLVED"}, {item["code"] for item in first_percussion["diagnostics"]})
        first_effects, second_effects = self._plan(4), self._plan(4)
        self.assertEqual(core.canonical_json(first_effects), core.canonical_json(second_effects))
        self.assertEqual("unsupported", first_effects["status"])
        self.assertEqual({"COMPILER_BINDING_UNSUPPORTED"}, {item["code"] for item in first_effects["diagnostics"]})

    def test_exact_catalog_revision_and_projection_are_selected(self) -> None:
        self.assertEqual("catalog-corpus-v2", self.context.records["catalog"][0]["schema_version"])
        self.assertEqual(2, self.context.records["catalog"][0]["revision"])
        self.assertEqual("catalog-projection-v2", self.context.catalog_projection["schema_version"])
        self.assertEqual(40, len(self.context.catalog_projection["families"]))

    def test_catalog_source_authority_is_exactly_one(self) -> None:
        with self.assertRaisesRegex(
            catalog_projection.CatalogProjectionError,
            "exactly one source authority",
        ):
            catalog_projection._authority_values(
                {"source_observation": {}, "source_authority": {}}, {}, core
            )

    def test_parent_members_and_prior_results_are_preserved(self) -> None:
        parent = core.load_json(ROOT / "contracts/record-sets/task016-complete-gills-direct-v1.json")
        successor = core.load_json(RECORD_SET)
        self.assertTrue(all(item in successor["schema_members"] for item in parent["schema_members"]))
        self.assertTrue(all(item in successor["record_members"] for item in parent["record_members"]))
        preservation = core.load_json(EVIDENCE / "preservation.json")
        self.assertEqual("passed", preservation["status"])
        for item in preservation["files"]:
            self.assertEqual(item["byte_sha256"], core.sha256_file(ROOT / item["portable_path"]))

    def test_generated_records_and_cli_evidence_are_byte_deterministic(self) -> None:
        files, manifest = generator.generated()
        files[RECORD_SET.relative_to(ROOT).as_posix()] = manifest
        self.assertTrue(all((ROOT / relative).read_bytes() == payload for relative, payload in files.items()))
        summary = core.load_json(EVIDENCE / "validation-summary.json")
        self.assertTrue(summary["cli_outputs_identical"])
        self.assertFalse(summary["direct_execution_performed"])
        self.assertEqual(["passed", "passed"] + ["not-run"] * 6, [item["status"] for item in summary["evidence_levels"]])


if __name__ == "__main__":
    unittest.main()
