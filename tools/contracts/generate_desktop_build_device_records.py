#!/usr/bin/env python3
"""Generate additive desktop build/device schemas and exact successor set."""

from __future__ import annotations

import argparse
import copy
import hashlib
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "tools/contracts") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools/contracts"))

from tools.contracts import record_set_rules  # noqa: E402
from tools.contracts import validator_core as core  # noqa: E402


PARENT = ROOT / "contracts/record-sets/ui-desktop-patcher-authoring-v1.json"
OUTPUT = ROOT / "contracts/record-sets/ui-desktop-build-device-v1.json"
SCHEMA_NAMES = (
    "application-capability-description-v5",
    "operation-request-v12",
    "operation-result-v12",
)


def _canonical_bytes(value: object) -> bytes:
    return (core.canonical_json(value) + "\n").encode("utf-8")


def _operation(name: str, payload: dict[str, object]) -> dict[str, object]:
    return {
        "type": "object",
        "required": ["schema_version", "canonical_profile", "operation", "payload"],
        "properties": {
            "schema_version": {"const": "schuss-operation-request-v12"},
            "canonical_profile": {"const": "schuss-canonical-json-v1"},
            "operation": {"const": name},
            "payload": payload,
        },
        "additionalProperties": False,
    }


def _payload(required: list[str], properties: dict[str, object]) -> dict[str, object]:
    return {
        "type": "object",
        "required": required,
        "properties": properties,
        "additionalProperties": False,
    }


def _request_schema() -> dict[str, object]:
    source = core.load_json(ROOT / "schemas/operation-request-v5.schema.json")
    request_reference = copy.deepcopy(source["$defs"]["requestReference"])
    session_id = {
        "type": "string",
        "pattern": "^build-session-[0-9]{6}$",
    }
    device_id = {
        "type": "string",
        "pattern": "^device-session-[0-9]{6}$",
    }
    upload_id = {
        "type": "string",
        "pattern": "^upload-session-[0-9]{6}$",
    }
    definitions = {
        "contentHash": copy.deepcopy(source["$defs"]["contentHash"]),
        "requestReference": request_reference,
        "buildSessionId": session_id,
        "deviceSessionId": device_id,
        "uploadSessionId": upload_id,
    }
    operations = [
        _operation(
            "build.session.start",
            _payload(
                ["build_request_reference", "execution_intent"],
                {
                    "build_request_reference": {"$ref": "#/$defs/requestReference"},
                    "execution_intent": {"const": True},
                },
            ),
        ),
        _operation(
            "build.session.inspect",
            _payload(
                ["build_session_id"],
                {"build_session_id": {"$ref": "#/$defs/buildSessionId"}},
            ),
        ),
        _operation(
            "device.session.discover",
            _payload(
                ["build_request_reference", "discovery_intent"],
                {
                    "build_request_reference": {"$ref": "#/$defs/requestReference"},
                    "discovery_intent": {"const": True},
                },
            ),
        ),
        _operation(
            "device.session.inspect",
            _payload(
                ["device_session_id"],
                {"device_session_id": {"$ref": "#/$defs/deviceSessionId"}},
            ),
        ),
        _operation(
            "device.upload.start",
            _payload(
                [
                    "device_session_id",
                    "build_session_id",
                    "artifact_sha256",
                    "upload_intent",
                    "start_patch",
                ],
                {
                    "device_session_id": {"$ref": "#/$defs/deviceSessionId"},
                    "build_session_id": {"$ref": "#/$defs/buildSessionId"},
                    "artifact_sha256": {
                        "type": "string",
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "upload_intent": {"const": "explicit-volatile-ram"},
                    "start_patch": {"type": "boolean"},
                },
            ),
        ),
        _operation(
            "device.upload.inspect",
            _payload(
                ["upload_session_id"],
                {"upload_session_id": {"$ref": "#/$defs/uploadSessionId"}},
            ),
        ),
    ]
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "operation-request-v12.schema.json",
        "title": "Schuss desktop build and device operation request v12",
        "oneOf": operations,
        "$defs": definitions,
    }


def _result_schema() -> dict[str, object]:
    source = core.load_json(ROOT / "schemas/operation-result-v5.schema.json")
    source["$id"] = "operation-result-v12.schema.json"
    source["title"] = "Schuss desktop build and device operation result v12"
    source["properties"]["schema_version"]["const"] = "schuss-operation-result-v12"
    source["properties"]["operation"]["enum"] = [
        "build.session.start",
        "build.session.inspect",
        "device.session.discover",
        "device.session.inspect",
        "device.upload.start",
        "device.upload.inspect",
        "invalid-request",
    ]
    return source


def _capability_schema() -> dict[str, object]:
    source = core.load_json(
        ROOT / "schemas/application-capability-description-v4.schema.json"
    )
    source["$id"] = "application-capability-description-v5.schema.json"
    source["title"] = "Schuss application capability description v5"
    source["properties"]["schema_version"]["const"] = (
        "application-capability-description-v5"
    )
    source["properties"]["description_version"]["const"] = (
        "schuss-application-capability-description-v5"
    )
    operations = source["properties"]["operations"]
    operations["minItems"] = 27
    operations["maxItems"] = 27
    entry = source["$defs"]["operationCapability"]["properties"]
    entry["domain_group"]["enum"] = sorted(
        set(entry["domain_group"]["enum"]) | {"device"}
    )
    entry["operation"]["enum"] = sorted(
        set(entry["operation"]["enum"])
        | {
            "build.session.start",
            "build.session.inspect",
            "device.session.discover",
            "device.session.inspect",
            "device.upload.start",
            "device.upload.inspect",
        }
    )
    entry["effect_class"]["enum"] = sorted(
        set(entry["effect_class"]["enum"])
        | {"device-read", "device-volatile-write"}
    )
    entry["availability"]["enum"] = sorted(
        set(entry["availability"]["enum"]) | {"requires-session-services"}
    )
    source["$defs"]["contextSet"]["items"]["enum"] = sorted(
        set(source["$defs"]["contextSet"]["items"]["enum"])
        | {
            "exact-project-snapshot",
            "process-local-build-service",
            "process-local-device-service",
        }
    )
    source["$defs"]["gateSet"]["items"]["enum"] = sorted(
        set(source["$defs"]["gateSet"]["items"]["enum"])
        | {
            "discovery-intent",
            "exact-artifact",
            "exact-session",
            "volatile-upload-intent",
        }
    )
    entry["request_schema_version"]["pattern"] = (
        "^schuss-operation-request-v(?:[1-9]|10|11|12)$"
    )
    entry["result_schema_version"]["pattern"] = (
        "^schuss-operation-result-v(?:[1-9]|10|11|12)$"
    )
    return source


def generated() -> tuple[dict[str, bytes], bytes, dict[str, object]]:
    schemas = {
        "operation-request-v12": _request_schema(),
        "operation-result-v12": _result_schema(),
        "application-capability-description-v5": _capability_schema(),
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
            raise ValueError(f"desktop build/device schema collides with parent: {name}")
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
        "record_set_id": "schuss-record-set-000025",
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
        "schema_version": "desktop-build-device-generation-summary-v1",
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
    expected = {**files, OUTPUT.relative_to(ROOT).as_posix(): manifest}
    if args.check:
        stale = [
            path
            for path, payload in expected.items()
            if not (ROOT / path).is_file() or (ROOT / path).read_bytes() != payload
        ]
        if stale:
            raise SystemExit("stale desktop build/device generated files: " + ", ".join(stale))
    else:
        for path, payload in expected.items():
            destination = ROOT / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(payload)
    print(core.canonical_json(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
