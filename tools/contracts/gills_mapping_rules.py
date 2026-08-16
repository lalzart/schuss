#!/usr/bin/env python3
"""Task 018 Gills evidence, coverage, and runtime-realization rules."""

from __future__ import annotations

import copy
from collections import Counter
from typing import Any, Iterable

import validator_core as core


SCHEMA_SPECS = {
    "panel_evidence": ("gills-panel-evidence-v0.schema.json", "gills-panel-evidence-v0", "panel_evidence_packet_id"),
    "mapping_coverage": ("gills-mapping-coverage-v0.schema.json", "gills-mapping-coverage-v0", "coverage_report_id"),
    "runtime_realizations": ("gills-runtime-realization-v0.schema.json", "gills-runtime-realization-v0", "runtime_realization_id"),
}


def _ref(value: dict[str, Any], id_field: str) -> tuple[str, int, str]:
    return value[id_field], value["revision"], value["content_hash"]


def _registry(values: Iterable[dict[str, Any]], id_field: str) -> dict[tuple[str, int, str], dict[str, Any]]:
    return {_ref(value, id_field): value for value in values}


def _diagnostic(
    diagnostics: list[core.Diagnostic], code: str, subject: str, location: str, message: str
) -> None:
    core.add_diagnostic(diagnostics, code, subject, location, message)


def _device_slots(device: dict[str, Any]) -> set[tuple[str, str]]:
    result: set[tuple[str, str]] = set()
    for kind, collection, id_field in (
        ("input-control", "input_controls", "slot_id"),
        ("gesture", "gestures", "gesture_id"),
        ("feedback-output", "feedback_outputs", "slot_id"),
        ("display", "displays", "slot_id"),
        ("physical-io", "physical_io", "slot_id"),
    ):
        result.update((kind, item[id_field]) for item in device[collection])
    return result


def _instrument_facets(instrument: dict[str, Any]) -> set[tuple[str, str]]:
    result: set[tuple[str, str]] = set()
    for kind, collection, id_field in (
        ("parameter", "parameters", "facet_id"),
        ("action", "actions", "facet_id"),
        ("display", "displays", "facet_id"),
        ("state", "state_declarations", "state_id"),
    ):
        result.update((kind, item[id_field]) for item in instrument[collection])
    return result


def _mapping_ids(instrument: dict[str, Any]) -> set[tuple[str, str]]:
    return {
        *(("device-input", item["mapping_id"]) for item in instrument["device_input_mappings"]),
        *(("device-feedback", item["mapping_id"]) for item in instrument["device_feedback_mappings"]),
        *(("graph", item["mapping_id"]) for item in instrument["graph_mappings"]),
    }


def _validate_structural(
    groups: dict[str, list[dict[str, Any]]],
    schemas: dict[str, dict[str, Any]],
    diagnostics: list[core.Diagnostic],
) -> dict[str, list[dict[str, Any]]]:
    valid: dict[str, list[dict[str, Any]]] = {}
    for group, (schema_name, version, id_field) in SCHEMA_SPECS.items():
        schema = schemas[group]
        valid[group] = core.validate_structural_records(
            groups[group], schema, schema_name, version, id_field, diagnostics
        )
    return valid


def _validate_panel(
    panel: dict[str, Any], devices: dict[tuple[str, int, str], dict[str, Any]], diagnostics: list[core.Diagnostic]
) -> None:
    subject = core.record_subject(panel)
    source_ids = [item["source_id"] for item in panel["sources"]]
    if len(source_ids) != len(set(source_ids)):
        _diagnostic(diagnostics, "GILLS_EVIDENCE_SOURCE_DUPLICATE", subject, "$.sources", "panel evidence source IDs must be unique")
    known_sources = set(source_ids)
    slot_keys = [(item["slot_kind"], item["slot_id"]) for item in panel["slot_evidence"]]
    if len(slot_keys) != len(set(slot_keys)):
        _diagnostic(diagnostics, "GILLS_EVIDENCE_SLOT_DUPLICATE", subject, "$.slot_evidence", "panel evidence slots must be unique")
    for slot_index, slot in enumerate(panel["slot_evidence"]):
        fact_keys = [item["key"] for item in slot["facts"]]
        if len(fact_keys) != len(set(fact_keys)):
            _diagnostic(diagnostics, "GILLS_EVIDENCE_FACT_DUPLICATE", subject, f"$.slot_evidence[{slot_index}].facts", "one slot may declare each fact key once")
        for fact_index, fact in enumerate(slot["facts"]):
            location = f"$.slot_evidence[{slot_index}].facts[{fact_index}]"
            references = fact["evidence_refs"]
            if fact["status"] == "observed" and not references:
                _diagnostic(diagnostics, "GILLS_OBSERVED_FACT_UNAUTHENTICATED", subject, location, "observed facts require exact source references")
            for reference in references:
                if reference["source_id"] not in known_sources:
                    _diagnostic(diagnostics, "GILLS_EVIDENCE_REFERENCE_UNRESOLVED", subject, location, "panel fact source reference does not resolve")
    for index, fact in enumerate(panel["unresolved_facts"]):
        for reference in fact["evidence_refs"]:
            if reference["source_id"] not in known_sources:
                _diagnostic(diagnostics, "GILLS_EVIDENCE_REFERENCE_UNRESOLVED", subject, f"$.unresolved_facts[{index}]", "unresolved-fact source reference does not resolve")
        unknown = set(fact["affected_slots"]) - {item[1] for item in slot_keys}
        if unknown:
            _diagnostic(diagnostics, "GILLS_UNRESOLVED_SLOT_UNKNOWN", subject, f"$.unresolved_facts[{index}].affected_slots", "unresolved fact names a slot absent from the evidence census")
    successors = [value for value in devices.values() if value["device_profile_id"] == "schuss-device-profile-000001" and value["revision"] == 2]
    if len(successors) == 1:
        expected = _device_slots(successors[0])
        if set(slot_keys) != expected:
            _diagnostic(diagnostics, "GILLS_EVIDENCE_CENSUS_INCOMPLETE", subject, "$.slot_evidence", "panel evidence slots and exact successor device slots must be total and equal")
    else:
        _diagnostic(diagnostics, "GILLS_DEVICE_SUCCESSOR_UNRESOLVED", subject, "$", "exact Gills device-profile successor did not resolve once")
    boundaries = panel["evidence_boundaries"]
    if [item["level"] for item in boundaries] != list(range(1, 9)) or [item["status"] for item in boundaries] != ["passed"] + ["not-run"] * 7:
        _diagnostic(diagnostics, "GILLS_EVIDENCE_BOUNDARY_INVALID", subject, "$.evidence_boundaries", "panel evidence packet may pass only structural level 1")


def _validate_runtime(
    runtime: dict[str, Any],
    devices: dict[tuple[str, int, str], dict[str, Any]],
    panels: dict[tuple[str, int, str], dict[str, Any]],
    instruments: dict[tuple[str, int, str], dict[str, Any]],
    requests: dict[tuple[str, int, str], dict[str, Any]],
    targets: dict[tuple[str, int, str], dict[str, Any]],
    backends: dict[tuple[str, int, str], dict[str, Any]],
    environments: dict[tuple[str, int, str], dict[str, Any]],
    diagnostics: list[core.Diagnostic],
) -> None:
    subject = core.record_subject(runtime)
    device = devices.get(_ref(runtime["device_profile_reference"], "device_profile_id"))
    panel = panels.get(_ref(runtime["panel_evidence_reference"], "panel_evidence_packet_id"))
    target = targets.get(_ref(runtime["compute_target_reference"], "compute_target_id"))
    backend = backends.get(_ref(runtime["backend_reference"], "backend_id"))
    environment = environments.get(_ref(runtime["firmware_runtime_reference"], "build_environment_id"))
    for value, code, location in (
        (device, "GILLS_RUNTIME_DEVICE_UNRESOLVED", "$.device_profile_reference"),
        (panel, "GILLS_RUNTIME_EVIDENCE_UNRESOLVED", "$.panel_evidence_reference"),
        (target, "GILLS_RUNTIME_TARGET_UNRESOLVED", "$.compute_target_reference"),
        (backend, "GILLS_RUNTIME_BACKEND_UNRESOLVED", "$.backend_reference"),
        (environment, "GILLS_RUNTIME_ENVIRONMENT_UNRESOLVED", "$.firmware_runtime_reference"),
    ):
        if value is None:
            _diagnostic(diagnostics, code, subject, location, "exact runtime realization reference did not resolve")
    if backend is not None and backend["firmware_runtime_reference"] != runtime["firmware_runtime_reference"]:
        _diagnostic(diagnostics, "GILLS_RUNTIME_ENVIRONMENT_MISMATCH", subject, "$.firmware_runtime_reference", "runtime realization and backend name different firmware/runtime identities")
    if target is not None and target["firmware_runtime_reference"] != runtime["firmware_runtime_reference"]:
        _diagnostic(diagnostics, "GILLS_RUNTIME_TARGET_ENVIRONMENT_MISMATCH", subject, "$.firmware_runtime_reference", "runtime realization and compute target name different firmware/runtime identities")

    all_bindings = [item for collection in ("input_bindings", "feedback_bindings", "display_bindings", "physical_io_bindings") for item in runtime[collection]]
    binding_ids = [item["binding_id"] for item in all_bindings]
    if len(binding_ids) != len(set(binding_ids)):
        _diagnostic(diagnostics, "GILLS_RUNTIME_BINDING_DUPLICATE", subject, "$", "runtime binding IDs must be globally unique within the realization")
    if device is not None:
        expected = {
            "input_bindings": {item["slot_id"] for item in device["input_controls"]},
            "feedback_bindings": {item["slot_id"] for item in device["feedback_outputs"]},
            "display_bindings": {item["slot_id"] for item in device["displays"]},
            "physical_io_bindings": {item["slot_id"] for item in device["physical_io"]},
        }
        for collection, slot_ids in expected.items():
            actual = [item["slot_id"] for item in runtime[collection]]
            if len(actual) != len(set(actual)) or set(actual) != slot_ids:
                _diagnostic(diagnostics, "GILLS_RUNTIME_BINDING_COVERAGE_INCOMPLETE", subject, f"$.{collection}", "runtime bindings and exact device slots must be total and equal")
    source_ids = {item["source_id"] for item in panel["sources"]} if panel else set()
    for index, binding in enumerate(all_bindings):
        if not set(binding["evidence_source_ids"]) <= source_ids:
            _diagnostic(diagnostics, "GILLS_RUNTIME_BINDING_EVIDENCE_UNRESOLVED", subject, f"$.bindings[{index}]", "runtime binding cites an absent panel evidence source")

    build_keys: set[tuple[str, int, str]] = set()
    for index, supported in enumerate(runtime["supported_builds"]):
        location = f"$.supported_builds[{index}]"
        request_key = _ref(supported["build_request_reference"], "build_request_id")
        instrument_key = _ref(supported["instrument_reference"], "instrument_id")
        request = requests.get(request_key)
        instrument = instruments.get(instrument_key)
        if request_key in build_keys:
            _diagnostic(diagnostics, "GILLS_RUNTIME_BUILD_DUPLICATE", subject, location, "one exact build request may occur once per runtime realization")
        build_keys.add(request_key)
        if request is None or instrument is None:
            _diagnostic(diagnostics, "GILLS_RUNTIME_BUILD_REFERENCE_UNRESOLVED", subject, location, "supported build request or instrument did not resolve exactly")
            continue
        if request["instrument_reference"] != {"status": "included", **supported["instrument_reference"]}:
            _diagnostic(diagnostics, "GILLS_RUNTIME_BUILD_INSTRUMENT_MISMATCH", subject, location, "runtime build and request name different exact instruments")
        if request["backend_reference"] != runtime["backend_reference"] or request["compute_target_reference"] != runtime["compute_target_reference"]:
            _diagnostic(diagnostics, "GILLS_RUNTIME_BUILD_CLOSURE_MISMATCH", subject, location, "runtime build, backend, and target references are not one exact closure")
        if instrument["device_profile_reference"] != runtime["device_profile_reference"]:
            _diagnostic(diagnostics, "GILLS_RUNTIME_DEVICE_INSTRUMENT_MISMATCH", subject, location, "runtime and instrument name different exact device profiles")


def _validate_coverage(
    coverage: dict[str, Any],
    devices: dict[tuple[str, int, str], dict[str, Any]],
    panels: dict[tuple[str, int, str], dict[str, Any]],
    instruments: dict[tuple[str, int, str], dict[str, Any]],
    runtimes: list[dict[str, Any]],
    diagnostics: list[core.Diagnostic],
) -> None:
    subject = core.record_subject(coverage)
    device = devices.get(_ref(coverage["device_profile_reference"], "device_profile_id"))
    panel = panels.get(_ref(coverage["panel_evidence_reference"], "panel_evidence_packet_id"))
    instrument_key = _ref(coverage["instrument_reference"], "instrument_id")
    instrument = instruments.get(instrument_key)
    if device is None or panel is None or instrument is None:
        _diagnostic(diagnostics, "GILLS_COVERAGE_REFERENCE_UNRESOLVED", subject, "$", "coverage device, instrument, or panel reference did not resolve exactly")
        return
    device_keys = [(item["slot_kind"], item["slot_id"]) for item in coverage["device_slot_coverage"]]
    facet_keys = [(item["facet_kind"], item["facet_id"]) for item in coverage["instrument_facet_coverage"]]
    if len(device_keys) != len(set(device_keys)) or set(device_keys) != _device_slots(device):
        _diagnostic(diagnostics, "GILLS_DEVICE_COVERAGE_INCOMPLETE", subject, "$.device_slot_coverage", "coverage and exact device slots must be total and equal")
    if len(facet_keys) != len(set(facet_keys)) or set(facet_keys) != _instrument_facets(instrument):
        _diagnostic(diagnostics, "GILLS_INSTRUMENT_COVERAGE_INCOMPLETE", subject, "$.instrument_facet_coverage", "coverage and exact public instrument facets must be total and equal")
    semantic_ids = _mapping_ids(instrument)
    runtime_ids = {
        ("runtime", binding["binding_id"])
        for runtime in runtimes
        if runtime["device_profile_reference"] == coverage["device_profile_reference"]
        and any(item["instrument_reference"] == coverage["instrument_reference"] for item in runtime["supported_builds"])
        for collection in ("input_bindings", "feedback_bindings", "display_bindings", "physical_io_bindings")
        for binding in runtime[collection]
    }
    for collection in ("device_slot_coverage", "instrument_facet_coverage"):
        for index, item in enumerate(coverage[collection]):
            refs = {(value["mapping_kind"], value["mapping_id"]) for value in item["mapping_refs"]}
            if item["outcome"] == "mapped" and not refs:
                _diagnostic(diagnostics, "GILLS_MAPPED_COVERAGE_EMPTY", subject, f"$.{collection}[{index}]", "mapped coverage requires at least one exact mapping reference")
            if item["outcome"] != "mapped" and refs:
                _diagnostic(diagnostics, "GILLS_UNMAPPED_COVERAGE_HAS_MAPPING", subject, f"$.{collection}[{index}]", "unused or unresolved coverage cannot cite a mapping")
            if not refs <= semantic_ids | runtime_ids:
                _diagnostic(diagnostics, "GILLS_COVERAGE_MAPPING_UNRESOLVED", subject, f"$.{collection}[{index}].mapping_refs", "coverage mapping reference does not resolve in the exact instrument/runtime closure")
    outcomes = Counter(item["outcome"] for item in coverage["device_slot_coverage"] + coverage["instrument_facet_coverage"])
    expected_summary = {
        "device_slots_total": len(device_keys), "instrument_facets_total": len(facet_keys),
        "mapped": outcomes["mapped"], "intentionally_unused": outcomes["intentionally-unused"],
        "unresolved": outcomes["unresolved"], "absence_is_coverage": False,
    }
    if coverage["summary"] != expected_summary:
        _diagnostic(diagnostics, "GILLS_COVERAGE_SUMMARY_MISMATCH", subject, "$.summary", "coverage summary does not equal the exact entry outcomes")


def validate_values(
    groups: dict[str, list[dict[str, Any]]], schemas: dict[str, dict[str, Any]],
    domain_records: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    """Validate one explicit Task 018 in-memory closure without I/O."""

    diagnostics: list[core.Diagnostic] = []
    if not any(groups.values()):
        return {
            "schema_version": "task018-validation-summary-v0", "status": "not-applicable",
            "record_counts": {key: 0 for key in SCHEMA_SPECS}, "diagnostics": [],
            "evidence_levels": [{"level": level, "status": "not-run"} for level in range(1, 9)],
        }
    valid = _validate_structural(groups, schemas, diagnostics)
    devices = _registry(domain_records["devices"], "device_profile_id")
    instruments = _registry(domain_records["instruments"], "instrument_id")
    requests = _registry(domain_records["request"], "build_request_id")
    targets = _registry(domain_records["target"], "compute_target_id")
    backends = _registry(domain_records["backend"], "backend_id")
    environments = _registry(domain_records["environment"], "build_environment_id")
    panels = _registry(valid["panel_evidence"], "panel_evidence_packet_id")
    for panel in valid["panel_evidence"]:
        _validate_panel(panel, devices, diagnostics)
    for runtime in valid["runtime_realizations"]:
        _validate_runtime(runtime, devices, panels, instruments, requests, targets, backends, environments, diagnostics)
    for coverage in valid["mapping_coverage"]:
        _validate_coverage(coverage, devices, panels, instruments, valid["runtime_realizations"], diagnostics)

    successor_instruments = {
        key for key in instruments if key[0] in {"schuss-instrument-000002", "schuss-instrument-000003", "schuss-instrument-000004"} and key[1] == 2
    }
    covered_instruments = {_ref(item["instrument_reference"], "instrument_id") for item in valid["mapping_coverage"]}
    runtime_instruments = {_ref(item["instrument_reference"], "instrument_id") for runtime in valid["runtime_realizations"] for item in runtime["supported_builds"]}
    for actual, code, location in (
        (covered_instruments, "GILLS_SUCCESSOR_COVERAGE_INCOMPLETE", "$.mapping_coverage"),
        (runtime_instruments, "GILLS_SUCCESSOR_RUNTIME_INCOMPLETE", "$.runtime_realizations"),
    ):
        if actual != successor_instruments:
            _diagnostic(diagnostics, code, "task018", location, "all and only the three exact Task 018 instrument successors must be present")
    mapped_handlers = [item for runtime in valid["runtime_realizations"] for item in runtime["supported_builds"] if item["handler"]["status"] == "supported"]
    if len(mapped_handlers) != 1 or mapped_handlers[0]["instrument_reference"]["instrument_id"] != "schuss-instrument-000002":
        _diagnostic(diagnostics, "GILLS_EXECUTABLE_PROMOTION_CLOSURE_INVALID", "task018", "$.runtime_realizations", "exactly one mapped Task 016 successor must name a supported handler")

    diagnostics = sorted(set(diagnostics), key=core.diagnostic_sort_key)
    status = "invalid" if diagnostics else "valid"
    return {
        "schema_version": "task018-validation-summary-v0", "status": status,
        "record_counts": {key: len(groups[key]) for key in SCHEMA_SPECS},
        "successor_instruments": len(successor_instruments),
        "coverage_complete": not any(item.code in {"GILLS_DEVICE_COVERAGE_INCOMPLETE", "GILLS_INSTRUMENT_COVERAGE_INCOMPLETE"} for item in diagnostics),
        "runtime_closures": len(valid["runtime_realizations"]),
        "evidence_levels": [{"level": level, "status": "passed" if level <= 2 and not diagnostics else "not-run" if level > 2 else "failed"} for level in range(1, 9)],
        "diagnostics": [item.as_dict() for item in diagnostics],
    }
