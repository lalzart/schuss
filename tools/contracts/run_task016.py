#!/usr/bin/env python3
"""Run and retain the exact Task 016 direct build from two fresh roots."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/contracts")]

from packages.schuss_core.build_execution import ExecutionService, handler_reference  # noqa: E402
from packages.schuss_core.control_plane import dispatch_operation, load_repository_context  # noqa: E402
from packages.schuss_core.gills_direct_backend import registration  # noqa: E402

import validator_core as core  # noqa: E402


RECORD_SET = ROOT / "contracts/record-sets/task016-complete-gills-direct-v1.json"
EVIDENCE_ROOT = ROOT / "evidence/task016-completion-v1"


def _execute(context: Any, request_reference: dict[str, Any], prefix: str) -> tuple[dict[str, Any], dict[str, bytes]]:
    handler = registration()
    with tempfile.TemporaryDirectory(prefix=prefix) as temporary:
        output_root = Path(temporary) / "published"
        service = ExecutionService.from_values((handler,), output_root)
        operation = {
            "schema_version": "schuss-operation-request-v5",
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": "build.execute",
            "payload": {
                "build_request_reference": request_reference,
                "handler_reference": handler_reference(handler.descriptor),
                "output_locator": "build-output",
                "execution_intent": True,
            },
        }
        result = dispatch_operation(operation, context, execution_service=service)
        if result["status"] != "success":
            raise ValueError("direct execution failed: " + core.canonical_json(result["diagnostics"]))
        artifacts = {
            item["byte_sha256"]: (
                output_root / "artifacts" / item["portable_locator"]
            ).read_bytes()
            for item in result["value"]["artifacts"]
        }
        return result, artifacts


def generated() -> tuple[dict[str, bytes], dict[str, Any]]:
    context = load_repository_context(record_set_path=RECORD_SET)
    request = next(
        item for item in context.records["request"]
        if item["build_request_id"] == "schuss-build-request-000002" and item["revision"] == 3
    )
    reference = {
        key: request[key]
        for key in ("build_request_id", "revision", "content_hash")
    }
    first, first_artifacts = _execute(context, reference, "schuss-task016-root-a-")
    second, second_artifacts = _execute(context, reference, "schuss-task016-root-b-")
    if core.canonical_json(first) != core.canonical_json(second):
        raise ValueError("fresh-root portable operation results differ")
    if first_artifacts != second_artifacts:
        raise ValueError("fresh-root artifact bytes differ")
    value = first["value"]
    statuses = [item["status"] for item in value["evidence_levels"]]
    if statuses != ["passed"] * 5 + ["not-run"] * 3:
        raise ValueError("evidence levels are not separated at the Task 016 boundary")
    summary = {
        "schema_version": "task016-validation-summary-v1",
        "status": "valid",
        "record_set_reference": context.record_set_reference,
        "build_request_reference": reference,
        "handler_reference": value["handler_reference"],
        "plan_sha256": value["plan_sha256"],
        "fresh_root_runs": 2,
        "portable_operation_results_identical": True,
        "artifact_bytes_identical": True,
        "artifacts": value["artifacts"],
        "evidence_levels": value["evidence_levels"],
        "output_publication": value["output_publication"],
        "java_used": False,
        "legacy_boundary_patch_used": False,
        "ambient_discovery_used": False,
        "device_actions_performed": False,
        "real_time_validation_performed": False,
        "audible_validation_performed": False,
    }
    files = {
        "validation-summary.json": core.canonical_json(summary).encode("utf-8") + b"\n",
        "portable-operation-result.json": core.canonical_json(first).encode("utf-8") + b"\n",
    }
    for digest, payload in first_artifacts.items():
        if hashlib.sha256(payload).hexdigest() != digest:
            raise ValueError("retained artifact bytes do not match their digest")
        files["artifacts/sha256/" + digest] = payload
    return files, summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        files, summary = generated()
        stale = [
            relative for relative, payload in files.items()
            if not (EVIDENCE_ROOT / relative).is_file()
            or (EVIDENCE_ROOT / relative).read_bytes() != payload
        ]
        if args.check and stale:
            raise ValueError("retained evidence is stale: " + ", ".join(sorted(stale)))
        if not args.check:
            expected_artifacts = {
                (EVIDENCE_ROOT / relative).resolve()
                for relative in files
                if relative.startswith("artifacts/sha256/")
            }
            artifact_root = EVIDENCE_ROOT / "artifacts/sha256"
            if artifact_root.is_dir():
                for obsolete in artifact_root.iterdir():
                    if obsolete.is_file() and obsolete.resolve() not in expected_artifacts:
                        obsolete.unlink()
            for relative, payload in files.items():
                path = EVIDENCE_ROOT / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
    except (OSError, ValueError) as exc:
        print("Task 016 execution failed: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
