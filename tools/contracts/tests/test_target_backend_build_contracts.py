import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools/contracts"
SCHEMA_ROOT = ROOT / "schemas"
CONTRACT_ROOT = ROOT / "contracts"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _load_module(name, path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


BASE = _load_module("validate_device_instrument_contracts", TOOLS / "validate_device_instrument_contracts.py")
COMPONENT = _load_module("validate_component_graph_contracts", TOOLS / "validate_component_graph_contracts.py")
VALIDATOR = _load_module("validate_target_backend_build_contracts", TOOLS / "validate_target_backend_build_contracts.py")


def _ref(record, id_field):
    return {id_field: record[id_field], "revision": record["revision"], "content_hash": record["content_hash"]}


def _key(record, id_field):
    return record[id_field], record["revision"], record["content_hash"]


def _codes(diagnostics):
    return {item.code if hasattr(item, "code") else item["code"] for item in diagnostics}


def _set_pointer(value, pointer, replacement):
    tokens = [token.replace("~1", "/").replace("~0", "~") for token in pointer[1:].split("/")]
    parent = value
    for token in tokens[:-1]:
        parent = parent[int(token)] if isinstance(parent, list) else parent[token]
    token = tokens[-1]
    if isinstance(parent, list):
        parent[int(token)] = copy.deepcopy(replacement)
    else:
        parent[token] = copy.deepcopy(replacement)


class TargetBackendBuildContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schemas = VALIDATOR._schemas(SCHEMA_ROOT)
        cls.records = VALIDATOR._records(CONTRACT_ROOT)
        cls.vocabulary = cls.records["capability"][0]
        cls.environment_tool = cls.records["environment"][0]
        cls.environment_runtime = cls.records["environment"][1]
        cls.target = cls.records["target"][0]
        cls.backend = cls.records["backend"][0]
        cls.eligibility = cls.records["eligibility"][0]
        cls.request = cls.records["request"][0]
        cls.graph = BASE.load_json(CONTRACT_ROOT / "graphs/blend-crossfader-v0.json")
        cls.instrument = BASE.load_json(CONTRACT_ROOT / "instruments/blend-reference-v0-r2.json")
        cls.contract = BASE.load_json(CONTRACT_ROOT / "component-contracts/crossfader-mixed-v0.json")
        cls.binding = BASE.load_json(CONTRACT_ROOT / "implementation-bindings/crossfader-mixed-legacy-v0.json")
        cls.positive = BASE.load_json(FIXTURES / "target-backend-build-positive-fixtures.json")
        cls.negative = BASE.load_json(FIXTURES / "target-backend-build-negative-fixtures.json")
        cls.capability_registry = VALIDATOR._registry([cls.vocabulary], "capability_vocabulary_id")
        cls.definitions = {item["key"]: item for item in cls.vocabulary["definitions"]}
        cls.environment_registry = VALIDATOR._registry([cls.environment_tool, cls.environment_runtime], "build_environment_id")
        cls.target_registry = VALIDATOR._registry([cls.target], "compute_target_id")
        cls.backend_registry = VALIDATOR._registry([cls.backend], "backend_id")

    def rehash(self, record, kind):
        record["content_hash"] = BASE.record_content_hash(record, self.schemas[kind])

    def supported_target(self):
        target = copy.deepcopy(self.target)
        evidence = copy.deepcopy(target["processor"]["evidence_refs"][:1])
        for declaration in target["capability_declarations"]:
            declaration["state"] = {"status": "supported", "value": True, "evidence_level": 2, "evidence_refs": evidence}
        return target

    def supported_eligibility(self, numeric_id=900001, priority=100):
        eligibility = copy.deepcopy(self.eligibility)
        eligibility["binding_eligibility_id"] = f"schuss-binding-eligibility-{numeric_id:06d}"
        eligibility["allowed_pair"]["state"] = {
            "status": "supported",
            "evidence_level": 2,
            "evidence_refs": [{"evidence_claim_id": "schuss-evidence-claim-900002", "revision": 1, "content_hash": self.positive["evidence_claims"][1]["content_hash"]}],
        }
        eligibility["compatibility_evidence"] = copy.deepcopy(eligibility["allowed_pair"]["state"]["evidence_refs"])
        eligibility["selection_policy"]["priority"] = priority
        eligibility["selection_policy"]["policy_id"] = f"schuss-selection-policy-{numeric_id:06d}"
        eligibility["unresolved_questions"] = []
        self.rehash(eligibility, "eligibility")
        return eligibility

    def test_production_closure_is_valid_but_selection_is_unresolved(self):
        result = VALIDATOR.validate_target_backend_build_directory(CONTRACT_ROOT, SCHEMA_ROOT, ROOT)
        self.assertEqual("valid", result.summary["status"])
        self.assertEqual([], result.summary["diagnostics"])
        self.assertEqual("unresolved", result.resolution_traces[0]["status"])
        reasons = result.resolution_traces[0]["candidates"][0]["unresolved_reasons"]
        self.assertIn("COMPATIBILITY_EVIDENCE_MISSING", reasons)
        self.assertEqual("not-run", result.summary["evidence_levels"][2]["status"])

    def test_fresh_process_summary_and_canonical_emission_are_identical(self):
        command = [sys.executable, str(TOOLS / "validate_target_backend_build_contracts.py")]
        first = subprocess.run(command, cwd=ROOT, check=True, stdout=subprocess.PIPE).stdout
        second = subprocess.run(command, cwd=ROOT, check=True, stdout=subprocess.PIPE).stdout
        self.assertEqual(first, second)
        canonical = command + ["--canonical-record", str(CONTRACT_ROOT / "compute-targets/ksoloti-core-v0.json"), "--record-kind", "target"]
        one = subprocess.run(canonical, cwd=ROOT, check=True, stdout=subprocess.PIPE).stdout
        two = subprocess.run(canonical, cwd=ROOT, check=True, stdout=subprocess.PIPE).stdout
        self.assertEqual(one, two)

    def test_schemas_are_closed_annotated_and_production_hashes_match(self):
        for kind, schema in self.schemas.items():
            self.assertEqual(False, schema["additionalProperties"], kind)
            self.assertEqual([], BASE.validate_schema_annotations(schema), kind)
            for record in self.records[kind]:
                self.assertEqual(record["content_hash"], BASE.record_content_hash(record, schema), (kind, VALIDATOR._subject(record)))

    def test_reusable_schemas_do_not_const_lock_ksoloti_identities(self):
        target = copy.deepcopy(self.target)
        target["processor"].update({"family":"rp2040","core":"cortex-m0-plus","instruction_set":"thumb","fpu":"not-present"})
        target["abi_constraints"].update({"target_triple":"arm-none-eabi","float_abi":"soft"})
        self.rehash(target, "target")
        self.assertEqual([], BASE._schema_errors(target, self.schemas["target"], self.schemas["target"]))
        environment = copy.deepcopy(self.environment_tool)
        environment["identity"]["required_identity_kind"] = "llvm-embedded-toolchain"
        self.rehash(environment, "environment")
        self.assertEqual([], BASE._schema_errors(environment, self.schemas["environment"], self.schemas["environment"]))
        backend = copy.deepcopy(self.backend)
        backend["lowering_identity"] = {"backend_kind":"native-cpp","contract_version":"native-cpp-lowering-v0"}
        backend["bridge_boundary"].update({"kind":"isolated-native-bridge","location":"legacy/native-bridge"})
        self.rehash(backend, "backend")
        self.assertEqual([], BASE._schema_errors(backend, self.schemas["backend"], self.schemas["backend"]))

    def test_set_reordering_is_invariant_but_stage_reordering_is_not(self):
        target = copy.deepcopy(self.target)
        target["memory_regions"].reverse()
        self.assertEqual(
            BASE.canonical_record_bytes(self.target, self.schemas["target"]),
            BASE.canonical_record_bytes(target, self.schemas["target"]),
        )
        backend = copy.deepcopy(self.backend)
        backend["stage_contract"][0], backend["stage_contract"][1] = backend["stage_contract"][1], backend["stage_contract"][0]
        self.assertNotEqual(
            BASE.canonical_record_bytes(self.backend, self.schemas["backend"]),
            BASE.canonical_record_bytes(backend, self.schemas["backend"]),
        )
        diagnostics = []
        VALIDATOR._validate_backends([backend], self.capability_registry, self.definitions, self.target_registry, self.environment_registry, diagnostics)
        self.assertIn("BACKEND_STAGE_ORDER_INVALID", _codes(diagnostics))

    def test_id_collision_stale_hash_and_missing_exact_member_fail(self):
        duplicate = copy.deepcopy(self.target)
        duplicate["display_name"] = "Collision fixture"
        self.rehash(duplicate, "target")
        diagnostics = []
        records = {kind: [] for kind in self.schemas}
        records["target"] = [self.target, duplicate]
        VALIDATOR._validate_structural(records, self.schemas, diagnostics)
        self.assertIn("ID_REVISION_COLLISION", _codes(diagnostics))
        stale = copy.deepcopy(self.request)
        stale["graph_reference"]["content_hash"] = "sha256:" + "0" * 64
        self.rehash(stale, "request")
        diagnostics = []
        VALIDATOR._validate_build_requests([stale], {}, {_key(self.instrument, "instrument_id"): self.instrument}, self.target_registry, self.backend_registry, diagnostics)
        self.assertIn("BUILD_REQUEST_GRAPH_REFERENCE_UNRESOLVED", _codes(diagnostics))

    def test_structural_negative_fixture_matrix(self):
        source = {
            "target": self.target,
            "request": self.request,
            "artifact": self.positive["artifact"],
            "resource": self.positive["resource_report"],
            "result": self.positive["build_result"],
            "evidence": self.positive["evidence_claims"][0],
        }
        for case in self.negative["schema_cases"]:
            with self.subTest(case=case["case_id"]):
                record = copy.deepcopy(source[case["record_kind"]])
                _set_pointer(record, case["pointer"], case["value"])
                errors = BASE._schema_errors(record, self.schemas[case["record_kind"]], self.schemas[case["record_kind"]])
                errors += VALIDATOR._schema_maximum_errors(record, self.schemas[case["record_kind"]], self.schemas[case["record_kind"]])
                self.assertTrue(errors)

    def test_capability_and_target_fail_closed_boundaries(self):
        vocabulary = copy.deepcopy(self.vocabulary)
        vocabulary["definitions"][0]["unit"] = "bytes"
        diagnostics = []
        VALIDATOR._capability_definitions([vocabulary], diagnostics)
        self.assertIn("CAPABILITY_VALUE_SHAPE_INVALID", _codes(diagnostics))

        target = copy.deepcopy(self.target)
        target["memory_regions"].append(copy.deepcopy(target["memory_regions"][0]))
        target["memory_regions"][0]["alignment_bytes"] = 3
        target["processor"]["evidence_refs"] = []
        target["capability_declarations"][0]["capability_key"] = "unknown-capability"
        diagnostics = []
        VALIDATOR._validate_targets([target], self.capability_registry, self.definitions, self.environment_registry, diagnostics)
        codes = _codes(diagnostics)
        self.assertTrue({"TARGET_MEMORY_REGION_DUPLICATE", "TARGET_MEMORY_REGION_ALIGNMENT_INVALID", "TARGET_FACT_EVIDENCE_MISSING", "CAPABILITY_UNKNOWN"} <= codes)

    def test_backend_and_eligibility_reference_rules(self):
        backend = copy.deepcopy(self.backend)
        backend["target_pairings"][0]["target_reference"]["content_hash"] = "sha256:" + "0" * 64
        backend["artifact_declarations"].append(copy.deepcopy(backend["artifact_declarations"][0]))
        diagnostics = []
        VALIDATOR._validate_backends([backend], self.capability_registry, self.definitions, self.target_registry, self.environment_registry, diagnostics)
        self.assertTrue({"BACKEND_TARGET_PAIRING_UNRESOLVED", "BACKEND_ARTIFACT_DUPLICATE"} <= _codes(diagnostics))

        eligibility = copy.deepcopy(self.eligibility)
        eligibility["contract_reference"] = _ref(BASE.load_json(CONTRACT_ROOT / "component-contracts/crossfader-audio-v0.json"), "component_contract_id")
        diagnostics = []
        VALIDATOR._validate_eligibility_records(
            [eligibility], {_key(self.binding, "implementation_id"): self.binding},
            {_key(self.contract, "component_contract_id"): self.contract}, self.target_registry,
            self.backend_registry, self.definitions, {}, diagnostics,
        )
        self.assertTrue({"ELIGIBILITY_CONTRACT_REFERENCE_UNRESOLVED", "ELIGIBILITY_BINDING_CONTRACT_MISMATCH"} <= _codes(diagnostics))

    def test_resolver_distinguishes_selected_unsupported_unresolved_ambiguous_and_override(self):
        bindings = {_key(self.binding, "implementation_id"): self.binding}
        supported = self.supported_eligibility()
        target = self.supported_target()
        selected = VALIDATOR.resolve_graph_bindings(self.graph, target, self.backend, [supported], bindings, self.definitions)
        self.assertEqual("selected", selected[0]["status"])
        self.assertEqual("unsupported", VALIDATOR.resolve_graph_bindings(self.graph, target, self.backend, [], bindings, self.definitions)[0]["status"])
        self.assertEqual("unresolved", VALIDATOR.resolve_graph_bindings(self.graph, self.target, self.backend, [self.eligibility], bindings, self.definitions)[0]["status"])
        tie = self.supported_eligibility(900002, 100)
        self.assertEqual("ambiguous", VALIDATOR.resolve_graph_bindings(self.graph, target, self.backend, [supported, tie], bindings, self.definitions)[0]["status"])
        override = {"override_id": "build-override-900001", "node_id": "graph-node-000001", "mode": "select-only-if-eligible", "binding_reference": _ref(self.binding, "implementation_id")}
        self.assertEqual("selected", VALIDATOR.resolve_graph_bindings(self.graph, target, self.backend, [supported, tie], bindings, self.definitions, [override])[0]["status"])
        override["binding_reference"] = {"implementation_id": "schuss-implementation-999999", "revision": 1, "content_hash": "sha256:" + "9" * 64}
        self.assertEqual("invalid-override", VALIDATOR.resolve_graph_bindings(self.graph, target, self.backend, [supported], bindings, self.definitions, [override])[0]["status"])

    def test_build_request_instrument_asset_override_and_stop_rules(self):
        graph_registry = {_key(self.graph, "graph_id"): self.graph}
        instrument_registry = {_key(self.instrument, "instrument_id"): self.instrument}
        request = copy.deepcopy(self.request)
        request["requested_stopping_stage"] = "artifact-generation"
        request["asset_references"] = [{"asset_id":"schuss-asset-900001","revision":1,"content_hash":"sha256:"+"1"*64,"byte_sha256":"2"*64,"byte_length":1,"portable_locator":"sha256/"+"2"*64,"resolution_status":"unresolved"}]
        request["binding_overrides"] = [{"override_id":"build-override-900001","node_id":"graph-node-999999","mode":"select-only-if-eligible","binding_reference":_ref(self.binding,"implementation_id")}]
        diagnostics = []
        VALIDATOR._validate_build_requests([request], graph_registry, instrument_registry, self.target_registry, self.backend_registry, diagnostics)
        self.assertTrue({"BUILD_REQUEST_STOPPING_STAGE_INVALID", "BUILD_REQUEST_ASSET_UNRESOLVED", "BUILD_REQUEST_OVERRIDE_NODE_UNKNOWN"} <= _codes(diagnostics))

    def test_artifact_shapes_hash_separation_bytes_and_cycles(self):
        artifact = copy.deepcopy(self.positive["artifact"])
        diagnostics = []
        VALIDATOR._validate_artifacts([artifact], diagnostics)
        self.assertEqual([], diagnostics)
        payload = self.positive["artifact_bytes_utf8"].encode("utf-8")
        self.assertEqual((), VALIDATOR.validate_artifact_fixture_bytes(artifact, payload))
        self.assertEqual({"ARTIFACT_BYTE_LENGTH_MISMATCH", "ARTIFACT_BYTE_HASH_MISMATCH"}, _codes(VALIDATOR.validate_artifact_fixture_bytes(artifact, payload + b"x")))
        artifact["byte_sha256"] = artifact["content_hash"].removeprefix("sha256:")
        artifact["portable_locator"] = "sha256/" + artifact["byte_sha256"]
        diagnostics = []
        VALIDATOR._validate_artifacts([artifact], diagnostics)
        self.assertIn("ARTIFACT_DESCRIPTOR_BYTE_HASH_CONFLATED", _codes(diagnostics))

        first = copy.deepcopy(self.positive["artifact"])
        second = copy.deepcopy(first)
        second["artifact_id"] = "schuss-artifact-900002"
        second["content_hash"] = "sha256:" + "2" * 64
        first["parent_artifact_references"] = [_ref(second, "artifact_id")]
        second["parent_artifact_references"] = [_ref(first, "artifact_id")]
        diagnostics = []
        VALIDATOR._validate_artifacts([first, second], diagnostics)
        self.assertIn("ARTIFACT_REFERENCE_CYCLE", _codes(diagnostics))

    def test_resource_exact_alignment_equality_overflow_and_cross_region(self):
        report = copy.deepcopy(self.positive["resource_report"])
        target = {"compute_target_id":"schuss-compute-target-900001","revision":1,"content_hash":"sha256:"+"3"*64,"memory_regions":[{"region_id":"target-memory-region-900001","length_bytes":128,"resource_kinds":["code"]}]}
        request = {"schema_version":"build-request-v0","build_request_id":"schuss-build-request-900001","revision":1,"content_hash":"sha256:"+"2"*64}
        diagnostics = []
        VALIDATOR._validate_resource_reports([report], {_key(target,"compute_target_id"):target}, {("schuss-build-request-900001",1,"sha256:"+"2"*64):request}, diagnostics)
        self.assertEqual([], diagnostics)
        report["budget_comparisons"][0]["total_aligned_amount_bytes"] = 100
        diagnostics = []
        VALIDATOR._validate_resource_reports([report], {_key(target,"compute_target_id"):target}, {("schuss-build-request-900001",1,"sha256:"+"2"*64):request}, diagnostics)
        self.assertIn("RESOURCE_BUDGET_COMPARISON_INEXACT", _codes(diagnostics))
        for amount, outcome in ((128, "equal-to-budget"), (129, "overflow")):
            fixture = copy.deepcopy(self.positive["resource_report"])
            fixture["observations"][0]["amount_bytes"] = amount
            aligned = ((amount + 15) // 16) * 16
            fixture["budget_comparisons"][0]["total_aligned_amount_bytes"] = aligned
            fixture["budget_comparisons"][0]["outcome"] = outcome if amount == aligned else "overflow"
            diagnostics = []
            VALIDATOR._validate_resource_reports([fixture], {_key(target,"compute_target_id"):target}, {("schuss-build-request-900001",1,"sha256:"+"2"*64):request}, diagnostics)
            self.assertEqual([], diagnostics)

    def test_all_eight_evidence_levels_are_independent_and_stratified(self):
        fixture = self.positive
        result = fixture["build_result"]
        target = {"schema_version":"compute-target-v0","compute_target_id":"schuss-compute-target-900001","revision":1,"content_hash":"sha256:"+"3"*64}
        binding_r1 = {"schema_version":"implementation-binding-v0","implementation_id":"schuss-implementation-900001","revision":1,"content_hash":"sha256:"+"d"*64}
        instrument = self.instrument
        resource = fixture["resource_report"]
        stable = VALIDATOR._stable_registry([[target, binding_r1, instrument, resource, result]])
        diagnostics = []
        evidence = VALIDATOR._validate_evidence_claims(fixture["evidence_claims"], stable, {_key(result,"build_result_id"):result}, diagnostics)
        self.assertEqual([], diagnostics)
        self.assertEqual(set(range(1, 9)), {item["level"] for item in evidence.values()})

        wrong = copy.deepcopy(fixture["evidence_claims"][2])
        wrong["subject_reference"]["stage"] = "artifact-generation"
        diagnostics = []
        VALIDATOR._validate_evidence_claims([wrong], stable, {_key(result,"build_result_id"):result}, diagnostics)
        self.assertIn("EVIDENCE_LEVEL_STAGE_MISMATCH", _codes(diagnostics))

        companion = self.supported_eligibility()
        companion["binding_reference"] = {"implementation_id":"schuss-implementation-900001","revision":2,"content_hash":"sha256:"+"8"*64}
        companion["compatibility_evidence"] = [_ref(fixture["evidence_claims"][1], "evidence_claim_id")]
        diagnostics = []
        VALIDATOR._validate_evidence_stratification([companion], evidence, diagnostics)
        self.assertEqual([], diagnostics)
        companion["binding_reference"]["revision"] = 1
        diagnostics = []
        VALIDATOR._validate_evidence_stratification([companion], evidence, diagnostics)
        self.assertIn("ELIGIBILITY_EVIDENCE_REVISION_NOT_EARLIER", _codes(diagnostics))

    def test_build_result_full_shape_and_fail_closed_mutations(self):
        result = copy.deepcopy(self.positive["build_result"])
        request = {"schema_version":"build-request-v0","build_request_id":"schuss-build-request-900001","revision":1,"content_hash":"sha256:"+"2"*64,"graph_reference":{"graph_id":"schuss-graph-900001","revision":1,"content_hash":"sha256:"+"7"*64},"instrument_reference":{"status":"omitted"},"compute_target_reference":result["compute_target_reference"],"backend_reference":result["backend_reference"],"options":result["options_used"]}
        graph = {"schema_version":"dsp-graph-v0","graph_id":"schuss-graph-900001","revision":1,"content_hash":"sha256:"+"7"*64,"nodes":[{"node_id":"graph-node-900001"}]}
        target = {"schema_version":"compute-target-v0","compute_target_id":"schuss-compute-target-900001","revision":1,"content_hash":"sha256:"+"3"*64}
        tool = {"schema_version":"build-environment-v0","build_environment_id":"schuss-build-environment-900001","revision":1,"content_hash":"sha256:"+"5"*64}
        runtime = {"schema_version":"build-environment-v0","build_environment_id":"schuss-build-environment-900002","revision":1,"content_hash":"sha256:"+"6"*64}
        backend = {"schema_version":"backend-v0","backend_id":"schuss-backend-900001","revision":1,"content_hash":"sha256:"+"4"*64,"toolchain_reference":_ref(tool,"build_environment_id"),"firmware_runtime_reference":_ref(runtime,"build_environment_id"),"artifact_declarations":[{"artifact_kind":"resolution-plan","media_type":"application/vnd.schuss.resolution-plan+json","producer_stage":"implementation-resolution"}]}
        binding = {"implementation_id":"schuss-implementation-900001","revision":2,"content_hash":"sha256:"+"8"*64}
        eligibility = {"binding_eligibility_id":"schuss-binding-eligibility-900001","revision":1,"content_hash":"sha256:"+"9"*64,"binding_reference":_ref(binding,"implementation_id"),"allowed_pair":{"state":{"status":"supported"}},"selection_policy":{"policy_id":"schuss-selection-policy-900001"}}
        artifact = self.positive["artifact"]
        resource = self.positive["resource_report"]
        stable = VALIDATOR._stable_registry([[request, graph, target, backend, tool, runtime]])
        args = (
            {_key(request,"build_request_id"):request}, {_key(graph,"graph_id"):graph}, {_key(target,"compute_target_id"):target},
            {_key(backend,"backend_id"):backend}, {_key(tool,"build_environment_id"):tool, _key(runtime,"build_environment_id"):runtime},
            {_key(binding,"implementation_id"):binding}, {_key(eligibility,"binding_eligibility_id"):eligibility},
            {_key(artifact,"artifact_id"):artifact}, {_key(resource,"resource_report_id"):resource}, stable,
        )
        diagnostics = []
        VALIDATOR._validate_build_results([result], *args, diagnostics)
        self.assertEqual([], diagnostics)
        broken = copy.deepcopy(result)
        broken["stage_outcomes"][1]["status"] = "failed"
        broken["stage_outcomes"][2]["status"] = "success"
        broken["options_used"]["implicit_discovery"] = True
        broken["selected_bindings"] = []
        diagnostics = []
        VALIDATOR._validate_build_results([broken], *args, diagnostics)
        self.assertTrue({"BUILD_RESULT_STAGE_AFTER_TERMINAL", "BUILD_RESULT_OPTIONS_CHANGED", "BUILD_RESULT_NODE_SELECTION_INCOMPLETE"} <= _codes(diagnostics))

    def test_task005_task006_and_phase4a_frozen_hashes(self):
        frozen = [
            "schemas/device-profile-v0.schema.json", "schemas/instrument-v0.schema.json",
            "schemas/catalog-family-companion-v0.schema.json", "schemas/component-contract-v0.schema.json",
            "schemas/implementation-binding-v0.schema.json", "schemas/dsp-graph-v0.schema.json",
            "contracts/device-profiles/gills-minimal-v0.json", "contracts/instruments/blend-reference-v0-r2.json",
            "contracts/instruments/blend-reference-v0.json", "contracts/catalog-families/crossfader-v1.json",
            "contracts/component-contracts/crossfader-audio-v0.json", "contracts/component-contracts/crossfader-control-v0.json",
            "contracts/component-contracts/crossfader-mixed-v0.json", "contracts/implementation-bindings/crossfader-audio-legacy-v0.json",
            "contracts/implementation-bindings/crossfader-control-legacy-v0.json", "contracts/implementation-bindings/crossfader-mixed-legacy-v0.json",
            "contracts/graphs/blend-crossfader-v0.json", "catalog/sources.lock.json",
            "catalog/overlays/phase-4a-semantic-catalog-v0/catalog.json",
        ]
        for relative in frozen:
            with self.subTest(path=relative):
                committed = subprocess.run(["git", "show", f"HEAD:{relative}"], cwd=ROOT, check=True, stdout=subprocess.PIPE).stdout
                self.assertEqual(committed, (ROOT / relative).read_bytes())


if __name__ == "__main__":
    unittest.main()
