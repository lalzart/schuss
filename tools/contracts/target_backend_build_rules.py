#!/usr/bin/env python3
"""Target, backend, build, artifact, resource, and evidence domain rules."""

from __future__ import annotations

import hashlib
import re
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import validator_core as core

# Retain the historic local name while binding it only to shared mechanisms.
base = core


SCHEMA_SPECS = {
    "capability": ("capability-vocabulary-v0.schema.json", "capability-vocabulary-v0", "capability_vocabulary_id", "capabilities"),
    "environment": ("build-environment-v0.schema.json", "build-environment-v0", "build_environment_id", "build-environments"),
    "target": ("compute-target-v0.schema.json", "compute-target-v0", "compute_target_id", "compute-targets"),
    "backend": ("backend-v0.schema.json", "backend-v0", "backend_id", "backends"),
    "eligibility": ("binding-eligibility-v0.schema.json", "binding-eligibility-v0", "binding_eligibility_id", "binding-eligibility"),
    "request": ("build-request-v0.schema.json", "build-request-v0", "build_request_id", "build-requests"),
    "result": ("build-result-v0.schema.json", "build-result-v0", "build_result_id", "build-results"),
    "artifact": ("artifact-descriptor-v0.schema.json", "artifact-descriptor-v0", "artifact_id", "artifacts"),
    "resource": ("resource-report-v0.schema.json", "resource-report-v0", "resource_report_id", "resource-reports"),
    "evidence": ("evidence-claim-v0.schema.json", "evidence-claim-v0", "evidence_claim_id", "evidence-claims"),
}

STAGES = (
    "schema-identity-validation",
    "target-independent-graph-validation",
    "target-backend-validation",
    "implementation-resolution",
    "compound-elaboration",
    "dependency-resource-planning",
    "backend-lowering",
    "artifact-generation",
    "target-compile-link",
    "packaging-evidence-recording",
)

EVIDENCE_LEVEL_NAMES = {
    1: "structural-schema-validation",
    2: "component-graph-resolution",
    3: "backend-lowering",
    4: "source-artifact-generation",
    5: "arm-compilation-linking",
    6: "connected-device-execution",
    7: "real-time-resource-validation",
    8: "audible-listening-validation",
}

@dataclass(frozen=True)
class Task007Validation:
    summary: dict[str, Any]
    resolution_traces: tuple[dict[str, Any], ...]
    diagnostics: tuple[base.Diagnostic, ...]


def _diagnostic(
    diagnostics: list[base.Diagnostic],
    code: str,
    subject: str,
    location: str,
    message: str,
) -> None:
    diagnostics.append(base.Diagnostic(code, "error", subject, location, message))


def _subject(record: dict[str, Any]) -> str:
    for _, (_, _, id_field, _) in SCHEMA_SPECS.items():
        if id_field in record:
            return f"{record.get(id_field, '<unknown>')}@{record.get('revision', '?')}"
    return core.record_subject(record)


def _exact(record: dict[str, Any], id_field: str) -> tuple[str, int, str]:
    return record[id_field], record["revision"], record["content_hash"]


def _ref(reference: dict[str, Any], id_field: str) -> tuple[str, int, str]:
    return reference[id_field], reference["revision"], reference["content_hash"]


def _record_files(root: Path, child: str) -> list[Path]:
    return sorted(path for path in (root / child).glob("*.json") if path.is_file())


def _schemas(schema_root: Path) -> dict[str, dict[str, Any]]:
    return {
        kind: base.load_json(schema_root / spec[0])
        for kind, spec in SCHEMA_SPECS.items()
    }


def _records(contract_root: Path) -> dict[str, list[dict[str, Any]]]:
    return {
        kind: [base.load_json(path) for path in _record_files(contract_root, spec[3])]
        for kind, spec in SCHEMA_SPECS.items()
    }


def _validate_structural(
    records: dict[str, list[dict[str, Any]]],
    schemas: dict[str, dict[str, Any]],
    diagnostics: list[base.Diagnostic],
) -> dict[str, list[dict[str, Any]]]:
    valid: dict[str, list[dict[str, Any]]] = {}
    for kind, values in records.items():
        schema_name, schema_version, id_field, _ = SCHEMA_SPECS[kind]
        candidates = core.validate_structural_records(
            values,
            schemas[kind],
            schema_name,
            schema_version,
            id_field,
            diagnostics,
        )
        valid[kind] = []
        for record in candidates:
            maximum_errors = _schema_maximum_errors(record, schemas[kind], schemas[kind])
            for error in maximum_errors:
                _diagnostic(diagnostics, "SCHEMA_STRUCTURE_INVALID", _subject(record), "$", error)
            if not maximum_errors:
                valid[kind].append(record)
    return valid


def _schema_maximum_errors(
    value: Any,
    schema: dict[str, Any],
    root_schema: dict[str, Any],
    location: str = "$",
) -> list[str]:
    """Close the numeric-maximum gap in the inherited restricted validator."""
    schema = core.resolve_schema(schema, root_schema)
    if "oneOf" in schema:
        matches = [branch for branch in schema["oneOf"] if not core.schema_errors(value, branch, root_schema, location)]
        if len(matches) == 1:
            return _schema_maximum_errors(value, matches[0], root_schema, location)
        return []
    errors: list[str] = []
    if isinstance(value, int) and not isinstance(value, bool) and "maximum" in schema and value > schema["maximum"]:
        errors.append(f"{location}: value is above maximum {schema['maximum']}")
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        for key, item in value.items():
            if key in properties:
                errors.extend(_schema_maximum_errors(item, properties[key], root_schema, f"{location}.{key}"))
    if isinstance(value, list) and "items" in schema:
        for index, item in enumerate(value):
            errors.extend(_schema_maximum_errors(item, schema["items"], root_schema, f"{location}[{index}]"))
    return errors


def _source_lock_entries(source_lock: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in source_lock["sources"]}


def _local_sources(repository_root: Path) -> dict[str, Path]:
    path = repository_root / "catalog/sources.local.yml"
    if not path.is_file():
        return {}
    result: dict[str, Path] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^  ([a-z0-9-]+):\s+(.+?)\s*$", line)
        if match:
            result[match.group(1)] = Path(match.group(2))
    return result


def _walk_source_evidence(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        if {"source_id", "commit", "path", "byte_sha256", "claim_kind"} <= set(value):
            yield value
        for item in value.values():
            yield from _walk_source_evidence(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_source_evidence(item)


def _verify_source_evidence(
    values: Iterable[dict[str, Any]],
    source_lock: dict[str, Any],
    local_sources: dict[str, Path],
    diagnostics: list[base.Diagnostic],
) -> tuple[int, int]:
    locked = _source_lock_entries(source_lock)
    unique = {
        base.canonical_json(item): item
        for value in values
        for item in _walk_source_evidence(value)
    }
    local_verified = 0
    for encoded in sorted(unique):
        evidence = unique[encoded]
        subject = f"source:{evidence['source_id']}@{evidence['commit']}:{evidence['path']}"
        lock = locked.get(evidence["source_id"])
        if lock is None or lock["commit"] != evidence["commit"]:
            _diagnostic(
                diagnostics,
                "SOURCE_EVIDENCE_LOCK_MISMATCH",
                subject,
                "$",
                "portable source evidence is absent from or stale against the source lock",
            )
            continue
        checkout = local_sources.get(evidence["source_id"])
        if checkout is None:
            continue
        completed = subprocess.run(
            ["git", "-C", str(checkout), "show", f"{evidence['commit']}:{evidence['path']}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode != 0:
            _diagnostic(
                diagnostics,
                "SOURCE_EVIDENCE_UNRESOLVED",
                subject,
                "$",
                "the exact pinned source path could not be read from the configured checkout",
            )
            continue
        actual = hashlib.sha256(completed.stdout).hexdigest()
        if actual != evidence["byte_sha256"]:
            _diagnostic(
                diagnostics,
                "SOURCE_EVIDENCE_HASH_MISMATCH",
                subject,
                "$.byte_sha256",
                f"expected {actual}",
            )
            continue
        local_verified += 1
    return len(unique), local_verified


def _registry(records: Iterable[dict[str, Any]], id_field: str) -> dict[tuple[str, int, str], dict[str, Any]]:
    return {_exact(item, id_field): item for item in records}


def _power_of_two(value: int) -> bool:
    return value > 0 and value & (value - 1) == 0


def _capability_definitions(
    vocabularies: list[dict[str, Any]], diagnostics: list[base.Diagnostic]
) -> tuple[dict[tuple[str, int, str], dict[str, Any]], dict[str, dict[str, Any]]]:
    registry = _registry(vocabularies, "capability_vocabulary_id")
    definitions: dict[str, dict[str, Any]] = {}
    for record in vocabularies:
        subject = _subject(record)
        for definition in record["definitions"]:
            key = definition["key"]
            if key in definitions:
                _diagnostic(diagnostics, "CAPABILITY_KEY_DUPLICATE", subject, "$.definitions", f"capability {key!r} is duplicated")
            definitions[key] = definition
            if definition["value_kind"] == "boolean" and (
                definition["unit"] != "none" or definition["comparison_rule"] != "exact"
            ):
                _diagnostic(diagnostics, "CAPABILITY_VALUE_SHAPE_INVALID", subject, "$.definitions", "boolean capabilities require unit none and exact comparison")
            if not definition["unknown_blocks_eligibility"]:
                _diagnostic(diagnostics, "CAPABILITY_UNKNOWN_POLICY_INVALID", subject, "$.definitions", "v0 eligibility-critical capabilities must fail closed on unknown")
    return registry, definitions


def _value_kind_matches(value: Any, kind: str) -> bool:
    if kind == "boolean":
        return isinstance(value, bool)
    return isinstance(value, int) and not isinstance(value, bool)


def _compare_capability(actual: Any, expected: Any, rule: str) -> bool:
    if rule == "exact":
        return actual == expected
    if not isinstance(actual, int) or isinstance(actual, bool) or not isinstance(expected, int) or isinstance(expected, bool):
        return False
    return actual >= expected if rule == "at-least" else actual <= expected


def _validate_environments(
    environments: list[dict[str, Any]], diagnostics: list[base.Diagnostic]
) -> dict[tuple[str, int, str], dict[str, Any]]:
    registry = _registry(environments, "build_environment_id")
    for record in environments:
        subject = _subject(record)
        identity = record["identity"]
        if identity["status"] == "supported":
            components = [item["component"] for item in identity["component_hashes"]]
            if len(components) != len(set(components)):
                _diagnostic(diagnostics, "BUILD_ENVIRONMENT_COMPONENT_DUPLICATE", subject, "$.identity.component_hashes", "component identities must be unique")
            if identity["portable_locator"] != f"sha256/{identity['component_hashes'][0]['sha256']}":
                _diagnostic(diagnostics, "BUILD_ENVIRONMENT_LOCATOR_MISMATCH", subject, "$.identity.portable_locator", "v0 portable locator must name the first declared identity component")
    return registry


def _validate_targets(
    targets: list[dict[str, Any]],
    capability_registry: dict[tuple[str, int, str], dict[str, Any]],
    definitions: dict[str, dict[str, Any]],
    environments: dict[tuple[str, int, str], dict[str, Any]],
    diagnostics: list[base.Diagnostic],
) -> dict[tuple[str, int, str], dict[str, Any]]:
    registry = _registry(targets, "compute_target_id")
    for target in targets:
        subject = _subject(target)
        if not target["processor"]["evidence_refs"] or not target["abi_constraints"]["evidence_refs"]:
            _diagnostic(diagnostics, "TARGET_FACT_EVIDENCE_MISSING", subject, "$", "processor and ABI facts require exact pinned evidence")
        endianness = target["abi_constraints"]["endianness"]
        if endianness["status"] == "supported" and not endianness["evidence_refs"]:
            _diagnostic(diagnostics, "TARGET_ABI_EVIDENCE_MISSING", subject, "$.abi_constraints.endianness", "a positive endianness fact requires exact evidence")
        if _ref(target["capability_vocabulary_reference"], "capability_vocabulary_id") not in capability_registry:
            _diagnostic(diagnostics, "CAPABILITY_VOCABULARY_REFERENCE_UNRESOLVED", subject, "$.capability_vocabulary_reference", "exact capability vocabulary did not resolve")
        runtime_key = _ref(target["firmware_runtime_reference"], "build_environment_id")
        runtime = environments.get(runtime_key)
        if runtime is None or runtime["environment_kind"] != "firmware-runtime-abi":
            _diagnostic(diagnostics, "FIRMWARE_RUNTIME_REFERENCE_UNRESOLVED", subject, "$.firmware_runtime_reference", "exact firmware/runtime identity did not resolve")

        runtime_keys = [item["key"] for item in target["runtime_assumptions"]]
        if len(runtime_keys) != len(set(runtime_keys)):
            _diagnostic(diagnostics, "TARGET_RUNTIME_ASSUMPTION_DUPLICATE", subject, "$.runtime_assumptions", "runtime assumption keys must be unique")
        expected_units = {"audio-sample-rate": "hertz", "audio-block-frames": "frames"}
        for item in target["runtime_assumptions"]:
            if item["unit"] != expected_units[item["key"]] or not item["evidence_refs"]:
                _diagnostic(diagnostics, "TARGET_RUNTIME_ASSUMPTION_INVALID", subject, "$.runtime_assumptions", "runtime constant unit or evidence is invalid")

        regions: dict[str, dict[str, Any]] = {}
        intervals: list[tuple[int, int, str]] = []
        for region in target["memory_regions"]:
            region_id = region["region_id"]
            if region_id in regions:
                _diagnostic(diagnostics, "TARGET_MEMORY_REGION_DUPLICATE", subject, "$.memory_regions", f"region {region_id!r} is duplicated")
            regions[region_id] = region
            start = int(region["address_start"], 16)
            end = start + region["length_bytes"]
            if not _power_of_two(region["alignment_bytes"]) or start % region["alignment_bytes"]:
                _diagnostic(diagnostics, "TARGET_MEMORY_REGION_ALIGNMENT_INVALID", subject, "$.memory_regions", f"region {region_id!r} has invalid alignment")
            if end > 0x1_0000_0000:
                _diagnostic(diagnostics, "TARGET_MEMORY_REGION_BOUNDS_INVALID", subject, "$.memory_regions", f"region {region_id!r} exceeds the 32-bit address space")
            if not region["evidence_refs"]:
                _diagnostic(diagnostics, "TARGET_FACT_EVIDENCE_MISSING", subject, "$.memory_regions", f"region {region_id!r} lacks exact evidence")
            intervals.append((start, end, region_id))
        for index, first in enumerate(sorted(intervals)):
            for second in sorted(intervals)[index + 1:]:
                if second[0] < first[1] and first[0] < second[1]:
                    _diagnostic(diagnostics, "TARGET_MEMORY_REGION_OVERLAP", subject, "$.memory_regions", f"regions {first[2]!r} and {second[2]!r} overlap")

        declared: set[str] = set()
        for declaration in target["capability_declarations"]:
            key = declaration["capability_key"]
            definition = definitions.get(key)
            if key in declared:
                _diagnostic(diagnostics, "CAPABILITY_DECLARATION_DUPLICATE", subject, "$.capability_declarations", f"capability {key!r} is duplicated")
            declared.add(key)
            if definition is None:
                _diagnostic(diagnostics, "CAPABILITY_UNKNOWN", subject, "$.capability_declarations", f"capability {key!r} is undefined")
                continue
            if "compute-target" not in definition["declaration_subject_kinds"]:
                _diagnostic(diagnostics, "CAPABILITY_DECLARATION_SUBJECT_INVALID", subject, "$.capability_declarations", f"capability {key!r} cannot be declared by a target")
            state = declaration["state"]
            if state["status"] in {"supported", "unsupported"}:
                if not _value_kind_matches(state["value"], definition["value_kind"]):
                    _diagnostic(diagnostics, "CAPABILITY_VALUE_TYPE_INVALID", subject, "$.capability_declarations", f"capability {key!r} has the wrong value type")
                if state["status"] == "supported" and (
                    state["evidence_level"] < definition["required_evidence_level"] or not state["evidence_refs"]
                ):
                    _diagnostic(diagnostics, "CAPABILITY_EVIDENCE_INSUFFICIENT", subject, "$.capability_declarations", f"capability {key!r} lacks its required evidence")
        for limit in target["asset_storage_limits"]:
            region = regions.get(limit["region_id"])
            if region is None or "asset" not in region["resource_kinds"] or limit["maximum_bytes"] > region["length_bytes"]:
                _diagnostic(diagnostics, "TARGET_ASSET_LIMIT_INVALID", subject, "$.asset_storage_limits", "asset limit is absent from or exceeds its exact region")
    return registry


def _requirement_semantics(
    requirement: dict[str, Any],
    subject_kind: str,
    definitions: dict[str, dict[str, Any]],
    subject: str,
    location: str,
    diagnostics: list[base.Diagnostic],
) -> None:
    key = requirement["capability_key"]
    definition = definitions.get(key)
    if definition is None:
        _diagnostic(diagnostics, "CAPABILITY_UNKNOWN", subject, location, f"capability {key!r} is undefined")
        return
    if subject_kind not in definition["requirement_subject_kinds"]:
        _diagnostic(diagnostics, "CAPABILITY_REQUIREMENT_SUBJECT_INVALID", subject, location, f"capability {key!r} cannot be required by {subject_kind}")
    if not _value_kind_matches(requirement["value"], definition["value_kind"]):
        _diagnostic(diagnostics, "CAPABILITY_VALUE_TYPE_INVALID", subject, location, f"capability {key!r} has the wrong value type")
    if requirement["comparison_rule"] != definition["comparison_rule"]:
        _diagnostic(diagnostics, "CAPABILITY_COMPARISON_RULE_INVALID", subject, location, f"capability {key!r} must use the vocabulary comparison rule")


def _validate_backends(
    backends: list[dict[str, Any]],
    capability_registry: dict[tuple[str, int, str], dict[str, Any]],
    definitions: dict[str, dict[str, Any]],
    targets: dict[tuple[str, int, str], dict[str, Any]],
    environments: dict[tuple[str, int, str], dict[str, Any]],
    diagnostics: list[base.Diagnostic],
) -> dict[tuple[str, int, str], dict[str, Any]]:
    registry = _registry(backends, "backend_id")
    for backend in backends:
        subject = _subject(backend)
        if _ref(backend["capability_vocabulary_reference"], "capability_vocabulary_id") not in capability_registry:
            _diagnostic(diagnostics, "CAPABILITY_VOCABULARY_REFERENCE_UNRESOLVED", subject, "$.capability_vocabulary_reference", "exact capability vocabulary did not resolve")
        for field, expected_kind in (("toolchain_reference", "toolchain"), ("firmware_runtime_reference", "firmware-runtime-abi")):
            environment = environments.get(_ref(backend[field], "build_environment_id"))
            if environment is None or environment["environment_kind"] != expected_kind:
                _diagnostic(diagnostics, "BACKEND_ENVIRONMENT_REFERENCE_UNRESOLVED", subject, f"$.{field}", f"exact {expected_kind} identity did not resolve")

        requirements = backend["required_target_capabilities"]
        keys = [item["capability_key"] for item in requirements]
        if len(keys) != len(set(keys)):
            _diagnostic(diagnostics, "BACKEND_CAPABILITY_REQUIREMENT_DUPLICATE", subject, "$.required_target_capabilities", "backend capability requirements must be unique")
        for index, requirement in enumerate(requirements):
            _requirement_semantics(requirement, "backend", definitions, subject, f"$.required_target_capabilities[{index}]", diagnostics)

        pair_keys: set[tuple[str, int, str]] = set()
        for pairing in backend["target_pairings"]:
            key = _ref(pairing["target_reference"], "compute_target_id")
            if key not in targets:
                _diagnostic(diagnostics, "BACKEND_TARGET_PAIRING_UNRESOLVED", subject, "$.target_pairings", "declared exact target pairing did not resolve")
            if key in pair_keys:
                _diagnostic(diagnostics, "BACKEND_TARGET_PAIRING_DUPLICATE", subject, "$.target_pairings", "target pairings must be unique")
            pair_keys.add(key)

        stages = backend["stage_contract"]
        actual = [(item["ordinal"], item["stage"]) for item in stages]
        expected = list(enumerate(STAGES, 1))
        if actual != expected:
            _diagnostic(diagnostics, "BACKEND_STAGE_ORDER_INVALID", subject, "$.stage_contract", "backend stages must be the complete fixed sequence")
        declared_artifacts: set[str] = set()
        for artifact in backend["artifact_declarations"]:
            kind = artifact["artifact_kind"]
            if kind in declared_artifacts:
                _diagnostic(diagnostics, "BACKEND_ARTIFACT_DUPLICATE", subject, "$.artifact_declarations", f"artifact kind {kind!r} is duplicated")
            declared_artifacts.add(kind)
            if artifact["producer_stage"] not in STAGES:
                _diagnostic(diagnostics, "BACKEND_ARTIFACT_STAGE_INVALID", subject, "$.artifact_declarations", f"artifact kind {kind!r} has an invalid producer stage")
        if backend["bridge_boundary"]["execution_status"] != "not-run":
            _diagnostic(diagnostics, "BACKEND_PREMATURE_EXECUTION_CLAIM", subject, "$.bridge_boundary.execution_status", "Task 007 may declare but cannot execute the compatibility bridge")
    return registry


def _validate_eligibility_records(
    records: list[dict[str, Any]],
    bindings: dict[tuple[str, int, str], dict[str, Any]],
    contracts: dict[tuple[str, int, str], dict[str, Any]],
    targets: dict[tuple[str, int, str], dict[str, Any]],
    backends: dict[tuple[str, int, str], dict[str, Any]],
    definitions: dict[str, dict[str, Any]],
    evidence: dict[tuple[str, int, str], dict[str, Any]],
    diagnostics: list[base.Diagnostic],
) -> dict[tuple[str, int, str], dict[str, Any]]:
    registry = _registry(records, "binding_eligibility_id")
    seen_bindings: set[tuple[tuple[str, int, str], tuple[str, int, str], tuple[str, int, str]]] = set()
    for record in records:
        subject = _subject(record)
        binding_key = _ref(record["binding_reference"], "implementation_id")
        contract_key = _ref(record["contract_reference"], "component_contract_id")
        target_key = _ref(record["allowed_pair"]["target_reference"], "compute_target_id")
        backend_key = _ref(record["allowed_pair"]["backend_reference"], "backend_id")
        binding = bindings.get(binding_key)
        contract = contracts.get(contract_key)
        target = targets.get(target_key)
        backend = backends.get(backend_key)
        if binding is None:
            _diagnostic(diagnostics, "ELIGIBILITY_BINDING_REFERENCE_UNRESOLVED", subject, "$.binding_reference", "exact implementation binding did not resolve")
        if contract is None:
            _diagnostic(diagnostics, "ELIGIBILITY_CONTRACT_REFERENCE_UNRESOLVED", subject, "$.contract_reference", "exact component contract did not resolve")
        if binding is not None and _ref(binding["contract_reference"], "component_contract_id") != contract_key:
            _diagnostic(diagnostics, "ELIGIBILITY_BINDING_CONTRACT_MISMATCH", subject, "$.contract_reference", "eligibility contract differs from the binding contract")
        if binding is not None and binding["realization"]["form"] != record["realization_form"]:
            _diagnostic(diagnostics, "ELIGIBILITY_REALIZATION_FORM_MISMATCH", subject, "$.realization_form", "eligibility form differs from the binding realization")
        if target is None:
            _diagnostic(diagnostics, "ELIGIBILITY_TARGET_REFERENCE_UNRESOLVED", subject, "$.allowed_pair.target_reference", "exact target did not resolve")
        if backend is None:
            _diagnostic(diagnostics, "ELIGIBILITY_BACKEND_REFERENCE_UNRESOLVED", subject, "$.allowed_pair.backend_reference", "exact backend did not resolve")
        elif target_key not in {_ref(item["target_reference"], "compute_target_id") for item in backend["target_pairings"]}:
            _diagnostic(diagnostics, "ELIGIBILITY_TARGET_BACKEND_PAIR_UNDECLARED", subject, "$.allowed_pair", "eligibility pair is absent from the backend contract")
        elif (
            record["realization_form"] not in backend["supported_realization_forms"]
            and record["allowed_pair"]["state"]["status"]
            not in {"unsupported", "not-evaluated"}
        ):
            _diagnostic(diagnostics, "ELIGIBILITY_REALIZATION_FORM_UNSUPPORTED", subject, "$.realization_form", "backend does not accept the eligibility realization form")

        composite_key = binding_key, target_key, backend_key
        if composite_key in seen_bindings:
            _diagnostic(diagnostics, "ELIGIBILITY_BINDING_PAIR_AMBIGUOUS", subject, "$", "one binding may have only one eligibility companion for an exact pair")
        seen_bindings.add(composite_key)

        requirements = record["capability_requirements"]
        keys = [item["capability_key"] for item in requirements]
        if len(keys) != len(set(keys)):
            _diagnostic(diagnostics, "ELIGIBILITY_CAPABILITY_REQUIREMENT_DUPLICATE", subject, "$.capability_requirements", "eligibility capability requirements must be unique")
        for index, requirement in enumerate(requirements):
            _requirement_semantics(requirement, "binding-eligibility", definitions, subject, f"$.capability_requirements[{index}]", diagnostics)
        if backend is not None:
            backend_requirements = {base.canonical_json(item) for item in backend["required_target_capabilities"]}
            eligibility_requirements = {base.canonical_json(item) for item in requirements}
            if not backend_requirements <= eligibility_requirements:
                _diagnostic(diagnostics, "ELIGIBILITY_CAPABILITY_REQUIREMENTS_INCOMPLETE", subject, "$.capability_requirements", "eligibility must preserve every backend target requirement")

        regions = {item["region_id"]: item for item in target["memory_regions"]} if target else {}
        for requirement in record["resource_requirements"]:
            region = regions.get(requirement["region_id"])
            if region is None or requirement["resource_kind"] not in region["resource_kinds"]:
                _diagnostic(diagnostics, "ELIGIBILITY_RESOURCE_REGION_INVALID", subject, "$.resource_requirements", "resource requirement does not fit the exact target region")
            if not _power_of_two(requirement["alignment_bytes"]):
                _diagnostic(diagnostics, "ELIGIBILITY_RESOURCE_ALIGNMENT_INVALID", subject, "$.resource_requirements", "resource alignment must be a power of two")
            state = requirement["state"]
            if state["status"] == "supported" and not state["evidence_refs"]:
                _diagnostic(diagnostics, "ELIGIBILITY_RESOURCE_EVIDENCE_MISSING", subject, "$.resource_requirements", "supported resource requirements require evidence")

        for reference in record["compatibility_evidence"]:
            claim = evidence.get(_ref(reference, "evidence_claim_id"))
            if claim is None:
                _diagnostic(diagnostics, "ELIGIBILITY_EVIDENCE_REFERENCE_UNRESOLVED", subject, "$.compatibility_evidence", "compatibility evidence did not resolve exactly")
            elif claim["level"] < record["required_evidence_level"]:
                _diagnostic(diagnostics, "ELIGIBILITY_EVIDENCE_LEVEL_INSUFFICIENT", subject, "$.compatibility_evidence", "compatibility evidence is below the required level")
    return registry


def resolve_graph_bindings(
    graph: dict[str, Any],
    target: dict[str, Any],
    backend: dict[str, Any],
    eligibility_records: Iterable[dict[str, Any]],
    bindings: dict[tuple[str, int, str], dict[str, Any]],
    definitions: dict[str, dict[str, Any]],
    overrides: Iterable[dict[str, Any]] = (),
) -> tuple[dict[str, Any], ...]:
    """Resolve without I/O; unresolved facts remain trace outcomes, not guesses."""
    target_key = _exact(target, "compute_target_id")
    backend_key = _exact(backend, "backend_id")
    declarations = {item["capability_key"]: item["state"] for item in target["capability_declarations"]}
    override_by_node = {item["node_id"]: item for item in overrides}
    traces: list[dict[str, Any]] = []
    for node in graph["nodes"]:
        contract_key = _ref(node["contract_reference"], "component_contract_id")
        candidates: list[dict[str, Any]] = []
        for eligibility in eligibility_records:
            if _ref(eligibility["contract_reference"], "component_contract_id") != contract_key:
                continue
            binding_key = _ref(eligibility["binding_reference"], "implementation_id")
            reasons: list[str] = []
            unresolved: list[str] = []
            binding = bindings.get(binding_key)
            if binding is None or _ref(binding["contract_reference"], "component_contract_id") != contract_key:
                reasons.append("EXACT_CONTRACT_MISMATCH")
            if binding is not None and binding["realization"]["form"] not in backend["supported_realization_forms"]:
                reasons.append("REALIZATION_FORM_UNSUPPORTED")
            pair = eligibility["allowed_pair"]
            if _ref(pair["target_reference"], "compute_target_id") != target_key or _ref(pair["backend_reference"], "backend_id") != backend_key:
                reasons.append("TARGET_BACKEND_PAIR_MISMATCH")
            pair_status = pair["state"]["status"]
            if pair_status == "unsupported":
                reasons.append("TARGET_BACKEND_PAIR_UNSUPPORTED")
            elif pair_status in {"unresolved", "not-evaluated"}:
                unresolved.append(pair["state"]["code"])

            requirements = list(backend["required_target_capabilities"]) + list(eligibility["capability_requirements"])
            for requirement in requirements:
                key = requirement["capability_key"]
                definition = definitions.get(key)
                state = declarations.get(key)
                if definition is None:
                    reasons.append(f"CAPABILITY_UNKNOWN:{key}")
                elif state is None or state["status"] in {"unresolved", "not-evaluated"}:
                    unresolved.append(f"CAPABILITY_UNRESOLVED:{key}")
                elif state["status"] == "unsupported" or not _compare_capability(state["value"], requirement["value"], requirement["comparison_rule"]):
                    reasons.append(f"CAPABILITY_UNSUPPORTED:{key}")
                elif state["evidence_level"] < definition["required_evidence_level"]:
                    unresolved.append(f"CAPABILITY_EVIDENCE_INSUFFICIENT:{key}")
            for requirement in eligibility["dependency_requirements"]:
                status = requirement["state"]["status"]
                if status == "unsupported":
                    reasons.append(f"DEPENDENCY_UNSUPPORTED:{requirement['dependency_id']}")
                elif status in {"unresolved", "not-evaluated"}:
                    unresolved.append(f"DEPENDENCY_UNRESOLVED:{requirement['dependency_id']}")
            regions = {item["region_id"]: item for item in target["memory_regions"]}
            for requirement in eligibility["resource_requirements"]:
                status = requirement["state"]["status"]
                region = regions.get(requirement["region_id"])
                if status == "unsupported" or region is None or requirement["amount_bytes"] > (region or {"length_bytes": -1})["length_bytes"]:
                    reasons.append(f"RESOURCE_UNSUPPORTED:{requirement['requirement_id']}")
                elif status in {"unresolved", "not-evaluated"}:
                    unresolved.append(f"RESOURCE_UNRESOLVED:{requirement['requirement_id']}")
            if len(eligibility["compatibility_evidence"]) == 0:
                unresolved.append("COMPATIBILITY_EVIDENCE_MISSING")
            candidates.append({
                "binding_reference": eligibility["binding_reference"],
                "eligibility_reference": {
                    "binding_eligibility_id": eligibility["binding_eligibility_id"],
                    "revision": eligibility["revision"],
                    "content_hash": eligibility["content_hash"],
                },
                "priority": eligibility["selection_policy"]["priority"],
                "selection_policy_id": eligibility["selection_policy"]["policy_id"],
                "exclusion_reasons": sorted(set(reasons)),
                "unresolved_reasons": sorted(set(unresolved)),
            })

        override = override_by_node.get(node["node_id"])
        eligible = [item for item in candidates if not item["exclusion_reasons"] and not item["unresolved_reasons"]]
        unresolved_candidates = [item for item in candidates if not item["exclusion_reasons"] and item["unresolved_reasons"]]
        status: str
        selected: dict[str, Any] | None = None
        if override is not None:
            eligible = [item for item in eligible if item["binding_reference"] == override["binding_reference"]]
            unresolved_override = [item for item in unresolved_candidates if item["binding_reference"] == override["binding_reference"]]
            if not eligible and unresolved_override:
                status = "unresolved"
            elif not eligible:
                status = "invalid-override"
            else:
                status = "selected"
                selected = eligible[0]
        elif eligible:
            highest = max(item["priority"] for item in eligible)
            ranked = [item for item in eligible if item["priority"] == highest]
            if len(ranked) == 1:
                status = "selected"
                selected = ranked[0]
            else:
                status = "ambiguous"
        elif unresolved_candidates:
            status = "unresolved"
        else:
            status = "unsupported"
        traces.append({
            "node_id": node["node_id"],
            "contract_reference": node["contract_reference"],
            "status": status,
            "selected_binding_reference": selected["binding_reference"] if selected else None,
            "selection_policy_id": selected["selection_policy_id"] if selected else None,
            "candidates": sorted(candidates, key=lambda item: base.canonical_json(item["binding_reference"])),
        })
    return tuple(traces)


def _validate_build_requests(
    requests: list[dict[str, Any]],
    graphs: dict[tuple[str, int, str], dict[str, Any]],
    instruments: dict[tuple[str, int, str], dict[str, Any]],
    targets: dict[tuple[str, int, str], dict[str, Any]],
    backends: dict[tuple[str, int, str], dict[str, Any]],
    diagnostics: list[base.Diagnostic],
) -> dict[tuple[str, int, str], dict[str, Any]]:
    registry = _registry(requests, "build_request_id")
    for request in requests:
        subject = _subject(request)
        graph_key = _ref(request["graph_reference"], "graph_id")
        graph = graphs.get(graph_key)
        target = targets.get(_ref(request["compute_target_reference"], "compute_target_id"))
        backend = backends.get(_ref(request["backend_reference"], "backend_id"))
        if graph is None:
            _diagnostic(diagnostics, "BUILD_REQUEST_GRAPH_REFERENCE_UNRESOLVED", subject, "$.graph_reference", "exact graph did not resolve")
        if target is None:
            _diagnostic(diagnostics, "BUILD_REQUEST_TARGET_REFERENCE_UNRESOLVED", subject, "$.compute_target_reference", "exact compute target did not resolve")
        if backend is None:
            _diagnostic(diagnostics, "BUILD_REQUEST_BACKEND_REFERENCE_UNRESOLVED", subject, "$.backend_reference", "exact backend did not resolve")
        instrument_ref = request["instrument_reference"]
        if instrument_ref["status"] == "included":
            instrument = instruments.get(_ref(instrument_ref, "instrument_id"))
            if instrument is None:
                _diagnostic(diagnostics, "BUILD_REQUEST_INSTRUMENT_REFERENCE_UNRESOLVED", subject, "$.instrument_reference", "exact instrument did not resolve")
            elif instrument["graph_reference"]["status"] != "resolved" or _ref(instrument["graph_reference"], "graph_id") != graph_key:
                _diagnostic(diagnostics, "BUILD_REQUEST_INSTRUMENT_GRAPH_MISMATCH", subject, "$.instrument_reference", "instrument exact graph differs from the request graph")
        if target is not None and backend is not None:
            target_key = _exact(target, "compute_target_id")
            if target_key not in {_ref(item["target_reference"], "compute_target_id") for item in backend["target_pairings"]}:
                _diagnostic(diagnostics, "BUILD_REQUEST_TARGET_BACKEND_PAIR_UNDECLARED", subject, "$.backend_reference", "backend does not declare the exact request target")
            if request["requested_stopping_stage"] not in backend["permitted_stopping_stages"]:
                _diagnostic(diagnostics, "BUILD_REQUEST_STOPPING_STAGE_INVALID", subject, "$.requested_stopping_stage", "backend does not permit the requested stopping stage")
        for asset in request["asset_references"]:
            if asset["portable_locator"] != f"sha256/{asset['byte_sha256']}":
                _diagnostic(diagnostics, "BUILD_REQUEST_ASSET_LOCATOR_MISMATCH", subject, "$.asset_references", "asset locator and byte hash disagree")
            if asset["resolution_status"] != "resolved":
                _diagnostic(diagnostics, "BUILD_REQUEST_ASSET_UNRESOLVED", subject, "$.asset_references", "a build request cannot proceed with an unresolved asset")
        node_ids = {item["node_id"] for item in graph["nodes"]} if graph else set()
        override_nodes: set[str] = set()
        for override in request["binding_overrides"]:
            if override["node_id"] not in node_ids:
                _diagnostic(diagnostics, "BUILD_REQUEST_OVERRIDE_NODE_UNKNOWN", subject, "$.binding_overrides", "override node is absent from the exact graph")
            if override["node_id"] in override_nodes:
                _diagnostic(diagnostics, "BUILD_REQUEST_OVERRIDE_DUPLICATE", subject, "$.binding_overrides", "at most one override may name a graph node")
            override_nodes.add(override["node_id"])
    return registry


def _artifact_cycles(artifacts: dict[tuple[str, int, str], dict[str, Any]]) -> set[tuple[str, int, str]]:
    edges: dict[tuple[str, int, str], set[tuple[str, int, str]]] = defaultdict(set)
    for key, artifact in artifacts.items():
        for field in ("parent_artifact_references", "source_map_artifact_references"):
            edges[key].update(_ref(item, "artifact_id") for item in artifact[field])
    visited: set[tuple[str, int, str]] = set()
    active: set[tuple[str, int, str]] = set()
    cyclic: set[tuple[str, int, str]] = set()

    def visit(node: tuple[str, int, str]) -> None:
        if node in active:
            cyclic.update(active)
            return
        if node in visited:
            return
        visited.add(node)
        active.add(node)
        for child in edges.get(node, set()):
            if child in artifacts:
                visit(child)
        active.remove(node)

    for key in sorted(artifacts):
        visit(key)
    return cyclic


def _validate_artifacts(
    values: list[dict[str, Any]], diagnostics: list[base.Diagnostic]
) -> dict[tuple[str, int, str], dict[str, Any]]:
    registry = _registry(values, "artifact_id")
    for artifact in values:
        subject = _subject(artifact)
        if artifact["portable_locator"] != f"sha256/{artifact['byte_sha256']}":
            _diagnostic(diagnostics, "ARTIFACT_LOCATOR_HASH_MISMATCH", subject, "$.portable_locator", "portable locator must address artifact bytes, not descriptor identity")
        if artifact["content_hash"].removeprefix("sha256:") == artifact["byte_sha256"]:
            _diagnostic(diagnostics, "ARTIFACT_DESCRIPTOR_BYTE_HASH_CONFLATED", subject, "$.byte_sha256", "descriptor content hash and artifact-byte hash are distinct facts")
        for field in ("parent_artifact_references", "source_map_artifact_references"):
            for reference in artifact[field]:
                if _ref(reference, "artifact_id") not in registry:
                    _diagnostic(diagnostics, "ARTIFACT_REFERENCE_UNRESOLVED", subject, f"$.{field}", "exact artifact reference did not resolve")
    for key in _artifact_cycles(registry):
        _diagnostic(diagnostics, "ARTIFACT_REFERENCE_CYCLE", _subject(registry[key]), "$", "artifact ownership/reference graph must be acyclic")
    return registry


def validate_artifact_fixture_bytes(artifact: dict[str, Any], payload: bytes) -> tuple[base.Diagnostic, ...]:
    """Fixture-only byte check; aggregate validation never reads or creates artifacts."""
    diagnostics: list[base.Diagnostic] = []
    subject = _subject(artifact)
    if len(payload) != artifact["byte_length"]:
        _diagnostic(diagnostics, "ARTIFACT_BYTE_LENGTH_MISMATCH", subject, "$.byte_length", "descriptor byte length differs from supplied fixture bytes")
    if hashlib.sha256(payload).hexdigest() != artifact["byte_sha256"]:
        _diagnostic(diagnostics, "ARTIFACT_BYTE_HASH_MISMATCH", subject, "$.byte_sha256", "descriptor byte hash differs from supplied fixture bytes")
    return tuple(sorted(diagnostics, key=lambda item: (item.code, item.subject, item.location, item.message)))


def _stable_registry(groups: Iterable[Iterable[dict[str, Any]]]) -> dict[tuple[str, int, str], dict[str, Any]]:
    registry: dict[tuple[str, int, str], dict[str, Any]] = {}
    id_fields = (
        "family_id", "component_contract_id", "implementation_id", "graph_id",
        "device_profile_id", "instrument_id", "capability_vocabulary_id",
        "build_environment_id", "compute_target_id", "backend_id",
        "binding_eligibility_id", "build_request_id", "build_result_id",
        "artifact_id", "resource_report_id", "evidence_claim_id",
        "conformance_probe_evidence_id", "conformance_probe_id",
        "conformance_probe_result_id", "prerequisite_environment_id",
        "procedure_id",
    )
    for group in groups:
        for record in group:
            id_field = next((field for field in id_fields if field in record), None)
            if id_field is not None:
                registry[(record[id_field], record["revision"], record["content_hash"])] = record
    return registry


def _validate_resource_reports(
    values: list[dict[str, Any]],
    targets: dict[tuple[str, int, str], dict[str, Any]],
    stable_records: dict[tuple[str, int, str], dict[str, Any]],
    diagnostics: list[base.Diagnostic],
) -> dict[tuple[str, int, str], dict[str, Any]]:
    registry = _registry(values, "resource_report_id")
    method_contract = {
        "hard-declared-requirement": ("binding-declaration", 2),
        "static-estimate": ("static-analysis", 3),
        "compiler-link-map-observation": ("compiler-link-map", 5),
        "connected-runtime-measurement": ("connected-runtime-probe", 7),
    }
    for report in values:
        subject = _subject(report)
        target = targets.get(_ref(report["compute_target_reference"], "compute_target_id"))
        subject_ref = report["subject_reference"]
        if (subject_ref["stable_id"], subject_ref["revision"], subject_ref["content_hash"]) not in stable_records:
            _diagnostic(diagnostics, "RESOURCE_SUBJECT_REFERENCE_UNRESOLVED", subject, "$.subject_reference", "resource subject did not resolve exactly")
        if target is None:
            _diagnostic(diagnostics, "RESOURCE_TARGET_REFERENCE_UNRESOLVED", subject, "$.compute_target_reference", "resource target did not resolve exactly")
            continue
        regions = {item["region_id"]: item for item in target["memory_regions"]}
        observations = {item["observation_id"]: item for item in report["observations"]}
        for observation in report["observations"]:
            region = regions.get(observation["region_id"])
            if region is None or observation["resource_kind"] not in region["resource_kinds"]:
                _diagnostic(diagnostics, "RESOURCE_REGION_INVALID", subject, "$.observations", "observation region is absent or does not admit the resource kind")
            if "amount_bytes" in observation:
                expected = method_contract[observation["observation_kind"]]
                if (observation["method"], observation["evidence_level"]) != expected:
                    _diagnostic(diagnostics, "RESOURCE_METHOD_EVIDENCE_MISMATCH", subject, "$.observations", "observation kind, method, and evidence level disagree")
                if not _power_of_two(observation["alignment_bytes"]):
                    _diagnostic(diagnostics, "RESOURCE_ALIGNMENT_INVALID", subject, "$.observations", "resource alignment must be a power of two")
        compared: set[str] = set()
        for comparison in report["budget_comparisons"]:
            region = regions.get(comparison["region_id"])
            selected = [observations.get(item) for item in comparison["observation_ids"]]
            if region is None or any(item is None or item["region_id"] != comparison["region_id"] for item in selected):
                _diagnostic(diagnostics, "RESOURCE_CROSS_REGION_AGGREGATION", subject, "$.budget_comparisons", "one comparison may aggregate only exact observations from one region")
                continue
            compared.update(comparison["observation_ids"])
            if any("amount_bytes" not in item for item in selected):
                if comparison["outcome"] != "unresolved":
                    _diagnostic(diagnostics, "RESOURCE_UNRESOLVED_BUDGET_CLAIM", subject, "$.budget_comparisons", "unknown observations require an unresolved comparison")
                continue
            total = sum(
                ((item["amount_bytes"] + item["alignment_bytes"] - 1) // item["alignment_bytes"]) * item["alignment_bytes"]
                for item in selected
            )
            outcome = "overflow" if total > region["length_bytes"] else ("equal-to-budget" if total == region["length_bytes"] else "within-budget")
            if comparison["budget_bytes"] != region["length_bytes"] or comparison["total_aligned_amount_bytes"] != total or comparison["outcome"] != outcome:
                _diagnostic(diagnostics, "RESOURCE_BUDGET_COMPARISON_INEXACT", subject, "$.budget_comparisons", "budget, aligned aggregate, or outcome differs from exact arithmetic")
        required = {item["observation_id"] for item in report["observations"] if item["observation_kind"] == "hard-declared-requirement"}
        if not required <= compared:
            _diagnostic(diagnostics, "RESOURCE_REQUIRED_BUDGET_UNCOMPARED", subject, "$.budget_comparisons", "every hard-declared requirement must participate in a budget comparison")
    return registry


def _closure_hash(values: list[dict[str, Any]]) -> str:
    ordered = sorted(values, key=base.canonical_json)
    return "sha256:" + hashlib.sha256(base.canonical_json(ordered).encode("utf-8")).hexdigest()


def _validate_build_results(
    values: list[dict[str, Any]],
    requests: dict[tuple[str, int, str], dict[str, Any]],
    graphs: dict[tuple[str, int, str], dict[str, Any]],
    targets: dict[tuple[str, int, str], dict[str, Any]],
    backends: dict[tuple[str, int, str], dict[str, Any]],
    environments: dict[tuple[str, int, str], dict[str, Any]],
    bindings: dict[tuple[str, int, str], dict[str, Any]],
    eligibility: dict[tuple[str, int, str], dict[str, Any]],
    artifacts: dict[tuple[str, int, str], dict[str, Any]],
    resources: dict[tuple[str, int, str], dict[str, Any]],
    stable_records: dict[tuple[str, int, str], dict[str, Any]],
    diagnostics: list[base.Diagnostic],
) -> dict[tuple[str, int, str], dict[str, Any]]:
    registry = _registry(values, "build_result_id")
    kind_by_schema = {
        "catalog-family-companion-v0": "catalog-family",
        "component-contract-v0": "component-contract",
        "implementation-binding-v0": "implementation-binding",
        "dsp-graph-v0": "dsp-graph",
        "device-profile-v0": "device-profile",
        "instrument-v0": "instrument",
        "capability-vocabulary-v0": "capability-vocabulary",
        "compute-target-v0": "compute-target",
        "backend-v0": "backend",
        "build-environment-v0": "build-environment",
        "binding-eligibility-v0": "binding-eligibility",
        "build-request-v0": "build-request",
    }
    for result in values:
        subject = _subject(result)
        request = requests.get(_ref(result["request_reference"], "build_request_id"))
        if request is None:
            _diagnostic(diagnostics, "BUILD_RESULT_REQUEST_REFERENCE_UNRESOLVED", subject, "$.request_reference", "exact build request did not resolve")
            continue
        graph = graphs.get(_ref(request["graph_reference"], "graph_id"))
        target_key = _ref(result["compute_target_reference"], "compute_target_id")
        backend_key = _ref(result["backend_reference"], "backend_id")
        target = targets.get(target_key)
        backend = backends.get(backend_key)
        if target_key != _ref(request["compute_target_reference"], "compute_target_id") or target is None:
            _diagnostic(diagnostics, "BUILD_RESULT_TARGET_MISMATCH", subject, "$.compute_target_reference", "result target differs from or fails to resolve against the request")
        if backend_key != _ref(request["backend_reference"], "backend_id") or backend is None:
            _diagnostic(diagnostics, "BUILD_RESULT_BACKEND_MISMATCH", subject, "$.backend_reference", "result backend differs from or fails to resolve against the request")
        if result["options_used"] != request["options"]:
            _diagnostic(diagnostics, "BUILD_RESULT_OPTIONS_CHANGED", subject, "$.options_used", "result options must equal immutable request options")
        if backend is not None:
            for field in ("toolchain_reference", "firmware_runtime_reference"):
                if result[field] != backend[field] or _ref(result[field], "build_environment_id") not in environments:
                    _diagnostic(diagnostics, "BUILD_RESULT_ENVIRONMENT_MISMATCH", subject, f"$.{field}", "result environment must equal the exact backend environment")

        closure_keys: set[tuple[str, int, str]] = set()
        for index, reference in enumerate(result["input_closure"]):
            key = (reference["stable_id"], reference["revision"], reference["content_hash"])
            record = stable_records.get(key)
            if record is None:
                _diagnostic(diagnostics, "BUILD_RESULT_CLOSURE_REFERENCE_UNRESOLVED", subject, f"$.input_closure[{index}]", "closure member did not resolve exactly")
            elif kind_by_schema.get(record["schema_version"]) != reference["record_kind"]:
                _diagnostic(diagnostics, "BUILD_RESULT_CLOSURE_KIND_MISMATCH", subject, f"$.input_closure[{index}]", "closure member kind disagrees with the exact record schema")
            closure_keys.add(key)
        if result["input_closure_hash"] != _closure_hash(result["input_closure"]):
            _diagnostic(diagnostics, "BUILD_RESULT_CLOSURE_HASH_MISMATCH", subject, "$.input_closure_hash", "input closure hash does not match canonical exact references")
        required_closure = {
            (request["build_request_id"], request["revision"], request["content_hash"]),
            _ref(request["graph_reference"], "graph_id"),
            target_key,
            backend_key,
            _ref(result["toolchain_reference"], "build_environment_id"),
            _ref(result["firmware_runtime_reference"], "build_environment_id"),
        }
        if request["instrument_reference"]["status"] == "included":
            required_closure.add(_ref(request["instrument_reference"], "instrument_id"))
        if not required_closure <= closure_keys:
            _diagnostic(diagnostics, "BUILD_RESULT_CLOSURE_INCOMPLETE", subject, "$.input_closure", "result closure omits request, graph, instrument, target, backend, or environment identity")

        node_ids = {item["node_id"] for item in graph["nodes"]} if graph else set()
        selections = {item["node_id"]: item for item in result["selected_bindings"]}
        if len(selections) != len(result["selected_bindings"]):
            _diagnostic(diagnostics, "BUILD_RESULT_NODE_SELECTION_DUPLICATE", subject, "$.selected_bindings", "node selections must be unique")
        if set(selections) != node_ids:
            _diagnostic(diagnostics, "BUILD_RESULT_NODE_SELECTION_INCOMPLETE", subject, "$.selected_bindings", "result must select exactly one binding for every graph node")
        for selection in result["selected_bindings"]:
            binding_key = _ref(selection["binding_reference"], "implementation_id")
            eligibility_key = _ref(selection["eligibility_reference"], "binding_eligibility_id")
            binding = bindings.get(binding_key)
            companion = eligibility.get(eligibility_key)
            if binding is None or companion is None or companion["binding_reference"] != selection["binding_reference"]:
                _diagnostic(diagnostics, "BUILD_RESULT_SELECTION_REFERENCE_UNRESOLVED", subject, "$.selected_bindings", "selected binding and eligibility must resolve as an exact pair")
            elif companion["selection_policy"]["policy_id"] != selection["selection_policy_id"]:
                _diagnostic(diagnostics, "BUILD_RESULT_SELECTION_POLICY_MISMATCH", subject, "$.selected_bindings", "selection policy identity differs from the eligibility companion")
            elif companion["allowed_pair"]["state"]["status"] != "supported":
                _diagnostic(diagnostics, "BUILD_RESULT_SELECTION_INELIGIBLE", subject, "$.selected_bindings", "a result may select only an evidence-supported eligibility pair")

        stages = result["stage_outcomes"]
        if [(item["ordinal"], item["stage"]) for item in stages] != list(enumerate(STAGES, 1)):
            _diagnostic(diagnostics, "BUILD_RESULT_STAGE_SEQUENCE_INVALID", subject, "$.stage_outcomes", "result requires the complete fixed stage sequence")
        requested_stop_ordinal = STAGES.index(request["requested_stopping_stage"]) + 1
        terminal_seen = False
        first_terminal: str | None = None
        for stage in stages:
            if stage["ordinal"] > requested_stop_ordinal:
                if stage["status"] != "not-run":
                    _diagnostic(
                        diagnostics,
                        "BUILD_RESULT_STAGE_AFTER_REQUESTED_STOP",
                        subject,
                        "$.stage_outcomes",
                        "every stage after the immutable request stopping stage must be not-run",
                    )
                if stage["diagnostic_ids"] or stage["artifact_references"] or stage["resource_report_references"]:
                    _diagnostic(
                        diagnostics,
                        "BUILD_RESULT_OUTPUT_AFTER_REQUESTED_STOP",
                        subject,
                        "$.stage_outcomes",
                        "a stage after the immutable request stopping stage cannot own outputs",
                    )
                continue
            if terminal_seen and stage["status"] != "not-run":
                _diagnostic(diagnostics, "BUILD_RESULT_STAGE_AFTER_TERMINAL", subject, "$.stage_outcomes", "every stage after the first non-success outcome must be not-run")
            if not terminal_seen and stage["status"] != "success":
                terminal_seen = True
                first_terminal = stage["status"]
        expected_overall = first_terminal or "success"
        if result["overall_status"] != expected_overall:
            _diagnostic(diagnostics, "BUILD_RESULT_OVERALL_STATUS_INVALID", subject, "$.overall_status", "overall status must equal the first non-success stage or success")

        diagnostic_ids = [item["diagnostic_id"] for item in result["diagnostics"]]
        expected_ids = [f"diagnostic-{index:06d}" for index in range(1, len(diagnostic_ids) + 1)]
        if diagnostic_ids != expected_ids:
            _diagnostic(diagnostics, "BUILD_RESULT_DIAGNOSTIC_ORDER_INVALID", subject, "$.diagnostics", "diagnostic IDs and sequence must be deterministic and contiguous")
        diagnostic_map = {item["diagnostic_id"]: item for item in result["diagnostics"]}
        related_edges: dict[str, set[str]] = defaultdict(set)
        known_subjects = node_ids | {request["build_request_id"], request["graph_reference"]["graph_id"], target_key[0], backend_key[0]}
        for item in result["diagnostics"]:
            related_edges[item["diagnostic_id"]].update(item["related_diagnostic_ids"])
            for related in item["related_diagnostic_ids"]:
                if related not in diagnostic_map:
                    _diagnostic(diagnostics, "BUILD_RESULT_DIAGNOSTIC_REFERENCE_UNRESOLVED", subject, "$.diagnostics", "related diagnostic ID did not resolve")
            if any(reference["subject_id"] not in known_subjects for reference in item["subject_references"]):
                _diagnostic(diagnostics, "BUILD_RESULT_DIAGNOSTIC_SUBJECT_UNKNOWN", subject, "$.diagnostics", "diagnostic subject is absent from the exact build closure")
        if core.cycle_nodes(related_edges):
            _diagnostic(diagnostics, "BUILD_RESULT_DIAGNOSTIC_CYCLE", subject, "$.diagnostics", "related diagnostic references must be acyclic")
        for stage in stages:
            if any(item not in diagnostic_map for item in stage["diagnostic_ids"]):
                _diagnostic(diagnostics, "BUILD_RESULT_STAGE_DIAGNOSTIC_UNRESOLVED", subject, "$.stage_outcomes", "stage diagnostic ID did not resolve")

        artifact_refs = {_ref(item, "artifact_id") for item in result["artifact_references"]}
        resource_refs = {_ref(item, "resource_report_id") for item in result["resource_report_references"]}
        if any(item not in artifacts for item in artifact_refs):
            _diagnostic(diagnostics, "BUILD_RESULT_ARTIFACT_REFERENCE_UNRESOLVED", subject, "$.artifact_references", "result artifact did not resolve exactly")
        if backend is not None:
            declarations = {
                (item["artifact_kind"], item["media_type"], item["producer_stage"])
                for item in backend["artifact_declarations"]
            }
            for key in artifact_refs:
                artifact = artifacts.get(key)
                if artifact is not None and (artifact["artifact_kind"], artifact["media_type"], artifact["producer_stage"]) not in declarations:
                    _diagnostic(diagnostics, "BUILD_RESULT_ARTIFACT_UNDECLARED", subject, "$.artifact_references", "artifact kind, media type, and producer stage must match the backend declaration")
        if any(item not in resources for item in resource_refs):
            _diagnostic(diagnostics, "BUILD_RESULT_RESOURCE_REFERENCE_UNRESOLVED", subject, "$.resource_report_references", "result resource report did not resolve exactly")
        stage_artifacts = {_ref(item, "artifact_id") for stage in stages for item in stage["artifact_references"]}
        stage_resources = {_ref(item, "resource_report_id") for stage in stages for item in stage["resource_report_references"]}
        if stage_artifacts != artifact_refs or stage_resources != resource_refs:
            _diagnostic(diagnostics, "BUILD_RESULT_OUTPUT_REFERENCE_MISMATCH", subject, "$.stage_outcomes", "stage output references and result output references must be total and equal")
    return registry


def _validate_evidence_claims(
    values: list[dict[str, Any]],
    stable_records: dict[tuple[str, int, str], dict[str, Any]],
    build_results: dict[tuple[str, int, str], dict[str, Any]],
    diagnostics: list[base.Diagnostic],
) -> dict[tuple[str, int, str], dict[str, Any]]:
    registry = _registry(values, "evidence_claim_id")
    expected_stage = {
        1: "schema-identity-validation",
        2: "target-independent-graph-validation",
        3: "backend-lowering",
        4: "artifact-generation",
        5: "target-compile-link",
        6: "connected-device-execution",
        7: "real-time-resource-validation",
        8: "audible-listening-validation",
    }
    producer_kind = {
        1: "validator", 2: "validator", 3: "backend", 4: "backend",
        5: "toolchain", 6: "device-procedure", 7: "measurement-procedure", 8: "listening-procedure",
    }
    subject_kinds = {
        1: {"semantic-record", "build-result"},
        2: {"semantic-record", "build-result", "build-stage", "instrument"},
        3: {"build-result", "build-stage"},
        4: {"build-result", "build-stage", "artifact"},
        5: {"build-result", "build-stage", "artifact"},
        6: {"build-result", "device-profile", "instrument"},
        7: {"resource-report"},
        8: {"device-profile", "instrument"},
    }
    for claim in values:
        subject = _subject(claim)
        level = claim["level"]
        reference = claim["subject_reference"]
        if claim["level_name"] != EVIDENCE_LEVEL_NAMES[level]:
            _diagnostic(diagnostics, "EVIDENCE_LEVEL_NAME_MISMATCH", subject, "$.level_name", "evidence level and controlled name disagree")
        if reference["stage"] != expected_stage[level]:
            _diagnostic(diagnostics, "EVIDENCE_LEVEL_STAGE_MISMATCH", subject, "$.subject_reference.stage", "one claim may represent only its own evidence level")
        if reference["subject_kind"] not in subject_kinds[level]:
            _diagnostic(diagnostics, "EVIDENCE_LEVEL_SUBJECT_INVALID", subject, "$.subject_reference.subject_kind", "subject kind is not valid for this evidence level")
        if claim["producer_identity"]["producer_kind"] != producer_kind[level]:
            _diagnostic(diagnostics, "EVIDENCE_LEVEL_PRODUCER_INVALID", subject, "$.producer_identity.producer_kind", "producer kind is not valid for this evidence level")
        subject_key = (reference["stable_id"], reference["revision"], reference["content_hash"])
        subject_record = stable_records.get(subject_key)
        if subject_record is None:
            _diagnostic(diagnostics, "EVIDENCE_SUBJECT_REFERENCE_UNRESOLVED", subject, "$.subject_reference", "evidence subject did not resolve exactly")
        elif reference["subject_kind"] == "build-stage":
            result = build_results.get(subject_key)
            if result is None or next((item for item in result["stage_outcomes"] if item["stage"] == reference["stage"]), {"status": "not-run"})["status"] != "success":
                _diagnostic(diagnostics, "EVIDENCE_STAGE_NOT_PERFORMED", subject, "$.subject_reference", "evidence cannot claim a build stage that was not successful")
        for input_reference in claim["evidence_inputs"]:
            if input_reference["input_kind"] == "procedure":
                continue
            input_key = (input_reference["stable_id"], input_reference["revision"], input_reference["content_hash"])
            if input_key not in stable_records:
                _diagnostic(diagnostics, "EVIDENCE_INPUT_REFERENCE_UNRESOLVED", subject, "$.evidence_inputs", "evidence input did not resolve exactly")
    return registry


def _validate_evidence_stratification(
    eligibility_records: Iterable[dict[str, Any]],
    evidence: dict[tuple[str, int, str], dict[str, Any]],
    diagnostics: list[base.Diagnostic],
) -> None:
    for eligibility in eligibility_records:
        subject = _subject(eligibility)
        binding = eligibility["binding_reference"]
        for reference in eligibility["compatibility_evidence"]:
            claim = evidence.get(_ref(reference, "evidence_claim_id"))
            if claim is None:
                continue
            cited_revisions = [
                item["revision"]
                for item in claim["evidence_inputs"]
                if item["stable_id"] == binding["implementation_id"]
            ]
            if not cited_revisions or max(cited_revisions) >= binding["revision"]:
                _diagnostic(diagnostics, "ELIGIBILITY_EVIDENCE_REVISION_NOT_EARLIER", subject, "$.compatibility_evidence", "compatibility evidence must cite a strictly earlier binding revision")


def _global_identity_collisions(
    groups: Iterable[Iterable[dict[str, Any]]], diagnostics: list[base.Diagnostic]
) -> None:
    entries: dict[tuple[str, int], set[str]] = defaultdict(set)
    for group in groups:
        for record in group:
            subject = _subject(record).rsplit("@", 1)[0]
            entries[(subject, record["revision"])].add(record["content_hash"])
    for (stable_id, revision), hashes in sorted(entries.items()):
        if len(hashes) > 1:
            _diagnostic(diagnostics, "GLOBAL_ID_REVISION_COLLISION", f"{stable_id}@{revision}", "$", "one stable ID and revision maps to multiple content hashes")


def validate_target_backend_build_directory(
    contract_root: Path,
    schema_root: Path,
    repository_root: Path,
    upstream_summary: dict[str, Any],
) -> Task007Validation:
    schemas = _schemas(schema_root)
    loaded = _records(contract_root)
    upstream = {
        "families": [base.load_json(path) for path in _record_files(contract_root, "catalog-families")],
        "contracts": [base.load_json(path) for path in _record_files(contract_root, "component-contracts")],
        "bindings": [base.load_json(path) for path in _record_files(contract_root, "implementation-bindings")],
        "graphs": [base.load_json(path) for path in _record_files(contract_root, "graphs")],
        "devices": [base.load_json(path) for path in _record_files(contract_root, "device-profiles")],
        "instruments": [base.load_json(path) for path in _record_files(contract_root, "instruments")],
    }
    return validate_target_backend_build_values(
        loaded,
        schemas,
        upstream,
        repository_root,
        upstream_summary,
    )


def validate_target_backend_build_values(
    loaded: dict[str, list[dict[str, Any]]],
    schemas: dict[str, dict[str, Any]],
    upstream: dict[str, list[dict[str, Any]]],
    repository_root: Path,
    upstream_summary: dict[str, Any],
    additional_semantic_records: Iterable[dict[str, Any]] = (),
) -> Task007Validation:
    """Validate one explicitly selected in-memory record-set closure."""

    diagnostics: list[base.Diagnostic] = []
    semantic_records = list(additional_semantic_records)
    if upstream_summary["status"] == "invalid":
        for item in upstream_summary["diagnostics"]:
            diagnostics.append(base.Diagnostic(item["code"], item["severity"], item["subject"], item["location"], item["message"]))

    valid = _validate_structural(loaded, schemas, diagnostics)
    contract_registry = _registry(upstream["contracts"], "component_contract_id")
    binding_registry = _registry(upstream["bindings"], "implementation_id")
    graph_registry = _registry(upstream["graphs"], "graph_id")
    instrument_registry = _registry(upstream["instruments"], "instrument_id")

    capability_registry, definitions = _capability_definitions(valid["capability"], diagnostics)
    environment_registry = _validate_environments(valid["environment"], diagnostics)
    target_registry = _validate_targets(valid["target"], capability_registry, definitions, environment_registry, diagnostics)
    backend_registry = _validate_backends(valid["backend"], capability_registry, definitions, target_registry, environment_registry, diagnostics)
    evidence_registry = _registry(valid["evidence"], "evidence_claim_id")
    eligibility_registry = _validate_eligibility_records(
        valid["eligibility"], binding_registry, contract_registry, target_registry,
        backend_registry, definitions, evidence_registry, diagnostics,
    )
    request_registry = _validate_build_requests(
        valid["request"], graph_registry, instrument_registry, target_registry, backend_registry, diagnostics,
    )
    artifact_registry = _validate_artifacts(valid["artifact"], diagnostics)

    stable_before_resources = _stable_registry([
        *upstream.values(), valid["capability"], valid["environment"], valid["target"],
        valid["backend"], valid["eligibility"], valid["request"], valid["artifact"],
        semantic_records,
    ])
    resource_registry = _validate_resource_reports(valid["resource"], target_registry, stable_before_resources, diagnostics)
    stable_before_results = _stable_registry([
        *upstream.values(), valid["capability"], valid["environment"], valid["target"],
        valid["backend"], valid["eligibility"], valid["request"], valid["artifact"], valid["resource"],
        semantic_records,
    ])
    result_registry = _validate_build_results(
        valid["result"], request_registry, graph_registry, target_registry, backend_registry,
        environment_registry, binding_registry, eligibility_registry, artifact_registry,
        resource_registry, stable_before_results, diagnostics,
    )
    stable_before_evidence = _stable_registry([
        *upstream.values(), *valid.values(), semantic_records,
    ])
    evidence_registry = _validate_evidence_claims(valid["evidence"], stable_before_evidence, result_registry, diagnostics)
    _validate_evidence_stratification(valid["eligibility"], evidence_registry, diagnostics)
    _global_identity_collisions([*upstream.values(), *valid.values(), semantic_records], diagnostics)

    source_lock = base.load_json(repository_root / "catalog/sources.lock.json")
    source_reference_count, locally_verified_count = _verify_source_evidence(
        (record for values in valid.values() for record in values),
        source_lock,
        _local_sources(repository_root),
        diagnostics,
    )

    traces: list[dict[str, Any]] = []
    for request in valid["request"]:
        graph = graph_registry.get(_ref(request["graph_reference"], "graph_id"))
        target = target_registry.get(_ref(request["compute_target_reference"], "compute_target_id"))
        backend = backend_registry.get(_ref(request["backend_reference"], "backend_id"))
        if graph is not None and target is not None and backend is not None:
            traces.extend(resolve_graph_bindings(
                graph, target, backend, valid["eligibility"], binding_registry,
                definitions, request["binding_overrides"],
            ))

    diagnostics = sorted(set(diagnostics), key=lambda item: (item.severity, item.code, item.subject, item.location, item.message))
    status = "invalid" if diagnostics else "valid"
    counts = {SCHEMA_SPECS[kind][3].replace("-", "_"): len(values) for kind, values in loaded.items()}
    summary = {
        "schema_version": "task-007-validation-summary-v0",
        "status": status,
        "record_counts": counts,
        "reference_resolution": {
            "source_evidence_references": source_reference_count,
            "source_evidence_locally_verified": locally_verified_count,
            "resolution_outcomes": dict(sorted(Counter(item["status"] for item in traces).items())),
        },
        "evidence_levels": [
            {"level": level, "name": EVIDENCE_LEVEL_NAMES[level], "status": "passed" if level in (1, 2) and not diagnostics else ("failed" if level in (1, 2) else "not-run")}
            for level in range(1, 9)
        ],
        "resolution_traces": traces,
        "diagnostics": [item.as_dict() for item in diagnostics],
    }
    return Task007Validation(summary, tuple(traces), tuple(diagnostics))
