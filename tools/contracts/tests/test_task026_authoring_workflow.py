import copy
import hashlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools/contracts"
sys.path[:0] = [str(ROOT), str(TOOLS)]

from packages.schuss_core import dispatch_operation, load_repository_context
from packages.schuss_core.cli import run as run_cli
from packages.schuss_core.product_cli import build_plan_request
from packages.schuss_core.project_cli import (
    project_history_request,
    project_init_request,
    project_profile_fork_request,
    project_profile_transact_request,
    project_revert_request,
)
from packages.schuss_core.project_service import ProjectService, with_project_schemas

import validator_core as core
import generate_task026_cli_golden as cli_golden


RECORD_SET = ROOT / "contracts/record-sets/task026-authoring-workflow-v1.json"
RECORD_SET_LOCATOR = "contracts/record-sets/task026-authoring-workflow-v1.json"


class InjectedFailure(RuntimeError):
    pass


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


class Task026AuthoringWorkflowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = with_project_schemas(
            load_repository_context(ROOT, record_set_path=RECORD_SET), ROOT
        )
        cls.graph = next(
            item
            for item in cls.context.records["graphs"]
            if item["graph_id"] == "schuss-graph-000006"
            and item["revision"] == 1
        )
        cls.instrument = next(
            item
            for item in cls.context.records["instruments"]
            if item["instrument_id"] == "schuss-instrument-000005"
            and item["revision"] == 1
        )
        cls.request = next(
            item
            for item in cls.context.records["request"]
            if item["build_request_id"] == "schuss-build-request-000005"
            and item["revision"] == 1
        )

    def initialize_and_fork(self, workspace):
        service = ProjectService(workspace, initial_context=self.context)
        init = dispatch_operation(
            project_init_request(
                "schuss-project-000026",
                {
                    "reference": copy.deepcopy(self.context.record_set_reference),
                    "portable_locator": RECORD_SET_LOCATOR,
                },
                _ref(self.graph, "graph_id"),
                [_ref(self.instrument, "instrument_id")],
                [_ref(self.request, "build_request_id")],
            ),
            service.context,
            project_service=service,
        )
        self.assertEqual("success", init["status"], init["diagnostics"])
        fork = dispatch_operation(
            project_profile_fork_request(
                _ref(init["value"]["project"], "project_id"),
                _ref(self.graph, "graph_id"),
                _ref(self.instrument, "instrument_id"),
                _ref(self.request, "build_request_id"),
            ),
            service.context,
            project_service=service,
        )
        self.assertEqual("success", fork["status"], fork["diagnostics"])
        return service, fork

    @staticmethod
    def profile_edits(graph):
        output = next(
            item for item in graph["nodes"] if item["node_id"] == "graph-node-000008"
        )
        output_connections = [
            item
            for item in graph["connections"]
            if item["connection_id"]
            in {"graph-connection-000008", "graph-connection-000009"}
        ]
        first_point = graph["parameter_bindings"][0]["transform"]["points"][0]
        return [
            *[
                {"edit": "remove-connection", "connection_id": item["connection_id"]}
                for item in output_connections
            ],
            {"edit": "remove-node", "node_id": output["node_id"]},
            {
                "edit": "set-node-parameter",
                "node_id": "graph-node-000001",
                "facet_id": "component-parameter-000001",
                "value": "-24",
            },
            {
                "edit": "set-public-parameter-default",
                "facet_id": "graph-facet-000001",
                "value": "0.5",
            },
            {
                "edit": "set-parameter-binding-point",
                "binding_id": graph["parameter_bindings"][0]["binding_id"],
                "point_index": 0,
                "source": first_point["source"],
                "destination": first_point["destination"],
            },
            {"edit": "add-node", "node": copy.deepcopy(output)},
            *[
                {"edit": "add-connection", "connection": copy.deepcopy(item)}
                for item in output_connections
            ],
        ]

    def test_schemas_and_successor_record_set_are_closed_and_fresh(self):
        manifest = core.load_json(RECORD_SET)
        parent = core.load_json(
            ROOT / "contracts/record-sets/task026a-executable-profile-v1.json"
        )
        self.assertEqual("schuss-record-set-000019", manifest["record_set_id"])
        self.assertEqual(
            {
                "status": "included",
                **{
                    key: parent[key]
                    for key in ("record_set_id", "revision", "content_hash")
                },
            },
            manifest["parent_reference"],
        )
        for name in (
            "application_capability_description_v1",
            "operation_request_v8",
            "operation_result_v8",
            "project_write_plan_v1",
        ):
            self.assertEqual(
                [], core.validate_schema_annotations(self.context.schemas[name])
            )
        description = dispatch_operation(
            {
                "schema_version": "schuss-operation-request-v7",
                "canonical_profile": "schuss-canonical-json-v1",
                "operation": "application.describe",
                "payload": {"scope": "selected-context"},
            },
            self.context,
        )
        self.assertEqual("success", description["status"])
        operations = {
            item["operation"] for item in description["value"]["operations"]
        }
        self.assertEqual(18, len(operations))
        self.assertTrue(
            {
                "project.profile.fork",
                "project.profile.transact",
                "project.history.inspect",
                "project.revert",
            }
            <= operations
        )

    def test_create_edit_history_revert_redo_and_plan_exact_owned_closure(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "workspace"
            service, fork = self.initialize_and_fork(workspace)
            value = fork["value"]
            self.assertEqual(2, value["project"]["revision"])
            self.assertEqual(3, len(value["project"]["owned_members"]))
            self.assertNotEqual(self.graph["graph_id"], value["graph"]["graph_id"])
            self.assertNotEqual(
                self.instrument["instrument_id"], value["instrument"]["instrument_id"]
            )
            self.assertNotEqual(
                self.request["build_request_id"],
                value["build_request"]["build_request_id"],
            )

            edit = dispatch_operation(
                project_profile_transact_request(
                    _ref(value["project"], "project_id"),
                    _ref(value["graph"], "graph_id"),
                    self.profile_edits(value["graph"]),
                ),
                service.context,
                project_service=service,
            )
            self.assertEqual("success", edit["status"], edit["diagnostics"])
            edited = edit["value"]
            self.assertEqual(3, edited["project"]["revision"])
            self.assertEqual(2, edited["graph"]["revision"])
            self.assertEqual(2, edited["instrument"]["revision"])
            self.assertEqual(2, edited["build_request"]["revision"])
            self.assertEqual(6, len(edited["project"]["owned_members"]))

            history = dispatch_operation(
                project_history_request(),
                service.context,
                project_service=service,
            )
            self.assertEqual("success", history["status"])
            self.assertEqual(3, history["value"]["revision_count"])

            undo = dispatch_operation(
                project_revert_request(
                    _ref(edited["project"], "project_id"),
                    _ref(value["project"], "project_id"),
                ),
                service.context,
                project_service=service,
            )
            self.assertEqual("success", undo["status"], undo["diagnostics"])
            self.assertEqual(
                value["project"]["primary_graph_reference"],
                undo["value"]["project"]["primary_graph_reference"],
            )
            redo = dispatch_operation(
                project_revert_request(
                    _ref(undo["value"]["project"], "project_id"),
                    _ref(edited["project"], "project_id"),
                ),
                service.context,
                project_service=service,
            )
            self.assertEqual("success", redo["status"], redo["diagnostics"])
            self.assertEqual(
                edited["project"]["build_request_references"],
                redo["value"]["project"]["build_request_references"],
            )
            self.assertEqual(5, redo["value"]["project"]["revision"])

            request_reference = redo["value"]["project"][
                "build_request_references"
            ][0]
            plan = dispatch_operation(
                build_plan_request(request_reference),
                service.context,
                project_service=service,
            )
            self.assertEqual("success", plan["status"], plan["diagnostics"])

            before = _governed_hashes(workspace)
            stale = copy.deepcopy(
                project_profile_transact_request(
                    _ref(redo["value"]["project"], "project_id"),
                    copy.deepcopy(
                        redo["value"]["project"]["primary_graph_reference"]
                    ),
                    [
                        {
                            "edit": "set-public-parameter-default",
                            "facet_id": "graph-facet-000001",
                            "value": "0.5",
                        }
                    ],
                )
            )
            stale["payload"]["expected_project_reference"]["content_hash"] = (
                "sha256:" + "0" * 64
            )
            rejected = dispatch_operation(
                stale, service.context, project_service=service
            )
            self.assertEqual("conflict", rejected["status"])
            self.assertEqual(before, _governed_hashes(workspace))

            reloaded = ProjectService(workspace).load()
            self.assertEqual(redo["value"]["project"], reloaded.manifest)
            self.assertEqual("valid", reloaded.validation["status"])

            baseline = _governed_hashes(workspace)
            fired = []

            def interrupt(label):
                if label == "after:immutable-1.publish" and not fired:
                    fired.append(label)
                    raise InjectedFailure(label)

            interrupted_service = ProjectService(
                workspace,
                failure_injector=interrupt,
                pid_provider=lambda: 424242,
                process_alive=lambda pid: False,
            )
            selected_graph = next(
                item
                for item in interrupted_service.load().context.records["graphs"]
                if _ref(item, "graph_id")
                == redo["value"]["project"]["primary_graph_reference"]
            )
            with self.assertRaises(InjectedFailure):
                dispatch_operation(
                    project_profile_transact_request(
                        _ref(redo["value"]["project"], "project_id"),
                        _ref(selected_graph, "graph_id"),
                        [
                            {
                                "edit": "set-public-parameter-default",
                                "facet_id": "graph-facet-000001",
                                "value": "0.5",
                            }
                        ],
                    ),
                    interrupted_service.context,
                    project_service=interrupted_service,
                )
            self.assertEqual(["after:immutable-1.publish"], fired)
            recovered = ProjectService(
                workspace, process_alive=lambda pid: False
            ).load()
            self.assertEqual(redo["value"]["project"], recovered.manifest)
            self.assertEqual(baseline, _governed_hashes(workspace))

    def test_cli_help_completion_and_v8_machine_request_are_public(self):
        self.assertEqual(
            core.load_json(
                ROOT
                / "tools/contracts/tests/fixtures/task026-cli-successor-golden-hashes.json"
            ),
            cli_golden.generated(),
        )
        for argv in (
            ["project", "create", "--help"],
            ["project", "edit", "--help"],
            ["project", "history", "--help"],
            ["project", "revert", "--help"],
            ["build", "plan", "--help"],
            ["build", "execute", "--help"],
        ):
            with self.subTest(argv=argv):
                out = io.BytesIO()
                code = run_cli(argv, io.BytesIO(), out, io.StringIO())
                self.assertEqual(0, code)
                self.assertIn(b"--help", out.getvalue())
        for shell in ("bash", "zsh", "fish"):
            out = io.BytesIO()
            code = run_cli(
                ["project", "completion", shell],
                io.BytesIO(),
                out,
                io.StringIO(),
            )
            self.assertEqual(0, code)
            self.assertIn(b"create", out.getvalue())
            self.assertIn(b"history", out.getvalue())
            self.assertIn(b"revert", out.getvalue())


if __name__ == "__main__":
    unittest.main()
