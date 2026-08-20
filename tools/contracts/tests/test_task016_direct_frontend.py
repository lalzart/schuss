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

from packages.schuss_core.build_execution import handler_reference  # noqa: E402
from packages.schuss_core.control_plane import dispatch_operation, load_repository_context  # noqa: E402
from packages.schuss_core.gills_direct_backend import descriptor  # noqa: E402
from packages.schuss_core.gills_direct_frontend import (  # noqa: E402
    DIRECT_BINDING_IDS,
    NODE_OPERATIONS,
    lower_gills_direct,
    semantic_goldens,
)

import validator_core as core  # noqa: E402
from tools.validation.profile import requires_profile  # noqa: E402


RECORD_SET = ROOT / "contracts/record-sets/task016-complete-gills-direct-v1.json"
EVIDENCE = ROOT / "evidence/task016-completion-v1/validation-summary.json"


class Task016DirectFrontendTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = load_repository_context(record_set_path=RECORD_SET)
        cls.request = next(
            item for item in cls.context.records["request"]
            if item["build_request_id"] == "schuss-build-request-000002"
            and item["revision"] == 3
        )
        reference = {
            key: cls.request[key]
            for key in ("build_request_id", "revision", "content_hash")
        }
        operation = {
            "schema_version": "schuss-operation-request-v4",
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": "build.plan",
            "payload": {"build_request_reference": reference},
        }
        cls.plan = dispatch_operation(operation, cls.context)["value"]
        cls.graph = next(
            item for item in cls.context.records["graphs"]
            if item["graph_id"] == "schuss-graph-000002"
        )
        cls.result = lower_gills_direct(
            cls.plan,
            cls.graph,
            cls.context.records["contracts"],
            cls.context.records["direct_operation_specs"],
        )

    def test_record_set_and_frontend_schemas(self) -> None:
        self.assertEqual("valid", self.context.task007_summary["status"])
        self.assertEqual(
            [],
            core.schema_errors(
                self.result["module"],
                self.context.schemas["normalized_dsp_module_v1"],
                self.context.schemas["normalized_dsp_module_v1"],
            ),
        )
        self.assertEqual(
            [],
            core.schema_errors(
                self.result,
                self.context.schemas["direct_frontend_result_v1"],
                self.context.schemas["direct_frontend_result_v1"],
            ),
        )

    def test_exact_direct_selection_and_sine_reuse(self) -> None:
        resolution = next(
            item["payload"] for item in self.plan["artifacts"]
            if item["descriptor"]["artifact_kind"] == "resolution-plan"
        )
        traces = {item["node_id"]: item for item in resolution["traces"]}
        for node_id, opcode in NODE_OPERATIONS.items():
            selected = traces[node_id]["selected_binding_reference"]
            self.assertEqual(DIRECT_BINDING_IDS[opcode], selected["implementation_id"])
            self.assertEqual(2, selected["revision"])
        self.assertEqual(
            traces["graph-node-000004"]["selected_binding_reference"],
            traces["graph-node-000005"]["selected_binding_reference"],
        )

    def test_schedule_state_and_goldens_are_explicit(self) -> None:
        module = self.result["module"]
        self.assertEqual(9, len(module["operations"]))
        self.assertEqual(
            [f"dsp-operation-{number:06d}" for number in range(1, 10)],
            module["schedule"]["operation_ids"],
        )
        goldens = semantic_goldens()
        self.assertEqual(7, len(goldens["operations"]))
        self.assertEqual(2, len(goldens["graph_transitions"]))

    def test_every_node_facet_connection_and_public_binding_has_origin(self) -> None:
        origins = {item["origin"] for item in self.result["source_map"]["mappings"]}
        for node in self.graph["nodes"]:
            self.assertIn(node["node_id"], origins)
            contract = next(
                value for value in self.context.records["contracts"]
                if all(value.get(key) == item for key, item in node["contract_reference"].items())
            )
            for collection in ("ports", "parameters", "attributes", "actions", "displays", "state_declarations"):
                for facet in contract.get(collection, []):
                    facet_id = facet.get("facet_id", facet.get("state_id"))
                    self.assertIn(node["node_id"] + "/" + facet_id, origins)
        for connection in self.graph["connections"]:
            self.assertIn(connection["connection_id"], origins)
        for binding in self.graph["parameter_bindings"]:
            self.assertIn(binding["binding_id"], origins)

    def test_direct_cpp_has_runtime_calls_and_no_legacy_path(self) -> None:
        text = self.result["generated_cpp"]["text"]
        for required in ("mtof48k_ext_q31", "sin_q31", "xpatch_init", "PatchProcess"):
            self.assertIn(required, text)
        self.assertNotIn(".axp", text.lower())
        self.assertNotIn("java", text.lower())
        self.assertNotIn("legacy/ksoloti-bridge", text)
        self.assertFalse(self.result["java_used"])
        self.assertFalse(self.result["legacy_boundary_patch_used"])
        self.assertFalse(self.result["ambient_discovery_used"])

    def test_unsupported_inputs_fail_before_generation(self) -> None:
        with self.assertRaisesRegex(ValueError, "DIRECT_OPERATION_SPEC_SET_UNSUPPORTED"):
            lower_gills_direct(
                self.plan,
                self.graph,
                self.context.records["contracts"],
                self.context.records["direct_operation_specs"][:-1],
            )
        graph = copy.deepcopy(self.graph)
        graph["connections"] = graph["connections"][:-1]
        with self.assertRaisesRegex(ValueError, "DIRECT_GRAPH_CONNECTIONS_UNSUPPORTED"):
            lower_gills_direct(
                self.plan,
                graph,
                self.context.records["contracts"],
                self.context.records["direct_operation_specs"],
            )

    def test_registered_handler_is_exact_direct_request_only(self) -> None:
        value = descriptor()
        self.assertEqual(
            [],
            core.schema_errors(
                value,
                self.context.schemas["build_handler_descriptor"],
                self.context.schemas["build_handler_descriptor"],
            ),
        )
        self.assertEqual("direct", value["adapter_kind"])
        self.assertEqual("schuss-build-handler-000002", value["build_handler_id"])
        self.assertEqual(self.request["content_hash"], value["supported_build_request_reference"]["content_hash"])
        self.assertEqual(value["content_hash"], handler_reference(value)["content_hash"])

    def test_retained_two_root_evidence_is_separated(self) -> None:
        evidence = core.load_json(EVIDENCE)
        self.assertTrue(evidence["portable_operation_results_identical"])
        self.assertTrue(evidence["artifact_bytes_identical"])
        self.assertEqual(2, evidence["fresh_root_runs"])
        self.assertEqual(["passed"] * 5 + ["not-run"] * 3, [item["status"] for item in evidence["evidence_levels"]])
        self.assertFalse(evidence["device_actions_performed"])
        self.assertFalse(evidence["real_time_validation_performed"])
        self.assertFalse(evidence["audible_validation_performed"])

    @requires_profile("native")
    def test_product_cli_executes_only_the_requested_direct_handler(self) -> None:
        with tempfile.TemporaryDirectory(prefix="schuss-task016-cli-") as temporary:
            output = Path(temporary) / "published"
            completed = subprocess.run(
                [
                    str(ROOT / "bin/schuss"),
                    "build", "execute", "schuss-build-request-000002@3",
                    "--handler", "schuss-build-handler-000002@1",
                    "--output-root", str(output),
                    "--execute",
                    "--record-set", str(RECORD_SET),
                    "--json",
                ],
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stderr.decode("utf-8"))
            value = json.loads(completed.stdout)["value"]
            self.assertEqual("schuss-build-handler-000002", value["handler_reference"]["build_handler_id"])
            self.assertEqual("success", value["status"])


if __name__ == "__main__":
    unittest.main()
