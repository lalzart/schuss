#!/usr/bin/env python3
"""Focused positive and negative Task 011B closure tests."""

from __future__ import annotations

import copy
import os
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools/contracts"))

import component_graph_rules as component  # noqa: E402
import record_set_rules  # noqa: E402
import task011b_rules as task011b  # noqa: E402
import validator_core as core  # noqa: E402
from packages.schuss_core.control_plane import (  # noqa: E402
    canonical_result_bytes,
    dispatch_operation,
    load_repository_context,
)


MANIFEST = Path("contracts/record-sets/task011b-vertical-slice-v1.json")
FIXTURES = ROOT / "tools/contracts/tests/fixtures/task011b-vertical-slice-fixtures.json"


class Task011BTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.selected = record_set_rules.load_record_set(
            ROOT,
            MANIFEST,
            accepted_manifest_path=task011b.PARENT_PATH,
        )
        cls.context = load_repository_context(ROOT, record_set_path=MANIFEST)
        cls.fixtures = core.load_json(FIXTURES)
        cls.graph = next(
            item
            for item in cls.context.records["graphs"]
            if item["graph_id"] == task011b.GRAPH_ID
        )
        cls.contracts = {
            item["component_contract_id"]: item
            for item in cls.context.records["contracts"]
        }

    def test_positive_validator_and_fail_closed_resolution(self):
        summary = task011b.validate_task011b(ROOT, MANIFEST)
        expected = self.fixtures["positive"]
        self.assertEqual("valid", summary["status"])
        self.assertEqual(expected["node_count"], summary["graph"]["nodes"])
        self.assertEqual(
            expected["connection_count"], summary["graph"]["connections"]
        )
        self.assertEqual(
            expected["contract_closure_count"],
            summary["graph"]["contract_closure"],
        )
        self.assertEqual(
            expected["build_status"], summary["build_resolution"]["status"]
        )
        self.assertIsNone(summary["build_resolution"]["backend_invocation"])
        self.assertEqual(
            expected["selected_nodes"],
            sorted(
                node
                for node, status in summary["build_resolution"][
                    "trace_status"
                ].items()
                if status == "selected"
            ),
        )

    def test_generation_is_current(self):
        completed = subprocess.run(
            [sys.executable, "tools/contracts/generate_task011b_records.py", "--check"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn('"changed":0', completed.stdout)

    def test_process_environment_and_record_order_are_deterministic(self):
        command = [sys.executable, str(ROOT / "tools/contracts/validate_task011b.py")]
        outputs = []
        for cwd, seed in ((ROOT, "1"), (Path("/tmp"), "73")):
            environment = dict(os.environ)
            environment.update({"LC_ALL": "C", "LANG": "C", "PYTHONHASHSEED": seed})
            outputs.append(
                subprocess.check_output(command, cwd=cwd, env=environment)
            )
        self.assertEqual(outputs[0], outputs[1])

        reversed_context = self.context.with_records(
            **{
                name: reversed(values)
                for name, values in self.context.records.items()
            }
        )
        graph_reference = {
            "graph_id": self.graph["graph_id"],
            "revision": self.graph["revision"],
            "content_hash": self.graph["content_hash"],
        }
        for context in (self.context, reversed_context):
            result = dispatch_operation(
                {
                    "schema_version": "schuss-operation-request-v1",
                    "canonical_profile": "schuss-canonical-json-v1",
                    "operation": "graph.inspect",
                    "payload": {"graph_reference": graph_reference},
                },
                context,
            )
            outputs.append(canonical_result_bytes(result, context))
        self.assertEqual(outputs[-2], outputs[-1])

    def _shape_codes(
        self,
        graph: dict | None = None,
        contracts: dict[str, dict] | None = None,
    ) -> set[str]:
        return {
            item.code
            for item in task011b.validate_graph_shape(
                copy.deepcopy(self.graph if graph is None else graph),
                copy.deepcopy(self.contracts if contracts is None else contracts),
            )
        }

    def test_topology_mutation_is_rejected(self):
        graph = copy.deepcopy(self.graph)
        graph["connections"].pop()
        self.assertIn(
            "TASK011B_TOPOLOGY_CONNECTION_SET_MISMATCH", self._shape_codes(graph)
        )

    def test_reviewed_fixed_value_mutation_is_rejected(self):
        graph = copy.deepcopy(self.graph)
        node = next(
            item for item in graph["nodes"] if item["node_id"] == "graph-node-000002"
        )
        node["parameter_values"][0]["value"] = "5"
        self.assertIn("TASK011B_FIXED_VALUES_MISMATCH", self._shape_codes(graph))

    def test_behavior_mutation_is_rejected(self):
        contracts = copy.deepcopy(self.contracts)
        lfo = contracts[task011b.CONTRACT_IDS["lfo"]]
        lfo["behavior_rules"] = [
            item
            for item in lfo["behavior_rules"]
            if item["kind"] != "edge-triggered-transition"
        ]
        self.assertIn(
            "TASK011B_BEHAVIOR_RULE_SET_MISMATCH",
            self._shape_codes(contracts=contracts),
        )

    def test_clock_transport_mutation_requires_visible_adapter(self):
        contracts = copy.deepcopy(self.contracts)
        counter = contracts[task011b.CONTRACT_IDS["counter"]]
        trigger = next(
            item
            for item in counter["ports"]
            if item["facet_id"] == "component-port-000001"
        )
        trigger["port_type"]["semantic_role"] = "trigger"
        self.assertIn(
            "TASK011B_CLOCK_ADAPTER_REQUIRED",
            self._shape_codes(contracts=contracts),
        )

    def test_low_pass_fanout_mutation_requires_visible_adapter(self):
        contracts = copy.deepcopy(self.contracts)
        filter_contract = contracts[task011b.CONTRACT_IDS["filter"]]
        low_pass = next(
            item
            for item in filter_contract["ports"]
            if item["facet_id"] == "component-port-000006"
        )
        low_pass["port_type"]["cardinality"]["maximum_connections"] = 1
        self.assertIn(
            "TASK011B_MONO_STEREO_ADAPTER_REQUIRED",
            self._shape_codes(contracts=contracts),
        )

    def _component_result(self, graph: dict) -> component.CoreValidation:
        graph = copy.deepcopy(graph)
        graph["content_hash"] = core.record_content_hash(
            graph, self.context.schemas["graph"]
        )
        family_refs = [
            copy.deepcopy(item["family_reference"])
            for item in self.context.catalog_projection["families"]
        ]
        corpus = self.context.records["catalog"][0]
        return component.validate_component_graph_values(
            list(copy.deepcopy(self.context.records["families"])),
            list(copy.deepcopy(self.context.records["contracts"])),
            list(copy.deepcopy(self.context.records["bindings"])),
            [
                copy.deepcopy(item)
                for item in self.context.records["graphs"]
                if item["graph_id"] != task011b.GRAPH_ID
            ]
            + [graph],
            {
                key: copy.deepcopy(self.context.schemas[key])
                for key in (
                    "family",
                    "contract",
                    "contract_versions",
                    "binding",
                    "binding_versions",
                    "graph",
                )
            },
            copy.deepcopy(self.context.overlay),
            self.context.overlay_sha256,
            self.context.manifest_sha256,
            copy.deepcopy(dict(self.context.observations)),
            additional_family_references=family_refs,
            additional_implementations=copy.deepcopy(
                corpus["implementation_additions"]
            ),
        )

    def test_out_of_range_fixed_value_fails_shared_validator(self):
        graph = copy.deepcopy(self.graph)
        node = next(
            item for item in graph["nodes"] if item["node_id"] == "graph-node-000002"
        )
        node["parameter_values"][0]["value"] = "70000"
        codes = {item.code for item in self._component_result(graph).diagnostics}
        self.assertIn("GRAPH_FIXED_VALUE_OUT_OF_RANGE", codes)

    def test_implicit_boolean_integer_conversion_fails_shared_validator(self):
        graph = copy.deepcopy(self.graph)
        first = next(
            item
            for item in graph["connections"]
            if item["connection_id"] == "graph-connection-000001"
        )
        first["destination"] = {
            "node_id": "graph-node-000003",
            "facet_id": "component-port-000001",
        }
        codes = {item.code for item in self._component_result(graph).diagnostics}
        self.assertIn("GRAPH_CONNECTION_TYPE_INCOMPATIBLE", codes)

    def test_third_low_pass_consumer_fails_shared_validator(self):
        graph = copy.deepcopy(self.graph)
        graph["connections"].append(
            {
                "connection_id": "graph-connection-000010",
                "source": {
                    "node_id": "graph-node-000007",
                    "facet_id": "component-port-000006",
                },
                "destination": {
                    "node_id": "graph-node-000007",
                    "facet_id": "component-port-000002",
                },
            }
        )
        codes = {item.code for item in self._component_result(graph).diagnostics}
        self.assertIn("GRAPH_OUTPUT_CARDINALITY_EXCEEDED", codes)

    def test_two_oscillators_share_one_exact_contract(self):
        nodes = {
            item["node_id"]: item for item in self.graph["nodes"]
        }
        self.assertEqual(
            nodes["graph-node-000004"]["contract_reference"],
            nodes["graph-node-000005"]["contract_reference"],
        )

    def test_probe_inputs_are_closed_and_not_authorized(self):
        probes = [
            item
            for item in self.selected.records["conformance-probe-input"]
            if 3
            <= int(item["conformance_probe_id"].rsplit("-", 1)[1])
            <= 8
        ]
        self.assertEqual(6, len(probes))
        self.assertEqual({"not-authorized"}, {item["execution_authorization"] for item in probes})
        self.assertEqual({False}, {item["production_selection_authority"] for item in probes})


if __name__ == "__main__":
    unittest.main()
