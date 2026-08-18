"""Small process-local build jobs over the accepted Schuss build executor."""

from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import tempfile
from threading import Event, Lock, Thread
from typing import Any, Callable, Mapping

from . import build_execution
from .compiler_front_half import CompilationContext
from .execution_registry import registered_execution_service


TERMINAL_STATUSES = {
    "success",
    "failed",
    "cancelled",
    "unavailable",
    "invalid",
    "unresolved",
    "unsupported",
    "ambiguous",
    "budget-failure",
}


class BuildSessionError(ValueError):
    """Stable fail-closed build-session preflight rejection."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


ExecutionFactory = Callable[[Path], build_execution.ExecutionService]
ExecuteFunction = Callable[..., dict[str, Any]]


def _reference(record: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "build_request_id": record["build_request_id"],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def _diagnostic(code: str, stage: str, subject: str, message: str) -> dict[str, str]:
    return {
        "code": code,
        "severity": "error",
        "stage": stage,
        "subject": subject,
        "message": message,
    }


class BuildSessionService:
    """Own bounded temporary outputs and asynchronous execution state."""

    def __init__(
        self,
        *,
        execution_factory: ExecutionFactory = registered_execution_service,
        execute_function: ExecuteFunction = build_execution.execute_build,
        maximum_sessions: int = 8,
    ) -> None:
        if maximum_sessions < 1:
            raise ValueError("maximum_sessions must be positive")
        self._execution_factory = execution_factory
        self._execute_function = execute_function
        self._maximum_sessions = maximum_sessions
        self._lock = Lock()
        self._next_id = 1
        self._sessions: dict[str, dict[str, Any]] = {}
        self._roots: dict[str, tempfile.TemporaryDirectory[str]] = {}

    def _exact_request(
        self,
        context: CompilationContext,
        requested: Mapping[str, Any],
    ) -> dict[str, Any]:
        matches = [
            item
            for item in context.records()["request"]
            if _reference(item) == dict(requested)
        ]
        if len(matches) != 1:
            raise BuildSessionError(
                "BUILD_SESSION_REQUEST_NOT_EXACT",
                f"expected one exact accepted build request, found {len(matches)}",
            )
        return matches[0]

    def _exact_handler(
        self,
        service: build_execution.ExecutionService,
        request_record: Mapping[str, Any],
    ) -> dict[str, Any]:
        request_reference = _reference(request_record)
        matches = []
        for registration in service.registrations:
            descriptor = registration.descriptor
            if descriptor.get("backend_reference") != request_record["backend_reference"]:
                continue
            if descriptor.get("schema_version") == "build-handler-descriptor-v0":
                if descriptor.get("supported_build_request_reference") != request_reference:
                    continue
            elif descriptor.get("schema_version") != "build-handler-descriptor-v1":
                continue
            matches.append(build_execution.handler_reference(descriptor))
        if len(matches) != 1:
            raise BuildSessionError(
                "BUILD_SESSION_HANDLER_NOT_EXACT",
                f"expected one exact compatible registered handler, found {len(matches)}",
            )
        return copy.deepcopy(matches[0])

    def _evict_if_needed(self) -> None:
        while len(self._sessions) >= self._maximum_sessions:
            terminal = [
                identifier
                for identifier, session in self._sessions.items()
                if session["status"] in TERMINAL_STATUSES
            ]
            if not terminal:
                raise BuildSessionError(
                    "BUILD_SESSION_LIMIT_REACHED",
                    "all retained build sessions are still active",
                )
            identifier = terminal[0]
            self._sessions.pop(identifier)
            root = self._roots.pop(identifier, None)
            if root is not None:
                root.cleanup()

    @staticmethod
    def _public(session: Mapping[str, Any]) -> dict[str, Any]:
        return copy.deepcopy(
            {
                key: value
                for key, value in session.items()
                if key not in {"compilation_context", "output_root", "execution_service"}
            }
        )

    def start(
        self,
        compilation_context: CompilationContext,
        *,
        build_request_reference: Mapping[str, Any],
        execution_intent: bool,
        project_reference: Mapping[str, Any],
    ) -> dict[str, Any]:
        if execution_intent is not True:
            raise BuildSessionError(
                "BUILD_SESSION_INTENT_REQUIRED",
                "explicit build execution intent is required",
            )
        request_record = self._exact_request(
            compilation_context, build_request_reference
        )
        temporary = tempfile.TemporaryDirectory(prefix="schuss-build-session-")
        output_root = Path(temporary.name) / "build-output"
        try:
            execution_service = self._execution_factory(output_root)
            handler_reference = self._exact_handler(execution_service, request_record)
            with self._lock:
                self._evict_if_needed()
                identifier = f"build-session-{self._next_id:06d}"
                self._next_id += 1
                session = {
                    "session_id": identifier,
                    "status": "queued",
                    "phase": "queued",
                    "project_reference": copy.deepcopy(dict(project_reference)),
                    "build_request_reference": copy.deepcopy(
                        dict(build_request_reference)
                    ),
                    "handler_reference": handler_reference,
                    "progress": [],
                    "stage_outcomes": [],
                    "artifacts": [],
                    "evidence_levels": [
                        {"level": level, "status": "not-run"}
                        for level in range(1, 9)
                    ],
                    "diagnostics": [],
                    "authoritative_records_mutated": False,
                    "device_actions_performed": False,
                    "compilation_context": compilation_context,
                    "output_root": output_root,
                    "execution_service": execution_service,
                }
                self._sessions[identifier] = session
                self._roots[identifier] = temporary
                initial = self._public(session)
        except Exception:
            temporary.cleanup()
            raise

        begin = Event()
        thread = Thread(
            target=self._run,
            args=(identifier, begin),
            name=identifier,
            daemon=True,
        )
        thread.start()
        begin.set()
        return initial

    def _run(self, identifier: str, begin: Event) -> None:
        begin.wait()
        with self._lock:
            session = self._sessions[identifier]
            session["status"] = "running"
            session["phase"] = "planning"

        def progress(value: dict[str, Any]) -> None:
            with self._lock:
                current = self._sessions.get(identifier)
                if current is None:
                    return
                current["progress"].append(copy.deepcopy(value))
                current["phase"] = value["event"]

        try:
            with self._lock:
                session = self._sessions[identifier]
                compilation_context = session["compilation_context"]
                handler_reference = copy.deepcopy(session["handler_reference"])
                execution_service = session["execution_service"]
            result = self._execute_function(
                compilation_context,
                handler_reference,
                execution_service,
                execution_intent=True,
                progress_callback=progress,
            )
            with self._lock:
                current = self._sessions[identifier]
                current["status"] = result["status"]
                current["phase"] = (
                    "completed" if result["status"] == "success" else "failed"
                )
                current["progress"] = copy.deepcopy(result["progress"])
                current["stage_outcomes"] = copy.deepcopy(result["stage_outcomes"])
                current["artifacts"] = copy.deepcopy(result["artifacts"])
                current["evidence_levels"] = copy.deepcopy(result["evidence_levels"])
                current["diagnostics"] = copy.deepcopy(result["diagnostics"])
        except Exception as error:
            code = str(getattr(error, "code", "BUILD_SESSION_INTERNAL_FAILED"))
            stage = str(getattr(error, "stage", "build-session"))
            subject = str(getattr(error, "subject", identifier))
            with self._lock:
                current = self._sessions[identifier]
                current["status"] = "failed"
                current["phase"] = "failed"
                current["diagnostics"] = [
                    _diagnostic(code, stage, subject, str(error))
                ]

    def inspect(self, identifier: str) -> dict[str, Any]:
        with self._lock:
            session = self._sessions.get(identifier)
            if session is None:
                raise BuildSessionError(
                    "BUILD_SESSION_NOT_FOUND",
                    "the process-local build session is absent or expired",
                )
            return self._public(session)

    def target_artifact(
        self, identifier: str, artifact_sha256: str
    ) -> tuple[dict[str, Any], Path]:
        with self._lock:
            session = self._sessions.get(identifier)
            if session is None:
                raise BuildSessionError(
                    "BUILD_SESSION_NOT_FOUND",
                    "the process-local build session is absent or expired",
                )
            if session["status"] != "success":
                raise BuildSessionError(
                    "BUILD_SESSION_NOT_SUCCESSFUL",
                    "upload requires one successful build session",
                )
            matches = [
                item
                for item in session["artifacts"]
                if item["artifact_kind"] == "target-executable"
                and item["byte_sha256"] == artifact_sha256
            ]
            if len(matches) != 1:
                raise BuildSessionError(
                    "BUILD_SESSION_ARTIFACT_NOT_EXACT",
                    "the exact successful target executable did not resolve once",
                )
            descriptor = copy.deepcopy(matches[0])
            path = session["output_root"] / "artifacts" / descriptor["portable_locator"]
        if (
            not path.is_file()
            or path.is_symlink()
            or path.stat().st_size != descriptor["byte_length"]
        ):
            raise BuildSessionError(
                "BUILD_SESSION_ARTIFACT_BYTES_INVALID",
                "retained target executable bytes are unavailable",
            )
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != descriptor["byte_sha256"]:
            raise BuildSessionError(
                "BUILD_SESSION_ARTIFACT_BYTES_INVALID",
                "retained target executable hash does not match its descriptor",
            )
        return descriptor, path

    def close(self) -> None:
        with self._lock:
            roots = list(self._roots.values())
            self._roots.clear()
            self._sessions.clear()
        for root in roots:
            root.cleanup()
