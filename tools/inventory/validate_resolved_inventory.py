#!/usr/bin/env python3
"""Validate and reconcile a Schuss Phase 3 Java-resolved inventory."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


MANIFEST_SCHEMA = "legacy-resolved-manifest-v0.schema.json"
OBJECT_SCHEMA = "legacy-resolved-object-v0.schema.json"
GRAPH_SCHEMA = "legacy-resolved-graph-v0.schema.json"
ISSUE_SCHEMA = "legacy-resolved-issue-v0.schema.json"
SUMMARY_SCHEMA = "legacy-resolved-summary-v0.schema.json"
LEGACY_SOURCE_ORDER = (
    "axoloti-factory",
    "axoloti-contrib",
    "ksoloti-objects",
    "ksoloti-contrib",
    "patcher",
)
UUID_V4_RE = re.compile(
    r"(?i)(?<![0-9a-f])[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-"
    r"[89ab][0-9a-f]{3}-[0-9a-f]{12}(?![0-9a-f])"
)


class InventoryValidationError(AssertionError):
    """A resolved inventory violated its versioned contract."""


def _fail(message: str) -> None:
    raise InventoryValidationError(message)


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
            value = json.loads(raw_line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            _fail(f"{path}:{line_number}: invalid UTF-8 JSON: {exc}")
        if not isinstance(value, dict):
            _fail(f"{path}:{line_number}: record must be an object")
        records.append(value)
    return records


def _json_type_matches(value: Any, name: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }.get(name, False)


def validate_schema(
    value: Any,
    schema: dict[str, Any],
    location: str = "$",
    root_schema: dict[str, Any] | None = None,
) -> None:
    """Validate the strict Draft 2020-12 subset used by Phase 3 schemas."""

    if root_schema is None:
        root_schema = schema
    if "$ref" in schema:
        reference = schema["$ref"]
        if not reference.startswith("#/"):
            _fail(f"{location}: unsupported non-local schema reference {reference!r}")
        target: Any = root_schema
        for token in reference[2:].split("/"):
            token = token.replace("~1", "/").replace("~0", "~")
            if not isinstance(target, dict) or token not in target:
                _fail(f"{location}: unresolved schema reference {reference!r}")
            target = target[token]
        validate_schema(value, target, location, root_schema)

    for branch in schema.get("allOf", []):
        validate_schema(value, branch, location, root_schema)

    if "oneOf" in schema:
        matches = 0
        errors: list[str] = []
        for branch in schema["oneOf"]:
            try:
                validate_schema(value, branch, location, root_schema)
                matches += 1
            except InventoryValidationError as exc:
                errors.append(str(exc))
        if matches != 1:
            detail = errors[0] if errors else "multiple alternatives matched"
            _fail(f"{location}: expected exactly one schema alternative ({detail})")

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
            encoded = [
                json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                for item in value
            ]
            if len(encoded) != len(set(encoded)):
                _fail(f"{location}: duplicate items")
        if "contains" in schema:
            found = False
            for item in value:
                try:
                    validate_schema(item, schema["contains"], location, root_schema)
                    found = True
                    break
                except InventoryValidationError:
                    pass
            if not found:
                _fail(f"{location}: no item satisfies contains")
        if "items" in schema:
            for index, item in enumerate(value):
                validate_schema(item, schema["items"], f"{location}[{index}]", root_schema)

    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            _fail(f"{location}: string is too short")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            _fail(f"{location}: string does not match {schema['pattern']!r}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            _fail(f"{location}: value is below minimum")
        if "maximum" in schema and value > schema["maximum"]:
            _fail(f"{location}: value is above maximum")


def _schema(schema_root: Path, filename: str) -> dict[str, Any]:
    value = load_json(schema_root / filename)
    if not isinstance(value, dict):
        _fail(f"{schema_root / filename}: schema must be an object")
    return value


def _portable(path: str, location: str) -> None:
    pure = PurePosixPath(path)
    if pure.is_absolute() or ".." in pure.parts or "\\" in path:
        _fail(f"{location}: non-portable path {path!r}")


def _legacy_file_type(path: str) -> str:
    lowered = PurePosixPath(path).name.casefold()
    for file_type in ("axo", "axs", "axp", "java"):
        if lowered.endswith("." + file_type):
            return file_type
    return ""


def _consecutive(values: Iterable[int], location: str) -> None:
    sequence = list(values)
    if sequence != list(range(len(sequence))):
        _fail(f"{location}: expected consecutive indexes, got {sequence}")


def _consecutive_set(values: Iterable[int], location: str) -> None:
    sequence = list(values)
    if sorted(sequence) != list(range(len(sequence))):
        _fail(f"{location}: expected a consecutive index set, got {sequence}")


def _named_counts(counter: Counter[str]) -> list[dict[str, Any]]:
    return [{"name": name, "count": counter[name]} for name in sorted(counter)]


def _typed_counts(counter: Counter[str]) -> list[dict[str, Any]]:
    return [{"file_type": name, "count": counter[name]} for name in sorted(counter)]


def _source_typed_counts(counter: Counter[tuple[str, str]]) -> list[dict[str, Any]]:
    return [
        {"source_id": source, "file_type": file_type, "count": counter[(source, file_type)]}
        for source, file_type in sorted(counter)
    ]


def _exceptional_object_paths(
    issues: list[dict[str, Any]], code: str
) -> set[tuple[str, str]]:
    result: set[tuple[str, str]] = set()
    for issue in issues:
        if issue["code"] != code:
            continue
        location = issue["location"]
        source_id, path = location["source_id"], location["path"]
        if source_id is None or path is None:
            _fail(f"issue {issue['issue_index']}: {code} needs a source path")
        key = (source_id, path)
        if key in result:
            _fail(f"{code}: repeated object-file issue for {source_id}:{path}")
        result.add(key)
    return result


def build_summary(
    raw_files: list[dict[str, Any]],
    objects: list[dict[str, Any]],
    graphs: list[dict[str, Any]],
    issues: list[dict[str, Any]],
    enabled_object_roots: set[tuple[str, str]] | None = None,
) -> dict[str, Any]:
    """Derive the entire summary from retained raw and resolved evidence."""

    raw_types = Counter(item["file_type"] for item in raw_files)
    raw_source_types = Counter(
        (item["source_repository"], item["file_type"]) for item in raw_files
    )
    enabled_object_roots = enabled_object_roots or {
        (item["source_repository"], "") for item in raw_files if item["file_type"] == "axo"
    }
    def is_under_enabled_root(source_id: str, path: str) -> bool:
        return any(
            source_id == root_source
            and (not prefix or path == prefix or path.startswith(prefix + "/"))
            for root_source, prefix in enabled_object_roots
        )

    not_enabled_objects = sum(
        item["file_type"] == "axo"
        and not is_under_enabled_root(item["source_repository"], item["path"])
        for item in raw_files
    )
    raw_subpatches = raw_types["axs"]
    not_enabled_subpatches = sum(
        item["file_type"] == "axs"
        and not is_under_enabled_root(item["source_repository"], item["path"])
        for item in raw_files
    )
    omission_types = Counter()
    for issue in issues:
        if issue["code"] != "RAW_BASELINE_OMISSION":
            continue
        facts = {fact["name"]: fact["value"] for fact in issue["facts"]}
        file_type = facts.get("file_type")
        if file_type not in {"axo", "axs", "axp"}:
            _fail("RAW_BASELINE_OMISSION must include an axo/axs/axp file_type fact")
        sha256 = facts.get("sha256")
        if not isinstance(sha256, str) or re.fullmatch(r"[0-9a-f]{64}", sha256) is None:
            _fail("RAW_BASELINE_OMISSION must include a lowercase SHA-256 fact")
        omission_types[file_type] += 1
    attempted_objects = raw_types["axo"] - not_enabled_objects + omission_types["axo"]
    omitted_catalog_subpatches = sum(
        issue["code"] == "RAW_BASELINE_OMISSION"
        and {fact["name"]: fact["value"] for fact in issue["facts"]}.get("file_type") == "axs"
        and is_under_enabled_root(
            issue["location"]["source_id"], issue["location"]["path"]
        )
        for issue in issues
    )
    registered_subpatches = raw_subpatches - not_enabled_subpatches + omitted_catalog_subpatches
    observed_subpatches = sum(
        item.get("legacy_kind") == "subpatch_catalog_placeholder" for item in objects
    )
    if observed_subpatches != registered_subpatches:
        _fail(
            f"registered subpatch files ({registered_subpatches}) do not match "
            f"catalog placeholder records ({observed_subpatches})"
        )
    relaxed = _exceptional_object_paths(issues, "OBJECT_PARSE_RELAXED")
    failed = _exceptional_object_paths(issues, "OBJECT_PARSE_FAILED")
    zero = _exceptional_object_paths(issues, "OBJECT_FILE_ZERO_DEFINITIONS")
    exceptional = relaxed | failed | zero
    if len(exceptional) != len(relaxed) + len(failed) + len(zero):
        _fail("object-file outcome issue categories overlap")
    if len(exceptional) > attempted_objects:
        _fail("object-file outcomes exceed raw .axo candidates")
    attempted_object_paths = {
        (item["source_repository"], item["path"])
        for item in raw_files
        if item["file_type"] == "axo"
        and is_under_enabled_root(item["source_repository"], item["path"])
    } | {
        (issue["location"]["source_id"], issue["location"]["path"])
        for issue in issues
        if issue["code"] == "RAW_BASELINE_OMISSION"
        and {fact["name"]: fact["value"] for fact in issue["facts"]}.get("file_type") == "axo"
    }
    if not exceptional <= attempted_object_paths:
        _fail("object-file outcome issue refers to a file outside enabled inputs")

    object_status = Counter(item["export_status"] for item in objects)
    object_classes = Counter(item["legacy_class"] for item in objects)
    origin_kinds = Counter(item["origin"]["kind"] for item in objects)
    uuid_kinds = Counter(item["uuid"]["runtime_kind"] for item in objects)
    definition_occurrences = sum(
        item["origin"]["kind"] == "file"
        and item["origin"]["path"].casefold().endswith(".axo")
        for item in objects
    )
    retained = sum(item["legacy_object_list_index"] is not None for item in objects)
    collapsed = 0
    for issue in issues:
        if issue["code"] == "LEGACY_OBJECT_LIST_COLLAPSE":
            candidates = issue["candidate_variant_indexes"]
            if len(candidates) < 2:
                _fail("LEGACY_OBJECT_LIST_COLLAPSE must name survivor and omitted variants")
            collapsed += len(candidates) - 1

    # Provider-only records are fail-closed observations of generated output
    # that did not exactly match the pinned file-backed catalog. They are not
    # members of the legacy catalog search collection, so they must not create
    # synthetic catalog overload or duplicate-UUID groups here.
    catalog_objects = [item for item in objects if item["origin"]["kind"] == "file"]
    overloads = Counter(
        item["legacy_id"] for item in catalog_objects if item["legacy_id"]
    )
    overloaded_groups = sum(count > 1 for count in overloads.values())
    explicit_uuids = Counter(
        item["uuid"]["durable_value"]
        for item in catalog_objects
        if item["uuid"]["runtime_kind"] == "explicit"
    )
    duplicate_uuid_groups = sum(count > 1 for count in explicit_uuids.values())
    if sum(issue["code"] == "OVERLOADED_NAME_CANDIDATES" for issue in issues) != overloaded_groups:
        _fail("OVERLOADED_NAME_CANDIDATES issues do not reconcile with object records")
    if sum(issue["code"] == "DUPLICATE_UUID_CANDIDATES" for issue in issues) != duplicate_uuid_groups:
        _fail("DUPLICATE_UUID_CANDIDATES issues do not reconcile with object records")

    graph_status = Counter(item["export_status"] for item in graphs)
    raw_graph_candidates = raw_types["axs"] + raw_types["axp"]
    graph_candidates = raw_graph_candidates + omission_types["axs"] + omission_types["axp"]
    if len(graphs) != graph_candidates:
        _fail(
            f"resolved graph records ({len(graphs)}) do not match raw candidates "
            f"plus named baseline omissions ({graph_candidates})"
        )
    instances = [instance for graph in graphs for instance in graph["instances"]]
    nets = [net for graph in graphs for net in graph["nets"]]
    endpoint_status = Counter(
        endpoint["resolution_status"]
        for net in nets
        for endpoint in net["sources"] + net["destinations"]
    )

    issue_severity = Counter(item["severity"] for item in issues)
    issue_stage = Counter(item["stage"] for item in issues)
    issue_code = Counter(item["code"] for item in issues)

    return {
        "schema_version": "legacy-resolved-summary-v0",
        "raw_candidates": {
            "total": len(raw_files),
            "by_type": _typed_counts(raw_types),
            "by_source_and_type": _source_typed_counts(raw_source_types),
        },
        "object_files": {
            "raw_candidates": raw_types["axo"],
            "attempted": attempted_objects,
            "not_enabled": not_enabled_objects,
            "not_in_raw_baseline": omission_types["axo"],
            "strict_loaded": attempted_objects - len(exceptional),
            "relaxed_loaded": len(relaxed),
            "failed": len(failed),
            "zero_definition": len(zero),
        },
        "catalog_subpatch_files": {
            "raw_candidates": raw_subpatches,
            "not_enabled": not_enabled_subpatches,
            "not_in_raw_baseline": omitted_catalog_subpatches,
            "registered": registered_subpatches,
        },
        "objects": {
            "definition_occurrences": definition_occurrences,
            "records": len(objects),
            "complete": object_status["complete"],
            "partial": object_status["partial"],
            "retained_in_legacy_object_list": retained,
            "collapsed_by_legacy_equality": collapsed,
            "by_legacy_class": _named_counts(object_classes),
            "by_origin_kind": [
                {"kind": name, "count": origin_kinds[name]} for name in sorted(origin_kinds)
            ],
            "by_uuid_runtime_kind": [
                {"kind": name, "count": uuid_kinds[name]} for name in sorted(uuid_kinds)
            ],
            "overloaded_name_groups": overloaded_groups,
            "duplicate_uuid_groups": duplicate_uuid_groups,
        },
        "graphs": {
            "raw_candidates": raw_graph_candidates,
            "candidates": graph_candidates,
            "not_in_raw_baseline": omission_types["axs"] + omission_types["axp"],
            "attempted": len(graphs),
            "complete": graph_status["complete"],
            "partial": graph_status["partial"],
            "failed": graph_status["failed"],
            "instances": len(instances),
            "resolved_instances": sum(
                item["resolution"]["status"] == "resolved" for item in instances
            ),
            "ambiguous_instances": sum(
                item["resolution"]["status"] == "ambiguous" for item in instances
            ),
            "hard_zombies": sum(
                item["zombie_kind"] == "serialized-hard" for item in instances
            ),
            "created_zombies": sum(
                item["zombie_kind"] == "created-by-resolution" for item in instances
            ),
            "source_nets": len(nets),
            "resolved_nets": sum(item["status"] == "resolved" for item in nets),
            "removed_nets": sum(item["status"] == "removed" for item in nets),
            "endpoint_status_counts": {
                name: endpoint_status[name]
                for name in ("resolved", "missing_instance", "missing_port", "not_evaluated")
            },
        },
        "issues": {
            "total": len(issues),
            "by_severity": {
                name: issue_severity[name] for name in ("info", "warning", "error")
            },
            "by_stage": _named_counts(issue_stage),
            "by_code": _named_counts(issue_code),
        },
    }


def render_summary_markdown(summary: dict[str, Any]) -> str:
    """Render a compact deterministic view; JSON remains authoritative."""

    objects = summary["objects"]
    graphs = summary["graphs"]
    issues = summary["issues"]
    lines = [
        "# Java-resolved legacy inventory summary",
        "",
        f"Raw candidates: {summary['raw_candidates']['total']}",
        f"Resolved object records: {objects['records']}",
        f"Resolved graph records: {graphs['attempted']}",
        f"Issues: {issues['total']}",
        "",
        "## Object identity observations",
        "",
        f"- Definition occurrences: {objects['definition_occurrences']}",
        f"- Retained in legacy ObjectList: {objects['retained_in_legacy_object_list']}",
        f"- Collapsed by legacy equality: {objects['collapsed_by_legacy_equality']}",
        f"- Overloaded name groups: {objects['overloaded_name_groups']}",
        f"- Duplicate UUID groups: {objects['duplicate_uuid_groups']}",
        "",
        "## Graph resolution observations",
        "",
        f"- Complete: {graphs['complete']}",
        f"- Partial: {graphs['partial']}",
        f"- Failed: {graphs['failed']}",
        f"- Hard zombies: {graphs['hard_zombies']}",
        f"- Zombies created by resolution: {graphs['created_zombies']}",
        "",
    ]
    return "\n".join(lines)


def _validate_object_indexes(objects: list[dict[str, Any]]) -> None:
    _consecutive((item["variant_index"] for item in objects), "objects.variant_index")
    list_indexes = [
        item["legacy_object_list_index"]
        for item in objects
        if item["legacy_object_list_index"] is not None
    ]
    _consecutive(list_indexes, "objects.legacy_object_list_index")
    for item in objects:
        for facet_name in (
            "inlets", "outlets", "parameters", "attributes", "displays",
            "modulators", "file_dependencies",
        ):
            _consecutive(
                (entry["index"] for entry in item["facets"][facet_name]),
                f"object {item['variant_index']}.{facet_name}",
            )


def _validate_graph_indexes(graphs: list[dict[str, Any]], object_count: int) -> None:
    expected_order = sorted(
        graphs, key=lambda item: (item["source"]["source_id"], item["source"]["path"])
    )
    if graphs != expected_order:
        _fail("graphs: expected source_id/path ordering")
    _consecutive((item["graph_index"] for item in graphs), "graphs.graph_index")
    for graph in graphs:
        graph_index = graph["graph_index"]
        _portable(graph["source"]["path"], f"graph {graph_index}.source.path")
        _consecutive(
            (item["serialized_index"] for item in graph["instances"]),
            f"graph {graph_index}.instances.serialized_index",
        )
        _consecutive_set(
            (
                item["post_resolution_index"]
                for item in graph["instances"]
                if item["post_resolution_index"] is not None
            ),
            f"graph {graph_index}.instances.post_resolution_index",
        )
        _consecutive(
            (item["serialized_index"] for item in graph["nets"]),
            f"graph {graph_index}.nets.serialized_index",
        )
        _consecutive_set(
            (
                item["post_resolution_index"]
                for item in graph["nets"]
                if item["post_resolution_index"] is not None
            ),
            f"graph {graph_index}.nets.post_resolution_index",
        )
        for instance in graph["instances"]:
            for candidate in instance["resolution"]["candidates"]:
                if candidate["kind"] == "catalog" and candidate["variant_index"] >= object_count:
                    _fail(f"graph {graph_index}: dangling candidate variant index")
            selected = instance["resolution"]["legacy_selected"]
            if selected and selected["kind"] == "catalog" and selected["variant_index"] >= object_count:
                _fail(f"graph {graph_index}: dangling selected variant index")
            for values_name in ("parameter_values", "attribute_values"):
                _consecutive(
                    (entry["index"] for entry in instance[values_name]),
                    f"graph {graph_index} instance {instance['serialized_index']}.{values_name}",
                )
        for net in graph["nets"]:
            for role in ("sources", "destinations"):
                _consecutive(
                    (endpoint["serialized_index"] for endpoint in net[role]),
                    f"graph {graph_index} net {net['serialized_index']}.{role}",
                )


def _none_first(value: Any) -> tuple[int, Any]:
    return (0, "") if value is None else (1, value)


def _issue_sort_key(issue: dict[str, Any]) -> tuple[Any, ...]:
    location = issue["location"]
    return tuple(
        _none_first(location[name])
        for name in (
            "source_id", "path", "variant_index", "graph_index", "instance_index",
            "net_index", "endpoint_role", "endpoint_index",
        )
    ) + (
        issue["stage"],
        issue["code"],
        tuple(issue["candidate_variant_indexes"]),
        json.dumps(issue["facts"], ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        issue["message"],
    )


def _validate_issue_indexes(
    issues: list[dict[str, Any]], object_count: int, graph_count: int
) -> None:
    keys = [_issue_sort_key(item) for item in issues]
    if keys != sorted(keys):
        _fail("issues: expected portable location/stage/code ordering")
    _consecutive((item["issue_index"] for item in issues), "issues.issue_index")
    for issue in issues:
        location = issue["location"]
        if location["path"] is not None:
            _portable(location["path"], f"issue {issue['issue_index']}.location.path")
        if location["variant_index"] is not None and location["variant_index"] >= object_count:
            _fail(f"issue {issue['issue_index']}: dangling variant index")
        if location["graph_index"] is not None and location["graph_index"] >= graph_count:
            _fail(f"issue {issue['issue_index']}: dangling graph index")
        for candidate in issue["candidate_variant_indexes"]:
            if candidate >= object_count:
                _fail(f"issue {issue['issue_index']}: dangling candidate variant index")


def _contains_uuid_v4(value: Any) -> bool:
    if isinstance(value, str):
        return UUID_V4_RE.search(value) is not None
    if isinstance(value, dict):
        return any(_contains_uuid_v4(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_uuid_v4(item) for item in value)
    return False


def _reject_generated_uuid_leaks(objects: list[dict[str, Any]]) -> None:
    for item in objects:
        origin = item["origin"]
        provider_backed = origin["kind"] == "provider" or (
            origin["kind"] == "file" and origin["generated_by"] is not None
        )
        generated_uuid = item["uuid"]["runtime_kind"] == "generated-nondeterministic"
        if provider_backed and generated_uuid and _contains_uuid_v4(item):
            _fail(
                f"object {item['variant_index']}: random provider UUID leaked into durable data"
            )


def _fact_map(issue: dict[str, Any]) -> dict[str, Any]:
    names = [fact["name"] for fact in issue["facts"]]
    if len(names) != len(set(names)):
        _fail(f"issue {issue['issue_index']}: facts must have unique names")
    return {fact["name"]: fact["value"] for fact in issue["facts"]}


def _validate_provenance(
    manifest: dict[str, Any],
    raw_files: list[dict[str, Any]],
    objects: list[dict[str, Any]],
    graphs: list[dict[str, Any]],
    issues: list[dict[str, Any]],
) -> None:
    commits = {item["id"]: item["commit"] for item in manifest["sources"]}
    raw: dict[tuple[str, str], dict[str, Any]] = {}
    for item in raw_files:
        key = (item["source_repository"], item["path"])
        if key in raw:
            _fail(f"raw snapshot has duplicate source/path {key}")
        if item["source_repository"] not in commits:
            _fail(f"raw snapshot names unlocked source {item['source_repository']!r}")
        if item["source_commit"] != commits[item["source_repository"]]:
            _fail(f"raw snapshot commit mismatch for {key}")
        raw[key] = item

    omissions: dict[tuple[str, str], tuple[str, str]] = {}
    for issue in issues:
        _fact_map(issue)
        if issue["code"] != "RAW_BASELINE_OMISSION":
            continue
        location = issue["location"]
        if issue["stage"] != "reconcile" or location["source_id"] is None or location["path"] is None:
            _fail("RAW_BASELINE_OMISSION must be a source/path reconcile issue")
        key = (location["source_id"], location["path"])
        if key in raw or key in omissions:
            _fail(f"RAW_BASELINE_OMISSION is duplicate or already in raw baseline: {key}")
        facts = _fact_map(issue)
        omissions[key] = (facts["sha256"], facts["file_type"])

    referenced_omissions: set[tuple[str, str]] = set()

    def check_reference(
        source_id: str, path: str, sha256: str, expected_types: set[str], label: str
    ) -> None:
        if source_id not in commits:
            _fail(f"{label}: source {source_id!r} is not locked")
        _portable(path, f"{label}.path")
        key = (source_id, path)
        if key in raw:
            record = raw[key]
            if record["sha256"] != sha256:
                _fail(f"{label}: SHA-256 differs from raw evidence")
            if record["file_type"] not in expected_types:
                _fail(f"{label}: raw file type is incompatible")
            return
        if key not in omissions:
            _fail(f"{label}: source/path is neither raw evidence nor a named omission")
        omission_sha, omission_type = omissions[key]
        if omission_sha != sha256 or omission_type not in expected_types:
            _fail(f"{label}: RAW_BASELINE_OMISSION facts do not match")
        referenced_omissions.add(key)

    def check_provider(provider: dict[str, Any], label: str) -> None:
        check_reference(
            provider["source_id"], provider["path"], provider["sha256"], {"java"}, label
        )

    for item in objects:
        origin = item["origin"]
        label = f"object {item['variant_index']}.origin"
        if origin["kind"] == "file":
            suffix = _legacy_file_type(origin["path"])
            if not suffix:
                _fail(f"{label}: unsupported source filename")
            check_reference(
                origin["source_id"], origin["path"], origin["sha256"], {suffix}, label
            )
            if origin["generated_by"] is not None:
                check_provider(origin["generated_by"], f"{label}.generated_by")
        elif origin["kind"] == "provider":
            check_provider(origin["provider"], f"{label}.provider")

    for graph in graphs:
        source = graph["source"]
        check_reference(
            source["source_id"], source["path"], source["sha256"], {source["file_type"]},
            f"graph {graph['graph_index']}.source",
        )
        for instance in graph["instances"]:
            references = list(instance["resolution"]["candidates"])
            selected = instance["resolution"]["legacy_selected"]
            if selected is not None:
                references.append(selected)
            for reference in references:
                if reference["kind"] == "graph-local-file":
                    suffix = _legacy_file_type(reference["path"])
                    if not suffix:
                        _fail(f"graph {graph['graph_index']}: unsupported local filename")
                    check_reference(
                        reference["source_id"], reference["path"], reference["sha256"],
                        {suffix}, f"graph {graph['graph_index']}.graph-local-file",
                    )

    # A zero-definition or failed omitted .axo has no object origin, but it must
    # still have a file-outcome issue at the same source/path.
    outcome_paths = {
        (issue["location"]["source_id"], issue["location"]["path"])
        for issue in issues
        if issue["code"] in {"OBJECT_PARSE_FAILED", "OBJECT_FILE_ZERO_DEFINITIONS"}
    }
    unreferenced = set(omissions) - referenced_omissions - outcome_paths
    if unreferenced:
        _fail(f"RAW_BASELINE_OMISSION entries are not tied to exported evidence: {sorted(unreferenced)}")

    for item in objects:
        if item["export_status"] == "partial" and not any(
            issue["location"]["variant_index"] == item["variant_index"] for issue in issues
        ):
            _fail(f"partial object {item['variant_index']} has no matching issue")
    for graph in graphs:
        if graph["export_status"] in {"partial", "failed"} and not any(
            issue["location"]["graph_index"] == graph["graph_index"] for issue in issues
        ):
            _fail(f"{graph['export_status']} graph {graph['graph_index']} has no matching issue")


def _validate_manifest_sources(
    manifest: dict[str, Any], source_lock: Path | None
) -> None:
    source_ids = [item["id"] for item in manifest["sources"]]
    if len(source_ids) != len(set(source_ids)):
        _fail("manifest.sources: duplicate source ID")
    orders = [item["order"] for item in manifest["object_roots"]]
    _consecutive(orders, "manifest.object_roots.order")
    for item in manifest["object_roots"]:
        _portable(item["relative_path"], "manifest.object_roots.relative_path")
        if item["source_id"] not in source_ids:
            _fail("manifest.object_roots: source ID is absent from sources")
    if source_lock is None:
        return
    lock = load_json(source_lock)
    if lock.get("schema_version") != "schuss-source-lock-v1":
        _fail(f"{source_lock}: unexpected source-lock schema version")
    expected = [
        {"id": item["id"], "url": item["url"], "commit": item["commit"]}
        for item in lock["sources"]
    ]
    observed = [
        {"id": item["id"], "url": item["url"], "commit": item["commit"]}
        for item in manifest["sources"]
    ]
    if observed != expected:
        _fail("manifest.sources does not exactly match the source lock")
    patcher = next((item for item in expected if item["id"] == "patcher"), None)
    if patcher is None or manifest["legacy_runtime"]["source_id"] != "patcher":
        _fail("manifest.legacy_runtime must identify the locked patcher")
    if manifest["legacy_runtime"]["commit"] != patcher["commit"]:
        _fail("manifest.legacy_runtime commit does not match the source lock")
    if set(source_ids) == set(LEGACY_SOURCE_ORDER):
        expected_roots = [
            {"order": index, "source_id": source_id, "relative_path": "objects"}
            for index, source_id in enumerate(LEGACY_SOURCE_ORDER[:-1])
        ]
        if manifest["object_roots"] != expected_roots:
            _fail("manifest.object_roots does not preserve the legacy default order")


def validate_inventory(
    root: Path,
    *,
    schema_root: Path | None = None,
    source_lock: Path | None = None,
    raw_snapshot: Path | None = None,
) -> dict[str, int]:
    root = root.resolve()
    repository_root = Path(__file__).resolve().parents[2]
    schema_root = (schema_root or repository_root / "schemas").resolve()

    manifest = load_json(root / "manifest.json")
    objects = load_jsonl(root / "resolved/objects.jsonl")
    graphs = load_jsonl(root / "resolved/graphs.jsonl")
    issues = load_jsonl(root / "resolved/issues.jsonl")
    summary = load_json(root / "reports/summary.json")
    summary_markdown = (root / "reports/summary.md").read_bytes()
    if b"\r" in summary_markdown or not summary_markdown.endswith(b"\n"):
        _fail("reports/summary.md: expected LF line endings and final LF")

    validate_schema(manifest, _schema(schema_root, MANIFEST_SCHEMA))
    object_schema = _schema(schema_root, OBJECT_SCHEMA)
    graph_schema = _schema(schema_root, GRAPH_SCHEMA)
    issue_schema = _schema(schema_root, ISSUE_SCHEMA)
    validate_schema(summary, _schema(schema_root, SUMMARY_SCHEMA))
    for index, item in enumerate(objects):
        validate_schema(item, object_schema, f"objects[{index}]")
    for index, item in enumerate(graphs):
        validate_schema(item, graph_schema, f"graphs[{index}]")
    for index, item in enumerate(issues):
        validate_schema(item, issue_schema, f"issues[{index}]")

    _validate_manifest_sources(manifest, source_lock)
    _validate_object_indexes(objects)
    _validate_graph_indexes(graphs, len(objects))
    _validate_issue_indexes(issues, len(objects), len(graphs))
    _reject_generated_uuid_leaks(objects)

    if raw_snapshot is None:
        _fail("raw_snapshot is required to reconcile the Phase 3 summary")
    raw_snapshot = raw_snapshot.resolve()
    raw_manifest_path = raw_snapshot / "manifest.json"
    raw_files_path = raw_snapshot / "raw/files.jsonl"
    if manifest["raw_snapshot"]["manifest_sha256"] != sha256_file(raw_manifest_path):
        _fail("manifest.raw_snapshot.manifest_sha256 mismatch")
    if manifest["raw_snapshot"]["files_jsonl_sha256"] != sha256_file(raw_files_path):
        _fail("manifest.raw_snapshot.files_jsonl_sha256 mismatch")
    raw_manifest = load_json(raw_manifest_path)
    if raw_manifest.get("schema_version") != manifest["raw_snapshot"]["schema_version"]:
        _fail("manifest.raw_snapshot.schema_version mismatch")
    raw_files = load_jsonl(raw_files_path)

    _validate_provenance(manifest, raw_files, objects, graphs, issues)
    enabled_roots = {
        (item["source_id"], item["relative_path"]) for item in manifest["object_roots"]
    }
    expected_summary = build_summary(
        raw_files, objects, graphs, issues, enabled_object_roots=enabled_roots
    )
    if summary != expected_summary:
        _fail("reports/summary.json does not reconcile with raw and resolved records")
    if summary["objects"]["records"] != (
        summary["objects"]["complete"] + summary["objects"]["partial"]
    ):
        _fail("summary.objects status counts do not reconcile")
    if summary["graphs"]["attempted"] != (
        summary["graphs"]["complete"]
        + summary["graphs"]["partial"]
        + summary["graphs"]["failed"]
    ):
        _fail("summary.graphs status counts do not reconcile")
    if summary_markdown.decode("utf-8") != render_summary_markdown(summary):
        _fail("reports/summary.md is not the deterministic summary rendering")

    return {"objects": len(objects), "graphs": len(graphs), "issues": len(issues)}


def main() -> int:
    repository_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("inventory", type=Path)
    parser.add_argument("--schema-root", type=Path, default=repository_root / "schemas")
    parser.add_argument(
        "--source-lock", type=Path, default=repository_root / "catalog/sources.lock.json"
    )
    parser.add_argument(
        "--raw-snapshot",
        type=Path,
        default=repository_root / "catalog/snapshots/legacy-catalog-v0",
    )
    args = parser.parse_args()
    try:
        counts = validate_inventory(
            args.inventory,
            schema_root=args.schema_root,
            source_lock=args.source_lock,
            raw_snapshot=args.raw_snapshot,
        )
    except (InventoryValidationError, OSError, KeyError, TypeError) as exc:
        print(f"resolved inventory validation failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"ok": True, **counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
