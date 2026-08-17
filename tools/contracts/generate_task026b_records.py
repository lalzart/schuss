from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/contracts"))

import validator_core as core  # noqa: E402


PARENT = ROOT / "contracts/record-sets/task026a-executable-profile-v1.json"
MANIFEST = ROOT / "contracts/record-sets/task026-authoring-workflow-v1.json"
SCHEMAS = (
    "schemas/application-capability-description-v1.schema.json",
    "schemas/operation-request-v8.schema.json",
    "schemas/operation-result-v8.schema.json",
    "schemas/project-write-plan-v1.schema.json",
)


def generated() -> dict:
    parent = core.load_json(PARENT)
    schema_members = copy.deepcopy(parent["schema_members"])
    existing = {item["schema_version"] for item in schema_members}
    for portable_path in SCHEMAS:
        schema = core.load_json(ROOT / portable_path)
        schema_version = schema["$id"].removesuffix(".schema.json")
        if schema_version in existing:
            raise ValueError(f"duplicate schema version {schema_version}")
        existing.add(schema_version)
        schema_members.append(
            {
                "schema_version": schema_version,
                "portable_path": portable_path,
                "byte_sha256": core.sha256_file(ROOT / portable_path),
            }
        )
    manifest = {
        "schema_version": "record-set-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "record_set_id": "schuss-record-set-000019",
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
        "schema_members": sorted(
            schema_members, key=lambda item: item["portable_path"]
        ),
        "record_members": copy.deepcopy(parent["record_members"]),
        "enforced_directories": copy.deepcopy(parent["enforced_directories"]),
    }
    schema = core.load_json(
        ROOT / "schemas/prerequisite/record-set-v0.schema.json"
    )
    errors = core.schema_errors(manifest, schema, schema)
    if errors:
        raise ValueError("; ".join(errors))
    manifest["content_hash"] = core.record_content_hash(manifest, schema)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    manifest = generated()
    data = core.canonical_json(manifest).encode("utf-8") + b"\n"
    if args.check:
        if not MANIFEST.is_file() or MANIFEST.read_bytes() != data:
            raise SystemExit("stale Task 026B record set")
        print("Task 026B generated record set: fresh")
        return 0
    MANIFEST.write_bytes(data)
    print("wrote Task 026B record set")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
