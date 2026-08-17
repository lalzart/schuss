#!/usr/bin/env python3
"""Prove Task 029 machine.inspect fixture bytes in fresh CLI processes."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/contracts"))

import validator_core as core  # noqa: E402


CLI = ROOT / "bin/schuss"
RECORD_SET = ROOT / "contracts/record-sets/task029-gills-machines-v1.json"
REQUESTS = ROOT / "tools/contracts/tests/fixtures/task029-machine-operation-requests.json"
FIXTURES = {
    "schuss-machine-source-review-000001": ROOT / "apps/schuss_machine_viewer/fixtures/palimpsest-machine-inspect.json",
    "schuss-machine-source-review-000002": ROOT / "apps/schuss_machine_viewer/fixtures/tide-pit-machine-inspect.json",
}


def main() -> int:
    requests = json.loads(REQUESTS.read_text(encoding="utf-8"))
    if len(requests) != 2:
        raise ValueError("Task 029 requires exactly two machine inspection requests")
    process_count = 0
    for request in requests:
        reference = request["payload"]["source_review_reference"]
        expected = FIXTURES[reference["machine_source_review_id"]].read_bytes()
        encoded = core.canonical_json(request).encode("utf-8") + b"\n"
        for cwd in (ROOT, ROOT.parent):
            completed = subprocess.run(
                [
                    str(CLI),
                    "op",
                    "--request",
                    "-",
                    "--record-set",
                    str(RECORD_SET),
                    "--json",
                ],
                cwd=cwd,
                input=encoded,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            process_count += 1
            if completed.returncode != 0:
                raise ValueError(
                    f"fresh machine.inspect failed from {cwd}: "
                    + completed.stderr.decode("utf-8", errors="replace")
                )
            if completed.stdout != expected:
                raise ValueError(
                    f"fresh machine.inspect bytes differ for "
                    f'{reference["machine_source_review_id"]} from {cwd}'
                )
    print(
        core.canonical_json(
            {
                "schema_version": "task029-fresh-process-result-v0",
                "status": "passed",
                "operation": "machine.inspect",
                "reference_count": len(requests),
                "fresh_process_count": process_count,
                "cwd_count": 2,
                "canonical_fixture_match": True,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
