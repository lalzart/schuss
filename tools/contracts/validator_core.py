"""Shared language-neutral validation, canonicalization, and registry mechanics.

This module owns no device, graph, target, backend, build, or evidence policy.
Domain-rule modules depend on it; it never imports a domain-rule module.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


MAX_IJSON_INTEGER = 9_007_199_254_740_991

ABSOLUTE_PATH_RE = re.compile(
    r"^(?:/|[A-Za-z]:[\\/])|(?:^|[\\/])(?:Users|home|tmp|private/tmp)[\\/]"
)
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


def diagnostic_sort_key(item: Diagnostic | dict[str, str]) -> tuple[str, ...]:
    if isinstance(item, Diagnostic):
        return (item.severity, item.code, item.subject, item.location, item.message)
    return (
        item["severity"],
        item["code"],
        item["subject"],
        item["location"],
        item["message"],
    )


def add_diagnostic(
    diagnostics: list[Diagnostic],
    code: str,
    subject: str,
    location: str,
    message: str,
    severity: str = "error",
) -> None:
    diagnostics.append(Diagnostic(code, severity, subject, location, message))


def canonical_json(value: Any) -> str:
    """Serialize the restricted Schuss/I-JSON value space in canonical form."""

    assert_portable_json_value(value)
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise DuplicateJsonMemberError(f"duplicate JSON member {key!r}")
        value[key] = item
    return value


def reject_float(text: str) -> None:
    raise ValueError(
        f"JSON floating-point number {text!r} is outside the restricted profile"
    )


def parse_int(text: str) -> int:
    value = int(text)
    if abs(value) > MAX_IJSON_INTEGER:
        raise ValueError(f"JSON integer {text!r} exceeds the exact I-JSON range")
    return value


def load_json_bytes(data: bytes, subject: str = "<input>", require_final_lf: bool = True) -> Any:
    """Load restricted UTF-8 JSON from bytes without client-specific coercion."""

    if data.startswith(b"\xef\xbb\xbf") or b"\r" in data:
        raise ValueError(f"{subject}: expected UTF-8 without BOM and LF line endings")
    if require_final_lf and not data.endswith(b"\n"):
        raise ValueError(f"{subject}: expected a final LF")
    try:
        return json.loads(
            data.decode("utf-8"),
            object_pairs_hook=object_pairs,
            parse_float=reject_float,
            parse_int=parse_int,
            parse_constant=lambda text: (_ for _ in ()).throw(
                ValueError(f"non-finite JSON number {text!r} is prohibited")
            ),
        )
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        DuplicateJsonMemberError,
        ValueError,
    ) as exc:
        raise ValueError(f"{subject}: invalid restricted JSON: {exc}") from exc


def load_json(path: Path) -> Any:
    """Load LF-terminated UTF-8 JSON while rejecting duplicate keys and floats."""

    return load_json_bytes(path.read_bytes(), str(path), require_final_lf=True)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf") or b"\r" in data:
        raise ValueError(f"{path}: expected UTF-8 without BOM and LF line endings")
    if data and not data.endswith(b"\n"):
        raise ValueError(f"{path}: expected a final LF")
    records: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(data.splitlines(), 1):
        if not raw_line:
            raise ValueError(f"{path}:{line_number}: blank JSONL line")
        record = load_json_bytes(
            raw_line,
            f"{path}:{line_number}",
            require_final_lf=False,
        )
        if not isinstance(record, dict):
            raise ValueError(f"{path}:{line_number}: record must be an object")
        records.append(record)
    return records


def assert_portable_json_value(value: Any, location: str = "$") -> None:
    if value is None or isinstance(value, bool) or isinstance(value, str):
        return
    if isinstance(value, int):
        if abs(value) > MAX_IJSON_INTEGER:
            raise ValueError(f"{location}: integer exceeds the exact I-JSON range")
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{location}: non-finite number is prohibited")
        raise ValueError(
            f"{location}: floating-point numbers are outside the restricted profile"
        )
    if isinstance(value, list):
        for index, item in enumerate(value):
            assert_portable_json_value(item, f"{location}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{location}: object member names must be strings")
            assert_portable_json_value(item, f"{location}.{key}")
        return
    raise ValueError(f"{location}: unsupported value type {type(value).__name__}")


def resolve_schema(schema: dict[str, Any], root_schema: dict[str, Any]) -> dict[str, Any]:
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


def json_type_matches(value: Any, expected: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }.get(expected, False)


def schema_errors(
    value: Any,
    schema: dict[str, Any],
    root_schema: dict[str, Any],
    location: str = "$",
) -> list[str]:
    schema = resolve_schema(schema, root_schema)
    errors: list[str] = []

    if "oneOf" in schema:
        branches = schema["oneOf"]
        matches = [
            branch
            for branch in branches
            if not schema_errors(value, branch, root_schema, location)
        ]
        if len(matches) != 1:
            errors.append(
                f"{location}: expected exactly one schema alternative, matched {len(matches)}"
            )
        return errors

    if "const" in schema and value != schema["const"]:
        errors.append(f"{location}: expected {schema['const']!r}, got {value!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{location}: value {value!r} is outside the controlled vocabulary")

    expected = schema.get("type")
    if expected is not None and not json_type_matches(value, expected):
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
                    schema_errors(value[key], properties[key], root_schema, f"{location}.{key}")
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
                    schema_errors(item, schema["items"], root_schema, f"{location}[{index}]")
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
    """Check that every array declares set or sequence semantics."""

    errors: list[str] = []
    visited: set[int] = set()

    def visit(node: Any, location: str) -> None:
        if not isinstance(node, dict) or id(node) in visited:
            return
        visited.add(id(node))
        if (
            node.get("type") == "object"
            and node.get("additionalProperties") is not False
            and node.get("x-schuss-domain-value") is not True
        ):
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


def matching_one_of(
    value: Any, schema: dict[str, Any], root_schema: dict[str, Any]
) -> dict[str, Any]:
    matches = [
        branch
        for branch in schema["oneOf"]
        if not schema_errors(value, branch, root_schema)
    ]
    if len(matches) != 1:
        raise ValueError(
            f"canonicalization requires exactly one matching oneOf branch, got {len(matches)}"
        )
    return resolve_schema(matches[0], root_schema)


def canonicalize_with_schema(
    value: Any, schema: dict[str, Any], root_schema: dict[str, Any]
) -> Any:
    schema = resolve_schema(schema, root_schema)
    if "oneOf" in schema:
        schema = matching_one_of(value, schema, root_schema)
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        return {
            key: canonicalize_with_schema(item, properties[key], root_schema)
            for key, item in value.items()
        }
    if isinstance(value, list):
        items = [
            canonicalize_with_schema(item, schema["items"], root_schema)
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
    digest_input = {
        key: copy.deepcopy(value)
        for key, value in record.items()
        if key != "content_hash"
    }
    canonical_value = canonicalize_with_schema(digest_input, schema, schema)
    return canonical_json(canonical_value).encode("utf-8")


def record_content_hash(record: dict[str, Any], schema: dict[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(canonical_record_bytes(record, schema)).hexdigest()


def scan_portability(
    value: Any,
    subject: str,
    diagnostics: list[Diagnostic],
    location: str = "$",
) -> None:
    try:
        assert_portable_json_value(value, location)
    except ValueError as exc:
        add_diagnostic(diagnostics, "NONPORTABLE_NUMBER", subject, location, str(exc))
        return
    if isinstance(value, str):
        if ABSOLUTE_PATH_RE.search(value):
            add_diagnostic(
                diagnostics,
                "NONPORTABLE_ABSOLUTE_PATH",
                subject,
                location,
                "machine-local absolute paths are prohibited",
            )
        if TIMESTAMP_RE.search(value):
            add_diagnostic(
                diagnostics,
                "NONPORTABLE_TIMESTAMP",
                subject,
                location,
                "timestamps are prohibited in semantic records",
            )
        if UUID_RE.search(value):
            add_diagnostic(
                diagnostics,
                "NONPORTABLE_RANDOM_ID",
                subject,
                location,
                "UUID-shaped random identifiers are prohibited",
            )
    elif isinstance(value, list):
        for index, item in enumerate(value):
            scan_portability(item, subject, diagnostics, f"{location}[{index}]")
    elif isinstance(value, dict):
        for key in sorted(value):
            scan_portability(value[key], subject, diagnostics, f"{location}.{key}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def record_files(root: Path, child: str) -> list[Path]:
    return sorted(path for path in (root / child).glob("*.json") if path.is_file())


def exact_key(record: dict[str, Any], id_field: str) -> tuple[str, int, str]:
    return record[id_field], record["revision"], record["content_hash"]


def reference_key(reference: dict[str, Any], id_field: str) -> tuple[str, int, str]:
    return reference[id_field], reference["revision"], reference["content_hash"]


def record_subject(record: dict[str, Any]) -> str:
    id_fields = (
        "capability_vocabulary_id",
        "build_environment_id",
        "compute_target_id",
        "backend_id",
        "binding_eligibility_id",
        "build_request_id",
        "build_result_id",
        "artifact_id",
        "resource_report_id",
        "evidence_claim_id",
        "family_id",
        "component_contract_id",
        "implementation_id",
        "graph_id",
        "device_profile_id",
        "instrument_id",
        "conformance_probe_evidence_id",
        "conformance_probe_id",
        "conformance_probe_result_id",
        "coverage_report_id",
        "panel_evidence_packet_id",
        "prerequisite_environment_id",
        "procedure_id",
        "runtime_realization_id",
    )
    for field in id_fields:
        if field in record:
            return f"{record.get(field, '<unknown>')}@{record.get('revision', '?')}"
    return "<unknown>@?"


def validate_structural_records(
    records: list[dict[str, Any]],
    schema: dict[str, Any],
    schema_name: str,
    schema_version: str,
    id_field: str,
    diagnostics: list[Diagnostic],
    subject_fn: Callable[[dict[str, Any]], str] = record_subject,
) -> list[dict[str, Any]]:
    for error in validate_schema_annotations(schema):
        add_diagnostic(diagnostics, "SCHEMA_CONTRACT_INVALID", schema_name, "$", error)

    valid: list[dict[str, Any]] = []
    for record in records:
        subject = subject_fn(record)
        scan_portability(record, subject, diagnostics)
        errors = schema_errors(record, schema, schema)
        for error in errors:
            add_diagnostic(
                diagnostics,
                "SCHEMA_STRUCTURE_INVALID",
                subject,
                "$",
                error,
            )
        if not errors and record.get("schema_version") == schema_version:
            valid.append(record)

    seen: dict[tuple[str, int], str] = {}
    for record in valid:
        key = (record[id_field], record["revision"])
        if key in seen:
            code = (
                "ID_REVISION_COLLISION"
                if seen[key] != record["content_hash"]
                else "DUPLICATE_RECORD"
            )
            add_diagnostic(
                diagnostics,
                code,
                f"{key[0]}@{key[1]}",
                "$",
                "one stable-ID/revision pair must occur once and resolve to one hash",
            )
        else:
            seen[key] = record["content_hash"]

        expected = record_content_hash(record, schema)
        if record["content_hash"] != expected:
            add_diagnostic(
                diagnostics,
                "CONTENT_HASH_MISMATCH",
                subject_fn(record),
                "$.content_hash",
                f"expected {expected}",
            )
    return valid


def canonical_member_hash(value: dict[str, Any]) -> str:
    data = canonical_json(value).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def cycle_nodes(edges: dict[Any, set[Any]]) -> set[Any]:
    """Return cyclic nodes and their dependency ancestors in stable traversal."""

    visiting: set[Any] = set()
    visited: set[Any] = set()
    cycles: set[Any] = set()

    def visit(node: Any) -> None:
        if node in visiting:
            cycles.add(node)
            return
        if node in visited:
            return
        visiting.add(node)
        for child in sorted(edges.get(node, set())):
            visit(child)
            if child in cycles:
                cycles.add(node)
        visiting.remove(node)
        visited.add(node)

    for node in sorted(edges):
        visit(node)
    return cycles
