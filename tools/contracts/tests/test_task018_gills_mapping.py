from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/contracts")]

from packages.schuss_core import compiler_front_half as compiler  # noqa: E402
from packages.schuss_core.build_execution import handler_reference  # noqa: E402
from packages.schuss_core.control_plane import (  # noqa: E402
    dispatch_operation,
    load_repository_context,
)
from packages.schuss_core.gills_direct_frontend import (  # noqa: E402
    lower_gills_direct,
)
from packages.schuss_core.gills_mapped_backend import (  # noqa: E402
    REQUEST_REFERENCE,
    descriptor,
)
from packages.schuss_core.gills_mapped_frontend import (  # noqa: E402
    lower_gills_mapped,
)
from packages.schuss_core.gills_panel_runtime import (  # noqa: E402
    ADC_MAX,
    Q27_SCALE,
    evaluate_panel_update,
    host_vectors,
    PanelState,
    raw_to_q27,
)

import device_instrument_rules as device_rules  # noqa: E402
import generate_task018_records as generator  # noqa: E402
import gills_mapping_rules as gills_rules  # noqa: E402
import validator_core as core  # noqa: E402


RECORD_SET = ROOT / "contracts/record-sets/task018-full-gills-v1.json"
EVIDENCE = ROOT / "evidence/task018-completion-v1/validation-summary.json"
FIXTURES = ROOT / "tools/contracts/tests/fixtures/task018-gills-negative-fixtures.json"


class Task018GillsMappingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = load_repository_context(record_set_path=RECORD_SET)
        cls.instrument = next(
            value
            for value in cls.context.records["instruments"]
            if (value["instrument_id"], value["revision"])
            == ("schuss-instrument-000002", 2)
        )
        cls.request = next(
            value
            for value in cls.context.records["request"]
            if (value["build_request_id"], value["revision"])
            == ("schuss-build-request-000002", 4)
        )
        cls.graph = next(
            value
            for value in cls.context.records["graphs"]
            if value["graph_id"] == "schuss-graph-000002"
        )
        cls.runtime = next(
            value
            for value in cls.context.records["runtime_realizations"]
            if value["runtime_realization_id"]
            == "schuss-runtime-realization-000001"
        )
        cls.coverage = next(
            value
            for value in cls.context.records["mapping_coverage"]
            if value["coverage_report_id"] == "schuss-coverage-report-000001"
        )
        cls.plan_result = dispatch_operation(
            {
                "schema_version": "schuss-operation-request-v4",
                "canonical_profile": "schuss-canonical-json-v1",
                "operation": "build.plan",
                "payload": {"build_request_reference": REQUEST_REFERENCE},
            },
            cls.context,
        )

    def _gills_summary(
        self,
        *,
        coverages: list[dict] | None = None,
        runtimes: list[dict] | None = None,
    ) -> dict:
        groups = {
            "panel_evidence": copy.deepcopy(self.context.records["panel_evidence"]),
            "mapping_coverage": copy.deepcopy(
                coverages
                if coverages is not None
                else self.context.records["mapping_coverage"]
            ),
            "runtime_realizations": copy.deepcopy(
                runtimes
                if runtimes is not None
                else self.context.records["runtime_realizations"]
            ),
        }
        schemas = {
            "panel_evidence": self.context.schemas["panel_evidence"],
            "mapping_coverage": self.context.schemas["mapping_coverage"],
            "runtime_realizations": self.context.schemas["runtime_realizations"],
        }
        return gills_rules.validate_values(groups, schemas, self.context.records)

    def test_generated_successor_and_semantic_closure_are_valid(self) -> None:
        files, manifest, _ = generator.generated()
        files[RECORD_SET.relative_to(ROOT).as_posix()] = manifest
        self.assertTrue(
            all((ROOT / relative).read_bytes() == payload for relative, payload in files.items())
        )
        self.assertEqual("valid", self.context.task018_summary["status"])
        self.assertEqual("schuss-record-set-000012", self.context.record_set_reference["record_set_id"])
        self.assertEqual(
            ["passed", "passed"] + ["not-run"] * 6,
            [item["status"] for item in self.context.task018_summary["evidence_levels"]],
        )

    def test_complete_census_and_coverage_are_total(self) -> None:
        device = next(
            value
            for value in self.context.records["devices"]
            if (value["device_profile_id"], value["revision"])
            == ("schuss-device-profile-000001", 2)
        )
        slot_total = sum(
            len(device[collection])
            for collection in (
                "input_controls",
                "gestures",
                "feedback_outputs",
                "displays",
                "physical_io",
            )
        )
        self.assertEqual(63, slot_total)
        self.assertEqual(
            slot_total,
            len(self.context.records["panel_evidence"][0]["slot_evidence"]),
        )
        for coverage in self.context.records["mapping_coverage"]:
            self.assertEqual(slot_total, coverage["summary"]["device_slots_total"])
            self.assertEqual(
                slot_total, len(coverage["device_slot_coverage"])
            )
            self.assertFalse(coverage["summary"]["absence_is_coverage"])

    def test_all_exact_instruments_inspect_and_plan_without_fallback(self) -> None:
        expected = {
            ("schuss-instrument-000002", 2): "success",
            ("schuss-instrument-000003", 2): "success",
            ("schuss-instrument-000004", 2): "success",
        }
        for identity, status in expected.items():
            record = next(
                value
                for value in self.context.records["instruments"]
                if (value["instrument_id"], value["revision"]) == identity
            )
            reference = {
                key: record[key]
                for key in ("instrument_id", "revision", "content_hash")
            }
            result = dispatch_operation(
                {
                    "schema_version": "schuss-operation-request-v6",
                    "canonical_profile": "schuss-canonical-json-v1",
                    "operation": "gills.inspect",
                    "payload": {"instrument_reference": reference},
                },
                self.context,
            )
            self.assertEqual(status, result["status"])
            self.assertFalse(
                any(
                    item.get("handler", {}).get("fallback")
                    for item in result["value"]["runtime_realization"]["supported_builds"]
                )
            )
        self.assertEqual("success", self.plan_result["status"])

    def test_mapped_frontend_preserves_dsp_goldens_and_adds_panel_runtime(self) -> None:
        result = lower_gills_mapped(
            self.plan_result["value"],
            self.graph,
            self.context.records["contracts"],
            self.context.records["direct_operation_specs"],
            self.instrument,
            self.runtime,
            self.coverage,
            REQUEST_REFERENCE,
        )
        task016_context = load_repository_context(
            record_set_path=ROOT
            / "contracts/record-sets/task016-complete-gills-direct-v1.json"
        )
        task016_request = next(
            value
            for value in task016_context.records["request"]
            if (value["build_request_id"], value["revision"])
            == ("schuss-build-request-000002", 3)
        )
        task016_reference = {
            key: task016_request[key]
            for key in ("build_request_id", "revision", "content_hash")
        }
        task016_plan = dispatch_operation(
            {
                "schema_version": "schuss-operation-request-v4",
                "canonical_profile": "schuss-canonical-json-v1",
                "operation": "build.plan",
                "payload": {"build_request_reference": task016_reference},
            },
            task016_context,
        )["value"]
        direct = lower_gills_direct(
            task016_plan,
            self.graph,
            task016_context.records["contracts"],
            task016_context.records["direct_operation_specs"],
        )
        self.assertEqual(direct["semantic_goldens"], result["semantic_goldens"])
        for symbol in (
            "process_gills_panel",
            "initialize_gills_panel_hardware",
            "SchussOledWorkingArea",
            "adcvalues[adc_index[index]]",
            "palWritePad(GPIOG,6",
        ):
            self.assertIn(symbol, result["generated_cpp"]["text"])
        self.assertEqual(4, len(result["panel_runtime"]["paths"]))
        self.assertFalse(result["ambient_discovery_used"])

    def test_host_vectors_cover_transform_smoothing_pickup_gestures_and_display(self) -> None:
        vectors = host_vectors()
        self.assertEqual(0, raw_to_q27(0))
        self.assertEqual(Q27_SCALE, raw_to_q27(ADC_MAX))
        self.assertEqual(10, len(vectors["pot_endpoints"]))
        self.assertEqual(
            ["button-1-press", "button-1-hold", "button-1-release"],
            vectors["button_1_events"],
        )
        self.assertTrue(vectors["pickup_trace"][0]["pickup_armed"])
        self.assertFalse(vectors["pickup_trace"][-1]["pickup_armed"])
        self.assertEqual(
            [["encoder-turn-positive"], ["encoder-turn-negative"]],
            vectors["encoder_events"],
        )
        state, output = evaluate_panel_update(
            PanelState(), [0] * 10, [False] * 4, True, True, False
        )
        self.assertEqual("SCHUSS", output["display_lines"][0])
        self.assertTrue(state.pickup_armed)

    def test_exact_handler_and_retained_level5_evidence(self) -> None:
        value = descriptor()
        self.assertEqual(
            {"status": "supported", **handler_reference(value)},
            self.runtime["supported_builds"][0]["handler"],
        )
        summary = core.load_json(EVIDENCE)
        self.assertEqual("valid", summary["status"])
        self.assertEqual(2, summary["fresh_processes"])
        self.assertTrue(summary["artifact_bytes_identical"])
        self.assertEqual(
            ["passed"] * 5 + ["not-run"] * 3,
            [item["status"] for item in summary["evidence_levels"]],
        )
        self.assertFalse(summary["device_actions_performed"])
        self.assertFalse(summary["connected_device_validation_performed"])
        self.assertFalse(summary["real_time_validation_performed"])
        self.assertFalse(summary["audible_validation_performed"])

    def test_product_cli_selects_only_the_exact_mapped_handler(self) -> None:
        with tempfile.TemporaryDirectory(prefix="schuss-task018-cli-") as temporary:
            output = Path(temporary) / "published"
            completed = subprocess.run(
                [
                    str(ROOT / "bin/schuss"),
                    "build",
                    "execute",
                    "schuss-build-request-000002@4",
                    "--handler",
                    "schuss-build-handler-000003@1",
                    "--output-root",
                    str(output),
                    "--execute",
                    "--record-set",
                    str(RECORD_SET),
                    "--json",
                ],
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=300,
            )
            self.assertEqual(
                0, completed.returncode, completed.stderr.decode("utf-8")
            )
            value = json.loads(completed.stdout)["value"]
            self.assertEqual("success", value["status"])
            self.assertEqual(
                "schuss-build-handler-000003",
                value["handler_reference"]["build_handler_id"],
            )
            self.assertEqual(
                ["passed"] * 5 + ["not-run"] * 3,
                [item["status"] for item in value["evidence_levels"]],
            )

    def test_focused_negative_fixtures_fail_closed(self) -> None:
        fixtures = core.load_json(FIXTURES)
        observed: dict[str, set[str]] = {}

        coverage = copy.deepcopy(self.coverage)
        coverage["device_slot_coverage"].pop(0)
        coverage["content_hash"] = core.record_content_hash(
            coverage, self.context.schemas["mapping_coverage"]
        )
        summary = self._gills_summary(
            coverages=[
                coverage
                if item["coverage_report_id"] == coverage["coverage_report_id"]
                else copy.deepcopy(item)
                for item in self.context.records["mapping_coverage"]
            ]
        )
        observed["missing-device-slot-coverage"] = {
            item["code"] for item in summary["diagnostics"]
        }

        instrument = copy.deepcopy(self.instrument)
        instrument["device_input_mappings"][0]["destination"]["facet_id"] = "graph-facet-000001"
        direct_summary = device_rules.validate_contract_values(
            copy.deepcopy(self.context.records["devices"]),
            [instrument],
            self.context.schemas["device"],
            self.context.schemas["instrument"],
            {},
        )
        observed["direct-device-to-graph-shortcut"] = {
            item["code"] for item in direct_summary["diagnostics"]
        }

        runtime = copy.deepcopy(self.runtime)
        runtime["input_bindings"][0]["evidence_source_ids"] = [
            "panel-source-999999"
        ]
        runtime["content_hash"] = core.record_content_hash(
            runtime, self.context.schemas["runtime_realizations"]
        )
        summary = self._gills_summary(
            runtimes=[
                runtime
                if item["runtime_realization_id"]
                == runtime["runtime_realization_id"]
                else copy.deepcopy(item)
                for item in self.context.records["runtime_realizations"]
            ]
        )
        observed["unresolved-runtime-evidence"] = {
            item["code"] for item in summary["diagnostics"]
        }

        duplicate = copy.deepcopy(self.runtime)
        duplicate["runtime_realization_id"] = "schuss-runtime-realization-000003"
        duplicate["content_hash"] = core.record_content_hash(
            duplicate, self.context.schemas["runtime_realizations"]
        )
        records = {
            key: list(copy.deepcopy(values))
            for key, values in self.context.records.items()
        }
        records["runtime_realizations"].append(duplicate)
        compilation = compiler.CompilationContext.from_values(
            build_request_reference=REQUEST_REFERENCE,
            closure_source={
                "kind": "record-set",
                "record_set_reference": self.context.record_set_reference,
            },
            records=records,
            schemas=self.context.schemas,
        )
        ambiguous = compiler.plan_build(compilation)
        observed["ambiguous-runtime-selection"] = {
            item["code"] for item in ambiguous["diagnostics"]
        }

        for fixture in fixtures["cases"]:
            self.assertIn(
                fixture["expected_diagnostic"],
                observed[fixture["case_id"]],
                fixture["case_id"],
            )

    def test_parent_manifest_members_are_preserved_byte_exactly(self) -> None:
        parent = core.load_json(
            ROOT / "contracts/record-sets/task017-curated-core-v1.json"
        )
        successor = core.load_json(RECORD_SET)
        self.assertTrue(
            all(item in successor["schema_members"] for item in parent["schema_members"])
        )
        self.assertTrue(
            all(item in successor["record_members"] for item in parent["record_members"])
        )
        for item in parent["schema_members"] + parent["record_members"]:
            self.assertEqual(item["byte_sha256"], core.sha256_file(ROOT / item["portable_path"]))


if __name__ == "__main__":
    unittest.main()
