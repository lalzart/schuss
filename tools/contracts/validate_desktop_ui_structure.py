#!/usr/bin/env python3
"""Validate the closed Schuss desktop authoring/build/device boundary."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = Path("apps/schuss_desktop")
BOUNDARY = APP_ROOT / "contracts/ui-core-boundary-v1.json"
PACKAGE = APP_ROOT / "package.json"
PACKAGE_LOCK = APP_ROOT / "package-lock.json"
TAURI_CAPABILITY = APP_ROOT / "src-tauri/capabilities/default.json"
TASK_CONTRACT = Path("docs/tasks/ui-desktop-patcher-authoring.md")
PERFORMANCE_TASK_CONTRACT = Path("docs/tasks/ui-desktop-authoring-performance.md")
BUILD_DEVICE_TASK_CONTRACT = Path("docs/tasks/ui-desktop-build-device-workflow.md")
PROJECT_OBJECT_TASK_CONTRACT = Path("docs/tasks/ui-desktop-project-object-handoff.md")
WORKSPACE_SHELL_TASK_CONTRACT = Path("docs/tasks/ui-desktop-workspace-shell.md")
BOUNDARY_DOCUMENT = Path("docs/DESKTOP_UI_BOUNDARY.md")

REQUIRED_APP_FILES = {
    Path(value)
    for value in (
        ".gitignore",
        "README.md",
        "bridge/desktop_core_bridge.py",
        "contracts/ui-core-boundary-v1.json",
        "index.html",
        "package-lock.json",
        "package.json",
        "src-tauri/Cargo.lock",
        "src-tauri/Cargo.toml",
        "src-tauri/README.md",
        "src-tauri/app-icon.svg",
        "src-tauri/build.rs",
        "src-tauri/capabilities/default.json",
        "src-tauri/icons/512x512.png",
        "src-tauri/src/desktop_bridge.rs",
        "src-tauri/src/lib.rs",
        "src-tauri/src/main.rs",
        "src-tauri/tauri.conf.json",
        "src/App.module.css",
        "src/App.test.tsx",
        "src/App.tsx",
        "src/README.md",
        "src/components/DesktopApp.module.css",
        "src/components/DesktopApp.test.tsx",
        "src/components/DesktopApp.tsx",
        "src/components/ObjectLibrary.module.css",
        "src/components/ObjectLibrary.test.tsx",
        "src/components/ObjectLibrary.tsx",
        "src/components/PatchEditor.module.css",
        "src/components/PatchEditor.test.tsx",
        "src/components/PatchEditor.tsx",
        "src/components/PatchNode.module.css",
        "src/components/PatchNode.tsx",
        "src/core/bridge.ts",
        "src/core/desktopPreferences.ts",
        "src/core/desktopPreferences.test.ts",
        "src/core/patcherRequests.test.ts",
        "src/core/patcherRequests.ts",
        "src/core/requests.test.ts",
        "src/core/requests.ts",
        "src/core/types.ts",
        "src/hooks/useDebouncedValue.ts",
        "src/main.tsx",
        "src/styles/global.css",
        "src/styles/tokens.css",
        "tsconfig.json",
        "vite.config.ts",
        "vitest.config.ts",
        "vitest.setup.ts",
    )
}
GOVERNED_PATHS = tuple(
    sorted(
        [APP_ROOT / path for path in REQUIRED_APP_FILES]
        + [TASK_CONTRACT, PERFORMANCE_TASK_CONTRACT, BUILD_DEVICE_TASK_CONTRACT, PROJECT_OBJECT_TASK_CONTRACT, WORKSPACE_SHELL_TASK_CONTRACT, BOUNDARY_DOCUMENT],
        key=lambda path: path.as_posix(),
    )
)
IGNORED = {"__pycache__", "dist", "gen", "node_modules", "target"}
SEMANTIC_DIRECTORIES = {"catalog", "evidence", "projects", "records", "schemas"}
SEMANTIC_RECORD_NAME = re.compile(
    r"^schuss-(?:build-request|catalog|component|graph|implementation|instrument|project|record-set)-.*\.json$"
)
EXPECTED_RUNTIME = (
    "build.session.start",
    "build.session.inspect",
    "application.describe",
    "device.session.discover",
    "device.session.inspect",
    "device.upload.start",
    "device.upload.inspect",
    "catalog.implementations.search",
    "catalog.inspect",
    "catalog.search",
    "component.inspect",
    "graph.inspect",
    "graph.transact",
    "project.history.inspect",
    "project.init",
    "project.inspect",
    "project.object.inspect",
    "project.objects.list",
    "project.profile.fork",
    "project.profile.transact",
    "project.revert",
    "project.validate",
    "workspace.project.create",
    "workspace.projects.list",
)
EXPECTED_DEPENDENCIES = {
    "@radix-ui/react-scroll-area": "1.2.18",
    "@radix-ui/react-tabs": "1.1.21",
    "@radix-ui/react-tooltip": "1.2.16",
    "@tauri-apps/api": "2.11.1",
    "@xyflow/react": "12.11.3",
    "react": "19.2.8",
    "react-dom": "19.2.8",
}


def stable_json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True).encode("utf-8") + b"\n"


def _diagnostic(items: list[dict[str, str]], code: str, path: Path, detail: str) -> None:
    items.append({"code": code, "detail": detail, "path": path.as_posix()})


def _load(root: Path, path: Path, items: list[dict[str, str]]) -> Any | None:
    try:
        return json.loads((root / path).read_bytes())
    except (OSError, json.JSONDecodeError, UnicodeError) as error:
        _diagnostic(items, "DESKTOP_CONFIGURATION_INVALID", path, str(error))
        return None


def _source_files(app_root: Path) -> list[Path]:
    return sorted(
        (
            path
            for path in app_root.rglob("*")
            if path.is_file()
            and not IGNORED.intersection(path.relative_to(app_root).parts)
        ),
        key=lambda path: path.as_posix(),
    )


def validate_structure(root: Path) -> dict[str, Any]:
    diagnostics: list[dict[str, str]] = []
    app_root = root / APP_ROOT
    files = _source_files(app_root) if app_root.is_dir() else []
    observed = {path.relative_to(app_root) for path in files}
    for path in sorted(REQUIRED_APP_FILES - observed, key=lambda value: value.as_posix()):
        _diagnostic(diagnostics, "DESKTOP_APP_PATH_MISSING", APP_ROOT / path, "required desktop file is absent")
    for path in sorted(observed - REQUIRED_APP_FILES, key=lambda value: value.as_posix()):
        _diagnostic(diagnostics, "DESKTOP_APP_PATH_UNEXPECTED", APP_ROOT / path, "desktop application boundary is closed")

    semantic_count = 0
    for path in files:
        relative = path.relative_to(app_root)
        if SEMANTIC_DIRECTORIES.intersection(relative.parts) or SEMANTIC_RECORD_NAME.match(path.name):
            semantic_count += 1
            _diagnostic(diagnostics, "DESKTOP_SEMANTIC_RECORD_OWNERSHIP_INVALID", APP_ROOT / relative, "renderer may not own semantic records")

    package = _load(root, PACKAGE, diagnostics)
    if not isinstance(package, dict) or package.get("dependencies") != EXPECTED_DEPENDENCIES or package.get("schuss", {}).get("recordSet") != "schuss-record-set-000028@1" or package.get("schuss", {}).get("status") != "workspace-patcher-shell":
        _diagnostic(diagnostics, "DESKTOP_PACKAGE_INVALID", PACKAGE, "desktop dependency or boundary metadata drifted")
    lock = _load(root, PACKAGE_LOCK, diagnostics)
    if not isinstance(lock, dict) or lock.get("packages", {}).get("", {}).get("dependencies") != EXPECTED_DEPENDENCIES:
        _diagnostic(diagnostics, "DESKTOP_PACKAGE_LOCK_INVALID", PACKAGE_LOCK, "lockfile root dependencies drifted")

    boundary = _load(root, BOUNDARY, diagnostics)
    runtime_count = 0
    planned_count = 0
    if not isinstance(boundary, dict) or boundary.get("schema_version") != "schuss-desktop-core-boundary-v1" or boundary.get("client", {}).get("status") != "workspace-patcher-shell":
        _diagnostic(diagnostics, "DESKTOP_CORE_BOUNDARY_INVALID", BOUNDARY, "desktop workflow boundary identity drifted")
    else:
        runtime = boundary.get("runtime_capabilities")
        operations = tuple(item.get("operation") for item in runtime if isinstance(item, dict)) if isinstance(runtime, list) else ()
        runtime_count = len(operations)
        if operations != EXPECTED_RUNTIME:
            _diagnostic(diagnostics, "DESKTOP_RUNTIME_CAPABILITY_INVALID", BOUNDARY, "desktop operation allowlist drifted")
        phases = boundary.get("planned_capability_phases")
        if isinstance(phases, list):
            planned_count = sum(len(item.get("operations", [])) for item in phases if isinstance(item, dict))
        transport = boundary.get("transport", {})
        if transport.get("command") != "dispatch_desktop_operation" or transport.get("selected_record_set") != "contracts/record-sets/ui-desktop-workspace-shell-v1.json":
            _diagnostic(diagnostics, "DESKTOP_TRANSPORT_BOUNDARY_INVALID", BOUNDARY, "desktop transport or exact record set drifted")
        ownership = boundary.get("ownership", {})
        if any(ownership.get(key) != "forbidden" for key in ("direct_catalog_file_access", "direct_renderer_process_access", "direct_semantic_json_access", "direct_workspace_mutation")):
            _diagnostic(diagnostics, "DESKTOP_SEMANTIC_OWNERSHIP_INVALID", BOUNDARY, "renderer semantic ownership drifted")

    capability = _load(root, TAURI_CAPABILITY, diagnostics)
    if not isinstance(capability, dict) or capability.get("permissions") != ["core:default"]:
        _diagnostic(diagnostics, "DESKTOP_TAURI_PERMISSION_INVALID", TAURI_CAPABILITY, "only Tauri core defaults are authorized")

    source = "\n".join(
        (root / path).read_text(encoding="utf-8")
        for path in (
            APP_ROOT / "src/core/bridge.ts",
            APP_ROOT / "src/core/patcherRequests.ts",
            APP_ROOT / "src/components/PatchEditor.tsx",
            APP_ROOT / "src-tauri/src/desktop_bridge.rs",
            APP_ROOT / "bridge/desktop_core_bridge.py",
        )
    )
    for token in ("@tauri-apps/plugin-fs", "@tauri-apps/plugin-shell"):
        if token in source:
            _diagnostic(diagnostics, "DESKTOP_FORBIDDEN_CAPABILITY_PRESENT", APP_ROOT, f"forbidden runtime token {token!r} is present")
    for token in ("ReactFlow", "project.profile.transact", "project.objects.list", "workspace.projects.list", "workspace.project.create", "component.inspect", "build.session.start", "device.upload.start", "dispatch_desktop_operation"):
        if token not in source:
            _diagnostic(diagnostics, "DESKTOP_REQUIRED_CAPABILITY_MISSING", APP_ROOT, f"required implementation token {token!r} is absent")

    diagnostics.sort(key=lambda item: (item["path"], item["code"], item["detail"]))
    return {
        "boundary_schema_version": boundary.get("schema_version") if isinstance(boundary, dict) else None,
        "diagnostics": diagnostics,
        "file_count": len(files),
        "planned_operation_count": planned_count,
        "runtime_capability_count": runtime_count,
        "schema_version": "schuss-desktop-ui-structure-validation-v3",
        "semantic_record_count": semantic_count,
        "status": "valid" if not diagnostics else "invalid",
    }


def main() -> int:
    summary = validate_structure(ROOT)
    sys.stdout.buffer.write(
        json.dumps(summary, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8") + b"\n"
    )
    return 0 if summary["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
