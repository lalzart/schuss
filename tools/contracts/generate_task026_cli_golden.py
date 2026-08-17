from __future__ import annotations

import argparse
import hashlib
import io
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools/contracts"))

from packages.schuss_core.cli import run as run_cli  # noqa: E402
from packages.schuss_core.project_cli import project_completion_script  # noqa: E402

import validator_core as core  # noqa: E402


FIXTURE = ROOT / "tools/contracts/tests/fixtures/task026-cli-successor-golden-hashes.json"
RECORD_SET = ROOT / "contracts/record-sets/task026-authoring-workflow-v1.json"


def fact(data: bytes) -> dict[str, object]:
    return {
        "byte_length": len(data),
        "byte_sha256": hashlib.sha256(data).hexdigest(),
    }


def invoke(arguments: list[str]) -> bytes:
    stdout = io.BytesIO()
    stderr = io.StringIO()
    code = run_cli(arguments, io.BytesIO(), stdout, stderr)
    if code != 0 or stderr.getvalue():
        raise ValueError(
            f"CLI golden command failed: {arguments}: {code}: {stderr.getvalue()}"
        )
    return stdout.getvalue()


def generated() -> dict[str, object]:
    help_cases = {
        "project": ["project", "--help"],
        "project-create": ["project", "create", "--help"],
        "project-edit": ["project", "edit", "--help"],
        "project-history": ["project", "history", "--help"],
        "project-revert": ["project", "revert", "--help"],
        "build-plan": ["build", "plan", "--help"],
        "build-execute": ["build", "execute", "--help"],
    }
    return {
        "schema_version": "task026-cli-successor-golden-v1",
        "help": {
            name: fact(invoke(arguments))
            for name, arguments in sorted(help_cases.items())
        },
        "project_completion": {
            shell: fact(project_completion_script(shell))
            for shell in ("bash", "fish", "zsh")
        },
        "application_describe_json": fact(
            invoke(
                [
                    "application",
                    "describe",
                    "--record-set",
                    str(RECORD_SET),
                    "--json",
                ]
            )
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = core.canonical_json(generated()).encode("utf-8") + b"\n"
    if args.check:
        if not FIXTURE.is_file() or FIXTURE.read_bytes() != data:
            raise SystemExit("stale Task 026 CLI successor golden")
        print("Task 026 CLI successor golden: fresh")
        return 0
    FIXTURE.write_bytes(data)
    print("wrote Task 026 CLI successor golden")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
