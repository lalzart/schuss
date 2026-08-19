"""Process-local Task 031 offline-render and native audio session services.

Schuss core owns the exact project snapshot, lowering authority, package
identity, and volatile session handle.  The native engine owns device access
and the real-time callback; no sample buffer crosses this protocol.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import selectors
import subprocess
import tempfile
from pathlib import Path
from threading import Lock
from typing import Any, Callable, Mapping, Protocol

from .control_plane import OperationContext, canonical_result_bytes, core, with_compiler_schemas
from .host_runtime import HOST_ENGINE_PROTOCOL_ABI, HOST_RUNTIME_ABI, HostRuntimeError, lower_host_package
from .project_service import ProjectError, ProjectService


PROTOCOL_SCHEMA_VERSION = "host-engine-protocol-v0"
PACKAGE_SCHEMA_VERSION = "host-runtime-package-v0"
MAXIMUM_RETAINED_RENDERS = 8


class HostSessionError(ValueError):
    """Stable fail-closed error surfaced through operation result v14."""

    def __init__(self, code: str, message: str, *, status: str = "failed") -> None:
        super().__init__(message)
        self.code = code
        self.status = status


class EngineProtocolError(HostSessionError):
    """Native process or private-protocol failure."""


class EngineTransport(Protocol):
    def request(self, message: Mapping[str, Any]) -> dict[str, Any]: ...
    def close(self) -> None: ...


def _project_reference(manifest: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "project_id": manifest["project_id"],
        "revision": manifest["revision"],
        "content_hash": manifest["content_hash"],
    }


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return core.canonical_json(dict(value)).encode("utf-8") + b"\n"


def _public_error_message(error: BaseException) -> str:
    """Keep operation diagnostics useful without leaking host paths."""

    if isinstance(error, (HostSessionError, HostRuntimeError)):
        return str(error)
    if isinstance(error, ProjectError):
        return "the accepted project could not be loaded"
    return "the process-local host operation failed"


class SubprocessEngineTransport:
    """One line-delimited private protocol connection to a native engine."""

    def __init__(
        self,
        executable: Path,
        protocol_schema: Mapping[str, Any],
        *,
        protocol_abi: str = HOST_ENGINE_PROTOCOL_ABI,
        response_timeout_seconds: float = 5.0,
    ) -> None:
        executable = Path(executable)
        if not executable.is_file() or executable.is_symlink() or not os.access(executable, os.X_OK):
            raise EngineProtocolError(
                "ENGINE_EXECUTABLE_UNAVAILABLE",
                "the configured native audio engine is unavailable",
                status="unavailable",
            )
        if response_timeout_seconds <= 0:
            raise ValueError("response timeout must be positive")
        if not isinstance(protocol_abi, str) or not protocol_abi:
            raise ValueError("protocol ABI must be a non-empty string")
        self._protocol_schema = copy.deepcopy(dict(protocol_schema))
        self._protocol_abi = protocol_abi
        self._timeout = response_timeout_seconds
        try:
            self._process = subprocess.Popen(
                [str(executable)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="strict",
                bufsize=1,
            )
        except OSError as error:
            raise EngineProtocolError(
                "ENGINE_PROCESS_LAUNCH_FAILED",
                "the native audio engine could not be launched",
                status="unavailable",
            ) from error
        self._closed = False
        self._lock = Lock()

    def _read_response(self) -> str:
        assert self._process.stdout is not None
        selector = selectors.DefaultSelector()
        try:
            selector.register(self._process.stdout, selectors.EVENT_READ)
            if not selector.select(self._timeout):
                raise EngineProtocolError(
                    "ENGINE_RESPONSE_TIMEOUT",
                    "the native audio engine did not respond within the bounded timeout",
                    status="unavailable",
                )
            line = self._process.stdout.readline()
        finally:
            selector.close()
        if not line:
            return_code = self._process.poll()
            suffix = "" if return_code is None else f" with exit code {return_code}"
            raise EngineProtocolError(
                "ENGINE_PROCESS_DISCONNECTED",
                "the native audio engine disconnected" + suffix,
                status="unavailable",
            )
        if len(line.encode("utf-8")) > 1024 * 1024:
            raise EngineProtocolError("ENGINE_RESPONSE_OVERSIZED", "the native audio engine response exceeded its bound")
        return line

    @staticmethod
    def _validate_response(
        response: Any,
        message_id: str,
        protocol_abi: str,
    ) -> dict[str, Any]:
        if not isinstance(response, dict) or set(response) != {
            "diagnostics", "message_id", "protocol_abi", "status", "value"
        }:
            raise EngineProtocolError("ENGINE_RESPONSE_INVALID", "the native audio engine returned an invalid response shape")
        if response["message_id"] != message_id:
            raise EngineProtocolError("ENGINE_RESPONSE_ID_MISMATCH", "the native audio engine response did not match the request")
        if response["protocol_abi"] != protocol_abi:
            raise EngineProtocolError("ENGINE_RESPONSE_ABI_MISMATCH", "the native audio engine response ABI is unsupported")
        if response["status"] not in {"success", "failed"} or not isinstance(response["diagnostics"], list):
            raise EngineProtocolError("ENGINE_RESPONSE_INVALID", "the native audio engine returned an invalid status")
        for diagnostic in response["diagnostics"]:
            if not isinstance(diagnostic, dict) or set(diagnostic) != {"code", "message", "severity"}:
                raise EngineProtocolError("ENGINE_RESPONSE_INVALID", "the native audio engine returned an invalid diagnostic")
            if diagnostic["severity"] not in {"error", "warning", "info"}:
                raise EngineProtocolError("ENGINE_RESPONSE_INVALID", "the native audio engine returned an invalid diagnostic severity")
        if response["status"] == "failed":
            diagnostic = response["diagnostics"][0] if response["diagnostics"] else {}
            raise EngineProtocolError(
                str(diagnostic.get("code", "ENGINE_OPERATION_FAILED")),
                str(diagnostic.get("message", "the native audio engine rejected the operation")),
            )
        if not isinstance(response["value"], dict):
            raise EngineProtocolError("ENGINE_RESPONSE_INVALID", "the native audio engine returned no successful value")
        return copy.deepcopy(response["value"])

    def request(self, message: Mapping[str, Any]) -> dict[str, Any]:
        request = copy.deepcopy(dict(message))
        errors = core.schema_errors(request, self._protocol_schema, self._protocol_schema)
        if errors:
            raise EngineProtocolError("ENGINE_REQUEST_INVALID", "; ".join(errors))
        message_id = request["message_id"]
        with self._lock:
            if self._closed or self._process.poll() is not None:
                raise EngineProtocolError(
                    "ENGINE_PROCESS_UNAVAILABLE",
                    "the native audio engine process is not available",
                    status="unavailable",
                )
            assert self._process.stdin is not None
            try:
                self._process.stdin.write(core.canonical_json(request) + "\n")
                self._process.stdin.flush()
                response = json.loads(self._read_response())
            except EngineProtocolError:
                raise
            except (BrokenPipeError, OSError, UnicodeError, json.JSONDecodeError) as error:
                raise EngineProtocolError(
                    "ENGINE_PROCESS_DISCONNECTED",
                    "the native audio engine connection failed",
                    status="unavailable",
                ) from error
            return self._validate_response(
                response,
                message_id,
                self._protocol_abi,
            )

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
            process = self._process
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2.0)
        for stream in (process.stdin, process.stdout):
            if stream is not None:
                stream.close()


TransportFactory = Callable[[], EngineTransport]


class _MessageFactory:
    def __init__(self) -> None:
        self._next_id = 1

    def make(self, message_type: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        message = {
            "schema_version": PROTOCOL_SCHEMA_VERSION,
            "protocol_abi": HOST_ENGINE_PROTOCOL_ABI,
            "message_id": f"engine-message-{self._next_id:06d}",
            "message_type": message_type,
            "payload": copy.deepcopy(dict(payload)),
        }
        self._next_id += 1
        return message


class AudioSessionService:
    """Own one native engine generation and exact process-local sessions."""

    def __init__(self, project_service: ProjectService, transport_factory: TransportFactory) -> None:
        self.project_service = project_service
        self._transport_factory = transport_factory
        self._transport: EngineTransport | None = None
        self._generation = 0
        self._messages = _MessageFactory()
        self._next_id = 1
        self._sessions: dict[str, dict[str, Any]] = {}
        self._temporary = tempfile.TemporaryDirectory(prefix="schuss-audio-session-")
        self._lock = Lock()

    def _message(self, message_type: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        return self._messages.make(message_type, payload)

    def _invalidate(self) -> None:
        transport, self._transport = self._transport, None
        if transport is not None:
            transport.close()

    def _ensure_transport(self) -> EngineTransport:
        if self._transport is not None:
            return self._transport
        transport = self._transport_factory()
        try:
            value = transport.request(
                self._message(
                    "hello",
                    {
                        "runtime_abi": HOST_RUNTIME_ABI,
                        "package_schema_version": PACKAGE_SCHEMA_VERSION,
                    },
                )
            )
            if value != {
                "package_schema_version": PACKAGE_SCHEMA_VERSION,
                "runtime_abi": HOST_RUNTIME_ABI,
            }:
                raise EngineProtocolError("ENGINE_HANDSHAKE_MISMATCH", "the native engine handshake did not match the accepted ABIs")
        except Exception:
            transport.close()
            raise
        self._generation += 1
        self._transport = transport
        return transport

    def _request(self, message_type: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        try:
            return self._ensure_transport().request(self._message(message_type, payload))
        except EngineProtocolError as error:
            if error.status == "unavailable" or error.code in {
                "ENGINE_RESPONSE_ABI_MISMATCH",
                "ENGINE_RESPONSE_ID_MISMATCH",
                "ENGINE_RESPONSE_INVALID",
            }:
                self._invalidate()
            raise

    def inspect_devices(self, *, inspection_intent: str) -> dict[str, Any]:
        if inspection_intent != "enumerate-local-audio-midi":
            raise HostSessionError("AUDIO_DEVICE_INSPECTION_INTENT_REQUIRED", "explicit local audio/MIDI inspection intent is required", status="invalid")
        value = self._request("devices.inspect", {"inspection_intent": inspection_intent})
        if set(value) != {"audio_devices", "midi_inputs"} or not all(
            isinstance(value[key], list) for key in value
        ):
            self._invalidate()
            raise EngineProtocolError("ENGINE_DEVICE_RESPONSE_INVALID", "the native engine returned invalid device inspection facts")
        return {
            "inspection_intent": inspection_intent,
            "engine_generation": self._generation,
            **copy.deepcopy(value),
            "device_action_performed": "identity-enumeration-only",
        }

    def _exact_project(self, requested: Mapping[str, Any]):
        loaded = self.project_service.load()
        actual = _project_reference(loaded.manifest)
        if dict(requested) != actual:
            raise HostSessionError(
                "AUDIO_SESSION_PROJECT_NOT_EXACT",
                "the requested project reference is not the accepted workspace head",
                status="conflict",
            )
        return loaded, actual

    def start(
        self,
        *,
        project_reference: Mapping[str, Any],
        sample_rate_hz: int,
        block_frames: int,
        start_intent: str,
    ) -> dict[str, Any]:
        if start_intent != "start-local-audio-session":
            raise HostSessionError("AUDIO_SESSION_START_INTENT_REQUIRED", "explicit local audio start intent is required", status="invalid")
        if (
            isinstance(sample_rate_hz, bool)
            or not isinstance(sample_rate_hz, int)
            or sample_rate_hz != 48000
            or isinstance(block_frames, bool)
            or not isinstance(block_frames, int)
            or not 1 <= block_frames <= 512
        ):
            raise HostSessionError(
                "AUDIO_SESSION_CONFIGURATION_UNSUPPORTED",
                "the initial host runtime accepts 48000 Hz and block sizes from 1 through 512",
                status="invalid",
            )
        with self._lock:
            if any(value["status"] == "active" for value in self._sessions.values()):
                raise HostSessionError("AUDIO_SESSION_ALREADY_ACTIVE", "one process-local audio session is already active", status="conflict")
            loaded, snapshot = self._exact_project(project_reference)
            context = with_compiler_schemas(loaded.context, self.project_service.repository_root)
            package, _ = lower_host_package(context, project_reference=snapshot)
            package_path = Path(self._temporary.name) / (package["content_hash"].removeprefix("sha256:") + ".json")
            expected_bytes = _canonical_bytes(package)
            if package_path.exists():
                if package_path.is_symlink() or package_path.read_bytes() != expected_bytes:
                    raise HostSessionError("AUDIO_SESSION_PACKAGE_STAGING_CONFLICT", "the process-local package staging identity is inconsistent")
            else:
                package_path.write_bytes(expected_bytes)
            try:
                prepared = self._request(
                    "package.prepare",
                    {"package_path": str(package_path), "package_content_hash": package["content_hash"]},
                )
                if prepared != {"package_content_hash": package["content_hash"], "runtime_abi": HOST_RUNTIME_ABI}:
                    raise EngineProtocolError("ENGINE_PREPARE_RESPONSE_MISMATCH", "the native engine did not confirm the exact accepted package")
                engine = self._request(
                    "session.start",
                    {"sample_rate_hz": sample_rate_hz, "block_frames": block_frames},
                )
                if engine.get("active") is not True or engine.get("package_content_hash") != package["content_hash"]:
                    raise EngineProtocolError("ENGINE_START_RESPONSE_MISMATCH", "the native engine did not activate the exact accepted package")
            except Exception:
                self._invalidate()
                raise
            identifier = f"audio-session-{self._next_id:06d}"
            self._next_id += 1
            session = {
                "audio_session_id": identifier,
                "status": "active",
                "project_reference": snapshot,
                "package_content_hash": package["content_hash"],
                "engine_generation": self._generation,
                "requested_configuration": {
                    "sample_rate_hz": sample_rate_hz,
                    "block_frames": block_frames,
                },
                "engine": copy.deepcopy(engine),
                "authoritative_records_mutated": False,
            }
            self._sessions[identifier] = session
            return copy.deepcopy(session)

    def _session(self, identifier: str) -> dict[str, Any]:
        session = self._sessions.get(identifier)
        if session is None:
            raise HostSessionError("AUDIO_SESSION_NOT_FOUND", "the process-local audio session is absent or belongs to another service", status="unresolved")
        if session["engine_generation"] != self._generation or self._transport is None:
            session["status"] = "failed"
            raise HostSessionError("AUDIO_SESSION_STALE_ENGINE", "the audio session belongs to an expired native engine generation", status="unresolved")
        return session

    def inspect(self, identifier: str) -> dict[str, Any]:
        with self._lock:
            session = self._session(identifier)
            if session["status"] != "active":
                return copy.deepcopy(session)
            try:
                engine = self._request("session.inspect", {})
                if engine.get("active") is not True or engine.get("package_content_hash") != session["package_content_hash"]:
                    raise EngineProtocolError("ENGINE_SESSION_STATE_MISMATCH", "the native engine no longer reports the accepted active session")
            except Exception:
                session["status"] = "failed"
                self._invalidate()
                raise
            session["engine"] = copy.deepcopy(engine)
            return copy.deepcopy(session)

    def stop(self, identifier: str, *, stop_intent: str) -> dict[str, Any]:
        if stop_intent != "stop-local-audio-session":
            raise HostSessionError("AUDIO_SESSION_STOP_INTENT_REQUIRED", "explicit local audio stop intent is required", status="invalid")
        with self._lock:
            session = self._session(identifier)
            if session["status"] != "active":
                raise HostSessionError("AUDIO_SESSION_NOT_ACTIVE", "the process-local audio session is not active", status="conflict")
            try:
                engine = self._request("session.stop", {})
                if engine.get("active") is not False:
                    raise EngineProtocolError("ENGINE_STOP_RESPONSE_MISMATCH", "the native engine did not confirm a stopped session")
            except Exception:
                session["status"] = "failed"
                self._invalidate()
                raise
            session["status"] = "stopped"
            session["engine"] = copy.deepcopy(engine)
            return copy.deepcopy(session)

    def close(self) -> None:
        with self._lock:
            self._invalidate()
            for session in self._sessions.values():
                if session["status"] == "active":
                    session["status"] = "stopped"
        self._temporary.cleanup()


RendererRunner = Callable[[list[str]], subprocess.CompletedProcess[str]]


def _run_renderer(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


class HostRenderService:
    """Synchronous, process-local deterministic offline render sessions."""

    def __init__(
        self,
        project_service: ProjectService,
        renderer_executable: Path,
        *,
        runner: RendererRunner = _run_renderer,
    ) -> None:
        self.project_service = project_service
        self._renderer = Path(renderer_executable)
        self._runner = runner
        self._next_id = 1
        self._sessions: dict[str, dict[str, Any]] = {}
        self._roots: dict[str, tempfile.TemporaryDirectory[str]] = {}

    def start(
        self,
        *,
        project_reference: Mapping[str, Any],
        render_frames: int,
        block_frames: int,
        render_intent: str,
    ) -> dict[str, Any]:
        if render_intent != "offline-render":
            raise HostSessionError("HOST_RENDER_INTENT_REQUIRED", "explicit offline render intent is required", status="invalid")
        if (
            isinstance(render_frames, bool)
            or not isinstance(render_frames, int)
            or not 1 <= render_frames <= 480000
            or isinstance(block_frames, bool)
            or not isinstance(block_frames, int)
            or not 1 <= block_frames <= 512
        ):
            raise HostSessionError(
                "HOST_RENDER_CONFIGURATION_UNSUPPORTED",
                "the offline renderer requires 1 through 480000 frames and block sizes from 1 through 512",
                status="invalid",
            )
        if not self._renderer.is_file() or self._renderer.is_symlink() or not os.access(self._renderer, os.X_OK):
            raise HostSessionError("HOST_RENDERER_UNAVAILABLE", "the configured offline renderer is unavailable", status="unavailable")
        loaded = self.project_service.load()
        snapshot = _project_reference(loaded.manifest)
        if dict(project_reference) != snapshot:
            raise HostSessionError("HOST_RENDER_PROJECT_NOT_EXACT", "the requested project reference is not the accepted workspace head", status="conflict")
        context = with_compiler_schemas(loaded.context, self.project_service.repository_root)
        package, _ = lower_host_package(context, project_reference=snapshot)
        identifier = f"host-render-{self._next_id:06d}"
        temporary = tempfile.TemporaryDirectory(prefix=identifier + "-")
        root = Path(temporary.name)
        package_path = root / "package.json"
        wav_path = root / "output.wav"
        observation_path = root / "observation.json"
        package_path.write_bytes(_canonical_bytes(package))
        completed = self._runner(
            [
                str(self._renderer),
                "--package", str(package_path),
                "--package-hash", package["content_hash"],
                "--output", str(wav_path),
                "--observation", str(observation_path),
                "--frames", str(render_frames),
                "--block", str(block_frames),
            ]
        )
        if completed.returncode or not wav_path.is_file() or not observation_path.is_file():
            temporary.cleanup()
            raise HostSessionError("HOST_RENDER_EXECUTION_FAILED", "the offline renderer did not publish complete process-local outputs")
        try:
            observation = core.load_json(observation_path)
            schema = context.schemas["host_runtime_observation"]
            errors = core.schema_errors(observation, schema, schema)
            if errors or observation["content_hash"] != core.record_content_hash(observation, schema):
                raise HostSessionError("HOST_RENDER_OBSERVATION_INVALID", "the offline renderer published an invalid observation")
            wav = wav_path.read_bytes()
            if (
                observation["package_content_hash"] != package["content_hash"]
                or observation["output"]["byte_length"] != len(wav)
                or observation["output"]["byte_sha256"] != hashlib.sha256(wav).hexdigest()
            ):
                raise HostSessionError("HOST_RENDER_OUTPUT_IDENTITY_MISMATCH", "the offline render output does not match its observation")
        except Exception:
            temporary.cleanup()
            raise
        self._next_id += 1
        session = {
            "render_session_id": identifier,
            "status": "success",
            "project_reference": snapshot,
            "package_content_hash": package["content_hash"],
            "observation": observation,
            "authoritative_records_mutated": False,
            "device_actions_performed": False,
        }
        self._sessions[identifier] = session
        self._roots[identifier] = temporary
        while len(self._sessions) > MAXIMUM_RETAINED_RENDERS:
            oldest = next(iter(self._sessions))
            self._sessions.pop(oldest)
            self._roots.pop(oldest).cleanup()
        return copy.deepcopy(session)

    def inspect(self, identifier: str) -> dict[str, Any]:
        session = self._sessions.get(identifier)
        if session is None:
            raise HostSessionError("HOST_RENDER_NOT_FOUND", "the process-local host render is absent or expired", status="unresolved")
        return copy.deepcopy(session)

    def close(self) -> None:
        for temporary in self._roots.values():
            temporary.cleanup()
        self._roots.clear()
        self._sessions.clear()


def _diagnostic(code: str, subject: str, message: str) -> dict[str, str]:
    return {
        "code": code,
        "severity": "error",
        "subject": subject,
        "location": "$.payload",
        "message": message,
    }


def _result(operation: str, status: str, value: dict[str, Any] | None, diagnostics: list[dict[str, str]] | None = None) -> dict[str, Any]:
    return {
        "schema_version": "schuss-operation-result-v14",
        "canonical_profile": "schuss-canonical-json-v1",
        "operation": operation,
        "status": status,
        "value": copy.deepcopy(value),
        "diagnostics": sorted(diagnostics or [], key=core.diagnostic_sort_key),
    }


def dispatch_host_operation(
    request: dict[str, Any],
    context: OperationContext,
    host_render_service: HostRenderService | None,
    audio_session_service: AudioSessionService | None,
) -> dict[str, Any]:
    """Validate and dispatch one accepted Task 031 operation request."""

    schema = context.schemas.get("operation_request_v14")
    result_schema = context.schemas.get("operation_result_v14")
    operation = request.get("operation") if isinstance(request, dict) else None
    if schema is None or result_schema is None:
        raise ValueError("Task 031 operation schemas are unavailable")
    errors: list[str] = []
    try:
        core.assert_portable_json_value(request)
    except ValueError as error:
        errors.append(str(error))
    errors.extend(core.schema_errors(request, schema, schema))
    if errors:
        result = _result(
            operation if operation in result_schema["properties"]["operation"]["enum"] else "invalid-request",
            "invalid",
            None,
            [_diagnostic("OPERATION_REQUEST_INVALID", str(operation or "invalid-request"), error) for error in sorted(set(errors))],
        )
        canonical_result_bytes(result, context)
        return result
    assert isinstance(operation, str)
    payload = request["payload"]
    try:
        if operation == "host.render.start":
            if host_render_service is None:
                raise HostSessionError("HOST_RUNTIME_SERVICE_UNAVAILABLE", "the process-local host runtime service is unavailable", status="unavailable")
            value = host_render_service.start(**payload)
        elif operation == "host.render.inspect":
            if host_render_service is None:
                raise HostSessionError("HOST_RUNTIME_SERVICE_UNAVAILABLE", "the process-local host runtime service is unavailable", status="unavailable")
            value = host_render_service.inspect(payload["render_session_id"])
        elif operation == "audio.devices.inspect":
            if audio_session_service is None:
                raise HostSessionError("AUDIO_SESSION_SERVICE_UNAVAILABLE", "the process-local audio session service is unavailable", status="unavailable")
            value = audio_session_service.inspect_devices(**payload)
        elif operation == "audio.session.start":
            if audio_session_service is None:
                raise HostSessionError("AUDIO_SESSION_SERVICE_UNAVAILABLE", "the process-local audio session service is unavailable", status="unavailable")
            value = audio_session_service.start(**payload)
        elif operation == "audio.session.inspect":
            if audio_session_service is None:
                raise HostSessionError("AUDIO_SESSION_SERVICE_UNAVAILABLE", "the process-local audio session service is unavailable", status="unavailable")
            value = audio_session_service.inspect(payload["audio_session_id"])
        else:
            if audio_session_service is None:
                raise HostSessionError("AUDIO_SESSION_SERVICE_UNAVAILABLE", "the process-local audio session service is unavailable", status="unavailable")
            value = audio_session_service.stop(payload["audio_session_id"], stop_intent=payload["stop_intent"])
    except (HostSessionError, HostRuntimeError, ProjectError) as error:
        status = str(getattr(error, "status", "failed"))
        code = str(getattr(error, "code", "HOST_OPERATION_FAILED"))
        result = _result(operation, status, None, [_diagnostic(code, operation, _public_error_message(error))])
        canonical_result_bytes(result, context)
        return result
    except Exception as error:
        result = _result(operation, "failed", None, [_diagnostic("HOST_OPERATION_INTERNAL_FAILED", operation, _public_error_message(error))])
        canonical_result_bytes(result, context)
        return result
    result = _result(operation, "success", value)
    canonical_result_bytes(result, context)
    return result


__all__ = [
    "AudioSessionService",
    "EngineProtocolError",
    "HostRenderService",
    "HostSessionError",
    "SubprocessEngineTransport",
    "dispatch_host_operation",
]
