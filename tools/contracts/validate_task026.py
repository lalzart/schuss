from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/contracts"))

import validator_core as core  # noqa: E402


def run(*command: str) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    run("python3", "tools/contracts/validate_task026_contract.py")
    run("python3", "tools/contracts/generate_task026b_records.py", "--check")
    run("python3", "tools/contracts/generate_task026_cli_golden.py", "--check")
    run(
        "python3",
        "-m",
        "unittest",
        "tools.contracts.tests.test_task026_authoring_workflow",
    )
    summary = core.load_json(
        ROOT / "evidence/task026-completion-v1/validation-summary.json"
    )
    artifacts = core.load_json(
        ROOT / "evidence/task026-completion-v1/artifact-hashes.json"
    )
    manifest = core.load_json(
        ROOT / "contracts/record-sets/task026-authoring-workflow-v1.json"
    )
    expected_reference = {
        key: manifest[key]
        for key in ("record_set_id", "revision", "content_hash")
    }
    if summary.get("status") != "passed":
        raise ValueError("Task 026 end-to-end summary is not passed")
    if summary.get("record_set_reference") != expected_reference:
        raise ValueError("Task 026 evidence does not name the exact current record set")
    if artifacts.get("record_set_reference") != expected_reference:
        raise ValueError("Task 026 artifact evidence names a stale record set")
    if summary.get("fresh_workspace_runs") != 2:
        raise ValueError("Task 026 evidence lacks two fresh workspace runs")
    expected_levels = [
        {"level": level, "status": "passed" if level <= 5 else "not-run"}
        for level in range(1, 9)
    ]
    if summary.get("evidence_levels") != expected_levels:
        raise ValueError("Task 026 evidence levels cross the accepted boundary")
    for flag in (
        "reverb_consumed",
        "java_used",
        "legacy_boundary_patch_used",
        "device_actions_performed",
        "real_time_validation_performed",
        "audible_validation_performed",
        "git_publication_performed",
    ):
        if summary.get(flag) is not False:
            raise ValueError(f"Task 026 evidence flag {flag} is not false")
    print("Task 026 complete authoring workflow: valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
