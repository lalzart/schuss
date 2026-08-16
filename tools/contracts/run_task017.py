#!/usr/bin/env python3
"""Generate deterministic Task 017 headless planning and CLI evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/contracts")]

from packages.schuss_core.control_plane import load_repository_context  # noqa: E402

import validator_core as core  # noqa: E402


RECORD_SET = ROOT / "contracts/record-sets/task017-curated-core-v1.json"
EVIDENCE_ROOT = ROOT / "evidence/task017-completion-v1"
CLI = ROOT / "bin/schuss"

PRESERVED_RESULTS = {
    "evidence/task-011c-v1/completion-manifest.json": "009a626136cde5e123086d66356810c225eb332779b5d985a6d0a7fdd3142205",
    "evidence/task013-completion-v1/validation-summary.json": "6f621400bfd0ffa94703263256130ecf1d5b533b875f391c3dd7c12045217b1d",
    "evidence/task014-completion-v1/validation-summary.json": "58c9102416faff7ef33ed233c10864ecaedb7438ff72b664511e354f60b6d6e9",
    "evidence/task015-completion-v1/validation-summary.json": "231ed9e80132311a7087ed7ba203ec2f7568f3739c82b1264ac3754e35b76989",
    "evidence/task016-completion-v1/semantic-goldens.json": "6cb9ad9a94fd8b4c0bb168cfab75237523a9104f94024eaf399e269212fe8b4b",
    "evidence/task016-completion-v1/validation-summary.json": "c5a5495044019d87c9da9c24f75f262f0953732b02e39674309e1810ee0c4330",
    "contracts/record-sets/task016-complete-gills-direct-v1.json": "4bc6c668d13cc4d63ada766881cd828ef30cbbabd5190f6a2a1e246f99271eaf",
}

COMMANDS = {
    "catalog-search-percussion.json": (["catalog", "search", "percussion"], 0),
    "catalog-inspect-dual-percussion.json": (["catalog", "inspect", "schuss-family-000040@1"], 0),
    "graph-inspect-percussion.json": (["graph", "inspect", "schuss-graph-000003@1"], 0),
    "graph-inspect-effects.json": (["graph", "inspect", "schuss-graph-000004@1"], 0),
    "build-plan-percussion.json": (["build", "plan", "schuss-build-request-000003@1"], 1),
    "build-plan-effects.json": (["build", "plan", "schuss-build-request-000004@1"], 1),
}


def _run(arguments: list[str], cwd: Path) -> bytes:
    completed = subprocess.run(
        [str(CLI), *arguments, "--record-set", str(RECORD_SET), "--json"],
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    expected = next(value for command, value in COMMANDS.values() if command == arguments)
    if completed.returncode != expected:
        raise ValueError(
            f"CLI exit changed for {arguments}: {completed.returncode}: "
            + completed.stderr.decode("utf-8", errors="replace")
        )
    if completed.stderr:
        raise ValueError(f"CLI emitted stderr for {arguments}")
    core.load_json_bytes(completed.stdout, "Task 017 CLI output", require_final_lf=True)
    return completed.stdout


def generated() -> tuple[dict[str, bytes], dict[str, Any]]:
    context = load_repository_context(record_set_path=RECORD_SET)
    if context.task007_summary["status"] != "valid":
        raise ValueError("Task 017 structural closure is invalid")

    files: dict[str, bytes] = {}
    cli_results: dict[str, dict[str, Any]] = {}
    with tempfile.TemporaryDirectory(prefix="schuss-task017-cli-a-") as first_root, tempfile.TemporaryDirectory(prefix="schuss-task017-cli-b-") as second_root:
        for name, (arguments, _) in COMMANDS.items():
            first = _run(arguments, Path(first_root))
            second = _run(arguments, Path(second_root))
            if first != second:
                raise ValueError(f"fresh-process CLI bytes differ for {name}")
            files["cli/" + name] = first
            cli_results[name] = json.loads(first)

    if cli_results["build-plan-percussion.json"]["status"] != "invalid":
        raise ValueError("percussion compound must fail closed at unsupported internals")
    percussion_codes = {
        item["code"] for item in cli_results["build-plan-percussion.json"]["diagnostics"]
    }
    if percussion_codes != {"COMPILER_COMPOUND_INTERNAL_BINDING_UNRESOLVED"}:
        raise ValueError("percussion unsupported diagnostic set changed")
    if cli_results["build-plan-effects.json"]["status"] != "unsupported":
        raise ValueError("effects graph must remain deterministically unsupported")
    effects_codes = {
        item["code"] for item in cli_results["build-plan-effects.json"]["diagnostics"]
    }
    if effects_codes != {"COMPILER_BINDING_UNSUPPORTED"}:
        raise ValueError("effects unsupported diagnostic set changed")

    preserved = []
    for relative, expected in sorted(PRESERVED_RESULTS.items()):
        actual = core.sha256_file(ROOT / relative)
        if actual != expected:
            raise ValueError(f"accepted result bytes changed: {relative}")
        preserved.append({"portable_path": relative, "byte_sha256": actual})
    preservation = {
        "schema_version": "task017-preservation-v1",
        "status": "passed",
        "files": preserved,
    }
    files["preservation.json"] = core.canonical_json(preservation).encode("utf-8") + b"\n"

    evidence_levels = [
        {"level": level, "status": "passed" if level <= 2 else "not-run"}
        for level in range(1, 9)
    ]
    summary = {
        "schema_version": "task017-validation-summary-v1",
        "status": "valid",
        "record_set_reference": context.record_set_reference,
        "selected_family_count": 12,
        "reference_instrument_count": 2,
        "fresh_process_runs_per_cli_command": 2,
        "cli_outputs_identical": True,
        "percussion_plan_status": "invalid",
        "percussion_diagnostic_codes": sorted(percussion_codes),
        "effects_plan_status": "unsupported",
        "effects_diagnostic_codes": sorted(effects_codes),
        "preserved_result_count": len(preserved),
        "evidence_levels": evidence_levels,
        "direct_execution_performed": False,
        "device_actions_performed": False,
        "real_time_validation_performed": False,
        "audible_validation_performed": False,
        "ui_validation_performed": False,
        "hardware_actions_performed": False,
        "publication_performed": False,
    }
    files["validation-summary.json"] = core.canonical_json(summary).encode("utf-8") + b"\n"
    return files, summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    try:
        files, summary = generated()
        stale = [
            relative
            for relative, payload in files.items()
            if not (EVIDENCE_ROOT / relative).is_file()
            or (EVIDENCE_ROOT / relative).read_bytes() != payload
        ]
        if arguments.check and stale:
            raise ValueError("retained Task 017 evidence is stale: " + ", ".join(sorted(stale)))
        if not arguments.check:
            for relative, payload in files.items():
                path = EVIDENCE_ROOT / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
    except (OSError, ValueError) as exc:
        print("Task 017 evidence failed: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
