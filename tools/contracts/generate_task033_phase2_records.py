#!/usr/bin/env python3
"""Generate Task 033 Phase 2 collection/provider contracts and record set."""

from __future__ import annotations

import argparse
import copy
import hashlib
from pathlib import Path
import sys
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "tools/contracts") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools/contracts"))

from tools.contracts import record_set_rules  # noqa: E402
from tools.contracts import validator_core as core  # noqa: E402


PARENT = ROOT / "contracts/record-sets/task034-performance-control-v1.json"
OUTPUT = ROOT / "contracts/record-sets/task033-phase2-collection-provider-v1.json"
TASK_DIR = ROOT / "contracts/task033/phase2"
RECORD_SET_ID = "schuss-record-set-000031"
PARENT_REFERENCE = {
    "record_set_id": "schuss-record-set-000030",
    "revision": 1,
    "content_hash": "sha256:199b3b2f8fe20ea6a2ce4751a9bd4d35a2e6522d69252ef916c7668ad5e93c54",
}
SCHEMA_NAMES = (
    "application-capability-description-v11",
    "catalog-corpus-v6",
    "catalog-projection-v6",
    "collection-profile-v0",
    "implementation-availability-policy-v0",
    "implementation-provider-v0",
    "object-collection-v0",
    "operation-request-v18",
    "operation-result-v18",
    "source-release-v0",
)
SOURCE_LOCK_PATH = "catalog/sources.lock.json"
JUCE_LOCK_PATH = "contracts/task031/juce-source-lock.json"
JUCE_AUDIT_PATH = "catalog/reviews/task033-juce-dsp-audit-v1/manifest.json"
SCHUSS_SOURCE_COMMIT = "c1eaea0114630d07e59c859b9264c3de24909e54"
SCHUSS_SOURCE_URL = "https://github.com/lalzart/schuss.git"
SCHUSS_SOURCE_FILE_HASHES = {
    "packages/schuss_rt/CMakeLists.txt": "65ae742fc3bb224d92d14953bb4d9c987c16c452bae655558ea61fd6aa760e60",
    "packages/schuss_rt/include/schuss_rt/runtime.hpp": "ba710c64425f409ba92627afb0e30e83ae09f2182912588eedc559acc225d8e2",
    "packages/schuss_rt/include/schuss_rt/runtime_replacement.hpp": "d2ec130b689354ced95fddfc5b71a366fb7cdffdc9b88996fdbfd132b8b164d9",
    "packages/schuss_rt/include/schuss_rt/runtime_v1.hpp": "37ccbc72f0c33f764a535fb1088e915fef07a228f70c1f481fbd99fbb8bb9f3f",
    "packages/schuss_rt/include/schuss_rt/sha256.hpp": "59d4f6a9724aeaef65ff8ef9ba473287d3702e7fec756d44e095437bbd59db34",
    "packages/schuss_rt/src/package_parser.cpp": "04a534a6329653a0acdf7941db4c89ad9ff6284e0af5847d4d58236954942404",
    "packages/schuss_rt/src/package_parser_v1.cpp": "b332e9f2379dcdd83dbef7513d9044057e651db02870ce9ed720085af3c3baf1",
    "packages/schuss_rt/src/runtime.cpp": "455221c3b0d80251b5aa77fa56a2305eea7606dc8bdc61f7d782072ce079353d",
    "packages/schuss_rt/src/runtime_v1.cpp": "d224c6bfd5c89ca369e6516058cb19a84ca00e600ad775482488a55858699122",
    "packages/schuss_rt/src/sha256.cpp": "da778852a234453009ae6fa16a9f447bb61fff75700538adcda7e8285fa7587a",
    "packages/schuss_rt/tests/runtime_replacement_tests.cpp": "9ef9316484014f3e7df53797f49036d496e8dff7f155144586d8220a831f2fdc",
    "packages/schuss_rt/tests/runtime_tests.cpp": "cd5e62e93cf4c1c8e0f2ae284a86a1c4dd8d479c2a2f54dc23f0c0b6dbc31a6f",
    "packages/schuss_rt/tests/runtime_v1_tests.cpp": "92efcee61e351591fa23dd56f36a003ee60caf0c1628252b9cd3c5a05c6fb034",
}

HOST_SPECS = (
    (162, "saw", "Saw oscillator", "schuss.rt.saw-q27-v0"),
    (163, "pwm", "PWM oscillator", "schuss.rt.pwm-q27-v0"),
    (164, "soft", "Soft clipper", "schuss.rt.soft-q27-v0"),
    (165, "smooth", "Exponential smoother", "schuss.rt.smooth-q27-v0"),
    (166, "crossfade", "Crossfader", "schuss.rt.crossfade-q27-v0"),
    (167, "vca", "VCA", "schuss.rt.vca-q27-v0"),
    (168, "output", "Stereo output", "schuss.rt.output-q27-v0"),
)


def _canonical_bytes(value: object) -> bytes:
    return (core.canonical_json(value) + "\n").encode("utf-8")


def _raw_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _closed(required: Iterable[str], properties: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "type": "object",
        "required": list(required),
        "properties": dict(properties),
        "additionalProperties": False,
    }


def _set(items: dict[str, Any], *, minimum: int = 0) -> dict[str, Any]:
    return {
        "type": "array",
        "x-schuss-array-kind": "set",
        "minItems": minimum,
        "uniqueItems": True,
        "items": items,
    }


def _sequence(items: dict[str, Any], *, minimum: int = 0) -> dict[str, Any]:
    return {
        "type": "array",
        "x-schuss-array-kind": "sequence",
        "minItems": minimum,
        "uniqueItems": True,
        "items": items,
    }


def _content_hash() -> dict[str, Any]:
    return {"type": "string", "pattern": r"^sha256:[0-9a-f]{64}$"}


def _raw_hash() -> dict[str, Any]:
    return {"type": "string", "pattern": r"^[0-9a-f]{64}$"}


def _portable_path() -> dict[str, Any]:
    return {
        "type": "string",
        "minLength": 1,
        "pattern": r"^(?!/)(?!.*(?:^|/)\.\.(?:/|$))(?!.*\\).+$",
    }


def _label() -> dict[str, Any]:
    return {"type": "string", "minLength": 1}


def _reference(id_field: str, pattern: str) -> dict[str, Any]:
    return _closed(
        (id_field, "revision", "content_hash"),
        {
            id_field: {"type": "string", "pattern": pattern},
            "revision": {"type": "integer", "minimum": 1},
            "content_hash": _content_hash(),
        },
    )


def _generic_reference() -> dict[str, Any]:
    return _closed(
        ("stable_id", "revision", "content_hash"),
        {
            "stable_id": {"type": "string", "pattern": r"^schuss-[a-z0-9-]+-[0-9]{6}$"},
            "revision": {"type": "integer", "minimum": 1},
            "content_hash": _content_hash(),
        },
    )


def _catalog_reference() -> dict[str, Any]:
    return _reference("catalog_id", r"^schuss-catalog-[0-9]{6}$")


def _catalog_locator() -> dict[str, Any]:
    return _closed(
        ("catalog_reference", "implementation_id"),
        {
            "catalog_reference": _catalog_reference(),
            "implementation_id": {
                "type": "string",
                "pattern": r"^schuss-implementation-[0-9]{6}$",
            },
        },
    )


def _target_backend_pair() -> dict[str, Any]:
    return _closed(
        ("target_reference", "backend_reference"),
        {
            "target_reference": _reference(
                "compute_target_id", r"^schuss-compute-target-[0-9]{6}$"
            ),
            "backend_reference": _reference(
                "backend_id", r"^schuss-backend-[0-9]{6}$"
            ),
        },
    )


def _identity(
    schema_version: str, id_field: str, pattern: str
) -> tuple[tuple[str, ...], dict[str, Any]]:
    return (
        (
            "schema_version",
            "canonical_profile",
            id_field,
            "revision",
            "content_hash",
            "display_name",
        ),
        {
            "schema_version": {"const": schema_version},
            "canonical_profile": {"const": "schuss-canonical-json-v1"},
            id_field: {"type": "string", "pattern": pattern},
            "revision": {"type": "integer", "minimum": 1},
            "content_hash": _content_hash(),
            "display_name": _label(),
        },
    )


def _source_release_schema() -> dict[str, Any]:
    required, properties = _identity(
        "source-release-v0", "source_release_id", r"^schuss-source-release-[0-9]{6}$"
    )
    repository = _closed(
        ("identity_kind", "repository_url", "commit"),
        {
            "identity_kind": {"const": "git-commit"},
            "repository_url": {"type": "string", "pattern": r"^https://[^ ]+$"},
            "commit": {"type": "string", "pattern": r"^[0-9a-f]{40}$"},
        },
    )
    archive = copy.deepcopy(repository)
    archive["required"] = [
        "identity_kind",
        "repository_url",
        "commit",
        "archive_url",
        "archive_sha256",
        "tag",
    ]
    archive["properties"]["identity_kind"] = {"const": "git-archive"}
    archive["properties"].update(
        {
            "archive_url": {"type": "string", "pattern": r"^https://[^ ]+$"},
            "archive_sha256": _raw_hash(),
            "tag": _label(),
        }
    )
    anchor = {
        "oneOf": [
            _closed(
                ("anchor_kind", "portable_path", "byte_sha256", "scope"),
                {
                    "anchor_kind": {"const": "portable-file"},
                    "portable_path": _portable_path(),
                    "byte_sha256": _raw_hash(),
                    "scope": _label(),
                },
            ),
            _closed(
                (
                    "anchor_kind",
                    "portable_path",
                    "byte_sha256",
                    "entry_sha256",
                    "scope",
                ),
                {
                    "anchor_kind": {"const": "source-lock-entry"},
                    "portable_path": _portable_path(),
                    "byte_sha256": _raw_hash(),
                    "entry_sha256": _raw_hash(),
                    "scope": _label(),
                },
            ),
            _closed(
                (
                    "anchor_kind",
                    "portable_path",
                    "byte_sha256",
                    "record_reference",
                    "scope",
                ),
                {
                    "anchor_kind": {"const": "semantic-record"},
                    "portable_path": _portable_path(),
                    "byte_sha256": _raw_hash(),
                    "record_reference": _generic_reference(),
                    "scope": _label(),
                },
            ),
        ]
    }
    license_evidence = _closed(
        ("scope", "status", "declared_expression", "limitations"),
        {
            "scope": _label(),
            "status": {
                "enum": ["unreviewed", "repository-declared-only", "scope-reviewed"]
            },
            "declared_expression": _label(),
            "limitations": _set(_label()),
        },
    )
    properties.update(
        {
            "portable_source_id": {
                "type": "string",
                "pattern": r"^[a-z][a-z0-9-]*$",
            },
            "release_scope": {
                "enum": [
                    "object-library",
                    "patcher-source",
                    "native-runtime",
                    "audited-candidate-source",
                ]
            },
            "release_identity": {"oneOf": [repository, archive]},
            "evidence_anchors": _set(anchor, minimum=1),
            "declared_license_evidence": _set(license_evidence, minimum=1),
            "distribution_review_status": {
                "enum": [
                    "not-reviewed",
                    "required-before-distribution",
                    "private-development-reviewed",
                ]
            },
            "importer_boundary": {
                "enum": [
                    "inventory-candidate-only",
                    "audited-candidate-only",
                    "static-native-provider-source",
                ]
            },
            "support_claim": {"const": "source-identity-and-provenance-only"},
        }
    )
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "source-release-v0.schema.json",
        "title": "Schuss source release v0",
        **_closed(
            (
                *required,
                "portable_source_id",
                "release_scope",
                "release_identity",
                "evidence_anchors",
                "declared_license_evidence",
                "distribution_review_status",
                "importer_boundary",
                "support_claim",
            ),
            properties,
        ),
    }


def _object_collection_schema() -> dict[str, Any]:
    required, properties = _identity(
        "object-collection-v0",
        "object_collection_id",
        r"^schuss-object-collection-[0-9]{6}$",
    )
    properties.update(
        {
            "description": _label(),
            "distribution_role": {
                "enum": ["core", "first-party", "contributed", "audited-provenance"]
            },
            "catalog_reference": _catalog_reference(),
            "source_release_references": _set(
                _reference("source_release_id", r"^schuss-source-release-[0-9]{6}$")
            ),
            "implementation_ids": _set(
                {
                    "type": "string",
                    "pattern": r"^schuss-implementation-[0-9]{6}$",
                },
                minimum=1,
            ),
            "membership_rule": {"const": "exact-catalog-reference-plus-implementation-id"},
            "function_neutral": {"const": True},
            "target_promise": {"const": False},
            "project_identity_authority": {"const": False},
        }
    )
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "object-collection-v0.schema.json",
        "title": "Schuss object collection v0",
        **_closed(
            (
                *required,
                "description",
                "distribution_role",
                "catalog_reference",
                "source_release_references",
                "implementation_ids",
                "membership_rule",
                "function_neutral",
                "target_promise",
                "project_identity_authority",
            ),
            properties,
        ),
    }


def _implementation_provider_schema() -> dict[str, Any]:
    required, properties = _identity(
        "implementation-provider-v0",
        "implementation_provider_id",
        r"^schuss-implementation-provider-[0-9]{6}$",
    )
    pair = _target_backend_pair()
    binding = _closed(
        (
            "provider_binding_id",
            "catalog_implementation_locator",
            "component_contract_reference",
            "implementation_binding_reference",
            "eligibility_reference",
            "target_reference",
            "backend_reference",
            "runtime_factory_id",
        ),
        {
            "provider_binding_id": {
                "type": "string",
                "pattern": r"^provider-binding-[0-9]{6}$",
            },
            "catalog_implementation_locator": _catalog_locator(),
            "component_contract_reference": _reference(
                "component_contract_id", r"^schuss-component-contract-[0-9]{6}$"
            ),
            "implementation_binding_reference": _reference(
                "implementation_id", r"^schuss-implementation-[0-9]{6}$"
            ),
            "eligibility_reference": _reference(
                "binding_eligibility_id", r"^schuss-binding-eligibility-[0-9]{6}$"
            ),
            "target_reference": pair["properties"]["target_reference"],
            "backend_reference": pair["properties"]["backend_reference"],
            "runtime_factory_id": {
                "type": "string",
                "pattern": r"^schuss\.rt\.[a-z0-9-]+$",
            },
        },
    )
    license_boundary = _closed(
        ("private_development_status", "distribution_status"),
        {
            "private_development_status": {
                "enum": ["reviewed", "unreviewed"]
            },
            "distribution_status": {"const": "review-required"},
        },
    )
    properties.update(
        {
            "provider_kind": {"const": "statically-linked"},
            "source_release_reference": _reference(
                "source_release_id", r"^schuss-source-release-[0-9]{6}$"
            ),
            "provider_abi": {"const": "schuss-rt-abi-v1"},
            "registry_version": {"const": "schuss-rt-factory-registry-v1"},
            "target_backend_pairs": _set(pair, minimum=1),
            "required_source_release_references": _set(
                _reference("source_release_id", r"^schuss-source-release-[0-9]{6}$"),
                minimum=1,
            ),
            "link_requirements": _set(_label()),
            "callback_constraints": _set(
                {
                    "enum": [
                        "no-allocation",
                        "no-filesystem",
                        "no-locking",
                        "no-network",
                        "no-process-control",
                    ]
                },
                minimum=5,
            ),
            "license_boundary": license_boundary,
            "bindings": _set(binding, minimum=1),
            "selection_priority_owner": {"const": "binding-eligibility"},
            "dynamic_loading": {"const": False},
        }
    )
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "implementation-provider-v0.schema.json",
        "title": "Schuss implementation provider v0",
        **_closed(
            (
                *required,
                "provider_kind",
                "source_release_reference",
                "provider_abi",
                "registry_version",
                "target_backend_pairs",
                "required_source_release_references",
                "link_requirements",
                "callback_constraints",
                "license_boundary",
                "bindings",
                "selection_priority_owner",
                "dynamic_loading",
            ),
            properties,
        ),
    }


def _availability_policy_schema() -> dict[str, Any]:
    required, properties = _identity(
        "implementation-availability-policy-v0",
        "implementation_availability_policy_id",
        r"^schuss-implementation-availability-policy-[0-9]{6}$",
    )
    pair = _target_backend_pair()
    pair["required"] = ["pair_id", "display_name", *pair["required"]]
    pair["properties"].update(
        {
            "pair_id": {
                "type": "string",
                "pattern": r"^availability-pair-[0-9]{6}$",
            },
            "display_name": _label(),
        }
    )
    properties.update(
        {
            "catalog_reference": _catalog_reference(),
            "reported_pairs": _sequence(pair, minimum=1),
            "readiness_order": _sequence(
                {
                    "enum": [
                        "catalogued-only",
                        "contracted",
                        "bound",
                        "eligible",
                        "compile-proven",
                        "device-tested",
                        "real-time-tested",
                        "audible-tested",
                        "unresolved",
                    ]
                },
                minimum=9,
            ),
            "selection_authority": {"const": False},
            "family_union_allowed": {"const": False},
            "source_presence_implies_support": {"const": False},
        }
    )
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "implementation-availability-policy-v0.schema.json",
        "title": "Schuss implementation availability policy v0",
        **_closed(
            (
                *required,
                "catalog_reference",
                "reported_pairs",
                "readiness_order",
                "selection_authority",
                "family_union_allowed",
                "source_presence_implies_support",
            ),
            properties,
        ),
    }


def _collection_profile_schema() -> dict[str, Any]:
    collection_ref = _reference(
        "object_collection_id", r"^schuss-object-collection-[0-9]{6}$"
    )
    state = _closed(
        ("collection_reference", "enabled_for_discovery"),
        {
            "collection_reference": collection_ref,
            "enabled_for_discovery": {"type": "boolean"},
        },
    )
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "collection-profile-v0.schema.json",
        "title": "Schuss machine-local collection profile v0",
        **_closed(
            (
                "schema_version",
                "canonical_profile",
                "use_context",
                "installed_source_release_references",
                "installed_provider_references",
                "collection_states",
                "collection_order",
            ),
            {
                "schema_version": {"const": "collection-profile-v0"},
                "canonical_profile": {"const": "schuss-canonical-json-v1"},
                "use_context": {"enum": ["private-development", "distribution-review"]},
                "installed_source_release_references": _set(
                    _reference("source_release_id", r"^schuss-source-release-[0-9]{6}$")
                ),
                "installed_provider_references": _set(
                    _reference(
                        "implementation_provider_id",
                        r"^schuss-implementation-provider-[0-9]{6}$",
                    )
                ),
                "collection_states": _set(state),
                "collection_order": _sequence(collection_ref),
            },
        ),
    }


def _catalog_schemas() -> tuple[dict[str, Any], dict[str, Any]]:
    corpus = copy.deepcopy(core.load_json(ROOT / "schemas/catalog-corpus-v5.schema.json"))
    corpus["$id"] = "catalog-corpus-v6.schema.json"
    corpus["title"] = "Schuss complete catalog corpus with native host companions v6"
    corpus["properties"]["schema_version"] = {"const": "catalog-corpus-v6"}
    corpus["properties"]["revision"] = {"const": 6}
    corpus["properties"]["projection_version"] = {
        "const": "schuss-catalog-projection-v6"
    }
    corpus["properties"]["implementation_additions"]["maxItems"] = 102
    corpus["properties"]["implementation_additions"]["minItems"] = 102
    corpus["$defs"]["catalogReference"]["properties"]["revision"] = {"const": 5}
    corpus["$defs"]["sourceReleaseReference"] = _reference(
        "source_release_id", r"^schuss-source-release-[0-9]{6}$"
    )
    corpus["$defs"]["sourceAuthority"]["oneOf"].append(
        _closed(
            (
                "kind",
                "source_release_reference",
                "evidence_ref",
                "provider_boundary",
            ),
            {
                "kind": {"const": "schuss-native-core"},
                "source_release_reference": {
                    "$ref": "#/$defs/sourceReleaseReference"
                },
                "evidence_ref": {"const": "fixture:task032-native-runtime"},
                "provider_boundary": {"const": "static-native-provider"},
            },
        )
    )
    addition = corpus["$defs"]["implementationAddition"]
    addition["properties"]["form"]["enum"] = sorted(
        set(addition["properties"]["form"]["enum"]) | {"native-cpp"}
    )
    addition["properties"]["review_status"]["enum"] = sorted(
        set(addition["properties"]["review_status"]["enum"]) | {"task033-reviewed"}
    )

    projection = copy.deepcopy(
        core.load_json(ROOT / "schemas/catalog-projection-v5.schema.json")
    )
    projection["$id"] = "catalog-projection-v6.schema.json"
    projection["title"] = "Schuss catalog projection with per-target availability v6"
    projection["properties"]["schema_version"] = {"const": "catalog-projection-v6"}
    projection["properties"]["projection_version"] = {
        "const": "schuss-catalog-projection-v6"
    }
    projection["$defs"]["catalogReference"]["properties"]["revision"] = {
        "const": 6
    }
    projection["$defs"]["targetAvailability"] = _closed(
        (
            "pair_id",
            "display_name",
            "target_reference",
            "backend_reference",
            "binding_status",
            "eligibility_status",
            "provider_status",
            "binding_references",
            "eligibility_references",
            "provider_references",
            "readiness_states",
            "unresolved_facts",
        ),
        {
            "pair_id": {
                "type": "string",
                "pattern": r"^availability-pair-[0-9]{6}$",
            },
            "display_name": _label(),
            "target_reference": _generic_reference(),
            "backend_reference": _generic_reference(),
            "binding_status": {"enum": ["absent", "present"]},
            "eligibility_status": {
                "enum": [
                    "ambiguous",
                    "no-binding-or-eligibility",
                    "not-evaluated",
                    "supported",
                    "unresolved",
                    "unsupported",
                ]
            },
            "provider_status": {"enum": ["ambiguous", "available", "not-declared"]},
            "binding_references": _set(_generic_reference()),
            "eligibility_references": _set(_generic_reference()),
            "provider_references": _set(_generic_reference()),
            "readiness_states": _set(_label()),
            "unresolved_facts": _set(_label()),
        },
    )
    implementation = projection["$defs"]["implementationSummary"]
    implementation["properties"]["target_availability"] = {
        "type": "array",
        "x-schuss-array-kind": "sequence",
        "items": {"$ref": "#/$defs/targetAvailability"},
    }
    implementation["required"].append("target_availability")
    projection["properties"]["availability_policy_reference"] = _generic_reference()
    projection["required"].append("availability_policy_reference")
    return corpus, projection


def _operation_schemas(
    profile_schema: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    profile_value = copy.deepcopy(profile_schema)
    for key in ("$schema", "$id", "title"):
        profile_value.pop(key)
    base = {
        "schema_version": {"const": "schuss-operation-request-v18"},
        "canonical_profile": {"const": "schuss-canonical-json-v1"},
    }
    list_request = _closed(
        ("schema_version", "canonical_profile", "operation", "payload"),
        {
            **copy.deepcopy(base),
            "operation": {"const": "collections.inspect"},
            "payload": _closed(("profile",), {"profile": copy.deepcopy(profile_value)}),
        },
    )
    availability_request = _closed(
        ("schema_version", "canonical_profile", "operation", "payload"),
        {
            **copy.deepcopy(base),
            "operation": {"const": "implementation.availability.inspect"},
            "payload": _closed(
                (
                    "profile",
                    "catalog_implementation_locator",
                    "target_reference",
                    "backend_reference",
                ),
                {
                    "profile": copy.deepcopy(profile_value),
                    "catalog_implementation_locator": _catalog_locator(),
                    "target_reference": _reference(
                        "compute_target_id", r"^schuss-compute-target-[0-9]{6}$"
                    ),
                    "backend_reference": _reference(
                        "backend_id", r"^schuss-backend-[0-9]{6}$"
                    ),
                },
            ),
        },
    )
    request = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "operation-request-v18.schema.json",
        "title": "Schuss collection/provider operation request v18",
        "oneOf": [list_request, availability_request],
    }
    result = copy.deepcopy(core.load_json(ROOT / "schemas/operation-result-v17.schema.json"))
    result["$id"] = "operation-result-v18.schema.json"
    result["title"] = "Schuss collection/provider operation result v18"
    result["properties"]["schema_version"] = {
        "const": "schuss-operation-result-v18"
    }
    result["properties"]["operation"]["enum"] = [
        "collections.inspect",
        "implementation.availability.inspect",
        "invalid-request",
    ]

    application = copy.deepcopy(
        core.load_json(ROOT / "schemas/application-capability-description-v10.schema.json")
    )
    application["$id"] = "application-capability-description-v11.schema.json"
    application["title"] = "Schuss application capability description v11"
    application["properties"]["schema_version"] = {
        "const": "application-capability-description-v11"
    }
    application["properties"]["description_version"] = {
        "const": "schuss-application-capability-description-v11"
    }
    operation = application["$defs"]["operationCapability"]["properties"]
    operation["operation"]["enum"] = sorted(
        set(operation["operation"]["enum"])
        | {"collections.inspect", "implementation.availability.inspect"}
    )
    operation["request_schema_version"]["pattern"] = (
        r"^schuss-operation-request-v(?:[1-9]|1[0-8])$"
    )
    operation["result_schema_version"]["pattern"] = (
        r"^schuss-operation-result-v(?:[1-9]|1[0-8])$"
    )
    gates = application["$defs"]["gateSet"]["items"]["enum"]
    application["$defs"]["gateSet"]["items"]["enum"] = sorted(
        set(gates) | {"explicit-local-collection-profile"}
    )
    contexts = application["$defs"]["contextSet"]["items"]["enum"]
    application["$defs"]["contextSet"]["items"]["enum"] = sorted(
        set(contexts) | {"explicit-local-collection-profile"}
    )
    application["properties"]["operations"]["minItems"] = 47
    application["properties"]["operations"]["maxItems"] = 47
    return request, result, application


def _hash_record(record: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(record)
    result["content_hash"] = "sha256:" + "0" * 64
    result["content_hash"] = core.record_content_hash(result, schema)
    errors = core.schema_errors(result, schema, schema)
    if errors:
        raise ValueError("; ".join(errors))
    return result


def _child_hash(record: dict[str, Any]) -> str:
    material = copy.deepcopy(record)
    material.pop("content_hash", None)
    return "sha256:" + hashlib.sha256(
        core.canonical_json(material).encode("utf-8")
    ).hexdigest()


def _exact_ref(record: Mapping[str, Any], id_field: str) -> dict[str, Any]:
    return {
        id_field: record[id_field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def _generic_ref(record: Mapping[str, Any], id_field: str) -> dict[str, Any]:
    return {
        "stable_id": record[id_field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def _exact(
    values: Iterable[dict[str, Any]], id_field: str, stable_id: str, revision: int
) -> dict[str, Any]:
    matches = [
        value
        for value in values
        if value[id_field] == stable_id and value["revision"] == revision
    ]
    if len(matches) != 1:
        raise ValueError(f"exact parent record is absent or ambiguous: {stable_id}@{revision}")
    return matches[0]


def _source_releases(schema: dict[str, Any]) -> list[dict[str, Any]]:
    lock = core.load_json(ROOT / SOURCE_LOCK_PATH)
    lock_bytes = (ROOT / SOURCE_LOCK_PATH).read_bytes()
    lock_sha = _raw_sha256(lock_bytes)
    by_id = {entry["id"]: entry for entry in lock["sources"]}
    source_specs = (
        (1, "axoloti-factory", "Axoloti factory objects", "object-library"),
        (2, "ksoloti-objects", "Ksoloti first-party objects", "object-library"),
        (3, "axoloti-contrib", "Axoloti contributed objects", "object-library"),
        (4, "ksoloti-contrib", "Ksoloti contributed objects", "object-library"),
        (5, "patcher", "Pinned Ksoloti patcher source", "patcher-source"),
    )
    records: list[dict[str, Any]] = []
    for number, source_id, display_name, scope in source_specs:
        entry = by_id[source_id]
        record = {
            "schema_version": "source-release-v0",
            "canonical_profile": "schuss-canonical-json-v1",
            "source_release_id": f"schuss-source-release-{number:06d}",
            "revision": 1,
            "content_hash": "sha256:" + "0" * 64,
            "display_name": display_name,
            "portable_source_id": source_id,
            "release_scope": scope,
            "release_identity": {
                "identity_kind": "git-commit",
                "repository_url": entry["url"],
                "commit": entry["commit"],
            },
            "evidence_anchors": [
                {
                    "anchor_kind": "source-lock-entry",
                    "portable_path": SOURCE_LOCK_PATH,
                    "byte_sha256": lock_sha,
                    "entry_sha256": _raw_sha256(
                        core.canonical_json(entry).encode("utf-8")
                    ),
                    "scope": source_id,
                }
            ],
            "declared_license_evidence": [
                {
                    "scope": "repository-and-files",
                    "status": "unreviewed",
                    "declared_expression": "not-reviewed",
                    "limitations": [
                        "The source lock proves repository identity only and does not infer per-file licensing."
                    ],
                }
            ],
            "distribution_review_status": "not-reviewed",
            "importer_boundary": "inventory-candidate-only",
            "support_claim": "source-identity-and-provenance-only",
        }
        records.append(_hash_record(record, schema))

    actual_scoped_paths = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "packages/schuss_rt").rglob("*")
        if path.is_file()
    }
    if actual_scoped_paths != set(SCHUSS_SOURCE_FILE_HASHES):
        raise ValueError("Task 032 Schuss native runtime source membership changed")
    for portable_path, expected_hash in SCHUSS_SOURCE_FILE_HASHES.items():
        if core.sha256_file(ROOT / portable_path) != expected_hash:
            raise ValueError(
                f"Task 032 Schuss native runtime source changed: {portable_path}"
            )
    schuss = {
        "schema_version": "source-release-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "source_release_id": "schuss-source-release-000006",
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "display_name": "Schuss native runtime source",
        "portable_source_id": "schuss-native-core",
        "release_scope": "native-runtime",
        "release_identity": {
            "identity_kind": "git-commit",
            "repository_url": SCHUSS_SOURCE_URL,
            "commit": SCHUSS_SOURCE_COMMIT,
        },
        "evidence_anchors": [
            {
                "anchor_kind": "portable-file",
                "portable_path": portable_path,
                "byte_sha256": byte_sha256,
                "scope": "packages/schuss_rt",
            }
            for portable_path, byte_sha256 in sorted(
                SCHUSS_SOURCE_FILE_HASHES.items()
            )
        ],
        "declared_license_evidence": [
            {
                "scope": "private Schuss repository native runtime",
                "status": "scope-reviewed",
                "declared_expression": "private-project-source",
                "limitations": [
                    "Distribution and third-party dependency review remain separate."
                ],
            }
        ],
        "distribution_review_status": "private-development-reviewed",
        "importer_boundary": "static-native-provider-source",
        "support_claim": "source-identity-and-provenance-only",
    }
    records.append(_hash_record(schuss, schema))

    juce_lock = core.load_json(ROOT / JUCE_LOCK_PATH)
    juce_audit_bytes = (ROOT / JUCE_AUDIT_PATH).read_bytes()
    juce = {
        "schema_version": "source-release-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "source_release_id": "schuss-source-release-000007",
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "display_name": "JUCE 8.0.15 audited candidate source",
        "portable_source_id": "juce",
        "release_scope": "audited-candidate-source",
        "release_identity": {
            "identity_kind": "git-archive",
            "repository_url": juce_lock["source"]["repository_url"],
            "commit": juce_lock["source"]["commit"],
            "archive_url": juce_lock["source"]["archive_url"],
            "archive_sha256": juce_lock["source"]["archive_sha256"],
            "tag": juce_lock["source"]["tag"],
        },
        "evidence_anchors": [
            {
                "anchor_kind": "semantic-record",
                "portable_path": JUCE_LOCK_PATH,
                "byte_sha256": core.sha256_file(ROOT / JUCE_LOCK_PATH),
                "record_reference": _generic_ref(
                    juce_lock, "third_party_source_lock_id"
                ),
                "scope": "accepted Task 031 JUCE adapter modules",
            },
            {
                "anchor_kind": "portable-file",
                "portable_path": JUCE_AUDIT_PATH,
                "byte_sha256": _raw_sha256(juce_audit_bytes),
                "scope": "authenticated juce_dsp candidate audit",
            },
        ],
        "declared_license_evidence": [
            {
                "scope": "pinned JUCE repository and juce_dsp module",
                "status": "repository-declared-only",
                "declared_expression": "AGPL-3.0-or-later-or-commercial",
                "limitations": [
                    "Private development does not approve a distributable binary.",
                    "No JUCE DSP implementation or provider is accepted by Phase 2.",
                ],
            }
        ],
        "distribution_review_status": "required-before-distribution",
        "importer_boundary": "audited-candidate-only",
        "support_claim": "source-identity-and-provenance-only",
    }
    records.append(_hash_record(juce, schema))
    return records


def _catalog_records(
    schema: dict[str, Any],
    selector_schema: dict[str, Any],
    parent: record_set_rules.LoadedRecordSet,
    schuss_release: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    source = _exact(
        parent.records["catalog-corpus"], "catalog_id", "schuss-catalog-000001", 5
    )
    corpus = copy.deepcopy(source)
    corpus["schema_version"] = "catalog-corpus-v6"
    corpus["revision"] = 6
    corpus["content_hash"] = "sha256:" + "0" * 64
    corpus["projection_version"] = "schuss-catalog-projection-v6"
    corpus["parent_corpus_reference"] = _exact_ref(source, "catalog_id")

    contracts = {
        record["component_contract_id"]: record
        for record in parent.records["component-contract"]
        if record["revision"] == 1
    }
    bindings = {
        record["implementation_id"]: record
        for record in parent.records["implementation-binding"]
        if record["revision"] == 2
        and record["implementation_id"]
        in {f"schuss-implementation-{number:06d}" for number, *_ in HOST_SPECS}
    }
    for number, role, display_name, _ in HOST_SPECS:
        implementation_id = f"schuss-implementation-{number:06d}"
        binding = bindings[implementation_id]
        contract = contracts[binding["contract_reference"]["component_contract_id"]]
        addition = {
            "implementation_id": implementation_id,
            "revision": 1,
            "content_hash": "sha256:" + "0" * 64,
            "family_reference": copy.deepcopy(contract["family_reference"]),
            "display_name": f"Schuss native {display_name}",
            "form": "native-cpp",
            "review_status": "task033-reviewed",
            "membership_confidence": "high",
            "membership_rationale": (
                "The accepted Task 031/032 host binding is a distinct Schuss-native "
                f"fixed-Q27 realization of the {role} component contract."
            ),
            "compatibility_status": "not-evaluated",
            "source_authority": {
                "kind": "schuss-native-core",
                "source_release_reference": _exact_ref(
                    schuss_release, "source_release_id"
                ),
                "evidence_ref": "fixture:task032-native-runtime",
                "provider_boundary": "static-native-provider",
            },
            "unresolved_questions": [
                "General real-time/resource, audible equivalence, Ksoloti equivalence, and distribution remain unproved."
            ],
        }
        addition["content_hash"] = _child_hash(addition)
        corpus["implementation_additions"].append(addition)
    corpus["implementation_additions"] = sorted(
        corpus["implementation_additions"], key=lambda item: item["implementation_id"]
    )
    corpus = _hash_record(corpus, schema)

    prior_selector = _exact(
        parent.records["catalog-selection"],
        "catalog_selection_id",
        "schuss-catalog-selection-000001",
        4,
    )
    selector = copy.deepcopy(prior_selector)
    selector["revision"] = 5
    selector["content_hash"] = "sha256:" + "0" * 64
    selector["corpus_reference"] = _exact_ref(corpus, "catalog_id")
    selector["rationale"] = (
        "Select the exact Task 033 Phase 2 catalog that preserves all Task 030 "
        "members and adds only seven accepted Schuss-native host companions."
    )
    selector = _hash_record(selector, selector_schema)
    return corpus, selector


def _availability_policy(
    schema: dict[str, Any],
    parent: record_set_rules.LoadedRecordSet,
    catalog: dict[str, Any],
) -> dict[str, Any]:
    host_target = _exact(
        parent.records["target"],
        "compute_target_id",
        "schuss-compute-target-000002",
        1,
    )
    host_backend = _exact(
        parent.records["backend"], "backend_id", "schuss-backend-000003", 1
    )
    ksoloti_target = _exact(
        parent.records["target"],
        "compute_target_id",
        "schuss-compute-target-000001",
        2,
    )
    ksoloti_backend = _exact(
        parent.records["backend"], "backend_id", "schuss-backend-000002", 4
    )
    record = {
        "schema_version": "implementation-availability-policy-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "implementation_availability_policy_id": "schuss-implementation-availability-policy-000001",
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "display_name": "Desktop Host and current direct-Ksoloti availability",
        "catalog_reference": _exact_ref(catalog, "catalog_id"),
        "reported_pairs": [
            {
                "pair_id": "availability-pair-000001",
                "display_name": "Desktop Host",
                "target_reference": _exact_ref(host_target, "compute_target_id"),
                "backend_reference": _exact_ref(host_backend, "backend_id"),
            },
            {
                "pair_id": "availability-pair-000002",
                "display_name": "Ksoloti Core",
                "target_reference": _exact_ref(ksoloti_target, "compute_target_id"),
                "backend_reference": _exact_ref(ksoloti_backend, "backend_id"),
            },
        ],
        "readiness_order": list(
            (
                "catalogued-only",
                "contracted",
                "bound",
                "eligible",
                "compile-proven",
                "device-tested",
                "real-time-tested",
                "audible-tested",
                "unresolved",
            )
        ),
        "selection_authority": False,
        "family_union_allowed": False,
        "source_presence_implies_support": False,
    }
    return _hash_record(record, schema)


def _provider(
    schema: dict[str, Any],
    parent: record_set_rules.LoadedRecordSet,
    catalog: dict[str, Any],
    schuss_release: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    host_pair = policy["reported_pairs"][0]
    bindings = {
        record["implementation_id"]: record
        for record in parent.records["implementation-binding"]
        if record["revision"] == 2
        and record["implementation_id"]
        in {f"schuss-implementation-{number:06d}" for number, *_ in HOST_SPECS}
    }
    eligibilities = {
        record["binding_reference"]["implementation_id"]: record
        for record in parent.records["eligibility"]
        if record["binding_reference"]["implementation_id"] in bindings
        and record["allowed_pair"]["target_reference"] == host_pair["target_reference"]
        and record["allowed_pair"]["backend_reference"] == host_pair["backend_reference"]
    }
    provider_bindings = []
    for index, (number, _, _, factory_id) in enumerate(HOST_SPECS, start=1):
        implementation_id = f"schuss-implementation-{number:06d}"
        binding = bindings[implementation_id]
        eligibility = eligibilities[implementation_id]
        provider_bindings.append(
            {
                "provider_binding_id": f"provider-binding-{index:06d}",
                "catalog_implementation_locator": {
                    "catalog_reference": _exact_ref(catalog, "catalog_id"),
                    "implementation_id": implementation_id,
                },
                "component_contract_reference": copy.deepcopy(
                    binding["contract_reference"]
                ),
                "implementation_binding_reference": _exact_ref(
                    binding, "implementation_id"
                ),
                "eligibility_reference": _exact_ref(
                    eligibility, "binding_eligibility_id"
                ),
                "target_reference": copy.deepcopy(host_pair["target_reference"]),
                "backend_reference": copy.deepcopy(host_pair["backend_reference"]),
                "runtime_factory_id": factory_id,
            }
        )
    record = {
        "schema_version": "implementation-provider-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "implementation_provider_id": "schuss-implementation-provider-000001",
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "display_name": "Schuss native fixed-Q27 core",
        "provider_kind": "statically-linked",
        "source_release_reference": _exact_ref(schuss_release, "source_release_id"),
        "provider_abi": "schuss-rt-abi-v1",
        "registry_version": "schuss-rt-factory-registry-v1",
        "target_backend_pairs": [
            {
                "target_reference": copy.deepcopy(host_pair["target_reference"]),
                "backend_reference": copy.deepcopy(host_pair["backend_reference"]),
            }
        ],
        "required_source_release_references": [
            _exact_ref(schuss_release, "source_release_id")
        ],
        "link_requirements": [],
        "callback_constraints": [
            "no-allocation",
            "no-filesystem",
            "no-locking",
            "no-network",
            "no-process-control",
        ],
        "license_boundary": {
            "private_development_status": "reviewed",
            "distribution_status": "review-required",
        },
        "bindings": provider_bindings,
        "selection_priority_owner": "binding-eligibility",
        "dynamic_loading": False,
    }
    return _hash_record(record, schema)


def _implementation_sources(
    overlay: dict[str, Any], corpus: dict[str, Any]
) -> dict[str, set[str]]:
    result = {
        item["implementation_id"]: {
            ref["source_id"] for ref in item["provenance_refs"]
        }
        for item in overlay["implementations"]
    }
    for item in corpus["implementation_additions"]:
        if "source_observation" in item:
            sources = {item["source_observation"]["source_id"]}
        else:
            authority = item["source_authority"]
            if authority["kind"] == "legacy-observation":
                sources = {authority["observation"]["source_id"]}
            elif authority["kind"] == "pinned-source-object":
                sources = {authority["source_id"]}
            elif authority["kind"] == "schuss-transparent-compound":
                sources = {"schuss"}
            elif authority["kind"] == "schuss-native-core":
                sources = {"schuss-native-core"}
            else:
                raise ValueError("unsupported catalog authority")
        result[item["implementation_id"]] = sources
    return result


def _collections(
    schema: dict[str, Any],
    catalog: dict[str, Any],
    releases: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    overlay = core.load_json(
        ROOT / "catalog/overlays/phase-4a-semantic-catalog-v0/catalog.json"
    )
    sources = _implementation_sources(overlay, catalog)
    first_party_sources = {"axoloti-factory", "ksoloti-objects", "patcher"}
    contributed_sources = {"axoloti-contrib", "ksoloti-contrib"}
    first_party = sorted(
        identifier
        for identifier, values in sources.items()
        if values & first_party_sources
    )
    contributed = sorted(
        identifier
        for identifier, values in sources.items()
        if values & contributed_sources
    )
    mutable = sorted(
        item["implementation_id"]
        for item in catalog["mutable_instruments_review"]["implementation_tags"]
        if item["tag_id"] == "mutable-instruments-derived"
    )
    host = [f"schuss-implementation-{number:06d}" for number, *_ in HOST_SPECS]
    release_by_number = {index: record for index, record in enumerate(releases, start=1)}
    specs = (
        (
            1,
            "Schuss Native Core",
            "The accepted statically linked JUCE-independent fixed-Q27 host implementations.",
            "core",
            (6,),
            host,
        ),
        (
            2,
            "Ksoloti First-party",
            "Exact catalog implementations whose provenance names a pinned first-party or patcher source release.",
            "first-party",
            (1, 2, 5),
            first_party,
        ),
        (
            3,
            "Ksoloti Contributed",
            "Exact catalog implementations whose provenance names a pinned contributed source release.",
            "contributed",
            (3, 4),
            contributed,
        ),
        (
            4,
            "Mutable-derived Audited Cohort",
            "The exact 56 catalog implementations carrying the reviewed Mutable-derived provenance facet.",
            "audited-provenance",
            (1, 5),
            mutable,
        ),
    )
    result = []
    for number, display_name, description, role, release_numbers, ids in specs:
        record = {
            "schema_version": "object-collection-v0",
            "canonical_profile": "schuss-canonical-json-v1",
            "object_collection_id": f"schuss-object-collection-{number:06d}",
            "revision": 1,
            "content_hash": "sha256:" + "0" * 64,
            "display_name": display_name,
            "description": description,
            "distribution_role": role,
            "catalog_reference": _exact_ref(catalog, "catalog_id"),
            "source_release_references": [
                _exact_ref(release_by_number[value], "source_release_id")
                for value in release_numbers
            ],
            "implementation_ids": ids,
            "membership_rule": "exact-catalog-reference-plus-implementation-id",
            "function_neutral": True,
            "target_promise": False,
            "project_identity_authority": False,
        }
        result.append(_hash_record(record, schema))
    return result


def _stable_id(record: Mapping[str, Any]) -> str:
    for field in (
        "catalog_id",
        "catalog_selection_id",
        "implementation_availability_policy_id",
        "implementation_provider_id",
        "object_collection_id",
        "source_release_id",
    ):
        if field in record:
            return str(record[field])
    raise ValueError("Task 033 Phase 2 record has no stable ID")


def generated() -> tuple[dict[str, bytes], bytes, dict[str, Any]]:
    corpus_schema, projection_schema = _catalog_schemas()
    profile_schema = _collection_profile_schema()
    request_schema, result_schema, application_schema = _operation_schemas(
        profile_schema
    )
    schemas = {
        "application-capability-description-v11": application_schema,
        "catalog-corpus-v6": corpus_schema,
        "catalog-projection-v6": projection_schema,
        "collection-profile-v0": profile_schema,
        "implementation-availability-policy-v0": _availability_policy_schema(),
        "implementation-provider-v0": _implementation_provider_schema(),
        "object-collection-v0": _object_collection_schema(),
        "operation-request-v18": request_schema,
        "operation-result-v18": result_schema,
        "source-release-v0": _source_release_schema(),
    }
    files = {
        f"schemas/{name}.schema.json": _canonical_bytes(schema)
        for name, schema in schemas.items()
    }

    parent = record_set_rules.load_record_set(ROOT, PARENT)
    if parent.reference != PARENT_REFERENCE:
        raise ValueError("Task 033 Phase 2 parent record set changed")
    releases = _source_releases(schemas["source-release-v0"])
    catalog, selector = _catalog_records(
        schemas["catalog-corpus-v6"],
        parent.schemas["catalog-selection-v0"],
        parent,
        releases[5],
    )
    policy = _availability_policy(
        schemas["implementation-availability-policy-v0"], parent, catalog
    )
    provider = _provider(
        schemas["implementation-provider-v0"],
        parent,
        catalog,
        releases[5],
        policy,
    )
    collections = _collections(
        schemas["object-collection-v0"], catalog, releases
    )
    records: list[tuple[str, str, dict[str, Any]]] = [
        ("catalog-corpus", "catalog-corpus-v6.json", catalog),
        ("catalog-selection", "catalog-selection-r5.json", selector),
        *(
            ("source-release", f"source-release-{index:02d}.json", record)
            for index, record in enumerate(releases, start=1)
        ),
        *(
            ("object-collection", f"object-collection-{index:02d}.json", record)
            for index, record in enumerate(collections, start=1)
        ),
        ("implementation-provider", "implementation-provider-01.json", provider),
        (
            "implementation-availability-policy",
            "implementation-availability-policy-01.json",
            policy,
        ),
    ]
    for _, filename, record in records:
        path = f"contracts/task033/phase2/{filename}"
        files[path] = _canonical_bytes(record)

    schema_members = copy.deepcopy(parent.manifest["schema_members"])
    existing_schemas = {member["schema_version"] for member in schema_members}
    for name in sorted(SCHEMA_NAMES):
        if name in existing_schemas:
            raise ValueError(f"Task 033 Phase 2 schema collides with parent: {name}")
        path = f"schemas/{name}.schema.json"
        schema_members.append(
            {
                "schema_version": name,
                "portable_path": path,
                "byte_sha256": _raw_sha256(files[path]),
            }
        )

    record_members = copy.deepcopy(parent.manifest["record_members"])
    for kind, filename, record in records:
        path = f"contracts/task033/phase2/{filename}"
        record_members.append(
            {
                "record_kind": kind,
                "stable_id": _stable_id(record),
                "revision": record["revision"],
                "content_hash": record["content_hash"],
                "portable_path": path,
                "byte_sha256": _raw_sha256(files[path]),
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
        "schema_members": sorted(
            schema_members,
            key=lambda item: (item["byte_sha256"], item["portable_path"]),
        ),
        "record_members": sorted(
            record_members,
            key=lambda item: (
                item["record_kind"],
                item["stable_id"],
                item["revision"],
                item["content_hash"],
            ),
        ),
        "enforced_directories": sorted(
            set(parent.manifest["enforced_directories"])
            | {"contracts/task033/phase2"}
        ),
    }
    errors = core.schema_errors(manifest, manifest_schema, manifest_schema)
    if errors:
        raise ValueError("; ".join(errors))
    manifest["content_hash"] = core.record_content_hash(manifest, manifest_schema)
    summary = {
        "schema_version": "task033-phase2-generation-summary-v1",
        "status": "valid",
        "record_set_reference": {
            key: manifest[key]
            for key in ("record_set_id", "revision", "content_hash")
        },
        "added_schema_versions": list(SCHEMA_NAMES),
        "source_release_count": len(releases),
        "collection_count": len(collections),
        "catalog_implementation_count": len(catalog["implementation_additions"]) + 38,
        "host_companion_count": len(HOST_SPECS),
        "provider_count": 1,
        "native_registry_modified": False,
        "ui_or_hardware_access_performed": False,
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
            if not destination.exists() or destination.read_bytes() != data:
                stale.append(relative)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_bytes() != manifest:
            stale.append(OUTPUT.relative_to(ROOT).as_posix())
        if stale:
            raise SystemExit("stale Task 033 Phase 2 generated files: " + ", ".join(stale))
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_bytes(manifest)
    print(core.canonical_json(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
