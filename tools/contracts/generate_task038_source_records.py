#!/usr/bin/env python3
"""Generate Task 038 Mutable dependency source authorities and successor set."""

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


PARENT_PATH = Path("contracts/record-sets/task033-phase2-collection-provider-v1.json")
OUTPUT_PATH = Path("contracts/record-sets/task038-instrument-source-dependencies-v1.json")
TASK_DIR = Path("contracts/task038")
AUDIT_PATH = Path("catalog/reviews/task038-mutable-source-dependencies-v1/manifest.json")
SOURCE_RELEASE_SCHEMA_PATH = Path("schemas/source-release-v0.schema.json")
RECORD_SET_ID = "schuss-record-set-000032"
EXPECTED_PARENT = {
    "record_set_id": "schuss-record-set-000031",
    "revision": 1,
    "content_hash": "sha256:09ef78ec79d72736add893045973070fa0b2c43e06fc124d05392213d73fc789",
}
SOURCE_SPECS = (
    {
        "number": 8,
        "portable_source_id": "mutable-eurorack",
        "display_name": "Mutable Instruments Eurorack Braids dependency",
        "repository_url": "https://github.com/pichenettes/eurorack.git",
        "commit": "08460a69a7e1f7a81c5a2abcc7189c9a6b7208d4",
        "package_root": "packages/dsp_sources/mutable_eurorack_braids_v1",
        "scope": "selected Braids source closure",
    },
    {
        "number": 9,
        "portable_source_id": "mutable-stmlib",
        "display_name": "Mutable Instruments stmlib dependency",
        "repository_url": "https://github.com/pichenettes/stmlib.git",
        "commit": "e3bd7c9cc00e4364166f9905c0509b6ffd0535ec",
        "package_root": "packages/dsp_sources/mutable_stmlib_v1",
        "scope": "selected stmlib source closure",
    },
)


def _canonical_bytes(value: object) -> bytes:
    return (core.canonical_json(value) + "\n").encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _hash_record(record: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(record)
    result["content_hash"] = "sha256:" + "0" * 64
    result["content_hash"] = core.record_content_hash(result, schema)
    errors = core.schema_errors(result, schema, schema)
    if errors:
        raise ValueError("; ".join(errors))
    return result


def _source_files(package_root: Path) -> list[dict[str, str]]:
    immutable = package_root / "upstream"
    files = []
    for path in sorted(item for item in immutable.rglob("*") if item.is_file()):
        files.append(
            {
                "path": path.relative_to(immutable).as_posix(),
                "sha256": core.sha256_file(path),
            }
        )
    if not files:
        raise ValueError(f"source audit closure is empty: {package_root}")
    return files


def generated() -> tuple[dict[str, bytes], bytes, dict[str, Any]]:
    source_schema = core.load_json(ROOT / SOURCE_RELEASE_SCHEMA_PATH)
    parent = record_set_rules.load_record_set(ROOT, PARENT_PATH)
    if parent.reference != EXPECTED_PARENT:
        raise ValueError("Task 038 parent record set changed")

    audit_sources = []
    for spec in SOURCE_SPECS:
        files = _source_files(ROOT / spec["package_root"])
        audit_sources.append(
            {
                "commit": spec["commit"],
                "files": files,
                "license_observation": {
                    "declared_expression": "MIT",
                    "evidence": "selected source headers and retained notice bytes",
                    "scope": spec["scope"],
                    "status": "scope-reviewed",
                },
                "portable_source_id": spec["portable_source_id"],
                "repository_url": spec["repository_url"],
            }
        )
    audit = {
        "claims": {
            "catalog_membership": False,
            "distribution_approved": False,
            "provider_identity": False,
            "runtime_support": False,
        },
        "schema_version": "task038-mutable-source-dependencies-audit-v1",
        "sources": audit_sources,
    }
    audit_bytes = _canonical_bytes(audit)

    records: list[dict[str, Any]] = []
    for spec in SOURCE_SPECS:
        records.append(
            _hash_record(
                {
                    "schema_version": "source-release-v0",
                    "canonical_profile": "schuss-canonical-json-v1",
                    "source_release_id": f"schuss-source-release-{spec['number']:06d}",
                    "revision": 1,
                    "content_hash": "sha256:" + "0" * 64,
                    "display_name": spec["display_name"],
                    "portable_source_id": spec["portable_source_id"],
                    "release_scope": "audited-candidate-source",
                    "release_identity": {
                        "identity_kind": "git-commit",
                        "repository_url": spec["repository_url"],
                        "commit": spec["commit"],
                    },
                    "evidence_anchors": [
                        {
                            "anchor_kind": "portable-file",
                            "portable_path": AUDIT_PATH.as_posix(),
                            "byte_sha256": _sha256_bytes(audit_bytes),
                            "scope": spec["scope"],
                        }
                    ],
                    "declared_license_evidence": [
                        {
                            "scope": spec["scope"],
                            "status": "scope-reviewed",
                            "declared_expression": "MIT",
                            "limitations": [
                                "Review applies only to the selected physical closure.",
                                "Distribution packaging and notice placement require a separate review.",
                            ],
                        }
                    ],
                    "distribution_review_status": "required-before-distribution",
                    "importer_boundary": "audited-candidate-only",
                    "support_claim": "source-identity-and-provenance-only",
                },
                source_schema,
            )
        )

    files: dict[str, bytes] = {AUDIT_PATH.as_posix(): audit_bytes}
    for index, record in enumerate(records, start=1):
        files[(TASK_DIR / f"source-release-{index:02d}.json").as_posix()] = _canonical_bytes(record)

    record_members = copy.deepcopy(parent.manifest["record_members"])
    for index, record in enumerate(records, start=1):
        path = (TASK_DIR / f"source-release-{index:02d}.json").as_posix()
        data = files[path]
        record_members.append(
            {
                "record_kind": "source-release",
                "stable_id": record["source_release_id"],
                "revision": record["revision"],
                "content_hash": record["content_hash"],
                "portable_path": path,
                "byte_sha256": _sha256_bytes(data),
            }
        )

    manifest_schema = core.load_json(ROOT / record_set_rules.RECORD_SET_SCHEMA)
    manifest = {
        "schema_version": "record-set-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "record_set_id": RECORD_SET_ID,
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "purpose": "prospective-task",
        "parent_reference": {"status": "included", **parent.reference},
        "schema_members": copy.deepcopy(parent.manifest["schema_members"]),
        "record_members": sorted(
            record_members,
            key=lambda item: (
                item["record_kind"], item["stable_id"], item["revision"], item["content_hash"]
            ),
        ),
        "enforced_directories": sorted(
            set(parent.manifest["enforced_directories"]) | {TASK_DIR.as_posix()}
        ),
    }
    errors = core.schema_errors(manifest, manifest_schema, manifest_schema)
    if errors:
        raise ValueError("; ".join(errors))
    manifest["content_hash"] = core.record_content_hash(manifest, manifest_schema)
    summary = {
        "schema_version": "task038-source-generation-summary-v1",
        "status": "valid",
        "parent_record_set_reference": parent.reference,
        "record_set_reference": {
            key: manifest[key] for key in ("record_set_id", "revision", "content_hash")
        },
        "added_source_release_ids": [record["source_release_id"] for record in records],
        "catalog_collection_provider_mutation": False,
    }
    return files, _canonical_bytes(manifest), summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files, manifest, summary = generated()
    stale: list[str] = []
    for relative, data in sorted(files.items()):
        destination = ROOT / relative
        if args.check:
            if not destination.is_file() or destination.read_bytes() != data:
                stale.append(relative)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
    output = ROOT / OUTPUT_PATH
    if args.check:
        if not output.is_file() or output.read_bytes() != manifest:
            stale.append(OUTPUT_PATH.as_posix())
        if stale:
            raise SystemExit("stale Task 038 source records: " + ", ".join(stale))
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(manifest)
    print(core.canonical_json(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
