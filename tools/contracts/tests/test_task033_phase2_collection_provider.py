from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools/contracts"
sys.path[:0] = [str(ROOT), str(TOOLS)]

import collection_provider_rules as rules  # noqa: E402
import record_set_rules  # noqa: E402
import validator_core as core  # noqa: E402
from packages.schuss_core import application_capabilities  # noqa: E402
from packages.schuss_core.control_plane import (  # noqa: E402
    canonical_result_bytes,
    dispatch_operation,
    load_repository_context,
)


RECORD_SET = Path(
    "contracts/record-sets/task033-phase2-collection-provider-v1.json"
)
PARENT_RECORD_SET = Path("contracts/record-sets/task034-performance-control-v1.json")
HOST_IDS = {f"schuss-implementation-{number:06d}" for number in range(162, 169)}


def _reference(record, id_field):
    return {
        id_field: record[id_field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


class Task033Phase2CollectionProviderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.selected = record_set_rules.load_record_set(ROOT, RECORD_SET)
        cls.parent = record_set_rules.load_record_set(ROOT, PARENT_RECORD_SET)
        cls.context = load_repository_context(ROOT, record_set_path=RECORD_SET)
        cls.projection = cls.context.catalog_projection
        cls.implementations = {
            implementation["implementation_id"]: implementation
            for family in cls.projection["families"]
            for implementation in family["implementations"]
        }
        cls.base_records = {
            "catalog": list(cls.context.records["catalog"]),
            "source_releases": list(cls.context.records["source_releases"]),
            "object_collections": list(cls.context.records["object_collections"]),
            "implementation_providers": list(
                cls.context.records["implementation_providers"]
            ),
            "availability_policies": list(cls.context.records["availability_policies"]),
            "contracts": list(cls.context.records["contracts"]),
            "bindings": list(cls.context.records["bindings"]),
            "eligibility": list(cls.context.records["eligibility"]),
            "target": list(cls.context.records["target"]),
            "backend": list(cls.context.records["backend"]),
        }

    def _mutated(self):
        return copy.deepcopy(self.base_records)

    def _validate(self, records):
        return rules.validate_values(
            records,
            self.selected.schemas,
            self.projection,
            repository_root=ROOT,
            all_records=self.selected.records,
        )

    @staticmethod
    def _codes(value):
        return {item["code"] for item in value["diagnostics"]}

    def _rehash(self, record, schema_version):
        record["content_hash"] = "sha256:" + "0" * 64
        record["content_hash"] = core.record_content_hash(
            record, self.selected.schemas[schema_version]
        )

    def _profile(
        self,
        *,
        installed_sources=True,
        installed_provider=True,
        enabled=True,
        use_context="private-development",
        order=None,
    ):
        collections = list(self.context.records["object_collections"])
        if order is not None:
            by_id = {item["object_collection_id"]: item for item in collections}
            ordered = [by_id[item] for item in order]
        else:
            ordered = collections
        source_records = (
            list(self.context.records["source_releases"])
            if installed_sources is True
            else [
                item
                for item in self.context.records["source_releases"]
                if item["source_release_id"] in set(installed_sources)
            ]
        )
        providers = (
            list(self.context.records["implementation_providers"])
            if installed_provider
            else []
        )
        enabled_ids = (
            {item["object_collection_id"] for item in collections}
            if enabled is True
            else set(enabled)
            if enabled is not False
            else set()
        )
        return {
            "schema_version": "collection-profile-v0",
            "canonical_profile": "schuss-canonical-json-v1",
            "use_context": use_context,
            "installed_source_release_references": [
                _reference(item, "source_release_id") for item in source_records
            ],
            "installed_provider_references": [
                _reference(item, "implementation_provider_id") for item in providers
            ],
            "collection_states": [
                {
                    "collection_reference": _reference(
                        item, "object_collection_id"
                    ),
                    "enabled_for_discovery": item["object_collection_id"]
                    in enabled_ids,
                }
                for item in collections
            ],
            "collection_order": [
                _reference(item, "object_collection_id") for item in ordered
            ],
        }

    def _availability_request(self, profile, *, pair_index=0, implementation_id=None):
        implementation_id = implementation_id or "schuss-implementation-000162"
        pair = self.context.records["availability_policies"][0]["reported_pairs"][
            pair_index
        ]
        return {
            "schema_version": "schuss-operation-request-v18",
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": "implementation.availability.inspect",
            "payload": {
                "profile": profile,
                "catalog_implementation_locator": {
                    "catalog_reference": copy.deepcopy(
                        self.projection["catalog_reference"]
                    ),
                    "implementation_id": implementation_id,
                },
                "target_reference": copy.deepcopy(pair["target_reference"]),
                "backend_reference": copy.deepcopy(pair["backend_reference"]),
            },
        }

    def test_generation_is_fresh_and_parent_is_exactly_preserved(self):
        completed = subprocess.run(
            [
                sys.executable,
                "tools/contracts/generate_task033_phase2_records.py",
                "--check",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual(
            {"status": "included", **self.parent.reference},
            self.selected.manifest["parent_reference"],
        )
        parent_schemas = {
            (item["schema_version"], item["portable_path"]): item
            for item in self.parent.manifest["schema_members"]
        }
        selected_schemas = {
            (item["schema_version"], item["portable_path"]): item
            for item in self.selected.manifest["schema_members"]
        }
        self.assertEqual(
            parent_schemas,
            {key: selected_schemas[key] for key in parent_schemas},
        )
        parent_records = {
            (
                item["record_kind"],
                item["stable_id"],
                item["revision"],
                item["portable_path"],
            ): item
            for item in self.parent.manifest["record_members"]
        }
        selected_records = {
            (
                item["record_kind"],
                item["stable_id"],
                item["revision"],
                item["portable_path"],
            ): item
            for item in self.selected.manifest["record_members"]
        }
        self.assertEqual(
            parent_records,
            {key: selected_records[key] for key in parent_records},
        )

    def test_complete_collection_provider_closure_is_valid(self):
        summary = self._validate(self._mutated())
        self.assertEqual("valid", summary["status"])
        self.assertEqual([], summary["diagnostics"])
        self.assertEqual(
            {
                "source_releases": 7,
                "object_collections": 4,
                "implementation_providers": 1,
                "availability_policies": 1,
            },
            summary["record_counts"],
        )
        self.assertTrue(
            summary["boundary_assertions"]["collections_are_function_neutral"]
        )
        self.assertTrue(summary["boundary_assertions"]["providers_are_static"])

    def test_catalog_preserves_task030_and_adds_only_seven_host_companions(self):
        self.assertEqual(107, len(self.projection["families"]))
        self.assertEqual(140, len(self.implementations))
        current_catalog = self.context.records["catalog"][0]
        parent_catalog = next(
            item
            for item in self.parent.records["catalog-corpus"]
            if item["catalog_id"] == "schuss-catalog-000001"
            and item["revision"] == 5
        )
        parent_additions = {
            item["implementation_id"]: item
            for item in parent_catalog["implementation_additions"]
        }
        current_historical = {
            item["implementation_id"]: item
            for item in current_catalog["implementation_additions"]
            if item["implementation_id"] not in HOST_IDS
        }
        self.assertEqual(parent_additions, current_historical)
        self.assertEqual(
            HOST_IDS,
            {
                item["implementation_id"]
                for item in current_catalog["implementation_additions"]
            }
            - set(parent_additions),
        )
        for implementation_id in HOST_IDS:
            implementation = self.implementations[implementation_id]
            self.assertEqual("native-cpp", implementation["form"])
            self.assertEqual(["schuss-native-core"], implementation["provenance_sources"])
            self.assertEqual(2, len(implementation["target_availability"]))
            self.assertEqual("supported", implementation["target_availability"][0]["eligibility_status"])
            self.assertEqual("available", implementation["target_availability"][0]["provider_status"])
            self.assertEqual("no-binding-or-eligibility", implementation["target_availability"][1]["eligibility_status"])

    def test_collection_membership_counts_and_mutable_cohort_are_exact(self):
        collections = {
            item["object_collection_id"]: item
            for item in self.context.records["object_collections"]
        }
        self.assertEqual(
            {
                "schuss-object-collection-000001": 7,
                "schuss-object-collection-000002": 128,
                "schuss-object-collection-000003": 4,
                "schuss-object-collection-000004": 56,
            },
            {
                key: len(value["implementation_ids"])
                for key, value in collections.items()
            },
        )
        catalog = self.context.records["catalog"][0]
        mutable_ids = {
            item["implementation_id"]
            for item in catalog["mutable_instruments_review"]["implementation_tags"]
            if item["tag_id"] == "mutable-instruments-derived"
        }
        self.assertEqual(
            mutable_ids,
            set(collections["schuss-object-collection-000004"]["implementation_ids"]),
        )

    def test_duplicate_factory_and_ambiguous_binding_fail_distinctly(self):
        duplicate_factory = self._mutated()
        provider = duplicate_factory["implementation_providers"][0]
        provider["bindings"][1]["runtime_factory_id"] = provider["bindings"][0][
            "runtime_factory_id"
        ]
        self._rehash(provider, "implementation-provider-v0")
        self.assertIn("PROVIDER_FACTORY_DUPLICATE", self._codes(self._validate(duplicate_factory)))

        ambiguous = self._mutated()
        provider = ambiguous["implementation_providers"][0]
        claim = copy.deepcopy(provider["bindings"][0])
        claim["provider_binding_id"] = "provider-binding-000008"
        claim["runtime_factory_id"] = "schuss.rt.ambiguous-test-v0"
        provider["bindings"].append(claim)
        self._rehash(provider, "implementation-provider-v0")
        codes = self._codes(self._validate(ambiguous))
        self.assertIn("PROVIDER_BINDING_AMBIGUOUS", codes)
        self.assertNotIn("PROVIDER_FACTORY_DUPLICATE", codes)

    def test_missing_stale_source_and_unreviewed_provider_fail_distinctly(self):
        missing = self._mutated()
        missing["source_releases"] = [
            item
            for item in missing["source_releases"]
            if item["source_release_id"] != "schuss-source-release-000006"
        ]
        self.assertIn("PROVIDER_SOURCE_RELEASE_MISSING", self._codes(self._validate(missing)))

        stale = self._mutated()
        provider = stale["implementation_providers"][0]
        provider["source_release_reference"]["content_hash"] = "sha256:" + "f" * 64
        self._rehash(provider, "implementation-provider-v0")
        self.assertIn("PROVIDER_SOURCE_REFERENCE_STALE", self._codes(self._validate(stale)))

        license_unreviewed = self._mutated()
        provider = license_unreviewed["implementation_providers"][0]
        provider["license_boundary"]["private_development_status"] = "unreviewed"
        self._rehash(provider, "implementation-provider-v0")
        license_summary = self._validate(license_unreviewed)
        self.assertEqual("valid", license_summary["status"])
        self.assertIn("PROVIDER_LICENSE_UNREVIEWED", self._codes(license_summary))

    def test_read_operations_are_exact_and_deterministic(self):
        profile = self._profile()
        request = {
            "schema_version": "schuss-operation-request-v18",
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": "collections.inspect",
            "payload": {"profile": profile},
        }
        first = dispatch_operation(copy.deepcopy(request), self.context)
        second = dispatch_operation(copy.deepcopy(request), self.context)
        self.assertEqual("success", first["status"])
        self.assertEqual(
            canonical_result_bytes(first, self.context),
            canonical_result_bytes(second, self.context),
        )
        reordered_sets = copy.deepcopy(request)
        reordered_sets["payload"]["profile"][
            "installed_source_release_references"
        ].reverse()
        reordered_sets["payload"]["profile"]["installed_provider_references"].reverse()
        reordered_sets["payload"]["profile"]["collection_states"].reverse()
        equivalent = dispatch_operation(reordered_sets, self.context)
        self.assertEqual(
            canonical_result_bytes(first, self.context),
            canonical_result_bytes(equivalent, self.context),
        )
        self.assertEqual(4, len(first["value"]["collections"]))
        self.assertEqual("never", first["value"]["project_owned_source_view"]["collection_membership"])
        self.assertEqual("presentation-only", first["value"]["boundary_summary"]["collection_order_effect"])

        availability = dispatch_operation(
            self._availability_request(profile), self.context
        )
        self.assertEqual("success", availability["status"])
        self.assertEqual("available", availability["value"]["execution_availability"])
        self.assertEqual(
            "schuss.rt.saw-q27-v0",
            availability["value"]["selected_provider_binding"]["runtime_factory_id"],
        )
        self.assertFalse(availability["value"]["boundary_summary"]["fallback_attempted"])

    def test_unavailable_provider_missing_source_and_unsupported_target_do_not_fallback(self):
        provider_missing = dispatch_operation(
            self._availability_request(self._profile(installed_provider=False)),
            self.context,
        )
        self.assertEqual("unavailable", provider_missing["status"])
        self.assertIn("PROVIDER_UNAVAILABLE", self._codes(provider_missing))

        source_missing = dispatch_operation(
            self._availability_request(
                self._profile(
                    installed_sources={
                        item["source_release_id"]
                        for item in self.context.records["source_releases"]
                        if item["source_release_id"] != "schuss-source-release-000006"
                    }
                )
            ),
            self.context,
        )
        self.assertEqual("unavailable", source_missing["status"])
        self.assertIn("SOURCE_RELEASE_MISSING", self._codes(source_missing))

        unsupported = dispatch_operation(
            self._availability_request(self._profile(), pair_index=1), self.context
        )
        self.assertEqual("unsupported", unsupported["status"])
        self.assertIn("IMPLEMENTATION_TARGET_UNSUPPORTED", self._codes(unsupported))
        self.assertFalse(unsupported["value"]["boundary_summary"]["fallback_attempted"])

    def test_stale_profile_hash_and_distribution_license_fail_distinctly(self):
        stale_profile = self._profile()
        stale_profile["installed_provider_references"][0]["content_hash"] = (
            "sha256:" + "f" * 64
        )
        stale = dispatch_operation(
            self._availability_request(stale_profile), self.context
        )
        self.assertEqual("invalid", stale["status"])
        self.assertIn("PROFILE_PROVIDER_REFERENCE_STALE", self._codes(stale))

        distribution = dispatch_operation(
            self._availability_request(
                self._profile(use_context="distribution-review")
            ),
            self.context,
        )
        self.assertEqual("unavailable", distribution["status"])
        self.assertIn("PROVIDER_LICENSE_UNREVIEWED", self._codes(distribution))

    def test_disabled_and_reordered_collections_never_change_provider_or_graph(self):
        before_graphs = core.canonical_json(list(self.context.records["graphs"]))
        before_record_set = copy.deepcopy(self.context.record_set_reference)
        enabled_order = [
            item["object_collection_id"]
            for item in self.context.records["object_collections"]
        ]
        reversed_order = list(reversed(enabled_order))
        first_profile = self._profile(order=enabled_order)
        second_profile = self._profile(
            enabled={
                item
                for item in enabled_order
                if item != "schuss-object-collection-000001"
            },
            order=reversed_order,
        )
        first = dispatch_operation(
            self._availability_request(first_profile), self.context
        )
        second = dispatch_operation(
            self._availability_request(second_profile), self.context
        )
        self.assertEqual("success", second["status"])
        self.assertIn("COLLECTION_DISCOVERY_DISABLED", self._codes(second))
        self.assertEqual(
            first["value"]["selected_provider_binding"],
            second["value"]["selected_provider_binding"],
        )
        self.assertEqual(before_graphs, core.canonical_json(list(self.context.records["graphs"])))
        self.assertEqual(before_record_set, self.context.record_set_reference)

        listed = dispatch_operation(
            {
                "schema_version": "schuss-operation-request-v18",
                "canonical_profile": "schuss-canonical-json-v1",
                "operation": "collections.inspect",
                "payload": {"profile": second_profile},
            },
            self.context,
        )
        self.assertEqual(reversed_order, [item["collection"]["object_collection_id"] for item in listed["value"]["collections"]])

    def test_capability_v11_adds_only_two_read_only_operations(self):
        description = application_capabilities.build_application_description(
            record_set_reference=self.context.record_set_reference,
            schemas=self.context.schemas,
        )
        self.assertEqual(
            "schuss-application-capability-description-v11",
            description["description_version"],
        )
        self.assertEqual(47, len(description["operations"]))
        operations = {item["operation"]: item for item in description["operations"]}
        for operation in (
            "collections.inspect",
            "implementation.availability.inspect",
        ):
            self.assertEqual("read-only", operations[operation]["effect_class"])
            self.assertEqual("available", operations[operation]["availability"])
            self.assertEqual(
                "schuss-operation-request-v18",
                operations[operation]["request_schema_version"],
            )
        schema = self.context.schemas["application_capability_description_v11"]
        self.assertEqual([], core.schema_errors(description, schema, schema))

    def test_existing_client_allowlists_remain_closed(self):
        for path in (
            ROOT / "packages/schuss_core/mcp_server.py",
            ROOT / "packages/schuss_core/product_cli.py",
            ROOT / "apps/schuss_desktop/bridge/desktop_core_bridge.py",
            ROOT / "apps/schuss_desktop/src-tauri/src/desktop_bridge.rs",
        ):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn('"collections.inspect"', text, path)
            self.assertNotIn('"implementation.availability.inspect"', text, path)


if __name__ == "__main__":
    unittest.main()
