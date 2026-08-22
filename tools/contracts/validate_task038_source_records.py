#!/usr/bin/env python3
"""Validate the Task 038 source-only record-set successor."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "tools/contracts") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools/contracts"))

from tools.contracts import generate_task038_source_records as generator  # noqa: E402
from tools.contracts import record_set_rules  # noqa: E402
from tools.contracts import validator_core as core  # noqa: E402


def validate() -> dict[str, object]:
    files, manifest_bytes, summary = generator.generated()
    stale = [
        path for path, expected in sorted(files.items())
        if not (ROOT / path).is_file() or (ROOT / path).read_bytes() != expected
    ]
    output = ROOT / generator.OUTPUT_PATH
    if not output.is_file() or output.read_bytes() != manifest_bytes:
        stale.append(generator.OUTPUT_PATH.as_posix())
    if stale:
        raise ValueError("stale Task 038 source records: " + ", ".join(stale))
    parent = record_set_rules.load_record_set(ROOT, generator.PARENT_PATH)
    selected = record_set_rules.load_record_set(ROOT, generator.OUTPUT_PATH)
    parent_members = {
        core.canonical_json(item) for item in parent.manifest["record_members"]
    }
    selected_members = {
        core.canonical_json(item) for item in selected.manifest["record_members"]
    }
    if not parent_members <= selected_members:
        raise ValueError("Task 038 changed a parent record member")
    additions = selected_members - parent_members
    if len(additions) != 2:
        raise ValueError("Task 038 must add exactly two source-release records")
    records = selected.records.get("source-release", ())
    added_ids = {
        record["source_release_id"] for record in records
        if record["source_release_id"] in {
            "schuss-source-release-000008", "schuss-source-release-000009"
        }
    }
    if added_ids != {"schuss-source-release-000008", "schuss-source-release-000009"}:
        raise ValueError("Task 038 source-release allocation drifted")
    for kind in ("object-collection", "implementation-provider"):
        if selected.records.get(kind) != parent.records.get(kind):
            raise ValueError(f"Task 038 changed {kind} records")
    return summary


def main() -> int:
    print(core.canonical_json(validate()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
