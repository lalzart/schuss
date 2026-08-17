"""Pure legacy-equivalent semantics for the safe Task 025 operation tranche.

This module models only five authenticated Ksoloti object seams.  It performs
no source discovery, lowering, build execution, or device action.  Reverb is
deliberately absent because its pinned allocation contract is inconsistent.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Callable, Sequence


BLOCK_SIZE = 16
Q27_ONE = 1 << 27
I32_MIN = -(1 << 31)
I32_MAX = (1 << 31) - 1
U32_MASK = (1 << 32) - 1

OPERATION_SPEC_IDS = {
    "blep-saw-q27": "schuss-direct-operation-spec-000008",
    "blep-pwm-q27": "schuss-direct-operation-spec-000009",
    "exponential-smooth-q27": "schuss-direct-operation-spec-000010",
    "soft-clip-q27": "schuss-direct-operation-spec-000011",
    "interpolated-vca-q27": "schuss-direct-operation-spec-000013",
}

DIRECT_BINDING_IDS = {
    "blep-saw-q27": "schuss-implementation-000090",
    "blep-pwm-q27": "schuss-implementation-000091",
    "exponential-smooth-q27": "schuss-implementation-000092",
    "soft-clip-q27": "schuss-implementation-000093",
    "interpolated-vca-q27": "schuss-implementation-000095",
}

SOURCE_BINDING_IDS = {
    "blep-saw-q27": "schuss-implementation-000051",
    "blep-pwm-q27": "schuss-implementation-000052",
    "exponential-smooth-q27": "schuss-implementation-000054",
    "soft-clip-q27": "schuss-implementation-000055",
    "interpolated-vca-q27": "schuss-implementation-000059",
}


def wrap_u32(value: int) -> int:
    return value & U32_MASK


def wrap_i32(value: int) -> int:
    value &= U32_MASK
    return value if value <= I32_MAX else value - (1 << 32)


def c_div_signed(numerator: int, denominator: int) -> int:
    """C99 integer division, which truncates toward zero."""

    if denominator == 0:
        raise ValueError("EFFECTS_DIRECT_INTEGER_DIVISION_BY_ZERO")
    quotient = abs(numerator) // abs(denominator)
    return -quotient if (numerator < 0) != (denominator < 0) else quotient


def saturate_signed(value: int, bits: int) -> int:
    minimum = -(1 << (bits - 1))
    maximum = (1 << (bits - 1)) - 1
    return min(maximum, max(minimum, value))


def smmul(left: int, right: int) -> int:
    """ARM signed most-significant-word multiply."""

    product = wrap_i32(left) * wrap_i32(right)
    return wrap_i32(product >> 32)


def smmla(left: int, right: int, accumulator: int) -> int:
    return wrap_i32(smmul(left, right) + wrap_i32(accumulator))


@dataclass
class BlepSawState:
    phase: int = 0
    voice_indexes: list[int] = field(default_factory=list)
    next_voice: int = 0


@dataclass
class BlepPwmState:
    phase: int = 0
    voice_indexes: list[int] = field(default_factory=list)
    next_voice: int = 0
    pulse_width_phase: int = 0


@dataclass
class SmoothState:
    value: int = 0


@dataclass
class VcaState:
    previous_gain: int = 0


@dataclass
class EffectsSemanticState:
    saw: BlepSawState = field(default_factory=BlepSawState)
    pwm: BlepPwmState = field(default_factory=BlepPwmState)
    smooth: SmoothState = field(default_factory=SmoothState)
    vca: VcaState = field(default_factory=VcaState)


def _require_blep_table(table: Sequence[int]) -> int:
    if len(table) < 65 or any(value < -(1 << 15) or value > (1 << 15) - 1 for value in table):
        raise ValueError("EFFECTS_DIRECT_BLEP_TABLE_INVALID")
    return len(table) - 1


def _initialize_voices(indexes: list[int], count: int, last: int) -> None:
    if not indexes:
        indexes.extend([last] * count)
    if len(indexes) != count or any(value < 0 or value > last for value in indexes):
        raise ValueError("EFFECTS_DIRECT_BLEP_STATE_INVALID")


def evaluate_blep_saw_block(
    state: BlepSawState,
    pitch: int,
    *,
    pitch_to_frequency: Callable[[int], int],
    blep_table: Sequence[int],
) -> list[int]:
    """Evaluate the exact 16-sample `osc/saw` control block."""

    last = _require_blep_table(blep_table)
    _initialize_voices(state.voice_indexes, 4, last)
    frequency = wrap_i32(pitch_to_frequency(wrap_i32(pitch)))
    output: list[int] = []
    for _ in range(BLOCK_SIZE):
        previous = wrap_i32(state.phase)
        state.phase = wrap_i32(previous + frequency)
        if state.phase > 0 and not previous > 0:
            state.next_voice = (state.next_voice + 1) & 3
            denominator = frequency >> 6
            index = c_div_signed(state.phase, denominator)
            if index < 0 or index > last:
                raise ValueError("EFFECTS_DIRECT_BLEP_INDEX_INVALID")
            state.voice_indexes[state.next_voice] = index
        total = 0
        for voice, index in enumerate(state.voice_indexes):
            total += int(blep_table[index])
            state.voice_indexes[voice] = min(last, index + 64)
        total = (16384 * 4) - total - 8192
        ramp = wrap_u32(state.phase) >> 5
        output.append(wrap_i32(ramp + (total << 13)))
    return output


def _pwm_index(phase_delta: int, frequency: int, last: int) -> int:
    frequency = wrap_u32(frequency)
    if frequency == 0:
        return 0
    if frequency >> 24:
        value = wrap_u32(phase_delta) // (frequency >> 6)
    else:
        value = wrap_u32(wrap_i32(phase_delta << 6)) // frequency
    if value > last:
        raise ValueError("EFFECTS_DIRECT_BLEP_INDEX_INVALID")
    return value


def evaluate_blep_pwm_block(
    state: BlepPwmState,
    pitch: int,
    pulse_width: int,
    *,
    pitch_to_frequency: Callable[[int], int],
    blep_table: Sequence[int],
) -> list[int]:
    """Evaluate the exact 16-sample `osc/pwm` control block."""

    last = _require_blep_table(blep_table)
    _initialize_voices(state.voice_indexes, 8, last)
    frequency = wrap_u32(pitch_to_frequency(wrap_i32(pitch)))
    output: list[int] = []

    def phase_crossing(previous: int) -> None:
        state.next_voice = (state.next_voice + 1) & 7
        state.voice_indexes[state.next_voice] = _pwm_index(state.phase, frequency, last)
        state.pulse_width_phase = wrap_i32((Q27_ONE + wrap_i32(pulse_width)) << 4)

    def width_crossing(previous: int) -> None:
        state.next_voice = (state.next_voice + 1) & 7
        delta = wrap_i32(state.phase - state.pulse_width_phase)
        state.voice_indexes[state.next_voice] = _pwm_index(delta, frequency, last)

    for _ in range(BLOCK_SIZE):
        previous = wrap_i32(state.phase)
        state.phase = wrap_i32(previous + frequency)
        current_delta = wrap_i32(state.phase - state.pulse_width_phase)
        previous_delta = wrap_i32(previous - state.pulse_width_phase)
        phase_crossed = state.phase > 0 and not previous > 0
        width_crossed = current_delta > 0 and not previous_delta > 0
        if state.phase >= current_delta:
            if phase_crossed:
                phase_crossing(previous)
            if width_crossed:
                width_crossing(previous)
        else:
            if width_crossed:
                width_crossing(previous)
            if phase_crossed:
                phase_crossing(previous)
        total = 0
        for voice, index in enumerate(state.voice_indexes):
            value = int(blep_table[index])
            total = total + value if voice & 1 else total - value
            state.voice_indexes[voice] = min(last, index + 64)
        polarity = ((((state.next_voice + 1) & 1) << 1) - 1) << 13
        total = wrap_i32(total - polarity)
        output.append(wrap_i32(total << 13))
    return output


def evaluate_exponential_smooth(
    state: SmoothState, input_value: int, time_value: int
) -> int:
    coefficient = wrap_i32((-(1 << 26)) + (wrap_i32(time_value) >> 1))
    difference = wrap_i32(state.value - wrap_i32(input_value))
    state.value = smmla(difference, coefficient, state.value)
    return state.value


def evaluate_soft_clip_sample(input_value: int) -> int:
    saturated = saturate_signed(wrap_i32(input_value), 28)
    q31 = wrap_i32(saturated << 3)
    cubic = smmul(q31, smmul(q31, q31))
    return wrap_i32(saturated + (saturated >> 1) - cubic)


def evaluate_soft_clip_block(values: Sequence[int]) -> list[int]:
    if len(values) != BLOCK_SIZE:
        raise ValueError("EFFECTS_DIRECT_AUDIO_BLOCK_SIZE_INVALID")
    return [evaluate_soft_clip_sample(value) for value in values]


def evaluate_vca_block(
    state: VcaState, gain: int, audio: Sequence[int]
) -> list[int]:
    if len(audio) != BLOCK_SIZE:
        raise ValueError("EFFECTS_DIRECT_AUDIO_BLOCK_SIZE_INVALID")
    gain = wrap_i32(gain)
    step = wrap_i32(gain - state.previous_gain) >> 4
    interpolated = wrap_i32(state.previous_gain)
    state.previous_gain = gain
    output = []
    for sample in audio:
        output.append(wrap_i32(smmul(wrap_i32(sample), interpolated) << 5))
        interpolated = wrap_i32(interpolated + step)
    return output


def _state_value(state: EffectsSemanticState) -> dict[str, object]:
    return {
        "saw": {
            "phase": state.saw.phase,
            "voice_indexes": list(state.saw.voice_indexes),
            "next_voice": state.saw.next_voice,
        },
        "pwm": {
            "phase": state.pwm.phase,
            "voice_indexes": list(state.pwm.voice_indexes),
            "next_voice": state.pwm.next_voice,
            "pulse_width_phase": state.pwm.pulse_width_phase,
        },
        "smooth": {"value": state.smooth.value},
        "vca": {"previous_gain": state.vca.previous_gain},
    }


def _fixture_table() -> list[int]:
    # Long enough for every injected dispatch index and one 64-entry advance.
    return [((index * 73 + 19) & 0x7FFF) - 0x4000 for index in range(2048)]


def _fixture_frequency(pitch: int) -> int:
    # A deterministic injected replacement for MTOFEXTENDED.  It is fixture
    # evidence only and is intentionally not a Schuss pitch-transfer policy.
    return wrap_u32(0x18000000 + ((pitch >> 10) & 0x00FF0000))


def semantic_goldens() -> dict[str, object]:
    """Return deterministic operation and two-block state vectors."""

    table = _fixture_table()
    operations: dict[str, object] = {}

    saw = BlepSawState(phase=wrap_i32(0xF4000000))
    saw_output = evaluate_blep_saw_block(
        saw, -(24 << 21), pitch_to_frequency=_fixture_frequency, blep_table=table
    )
    operations["blep-saw-q27"] = {
        "input": {"pitch": -(24 << 21)},
        "output": saw_output,
        "state": {"phase": saw.phase, "voice_indexes": saw.voice_indexes, "next_voice": saw.next_voice},
    }

    pwm = BlepPwmState(phase=wrap_i32(0xF0000000))
    pwm_output = evaluate_blep_pwm_block(
        pwm, -(12 << 21), Q27_ONE // 5,
        pitch_to_frequency=_fixture_frequency, blep_table=table,
    )
    operations["blep-pwm-q27"] = {
        "input": {"pitch": -(12 << 21), "pulse_width": Q27_ONE // 5},
        "output": pwm_output,
        "state": {
            "phase": pwm.phase,
            "voice_indexes": pwm.voice_indexes,
            "next_voice": pwm.next_voice,
            "pulse_width_phase": pwm.pulse_width_phase,
        },
    }

    smooth = SmoothState()
    smooth_outputs = [
        evaluate_exponential_smooth(smooth, value, 0)
        for value in (Q27_ONE, Q27_ONE // 2, -Q27_ONE // 4, 0)
    ]
    operations["exponential-smooth-q27"] = {
        "input": {"values": [Q27_ONE, Q27_ONE // 2, -Q27_ONE // 4, 0], "time": 0},
        "output": smooth_outputs,
        "state": {"value": smooth.value},
    }

    clip_inputs = [
        -(1 << 29), -(1 << 27), -(1 << 26), -1, 0, 1, 1 << 26,
        (1 << 27) - 1, 1 << 29,
    ]
    operations["soft-clip-q27"] = {
        "input": clip_inputs,
        "output": [evaluate_soft_clip_sample(value) for value in clip_inputs],
    }

    vca = VcaState(previous_gain=-(1 << 24))
    vca_input = [wrap_i32((index - 8) * (1 << 23)) for index in range(BLOCK_SIZE)]
    vca_output = evaluate_vca_block(vca, Q27_ONE // 2, vca_input)
    operations["interpolated-vca-q27"] = {
        "input": {"gain": Q27_ONE // 2, "audio": vca_input},
        "output": vca_output,
        "state": {"previous_gain": vca.previous_gain},
    }

    graph_state = EffectsSemanticState(
        saw=BlepSawState(phase=wrap_i32(0xF4000000)),
        pwm=BlepPwmState(phase=wrap_i32(0xF0000000)),
    )
    transitions = []
    for block_index in range(2):
        before = _state_value(graph_state)
        saw_block = evaluate_blep_saw_block(
            graph_state.saw, -(24 << 21),
            pitch_to_frequency=_fixture_frequency, blep_table=table,
        )
        pwm_block = evaluate_blep_pwm_block(
            graph_state.pwm, -(12 << 21), Q27_ONE // 5,
            pitch_to_frequency=_fixture_frequency, blep_table=table,
        )
        clipped = evaluate_soft_clip_block(saw_block)
        gain = evaluate_exponential_smooth(
            graph_state.smooth, Q27_ONE // 2 if block_index == 0 else Q27_ONE, 0
        )
        amplified = evaluate_vca_block(graph_state.vca, gain, pwm_block)
        transitions.append({
            "block": block_index,
            "before": before,
            "outputs": {
                "saw": saw_block,
                "pwm": pwm_block,
                "soft_clip": clipped,
                "smoothed_gain": gain,
                "vca": amplified,
            },
            "after": _state_value(graph_state),
        })

    return {
        "schema_version": "task025-semantic-goldens-v1",
        "block_size": BLOCK_SIZE,
        "fixture_runtime": {
            "pitch_function": "task025-injected-frequency-v1",
            "blep_table": "task025-injected-2048-entry-table-v1",
            "limitations": [
                "Fixture lookup values are not Ksoloti runtime table evidence.",
                "No reverb, compiler, ARM, device, real-time, or audible evidence is established.",
            ],
        },
        "operations": operations,
        "five_operation_transitions": copy.deepcopy(transitions),
        "reverb": {
            "status": "unsupported",
            "reason": "allocation-span-inconsistent",
            "native_binding_created": False,
        },
    }
