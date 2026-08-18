"""Bounded declarative DSP-kernel validation and deterministic host audition."""

from __future__ import annotations

import hashlib
import io
import math
import struct
import wave
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable


MAX_INSTRUCTIONS = 128
MAX_FRAMES = 192_000
MAX_NUMERIC_MAGNITUDE = 1_000_000_000.0
MAX_STIMULUS_AMPLITUDE = 16.0


class NativeKernelError(ValueError):
    """A closed native-kernel program or audition request is invalid."""

    def __init__(self, code: str, message: str, *, location: str = "$") -> None:
        super().__init__(message)
        self.code = code
        self.location = location


@dataclass(frozen=True)
class KernelValidation:
    instruction_count: int
    state_slot_count: int
    input_keys: tuple[str, ...]
    parameter_keys: tuple[str, ...]
    output_keys: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": "valid",
            "instruction_count": self.instruction_count,
            "state_slot_count": self.state_slot_count,
            "input_keys": list(self.input_keys),
            "parameter_keys": list(self.parameter_keys),
            "output_keys": list(self.output_keys),
            "arbitrary_code": "prohibited",
        }


_ARITY: dict[str, tuple[int, int]] = {
    "abs": (1, 1),
    "add": (2, 2),
    "clamp": (3, 3),
    "max": (2, 2),
    "min": (2, 2),
    "multiply": (2, 2),
    "negate": (1, 1),
    "noise": (0, 0),
    "one-pole-lowpass": (2, 2),
    "oscillator-saw": (1, 1),
    "oscillator-sine": (1, 1),
    "oscillator-square": (1, 2),
    "soft-clip": (1, 1),
    "subtract": (2, 2),
    "tanh": (1, 1),
    "wavefold": (1, 1),
}

_STATEFUL = {
    "noise",
    "one-pole-lowpass",
    "oscillator-saw",
    "oscillator-sine",
    "oscillator-square",
}


def _decimal(value: str, *, location: str) -> float:
    try:
        parsed = Decimal(value)
    except (InvalidOperation, TypeError) as exc:
        raise NativeKernelError(
            "NATIVE_KERNEL_DECIMAL_INVALID",
            "kernel values must use finite exact-decimal strings",
            location=location,
        ) from exc
    if not parsed.is_finite():
        raise NativeKernelError(
            "NATIVE_KERNEL_DECIMAL_INVALID",
            "kernel values must be finite",
            location=location,
        )
    result = float(parsed)
    if not math.isfinite(result) or abs(result) > MAX_NUMERIC_MAGNITUDE:
        raise NativeKernelError(
            "NATIVE_KERNEL_NUMERIC_LIMIT_EXCEEDED",
            f"kernel values must have magnitude at most {MAX_NUMERIC_MAGNITUDE:g}",
            location=location,
        )
    return result


def _source_key(
    source: dict[str, Any],
    *,
    input_keys: set[str],
    parameter_keys: set[str],
    prior_instructions: set[str],
    location: str,
) -> None:
    kind = source["kind"]
    if kind == "input" and source["key"] not in input_keys:
        raise NativeKernelError(
            "NATIVE_KERNEL_INPUT_UNRESOLVED",
            f"input {source['key']!r} is not declared by the public interface",
            location=location,
        )
    if kind == "parameter" and source["key"] not in parameter_keys:
        raise NativeKernelError(
            "NATIVE_KERNEL_PARAMETER_UNRESOLVED",
            f"parameter {source['key']!r} is not declared by the public interface",
            location=location,
        )
    if kind == "instruction" and source["instruction_id"] not in prior_instructions:
        raise NativeKernelError(
            "NATIVE_KERNEL_DATAFLOW_INVALID",
            "instruction sources must reference one unique earlier instruction",
            location=location,
        )
    if kind == "literal":
        _decimal(source["value"], location=f"{location}.value")


def validate_program(
    program: dict[str, Any],
    interface: dict[str, Any],
) -> KernelValidation:
    """Validate bounded acyclic dataflow against one compact public interface."""

    if len(program["instructions"]) > MAX_INSTRUCTIONS:
        raise NativeKernelError(
            "NATIVE_KERNEL_LIMIT_EXCEEDED",
            f"native kernels are limited to {MAX_INSTRUCTIONS} instructions",
            location="$.instructions",
        )
    ports = interface["ports"]
    parameters = interface["parameters"]
    interface_keys = [item["key"] for item in (*ports, *parameters)]
    if len(interface_keys) != len(set(interface_keys)):
        raise NativeKernelError(
            "NATIVE_KERNEL_INTERFACE_DUPLICATE",
            "public port and parameter keys must be unique",
            location="$.interface",
        )
    input_keys = {
        item["key"] for item in ports if item["direction"] == "inlet"
    }
    output_keys = {
        item["key"] for item in ports if item["direction"] == "outlet"
    }
    parameter_keys = {item["key"] for item in parameters}
    for index, parameter in enumerate(parameters):
        minimum = _decimal(
            parameter["minimum"], location=f"$.interface.parameters[{index}].minimum"
        )
        maximum = _decimal(
            parameter["maximum"], location=f"$.interface.parameters[{index}].maximum"
        )
        default = _decimal(
            parameter["default"], location=f"$.interface.parameters[{index}].default"
        )
        if minimum > maximum or not minimum <= default <= maximum:
            raise NativeKernelError(
                "NATIVE_KERNEL_PARAMETER_RANGE_INVALID",
                "parameter default must lie inside its ordered finite range",
                location=f"$.interface.parameters[{index}]",
            )
    declared_input_keys = set(program.get("input_keys", input_keys))
    declared_parameter_keys = set(program.get("parameter_keys", parameter_keys))
    if declared_input_keys != input_keys or declared_parameter_keys != parameter_keys:
        raise NativeKernelError(
            "NATIVE_KERNEL_INTERFACE_MISMATCH",
            "kernel input and parameter keys must exactly equal the public interface",
            location="$",
        )

    prior: set[str] = set()
    state_slots = 0
    for index, instruction in enumerate(program["instructions"]):
        identifier = instruction["instruction_id"]
        if identifier in prior:
            raise NativeKernelError(
                "NATIVE_KERNEL_INSTRUCTION_DUPLICATE",
                f"instruction {identifier!r} is duplicated",
                location=f"$.instructions[{index}].instruction_id",
            )
        operation = instruction["operation"]
        arity = _ARITY.get(operation)
        if arity is None:
            raise NativeKernelError(
                "NATIVE_KERNEL_OPERATION_UNSUPPORTED",
                f"operation {operation!r} is not in the bounded kernel language",
                location=f"$.instructions[{index}].operation",
            )
        count = len(instruction["inputs"])
        if count < arity[0] or count > arity[1]:
            raise NativeKernelError(
                "NATIVE_KERNEL_ARITY_INVALID",
                f"operation {operation!r} requires {arity[0]}"
                + ("" if arity[0] == arity[1] else f" to {arity[1]}")
                + " inputs",
                location=f"$.instructions[{index}].inputs",
            )
        for source_index, source in enumerate(instruction["inputs"]):
            _source_key(
                source,
                input_keys=input_keys,
                parameter_keys=parameter_keys,
                prior_instructions=prior,
                location=f"$.instructions[{index}].inputs[{source_index}]",
            )
        prior.add(identifier)
        state_slots += operation in _STATEFUL

    mapped_outputs: set[str] = set()
    for index, output in enumerate(program["outputs"]):
        key = output["port_key"]
        if key not in output_keys or key in mapped_outputs:
            raise NativeKernelError(
                "NATIVE_KERNEL_OUTPUT_INVALID",
                "each public outlet must be mapped exactly once",
                location=f"$.outputs[{index}].port_key",
            )
        _source_key(
            output["source"],
            input_keys=input_keys,
            parameter_keys=parameter_keys,
            prior_instructions=prior,
            location=f"$.outputs[{index}].source",
        )
        mapped_outputs.add(key)
    if mapped_outputs != output_keys:
        missing = sorted(output_keys - mapped_outputs)
        raise NativeKernelError(
            "NATIVE_KERNEL_OUTPUT_INCOMPLETE",
            f"public outlets are not completely mapped: {missing}",
            location="$.outputs",
        )
    return KernelValidation(
        instruction_count=len(program["instructions"]),
        state_slot_count=state_slots,
        input_keys=tuple(sorted(input_keys)),
        parameter_keys=tuple(sorted(parameter_keys)),
        output_keys=tuple(sorted(output_keys)),
    )


def _source_value(
    source: dict[str, Any],
    inputs: dict[str, float],
    parameters: dict[str, float],
    registers: dict[str, float],
) -> float:
    kind = source["kind"]
    if kind == "input":
        return inputs[source["key"]]
    if kind == "parameter":
        return parameters[source["key"]]
    if kind == "instruction":
        return registers[source["instruction_id"]]
    return float(Decimal(source["value"]))


def _fold(value: float) -> float:
    value = math.fmod(value + 1.0, 4.0)
    if value < 0:
        value += 4.0
    return 1.0 - abs(value - 2.0)


def _render_instruction(
    operation: str,
    values: list[float],
    state: dict[str, float | int],
    sample_rate: int,
) -> float:
    if operation == "abs":
        return abs(values[0])
    if operation == "add":
        return values[0] + values[1]
    if operation == "clamp":
        lower, upper = sorted((values[1], values[2]))
        return min(upper, max(lower, values[0]))
    if operation == "max":
        return max(values)
    if operation == "min":
        return min(values)
    if operation == "multiply":
        return values[0] * values[1]
    if operation == "negate":
        return -values[0]
    if operation == "subtract":
        return values[0] - values[1]
    if operation == "tanh":
        return math.tanh(values[0])
    if operation == "soft-clip":
        x = max(-1.5, min(1.5, values[0]))
        return max(-1.0, min(1.0, x - (x * x * x) / 3.0))
    if operation == "wavefold":
        return _fold(values[0])
    if operation == "noise":
        word = int(state.get("word", 0x6D2B79F5)) & 0xFFFFFFFF
        word ^= (word << 13) & 0xFFFFFFFF
        word ^= word >> 17
        word ^= (word << 5) & 0xFFFFFFFF
        state["word"] = word
        return (word / 2147483647.5) - 1.0
    if operation.startswith("oscillator-"):
        frequency = min(sample_rate * 0.49, max(0.0, values[0]))
        phase = float(state.get("phase", 0.0))
        if operation == "oscillator-sine":
            result = math.sin(phase * math.tau)
        elif operation == "oscillator-saw":
            result = 2.0 * phase - 1.0
        else:
            width = min(0.99, max(0.01, values[1] if len(values) == 2 else 0.5))
            result = 1.0 if phase < width else -1.0
        state["phase"] = (phase + frequency / sample_rate) % 1.0
        return result
    if operation == "one-pole-lowpass":
        cutoff = min(sample_rate * 0.49, max(0.0, values[1]))
        coefficient = 1.0 - math.exp(-math.tau * cutoff / sample_rate)
        previous = float(state.get("value", 0.0))
        result = previous + coefficient * (values[0] - previous)
        state["value"] = result
        return result
    raise AssertionError(operation)


def _stimulus_value(
    stimulus: dict[str, Any], frame: int, sample_rate: int
) -> float:
    amplitude = _decimal(stimulus["amplitude"], location="$.audition.stimuli.amplitude")
    kind = stimulus["kind"]
    if kind == "silence":
        return 0.0
    if kind == "constant":
        return amplitude
    if kind == "impulse":
        return amplitude if frame == 0 else 0.0
    frequency = _decimal(
        stimulus["frequency_hz"], location="$.audition.stimuli.frequency_hz"
    )
    return amplitude * math.sin(math.tau * frequency * frame / sample_rate)


def _metric(value: float) -> str:
    if not math.isfinite(value) or abs(value) < 0.0000000005:
        return "0"
    rendered = f"{value:.9f}".rstrip("0").rstrip(".")
    return "0" if rendered == "-0" else rendered


def evaluate_program(
    program: dict[str, Any],
    interface: dict[str, Any],
    audition: dict[str, Any],
) -> tuple[bytes, dict[str, Any]]:
    """Render a deterministic mono mix and return objective measurements."""

    validation = validate_program(program, interface)
    sample_rate = audition["sample_rate"]
    frame_count = audition["frame_count"]
    if frame_count > MAX_FRAMES:
        raise NativeKernelError(
            "NATIVE_KERNEL_AUDITION_LIMIT_EXCEEDED",
            f"auditions are limited to {MAX_FRAMES} frames",
            location="$.audition.frame_count",
        )
    stimuli = {item["port_key"]: item for item in audition["stimuli"]}
    if len(stimuli) != len(audition["stimuli"]):
        raise NativeKernelError(
            "NATIVE_KERNEL_STIMULUS_DUPLICATE",
            "each public inlet may have at most one audition stimulus",
            location="$.audition.stimuli",
        )
    if set(stimuli) - set(validation.input_keys):
        raise NativeKernelError(
            "NATIVE_KERNEL_STIMULUS_INVALID",
            "audition stimuli may reference only declared public inlets",
            location="$.audition.stimuli",
        )
    for index, stimulus in enumerate(audition["stimuli"]):
        amplitude = _decimal(
            stimulus["amplitude"],
            location=f"$.audition.stimuli[{index}].amplitude",
        )
        frequency = _decimal(
            stimulus["frequency_hz"],
            location=f"$.audition.stimuli[{index}].frequency_hz",
        )
        if abs(amplitude) > MAX_STIMULUS_AMPLITUDE:
            raise NativeKernelError(
                "NATIVE_KERNEL_STIMULUS_LIMIT_EXCEEDED",
                f"audition amplitude magnitude is limited to {MAX_STIMULUS_AMPLITUDE:g}",
                location=f"$.audition.stimuli[{index}].amplitude",
            )
        if frequency < 0 or (
            stimulus["kind"] == "sine" and frequency > sample_rate * 0.5
        ):
            raise NativeKernelError(
                "NATIVE_KERNEL_STIMULUS_FREQUENCY_INVALID",
                "audition frequency must be non-negative and sine stimuli may not exceed Nyquist",
                location=f"$.audition.stimuli[{index}].frequency_hz",
            )
    defaults = {
        item["key"]: _decimal(
            item["default"], location=f"$.interface.parameters[{index}].default"
        )
        for index, item in enumerate(interface["parameters"])
    }
    states: dict[str, dict[str, float | int]] = {}
    for item in program["instructions"]:
        state: dict[str, float | int] = {}
        if item["operation"] == "noise":
            state["word"] = int.from_bytes(
                hashlib.sha256(item["instruction_id"].encode("ascii")).digest()[:4],
                "big",
            ) or 0x6D2B79F5
        states[item["instruction_id"]] = state
    samples: list[float] = []
    output_count = max(1, len(program["outputs"]))
    for frame in range(frame_count):
        input_values = {
            key: _stimulus_value(
                stimuli.get(
                    key,
                    {
                        "kind": "silence",
                        "amplitude": "0",
                        "frequency_hz": "0",
                    },
                ),
                frame,
                sample_rate,
            )
            for key in validation.input_keys
        }
        registers: dict[str, float] = {}
        for instruction_index, instruction in enumerate(program["instructions"]):
            values = [
                _source_value(source, input_values, defaults, registers)
                for source in instruction["inputs"]
            ]
            try:
                rendered = _render_instruction(
                    instruction["operation"],
                    values,
                    states[instruction["instruction_id"]],
                    sample_rate,
                )
            except (OverflowError, ValueError) as exc:
                raise NativeKernelError(
                    "NATIVE_KERNEL_EVALUATION_NONFINITE",
                    "kernel evaluation produced an invalid numeric result",
                    location=f"$.instructions[{instruction_index}]",
                ) from exc
            if not math.isfinite(rendered):
                raise NativeKernelError(
                    "NATIVE_KERNEL_EVALUATION_NONFINITE",
                    "kernel evaluation produced a non-finite numeric result",
                    location=f"$.instructions[{instruction_index}]",
                )
            registers[instruction["instruction_id"]] = rendered
        output_values = [
            _source_value(output["source"], input_values, defaults, registers)
            for output in program["outputs"]
        ]
        if not all(math.isfinite(value) for value in output_values):
            raise NativeKernelError(
                "NATIVE_KERNEL_EVALUATION_NONFINITE",
                "kernel output produced a non-finite numeric result",
                location="$.outputs",
            )
        sample = sum(output_values) / output_count
        if not math.isfinite(sample):
            raise NativeKernelError(
                "NATIVE_KERNEL_EVALUATION_NONFINITE",
                "mixed kernel output produced a non-finite numeric result",
                location="$.outputs",
            )
        samples.append(max(-1.0, min(1.0, sample)))

    pcm = b"".join(
        struct.pack("<h", max(-32768, min(32767, int(round(sample * 32767.0)))))
        for sample in samples
    )
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(pcm)
    wav_bytes = buffer.getvalue()
    peak = max((abs(value) for value in samples), default=0.0)
    rms = math.sqrt(sum(value * value for value in samples) / max(1, len(samples)))
    dc = sum(samples) / max(1, len(samples))
    zero_crossings = sum(
        1
        for left, right in zip(samples, samples[1:])
        if (left < 0 <= right) or (left >= 0 > right)
    )
    crest = peak / rms if rms else 0.0
    facts = {
        "sample_rate": sample_rate,
        "frame_count": frame_count,
        "channel_count": 1,
        "sample_format": "signed-int16-little-endian",
        "byte_length": len(wav_bytes),
        "content_hash": "sha256:" + hashlib.sha256(wav_bytes).hexdigest(),
        "measurements": {
            "peak_absolute": _metric(peak),
            "rms": _metric(rms),
            "dc_mean": _metric(dc),
            "crest_factor": _metric(crest),
            "zero_crossing_count": zero_crossings,
        },
        "evidence": {
            "structural": "passed",
            "host_evaluation": "passed",
            "target_lowering": "not-run",
            "arm_build": "not-run",
            "connected_device": "not-run",
            "real_time_resources": "not-evaluated",
            "audible_listening": "not-run",
        },
        "interpretation_boundary": (
            "objective host measurements only; no subjective sonic quality, "
            "target, device, real-time, or listening conclusion"
        ),
    }
    return wav_bytes, facts


def source_references(program: dict[str, Any]) -> Iterable[dict[str, Any]]:
    """Yield every value source for focused validation/tests."""

    for instruction in program["instructions"]:
        yield from instruction["inputs"]
    for output in program["outputs"]:
        yield output["source"]
