#!/usr/bin/env python3
"""Generate the drum machine's compiled LC3 descriptors from control-map.json."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
from pathlib import Path
from typing import Any


PROTOTYPE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROTOTYPE_ROOT.parents[2]
CONTROL_MAP = PROTOTYPE_ROOT / "contract" / "control-map.json"
DEFAULT_OUTPUT = PROTOTYPE_ROOT / "generated" / "control_descriptors.hpp"
EXPECTED_TOPOLOGY_ARTIFACT = (
    "research/prototype_support/controllers/"
    "novation-launch-control-3-regular-v1.json"
)
EXPECTED_TOPOLOGY_SHA256 = (
    "d69475e54e1bc0a3f441f0bcb5863084c73dbeff5d995670b17c8e894654510b"
)
TOPOLOGY = REPO_ROOT / EXPECTED_TOPOLOGY_ARTIFACT

CONTROL_IDS = {
    "complexity-kick": "complexity_kick",
    "complexity-snare": "complexity_snare",
    "complexity-hat": "complexity_hat",
    "complexity-perc-1": "complexity_percussion_1",
    "complexity-perc-2": "complexity_percussion_2",
    "complexity-perc-3": "complexity_percussion_3",
    "enthusiasm": "enthusiasm",
    "tempo-milli-bpm": "tempo_milli_bpm",
    "swing-u15": "swing_u15",
    "rhythm-select": "rhythm_select",
    "shape-tune": "shape_tune",
    "shape-timbre": "shape_timbre",
    "shape-color": "shape_color",
    "shape-decay": "shape_decay",
    "shape-pitch-env": "shape_pitch_env",
    "shape-level": "shape_level",
    "fill": "fill",
    "rhythm-next": "rhythm_next",
    "shape-select-kick": "shape_select_kick",
    "shape-select-snare": "shape_select_snare",
    "shape-select-hat": "shape_select_hat",
    "shape-select-perc-1": "shape_select_percussion_1",
    "shape-select-perc-2": "shape_select_percussion_2",
    "shape-select-perc-3": "shape_select_percussion_3",
    "unassigned": "unassigned",
}

MAPPING_CURVES = {
    "round-half-up-65535-value-over-127": "u16_full_range",
    "round-half-up-30000-plus-210000-value-over-127": "tempo_milli_bpm",
    "round-half-up-32767-value-over-127": "swing_u15",
    "round-half-up-14-value-over-127": "rhythm_index",
    "identity-7-bit": "u7_identity",
    "none": "none",
}

GESTURES = {
    "direct-rising-edge": "direct_rising_edge",
    "none": "none",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cpp_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def validate_topology(document: dict[str, Any]) -> None:
    require(TOPOLOGY.is_file(), f"missing controller topology: {TOPOLOGY}")
    require(sha256(TOPOLOGY) == EXPECTED_TOPOLOGY_SHA256, "controller topology SHA-256 drift")
    topology = json.loads(TOPOLOGY.read_text(encoding="utf-8"))
    controller = topology["controller"]
    require(controller["model"] == "Launch Control 3", "unexpected controller model")
    require(controller["variant"] == "regular", "controller must be the regular variant")
    require(controller["faders"] == 0, "regular LC3 topology must not invent faders")
    custom_mode = topology["custom_mode_contract"]
    require(custom_mode["slot"] == 1, "unexpected Custom Mode slot")
    require(custom_mode["channel"] == 16, "unexpected topology MIDI channel")
    require(custom_mode["button_press_value"] == 127, "unexpected button press value")
    require(custom_mode["button_release_value"] == 0, "unexpected button release value")
    encoder_ccs = [item["cc"] for item in topology["surface"]["encoders"]]
    button_ccs = [item["cc"] for item in topology["surface"]["buttons"]]
    require(encoder_ccs == list(range(20, 36)), "topology encoder CC ordering drift")
    require(button_ccs == list(range(40, 48)), "topology button CC ordering drift")

    surface = document["compiled_surface"]
    binding = surface["topology"]
    require(binding["artifact"] == EXPECTED_TOPOLOGY_ARTIFACT, "unexpected topology artifact")
    require(binding["sha256"] == EXPECTED_TOPOLOGY_SHA256, "control-map topology hash drift")
    require(surface["channel"] == 16, "compiled surface must use MIDI channel 16")
    require([item["cc"] for item in surface["encoders"]] == encoder_ccs, "encoder selectors drift")
    require([item["cc"] for item in surface["buttons"]] == button_ccs, "button selectors drift")
    require(len(surface["encoders"]) == 16, "compiled surface must have 16 encoders")
    require(len(surface["buttons"]) == 8, "compiled surface must have eight buttons")

    expected_assigned_encoders = list(range(20, 36))
    actual_assigned_encoders = [item["cc"] for item in surface["encoders"] if item["assigned"]]
    require(actual_assigned_encoders == expected_assigned_encoders, "assigned encoder set drift")
    expected_assigned_buttons = list(range(40, 48))
    actual_assigned_buttons = [item["cc"] for item in surface["buttons"] if item["assigned"]]
    require(actual_assigned_buttons == expected_assigned_buttons, "assigned button set drift")

    for item in surface["encoders"]:
        require(item["control"] in CONTROL_IDS, f"unknown control {item['control']}")
        require(item["mapping"] in MAPPING_CURVES, f"unknown mapping {item['mapping']}")
        require(item["type"] in {"continuous", "unassigned"}, "invalid encoder type")
        require(item["assigned"] == (item["type"] == "continuous"), "encoder assignment/type mismatch")
    for item in surface["buttons"]:
        require(item["control"] in CONTROL_IDS, f"unknown control {item['control']}")
        require(item["gesture"] in GESTURES, f"unknown gesture {item['gesture']}")
        require(item["type"] in {"action", "unassigned"}, "invalid button type")
        require(item["assigned"] == (item["type"] == "action"), "button assignment/type mismatch")
        require(item["press_value"] == 127 and item["release_value"] == 0, "button values drift")

    preset = document["adapter_owned_desktop_audition_preset"]
    require(preset["owner"] == "standalone-adapter", "unexpected audition preset owner")
    require(not preset["canonical_source_default"], "audition preset cannot be a Core default")
    controls = preset["controls"]
    require(len(controls["complexity"]) == 6, "audition preset needs six complexities")
    require(all(0 <= value <= 65535 for value in controls["complexity"]), "complexity default out of range")
    require(0 <= controls["enthusiasm"] <= 65535, "enthusiasm default out of range")
    require(30000 <= controls["tempo_milli_bpm"] <= 240000, "tempo default out of range")
    require(0 <= controls["swing_u15"] <= 32767, "swing default out of range")
    require(controls["rhythm_preset"] == 0, "audition rhythm default must be First Light")


def render_encoder(item: dict[str, Any]) -> str:
    domain = item["domain"]
    return (
        "    {ControlId::%s, %d, %s, %s, %s, ControlKind::%s, "
        "MappingCurve::%s, %dU, %dU, %s},"
        % (
            CONTROL_IDS[item["control"]],
            item["cc"],
            cpp_string(item["physical_control"]),
            cpp_string(item["label"]),
            cpp_string(item["control"]),
            item["type"],
            MAPPING_CURVES[item["mapping"]],
            domain[0],
            domain[1],
            cpp_string(item["timing"]),
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
    validate_topology(document)
    surface = document["compiled_surface"]
    preset = document["adapter_owned_desktop_audition_preset"]["controls"]
    encoder_lines = "\n".join(render_encoder(item) for item in surface["encoders"])
    button_lines = "\n".join(render_button(item) for item in surface["buttons"])
    return f"""// Generated by tools/generate_control_descriptors.py. Do not edit.
// Source: control-map.json SHA-256 {sha256(CONTROL_MAP)}
// Topology: novation-launch-control-3-regular-v1.json SHA-256 {sha256(TOPOLOGY)}
#pragma once

#include "schuss/generative_drum_machine/control_map.hpp"

#include <array>
#include <cstdint>
#include <string_view>

namespace schuss::generative_drum_machine::generated {{

inline constexpr std::string_view kControlMapSha256{{{cpp_string(sha256(CONTROL_MAP))}}};
inline constexpr std::string_view kControllerTopologySha256{{{cpp_string(sha256(TOPOLOGY))}}};
inline constexpr std::uint8_t kMidiChannel{{{surface['channel']}}};

inline constexpr Controls kDesktopAuditionControls{{
    {{{{{', '.join(f'{value}U' for value in preset['complexity'])}}}}},
    {preset['enthusiasm']}U,
    {preset['tempo_milli_bpm']}U,
    {preset['swing_u15']}U,
}};

inline constexpr std::array<EncoderDescriptor, 16> kEncoders{{{{
{encoder_lines}
}}}};

inline constexpr std::array<ButtonDescriptor, 8> kButtons{{{{
{button_lines}
}}}};

}}  // namespace schuss::generative_drum_machine::generated
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if generated header is stale")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    try:
        expected = generate()
    except (KeyError, OSError, json.JSONDecodeError, ValueError) as error:
        print(f"control descriptor generation failed: {error}")
        return 1
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
