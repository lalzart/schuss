#!/usr/bin/env python3
"""Fail-closed Task 033 source, collection, and provider rules."""

from __future__ import annotations

import copy
import hashlib
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import record_set_rules
import validator_core as core


SCHEMA_VERSIONS = {
    "source_releases": "source-release-v0",
    "object_collections": "object-collection-v0",
    "implementation_providers": "implementation-provider-v0",
    "availability_policies": "implementation-availability-policy-v0",
}

ID_FIELDS = {
    "source_releases": "source_release_id",
    "object_collections": "object_collection_id",
    "implementation_providers": "implementation_provider_id",
    "availability_policies": "implementation_availability_policy_id",
}


def _diagnostic(
    diagnostics: list[core.Diagnostic],
    code: str,
    subject: str,
    location: str,
    message: str,
    *,
    severity: str = "error",
) -> None:
    core.add_diagnostic(
        diagnostics, code, subject, location, message, severity=severity
    )


def _subject(record: Mapping[str, Any]) -> str:
    for field in ID_FIELDS.values():
        if field in record:
            return f"{record[field]}@{record.get('revision', '?')}"
    return core.record_subject(dict(record))


def _key(value: Mapping[str, Any], id_field: str) -> tuple[str, int, str]:
    return (
        str(value[id_field]),
        int(value["revision"]),
        str(value["content_hash"]),
    )


def _id_revision(value: Mapping[str, Any], id_field: str) -> tuple[str, int]:
    return str(value[id_field]), int(value["revision"])


def _registry(
    values: Iterable[dict[str, Any]], id_field: str
) -> dict[tuple[str, int, str], dict[str, Any]]:
    return {_key(value, id_field): value for value in values}


def _resolve_reference(
    reference: Mapping[str, Any],
    values: Sequence[dict[str, Any]],
    id_field: str,
    *,
    diagnostics: list[core.Diagnostic],
    missing_code: str,
    stale_code: str,
    subject: str,
    location: str,
    noun: str,
) -> dict[str, Any] | None:
    identity = _id_revision(reference, id_field)
    candidates = [
        value for value in values if _id_revision(value, id_field) == identity
    ]
    if not candidates:
        _diagnostic(
            diagnostics,
            missing_code,
            subject,
            location,
            f"the exact {noun} stable ID and revision are absent",
        )
        return None
    exact = [value for value in candidates if _key(value, id_field) == _key(reference, id_field)]
    if len(exact) != 1:
        _diagnostic(
            diagnostics,
            stale_code,
            subject,
            location,
            f"the exact {noun} content hash is stale or ambiguous",
        )
        return None
    return exact[0]


def _catalog_implementations(
    projection: Mapping[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    if projection is None:
        return {}
    return {
        implementation["implementation_id"]: implementation
        for family in projection.get("families", ())
        for implementation in family.get("implementations", ())
    }


def _portable_path(repository_root: Path, portable_path: str) -> Path | None:
    candidate = repository_root / portable_path
    try:
        candidate.resolve().relative_to(repository_root.resolve())
    except ValueError:
        return None
    return candidate


def _generic_record_registry(
    all_records: Mapping[str, Sequence[dict[str, Any]]],
) -> dict[tuple[str, int, str], dict[str, Any]]:
    result: dict[tuple[str, int, str], dict[str, Any]] = {}
    for values in all_records.values():
        for record in values:
            fields = [field for field in record_set_rules.ID_FIELDS if field in record]
            if len(fields) == 1 and "revision" in record and "content_hash" in record:
                field = fields[0]
                result[(str(record[field]), int(record["revision"]), str(record["content_hash"]))] = record
    return result


def _validate_source_anchor(
    release: dict[str, Any],
    anchor: dict[str, Any],
    index: int,
    repository_root: Path | None,
    generic_records: Mapping[tuple[str, int, str], dict[str, Any]],
    diagnostics: list[core.Diagnostic],
) -> None:
    if repository_root is None:
        return
    subject = _subject(release)
    location = f"$.evidence_anchors[{index}]"
    path = _portable_path(repository_root, anchor["portable_path"])
    if path is None or not path.is_file():
        _diagnostic(
            diagnostics,
            "SOURCE_RELEASE_EVIDENCE_MISSING",
            subject,
            location + ".portable_path",
            "the portable evidence file is absent or escapes the repository",
        )
        return
    actual_hash = core.sha256_file(path)
    if actual_hash != anchor["byte_sha256"]:
        _diagnostic(
            diagnostics,
            "SOURCE_RELEASE_EVIDENCE_STALE",
            subject,
            location + ".byte_sha256",
            f"the evidence byte hash is stale; expected {actual_hash}",
        )
    if anchor["anchor_kind"] == "semantic-record":
        reference = anchor["record_reference"]
        key = (
            reference["stable_id"],
            reference["revision"],
            reference["content_hash"],
        )
        if key not in generic_records:
            _diagnostic(
                diagnostics,
                "SOURCE_RELEASE_SEMANTIC_REFERENCE_STALE",
                subject,
                location + ".record_reference",
                "the exact semantic evidence record is absent",
            )
    elif anchor["anchor_kind"] == "source-lock-entry":
        try:
            lock = core.load_json(path)
        except ValueError as error:
            _diagnostic(
                diagnostics,
                "SOURCE_RELEASE_LOCK_INVALID",
                subject,
                location + ".portable_path",
                str(error),
            )
            return
        entries = [
            item
            for item in lock.get("sources", ())
            if item.get("id") == release["portable_source_id"]
        ]
        actual_entry_hashes = {
            hashlib.sha256(core.canonical_json(item).encode("utf-8")).hexdigest()
            for item in entries
        }
        if len(entries) != 1 or anchor["entry_sha256"] not in actual_entry_hashes:
            _diagnostic(
                diagnostics,
                "SOURCE_RELEASE_LOCK_ENTRY_STALE",
                subject,
                location + ".entry_sha256",
                "the pinned source-lock entry is absent, ambiguous, or stale",
            )


def _pair_key(
    target_reference: Mapping[str, Any], backend_reference: Mapping[str, Any]
) -> tuple[str, int, str, str, int, str]:
    return (
        str(target_reference["compute_target_id"]),
        int(target_reference["revision"]),
        str(target_reference["content_hash"]),
        str(backend_reference["backend_id"]),
        int(backend_reference["revision"]),
        str(backend_reference["content_hash"]),
    )


def _structural(
    records: Mapping[str, Sequence[dict[str, Any]]],
    schemas: Mapping[str, dict[str, Any]],
    diagnostics: list[core.Diagnostic],
) -> dict[str, list[dict[str, Any]]]:
    valid = {group: [] for group in SCHEMA_VERSIONS}
    for group, version in SCHEMA_VERSIONS.items():
        schema = schemas.get(version)
        if schema is None:
            if records.get(group):
                _diagnostic(
                    diagnostics,
                    "COLLECTION_PROVIDER_SCHEMA_MISSING",
                    version,
                    "$",
                    "the exact semantic schema is absent",
                )
            continue
        valid[group] = core.validate_structural_records(
            list(records.get(group, ())),
            schema,
            f"{version}.schema.json",
            version,
            ID_FIELDS[group],
            diagnostics,
            subject_fn=_subject,
        )
    return valid


def _validate_policy(
    policies: list[dict[str, Any]],
    catalog_reference: Mapping[str, Any] | None,
    targets: Sequence[dict[str, Any]],
    backends: Sequence[dict[str, Any]],
    diagnostics: list[core.Diagnostic],
) -> tuple[dict[str, Any] | None, set[tuple[str, int, str, str, int, str]]]:
    if len(policies) != 1:
        _diagnostic(
            diagnostics,
            "AVAILABILITY_POLICY_NOT_EXACT",
            "implementation-availability-policy",
            "$",
            "the Task 033 closure requires exactly one availability policy",
        )
        return None, set()
    policy = policies[0]
    subject = _subject(policy)
    if catalog_reference is None or policy["catalog_reference"] != catalog_reference:
        _diagnostic(
            diagnostics,
            "AVAILABILITY_POLICY_CATALOG_STALE",
            subject,
            "$.catalog_reference",
            "the policy must name the exact selected catalog",
        )
    pair_keys: set[tuple[str, int, str, str, int, str]] = set()
    pair_ids: set[str] = set()
    for index, pair in enumerate(policy["reported_pairs"]):
        key = _pair_key(pair["target_reference"], pair["backend_reference"])
        if key in pair_keys or pair["pair_id"] in pair_ids:
            _diagnostic(
                diagnostics,
                "AVAILABILITY_POLICY_PAIR_DUPLICATE",
                subject,
                f"$.reported_pairs[{index}]",
                "target/backend pairs and local pair IDs must be unique",
            )
        pair_keys.add(key)
        pair_ids.add(pair["pair_id"])
        _resolve_reference(
            pair["target_reference"],
            targets,
            "compute_target_id",
            diagnostics=diagnostics,
            missing_code="AVAILABILITY_TARGET_MISSING",
            stale_code="AVAILABILITY_TARGET_STALE",
            subject=subject,
            location=f"$.reported_pairs[{index}].target_reference",
            noun="compute target",
        )
        _resolve_reference(
            pair["backend_reference"],
            backends,
            "backend_id",
            diagnostics=diagnostics,
            missing_code="AVAILABILITY_BACKEND_MISSING",
            stale_code="AVAILABILITY_BACKEND_STALE",
            subject=subject,
            location=f"$.reported_pairs[{index}].backend_reference",
            noun="backend",
        )
    return policy, pair_keys


def _validate_collection(
    collection: dict[str, Any],
    source_releases: Sequence[dict[str, Any]],
    catalog_reference: Mapping[str, Any] | None,
    implementations: Mapping[str, dict[str, Any]],
    diagnostics: list[core.Diagnostic],
) -> None:
    subject = _subject(collection)
    if catalog_reference is None or collection["catalog_reference"] != catalog_reference:
        _diagnostic(
            diagnostics,
            "COLLECTION_CATALOG_REFERENCE_STALE",
            subject,
            "$.catalog_reference",
            "collection membership must use the exact selected catalog reference",
        )
    declared_sources: set[str] = set()
    for index, reference in enumerate(collection["source_release_references"]):
        resolved_source = _resolve_reference(
            reference,
            source_releases,
            "source_release_id",
            diagnostics=diagnostics,
            missing_code="COLLECTION_SOURCE_RELEASE_MISSING",
            stale_code="COLLECTION_SOURCE_REFERENCE_STALE",
            subject=subject,
            location=f"$.source_release_references[{index}]",
            noun="source release",
        )
        if resolved_source is not None:
            declared_sources.add(resolved_source["portable_source_id"])
    for index, implementation_id in enumerate(collection["implementation_ids"]):
        implementation = implementations.get(implementation_id)
        if implementation is None:
            _diagnostic(
                diagnostics,
                "COLLECTION_IMPLEMENTATION_UNRESOLVED",
                subject,
                f"$.implementation_ids[{index}]",
                "the catalog implementation locator does not resolve exactly once",
            )
        elif not declared_sources.intersection(
            implementation["provenance_sources"]
        ):
            _diagnostic(
                diagnostics,
                "COLLECTION_SOURCE_MEMBERSHIP_MISMATCH",
                subject,
                f"$.implementation_ids[{index}]",
                "the implementation provenance does not name any declared collection source release",
            )


def _validate_provider(
    provider: dict[str, Any],
    *,
    source_releases: Sequence[dict[str, Any]],
    implementations: Mapping[str, dict[str, Any]],
    catalog_reference: Mapping[str, Any] | None,
    contracts: Sequence[dict[str, Any]],
    bindings: Sequence[dict[str, Any]],
    eligibilities: Sequence[dict[str, Any]],
    targets: Sequence[dict[str, Any]],
    backends: Sequence[dict[str, Any]],
    policy_pairs: set[tuple[str, int, str, str, int, str]],
    factory_claims: dict[str, tuple[str, str]],
    binding_claims: dict[tuple[str, tuple[str, int, str, str, int, str]], tuple[str, str]],
    diagnostics: list[core.Diagnostic],
) -> None:
    subject = _subject(provider)
    _resolve_reference(
        provider["source_release_reference"],
        source_releases,
        "source_release_id",
        diagnostics=diagnostics,
        missing_code="PROVIDER_SOURCE_RELEASE_MISSING",
        stale_code="PROVIDER_SOURCE_REFERENCE_STALE",
        subject=subject,
        location="$.source_release_reference",
        noun="provider source release",
    )
    for index, reference in enumerate(provider["required_source_release_references"]):
        _resolve_reference(
            reference,
            source_releases,
            "source_release_id",
            diagnostics=diagnostics,
            missing_code="PROVIDER_SOURCE_RELEASE_MISSING",
            stale_code="PROVIDER_SOURCE_REFERENCE_STALE",
            subject=subject,
            location=f"$.required_source_release_references[{index}]",
            noun="required source release",
        )
    if provider["source_release_reference"] not in provider[
        "required_source_release_references"
    ]:
        _diagnostic(
            diagnostics,
            "PROVIDER_SOURCE_REQUIREMENT_MISMATCH",
            subject,
            "$.required_source_release_references",
            "the provider's own exact source release must be an explicit requirement",
        )
    if provider["license_boundary"]["private_development_status"] != "reviewed":
        _diagnostic(
            diagnostics,
            "PROVIDER_LICENSE_UNREVIEWED",
            subject,
            "$.license_boundary.private_development_status",
            "a provider cannot be locally available until private-development licensing is reviewed",
            severity="warning",
        )
    provider_pairs = {
        _pair_key(pair["target_reference"], pair["backend_reference"])
        for pair in provider["target_backend_pairs"]
    }
    for index, pair in enumerate(provider["target_backend_pairs"]):
        pair_key = _pair_key(pair["target_reference"], pair["backend_reference"])
        if pair_key not in policy_pairs:
            _diagnostic(
                diagnostics,
                "PROVIDER_TARGET_PAIR_UNDECLARED",
                subject,
                f"$.target_backend_pairs[{index}]",
                "the provider pair is absent from the exact availability policy",
            )
        _resolve_reference(
            pair["target_reference"],
            targets,
            "compute_target_id",
            diagnostics=diagnostics,
            missing_code="PROVIDER_TARGET_MISSING",
            stale_code="PROVIDER_TARGET_STALE",
            subject=subject,
            location=f"$.target_backend_pairs[{index}].target_reference",
            noun="provider compute target",
        )
        _resolve_reference(
            pair["backend_reference"],
            backends,
            "backend_id",
            diagnostics=diagnostics,
            missing_code="PROVIDER_BACKEND_MISSING",
            stale_code="PROVIDER_BACKEND_STALE",
            subject=subject,
            location=f"$.target_backend_pairs[{index}].backend_reference",
            noun="provider backend",
        )

    provider_binding_ids: set[str] = set()
    for index, claim in enumerate(provider["bindings"]):
        location = f"$.bindings[{index}]"
        if claim["provider_binding_id"] in provider_binding_ids:
            _diagnostic(
                diagnostics,
                "PROVIDER_BINDING_ID_DUPLICATE",
                subject,
                location + ".provider_binding_id",
                "provider-local binding identities must be unique",
            )
        provider_binding_ids.add(claim["provider_binding_id"])
        locator = claim["catalog_implementation_locator"]
        if catalog_reference is None or locator["catalog_reference"] != catalog_reference:
            _diagnostic(
                diagnostics,
                "PROVIDER_CATALOG_REFERENCE_STALE",
                subject,
                location + ".catalog_implementation_locator.catalog_reference",
                "the provider locator must use the exact selected catalog",
            )
        implementation_id = locator["implementation_id"]
        if implementation_id not in implementations:
            _diagnostic(
                diagnostics,
                "PROVIDER_CATALOG_IMPLEMENTATION_MISSING",
                subject,
                location + ".catalog_implementation_locator.implementation_id",
                "the exact catalog implementation is absent",
            )
        pair_key = _pair_key(claim["target_reference"], claim["backend_reference"])
        if pair_key not in provider_pairs:
            _diagnostic(
                diagnostics,
                "PROVIDER_BINDING_PAIR_UNDECLARED",
                subject,
                location,
                "the provider binding pair is absent from the provider declaration",
            )
        factory_id = claim["runtime_factory_id"]
        prior_factory = factory_claims.get(factory_id)
        if prior_factory is not None:
            _diagnostic(
                diagnostics,
                "PROVIDER_FACTORY_DUPLICATE",
                subject,
                location + ".runtime_factory_id",
                f"runtime factory identity is already claimed by {prior_factory[0]} at {prior_factory[1]}",
            )
        else:
            factory_claims[factory_id] = (subject, location)
        binding_key = (implementation_id, pair_key)
        prior_binding = binding_claims.get(binding_key)
        if prior_binding is not None:
            _diagnostic(
                diagnostics,
                "PROVIDER_BINDING_AMBIGUOUS",
                subject,
                location,
                f"the exact catalog implementation and target/backend pair are already claimed by {prior_binding[0]} at {prior_binding[1]}",
            )
        else:
            binding_claims[binding_key] = (subject, location)

        contract = _resolve_reference(
            claim["component_contract_reference"],
            contracts,
            "component_contract_id",
            diagnostics=diagnostics,
            missing_code="PROVIDER_COMPONENT_CONTRACT_MISSING",
            stale_code="PROVIDER_COMPONENT_CONTRACT_STALE",
            subject=subject,
            location=location + ".component_contract_reference",
            noun="component contract",
        )
        binding = _resolve_reference(
            claim["implementation_binding_reference"],
            bindings,
            "implementation_id",
            diagnostics=diagnostics,
            missing_code="PROVIDER_IMPLEMENTATION_BINDING_MISSING",
            stale_code="PROVIDER_IMPLEMENTATION_BINDING_STALE",
            subject=subject,
            location=location + ".implementation_binding_reference",
            noun="implementation binding",
        )
        eligibility = _resolve_reference(
            claim["eligibility_reference"],
            eligibilities,
            "binding_eligibility_id",
            diagnostics=diagnostics,
            missing_code="PROVIDER_ELIGIBILITY_MISSING",
            stale_code="PROVIDER_ELIGIBILITY_STALE",
            subject=subject,
            location=location + ".eligibility_reference",
            noun="binding eligibility",
        )
        if claim["implementation_binding_reference"]["implementation_id"] != implementation_id:
            _diagnostic(
                diagnostics,
                "PROVIDER_BINDING_IDENTITY_MISMATCH",
                subject,
                location,
                "catalog and implementation-binding identities must agree",
            )
        if binding is not None and binding["contract_reference"] != claim["component_contract_reference"]:
            _diagnostic(
                diagnostics,
                "PROVIDER_COMPONENT_CONTRACT_MISMATCH",
                subject,
                location + ".component_contract_reference",
                "the provider contract does not match the exact implementation binding",
            )
        if contract is not None and binding is not None and binding["contract_reference"] != {
            "component_contract_id": contract["component_contract_id"],
            "revision": contract["revision"],
            "content_hash": contract["content_hash"],
        }:
            _diagnostic(
                diagnostics,
                "PROVIDER_COMPONENT_CONTRACT_MISMATCH",
                subject,
                location + ".component_contract_reference",
                "the resolved contract and binding do not agree",
            )
        if eligibility is not None:
            if eligibility["binding_reference"] != claim["implementation_binding_reference"]:
                _diagnostic(
                    diagnostics,
                    "PROVIDER_ELIGIBILITY_BINDING_MISMATCH",
                    subject,
                    location + ".eligibility_reference",
                    "eligibility does not name the provider's exact binding",
                )
            allowed = eligibility["allowed_pair"]
            if (
                allowed["target_reference"] != claim["target_reference"]
                or allowed["backend_reference"] != claim["backend_reference"]
                or allowed["state"]["status"] != "supported"
            ):
                _diagnostic(
                    diagnostics,
                    "PROVIDER_ELIGIBILITY_PAIR_MISMATCH",
                    subject,
                    location,
                    "provider availability requires the exact supported eligibility pair",
                )


def validate_values(
    records: Mapping[str, Sequence[dict[str, Any]]],
    schemas: Mapping[str, dict[str, Any]],
    catalog_projection: Mapping[str, Any] | None,
    *,
    repository_root: Path | None = None,
    all_records: Mapping[str, Sequence[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Validate one exact Phase 2 source/collection/provider closure."""

    if not any(records.get(group) for group in SCHEMA_VERSIONS):
        return {
            "schema_version": "collection-provider-validation-summary-v0",
            "status": "not-present",
            "record_counts": {
                "source_releases": 0,
                "object_collections": 0,
                "implementation_providers": 0,
                "availability_policies": 0,
            },
            "reference_resolution": {},
            "boundary_assertions": {},
            "diagnostics": [],
        }

    diagnostics: list[core.Diagnostic] = []
    valid = _structural(records, schemas, diagnostics)
    projection_reference = (
        copy.deepcopy(catalog_projection["catalog_reference"])
        if catalog_projection is not None
        else None
    )
    implementations = _catalog_implementations(catalog_projection)
    source_releases = valid["source_releases"]
    generic_records = _generic_record_registry(all_records or {})
    for release in source_releases:
        for index, anchor in enumerate(release["evidence_anchors"]):
            _validate_source_anchor(
                release,
                anchor,
                index,
                repository_root,
                generic_records,
                diagnostics,
            )

    for catalog in records.get("catalog", ()):
        for index, implementation in enumerate(catalog.get("implementation_additions", ())):
            authority = implementation.get("source_authority", {})
            reference = authority.get("source_release_reference")
            if reference is None:
                continue
            _resolve_reference(
                reference,
                source_releases,
                "source_release_id",
                diagnostics=diagnostics,
                missing_code="CATALOG_SOURCE_RELEASE_MISSING",
                stale_code="CATALOG_SOURCE_REFERENCE_STALE",
                subject=implementation["implementation_id"],
                location=f"$.implementation_additions[{index}].source_authority.source_release_reference",
                noun="catalog source release",
            )

    policy, policy_pairs = _validate_policy(
        valid["availability_policies"],
        projection_reference,
        list(records.get("target", ())),
        list(records.get("backend", ())),
        diagnostics,
    )
    for collection in valid["object_collections"]:
        _validate_collection(
            collection,
            source_releases,
            projection_reference,
            implementations,
            diagnostics,
        )
    factory_claims: dict[str, tuple[str, str]] = {}
    binding_claims: dict[
        tuple[str, tuple[str, int, str, str, int, str]], tuple[str, str]
    ] = {}
    for provider in valid["implementation_providers"]:
        _validate_provider(
            provider,
            source_releases=source_releases,
            implementations=implementations,
            catalog_reference=projection_reference,
            contracts=list(records.get("contracts", ())),
            bindings=list(records.get("bindings", ())),
            eligibilities=list(records.get("eligibility", ())),
            targets=list(records.get("target", ())),
            backends=list(records.get("backend", ())),
            policy_pairs=policy_pairs,
            factory_claims=factory_claims,
            binding_claims=binding_claims,
            diagnostics=diagnostics,
        )

    diagnostics = sorted(set(diagnostics), key=core.diagnostic_sort_key)
    status = "invalid" if any(item.severity == "error" for item in diagnostics) else "valid"
    return {
        "schema_version": "collection-provider-validation-summary-v0",
        "status": status,
        "record_counts": {
            group: len(records.get(group, ())) for group in SCHEMA_VERSIONS
        },
        "reference_resolution": {
            "catalog_implementation_count": len(implementations),
            "collection_memberships_resolved": sum(
                implementation_id in implementations
                for collection in valid["object_collections"]
                for implementation_id in collection["implementation_ids"]
            ),
            "provider_bindings_resolved": len(binding_claims),
            "reported_target_backend_pairs": len(policy_pairs) if policy is not None else 0,
        },
        "boundary_assertions": {
            "collections_are_function_neutral": all(
                collection["function_neutral"]
                and not collection["target_promise"]
                and not collection["project_identity_authority"]
                for collection in valid["object_collections"]
            ),
            "provider_priority_owned_by_eligibility": all(
                provider["selection_priority_owner"] == "binding-eligibility"
                for provider in valid["implementation_providers"]
            ),
            "providers_are_static": all(
                provider["provider_kind"] == "statically-linked"
                and not provider["dynamic_loading"]
                for provider in valid["implementation_providers"]
            ),
            "local_profile_is_not_semantic_record": True,
        },
        "diagnostics": [item.as_dict() for item in diagnostics],
    }


def validate_profile(
    profile: Mapping[str, Any],
    *,
    schema: Mapping[str, Any],
    source_releases: Sequence[dict[str, Any]],
    providers: Sequence[dict[str, Any]],
    collections: Sequence[dict[str, Any]],
) -> list[dict[str, str]]:
    """Validate machine-local exact references without granting semantic authority."""

    diagnostics: list[core.Diagnostic] = []
    try:
        core.assert_portable_json_value(profile)
    except ValueError as error:
        _diagnostic(
            diagnostics,
            "COLLECTION_PROFILE_INVALID",
            "collection-profile",
            "$",
            str(error),
        )
    for error in core.schema_errors(profile, dict(schema), dict(schema)):
        _diagnostic(
            diagnostics,
            "COLLECTION_PROFILE_INVALID",
            "collection-profile",
            "$",
            error,
        )
    if diagnostics:
        return [item.as_dict() for item in sorted(set(diagnostics), key=core.diagnostic_sort_key)]

    reference_sets = (
        (
            "installed_source_release_references",
            source_releases,
            "source_release_id",
            "PROFILE_SOURCE_RELEASE_MISSING",
            "PROFILE_SOURCE_REFERENCE_STALE",
            "source release",
        ),
        (
            "installed_provider_references",
            providers,
            "implementation_provider_id",
            "PROFILE_PROVIDER_MISSING",
            "PROFILE_PROVIDER_REFERENCE_STALE",
            "implementation provider",
        ),
        (
            "collection_order",
            collections,
            "object_collection_id",
            "PROFILE_COLLECTION_MISSING",
            "PROFILE_COLLECTION_REFERENCE_STALE",
            "object collection",
        ),
    )
    for field, values, id_field, missing, stale, noun in reference_sets:
        seen: set[tuple[str, int]] = set()
        for index, reference in enumerate(profile[field]):
            identity = _id_revision(reference, id_field)
            if identity in seen:
                _diagnostic(
                    diagnostics,
                    "COLLECTION_PROFILE_REFERENCE_DUPLICATE",
                    "collection-profile",
                    f"$.{field}[{index}]",
                    f"the {noun} stable ID and revision occur more than once",
                )
            seen.add(identity)
            _resolve_reference(
                reference,
                values,
                id_field,
                diagnostics=diagnostics,
                missing_code=missing,
                stale_code=stale,
                subject="collection-profile",
                location=f"$.{field}[{index}]",
                noun=noun,
            )
    seen_states: set[tuple[str, int]] = set()
    for index, state in enumerate(profile["collection_states"]):
        reference = state["collection_reference"]
        identity = _id_revision(reference, "object_collection_id")
        if identity in seen_states:
            _diagnostic(
                diagnostics,
                "COLLECTION_PROFILE_STATE_DUPLICATE",
                "collection-profile",
                f"$.collection_states[{index}]",
                "one collection may have only one discovery state",
            )
        seen_states.add(identity)
        _resolve_reference(
            reference,
            collections,
            "object_collection_id",
            diagnostics=diagnostics,
            missing_code="PROFILE_COLLECTION_MISSING",
            stale_code="PROFILE_COLLECTION_REFERENCE_STALE",
            subject="collection-profile",
            location=f"$.collection_states[{index}].collection_reference",
            noun="object collection",
        )
    return [
        item.as_dict() for item in sorted(set(diagnostics), key=core.diagnostic_sort_key)
    ]
