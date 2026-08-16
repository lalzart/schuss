#!/usr/bin/env python3
"""Validate the Task 023 application spine without writes or backend execution."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools/contracts"
for value in (ROOT, TOOLS):
    if str(value) not in sys.path:
        sys.path.insert(0, str(value))

from packages.schuss_core.cli import run as run_cli
from packages.schuss_core.control_plane import (
    canonical_result_bytes,
    dispatch_operation,
    load_repository_context,
)
from packages.schuss_core.product_cli import application_describe_request
from compiler_determinism_matrix import _repository_files, copy_current_tree
import validator_core as core


FIXTURE = ROOT / "tools/contracts/tests/fixtures/task023-smoke-cases.json"


class Task023ValidationError(ValueError):
    """A deterministic Task 023 validation failure."""


def _canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _source_snapshot(repository_root: Path) -> str:
    """Hash every tracked or non-ignored untracked source byte."""

    digest = hashlib.sha256()
    for relative in _repository_files(repository_root):
        path = repository_root / relative
        digest.update(relative.as_posix().encode("utf-8") + b"\0")
        if path.is_symlink():
            digest.update(b"symlink\0" + os.readlink(path).encode("utf-8") + b"\0")
        elif path.is_file():
            digest.update(b"file\0" + _file_sha256(path).encode("ascii") + b"\0")
        else:
            digest.update(b"absent\0")
    return digest.hexdigest()


def _filesystem_metadata_snapshot(repository_root: Path) -> str:
    """Cover ignored output/cache trees without reading multi-gigabyte artifacts."""

    digest = hashlib.sha256()
    for directory, names, files in os.walk(repository_root):
        base = Path(directory)
        if base == repository_root:
            names[:] = [name for name in names if name != ".git"]
        names.sort()
        files.sort()
        for name in [*names, *files]:
            path = base / name
            relative = path.relative_to(repository_root).as_posix()
            try:
                metadata = path.lstat()
            except FileNotFoundError:
                continue
            kind = (
                "link"
                if stat.S_ISLNK(metadata.st_mode)
                else "directory"
                if stat.S_ISDIR(metadata.st_mode)
                else "file"
            )
            digest.update(
                (
                    f"{relative}\0{kind}\0{metadata.st_size}\0"
                    f"{metadata.st_mtime_ns}\0"
                ).encode("utf-8")
            )
    return digest.hexdigest()


def _snapshot(repository_root: Path) -> dict[str, str]:
    return {
        "source_content_sha256": _source_snapshot(repository_root),
        "filesystem_metadata_sha256": _filesystem_metadata_snapshot(repository_root),
    }


def _validated_fixture(repository_root: Path) -> dict[str, Any]:
    fixture_path = (
        repository_root
        / "tools/contracts/tests/fixtures/task023-smoke-cases.json"
    )
    fixture = core.load_json(fixture_path)
    if fixture.get("schema_version") != "task023-smoke-cases-v1":
        raise Task023ValidationError("smoke fixture schema version is invalid")
    cases = fixture.get("cases")
    if not isinstance(cases, list) or len(cases) != 8:
        raise Task023ValidationError("smoke fixture must contain exactly eight cases")
    identifiers = [item.get("case_id") for item in cases if isinstance(item, dict)]
    if len(identifiers) != len(set(identifiers)):
        raise Task023ValidationError("smoke case identifiers must be unique")
    forbidden_routes = {
        ("build", "execute"),
        ("project", "init"),
        ("project", "transact"),
        ("project", "op"),
        ("graph", "transact"),
    }
    for case in cases:
        arguments = case.get("arguments")
        if not isinstance(arguments, list) or not all(
            isinstance(value, str) for value in arguments
        ):
            raise Task023ValidationError("smoke arguments must be string arrays")
        if tuple(arguments[:2]) in forbidden_routes:
            raise Task023ValidationError("smoke fixture contains a mutating route")
        if "--json" not in arguments:
            raise Task023ValidationError("every smoke case must request canonical JSON")
    return fixture


def _invoke(
    arguments: list[str],
    context_loader,
) -> tuple[int, bytes, str]:
    stdout = io.BytesIO()
    stderr = io.StringIO()
    code = run_cli(
        arguments,
        io.BytesIO(),
        stdout,
        stderr,
        context_loader,
    )
    return code, stdout.getvalue(), stderr.getvalue()


def run_smoke(repository_root: Path) -> dict[str, Any]:
    repository_root = repository_root.resolve()
    fixture = _validated_fixture(repository_root)
    record_set = repository_root / fixture["record_set"]
    project = repository_root / fixture["project"]
    context_cache: dict[str, Any] = {}

    def context_loader(**kwargs):
        selected = Path(kwargs.get("record_set_path") or repository_root).resolve()
        key = str(selected)
        if key not in context_cache:
            context_cache[key] = load_repository_context(
                repository_root,
                **kwargs,
            )
        return context_cache[key]

    before = _snapshot(repository_root)
    cases = []
    capability_value = None
    for case in fixture["cases"]:
        arguments = [
            str(project) if value == "{project}" else value
            for value in case["arguments"]
        ]
        code, output, error = _invoke(arguments, context_loader)
        if code != 0 or error:
            raise Task023ValidationError(
                f"smoke case {case['case_id']} failed with exit {code}"
            )
        try:
            value = json.loads(output)
        except json.JSONDecodeError as exc:
            raise Task023ValidationError(
                f"smoke case {case['case_id']} did not emit JSON"
            ) from exc
        for field, expected in (
            ("operation", case["expected_operation"]),
            ("status", case["expected_status"]),
            ("schema_version", case["expected_schema_version"]),
        ):
            if value.get(field) != expected:
                raise Task023ValidationError(
                    f"smoke case {case['case_id']} has unexpected {field}"
                )
        if _canonical_bytes(value) != output:
            raise Task023ValidationError(
                f"smoke case {case['case_id']} output is not canonical"
            )
        if case["case_id"] == "application-description":
            capability_value = value["value"]
        cases.append(
            {
                "case_id": case["case_id"],
                "byte_length": len(output),
                "byte_sha256": hashlib.sha256(output).hexdigest(),
                "operation": value["operation"],
                "schema_version": value["schema_version"],
                "status": value["status"],
            }
        )

    context = context_loader(record_set_path=record_set)
    direct_application = canonical_result_bytes(
        dispatch_operation(application_describe_request(), context), context
    ) + b"\n"
    application_case = next(
        item for item in cases if item["case_id"] == "application-description"
    )
    if hashlib.sha256(direct_application).hexdigest() != application_case["byte_sha256"]:
        raise Task023ValidationError(
            "direct and CLI application descriptions are not byte-identical"
        )
    assert capability_value is not None
    build_execute = next(
        (
            item
            for item in capability_value["operations"]
            if item["operation"] == "build.execute"
        ),
        None,
    )
    if build_execute is None or build_execute["effect_class"] != "build-output-write":
        raise Task023ValidationError("build capability inspection is incomplete")
    if not {
        "exact-handler",
        "execute-intent",
        "fresh-output-root",
    }.issubset(build_execute["explicit_gates"]):
        raise Task023ValidationError("build execution gates are incomplete")

    presentations = {}
    for presentation_id, arguments in (
        ("root-help", ["--help"]),
        ("completion-bash", ["completion", "bash"]),
        ("completion-fish", ["completion", "fish"]),
        ("completion-zsh", ["completion", "zsh"]),
    ):
        code, output, error = _invoke(arguments, context_loader)
        if code != 0 or error:
            raise Task023ValidationError(f"{presentation_id} failed")
        presentations[presentation_id] = {
            "byte_length": len(output),
            "byte_sha256": hashlib.sha256(output).hexdigest(),
        }

    after = _snapshot(repository_root)
    if before != after:
        raise Task023ValidationError("application smoke mutated the repository")
    return {
        "schema_version": "task023-smoke-result-v1",
        "status": "valid",
        "record_set": "schuss-record-set-000015@1",
        "cases": cases,
        "presentations": presentations,
        "application_description_sha256": application_case["byte_sha256"],
        "direct_cli_application_match": True,
        "build_capability": {
            "operation": "build.execute",
            "effect_class": build_execute["effect_class"],
            "availability": build_execute["availability"],
            "explicit_gates": build_execute["explicit_gates"],
        },
        "filesystem_unchanged": True,
        "backend_execution": "not-run",
        "project_write": "not-run",
        "hardware_access": "not-run",
    }


def _run_fresh_worker(
    repository_root: Path,
    *,
    cwd: Path,
    environment: dict[str, str],
) -> bytes:
    cwd.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        str(repository_root / "tools/contracts/validate_task023.py"),
        "--worker",
    ]
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise Task023ValidationError("fresh-root smoke worker failed")
    return completed.stdout


def validate(repository_root: Path = ROOT, *, fresh_roots: bool = True) -> dict[str, Any]:
    repository_root = repository_root.resolve()
    local = run_smoke(repository_root)
    fresh_root_match = "not-run"
    if fresh_roots:
        with tempfile.TemporaryDirectory(prefix="schuss-task023-") as temporary:
            temporary_root = Path(temporary)
            roots = (
                temporary_root / "fresh-root-a" / "repository",
                temporary_root / "fresh root b" / "nested" / "repository",
            )
            for root in roots:
                copy_current_tree(
                    repository_root,
                    root,
                    include_task009_capsule=False,
                )
            base_environment = {
                key: value
                for key, value in os.environ.items()
                if key not in {"PYTHONPATH", "PYTHONHOME", "COLUMNS", "TZ"}
            }
            environments = (
                {
                    **base_environment,
                    "PYTHONDONTWRITEBYTECODE": "1",
                    "PYTHONHASHSEED": "1",
                    "LC_ALL": "C",
                    "LANG": "C",
                    "COLUMNS": "29",
                    "TZ": "UTC",
                    "USER": "task023-user-a",
                    "LOGNAME": "task023-user-a",
                    "HOSTNAME": "task023-host-a",
                    "SCHUSS_TASK023_NOISE": "alpha",
                },
                {
                    **base_environment,
                    "PYTHONDONTWRITEBYTECODE": "1",
                    "PYTHONHASHSEED": "987654",
                    "LC_ALL": "C.UTF-8",
                    "LANG": "C.UTF-8",
                    "COLUMNS": "211",
                    "TZ": "Pacific/Honolulu",
                    "USER": "task023-user-b",
                    "LOGNAME": "task023-user-b",
                    "HOSTNAME": "task023-host-b",
                    "SCHUSS_TASK023_NOISE": "omega",
                },
            )
            outputs = [
                _run_fresh_worker(
                    root,
                    cwd=temporary_root / f"cwd-{index}",
                    environment=environment,
                )
                for index, (root, environment) in enumerate(
                    zip(roots, environments), start=1
                )
            ]
            if outputs[0] != outputs[1]:
                raise Task023ValidationError(
                    "fresh roots and varied environments produced different smoke bytes"
                )
            if json.loads(outputs[0]) != local:
                raise Task023ValidationError(
                    "fresh-root smoke differs from the source-root smoke"
                )
            fresh_root_match = "identical"
    return {
        "schema_version": "task023-validation-result-v1",
        "status": "valid",
        "fresh_roots": fresh_root_match,
        "smoke": local,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--no-fresh-roots", action="store_true")
    args = parser.parse_args()
    try:
        result = (
            run_smoke(ROOT)
            if args.worker
            else validate(ROOT, fresh_roots=not args.no_fresh_roots)
        )
    except (OSError, UnicodeError, ValueError, KeyError) as exc:
        print(f"task023-validation-error: {exc}", file=sys.stderr)
        return 1
    sys.stdout.buffer.write(_canonical_bytes(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
