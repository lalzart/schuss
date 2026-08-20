#!/usr/bin/env python3
"""Read-only complete Task 021 corrective and evidence validator."""

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
from packages.schuss_core.gills_mapped_backend import (  # noqa: E402
    descriptor as task018_descriptor,
)
from packages.schuss_core.gills_mapped_backend_v2 import (  # noqa: E402
    INSTRUMENT_REFERENCE,
    REQUEST_REFERENCE,
    RUNTIME_REFERENCE,
    descriptor,
)

import generate_task018_records as task018_generator  # noqa: E402
import generate_task021_records as generator  # noqa: E402
import run_task021 as runner  # noqa: E402
import validator_core as core  # noqa: E402


RECORD_SET = ROOT / "contracts/record-sets/task021-gills-dma-safe-v1.json"
PARENT_RECORD_SET = ROOT / "contracts/record-sets/task018-full-gills-v1.json"
EVIDENCE_ROOT = ROOT / "evidence/task021-completion-v1"


def _reference(record: dict[str, Any], id_field: str) -> dict[str, Any]:
    return {
        id_field: record[id_field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def _require_generated_files(
    files: dict[str, bytes], manifest: bytes, path: Path, label: str
) -> None:
    files[path.relative_to(ROOT).as_posix()] = manifest
    stale = [
        relative
        for relative, payload in files.items()
        if not (ROOT / relative).is_file()
        or (ROOT / relative).read_bytes() != payload
    ]
    if stale:
        raise ValueError(label + " generated files are stale: " + ", ".join(stale))


def validate() -> dict[str, Any]:
    files, manifest, generated_summary = generator.generated()
    _require_generated_files(files, manifest, RECORD_SET, "Task 021")
    old_files, old_manifest, _ = task018_generator.generated()
    _require_generated_files(
        old_files, old_manifest, PARENT_RECORD_SET, "Task 018"
    )

    context = load_repository_context(record_set_path=RECORD_SET)
    for name, summary in (
        ("device/instrument", context.device_summary),
        ("component/graph", context.component_summary),
        ("target/backend/build", context.task007_summary),
        ("Gills mapping/runtime", context.task018_summary),
    ):
        if summary["status"] not in {"valid", "valid-with-deferred-graph"}:
            raise ValueError(f"Task 021 {name} closure is invalid")
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

    inspections: dict[int, dict[str, Any]] = {}
    for revision in (2, 3):
        instrument = next(
            value
            for value in context.records["instruments"]
            if (value["instrument_id"], value["revision"])
            == ("schuss-instrument-000002", revision)
        )
        inspections[revision] = dispatch_operation(
            {
                "schema_version": "schuss-operation-request-v6",
                "canonical_profile": "schuss-canonical-json-v1",
                "operation": "gills.inspect",
                "payload": {
                    "instrument_reference": _reference(instrument, "instrument_id")
                },
            },
            context,
        )
        if inspections[revision]["status"] != "success":
            raise ValueError(f"instrument revision {revision} inspection is not exact")
    if (
        inspections[2]["value"]["runtime_realization"]["revision"] != 1
        or inspections[3]["value"]["runtime_realization"]["revision"] != 2
    ):
        raise ValueError("old and corrected inspections selected different closures")

    plan = dispatch_operation(
        {
            "schema_version": "schuss-operation-request-v4",
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": "build.plan",
            "payload": {"build_request_reference": REQUEST_REFERENCE},
        },
        context,
    )
    if plan["status"] != "success":
        raise ValueError("Task 021 exact build plan failed")
    mapped_handler = descriptor()
    handler_schema = context.schemas["build_handler_descriptor"]
    if core.schema_errors(mapped_handler, handler_schema, handler_schema):
        raise ValueError("Task 021 handler descriptor schema failure")
    runtime = inspections[3]["value"]["runtime_realization"]
    if _reference(runtime, "runtime_realization_id") != RUNTIME_REFERENCE:
        raise ValueError("Task 021 inspection selected a different runtime")
    if runtime["supported_builds"] != [
        {
            "build_request_reference": REQUEST_REFERENCE,
            "instrument_reference": INSTRUMENT_REFERENCE,
            "handler": {"status": "supported", **handler_reference(mapped_handler)},
        }
    ]:
        raise ValueError("Task 021 runtime and handler closure differs")
    if task018_descriptor()["content_hash"] != (
        "sha256:ddb9e50296bc9241f7d22b9b650f23a5d1c2c8b9c3a1558a3e947797675dfead"
    ):
        raise ValueError("Task 018 handler descriptor changed")

    evidence = next(
        item
        for item in context.records["evidence"]
        if item["evidence_claim_id"] == "schuss-evidence-claim-000037"
    )
    if (
        evidence["level"] != 6
        or evidence["outcome"] != "passed"
        or evidence["subject_reference"]["stable_id"]
        != INSTRUMENT_REFERENCE["instrument_id"]
        or evidence["subject_reference"]["revision"]
        != INSTRUMENT_REFERENCE["revision"]
    ):
        raise ValueError("Task 021 level-6 claim differs")

    live_summary = runner.check_retained()
    if [item["status"] for item in live_summary["product_evidence_levels"]] != (
        ["passed"] * 6 + ["not-run"] * 2
    ):
        raise ValueError("Task 021 product evidence levels differ")

    parent = core.load_json(PARENT_RECORD_SET)
    successor = core.load_json(RECORD_SET)
    for collection in ("schema_members", "record_members"):
        if not all(item in successor[collection] for item in parent[collection]):
            raise ValueError(f"Task 018 {collection} are not preserved")
    for item in successor["schema_members"] + successor["record_members"]:
        path = ROOT / item["portable_path"]
        if not path.is_file() or core.sha256_file(path) != item["byte_sha256"]:
            raise ValueError("manifest path/hash check failed: " + item["portable_path"])

    return {
        "schema_version": "task021-validator-result-v1",
        "status": "valid",
        "record_set_reference": context.record_set_reference,
        "manifest_byte_sha256": hashlib.sha256(RECORD_SET.read_bytes()).hexdigest(),
        "generated_record_set_reference": generated_summary["record_set"],
        "task018_handler_reference": handler_reference(task018_descriptor()),
        "task021_handler_reference": handler_reference(mapped_handler),
        "inspection_statuses": {
            str(key): value["status"] for key, value in inspections.items()
        },
        "fresh_processes": live_summary["fresh_processes"],
        "generated_cpp_sha256": runner.GENERATED_CPP_SHA256,
        "target_executable_sha256": runner.TARGET_ELF_SHA256,
        "device_binary_sha256": runner.DEVICE_BINARY_SHA256,
        "build_evidence_levels": live_summary["build_evidence_levels"],
        "product_evidence_levels": live_summary["product_evidence_levels"],
        "connected_device_observation_retained": True,
        "runner_device_actions_performed": False,
        "firmware_flash_performed": False,
        "sd_card_write_performed": False,
        "real_time_validation_performed": False,
        "audible_validation_performed": False,
        "publication_performed": False,
    }


def main() -> int:
    try:
        result = validate()
    except (OSError, ValueError) as exc:
        print("Task 021 validation failed: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
