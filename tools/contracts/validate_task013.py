#!/usr/bin/env python3
"""Read-only validator for the Task 013 compiler front half."""

from __future__ import annotations

import ast
import copy
import hashlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools/contracts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from packages.schuss_core import (
    CompilationContext,
    dispatch_operation,
    load_repository_context,
    plan_build,
)
from packages.schuss_core import control_plane

import validator_core as core


RECORD_SET = ROOT / "contracts/record-sets/task013-compiler-front-half-v1.json"
PARENT_RECORD_SET = ROOT / "contracts/record-sets/task011c-executed-v1.json"
COMPILER_MODULE = ROOT / "packages/schuss_core/compiler_front_half.py"
FORBIDDEN_IMPORT_PARTS = (
    "legacy",
    "ksoloti",
    "product_cli",
    "project_service",
    "device_transport",
    "hardware_transport",
    "schuss_ui",
)


def _ref(record: dict[str, object], field: str) -> dict[str, object]:
    return {
        field: record[field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def _artifact(plan: dict[str, object], kind: str) -> dict[str, object]:
    return next(
        value
        for value in plan["artifacts"]
        if value["descriptor"]["artifact_kind"] == kind
    )


def _validate_import_boundary() -> list[str]:
    tree = ast.parse(COMPILER_MODULE.read_text(encoding="utf-8"))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    forbidden = [
        value
        for value in imports
        if any(part in value.lower() for part in FORBIDDEN_IMPORT_PARTS)
    ]
    if forbidden:
        raise ValueError(f"compiler import boundary violated: {sorted(forbidden)}")
    return sorted(imports)


def validate() -> dict[str, object]:
    context = load_repository_context(ROOT, record_set_path=RECORD_SET)
    request = next(
        value
        for value in context.records["request"]
        if value["build_request_id"] == "schuss-build-request-000002"
        and value["revision"] == 2
    )
    request_ref = _ref(request, "build_request_id")
    compilation = CompilationContext.from_values(
        build_request_reference=request_ref,
        closure_source={
            "kind": "record-set",
            "record_set_reference": context.record_set_reference,
        },
        records=context.records,
        schemas=context.schemas,
    )
    plan = plan_build(compilation)
    if plan["status"] != "success":
        raise ValueError(f"Task 011C planning closure ended {plan['status']}")
    if [value["status"] for value in plan["stages"]] != ["success"] * 6:
        raise ValueError("not every Task 013 front-half stage passed")
    if [value["status"] for value in plan["later_stages"]] != ["not-run"] * 4:
        raise ValueError("a stage after Task 013 unexpectedly ran")
    if plan["build_result_status"] != "not-created" or plan["backend_execution_status"] != "not-run":
        raise ValueError("planning created a build result or executed a backend")

    resolution = _artifact(plan, "resolution-plan")["payload"]
    accepted_resolution = dispatch_operation(
        {
            "schema_version": "schuss-operation-request-v1",
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": "build.resolve",
            "payload": {"build_request_reference": copy.deepcopy(request_ref)},
        },
        context,
    )
    if accepted_resolution["status"] != "success":
        raise ValueError("accepted build.resolve comparison did not succeed")
    if resolution["traces"] != accepted_resolution["value"]["resolution_traces"]:
        raise ValueError("Task 013 resolution traces differ from accepted build.resolve")

    manifest = core.load_json(RECORD_SET)
    parent = core.load_json(PARENT_RECORD_SET)
    if manifest["record_members"] != parent["record_members"]:
        raise ValueError("Task 013 record set rewrites or adds semantic records")
    if manifest["parent_reference"] != {
        "status": "included",
        "record_set_id": parent["record_set_id"],
        "revision": parent["revision"],
        "content_hash": parent["content_hash"],
    }:
        raise ValueError("Task 013 exact parent reference changed")

    artifact_descriptors = {}
    for item in plan["artifacts"]:
        payload_bytes = core.canonical_json(item["payload"]).encode("utf-8")
        descriptor = item["descriptor"]
        digest = hashlib.sha256(payload_bytes).hexdigest()
        if descriptor["byte_sha256"] != digest or descriptor["byte_length"] != len(payload_bytes):
            raise ValueError(f"artifact descriptor mismatch: {descriptor['artifact_kind']}")
        artifact_descriptors[descriptor["artifact_kind"]] = descriptor

    elaborated = _artifact(plan, "elaborated-graph")["payload"]
    origin_map = _artifact(plan, "origin-source-map")["payload"]
    dependency_plan = _artifact(plan, "dependency-plan")["payload"]
    resource_plan = _artifact(plan, "resource-plan")["payload"]
    required_origin_kinds = {"node", "facet", "connection", "parameter-binding", "public-graph-facet"}
    actual_origin_kinds = {value["derived_subject"]["kind"] for value in origin_map["entries"]}
    if not required_origin_kinds <= actual_origin_kinds:
        raise ValueError("origin map omits a required successful-plan subject kind")
    if not elaborated["derived"] or elaborated["authoritative"]:
        raise ValueError("elaborated graph authority markers are unsafe")

    schema_hashes = {
        key: core.sha256_file(ROOT / "schemas" / filename)
        for key, filename in sorted(control_plane.TASK013_SCHEMA_NAMES.items())
    }
    selected_bindings = {
        value["node_id"]: value["selected_binding_reference"]
        for value in resolution["traces"]
    }
    if len(selected_bindings) != 8:
        raise ValueError("Task 011C comparison did not select eight nodes")
    if selected_bindings["graph-node-000004"] != selected_bindings["graph-node-000005"]:
        raise ValueError("Task 011C repeated Sine binding reuse changed")

    canonical_plan = core.canonical_json(plan).encode("utf-8")
    return {
        "schema_version": "task013-validation-summary-v0",
        "status": "valid",
        "record_set_reference": context.record_set_reference,
        "parent_record_set_reference": {
            "record_set_id": parent["record_set_id"],
            "revision": parent["revision"],
            "content_hash": parent["content_hash"],
        },
        "input_closure_hash": plan["input_closure"]["hash"],
        "plan_byte_length": len(canonical_plan),
        "plan_byte_sha256": hashlib.sha256(canonical_plan).hexdigest(),
        "stage_outcomes": [
            {"ordinal": value["ordinal"], "stage": value["stage"], "status": value["status"]}
            for value in plan["stages"]
        ],
        "later_stage_outcomes": copy.deepcopy(plan["later_stages"]),
        "artifact_descriptors": artifact_descriptors,
        "schema_byte_sha256": schema_hashes,
        "selected_bindings": selected_bindings,
        "selection_trace_count": len(resolution["traces"]),
        "derived_node_count": len(elaborated["nodes"]),
        "derived_connection_count": len(elaborated["connections"]),
        "origin_entry_count": len(origin_map["entries"]),
        "dependency_count": len(dependency_plan["dependencies"]),
        "resource_requirement_count": len(resource_plan["requirements"]),
        "diagnostic_codes": [value["code"] for value in plan["diagnostics"]],
        "compiler_imports": _validate_import_boundary(),
        "semantic_record_members_equal_parent": True,
        "build_result_status": plan["build_result_status"],
        "backend_execution_status": plan["backend_execution_status"],
        "evidence_levels": copy.deepcopy(plan["evidence_levels"]),
    }


def main() -> int:
    try:
        result = validate()
    except (KeyError, OSError, TypeError, ValueError) as error:
        print(f"task013-validator-error: {error}", file=sys.stderr)
        return 2
    print(core.canonical_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
