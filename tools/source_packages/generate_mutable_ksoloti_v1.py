#!/usr/bin/env python3
"""Generate the Task 036 physical closure from Task 033 source authority."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.contracts import validator_core as core  # noqa: E402


PACKAGE_ROOT = ROOT / "packages" / "dsp_sources" / "mutable_ksoloti_v1"
OUTPUT = PACKAGE_ROOT / "SOURCE_PACKAGE.json"
SOURCE_RELEASE_PATH = "contracts/task033/phase2/source-release-05.json"
SOURCE_RELEASE_SCHEMA_PATH = "schemas/source-release-v0.schema.json"
MANIFEST_ALGORITHM = (
    "SHA-256 lines with digest, two spaces, repository-relative path, LF; "
    "LC_ALL=C complete-line sort; SHA-256 of sorted bytes"
)
COMPONENT_GROUPS = {
    "braids-resources": [
        "firmware/mutable_instruments/braids/braids_resources.cpp",
        "firmware/mutable_instruments/braids/resources.h",
    ],
    "clouds-granular-headers": [
        "firmware/mutable_instruments/clouds/dsp/audio_buffer.h",
        "firmware/mutable_instruments/clouds/dsp/frame.h",
        "firmware/mutable_instruments/clouds/dsp/fx/fx_engine.h",
        "firmware/mutable_instruments/clouds/dsp/fx/reverb.h",
        "firmware/mutable_instruments/clouds/dsp/grain.h",
        "firmware/mutable_instruments/clouds/dsp/mu_law.h",
        "firmware/mutable_instruments/clouds/dsp/parameters.h",
    ],
    "clouds-resources": [
        "firmware/mutable_instruments/clouds/clouds_resources.cpp",
        "firmware/mutable_instruments/clouds/resources.h",
    ],
    "stmlib-core-headers": [
        "firmware/mutable_instruments/stmlib/dsp/cosine_oscillator.h",
        "firmware/mutable_instruments/stmlib/dsp/dsp.h",
        "firmware/mutable_instruments/stmlib/dsp/filter.h",
        "firmware/mutable_instruments/stmlib/dsp/rsqrt.h",
        "firmware/mutable_instruments/stmlib/dsp/units.h",
        "firmware/mutable_instruments/stmlib/stmlib.h",
        "firmware/mutable_instruments/stmlib/utils/dsp.h",
    ],
    "stmlib-random-source": [
        "firmware/mutable_instruments/stmlib/utils/random.cpp",
        "firmware/mutable_instruments/stmlib/utils/random.h",
    ],
    "stmlib-units-source": [
        "firmware/mutable_instruments/stmlib/dsp/units.cpp",
        "firmware/mutable_instruments/stmlib/dsp/units.h",
    ],
}


def _canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_release() -> dict[str, Any]:
    record = core.load_json(ROOT / SOURCE_RELEASE_PATH)
    schema = core.load_json(ROOT / SOURCE_RELEASE_SCHEMA_PATH)
    errors = core.schema_errors(record, schema, schema)
    if errors:
        raise ValueError("source-release authority is invalid: " + "; ".join(errors))
    if core.record_content_hash(record, schema) != record["content_hash"]:
        raise ValueError("source-release authority content hash drifted")
    if (
        record["source_release_id"] != "schuss-source-release-000005"
        or record["revision"] != 1
        or record["support_claim"] != "source-identity-and-provenance-only"
    ):
        raise ValueError("unexpected Task 033 source-release authority")
    return record


def generate() -> dict[str, Any]:
    source_release = _source_release()
    paths = sorted({path for paths in COMPONENT_GROUPS.values() for path in paths})
    files = []
    for path in paths:
        physical = PACKAGE_ROOT / "upstream" / path
        if not physical.is_file() or physical.is_symlink():
            raise ValueError(f"physical closure file is absent or not regular: {path}")
        files.append({"path": path, "sha256": _sha256(physical)})
    manifest_lines = [
        f"{entry['sha256']}  {entry['path']}\n".encode("utf-8")
        for entry in files
    ]
    manifest_sha256 = hashlib.sha256(b"".join(sorted(manifest_lines))).hexdigest()
    if manifest_sha256 != "0903f25038f0116422a8512b15f1c3531e7b22371da8ad393b130a16d821508f":
        raise ValueError("physical closure manifest does not match the Task 036 baseline")
    return {
        "authority": {
            "source_release": {
                "content_hash": source_release["content_hash"],
                "path": SOURCE_RELEASE_PATH,
                "revision": source_release["revision"],
                "source_release_id": source_release["source_release_id"],
            },
            "source_release_schema_path": SOURCE_RELEASE_SCHEMA_PATH,
        },
        "claims": {
            "does_not_provide": [
                "audible-evidence",
                "catalog-membership",
                "collection-membership",
                "device-evidence",
                "distribution-approval",
                "graph-identity",
                "implementation-identity",
                "license-authority",
                "provenance-authority",
                "provider-identity",
                "real-time-evidence",
                "runtime-support",
                "source-release-identity",
            ],
            "provides": ["physical-build-closure"],
        },
        "closure": {
            "files": files,
            "immutable_root": "upstream",
            "manifest_algorithm": MANIFEST_ALGORITHM,
            "manifest_sha256": manifest_sha256,
            "retained_notice_path": "THIRD_PARTY_NOTICES.md",
        },
        "component_groups": [
            {"name": name, "paths": paths}
            for name, paths in sorted(COMPONENT_GROUPS.items())
        ],
        "package_id": "mutable-ksoloti-v1",
        "package_revision": "1",
        "schema_version": "physical-source-closure-manifest-v1",
        "transitive_support": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = _canonical_bytes(generate())
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_bytes() != expected:
            print("source package manifest: stale")
            return 1
        print("source package manifest: fresh")
        return 0
    OUTPUT.write_bytes(expected)
    print("source package manifest: generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
