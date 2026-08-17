"""Deterministic Task 011A catalog projection and matching semantics.

The projection is rebuilt from exact semantic/evidence inputs.  It owns no
family, binding, compatibility, provenance, or readiness fact independently.
"""

from __future__ import annotations

import copy
import hashlib
import re
from typing import Any, Iterable, Mapping


PROJECTION_VERSION = "schuss-catalog-projection-v1"
MATCH_ALGORITHM = "schuss-catalog-match-v1"
READINESS_ORDER = (
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
FILTER_NAMES = (
    "function",
    "abstraction",
    "form",
    "signal_domain",
    "signal_rate",
    "signal_role",
    "capability",
    "technique",
    "readiness",
    "provenance",
)
ASCII_WHITESPACE_RE = re.compile(r"[ \t\n\r\f\v]+")


class CatalogProjectionError(ValueError):
    """The exact catalog input closure is stale, ambiguous, or invalid."""


def _ascii_casefold(value: str) -> str:
    return "".join(
        chr(ord(character) + 32) if "A" <= character <= "Z" else character
        for character in value
    )


def normalize_text(value: str) -> str:
    """Normalize only ASCII case and whitespace; preserve all other code points."""

    return _ascii_casefold(ASCII_WHITESPACE_RE.sub(" ", value).strip())


def canonical_filters(filters: Mapping[str, Iterable[str]]) -> dict[str, list[str]]:
    unknown = sorted(set(filters) - set(FILTER_NAMES))
    if unknown:
        raise CatalogProjectionError(f"unknown catalog filter kinds: {unknown}")
    return {
        name: sorted(
            {normalize_text(value) for value in filters.get(name, ()) if value != ""}
        )
        for name in FILTER_NAMES
    }


def _child_content_hash(value: dict[str, Any], core: Any) -> str:
    material = copy.deepcopy(value)
    material.pop("content_hash", None)
    return "sha256:" + hashlib.sha256(
        core.canonical_json(material).encode("utf-8")
    ).hexdigest()


def _generic_reference(record: dict[str, Any], id_field: str) -> dict[str, Any]:
    return {
        "stable_id": record[id_field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def _question_text(value: Any) -> str:
    if isinstance(value, dict):
        return f"{value.get('code', 'UNRESOLVED')}: {value.get('question', value)}"
    return str(value)


def _sorted_references(
    records: Iterable[tuple[dict[str, Any], str]], core: Any
) -> list[dict[str, Any]]:
    values = [_generic_reference(record, id_field) for record, id_field in records]
    return sorted(values, key=core.canonical_json)


def _source_for_evidence(
    evidence_ref: str, observations: Mapping[str, dict[str, Any]]
) -> str | None:
    observation = observations.get(evidence_ref)
    if observation is None:
        return None
    origin = observation.get("origin", {})
    source_id = origin.get("source_id")
    return source_id if isinstance(source_id, str) else None


def _validate_observation_source(
    source: dict[str, Any], observations: Mapping[str, dict[str, Any]], core: Any
) -> None:
    evidence_ref = source["evidence_ref"]
    observation = observations.get(evidence_ref)
    if observation is None:
        raise CatalogProjectionError(
            f"catalog source observation is absent: {evidence_ref}"
        )
    canonical_sha = hashlib.sha256(
        core.canonical_json(observation).encode("utf-8")
    ).hexdigest()
    origin = observation["origin"]
    expected = {
        "evidence_ref": evidence_ref,
        "canonical_observation_sha256": canonical_sha,
        "source_id": origin["source_id"],
        "source_path": origin["path"],
        "source_sha256": origin["sha256"],
        "legacy_id": observation["legacy_id"],
    }
    if "legacy_uuid_sha256" in source:
        expected["legacy_uuid_sha256"] = "sha256:" + hashlib.sha256(
            observation["uuid"]["durable_value"].encode("utf-8")
        ).hexdigest()
    else:
        expected["legacy_uuid"] = observation["uuid"]["durable_value"]
    if source != expected:
        raise CatalogProjectionError(
            f"catalog source observation closure is stale: {evidence_ref}"
        )


def _authority_values(
    value: dict[str, Any],
    observations: Mapping[str, dict[str, Any]],
    core: Any,
) -> tuple[list[str], set[str]]:
    """Validate and project either one legacy observation or Schuss design authority."""

    has_observation = "source_observation" in value
    has_authority = "source_authority" in value
    if has_observation == has_authority:
        raise CatalogProjectionError(
            "catalog addition must have exactly one source authority"
        )
    if has_observation:
        source = value["source_observation"]
        _validate_observation_source(source, observations, core)
        return [source["evidence_ref"]], {source["source_id"]}
    authority = value.get("source_authority")
    if not isinstance(authority, dict):
        raise CatalogProjectionError("catalog addition has no source authority")
    if authority["kind"] == "legacy-observation":
        source = authority["observation"]
        _validate_observation_source(source, observations, core)
        return [source["evidence_ref"]], {source["source_id"]}
    if authority["kind"] == "schuss-transparent-compound":
        return [authority["evidence_ref"]], {"schuss"}
    raise CatalogProjectionError("catalog addition source authority is unsupported")


def _validate_corpus(
    corpus: dict[str, Any],
    schema: dict[str, Any],
    overlay: dict[str, Any],
    overlay_sha256: str,
    observations: Mapping[str, dict[str, Any]],
    exact_families: Iterable[dict[str, Any]],
    core: Any,
) -> None:
    errors = core.schema_errors(corpus, schema, schema)
    if errors:
        raise CatalogProjectionError("catalog corpus schema invalid: " + "; ".join(errors))
    if core.record_content_hash(corpus, schema) != corpus["content_hash"]:
        raise CatalogProjectionError("catalog corpus content hash mismatch")
    source = corpus["overlay_source"]
    if (
        source["overlay_id"] != overlay["overlay_id"]
        or source["schema_version"] != overlay["schema_version"]
        or source["byte_sha256"] != overlay_sha256
        or source["legacy_manifest_sha256"]
        != overlay["legacy_evidence"]["manifest_sha256"]
    ):
        raise CatalogProjectionError("catalog overlay input closure is stale")

    overlay_families = {
        family["family_id"]: family for family in overlay["families"]
    }
    companion_ids: set[str] = set()
    for companion in corpus["family_companions"]:
        family_id = companion["family_id"]
        if family_id in companion_ids or family_id == "schuss-family-000018":
            raise CatalogProjectionError("catalog family companion identity is duplicated")
        companion_ids.add(family_id)
        source_family = overlay_families.get(family_id)
        if source_family is None:
            raise CatalogProjectionError(
                f"catalog family companion source is absent: {family_id}"
            )
        member_sha = hashlib.sha256(
            core.canonical_json(source_family).encode("utf-8")
        ).hexdigest()
        if companion["canonical_member_sha256"] != member_sha:
            raise CatalogProjectionError(
                f"catalog family companion member hash is stale: {family_id}"
            )
        if _child_content_hash(companion, core) != companion["content_hash"]:
            raise CatalogProjectionError(
                f"catalog family companion content hash is stale: {family_id}"
            )
        changed = companion["presentation_override"] is not None
        if changed != companion["semantics_changed"]:
            raise CatalogProjectionError(
                f"catalog family companion change declaration is inconsistent: {family_id}"
            )

    exact_family_registry = {
        family["family_id"]: family for family in exact_families
    }
    crossfader = exact_family_registry.get("schuss-family-000018")
    if crossfader is None:
        raise CatalogProjectionError("accepted Crossfader family companion is absent")
    if set(overlay_families) != companion_ids | {"schuss-family-000018"}:
        raise CatalogProjectionError(
            "catalog family companions do not cover the exact Phase 4A pilot"
        )

    additions: dict[str, dict[str, Any]] = {}
    for family in corpus["family_additions"]:
        if family["family_id"] in overlay_families or family["family_id"] in additions:
            raise CatalogProjectionError("catalog family addition identity collides")
        if _child_content_hash(family, core) != family["content_hash"]:
            raise CatalogProjectionError(
                f"catalog family addition content hash is stale: {family['family_id']}"
            )
        _authority_values(family, observations, core)
        additions[family["family_id"]] = family

    exact_refs = {
        companion["family_id"]: {
            "family_id": companion["family_id"],
            "revision": companion["revision"],
            "content_hash": companion["content_hash"],
        }
        for companion in corpus["family_companions"]
    }
    exact_refs["schuss-family-000018"] = {
        "family_id": crossfader["family_id"],
        "revision": crossfader["revision"],
        "content_hash": crossfader["content_hash"],
    }
    exact_refs.update(
        {
            family_id: {
                "family_id": family["family_id"],
                "revision": family["revision"],
                "content_hash": family["content_hash"],
            }
            for family_id, family in additions.items()
        }
    )
    implementation_ids: set[str] = set()
    implementation_family_ids: dict[str, str] = {}
    for implementation in corpus["implementation_additions"]:
        identifier = implementation["implementation_id"]
        if identifier in implementation_ids:
            raise CatalogProjectionError("catalog implementation identity is duplicated")
        implementation_ids.add(identifier)
        if _child_content_hash(implementation, core) != implementation["content_hash"]:
            raise CatalogProjectionError(
                f"catalog implementation content hash is stale: {identifier}"
            )
        family_id = implementation["family_reference"]["family_id"]
        implementation_family_ids[identifier] = family_id
        if implementation["family_reference"] != exact_refs.get(family_id):
            raise CatalogProjectionError(
                f"catalog implementation family reference is stale: {identifier}"
            )
        _authority_values(implementation, observations, core)
    if corpus["schema_version"] == "catalog-corpus-v1" and implementation_ids != {
        "schuss-implementation-000039",
        "schuss-implementation-000040",
        "schuss-implementation-000041",
    }:
        raise CatalogProjectionError("catalog implementation additions exceed slice scope")
    if corpus["schema_version"] == "catalog-corpus-v3":
        review = corpus.get("current_ksoloti_review")
        if not isinstance(review, dict):
            raise CatalogProjectionError("catalog v3 current-Ksoloti review is absent")
        expected_family_ids = {f"schuss-family-{value:06d}" for value in range(41, 61)}
        treatments = review["family_treatments"]
        treatment_ids = {
            item["family_reference"]["family_id"] for item in treatments
        }
        if treatment_ids != expected_family_ids or len(treatments) != 20:
            raise CatalogProjectionError(
                "catalog v3 current-Ksoloti family treatments do not cover IDs 41-60 exactly"
            )
        for treatment in treatments:
            family_id = treatment["family_reference"]["family_id"]
            if treatment["family_reference"] != exact_refs.get(family_id):
                raise CatalogProjectionError(
                    f"catalog v3 current-Ksoloti family reference is stale: {family_id}"
                )
            selected_ids = treatment["implementation_ids"]
            if len(selected_ids) != treatment["catalogued_variant_count"]:
                raise CatalogProjectionError(
                    f"catalog v3 current-Ksoloti implementation count is stale: {family_id}"
                )
            if treatment["catalogued_variant_count"] != treatment["candidate_variant_count"]:
                raise CatalogProjectionError(
                    f"catalog v3 current-Ksoloti variant cohort is incomplete: {family_id}"
                )
            if any(implementation_family_ids.get(identifier) != family_id for identifier in selected_ids):
                raise CatalogProjectionError(
                    f"catalog v3 current-Ksoloti implementation family is stale: {family_id}"
                )


def _evidence_for_binding(
    binding: dict[str, Any],
    records: Mapping[str, tuple[dict[str, Any], ...]],
    core: Any,
) -> tuple[
    list[dict[str, Any]],
    set[str],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    references: list[dict[str, Any]] = []
    states: set[str] = set()
    binding_key = (
        binding["implementation_id"],
        binding["revision"],
        binding["content_hash"],
    )
    selected_results = []
    for result in records.get("result", ()):
        for selected in result.get("selected_bindings", ()):
            reference = selected["binding_reference"]
            if (
                reference["implementation_id"],
                reference["revision"],
                reference["content_hash"],
            ) == binding_key:
                selected_results.append(result)
                break
    result_keys = {
        (result["build_result_id"], result["revision"], result["content_hash"])
        for result in selected_results
    }
    result_references = _sorted_references(
        ((result, "build_result_id") for result in selected_results), core
    )
    artifact_references = sorted(
        {
            core.canonical_json(reference): {
                "stable_id": reference["artifact_id"],
                "revision": reference["revision"],
                "content_hash": reference["content_hash"],
            }
            for result in selected_results
            for reference in result.get("artifact_references", ())
        }.values(),
        key=core.canonical_json,
    )
    for evidence in records.get("evidence", ()):
        subject = evidence.get("subject_reference", {})
        key = (
            subject.get("stable_id"),
            subject.get("revision"),
            subject.get("content_hash"),
        )
        if key not in result_keys or evidence.get("outcome") != "passed":
            continue
        references.append(_generic_reference(evidence, "evidence_claim_id"))
        level = evidence.get("level")
        if level == 5:
            states.add("compile-proven")
        elif level == 6:
            states.add("device-tested")
        elif level == 7:
            states.add("real-time-tested")
        elif level == 8:
            states.add("audible-tested")
    references.sort(key=core.canonical_json)
    return references, states, result_references, artifact_references


def build_catalog_projection(
    *,
    corpus: dict[str, Any],
    corpus_schema: dict[str, Any],
    projection_schema: dict[str, Any],
    overlay: dict[str, Any],
    overlay_sha256: str,
    observations: Mapping[str, dict[str, Any]],
    records: Mapping[str, tuple[dict[str, Any], ...]],
    record_set_reference: dict[str, Any],
    core: Any,
) -> dict[str, Any]:
    """Validate exact inputs and derive the complete client-neutral projection."""

    _validate_corpus(
        corpus,
        corpus_schema,
        overlay,
        overlay_sha256,
        observations,
        records.get("families", ()),
        core,
    )
    companion_by_id = {
        value["family_id"]: value for value in corpus["family_companions"]
    }
    exact_family_by_id = {
        value["family_id"]: value for value in records.get("families", ())
    }
    family_additions = {
        value["family_id"]: value for value in corpus["family_additions"]
    }
    implementation_additions = {
        value["implementation_id"]: value
        for value in corpus["implementation_additions"]
    }
    treatment_by_family = {
        value["family_reference"]["family_id"]: value
        for value in corpus.get("current_ksoloti_review", {}).get(
            "family_treatments", ()
        )
    }

    family_values: dict[str, dict[str, Any]] = {}
    family_refs: dict[str, dict[str, Any]] = {}
    for source in overlay["families"]:
        family = copy.deepcopy(source)
        companion = companion_by_id.get(family["family_id"])
        if companion is not None:
            override = companion["presentation_override"]
            if override is not None:
                family.update(copy.deepcopy(override))
            family_refs[family["family_id"]] = {
                "family_id": family["family_id"],
                "revision": companion["revision"],
                "content_hash": companion["content_hash"],
            }
        else:
            exact = exact_family_by_id[family["family_id"]]
            family_refs[family["family_id"]] = {
                "family_id": exact["family_id"],
                "revision": exact["revision"],
                "content_hash": exact["content_hash"],
            }
        family_values[family["family_id"]] = family
    for family_id, family in family_additions.items():
        family_values[family_id] = copy.deepcopy(family)
        family_refs[family_id] = {
            "family_id": family_id,
            "revision": family["revision"],
            "content_hash": family["content_hash"],
        }

    implementations: dict[str, dict[str, Any]] = {
        value["implementation_id"]: copy.deepcopy(value)
        for value in overlay["implementations"]
    }
    implementations.update(copy.deepcopy(implementation_additions))
    by_family: dict[str, list[dict[str, Any]]] = {}
    for implementation in implementations.values():
        family_id = implementation.get("family_id")
        if family_id is None:
            family_id = implementation["family_reference"]["family_id"]
        if family_id not in family_values:
            raise CatalogProjectionError(
                f"catalog implementation family is absent: {implementation['implementation_id']}"
            )
        by_family.setdefault(family_id, []).append(implementation)

    contracts_by_family: dict[str, list[dict[str, Any]]] = {}
    for contract in records.get("contracts", ()):
        contracts_by_family.setdefault(
            contract["family_reference"]["family_id"], []
        ).append(contract)
    bindings_by_implementation: dict[str, list[dict[str, Any]]] = {}
    for binding in records.get("bindings", ()):
        bindings_by_implementation.setdefault(
            binding["implementation_id"], []
        ).append(binding)
    eligibility_by_binding: dict[tuple[str, int, str], list[dict[str, Any]]] = {}
    for eligibility in records.get("eligibility", ()):
        reference = eligibility["binding_reference"]
        key = (
            reference["implementation_id"],
            reference["revision"],
            reference["content_hash"],
        )
        eligibility_by_binding.setdefault(key, []).append(eligibility)

    category_order = {
        value: index
        for index, value in enumerate(
            overlay["controlled_vocabulary"]["primary_categories"]
        )
    }
    entries: list[dict[str, Any]] = []
    for family_id, family in family_values.items():
        treatment = treatment_by_family.get(family_id)
        contracts = sorted(
            contracts_by_family.get(family_id, ()),
            key=core.canonical_json,
        )
        contract_refs = _sorted_references(
            ((contract, "component_contract_id") for contract in contracts), core
        )
        signal_facets = {
            (
                port["port_type"]["domain"],
                port["port_type"]["rate"],
                port["port_type"]["semantic_role"],
                port["port_type"]["channel_shape"]["count"],
            )
            for contract in contracts
            for port in contract.get("ports", ())
            if isinstance(port.get("port_type", {}).get("channel_shape", {}).get("count"), int)
        }
        contract_facet_names = {
            name
            for contract in contracts
            for collection in (
                "ports",
                "parameters",
                "attributes",
                "actions",
                "displays",
            )
            for facet in contract.get(collection, ())
            for name in (facet.get("semantic_key"), facet.get("display_label"))
            if isinstance(name, str) and name
        }
        capability_keys = {
            requirement["capability_key"]
            for contract in contracts
            for requirement in contract.get("capability_requirements", ())
        }
        implementation_summaries = []
        family_readiness: set[str] = set()
        family_unresolved: set[str] = {
            _question_text(item) for item in family.get("unresolved_questions", ())
        }
        provenance: set[str] = set()
        forms: set[str] = set()
        for implementation in sorted(
            by_family.get(family_id, ()),
            key=lambda value: value["implementation_id"],
        ):
            identifier = implementation["implementation_id"]
            addition = implementation_additions.get(identifier)
            if addition is None:
                exact_reference = None
                evidence_refs = list(implementation["legacy_evidence_refs"])
                sources = {
                    value["source_id"]
                    for value in implementation["provenance_refs"]
                }
                unresolved = {
                    _question_text(item)
                    for item in implementation.get("unresolved_questions", ())
                }
                if any(
                    value.get("status") == "not-evaluated"
                    for value in implementation.get("compatibility_evidence", ())
                ):
                    unresolved.add(
                        "Target/backend compatibility is not evaluated for the Phase 4A observation."
                    )
            else:
                exact_reference = _generic_reference(
                    addition, "implementation_id"
                )
                evidence_refs, sources = _authority_values(
                    addition, observations, core
                )
                unresolved = set(addition["unresolved_questions"])
            forms.add(implementation["form"])
            provenance.update(sources)
            bindings = sorted(
                bindings_by_implementation.get(identifier, ()),
                key=core.canonical_json,
            )
            binding_refs = _sorted_references(
                ((binding, "implementation_id") for binding in bindings), core
            )
            implementation_contracts = []
            eligibility_records = []
            evidence_records: list[dict[str, Any]] = []
            target_references: list[dict[str, Any]] = []
            backend_references: list[dict[str, Any]] = []
            result_references: list[dict[str, Any]] = []
            artifact_references: list[dict[str, Any]] = []
            readiness: set[str] = set()
            for binding in bindings:
                contract_reference = binding["contract_reference"]
                matching = [
                    contract
                    for contract in contracts
                    if contract["component_contract_id"]
                    == contract_reference["component_contract_id"]
                    and contract["revision"] == contract_reference["revision"]
                    and contract["content_hash"] == contract_reference["content_hash"]
                ]
                implementation_contracts.extend(matching)
                key = (
                    binding["implementation_id"],
                    binding["revision"],
                    binding["content_hash"],
                )
                for eligibility in eligibility_by_binding.get(key, ()):
                    eligibility_records.append(eligibility)
                    target = eligibility["allowed_pair"]["target_reference"]
                    target_references.append(
                        {
                            "stable_id": target["compute_target_id"],
                            "revision": target["revision"],
                            "content_hash": target["content_hash"],
                        }
                    )
                    backend = eligibility["allowed_pair"]["backend_reference"]
                    backend_references.append(
                        {
                            "stable_id": backend["backend_id"],
                            "revision": backend["revision"],
                            "content_hash": backend["content_hash"],
                        }
                    )
                    state = eligibility.get("allowed_pair", {}).get("state", {})
                    if state.get("status") == "supported":
                        readiness.add("eligible")
                    elif state.get("status") in {"unresolved", "not-evaluated"}:
                        unresolved.add(
                            f"Eligibility {eligibility['binding_eligibility_id']}@{eligibility['revision']} is {state.get('status')}."
                        )
                    for requirement in eligibility.get("capability_requirements", ()):
                        capability_keys.add(requirement["capability_key"])
                (
                    binding_evidence,
                    evidence_states,
                    binding_results,
                    binding_artifacts,
                ) = _evidence_for_binding(binding, records, core)
                evidence_records.extend(binding_evidence)
                result_references.extend(binding_results)
                artifact_references.extend(binding_artifacts)
                readiness.update(evidence_states)
            if implementation_contracts:
                readiness.add("contracted")
            if bindings:
                readiness.add("bound")
            if not implementation_contracts:
                readiness.add("catalogued-only")
            if unresolved:
                readiness.add("unresolved")
            family_readiness.update(readiness)
            family_unresolved.update(unresolved)
            implementation_summaries.append(
                {
                    "implementation_id": identifier,
                    "exact_reference": exact_reference,
                    "display_name": implementation["display_name"],
                    "form": implementation["form"],
                    "provenance_sources": sorted(sources),
                    "observation_references": sorted(evidence_refs),
                    "contract_references": _sorted_references(
                        (
                            (contract, "component_contract_id")
                            for contract in {
                                (
                                    value["component_contract_id"],
                                    value["revision"],
                                    value["content_hash"],
                                ): value
                                for value in implementation_contracts
                            }.values()
                        ),
                        core,
                    ),
                    "binding_references": binding_refs,
                    "eligibility_references": _sorted_references(
                        (
                            (eligibility, "binding_eligibility_id")
                            for eligibility in eligibility_records
                        ),
                        core,
                    ),
                    "target_references": sorted(
                        {
                            core.canonical_json(value): value
                            for value in target_references
                        }.values(),
                        key=core.canonical_json,
                    ),
                    "backend_references": sorted(
                        {
                            core.canonical_json(value): value
                            for value in backend_references
                        }.values(),
                        key=core.canonical_json,
                    ),
                    "result_references": sorted(
                        {
                            core.canonical_json(value): value
                            for value in result_references
                        }.values(),
                        key=core.canonical_json,
                    ),
                    "artifact_references": sorted(
                        {
                            core.canonical_json(value): value
                            for value in artifact_references
                        }.values(),
                        key=core.canonical_json,
                    ),
                    "evidence_references": sorted(
                        {
                            core.canonical_json(value): value
                            for value in evidence_records
                        }.values(),
                        key=core.canonical_json,
                    ),
                    "readiness_states": [
                        state for state in READINESS_ORDER if state in readiness
                    ],
                    "unresolved_facts": sorted(unresolved),
                }
            )
        entry = {
            "family_reference": family_refs[family_id],
            "display_name": family["display_name"],
            "aliases": sorted(family["aliases"]),
            "description": family["description"],
            "primary_function": family["primary_category"],
            "technique_tags": sorted(family["secondary_function_tags"]),
            "abstraction_level": family["abstraction_level"],
            "implementation_forms": sorted(forms),
            "signal_facets": [
                {
                    "domain": domain,
                    "rate": rate,
                    "role": role,
                    "channel_count": channels,
                }
                for domain, rate, role, channels in sorted(signal_facets)
            ],
            "contract_facet_names": sorted(contract_facet_names),
            "capability_keys": sorted(capability_keys),
            "provenance_facets": sorted(provenance),
            "readiness_states": [
                state for state in READINESS_ORDER if state in family_readiness
            ],
            "contract_facets_available": bool(contract_refs),
            "implementations": implementation_summaries,
            "unresolved_facts": sorted(family_unresolved),
        }
        if corpus["schema_version"] == "catalog-corpus-v3":
            entry.update(
                {
                    "curation_treatment": (
                        treatment["treatment"] if treatment is not None else "accepted"
                    ),
                    "drawer_visibility": (
                        treatment["drawer_visibility"] if treatment is not None else "default"
                    ),
                    "current_ksoloti_base_refs": (
                        copy.deepcopy(treatment["current_base_refs"])
                        if treatment is not None
                        else []
                    ),
                    "current_variant_coverage": {
                        "candidate_variant_count": (
                            treatment["candidate_variant_count"] if treatment is not None else 0
                        ),
                        "catalogued_variant_count": (
                            treatment["catalogued_variant_count"] if treatment is not None else 0
                        ),
                    },
                }
            )
        entries.append(entry)
    entries.sort(
        key=lambda entry: (
            category_order.get(entry["primary_function"], len(category_order)),
            normalize_text(entry["display_name"]).encode("utf-8"),
            entry["family_reference"]["family_id"],
            entry["family_reference"]["revision"],
            entry["family_reference"]["content_hash"],
        )
    )
    closure_material = {
        "record_set_reference": record_set_reference,
        "catalog_reference": {
            "catalog_id": corpus["catalog_id"],
            "revision": corpus["revision"],
            "content_hash": corpus["content_hash"],
        },
        "overlay_sha256": overlay_sha256,
        "semantic_records": {
            group: [
                record.get("content_hash", core.canonical_json(record))
                for record in records.get(group, ())
            ]
            for group in sorted(records)
            if group != "selection_packets"
        },
    }
    projection = {
        "schema_version": projection_schema["properties"]["schema_version"]["const"],
        "canonical_profile": "schuss-canonical-json-v1",
        "projection_version": projection_schema["properties"]["projection_version"]["const"],
        "match_algorithm": MATCH_ALGORITHM,
        "input_closure_hash": "sha256:"
        + hashlib.sha256(
            core.canonical_json(closure_material).encode("utf-8")
        ).hexdigest(),
        "record_set_reference": copy.deepcopy(record_set_reference),
        "catalog_reference": {
            "catalog_id": corpus["catalog_id"],
            "revision": corpus["revision"],
            "content_hash": corpus["content_hash"],
        },
        "families": entries,
    }
    errors = core.schema_errors(projection, projection_schema, projection_schema)
    if errors:
        raise CatalogProjectionError(
            "derived catalog projection violates its schema: " + "; ".join(errors)
        )
    return projection


def _indexed_fields(entry: dict[str, Any]) -> list[str]:
    fields = [
        entry["display_name"],
        entry["family_reference"]["family_id"],
        entry["description"],
        *entry["aliases"],
        *entry["technique_tags"],
        *entry["contract_facet_names"],
    ]
    for implementation in entry["implementations"]:
        fields.append(implementation["display_name"])
    for signal in entry["signal_facets"]:
        fields.extend(
            [signal["domain"], signal["rate"], signal["role"]]
        )
    return [normalize_text(value) for value in fields]


def _score_entry(entry: dict[str, Any], tokens: list[str]) -> int | None:
    fields = _indexed_fields(entry)
    score = 0
    for token in tokens:
        matches = []
        for field in fields:
            if token == field:
                matches.append(300)
            elif field.startswith(token):
                matches.append(200)
            elif token in field:
                matches.append(100)
        if not matches:
            return None
        score += max(matches)
    return score


def _facet_values(entry: dict[str, Any], name: str) -> set[str]:
    mapping = {
        "function": {entry["primary_function"]},
        "abstraction": {entry["abstraction_level"]},
        "form": set(entry["implementation_forms"]),
        "signal_domain": {item["domain"] for item in entry["signal_facets"]},
        "signal_rate": {item["rate"] for item in entry["signal_facets"]},
        "signal_role": {item["role"] for item in entry["signal_facets"]},
        "capability": set(entry["capability_keys"]),
        "technique": set(entry["technique_tags"]),
        "readiness": set(entry["readiness_states"]),
        "provenance": set(entry["provenance_facets"]),
    }
    return {normalize_text(value) for value in mapping[name]}


def validate_filter_values(
    projection: dict[str, Any], filters: dict[str, list[str]]
) -> list[tuple[str, str]]:
    invalid = []
    for name, requested in filters.items():
        available = {
            value
            for entry in projection["families"]
            for value in _facet_values(entry, name)
        }
        for value in requested:
            if value not in available:
                invalid.append((name, value))
    return sorted(invalid)


def search_catalog(
    projection: dict[str, Any],
    query: str,
    filters: Mapping[str, Iterable[str]],
) -> tuple[str, dict[str, list[str]], list[dict[str, Any]]]:
    normalized_query = normalize_text(query)
    tokens = normalized_query.split(" ") if normalized_query else []
    normalized_filters = canonical_filters(filters)
    scored = []
    for entry in projection["families"]:
        if any(
            requested
            and not (_facet_values(entry, name) & set(requested))
            for name, requested in normalized_filters.items()
        ):
            continue
        score = _score_entry(entry, tokens)
        if score is None:
            continue
        scored.append((score, entry))
    category_order = {}
    for entry in projection["families"]:
        category_order.setdefault(entry["primary_function"], len(category_order))
    scored.sort(
        key=lambda item: (
            -item[0],
            category_order[item[1]["primary_function"]],
            normalize_text(item[1]["display_name"]).encode("utf-8"),
            item[1]["family_reference"]["family_id"],
            item[1]["family_reference"]["revision"],
            item[1]["family_reference"]["content_hash"],
        )
    )
    summaries = [
        {
            "family_reference": copy.deepcopy(entry["family_reference"]),
            "display_name": entry["display_name"],
            "aliases": copy.deepcopy(entry["aliases"]),
            "description": entry["description"],
            "primary_function": entry["primary_function"],
            "technique_tags": copy.deepcopy(entry["technique_tags"]),
            "abstraction_level": entry["abstraction_level"],
            "implementation_forms": copy.deepcopy(entry["implementation_forms"]),
            "readiness_states": copy.deepcopy(entry["readiness_states"]),
            "contract_facets_available": entry["contract_facets_available"],
            "provenance_facets": copy.deepcopy(entry["provenance_facets"]),
            "score": score,
        }
        for score, entry in scored
    ]
    for summary, (_, entry) in zip(summaries, scored):
        if "curation_treatment" in entry:
            summary.update(
                {
                    "curation_treatment": entry["curation_treatment"],
                    "drawer_visibility": entry["drawer_visibility"],
                    "current_ksoloti_base_refs": copy.deepcopy(
                        entry["current_ksoloti_base_refs"]
                    ),
                    "current_variant_coverage": copy.deepcopy(
                        entry["current_variant_coverage"]
                    ),
                }
            )
    return normalized_query, normalized_filters, summaries


def inspect_family(
    projection: dict[str, Any], family_reference: dict[str, Any]
) -> dict[str, Any] | None:
    matches = [
        entry
        for entry in projection["families"]
        if entry["family_reference"] == family_reference
    ]
    return copy.deepcopy(matches[0]) if len(matches) == 1 else None
