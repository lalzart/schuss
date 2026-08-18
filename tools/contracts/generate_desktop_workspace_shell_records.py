#!/usr/bin/env python3
"""Generate the additive desktop workspace-shell operation surface."""

from __future__ import annotations

import argparse
import copy
import hashlib
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "tools/contracts") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools/contracts"))

from tools.contracts import record_set_rules  # noqa: E402
from tools.contracts import validator_core as core  # noqa: E402


PARENT = ROOT / "contracts/record-sets/ai-sonic-authoring-v1.json"
OUTPUT = ROOT / "contracts/record-sets/ui-desktop-workspace-shell-v1.json"
SCHEMA_NAMES = (
    "application-capability-description-v7",
    "operation-request-v14",
    "operation-result-v14",
)


def _canonical_bytes(value: object) -> bytes:
    return (core.canonical_json(value) + "\n").encode("utf-8")


def _closed(required: list[str], properties: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "object",
        "required": required,
        "properties": properties,
        "additionalProperties": False,
    }


def _request_schema() -> dict[str, Any]:
    shell = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "operation-request-v14.schema.json",
        "title": "Schuss projects-root workspace operation request v14",
        "oneOf": [],
    }
    common = {
        "schema_version": {"const": "schuss-operation-request-v14"},
        "canonical_profile": {"const": "schuss-canonical-json-v1"},
    }
    shell["oneOf"] = [
        _closed(
            ["schema_version", "canonical_profile", "operation", "payload"],
            {
                **common,
                "operation": {"const": "workspace.projects.list"},
                "payload": _closed([], {}),
            },
        ),
        _closed(
            ["schema_version", "canonical_profile", "operation", "payload"],
            {
                **common,
                "operation": {"const": "workspace.project.create"},
                "payload": _closed(
                    ["display_name"],
                    {"display_name": {"type": "string", "minLength": 1, "maxLength": 160}},
                ),
            },
        ),
    ]
    return shell


def _result_schema() -> dict[str, Any]:
    source = core.load_json(ROOT / "schemas/operation-result-v13.schema.json")
    source["$id"] = "operation-result-v14.schema.json"
    source["title"] = "Schuss projects-root workspace operation result v14"
    source["properties"]["schema_version"] = {
        "const": "schuss-operation-result-v14"
    }
    source["properties"]["operation"]["enum"] = [
        "workspace.project.create",
        "workspace.projects.list",
        "invalid-request",
    ]
    return source


def _application_schema() -> dict[str, Any]:
    source = core.load_json(
        ROOT / "schemas/application-capability-description-v6.schema.json"
    )
    source["$id"] = "application-capability-description-v7.schema.json"
    source["title"] = "Schuss application capability description v7"
    source["properties"]["schema_version"] = {
        "const": "application-capability-description-v7"
    }
    source["properties"]["description_version"] = {
        "const": "schuss-application-capability-description-v7"
    }
    operations = source["$defs"]["operationCapability"]["properties"]
    operations["operation"]["enum"] = sorted(
        set(operations["operation"]["enum"])
        | {"workspace.projects.list", "workspace.project.create"}
    )
    operations["request_schema_version"]["pattern"] = (
        r"^schuss-operation-request-v(?:[1-9]|1[0-4])$"
    )
    operations["result_schema_version"]["pattern"] = (
        r"^schuss-operation-result-v(?:[1-9]|1[0-4])$"
    )
    operations["availability"]["enum"] = sorted(
        set(operations["availability"]["enum"]) | {"requires-projects-root"}
    )
    context_enum = source["$defs"]["contextSet"]["items"]["enum"]
    source["$defs"]["contextSet"]["items"]["enum"] = sorted(
        set(context_enum) | {"explicit-projects-root"}
    )
    gate_enum = source["$defs"]["gateSet"]["items"]["enum"]
    source["$defs"]["gateSet"]["items"]["enum"] = sorted(
        set(gate_enum) | {"create-only-child-workspace", "explicit-projects-root"}
    )
    source["properties"]["operations"]["minItems"] = 37
    source["properties"]["operations"]["maxItems"] = 37
    return source


def generated() -> tuple[dict[str, bytes], bytes, dict[str, Any]]:
    schemas = {
        "application-capability-description-v7": _application_schema(),
        "operation-request-v14": _request_schema(),
        "operation-result-v14": _result_schema(),
    }
    files = {
        f"schemas/{name}.schema.json": _canonical_bytes(schema)
        for name, schema in schemas.items()
    }
    parent = core.load_json(PARENT)
    schema_members = copy.deepcopy(parent["schema_members"])
    existing = {item["schema_version"] for item in schema_members}
    for name in sorted(SCHEMA_NAMES):
        if name in existing:
            raise ValueError(f"workspace shell schema collides with parent: {name}")
        path = f"schemas/{name}.schema.json"
        schema_members.append(
            {
                "schema_version": name,
                "portable_path": path,
                "byte_sha256": hashlib.sha256(files[path]).hexdigest(),
            }
        )
    manifest_schema = core.load_json(ROOT / record_set_rules.RECORD_SET_SCHEMA)
    manifest = {
        "schema_version": "record-set-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "record_set_id": "schuss-record-set-000027",
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
    summary = {
        "schema_version": "desktop-workspace-shell-generation-summary-v1",
        "status": "valid",
        "record_set_reference": {
            key: manifest[key]
            for key in ("record_set_id", "revision", "content_hash")
        },
        "added_schema_versions": list(SCHEMA_NAMES),
        "parent_record_members_preserved": len(manifest["record_members"]),
        "semantic_records_added": 0,
        "build_or_hardware_performed": False,
    }
    return files, _canonical_bytes(manifest), summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files, manifest, summary = generated()
    stale: list[str] = []
    for relative, data in sorted(files.items()):
        path = ROOT / relative
        if args.check:
            if not path.exists() or path.read_bytes() != data:
                stale.append(relative)
        else:
            path.write_bytes(data)
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_bytes() != manifest:
            stale.append(str(OUTPUT.relative_to(ROOT)))
        if stale:
            raise SystemExit("stale generated files: " + ", ".join(stale))
    else:
        OUTPUT.write_bytes(manifest)
    print(core.canonical_json(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
