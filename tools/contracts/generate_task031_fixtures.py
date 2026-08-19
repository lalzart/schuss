#!/usr/bin/env python3
"""Generate the deterministic Task 031 saved-project and host-package fixtures."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.schuss_core.control_plane import (  # noqa: E402
    load_repository_context,
    with_compiler_schemas,
)
from packages.schuss_core.host_runtime import lower_host_package  # noqa: E402
from packages.schuss_core.project_service import with_project_schemas  # noqa: E402
from tools.contracts import validator_core as core  # noqa: E402


RECORD_SET_PATH = ROOT / "contracts/record-sets/task031-desktop-host-runtime-v1.json"
OUTPUT_ROOT = ROOT / "fixtures/task031"
PROJECT_ID = "schuss-project-000031"


def _bytes(value: object, *, newline: bool = True) -> bytes:
    return (core.canonical_json(value) + ("\n" if newline else "")).encode("utf-8")


def _ref(record: dict, id_field: str) -> dict:
    return {
        id_field: record[id_field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def generated() -> dict[str, bytes]:
    context = with_compiler_schemas(
        with_project_schemas(
            load_repository_context(ROOT, record_set_path=RECORD_SET_PATH), ROOT
        ),
        ROOT,
    )
    graph = next(
        value
        for value in context.records["graphs"]
        if value["graph_id"] == "schuss-graph-000006" and value["revision"] == 1
    )
    instrument = next(
        value
        for value in context.records["instruments"]
        if value["instrument_id"] == "schuss-instrument-000005"
        and value["revision"] == 1
    )
    request = next(
        value
        for value in context.records["request"]
        if value["build_request_id"] == "schuss-build-request-000006"
        and value["revision"] == 1
    )
    project = {
        "schema_version": "project-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "project_id": PROJECT_ID,
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "parent_reference": {"status": "omitted"},
        "base_record_set": {
            "portable_locator": "contracts/record-sets/task031-desktop-host-runtime-v1.json",
            "reference": context.record_set_reference,
        },
        "primary_graph_reference": _ref(graph, "graph_id"),
        "instrument_references": [_ref(instrument, "instrument_id")],
        "build_request_references": [_ref(request, "build_request_id")],
        "asset_references": [],
        "owned_members": [],
    }
    project_schema = context.schemas["project"]
    project["content_hash"] = core.record_content_hash(project, project_schema)
    project_errors = core.schema_errors(project, project_schema, project_schema)
    if project_errors:
        raise ValueError("; ".join(project_errors))
    project_bytes = _bytes(project)
    project_locator = f"project/revisions/{PROJECT_ID}-r000001.json"
    head = {
        "schema_version": "workspace-head-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "accepted_project_reference": _ref(project, "project_id"),
        "project_manifest_locator": project_locator,
        "project_manifest_byte_sha256": hashlib.sha256(project_bytes).hexdigest(),
    }
    head_schema = context.schemas["workspace_head"]
    head_errors = core.schema_errors(head, head_schema, head_schema)
    if head_errors:
        raise ValueError("; ".join(head_errors))

    package, plan = lower_host_package(context, project_reference=_ref(project, "project_id"))
    resolution = next(
        artifact["payload"]
        for artifact in plan["artifacts"]
        if artifact["descriptor"]["artifact_kind"] == "resolution-plan"
    )
    lowering = {
        "schema_version": "task031-host-lowering-fixture-v1",
        "status": "success",
        "project_reference": _ref(project, "project_id"),
        "package_content_hash": package["content_hash"],
        "source_plan_sha256": package["source_plan_sha256"],
        "selected_bindings": [
            {
                "node_id": trace["node_id"],
                "binding_reference": trace["selected_binding_reference"],
            }
            for trace in resolution["traces"]
        ],
        "native_build_or_execution_performed": False,
        "device_access_performed": False,
    }
    return {
        f"reference-project/{project_locator}": project_bytes,
        "reference-project/schuss-project.json": _bytes(head),
        "reference-host-package.json": _bytes(package),
        "reference-host-lowering.json": _bytes(lowering),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files = generated()
    stale: list[str] = []
    for relative, data in sorted(files.items()):
        path = OUTPUT_ROOT / relative
        if args.check:
            if not path.exists() or path.read_bytes() != data:
                stale.append(path.relative_to(ROOT).as_posix())
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    if stale:
        raise SystemExit("stale generated fixtures: " + ", ".join(stale))
    print(
        core.canonical_json(
            {
                "schema_version": "task031-fixture-generation-summary-v1",
                "status": "valid",
                "files": sorted(files),
                "native_build_or_execution_performed": False,
                "device_access_performed": False,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
