import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools/inventory"
sys.path.insert(0, str(TOOLS))

BUILDER_SPEC = importlib.util.spec_from_file_location(
    "build_phase3_review_packet", TOOLS / "build_phase3_review_packet.py"
)
BUILDER = importlib.util.module_from_spec(BUILDER_SPEC)
sys.modules[BUILDER_SPEC.name] = BUILDER
BUILDER_SPEC.loader.exec_module(BUILDER)


def object_record(index, *, path=None, kind="native_definition", list_index=None, provider=False):
    if provider:
        origin = {
            "kind": "provider",
            "provider": {"source_id": "patcher", "path": "src/Generator.java", "sha256": "0" * 64},
        }
    else:
        origin = {
            "kind": "file",
            "source_id": "factory",
            "path": path,
            "definition_index": index,
            "sha256": "0" * 64,
            "generated_by": None,
        }
    return {
        "variant_index": index,
        "legacy_kind": kind,
        "legacy_object_list_index": list_index,
        "origin": origin,
    }


class Phase3ReviewTest(unittest.TestCase):
    def test_object_reconciliation_names_both_equations(self):
        objects = [
            object_record(0, path="objects/a.axo", list_index=0),
            object_record(1, path="objects/a.axo"),
            object_record(
                2,
                path="objects/compound.axs",
                kind="subpatch_catalog_placeholder",
                list_index=1,
            ),
            object_record(3, provider=True),
        ]
        issues = [
            {
                "code": "LEGACY_OBJECT_LIST_COLLAPSE",
                "candidate_variant_indexes": [0, 1],
            }
        ]
        report = BUILDER.build_object_reconciliation(objects, issues)
        self.assertEqual(2, report["definition_occurrences"])
        self.assertEqual(1, report["legacy_equality_collapsed_occurrences"])
        self.assertEqual(1, report["catalog_subpatch_placeholders"])
        self.assertEqual(1, report["provider_only_records"])
        self.assertEqual(2, report["retained_in_legacy_object_list"])
        self.assertEqual(4, report["exported_object_records"])
        self.assertEqual(2, report["not_retained_in_legacy_object_list"])
        self.assertTrue(all(item["left"] == item["right"] for item in report["equations"]))

    def test_hash_rank_sample_is_order_independent(self):
        rows = [{"evidence_ref": f"item:{index}"} for index in range(40)]
        forward = BUILDER.deterministic_sample(rows, "fixture", "evidence_ref")
        reverse = BUILDER.deterministic_sample(reversed(rows), "fixture", "evidence_ref")
        self.assertEqual(forward, reverse)
        self.assertEqual(25, len(forward))
        self.assertEqual(25, len({item["evidence_ref"] for item in forward}))
        self.assertTrue(all(len(item["rank_sha256"]) == 64 for item in forward))

    def test_impact_policy_is_closed_and_uses_named_levels(self):
        expected_codes = {
            "AMBIGUOUS_INSTANCE_RESOLUTION",
            "GENERATED_DEFINITION_COUNT_MISMATCH",
            "GENERATED_EMISSION_UNMATCHED",
            "GENERATED_OUTPUT_REDEFINED",
            "GENERATED_OUTPUT_REPEATED_IDENTICAL",
            "GRAPH_POST_CONSTRUCTION_FAILED",
            "GRAPH_XML_SCAN_FAILED",
            "INSTANCE_BECAME_ZOMBIE",
            "INSTANCE_RESOLUTION_UNPROVEN",
            "LEGACY_OBJECT_LIST_COLLAPSE",
            "NET_ENDPOINT_PORT_MISSING",
            "NET_REMOVED_DURING_RESOLUTION",
            "NET_STRUCTURALLY_INCOMPLETE",
            "NONPORTABLE_GRAPH_VALUE_REDACTED",
            "OVERLOADED_NAME_CANDIDATES",
            "RAW_BASELINE_OMISSION",
            "SERIALIZED_ATTRIBUTE_NOT_PROJECTED",
            "SERIALIZED_HARD_ZOMBIE",
            "SERIALIZED_PARAMETER_NOT_PROJECTED",
            "UNSUPPORTED_ATTRIBUTE_VALUE",
        }
        self.assertEqual(expected_codes, set(BUILDER.IMPACT_POLICY))
        for policy in BUILDER.IMPACT_POLICY.values():
            self.assertIn(policy["taxonomy"], BUILDER.IMPACT_LEVELS)
            self.assertIn(policy["migration"], BUILDER.IMPACT_LEVELS)
            self.assertIn(policy["compilation"], BUILDER.IMPACT_LEVELS)
            self.assertTrue(policy["rationale"])


if __name__ == "__main__":
    unittest.main()
