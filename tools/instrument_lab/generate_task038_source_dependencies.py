#!/usr/bin/env python3
"""Generate the drum machine's compact reusable-source dependency handoff."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = Path("research/prototypes/generative-drum-machine/contract/source-dependencies.json")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_ref(path: str) -> dict[str, str]:
    return {"path": path, "sha256": sha256(ROOT / path)}


def source_ref(path: str) -> dict[str, object]:
    document = json.loads((ROOT / path).read_text(encoding="utf-8"))
    return {
        "content_hash": document["content_hash"],
        "path": path,
        "revision": document["revision"],
        "source_release_id": document["source_release_id"],
    }


def generated() -> bytes:
    braids_manifest = "packages/dsp_sources/mutable_eurorack_braids_v1/SOURCE_PACKAGE.json"
    stmlib_manifest = "packages/dsp_sources/mutable_stmlib_v1/SOURCE_PACKAGE.json"
    adapter_manifest = "packages/dsp_adapters/mutable_braids_v1/ADAPTER.json"
    juce_tree_manifest = "research/prototype_support/instrument_lab/juce-8.0.15-source-tree.json"
    document = {
        "adapter": {
            "interface": "SchussMutableBraidsV1::Core",
            "manifest": file_ref(adapter_manifest),
        },
        "authenticated_extracted_sources": [
            {
                "manifest": file_ref(juce_tree_manifest),
                "prerequisite": "operator-supplied exact extracted source tree",
                "source_release": source_ref("contracts/task033/phase2/source-release-07.json"),
            }
        ],
        "claims": {
            "catalog_membership": False,
            "graph_identity": False,
            "implementation_identity": False,
            "provider_identity": False,
            "runtime_support": False,
        },
        "consumer_id": "generative-drum-machine",
        "physical_packages": [
            {
                "manifest": file_ref(braids_manifest),
                "package_id": "mutable-eurorack-braids-v1",
                "package_revision": "1",
                "required_components": [
                    "braids-core-sources",
                    "braids-headers",
                    "braids-resources-source",
                ],
                "source_release": source_ref("contracts/task038/source-release-01.json"),
            },
            {
                "manifest": file_ref(stmlib_manifest),
                "package_id": "mutable-stmlib-v1",
                "package_revision": "1",
                "required_components": ["stmlib-headers", "stmlib-random-source"],
                "source_release": source_ref("contracts/task038/source-release-02.json"),
            },
        ],
        "schema_version": "instrument-lab-source-dependencies-v1",
    }
    return (json.dumps(document, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = generated()
    destination = ROOT / OUTPUT
    if args.check:
        if not destination.is_file() or destination.read_bytes() != expected:
            raise SystemExit(f"stale source dependency handoff: {OUTPUT}")
        print("drum-machine source dependency handoff: fresh")
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(expected)
        print("drum-machine source dependency handoff: generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
