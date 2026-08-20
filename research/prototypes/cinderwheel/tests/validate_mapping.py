#!/usr/bin/env python3
"""Validate the prototype-only Cinderwheel Launch Control 3 test map."""

from __future__ import annotations

import json
import re
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from typing import Any


FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "launch-control-3-test-map-v0.json"
)
CONTROL_MAP_HEADER = FIXTURE.parents[1] / "include" / "cinderwheel" / "control_map.hpp"

ENCODER_IDS = tuple(
    [f"encoder-top-{index:02d}" for index in range(1, 9)]
    + [f"encoder-bottom-{index:02d}" for index in range(1, 9)]
)
ENCODER_DESTINATIONS = (
    "wave-1",
    "wave-2",
    "wave-3",
    "wave-4",
    "rate",
    "memory",
    "body",
    "position",
    "fx-a",
    "fx-b",
    "root",
    "undertow",
    "pulse-divide",
    "wake",
    "structure",
    "ember",
)
ENCODER_DISPLAY_NAMES = (
    "WAVE1",
    "WAVE2",
    "WAVE3",
    "WAVE4",
    "RATE",
    "MEMORY",
    "BODY",
    "POSITION",
    "FX-A",
    "FX-B",
    "ROOT",
    "UNDERTOW",
    "PULSE DIV",
    "WAKE",
    "STRUCTURE",
    "EMBER",
)
BUTTON_IDS = tuple(f"button-{index:02d}" for index in range(1, 9))
BUTTON_DESTINATIONS = (
    "source-scale",
    "mutate",
    "lock",
    "freeze",
    "fx-mode",
    "wave-target",
    "bloom",
    "reset-panic",
)
BUTTON_DISPLAY_NAMES = (
    "SOURCE",
    "MUTATE",
    "LOCK",
    "FREEZE",
    "FX MODE",
    "TARGET",
    "BLOOM",
    "RESET",
)
DEFAULTS: dict[str, Any] = {
    "body": "0.55",
    "ember": "0",
    "fx-a": "0.5",
    "fx-b": "0.25",
    "memory": "0.65",
    "position": "0.35",
    "pulse-divide": 1,
    "rate": "0.8",
    "root": 48,
    "structure": "0.5",
    "undertow": "off",
    "wake": "0",
    "wave-1": "0.2",
    "wave-2": "0.7",
    "wave-3": "0.35",
    "wave-4": "0.85",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_fixture() -> tuple[bytes, dict[str, Any]]:
    raw = FIXTURE.read_bytes()
    document = json.loads(raw)
    expected = (
        json.dumps(document, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    require(raw == expected, "fixture is not deterministically formatted with sorted keys")
    return raw, document


def recursive_items(value: Any):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key, item
            yield from recursive_items(item)
    elif isinstance(value, list):
        for item in value:
            yield from recursive_items(item)


def validate_noncanonical_boundary(document: dict[str, Any]) -> None:
    require(
        document["schema_version"] == "cinderwheel-launch-control-3-test-map-v0",
        "unexpected prototype mapping schema version",
    )
    require(
        document["artifact_status"]
        == {
            "canonical_schuss_record": False,
            "purpose": "prototype-only simulated controller map",
            "stable_ids_allocated": False,
        },
        "prototype/noncanonical status is not explicit",
    )
    stable_id = re.compile(r"^schuss-[a-z0-9-]+-[0-9]{6}$")
    for key, value in recursive_items(document):
        require(key != "content_hash", "prototype fixture allocated a content hash")
        if isinstance(value, str):
            require(not stable_id.fullmatch(value), "prototype fixture allocated a Schuss stable ID")


def validate_controller_and_mode(document: dict[str, Any]) -> None:
    require(
        document["controller_guard"]
        == {
            "assignable_buttons": 8,
            "endless_encoders": 16,
            "faders": 0,
            "manufacturer": "Novation",
            "model": "Launch Control 3",
            "variant": "regular",
        },
        "controller guard is not the exact regular Launch Control 3 surface",
    )
    require(
        document["custom_mode"]
        == {
            "components_export_created": False,
            "encoder_response": "medium",
            "installation_state": "not-installed",
            "merge_enabled": False,
            "midi_thru_enabled": False,
            "name": "TIDE PIT+",
            "output_ports": ["main-usb-midi"],
            "slot": 1,
        },
        "unexpected Custom Mode trial decision",
    )
    require(
        document["not_modelled"]
        == {
            "components_custom_mode_bytes": "not-modelled",
            "device_endpoint_identity": "not-modelled",
            "encoder_feedback": "not-modelled",
            "oled_feedback": "not-modelled",
            "physical_midi_capture": "not-modelled",
        },
        "device, Components, or feedback proof gap is not explicit",
    )
    surface = document["surface_assignments"]
    require(set(surface) == {"buttons", "encoders"}, "surface includes an unsupported control class")
    require("faders" not in surface, "regular Launch Control 3 map contains faders")
    for _, value in recursive_items(surface):
        if isinstance(value, str):
            require("fader" not in value.lower(), "regular controller map names an XL-style fader")


def validate_event_contract(document: dict[str, Any]) -> None:
    contract = document["event_contract"]
    require(contract["protocol"] == "midi-1.0-channel-voice", "unexpected MIDI protocol")
    require(contract["accepted_message_kind"] == "control-change", "only CC is accepted")
    require(contract["channel"] == 16, "mapping must use one-based MIDI channel 16")
    require(contract["sample_rate_hz"] == 48000, "trial sample rate must be 48 kHz")
    require(
        contract["ordering"] == ["sample_timestamp", "ingress_sequence"],
        "event ordering must be sample timestamp then ingress sequence",
    )
    require(
        contract["unknown_message_policy"]
        == {
            "action": "ignore",
            "counter": "ignored-midi-message-count",
            "includes": [
                "malformed-data-byte",
                "other-channel",
                "other-message-kind",
                "unassigned-controller-number",
            ],
        },
        "unknown MIDI policy is not fail-closed and counted",
    )


def validate_surface_assignments(document: dict[str, Any]) -> tuple[set[int], set[int]]:
    surface = document["surface_assignments"]
    encoders = surface["encoders"]
    buttons = surface["buttons"]
    require(len(encoders) == 16, "mapping must contain exactly 16 encoders")
    require(len(buttons) == 8, "mapping must contain exactly eight buttons")
    require(tuple(item["control_id"] for item in encoders) == ENCODER_IDS, "encoder order/coverage drifted")
    require(tuple(item["control_id"] for item in buttons) == BUTTON_IDS, "button order/coverage drifted")
    require(tuple(item["cc"] for item in encoders) == tuple(range(20, 36)), "encoders must use CC20-35")
    require(tuple(item["cc"] for item in buttons) == tuple(range(40, 48)), "buttons must use CC40-47")
    require(
        tuple(item["display_name"] for item in encoders) == ENCODER_DISPLAY_NAMES,
        "encoder display labels drifted",
    )
    require(
        tuple(item["display_name"] for item in buttons) == BUTTON_DISPLAY_NAMES,
        "button display labels drifted",
    )

    selectors: set[tuple[str, int, int]] = set()
    ids: set[str] = set()
    for item in encoders:
        require(
            set(item)
            == {
                "cc",
                "channel",
                "control_id",
                "display_name",
                "message_kind",
                "resolution_bits",
                "value_mode",
                "value_range",
            },
            f"unexpected encoder fields for {item.get('control_id')}",
        )
        require(item["channel"] == 16, "encoder is not on channel 16")
        require(item["message_kind"] == "control-change", "encoder is not a CC")
        require(item["resolution_bits"] == 7, "encoder is not explicitly 7-bit")
        require(item["value_mode"] == "absolute", "encoder is not explicitly absolute")
        require(item["value_range"] == {"maximum": 127, "minimum": 0}, "encoder range is not 0-127")
        selector = (item["message_kind"], item["channel"], item["cc"])
        require(selector not in selectors, f"duplicate MIDI selector {selector}")
        require(item["control_id"] not in ids, f"duplicate control ID {item['control_id']}")
        selectors.add(selector)
        ids.add(item["control_id"])

    for item in buttons:
        require(
            set(item)
            == {
                "cc",
                "channel",
                "control_id",
                "display_name",
                "message_kind",
                "off_value",
                "on_value",
                "value_mode",
            },
            f"unexpected button fields for {item.get('control_id')}",
        )
        require(item["channel"] == 16, "button is not on channel 16")
        require(item["message_kind"] == "control-change", "button is not a CC")
        require(item["value_mode"] == "momentary", "button is not momentary")
        require(item["on_value"] == 127 and item["off_value"] == 0, "button press/release is not 127/0")
        selector = (item["message_kind"], item["channel"], item["cc"])
        require(selector not in selectors, f"duplicate MIDI selector {selector}")
        require(item["control_id"] not in ids, f"duplicate control ID {item['control_id']}")
        selectors.add(selector)
        ids.add(item["control_id"])

    return {item["cc"] for item in encoders}, {item["cc"] for item in buttons}


def normalized_mapping() -> dict[str, Any]:
    return {
        "curve": "linear",
        "formula": "value / 127",
        "input": {"maximum": 127, "minimum": 0, "unit": "midi-7-bit"},
        "output": {"maximum": "1", "minimum": "0", "unit": "normalized"},
    }


def expected_mapping(destination: str) -> dict[str, Any]:
    if destination == "rate":
        return {
            "curve": "exponential",
            "formula": "0.08 * pow(75, value / 127)",
            "input": {"maximum": 127, "minimum": 0, "unit": "midi-7-bit"},
            "output": {"maximum": "6", "minimum": "0.08", "unit": "cycles-per-second"},
        }
    if destination == "root":
        return {
            "curve": "quantized",
            "formula": "36 + round_half_up(36 * value / 127)",
            "input": {"maximum": 127, "minimum": 0, "unit": "midi-7-bit"},
            "output": {"maximum": 72, "minimum": 36, "unit": "midi-note"},
        }
    if destination == "undertow":
        return {
            "curve": "quantized",
            "formula": "value == 0 ? off : 1 + floor((value - 1) * 16 / 127)",
            "input": {"maximum": 127, "minimum": 0, "unit": "midi-7-bit"},
            "output": {"states": ["off", *range(1, 17)], "unit": "frequency-divisor"},
        }
    if destination == "pulse-divide":
        return {
            "curve": "quantized",
            "formula": "1 + floor((15 * value + 63) / 127)",
            "input": {"maximum": 127, "minimum": 0, "unit": "midi-7-bit"},
            "output": {"maximum": 16, "minimum": 1, "unit": "stage-transitions"},
        }
    return normalized_mapping()


def expected_application(destination: str) -> dict[str, Any]:
    if destination == "rate":
        return {"smoothing_ms": 20, "timing": "immediate-phase-continuous"}
    if destination in {"fx-a", "fx-b"}:
        return {"smoothing_ms": 20, "timing": "immediate-after-takeover"}
    if destination in {"root", "undertow"}:
        return {"crossfade_ms": 0, "smoothing_ms": 0, "timing": "next-stage-transition"}
    if destination == "pulse-divide":
        return {
            "crossfade_ms": 0,
            "smoothing_ms": 0,
            "timing": "next-stage-transition-phase-preserved",
        }
    if destination == "wake":
        return {"smoothing_ms": 20, "timing": "immediate-zero-clears-pending-energy"}
    if destination == "ember":
        return {"smoothing_ms": 20, "timing": "immediate-zero-disables-afterstrikes"}
    return {"smoothing_ms": 20, "timing": "immediate"}


def validate_encoder_semantics(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    bindings = document["semantic_bindings"]["encoders"]
    require(len(bindings) == 16, "semantic map must cover all 16 encoders")
    require(tuple(item["control_id"] for item in bindings) == ENCODER_IDS, "semantic encoder order drifted")
    require(
        tuple(item["destination"] for item in bindings) == ENCODER_DESTINATIONS,
        "semantic encoder destinations drifted",
    )
    require(len(set(item["destination"] for item in bindings)) == 16, "duplicate encoder destination")
    by_id = {item["control_id"]: item for item in bindings}
    for item in bindings:
        destination = item["destination"]
        require(set(item) == {"application", "control_id", "default", "destination", "mapping", "takeover"}, f"unexpected semantic fields for {destination}")
        require(item["default"] == DEFAULTS[destination], f"unexpected default for {destination}")
        require(item["mapping"] == expected_mapping(destination), f"mapping math drifted for {destination}")
        require(item["application"] == expected_application(destination), f"application timing drifted for {destination}")
        if destination in {"fx-a", "fx-b"}:
            require(
                item["takeover"]
                == {
                    "arming": "fx-mode-change-or-state-recall",
                    "mode": "soft-crossing",
                    "threshold_midi_steps": 2,
                },
                f"soft takeover drifted for {destination}",
            )
        else:
            require(item["takeover"] == "none", f"unexpected takeover for {destination}")

        mapping = item["mapping"]
        if mapping["curve"] in {"linear", "exponential"}:
            default = Decimal(str(item["default"]))
            minimum = Decimal(mapping["output"]["minimum"])
            maximum = Decimal(mapping["output"]["maximum"])
            require(minimum <= default <= maximum, f"default outside range for {destination}")
        elif destination == "root":
            require(36 <= item["default"] <= 72, "Root default outside MIDI 36-72")
        elif destination == "undertow":
            require(item["default"] in mapping["output"]["states"], "Undertow default is not a state")
        elif destination == "pulse-divide":
            require(1 <= item["default"] <= 16, "Pulse Divide default outside 1-16")
    return by_id


def validate_button_semantics(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    bindings = document["semantic_bindings"]["buttons"]
    require(len(bindings) == 8, "semantic map must cover all eight buttons")
    require(tuple(item["control_id"] for item in bindings) == BUTTON_IDS, "semantic button order drifted")
    require(
        tuple(item["destination"] for item in bindings) == BUTTON_DESTINATIONS,
        "semantic button destinations drifted",
    )
    require(len(set(item["destination"] for item in bindings)) == 8, "duplicate button destination")
    by_id = {item["control_id"]: item for item in bindings}

    source = by_id["button-01"]
    require(source["default"] == {"scale": "minor-pentatonic", "source": "REED"}, "Source/Scale default drifted")
    source_gesture = source["gesture"]
    require(source_gesture["short_release_states"] == ["REED", "RND", "FOLD", "DUST"], "source cycle drifted")
    require(
        [(item["name"], item["semitones"]) for item in source_gesture["hold_states"]]
        == [
            ("minor-pentatonic", [0, 3, 5, 7, 10, 12, 15, 17]),
            ("dorian", [0, 2, 3, 5, 7, 9, 10, 12]),
            ("harmonic-minor", [0, 2, 3, 5, 7, 8, 11, 12]),
            ("fifths", [0, 7, 12, 19, 24, 31, 36, 43]),
        ],
        "scale cycle drifted",
    )
    require(
        source_gesture["hold_threshold_samples"] == 28800
        and source_gesture["short_release_max_samples"] == 28799,
        "600 ms Source/Scale boundary drifted",
    )
    require(source_gesture["hold_action"] == "scale-cycle", "Source/Scale hold action drifted")
    require(source_gesture["short_release_action"] == "source-cycle", "Source/Scale tap action drifted")
    require(source_gesture["release_after_hold_action"] == "none", "Source/Scale release retriggers")

    require(
        by_id["button-02"]["gesture"]
        == {"action": "bounded-mutation", "edge": "press", "release_action": "none"},
        "Mutate gesture drifted",
    )
    for control_id, destination in (("button-03", "lock"), ("button-04", "freeze")):
        item = by_id[control_id]
        require(item["destination"] == destination and item["default"] is False, f"{destination} default drifted")
        require(
            item["gesture"]
            == {"edge": "tap-release", "kind": "toggle", "press_action": "none", "states": [False, True]},
            f"{destination} toggle semantics drifted",
        )
    require(
        by_id["button-05"]["gesture"]
        == {
            "edge": "tap-release",
            "kind": "cycle",
            "press_action": "none",
            "states": ["CLEAN", "FILT", "DRIVE"],
        },
        "FX mode cycle drifted",
    )
    require(
        by_id["button-06"]["gesture"]
        == {
            "edge": "tap-release",
            "kind": "cycle",
            "press_action": "none",
            "states": ["PITCH", "BODY", "GRAIN", "ALL"],
        },
        "Wave Target cycle drifted",
    )
    require(
        by_id["button-07"]["gesture"]
        == {
            "action": "arm-one-next-transition-token",
            "edge": "press",
            "release_action": "none",
            "retention": "pending-until-next-stage-transition-or-reset-panic",
        },
        "Bloom gesture drifted",
    )
    panic = by_id["button-08"]["gesture"]
    require(
        panic["hold_threshold_samples"] == 57600
        and panic["short_release_max_samples"] == 57599,
        "1200 ms Reset/Panic boundary drifted",
    )
    require(panic["hold_action"] == "panic", "Panic hold action drifted")
    require(panic["short_release_action"] == "reset", "Reset tap action drifted")
    require(panic["release_after_hold_action"] == "none", "Panic release retriggers Reset")

    sample_rate = document["event_contract"]["sample_rate_hz"]
    require(28800 == sample_rate * 600 // 1000, "600 ms threshold is not on sample timeline")
    require(57600 == sample_rate * 1200 // 1000, "1200 ms threshold is not on sample timeline")
    return by_id


def evaluate_encoder(binding: dict[str, Any], value: int) -> str:
    require(isinstance(value, int) and not isinstance(value, bool), "encoder value is not an integer")
    require(0 <= value <= 127, "encoder value outside MIDI 7-bit range")
    destination = binding["destination"]
    if binding["mapping"]["curve"] == "linear":
        result = Fraction(value, 127)
        return str(result.numerator) if result.denominator == 1 else f"{result.numerator}/{result.denominator}"
    if destination == "rate":
        if value == 0:
            return "0.08"
        if value == 127:
            return "6"
        raise AssertionError("rate validation vectors must use exact endpoints")
    if destination == "root":
        scaled = Fraction(36 * value, 127)
        rounded = (2 * scaled.numerator + scaled.denominator) // (2 * scaled.denominator)
        return str(36 + rounded)
    if destination == "undertow":
        state = 0 if value == 0 else 1 + ((value - 1) * 16) // 127
        if state == 0:
            return "off"
        return str(state)
    if destination == "pulse-divide":
        return str(1 + (15 * value + 63) // 127)
    raise AssertionError(f"no evaluator for {destination}")


def gesture_action(binding: dict[str, Any], phase: str, held_samples: int) -> str:
    gesture = binding["gesture"]
    if phase == "hold" and held_samples >= gesture["hold_threshold_samples"]:
        return gesture["hold_action"]
    if phase == "release" and held_samples <= gesture["short_release_max_samples"]:
        return gesture["short_release_action"]
    return "none"


def accepts_message(
    message: dict[str, Any], encoder_ccs: set[int], button_ccs: set[int]
) -> bool:
    value = message["value"]
    if (
        message["kind"] != "control-change"
        or message["channel"] != 16
        or not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 127
    ):
        return False
    cc = message["cc"]
    if cc in encoder_ccs:
        return True
    if cc in button_ccs:
        return value in {0, 127}
    return False


def validate_vectors(
    document: dict[str, Any],
    encoders: dict[str, dict[str, Any]],
    buttons: dict[str, dict[str, Any]],
    encoder_ccs: set[int],
    button_ccs: set[int],
) -> None:
    vectors = document["validation_vectors"]
    boundaries = vectors["encoder_boundaries"]
    require(len(boundaries) == 32, "must retain two endpoint vectors for every encoder")
    seen: set[tuple[str, int]] = set()
    for vector in boundaries:
        key = (vector["control_id"], vector["input"])
        require(key not in seen, f"duplicate encoder boundary vector {key}")
        seen.add(key)
        require(vector["control_id"] in encoders, f"unknown vector control {vector['control_id']}")
        require(
            evaluate_encoder(encoders[vector["control_id"]], vector["input"])
            == vector["expected"],
            f"encoder boundary vector failed for {key}",
        )
    require(
        seen == {(control_id, value) for control_id in ENCODER_IDS for value in (0, 127)},
        "encoder boundary vectors are not exhaustive",
    )

    undertow = encoders["encoder-bottom-04"]
    require(evaluate_encoder(undertow, 0) == "off", "Undertow Off boundary drifted")
    require(evaluate_encoder(undertow, 1) == "1", "Undertow divisor 1 lower boundary drifted")
    require(evaluate_encoder(undertow, 8) == "1", "Undertow divisor 1 upper boundary drifted")
    require(evaluate_encoder(undertow, 9) == "2", "Undertow divisor 2 lower boundary drifted")
    require(evaluate_encoder(undertow, 120) == "15", "Undertow divisor 15 upper boundary drifted")
    require(evaluate_encoder(undertow, 121) == "16", "Undertow divisor 16 lower boundary drifted")
    pulse = encoders["encoder-bottom-05"]
    require(evaluate_encoder(pulse, 4) == "1", "Pulse Divide 1 upper boundary drifted")
    require(evaluate_encoder(pulse, 5) == "2", "Pulse Divide 2 lower boundary drifted")
    require(evaluate_encoder(pulse, 122) == "15", "Pulse Divide 15 upper boundary drifted")
    require(evaluate_encoder(pulse, 123) == "16", "Pulse Divide 16 lower boundary drifted")

    gesture_vectors = vectors["gesture_boundaries"]
    require(len(gesture_vectors) == 4, "expected four tap/hold boundary vectors")
    for vector in gesture_vectors:
        binding = buttons[vector["control_id"]]
        require(
            gesture_action(binding, vector["phase"], vector["held_samples"])
            == vector["expected_action"],
            f"gesture boundary vector failed for {vector['control_id']}",
        )
    require(
        gesture_action(buttons["button-01"], "release", 28800) == "none",
        "Source/Scale release at hold threshold must not retrigger",
    )
    require(
        gesture_action(buttons["button-08"], "release", 57600) == "none",
        "Reset/Panic release at hold threshold must not retrigger",
    )

    for message in vectors["ignored_messages"]:
        require(
            not accepts_message(message, encoder_ccs, button_ccs),
            f"ignored-message vector was accepted: {message}",
        )
    require(
        accepts_message(
            {"cc": 20, "channel": 16, "kind": "control-change", "value": 64},
            encoder_ccs,
            button_ccs,
        ),
        "valid encoder message was rejected",
    )
    require(
        accepts_message(
            {"cc": 40, "channel": 16, "kind": "control-change", "value": 127},
            encoder_ccs,
            button_ccs,
        )
        and accepts_message(
            {"cc": 40, "channel": 16, "kind": "control-change", "value": 0},
            encoder_ccs,
            button_ccs,
        ),
        "valid momentary button message was rejected",
    )
    require(
        not accepts_message(
            {"cc": 40, "channel": 16, "kind": "control-change", "value": 64},
            encoder_ccs,
            button_ccs,
        ),
        "non-momentary button value was accepted",
    )

    ordering = vectors["ordering"]
    observed = [
        item["ingress_sequence"]
        for item in sorted(
            ordering["input"],
            key=lambda item: (item["sample_timestamp"], item["ingress_sequence"]),
        )
    ]
    require(observed == ordering["expected_ingress_sequence"], "ordering vector failed")


def validate_trial_decisions(document: dict[str, Any]) -> None:
    require(
        set(document["trial_decisions"])
        == {
            "button_gesture_boundaries",
            "controller_mode",
            "encoder_encoding",
            "mapping_defaults",
            "parameter_curves",
            "routing",
            "soft_takeover",
        },
        "trial decision ledger is incomplete",
    )


def validate_cpp_descriptor_linkage(document: dict[str, Any]) -> None:
    source = CONTROL_MAP_HEADER.read_text(encoding="utf-8")
    encoder_pattern = re.compile(
        r'\{ControlId::([a-z0-9_]+),\s*(\d+),\s*"[^"]+",\s*"([^"]+)",\s*'
        r'"([^"]+)",\s*ControlShape::([a-z]+),\s*([0-9.]+)\},'
    )
    button_pattern = re.compile(
        r'\{ControlId::([a-z0-9_]+),\s*(\d+),\s*"[^"]+",\s*"([^"]+)",\s*'
        r'"([^"]+)",\s*(\d+)\},'
    )
    cpp_encoders = encoder_pattern.findall(source)
    cpp_buttons = button_pattern.findall(source)
    require(len(cpp_encoders) == 16, "C++ map must expose exactly 16 encoder descriptors")
    require(len(cpp_buttons) == 8, "C++ map must expose exactly eight button descriptors")

    surface_encoders = document["surface_assignments"]["encoders"]
    semantic_encoders = document["semantic_bindings"]["encoders"]
    stepped = {"root", "undertow", "pulse-divide"}
    for cpp, surface, semantic in zip(cpp_encoders, surface_encoders, semantic_encoders):
        control, cc, label, destination, shape, _ = cpp
        require(int(cc) == surface["cc"], f"C++ CC drift for {destination}")
        require(label == surface["display_name"], f"C++ label drift for {destination}")
        require(destination == semantic["destination"], f"C++ destination drift for {destination}")
        require(control.replace("_", "-") == destination, f"C++ ControlId drift for {destination}")
        expected_shape = "stepped" if destination in stepped else "continuous"
        require(shape == expected_shape, f"C++ control shape drift for {destination}")

    surface_buttons = document["surface_assignments"]["buttons"]
    semantic_buttons = document["semantic_bindings"]["buttons"]
    for cpp, surface, semantic in zip(cpp_buttons, surface_buttons, semantic_buttons):
        control, cc, label, destination, hold_ms = cpp
        require(int(cc) == surface["cc"], f"C++ button CC drift for {destination}")
        require(label == surface["display_name"], f"C++ button label drift for {destination}")
        require(destination == semantic["destination"], f"C++ button destination drift for {destination}")
        require(control.replace("_", "-") == destination, f"C++ button ControlId drift for {destination}")
        gesture = semantic["gesture"]
        expected_hold_ms = int(gesture.get("hold_threshold_samples", 0) / 48)
        require(int(hold_ms) == expected_hold_ms, f"C++ hold threshold drift for {destination}")
    require(
        all(isinstance(value, str) and value for value in document["trial_decisions"].values()),
        "trial decisions must be explicit nonempty text",
    )


def main() -> None:
    _, document = load_fixture()
    validate_noncanonical_boundary(document)
    validate_controller_and_mode(document)
    validate_event_contract(document)
    encoder_ccs, button_ccs = validate_surface_assignments(document)
    encoders = validate_encoder_semantics(document)
    buttons = validate_button_semantics(document)
    validate_trial_decisions(document)
    validate_cpp_descriptor_linkage(document)
    validate_vectors(document, encoders, buttons, encoder_ccs, button_ccs)
    print(
        "validate_mapping: passed "
        "(16 encoders, 8 buttons, 32 encoder boundaries, 4 gesture boundaries)"
    )


if __name__ == "__main__":
    main()
