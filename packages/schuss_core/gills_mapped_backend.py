"""Exact Task 018 mapped-Gills handler and authenticated ARM build boundary."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .build_execution import (
    HandlerRegistration,
    HandlerRequest,
    descriptor_content_hash,
    handler_reference,
)
from .gills_direct_backend import (
    BACKEND_REFERENCE,
    DirectBackendError,
    DirectExecutionConfig,
    _artifact,
    _canonical_bytes,
    _compile_arm,
    _exact_record,
    verify_execution_config,
)
from .gills_direct_frontend import GRAPH_REFERENCE
from .gills_mapped_frontend import lower_gills_mapped


REQUEST_REFERENCE = {
    "build_request_id": "schuss-build-request-000002",
    "revision": 4,
    "content_hash": "sha256:a2ef80ef88acb33e5739a2e0f35c9a6cad033c30206cbdd7242d4f10c12e9aed",
}
INSTRUMENT_REFERENCE = {
    "instrument_id": "schuss-instrument-000002",
    "revision": 2,
    "content_hash": "sha256:03bc195c3b1848ed62ca4708a55f5d22de2f54ef64f5833e95aa7133f8cf85e8",
}
RUNTIME_REFERENCE = {
    "runtime_realization_id": "schuss-runtime-realization-000001",
    "revision": 1,
    "content_hash": "sha256:f038b8a673a648cd3512ff30277c986bc486500090eddcde58648430f80cd012",
}
COVERAGE_REFERENCE = {
    "coverage_report_id": "schuss-coverage-report-000001",
    "revision": 1,
    "content_hash": "sha256:4622ccd6ed35431851c658abbe4370d535b8c40f1dad792f459f6405a8039d7e",
}
PANEL_REFERENCE = {
    "panel_evidence_packet_id": "schuss-panel-evidence-000001",
    "revision": 1,
    "content_hash": "sha256:e14e1c4fb6161e8e895330328eeb4220ed2a7fbffb7b5dc6a1651e2ca2024d8e",
}
DEVICE_REFERENCE = {
    "device_profile_id": "schuss-device-profile-000001",
    "revision": 2,
    "content_hash": "sha256:26883806207677ec61e2a409c43a0e90f55800dc8a28e52bc75557efeee60338",
}


def descriptor() -> dict[str, Any]:
    value = {
        "schema_version": "build-handler-descriptor-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "build_handler_id": "schuss-build-handler-000003",
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "backend_reference": copy.deepcopy(BACKEND_REFERENCE),
        "supported_build_request_reference": copy.deepcopy(REQUEST_REFERENCE),
        "execution_policy": "exact-request-only",
        "adapter_kind": "direct",
        "mid_handler_cancellation": False,
    }
    value["content_hash"] = descriptor_content_hash(value)
    return value


def _fail(code: str, subject: str, message: str) -> None:
    raise DirectBackendError(code, "backend-lowering", subject, message)


def _run_handler_for_closure(
    request: HandlerRequest,
    config: DirectExecutionConfig | None = None,
    *,
    request_reference: dict[str, Any],
    instrument_reference: dict[str, Any],
    runtime_reference: dict[str, Any],
    coverage_reference: dict[str, Any],
    descriptor_value: dict[str, Any],
    lowerer: Any,
    task_id: str,
) -> dict[str, Any]:
    config = config or DirectExecutionConfig.local_default()
    direct_preflight = verify_execution_config(config)
    records = request.compilation_context.records()
    request_record = _exact_record(
        records["request"], request_reference, "build_request_id"
    )
    if request_record["backend_reference"] != BACKEND_REFERENCE:
        _fail(
            "GILLS_MAPPED_BACKEND_REFERENCE_MISMATCH",
            BACKEND_REFERENCE["backend_id"],
            "mapped request does not name the accepted exact direct backend",
        )
    graph = _exact_record(records["graphs"], GRAPH_REFERENCE, "graph_id")
    instrument = _exact_record(
        records["instruments"], instrument_reference, "instrument_id"
    )
    runtime = _exact_record(
        records["runtime_realizations"],
        runtime_reference,
        "runtime_realization_id",
    )
    coverage = _exact_record(
        records["mapping_coverage"], coverage_reference, "coverage_report_id"
    )
    panel = _exact_record(
        records["panel_evidence"], PANEL_REFERENCE, "panel_evidence_packet_id"
    )
    device = _exact_record(
        records["devices"], DEVICE_REFERENCE, "device_profile_id"
    )
    if request_record["instrument_reference"] != {
        "status": "included",
        **instrument_reference,
    }:
        _fail(
            "GILLS_MAPPED_INSTRUMENT_REFERENCE_MISMATCH",
            instrument_reference["instrument_id"],
            "mapped request does not name the exact mapped instrument",
        )
    if (
        instrument["device_profile_reference"] != DEVICE_REFERENCE
        or runtime["device_profile_reference"] != DEVICE_REFERENCE
        or coverage["device_profile_reference"] != DEVICE_REFERENCE
        or device["device_profile_id"] != DEVICE_REFERENCE["device_profile_id"]
    ):
        _fail(
            "GILLS_MAPPED_DEVICE_CLOSURE_MISMATCH",
            DEVICE_REFERENCE["device_profile_id"],
            "mapped instrument, evidence, coverage, and runtime do not share one exact device reference",
        )
    supported = [
        value
        for value in runtime["supported_builds"]
        if value["build_request_reference"] == request_reference
        and value["instrument_reference"] == instrument_reference
        and value["handler"]
        == {"status": "supported", **handler_reference(descriptor_value)}
    ]
    if len(supported) != 1:
        _fail(
            "GILLS_MAPPED_HANDLER_CLOSURE_UNRESOLVED",
            descriptor_value["build_handler_id"],
            "runtime realization does not resolve the exact mapped handler once",
        )
    if (
        request.plan.get("input_closure", {}).get("build_request_reference")
        != request_reference
    ):
        _fail(
            "GILLS_MAPPED_PLAN_REQUEST_MISMATCH",
            request_reference["build_request_id"],
            "handler received a plan for a different exact request",
        )

    result = lowerer(
        request.plan,
        graph,
        records["contracts"],
        records.get("direct_operation_specs", []),
        instrument,
        runtime,
        coverage,
        request_reference,
    )
    output_root = Path(request.output_root)
    if output_root.exists():
        _fail(
            "GILLS_MAPPED_OUTPUT_ROOT_NOT_FRESH",
            "output-root",
            "mapped handler output root must not exist",
        )
    output_root.mkdir(parents=True)
    resolution = next(
        item["payload"]
        for item in request.plan["artifacts"]
        if item["descriptor"]["artifact_kind"] == "resolution-plan"
    )
    payloads = [
        (
            "resolution-plan",
            resolution,
            "application/vnd.schuss.resolution-plan+json",
            "implementation-resolution",
        ),
        (
            "normalized-dsp",
            result["module"],
            "application/vnd.schuss.normalized-dsp+json",
            "backend-lowering",
        ),
        (
            "direct-source-map",
            result["direct_source_map"],
            "application/vnd.schuss.source-map+json",
            "artifact-generation",
        ),
        (
            "mapping-source-map",
            result["mapping_source_map"],
            "application/vnd.schuss.gills-mapping-source-map+json",
            "artifact-generation",
        ),
        (
            "semantic-goldens",
            result["semantic_goldens"],
            "application/vnd.schuss.semantic-goldens+json",
            "artifact-generation",
        ),
        (
            "panel-runtime-plan",
            result["panel_runtime"],
            "application/vnd.schuss.gills-panel-runtime+json",
            "backend-lowering",
        ),
        (
            "panel-host-vectors",
            result["host_vectors"],
            "application/vnd.schuss.gills-host-vectors+json",
            "artifact-generation",
        ),
        (
            "mapping-coverage",
            coverage,
            "application/vnd.schuss.gills-mapping-coverage+json",
            "backend-lowering",
        ),
        (
            "runtime-realization",
            runtime,
            "application/vnd.schuss.gills-runtime-realization+json",
            "backend-lowering",
        ),
    ]
    artifacts = [
        _artifact(kind, _canonical_bytes(value), media, stage, output_root)
        for kind, value, media, stage in payloads
    ]
    cpp_bytes = result["generated_cpp"]["text"].encode("utf-8")
    artifacts.append(
        _artifact(
            "generated-cpp",
            cpp_bytes,
            "text/x-c++src",
            "artifact-generation",
            output_root,
        )
    )
    arm_artifacts, commands, resource = _compile_arm(
        cpp_bytes, output_root, config
    )
    artifacts.extend(arm_artifacts)
    resource = {
        **resource,
        "schema_version": f"{task_id}-static-resource-facts-v1",
        "runtime_realization_reference": copy.deepcopy(runtime_reference),
        "device_profile_reference": copy.deepcopy(DEVICE_REFERENCE),
        "panel_evidence_reference": copy.deepcopy(PANEL_REFERENCE),
    }
    artifacts.append(
        _artifact(
            "resource-facts",
            _canonical_bytes(resource),
            "application/vnd.schuss.resource-facts+json",
            "target-compile-link",
            output_root,
        )
    )
    artifacts.append(
        _artifact(
            "command-vector",
            _canonical_bytes(commands),
            "application/vnd.schuss.command-vector+json",
            "target-compile-link",
            output_root,
        )
    )
    preflight = {
        "schema_version": f"{task_id}-mapped-preflight-v1",
        "status": "passed",
        "direct_preflight": direct_preflight,
        "device_profile_reference": copy.deepcopy(DEVICE_REFERENCE),
        "panel_evidence_reference": copy.deepcopy(PANEL_REFERENCE),
        "runtime_realization_reference": copy.deepcopy(runtime_reference),
        "source_pins": [
            {
                key: source[key]
                for key in (
                    "source_id",
                    "repository_url",
                    "commit",
                    "path",
                    "byte_sha256",
                )
            }
            for source in panel["sources"]
        ],
        "java_used": False,
        "ambient_discovery_used": False,
        "device_actions_performed": False,
    }
    artifacts.append(
        _artifact(
            "authenticated-preflight",
            _canonical_bytes(preflight),
            "application/vnd.schuss.authenticated-preflight+json",
            "backend-lowering",
            output_root,
        )
    )
    return {
        "status": "success",
        "stage_outcomes": [
            {"stage": "backend-lowering", "status": "success"},
            {"stage": "artifact-generation", "status": "success"},
            {"stage": "target-compile-link", "status": "success"},
        ],
        "artifacts": artifacts,
        "evidence_level": 5,
        "command_vectors": commands,
        "resource_facts": resource,
        "preflight": preflight,
        "java_used": False,
        "legacy_boundary_patch_used": False,
        "ambient_discovery_used": False,
        "device_actions_performed": False,
    }


def run_handler(
    request: HandlerRequest,
    config: DirectExecutionConfig | None = None,
) -> dict[str, Any]:
    return _run_handler_for_closure(
        request,
        config,
        request_reference=REQUEST_REFERENCE,
        instrument_reference=INSTRUMENT_REFERENCE,
        runtime_reference=RUNTIME_REFERENCE,
        coverage_reference=COVERAGE_REFERENCE,
        descriptor_value=descriptor(),
        lowerer=lower_gills_mapped,
        task_id="task018",
    )


def registration(
    config: DirectExecutionConfig | None = None,
) -> HandlerRegistration:
    return HandlerRegistration(
        descriptor(), lambda request: run_handler(request, config)
    )


__all__ = ["descriptor", "registration", "run_handler"]
