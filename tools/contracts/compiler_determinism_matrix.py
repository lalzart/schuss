#!/usr/bin/env python3
"""Reusable Tasks 013-015 compiler determinism matrix.

The parent process copies the current tracked and non-ignored untracked tree
into two temporary repository roots, then launches fresh Python processes with
varied roots, working directories, locales, hash seeds, record enumeration,
and harmless environment noise.  The source worktree is read only.  Task 014
execution is optional and can run only through its authenticated Task 011C
adapter into temporary scratch roots.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[2]
TASK013_RECORD_SET = Path("contracts/record-sets/task013-compiler-front-half-v1.json")
TASK014_RECORD_SET = Path("contracts/record-sets/task014-build-execution-v1.json")
TASK015_RECORD_SET = Path("contracts/record-sets/task015-minimal-direct-frontend-v1.json")
TASK009_CAPSULE = Path("build/task009-prerequisite-repair-v1/content-addressed")
ZERO_HASH = "sha256:" + "0" * 64

TIMESTAMP_PATTERN = re.compile(r"\b20\d\d-\d\d-\d\d(?:[T ][0-2]\d:[0-5]\d(?::[0-5]\d)?)?")
ABSOLUTE_PATH_PATTERNS = (
    re.compile(r"/(?:Users|home|private|tmp|var/folders)/[^\"\s]+"),
    re.compile(r"[A-Za-z]:\\\\[^\"\s]+"),
)


class MatrixFailure(RuntimeError):
    """A deterministic matrix invariant failed."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def byte_facts(value: bytes) -> dict[str, Any]:
    return {
        "byte_length": len(value),
        "byte_sha256": hashlib.sha256(value).hexdigest(),
    }


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parent_semantic_snapshot(repository_root: Path) -> dict[str, Any]:
    """Authenticate the unchanged semantic members inherited by Tasks 013-015."""

    manifests = {
        "task013": _load_json(repository_root / TASK013_RECORD_SET),
        "task014": _load_json(repository_root / TASK014_RECORD_SET),
        "task015": _load_json(repository_root / TASK015_RECORD_SET),
    }
    task013_members = manifests["task013"]["record_members"]
    for task in ("task014", "task015"):
        if manifests[task]["record_members"] != task013_members:
            raise MatrixFailure(f"{task} semantic record members differ from Task 013")

    authenticated = []
    for member in task013_members:
        portable_path = member["portable_path"]
        path = repository_root / portable_path
        if not path.is_file():
            raise MatrixFailure(f"parent semantic member is absent: {portable_path}")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != member["byte_sha256"]:
            raise MatrixFailure(f"parent semantic member bytes differ: {portable_path}")
        authenticated.append(
            {"portable_path": portable_path, "byte_sha256": actual}
        )

    manifest_facts = {
        task: byte_facts((repository_root / path).read_bytes())
        for task, path in (
            ("task013", TASK013_RECORD_SET),
            ("task014", TASK014_RECORD_SET),
            ("task015", TASK015_RECORD_SET),
        )
    }
    return {
        "record_count": len(authenticated),
        "records_byte_sha256": hashlib.sha256(
            canonical_bytes(authenticated)
        ).hexdigest(),
        "record_members_equal": True,
        "record_set_manifests": manifest_facts,
    }


def find_leaks(serialized: bytes, forbidden_values: Iterable[str]) -> list[str]:
    """Return stable leak classes without echoing host-local values."""

    text = serialized.decode("utf-8")
    findings = set()
    for value in forbidden_values:
        if value and value in text:
            findings.add("known-host-path")
    if TIMESTAMP_PATTERN.search(text):
        findings.add("timestamp")
    if any(pattern.search(text) for pattern in ABSOLUTE_PATH_PATTERNS):
        findings.add("absolute-path")
    return sorted(findings)


def _repository_files(repository_root: Path) -> list[Path]:
    completed = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=repository_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode == 0:
        return sorted(
            (
                Path(value.decode("utf-8"))
                for value in completed.stdout.split(b"\0")
                if value
            ),
            key=lambda value: value.as_posix(),
        )

    excluded = {".git", "build", "__pycache__", ".pytest_cache", ".DS_Store"}
    return sorted(
        (
            path.relative_to(repository_root)
            for path in repository_root.rglob("*")
            if path.is_file() and not any(part in excluded for part in path.parts)
        ),
        key=lambda value: value.as_posix(),
    )


def copy_current_tree(
    source_root: Path,
    destination_root: Path,
    *,
    include_task009_capsule: bool,
) -> None:
    """Copy current tracked/untracked task bytes without Git or ignored outputs."""

    destination_root.mkdir(parents=True)
    for relative in _repository_files(source_root):
        source = source_root / relative
        if not source.exists() and not source.is_symlink():
            continue
        destination = destination_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.is_symlink():
            destination.symlink_to(os.readlink(source))
        elif source.is_file():
            shutil.copy2(source, destination)
    if include_task009_capsule:
        source = source_root / TASK009_CAPSULE
        destination = destination_root / TASK009_CAPSULE
        shutil.copytree(source, destination, symlinks=True)


def _reverse_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    return {key: copy.deepcopy(item) for key, item in reversed(list(value.items()))}


def _ordered_records(
    records: Mapping[str, Iterable[Mapping[str, Any]]], order: str
) -> dict[str, list[dict[str, Any]]]:
    groups = list(records.items())
    if order == "reverse":
        groups.reverse()
    result = {}
    for group, values in groups:
        copied = [copy.deepcopy(value) for value in values]
        if order == "reverse":
            copied.reverse()
        result[group] = copied
    return result


def _request_reference(
    records: Mapping[str, Iterable[Mapping[str, Any]]], stable_id: str, revision: int
) -> dict[str, Any]:
    matches = [
        value
        for value in records["request"]
        if value["build_request_id"] == stable_id and value["revision"] == revision
    ]
    if len(matches) != 1:
        raise MatrixFailure(
            f"build request {stable_id}@{revision} does not resolve exactly once"
        )
    return {
        key: matches[0][key]
        for key in ("build_request_id", "revision", "content_hash")
    }


def _compilation_context(operation_context: Any, reference: dict[str, Any], order: str) -> Any:
    from packages.schuss_core.compiler_front_half import CompilationContext

    records = _ordered_records(operation_context.records, order)
    schemas = (
        _reverse_mapping(operation_context.schemas)
        if order == "reverse"
        else copy.deepcopy(dict(operation_context.schemas))
    )
    closure_source = {
        "kind": "record-set",
        "record_set_reference": copy.deepcopy(operation_context.record_set_reference),
    }
    if order == "reverse":
        closure_source = _reverse_mapping(closure_source)
        reference = _reverse_mapping(reference)
    return CompilationContext.from_values(
        build_request_reference=reference,
        closure_source=closure_source,
        records=records,
        schemas=schemas,
    )


def _artifact_payload(plan: Mapping[str, Any], kind: str) -> dict[str, Any]:
    matches = [
        item["payload"]
        for item in plan["artifacts"]
        if item["descriptor"]["artifact_kind"] == kind
    ]
    if len(matches) != 1:
        raise MatrixFailure(f"plan does not contain exactly one {kind} artifact")
    return matches[0]


def _plan_facts(plan: dict[str, Any]) -> dict[str, Any]:
    serialized = canonical_bytes(plan)
    origin = _artifact_payload(plan, "origin-source-map")
    return {
        **byte_facts(serialized),
        "status": plan["status"],
        "stage_order": [
            {"ordinal": item["ordinal"], "stage": item["stage"], "status": item["status"]}
            for item in plan["stages"]
        ],
        "artifact_order": [
            item["descriptor"]["artifact_kind"] for item in plan["artifacts"]
        ],
        "artifact_payloads": {
            item["descriptor"]["artifact_kind"]: {
                "byte_length": item["descriptor"]["byte_length"],
                "byte_sha256": item["descriptor"]["byte_sha256"],
            }
            for item in plan["artifacts"]
        },
        "diagnostic_order": [
            {
                "stage": item["stage"],
                "code": item["code"],
                "subject": item["subject"],
                "location": item["location"],
            }
            for item in plan["diagnostics"]
        ],
        "origin_map": {
            **byte_facts(canonical_bytes(origin)),
            "entry_count": len(origin["entries"]),
        },
    }


def _negative_plan(compilation: Any, order: str) -> dict[str, Any]:
    from packages.schuss_core.compiler_front_half import CompilationContext, plan_build

    records = compilation.records()
    targets = [
        value
        for value in records["graphs"]
        if value.get("graph_id") == "schuss-graph-000002"
    ]
    if len(targets) != 1:
        raise MatrixFailure("Task 013 negative fixture graph is not exact")
    changed = copy.deepcopy(targets[0])
    changed["display_name"] = "Determinism diagnostic fixture"
    records["graphs"] = [
        changed if value.get("graph_id") == changed["graph_id"] else value
        for value in records["graphs"]
    ]
    records["graphs"].append(copy.deepcopy(changed))
    if order == "reverse":
        records = _ordered_records(records, order)
    invalid = CompilationContext.from_values(
        build_request_reference=compilation.build_request_reference(),
        closure_source=compilation.closure_source(),
        records=records,
        schemas=compilation.schemas(),
    )
    return plan_build(invalid)


def _direct_inputs(context: Any, order: str) -> tuple[dict[str, Any], dict[str, Any]]:
    graphs = [
        copy.deepcopy(value)
        for value in context.records["graphs"]
        if value["graph_id"] == "schuss-graph-000001"
    ]
    contracts = [
        copy.deepcopy(value)
        for value in context.records["contracts"]
        if value["component_contract_id"] == "schuss-component-contract-000003"
    ]
    if len(graphs) != 1 or len(contracts) != 1:
        raise MatrixFailure("Task 015 graph/contract input is not exact")
    graph, contract = graphs[0], contracts[0]
    if order == "reverse":
        graph["public_port_exposures"] = list(reversed(graph["public_port_exposures"]))
        graph = _reverse_mapping(graph)
        contract = _reverse_mapping(contract)
    return graph, contract


def _host_compile_facts(result: Mapping[str, Any], scratch_root: Path) -> dict[str, Any]:
    from packages.schuss_core.direct_frontend import Q27_SCALE, evaluate_linear_mix_q27

    compiler = shutil.which("clang++")
    if compiler is None:
        raise MatrixFailure("clang++ is unavailable for Task 015 host validation")
    rng = random.Random(15001)
    vectors = [
        (-(1 << 31), (1 << 31) - 1, control)
        for control in (-1, 0, 1, Q27_SCALE // 2, Q27_SCALE, Q27_SCALE + 1)
    ] + [
        (
            rng.randint(-(1 << 31), (1 << 31) - 1),
            rng.randint(-(1 << 31), (1 << 31) - 1),
            rng.randint(-100, Q27_SCALE + 100),
        )
        for _ in range(32)
    ]
    rows = ",\n".join("{" + f"{a},{b},{control}" + "}" for a, b, control in vectors)
    source = (
        result["generated_cpp"]["text"]
        + "\n#include <cstdio>\n"
        + "int main(){std::int32_t v[][3]={"
        + rows
        + "};for(auto &r:v){std::int32_t o=0;"
        + "schuss_blend_process_q27(&r[0],&r[1],r[2],&o,1);"
        + 'std::printf("%d\\n",o);}return 0;}\n'
    )
    source_path = scratch_root / "task015-host.cpp"
    executable = scratch_root / "task015-host"
    source_path.write_text(source, encoding="utf-8", newline="\n")
    compiled = subprocess.run(
        [compiler, "-std=c++17", "-g0", str(source_path), "-o", str(executable)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if compiled.returncode != 0:
        raise MatrixFailure("Task 015 generated C++ did not host-compile")
    executed = subprocess.run(
        [str(executable)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if executed.returncode != 0 or executed.stderr:
        raise MatrixFailure("Task 015 host vector executable failed")
    observed = [int(value) for value in executed.stdout.decode("utf-8").splitlines()]
    expected = [evaluate_linear_mix_q27(*value) for value in vectors]
    if observed != expected:
        raise MatrixFailure("Task 015 host vectors differ from the pure evaluator")
    return {
        "status": "passed",
        "compiler": "clang++",
        "vector_count": len(vectors),
        "output_byte_sha256": hashlib.sha256(executed.stdout).hexdigest(),
    }


def _adapter_module(repository_root: Path) -> Any:
    path = repository_root / "legacy/ksoloti-bridge/task011c_adapter.py"
    specification = importlib.util.spec_from_file_location(
        "compiler_determinism_task014_adapter", path
    )
    if specification is None or specification.loader is None:
        raise MatrixFailure("Task 014 authenticated adapter cannot be loaded")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _task014_execution(
    repository_root: Path,
    order: str,
    scratch_root: Path,
) -> dict[str, Any]:
    from packages.schuss_core.build_execution import (
        ExecutionService,
        execute_build,
        handler_reference,
    )
    from packages.schuss_core.control_plane import load_repository_context

    context = load_repository_context(
        repository_root,
        record_set_path=repository_root / TASK014_RECORD_SET,
    )
    reference = _request_reference(
        context.records, "schuss-build-request-000002", 2
    )
    compilation = _compilation_context(context, reference, order)
    adapter = _adapter_module(repository_root)
    registration = adapter.registration()
    output_root = scratch_root / "task014-output"
    service = ExecutionService.from_values((registration,), output_root)
    result = execute_build(
        compilation,
        handler_reference(registration.descriptor),
        service,
        execution_intent=True,
    )
    if result["status"] != "success":
        codes = ",".join(item["code"] for item in result["diagnostics"])
        raise MatrixFailure(f"Task 014 authenticated execution failed: {codes}")
    return {
        **byte_facts(canonical_bytes(result)),
        "status": result["status"],
        "artifact_order": [item["artifact_kind"] for item in result["artifacts"]],
        "artifacts": {
            item["artifact_kind"]: {
                "byte_length": item["byte_length"],
                "byte_sha256": item["byte_sha256"],
            }
            for item in result["artifacts"]
        },
        "evidence_levels": copy.deepcopy(result["evidence_levels"]),
        "output_publication": result["output_publication"],
    }


def worker_result(
    repository_root: Path,
    order: str,
    scratch_root: Path,
    *,
    execute_task014: bool,
) -> dict[str, Any]:
    """Run one fresh-process matrix cell and return only portable facts."""

    sys.path[:0] = [
        str(repository_root),
        str(repository_root / "tools/contracts"),
    ]
    from packages.schuss_core.compiler_front_half import plan_build
    from packages.schuss_core.control_plane import load_repository_context
    from packages.schuss_core.direct_frontend import lower_minimal_direct

    task013_context = load_repository_context(
        repository_root,
        record_set_path=repository_root / TASK013_RECORD_SET,
    )
    task013_reference = _request_reference(
        task013_context.records, "schuss-build-request-000002", 2
    )
    task013_compilation = _compilation_context(
        task013_context, task013_reference, order
    )
    task013_plan = plan_build(task013_compilation)
    if task013_plan["status"] != "success":
        raise MatrixFailure("Task 013 matrix plan did not succeed")
    negative_plan = _negative_plan(task013_compilation, order)
    if negative_plan["status"] != "invalid" or not negative_plan["diagnostics"]:
        raise MatrixFailure("Task 013 negative diagnostic fixture did not fail closed")

    task015_context = load_repository_context(
        repository_root,
        record_set_path=repository_root / TASK015_RECORD_SET,
    )
    task015_reference = _request_reference(
        task015_context.records, "schuss-build-request-000001", 2
    )
    task015_compilation = _compilation_context(
        task015_context, task015_reference, order
    )
    task015_plan = plan_build(task015_compilation)
    graph, contract = _direct_inputs(task015_context, order)
    direct = lower_minimal_direct(task015_plan, graph, contract)
    host = _host_compile_facts(direct, scratch_root)

    serialized_values = (
        canonical_bytes(task013_plan),
        canonical_bytes(negative_plan),
        canonical_bytes(task015_plan),
        canonical_bytes(direct),
    )
    forbidden = (
        str(repository_root),
        str(Path.cwd()),
        os.environ.get("TMPDIR", ""),
    )
    leaks = sorted(
        {
            finding
            for value in serialized_values
            for finding in find_leaks(value, forbidden)
        }
    )
    if leaks:
        raise MatrixFailure("portable compiler output leaked: " + ",".join(leaks))

    direct_bytes = canonical_bytes(direct)
    source_map = canonical_bytes(direct["source_map"])
    result = {
        "task013": {
            "successful_plan": _plan_facts(task013_plan),
            "negative_plan": {
                **byte_facts(canonical_bytes(negative_plan)),
                "status": negative_plan["status"],
                "diagnostic_order": [
                    {
                        "stage": item["stage"],
                        "code": item["code"],
                        "subject": item["subject"],
                        "location": item["location"],
                    }
                    for item in negative_plan["diagnostics"]
                ],
            },
        },
        "task015": {
            "successful_plan": _plan_facts(task015_plan),
            "direct_result": {
                **byte_facts(direct_bytes),
                "module": byte_facts(canonical_bytes(direct["module"])),
                "generated_cpp": {
                    "byte_length": direct["generated_cpp"]["byte_length"],
                    "byte_sha256": direct["generated_cpp"]["byte_sha256"],
                },
                "source_map": {
                    **byte_facts(source_map),
                    "mapping_order": [
                        item["generated"] for item in direct["source_map"]["mappings"]
                    ],
                },
            },
            "host_compile": host,
        },
        "task014_execution": (
            _task014_execution(repository_root, order, scratch_root)
            if execute_task014
            else {"status": "not-run"}
        ),
        "parent_semantic_records": parent_semantic_snapshot(repository_root),
        "leak_check": "passed",
    }
    return result


def _available_locales() -> set[str]:
    completed = subprocess.run(
        ["locale", "-a"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        return {"C"}
    return {value.strip() for value in completed.stdout.decode("utf-8").splitlines()}


def _alternate_locale() -> str:
    available = _available_locales()
    for candidate in ("en_US.UTF-8", "C.UTF-8", "UTF-8"):
        if candidate in available:
            return candidate
    return "C"


def _task014_mode(repository_root: Path, requested: str) -> tuple[bool, str]:
    if requested == "skip":
        return False, "skipped-by-request"
    if not (repository_root / TASK009_CAPSULE).is_dir():
        if requested == "require":
            raise MatrixFailure("Task 014 execution prerequisite capsule is unavailable")
        return False, "skipped-prerequisite-unavailable"
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    checked = subprocess.run(
        [sys.executable, "tools/contracts/validate_task009_prerequisite.py"],
        cwd=repository_root,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if checked.returncode != 0:
        if requested == "require":
            raise MatrixFailure("Task 014 execution prerequisite validation failed")
        return False, "skipped-prerequisite-invalid"
    return True, "authenticated-handler"


def _scenario_definitions(alternate_locale: str) -> tuple[dict[str, str], ...]:
    return (
        {
            "scenario_id": "root-a-c-forward",
            "root_slot": "a",
            "cwd_kind": "repository",
            "locale": "C",
            "hash_seed": "1",
            "order": "forward",
            "timezone": "UTC",
            "source_date_epoch": "0",
            "noise": "alpha",
        },
        {
            "scenario_id": "root-a-alt-reverse",
            "root_slot": "a",
            "cwd_kind": "external",
            "locale": alternate_locale,
            "hash_seed": "991",
            "order": "reverse",
            "timezone": "Asia/Tokyo",
            "source_date_epoch": "2147483647",
            "noise": "beta",
        },
        {
            "scenario_id": "root-b-alt-forward",
            "root_slot": "b",
            "cwd_kind": "repository-parent",
            "locale": alternate_locale,
            "hash_seed": "130015",
            "order": "forward",
            "timezone": "Europe/Paris",
            "source_date_epoch": "946684800",
            "noise": "gamma",
        },
        {
            "scenario_id": "root-b-c-reverse",
            "root_slot": "b",
            "cwd_kind": "external-nested",
            "locale": "C",
            "hash_seed": "2147483647",
            "order": "reverse",
            "timezone": "America/New_York",
            "source_date_epoch": "123456789",
            "noise": "delta",
        },
    )


def _scenario_cwd(
    scenario: Mapping[str, str], repository_root: Path, scratch_root: Path
) -> Path:
    kind = scenario["cwd_kind"]
    if kind == "repository":
        return repository_root
    if kind == "repository-parent":
        return repository_root.parent
    if kind == "external":
        path = scratch_root / "unrelated-cwd"
    elif kind == "external-nested":
        path = scratch_root / "unrelated cwd" / "nested"
    else:
        raise MatrixFailure(f"unknown cwd kind {kind}")
    path.mkdir(parents=True, exist_ok=True)
    return path


def _run_worker(
    scenario: Mapping[str, str],
    repository_root: Path,
    scratch_root: Path,
    *,
    execute_task014: bool,
) -> dict[str, Any]:
    scenario_scratch = scratch_root / scenario["scenario_id"]
    scenario_scratch.mkdir(parents=True)
    temporary = scenario_scratch / "tmp"
    temporary.mkdir()
    cwd = _scenario_cwd(scenario, repository_root, scenario_scratch)
    environment = dict(os.environ)
    environment.update(
        {
            "PYTHONHASHSEED": scenario["hash_seed"],
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": str(repository_root),
            "LC_ALL": scenario["locale"],
            "LANG": scenario["locale"],
            "TZ": scenario["timezone"],
            "SOURCE_DATE_EPOCH": scenario["source_date_epoch"],
            "TMPDIR": str(temporary),
            "SCHUSS_HARMLESS_ENVIRONMENT_NOISE": scenario["noise"],
        }
    )
    command = [
        sys.executable,
        str(repository_root / "tools/contracts/compiler_determinism_matrix.py"),
        "--worker",
        "--repository-root",
        str(repository_root),
        "--scratch-root",
        str(scenario_scratch),
        "--order",
        scenario["order"],
    ]
    if execute_task014:
        command.append("--execute-task014")
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise MatrixFailure(
            f"matrix cell {scenario['scenario_id']} failed: {detail or 'no diagnostic'}"
        )
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise MatrixFailure(
            f"matrix cell {scenario['scenario_id']} returned invalid JSON"
        ) from exc


def run_matrix(repository_root: Path, task014_execution: str) -> dict[str, Any]:
    repository_root = repository_root.resolve()
    before = parent_semantic_snapshot(repository_root)
    execute_task014, task014_status = _task014_mode(
        repository_root, task014_execution
    )
    scenarios = _scenario_definitions(_alternate_locale())

    with tempfile.TemporaryDirectory(prefix="schuss-compiler-determinism-") as temporary:
        temporary_root = Path(temporary)
        roots = {
            "a": temporary_root / "fresh-root-a" / "repository",
            "b": temporary_root / "fresh root b" / "nested" / "repository",
        }
        for root in roots.values():
            copy_current_tree(
                repository_root,
                root,
                include_task009_capsule=execute_task014,
            )
        results = [
            _run_worker(
                scenario,
                roots[scenario["root_slot"]],
                temporary_root / "scratch",
                execute_task014=execute_task014,
            )
            for scenario in scenarios
        ]

    expected = canonical_bytes(results[0])
    for scenario, result in zip(scenarios[1:], results[1:]):
        if canonical_bytes(result) != expected:
            raise MatrixFailure(
                f"canonical facts differ in matrix cell {scenario['scenario_id']}"
            )
    after = parent_semantic_snapshot(repository_root)
    if before != after:
        raise MatrixFailure("source parent semantic bytes changed during the matrix")

    portable = results[0]
    scenario_summary = [
        {
            key: scenario[key]
            for key in (
                "scenario_id",
                "root_slot",
                "cwd_kind",
                "locale",
                "hash_seed",
                "order",
                "timezone",
                "source_date_epoch",
                "noise",
            )
        }
        for scenario in scenarios
    ]
    return {
        "schema_version": "compiler-determinism-matrix-result-v1",
        "status": "valid",
        "scenario_count": len(scenarios),
        "scenarios": scenario_summary,
        "canonical_facts_equal": True,
        "portable_facts": portable,
        "task014_execution_mode": task014_status,
        "source_parent_semantic_records_unchanged": True,
        "source_parent_semantic_records": before,
        "writes": "temporary-scratch-only",
        "evidence_boundary": {
            "structural": "passed",
            "host_compiled": "passed",
            "arm_compile_link": (
                "passed" if execute_task014 else "not-run"
            ),
            "connected_device": "not-run",
            "real_time": "not-run",
            "audible": "not-run",
        },
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the reusable Tasks 013-015 compiler determinism matrix."
    )
    parser.add_argument(
        "--task014-execution",
        choices=("auto", "require", "skip"),
        default="auto",
        help="run only the authenticated Task 014 handler when its prerequisite is valid",
    )
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--repository-root", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--scratch-root", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--order", choices=("forward", "reverse"), help=argparse.SUPPRESS)
    parser.add_argument("--execute-task014", action="store_true", help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        if arguments.worker:
            if arguments.repository_root is None or arguments.scratch_root is None or arguments.order is None:
                raise MatrixFailure("worker arguments are incomplete")
            result = worker_result(
                arguments.repository_root.resolve(),
                arguments.order,
                arguments.scratch_root.resolve(),
                execute_task014=arguments.execute_task014,
            )
        else:
            result = run_matrix(ROOT, arguments.task014_execution)
    except (MatrixFailure, OSError, ValueError) as exc:
        print(f"compiler-determinism-matrix-error: {exc}", file=sys.stderr)
        return 1
    sys.stdout.buffer.write(canonical_bytes(result) + b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
