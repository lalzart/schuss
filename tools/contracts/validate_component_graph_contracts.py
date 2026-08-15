#!/usr/bin/env python3
"""Read-only validation for Task 006 component, binding, and graph contracts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

TOOLS_ROOT = Path(__file__).resolve().parent
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

import aggregate_validator as aggregate
import component_graph_rules as rules
import device_instrument_rules as device
import validator_core as core


for _name in dir(rules):
    if not _name.startswith("__"):
        globals()[_name] = getattr(rules, _name)

base = core
validate_all_contracts = aggregate.validate_all_contracts


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    repository_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "contract_root",
        nargs="?",
        type=Path,
        default=repository_root / "contracts",
    )
    parser.add_argument("--schema-root", type=Path, default=repository_root / "schemas")
    parser.add_argument("--canonical-record", type=Path)
    parser.add_argument(
        "--record-kind",
        choices=(
            "catalog-family-companion",
            "component-contract",
            "implementation-binding",
            "dsp-graph",
            "device-profile",
            "instrument",
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    repository_root = Path(__file__).resolve().parents[2]
    if args.canonical_record is not None:
        if args.record_kind is None:
            print("--canonical-record requires --record-kind", file=sys.stderr)
            return 2
        schema_name = {
            "catalog-family-companion": FAMILY_SCHEMA_NAME,
            "component-contract": CONTRACT_SCHEMA_NAME,
            "implementation-binding": BINDING_SCHEMA_NAME,
            "dsp-graph": GRAPH_SCHEMA_NAME,
            "device-profile": device.DEVICE_SCHEMA_NAME,
            "instrument": device.INSTRUMENT_SCHEMA_NAME,
        }[args.record_kind]
        try:
            schema = core.load_json(args.schema_root / schema_name)
            record = core.load_json(args.canonical_record)
            errors = core.schema_errors(record, schema, schema)
            if errors:
                raise ValueError("; ".join(errors))
            sys.stdout.buffer.write(core.canonical_record_bytes(record, schema) + b"\n")
            return 0
        except (OSError, ValueError) as exc:
            print(f"canonical record emission failed: {exc}", file=sys.stderr)
            return 1
    try:
        summary = validate_all_contracts(args.contract_root, args.schema_root, repository_root)
    except (OSError, ValueError) as exc:
        summary = {
            "schema_version": "task-006-validation-summary-v0",
            "status": "invalid",
            "record_counts": {},
            "reference_resolution": {},
            "evidence_levels": [],
            "diagnostics": [
                core.Diagnostic(
                    "INPUT_READ_FAILED",
                    "error",
                    str(args.contract_root),
                    "$",
                    str(exc),
                ).as_dict()
            ],
        }
    print(core.canonical_json(summary))
    return 0 if summary["status"] != "invalid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
