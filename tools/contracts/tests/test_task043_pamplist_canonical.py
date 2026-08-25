from __future__ import annotations

import copy
from pathlib import Path
import unittest

from packages.schuss_core.control_plane import load_repository_context
from packages.schuss_core.instrument_library import (
    InstrumentLibraryError,
    InstrumentLibraryService,
)
from tools.contracts import generate_task043_pamplist_canonical as generator
from tools.contracts import validator_core as core


ROOT = Path(__file__).resolve().parents[3]
RECORD_SET = ROOT / "contracts/record-sets/task043-pamplist-canonical-v1.json"


class Task043PamplistCanonicalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = load_repository_context(ROOT, record_set_path=RECORD_SET)

    def test_complete_promotion_closure_is_valid(self) -> None:
        self.assertEqual(
            "schuss-record-set-000036",
            self.context.record_set_reference["record_set_id"],
        )
        self.assertEqual(
            "catalog-projection-v7",
            self.context.catalog_projection["schema_version"],
        )
        self.assertNotIn(
            generator.IMPLEMENTATION_ID,
            {
                binding["catalog_implementation_locator"]["implementation_id"]
                for provider in self.context.records["implementation_providers"]
                for binding in provider["bindings"]
            },
        )

    def test_catalog_and_semantic_identity_are_exact(self) -> None:
        family = next(
            value
            for value in self.context.catalog_projection["families"]
            if value["family_reference"]["family_id"] == generator.FAMILY_ID
        )
        graph = next(
            value
            for value in self.context.records["graphs"]
            if value["graph_id"] == generator.GRAPH_ID
        )
        instrument = next(
            value
            for value in self.context.records["performance_instruments"]
            if value["instrument_id"] == generator.INSTRUMENT_ID
        )
        self.assertEqual("instrument", family["abstraction_level"])
        self.assertEqual(
            [generator.IMPLEMENTATION_ID],
            [value["implementation_id"] for value in family["implementations"]],
        )
        self.assertEqual(7, len(graph["nodes"]))
        self.assertEqual(178, len(graph["parameter_bindings"]))
        self.assertEqual(180, len(instrument["graph_mappings"]))
        self.assertEqual(
            {
                "status": "resolved",
                "graph_id": graph["graph_id"],
                "revision": graph["revision"],
                "content_hash": graph["content_hash"],
            },
            instrument["graph_reference"],
        )

    def test_library_links_only_pamplist_to_the_selected_records(self) -> None:
        service = InstrumentLibraryService(
            ROOT,
            context=self.context,
            process_factory=lambda _path: self.fail("listing must not spawn"),
        )
        library = service.list_instruments()
        canonical = [
            value
            for value in library["instruments"]
            if value["canonical_identity"]["status"] == "canonical"
        ]
        self.assertEqual(2, library["library_revision"])
        self.assertEqual(6, library["instrument_count"])
        self.assertEqual(["pamplist"], [value["prototype_id"] for value in canonical])
        self.assertEqual(
            self.context.record_set_reference,
            canonical[0]["canonical_identity"]["record_set_reference"],
        )
        self.assertEqual("verified-local-build", canonical[0]["availability"])

    def test_stale_canonical_record_set_reference_fails_closed(self) -> None:
        manifest = core.load_json(
            ROOT
            / "research/prototype_support/instrument_library/"
            "audition-library-v2.json"
        )
        entry = copy.deepcopy(
            next(value for value in manifest["entries"] if value["prototype_id"] == "pamplist")
        )
        entry["canonical_identity"]["record_set_reference"]["content_hash"] = (
            "sha256:" + "0" * 64
        )
        service = InstrumentLibraryService(ROOT, context=self.context)
        with self.assertRaises(InstrumentLibraryError) as captured:
            service._validated_canonical_identity(entry)
        self.assertEqual("INSTRUMENT_CANONICAL_RECORD_SET_CHANGED", captured.exception.code)


if __name__ == "__main__":
    unittest.main()
