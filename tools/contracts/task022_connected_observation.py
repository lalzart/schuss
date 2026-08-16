#!/usr/bin/env python3
"""Exact failed connected observation retained after Task 022 approval gate 1."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/contracts")]

from run_task022 import (  # noqa: E402
    DEVICE_BINARY_LENGTH,
    DEVICE_BINARY_SHA256,
    GENERATED_CPP_LENGTH,
    GENERATED_CPP_SHA256,
    TARGET_ELF_LENGTH,
    TARGET_ELF_SHA256,
    diagnostic_identity,
    diagnostic_procedure,
)

import validator_core as core  # noqa: E402


OBSERVATION = ROOT / "evidence/task022-completion-v1/connected-device-observation.json"
TASK021_BINARY_LENGTH = 6440
TASK021_BINARY_SHA256 = "b573ea36aaa29b5e213ca0e616b13e7e2131d7cad2a0ab29a5b5fe9eaa8b13e3"


def observed_failure() -> dict[str, Any]:
    pot_result = {
        "status": "incomplete",
        "slot_identity": "passed-user-observed",
        "low_zone": "observed-aggregate-not-exact-per-slot",
        "middle_zone": "observed-aggregate-not-exact-per-slot",
        "high_zone": "observed-aggregate-not-exact-per-slot",
        "monotonic_order": "observed-smooth-aggregate-not-exact-per-slot",
        "travel": "observed-approximately-0000-to-4095",
        "non_frozen": "passed-user-observed",
        "discontinuity": "not-observed",
        "event_focus_stability": "failed",
        "raw_observations": [],
    }
    return {
        "schema_version": "task022-connected-device-observation-v1",
        "canonical_profile": "schuss-canonical-json-v1",
        "observation_id": "schuss-connected-observation-000001",
        "revision": 1,
        "observation_date": "2026-08-16",
        "observer": "user-confirmed",
        "status": "failed",
        "promotion_eligible": False,
        "diagnostic_identity": diagnostic_identity(),
        "procedure_reference": {
            key: diagnostic_procedure()[key]
            for key in ("stable_id", "revision", "content_hash")
        },
        "board_identity": {
            "product": "Ksoloti Core",
            "usb_serial": "003D00363532511735393330",
            "firmware_version": "1.1.0.0",
            "firmware_crc": "5021D42A",
        },
        "diagnostic_artifact": {
            "generated_cpp_sha256": GENERATED_CPP_SHA256,
            "generated_cpp_byte_length": GENERATED_CPP_LENGTH,
            "target_elf_sha256": TARGET_ELF_SHA256,
            "target_elf_byte_length": TARGET_ELF_LENGTH,
            "device_binary_sha256": DEVICE_BINARY_SHA256,
            "device_binary_byte_length": DEVICE_BINARY_LENGTH,
            "load_address": "0x20011000",
        },
        "diagnostic_device_checks": {
            "identity": "passed",
            "firmware_identity": "passed",
            "ram_readback": "byte-for-byte-match",
            "readback_sha256": DEVICE_BINARY_SHA256,
            "start_acknowledgement": "passed",
            "responsiveness_before_sweep": {
                "status": "passed",
                "probe_count": 3,
                "probe_window_seconds": 6,
            },
            "flags_before_sweep": 0,
            "responsiveness_after_complete_sweep": "not-run-sweep-stopped",
            "flags_after_complete_sweep": "not-run-sweep-stopped",
        },
        "oled": {
            "startup_text": "passed-user-confirmed",
            "startup_lines": ["SCHUSS", "PANEL TEST", "TASK022", "READY"],
            "upright_orientation": "passed-user-confirmed",
            "stable_output": "passed-user-confirmed",
            "led_channel_labels": "passed-user-confirmed",
            "event_telemetry": "failed-pot-focus-unstable",
            "completion_summary": "not-run-sweep-stopped",
        },
        "led_channels": [
            {
                "runtime_channel": index,
                "physical_indicator_illuminated": "passed-user-confirmed",
                "observed_hue": hue,
                "hue_identity_authenticated": False,
            }
            for index, hue in enumerate(
                ("green", "red", "blue", "red", "blue", "red"), start=1
            )
        ],
        "pot_sweep": {
            "status": "incomplete",
            "aggregate_user_observation": {
                "all_ten_slot_identities": "correct",
                "all_ten_response": "smooth-and-non-frozen",
                "low_endpoint": "approximately-0000-with-small-jitter",
                "middle_region": "approximately-2000-to-2010",
                "high_endpoint": "approximately-4093-to-4095",
                "stationary_adc_variation": "approximately-5-to-15-raw-counts",
                "last_moved_display": "cycled-among-stationary-pot-slots",
            },
            "exact_per_pot_raw_values_retained": False,
            "pots": [{"slot": index, **pot_result} for index in range(1, 11)],
        },
        "buttons": [
            {"slot": index, "press": "not-run", "release": "not-run", "hold": "not-run"}
            for index in range(1, 5)
        ],
        "encoder": {
            "clockwise_detents": [],
            "counterclockwise_detents": [],
            "opposite_consistent_signs": "not-run",
            "clockwise_positive_polarity": "not-observed",
            "profile_updated": False,
            "push": {"press": "not-run", "release": "not-run", "hold": "not-run"},
        },
        "failure": {
            "code": "POT_EVENT_FOCUS_UNSTABLE",
            "step": "phase-b-pot-sweep",
            "detail": (
                "Observed stationary ADC variation exceeded the diagnostic's four-count "
                "last-moved threshold, so line 2 repeatedly changed pot focus and exact "
                "per-pot low/middle/high telemetry could not be retained."
            ),
            "diagnostic_threshold_raw_counts": 4,
            "hardware_fault_claimed": False,
            "promotion_stopped": True,
        },
        "task021_product_mapping": {
            "status": "not-run",
            "approval_gate_2": "closed-after-diagnostic-failure",
            "binary_sha256": TASK021_BINARY_SHA256,
            "binary_byte_length": TASK021_BINARY_LENGTH,
            "volatile_ram_upload_performed": False,
        },
        "write_boundaries": {
            "volatile_ram_uploads_performed": 1,
            "firmware_flash": False,
            "sd_card_write": False,
            "persistent_install": False,
            "reset_performed": False,
            "second_upload_performed": False,
        },
        "current_device_state": {
            "volatile_binary": "task022-panel-diagnostic",
            "device_binary_sha256": DEVICE_BINARY_SHA256,
            "reset_or_power_loss_removes_binary": True,
        },
        "evidence_levels": {
            "device_profile_diagnostic_level_6": "not-run-failed-before-promotion",
            "task021_instrument_mapping_level_6": "not-run",
            "real_time_resource_level_7": "not-run",
            "audible_listening_level_8": "not-run",
        },
    }


def expected_bytes() -> bytes:
    return core.canonical_json(observed_failure()).encode("utf-8") + b"\n"


def main() -> int:
    try:
        actual = OBSERVATION.read_bytes()
        expected = expected_bytes()
    except OSError as exc:
        print("Task 022 connected observation check failed: " + str(exc), file=sys.stderr)
        return 1
    if actual != expected:
        print("Task 022 connected observation bytes are stale", file=sys.stderr)
        return 1
    print(json.dumps(observed_failure(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
