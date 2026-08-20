from __future__ import annotations

import copy
import hashlib
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/contracts")]

from packages.schuss_core import catalog_projection  # noqa: E402
from packages.schuss_core.control_plane import dispatch_operation, load_repository_context  # noqa: E402
from packages.schuss_core.product_cli import catalog_inspect_request, catalog_search_request  # noqa: E402

import generate_task027_records as generator  # noqa: E402
import validator_core as core  # noqa: E402
from tools.validation.profile import requires_profile  # noqa: E402


RECORD_SET = ROOT / "contracts/record-sets/task027-mutable-catalog-v1.json"
TAG = "mutable-instruments-derived"


class Task027MutableCatalogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = load_repository_context(record_set_path=RECORD_SET)
        cls.review = core.load_json(ROOT / "contracts/task027/catalog-source-review.json")
        cls.corpus = core.load_json(ROOT / "contracts/task027/catalog-corpus-v4.json")
        cls.packet = core.load_jsonl(ROOT / "catalog/reviews/task027-mutable-sources-v1/candidates.jsonl")

    def test_exact_parent_successor_preserves_sixty_families(self) -> None:
        manifest = core.load_json(RECORD_SET)
        parent = core.load_json(ROOT / "contracts/record-sets/task026-authoring-workflow-v1.json")
        self.assertEqual("schuss-record-set-000020", manifest["record_set_id"])
        self.assertTrue(all(item in manifest["schema_members"] for item in parent["schema_members"]))
        self.assertTrue(all(item in manifest["record_members"] for item in parent["record_members"]))
        self.assertEqual("catalog-corpus-v4", self.context.records["catalog"][0]["schema_version"])
        self.assertEqual("catalog-projection-v4", self.context.catalog_projection["schema_version"])
        self.assertEqual(60, len(self.context.catalog_projection["families"]))
        self.assertEqual(83, sum(len(item["implementations"]) for item in self.context.catalog_projection["families"]))

    def test_source_review_census_and_portability_are_exact(self) -> None:
        self.assertEqual(72, len(self.packet))
        self.assertEqual(self.review["entries"], self.packet)
        self.assertEqual([item["entry_id"] for item in self.packet], sorted(item["entry_id"] for item in self.packet))
        self.assertEqual(19, self.review["counts"]["extended"])
        self.assertEqual(53, self.review["counts"]["factory"])
        self.assertEqual(56, self.review["counts"]["tagged"])
        self.assertEqual(16, self.review["counts"]["inventory_only"])
        self.assertEqual(6, self.review["counts"]["catalogued_implementations"])
        self.assertEqual(50, self.review["counts"]["tagged_candidates"])
        encoded = b"".join(core.canonical_json(item).encode("utf-8") for item in self.packet)
        self.assertNotIn(b"/Users/", encoded)
        self.assertNotIn(b"2026-", encoded)

    def test_extended_inventory_has_exact_identity_license_category_and_disposition(self) -> None:
        extended = [item for item in self.packet if item["source_kind"] == "extended-object"]
        self.assertEqual(19, len(extended))
        self.assertEqual(19, len({item["stable_source_id"] for item in extended}))
        self.assertTrue(all(item["functional_category"] in generator.FUNCTION_CATEGORIES for item in extended))
        self.assertTrue(all(item["declared_license"] for item in extended))
        self.assertEqual(
            {
                "com.lalzart.ksoloti.extended.physical.resonator",
                "com.lalzart.ksoloti.extended.sequencing.topographic-3",
                "com.lalzart.ksoloti.extended.synthesis.macro-voice",
            },
            {item["stable_source_id"] for item in extended if TAG in item["provenance_tags"]},
        )
        self.assertEqual(16, sum(item["disposition"] == "inventory-only" for item in extended))

    def test_macro_voice_and_warps_boundaries_are_retained_as_source_metadata(self) -> None:
        macro = next(item for item in self.packet if item["stable_source_id"].endswith("synthesis.macro-voice"))
        self.assertEqual("tagged-candidate", macro["disposition"])
        self.assertEqual("h7-recommended", macro["source_manifest_metadata"]["tier"])
        self.assertEqual("build-failed", macro["source_manifest_metadata"]["build_status"])
        self.assertEqual("source-declared-metadata-not-schuss-evidence", macro["source_manifest_metadata"]["authority"])
        vocoder = next(item for item in self.packet if item["stable_source_id"].startswith("axoloti-factory:fx/wrps/vocoder@"))
        wrps = next(item for item in self.packet if item["stable_source_id"].startswith("axoloti-factory:fx/wrps/wrps@"))
        self.assertEqual("tagged-candidate", vocoder["disposition"])
        self.assertEqual("tagged-candidate", wrps["disposition"])
        self.assertTrue(any("will not currently link" in value for value in wrps["known_source_limitations"]))
        self.assertIsNone(vocoder["catalog_implementation_id"])
        self.assertIsNone(wrps["catalog_implementation_id"])

    def test_only_extended_resonator_is_added_as_an_existing_family_implementation(self) -> None:
        prior = core.load_json(ROOT / "contracts/task024/catalog-corpus-v3.json")
        self.assertEqual(prior["family_additions"], self.corpus["family_additions"])
        self.assertEqual(prior["implementation_additions"], self.corpus["implementation_additions"][:-1])
        addition = self.corpus["implementation_additions"][-1]
        self.assertEqual("schuss-implementation-000096", addition["implementation_id"])
        self.assertEqual("schuss-family-000010", addition["family_reference"]["family_id"])
        self.assertEqual("not-evaluated", addition["compatibility_status"])
        self.assertEqual("pinned-source-object", addition["source_authority"]["kind"])
        family = next(item for item in self.context.catalog_projection["families"] if item["family_reference"]["family_id"] == "schuss-family-000010")
        implementation = next(item for item in family["implementations"] if item["implementation_id"] == "schuss-implementation-000096")
        self.assertEqual(["catalogued-only", "unresolved"], implementation["readiness_states"])
        self.assertEqual([TAG], implementation["provenance_tags"])
        for field in (
            "contract_references", "binding_references", "eligibility_references",
            "result_references", "artifact_references", "evidence_references",
        ):
            self.assertEqual([], implementation[field])

    def test_shared_provenance_search_and_per_implementation_inspect_are_exact(self) -> None:
        request = catalog_search_request("", {"provenance": [TAG]})
        result = dispatch_operation(request, self.context)
        self.assertEqual("success", result["status"])
        self.assertEqual(
            {
                "schuss-family-000006", "schuss-family-000010", "schuss-family-000036",
                "schuss-family-000037", "schuss-family-000038",
            },
            {item["family_reference"]["family_id"] for item in result["value"]["results"]},
        )
        self.assertEqual(5, len(result["value"]["results"]))
        family = next(item for item in self.context.catalog_projection["families"] if item["family_reference"]["family_id"] == "schuss-family-000010")
        inspected = dispatch_operation(catalog_inspect_request(family["family_reference"]), self.context)
        self.assertEqual("success", inspected["status"])
        tags = {
            item["implementation_id"]: item["provenance_tags"]
            for item in inspected["value"]["family"]["implementations"]
        }
        self.assertEqual([TAG], tags["schuss-implementation-000016"])
        self.assertEqual([TAG], tags["schuss-implementation-000096"])

    def test_rings_reverb_failure_parent_bytes_remain_exact(self) -> None:
        manifest = core.load_json(RECORD_SET)
        parent = core.load_json(ROOT / "contracts/record-sets/task026-authoring-workflow-v1.json")
        task025_parent = {
            (item["portable_path"], item["byte_sha256"], item["content_hash"])
            for item in parent["record_members"]
            if item["portable_path"].startswith("contracts/task025/")
        }
        task025_current = {
            (item["portable_path"], item["byte_sha256"], item["content_hash"])
            for item in manifest["record_members"]
            if item["portable_path"].startswith("contracts/task025/")
        }
        self.assertEqual(task025_parent, task025_current)
        boundary = (ROOT / "contracts/task025/reverb-allocation-boundary.md").read_text(encoding="utf-8")
        self.assertIn("stays deterministically unsupported", boundary)

    def test_stale_provenance_source_evidence_fails_closed(self) -> None:
        corpus = copy.deepcopy(self.corpus)
        corpus["mutable_instruments_review"]["implementation_tags"][0]["source_entry_id"] = "factory:absent"
        schema = self.context.schemas["catalog_corpus"]
        corpus["content_hash"] = core.record_content_hash(corpus, schema)
        with self.assertRaisesRegex(catalog_projection.CatalogProjectionError, "source entry is absent"):
            catalog_projection.build_catalog_projection(
                corpus=corpus, corpus_schema=schema,
                projection_schema=self.context.schemas["catalog_projection"],
                overlay=copy.deepcopy(self.context.overlay), overlay_sha256=self.context.overlay_sha256,
                observations=copy.deepcopy(self.context.observations), records=self.context.records,
                record_set_reference=copy.deepcopy(self.context.record_set_reference), core=core,
            )

    @requires_profile("configured-sources")
    def test_configured_pinned_source_bytes_match_accepted_review(self) -> None:
        sources = generator._local_sources()
        for entry in self.review["entries"]:
            checkout = sources.get(entry["source_id"])
            self.assertIsNotNone(checkout, entry["source_id"])
            for source_path in entry["source_paths"]:
                completed = subprocess.run(
                    [
                        "git",
                        "-C",
                        str(checkout),
                        "show",
                        f"{entry['commit']}:{source_path['portable_path']}",
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )
                self.assertEqual(0, completed.returncode, completed.stderr.decode())
                self.assertEqual(
                    source_path["byte_sha256"],
                    hashlib.sha256(completed.stdout).hexdigest(),
                    entry["entry_id"],
                )


if __name__ == "__main__":
    unittest.main()
