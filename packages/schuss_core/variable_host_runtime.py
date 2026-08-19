"""Bounded Task 032 variable-graph host lowering.

The project graph remains authoritative.  This module validates one exact
project-owned graph/instrument/request closure, resolves it through the shared
compiler front half, and emits a deterministic non-authoritative v1 package.
"""

from __future__ import annotations

import copy
import hashlib
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Iterable, Mapping

from .compiler_front_half import CompilationContext, plan_build
from .control_plane import OperationContext, core
from .host_runtime import HostRuntimeError


HOST_TARGET_ID = "schuss-compute-target-000002"
HOST_BACKEND_ID = "schuss-backend-000003"
HOST_RUNTIME_ABI = "schuss-rt-abi-v1"
HOST_ENGINE_PROTOCOL_ABI = "schuss-audio-engine-protocol-v1"
HOST_PACKAGE_SCHEMA = "host-runtime-package-v1"
HOST_OBSERVATION_SCHEMA = "host-runtime-observation-v1"
HOST_PROTOCOL_SCHEMA = "host-engine-protocol-v1"
HOST_NUMERIC_PROFILE = "schuss-host-q27-reference-v0"
FACTORY_REGISTRY_VERSION = "schuss-rt-factory-registry-v1"

MAX_NODES = 64
MAX_CONNECTIONS = 192
MAX_BUFFERS = 128
MAX_STATE_BYTES = 65536
MAX_PARAMETERS = 256
MAX_EVENTS = 1024
MAX_SCHEDULE = 64


@dataclass(frozen=True)
class FactorySpec:
    role: str
    contract_id: str
    binding_id: str
    factory_id: str
    input_facets: tuple[str, ...]
    output_facets: tuple[str, ...]
    parameter_facets: tuple[str, ...]
    state_size: int
    state_alignment: int


FACTORY_SPECS = (
    FactorySpec(
        "saw",
        "schuss-component-contract-000012",
        "schuss-implementation-000162",
        "schuss.rt.saw-q27-v0",
        ("component-port-000001",),
        ("component-port-000002",),
        ("component-parameter-000001",),
        16,
        16,
    ),
    FactorySpec(
        "pwm",
        "schuss-component-contract-000013",
        "schuss-implementation-000163",
        "schuss.rt.pwm-q27-v0",
        ("component-port-000001", "component-port-000002"),
        ("component-port-000003",),
        ("component-parameter-000001",),
        16,
        16,
    ),
    FactorySpec(
        "soft",
        "schuss-component-contract-000016",
        "schuss-implementation-000164",
        "schuss.rt.soft-q27-v0",
        ("component-port-000001",),
        ("component-port-000002",),
        (),
        0,
        1,
    ),
    FactorySpec(
        "smooth",
        "schuss-component-contract-000015",
        "schuss-implementation-000165",
        "schuss.rt.smooth-q27-v0",
        ("component-port-000001",),
        ("component-port-000002",),
        ("component-parameter-000001",),
        8,
        8,
    ),
    FactorySpec(
        "crossfade",
        "schuss-component-contract-000003",
        "schuss-implementation-000166",
        "schuss.rt.crossfade-q27-v0",
        (
            "component-port-000001",
            "component-port-000002",
            "component-port-000003",
        ),
        ("component-port-000004",),
        (),
        0,
        1,
    ),
    FactorySpec(
        "vca",
        "schuss-component-contract-000020",
        "schuss-implementation-000167",
        "schuss.rt.vca-q27-v0",
        ("component-port-000001", "component-port-000002"),
        ("component-port-000003",),
        (),
        8,
        8,
    ),
    FactorySpec(
        "output",
        "schuss-component-contract-000009",
        "schuss-implementation-000168",
        "schuss.rt.output-q27-v0",
        ("component-port-000001", "component-port-000002"),
        (),
        (),
        0,
        1,
    ),
)

_SPEC_BY_CONTRACT = {spec.contract_id: spec for spec in FACTORY_SPECS}


def _fail(code: str, message: str) -> None:
    raise HostRuntimeError(code, message)


def _ref(record: Mapping[str, Any], id_field: str) -> dict[str, Any]:
    return {
        id_field: record[id_field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def _exact_reference(
    values: Iterable[dict[str, Any]],
    reference: Mapping[str, Any],
    id_field: str,
    code: str,
) -> dict[str, Any]:
    matches = [value for value in values if _ref(value, id_field) == dict(reference)]
    if len(matches) != 1:
        _fail(code, f"expected one exact {dict(reference)}, found {len(matches)}")
    return matches[0]


def _q(value: str, fractional_bits: int) -> int:
    scaled = Decimal(value) * (1 << fractional_bits)
    integral = int(scaled)
    if scaled != integral or not -(1 << 31) <= integral <= (1 << 31) - 1:
        _fail(
            "HOST_V1_VALUE_UNREPRESENTABLE",
            f"cannot encode {value!r} with {fractional_bits} fractional bits",
        )
    return integral


def _artifact(plan: Mapping[str, Any], kind: str) -> dict[str, Any]:
    matches = [
        item["payload"]
        for item in plan.get("artifacts", [])
        if item.get("descriptor", {}).get("artifact_kind") == kind
    ]
    if len(matches) != 1:
        _fail("HOST_V1_COMPILER_ARTIFACT_NOT_EXACT", f"expected one {kind} artifact")
    return matches[0]


def _port_signature(port: Mapping[str, Any]) -> tuple[Any, ...]:
    port_type = port["port_type"]
    return (
        port_type["domain"],
        port_type["rate"],
        core.canonical_json(port_type["channel_shape"]),
        core.canonical_json(port_type["representation"]),
        port_type["unit"],
    )


def _validate_project_ownership(
    project: Mapping[str, Any],
    context: OperationContext,
    request_reference: Mapping[str, Any],
) -> None:
    required_project_keys = {"project_id", "revision", "content_hash"}
    if not required_project_keys <= set(project):
        _fail("HOST_V1_PROJECT_REFERENCE_INVALID", "project manifest lacks exact identity")
    if project.get("schema_version") != "project-v1":
        _fail("HOST_V1_PROJECT_SCHEMA_UNSUPPORTED", "Task 032 requires project-v1")
    if project.get("base_record_set", {}).get("reference") != context.record_set_reference:
        _fail(
            "HOST_V1_PROJECT_RECORD_SET_MISMATCH",
            "project does not select the exact Task 032 record set",
        )
    selected = (
        ("dsp-graph", project.get("primary_graph_reference")),
        (
            "instrument",
            project.get("instrument_references", [None])[0]
            if len(project.get("instrument_references", [])) == 1
            else None,
        ),
        (
            "build-request",
            project.get("build_request_references", [None])[0]
            if len(project.get("build_request_references", [])) == 1
            else None,
        ),
    )
    if selected[2][1] != dict(request_reference):
        _fail(
            "HOST_V1_BUILD_REQUEST_NOT_SELECTED",
            "explicit host request is not the project's exact selected request",
        )
    members = project.get("owned_members", [])
    for kind, reference in selected:
        if not isinstance(reference, dict):
            _fail("HOST_V1_PROJECT_PROFILE_INVALID", "project profile selection is not exact")
        stable_id = next((key for key in reference if key.endswith("_id")), None)
        matches = [
            member
            for member in members
            if member.get("record_kind") == kind
            and member.get("stable_id") == reference.get(stable_id)
            and member.get("revision") == reference.get("revision")
            and member.get("content_hash") == reference.get("content_hash")
        ]
        if len(matches) != 1:
            _fail(
                "HOST_V1_PROJECT_PROFILE_NOT_OWNED",
                f"selected {kind} is not one exact project-owned member",
            )


def _contracts_for_nodes(
    context: OperationContext, graph: Mapping[str, Any]
) -> tuple[
    dict[str, dict[str, Any]],
    dict[str, FactorySpec],
    dict[tuple[str, str], dict[str, Any]],
]:
    node_by_id: dict[str, dict[str, Any]] = {}
    spec_by_node: dict[str, FactorySpec] = {}
    port_by_endpoint: dict[tuple[str, str], dict[str, Any]] = {}
    for node in graph["nodes"]:
        node_id = node["node_id"]
        if node_id in node_by_id:
            _fail("HOST_V1_NODE_ID_DUPLICATE", f"duplicate node {node_id}")
        contract = _exact_reference(
            context.records["contracts"],
            node["contract_reference"],
            "component_contract_id",
            "HOST_V1_CONTRACT_NOT_EXACT",
        )
        spec = _SPEC_BY_CONTRACT.get(contract["component_contract_id"])
        if spec is None:
            _fail(
                "HOST_V1_COMPONENT_UNSUPPORTED",
                f"{contract['component_contract_id']} has no Task 032 factory",
            )
        inputs = tuple(
            port["facet_id"] for port in contract["ports"] if port["direction"] == "inlet"
        )
        outputs = tuple(
            port["facet_id"] for port in contract["ports"] if port["direction"] == "outlet"
        )
        parameters = tuple(item["facet_id"] for item in contract["parameters"])
        if (inputs, outputs, parameters) != (
            spec.input_facets,
            spec.output_facets,
            spec.parameter_facets,
        ):
            _fail(
                "HOST_V1_FACTORY_CONTRACT_DRIFT",
                f"factory descriptor no longer matches {spec.contract_id}",
            )
        node_by_id[node_id] = node
        spec_by_node[node_id] = spec
        for port in contract["ports"]:
            port_by_endpoint[(node_id, port["facet_id"])] = port
    if not 2 <= len(node_by_id) <= MAX_NODES:
        _fail("HOST_V1_NODE_LIMIT", f"node count {len(node_by_id)} is outside 2..{MAX_NODES}")
    return node_by_id, spec_by_node, port_by_endpoint


def _parameter_driver_values(
    graph: Mapping[str, Any],
    port_by_endpoint: Mapping[tuple[str, str], dict[str, Any]],
) -> dict[tuple[str, str], int]:
    public = {item["facet_id"]: item for item in graph["public_parameters"]}
    drivers: dict[tuple[str, str], int] = {}
    for binding in graph["parameter_bindings"]:
        if (
            binding.get("binding_kind") != "parameter-to-port"
            or binding.get("driver_policy") != "exclusive"
            or binding.get("update_boundary") != "control-cycle"
            or binding.get("transform", {}).get("curve") != "linear"
            or binding.get("transform", {}).get("polarity") != "direct"
            or binding.get("transform", {}).get("points")
            != [
                {"destination": "0", "source": "0"},
                {"destination": "1", "source": "1"},
            ]
        ):
            _fail(
                "HOST_V1_PARAMETER_BINDING_UNSUPPORTED",
                "only exact direct 0..1 parameter-to-port bindings are supported",
            )
        destination = binding["destination"]
        endpoint = (destination["node_id"], destination["facet_id"])
        port = port_by_endpoint.get(endpoint)
        source = public.get(binding["source_graph_parameter_id"])
        if port is None or port["direction"] != "inlet" or source is None:
            _fail(
                "HOST_V1_PARAMETER_BINDING_INVALID",
                "parameter binding endpoint or source is unresolved",
            )
        if endpoint in drivers:
            _fail("HOST_V1_INPUT_MULTIPLE_DRIVERS", f"multiple drivers for {endpoint}")
        representation = port["port_type"]["representation"]
        drivers[endpoint] = _q(source["default"], representation["fractional_bits"])
    return drivers


def _validate_connections_and_schedule(
    graph: Mapping[str, Any],
    node_by_id: Mapping[str, dict[str, Any]],
    spec_by_node: Mapping[str, FactorySpec],
    port_by_endpoint: Mapping[tuple[str, str], dict[str, Any]],
    constant_drivers: Mapping[tuple[str, str], int],
) -> tuple[
    list[str],
    dict[tuple[str, str], dict[str, Any]],
    dict[tuple[str, str], list[dict[str, Any]]],
]:
    if len(graph["connections"]) > MAX_CONNECTIONS:
        _fail("HOST_V1_CONNECTION_LIMIT", "connection count exceeds 192")
    destination_drivers: dict[tuple[str, str], dict[str, Any]] = {}
    consumers: dict[tuple[str, str], list[dict[str, Any]]] = {}
    connection_ids: set[str] = set()
    adjacency = {node_id: set() for node_id in node_by_id}
    indegree = {node_id: 0 for node_id in node_by_id}
    for connection in graph["connections"]:
        if connection["connection_id"] in connection_ids:
            _fail("HOST_V1_CONNECTION_ID_DUPLICATE", "connection IDs must be unique")
        connection_ids.add(connection["connection_id"])
        source = (connection["source"]["node_id"], connection["source"]["facet_id"])
        destination = (
            connection["destination"]["node_id"],
            connection["destination"]["facet_id"],
        )
        source_port = port_by_endpoint.get(source)
        destination_port = port_by_endpoint.get(destination)
        if source_port is None or destination_port is None:
            _fail("HOST_V1_CONNECTION_FACET_UNKNOWN", "connection facet is unknown")
        if source_port["direction"] != "outlet" or destination_port["direction"] != "inlet":
            _fail("HOST_V1_CONNECTION_DIRECTION_INVALID", "connection direction is invalid")
        if _port_signature(source_port) != _port_signature(destination_port):
            _fail(
                "HOST_V1_CONNECTION_TYPE_MISMATCH",
                f"connection {connection['connection_id']} requires an implicit conversion",
            )
        if destination in destination_drivers or destination in constant_drivers:
            _fail("HOST_V1_INPUT_MULTIPLE_DRIVERS", f"multiple drivers for {destination}")
        destination_drivers[destination] = connection
        consumers.setdefault(source, []).append(connection)
        source_node, destination_node = source[0], destination[0]
        if destination_node not in adjacency[source_node]:
            adjacency[source_node].add(destination_node)
            indegree[destination_node] += 1

    output_nodes = [
        node_id for node_id, spec in spec_by_node.items() if spec.role == "output"
    ]
    if len(output_nodes) != 1:
        _fail("HOST_V1_STEREO_OUTPUT_COUNT", "exactly one stereo output node is required")
    for node_id, spec in spec_by_node.items():
        for facet_id in spec.input_facets:
            endpoint = (node_id, facet_id)
            port = port_by_endpoint[endpoint]
            optionality = port["port_type"]["optionality"]
            if endpoint not in destination_drivers and endpoint not in constant_drivers:
                if optionality["status"] != "optional":
                    _fail("HOST_V1_REQUIRED_INPUT_MISSING", f"required input {endpoint} is unbound")
        for facet_id in spec.output_facets:
            endpoint = (node_id, facet_id)
            if endpoint not in consumers:
                _fail(
                    "HOST_V1_DISCONNECTED_OUTPUT_UNSUPPORTED",
                    f"output {endpoint} is disconnected",
                )

    ready = sorted(node_id for node_id, value in indegree.items() if value == 0)
    schedule: list[str] = []
    while ready:
        node_id = ready.pop(0)
        schedule.append(node_id)
        for destination in sorted(adjacency[node_id]):
            indegree[destination] -= 1
            if indegree[destination] == 0:
                ready.append(destination)
                ready.sort()
    if len(schedule) != len(node_by_id):
        _fail("HOST_V1_GRAPH_CYCLE", "the graph contains an unsupported cycle")
    if len(schedule) > MAX_SCHEDULE:
        _fail("HOST_V1_SCHEDULE_LIMIT", "schedule length exceeds 64")
    if schedule[-1] != output_nodes[0]:
        _fail("HOST_V1_OUTPUT_NOT_FINAL", "the stereo output must be the sole terminal node")
    return schedule, destination_drivers, consumers


def _buffer_plan(
    schedule: list[str],
    spec_by_node: Mapping[str, FactorySpec],
    consumers: Mapping[tuple[str, str], list[dict[str, Any]]],
) -> tuple[dict[tuple[str, str], int], int]:
    schedule_index = {node_id: index for index, node_id in enumerate(schedule)}
    last_use = {
        endpoint: max(schedule_index[item["destination"]["node_id"]] for item in uses)
        for endpoint, uses in consumers.items()
    }
    all_assignments: dict[tuple[str, str], int] = {}
    assignments: dict[tuple[str, str], int] = {}
    free: set[int] = set()
    next_buffer = 0
    for index, node_id in enumerate(schedule):
        for endpoint, buffer_index in list(assignments.items()):
            if last_use[endpoint] < index:
                free.add(buffer_index)
                del assignments[endpoint]
        for facet_id in spec_by_node[node_id].output_facets:
            endpoint = (node_id, facet_id)
            if free:
                buffer_index = min(free)
                free.remove(buffer_index)
            else:
                buffer_index = next_buffer
                next_buffer += 1
                if next_buffer > MAX_BUFFERS:
                    _fail("HOST_V1_BUFFER_LIMIT", "buffer plan exceeds 128 buffers")
            assignments[endpoint] = buffer_index
            all_assignments[endpoint] = buffer_index
    return all_assignments, next_buffer


def _aligned(value: int, alignment: int) -> int:
    return (value + alignment - 1) // alignment * alignment


def lower_variable_host_package(
    context: OperationContext,
    *,
    project_manifest: Mapping[str, Any],
    host_build_request_reference: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Lower one exact project-owned variable graph to package v1."""

    expected_ref_keys = {"build_request_id", "revision", "content_hash"}
    if set(host_build_request_reference) != expected_ref_keys:
        _fail("HOST_V1_BUILD_REQUEST_REFERENCE_INVALID", "request reference must be closed")
    project = copy.deepcopy(dict(project_manifest))
    _validate_project_ownership(project, context, host_build_request_reference)

    request = _exact_reference(
        context.records["request"],
        host_build_request_reference,
        "build_request_id",
        "HOST_V1_BUILD_REQUEST_NOT_EXACT",
    )
    if request.get("requested_stopping_stage") != "artifact-generation":
        _fail("HOST_V1_BUILD_REQUEST_STAGE_INVALID", "host request must stop at artifact-generation")
    graph = _exact_reference(
        context.records["graphs"],
        request["graph_reference"],
        "graph_id",
        "HOST_V1_GRAPH_NOT_EXACT",
    )
    instrument_reference = {
        key: request["instrument_reference"][key]
        for key in ("instrument_id", "revision", "content_hash")
    }
    instrument = _exact_reference(
        context.records["instruments"],
        instrument_reference,
        "instrument_id",
        "HOST_V1_INSTRUMENT_NOT_EXACT",
    )
    if instrument.get("graph_reference") != {
        "status": "resolved",
        **_ref(graph, "graph_id"),
    }:
        _fail("HOST_V1_INSTRUMENT_GRAPH_MISMATCH", "instrument selects another graph")
    target = _exact_reference(
        context.records["target"],
        request["compute_target_reference"],
        "compute_target_id",
        "HOST_V1_TARGET_NOT_EXACT",
    )
    backend = _exact_reference(
        context.records["backend"],
        request["backend_reference"],
        "backend_id",
        "HOST_V1_BACKEND_NOT_EXACT",
    )
    if target["compute_target_id"] != HOST_TARGET_ID or backend["backend_id"] != HOST_BACKEND_ID:
        _fail("HOST_V1_TARGET_BACKEND_UNSUPPORTED", "only the accepted desktop host pair is supported")
    for key in (
        "hierarchy_edges",
        "compound_interface_mappings",
        "public_ports",
        "public_port_exposures",
        "public_actions",
        "public_displays",
        "public_facet_exposures",
    ):
        if graph.get(key):
            _fail("HOST_V1_GRAPH_SURFACE_UNSUPPORTED", f"non-empty {key} is unsupported")

    node_by_id, spec_by_node, port_by_endpoint = _contracts_for_nodes(context, graph)
    constant_drivers = _parameter_driver_values(graph, port_by_endpoint)
    schedule, destination_drivers, consumers = _validate_connections_and_schedule(
        graph,
        node_by_id,
        spec_by_node,
        port_by_endpoint,
        constant_drivers,
    )
    buffer_by_output, buffer_count = _buffer_plan(schedule, spec_by_node, consumers)
    if buffer_count == 0:
        _fail("HOST_V1_BUFFER_PLAN_EMPTY", "graph produced no buffers")

    compilation = CompilationContext.from_values(
        build_request_reference=copy.deepcopy(dict(host_build_request_reference)),
        closure_source={
            "kind": "project",
            "project_reference": _ref(project, "project_id"),
            "base_record_set_reference": copy.deepcopy(context.record_set_reference),
        },
        records=context.records,
        schemas=context.schemas,
    )
    plan = plan_build(compilation)
    if plan.get("status") != "success":
        codes = sorted(
            {item.get("code", "HOST_V1_COMPILER_FAILED") for item in plan.get("diagnostics", [])}
        )
        _fail("HOST_V1_COMPILER_PLAN_FAILED", ", ".join(codes) or "compiler plan failed")
    resolution = _artifact(plan, "resolution-plan")
    traces = {trace["node_id"]: trace for trace in resolution["traces"]}
    if set(traces) != set(node_by_id):
        _fail("HOST_V1_COMPILER_TRACE_MISMATCH", "compiler traces do not cover the graph")

    graph_connections = {
        connection["connection_id"]: connection for connection in graph["connections"]
    }
    package_connections = []
    for connection_id in sorted(graph_connections):
        connection = graph_connections[connection_id]
        endpoint = (connection["source"]["node_id"], connection["source"]["facet_id"])
        package_connections.append(
            {
                "connection_id": connection_id,
                "source": copy.deepcopy(connection["source"]),
                "destination": copy.deepcopy(connection["destination"]),
                "buffer_index": buffer_by_output[endpoint],
            }
        )

    nodes: list[dict[str, Any]] = []
    state_cursor = 0
    parameter_count = 0
    output_node_id = next(
        node_id for node_id, spec in spec_by_node.items() if spec.role == "output"
    )
    for node_id in schedule:
        source_node = node_by_id[node_id]
        spec = spec_by_node[node_id]
        trace = traces[node_id]
        binding_reference = trace.get("selected_binding_reference")
        if trace.get("status") != "selected" or not isinstance(binding_reference, dict):
            _fail("HOST_V1_BINDING_NOT_SELECTED", f"node {node_id} has no selected binding")
        if (
            binding_reference.get("implementation_id") != spec.binding_id
            or binding_reference.get("revision") != 2
        ):
            _fail("HOST_V1_BINDING_UNSUPPORTED", f"node {node_id} selected another binding")
        binding = _exact_reference(
            context.records["bindings"],
            binding_reference,
            "implementation_id",
            "HOST_V1_BINDING_NOT_EXACT",
        )
        if binding["contract_reference"] != source_node["contract_reference"]:
            _fail("HOST_V1_BINDING_CONTRACT_MISMATCH", f"binding mismatch for {node_id}")

        state_cursor = _aligned(state_cursor, spec.state_alignment)
        state_offset = state_cursor
        state_cursor += spec.state_size
        if state_cursor > MAX_STATE_BYTES:
            _fail("HOST_V1_STATE_LIMIT", "state plan exceeds 65536 bytes")

        inputs: list[dict[str, Any]] = []
        for facet_id in spec.input_facets:
            endpoint = (node_id, facet_id)
            port = port_by_endpoint[endpoint]
            connection = destination_drivers.get(endpoint)
            if connection is not None:
                source_endpoint = (
                    connection["source"]["node_id"],
                    connection["source"]["facet_id"],
                )
                inputs.append(
                    {
                        "facet_id": facet_id,
                        "source_kind": "buffer",
                        "buffer_index": buffer_by_output[source_endpoint],
                    }
                )
                continue
            representation = port["port_type"]["representation"]
            fractional_bits = representation["fractional_bits"]
            if endpoint in constant_drivers:
                value_q = constant_drivers[endpoint]
            else:
                optionality = port["port_type"]["optionality"]
                value_q = _q(optionality["default_value"], fractional_bits)
            inputs.append(
                {
                    "facet_id": facet_id,
                    "source_kind": "constant",
                    "value_q": value_q,
                    "fractional_bits": fractional_bits,
                }
            )

        outputs = [
            {
                "facet_id": facet_id,
                "buffer_index": buffer_by_output[(node_id, facet_id)],
            }
            for facet_id in spec.output_facets
        ]
        contract = _exact_reference(
            context.records["contracts"],
            source_node["contract_reference"],
            "component_contract_id",
            "HOST_V1_CONTRACT_NOT_EXACT",
        )
        node_values = {item["facet_id"]: item["value"] for item in source_node["parameter_values"]}
        parameters = []
        for parameter in contract["parameters"]:
            value = node_values.get(parameter["facet_id"], parameter["default"])
            parameters.append(
                {
                    "facet_id": parameter["facet_id"],
                    "value_q": _q(value, parameter["representation"]["fractional_bits"]),
                }
            )
        parameters.sort(key=core.canonical_json)
        parameter_count += len(parameters)
        if parameter_count > MAX_PARAMETERS:
            _fail("HOST_V1_PARAMETER_LIMIT", "parameter plan exceeds 256 values")
        nodes.append(
            {
                "node_id": node_id,
                "role": spec.role,
                "contract_reference": copy.deepcopy(source_node["contract_reference"]),
                "binding_reference": copy.deepcopy(binding_reference),
                "factory_id": spec.factory_id,
                "inputs": inputs,
                "outputs": outputs,
                "parameters": parameters,
                "state_offset_bytes": state_offset,
                "state_size_bytes": spec.state_size,
                "state_alignment_bytes": spec.state_alignment,
            }
        )
    state_bytes = _aligned(state_cursor, 16)
    if state_bytes == 0:
        state_bytes = 16

    output_inputs = {
        item["facet_id"]: item
        for item in next(node for node in nodes if node["node_id"] == output_node_id)["inputs"]
    }
    left = output_inputs["component-port-000001"]
    right = output_inputs["component-port-000002"]
    if left["source_kind"] != "buffer" or right["source_kind"] != "buffer":
        _fail("HOST_V1_OUTPUT_CONSTANT_UNSUPPORTED", "stereo outputs must be graph buffers")

    package: dict[str, Any] = {
        "schema_version": HOST_PACKAGE_SCHEMA,
        "canonical_profile": "schuss-canonical-json-v1",
        "derived": True,
        "authoritative": False,
        "content_hash": "sha256:" + "0" * 64,
        "runtime_abi": HOST_RUNTIME_ABI,
        "engine_protocol_abi": HOST_ENGINE_PROTOCOL_ABI,
        "factory_registry_version": FACTORY_REGISTRY_VERSION,
        "numeric_profile": HOST_NUMERIC_PROFILE,
        "project_reference": _ref(project, "project_id"),
        "graph_reference": _ref(graph, "graph_id"),
        "instrument_reference": _ref(instrument, "instrument_id"),
        "host_build_request_reference": _ref(request, "build_request_id"),
        "compute_target_reference": _ref(target, "compute_target_id"),
        "backend_reference": _ref(backend, "backend_id"),
        "source_plan_sha256": hashlib.sha256(
            core.canonical_json(plan).encode("utf-8")
        ).hexdigest(),
        "sample_rate_hz": 48000,
        "max_block_frames": 512,
        "control_period_frames": 16,
        "block_policy": "bounded-variable-with-final-partial",
        "input_channels": 0,
        "output_channels": 2,
        "latency_frames": 0,
        "tail_frames": 0,
        "seed": 0,
        "limits": {
            "node_count": MAX_NODES,
            "connection_count": MAX_CONNECTIONS,
            "buffer_count": MAX_BUFFERS,
            "state_bytes": MAX_STATE_BYTES,
            "parameter_count": MAX_PARAMETERS,
            "event_count": MAX_EVENTS,
            "schedule_length": MAX_SCHEDULE,
        },
        "memory_plan": {
            "state_bytes": state_bytes,
            "state_alignment_bytes": 16,
            "buffer_count": buffer_count,
            "buffer_frames": 512,
            "buffer_bytes": buffer_count * 512 * 4,
            "parameter_count": parameter_count,
            "event_capacity": MAX_EVENTS,
        },
        "nodes": nodes,
        "connections": sorted(package_connections, key=core.canonical_json),
        "schedule": schedule,
        "outputs": {
            "node_id": output_node_id,
            "left_buffer": left["buffer_index"],
            "right_buffer": right["buffer_index"],
        },
        "event_contract": {
            "capacity": MAX_EVENTS,
            "ordering": "frame-offset-then-sequence",
            "accepted_kinds": ["midi-message", "parameter-q27"],
            "overflow_policy": "drop-newest-and-count",
        },
        "exclusions": sorted(
            {
                "cycles and implicit delay",
                "dynamic graph mutation on callback",
                "implicit stream conversion",
                "JUCE dependency in schuss_rt",
                "Ksoloti equivalence claim",
                "state migration during replacement",
                "unsupported factories outside Task 031 seven",
            }
        ),
    }
    schema = context.schemas.get("host_runtime_package_v1")
    if schema is None:
        _fail("HOST_V1_PACKAGE_SCHEMA_UNAVAILABLE", "package v1 schema is absent")
    package["content_hash"] = core.record_content_hash(package, schema)
    errors = core.schema_errors(package, schema, schema)
    if errors:
        _fail("HOST_V1_PACKAGE_SCHEMA_INVALID", "; ".join(errors))
    return package, plan


__all__ = [
    "FACTORY_REGISTRY_VERSION",
    "FACTORY_SPECS",
    "HOST_ENGINE_PROTOCOL_ABI",
    "HOST_NUMERIC_PROFILE",
    "HOST_PACKAGE_SCHEMA",
    "HOST_RUNTIME_ABI",
    "lower_variable_host_package",
]
