from __future__ import annotations

import copy
import hashlib
import json
import sys
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/contracts")]

from packages.schuss_core.control_plane import dispatch_operation, load_repository_context  # noqa: E402
from packages.schuss_core import catalog_projection  # noqa: E402
from packages.schuss_core.product_cli import catalog_inspect_request, catalog_search_request  # noqa: E402

import generate_task024_records as generator  # noqa: E402
import validator_core as core  # noqa: E402


RECORD_SET = ROOT / "contracts/record-sets/task024-catalog-coverage-v1.json"
REVIEW = ROOT / "catalog/reviews/task024-catalog-coverage-v1"
CURRENT_REVIEW = ROOT / "catalog/reviews/task024-current-ksoloti-v1"
LOCAL_SOURCES = ROOT / "catalog/sources.local.yml"
LOCAL_SOURCE_SKIP = (
    "configured Task 024 source reproduction requires ignored "
    "catalog/sources.local.yml; run "
    "python3 tools/contracts/validate_task024_025_configured_sources.py separately"
)


class Task024CatalogCoverageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = load_repository_context(record_set_path=RECORD_SET)
        cls.coverage = core.load_json(ROOT / "contracts/task024/coverage-report.json")
        cls.packet = core.load_json(ROOT / "contracts/task024/task025-selection-packet.json")
        cls.current_corpus = core.load_json(ROOT / "contracts/task024/current-ksoloti-corpus.json")
        cls.current_candidates = core.load_jsonl(CURRENT_REVIEW / "candidates.jsonl")
        cls.dispositions = core.load_jsonl(REVIEW / "reports/dispositions.jsonl")
        cls.queue = core.load_jsonl(REVIEW / "packets/review-queue.jsonl")

    def test_exact_parent_successor_and_sixty_family_projection(self) -> None:
        manifest = core.load_json(RECORD_SET)
        parent = core.load_json(ROOT / "contracts/record-sets/task023-application-spine-v1.json")
        self.assertEqual("schuss-record-set-000016", manifest["record_set_id"])
        self.assertTrue(all(item in manifest["schema_members"] for item in parent["schema_members"]))
        self.assertTrue(all(item in manifest["record_members"] for item in parent["record_members"]))
        self.assertEqual("catalog-corpus-v3", self.context.records["catalog"][0]["schema_version"])
        self.assertEqual("catalog-projection-v3", self.context.catalog_projection["schema_version"])
        self.assertEqual(60, len(self.context.catalog_projection["families"]))

    def test_every_observation_has_one_exact_ordered_disposition(self) -> None:
        self.assertEqual(3602, len(self.dispositions))
        self.assertEqual(list(range(3602)), [item["variant_index"] for item in self.dispositions])
        counts = Counter(item["disposition"] for item in self.dispositions)
        actual_counts = {
            key: counts[key] for key in self.coverage["disposition_counts"]
        }
        self.assertEqual(self.coverage["disposition_counts"], actual_counts)
        self.assertEqual(3602, sum(counts.values()))
        self.assertEqual(0, counts["duplicate"])
        for item in self.dispositions:
            self.assertEqual(
                f"legacy-resolved-catalog-v0:object:{item['variant_index']}",
                item["evidence_ref"],
            )
            self.assertRegex(item["canonical_observation_sha256"], r"^[0-9a-f]{64}$")

    def test_current_ksoloti_library_model_and_primary_census_are_exact(self) -> None:
        libraries = {item["library_id"]: item for item in self.current_corpus["configured_libraries"]}
        self.assertEqual(
            {"axoloti-factory", "axoloti-contrib", "ksoloti-objects", "ksoloti-contrib"},
            set(libraries),
        )
        self.assertEqual(
            {"axoloti-factory", "ksoloti-objects"},
            {key for key, value in libraries.items() if value["candidate_indexed"]},
        )
        self.assertTrue(all(item["ksoloti_default_enabled"] for item in libraries.values()))
        primary = self.current_corpus["primary_corpus"]
        self.assertEqual(
            {
                "axo_file_count": 668,
                "normal_definition_count": 835,
                "canonical_base_ref_count": 666,
                "axs_compound_count": 19,
                "candidate_count": 685,
                "variant_count": 854,
            },
            {key: primary[key] for key in (
                "axo_file_count", "normal_definition_count", "canonical_base_ref_count",
                "axs_compound_count", "candidate_count", "variant_count",
            )},
        )
        self.assertEqual(685, len(self.current_candidates))
        self.assertEqual(854, sum(len(item["variants"]) for item in self.current_candidates))
        self.assertEqual(
            primary["candidate_artifact"]["byte_sha256"],
            core.sha256_file(CURRENT_REVIEW / "candidates.jsonl"),
        )

    def test_current_candidates_keep_import_dependency_and_lineage_facets_separate(self) -> None:
        self.assertEqual(
            [
                (item["library_id"], item["canonical_id"], item["import_form"])
                for item in self.current_candidates
            ],
            sorted(
                (item["library_id"], item["canonical_id"], item["import_form"])
                for item in self.current_candidates
            ),
        )
        forms = Counter(item["import_form"] for item in self.current_candidates)
        self.assertEqual(666, forms["axo-normal-definition"])
        self.assertEqual(19, forms["axs-unloaded-subpatch"])
        encoded = b"".join(core.canonical_json(item).encode("utf-8") for item in self.current_candidates)
        self.assertNotIn(b"/Users/", encoded)
        for candidate in self.current_candidates:
            self.assertIn(candidate["lineage_status"], {"complete", "partial", "absent"})
            for variant in candidate["variants"]:
                self.assertTrue(variant["source_path"].startswith("objects/"))
                self.assertRegex(variant["source_sha256"], r"^[0-9a-f]{64}$")
                self.assertIsInstance(variant["declared_includes"], list)
                self.assertIsInstance(variant["declared_dependencies"], list)

    def test_disposition_precedence_is_factual_and_fail_closed(self) -> None:
        base = {
            "variant_index": 7,
            "export_status": "complete",
            "legacy_class": "axoloti.object.AxoObject",
            "legacy_kind": "native_definition",
            "legacy_id": "unique/value",
            "uuid": {"runtime_kind": "explicit", "durable_value": "abc"},
        }
        self.assertEqual("implementation-variant", generator.disposition_for(base, reviewed=set(), duplicate_uuids=set(), overloaded_ids=set())[0])
        changed = copy.deepcopy(base); changed["export_status"] = "partial"
        self.assertEqual("unresolved", generator.disposition_for(changed, reviewed={7}, duplicate_uuids={"abc"}, overloaded_ids={"unique/value"})[0])
        changed = copy.deepcopy(base); changed["legacy_class"] = "axoloti.object.AxoObjectComment"
        self.assertEqual("editor-only-non-headless", generator.disposition_for(changed, reviewed={7}, duplicate_uuids={"abc"}, overloaded_ids={"unique/value"})[0])
        self.assertEqual("duplicate", generator.disposition_for(base, reviewed={7}, duplicate_uuids={"abc"}, overloaded_ids={"unique/value"})[0])
        self.assertEqual("reviewed-family", generator.disposition_for(base, reviewed={7}, duplicate_uuids=set(), overloaded_ids={"unique/value"})[0])
        self.assertEqual("overload-group", generator.disposition_for(base, reviewed=set(), duplicate_uuids=set(), overloaded_ids={"unique/value"})[0])
        changed = copy.deepcopy(base); changed["uuid"]["runtime_kind"] = "generated-nondeterministic"
        self.assertEqual("queued-human-review", generator.disposition_for(changed, reviewed=set(), duplicate_uuids=set(), overloaded_ids=set())[0])

    def test_review_queue_is_frequency_priority_only_and_deterministic(self) -> None:
        keys = [(-item["complete_graph_reference_count"], item["variant_index"]) for item in self.queue]
        self.assertEqual(sorted(keys), keys)
        self.assertTrue(all(item["frequency_policy"] == "prioritization-only" for item in self.queue))
        self.assertEqual(self.coverage["review_queue_count"], len(self.queue))

    def test_twenty_new_families_are_catalog_only_with_complete_current_cohorts(self) -> None:
        additions = [
            entry for entry in self.context.catalog_projection["families"]
            if 41 <= int(entry["family_reference"]["family_id"].rsplit("-", 1)[1]) <= 60
        ]
        self.assertEqual(20, len(additions))
        self.assertEqual(set(range(41, 61)), {int(item["family_reference"]["family_id"].rsplit("-", 1)[1]) for item in additions})
        treatment_counts = Counter(item["curation_treatment"] for item in additions)
        self.assertEqual({"retain": 11, "revise": 7, "reconsider": 2}, dict(treatment_counts))
        reconsidered = {item["family_reference"]["family_id"] for item in additions if item["curation_treatment"] == "reconsider"}
        self.assertEqual({"schuss-family-000042", "schuss-family-000057"}, reconsidered)
        for entry in additions:
            self.assertFalse(entry["contract_facets_available"])
            self.assertEqual(["catalogued-only", "unresolved"], entry["readiness_states"])
            self.assertTrue(entry["provenance_facets"])
            self.assertTrue(entry["unresolved_facts"])
            self.assertEqual(
                entry["current_variant_coverage"]["candidate_variant_count"],
                entry["current_variant_coverage"]["catalogued_variant_count"],
            )
            self.assertEqual(
                entry["current_variant_coverage"]["catalogued_variant_count"],
                len(entry["implementations"]),
            )
            self.assertTrue(entry["current_ksoloti_base_refs"])
            self.assertTrue(all(item["observation_references"] for item in entry["implementations"]))
        implementation_ids = {
            item["implementation_id"]
            for entry in additions
            for item in entry["implementations"]
        }
        self.assertTrue({f"schuss-implementation-{value:06d}" for value in range(81, 90)} <= implementation_ids)

    def test_task025_packet_is_exactly_the_effects_graph_contract_set(self) -> None:
        graph = next(item for item in self.context.records["graphs"] if item["graph_id"] == "schuss-graph-000004" and item["revision"] == 1)
        expected = {item["contract_reference"]["component_contract_id"] for item in graph["nodes"]}
        actual = {item["contract_reference"]["stable_id"] for item in self.packet["subjects"]}
        self.assertEqual(8, len(expected))
        self.assertEqual(expected, actual)
        self.assertEqual(["passed", "passed"] + ["not-run"] * 6, [item["status"] for item in self.packet["evidence_levels"]])

    def test_shared_search_and_inspect_expose_new_catalog_families(self) -> None:
        search = catalog_search_request("interpolated delay", {})
        first = dispatch_operation(search, self.context)
        second = dispatch_operation(copy.deepcopy(search), self.context)
        self.assertEqual(core.canonical_json(first), core.canonical_json(second))
        self.assertEqual("success", first["status"])
        self.assertEqual("schuss-family-000059", first["value"]["results"][0]["family_reference"]["family_id"])
        self.assertEqual("retain", first["value"]["results"][0]["curation_treatment"])
        self.assertEqual("advanced", first["value"]["results"][0]["drawer_visibility"])
        family = next(
            entry for entry in self.context.catalog_projection["families"]
            if entry["family_reference"]["family_id"] == "schuss-family-000059"
        )
        inspect_request = catalog_inspect_request(family["family_reference"])
        inspected = dispatch_operation(inspect_request, self.context)
        self.assertEqual("success", inspected["status"])
        self.assertEqual(["catalogued-only", "unresolved"], inspected["value"]["family"]["readiness_states"])
        self.assertEqual(["axoloti-factory:delay/read interp"], inspected["value"]["family"]["current_ksoloti_base_refs"])

    @unittest.skipUnless(LOCAL_SOURCES.is_file(), LOCAL_SOURCE_SKIP)
    def test_generated_outputs_are_fresh_and_byte_deterministic(self) -> None:
        first_files, first_manifest, first_summary = generator.generated()
        second_files, second_manifest, second_summary = generator.generated()
        self.assertEqual(first_manifest, second_manifest)
        self.assertEqual(first_summary, second_summary)
        self.assertEqual(first_files, second_files)
        expected = {**first_files, RECORD_SET.relative_to(ROOT).as_posix(): first_manifest}
        self.assertTrue(all((ROOT / path).read_bytes() == payload for path, payload in expected.items()))

    def test_stale_catalog_source_fails_projection(self) -> None:
        corpus = copy.deepcopy(self.context.records["catalog"][0])
        family = corpus["family_additions"][-1]
        family["source_authority"]["observation"]["source_sha256"] = "0" * 64
        family["content_hash"] = "sha256:" + hashlib.sha256(
            core.canonical_json(
                {key: value for key, value in family.items() if key != "content_hash"}
            ).encode("utf-8")
        ).hexdigest()
        schema = self.context.schemas["catalog_corpus"]
        corpus["content_hash"] = core.record_content_hash(corpus, schema)
        with self.assertRaisesRegex(catalog_projection.CatalogProjectionError, "source observation closure is stale"):
            catalog_projection.build_catalog_projection(
                corpus=corpus,
                corpus_schema=schema,
                projection_schema=self.context.schemas["catalog_projection"],
                overlay=core.load_json(ROOT / "catalog/overlays/phase-4a-semantic-catalog-v0/catalog.json"),
                overlay_sha256=core.sha256_file(ROOT / "catalog/overlays/phase-4a-semantic-catalog-v0/catalog.json"),
                observations={f"legacy-resolved-catalog-v0:object:{item['variant_index']}": item for item in core.load_jsonl(ROOT / "catalog/snapshots/legacy-resolved-catalog-v0/resolved/objects.jsonl")},
                records=self.context.records,
                record_set_reference=self.context.record_set_reference,
                core=core,
            )


if __name__ == "__main__":
    unittest.main()
