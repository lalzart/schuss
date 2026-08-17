#!/usr/bin/env python3
"""Fail-closed Task 029 machine, source-review, presentation, and panel rules."""

from __future__ import annotations

import copy
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

import validator_core as core


SCHEMA_SPECS = {
    "machine_source_reviews": ("machine-source-review-v0.schema.json", "machine-source-review-v0", "machine_source_review_id"),
    "panel_layouts": ("panel-layout-v0.schema.json", "panel-layout-v0", "panel_layout_id"),
    "machine_presentations": ("machine-presentation-v0.schema.json", "machine-presentation-v0", "machine_presentation_id"),
    "machines": ("machine-v0.schema.json", "machine-v0", "machine_id"),
}

EXPECTED_REVIEW_SLOTS = {
    *(f"device-input-{number:06d}" for number in range(1, 11)),
    *(f"device-gesture-{number:06d}" for number in range(1, 17)),
    *(f"device-feedback-{number:06d}" for number in range(1, 7)),
    *(f"device-display-{number:06d}" for number in range(1, 3)),
}

UNRESOLVED_MACHINE_DEPENDENCIES = {
    "catalogued-only",
    "observed-only",
    "absent",
    "unsuitable-for-standalone-promotion",
    "unsupported",
}


def _ref(value: dict[str, Any], field: str) -> tuple[str, int, str]:
    return value[field], value["revision"], value["content_hash"]


def _registry(values: Iterable[dict[str, Any]], field: str) -> dict[tuple[str, int, str], dict[str, Any]]:
    return {_ref(value, field): value for value in values}


def _diagnostic(
    diagnostics: list[core.Diagnostic],
    code: str,
    subject: str,
    location: str,
    message: str,
) -> None:
    core.add_diagnostic(diagnostics, code, subject, location, message)


def _structural(
    groups: dict[str, list[dict[str, Any]]],
    schemas: dict[str, dict[str, Any]],
    diagnostics: list[core.Diagnostic],
) -> dict[str, list[dict[str, Any]]]:
    valid: dict[str, list[dict[str, Any]]] = {}
    for group, (schema_name, version, id_field) in SCHEMA_SPECS.items():
        valid[group] = core.validate_structural_records(
            groups[group], schemas[group], schema_name, version, id_field, diagnostics
        )
    return valid


def _device_slots(device: dict[str, Any]) -> dict[str, str]:
    slots: dict[str, str] = {}
    for collection, field, kind in (
        ("input_controls", "slot_id", "input-control"),
        ("gestures", "gesture_id", "gesture"),
        ("feedback_outputs", "slot_id", "feedback-output"),
        ("displays", "slot_id", "display"),
    ):
        for item in device[collection]:
            slots[item[field]] = kind
    return slots


def _asset_path(repository_root: Path, portable_path: str) -> Path | None:
    path = repository_root / portable_path
    try:
        path.resolve().relative_to(repository_root.resolve())
    except ValueError:
        return None
    return path


def _validate_svg(
    panel: dict[str, Any], repository_root: Path, diagnostics: list[core.Diagnostic]
) -> set[str]:
    subject = core.record_subject(panel)
    path = _asset_path(repository_root, panel["asset"]["portable_path"])
    if path is None or not path.is_file():
        _diagnostic(diagnostics, "MACHINE_PANEL_ASSET_UNRESOLVED", subject, "$.asset.portable_path", "the panel SVG is absent or escapes the repository")
        return set()
    if core.sha256_file(path) != panel["asset"]["byte_sha256"]:
        _diagnostic(diagnostics, "MACHINE_PANEL_ASSET_HASH_MISMATCH", subject, "$.asset.byte_sha256", "the panel SVG byte hash does not match the exact asset")
    data = path.read_bytes()
    if b"\r" in data or not data.endswith(b"\n"):
        _diagnostic(diagnostics, "MACHINE_PANEL_ASSET_ENCODING_INVALID", subject, "$.asset", "the panel SVG must use LF-terminated UTF-8 bytes")
    if re.search(rb"(?:href|src)\s*=\s*['\"](?:https?:|file:|data:)", data, re.IGNORECASE):
        _diagnostic(diagnostics, "MACHINE_PANEL_ASSET_EXTERNAL_REFERENCE", subject, "$.asset", "the panel SVG must be self-contained and contain no external or embedded raster references")
    if re.search(rb"<image\b", data, re.IGNORECASE):
        _diagnostic(diagnostics, "MACHINE_PANEL_ASSET_RASTER_PRESENT", subject, "$.asset", "the panel SVG must not embed raster images")
    try:
        root = ET.fromstring(data)
    except (ET.ParseError, ValueError) as exc:
        _diagnostic(diagnostics, "MACHINE_PANEL_ASSET_XML_INVALID", subject, "$.asset", f"the panel SVG is not well-formed XML: {exc}")
        return set()
    if root.tag.rsplit("}", 1)[-1] != "svg":
        _diagnostic(diagnostics, "MACHINE_PANEL_ASSET_ROOT_INVALID", subject, "$.asset", "the asset root must be SVG")
    if root.attrib.get("viewBox") != "0 0 158 100" or root.attrib.get("width") != "158mm" or root.attrib.get("height") != "100mm":
        _diagnostic(diagnostics, "MACHINE_PANEL_GEOMETRY_INVALID", subject, "$.asset", "the editable SVG must use the exact 158 by 100 mm v0.6 coordinate system")
    ids = [value for element in root.iter() if (value := element.attrib.get("id")) is not None]
    duplicates = sorted(value for value, count in Counter(ids).items() if count != 1)
    if duplicates:
        _diagnostic(diagnostics, "MACHINE_PANEL_SVG_ID_DUPLICATE", subject, "$.asset", "SVG IDs must be globally unique: " + ", ".join(duplicates))
    return set(ids)


def _validate_panel(
    panel: dict[str, Any],
    devices: dict[tuple[str, int, str], dict[str, Any]],
    repository_root: Path,
    diagnostics: list[core.Diagnostic],
) -> None:
    subject = core.record_subject(panel)
    device = devices.get(_ref(panel["device_profile_reference"], "device_profile_id"))
    if device is None:
        _diagnostic(diagnostics, "MACHINE_PANEL_DEVICE_UNRESOLVED", subject, "$.device_profile_reference", "the exact device profile does not resolve")
        return
    slot_kinds = _device_slots(device)
    regions = panel["semantic_regions"]
    region_slots = [item["semantic_slot_id"] for item in regions]
    excluded = [item["semantic_slot_id"] for item in panel["excluded_slots"]]
    if len(region_slots) != len(set(region_slots)):
        _diagnostic(diagnostics, "MACHINE_PANEL_SEMANTIC_SLOT_DUPLICATE", subject, "$.semantic_regions", "each semantic device slot may occur once")
    represented_expected = set(slot_kinds) - {"device-input-000019"}
    if set(region_slots) != represented_expected or set(excluded) != {"device-input-000019"}:
        _diagnostic(diagnostics, "MACHINE_PANEL_SLOT_COVERAGE_INVALID", subject, "$.semantic_regions", "the map must represent all 42 qualified panel slots and explicitly exclude only the unanchored power switch")
    for index, region in enumerate(regions):
        expected_kind = slot_kinds.get(region["semantic_slot_id"])
        if expected_kind != region["slot_kind"]:
            _diagnostic(diagnostics, "MACHINE_PANEL_SLOT_KIND_MISMATCH", subject, f"$.semantic_regions[{index}]", "semantic region kind does not match the exact device profile")
    anchors: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for region in regions:
        anchor = (region["anchor"]["x"], region["anchor"]["y"])
        anchors.setdefault(anchor, []).append(region)
    for anchor, shared_regions in anchors.items():
        targets = {
            (item["svg_element_id"], item["highlight_element_id"])
            for item in shared_regions
        }
        if len(shared_regions) > 1 and len(targets) != 1:
            _diagnostic(
                diagnostics,
                "MACHINE_PANEL_SHARED_ANCHOR_INVALID",
                subject,
                "$.semantic_regions",
                f"semantic slots sharing anchor {anchor[0]},{anchor[1]} must share one reviewed physical region",
            )
    ids = _validate_svg(panel, repository_root, diagnostics)
    for index, region in enumerate(regions):
        for field in ("svg_element_id", "highlight_element_id"):
            if region[field] not in ids:
                _diagnostic(diagnostics, "MACHINE_PANEL_SVG_TARGET_UNRESOLVED", subject, f"$.semantic_regions[{index}].{field}", "semantic panel target is absent from the exact SVG")
    shared = {
        slot: next(item for item in regions if item["semantic_slot_id"] == slot)
        for slot in (
            "device-feedback-000003", "device-feedback-000004",
            "device-feedback-000005", "device-feedback-000006",
            "device-display-000001", "device-display-000002",
        )
        if slot in region_slots
    }
    for left, right in (("device-feedback-000003", "device-feedback-000004"), ("device-feedback-000005", "device-feedback-000006"), ("device-display-000001", "device-display-000002")):
        if left in shared and right in shared and (
            shared[left]["svg_element_id"] != shared[right]["svg_element_id"]
            or shared[left]["highlight_element_id"] != shared[right]["highlight_element_id"]
        ):
            _diagnostic(diagnostics, "MACHINE_PANEL_SHARED_REGION_INVALID", subject, "$.semantic_regions", "dual semantic channels must share their one physical LED or OLED region without sharing semantic identity")
    levels = panel["evidence_levels"]
    if [item["level"] for item in levels] != list(range(1, 9)) or [item["status"] for item in levels] != ["passed"] + ["not-run"] * 7:
        _diagnostic(diagnostics, "MACHINE_EVIDENCE_BOUNDARY_INVALID", subject, "$.evidence_levels", "panel evidence may pass only local structural level 1")


def _validate_exact_matches(
    review: dict[str, Any],
    domain_records: dict[str, list[dict[str, Any]]],
    diagnostics: list[core.Diagnostic],
) -> None:
    subject = core.record_subject(review)
    match_specs = {
        "component-contract": ("contracts", "component_contract_id"),
        "implementation-binding": ("bindings", "implementation_id"),
        "device-profile": ("devices", "device_profile_id"),
        "binding-eligibility": ("eligibility", "binding_eligibility_id"),
    }
    registries = {
        kind: _registry(domain_records[group], field)
        for kind, (group, field) in match_specs.items()
    }
    catalogs = _registry(domain_records["catalog"], "catalog_id")
    projection_text = core.canonical_json(domain_records.get("catalog_projection", []))
    for dep_index, dependency in enumerate(review["dependency_assessments"]):
        for match_index, match in enumerate(dependency["schuss_matches"]):
            kind = match["record_kind"]
            key = (match["stable_id"], match["revision"], match["content_hash"])
            if key not in registries[kind]:
                _diagnostic(diagnostics, "MACHINE_DEPENDENCY_MATCH_UNRESOLVED", subject, f"$.dependency_assessments[{dep_index}].schuss_matches[{match_index}]", "the exact Schuss semantic match is absent")
        for observation_index, observation in enumerate(dependency["catalog_observations"]):
            catalog = catalogs.get(_ref(observation["catalog_reference"], "catalog_id"))
            if catalog is None or (
                observation["stable_id"] not in core.canonical_json(catalog)
                and observation["stable_id"] not in projection_text
            ):
                _diagnostic(diagnostics, "MACHINE_DEPENDENCY_CATALOG_OBSERVATION_UNRESOLVED", subject, f"$.dependency_assessments[{dep_index}].catalog_observations[{observation_index}]", "the exact catalog corpus does not contain the observed identity")


def _validate_review(
    review: dict[str, Any],
    panels: list[dict[str, Any]],
    domain_records: dict[str, list[dict[str, Any]]],
    diagnostics: list[core.Diagnostic],
) -> None:
    subject = core.record_subject(review)
    files = review["source_identity"]["files"]
    file_ids = [item["source_file_id"] for item in files]
    if len(file_ids) != len(set(file_ids)):
        _diagnostic(diagnostics, "MACHINE_SOURCE_FILE_ID_DUPLICATE", subject, "$.source_identity.files", "source file IDs must be unique")
    spans = review["evidence_spans"]
    span_ids = [item["evidence_span_id"] for item in spans]
    if len(span_ids) != len(set(span_ids)):
        _diagnostic(diagnostics, "MACHINE_SOURCE_SPAN_ID_DUPLICATE", subject, "$.evidence_spans", "source span IDs must be unique")
    for index, span in enumerate(spans):
        source = span["source"]
        if source["source_file_id"] not in file_ids:
            _diagnostic(diagnostics, "MACHINE_SOURCE_SPAN_FILE_UNRESOLVED", subject, f"$.evidence_spans[{index}]", "source span names an absent exact file")
        if source["line_end"] < source["line_start"]:
            _diagnostic(diagnostics, "MACHINE_SOURCE_SPAN_RANGE_INVALID", subject, f"$.evidence_spans[{index}]", "source span end must not precede its start")
    known_spans = set(span_ids)
    blocks = review["source_blocks"]
    block_ids = [item["source_block_id"] for item in blocks]
    edge_ids = [item["source_edge_id"] for item in review["source_edges"]]
    mapping_ids = [item["mapping_id"] for item in review["panel_mappings"]]
    dependency_ids = [item["dependency_id"] for item in review["dependency_assessments"]]
    for values, code, location in (
        (block_ids, "MACHINE_SOURCE_BLOCK_ID_DUPLICATE", "$.source_blocks"),
        (edge_ids, "MACHINE_SOURCE_EDGE_ID_DUPLICATE", "$.source_edges"),
        (mapping_ids, "MACHINE_SOURCE_MAPPING_ID_DUPLICATE", "$.panel_mappings"),
        (dependency_ids, "MACHINE_DEPENDENCY_ID_DUPLICATE", "$.dependency_assessments"),
    ):
        if len(values) != len(set(values)):
            _diagnostic(diagnostics, code, subject, location, "stable local IDs must be unique")
    for collection_name in ("source_blocks", "source_edges", "panel_mappings", "dependency_assessments", "resource_declarations"):
        for index, value in enumerate(review[collection_name]):
            if not set(value["evidence_span_ids"]) <= known_spans:
                _diagnostic(diagnostics, "MACHINE_SOURCE_EVIDENCE_UNRESOLVED", subject, f"$.{collection_name}[{index}].evidence_span_ids", "source evidence reference does not resolve")
    known_blocks = set(block_ids)
    for index, edge in enumerate(review["source_edges"]):
        if {edge["source_block_id"], edge["destination_block_id"]} - known_blocks:
            _diagnostic(diagnostics, "MACHINE_SOURCE_EDGE_BLOCK_UNRESOLVED", subject, f"$.source_edges[{index}]", "source edge names an absent explanatory block")
    mappings = review["panel_mappings"]
    mapping_slots = [item["semantic_slot_id"] for item in mappings]
    if len(mapping_slots) != len(set(mapping_slots)) or set(mapping_slots) != EXPECTED_REVIEW_SLOTS:
        _diagnostic(diagnostics, "MACHINE_SOURCE_MAPPING_COVERAGE_INVALID", subject, "$.panel_mappings", "the review must account once for ten performance pots, all gestures, six feedback channels, and two display capabilities")
    panel_slots = {item["semantic_slot_id"] for panel in panels for item in panel["semantic_regions"]}
    if not set(mapping_slots) <= panel_slots:
        _diagnostic(diagnostics, "MACHINE_SOURCE_MAPPING_PANEL_UNRESOLVED", subject, "$.panel_mappings", "source mapping names a semantic slot absent from the authenticated panel map")
    identity = review["asserted_identity"]
    if identity["display_name"] == "Pamulist":
        _diagnostic(diagnostics, "MACHINE_SOURCE_IDENTITY_ALIAS_INVALID", subject, "$.asserted_identity.display_name", "Pamulist is corrected input evidence, not stable product identity")
    if identity["display_name"] == "Palimpsest":
        expected_alias = [{"input": "Pamulist", "disposition": "corrected-input-only", "correction": "Palimpsest"}]
        if identity["aliases"] != expected_alias:
            _diagnostic(diagnostics, "MACHINE_SOURCE_IDENTITY_CORRECTION_MISSING", subject, "$.asserted_identity.aliases", "Palimpsest must retain the Pamulist correction as input-only evidence")
    if identity["display_name"] == "Tide Pit":
        byte_total = sum(item["quantity"] for item in review["resource_declarations"] if item["unit"] == "bytes")
        if byte_total != 251408:
            _diagnostic(diagnostics, "MACHINE_TIDE_PIT_RESOURCE_TOTAL_INVALID", subject, "$.resource_declarations", "Tide Pit source-declared SDRAM allocations must total exactly 251408 bytes")
        rings = [item for item in review["dependency_assessments"] if item["dependency_id"] == "rings-reverb-non-dependency"]
        if len(rings) != 1 or rings[0]["required"] or rings[0]["classification"] != "unsupported":
            _diagnostic(diagnostics, "MACHINE_TIDE_PIT_RINGS_BOUNDARY_INVALID", subject, "$.dependency_assessments", "the unrelated Rings binding must remain a non-required unsupported non-dependency")
    levels = review["evidence_levels"]
    if [item["level"] for item in levels] != list(range(1, 9)) or [item["status"] for item in levels] != ["passed"] + ["not-run"] * 7:
        _diagnostic(diagnostics, "MACHINE_EVIDENCE_BOUNDARY_INVALID", subject, "$.evidence_levels", "source review may pass only local structural level 1")
    _validate_exact_matches(review, domain_records, diagnostics)


def _validate_presentation(
    presentation: dict[str, Any],
    reviews: dict[tuple[str, int, str], dict[str, Any]],
    panels: dict[tuple[str, int, str], dict[str, Any]],
    diagnostics: list[core.Diagnostic],
) -> None:
    subject = core.record_subject(presentation)
    review = reviews.get(_ref(presentation["source_review_reference"], "machine_source_review_id"))
    panel = panels.get(_ref(presentation["panel_layout_reference"], "panel_layout_id"))
    if review is None or panel is None:
        _diagnostic(diagnostics, "MACHINE_PRESENTATION_REFERENCE_UNRESOLVED", subject, "$", "presentation source review and panel layout must resolve exactly")
        return
    blocks = presentation["blocks"]
    block_ids = [item["presentation_block_id"] for item in blocks]
    if len(block_ids) != len(set(block_ids)):
        _diagnostic(diagnostics, "MACHINE_PRESENTATION_BLOCK_ID_DUPLICATE", subject, "$.blocks", "presentation block IDs must be unique")
    expected_source_blocks = {item["source_block_id"] for item in review["source_blocks"]}
    traced_source_blocks = [source_id for block in blocks for source_id in block["source_block_ids"]]
    if len(traced_source_blocks) != len(set(traced_source_blocks)) or set(traced_source_blocks) != expected_source_blocks:
        _diagnostic(diagnostics, "MACHINE_PRESENTATION_SOURCE_TRACE_INVALID", subject, "$.blocks", "presentation blocks must trace every source block exactly once")
    if presentation["presentation_state"] == "inspection-only" and any(block["graph_node_references"] for block in blocks):
        _diagnostic(diagnostics, "MACHINE_PRESENTATION_INSPECTION_GRAPH_CLAIM_INVALID", subject, "$.blocks", "inspection-only blocks cannot claim authoritative graph nodes")
    if presentation["presentation_state"] == "machine-complete" and any(not block["graph_node_references"] for block in blocks):
        _diagnostic(diagnostics, "MACHINE_PRESENTATION_GRAPH_TRACE_INCOMPLETE", subject, "$.blocks", "completed-machine blocks require exact graph-node traces")
    known_blocks = set(block_ids)
    source_edges = {item["source_edge_id"] for item in review["source_edges"]}
    traced_edges: list[str] = []
    for index, edge in enumerate(presentation["edges"]):
        if {edge["source_block_id"], edge["destination_block_id"]} - known_blocks:
            _diagnostic(diagnostics, "MACHINE_PRESENTATION_EDGE_BLOCK_UNRESOLVED", subject, f"$.edges[{index}]", "presentation edge names an absent block")
        if not set(edge["source_edge_ids"]) <= source_edges:
            _diagnostic(diagnostics, "MACHINE_PRESENTATION_EDGE_TRACE_UNRESOLVED", subject, f"$.edges[{index}]", "presentation edge trace names an absent source edge")
        traced_edges.extend(edge["source_edge_ids"])
    if set(traced_edges) != source_edges:
        _diagnostic(diagnostics, "MACHINE_PRESENTATION_EDGE_TRACE_INCOMPLETE", subject, "$.edges", "presentation must trace every source edge")
    mappings = {item["mapping_id"]: item for item in review["panel_mappings"]}
    mapped = {key for key, value in mappings.items() if value["mapping_state"] == "mapped"}
    links = presentation["panel_links"]
    linked = [item["source_mapping_id"] for item in links]
    panel_slots = {item["semantic_slot_id"] for item in panel["semantic_regions"]}
    if len(linked) != len(set(linked)) or set(linked) != mapped:
        _diagnostic(diagnostics, "MACHINE_PRESENTATION_PANEL_LINK_COVERAGE_INVALID", subject, "$.panel_links", "every mapped source mapping and no intentionally-unmapped mapping must be linked exactly once")
    for index, link in enumerate(links):
        source_mapping = mappings.get(link["source_mapping_id"])
        if link["presentation_block_id"] not in known_blocks or link["semantic_slot_id"] not in panel_slots or source_mapping is None or source_mapping["semantic_slot_id"] != link["semantic_slot_id"]:
            _diagnostic(diagnostics, "MACHINE_PRESENTATION_PANEL_LINK_UNRESOLVED", subject, f"$.panel_links[{index}]", "panel link does not resolve one exact block, mapping, and semantic panel slot")


def _validate_machine(
    machine: dict[str, Any],
    reviews: dict[tuple[str, int, str], dict[str, Any]],
    presentations: dict[tuple[str, int, str], dict[str, Any]],
    panels: dict[tuple[str, int, str], dict[str, Any]],
    instruments: dict[tuple[str, int, str], dict[str, Any]],
    graphs: dict[tuple[str, int, str], dict[str, Any]],
    diagnostics: list[core.Diagnostic],
) -> None:
    subject = core.record_subject(machine)
    review = reviews.get(_ref(machine["source_review_reference"], "machine_source_review_id"))
    presentation = presentations.get(_ref(machine["presentation_reference"], "machine_presentation_id"))
    instrument = instruments.get(_ref(machine["instrument_reference"], "instrument_id"))
    if review is None or presentation is None or instrument is None:
        _diagnostic(diagnostics, "MACHINE_CLOSURE_UNRESOLVED", subject, "$", "machine source review, presentation, and accepted instrument must resolve exactly")
        return
    if presentation["source_review_reference"] != machine["source_review_reference"] or presentation["presentation_state"] != "machine-complete":
        _diagnostic(diagnostics, "MACHINE_PRESENTATION_CLOSURE_INVALID", subject, "$.presentation_reference", "a completed machine requires a machine-complete presentation of the same source review")
    graph_reference = instrument["graph_reference"]
    if graph_reference.get("status") != "resolved":
        _diagnostic(diagnostics, "MACHINE_INSTRUMENT_GRAPH_UNRESOLVED", subject, "$.instrument_reference", "the accepted instrument must own one exact resolved graph")
        return
    graph_ref = {key: graph_reference[key] for key in ("graph_id", "revision", "content_hash")}
    graph = graphs.get(_ref(graph_ref, "graph_id"))
    if graph is None:
        _diagnostic(diagnostics, "MACHINE_GRAPH_UNRESOLVED", subject, "$.instrument_reference", "the instrument's exact authoritative graph is absent")
    else:
        presentation_node_refs = [
            reference
            for block in presentation["blocks"]
            for reference in block["graph_node_references"]
        ]
        reference_keys = [
            (item["graph_id"], item["revision"], item["content_hash"], item["node_id"])
            for item in presentation_node_refs
        ]
        if len(reference_keys) != len(set(reference_keys)):
            _diagnostic(
                diagnostics,
                "MACHINE_PRESENTATION_GRAPH_NODE_DUPLICATE",
                subject,
                "$.presentation_reference",
                "a completed presentation cannot trace one graph node more than once",
            )
        graph_nodes = {item["node_id"] for item in graph["nodes"]}
        for index, reference in enumerate(presentation_node_refs):
            exact_graph = {
                key: reference[key]
                for key in ("graph_id", "revision", "content_hash")
            }
            if exact_graph != graph_ref or reference["node_id"] not in graph_nodes:
                _diagnostic(
                    diagnostics,
                    "MACHINE_PRESENTATION_GRAPH_NODE_UNRESOLVED",
                    subject,
                    f"$.presentation_reference.graph_node_references[{index}]",
                    "the presentation trace does not resolve one node in the instrument's exact graph",
                )
    panel = panels.get(_ref(presentation["panel_layout_reference"], "panel_layout_id"))
    if panel is None or panel["device_profile_reference"] != instrument["device_profile_reference"]:
        _diagnostic(diagnostics, "MACHINE_DEVICE_PANEL_MISMATCH", subject, "$.presentation_reference", "machine panel and instrument must name the same exact device profile")
    unresolved = sorted(
        item["dependency_id"] for item in review["dependency_assessments"]
        if item["required"] and item["classification"] in UNRESOLVED_MACHINE_DEPENDENCIES
    )
    if unresolved:
        _diagnostic(diagnostics, "MACHINE_REQUIRED_DEPENDENCY_UNRESOLVED", subject, "$.source_review_reference", "required source dependencies remain fail closed: " + ", ".join(unresolved))


def validate_values(
    groups: dict[str, list[dict[str, Any]]],
    schemas: dict[str, dict[str, Any]],
    domain_records: dict[str, list[dict[str, Any]]],
    repository_root: Path,
) -> dict[str, Any]:
    """Validate an explicit machine layer without source checkout discovery."""

    diagnostics: list[core.Diagnostic] = []
    if not any(groups.values()):
        return {
            "schema_version": "machine-validation-summary-v0",
            "status": "not-applicable",
            "record_counts": {key: 0 for key in SCHEMA_SPECS},
            "inspection_candidate_count": 0,
            "accepted_machine_count": 0,
            "evidence_levels": [{"level": level, "status": "not-run"} for level in range(1, 9)],
            "diagnostics": [],
        }
    valid = _structural(groups, schemas, diagnostics)
    devices = _registry(domain_records["devices"], "device_profile_id")
    instruments = _registry(domain_records["instruments"], "instrument_id")
    graphs = _registry(domain_records["graphs"], "graph_id")
    panels = _registry(valid["panel_layouts"], "panel_layout_id")
    reviews = _registry(valid["machine_source_reviews"], "machine_source_review_id")
    presentations = _registry(valid["machine_presentations"], "machine_presentation_id")
    for panel in valid["panel_layouts"]:
        _validate_panel(panel, devices, repository_root, diagnostics)
    for review in valid["machine_source_reviews"]:
        _validate_review(review, valid["panel_layouts"], domain_records, diagnostics)
    for presentation in valid["machine_presentations"]:
        _validate_presentation(presentation, reviews, panels, diagnostics)
    for machine in valid["machines"]:
        _validate_machine(machine, reviews, presentations, panels, instruments, graphs, diagnostics)

    diagnostics = sorted(set(diagnostics), key=core.diagnostic_sort_key)
    status = "invalid" if diagnostics else "valid"
    return {
        "schema_version": "machine-validation-summary-v0",
        "status": status,
        "record_counts": {key: len(groups[key]) for key in SCHEMA_SPECS},
        "inspection_candidate_count": len(valid["machine_source_reviews"]),
        "accepted_machine_count": len(valid["machines"]),
        "panel_semantic_region_count": sum(len(item["semantic_regions"]) for item in valid["panel_layouts"]),
        "palette_mutation_count": 0,
        "evidence_levels": [
            {"level": level, "status": "passed" if level == 1 and not diagnostics else "failed" if level == 1 else "not-run"}
            for level in range(1, 9)
        ],
        "diagnostics": [item.as_dict() for item in diagnostics],
    }


def inspection_value(
    review: dict[str, Any],
    presentation: dict[str, Any],
    panel: dict[str, Any],
    record_set_reference: dict[str, Any],
    validation_summary: dict[str, Any],
    machine: dict[str, Any] | None = None,
    instrument: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Derive the one client-neutral read-only Viewer value."""

    resource_bytes = sum(
        item["quantity"]
        for item in review["resource_declarations"]
        if item["unit"] == "bytes"
    )
    return {
        "record_set_reference": copy.deepcopy(record_set_reference),
        "entry_kind": "machine" if machine is not None else "source-review",
        "inspection_state": "completed-machine" if machine is not None else "inspection-only",
        "identity": {
            "machine": copy.deepcopy(machine),
            "source_review_reference": {
                "machine_source_review_id": review["machine_source_review_id"],
                "revision": review["revision"],
                "content_hash": review["content_hash"],
            },
            "display_name": machine["display_name"] if machine is not None else review["asserted_identity"]["display_name"],
            "summary": machine["summary"] if machine is not None else review["asserted_identity"]["summary"],
            "source_identity": copy.deepcopy(review["source_identity"]),
            "aliases": copy.deepcopy(review["asserted_identity"]["aliases"]),
        },
        "machine_block_diagram": {
            "presentation_reference": {
                "machine_presentation_id": presentation["machine_presentation_id"],
                "revision": presentation["revision"],
                "content_hash": presentation["content_hash"],
            },
            "presentation_state": presentation["presentation_state"],
            "blocks": copy.deepcopy(presentation["blocks"]),
            "edges": copy.deepcopy(presentation["edges"]),
        },
        "source_evidence": {
            "blocks": copy.deepcopy(review["source_blocks"]),
            "edges": copy.deepcopy(review["source_edges"]),
            "spans": copy.deepcopy(review["evidence_spans"]),
        },
        "panel": {
            "panel_layout_reference": {
                "panel_layout_id": panel["panel_layout_id"],
                "revision": panel["revision"],
                "content_hash": panel["content_hash"],
            },
            "asset": copy.deepcopy(panel["asset"]),
            "coordinate_system": copy.deepcopy(panel["coordinate_system"]),
            "semantic_regions": copy.deepcopy(panel["semantic_regions"]),
            "source_mappings": copy.deepcopy(review["panel_mappings"]),
            "presentation_links": copy.deepcopy(presentation["panel_links"]),
            "visual_verification": copy.deepcopy(panel["visual_verification"]),
        },
        "dependencies": copy.deepcopy(review["dependency_assessments"]),
        "resources": {
            "declarations": copy.deepcopy(review["resource_declarations"]),
            "source_declared_bytes": resource_bytes,
            "measurement_state": "not-run",
        },
        "instrument": copy.deepcopy(instrument),
        "proof_boundary": copy.deepcopy(review["evidence_levels"]),
        "validation": copy.deepcopy(validation_summary),
        "affordances": {
            "inspect": True,
            "build": False,
            "deploy": False,
            "edit": False,
            "play": False,
            "promote": False,
        },
    }
