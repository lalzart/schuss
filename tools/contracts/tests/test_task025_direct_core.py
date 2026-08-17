from __future__ import annotations

import copy
import hashlib
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/contracts")]

from packages.schuss_core.control_plane import (  # noqa: E402
    dispatch_operation,
    load_repository_context,
)
from packages.schuss_core.effects_direct_semantics import (  # noqa: E402
    DIRECT_BINDING_IDS,
    OPERATION_SPEC_IDS,
    SOURCE_BINDING_IDS,
    BlepSawState,
    SmoothState,
    VcaState,
    evaluate_blep_saw_block,
    evaluate_exponential_smooth,
    evaluate_soft_clip_sample,
    evaluate_vca_block,
    semantic_goldens,
)

import generate_task025_records as generator  # noqa: E402
import validator_core as core  # noqa: E402


RECORD_SET = ROOT / "contracts/record-sets/task025-direct-core-v1.json"
PARENT_SET = ROOT / "contracts/record-sets/task024-catalog-coverage-v1.json"
LOCAL_SOURCES = ROOT / "catalog/sources.local.yml"
LOCAL_SOURCE_SKIP = (
    "configured Task 025 source reproduction requires ignored "
    "catalog/sources.local.yml; run "
    "python3 tools/contracts/validate_task024_025_configured_sources.py separately"
)


def _exact(values, field: str, stable_id: str, revision: int):
    matches = [
        value for value in values
        if value[field] == stable_id and value["revision"] == revision
    ]
    if len(matches) != 1:
        raise AssertionError(f"exact record does not resolve once: {stable_id}@{revision}")
    return matches[0]


class Task025DirectCoreTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = load_repository_context(record_set_path=RECORD_SET)
        cls.request = _exact(
            cls.context.records["request"],
            "build_request_id",
            "schuss-build-request-000004",
            3,
        )
        request_reference = {
            key: cls.request[key]
            for key in ("build_request_id", "revision", "content_hash")
        }
        cls.plan_envelope = dispatch_operation(
            {
                "schema_version": "schuss-operation-request-v4",
                "canonical_profile": "schuss-canonical-json-v1",
                "operation": "build.plan",
                "payload": {"build_request_reference": request_reference},
            },
            cls.context,
        )
        cls.plan = cls.plan_envelope["value"]
        cls.resolution = next(
            item["payload"]
            for item in cls.plan["artifacts"]
            if item["descriptor"]["artifact_kind"] == "resolution-plan"
        )

    def test_exact_parent_is_preserved_and_task024_catalog_stays_selected(self) -> None:
        manifest = core.load_json(RECORD_SET)
        parent = core.load_json(PARENT_SET)
        self.assertEqual("schuss-record-set-000017", manifest["record_set_id"])
        self.assertEqual(
            {key: parent[key] for key in ("record_set_id", "revision", "content_hash")},
            {key: manifest["parent_reference"][key] for key in ("record_set_id", "revision", "content_hash")},
        )
        self.assertTrue(all(item in manifest["schema_members"] for item in parent["schema_members"]))
        self.assertTrue(all(item in manifest["record_members"] for item in parent["record_members"]))
        self.assertEqual("catalog-corpus-v3", self.context.records["catalog"][0]["schema_version"])
        self.assertEqual(3, self.context.records["catalog"][0]["revision"])

    def test_schema_successors_coexist_with_historical_versions(self) -> None:
        self.assertEqual(
            {"direct-operation-spec-v0", "direct-operation-spec-v1"},
            set(self.context.schemas["direct_operation_spec_versions"]),
        )
        self.assertEqual(
            {"core-selection-packet-v0", "task025-selection-packet-v0"},
            set(self.context.schemas["selection_packet_versions"]),
        )
        packet_versions = {item["schema_version"] for item in self.context.records["selection_packets"]}
        self.assertEqual(
            {"core-selection-packet-v0", "task025-selection-packet-v0"},
            packet_versions,
        )

    def test_five_operation_specs_bind_exact_source_authorities(self) -> None:
        new_specs = [
            item for item in self.context.records["direct_operation_specs"]
            if item["schema_version"] == "direct-operation-spec-v1"
        ]
        self.assertEqual(set(OPERATION_SPEC_IDS.values()), {item["direct_operation_spec_id"] for item in new_specs})
        self.assertNotIn("schuss-direct-operation-spec-000012", {item["direct_operation_spec_id"] for item in new_specs})
        for opcode, stable_id in OPERATION_SPEC_IDS.items():
            spec = _exact(new_specs, "direct_operation_spec_id", stable_id, 1)
            self.assertEqual(opcode, spec["opcode"])
            self.assertEqual(SOURCE_BINDING_IDS[opcode], spec["source_binding_reference"]["implementation_id"])
            source = _exact(
                self.context.records["bindings"],
                "implementation_id",
                SOURCE_BINDING_IDS[opcode],
                2,
            )
            self.assertEqual(source["content_hash"], spec["source_binding_reference"]["content_hash"])
            self.assertTrue(spec["numeric_semantics"])
            self.assertTrue(spec["state_semantics"])
            self.assertTrue(spec["schedule_semantics"])

    def test_five_native_bindings_are_distinct_and_complete(self) -> None:
        new_bindings = [
            _exact(self.context.records["bindings"], "implementation_id", identifier, 1)
            for identifier in DIRECT_BINDING_IDS.values()
        ]
        self.assertNotIn("schuss-implementation-000094", {item["implementation_id"] for item in new_bindings})
        for binding in new_bindings:
            self.assertEqual("native-cpp", binding["realization"]["form"])
            mapped = {
                (item["contract_facet"]["facet_kind"], item["contract_facet"]["facet_id"])
                for item in binding["facet_mappings"]
            }
            self.assertEqual(len(mapped), len(binding["facet_mappings"]))
            self.assertTrue(binding["evidence_refs"])
        self.assertEqual("valid", self.context.component_summary["status"])

    def test_supported_and_unsupported_eligibility_is_explicit(self) -> None:
        supported_numbers = {27, 28, 29, 30, 32}
        expected_bindings = set(DIRECT_BINDING_IDS.values())
        actual_bindings = set()
        for number in supported_numbers:
            record = _exact(
                self.context.records["eligibility"],
                "binding_eligibility_id",
                f"schuss-binding-eligibility-{number:06d}",
                1,
            )
            self.assertEqual("supported", record["allowed_pair"]["state"]["status"])
            self.assertEqual(3, record["allowed_pair"]["backend_reference"]["revision"])
            self.assertFalse(record["selection_policy"]["implicit_fallback"])
            actual_bindings.add(record["binding_reference"]["implementation_id"])
        self.assertEqual(expected_bindings, actual_bindings)

        reverb = _exact(
            self.context.records["eligibility"],
            "binding_eligibility_id",
            "schuss-binding-eligibility-000031",
            1,
        )
        self.assertEqual("schuss-implementation-000056", reverb["binding_reference"]["implementation_id"])
        self.assertEqual(2, reverb["binding_reference"]["revision"])
        self.assertEqual("unsupported", reverb["allowed_pair"]["state"]["status"])
        self.assertTrue(all(item["state"]["status"] == "unsupported" for item in reverb["resource_requirements"]))

    def test_evidence_keeps_passed_promotions_and_failed_reverb_separate(self) -> None:
        passed_ids = {f"schuss-evidence-claim-{number:06d}" for number in (38, 39, 40, 41, 43)}
        passed = [
            _exact(self.context.records["evidence"], "evidence_claim_id", stable_id, 1)
            for stable_id in passed_ids
        ]
        self.assertTrue(all(item["level"] == 2 and item["outcome"] == "passed" for item in passed))
        reverb = _exact(
            self.context.records["evidence"],
            "evidence_claim_id",
            "schuss-evidence-claim-000042",
            1,
        )
        self.assertEqual(2, reverb["level"])
        self.assertEqual("failed", reverb["outcome"])
        self.assertIn("65536 bytes", " ".join(reverb["limitations"]))

    def test_plan_selects_seven_nodes_and_fails_closed_at_reverb(self) -> None:
        self.assertEqual("unsupported", self.plan_envelope["status"])
        self.assertEqual("unsupported", self.plan["status"])
        traces = self.resolution["traces"]
        self.assertEqual(8, len(traces))
        selected = {
            item["selected_binding_reference"]["implementation_id"]
            for item in traces
            if item["status"] == "selected"
        }
        self.assertEqual(
            {"schuss-implementation-000046", "schuss-implementation-000048", *DIRECT_BINDING_IDS.values()},
            selected,
        )
        rejected = [item for item in traces if item["status"] == "unsupported"]
        self.assertEqual(1, len(rejected))
        self.assertEqual("graph-node-000004", rejected[0]["node_id"])
        self.assertIsNone(rejected[0]["selected_binding_reference"])
        self.assertEqual(["COMPILER_BINDING_UNSUPPORTED"], [item["code"] for item in self.plan["diagnostics"]])

    def test_plan_stops_before_lowering_and_reports_evidence_honestly(self) -> None:
        self.assertEqual(
            ["success", "success", "success", "unsupported", "not-run", "not-run"],
            [item["status"] for item in self.plan["stages"]],
        )
        self.assertEqual(
            ["passed", "failed"] + ["not-run"] * 6,
            [item["status"] for item in self.plan["evidence_levels"]],
        )
        kinds = [item["descriptor"]["artifact_kind"] for item in self.plan["artifacts"]]
        self.assertEqual(["resolution-plan"], kinds)
        encoded = core.canonical_json(self.plan)
        for forbidden in ("generated-cpp", "support-header", "target-executable", ".elf"):
            self.assertNotIn(forbidden, encoded)
        self.assertEqual("not-run", self.plan["backend_execution_status"])
        self.assertFalse(self.plan["authoritative_records_mutated"])

    @unittest.skipUnless(LOCAL_SOURCES.is_file(), LOCAL_SOURCE_SKIP)
    def test_reverb_source_audit_and_absent_native_records_are_exact(self) -> None:
        observed = generator._verify_source_authority()
        self.assertEqual(
            "944fa85fd56fda21d207174b236e54d7f9e511dab923a8e648b1e37e0c2d51cd",
            observed["objects/fx/rngs/reverb.axo"],
        )
        self.assertEqual(
            "3da1acbf013cd4d7c2a105c95d99e19b0b1c173addc24dc2f79af85523d0a55b",
            observed["objects/fx/rngs/rings_fx.h"],
        )
        task_records = [
            member for member in core.load_json(RECORD_SET)["record_members"]
            if member["portable_path"].startswith("contracts/task025/")
        ]
        self.assertNotIn("schuss-implementation-000094", {item["stable_id"] for item in task_records})
        self.assertNotIn("schuss-direct-operation-spec-000012", {item["stable_id"] for item in task_records})
        self.assertNotIn("schuss-build-handler-000004", {item["stable_id"] for item in task_records})

    def test_semantic_vectors_and_state_transitions_are_stable(self) -> None:
        golden_path = ROOT / "evidence/task025-completion-v1/semantic-goldens.json"
        self.assertEqual(
            "7a0ec21f952175362986ada0c73534e45c19a860c4aae6eec431e34296c93873",
            hashlib.sha256(golden_path.read_bytes()).hexdigest(),
        )
        self.assertEqual(core.load_json(golden_path), semantic_goldens())
        self.assertEqual(-134217728, evaluate_soft_clip_sample(-(1 << 29)))
        self.assertEqual(134217728, evaluate_soft_clip_sample(1 << 29))
        smooth = SmoothState()
        self.assertEqual(2097152, evaluate_exponential_smooth(smooth, 1 << 27, 0))
        vca = VcaState()
        self.assertEqual([0] * 16, evaluate_vca_block(vca, 1 << 27, [1 << 27] * 16)[:1] + [0] * 15)
        with self.assertRaisesRegex(ValueError, "EFFECTS_DIRECT_BLEP_TABLE_INVALID"):
            evaluate_blep_saw_block(
                BlepSawState(),
                0,
                pitch_to_frequency=lambda _: 1,
                blep_table=[0] * 64,
            )

    def test_stale_reverb_disposition_fails_before_outputs(self) -> None:
        records = list(self.context.records["eligibility"])
        target = _exact(
            records,
            "binding_eligibility_id",
            "schuss-binding-eligibility-000031",
            1,
        )
        changed = copy.deepcopy(target)
        changed["allowed_pair"]["state"]["status"] = "supported"
        records[records.index(target)] = changed
        changed_context = self.context.with_records(eligibility=records)
        result = dispatch_operation(
            {
                "schema_version": "schuss-operation-request-v4",
                "canonical_profile": "schuss-canonical-json-v1",
                "operation": "build.plan",
                "payload": {
                    "build_request_reference": {
                        key: self.request[key]
                        for key in ("build_request_id", "revision", "content_hash")
                    }
                },
            },
            changed_context,
        )
        self.assertEqual("invalid", result["status"])
        self.assertIn(
            "COMPILER_CONTENT_HASH_MISMATCH",
            {item["code"] for item in result["value"]["diagnostics"]},
        )
        self.assertEqual([], result["value"]["artifacts"])

    @unittest.skipUnless(LOCAL_SOURCES.is_file(), LOCAL_SOURCE_SKIP)
    def test_generated_records_are_fresh_and_deterministic(self) -> None:
        first_files, first_manifest, first_summary = generator.generated()
        second_files, second_manifest, second_summary = generator.generated()
        self.assertEqual(first_files, second_files)
        self.assertEqual(first_manifest, second_manifest)
        self.assertEqual(first_summary, second_summary)
        expected = {**first_files, RECORD_SET.relative_to(ROOT).as_posix(): first_manifest}
        self.assertTrue(all((ROOT / path).read_bytes() == payload for path, payload in expected.items()))
        self.assertFalse(first_summary["build_handler_created"])
        self.assertFalse(first_summary["arm_build_performed"])


if __name__ == "__main__":
    unittest.main()
