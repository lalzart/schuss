#!/usr/bin/env python3
"""Read-only validation for Schuss device-profile-v0 and instrument-v0 records."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import re
import sys
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable


DEVICE_SCHEMA_NAME = "device-profile-v0.schema.json"
INSTRUMENT_SCHEMA_NAME = "instrument-v0.schema.json"
DEVICE_SCHEMA_VERSION = "device-profile-v0"
INSTRUMENT_SCHEMA_VERSION = "instrument-v0"
MAX_IJSON_INTEGER = 9_007_199_254_740_991

ABSOLUTE_PATH_RE = re.compile(r"^(?:/|[A-Za-z]:[\\/])|(?:^|[\\/])(?:Users|home|tmp|private/tmp)[\\/]")
TIMESTAMP_RE = re.compile(
    r"(?:^|[^0-9])\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})(?:$|[^0-9])"
)
UUID_RE = re.compile(
    r"(?:^|[^0-9A-Fa-f])[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[1-5][0-9A-Fa-f]{3}-[89AaBb][0-9A-Fa-f]{3}-[0-9A-Fa-f]{12}(?:$|[^0-9A-Fa-f])"
)


class DuplicateJsonMemberError(ValueError):
    """A JSON object repeated a member name and therefore is not I-JSON."""


@dataclass(frozen=True)
class Diagnostic:
    code: str
    severity: str
    subject: str
    location: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "location": self.location,
            "message": self.message,
            "severity": self.severity,
            "subject": self.subject,
        }


def canonical_json(value: Any) -> str:
    """Serialize the restricted Schuss/I-JSON value space in canonical form."""

    _assert_portable_json_value(value)
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise DuplicateJsonMemberError(f"duplicate JSON member {key!r}")
        value[key] = item
    return value


def _reject_float(text: str) -> None:
    raise ValueError(f"JSON floating-point number {text!r} is outside the restricted profile")


def _parse_int(text: str) -> int:
    value = int(text)
    if abs(value) > MAX_IJSON_INTEGER:
        raise ValueError(f"JSON integer {text!r} exceeds the exact I-JSON range")
    return value


def load_json(path: Path) -> Any:
    """Load LF-terminated UTF-8 JSON while rejecting duplicate keys and floats."""

    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf") or b"\r" in data:
        raise ValueError(f"{path}: expected UTF-8 without BOM and LF line endings")
    if not data.endswith(b"\n"):
        raise ValueError(f"{path}: expected a final LF")
    try:
        return json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_object_pairs,
            parse_float=_reject_float,
            parse_int=_parse_int,
            parse_constant=lambda text: (_ for _ in ()).throw(
                ValueError(f"non-finite JSON number {text!r} is prohibited")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError, DuplicateJsonMemberError, ValueError) as exc:
        raise ValueError(f"{path}: invalid restricted JSON: {exc}") from exc


def _assert_portable_json_value(value: Any, location: str = "$") -> None:
    if value is None or isinstance(value, bool) or isinstance(value, str):
        return
    if isinstance(value, int):
        if abs(value) > MAX_IJSON_INTEGER:
            raise ValueError(f"{location}: integer exceeds the exact I-JSON range")
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{location}: non-finite number is prohibited")
        raise ValueError(f"{location}: floating-point numbers are outside the restricted profile")
    if isinstance(value, list):
        for index, item in enumerate(value):
            _assert_portable_json_value(item, f"{location}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{location}: object member names must be strings")
            _assert_portable_json_value(item, f"{location}.{key}")
        return
    raise ValueError(f"{location}: unsupported value type {type(value).__name__}")


def _resolve_schema(schema: dict[str, Any], root_schema: dict[str, Any]) -> dict[str, Any]:
    while "$ref" in schema:
        reference = schema["$ref"]
        if not isinstance(reference, str) or not reference.startswith("#/"):
            raise ValueError(f"unsupported schema reference {reference!r}")
        target: Any = root_schema
        for token in reference[2:].split("/"):
            token = token.replace("~1", "/").replace("~0", "~")
            if not isinstance(target, dict) or token not in target:
                raise ValueError(f"unresolved schema reference {reference!r}")
            target = target[token]
        if not isinstance(target, dict):
            raise ValueError(f"schema reference {reference!r} is not an object")
        schema = target
    return schema


def _json_type_matches(value: Any, expected: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }.get(expected, False)


def _schema_errors(
    value: Any,
    schema: dict[str, Any],
    root_schema: dict[str, Any],
    location: str = "$",
) -> list[str]:
    schema = _resolve_schema(schema, root_schema)
    errors: list[str] = []

    if "oneOf" in schema:
        branches = schema["oneOf"]
        matches = [
            branch
            for branch in branches
            if not _schema_errors(value, branch, root_schema, location)
        ]
        if len(matches) != 1:
            errors.append(f"{location}: expected exactly one schema alternative, matched {len(matches)}")
        return errors

    if "const" in schema and value != schema["const"]:
        errors.append(f"{location}: expected {schema['const']!r}, got {value!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{location}: value {value!r} is outside the controlled vocabulary")

    expected = schema.get("type")
    if expected is not None and not _json_type_matches(value, expected):
        errors.append(f"{location}: expected {expected}, got {type(value).__name__}")
        return errors

    if isinstance(value, dict):
        required = set(schema.get("required", []))
        missing = sorted(required - set(value))
        if missing:
            errors.append(f"{location}: missing properties {missing}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            unexpected = sorted(set(value) - set(properties))
            if unexpected:
                errors.append(f"{location}: unexpected properties {unexpected}")
        for key in sorted(value):
            if key in properties:
                errors.extend(
                    _schema_errors(value[key], properties[key], root_schema, f"{location}.{key}")
                )

    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{location}: too few items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(f"{location}: too many items")
        if schema.get("uniqueItems"):
            encoded = [canonical_json(item) for item in value]
            if len(encoded) != len(set(encoded)):
                errors.append(f"{location}: duplicate items")
        if "items" in schema:
            for index, item in enumerate(value):
                errors.extend(
                    _schema_errors(item, schema["items"], root_schema, f"{location}[{index}]")
                )

    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{location}: string is too short")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            errors.append(f"{location}: string does not match {schema['pattern']!r}")

    if isinstance(value, int) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{location}: value is below minimum {schema['minimum']}")

    return errors


def validate_schema_annotations(schema: dict[str, Any]) -> list[str]:
    """Check that every array in these schemas declares set or sequence semantics."""

    errors: list[str] = []
    visited: set[int] = set()

    def visit(node: Any, location: str) -> None:
        if not isinstance(node, dict) or id(node) in visited:
            return
        visited.add(id(node))
        if node.get("type") == "object" and node.get("additionalProperties") is not False:
            errors.append(f"{location}: object schema is not closed")
        if node.get("type") == "array":
            if node.get("x-schuss-array-kind") not in {"set", "sequence"}:
                errors.append(f"{location}: array lacks x-schuss-array-kind")
        for key in ("properties", "$defs"):
            for name, child in node.get(key, {}).items():
                visit(child, f"{location}.{key}.{name}")
        if "items" in node:
            visit(node["items"], f"{location}.items")
        for index, child in enumerate(node.get("oneOf", [])):
            visit(child, f"{location}.oneOf[{index}]")

    visit(schema, "$")
    return sorted(errors)


def _matching_one_of(
    value: Any, schema: dict[str, Any], root_schema: dict[str, Any]
) -> dict[str, Any]:
    matches = [
        branch
        for branch in schema["oneOf"]
        if not _schema_errors(value, branch, root_schema)
    ]
    if len(matches) != 1:
        raise ValueError(f"canonicalization requires exactly one matching oneOf branch, got {len(matches)}")
    return _resolve_schema(matches[0], root_schema)


def _canonicalize_with_schema(
    value: Any, schema: dict[str, Any], root_schema: dict[str, Any]
) -> Any:
    schema = _resolve_schema(schema, root_schema)
    if "oneOf" in schema:
        schema = _matching_one_of(value, schema, root_schema)
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        return {
            key: _canonicalize_with_schema(item, properties[key], root_schema)
            for key, item in value.items()
        }
    if isinstance(value, list):
        items = [
            _canonicalize_with_schema(item, schema["items"], root_schema)
            for item in value
        ]
        array_kind = schema.get("x-schuss-array-kind")
        if array_kind == "set":
            items.sort(key=lambda item: canonical_json(item).encode("utf-8"))
        elif array_kind != "sequence":
            raise ValueError("array schema lacks set/sequence canonicalization metadata")
        return items
    return value


def canonical_record_bytes(record: dict[str, Any], schema: dict[str, Any]) -> bytes:
    """Canonicalize one validated record, omitting only its own content_hash."""

    if "content_hash" not in record:
        raise ValueError("record has no own content_hash field")
    digest_input = {key: copy.deepcopy(value) for key, value in record.items() if key != "content_hash"}
    canonical_value = _canonicalize_with_schema(digest_input, schema, schema)
    return canonical_json(canonical_value).encode("utf-8")


def record_content_hash(record: dict[str, Any], schema: dict[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(canonical_record_bytes(record, schema)).hexdigest()


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
    diagnostics.append(Diagnostic(code, severity, subject, location, message))


def _scan_portability(value: Any, subject: str, diagnostics: list[Diagnostic], location: str = "$") -> None:
    try:
        _assert_portable_json_value(value, location)
    except ValueError as exc:
        _diagnostic(diagnostics, "NONPORTABLE_NUMBER", subject, location, str(exc))
        return
    if isinstance(value, str):
        if ABSOLUTE_PATH_RE.search(value):
            _diagnostic(
                diagnostics,
                "NONPORTABLE_ABSOLUTE_PATH",
                subject,
                location,
                "machine-local absolute paths are prohibited",
            )
        if TIMESTAMP_RE.search(value):
            _diagnostic(
                diagnostics,
                "NONPORTABLE_TIMESTAMP",
                subject,
                location,
                "timestamps are prohibited in semantic records",
            )
        if UUID_RE.search(value):
            _diagnostic(
                diagnostics,
                "NONPORTABLE_RANDOM_ID",
                subject,
                location,
                "UUID-shaped random identifiers are prohibited",
            )
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _scan_portability(item, subject, diagnostics, f"{location}[{index}]")
    elif isinstance(value, dict):
        for key in sorted(value):
            _scan_portability(value[key], subject, diagnostics, f"{location}.{key}")


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
        _diagnostic(
            diagnostics,
            "GRAPH_RESOLUTION_UNAVAILABLE",
            subject,
            "$.graph_reference.status",
            "instrument-v0 has no accepted Task 006 graph resolver",
        )
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
        _validate_instrument_semantics(instrument, devices_by_exact_ref, diagnostics)

    diagnostics = sorted(
        set(diagnostics),
        key=lambda item: (item.severity, item.code, item.subject, item.location, item.message),
    )
    error_count = sum(item.severity == "error" for item in diagnostics)
    deferred_graph_count = sum(
        record.get("graph_reference", {}).get("status") == "deferred"
        for record in structurally_valid_instruments
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
            "graphs_resolved": 0,
        },
        "evidence_levels": [
            {"level": "structural-schema", "status": "failed" if error_count else "passed"},
            {"level": "component-graph-resolution", "status": graph_resolution_status},
            {"level": "backend-lowering", "status": "not-run"},
            {"level": "artifact-generation", "status": "not-run"},
            {"level": "arm-compile-link", "status": "not-run"},
            {"level": "connected-device", "status": "not-run"},
            {"level": "real-time-resource", "status": "not-run"},
            {"level": "audible-listening", "status": "not-run"},
        ],
        "diagnostics": [item.as_dict() for item in diagnostics],
    }


def _record_files(root: Path, child: str) -> list[Path]:
    directory = root / child
    return sorted(path for path in directory.glob("*.json") if path.is_file())


def validate_contract_directory(contract_root: Path, schema_root: Path) -> dict[str, Any]:
    device_schema = load_json(schema_root / DEVICE_SCHEMA_NAME)
    instrument_schema = load_json(schema_root / INSTRUMENT_SCHEMA_NAME)
    devices = [load_json(path) for path in _record_files(contract_root, "device-profiles")]
    instruments = [load_json(path) for path in _record_files(contract_root, "instruments")]
    return validate_contract_values(devices, instruments, device_schema, instrument_schema)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    repository_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "contract_root",
        nargs="?",
        type=Path,
        default=repository_root / "contracts",
    )
    parser.add_argument(
        "--schema-root",
        type=Path,
        default=repository_root / "schemas",
    )
    parser.add_argument("--canonical-record", type=Path)
    parser.add_argument(
        "--record-kind",
        choices=("device-profile", "instrument"),
        help="schema family for --canonical-record",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.canonical_record is not None:
        if args.record_kind is None:
            print("--canonical-record requires --record-kind", file=sys.stderr)
            return 2
        try:
            schema_name = (
                DEVICE_SCHEMA_NAME
                if args.record_kind == "device-profile"
                else INSTRUMENT_SCHEMA_NAME
            )
            schema = load_json(args.schema_root / schema_name)
            record = load_json(args.canonical_record)
            errors = _schema_errors(record, schema, schema)
            if errors:
                raise ValueError("; ".join(errors))
            sys.stdout.buffer.write(canonical_record_bytes(record, schema) + b"\n")
            return 0
        except (OSError, ValueError) as exc:
            print(f"canonical record emission failed: {exc}", file=sys.stderr)
            return 1
    try:
        summary = validate_contract_directory(args.contract_root, args.schema_root)
    except (OSError, ValueError) as exc:
        summary = {
            "schema_version": "device-instrument-validation-summary-v0",
            "status": "invalid",
            "record_counts": {"device_profiles": 0, "instruments": 0},
            "reference_resolution": {
                "device_profiles_resolved": 0,
                "graphs_deferred": 0,
                "graphs_resolved": 0,
            },
            "evidence_levels": [
                {"level": "structural-schema", "status": "failed"},
                {"level": "component-graph-resolution", "status": "not-run"},
                {"level": "backend-lowering", "status": "not-run"},
                {"level": "artifact-generation", "status": "not-run"},
                {"level": "arm-compile-link", "status": "not-run"},
                {"level": "connected-device", "status": "not-run"},
                {"level": "real-time-resource", "status": "not-run"},
                {"level": "audible-listening", "status": "not-run"},
            ],
            "diagnostics": [
                Diagnostic(
                    "INPUT_READ_FAILED",
                    "error",
                    str(args.contract_root),
                    "$",
                    str(exc),
                ).as_dict()
            ],
        }
    print(canonical_json(summary))
    return 0 if summary["status"] != "invalid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
