#!/usr/bin/env python3
"""Verify Wanderbody's frozen proposal and authenticated source boundaries."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
PROPOSAL_HASH = "2441ae557cd4a692cd3aa42b87b80bf42e401d35250f685912d1f288ba3d6682"
JUCE_MANIFEST_HASH = "db7daa7f6937fb8774b11784efa3977b5f8f91bb718a63cf262166c8d4115ac5"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    proposal = REPO_ROOT / "research" / "proposals" / "wanderbody-standalone-r01.md"
    if digest(proposal) != PROPOSAL_HASH:
        raise SystemExit("approved Wanderbody proposal drift")
    contract = json.loads((ROOT / "contract-r01" / "implementation-contract.json").read_text())
    if contract["status"] != "ready" or contract["proposal"]["sha256"] != PROPOSAL_HASH:
        raise SystemExit("ready implementation contract drift")
    equivalence = json.loads((ROOT / "contract-r01" / "source-equivalence.json").read_text())
    if equivalence != {
        "not_applicable_rationale": "New-design work has no normative implementation source.",
        "schema_version": "sonic-research-lab-source-equivalence-v1",
        "status": "not-applicable",
        "work_type": "new-design",
    }:
        raise SystemExit("new-design source-equivalence boundary drift")
    manifest = REPO_ROOT / "research/prototype_support/instrument_lab/juce-8.0.15-source-tree.json"
    if digest(manifest) != JUCE_MANIFEST_HASH:
        raise SystemExit("authenticated JUCE 8.0.15 manifest drift")
    dependencies = json.loads((ROOT / "source-dependencies.json").read_text())
    reference = dependencies["authenticated_extracted_sources"][0]["manifest"]
    if reference != {
        "path": "research/prototype_support/instrument_lab/juce-8.0.15-source-tree.json",
        "sha256": JUCE_MANIFEST_HASH,
    }:
        raise SystemExit("Wanderbody JUCE dependency reference drift")
    print("Wanderbody proposal and source boundaries verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
