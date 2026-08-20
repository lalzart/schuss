#!/usr/bin/env python3
"""Prove Task 029 machine.inspect fixture bytes in fresh CLI processes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/contracts"))

import retained_evidence  # noqa: E402
import validator_core as core  # noqa: E402


CLI = ROOT / "bin/schuss"
RECORD_SET = ROOT / "contracts/record-sets/task029-gills-machines-v1.json"
REQUESTS = ROOT / "tools/contracts/tests/fixtures/task029-machine-operation-requests.json"
FIXTURES = {
    "schuss-machine-source-review-000001": ROOT / "apps/schuss_machine_viewer/fixtures/palimpsest-machine-inspect.json",
    "schuss-machine-source-review-000002": ROOT / "apps/schuss_machine_viewer/fixtures/tide-pit-machine-inspect.json",
}
EVIDENCE_ROOT = ROOT / "evidence/task029-completion-v1"
HISTORICAL_COMMIT = "936d186bb7c01cf1cbfbb4b40e679eac5af3aa3e"
ACCEPTED_FIXTURE_PATHS = (
    Path("tools/contracts/tests/fixtures/task029-machine-operation-requests.json"),
    Path("apps/schuss_machine_viewer/fixtures/palimpsest-machine-inspect.json"),
    Path("apps/schuss_machine_viewer/fixtures/tide-pit-machine-inspect.json"),
)


def check_retained() -> dict[str, object]:
    retained_evidence.check_closure(
        EVIDENCE_ROOT,
        repository_root=ROOT,
        anchor_commit=HISTORICAL_COMMIT,
    )
    retained_evidence.check_files(
        ACCEPTED_FIXTURE_PATHS,
        repository_root=ROOT,
        anchor_commit=HISTORICAL_COMMIT,
    )
    acceptance = core.load_json(EVIDENCE_ROOT / "acceptance-matrix.json")
    reproduction_rows = [
        row
        for row in acceptance.get("acceptance_rows", [])
        if row.get("command")
        == "python3 tools/contracts/run_task029_fresh_process.py"
    ]
    if reproduction_rows != [
        {
            "command": "python3 tools/contracts/run_task029_fresh_process.py",
            "evidence": (
                "2 exact references matched canonical fixtures in 4 fresh CLI "
                "processes and 2 CWDs"
            ),
            "result": "passed",
        }
    ]:
        raise ValueError("Task 029 retained fresh-process claim is stale")
    summary = core.load_json(EVIDENCE_ROOT / "validation-summary.json")
    if (
        summary.get("schema_version") != "task029-validation-summary-v1"
        or summary.get("status") != "passed-with-documented-inherited-boundaries"
    ):
        raise ValueError("Task 029 retained validation boundary is stale")
    return summary


def reproduce() -> dict[str, object]:
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
    return {
        "schema_version": "task029-fresh-process-result-v0",
        "status": "passed",
        "operation": "machine.inspect",
        "reference_count": len(requests),
        "fresh_process_count": process_count,
        "cwd_count": 2,
        "canonical_fixture_match": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--reproduce", action="store_true")
    args = parser.parse_args()
    try:
        result = check_retained() if args.check else reproduce()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print("Task 029 fresh-process validation failed: " + str(exc), file=sys.stderr)
        return 1
    print(core.canonical_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
