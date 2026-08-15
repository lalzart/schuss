"""Conforming Task 014 adapter for the exact retained Task 011C handler.

This file is the only product-facing module that knows the local Ksoloti Java,
legacy source capsule, and ARM tool locations.  It deliberately supports one
exact accepted build request and does not generalize the legacy backend.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools/contracts"
for value in (ROOT, TOOLS):
    if str(value) not in sys.path:
        sys.path.insert(0, str(value))

from packages.schuss_core.build_execution import (  # noqa: E402
    HandlerRegistration,
    HandlerRequest,
    descriptor_content_hash,
)
import task011c_backend as backend  # noqa: E402
import validator_core as core  # noqa: E402


REQUEST_REFERENCE = {
    "build_request_id": "schuss-build-request-000002",
    "revision": 2,
    "content_hash": "sha256:dfc54339dc8ce4a243babad40de659437d67aa05c4c2f61be04e39741e4b0351",
}
BACKEND_REFERENCE = {
    "backend_id": "schuss-backend-000001",
    "revision": 3,
    "content_hash": "sha256:5dca1a744c001a62b01c5f9b8235e7a9beba41dc90bcfef84b0362ba38b74b87",
}


def descriptor() -> dict[str, Any]:
    value = {
        "schema_version": "build-handler-descriptor-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "build_handler_id": "schuss-build-handler-000001",
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "backend_reference": copy.deepcopy(BACKEND_REFERENCE),
        "supported_build_request_reference": copy.deepcopy(REQUEST_REFERENCE),
        "execution_policy": "exact-request-only",
        "adapter_kind": "transitional-legacy",
        "mid_handler_cancellation": False,
    }
    value["content_hash"] = descriptor_content_hash(value)
    return value


def _exact_record(values: list[dict[str, Any]], reference: dict[str, Any], id_field: str) -> dict[str, Any]:
    matches = [
        value
        for value in values
        if all(value.get(key) == item for key, item in reference.items())
    ]
    if len(matches) != 1:
        raise ValueError(f"expected one exact {id_field} record, found {len(matches)}")
    return matches[0]


def _resolution(plan: dict[str, Any]) -> dict[str, Any]:
    matches = [
        item["payload"]
        for item in plan["artifacts"]
        if item["descriptor"]["artifact_kind"] == "resolution-plan"
    ]
    if len(matches) != 1 or matches[0].get("status") != "success":
        raise ValueError("exact successful Task 013 resolution plan is absent")
    return matches[0]


def _run(request: HandlerRequest) -> dict[str, Any]:
    records = request.compilation_context.records()
    schemas = request.compilation_context.schemas()
    build_request = _exact_record(records["request"], REQUEST_REFERENCE, "build_request")
    resolution = _resolution(request.plan)
    selected = [
        {
            "node_id": trace["node_id"],
            "binding_reference": copy.deepcopy(trace["selected_binding_reference"]),
        }
        for trace in resolution["traces"]
    ]
    invocation = {
        "schema_version": "schuss-backend-invocation-input-v1",
        "status": "ready-for-backend-invocation",
        "accepted_build_request": copy.deepcopy(build_request),
        "resolution_traces": copy.deepcopy(resolution["traces"]),
        "selected_bindings": sorted(selected, key=lambda item: item["node_id"]),
        "boundary": {
            "completed_stage": "implementation-resolution",
            "next_stage": "backend-lowering",
            "next_stage_status": "not-run",
            "executable_handler_status": "absent",
        },
    }
    expected = {
        item["binding_reference"]["implementation_id"]: item["binding_reference"]
        for item in selected
    }
    config = backend.ExecutionConfig(
        ROOT,
        ROOT / "build/task009-prerequisite-repair-v1/content-addressed",
        Path("/Applications/Ksoloti Local.app/Contents/Resources/jre/bin/java"),
        Path("/Applications/Ksoloti Local.app/Contents/Resources/jre/bin/javac"),
        Path("/Applications/Ksoloti Local.app/Contents/Resources/platform_mac_x64/bin"),
        Path("/Users/lanceship/ksoloti/1.1.0/axoloti-contrib"),
    )
    outcome = backend.run_backend_handler(
        invocation,
        core.load_json(ROOT / "schemas/backend-invocation-input-v1.schema.json"),
        schemas["request"],
        expected,
        build_request,
        config,
        request.output_root,
    )
    artifacts = [
        {
            "artifact_kind": item.kind,
            "media_type": item.media_type,
            "producer_stage": item.producer_stage,
            "byte_sha256": item.byte_sha256,
            "byte_length": item.byte_length,
            "portable_locator": item.portable_locator,
        }
        for item in outcome.artifacts
    ]
    return {
        "status": outcome.status,
        "stage_outcomes": [
            {"stage": stage, "status": status}
            for stage, status in outcome.stage_statuses
        ],
        "artifacts": artifacts,
        "evidence_level": 5 if outcome.status == "success" else 2,
        "command_vectors": list(outcome.command_vectors),
        "bridge_result": copy.deepcopy(outcome.bridge_result),
        "resource_facts": copy.deepcopy(outcome.resource_facts),
    }


def registration() -> HandlerRegistration:
    return HandlerRegistration(descriptor(), _run)
