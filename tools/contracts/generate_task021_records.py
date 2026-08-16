#!/usr/bin/env python3
"""Generate the versioned Task 021 closure without mutating Task 018 records."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/contracts")]

from packages.schuss_core.gills_mapped_backend_v2 import (  # noqa: E402
    COVERAGE_REFERENCE,
    INSTRUMENT_REFERENCE,
    REQUEST_REFERENCE,
    RUNTIME_REFERENCE,
    descriptor,
)

import record_set_rules  # noqa: E402
import validator_core as core  # noqa: E402


PARENT = ROOT / "contracts/record-sets/task018-full-gills-v1.json"
OUTPUT = ROOT / "contracts/record-sets/task021-gills-dma-safe-v1.json"
TARGET_ELF_SHA256 = "4f9bd68f5f71fc9d5bf70bd88988e7e20ff980fb46a886beff52f60c968874de"
TARGET_ELF_LENGTH = 76136
DEVICE_PROCEDURE_REFERENCE = {
    "input_kind": "procedure",
    "stable_id": "schuss-procedure-000003",
    "revision": 1,
    "content_hash": "sha256:"
    + hashlib.sha256(b"schuss-task021-volatile-ram-oled-procedure-v1").hexdigest(),
}


def _record(value: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(value)
    result["content_hash"] = "sha256:" + "0" * 64
    errors = core.schema_errors(result, schema, schema)
    if errors:
        raise ValueError("; ".join(errors))
    result["content_hash"] = core.record_content_hash(result, schema)
    return result


def _reference(record: dict[str, Any], id_field: str) -> dict[str, Any]:
    return {
        id_field: record[id_field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def _input_reference(
    record: dict[str, Any], id_field: str, input_kind: str
) -> dict[str, Any]:
    return {
        "input_kind": input_kind,
        "stable_id": record[id_field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def generated() -> tuple[dict[str, bytes], bytes, dict[str, Any]]:
    request_schema = core.load_json(ROOT / "schemas/build-request-v0.schema.json")
    runtime_schema = core.load_json(
        ROOT / "schemas/gills-runtime-realization-v0.schema.json"
    )
    handler_schema = core.load_json(
        ROOT / "schemas/build-handler-descriptor-v0.schema.json"
    )
    instrument_schema = core.load_json(ROOT / "schemas/instrument-v0.schema.json")
    coverage_schema = core.load_json(
        ROOT / "schemas/gills-mapping-coverage-v0.schema.json"
    )
    artifact_schema = core.load_json(ROOT / "schemas/artifact-descriptor-v0.schema.json")
    evidence_schema = core.load_json(ROOT / "schemas/evidence-claim-v0.schema.json")

    instrument = core.load_json(
        ROOT / "contracts/task018/instrument-executable-r2.json"
    )
    instrument["revision"] = 3
    instrument = _record(instrument, instrument_schema)
    if _reference(instrument, "instrument_id") != INSTRUMENT_REFERENCE:
        raise ValueError("Task 021 instrument identity differs from the handler selector")

    coverage = core.load_json(ROOT / "contracts/task018/coverage-executable.json")
    coverage["revision"] = 2
    coverage["instrument_reference"] = copy.deepcopy(INSTRUMENT_REFERENCE)
    coverage = _record(coverage, coverage_schema)
    if _reference(coverage, "coverage_report_id") != COVERAGE_REFERENCE:
        raise ValueError("Task 021 coverage identity differs from the handler selector")

    request = core.load_json(
        ROOT / "contracts/task018/build-request-executable-r4.json"
    )
    request["revision"] = 5
    request["instrument_reference"] = {
        "status": "included",
        **copy.deepcopy(INSTRUMENT_REFERENCE),
    }
    request = _record(request, request_schema)
    if _reference(request, "build_request_id") != REQUEST_REFERENCE:
        raise ValueError("Task 021 request identity differs from the handler selector")

    handler = descriptor()
    handler_errors = core.schema_errors(handler, handler_schema, handler_schema)
    if handler_errors:
        raise ValueError("handler descriptor: " + "; ".join(handler_errors))

    runtime = core.load_json(
        ROOT / "contracts/task018/runtime-realization-mapped.json"
    )
    runtime["revision"] = 2
    runtime["supported_builds"][0]["build_request_reference"] = copy.deepcopy(
        REQUEST_REFERENCE
    )
    runtime["supported_builds"][0]["instrument_reference"] = copy.deepcopy(
        INSTRUMENT_REFERENCE
    )
    runtime["supported_builds"][0]["handler"] = {
        "status": "supported",
        **_reference(handler, "build_handler_id"),
    }
    runtime["display_bindings"][0]["rationale"] = (
        "Task 021 compiles the accepted text buffer and uses dedicated SRAM2 "
        "command and page buffers for the DMA-backed SH1106 transport boundary."
    )
    runtime["limitations"] = [
        "Task 021 connected-device evidence is limited to exact volatile-RAM "
        "execution and upright four-line OLED output; controls, audio, real-time "
        "behavior, and persistence remain unproven.",
        "Optional expansion and independently owned Core connectors remain "
        "unresolved where the evidence packet says so.",
    ]
    runtime = _record(runtime, runtime_schema)
    if _reference(runtime, "runtime_realization_id") != RUNTIME_REFERENCE:
        raise ValueError("Task 021 runtime identity differs from the handler selector")

    device = core.load_json(ROOT / "contracts/task018/gills-device-profile-r2.json")
    target = core.load_json(ROOT / "contracts/task009/ksoloti-core-v0-r2.json")
    closure_identity = [
        _reference(request, "build_request_id"),
        _reference(runtime, "runtime_realization_id"),
        _reference(instrument, "instrument_id"),
        _reference(device, "device_profile_id"),
        _reference(target, "compute_target_id"),
        _reference(handler, "build_handler_id"),
    ]
    closure_hash = "sha256:" + hashlib.sha256(
        core.canonical_json(closure_identity).encode("utf-8")
    ).hexdigest()
    artifact = _record(
        {
            "schema_version": "artifact-descriptor-v0",
            "canonical_profile": "schuss-canonical-json-v1",
            "artifact_id": "schuss-artifact-000029",
            "revision": 1,
            "content_hash": "sha256:" + "0" * 64,
            "artifact_kind": "target-executable",
            "media_type": "application/x-elf",
            "byte_length": TARGET_ELF_LENGTH,
            "byte_sha256": TARGET_ELF_SHA256,
            "producer_stage": "target-compile-link",
            "producer_contract": {
                "producer_id": "schuss-gills-mapped-backend",
                "producer_version": "task021-handler-r2",
            },
            "input_closure_hash": closure_hash,
            "portable_locator": "sha256/" + TARGET_ELF_SHA256,
            "parent_artifact_references": [],
            "source_map_artifact_references": [],
        },
        artifact_schema,
    )
    evidence = _record(
        {
            "schema_version": "evidence-claim-v0",
            "canonical_profile": "schuss-canonical-json-v1",
            "evidence_claim_id": "schuss-evidence-claim-000037",
            "revision": 1,
            "content_hash": "sha256:" + "0" * 64,
            "level": 6,
            "level_name": "connected-device-execution",
            "subject_reference": {
                "subject_kind": "instrument",
                "stable_id": instrument["instrument_id"],
                "revision": instrument["revision"],
                "content_hash": instrument["content_hash"],
                "stage": "connected-device-execution",
            },
            "method": "volatile-ram-upload-and-oled-observation",
            "outcome": "passed",
            "evidence_inputs": [
                _input_reference(request, "build_request_id", "build-request"),
                _input_reference(instrument, "instrument_id", "instrument"),
                _input_reference(device, "device_profile_id", "device-profile"),
                _input_reference(target, "compute_target_id", "compute-target"),
                _input_reference(artifact, "artifact_id", "artifact"),
                copy.deepcopy(DEVICE_PROCEDURE_REFERENCE),
            ],
            "limitations": [
                "Passed only on Ksoloti Core USB serial "
                "003D00363532511735393330 running firmware 1.1.0.0 with CRC "
                "5021D42A by volatile RAM upload.",
                "Visual observation established upright display and the four words "
                "SCHUSS, BLEND, PICKUP, and TASK018; it did not measure controls or audio.",
                "Levels 7 and 8, persistence, flash, SD-card writes, electrical safety, "
                "and release readiness remain unproven.",
            ],
            "producer_identity": {
                "producer_kind": "device-procedure",
                "producer_id": "schuss-task021-connected-device-procedure",
                "version": "task021-device-procedure-v1",
                "content_hash": DEVICE_PROCEDURE_REFERENCE["content_hash"],
            },
        },
        evidence_schema,
    )

    records: dict[str, tuple[str, dict[str, Any]]] = {
        "instrument-executable-r3.json": ("instrument", instrument),
        "coverage-executable-r2.json": ("gills-mapping-coverage", coverage),
        "build-request-executable-r5.json": ("request", request),
        "runtime-realization-mapped-r2.json": ("gills-runtime-realization", runtime),
        "connected-target-executable.json": ("artifact", artifact),
        "connected-device-evidence.json": ("evidence", evidence),
    }
    files = {
        f"contracts/task021/{name}": core.canonical_json(record).encode("utf-8") + b"\n"
        for name, (_, record) in records.items()
    }
    parent = core.load_json(PARENT)
    record_members = copy.deepcopy(parent["record_members"])
    for name, (kind, record) in records.items():
        relative = f"contracts/task021/{name}"
        id_field = next(field for field in record_set_rules.ID_FIELDS if field in record)
        record_members.append(
            {
                "record_kind": kind,
                "stable_id": record[id_field],
                "revision": record["revision"],
                "content_hash": record["content_hash"],
                "portable_path": relative,
                "byte_sha256": hashlib.sha256(files[relative]).hexdigest(),
            }
        )
    manifest_schema = core.load_json(ROOT / record_set_rules.RECORD_SET_SCHEMA)
    manifest = {
        "schema_version": "record-set-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "record_set_id": "schuss-record-set-000013",
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "purpose": "prospective-task",
        "parent_reference": {
            "status": "included",
            **{
                key: parent[key]
                for key in ("record_set_id", "revision", "content_hash")
            },
        },
        "schema_members": copy.deepcopy(parent["schema_members"]),
        "record_members": sorted(
            record_members, key=lambda item: (item["byte_sha256"], item["portable_path"])
        ),
        "enforced_directories": sorted(
            parent["enforced_directories"] + ["contracts/task021"]
        ),
    }
    manifest["content_hash"] = core.record_content_hash(manifest, manifest_schema)
    summary = {
        "request": _reference(request, "build_request_id"),
        "instrument": _reference(instrument, "instrument_id"),
        "coverage": _reference(coverage, "coverage_report_id"),
        "runtime": _reference(runtime, "runtime_realization_id"),
        "handler": _reference(handler, "build_handler_id"),
        "artifact": _reference(artifact, "artifact_id"),
        "evidence": _reference(evidence, "evidence_claim_id"),
        "record_set": {
            key: manifest[key]
            for key in ("record_set_id", "revision", "content_hash")
        },
    }
    return files, core.canonical_json(manifest).encode("utf-8") + b"\n", summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        files, manifest, summary = generated()
        files[OUTPUT.relative_to(ROOT).as_posix()] = manifest
        stale = [
            relative
            for relative, payload in files.items()
            if not (ROOT / relative).is_file()
            or (ROOT / relative).read_bytes() != payload
        ]
        if args.check and stale:
            raise ValueError(
                "Task 021 generated files are stale: " + ", ".join(sorted(stale))
            )
        if not args.check:
            for relative, payload in files.items():
                path = ROOT / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
    except (OSError, ValueError) as exc:
        print("Task 021 record generation failed: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
