#!/usr/bin/env python3
"""Manifest-driven, deduplicated Schuss validation runner."""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = Path(__file__).with_name("manifest-v1.json")
VALID_KINDS = frozenset({"command", "unittest-discover", "unittest-names"})
VALID_COSTS = frozenset({"fast", "semantic", "configured", "native", "reproduction"})
VALID_PROFILES = frozenset(
    {"current", "compatibility", "configured-sources", "native", "reproduction", "release"}
)
EXECUTION_PROFILES = VALID_PROFILES - {"release"}
GATED_PROFILES = frozenset({"configured-sources", "native", "reproduction"})
PROFILE_COSTS = {
    "current": frozenset({"fast", "semantic"}),
    "compatibility": frozenset({"semantic"}),
    "configured-sources": frozenset({"configured"}),
    "native": frozenset({"native"}),
    "reproduction": frozenset({"reproduction"}),
}


class ValidationPlanError(ValueError):
    pass


def _load_manifest(path: Path = MANIFEST) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationPlanError(f"validation manifest is unreadable: {exc}") from exc
    _validate_manifest(value)
    return value


def _portable(value: str) -> bool:
    path = Path(value)
    return bool(value) and not path.is_absolute() and ".." not in path.parts


def _validate_manifest(value: dict[str, Any]) -> None:
    if set(value) != {
        "schema_version",
        "compatibility_test_modules",
        "checks",
        "profiles",
        "gated_tests",
    }:
        raise ValidationPlanError("validation manifest fields are invalid")
    if value.get("schema_version") != "schuss-validation-manifest-v1":
        raise ValidationPlanError("unsupported validation manifest schema")
    compatibility_modules = value.get("compatibility_test_modules")
    checks = value.get("checks")
    profiles = value.get("profiles")
    gated = value.get("gated_tests")
    if (
        not isinstance(compatibility_modules, list)
        or not compatibility_modules
        or not all(
            isinstance(item, str)
            and item.startswith("tools.contracts.tests.test_")
            for item in compatibility_modules
        )
        or len(compatibility_modules) != len(set(compatibility_modules))
    ):
        raise ValidationPlanError("compatibility test modules are invalid")
    unknown_compatibility = [
        item
        for item in compatibility_modules
        if not (
            ROOT
            / (item.replace(".", "/") + ".py")
        ).is_file()
    ]
    if unknown_compatibility:
        raise ValidationPlanError(
            f"unknown compatibility test modules: {unknown_compatibility}"
        )
    if not isinstance(checks, list) or not isinstance(profiles, dict) or not isinstance(gated, list):
        raise ValidationPlanError("validation manifest collections are invalid")
    by_id: dict[str, dict[str, Any]] = {}
    named_tests: dict[str, str] = {}
    for check in checks:
        if not isinstance(check, dict) or not isinstance(check.get("id"), str):
            raise ValidationPlanError("validation check identity is invalid")
        identifier = check["id"]
        if identifier in by_id:
            raise ValidationPlanError(f"duplicate validation check: {identifier}")
        by_id[identifier] = check
        kind = check.get("kind")
        if kind not in VALID_KINDS:
            raise ValidationPlanError(f"unknown validation check kind: {identifier}")
        common = {"id", "kind", "validation_profile", "cost_class", "inputs"}
        optional = {
            "depends_on",
            "explicit_only",
            "preflight",
            "prerequisites",
            "tool_prerequisites",
        }
        kind_fields = {
            "command": {"argv"},
            "unittest-discover": {"start_dir", "pattern"},
            "unittest-names": {"tests"},
        }[kind]
        expected_fields = common | optional | kind_fields
        required_fields = common | kind_fields
        if not required_fields <= set(check) or not set(check) <= expected_fields:
            raise ValidationPlanError(
                f"invalid validation check fields: {identifier}"
            )
        if check.get("cost_class") not in VALID_COSTS:
            raise ValidationPlanError(f"unknown validation cost class: {identifier}")
        if check.get("validation_profile") not in EXECUTION_PROFILES:
            raise ValidationPlanError(f"invalid execution profile: {identifier}")
        if check["cost_class"] not in PROFILE_COSTS[check["validation_profile"]]:
            raise ValidationPlanError(
                f"validation profile/cost mismatch: {identifier}"
            )
        if not isinstance(check.get("explicit_only", False), bool):
            raise ValidationPlanError(f"invalid explicit-only flag: {identifier}")
        if not isinstance(check.get("preflight", False), bool):
            raise ValidationPlanError(f"invalid preflight flag: {identifier}")
        if check.get("preflight", False) and kind != "command":
            raise ValidationPlanError(
                f"validation preflight must be a command: {identifier}"
            )
        dependencies = check.get("depends_on", [])
        if (
            not isinstance(dependencies, list)
            or not all(isinstance(item, str) and item for item in dependencies)
            or len(dependencies) != len(set(dependencies))
        ):
            raise ValidationPlanError(
                f"invalid validation dependencies: {identifier}"
            )
        inputs = check.get("inputs")
        if not isinstance(inputs, list) or not inputs or not all(
            isinstance(item, str) and _portable(item.replace("**", "x")) for item in inputs
        ):
            raise ValidationPlanError(f"invalid validation inputs: {identifier}")
        declared_prerequisites = check.get("prerequisites", [])
        prerequisite_inputs = (
            set(declared_prerequisites)
            if isinstance(declared_prerequisites, list)
            and all(isinstance(item, str) for item in declared_prerequisites)
            else set()
        )
        missing_inputs = [
            item
            for item in inputs
            if item not in prerequisite_inputs
            and not glob.glob(str(ROOT / item), recursive=True)
        ]
        if missing_inputs:
            raise ValidationPlanError(
                f"unknown validation inputs for {identifier}: {missing_inputs}"
            )
        prerequisites = declared_prerequisites
        if not isinstance(prerequisites, list) or not all(
            isinstance(item, str) and _portable(item) for item in prerequisites
        ):
            raise ValidationPlanError(f"invalid validation prerequisites: {identifier}")
        tools = check.get("tool_prerequisites", [])
        if (
            not isinstance(tools, list)
            or not all(isinstance(item, str) and item for item in tools)
            or len(tools) != len(set(tools))
        ):
            raise ValidationPlanError(
                f"invalid validation tool prerequisites: {identifier}"
            )
        if kind == "unittest-discover":
            if not _portable(check.get("start_dir", "")) or check.get("pattern") != "test_*.py":
                raise ValidationPlanError(f"invalid discovery check: {identifier}")
        elif kind == "unittest-names":
            tests = check.get("tests")
            if not isinstance(tests, list) or not tests or not all(isinstance(item, str) for item in tests):
                raise ValidationPlanError(f"invalid named-test check: {identifier}")
            if check["validation_profile"] in GATED_PROFILES:
                for test in tests:
                    if test in named_tests:
                        raise ValidationPlanError(f"gated test is classified twice: {test}")
                    named_tests[test] = check["validation_profile"]
        else:
            argv = check.get("argv")
            if not isinstance(argv, list) or not argv or not all(isinstance(item, str) for item in argv):
                raise ValidationPlanError(f"invalid command check: {identifier}")
    for identifier, check in by_id.items():
        dependencies = check.get("depends_on", [])
        unknown_dependencies = sorted(set(dependencies) - set(by_id))
        if unknown_dependencies:
            raise ValidationPlanError(
                f"unknown validation dependencies for {identifier}: "
                f"{unknown_dependencies}"
            )
        if identifier in dependencies:
            raise ValidationPlanError(
                f"validation check depends on itself: {identifier}"
            )
        if check.get("preflight", False) and dependencies:
            raise ValidationPlanError(
                f"validation preflight cannot have dependencies: {identifier}"
            )
    _resolve_check_dependencies(value, by_id)

    if set(profiles) != VALID_PROFILES:
        raise ValidationPlanError("validation profile set is incomplete")
    direct_owners: dict[str, str] = {}
    for profile, entries in profiles.items():
        if not isinstance(entries, list):
            raise ValidationPlanError(f"validation profile is not a list: {profile}")
        for entry in entries:
            if not isinstance(entry, str):
                raise ValidationPlanError(f"validation profile entry is invalid: {profile}")
            if entry.startswith("@"):
                if entry[1:] not in profiles or entry[1:] == profile:
                    raise ValidationPlanError(f"validation profile reference is invalid: {entry}")
            elif entry not in by_id:
                raise ValidationPlanError(f"unknown validation check: {entry}")
            elif profile != "release":
                if entry in direct_owners:
                    raise ValidationPlanError(
                        f"validation check has multiple owners: {entry}"
                    )
                direct_owners[entry] = profile
                if by_id[entry]["validation_profile"] != profile:
                    raise ValidationPlanError(
                        f"validation check profile mismatch: {entry}"
                    )
    for identifier, check in by_id.items():
        explicit_only = check.get("explicit_only", False)
        if explicit_only and identifier in direct_owners:
            raise ValidationPlanError(
                f"explicit-only validation check has a profile owner: {identifier}"
            )
        if not explicit_only and identifier not in direct_owners:
            raise ValidationPlanError(
                f"validation check has no direct owner: {identifier}"
            )
    gated_map: dict[str, str] = {}
    for item in gated:
        if not isinstance(item, dict) or set(item) != {"test", "profile"}:
            raise ValidationPlanError("gated-test declaration is invalid")
        test = item["test"]
        profile = item["profile"]
        if test in gated_map:
            raise ValidationPlanError(f"gated test is declared twice: {test}")
        gated_map[test] = profile
    if gated_map != named_tests:
        missing = sorted(set(named_tests) - set(gated_map))
        extra = sorted(set(gated_map) - set(named_tests))
        raise ValidationPlanError(
            f"gated-test classification mismatch; missing={missing}; extra={extra}"
        )
    _expand_profiles(value, ["release"])


def _resolve_check_dependencies(
    value: dict[str, Any], selected: Iterable[str]
) -> list[str]:
    by_id = {check["id"]: check for check in value["checks"]}
    ordered: list[str] = []
    resolved: set[str] = set()
    visiting: set[str] = set()

    def visit(identifier: str) -> None:
        if identifier in resolved:
            return
        if identifier in visiting:
            raise ValidationPlanError(
                f"validation dependency cycle: {identifier}"
            )
        if identifier not in by_id:
            raise ValidationPlanError(
                f"unknown validation check dependency: {identifier}"
            )
        visiting.add(identifier)
        for dependency in by_id[identifier].get("depends_on", []):
            visit(dependency)
        visiting.remove(identifier)
        resolved.add(identifier)
        ordered.append(identifier)

    for identifier in selected:
        visit(identifier)
    return [
        *[
            identifier
            for identifier in ordered
            if by_id[identifier].get("preflight", False)
        ],
        *[
            identifier
            for identifier in ordered
            if not by_id[identifier].get("preflight", False)
        ],
    ]


def _expand_profiles(value: dict[str, Any], requested: Iterable[str]) -> list[str]:
    profiles = value["profiles"]
    by_id = {check["id"]: check for check in value["checks"]}
    expanded: list[str] = []
    seen_checks: set[str] = set()
    visiting: set[str] = set()

    def visit(profile: str) -> None:
        if profile not in profiles:
            raise ValidationPlanError(f"unknown validation profile: {profile}")
        if profile in visiting:
            raise ValidationPlanError(f"validation profile cycle: {profile}")
        visiting.add(profile)
        for entry in profiles[profile]:
            if entry.startswith("@"):
                visit(entry[1:])
            elif entry not in by_id:
                raise ValidationPlanError(f"unknown validation check: {entry}")
            elif entry not in seen_checks:
                seen_checks.add(entry)
                expanded.append(entry)
        visiting.remove(profile)

    for profile in requested:
        visit(profile)
    return _resolve_check_dependencies(value, expanded)


def _argv(check: dict[str, Any]) -> list[str]:
    kind = check["kind"]
    if kind == "unittest-discover":
        return [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            check["start_dir"],
            "-p",
            check["pattern"],
        ]
    if kind == "unittest-names":
        return [
            sys.executable,
            "tools/validation/unittest_gate.py",
            *check["tests"],
        ]
    return [sys.executable if item == "{python}" else item for item in check["argv"]]


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _missing_prerequisites(check: dict[str, Any]) -> tuple[list[str], list[str]]:
    files = [
        prerequisite
        for prerequisite in check.get("prerequisites", [])
        if not (ROOT / prerequisite).is_file()
    ]
    tools = [
        prerequisite
        for prerequisite in check.get("tool_prerequisites", [])
        if shutil.which(prerequisite) is None
    ]
    return files, tools


def _run_check(check: dict[str, Any]) -> dict[str, Any]:
    missing_files, missing_tools = _missing_prerequisites(check)
    if missing_files or missing_tools:
        return {
            "id": check["id"],
            "profile": check["validation_profile"],
            "cost_class": check["cost_class"],
            "status": "missing-prerequisite",
            "diagnostic_code": (
                "MISSING_CONFIGURED_SOURCE_PREREQUISITE"
                if "catalog/sources.local.yml" in missing_files
                else "MISSING_VALIDATION_TOOL_PREREQUISITE"
                if missing_tools
                else "MISSING_VALIDATION_FILE_PREREQUISITE"
            ),
            "exit_code": 2,
            "duration_ms": 0,
            "prerequisites": missing_files,
            "tool_prerequisites": missing_tools,
            "stdout_sha256": _sha256(b""),
            "stderr_sha256": _sha256(b""),
        }
    command = _argv(check)
    environment = os.environ.copy()
    environment["SCHUSS_VALIDATION_PROFILE"] = check["validation_profile"]
    started = time.monotonic_ns()
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    duration_ms = (time.monotonic_ns() - started) // 1_000_000
    return {
        "id": check["id"],
        "profile": check["validation_profile"],
        "cost_class": check["cost_class"],
        "status": (
            "passed"
            if completed.returncode == 0
            else "incomplete"
            if completed.returncode == 3
            else "failed"
        ),
        "diagnostic_code": (
            "EXPLICIT_VALIDATION_SKIPPED"
            if completed.returncode == 3 and check["kind"] == "unittest-names"
            else "VALIDATION_PREFLIGHT_INCOMPLETE"
            if completed.returncode == 3 and check.get("preflight", False)
            else "VALIDATION_COMMAND_INCOMPLETE"
            if completed.returncode == 3
            else None
        ),
        "exit_code": completed.returncode,
        "duration_ms": duration_ms,
        "prerequisites": [],
        "tool_prerequisites": [],
        "argv": command,
        "stdout_sha256": _sha256(completed.stdout),
        "stderr_sha256": _sha256(completed.stderr),
        "stdout_tail": completed.stdout.decode("utf-8", errors="replace")[-2000:],
        "stderr_tail": completed.stderr.decode("utf-8", errors="replace")[-4000:],
    }


def _report(
    requested: list[str],
    requested_checks: list[str],
    selected: list[str],
    results: list[dict[str, Any]],
) -> tuple[int, dict[str, Any]]:
    failed = sum(item["status"] == "failed" for item in results)
    incomplete = sum(
        item["status"] in {"incomplete", "missing-prerequisite"}
        for item in results
    )
    report = {
        "schema_version": "schuss-validation-report-v1",
        "requested_profiles": requested,
        "requested_checks": requested_checks,
        "selected_check_ids": selected,
        "checks": results,
        "summary": {
            "status": "failed" if failed else "incomplete" if incomplete else "passed",
            "passed": sum(item["status"] == "passed" for item in results),
            "failed": failed,
            "incomplete": incomplete,
            "not_run": len(selected) - len(results),
            "duration_ms": sum(item["duration_ms"] for item in results),
        },
    }
    return (1 if failed else 2 if incomplete else 0), report


def run_profiles(
    requested: list[str],
    *,
    requested_checks: list[str] | None = None,
    keep_going: bool = False,
    manifest_path: Path = MANIFEST,
) -> tuple[int, dict[str, Any]]:
    manifest = _load_manifest(manifest_path)
    check_ids = _expand_profiles(manifest, requested)
    by_id = {check["id"]: check for check in manifest["checks"]}
    explicit = requested_checks or []
    unknown = sorted(set(explicit) - set(by_id))
    if unknown:
        raise ValidationPlanError(f"unknown explicit validation checks: {unknown}")
    check_ids = _resolve_check_dependencies(
        manifest, [*check_ids, *explicit]
    )
    prerequisite_results = [
        _run_check(check)
        for identifier in check_ids
        if any(_missing_prerequisites(check := by_id[identifier]))
    ]
    if prerequisite_results:
        for result in prerequisite_results:
            print(f"[{result['id']}] {result['status']} (0 ms)", file=sys.stderr)
        return _report(requested, explicit, check_ids, prerequisite_results)

    results: list[dict[str, Any]] = []
    for identifier in check_ids:
        result = _run_check(by_id[identifier])
        results.append(result)
        print(
            f"[{identifier}] {result['status']} ({result['duration_ms']} ms)",
            file=sys.stderr,
        )
        if result["status"] != "passed" and (
            by_id[identifier].get("preflight", False) or not keep_going
        ):
            break
    return _report(requested, explicit, check_ids, results)


def _plan(manifest: dict[str, Any], selected: list[str]) -> dict[str, Any]:
    by_id = {check["id"]: check for check in manifest["checks"]}
    return {
        "schema_version": "schuss-validation-plan-v1",
        "selected_check_ids": selected,
        "checks": [
            {
                "id": identifier,
                "profile": by_id[identifier]["validation_profile"],
                "cost_class": by_id[identifier]["cost_class"],
                "inputs": by_id[identifier]["inputs"],
                "prerequisites": by_id[identifier].get("prerequisites", []),
                "tool_prerequisites": by_id[identifier].get(
                    "tool_prerequisites", []
                ),
                "preflight": by_id[identifier].get("preflight", False),
                "depends_on": by_id[identifier].get("depends_on", []),
                "argv": _argv(by_id[identifier]),
            }
            for identifier in selected
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--profile",
        action="append",
        choices=sorted(VALID_PROFILES),
        dest="profiles",
    )
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--only", action="append", dest="checks")
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--keep-going", action="store_true")
    parser.add_argument("--validate-manifest", action="store_true")
    arguments = parser.parse_args(argv)
    try:
        manifest = _load_manifest(arguments.manifest)
        custom_manifest = arguments.manifest.resolve() != MANIFEST.resolve()
        if custom_manifest and not (
            arguments.validate_manifest or arguments.list or arguments.plan
        ):
            raise ValidationPlanError(
                "custom manifests are inspection-only; use --validate-manifest, "
                "--list, or --plan"
            )
        if arguments.validate_manifest:
            print(json.dumps({"status": "valid", "check_count": len(manifest["checks"])}, sort_keys=True))
            return 0
        if arguments.list:
            print(
                json.dumps(
                    {
                        "schema_version": "schuss-validation-list-v1",
                        "profiles": manifest["profiles"],
                        "checks": manifest["checks"],
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
            )
            return 0
        profiles = arguments.profiles or ([] if arguments.checks else ["current"])
        selected = _expand_profiles(manifest, profiles)
        by_id = {check["id"]: check for check in manifest["checks"]}
        unknown = sorted(set(arguments.checks or []) - set(by_id))
        if unknown:
            raise ValidationPlanError(f"unknown explicit validation checks: {unknown}")
        selected = _resolve_check_dependencies(
            manifest, [*selected, *(arguments.checks or [])]
        )
        if arguments.plan:
            print(json.dumps(_plan(manifest, selected), ensure_ascii=False, sort_keys=True, separators=(",", ":")))
            return 0
        code, report = run_profiles(
            profiles,
            requested_checks=arguments.checks,
            keep_going=arguments.keep_going,
            manifest_path=arguments.manifest,
        )
    except ValidationPlanError as exc:
        print(f"validation plan invalid: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
