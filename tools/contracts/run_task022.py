#!/usr/bin/env python3
"""Build Task 022 twice and retain only offline, pre-upload evidence."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/contracts")]

from packages.schuss_core.control_plane import (  # noqa: E402
    dispatch_operation,
    load_repository_context,
)
from packages.schuss_core.gills_direct_backend import (  # noqa: E402
    DirectExecutionConfig,
    _artifact,
    _canonical_bytes,
    _compile_arm,
    verify_execution_config,
)
from packages.schuss_core.gills_direct_frontend import (  # noqa: E402
    lower_gills_direct_successor,
)
from packages.schuss_core.gills_mapped_backend import (  # noqa: E402
    DEVICE_REFERENCE,
    PANEL_REFERENCE,
)
from packages.schuss_core.gills_mapped_backend_v2 import (  # noqa: E402
    REQUEST_REFERENCE as PARENT_REQUEST_REFERENCE,
)
from packages.schuss_core.gills_panel_diagnostic import (  # noqa: E402
    diagnostic_cpp,
    diagnostic_host_vectors,
)

import historical_reproduction  # noqa: E402
import retained_evidence  # noqa: E402
import validator_core as core  # noqa: E402


RECORD_SET = ROOT / "contracts/record-sets/task021-gills-dma-safe-v1.json"
EVIDENCE_ROOT = ROOT / "evidence/task022-completion-v1"
HISTORICAL_COMMIT = "a5fa3287d037a2eac9909fafe9ea1fb06aa7ce90"


def check_retained() -> dict[str, Any]:
    return retained_evidence.check_summary(
        EVIDENCE_ROOT,
        repository_root=ROOT,
        anchor_commit=HISTORICAL_COMMIT,
        schema_version="task022-offline-validation-summary-v1",
    )


def reproduce_historical() -> dict[str, Any]:
    return historical_reproduction.reproduce_summary(
        repository_root=ROOT,
        completion_commit=HISTORICAL_COMMIT,
        runner_path=Path("tools/contracts/run_task022.py"),
        retained_summary=check_retained(),
        report_schema_version="task022-historical-reproduction-v1",
    )
LOAD_ADDRESS = "0x20011000"
BOARD_IDENTITY = {
    "product": "Ksoloti Core",
    "usb_serial": "003D00363532511735393330",
    "firmware_version": "1.1.0.0",
    "firmware_crc": "5021D42A",
}
PARENT_RECORD_SET_REFERENCE = {
    "record_set_id": "schuss-record-set-000013",
    "revision": 1,
    "content_hash": "sha256:6e2b1f63abc999ab3067541f6dc0095ed338fb4b3f5c55898a58cdd3397bc8d3",
}
GENERATED_CPP_SHA256 = "f00bd3f1653a02a94c8183b913ed6619e2add4f35cc623af79143d88318c1ca3"
GENERATED_CPP_LENGTH = 25224
TARGET_ELF_SHA256 = "2f003cde514dcb48ecb09ecc0d61f880bb1ecdec5761ddb8b737bc3c68571231"
TARGET_ELF_LENGTH = 75504
DEVICE_BINARY_SHA256 = "7c843acb42b17c13d0c535834d12ab620d312b451fd4ee435733e4acf7321113"
DEVICE_BINARY_LENGTH = 5552


def diagnostic_identity() -> dict[str, Any]:
    material = {
        "kind": "non-product-gills-panel-telemetry",
        "parent_record_set_reference": PARENT_RECORD_SET_REFERENCE,
        "parent_build_request_reference": PARENT_REQUEST_REFERENCE,
        "transform": "schuss-task022-panel-diagnostic-cpp-v1",
        "instrument_reference": {"status": "omitted"},
    }
    return {
        "stable_id": "schuss-panel-diagnostic-000001",
        "revision": 1,
        "content_hash": "sha256:"
        + hashlib.sha256(core.canonical_json(material).encode("utf-8")).hexdigest(),
    }


def diagnostic_procedure() -> dict[str, Any]:
    value = {
        "schema_version": "task022-connected-panel-procedure-v1",
        "canonical_profile": "schuss-canonical-json-v1",
        "stable_id": "schuss-procedure-000004",
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "board_identity": BOARD_IDENTITY,
        "load_address": LOAD_ADDRESS,
        "upload_count": 2,
        "uploads": [
            {
                "ordinal": 1,
                "role": "task022-panel-diagnostic",
                "approval_gate": "diagnostic-volatile-ram-upload",
                "persistent": False,
            },
            {
                "ordinal": 2,
                "role": "immutable-task021-product-binary",
                "approval_gate": "task021-product-volatile-ram-upload",
                "persistent": False,
                "byte_length": 6440,
                "byte_sha256": "b573ea36aaa29b5e213ca0e616b13e7e2131d7cad2a0ab29a5b5fe9eaa8b13e3",
            },
        ],
        "diagnostic_order": [
            "oled-startup",
            "led-channels-1-through-6",
            "pots-1-through-10-low-middle-high",
            "buttons-1-through-4-press-release-hold",
            "encoder-three-detents-each-direction",
            "encoder-push-press-release-hold",
        ],
        "product_order": [
            "pot-1-soft-pickup-hold-and-crossing",
            "button-1-reset-and-rearm",
            "unused-performance-control-isolation",
        ],
        "write_boundaries": {
            "volatile_ram_only": True,
            "firmware_flash": False,
            "sd_card_write": False,
            "persistent_install": False,
            "automatic_reset": False,
        },
        "stop_conditions": [
            "lost-responsiveness",
            "nonzero-device-flags",
            "inverted-or-corrupted-display",
            "unexpected-heat-or-odor",
            "repeated-reset",
            "write-boundary-deviation",
        ],
    }
    payload = {key: item for key, item in value.items() if key != "content_hash"}
    value["content_hash"] = "sha256:" + hashlib.sha256(
        core.canonical_json(payload).encode("utf-8")
    ).hexdigest()
    return value


def _exact_record(
    values: list[dict[str, Any]], reference: dict[str, Any], id_field: str
) -> dict[str, Any]:
    matches = [
        copy.deepcopy(value)
        for value in values
        if all(value.get(key) == item for key, item in reference.items())
    ]
    if len(matches) != 1:
        raise ValueError(f"Task 022 exact {id_field} record did not resolve once")
    return matches[0]


def _diagnostic_plan() -> dict[str, Any]:
    return {
        "schema_version": "task022-panel-diagnostic-plan-v1",
        "canonical_profile": "schuss-canonical-json-v1",
        "diagnostic_identity": diagnostic_identity(),
        "diagnostic_kind": "non-product-gills-panel-telemetry",
        "parent_record_set_reference": PARENT_RECORD_SET_REFERENCE,
        "parent_build_request_reference": PARENT_REQUEST_REFERENCE,
        "instrument_reference": {"status": "omitted"},
        "device_profile_reference": DEVICE_REFERENCE,
        "panel_evidence_reference": PANEL_REFERENCE,
        "audio_output_policy": "forced-silence",
        "control_update_policy": "once-per-16-sample-block-at-48khz",
        "startup_lines": ["SCHUSS", "PANEL TEST", "TASK022", "READY"],
        "pot_adc_indices": [0, 1, 2, 3, 6, 7, 8, 9, 11, 12],
        "button_policy": {"debounce_updates": 4, "hold_updates": 1500},
        "encoder_policy": {
            "scan_divisor": 4,
            "algorithm": "falling-edge-a-direction-from-b",
        },
        "led_scan": {
            "automatic": True,
            "channels": 6,
            "step_updates": 1500,
            "hue_identity_authenticated": False,
        },
        "oled_transport": {
            "controller": "SH1106",
            "address": "0x3c",
            "refresh_milliseconds": 32,
            "command_buffer": "SchussDiagnosticOledCommand[2]",
            "page_buffer": "SchussDiagnosticOledTx[129]",
            "buffers_independent": True,
            "dma_visible_section": ".sram2",
        },
        "product_mapping_present": False,
        "java_used": False,
        "legacy_boundary_patch_used": False,
        "ambient_discovery_used": False,
    }


def _worker(output_parent: Path) -> dict[str, Any]:
    output_parent.mkdir(parents=True)
    context = load_repository_context(record_set_path=RECORD_SET)
    if context.record_set_reference != PARENT_RECORD_SET_REFERENCE:
        raise ValueError("Task 022 parent record-set identity differs")
    validation = dispatch_operation(
        {
            "schema_version": "schuss-operation-request-v1",
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": "records.validate",
            "payload": {"scope": "accepted-record-closure"},
        },
        context,
    )
    plan = dispatch_operation(
        {
            "schema_version": "schuss-operation-request-v4",
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": "build.plan",
            "payload": {"build_request_reference": PARENT_REQUEST_REFERENCE},
        },
        context,
    )
    if validation["status"] != "success" or plan["status"] != "success":
        raise ValueError("Task 022 exact Task 021 parent validation or plan failed")
    records = context.records
    graph = _exact_record(
        records["graphs"],
        {
            "graph_id": "schuss-graph-000002",
            "revision": 1,
            "content_hash": "sha256:ea98b4cbf1ecb58d70338e5aaaef02385a6ede707b9b78bbc90fac09d53c7460",
        },
        "graph_id",
    )
    _exact_record(records["devices"], DEVICE_REFERENCE, "device_profile_id")
    _exact_record(
        records["panel_evidence"], PANEL_REFERENCE, "panel_evidence_packet_id"
    )
    parent_artifact = _exact_record(
        records["artifact"],
        {
            "artifact_id": "schuss-artifact-000029",
            "revision": 1,
            "content_hash": "sha256:722cc070aec8228a3cb15ac74805dff1663998cb26e21395ed3f14e112f5093c",
        },
        "artifact_id",
    )
    direct = lower_gills_direct_successor(
        plan["value"],
        graph,
        records["contracts"],
        records["direct_operation_specs"],
        PARENT_REQUEST_REFERENCE,
    )
    cpp = diagnostic_cpp(direct["generated_cpp"]["text"])
    cpp_bytes = cpp.encode("utf-8")
    config = DirectExecutionConfig.local_default()
    preflight = {
        **verify_execution_config(config),
        "schema_version": "task022-diagnostic-preflight-v1",
        "diagnostic_identity": diagnostic_identity(),
        "parent_record_set_reference": PARENT_RECORD_SET_REFERENCE,
        "parent_build_request_reference": PARENT_REQUEST_REFERENCE,
        "parent_target_executable_reference": {
            key: parent_artifact[key]
            for key in ("artifact_id", "revision", "content_hash")
        },
        "parent_target_executable_byte_sha256": parent_artifact["byte_sha256"],
        "parent_target_executable_byte_length": parent_artifact["byte_length"],
        "instrument_reference": {"status": "omitted"},
        "product_mapping_present": False,
        "audio_output_policy": "forced-silence",
        "device_actions_performed": False,
    }
    output_root = output_parent / "build-output"
    output_root.mkdir()
    resolution = next(
        item["payload"]
        for item in plan["value"]["artifacts"]
        if item["descriptor"]["artifact_kind"] == "resolution-plan"
    )
    payloads = [
        (
            "resolution-plan",
            resolution,
            "application/vnd.schuss.resolution-plan+json",
            "implementation-resolution",
        ),
        (
            "normalized-dsp",
            direct["module"],
            "application/vnd.schuss.normalized-dsp+json",
            "backend-lowering",
        ),
        (
            "source-map",
            direct["source_map"],
            "application/vnd.schuss.source-map+json",
            "artifact-generation",
        ),
        (
            "semantic-goldens",
            direct["semantic_goldens"],
            "application/vnd.schuss.semantic-goldens+json",
            "artifact-generation",
        ),
        (
            "panel-diagnostic-plan",
            _diagnostic_plan(),
            "application/vnd.schuss.gills-panel-diagnostic+json",
            "backend-lowering",
        ),
        (
            "panel-host-vectors",
            diagnostic_host_vectors(),
            "application/vnd.schuss.gills-host-vectors+json",
            "artifact-generation",
        ),
    ]
    artifacts = [
        _artifact(kind, _canonical_bytes(value), media, stage, output_root)
        for kind, value, media, stage in payloads
    ]
    artifacts.append(
        _artifact(
            "generated-cpp",
            cpp_bytes,
            "text/x-c++src",
            "artifact-generation",
            output_root,
        )
    )
    arm_artifacts, commands, resource = _compile_arm(cpp_bytes, output_root, config)
    artifacts.extend(arm_artifacts)
    resource = {
        **resource,
        "schema_version": "task022-static-resource-facts-v1",
        "diagnostic_identity": diagnostic_identity(),
        "device_profile_reference": DEVICE_REFERENCE,
        "panel_evidence_reference": PANEL_REFERENCE,
        "parent_target_executable_byte_sha256": parent_artifact["byte_sha256"],
    }
    artifacts.extend(
        [
            _artifact(
                "resource-facts",
                _canonical_bytes(resource),
                "application/vnd.schuss.resource-facts+json",
                "target-compile-link",
                output_root,
            ),
            _artifact(
                "command-vector",
                _canonical_bytes(commands),
                "application/vnd.schuss.command-vector+json",
                "target-compile-link",
                output_root,
            ),
            _artifact(
                "authenticated-preflight",
                _canonical_bytes(preflight),
                "application/vnd.schuss.authenticated-preflight+json",
                "backend-lowering",
                output_root,
            ),
        ]
    )
    return {
        "schema_version": "task022-offline-build-result-v1",
        "canonical_profile": "schuss-canonical-json-v1",
        "status": "success",
        "diagnostic_identity": diagnostic_identity(),
        "parent_record_set_reference": context.record_set_reference,
        "parent_build_request_reference": PARENT_REQUEST_REFERENCE,
        "instrument_reference": {"status": "omitted"},
        "parent_validation_status": validation["status"],
        "parent_plan_status": plan["status"],
        "parent_plan_sha256": "sha256:"
        + hashlib.sha256(core.canonical_json(plan["value"]).encode("utf-8")).hexdigest(),
        "artifacts": sorted(artifacts, key=lambda item: item["artifact_kind"]),
        "evidence_levels": [
            {"level": level, "status": "passed" if level <= 5 else "not-run"}
            for level in range(1, 9)
        ],
        "preflight": preflight,
        "device_actions_performed": False,
        "java_used": False,
        "legacy_boundary_patch_used": False,
        "ambient_discovery_used": False,
    }


def _run_process(output_parent: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--worker-root", str(output_parent)],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=600,
    )
    if completed.returncode:
        raise ValueError(
            "fresh process failed: "
            + completed.stderr.decode("utf-8", errors="replace").strip()
        )
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("fresh process returned non-JSON output") from exc


def _artifact_bytes(result: dict[str, Any], output_parent: Path) -> dict[str, bytes]:
    output_root = output_parent / "build-output"
    values: dict[str, bytes] = {}
    for artifact in result["artifacts"]:
        digest = artifact["byte_sha256"]
        payload = (output_root / "artifacts" / artifact["portable_locator"]).read_bytes()
        if hashlib.sha256(payload).hexdigest() != digest:
            raise ValueError("published artifact bytes do not match their digest")
        values[digest] = payload
    return values


def _artifact_by_kind(
    result: dict[str, Any], artifacts: dict[str, bytes], kind: str
) -> tuple[dict[str, Any], bytes]:
    matches = [item for item in result["artifacts"] if item["artifact_kind"] == kind]
    if len(matches) != 1:
        raise ValueError(f"exact {kind} artifact did not resolve once")
    descriptor = matches[0]
    return descriptor, artifacts[descriptor["byte_sha256"]]


def _device_binary(elf: bytes) -> bytes:
    objcopy = DirectExecutionConfig.local_default().arm_bin / "arm-none-eabi-objcopy"
    with tempfile.TemporaryDirectory(prefix="schuss-task022-device-binary-") as raw:
        root = Path(raw)
        source = root / "diagnostic.elf"
        destination = root / "diagnostic.bin"
        source.write_bytes(elf)
        completed = subprocess.run(
            [str(objcopy), "-O", "binary", str(source), str(destination)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode or not destination.is_file():
            raise ValueError("authenticated objcopy could not derive diagnostic binary")
        return destination.read_bytes()


def _not_run_result_template(
    elf_descriptor: dict[str, Any], binary: bytes
) -> dict[str, Any]:
    not_run = "not-run"
    return {
        "schema_version": "task022-connected-result-v1",
        "status": "not-run",
        "promotion_eligible": False,
        "recorded_observation_date": None,
        "diagnostic_identity": diagnostic_identity(),
        "procedure_reference": {
            key: diagnostic_procedure()[key]
            for key in ("stable_id", "revision", "content_hash")
        },
        "board_identity": BOARD_IDENTITY,
        "diagnostic_artifact": {
            "target_elf_sha256": elf_descriptor["byte_sha256"],
            "target_elf_byte_length": elf_descriptor["byte_length"],
            "device_binary_sha256": hashlib.sha256(binary).hexdigest(),
            "device_binary_byte_length": len(binary),
            "load_address": LOAD_ADDRESS,
        },
        "diagnostic_device_checks": {
            key: not_run
            for key in (
                "identity",
                "ram_readback",
                "start_acknowledgement",
                "responsiveness_before",
                "flags_before",
                "responsiveness_after",
                "flags_after",
            )
        },
        "oled": {
            key: not_run
            for key in (
                "startup_text",
                "upright_orientation",
                "stable_output",
                "event_telemetry",
                "led_channel_labels",
                "completion_summary",
            )
        },
        "pots": [
            {
                "slot": index,
                **{
                    key: not_run
                    for key in (
                        "slot_identity",
                        "low_zone",
                        "middle_zone",
                        "high_zone",
                        "monotonic_order",
                        "travel",
                        "non_frozen",
                        "discontinuity",
                    )
                },
                "raw_observations": [],
            }
            for index in range(1, 11)
        ],
        "buttons": [
            {"slot": index, "press": not_run, "release": not_run, "hold": not_run}
            for index in range(1, 5)
        ],
        "encoder": {
            "clockwise_detents": [],
            "counterclockwise_detents": [],
            "opposite_consistent_signs": not_run,
            "clockwise_positive_polarity": "not-observed",
            "profile_updated": False,
            "push": {"press": not_run, "release": not_run, "hold": not_run},
        },
        "led_channels": [
            {
                "runtime_channel": index,
                "physical_indicator_illuminated": not_run,
                "observed_hue": "not-observed",
                "hue_identity_authenticated": False,
            }
            for index in range(1, 7)
        ],
        "task021_product_mapping": {
            "binary_sha256": "b573ea36aaa29b5e213ca0e616b13e7e2131d7cad2a0ab29a5b5fe9eaa8b13e3",
            "binary_byte_length": 6440,
            "load_address": LOAD_ADDRESS,
            "device_checks": {
                key: not_run
                for key in (
                    "ram_readback",
                    "start_acknowledgement",
                    "responsiveness_before",
                    "flags_before",
                    "responsiveness_after",
                    "flags_after",
                    "upright_startup",
                    "led1_pickup_armed",
                )
            },
            "pot1": {
                key: not_run
                for key in (
                    "soft_pickup_hold",
                    "crossing",
                    "monotonic_follow",
                    "oled_feedback",
                    "button1_reset_rearm",
                )
            },
            "unused_controls": [
                {
                    "control": label,
                    "blend_unchanged": not_run,
                    "pickup_unchanged": not_run,
                    "led1_unchanged": not_run,
                    "display_roles_unchanged": not_run,
                }
                for label in (
                    [f"pot-{index}" for index in range(2, 11)]
                    + [f"button-{index}" for index in range(2, 5)]
                    + ["encoder-clockwise", "encoder-counterclockwise", "encoder-push"]
                )
            ],
        },
        "write_boundaries": {
            "volatile_ram_uploads_performed": 0,
            "firmware_flash": False,
            "sd_card_write": False,
            "persistent_install": False,
        },
        "evidence_levels": {
            "device_profile_diagnostic_level_6": "not-run",
            "task021_instrument_mapping_level_6": "not-run",
            "real_time_resource_level_7": "not-run",
            "audible_listening_level_8": "not-run",
        },
    }


def generated() -> tuple[dict[str, bytes], dict[str, Any]]:
    with tempfile.TemporaryDirectory(prefix="schuss-task022-fresh-processes-") as raw:
        root = Path(raw)
        first_root = root / "fresh-a"
        second_root = root / "fresh-b-with-longer-name"
        first = _run_process(first_root)
        second = _run_process(second_root)
        if core.canonical_json(first) != core.canonical_json(second):
            raise ValueError("fresh-process canonical results differ")
        first_artifacts = _artifact_bytes(first, first_root)
        second_artifacts = _artifact_bytes(second, second_root)
        if first_artifacts != second_artifacts:
            raise ValueError("fresh-process artifact bytes differ")
        cpp_descriptor, cpp = _artifact_by_kind(first, first_artifacts, "generated-cpp")
        elf_descriptor, elf = _artifact_by_kind(first, first_artifacts, "target-executable")
        required_cpp = (
            b"SchussDiagnosticOledCommand[2]",
            b"SchussDiagnosticOledTx[129]",
            b"SchussDiagnosticOledTx[0] = 0x40",
            b'"PANEL TEST"',
            b'"TASK022"',
            b"process_gills_diagnostic();",
        )
        if not all(anchor in cpp for anchor in required_cpp):
            raise ValueError("generated C++ lacks required diagnostic anchors")
        if (
            b"process_gills_panel();" in cpp
            or b'"PICKUP ARM"' in cpp
            or b'"TASK018"' in cpp
            or b"uint8_t bytes[2]" in cpp
        ):
            raise ValueError("diagnostic C++ contains a product or unsafe OLED path")
        if (
            cpp_descriptor["byte_sha256"] != GENERATED_CPP_SHA256
            or cpp_descriptor["byte_length"] != GENERATED_CPP_LENGTH
        ):
            raise ValueError("diagnostic generated C++ differs from the exact candidate")
        if (
            elf_descriptor["byte_sha256"] != TARGET_ELF_SHA256
            or elf_descriptor["byte_length"] != TARGET_ELF_LENGTH
        ):
            raise ValueError("diagnostic target ELF differs from the exact candidate")
        binary = _device_binary(elf)
        if (
            hashlib.sha256(binary).hexdigest() != DEVICE_BINARY_SHA256
            or len(binary) != DEVICE_BINARY_LENGTH
        ):
            raise ValueError("diagnostic device binary differs from the exact candidate")
        result_template = _not_run_result_template(elf_descriptor, binary)
        summary = {
            "schema_version": "task022-offline-validation-summary-v1",
            "status": "valid",
            "task_state": "ready-for-diagnostic-upload-approval",
            "diagnostic_identity": diagnostic_identity(),
            "parent_record_set_reference": PARENT_RECORD_SET_REFERENCE,
            "parent_build_request_reference": PARENT_REQUEST_REFERENCE,
            "instrument_reference": {"status": "omitted"},
            "diagnostic_procedure_reference": {
                key: diagnostic_procedure()[key]
                for key in ("stable_id", "revision", "content_hash")
            },
            "board_identity": BOARD_IDENTITY,
            "load_address": LOAD_ADDRESS,
            "planned_device_uploads": 2,
            "next_approved_uploads": 0,
            "fresh_roots": 2,
            "fresh_processes": 2,
            "portable_results_identical": True,
            "artifact_bytes_identical": True,
            "parent_validation_status": first["parent_validation_status"],
            "parent_plan_status": first["parent_plan_status"],
            "artifacts": first["artifacts"],
            "generated_cpp_sha256": cpp_descriptor["byte_sha256"],
            "generated_cpp_byte_length": cpp_descriptor["byte_length"],
            "target_elf_sha256": elf_descriptor["byte_sha256"],
            "target_elf_byte_length": elf_descriptor["byte_length"],
            "device_binary_sha256": hashlib.sha256(binary).hexdigest(),
            "device_binary_byte_length": len(binary),
            "build_evidence_levels": first["evidence_levels"],
            "device_profile_diagnostic_level_6": "not-run",
            "task021_mapping_level_6": "not-run",
            "real_time_resource_level_7": "not-run",
            "audible_listening_level_8": "not-run",
            "runner_device_actions_performed": False,
            "observed_volatile_ram_uploads": 0,
            "firmware_flash_performed": False,
            "sd_card_write_performed": False,
            "java_used": False,
            "legacy_boundary_patch_used": False,
            "ambient_discovery_used": False,
        }
        files = {
            "validation-summary.json": core.canonical_json(summary).encode("utf-8") + b"\n",
            "portable-offline-build-result.json": core.canonical_json(first).encode("utf-8") + b"\n",
            "diagnostic-procedure.json": core.canonical_json(diagnostic_procedure()).encode("utf-8") + b"\n",
            "connected-result-template.json": core.canonical_json(result_template).encode("utf-8") + b"\n",
            "device-artifacts/sha256/" + hashlib.sha256(binary).hexdigest(): binary,
        }
        for digest, payload in first_artifacts.items():
            files["artifacts/sha256/" + digest] = payload
        return files, summary


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--reproduce", action="store_true")
    mode.add_argument("--worker-root", type=Path)
    args = parser.parse_args()
    if args.worker_root is not None:
        try:
            print(core.canonical_json(_worker(args.worker_root)))
        except (OSError, ValueError) as exc:
            print("Task 022 worker failed: " + str(exc), file=sys.stderr)
            return 1
        return 0
    try:
        if args.check:
            summary = check_retained()
            print(json.dumps(summary, sort_keys=True))
            return 0
        summary = reproduce_historical()
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print("Task 022 execution failed: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
