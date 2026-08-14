#!/usr/bin/env python3
"""Validate the deterministic Phase 3 inventory review packet."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from build_phase3_review_packet import (
    GRAPH_TYPES,
    IMPACT_LEVELS,
    IMPACT_POLICY,
    IMPACT_POLICY_VERSION,
    SAMPLE_METHOD,
    SAMPLE_SEED,
    SAMPLE_SIZE,
    SCHEMA_VERSION,
    SEVERITIES,
    SNAPSHOT_VERSION,
    STATUSES,
    _rank,
    _summary_markdown,
    graph_ref,
    issue_location_key,
    object_ref,
    source_ref,
)
from validate_resolved_inventory import (
    load_json,
    load_jsonl,
    validate_inventory,
    validate_schema,
)


class ReviewValidationError(RuntimeError):
    pass


def _fail(message: str) -> None:
    raise ReviewValidationError(message)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _file_hashes(root: Path, *, exclude_manifest: bool = False) -> list[dict[str, str]]:
    return [
        {"path": path.relative_to(root).as_posix(), "sha256": _sha256_file(path)}
        for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix())
        if path.is_file() and not (exclude_manifest and path.name == "manifest.json")
    ]


def _machine_path_hits(root: Path) -> int:
    markers = (b"/Users/", b"/home/", b"/tmp/", b"/var/folders/", b":\\Users\\")
    return sum(
        path.read_bytes().count(marker)
        for path in root.rglob("*")
        if path.is_file()
        for marker in markers
    )


def _keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        _fail(f"{label}: keys changed: observed={sorted(value)}, expected={sorted(expected)}")


def _direct_record(issue: dict[str, Any]) -> tuple[str, str]:
    location = issue["location"]
    if location["variant_index"] is not None:
        return "object", object_ref(location["variant_index"])
    if location["graph_index"] is not None:
        return "graph", graph_ref(location["graph_index"])
    if location["source_id"] is not None and location["path"] is not None:
        return "source", source_ref(location["source_id"], location["path"])
    return "global", f"{SNAPSHOT_VERSION}:global"


def _source_for_object(item: dict[str, Any]) -> str:
    origin = item["origin"]
    if origin["kind"] == "file":
        return origin["source_id"]
    if origin["kind"] == "provider":
        return origin["provider"]["source_id"]
    return "unresolved"


def _catalog_candidate_indexes(instance: dict[str, Any]) -> list[int]:
    return [
        value["variant_index"]
        for value in instance["resolution"]["candidates"]
        if value["kind"] == "catalog"
    ]


def _selected_index(instance: dict[str, Any]) -> int | None:
    selected = instance["resolution"]["legacy_selected"]
    if selected is None or selected["kind"] != "catalog":
        return None
    return selected["variant_index"]


def _selection_ref(graph: dict[str, Any], instance: dict[str, Any]) -> str:
    return f"{graph_ref(graph['graph_index'])}:instance:{instance['serialized_index']}"


def _facet_counts(item: dict[str, Any]) -> dict[str, int]:
    facets = item["facets"]
    return {
        "inlets": len(facets["inlets"]),
        "outlets": len(facets["outlets"]),
        "ports": len(facets["inlets"]) + len(facets["outlets"]),
        "parameters": len(facets["parameters"]),
        "attributes": len(facets["attributes"]),
        "displays": len(facets["displays"]),
    }


def _validate_issue_groups(
    rows: list[dict[str, Any]], issues: list[dict[str, Any]], objects: list[dict[str, Any]]
) -> None:
    if [row["code"] for row in rows] != sorted({issue["code"] for issue in issues}):
        _fail("issues-by-code rows do not exactly cover sorted issue codes")
    objects_by_index = {item["variant_index"]: item for item in objects}
    by_code: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for issue in issues:
        by_code[issue["code"]].append(issue)
    for row in rows:
        _keys(
            row,
            {
                "schema_version", "code", "issue_count", "severity_counts", "stage_counts",
                "source_counts", "unique_location_count", "direct_affected_record_count",
                "direct_affected_by_kind", "direct_affected_refs", "implicated_object_count",
                "implicated_object_refs", "implicated_object_sources",
            },
            f"issue group {row['code']}",
        )
        if row["schema_version"] != "phase3-review-issue-group-v0":
            _fail(f"issue group {row['code']}: wrong schema version")
        values = by_code[row["code"]]
        direct = sorted({_direct_record(issue) for issue in values})
        candidates = sorted(
            {index for issue in values for index in issue["candidate_variant_indexes"]}
        )
        severity_counts = [
            {"severity": severity, "count": sum(issue["severity"] == severity for issue in values)}
            for severity in SEVERITIES
        ]
        stage_counts = [
            {"stage": stage, "count": sum(issue["stage"] == stage for issue in values)}
            for stage in sorted({issue["stage"] for issue in values})
        ]
        sources: dict[str | None, list[dict[str, Any]]] = defaultdict(list)
        for issue in values:
            sources[issue["location"]["source_id"]].append(issue)
        source_counts = [
            {
                "source_id": source_id,
                "issue_count": len(sources[source_id]),
                "direct_affected_record_count": len(
                    {_direct_record(issue) for issue in sources[source_id]}
                ),
            }
            for source_id in sorted(sources, key=lambda value: "" if value is None else value)
        ]
        by_kind = Counter(kind for kind, _ in direct)
        expected = {
            "issue_count": len(values),
            "severity_counts": severity_counts,
            "stage_counts": stage_counts,
            "source_counts": source_counts,
            "unique_location_count": len({issue_location_key(issue) for issue in values}),
            "direct_affected_record_count": len(direct),
            "direct_affected_by_kind": [
                {"kind": kind, "count": by_kind[kind]} for kind in sorted(by_kind)
            ],
            "direct_affected_refs": [reference for _, reference in direct],
            "implicated_object_count": len(candidates),
            "implicated_object_refs": [object_ref(index) for index in candidates],
            "implicated_object_sources": [
                {"source_id": source_id, "count": count}
                for source_id, count in sorted(
                    Counter(_source_for_object(objects_by_index[index]) for index in candidates).items()
                )
            ],
        }
        for key, value in expected.items():
            if row[key] != value:
                _fail(f"issue group {row['code']}.{key} does not reconcile")


def _validate_reconciliation(
    report: dict[str, Any], objects: list[dict[str, Any]], issues: list[dict[str, Any]]
) -> None:
    _keys(
        report,
        {
            "schema_version", "definition_occurrences", "legacy_equality_collapsed_occurrences",
            "catalog_subpatch_placeholders", "provider_only_records",
            "retained_in_legacy_object_list", "exported_object_records",
            "not_retained_in_legacy_object_list", "equations",
        },
        "object reconciliation",
    )
    definitions = sum(
        item["origin"]["kind"] == "file"
        and item["origin"]["path"].casefold().endswith(".axo")
        for item in objects
    )
    placeholders = sum(item["legacy_kind"] == "subpatch_catalog_placeholder" for item in objects)
    providers = sum(item["origin"]["kind"] == "provider" for item in objects)
    retained = sum(item["legacy_object_list_index"] is not None for item in objects)
    collapsed = sum(
        len(issue["candidate_variant_indexes"]) - 1
        for issue in issues
        if issue["code"] == "LEGACY_OBJECT_LIST_COLLAPSE"
    )
    observed = (
        report["definition_occurrences"],
        report["legacy_equality_collapsed_occurrences"],
        report["catalog_subpatch_placeholders"],
        report["provider_only_records"],
        report["retained_in_legacy_object_list"],
        report["exported_object_records"],
        report["not_retained_in_legacy_object_list"],
    )
    expected = (
        definitions, collapsed, placeholders, providers, retained, len(objects), len(objects) - retained
    )
    if observed != expected:
        _fail(f"object reconciliation changed: observed={observed}, expected={expected}")
    for equation in report["equations"]:
        if equation["left"] != equation["right"]:
            _fail(f"object reconciliation equation failed: {equation['name']}")


def _overload_groups(objects: list[dict[str, Any]]) -> dict[str, tuple[int, ...]]:
    grouped: dict[str, list[int]] = defaultdict(list)
    for item in objects:
        if item["origin"]["kind"] == "file" and item["legacy_id"]:
            grouped[item["legacy_id"]].append(item["variant_index"])
    return {name: tuple(indexes) for name, indexes in grouped.items() if len(indexes) > 1}


def _expected_overload_evidence(
    groups: dict[str, tuple[int, ...]], graphs: list[dict[str, Any]]
) -> dict[str, list[str]]:
    group_for_variant = {index: name for name, indexes in groups.items() for index in indexes}
    result: dict[str, list[str]] = defaultdict(list)
    for graph in graphs:
        for instance in graph["instances"]:
            indexes = _catalog_candidate_indexes(instance)
            selected = _selected_index(instance)
            if selected is not None:
                indexes.append(selected)
            related = sorted({group_for_variant[index] for index in indexes if index in group_for_variant})
            for name in related:
                result[name].append(_selection_ref(graph, instance))
    return result


def _validate_overloads(
    rows: list[dict[str, Any]], objects: list[dict[str, Any]], graphs: list[dict[str, Any]]
) -> None:
    groups = _overload_groups(objects)
    if [row["legacy_id"] for row in rows] != sorted(groups):
        _fail("overloaded-name report does not exactly cover sorted overload groups")
    expected_evidence = _expected_overload_evidence(groups, graphs)
    for row in rows:
        indexes = [item["variant_index"] for item in row["candidates"]]
        if tuple(indexes) != groups[row["legacy_id"]]:
            _fail(f"overload {row['legacy_id']}: candidate order changed")
        if row["candidate_count"] != len(indexes):
            _fail(f"overload {row['legacy_id']}: candidate count changed")
        refs = [item["evidence_ref"] for item in row["selection_evidence"]]
        if refs != expected_evidence.get(row["legacy_id"], []):
            _fail(f"overload {row['legacy_id']}: selection evidence changed")
        if row["selection_evidence_count"] != len(refs):
            _fail(f"overload {row['legacy_id']}: selection evidence count changed")
        if row["ambiguous_selection_count"] != sum(
            item["resolution_status"] == "ambiguous" for item in row["selection_evidence"]
        ):
            _fail(f"overload {row['legacy_id']}: ambiguous count changed")


def _validate_zombies(rows: list[dict[str, Any]], graphs: list[dict[str, Any]]) -> None:
    expected: dict[tuple[Any, ...], list[str]] = defaultdict(list)
    for graph in graphs:
        for instance in graph["instances"]:
            if instance["zombie_kind"] != "created-by-resolution":
                continue
            requested = instance["requested_type"]
            key = (requested["name"], requested["uuid"], requested["sha"])
            expected[key].append(_selection_ref(graph, instance))
    observed_keys = [
        (row["requested_type"]["name"], row["requested_type"]["uuid"], row["requested_type"]["sha"])
        for row in rows
    ]
    expected_keys = sorted(
        expected, key=lambda value: tuple("" if item is None else item for item in value)
    )
    if observed_keys != expected_keys:
        _fail("resolution-created zombie groups changed")
    for row, key in zip(rows, expected_keys):
        refs = [item["evidence_ref"] for item in row["occurrences"]]
        if refs != expected[key] or row["occurrence_count"] != len(refs):
            _fail(f"zombie group {key}: occurrence evidence changed")
        if row["graph_count"] != len(set(item["graph_ref"] for item in row["occurrences"])):
            _fail(f"zombie group {key}: graph count changed")


def _validate_partial_graphs(
    report: dict[str, Any], graphs: list[dict[str, Any]], issues: list[dict[str, Any]]
) -> None:
    partial = {graph["graph_index"] for graph in graphs if graph["export_status"] == "partial"}
    codes: dict[int, Counter[str]] = defaultdict(Counter)
    for issue in issues:
        index = issue["location"]["graph_index"]
        if index in partial:
            codes[index][issue["code"]] += 1
    if set(codes) != partial or report["partial_graph_count"] != len(partial):
        _fail("partial graph report does not cover every partial graph")
    expected_reason = {
        code: {index for index in partial if code in codes[index]}
        for code in {code for index in partial for code in codes[index]}
    }
    observed_reason = {
        row["code"]: {int(ref.rsplit(":", 1)[1]) for ref in row["graph_refs"]}
        for row in report["reason_groups"]
    }
    if observed_reason != expected_reason:
        _fail("partial graph reason groups changed")
    observed_partition: dict[tuple[str, ...], set[int]] = {}
    for row in report["reason_combinations"]:
        observed_partition[tuple(row["codes"])] = {
            int(ref.rsplit(":", 1)[1]) for ref in row["graph_refs"]
        }
    expected_partition: dict[tuple[str, ...], set[int]] = defaultdict(set)
    for index in partial:
        expected_partition[tuple(sorted(codes[index]))].add(index)
    if observed_partition != expected_partition:
        _fail("partial graph reason combinations do not form the exact partition")


def _validate_graph_matrix(
    report: dict[str, Any], manifest: dict[str, Any], graphs: list[dict[str, Any]]
) -> None:
    sources = [item["id"] for item in manifest["sources"]]
    counts = Counter(
        (graph["source"]["source_id"], graph["source"]["file_type"], graph["export_status"])
        for graph in graphs
    )
    expected_rows = [
        {
            "source_id": source_id,
            "file_type": file_type,
            "status": status,
            "count": counts[(source_id, file_type, status)],
        }
        for source_id in sources
        for file_type in GRAPH_TYPES
        for status in STATUSES
    ]
    if report["rows"] != expected_rows or report["graph_count"] != len(graphs):
        _fail("graph status matrix rows changed")
    if sum(row["count"] for row in report["rows"]) != len(graphs):
        _fail("graph status matrix does not reconcile to total graphs")


def _expected_coverage(objects: list[dict[str, Any]], key_name: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in objects:
        grouped[item[key_name]].append(item)
    rows = []
    for value in sorted(grouped):
        members = grouped[value]
        counts = [_facet_counts(item) for item in members]
        rows.append(
            {
                key_name: value,
                "object_count": len(members),
                "coverage": {
                    facet: {
                        "objects_with": sum(item[facet] > 0 for item in counts),
                        "total_entries": sum(item[facet] for item in counts),
                        "object_count": len(members),
                    }
                    for facet in (
                        "inlets", "outlets", "ports", "parameters", "attributes", "displays"
                    )
                },
            }
        )
    return rows


def _validate_coverage(report: dict[str, Any], objects: list[dict[str, Any]]) -> None:
    if report["object_count"] != len(objects):
        _fail("facet coverage object count changed")
    if report["by_legacy_kind"] != _expected_coverage(objects, "legacy_kind"):
        _fail("facet coverage by legacy kind changed")
    if report["by_legacy_class"] != _expected_coverage(objects, "legacy_class"):
        _fail("facet coverage by legacy class changed")


def _impact_refs(group: dict[str, Any]) -> list[str]:
    return sorted(set(group["direct_affected_refs"]) | set(group["implicated_object_refs"]))


def _validate_impact(
    rows: list[dict[str, Any]], issue_groups: list[dict[str, Any]], summary: dict[str, Any]
) -> None:
    groups = {row["code"]: row for row in issue_groups}
    if [row["code"] for row in rows] != sorted(groups):
        _fail("impact rows do not exactly cover issue groups")
    for row in rows:
        if row["policy_version"] != IMPACT_POLICY_VERSION:
            _fail(f"impact {row['code']}: policy version changed")
        policy = IMPACT_POLICY.get(row["code"])
        if policy is None:
            _fail(f"impact {row['code']}: no fail-closed policy entry")
        for dimension in ("taxonomy", "migration", "compilation"):
            if row[dimension] not in IMPACT_LEVELS or row[dimension] != policy[dimension]:
                _fail(f"impact {row['code']}.{dimension} changed")
        refs = _impact_refs(groups[row["code"]])
        if row["affected_refs"] != refs or row["affected_record_count"] != len(refs):
            _fail(f"impact {row['code']}: affected records changed")
    for dimension in ("taxonomy", "migration", "compilation"):
        material = [row for row in rows if row[dimension] in {"material", "blocking"}]
        refs = {ref for row in material for ref in row["affected_refs"]}
        value = summary["material_impact"][dimension]
        if value["material_issue_class_count"] != len(material):
            _fail(f"summary material impact {dimension}: class count changed")
        if value["unique_affected_record_count"] != len(refs):
            _fail(f"summary material impact {dimension}: unique record count changed")
        if value["issue_codes"] != [row["code"] for row in material]:
            _fail(f"summary material impact {dimension}: issue code order changed")


def _expected_hash_sample(refs: Iterable[str], cohort: str) -> list[str]:
    return [
        ref
        for _, ref in sorted((_rank(cohort, ref), ref) for ref in refs)[:SAMPLE_SIZE]
    ]


def _validate_samples(
    root: Path, objects: list[dict[str, Any]], graphs: list[dict[str, Any]]
) -> None:
    complete = load_jsonl(root / "samples/complete-graphs.jsonl")
    partial = load_jsonl(root / "samples/partial-graphs.jsonl")
    overload = load_jsonl(root / "samples/overloaded-selections.jsonl")
    object_rows = load_jsonl(root / "samples/representative-objects.jsonl")
    for label, rows in (
        ("complete graphs", complete),
        ("partial graphs", partial),
        ("overloaded selections", overload),
        ("representative objects", object_rows),
    ):
        if len(rows) != SAMPLE_SIZE or len({row["evidence_ref"] for row in rows}) != SAMPLE_SIZE:
            _fail(f"sample {label}: expected 25 distinct records")

    expected_complete = _expected_hash_sample(
        (graph_ref(graph["graph_index"]) for graph in graphs if graph["export_status"] == "complete"),
        "graph-complete",
    )
    expected_partial = _expected_hash_sample(
        (graph_ref(graph["graph_index"]) for graph in graphs if graph["export_status"] == "partial"),
        "graph-partial",
    )
    if [row["evidence_ref"] for row in complete] != expected_complete:
        _fail("complete graph sample changed")
    if [row["evidence_ref"] for row in partial] != expected_partial:
        _fail("partial graph sample changed")

    ambiguous_refs = []
    for graph in graphs:
        for instance in graph["instances"]:
            if (
                instance["resolution"]["status"] == "ambiguous"
                and len(_catalog_candidate_indexes(instance)) > 1
            ):
                ambiguous_refs.append(_selection_ref(graph, instance))
    expected_overload = _expected_hash_sample(ambiguous_refs, "overloaded-selection")
    if [row["evidence_ref"] for row in overload] != expected_overload:
        _fail("overloaded selection sample changed")

    object_by_ref = {object_ref(item["variant_index"]): item for item in objects}
    by_stratum: dict[str, list[str]] = defaultdict(list)
    for ref, item in object_by_ref.items():
        stratum = f"{item['origin']['kind']}|{item['legacy_kind']}|{_source_for_object(item)}"
        by_stratum[stratum].append(ref)
    selected = []
    used = set()
    for stratum in sorted(by_stratum):
        winner = min(by_stratum[stratum], key=lambda ref: (_rank("representative-object", ref), ref))
        selected.append(winner)
        used.add(winner)
    remaining = sorted(
        (ref for ref in object_by_ref if ref not in used),
        key=lambda ref: (_rank("representative-object", ref), ref),
    )
    selected.extend(remaining[: SAMPLE_SIZE - len(selected)])
    expected_objects = sorted(
        selected,
        key=lambda ref: (
            ref not in used,
            _rank("representative-object", ref),
        ),
    )
    if [row["evidence_ref"] for row in object_rows] != expected_objects:
        _fail("representative object sample changed")
    for rows, cohort in (
        (complete, "graph-complete"),
        (partial, "graph-partial"),
        (overload, "overloaded-selection"),
        (object_rows, "representative-object"),
    ):
        for row in rows:
            if row["rank_sha256"] != _rank(cohort, row["evidence_ref"]):
                _fail(f"sample rank changed for {row['evidence_ref']}")


def validate_review_packet(root: Path, *, snapshot: Path) -> dict[str, int]:
    root = root.resolve()
    snapshot = snapshot.resolve()
    repository_root = Path(__file__).resolve().parents[2]
    schema_root = repository_root / "schemas"
    raw_snapshot = repository_root / "catalog/snapshots/legacy-catalog-v0"
    source_lock = repository_root / "catalog/sources.lock.json"
    validate_inventory(snapshot, source_lock=source_lock, raw_snapshot=raw_snapshot)

    manifest = load_json(root / "manifest.json")
    summary = load_json(root / "reports/summary.json")
    validate_schema(manifest, load_json(schema_root / "phase3-review-manifest-v0.schema.json"))
    validate_schema(summary, load_json(schema_root / "phase3-review-summary-v0.schema.json"))
    if manifest["schema_version"] != SCHEMA_VERSION:
        _fail("review manifest schema version changed")
    if manifest["input_snapshot"]["files"] != _file_hashes(snapshot):
        _fail("review manifest no longer binds the exact frozen snapshot files")
    if manifest["generated_files"] != _file_hashes(root, exclude_manifest=True):
        _fail("review manifest generated-file hashes changed")
    expected_files = {"manifest.json"} | {
        item["path"] for item in manifest["generated_files"]
    }
    actual_files = {
        path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()
    }
    if actual_files != expected_files:
        _fail("review packet contains missing or undeclared files")
    if _machine_path_hits(snapshot) != 0 or _machine_path_hits(root) != 0:
        _fail("snapshot or review packet contains a machine-specific absolute path")

    objects = load_jsonl(snapshot / "resolved/objects.jsonl")
    graphs = load_jsonl(snapshot / "resolved/graphs.jsonl")
    issues = load_jsonl(snapshot / "resolved/issues.jsonl")
    resolved_manifest = load_json(snapshot / "manifest.json")
    issue_groups = load_jsonl(root / "reports/issues-by-code.jsonl")
    reconciliation = load_json(root / "reports/object-reconciliation.json")
    overloads = load_jsonl(root / "reports/overloaded-name-groups.jsonl")
    zombies = load_jsonl(root / "reports/resolution-created-zombies.jsonl")
    partial = load_json(root / "reports/partial-graphs.json")
    matrix = load_json(root / "reports/graph-status-matrix.json")
    coverage = load_json(root / "reports/facet-coverage.json")
    impacts = load_jsonl(root / "reports/issue-impact.jsonl")

    _validate_issue_groups(issue_groups, issues, objects)
    _validate_reconciliation(reconciliation, objects, issues)
    _validate_overloads(overloads, objects, graphs)
    _validate_zombies(zombies, graphs)
    _validate_partial_graphs(partial, graphs, issues)
    _validate_graph_matrix(matrix, resolved_manifest, graphs)
    _validate_coverage(coverage, objects)
    _validate_impact(impacts, issue_groups, summary)
    _validate_samples(root, objects, graphs)

    expected_input_counts = {
        "objects": len(objects),
        "graphs": len(graphs),
        "issues": len(issues),
        "definition_occurrences": reconciliation["definition_occurrences"],
        "retained_in_legacy_object_list": reconciliation["retained_in_legacy_object_list"],
        "overloaded_name_groups": len(overloads),
        "resolution_created_zombies": sum(row["occurrence_count"] for row in zombies),
        "partial_graphs": partial["partial_graph_count"],
    }
    if summary["input_counts"] != expected_input_counts:
        _fail("review summary input counts changed")
    if summary["issue_classes"] != len(issue_groups):
        _fail("review summary issue class count changed")
    if summary["direct_unique_affected_records"] != len(
        {ref for row in issue_groups for ref in row["direct_affected_refs"]}
    ):
        _fail("review summary direct unique affected count changed")
    if summary["implicated_unique_objects"] != len(
        {ref for row in issue_groups for ref in row["implicated_object_refs"]}
    ):
        _fail("review summary implicated object count changed")
    if summary["samples"] != {
        "method": SAMPLE_METHOD,
        "seed": SAMPLE_SEED,
        "sample_size": SAMPLE_SIZE,
        "complete_graphs": SAMPLE_SIZE,
        "partial_graphs": SAMPLE_SIZE,
        "overloaded_selections": SAMPLE_SIZE,
        "representative_objects": SAMPLE_SIZE,
    }:
        _fail("review summary sample contract changed")

    markdown_path = root / "reports/summary.md"
    markdown = markdown_path.read_bytes()
    if b"\r" in markdown or not markdown.endswith(b"\n"):
        _fail("review summary markdown must use LF and a final newline")
    expected_markdown = _summary_markdown(summary, issue_groups, impacts, matrix, partial)
    if markdown.decode("utf-8") != expected_markdown:
        _fail("review summary markdown is not the deterministic rendering")
    return {
        "issue_classes": len(issue_groups),
        "overload_groups": len(overloads),
        "zombie_groups": len(zombies),
        "partial_graphs": partial["partial_graph_count"],
    }


def main() -> int:
    repository_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Validate a Phase 3 inventory review packet")
    parser.add_argument("packet", type=Path)
    parser.add_argument(
        "--snapshot",
        type=Path,
        default=repository_root / "catalog/snapshots/legacy-resolved-catalog-v0",
    )
    args = parser.parse_args()
    try:
        counts = validate_review_packet(args.packet, snapshot=args.snapshot)
    except (ReviewValidationError, OSError, KeyError, TypeError, ValueError) as exception:
        print(f"phase 3 review validation failed: {exception}")
        return 1
    print(json.dumps({"ok": True, **counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
