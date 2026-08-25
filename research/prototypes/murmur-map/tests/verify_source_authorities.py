#!/usr/bin/env python3
"""Verify Murmur Map's exact shared source and controller authorities."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[4]
PROTOTYPE = REPO / "research/prototypes/murmur-map"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    handoff = json.loads((PROTOTYPE / "source-dependencies.json").read_text(encoding="utf-8"))
    references: list[dict[str, str]] = [handoff["adapter"]["manifest"]]
    references.extend(item["manifest"] for item in handoff["physical_packages"])
    references.extend(item["manifest"] for item in handoff["authenticated_extracted_sources"])
    for reference in references:
        path = REPO / reference["path"]
        if not path.is_file() or digest(path) != reference["sha256"]:
            raise SystemExit(f"authority hash mismatch: {reference['path']}")

    for item in [*handoff["physical_packages"], *handoff["authenticated_extracted_sources"]]:
        reference = item["source_release"]
        record = json.loads((REPO / reference["path"]).read_text(encoding="utf-8"))
        expected = {
            "source_release_id": reference["source_release_id"],
            "revision": reference["revision"],
            "content_hash": reference["content_hash"],
        }
        actual = {key: record.get(key) for key in expected}
        if actual != expected:
            raise SystemExit(f"source-release drift: {reference['path']}")

    controller = REPO / "research/prototype_support/controllers/novation-launch-control-3-regular-v1.json"
    if digest(controller) != "d69475e54e1bc0a3f441f0bcb5863084c73dbeff5d995670b17c8e894654510b":
        raise SystemExit("regular Launch Control 3 topology drift")

    proposal = REPO / "research/proposals/modular-generative-juce-instrument-study.md"
    if digest(proposal) != "65180864c42996a3e7a68de0b7356522329b25043e3ef5721e7e49fd3d49926f":
        raise SystemExit("approved Murmur Map proposal drift")

    print("Murmur Map source and controller authorities verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
