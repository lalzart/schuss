#!/usr/bin/env python3
"""Validate the exact Task 022 offline boundary without device access."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/contracts")]

from packages.schuss_core.control_plane import (  # noqa: E402
    dispatch_operation,
    load_repository_context,
)
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

import generate_task021_records as task021_generator  # noqa: E402
import generate_task022_records as generator  # noqa: E402
import task022_connected_observation as connected_observation  # noqa: E402
import validator_core as core  # noqa: E402
from target_backend_build_rules import validate_artifact_fixture_bytes  # noqa: E402


RECORD_SET = ROOT / "contracts/record-sets/task022-gills-panel-diagnostic-v1.json"
EVIDENCE = ROOT / "evidence/task022-completion-v1"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate() -> dict[str, object]:
    generated_files, manifest, generated_summary = generator.generated()
    generated_files[RECORD_SET.relative_to(ROOT).as_posix()] = manifest
    _require(
        all(
            (ROOT / relative).is_file()
            and (ROOT / relative).read_bytes() == payload
            for relative, payload in generated_files.items()
        ),
        "Task 022 generated record bytes are stale",
    )
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
    _require(validation["status"] == "success", "Task 022 record set is invalid")
    manifest_value = core.load_json(RECORD_SET)
    for member in manifest_value["record_members"]:
        path = ROOT / member["portable_path"]
        _require(
            path.is_file() and core.sha256_file(path) == member["byte_sha256"],
            "Task 022 manifest path/hash check failed: " + member["portable_path"],
        )
    artifact_reference = generated_summary["artifact"]
    matches = [
        value
        for value in context.records["artifact"]
        if all(value.get(key) == item for key, item in artifact_reference.items())
    ]
    _require(len(matches) == 1, "Task 022 artifact descriptor did not resolve once")
    elf = (EVIDENCE / "artifacts/sha256" / TARGET_ELF_SHA256).read_bytes()
    _require(
        not validate_artifact_fixture_bytes(matches[0], elf),
        "Task 022 retained ELF differs from its artifact descriptor",
    )
    cpp = (EVIDENCE / "artifacts/sha256" / GENERATED_CPP_SHA256).read_bytes()
    binary = (EVIDENCE / "device-artifacts/sha256" / DEVICE_BINARY_SHA256).read_bytes()
    _require(
        len(cpp) == GENERATED_CPP_LENGTH
        and hashlib.sha256(cpp).hexdigest() == GENERATED_CPP_SHA256,
        "Task 022 generated C++ fixture differs",
    )
    _require(
        len(elf) == TARGET_ELF_LENGTH
        and hashlib.sha256(elf).hexdigest() == TARGET_ELF_SHA256,
        "Task 022 ELF fixture differs",
    )
    _require(
        len(binary) == DEVICE_BINARY_LENGTH
        and hashlib.sha256(binary).hexdigest() == DEVICE_BINARY_SHA256,
        "Task 022 binary fixture differs",
    )
    summary = core.load_json(EVIDENCE / "validation-summary.json")
    _require(summary["status"] == "valid", "Task 022 offline summary is invalid")
    _require(
        summary["task_state"] == "ready-for-diagnostic-upload-approval",
        "Task 022 offline state is inflated or stale",
    )
    _require(
        summary["diagnostic_identity"] == diagnostic_identity()
        and summary["diagnostic_procedure_reference"]
        == {
            key: diagnostic_procedure()[key]
            for key in ("stable_id", "revision", "content_hash")
        },
        "Task 022 diagnostic or procedure identity differs",
    )
    _require(
        summary["generated_cpp_sha256"] == GENERATED_CPP_SHA256
        and summary["generated_cpp_byte_length"] == GENERATED_CPP_LENGTH
        and summary["target_elf_sha256"] == TARGET_ELF_SHA256
        and summary["target_elf_byte_length"] == TARGET_ELF_LENGTH
        and summary["device_binary_sha256"] == DEVICE_BINARY_SHA256
        and summary["device_binary_byte_length"] == DEVICE_BINARY_LENGTH,
        "Task 022 summary artifact facts differ",
    )
    _require(
        summary["fresh_roots"] == 2
        and summary["fresh_processes"] == 2
        and summary["portable_results_identical"] is True
        and summary["artifact_bytes_identical"] is True,
        "Task 022 determinism evidence differs",
    )
    _require(
        [item["status"] for item in summary["build_evidence_levels"]]
        == ["passed"] * 5 + ["not-run"] * 3,
        "Task 022 evidence levels are not separated",
    )
    _require(
        summary["device_profile_diagnostic_level_6"] == "not-run"
        and summary["task021_mapping_level_6"] == "not-run"
        and summary["real_time_resource_level_7"] == "not-run"
        and summary["audible_listening_level_8"] == "not-run",
        "Task 022 connected or later evidence was inflated",
    )
    _require(
        summary["runner_device_actions_performed"] is False
        and summary["observed_volatile_ram_uploads"] == 0
        and summary["firmware_flash_performed"] is False
        and summary["sd_card_write_performed"] is False,
        "Task 022 offline runner claims a device action",
    )
    template = core.load_json(EVIDENCE / "connected-result-template.json")
    _require(
        template["status"] == "not-run"
        and template["promotion_eligible"] is False
        and len(template["pots"]) == 10
        and len(template["buttons"]) == 4
        and len(template["led_channels"]) == 6,
        "Task 022 connected result template is partial or promoted",
    )
    _require(
        all(
            value == "not-run"
            for item in template["pots"]
            for key, value in item.items()
            if key not in {"slot", "raw_observations"}
        ),
        "Task 022 pot template omits an explicit not-run result",
    )
    observation_path = EVIDENCE / "connected-device-observation.json"
    _require(
        observation_path.read_bytes() == connected_observation.expected_bytes(),
        "Task 022 connected failed-observation bytes are stale",
    )
    observation = core.load_json(observation_path)
    _require(
        observation["status"] == "failed"
        and observation["promotion_eligible"] is False
        and observation["failure"]["code"] == "POT_EVENT_FOCUS_UNSTABLE"
        and observation["failure"]["promotion_stopped"] is True,
        "Task 022 connected failure boundary differs",
    )
    _require(
        observation["write_boundaries"]["volatile_ram_uploads_performed"] == 1
        and observation["write_boundaries"]["second_upload_performed"] is False
        and observation["write_boundaries"]["firmware_flash"] is False
        and observation["write_boundaries"]["sd_card_write"] is False,
        "Task 022 connected write boundary differs",
    )
    _require(
        observation["evidence_levels"]["device_profile_diagnostic_level_6"]
        == "not-run-failed-before-promotion"
        and observation["evidence_levels"]["task021_instrument_mapping_level_6"]
        == "not-run"
        and observation["task021_product_mapping"]["approval_gate_2"]
        == "closed-after-diagnostic-failure",
        "Task 022 failed promotion or closed gate differs",
    )
    task021_files, task021_manifest, _ = task021_generator.generated()
    task021_files[
        "contracts/record-sets/task021-gills-dma-safe-v1.json"
    ] = task021_manifest
    _require(
        all((ROOT / relative).read_bytes() == payload for relative, payload in task021_files.items()),
        "Task 021 generated bytes changed",
    )
    return {
        "schema_version": "task022-validator-result-v1",
        "status": "valid",
        "task_state": "diagnostic-failed-promotion-stopped",
        "record_set_reference": context.record_set_reference,
        "diagnostic_identity": diagnostic_identity(),
        "target_elf_sha256": TARGET_ELF_SHA256,
        "target_elf_byte_length": TARGET_ELF_LENGTH,
        "device_binary_sha256": DEVICE_BINARY_SHA256,
        "device_binary_byte_length": DEVICE_BINARY_LENGTH,
        "fresh_processes": 2,
        "connected_device_validation_performed": True,
        "level6_claim_count": 0,
        "real_time_validation_performed": False,
        "audible_validation_performed": False,
        "device_actions_performed": True,
        "publication_performed": False,
    }


def main() -> int:
    try:
        result = validate()
    except (OSError, KeyError, TypeError, ValueError) as exc:
        print("Task 022 validation failed: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
