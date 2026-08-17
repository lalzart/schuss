#!/usr/bin/env python3
"""Validate the runnable read-only Schuss desktop boundary without writing state."""

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
PACKAGE_LOCK = APP_ROOT / "package-lock.json"
TSCONFIG = APP_ROOT / "tsconfig.json"
TAURI_CONFIG = APP_ROOT / "src-tauri/tauri.conf.json"
TAURI_CAPABILITY = APP_ROOT / "src-tauri/capabilities/default.json"
TASK_CONTRACT = Path("docs/tasks/ui-desktop-read-only-catalog.md")
INITIALIZATION_CONTRACT = Path("docs/tasks/ui-desktop-initialization.md")
BOUNDARY_DOCUMENT = Path("docs/DESKTOP_UI_BOUNDARY.md")

REQUIRED_APP_FILES = {
    Path(".gitignore"),
    Path("README.md"),
    Path("bridge/read_only_catalog_bridge.py"),
    Path("contracts/ui-core-boundary-v1.json"),
    Path("index.html"),
    Path("package-lock.json"),
    Path("package.json"),
    Path("src-tauri/Cargo.lock"),
    Path("src-tauri/Cargo.toml"),
    Path("src-tauri/app-icon.svg"),
    Path("src-tauri/build.rs"),
    Path("src-tauri/capabilities/default.json"),
    Path("src-tauri/icons/512x512.png"),
    Path("src-tauri/README.md"),
    Path("src-tauri/src/lib.rs"),
    Path("src-tauri/src/main.rs"),
    Path("src-tauri/src/read_only_bridge.rs"),
    Path("src-tauri/tauri.conf.json"),
    Path("src/App.module.css"),
    Path("src/App.tsx"),
    Path("src/components/CatalogBrowser.module.css"),
    Path("src/components/CatalogBrowser.test.tsx"),
    Path("src/components/CatalogBrowser.tsx"),
    Path("src/components/CatalogDetail.tsx"),
    Path("src/components/CatalogList.tsx"),
    Path("src/components/StatusBadge.tsx"),
    Path("src/core/bridge.ts"),
    Path("src/core/requests.test.ts"),
    Path("src/core/requests.ts"),
    Path("src/core/types.ts"),
    Path("src/hooks/useDebouncedValue.ts"),
    Path("src/main.tsx"),
    Path("src/README.md"),
    Path("src/styles/global.css"),
    Path("src/styles/tokens.css"),
    Path("tsconfig.json"),
    Path("vite.config.ts"),
    Path("vitest.config.ts"),
    Path("vitest.setup.ts"),
}
GOVERNED_PATHS = tuple(
    sorted(
        [APP_ROOT / path for path in REQUIRED_APP_FILES]
        + [TASK_CONTRACT, INITIALIZATION_CONTRACT, BOUNDARY_DOCUMENT],
        key=lambda path: path.as_posix(),
    )
)

IGNORED_DIRECTORY_NAMES = {
    "__pycache__",
    "coverage",
    "dist",
    "gen",
    "node_modules",
    "target",
}
SEMANTIC_DIRECTORY_NAMES = {"catalog", "evidence", "projects", "records", "schemas"}
SEMANTIC_RECORD_NAME = re.compile(
    r"^schuss-(?:build-request|catalog|component|graph|implementation|instrument|project|record-set)-.*\.json$"
)

EXPECTED_PHASES = (
    (
        "read-only-catalog",
        "implemented-read-only",
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
EXPECTED_RUNTIME_OPERATIONS = (
    "application.describe",
    "catalog.inspect",
    "catalog.search",
)
CAPABILITIES = {
    entry["operation"]: entry
    for entry in (*CAPABILITY_ENTRIES, *TASK026_CAPABILITY_ENTRIES)
}

EXPECTED_DEPENDENCIES = {
    "@radix-ui/react-scroll-area": "1.2.18",
    "@radix-ui/react-tabs": "1.1.21",
    "@radix-ui/react-tooltip": "1.2.16",
    "@tauri-apps/api": "2.11.1",
    "react": "19.2.8",
    "react-dom": "19.2.8",
}
EXPECTED_DEV_DEPENDENCIES = {
    "@tauri-apps/cli": "2.11.4",
    "@testing-library/jest-dom": "7.0.1",
    "@testing-library/react": "16.3.2",
    "@testing-library/user-event": "14.6.4",
    "@types/node": "26.2.0",
    "@types/react": "19.2.18",
    "@types/react-dom": "19.2.4",
    "@vitejs/plugin-react": "6.0.5",
    "jsdom": "30.0.1",
    "typescript": "7.0.2",
    "vite": "8.2.1",
    "vitest": "4.1.10",
}
EXPECTED_SCRIPTS = {
    "build": "tsc && vite build",
    "dev": "tauri dev",
    "dev:web": "vite",
    "test": "vitest run",
    "test:watch": "vitest",
    "validate:structure": "python3 ../../tools/contracts/validate_desktop_ui_structure.py",
}


def stable_json_bytes(value: Any) -> bytes:
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
    require_stable_encoding: bool = True,
) -> Any | None:
    candidate = root / path
    try:
        raw = candidate.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        _diagnostic(diagnostics, code, path, f"cannot load JSON: {error}")
        return None
    if require_stable_encoding and raw != stable_json_bytes(value):
        _diagnostic(
            diagnostics,
            "DESKTOP_CONFIGURATION_ENCODING_INVALID",
            path,
            "JSON must use sorted keys, two-space indentation, and one final LF",
        )
    return value


def _source_files(app_root: Path) -> list[Path]:
    return sorted(
        (
            path
            for path in app_root.rglob("*")
            if path.is_file()
            and not IGNORED_DIRECTORY_NAMES.intersection(
                path.relative_to(app_root).parts
            )
        ),
        key=lambda path: path.as_posix(),
    )


def _validate_files(root: Path, diagnostics: list[dict[str, str]]) -> tuple[int, int]:
    app_root = root / APP_ROOT
    try:
        files = _source_files(app_root)
    except OSError as error:
        _diagnostic(
            diagnostics,
            "DESKTOP_APP_ROOT_MISSING",
            APP_ROOT,
            f"cannot inspect application root: {error}",
        )
        return 0, 0

    relative_files = {path.relative_to(app_root) for path in files}
    for missing in sorted(
        REQUIRED_APP_FILES - relative_files, key=lambda path: path.as_posix()
    ):
        _diagnostic(
            diagnostics,
            "DESKTOP_APP_PATH_MISSING",
            APP_ROOT / missing,
            "required read-only desktop file is absent",
        )
    for unexpected in sorted(
        relative_files - REQUIRED_APP_FILES, key=lambda path: path.as_posix()
    ):
        _diagnostic(
            diagnostics,
            "DESKTOP_APP_PATH_UNEXPECTED",
            APP_ROOT / unexpected,
            "the read-only application boundary is closed until a later accepted task",
        )

    semantic_record_count = 0
    for path in files:
        relative = path.relative_to(app_root)
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
    expected_keys = {
        "dependencies",
        "description",
        "devDependencies",
        "name",
        "private",
        "schuss",
        "scripts",
        "type",
        "version",
    }
    if set(package) != expected_keys:
        _diagnostic(
            diagnostics,
            "DESKTOP_PACKAGE_INVALID",
            PACKAGE,
            f"top-level keys must be exactly {sorted(expected_keys)}",
        )
    if (
        package.get("name") != "@schuss/desktop"
        or package.get("private") is not True
        or package.get("type") != "module"
        or package.get("version") != "0.0.0"
        or package.get("dependencies") != EXPECTED_DEPENDENCIES
        or package.get("devDependencies") != EXPECTED_DEV_DEPENDENCIES
        or package.get("scripts") != EXPECTED_SCRIPTS
    ):
        _diagnostic(
            diagnostics,
            "DESKTOP_PACKAGE_INVALID",
            PACKAGE,
            "identity, exact dependencies, or executable scripts drifted",
        )
    if package.get("schuss") != {
        "applicationBoundary": "apps/schuss_desktop",
        "coreBoundaryContract": "contracts/ui-core-boundary-v1.json",
        "recordSet": "schuss-record-set-000021@1",
        "status": "read-only-catalog",
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
            "the exact stack, record set, and read-only boundary metadata must remain fixed",
        )


def _validate_package_lock(lock: Any, diagnostics: list[dict[str, str]]) -> None:
    if not isinstance(lock, dict) or lock.get("lockfileVersion") != 3:
        _diagnostic(
            diagnostics,
            "DESKTOP_PACKAGE_LOCK_INVALID",
            PACKAGE_LOCK,
            "npm package lock v3 is required",
        )
        return
    root_package = lock.get("packages", {}).get("")
    if not isinstance(root_package, dict) or (
        root_package.get("dependencies") != EXPECTED_DEPENDENCIES
        or root_package.get("devDependencies") != EXPECTED_DEV_DEPENDENCIES
    ):
        _diagnostic(
            diagnostics,
            "DESKTOP_PACKAGE_LOCK_INVALID",
            PACKAGE_LOCK,
            "lockfile root dependencies must match the exact reviewed package boundary",
        )


def _validate_tsconfig(tsconfig: Any, diagnostics: list[dict[str, str]]) -> None:
    expected = {
        "compilerOptions": {
            "allowJs": False,
            "allowSyntheticDefaultImports": True,
            "isolatedModules": True,
            "jsx": "react-jsx",
            "lib": ["DOM", "DOM.Iterable", "ES2022"],
            "module": "ESNext",
            "moduleResolution": "Bundler",
            "noEmit": True,
            "strict": True,
            "target": "ES2022",
            "types": ["vite/client", "vitest/globals"],
            "verbatimModuleSyntax": True,
        },
        "include": [
            "src/**/*.ts",
            "src/**/*.tsx",
            "vite.config.ts",
            "vitest.config.ts",
            "vitest.setup.ts",
        ],
    }
    if tsconfig != expected:
        _diagnostic(
            diagnostics,
            "DESKTOP_TSCONFIG_INVALID",
            TSCONFIG,
            "strict renderer and build configuration drifted",
        )


def _operation_metadata(operation: str) -> dict[str, str] | None:
    capability = CAPABILITIES.get(operation)
    if capability is None:
        return None
    return {
        "effect_class": capability["effect_class"],
        "operation": operation,
        "request_schema_version": capability["request_schema_version"],
        "result_schema_version": capability["result_schema_version"],
    }


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
    if set(boundary) != expected_keys or (
        boundary.get("schema_version") != "schuss-desktop-core-boundary-v1"
        or boundary.get("canonical_profile") != "schuss-canonical-json-v1"
    ):
        _diagnostic(
            diagnostics,
            "DESKTOP_CORE_BOUNDARY_INVALID",
            BOUNDARY,
            "desktop boundary identity or top-level shape drifted",
        )

    if boundary.get("client") != {
        "application_path": "apps/schuss_desktop",
        "client_id": "schuss-desktop",
        "intended_stack": {
            "language": "TypeScript",
            "shell": "Tauri 2",
            "view": "React",
        },
        "status": "read-only-catalog",
    }:
        _diagnostic(
            diagnostics,
            "DESKTOP_CLIENT_METADATA_INVALID",
            BOUNDARY,
            "client identity and read-only status must remain exact",
        )

    ownership = boundary.get("ownership")
    if not isinstance(ownership, dict) or any(
        ownership.get(field) != "forbidden"
        for field in (
            "direct_catalog_file_access",
            "direct_renderer_process_access",
            "direct_semantic_json_access",
            "direct_workspace_mutation",
        )
    ) or ownership.get("semantic_mutation_mode") != "shared-operation-only-after-authorization":
        _diagnostic(
            diagnostics,
            "DESKTOP_SEMANTIC_OWNERSHIP_INVALID",
            BOUNDARY,
            "semantic state and process access must remain behind shared operations",
        )

    expected_transport = {
        "adapter": "tauri-command-to-persistent-python-core",
        "canonical_result_handling": "consume-unchanged",
        "command": "dispatch_read_only_operation",
        "development_verification": "vite-local-read-only-proxy",
        "operation_selection": "closed-listed-allowlist",
        "renderer_file_access": "absent",
        "request_handling": "submit-one-versioned-schuss-operation",
        "selected_record_set": "contracts/record-sets/task028-direct-palette-v1.json",
        "status": "implemented-read-only",
        "unknown_operation": "reject",
        "unknown_result_schema": "reject",
        "version_mismatch": "reject",
    }
    if boundary.get("transport") != expected_transport:
        _diagnostic(
            diagnostics,
            "DESKTOP_TRANSPORT_BOUNDARY_INVALID",
            BOUNDARY,
            "transport must remain local, canonical, exact-context, and fail-closed",
        )

    runtime = boundary.get("runtime_capabilities")
    observed_runtime = (
        tuple(item.get("operation") for item in runtime if isinstance(item, dict))
        if isinstance(runtime, list)
        else ()
    )
    if observed_runtime != EXPECTED_RUNTIME_OPERATIONS:
        _diagnostic(
            diagnostics,
            "DESKTOP_RUNTIME_CAPABILITY_INVALID",
            BOUNDARY,
            "runtime allowlist must contain exactly the three read-only catalog routes",
        )
    if isinstance(runtime, list):
        for item in runtime:
            if not isinstance(item, dict):
                continue
            expected = _operation_metadata(item.get("operation"))
            if expected is None or item != expected or item.get("effect_class") != "read-only":
                _diagnostic(
                    diagnostics,
                    "DESKTOP_RUNTIME_CAPABILITY_INVALID",
                    BOUNDARY,
                    "runtime operation metadata must match the shared capability registry",
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
    for phase, expected_phase in zip(phases, EXPECTED_PHASES):
        phase_name, status, prerequisites, operation_names = expected_phase
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
        ):
            _diagnostic(
                diagnostics,
                "DESKTOP_CAPABILITY_PLAN_INVALID",
                BOUNDARY,
                f"phase {phase_name} does not match the closed UI sequence",
            )
        if not isinstance(operations, list):
            continue
        for item in operations:
            if not isinstance(item, dict):
                continue
            operation = item.get("operation")
            if isinstance(operation, str):
                observed_operations.append(operation)
            expected = _operation_metadata(operation)
            if expected is None:
                _diagnostic(
                    diagnostics,
                    "DESKTOP_OPERATION_NOT_SHARED",
                    BOUNDARY,
                    f"{operation!r} is not in the shared capability registry",
                )
            elif item != expected:
                _diagnostic(
                    diagnostics,
                    "DESKTOP_OPERATION_METADATA_DRIFT",
                    BOUNDARY,
                    f"{operation} must retain shared request/result/effect metadata",
                )
    if len(observed_operations) != len(set(observed_operations)):
        _diagnostic(
            diagnostics,
            "DESKTOP_OPERATION_DUPLICATE",
            BOUNDARY,
            "one shared operation may appear in only one capability phase",
        )
    return len(observed_operations)


def _validate_tauri(root: Path, config: Any, capability: Any, diagnostics: list[dict[str, str]]) -> None:
    if not isinstance(config, dict) or config.get("identifier") != "org.schuss.desktop":
        _diagnostic(
            diagnostics,
            "DESKTOP_TAURI_CONFIG_INVALID",
            TAURI_CONFIG,
            "Tauri application identity is absent or invalid",
        )
    else:
        app = config.get("app", {})
        build = config.get("build", {})
        bundle = config.get("bundle", {})
        if (
            app.get("withGlobalTauri") is not False
            or build.get("devUrl") != "http://127.0.0.1:1420"
            or build.get("frontendDist") != "../dist"
            or bundle.get("active") is not False
        ):
            _diagnostic(
                diagnostics,
                "DESKTOP_TAURI_CONFIG_INVALID",
                TAURI_CONFIG,
                "local shell, non-global API, and packaging-disabled boundary drifted",
            )
    if not isinstance(capability, dict) or capability.get("permissions") != ["core:default"]:
        _diagnostic(
            diagnostics,
            "DESKTOP_TAURI_PERMISSION_INVALID",
            TAURI_CAPABILITY,
            "only Tauri core defaults are permitted; no plugin capability is authorized",
        )

    text_paths = (
        APP_ROOT / "src/core/bridge.ts",
        APP_ROOT / "src-tauri/src/read_only_bridge.rs",
        APP_ROOT / "bridge/read_only_catalog_bridge.py",
    )
    combined = ""
    for path in text_paths:
        try:
            source = (root / path).read_text(encoding="utf-8")
            if path.name == "read_only_bridge.rs":
                source = source.split("#[cfg(test)]", 1)[0]
            combined += source + "\n"
        except (OSError, UnicodeError) as error:
            _diagnostic(
                diagnostics,
                "DESKTOP_BRIDGE_SOURCE_MISSING",
                path,
                f"cannot read bridge source: {error}",
            )
    forbidden_fragments = (
        "@tauri-apps/plugin-fs",
        "@tauri-apps/plugin-shell",
        "@tauri-apps/plugin-http",
        "graph.transact\"",
        "build.execute\"",
        "project.profile.transact\"",
    )
    for fragment in forbidden_fragments:
        if fragment in combined:
            _diagnostic(
                diagnostics,
                "DESKTOP_BRIDGE_FORBIDDEN_CAPABILITY",
                APP_ROOT,
                f"bridge contains forbidden runtime capability {fragment!r}",
            )


def _validate_documents(root: Path, diagnostics: list[dict[str, str]]) -> None:
    required_fragments = {
        TASK_CONTRACT: (
            "Status: accepted by explicit user authorization and complete locally on",
            "2026-08-17 at the read-only host/UI boundary.",
            "## Goal and why it exists",
            "## In scope",
            "## Out of scope",
            "## Inputs and deliverables",
            "## Acceptance tests",
            "## Validation cadence",
            "## Decisions this task may make",
            "## Decisions this task must not make",
            "## Completion boundary",
        ),
        INITIALIZATION_CONTRACT: (
            "Status: accepted and complete on 2026-08-17 at structural level only.",
            "Each later slice requires its own accepted boundary",
        ),
        BOUNDARY_DOCUMENT: (
            "Schuss core remains the authority",
            "application.describe",
            "catalog.search",
            "catalog.inspect",
            "Graph visualization",
            "Project mutation through existing operations",
        ),
        APP_ROOT / "README.md": (
            "Read-only catalog",
            "npm run dev",
            "must never edit catalog files",
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
    diagnostics: list[dict[str, str]] = []
    file_count, semantic_record_count = _validate_files(root, diagnostics)
    package = _load_json(root, PACKAGE, diagnostics, code="DESKTOP_PACKAGE_INVALID")
    package_lock = _load_json(
        root,
        PACKAGE_LOCK,
        diagnostics,
        code="DESKTOP_PACKAGE_LOCK_INVALID",
        require_stable_encoding=False,
    )
    tsconfig = _load_json(root, TSCONFIG, diagnostics, code="DESKTOP_TSCONFIG_INVALID")
    boundary = _load_json(root, BOUNDARY, diagnostics, code="DESKTOP_CORE_BOUNDARY_INVALID")
    tauri_config = _load_json(
        root, TAURI_CONFIG, diagnostics, code="DESKTOP_TAURI_CONFIG_INVALID"
    )
    capability = _load_json(
        root, TAURI_CAPABILITY, diagnostics, code="DESKTOP_TAURI_PERMISSION_INVALID"
    )
    if package is not None:
        _validate_package(package, diagnostics)
    if package_lock is not None:
        _validate_package_lock(package_lock, diagnostics)
    if tsconfig is not None:
        _validate_tsconfig(tsconfig, diagnostics)
    planned_operation_count = 0
    if boundary is not None:
        planned_operation_count = _validate_boundary(boundary, diagnostics)
    _validate_tauri(root, tauri_config, capability, diagnostics)
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
        "schema_version": "schuss-desktop-ui-structure-validation-v2",
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
