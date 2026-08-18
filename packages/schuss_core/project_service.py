"""Durable Task 012A project/workspace service.

The service owns portable project loading, exact base-plus-overlay validation,
exclusive local coordination, deterministic write planning, atomic publication,
and recovery.  CLI and process adapters only construct requests and render the
shared operation results.
"""

from __future__ import annotations

import copy
import hashlib
import os
import re
from collections import OrderedDict
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Callable, Iterable

from .control_plane import (
    OperationContext,
    REPOSITORY_ROOT,
    _diagnostic,
    dispatch_operation,
    load_repository_context,
    transact_graph_payload,
    with_compiler_schemas,
)

from .control_plane import aggregate, component, core, device, record_set_rules, target


PROJECT_SCHEMA = "project-v0.schema.json"
HEAD_SCHEMA = "workspace-head-v0.schema.json"
WRITE_PLAN_SCHEMA = "project-write-plan-v0.schema.json"
WRITE_PLAN_V1_SCHEMA = "project-write-plan-v1.schema.json"
LOCK_SCHEMA = "workspace-lock-v0.schema.json"
RECOVERY_SCHEMA = "workspace-recovery-v0.schema.json"
REQUEST_SCHEMA = "operation-request-v3.schema.json"
RESULT_SCHEMA = "operation-result-v3.schema.json"
REQUEST_V8_SCHEMA = "operation-request-v8.schema.json"
RESULT_V8_SCHEMA = "operation-result-v8.schema.json"
RESULT_V11_SCHEMA = "operation-result-v11.schema.json"
DEFAULT_SEMANTIC_CACHE_SIZE = 8

TASK012A_SCHEMA_NAMES = {
    "project": PROJECT_SCHEMA,
    "workspace_head": HEAD_SCHEMA,
    "project_write_plan": WRITE_PLAN_SCHEMA,
    "project_write_plan_v1": WRITE_PLAN_V1_SCHEMA,
    "workspace_lock": LOCK_SCHEMA,
    "workspace_recovery": RECOVERY_SCHEMA,
    "operation_request_v3": REQUEST_SCHEMA,
    "operation_result_v3": RESULT_SCHEMA,
    "operation_request_v8": REQUEST_V8_SCHEMA,
    "operation_result_v8": RESULT_V8_SCHEMA,
}

HEAD_LOCATOR = "schuss-project.json"
LOCK_LOCATOR = ".schuss/lock.json"
RECOVERY_LOCATOR = ".schuss/recovery/pending.json"
TMP_LOCATOR = ".schuss/tmp"

PORTABLE_LOCATOR_RE = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]*(?:/[A-Za-z0-9][A-Za-z0-9._-]*)*$"
)
WORKSPACE_LOCATOR_RE = re.compile(
    r"^(?:[A-Za-z0-9][A-Za-z0-9._-]*|\.schuss)"
    r"(?:/[A-Za-z0-9][A-Za-z0-9._-]*)*$"
)

OWNED_KIND_FIELDS = {
    "dsp-graph": ("graphs", "graph_id"),
    "instrument": ("instruments", "instrument_id"),
    "build-request": ("request", "build_request_id"),
}


class ProjectError(ValueError):
    """Stable project/workspace failure surfaced as one operation diagnostic."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        status: str = "invalid",
        subject: str = "project-workspace",
        location: str = "$",
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status = status
        self.subject = subject
        self.location = location


class ProjectTransactionRejected(Exception):
    """Existing graph.transact rejected before persistence began."""

    def __init__(self, result: dict[str, Any]) -> None:
        super().__init__(result["status"])
        self.result = result


@dataclass(frozen=True)
class LoadedProject:
    head: dict[str, Any]
    manifest: dict[str, Any]
    context: OperationContext
    project_records: dict[str, tuple[dict[str, Any], ...]]
    validation: dict[str, Any]
    recovery_status: str
    head_bytes: bytes
    manifest_bytes: bytes


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _project_reference(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "project_id": manifest["project_id"],
        "revision": manifest["revision"],
        "content_hash": manifest["content_hash"],
    }


def _graph_reference(graph: dict[str, Any]) -> dict[str, Any]:
    return {
        "graph_id": graph["graph_id"],
        "revision": graph["revision"],
        "content_hash": graph["content_hash"],
    }


def _instrument_reference(instrument: dict[str, Any]) -> dict[str, Any]:
    return {
        "instrument_id": instrument["instrument_id"],
        "revision": instrument["revision"],
        "content_hash": instrument["content_hash"],
    }


def _build_request_reference(request: dict[str, Any]) -> dict[str, Any]:
    return {
        "build_request_id": request["build_request_id"],
        "revision": request["revision"],
        "content_hash": request["content_hash"],
    }


def _member_key(member: dict[str, Any]) -> tuple[str, str, int, str]:
    return (
        member["record_kind"],
        member["stable_id"],
        member["revision"],
        member["content_hash"],
    )


def _member_revision_key(member: dict[str, Any]) -> tuple[str, str, int]:
    return _member_key(member)[:3]


def _byte_state(data: bytes) -> dict[str, Any]:
    return {
        "status": "present",
        "byte_length": len(data),
        "byte_sha256": _sha256_bytes(data),
    }


def _new_byte_state(data: bytes) -> dict[str, Any]:
    return {
        "byte_length": len(data),
        "byte_sha256": _sha256_bytes(data),
    }


def _schema_value_bytes(value: dict[str, Any], schema: dict[str, Any]) -> bytes:
    errors = core.schema_errors(value, schema, schema)
    if errors:
        raise ProjectError(
            "PROJECT_SCHEMA_INVALID",
            "; ".join(errors),
        )
    if schema.get("$id") in {
        RECOVERY_SCHEMA,
        RESULT_SCHEMA,
        RESULT_V8_SCHEMA,
        RESULT_V11_SCHEMA,
    }:
        canonical = copy.deepcopy(value)
    else:
        canonical = core.canonicalize_with_schema(value, schema, schema)
    return core.canonical_json(canonical).encode("utf-8") + b"\n"


def _record_value_bytes(value: dict[str, Any], schema: dict[str, Any]) -> bytes:
    value = copy.deepcopy(value)
    value["content_hash"] = core.record_content_hash(value, schema)
    return _schema_value_bytes(value, schema)


def with_project_schemas(
    context: OperationContext,
    repository_root: Path = REPOSITORY_ROOT,
) -> OperationContext:
    """Return a context with additive Task 012A schemas; base membership is unchanged."""

    schemas = dict(context.schemas)
    schema_root = repository_root / "schemas"
    for key, filename in TASK012A_SCHEMA_NAMES.items():
        schema = core.load_json(schema_root / filename)
        annotations = core.validate_schema_annotations(schema)
        if annotations:
            raise ProjectError(
                "PROJECT_SCHEMA_INVALID",
                f"{filename}: {annotations}",
            )
        schemas[key] = schema
    return with_compiler_schemas(
        replace(context, schemas=schemas), repository_root
    )


def _operation_result(
    operation: str,
    status: str,
    value: dict[str, Any] | None,
    diagnostics: Iterable[dict[str, str]] = (),
    *,
    version: int = 3,
) -> dict[str, Any]:
    ordered = [copy.deepcopy(item) for item in diagnostics]
    ordered.sort(key=core.diagnostic_sort_key)
    return {
        "schema_version": f"schuss-operation-result-v{version}",
        "canonical_profile": "schuss-canonical-json-v1",
        "operation": operation,
        "status": status,
        "value": copy.deepcopy(value),
        "diagnostics": ordered,
    }


class ProjectService:
    """Client-neutral project/workspace service used by every Task 012A client."""

    def __init__(
        self,
        workspace: Path,
        *,
        repository_root: Path = REPOSITORY_ROOT,
        initial_context: OperationContext | None = None,
        failure_injector: Callable[[str], None] | None = None,
        pid_provider: Callable[[], int] = os.getpid,
        process_alive: Callable[[int], bool] | None = None,
        semantic_cache_size: int = DEFAULT_SEMANTIC_CACHE_SIZE,
    ) -> None:
        if (
            isinstance(semantic_cache_size, bool)
            or not isinstance(semantic_cache_size, int)
            or semantic_cache_size < 0
        ):
            raise ValueError("semantic cache size must be a non-negative integer")
        self.workspace = Path(workspace).absolute()
        self.repository_root = Path(repository_root).resolve()
        self.failure_injector = failure_injector
        self.pid_provider = pid_provider
        self.process_alive = process_alive or self._default_process_alive
        prepared_context = (
            with_project_schemas(initial_context, self.repository_root)
            if initial_context is not None
            else None
        )
        self._context = prepared_context
        self._base_context = prepared_context
        self._base_loaded = (
            prepared_context.loaded_record_set
            if prepared_context is not None
            else None
        )
        self._base_record_set_path = (
            prepared_context.record_set_path
            if prepared_context is not None
            else None
        )
        self._semantic_cache_size = semantic_cache_size
        self._semantic_cache: OrderedDict[
            tuple[str, ...], tuple[OperationContext, dict[str, Any]]
        ] = OrderedDict()
        self._cache_metrics = {
            "base_loads": 0,
            "base_reuses": 0,
            "semantic_hits": 0,
            "semantic_misses": 0,
            "semantic_evictions": 0,
        }
        self._recovery_status = "not-needed"

    @property
    def context(self) -> OperationContext:
        if self._context is None:
            self._context = with_project_schemas(
                load_repository_context(self.repository_root), self.repository_root
            )
            self._base_context = self._context
            self._base_loaded = self._context.loaded_record_set
            self._base_record_set_path = self._context.record_set_path
        return self._context

    @property
    def cache_metrics(self) -> dict[str, int]:
        """Return private-process cache evidence without exposing semantic state."""

        return {
            **self._cache_metrics,
            "semantic_entries": len(self._semantic_cache),
            "semantic_capacity": self._semantic_cache_size,
        }

    @staticmethod
    def _default_process_alive(pid: int) -> bool:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True

    def _inject(self, boundary: str) -> None:
        if self.failure_injector is not None:
            self.failure_injector(boundary)

    def _safe_workspace_path(self, locator: str) -> Path:
        if not WORKSPACE_LOCATOR_RE.fullmatch(locator):
            raise ProjectError(
                "PROJECT_LOCATOR_INVALID",
                "workspace locator is not normalized and portable",
                subject=locator or "empty-locator",
            )
        candidate = self.workspace.joinpath(*locator.split("/"))
        current = self.workspace
        for part in locator.split("/"):
            current = current / part
            if current.is_symlink():
                raise ProjectError(
                    "PROJECT_SYMLINK_ESCAPE",
                    "workspace governed paths may not traverse symlinks",
                    subject=locator,
                )
        workspace_resolved = self.workspace.resolve(strict=False)
        try:
            candidate.resolve(strict=False).relative_to(workspace_resolved)
        except ValueError as exc:
            raise ProjectError(
                "PROJECT_PATH_ESCAPE",
                "workspace locator escapes the selected workspace",
                subject=locator,
            ) from exc
        return candidate

    def _repository_path(self, locator: str) -> Path:
        if not PORTABLE_LOCATOR_RE.fullmatch(locator):
            raise ProjectError(
                "PROJECT_BASE_LOCATOR_INVALID",
                "base record-set locator is not normalized and portable",
                subject=locator or "empty-locator",
            )
        path = self.repository_root.joinpath(*locator.split("/"))
        current = self.repository_root
        for part in locator.split("/"):
            current = current / part
            if current.is_symlink():
                raise ProjectError(
                    "PROJECT_BASE_SYMLINK_INVALID",
                    "base record-set locator may not traverse a symlink",
                    subject=locator,
                )
        try:
            path.resolve(strict=False).relative_to(self.repository_root)
        except ValueError as exc:
            raise ProjectError(
                "PROJECT_BASE_LOCATOR_INVALID",
                "base record-set locator escapes the Schuss installation",
                subject=locator,
            ) from exc
        return path

    def _mkdir(self, path: Path, label: str) -> None:
        if path.exists():
            if path.is_symlink() or not path.is_dir():
                raise ProjectError(
                    "PROJECT_WORKSPACE_LAYOUT_INVALID",
                    "workspace directory is missing or replaced by a non-directory",
                    subject=path.name,
                )
            return
        self._inject(f"before:{label}.mkdir")
        path.mkdir(parents=True, exist_ok=False)
        self._inject(f"after:{label}.mkdir")

    def _prepare_layout(self) -> None:
        self._mkdir(self.workspace, "workspace")
        for locator, label in (
            ("project/revisions", "project-revisions"),
            ("records/dsp-graphs", "graph-records"),
            ("records/instruments", "instrument-records"),
            ("records/build-requests", "build-request-records"),
            ("assets", "assets"),
            (TMP_LOCATOR, "temporary-state"),
            (".schuss/recovery", "recovery-state"),
        ):
            self._mkdir(self._safe_workspace_path(locator), label)

    def _temp_path(self, label: str, data: bytes) -> Path:
        token = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")
        return self._safe_workspace_path(
            f"{TMP_LOCATOR}/{token}-{_sha256_bytes(data)}.tmp"
        )

    def _atomic_write(
        self,
        target: Path,
        data: bytes,
        *,
        label: str,
        replace_target: bool,
        allow_identical: bool = False,
        expected_old: bytes | None = None,
    ) -> None:
        if target.is_symlink():
            raise ProjectError(
                "PROJECT_SYMLINK_ESCAPE",
                "atomic write target is a symlink",
                subject=target.name,
            )
        if target.exists() and not replace_target:
            if allow_identical and target.read_bytes() == data:
                return
            raise ProjectError(
                "PROJECT_EXPECTED_ABSENT_CHANGED",
                "immutable write target already exists",
                status="conflict",
                subject=target.name,
            )
        temp = self._temp_path(label, data)
        if temp.exists():
            raise ProjectError(
                "PROJECT_TEMP_STATE_AMBIGUOUS",
                "deterministic temporary path already exists without owned recovery state",
                subject=temp.name,
            )
        self._inject(f"before:{label}.temp-create")
        with temp.open("xb") as handle:
            midpoint = max(1, len(data) // 2)
            handle.write(data[:midpoint])
            handle.flush()
            self._inject(f"during:{label}.temp-write")
            handle.write(data[midpoint:])
            handle.flush()
            os.fsync(handle.fileno())
        self._inject(f"after:{label}.temp-fsync")
        if replace_target:
            self._inject(f"before:{label}.publish")
            if expected_old is not None and (
                not target.is_file()
                or target.is_symlink()
                or target.read_bytes() != expected_old
            ):
                raise ProjectError(
                    "PROJECT_EXPECTED_OLD_BYTES_CHANGED",
                    "acceptance marker changed after the write plan was prepared",
                    status="conflict",
                    subject=target.name,
                )
            os.replace(temp, target)
            self._inject(f"after:{label}.publish")
        else:
            self._inject(f"before:{label}.publish")
            try:
                os.link(temp, target)
            except FileExistsError as exc:
                raise ProjectError(
                    "PROJECT_EXPECTED_ABSENT_CHANGED",
                    "immutable target appeared during publication",
                    status="conflict",
                    subject=target.name,
                ) from exc
            self._inject(f"after:{label}.publish")
            self._inject(f"before:{label}.temp-remove")
            temp.unlink()
            self._inject(f"after:{label}.temp-remove")
        try:
            directory_fd = os.open(target.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except OSError:
            pass

    def _unlink(self, path: Path, label: str) -> None:
        if not path.exists():
            return
        if path.is_symlink():
            raise ProjectError(
                "PROJECT_SYMLINK_ESCAPE",
                "local state path is a symlink",
                subject=path.name,
            )
        self._inject(f"before:{label}.remove")
        path.unlink()
        self._inject(f"after:{label}.remove")

    def _load_base(
        self, base: dict[str, Any]
    ) -> tuple[OperationContext, record_set_rules.LoadedRecordSet]:
        path = self._repository_path(base["portable_locator"]).resolve()
        if (
            self._base_context is not None
            and self._base_loaded is not None
            and self._base_record_set_path == path
            and self._base_context.record_set_reference == base["reference"]
        ):
            self._cache_metrics["base_reuses"] += 1
            return self._base_context, self._base_loaded
        try:
            context = load_repository_context(
                self.repository_root,
                record_set_path=path,
            )
        except (OSError, ValueError) as exc:
            raise ProjectError(
                "PROJECT_BASE_RECORD_SET_INVALID",
                str(exc),
                subject=base["portable_locator"],
            ) from exc
        if context.record_set_reference != base["reference"]:
            raise ProjectError(
                "PROJECT_BASE_RECORD_SET_STALE",
                "base record-set locator does not resolve to the pinned exact reference",
                subject=base["portable_locator"],
            )
        context = with_project_schemas(context, self.repository_root)
        loaded = context.loaded_record_set
        self._cache_metrics["base_loads"] += 1
        self._base_context = context
        self._base_loaded = loaded
        self._base_record_set_path = context.record_set_path
        self._context = context
        return context, loaded

    @staticmethod
    def _exact_match(
        records: Iterable[dict[str, Any]],
        reference: dict[str, Any],
        id_field: str,
    ) -> dict[str, Any] | None:
        matches = [
            item
            for item in records
            if item.get(id_field) == reference.get(id_field)
            and item.get("revision") == reference.get("revision")
            and item.get("content_hash") == reference.get("content_hash")
        ]
        return matches[0] if len(matches) == 1 else None

    def _validate_init_references(
        self, payload: dict[str, Any], context: OperationContext
    ) -> None:
        if self._exact_match(
            context.records["graphs"], payload["primary_graph_reference"], "graph_id"
        ) is None:
            raise ProjectError(
                "PROJECT_PRIMARY_GRAPH_UNRESOLVED",
                "primary graph is absent from the exact immutable base",
                location="$.payload.primary_graph_reference",
            )
        for location, group, id_field in (
            ("instrument_references", "instruments", "instrument_id"),
            ("build_request_references", "request", "build_request_id"),
        ):
            for reference in payload[location]:
                if self._exact_match(context.records[group], reference, id_field) is None:
                    raise ProjectError(
                        "PROJECT_INCLUDED_REFERENCE_UNRESOLVED",
                        "included reference is absent from the exact immutable base",
                        location=f"$.payload.{location}",
                    )

    def _project_manifest_locator(self, project_id: str, revision: int) -> str:
        return f"project/revisions/{project_id}-r{revision:06d}.json"

    def _graph_locator(self, graph_id: str, revision: int) -> str:
        return f"records/dsp-graphs/{graph_id}-r{revision:06d}.json"

    def _instrument_locator(self, instrument_id: str, revision: int) -> str:
        return f"records/instruments/{instrument_id}-r{revision:06d}.json"

    def _build_request_locator(self, request_id: str, revision: int) -> str:
        return f"records/build-requests/{request_id}-r{revision:06d}.json"

    def _read_schema_value(
        self, locator: str, schema: dict[str, Any]
    ) -> tuple[dict[str, Any], bytes]:
        path = self._safe_workspace_path(locator)
        if path.is_symlink():
            raise ProjectError(
                "PROJECT_SYMLINK_ESCAPE",
                "governed file locator resolves through a symlink",
                subject=locator,
            )
        if not path.is_file():
            raise ProjectError(
                "PROJECT_GOVERNED_FILE_MISSING",
                "governed file is missing or is not a regular file",
                subject=locator,
            )
        data = path.read_bytes()
        try:
            value = core.load_json_bytes(data, locator, require_final_lf=True)
        except ValueError as exc:
            raise ProjectError(
                "PROJECT_GOVERNED_FILE_INVALID",
                str(exc),
                subject=locator,
            ) from exc
        if not isinstance(value, dict):
            raise ProjectError(
                "PROJECT_GOVERNED_FILE_INVALID",
                "governed JSON value must be an object",
                subject=locator,
            )
        errors = core.schema_errors(value, schema, schema)
        if errors:
            raise ProjectError(
                "PROJECT_GOVERNED_FILE_INVALID",
                "; ".join(errors),
                subject=locator,
            )
        expected = _schema_value_bytes(value, schema)
        if data != expected:
            raise ProjectError(
                "PROJECT_GOVERNED_BYTES_NONCANONICAL",
                "governed file bytes are not canonical",
                subject=locator,
            )
        return value, data

    def _load_project_history(
        self, head: dict[str, Any]
    ) -> tuple[list[dict[str, Any]], list[bytes], set[str]]:
        schema = self.context.schemas["project"]
        reference = head["accepted_project_reference"]
        expected_locator = self._project_manifest_locator(
            reference["project_id"], reference["revision"]
        )
        if head["project_manifest_locator"] != expected_locator:
            raise ProjectError(
                "PROJECT_HEAD_LOCATOR_MISMATCH",
                "workspace head does not use the canonical project-revision locator",
                subject=HEAD_LOCATOR,
            )
        history: list[dict[str, Any]] = []
        history_bytes: list[bytes] = []
        locators: set[str] = set()
        expected_reference = copy.deepcopy(reference)
        for revision in range(reference["revision"], 0, -1):
            locator = self._project_manifest_locator(reference["project_id"], revision)
            manifest, data = self._read_schema_value(locator, schema)
            if manifest["content_hash"] != core.record_content_hash(manifest, schema):
                raise ProjectError(
                    "PROJECT_CONTENT_HASH_MISMATCH",
                    "project manifest content hash is stale",
                    subject=locator,
                )
            if _project_reference(manifest) != expected_reference:
                raise ProjectError(
                    "PROJECT_PARENT_REFERENCE_MISMATCH",
                    "project revision does not match its exact child/head reference",
                    subject=locator,
                )
            history.append(manifest)
            history_bytes.append(data)
            locators.add(locator)
            parent = manifest["parent_reference"]
            if revision == 1:
                if parent != {"status": "omitted"}:
                    raise ProjectError(
                        "PROJECT_ROOT_PARENT_INVALID",
                        "project revision 1 must omit its parent",
                        subject=locator,
                    )
            else:
                expected_reference = {
                    "project_id": parent.get("project_id"),
                    "revision": parent.get("revision"),
                    "content_hash": parent.get("content_hash"),
                }
                if parent.get("status") != "included" or expected_reference["revision"] != revision - 1:
                    raise ProjectError(
                        "PROJECT_PARENT_REFERENCE_MISMATCH",
                        "successor project must name the immediately preceding exact revision",
                        subject=locator,
                    )
        history.reverse()
        history_bytes.reverse()
        for previous, successor in zip(history, history[1:]):
            previous_members = {_member_key(item) for item in previous["owned_members"]}
            successor_members = {_member_key(item) for item in successor["owned_members"]}
            if not previous_members <= successor_members:
                raise ProjectError(
                    "PROJECT_OWNED_HISTORY_REWRITTEN",
                    "successor project omits or changes a previously owned member",
                    subject=successor["project_id"],
                )
            if successor["base_record_set"] != previous["base_record_set"]:
                raise ProjectError(
                    "PROJECT_BASE_RECORD_SET_CHANGED",
                    "project successor changes the immutable base record set",
                    subject=successor["project_id"],
                )
        return history, history_bytes, locators

    def _load_owned_records(
        self,
        manifest: dict[str, Any],
        base: record_set_rules.LoadedRecordSet,
    ) -> tuple[dict[str, tuple[dict[str, Any], ...]], set[str]]:
        base_revisions = {
            (item["record_kind"], item["stable_id"], item["revision"]): item
            for item in base.manifest["record_members"]
        }
        owned_by_revision: dict[tuple[str, str, int], dict[str, Any]] = {}
        records: dict[str, list[dict[str, Any]]] = {
            kind: [] for kind in OWNED_KIND_FIELDS
        }
        locators: set[str] = set()
        for member in manifest["owned_members"]:
            revision_key = _member_revision_key(member)
            if revision_key in owned_by_revision:
                raise ProjectError(
                    "PROJECT_OWNED_IDENTITY_DUPLICATE",
                    "project-owned stable ID/revision is duplicated",
                    subject=member["stable_id"],
                )
            if revision_key in base_revisions:
                raise ProjectError(
                    "PROJECT_BASE_OVERLAY_COLLISION",
                    "project-owned member collides with immutable base identity",
                    subject=member["stable_id"],
                )
            schema = base.schemas.get(member["schema_version"])
            if schema is None:
                raise ProjectError(
                    "PROJECT_OWNED_SCHEMA_UNAVAILABLE",
                    "project-owned member schema is absent from the immutable base",
                    subject=member["schema_version"],
                )
            record, data = self._read_schema_value(member["portable_locator"], schema)
            if member["byte_sha256"] != _sha256_bytes(data):
                raise ProjectError(
                    "PROJECT_OWNED_BYTE_HASH_MISMATCH",
                    "project-owned member byte hash is stale",
                    subject=member["portable_locator"],
                )
            if record.get("content_hash") != member["content_hash"] or core.record_content_hash(record, schema) != member["content_hash"]:
                raise ProjectError(
                    "PROJECT_OWNED_CONTENT_HASH_MISMATCH",
                    "project-owned member semantic hash is stale",
                    subject=member["portable_locator"],
                )
            _, id_field = OWNED_KIND_FIELDS[member["record_kind"]]
            if (
                record.get(id_field) != member["stable_id"]
                or record.get("revision") != member["revision"]
                or record.get("schema_version") != member["schema_version"]
            ):
                raise ProjectError(
                    "PROJECT_OWNED_IDENTITY_MISMATCH",
                    "project-owned member identity does not match its exact index entry",
                    subject=member["portable_locator"],
                )
            owned_by_revision[revision_key] = member
            records[member["record_kind"]].append(record)
            locators.add(member["portable_locator"])

        for member in manifest["owned_members"]:
            parent = member["parent_reference"]
            if member["revision"] == 1:
                if parent != {"status": "omitted"}:
                    raise ProjectError(
                        "PROJECT_MEMBER_PARENT_INVALID",
                        "owned revision 1 must omit its parent",
                        subject=member["stable_id"],
                    )
                continue
            expected_key = (
                member["record_kind"], member["stable_id"], member["revision"] - 1
            )
            if (
                parent.get("status") != "included"
                or (
                    parent.get("record_kind"),
                    parent.get("stable_id"),
                    parent.get("revision"),
                )
                != expected_key
            ):
                raise ProjectError(
                    "PROJECT_MEMBER_PARENT_INVALID",
                    "owned successor must name the immediately preceding exact revision",
                    subject=member["stable_id"],
                )
            parent_member = owned_by_revision.get(expected_key) or base_revisions.get(expected_key)
            if parent_member is None or parent_member["content_hash"] != parent.get("content_hash"):
                raise ProjectError(
                    "PROJECT_MEMBER_PARENT_UNRESOLVED",
                    "owned successor parent is missing or hash-mismatched",
                    subject=member["stable_id"],
                )
        return (
            {
                kind: tuple(sorted(values, key=core.canonical_json))
                for kind, values in records.items()
            },
            locators,
        )

    @staticmethod
    def _semantic_cache_key(
        base_context: OperationContext,
        project_records: dict[str, tuple[dict[str, Any], ...]],
    ) -> tuple[str, ...]:
        return (
            core.canonical_json(base_context.record_set_reference),
            *(
                f"{kind}:{core.canonical_json(record)}"
                for kind in sorted(project_records)
                for record in sorted(
                    project_records[kind], key=core.canonical_json
                )
            ),
        )

    def _augment_context(
        self,
        base_context: OperationContext,
        project_records: dict[str, tuple[dict[str, Any], ...]],
        base_loaded: record_set_rules.LoadedRecordSet,
    ) -> tuple[OperationContext, dict[str, Any]]:
        key = self._semantic_cache_key(base_context, project_records)
        cached = self._semantic_cache.get(key)
        if cached is not None:
            self._semantic_cache.move_to_end(key)
            self._cache_metrics["semantic_hits"] += 1
            context, validation = cached
            return context, copy.deepcopy(validation)

        self._cache_metrics["semantic_misses"] += 1
        context, validation = self._augment_context_uncached(
            base_context, project_records, base_loaded
        )
        if self._semantic_cache_size > 0:
            self._semantic_cache[key] = (context, copy.deepcopy(validation))
            if len(self._semantic_cache) > self._semantic_cache_size:
                self._semantic_cache.popitem(last=False)
                self._cache_metrics["semantic_evictions"] += 1
        return context, validation

    def _augment_context_uncached(
        self,
        base_context: OperationContext,
        project_records: dict[str, tuple[dict[str, Any], ...]],
        base_loaded: record_set_rules.LoadedRecordSet,
    ) -> tuple[OperationContext, dict[str, Any]]:
        owned_count = sum(len(values) for values in project_records.values())
        if owned_count == 0:
            return base_context, {
                "status": "valid",
                "base_record_count": sum(
                    len(values) for values in base_loaded.records.values()
                ),
                "owned_record_count": 0,
                "graph_count": len(base_context.records["graphs"]),
                "instrument_count": len(base_context.records["instruments"]),
                "build_request_count": len(base_context.records["request"]),
                "component_graph_status": base_context.component_summary["status"],
                "device_instrument_status": base_context.device_summary["status"],
                "target_backend_build_status": base_context.task007_summary["status"],
            }
        context = base_context.with_records(
            graphs=(*base_context.records["graphs"], *project_records["dsp-graph"]),
            instruments=(
                *base_context.records["instruments"],
                *project_records["instrument"],
            ),
            request=(
                *base_context.records["request"],
                *project_records["build-request"],
            ),
        )
        additional_family_references: list[dict[str, Any]] = []
        additional_implementations: list[dict[str, Any]] = []
        if context.catalog_projection is not None:
            exact_family_ids = {item["family_id"] for item in context.records["families"]}
            referenced_family_ids = {
                item["family_reference"]["family_id"]
                for item in context.records["contracts"]
            }
            additional_family_references = [
                copy.deepcopy(item["family_reference"])
                for item in context.catalog_projection["families"]
                if item["family_reference"]["family_id"] in referenced_family_ids
                and item["family_reference"]["family_id"] not in exact_family_ids
            ]
            overlay_ids = {
                item["implementation_id"] for item in context.overlay["implementations"]
            }
            bound_ids = {
                item["implementation_id"] for item in context.records["bindings"]
            }
            corpus = context.records["catalog"][0]
            additional_implementations = [
                copy.deepcopy(item)
                for item in corpus["implementation_additions"]
                if item["implementation_id"] in bound_ids
                and item["implementation_id"] not in overlay_ids
            ]
        component_result = component.validate_component_graph_values(
            list(copy.deepcopy(context.records["families"])),
            list(copy.deepcopy(context.records["contracts"])),
            list(copy.deepcopy(context.records["bindings"])),
            list(copy.deepcopy(context.records["graphs"])),
            {
                "family": context.schemas["family"],
                "contract": context.schemas["contract"],
                "contract_versions": context.schemas["contract_versions"],
                "binding": context.schemas["binding"],
                "binding_versions": context.schemas["binding_versions"],
                "graph": context.schemas["graph"],
            },
            copy.deepcopy(context.overlay),
            context.overlay_sha256,
            context.manifest_sha256,
            copy.deepcopy(dict(context.observations)),
            additional_family_references=additional_family_references,
            additional_implementations=additional_implementations,
        )
        device_summary = device.validate_contract_values(
            list(copy.deepcopy(context.records["devices"])),
            list(copy.deepcopy(context.records["instruments"])),
            context.schemas["device"],
            context.schemas["instrument"],
            component_result.graph_targets,
        )
        task006_summary = aggregate.combine_task006_summaries(
            component_result.summary,
            device_summary,
            len(context.records["devices"]),
            len(context.records["instruments"]),
        )
        target_result = target.validate_target_backend_build_values(
            {kind: list(copy.deepcopy(context.records[kind])) for kind in target.SCHEMA_SPECS},
            {kind: context.schemas[kind] for kind in target.SCHEMA_SPECS},
            {
                "families": list(copy.deepcopy(context.records["families"])),
                "contracts": list(copy.deepcopy(context.records["contracts"])),
                "bindings": list(copy.deepcopy(context.records["bindings"])),
                "graphs": list(copy.deepcopy(context.records["graphs"])),
                "devices": list(copy.deepcopy(context.records["devices"])),
                "instruments": list(copy.deepcopy(context.records["instruments"])),
            },
            self.repository_root,
            task006_summary,
            additional_semantic_records=[
                copy.deepcopy(record)
                for kind in (
                    "conformance-probe-evidence",
                    "conformance-probe-input",
                    "conformance-probe-result",
                    "conformance-probe-procedure",
                    "prerequisite-environment",
                    "direct-operation-spec",
                    "gills-panel-evidence",
                    "gills-mapping-coverage",
                    "gills-runtime-realization",
                )
                for record in base_loaded.records.get(kind, ())
            ],
        )
        diagnostics = (
            list(component_result.summary.get("diagnostics", ()))
            + list(device_summary.get("diagnostics", ()))
            + list(target_result.summary.get("diagnostics", ()))
        )
        inherited_diagnostics = {
            core.canonical_json(item)
            for summary in (
                base_context.component_summary,
                base_context.device_summary,
                base_context.task007_summary,
            )
            for item in summary.get("diagnostics", ())
        }
        introduced_diagnostics = [
            item
            for item in diagnostics
            if core.canonical_json(item) not in inherited_diagnostics
        ]
        if introduced_diagnostics:
            first = sorted(introduced_diagnostics, key=core.diagnostic_sort_key)[0]
            raise ProjectError(
                "PROJECT_SEMANTIC_CLOSURE_INVALID",
                first["message"],
                subject=first["subject"],
                location=first["location"],
            )
        context = replace(
            context,
            device_summary=copy.deepcopy(device_summary),
            component_summary=copy.deepcopy(component_result.summary),
            task006_summary=copy.deepcopy(task006_summary),
            task007_summary=copy.deepcopy(target_result.summary),
        )
        validation = {
            "status": "valid",
            "base_record_count": sum(len(values) for values in base_loaded.records.values()),
            "owned_record_count": owned_count,
            "graph_count": len(context.records["graphs"]),
            "instrument_count": len(context.records["instruments"]),
            "build_request_count": len(context.records["request"]),
            "component_graph_status": component_result.summary["status"],
            "device_instrument_status": device_summary["status"],
            "target_backend_build_status": target_result.summary["status"],
        }
        return context, validation

    def _validate_selected_references(
        self, manifest: dict[str, Any], context: OperationContext
    ) -> None:
        if self._exact_match(
            context.records["graphs"], manifest["primary_graph_reference"], "graph_id"
        ) is None:
            raise ProjectError(
                "PROJECT_PRIMARY_GRAPH_UNRESOLVED",
                "primary graph does not resolve exactly in base-plus-project closure",
            )
        for name, group, id_field in (
            ("instrument_references", "instruments", "instrument_id"),
            ("build_request_references", "request", "build_request_id"),
        ):
            for reference in manifest[name]:
                if self._exact_match(context.records[group], reference, id_field) is None:
                    raise ProjectError(
                        "PROJECT_INCLUDED_REFERENCE_UNRESOLVED",
                        "included project reference does not resolve exactly",
                        location=f"$.{name}",
                    )

    def _validate_assets(self, manifest: dict[str, Any]) -> set[str]:
        locators: set[str] = set()
        for asset in manifest["asset_references"]:
            locator = asset["portable_locator"]
            path = self._safe_workspace_path(locator)
            if not path.is_file() or path.is_symlink():
                raise ProjectError(
                    "PROJECT_ASSET_MISSING",
                    "content-addressed asset is missing",
                    subject=locator,
                )
            data = path.read_bytes()
            if len(data) != asset["byte_length"] or "sha256:" + _sha256_bytes(data) != asset["content_hash"]:
                raise ProjectError(
                    "PROJECT_ASSET_HASH_MISMATCH",
                    "content-addressed asset bytes do not match the exact reference",
                    subject=locator,
                )
            locators.add(locator)
        return locators

    def _scan_governed_files(self) -> set[str]:
        actual: set[str] = set()
        head = self._safe_workspace_path(HEAD_LOCATOR)
        if head.exists():
            if head.is_symlink() or not head.is_file():
                raise ProjectError(
                    "PROJECT_SYMLINK_ESCAPE",
                    "workspace head is not a regular governed file",
                    subject=HEAD_LOCATOR,
                )
            actual.add(HEAD_LOCATOR)
        for root_locator in ("project", "records", "assets"):
            root = self._safe_workspace_path(root_locator)
            if not root.exists():
                continue
            for path in sorted(root.rglob("*")):
                if path.is_symlink():
                    raise ProjectError(
                        "PROJECT_SYMLINK_ESCAPE",
                        "governed workspace roots may not contain symlinks",
                        subject=path.name,
                    )
                if path.is_file():
                    actual.add(path.relative_to(self.workspace).as_posix())
        return actual

    def _load_lock(self) -> dict[str, Any] | None:
        path = self._safe_workspace_path(LOCK_LOCATOR)
        if not path.exists():
            return None
        value, _ = self._read_schema_value(
            LOCK_LOCATOR, self.context.schemas["workspace_lock"]
        )
        return value

    def _recover_if_needed(self) -> str:
        lock_path = self._safe_workspace_path(LOCK_LOCATOR)
        recovery_path = self._safe_workspace_path(RECOVERY_LOCATOR)
        lock = self._load_lock()
        if lock is not None and self.process_alive(lock["owner_pid"]):
            raise ProjectError(
                "PROJECT_WORKSPACE_LOCKED",
                "workspace has a live exclusive writer",
                status="conflict",
                subject=LOCK_LOCATOR,
            )
        if not recovery_path.exists():
            if lock is not None:
                lock_path.unlink()
                return "abandoned-lock-removed"
            return "not-needed"
        recovery, _ = self._read_schema_value(
            RECOVERY_LOCATOR, self.context.schemas["workspace_recovery"]
        )
        plan = recovery["write_plan"]
        plan_schema_key = {
            "project-write-plan-v0": "project_write_plan",
            "project-write-plan-v1": "project_write_plan_v1",
        }.get(plan.get("schema_version"))
        if plan_schema_key is None or plan_schema_key not in self.context.schemas:
            raise ProjectError(
                "PROJECT_RECOVERY_AMBIGUOUS",
                "pending recovery plan uses an unavailable schema version",
                subject=RECOVERY_LOCATOR,
            )
        schema = self.context.schemas[plan_schema_key]
        errors = core.schema_errors(plan, schema, schema)
        if errors or plan.get("content_hash") != core.record_content_hash(plan, schema):
            raise ProjectError(
                "PROJECT_RECOVERY_AMBIGUOUS",
                "pending recovery plan is malformed or hash-mismatched",
                subject=RECOVERY_LOCATOR,
            )
        acceptance = next(
            (
                item
                for item in plan["mutations"]
                if item["ordinal"] == plan["acceptance_boundary"]["mutation_ordinal"]
            ),
            None,
        )
        if acceptance is None:
            raise ProjectError(
                "PROJECT_RECOVERY_AMBIGUOUS",
                "write plan acceptance mutation is absent",
                subject=RECOVERY_LOCATOR,
            )
        head_path = self._safe_workspace_path(acceptance["portable_locator"])
        if not head_path.is_file() or head_path.is_symlink():
            raise ProjectError(
                "PROJECT_RECOVERY_AMBIGUOUS",
                "workspace head is missing during recovery",
                subject=HEAD_LOCATOR,
            )
        current = _byte_state(head_path.read_bytes())
        if current == acceptance["expected_old"]:
            status = "recovered-prior"
            for mutation in plan["mutations"]:
                if mutation["kind"] != "create-immutable":
                    continue
                target_path = self._safe_workspace_path(mutation["portable_locator"])
                if not target_path.exists():
                    continue
                if target_path.is_symlink() or _new_byte_state(target_path.read_bytes()) != mutation["proposed_new"]:
                    raise ProjectError(
                        "PROJECT_RECOVERY_AMBIGUOUS",
                        "unaccepted immutable target differs from its owned write plan",
                        subject=mutation["portable_locator"],
                    )
                target_path.unlink()
        elif _new_byte_state(head_path.read_bytes()) == acceptance["proposed_new"]:
            status = "recovered-successor"
            for mutation in plan["mutations"]:
                target_path = self._safe_workspace_path(mutation["portable_locator"])
                if not target_path.is_file() or target_path.is_symlink() or _new_byte_state(target_path.read_bytes()) != mutation["proposed_new"]:
                    raise ProjectError(
                        "PROJECT_RECOVERY_AMBIGUOUS",
                        "accepted successor is incomplete or hash-mismatched",
                        subject=mutation["portable_locator"],
                    )
        else:
            raise ProjectError(
                "PROJECT_RECOVERY_AMBIGUOUS",
                "workspace head matches neither the prior nor successor write-plan bytes",
                subject=HEAD_LOCATOR,
            )
        recovery_path.unlink()
        if lock_path.exists():
            lock_path.unlink()
        temp_root = self._safe_workspace_path(TMP_LOCATOR)
        if temp_root.exists():
            for path in sorted(temp_root.glob("*.tmp")):
                if path.is_symlink():
                    raise ProjectError(
                        "PROJECT_RECOVERY_AMBIGUOUS",
                        "temporary recovery state contains a symlink",
                        subject=path.name,
                    )
                path.unlink()
        return status

    def load(self, *, recover: bool = True) -> LoadedProject:
        if recover:
            self._recovery_status = self._recover_if_needed()
        head, head_bytes = self._read_schema_value(
            HEAD_LOCATOR, self.context.schemas["workspace_head"]
        )
        history, history_bytes, history_locators = self._load_project_history(head)
        manifest = history[-1]
        manifest_bytes = history_bytes[-1]
        if head["project_manifest_byte_sha256"] != _sha256_bytes(manifest_bytes):
            raise ProjectError(
                "PROJECT_HEAD_BYTE_HASH_MISMATCH",
                "workspace head does not match accepted project-manifest bytes",
                subject=HEAD_LOCATOR,
            )
        base_context, base_loaded = self._load_base(manifest["base_record_set"])
        project_records, record_locators = self._load_owned_records(
            manifest, base_loaded
        )
        context, validation = self._augment_context(
            base_context, project_records, base_loaded
        )
        self._validate_selected_references(manifest, context)
        asset_locators = self._validate_assets(manifest)
        expected = {
            HEAD_LOCATOR,
            *history_locators,
            *record_locators,
            *asset_locators,
        }
        actual = self._scan_governed_files()
        if actual != expected:
            missing = sorted(expected - actual)
            extra = sorted(actual - expected)
            raise ProjectError(
                "PROJECT_GOVERNED_MEMBERSHIP_MISMATCH",
                f"governed membership mismatch; missing={missing}; extra={extra}",
            )
        validation = {
            **validation,
            "project_revision_count": len(history),
            "governed_file_count": len(expected),
            "temporary_file_count": len(
                list(self._safe_workspace_path(TMP_LOCATOR).glob("*.tmp"))
            ),
            "recovery_status": self._recovery_status,
        }
        self._context = context
        return LoadedProject(
            head=copy.deepcopy(head),
            manifest=copy.deepcopy(manifest),
            context=context,
            project_records=project_records,
            validation=validation,
            recovery_status=self._recovery_status,
            head_bytes=head_bytes,
            manifest_bytes=manifest_bytes,
        )

    def init(self, payload: dict[str, Any]) -> dict[str, Any]:
        self._prepare_layout()
        head_path = self._safe_workspace_path(HEAD_LOCATOR)
        if head_path.exists():
            raise ProjectError(
                "PROJECT_ALREADY_INITIALIZED",
                "workspace already contains an accepted project head",
                status="conflict",
            )
        base_context, _ = self._load_base(payload["base_record_set"])
        self._validate_init_references(payload, base_context)
        for asset in payload["asset_references"]:
            self._validate_assets({"asset_references": [asset]})
        manifest = {
            "schema_version": "project-v0",
            "canonical_profile": "schuss-canonical-json-v1",
            "project_id": payload["project_id"],
            "revision": 1,
            "content_hash": "sha256:" + "0" * 64,
            "parent_reference": {"status": "omitted"},
            "base_record_set": copy.deepcopy(payload["base_record_set"]),
            "owned_members": [],
            "primary_graph_reference": copy.deepcopy(
                payload["primary_graph_reference"]
            ),
            "instrument_references": copy.deepcopy(
                payload["instrument_references"]
            ),
            "build_request_references": copy.deepcopy(
                payload["build_request_references"]
            ),
            "asset_references": copy.deepcopy(payload["asset_references"]),
        }
        project_schema = self.context.schemas["project"]
        manifest["content_hash"] = core.record_content_hash(manifest, project_schema)
        manifest_bytes = _schema_value_bytes(manifest, project_schema)
        manifest_locator = self._project_manifest_locator(
            manifest["project_id"], manifest["revision"]
        )
        head = {
            "schema_version": "workspace-head-v0",
            "canonical_profile": "schuss-canonical-json-v1",
            "accepted_project_reference": _project_reference(manifest),
            "project_manifest_locator": manifest_locator,
            "project_manifest_byte_sha256": _sha256_bytes(manifest_bytes),
        }
        head_bytes = _schema_value_bytes(head, self.context.schemas["workspace_head"])
        self._atomic_write(
            self._safe_workspace_path(manifest_locator),
            manifest_bytes,
            label="init-project",
            replace_target=False,
            allow_identical=True,
        )
        self._atomic_write(
            head_path,
            head_bytes,
            label="init-head",
            replace_target=False,
        )
        loaded = self.load(recover=False)
        return {
            "project": loaded.manifest,
            "workspace_head": loaded.head,
            "validation": loaded.validation,
            "persistence_status": "written",
            "acceptance_boundary": "workspace-head-created",
        }

    def inspect(self) -> dict[str, Any]:
        loaded = self.load()
        return {
            "project": loaded.manifest,
            "workspace_head": loaded.head,
            "validation": loaded.validation,
            "durable_files": {
                "acceptance_marker": HEAD_LOCATOR,
                "project_revision_root": "project/revisions",
                "record_root": "records",
                "asset_root": "assets",
            },
            "local_state": {
                "lock": LOCK_LOCATOR,
                "recovery": RECOVERY_LOCATOR,
                "temporary_root": TMP_LOCATOR,
                "canonical_identity": "excluded",
            },
        }

    def validate(self) -> dict[str, Any]:
        loaded = self.load()
        return {
            "project_reference": _project_reference(loaded.manifest),
            "base_record_set_reference": copy.deepcopy(
                loaded.context.record_set_reference
            ),
            "primary_graph_reference": copy.deepcopy(
                loaded.manifest["primary_graph_reference"]
            ),
            "summary": loaded.validation,
        }

    def _acquire_lock(self) -> None:
        self._prepare_layout()
        existing = self._load_lock()
        if existing is not None:
            if self.process_alive(existing["owner_pid"]):
                raise ProjectError(
                    "PROJECT_WORKSPACE_LOCKED",
                    "workspace has a live exclusive writer",
                    status="conflict",
                    subject=LOCK_LOCATOR,
                )
            self._recover_if_needed()
        lock = {
            "schema_version": "workspace-lock-v0",
            "owner_pid": self.pid_provider(),
            "operation": "project.graph.commit",
            "recovery_locator": RECOVERY_LOCATOR,
        }
        data = _schema_value_bytes(lock, self.context.schemas["workspace_lock"])
        path = self._safe_workspace_path(LOCK_LOCATOR)
        self._inject("before:lock.create")
        try:
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError as exc:
            raise ProjectError(
                "PROJECT_WORKSPACE_LOCKED",
                "workspace lock appeared during exclusive acquisition",
                status="conflict",
                subject=LOCK_LOCATOR,
            ) from exc
        try:
            os.write(descriptor, data)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        self._inject("after:lock.create")

    def _release_lock(self) -> None:
        self._unlink(self._safe_workspace_path(LOCK_LOCATOR), "lock")

    def _build_write_plan(
        self,
        loaded: LoadedProject,
        graph: dict[str, Any],
        graph_locator: str,
        graph_bytes: bytes,
        manifest: dict[str, Any],
        manifest_locator: str,
        manifest_bytes: bytes,
        head_bytes: bytes,
    ) -> dict[str, Any]:
        plan = {
            "schema_version": "project-write-plan-v0",
            "canonical_profile": "schuss-canonical-json-v1",
            "content_hash": "sha256:" + "0" * 64,
            "project_transition": {
                "parent_reference": _project_reference(loaded.manifest),
                "successor_reference": _project_reference(manifest),
            },
            "graph_transition": {
                "parent_reference": copy.deepcopy(
                    loaded.manifest["primary_graph_reference"]
                ),
                "successor_reference": _graph_reference(graph),
            },
            "mutations": [
                {
                    "ordinal": 1,
                    "kind": "create-immutable",
                    "portable_locator": graph_locator,
                    "expected_old": {"status": "absent"},
                    "proposed_new": _new_byte_state(graph_bytes),
                },
                {
                    "ordinal": 2,
                    "kind": "create-immutable",
                    "portable_locator": manifest_locator,
                    "expected_old": {"status": "absent"},
                    "proposed_new": _new_byte_state(manifest_bytes),
                },
                {
                    "ordinal": 3,
                    "kind": "replace-acceptance-marker",
                    "portable_locator": HEAD_LOCATOR,
                    "expected_old": _byte_state(loaded.head_bytes),
                    "proposed_new": _new_byte_state(head_bytes),
                },
            ],
            "acceptance_boundary": {
                "mutation_ordinal": 3,
                "portable_locator": HEAD_LOCATOR,
                "meaning": "atomic-workspace-head-replacement",
            },
        }
        schema = self.context.schemas["project_write_plan"]
        plan["content_hash"] = core.record_content_hash(plan, schema)
        _schema_value_bytes(plan, schema)
        return plan

    @staticmethod
    def _allocate_owned_id(
        project_id: str,
        record_kind: str,
        prefix: str,
        existing_ids: set[str],
    ) -> str:
        seed = hashlib.sha256(
            f"task026-profile-v1:{project_id}:{record_kind}".encode("utf-8")
        ).digest()
        candidate = int.from_bytes(seed[:8], "big") % 999999 + 1
        for _ in range(999999):
            stable_id = f"{prefix}-{candidate:06d}"
            if stable_id not in existing_ids:
                return stable_id
            candidate = candidate % 999999 + 1
        raise ProjectError(
            "PROJECT_ID_ALLOCATION_EXHAUSTED",
            "no project-owned stable identity remains available",
            subject=record_kind,
        )

    @staticmethod
    def _owned_member(
        record_kind: str,
        stable_id: str,
        record: dict[str, Any],
        locator: str,
        data: bytes,
    ) -> dict[str, Any]:
        return {
            "record_kind": record_kind,
            "stable_id": stable_id,
            "revision": record["revision"],
            "content_hash": record["content_hash"],
            "schema_version": record["schema_version"],
            "portable_locator": locator,
            "byte_sha256": _sha256_bytes(data),
            "parent_reference": {"status": "omitted"},
        }

    @staticmethod
    def _owned_successor_member(
        record_kind: str,
        stable_id: str,
        record: dict[str, Any],
        locator: str,
        data: bytes,
        parent: dict[str, Any],
    ) -> dict[str, Any]:
        member = ProjectService._owned_member(
            record_kind, stable_id, record, locator, data
        )
        member["parent_reference"] = {
            "status": "included",
            "record_kind": record_kind,
            "stable_id": stable_id,
            "revision": parent["revision"],
            "content_hash": parent["content_hash"],
        }
        return member

    def _build_multi_write_plan(
        self,
        loaded: LoadedProject,
        immutable_values: list[tuple[str, bytes]],
        manifest: dict[str, Any],
        manifest_locator: str,
        manifest_bytes: bytes,
        head_bytes: bytes,
    ) -> tuple[dict[str, Any], list[tuple[str, bytes]]]:
        all_immutables = [*immutable_values, (manifest_locator, manifest_bytes)]
        mutations = [
            {
                "ordinal": ordinal,
                "kind": "create-immutable",
                "portable_locator": locator,
                "expected_old": {"status": "absent"},
                "proposed_new": _new_byte_state(data),
            }
            for ordinal, (locator, data) in enumerate(all_immutables, 1)
        ]
        acceptance_ordinal = len(mutations) + 1
        mutations.append(
            {
                "ordinal": acceptance_ordinal,
                "kind": "replace-acceptance-marker",
                "portable_locator": HEAD_LOCATOR,
                "expected_old": _byte_state(loaded.head_bytes),
                "proposed_new": _new_byte_state(head_bytes),
            }
        )
        plan = {
            "schema_version": "project-write-plan-v1",
            "canonical_profile": "schuss-canonical-json-v1",
            "content_hash": "sha256:" + "0" * 64,
            "project_transition": {
                "parent_reference": _project_reference(loaded.manifest),
                "successor_reference": _project_reference(manifest),
            },
            "mutations": mutations,
            "acceptance_boundary": {
                "mutation_ordinal": acceptance_ordinal,
                "portable_locator": HEAD_LOCATOR,
                "meaning": "atomic-workspace-head-replacement",
            },
        }
        schema = self.context.schemas["project_write_plan_v1"]
        plan["content_hash"] = core.record_content_hash(plan, schema)
        _schema_value_bytes(plan, schema)
        return plan, all_immutables

    def _publish_multi_write_plan(
        self,
        loaded: LoadedProject,
        plan: dict[str, Any],
        immutables: list[tuple[str, bytes]],
        expected_manifest: dict[str, Any],
        head_bytes: bytes,
    ) -> LoadedProject:
        recovery = {
            "schema_version": "workspace-recovery-v0",
            "write_plan": copy.deepcopy(plan),
        }
        recovery_bytes = _schema_value_bytes(
            recovery, loaded.context.schemas["workspace_recovery"]
        )
        self._atomic_write(
            self._safe_workspace_path(RECOVERY_LOCATOR),
            recovery_bytes,
            label="recovery",
            replace_target=False,
        )
        for ordinal, (locator, data) in enumerate(immutables, 1):
            self._atomic_write(
                self._safe_workspace_path(locator),
                data,
                label=f"immutable-{ordinal}",
                replace_target=False,
            )
        self._atomic_write(
            self._safe_workspace_path(HEAD_LOCATOR),
            head_bytes,
            label="head",
            replace_target=True,
            expected_old=loaded.head_bytes,
        )
        successor = self.load(recover=False)
        if _project_reference(successor.manifest) != _project_reference(
            expected_manifest
        ):
            raise ProjectError(
                "PROJECT_POST_WRITE_RELOAD_MISMATCH",
                "accepted successor reload differs from the proposed project",
            )
        self._unlink(self._safe_workspace_path(RECOVERY_LOCATOR), "recovery")
        return successor

    def fork_profile(self, payload: dict[str, Any]) -> dict[str, Any]:
        locked = False
        completed = False
        try:
            self._acquire_lock()
            locked = True
            loaded = self.load(recover=False)
            if payload["expected_project_reference"] != _project_reference(
                loaded.manifest
            ):
                raise ProjectError(
                    "PROJECT_REVISION_STALE",
                    "profile fork expected a different accepted project revision",
                    status="conflict",
                    location="$.payload.expected_project_reference",
                )
            expected_selections = (
                payload["template_graph_reference"],
                [payload["template_instrument_reference"]],
                [payload["template_build_request_reference"]],
            )
            actual_selections = (
                loaded.manifest["primary_graph_reference"],
                loaded.manifest["instrument_references"],
                loaded.manifest["build_request_references"],
            )
            if (
                loaded.manifest["revision"] != 1
                or loaded.manifest["owned_members"]
                or actual_selections != expected_selections
            ):
                raise ProjectError(
                    "PROJECT_PROFILE_FORK_PRECONDITION_FAILED",
                    "profile fork requires the untouched exact initialized template head",
                    status="conflict",
                )
            template_graph = self._exact_match(
                loaded.context.records["graphs"],
                payload["template_graph_reference"],
                "graph_id",
            )
            template_instrument = self._exact_match(
                loaded.context.records["instruments"],
                payload["template_instrument_reference"],
                "instrument_id",
            )
            template_request = self._exact_match(
                loaded.context.records["request"],
                payload["template_build_request_reference"],
                "build_request_id",
            )
            if None in (template_graph, template_instrument, template_request):
                raise ProjectError(
                    "PROJECT_PROFILE_TEMPLATE_UNRESOLVED",
                    "one exact profile template record is absent",
                    location="$.payload",
                )
            assert template_graph is not None
            assert template_instrument is not None
            assert template_request is not None
            if (
                template_instrument["graph_reference"]
                != {"status": "resolved", **payload["template_graph_reference"]}
                or template_request["graph_reference"]
                != payload["template_graph_reference"]
                or template_request["instrument_reference"]
                != {"status": "included", **payload["template_instrument_reference"]}
            ):
                raise ProjectError(
                    "PROJECT_PROFILE_TEMPLATE_INCOHERENT",
                    "template graph, instrument, and request do not form one exact closure",
                )

            graph_id = self._allocate_owned_id(
                loaded.manifest["project_id"],
                "dsp-graph",
                "schuss-graph",
                {item["graph_id"] for item in loaded.context.records["graphs"]},
            )
            instrument_id = self._allocate_owned_id(
                loaded.manifest["project_id"],
                "instrument",
                "schuss-instrument",
                {
                    item["instrument_id"]
                    for item in loaded.context.records["instruments"]
                },
            )
            request_id = self._allocate_owned_id(
                loaded.manifest["project_id"],
                "build-request",
                "schuss-build-request",
                {
                    item["build_request_id"]
                    for item in loaded.context.records["request"]
                },
            )

            graph = copy.deepcopy(template_graph)
            graph.update(
                {
                    "graph_id": graph_id,
                    "revision": 1,
                    "content_hash": "sha256:" + "0" * 64,
                }
            )
            graph_schema = loaded.context.schemas["graph"]
            graph["content_hash"] = core.record_content_hash(graph, graph_schema)
            graph_bytes = _schema_value_bytes(graph, graph_schema)
            graph_locator = self._graph_locator(graph_id, 1)

            instrument = copy.deepcopy(template_instrument)
            instrument.update(
                {
                    "instrument_id": instrument_id,
                    "revision": 1,
                    "content_hash": "sha256:" + "0" * 64,
                }
            )
            instrument["graph_reference"] = {
                "status": "resolved",
                **_graph_reference(graph),
            }
            instrument_schema = loaded.context.schemas["instrument"]
            instrument["content_hash"] = core.record_content_hash(
                instrument, instrument_schema
            )
            instrument_bytes = _schema_value_bytes(instrument, instrument_schema)
            instrument_locator = self._instrument_locator(instrument_id, 1)

            request = copy.deepcopy(template_request)
            request.update(
                {
                    "build_request_id": request_id,
                    "revision": 1,
                    "content_hash": "sha256:" + "0" * 64,
                }
            )
            request["graph_reference"] = _graph_reference(graph)
            request["instrument_reference"] = {
                "status": "included",
                **_instrument_reference(instrument),
            }
            request_schema = loaded.context.schemas["request"]
            request["content_hash"] = core.record_content_hash(
                request, request_schema
            )
            request_bytes = _schema_value_bytes(request, request_schema)
            request_locator = self._build_request_locator(request_id, 1)

            members = [
                self._owned_member(
                    "dsp-graph", graph_id, graph, graph_locator, graph_bytes
                ),
                self._owned_member(
                    "instrument",
                    instrument_id,
                    instrument,
                    instrument_locator,
                    instrument_bytes,
                ),
                self._owned_member(
                    "build-request",
                    request_id,
                    request,
                    request_locator,
                    request_bytes,
                ),
            ]
            members.sort(key=core.canonical_json)
            manifest = copy.deepcopy(loaded.manifest)
            manifest["revision"] = 2
            manifest["parent_reference"] = {
                "status": "included",
                **_project_reference(loaded.manifest),
            }
            manifest["owned_members"] = members
            manifest["primary_graph_reference"] = _graph_reference(graph)
            manifest["instrument_references"] = [
                _instrument_reference(instrument)
            ]
            manifest["build_request_references"] = [
                _build_request_reference(request)
            ]
            manifest["content_hash"] = "sha256:" + "0" * 64
            project_schema = loaded.context.schemas["project"]
            manifest["content_hash"] = core.record_content_hash(
                manifest, project_schema
            )
            manifest_bytes = _schema_value_bytes(manifest, project_schema)
            manifest_locator = self._project_manifest_locator(
                manifest["project_id"], manifest["revision"]
            )
            head = {
                "schema_version": "workspace-head-v0",
                "canonical_profile": "schuss-canonical-json-v1",
                "accepted_project_reference": _project_reference(manifest),
                "project_manifest_locator": manifest_locator,
                "project_manifest_byte_sha256": _sha256_bytes(manifest_bytes),
            }
            head_bytes = _schema_value_bytes(
                head, loaded.context.schemas["workspace_head"]
            )

            base_context, base_loaded = self._load_base(
                loaded.manifest["base_record_set"]
            )
            proposed_records = {
                "dsp-graph": (graph,),
                "instrument": (instrument,),
                "build-request": (request,),
            }
            proposed_context, _ = self._augment_context(
                base_context, proposed_records, base_loaded
            )
            self._validate_selected_references(manifest, proposed_context)

            plan, immutables = self._build_multi_write_plan(
                loaded,
                [
                    (graph_locator, graph_bytes),
                    (instrument_locator, instrument_bytes),
                    (request_locator, request_bytes),
                ],
                manifest,
                manifest_locator,
                manifest_bytes,
                head_bytes,
            )
            successor = self._publish_multi_write_plan(
                loaded, plan, immutables, manifest, head_bytes
            )
            completed = True
            return {
                "project": successor.manifest,
                "graph": graph,
                "instrument": instrument,
                "build_request": request,
                "validation": successor.validation,
                "write_plan": plan,
                "persistence_status": "written",
                "acceptance_boundary": "workspace-head-replaced",
            }
        finally:
            if locked:
                try:
                    self._release_lock()
                except Exception:
                    if completed:
                        raise

    def transact_profile(self, payload: dict[str, Any]) -> dict[str, Any]:
        locked = False
        completed = False
        try:
            self._acquire_lock()
            locked = True
            loaded = self.load(recover=False)
            if payload["expected_project_reference"] != _project_reference(
                loaded.manifest
            ):
                raise ProjectError(
                    "PROJECT_REVISION_STALE",
                    "profile transaction expected a different accepted project revision",
                    status="conflict",
                    location="$.payload.expected_project_reference",
                )
            if payload["graph_reference"] != loaded.manifest["primary_graph_reference"]:
                raise ProjectError(
                    "PROJECT_PRIMARY_GRAPH_STALE",
                    "profile transaction base is not the accepted primary graph",
                    status="conflict",
                    location="$.payload.graph_reference",
                )
            if (
                len(loaded.manifest["instrument_references"]) != 1
                or len(loaded.manifest["build_request_references"]) != 1
            ):
                raise ProjectError(
                    "PROJECT_PROFILE_SELECTION_INVALID",
                    "profile transaction requires exactly one selected instrument and request",
                )
            graph = self._exact_match(
                loaded.context.records["graphs"],
                loaded.manifest["primary_graph_reference"],
                "graph_id",
            )
            instrument = self._exact_match(
                loaded.context.records["instruments"],
                loaded.manifest["instrument_references"][0],
                "instrument_id",
            )
            request = self._exact_match(
                loaded.context.records["request"],
                loaded.manifest["build_request_references"][0],
                "build_request_id",
            )
            if None in (graph, instrument, request):
                raise ProjectError(
                    "PROJECT_PROFILE_SELECTION_UNRESOLVED",
                    "selected profile graph, instrument, or request is unresolved",
                )
            assert graph is not None
            assert instrument is not None
            assert request is not None
            selected_member_keys = {
                _member_revision_key(item) for item in loaded.manifest["owned_members"]
            }
            expected_member_keys = {
                ("dsp-graph", graph["graph_id"], graph["revision"]),
                ("instrument", instrument["instrument_id"], instrument["revision"]),
                ("build-request", request["build_request_id"], request["revision"]),
            }
            if not expected_member_keys <= selected_member_keys:
                raise ProjectError(
                    "PROJECT_PROFILE_SELECTION_NOT_OWNED",
                    "profile transaction can only version the selected project-owned closure",
                    status="conflict",
                )
            if (
                instrument["graph_reference"]
                != {"status": "resolved", **_graph_reference(graph)}
                or request["graph_reference"] != _graph_reference(graph)
                or request["instrument_reference"]
                != {"status": "included", **_instrument_reference(instrument)}
            ):
                raise ProjectError(
                    "PROJECT_PROFILE_SELECTION_INCOHERENT",
                    "selected project-owned graph, instrument, and request do not form one closure",
                )

            graph_result = transact_graph_payload(
                {
                    "graph_reference": copy.deepcopy(payload["graph_reference"]),
                    "base_content_hash": payload["base_content_hash"],
                    "edits": copy.deepcopy(payload["edits"]),
                },
                loaded.context,
            )
            if graph_result["status"] != "success":
                raise ProjectTransactionRejected(graph_result)
            successor_graph = graph_result["value"]["proposed_graph"]
            graph_schema = loaded.context.schemas["graph"]
            graph_bytes = _schema_value_bytes(successor_graph, graph_schema)
            graph_locator = self._graph_locator(
                successor_graph["graph_id"], successor_graph["revision"]
            )

            successor_instrument = copy.deepcopy(instrument)
            successor_instrument["revision"] += 1
            successor_instrument["content_hash"] = "sha256:" + "0" * 64
            successor_instrument["graph_reference"] = {
                "status": "resolved",
                **_graph_reference(successor_graph),
            }
            instrument_schema = loaded.context.schemas["instrument"]
            successor_instrument["content_hash"] = core.record_content_hash(
                successor_instrument, instrument_schema
            )
            instrument_bytes = _schema_value_bytes(
                successor_instrument, instrument_schema
            )
            instrument_locator = self._instrument_locator(
                successor_instrument["instrument_id"],
                successor_instrument["revision"],
            )

            successor_request = copy.deepcopy(request)
            successor_request["revision"] += 1
            successor_request["content_hash"] = "sha256:" + "0" * 64
            successor_request["graph_reference"] = _graph_reference(
                successor_graph
            )
            successor_request["instrument_reference"] = {
                "status": "included",
                **_instrument_reference(successor_instrument),
            }
            request_schema = loaded.context.schemas["request"]
            successor_request["content_hash"] = core.record_content_hash(
                successor_request, request_schema
            )
            request_bytes = _schema_value_bytes(successor_request, request_schema)
            request_locator = self._build_request_locator(
                successor_request["build_request_id"], successor_request["revision"]
            )

            new_members = [
                self._owned_successor_member(
                    "dsp-graph",
                    successor_graph["graph_id"],
                    successor_graph,
                    graph_locator,
                    graph_bytes,
                    graph,
                ),
                self._owned_successor_member(
                    "instrument",
                    successor_instrument["instrument_id"],
                    successor_instrument,
                    instrument_locator,
                    instrument_bytes,
                    instrument,
                ),
                self._owned_successor_member(
                    "build-request",
                    successor_request["build_request_id"],
                    successor_request,
                    request_locator,
                    request_bytes,
                    request,
                ),
            ]
            manifest = copy.deepcopy(loaded.manifest)
            manifest["revision"] += 1
            manifest["parent_reference"] = {
                "status": "included",
                **_project_reference(loaded.manifest),
            }
            manifest["owned_members"].extend(new_members)
            manifest["owned_members"].sort(key=core.canonical_json)
            manifest["primary_graph_reference"] = _graph_reference(
                successor_graph
            )
            manifest["instrument_references"] = [
                _instrument_reference(successor_instrument)
            ]
            manifest["build_request_references"] = [
                _build_request_reference(successor_request)
            ]
            manifest["content_hash"] = "sha256:" + "0" * 64
            project_schema = loaded.context.schemas["project"]
            manifest["content_hash"] = core.record_content_hash(
                manifest, project_schema
            )
            manifest_bytes = _schema_value_bytes(manifest, project_schema)
            manifest_locator = self._project_manifest_locator(
                manifest["project_id"], manifest["revision"]
            )
            head = {
                "schema_version": "workspace-head-v0",
                "canonical_profile": "schuss-canonical-json-v1",
                "accepted_project_reference": _project_reference(manifest),
                "project_manifest_locator": manifest_locator,
                "project_manifest_byte_sha256": _sha256_bytes(manifest_bytes),
            }
            head_bytes = _schema_value_bytes(
                head, loaded.context.schemas["workspace_head"]
            )

            base_context, base_loaded = self._load_base(
                loaded.manifest["base_record_set"]
            )
            proposed_records = {
                "dsp-graph": (*loaded.project_records["dsp-graph"], successor_graph),
                "instrument": (
                    *loaded.project_records["instrument"],
                    successor_instrument,
                ),
                "build-request": (
                    *loaded.project_records["build-request"],
                    successor_request,
                ),
            }
            proposed_context, _ = self._augment_context(
                base_context, proposed_records, base_loaded
            )
            self._validate_selected_references(manifest, proposed_context)

            plan, immutables = self._build_multi_write_plan(
                loaded,
                [
                    (graph_locator, graph_bytes),
                    (instrument_locator, instrument_bytes),
                    (request_locator, request_bytes),
                ],
                manifest,
                manifest_locator,
                manifest_bytes,
                head_bytes,
            )
            successor = self._publish_multi_write_plan(
                loaded, plan, immutables, manifest, head_bytes
            )
            completed = True
            return {
                "project": successor.manifest,
                "graph": successor_graph,
                "instrument": successor_instrument,
                "build_request": successor_request,
                "graph_transaction_result": graph_result,
                "validation": successor.validation,
                "write_plan": plan,
                "persistence_status": "written",
                "acceptance_boundary": "workspace-head-replaced",
            }
        finally:
            if locked:
                try:
                    self._release_lock()
                except Exception:
                    if completed:
                        raise

    def history(self) -> dict[str, Any]:
        loaded = self.load()
        history, _, _ = self._load_project_history(loaded.head)
        return {
            "head_project_reference": _project_reference(loaded.manifest),
            "revision_count": len(history),
            "ancestry": [
                {
                    "project_reference": _project_reference(manifest),
                    "parent_reference": copy.deepcopy(
                        manifest["parent_reference"]
                    ),
                    "primary_graph_reference": copy.deepcopy(
                        manifest["primary_graph_reference"]
                    ),
                    "instrument_references": copy.deepcopy(
                        manifest["instrument_references"]
                    ),
                    "build_request_references": copy.deepcopy(
                        manifest["build_request_references"]
                    ),
                    "owned_member_count": len(manifest["owned_members"]),
                }
                for manifest in history
            ],
            "persistence_status": "not-written",
        }

    def revert(self, payload: dict[str, Any]) -> dict[str, Any]:
        locked = False
        completed = False
        try:
            self._acquire_lock()
            locked = True
            loaded = self.load(recover=False)
            if payload["expected_project_reference"] != _project_reference(
                loaded.manifest
            ):
                raise ProjectError(
                    "PROJECT_REVISION_STALE",
                    "revert expected a different accepted project revision",
                    status="conflict",
                    location="$.payload.expected_project_reference",
                )
            history, _, _ = self._load_project_history(loaded.head)
            target = next(
                (
                    manifest
                    for manifest in history[:-1]
                    if _project_reference(manifest)
                    == payload["target_project_reference"]
                ),
                None,
            )
            if target is None:
                raise ProjectError(
                    "PROJECT_REVERT_TARGET_NOT_ANCESTOR",
                    "revert target is not an exact prior project revision",
                    status="conflict",
                    location="$.payload.target_project_reference",
                )
            manifest = copy.deepcopy(loaded.manifest)
            manifest["revision"] += 1
            manifest["parent_reference"] = {
                "status": "included",
                **_project_reference(loaded.manifest),
            }
            for field in (
                "primary_graph_reference",
                "instrument_references",
                "build_request_references",
                "asset_references",
            ):
                manifest[field] = copy.deepcopy(target[field])
            manifest["content_hash"] = "sha256:" + "0" * 64
            self._validate_selected_references(manifest, loaded.context)
            project_schema = loaded.context.schemas["project"]
            manifest["content_hash"] = core.record_content_hash(
                manifest, project_schema
            )
            manifest_bytes = _schema_value_bytes(manifest, project_schema)
            manifest_locator = self._project_manifest_locator(
                manifest["project_id"], manifest["revision"]
            )
            head = {
                "schema_version": "workspace-head-v0",
                "canonical_profile": "schuss-canonical-json-v1",
                "accepted_project_reference": _project_reference(manifest),
                "project_manifest_locator": manifest_locator,
                "project_manifest_byte_sha256": _sha256_bytes(manifest_bytes),
            }
            head_bytes = _schema_value_bytes(
                head, loaded.context.schemas["workspace_head"]
            )
            plan, immutables = self._build_multi_write_plan(
                loaded,
                [],
                manifest,
                manifest_locator,
                manifest_bytes,
                head_bytes,
            )
            successor = self._publish_multi_write_plan(
                loaded, plan, immutables, manifest, head_bytes
            )
            completed = True
            return {
                "project": successor.manifest,
                "reverted_to_project_reference": copy.deepcopy(
                    payload["target_project_reference"]
                ),
                "validation": successor.validation,
                "write_plan": plan,
                "persistence_status": "written",
                "acceptance_boundary": "workspace-head-replaced",
            }
        finally:
            if locked:
                try:
                    self._release_lock()
                except Exception:
                    if completed:
                        raise

    def commit_graph(self, payload: dict[str, Any]) -> dict[str, Any]:
        locked = False
        completed = False
        try:
            self._acquire_lock()
            locked = True
            loaded = self.load(recover=False)
            if payload["expected_project_reference"] != _project_reference(
                loaded.manifest
            ):
                raise ProjectError(
                    "PROJECT_REVISION_STALE",
                    "write expected a different accepted project revision",
                    status="conflict",
                    location="$.payload.expected_project_reference",
                )
            if payload["graph_reference"] != loaded.manifest["primary_graph_reference"]:
                raise ProjectError(
                    "PROJECT_PRIMARY_GRAPH_STALE",
                    "write base is not the accepted primary graph",
                    status="conflict",
                    location="$.payload.graph_reference",
                )
            graph_request = {
                "schema_version": "schuss-operation-request-v1",
                "canonical_profile": "schuss-canonical-json-v1",
                "operation": "graph.transact",
                "payload": {
                    "graph_reference": copy.deepcopy(payload["graph_reference"]),
                    "base_content_hash": payload["base_content_hash"],
                    "edits": copy.deepcopy(payload["edits"]),
                },
            }
            graph_result = dispatch_operation(graph_request, loaded.context)
            if graph_result["status"] != "success":
                raise ProjectTransactionRejected(graph_result)
            graph = graph_result["value"]["proposed_graph"]
            graph_schema = loaded.context.schemas["graph"]
            graph_bytes = _schema_value_bytes(graph, graph_schema)
            graph_locator = self._graph_locator(graph["graph_id"], graph["revision"])
            member = {
                "record_kind": "dsp-graph",
                "stable_id": graph["graph_id"],
                "revision": graph["revision"],
                "content_hash": graph["content_hash"],
                "schema_version": graph["schema_version"],
                "portable_locator": graph_locator,
                "byte_sha256": _sha256_bytes(graph_bytes),
                "parent_reference": {
                    "status": "included",
                    "record_kind": "dsp-graph",
                    "stable_id": payload["graph_reference"]["graph_id"],
                    "revision": payload["graph_reference"]["revision"],
                    "content_hash": payload["graph_reference"]["content_hash"],
                },
            }
            manifest = copy.deepcopy(loaded.manifest)
            manifest["revision"] += 1
            manifest["parent_reference"] = {
                "status": "included",
                **_project_reference(loaded.manifest),
            }
            manifest["owned_members"].append(member)
            manifest["primary_graph_reference"] = _graph_reference(graph)
            manifest["content_hash"] = "sha256:" + "0" * 64
            project_schema = loaded.context.schemas["project"]
            manifest["content_hash"] = core.record_content_hash(
                manifest, project_schema
            )
            manifest_bytes = _schema_value_bytes(manifest, project_schema)
            manifest_locator = self._project_manifest_locator(
                manifest["project_id"], manifest["revision"]
            )
            head = {
                "schema_version": "workspace-head-v0",
                "canonical_profile": "schuss-canonical-json-v1",
                "accepted_project_reference": _project_reference(manifest),
                "project_manifest_locator": manifest_locator,
                "project_manifest_byte_sha256": _sha256_bytes(manifest_bytes),
            }
            head_bytes = _schema_value_bytes(
                head, loaded.context.schemas["workspace_head"]
            )
            plan = self._build_write_plan(
                loaded,
                graph,
                graph_locator,
                graph_bytes,
                manifest,
                manifest_locator,
                manifest_bytes,
                head_bytes,
            )
            recovery = {
                "schema_version": "workspace-recovery-v0",
                "write_plan": copy.deepcopy(plan),
            }
            recovery_bytes = _schema_value_bytes(
                recovery, loaded.context.schemas["workspace_recovery"]
            )
            self._atomic_write(
                self._safe_workspace_path(RECOVERY_LOCATOR),
                recovery_bytes,
                label="recovery",
                replace_target=False,
            )
            self._atomic_write(
                self._safe_workspace_path(graph_locator),
                graph_bytes,
                label="graph",
                replace_target=False,
            )
            self._atomic_write(
                self._safe_workspace_path(manifest_locator),
                manifest_bytes,
                label="project",
                replace_target=False,
            )
            self._atomic_write(
                self._safe_workspace_path(HEAD_LOCATOR),
                head_bytes,
                label="head",
                replace_target=True,
                expected_old=loaded.head_bytes,
            )
            successor = self.load(recover=False)
            if successor.manifest != manifest:
                raise ProjectError(
                    "PROJECT_POST_WRITE_RELOAD_MISMATCH",
                    "accepted successor reload differs from the proposed project",
                )
            self._unlink(
                self._safe_workspace_path(RECOVERY_LOCATOR), "recovery"
            )
            completed = True
            return {
                "project": successor.manifest,
                "graph": graph,
                "validation": successor.validation,
                "write_plan": plan,
                "persistence_status": "written",
                "acceptance_boundary": "workspace-head-replaced",
            }
        finally:
            if locked:
                try:
                    self._release_lock()
                except Exception:
                    if completed:
                        raise


def dispatch_project_operation(
    request: dict[str, Any], service: ProjectService
) -> dict[str, Any]:
    """Dispatch one additive project request through the shared service."""

    operation = request.get("operation") if isinstance(request, dict) else None
    request_version = request.get("schema_version") if isinstance(request, dict) else None
    is_v8 = request_version == "schuss-operation-request-v8"
    is_v11 = request_version == "schuss-operation-request-v11"
    is_authoring = is_v8 or is_v11
    schema_key = (
        "operation_request_v11"
        if is_v11
        else "operation_request_v8"
        if is_v8
        else "operation_request_v3"
    )
    result_schema_key = (
        "operation_result_v11"
        if is_v11
        else "operation_result_v8"
        if is_v8
        else "operation_result_v3"
    )
    result_version = 11 if is_v11 else 8 if is_v8 else 3
    schema = service.context.schemas[schema_key]
    errors: list[str] = []
    try:
        core.assert_portable_json_value(request)
    except ValueError as exc:
        errors.append(str(exc))
    if not isinstance(request, dict):
        errors.append("$: operation request must be an object")
    else:
        errors.extend(core.schema_errors(request, schema, schema))
    allowed_v3 = {
        "records.validate",
        "graph.inspect",
        "build.resolve",
        "graph.transact",
        "catalog.search",
        "catalog.inspect",
        "project.init",
        "project.inspect",
        "project.validate",
        "project.graph.commit",
    }
    allowed_v8 = {
        "project.profile.fork",
        "project.profile.transact",
        "project.history.inspect",
        "project.revert",
    }
    allowed_v11 = {"project.profile.transact"}
    allowed = allowed_v11 if is_v11 else allowed_v8 if is_v8 else allowed_v3
    if errors:
        result = _operation_result(
            operation if operation in allowed else "invalid-request",
            "invalid",
            None,
            [
                _diagnostic(
                    "OPERATION_REQUEST_INVALID",
                    operation if isinstance(operation, str) else "invalid-request",
                    "$",
                    message,
                )
                for message in sorted(set(errors))
            ],
            version=result_version,
        )
        _schema_value_bytes(result, service.context.schemas[result_schema_key])
        return result
    try:
        if operation == "project.profile.fork":
            value = service.fork_profile(request["payload"])
        elif operation == "project.profile.transact":
            value = service.transact_profile(request["payload"])
        elif operation == "project.history.inspect":
            value = service.history()
        elif operation == "project.revert":
            value = service.revert(request["payload"])
        elif operation == "project.init":
            value = service.init(request["payload"])
        elif operation == "project.inspect":
            value = service.inspect()
        elif operation == "project.validate":
            value = service.validate()
        elif operation == "project.graph.commit":
            value = service.commit_graph(request["payload"])
        elif not is_authoring:
            loaded = service.load()
            downgraded = copy.deepcopy(request)
            if operation in {"catalog.search", "catalog.inspect"}:
                downgraded["schema_version"] = "schuss-operation-request-v2"
            else:
                downgraded["schema_version"] = "schuss-operation-request-v1"
            result = dispatch_operation(downgraded, loaded.context)
            result["schema_version"] = "schuss-operation-result-v3"
            _schema_value_bytes(
                result, loaded.context.schemas["operation_result_v3"]
            )
            return result
        else:
            raise ProjectError(
                "OPERATION_REQUEST_INVALID",
                "unsupported project operation version",
            )
        result = _operation_result(
            operation, "success", value, version=result_version
        )
    except ProjectTransactionRejected as exc:
        graph_result = exc.result
        result = _operation_result(
            operation,
            graph_result["status"],
            {
                "graph_transaction_result": graph_result,
                "persistence_status": "not-written",
            },
            graph_result["diagnostics"],
            version=result_version,
        )
    except ProjectError as exc:
        result = _operation_result(
            operation,
            exc.status,
            None,
            [
                _diagnostic(
                    exc.code,
                    exc.subject,
                    exc.location,
                    str(exc),
                )
            ],
            version=result_version,
        )
    _schema_value_bytes(result, service.context.schemas[result_schema_key])
    return result
