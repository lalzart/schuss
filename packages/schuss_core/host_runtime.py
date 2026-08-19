"""Deterministic Task 031 host-package lowering for the exact effects profile.

The authoritative input remains the accepted Schuss project/graph closure.  A
host runtime package is a derived boundary artifact and is never read back as
an authoring graph.
"""

from __future__ import annotations

import copy
import hashlib
from decimal import Decimal
from typing import Any, Mapping

from .compiler_front_half import CompilationContext, plan_build
from .control_plane import OperationContext, core
from .effects_profile_frontend import (
    PARAMETERS,
    ROLE_CONNECTIONS,
    ROLE_CONTRACTS,
    profile_reference,
    semantic_profile_signature,
)


HOST_BUILD_REQUEST_ID = "schuss-build-request-000006"
HOST_TARGET_ID = "schuss-compute-target-000002"
HOST_BACKEND_ID = "schuss-backend-000003"
HOST_RUNTIME_ABI = "schuss-rt-abi-v0"
HOST_ENGINE_PROTOCOL_ABI = "schuss-audio-engine-protocol-v0"
HOST_NUMERIC_PROFILE = "schuss-host-q27-reference-v0"
ROLE_ORDER = ("saw", "pwm", "soft", "smooth", "crossfade", "vca", "output")
FACTORY_IDS = {role: f"schuss.rt.{role}-q27-v0" for role in ROLE_ORDER}
EXPECTED_BINDING_IDS = {
    role: f"schuss-implementation-{162 + index:06d}"
    for index, role in enumerate(ROLE_ORDER)
}
OUTPUT_BUFFERS = {
    "saw": (0,),
    "pwm": (1,),
    "soft": (2,),
    "smooth": (3,),
    "crossfade": (4,),
    "vca": (5,),
    "output": (6, 7),
}
INPUT_BUFFERS = {
    "saw": (),
    "pwm": (),
    "soft": (0,),
    "smooth": (),
    "crossfade": (1, 2),
    "vca": (3, 4),
    "output": (5, 5),
}
STATE_SIZES = {
    "saw": 16,
    "pwm": 16,
    "soft": 0,
    "smooth": 8,
    "crossfade": 0,
    "vca": 8,
    "output": 0,
}


class HostRuntimeError(ValueError):
    """Stable fail-closed host lowering error."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _ref(record: Mapping[str, Any], id_field: str) -> dict[str, Any]:
    return {
        id_field: record[id_field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def _exact_one(
    values: tuple[dict[str, Any], ...] | list[dict[str, Any]],
    id_field: str,
    identifier: str,
    code: str,
) -> dict[str, Any]:
    matches = [value for value in values if value.get(id_field) == identifier]
    if len(matches) != 1:
        raise HostRuntimeError(code, f"expected one exact {identifier}, found {len(matches)}")
    return matches[0]


def _q(value: str, fractional_bits: int) -> int:
    scaled = Decimal(value) * (1 << fractional_bits)
    integral = int(scaled)
    if scaled != integral or integral < -(1 << 31) or integral > (1 << 31) - 1:
        raise HostRuntimeError("HOST_PARAMETER_VALUE_UNSUPPORTED", f"cannot encode {value!r} as Q{fractional_bits}")
    return integral


def _artifact(plan: Mapping[str, Any], kind: str) -> dict[str, Any]:
    matches = [
        value["payload"]
        for value in plan.get("artifacts", [])
        if value.get("descriptor", {}).get("artifact_kind") == kind
    ]
    if len(matches) != 1:
        raise HostRuntimeError("HOST_COMPILER_ARTIFACT_NOT_EXACT", f"expected one exact {kind} artifact")
    return matches[0]


def _parameters(role: str) -> list[dict[str, Any]]:
    values = [
        {"facet_id": item["facet_id"], "value_q": _q(item["value"], 21)}
        for item in PARAMETERS[role]
    ]
    if role == "pwm":
        values.append({"facet_id": "component-port-000002", "value_q": 0})
    elif role == "smooth":
        values.extend(
            [
                {"facet_id": "component-parameter-000001", "value_q": 0},
                {"facet_id": "component-port-000001", "value_q": _q("0.5", 27)},
            ]
        )
    elif role == "crossfade":
        values.append({"facet_id": "component-port-000003", "value_q": _q("0.5", 27)})
    return sorted(values, key=core.canonical_json)


def lower_host_package(
    context: OperationContext,
    *,
    project_reference: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Lower the exact Task 026 profile through the shared compiler front half.

    Returns ``(package, plan)``.  No filesystem, native build, process launch,
    device access, or hardware action occurs.
    """

    if set(project_reference) != {"project_id", "revision", "content_hash"}:
        raise HostRuntimeError("HOST_PROJECT_REFERENCE_INVALID", "project reference must be closed and exact")

    request = _exact_one(context.records["request"], "build_request_id", HOST_BUILD_REQUEST_ID, "HOST_BUILD_REQUEST_NOT_EXACT")
    if request.get("requested_stopping_stage") != "artifact-generation":
        raise HostRuntimeError("HOST_BUILD_REQUEST_STAGE_INVALID", "host request must stop at artifact-generation")
    target = _exact_one(context.records["target"], "compute_target_id", HOST_TARGET_ID, "HOST_TARGET_NOT_EXACT")
    backend = _exact_one(context.records["backend"], "backend_id", HOST_BACKEND_ID, "HOST_BACKEND_NOT_EXACT")

    graph_matches = [
        value
        for value in context.records["graphs"]
        if _ref(value, "graph_id") == request["graph_reference"]
    ]
    instrument_matches = [
        value
        for value in context.records["instruments"]
        if _ref(value, "instrument_id")
        == {key: request["instrument_reference"][key] for key in ("instrument_id", "revision", "content_hash")}
    ]
    if len(graph_matches) != 1 or len(instrument_matches) != 1:
        raise HostRuntimeError("HOST_PROFILE_CLOSURE_NOT_EXACT", "host request graph and instrument must resolve exactly once")
    graph = graph_matches[0]
    instrument = instrument_matches[0]
    match = semantic_profile_signature(graph)
    graph_reference = _ref(graph, "graph_id")
    instrument_reference = _ref(instrument, "instrument_id")
    if instrument.get("graph_reference", {}).get("status") != "resolved" or {
        key: instrument["graph_reference"].get(key)
        for key in ("graph_id", "revision", "content_hash")
    } != graph_reference:
        raise HostRuntimeError("HOST_INSTRUMENT_GRAPH_MISMATCH", "instrument does not select the exact host graph")

    compilation = CompilationContext.from_values(
        build_request_reference=_ref(request, "build_request_id"),
        closure_source={
            "kind": "project",
            "project_reference": copy.deepcopy(dict(project_reference)),
            "base_record_set_reference": copy.deepcopy(context.record_set_reference),
        },
        records=context.records,
        schemas=context.schemas,
    )
    plan = plan_build(compilation)
    if plan.get("status") != "success":
        codes = sorted({item.get("code", "HOST_COMPILER_FAILED") for item in plan.get("diagnostics", [])})
        raise HostRuntimeError("HOST_COMPILER_PLAN_FAILED", ", ".join(codes) or "compiler plan did not succeed")
    resolution = _artifact(plan, "resolution-plan")
    traces = {item["node_id"]: item for item in resolution["traces"]}

    nodes: list[dict[str, Any]] = []
    state_offset = 0
    for role in ROLE_ORDER:
        node_id = match.role_nodes[role]
        trace = traces.get(node_id)
        if trace is None or trace.get("status") != "selected":
            raise HostRuntimeError("HOST_BINDING_NOT_EXACT", f"role {role} has no selected compiler binding")
        binding_reference = trace["selected_binding_reference"]
        if binding_reference["implementation_id"] != EXPECTED_BINDING_IDS[role]:
            raise HostRuntimeError("HOST_BINDING_ID_UNSUPPORTED", f"role {role} selected {binding_reference['implementation_id']}")
        size = STATE_SIZES[role]
        nodes.append(
            {
                "node_id": node_id,
                "role": role,
                "contract_reference": copy.deepcopy(ROLE_CONTRACTS[role]),
                "binding_reference": copy.deepcopy(binding_reference),
                "factory_id": FACTORY_IDS[role],
                "input_buffers": list(INPUT_BUFFERS[role]),
                "output_buffers": list(OUTPUT_BUFFERS[role]),
                "parameters": _parameters(role),
                "state_offset_bytes": state_offset,
                "state_size_bytes": size,
            }
        )
        state_offset += size

    source_buffers = {role: OUTPUT_BUFFERS[role][0] for role in ROLE_ORDER if role != "output"}
    graph_connections = {
        (
            item["source"]["node_id"],
            item["source"]["facet_id"],
            item["destination"]["node_id"],
            item["destination"]["facet_id"],
        ): item
        for item in graph["connections"]
    }
    connections: list[dict[str, Any]] = []
    for source_role, source_facet, destination_role, destination_facet in ROLE_CONNECTIONS:
        key = (match.role_nodes[source_role], source_facet, match.role_nodes[destination_role], destination_facet)
        item = graph_connections.get(key)
        if item is None:
            raise HostRuntimeError("HOST_CONNECTION_NOT_EXACT", f"missing exact {source_role} to {destination_role} connection")
        connections.append(
            {
                "connection_id": item["connection_id"],
                "source": copy.deepcopy(item["source"]),
                "destination": copy.deepcopy(item["destination"]),
                "buffer_index": source_buffers[source_role],
            }
        )

    package: dict[str, Any] = {
        "schema_version": "host-runtime-package-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "derived": True,
        "authoritative": False,
        "content_hash": "sha256:" + "0" * 64,
        "runtime_abi": HOST_RUNTIME_ABI,
        "engine_protocol_abi": HOST_ENGINE_PROTOCOL_ABI,
        "numeric_profile": HOST_NUMERIC_PROFILE,
        "project_reference": copy.deepcopy(dict(project_reference)),
        "graph_reference": graph_reference,
        "instrument_reference": instrument_reference,
        "host_build_request_reference": _ref(request, "build_request_id"),
        "compute_target_reference": _ref(target, "compute_target_id"),
        "backend_reference": _ref(backend, "backend_id"),
        "semantic_profile_reference": profile_reference(),
        "source_plan_sha256": hashlib.sha256(core.canonical_json(plan).encode("utf-8")).hexdigest(),
        "sample_rate_hz": 48000,
        "max_block_frames": 512,
        "control_period_frames": 16,
        "block_policy": "bounded-variable-with-final-partial",
        "input_channels": 0,
        "output_channels": 2,
        "latency_frames": 0,
        "tail_frames": 0,
        "seed": 0,
        "memory_plan": {
            "state_bytes": state_offset,
            "buffer_count": 8,
            "buffer_frames": 512,
            "buffer_bytes": 8 * 512 * 4,
            "event_capacity": 1024,
        },
        "nodes": nodes,
        "connections": sorted(connections, key=core.canonical_json),
        "schedule": [match.role_nodes[role] for role in ROLE_ORDER],
        "outputs": {"left_buffer": 6, "right_buffer": 7},
        "event_contract": {
            "capacity": 1024,
            "ordering": "frame-offset-then-sequence",
            "accepted_kinds": ["midi-message", "parameter-q27"],
            "overflow_policy": "drop-newest-and-count",
        },
        "exclusions": sorted(
            {
                "dynamic graph mutation",
                "implicit device access",
                "JUCE dependency in schuss_rt",
                "Ksoloti equivalence claim",
                "reverb",
                "runtime parsing on the audio callback",
            }
        ),
    }
    schema = context.schemas.get("host_runtime_package")
    if schema is None:
        raise HostRuntimeError("HOST_PACKAGE_SCHEMA_UNAVAILABLE", "host runtime package schema is absent")
    package["content_hash"] = core.record_content_hash(package, schema)
    errors = core.schema_errors(package, schema, schema)
    if errors:
        raise HostRuntimeError("HOST_PACKAGE_SCHEMA_INVALID", "; ".join(errors))
    return package, plan


__all__ = [
    "HOST_BACKEND_ID",
    "HOST_BUILD_REQUEST_ID",
    "HOST_NUMERIC_PROFILE",
    "HOST_RUNTIME_ABI",
    "HOST_TARGET_ID",
    "HostRuntimeError",
    "lower_host_package",
]
