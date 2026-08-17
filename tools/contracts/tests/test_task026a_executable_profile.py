from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/contracts")]

from packages.schuss_core.control_plane import dispatch_operation, load_repository_context  # noqa: E402
from packages.schuss_core.effects_profile_backend import descriptor  # noqa: E402
from packages.schuss_core.effects_profile_frontend import (  # noqa: E402
    DIRECT_BINDINGS,
    lower_effects_profile,
    profile_reference,
    semantic_profile_signature,
)

import generate_task026a_records as generator  # noqa: E402
import validator_core as core  # noqa: E402


RECORD_SET = ROOT / "contracts/record-sets/task026a-executable-profile-v1.json"


def exact(values, field: str, stable_id: str, revision: int = 1):
    matches = [item for item in values if item[field] == stable_id and item["revision"] == revision]
    if len(matches) != 1:
        raise AssertionError(f"{stable_id}@{revision} did not resolve exactly")
    return matches[0]


def reference(record, field: str):
    return {field: record[field], "revision": record["revision"], "content_hash": record["content_hash"]}


class Task026AExecutableProfileTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = load_repository_context(record_set_path=RECORD_SET)
        cls.graph = exact(cls.context.records["graphs"], "graph_id", "schuss-graph-000006")
        cls.instrument = exact(cls.context.records["instruments"], "instrument_id", "schuss-instrument-000005")
        cls.request = exact(cls.context.records["request"], "build_request_id", "schuss-build-request-000005")
        cls.plan = dispatch_operation({
            "schema_version": "schuss-operation-request-v4",
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": "build.plan",
            "payload": {"build_request_reference": reference(cls.request, "build_request_id")},
        }, cls.context)["value"]
        cls.lowered = lower_effects_profile(
            cls.plan, cls.graph, cls.instrument, cls.request,
            cls.context.records["contracts"], cls.context.records["direct_operation_specs"],
        )

    def test_exact_parent_profile_records_and_reverb_boundary(self):
        manifest = core.load_json(RECORD_SET)
        parent = core.load_json(ROOT / "contracts/record-sets/task025-direct-core-v1.json")
        self.assertEqual("schuss-record-set-000018", manifest["record_set_id"])
        self.assertEqual(
            {key: parent[key] for key in ("record_set_id", "revision", "content_hash")},
            {key: manifest["parent_reference"][key] for key in ("record_set_id", "revision", "content_hash")},
        )
        task_members = [item for item in manifest["record_members"] if item["portable_path"].startswith("contracts/task026/")]
        ids = {item["stable_id"] for item in task_members}
        self.assertNotIn("schuss-implementation-000094", ids)
        self.assertNotIn("schuss-direct-operation-spec-000012", ids)
        self.assertIn("schuss-direct-operation-spec-000014", ids)
        self.assertEqual(7, len(self.graph["nodes"]))
        self.assertNotIn("schuss-component-contract-000017", {item["contract_reference"]["component_contract_id"] for item in self.graph["nodes"]})

    def test_plan_selects_exact_seven_bindings_and_included_instrument(self):
        self.assertEqual("success", self.plan["status"])
        self.assertEqual(["success"] * 6, [item["status"] for item in self.plan["stages"]])
        resolution = next(item["payload"] for item in self.plan["artifacts"] if item["descriptor"]["artifact_kind"] == "resolution-plan")
        selected = {(item["selected_binding_reference"]["implementation_id"], item["selected_binding_reference"]["revision"]) for item in resolution["traces"]}
        self.assertEqual(set(DIRECT_BINDINGS.values()), selected)
        self.assertEqual("included", self.request["instrument_reference"]["status"])
        self.assertEqual("direct-runtime-abi-instrument-closure-only", exact(self.context.records["backend"], "backend_id", "schuss-backend-000002", 4)["bridge_boundary"]["kind"])

    def test_profile_is_graph_identity_independent_but_semantically_exact(self):
        original = semantic_profile_signature(self.graph)
        clone = copy.deepcopy(self.graph)
        clone["graph_id"] = "schuss-graph-999991"
        clone["revision"] = 9
        clone["content_hash"] = "sha256:" + "0" * 64
        clone["content_hash"] = core.record_content_hash(clone, self.context.schemas["graph"])
        observed = semantic_profile_signature(clone)
        self.assertEqual(original.profile_hash, observed.profile_hash)
        self.assertNotEqual(reference(self.graph, "graph_id"), reference(clone, "graph_id"))
        for mutate, code in (
            (lambda value: value["nodes"].append(copy.deepcopy(value["nodes"][0])), "EFFECTS_PROFILE_NODE_SET_UNSUPPORTED"),
            (lambda value: value["connections"].pop(), "EFFECTS_PROFILE_CONNECTIONS_UNSUPPORTED"),
            (lambda value: value["nodes"][0]["parameter_values"][0].update({"value": "-23"}), "EFFECTS_PROFILE_NODE_VALUES_UNSUPPORTED"),
            (lambda value: value["parameter_bindings"][0]["smoothing"].update({"completion": "immediate"}), "EFFECTS_PROFILE_PARAMETER_BINDING_SEMANTICS_UNSUPPORTED"),
        ):
            changed = copy.deepcopy(self.graph)
            mutate(changed)
            with self.assertRaisesRegex(ValueError, code):
                semantic_profile_signature(changed)

    def test_frontend_is_complete_origin_preserving_and_reverb_free(self):
        self.assertEqual("success", self.lowered["status"])
        self.assertEqual(9, len(self.lowered["module"]["operations"]))
        self.assertEqual(9, len(self.lowered["module"]["connections"]))
        self.assertEqual([], core.schema_errors(self.lowered["module"], self.context.schemas["normalized_dsp_module_v1"], self.context.schemas["normalized_dsp_module_v1"]))
        self.assertEqual([], core.schema_errors(self.lowered, self.context.schemas["direct_frontend_result_v1"], self.context.schemas["direct_frontend_result_v1"]))
        origins = {item["origin"] for item in self.lowered["source_map"]["mappings"]}
        for node in self.graph["nodes"]:
            self.assertIn(node["node_id"], origins)
        for connection in self.graph["connections"]:
            self.assertIn(connection["connection_id"], origins)
        cpp = self.lowered["generated_cpp"]["text"].lower()
        for forbidden in ("reverb", "rings_fx", ".axp", "java", "legacy/ksoloti-bridge"):
            self.assertNotIn(forbidden, cpp)
        for required in ("process_saw", "process_pwm", "process_soft", "process_crossfade", "process_vca", "patchprocess"):
            self.assertIn(required, cpp)

    def test_profile_handler_descriptor_is_v1_and_not_request_locked(self):
        value = descriptor()
        schema = self.context.schemas["build_handler_descriptor_v1"]
        self.assertEqual([], core.schema_errors(value, schema, schema))
        self.assertEqual("exact-semantic-profile", value["execution_policy"])
        self.assertEqual(profile_reference(), value["supported_semantic_profile"])
        self.assertNotIn("supported_build_request_reference", value)

    def test_crossfade_application_spec_is_distinct_from_task016_schedule(self):
        old = exact(self.context.records["direct_operation_specs"], "direct_operation_spec_id", "schuss-direct-operation-spec-000005")
        new = exact(self.context.records["direct_operation_specs"], "direct_operation_spec_id", "schuss-direct-operation-spec-000014")
        self.assertIn('second_input="previous-sine-b-block"', old["schedule_semantics"])
        self.assertIn('second_input="current-soft-clipped-saw-block"', new["schedule_semantics"])
        self.assertEqual("schuss-implementation-000046", new["source_binding_reference"]["implementation_id"])

    def test_generated_records_are_fresh(self):
        files, manifest = generator.generated()
        for path, expected in files.items():
            self.assertEqual(expected, (ROOT / path).read_bytes(), path)
        expected_manifest = core.canonical_json(manifest).encode("utf-8") + b"\n"
        self.assertEqual(expected_manifest, RECORD_SET.read_bytes())


if __name__ == "__main__":
    unittest.main()
