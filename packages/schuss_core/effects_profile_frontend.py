"""Identity-independent direct frontend for the exact reverb-free effects profile."""

from __future__ import annotations

import copy
import hashlib
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .compiler_front_half import core
from .effects_direct_semantics import semantic_goldens as task025_semantic_goldens


FRONTEND_ID = "schuss-direct-frontend-000002"
FRONTEND_VERSION = 1
PROFILE_ID = "schuss-semantic-profile-000001"
PROFILE_VERSION = 1
BLOCK_SIZE = 16
Q21_SCALE = 1 << 21
Q27_SCALE = 1 << 27

TARGET_REFERENCE = {
    "compute_target_id": "schuss-compute-target-000001",
    "revision": 2,
    "content_hash": "sha256:d8a9652bd079d0f2a8806cc4922f2a380c8092549f267047d5a4a0360b4a6753",
}

ROLE_CONTRACTS = {
    "saw": {"component_contract_id": "schuss-component-contract-000012", "revision": 1, "content_hash": "sha256:3f399547dbe7a1a76bdcedc1d1d886ccd49d0620fdbca3fbace6aac0a9d2292c"},
    "pwm": {"component_contract_id": "schuss-component-contract-000013", "revision": 1, "content_hash": "sha256:2c4d15d5228dadfbf9c5ecb8734e7207b7157fc8960fb4100b461b59f859daa0"},
    "soft": {"component_contract_id": "schuss-component-contract-000016", "revision": 1, "content_hash": "sha256:c98e44b172cf256439edfe2f51c15499f29ffe39900d9f8de72c339e346762e2"},
    "smooth": {"component_contract_id": "schuss-component-contract-000015", "revision": 1, "content_hash": "sha256:705b8e11c00d985eb8fd010a2d3fd71cb891f00711ad647b0746cdfb90c6ff81"},
    "crossfade": {"component_contract_id": "schuss-component-contract-000003", "revision": 1, "content_hash": "sha256:96a29faf58769be5f2ac52de07aa80cae3dcdff28f0f3c158fb1fd12cc234a8d"},
    "vca": {"component_contract_id": "schuss-component-contract-000020", "revision": 1, "content_hash": "sha256:0cf9737582327560e82feb565fd3092993b750938a9669fc43305b5658ac5490"},
    "output": {"component_contract_id": "schuss-component-contract-000009", "revision": 1, "content_hash": "sha256:179c1526ed2bd6d9ad1c6fbfc9caa7abc21f479bef50cf93c8599b5817ca8718"},
}

ROLE_OPCODES = {
    "saw": "blep-saw-q27",
    "pwm": "blep-pwm-q27",
    "soft": "soft-clip-q27",
    "smooth": "exponential-smooth-q27",
    "crossfade": "linear-mix-current-block-q27",
    "vca": "interpolated-vca-q27",
    "output": "stereo-audio-output-q27",
}

OPERATION_SPEC_IDS = {
    "blep-saw-q27": "schuss-direct-operation-spec-000008",
    "blep-pwm-q27": "schuss-direct-operation-spec-000009",
    "exponential-smooth-q27": "schuss-direct-operation-spec-000010",
    "soft-clip-q27": "schuss-direct-operation-spec-000011",
    "interpolated-vca-q27": "schuss-direct-operation-spec-000013",
    "linear-mix-current-block-q27": "schuss-direct-operation-spec-000014",
    "stereo-audio-output-q27": "schuss-direct-operation-spec-000007",
}

DIRECT_BINDINGS = {
    "saw": ("schuss-implementation-000090", 1),
    "pwm": ("schuss-implementation-000091", 1),
    "smooth": ("schuss-implementation-000092", 1),
    "soft": ("schuss-implementation-000093", 1),
    "vca": ("schuss-implementation-000095", 1),
    "crossfade": ("schuss-implementation-000046", 2),
    "output": ("schuss-implementation-000048", 2),
}

PARAMETERS = {
    "saw": [{"facet_id": "component-parameter-000001", "value": "-24"}],
    "pwm": [{"facet_id": "component-parameter-000001", "value": "-12"}],
    "soft": [], "smooth": [], "crossfade": [], "vca": [], "output": [],
}

ROLE_CONNECTIONS = (
    ("saw", "component-port-000002", "soft", "component-port-000001"),
    ("pwm", "component-port-000003", "crossfade", "component-port-000001"),
    ("soft", "component-port-000002", "crossfade", "component-port-000002"),
    ("smooth", "component-port-000002", "vca", "component-port-000001"),
    ("crossfade", "component-port-000004", "vca", "component-port-000002"),
    ("vca", "component-port-000003", "output", "component-port-000001"),
    ("vca", "component-port-000003", "output", "component-port-000002"),
)

PUBLIC_PARAMETER_EXPECTATIONS = {
    "motion": {"default": "0.5", "facet_id": "graph-facet-000001", "destination_role": "smooth", "destination_facet": "component-port-000001"},
    "blend": {"default": "0.5", "facet_id": "graph-facet-000002", "destination_role": "crossfade", "destination_facet": "component-port-000003"},
}

SCHEDULE = (
    ("dsp-operation-000001", "saw"),
    ("dsp-operation-000002", "pwm"),
    ("dsp-operation-000003", "soft"),
    ("dsp-operation-000004", "smooth"),
    ("dsp-operation-000005", "crossfade"),
    ("dsp-operation-000006", "vca"),
    ("dsp-operation-000007", "output"),
    ("dsp-operation-000008", "motion-latch"),
    ("dsp-operation-000009", "blend-latch"),
)


def _canonical_bytes(value: Any) -> bytes:
    return core.canonical_json(value).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _ref(record: Mapping[str, Any], id_field: str) -> dict[str, Any]:
    return {id_field: record[id_field], "revision": record["revision"], "content_hash": record["content_hash"]}


def _public_shape(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: copy.deepcopy(value[key])
        for key in ("semantic_key", "default", "domain", "value_type", "update_behavior")
    }


@dataclass(frozen=True)
class ProfileMatch:
    role_nodes: dict[str, str]
    profile_hash: str


def profile_definition() -> dict[str, Any]:
    return {
        "profile_id": PROFILE_ID,
        "version": PROFILE_VERSION,
        "contracts": copy.deepcopy(ROLE_CONTRACTS),
        "parameters": copy.deepcopy(PARAMETERS),
        "connections": [list(item) for item in ROLE_CONNECTIONS],
        "public_parameters": {
            key: {name: item[name] for name in ("default", "destination_role", "destination_facet")}
            for key, item in PUBLIC_PARAMETER_EXPECTATIONS.items()
        },
        "schedule": [role for _, role in SCHEDULE],
        "operation_specs": copy.deepcopy(OPERATION_SPEC_IDS),
        "bindings": {role: list(value) for role, value in DIRECT_BINDINGS.items()},
        "instrument_policy": "included-headless-graph-mapping-only",
        "reverb": "unsupported-and-absent",
    }


def profile_reference() -> dict[str, Any]:
    return {
        "profile_id": PROFILE_ID,
        "version": PROFILE_VERSION,
        "content_hash": "sha256:" + _sha256(_canonical_bytes(profile_definition())),
    }


def semantic_profile_signature(graph: Mapping[str, Any]) -> ProfileMatch:
    value = copy.deepcopy(dict(graph))
    nodes = value.get("nodes")
    if not isinstance(nodes, list) or len(nodes) != len(ROLE_CONTRACTS):
        raise ValueError("EFFECTS_PROFILE_NODE_SET_UNSUPPORTED")
    by_contract = {item["component_contract_id"]: role for role, item in ROLE_CONTRACTS.items()}
    role_nodes: dict[str, str] = {}
    node_roles: dict[str, str] = {}
    for node in nodes:
        role = by_contract.get(node.get("contract_reference", {}).get("component_contract_id"))
        if role is None or node.get("contract_reference") != ROLE_CONTRACTS[role] or role in role_nodes:
            raise ValueError("EFFECTS_PROFILE_CONTRACT_SET_UNSUPPORTED")
        if node.get("parameter_values") != PARAMETERS[role] or node.get("attribute_values") != []:
            raise ValueError("EFFECTS_PROFILE_NODE_VALUES_UNSUPPORTED")
        role_nodes[role] = node["node_id"]
        node_roles[node["node_id"]] = role
    if set(role_nodes) != set(ROLE_CONTRACTS):
        raise ValueError("EFFECTS_PROFILE_CONTRACT_SET_UNSUPPORTED")
    observed_connections = []
    for item in value.get("connections", []):
        try:
            observed_connections.append((
                node_roles[item["source"]["node_id"]], item["source"]["facet_id"],
                node_roles[item["destination"]["node_id"]], item["destination"]["facet_id"],
            ))
        except KeyError as exc:
            raise ValueError("EFFECTS_PROFILE_CONNECTION_ENDPOINT_UNSUPPORTED") from exc
    if sorted(observed_connections) != sorted(ROLE_CONNECTIONS):
        raise ValueError("EFFECTS_PROFILE_CONNECTIONS_UNSUPPORTED")
    if value.get("hierarchy_edges") != [] or value.get("compound_interface_mappings") != []:
        raise ValueError("EFFECTS_PROFILE_HIERARCHY_UNSUPPORTED")
    for name in ("public_ports", "public_port_exposures", "public_facet_exposures", "public_actions", "public_displays"):
        if value.get(name) != []:
            raise ValueError("EFFECTS_PROFILE_PUBLIC_FACETS_UNSUPPORTED")
    public = value.get("public_parameters", [])
    by_semantic = {item.get("semantic_key"): item for item in public}
    if set(by_semantic) != set(PUBLIC_PARAMETER_EXPECTATIONS):
        raise ValueError("EFFECTS_PROFILE_PUBLIC_PARAMETERS_UNSUPPORTED")
    bindings = value.get("parameter_bindings", [])
    if len(bindings) != 2:
        raise ValueError("EFFECTS_PROFILE_PARAMETER_BINDINGS_UNSUPPORTED")
    for semantic, expectation in PUBLIC_PARAMETER_EXPECTATIONS.items():
        parameter = by_semantic[semantic]
        if parameter.get("facet_id") != expectation["facet_id"] or parameter.get("default") != expectation["default"]:
            raise ValueError("EFFECTS_PROFILE_PUBLIC_PARAMETER_VALUE_UNSUPPORTED")
        matches = [item for item in bindings if item.get("source_graph_parameter_id") == parameter["facet_id"]]
        if len(matches) != 1:
            raise ValueError("EFFECTS_PROFILE_PARAMETER_BINDINGS_UNSUPPORTED")
        binding = matches[0]
        destination = binding.get("destination", {})
        if (
            node_roles.get(destination.get("node_id")) != expectation["destination_role"]
            or destination.get("facet_id") != expectation["destination_facet"]
            or binding.get("binding_kind") != "parameter-to-port"
            or binding.get("driver_policy") != "exclusive"
            or binding.get("update_boundary") != "control-cycle"
            or binding.get("smoothing") != {"completion": "next-control-cycle", "kind": "linear", "responsibility": "graph"}
            or binding.get("transform", {}).get("curve") != "linear"
            or binding.get("transform", {}).get("polarity") != "direct"
        ):
            raise ValueError("EFFECTS_PROFILE_PARAMETER_BINDING_SEMANTICS_UNSUPPORTED")
    semantic = {
        "profile": profile_definition(),
        "public_shapes": {key: _public_shape(by_semantic[key]) for key in sorted(by_semantic)},
        "binding_domains": {
            key: {
                "source": copy.deepcopy(next(item for item in bindings if item["source_graph_parameter_id"] == by_semantic[key]["facet_id"])["source_domain"]),
                "destination": copy.deepcopy(next(item for item in bindings if item["source_graph_parameter_id"] == by_semantic[key]["facet_id"])["destination_domain"]),
                "transform": copy.deepcopy(next(item for item in bindings if item["source_graph_parameter_id"] == by_semantic[key]["facet_id"])["transform"]),
            }
            for key in sorted(by_semantic)
        },
    }
    digest = "sha256:" + _sha256(_canonical_bytes(semantic))
    return ProfileMatch(role_nodes, digest)


def _validate_instrument(instrument: Mapping[str, Any], graph: Mapping[str, Any]) -> None:
    if instrument.get("graph_reference", {}).get("status") != "resolved" or {
        key: instrument["graph_reference"].get(key) for key in ("graph_id", "revision", "content_hash")
    } != _ref(graph, "graph_id"):
        raise ValueError("EFFECTS_PROFILE_INSTRUMENT_GRAPH_UNSUPPORTED")
    parameters = {item.get("facet_id"): item for item in instrument.get("parameters", [])}
    mappings = instrument.get("graph_mappings", [])
    if len(parameters) != 2 or len(mappings) != 2:
        raise ValueError("EFFECTS_PROFILE_INSTRUMENT_SHAPE_UNSUPPORTED")
    expected = {"instrument-parameter-000001": "graph-facet-000001", "instrument-parameter-000002": "graph-facet-000002"}
    for source, destination in expected.items():
        if source not in parameters or parameters[source].get("default") != "0.5":
            raise ValueError("EFFECTS_PROFILE_INSTRUMENT_PARAMETER_UNSUPPORTED")
        found = [item for item in mappings if item.get("source", {}).get("facet_id") == source]
        if len(found) != 1 or found[0].get("destination", {}).get("facet_id") != destination:
            raise ValueError("EFFECTS_PROFILE_INSTRUMENT_MAPPING_UNSUPPORTED")
    if instrument.get("device_input_mappings") != [] or instrument.get("device_feedback_mappings") != []:
        raise ValueError("EFFECTS_PROFILE_INSTRUMENT_DEVICE_MAPPING_UNSUPPORTED")


def match_effects_profile(
    plan: Mapping[str, Any], graph: Mapping[str, Any], instrument: Mapping[str, Any],
    request: Mapping[str, Any], contracts: Iterable[Mapping[str, Any]],
    operation_specs: Iterable[Mapping[str, Any]],
) -> ProfileMatch:
    if plan.get("status") != "success":
        raise ValueError("EFFECTS_PROFILE_PLAN_NOT_SUCCESSFUL")
    request_ref = plan.get("input_closure", {}).get("build_request_reference", {})
    if request_ref != _ref(request, "build_request_id"):
        raise ValueError("EFFECTS_PROFILE_REQUEST_NOT_EXACT")
    if request.get("graph_reference") != _ref(graph, "graph_id"):
        raise ValueError("EFFECTS_PROFILE_REQUEST_GRAPH_UNSUPPORTED")
    if request.get("instrument_reference") != {"status": "included", **_ref(instrument, "instrument_id")}:
        raise ValueError("EFFECTS_PROFILE_REQUEST_INSTRUMENT_UNSUPPORTED")
    if request.get("compute_target_reference") != TARGET_REFERENCE:
        raise ValueError("EFFECTS_PROFILE_TARGET_UNSUPPORTED")
    backend = request.get("backend_reference", {})
    if backend.get("backend_id") != "schuss-backend-000002" or backend.get("revision") != 4:
        raise ValueError("EFFECTS_PROFILE_BACKEND_UNSUPPORTED")
    match = semantic_profile_signature(graph)
    _validate_instrument(instrument, graph)
    contract_records = {item["component_contract_id"]: item for item in contracts}
    for reference in ROLE_CONTRACTS.values():
        record = contract_records.get(reference["component_contract_id"])
        if record is None or _ref(record, "component_contract_id") != reference:
            raise ValueError("EFFECTS_PROFILE_CONTRACT_RECORD_UNSUPPORTED")
    specs = {item.get("opcode"): item for item in operation_specs}
    for role, opcode in ROLE_OPCODES.items():
        spec = specs.get(opcode)
        if (
            spec is None
            or spec.get("direct_operation_spec_id") != OPERATION_SPEC_IDS[opcode]
            or spec.get("revision") != 1
            or spec.get("contract_reference") != ROLE_CONTRACTS[role]
        ):
            raise ValueError("EFFECTS_PROFILE_OPERATION_SPEC_UNSUPPORTED")
    resolution = [item["payload"] for item in plan.get("artifacts", []) if item.get("descriptor", {}).get("artifact_kind") == "resolution-plan"]
    if len(resolution) != 1 or resolution[0].get("status") != "success":
        raise ValueError("EFFECTS_PROFILE_RESOLUTION_PLAN_UNSUPPORTED")
    traces = {item["node_id"]: item for item in resolution[0].get("traces", [])}
    if set(traces) != set(match.role_nodes.values()):
        raise ValueError("EFFECTS_PROFILE_RESOLUTION_TRACE_SET_UNSUPPORTED")
    for role, node_id in match.role_nodes.items():
        selected = traces[node_id].get("selected_binding_reference", {})
        if (selected.get("implementation_id"), selected.get("revision")) != DIRECT_BINDINGS[role]:
            raise ValueError("EFFECTS_PROFILE_BINDING_SELECTION_UNSUPPORTED")
    return match


def _normalized_module(plan: Mapping[str, Any], graph: Mapping[str, Any], match: ProfileMatch, specs: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    operations = []
    for operation_id, role in SCHEDULE:
        value: dict[str, Any] = {"operation_id": operation_id, "role": role, "origin": {"subject_id": match.role_nodes.get(role, "graph-facet-" + role)}}
        if role in ROLE_OPCODES:
            opcode = ROLE_OPCODES[role]
            value.update({"opcode": opcode, "contract_reference": copy.deepcopy(ROLE_CONTRACTS[role]), "operation_spec_reference": _ref(specs[opcode], "direct_operation_spec_id")})
        else:
            value["opcode"] = "public-control-next-cycle-latch-q27"
        operations.append(value)
    connections = [{"connection_id": item["connection_id"], "source": copy.deepcopy(item["source"]), "destination": copy.deepcopy(item["destination"]), "lowering": "direct-exact-no-adapter"} for item in sorted(graph["connections"], key=lambda item: item["connection_id"])]
    connections.extend({"connection_id": item["binding_id"], "source": {"graph_parameter_id": item["source_graph_parameter_id"]}, "destination": copy.deepcopy(item["destination"]), "lowering": "next-control-cycle-latch"} for item in sorted(graph["parameter_bindings"], key=lambda item: item["binding_id"]))
    parameter_values = []
    for role in ("saw", "pwm"):
        parameter_values.append({"node_id": match.role_nodes[role], "facet_id": "component-parameter-000001", "raw_value": int(PARAMETERS[role][0]["value"]) * Q21_SCALE})
    parameter_values.extend([
        {"node_id": match.role_nodes["smooth"], "facet_id": "component-parameter-000001", "raw_value": 0},
        {"node_id": match.role_nodes["pwm"], "facet_id": "component-port-000002", "raw_value": 0},
    ])
    return {
        "schema_version": "normalized-dsp-module-v1", "canonical_profile": "schuss-canonical-json-v1", "derived": True, "authoritative": False,
        "module_id": "schuss-normalized-dsp-module-000003", "frontend": {"frontend_id": FRONTEND_ID, "version": FRONTEND_VERSION},
        "source_plan_sha256": _sha256(_canonical_bytes(plan)), "graph_reference": _ref(graph, "graph_id"),
        "runtime_contract": {"sample_rate_hz": 48000, "audio_block_frames": BLOCK_SIZE, "patch_abi": "ksoloti-xpatch-task026a", "runtime_calls": ["MTOFEXTENDED", "blept", "___SMMUL", "___SMMLA", "__SSAT", "__USAT"], "java_required": False, "legacy_boundary_patch_required": False},
        "numeric_contracts": [{"name": "semitone", "representation": "signed-q21", "scale": Q21_SCALE, "overflow": "operation-specific"}, {"name": "audio-control", "representation": "signed-q27", "scale": Q27_SCALE, "overflow": "operation-specific"}],
        "parameter_values": parameter_values,
        "state_layout": [
            {"state_id": "state-saw", "owner": match.role_nodes["saw"], "initial": "zero-phase-tail-voices"},
            {"state_id": "state-pwm", "owner": match.role_nodes["pwm"], "initial": "zero-phase-width-tail-voices"},
            {"state_id": "state-smooth", "owner": match.role_nodes["smooth"], "initial": 0},
            {"state_id": "state-vca", "owner": match.role_nodes["vca"], "initial": 0},
            {"state_id": "state-motion-latch", "owner": "graph-facet-000001", "initial": 0, "update": "after-all-operations"},
            {"state_id": "state-blend-latch", "owner": "graph-facet-000002", "initial": 0, "update": "after-all-operations"},
        ],
        "connections": connections, "operations": operations,
        "schedule": {"unit": "one-control-cycle-per-16-sample-audio-block", "operation_ids": [item[0] for item in SCHEDULE], "latch_updates": ["state-motion-latch", "state-blend-latch"]},
        "outputs": [{"value_id": "dsp-value-output-left", "origin": match.role_nodes["output"] + "/component-port-000001", "kind": "audio-buffer-q27"}, {"value_id": "dsp-value-output-right", "origin": match.role_nodes["output"] + "/component-port-000002", "kind": "audio-buffer-q27"}],
    }


def _source_map(graph: Mapping[str, Any], instrument: Mapping[str, Any], match: ProfileMatch, contracts: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    mappings: list[dict[str, Any]] = []
    for operation_id, role in SCHEDULE:
        mappings.append({"generated": "operation:" + role, "origin": match.role_nodes.get(role, role), "operation_id": operation_id})
    role_by_node = {node: role for role, node in match.role_nodes.items()}
    for node in sorted(graph["nodes"], key=lambda item: item["node_id"]):
        role = role_by_node[node["node_id"]]
        mappings.append({"generated": "node:" + role, "origin": node["node_id"], "contract_reference": copy.deepcopy(ROLE_CONTRACTS[role])})
        record = contracts[ROLE_CONTRACTS[role]["component_contract_id"]]
        for collection, kind in (("ports", "port"), ("parameters", "parameter"), ("attributes", "attribute"), ("actions", "action"), ("displays", "display"), ("state_declarations", "state")):
            for facet in sorted(record.get(collection, []), key=lambda item: item.get("facet_id", item.get("state_id", ""))):
                facet_id = facet.get("facet_id", facet.get("state_id"))
                mappings.append({"generated": f"facet:{role}/{facet_id}", "origin": f"{node['node_id']}/{facet_id}", "facet_kind": kind})
    for item in sorted(graph["connections"], key=lambda value: value["connection_id"]):
        mappings.append({"generated": "connection:" + item["connection_id"], "origin": item["connection_id"], "source": copy.deepcopy(item["source"]), "destination": copy.deepcopy(item["destination"])})
    for item in sorted(graph["parameter_bindings"], key=lambda value: value["binding_id"]):
        mappings.append({"generated": "public-parameter:" + item["binding_id"], "origin": item["binding_id"], "destination": copy.deepcopy(item["destination"])})
    for item in sorted(instrument["graph_mappings"], key=lambda value: value["mapping_id"]):
        mappings.append({"generated": "instrument-mapping:" + item["mapping_id"], "origin": instrument["instrument_id"] + "/" + item["mapping_id"], "destination": copy.deepcopy(item["destination"])})
    return {"schema_version": "direct-source-map-v2", "graph_reference": _ref(graph, "graph_id"), "instrument_reference": _ref(instrument, "instrument_id"), "semantic_profile": profile_reference(), "generated_symbols": ["xpatch_init", "PatchProcess", "PatchDispose", "ApplyPreset", "PatchMidiInHandler", "schuss_effects_set_motion_q27", "schuss_effects_set_blend_q27"], "mappings": mappings}


def _generated_cpp() -> str:
    return r'''#include "xpatch.h"
#include "axoloti_oscs.h"

#pragma GCC diagnostic ignored "-Wunused-parameter"

int32buffer AudioInputLeft, AudioInputRight, AudioOutputLeft, AudioOutputRight;
static volatile int32_t SchussMotionInputQ27;
static volatile int32_t SchussBlendInputQ27;

extern "C" void schuss_effects_set_motion_q27(int32_t value) { SchussMotionInputQ27 = __USAT(value, 27); }
extern "C" void schuss_effects_set_blend_q27(int32_t value) { SchussBlendInputQ27 = __USAT(value, 27); }

struct SchussEffectsState {
  static const uint16_t NPEXCH = 4;
  ParameterExchange_t parameters[NPEXCH];
  int32_t display_vector[5];
  int32_t saw_phase;
  int16_t* saw_blep[4];
  uint32_t saw_next;
  int32_t pwm_phase;
  int16_t* pwm_blep[8];
  uint32_t pwm_next;
  int32_t pwm_width_phase;
  int32_t smooth_value;
  int32_t vca_previous;
  int32_t motion_latch;
  int32_t blend_latch;
};
static SchussEffectsState State;
static const int32_t InitialParameters[4] = {-50331648, -25165824, 0, 0};

static void initialize_state(void) {
  State.display_vector[0] = 0x446F7841; State.display_vector[1] = 0; State.display_vector[2] = 2; State.display_vector[3] = 0; State.display_vector[4] = 0;
  State.saw_phase = 0; State.saw_next = 0; State.pwm_phase = 0; State.pwm_next = 0; State.pwm_width_phase = 0;
  State.smooth_value = 0; State.vca_previous = 0; State.motion_latch = 0; State.blend_latch = 0;
  SchussMotionInputQ27 = 0; SchussBlendInputQ27 = 0;
  for (int index = 0; index < 4; ++index) State.saw_blep[index] = &blept[BLEPSIZE - 1];
  for (int index = 0; index < 8; ++index) State.pwm_blep[index] = &blept[BLEPSIZE - 1];
  for (uint32_t index = 0; index < 4; ++index) {
    State.parameters[index].value = InitialParameters[index]; State.parameters[index].modvalue = InitialParameters[index]; State.parameters[index].signals = 0; State.parameters[index].pfunction = 0;
  }
  State.parameters[0].pfunction = pfun_signed_clamp; State.parameters[1].pfunction = pfun_signed_clamp; State.parameters[2].pfunction = pfun_unsigned_clamp; State.parameters[3].pfunction = pfun_signed_clamp;
  for (uint32_t index = 0; index < 4; ++index) State.parameters[index].pfunction(&State.parameters[index]);
}

static void process_saw(int32buffer& output) {
  int32_t frequency; MTOFEXTENDED(State.parameters[0].finalvalue, frequency);
  int16_t* last = &blept[BLEPSIZE - 1];
  for (int sample = 0; sample < BUFSIZE; ++sample) {
    int32_t previous = State.saw_phase; State.saw_phase = previous + frequency;
    if ((State.saw_phase > 0) && !(previous > 0)) { State.saw_next = (State.saw_next + 1) & 3; State.saw_blep[State.saw_next] = &blept[State.saw_phase / (frequency >> 6)]; }
    int32_t total = 0;
    for (int voice = 0; voice < 4; ++voice) { int16_t* cursor = State.saw_blep[voice]; total += *cursor; cursor += 64; if (cursor >= last) cursor = last; State.saw_blep[voice] = cursor; }
    total = (16384 * 4) - total - 8192; uint32_t phase = State.saw_phase; output[sample] = (phase >> 5) + (total << 13);
  }
}

static uint32_t pwm_index(uint32_t delta, uint32_t frequency) {
  if (frequency >> 24) return delta / (frequency >> 6);
  if (frequency) return (delta << 6) / frequency;
  return 0;
}
static void dispatch_pwm_phase(uint32_t frequency) { State.pwm_next = (State.pwm_next + 1) & 7; State.pwm_blep[State.pwm_next] = &blept[pwm_index((uint32_t)State.pwm_phase, frequency)]; State.pwm_width_phase = ((1 << 27) + State.parameters[3].finalvalue) << 4; }
static void dispatch_pwm_width(uint32_t frequency) { State.pwm_next = (State.pwm_next + 1) & 7; State.pwm_blep[State.pwm_next] = &blept[pwm_index((uint32_t)(State.pwm_phase - State.pwm_width_phase), frequency)]; }
static void process_pwm(int32buffer& output) {
  uint32_t frequency; MTOFEXTENDED(State.parameters[1].finalvalue, frequency); int16_t* last = &blept[BLEPSIZE - 1];
  for (int sample = 0; sample < BUFSIZE; ++sample) {
    int32_t previous = State.pwm_phase; State.pwm_phase = previous + frequency; int32_t total = 0;
    bool phase_cross = (State.pwm_phase > 0) && !(previous > 0); bool width_cross = ((State.pwm_phase - State.pwm_width_phase) > 0) && !((previous - State.pwm_width_phase) > 0);
    if (State.pwm_phase >= State.pwm_phase - State.pwm_width_phase) { if (phase_cross) dispatch_pwm_phase(frequency); if (width_cross) dispatch_pwm_width(frequency); }
    else { if (width_cross) dispatch_pwm_width(frequency); if (phase_cross) dispatch_pwm_phase(frequency); }
    for (int voice = 0; voice < 8; ++voice) { int16_t* cursor = State.pwm_blep[voice]; if (voice & 1) total += *cursor; else total -= *cursor; cursor += 64; if (cursor >= last) cursor = last; State.pwm_blep[voice] = cursor; }
    total -= ((((State.pwm_next + 1) & 1) << 1) - 1) << 13; output[sample] = total << 13;
  }
}
static void process_soft(const int32buffer input, int32buffer& output) { for (int sample = 0; sample < BUFSIZE; ++sample) { int32_t value = __SSAT(input[sample], 28); int32_t q31 = value << 3; int32_t cubic = ___SMMUL(q31, ___SMMUL(q31, q31)); output[sample] = value + (value >> 1) - cubic; } }
static int32_t process_smooth(int32_t input) { State.smooth_value = ___SMMLA(State.smooth_value - input, (-1 << 26) + (State.parameters[2].finalvalue >> 1), State.smooth_value); return State.smooth_value; }
static void process_crossfade(const int32buffer first, const int32buffer second, int32_t control, int32buffer& output) { control = __USAT(control, 27); int32_t complement = (128 << 20) - control; for (int sample = 0; sample < BUFSIZE; ++sample) { int64_t mixed = (int64_t)second[sample] * control + (int64_t)first[sample] * complement; output[sample] = mixed >> 27; } }
static void process_vca(const int32buffer input, int32_t gain, int32buffer& output) { int32_t step = (gain - State.vca_previous) >> 4; int32_t interpolation = State.vca_previous; State.vca_previous = gain; for (int sample = 0; sample < BUFSIZE; ++sample) { output[sample] = ___SMMUL(input[sample], interpolation) << 5; interpolation += step; } }
static void process_output(const int32buffer mono) { for (int sample = 0; sample < BUFSIZE; ++sample) { AudioOutputLeft[sample] += __SSAT(mono[sample], 28); AudioOutputRight[sample] += __SSAT(mono[sample], 28); } State.display_vector[3] = mono[0]; State.display_vector[4] = mono[0]; }

static void process_graph(void) {
  int32buffer saw, pwm, clipped, mixed, amplified;
  for (int sample = 0; sample < BUFSIZE; ++sample) { AudioOutputLeft[sample] = 0; AudioOutputRight[sample] = 0; }
  process_saw(saw); process_pwm(pwm); process_soft(saw, clipped); int32_t gain = process_smooth(State.motion_latch); process_crossfade(pwm, clipped, State.blend_latch, mixed); process_vca(mixed, gain, amplified); process_output(amplified);
  State.motion_latch = __USAT(SchussMotionInputQ27, 27); State.blend_latch = __USAT(SchussBlendInputQ27, 27);
}
void PatchProcess(int32_t* input, int32_t* output) { for (int index = 0; index < BUFSIZE; ++index) { AudioInputLeft[index] = input[index << 1] >> 4; AudioInputRight[index] = input[(index << 1) + 1] >> 4; } process_graph(); for (int index = 0; index < BUFSIZE; ++index) { output[index << 1] = __SSAT(AudioOutputLeft[index], 28) << 4; output[(index << 1) + 1] = __SSAT(AudioOutputRight[index], 28) << 4; } }
void ApplyPreset(uint8_t index) { if (index == 0) initialize_state(); }
void PatchMidiInHandler(midi_device_t device, uint8_t port, uint8_t status, uint8_t data1, uint8_t data2) {}
typedef void (*SchussFunction)(void); extern SchussFunction __ctor_array_start; extern SchussFunction __ctor_array_end; extern SchussFunction __dtor_array_start; extern SchussFunction __dtor_array_end;
void PatchDispose(void) { SchussFunction* function = &__dtor_array_start; while (function < &__dtor_array_end) { (*function)(); ++function; } }
static void xpatch_init2(uint32_t firmware_id) { if (firmware_id != 0x5021D42A) return; extern uint32_t _pbss_start; extern uint32_t _pbss_end; for (volatile uint32_t* value = &_pbss_start; value < &_pbss_end; ++value) *value = 0; SchussFunction* function = &__ctor_array_start; while (function < &__ctor_array_end) { (*function)(); ++function; } patchMeta.npresets = 0; patchMeta.npreset_entries = 0; patchMeta.pPresets = 0; patchMeta.pPExch = &State.parameters[0]; patchMeta.pDisplayVector = &State.display_vector[0]; patchMeta.numPEx = 4; patchMeta.patchID = -2064091902; extern char _sdram_dyn_start; extern char _sdram_dyn_end; sdram_init(&_sdram_dyn_start, &_sdram_dyn_end); initialize_state(); patchMeta.fptr_applyPreset = ApplyPreset; patchMeta.fptr_patch_dispose = PatchDispose; patchMeta.fptr_MidiInHandler = PatchMidiInHandler; patchMeta.fptr_dsp_process = PatchProcess; }
extern "C" __attribute__((section(".boot"))) void xpatch_init(uint32_t firmware_id) { xpatch_init2(firmware_id); }
'''


def lower_effects_profile(
    plan: Mapping[str, Any], graph: Mapping[str, Any], instrument: Mapping[str, Any], request: Mapping[str, Any],
    contracts: Iterable[Mapping[str, Any]], operation_specs: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    contracts_list = [copy.deepcopy(dict(item)) for item in contracts]
    specs_list = [copy.deepcopy(dict(item)) for item in operation_specs]
    match = match_effects_profile(plan, graph, instrument, request, contracts_list, specs_list)
    specs = {item["opcode"]: item for item in specs_list}
    contracts_by_id = {item["component_contract_id"]: item for item in contracts_list}
    module = _normalized_module(plan, graph, match, specs)
    source_map = _source_map(graph, instrument, match, contracts_by_id)
    cpp = _generated_cpp()
    module_bytes = _canonical_bytes(module); map_bytes = _canonical_bytes(source_map); cpp_bytes = cpp.encode("utf-8")
    return {
        "schema_version": "direct-frontend-result-v1", "canonical_profile": "schuss-canonical-json-v1", "status": "success",
        "frontend": {"frontend_id": FRONTEND_ID, "version": FRONTEND_VERSION, "semantic_profile": profile_reference(), "observed_profile_hash": match.profile_hash},
        "input_plan_sha256": _sha256(_canonical_bytes(plan)), "module": module,
        "artifacts": [
            {"artifact_kind": "normalized-dsp", "media_type": "application/vnd.schuss.normalized-dsp+json", "byte_length": len(module_bytes), "byte_sha256": _sha256(module_bytes), "portable_locator": "direct/sha256/" + _sha256(module_bytes)},
            {"artifact_kind": "generated-cpp", "media_type": "text/x-c++src", "byte_length": len(cpp_bytes), "byte_sha256": _sha256(cpp_bytes), "portable_locator": "direct/sha256/" + _sha256(cpp_bytes) + ".cpp"},
            {"artifact_kind": "source-map", "media_type": "application/vnd.schuss.source-map+json", "byte_length": len(map_bytes), "byte_sha256": _sha256(map_bytes), "portable_locator": "direct/sha256/" + _sha256(map_bytes)},
        ],
        "generated_cpp": {"text": cpp, "byte_sha256": _sha256(cpp_bytes), "byte_length": len(cpp_bytes)}, "source_map": source_map,
        "semantic_goldens": task025_semantic_goldens(), "diagnostics": [],
        "evidence_levels": [{"level": level, "status": "passed" if level <= 4 else "not-run"} for level in range(1, 9)],
        "java_used": False, "legacy_boundary_patch_used": False, "ambient_discovery_used": False, "authoritative_records_mutated": False,
    }


__all__ = ["ProfileMatch", "profile_definition", "profile_reference", "semantic_profile_signature", "match_effects_profile", "lower_effects_profile"]
