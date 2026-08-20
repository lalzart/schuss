#!/usr/bin/env python3
"""Validate the exact Task 033 Phase 2 collection/provider successor."""

from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import sys
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "tools/contracts") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools/contracts"))

from packages.schuss_core import application_capabilities  # noqa: E402
from packages.schuss_core.control_plane import (  # noqa: E402
    canonical_result_bytes,
    dispatch_operation,
    load_repository_context,
)
from tools.contracts import generate_task033_phase2_records as generator  # noqa: E402
from tools.contracts import record_set_rules  # noqa: E402
from tools.contracts import validator_core as core  # noqa: E402


RECORD_SET = Path(
    "contracts/record-sets/task033-phase2-collection-provider-v1.json"
)
PARENT_RECORD_SET = Path("contracts/record-sets/task034-performance-control-v1.json")
HOST_IDS = {f"schuss-implementation-{number:06d}" for number in range(162, 169)}


def _reference(record: Mapping[str, Any], id_field: str) -> dict[str, Any]:
    return {
        id_field: record[id_field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def _profile(context: Any) -> dict[str, Any]:
    return {
        "schema_version": "collection-profile-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "use_context": "private-development",
        "installed_source_release_references": [
            _reference(record, "source_release_id")
            for record in context.records["source_releases"]
        ],
        "installed_provider_references": [
            _reference(record, "implementation_provider_id")
            for record in context.records["implementation_providers"]
        ],
        "collection_states": [
            {
                "collection_reference": _reference(
                    record, "object_collection_id"
                ),
                "enabled_for_discovery": True,
            }
            for record in context.records["object_collections"]
        ],
        "collection_order": [
            _reference(record, "object_collection_id")
            for record in context.records["object_collections"]
        ],
    }


def _freshness(repository_root: Path) -> None:
    files, manifest, _ = generator.generated()
    stale = [
        path
        for path, expected in sorted(files.items())
        if not (repository_root / path).is_file()
        or (repository_root / path).read_bytes() != expected
    ]
    manifest_path = repository_root / RECORD_SET
    if not manifest_path.is_file() or manifest_path.read_bytes() != manifest:
        stale.append(RECORD_SET.as_posix())
    if stale:
        raise ValueError("stale generated Phase 2 files: " + ", ".join(stale))


def _preserved_parent(parent: Any, child: Any) -> None:
    child_schemas = {
        (item["schema_version"], item["portable_path"]): item
        for item in child.manifest["schema_members"]
    }
    child_records = {
        (
            item["record_kind"],
            item["stable_id"],
            item["revision"],
            item["content_hash"],
            item["portable_path"],
        ): item
        for item in child.manifest["record_members"]
    }
    for item in parent.manifest["schema_members"]:
        key = (item["schema_version"], item["portable_path"])
        if child_schemas.get(key) != item:
            raise ValueError(f"parent schema member changed: {key}")
    for item in parent.manifest["record_members"]:
        key = (
            item["record_kind"],
            item["stable_id"],
            item["revision"],
            item["content_hash"],
            item["portable_path"],
        )
        if child_records.get(key) != item:
            raise ValueError(f"parent record member changed: {key}")


def validate(repository_root: Path = ROOT) -> dict[str, Any]:
    repository_root = repository_root.resolve()
    _freshness(repository_root)
    parent = record_set_rules.load_record_set(repository_root, PARENT_RECORD_SET)
    selected = record_set_rules.load_record_set(repository_root, RECORD_SET)
    expected_parent = {
        "status": "included",
        **parent.reference,
    }
    if selected.manifest["parent_reference"] != expected_parent:
        raise ValueError("Phase 2 parent reference is not exact")
    _preserved_parent(parent, selected)

    context = load_repository_context(
        repository_root=repository_root,
        record_set_path=RECORD_SET,
    )
    if context.collection_provider_summary["status"] != "valid":
        raise ValueError(core.canonical_json(context.collection_provider_summary))
    projection = context.catalog_projection
    if projection is None:
        raise ValueError("Phase 2 catalog projection is absent")
    implementations = {
        implementation["implementation_id"]: implementation
        for family in projection["families"]
        for implementation in family["implementations"]
    }
    if len(projection["families"]) != 107 or len(implementations) != 140:
        raise ValueError("Phase 2 catalog must contain exactly 107 families and 140 implementations")
    if not HOST_IDS <= set(implementations):
        raise ValueError("the seven existing host implementation companions are incomplete")

    parent_catalog = next(
        item
        for item in parent.records["catalog-corpus"]
        if item["catalog_id"] == "schuss-catalog-000001" and item["revision"] == 5
    )
    selected_catalog = context.records["catalog"][0]
    parent_additions = {
        item["implementation_id"]: item
        for item in parent_catalog["implementation_additions"]
    }
    selected_historical = {
        item["implementation_id"]: item
        for item in selected_catalog["implementation_additions"]
        if item["implementation_id"] not in HOST_IDS
    }
    if core.canonical_json(parent_additions) != core.canonical_json(selected_historical):
        raise ValueError("Task 030 catalog implementation members changed")

    collections = {
        item["object_collection_id"]: item
        for item in context.records["object_collections"]
    }
    expected_counts = {
        "schuss-object-collection-000001": 7,
        "schuss-object-collection-000002": 128,
        "schuss-object-collection-000003": 4,
        "schuss-object-collection-000004": 56,
    }
    actual_counts = {
        key: len(value["implementation_ids"])
        for key, value in collections.items()
    }
    if actual_counts != expected_counts:
        raise ValueError(f"collection membership counts changed: {actual_counts}")
    mutable_ids = {
        item["implementation_id"]
        for item in selected_catalog["mutable_instruments_review"]["implementation_tags"]
        if item["tag_id"] == "mutable-instruments-derived"
    }
    if set(collections["schuss-object-collection-000004"]["implementation_ids"]) != mutable_ids:
        raise ValueError("the Mutable-derived collection is not the exact 56-entry cohort")

    provider = context.records["implementation_providers"][0]
    if (
        len(provider["bindings"]) != 7
        or {item["catalog_implementation_locator"]["implementation_id"] for item in provider["bindings"]}
        != HOST_IDS
    ):
        raise ValueError("the native provider does not resolve exactly seven host bindings")
    for implementation_id in HOST_IDS:
        row = implementations[implementation_id]["target_availability"][0]
        if row["eligibility_status"] != "supported" or row["provider_status"] != "available":
            raise ValueError(f"host availability chain is incomplete: {implementation_id}")

    description = application_capabilities.build_application_description(
        record_set_reference=context.record_set_reference,
        schemas=context.schemas,
    )
    capability_schema = context.schemas["application_capability_description_v11"]
    capability_errors = core.schema_errors(
        description, capability_schema, capability_schema
    )
    if capability_errors or len(description["operations"]) != 47:
        raise ValueError("application capability v11 is invalid: " + "; ".join(capability_errors))

    profile = _profile(context)
    collection_request = {
        "schema_version": "schuss-operation-request-v18",
        "canonical_profile": "schuss-canonical-json-v1",
        "operation": "collections.inspect",
        "payload": {"profile": profile},
    }
    first = dispatch_operation(copy.deepcopy(collection_request), context)
    second = dispatch_operation(copy.deepcopy(collection_request), context)
    first_bytes = canonical_result_bytes(first, context)
    if first["status"] != "success" or first_bytes != canonical_result_bytes(second, context):
        raise ValueError("collections.inspect is not successful and deterministic")

    policy = context.records["availability_policies"][0]
    host_pair = policy["reported_pairs"][0]
    availability_hashes: list[dict[str, str]] = []
    for implementation_id in sorted(HOST_IDS):
        request = {
            "schema_version": "schuss-operation-request-v18",
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": "implementation.availability.inspect",
            "payload": {
                "profile": profile,
                "catalog_implementation_locator": {
                    "catalog_reference": copy.deepcopy(projection["catalog_reference"]),
                    "implementation_id": implementation_id,
                },
                "target_reference": copy.deepcopy(host_pair["target_reference"]),
                "backend_reference": copy.deepcopy(host_pair["backend_reference"]),
            },
        }
        result = dispatch_operation(request, context)
        result_bytes = canonical_result_bytes(result, context)
        if result["status"] != "success" or result["value"]["execution_availability"] != "available":
            raise ValueError(f"provider availability failed: {implementation_id}")
        availability_hashes.append(
            {
                "implementation_id": implementation_id,
                "result_sha256": hashlib.sha256(result_bytes).hexdigest(),
            }
        )

    return {
        "schema_version": "task033-phase2-validation-summary-v1",
        "status": "valid",
        "record_set_reference": copy.deepcopy(context.record_set_reference),
        "parent_record_set_reference": copy.deepcopy(parent.reference),
        "catalog_projection_sha256": hashlib.sha256(
            core.canonical_json(projection).encode("utf-8")
        ).hexdigest(),
        "collection_provider_validation_sha256": hashlib.sha256(
            core.canonical_json(context.collection_provider_summary).encode("utf-8")
        ).hexdigest(),
        "collections_result_sha256": hashlib.sha256(first_bytes).hexdigest(),
        "availability_results": availability_hashes,
        "catalog_family_count": len(projection["families"]),
        "catalog_implementation_count": len(implementations),
        "source_release_count": len(context.records["source_releases"]),
        "collection_counts": actual_counts,
        "provider_binding_count": len(provider["bindings"]),
        "reported_target_backend_pair_count": len(policy["reported_pairs"]),
        "parent_members_preserved": True,
        "native_registry_modified": False,
        "project_graph_backend_ui_or_hardware_mutation_performed": False,
    }


def main() -> int:
    print(core.canonical_json(validate(ROOT)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
