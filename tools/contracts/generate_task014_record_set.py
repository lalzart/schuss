#!/usr/bin/env python3
"""Generate the exact additive record set for Task 014."""

from __future__ import annotations

import argparse
import copy
import hashlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools/contracts"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import record_set_rules
import validator_core as core


PARENT = ROOT / "contracts/record-sets/task013-compiler-front-half-v1.json"
OUTPUT = ROOT / "contracts/record-sets/task014-build-execution-v1.json"
SCHEMA_PATHS = (
    "schemas/build-execution-result-v0.schema.json",
    "schemas/build-handler-descriptor-v0.schema.json",
    "schemas/operation-request-v5.schema.json",
    "schemas/operation-result-v5.schema.json",
)


def _schema_member(relative: str) -> dict[str, str]:
    path = ROOT / relative
    schema = core.load_json(path)
    return {
        "schema_version": schema["$id"].removesuffix(".schema.json"),
        "portable_path": relative,
        "byte_sha256": core.sha256_file(path),
    }


def generated_bytes() -> bytes:
    parent = core.load_json(PARENT)
    manifest = {
        "schema_version": "record-set-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "record_set_id": "schuss-record-set-000008",
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "purpose": "prospective-task",
        "parent_reference": {"status": "included", **{key: parent[key] for key in ("record_set_id", "revision", "content_hash")}},
        "schema_members": sorted(
            [*copy.deepcopy(parent["schema_members"]), *map(_schema_member, SCHEMA_PATHS)],
            key=lambda value: (value["schema_version"], value["portable_path"]),
        ),
        "record_members": copy.deepcopy(parent["record_members"]),
        "enforced_directories": copy.deepcopy(parent["enforced_directories"]),
    }
    schema = core.load_json(ROOT / record_set_rules.RECORD_SET_SCHEMA)
    manifest["content_hash"] = core.record_content_hash(manifest, schema)
    errors = core.schema_errors(manifest, schema, schema)
    if errors:
        raise ValueError("generated Task 014 record set is invalid: " + "; ".join(errors))
    return core.canonical_json(manifest).encode("utf-8") + b"\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = generated_bytes()
    current = OUTPUT.read_bytes() if OUTPUT.is_file() else None
    if args.check:
        if current != expected:
            print(f"Task 014 record set is stale: {OUTPUT.relative_to(ROOT)}", file=sys.stderr)
            return 1
        print(f"Task 014 record set passed: bytes_sha256={hashlib.sha256(expected).hexdigest()}")
        return 0
    OUTPUT.write_bytes(expected)
    print(f"Task 014 record set generated: bytes_sha256={hashlib.sha256(expected).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
