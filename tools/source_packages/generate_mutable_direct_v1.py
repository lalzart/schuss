#!/usr/bin/env python3
"""Generate the two Task 038 direct-upstream Mutable physical closures."""

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


SCHEMA_PATH = "schemas/source-release-v0.schema.json"
MANIFEST_ALGORITHM = (
    "SHA-256 lines with digest, two spaces, repository-relative path, LF; "
    "LC_ALL=C complete-line sort; SHA-256 of sorted bytes"
)
COMMON_EXCLUSIONS = [
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
]
PACKAGES = {
    "mutable-eurorack-braids-v1": {
        "root": "packages/dsp_sources/mutable_eurorack_braids_v1",
        "source_release": "contracts/task038/source-release-01.json",
        "source_release_id": "schuss-source-release-000008",
        "expected_manifest": "6079cb67522374c4f6b3cac31da3810e4fb62b0112d86b6c4e2bccff4895d4df",
        "components": {
            "braids-core-sources": [
                "braids/analog_oscillator.cc",
                "braids/digital_oscillator.cc",
                "braids/macro_oscillator.cc",
            ],
            "braids-headers": [
                "braids/analog_oscillator.h",
                "braids/digital_oscillator.h",
                "braids/excitation.h",
                "braids/macro_oscillator.h",
                "braids/parameter_interpolation.h",
                "braids/resources.h",
                "braids/settings.h",
                "braids/svf.h",
            ],
            "braids-resources-source": ["braids/resources.cc"],
        },
        "transitive_support": [],
    },
    "mutable-stmlib-v1": {
        "root": "packages/dsp_sources/mutable_stmlib_v1",
        "source_release": "contracts/task038/source-release-02.json",
        "source_release_id": "schuss-source-release-000009",
        "expected_manifest": "ee35268d95d661a9be2ff5f3e8ff0c6d89f06c4b0337ceaacbb7ec8ba51426bb",
        "components": {
            "stmlib-headers": [
                "stmlib/stmlib.h",
                "stmlib/utils/dsp.h",
                "stmlib/utils/random.h",
            ],
            "stmlib-random-source": ["stmlib/utils/random.cc"],
        },
        "transitive_support": ["stmlib/LICENSE"],
    },
}


def _canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _source_release(relative: str, expected_id: str) -> dict[str, Any]:
    record = core.load_json(ROOT / relative)
    schema = core.load_json(ROOT / SCHEMA_PATH)
    errors = core.schema_errors(record, schema, schema)
    if errors or core.record_content_hash(record, schema) != record.get("content_hash"):
        raise ValueError(f"source-release authority is invalid: {relative}")
    if (
        record.get("source_release_id") != expected_id
        or record.get("revision") != 1
        or record.get("support_claim") != "source-identity-and-provenance-only"
    ):
        raise ValueError(f"unexpected source-release authority: {relative}")
    return record


def generate_one(package_id: str, spec: dict[str, Any]) -> dict[str, Any]:
    package_root = ROOT / spec["root"]
    release = _source_release(spec["source_release"], spec["source_release_id"])
    paths = sorted(
        set(spec["transitive_support"])
        | {path for values in spec["components"].values() for path in values}
    )
    files = []
    lines = []
    for path in paths:
        physical = package_root / "upstream" / path
        if not physical.is_file() or physical.is_symlink():
            raise ValueError(f"physical closure file is absent or not regular: {path}")
        digest = core.sha256_file(physical)
        files.append({"path": path, "sha256": digest})
        lines.append(f"{digest}  {path}\n".encode("utf-8"))
    manifest = hashlib.sha256(b"".join(sorted(lines))).hexdigest()
    if manifest != spec["expected_manifest"]:
        raise ValueError(f"{package_id} physical closure drifted")
    return {
        "authority": {
            "source_release": {
                "content_hash": release["content_hash"],
                "path": spec["source_release"],
                "revision": release["revision"],
                "source_release_id": release["source_release_id"],
            },
            "source_release_schema_path": SCHEMA_PATH,
        },
        "claims": {
            "does_not_provide": COMMON_EXCLUSIONS,
            "provides": ["physical-build-closure"],
        },
        "closure": {
            "files": files,
            "immutable_root": "upstream",
            "manifest_algorithm": MANIFEST_ALGORITHM,
            "manifest_sha256": manifest,
            "retained_notice_path": "THIRD_PARTY_NOTICES.md",
        },
        "component_groups": [
            {"name": name, "paths": paths}
            for name, paths in sorted(spec["components"].items())
        ],
        "package_id": package_id,
        "package_revision": "1",
        "schema_version": "physical-source-closure-manifest-v1",
        "transitive_support": spec["transitive_support"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    stale = []
    for package_id, spec in PACKAGES.items():
        output = ROOT / spec["root"] / "SOURCE_PACKAGE.json"
        expected = _canonical_bytes(generate_one(package_id, spec))
        if args.check:
            if not output.is_file() or output.read_bytes() != expected:
                stale.append(output.relative_to(ROOT).as_posix())
        else:
            output.write_bytes(expected)
    if stale:
        raise SystemExit("stale direct Mutable source packages: " + ", ".join(stale))
    print("direct Mutable physical source packages: " + ("fresh" if args.check else "generated"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
