#!/usr/bin/env python3
"""Fail-closed validator for the Task 036 Instrument Lab handoff."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.source_packages.validate_source_package import validate_package  # noqa: E402


SCHEMA_VERSION = "task036-instrument-lab-source-handoff-v1"
SHA256 = set("0123456789abcdef")
NEGATIVE_CLAIMS = {
    "device_promoted",
    "distribution_promoted",
    "graph_promoted",
    "listening_promoted",
    "provider_promoted",
    "publication_promoted",
    "real_time_promoted",
    "runtime_promoted",
}
TOP_FIELDS = {
    "negative_claims",
    "results",
    "schema_version",
    "source_package",
    "status",
    "task",
    "tide_pit",
    "validation",
}


def _canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key}")
        result[key] = value
    return result


def _portable_path(value: object) -> bool:
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    path = PurePosixPath(value)
    return (
        not path.is_absolute()
        and path.as_posix() == value
        and "." not in path.parts
        and ".." not in path.parts
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _check_file_ref(value: object, label: str, errors: list[str]) -> None:
    if not isinstance(value, dict) or set(value) != {"path", "sha256"}:
        errors.append(f"INVALID_FILE_REF: {label}")
        return
    path = value.get("path")
    digest = value.get("sha256")
    if not _portable_path(path):
        errors.append(f"NON_PORTABLE_PATH: {label}")
        return
    if not isinstance(digest, str) or len(digest) != 64 or set(digest) - SHA256:
        errors.append(f"INVALID_SHA256: {label}")
        return
    target = (ROOT / path).resolve()
    try:
        target.relative_to(ROOT.resolve())
    except ValueError:
        errors.append(f"ESCAPING_PATH: {label}")
        return
    if not target.is_file() or target.is_symlink():
        errors.append(f"MISSING_FILE: {label}")
    elif _sha256(target) != digest:
        errors.append(f"FILE_HASH_DRIFT: {label}")


def _closed_object(
    value: object, fields: set[str], label: str, errors: list[str]
) -> dict[str, Any] | None:
    if not isinstance(value, dict) or set(value) != fields:
        errors.append(f"INVALID_FIELDS: {label}")
        return None
    return value


def _walk_no_absolute_or_mutable_latest(value: object, errors: list[str]) -> None:
    if isinstance(value, dict):
        for child in value.values():
            _walk_no_absolute_or_mutable_latest(child, errors)
    elif isinstance(value, list):
        for child in value:
            _walk_no_absolute_or_mutable_latest(child, errors)
    elif isinstance(value, str):
        if value.startswith(("/", "~", "file://")):
            errors.append("ABSOLUTE_VALUE: handoff contains a machine-local value")
        if value.lower() == "latest" or "mutable_latest" in value.lower():
            errors.append("MUTABLE_LATEST: handoff contains mutable latest identity")


def validate_handoff(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8", errors="strict")
        document = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return ["MALFORMED_HANDOFF: handoff is not readable canonical UTF-8 JSON"]
    if not isinstance(document, dict):
        return ["INVALID_HANDOFF: handoff must be an object"]
    if raw != _canonical_bytes(document):
        errors.append("NONCANONICAL_HANDOFF: handoff must be sorted UTF-8/LF JSON")
    if set(document) != TOP_FIELDS:
        errors.append("INVALID_FIELDS: handoff top-level fields")
        return errors
    _walk_no_absolute_or_mutable_latest(document, errors)
    if document.get("schema_version") != SCHEMA_VERSION:
        errors.append("WRONG_SCHEMA: unsupported handoff schema")
    if document.get("status") != "complete":
        errors.append("INCOMPLETE: Task 036 is not complete")

    claims = _closed_object(
        document.get("negative_claims"), NEGATIVE_CLAIMS, "negative_claims", errors
    )
    if claims is not None and any(value is not False for value in claims.values()):
        errors.append("PROMOTED_CLAIM: all promotion claims must remain false")

    task = _closed_object(document.get("task"), {"contract", "proposal"}, "task", errors)
    if task:
        _check_file_ref(task["contract"], "task.contract", errors)
        _check_file_ref(task["proposal"], "task.proposal", errors)
        if task["contract"].get("sha256") != "4bdd4b60fff8cc28c7f21a17763a949e2e123cafea84e2aad30252338be501f0":
            errors.append("TASK_HASH_DRIFT: Task 036 contract hash changed")
        if task["proposal"].get("sha256") != "be4636f2550481bd45cb982fe47c01ee8fbe0de74621f22e9d27cffca680cf7a":
            errors.append("PROPOSAL_HASH_DRIFT: Task 036 proposal hash changed")

    results = _closed_object(
        document.get("results"), {"gaps", "results"}, "results", errors
    )
    if results:
        _check_file_ref(results["gaps"], "results.gaps", errors)
        _check_file_ref(results["results"], "results.results", errors)

    source_fields = {
        "authority_source_release",
        "closure_manifest_sha256",
        "cmake_include",
        "component_groups",
        "component_resolution_function",
        "generator",
        "interface_target",
        "manifest",
        "package_id",
        "package_path",
        "package_revision",
        "validator",
        "validator_command",
        "validator_tests",
    }
    source = _closed_object(
        document.get("source_package"), source_fields, "source_package", errors
    )
    if source:
        for name in ("cmake_include", "generator", "manifest", "validator", "validator_tests"):
            _check_file_ref(source[name], f"source_package.{name}", errors)
        expected_authority = {
            "content_hash": "sha256:51750a00f07f98c783cfc1972580c9399ac64690eaf3d40ad6e1d736698c972c",
            "path": "contracts/task033/phase2/source-release-05.json",
            "revision": 1,
            "source_release_id": "schuss-source-release-000005",
        }
        expected_groups = [
            "braids-resources",
            "clouds-granular-headers",
            "clouds-resources",
            "stmlib-core-headers",
            "stmlib-random-source",
            "stmlib-units-source",
        ]
        expected_command = [
            "python3",
            "tools/source_packages/validate_source_package.py",
            "packages/dsp_sources/mutable_ksoloti_v1",
        ]
        if source.get("authority_source_release") != expected_authority:
            errors.append("AUTHORITY_DRIFT: source-release reference changed")
        if source.get("component_groups") != expected_groups:
            errors.append("COMPONENT_GROUP_DRIFT: component groups changed")
        if source.get("validator_command") != expected_command:
            errors.append("VALIDATOR_COMMAND_DRIFT: package validator command changed")
        expected_scalars = {
            "closure_manifest_sha256": "0903f25038f0116422a8512b15f1c3531e7b22371da8ad393b130a16d821508f",
            "component_resolution_function": "mutable_ksoloti_v1_resolve_components",
            "interface_target": "MutableKsolotiV1::Headers",
            "package_id": "mutable-ksoloti-v1",
            "package_path": "packages/dsp_sources/mutable_ksoloti_v1",
            "package_revision": "1",
        }
        for key, expected in expected_scalars.items():
            if source.get(key) != expected:
                errors.append(f"SOURCE_PACKAGE_DRIFT: {key}")
        package_root = ROOT / "packages/dsp_sources/mutable_ksoloti_v1"
        _, package_errors = validate_package(
            package_root,
            expected_package_id="mutable-ksoloti-v1",
            expected_package_revision="1",
            expected_source_release_id="schuss-source-release-000005",
            expected_source_release_revision=1,
            expected_source_release_content_hash=expected_authority["content_hash"],
            expected_closure_manifest_sha256=expected_scalars["closure_manifest_sha256"],
            requested_components=expected_groups,
        )
        errors.extend(f"SOURCE_PACKAGE_INVALID: {error.line()}" for error in package_errors)

    tide_fields = {
        "compile_policy",
        "compiled_target",
        "consumer_path",
        "evidence",
        "reference_golden",
        "source_equivalence",
        "source_lock",
    }
    tide = _closed_object(document.get("tide_pit"), tide_fields, "tide_pit", errors)
    if tide:
        for name in ("compile_policy", "source_equivalence", "source_lock"):
            _check_file_ref(tide[name], f"tide_pit.{name}", errors)
        if tide.get("compiled_target") != "tide_pit_mutable":
            errors.append("TIDE_TARGET_DRIFT: compiled target changed")
        if tide.get("consumer_path") != "research/prototypes/tide-pit-gills":
            errors.append("TIDE_PATH_DRIFT: consumer path changed")
        evidence = _closed_object(
            tide.get("evidence"),
            {"control_map", "experiment", "source_lock_validator", "validation_plan"},
            "tide_pit.evidence",
            errors,
        )
        if evidence:
            for name, value in evidence.items():
                _check_file_ref(value, f"tide_pit.evidence.{name}", errors)
        golden = _closed_object(
            tide.get("reference_golden"),
            {"expected_bytes", "expected_peak_q27", "expected_rms_q27", "expected_sha256", "test"},
            "tide_pit.reference_golden",
            errors,
        )
        if golden:
            _check_file_ref(golden["test"], "tide_pit.reference_golden.test", errors)
            expected_golden = {
                "expected_bytes": 1536000,
                "expected_peak_q27": 39182832,
                "expected_rms_q27": "14011444.589680206",
                "expected_sha256": "39d8c2a67a1b9511b4a063914b01ab816635996a47530e6c09baa8accf45ad2b",
            }
            for key, expected in expected_golden.items():
                if golden.get(key) != expected:
                    errors.append(f"GOLDEN_DRIFT: {key}")

    validation = _closed_object(
        document.get("validation"),
        {"handoff_validator", "handoff_validator_command", "handoff_validator_tests"},
        "validation",
        errors,
    )
    if validation:
        _check_file_ref(validation["handoff_validator"], "validation.handoff_validator", errors)
        _check_file_ref(validation["handoff_validator_tests"], "validation.handoff_validator_tests", errors)
        if validation.get("handoff_validator_command") != [
            "python3",
            "tools/source_packages/validate_task036_handoff.py",
            "docs/tasks/036-INSTRUMENT-LAB-HANDOFF.json",
        ]:
            errors.append("HANDOFF_VALIDATOR_COMMAND_DRIFT: command changed")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "handoff",
        nargs="?",
        type=Path,
        default=ROOT / "docs/tasks/036-INSTRUMENT-LAB-HANDOFF.json",
    )
    args = parser.parse_args()
    errors = validate_handoff(args.handoff)
    if errors:
        for error in errors:
            print(error)
        return 1
    print("Task 036 handoff: valid and complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
