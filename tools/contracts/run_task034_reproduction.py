#!/usr/bin/env python3
"""Produce deterministic Task 034 structural and operation fingerprints."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.schuss_core.control_plane import (  # noqa: E402
    canonical_result_bytes,
    dispatch_operation,
    load_repository_context,
)
from tools.contracts import validator_core as core  # noqa: E402


RECORD_SET = Path("contracts/record-sets/task034-performance-control-v1.json")


def reproduce(repository_root: Path) -> dict[str, object]:
    context = load_repository_context(
        repository_root=repository_root,
        record_set_path=RECORD_SET,
    )
    inspections: list[dict[str, str]] = []
    for configuration in context.records["performance_configurations"]:
        reference = {
            key: configuration[key]
            for key in (
                "performance_configuration_id",
                "revision",
                "content_hash",
            )
        }
        request = {
            "schema_version": "schuss-operation-request-v17",
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": "performance.inspect",
            "payload": {"performance_configuration_reference": reference},
        }
        result = dispatch_operation(request, context)
        if result["status"] != "success":
            raise ValueError(core.canonical_json(result))
        result_bytes = canonical_result_bytes(result, context)
        inspections.append(
            {
                "performance_configuration_id": configuration[
                    "performance_configuration_id"
                ],
                "result_sha256": hashlib.sha256(result_bytes).hexdigest(),
            }
        )
    return {
        "schema_version": "task034-reproduction-summary-v1",
        "status": "valid",
        "record_set_reference": context.record_set_reference,
        "performance_validation_sha256": hashlib.sha256(
            core.canonical_json(context.performance_summary).encode("utf-8")
        ).hexdigest(),
        "inspections": inspections,
        "control_graph_execution": "not-run",
        "native_build_or_device_access_performed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, default=ROOT)
    args = parser.parse_args()
    print(core.canonical_json(reproduce(args.repository_root.resolve())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
