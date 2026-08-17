from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validator_core as core


ROOT = Path(__file__).resolve().parents[2]


def run(*arguments: str) -> None:
    completed = subprocess.run(arguments, cwd=ROOT, check=False)
    if completed.returncode:
        raise SystemExit(completed.returncode)


def main() -> int:
    run(sys.executable, "tools/contracts/validate_task026_contract.py")
    run(sys.executable, "tools/contracts/generate_task026a_records.py", "--check")
    run(sys.executable, "-m", "unittest", "tools.contracts.tests.test_task026a_executable_profile")
    summary = core.load_json(ROOT / "evidence/task026a-executable-profile-v1/validation-summary.json")
    artifacts = core.load_json(ROOT / "evidence/task026a-executable-profile-v1/artifact-hashes.json")
    if summary["status"] != "passed" or summary["fresh_output_root_runs"] != 2:
        raise SystemExit("Task 026A retained reproduction summary is not passed")
    if [item["status"] for item in summary["evidence_levels"]] != ["passed"] * 5 + ["not-run"] * 3:
        raise SystemExit("Task 026A evidence-level boundary differs")
    if summary["artifact_hashes_sha256"] != __import__("hashlib").sha256(core.canonical_json(artifacts).encode("utf-8")).hexdigest():
        raise SystemExit("Task 026A artifact-hash evidence differs")
    if any(summary[key] for key in ("reverb_consumed", "device_actions_performed", "real_time_validation_performed", "audible_validation_performed", "git_publication_performed")):
        raise SystemExit("Task 026A evidence records a prohibited action")
    print("Task 026A executable profile: valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
