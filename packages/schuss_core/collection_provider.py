"""Read-only Task 033 collection and implementation-availability operations."""

from __future__ import annotations

import copy
import hashlib
from collections import Counter
from typing import Any, Iterable, Mapping

import collection_provider_rules as rules

from .control_plane import OperationContext, canonical_result_bytes, core


def _diagnostic(
    code: str,
    subject: str,
    location: str,
    message: str,
    *,
    severity: str = "error",
) -> dict[str, str]:
    return {
        "code": code,
        "severity": severity,
        "subject": subject,
        "location": location,
        "message": message,
    }


def _result(
    operation: str,
    status: str,
    value: dict[str, Any] | None,
    diagnostics: Iterable[dict[str, str]] = (),
) -> dict[str, Any]:
    return {
        "schema_version": "schuss-operation-result-v18",
        "canonical_profile": "schuss-canonical-json-v1",
        "operation": operation,
        "status": status,
        "value": copy.deepcopy(value),
        "diagnostics": sorted(
            (copy.deepcopy(item) for item in diagnostics),
            key=core.diagnostic_sort_key,
        ),
    }


def _exact_reference(record: Mapping[str, Any], id_field: str) -> dict[str, Any]:
    return {
        id_field: record[id_field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def _generic_to_typed(
    reference: Mapping[str, Any], id_field: str
) -> dict[str, Any]:
    return {
        id_field: reference["stable_id"],
        "revision": reference["revision"],
        "content_hash": reference["content_hash"],
    }


def _profile_reference_set(
    profile: Mapping[str, Any], field: str, id_field: str
) -> set[tuple[str, int, str]]:
    return {
        (
            reference[id_field],
            reference["revision"],
            reference["content_hash"],
        )
        for reference in profile[field]
    }


def _profile_validation(
    context: OperationContext, profile: Mapping[str, Any]
) -> list[dict[str, str]]:
    schema = context.schemas.get("collection_profile_v0")
    if schema is None:
        return [
            _diagnostic(
                "COLLECTION_PROFILE_SCHEMA_UNAVAILABLE",
                "collection-profile",
                "$.payload.profile",
                "the exact collection-profile schema is absent",
            )
        ]
    return rules.validate_profile(
        profile,
        schema=schema,
        source_releases=context.records["source_releases"],
        providers=context.records["implementation_providers"],
        collections=context.records["object_collections"],
    )


def _collection_states(
    context: OperationContext, profile: Mapping[str, Any]
) -> dict[tuple[str, int, str], bool]:
    return {
        (
            state["collection_reference"]["object_collection_id"],
            state["collection_reference"]["revision"],
            state["collection_reference"]["content_hash"],
        ): state["enabled_for_discovery"]
        for state in profile["collection_states"]
    }


def _ordered_collections(
    context: OperationContext, profile: Mapping[str, Any]
) -> list[dict[str, Any]]:
    collections = list(context.records["object_collections"])
    by_key = {
        (
            item["object_collection_id"],
            item["revision"],
            item["content_hash"],
        ): item
        for item in collections
    }
    order_keys = [
        (
            item["object_collection_id"],
            item["revision"],
            item["content_hash"],
        )
        for item in profile["collection_order"]
    ]
    ordered = [by_key[key] for key in order_keys]
    ordered_keys = set(order_keys)
    ordered.extend(
        sorted(
            (item for key, item in by_key.items() if key not in ordered_keys),
            key=lambda item: (
                item["display_name"].casefold().encode("utf-8"),
                item["object_collection_id"],
            ),
        )
    )
    return ordered


def _implementation_map(context: OperationContext) -> dict[str, dict[str, Any]]:
    projection = context.catalog_projection or {}
    return {
        implementation["implementation_id"]: implementation
        for family in projection.get("families", ())
        for implementation in family["implementations"]
    }


def _availability_counts(
    implementation_ids: Iterable[str],
    implementations: Mapping[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows_by_pair: dict[str, list[dict[str, Any]]] = {}
    pair_order: list[str] = []
    for implementation_id in implementation_ids:
        for row in implementations[implementation_id]["target_availability"]:
            if row["pair_id"] not in rows_by_pair:
                rows_by_pair[row["pair_id"]] = []
                pair_order.append(row["pair_id"])
            rows_by_pair[row["pair_id"]].append(row)
    result: list[dict[str, Any]] = []
    for pair_id in pair_order:
        rows = rows_by_pair[pair_id]
        first = rows[0]
        readiness = Counter(
            state for row in rows for state in row["readiness_states"]
        )
        result.append(
            {
                "pair_id": pair_id,
                "display_name": first["display_name"],
                "target_reference": copy.deepcopy(first["target_reference"]),
                "backend_reference": copy.deepcopy(first["backend_reference"]),
                "implementation_count": len(rows),
                "binding_status_counts": dict(
                    sorted(Counter(row["binding_status"] for row in rows).items())
                ),
                "eligibility_status_counts": dict(
                    sorted(Counter(row["eligibility_status"] for row in rows).items())
                ),
                "provider_status_counts": dict(
                    sorted(Counter(row["provider_status"] for row in rows).items())
                ),
                "readiness_state_counts": dict(sorted(readiness.items())),
            }
        )
    return result


def inspect_collections(
    context: OperationContext, profile: Mapping[str, Any]
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    """Return discovery state without changing semantic or selection state."""

    implementations = _implementation_map(context)
    installed_sources = _profile_reference_set(
        profile, "installed_source_release_references", "source_release_id"
    )
    installed_providers = _profile_reference_set(
        profile, "installed_provider_references", "implementation_provider_id"
    )
    states = _collection_states(context, profile)
    source_registry = {
        (
            item["source_release_id"],
            item["revision"],
            item["content_hash"],
        ): item
        for item in context.records["source_releases"]
    }
    provider_bindings = [
        (provider, binding)
        for provider in context.records["implementation_providers"]
        if (
            provider["implementation_provider_id"],
            provider["revision"],
            provider["content_hash"],
        )
        in installed_providers
        for binding in provider["bindings"]
    ]
    diagnostics: list[dict[str, str]] = []
    values: list[dict[str, Any]] = []
    for position, collection in enumerate(_ordered_collections(context, profile)):
        reference = _exact_reference(collection, "object_collection_id")
        key = (
            reference["object_collection_id"],
            reference["revision"],
            reference["content_hash"],
        )
        enabled = states.get(key, False)
        if not enabled:
            diagnostics.append(
                _diagnostic(
                    "COLLECTION_DISCOVERY_DISABLED",
                    f"{collection['object_collection_id']}@{collection['revision']}",
                    "$.payload.profile.collection_states",
                    "the collection is disabled for discovery; graph and provider identity are unchanged",
                    severity="info",
                )
            )
        collection_ids = set(collection["implementation_ids"])
        sources = []
        for source_reference in collection["source_release_references"]:
            source_key = (
                source_reference["source_release_id"],
                source_reference["revision"],
                source_reference["content_hash"],
            )
            sources.append(
                {
                    "source_release": copy.deepcopy(source_registry[source_key]),
                    "installed": source_key in installed_sources,
                }
            )
        values.append(
            {
                "collection": copy.deepcopy(collection),
                "presentation_position": position,
                "enabled_for_discovery": enabled,
                "installed_source_release_count": sum(
                    source["installed"] for source in sources
                ),
                "source_releases": sources,
                "installed_provider_binding_count": sum(
                    binding["catalog_implementation_locator"]["implementation_id"]
                    in collection_ids
                    for _, binding in provider_bindings
                ),
                "target_availability": _availability_counts(
                    collection["implementation_ids"], implementations
                ),
            }
        )
    profile_bytes = core.canonical_json(profile).encode("utf-8")
    projection = context.catalog_projection or {}
    return (
        {
            "record_set_reference": copy.deepcopy(context.record_set_reference),
            "catalog_reference": copy.deepcopy(projection["catalog_reference"]),
            "availability_policy_reference": copy.deepcopy(
                projection["availability_policy_reference"]
            ),
            "local_profile_fingerprint": "sha256:"
            + hashlib.sha256(profile_bytes).hexdigest(),
            "collections": values,
            "project_owned_source_view": {
                "source_kind": "exact-project-owned",
                "collection_membership": "never",
                "installed_state": "not-applicable",
                "graph_identity_effect": "none",
                "build_priority_effect": "none",
            },
            "boundary_summary": {
                "collection_order_effect": "presentation-only",
                "collection_enablement_effect": "discovery-only",
                "source_presence_implies_target_support": False,
                "provider_selection_uses_collection_order": False,
                "project_or_graph_mutation": "not-run",
                "backend_or_hardware_execution": "not-run",
            },
            "validation_summary": copy.deepcopy(
                context.collection_provider_summary
            ),
        },
        diagnostics,
    )


def _implementation_and_family(
    context: OperationContext, implementation_id: str
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    projection = context.catalog_projection or {}
    matches = [
        (implementation, family)
        for family in projection.get("families", ())
        for implementation in family["implementations"]
        if implementation["implementation_id"] == implementation_id
    ]
    return matches[0] if len(matches) == 1 else None


def _pair_row(
    implementation: Mapping[str, Any],
    target_reference: Mapping[str, Any],
    backend_reference: Mapping[str, Any],
) -> dict[str, Any] | None:
    matches = [
        row
        for row in implementation["target_availability"]
        if _generic_to_typed(row["target_reference"], "compute_target_id")
        == target_reference
        and _generic_to_typed(row["backend_reference"], "backend_id")
        == backend_reference
    ]
    return matches[0] if len(matches) == 1 else None


def _collection_memberships(
    context: OperationContext,
    profile: Mapping[str, Any],
    implementation_id: str,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    states = _collection_states(context, profile)
    memberships: list[dict[str, Any]] = []
    diagnostics: list[dict[str, str]] = []
    for collection in sorted(
        context.records["object_collections"],
        key=lambda value: value["object_collection_id"],
    ):
        if implementation_id not in collection["implementation_ids"]:
            continue
        reference = _exact_reference(collection, "object_collection_id")
        key = (
            reference["object_collection_id"],
            reference["revision"],
            reference["content_hash"],
        )
        enabled = states.get(key, False)
        memberships.append(
            {
                "collection_reference": reference,
                "display_name": collection["display_name"],
                "enabled_for_discovery": enabled,
            }
        )
        if not enabled:
            diagnostics.append(
                _diagnostic(
                    "COLLECTION_DISCOVERY_DISABLED",
                    f"{collection['object_collection_id']}@{collection['revision']}",
                    "$.payload.profile.collection_states",
                    "this membership is hidden from discovery only; runtime availability is unchanged",
                    severity="info",
                )
            )
    return memberships, diagnostics


def inspect_implementation_availability(
    context: OperationContext, payload: Mapping[str, Any]
) -> tuple[str, dict[str, Any] | None, list[dict[str, str]]]:
    projection = context.catalog_projection or {}
    locator = payload["catalog_implementation_locator"]
    selected_catalog = projection.get("catalog_reference")
    if locator["catalog_reference"] != selected_catalog:
        same_identity = (
            selected_catalog is not None
            and locator["catalog_reference"]["catalog_id"]
            == selected_catalog["catalog_id"]
            and locator["catalog_reference"]["revision"]
            == selected_catalog["revision"]
        )
        return (
            "invalid",
            None,
            [
                _diagnostic(
                    "CATALOG_REFERENCE_STALE" if same_identity else "CATALOG_REFERENCE_UNRESOLVED",
                    locator["implementation_id"],
                    "$.payload.catalog_implementation_locator.catalog_reference",
                    "the locator does not name the exact selected catalog",
                )
            ],
        )
    resolved = _implementation_and_family(context, locator["implementation_id"])
    if resolved is None:
        return (
            "invalid",
            None,
            [
                _diagnostic(
                    "CATALOG_IMPLEMENTATION_UNRESOLVED",
                    locator["implementation_id"],
                    "$.payload.catalog_implementation_locator.implementation_id",
                    "the exact catalog contains no unique implementation with this identity",
                )
            ],
        )
    implementation, family = resolved
    memberships, diagnostics = _collection_memberships(
        context, payload["profile"], implementation["implementation_id"]
    )
    row = _pair_row(
        implementation,
        payload["target_reference"],
        payload["backend_reference"],
    )
    base_value = {
        "record_set_reference": copy.deepcopy(context.record_set_reference),
        "catalog_implementation_locator": copy.deepcopy(locator),
        "family_reference": copy.deepcopy(family["family_reference"]),
        "implementation": copy.deepcopy(implementation),
        "collection_memberships": memberships,
        "discovery_visibility": (
            "enabled"
            if any(item["enabled_for_discovery"] for item in memberships)
            else "disabled-or-uncollected"
        ),
        "requested_target_reference": copy.deepcopy(payload["target_reference"]),
        "requested_backend_reference": copy.deepcopy(payload["backend_reference"]),
        "selected_provider": None,
        "selected_provider_binding": None,
        "execution_availability": "unsupported",
        "boundary_summary": {
            "collection_state_affects_provider_selection": False,
            "collection_order_affects_binding_priority": False,
            "source_presence_implies_target_support": False,
            "fallback_attempted": False,
            "project_or_graph_mutation": "not-run",
            "backend_or_hardware_execution": "not-run",
        },
    }
    if row is None:
        diagnostics.append(
            _diagnostic(
                "IMPLEMENTATION_TARGET_UNSUPPORTED",
                implementation["implementation_id"],
                "$.payload.target_reference",
                "the exact target/backend pair is outside the reported availability policy; no fallback was attempted",
            )
        )
        return "unsupported", base_value, diagnostics
    base_value["target_availability"] = copy.deepcopy(row)
    if row["eligibility_status"] != "supported":
        diagnostics.append(
            _diagnostic(
                "IMPLEMENTATION_TARGET_UNSUPPORTED",
                implementation["implementation_id"],
                "$.payload.target_reference",
                f"exact eligibility for this target/backend pair is {row['eligibility_status']}; no fallback was attempted",
            )
        )
        return "unsupported", base_value, diagnostics
    if row["provider_status"] == "ambiguous" or len(row["provider_references"]) > 1:
        base_value["execution_availability"] = "ambiguous-provider"
        diagnostics.append(
            _diagnostic(
                "PROVIDER_BINDING_AMBIGUOUS",
                implementation["implementation_id"],
                "$.target_availability.provider_references",
                "more than one provider claims the exact implementation and target/backend pair",
            )
        )
        return "ambiguous", base_value, diagnostics
    if row["provider_status"] != "available" or len(row["provider_references"]) != 1:
        base_value["execution_availability"] = "provider-unavailable"
        diagnostics.append(
            _diagnostic(
                "PROVIDER_UNAVAILABLE",
                implementation["implementation_id"],
                "$.target_availability.provider_references",
                "no exact provider is declared for the eligible implementation pair; no fallback was attempted",
            )
        )
        return "unavailable", base_value, diagnostics

    provider_reference = _generic_to_typed(
        row["provider_references"][0], "implementation_provider_id"
    )
    provider_matches = [
        provider
        for provider in context.records["implementation_providers"]
        if _exact_reference(provider, "implementation_provider_id")
        == provider_reference
    ]
    if len(provider_matches) != 1:
        base_value["execution_availability"] = "provider-unavailable"
        diagnostics.append(
            _diagnostic(
                "PROVIDER_UNAVAILABLE",
                implementation["implementation_id"],
                "$.target_availability.provider_references",
                "the exact declared provider record is absent; no fallback was attempted",
            )
        )
        return "unavailable", base_value, diagnostics
    provider = provider_matches[0]
    installed_providers = _profile_reference_set(
        payload["profile"],
        "installed_provider_references",
        "implementation_provider_id",
    )
    provider_key = (
        provider["implementation_provider_id"],
        provider["revision"],
        provider["content_hash"],
    )
    if provider_key not in installed_providers:
        base_value["execution_availability"] = "provider-unavailable"
        diagnostics.append(
            _diagnostic(
                "PROVIDER_UNAVAILABLE",
                implementation["implementation_id"],
                "$.payload.profile.installed_provider_references",
                "the exact provider is not installed in the local profile; no fallback was attempted",
            )
        )
        return "unavailable", base_value, diagnostics
    installed_sources = _profile_reference_set(
        payload["profile"],
        "installed_source_release_references",
        "source_release_id",
    )
    missing_sources = [
        reference
        for reference in provider["required_source_release_references"]
        if (
            reference["source_release_id"],
            reference["revision"],
            reference["content_hash"],
        )
        not in installed_sources
    ]
    if missing_sources:
        base_value["execution_availability"] = "source-unavailable"
        diagnostics.extend(
            _diagnostic(
                "SOURCE_RELEASE_MISSING",
                reference["source_release_id"],
                "$.payload.profile.installed_source_release_references",
                "the exact provider source release is not installed; no fallback was attempted",
            )
            for reference in missing_sources
        )
        return "unavailable", base_value, diagnostics
    use_context = payload["profile"]["use_context"]
    license_reviewed = (
        provider["license_boundary"]["private_development_status"] == "reviewed"
        if use_context == "private-development"
        else provider["license_boundary"]["distribution_status"] != "review-required"
    )
    if not license_reviewed:
        base_value["execution_availability"] = "license-unreviewed"
        diagnostics.append(
            _diagnostic(
                "PROVIDER_LICENSE_UNREVIEWED",
                provider["implementation_provider_id"],
                "$.payload.profile.use_context",
                f"provider licensing is not reviewed for {use_context}; no fallback was attempted",
            )
        )
        return "unavailable", base_value, diagnostics

    binding_matches = [
        binding
        for binding in provider["bindings"]
        if binding["catalog_implementation_locator"] == locator
        and binding["target_reference"] == payload["target_reference"]
        and binding["backend_reference"] == payload["backend_reference"]
    ]
    if len(binding_matches) != 1:
        base_value["execution_availability"] = "ambiguous-provider"
        diagnostics.append(
            _diagnostic(
                "PROVIDER_BINDING_AMBIGUOUS",
                implementation["implementation_id"],
                "$.implementation_provider.bindings",
                "the installed provider does not resolve exactly one provider binding",
            )
        )
        return "ambiguous", base_value, diagnostics
    base_value["selected_provider"] = copy.deepcopy(provider)
    base_value["selected_provider_binding"] = copy.deepcopy(binding_matches[0])
    base_value["execution_availability"] = "available"
    return "success", base_value, diagnostics


def dispatch_collection_provider_operation(
    request: dict[str, Any], context: OperationContext
) -> dict[str, Any]:
    """Validate and dispatch the two Phase 2 read-only operations."""

    request_schema = context.schemas.get("operation_request_v18")
    result_schema = context.schemas.get("operation_result_v18")
    operation = request.get("operation") if isinstance(request, dict) else None
    if request_schema is None or result_schema is None:
        raise ValueError("Task 033 Phase 2 operation schemas are unavailable")
    errors: list[str] = []
    try:
        core.assert_portable_json_value(request)
    except ValueError as error:
        errors.append(str(error))
    errors.extend(core.schema_errors(request, request_schema, request_schema))
    allowed = {"collections.inspect", "implementation.availability.inspect"}
    if errors:
        result = _result(
            operation if operation in allowed else "invalid-request",
            "invalid",
            None,
            [
                _diagnostic(
                    "OPERATION_REQUEST_INVALID",
                    str(operation or "invalid-request"),
                    "$",
                    error,
                )
                for error in sorted(set(errors))
            ],
        )
        canonical_result_bytes(result, context)
        return result
    profile_diagnostics = _profile_validation(context, request["payload"]["profile"])
    if profile_diagnostics:
        result = _result(operation, "invalid", None, profile_diagnostics)
        canonical_result_bytes(result, context)
        return result
    profile_schema = context.schemas["collection_profile_v0"]
    payload = copy.deepcopy(request["payload"])
    payload["profile"] = core.canonicalize_with_schema(
        payload["profile"], profile_schema, profile_schema
    )
    if operation == "collections.inspect":
        value, diagnostics = inspect_collections(
            context, payload["profile"]
        )
        result = _result(operation, "success", value, diagnostics)
    else:
        status, value, diagnostics = inspect_implementation_availability(
            context, payload
        )
        result = _result(operation, status, value, diagnostics)
    canonical_result_bytes(result, context)
    return result
