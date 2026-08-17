#!/usr/bin/env python3
"""Generate deterministic Task 030 CLI successor golden hashes."""

from __future__ import annotations

import argparse
import hashlib
import io
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/contracts")]

from packages.schuss_core.cli import run as run_cli  # noqa: E402
from packages.schuss_core.control_plane import load_repository_context  # noqa: E402
from packages.schuss_core.product_cli import completion_script  # noqa: E402

import validator_core as core  # noqa: E402


FIXTURE = ROOT / "tools/contracts/tests/fixtures/task030-cli-v3-golden-hashes.json"
RECORD_SET = ROOT / "contracts/record-sets/task030-complete-mutable-catalog-v1.json"
TAG = "mutable-instruments-derived"


def fact(data: bytes) -> dict[str, object]:
    return {
        "byte_length": len(data),
        "byte_sha256": hashlib.sha256(data).hexdigest(),
    }


def generated() -> dict[str, object]:
    context = load_repository_context(record_set_path=RECORD_SET)

    def invoke(arguments: list[str]) -> bytes:
        stdout = io.BytesIO()
        stderr = io.StringIO()
        code = run_cli(
            arguments,
            io.BytesIO(),
            stdout,
            stderr,
            lambda **kwargs: context,
        )
        if code != 0 or stderr.getvalue():
            raise ValueError(
                f"CLI golden command failed: {arguments}: {code}: {stderr.getvalue()}"
            )
        return stdout.getvalue()

    help_cases = {
        "root": ["--help"],
        "catalog": ["catalog", "--help"],
        "catalog-search": ["catalog", "search", "--help"],
        "catalog-objects": ["catalog", "objects", "--help"],
        "catalog-inspect": ["catalog", "inspect", "--help"],
    }
    command_cases = {
        "catalog-search-mutable": [
            "catalog",
            "search",
            "--provenance",
            TAG,
        ],
        "catalog-objects-mutable": [
            "catalog",
            "objects",
            "--provenance",
            TAG,
        ],
        "catalog-objects-macro": [
            "catalog",
            "objects",
            "macro",
            "--provenance",
            TAG,
        ],
        "catalog-inspect-macro": [
            "catalog",
            "inspect",
            "schuss-family-000062@1",
        ],
    }
    return {
        "schema_version": "task030-cli-v3-golden-v1",
        "help": {
            name: fact(invoke(arguments))
            for name, arguments in sorted(help_cases.items())
        },
        "completion": {
            shell: fact(completion_script(shell))
            for shell in ("bash", "fish", "zsh")
        },
        "human": {
            name: fact(invoke(arguments))
            for name, arguments in sorted(command_cases.items())
        },
        "json": {
            name: fact(invoke([*arguments, "--json"]))
            for name, arguments in sorted(command_cases.items())
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
            raise SystemExit("stale Task 030 CLI v3 successor golden")
        print("Task 030 CLI v3 successor golden: fresh")
        return 0
    FIXTURE.write_bytes(data)
    print("wrote Task 030 CLI v3 successor golden")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
