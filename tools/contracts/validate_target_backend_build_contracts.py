#!/usr/bin/env python3
"""Read-only Task 007 target, backend, build, artifact, resource, and evidence validation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

TOOLS_ROOT = Path(__file__).resolve().parent
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

import aggregate_validator as aggregate
import target_backend_build_rules as rules
import validator_core as core


for _name in dir(rules):
    if not _name.startswith("__"):
        globals()[_name] = getattr(rules, _name)

base = core
validate_target_backend_build_directory = (
    aggregate.validate_target_backend_build_directory
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
    parser.add_argument("--schema-root", type=Path, default=repository_root / "schemas")
    parser.add_argument("--canonical-record", type=Path)
    parser.add_argument("--record-kind", choices=tuple(sorted(SCHEMA_SPECS)))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    repository_root = Path(__file__).resolve().parents[2]
    if args.canonical_record is not None:
        if args.record_kind is None:
            print("--canonical-record requires --record-kind", file=sys.stderr)
            return 2
        try:
            schema = core.load_json(args.schema_root / SCHEMA_SPECS[args.record_kind][0])
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
        result = validate_target_backend_build_directory(
            args.contract_root,
            args.schema_root,
            repository_root,
        )
        summary = result.summary
    except (OSError, ValueError, KeyError) as exc:
        summary = {
            "schema_version": "task-007-validation-summary-v0",
            "status": "invalid",
            "record_counts": {},
            "reference_resolution": {},
            "evidence_levels": [],
            "resolution_traces": [],
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
    return 0 if summary["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
