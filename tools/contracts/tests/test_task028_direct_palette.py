from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/contracts")]

from packages.schuss_core.control_plane import load_repository_context  # noqa: E402
from packages.schuss_core.palette_direct_frontend import lower_palette  # noqa: E402

import generate_task028_records as generator  # noqa: E402
import validator_core as core  # noqa: E402


RECORD_SET = ROOT / "contracts/record-sets/task028-direct-palette-v1.json"
PARENT_SET = ROOT / "contracts/record-sets/task027-mutable-catalog-v1.json"


def exact(values, field: str, identifier: str, revision: int = 1):
    matches = [item for item in values if item[field] == identifier and item["revision"] == revision]
    if len(matches) != 1:
        raise AssertionError(f"{identifier}@{revision} did not resolve exactly")
    return matches[0]


class Task028DirectPaletteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = load_repository_context(record_set_path=RECORD_SET)
        cls.parent = load_repository_context(record_set_path=PARENT_SET)
        cls.packet = exact(cls.context.records["selection_packets"], "selection_packet_id", "schuss-core-selection-000003")
        cls.proof = exact(cls.context.records["palette_lowering_proofs"], "palette_lowering_proof_id", "schuss-palette-lowering-proof-000001")
        cls.target = exact(cls.context.records["target"], "compute_target_id", "schuss-compute-target-000001", 2)
        cls.backend = exact(cls.context.records["backend"], "backend_id", "schuss-backend-000002", 4)
        vocabulary = exact(cls.context.records["capability"], "capability_vocabulary_id", "schuss-capability-vocabulary-000001", 1)
        cls.definitions = {item["key"]: item for item in vocabulary["definitions"]}

    def test_exact_parent_and_closed_count(self):
        manifest = core.load_json(RECORD_SET)
        parent = core.load_json(PARENT_SET)
        self.assertEqual("schuss-record-set-000021", manifest["record_set_id"])
        self.assertEqual(
            {key: parent[key] for key in ("record_set_id", "revision", "content_hash")},
            {key: manifest["parent_reference"][key] for key in ("record_set_id", "revision", "content_hash")},
        )
        self.assertEqual(5, len(self.packet["baseline"]))
        self.assertEqual(15, len(self.packet["additions"]))
        self.assertEqual(20, self.packet["final_safe_selectable_total"])
        self.assertEqual(7, len(self.packet["supporting_profile_not_counted"]))

    def test_exact_fifteen_allocations_and_sources(self):
        self.assertEqual(
            [f"schuss-implementation-{number:06d}" for number in range(97, 112)],
            [item["native_binding_reference"]["implementation_id"] for item in self.packet["additions"]],
        )
        self.assertEqual(
            [f"schuss-direct-operation-spec-{number:06d}" for number in range(15, 30)],
            [item["operation_spec_reference"]["direct_operation_spec_id"] for item in self.packet["additions"]],
        )
        self.assertEqual(
            [113, 229, 1208, 527, 526, 499, 115, 208, 123, 199, 162, 318, 421, 255, 224],
            [item["source_identity"]["variant_index"] for item in self.packet["additions"]],
        )
        self.assertEqual(15, len({core.canonical_json(item["source_identity"]) for item in self.packet["additions"]}))

    def test_contracts_and_native_maps_cover_exact_observed_facets(self):
        observations = {item["variant_index"]: item for item in core.load_jsonl(generator.OBSERVATIONS)}
        for addition in self.packet["additions"]:
            contract_ref = addition["contract_reference"]
            contract = exact(self.context.records["contracts"], "component_contract_id", contract_ref["component_contract_id"], contract_ref["revision"])
            binding_ref = addition["native_binding_reference"]
            binding = exact(self.context.records["bindings"], "implementation_id", binding_ref["implementation_id"], binding_ref["revision"])
            contract_facets = {
                (kind, item["facet_id"])
                for collection, kind in (("ports", "port"), ("parameters", "parameter"), ("attributes", "attribute"), ("actions", "action"), ("displays", "display"))
                for item in contract[collection]
            }
            mapped = {(item["contract_facet"]["facet_kind"], item["contract_facet"]["facet_id"]) for item in binding["facet_mappings"]}
            self.assertEqual(contract_facets, mapped, addition["candidate_id"])
            observation = observations[addition["source_identity"]["variant_index"]]
            observed_count = sum(len(observation["facets"].get(key, [])) for key in ("inlets", "outlets", "parameters", "attributes", "displays"))
            self.assertEqual(observed_count, len(contract_facets), addition["candidate_id"])

    def test_eligibility_is_exact_supported_and_never_falls_back(self):
        for addition in self.packet["additions"]:
            reference = addition["eligibility_reference"]
            eligibility = exact(self.context.records["eligibility"], "binding_eligibility_id", reference["binding_eligibility_id"], reference["revision"])
            self.assertEqual(addition["native_binding_reference"], eligibility["binding_reference"])
            self.assertEqual(self.packet["target_reference"], eligibility["allowed_pair"]["target_reference"])
            self.assertEqual(self.packet["backend_reference"], eligibility["allowed_pair"]["backend_reference"])
            self.assertEqual("supported", eligibility["allowed_pair"]["state"]["status"])
            self.assertEqual(2, eligibility["required_evidence_level"])
            self.assertFalse(eligibility["selection_policy"]["implicit_fallback"])

    def test_all_fifteen_select_and_lower_independently(self):
        self.assertEqual(15, self.proof["selection_count"])
        self.assertEqual(["selected"] * 15, [item["selection_status"] for item in self.proof["operations"]])
        self.assertEqual(
            [item["native_binding_reference"] for item in self.packet["additions"]],
            [item["native_binding_reference"] for item in self.proof["operations"]],
        )
        self.assertTrue(all(item["facet_lowering"] for item in self.proof["operations"]))
        self.assertEqual("normalized-operation-ir-only", self.proof["lowering_boundary"])

    def test_lowerer_fails_closed_on_source_and_eligibility_mutations(self):
        changed = copy.deepcopy(self.packet)
        changed["additions"][0]["source_identity"]["byte_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "TASK028_SOURCE_IDENTITY_MISMATCH"):
            lower_palette(changed, self.context.records["direct_operation_specs"], self.context.records["contracts"], self.context.records["bindings"], self.context.records["eligibility"], self.target, self.backend, self.definitions)
        missing = [item for item in self.context.records["eligibility"] if item["binding_eligibility_id"] != "schuss-binding-eligibility-000033"]
        with self.assertRaisesRegex(ValueError, "TASK028_ELIGIBILITY_REFERENCE_UNRESOLVED"):
            lower_palette(self.packet, self.context.records["direct_operation_specs"], self.context.records["contracts"], self.context.records["bindings"], missing, self.target, self.backend, self.definitions)

    def test_level_specific_evidence_stops_after_lowering(self):
        new_claims = [item for item in self.context.records["evidence"] if 45 <= int(item["evidence_claim_id"].rsplit("-", 1)[1]) <= 74]
        self.assertEqual(30, len(new_claims))
        self.assertEqual(15, sum(item["level"] == 2 for item in new_claims))
        self.assertEqual(15, sum(item["level"] == 3 for item in new_claims))
        self.assertEqual(["passed"] * 3 + ["not-run"] * 5, [item["status"] for item in self.proof["evidence_levels"]])
        self.assertTrue(all(value is False for value in self.proof["actions_performed"].values()))

    def test_mutable_provenance_remains_separate_and_exact(self):
        tagged = [item for item in self.packet["additions"] if item["source_identity"]["provenance_tags"]]
        self.assertEqual({"schuss-implementation-000057", "schuss-implementation-000058"}, {item["source_identity"]["catalog_implementation_id"] for item in tagged})
        self.assertTrue(all(item["functional_category"] == "sound-sources" for item in tagged))
        self.assertTrue(all(item["source_identity"]["provenance_tags"] == ["mutable-instruments-derived"] for item in tagged))

    def test_rings_contradiction_and_absent_native_allocation_are_preserved(self):
        task_records = [item for item in core.load_json(RECORD_SET)["record_members"] if item["portable_path"].startswith("contracts/task028/")]
        self.assertNotIn("schuss-implementation-000094", {item["stable_id"] for item in task_records})
        failed = exact(self.context.records["evidence"], "evidence_claim_id", "schuss-evidence-claim-000042", 1)
        unsupported = exact(self.context.records["eligibility"], "binding_eligibility_id", "schuss-binding-eligibility-000031", 1)
        self.assertEqual("failed", failed["outcome"])
        self.assertEqual("unsupported", unsupported["allowed_pair"]["state"]["status"])
        self.assertEqual(
            exact(self.parent.records["evidence"], "evidence_claim_id", "schuss-evidence-claim-000042", 1), failed
        )
        self.assertEqual(
            exact(self.parent.records["eligibility"], "binding_eligibility_id", "schuss-binding-eligibility-000031", 1), unsupported
        )

    def test_gap_ledger_accounts_for_catalog_and_task027_review(self):
        gaps = core.load_json(ROOT / "evidence/task028-completion-v1/remaining-gaps.json")
        self.assertEqual((83, 20, 63), (gaps["catalog_implementation_count"], gaps["catalog_implementations_backing_counted_promotions"], gaps["catalog_implementations_not_in_bounded_palette"]))
        self.assertEqual(83, len(gaps["catalog_accounting"]))
        self.assertEqual((72, 2, 70), (gaps["task027_source_review_count"], len(gaps["task027_entries_selected_here"]), gaps["task027_entries_remaining"]))
        self.assertEqual(70, len(gaps["task027_remaining_accounting"]))

    def test_generated_records_are_fresh_and_in_process_deterministic(self):
        first_files, first_manifest, first_summary = generator.generated()
        second_files, second_manifest, second_summary = generator.generated()
        self.assertEqual(first_files, second_files)
        self.assertEqual(first_manifest, second_manifest)
        self.assertEqual(first_summary, second_summary)
        for path, expected in first_files.items():
            self.assertEqual(expected, (ROOT / path).read_bytes(), path)
        self.assertEqual(first_manifest, RECORD_SET.read_bytes())


if __name__ == "__main__":
    unittest.main()
