#!/usr/bin/env python3
"""Generate the deterministic Task 036 completion handoff."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs" / "tasks" / "036-INSTRUMENT-LAB-HANDOFF.json"

SOURCE_RELEASE = {
    "content_hash": "sha256:51750a00f07f98c783cfc1972580c9399ac64690eaf3d40ad6e1d736698c972c",
    "path": "contracts/task033/phase2/source-release-05.json",
    "revision": 1,
    "source_release_id": "schuss-source-release-000005",
}
COMPONENT_GROUPS = [
    "braids-resources",
    "clouds-granular-headers",
    "clouds-resources",
    "stmlib-core-headers",
    "stmlib-random-source",
    "stmlib-units-source",
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _file_ref(path: str) -> dict[str, str]:
    return {"path": path, "sha256": _sha256(ROOT / path)}


def _canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def generate() -> dict[str, object]:
    package_manifest_path = (
        "packages/dsp_sources/mutable_ksoloti_v1/SOURCE_PACKAGE.json"
    )
    package_manifest = json.loads((ROOT / package_manifest_path).read_text("utf-8"))
    authority = package_manifest.get("authority", {}).get("source_release")
    if authority != SOURCE_RELEASE:
        raise ValueError("physical package no longer references the expected authority")
    if package_manifest.get("closure", {}).get("manifest_sha256") != (
        "0903f25038f0116422a8512b15f1c3531e7b22371da8ad393b130a16d821508f"
    ):
        raise ValueError("physical closure manifest drifted")
    if [group.get("name") for group in package_manifest.get("component_groups", [])] != COMPONENT_GROUPS:
        raise ValueError("physical package component groups drifted")

    return {
        "negative_claims": {
            "device_promoted": False,
            "distribution_promoted": False,
            "graph_promoted": False,
            "listening_promoted": False,
            "provider_promoted": False,
            "publication_promoted": False,
            "real_time_promoted": False,
            "runtime_promoted": False,
        },
        "results": {
            "gaps": _file_ref("docs/tasks/036-GAPS.md"),
            "results": _file_ref("docs/tasks/036-RESULTS.md"),
        },
        "schema_version": "task036-instrument-lab-source-handoff-v1",
        "source_package": {
            "authority_source_release": SOURCE_RELEASE,
            "closure_manifest_sha256": (
                "0903f25038f0116422a8512b15f1c3531e7b22371da8ad393b130a16d821508f"
            ),
            "cmake_include": _file_ref(
                "packages/dsp_sources/mutable_ksoloti_v1/cmake/MutableKsolotiSource.cmake"
            ),
            "component_groups": COMPONENT_GROUPS,
            "component_resolution_function": "mutable_ksoloti_v1_resolve_components",
            "generator": _file_ref(
                "tools/source_packages/generate_mutable_ksoloti_v1.py"
            ),
            "interface_target": "MutableKsolotiV1::Headers",
            "manifest": _file_ref(package_manifest_path),
            "package_id": "mutable-ksoloti-v1",
            "package_path": "packages/dsp_sources/mutable_ksoloti_v1",
            "package_revision": "1",
            "validator": _file_ref(
                "tools/source_packages/validate_source_package.py"
            ),
            "validator_command": [
                "python3",
                "tools/source_packages/validate_source_package.py",
                "packages/dsp_sources/mutable_ksoloti_v1",
            ],
            "validator_tests": _file_ref(
                "tools/source_packages/tests/test_validate_source_package.py"
            ),
        },
        "status": "complete",
        "task": {
            "contract": _file_ref(
                "docs/tasks/036-shared-authenticated-mutable-dsp-source-package-pilot.md"
            ),
            "proposal": _file_ref(
                "research/proposals/shared-authenticated-mutable-dsp-source-package-pilot.md"
            ),
        },
        "tide_pit": {
            "compile_policy": _file_ref(
                "research/prototypes/tide-pit-gills/CMakeLists.txt"
            ),
            "compiled_target": "tide_pit_mutable",
            "consumer_path": "research/prototypes/tide-pit-gills",
            "evidence": {
                "control_map": _file_ref(
                    "research/prototypes/tide-pit-gills/control-map.json"
                ),
                "experiment": _file_ref(
                    "research/prototypes/tide-pit-gills/experiment.json"
                ),
                "source_lock_validator": _file_ref(
                    "research/prototypes/tide-pit-gills/tests/validate_source_lock.py"
                ),
                "validation_plan": _file_ref(
                    "research/prototypes/tide-pit-gills/validation-plan.json"
                ),
            },
            "reference_golden": {
                "expected_bytes": 1536000,
                "expected_peak_q27": 39182832,
                "expected_rms_q27": "14011444.589680206",
                "expected_sha256": "39d8c2a67a1b9511b4a063914b01ab816635996a47530e6c09baa8accf45ad2b",
                "test": _file_ref(
                    "research/prototypes/tide-pit-gills/tests/reference_golden_tests.cpp"
                ),
            },
            "source_equivalence": _file_ref(
                "research/prototypes/tide-pit-gills/source-equivalence.json"
            ),
            "source_lock": _file_ref(
                "research/prototypes/tide-pit-gills/third_party/SOURCE_LOCK.json"
            ),
        },
        "validation": {
            "handoff_validator": _file_ref(
                "tools/source_packages/validate_task036_handoff.py"
            ),
            "handoff_validator_command": [
                "python3",
                "tools/source_packages/validate_task036_handoff.py",
                "docs/tasks/036-INSTRUMENT-LAB-HANDOFF.json",
            ],
            "handoff_validator_tests": _file_ref(
                "tools/source_packages/tests/test_validate_task036_handoff.py"
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = _canonical_bytes(generate())
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_bytes() != expected:
            print("Task 036 handoff: stale")
            return 1
        print("Task 036 handoff: fresh")
        return 0
    OUTPUT.write_bytes(expected)
    print("Task 036 handoff: generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
