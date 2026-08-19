#!/usr/bin/env python3
"""Generate Task 032 project-owned variable-graph and package fixtures."""

from __future__ import annotations

import argparse
import copy
import hashlib
from pathlib import Path
import sys
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.schuss_core.control_plane import (  # noqa: E402
    load_repository_context,
    with_compiler_schemas,
)
from packages.schuss_core.project_service import with_project_schemas  # noqa: E402
from packages.schuss_core.variable_host_runtime import (  # noqa: E402
    lower_variable_host_package,
)
from tools.contracts import validator_core as core  # noqa: E402


RECORD_SET = ROOT / "contracts/record-sets/task032-variable-host-runtime-v1.json"
OUTPUT_ROOT = ROOT / "fixtures/task032"
ALLOCATIONS = {
    "smaller": {
        "project_id": "schuss-project-000032",
        "graph_id": "schuss-graph-068746",
        "instrument_id": "schuss-instrument-237474",
        "build_request_id": "schuss-build-request-139035",
    },
    "reference": {
        "project_id": "schuss-project-000033",
        "graph_id": "schuss-graph-508458",
        "instrument_id": "schuss-instrument-289694",
        "build_request_id": "schuss-build-request-413229",
    },
    "larger": {
        "project_id": "schuss-project-000034",
        "graph_id": "schuss-graph-667107",
        "instrument_id": "schuss-instrument-191798",
        "build_request_id": "schuss-build-request-808211",
    },
}


def _bytes(value: object) -> bytes:
    return (core.canonical_json(value) + "\n").encode("utf-8")


def _ref(record: Mapping[str, Any], id_field: str) -> dict[str, Any]:
    return {
        id_field: record[id_field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def _hashed(record: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(record)
    result["content_hash"] = "sha256:" + "0" * 64
    result = core.canonicalize_with_schema(result, schema, schema)
    result["content_hash"] = core.record_content_hash(result, schema)
    errors = core.schema_errors(result, schema, schema)
    if errors:
        raise ValueError("; ".join(errors))
    if result != core.canonicalize_with_schema(result, schema, schema):
        raise ValueError("generated fixture is not canonical")
    return result


def _contract_ref(context, suffix: str) -> dict[str, Any]:
    matches = [
        item
        for item in context.records["contracts"]
        if item["component_contract_id"] == f"schuss-component-contract-{suffix}"
    ]
    if len(matches) != 1:
        raise ValueError(f"contract {suffix} is not exact")
    return _ref(matches[0], "component_contract_id")


def _node(
    node_id: str,
    contract_reference: Mapping[str, Any],
    parameters: list[tuple[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "node_id": node_id,
        "contract_reference": copy.deepcopy(dict(contract_reference)),
        "parameter_values": [
            {"facet_id": facet_id, "value": value}
            for facet_id, value in (parameters or [])
        ],
        "attribute_values": [],
    }


def _connection(
    identifier: int,
    source_node: str,
    source_facet: str,
    destination_node: str,
    destination_facet: str,
) -> dict[str, Any]:
    return {
        "connection_id": f"graph-connection-{identifier:06d}",
        "source": {"node_id": source_node, "facet_id": source_facet},
        "destination": {
            "node_id": destination_node,
            "facet_id": destination_facet,
        },
    }


def _empty_graph(graph_id: str, display_name: str) -> dict[str, Any]:
    return {
        "schema_version": "dsp-graph-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "graph_id": graph_id,
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "display_name": display_name,
        "public_ports": [],
        "public_parameters": [],
        "public_actions": [],
        "public_displays": [],
        "nodes": [],
        "connections": [],
        "public_port_exposures": [],
        "public_facet_exposures": [],
        "parameter_bindings": [],
        "compound_interface_mappings": [],
        "hierarchy_edges": [],
    }


def _smaller_graph(context, graph_id: str) -> dict[str, Any]:
    graph = _empty_graph(graph_id, "Task 032 smaller saw soft-clip stereo graph")
    graph["nodes"] = [
        _node(
            "graph-node-000101",
            _contract_ref(context, "000012"),
            [("component-parameter-000001", "-24")],
        ),
        _node("graph-node-000102", _contract_ref(context, "000016")),
        _node("graph-node-000103", _contract_ref(context, "000009")),
    ]
    graph["connections"] = [
        _connection(
            101,
            "graph-node-000101",
            "component-port-000002",
            "graph-node-000102",
            "component-port-000001",
        ),
        _connection(
            102,
            "graph-node-000102",
            "component-port-000002",
            "graph-node-000103",
            "component-port-000001",
        ),
        _connection(
            103,
            "graph-node-000102",
            "component-port-000002",
            "graph-node-000103",
            "component-port-000002",
        ),
    ]
    return _hashed(graph, context.schemas["graph"])


def _reference_graph(context, graph_id: str) -> dict[str, Any]:
    source = next(
        item
        for item in context.records["graphs"]
        if item["graph_id"] == "schuss-graph-000006" and item["revision"] == 1
    )
    graph = copy.deepcopy(source)
    graph.update(
        {
            "graph_id": graph_id,
            "revision": 1,
            "content_hash": "sha256:" + "0" * 64,
            "display_name": "Task 032 project-owned seven-node reference graph",
        }
    )
    return _hashed(graph, context.schemas["graph"])


def _performance_parameter(
    facet_id: str, semantic_key: str, display_label: str
) -> dict[str, Any]:
    return {
        "facet_id": facet_id,
        "semantic_key": semantic_key,
        "display_label": display_label,
        "value_type": "exact-decimal",
        "domain": {
            "status": "known",
            "minimum": "0",
            "maximum": "1",
            "minimum_inclusive": True,
            "maximum_inclusive": True,
            "overflow_policy": "reject",
            "unit": "normalized",
        },
        "default": "0.5",
        "update_behavior": {"update_kind": "runtime", "stateful": True},
    }


def _parameter_binding(
    identifier: int, source_facet: str, node_id: str, destination_facet: str
) -> dict[str, Any]:
    domain = {
        "status": "known",
        "minimum": "0",
        "maximum": "1",
        "minimum_inclusive": True,
        "maximum_inclusive": True,
        "overflow_policy": "reject",
        "unit": "normalized",
    }
    return {
        "binding_id": f"graph-binding-{identifier:06d}",
        "binding_kind": "parameter-to-port",
        "source_graph_parameter_id": source_facet,
        "destination": {
            "node_id": node_id,
            "facet_kind": "port",
            "facet_id": destination_facet,
        },
        "source_domain": copy.deepcopy(domain),
        "destination_domain": copy.deepcopy(domain),
        "transform": {
            "curve": "linear",
            "polarity": "direct",
            "points": [
                {"source": "0", "destination": "0"},
                {"source": "1", "destination": "1"},
            ],
        },
        "update_boundary": "control-cycle",
        "smoothing": {
            "kind": "linear",
            "responsibility": "graph",
            "completion": "next-control-cycle",
        },
        "driver_policy": "exclusive",
    }


def _larger_graph(context, graph_id: str) -> dict[str, Any]:
    graph = _empty_graph(
        graph_id, "Task 032 larger repeated-soft-clip variable graph"
    )
    graph["public_parameters"] = [
        _performance_parameter("graph-facet-000001", "motion", "Motion"),
        _performance_parameter("graph-facet-000002", "blend", "Blend"),
    ]
    graph["nodes"] = [
        _node(
            "graph-node-000201",
            _contract_ref(context, "000012"),
            [("component-parameter-000001", "-24")],
        ),
        _node(
            "graph-node-000202",
            _contract_ref(context, "000013"),
            [("component-parameter-000001", "-12")],
        ),
        _node("graph-node-000203", _contract_ref(context, "000016")),
        _node("graph-node-000204", _contract_ref(context, "000016")),
        _node("graph-node-000205", _contract_ref(context, "000015")),
        _node("graph-node-000206", _contract_ref(context, "000003")),
        _node("graph-node-000207", _contract_ref(context, "000020")),
        _node("graph-node-000208", _contract_ref(context, "000009")),
    ]
    graph["connections"] = [
        _connection(201, "graph-node-000201", "component-port-000002", "graph-node-000203", "component-port-000001"),
        _connection(202, "graph-node-000202", "component-port-000003", "graph-node-000204", "component-port-000001"),
        _connection(203, "graph-node-000203", "component-port-000002", "graph-node-000206", "component-port-000001"),
        _connection(204, "graph-node-000204", "component-port-000002", "graph-node-000206", "component-port-000002"),
        _connection(205, "graph-node-000205", "component-port-000002", "graph-node-000207", "component-port-000001"),
        _connection(206, "graph-node-000206", "component-port-000004", "graph-node-000207", "component-port-000002"),
        _connection(207, "graph-node-000207", "component-port-000003", "graph-node-000208", "component-port-000001"),
        _connection(208, "graph-node-000207", "component-port-000003", "graph-node-000208", "component-port-000002"),
    ]
    graph["parameter_bindings"] = [
        _parameter_binding(
            201, "graph-facet-000001", "graph-node-000205", "component-port-000001"
        ),
        _parameter_binding(
            202, "graph-facet-000002", "graph-node-000206", "component-port-000003"
        ),
    ]
    return _hashed(graph, context.schemas["graph"])


def _instrument(
    context,
    *,
    instrument_id: str,
    graph: Mapping[str, Any],
    with_parameters: bool,
    display_name: str,
) -> dict[str, Any]:
    template = next(
        item
        for item in context.records["instruments"]
        if item["instrument_id"] == "schuss-instrument-000005"
        and item["revision"] == 1
    )
    instrument = copy.deepcopy(template)
    instrument.update(
        {
            "instrument_id": instrument_id,
            "revision": 1,
            "content_hash": "sha256:" + "0" * 64,
            "display_name": display_name,
            "graph_reference": {"status": "resolved", **_ref(graph, "graph_id")},
        }
    )
    if not with_parameters:
        instrument["parameters"] = []
        instrument["graph_mappings"] = []
    return _hashed(instrument, context.schemas["instrument"])


def _request(
    context,
    *,
    request_id: str,
    graph: Mapping[str, Any],
    instrument: Mapping[str, Any],
) -> dict[str, Any]:
    template = next(
        item
        for item in context.records["request"]
        if item["build_request_id"] == "schuss-build-request-000007"
        and item["revision"] == 1
    )
    request = copy.deepcopy(template)
    request.update(
        {
            "build_request_id": request_id,
            "revision": 1,
            "content_hash": "sha256:" + "0" * 64,
            "graph_reference": _ref(graph, "graph_id"),
            "instrument_reference": {
                "status": "included",
                **_ref(instrument, "instrument_id"),
            },
        }
    )
    return _hashed(request, context.schemas["request"])


def _owned_member(
    kind: str, stable_id: str, record: Mapping[str, Any], locator: str, data: bytes
) -> dict[str, Any]:
    return {
        "record_kind": kind,
        "stable_id": stable_id,
        "revision": record["revision"],
        "content_hash": record["content_hash"],
        "schema_version": record["schema_version"],
        "portable_locator": locator,
        "byte_sha256": hashlib.sha256(data).hexdigest(),
        "parent_reference": {"status": "omitted"},
    }


def _project_files(context, name: str) -> tuple[dict[str, bytes], dict[str, Any]]:
    allocation = ALLOCATIONS[name]
    if name == "smaller":
        graph = _smaller_graph(context, allocation["graph_id"])
        with_parameters = False
    elif name == "reference":
        graph = _reference_graph(context, allocation["graph_id"])
        with_parameters = True
    else:
        graph = _larger_graph(context, allocation["graph_id"])
        with_parameters = True
    instrument = _instrument(
        context,
        instrument_id=allocation["instrument_id"],
        graph=graph,
        with_parameters=with_parameters,
        display_name=f"Task 032 {name} variable host fixture",
    )
    request = _request(
        context,
        request_id=allocation["build_request_id"],
        graph=graph,
        instrument=instrument,
    )
    graph_locator = f"records/dsp-graphs/{allocation['graph_id']}-r000001.json"
    instrument_locator = (
        f"records/instruments/{allocation['instrument_id']}-r000001.json"
    )
    request_locator = (
        f"records/build-requests/{allocation['build_request_id']}-r000001.json"
    )
    graph_bytes = _bytes(graph)
    instrument_bytes = _bytes(instrument)
    request_bytes = _bytes(request)
    members = sorted(
        [
            _owned_member("dsp-graph", allocation["graph_id"], graph, graph_locator, graph_bytes),
            _owned_member("instrument", allocation["instrument_id"], instrument, instrument_locator, instrument_bytes),
            _owned_member("build-request", allocation["build_request_id"], request, request_locator, request_bytes),
        ],
        key=core.canonical_json,
    )
    project = {
        "schema_version": "project-v1",
        "canonical_profile": "schuss-canonical-json-v1",
        "project_id": allocation["project_id"],
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "parent_reference": {"status": "omitted"},
        "base_record_set": {
            "reference": copy.deepcopy(context.record_set_reference),
            "portable_locator": "contracts/record-sets/task032-variable-host-runtime-v1.json",
        },
        "owned_members": members,
        "primary_graph_reference": _ref(graph, "graph_id"),
        "instrument_references": [_ref(instrument, "instrument_id")],
        "build_request_references": [_ref(request, "build_request_id")],
        "asset_references": [],
    }
    project = _hashed(project, context.schemas["project_v1"])
    project_bytes = _bytes(project)
    manifest_locator = f"project/revisions/{allocation['project_id']}-r000001.json"
    head = {
        "schema_version": "workspace-head-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "accepted_project_reference": _ref(project, "project_id"),
        "project_manifest_locator": manifest_locator,
        "project_manifest_byte_sha256": hashlib.sha256(project_bytes).hexdigest(),
    }
    head_errors = core.schema_errors(
        head, context.schemas["workspace_head"], context.schemas["workspace_head"]
    )
    if head_errors:
        raise ValueError("; ".join(head_errors))
    augmented = context.with_records(
        graphs=(*context.records["graphs"], graph),
        instruments=(*context.records["instruments"], instrument),
        request=(*context.records["request"], request),
    )
    package, plan = lower_variable_host_package(
        augmented,
        project_manifest=project,
        host_build_request_reference=_ref(request, "build_request_id"),
    )
    resolution = next(
        item["payload"]
        for item in plan["artifacts"]
        if item["descriptor"]["artifact_kind"] == "resolution-plan"
    )
    lowering = {
        "schema_version": "task032-variable-host-lowering-fixture-v1",
        "status": "success",
        "project_reference": _ref(project, "project_id"),
        "graph_reference": _ref(graph, "graph_id"),
        "host_build_request_reference": _ref(request, "build_request_id"),
        "package_content_hash": package["content_hash"],
        "source_plan_sha256": package["source_plan_sha256"],
        "node_count": len(package["nodes"]),
        "connection_count": len(package["connections"]),
        "schedule": package["schedule"],
        "buffer_count": package["memory_plan"]["buffer_count"],
        "selected_bindings": sorted(
            [
                {
                    "node_id": trace["node_id"],
                    "binding_reference": trace["selected_binding_reference"],
                }
                for trace in resolution["traces"]
            ],
            key=core.canonical_json,
        ),
        "native_build_or_execution_performed": False,
        "device_access_performed": False,
    }
    return (
        {
            graph_locator: graph_bytes,
            instrument_locator: instrument_bytes,
            request_locator: request_bytes,
            manifest_locator: project_bytes,
            "schuss-project.json": _bytes(head),
        },
        {"package": package, "lowering": lowering},
    )


def generated() -> dict[str, bytes]:
    context = with_compiler_schemas(
        with_project_schemas(
            load_repository_context(ROOT, record_set_path=RECORD_SET), ROOT
        ),
        ROOT,
    )
    files: dict[str, bytes] = {}
    for name in ("smaller", "reference", "larger"):
        project_files, products = _project_files(context, name)
        for locator, data in project_files.items():
            files[f"{name}-project/{locator}"] = data
        files[f"{name}-host-package.json"] = _bytes(products["package"])
        files[f"{name}-host-lowering.json"] = _bytes(products["lowering"])
    return files


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files = generated()
    stale: list[str] = []
    for relative, data in sorted(files.items()):
        destination = OUTPUT_ROOT / relative
        if args.check:
            if not destination.exists() or destination.read_bytes() != data:
                stale.append(destination.relative_to(ROOT).as_posix())
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
    if stale:
        raise SystemExit("stale generated fixtures: " + ", ".join(stale))
    print(
        core.canonical_json(
            {
                "schema_version": "task032-fixture-generation-summary-v1",
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
