#!/usr/bin/env python3
"""Device and instrument domain rules."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable

import validator_core as core


DEVICE_SCHEMA_NAME = "device-profile-v0.schema.json"
INSTRUMENT_SCHEMA_NAME = "instrument-v0.schema.json"
DEVICE_SCHEMA_VERSION = "device-profile-v0"
INSTRUMENT_SCHEMA_VERSION = "instrument-v0"

# Compatibility aliases are intentionally bound to the shared core. Domain
# policy below uses these mechanisms but does not reimplement them.
DuplicateJsonMemberError = core.DuplicateJsonMemberError
Diagnostic = core.Diagnostic
canonical_json = core.canonical_json
_object_pairs = core.object_pairs
_reject_float = core.reject_float
_parse_int = core.parse_int
load_json = core.load_json
_assert_portable_json_value = core.assert_portable_json_value
_resolve_schema = core.resolve_schema
_json_type_matches = core.json_type_matches
_schema_errors = core.schema_errors
validate_schema_annotations = core.validate_schema_annotations
_matching_one_of = core.matching_one_of
_canonicalize_with_schema = core.canonicalize_with_schema
canonical_record_bytes = core.canonical_record_bytes
record_content_hash = core.record_content_hash
_scan_portability = core.scan_portability


def _record_subject(record: dict[str, Any]) -> str:
    if "device_profile_id" in record:
        return f"{record.get('device_profile_id', '<unknown>')}@{record.get('revision', '?')}"
    return f"{record.get('instrument_id', '<unknown>')}@{record.get('revision', '?')}"


def _diagnostic(
    diagnostics: list[Diagnostic],
    code: str,
    subject: str,
    location: str,
    message: str,
    severity: str = "error",
) -> None:
    core.add_diagnostic(diagnostics, code, subject, location, message, severity)


def _decimal(value: str) -> Decimal:
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError) as exc:
        raise ValueError(f"invalid exact decimal {value!r}") from exc


def _range_tuple(value: dict[str, Any]) -> tuple[Decimal, Decimal, str]:
    return _decimal(value["minimum"]), _decimal(value["maximum"]), value["unit"]


def _validate_range(
    value: dict[str, Any], subject: str, location: str, diagnostics: list[Diagnostic]
) -> None:
    minimum, maximum, _ = _range_tuple(value)
    if minimum >= maximum:
        _diagnostic(
            diagnostics,
            "RANGE_INVALID",
            subject,
            location,
            "range minimum must be less than maximum",
        )


def _validate_transform(
    source_domain: dict[str, Any],
    destination_domain: dict[str, Any],
    transform: dict[str, Any],
    subject: str,
    location: str,
    diagnostics: list[Diagnostic],
) -> None:
    source_min, source_max, source_unit = _range_tuple(source_domain)
    destination_min, destination_max, destination_unit = _range_tuple(destination_domain)
    points = transform["points"]
    point_sources = [_decimal(point["source"]) for point in points]
    point_destinations = [_decimal(point["destination"]) for point in points]
    if point_sources != [source_min, source_max]:
        _diagnostic(
            diagnostics,
            "MAPPING_TRANSFORM_INCOMPATIBLE",
            subject,
            location,
            "ordered transform source endpoints must equal the declared source domain",
        )
    expected_destinations = (
        [destination_min, destination_max]
        if transform["polarity"] == "direct"
        else [destination_max, destination_min]
    )
    if point_destinations != expected_destinations:
        _diagnostic(
            diagnostics,
            "MAPPING_TRANSFORM_INCOMPATIBLE",
            subject,
            location,
            "ordered transform destination endpoints do not match range and polarity",
        )
    if source_unit != destination_unit:
        _diagnostic(
            diagnostics,
            "MAPPING_TRANSFORM_INCOMPATIBLE",
            subject,
            location,
            "v0 linear mappings cannot silently change units",
        )


def _local_id_maps(device: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    return {
        "input-control": {item["slot_id"]: item for item in device["input_controls"]},
        "gesture": {item["gesture_id"]: item for item in device["gestures"]},
        "feedback-output": {item["slot_id"]: item for item in device["feedback_outputs"]},
        "display": {item["slot_id"]: item for item in device["displays"]},
        "physical-io": {item["slot_id"]: item for item in device["physical_io"]},
    }


def _instrument_facet_maps(instrument: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    return {
        "parameter": {item["facet_id"]: item for item in instrument["parameters"]},
        "action": {item["facet_id"]: item for item in instrument["actions"]},
        "display": {item["facet_id"]: item for item in instrument["displays"]},
        "state": {item["state_id"]: item for item in instrument["state_declarations"]},
    }


def _validate_unique_ids(
    records: Iterable[tuple[str, str]],
    subject: str,
    location: str,
    diagnostics: list[Diagnostic],
) -> None:
    seen: dict[str, str] = {}
    for kind, identifier in records:
        if identifier in seen:
            _diagnostic(
                diagnostics,
                "DUPLICATE_LOCAL_ID",
                subject,
                location,
                f"{identifier!r} is reused by {seen[identifier]} and {kind}",
            )
        else:
            seen[identifier] = kind


def _validate_device_semantics(device: dict[str, Any], diagnostics: list[Diagnostic]) -> None:
    subject = _record_subject(device)
    maps = _local_id_maps(device)
    local_ids: list[tuple[str, str]] = []
    for kind, values in maps.items():
        local_ids.extend((kind, identifier) for identifier in values)
    _validate_unique_ids(local_ids, subject, "$", diagnostics)

    expected_control_shapes = {
        ("absolute", "knob"): ("normalized-position", "normalized"),
        ("relative", "encoder"): ("relative-step", "steps"),
        ("discrete", "button"): ("binary-state", "boolean"),
        ("discrete", "switch"): ("binary-state", "boolean"),
    }
    unresolved = {item["fact_id"]: item for item in device["unresolved_facts"]}
    if len(unresolved) != len(device["unresolved_facts"]):
        _diagnostic(
            diagnostics,
            "DUPLICATE_LOCAL_ID",
            subject,
            "$.unresolved_facts",
            "unresolved fact IDs must be unique",
        )

    def validate_unresolved_link(value: dict[str, Any], location: str, affected: str) -> None:
        if value["status"] != "unresolved":
            return
        fact_id = value["unresolved_fact_id"]
        fact = unresolved.get(fact_id)
        if fact is None:
            _diagnostic(
                diagnostics,
                "UNRESOLVED_FACT_UNKNOWN",
                subject,
                location,
                f"unresolved fact {fact_id!r} is not declared",
            )
        elif affected not in fact["affected_subjects"]:
            _diagnostic(
                diagnostics,
                "UNRESOLVED_FACT_SCOPE_MISMATCH",
                subject,
                location,
                f"{fact_id!r} does not name affected subject {affected!r}",
            )

    for index, control in enumerate(device["input_controls"]):
        location = f"$.input_controls[{index}]"
        expected = expected_control_shapes.get((control["control_kind"], control["physical_form"]))
        if expected is None or (control["output_domain"], control["logical_range"]["unit"]) != expected:
            _diagnostic(
                diagnostics,
                "CONTROL_SHAPE_INCOMPATIBLE",
                subject,
                location,
                "control kind, form, output domain, and logical unit are incompatible",
            )
        _validate_range(control["logical_range"], subject, f"{location}.logical_range", diagnostics)
        affected = f"input-control:{control['slot_id']}"
        validate_unresolved_link(control["physical_range"], f"{location}.physical_range", affected)
        validate_unresolved_link(control["resolution"], f"{location}.resolution", affected)
        if control["physical_range"]["status"] == "known":
            _validate_range(
                control["physical_range"]["range"],
                subject,
                f"{location}.physical_range.range",
                diagnostics,
            )

    for index, gesture in enumerate(device["gestures"]):
        location = f"$.gestures[{index}]"
        for source_id in gesture["source_control_ids"]:
            if source_id not in maps["input-control"]:
                _diagnostic(
                    diagnostics,
                    "GESTURE_SOURCE_UNKNOWN",
                    subject,
                    f"{location}.source_control_ids",
                    f"gesture source {source_id!r} is not an input control",
                )
        validate_unresolved_link(
            gesture["recognition"],
            f"{location}.recognition",
            f"gesture:{gesture['gesture_id']}",
        )

        expected_capability = {
            "press": "edge-detected-gesture",
            "release": "edge-detected-gesture",
            "hold": "hold-duration-gesture",
            "turn": "relative-turn-gesture",
        }[gesture["gesture_kind"]]
        if (
            gesture["recognition"]["status"] == "known"
            and gesture["recognition"]["capability"] != expected_capability
        ):
            _diagnostic(
                diagnostics,
                "CONTROL_SHAPE_INCOMPATIBLE",
                subject,
                f"{location}.recognition",
                "gesture kind and known recognition capability are incompatible",
            )

    for collection, kind, field in (
        ("feedback_outputs", "feedback-output", "capability"),
        ("displays", "display", "capability"),
        ("physical_io", "physical-io", "capability"),
    ):
        for index, item in enumerate(device[collection]):
            validate_unresolved_link(
                item[field],
                f"$.{collection}[{index}].{field}",
                f"{kind}:{item['slot_id']}",
            )

    expected_feedback_capabilities = {
        "indicator": "binary-indicator-output",
        "haptic": "haptic-output",
    }
    for index, item in enumerate(device["feedback_outputs"]):
        if (
            item["capability"]["status"] == "known"
            and item["capability"]["capability"]
            != expected_feedback_capabilities[item["feedback_kind"]]
        ):
            _diagnostic(
                diagnostics,
                "CONTROL_SHAPE_INCOMPATIBLE",
                subject,
                f"$.feedback_outputs[{index}].capability",
                "feedback kind and known capability are incompatible",
            )

    expected_display_capabilities = {
        "text": "text-output",
        "graphics": "graphics-output",
    }
    for index, item in enumerate(device["displays"]):
        if (
            item["capability"]["status"] == "known"
            and item["capability"]["capability"]
            != expected_display_capabilities[item["display_kind"]]
        ):
            _diagnostic(
                diagnostics,
                "CONTROL_SHAPE_INCOMPATIBLE",
                subject,
                f"$.displays[{index}].capability",
                "display kind and known capability are incompatible",
            )

    expected_io_capabilities = {
        "audio": "audio-signal",
        "midi": "midi-messages",
        "cv": "cv-voltage",
        "generic": "generic-io",
    }
    for index, item in enumerate(device["physical_io"]):
        if (
            item["capability"]["status"] == "known"
            and item["capability"]["capability"]
            != expected_io_capabilities[item["io_kind"]]
        ):
            _diagnostic(
                diagnostics,
                "CONTROL_SHAPE_INCOMPATIBLE",
                subject,
                f"$.physical_io[{index}].capability",
                "physical-I/O kind and known capability are incompatible",
            )


def _validate_instrument_semantics(
    instrument: dict[str, Any],
    devices_by_exact_ref: dict[tuple[str, int, str], dict[str, Any]],
    diagnostics: list[Diagnostic],
    graph_targets_by_exact_ref: dict[
        tuple[str, int, str], dict[str, dict[str, Any]]
    ]
    | None = None,
) -> None:
    subject = _record_subject(instrument)
    facets = _instrument_facet_maps(instrument)
    local_ids: list[tuple[str, str]] = []
    for kind, values in facets.items():
        local_ids.extend((kind, identifier) for identifier in values)
    mapping_ids: list[tuple[str, str]] = []
    for collection in ("device_input_mappings", "device_feedback_mappings", "graph_mappings"):
        mapping_ids.extend((collection, item["mapping_id"]) for item in instrument[collection])
    _validate_unique_ids(local_ids + mapping_ids, subject, "$", diagnostics)

    for index, parameter in enumerate(instrument["parameters"]):
        location = f"$.parameters[{index}]"
        _validate_range(parameter["domain"], subject, f"{location}.domain", diagnostics)
        minimum, maximum, _ = _range_tuple(parameter["domain"])
        default = _decimal(parameter["default"])
        if not minimum <= default <= maximum:
            _diagnostic(
                diagnostics,
                "PARAMETER_DEFAULT_OUT_OF_RANGE",
                subject,
                f"{location}.default",
                "parameter default is outside its domain",
            )

    reference = instrument["device_profile_reference"]
    device_key = (
        reference["device_profile_id"],
        reference["revision"],
        reference["content_hash"],
    )
    device = devices_by_exact_ref.get(device_key)
    if device is None:
        _diagnostic(
            diagnostics,
            "DEVICE_REFERENCE_UNRESOLVED",
            subject,
            "$.device_profile_reference",
            "the exact device-profile ID/revision/hash tuple did not resolve",
        )
        return

    device_maps = _local_id_maps(device)
    graph_reference = instrument["graph_reference"]
    graph_targets: dict[str, dict[str, Any]] = {}
    if graph_reference["status"] == "resolved":
        graph_key = (
            graph_reference["graph_id"],
            graph_reference["revision"],
            graph_reference["content_hash"],
        )
        resolved_targets = (
            graph_targets_by_exact_ref.get(graph_key)
            if graph_targets_by_exact_ref is not None
            else None
        )
        if resolved_targets is None:
            _diagnostic(
                diagnostics,
                "GRAPH_RESOLUTION_UNAVAILABLE",
                subject,
                "$.graph_reference",
                "the exact graph tuple did not resolve through an accepted graph registry",
            )
        else:
            graph_targets = resolved_targets
    else:
        for target in graph_reference["declared_targets"]:
            if target["facet_id"] in graph_targets:
                _diagnostic(
                    diagnostics,
                    "DUPLICATE_LOCAL_ID",
                    subject,
                    "$.graph_reference.declared_targets",
                    f"deferred graph target {target['facet_id']!r} is duplicated",
                )
            graph_targets[target["facet_id"]] = target

    driven_device_destinations: set[tuple[str, str]] = set()
    for index, mapping in enumerate(instrument["device_input_mappings"]):
        location = f"$.device_input_mappings[{index}]"
        source = mapping["source"]
        destination = mapping["destination"]
        if mapping["mapping_kind"] == "parameter-control":
            source_item = device_maps["input-control"].get(source["slot_id"])
            if source_item is None:
                _diagnostic(
                    diagnostics,
                    "MAPPING_SOURCE_UNKNOWN",
                    subject,
                    f"{location}.source",
                    f"device input {source['slot_id']!r} does not exist",
                )
            destination_item = facets.get(destination["facet_kind"], {}).get(destination["facet_id"])
            if destination["facet_kind"] != "parameter":
                _diagnostic(
                    diagnostics,
                    "MAPPING_FACET_KIND_MISMATCH",
                    subject,
                    f"{location}.destination",
                    "parameter-control mappings must target an instrument parameter",
                )
            elif destination_item is None:
                _diagnostic(
                    diagnostics,
                    "MAPPING_DESTINATION_UNKNOWN",
                    subject,
                    f"{location}.destination",
                    f"instrument parameter {destination['facet_id']!r} does not exist",
                )
            if source_item is not None and mapping["source_domain"] != source_item["logical_range"]:
                _diagnostic(
                    diagnostics,
                    "MAPPING_DOMAIN_REDEFINITION",
                    subject,
                    f"{location}.source_domain",
                    "mapping source domain differs from the device control domain",
                )
            if destination_item is not None and mapping["destination_domain"] != destination_item["domain"]:
                _diagnostic(
                    diagnostics,
                    "MAPPING_DOMAIN_REDEFINITION",
                    subject,
                    f"{location}.destination_domain",
                    "mapping destination domain differs from the instrument parameter domain",
                )
            _validate_range(mapping["source_domain"], subject, f"{location}.source_domain", diagnostics)
            _validate_range(
                mapping["destination_domain"],
                subject,
                f"{location}.destination_domain",
                diagnostics,
            )
            _validate_transform(
                mapping["source_domain"],
                mapping["destination_domain"],
                mapping["transform"],
                subject,
                f"{location}.transform",
                diagnostics,
            )
        else:
            if source["gesture_id"] not in device_maps["gesture"]:
                _diagnostic(
                    diagnostics,
                    "MAPPING_SOURCE_UNKNOWN",
                    subject,
                    f"{location}.source",
                    f"device gesture {source['gesture_id']!r} does not exist",
                )
            if destination["facet_id"] not in facets["action"]:
                _diagnostic(
                    diagnostics,
                    "MAPPING_DESTINATION_UNKNOWN",
                    subject,
                    f"{location}.destination",
                    f"instrument action {destination['facet_id']!r} does not exist",
                )
        destination_key = (destination["facet_kind"], destination["facet_id"])
        if destination_key in driven_device_destinations:
            _diagnostic(
                diagnostics,
                "DUPLICATE_DRIVER",
                subject,
                f"{location}.destination",
                "instrument facet has more than one device-input driver",
            )
        driven_device_destinations.add(destination_key)

    feedback_destinations: set[tuple[str, str]] = set()
    for index, mapping in enumerate(instrument["device_feedback_mappings"]):
        location = f"$.device_feedback_mappings[{index}]"
        source = mapping["source"]
        destination = mapping["destination"]
        if source["facet_id"] not in facets[source["facet_kind"]]:
            _diagnostic(
                diagnostics,
                "MAPPING_SOURCE_UNKNOWN",
                subject,
                f"{location}.source",
                f"instrument {source['facet_kind']} {source['facet_id']!r} does not exist",
            )
        if destination["slot_id"] not in device_maps[destination["slot_kind"]]:
            _diagnostic(
                diagnostics,
                "MAPPING_DESTINATION_UNKNOWN",
                subject,
                f"{location}.destination",
                f"device {destination['slot_kind']} {destination['slot_id']!r} does not exist",
            )
        destination_key = (destination["slot_kind"], destination["slot_id"])
        if destination_key in feedback_destinations:
            _diagnostic(
                diagnostics,
                "DUPLICATE_DRIVER",
                subject,
                f"{location}.destination",
                "device feedback slot has more than one instrument driver",
            )
        feedback_destinations.add(destination_key)

    graph_destinations: set[tuple[str, str]] = set()
    for index, mapping in enumerate(instrument["graph_mappings"]):
        location = f"$.graph_mappings[{index}]"
        source = mapping["source"]
        destination = mapping["destination"]
        source_item = facets.get(source["facet_kind"], {}).get(source["facet_id"])
        if source_item is None:
            _diagnostic(
                diagnostics,
                "MAPPING_SOURCE_UNKNOWN",
                subject,
                f"{location}.source",
                f"instrument {source['facet_kind']} {source['facet_id']!r} does not exist",
            )
        target = graph_targets.get(destination["facet_id"])
        if target is None:
            _diagnostic(
                diagnostics,
                "GRAPH_TARGET_NOT_DECLARED",
                subject,
                f"{location}.destination",
                "graph target is absent from the closed deferred-target declaration",
            )
        elif target["facet_kind"] != destination["facet_kind"]:
            _diagnostic(
                diagnostics,
                "MAPPING_FACET_KIND_MISMATCH",
                subject,
                f"{location}.destination",
                "graph target facet kind disagrees with the deferred declaration",
            )
        elif (
            mapping["mapping_kind"] != "action-to-action"
            and "domain" in target
            and mapping["destination_domain"] != target["domain"]
        ):
            _diagnostic(
                diagnostics,
                "MAPPING_DOMAIN_REDEFINITION",
                subject,
                f"{location}.destination_domain",
                "graph mapping destination domain differs from the resolved graph facet domain",
            )
        expected_destination_kind = {
            "parameter-to-parameter": "parameter",
            "parameter-to-port": "port",
            "action-to-action": "action",
        }[mapping["mapping_kind"]]
        if destination["facet_kind"] != expected_destination_kind:
            _diagnostic(
                diagnostics,
                "MAPPING_FACET_KIND_MISMATCH",
                subject,
                f"{location}.destination",
                f"{mapping['mapping_kind']} must end at a graph {expected_destination_kind}",
            )
        if mapping["mapping_kind"] != "action-to-action":
            if source_item is not None and mapping["source_domain"] != source_item["domain"]:
                _diagnostic(
                    diagnostics,
                    "MAPPING_DOMAIN_REDEFINITION",
                    subject,
                    f"{location}.source_domain",
                    "graph mapping source domain differs from the instrument parameter domain",
                )
            _validate_range(
                mapping["source_domain"],
                subject,
                f"{location}.source_domain",
                diagnostics,
            )
            _validate_range(
                mapping["destination_domain"],
                subject,
                f"{location}.destination_domain",
                diagnostics,
            )
            _validate_transform(
                mapping["source_domain"],
                mapping["destination_domain"],
                mapping["transform"],
                subject,
                f"{location}.transform",
                diagnostics,
            )
        destination_key = (destination["facet_kind"], destination["facet_id"])
        if destination_key in graph_destinations:
            _diagnostic(
                diagnostics,
                "DUPLICATE_DRIVER",
                subject,
                f"{location}.destination",
                "graph public facet has more than one instrument driver",
            )
        graph_destinations.add(destination_key)


def _identity_collisions(
    records: list[dict[str, Any]],
    id_field: str,
    diagnostics: list[Diagnostic],
) -> None:
    seen: dict[tuple[str, int], str] = {}
    for record in records:
        key = (record[id_field], record["revision"])
        content_hash = record["content_hash"]
        if key in seen:
            code = "ID_REVISION_COLLISION" if seen[key] != content_hash else "DUPLICATE_RECORD"
            _diagnostic(
                diagnostics,
                code,
                f"{key[0]}@{key[1]}",
                "$",
                "one stable-ID/revision pair must occur once and resolve to one hash",
            )
        else:
            seen[key] = content_hash


def validate_contract_values(
    device_records: list[dict[str, Any]],
    instrument_records: list[dict[str, Any]],
    device_schema: dict[str, Any],
    instrument_schema: dict[str, Any],
    graph_targets_by_exact_ref: dict[
        tuple[str, int, str], dict[str, dict[str, Any]]
    ]
    | None = None,
) -> dict[str, Any]:
    """Validate records and return one deterministic structured summary."""

    diagnostics: list[Diagnostic] = []
    for name, schema in ((DEVICE_SCHEMA_NAME, device_schema), (INSTRUMENT_SCHEMA_NAME, instrument_schema)):
        for error in validate_schema_annotations(schema):
            _diagnostic(
                diagnostics,
                "SCHEMA_CONTRACT_INVALID",
                name,
                "$",
                error,
            )

    structurally_valid_devices: list[dict[str, Any]] = []
    structurally_valid_instruments: list[dict[str, Any]] = []
    for records, schema, expected_version, valid_records in (
        (device_records, device_schema, DEVICE_SCHEMA_VERSION, structurally_valid_devices),
        (instrument_records, instrument_schema, INSTRUMENT_SCHEMA_VERSION, structurally_valid_instruments),
    ):
        for record in records:
            subject = _record_subject(record)
            _scan_portability(record, subject, diagnostics)
            errors = _schema_errors(record, schema, schema)
            for error in errors:
                _diagnostic(
                    diagnostics,
                    "SCHEMA_STRUCTURE_INVALID",
                    subject,
                    "$",
                    error,
                )
            if not errors and record.get("schema_version") == expected_version:
                valid_records.append(record)

    _identity_collisions(structurally_valid_devices, "device_profile_id", diagnostics)
    _identity_collisions(structurally_valid_instruments, "instrument_id", diagnostics)

    for device in structurally_valid_devices:
        _validate_device_semantics(device, diagnostics)
    for record, schema in (
        *((record, device_schema) for record in structurally_valid_devices),
        *((record, instrument_schema) for record in structurally_valid_instruments),
    ):
        expected = record_content_hash(record, schema)
        if record["content_hash"] != expected:
            _diagnostic(
                diagnostics,
                "CONTENT_HASH_MISMATCH",
                _record_subject(record),
                "$.content_hash",
                f"expected {expected}",
            )

    devices_by_exact_ref = {
        (record["device_profile_id"], record["revision"], record["content_hash"]): record
        for record in structurally_valid_devices
        if record["content_hash"] == record_content_hash(record, device_schema)
    }
    for instrument in structurally_valid_instruments:
        _validate_instrument_semantics(
            instrument,
            devices_by_exact_ref,
            diagnostics,
            graph_targets_by_exact_ref,
        )

    diagnostics = sorted(
        set(diagnostics),
        key=lambda item: (item.severity, item.code, item.subject, item.location, item.message),
    )
    error_count = sum(item.severity == "error" for item in diagnostics)
    deferred_graph_count = sum(
        record.get("graph_reference", {}).get("status") == "deferred"
        for record in structurally_valid_instruments
    )
    resolved_graph_count = sum(
        (
            record["graph_reference"]["graph_id"],
            record["graph_reference"]["revision"],
            record["graph_reference"]["content_hash"],
        )
        in (graph_targets_by_exact_ref or {})
        for record in structurally_valid_instruments
        if record.get("graph_reference", {}).get("status") == "resolved"
    )
    resolved_device_count = sum(
        (
            record["device_profile_reference"]["device_profile_id"],
            record["device_profile_reference"]["revision"],
            record["device_profile_reference"]["content_hash"],
        )
        in devices_by_exact_ref
        for record in structurally_valid_instruments
    )
    status = "invalid" if error_count else (
        "valid-with-deferred-graph" if deferred_graph_count else "valid"
    )
    graph_resolution_status = "failed" if error_count else (
        "deferred" if deferred_graph_count else "not-applicable"
    )
    return {
        "schema_version": "device-instrument-validation-summary-v0",
        "status": status,
        "record_counts": {
            "device_profiles": len(device_records),
            "instruments": len(instrument_records),
        },
        "reference_resolution": {
            "device_profiles_resolved": resolved_device_count,
            "graphs_deferred": deferred_graph_count,
            "graphs_resolved": resolved_graph_count,
        },
        "evidence_levels": [
            {"level": "structural-schema", "status": "failed" if error_count else "passed"},
            {
                "level": "component-graph-resolution",
                "status": (
                    "failed"
                    if error_count
                    else "deferred"
                    if deferred_graph_count
                    else "passed"
                    if resolved_graph_count
                    else graph_resolution_status
                ),
            },
            {"level": "backend-lowering", "status": "not-run"},
            {"level": "artifact-generation", "status": "not-run"},
            {"level": "arm-compile-link", "status": "not-run"},
            {"level": "connected-device", "status": "not-run"},
            {"level": "real-time-resource", "status": "not-run"},
            {"level": "audible-listening", "status": "not-run"},
        ],
        "diagnostics": [item.as_dict() for item in diagnostics],
    }

