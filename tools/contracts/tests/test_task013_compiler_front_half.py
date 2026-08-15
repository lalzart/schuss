import copy
import hashlib
import io
import os
import random
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools/contracts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from packages.schuss_core import (
    CompilationContext,
    ProjectService,
    canonical_result_bytes,
    dispatch_operation,
    load_repository_context,
    plan_build,
)
from packages.schuss_core import control_plane
from packages.schuss_core.cli import run as run_cli

import validator_core as core


RECORD_SET = ROOT / "contracts/record-sets/task013-compiler-front-half-v1.json"
TASK011C_RECORD_SET = ROOT / "contracts/record-sets/task011c-executed-v1.json"
PROJECT_FIXTURE = ROOT / "fixtures/task012a/minimal-project"


def _ref(record, field):
    return {
        field: record[field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def _artifact(plan, kind):
    return next(
        item for item in plan["artifacts"] if item["descriptor"]["artifact_kind"] == kind
    )


class Task013CompilerFrontHalfTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = load_repository_context(ROOT, record_set_path=RECORD_SET)
        cls.request = next(
            value
            for value in cls.context.records["request"]
            if value["build_request_id"] == "schuss-build-request-000002"
            and value["revision"] == 2
        )
        cls.request_ref = _ref(cls.request, "build_request_id")

    def compilation_context(self, context=None, request_ref=None, source=None, records=None):
        context = context or self.context
        return CompilationContext.from_values(
            build_request_reference=request_ref or self.request_ref,
            closure_source=source
            or {
                "kind": "record-set",
                "record_set_reference": context.record_set_reference,
            },
            records=records or context.records,
            schemas=context.schemas,
        )

    def plan(self, context=None, request_ref=None):
        return plan_build(self.compilation_context(context, request_ref))

    def replace_records(self, **groups):
        return self.context.with_records(**groups)

    def rehash(self, value, schema_key):
        schema = self.context.schemas[schema_key]
        value["content_hash"] = core.record_content_hash(value, schema)

    def rehash_versioned(self, value, schema_group):
        schema = self.context.schemas[schema_group][value["schema_version"]]
        value["content_hash"] = core.record_content_hash(value, schema)

    def dependency_plan(self, dependency_ids, providers):
        eligibilities = [copy.deepcopy(value) for value in self.context.records["eligibility"]]
        eligibility = next(
            value
            for value in eligibilities
            if value["binding_eligibility_id"] == "schuss-binding-eligibility-000002"
            and value["revision"] == 2
        )
        eligibility["dependency_requirements"] = [
            {
                "dependency_id": dependency_id,
                "portable_locator": f"sha256/{index:064x}",
                "state": {
                    "status": "supported",
                    "evidence_refs": ["fixture:task013-dependency-facts"],
                },
            }
            for index, dependency_id in enumerate(dependency_ids, 1)
        ]
        self.rehash(eligibility, "eligibility")
        context = self.replace_records(eligibility=eligibilities)
        facts = {
            "schema_version": "compiler-dependency-facts-v0",
            "canonical_profile": "schuss-canonical-json-v1",
            "compiler_dependency_facts_id": "schuss-compiler-dependency-facts-000001",
            "revision": 1,
            "content_hash": "sha256:" + "0" * 64,
            "providers": copy.deepcopy(providers),
        }
        self.rehash(facts, "compiler_dependency_facts")
        records = {**context.records, "dependency_facts": [facts]}
        return plan_build(self.compilation_context(context, records=records))

    def test_schemas_are_closed_portable_and_backend_neutral(self):
        for key in control_plane.TASK013_SCHEMA_NAMES:
            with self.subTest(schema=key):
                schema = self.context.schemas[key]
                self.assertEqual([], core.validate_schema_annotations(schema))
                text = core.canonical_json(schema).lower()
                self.assertNotIn("/users/", text)
                for forbidden in ("ksoloti", "java", "arm-none-eabi", ".axp"):
                    self.assertNotIn(forbidden, text)

    def test_public_context_is_immutable_and_api_has_one_planning_entry(self):
        records = {
            group: [copy.deepcopy(value) for value in values]
            for group, values in self.context.records.items()
        }
        compilation = CompilationContext.from_values(
            build_request_reference=self.request_ref,
            closure_source={
                "kind": "record-set",
                "record_set_reference": self.context.record_set_reference,
            },
            records=records,
            schemas=self.context.schemas,
        )
        records["graphs"][0]["display_name"] = "caller mutation"
        first = plan_build(compilation)
        second = plan_build(compilation)
        self.assertEqual(core.canonical_json(first), core.canonical_json(second))
        self.assertEqual("success", first["status"])

    def test_task011c_plan_reaches_stage6_without_backend_execution(self):
        plan = self.plan()
        self.assertEqual("success", plan["status"])
        self.assertEqual(["success"] * 6, [value["status"] for value in plan["stages"]])
        self.assertEqual(
            [
                "dependency-plan",
                "elaborated-graph",
                "origin-source-map",
                "resolution-plan",
                "resource-plan",
            ],
            [value["descriptor"]["artifact_kind"] for value in plan["artifacts"]],
        )
        self.assertEqual("not-created", plan["build_result_status"])
        self.assertEqual("not-run", plan["backend_execution_status"])
        self.assertFalse(plan["authoritative_records_mutated"])
        self.assertEqual(["not-run"] * 4, [value["status"] for value in plan["later_stages"]])
        self.assertEqual("passed", plan["evidence_levels"][0]["status"])
        self.assertEqual("passed", plan["evidence_levels"][1]["status"])
        self.assertEqual(["not-run"] * 6, [value["status"] for value in plan["evidence_levels"][2:]])

    def test_resolution_bytes_match_the_accepted_resolver_trace(self):
        plan = self.plan()
        resolution = _artifact(plan, "resolution-plan")["payload"]
        result = dispatch_operation(
            {
                "schema_version": "schuss-operation-request-v1",
                "canonical_profile": "schuss-canonical-json-v1",
                "operation": "build.resolve",
                "payload": {"build_request_reference": copy.deepcopy(self.request_ref)},
            },
            self.context,
        )
        self.assertEqual("success", result["status"])
        self.assertEqual(result["value"]["resolution_traces"], resolution["traces"])
        selected = {
            value["node_id"]: value["selected_binding_reference"]
            for value in resolution["traces"]
        }
        self.assertEqual(8, len(selected))
        self.assertEqual(selected["graph-node-000004"], selected["graph-node-000005"])

    def test_artifact_descriptors_bind_exact_canonical_payload_bytes(self):
        plan = self.plan()
        closure_hash = plan["input_closure"]["hash"]
        for item in plan["artifacts"]:
            payload = core.canonical_json(item["payload"]).encode()
            descriptor = item["descriptor"]
            digest = hashlib.sha256(payload).hexdigest()
            self.assertEqual(len(payload), descriptor["byte_length"])
            self.assertEqual(digest, descriptor["byte_sha256"])
            self.assertEqual(closure_hash, descriptor["input_closure_hash"])
            self.assertEqual(
                f"compiler-plans/sha256/{digest}.json", descriptor["portable_locator"]
            )
        elaborated = _artifact(plan, "elaborated-graph")["payload"]
        self.assertTrue(elaborated["derived"])
        self.assertFalse(elaborated["authoritative"])
        self.assertEqual(8, len(elaborated["nodes"]))
        self.assertEqual(9, len(elaborated["connections"]))
        parameter_binding = elaborated["public_interface"]["parameter_bindings"][0]
        self.assertEqual("graph-binding-000001", parameter_binding["binding_id"])
        self.assertEqual("derived-node:graph-node-000006", parameter_binding["derived_destination"]["derived_node_id"])

    def test_stage1_hash_failure_prevents_every_later_stage(self):
        graph = copy.deepcopy(
            next(value for value in self.context.records["graphs"] if value["graph_id"] == "schuss-graph-000002")
        )
        graph["display_name"] = "stale bytes"
        context = self.replace_records(
            graphs=[
                graph if value["graph_id"] == graph["graph_id"] else value
                for value in self.context.records["graphs"]
            ]
        )
        plan = self.plan(context)
        self.assertEqual("invalid", plan["status"])
        self.assertEqual("invalid", plan["stages"][0]["status"])
        self.assertEqual(["not-run"] * 5, [value["status"] for value in plan["stages"][1:]])
        self.assertIn("COMPILER_CONTENT_HASH_MISMATCH", {value["code"] for value in plan["diagnostics"]})
        self.assertEqual([], plan["artifacts"])

    def test_stage1_malformed_record_and_request_reference_fail_as_data(self):
        graph = copy.deepcopy(
            next(value for value in self.context.records["graphs"] if value["graph_id"] == "schuss-graph-000002")
        )
        del graph["nodes"]
        malformed = self.plan(
            self.replace_records(
                graphs=[
                    graph if value["graph_id"] == graph["graph_id"] else value
                    for value in self.context.records["graphs"]
                ]
            )
        )
        self.assertEqual("invalid", malformed["stages"][0]["status"])
        self.assertEqual(["not-run"] * 5, [value["status"] for value in malformed["stages"][1:]])
        self.assertIn("COMPILER_SCHEMA_STRUCTURE_INVALID", {value["code"] for value in malformed["diagnostics"]})

        invalid_reference = plan_build(
            self.compilation_context(request_ref={"build_request_id": self.request_ref["build_request_id"]})
        )
        self.assertEqual("invalid", invalid_reference["stages"][0]["status"])
        self.assertIn(
            "COMPILER_BUILD_REQUEST_REFERENCE_INVALID",
            {value["code"] for value in invalid_reference["diagnostics"]},
        )

        duplicate = self.plan(
            self.replace_records(
                graphs=(*self.context.records["graphs"], copy.deepcopy(self.context.records["graphs"][0]))
            )
        )
        self.assertEqual("invalid", duplicate["stages"][0]["status"])
        self.assertIn(
            "COMPILER_ID_REVISION_DUPLICATE",
            {value["code"] for value in duplicate["diagnostics"]},
        )

    def test_stage2_type_failure_prevents_target_and_resolution(self):
        graph = copy.deepcopy(
            next(value for value in self.context.records["graphs"] if value["graph_id"] == "schuss-graph-000002")
        )
        graph["connections"][1]["destination"] = {
            "node_id": "graph-node-000004",
            "facet_id": "component-port-000001",
        }
        self.rehash(graph, "graph")
        request = copy.deepcopy(self.request)
        request["graph_reference"] = _ref(graph, "graph_id")
        request["instrument_reference"] = {"status": "omitted"}
        self.rehash(request, "request")
        context = self.replace_records(
            graphs=[graph if value["graph_id"] == graph["graph_id"] else value for value in self.context.records["graphs"]],
            request=[request if value["build_request_id"] == request["build_request_id"] and value["revision"] == request["revision"] else value for value in self.context.records["request"]],
        )
        plan = self.plan(context, _ref(request, "build_request_id"))
        self.assertEqual("invalid", plan["stages"][1]["status"])
        self.assertEqual(["not-run"] * 4, [value["status"] for value in plan["stages"][2:]])
        self.assertIn("GRAPH_CONNECTION_TYPE_INCOMPATIBLE", {value["code"] for value in plan["diagnostics"]})

    def test_stage3_unsupported_pair_prevents_binding_resolution(self):
        backend = copy.deepcopy(
            next(value for value in self.context.records["backend"] if value["backend_id"] == "schuss-backend-000001" and value["revision"] == 3)
        )
        older_target = next(value for value in self.context.records["target"] if value["revision"] == 1)
        backend["target_pairings"] = [
            {**copy.deepcopy(backend["target_pairings"][0]), "target_reference": _ref(older_target, "compute_target_id")}
        ]
        self.rehash(backend, "backend")
        request = copy.deepcopy(self.request)
        request["backend_reference"] = _ref(backend, "backend_id")
        self.rehash(request, "request")
        context = self.replace_records(
            backend=[backend if value["backend_id"] == backend["backend_id"] and value["revision"] == backend["revision"] else value for value in self.context.records["backend"]],
            request=[request if value["build_request_id"] == request["build_request_id"] and value["revision"] == request["revision"] else value for value in self.context.records["request"]],
        )
        plan = self.plan(context, _ref(request, "build_request_id"))
        self.assertEqual("invalid", plan["stages"][2]["status"])
        self.assertEqual(["not-run"] * 3, [value["status"] for value in plan["stages"][3:]])
        self.assertIn("BUILD_REQUEST_TARGET_BACKEND_PAIR_UNDECLARED", {value["code"] for value in plan["diagnostics"]})

    def test_zero_candidates_and_equal_priority_candidates_fail_closed(self):
        lfo_contract = "schuss-component-contract-000004"
        without_lfo = [
            value
            for value in self.context.records["eligibility"]
            if value["contract_reference"]["component_contract_id"] != lfo_contract
        ]
        unsupported = self.plan(self.replace_records(eligibility=without_lfo))
        self.assertEqual("unsupported", unsupported["stages"][3]["status"])

        binding = copy.deepcopy(
            next(value for value in self.context.records["bindings"] if value["implementation_id"] == "schuss-implementation-000039" and value["revision"] == 2)
        )
        binding["implementation_id"] = "schuss-implementation-999001"
        self.rehash_versioned(binding, "binding_versions")
        eligibility = copy.deepcopy(
            next(value for value in self.context.records["eligibility"] if value["binding_eligibility_id"] == "schuss-binding-eligibility-000002" and value["revision"] == 2)
        )
        eligibility["binding_eligibility_id"] = "schuss-binding-eligibility-999001"
        eligibility["binding_reference"] = _ref(binding, "implementation_id")
        self.rehash(eligibility, "eligibility")
        ambiguous = self.plan(
            self.replace_records(
                bindings=(*self.context.records["bindings"], binding),
                eligibility=(*self.context.records["eligibility"], eligibility),
            )
        )
        self.assertEqual("ambiguous", ambiguous["stages"][3]["status"])
        self.assertEqual("not-run", ambiguous["stages"][4]["status"])

    def test_exact_override_may_narrow_but_cannot_make_ineligible_binding_eligible(self):
        binding = copy.deepcopy(
            next(value for value in self.context.records["bindings"] if value["implementation_id"] == "schuss-implementation-000039" and value["revision"] == 2)
        )
        binding["implementation_id"] = "schuss-implementation-999002"
        self.rehash_versioned(binding, "binding_versions")
        eligibility = copy.deepcopy(
            next(value for value in self.context.records["eligibility"] if value["binding_eligibility_id"] == "schuss-binding-eligibility-000002" and value["revision"] == 2)
        )
        eligibility["binding_eligibility_id"] = "schuss-binding-eligibility-999002"
        eligibility["binding_reference"] = _ref(binding, "implementation_id")
        eligibility["selection_policy"]["priority"] = 1
        self.rehash(eligibility, "eligibility")
        request = copy.deepcopy(self.request)
        request["binding_overrides"] = [
            {
                "override_id": "build-override-999002",
                "node_id": "graph-node-000001",
                "mode": "select-only-if-eligible",
                "binding_reference": _ref(binding, "implementation_id"),
            }
        ]
        self.rehash(request, "request")
        context = self.replace_records(
            bindings=(*self.context.records["bindings"], binding),
            eligibility=(*self.context.records["eligibility"], eligibility),
            request=[request if value["build_request_id"] == request["build_request_id"] and value["revision"] == request["revision"] else value for value in self.context.records["request"]],
        )
        plan = self.plan(context, _ref(request, "build_request_id"))
        trace = next(value for value in _artifact(plan, "resolution-plan")["payload"]["traces"] if value["node_id"] == "graph-node-000001")
        self.assertEqual(_ref(binding, "implementation_id"), trace["selected_binding_reference"])

        bad = copy.deepcopy(eligibility)
        bad["allowed_pair"]["state"] = {
            "status": "unsupported",
            "evidence_level": 2,
            "evidence_refs": copy.deepcopy(eligibility["allowed_pair"]["state"]["evidence_refs"]),
        }
        self.rehash(bad, "eligibility")
        invalid = self.plan(context.with_records(eligibility=(*self.context.records["eligibility"], bad)), _ref(request, "build_request_id"))
        self.assertEqual("invalid", invalid["stages"][3]["status"])

    def test_dependency_hash_conflict_is_stage6_and_traceable(self):
        eligibilities = [copy.deepcopy(value) for value in self.context.records["eligibility"]]
        targets = [
            value
            for value in eligibilities
            if value["binding_eligibility_id"] in {"schuss-binding-eligibility-000002", "schuss-binding-eligibility-000003"}
            and value["revision"] == 2
        ]
        for index, value in enumerate(targets, 1):
            value["dependency_requirements"] = [
                {
                    "dependency_id": "shared-dsp-library",
                    "portable_locator": f"sha256/{str(index) * 64}",
                    "state": {"status": "supported", "evidence_refs": ["fixture:task013-dependency"]},
                }
            ]
            self.rehash(value, "eligibility")
        plan = self.plan(self.replace_records(eligibility=eligibilities))
        self.assertEqual("invalid", plan["stages"][5]["status"])
        self.assertEqual("failed", plan["evidence_levels"][1]["status"])
        self.assertIn("COMPILER_DEPENDENCY_HASH_CONFLICT", {value["code"] for value in plan["diagnostics"]})
        dependency = _artifact(plan, "dependency-plan")["payload"]["dependencies"][0]
        self.assertEqual("conflict", dependency["decision"])
        origins = _artifact(plan, "origin-source-map")["payload"]["entries"]
        self.assertTrue(any(value["derived_subject"]["kind"] == "diagnostic" for value in origins))

    def test_missing_dependency_provider_fails_closed_at_stage6(self):
        plan = self.dependency_plan(["required-library"], [])
        self.assertEqual("invalid", plan["stages"][5]["status"])
        self.assertIn("COMPILER_DEPENDENCY_MISSING", {value["code"] for value in plan["diagnostics"]})
        dependency = _artifact(plan, "dependency-plan")["payload"]["dependencies"][0]
        self.assertEqual("missing", dependency["decision"])

    def test_ambiguous_dependency_versions_and_hashes_fail_closed(self):
        providers = [
            {
                "provider_id": f"dependency-provider-{index:06d}",
                "dependency_id": "required-library",
                "version": str(index),
                "portable_locator": "sha256/" + "0" * 63 + "1",
                "availability": "available",
                "requires": [],
                "exclusive_service": None,
            }
            for index in (1, 2)
        ]
        plan = self.dependency_plan(["required-library"], providers)
        codes = {value["code"] for value in plan["diagnostics"]}
        self.assertIn("COMPILER_DEPENDENCY_PROVIDER_AMBIGUOUS", codes)
        self.assertIn("COMPILER_DEPENDENCY_VERSION_HASH_CONFLICT", codes)
        self.assertEqual("conflict", _artifact(plan, "dependency-plan")["payload"]["dependencies"][0]["decision"])

    def test_dependency_cycle_is_detected_without_recursing(self):
        providers = [
            {
                "provider_id": "dependency-provider-000001",
                "dependency_id": "root-library",
                "version": "1",
                "portable_locator": "sha256/" + "0" * 63 + "1",
                "availability": "available",
                "requires": ["support-library"],
                "exclusive_service": None,
            },
            {
                "provider_id": "dependency-provider-000002",
                "dependency_id": "support-library",
                "version": "1",
                "portable_locator": "sha256/" + "0" * 63 + "2",
                "availability": "available",
                "requires": ["root-library"],
                "exclusive_service": None,
            },
        ]
        plan = self.dependency_plan(["root-library"], providers)
        self.assertIn("COMPILER_DEPENDENCY_CYCLE_PROHIBITED", {value["code"] for value in plan["diagnostics"]})
        dependency_plan = _artifact(plan, "dependency-plan")["payload"]
        self.assertEqual([{"dependency_ids": ["root-library", "support-library"]}], dependency_plan["cycles"])

    def test_dependency_order_places_providers_before_consumers(self):
        providers = [
            {
                "provider_id": "dependency-provider-000001",
                "dependency_id": "root-library",
                "version": "1",
                "portable_locator": "sha256/" + "0" * 63 + "1",
                "availability": "available",
                "requires": ["support-library"],
                "exclusive_service": None,
            },
            {
                "provider_id": "dependency-provider-000002",
                "dependency_id": "support-library",
                "version": "1",
                "portable_locator": "sha256/" + "0" * 63 + "2",
                "availability": "available",
                "requires": [],
                "exclusive_service": None,
            },
        ]
        plan = self.dependency_plan(["root-library"], providers)
        self.assertEqual("success", plan["status"])
        dependency_plan = _artifact(plan, "dependency-plan")["payload"]
        self.assertEqual(
            ["support-library", "root-library"],
            dependency_plan["ordered_dependency_ids"],
        )

    def test_exclusive_dependency_service_conflict_is_reported(self):
        providers = [
            {
                "provider_id": f"dependency-provider-{index:06d}",
                "dependency_id": dependency_id,
                "version": "1",
                "portable_locator": f"sha256/{index:064x}",
                "availability": "available",
                "requires": [],
                "exclusive_service": "singleton-runtime",
            }
            for index, dependency_id in enumerate(("first-library", "second-library"), 1)
        ]
        plan = self.dependency_plan(["first-library", "second-library"], providers)
        self.assertIn("COMPILER_DEPENDENCY_EXCLUSIVE_SERVICE_CONFLICT", {value["code"] for value in plan["diagnostics"]})
        conflicts = _artifact(plan, "dependency-plan")["payload"]["exclusive_services"]
        self.assertEqual(["first-library", "second-library"], conflicts[0]["dependency_ids"])

    def test_nonportable_dependency_fact_is_rejected_at_stage1(self):
        facts = {
            "schema_version": "compiler-dependency-facts-v0",
            "canonical_profile": "schuss-canonical-json-v1",
            "compiler_dependency_facts_id": "schuss-compiler-dependency-facts-000002",
            "revision": 1,
            "content_hash": "sha256:" + "0" * 64,
            "providers": [
                {
                    "provider_id": "dependency-provider-000001",
                    "dependency_id": "required-library",
                    "version": "1",
                    "portable_locator": "/Users/example/private/library.a",
                    "availability": "available",
                    "requires": [],
                    "exclusive_service": None,
                }
            ],
        }
        records = {**self.context.records, "dependency_facts": [facts]}
        plan = plan_build(self.compilation_context(records=records))
        self.assertEqual("invalid", plan["stages"][0]["status"])
        self.assertIn("COMPILER_INPUT_NONPORTABLE", {value["code"] for value in plan["diagnostics"]})
        self.assertEqual(["not-run"] * 5, [value["status"] for value in plan["stages"][1:]])

    def test_repeated_binding_resource_requirements_can_exceed_a_hard_budget(self):
        eligibility = copy.deepcopy(
            next(value for value in self.context.records["eligibility"] if value["binding_eligibility_id"] == "schuss-binding-eligibility-000005" and value["revision"] == 2)
        )
        target_record = next(value for value in self.context.records["target"] if value["revision"] == 2)
        region = next(value for value in target_record["memory_regions"] if "code" in value["resource_kinds"])
        amount = region["length_bytes"] // 2 + 1
        eligibility["resource_requirements"] = [
            {
                "requirement_id": "binding-resource-requirement-999001",
                "resource_kind": "code",
                "region_id": region["region_id"],
                "amount_bytes": amount,
                "alignment_bytes": 1,
                "state": {"status": "supported", "evidence_refs": ["fixture:task013-resource"]},
            }
        ]
        self.rehash(eligibility, "eligibility")
        eligibilities = [
            eligibility if value["binding_eligibility_id"] == eligibility["binding_eligibility_id"] and value["revision"] == eligibility["revision"] else value
            for value in self.context.records["eligibility"]
        ]
        plan = self.plan(self.replace_records(eligibility=eligibilities))
        self.assertEqual("budget-failure", plan["status"])
        self.assertEqual("budget-failure", plan["stages"][5]["status"])
        self.assertEqual("failed", plan["evidence_levels"][1]["status"])
        resource = _artifact(plan, "resource-plan")["payload"]
        self.assertEqual(2, len([value for value in resource["requirements"] if value["requirement_id"] == eligibility["resource_requirements"][0]["requirement_id"]]))
        self.assertIn("exceeded", {value["decision"] for value in resource["budgets"]})
        self.assertEqual([], resource["estimates"])
        self.assertEqual([], resource["measurements"])

    def test_unknown_required_resource_remains_unresolved_without_guessing(self):
        eligibility = copy.deepcopy(
            next(value for value in self.context.records["eligibility"] if value["binding_eligibility_id"] == "schuss-binding-eligibility-000005" and value["revision"] == 2)
        )
        target_record = next(value for value in self.context.records["target"] if value["revision"] == 2)
        region = next(value for value in target_record["memory_regions"] if "code" in value["resource_kinds"])
        eligibility["resource_requirements"] = [
            {
                "requirement_id": "binding-resource-requirement-999002",
                "resource_kind": "code",
                "region_id": region["region_id"],
                "amount_bytes": 1,
                "alignment_bytes": 1,
                "state": {"status": "unresolved", "code": "RESOURCE_FACT_UNKNOWN", "rationale": "fixture required fact is absent"},
            }
        ]
        self.rehash(eligibility, "eligibility")
        eligibilities = [
            eligibility if value["binding_eligibility_id"] == eligibility["binding_eligibility_id"] and value["revision"] == eligibility["revision"] else value
            for value in self.context.records["eligibility"]
        ]
        plan = self.plan(self.replace_records(eligibility=eligibilities))
        self.assertEqual("unresolved", plan["stages"][3]["status"])
        self.assertEqual(["not-run", "not-run"], [value["status"] for value in plan["stages"][4:]])

    def transparent_fixture(self, *, recursive=False, incomplete=False, incompatible=False):
        mixed = next(value for value in self.context.records["contracts"] if value["component_contract_id"] == "schuss-component-contract-000003")
        outer = copy.deepcopy(mixed)
        outer["component_contract_id"] = "schuss-component-contract-999100"
        outer["display_name"] = "Transparent Crossfader fixture"
        outer["compound_interface"] = {
            "kind": "transparent-compound",
            "mapping_keys": [
                {"mapping_key": f"compound-mapping-key-{index:06d}", "facet_kind": "port", "facet_id": f"component-port-{index:06d}"}
                for index in range(1, 5)
            ],
        }
        self.rehash_versioned(outer, "contract_versions")

        template = next(value for value in self.context.records["graphs"] if value["graph_id"] == "schuss-graph-000001")
        inner = copy.deepcopy(template)
        inner["graph_id"] = "schuss-graph-999100"
        inner["display_name"] = "Transparent implementation fixture"
        inner["nodes"][0]["contract_reference"] = _ref(outer if recursive else mixed, "component_contract_id")
        inner["compound_interface_mappings"] = [
            {
                "mapping_key": f"compound-mapping-key-{index:06d}",
                "target": {"node_id": inner["nodes"][0]["node_id"], "facet_kind": "port", "facet_id": f"component-port-{index:06d}"},
            }
            for index in range(1, 5)
        ]
        if incomplete:
            inner["compound_interface_mappings"].pop()
        if incompatible:
            inner["compound_interface_mappings"][0]["target"]["facet_id"] = "component-port-000004"
        self.rehash(inner, "graph")

        top = copy.deepcopy(template)
        top["graph_id"] = "schuss-graph-999101"
        top["display_name"] = "Transparent outer fixture"
        top["nodes"][0]["contract_reference"] = _ref(outer, "component_contract_id")
        self.rehash(top, "graph")

        binding_template = next(value for value in self.context.records["bindings"] if value["implementation_id"] == "schuss-implementation-000028" and value["revision"] == 2)
        binding = copy.deepcopy(binding_template)
        binding["implementation_id"] = "schuss-implementation-999100"
        binding["contract_reference"] = _ref(outer, "component_contract_id")
        binding["realization"] = {"form": "transparent-compound", "graph_reference": _ref(inner, "graph_id")}
        binding["facet_mappings"] = [
            {
                "mapping_id": f"binding-map-{999100 + index - 1:06d}",
                "contract_facet": {"facet_kind": "port", "facet_id": f"component-port-{index:06d}"},
                "implementation_seam": {"seam_kind": "graph-mapping-key", "mapping_key": f"compound-mapping-key-{index:06d}"},
            }
            for index in range(1, 5)
        ]
        if incompatible:
            binding["facet_mappings"][0]["contract_facet"]["facet_id"] = "component-port-000002"
        binding["observed_dependencies"] = []
        binding["private_state"] = []
        binding["evidence_refs"] = ["fixture:task013-transparent"]
        self.rehash_versioned(binding, "binding_versions")

        backend = copy.deepcopy(next(value for value in self.context.records["backend"] if value["backend_id"] == "schuss-backend-000001" and value["revision"] == 3))
        backend["supported_realization_forms"].append("transparent-compound")
        self.rehash(backend, "backend")

        eligibilities = [copy.deepcopy(value) for value in self.context.records["eligibility"]]
        for value in eligibilities:
            if value["allowed_pair"]["backend_reference"]["revision"] == 3:
                value["allowed_pair"]["backend_reference"] = _ref(backend, "backend_id")
                self.rehash(value, "eligibility")
        eligibility = copy.deepcopy(next(value for value in eligibilities if value["binding_eligibility_id"] == "schuss-binding-eligibility-000001" and value["revision"] == 3))
        eligibility["binding_eligibility_id"] = "schuss-binding-eligibility-999100"
        eligibility["binding_reference"] = _ref(binding, "implementation_id")
        eligibility["contract_reference"] = _ref(outer, "component_contract_id")
        eligibility["realization_form"] = "transparent-compound"
        self.rehash(eligibility, "eligibility")
        eligibilities.append(eligibility)

        request = copy.deepcopy(self.request)
        request["build_request_id"] = "schuss-build-request-999100"
        request["graph_reference"] = _ref(top, "graph_id")
        request["instrument_reference"] = {"status": "omitted"}
        request["backend_reference"] = _ref(backend, "backend_id")
        self.rehash(request, "request")
        context = self.replace_records(
            contracts=(*self.context.records["contracts"], outer),
            bindings=(*self.context.records["bindings"], binding),
            graphs=(*self.context.records["graphs"], inner, top),
            backend=[backend if value["backend_id"] == backend["backend_id"] and value["revision"] == backend["revision"] else value for value in self.context.records["backend"]],
            eligibility=eligibilities,
            request=(*self.context.records["request"], request),
        )
        return context, request

    def test_transparent_compound_elaboration_is_namespaced_and_traceable(self):
        context, request = self.transparent_fixture()
        plan = self.plan(context, _ref(request, "build_request_id"))
        self.assertEqual("success", plan["status"])
        elaborated = _artifact(plan, "elaborated-graph")["payload"]
        self.assertEqual(1, len(elaborated["nodes"]))
        node = elaborated["nodes"][0]
        self.assertEqual("derived-node:graph-node-000001/graph-node-000001", node["derived_node_id"])
        self.assertEqual("graph-node-000001", node["origin"]["outer_node_id"])
        self.assertEqual("schuss-graph-999100", node["origin"]["implementation_graph_reference"]["graph_id"])
        self.assertEqual(1, len(elaborated["hierarchy"][0]["compound_ancestors"]))

    def test_compound_recursion_and_incomplete_mapping_fail_before_stage6(self):
        for recursive, incomplete, incompatible, code in (
            (True, False, False, "COMPILER_COMPOUND_RECURSION"),
            (False, True, False, "COMPILER_COMPOUND_MAPPING_INCOMPLETE"),
            (False, False, True, "COMPILER_COMPOUND_MAPPING_INCOMPATIBLE"),
        ):
            with self.subTest(code=code):
                context, request = self.transparent_fixture(
                    recursive=recursive,
                    incomplete=incomplete,
                    incompatible=incompatible,
                )
                plan = self.plan(context, _ref(request, "build_request_id"))
                self.assertEqual("invalid", plan["stages"][4]["status"])
                self.assertEqual("not-run", plan["stages"][5]["status"])
                self.assertIn(code, {value["code"] for value in plan["diagnostics"]})

    def test_additive_operation_direct_process_and_project_context_agree(self):
        request = {
            "schema_version": "schuss-operation-request-v4",
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": "build.plan",
            "payload": {"build_request_reference": copy.deepcopy(self.request_ref)},
        }
        with mock.patch.object(control_plane.compiler, "plan_build", wraps=control_plane.compiler.plan_build) as wrapped:
            direct = dispatch_operation(copy.deepcopy(request), self.context)
            self.assertEqual(1, wrapped.call_count)
        direct_bytes = canonical_result_bytes(direct, self.context)
        stdin = io.BytesIO(core.canonical_json(request).encode() + b"\n")
        stdout = io.BytesIO()
        stderr = io.StringIO()
        code = run_cli(
            ["op", "--record-set", str(RECORD_SET), "--request", "-", "--json"],
            stdin,
            stdout,
            stderr,
        )
        self.assertEqual(0, code, stderr.getvalue())
        self.assertEqual(direct_bytes + b"\n", stdout.getvalue())

        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "workspace"
            shutil.copytree(PROJECT_FIXTURE, workspace)
            service = ProjectService(workspace)
            project_result = dispatch_operation(request, service.context, project_service=service)
            self.assertEqual("success", project_result["status"])
            self.assertEqual("project", project_result["value"]["input_closure"]["closure_source"]["kind"])
            project_stdout = io.BytesIO()
            project_stderr = io.StringIO()
            project_code = run_cli(
                ["project", "op", "--project", str(workspace), "--request", "-", "--json"],
                io.BytesIO(core.canonical_json(request).encode() + b"\n"),
                project_stdout,
                project_stderr,
            )
            self.assertEqual(0, project_code, project_stderr.getvalue())
            self.assertEqual(
                canonical_result_bytes(project_result, service.context) + b"\n",
                project_stdout.getvalue(),
            )

    def test_determinism_survives_enumeration_and_environment_variation(self):
        expected = core.canonical_json(self.plan()).encode()
        shuffled = {}
        randomizer = random.Random(130013)
        for group, values in self.context.records.items():
            values = list(values)
            randomizer.shuffle(values)
            shuffled[group] = values
        alternate = self.context.with_records(**shuffled)
        self.assertEqual(expected, core.canonical_json(self.plan(alternate)).encode())

        script = """
import os
from pathlib import Path
from packages.schuss_core import CompilationContext, load_repository_context, plan_build
from packages.schuss_core.control_plane import core
root=Path(os.environ['SCHUSS_TEST_ROOT']); c=load_repository_context(root,record_set_path=root/'contracts/record-sets/task013-compiler-front-half-v1.json')
r=next(x for x in c.records['request'] if x['build_request_id']=='schuss-build-request-000002' and x['revision']==2)
cc=CompilationContext.from_values(build_request_reference={k:r[k] for k in ('build_request_id','revision','content_hash')},closure_source={'kind':'record-set','record_set_reference':c.record_set_reference},records=c.records,schemas=c.schemas)
print(core.canonical_json(plan_build(cc)))
"""
        with tempfile.TemporaryDirectory() as temporary:
            for seed, locale, working_directory in (
                ("1", "C", ROOT),
                ("991", "en_US.UTF-8", Path(temporary)),
            ):
                environment = dict(
                    os.environ,
                    PYTHONHASHSEED=seed,
                    LC_ALL=locale,
                    LANG=locale,
                    SCHUSS_TEST_ROOT=str(ROOT),
                    PYTHONPATH=str(ROOT),
                )
                output = subprocess.run(
                    [sys.executable, "-c", script],
                    cwd=working_directory,
                    env=environment,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True,
                ).stdout.rstrip(b"\n")
                self.assertEqual(expected, output)


if __name__ == "__main__":
    unittest.main()
