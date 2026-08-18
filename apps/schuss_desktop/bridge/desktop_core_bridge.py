#!/usr/bin/env python3
"""Persistent fail-closed adapter for the bounded Schuss desktop operations."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from packages.schuss_core.control_plane import (  # noqa: E402
    canonical_result_bytes,
    dispatch_operation,
    load_repository_context,
)
from packages.schuss_core.project_service import ProjectService  # noqa: E402
from packages.schuss_core.build_sessions import BuildSessionService  # noqa: E402
from packages.schuss_core.device_sessions import DeviceSessionService  # noqa: E402
from tools.contracts import validator_core as core  # noqa: E402


RECORD_SET_PATH = (
    REPOSITORY_ROOT
    / "contracts/record-sets/ui-desktop-build-device-v1.json"
)
ALLOWED_OPERATIONS = {
    "application.describe": (
        "schuss-operation-request-v7",
        "schuss-operation-result-v7",
        False,
    ),
    "catalog.implementations.search": (
        "schuss-operation-request-v10",
        "schuss-operation-result-v10",
        False,
    ),
    "catalog.inspect": (
        "schuss-operation-request-v2",
        "schuss-operation-result-v2",
        False,
    ),
    "catalog.search": (
        "schuss-operation-request-v2",
        "schuss-operation-result-v2",
        False,
    ),
    "component.inspect": (
        "schuss-operation-request-v11",
        "schuss-operation-result-v11",
        False,
    ),
    "build.session.start": (
        "schuss-operation-request-v12",
        "schuss-operation-result-v12",
        True,
    ),
    "build.session.inspect": (
        "schuss-operation-request-v12",
        "schuss-operation-result-v12",
        True,
    ),
    "device.session.discover": (
        "schuss-operation-request-v12",
        "schuss-operation-result-v12",
        True,
    ),
    "device.session.inspect": (
        "schuss-operation-request-v12",
        "schuss-operation-result-v12",
        True,
    ),
    "device.upload.start": (
        "schuss-operation-request-v12",
        "schuss-operation-result-v12",
        True,
    ),
    "device.upload.inspect": (
        "schuss-operation-request-v12",
        "schuss-operation-result-v12",
        True,
    ),
    "graph.inspect": (
        "schuss-operation-request-v1",
        "schuss-operation-result-v1",
        False,
    ),
    "graph.transact": (
        "schuss-operation-request-v11",
        "schuss-operation-result-v11",
        True,
    ),
    "project.history.inspect": (
        "schuss-operation-request-v8",
        "schuss-operation-result-v8",
        True,
    ),
    "project.init": (
        "schuss-operation-request-v3",
        "schuss-operation-result-v3",
        True,
    ),
    "project.inspect": (
        "schuss-operation-request-v3",
        "schuss-operation-result-v3",
        True,
    ),
    "project.profile.fork": (
        "schuss-operation-request-v8",
        "schuss-operation-result-v8",
        True,
    ),
    "project.profile.transact": (
        "schuss-operation-request-v11",
        "schuss-operation-result-v11",
        True,
    ),
    "project.revert": (
        "schuss-operation-request-v8",
        "schuss-operation-result-v8",
        True,
    ),
    "project.validate": (
        "schuss-operation-request-v3",
        "schuss-operation-result-v3",
        True,
    ),
}
MAX_REQUEST_BYTES = 262_144


class BridgeRequestError(ValueError):
    """Stable adapter rejection that is not a Schuss operation result."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def bridge_error_bytes(code: str, message: str) -> bytes:
    value = {
        "error": {"code": code, "message": message},
        "schema_version": "schuss-desktop-bridge-error-v1",
    }
    return core.canonical_json(value).encode("utf-8")


def _workspace_path(value: Any) -> Path | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value or "\x00" in value:
        raise BridgeRequestError(
            "BRIDGE_WORKSPACE_INVALID",
            "workspace must be one explicit non-empty absolute path",
        )
    path = Path(value)
    if not path.is_absolute():
        raise BridgeRequestError(
            "BRIDGE_WORKSPACE_INVALID",
            "workspace must be one explicit absolute path",
        )
    return path


def validate_envelope(value: Any) -> tuple[dict[str, Any], Path | None, str]:
    if not isinstance(value, dict) or set(value) != {"request", "workspace"}:
        raise BridgeRequestError(
            "BRIDGE_REQUEST_INVALID",
            "desktop envelope must contain only request and workspace",
        )
    request = value["request"]
    if not isinstance(request, dict):
        raise BridgeRequestError("BRIDGE_REQUEST_INVALID", "request must be an object")
    operation = request.get("operation")
    if not isinstance(operation, str) or operation not in ALLOWED_OPERATIONS:
        raise BridgeRequestError(
            "BRIDGE_OPERATION_FORBIDDEN",
            "operation is not in the desktop allowlist",
        )
    expected_request, expected_result, requires_workspace = ALLOWED_OPERATIONS[operation]
    if request.get("schema_version") != expected_request:
        raise BridgeRequestError(
            "BRIDGE_REQUEST_VERSION_INVALID",
            "operation request schema does not match the allowlist",
        )
    if request.get("canonical_profile") != "schuss-canonical-json-v1":
        raise BridgeRequestError(
            "BRIDGE_CANONICAL_PROFILE_INVALID",
            "operation request must use the Schuss canonical JSON profile",
        )
    if not isinstance(request.get("payload"), dict) or set(request) != {
        "schema_version",
        "canonical_profile",
        "operation",
        "payload",
    }:
        raise BridgeRequestError(
            "BRIDGE_REQUEST_INVALID",
            "request fields do not match the shared operation envelope",
        )
    workspace = _workspace_path(value["workspace"])
    if requires_workspace and workspace is None:
        raise BridgeRequestError(
            "BRIDGE_WORKSPACE_REQUIRED",
            "operation requires one explicit project workspace",
        )
    return request, workspace, expected_result


class DesktopCore:
    def __init__(self) -> None:
        self.context = load_repository_context(
            repository_root=REPOSITORY_ROOT,
            record_set_path=RECORD_SET_PATH,
        )
        self.services: dict[Path, ProjectService] = {}
        self.build_sessions = BuildSessionService()
        self.device_sessions = DeviceSessionService(self.build_sessions)

    def service(self, workspace: Path) -> ProjectService:
        normalized = workspace.resolve(strict=False)
        service = self.services.get(normalized)
        if service is None:
            service = ProjectService(
                normalized,
                repository_root=REPOSITORY_ROOT,
                initial_context=self.context,
            )
            self.services[normalized] = service
        return service

    def dispatch(self, request: dict[str, Any], workspace: Path | None) -> dict[str, Any]:
        service = self.service(workspace) if workspace is not None else None
        return dispatch_operation(
            request,
            self.context,
            project_service=service,
            build_session_service=self.build_sessions,
            device_session_service=self.device_sessions,
        )


def dispatch_line(line: bytes, desktop: DesktopCore) -> bytes:
    if len(line) > MAX_REQUEST_BYTES:
        raise BridgeRequestError(
            "BRIDGE_REQUEST_TOO_LARGE", "request exceeds the desktop bridge limit"
        )
    envelope = core.load_json_bytes(
        line, "desktop bridge request", require_final_lf=True
    )
    request, workspace, expected_result = validate_envelope(envelope)
    result = desktop.dispatch(request, workspace)
    if result.get("operation") != request["operation"]:
        raise BridgeRequestError(
            "BRIDGE_RESULT_OPERATION_INVALID",
            "core result operation does not match the request",
        )
    if result.get("schema_version") != expected_result:
        raise BridgeRequestError(
            "BRIDGE_RESULT_VERSION_INVALID",
            "core result schema does not match the allowlist",
        )
    context = (
        desktop.context
        if result.get("schema_version") == "schuss-operation-result-v12"
        else desktop.service(workspace).context
        if workspace is not None
        else desktop.context
    )
    return canonical_result_bytes(result, context)


def run() -> int:
    desktop = DesktopCore()
    for line in sys.stdin.buffer:
        try:
            response = dispatch_line(line, desktop)
        except BridgeRequestError as error:
            response = bridge_error_bytes(error.code, str(error))
        except (UnicodeError, ValueError, json.JSONDecodeError):
            response = bridge_error_bytes(
                "BRIDGE_REQUEST_INVALID", "request is not restricted canonical JSON"
            )
        except Exception:
            response = bridge_error_bytes(
                "BRIDGE_INTERNAL",
                "desktop core bridge could not dispatch the request",
            )
        sys.stdout.buffer.write(response + b"\n")
        sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
