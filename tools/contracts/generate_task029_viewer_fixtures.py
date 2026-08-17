#!/usr/bin/env python3
"""Generate Machine Viewer fixtures only through machine.inspect."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/contracts")]

from packages.schuss_core.control_plane import (  # noqa: E402
    canonical_result_bytes,
    dispatch_operation,
    load_repository_context,
)

import validator_core as core  # noqa: E402


RECORD_SET = ROOT / "contracts/record-sets/task029-gills-machines-v1.json"
FIXTURE_ROOT = ROOT / "apps/schuss_machine_viewer/fixtures"


def generated() -> dict[Path, bytes]:
    context = load_repository_context(record_set_path=RECORD_SET)
    outputs: dict[Path, bytes] = {}
    names = {
        "Palimpsest": "palimpsest-machine-inspect.json",
        "Tide Pit": "tide-pit-machine-inspect.json",
    }
    for review in context.records["machine_source_reviews"]:
        reference = {
            key: review[key]
            for key in ("machine_source_review_id", "revision", "content_hash")
        }
        request = {
            "schema_version": "schuss-operation-request-v9",
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": "machine.inspect",
            "payload": {"source_review_reference": reference},
        }
        result = dispatch_operation(request, context)
        if result["status"] != "success":
            raise ValueError("machine.inspect fixture generation failed")
        outputs[FIXTURE_ROOT / names[review["asserted_identity"]["display_name"]]] = (
            canonical_result_bytes(result, context) + b"\n"
        )
    requests = [
        {
            "schema_version": "schuss-operation-request-v9",
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": "machine.inspect",
            "payload": {
                "source_review_reference": {
                    key: review[key]
                    for key in ("machine_source_review_id", "revision", "content_hash")
                }
            },
        }
        for review in context.records["machine_source_reviews"]
    ]
    outputs[ROOT / "tools/contracts/tests/fixtures/task029-machine-operation-requests.json"] = (
        core.canonical_json(requests).encode("utf-8") + b"\n"
    )
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = generated()
    if args.check:
        stale = [path.relative_to(ROOT).as_posix() for path, data in outputs.items() if not path.is_file() or path.read_bytes() != data]
        if stale:
            raise SystemExit("stale Task 029 Viewer fixtures: " + ", ".join(sorted(stale)))
    else:
        for path, data in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    print(core.canonical_json({"fixture_count": 2, "operation": "machine.inspect", "status": "fresh"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
