"""Task 032 variable-host render, session, and safe replacement services."""

from __future__ import annotations

import copy
import hashlib
import os
import subprocess
import tempfile
from pathlib import Path
from threading import Lock
from typing import Any, Callable, Mapping

from .audio_sessions import (
    EngineProtocolError,
    EngineTransport,
    HostSessionError,
    _public_error_message,
)
from .control_plane import (
    OperationContext,
    canonical_result_bytes,
    core,
    with_compiler_schemas,
)
from .host_runtime import HostRuntimeError
from .project_service import ProjectError, ProjectService
from .variable_host_runtime import (
    HOST_ENGINE_PROTOCOL_ABI,
    HOST_PACKAGE_SCHEMA,
    HOST_RUNTIME_ABI,
    lower_variable_host_package,
)


PROTOCOL_SCHEMA_VERSION = "host-engine-protocol-v1"
MAXIMUM_RETAINED_RENDERS = 8


def _project_reference(manifest: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "project_id": manifest["project_id"],
        "revision": manifest["revision"],
        "content_hash": manifest["content_hash"],
    }


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return core.canonical_json(dict(value)).encode("utf-8") + b"\n"


ProjectResolver = Callable[[Mapping[str, Any]], ProjectService]
TransportFactory = Callable[[], EngineTransport]
RendererRunner = Callable[[list[str]], subprocess.CompletedProcess[str]]


def _run_renderer(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


class _MessageFactory:
    def __init__(self) -> None:
        self._next_id = 1
        self._lock = Lock()

    def make(self, message_type: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        with self._lock:
            identifier = self._next_id
            self._next_id += 1
        return {
            "schema_version": PROTOCOL_SCHEMA_VERSION,
            "protocol_abi": HOST_ENGINE_PROTOCOL_ABI,
            "message_id": f"engine-message-{identifier:06d}",
            "message_type": message_type,
            "payload": copy.deepcopy(dict(payload)),
        }


class _ProjectSnapshots:
    def __init__(
        self,
        project_service: ProjectService,
        resolver: ProjectResolver | None,
    ) -> None:
        self.project_service = project_service
        self._resolver = resolver

    def exact(self, reference: Mapping[str, Any]):
        service = (
            self._resolver(reference)
            if self._resolver is not None
            else self.project_service
        )
        loaded = service.load()
        actual = _project_reference(loaded.manifest)
        if dict(reference) != actual:
            raise HostSessionError(
                "HOST_V1_PROJECT_NOT_EXACT",
                "the requested project reference is not an accepted workspace head",
                status="conflict",
            )
        context = with_compiler_schemas(loaded.context, service.repository_root)
        return service, loaded, context, actual


class VariableAudioSessionService:
    """Own one v1 native engine and one bounded active replacement lane."""

    def __init__(
        self,
        project_service: ProjectService,
        transport_factory: TransportFactory,
        *,
        project_resolver: ProjectResolver | None = None,
    ) -> None:
        self.project_service = project_service
        self._snapshots = _ProjectSnapshots(project_service, project_resolver)
        self._transport_factory = transport_factory
        self._transport: EngineTransport | None = None
        self._transport_generation = 0
        self._messages = _MessageFactory()
        self._next_id = 1
        self._sessions: dict[str, dict[str, Any]] = {}
        self._temporary = tempfile.TemporaryDirectory(prefix="schuss-audio-session-v1-")
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
                        "package_schema_version": HOST_PACKAGE_SCHEMA,
                    },
                )
            )
            if value != {
                "package_schema_version": HOST_PACKAGE_SCHEMA,
                "runtime_abi": HOST_RUNTIME_ABI,
            }:
                raise EngineProtocolError(
                    "ENGINE_HANDSHAKE_MISMATCH",
                    "the native engine handshake did not match the v1 ABIs",
                )
        except Exception:
            transport.close()
            raise
        self._transport_generation += 1
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

    def _stage(self, package: Mapping[str, Any]) -> Path:
        destination = Path(self._temporary.name) / (
            package["content_hash"].removeprefix("sha256:") + ".json"
        )
        expected = _canonical_bytes(package)
        if destination.exists():
            if destination.is_symlink() or destination.read_bytes() != expected:
                raise HostSessionError(
                    "HOST_V1_PACKAGE_STAGING_CONFLICT",
                    "the process-local package staging identity is inconsistent",
                )
        else:
            destination.write_bytes(expected)
        return destination

    @staticmethod
    def _public(session: Mapping[str, Any]) -> dict[str, Any]:
        value = copy.deepcopy(dict(session))
        value.pop("_transport_generation", None)
        return value

    def inspect_devices(self, *, inspection_intent: str) -> dict[str, Any]:
        if inspection_intent != "enumerate-local-audio-midi":
            raise HostSessionError(
                "AUDIO_DEVICE_INSPECTION_INTENT_REQUIRED",
                "explicit local audio/MIDI inspection intent is required",
                status="invalid",
            )
        value = self._request(
            "devices.inspect", {"inspection_intent": inspection_intent}
        )
        if set(value) != {"audio_devices", "midi_inputs"} or not all(
            isinstance(value[key], list) for key in value
        ):
            raise EngineProtocolError(
                "ENGINE_DEVICE_RESPONSE_INVALID",
                "the native engine returned invalid device inspection facts",
            )
        return {
            "inspection_intent": inspection_intent,
            "transport_generation": self._transport_generation,
            **copy.deepcopy(value),
            "device_action_performed": "identity-enumeration-only",
        }

    def start(
        self,
        *,
        project_reference: Mapping[str, Any],
        host_build_request_reference: Mapping[str, Any],
        sample_rate_hz: int,
        block_frames: int,
        start_intent: str,
    ) -> dict[str, Any]:
        if start_intent != "start-local-audio-session":
            raise HostSessionError(
                "AUDIO_SESSION_START_INTENT_REQUIRED",
                "explicit local audio start intent is required",
                status="invalid",
            )
        if (
            isinstance(sample_rate_hz, bool)
            or sample_rate_hz != 48000
            or isinstance(block_frames, bool)
            or not isinstance(block_frames, int)
            or not 1 <= block_frames <= 512
        ):
            raise HostSessionError(
                "AUDIO_SESSION_CONFIGURATION_UNSUPPORTED",
                "the v1 runtime accepts 48000 Hz and block sizes from 1 through 512",
                status="invalid",
            )
        with self._lock:
            if any(item["status"] == "active" for item in self._sessions.values()):
                raise HostSessionError(
                    "AUDIO_SESSION_ALREADY_ACTIVE",
                    "one process-local audio session is already active",
                    status="conflict",
                )
        _, loaded, context, snapshot = self._snapshots.exact(project_reference)
        package, _ = lower_variable_host_package(
            context,
            project_manifest=loaded.manifest,
            host_build_request_reference=host_build_request_reference,
        )
        package_path = self._stage(package)
        prepared = self._request(
            "package.prepare",
            {
                "package_path": str(package_path),
                "package_content_hash": package["content_hash"],
            },
        )
        if prepared != {
            "package_content_hash": package["content_hash"],
            "runtime_abi": HOST_RUNTIME_ABI,
        }:
            raise EngineProtocolError(
                "ENGINE_PREPARE_RESPONSE_MISMATCH",
                "the native engine did not confirm the exact v1 package",
            )
        engine = self._request(
            "session.start",
            {"sample_rate_hz": sample_rate_hz, "block_frames": block_frames},
        )
        if (
            engine.get("active") is not True
            or engine.get("package_content_hash") != package["content_hash"]
        ):
            raise EngineProtocolError(
                "ENGINE_START_RESPONSE_MISMATCH",
                "the native engine did not activate the exact v1 package",
            )
        engine_generation = engine.get("engine_generation", 1)
        if isinstance(engine_generation, bool) or not isinstance(engine_generation, int) or engine_generation < 1:
            raise EngineProtocolError(
                "ENGINE_START_RESPONSE_MISMATCH", "engine generation is invalid"
            )
        with self._lock:
            identifier = f"audio-session-{self._next_id:06d}"
            self._next_id += 1
            session = {
                "audio_session_id": identifier,
                "status": "active",
                "project_reference": snapshot,
                "host_build_request_reference": copy.deepcopy(
                    dict(host_build_request_reference)
                ),
                "package_content_hash": package["content_hash"],
                "engine_generation": engine_generation,
                "requested_configuration": {
                    "sample_rate_hz": sample_rate_hz,
                    "block_frames": block_frames,
                },
                "replacement_status": "none",
                "last_replacement": None,
                "engine": copy.deepcopy(engine),
                "authoritative_records_mutated": False,
                "_transport_generation": self._transport_generation,
            }
            self._sessions[identifier] = session
            return self._public(session)

    def _session(self, identifier: str) -> dict[str, Any]:
        session = self._sessions.get(identifier)
        if session is None:
            raise HostSessionError(
                "AUDIO_SESSION_NOT_FOUND",
                "the process-local audio session is absent or belongs to another service",
                status="unresolved",
            )
        if (
            session["_transport_generation"] != self._transport_generation
            or self._transport is None
        ):
            session["status"] = "failed"
            raise HostSessionError(
                "AUDIO_SESSION_STALE_ENGINE",
                "the audio session belongs to an expired native engine",
                status="unresolved",
            )
        return session

    def inspect(self, identifier: str) -> dict[str, Any]:
        with self._lock:
            session = self._session(identifier)
            snapshot = self._public(session)
        if snapshot["status"] != "active":
            return snapshot
        engine = self._request("session.inspect", {})
        if (
            engine.get("active") is not True
            or engine.get("package_content_hash") != snapshot["package_content_hash"]
            or engine.get("engine_generation", snapshot["engine_generation"])
            != snapshot["engine_generation"]
        ):
            raise EngineProtocolError(
                "ENGINE_SESSION_STATE_MISMATCH",
                "the native engine no longer reports the accepted active session",
            )
        with self._lock:
            session = self._session(identifier)
            session["engine"] = copy.deepcopy(engine)
            return self._public(session)

    def stop(self, identifier: str, *, stop_intent: str) -> dict[str, Any]:
        if stop_intent != "stop-local-audio-session":
            raise HostSessionError(
                "AUDIO_SESSION_STOP_INTENT_REQUIRED",
                "explicit local audio stop intent is required",
                status="invalid",
            )
        with self._lock:
            session = self._session(identifier)
            if session["status"] != "active":
                raise HostSessionError(
                    "AUDIO_SESSION_NOT_ACTIVE",
                    "the process-local audio session is not active",
                    status="conflict",
                )
            if session["replacement_status"] != "none":
                raise HostSessionError(
                    "AUDIO_REPLACEMENT_ALREADY_PENDING",
                    "a successor is already being prepared",
                    status="conflict",
                )
        engine = self._request("session.stop", {})
        if engine.get("active") is not False:
            raise EngineProtocolError(
                "ENGINE_STOP_RESPONSE_MISMATCH",
                "the native engine did not confirm a stopped session",
            )
        with self._lock:
            session = self._session(identifier)
            session["status"] = "stopped"
            session["engine"] = copy.deepcopy(engine)
            return self._public(session)

    def replace(
        self,
        *,
        audio_session_id: str,
        expected_engine_generation: int,
        expected_active_package_content_hash: str,
        successor_project_reference: Mapping[str, Any],
        successor_host_build_request_reference: Mapping[str, Any],
        replacement_intent: str,
    ) -> dict[str, Any]:
        if replacement_intent != "prepare-and-activate-next-block-reset-state":
            raise HostSessionError(
                "AUDIO_REPLACEMENT_INTENT_REQUIRED",
                "explicit next-block reset-state replacement intent is required",
                status="invalid",
            )
        with self._lock:
            session = self._session(audio_session_id)
            if session["status"] != "active":
                raise HostSessionError(
                    "AUDIO_SESSION_NOT_ACTIVE", "the audio session is not active", status="conflict"
                )
            if session["engine_generation"] != expected_engine_generation:
                raise HostSessionError(
                    "AUDIO_REPLACEMENT_GENERATION_STALE",
                    "the expected engine generation is stale",
                    status="conflict",
                )
            if session["package_content_hash"] != expected_active_package_content_hash:
                raise HostSessionError(
                    "AUDIO_REPLACEMENT_ACTIVE_HASH_STALE",
                    "the expected active package is stale",
                    status="conflict",
                )
            if session["replacement_status"] != "none":
                raise HostSessionError(
                    "AUDIO_REPLACEMENT_ALREADY_PENDING",
                    "one successor replacement is already pending",
                    status="conflict",
                )
            old_project = copy.deepcopy(session["project_reference"])
            session["replacement_status"] = "preparing"

        engine_prepared = False
        successor_hash = ""
        try:
            _, loaded, context, successor_snapshot = self._snapshots.exact(
                successor_project_reference
            )
            package, _ = lower_variable_host_package(
                context,
                project_manifest=loaded.manifest,
                host_build_request_reference=successor_host_build_request_reference,
            )
            successor_hash = package["content_hash"]
            if successor_hash == expected_active_package_content_hash:
                raise HostSessionError(
                    "AUDIO_REPLACEMENT_IDENTICAL_PACKAGE",
                    "replacement requires a distinct successor package",
                    status="invalid",
                )
            package_path = self._stage(package)
            prepared = self._request(
                "replacement.prepare",
                {
                    "audio_session_id": audio_session_id,
                    "expected_engine_generation": expected_engine_generation,
                    "expected_active_package_content_hash": expected_active_package_content_hash,
                    "successor_package_path": str(package_path),
                    "successor_package_content_hash": successor_hash,
                },
            )
            if (
                prepared.get("pending_package_content_hash") != successor_hash
                or prepared.get("active_package_content_hash")
                != expected_active_package_content_hash
                or prepared.get("engine_generation") != expected_engine_generation
                or prepared.get("runtime_abi") != HOST_RUNTIME_ABI
            ):
                raise EngineProtocolError(
                    "ENGINE_REPLACEMENT_PREPARE_MISMATCH",
                    "the engine did not retain the exact prepared successor",
                )
            engine_prepared = True
            activated = self._request(
                "replacement.activate",
                {
                    "audio_session_id": audio_session_id,
                    "expected_engine_generation": expected_engine_generation,
                    "expected_active_package_content_hash": expected_active_package_content_hash,
                    "successor_package_content_hash": successor_hash,
                    "activation_policy": "next-block-reset-state",
                },
            )
            next_generation = expected_engine_generation + 1
            if (
                activated.get("active") is not True
                or activated.get("old_package_content_hash")
                != expected_active_package_content_hash
                or activated.get("package_content_hash") != successor_hash
                or activated.get("engine_generation") != next_generation
                or activated.get("reset_state") is not True
                or activated.get("activation_boundary") != "audio-block-boundary"
                or activated.get("retired_runtime_reclaimed_off_callback") is not True
            ):
                raise EngineProtocolError(
                    "ENGINE_REPLACEMENT_ACTIVATION_MISMATCH",
                    "the engine did not report one exact block-boundary activation",
                )
            telemetry = {
                "old_project_reference": old_project,
                "new_project_reference": successor_snapshot,
                "old_package_content_hash": expected_active_package_content_hash,
                "new_package_content_hash": successor_hash,
                "activation_generation": next_generation,
                "activation_boundary": "audio-block-boundary",
                "state_policy": "reset-state",
                "retired_runtime_reclaimed_off_callback": True,
                "authoritative_records_mutated": False,
            }
            with self._lock:
                session = self._session(audio_session_id)
                if (
                    session["engine_generation"] != expected_engine_generation
                    or session["package_content_hash"]
                    != expected_active_package_content_hash
                    or session["replacement_status"] != "preparing"
                ):
                    raise HostSessionError(
                        "AUDIO_REPLACEMENT_SESSION_CHANGED",
                        "the active session changed during successor preparation",
                        status="conflict",
                    )
                session["project_reference"] = successor_snapshot
                session["host_build_request_reference"] = copy.deepcopy(
                    dict(successor_host_build_request_reference)
                )
                session["package_content_hash"] = successor_hash
                session["engine_generation"] = next_generation
                session["replacement_status"] = "none"
                session["last_replacement"] = telemetry
                session["engine"] = copy.deepcopy(activated)
                return self._public(session)
        except Exception:
            if engine_prepared:
                try:
                    self._request(
                        "replacement.cancel",
                        {
                            "audio_session_id": audio_session_id,
                            "expected_engine_generation": expected_engine_generation,
                            "expected_active_package_content_hash": expected_active_package_content_hash,
                            "successor_package_content_hash": successor_hash,
                        },
                    )
                except Exception:
                    pass
            with self._lock:
                session = self._sessions.get(audio_session_id)
                if session is not None and session["replacement_status"] == "preparing":
                    session["replacement_status"] = "none"
            raise

    def close(self) -> None:
        with self._lock:
            self._invalidate()
            for session in self._sessions.values():
                if session["status"] == "active":
                    session["status"] = "stopped"
        self._temporary.cleanup()


class VariableHostRenderService:
    """Synchronous deterministic v1 offline render sessions."""

    def __init__(
        self,
        project_service: ProjectService,
        renderer_executable: Path,
        *,
        project_resolver: ProjectResolver | None = None,
        runner: RendererRunner = _run_renderer,
    ) -> None:
        self.project_service = project_service
        self._snapshots = _ProjectSnapshots(project_service, project_resolver)
        self._renderer = Path(renderer_executable)
        self._runner = runner
        self._next_id = 1
        self._sessions: dict[str, dict[str, Any]] = {}
        self._roots: dict[str, tempfile.TemporaryDirectory[str]] = {}

    def start(
        self,
        *,
        project_reference: Mapping[str, Any],
        host_build_request_reference: Mapping[str, Any],
        render_frames: int,
        block_frames: int,
        render_intent: str,
    ) -> dict[str, Any]:
        if render_intent != "offline-render":
            raise HostSessionError(
                "HOST_RENDER_INTENT_REQUIRED",
                "explicit offline render intent is required",
                status="invalid",
            )
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
                "the renderer requires 1 through 480000 frames and blocks through 512",
                status="invalid",
            )
        if (
            not self._renderer.is_file()
            or self._renderer.is_symlink()
            or not os.access(self._renderer, os.X_OK)
        ):
            raise HostSessionError(
                "HOST_RENDERER_UNAVAILABLE",
                "the configured offline renderer is unavailable",
                status="unavailable",
            )
        _, loaded, context, snapshot = self._snapshots.exact(project_reference)
        package, _ = lower_variable_host_package(
            context,
            project_manifest=loaded.manifest,
            host_build_request_reference=host_build_request_reference,
        )
        identifier = f"host-render-{self._next_id:06d}"
        temporary = tempfile.TemporaryDirectory(prefix=identifier + "-v1-")
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
            raise HostSessionError(
                "HOST_RENDER_EXECUTION_FAILED",
                "the offline renderer did not publish complete process-local outputs",
            )
        observation = core.load_json(observation_path)
        schema = context.schemas["host_runtime_observation_v1"]
        errors = core.schema_errors(observation, schema, schema)
        wav = wav_path.read_bytes()
        if (
            errors
            or observation["content_hash"] != core.record_content_hash(observation, schema)
            or observation["package_content_hash"] != package["content_hash"]
            or observation["output"]["byte_length"] != len(wav)
            or observation["output"]["byte_sha256"] != hashlib.sha256(wav).hexdigest()
        ):
            temporary.cleanup()
            raise HostSessionError(
                "HOST_RENDER_OUTPUT_IDENTITY_MISMATCH",
                "the v1 render output does not match its observation",
            )
        self._next_id += 1
        session = {
            "render_session_id": identifier,
            "status": "success",
            "project_reference": snapshot,
            "host_build_request_reference": copy.deepcopy(
                dict(host_build_request_reference)
            ),
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
            raise HostSessionError(
                "HOST_RENDER_NOT_FOUND",
                "the process-local host render is absent or expired",
                status="unresolved",
            )
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


def _result(
    operation: str,
    status: str,
    value: dict[str, Any] | None,
    diagnostics: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "schuss-operation-result-v16",
        "canonical_profile": "schuss-canonical-json-v1",
        "operation": operation,
        "status": status,
        "value": copy.deepcopy(value),
        "diagnostics": sorted(diagnostics or [], key=core.diagnostic_sort_key),
    }


def dispatch_variable_host_operation(
    request: dict[str, Any],
    context: OperationContext,
    host_render_service: VariableHostRenderService | None,
    audio_session_service: VariableAudioSessionService | None,
) -> dict[str, Any]:
    """Validate and dispatch one accepted Task 032 operation."""

    schema = context.schemas.get("operation_request_v16")
    result_schema = context.schemas.get("operation_result_v16")
    operation = request.get("operation") if isinstance(request, dict) else None
    if schema is None or result_schema is None:
        raise ValueError("Task 032 operation schemas are unavailable")
    errors: list[str] = []
    try:
        core.assert_portable_json_value(request)
    except ValueError as error:
        errors.append(str(error))
    errors.extend(core.schema_errors(request, schema, schema))
    allowed = set(result_schema["properties"]["operation"]["enum"])
    if errors:
        result = _result(
            operation if operation in allowed else "invalid-request",
            "invalid",
            None,
            [
                _diagnostic(
                    "OPERATION_REQUEST_INVALID",
                    str(operation or "invalid-request"),
                    error,
                )
                for error in sorted(set(errors))
            ],
        )
        canonical_result_bytes(result, context)
        return result
    assert isinstance(operation, str)
    payload = request["payload"]
    try:
        if operation == "host.render.start":
            if host_render_service is None:
                raise HostSessionError(
                    "HOST_RUNTIME_SERVICE_UNAVAILABLE",
                    "the process-local host runtime service is unavailable",
                    status="unavailable",
                )
            value = host_render_service.start(**payload)
        elif operation == "host.render.inspect":
            if host_render_service is None:
                raise HostSessionError(
                    "HOST_RUNTIME_SERVICE_UNAVAILABLE",
                    "the process-local host runtime service is unavailable",
                    status="unavailable",
                )
            value = host_render_service.inspect(payload["render_session_id"])
        elif operation == "audio.devices.inspect":
            if audio_session_service is None:
                raise HostSessionError(
                    "AUDIO_SESSION_SERVICE_UNAVAILABLE",
                    "the process-local audio session service is unavailable",
                    status="unavailable",
                )
            value = audio_session_service.inspect_devices(**payload)
        elif operation == "audio.session.start":
            if audio_session_service is None:
                raise HostSessionError(
                    "AUDIO_SESSION_SERVICE_UNAVAILABLE",
                    "the process-local audio session service is unavailable",
                    status="unavailable",
                )
            value = audio_session_service.start(**payload)
        elif operation == "audio.session.inspect":
            if audio_session_service is None:
                raise HostSessionError(
                    "AUDIO_SESSION_SERVICE_UNAVAILABLE",
                    "the process-local audio session service is unavailable",
                    status="unavailable",
                )
            value = audio_session_service.inspect(payload["audio_session_id"])
        elif operation == "audio.session.replace":
            if audio_session_service is None:
                raise HostSessionError(
                    "AUDIO_SESSION_SERVICE_UNAVAILABLE",
                    "the process-local audio session service is unavailable",
                    status="unavailable",
                )
            value = audio_session_service.replace(**payload)
        else:
            if audio_session_service is None:
                raise HostSessionError(
                    "AUDIO_SESSION_SERVICE_UNAVAILABLE",
                    "the process-local audio session service is unavailable",
                    status="unavailable",
                )
            value = audio_session_service.stop(
                payload["audio_session_id"], stop_intent=payload["stop_intent"]
            )
    except (HostSessionError, HostRuntimeError, ProjectError) as error:
        result = _result(
            operation,
            str(getattr(error, "status", "failed")),
            None,
            [
                _diagnostic(
                    str(getattr(error, "code", "HOST_V1_OPERATION_FAILED")),
                    operation,
                    _public_error_message(error),
                )
            ],
        )
    except Exception as error:
        result = _result(
            operation,
            "failed",
            None,
            [
                _diagnostic(
                    "HOST_V1_OPERATION_INTERNAL_FAILED",
                    operation,
                    _public_error_message(error),
                )
            ],
        )
    else:
        result = _result(operation, "success", value)
    canonical_result_bytes(result, context)
    return result


__all__ = [
    "VariableAudioSessionService",
    "VariableHostRenderService",
    "dispatch_variable_host_operation",
]
