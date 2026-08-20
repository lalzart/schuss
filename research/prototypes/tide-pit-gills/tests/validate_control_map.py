#!/usr/bin/env python3
"""Validate Tide Pit's generated Launch Control 3 mapping contract."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any


PROTOTYPE_ROOT = Path(__file__).resolve().parents[1]
CONTROL_MAP = PROTOTYPE_ROOT / "control-map.json"
GENERATED = PROTOTYPE_ROOT / "generated" / "control_descriptors.hpp"
GENERATOR = PROTOTYPE_ROOT / "tools" / "generate_control_descriptors.py"
TOPOLOGY = (
    PROTOTYPE_ROOT.parents[1]
    / "prototype_support"
    / "controllers"
    / "novation-launch-control-3-regular-v1.json"
)
TOPOLOGY_ARTIFACT = (
    "research/prototype_support/controllers/"
    "novation-launch-control-3-regular-v1.json"
)
TOPOLOGY_SHA256 = "d69475e54e1bc0a3f441f0bcb5863084c73dbeff5d995670b17c8e894654510b"

EXPECTED_ENCODERS = (
    (20, "top-1", "STAGE 1", "stage-1", "linear-normalized", "direct-normalized", "next-source-quantum", 0.20, 25, "normalized"),
    (21, "top-2", "STAGE 2", "stage-2", "linear-normalized", "direct-normalized", "next-source-quantum", 0.50, 64, "normalized"),
    (22, "top-3", "STAGE 3", "stage-3", "linear-normalized", "direct-normalized", "next-source-quantum", 0.80, 102, "normalized"),
    (23, "top-4", "STAGE 4", "stage-4", "linear-normalized", "direct-normalized", "next-source-quantum", 0.30, 38, "normalized"),
    (24, "top-5", "RATE", "rate", "linear-normalized", "0.08-plus-5.92-x-squared-hz", "next-source-quantum", 0.55, 70, "normalized"),
    (25, "top-6", "MEMORY", "memory", "linear-normalized", "mutation-threshold-memory-squared", "next-source-quantum", 0.78, 99, "normalized"),
    (26, "top-7", "MATERIAL", "material", "linear-normalized", "contextual-source-material", "next-source-quantum", 0.50, 64, "normalized"),
    (27, "top-8", "POSITION", "position", "linear-normalized", "grain-position", "next-source-quantum", 0.31, 39, "normalized"),
    (28, "bottom-1", "FX-A", "fx-a", "linear-normalized", "contextual-source-effect-a-with-soft-pickup", "next-source-quantum-after-pickup", 0.60, 76, "normalized"),
    (29, "bottom-2", "FX-B", "fx-b", "linear-normalized", "contextual-source-effect-b-with-soft-pickup", "next-source-quantum-after-pickup", 0.35, 44, "normalized"),
    (30, "bottom-3", "ROOT", "root", "round-half-up-36-plus-36-value-over-127", "quantized-midi-note-36-through-72", "next-source-quantum", 60, 85, "midi-note"),
)

EXPECTED_BUTTONS = (
    (40, "button-1", "SOURCE", "source-next", "direct-rising-edge"),
    (41, "button-2", "MUTATE", "mutate", "direct-rising-edge"),
    (42, "button-3", "LOCK", "lock-toggle", "direct-rising-edge"),
    (43, "button-4", "FREEZE", "capture-toggle", "source-effect-button-hold"),
    (44, "button-5", "FX MODE", "effect-next", "source-effect-button-tap"),
    (45, "button-6", "TARGET", "target-next", "source-encoder-switch-hold"),
    (46, "button-7", "SCALE", "scale-next", "source-encoder-switch-tap"),
)

PRESET = {
    "fx-a": 0.60,
    "fx-b": 0.35,
    "material": 0.50,
    "memory": 0.78,
    "position": 0.31,
    "rate": 0.55,
    "root": 60,
    "stage-1": 0.20,
    "stage-2": 0.50,
    "stage-3": 0.80,
    "stage-4": 0.30,
}

GESTURE_SYNTHESIS = {
    "effect-next": "Drive 76 high blocks total (one candidate-change observation plus 75 matching observations), then 76 low blocks by the same rule; effect changes on debounced release.",
    "capture-toggle": "Drive 1575 high blocks total: one candidate-change observation, 75 matching observations to accept high, and 1499 further high blocks so the hold counter reaches 1500 including the acceptance block; then drive 76 low blocks without a tap action.",
    "scale-next": "Drive 9 high blocks total (one candidate-change observation plus 8 matching observations), then 9 low blocks by the same rule; scale changes on debounced release.",
    "target-next": "Drive 1508 high blocks total: one candidate-change observation, 8 matching observations to accept high, and 1499 further high blocks so the hold counter reaches 1500 including the acceptance block; then drive 9 low blocks without a tap action.",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_topology(document: dict[str, Any]) -> None:
    require(sha256(TOPOLOGY) == TOPOLOGY_SHA256, "controller topology bytes drifted")
    topology = json.loads(TOPOLOGY.read_text(encoding="utf-8"))
    require(topology["schema_version"] == "schuss-prototype-controller-surface-v1", "unexpected topology schema")
    require(
        topology["controller"]
        == {
            "assignable_buttons": 8,
            "endless_encoders": 16,
            "faders": 0,
            "manufacturer": "Novation",
            "model": "Launch Control 3",
            "variant": "regular",
        },
        "topology is not the exact regular Launch Control 3",
    )
    mode = topology["custom_mode_contract"]
    require(mode["channel"] == 16, "topology must use channel 16")
    require(mode["encoder_message"] == "midi-1.0-control-change-7-bit-absolute", "encoder protocol drifted")
    require(mode["encoder_minimum"] == 0 and mode["encoder_maximum"] == 127, "encoder range drifted")
    require(mode["button_message"] == "midi-1.0-control-change-momentary", "button protocol drifted")
    require(mode["button_press_value"] == 127 and mode["button_release_value"] == 0, "button values are not 127/0")
    encoders = topology["surface"]["encoders"]
    buttons = topology["surface"]["buttons"]
    require([item["cc"] for item in encoders] == list(range(20, 36)), "topology encoder CCs are not 20-35")
    require([item["cc"] for item in buttons] == list(range(40, 48)), "topology button CCs are not 40-47")
    require(len({item["id"] for item in encoders + buttons}) == 24, "duplicate topology control ID")

    surface = document["compiled_surface"]
    require(surface["channel"] == 16, "compiled surface is not channel 16")
    require(
        surface["topology"] == {"artifact": TOPOLOGY_ARTIFACT, "sha256": TOPOLOGY_SHA256},
        "compiled surface does not bind the current topology bytes",
    )
    binding = document["surface_assignments"]
    require(len(binding) == 1, "expected one surface assignment")
    require(binding[0]["artifact"] == TOPOLOGY_ARTIFACT, "surface assignment artifact drifted")
    require(binding[0]["sha256"] == TOPOLOGY_SHA256, "surface assignment hash drifted")
    require(binding[0]["channel"] == 16, "surface assignment channel drifted")


def validate_encoders(document: dict[str, Any]) -> None:
    encoders = document["compiled_surface"]["encoders"]
    require(len(encoders) == 16, "expected exactly 16 encoder descriptors")
    require([item["cc"] for item in encoders] == list(range(20, 36)), "encoder CC order/coverage drifted")
    require(len({item["cc"] for item in encoders}) == 16, "duplicate encoder CC")
    require(all(0 <= item["cc"] <= 127 for item in encoders), "encoder CC outside MIDI range")

    assigned = encoders[:11]
    for item, expected in zip(assigned, EXPECTED_ENCODERS, strict=True):
        cc, physical, label, control, midi_curve, source_curve, timing, semantic_default, midi_default, unit = expected
        require(
            set(item)
            == {
                "adapter_owned_default",
                "assigned",
                "cc",
                "control",
                "label",
                "midi_curve",
                "physical_control",
                "source_curve",
                "timing",
                "type",
            },
            f"unexpected encoder fields for CC{cc}",
        )
        require(item["assigned"] is True and item["type"] == "continuous", f"CC{cc} must be assigned continuous")
        require(
            (item["cc"], item["physical_control"], item["label"], item["control"])
            == (cc, physical, label, control),
            f"CC{cc} identity or UI label drifted",
        )
        require(item["midi_curve"] == midi_curve and item["source_curve"] == source_curve, f"CC{cc} curve drifted")
        require(item["timing"] == timing, f"CC{cc} timing drifted")
        default = item["adapter_owned_default"]
        require(
            default == {"midi_value": midi_default, "semantic_value": semantic_default, "unit": unit},
            f"CC{cc} adapter-owned default drifted",
        )
        if unit == "normalized":
            calculated = int((Decimal(str(semantic_default)) * Decimal(127)).quantize(Decimal(1), rounding=ROUND_HALF_UP))
            require(calculated == midi_default, f"CC{cc} default MIDI representation is not half-up rounded")

    for index, item in enumerate(encoders[11:], start=31):
        require(
            item
            == {
                "adapter_owned_default": None,
                "assigned": False,
                "cc": index,
                "control": "unassigned",
                "label": "UNASSIGNED",
                "midi_curve": "none",
                "physical_control": f"bottom-{index - 27}",
                "source_curve": "none",
                "timing": "ignore-and-count",
                "type": "unassigned",
            },
            f"CC{index} must remain visibly unassigned",
        )

    controls = [item["control"] for item in assigned]
    require(len(set(controls)) == len(controls), "duplicate assigned encoder semantic control")
    require(tuple(item["label"] for item in encoders) == tuple(
        ["STAGE 1", "STAGE 2", "STAGE 3", "STAGE 4", "RATE", "MEMORY", "MATERIAL", "POSITION", "FX-A", "FX-B", "ROOT"]
        + ["UNASSIGNED"] * 5
    ), "encoder UI labels drifted")


def validate_buttons(document: dict[str, Any]) -> None:
    buttons = document["compiled_surface"]["buttons"]
    require(len(buttons) == 8, "expected exactly eight button descriptors")
    require([item["cc"] for item in buttons] == list(range(40, 48)), "button CC order/coverage drifted")
    require(len({item["cc"] for item in buttons}) == 8, "duplicate button CC")
    for item, expected in zip(buttons[:7], EXPECTED_BUTTONS, strict=True):
        cc, physical, label, control, gesture = expected
        require(item["assigned"] is True and item["type"] == "action", f"CC{cc} must be assigned action")
        require(
            (item["cc"], item["physical_control"], item["label"], item["control"], item["gesture"])
            == expected,
            f"CC{cc} action descriptor drifted",
        )
        require(item["press_value"] == 127 and item["release_value"] == 0, f"CC{cc} must be momentary 127/0")
    require(
        buttons[7]
        == {
            "assigned": False,
            "cc": 47,
            "control": "unassigned",
            "gesture": "none",
            "label": "UNASSIGNED",
            "physical_control": "button-8",
            "press_value": 127,
            "release_value": 0,
            "type": "unassigned",
        },
        "CC47 must remain visibly unassigned",
    )
    require(len({item["control"] for item in buttons[:7]}) == 7, "duplicate assigned button semantic control")
    require(tuple(item["label"] for item in buttons) == tuple(
        ["SOURCE", "MUTATE", "LOCK", "FREEZE", "FX MODE", "TARGET", "SCALE", "UNASSIGNED"]
    ), "button UI labels drifted")


def validate_semantics_and_defaults(document: dict[str, Any]) -> None:
    preset = document["adapter_owned_desktop_audition_preset"]
    require(preset["owner"] == "desktop-adapter", "audition preset owner is not explicit")
    require(preset["canonical_source_default"] is False, "audition preset was promoted to a source default")
    require(preset["controls"] == PRESET, "adapter-owned desktop audition preset drifted")
    require(
        preset["startup_contract"]
        == "Core::prepare resets to Controls{}; compile-time and runtime tests require those values to equal this map-generated preset, so the JUCE app sends no synthetic startup MIDI.",
        "Core/JUCE startup application contract drifted",
    )
    descriptor_defaults = {
        item["control"]: item["adapter_owned_default"]["semantic_value"]
        for item in document["compiled_surface"]["encoders"]
        if item["assigned"]
    }
    require(descriptor_defaults == PRESET, "descriptor defaults and adapter preset disagree")

    semantic = document["semantic_bindings"]
    assigned = document["compiled_surface"]["encoders"][:11] + document["compiled_surface"]["buttons"][:7]
    require(len(semantic) == 18, "semantic bindings must contain exactly 18 assigned controls")
    require(
        [(item["cc"], item["control"], item["type"]) for item in semantic]
        == [(item["cc"], item["control"], item["type"]) for item in assigned],
        "semantic bindings disagree with compiled descriptors",
    )
    require(semantic[4]["mapping"] == "value/127", "rate MIDI adapter must remain normalized before source curve")
    require(semantic[8]["mapping"] == "value/127 with source soft pickup", "FX-A pickup mapping drifted")
    require(semantic[9]["mapping"] == "value/127 with source soft pickup", "FX-B pickup mapping drifted")
    require(semantic[10]["mapping"] == "round(36 + 36*value/127)", "root mapping drifted")
    require(all(item.get("edge") == "press-127" for item in semantic[11:]), "button action edge drifted")
    require(36 + (85 * 36 + 63) // 127 == 60, "root default MIDI value no longer maps to C4")
    require(
        {item["action"]: item["source_synthesis"] for item in document["gesture_state_machines"]}
        == GESTURE_SYNTHESIS,
        "gesture synthesis counts do not distinguish candidate and matching observations",
    )


def validate_generated_freshness() -> None:
    subprocess.run([sys.executable, str(GENERATOR), "--check"], check=True)
    generated = GENERATED.read_text(encoding="utf-8")
    map_hash = sha256(CONTROL_MAP)
    require(re.search(rf'kControlMapSha256\{{"{map_hash}"\}}', generated) is not None, "generated map fingerprint is stale")
    require(re.search(rf'kControllerTopologySha256\{{"{TOPOLOGY_SHA256}"\}}', generated) is not None, "generated topology fingerprint is stale")
    require("inline constexpr std::uint8_t kMidiChannel{16};" in generated, "generated channel drifted")
    require("inline constexpr Controls kAdapterOwnedDesktopAuditionPreset{" in generated, "generated adapter preset is missing")
    require("inline constexpr Controls kDeclaredCoreStartupControls{};" in generated, "generated Core startup guard is missing")
    require(
        generated.count("static_assert(kDeclaredCoreStartupControls.") == 11,
        "generated Core startup guard does not cover every continuous control",
    )


def main() -> int:
    raw = CONTROL_MAP.read_bytes()
    require(b"\r" not in raw, "control map must use LF line endings")
    require(raw.endswith(b"\n"), "control map must end with a newline")
    document = json.loads(raw)
    require(document["schema_version"] == "sonic-research-lab-control-map-v1", "unexpected control-map schema")
    require(document["status"] == "ready", "control map is not ready")
    require(
        document["source_of_truth"]
        == {
            "artifact": "control-map.json compiled_surface",
            "freshness": "generated header records SHA-256 of the current control-map.json and controller topology bytes",
            "generated_artifact": "generated/control_descriptors.hpp",
            "strategy": "generate",
        },
        "source-of-truth contract drifted",
    )
    validate_topology(document)
    validate_encoders(document)
    validate_buttons(document)
    validate_semantics_and_defaults(document)
    validate_generated_freshness()
    print("Tide Pit control map validated: 16 encoders, 8 buttons, generated header current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
