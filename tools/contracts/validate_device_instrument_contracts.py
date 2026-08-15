#!/usr/bin/env python3
"""Read-only validation for Schuss device-profile-v0 and instrument-v0 records."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

TOOLS_ROOT = Path(__file__).resolve().parent
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

import aggregate_validator as aggregate
import device_instrument_rules as rules
import record_set_rules
import validator_core as core


for _name in dir(rules):
    if not _name.startswith("__"):
        globals()[_name] = getattr(rules, _name)

_record_files = core.record_files


def validate_contract_directory(contract_root: Path, schema_root: Path) -> dict:
    return aggregate.validate_device_instrument_directory(
        contract_root,
        schema_root,
        Path(__file__).resolve().parents[2],
    )


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    repository_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "contract_root",
        nargs="?",
        type=Path,
        default=repository_root / "contracts",
    )
    parser.add_argument(
        "--schema-root",
        type=Path,
        default=repository_root / "schemas",
    )
    parser.add_argument("--canonical-record", type=Path)
    parser.add_argument(
        "--record-kind",
        choices=("device-profile", "instrument"),
        help="schema family for --canonical-record",
    )
    parser.add_argument(
        "--record-set",
        type=Path,
        help="exact record-set manifest; the repository default uses the accepted Task 005-008 set",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.canonical_record is not None:
        if args.record_kind is None:
            print("--canonical-record requires --record-kind", file=sys.stderr)
            return 2
        try:
            schema_name = (
                DEVICE_SCHEMA_NAME
                if args.record_kind == "device-profile"
                else INSTRUMENT_SCHEMA_NAME
            )
            schema = load_json(args.schema_root / schema_name)
            record = load_json(args.canonical_record)
            errors = _schema_errors(record, schema, schema)
            if errors:
                raise ValueError("; ".join(errors))
            sys.stdout.buffer.write(canonical_record_bytes(record, schema) + b"\n")
            return 0
        except (OSError, ValueError) as exc:
            print(f"canonical record emission failed: {exc}", file=sys.stderr)
            return 1
    try:
        repository_root = Path(__file__).resolve().parents[2]
        use_default_set = (
            args.contract_root.resolve() == (repository_root / "contracts").resolve()
            and args.schema_root.resolve() == (repository_root / "schemas").resolve()
        )
        if args.record_set is not None or use_default_set:
            selected = record_set_rules.load_record_set(
                repository_root,
                args.record_set or record_set_rules.ACCEPTED_RECORD_SET,
            )
            summary = aggregate.validate_device_instrument_record_set(
                selected,
                repository_root,
            )
        else:
            summary = validate_contract_directory(args.contract_root, args.schema_root)
    except (OSError, ValueError) as exc:
        summary = {
            "schema_version": "device-instrument-validation-summary-v0",
            "status": "invalid",
            "record_counts": {"device_profiles": 0, "instruments": 0},
            "reference_resolution": {
                "device_profiles_resolved": 0,
                "graphs_deferred": 0,
                "graphs_resolved": 0,
            },
            "evidence_levels": [
                {"level": "structural-schema", "status": "failed"},
                {"level": "component-graph-resolution", "status": "not-run"},
                {"level": "backend-lowering", "status": "not-run"},
                {"level": "artifact-generation", "status": "not-run"},
                {"level": "arm-compile-link", "status": "not-run"},
                {"level": "connected-device", "status": "not-run"},
                {"level": "real-time-resource", "status": "not-run"},
                {"level": "audible-listening", "status": "not-run"},
            ],
            "diagnostics": [
                Diagnostic(
                    "INPUT_READ_FAILED",
                    "error",
                    str(args.contract_root),
                    "$",
                    str(exc),
                ).as_dict()
            ],
        }
    print(canonical_json(summary))
    return 0 if summary["status"] != "invalid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
