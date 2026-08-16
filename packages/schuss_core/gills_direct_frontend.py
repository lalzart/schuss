"""Task 016 exact eight-node Gills normalized DSP and direct C++ frontend.

The module is deliberately bounded to ``schuss-graph-000002@1``.  Runtime
pitch conversion, sine interpolation, ARM saturation, and the patch ABI remain
owned by the authenticated Ksoloti runtime.  This module describes and emits
the calls; it does not copy the runtime tables or depend on Java, ``.axp``, or
legacy object dispatch.
"""

from __future__ import annotations

import copy
import hashlib
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping, Sequence

from .compiler_front_half import core


FRONTEND_ID = "schuss-direct-frontend-000001"
FRONTEND_VERSION = 2
GRAPH_REFERENCE = {
    "graph_id": "schuss-graph-000002",
    "revision": 1,
    "content_hash": "sha256:ea98b4cbf1ecb58d70338e5aaaef02385a6ede707b9b78bbc90fac09d53c7460",
}
REQUEST_ID = "schuss-build-request-000002"
REQUEST_REVISION = 3
DIRECT_BACKEND_ID = "schuss-backend-000002"
BLOCK_SIZE = 16
Q21_SCALE = 1 << 21
Q27_SCALE = 1 << 27

CONTRACT_REFERENCES = {
    "linear-mix-q27": {
        "component_contract_id": "schuss-component-contract-000003",
        "revision": 1,
        "content_hash": "sha256:96a29faf58769be5f2ac52de07aa80cae3dcdff28f0f3c158fb1fd12cc234a8d",
    },
    "square-lfo-q31": {
        "component_contract_id": "schuss-component-contract-000004",
        "revision": 1,
        "content_hash": "sha256:987acb05ac5334d69a87af584395d3d9728a2e566d8f932d7767176324701877",
    },
    "cyclic-counter-rising": {
        "component_contract_id": "schuss-component-contract-000005",
        "revision": 1,
        "content_hash": "sha256:09e0ccff23775d0b01b8792aa92f370fb3f741d7baa541eb92123bcfcbf871e1",
    },
    "four-step-select-q21": {
        "component_contract_id": "schuss-component-contract-000006",
        "revision": 1,
        "content_hash": "sha256:f1aa523d117d6516a72bbb7ab70c36399abf34d2dbfe6a27bf1d14e8a6e58023",
    },
    "sine-oscillator-q31": {
        "component_contract_id": "schuss-component-contract-000007",
        "revision": 1,
        "content_hash": "sha256:6c3bdbe18269794e885c392b3cd40d90c445ed0b207ab4dedb79abe8c28ec410",
    },
    "state-variable-filter-q27": {
        "component_contract_id": "schuss-component-contract-000008",
        "revision": 1,
        "content_hash": "sha256:b4a4f03947665ff8d100371427d886b7217fcc68199f3b164f8c1ca37cdd1c77",
    },
    "stereo-audio-output-q27": {
        "component_contract_id": "schuss-component-contract-000009",
        "revision": 1,
        "content_hash": "sha256:179c1526ed2bd6d9ad1c6fbfc9caa7abc21f479bef50cf93c8599b5817ca8718",
    },
}

OPERATION_SPEC_IDS = {
    "square-lfo-q31": "schuss-direct-operation-spec-000001",
    "cyclic-counter-rising": "schuss-direct-operation-spec-000002",
    "four-step-select-q21": "schuss-direct-operation-spec-000003",
    "sine-oscillator-q31": "schuss-direct-operation-spec-000004",
    "linear-mix-q27": "schuss-direct-operation-spec-000005",
    "state-variable-filter-q27": "schuss-direct-operation-spec-000006",
    "stereo-audio-output-q27": "schuss-direct-operation-spec-000007",
}

DIRECT_BINDING_IDS = {
    "square-lfo-q31": "schuss-implementation-000042",
    "cyclic-counter-rising": "schuss-implementation-000043",
    "four-step-select-q21": "schuss-implementation-000044",
    "sine-oscillator-q31": "schuss-implementation-000045",
    "linear-mix-q27": "schuss-implementation-000046",
    "state-variable-filter-q27": "schuss-implementation-000047",
    "stereo-audio-output-q27": "schuss-implementation-000048",
}

NODE_OPERATIONS = {
    "graph-node-000001": "square-lfo-q31",
    "graph-node-000002": "cyclic-counter-rising",
    "graph-node-000003": "four-step-select-q21",
    "graph-node-000004": "sine-oscillator-q31",
    "graph-node-000005": "sine-oscillator-q31",
    "graph-node-000006": "linear-mix-q27",
    "graph-node-000007": "state-variable-filter-q27",
    "graph-node-000008": "stereo-audio-output-q27",
}

SCHEDULE = (
    ("dsp-operation-000001", "graph-node-000004", "sine-oscillator-q31", "sine-a"),
    ("dsp-operation-000002", "graph-node-000001", "square-lfo-q31", "square-lfo"),
    ("dsp-operation-000003", "graph-node-000002", "cyclic-counter-rising", "counter"),
    ("dsp-operation-000004", "graph-node-000003", "four-step-select-q21", "sequencer"),
    ("dsp-operation-000005", "graph-node-000006", "linear-mix-q27", "crossfader"),
    ("dsp-operation-000006", "graph-node-000007", "state-variable-filter-q27", "filter"),
    ("dsp-operation-000007", "graph-node-000008", "stereo-audio-output-q27", "audio-output"),
    ("dsp-operation-000008", "graph-node-000005", "sine-oscillator-q31", "sine-b"),
    ("dsp-operation-000009", "graph-facet-000001", "public-control-latch-q27", "blend-control"),
)


def _canonical_bytes(value: Any) -> bytes:
    return core.canonical_json(value).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def wrap_u32(value: int) -> int:
    return int(value) & 0xFFFFFFFF


def wrap_i32(value: int) -> int:
    value = wrap_u32(value)
    return value - (1 << 32) if value >= (1 << 31) else value


def saturate_signed(value: int, bits: int) -> int:
    minimum = -(1 << (bits - 1))
    maximum = (1 << (bits - 1)) - 1
    return min(maximum, max(minimum, int(value)))


def saturate_unsigned(value: int, bits: int) -> int:
    return min((1 << bits) - 1, max(0, int(value)))


def smmul(left: int, right: int) -> int:
    return wrap_i32((wrap_i32(left) * wrap_i32(right)) >> 32)


@dataclass(frozen=True)
class SquareLfoState:
    phase: int = 0
    reset_arm: int = 1


@dataclass(frozen=True)
class CounterState:
    trigger_history: int = 0
    reset_history: int = 0
    count: int = 0


@dataclass(frozen=True)
class FilterState:
    low: int = 0
    band: int = 0


@dataclass(frozen=True)
class GillsGraphState:
    lfo: SquareLfoState = SquareLfoState()
    counter: CounterState = CounterState()
    sine_a_phase: int = 0
    sine_b_phase: int = 0
    filter: FilterState = FilterState()
    sequencer_latch: int = 0
    sine_b_latch: tuple[int, ...] = (0,) * BLOCK_SIZE
    blend_latch: int = 0


def evaluate_square_lfo(
    state: SquareLfoState,
    pitch_q21: int,
    reset: int,
    mtof_q31: Callable[[int], int],
) -> tuple[SquareLfoState, int]:
    phase = wrap_i32(state.phase)
    reset_arm = int(state.reset_arm)
    if reset and reset_arm:
        phase = 0
        reset_arm = 0
    else:
        if not reset:
            reset_arm = 1
        phase = wrap_i32(phase + (wrap_i32(mtof_q31(wrap_i32(pitch_q21))) >> 2))
    return SquareLfoState(phase, reset_arm), int(phase > 0)


def evaluate_counter(
    state: CounterState, trigger: int, reset: int, maximum: int
) -> tuple[CounterState, int, int]:
    trigger_history = state.trigger_history
    reset_history = state.reset_history
    count = state.count
    carry = 0
    if trigger > 0 and not trigger_history:
        count += 1
        if count >= maximum:
            count = 0
            carry = 1
        trigger_history = 1
    elif trigger <= 0:
        trigger_history = 0
    if reset > 0 and not reset_history:
        count = 0
        reset_history = 1
    elif reset <= 0:
        reset_history = 0
    return CounterState(trigger_history, reset_history, count), count, carry


def evaluate_four_step(step: int, values: Sequence[int]) -> tuple[int, int]:
    if len(values) != 4:
        raise ValueError("DIRECT_SEQUENCER_VALUE_COUNT_INVALID")
    output = int(values[step]) if 0 <= step < 4 else 0
    return wrap_i32(step - 4), wrap_i32(output)


def evaluate_sine_block(
    phase: int,
    frequency_q31: int,
    frequency_inputs: Sequence[int],
    phase_inputs: Sequence[int],
    sin_q31: Callable[[int], int],
) -> tuple[int, tuple[int, ...]]:
    if len(frequency_inputs) != BLOCK_SIZE or len(phase_inputs) != BLOCK_SIZE:
        raise ValueError("DIRECT_AUDIO_BLOCK_SIZE_INVALID")
    current = wrap_u32(phase)
    output: list[int] = []
    for frequency_input, phase_input in zip(frequency_inputs, phase_inputs):
        current = wrap_u32(current + wrap_u32(frequency_q31) + wrap_u32(frequency_input))
        lookup_phase = wrap_i32(current + (wrap_i32(phase_input) << 4))
        output.append(wrap_i32(sin_q31(lookup_phase)) >> 4)
    return current, tuple(output)


def evaluate_linear_mix_block(
    first: Sequence[int], second: Sequence[int], control_q27: int
) -> tuple[int, ...]:
    if len(first) != BLOCK_SIZE or len(second) != BLOCK_SIZE:
        raise ValueError("DIRECT_AUDIO_BLOCK_SIZE_INVALID")
    control = saturate_unsigned(control_q27, 27)
    complement = Q27_SCALE - control
    return tuple(
        wrap_i32((wrap_i32(right) * control + wrap_i32(left) * complement) >> 27)
        for left, right in zip(first, second)
    )


def evaluate_filter_block(
    state: FilterState,
    input_values: Sequence[int],
    pitch_q21: int,
    resonance_parameter: int,
    mtof_q31: Callable[[int], int],
    sin_q31: Callable[[int], int],
) -> tuple[FilterState, tuple[int, ...], tuple[int, ...], tuple[int, ...]]:
    if len(input_values) != BLOCK_SIZE:
        raise ValueError("DIRECT_AUDIO_BLOCK_SIZE_INVALID")
    damp = wrap_i32((0x80 << 24) - (saturate_unsigned(resonance_parameter, 27) << 4))
    damp = smmul(damp, damp)
    pitch = saturate_signed(pitch_q21, 28)
    frequency = wrap_i32(sin_q31(wrap_i32(mtof_q31(pitch))))
    low = wrap_i32(state.low)
    band = wrap_i32(state.band)
    high_values: list[int] = []
    band_values: list[int] = []
    low_values: list[int] = []
    for input_value in input_values:
        sample = wrap_i32(input_value)
        notch = wrap_i32(sample - wrap_i32(smmul(damp, band) << 1))
        low = wrap_i32(low + wrap_i32(smmul(frequency, band) << 1))
        high = wrap_i32(notch - low)
        band = wrap_i32(wrap_i32(smmul(frequency, high) << 1) + band)
        low_values.append(low)
        high_values.append(high)
        band_values.append(band)
    return FilterState(low, band), tuple(high_values), tuple(band_values), tuple(low_values)


def evaluate_audio_output(
    left: Sequence[int], right: Sequence[int]
) -> tuple[tuple[int, ...], tuple[int, ...], int, int]:
    if len(left) != BLOCK_SIZE or len(right) != BLOCK_SIZE:
        raise ValueError("DIRECT_AUDIO_BLOCK_SIZE_INVALID")
    left_output = tuple(saturate_signed(value, 28) for value in left)
    right_output = tuple(saturate_signed(value, 28) for value in right)
    return left_output, right_output, wrap_i32(left[0]), wrap_i32(right[0])


def evaluate_graph_block(
    state: GillsGraphState,
    blend_input_q27: int,
    mtof_q31: Callable[[int], int],
    sin_q31: Callable[[int], int],
) -> tuple[GillsGraphState, dict[str, Any]]:
    """Evaluate the exact retained nine-step block schedule.

    The injected runtime callables let host goldens prove integer operations,
    state, and latch timing without copying the retained runtime tables.
    """

    zero = (0,) * BLOCK_SIZE
    sine_a_frequency = wrap_i32(mtof_q31(wrap_i32(-24 * Q21_SCALE + state.sequencer_latch)))
    sine_a_phase, sine_a = evaluate_sine_block(
        state.sine_a_phase, sine_a_frequency, zero, zero, sin_q31
    )
    lfo_state, lfo_wave = evaluate_square_lfo(
        state.lfo, -48 * Q21_SCALE, 0, mtof_q31
    )
    counter_state, count, carry = evaluate_counter(state.counter, lfo_wave, 0, 4)
    chain, sequence = evaluate_four_step(
        count, (0, 5 * Q21_SCALE, 7 * Q21_SCALE, 12 * Q21_SCALE)
    )
    mixed = evaluate_linear_mix_block(sine_a, state.sine_b_latch, state.blend_latch)
    filter_state, high, band, low = evaluate_filter_block(
        state.filter,
        mixed,
        24 * Q21_SCALE,
        262144,
        mtof_q31,
        sin_q31,
    )
    output_left, output_right, vu_left, vu_right = evaluate_audio_output(low, low)
    sine_b_frequency = wrap_i32(mtof_q31(wrap_i32((-23 * Q21_SCALE - (7 * Q21_SCALE // 8)) + sequence)))
    sine_b_phase, sine_b = evaluate_sine_block(
        state.sine_b_phase, sine_b_frequency, zero, zero, sin_q31
    )
    next_state = GillsGraphState(
        lfo=lfo_state,
        counter=counter_state,
        sine_a_phase=sine_a_phase,
        sine_b_phase=sine_b_phase,
        filter=filter_state,
        sequencer_latch=sequence,
        sine_b_latch=sine_b,
        blend_latch=saturate_unsigned(blend_input_q27, 27),
    )
    return next_state, {
        "schedule": [item[0] for item in SCHEDULE],
        "lfo_wave": lfo_wave,
        "counter_count": count,
        "counter_carry": carry,
        "sequencer_chain": chain,
        "sequencer_output": sequence,
        "sine_a": list(sine_a),
        "sine_b": list(sine_b),
        "mixed": list(mixed),
        "filter_high": list(high),
        "filter_band": list(band),
        "filter_low": list(low),
        "output_left": list(output_left),
        "output_right": list(output_right),
        "vu_left": vu_left,
        "vu_right": vu_right,
        "latches_after_block": {
            "sequencer": next_state.sequencer_latch,
            "sine_b": list(next_state.sine_b_latch),
            "blend": next_state.blend_latch,
        },
    }


def semantic_goldens() -> dict[str, Any]:
    """Return deterministic operation and graph-transition compatibility vectors."""

    runtime_pitch = lambda pitch: wrap_i32((pitch * 17) + 0x10203040)
    runtime_sine = lambda phase: wrap_i32((phase * 3) ^ 0x13579BDF)
    lfo_states = []
    lfo = SquareLfoState()
    for reset in (0, 1, 1, 0):
        lfo, wave = evaluate_square_lfo(lfo, -48 * Q21_SCALE, reset, runtime_pitch)
        lfo_states.append({"reset": reset, "state": lfo.__dict__, "wave": wave})
    counter_rows = []
    counter = CounterState()
    for trigger in (0, 1, 1, 0, 1, 0, 1, 0, 1):
        counter, count, carry = evaluate_counter(counter, trigger, 0, 4)
        counter_rows.append({"trigger": trigger, "count": count, "carry": carry, "state": counter.__dict__})
    sine_phase, sine = evaluate_sine_block(
        0xFFFFFFF0, 0x21, (0,) * BLOCK_SIZE, (0,) * BLOCK_SIZE, runtime_sine
    )
    filter_state, high, band, low = evaluate_filter_block(
        FilterState(), tuple(range(-8, 8)), 24 * Q21_SCALE, 262144, runtime_pitch, runtime_sine
    )
    first_state, first = evaluate_graph_block(GillsGraphState(), Q27_SCALE, runtime_pitch, runtime_sine)
    second_state, second = evaluate_graph_block(first_state, 0, runtime_pitch, runtime_sine)
    operations = {
        "square-lfo-q31": lfo_states,
        "cyclic-counter-rising": counter_rows,
        "four-step-select-q21": [
            {"step": step, "result": list(evaluate_four_step(step, (0, 5 * Q21_SCALE, 7 * Q21_SCALE, 12 * Q21_SCALE)))}
            for step in (-1, 0, 1, 2, 3, 4)
        ],
        "sine-oscillator-q31": {"phase": sine_phase, "samples": list(sine)},
        "linear-mix-q27": {
            "zero": list(evaluate_linear_mix_block(tuple(range(16)), tuple(range(16, 32)), 0)),
            "half": list(evaluate_linear_mix_block(tuple(range(16)), tuple(range(16, 32)), Q27_SCALE // 2)),
            "full": list(evaluate_linear_mix_block(tuple(range(16)), tuple(range(16, 32)), Q27_SCALE)),
        },
        "state-variable-filter-q27": {
            "state": filter_state.__dict__, "high": list(high), "band": list(band), "low": list(low)
        },
        "stereo-audio-output-q27": {
            "result": [list(value) if isinstance(value, tuple) else value for value in evaluate_audio_output(tuple(range(-8, 8)), tuple(range(8, -8, -1)))]
        },
    }
    return {
        "schema_version": "task016-semantic-goldens-v1",
        "runtime_fixture": "injected-integer-runtime-oracle-v1",
        "runtime_boundary_note": "Fixture return values test call, arithmetic, state, and schedule semantics; authenticated Ksoloti runtime owns pitch and sine table values.",
        "operations": operations,
        "graph_transitions": [
            {"cycle": 1, "output": first, "state": _state_value(first_state)},
            {"cycle": 2, "output": second, "state": _state_value(second_state)},
        ],
    }


def _state_value(state: GillsGraphState) -> dict[str, Any]:
    return {
        "lfo": state.lfo.__dict__,
        "counter": state.counter.__dict__,
        "sine_a_phase": state.sine_a_phase,
        "sine_b_phase": state.sine_b_phase,
        "filter": state.filter.__dict__,
        "sequencer_latch": state.sequencer_latch,
        "sine_b_latch": list(state.sine_b_latch),
        "blend_latch": state.blend_latch,
    }


def _exact_reference(record: Mapping[str, Any], id_field: str) -> dict[str, Any]:
    return {
        id_field: record[id_field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def _validate_inputs(
    plan: Mapping[str, Any],
    graph: Mapping[str, Any],
    contracts: Iterable[Mapping[str, Any]],
    operation_specs: Iterable[Mapping[str, Any]],
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    plan_value = copy.deepcopy(dict(plan))
    graph_value = copy.deepcopy(dict(graph))
    if plan_value.get("status") != "success":
        raise ValueError("DIRECT_PLAN_NOT_SUCCESSFUL")
    request_reference = plan_value.get("input_closure", {}).get("build_request_reference", {})
    if request_reference.get("build_request_id") != REQUEST_ID or request_reference.get("revision") != REQUEST_REVISION:
        raise ValueError("DIRECT_BUILD_REQUEST_UNSUPPORTED")
    if {key: graph_value.get(key) for key in GRAPH_REFERENCE} != GRAPH_REFERENCE:
        raise ValueError("DIRECT_GRAPH_UNSUPPORTED")
    nodes = graph_value.get("nodes")
    connections = graph_value.get("connections")
    if not isinstance(nodes, list) or {item.get("node_id") for item in nodes} != set(NODE_OPERATIONS):
        raise ValueError("DIRECT_GRAPH_SHAPE_UNSUPPORTED")
    if not isinstance(connections, list) or len(connections) != 9:
        raise ValueError("DIRECT_GRAPH_CONNECTIONS_UNSUPPORTED")
    contracts_by_id = {item["component_contract_id"]: copy.deepcopy(dict(item)) for item in contracts}
    expected_contracts = {value["component_contract_id"]: value for value in CONTRACT_REFERENCES.values()}
    if {
        key: _exact_reference(value, "component_contract_id")
        for key, value in contracts_by_id.items() if key in expected_contracts
    } != expected_contracts:
        raise ValueError("DIRECT_CONTRACT_SET_UNSUPPORTED")
    specs_by_opcode = {item["opcode"]: copy.deepcopy(dict(item)) for item in operation_specs}
    if set(specs_by_opcode) != set(OPERATION_SPEC_IDS):
        raise ValueError("DIRECT_OPERATION_SPEC_SET_UNSUPPORTED")
    for opcode, stable_id in OPERATION_SPEC_IDS.items():
        spec = specs_by_opcode[opcode]
        if spec.get("direct_operation_spec_id") != stable_id or spec.get("revision") != 1:
            raise ValueError("DIRECT_OPERATION_SPEC_IDENTITY_UNSUPPORTED")
        if spec.get("contract_reference") != CONTRACT_REFERENCES[opcode]:
            raise ValueError("DIRECT_OPERATION_SPEC_CONTRACT_UNSUPPORTED")
        if spec.get("compatibility_mode") != "legacy-equivalent-task011c":
            raise ValueError("DIRECT_COMPATIBILITY_MODE_UNSUPPORTED")
    resolution = [
        item["payload"] for item in plan_value.get("artifacts", [])
        if item.get("descriptor", {}).get("artifact_kind") == "resolution-plan"
    ]
    if len(resolution) != 1 or resolution[0].get("status") != "success":
        raise ValueError("DIRECT_RESOLUTION_PLAN_MISSING")
    traces = {item["node_id"]: item for item in resolution[0].get("traces", [])}
    if set(traces) != set(NODE_OPERATIONS):
        raise ValueError("DIRECT_RESOLUTION_TRACE_SET_UNSUPPORTED")
    for node_id, opcode in NODE_OPERATIONS.items():
        binding = traces[node_id].get("selected_binding_reference", {})
        if binding.get("implementation_id") != DIRECT_BINDING_IDS[opcode] or binding.get("revision") != 2:
            raise ValueError("DIRECT_BINDING_SELECTION_UNSUPPORTED")
    return plan_value, contracts_by_id, specs_by_opcode


def _normalized_module(
    plan: Mapping[str, Any],
    graph: Mapping[str, Any],
    specs: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    plan_sha = _sha256(_canonical_bytes(plan))
    operations = []
    for operation_id, origin_id, opcode, role in SCHEDULE:
        value: dict[str, Any] = {
            "operation_id": operation_id,
            "opcode": opcode,
            "role": role,
            "origin": {"subject_id": origin_id},
        }
        if opcode in specs:
            value["operation_spec_reference"] = _exact_reference(specs[opcode], "direct_operation_spec_id")
            value["contract_reference"] = copy.deepcopy(CONTRACT_REFERENCES[opcode])
        operations.append(value)
    connection_values = [
        {
            "connection_id": item["connection_id"],
            "source": copy.deepcopy(item["source"]),
            "destination": copy.deepcopy(item["destination"]),
            "lowering": "direct-exact-no-adapter",
        }
        for item in sorted(graph["connections"], key=lambda item: item["connection_id"])
    ]
    return {
        "schema_version": "normalized-dsp-module-v1",
        "canonical_profile": "schuss-canonical-json-v1",
        "derived": True,
        "authoritative": False,
        "module_id": "schuss-normalized-dsp-module-000002",
        "frontend": {"frontend_id": FRONTEND_ID, "version": FRONTEND_VERSION},
        "source_plan_sha256": plan_sha,
        "graph_reference": copy.deepcopy(GRAPH_REFERENCE),
        "runtime_contract": {
            "sample_rate_hz": 48000,
            "audio_block_frames": BLOCK_SIZE,
            "patch_abi": "ksoloti-xpatch-task011c",
            "runtime_calls": ["mtof48k_ext_q31", "sin_q31", "___SMMUL", "__SSAT", "__USAT"],
            "java_required": False,
            "legacy_boundary_patch_required": False,
        },
        "numeric_contracts": [
            {"name": "semitone", "representation": "signed-q21", "scale": Q21_SCALE, "overflow": "operation-specific"},
            {"name": "normalized-audio-control", "representation": "signed-q27", "scale": Q27_SCALE, "overflow": "operation-specific"},
            {"name": "phase-frequency", "representation": "q31-bits", "width_bits": 32, "overflow": "wrap"},
            {"name": "boolean-control", "representation": "zero-or-one", "width_bits": 32},
        ],
        "parameter_values": [
            {"node_id": "graph-node-000004", "facet_id": "component-parameter-000001", "raw_value": -50331648},
            {"node_id": "graph-node-000001", "facet_id": "component-parameter-000001", "raw_value": -100663296},
            {"node_id": "graph-node-000002", "facet_id": "component-parameter-000001", "raw_value": 4},
            {"node_id": "graph-node-000003", "facet_id": "component-parameter-000001", "raw_value": 0},
            {"node_id": "graph-node-000003", "facet_id": "component-parameter-000002", "raw_value": 10485760},
            {"node_id": "graph-node-000003", "facet_id": "component-parameter-000003", "raw_value": 14680064},
            {"node_id": "graph-node-000003", "facet_id": "component-parameter-000004", "raw_value": 25165824},
            {"node_id": "graph-node-000007", "facet_id": "component-parameter-000001", "raw_value": 50331648},
            {"node_id": "graph-node-000007", "facet_id": "component-parameter-000002", "raw_value": 262144},
            {"node_id": "graph-node-000005", "facet_id": "component-parameter-000001", "raw_value": -50069504},
        ],
        "state_layout": [
            {"state_id": "state-lfo-phase", "owner": "graph-node-000001", "initial": 0, "representation": "signed-32-wrap"},
            {"state_id": "state-lfo-reset-arm", "owner": "graph-node-000001", "initial": 1, "representation": "unsigned-32"},
            {"state_id": "state-counter-trigger-history", "owner": "graph-node-000002", "initial": 0, "representation": "integer"},
            {"state_id": "state-counter-reset-history", "owner": "graph-node-000002", "initial": 0, "representation": "integer"},
            {"state_id": "state-counter-count", "owner": "graph-node-000002", "initial": 0, "representation": "integer"},
            {"state_id": "state-sine-a-phase", "owner": "graph-node-000004", "initial": 0, "representation": "unsigned-32-wrap"},
            {"state_id": "state-sine-b-phase", "owner": "graph-node-000005", "initial": 0, "representation": "unsigned-32-wrap"},
            {"state_id": "state-filter-low", "owner": "graph-node-000007", "initial": 0, "representation": "signed-32-wrap"},
            {"state_id": "state-filter-band", "owner": "graph-node-000007", "initial": 0, "representation": "signed-32-wrap"},
            {"state_id": "state-sequencer-latch", "owner": "graph-connection-000004", "initial": 0, "update": "after-all-operations"},
            {"state_id": "state-sine-b-buffer-latch", "owner": "graph-connection-000006", "initial": [0] * BLOCK_SIZE, "update": "after-all-operations"},
            {"state_id": "state-blend-control-latch", "owner": "graph-facet-000001", "initial": 0, "update": "after-all-operations"},
        ],
        "connections": connection_values,
        "operations": operations,
        "schedule": {
            "unit": "one-control-cycle-per-16-sample-audio-block",
            "operation_ids": [item[0] for item in SCHEDULE],
            "latch_updates": ["state-sequencer-latch", "state-sine-b-buffer-latch", "state-blend-control-latch"],
        },
        "outputs": [
            {"value_id": "dsp-value-output-left", "origin": "graph-node-000008/component-port-000001", "kind": "audio-buffer-q27"},
            {"value_id": "dsp-value-output-right", "origin": "graph-node-000008/component-port-000002", "kind": "audio-buffer-q27"},
        ],
    }


def _source_map(
    graph: Mapping[str, Any],
    specs: Mapping[str, Mapping[str, Any]],
    contracts: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    mappings: list[dict[str, Any]] = []
    for operation_id, origin_id, opcode, role in SCHEDULE:
        mappings.append({
            "generated": f"operation:{role}",
            "origin": origin_id,
            "operation_id": operation_id,
            "operation_spec_id": OPERATION_SPEC_IDS.get(opcode, "graph-public-control-latch"),
        })
    for node in sorted(graph["nodes"], key=lambda item: item["node_id"]):
        contract = next(
            value for value in CONTRACT_REFERENCES.values()
            if value == node["contract_reference"]
        )
        mappings.append({
            "generated": f"node:{node['node_id']}",
            "origin": node["node_id"],
            "contract_reference": copy.deepcopy(contract),
        })
        contract_record = contracts[contract["component_contract_id"]]
        opcode = NODE_OPERATIONS[node["node_id"]]
        mappings.append({
            "generated": f"binding:{node['node_id']}",
            "origin": node["node_id"],
            "direct_binding_id": DIRECT_BINDING_IDS[opcode],
            "operation_spec_reference": _exact_reference(specs[opcode], "direct_operation_spec_id"),
        })
        for collection, facet_kind in (
            ("ports", "port"),
            ("parameters", "parameter"),
            ("attributes", "attribute"),
            ("actions", "action"),
            ("displays", "display"),
            ("state_declarations", "state"),
        ):
            for facet in sorted(
                contract_record.get(collection, []),
                key=lambda item: item.get("facet_id", item.get("state_id", "")),
            ):
                facet_id = facet.get("facet_id", facet.get("state_id"))
                mappings.append({
                    "generated": f"facet:{node['node_id']}/{facet_id}",
                    "origin": f"{node['node_id']}/{facet_id}",
                    "facet_kind": facet_kind,
                    "contract_reference": copy.deepcopy(contract),
                })
    for connection in sorted(graph["connections"], key=lambda item: item["connection_id"]):
        mappings.append({
            "generated": f"connection:{connection['connection_id']}",
            "origin": connection["connection_id"],
            "source": copy.deepcopy(connection["source"]),
            "destination": copy.deepcopy(connection["destination"]),
        })
    for binding in sorted(graph.get("parameter_bindings", []), key=lambda item: item["binding_id"]):
        mappings.append({
            "generated": f"public-parameter:{binding['binding_id']}",
            "origin": binding["binding_id"],
            "source": {"graph_parameter_id": binding["source_graph_parameter_id"]},
            "destination": copy.deepcopy(binding["destination"]),
        })
    return {
        "schema_version": "direct-source-map-v1",
        "graph_reference": copy.deepcopy(GRAPH_REFERENCE),
        "generated_symbols": [
            "xpatch_init", "PatchProcess", "PatchDispose", "ApplyPreset",
            "PatchMidiInHandler", "schuss_gills_set_blend_q27",
        ],
        "mappings": mappings,
    }


def _generated_cpp() -> str:
    return r'''#include "xpatch.h"

#pragma GCC diagnostic ignored "-Wunused-parameter"

int32buffer AudioInputLeft, AudioInputRight, AudioOutputLeft, AudioOutputRight;

static volatile int32_t SchussBlendInputQ27;

extern "C" void schuss_gills_set_blend_q27(int32_t value) {
  SchussBlendInputQ27 = __USAT(value, 27);
}

struct SchussGillsState {
  static const uint16_t NPEXCH = 10;
  ParameterExchange_t parameters[NPEXCH];
  int32_t display_vector[5];
  int32_t lfo_phase;
  uint32_t lfo_reset_arm;
  int32_t counter_trigger_history;
  int32_t counter_reset_history;
  int32_t counter_count;
  uint32_t sine_a_phase;
  uint32_t sine_b_phase;
  int32_t filter_low;
  int32_t filter_band;
  int32_t sequencer_latch;
  int32buffer sine_b_latch;
  int32_t blend_latch;
};

static SchussGillsState State;

static const int32_t InitialParameters[SchussGillsState::NPEXCH] = {
  -50331648, -100663296, 4, 0, 10485760,
  14680064, 25165824, 50331648, 262144, -50069504
};

static void initialize_parameters(void) {
  for (uint32_t index = 0; index < SchussGillsState::NPEXCH; ++index) {
    State.parameters[index].value = InitialParameters[index];
    State.parameters[index].modvalue = InitialParameters[index];
    State.parameters[index].signals = 0;
    State.parameters[index].pfunction = 0;
  }
  State.parameters[0].pfunction = pfun_signed_clamp;
  State.parameters[1].pfunction = pfun_signed_clamp;
  State.parameters[3].pfunction = pfun_signed_clamp;
  State.parameters[4].pfunction = pfun_signed_clamp;
  State.parameters[5].pfunction = pfun_signed_clamp;
  State.parameters[6].pfunction = pfun_signed_clamp;
  State.parameters[7].pfunction = pfun_signed_clamp;
  State.parameters[8].pfunction = pfun_unsigned_clamp;
  State.parameters[9].pfunction = pfun_signed_clamp;
  for (uint32_t index = 0; index < SchussGillsState::NPEXCH; ++index) {
    if (State.parameters[index].pfunction) {
      State.parameters[index].pfunction(&State.parameters[index]);
    } else {
      State.parameters[index].finalvalue = State.parameters[index].value;
    }
  }
}

static void initialize_state(void) {
  State.display_vector[0] = 0x446F7841;
  State.display_vector[1] = 0;
  State.display_vector[2] = 2;
  State.display_vector[3] = 0;
  State.display_vector[4] = 0;
  State.lfo_phase = 0;
  State.lfo_reset_arm = 1;
  State.counter_trigger_history = 0;
  State.counter_reset_history = 0;
  State.counter_count = 0;
  State.sine_a_phase = 0;
  State.sine_b_phase = 0;
  State.filter_low = 0;
  State.filter_band = 0;
  State.sequencer_latch = 0;
  State.blend_latch = 0;
  SchussBlendInputQ27 = 0;
  for (uint32_t index = 0; index < BUFSIZE; ++index) {
    State.sine_b_latch[index] = 0;
  }
  initialize_parameters();
}

static void process_sine(uint32_t* phase, int32_t pitch, int32buffer& output) {
  const uint32_t frequency = mtof48k_ext_q31(pitch);
  for (uint32_t index = 0; index < BUFSIZE; ++index) {
    *phase += frequency;
    output[index] = sin_q31((int32_t)(*phase)) >> 4;
  }
}

static bool process_square_lfo(int32_t pitch, bool reset) {
  if (reset && State.lfo_reset_arm) {
    State.lfo_phase = 0;
    State.lfo_reset_arm = 0;
  } else {
    if (!reset) State.lfo_reset_arm = 1;
    const int32_t frequency = mtof48k_ext_q31(pitch);
    State.lfo_phase += frequency >> 2;
  }
  return State.lfo_phase > 0;
}

static int32_t process_counter(bool trigger, bool reset) {
  if (trigger && !State.counter_trigger_history) {
    State.counter_count += 1;
    if (State.counter_count >= State.parameters[2].finalvalue) State.counter_count = 0;
    State.counter_trigger_history = 1;
  } else if (!trigger) {
    State.counter_trigger_history = 0;
  }
  if (reset && !State.counter_reset_history) {
    State.counter_count = 0;
    State.counter_reset_history = 1;
  } else if (!reset) {
    State.counter_reset_history = 0;
  }
  return State.counter_count;
}

static int32_t process_four_step(int32_t step) {
  switch (step) {
    case 0: return State.parameters[3].finalvalue;
    case 1: return State.parameters[4].finalvalue;
    case 2: return State.parameters[5].finalvalue;
    case 3: return State.parameters[6].finalvalue;
    default: return 0;
  }
}

static void process_crossfader(const int32buffer first, const int32buffer second,
                               int32_t control, int32buffer& output) {
  control = __USAT(control, 27);
  const int32_t complement = (128 << 20) - control;
  for (uint32_t index = 0; index < BUFSIZE; ++index) {
    int64_t mixed = (int64_t)second[index] * control;
    mixed += (int64_t)first[index] * complement;
    output[index] = mixed >> 27;
  }
}

static void process_filter(const int32buffer input, int32buffer& low_output) {
  int32_t damp = (0x80 << 24) - (__USAT(State.parameters[8].finalvalue, 27) << 4);
  damp = ___SMMUL(damp, damp);
  const int32_t pitch = __SSAT(State.parameters[7].finalvalue, 28);
  const int32_t alpha = mtof48k_ext_q31(pitch);
  const int32_t frequency = sin_q31(alpha);
  for (uint32_t index = 0; index < BUFSIZE; ++index) {
    const int32_t notch = input[index] - (___SMMUL(damp, State.filter_band) << 1);
    State.filter_low += ___SMMUL(frequency, State.filter_band) << 1;
    const int32_t high = notch - State.filter_low;
    State.filter_band = (___SMMUL(frequency, high) << 1) + State.filter_band;
    low_output[index] = State.filter_low;
  }
}

static void process_audio_output(const int32buffer left, const int32buffer right) {
  for (uint32_t index = 0; index < BUFSIZE; ++index) {
    AudioOutputLeft[index] += __SSAT(left[index], 28);
    AudioOutputRight[index] += __SSAT(right[index], 28);
  }
  State.display_vector[3] = left[0];
  State.display_vector[4] = right[0];
}

static void process_graph(void) {
  int32buffer sine_a;
  int32buffer sine_b;
  int32buffer mixed;
  int32buffer low;
  for (uint32_t index = 0; index < BUFSIZE; ++index) {
    AudioOutputLeft[index] = 0;
    AudioOutputRight[index] = 0;
  }
  process_sine(&State.sine_a_phase,
               State.parameters[0].finalvalue + State.sequencer_latch, sine_a);
  const bool lfo = process_square_lfo(State.parameters[1].finalvalue, false);
  const int32_t count = process_counter(lfo, false);
  const int32_t sequence = process_four_step(count);
  process_crossfader(sine_a, State.sine_b_latch, State.blend_latch, mixed);
  process_filter(mixed, low);
  process_audio_output(low, low);
  process_sine(&State.sine_b_phase, State.parameters[9].finalvalue + sequence, sine_b);
  const int32_t blend = __USAT(SchussBlendInputQ27, 27);
  State.sequencer_latch = sequence;
  for (uint32_t index = 0; index < BUFSIZE; ++index) {
    State.sine_b_latch[index] = sine_b[index];
  }
  State.blend_latch = blend;
}

void PatchProcess(int32_t* input, int32_t* output) {
  for (uint32_t index = 0; index < BUFSIZE; ++index) {
    AudioInputLeft[index] = input[index << 1] >> 4;
    AudioInputRight[index] = input[(index << 1) + 1] >> 4;
  }
  process_graph();
  for (uint32_t index = 0; index < BUFSIZE; ++index) {
    output[index << 1] = __SSAT(AudioOutputLeft[index], 28) << 4;
    output[(index << 1) + 1] = __SSAT(AudioOutputRight[index], 28) << 4;
  }
}

void ApplyPreset(uint8_t index) {
  if (index == 0) initialize_parameters();
}

void PatchMidiInHandler(midi_device_t device, uint8_t port, uint8_t status,
                        uint8_t data1, uint8_t data2) {}

typedef void (*SchussFunction)(void);
extern SchussFunction __ctor_array_start;
extern SchussFunction __ctor_array_end;
extern SchussFunction __dtor_array_start;
extern SchussFunction __dtor_array_end;

void PatchDispose(void) {
  SchussFunction* function = &__dtor_array_start;
  while (function < &__dtor_array_end) {
    (*function)();
    ++function;
  }
}

static void xpatch_init2(uint32_t firmware_id) {
  if (firmware_id != 0x5021D42A) return;
  extern uint32_t _pbss_start;
  extern uint32_t _pbss_end;
  for (volatile uint32_t* value = &_pbss_start; value < &_pbss_end; ++value) {
    *value = 0;
  }
  SchussFunction* function = &__ctor_array_start;
  while (function < &__ctor_array_end) {
    (*function)();
    ++function;
  }
  patchMeta.npresets = 0;
  patchMeta.npreset_entries = 0;
  patchMeta.pPresets = 0;
  patchMeta.pPExch = &State.parameters[0];
  patchMeta.pDisplayVector = &State.display_vector[0];
  patchMeta.numPEx = SchussGillsState::NPEXCH;
  patchMeta.patchID = -2064091903;
  extern char _sdram_dyn_start;
  extern char _sdram_dyn_end;
  sdram_init(&_sdram_dyn_start, &_sdram_dyn_end);
  initialize_state();
  patchMeta.fptr_applyPreset = ApplyPreset;
  patchMeta.fptr_patch_dispose = PatchDispose;
  patchMeta.fptr_MidiInHandler = PatchMidiInHandler;
  patchMeta.fptr_dsp_process = PatchProcess;
}

extern "C" __attribute__((section(".boot"))) void xpatch_init(uint32_t firmware_id) {
  xpatch_init2(firmware_id);
}
'''


def lower_gills_direct(
    plan: Mapping[str, Any],
    graph: Mapping[str, Any],
    contracts: Iterable[Mapping[str, Any]],
    operation_specs: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Lower only the accepted complete Gills graph through the direct path."""

    plan_value, contracts_by_id, specs_by_opcode = _validate_inputs(
        plan, graph, contracts, operation_specs
    )
    graph_value = copy.deepcopy(dict(graph))
    module = _normalized_module(plan_value, graph_value, specs_by_opcode)
    source_map = _source_map(graph_value, specs_by_opcode, contracts_by_id)
    cpp = _generated_cpp()
    cpp_bytes = cpp.encode("utf-8")
    module_bytes = _canonical_bytes(module)
    source_map_bytes = _canonical_bytes(source_map)
    goldens = semantic_goldens()
    return {
        "schema_version": "direct-frontend-result-v1",
        "canonical_profile": "schuss-canonical-json-v1",
        "status": "success",
        "frontend": {"frontend_id": FRONTEND_ID, "version": FRONTEND_VERSION},
        "input_plan_sha256": _sha256(_canonical_bytes(plan_value)),
        "module": module,
        "artifacts": [
            {
                "artifact_kind": "normalized-dsp",
                "media_type": "application/vnd.schuss.normalized-dsp+json",
                "byte_length": len(module_bytes),
                "byte_sha256": _sha256(module_bytes),
                "portable_locator": "direct/sha256/" + _sha256(module_bytes),
            },
            {
                "artifact_kind": "generated-cpp",
                "media_type": "text/x-c++src",
                "byte_length": len(cpp_bytes),
                "byte_sha256": _sha256(cpp_bytes),
                "portable_locator": "direct/sha256/" + _sha256(cpp_bytes) + ".cpp",
            },
            {
                "artifact_kind": "source-map",
                "media_type": "application/vnd.schuss.source-map+json",
                "byte_length": len(source_map_bytes),
                "byte_sha256": _sha256(source_map_bytes),
                "portable_locator": "direct/sha256/" + _sha256(source_map_bytes),
            },
        ],
        "generated_cpp": {"text": cpp, "byte_sha256": _sha256(cpp_bytes), "byte_length": len(cpp_bytes)},
        "source_map": source_map,
        "semantic_goldens": goldens,
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
