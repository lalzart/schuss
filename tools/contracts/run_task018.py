#!/usr/bin/env python3
"""Run Task 018 twice in fresh processes and retain portable level-5 evidence."""

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
from packages.schuss_core.gills_mapped_backend import (  # noqa: E402
    INSTRUMENT_REFERENCE,
    REQUEST_REFERENCE,
    RUNTIME_REFERENCE,
    registration,
)

import historical_reproduction  # noqa: E402
import retained_evidence  # noqa: E402
import validator_core as core  # noqa: E402


RECORD_SET = ROOT / "contracts/record-sets/task018-full-gills-v1.json"
EVIDENCE_ROOT = ROOT / "evidence/task018-completion-v1"
HISTORICAL_COMMIT = "0ee69391bc2d43f4caf2580a3f0db139249d2307"


def check_retained() -> dict[str, Any]:
    return retained_evidence.check_summary(
        EVIDENCE_ROOT,
        repository_root=ROOT,
        anchor_commit=HISTORICAL_COMMIT,
        schema_version="task018-validation-summary-v1",
    )


def reproduce_historical(
    source_configuration: Path | None = None,
) -> dict[str, Any]:
    return historical_reproduction.reproduce_summary(
        repository_root=ROOT,
        completion_commit=HISTORICAL_COMMIT,
        runner_path=Path("tools/contracts/run_task018.py"),
        retained_summary=check_retained(),
        report_schema_version="task018-historical-reproduction-v1",
        source_configuration=(
            source_configuration
            if source_configuration is not None
            else ROOT / "catalog/sources.local.yml"
        ),
    )
INSTRUMENTS = {
    "executable": ("schuss-instrument-000002", 2),
    "percussion": ("schuss-instrument-000003", 2),
    "effects": ("schuss-instrument-000004", 2),
}
REQUESTS = {
    "executable": ("schuss-build-request-000002", 4),
    "percussion": ("schuss-build-request-000003", 2),
    "effects": ("schuss-build-request-000004", 2),
}


def _exact_reference(
    values: list[dict[str, Any]], id_field: str, identity: tuple[str, int]
) -> dict[str, Any]:
    matches = [
        value
        for value in values
        if (value[id_field], value["revision"]) == identity
    ]
    if len(matches) != 1:
        raise ValueError(f"exact {id_field} {identity!r} did not resolve once")
    return {
        id_field: matches[0][id_field],
        "revision": matches[0]["revision"],
        "content_hash": matches[0]["content_hash"],
    }


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
    inspections: dict[str, Any] = {}
    for name, identity in INSTRUMENTS.items():
        reference = _exact_reference(
            context.records["instruments"], "instrument_id", identity
        )
        inspections[name] = dispatch_operation(
            {
                "schema_version": "schuss-operation-request-v6",
                "canonical_profile": "schuss-canonical-json-v1",
                "operation": "gills.inspect",
                "payload": {"instrument_reference": reference},
            },
            context,
        )
    plans: dict[str, Any] = {}
    for name, identity in REQUESTS.items():
        reference = _exact_reference(
            context.records["request"], "build_request_id", identity
        )
        plans[name] = dispatch_operation(
            {
                "schema_version": "schuss-operation-request-v4",
                "canonical_profile": "schuss-canonical-json-v1",
                "operation": "build.plan",
                "payload": {"build_request_reference": reference},
            },
            context,
        )
    mapped = registration()
    published = output_parent / "published"
    service = ExecutionService.from_values((mapped,), published)
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
        "schema_version": "task018-fresh-process-result-v1",
        "record_set_reference": context.record_set_reference,
        "validation": validation,
        "inspections": inspections,
        "plans": plans,
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
            "mapped execution failed: " + core.canonical_json(execution["diagnostics"])
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


def generated() -> tuple[dict[str, bytes], dict[str, Any]]:
    with tempfile.TemporaryDirectory(prefix="schuss-task018-fresh-processes-") as temporary:
        temporary_root = Path(temporary)
        first_root = temporary_root / "fresh-a"
        second_root = temporary_root / "fresh-b-with-longer-name"
        first = _run_process(first_root)
        second = _run_process(second_root)
        if core.canonical_json(first) != core.canonical_json(second):
            raise ValueError("fresh-process canonical results differ")
        first_artifacts = _artifact_bytes(first, first_root)
        second_artifacts = _artifact_bytes(second, second_root)
        if first_artifacts != second_artifacts:
            raise ValueError("fresh-process artifact bytes differ")

        if first["validation"]["status"] != "success":
            raise ValueError("Task 018 accepted record closure is invalid")
        if any(value["status"] != "success" for value in first["inspections"].values()):
            raise ValueError("one or more exact Gills inspections failed")
        expected_plan_statuses = {
            "executable": "success",
            "percussion": "invalid",
            "effects": "unsupported",
        }
        actual_plan_statuses = {
            key: value["status"] for key, value in first["plans"].items()
        }
        if actual_plan_statuses != expected_plan_statuses:
            raise ValueError(
                "Task 018 plan outcomes differ: "
                + core.canonical_json(actual_plan_statuses)
            )
        diagnostic_codes = {
            key: sorted({item["code"] for item in value["diagnostics"]})
            for key, value in first["plans"].items()
        }
        if diagnostic_codes != {
            "executable": [],
            "percussion": ["COMPILER_COMPOUND_INTERNAL_BINDING_UNRESOLVED"],
            "effects": ["COMPILER_BINDING_UNSUPPORTED"],
        }:
            raise ValueError(
                "Task 017 successor diagnostics differ: "
                + core.canonical_json(diagnostic_codes)
            )
        execution_value = first["execution"]["value"]
        if [item["status"] for item in execution_value["evidence_levels"]] != (
            ["passed"] * 5 + ["not-run"] * 3
        ):
            raise ValueError("Task 018 evidence levels are not separated")
        inspected_runtime = first["inspections"]["executable"]["value"][
            "runtime_realization"
        ]
        if {
            key: inspected_runtime[key]
            for key in ("runtime_realization_id", "revision", "content_hash")
        } != RUNTIME_REFERENCE:
            raise ValueError("inspection and handler runtime realization differ")

        summary = {
            "schema_version": "task018-validation-summary-v1",
            "status": "valid",
            "record_set_reference": first["record_set_reference"],
            "build_request_reference": copy_reference(REQUEST_REFERENCE),
            "instrument_reference": copy_reference(INSTRUMENT_REFERENCE),
            "runtime_realization_reference": copy_reference(RUNTIME_REFERENCE),
            "handler_reference": execution_value["handler_reference"],
            "plan_sha256": execution_value["plan_sha256"],
            "fresh_roots": 2,
            "fresh_processes": 2,
            "portable_results_identical": True,
            "plans_and_diagnostics_identical": True,
            "artifact_bytes_identical": True,
            "records_validation_status": first["validation"]["status"],
            "inspection_statuses": {
                key: value["status"]
                for key, value in first["inspections"].items()
            },
            "plan_statuses": actual_plan_statuses,
            "plan_diagnostic_codes": diagnostic_codes,
            "artifacts": execution_value["artifacts"],
            "evidence_levels": execution_value["evidence_levels"],
            "output_publication": execution_value["output_publication"],
            "java_used": False,
            "legacy_boundary_patch_used": False,
            "ambient_discovery_used": False,
            "device_actions_performed": False,
            "connected_device_validation_performed": False,
            "real_time_validation_performed": False,
            "audible_validation_performed": False,
        }
        files = {
            "validation-summary.json": core.canonical_json(summary).encode("utf-8")
            + b"\n",
            "portable-operation-result.json": core.canonical_json(first["execution"]).encode("utf-8")
            + b"\n",
            "records-validation-result.json": core.canonical_json(first["validation"]).encode("utf-8")
            + b"\n",
        }
        for name, value in first["inspections"].items():
            files[f"inspections/{name}.json"] = core.canonical_json(value).encode("utf-8") + b"\n"
        for name, value in first["plans"].items():
            files[f"plans/{name}.json"] = core.canonical_json(value).encode("utf-8") + b"\n"
        for digest, payload in first_artifacts.items():
            files["artifacts/sha256/" + digest] = payload
        return files, summary


def copy_reference(value: dict[str, Any]) -> dict[str, Any]:
    return json.loads(core.canonical_json(value))


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
            print("Task 018 worker failed: " + str(exc), file=sys.stderr)
            return 1
        return 0
    try:
        if args.check:
            summary = check_retained()
            print(json.dumps(summary, sort_keys=True))
            return 0
        summary = reproduce_historical(args.source_configuration)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print("Task 018 execution failed: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
