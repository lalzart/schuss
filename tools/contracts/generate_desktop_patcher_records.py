#!/usr/bin/env python3
"""Generate the additive desktop patcher operation schemas and record set."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "tools/contracts") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools/contracts"))

from tools.contracts import record_set_rules  # noqa: E402
from tools.contracts import validator_core as core  # noqa: E402


PARENT = ROOT / "contracts/record-sets/task030-complete-mutable-catalog-v1.json"
OUTPUT = ROOT / "contracts/record-sets/ui-desktop-patcher-authoring-v1.json"
SCHEMA_NAMES = (
    "application-capability-description-v4",
    "operation-request-v11",
    "operation-result-v11",
)


def _canonical_bytes(value: object) -> bytes:
    return (core.canonical_json(value) + "\n").encode("utf-8")


def _rename_edit() -> dict[str, object]:
    return {
        "type": "object",
        "required": ["edit", "display_name"],
        "properties": {
            "edit": {"const": "set-graph-display-name"},
            "display_name": {"type": "string", "minLength": 1, "maxLength": 160},
        },
        "additionalProperties": False,
    }


def _request_schema() -> dict[str, object]:
    source = core.load_json(ROOT / "schemas/operation-request-v8.schema.json")
    defs = source["$defs"]
    edit = copy.deepcopy(defs["edit"])
    edit["oneOf"].append(_rename_edit())

    component_reference = {
        "type": "object",
        "required": ["component_contract_id", "revision", "content_hash"],
        "properties": {
            "component_contract_id": {
                "type": "string",
                "pattern": "^schuss-component-contract-[0-9]{6}$",
            },
            "revision": {"type": "integer", "minimum": 1},
            "content_hash": {"$ref": "#/$defs/contentHash"},
        },
        "additionalProperties": False,
    }
    component_inspect = {
        "type": "object",
        "required": ["schema_version", "canonical_profile", "operation", "payload"],
        "properties": {
            "schema_version": {"const": "schuss-operation-request-v11"},
            "canonical_profile": {"const": "schuss-canonical-json-v1"},
            "operation": {"const": "component.inspect"},
            "payload": {
                "type": "object",
                "required": ["component_contract_reference"],
                "properties": {
                    "component_contract_reference": {
                        "$ref": "#/$defs/componentReference"
                    }
                },
                "additionalProperties": False,
            },
        },
        "additionalProperties": False,
    }
    graph_transact = {
        "type": "object",
        "required": ["schema_version", "canonical_profile", "operation", "payload"],
        "properties": {
            "schema_version": {"const": "schuss-operation-request-v11"},
            "canonical_profile": {"const": "schuss-canonical-json-v1"},
            "operation": {"const": "graph.transact"},
            "payload": {
                "type": "object",
                "required": ["graph_reference", "base_content_hash", "edits"],
                "properties": {
                    "graph_reference": {"$ref": "#/$defs/graphReference"},
                    "base_content_hash": {"$ref": "#/$defs/contentHash"},
                    "edits": {
                        "type": "array",
                        "x-schuss-array-kind": "sequence",
                        "minItems": 1,
                        "items": {"$ref": "#/$defs/edit"},
                    },
                },
                "additionalProperties": False,
            },
        },
        "additionalProperties": False,
    }
    profile_transact = copy.deepcopy(defs["profileTransact"])
    profile_transact["properties"]["schema_version"]["const"] = (
        "schuss-operation-request-v11"
    )

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "operation-request-v11.schema.json",
        "title": "Schuss desktop patcher operation request v11",
        "oneOf": [
            {"$ref": "#/$defs/componentInspect"},
            {"$ref": "#/$defs/graphTransact"},
            {"$ref": "#/$defs/profileTransact"},
        ],
        "$defs": {
            "contentHash": copy.deepcopy(defs["contentHash"]),
            "projectReference": copy.deepcopy(defs["projectReference"]),
            "graphReference": copy.deepcopy(defs["graphReference"]),
            "componentReference": component_reference,
            "facetValue": copy.deepcopy(defs["facetValue"]),
            "node": copy.deepcopy(defs["node"]),
            "portEndpoint": copy.deepcopy(defs["portEndpoint"]),
            "connection": copy.deepcopy(defs["connection"]),
            "edit": edit,
            "componentInspect": component_inspect,
            "graphTransact": graph_transact,
            "profileTransact": profile_transact,
        },
    }


def _result_schema() -> dict[str, object]:
    source = core.load_json(ROOT / "schemas/operation-result-v8.schema.json")
    source["$id"] = "operation-result-v11.schema.json"
    source["title"] = "Schuss desktop patcher operation result v11"
    source["properties"]["schema_version"]["const"] = (
        "schuss-operation-result-v11"
    )
    source["properties"]["operation"]["enum"] = [
        "component.inspect",
        "graph.transact",
        "project.profile.transact",
        "invalid-request",
    ]
    return source


def _capability_schema() -> dict[str, object]:
    source = core.load_json(
        ROOT / "schemas/application-capability-description-v3.schema.json"
    )
    source["$id"] = "application-capability-description-v4.schema.json"
    source["title"] = "Schuss application capability description v4"
    source["properties"]["schema_version"]["const"] = (
        "application-capability-description-v4"
    )
    source["properties"]["description_version"]["const"] = (
        "schuss-application-capability-description-v4"
    )
    operations = source["properties"]["operations"]
    operations["minItems"] = 21
    operations["maxItems"] = 21
    entry = source["$defs"]["operationCapability"]["properties"]
    entry["domain_group"]["enum"] = sorted(
        set(entry["domain_group"]["enum"]) | {"component"}
    )
    entry["operation"]["enum"] = sorted(
        set(entry["operation"]["enum"]) | {"component.inspect"}
    )
    entry["request_schema_version"]["pattern"] = (
        "^schuss-operation-request-v(?:[1-9]|10|11)$"
    )
    entry["result_schema_version"]["pattern"] = (
        "^schuss-operation-result-v(?:[1-9]|10|11)$"
    )
    return source


def generated() -> tuple[dict[str, bytes], bytes, dict[str, object]]:
    schemas = {
        "operation-request-v11": _request_schema(),
        "operation-result-v11": _result_schema(),
        "application-capability-description-v4": _capability_schema(),
    }
    for name, schema in schemas.items():
        errors = core.validate_schema_annotations(schema)
        if errors:
            raise ValueError(f"{name}: " + "; ".join(errors))

    files = {
        f"schemas/{name}.schema.json": _canonical_bytes(schema)
        for name, schema in schemas.items()
    }
    parent = core.load_json(PARENT)
    schema_members = copy.deepcopy(parent["schema_members"])
    existing = {item["schema_version"] for item in schema_members}
    for name in sorted(SCHEMA_NAMES):
        if name in existing:
            raise ValueError(f"desktop patcher schema collides with parent: {name}")
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
        "record_set_id": "schuss-record-set-000024",
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
        "schema_version": "desktop-patcher-generation-summary-v1",
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
    try:
        files, manifest, summary = generated()
        expected = {**files, OUTPUT.relative_to(ROOT).as_posix(): manifest}
        stale = [
            path
            for path, payload in expected.items()
            if not (ROOT / path).is_file() or (ROOT / path).read_bytes() != payload
        ]
        if args.check and stale:
            raise ValueError(
                "desktop patcher generated outputs are stale: "
                + ", ".join(sorted(stale))
            )
        if not args.check:
            for relative, payload in expected.items():
                path = ROOT / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
    except (KeyError, OSError, ValueError) as exc:
        print("Desktop patcher generation failed: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
