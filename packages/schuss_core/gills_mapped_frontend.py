"""Task 018 Gills panel mapping layered over the accepted direct DSP frontend."""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Iterable, Mapping

from .gills_direct_frontend import (
    GRAPH_REFERENCE,
    lower_gills_direct_successor,
    semantic_goldens,
)
from .gills_panel_runtime import (
    correct_mapped_cpp_dma_buffers,
    host_vectors,
    mapped_cpp,
)


FRONTEND_ID = "schuss-gills-mapped-frontend-000001"
FRONTEND_VERSION = 1
DMA_SAFE_FRONTEND_VERSION = 2


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _ref(record: Mapping[str, Any], id_field: str) -> dict[str, Any]:
    return {
        id_field: record[id_field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise ValueError(code)


def _mapping_runtime_plan(
    instrument: Mapping[str, Any],
    runtime: Mapping[str, Any],
    coverage: Mapping[str, Any],
    request_reference: Mapping[str, Any],
) -> dict[str, Any]:
    input_mappings = {
        item["mapping_id"]: copy.deepcopy(item)
        for item in instrument["device_input_mappings"]
    }
    graph_mappings = {
        item["mapping_id"]: copy.deepcopy(item)
        for item in instrument["graph_mappings"]
    }
    feedback_mappings = {
        item["mapping_id"]: copy.deepcopy(item)
        for item in instrument["device_feedback_mappings"]
    }
    runtime_bindings = {
        item["slot_id"]: copy.deepcopy(item)
        for collection in (
            "input_bindings",
            "feedback_bindings",
            "display_bindings",
            "physical_io_bindings",
        )
        for item in runtime[collection]
    }
    return {
        "schema_version": "task018-panel-runtime-plan-v1",
        "canonical_profile": "schuss-canonical-json-v1",
        "derived": True,
        "frontend": {"frontend_id": FRONTEND_ID, "version": FRONTEND_VERSION},
        "build_request_reference": copy.deepcopy(dict(request_reference)),
        "instrument_reference": _ref(instrument, "instrument_id"),
        "runtime_realization_reference": _ref(runtime, "runtime_realization_id"),
        "coverage_report_reference": _ref(coverage, "coverage_report_id"),
        "policies": copy.deepcopy(runtime["policies"]),
        "paths": [
            {
                "path_id": "mapped-path-000001",
                "role": "parameter-control",
                "runtime_binding": runtime_bindings["device-input-000001"],
                "device_to_instrument": input_mappings["device-mapping-000001"],
                "instrument_to_graph": graph_mappings["graph-mapping-000001"],
                "generated_symbol": "SchussBlendInputQ27",
            },
            {
                "path_id": "mapped-path-000002",
                "role": "action-trigger",
                "runtime_binding": runtime_bindings["device-input-000011"],
                "device_to_instrument": input_mappings["device-mapping-000002"],
                "generated_symbol": "initialize_gills_panel_state/reset-blend",
            },
            {
                "path_id": "mapped-path-000003",
                "role": "state-feedback",
                "instrument_to_device": feedback_mappings["feedback-mapping-000001"],
                "runtime_binding": runtime_bindings["device-feedback-000001"],
                "generated_symbol": "GPIOG:6",
            },
            {
                "path_id": "mapped-path-000004",
                "role": "display-feedback",
                "instrument_to_device": feedback_mappings["feedback-mapping-000002"],
                "runtime_binding": runtime_bindings["device-display-000001"],
                "generated_symbol": "I2CD1:SH1106:0x3c:text",
            },
        ],
        "coverage_summary": copy.deepcopy(coverage["summary"]),
        "authoritative_records_mutated": False,
    }


def _mapping_source_map(
    instrument: Mapping[str, Any],
    runtime: Mapping[str, Any],
    coverage: Mapping[str, Any],
) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for collection, generated_prefix in (
        ("device_input_mappings", "device-input-mapping"),
        ("graph_mappings", "graph-mapping"),
        ("device_feedback_mappings", "device-feedback-mapping"),
    ):
        for mapping in instrument[collection]:
            entries.append(
                {
                    "derived_subject": generated_prefix + ":" + mapping["mapping_id"],
                    "origin": {
                        "instrument_reference": _ref(instrument, "instrument_id"),
                        "mapping_id": mapping["mapping_id"],
                    },
                }
            )
    for collection in (
        "input_bindings",
        "feedback_bindings",
        "display_bindings",
        "physical_io_bindings",
    ):
        for binding in runtime[collection]:
            entries.append(
                {
                    "derived_subject": "runtime-binding:" + binding["binding_id"],
                    "origin": {
                        "runtime_realization_reference": _ref(
                            runtime, "runtime_realization_id"
                        ),
                        "binding_id": binding["binding_id"],
                        "slot_id": binding["slot_id"],
                        "evidence_source_ids": copy.deepcopy(
                            binding["evidence_source_ids"]
                        ),
                    },
                }
            )
    for item in (
        list(coverage["device_slot_coverage"])
        + list(coverage["instrument_facet_coverage"])
    ):
        subject_id = item.get("slot_id", item.get("facet_id"))
        entries.append(
            {
                "derived_subject": "coverage:" + subject_id,
                "origin": {
                    "coverage_report_reference": _ref(
                        coverage, "coverage_report_id"
                    ),
                    "outcome": item["outcome"],
                    "mapping_refs": copy.deepcopy(item["mapping_refs"]),
                },
            }
        )
    return {
        "schema_version": "task018-mapping-source-map-v1",
        "canonical_profile": "schuss-canonical-json-v1",
        "derived": True,
        "entries": sorted(entries, key=lambda item: item["derived_subject"]),
    }


def lower_gills_mapped(
    plan: Mapping[str, Any],
    graph: Mapping[str, Any],
    contracts: Iterable[Mapping[str, Any]],
    operation_specs: Iterable[Mapping[str, Any]],
    instrument: Mapping[str, Any],
    runtime: Mapping[str, Any],
    coverage: Mapping[str, Any],
    request_reference: Mapping[str, Any],
) -> dict[str, Any]:
    """Lower one exact Task 018 mapped successor without changing DSP semantics."""

    plan_value = copy.deepcopy(dict(plan))
    instrument_value = copy.deepcopy(dict(instrument))
    runtime_value = copy.deepcopy(dict(runtime))
    coverage_value = copy.deepcopy(dict(coverage))
    request_ref = copy.deepcopy(dict(request_reference))
    _require(
        plan_value.get("input_closure", {}).get("build_request_reference")
        == request_ref,
        "GILLS_MAPPED_PLAN_REQUEST_MISMATCH",
    )
    _require(
        instrument_value["graph_reference"]
        == {"status": "resolved", **GRAPH_REFERENCE},
        "GILLS_MAPPED_INSTRUMENT_GRAPH_MISMATCH",
    )
    _require(
        instrument_value["device_profile_reference"]
        == runtime_value["device_profile_reference"],
        "GILLS_MAPPED_RUNTIME_DEVICE_MISMATCH",
    )
    _require(
        coverage_value["instrument_reference"]
        == _ref(instrument_value, "instrument_id")
        and coverage_value["device_profile_reference"]
        == runtime_value["device_profile_reference"],
        "GILLS_MAPPED_COVERAGE_CLOSURE_MISMATCH",
    )
    supported = [
        item
        for item in runtime_value["supported_builds"]
        if item["build_request_reference"] == request_ref
        and item["instrument_reference"] == _ref(instrument_value, "instrument_id")
        and item["handler"]["status"] == "supported"
    ]
    _require(len(supported) == 1, "GILLS_MAPPED_RUNTIME_BUILD_UNRESOLVED")
    _require(
        {item["mapping_id"] for item in instrument_value["device_input_mappings"]}
        == {"device-mapping-000001", "device-mapping-000002"}
        and {item["mapping_id"] for item in instrument_value["graph_mappings"]}
        == {"graph-mapping-000001"}
        and {
            item["mapping_id"]
            for item in instrument_value["device_feedback_mappings"]
        }
        == {"feedback-mapping-000001", "feedback-mapping-000002"},
        "GILLS_MAPPED_MAPPING_SET_UNSUPPORTED",
    )
    _require(
        coverage_value["summary"]["unresolved"] == 0
        and coverage_value["summary"]["absence_is_coverage"] is False,
        "GILLS_MAPPED_COVERAGE_UNRESOLVED",
    )

    direct = lower_gills_direct_successor(
        plan_value, graph, contracts, operation_specs, request_ref
    )
    _require(
        direct["semantic_goldens"] == semantic_goldens(),
        "GILLS_MAPPED_DIRECT_SEMANTICS_CHANGED",
    )
    cpp = mapped_cpp(direct["generated_cpp"]["text"])
    cpp_bytes = cpp.encode("utf-8")
    panel_runtime = _mapping_runtime_plan(
        instrument_value, runtime_value, coverage_value, request_ref
    )
    mapping_source_map = _mapping_source_map(
        instrument_value, runtime_value, coverage_value
    )
    vectors = host_vectors()
    return {
        "schema_version": "gills-mapped-frontend-result-v1",
        "canonical_profile": "schuss-canonical-json-v1",
        "status": "success",
        "frontend": {"frontend_id": FRONTEND_ID, "version": FRONTEND_VERSION},
        "input_plan_sha256": _sha256(_canonical_bytes(plan_value)),
        "module": direct["module"],
        "direct_source_map": direct["source_map"],
        "mapping_source_map": mapping_source_map,
        "semantic_goldens": direct["semantic_goldens"],
        "panel_runtime": panel_runtime,
        "host_vectors": vectors,
        "generated_cpp": {
            "text": cpp,
            "byte_sha256": _sha256(cpp_bytes),
            "byte_length": len(cpp_bytes),
        },
        "diagnostics": [],
        "evidence_levels": [
            {"level": level, "status": "passed" if level <= 4 else "not-run"}
            for level in range(1, 9)
        ],
        "java_used": False,
        "legacy_boundary_patch_used": False,
        "ambient_discovery_used": False,
        "authoritative_records_mutated": False,
    }


def lower_gills_mapped_dma_safe(
    plan: Mapping[str, Any],
    graph: Mapping[str, Any],
    contracts: Iterable[Mapping[str, Any]],
    operation_specs: Iterable[Mapping[str, Any]],
    instrument: Mapping[str, Any],
    runtime: Mapping[str, Any],
    coverage: Mapping[str, Any],
    request_reference: Mapping[str, Any],
) -> dict[str, Any]:
    """Lower the Task 021 successor while preserving Task 018 DSP semantics."""

    result = lower_gills_mapped(
        plan,
        graph,
        contracts,
        operation_specs,
        instrument,
        runtime,
        coverage,
        request_reference,
    )
    cpp = correct_mapped_cpp_dma_buffers(result["generated_cpp"]["text"])
    cpp_bytes = cpp.encode("utf-8")
    frontend = {
        "frontend_id": FRONTEND_ID,
        "version": DMA_SAFE_FRONTEND_VERSION,
    }
    result["schema_version"] = "gills-mapped-frontend-result-v2"
    result["frontend"] = copy.deepcopy(frontend)
    result["panel_runtime"]["schema_version"] = "task021-panel-runtime-plan-v1"
    result["panel_runtime"]["frontend"] = copy.deepcopy(frontend)
    result["generated_cpp"] = {
        "text": cpp,
        "byte_sha256": _sha256(cpp_bytes),
        "byte_length": len(cpp_bytes),
    }
    return result


__all__ = ["lower_gills_mapped", "lower_gills_mapped_dma_safe"]
