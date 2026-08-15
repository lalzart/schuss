import ast
import copy
import hashlib
import io
import json
import os
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
    canonical_result_bytes,
    dispatch_operation,
    load_repository_context,
)
from packages.schuss_core import cli as cli_module
from packages.schuss_core.cli import run as run_cli
from packages.schuss_core.project_cli import (
    project_graph_commit_request,
    project_inspect_request,
)
from packages.schuss_core.project_service import (
    HEAD_LOCATOR,
    LOCK_LOCATOR,
    ProjectError,
    ProjectService,
    with_project_schemas,
)

import validator_core as core


RECORD_SET = ROOT / "contracts/record-sets/task011c-executed-v1.json"
FIXTURE = ROOT / "fixtures/task012a/minimal-project"
EDITS = ROOT / "tools/contracts/tests/fixtures/task012a-graph-edits.json"
NEGATIVE_FIXTURES = (
    ROOT / "tools/contracts/tests/fixtures/task012a-project-negative-fixtures.json"
)
SUCCESSOR_GOLDEN = (
    ROOT / "tools/contracts/tests/fixtures/task012a-successor-golden-hashes.json"
)
CLI = ROOT / "bin/schuss"


def _ref(record, id_field):
    return {
        id_field: record[id_field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def _governed_hashes(workspace):
    return {
        path.relative_to(workspace).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in sorted(Path(workspace).rglob("*"))
        if path.is_file() and ".schuss" not in path.parts
    }


class InjectedFailure(RuntimeError):
    pass


class Task012AProjectTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = with_project_schemas(
            load_repository_context(ROOT, record_set_path=RECORD_SET), ROOT
        )
        cls.graph = next(
            item
            for item in cls.context.records["graphs"]
            if item["graph_id"] == "schuss-graph-000002"
        )
        cls.instrument = next(
            item
            for item in cls.context.records["instruments"]
            if item["instrument_id"] == "schuss-instrument-000002"
        )
        cls.build_request = next(
            item
            for item in cls.context.records["request"]
            if item["build_request_id"] == "schuss-build-request-000002"
            and item["revision"] == 2
        )
        cls.edits = core.load_json(EDITS)
        cls.negative = core.load_json(NEGATIVE_FIXTURES)
        cls.successor_golden = core.load_json(SUCCESSOR_GOLDEN)

    def workspace(self, temporary):
        path = Path(temporary) / "workspace"
        shutil.copytree(FIXTURE, path)
        return path

    def loaded(self, workspace, **kwargs):
        service = ProjectService(workspace, **kwargs)
        return service, service.load()

    def commit_request(self, loaded, **changes):
        request = project_graph_commit_request(
            _ref(loaded.manifest, "project_id"),
            copy.deepcopy(loaded.manifest["primary_graph_reference"]),
            copy.deepcopy(self.edits),
        )
        request["payload"].update(changes)
        return request

    def rewrite_current_manifest(self, workspace, mutate):
        head_path = Path(workspace) / HEAD_LOCATOR
        head = core.load_json(head_path)
        manifest_path = Path(workspace) / head["project_manifest_locator"]
        manifest = core.load_json(manifest_path)
        mutate(manifest)
        schema = self.context.schemas["project"]
        manifest["content_hash"] = core.record_content_hash(manifest, schema)
        manifest = core.canonicalize_with_schema(manifest, schema, schema)
        manifest_bytes = core.canonical_json(manifest).encode() + b"\n"
        manifest_path.write_bytes(manifest_bytes)
        head["accepted_project_reference"] = _ref(manifest, "project_id")
        head["project_manifest_byte_sha256"] = hashlib.sha256(
            manifest_bytes
        ).hexdigest()
        head_schema = self.context.schemas["workspace_head"]
        head = core.canonicalize_with_schema(head, head_schema, head_schema)
        head_path.write_bytes(core.canonical_json(head).encode() + b"\n")

    def test_schemas_are_closed_versioned_and_portable(self):
        for name in (
            "project",
            "workspace_head",
            "project_write_plan",
            "workspace_lock",
            "workspace_recovery",
            "operation_request_v3",
            "operation_result_v3",
        ):
            with self.subTest(schema=name):
                schema = self.context.schemas[name]
                self.assertEqual([], core.validate_schema_annotations(schema))
                text = core.canonical_json(schema)
                self.assertNotIn("/Users/", text)
                self.assertNotIn("ksoloti", text.lower())
        self.assertFalse(self.context.schemas["project"]["additionalProperties"])

    def test_positive_fixture_uses_exact_task011c_base_without_copying_it(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = self.workspace(temporary)
            service, loaded = self.loaded(workspace)
            self.assertEqual("valid", loaded.validation["status"])
            self.assertEqual(self.context.record_set_reference, loaded.context.record_set_reference)
            self.assertEqual(0, loaded.validation["owned_record_count"])
            self.assertEqual(2, loaded.validation["governed_file_count"])
            self.assertFalse((workspace / "contracts").exists())
            self.assertEqual(
                "sha256:61ebe4b3bb3ddea3a710449205f5aa5fc7bea77ff6462a2b48f2c1b1919e6f47",
                loaded.manifest["content_hash"],
            )

    def test_init_in_two_fresh_roots_has_identical_governed_bytes(self):
        outputs = []
        for _ in range(2):
            temporary = tempfile.TemporaryDirectory()
            self.addCleanup(temporary.cleanup)
            workspace = Path(temporary.name) / "different-parent" / "workspace"
            service = ProjectService(workspace, initial_context=self.context)
            request = {
                "schema_version": "schuss-operation-request-v3",
                "canonical_profile": "schuss-canonical-json-v1",
                "operation": "project.init",
                "payload": {
                    "project_id": "schuss-project-000001",
                    "base_record_set": {
                        "reference": self.context.record_set_reference,
                        "portable_locator": "contracts/record-sets/task011c-executed-v1.json",
                    },
                    "primary_graph_reference": _ref(self.graph, "graph_id"),
                    "instrument_references": [_ref(self.instrument, "instrument_id")],
                    "build_request_references": [
                        _ref(self.build_request, "build_request_id")
                    ],
                    "asset_references": [],
                },
            }
            result = dispatch_operation(request, service.context, project_service=service)
            self.assertEqual("success", result["status"])
            outputs.append(_governed_hashes(workspace))
        self.assertEqual(outputs[0], outputs[1])

    def test_copying_workspace_does_not_change_identity_or_validation(self):
        with tempfile.TemporaryDirectory() as temporary:
            first = self.workspace(temporary)
            second = Path(temporary) / "another" / "copied"
            second.parent.mkdir()
            shutil.copytree(first, second)
            _, one = self.loaded(first)
            _, two = self.loaded(second)
            self.assertEqual(one.manifest, two.manifest)
            self.assertEqual(one.validation, two.validation)
            self.assertEqual(_governed_hashes(first), _governed_hashes(second))

    def test_successful_commit_retains_exact_graph_and_project_parents(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = self.workspace(temporary)
            service, loaded = self.loaded(workspace)
            result = dispatch_operation(
                self.commit_request(loaded), service.context, project_service=service
            )
            self.assertEqual("success", result["status"])
            value = result["value"]
            self.assertEqual(2, value["project"]["revision"])
            self.assertEqual(2, value["graph"]["revision"])
            self.assertEqual(
                {"status": "included", **_ref(loaded.manifest, "project_id")},
                value["project"]["parent_reference"],
            )
            member = value["project"]["owned_members"][0]
            self.assertEqual(
                {
                    "status": "included",
                    "record_kind": "dsp-graph",
                    "stable_id": self.graph["graph_id"],
                    "revision": 1,
                    "content_hash": self.graph["content_hash"],
                },
                member["parent_reference"],
            )
            self.assertEqual("workspace-head-replaced", value["acceptance_boundary"])
            self.assertEqual(3, len(value["write_plan"]["mutations"]))
            self.assertEqual(
                self.successor_golden["project_content_hash"],
                value["project"]["content_hash"],
            )
            self.assertEqual(
                self.successor_golden["graph_content_hash"],
                value["graph"]["content_hash"],
            )
            self.assertEqual(
                self.successor_golden["write_plan_content_hash"],
                value["write_plan"]["content_hash"],
            )
            observed_files = {
                path: {
                    "byte_length": len((workspace / path).read_bytes()),
                    "byte_sha256": digest,
                }
                for path, digest in _governed_hashes(workspace).items()
            }
            self.assertEqual(
                self.successor_golden["governed_files"], observed_files
            )
            reloaded = service.load()
            self.assertEqual(value["project"], reloaded.manifest)
            self.assertEqual(value["graph"], reloaded.project_records["dsp-graph"][0])

    def test_proposal_only_graph_transact_is_still_not_written(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = self.workspace(temporary)
            before = _governed_hashes(workspace)
            service, loaded = self.loaded(workspace)
            request = {
                "schema_version": "schuss-operation-request-v1",
                "canonical_profile": "schuss-canonical-json-v1",
                "operation": "graph.transact",
                "payload": {
                    "graph_reference": loaded.manifest["primary_graph_reference"],
                    "base_content_hash": loaded.manifest["primary_graph_reference"]["content_hash"],
                    "edits": copy.deepcopy(self.edits),
                },
            }
            result = dispatch_operation(request, loaded.context)
            self.assertEqual("success", result["status"])
            self.assertEqual("not-written", result["value"]["persistence_status"])
            self.assertEqual(before, _governed_hashes(workspace))

    def test_failed_edit_and_all_stale_writers_leave_prior_project(self):
        cases = []
        with tempfile.TemporaryDirectory() as temporary:
            workspace = self.workspace(temporary)
            service, loaded = self.loaded(workspace)
            invalid = self.commit_request(loaded)
            invalid["payload"]["edits"] = [
                {"edit": "remove-node", "node_id": "graph-node-999999"}
            ]
            cases.append((invalid, "invalid"))
            stale_project = self.commit_request(loaded)
            stale_project["payload"]["expected_project_reference"]["content_hash"] = "sha256:" + "0" * 64
            cases.append((stale_project, "conflict"))
            stale_graph = self.commit_request(loaded)
            stale_graph["payload"]["graph_reference"]["content_hash"] = "sha256:" + "0" * 64
            stale_graph["payload"]["base_content_hash"] = "sha256:" + "0" * 64
            cases.append((stale_graph, "conflict"))
            before = _governed_hashes(workspace)
            for request, status in cases:
                with self.subTest(status=status, request=request):
                    result = dispatch_operation(
                        request, service.context, project_service=service
                    )
                    self.assertEqual(status, result["status"])
                    self.assertEqual(before, _governed_hashes(workspace))

    def test_missing_parent_stale_hash_extra_member_and_symlink_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = self.workspace(temporary)
            service, loaded = self.loaded(workspace)
            result = dispatch_operation(
                self.commit_request(loaded), service.context, project_service=service
            )
            self.assertEqual("success", result["status"])
            self.rewrite_current_manifest(
                workspace,
                lambda manifest: manifest.update(
                    {"parent_reference": {"status": "omitted"}}
                ),
            )
            with self.assertRaisesRegex(ProjectError, "immediately preceding"):
                ProjectService(workspace).load()

        with tempfile.TemporaryDirectory() as temporary:
            workspace = self.workspace(temporary)
            manifest = workspace / "project/revisions/schuss-project-000001-r000001.json"
            value = core.load_json(manifest)
            value["primary_graph_reference"]["content_hash"] = "sha256:" + "0" * 64
            manifest.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")
            with self.assertRaises(ProjectError):
                ProjectService(workspace).load()

        with tempfile.TemporaryDirectory() as temporary:
            workspace = self.workspace(temporary)
            orphan = workspace / "records/dsp-graphs/orphan.json"
            orphan.parent.mkdir(parents=True, exist_ok=True)
            orphan.write_text("{}\n")
            with self.assertRaisesRegex(ProjectError, "membership mismatch"):
                ProjectService(workspace).load()

        if hasattr(os, "symlink"):
            with tempfile.TemporaryDirectory() as temporary:
                workspace = self.workspace(temporary)
                manifest = workspace / "project/revisions/schuss-project-000001-r000001.json"
                outside = Path(temporary) / "outside.json"
                shutil.copyfile(manifest, outside)
                manifest.unlink()
                manifest.symlink_to(outside)
                with self.assertRaises(ProjectError) as caught:
                    ProjectService(workspace).load()
                self.assertEqual("PROJECT_SYMLINK_ESCAPE", caught.exception.code)

    def test_path_escape_and_absolute_locator_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            service = ProjectService(Path(temporary))
            for locator in ("../escape.json", "/absolute.json", "records/../escape"):
                with self.subTest(locator=locator):
                    with self.assertRaises(ProjectError):
                        service._safe_workspace_path(locator)

    def test_duplicate_collision_and_invalid_exact_reference_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = self.workspace(temporary)
            service, loaded = self.loaded(workspace)
            result = dispatch_operation(
                self.commit_request(loaded), service.context, project_service=service
            )
            self.assertEqual("success", result["status"])
            graph_path = next((workspace / "records/dsp-graphs").glob("*-r000002.json"))
            duplicate_path = workspace / "records/dsp-graphs/duplicate.json"
            shutil.copyfile(graph_path, duplicate_path)

            def duplicate(manifest):
                member = copy.deepcopy(manifest["owned_members"][0])
                member["portable_locator"] = "records/dsp-graphs/duplicate.json"
                manifest["owned_members"].append(member)

            self.rewrite_current_manifest(workspace, duplicate)
            with self.assertRaises(ProjectError) as caught:
                ProjectService(workspace).load()
            self.assertEqual("PROJECT_OWNED_IDENTITY_DUPLICATE", caught.exception.code)

        with tempfile.TemporaryDirectory() as temporary:
            workspace = self.workspace(temporary)
            base_copy = workspace / "records/dsp-graphs/base-copy.json"
            base_copy.parent.mkdir(parents=True)
            source = ROOT / "contracts/task011b/graphs/four-step-dual-sine.json"
            shutil.copyfile(source, base_copy)
            data = base_copy.read_bytes()

            def collide(manifest):
                manifest["owned_members"] = [
                    {
                        "record_kind": "dsp-graph",
                        "stable_id": self.graph["graph_id"],
                        "revision": self.graph["revision"],
                        "content_hash": self.graph["content_hash"],
                        "schema_version": self.graph["schema_version"],
                        "portable_locator": "records/dsp-graphs/base-copy.json",
                        "byte_sha256": hashlib.sha256(data).hexdigest(),
                        "parent_reference": {"status": "omitted"},
                    }
                ]

            self.rewrite_current_manifest(workspace, collide)
            with self.assertRaises(ProjectError) as caught:
                ProjectService(workspace).load()
            self.assertEqual("PROJECT_BASE_OVERLAY_COLLISION", caught.exception.code)

        with tempfile.TemporaryDirectory() as temporary:
            workspace = self.workspace(temporary)

            def stale_reference(manifest):
                manifest["instrument_references"][0]["content_hash"] = (
                    "sha256:" + "0" * 64
                )

            self.rewrite_current_manifest(workspace, stale_reference)
            with self.assertRaises(ProjectError) as caught:
                ProjectService(workspace).load()
            self.assertEqual("PROJECT_INCLUDED_REFERENCE_UNRESOLVED", caught.exception.code)

    def test_changed_expected_old_head_bytes_reject_before_acceptance(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = self.workspace(temporary)
            baseline = ProjectService(workspace).load()
            head_path = workspace / HEAD_LOCATOR
            prior_head = head_path.read_bytes()
            changed = []

            def mutate_head(label):
                if label == "before:head.publish" and not changed:
                    head_path.write_bytes(prior_head + b" ")
                    changed.append(label)

            service = ProjectService(workspace, failure_injector=mutate_head)
            result = dispatch_operation(
                self.commit_request(baseline), service.context, project_service=service
            )
            self.assertEqual("conflict", result["status"])
            self.assertEqual(
                "PROJECT_EXPECTED_OLD_BYTES_CHANGED",
                result["diagnostics"][0]["code"],
            )
            head_path.write_bytes(prior_head)
            recovered = ProjectService(
                workspace, process_alive=lambda pid: False
            ).load()
            self.assertEqual(1, recovered.manifest["revision"])

    def test_live_malformed_and_abandoned_locks_have_stable_behavior(self):
        lock = {
            "schema_version": "workspace-lock-v0",
            "owner_pid": 424242,
            "operation": "project.graph.commit",
            "recovery_locator": ".schuss/recovery/pending.json",
        }
        lock_schema = self.context.schemas["workspace_lock"]
        lock_bytes = (
            core.canonical_json(
                core.canonicalize_with_schema(lock, lock_schema, lock_schema)
            ).encode()
            + b"\n"
        )
        with tempfile.TemporaryDirectory() as temporary:
            workspace = self.workspace(temporary)
            path = workspace / LOCK_LOCATOR
            path.parent.mkdir(parents=True)
            path.write_bytes(lock_bytes)
            with self.assertRaises(ProjectError) as caught:
                ProjectService(workspace, process_alive=lambda pid: True).load()
            self.assertEqual("PROJECT_WORKSPACE_LOCKED", caught.exception.code)

        with tempfile.TemporaryDirectory() as temporary:
            workspace = self.workspace(temporary)
            path = workspace / LOCK_LOCATOR
            path.parent.mkdir(parents=True)
            path.write_text("{}\n")
            with self.assertRaises(ProjectError) as caught:
                ProjectService(workspace, process_alive=lambda pid: False).load()
            self.assertEqual("PROJECT_GOVERNED_FILE_INVALID", caught.exception.code)

        with tempfile.TemporaryDirectory() as temporary:
            workspace = self.workspace(temporary)
            path = workspace / LOCK_LOCATOR
            path.parent.mkdir(parents=True)
            path.write_bytes(lock_bytes)
            loaded = ProjectService(
                workspace, process_alive=lambda pid: False
            ).load()
            self.assertEqual("abandoned-lock-removed", loaded.recovery_status)
            self.assertFalse(path.exists())

    def test_failure_injection_proves_prior_or_successor_at_every_write_phase(self):
        boundaries = (
            "before:recovery.temp-create",
            "during:recovery.temp-write",
            "after:recovery.publish",
            "before:graph.temp-create",
            "during:graph.temp-write",
            "after:graph.publish",
            "before:project.temp-create",
            "during:project.temp-write",
            "after:project.publish",
            "before:head.temp-create",
            "during:head.temp-write",
            "before:head.publish",
            "after:head.publish",
            "before:recovery.remove",
            "before:lock.remove",
        )
        for boundary in boundaries:
            with self.subTest(boundary=boundary), tempfile.TemporaryDirectory() as temporary:
                workspace = self.workspace(temporary)
                baseline = ProjectService(workspace).load()
                fired = []

                def inject(label):
                    if label == boundary and not fired:
                        fired.append(label)
                        raise InjectedFailure(label)

                service = ProjectService(
                    workspace,
                    failure_injector=inject,
                    pid_provider=lambda: 424242,
                    process_alive=lambda pid: False,
                )
                with self.assertRaises(InjectedFailure):
                    dispatch_operation(
                        self.commit_request(baseline),
                        service.context,
                        project_service=service,
                    )
                self.assertEqual([boundary], fired)
                recovered = ProjectService(
                    workspace, process_alive=lambda pid: False
                ).load()
                self.assertIn(recovered.manifest["revision"], {1, 2})
                self.assertEqual("valid", recovered.validation["status"])
                self.assertEqual(
                    recovered.validation["governed_file_count"],
                    len(_governed_hashes(workspace)),
                )

    def test_ambiguous_recovery_never_guesses(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = self.workspace(temporary)
            baseline = ProjectService(workspace).load()

            def inject(label):
                if label == "after:graph.publish":
                    raise InjectedFailure(label)

            service = ProjectService(
                workspace,
                failure_injector=inject,
                pid_provider=lambda: 424242,
                process_alive=lambda pid: False,
            )
            with self.assertRaises(InjectedFailure):
                dispatch_operation(
                    self.commit_request(baseline),
                    service.context,
                    project_service=service,
                )
            graph = next((workspace / "records/dsp-graphs").glob("*-r000002.json"))
            graph.write_bytes(graph.read_bytes() + b" ")
            with self.assertRaises(ProjectError) as caught:
                ProjectService(workspace, process_alive=lambda pid: False).load()
            self.assertEqual("PROJECT_RECOVERY_AMBIGUOUS", caught.exception.code)

    def test_direct_process_ergonomic_json_and_reload_results_agree(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = self.workspace(temporary)
            request = project_inspect_request()
            service = ProjectService(workspace)
            direct = dispatch_operation(
                request, service.context, project_service=service
            )
            expected = canonical_result_bytes(direct, service.context) + b"\n"
            request_bytes = core.canonical_json(request).encode() + b"\n"

            process_out = io.BytesIO()
            process_err = io.StringIO()
            code = run_cli(
                ["project", "op", "--project", str(workspace), "--request", "-", "--json"],
                io.BytesIO(request_bytes),
                process_out,
                process_err,
            )
            self.assertEqual(0, code, process_err.getvalue())
            self.assertEqual(expected, process_out.getvalue())

            ergonomic_out = io.BytesIO()
            ergonomic_err = io.StringIO()
            code = run_cli(
                ["project", "inspect", "--project", str(workspace), "--json"],
                io.BytesIO(),
                ergonomic_out,
                ergonomic_err,
            )
            self.assertEqual(0, code, ergonomic_err.getvalue())
            self.assertEqual(expected, ergonomic_out.getvalue())

            reloaded_service = ProjectService(workspace)
            reloaded = dispatch_operation(
                request,
                reloaded_service.context,
                project_service=reloaded_service,
            )
            self.assertEqual(expected, canonical_result_bytes(reloaded, reloaded_service.context) + b"\n")

    def test_cli_dispatches_once_and_contains_no_persistence_algorithm(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = self.workspace(temporary)
            calls = []
            original = cli_module.dispatch_operation

            def counted(*args, **kwargs):
                calls.append(args[0]["operation"])
                return original(*args, **kwargs)

            stdout = io.BytesIO()
            stderr = io.StringIO()
            with mock.patch.object(cli_module, "dispatch_operation", counted):
                code = run_cli(
                    ["project", "validate", "--project", str(workspace), "--json"],
                    io.BytesIO(),
                    stdout,
                    stderr,
                )
            self.assertEqual(0, code, stderr.getvalue())
            self.assertEqual(["project.validate"], calls)

        tree = ast.parse((ROOT / "packages/schuss_core/cli.py").read_text())
        prohibited = {
            (node.func.value.id, node.func.attr)
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in {"os", "Path"}
            and node.func.attr in {"replace", "unlink", "link", "fsync"}
        }
        self.assertEqual(set(), prohibited)

    def test_cli_json_help_completion_and_environment_are_deterministic(self):
        legacy = {
            shell: subprocess.run(
                [str(CLI), "completion", shell],
                cwd=ROOT,
                check=True,
                stdout=subprocess.PIPE,
            ).stdout
            for shell in ("bash", "zsh", "fish")
        }
        for shell in ("bash", "zsh", "fish"):
            first = subprocess.run(
                [str(CLI), "project", "completion", shell],
                cwd="/tmp",
                check=True,
                stdout=subprocess.PIPE,
            ).stdout
            second = subprocess.run(
                [str(CLI), "project", "completion", shell],
                cwd=ROOT,
                check=True,
                stdout=subprocess.PIPE,
            ).stdout
            self.assertEqual(first, second)
            self.assertIn(b"project", first)
            self.assertEqual(
                legacy[shell],
                subprocess.run(
                    [str(CLI), "completion", shell],
                    cwd="/tmp",
                    check=True,
                    stdout=subprocess.PIPE,
                ).stdout,
            )

        help_one = subprocess.run(
            [str(CLI), "project", "transact", "--help"],
            cwd="/tmp",
            check=True,
            stdout=subprocess.PIPE,
        ).stdout
        help_two = subprocess.run(
            [str(CLI), "project", "transact", "--help"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
        ).stdout
        self.assertEqual(help_one, help_two)
        self.assertLessEqual(max(map(len, help_one.splitlines())), 80)

        with tempfile.TemporaryDirectory() as temporary:
            workspace = self.workspace(temporary)
            outputs = []
            for seed, locale in (("1", "C"), ("777", "C.UTF-8")):
                environment = dict(os.environ)
                environment.update(
                    {"PYTHONHASHSEED": seed, "LC_ALL": locale, "LANG": locale}
                )
                completed = subprocess.run(
                    [str(CLI), "project", "validate", "--project", str(workspace), "--json"],
                    cwd="/tmp" if seed == "1" else ROOT,
                    env=environment,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                self.assertEqual(b"", completed.stderr)
                outputs.append(completed.stdout)
            self.assertEqual(outputs[0], outputs[1])

    def test_negative_fixture_matrix_names_every_required_failure_class(self):
        self.assertEqual(
            {
                "stale_project",
                "stale_graph",
                "missing_parent",
                "invalid_reference",
                "path_escape",
                "symlink_escape",
                "duplicate_identity",
                "base_overlay_collision",
                "concurrent_writer",
                "malformed_lock",
                "interrupted_write",
                "uncommitted_partial_state",
            },
            set(self.negative),
        )


if __name__ == "__main__":
    unittest.main()
