#!/usr/bin/env python3
"""Run Task 021 twice and retain build and connected-device evidence separately."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/contracts")]

from packages.schuss_core.build_execution import (  # noqa: E402
    ExecutionService,
    handler_reference,
)
from packages.schuss_core.control_plane import (  # noqa: E402
    dispatch_operation,
    load_repository_context,
)
from packages.schuss_core.gills_direct_backend import (  # noqa: E402
    DirectExecutionConfig,
)
from packages.schuss_core.gills_mapped_backend_v2 import (  # noqa: E402
    INSTRUMENT_REFERENCE,
    REQUEST_REFERENCE,
    RUNTIME_REFERENCE,
    registration,
)

from generate_task021_records import (  # noqa: E402
    DEVICE_PROCEDURE_REFERENCE,
    TARGET_ELF_LENGTH,
    TARGET_ELF_SHA256,
)
import historical_reproduction  # noqa: E402
import retained_evidence  # noqa: E402
import validator_core as core  # noqa: E402
from target_backend_build_rules import validate_artifact_fixture_bytes  # noqa: E402


RECORD_SET = ROOT / "contracts/record-sets/task021-gills-dma-safe-v1.json"
EVIDENCE_ROOT = ROOT / "evidence/task021-completion-v1"
HISTORICAL_COMMIT = "8ca4907e760951e59580e1f0c5916a7e717ff88c"


def check_retained() -> dict[str, Any]:
    return retained_evidence.check_summary(
        EVIDENCE_ROOT,
        repository_root=ROOT,
        anchor_commit=HISTORICAL_COMMIT,
        schema_version="task021-validation-summary-v1",
    )


def reproduce_historical(
    source_configuration: Path | None = None,
) -> dict[str, Any]:
    return historical_reproduction.reproduce_summary(
        repository_root=ROOT,
        completion_commit=HISTORICAL_COMMIT,
        runner_path=Path("tools/contracts/run_task021.py"),
        retained_summary=check_retained(),
        report_schema_version="task021-historical-reproduction-v1",
        source_configuration=(
            source_configuration
            if source_configuration is not None
            else ROOT / "catalog/sources.local.yml"
        ),
    )
GENERATED_CPP_SHA256 = "e69155998e91c7c3af6b6e0aaebbac965f4cf822b67382f25de5776453af2928"
DEVICE_BINARY_SHA256 = "b573ea36aaa29b5e213ca0e616b13e7e2131d7cad2a0ab29a5b5fe9eaa8b13e3"
DEVICE_BINARY_LENGTH = 6440


def _worker(output_parent: Path) -> dict[str, Any]:
    output_parent.mkdir(parents=True)
    context = load_repository_context(record_set_path=RECORD_SET)
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
            "payload": {"build_request_reference": REQUEST_REFERENCE},
        },
        context,
    )
    mapped = registration()
    service = ExecutionService.from_values((mapped,), output_parent / "published")
    execution = dispatch_operation(
        {
            "schema_version": "schuss-operation-request-v5",
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": "build.execute",
            "payload": {
                "build_request_reference": REQUEST_REFERENCE,
                "handler_reference": handler_reference(mapped.descriptor),
                "output_locator": "build-output",
                "execution_intent": True,
            },
        },
        context,
        execution_service=service,
    )
    return {
        "schema_version": "task021-fresh-process-result-v1",
        "record_set_reference": context.record_set_reference,
        "validation": validation,
        "plan": plan,
        "execution": execution,
    }


def _run_process(output_parent: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--worker-root",
            str(output_parent),
        ],
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


def _artifact_bytes(
    result: dict[str, Any], output_parent: Path
) -> dict[str, bytes]:
    execution = result["execution"]
    if execution["status"] != "success":
        raise ValueError(
            "Task 021 execution failed: "
            + core.canonical_json(execution["diagnostics"])
        )
    published = output_parent / "published"
    values: dict[str, bytes] = {}
    for artifact in execution["value"]["artifacts"]:
        digest = artifact["byte_sha256"]
        payload = (published / "artifacts" / artifact["portable_locator"]).read_bytes()
        if hashlib.sha256(payload).hexdigest() != digest:
            raise ValueError("published artifact bytes do not match their digest")
        values[digest] = payload
    return values


def _artifact_by_kind(
    execution_value: dict[str, Any], artifacts: dict[str, bytes], kind: str
) -> tuple[dict[str, Any], bytes]:
    matches = [
        item for item in execution_value["artifacts"] if item["artifact_kind"] == kind
    ]
    if len(matches) != 1:
        raise ValueError(f"exact {kind} artifact did not resolve once")
    descriptor = matches[0]
    return descriptor, artifacts[descriptor["byte_sha256"]]


def _device_binary(elf: bytes) -> bytes:
    objcopy = DirectExecutionConfig.local_default().arm_bin / "arm-none-eabi-objcopy"
    with tempfile.TemporaryDirectory(prefix="schuss-task021-device-binary-") as raw:
        root = Path(raw)
        source = root / "candidate.elf"
        destination = root / "candidate.bin"
        source.write_bytes(elf)
        completed = subprocess.run(
            [str(objcopy), "-O", "binary", str(source), str(destination)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode or not destination.is_file():
            raise ValueError("authenticated objcopy could not derive the device binary")
        return destination.read_bytes()


def _observation(
    evidence_reference: dict[str, Any], artifact_reference: dict[str, Any]
) -> dict[str, Any]:
    return {
        "schema_version": "task021-connected-device-observation-v1",
        "status": "passed",
        "observation_date": "2026-08-16",
        "procedure_reference": {
            key: DEVICE_PROCEDURE_REFERENCE[key]
            for key in ("stable_id", "revision", "content_hash")
        },
        "evidence_claim_reference": evidence_reference,
        "target_executable_reference": artifact_reference,
        "board_identity": {
            "product": "Ksoloti Core",
            "usb_serial": "003D00363532511735393330",
            "firmware_version": "1.1.0.0",
            "firmware_crc": "5021D42A",
        },
        "volatile_execution": {
            "load_address": "0x20011000",
            "target_elf_sha256": TARGET_ELF_SHA256,
            "target_elf_byte_length": TARGET_ELF_LENGTH,
            "device_binary_sha256": DEVICE_BINARY_SHA256,
            "device_binary_byte_length": DEVICE_BINARY_LENGTH,
            "ram_readback": "byte-for-byte-match",
            "start_acknowledged": True,
            "responsiveness_probe_count": 3,
            "responsiveness_probe_window_seconds": 6,
            "responsiveness_status": "passed",
            "device_flags": 0,
        },
        "visual_observation": {
            "orientation": "upright",
            "all_expected_words_visible": True,
            "words": ["SCHUSS", "BLEND", "PICKUP", "TASK018"],
            "observer": "user-confirmed",
        },
        "write_boundaries": {
            "volatile_ram_upload": True,
            "firmware_flash": False,
            "sd_card_write": False,
            "persistent_install": False,
        },
        "limitations": [
            "The retained observation is bound to one exact board identity and exact candidate bytes.",
            "No control sweep, audio path, real-time load, endurance, or electrical measurement was performed.",
            "This establishes level 6 only; levels 7 and 8 remain not-run.",
        ],
    }


def generated() -> tuple[dict[str, bytes], dict[str, Any]]:
    with tempfile.TemporaryDirectory(
        prefix="schuss-task021-fresh-processes-"
    ) as temporary:
        root = Path(temporary)
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
        if first["validation"]["status"] != "success":
            raise ValueError("Task 021 record closure is invalid")
        if first["plan"]["status"] != "success":
            raise ValueError("Task 021 exact build plan did not succeed")

        execution = first["execution"]["value"]
        if [item["status"] for item in execution["evidence_levels"]] != (
            ["passed"] * 5 + ["not-run"] * 3
        ):
            raise ValueError("build execution evidence levels are not separated")
        cpp_descriptor, cpp = _artifact_by_kind(
            execution, first_artifacts, "generated-cpp"
        )
        elf_descriptor, elf = _artifact_by_kind(
            execution, first_artifacts, "target-executable"
        )
        if (
            cpp_descriptor["byte_sha256"] != GENERATED_CPP_SHA256
            or len(cpp) != 19684
            or b"SchussOledCommand[2]" not in cpp
            or b"uint8_t bytes[2]" in cpp
            or b"SchussOledTx[0] = 0x40" not in cpp
        ):
            raise ValueError("generated C++ does not contain only the DMA-safe correction")
        if (
            elf_descriptor["byte_sha256"] != TARGET_ELF_SHA256
            or elf_descriptor["byte_length"] != TARGET_ELF_LENGTH
        ):
            raise ValueError("target executable differs from the connected candidate")
        binary = _device_binary(elf)
        if (
            hashlib.sha256(binary).hexdigest() != DEVICE_BINARY_SHA256
            or len(binary) != DEVICE_BINARY_LENGTH
        ):
            raise ValueError("derived device binary differs from the uploaded candidate")

        context = load_repository_context(record_set_path=RECORD_SET)
        evidence = next(
            value
            for value in context.records["evidence"]
            if value["evidence_claim_id"] == "schuss-evidence-claim-000037"
        )
        artifact = next(
            value
            for value in context.records["artifact"]
            if value["artifact_id"] == "schuss-artifact-000029"
        )
        fixture_diagnostics = validate_artifact_fixture_bytes(artifact, elf)
        if fixture_diagnostics:
            raise ValueError("retained artifact descriptor does not match target ELF")
        evidence_reference = {
            key: evidence[key]
            for key in ("evidence_claim_id", "revision", "content_hash")
        }
        artifact_reference = {
            key: artifact[key]
            for key in ("artifact_id", "revision", "content_hash")
        }
        observation = _observation(evidence_reference, artifact_reference)
        product_levels = [
            {
                "level": level,
                "status": "passed" if level <= 6 else "not-run",
            }
            for level in range(1, 9)
        ]
        summary = {
            "schema_version": "task021-validation-summary-v1",
            "status": "valid",
            "record_set_reference": first["record_set_reference"],
            "build_request_reference": REQUEST_REFERENCE,
            "instrument_reference": INSTRUMENT_REFERENCE,
            "runtime_realization_reference": RUNTIME_REFERENCE,
            "handler_reference": execution["handler_reference"],
            "evidence_claim_reference": evidence_reference,
            "target_executable_reference": artifact_reference,
            "plan_sha256": execution["plan_sha256"],
            "fresh_roots": 2,
            "fresh_processes": 2,
            "portable_results_identical": True,
            "artifact_bytes_identical": True,
            "records_validation_status": first["validation"]["status"],
            "plan_status": first["plan"]["status"],
            "artifacts": execution["artifacts"],
            "build_evidence_levels": execution["evidence_levels"],
            "product_evidence_levels": product_levels,
            "connected_device_observation_retained": True,
            "runner_device_actions_performed": False,
            "observed_volatile_ram_upload": True,
            "observed_firmware_flash": False,
            "observed_sd_card_write": False,
            "real_time_validation_performed": False,
            "audible_validation_performed": False,
            "java_used": False,
            "legacy_boundary_patch_used": False,
            "ambient_discovery_used": False,
        }
        files = {
            "validation-summary.json": core.canonical_json(summary).encode("utf-8")
            + b"\n",
            "portable-operation-result.json": core.canonical_json(
                first["execution"]
            ).encode("utf-8")
            + b"\n",
            "records-validation-result.json": core.canonical_json(
                first["validation"]
            ).encode("utf-8")
            + b"\n",
            "build-plan-result.json": core.canonical_json(first["plan"]).encode(
                "utf-8"
            )
            + b"\n",
            "connected-device-observation.json": core.canonical_json(
                observation
            ).encode("utf-8")
            + b"\n",
            "device-artifacts/sha256/" + DEVICE_BINARY_SHA256: binary,
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
    parser.add_argument("--source-configuration", type=Path)
    args = parser.parse_args()
    if args.source_configuration is not None and not args.reproduce:
        parser.error("--source-configuration requires --reproduce")
    if args.worker_root is not None:
        try:
            print(core.canonical_json(_worker(args.worker_root)))
        except (OSError, ValueError) as exc:
            print("Task 021 worker failed: " + str(exc), file=sys.stderr)
            return 1
        return 0
    try:
        if args.check:
            summary = check_retained()
            print(json.dumps(summary, sort_keys=True))
            return 0
        summary = reproduce_historical(args.source_configuration)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print("Task 021 execution failed: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
