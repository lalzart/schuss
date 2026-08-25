"""Exact, process-local audition sessions for Schuss instrument prototypes.

The public values deliberately omit repository paths and commands.  The core
owns manifest validation, build identity checks, and direct argv-based process
creation so a presentation client cannot choose an arbitrary executable.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any, Callable

from .control_plane import OperationContext, canonical_result_bytes, core


REQUEST_SCHEMA_KEY = "operation_request_v19"
RESULT_SCHEMA_KEY = "operation_result_v19"
LIBRARY_SCHEMA_SPECS = (
    (
        "instrument_audition_library_v2",
        "instrument-audition-library-v2",
        Path(
            "research/prototype_support/instrument_library/"
            "audition-library-v2.json"
        ),
    ),
    (
        "instrument_audition_library_v1",
        "instrument-audition-library-v1",
        Path(
            "research/prototype_support/instrument_library/"
            "audition-library-v1.json"
        ),
    ),
)
LAUNCH_INTENT = "explicit-native-juce-audition"


class InstrumentLibraryError(ValueError):
    """Stable library/session failure surfaced as an operation diagnostic."""

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


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _diagnostic(
    code: str, operation: str, location: str, message: str
) -> dict[str, str]:
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
        "schema_version": "schuss-operation-result-v19",
        "canonical_profile": "schuss-canonical-json-v1",
        "operation": operation,
        "status": status,
        "value": copy.deepcopy(value),
        "diagnostics": sorted(
            diagnostics or [], key=core.diagnostic_sort_key
        ),
    }


def _default_process_factory(executable: Path) -> Any:
    return subprocess.Popen(  # noqa: S603 - executable is exact, verified authority
        [str(executable)],
        cwd=str(executable.parent),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
    )


class InstrumentLibraryService:
    """Core-owned view of one generated audition library and its exact identities."""

    def __init__(
        self,
        repository_root: Path,
        *,
        context: OperationContext,
        library_path: Path | None = None,
        process_factory: Callable[[Path], Any] | None = None,
    ) -> None:
        root = Path(repository_root)
        if not root.is_absolute():
            raise InstrumentLibraryError(
                "INSTRUMENT_REPOSITORY_ROOT_NOT_ABSOLUTE",
                "repository root must be an explicit absolute path",
                location="$.repository",
            )
        self.repository_root = root.resolve(strict=True)
        self.context = context
        self.library_path = Path(library_path) if library_path is not None else None
        self.process_factory = process_factory or _default_process_factory
        self._sessions: dict[str, dict[str, Any]] = {}
        self._next_session = 1

    def _repository_path(
        self,
        portable_path: str | Path,
        *,
        require_file: bool = False,
        require_directory: bool = False,
    ) -> Path:
        portable = PurePosixPath(str(portable_path))
        if portable.is_absolute() or ".." in portable.parts or not portable.parts:
            raise InstrumentLibraryError(
                "INSTRUMENT_LIBRARY_PATH_INVALID",
                "library paths must be portable repository-relative paths",
            )
        candidate = self.repository_root.joinpath(*portable.parts)
        cursor = self.repository_root
        for part in portable.parts:
            cursor = cursor / part
            if cursor.is_symlink():
                raise InstrumentLibraryError(
                    "INSTRUMENT_LIBRARY_SYMLINK_REJECTED",
                    "library authority and launch paths must not contain symbolic links",
                )
        try:
            resolved = candidate.resolve(strict=True)
        except FileNotFoundError:
            raise
        if not resolved.is_relative_to(self.repository_root):
            raise InstrumentLibraryError(
                "INSTRUMENT_LIBRARY_PATH_ESCAPE",
                "library path escaped the repository root",
            )
        if require_file and not resolved.is_file():
            raise InstrumentLibraryError(
                "INSTRUMENT_LIBRARY_FILE_REQUIRED",
                "library path must identify a regular file",
            )
        if require_directory and not resolved.is_dir():
            raise InstrumentLibraryError(
                "INSTRUMENT_LIBRARY_DIRECTORY_REQUIRED",
                "library path must identify a directory",
            )
        return resolved

    def _load_manifest(self) -> dict[str, Any]:
        if self.library_path is None:
            selected = next(
                (
                    (schema_key, schema_version, path)
                    for schema_key, schema_version, path in LIBRARY_SCHEMA_SPECS
                    if schema_key in self.context.schemas
                ),
                None,
            )
            if selected is None:
                raise InstrumentLibraryError(
                    "INSTRUMENT_LIBRARY_SCHEMA_UNAVAILABLE",
                    "selected record set has no instrument audition library schema",
                )
            _schema_key, _schema_version, library_path = selected
        else:
            library_path = self.library_path
        path = self._repository_path(library_path, require_file=True)
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise InstrumentLibraryError(
                "INSTRUMENT_LIBRARY_INVALID",
                f"instrument library could not be read: {exc}",
            ) from exc
        version = value.get("schema_version") if isinstance(value, dict) else None
        matching_specs = [
            (schema_key, expected_version)
            for schema_key, expected_version, _path in LIBRARY_SCHEMA_SPECS
            if expected_version == version
        ]
        if len(matching_specs) != 1 or matching_specs[0][0] not in self.context.schemas:
            raise InstrumentLibraryError(
                "INSTRUMENT_LIBRARY_SCHEMA_UNAVAILABLE",
                "selected record set does not contain the library's exact schema",
            )
        schema = self.context.schemas[matching_specs[0][0]]
        errors = core.schema_errors(value, schema, schema)
        if errors:
            raise InstrumentLibraryError(
                "INSTRUMENT_LIBRARY_INVALID",
                "; ".join(errors),
            )
        return value

    def _validated_canonical_identity(
        self, entry: dict[str, Any]
    ) -> dict[str, Any]:
        identity = copy.deepcopy(
            entry.get("canonical_identity", {"status": "not-promoted"})
        )
        if identity.get("status") == "not-promoted":
            return identity
        if identity.get("status") != "canonical":
            raise InstrumentLibraryError(
                "INSTRUMENT_CANONICAL_IDENTITY_INVALID",
                "instrument canonical identity has an unsupported status",
            )
        if identity["record_set_reference"] != self.context.record_set_reference:
            raise InstrumentLibraryError(
                "INSTRUMENT_CANONICAL_RECORD_SET_CHANGED",
                "canonical instrument identity names a different selected record set",
            )

        def resolve_exact(
            reference: dict[str, Any], group: str, identifier: str
        ) -> dict[str, Any]:
            matches = [
                value
                for value in self.context.records.get(group, ())
                if value.get(identifier) == reference[identifier]
                and value.get("revision") == reference["revision"]
                and value.get("content_hash") == reference["content_hash"]
            ]
            if len(matches) != 1:
                raise InstrumentLibraryError(
                    "INSTRUMENT_CANONICAL_REFERENCE_CHANGED",
                    "canonical instrument identity does not resolve exactly once",
                )
            return matches[0]

        graph = resolve_exact(identity["graph_reference"], "graphs", "graph_id")
        instrument = resolve_exact(
            identity["instrument_reference"],
            "performance_instruments",
            "instrument_id",
        )
        instrument_graph = {
            key: instrument["graph_reference"][key]
            for key in ("graph_id", "revision", "content_hash")
        }
        if instrument_graph != identity["graph_reference"]:
            raise InstrumentLibraryError(
                "INSTRUMENT_CANONICAL_GRAPH_CHANGED",
                "canonical instrument and library graph references disagree",
            )
        if graph.get("graph_id") != instrument_graph["graph_id"]:
            raise InstrumentLibraryError(
                "INSTRUMENT_CANONICAL_GRAPH_CHANGED",
                "canonical graph identity is inconsistent",
            )
        return identity

    def _validated_entry(self, entry: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        prototype_path = self._repository_path(
            entry["prototype_index"]["path"], require_file=True
        )
        result_path = self._repository_path(
            entry["result_evidence"]["path"], require_file=True
        )
        if _sha256_file(prototype_path) != entry["prototype_index"]["byte_sha256"]:
            raise InstrumentLibraryError(
                "INSTRUMENT_PROTOTYPE_AUTHORITY_CHANGED",
                f"prototype authority changed for {entry['prototype_id']} {entry['revision']}",
            )
        if _sha256_file(result_path) != entry["result_evidence"]["byte_sha256"]:
            raise InstrumentLibraryError(
                "INSTRUMENT_RESULT_EVIDENCE_CHANGED",
                f"result evidence changed for {entry['prototype_id']} {entry['revision']}",
            )
        try:
            prototype = json.loads(prototype_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise InstrumentLibraryError(
                "INSTRUMENT_PROTOTYPE_AUTHORITY_INVALID",
                f"prototype authority could not be read: {exc}",
            ) from exc
        if (
            prototype.get("prototype_id") != entry["prototype_id"]
            or prototype.get("revision") != entry["revision"]
        ):
            raise InstrumentLibraryError(
                "INSTRUMENT_PROTOTYPE_IDENTITY_MISMATCH",
                "library identity does not match its exact prototype authority",
            )
        claims = prototype.get("claims")
        if not isinstance(claims, dict) or claims.get("canonical_schuss_record") is not False:
            raise InstrumentLibraryError(
                "INSTRUMENT_PROTOTYPE_CLAIMS_INVALID",
                "audition entries must remain explicitly noncanonical",
            )
        if claims.get("production_ready") is not False:
            raise InstrumentLibraryError(
                "INSTRUMENT_PROTOTYPE_CLAIMS_INVALID",
                "audition entries must not claim production readiness",
            )
        return entry, prototype

    def _launch_status(self, entry: dict[str, Any]) -> tuple[str, Path | None, str | None]:
        launch = entry["launch"]
        if launch is None:
            return "research-only", None, None
        expected = launch["expected_executable"]
        if expected["status"] == "unresolved":
            return "build-required", None, None
        if not launch["bundle_path"].startswith("build/") or not launch[
            "executable_path"
        ].startswith("build/"):
            raise InstrumentLibraryError(
                "INSTRUMENT_LAUNCH_PATH_INVALID",
                "native audition targets must remain under the repository build directory",
            )
        try:
            bundle = self._repository_path(
                launch["bundle_path"], require_directory=True
            )
            executable = self._repository_path(
                launch["executable_path"], require_file=True
            )
        except FileNotFoundError:
            return "build-required", None, None
        if not executable.is_relative_to(bundle):
            raise InstrumentLibraryError(
                "INSTRUMENT_EXECUTABLE_OUTSIDE_BUNDLE",
                "native audition executable must be contained by its exact application bundle",
            )
        actual = _sha256_file(executable)
        if actual != expected["sha256"]:
            return "stale-build", None, actual
        if not os.access(executable, os.X_OK):
            return "build-required", None, actual
        return "verified-local-build", executable, actual

    def _library_entries(
        self,
    ) -> tuple[dict[str, Any], list[tuple[dict[str, Any], Path | None]]]:
        manifest = self._load_manifest()
        entries: list[tuple[dict[str, Any], Path | None]] = []
        identities: set[tuple[str, str]] = set()
        for source in manifest["entries"]:
            entry, prototype = self._validated_entry(source)
            identity = (entry["prototype_id"], entry["revision"])
            if identity in identities:
                raise InstrumentLibraryError(
                    "INSTRUMENT_LIBRARY_IDENTITY_AMBIGUOUS",
                    "each exact prototype identity must appear once",
                    status="ambiguous",
                )
            identities.add(identity)
            availability, executable, actual_hash = self._launch_status(entry)
            summary = {
                "prototype_id": entry["prototype_id"],
                "revision": entry["revision"],
                "display_name": entry["display_name"],
                "summary": entry["summary"],
                "controller_label": entry["controller_label"],
                "lane": prototype["lane"],
                "canonical_identity": self._validated_canonical_identity(entry),
                "availability": availability,
                "launchable": availability == "verified-local-build",
                "evidence": {
                    "application_launch": "not-evaluated",
                    "listening": "not-evaluated",
                    "physical_controller": "not-evaluated",
                },
            }
            if availability == "verified-local-build":
                summary["executable_sha256"] = actual_hash
            entries.append((summary, executable))
        entries.sort(
            key=lambda item: (
                item[0]["display_name"].casefold(),
                item[0]["prototype_id"],
                item[0]["revision"],
            )
        )
        return manifest, entries

    def list_instruments(self) -> dict[str, Any]:
        manifest, validated_entries = self._library_entries()
        entries = [summary for summary, _executable in validated_entries]
        return {
            "library_id": manifest["library_id"],
            "library_revision": manifest["revision"],
            "claims": copy.deepcopy(manifest["claims"]),
            "instrument_count": len(entries),
            "instruments": entries,
        }

    def start(self, payload: dict[str, Any]) -> dict[str, Any]:
        identity = (payload["prototype_id"], payload["revision"])
        if payload["launch_intent"] != LAUNCH_INTENT:
            raise InstrumentLibraryError(
                "INSTRUMENT_LAUNCH_INTENT_REQUIRED",
                "native audition requires the exact explicit launch intent",
                location="$.payload.launch_intent",
            )
        _manifest, entries = self._library_entries()
        matches = [
            (summary, executable)
            for summary, executable in entries
            if (summary["prototype_id"], summary["revision"]) == identity
        ]
        if len(matches) != 1:
            raise InstrumentLibraryError(
                "INSTRUMENT_PROTOTYPE_NOT_FOUND",
                "exact prototype identity is absent from the audition library",
                status="unresolved",
            )
        summary, executable = matches[0]
        if not summary["launchable"] or executable is None:
            raise InstrumentLibraryError(
                "INSTRUMENT_BUILD_UNAVAILABLE",
                f"instrument is not launchable: {summary['availability']}",
                status="unavailable",
            )
        for session in self._sessions.values():
            if session["identity"] == identity and session["process"].poll() is None:
                raise InstrumentLibraryError(
                    "INSTRUMENT_SESSION_ALREADY_RUNNING",
                    "this exact instrument already has a running audition session",
                    status="conflict",
                )
        process = self.process_factory(executable)
        session_id = f"instrument-session-{self._next_session:06d}"
        self._next_session += 1
        self._sessions[session_id] = {
            "identity": identity,
            "process": process,
            "summary": copy.deepcopy(summary),
        }
        return self.inspect(session_id)

    def inspect(self, session_id: str) -> dict[str, Any]:
        session = self._sessions.get(session_id)
        if session is None:
            raise InstrumentLibraryError(
                "INSTRUMENT_SESSION_NOT_FOUND",
                "instrument session is unknown to this process",
                status="unresolved",
                location="$.payload.instrument_session_id",
            )
        return_code = session["process"].poll()
        summary = session["summary"]
        value = {
            "instrument_session_id": session_id,
            "prototype_id": summary["prototype_id"],
            "revision": summary["revision"],
            "display_name": summary["display_name"],
            "status": "running" if return_code is None else "exited",
            "executable_sha256": summary["executable_sha256"],
        }
        if return_code is not None:
            value["exit_code"] = return_code
        return value


def dispatch_instrument_operation(
    request: dict[str, Any],
    context: OperationContext,
    service: InstrumentLibraryService | None,
) -> dict[str, Any]:
    """Validate and dispatch one v19 instrument library operation."""

    operation = request.get("operation") if isinstance(request, dict) else None
    required = (REQUEST_SCHEMA_KEY, RESULT_SCHEMA_KEY)
    missing = sorted(name for name in required if name not in context.schemas)
    if not any(
        schema_key in context.schemas
        for schema_key, _schema_version, _path in LIBRARY_SCHEMA_SPECS
    ):
        missing.append("instrument_audition_library_v1_or_v2")
    if missing:
        result = _result(
            "invalid-request",
            "invalid",
            None,
            [
                _diagnostic(
                    "INSTRUMENT_SCHEMA_UNAVAILABLE",
                    str(operation or "invalid-request"),
                    "$",
                    "selected context is missing instrument schema keys: "
                    + ", ".join(missing),
                )
            ],
        )
        canonical_result_bytes(result, context)
        return result
    errors: list[str] = []
    try:
        core.assert_portable_json_value(request)
    except ValueError as exc:
        errors.append(str(exc))
    schema = context.schemas[REQUEST_SCHEMA_KEY]
    if isinstance(request, dict):
        errors.extend(core.schema_errors(request, schema, schema))
    else:
        errors.append("$: operation request must be an object")
    if errors:
        valid_operations = {
            "instrument.library.list",
            "instrument.session.inspect",
            "instrument.session.start",
        }
        result = _result(
            operation if operation in valid_operations else "invalid-request",
            "invalid",
            None,
            [
                _diagnostic(
                    "OPERATION_REQUEST_INVALID",
                    str(operation or "invalid-request"),
                    "$",
                    error,
                )
                for error in sorted(set(errors))
            ],
        )
        canonical_result_bytes(result, context)
        return result
    if service is None:
        result = _result(
            str(operation),
            "unavailable",
            None,
            [
                _diagnostic(
                    "INSTRUMENT_LIBRARY_SERVICE_REQUIRED",
                    str(operation),
                    "$",
                    "instrument operations require a process-local library service",
                )
            ],
        )
        canonical_result_bytes(result, context)
        return result
    try:
        payload = request["payload"]
        if operation == "instrument.library.list":
            value = service.list_instruments()
        elif operation == "instrument.session.start":
            value = service.start(payload)
        else:
            value = service.inspect(payload["instrument_session_id"])
    except Exception as exc:
        code = str(getattr(exc, "code", "INSTRUMENT_OPERATION_FAILED"))
        status = str(getattr(exc, "status", "failed"))
        location = str(getattr(exc, "location", "$.payload"))
        result = _result(
            str(operation),
            status,
            None,
            [_diagnostic(code, str(operation), location, str(exc))],
        )
        canonical_result_bytes(result, context)
        return result
    result = _result(str(operation), "success", value)
    canonical_result_bytes(result, context)
    return result
