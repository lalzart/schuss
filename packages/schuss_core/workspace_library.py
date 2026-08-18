"""Bounded projects-root browsing and template-backed project creation.

The desktop, CLI, and future clients call this service instead of scanning
project manifests themselves. One service instance owns one explicit absolute
projects root and returns only projects that the canonical ProjectService can
load and validate.
"""

from __future__ import annotations

import copy
import hashlib
import os
import re
import shutil
from pathlib import Path
from typing import Any

from .control_plane import OperationContext, canonical_result_bytes, core
from .project_service import ProjectError, ProjectService


MAX_PROJECTS = 128
REQUEST_SCHEMA_KEY = "operation_request_v14"
RESULT_SCHEMA_KEY = "operation_result_v14"
PROJECT_ID_RE = re.compile(r"^schuss-project-[0-9]{6}$")


class WorkspaceLibraryError(ValueError):
    """Stable projects-root failure surfaced as an operation diagnostic."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        status: str = "invalid",
        location: str = "$",
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status = status
        self.location = location


def _diagnostic(code: str, operation: str, location: str, message: str) -> dict[str, str]:
    return {
        "code": code,
        "severity": "error",
        "subject": operation,
        "location": location,
        "message": message,
    }


def _result(
    operation: str,
    status: str,
    value: dict[str, Any] | None,
    diagnostics: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "schuss-operation-result-v14",
        "canonical_profile": "schuss-canonical-json-v1",
        "operation": operation,
        "status": status,
        "value": copy.deepcopy(value),
        "diagnostics": sorted(
            diagnostics or [], key=core.diagnostic_sort_key
        ),
    }


def _reference(value: dict[str, Any], id_field: str) -> dict[str, Any]:
    return {
        id_field: value[id_field],
        "revision": value["revision"],
        "content_hash": value["content_hash"],
    }


def _slug(display_name: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", display_name.casefold()).strip("-")
    return (normalized[:64].rstrip("-") or "untitled-patch")


class WorkspaceLibraryService:
    """Core-owned library over direct children of one projects root."""

    def __init__(
        self,
        projects_root: Path,
        *,
        repository_root: Path,
        initial_context: OperationContext,
        maximum_projects: int = MAX_PROJECTS,
    ) -> None:
        root = Path(projects_root)
        if not root.is_absolute():
            raise WorkspaceLibraryError(
                "WORKSPACE_ROOT_NOT_ABSOLUTE",
                "projects root must be an explicit absolute path",
                location="$.workspace",
            )
        if maximum_projects < 1 or maximum_projects > MAX_PROJECTS:
            raise ValueError(f"maximum projects must be between 1 and {MAX_PROJECTS}")
        self.projects_root = root
        self.repository_root = Path(repository_root).resolve()
        self.initial_context = initial_context
        self.maximum_projects = maximum_projects

    def _resolved_root(self, *, create: bool) -> Path:
        if self.projects_root.is_symlink():
            raise WorkspaceLibraryError(
                "WORKSPACE_ROOT_SYMLINK_REJECTED",
                "projects root must not be a symbolic link",
                location="$.workspace",
            )
        if not self.projects_root.exists():
            if not create:
                raise WorkspaceLibraryError(
                    "WORKSPACE_ROOT_NOT_FOUND",
                    "configured projects root does not exist",
                    status="unavailable",
                    location="$.workspace",
                )
            self.projects_root.mkdir(parents=True, exist_ok=False)
        if not self.projects_root.is_dir():
            raise WorkspaceLibraryError(
                "WORKSPACE_ROOT_NOT_DIRECTORY",
                "configured projects root is not a directory",
                location="$.workspace",
            )
        return self.projects_root.resolve(strict=True)

    def _service(self, workspace: Path) -> ProjectService:
        return ProjectService(
            workspace,
            repository_root=self.repository_root,
            initial_context=self.initial_context,
        )

    @staticmethod
    def _summary(workspace: Path, loaded: Any) -> dict[str, Any]:
        graph_reference = loaded.manifest["primary_graph_reference"]
        graphs = [
            graph
            for graph in loaded.context.records["graphs"]
            if _reference(graph, "graph_id") == graph_reference
        ]
        if len(graphs) != 1:
            raise WorkspaceLibraryError(
                "WORKSPACE_PROJECT_GRAPH_UNRESOLVED",
                "accepted project primary graph did not resolve exactly once",
            )
        return {
            "workspace": str(workspace),
            "project_reference": _reference(loaded.manifest, "project_id"),
            "graph_reference": copy.deepcopy(graph_reference),
            "display_name": graphs[0]["display_name"],
        }

    def _discover_projects(
        self, root: Path
    ) -> tuple[list[dict[str, Any]], int, bool, int]:
        candidates: list[dict[str, Any]] = []
        rejected = 0
        visible_children = [
            child
            for child in sorted(root.iterdir(), key=lambda path: path.name.casefold())
            if not child.name.startswith(".") and (child.is_dir() or child.is_symlink())
        ]
        for child in visible_children[: self.maximum_projects]:
            if child.is_symlink():
                rejected += 1
                continue
            if not child.is_dir():
                continue
            try:
                resolved = child.resolve(strict=True)
                if resolved.parent != root:
                    raise WorkspaceLibraryError(
                        "WORKSPACE_PROJECT_ESCAPE_REJECTED",
                        "project child escapes the configured projects root",
                    )
                loaded = self._service(resolved).load()
                candidates.append(self._summary(resolved, loaded))
            except (OSError, ProjectError, WorkspaceLibraryError, ValueError):
                rejected += 1
        return (
            candidates,
            rejected,
            len(visible_children) > self.maximum_projects,
            len(visible_children),
        )

    def list_projects(self) -> dict[str, Any]:
        root = self._resolved_root(create=False)
        candidates, rejected, truncated, _child_count = self._discover_projects(root)
        identity_counts: dict[str, int] = {}
        for item in candidates:
            project_id = item["project_reference"]["project_id"]
            identity_counts[project_id] = identity_counts.get(project_id, 0) + 1
        duplicate_ids = {
            project_id for project_id, count in identity_counts.items() if count > 1
        }
        rejected += sum(identity_counts[project_id] for project_id in duplicate_ids)
        projects = [
            item
            for item in candidates
            if item["project_reference"]["project_id"] not in duplicate_ids
        ]
        projects.sort(
            key=lambda item: (
                item["display_name"].casefold(),
                item["project_reference"]["project_id"],
            )
        )
        return {
            "projects_root": str(root),
            "project_count": len(projects),
            "rejected_child_count": rejected,
            "truncated": truncated,
            "projects": projects,
        }

    def _allocate_directory(self, root: Path, display_name: str) -> Path:
        stem = _slug(display_name)
        for index in range(1, 1000):
            suffix = "" if index == 1 else f"-{index}"
            candidate = root / f"{stem}{suffix}"
            if not candidate.exists() and not candidate.is_symlink():
                return candidate
        raise WorkspaceLibraryError(
            "WORKSPACE_DIRECTORY_EXHAUSTED",
            "could not allocate a unique project directory",
            status="conflict",
        )

    def _allocate_project_id(self, root: Path, final: Path, existing: set[str]) -> str:
        seed = f"{root}\n{final.name}".encode("utf-8")
        start = int.from_bytes(hashlib.sha256(seed).digest()[:8], "big") % 900000
        for offset in range(900000):
            candidate = f"schuss-project-{100000 + ((start + offset) % 900000):06d}"
            if candidate not in existing and PROJECT_ID_RE.fullmatch(candidate):
                return candidate
        raise WorkspaceLibraryError(
            "WORKSPACE_PROJECT_ID_EXHAUSTED",
            "could not allocate a unique project identity",
            status="conflict",
        )

    def create_project(self, payload: dict[str, Any]) -> dict[str, Any]:
        display_name = payload["display_name"].strip()
        if not display_name:
            raise WorkspaceLibraryError(
                "WORKSPACE_PROJECT_NAME_EMPTY",
                "patch name must contain visible characters",
                location="$.payload.display_name",
            )
        root = self._resolved_root(create=True)
        existing, _rejected, truncated, child_count = self._discover_projects(root)
        if truncated or child_count >= self.maximum_projects:
            raise WorkspaceLibraryError(
                "WORKSPACE_PROJECT_LIMIT_REACHED",
                f"projects root already contains the bounded maximum of {self.maximum_projects} project directories",
                status="conflict",
            )
        final = self._allocate_directory(root, display_name)
        project_id = self._allocate_project_id(
            root,
            final,
            {item["project_reference"]["project_id"] for item in existing},
        )
        temporary = root / f".schuss-create-{project_id.removeprefix('schuss-project-')}"
        if temporary.exists() or temporary.is_symlink():
            raise WorkspaceLibraryError(
                "WORKSPACE_CREATE_TEMP_CONFLICT",
                "project creation staging directory already exists",
                status="conflict",
            )
        temporary.mkdir(mode=0o700)
        try:
            service = self._service(temporary)
            initialized = service.init(
                {
                    "project_id": project_id,
                    "base_record_set": {
                        "reference": copy.deepcopy(self.initial_context.record_set_reference),
                        "portable_locator": "contracts/record-sets/ui-desktop-workspace-shell-v1.json",
                    },
                    "primary_graph_reference": {
                        "graph_id": "schuss-graph-000006",
                        "revision": 1,
                        "content_hash": "sha256:1c3e3e66245cf497b507d60d21d3a8ebd8cdc5117f02eab8b793853a4bef5aa2",
                    },
                    "instrument_references": [
                        {
                            "instrument_id": "schuss-instrument-000005",
                            "revision": 1,
                            "content_hash": "sha256:e4d8d801dba7f8c557295444d3de22ad212601b88d3bd4bf7dfa7f4025aa2679",
                        }
                    ],
                    "build_request_references": [
                        {
                            "build_request_id": "schuss-build-request-000005",
                            "revision": 1,
                            "content_hash": "sha256:8f40ac2f996f32f10f59b862da566f1d66f145cdf1780f29d786c9b2f42f03c2",
                        }
                    ],
                    "asset_references": [],
                }
            )
            forked = service.fork_profile(
                {
                    "expected_project_reference": _reference(
                        initialized["project"], "project_id"
                    ),
                    "template_graph_reference": initialized["project"]["primary_graph_reference"],
                    "template_instrument_reference": initialized["project"]["instrument_references"][0],
                    "template_build_request_reference": initialized["project"]["build_request_references"][0],
                    "write_intent": "explicit",
                }
            )
            renamed = service.transact_profile(
                {
                    "expected_project_reference": _reference(forked["project"], "project_id"),
                    "graph_reference": _reference(forked["graph"], "graph_id"),
                    "base_content_hash": forked["graph"]["content_hash"],
                    "edits": [
                        {"edit": "set-graph-display-name", "display_name": display_name}
                    ],
                    "write_intent": "explicit",
                }
            )
            os.replace(temporary, final)
            loaded = self._service(final).load()
            summary = self._summary(final, loaded)
            return {
                "projects_root": str(root),
                "project": summary,
                "creation": {
                    "project_id_allocated": project_id,
                    "template_profile_forked": True,
                    "display_name_revision": renamed["project"]["revision"],
                    "publication": "atomic-directory-rename",
                },
            }
        except Exception:
            if temporary.exists() and not temporary.is_symlink():
                shutil.rmtree(temporary)
            raise


def dispatch_workspace_operation(
    request: dict[str, Any],
    context: OperationContext,
    service: WorkspaceLibraryService | None,
) -> dict[str, Any]:
    """Validate and dispatch one v14 projects-root operation."""

    operation = request.get("operation") if isinstance(request, dict) else None
    schema = context.schemas.get(REQUEST_SCHEMA_KEY)
    errors: list[str] = []
    try:
        core.assert_portable_json_value(request)
    except ValueError as exc:
        errors.append(str(exc))
    if schema is None:
        errors.append("$: workspace operation schema is unavailable")
    elif isinstance(request, dict):
        errors.extend(core.schema_errors(request, schema, schema))
    else:
        errors.append("$: operation request must be an object")
    if errors:
        valid_operation = operation if operation in {
            "workspace.projects.list",
            "workspace.project.create",
        } else "invalid-request"
        result = _result(
            valid_operation,
            "invalid",
            None,
            [
                _diagnostic("OPERATION_REQUEST_INVALID", valid_operation, "$", error)
                for error in sorted(set(errors))
            ],
        )
        canonical_result_bytes(result, context)
        return result
    if service is None:
        result = _result(
            operation,
            "unavailable",
            None,
            [_diagnostic(
                "WORKSPACE_SERVICE_REQUIRED",
                operation,
                "$.workspace",
                "operation requires one explicit projects-root service",
            )],
        )
        canonical_result_bytes(result, context)
        return result
    try:
        value = (
            service.list_projects()
            if operation == "workspace.projects.list"
            else service.create_project(request["payload"])
        )
        result = _result(operation, "success", value)
    except WorkspaceLibraryError as exc:
        result = _result(
            operation,
            exc.status,
            None,
            [_diagnostic(exc.code, operation, exc.location, str(exc))],
        )
    except ProjectError as exc:
        result = _result(
            operation,
            exc.status,
            None,
            [_diagnostic(exc.code, operation, exc.location, str(exc))],
        )
    canonical_result_bytes(result, context)
    return result
