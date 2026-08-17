#!/usr/bin/env python3
"""Persistent, fail-closed adapter for Schuss's three desktop read routes."""

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
from tools.contracts import validator_core as core  # noqa: E402


RECORD_SET_PATH = (
    REPOSITORY_ROOT / "contracts/record-sets/task028-direct-palette-v1.json"
)
ALLOWED_OPERATIONS = {
    "application.describe": (
        "schuss-operation-request-v7",
        "schuss-operation-result-v7",
    ),
    "catalog.inspect": (
        "schuss-operation-request-v2",
        "schuss-operation-result-v2",
    ),
    "catalog.search": (
        "schuss-operation-request-v2",
        "schuss-operation-result-v2",
    ),
}
MAX_REQUEST_BYTES = 65_536


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


def validate_allowed_request(request: Any) -> tuple[str, str]:
    if not isinstance(request, dict):
        raise BridgeRequestError("BRIDGE_REQUEST_INVALID", "request must be an object")
    operation = request.get("operation")
    if not isinstance(operation, str) or operation not in ALLOWED_OPERATIONS:
        raise BridgeRequestError(
            "BRIDGE_OPERATION_FORBIDDEN",
            "operation is not in the read-only desktop allowlist",
        )
    expected_request, expected_result = ALLOWED_OPERATIONS[operation]
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
    return operation, expected_result


def dispatch_line(line: bytes, context: Any) -> bytes:
    if len(line) > MAX_REQUEST_BYTES:
        raise BridgeRequestError(
            "BRIDGE_REQUEST_TOO_LARGE", "request exceeds the desktop bridge limit"
        )
    request = core.load_json_bytes(line, "desktop bridge request", require_final_lf=True)
    operation, expected_result = validate_allowed_request(request)
    result = dispatch_operation(request, context)
    if result.get("operation") != operation:
        raise BridgeRequestError(
            "BRIDGE_RESULT_OPERATION_INVALID",
            "core result operation does not match the request",
        )
    if result.get("schema_version") != expected_result:
        raise BridgeRequestError(
            "BRIDGE_RESULT_VERSION_INVALID",
            "core result schema does not match the allowlist",
        )
    return canonical_result_bytes(result, context)


def run() -> int:
    context = load_repository_context(
        repository_root=REPOSITORY_ROOT,
        record_set_path=RECORD_SET_PATH,
    )
    for line in sys.stdin.buffer:
        try:
            response = dispatch_line(line, context)
        except BridgeRequestError as error:
            response = bridge_error_bytes(error.code, str(error))
        except (UnicodeError, ValueError, json.JSONDecodeError):
            response = bridge_error_bytes(
                "BRIDGE_REQUEST_INVALID", "request is not restricted canonical JSON"
            )
        except Exception:
            response = bridge_error_bytes(
                "BRIDGE_INTERNAL",
                "read-only core bridge could not dispatch the request",
            )
        sys.stdout.buffer.write(response + b"\n")
        sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
