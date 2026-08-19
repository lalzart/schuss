from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools/contracts"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import aggregate_validator as aggregate  # noqa: E402
import performance_control_rules as performance  # noqa: E402
import record_set_rules  # noqa: E402
import validator_core as core  # noqa: E402
from packages.schuss_core import application_capabilities  # noqa: E402
from packages.schuss_core.control_plane import (  # noqa: E402
    canonical_result_bytes,
    dispatch_operation,
    load_repository_context,
)


RECORD_SET = Path("contracts/record-sets/task034-performance-control-v1.json")


class Task034PerformanceControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.selected = record_set_rules.load_record_set(ROOT, RECORD_SET)
        cls.component = aggregate._component_record_set_validation(cls.selected, ROOT)
        cls.context = load_repository_context(record_set_path=RECORD_SET)
        cls.schemas = {
            version: cls.selected.schemas[version]
            for version in performance.SCHEMA_VERSIONS.values()
        }
        cls.base_records = {
            "instruments_v0": [
                record
                for record in cls.selected.records["instrument"]
                if record["schema_version"] == "instrument-v0"
            ],
            "instruments_v1": [
                record
                for record in cls.selected.records["instrument"]
                if record["schema_version"] == "instrument-v1"
            ],
            "dsp_graphs": list(cls.selected.records["dsp-graph"]),
            "devices": list(cls.selected.records["device-profile"]),
            "performance_control_contracts": list(
                cls.selected.records["performance-control-contract"]
            ),
            "performance_control_graphs": list(
                cls.selected.records["performance-control-graph"]
            ),
            "performance_configurations": list(
                cls.selected.records["performance-configuration"]
            ),
        }

    def _validate(self, records: dict[str, list[dict[str, object]]]):
        return performance.validate_values(
            records, self.schemas, self.component.graph_targets
        )

    def _mutated(self):
        return copy.deepcopy(self.base_records)

    def _rehash(self, record: dict[str, object], schema_version: str) -> None:
        record["content_hash"] = "sha256:" + "0" * 64
        record["content_hash"] = core.record_content_hash(
            record, self.schemas[schema_version]
        )

    @staticmethod
    def _codes(summary: dict[str, object]) -> set[str]:
        return {item["code"] for item in summary["diagnostics"]}

    def test_exact_record_set_allocation_and_generation_are_fresh(self) -> None:
        self.assertEqual("schuss-record-set-000030", self.selected.reference["record_set_id"])
        self.assertEqual(
            {
                "record_set_id": "schuss-record-set-000029",
                "revision": 1,
                "content_hash": "sha256:8d6d8e5b0c3a90862f1e7c9ddab9c054a7b5908f268db9fa356c131bdc37c55c",
                "status": "included",
            },
            self.selected.manifest["parent_reference"],
        )
        run = subprocess.run(
            [sys.executable, "tools/contracts/generate_task034_records.py", "--check"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(0, run.returncode, run.stderr)

    def test_complete_semantic_closure_is_valid(self) -> None:
        summary = self._validate(self._mutated())
        self.assertEqual("valid", summary["status"])
        self.assertEqual([], summary["diagnostics"])
        self.assertEqual(
            {
                "instrument_v1": 1,
                "performance_control_contracts": 2,
                "performance_control_graphs": 1,
                "performance_configurations": 2,
            },
            summary["record_counts"],
        )
        self.assertEqual(
            [
                {"level": "structural-schema-and-reference", "status": "passed"},
                {"level": "control-graph-execution", "status": "not-run"},
                {"level": "backend-lowering", "status": "not-run"},
                {"level": "native-build", "status": "not-run"},
                {"level": "physical-controller", "status": "not-run"},
                {"level": "real-time-resource", "status": "not-run"},
                {"level": "audible-listening", "status": "not-run"},
            ],
            summary["evidence_levels"],
        )

    def test_instrument_successor_moves_only_device_ownership(self) -> None:
        predecessor = next(
            item
            for item in self.base_records["instruments_v0"]
            if item["instrument_id"] == "schuss-instrument-000005"
            and item["revision"] == 1
        )
        successor = self.base_records["instruments_v1"][0]
        self.assertEqual("schuss-instrument-000005", successor["instrument_id"])
        self.assertEqual(2, successor["revision"])
        self.assertEqual(
            {
                "status": "successor",
                "predecessor_reference": {
                    "instrument_id": predecessor["instrument_id"],
                    "revision": predecessor["revision"],
                    "content_hash": predecessor["content_hash"],
                },
            },
            successor["lineage"],
        )
        for field in (
            "display_name",
            "graph_reference",
            "parameters",
            "actions",
            "displays",
            "state_declarations",
            "graph_mappings",
        ):
            self.assertEqual(predecessor[field], successor[field], field)
        self.assertEqual([], successor["event_inputs"])
        serialized = core.canonical_json(successor)
        for forbidden in (
            "device_profile_reference",
            "device_input_mappings",
            "device_feedback_mappings",
            "schuss-device-profile-",
        ):
            self.assertNotIn(forbidden, serialized)

    def test_same_instrument_and_graph_have_gills_and_midi_presentations(self) -> None:
        configurations = self.base_records["performance_configurations"]
        self.assertEqual(2, len(configurations))
        self.assertEqual(
            1, len({core.canonical_json(item["instrument_reference"]) for item in configurations})
        )
        self.assertEqual(
            1,
            len(
                {
                    core.canonical_json(item["performance_control_graph_reference"])
                    for item in configurations
                }
            ),
        )
        self.assertEqual(
            {"device-profile", "midi"},
            {item["controller_sources"][0]["source_kind"] for item in configurations},
        )
        midi = next(
            item
            for item in configurations
            if item["controller_sources"][0]["source_kind"] == "midi"
        )
        serialized = core.canonical_json(midi)
        self.assertNotIn("juce", serialized.lower())
        self.assertNotIn("endpoint_name", serialized)
        self.assertNotIn("device_profile_reference", serialized)

    def test_control_graph_and_contracts_have_no_adjacent_layer_identity(self) -> None:
        values = [
            *self.base_records["performance_control_contracts"],
            *self.base_records["performance_control_graphs"],
        ]
        serialized = core.canonical_json(values)
        for forbidden in (
            "schuss-device-profile-",
            "device-input-",
            "schuss-instrument-",
            "schuss-graph-",
            "graph-node-",
            "schuss-backend-",
            "schuss.rt.",
            "juce",
        ):
            self.assertNotIn(forbidden, serialized.lower())

    def test_unknown_connection_endpoint_fails_closed(self) -> None:
        records = self._mutated()
        graph = records["performance_control_graphs"][0]
        graph["connections"][0]["source"]["facet_id"] = "performance-control-input-999999"
        self._rehash(graph, "performance-control-graph-v0")
        summary = self._validate(records)
        self.assertIn("PERFORMANCE_CONTROL_SOURCE_UNKNOWN", self._codes(summary))

    def test_multiple_driver_fails_closed(self) -> None:
        records = self._mutated()
        graph = records["performance_control_graphs"][0]
        duplicate = copy.deepcopy(graph["connections"][0])
        duplicate["connection_id"] = "performance-control-connection-000005"
        graph["connections"].append(duplicate)
        self._rehash(graph, "performance-control-graph-v0")
        summary = self._validate(records)
        self.assertIn("PERFORMANCE_CONTROL_MULTIPLE_DRIVERS", self._codes(summary))

    def test_control_cycle_fails_closed(self) -> None:
        records = self._mutated()
        graph = records["performance_control_graphs"][0]
        graph["connections"][0]["source"] = {
            "endpoint_kind": "node-output",
            "node_id": "performance-control-node-000002",
            "facet_id": "performance-control-port-000002",
        }
        graph["connections"][2]["source"] = {
            "endpoint_kind": "node-output",
            "node_id": "performance-control-node-000001",
            "facet_id": "performance-control-port-000002",
        }
        self._rehash(graph, "performance-control-graph-v0")
        summary = self._validate(records)
        self.assertIn("PERFORMANCE_CONTROL_CYCLE_UNSUPPORTED", self._codes(summary))

    def test_type_mismatch_fails_closed(self) -> None:
        records = self._mutated()
        graph = records["performance_control_graphs"][0]
        graph["public_inputs"][0]["shape"] = {"value_kind": "boolean"}
        self._rehash(graph, "performance-control-graph-v0")
        summary = self._validate(records)
        self.assertIn("PERFORMANCE_CONTROL_TYPE_MISMATCH", self._codes(summary))

    def test_unknown_gills_slot_fails_closed(self) -> None:
        records = self._mutated()
        configuration = next(
            item
            for item in records["performance_configurations"]
            if item["controller_sources"][0]["source_kind"] == "device-profile"
        )
        configuration["controller_sources"][0]["bindings"][0]["selector"][
            "slot_id"
        ] = "device-input-999999"
        self._rehash(configuration, "performance-configuration-v0")
        summary = self._validate(records)
        self.assertIn("PERFORMANCE_CONTROLLER_SELECTOR_UNKNOWN", self._codes(summary))

    def test_invalid_midi_range_fails_schema(self) -> None:
        records = self._mutated()
        configuration = next(
            item
            for item in records["performance_configurations"]
            if item["controller_sources"][0]["source_kind"] == "midi"
        )
        configuration["controller_sources"][0]["bindings"][0]["selector"][
            "controller_number"
        ] = 128
        summary = self._validate(records)
        self.assertIn("PERFORMANCE_MIDI_SELECTOR_OUT_OF_RANGE", self._codes(summary))

    def test_stale_exact_configuration_reference_fails_closed(self) -> None:
        records = self._mutated()
        configuration = records["performance_configurations"][0]
        configuration["performance_control_graph_reference"]["content_hash"] = (
            "sha256:" + "f" * 64
        )
        self._rehash(configuration, "performance-configuration-v0")
        summary = self._validate(records)
        self.assertIn("PERFORMANCE_CONFIGURATION_GRAPH_UNRESOLVED", self._codes(summary))

    def test_control_layer_identity_leak_fails_closed(self) -> None:
        records = self._mutated()
        contract = records["performance_control_contracts"][0]
        contract["display_name"] = "schuss-device-profile-000001"
        self._rehash(contract, "performance-control-contract-v0")
        summary = self._validate(records)
        self.assertIn("PERFORMANCE_CONTROL_LAYER_LEAKAGE", self._codes(summary))

    def test_dsp_shortcut_field_is_rejected(self) -> None:
        records = self._mutated()
        configuration = records["performance_configurations"][0]
        configuration["dsp_node_id"] = "graph-node-000001"
        summary = self._validate(records)
        self.assertIn("PERFORMANCE_SCHEMA_STRUCTURE_INVALID", self._codes(summary))

    def test_inspect_operation_is_exact_complete_and_deterministic(self) -> None:
        configuration = self.context.records["performance_configurations"][0]
        reference = {
            key: configuration[key]
            for key in (
                "performance_configuration_id",
                "revision",
                "content_hash",
            )
        }
        request = {
            "schema_version": "schuss-operation-request-v17",
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": "performance.inspect",
            "payload": {"performance_configuration_reference": reference},
        }
        first = dispatch_operation(copy.deepcopy(request), self.context)
        second = dispatch_operation(copy.deepcopy(request), self.context)
        first_bytes = canonical_result_bytes(first, self.context)
        self.assertEqual(first_bytes, canonical_result_bytes(second, self.context))
        self.assertEqual("success", first["status"])
        value = first["value"]
        self.assertEqual(configuration, value["configuration"])
        self.assertEqual("instrument-v1", value["instrument"]["schema_version"])
        self.assertEqual("dsp-graph-v0", value["dsp_graph"]["schema_version"])
        self.assertEqual("not-run", value["boundary_summary"]["control_graph_execution"])
        self.assertEqual("valid", value["validation_summary"]["status"])
        self.assertEqual(
            hashlib.sha256(first_bytes).hexdigest(),
            hashlib.sha256(canonical_result_bytes(second, self.context)).hexdigest(),
        )

    def test_invalid_inspect_request_is_structured(self) -> None:
        result = dispatch_operation(
            {
                "schema_version": "schuss-operation-request-v17",
                "canonical_profile": "schuss-canonical-json-v1",
                "operation": "performance.inspect",
                "payload": {},
            },
            self.context,
        )
        self.assertEqual("invalid", result["status"])
        self.assertEqual("OPERATION_REQUEST_INVALID", result["diagnostics"][0]["code"])
        canonical_result_bytes(result, self.context)

    def test_capability_v10_adds_one_read_only_operation(self) -> None:
        description = application_capabilities.build_application_description(
            record_set_reference=self.context.record_set_reference,
            schemas=self.context.schemas,
        )
        self.assertEqual(
            "schuss-application-capability-description-v10",
            description["description_version"],
        )
        self.assertEqual(45, len(description["operations"]))
        operation = next(
            item
            for item in description["operations"]
            if item["operation"] == "performance.inspect"
        )
        self.assertEqual("read-only", operation["effect_class"])
        self.assertEqual("available", operation["availability"])
        schema = self.context.schemas["application_capability_description_v10"]
        self.assertEqual([], core.schema_errors(description, schema, schema))

    def test_v0_domain_and_aggregate_boundaries_remain_valid(self) -> None:
        self.assertEqual(10, len(self.context.records["instruments"]))
        self.assertEqual(1, len(self.context.records["performance_instruments"]))
        self.assertEqual("valid-with-deferred-graph", self.context.device_summary["status"])
        aggregate_summary = aggregate.validate_all_record_set(self.selected, ROOT)
        parent = record_set_rules.load_record_set(
            ROOT,
            Path("contracts/record-sets/task032-variable-host-runtime-v1.json"),
        )
        self.assertEqual(
            aggregate.validate_all_record_set(parent, ROOT), aggregate_summary
        )


if __name__ == "__main__":
    unittest.main()
