from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/contracts")]

from packages.schuss_core.build_execution import ExecutionService, handler_reference  # noqa: E402
from packages.schuss_core.control_plane import dispatch_operation, load_repository_context  # noqa: E402
from packages.schuss_core.effects_profile_backend import registration  # noqa: E402
from packages.schuss_core.product_cli import build_execute_request, build_plan_request  # noqa: E402
from packages.schuss_core.project_cli import (  # noqa: E402
    project_history_request,
    project_init_request,
    project_profile_fork_request,
    project_profile_transact_request,
    project_revert_request,
)
from packages.schuss_core.project_service import ProjectService, with_project_schemas  # noqa: E402

import validator_core as core  # noqa: E402


RECORD_SET = ROOT / "contracts/record-sets/task026-authoring-workflow-v1.json"
RECORD_SET_LOCATOR = "contracts/record-sets/task026-authoring-workflow-v1.json"
EVIDENCE_ROOT = ROOT / "evidence/task026-completion-v1"


def exact(values, field: str, stable_id: str, revision: int = 1) -> dict:
    matches = [
        item
        for item in values
        if item[field] == stable_id and item["revision"] == revision
    ]
    if len(matches) != 1:
        raise ValueError(f"{stable_id}@{revision} does not resolve exactly")
    return matches[0]


def ref(record: dict, id_field: str) -> dict:
    return {
        id_field: record[id_field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def digest(value: object) -> str:
    return hashlib.sha256(core.canonical_json(value).encode("utf-8")).hexdigest()


def file_facts(root: Path) -> dict[str, dict[str, object]]:
    return {
        path.relative_to(root).as_posix(): {
            "byte_length": len(path.read_bytes()),
            "byte_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        for path in sorted(root.rglob("*"))
        if path.is_file() and ".schuss" not in path.parts
    }


def profile_edits(graph: dict) -> list[dict]:
    output = next(
        item for item in graph["nodes"] if item["node_id"] == "graph-node-000008"
    )
    connections = [
        item
        for item in graph["connections"]
        if item["connection_id"]
        in {"graph-connection-000008", "graph-connection-000009"}
    ]
    first_binding = graph["parameter_bindings"][0]
    first_point = first_binding["transform"]["points"][0]
    return [
        *[
            {"edit": "remove-connection", "connection_id": item["connection_id"]}
            for item in connections
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
            "binding_id": first_binding["binding_id"],
            "point_index": 0,
            "source": first_point["source"],
            "destination": first_point["destination"],
        },
        {"edit": "add-node", "node": copy.deepcopy(output)},
        *[
            {"edit": "add-connection", "connection": copy.deepcopy(item)}
            for item in connections
        ],
    ]


def require_success(result: dict, label: str) -> dict:
    if result["status"] != "success":
        raise ValueError(f"{label} failed: {result['diagnostics']}")
    return result["value"]


def run_once(context, graph, instrument, request, ordinal: int) -> dict:
    with tempfile.TemporaryDirectory(
        prefix=f"schuss-task026-root-{ordinal}-"
    ) as temporary:
        root = Path(temporary)
        workspace = root / "workspace"
        service = ProjectService(workspace, initial_context=context)
        initialized = require_success(
            dispatch_operation(
                project_init_request(
                    "schuss-project-000026",
                    {
                        "reference": copy.deepcopy(context.record_set_reference),
                        "portable_locator": RECORD_SET_LOCATOR,
                    },
                    ref(graph, "graph_id"),
                    [ref(instrument, "instrument_id")],
                    [ref(request, "build_request_id")],
                ),
                service.context,
                project_service=service,
            ),
            "project.init",
        )
        forked = require_success(
            dispatch_operation(
                project_profile_fork_request(
                    ref(initialized["project"], "project_id"),
                    ref(graph, "graph_id"),
                    ref(instrument, "instrument_id"),
                    ref(request, "build_request_id"),
                ),
                service.context,
                project_service=service,
            ),
            "project.profile.fork",
        )
        edited = require_success(
            dispatch_operation(
                project_profile_transact_request(
                    ref(forked["project"], "project_id"),
                    ref(forked["graph"], "graph_id"),
                    profile_edits(forked["graph"]),
                ),
                service.context,
                project_service=service,
            ),
            "project.profile.transact",
        )
        history_before = require_success(
            dispatch_operation(
                project_history_request(),
                service.context,
                project_service=service,
            ),
            "project.history.inspect",
        )
        undone = require_success(
            dispatch_operation(
                project_revert_request(
                    ref(edited["project"], "project_id"),
                    ref(forked["project"], "project_id"),
                ),
                service.context,
                project_service=service,
            ),
            "project.revert.undo",
        )
        redone = require_success(
            dispatch_operation(
                project_revert_request(
                    ref(undone["project"], "project_id"),
                    ref(edited["project"], "project_id"),
                ),
                service.context,
                project_service=service,
            ),
            "project.revert.redo",
        )
        reloaded_service = ProjectService(workspace)
        reloaded = reloaded_service.load()
        if reloaded.manifest != redone["project"]:
            raise ValueError("close/reopen changed the accepted project head")
        final_request_reference = reloaded.manifest["build_request_references"][0]
        plan_result = dispatch_operation(
            build_plan_request(final_request_reference),
            reloaded.context,
            project_service=reloaded_service,
        )
        require_success(plan_result, "build.plan")
        handler = registration()
        output_root = root / "published"
        execution_service = ExecutionService.from_values((handler,), output_root)
        execution_result = dispatch_operation(
            build_execute_request(
                final_request_reference, handler_reference(handler.descriptor)
            ),
            reloaded.context,
            project_service=reloaded_service,
            execution_service=execution_service,
        )
        execution = require_success(execution_result, "build.execute")
        if not output_root.is_dir():
            raise ValueError("build execution did not publish its fresh output root")
        if any(
            item["status"] != ("passed" if item["level"] <= 5 else "not-run")
            for item in execution["evidence_levels"]
        ):
            raise ValueError("execution evidence levels crossed the accepted boundary")
        history_after = require_success(
            dispatch_operation(
                project_history_request(),
                reloaded.context,
                project_service=reloaded_service,
            ),
            "project.history.inspect.final",
        )
        return {
            "project_reference": ref(reloaded.manifest, "project_id"),
            "graph_reference": copy.deepcopy(
                reloaded.manifest["primary_graph_reference"]
            ),
            "instrument_reference": copy.deepcopy(
                reloaded.manifest["instrument_references"][0]
            ),
            "build_request_reference": copy.deepcopy(final_request_reference),
            "history_before_sha256": digest(history_before),
            "history_after_sha256": digest(history_after),
            "plan_result_sha256": digest(plan_result),
            "execution_result_sha256": digest(execution_result),
            "workspace_files": file_facts(workspace),
            "published_files": file_facts(output_root),
            "artifact_hashes": {
                item["artifact_kind"]: item["byte_sha256"]
                for item in execution["artifacts"]
            },
            "evidence_levels": copy.deepcopy(execution["evidence_levels"]),
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    context = with_project_schemas(
        load_repository_context(ROOT, record_set_path=RECORD_SET), ROOT
    )
    graph = exact(context.records["graphs"], "graph_id", "schuss-graph-000006")
    instrument = exact(
        context.records["instruments"], "instrument_id", "schuss-instrument-000005"
    )
    request = exact(
        context.records["request"],
        "build_request_id",
        "schuss-build-request-000005",
    )
    first = run_once(context, graph, instrument, request, 1)
    second = run_once(context, graph, instrument, request, 2)
    if first != second:
        differing = sorted(
            key for key in first if first.get(key) != second.get(key)
        )
        raise ValueError(
            "Task 026 fresh-root authoring/build flows differ: " + ", ".join(differing)
        )
    handler = registration().descriptor
    artifacts = {
        "schema_version": "task026-artifact-hashes-v1",
        "record_set_reference": copy.deepcopy(context.record_set_reference),
        "project_reference": first["project_reference"],
        "graph_reference": first["graph_reference"],
        "instrument_reference": first["instrument_reference"],
        "build_request_reference": first["build_request_reference"],
        "handler_reference": handler_reference(handler),
        "history_result_sha256": first["history_after_sha256"],
        "plan_result_sha256": first["plan_result_sha256"],
        "execution_result_sha256": first["execution_result_sha256"],
        "workspace_files": first["workspace_files"],
        "published_files": first["published_files"],
        "artifact_hashes": first["artifact_hashes"],
    }
    summary = {
        "schema_version": "task026-validation-summary-v1",
        "status": "passed",
        "fresh_workspace_runs": 2,
        "workspace_history_bytes_identical": True,
        "compiler_plan_bytes_identical": True,
        "generated_source_and_elf_bytes_identical": True,
        "record_set_reference": copy.deepcopy(context.record_set_reference),
        "project_reference": first["project_reference"],
        "graph_reference": first["graph_reference"],
        "instrument_reference": first["instrument_reference"],
        "build_request_reference": first["build_request_reference"],
        "handler_reference": artifacts["handler_reference"],
        "artifact_hashes_sha256": digest(artifacts),
        "evidence_levels": first["evidence_levels"],
        "reverb_consumed": False,
        "java_used": False,
        "legacy_boundary_patch_used": False,
        "device_actions_performed": False,
        "real_time_validation_performed": False,
        "audible_validation_performed": False,
        "git_publication_performed": False,
    }
    if args.write:
        EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)
        for name, value in (
            ("artifact-hashes.json", artifacts),
            ("validation-summary.json", summary),
        ):
            (EVIDENCE_ROOT / name).write_text(
                core.canonical_json(value) + "\n", encoding="utf-8"
            )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
