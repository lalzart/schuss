from __future__ import annotations

import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools/contracts"
for value in (ROOT, TOOLS):
    if str(value) not in sys.path:
        sys.path.insert(0, str(value))

from packages.schuss_core.build_execution import (
    CancellationToken,
    ExecutionService,
    HandlerRegistration,
    descriptor_content_hash,
    execute_build,
    handler_reference,
)
from packages.schuss_core.compiler_front_half import CompilationContext, plan_build
from packages.schuss_core.control_plane import (
    canonical_result_bytes,
    dispatch_operation,
    load_repository_context,
)
import validator_core as core


RECORD_SET = ROOT / "contracts/record-sets/task014-build-execution-v1.json"


def _adapter_module():
    path = ROOT / "legacy/ksoloti-bridge/task011c_adapter.py"
    spec = importlib.util.spec_from_file_location("task014_test_adapter", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Task014BuildExecutionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = load_repository_context(record_set_path=RECORD_SET)
        cls.request = next(
            item for item in cls.context.records["request"]
            if item["build_request_id"] == "schuss-build-request-000002"
            and item["revision"] == 2
        )
        cls.request_reference = {
            key: cls.request[key]
            for key in ("build_request_id", "revision", "content_hash")
        }
        cls.compilation_context = CompilationContext.from_values(
            build_request_reference=cls.request_reference,
            closure_source={
                "kind": "record-set",
                "record_set_reference": cls.context.record_set_reference,
            },
            records=cls.context.records,
            schemas=cls.context.schemas,
        )
        cls.descriptor = _adapter_module().descriptor()

    @staticmethod
    def _fake_handler(request):
        request.output_root.mkdir()
        payload = b"task014-fake-artifact\n"
        (request.output_root / "artifact.bin").write_bytes(payload)
        digest = hashlib.sha256(payload).hexdigest()
        return {
            "status": "success",
            "stage_outcomes": [
                {"stage": stage, "status": "success"}
                for stage in (
                    "backend-lowering",
                    "artifact-generation",
                    "target-compile-link",
                )
            ],
            "artifacts": [{
                "artifact_kind": "test-artifact",
                "media_type": "application/octet-stream",
                "producer_stage": "target-compile-link",
                "byte_sha256": digest,
                "byte_length": len(payload),
                "portable_locator": "sha256/" + digest,
            }],
            "evidence_level": 5,
        }

    def _service(self, root: Path, handler=None, descriptor=None, duplicates=1):
        registration = HandlerRegistration(
            copy.deepcopy(descriptor or self.descriptor),
            handler or self._fake_handler,
        )
        return ExecutionService.from_values(
            [registration] * duplicates, root
        )

    def _execute(self, root: Path, **kwargs):
        return execute_build(
            self.compilation_context,
            handler_reference(self.descriptor),
            self._service(root),
            execution_intent=True,
            **kwargs,
        )

    def test_descriptor_is_closed_hashed_and_schema_valid(self):
        schema = core.load_json(ROOT / "schemas/build-handler-descriptor-v0.schema.json")
        self.assertEqual([], core.schema_errors(self.descriptor, schema, schema))
        self.assertEqual(self.descriptor["content_hash"], descriptor_content_hash(self.descriptor))
        self.assertEqual(self.descriptor["content_hash"], core.record_content_hash(self.descriptor, schema))

    def test_success_plans_once_publishes_and_validates(self):
        calls = []
        def planner(value):
            calls.append(value)
            return plan_build(value)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "output"
            result = execute_build(
                self.compilation_context,
                handler_reference(self.descriptor),
                self._service(root),
                execution_intent=True,
                plan_function=planner,
            )
            self.assertEqual(1, len(calls))
            self.assertEqual("success", result["status"])
            self.assertEqual("published", result["output_publication"])
            self.assertTrue((root / "artifact.bin").is_file())
            self.assertEqual(list(range(1, 7)), [item["ordinal"] for item in result["progress"]])
            schema = core.load_json(ROOT / "schemas/build-execution-result-v0.schema.json")
            self.assertEqual([], core.schema_errors(result, schema, schema))

    def test_two_fresh_roots_have_identical_portable_result(self):
        with tempfile.TemporaryDirectory() as temporary:
            first = self._execute(Path(temporary) / "a")
            second = self._execute(Path(temporary) / "root-with-longer-name-b")
        self.assertEqual(core.canonical_json(first), core.canonical_json(second))
        self.assertNotIn(temporary, core.canonical_json(first))

    def test_explicit_intent_is_required_before_planning(self):
        calls = []
        with tempfile.TemporaryDirectory() as temporary:
            result = execute_build(
                self.compilation_context,
                handler_reference(self.descriptor),
                self._service(Path(temporary) / "output"),
                execution_intent=False,
                plan_function=lambda value: calls.append(value),
            )
        self.assertEqual([], calls)
        self.assertEqual("invalid", result["status"])
        self.assertEqual("BUILD_EXECUTION_INTENT_REQUIRED", result["diagnostics"][0]["code"])

    def test_cancel_before_planning(self):
        calls = []
        with tempfile.TemporaryDirectory() as temporary:
            result = execute_build(
                self.compilation_context,
                handler_reference(self.descriptor),
                self._service(Path(temporary) / "output"),
                execution_intent=True,
                cancellation_token=CancellationToken(lambda: True),
                plan_function=lambda value: calls.append(value),
            )
        self.assertEqual([], calls)
        self.assertEqual("cancelled", result["status"])

    def test_cancel_after_planning_preserves_level_two_only(self):
        decisions = iter((False, True))
        with tempfile.TemporaryDirectory() as temporary:
            result = execute_build(
                self.compilation_context,
                handler_reference(self.descriptor),
                self._service(Path(temporary) / "output"),
                execution_intent=True,
                cancellation_token=CancellationToken(lambda: next(decisions)),
            )
            self.assertFalse((Path(temporary) / "output").exists())
        self.assertEqual("cancelled", result["status"])
        self.assertEqual(["passed", "passed"], [item["status"] for item in result["evidence_levels"][:2]])
        self.assertTrue(all(item["status"] == "not-run" for item in result["evidence_levels"][2:]))

    def test_missing_and_duplicate_handlers_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            empty = ExecutionService.from_values((), Path(temporary) / "empty")
            missing = execute_build(
                self.compilation_context, handler_reference(self.descriptor), empty,
                execution_intent=True,
            )
            duplicate = execute_build(
                self.compilation_context, handler_reference(self.descriptor),
                self._service(Path(temporary) / "duplicate", duplicates=2),
                execution_intent=True,
            )
        self.assertEqual("unavailable", missing["status"])
        self.assertEqual("unavailable", duplicate["status"])
        self.assertEqual("BUILD_HANDLER_NOT_EXACT", missing["diagnostics"][0]["code"])

    def test_wrong_backend_descriptor_fails_before_handler(self):
        changed = copy.deepcopy(self.descriptor)
        changed["backend_reference"]["revision"] = 2
        changed["backend_reference"]["content_hash"] = "sha256:" + "1" * 64
        changed["content_hash"] = descriptor_content_hash(changed)
        with tempfile.TemporaryDirectory() as temporary:
            result = execute_build(
                self.compilation_context, handler_reference(changed),
                self._service(Path(temporary) / "output", descriptor=changed),
                execution_intent=True,
            )
        self.assertEqual("unavailable", result["status"])

    def test_existing_or_symlink_output_is_never_replaced(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "existing"
            root.mkdir()
            marker = root / "marker"
            marker.write_text("keep", encoding="utf-8")
            existing = self._execute(root)
            target = Path(temporary) / "target"
            target.mkdir()
            link = Path(temporary) / "link"
            link.symlink_to(target, target_is_directory=True)
            symlink = self._execute(link)
            self.assertEqual("keep", marker.read_text(encoding="utf-8"))
            self.assertTrue(link.is_symlink())
        self.assertEqual("BUILD_OUTPUT_ROOT_EXISTS", existing["diagnostics"][0]["code"])
        self.assertEqual("BUILD_OUTPUT_ROOT_EXISTS", symlink["diagnostics"][0]["code"])

    def test_handler_failure_cleans_owned_staging_and_publishes_nothing(self):
        def failing(request):
            request.output_root.mkdir()
            (request.output_root / "partial").write_bytes(b"partial")
            raise RuntimeError("injected handler failure")
        with tempfile.TemporaryDirectory() as temporary:
            final = Path(temporary) / "output"
            result = execute_build(
                self.compilation_context, handler_reference(self.descriptor),
                self._service(final, handler=failing), execution_intent=True,
            )
            self.assertFalse(final.exists())
            self.assertEqual([], list(Path(temporary).iterdir()))
        self.assertEqual("failed", result["status"])
        self.assertEqual("not-published", result["output_publication"])

    def test_unresolved_plan_does_not_invoke_handler(self):
        old = next(
            item for item in self.context.records["request"]
            if item["build_request_id"] == "schuss-build-request-000002"
            and item["revision"] == 1
        )
        reference = {key: old[key] for key in ("build_request_id", "revision", "content_hash")}
        compilation = CompilationContext.from_values(
            build_request_reference=reference,
            closure_source={"kind": "record-set", "record_set_reference": self.context.record_set_reference},
            records=self.context.records,
            schemas=self.context.schemas,
        )
        calls = []
        with tempfile.TemporaryDirectory() as temporary:
            service = self._service(Path(temporary) / "output", handler=lambda value: calls.append(value))
            result = execute_build(
                compilation, handler_reference(self.descriptor), service,
                execution_intent=True,
            )
        self.assertEqual([], calls)
        self.assertEqual("unresolved", result["status"])

    def test_operation_direct_and_process_unavailable_parity(self):
        request = {
            "schema_version": "schuss-operation-request-v5",
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": "build.execute",
            "payload": {
                "build_request_reference": self.request_reference,
                "handler_reference": handler_reference(self.descriptor),
                "output_locator": "build-output",
                "execution_intent": True,
            },
        }
        direct = dispatch_operation(request, self.context)
        self.assertEqual("unavailable", direct["status"])
        with tempfile.TemporaryDirectory() as temporary:
            request_path = Path(temporary) / "request.json"
            request_path.write_bytes(core.canonical_json(request).encode("utf-8") + b"\n")
            process = subprocess.run(
                [str(ROOT / "bin/schuss"), "op", "--request", str(request_path), "--record-set", str(RECORD_SET), "--json"],
                cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            )
        self.assertEqual(1, process.returncode, process.stderr.decode())
        self.assertEqual(canonical_result_bytes(direct, self.context) + b"\n", process.stdout)

    def test_product_plan_and_additive_completion(self):
        process = subprocess.run(
            [str(ROOT / "bin/schuss"), "build", "plan", "schuss-build-request-000002@2", "--json"],
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        self.assertEqual(0, process.returncode, process.stderr.decode())
        self.assertEqual("success", json.loads(process.stdout)["status"])
        completion = subprocess.run(
            [str(ROOT / "bin/schuss"), "build", "completion", "zsh"],
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        self.assertEqual(0, completion.returncode)
        self.assertIn(b"plan execute", completion.stdout)

    def test_product_execute_requires_explicit_intent(self):
        process = subprocess.run(
            [str(ROOT / "bin/schuss"), "build", "execute", "schuss-build-request-000002@2", "--output-root", "unused"],
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        self.assertEqual(2, process.returncode)
        self.assertIn(b"--execute", process.stderr)


if __name__ == "__main__":
    unittest.main()
