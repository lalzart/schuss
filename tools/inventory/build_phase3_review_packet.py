#!/usr/bin/env python3
"""Build the deterministic, reporting-only Phase 3 inventory review packet."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from validate_resolved_inventory import load_json, load_jsonl, validate_inventory


SCHEMA_VERSION = "phase3-inventory-review-v0"
SNAPSHOT_VERSION = "legacy-resolved-catalog-v0"
GENERATOR_VERSION = 1
SAMPLE_SEED = "schuss-phase3-inventory-review-v0"
SAMPLE_SIZE = 25
SAMPLE_METHOD = "sha256-rank-v1"
IMPACT_POLICY_VERSION = "phase3-review-impact-v0"
STATUSES = ("complete", "partial", "failed")
GRAPH_TYPES = ("axs", "axp")
SEVERITIES = ("info", "warning", "error")
IMPACT_LEVELS = ("none", "context", "material", "blocking")


class ReviewBuildError(RuntimeError):
    pass


IMPACT_POLICY: dict[str, dict[str, str]] = {
    "AMBIGUOUS_INSTANCE_RESOLUTION": {
        "taxonomy": "context",
        "migration": "material",
        "compilation": "material",
        "rationale": (
            "The legacy selection is observed, but candidate context must remain available "
            "to migration and compilation adapters."
        ),
    },
    "GENERATED_DEFINITION_COUNT_MISMATCH": {
        "taxonomy": "material",
        "migration": "material",
        "compilation": "context",
        "rationale": (
            "Provider emissions do not reconcile one-to-one with file definitions, so "
            "identity and provenance require review before curation or migration."
        ),
    },
    "GENERATED_EMISSION_UNMATCHED": {
        "taxonomy": "material",
        "migration": "material",
        "compilation": "context",
        "rationale": (
            "The object exists as an observed provider emission but has no exact file-backed "
            "match in the resolved catalog."
        ),
    },
    "GENERATED_OUTPUT_REDEFINED": {
        "taxonomy": "material",
        "migration": "material",
        "compilation": "context",
        "rationale": (
            "One provider output identity was redefined, so deduplication and migration "
            "cannot rely on the final map value alone."
        ),
    },
    "GENERATED_OUTPUT_REPEATED_IDENTICAL": {
        "taxonomy": "context",
        "migration": "material",
        "compilation": "none",
        "rationale": (
            "Repeated identical output is not lost, but migration must avoid counting the "
            "emission twice."
        ),
    },
    "GRAPH_POST_CONSTRUCTION_FAILED": {
        "taxonomy": "material",
        "migration": "blocking",
        "compilation": "blocking",
        "rationale": (
            "The graph has serialized evidence but no trustworthy post-construction model."
        ),
    },
    "GRAPH_XML_SCAN_FAILED": {
        "taxonomy": "material",
        "migration": "blocking",
        "compilation": "blocking",
        "rationale": (
            "The graph structure could not be inspected safely, so compound behavior and "
            "migration readiness are unknown."
        ),
    },
    "INSTANCE_BECAME_ZOMBIE": {
        "taxonomy": "context",
        "migration": "blocking",
        "compilation": "blocking",
        "rationale": (
            "Legacy resolution replaced the instance with a zombie; the graph cannot be "
            "treated as migration- or compilation-ready."
        ),
    },
    "INSTANCE_RESOLUTION_UNPROVEN": {
        "taxonomy": "context",
        "migration": "material",
        "compilation": "material",
        "rationale": (
            "The selected target is not representable as a traceable v0 identity. Most cases "
            "are embedded patcher definitions, not proof of broken source."
        ),
    },
    "LEGACY_OBJECT_LIST_COLLAPSE": {
        "taxonomy": "material",
        "migration": "material",
        "compilation": "context",
        "rationale": (
            "Distinct definition occurrences compare equal in the legacy collection and need "
            "separate stable identities in Schuss."
        ),
    },
    "NET_ENDPOINT_PORT_MISSING": {
        "taxonomy": "context",
        "migration": "blocking",
        "compilation": "blocking",
        "rationale": (
            "A serialized endpoint has no resolved port, preventing a faithful migrated net."
        ),
    },
    "NET_REMOVED_DURING_RESOLUTION": {
        "taxonomy": "context",
        "migration": "blocking",
        "compilation": "blocking",
        "rationale": (
            "Legacy post-construction removed the serialized net, so the retained graph is "
            "not a complete executable topology."
        ),
    },
    "NET_STRUCTURALLY_INCOMPLETE": {
        "taxonomy": "context",
        "migration": "blocking",
        "compilation": "blocking",
        "rationale": (
            "The source net lacks the structure needed for a faithful migrated or compiled "
            "connection."
        ),
    },
    "NONPORTABLE_GRAPH_VALUE_REDACTED": {
        "taxonomy": "none",
        "migration": "material",
        "compilation": "material",
        "rationale": (
            "A machine-specific serialized value was intentionally removed; migration or "
            "compilation may need an explicit portable replacement."
        ),
    },
    "OVERLOADED_NAME_CANDIDATES": {
        "taxonomy": "material",
        "migration": "material",
        "compilation": "context",
        "rationale": (
            "A legacy display/name identifier maps to multiple definitions and cannot serve "
            "as a stable Schuss identity."
        ),
    },
    "RAW_BASELINE_OMISSION": {
        "taxonomy": "none",
        "migration": "none",
        "compilation": "none",
        "rationale": (
            "Phase 3 explicitly recovered and reconciled the omitted candidate; this remains "
            "provenance context rather than current workflow interference."
        ),
    },
    "SERIALIZED_ATTRIBUTE_NOT_PROJECTED": {
        "taxonomy": "context",
        "migration": "material",
        "compilation": "material",
        "rationale": (
            "A serialized attribute did not project onto the resolved instance and needs an "
            "explicit migration decision."
        ),
    },
    "SERIALIZED_HARD_ZOMBIE": {
        "taxonomy": "context",
        "migration": "blocking",
        "compilation": "blocking",
        "rationale": (
            "The graph intentionally serializes a hard zombie and lacks a resolvable target."
        ),
    },
    "SERIALIZED_PARAMETER_NOT_PROJECTED": {
        "taxonomy": "context",
        "migration": "material",
        "compilation": "material",
        "rationale": (
            "A serialized parameter did not project onto the resolved instance and needs an "
            "explicit migration decision."
        ),
    },
    "UNSUPPORTED_ATTRIBUTE_VALUE": {
        "taxonomy": "material",
        "migration": "material",
        "compilation": "material",
        "rationale": (
            "The typed v0 record cannot represent one attribute value, so behavior-dependent "
            "review cannot treat the record as complete."
        ),
    },
}


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def snapshot_file_hashes(root: Path) -> list[dict[str, str]]:
    return [
        {"path": path.relative_to(root).as_posix(), "sha256": sha256_file(path)}
        for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix())
        if path.is_file()
    ]


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(
                json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                + "\n"
            )


def object_ref(index: int) -> str:
    return f"{SNAPSHOT_VERSION}:object:{index}"


def graph_ref(index: int) -> str:
    return f"{SNAPSHOT_VERSION}:graph:{index}"


def issue_ref(index: int) -> str:
    return f"{SNAPSHOT_VERSION}:issue:{index}"


def source_ref(source_id: str, path: str) -> str:
    digest = _sha256_bytes((source_id + "\0" + path).encode("utf-8"))
    return f"{SNAPSHOT_VERSION}:source:{digest}"


def direct_affected_record(issue: dict[str, Any]) -> tuple[str, str]:
    location = issue["location"]
    if location["variant_index"] is not None:
        return "object", object_ref(location["variant_index"])
    if location["graph_index"] is not None:
        return "graph", graph_ref(location["graph_index"])
    if location["source_id"] is not None and location["path"] is not None:
        return "source", source_ref(location["source_id"], location["path"])
    return "global", f"{SNAPSHOT_VERSION}:global"


def issue_location_key(issue: dict[str, Any]) -> tuple[Any, ...]:
    location = issue["location"]
    return tuple(
        location[name]
        for name in (
            "kind", "source_id", "path", "variant_index", "graph_index",
            "instance_index", "net_index", "endpoint_role", "endpoint_index",
        )
    )


def _rank(cohort: str, evidence_ref: str) -> str:
    return _sha256_bytes(
        (SAMPLE_SEED + "\0" + cohort + "\0" + evidence_ref).encode("utf-8")
    )


def deterministic_sample(
    rows: Iterable[dict[str, Any]], cohort: str, reference_key: str, size: int = SAMPLE_SIZE
) -> list[dict[str, Any]]:
    ranked = []
    for row in rows:
        copied = dict(row)
        copied["rank_sha256"] = _rank(cohort, copied[reference_key])
        ranked.append(copied)
    ranked.sort(key=lambda row: (row["rank_sha256"], row[reference_key]))
    return ranked[:size]


def _source_for_object(item: dict[str, Any]) -> str:
    origin = item["origin"]
    if origin["kind"] == "file":
        return origin["source_id"]
    if origin["kind"] == "provider":
        return origin["provider"]["source_id"]
    return "unresolved"


def _origin_summary(item: dict[str, Any]) -> dict[str, Any]:
    origin = item["origin"]
    if origin["kind"] == "file":
        return {
            "kind": "file",
            "source_id": origin["source_id"],
            "path": origin["path"],
            "definition_index": origin["definition_index"],
            "generated_by": origin["generated_by"],
        }
    if origin["kind"] == "provider":
        return {
            "kind": "provider",
            "source_id": origin["provider"]["source_id"],
            "path": origin["provider"]["path"],
            "definition_index": None,
            "generated_by": origin["provider"],
        }
    return {
        "kind": origin["kind"],
        "source_id": None,
        "path": None,
        "definition_index": None,
        "generated_by": None,
    }


def _candidate_summary(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "evidence_ref": object_ref(item["variant_index"]),
        "variant_index": item["variant_index"],
        "legacy_object_list_index": item["legacy_object_list_index"],
        "legacy_id": item["legacy_id"],
        "legacy_kind": item["legacy_kind"],
        "legacy_class": item["legacy_class"],
        "export_status": item["export_status"],
        "uuid": item["uuid"],
        "origin": _origin_summary(item),
        "facet_counts": _facet_counts(item),
    }


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


def build_issue_groups(
    issues: list[dict[str, Any]], objects: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    objects_by_index = {item["variant_index"]: item for item in objects}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for issue in issues:
        grouped[issue["code"]].append(issue)

    rows = []
    for code in sorted(grouped):
        values = grouped[code]
        direct = sorted({direct_affected_record(issue) for issue in values})
        implicated_indexes = sorted(
            {
                candidate
                for issue in values
                for candidate in issue["candidate_variant_indexes"]
            }
        )
        implicated = [object_ref(index) for index in implicated_indexes]
        sources: dict[str | None, list[dict[str, Any]]] = defaultdict(list)
        for issue in values:
            sources[issue["location"]["source_id"]].append(issue)
        source_rows = []
        for source_id in sorted(sources, key=lambda value: "" if value is None else value):
            source_values = sources[source_id]
            source_rows.append(
                {
                    "source_id": source_id,
                    "issue_count": len(source_values),
                    "direct_affected_record_count": len(
                        {direct_affected_record(issue) for issue in source_values}
                    ),
                }
            )
        by_kind = Counter(kind for kind, _ in direct)
        rows.append(
            {
                "schema_version": "phase3-review-issue-group-v0",
                "code": code,
                "issue_count": len(values),
                "severity_counts": [
                    {"severity": severity, "count": sum(v["severity"] == severity for v in values)}
                    for severity in SEVERITIES
                ],
                "stage_counts": [
                    {"stage": stage, "count": sum(v["stage"] == stage for v in values)}
                    for stage in sorted({value["stage"] for value in values})
                ],
                "source_counts": source_rows,
                "unique_location_count": len({issue_location_key(issue) for issue in values}),
                "direct_affected_record_count": len(direct),
                "direct_affected_by_kind": [
                    {"kind": kind, "count": by_kind[kind]} for kind in sorted(by_kind)
                ],
                "direct_affected_refs": [reference for _, reference in direct],
                "implicated_object_count": len(implicated),
                "implicated_object_refs": implicated,
                "implicated_object_sources": [
                    {
                        "source_id": source_id,
                        "count": count,
                    }
                    for source_id, count in sorted(
                        Counter(_source_for_object(objects_by_index[index]) for index in implicated_indexes).items()
                    )
                ],
            }
        )
    return rows


def build_object_reconciliation(
    objects: list[dict[str, Any]], issues: list[dict[str, Any]]
) -> dict[str, Any]:
    definitions = sum(
        item["origin"]["kind"] == "file"
        and item["origin"]["path"].casefold().endswith(".axo")
        for item in objects
    )
    placeholders = sum(
        item["legacy_kind"] == "subpatch_catalog_placeholder" for item in objects
    )
    provider_only = sum(item["origin"]["kind"] == "provider" for item in objects)
    retained = sum(item["legacy_object_list_index"] is not None for item in objects)
    collapsed = sum(
        len(issue["candidate_variant_indexes"]) - 1
        for issue in issues
        if issue["code"] == "LEGACY_OBJECT_LIST_COLLAPSE"
    )
    exported = len(objects)
    not_retained = exported - retained
    return {
        "schema_version": "phase3-review-object-reconciliation-v0",
        "definition_occurrences": definitions,
        "legacy_equality_collapsed_occurrences": collapsed,
        "catalog_subpatch_placeholders": placeholders,
        "provider_only_records": provider_only,
        "retained_in_legacy_object_list": retained,
        "exported_object_records": exported,
        "not_retained_in_legacy_object_list": not_retained,
        "equations": [
            {
                "name": "exported_records",
                "expression": "definition_occurrences + catalog_subpatch_placeholders + provider_only_records",
                "left": exported,
                "right": definitions + placeholders + provider_only,
            },
            {
                "name": "legacy_object_list",
                "expression": "definition_occurrences - legacy_equality_collapsed_occurrences + catalog_subpatch_placeholders",
                "left": retained,
                "right": definitions - collapsed + placeholders,
            },
            {
                "name": "not_retained_records",
                "expression": "legacy_equality_collapsed_occurrences + provider_only_records",
                "left": not_retained,
                "right": collapsed + provider_only,
            },
        ],
    }


def _selection_summary(
    graph: dict[str, Any], instance: dict[str, Any]
) -> dict[str, Any]:
    candidates = [
        value["variant_index"]
        for value in instance["resolution"]["candidates"]
        if value["kind"] == "catalog"
    ]
    selected_value = instance["resolution"]["legacy_selected"]
    selected = (
        selected_value["variant_index"]
        if selected_value is not None and selected_value["kind"] == "catalog"
        else None
    )
    return {
        "evidence_ref": (
            f"{graph_ref(graph['graph_index'])}:instance:{instance['serialized_index']}"
        ),
        "graph_ref": graph_ref(graph["graph_index"]),
        "graph_index": graph["graph_index"],
        "source": graph["source"],
        "instance_index": instance["serialized_index"],
        "instance_name": instance["instance_name"],
        "requested_type": instance["requested_type"],
        "resolution_method": instance["resolution"]["method"],
        "resolution_status": instance["resolution"]["status"],
        "candidate_variant_indexes": candidates,
        "selected_variant_index": selected,
        "zombie_kind": instance["zombie_kind"],
    }


def build_overload_groups(
    objects: list[dict[str, Any]], graphs: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    objects_by_index = {item["variant_index"]: item for item in objects}
    grouped: dict[str, list[int]] = defaultdict(list)
    for item in objects:
        if item["origin"]["kind"] == "file" and item["legacy_id"]:
            grouped[item["legacy_id"]].append(item["variant_index"])
    overloads = {
        legacy_id: tuple(indexes)
        for legacy_id, indexes in grouped.items()
        if len(indexes) > 1
    }
    group_for_variant = {
        index: legacy_id for legacy_id, indexes in overloads.items() for index in indexes
    }
    evidence: dict[str, list[dict[str, Any]]] = defaultdict(list)
    ambiguous_evidence: list[dict[str, Any]] = []
    for graph in graphs:
        for instance in graph["instances"]:
            selection = _selection_summary(graph, instance)
            related_groups = sorted(
                {
                    group_for_variant[index]
                    for index in (
                        selection["candidate_variant_indexes"]
                        + ([selection["selected_variant_index"]]
                           if selection["selected_variant_index"] is not None else [])
                    )
                    if index in group_for_variant
                }
            )
            for legacy_id in related_groups:
                value = dict(selection)
                value["requested_name_matches_group"] = (
                    selection["requested_type"]["name"] == legacy_id
                )
                evidence[legacy_id].append(value)
            if (
                selection["resolution_status"] == "ambiguous"
                and len(selection["candidate_variant_indexes"]) > 1
            ):
                selection["overloaded_legacy_ids"] = related_groups
                ambiguous_evidence.append(selection)

    rows = []
    for legacy_id in sorted(overloads):
        indexes = overloads[legacy_id]
        selections = sorted(
            evidence[legacy_id], key=lambda value: (value["graph_index"], value["instance_index"])
        )
        selected_counts = Counter(
            value["selected_variant_index"]
            for value in selections
            if value["selected_variant_index"] is not None
        )
        rows.append(
            {
                "schema_version": "phase3-review-overload-group-v0",
                "legacy_id": legacy_id,
                "candidate_count": len(indexes),
                "candidates": [_candidate_summary(objects_by_index[index]) for index in indexes],
                "selection_evidence_count": len(selections),
                "ambiguous_selection_count": sum(
                    value["resolution_status"] == "ambiguous" for value in selections
                ),
                "selected_variant_counts": [
                    {"variant_index": index, "count": selected_counts[index]}
                    for index in sorted(selected_counts)
                ],
                "selection_evidence": selections,
            }
        )
    return rows, ambiguous_evidence


def build_zombie_groups(graphs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for graph in graphs:
        for instance in graph["instances"]:
            if instance["zombie_kind"] != "created-by-resolution":
                continue
            requested = instance["requested_type"]
            key = (requested["name"], requested["uuid"], requested["sha"])
            grouped[key].append(_selection_summary(graph, instance))
    rows = []
    for key in sorted(
        grouped,
        key=lambda value: tuple("" if item is None else item for item in value),
    ):
        occurrences = sorted(
            grouped[key], key=lambda value: (value["graph_index"], value["instance_index"])
        )
        graph_refs = sorted({value["graph_ref"] for value in occurrences})
        candidate_indexes = sorted(
            {index for value in occurrences for index in value["candidate_variant_indexes"]}
        )
        rows.append(
            {
                "schema_version": "phase3-review-zombie-group-v0",
                "requested_type": {"name": key[0], "uuid": key[1], "sha": key[2]},
                "occurrence_count": len(occurrences),
                "graph_count": len(graph_refs),
                "graph_refs": graph_refs,
                "candidate_variant_indexes": candidate_indexes,
                "source_counts": [
                    {"source_id": source_id, "count": count}
                    for source_id, count in sorted(
                        Counter(value["source"]["source_id"] for value in occurrences).items()
                    )
                ],
                "occurrences": occurrences,
            }
        )
    return rows


def build_partial_graph_report(
    graphs: list[dict[str, Any]], issues: list[dict[str, Any]]
) -> dict[str, Any]:
    partial = [graph for graph in graphs if graph["export_status"] == "partial"]
    partial_indexes = {graph["graph_index"] for graph in partial}
    codes_by_graph: dict[int, Counter[str]] = defaultdict(Counter)
    for issue in issues:
        index = issue["location"]["graph_index"]
        if index in partial_indexes:
            codes_by_graph[index][issue["code"]] += 1
    if set(codes_by_graph) != partial_indexes:
        missing = sorted(partial_indexes - set(codes_by_graph))
        raise ReviewBuildError(f"partial graphs lack issues: {missing}")

    reason_graphs: dict[str, set[int]] = defaultdict(set)
    combinations: dict[tuple[str, ...], list[int]] = defaultdict(list)
    for index in sorted(partial_indexes):
        codes = tuple(sorted(codes_by_graph[index]))
        combinations[codes].append(index)
        for code in codes:
            reason_graphs[code].add(index)
    return {
        "schema_version": "phase3-review-partial-graphs-v0",
        "partial_graph_count": len(partial),
        "reason_groups": [
            {
                "code": code,
                "graph_count": len(reason_graphs[code]),
                "graph_refs": [graph_ref(index) for index in sorted(reason_graphs[code])],
                "issue_count": sum(codes_by_graph[index][code] for index in reason_graphs[code]),
            }
            for code in sorted(reason_graphs)
        ],
        "reason_combinations": [
            {
                "codes": list(codes),
                "graph_count": len(indexes),
                "graph_refs": [graph_ref(index) for index in indexes],
            }
            for codes, indexes in sorted(combinations.items())
        ],
    }


def build_graph_status_matrix(
    manifest: dict[str, Any], graphs: list[dict[str, Any]]
) -> dict[str, Any]:
    sources = [item["id"] for item in manifest["sources"]]
    counts = Counter(
        (graph["source"]["source_id"], graph["source"]["file_type"], graph["export_status"])
        for graph in graphs
    )
    rows = [
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
    return {
        "schema_version": "phase3-review-graph-status-matrix-v0",
        "graph_count": len(graphs),
        "rows": rows,
        "by_status": [
            {"status": status, "count": sum(graph["export_status"] == status for graph in graphs)}
            for status in STATUSES
        ],
        "by_source": [
            {
                "source_id": source_id,
                "count": sum(graph["source"]["source_id"] == source_id for graph in graphs),
            }
            for source_id in sources
        ],
        "by_file_type": [
            {
                "file_type": file_type,
                "count": sum(graph["source"]["file_type"] == file_type for graph in graphs),
            }
            for file_type in GRAPH_TYPES
        ],
    }


def _coverage_rows(objects: list[dict[str, Any]], key_name: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in objects:
        grouped[item[key_name]].append(item)
    rows = []
    for value in sorted(grouped):
        members = grouped[value]
        counts = [_facet_counts(item) for item in members]
        coverage = {}
        for facet in ("inlets", "outlets", "ports", "parameters", "attributes", "displays"):
            coverage[facet] = {
                "objects_with": sum(item[facet] > 0 for item in counts),
                "total_entries": sum(item[facet] for item in counts),
                "object_count": len(members),
            }
        rows.append({key_name: value, "object_count": len(members), "coverage": coverage})
    return rows


def build_facet_coverage(objects: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "phase3-review-facet-coverage-v0",
        "object_count": len(objects),
        "by_legacy_kind": _coverage_rows(objects, "legacy_kind"),
        "by_legacy_class": _coverage_rows(objects, "legacy_class"),
    }


def build_impact_rows(issue_groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    observed = {row["code"] for row in issue_groups}
    if observed != set(IMPACT_POLICY):
        missing = sorted(observed - set(IMPACT_POLICY))
        unused = sorted(set(IMPACT_POLICY) - observed)
        raise ReviewBuildError(
            f"impact policy does not exactly cover issue codes: missing={missing}, unused={unused}"
        )
    rows = []
    for group in issue_groups:
        policy = IMPACT_POLICY[group["code"]]
        implicated = set(group["implicated_object_refs"])
        affected = sorted(set(group["direct_affected_refs"]) | implicated)
        rows.append(
            {
                "schema_version": "phase3-review-issue-impact-v0",
                "policy_version": IMPACT_POLICY_VERSION,
                "code": group["code"],
                "issue_count": group["issue_count"],
                "affected_record_count": len(affected),
                "affected_refs": affected,
                "taxonomy": policy["taxonomy"],
                "migration": policy["migration"],
                "compilation": policy["compilation"],
                "rationale": policy["rationale"],
                "evidence_boundary": (
                    "Impact levels are engineering review routing, not proof of taxonomy "
                    "invalidity or ARM compilation failure."
                ),
            }
        )
    return rows


def _impact_summary(impact_rows: list[dict[str, Any]]) -> dict[str, Any]:
    result = {}
    for dimension in ("taxonomy", "migration", "compilation"):
        material_rows = [
            row for row in impact_rows if row[dimension] in {"material", "blocking"}
        ]
        refs = sorted({ref for row in material_rows for ref in row["affected_refs"]})
        by_kind = Counter(
            "object" if ":object:" in ref else
            "graph" if ":graph:" in ref else
            "source" if ":source:" in ref else "global"
            for ref in refs
        )
        result[dimension] = {
            "material_issue_class_count": len(material_rows),
            "unique_affected_record_count": len(refs),
            "affected_by_kind": [
                {"kind": kind, "count": by_kind[kind]} for kind in sorted(by_kind)
            ],
            "issue_codes": [row["code"] for row in material_rows],
        }
    return result


def _graph_sample_candidate(
    graph: dict[str, Any], issues_by_graph: dict[int, list[dict[str, Any]]], kind: str
) -> dict[str, Any]:
    instances = graph["instances"]
    nets = graph["nets"]
    issue_counts = Counter(issue["code"] for issue in issues_by_graph.get(graph["graph_index"], []))
    return {
        "schema_version": "phase3-review-graph-sample-v0",
        "sample_kind": kind,
        "evidence_ref": graph_ref(graph["graph_index"]),
        "graph_index": graph["graph_index"],
        "source": graph["source"],
        "export_status": graph["export_status"],
        "instance_count": len(instances),
        "net_count": len(nets),
        "resolution_status_counts": [
            {"status": status, "count": count}
            for status, count in sorted(
                Counter(item["resolution"]["status"] for item in instances).items()
            )
        ],
        "zombie_counts": [
            {"kind": zombie_kind, "count": count}
            for zombie_kind, count in sorted(
                Counter(item["zombie_kind"] for item in instances if item["zombie_kind"] != "none").items()
            )
        ],
        "issue_counts": [
            {"code": code, "count": issue_counts[code]} for code in sorted(issue_counts)
        ],
        "requested_types": sorted(
            {
                item["requested_type"]["name"]
                for item in instances
                if item["requested_type"]["name"] is not None
            }
        ),
    }


def build_graph_samples(
    graphs: list[dict[str, Any]], issues: list[dict[str, Any]], status: str
) -> list[dict[str, Any]]:
    issues_by_graph: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for issue in issues:
        if issue["location"]["graph_index"] is not None:
            issues_by_graph[issue["location"]["graph_index"]].append(issue)
    candidates = [
        _graph_sample_candidate(graph, issues_by_graph, status)
        for graph in graphs
        if graph["export_status"] == status
    ]
    return deterministic_sample(candidates, f"graph-{status}", "evidence_ref")


def build_overload_sample(
    ambiguous_evidence: list[dict[str, Any]], objects: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    objects_by_index = {item["variant_index"]: item for item in objects}
    candidates = []
    for evidence in ambiguous_evidence:
        row = {
            "schema_version": "phase3-review-overload-selection-sample-v0",
            **evidence,
            "candidate_definitions": [
                _candidate_summary(objects_by_index[index])
                for index in evidence["candidate_variant_indexes"]
            ],
        }
        candidates.append(row)
    return deterministic_sample(candidates, "overloaded-selection", "evidence_ref")


def build_object_sample(objects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = []
    for item in objects:
        source_id = _source_for_object(item)
        stratum = f"{item['origin']['kind']}|{item['legacy_kind']}|{source_id}"
        candidates.append(
            {
                "schema_version": "phase3-review-object-sample-v0",
                "evidence_ref": object_ref(item["variant_index"]),
                "variant_index": item["variant_index"],
                "stratum": stratum,
                "selection_stage": None,
                "legacy_id": item["legacy_id"],
                "legacy_kind": item["legacy_kind"],
                "legacy_class": item["legacy_class"],
                "export_status": item["export_status"],
                "origin": _origin_summary(item),
                "uuid": item["uuid"],
                "metadata": item["metadata"],
                "facet_counts": _facet_counts(item),
            }
        )
    by_stratum: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidates:
        row["rank_sha256"] = _rank("representative-object", row["evidence_ref"])
        by_stratum[row["stratum"]].append(row)
    selected = []
    used = set()
    for stratum in sorted(by_stratum):
        winner = min(
            by_stratum[stratum], key=lambda row: (row["rank_sha256"], row["evidence_ref"])
        )
        winner["selection_stage"] = "stratum"
        selected.append(winner)
        used.add(winner["evidence_ref"])
    remaining = sorted(
        (row for row in candidates if row["evidence_ref"] not in used),
        key=lambda row: (row["rank_sha256"], row["evidence_ref"]),
    )
    for row in remaining[: max(0, SAMPLE_SIZE - len(selected))]:
        row["selection_stage"] = "fill"
        selected.append(row)
    selected.sort(key=lambda row: (row["selection_stage"] != "stratum", row["rank_sha256"]))
    return selected[:SAMPLE_SIZE]


def _count_machine_paths(root: Path) -> int:
    markers = (b"/Users/", b"/home/", b"/tmp/", b"/var/folders/", b":\\Users\\")
    hits = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        data = path.read_bytes()
        hits += sum(data.count(marker) for marker in markers)
    return hits


def _generated_files(root: Path) -> list[dict[str, str]]:
    return [
        {"path": path.relative_to(root).as_posix(), "sha256": sha256_file(path)}
        for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix())
        if path.is_file() and path.name != "manifest.json"
    ]


def _summary_markdown(
    summary: dict[str, Any], issue_groups: list[dict[str, Any]],
    impact_rows: list[dict[str, Any]], matrix: dict[str, Any],
    partial_report: dict[str, Any],
) -> str:
    impact_by_code = {row["code"]: row for row in impact_rows}
    lines = [
        "# Phase 3 inventory review gate",
        "",
        "The frozen Phase 3 snapshot is deterministic evidence, not a fully resolved Schuss catalog.",
        "This packet separates observed counts from engineering review routing.",
        "",
        "## Object census reconciliation",
        "",
        "- 3,417 definition occurrences + 134 catalog subpatch placeholders + 51 provider-only records = 3,602 exported objects.",
        "- 3,417 definition occurrences - 3 legacy-equality collapses + 134 placeholders = 3,548 retained ObjectList entries.",
        "- The 54 exported records absent from ObjectList are the three preserved collapsed occurrences plus 51 provider-only records.",
        "",
        "## Unique material review impact",
        "",
        "Impact means that the item needs explicit handling before the named workflow relies on it; compilation impact is not proof of an ARM compile failure.",
        "",
        "| Dimension | Material issue classes | Unique affected records |",
        "| --- | ---: | ---: |",
    ]
    for dimension in ("taxonomy", "migration", "compilation"):
        value = summary["material_impact"][dimension]
        lines.append(
            f"| {dimension.title()} | {value['material_issue_class_count']} | {value['unique_affected_record_count']} |"
        )
    lines.extend(
        [
            "",
            "## Issues by code",
            "",
            "| Code | Issues | Direct records | Locations | Taxonomy | Migration | Compilation |",
            "| --- | ---: | ---: | ---: | --- | --- | --- |",
        ]
    )
    for group in issue_groups:
        impact = impact_by_code[group["code"]]
        lines.append(
            f"| `{group['code']}` | {group['issue_count']} | "
            f"{group['direct_affected_record_count']} | {group['unique_location_count']} | "
            f"{impact['taxonomy']} | {impact['migration']} | {impact['compilation']} |"
        )
    lines.extend(
        [
            "",
            "## Graph status by source and type",
            "",
            "| Source | Type | Complete | Partial | Failed |",
            "| --- | --- | ---: | ---: | ---: |",
        ]
    )
    matrix_counts = {
        (row["source_id"], row["file_type"], row["status"]): row["count"]
        for row in matrix["rows"]
    }
    source_ids = [row["source_id"] for row in matrix["by_source"]]
    for source_id in source_ids:
        for file_type in GRAPH_TYPES:
            lines.append(
                f"| {source_id} | {file_type} | "
                f"{matrix_counts[(source_id, file_type, 'complete')]} | "
                f"{matrix_counts[(source_id, file_type, 'partial')]} | "
                f"{matrix_counts[(source_id, file_type, 'failed')]} |"
            )
    lines.extend(
        [
            "",
            "## Partial graph reasons",
            "",
            "Reason groups overlap; reason combinations in `reports/partial-graphs.json` form the exact 805-graph partition.",
            "",
            "| Reason | Graphs | Issues |",
            "| --- | ---: | ---: |",
        ]
    )
    for row in sorted(
        partial_report["reason_groups"], key=lambda value: (-value["graph_count"], value["code"])
    ):
        lines.append(f"| `{row['code']}` | {row['graph_count']} | {row['issue_count']} |")
    lines.extend(
        [
            "",
            "## Gate conclusion",
            "",
            "The resolved catalog is suitable as frozen evidence and as an input to a separate Phase 4 classification overlay. Complete graphs may provide strong reference-frequency evidence; partial graph references must remain lower-confidence and retain their reason codes. Migration and compilation work must preserve overload candidates, embedded-definition opacity, zombie context, and missing-net diagnostics rather than treating the legacy selected object as definitive.",
            "",
        ]
    )
    return "\n".join(lines)


def _generate_once(snapshot: Path, destination: Path, input_hashes: list[dict[str, str]]) -> None:
    manifest = load_json(snapshot / "manifest.json")
    objects = load_jsonl(snapshot / "resolved/objects.jsonl")
    graphs = load_jsonl(snapshot / "resolved/graphs.jsonl")
    issues = load_jsonl(snapshot / "resolved/issues.jsonl")
    resolved_summary = load_json(snapshot / "reports/summary.json")

    issue_groups = build_issue_groups(issues, objects)
    reconciliation = build_object_reconciliation(objects, issues)
    overload_groups, ambiguous_evidence = build_overload_groups(objects, graphs)
    zombie_groups = build_zombie_groups(graphs)
    partial_report = build_partial_graph_report(graphs, issues)
    graph_matrix = build_graph_status_matrix(manifest, graphs)
    facet_coverage = build_facet_coverage(objects)
    impact_rows = build_impact_rows(issue_groups)
    impact_summary = _impact_summary(impact_rows)
    complete_sample = build_graph_samples(graphs, issues, "complete")
    partial_sample = build_graph_samples(graphs, issues, "partial")
    overload_sample = build_overload_sample(ambiguous_evidence, objects)
    object_sample = build_object_sample(objects)

    summary = {
        "schema_version": "phase3-review-summary-v0",
        "input_counts": {
            "objects": len(objects),
            "graphs": len(graphs),
            "issues": len(issues),
            "definition_occurrences": reconciliation["definition_occurrences"],
            "retained_in_legacy_object_list": reconciliation["retained_in_legacy_object_list"],
            "overloaded_name_groups": len(overload_groups),
            "resolution_created_zombies": sum(row["occurrence_count"] for row in zombie_groups),
            "partial_graphs": partial_report["partial_graph_count"],
        },
        "issue_classes": len(issue_groups),
        "direct_unique_affected_records": len(
            {ref for row in issue_groups for ref in row["direct_affected_refs"]}
        ),
        "implicated_unique_objects": len(
            {ref for row in issue_groups for ref in row["implicated_object_refs"]}
        ),
        "material_impact": impact_summary,
        "samples": {
            "method": SAMPLE_METHOD,
            "seed": SAMPLE_SEED,
            "sample_size": SAMPLE_SIZE,
            "complete_graphs": len(complete_sample),
            "partial_graphs": len(partial_sample),
            "overloaded_selections": len(overload_sample),
            "representative_objects": len(object_sample),
        },
        "portability": {
            "snapshot_machine_path_hits": _count_machine_paths(snapshot),
            "packet_machine_path_hits": 0,
        },
        "evidence_boundary": (
            "Observed counts come from the frozen resolved snapshot. Impact levels are "
            "engineering review routing and do not prove taxonomy invalidity, ARM "
            "compile/link failure, connected-board behavior, or audible behavior."
        ),
    }

    expected = resolved_summary
    if (
        reconciliation["definition_occurrences"] != expected["objects"]["definition_occurrences"]
        or reconciliation["retained_in_legacy_object_list"]
        != expected["objects"]["retained_in_legacy_object_list"]
        or reconciliation["exported_object_records"] != expected["objects"]["records"]
        or len(overload_groups) != expected["objects"]["overloaded_name_groups"]
        or partial_report["partial_graph_count"] != expected["graphs"]["partial"]
        or sum(row["occurrence_count"] for row in zombie_groups)
        != expected["graphs"]["created_zombies"]
    ):
        raise ReviewBuildError("review reports do not reconcile with the resolved summary")

    _write_json(destination / "reports/summary.json", summary)
    (destination / "reports/summary.md").write_text(
        _summary_markdown(summary, issue_groups, impact_rows, graph_matrix, partial_report),
        encoding="utf-8",
        newline="\n",
    )
    _write_jsonl(destination / "reports/issues-by-code.jsonl", issue_groups)
    _write_json(destination / "reports/object-reconciliation.json", reconciliation)
    _write_jsonl(destination / "reports/overloaded-name-groups.jsonl", overload_groups)
    _write_jsonl(destination / "reports/resolution-created-zombies.jsonl", zombie_groups)
    _write_json(destination / "reports/partial-graphs.json", partial_report)
    _write_json(destination / "reports/graph-status-matrix.json", graph_matrix)
    _write_json(destination / "reports/facet-coverage.json", facet_coverage)
    _write_jsonl(destination / "reports/issue-impact.jsonl", impact_rows)
    _write_jsonl(destination / "samples/complete-graphs.jsonl", complete_sample)
    _write_jsonl(destination / "samples/partial-graphs.jsonl", partial_sample)
    _write_jsonl(destination / "samples/overloaded-selections.jsonl", overload_sample)
    _write_jsonl(destination / "samples/representative-objects.jsonl", object_sample)

    if _count_machine_paths(destination) != 0:
        raise ReviewBuildError("generated review reports contain a machine-specific path")
    generated_files = _generated_files(destination)
    review_manifest = {
        "schema_version": SCHEMA_VERSION,
        "generator": {
            "name": "build_phase3_review_packet.py",
            "version": GENERATOR_VERSION,
        },
        "input_snapshot": {
            "schema_version": manifest["schema_version"],
            "files": input_hashes,
        },
        "sample_selection": {
            "method": SAMPLE_METHOD,
            "seed": SAMPLE_SEED,
            "sample_size": SAMPLE_SIZE,
        },
        "impact_policy_version": IMPACT_POLICY_VERSION,
        "options": {
            "snapshot_mutation": False,
            "timestamp_included": False,
            "random_runtime_values": False,
        },
        "generated_files": generated_files,
    }
    _write_json(destination / "manifest.json", review_manifest)
    if _count_machine_paths(destination) != 0:
        raise ReviewBuildError("review manifest contains a machine-specific path")


def _compare_trees(first: Path, second: Path) -> None:
    first_files = [
        path.relative_to(first).as_posix()
        for path in sorted(first.rglob("*"))
        if path.is_file()
    ]
    second_files = [
        path.relative_to(second).as_posix()
        for path in sorted(second.rglob("*"))
        if path.is_file()
    ]
    if first_files != second_files:
        raise ReviewBuildError("fresh review generations produced different file sets")
    for relative in first_files:
        if (first / relative).read_bytes() != (second / relative).read_bytes():
            raise ReviewBuildError(f"fresh review generations differ: {relative}")


def build_review_packet(snapshot: Path, output: Path) -> dict[str, int]:
    snapshot = snapshot.resolve()
    output = output.resolve()
    if not snapshot.is_dir():
        raise ReviewBuildError(f"resolved snapshot does not exist: {snapshot}")
    try:
        output.relative_to(snapshot)
    except ValueError:
        pass
    else:
        raise ReviewBuildError("review packet must not be written inside the frozen snapshot")
    if output.exists() and any(output.iterdir()):
        raise ReviewBuildError(f"output directory is not empty: {output}")

    repository_root = Path(__file__).resolve().parents[2]
    raw_snapshot = repository_root / "catalog/snapshots/legacy-catalog-v0"
    source_lock = repository_root / "catalog/sources.lock.json"
    validate_inventory(
        snapshot,
        source_lock=source_lock,
        raw_snapshot=raw_snapshot,
    )
    before = snapshot_file_hashes(snapshot)
    with tempfile.TemporaryDirectory(prefix="schuss-phase3-review-") as temporary:
        root = Path(temporary)
        first = root / "run-1"
        second = root / "run-2"
        _generate_once(snapshot, first, before)
        _generate_once(snapshot, second, before)
        _compare_trees(first, second)
        from validate_phase3_review_packet import validate_review_packet

        counts = validate_review_packet(first, snapshot=snapshot)
        validate_review_packet(second, snapshot=snapshot)
        if snapshot_file_hashes(snapshot) != before:
            raise ReviewBuildError("frozen Phase 3 snapshot changed during review generation")
        if output.exists():
            shutil.copytree(first, output, dirs_exist_ok=True)
        else:
            shutil.copytree(first, output)
    if snapshot_file_hashes(snapshot) != before:
        raise ReviewBuildError("frozen Phase 3 snapshot changed while materializing review packet")
    return counts


def main() -> int:
    repository_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description="Build the deterministic Phase 3 inventory review packet twice"
    )
    parser.add_argument(
        "--snapshot",
        type=Path,
        default=repository_root / "catalog/snapshots/legacy-resolved-catalog-v0",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        counts = build_review_packet(args.snapshot, args.output)
    except (ReviewBuildError, OSError, KeyError, TypeError, ValueError) as exception:
        print(f"phase 3 review build failed: {exception}")
        return 1
    print(json.dumps({"ok": True, **counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
