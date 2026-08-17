#!/usr/bin/env python3
"""Validate the inert Schuss desktop boundary without writing repository state."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.schuss_core.application_capabilities import (  # noqa: E402
    CAPABILITY_ENTRIES,
    TASK026_CAPABILITY_ENTRIES,
)


APP_ROOT = Path("apps/schuss_desktop")
BOUNDARY = APP_ROOT / "contracts/ui-core-boundary-v1.json"
PACKAGE = APP_ROOT / "package.json"
TSCONFIG = APP_ROOT / "tsconfig.json"
TASK_CONTRACT = Path("docs/tasks/ui-desktop-initialization.md")
BOUNDARY_DOCUMENT = Path("docs/DESKTOP_UI_BOUNDARY.md")

REQUIRED_APP_FILES = {
    Path(".gitignore"),
    Path("README.md"),
    Path("contracts/ui-core-boundary-v1.json"),
    Path("package.json"),
    Path("src-tauri/README.md"),
    Path("src/README.md"),
    Path("tsconfig.json"),
}
GOVERNED_PATHS = tuple(
    sorted(
        [APP_ROOT / path for path in REQUIRED_APP_FILES]
        + [TASK_CONTRACT, BOUNDARY_DOCUMENT],
        key=lambda path: path.as_posix(),
    )
)

EXPECTED_PHASES = (
    (
        "read-only-catalog",
        "planned-not-implemented",
        ("separately-accepted-visual-slice",),
        ("application.describe", "catalog.inspect", "catalog.search"),
    ),
    (
        "graph-visualization",
        "planned-not-implemented",
        ("read-only-catalog-accepted",),
        ("graph.inspect",),
    ),
    (
        "project-mutation-through-shared-operations",
        "gated-not-authorized",
        (
            "explicit-ui-implementation-authorization",
            "graph-visualization-accepted",
            "task-027-accepted-complete",
        ),
        (
            "graph.transact",
            "project.graph.commit",
            "project.history.inspect",
            "project.init",
            "project.inspect",
            "project.profile.fork",
            "project.profile.transact",
            "project.revert",
            "project.validate",
        ),
    ),
)

CAPABILITIES = {
    entry["operation"]: entry
    for entry in (*CAPABILITY_ENTRIES, *TASK026_CAPABILITY_ENTRIES)
}

PRODUCT_SOURCE_SUFFIXES = {
    ".css",
    ".html",
    ".jsx",
    ".rs",
    ".scss",
    ".tsx",
}
RUNTIME_OR_LOCK_NAMES = {
    "Cargo.lock",
    "Cargo.toml",
    "build.rs",
    "bun.lock",
    "bun.lockb",
    "package-lock.json",
    "pnpm-lock.yaml",
    "tauri.conf.json",
    "tauri.conf.json5",
    "yarn.lock",
}
SEMANTIC_DIRECTORY_NAMES = {"catalog", "evidence", "projects", "records", "schemas"}
SEMANTIC_RECORD_NAME = re.compile(
    r"^schuss-(?:build-request|catalog|component|graph|implementation|instrument|project|record-set)-.*\.json$"
)


def stable_json_bytes(value: Any) -> bytes:
    """Return the repository's deterministic readable configuration encoding."""

    return (
        json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True).encode("utf-8")
        + b"\n"
    )


def summary_bytes(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode(
            "utf-8"
        )
        + b"\n"
    )


def _diagnostic(
    diagnostics: list[dict[str, str]], code: str, path: Path | str, detail: str
) -> None:
    diagnostics.append({"code": code, "detail": detail, "path": str(path)})


def _load_json(
    root: Path,
    path: Path,
    diagnostics: list[dict[str, str]],
    *,
    code: str,
) -> Any | None:
    candidate = root / path
    try:
        raw = candidate.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        _diagnostic(diagnostics, code, path, f"cannot load JSON: {error}")
        return None
    if raw != stable_json_bytes(value):
        _diagnostic(
            diagnostics,
            "DESKTOP_CONFIGURATION_ENCODING_INVALID",
            path,
            "JSON must use sorted keys, two-space indentation, and one final LF",
        )
    return value


def _validate_files(root: Path, diagnostics: list[dict[str, str]]) -> tuple[int, int]:
    app_root = root / APP_ROOT
    try:
        files = sorted(
            (path for path in app_root.rglob("*") if path.is_file()),
            key=lambda path: path.as_posix(),
        )
    except OSError as error:
        _diagnostic(
            diagnostics,
            "DESKTOP_APP_ROOT_MISSING",
            APP_ROOT,
            f"cannot inspect application root: {error}",
        )
        return 0, 0

    relative_files = {path.relative_to(app_root) for path in files}
    for missing in sorted(REQUIRED_APP_FILES - relative_files, key=lambda path: path.as_posix()):
        _diagnostic(
            diagnostics,
            "DESKTOP_APP_PATH_MISSING",
            APP_ROOT / missing,
            "required initialization file is absent",
        )
    for unexpected in sorted(relative_files - REQUIRED_APP_FILES, key=lambda path: path.as_posix()):
        _diagnostic(
            diagnostics,
            "DESKTOP_APP_PATH_UNEXPECTED",
            APP_ROOT / unexpected,
            "initialization boundary is closed until a later accepted task",
        )

    semantic_record_count = 0
    for path in files:
        relative = path.relative_to(app_root)
        if path.suffix.lower() in PRODUCT_SOURCE_SUFFIXES or path.name in RUNTIME_OR_LOCK_NAMES:
            _diagnostic(
                diagnostics,
                "DESKTOP_PRODUCT_SOURCE_PRESENT",
                APP_ROOT / relative,
                "product UI, Rust/Tauri runtime, and lockfiles are outside initialization scope",
            )
        semantic_path = bool(SEMANTIC_DIRECTORY_NAMES.intersection(relative.parts))
        semantic_name = bool(SEMANTIC_RECORD_NAME.match(path.name))
        if semantic_path or semantic_name:
            semantic_record_count += 1
            _diagnostic(
                diagnostics,
                "DESKTOP_SEMANTIC_RECORD_OWNERSHIP_INVALID",
                APP_ROOT / relative,
                "the desktop tree may not own catalog, project, schema, evidence, or semantic records",
            )
    return len(files), semantic_record_count


def _validate_package(package: Any, diagnostics: list[dict[str, str]]) -> None:
    if not isinstance(package, dict):
        _diagnostic(diagnostics, "DESKTOP_PACKAGE_INVALID", PACKAGE, "root must be an object")
        return
    expected_keys = {"description", "name", "private", "schuss", "scripts", "type", "version"}
    if set(package) != expected_keys:
        _diagnostic(
            diagnostics,
            "DESKTOP_PACKAGE_INVALID",
            PACKAGE,
            f"top-level keys must be exactly {sorted(expected_keys)}",
        )
    forbidden = {
        "dependencies",
        "devDependencies",
        "optionalDependencies",
        "peerDependencies",
        "packageManager",
        "workspaces",
    }
    present = sorted(forbidden.intersection(package))
    if present:
        _diagnostic(
            diagnostics,
            "DESKTOP_DEPENDENCY_DECLARATION_PRESENT",
            PACKAGE,
            f"dependency or package-manager fields are not allowed: {present}",
        )
    if (
        package.get("name") != "@schuss/desktop"
        or package.get("private") is not True
        or package.get("type") != "module"
        or package.get("version") != "0.0.0"
    ):
        _diagnostic(
            diagnostics,
            "DESKTOP_PACKAGE_INVALID",
            PACKAGE,
            "name, private, type, or inert version metadata drifted",
        )
    if package.get("scripts") != {
        "validate:structure": "python3 ../../tools/contracts/validate_desktop_ui_structure.py"
    }:
        _diagnostic(
            diagnostics,
            "DESKTOP_PACKAGE_SCRIPT_INVALID",
            PACKAGE,
            "only the dependency-free structural validator script is permitted",
        )
    if package.get("schuss") != {
        "applicationBoundary": "apps/schuss_desktop",
        "coreBoundaryContract": "contracts/ui-core-boundary-v1.json",
        "status": "structure-only",
        "targetStack": {
            "language": "TypeScript",
            "shell": "Tauri 2",
            "view": "React",
        },
    }:
        _diagnostic(
            diagnostics,
            "DESKTOP_PACKAGE_BOUNDARY_INVALID",
            PACKAGE,
            "the inert stack and boundary metadata must remain exact",
        )


def _validate_tsconfig(tsconfig: Any, diagnostics: list[dict[str, str]]) -> None:
    if not isinstance(tsconfig, dict) or set(tsconfig) != {"compilerOptions", "include"}:
        _diagnostic(
            diagnostics,
            "DESKTOP_TSCONFIG_INVALID",
            TSCONFIG,
            "configuration must contain only compilerOptions and include",
        )
        return
    expected_options = {
        "allowJs": False,
        "isolatedModules": True,
        "jsx": "react-jsx",
        "lib": ["DOM", "ES2022"],
        "module": "ESNext",
        "moduleResolution": "Bundler",
        "noEmit": True,
        "strict": True,
        "target": "ES2022",
        "verbatimModuleSyntax": True,
    }
    expected_include = ["src/**/*.ts", "src/**/*.tsx", "vite.config.ts"]
    if tsconfig.get("compilerOptions") != expected_options or tsconfig.get("include") != expected_include:
        _diagnostic(
            diagnostics,
            "DESKTOP_TSCONFIG_INVALID",
            TSCONFIG,
            "future TypeScript constraints must remain exact and non-emitting",
        )


def _validate_boundary(boundary: Any, diagnostics: list[dict[str, str]]) -> int:
    if not isinstance(boundary, dict):
        _diagnostic(
            diagnostics, "DESKTOP_CORE_BOUNDARY_INVALID", BOUNDARY, "root must be an object"
        )
        return 0
    expected_keys = {
        "canonical_profile",
        "client",
        "ownership",
        "planned_capability_phases",
        "runtime_capabilities",
        "schema_version",
        "transport",
    }
    if set(boundary) != expected_keys:
        _diagnostic(
            diagnostics,
            "DESKTOP_CORE_BOUNDARY_INVALID",
            BOUNDARY,
            f"top-level keys must be exactly {sorted(expected_keys)}",
        )
    if (
        boundary.get("schema_version") != "schuss-desktop-core-boundary-v1"
        or boundary.get("canonical_profile") != "schuss-canonical-json-v1"
        or boundary.get("runtime_capabilities") != []
    ):
        _diagnostic(
            diagnostics,
            "DESKTOP_RUNTIME_CAPABILITY_INVALID",
            BOUNDARY,
            "v1 must use canonical Schuss JSON and expose zero runtime capabilities",
        )

    if boundary.get("client") != {
        "application_path": "apps/schuss_desktop",
        "client_id": "schuss-desktop",
        "intended_stack": {
            "language": "TypeScript",
            "shell": "Tauri 2",
            "view": "React",
        },
        "status": "structure-only",
    }:
        _diagnostic(
            diagnostics,
            "DESKTOP_CLIENT_METADATA_INVALID",
            BOUNDARY,
            "client identity, path, intended stack, and structure-only status must remain exact",
        )

    ownership = boundary.get("ownership")
    if not isinstance(ownership, dict) or any(
        ownership.get(field) != "forbidden"
        for field in (
            "direct_catalog_file_access",
            "direct_semantic_json_access",
            "direct_workspace_mutation",
        )
    ) or ownership.get("semantic_mutation_mode") != "shared-operation-only-after-authorization":
        _diagnostic(
            diagnostics,
            "DESKTOP_SEMANTIC_OWNERSHIP_INVALID",
            BOUNDARY,
            "semantic reads and writes must stay behind authorized shared operations",
        )

    transport = boundary.get("transport")
    expected_transport = {
        "canonical_result_handling": "consume-unchanged",
        "operation_selection": "closed-listed-allowlist",
        "request_handling": "submit-one-versioned-schuss-operation",
        "status": "not-implemented",
        "unknown_operation": "reject",
        "unknown_result_schema": "reject",
        "version_mismatch": "reject",
    }
    if transport != expected_transport:
        _diagnostic(
            diagnostics,
            "DESKTOP_TRANSPORT_BOUNDARY_INVALID",
            BOUNDARY,
            "transport must remain unimplemented, canonical, closed, and fail-closed",
        )

    phases = boundary.get("planned_capability_phases")
    if not isinstance(phases, list) or len(phases) != len(EXPECTED_PHASES):
        _diagnostic(
            diagnostics,
            "DESKTOP_CAPABILITY_PLAN_INVALID",
            BOUNDARY,
            "planned phases are absent or have unexpected cardinality",
        )
        return 0

    observed_operations: list[str] = []
    for phase, expected in zip(phases, EXPECTED_PHASES):
        phase_name, status, prerequisites, operation_names = expected
        if not isinstance(phase, dict):
            _diagnostic(
                diagnostics,
                "DESKTOP_CAPABILITY_PLAN_INVALID",
                BOUNDARY,
                f"phase {phase_name} must be an object",
            )
            continue
        operations = phase.get("operations")
        observed_names = (
            tuple(item.get("operation") for item in operations if isinstance(item, dict))
            if isinstance(operations, list)
            else ()
        )
        if (
            set(phase) != {"operations", "phase", "prerequisites", "status"}
            or phase.get("phase") != phase_name
            or phase.get("status") != status
            or tuple(phase.get("prerequisites", ())) != prerequisites
            or observed_names != operation_names
            or not isinstance(operations, list)
            or len(operations) != len(operation_names)
        ):
            _diagnostic(
                diagnostics,
                "DESKTOP_CAPABILITY_PLAN_INVALID",
                BOUNDARY,
                f"phase {phase_name} does not match the closed initialization plan",
            )
        if not isinstance(operations, list):
            continue
        for item in operations:
            if not isinstance(item, dict):
                continue
            operation = item.get("operation")
            if isinstance(operation, str):
                observed_operations.append(operation)
            capability = CAPABILITIES.get(operation)
            if capability is None:
                _diagnostic(
                    diagnostics,
                    "DESKTOP_OPERATION_NOT_SHARED",
                    BOUNDARY,
                    f"{operation!r} is not in the shared Schuss capability registry",
                )
                continue
            expected_item = {
                "effect_class": capability["effect_class"],
                "operation": operation,
                "request_schema_version": capability["request_schema_version"],
                "result_schema_version": capability["result_schema_version"],
            }
            if item != expected_item:
                _diagnostic(
                    diagnostics,
                    "DESKTOP_OPERATION_METADATA_DRIFT",
                    BOUNDARY,
                    f"{operation} must retain the shared request/result/effect metadata",
                )
    if len(observed_operations) != len(set(observed_operations)):
        _diagnostic(
            diagnostics,
            "DESKTOP_OPERATION_DUPLICATE",
            BOUNDARY,
            "one shared operation may appear in only one planned phase",
        )
    return len(observed_operations)


def _validate_documents(root: Path, diagnostics: list[dict[str, str]]) -> None:
    required_fragments = {
        TASK_CONTRACT: (
            "Status: accepted and complete on 2026-08-17 at structural level only.",
            "It is not Task 028",
            "## Goal and why it exists",
            "## In scope",
            "## Out of scope",
            "## Inputs and deliverables",
            "## Acceptance tests",
            "## Validation cadence",
            "## Decisions this task may make",
            "## Decisions this task must not make",
            "The repository-wide contract aggregate is therefore explicitly not green.",
            "No desktop-initialization or adjacent-governance test failed.",
            "does not produce a runnable desktop application",
        ),
        BOUNDARY_DOCUMENT: (
            "Status: unnumbered structural initialization complete; product UI not started.",
            "existing Schuss Python core and its versioned operations remain the sole",
            "Read-only catalog browsing",
            "Graph visualization",
            "Project mutation through existing operations",
            "This initialization is not Task 028.",
        ),
        APP_ROOT / "README.md": (
            "Status: structure-only initialization; no desktop application is implemented.",
            "must never edit catalog files,",
            "semantic JSON records, or project workspace files directly.",
        ),
    }
    for path, fragments in required_fragments.items():
        try:
            text = (root / path).read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            _diagnostic(
                diagnostics,
                "DESKTOP_DOCUMENT_MISSING",
                path,
                f"cannot load required document: {error}",
            )
            continue
        normalized = " ".join(text.split())
        for fragment in fragments:
            if fragment not in normalized:
                _diagnostic(
                    diagnostics,
                    "DESKTOP_DOCUMENT_BOUNDARY_INVALID",
                    path,
                    f"missing required assertion: {fragment}",
                )


def validate_structure(root: Path = ROOT) -> dict[str, Any]:
    """Return a deterministic summary for one repository root."""

    diagnostics: list[dict[str, str]] = []
    file_count, semantic_record_count = _validate_files(root, diagnostics)
    package = _load_json(root, PACKAGE, diagnostics, code="DESKTOP_PACKAGE_INVALID")
    tsconfig = _load_json(root, TSCONFIG, diagnostics, code="DESKTOP_TSCONFIG_INVALID")
    boundary = _load_json(root, BOUNDARY, diagnostics, code="DESKTOP_CORE_BOUNDARY_INVALID")
    if package is not None:
        _validate_package(package, diagnostics)
    if tsconfig is not None:
        _validate_tsconfig(tsconfig, diagnostics)
    planned_operation_count = 0
    if boundary is not None:
        planned_operation_count = _validate_boundary(boundary, diagnostics)
    _validate_documents(root, diagnostics)

    diagnostics.sort(key=lambda item: (item["code"], item["path"], item["detail"]))
    return {
        "application_path": APP_ROOT.as_posix(),
        "boundary_schema_version": (
            boundary.get("schema_version") if isinstance(boundary, dict) else None
        ),
        "diagnostics": diagnostics,
        "file_count": file_count,
        "planned_operation_count": planned_operation_count,
        "runtime_capability_count": (
            len(boundary.get("runtime_capabilities", []))
            if isinstance(boundary, dict)
            and isinstance(boundary.get("runtime_capabilities"), list)
            else None
        ),
        "schema_version": "schuss-desktop-ui-structure-validation-v1",
        "semantic_record_count": semantic_record_count,
        "status": "valid" if not diagnostics else "invalid",
    }


def main() -> int:
    summary = validate_structure()
    stream = sys.stdout.buffer if summary["status"] == "valid" else sys.stderr.buffer
    stream.write(summary_bytes(summary))
    return 0 if summary["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
