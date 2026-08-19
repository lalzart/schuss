#!/usr/bin/env python3
"""Read-only Task 034 performance-control record-set validation."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "tools/contracts") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools/contracts"))

import aggregate_validator as aggregate  # noqa: E402
import performance_control_rules as performance  # noqa: E402
import record_set_rules  # noqa: E402
import validator_core as core  # noqa: E402


DEFAULT_RECORD_SET = Path(
    "contracts/record-sets/task034-performance-control-v1.json"
)


def validate(repository_root: Path, record_set_path: Path) -> dict[str, object]:
    selected = record_set_rules.load_record_set(repository_root, record_set_path)
    component_result = aggregate._component_record_set_validation(
        selected, repository_root
    )
    records = {
        "instruments_v0": [
            record
            for record in selected.records.get("instrument", ())
            if record.get("schema_version") == "instrument-v0"
        ],
        "instruments_v1": [
            record
            for record in selected.records.get("instrument", ())
            if record.get("schema_version") == "instrument-v1"
        ],
        "dsp_graphs": list(selected.records.get("dsp-graph", ())),
        "devices": list(selected.records.get("device-profile", ())),
        "performance_control_contracts": list(
            selected.records.get("performance-control-contract", ())
        ),
        "performance_control_graphs": list(
            selected.records.get("performance-control-graph", ())
        ),
        "performance_configurations": list(
            selected.records.get("performance-configuration", ())
        ),
    }
    schemas = {
        version: selected.schemas[version]
        for version in performance.SCHEMA_VERSIONS.values()
    }
    return performance.validate_values(
        records, schemas, component_result.graph_targets
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, default=ROOT)
    parser.add_argument("--record-set", type=Path, default=DEFAULT_RECORD_SET)
    args = parser.parse_args()
    summary = validate(args.repository_root.resolve(), args.record_set)
    print(core.canonical_json(summary))
    return 0 if summary["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
