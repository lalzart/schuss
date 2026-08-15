import ast
import copy
import hashlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools/contracts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from packages.schuss_core import (
    canonical_result_bytes,
    dispatch_operation,
    load_repository_context,
)
from packages.schuss_core import control_plane
from packages.schuss_core.cli import run as run_cli

import validator_core as core


FIXTURE_PATH = (
    ROOT
    / "tools/contracts/tests/fixtures/task008-operation-requests.json"
)
POSITIVE_PATH = (
    ROOT
    / "tools/contracts/tests/fixtures/target-backend-build-positive-fixtures.json"
)
CLI = ROOT / "bin/schuss"


def _ref(record, id_field):
    return {
        id_field: record[id_field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def _tree_hashes(root):
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


class Task008ControlPlaneTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = load_repository_context(ROOT)
        cls.fixtures = core.load_json(FIXTURE_PATH)
        cls.positive = core.load_json(POSITIVE_PATH)

    def dispatch(self, fixture_name, context=None):
        return dispatch_operation(
            copy.deepcopy(self.fixtures[fixture_name]),
            self.context if context is None else context,
        )

    def supported_context(self):
        target_record = copy.deepcopy(self.context.records["target"][0])
        source_evidence = copy.deepcopy(
            target_record["processor"]["evidence_refs"][:1]
        )
        for declaration in target_record["capability_declarations"]:
            declaration["state"] = {
                "status": "supported",
                "value": True,
                "evidence_level": 2,
                "evidence_refs": source_evidence,
            }
        target_record["content_hash"] = core.record_content_hash(
            target_record, self.context.schemas["target"]
        )

        backend = copy.deepcopy(self.context.records["backend"][0])
        for pairing in backend["target_pairings"]:
            pairing["target_reference"] = _ref(
                target_record, "compute_target_id"
            )
        backend["content_hash"] = core.record_content_hash(
            backend, self.context.schemas["backend"]
        )

        eligibility = copy.deepcopy(self.context.records["eligibility"][0])
        eligibility["allowed_pair"]["target_reference"] = _ref(
            target_record, "compute_target_id"
        )
        eligibility["allowed_pair"]["backend_reference"] = _ref(
            backend, "backend_id"
        )
        evidence_reference = _ref(
            self.positive["evidence_claims"][1], "evidence_claim_id"
        )
        eligibility["allowed_pair"]["state"] = {
            "status": "supported",
            "evidence_level": 2,
            "evidence_refs": [evidence_reference],
        }
        eligibility["compatibility_evidence"] = [evidence_reference]
        eligibility["unresolved_questions"] = []
        eligibility["content_hash"] = core.record_content_hash(
            eligibility, self.context.schemas["eligibility"]
        )

        request = copy.deepcopy(self.context.records["request"][0])
        request["compute_target_reference"] = _ref(
            target_record, "compute_target_id"
        )
        request["backend_reference"] = _ref(backend, "backend_id")
        request["content_hash"] = core.record_content_hash(
            request, self.context.schemas["request"]
        )
        context = self.context.with_records(
            target=[target_record],
            backend=[backend],
            eligibility=[eligibility],
            request=[request],
            evidence=self.positive["evidence_claims"],
        )
        operation = copy.deepcopy(self.fixtures["build_resolve"])
        operation["payload"]["build_request_reference"] = _ref(
            request, "build_request_id"
        )
        return context, request, operation

    def test_validator_dependency_direction_is_exactly_one_way(self):
        domain_names = {
            "device_instrument_rules",
            "component_graph_rules",
            "target_backend_build_rules",
        }
        for name in sorted(domain_names):
            tree = ast.parse((TOOLS / f"{name}.py").read_text(encoding="utf-8"))
            imports = {
                alias.name
                for node in ast.walk(tree)
                if isinstance(node, ast.Import)
                for alias in node.names
            }
            imports |= {
                node.module
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.module
            }
            self.assertIn("validator_core", imports)
            self.assertFalse(imports & (domain_names - {name}))
        aggregate_tree = ast.parse(
            (TOOLS / "aggregate_validator.py").read_text(encoding="utf-8")
        )
        aggregate_imports = {
            alias.name
            for node in ast.walk(aggregate_tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        self.assertTrue(domain_names <= aggregate_imports)

    def test_all_legacy_validator_stdout_bytes_are_preserved(self):
        expected = {
            "validate_device_instrument_contracts.py": (
                684,
                "254a77c534c911da759a21e438544b4b0e69e16093307e0fc269a0857b6d3af6",
            ),
            "validate_component_graph_contracts.py": (
                1069,
                "d295106d38cdf9075a85d9e1a803b5df23e3ffbbe934dceb3cec9194b59ce6af",
            ),
            "validate_target_backend_build_contracts.py": (
                1964,
                "7a898b3409e5ad7ef02eab1246f87756cc2af7cbd512d72f9a5eb43b1573a3a2",
            ),
        }
        for filename, (length, digest) in expected.items():
            with self.subTest(filename=filename):
                output = subprocess.run(
                    [sys.executable, str(TOOLS / filename)],
                    cwd=ROOT,
                    check=True,
                    stdout=subprocess.PIPE,
                ).stdout
                self.assertEqual(length, len(output))
                self.assertEqual(digest, hashlib.sha256(output).hexdigest())

    def test_operation_schemas_are_versioned_closed_and_target_neutral(self):
        request_schema = self.context.schemas["operation_request"]
        result_schema = self.context.schemas["operation_result"]
        self.assertEqual([], core.validate_schema_annotations(request_schema))
        self.assertEqual([], core.validate_schema_annotations(result_schema))
        self.assertFalse(result_schema["additionalProperties"])
        for branch in request_schema["oneOf"]:
            resolved = core.resolve_schema(branch, request_schema)
            self.assertFalse(resolved["additionalProperties"])
            self.assertFalse(
                resolved["properties"]["payload"]["additionalProperties"]
            )
        text = core.canonical_json(request_schema) + core.canonical_json(result_schema)
        for forbidden in ("ksoloti", "stm32", "arm-none-eabi", "legacy-ksoloti"):
            self.assertNotIn(forbidden, text.lower())

    def test_records_validate_composes_all_rule_modules(self):
        result = self.dispatch("records_validate")
        self.assertEqual("success", result["status"])
        summaries = result["value"]["summaries"]
        self.assertEqual(
            {
                "device_instrument_rules",
                "component_graph_rules",
                "target_backend_build_rules",
                "aggregate_validator",
            },
            set(summaries),
        )
        self.assertTrue(all(summary["status"] != "invalid" for summary in summaries.values()))

    def test_graph_inspect_returns_exact_target_independent_closure(self):
        result = self.dispatch("graph_inspect")
        self.assertEqual("success", result["status"])
        value = result["value"]
        self.assertEqual("not-evaluated", value["selection_status"])
        self.assertEqual("not-run", value["lowering_status"])
        self.assertEqual(1, len(value["component_contract_closure"]))
        self.assertNotIn("implementation_id", core.canonical_json(value))
        self.assertNotIn("backend_id", core.canonical_json(value))

    def test_build_resolve_reports_complete_uncertainty_without_selection(self):
        result = self.dispatch("build_resolve")
        self.assertEqual("unresolved", result["status"])
        trace = result["value"]["resolution_traces"][0]
        self.assertEqual("unresolved", trace["status"])
        self.assertIsNone(trace["selected_binding_reference"])
        self.assertIsNone(result["value"]["backend_invocation"])
        candidate = trace["candidates"][0]
        self.assertIn("exclusion_reasons", candidate)
        self.assertIn("unresolved_reasons", candidate)
        self.assertIn("COMPATIBILITY_EVIDENCE_MISSING", candidate["unresolved_reasons"])

    def test_selected_resolution_exposes_only_the_non_executable_task009_seam(self):
        context, request, operation = self.supported_context()
        result = dispatch_operation(operation, context)
        self.assertEqual("success", result["status"])
        seam = result["value"]["backend_invocation"]
        self.assertEqual(request, seam["accepted_build_request"])
        self.assertEqual("ready-for-backend-invocation", seam["status"])
        self.assertEqual("implementation-resolution", seam["boundary"]["completed_stage"])
        self.assertEqual("backend-lowering", seam["boundary"]["next_stage"])
        self.assertEqual("not-run", seam["boundary"]["next_stage_status"])
        self.assertEqual("absent", seam["boundary"]["executable_handler_status"])
        self.assertEqual("selected", seam["resolution_traces"][0]["status"])

    def test_graph_transaction_is_deterministic_atomic_and_not_persisted(self):
        request = copy.deepcopy(self.fixtures["graph_transact_noop"])
        before = copy.deepcopy(self.context.records["graphs"])
        first = dispatch_operation(request, self.context)
        second = dispatch_operation(copy.deepcopy(request), self.context)
        self.assertEqual("success", first["status"])
        self.assertEqual(
            canonical_result_bytes(first, self.context),
            canonical_result_bytes(second, self.context),
        )
        proposed = first["value"]["proposed_graph"]
        self.assertEqual(2, proposed["revision"])
        self.assertEqual("not-written", first["value"]["persistence_status"])
        self.assertEqual(before, self.context.records["graphs"])

        failed = copy.deepcopy(request)
        failed["payload"]["edits"] = [
            request["payload"]["edits"][0],
            {"edit": "remove-node", "node_id": "graph-node-999999"},
        ]
        failure = dispatch_operation(failed, self.context)
        self.assertEqual("invalid", failure["status"])
        self.assertIsNone(failure["value"])
        self.assertEqual(before, self.context.records["graphs"])

    def test_graph_transaction_rejects_stale_base_and_full_task006_failure(self):
        stale = copy.deepcopy(self.fixtures["graph_transact_noop"])
        stale["payload"]["base_content_hash"] = "sha256:" + "0" * 64
        result = dispatch_operation(stale, self.context)
        self.assertEqual("conflict", result["status"])
        self.assertEqual("OPERATION_BASE_HASH_STALE", result["diagnostics"][0]["code"])
        self.assertIsNone(result["value"])

        invalid = copy.deepcopy(self.fixtures["graph_transact_noop"])
        invalid["payload"]["edits"] = invalid["payload"]["edits"][:1]
        result = dispatch_operation(invalid, self.context)
        self.assertEqual("invalid", result["status"])
        self.assertIsNone(result["value"])
        self.assertIn("GRAPH_REQUIRED_INLET_UNDRIVEN", {item["code"] for item in result["diagnostics"]})

    def test_all_six_transaction_edit_forms_are_bounded(self):
        graph = copy.deepcopy(self.context.records["graphs"][0])
        added_node = copy.deepcopy(graph["nodes"][0])
        added_node["node_id"] = "graph-node-000002"
        connection = {
            "connection_id": "graph-connection-000001",
            "source": {"node_id": "graph-node-000001", "facet_id": "component-port-000004"},
            "destination": {"node_id": "graph-node-000002", "facet_id": "component-port-000001"},
        }
        edits = [
            {"edit": "add-node", "node": added_node},
            {"edit": "add-connection", "connection": connection},
            {"edit": "set-node-parameter", "node_id": "graph-node-000002", "facet_id": "component-parameter-000001", "value": "0.5"},
            {"edit": "set-node-attribute", "node_id": "graph-node-000002", "facet_id": "component-attribute-000001", "value": "fixture"},
            {"edit": "remove-connection", "connection_id": "graph-connection-000001"},
            {"edit": "remove-node", "node_id": "graph-node-000002"},
        ]
        for edit in edits:
            control_plane._apply_edit(graph, edit)
        self.assertEqual(self.context.records["graphs"][0]["nodes"], graph["nodes"])
        self.assertEqual([], graph["connections"])

        unsupported = copy.deepcopy(self.fixtures["graph_transact_noop"])
        unsupported["payload"]["edits"][0]["edit"] = "rename-node"
        result = dispatch_operation(unsupported, self.context)
        self.assertEqual("invalid", result["status"])
        self.assertEqual("OPERATION_REQUEST_INVALID", result["diagnostics"][0]["code"])

    def test_api_and_cli_emit_byte_identical_results_and_stable_domain_exit(self):
        for fixture_name, expected_exit in (("records_validate", 0), ("build_resolve", 1)):
            with self.subTest(fixture=fixture_name), tempfile.TemporaryDirectory() as temporary:
                request = self.fixtures[fixture_name]
                request_path = Path(temporary) / "request.json"
                request_path.write_bytes(core.canonical_json(request).encode("utf-8") + b"\n")
                direct = dispatch_operation(copy.deepcopy(request), self.context)
                expected = canonical_result_bytes(direct, self.context) + b"\n"
                process = subprocess.run(
                    [str(CLI), "op", "--request", str(request_path), "--json"],
                    cwd=ROOT,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                self.assertEqual(expected_exit, process.returncode)
                self.assertEqual(expected, process.stdout)
                self.assertEqual(b"", process.stderr)

    def test_cli_usage_parse_and_internal_exit_contract(self):
        usage = subprocess.run(
            [str(CLI), "op", "--request", "-"],
            cwd=ROOT,
            input=b"{}\n",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(2, usage.returncode)
        self.assertEqual(b"", usage.stdout)
        self.assertIn(b"usage error", usage.stderr)

        malformed = subprocess.run(
            [str(CLI), "op", "--request", "-", "--json"],
            cwd=ROOT,
            input=b"{\n",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(2, malformed.returncode)
        self.assertEqual(b"", malformed.stdout)
        self.assertIn(b"request input failed", malformed.stderr)

        request_bytes = (
            core.canonical_json(self.fixtures["records_validate"]).encode("utf-8")
            + b"\n"
        )
        stdout = io.BytesIO()
        stderr = io.StringIO()

        def fail_context():
            raise RuntimeError("fixture adapter fault")

        code = run_cli(
            ["op", "--request", "-", "--json"],
            io.BytesIO(request_bytes),
            stdout,
            stderr,
            fail_context,
        )
        self.assertEqual(3, code)
        self.assertEqual(b"", stdout.getvalue())
        self.assertIn("internal operation failure", stderr.getvalue())

    def test_results_ignore_record_and_filesystem_enumeration_order(self):
        reversed_context = self.context.with_records(
            **{
                name: reversed(values)
                for name, values in self.context.records.items()
            }
        )
        for fixture_name in ("graph_inspect", "build_resolve"):
            original = self.dispatch(fixture_name)
            reordered = self.dispatch(fixture_name, reversed_context)
            self.assertEqual(
                canonical_result_bytes(original, self.context),
                canonical_result_bytes(reordered, reversed_context),
            )

        def reverse_enumerator(root, child):
            return reversed(list((root / child).glob("*.json")))

        filesystem_context = load_repository_context(ROOT, reverse_enumerator)
        original = self.dispatch("records_validate")
        reordered = self.dispatch("records_validate", filesystem_context)
        self.assertEqual(
            canonical_result_bytes(original, self.context),
            canonical_result_bytes(reordered, filesystem_context),
        )

    def test_operations_do_not_mutate_filesystem_or_production_records(self):
        before_files = _tree_hashes(ROOT / "contracts")
        before_records = copy.deepcopy(self.context.records)
        for fixture_name in (
            "records_validate",
            "graph_inspect",
            "build_resolve",
            "graph_transact_noop",
        ):
            self.dispatch(fixture_name)
        self.assertEqual(before_files, _tree_hashes(ROOT / "contracts"))
        self.assertEqual(before_records, self.context.records)

    def test_task007_build_request_and_production_graph_bytes_are_frozen(self):
        request_path = ROOT / "contracts/build-requests/blend-validation-v0.json"
        graph_path = ROOT / "contracts/graphs/blend-crossfader-v0.json"
        self.assertEqual(
            "43f9b680116f2ac17e2aa2b164e54bd0b9bcc26582ca5272c14ca620836bac6e",
            hashlib.sha256(request_path.read_bytes()).hexdigest(),
        )
        self.assertEqual(
            "c21b9b2d79a5a6e10d8cd2dd5ca4959ff1556949fd1a1c411d0323ab605c4c15",
            hashlib.sha256(graph_path.read_bytes()).hexdigest(),
        )
        request = core.load_json(request_path)
        self.assertEqual(
            "sha256:0ba7e74977ac7ebcf50cb73826c349040d998541f688bb32cbedf88140259e95",
            request["content_hash"],
        )

    def test_control_plane_contains_no_executable_backend_or_product_cli_work(self):
        tree = ast.parse(
            (ROOT / "packages/schuss_core/control_plane.py").read_text(encoding="utf-8")
        )
        imports = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        self.assertNotIn("subprocess", imports)
        calls = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertFalse({"compile", "exec", "eval"} & calls)
        self.assertTrue(CLI.stat().st_mode & 0o111)


if __name__ == "__main__":
    unittest.main()
