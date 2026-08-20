#!/usr/bin/env python3
"""Generate Tide Pit's compiled controller descriptors from control-map.json."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
from pathlib import Path
from typing import Any


PROTOTYPE_ROOT = Path(__file__).resolve().parents[1]
CONTROL_MAP = PROTOTYPE_ROOT / "control-map.json"
DEFAULT_OUTPUT = PROTOTYPE_ROOT / "generated" / "control_descriptors.hpp"
EXPECTED_TOPOLOGY_ARTIFACT = (
    "research/prototype_support/controllers/"
    "novation-launch-control-3-regular-v1.json"
)
TOPOLOGY = (
    PROTOTYPE_ROOT.parents[1]
    / "prototype_support"
    / "controllers"
    / "novation-launch-control-3-regular-v1.json"
)


CONTROL_IDS = {
    "stage-1": "set_stage_1",
    "stage-2": "set_stage_2",
    "stage-3": "set_stage_3",
    "stage-4": "set_stage_4",
    "rate": "set_rate",
    "memory": "set_memory",
    "material": "set_material",
    "position": "set_position",
    "fx-a": "set_fx_a",
    "fx-b": "set_fx_b",
    "root": "set_root",
    "source-next": "source_next",
    "mutate": "mutate",
    "lock-toggle": "lock_toggle",
    "capture-toggle": "capture_toggle",
    "effect-next": "effect_next",
    "target-next": "target_next",
    "scale-next": "scale_next",
    "unassigned": "unassigned",
}

MIDI_CURVES = {
    "linear-normalized": "linear_normalized",
    "round-half-up-36-plus-36-value-over-127": "root_note_round_half_up",
    "none": "none",
}

SOURCE_CURVES = {
    "direct-normalized": "direct_normalized",
    "0.08-plus-5.92-x-squared-hz": "rate_quadratic",
    "mutation-threshold-memory-squared": "memory_squared_threshold",
    "contextual-source-material": "contextual_material",
    "grain-position": "grain_position",
    "contextual-source-effect-a-with-soft-pickup": "contextual_fx_a_soft_pickup",
    "contextual-source-effect-b-with-soft-pickup": "contextual_fx_b_soft_pickup",
    "quantized-midi-note-36-through-72": "root_note_36_to_72",
    "none": "none",
}

GESTURES = {
    "direct-rising-edge": "direct_rising_edge",
    "source-effect-button-hold": "source_effect_button_hold",
    "source-effect-button-tap": "source_effect_button_tap",
    "source-encoder-switch-hold": "source_encoder_switch_hold",
    "source-encoder-switch-tap": "source_encoder_switch_tap",
    "none": "none",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cpp_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def cpp_float(value: int | float) -> str:
    rendered = repr(float(value))
    return rendered if "." in rendered else rendered + ".0"


def cpp_float32(value: int | float) -> str:
    return cpp_float(value) + "f"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_generation_inputs(document: dict[str, Any]) -> None:
    surface = document["compiled_surface"]
    topology_binding = surface["topology"]
    require(
        topology_binding["artifact"] == EXPECTED_TOPOLOGY_ARTIFACT,
        "unexpected controller topology artifact",
    )
    require(TOPOLOGY.is_file(), f"missing controller topology: {TOPOLOGY}")
    require(
        sha256(TOPOLOGY) == topology_binding["sha256"],
        "controller topology bytes do not match the bound SHA-256",
    )
    require(surface["channel"] == 16, "compiled surface must use MIDI channel 16")
    require(len(surface["encoders"]) == 16, "compiled surface must have 16 encoders")
    require(len(surface["buttons"]) == 8, "compiled surface must have eight buttons")
    for item in surface["encoders"]:
        require(item["control"] in CONTROL_IDS, f"unknown control {item['control']}")
        require(item["midi_curve"] in MIDI_CURVES, f"unknown MIDI curve {item['midi_curve']}")
        require(item["source_curve"] in SOURCE_CURVES, f"unknown source curve {item['source_curve']}")
    for item in surface["buttons"]:
        require(item["control"] in CONTROL_IDS, f"unknown control {item['control']}")
        require(item["gesture"] in GESTURES, f"unknown gesture {item['gesture']}")


def render_encoder(item: dict[str, Any]) -> str:
    default = item["adapter_owned_default"]
    if default is None:
        default_value = "0.0"
        default_midi = 0
        has_default = "false"
    else:
        default_value = cpp_float(default["semantic_value"])
        default_midi = default["midi_value"]
        has_default = "true"
    soft_pickup = "true" if "soft-pickup" in item["source_curve"] else "false"
    return (
        "    {ControlId::%s, %d, %s, %s, %s, ControlKind::%s, "
        "MidiCurve::%s, SourceCurve::%s, %s, %s, %d, %s, %s},"
        % (
            CONTROL_IDS[item["control"]],
            item["cc"],
            cpp_string(item["physical_control"]),
            cpp_string(item["label"]),
            cpp_string(item["control"]),
            item["type"],
            MIDI_CURVES[item["midi_curve"]],
            SOURCE_CURVES[item["source_curve"]],
            cpp_string(item["timing"]),
            default_value,
            default_midi,
            has_default,
            soft_pickup,
        )
    )


def render_button(item: dict[str, Any]) -> str:
    return (
        "    {ControlId::%s, %d, %s, %s, %s, ControlKind::%s, "
        "GestureKind::%s, %d, %d},"
        % (
            CONTROL_IDS[item["control"]],
            item["cc"],
            cpp_string(item["physical_control"]),
            cpp_string(item["label"]),
            cpp_string(item["control"]),
            item["type"],
            GESTURES[item["gesture"]],
            item["press_value"],
            item["release_value"],
        )
    )


def generate() -> str:
    document = json.loads(CONTROL_MAP.read_text(encoding="utf-8"))
    validate_generation_inputs(document)
    surface = document["compiled_surface"]
    preset = document["adapter_owned_desktop_audition_preset"]["controls"]
    encoder_lines = "\n".join(render_encoder(item) for item in surface["encoders"])
    button_lines = "\n".join(render_button(item) for item in surface["buttons"])
    return f"""// Generated by tools/generate_control_descriptors.py. Do not edit.
// Source: control-map.json SHA-256 {sha256(CONTROL_MAP)}
// Topology: novation-launch-control-3-regular-v1.json SHA-256 {sha256(TOPOLOGY)}
#pragma once

#include \"tidepit/control_map.hpp\"

#include <array>
#include <cstdint>
#include <string_view>

namespace tidepit::generated {{

inline constexpr std::string_view kControlMapSha256{{{cpp_string(sha256(CONTROL_MAP))}}};
inline constexpr std::string_view kControllerTopologySha256{{{cpp_string(sha256(TOPOLOGY))}}};
inline constexpr std::uint8_t kMidiChannel{{{surface['channel']}}};

inline constexpr Controls kAdapterOwnedDesktopAuditionPreset{{
    {{{{{cpp_float32(preset['stage-1'])}, {cpp_float32(preset['stage-2'])}, {cpp_float32(preset['stage-3'])}, {cpp_float32(preset['stage-4'])}}}}},
    {cpp_float32(preset['rate'])},
    {cpp_float32(preset['memory'])},
    {cpp_float32(preset['material'])},
    {cpp_float32(preset['position'])},
    {cpp_float32(preset['fx-a'])},
    {cpp_float32(preset['fx-b'])},
    {preset['root']},
}};

// Core::prepare resets to Controls{{}}. These compile-time guards make the
// map-generated adapter preset authoritative without injecting startup MIDI.
inline constexpr Controls kDeclaredCoreStartupControls{{}};
static_assert(kDeclaredCoreStartupControls.stages[0] == kAdapterOwnedDesktopAuditionPreset.stages[0]);
static_assert(kDeclaredCoreStartupControls.stages[1] == kAdapterOwnedDesktopAuditionPreset.stages[1]);
static_assert(kDeclaredCoreStartupControls.stages[2] == kAdapterOwnedDesktopAuditionPreset.stages[2]);
static_assert(kDeclaredCoreStartupControls.stages[3] == kAdapterOwnedDesktopAuditionPreset.stages[3]);
static_assert(kDeclaredCoreStartupControls.rate == kAdapterOwnedDesktopAuditionPreset.rate);
static_assert(kDeclaredCoreStartupControls.memory == kAdapterOwnedDesktopAuditionPreset.memory);
static_assert(kDeclaredCoreStartupControls.material == kAdapterOwnedDesktopAuditionPreset.material);
static_assert(kDeclaredCoreStartupControls.position == kAdapterOwnedDesktopAuditionPreset.position);
static_assert(kDeclaredCoreStartupControls.fx_a == kAdapterOwnedDesktopAuditionPreset.fx_a);
static_assert(kDeclaredCoreStartupControls.fx_b == kAdapterOwnedDesktopAuditionPreset.fx_b);
static_assert(kDeclaredCoreStartupControls.root_note == kAdapterOwnedDesktopAuditionPreset.root_note);

inline constexpr std::array<EncoderDescriptor, 16> kEncoders{{{{
{encoder_lines}
}}}};

inline constexpr std::array<ButtonDescriptor, 8> kButtons{{{{
{button_lines}
}}}};

}}  // namespace tidepit::generated
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if the generated header is stale")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()

    expected = generate()
    if arguments.check:
        if not arguments.output.is_file():
            print(f"missing generated header: {arguments.output}")
            return 1
        current = arguments.output.read_text(encoding="utf-8")
        if current != expected:
            print(
                "".join(
                    difflib.unified_diff(
                        current.splitlines(keepends=True),
                        expected.splitlines(keepends=True),
                        fromfile=str(arguments.output),
                        tofile="expected generated output",
                    )
                ),
                end="",
            )
            return 1
        print(f"control descriptors are current: {arguments.output}")
        return 0

    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(expected, encoding="utf-8", newline="\n")
    print(f"generated {arguments.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
