#!/usr/bin/env python3
"""Validate the Phase 4A semantic catalog overlay against frozen evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SCHEMA_NAME = "semantic-catalog-overlay-v0.schema.json"
CATALOG_NAME = "catalog.json"
PRIMARY_CATEGORIES = [
    "input-output",
    "sound-sources",
    "sampling-buffers",
    "modulation-control",
    "filters-resonators",
    "shaping-dynamics",
    "delay-reverb",
    "spectral-analysis",
    "mixing-routing",
    "pitch-notes",
    "timing-sequencing",
    "data-math-logic",
    "interface-system",
]
ABSTRACTION_LEVELS = ["primitive", "compound", "instrument"]
IMPLEMENTATION_FORMS = [
    "native-object",
    "generated-object",
    "legacy-subpatch",
    "service",
    "example",
]
ABSOLUTE_PATH_RE = re.compile(r"(?:^|[\s\"'])(?:/Users/|/home/|[A-Za-z]:\\)")
TIMESTAMP_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")


class CatalogValidationError(AssertionError):
    """The overlay violated its schema or semantic contract."""


def _fail(message: str) -> None:
    raise CatalogValidationError(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    try:
        data = path.read_bytes()
    except OSError as exc:
        _fail(f"{path}: cannot read: {exc}")
    if data.startswith(b"\xef\xbb\xbf") or b"\r" in data:
        _fail(f"{path}: expected UTF-8 without BOM and LF line endings")
    if not data.endswith(b"\n"):
        _fail(f"{path}: expected a final LF")
    try:
        return json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        _fail(f"{path}: invalid UTF-8 JSON: {exc}")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        data = path.read_bytes()
    except OSError as exc:
        _fail(f"{path}: cannot read: {exc}")
    if data.startswith(b"\xef\xbb\xbf") or b"\r" in data:
        _fail(f"{path}: expected UTF-8 without BOM and LF line endings")
    if data and not data.endswith(b"\n"):
        _fail(f"{path}: expected a final LF")
    records: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(data.splitlines(), 1):
        if not raw_line:
            _fail(f"{path}:{line_number}: blank JSONL line")
        try:
            record = json.loads(raw_line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            _fail(f"{path}:{line_number}: invalid JSON: {exc}")
        if not isinstance(record, dict):
            _fail(f"{path}:{line_number}: record must be an object")
        records.append(record)
    return records


def _json_type_matches(value: Any, expected: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }.get(expected, False)


def validate_schema(
    value: Any,
    schema: dict[str, Any],
    location: str = "$",
    root_schema: dict[str, Any] | None = None,
) -> None:
    """Validate the strict JSON Schema subset used by the overlay."""

    if root_schema is None:
        root_schema = schema
    if "$ref" in schema:
        reference = schema["$ref"]
        if not reference.startswith("#/"):
            _fail(f"{location}: unsupported schema reference {reference!r}")
        target: Any = root_schema
        for token in reference[2:].split("/"):
            token = token.replace("~1", "/").replace("~0", "~")
            if not isinstance(target, dict) or token not in target:
                _fail(f"{location}: unresolved schema reference {reference!r}")
            target = target[token]
        validate_schema(value, target, location, root_schema)
        return

    if "const" in schema and value != schema["const"]:
        _fail(f"{location}: expected {schema['const']!r}, got {value!r}")
    if "enum" in schema and value not in schema["enum"]:
        _fail(f"{location}: value {value!r} is outside the enum")

    expected = schema.get("type")
    if expected is not None:
        names = expected if isinstance(expected, list) else [expected]
        if not any(_json_type_matches(value, name) for name in names):
            _fail(f"{location}: expected type {names}, got {type(value).__name__}")

    if isinstance(value, dict):
        required = set(schema.get("required", []))
        missing = required - set(value)
        if missing:
            _fail(f"{location}: missing properties {sorted(missing)}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            unexpected = set(value) - set(properties)
            if unexpected:
                _fail(f"{location}: unexpected properties {sorted(unexpected)}")
        for key, item in value.items():
            if key in properties:
                validate_schema(item, properties[key], f"{location}.{key}", root_schema)

    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            _fail(f"{location}: too few items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            _fail(f"{location}: too many items")
        if schema.get("uniqueItems"):
            encoded = [canonical_json(item) for item in value]
            if len(encoded) != len(set(encoded)):
                _fail(f"{location}: duplicate items")
        if "items" in schema:
            for index, item in enumerate(value):
                validate_schema(item, schema["items"], f"{location}[{index}]", root_schema)

    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            _fail(f"{location}: string is too short")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            _fail(f"{location}: string does not match {schema['pattern']!r}")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def identity_projection(overlay: dict[str, Any]) -> dict[str, list[str]]:
    return {
        "family_ids": [item["family_id"] for item in overlay["families"]],
        "implementation_ids": [
            item["implementation_id"] for item in overlay["implementations"]
        ],
    }


def _source_id(record: dict[str, Any], kind: str) -> str:
    if kind == "graph":
        return record["source"]["source_id"]
    origin = record["origin"]
    if origin["kind"] == "file":
        return origin["source_id"]
    if origin["kind"] == "provider":
        return origin["provider"]["source_id"]
    _fail("pilot evidence may not use an unresolved object origin")
    raise AssertionError("unreachable")


def _evidence_maps(snapshot_root: Path) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    objects = load_jsonl(snapshot_root / "resolved/objects.jsonl")
    graphs = load_jsonl(snapshot_root / "resolved/graphs.jsonl")
    object_map: dict[str, dict[str, Any]] = {}
    graph_map: dict[str, dict[str, Any]] = {}
    for expected_index, record in enumerate(objects):
        if record["variant_index"] != expected_index:
            _fail("frozen object indexes are not consecutive")
        object_map[f"legacy-resolved-catalog-v0:object:{expected_index}"] = record
    for expected_index, record in enumerate(graphs):
        if record["graph_index"] != expected_index:
            _fail("frozen graph indexes are not consecutive")
        graph_map[f"legacy-resolved-catalog-v0:graph:{expected_index}"] = record
    return object_map, graph_map


def _validate_sorted_unique(values: list[Any], location: str, key=lambda item: item) -> None:
    keys = [key(item) for item in values]
    if keys != sorted(keys):
        _fail(f"{location}: values must be sorted")
    if len(keys) != len(set(keys)):
        _fail(f"{location}: values must be unique")


def validate_overlay_value(
    overlay: dict[str, Any],
    schema: dict[str, Any],
    snapshot_root: Path,
    review_root: Path,
) -> dict[str, Any]:
    validate_schema(overlay, schema)

    durable_text = canonical_json(overlay)
    if ABSOLUTE_PATH_RE.search(durable_text):
        _fail("overlay contains a machine-specific absolute path")
    if TIMESTAMP_RE.search(durable_text):
        _fail("overlay contains a timestamp")

    vocabulary = overlay["controlled_vocabulary"]
    if vocabulary["primary_categories"] != PRIMARY_CATEGORIES:
        _fail("controlled primary category order or membership drifted")
    if vocabulary["abstraction_levels"] != ABSTRACTION_LEVELS:
        _fail("controlled abstraction levels drifted")
    if vocabulary["implementation_forms"] != IMPLEMENTATION_FORMS:
        _fail("controlled implementation forms drifted")
    _validate_sorted_unique(
        vocabulary["secondary_function_tags"],
        "controlled_vocabulary.secondary_function_tags",
    )

    manifest_path = snapshot_root / "manifest.json"
    manifest = load_json(manifest_path)
    if overlay["legacy_evidence"]["snapshot_schema_version"] != manifest["schema_version"]:
        _fail("overlay legacy schema version does not match the frozen manifest")
    if overlay["legacy_evidence"]["manifest_sha256"] != sha256_file(manifest_path):
        _fail("overlay legacy manifest hash does not match frozen evidence")

    object_map, graph_map = _evidence_maps(snapshot_root)
    evidence = {**object_map, **graph_map}
    families = overlay["families"]
    implementations = overlay["implementations"]
    family_ids = [item["family_id"] for item in families]
    implementation_ids = [item["implementation_id"] for item in implementations]
    _validate_sorted_unique(family_ids, "families")
    _validate_sorted_unique(implementation_ids, "implementations")
    family_id_set = set(family_ids)

    category_counts = Counter(item["primary_category"] for item in families)
    if set(category_counts) != set(PRIMARY_CATEGORIES):
        _fail("pilot must cover every Phase 4A primary category")

    vocabulary_tags = set(vocabulary["secondary_function_tags"])
    for index, family in enumerate(families):
        _validate_sorted_unique(family["aliases"], f"families[{index}].aliases")
        _validate_sorted_unique(
            family["secondary_function_tags"],
            f"families[{index}].secondary_function_tags",
        )
        if not set(family["secondary_function_tags"]) <= vocabulary_tags:
            _fail(f"{family['family_id']}: uncontrolled function tag")
        if family["classification_confidence"] == "low" and not any(
            item["affects"] == "classification" for item in family["unresolved_questions"]
        ):
            _fail(f"{family['family_id']}: low classification confidence needs a question")

    implementations_by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    used_sources: set[str] = set()
    selected_object_records: list[dict[str, Any]] = []
    selected_graph_records: list[dict[str, Any]] = []
    provider_only = False
    provider_backed = False
    for index, implementation in enumerate(implementations):
        implementation_id = implementation["implementation_id"]
        family_id = implementation["family_id"]
        if family_id not in family_id_set:
            _fail(f"{implementation_id}: unknown family {family_id}")
        implementations_by_family[family_id].append(implementation)
        refs = implementation["legacy_evidence_refs"]
        _validate_sorted_unique(refs, f"implementations[{index}].legacy_evidence_refs")
        if not any(":object:" in ref for ref in refs):
            _fail(f"{implementation_id}: legacy pilot implementation needs an object observation")
        for ref in refs:
            if ref not in evidence:
                _fail(f"{implementation_id}: unresolved evidence reference {ref}")
            record = evidence[ref]
            if ":object:" in ref:
                selected_object_records.append(record)
                origin = record["origin"]
                provider_only |= origin["kind"] == "provider"
                provider_backed |= origin["kind"] == "provider" or (
                    origin["kind"] == "file" and origin.get("generated_by") is not None
                )
            else:
                selected_graph_records.append(record)

        provenance_refs = implementation["provenance_refs"]
        _validate_sorted_unique(
            provenance_refs,
            f"implementations[{index}].provenance_refs",
            key=lambda item: (item["source_id"], item["evidence_ref"]),
        )
        provenance_by_ref = {item["evidence_ref"]: item["source_id"] for item in provenance_refs}
        if set(provenance_by_ref) != set(refs):
            _fail(f"{implementation_id}: provenance must cover every evidence reference exactly")
        for ref, source_id in provenance_by_ref.items():
            kind = "object" if ":object:" in ref else "graph"
            if source_id != _source_id(evidence[ref], kind):
                _fail(f"{implementation_id}: provenance source disagrees with {ref}")
            used_sources.add(source_id)

        for compatibility in implementation["compatibility_evidence"]:
            _validate_sorted_unique(
                compatibility["evidence_refs"],
                f"{implementation_id}.compatibility_evidence",
            )
            if not set(compatibility["evidence_refs"]) <= set(refs):
                _fail(f"{implementation_id}: compatibility cites evidence outside membership")
            if compatibility["status"] != "not-evaluated":
                _fail(f"{implementation_id}: Phase 4A cannot assert target compatibility")
        if implementation["membership_confidence"] == "low" and not any(
            item["affects"] == "membership"
            for item in implementation["unresolved_questions"]
        ):
            _fail(f"{implementation_id}: low membership confidence needs a question")

    missing_implementations = family_id_set - set(implementations_by_family)
    if missing_implementations:
        _fail(f"families without implementations: {sorted(missing_implementations)}")

    overload_groups = load_jsonl(review_root / "reports/overloaded-name-groups.jsonl")
    overload_indexes = {
        item["legacy_id"]: {candidate["variant_index"] for candidate in item["candidates"]}
        for item in overload_groups
    }
    object_indexes_by_family: dict[str, set[int]] = defaultdict(set)
    for implementation in implementations:
        for ref in implementation["legacy_evidence_refs"]:
            if ref in object_map:
                object_indexes_by_family[implementation["family_id"]].add(
                    object_map[ref]["variant_index"]
                )
    overloaded_family_ids = sorted(
        family_id
        for family_id, indexes in object_indexes_by_family.items()
        if any(len(indexes & candidates) >= 2 for candidates in overload_indexes.values())
    )
    compound_graphs = [
        record
        for record in selected_graph_records
        if record["source"]["file_type"] == "axs" and record["export_status"] == "complete"
    ]
    parameter_heavy = sorted(
        record["variant_index"]
        for record in selected_object_records
        if len(record["facets"]["parameters"]) >= 10
    )
    port_heavy = sorted(
        record["variant_index"]
        for record in selected_object_records
        if len(record["facets"]["inlets"]) + len(record["facets"]["outlets"]) >= 10
    )
    uncertain_family_ids = sorted(
        item["family_id"] for item in families if item["classification_confidence"] == "low"
    )
    uncertain_implementation_ids = sorted(
        item["implementation_id"]
        for item in implementations
        if item["membership_confidence"] == "low"
    )
    multi_implementation_family_ids = sorted(
        family_id
        for family_id, records in implementations_by_family.items()
        if len(records) > 1
    )
    native_primitive = any(
        implementation["form"] == "native-object"
        and next(
            family["abstraction_level"]
            for family in families
            if family["family_id"] == implementation["family_id"]
        )
        == "primitive"
        for implementation in implementations
    )
    required_cases = {
        "complete_compound_axs": len(compound_graphs) >= 1,
        "generated_or_provider_backed": provider_backed,
        "provider_only_observation": provider_only,
        "overloaded_name_group": bool(overloaded_family_ids),
        "multi_implementation_family": bool(multi_implementation_family_ids),
        "explicit_uncertainty": bool(uncertain_family_ids or uncertain_implementation_ids),
        "parameter_heavy": bool(parameter_heavy),
        "port_heavy": bool(port_heavy),
        "multiple_provenance_sources": len(used_sources) >= 3,
        "native_primitive": native_primitive,
    }
    if not all(required_cases.values()):
        _fail(f"pilot difficult-case coverage failed: {required_cases}")

    return {
        "schema_version": "semantic-catalog-validation-summary-v0",
        "overlay_id": overlay["overlay_id"],
        "family_count": len(families),
        "implementation_count": len(implementations),
        "category_coverage": [
            {"category": category, "family_count": category_counts[category]}
            for category in PRIMARY_CATEGORIES
        ],
        "provenance_sources": sorted(used_sources),
        "overloaded_family_ids": overloaded_family_ids,
        "multi_implementation_family_ids": multi_implementation_family_ids,
        "uncertain_family_ids": uncertain_family_ids,
        "uncertain_implementation_ids": uncertain_implementation_ids,
        "parameter_heavy_variant_indexes": parameter_heavy,
        "port_heavy_variant_indexes": port_heavy,
        "complete_compound_graph_indexes": sorted(
            record["graph_index"] for record in compound_graphs
        ),
        "required_cases": required_cases,
    }


def validate_catalog(
    overlay_root: Path,
    schema_root: Path,
    snapshot_root: Path,
    review_root: Path,
) -> dict[str, Any]:
    overlay = load_json(overlay_root / CATALOG_NAME)
    schema = load_json(schema_root / SCHEMA_NAME)
    if not isinstance(overlay, dict) or not isinstance(schema, dict):
        _fail("overlay and schema roots must be JSON objects")
    return validate_overlay_value(overlay, schema, snapshot_root, review_root)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("overlay_root", type=Path)
    repository_root = Path(__file__).resolve().parents[2]
    parser.add_argument("--schema-root", type=Path, default=repository_root / "schemas")
    parser.add_argument(
        "--snapshot-root",
        type=Path,
        default=repository_root / "catalog/snapshots/legacy-resolved-catalog-v0",
    )
    parser.add_argument(
        "--review-root",
        type=Path,
        default=repository_root / "catalog/reviews/phase-3-inventory-review-v0",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        summary = validate_catalog(
            args.overlay_root,
            args.schema_root,
            args.snapshot_root,
            args.review_root,
        )
    except CatalogValidationError as exc:
        print(f"semantic catalog validation failed: {exc}", file=sys.stderr)
        return 1
    print(canonical_json(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
