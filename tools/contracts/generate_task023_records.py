#!/usr/bin/env python3
"""Generate the exact Task 023 schema-only application-surface record set."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/contracts"))

import record_set_rules  # noqa: E402
import validator_core as core  # noqa: E402


PARENT = ROOT / "contracts/record-sets/task022-gills-panel-diagnostic-v1.json"
OUTPUT = ROOT / "contracts/record-sets/task023-application-spine-v1.json"
SCHEMA_ADDITIONS = {
    "application-capability-description-v0": "schemas/application-capability-description-v0.schema.json",
    "operation-request-v7": "schemas/operation-request-v7.schema.json",
    "operation-result-v7": "schemas/operation-result-v7.schema.json",
}


def generated() -> tuple[bytes, dict[str, object]]:
    parent = core.load_json(PARENT)
    parent_reference = {
        key: parent[key] for key in ("record_set_id", "revision", "content_hash")
    }
    schema_members = copy.deepcopy(parent["schema_members"])
    existing_versions = {item["schema_version"] for item in schema_members}
    for version, relative in sorted(SCHEMA_ADDITIONS.items()):
        if version in existing_versions:
            raise ValueError(f"Task 023 parent already contains schema {version}")
        path = ROOT / relative
        schema = core.load_json(path)
        if schema.get("$id") != Path(relative).name:
            raise ValueError(f"Task 023 schema $id differs for {relative}")
        annotations = core.validate_schema_annotations(schema)
        if annotations:
            raise ValueError(f"Task 023 schema annotations invalid for {relative}: {annotations}")
        schema_members.append(
            {
                "schema_version": version,
                "portable_path": relative,
                "byte_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    manifest_schema = core.load_json(ROOT / record_set_rules.RECORD_SET_SCHEMA)
    manifest = {
        "schema_version": "record-set-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "record_set_id": "schuss-record-set-000015",
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "purpose": "prospective-task",
        "parent_reference": {"status": "included", **parent_reference},
        "schema_members": sorted(
            schema_members,
            key=lambda item: (item["byte_sha256"], item["portable_path"]),
        ),
        "record_members": copy.deepcopy(parent["record_members"]),
        "enforced_directories": copy.deepcopy(parent["enforced_directories"]),
    }
    errors = core.schema_errors(manifest, manifest_schema, manifest_schema)
    if errors:
        raise ValueError("; ".join(errors))
    manifest["content_hash"] = core.record_content_hash(manifest, manifest_schema)
    payload = core.canonical_json(manifest).encode("utf-8") + b"\n"
    summary = {
        "schema_version": "task023-record-generation-summary-v1",
        "status": "valid",
        "parent_record_set": parent_reference,
        "record_set": {
            key: manifest[key]
            for key in ("record_set_id", "revision", "content_hash")
        },
        "added_schema_versions": sorted(SCHEMA_ADDITIONS),
        "added_record_count": 0,
    }
    return payload, summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        payload, summary = generated()
        stale = not OUTPUT.is_file() or OUTPUT.read_bytes() != payload
        if args.check and stale:
            raise ValueError("Task 023 generated record set is stale")
        if not args.check:
            OUTPUT.parent.mkdir(parents=True, exist_ok=True)
            OUTPUT.write_bytes(payload)
    except (OSError, ValueError) as exc:
        print("Task 023 record generation failed: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
