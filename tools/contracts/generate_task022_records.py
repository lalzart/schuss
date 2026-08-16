#!/usr/bin/env python3
"""Generate the exact Task 022 offline artifact successor record set."""

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

from packages.schuss_core.gills_direct_backend import BACKEND_REFERENCE  # noqa: E402
from packages.schuss_core.gills_mapped_backend import DEVICE_REFERENCE  # noqa: E402
from run_task022 import (  # noqa: E402
    GENERATED_CPP_SHA256,
    PARENT_RECORD_SET_REFERENCE,
    TARGET_ELF_LENGTH,
    TARGET_ELF_SHA256,
    diagnostic_identity,
)

import record_set_rules  # noqa: E402
import validator_core as core  # noqa: E402


PARENT = ROOT / "contracts/record-sets/task021-gills-dma-safe-v1.json"
OUTPUT = ROOT / "contracts/record-sets/task022-gills-panel-diagnostic-v1.json"
TARGET_REFERENCE = {
    "compute_target_id": "schuss-compute-target-000001",
    "revision": 2,
    "content_hash": "sha256:d8a9652bd079d0f2a8806cc4922f2a380c8092549f267047d5a4a0360b4a6753",
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


def generated() -> tuple[dict[str, bytes], bytes, dict[str, Any]]:
    artifact_schema = core.load_json(ROOT / "schemas/artifact-descriptor-v0.schema.json")
    closure = [
        diagnostic_identity(),
        PARENT_RECORD_SET_REFERENCE,
        DEVICE_REFERENCE,
        TARGET_REFERENCE,
        BACKEND_REFERENCE,
        {"generated_cpp_sha256": GENERATED_CPP_SHA256},
    ]
    closure_hash = "sha256:" + hashlib.sha256(
        core.canonical_json(closure).encode("utf-8")
    ).hexdigest()
    artifact = _record(
        {
            "schema_version": "artifact-descriptor-v0",
            "canonical_profile": "schuss-canonical-json-v1",
            "artifact_id": "schuss-artifact-000030",
            "revision": 1,
            "content_hash": "sha256:" + "0" * 64,
            "artifact_kind": "target-executable",
            "media_type": "application/x-elf",
            "byte_length": TARGET_ELF_LENGTH,
            "byte_sha256": TARGET_ELF_SHA256,
            "producer_stage": "target-compile-link",
            "producer_contract": {
                "producer_id": "schuss-gills-panel-diagnostic-builder",
                "producer_version": "task022-offline-builder-v1",
            },
            "input_closure_hash": closure_hash,
            "portable_locator": "sha256/" + TARGET_ELF_SHA256,
            "parent_artifact_references": [],
            "source_map_artifact_references": [],
        },
        artifact_schema,
    )
    relative = "contracts/task022/panel-diagnostic-target-executable.json"
    files = {relative: core.canonical_json(artifact).encode("utf-8") + b"\n"}
    parent = core.load_json(PARENT)
    if {
        key: parent[key]
        for key in ("record_set_id", "revision", "content_hash")
    } != PARENT_RECORD_SET_REFERENCE:
        raise ValueError("Task 022 parent record-set identity differs")
    record_members = copy.deepcopy(parent["record_members"])
    record_members.append(
        {
            "record_kind": "artifact",
            "stable_id": artifact["artifact_id"],
            "revision": artifact["revision"],
            "content_hash": artifact["content_hash"],
            "portable_path": relative,
            "byte_sha256": hashlib.sha256(files[relative]).hexdigest(),
        }
    )
    manifest_schema = core.load_json(ROOT / record_set_rules.RECORD_SET_SCHEMA)
    manifest = {
        "schema_version": "record-set-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "record_set_id": "schuss-record-set-000014",
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "purpose": "prospective-task",
        "parent_reference": {"status": "included", **PARENT_RECORD_SET_REFERENCE},
        "schema_members": copy.deepcopy(parent["schema_members"]),
        "record_members": sorted(
            record_members,
            key=lambda item: (item["byte_sha256"], item["portable_path"]),
        ),
        "enforced_directories": sorted(
            parent["enforced_directories"] + ["contracts/task022"]
        ),
    }
    manifest["content_hash"] = core.record_content_hash(manifest, manifest_schema)
    summary = {
        "artifact": _reference(artifact, "artifact_id"),
        "diagnostic_identity": diagnostic_identity(),
        "parent_record_set": PARENT_RECORD_SET_REFERENCE,
        "record_set": {
            key: manifest[key]
            for key in ("record_set_id", "revision", "content_hash")
        },
        "instrument_reference": {"status": "omitted"},
        "device_actions_performed": False,
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
                "Task 022 generated files are stale: " + ", ".join(sorted(stale))
            )
        if not args.check:
            for relative, payload in files.items():
                path = ROOT / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
    except (OSError, ValueError) as exc:
        print("Task 022 record generation failed: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
