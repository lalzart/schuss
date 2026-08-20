from __future__ import annotations

import copy
import hashlib
import io
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools/contracts"
sys.path[:0] = [str(ROOT), str(TOOLS)]

from packages.schuss_core import application_capabilities as application  # noqa: E402
from packages.schuss_core import catalog_projection  # noqa: E402
from packages.schuss_core.cli import CATALOG_RECORD_SET_PATH, run as run_cli  # noqa: E402
from packages.schuss_core.control_plane import (  # noqa: E402
    canonical_result_bytes,
    dispatch_operation,
    load_repository_context,
)
from packages.schuss_core.product_cli import (  # noqa: E402
    application_describe_request,
    catalog_implementation_search_request,
    completion_script,
)

import generate_task030_records as generator  # noqa: E402
import generate_task030_cli_golden as cli_golden  # noqa: E402
import validator_core as core  # noqa: E402


RECORD_SET = ROOT / "contracts/record-sets/task030-complete-mutable-catalog-v1.json"
PARENT_SET = ROOT / "contracts/record-sets/task029-gills-machines-v1.json"
TASK027_REVIEW = ROOT / "contracts/task027/catalog-source-review.json"
TASK027_PACKET = ROOT / "catalog/reviews/task027-mutable-sources-v1/candidates.jsonl"
SUCCESSOR_REVIEW = ROOT / "contracts/task030/catalog-source-review-r2.json"
SUCCESSOR_PACKET = ROOT / "catalog/reviews/task030-mutable-catalog-v1/entries.jsonl"
TAG = "mutable-instruments-derived"


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Task030CompleteMutableCatalogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = load_repository_context(record_set_path=RECORD_SET)
        cls.parent = load_repository_context(record_set_path=PARENT_SET)
        cls.manifest = core.load_json(RECORD_SET)
        cls.parent_manifest = core.load_json(PARENT_SET)
        cls.parent_review = core.load_json(TASK027_REVIEW)
        cls.review = core.load_json(SUCCESSOR_REVIEW)
        cls.packet = core.load_jsonl(SUCCESSOR_PACKET)
        cls.corpus = core.load_json(ROOT / "contracts/task030/catalog-corpus-v5.json")
        cls.implementations = {
            value["implementation_id"]: (family, value)
            for family in cls.context.catalog_projection["families"]
            for value in family["implementations"]
        }

    def invoke(self, arguments: list[str]) -> tuple[int, bytes, str]:
        stdout = io.BytesIO()
        stderr = io.StringIO()
        code = run_cli(
            arguments,
            io.BytesIO(),
            stdout,
            stderr,
            load_repository_context,
        )
        return code, stdout.getvalue(), stderr.getvalue()

    def test_exact_parent_successor_and_additive_members_are_preserved(self) -> None:
        self.assertEqual("schuss-record-set-000023", self.manifest["record_set_id"])
        self.assertEqual(
            {
                "status": "included",
                **{
                    key: self.parent_manifest[key]
                    for key in ("record_set_id", "revision", "content_hash")
                },
            },
            self.manifest["parent_reference"],
        )
        self.assertTrue(
            all(
                item in self.manifest["schema_members"]
                for item in self.parent_manifest["schema_members"]
            )
        )
        self.assertTrue(
            all(
                item in self.manifest["record_members"]
                for item in self.parent_manifest["record_members"]
            )
        )
        self.assertEqual(
            (6, 3),
            (
                len(self.manifest["schema_members"])
                - len(self.parent_manifest["schema_members"]),
                len(self.manifest["record_members"])
                - len(self.parent_manifest["record_members"]),
            ),
        )

    def test_task027_review_packet_and_historical_cli_fixtures_are_immutable(self) -> None:
        self.assertEqual(
            "27ca21c54a04077fe458b461215c7437710818e8ab1e979035d80d2ffede0758",
            _digest(TASK027_REVIEW),
        )
        self.assertEqual(
            "0ec077ecee40b34af946abf5263ba64fa7809e9b2f1d8a781a5b1e8075b53e82",
            _digest(TASK027_PACKET),
        )
        self.assertEqual(
            "f4530b7e13e1275df11fdb17a99abaf70758547db36d1025e666cb1aa8c94ed4",
            _digest(ROOT / "tools/contracts/tests/fixtures/task011a-cli-golden-hashes.json"),
        )
        self.assertEqual(
            "3a27c68ae935c42d5ac17606ed68da6e74b5e722d1c2a5a274398905a96c7d62",
            _digest(ROOT / "tools/contracts/tests/fixtures/task023-cli-v2-golden-hashes.json"),
        )

    def test_successor_review_has_exact_census_and_identity_closure(self) -> None:
        self.assertEqual(72, len(self.review["entries"]))
        self.assertEqual(self.review["entries"], self.packet)
        self.assertEqual(
            [item["stable_source_id"] for item in self.parent_review["entries"]],
            [item["stable_source_id"] for item in self.review["entries"]],
        )
        self.assertEqual(
            {
                "total": 72,
                "extended": 19,
                "factory": 53,
                "tagged": 56,
                "inventory_only": 16,
                "catalogued_implementations": 56,
                "tagged_candidates": 0,
            },
            self.review["counts"],
        )
        tagged = [item for item in self.packet if TAG in item["provenance_tags"]]
        inventory_only = [
            item for item in self.packet if item["disposition"] == "inventory-only"
        ]
        self.assertEqual(56, len(tagged))
        self.assertTrue(all(item["catalog_implementation_id"] for item in tagged))
        self.assertEqual(16, len(inventory_only))
        self.assertTrue(
            all(item["catalog_implementation_id"] is None for item in inventory_only)
        )

    def test_exact_fifty_additions_and_family_allocation(self) -> None:
        additions = self.corpus["implementation_additions"]
        parent_additions = self.parent.records["catalog"][0]["implementation_additions"]
        new = [item for item in additions if item not in parent_additions]
        self.assertEqual(
            [f"schuss-implementation-{value:06d}" for value in range(112, 162)],
            [item["implementation_id"] for item in new],
        )
        parent_families = self.parent.records["catalog"][0]["family_additions"]
        new_families = [
            item for item in self.corpus["family_additions"] if item not in parent_families
        ]
        self.assertEqual(
            [f"schuss-family-{value:06d}" for value in range(61, 108)],
            [item["family_id"] for item in new_families],
        )
        assigned = {
            item["catalog_implementation_id"]
            for item in self.packet
            if item["disposition"] == "catalogued-new-implementation"
            and int(item["catalog_implementation_id"].rsplit("-", 1)[-1]) >= 112
        }
        self.assertEqual({item["implementation_id"] for item in new}, assigned)

    def test_projection_counts_and_all_mutable_objects_are_exact(self) -> None:
        projection = self.context.catalog_projection
        self.assertEqual("catalog-projection-v5", projection["schema_version"])
        self.assertEqual(107, len(projection["families"]))
        self.assertEqual(133, len(self.implementations))
        tagged = {
            identifier
            for identifier, (_, item) in self.implementations.items()
            if TAG in item["provenance_tags"]
        }
        expected = {
            item["catalog_implementation_id"]
            for item in self.packet
            if TAG in item["provenance_tags"]
        }
        self.assertEqual(expected, tagged)
        self.assertEqual(56, len(tagged))

    def test_new_objects_are_catalogued_only_and_have_no_support_evidence(self) -> None:
        empty_fields = (
            "contract_references",
            "binding_references",
            "eligibility_references",
            "result_references",
            "artifact_references",
            "evidence_references",
        )
        for value in range(112, 162):
            identifier = f"schuss-implementation-{value:06d}"
            family, implementation = self.implementations[identifier]
            with self.subTest(identifier=identifier):
                self.assertIsNotNone(implementation["exact_reference"])
                self.assertEqual(
                    ["catalogued-only", "unresolved"],
                    implementation["readiness_states"],
                )
                self.assertEqual([TAG], implementation["provenance_tags"])
                self.assertEqual(
                    {"family_id", "revision", "content_hash"},
                    set(family["family_reference"]),
                )
                for field in empty_fields:
                    self.assertEqual([], implementation[field])

    def test_retained_failures_are_not_promoted(self) -> None:
        macro = next(
            item
            for item in self.packet
            if item["stable_source_id"].endswith("synthesis.macro-voice")
        )
        warps = next(
            item
            for item in self.packet
            if item["stable_source_id"].startswith("axoloti-factory:fx/wrps/wrps@")
        )
        self.assertEqual("h7-recommended", macro["source_manifest_metadata"]["tier"])
        self.assertEqual(
            "build-failed", macro["source_manifest_metadata"]["build_status"]
        )
        self.assertTrue(
            any("will not currently link" in value for value in warps["known_source_limitations"])
        )
        boundary = (
            ROOT / "contracts/task025/reverb-allocation-boundary.md"
        ).read_text(encoding="utf-8")
        self.assertIn("stays deterministically unsupported", boundary)

    def test_shared_implementation_search_is_exact_and_per_object(self) -> None:
        request = catalog_implementation_search_request("", {"provenance": [TAG]})
        first = dispatch_operation(copy.deepcopy(request), self.context)
        second = dispatch_operation(copy.deepcopy(request), self.context)
        self.assertEqual(first, second)
        self.assertEqual("success", first["status"])
        self.assertEqual(56, first["value"]["total_matches"])
        ids = [item["implementation_id"] for item in first["value"]["results"]]
        self.assertEqual(56, len(ids))
        self.assertEqual(56, len(set(ids)))
        self.assertTrue(all(item["provenance_tags"] == [TAG] for item in first["value"]["results"]))
        resonators = [
            item
            for item in first["value"]["results"]
            if item["family_reference"]["family_id"] == "schuss-family-000010"
        ]
        self.assertEqual(4, len(resonators))
        self.assertNotIn("schuss-implementation-000015", {item["implementation_id"] for item in resonators})

    def test_closed_filters_and_schema_drift_fail_closed(self) -> None:
        invalid_filter = dispatch_operation(
            catalog_implementation_search_request(
                "", {"provenance": ["mutable-by-name-only"]}
            ),
            self.context,
        )
        self.assertEqual("invalid", invalid_filter["status"])
        self.assertEqual(
            "CATALOG_FILTER_VALUE_UNSUPPORTED",
            invalid_filter["diagnostics"][0]["code"],
        )
        malformed = catalog_implementation_search_request("", {})
        malformed["payload"]["unknown"] = True
        result = dispatch_operation(malformed, self.context)
        self.assertEqual("invalid", result["status"])
        self.assertEqual("OPERATION_REQUEST_INVALID", result["diagnostics"][0]["code"])
        unavailable = dispatch_operation(
            catalog_implementation_search_request("", {}), self.parent
        )
        self.assertEqual("invalid", unavailable["status"])
        self.assertEqual("OPERATION_REQUEST_INVALID", unavailable["diagnostics"][0]["code"])

    def test_stale_successor_source_mapping_fails_closed(self) -> None:
        corpus = copy.deepcopy(self.corpus)
        corpus["mutable_instruments_review"]["implementation_tags"][-1][
            "source_entry_id"
        ] = "factory:absent"
        schema = self.context.schemas["catalog_corpus"]
        corpus["content_hash"] = core.record_content_hash(corpus, schema)
        with self.assertRaisesRegex(
            catalog_projection.CatalogProjectionError, "source entry is absent"
        ):
            catalog_projection.build_catalog_projection(
                corpus=corpus,
                corpus_schema=schema,
                projection_schema=self.context.schemas["catalog_projection"],
                overlay=copy.deepcopy(self.context.overlay),
                overlay_sha256=self.context.overlay_sha256,
                observations=copy.deepcopy(self.context.observations),
                records=self.context.records,
                record_set_reference=copy.deepcopy(self.context.record_set_reference),
                core=core,
            )

    def test_cli_defaults_dispatches_once_and_json_matches_api(self) -> None:
        request = catalog_implementation_search_request("", {"provenance": [TAG]})
        expected = canonical_result_bytes(
            dispatch_operation(copy.deepcopy(request), self.context), self.context
        ) + b"\n"
        loaded: list[Path] = []
        requests: list[dict[str, object]] = []

        def loader(**kwargs):
            loaded.append(kwargs["record_set_path"])
            return self.context

        def counted(value, context, **services):
            requests.append(copy.deepcopy(value))
            return dispatch_operation(value, context, **services)

        stdout = io.BytesIO()
        stderr = io.StringIO()
        with mock.patch(
            "packages.schuss_core.cli.dispatch_operation", side_effect=counted
        ):
            code = run_cli(
                ["catalog", "objects", "--provenance", TAG, "--json"],
                io.BytesIO(),
                stdout,
                stderr,
                loader,
            )
        self.assertEqual((0, ""), (code, stderr.getvalue()))
        self.assertEqual([CATALOG_RECORD_SET_PATH.resolve()], loaded)
        self.assertEqual(["catalog.implementations.search"], [item["operation"] for item in requests])
        self.assertEqual(expected, stdout.getvalue())

    def test_cli_human_help_completion_and_application_capability_v3(self) -> None:
        code, human, error = self.invoke(
            ["catalog", "objects", "macro", "--provenance", TAG]
        )
        self.assertEqual((0, ""), (code, error))
        self.assertIn(b"record_set: schuss-record-set-000023@1", human)
        self.assertIn(b"implementation_id: schuss-implementation-000113", human)
        self.assertIn(b"provenance_tags:\n      - mutable-instruments-derived", human)
        for arguments, token in (
            (["--help"], b"Schuss CLI v3"),
            (["catalog", "--help"], b"objects"),
            (["catalog", "objects", "--help"], b"--provenance"),
        ):
            code, output, error = self.invoke(arguments)
            self.assertEqual((0, ""), (code, error))
            self.assertIn(token, output)
            self.assertLessEqual(max(map(len, output.splitlines())), 80)
        for shell, command in (("bash", ["bash", "-n"]), ("zsh", ["zsh", "-n"])):
            script = completion_script(shell)
            self.assertIn(b"objects", script)
            completed = subprocess.run(
                command,
                input=script,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
        request = application_describe_request()
        described = dispatch_operation(request, self.context)
        self.assertEqual("success", described["status"])
        self.assertEqual(
            "application-capability-description-v3",
            described["value"]["schema_version"],
        )
        names = [item["operation"] for item in described["value"]["operations"]]
        self.assertEqual(list(application.EXPECTED_OPERATIONS_V3), names)
        self.assertEqual(20, len(names))
        self.assertIn("catalog.implementations.search", names)

    def test_generation_is_fresh_deterministic_and_portable(self) -> None:
        first_files, first_manifest, first_summary, first_projection = generator.generated()
        second_files, second_manifest, second_summary, second_projection = generator.generated()
        self.assertEqual(first_files, second_files)
        self.assertEqual(first_manifest, second_manifest)
        self.assertEqual(first_summary, second_summary)
        self.assertEqual(first_projection, second_projection)
        expected = {**first_files, RECORD_SET.relative_to(ROOT).as_posix(): first_manifest}
        for path, data in expected.items():
            self.assertEqual(data, (ROOT / path).read_bytes(), path)
            self.assertNotIn(b"/Users/", data, path)
        self.assertEqual(
            first_summary["projection_sha256"],
            hashlib.sha256(generator._canonical_bytes(first_projection)).hexdigest(),
        )
        self.assertEqual(
            ["passed", "passed"] + ["not-run"] * 6,
            [item["status"] for item in first_summary["evidence_levels"]],
        )
        self.assertFalse(first_summary["compiler_or_build_performed"])
        self.assertFalse(first_summary["project_or_machine_mutation_performed"])
        self.assertFalse(first_summary["hardware_or_publication_performed"])
        expected_golden = (
            core.canonical_json(cli_golden.generated()).encode("utf-8") + b"\n"
        )
        self.assertEqual(expected_golden, cli_golden.FIXTURE.read_bytes())

    def test_historical_aggregate_report_is_immutable_not_a_current_gate(self) -> None:
        report_path = ROOT / "evidence/task030-completion-v1/final-aggregate-result.json"
        self.assertEqual(
            "d07aecd148412d5445b70fbed3a5cd9ff0c51633c7e0a63a329f986c35f5bac7",
            hashlib.sha256(report_path.read_bytes()).hexdigest(),
        )
        result = core.load_json(
            report_path
        )
        self.assertEqual(
            "task030-valid-repository-aggregate-not-green", result["status"]
        )
        self.assertEqual((394, 3, 0), (
            result["test_count"],
            result["failure_count"],
            result["task030_failure_count"],
        ))
        self.assertEqual(5, result["unique_retained_output_mismatch_count"])
        self.assertEqual(
            {
                "pre-existing-historical-task023-input-closure-gate",
                "pre-existing-task027-retained-projection-hash-gate",
            },
            {item["classification"] for item in result["failures"]},
        )
        self.assertFalse(result["historical_goldens_updated"])
        self.assertFalse(result["local_source_mapping_changed"])


if __name__ == "__main__":
    unittest.main()
