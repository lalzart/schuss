#!/usr/bin/env python3
"""Validate the durable Task 029 contract and evidence-backed plan."""

from __future__ import annotations

import re
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/contracts"))

import validator_core as core  # noqa: E402


CONTRACT = ROOT / "docs/GILLS_MACHINE_IMPLEMENTATION_CONTRACT.md"
PLAN = ROOT / "docs/GILLS_MACHINE_LAYER_PLAN.md"

REQUIRED_CONTRACT_HEADINGS = (
    "## Goal and why it exists",
    "## Execution baseline and isolation gate",
    "## In scope",
    "## Out of scope",
    "## Inputs",
    "## Deliverables",
    "## Required data and operation behavior",
    "## Read-only Viewer behavior",
    "## Acceptance tests",
    "## Decisions this task may make",
    "## Decisions this task must not make",
    "## Evidence levels and completion rule",
)

REQUIRED_ASSERTIONS = (
    "schuss-record-set-000022@1",
    "schuss-record-set-000021@1",
    "projects/palimpsest-gills/",
    "projects/tide-pit-gills/",
    "assets/gills/gills-panel-v06.svg",
    "machine.inspect",
    "inspection-only",
    "Machine Builder",
    "current 20-object palette",
    "Pamulist",
    "Palimpsest",
    "Tide Pit",
)


def _relative_links(path: Path, text: str) -> list[str]:
    errors = []
    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
        if target.startswith(("http://", "https://", "#")):
            continue
        relative = target.split("#", 1)[0]
        if relative and not (path.parent / relative).resolve().is_file():
            errors.append(target)
    return errors


def main() -> int:
    contract = CONTRACT.read_text(encoding="utf-8")
    plan = PLAN.read_text(encoding="utf-8")
    missing_headings = [item for item in REQUIRED_CONTRACT_HEADINGS if contract.count(item) != 1]
    missing_assertions = [item for item in REQUIRED_ASSERTIONS if item not in contract]
    errors = []
    if "Status: proposed and inactive" in contract or "evidence-backed proposal" in plan:
        errors.append("stale inactive status remains")
    if "/Users/" in contract + plan or "/tmp/" in contract + plan:
        errors.append("durable documentation contains an absolute local path")
    for path, text in ((CONTRACT, contract), (PLAN, plan)):
        links = _relative_links(path, text)
        if links:
            errors.append(f"{path.name} has unresolved relative links: {links}")
        if any(line.endswith((" ", "\t")) for line in text.splitlines()):
            errors.append(f"{path.name} has trailing whitespace")
    if missing_headings or missing_assertions or errors:
        raise ValueError(
            core.canonical_json(
                {
                    "missing_headings": missing_headings,
                    "missing_assertions": missing_assertions,
                    "errors": errors,
                }
            )
        )
    print(
        core.canonical_json(
            {
                "schema_version": "task029-contract-validation-v1",
                "status": "passed",
                "required_heading_count": len(REQUIRED_CONTRACT_HEADINGS),
                "required_assertion_count": len(REQUIRED_ASSERTIONS),
                "relative_links": "resolved",
                "portable_paths": "passed",
                "implementation_state": "implemented-local-not-committed",
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
