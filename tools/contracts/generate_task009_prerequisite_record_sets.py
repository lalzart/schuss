#!/usr/bin/env python3
"""Generate exact accepted and prospective record-set manifests."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import validator_core as core


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "schemas/prerequisite/record-set-v0.schema.json"

ACCEPTED_SCHEMAS = (
    "schemas/artifact-descriptor-v0.schema.json",
    "schemas/backend-invocation-input-v1.schema.json",
    "schemas/backend-v0.schema.json",
    "schemas/binding-eligibility-v0.schema.json",
    "schemas/build-environment-v0.schema.json",
    "schemas/build-request-v0.schema.json",
    "schemas/build-result-v0.schema.json",
    "schemas/capability-vocabulary-v0.schema.json",
    "schemas/catalog-family-companion-v0.schema.json",
    "schemas/component-contract-v0.schema.json",
    "schemas/compute-target-v0.schema.json",
    "schemas/device-profile-v0.schema.json",
    "schemas/dsp-graph-v0.schema.json",
    "schemas/evidence-claim-v0.schema.json",
    "schemas/implementation-binding-v0.schema.json",
    "schemas/instrument-v0.schema.json",
    "schemas/operation-request-v1.schema.json",
    "schemas/operation-result-v1.schema.json",
    "schemas/resource-report-v0.schema.json",
)

PREREQUISITE_SCHEMAS = (
    "schemas/prerequisite/conformance-probe-evidence-v0.schema.json",
    "schemas/prerequisite/conformance-probe-input-v0.schema.json",
    "schemas/prerequisite/conformance-probe-procedure-v0.schema.json",
    "schemas/prerequisite/conformance-probe-result-v0.schema.json",
    "schemas/prerequisite/prerequisite-environment-v0.schema.json",
    "schemas/prerequisite/record-set-v0.schema.json",
)

ACCEPTED_RECORDS = (
    ("backend", "contracts/backends/legacy-ksoloti-v0.json"),
    ("eligibility", "contracts/binding-eligibility/crossfader-mixed-legacy-v0.json"),
    ("environment", "contracts/build-environments/arm-none-eabi-unresolved-v0.json"),
    ("environment", "contracts/build-environments/ksoloti-runtime-abi-unresolved-v0.json"),
    ("request", "contracts/build-requests/blend-validation-v0.json"),
    ("capability", "contracts/capabilities/task007-v0.json"),
    ("catalog-family", "contracts/catalog-families/crossfader-v1.json"),
    ("component-contract", "contracts/component-contracts/crossfader-audio-v0.json"),
    ("component-contract", "contracts/component-contracts/crossfader-control-v0.json"),
    ("component-contract", "contracts/component-contracts/crossfader-mixed-v0.json"),
    ("target", "contracts/compute-targets/ksoloti-core-v0.json"),
    ("device-profile", "contracts/device-profiles/gills-minimal-v0.json"),
    ("dsp-graph", "contracts/graphs/blend-crossfader-v0.json"),
    ("implementation-binding", "contracts/implementation-bindings/crossfader-audio-legacy-v0.json"),
    ("implementation-binding", "contracts/implementation-bindings/crossfader-control-legacy-v0.json"),
    ("implementation-binding", "contracts/implementation-bindings/crossfader-mixed-legacy-v0.json"),
    ("instrument", "contracts/instruments/blend-reference-v0-r2.json"),
    ("instrument", "contracts/instruments/blend-reference-v0.json"),
)

PREREQUISITE_RECORDS = (
    ("conformance-probe-evidence", "contracts/prerequisite/task009/probe-evidence-v0.json"),
    ("conformance-probe-input", "contracts/prerequisite/task009/probe-input-v0.json"),
    ("conformance-probe-procedure", "contracts/prerequisite/task009/procedure-v0.json"),
    ("conformance-probe-result", "contracts/prerequisite/task009/probe-result-v0.json"),
    ("prerequisite-environment", "contracts/prerequisite/task009/environment-v0.json"),
)

ACCEPTED_DIRECTORIES = (
    "contracts/backends",
    "contracts/binding-eligibility",
    "contracts/build-environments",
    "contracts/build-requests",
    "contracts/capabilities",
    "contracts/catalog-families",
    "contracts/component-contracts",
    "contracts/compute-targets",
    "contracts/device-profiles",
    "contracts/graphs",
    "contracts/implementation-bindings",
    "contracts/instruments",
)

ID_FIELDS = (
    "backend_id", "binding_eligibility_id", "build_environment_id",
    "build_request_id", "capability_vocabulary_id", "family_id",
    "component_contract_id", "compute_target_id", "device_profile_id",
    "graph_id", "implementation_id", "instrument_id",
    "conformance_probe_evidence_id", "conformance_probe_id", "procedure_id",
    "conformance_probe_result_id", "prerequisite_environment_id",
)


def schema_version(path: Path) -> str:
    identity = core.load_json(path)["$id"]
    return identity[: -len(".schema.json")]


def stable_id(record: dict[str, Any]) -> str:
    matches = [record[field] for field in ID_FIELDS if field in record]
    if len(matches) != 1:
        raise ValueError("record must expose exactly one stable ID")
    return matches[0]


def schema_member(relative: str) -> dict[str, Any]:
    path = ROOT / relative
    return {
        "schema_version": schema_version(path),
        "portable_path": relative,
        "byte_sha256": core.sha256_file(path),
    }


def record_member(kind: str, relative: str) -> dict[str, Any]:
    path = ROOT / relative
    record = core.load_json(path)
    return {
        "record_kind": kind,
        "stable_id": stable_id(record),
        "revision": record["revision"],
        "content_hash": record["content_hash"],
        "portable_path": relative,
        "byte_sha256": core.sha256_file(path),
    }


def render(record: dict[str, Any], schema: dict[str, Any]) -> bytes:
    record["content_hash"] = core.record_content_hash(record, schema)
    errors = core.schema_errors(record, schema, schema)
    if errors:
        raise ValueError(errors)
    canonical = core.canonicalize_with_schema(record, schema, schema)
    return core.canonical_json(canonical).encode("utf-8") + b"\n"


def generate() -> tuple[Path, Path]:
    schema = core.load_json(SCHEMA_PATH)
    output_root = ROOT / "contracts/record-sets"
    output_root.mkdir(parents=True, exist_ok=True)
    accepted_path = output_root / "task005-008-accepted-v0.json"
    prospective_path = output_root / "task009-prospective-v0.json"

    accepted = {
        "schema_version": "record-set-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "record_set_id": "schuss-record-set-000001",
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "purpose": "accepted-baseline",
        "parent_reference": {"status": "omitted"},
        "schema_members": [schema_member(path) for path in ACCEPTED_SCHEMAS],
        "record_members": [record_member(kind, path) for kind, path in ACCEPTED_RECORDS],
        "enforced_directories": list(ACCEPTED_DIRECTORIES),
    }
    accepted_path.write_bytes(render(accepted, schema))
    accepted = core.load_json(accepted_path)

    prospective = {
        "schema_version": "record-set-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "record_set_id": "schuss-record-set-000002",
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "purpose": "prospective-task",
        "parent_reference": {
            "status": "included",
            "record_set_id": accepted["record_set_id"],
            "revision": accepted["revision"],
            "content_hash": accepted["content_hash"],
        },
        "schema_members": [
            schema_member(path)
            for path in (*ACCEPTED_SCHEMAS, *PREREQUISITE_SCHEMAS)
        ],
        "record_members": [
            record_member(kind, path)
            for kind, path in (*ACCEPTED_RECORDS, *PREREQUISITE_RECORDS)
        ],
        "enforced_directories": [*ACCEPTED_DIRECTORIES, "contracts/prerequisite/task009"],
    }
    prospective_path.write_bytes(render(prospective, schema))
    return accepted_path, prospective_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    try:
        accepted, prospective = generate()
    except (OSError, ValueError, core.DuplicateJsonMemberError) as exc:
        print(f"record-set generation failed: {exc}", file=sys.stderr)
        return 1
    print(f"accepted={core.sha256_file(accepted)}")
    print(f"prospective={core.sha256_file(prospective)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
