#!/usr/bin/env python3
"""Generate the exact Task 018 Gills panel, mapping, and runtime closure."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/contracts")]

from packages.schuss_core.build_execution import descriptor_content_hash  # noqa: E402

import record_set_rules  # noqa: E402
import validator_core as core  # noqa: E402


PARENT = ROOT / "contracts/record-sets/task017-curated-core-v1.json"
OUTPUT = ROOT / "contracts/record-sets/task018-full-gills-v1.json"
RECORD_ROOT = ROOT / "contracts/task018"

HARDWARE_REPOSITORY = "https://github.com/ksoloti/ksoloti-gills"
HARDWARE_COMMIT = "280503036aee95e6c6ef91a1f1357443f4768faa"
OBJECT_REPOSITORY = "https://github.com/ksoloti/ksoloti-objects"
OBJECT_COMMIT = "3e236e503f490e2bb93187b9cbaf06781dd88b8b"

TARGET_REFERENCE = {
    "compute_target_id": "schuss-compute-target-000001",
    "revision": 2,
    "content_hash": "sha256:d8a9652bd079d0f2a8806cc4922f2a380c8092549f267047d5a4a0360b4a6753",
}
FIRMWARE_REFERENCE = {
    "build_environment_id": "schuss-build-environment-000002",
    "revision": 2,
    "content_hash": "sha256:a656a898798cad529dfec7b02f0a881b61b93e150dd0788b7028ec8e5e4ce2df",
}

SOURCE_SPECS = (
    (1, HARDWARE_REPOSITORY, HARDWARE_COMMIT, "README.md", "dcb827b02afa3ffb7108de81fdec229b4c16b6a1c876a223b96334e32e07d21d", "hardware-design-source", "no per-file declaration; repository license is recorded separately"),
    (2, HARDWARE_REPOSITORY, HARDWARE_COMMIT, "LICENSE", "9e5f1b3c610b9c2da5c313bf81d577a7d1acec686bdb0384edefa6df0f90cd94", "repository-license-source", "CC BY 4.0 license text for the hardware repository"),
    (3, HARDWARE_REPOSITORY, HARDWARE_COMMIT, "ksoloti-gills.kicad_sch", "05aaaee1fd8f43815d8124fc239174fd10f1c78f2270d4a137a78f4bfa8e8b93", "hardware-design-source", "no per-file declaration; repository license is recorded separately"),
    (4, HARDWARE_REPOSITORY, HARDWARE_COMMIT, "pots.kicad_sch", "57f1e7a378b53703138cb06b454aa53ed6cb2c0b73a787111cbc0f74815f171d", "hardware-design-source", "no per-file declaration; repository license is recorded separately"),
    (5, HARDWARE_REPOSITORY, HARDWARE_COMMIT, "leds_switches.kicad_sch", "d90aaf34532f163cde7f88d9c47c0f85ec221db34232a4bc18dd3579bf5e1911", "hardware-design-source", "no per-file declaration; repository license is recorded separately"),
    (6, HARDWARE_REPOSITORY, HARDWARE_COMMIT, "audio_io.kicad_sch", "0e956278c057c88f5083b7a17a135e010413d2c1de9943ec27fc151dc1d3b416", "hardware-design-source", "no per-file declaration; repository license is recorded separately"),
    (7, HARDWARE_REPOSITORY, HARDWARE_COMMIT, "midi.kicad_sch", "b67412f1ea883c5f723f0c531bb2936ef199906fcc43c6ca559d78b38b943743", "hardware-design-source", "no per-file declaration; repository license is recorded separately"),
    (8, HARDWARE_REPOSITORY, HARDWARE_COMMIT, "cv.kicad_sch", "a38a52d3eff023ac1406b38ca9051ac014843cf61d740fd4d0da2af54d1ea399", "hardware-design-source", "no per-file declaration; repository license is recorded separately"),
    (9, HARDWARE_REPOSITORY, HARDWARE_COMMIT, "digital_mic.kicad_sch", "34bd5212d49fe53a049f984c0b9b9eb5ddb48883616eb49b244825d13fc23026", "hardware-design-source", "no per-file declaration; repository license is recorded separately"),
    (10, HARDWARE_REPOSITORY, HARDWARE_COMMIT, "power.kicad_sch", "34ac2a4bdc2d907b8a55e7c59c11571ad49fe02ff8012ff00d5a7caba1f3f78a", "hardware-design-source", "no per-file declaration; repository license is recorded separately"),
    (11, HARDWARE_REPOSITORY, HARDWARE_COMMIT, "changelog.kicad_sch", "e2aad255ef01d76937ad1d5620363c7a00c7fdac1d2e50cf56dc2b87f2d63ef8", "hardware-design-source", "no per-file declaration; repository license is recorded separately"),
    (12, HARDWARE_REPOSITORY, HARDWARE_COMMIT, "jlcpcb/production_files/BOM-ksoloti-gills.csv", "ad97afdf7b08989eb3569f2d89d894e8207d81754d93caedbb222ce83b8c7472", "assembly-source", "no per-file declaration; repository license is recorded separately"),
    (13, HARDWARE_REPOSITORY, HARDWARE_COMMIT, "ksoloti-gills.kicad_pcb", "46b23d6a11ad74d6971958d77ababa976d4f33e6f883a3d7dd9153b23309b8f4", "hardware-design-source", "no per-file declaration; repository license is recorded separately"),
    (14, HARDWARE_REPOSITORY, HARDWARE_COMMIT, "ksoloti-gills_panel/ksoloti-gills_panel.kicad_pcb", "348e22c25b7b54bd9db989c581408ed7429b9d7c2df65f19e8beb6a99b0368c4", "hardware-design-source", "no per-file declaration; repository license is recorded separately"),
    (15, OBJECT_REPOSITORY, OBJECT_COMMIT, "objects/ksoloti/gills/pot p.axo", "716a829ab2a0e2eb96dbf88179a871cf87db77c9cbfe6640665bfd2e10c45917", "runtime-object-source", "BSD declared by the object metadata"),
    (16, OBJECT_REPOSITORY, OBJECT_COMMIT, "objects/ksoloti/gills/button.axo", "a59aa7746210ec0289b6760c38dfd0b2bfed19ddae9377af395e058892444d02", "runtime-object-source", "BSD declared by the object metadata"),
    (17, OBJECT_REPOSITORY, OBJECT_COMMIT, "objects/ksoloti/gills/encoder.axo", "3f7a3a60dcd10133f6727bb0cc2934aecf1288509712540e63ab08e90fafff44", "runtime-object-source", "BSD declared by the object metadata"),
    (18, OBJECT_REPOSITORY, OBJECT_COMMIT, "objects/ksoloti/gills/led.axo", "7b5306a2da128144a7024a53b35062c5ec1d50844e05265ee689fa2fff50e1cf", "runtime-object-source", "BSD declared by the object metadata"),
    (19, OBJECT_REPOSITORY, OBJECT_COMMIT, "objects/ksoloti/gills/display.axo", "7cd2b0889175b07149d99e96f1f189ef4687a1f36eeb93409fb495f8c90c676b", "runtime-object-source", "GPL v3.0 declared by the object metadata"),
    (20, OBJECT_REPOSITORY, OBJECT_COMMIT, "objects/ksoloti/gills/pot denoise p.axo", "6b0bf649a55f6b48d8f5112c1d48bdf0b9560d0b19e6d11a73f6d90f700ceacb", "runtime-object-source", "GPL 3.0 declared by the object metadata"),
    (21, OBJECT_REPOSITORY, OBJECT_COMMIT, "objects/ksoloti/gills/responsiveAnalogRead.h", "48e6436b439198661565e31f7c927d87593ae53ec75a064f9d9d3b2201aef93b", "runtime-object-source", "no per-file declaration; repository license is recorded separately"),
    (22, OBJECT_REPOSITORY, OBJECT_COMMIT, "objects/ksoloti/gills/led pwm.axo", "e642bac8151246b5ceae8c9505c0d44f6f2610f6b1c41c8c3a4975c4bcf56dc6", "runtime-object-source", "BSD declared by the object metadata"),
    (23, OBJECT_REPOSITORY, OBJECT_COMMIT, "objects/ksoloti/gills/font5x8_offset.h", "965c989cc89e65a0e98f9591e13e614b8f8579a21562dd17af0d5d1df0a790f9", "runtime-object-source", "no per-file declaration; repository license is recorded separately"),
    (24, OBJECT_REPOSITORY, OBJECT_COMMIT, "LICENSE", "53927bd0b739d38c87a0a82236fd9b070c2dfff11c0c119be50372005d5047ad", "repository-license-source", "GPL v3.0 license text for the objects repository; not treated as a per-file declaration"),
)


def _record(value: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(value)
    result["content_hash"] = "sha256:" + "0" * 64
    errors = core.schema_errors(result, schema, schema)
    if errors:
        raise ValueError("; ".join(errors))
    result["content_hash"] = core.record_content_hash(result, schema)
    return result


def _ref(record: dict[str, Any], id_field: str) -> dict[str, Any]:
    return {
        id_field: record[id_field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def _known_range(minimum: str, maximum: str, unit: str) -> dict[str, Any]:
    return {"status": "known", "range": {"minimum": minimum, "maximum": maximum, "unit": unit}}


def _known_resolution(steps: int) -> dict[str, Any]:
    return {"status": "known", "steps": steps}


def _unresolved(fact: int) -> dict[str, Any]:
    return {"status": "unresolved", "unresolved_fact_id": f"unresolved-fact-{fact:06d}"}


def _capability(value: str) -> dict[str, Any]:
    return {"status": "known", "capability": value}


def _source_ref(number: int, locator: str) -> dict[str, Any]:
    return {"source_id": f"panel-source-{number:06d}", "locator": locator}


def _fact(key: str, value: str, *references: tuple[int, str], status: str = "observed") -> dict[str, Any]:
    return {
        "key": key,
        "value": value,
        "status": status,
        "evidence_refs": [_source_ref(number, locator) for number, locator in references],
    }


def _input_control(
    number: int,
    label: str,
    control_kind: str,
    physical_form: str,
    output_domain: str,
    logical_range: dict[str, str],
    physical_range: dict[str, Any],
    resolution: dict[str, Any],
) -> dict[str, Any]:
    return {
        "slot_id": f"device-input-{number:06d}",
        "display_label": label,
        "control_kind": control_kind,
        "physical_form": physical_form,
        "output_domain": output_domain,
        "logical_range": logical_range,
        "physical_range": physical_range,
        "resolution": resolution,
    }


def _device(schema: dict[str, Any]) -> dict[str, Any]:
    normalized = {"minimum": "0", "maximum": "1", "unit": "normalized"}
    boolean = {"minimum": "0", "maximum": "1", "unit": "boolean"}
    relative = {"minimum": "-1", "maximum": "1", "unit": "steps"}
    inputs = [
        _input_control(index, f"Performance Pot {index}", "absolute", "knob", "normalized-position", normalized, _known_range("0", "4095", "raw-count"), _known_resolution(4096))
        for index in range(1, 11)
    ]
    inputs.extend(
        _input_control(10 + index, f"Button {index}", "discrete", "button", "binary-state", boolean, _known_range("0", "1", "boolean"), _known_resolution(2))
        for index in range(1, 5)
    )
    inputs.extend([
        _input_control(15, "Encoder Turn", "relative", "encoder", "relative-step", relative, _known_range("-1", "1", "steps"), _known_resolution(3)),
        _input_control(16, "Encoder Push", "discrete", "button", "binary-state", boolean, _known_range("0", "1", "boolean"), _known_resolution(2)),
        _input_control(17, "Input Volume", "absolute", "knob", "normalized-position", normalized, _unresolved(1), _unresolved(1)),
        _input_control(18, "Output Volume", "absolute", "knob", "normalized-position", normalized, _unresolved(1), _unresolved(1)),
        _input_control(19, "Power Switch", "discrete", "switch", "binary-state", boolean, _known_range("0", "1", "boolean"), _known_resolution(2)),
    ])
    gestures = []
    gesture_number = 1
    for button in range(11, 15):
        for kind, capability in (("press", "edge-detected-gesture"), ("release", "edge-detected-gesture"), ("hold", "hold-duration-gesture")):
            gestures.append({
                "gesture_id": f"device-gesture-{gesture_number:06d}",
                "display_label": f"Button {button - 10} {kind.title()}",
                "gesture_kind": kind,
                "source_control_ids": [f"device-input-{button:06d}"],
                "recognition": _capability(capability),
            })
            gesture_number += 1
    gestures.append({
        "gesture_id": "device-gesture-000013",
        "display_label": "Encoder Turn",
        "gesture_kind": "turn",
        "source_control_ids": ["device-input-000015"],
        "recognition": _capability("relative-turn-gesture"),
    })
    for number, kind, capability in (
        (14, "press", "edge-detected-gesture"),
        (15, "release", "edge-detected-gesture"),
        (16, "hold", "hold-duration-gesture"),
    ):
        gestures.append({
            "gesture_id": f"device-gesture-{number:06d}",
            "display_label": f"Encoder Push {kind.title()}",
            "gesture_kind": kind,
            "source_control_ids": ["device-input-000016"],
            "recognition": _capability(capability),
        })
    feedback = [
        {
            "slot_id": f"device-feedback-{number:06d}",
            "display_label": label,
            "feedback_kind": "indicator",
            "direction": "instrument-to-device",
            "capability": _capability("binary-indicator-output"),
        }
        for number, label in enumerate(("LED 1 Green", "LED 2 Red", "LED 3 Color A", "LED 3 Red", "LED 4 Color A", "LED 4 Red"), 1)
    ]
    displays = [
        {"slot_id": "device-display-000001", "display_label": "OLED Text", "display_kind": "text", "direction": "instrument-to-device", "capability": _capability("text-output")},
        {"slot_id": "device-display-000002", "display_label": "OLED Graphics", "display_kind": "graphics", "direction": "instrument-to-device", "capability": _capability("graphics-output")},
    ]
    io_specs = (
        (1, "Line Input Left", "audio", "input", _capability("audio-signal")),
        (2, "Line Input Right", "audio", "input", _capability("audio-signal")),
        (3, "Line Output Left", "audio", "output", _capability("audio-signal")),
        (4, "Line Output Right", "audio", "output", _capability("audio-signal")),
        (5, "Headphone Output", "audio", "output", _capability("audio-signal")),
        (6, "Configurable MIDI DIN", "midi", "bidirectional", _capability("midi-messages")),
        (7, "MIDI Output DIN", "midi", "output", _capability("midi-messages")),
        (8, "Expansion Jack 1", "cv", "bidirectional", _unresolved(2)),
        (9, "Expansion Jack 2", "cv", "bidirectional", _unresolved(2)),
        (10, "Gate Output Jack", "cv", "output", _unresolved(2)),
        (11, "Core SD Slot", "generic", "bidirectional", _unresolved(3)),
        (12, "Core USB Device", "generic", "bidirectional", _unresolved(3)),
        (13, "Core USB Host", "generic", "bidirectional", _unresolved(3)),
        (14, "DC Power Input", "generic", "input", _capability("generic-io")),
        (15, "Output Insert Header", "audio", "bidirectional", _capability("audio-signal")),
        (16, "PDM Microphone Header", "generic", "input", _unresolved(4)),
        (17, "CV Expansion Header", "cv", "bidirectional", _unresolved(2)),
        (18, "Headphone Pot Header", "generic", "bidirectional", _unresolved(4)),
        (19, "Line I/O Header", "audio", "bidirectional", _capability("audio-signal")),
        (20, "Power Header", "generic", "bidirectional", _capability("generic-io")),
    )
    physical_io = [
        {"slot_id": f"device-physical-io-{number:06d}", "display_label": label, "io_kind": kind, "direction": direction, "capability": capability}
        for number, label, kind, direction, capability in io_specs
    ]
    unresolved = [
        {
            "fact_id": "unresolved-fact-000001", "status": "unresolved", "code": "ANALOG_VOLUME_TRANSFER_UNPROVEN",
            "affected_subjects": ["input-control:device-input-000017", "input-control:device-input-000018"],
            "owner": "device-profile-owner", "earliest_task": "task-018",
            "rationale": "The BOM identifies dual B100k controls, but the physical transfer, tolerance, and effective resolution are not a software-readable panel contract.",
            "question": "What measured mechanical and electrical transfer applies to the two analog volume controls?",
            "evidence_status": "partial-portable-evidence", "evidence_refs": ["contracts/task018/gills-panel-evidence.json"],
        },
        {
            "fact_id": "unresolved-fact-000002", "status": "unresolved", "code": "OPTIONAL_CV_POPULATION_UNPROVEN",
            "affected_subjects": [f"physical-io:device-physical-io-{number:06d}" for number in (8, 9, 10, 17)],
            "owner": "device-profile-owner", "earliest_task": "task-018",
            "rationale": "The base design exposes protected expansion connections, but usable CV/gate behavior depends on optional population and remains explicitly marked untested in the schematic.",
            "question": "Which optional expansion components are populated and electrically validated on a specific assembly?",
            "evidence_status": "partial-portable-evidence", "evidence_refs": ["contracts/task018/gills-panel-evidence.json"],
        },
        {
            "fact_id": "unresolved-fact-000003", "status": "unresolved", "code": "CORE_PORT_REVISION_UNPINNED",
            "affected_subjects": [f"physical-io:device-physical-io-{number:06d}" for number in (11, 12, 13)],
            "owner": "device-profile-owner", "earliest_task": "task-018",
            "rationale": "These connectors belong to the independently identified Ksoloti Core rather than the pinned Gills main board and panel.",
            "question": "Which exact attached Core hardware revision provides these three connector slots?",
            "evidence_status": "partial-portable-evidence", "evidence_refs": ["contracts/task018/gills-panel-evidence.json"],
        },
        {
            "fact_id": "unresolved-fact-000004", "status": "unresolved", "code": "OPTIONAL_HEADER_POPULATION_UNPROVEN",
            "affected_subjects": ["physical-io:device-physical-io-000016", "physical-io:device-physical-io-000018"],
            "owner": "device-profile-owner", "earliest_task": "task-018",
            "rationale": "The design provides optional headers, but the selected base configuration deliberately excludes their optional modules.",
            "question": "Are the optional microphone and headphone-control modules populated on a particular assembly?",
            "evidence_status": "partial-portable-evidence", "evidence_refs": ["contracts/task018/gills-panel-evidence.json"],
        },
    ]
    return _record({
        "schema_version": "device-profile-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "device_profile_id": "schuss-device-profile-000001",
        "revision": 2,
        "content_hash": "sha256:" + "0" * 64,
        "display_name": "Gills v0.6 complete reviewed panel profile",
        "input_controls": inputs,
        "gestures": gestures,
        "feedback_outputs": feedback,
        "displays": displays,
        "physical_io": physical_io,
        "unresolved_facts": unresolved,
    }, schema)


def _sources() -> list[dict[str, Any]]:
    return [
        {
            "source_id": f"panel-source-{number:06d}",
            "repository_url": repository,
            "commit": commit,
            "path": path,
            "byte_sha256": digest,
            "authority": authority,
            "license_observation": license_observation,
            "limitations": [
                "Static source bytes do not prove a particular physical assembly or connected behavior."
            ],
        }
        for number, repository, commit, path, digest, authority, license_observation in SOURCE_SPECS
    ]


def _slot_evidence(device: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    adc_indices = (0, 1, 2, 3, 6, 7, 8, 9, 11, 12)
    for number, adc_index in enumerate(adc_indices, 1):
        result.append({
            "slot_kind": "input-control", "slot_id": f"device-input-{number:06d}", "physical_reference": f"RV{number}", "configuration_status": "installed",
            "facts": [
                _fact("assembly", "B10k panel potentiometer", (12, f"Designator RV{number}"), (4, f"RV{number}")),
                _fact("runtime-locator", f"adcvalues[{adc_index}]", (15, f"CEntries pot {number}")),
                _fact("raw-domain", "0..4095 inclusive", (21, "analogResolution=4096"), (15, "adcvalues[attr_pot]")),
            ],
            "limitations": ["ADC transfer and noise were not measured on a connected board."],
        })
    button_pins = ((1, "GPIOB:5"), (2, "GPIOA:10"), (3, "GPIOB:12"), (4, "GPIOB:13"))
    for button, pin in button_pins:
        result.append({
            "slot_kind": "input-control", "slot_id": f"device-input-{button + 10:06d}", "physical_reference": f"SW{button}", "configuration_status": "installed",
            "facts": [_fact("assembly", "TL1105 momentary button", (12, f"Designator SW{button}"), (5, f"SW{button}")), _fact("runtime-locator", pin, (16, f"button {button}")), _fact("pressed-level", "HIGH", (16, "pressed = HIGH"))],
            "limitations": ["The source object performs no debounce; Task 018 recognition policy is separate."],
        })
    result.extend([
        {"slot_kind": "input-control", "slot_id": "device-input-000015", "physical_reference": "ENC1 A/B", "configuration_status": "installed", "facts": [_fact("assembly", "ALPS STEC11/STEC12 encoder", (12, "Designator ENC1")), _fact("runtime-locator", "GPIOC:7/GPIOC:1", (17, "GILLS_ENC_A_PIN and GILLS_ENC_B_PIN")), _fact("scan-boundary", "every four control updates", (17, "counter modulo 4"))], "limitations": ["Mechanical detent count and bounce are not asserted."]},
        {"slot_kind": "input-control", "slot_id": "device-input-000016", "physical_reference": "ENC1 push", "configuration_status": "installed", "facts": [_fact("assembly", "encoder integral switch", (12, "Designator ENC1")), _fact("runtime-locator", "GPIOA:9", (17, "GILLS_ENC_SW_PIN")), _fact("pressed-level", "HIGH with pulldown", (17, "PAL_MODE_INPUT_PULLDOWN"))], "limitations": ["The source object performs no debounce; Task 018 recognition policy is separate."]},
        {"slot_kind": "input-control", "slot_id": "device-input-000017", "physical_reference": "RV11", "configuration_status": "installed", "facts": [_fact("assembly", "dual B100k analog input-volume potentiometer", (12, "Designator RV11"), (6, "RV11")), _fact("software-addressability", "hardware-only", (6, "INPUT analog path"))], "limitations": ["Physical transfer and effective resolution are unresolved."]},
        {"slot_kind": "input-control", "slot_id": "device-input-000018", "physical_reference": "RV12", "configuration_status": "installed", "facts": [_fact("assembly", "dual B100k analog output-volume potentiometer", (12, "Designator RV12"), (6, "RV12")), _fact("software-addressability", "hardware-only", (6, "OUTPUT analog path"))], "limitations": ["Physical transfer and effective resolution are unresolved."]},
        {"slot_kind": "input-control", "slot_id": "device-input-000019", "physical_reference": "J2 power switch header", "configuration_status": "installed", "facts": [_fact("assembly", "power switch connection", (12, "Designator J2"), (10, "PWR_SWITCH")), _fact("software-addressability", "hardware-only", (10, "power path"))], "limitations": ["No software gesture is assigned to the power switch."]},
    ])
    for gesture in device["gestures"]:
        result.append({
            "slot_kind": "gesture", "slot_id": gesture["gesture_id"], "physical_reference": "+".join(gesture["source_control_ids"]), "configuration_status": "installed",
            "facts": [_fact("recognition", gesture["gesture_kind"], status="task-policy"), _fact("recognition-boundary", "Task 018 deterministic panel runtime", status="task-policy")],
            "limitations": ["Recognition is a Task 018 runtime policy, not an observed mechanical timing fact."],
        })
    led_refs = ("LED1 PG6", "LED2 PC6", "LED3 PB3", "LED3 PB4", "LED4 PB6", "LED4 PB7")
    for number, physical in enumerate(led_refs, 1):
        result.append({
            "slot_kind": "feedback-output", "slot_id": f"device-feedback-{number:06d}", "physical_reference": physical.split()[0], "configuration_status": "installed",
            "facts": [_fact("runtime-locator", physical.split()[1], (18, physical)), _fact("output-shape", "binary indicator", (18, "positive = true")), _fact("assembly", physical.split()[0], (5, physical.split()[0]), (12, f"Designator {physical.split()[0]}"))],
            "limitations": (["Exact emitted hue for dual-color channel A depends on populated part and is unresolved."] if number in (3, 5) else []),
        })
    for number, kind in ((1, "text"), (2, "graphics")):
        result.append({
            "slot_kind": "display", "slot_id": f"device-display-{number:06d}", "physical_reference": "OLED1", "configuration_status": "installed",
            "facts": [_fact("geometry", "128x64", (12, "Designator OLED1"), (19, "OLEDWIDTH and OLEDHEIGHT")), _fact("controller", "SH1106 at I2C address 0x3C", (19, "__SH1106 and __I2C_ADDR")), _fact("mode", kind, (19, "text and scope modes"))],
            "limitations": ["Text and graphics are two logical capabilities of one physical OLED; no connected display was observed."],
        })
    io_sources = {
        1: ("J3", 6, "IN_L"), 2: ("J4", 6, "IN_R"), 3: ("J5", 6, "OUT_L"), 4: ("J6", 6, "OUT_R"),
        5: ("J7", 6, "HP_OUT"), 6: ("J11", 7, "MIDI_IO"), 7: ("J10", 7, "MIDI_OUT"),
        8: ("J8", 8, "EXP_IO"), 9: ("J9", 8, "EXP_IO"), 10: ("J17", 8, "GATE_OUT"),
        11: ("Ksoloti Core SD", 3, "Core module connection"), 12: ("Ksoloti Core USB device", 3, "Core module connection"), 13: ("Ksoloti Core USB host", 3, "Core module connection"),
        14: ("J1", 10, "9-20VDC"), 15: ("J19", 6, "OUTPUT_INSERT"), 16: ("M1/H6", 9, "PDM microphone"),
        17: ("J16", 8, "EXPANSION"), 18: ("J14", 6, "HP_POT"), 19: ("J12", 6, "LINE_IN_OUT"), 20: ("J20", 10, "POWER_HEADER"),
    }
    optional = {8, 9, 10, 16, 18}
    internal = {15, 17, 19, 20}
    compute = {11, 12, 13}
    for io in device["physical_io"]:
        number = int(io["slot_id"].rsplit("-", 1)[1])
        physical, source_number, locator = io_sources[number]
        status = "optional-unpopulated" if number in optional else "internal-header" if number in internal else "compute-module" if number in compute else "installed"
        result.append({
            "slot_kind": "physical-io", "slot_id": io["slot_id"], "physical_reference": physical, "configuration_status": status,
            "facts": [_fact("physical-reference", physical, (source_number, locator)), _fact("declared-direction", io["direction"], status="task-policy"), _fact("declared-kind", io["io_kind"], status="task-policy")],
            "limitations": (["Optional population or exact attached Core revision remains unresolved."] if status in {"optional-unpopulated", "compute-module"} else []),
        })
    return result


def _panel_evidence(device: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    names = (
        "structural-schema-validation", "component-graph-resolution", "backend-lowering", "source-artifact-generation",
        "arm-compilation-linking", "connected-device-execution", "real-time-resource-validation", "audible-listening-validation",
    )
    return _record({
        "schema_version": "gills-panel-evidence-v0", "canonical_profile": "schuss-canonical-json-v1",
        "panel_evidence_packet_id": "schuss-panel-evidence-000001", "revision": 1, "content_hash": "sha256:" + "0" * 64,
        "reviewed_configuration": {
            "product": "Ksoloti Gills", "hardware_revision": "v0.6", "panel_revision": "v0.6",
            "assembly_scope": "base-gills-main-board-and-panel", "compute_module": "Ksoloti Core required but independently identified",
            "excluded_options": ["CV expander module", "PDM microphone module", "headphone-volume modification"],
        },
        "sources": _sources(),
        "slot_evidence": _slot_evidence(device),
        "unresolved_facts": [
            {"fact_id": "panel-unresolved-000001", "code": "OPTIONAL_ASSEMBLY_POPULATION_UNPROVEN", "affected_slots": [f"device-physical-io-{number:06d}" for number in (8, 9, 10, 16, 17, 18)], "question": "Which optional connectors and modules are populated on a particular physical assembly?", "evidence_refs": [_source_ref(8, "optional CV notes"), _source_ref(9, "optional PDM circuit"), _source_ref(12, "through-hole BOM rows")]},
            {"fact_id": "panel-unresolved-000002", "code": "ANALOG_VOLUME_TRANSFER_UNPROVEN", "affected_slots": ["device-input-000017", "device-input-000018"], "question": "What measured physical transfer and effective resolution apply to the analog volume controls?", "evidence_refs": [_source_ref(6, "RV11/RV12"), _source_ref(12, "dual B100k rows")]},
            {"fact_id": "panel-unresolved-000003", "code": "DUAL_LED_HUE_POPULATION_UNPROVEN", "affected_slots": ["device-feedback-000003", "device-feedback-000005"], "question": "Does a particular assembly populate blue-red or green-red dual LEDs?", "evidence_refs": [_source_ref(5, "LED3/LED4"), _source_ref(11, "dual-color changelog"), _source_ref(12, "LED_Dual_AKA rows")]},
            {"fact_id": "panel-unresolved-000004", "code": "CORE_HARDWARE_REVISION_UNPINNED", "affected_slots": [f"device-physical-io-{number:06d}" for number in (11, 12, 13)], "question": "Which exact Ksoloti Core hardware revision supplies the attached Core connectors?", "evidence_refs": [_source_ref(3, "Core module hierarchy")]} ,
            {"fact_id": "panel-unresolved-000005", "code": "CONNECTED_DISPLAY_BEHAVIOR_NOT_RUN", "affected_slots": ["device-display-000001", "device-display-000002"], "question": "Does the compiled display runtime operate correctly on a connected OLED without real-time interference?", "evidence_refs": [_source_ref(19, "SH1106 implementation")]},
        ],
        "evidence_boundaries": [{"level": level, "name": name, "status": "passed" if level == 1 else "not-run"} for level, name in enumerate(names, 1)],
    }, schema)


def _normalized() -> dict[str, str]:
    return {"minimum": "0", "maximum": "1", "unit": "normalized"}


def _linear() -> dict[str, Any]:
    return {"curve": "linear", "polarity": "direct", "points": [{"source": "0", "destination": "0"}, {"source": "1", "destination": "1"}]}


def _parameter_mapping(number: int, source_number: int, destination_number: int, smoothing: str) -> dict[str, Any]:
    return {
        "mapping_id": f"device-mapping-{number:06d}", "mapping_kind": "parameter-control", "direction": "device-to-instrument",
        "source": {"facet_kind": "input-control", "slot_id": f"device-input-{source_number:06d}"},
        "destination": {"facet_kind": "parameter", "facet_id": f"instrument-parameter-{destination_number:06d}"},
        "source_domain": _normalized(), "destination_domain": _normalized(), "transform": _linear(),
        "response": {"response_time": "control-update", "smoothing_responsibility": smoothing},
        "pickup": {"mode": "soft", "responsibility": "instrument"},
    }


def _instruments(device: dict[str, Any], schema: dict[str, Any]) -> dict[str, dict[str, Any]]:
    device_ref = _ref(device, "device_profile_id")
    executable = core.load_json(ROOT / "contracts/task011b/instruments/four-step-dual-sine.json")
    executable.update({"revision": 2, "display_name": "Four-step dual-sine full-panel mapped instrument", "device_profile_reference": copy.deepcopy(device_ref)})
    executable["parameters"][0]["update_behavior"]["smoothing_responsibility"] = "instrument"
    executable["actions"] = [{"facet_id": "instrument-action-000001", "display_label": "Reset Blend Control", "payload_kind": "none"}]
    executable["displays"] = [{"facet_id": "instrument-display-000001", "display_label": "Blend Value", "value_kind": "exact-decimal", "access": "read-only"}]
    executable["state_declarations"] = [{"state_id": "instrument-state-000001", "display_label": "Pickup Armed", "value_kind": "boolean", "persistence": "volatile", "reset_policy": "default-on-start"}]
    executable["device_input_mappings"] = [
        _parameter_mapping(1, 1, 1, "instrument"),
        {"mapping_id": "device-mapping-000002", "mapping_kind": "action-trigger", "direction": "device-to-instrument", "source": {"facet_kind": "gesture", "gesture_id": "device-gesture-000001"}, "destination": {"facet_kind": "action", "facet_id": "instrument-action-000001"}},
    ]
    executable["device_feedback_mappings"] = [
        {"mapping_id": "feedback-mapping-000001", "direction": "instrument-to-device", "source": {"facet_kind": "state", "facet_id": "instrument-state-000001"}, "destination": {"slot_kind": "feedback-output", "slot_id": "device-feedback-000001"}, "update_responsibility": "instrument"},
        {"mapping_id": "feedback-mapping-000002", "direction": "instrument-to-device", "source": {"facet_kind": "display", "facet_id": "instrument-display-000001"}, "destination": {"slot_kind": "display", "slot_id": "device-display-000001"}, "update_responsibility": "instrument"},
    ]
    executable = _record(executable, schema)

    percussion = core.load_json(ROOT / "contracts/task017/instrument-percussion.json")
    percussion.update({"revision": 2, "display_name": "Clocked dual-percussion full-panel reference instrument", "device_profile_reference": copy.deepcopy(device_ref)})
    percussion["device_input_mappings"] = [_parameter_mapping(1, 1, 1, "graph")]
    percussion = _record(percussion, schema)

    effects = core.load_json(ROOT / "contracts/task017/instrument-effects.json")
    effects.update({"revision": 2, "display_name": "Modulated oscillator effects full-panel reference instrument", "device_profile_reference": copy.deepcopy(device_ref)})
    effects["device_input_mappings"] = [_parameter_mapping(1, 1, 1, "graph"), _parameter_mapping(2, 2, 2, "graph")]
    effects = _record(effects, schema)
    return {"executable": executable, "percussion": percussion, "effects": effects}


def _requests(instruments: dict[str, dict[str, Any]], schema: dict[str, Any]) -> dict[str, dict[str, Any]]:
    paths = {
        "executable": ROOT / "contracts/task016/four-step-dual-sine-direct-build-request-r3.json",
        "percussion": ROOT / "contracts/task017/build-request-percussion.json",
        "effects": ROOT / "contracts/task017/build-request-effects.json",
    }
    revisions = {"executable": 4, "percussion": 2, "effects": 2}
    result = {}
    for name, path in paths.items():
        value = core.load_json(path)
        value["revision"] = revisions[name]
        value["instrument_reference"] = {"status": "included", **_ref(instruments[name], "instrument_id")}
        result[name] = _record(value, schema)
    return result


def _descriptor(request: dict[str, Any], backend: dict[str, Any]) -> dict[str, Any]:
    value = {
        "schema_version": "build-handler-descriptor-v0", "canonical_profile": "schuss-canonical-json-v1",
        "build_handler_id": "schuss-build-handler-000003", "revision": 1, "content_hash": "sha256:" + "0" * 64,
        "backend_reference": _ref(backend, "backend_id"), "supported_build_request_reference": _ref(request, "build_request_id"),
        "execution_policy": "exact-request-only", "adapter_kind": "direct", "mid_handler_cancellation": False,
    }
    value["content_hash"] = descriptor_content_hash(value)
    return value


def _binding(binding_id: int, slot_id: str, status: str, locator: str, sources: Iterable[int], rationale: str) -> dict[str, Any]:
    return {
        "binding_id": f"runtime-binding-{binding_id:06d}", "slot_id": slot_id, "binding_status": status,
        "runtime_locator": locator, "evidence_source_ids": [f"panel-source-{number:06d}" for number in sources], "rationale": rationale,
    }


def _runtime_bindings() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    input_bindings: list[dict[str, Any]] = []
    adc_indices = (0, 1, 2, 3, 6, 7, 8, 9, 11, 12)
    for number, adc_index in enumerate(adc_indices, 1):
        input_bindings.append(_binding(number, f"device-input-{number:06d}", "bound", f"adcvalues[{adc_index}]", (15,), "Exact official Gills pot selector; Task 018 adds deterministic transform and smoothing."))
    for number, locator in ((11, "GPIOB:5"), (12, "GPIOA:10"), (13, "GPIOB:12"), (14, "GPIOB:13")):
        input_bindings.append(_binding(number, f"device-input-{number:06d}", "bound", locator, (16,), "Exact official Gills button pin with Task 018 debounce and gestures."))
    input_bindings.extend([
        _binding(15, "device-input-000015", "bound", "GPIOC:7/GPIOC:1", (17,), "Exact official encoder A/B pins and scan policy."),
        _binding(16, "device-input-000016", "bound", "GPIOA:9", (17,), "Exact official encoder-switch pin with Task 018 debounce and gestures."),
        _binding(17, "device-input-000017", "intentionally-unavailable", "hardware-only:RV11", (6, 12), "Analog input volume is not software readable."),
        _binding(18, "device-input-000018", "intentionally-unavailable", "hardware-only:RV12", (6, 12), "Analog output volume is not software readable."),
        _binding(19, "device-input-000019", "intentionally-unavailable", "hardware-only:J2", (10, 12), "Power switching is outside the patch runtime."),
    ])
    feedback_locators = ("GPIOG:6", "GPIOC:6", "GPIOB:3", "GPIOB:4", "GPIOB:6", "GPIOB:7")
    feedback = [_binding(100 + number, f"device-feedback-{number:06d}", "bound", locator, (18,), "Exact official LED channel locator.") for number, locator in enumerate(feedback_locators, 1)]
    displays = [
        _binding(201, "device-display-000001", "bound", "I2CD1:SH1106:0x3c:text", (19, 23), "Task 018 compiles the accepted text buffer and SH1106 transport boundary."),
        _binding(202, "device-display-000002", "bound", "I2CD1:SH1106:0x3c:graphics", (19,), "The physical graphics capability is bound, though unused by the mapped executable reference."),
    ]
    io_locators = (
        "patch-abi:audio-input-left", "patch-abi:audio-input-right", "patch-abi:audio-output-left", "patch-abi:audio-output-right",
        "hardware-only:J7", "patch-abi:midi-configurable", "patch-abi:midi-output", "optional:PA4", "optional:PA5", "optional:gate-output",
        "core-owned:sd", "core-owned:usb-device", "core-owned:usb-host", "hardware-only:J1", "hardware-only:J19", "optional:PDM",
        "optional:J16", "optional:J14", "hardware-only:J12", "hardware-only:J20",
    )
    bound_io = {1, 2, 3, 4, 6, 7}
    io = [
        _binding(300 + number, f"device-physical-io-{number:06d}", "bound" if number in bound_io else "unresolved" if number in {8, 9, 10, 11, 12, 13, 16, 17, 18} else "intentionally-unavailable", locator, ((6,) if number in {1, 2, 3, 4, 5, 15, 18, 19} else (7,) if number in {6, 7} else (8,) if number in {8, 9, 10, 17} else (9,) if number == 16 else (10,) if number in {14, 20} else (3,)), "Binding status preserves the reviewed base-assembly and ownership boundary.")
        for number, locator in enumerate(io_locators, 1)
    ]
    return input_bindings, feedback, displays, io


def _runtime_realizations(
    device: dict[str, Any], panel: dict[str, Any], instruments: dict[str, dict[str, Any]],
    requests: dict[str, dict[str, Any]], descriptor: dict[str, Any], schema: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    bindings = _runtime_bindings()
    policies = {
        "control_update": "one-update-per-16-sample-block-at-48000-hz",
        "absolute_transform": "raw-0-through-4095-to-q27-0-through-134217728-linear",
        "smoothing": "signed-error-arithmetic-shift-right-3-per-control-update",
        "pickup": "soft-crossing-or-within-16-raw-counts-then-latched",
        "debounce": "four-identical-control-updates",
        "hold": "1500-debounced-control-updates-single-event",
        "encoder": "official-falling-edge-a-direction-from-b-every-four-control-updates",
        "feedback": "instrument-state-to-led-at-control-update",
        "display": "instrument-display-to-sh1106-0x3c-four-line-text-buffer-32-ms-refresh",
    }
    common = {
        "schema_version": "gills-runtime-realization-v0", "canonical_profile": "schuss-canonical-json-v1",
        "revision": 1, "content_hash": "sha256:" + "0" * 64,
        "device_profile_reference": _ref(device, "device_profile_id"), "compute_target_reference": copy.deepcopy(TARGET_REFERENCE),
        "firmware_runtime_reference": copy.deepcopy(FIRMWARE_REFERENCE), "panel_evidence_reference": _ref(panel, "panel_evidence_packet_id"),
        "input_bindings": bindings[0], "feedback_bindings": bindings[1], "display_bindings": bindings[2], "physical_io_bindings": bindings[3],
        "policies": policies,
        "limitations": [
            "ARM compile and link do not prove connected controls, OLED output, real-time behavior, or audible behavior.",
            "Optional expansion and independently owned Core connectors remain unresolved where the evidence packet says so.",
        ],
    }
    backend1 = core.load_json(ROOT / "contracts/task016/direct-backend.json")
    mapped = _record({
        **copy.deepcopy(common), "runtime_realization_id": "schuss-runtime-realization-000001", "backend_reference": _ref(backend1, "backend_id"),
        "supported_builds": [{"build_request_reference": _ref(requests["executable"], "build_request_id"), "instrument_reference": _ref(instruments["executable"], "instrument_id"), "handler": {"status": "supported", **_ref(descriptor, "build_handler_id")}}],
    }, schema)
    backend2 = core.load_json(ROOT / "contracts/task017/direct-backend-r2.json")
    unsupported = _record({
        **copy.deepcopy(common), "runtime_realization_id": "schuss-runtime-realization-000002", "backend_reference": _ref(backend2, "backend_id"),
        "supported_builds": [
            {"build_request_reference": _ref(requests["percussion"], "build_request_id"), "instrument_reference": _ref(instruments["percussion"], "instrument_id"), "handler": {"status": "unsupported", "diagnostic_code": "COMPILER_COMPOUND_INTERNAL_BINDING_UNRESOLVED", "fallback": False}},
            {"build_request_reference": _ref(requests["effects"], "build_request_id"), "instrument_reference": _ref(instruments["effects"], "instrument_id"), "handler": {"status": "unsupported", "diagnostic_code": "COMPILER_BINDING_UNSUPPORTED", "fallback": False}},
        ],
    }, schema)
    return {"mapped": mapped, "unsupported": unsupported}


def _mapping_ref(kind: str, mapping_id: str) -> dict[str, str]:
    return {"mapping_kind": kind, "mapping_id": mapping_id}


def _coverage(
    number: int, device: dict[str, Any], instrument: dict[str, Any], panel: dict[str, Any],
    executable: bool, schema: dict[str, Any],
) -> dict[str, Any]:
    device_refs: dict[tuple[str, str], list[dict[str, str]]] = {}
    for mapping in instrument["device_input_mappings"]:
        source = mapping["source"]
        key = (source["facet_kind"], source.get("slot_id", source.get("gesture_id")))
        device_refs.setdefault(key, []).append(_mapping_ref("device-input", mapping["mapping_id"]))
    for mapping in instrument["device_feedback_mappings"]:
        destination = mapping["destination"]
        key = (destination["slot_kind"], destination["slot_id"])
        device_refs.setdefault(key, []).append(_mapping_ref("device-feedback", mapping["mapping_id"]))
    if executable:
        for physical_number in (3, 4):
            key = ("physical-io", f"device-physical-io-{physical_number:06d}")
            device_refs[key] = [_mapping_ref("runtime", f"runtime-binding-{300 + physical_number:06d}")]

    collections = (("input-control", "input_controls", "slot_id"), ("gesture", "gestures", "gesture_id"), ("feedback-output", "feedback_outputs", "slot_id"), ("display", "displays", "slot_id"), ("physical-io", "physical_io", "slot_id"))
    device_coverage = []
    for kind, collection, id_field in collections:
        for item in device[collection]:
            key = (kind, item[id_field])
            refs = device_refs.get(key, [])
            device_coverage.append({
                "slot_kind": kind, "slot_id": item[id_field], "outcome": "mapped" if refs else "intentionally-unused", "mapping_refs": refs,
                "rationale": "Exact accepted mapping owns this slot." if refs else "This exact instrument does not use the slot; the complete device profile and runtime binding retain it explicitly.",
            })

    facet_refs: dict[tuple[str, str], list[dict[str, str]]] = {}
    for mapping in instrument["device_input_mappings"]:
        destination = mapping["destination"]
        facet_refs.setdefault((destination["facet_kind"], destination["facet_id"]), []).append(_mapping_ref("device-input", mapping["mapping_id"]))
    for mapping in instrument["device_feedback_mappings"]:
        source = mapping["source"]
        facet_refs.setdefault((source["facet_kind"], source["facet_id"]), []).append(_mapping_ref("device-feedback", mapping["mapping_id"]))
    for mapping in instrument["graph_mappings"]:
        source = mapping["source"]
        facet_refs.setdefault((source["facet_kind"], source["facet_id"]), []).append(_mapping_ref("graph", mapping["mapping_id"]))
    facets = (("parameter", "parameters", "facet_id"), ("action", "actions", "facet_id"), ("display", "displays", "facet_id"), ("state", "state_declarations", "state_id"))
    facet_coverage = []
    for kind, collection, id_field in facets:
        for item in instrument[collection]:
            key = (kind, item[id_field])
            refs = facet_refs.get(key, [])
            facet_coverage.append({
                "facet_kind": kind, "facet_id": item[id_field], "outcome": "mapped" if refs else "intentionally-unused", "mapping_refs": refs,
                "rationale": "All directions used by this public facet are explicit mappings." if refs else "The facet is retained but has no reviewed producer or consumer in this exact reference.",
            })
    outcomes = [item["outcome"] for item in device_coverage + facet_coverage]
    return _record({
        "schema_version": "gills-mapping-coverage-v0", "canonical_profile": "schuss-canonical-json-v1",
        "coverage_report_id": f"schuss-coverage-report-{number:06d}", "revision": 1, "content_hash": "sha256:" + "0" * 64,
        "device_profile_reference": _ref(device, "device_profile_id"), "instrument_reference": _ref(instrument, "instrument_id"), "panel_evidence_reference": _ref(panel, "panel_evidence_packet_id"),
        "device_slot_coverage": device_coverage, "instrument_facet_coverage": facet_coverage,
        "summary": {"device_slots_total": len(device_coverage), "instrument_facets_total": len(facet_coverage), "mapped": outcomes.count("mapped"), "intentionally_unused": outcomes.count("intentionally-unused"), "unresolved": outcomes.count("unresolved"), "absence_is_coverage": False},
    }, schema)


def generated() -> tuple[dict[str, bytes], bytes, dict[str, Any]]:
    schemas = {
        "device": core.load_json(ROOT / "schemas/device-profile-v0.schema.json"),
        "instrument": core.load_json(ROOT / "schemas/instrument-v0.schema.json"),
        "request": core.load_json(ROOT / "schemas/build-request-v0.schema.json"),
        "panel": core.load_json(ROOT / "schemas/gills-panel-evidence-v0.schema.json"),
        "coverage": core.load_json(ROOT / "schemas/gills-mapping-coverage-v0.schema.json"),
        "runtime": core.load_json(ROOT / "schemas/gills-runtime-realization-v0.schema.json"),
        "handler": core.load_json(ROOT / "schemas/build-handler-descriptor-v0.schema.json"),
    }
    for name in ("panel", "coverage", "runtime"):
        annotations = core.validate_schema_annotations(schemas[name])
        if annotations:
            raise ValueError(f"{name} schema annotations: {annotations}")
    device = _device(schemas["device"])
    panel = _panel_evidence(device, schemas["panel"])
    instruments = _instruments(device, schemas["instrument"])
    requests = _requests(instruments, schemas["request"])
    backend = core.load_json(ROOT / "contracts/task016/direct-backend.json")
    descriptor = _descriptor(requests["executable"], backend)
    descriptor_errors = core.schema_errors(descriptor, schemas["handler"], schemas["handler"])
    if descriptor_errors:
        raise ValueError("handler descriptor: " + "; ".join(descriptor_errors))
    runtimes = _runtime_realizations(device, panel, instruments, requests, descriptor, schemas["runtime"])
    coverages = {
        "executable": _coverage(1, device, instruments["executable"], panel, True, schemas["coverage"]),
        "percussion": _coverage(2, device, instruments["percussion"], panel, False, schemas["coverage"]),
        "effects": _coverage(3, device, instruments["effects"], panel, False, schemas["coverage"]),
    }
    records: dict[str, tuple[str, dict[str, Any]]] = {
        "gills-device-profile-r2.json": ("device-profile", device),
        "gills-panel-evidence.json": ("gills-panel-evidence", panel),
        "instrument-executable-r2.json": ("instrument", instruments["executable"]),
        "instrument-percussion-r2.json": ("instrument", instruments["percussion"]),
        "instrument-effects-r2.json": ("instrument", instruments["effects"]),
        "build-request-executable-r4.json": ("request", requests["executable"]),
        "build-request-percussion-r2.json": ("request", requests["percussion"]),
        "build-request-effects-r2.json": ("request", requests["effects"]),
        "runtime-realization-mapped.json": ("gills-runtime-realization", runtimes["mapped"]),
        "runtime-realization-unsupported.json": ("gills-runtime-realization", runtimes["unsupported"]),
        "coverage-executable.json": ("gills-mapping-coverage", coverages["executable"]),
        "coverage-percussion.json": ("gills-mapping-coverage", coverages["percussion"]),
        "coverage-effects.json": ("gills-mapping-coverage", coverages["effects"]),
    }
    files = {
        f"contracts/task018/{name}": core.canonical_json(record).encode("utf-8") + b"\n"
        for name, (_, record) in records.items()
    }
    parent = core.load_json(PARENT)
    schema_members = copy.deepcopy(parent["schema_members"])
    for filename in (
        "gills-panel-evidence-v0.schema.json", "gills-mapping-coverage-v0.schema.json",
        "gills-runtime-realization-v0.schema.json", "operation-request-v6.schema.json",
        "operation-result-v6.schema.json",
    ):
        path = ROOT / "schemas" / filename
        schema_members.append({"schema_version": filename.removesuffix(".schema.json"), "portable_path": f"schemas/{filename}", "byte_sha256": core.sha256_file(path)})
    record_members = copy.deepcopy(parent["record_members"])
    for name, (kind, record) in records.items():
        relative = f"contracts/task018/{name}"
        id_field = next(field for field in record_set_rules.ID_FIELDS if field in record)
        record_members.append({"record_kind": kind, "stable_id": record[id_field], "revision": record["revision"], "content_hash": record["content_hash"], "portable_path": relative, "byte_sha256": hashlib.sha256(files[relative]).hexdigest()})
    manifest_schema = core.load_json(ROOT / record_set_rules.RECORD_SET_SCHEMA)
    manifest = {
        "schema_version": "record-set-v0", "canonical_profile": "schuss-canonical-json-v1",
        "record_set_id": "schuss-record-set-000012", "revision": 1, "content_hash": "sha256:" + "0" * 64,
        "purpose": "prospective-task", "parent_reference": {"status": "included", **{key: parent[key] for key in ("record_set_id", "revision", "content_hash")}},
        "schema_members": sorted(schema_members, key=lambda item: (item["schema_version"], item["portable_path"])),
        "record_members": sorted(record_members, key=lambda item: (item["byte_sha256"], item["portable_path"])),
        "enforced_directories": sorted(parent["enforced_directories"] + ["contracts/task018"]),
    }
    manifest["content_hash"] = core.record_content_hash(manifest, manifest_schema)
    summary = {
        "device": _ref(device, "device_profile_id"), "panel": _ref(panel, "panel_evidence_packet_id"),
        "instruments": {key: _ref(value, "instrument_id") for key, value in instruments.items()},
        "requests": {key: _ref(value, "build_request_id") for key, value in requests.items()},
        "handler": _ref(descriptor, "build_handler_id"), "runtimes": {key: _ref(value, "runtime_realization_id") for key, value in runtimes.items()},
        "record_set": {key: manifest[key] for key in ("record_set_id", "revision", "content_hash")},
    }
    return files, core.canonical_json(manifest).encode("utf-8") + b"\n", summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        files, manifest, summary = generated()
        files[OUTPUT.relative_to(ROOT).as_posix()] = manifest
        stale = [relative for relative, payload in files.items() if not (ROOT / relative).is_file() or (ROOT / relative).read_bytes() != payload]
        if args.check and stale:
            raise ValueError("Task 018 generated files are stale: " + ", ".join(sorted(stale)))
        if not args.check:
            for relative, payload in files.items():
                path = ROOT / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
    except (OSError, ValueError) as exc:
        print("Task 018 record generation failed: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
