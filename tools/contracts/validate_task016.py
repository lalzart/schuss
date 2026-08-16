#!/usr/bin/env python3
"""Read-only complete Task 016 direct-frontend validator."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/contracts")]

from packages.schuss_core.control_plane import dispatch_operation, load_repository_context  # noqa: E402
from packages.schuss_core.gills_direct_backend import descriptor, verify_execution_config, DirectExecutionConfig  # noqa: E402
from packages.schuss_core.gills_direct_frontend import lower_gills_direct, semantic_goldens  # noqa: E402

import generate_task016_records as generator  # noqa: E402
import run_task016 as runner  # noqa: E402
import validate_task015  # noqa: E402
import validator_core as core  # noqa: E402


RECORD_SET = ROOT / "contracts/record-sets/task016-complete-gills-direct-v1.json"
EVIDENCE_ROOT = ROOT / "evidence/task016-completion-v1"


def validate() -> dict[str, object]:
    generated_files, manifest = generator.generated()
    generated_files[RECORD_SET.relative_to(ROOT).as_posix()] = manifest
    stale = [
        relative for relative, payload in generated_files.items()
        if not (ROOT / relative).is_file() or (ROOT / relative).read_bytes() != payload
    ]
    if stale:
        raise ValueError("generated Task 016 records are stale: " + ", ".join(sorted(stale)))
    context = load_repository_context(record_set_path=RECORD_SET)
    if context.task007_summary["status"] != "valid":
        raise ValueError("Task 016 exact target/backend closure is invalid")
    request = next(
        item for item in context.records["request"]
        if item["build_request_id"] == "schuss-build-request-000002" and item["revision"] == 3
    )
    reference = {key: request[key] for key in ("build_request_id", "revision", "content_hash")}
    plan_result = dispatch_operation(
        {
            "schema_version": "schuss-operation-request-v4",
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": "build.plan",
            "payload": {"build_request_reference": reference},
        },
        context,
    )
    if plan_result["status"] != "success":
        raise ValueError("Task 016 front-half plan is not successful")
    graph = next(item for item in context.records["graphs"] if item["graph_id"] == "schuss-graph-000002")
    direct = lower_gills_direct(
        plan_result["value"], graph, context.records["contracts"],
        context.records["direct_operation_specs"],
    )
    for value, key in (
        (direct["module"], "normalized_dsp_module_v1"),
        (direct, "direct_frontend_result_v1"),
    ):
        errors = core.schema_errors(value, context.schemas[key], context.schemas[key])
        if errors:
            raise ValueError(f"Task 016 {key} schema failure: {errors}")
    golden_bytes = core.canonical_json(semantic_goldens()).encode("utf-8") + b"\n"
    if (EVIDENCE_ROOT / "semantic-goldens.json").read_bytes() != golden_bytes:
        raise ValueError("Task 016 retained semantic goldens differ")
    verify_execution_config(DirectExecutionConfig.local_default())
    evidence_files, live_summary = runner.generated()
    stale_evidence = [
        relative for relative, payload in evidence_files.items()
        if not (EVIDENCE_ROOT / relative).is_file()
        or (EVIDENCE_ROOT / relative).read_bytes() != payload
    ]
    if stale_evidence:
        raise ValueError("Task 016 retained execution evidence differs: " + ", ".join(sorted(stale_evidence)))
    task015 = validate_task015.validate()
    if task015["status"] != "valid":
        raise ValueError("Task 015 byte-stability validation failed")
    handler = descriptor()
    handler_errors = core.schema_errors(
        handler,
        context.schemas["build_handler_descriptor"],
        context.schemas["build_handler_descriptor"],
    )
    if handler_errors:
        raise ValueError(f"direct handler descriptor schema failure: {handler_errors}")
    if handler["backend_reference"] != request["backend_reference"]:
        raise ValueError("direct handler and exact request backend differ")
    return {
        "schema_version": "task016-validator-result-v1",
        "status": "valid",
        "record_set_reference": context.record_set_reference,
        "manifest_byte_sha256": hashlib.sha256(RECORD_SET.read_bytes()).hexdigest(),
        "operation_specifications": len(context.records["direct_operation_specs"]),
        "graph_nodes": len(graph["nodes"]),
        "graph_connections": len(graph["connections"]),
        "scheduled_operations": len(direct["module"]["operations"]),
        "source_origins": len(direct["source_map"]["mappings"]),
        "fresh_root_runs": live_summary["fresh_root_runs"],
        "generated_cpp_sha256": direct["generated_cpp"]["byte_sha256"],
        "arm_object_sha256": next(item["byte_sha256"] for item in live_summary["artifacts"] if item["artifact_kind"] == "arm-object"),
        "target_executable_sha256": next(item["byte_sha256"] for item in live_summary["artifacts"] if item["artifact_kind"] == "target-executable"),
        "evidence_levels": live_summary["evidence_levels"],
        "task015_generated_cpp_sha256": task015["generated_cpp_sha256"],
        "device_actions_performed": False,
    }


def main() -> int:
    try:
        result = validate()
    except (OSError, ValueError) as exc:
        print("Task 016 validation failed: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
