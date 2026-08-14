import copy
import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools/catalog"
SPEC = importlib.util.spec_from_file_location(
    "validate_semantic_catalog", TOOLS / "validate_semantic_catalog.py"
)
VALIDATOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = VALIDATOR
SPEC.loader.exec_module(VALIDATOR)

OVERLAY_ROOT = ROOT / "catalog/overlays/phase-4a-semantic-catalog-v0"
SCHEMA_ROOT = ROOT / "schemas"
SNAPSHOT_ROOT = ROOT / "catalog/snapshots/legacy-resolved-catalog-v0"
REVIEW_ROOT = ROOT / "catalog/reviews/phase-3-inventory-review-v0"


class SemanticCatalogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.overlay = VALIDATOR.load_json(OVERLAY_ROOT / "catalog.json")
        cls.schema = VALIDATOR.load_json(
            SCHEMA_ROOT / "semantic-catalog-overlay-v0.schema.json"
        )

    def validate(self, overlay):
        return VALIDATOR.validate_overlay_value(
            overlay, self.schema, SNAPSHOT_ROOT, REVIEW_ROOT
        )

    def test_committed_pilot_validates_and_covers_required_cases(self):
        summary = self.validate(copy.deepcopy(self.overlay))
        self.assertEqual(26, summary["family_count"])
        self.assertEqual(38, summary["implementation_count"])
        self.assertEqual(13, len(summary["category_coverage"]))
        self.assertTrue(all(summary["required_cases"].values()))

    def test_validation_summary_is_deterministic(self):
        first = VALIDATOR.canonical_json(self.validate(copy.deepcopy(self.overlay)))
        second = VALIDATOR.canonical_json(self.validate(copy.deepcopy(self.overlay)))
        self.assertEqual(first, second)

    def test_identity_does_not_follow_display_or_category_edits(self):
        changed = copy.deepcopy(self.overlay)
        before = VALIDATOR.identity_projection(changed)
        changed["families"][0]["display_name"] = "Renamed Input"
        changed["families"][0]["primary_category"] = "interface-system"
        changed["families"][24]["primary_category"] = "input-output"
        after = VALIDATOR.identity_projection(changed)
        self.assertEqual(before, after)
        self.validate(changed)

    def test_missing_evidence_reference_fails_closed(self):
        changed = copy.deepcopy(self.overlay)
        changed["implementations"][0]["legacy_evidence_refs"] = [
            "legacy-resolved-catalog-v0:object:999999"
        ]
        with self.assertRaisesRegex(
            VALIDATOR.CatalogValidationError, "unresolved evidence reference"
        ):
            self.validate(changed)

    def test_low_membership_confidence_requires_question(self):
        changed = copy.deepcopy(self.overlay)
        changed["implementations"][22]["unresolved_questions"] = []
        with self.assertRaisesRegex(
            VALIDATOR.CatalogValidationError, "low membership confidence"
        ):
            self.validate(changed)

    def test_primary_category_cannot_be_provenance(self):
        changed = copy.deepcopy(self.overlay)
        changed["families"][0]["primary_category"] = "factory"
        with self.assertRaisesRegex(
            VALIDATOR.CatalogValidationError, "outside the enum"
        ):
            self.validate(changed)


if __name__ == "__main__":
    unittest.main()
