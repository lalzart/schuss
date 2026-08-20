#!/usr/bin/env python3
"""Read-only complete Task 018 Gills panel/runtime validator."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/contracts")]

from packages.schuss_core.build_execution import handler_reference  # noqa: E402
from packages.schuss_core.control_plane import (  # noqa: E402
    dispatch_operation,
    load_repository_context,
)
from packages.schuss_core.gills_direct_backend import (  # noqa: E402
    DirectExecutionConfig,
    verify_execution_config,
)
from packages.schuss_core.gills_mapped_backend import (  # noqa: E402
    REQUEST_REFERENCE,
    RUNTIME_REFERENCE,
    descriptor,
)
from packages.schuss_core.gills_panel_runtime import host_vectors  # noqa: E402

import generate_task018_records as generator  # noqa: E402
import run_task018 as runner  # noqa: E402
import validator_core as core  # noqa: E402


RECORD_SET = ROOT / "contracts/record-sets/task018-full-gills-v1.json"
PARENT_RECORD_SET = ROOT / "contracts/record-sets/task017-curated-core-v1.json"
EVIDENCE_ROOT = ROOT / "evidence/task018-completion-v1"


def _reference(record: dict[str, Any], id_field: str) -> dict[str, Any]:
    return {
        id_field: record[id_field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def validate() -> dict[str, Any]:
    generated_files, manifest_bytes, generated_summary = generator.generated()
    generated_files[RECORD_SET.relative_to(ROOT).as_posix()] = manifest_bytes
    stale = [
        relative
        for relative, payload in generated_files.items()
        if not (ROOT / relative).is_file()
        or (ROOT / relative).read_bytes() != payload
    ]
    if stale:
        raise ValueError(
            "generated Task 018 records are stale: " + ", ".join(sorted(stale))
        )

    context = load_repository_context(record_set_path=RECORD_SET)
    for name, summary in (
        ("device/instrument", context.device_summary),
        ("component/graph", context.component_summary),
        ("target/backend/build", context.task007_summary),
        ("Gills mapping/runtime", context.task018_summary),
    ):
        if summary["status"] not in {"valid", "valid-with-deferred-graph"}:
            raise ValueError(f"Task 018 {name} closure is invalid")
    if [
        item["status"] for item in context.task018_summary["evidence_levels"]
    ] != ["passed", "passed"] + ["not-run"] * 6:
        raise ValueError("Task 018 semantic evidence levels are not separated")

    validation = dispatch_operation(
        {
            "schema_version": "schuss-operation-request-v1",
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": "records.validate",
            "payload": {"scope": "accepted-record-closure"},
        },
        context,
    )
    if validation["status"] != "success":
        raise ValueError("shared record validation operation failed")

    inspections: dict[str, dict[str, Any]] = {}
    for name, identity in (
        ("executable", ("schuss-instrument-000002", 2)),
        ("percussion", ("schuss-instrument-000003", 2)),
        ("effects", ("schuss-instrument-000004", 2)),
    ):
        instrument = next(
            value
            for value in context.records["instruments"]
            if (value["instrument_id"], value["revision"]) == identity
        )
        inspections[name] = dispatch_operation(
            {
                "schema_version": "schuss-operation-request-v6",
                "canonical_profile": "schuss-canonical-json-v1",
                "operation": "gills.inspect",
                "payload": {
                    "instrument_reference": _reference(
                        instrument, "instrument_id"
                    )
                },
            },
            context,
        )
        if inspections[name]["status"] != "success":
            raise ValueError(f"exact {name} Gills inspection failed")

    plans: dict[str, dict[str, Any]] = {}
    for name, identity in (
        ("executable", ("schuss-build-request-000002", 4)),
        ("percussion", ("schuss-build-request-000003", 2)),
        ("effects", ("schuss-build-request-000004", 2)),
    ):
        request = next(
            value
            for value in context.records["request"]
            if (value["build_request_id"], value["revision"]) == identity
        )
        plans[name] = dispatch_operation(
            {
                "schema_version": "schuss-operation-request-v4",
                "canonical_profile": "schuss-canonical-json-v1",
                "operation": "build.plan",
                "payload": {
                    "build_request_reference": _reference(
                        request, "build_request_id"
                    )
                },
            },
            context,
        )
    if {key: value["status"] for key, value in plans.items()} != {
        "executable": "success",
        "percussion": "invalid",
        "effects": "unsupported",
    }:
        raise ValueError("Task 018 plan outcomes differ")
    if {item["code"] for item in plans["percussion"]["diagnostics"]} != {
        "COMPILER_COMPOUND_INTERNAL_BINDING_UNRESOLVED"
    }:
        raise ValueError("percussion successor diagnostic differs")
    if {item["code"] for item in plans["effects"]["diagnostics"]} != {
        "COMPILER_BINDING_UNSUPPORTED"
    }:
        raise ValueError("effects successor diagnostic differs")

    mapped_handler = descriptor()
    handler_errors = core.schema_errors(
        mapped_handler,
        context.schemas["build_handler_descriptor"],
        context.schemas["build_handler_descriptor"],
    )
    if handler_errors:
        raise ValueError("mapped handler descriptor schema failure")
    runtime = inspections["executable"]["value"]["runtime_realization"]
    if _reference(runtime, "runtime_realization_id") != RUNTIME_REFERENCE:
        raise ValueError("mapped inspection selected a different runtime realization")
    supported = runtime["supported_builds"]
    if supported != [
        {
            "build_request_reference": REQUEST_REFERENCE,
            "instrument_reference": inspections["executable"]["value"][
                "coverage_report"
            ]["instrument_reference"],
            "handler": {"status": "supported", **handler_reference(mapped_handler)},
        }
    ]:
        raise ValueError("mapped runtime and handler do not form one exact closure")

    vectors = host_vectors()
    if (
        len(vectors["pot_endpoints"]) != 10
        or vectors["pickup_trace"][-1]["pickup_armed"]
        or vectors["button_1_events"]
        != ["button-1-press", "button-1-hold", "button-1-release"]
    ):
        raise ValueError("deterministic host panel vectors differ")

    verify_execution_config(DirectExecutionConfig.local_default())
    live_summary = runner.check_retained()
    if [item["status"] for item in live_summary["evidence_levels"]] != (
        ["passed"] * 5 + ["not-run"] * 3
    ):
        raise ValueError("Task 018 execution evidence levels differ")

    parent = core.load_json(PARENT_RECORD_SET)
    successor = core.load_json(RECORD_SET)
    for collection in ("schema_members", "record_members"):
        if not all(item in successor[collection] for item in parent[collection]):
            raise ValueError(f"Task 017 {collection} are not preserved")
    for item in successor["schema_members"] + successor["record_members"]:
        path = ROOT / item["portable_path"]
        if not path.is_file() or core.sha256_file(path) != item["byte_sha256"]:
            raise ValueError(
                "manifest path/hash check failed: " + item["portable_path"]
            )

    device = inspections["executable"]["value"]["device_profile"]
    slot_count = sum(
        len(device[collection])
        for collection in (
            "input_controls",
            "gestures",
            "feedback_outputs",
            "displays",
            "physical_io",
        )
    )
    return {
        "schema_version": "task018-validator-result-v1",
        "status": "valid",
        "record_set_reference": context.record_set_reference,
        "manifest_byte_sha256": hashlib.sha256(RECORD_SET.read_bytes()).hexdigest(),
        "generated_record_set_reference": generated_summary["record_set"],
        "panel_slot_count": slot_count,
        "panel_evidence_source_count": len(
            inspections["executable"]["value"]["panel_evidence"]["sources"]
        ),
        "instrument_successor_count": len(inspections),
        "runtime_realization_count": len(context.records["runtime_realizations"]),
        "plan_statuses": {key: value["status"] for key, value in plans.items()},
        "fresh_processes": live_summary["fresh_processes"],
        "arm_object_sha256": next(
            item["byte_sha256"]
            for item in live_summary["artifacts"]
            if item["artifact_kind"] == "arm-object"
        ),
        "target_executable_sha256": next(
            item["byte_sha256"]
            for item in live_summary["artifacts"]
            if item["artifact_kind"] == "target-executable"
        ),
        "evidence_levels": live_summary["evidence_levels"],
        "device_actions_performed": False,
        "connected_device_validation_performed": False,
        "real_time_validation_performed": False,
        "audible_validation_performed": False,
        "publication_performed": False,
    }


def main() -> int:
    try:
        result = validate()
    except (OSError, ValueError) as exc:
        print("Task 018 validation failed: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
