"""Bounded Task 026A handler for the reverb-free semantic profile."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Mapping

from .build_execution import HandlerRegistration, HandlerRequest, descriptor_content_hash
from .effects_profile_frontend import lower_effects_profile, profile_reference
from .gills_direct_backend import (
    DirectBackendError,
    DirectExecutionConfig,
    _artifact,
    _canonical_bytes,
    _compile_arm,
    _exact_record,
    _require_hash,
    verify_execution_config,
)


BACKEND_REFERENCE = {
    "backend_id": "schuss-backend-000002",
    "revision": 4,
    "content_hash": "sha256:e30889d5a33fca838086a0f3f8aacdcd065826d64fea396f74bda8aa164ee9db",
}

EFFECT_SOURCE_HASHES = {
    "objects/osc/saw.axo": "8f225df94b7528c3e5b9a6b90e471f5e195f4e6e15afb6468871294ab80388b0",
    "objects/osc/pwm.axo": "92162c00b235967c46c43928786e004a9e1fa3d6429523208fdd37d8b591e3b0",
    "objects/math/smooth.axo": "f4c2bfbfc6f9748393bfe62af39e095ca184f9a5cc0ada21414b22a396e73fb0",
    "objects/dist/soft.axo": "c6d4ec99987b8d324a4fc8628b056ff3b6f45eb7d2f1785dec5be7b1414b00f1",
    "objects/gain/vca.axo": "0fc7ff51ec5ca878375540cb7764651884a2286ff7699ed05c6a103b565cb3b7",
}


def descriptor() -> dict[str, Any]:
    value = {
        "schema_version": "build-handler-descriptor-v1",
        "canonical_profile": "schuss-canonical-json-v1",
        "build_handler_id": "schuss-build-handler-000004",
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "backend_reference": copy.deepcopy(BACKEND_REFERENCE),
        "supported_semantic_profile": profile_reference(),
        "execution_policy": "exact-semantic-profile",
        "adapter_kind": "direct",
        "mid_handler_cancellation": False,
    }
    value["content_hash"] = descriptor_content_hash(value)
    return value


def verify_effects_execution_config(config: DirectExecutionConfig) -> dict[str, Any]:
    preflight = verify_execution_config(config)
    for relative, digest in EFFECT_SOURCE_HASHES.items():
        _require_hash(config.factory_root / relative, digest, "factory:" + relative)
    result = copy.deepcopy(preflight)
    result["schema_version"] = "task026a-direct-preflight-v1"
    result["effect_source_hashes"] = copy.deepcopy(EFFECT_SOURCE_HASHES)
    result["reverb_source_consumed"] = False
    return result


def run_handler(request: HandlerRequest, config: DirectExecutionConfig | None = None) -> dict[str, Any]:
    config = config or DirectExecutionConfig.local_default()
    preflight = verify_effects_execution_config(config)
    records = request.compilation_context.records()
    request_reference = request.plan.get("input_closure", {}).get("build_request_reference", {})
    request_record = _exact_record(records["request"], request_reference, "build_request_id")
    if request_record.get("backend_reference") != BACKEND_REFERENCE:
        raise DirectBackendError("EFFECTS_PROFILE_BACKEND_REFERENCE_MISMATCH", "backend-lowering", BACKEND_REFERENCE["backend_id"], "build request does not name the exact profile backend")
    graph = _exact_record(records["graphs"], request_record["graph_reference"], "graph_id")
    instrument_reference = request_record.get("instrument_reference", {})
    if instrument_reference.get("status") != "included":
        raise DirectBackendError("EFFECTS_PROFILE_INSTRUMENT_REQUIRED", "backend-lowering", request_record["build_request_id"], "semantic profile requires one included instrument")
    instrument = _exact_record(records["instruments"], {key: instrument_reference[key] for key in ("instrument_id", "revision", "content_hash")}, "instrument_id")
    result = lower_effects_profile(request.plan, graph, instrument, request_record, records["contracts"], records["direct_operation_specs"])
    output_root = request.output_root
    if output_root.exists():
        raise DirectBackendError("EFFECTS_PROFILE_OUTPUT_ROOT_NOT_FRESH", "backend-lowering", "output-root", "handler output root must not exist")
    output_root.mkdir(parents=True)
    resolution = next(item["payload"] for item in request.plan["artifacts"] if item["descriptor"]["artifact_kind"] == "resolution-plan")
    payloads = [
        ("resolution-plan", _canonical_bytes(resolution), "application/vnd.schuss.resolution-plan+json", "implementation-resolution"),
        ("normalized-dsp", _canonical_bytes(result["module"]), "application/vnd.schuss.normalized-dsp+json", "backend-lowering"),
        ("source-map", _canonical_bytes(result["source_map"]), "application/vnd.schuss.source-map+json", "artifact-generation"),
        ("generated-cpp", result["generated_cpp"]["text"].encode("utf-8"), "text/x-c++src", "artifact-generation"),
        ("semantic-goldens", _canonical_bytes(result["semantic_goldens"]), "application/vnd.schuss.semantic-goldens+json", "artifact-generation"),
    ]
    artifacts = [_artifact(kind, data, media, stage, output_root) for kind, data, media, stage in payloads]
    arm_artifacts, commands, resource = _compile_arm(result["generated_cpp"]["text"].encode("utf-8"), output_root, config)
    artifacts.extend(arm_artifacts)
    # The authenticated Makefile emits dependency, precompiled-header, and
    # unstripped intermediates containing the fresh absolute build root. They
    # are not declared artifacts and must not cross the publication boundary.
    for relative in (
        "build/gills-direct.d",
        "build/gills-direct.elf",
        "build/gills-direct.o",
        "build/xpatch.h.d",
        "build/xpatch.h.gch",
    ):
        path = output_root / relative
        if path.is_file():
            path.unlink()
    artifacts.extend([
        _artifact("resource-facts", _canonical_bytes(resource), "application/vnd.schuss.resource-facts+json", "target-compile-link", output_root),
        _artifact("command-vector", _canonical_bytes(commands), "application/vnd.schuss.command-vector+json", "target-compile-link", output_root),
        _artifact("authenticated-preflight", _canonical_bytes(preflight), "application/vnd.schuss.authenticated-preflight+json", "backend-lowering", output_root),
    ])
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
    }


def registration(config: DirectExecutionConfig | None = None) -> HandlerRegistration:
    return HandlerRegistration(descriptor(), lambda request: run_handler(request, config))


__all__ = ["descriptor", "registration", "run_handler", "verify_effects_execution_config"]
