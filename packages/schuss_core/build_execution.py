"""Client-neutral build execution after the accepted compiler front half.

The module owns no backend implementation.  Callers inject an exact registry
of handler descriptors and callables plus one host-local fresh output root.
Canonical results retain only portable identities and artifact facts.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from .compiler_front_half import CompilationContext, plan_build


EXECUTION_POLICY = "schuss-build-execution-v1"
PROGRESS_EVENTS = (
    "planning-started",
    "planning-completed",
    "handler-selected",
    "handler-started",
    "handler-completed",
    "output-published",
)


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical_bytes(value)).hexdigest()


def descriptor_content_hash(value: Mapping[str, Any]) -> str:
    payload = {
        key: copy.deepcopy(item)
        for key, item in value.items()
        if key != "content_hash"
    }
    return _sha256(payload)


def handler_reference(descriptor: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "build_handler_id": descriptor["build_handler_id"],
        "revision": descriptor["revision"],
        "content_hash": descriptor["content_hash"],
    }


@dataclass(frozen=True)
class CancellationToken:
    """Small deterministic cancellation boundary owned by the caller."""

    check: Callable[[], bool] = lambda: False

    @property
    def cancelled(self) -> bool:
        return bool(self.check())


@dataclass(frozen=True)
class HandlerRequest:
    plan: dict[str, Any]
    compilation_context: CompilationContext
    output_root: Path


Handler = Callable[[HandlerRequest], dict[str, Any]]
ProgressCallback = Callable[[dict[str, Any]], None]


@dataclass(frozen=True)
class HandlerRegistration:
    descriptor: dict[str, Any]
    handler: Handler

    def __post_init__(self) -> None:
        expected = descriptor_content_hash(self.descriptor)
        if self.descriptor.get("content_hash") != expected:
            raise ValueError("build handler descriptor content hash is invalid")


@dataclass(frozen=True)
class ExecutionService:
    """Exact immutable registry plus a host-local final output root."""

    registrations: tuple[HandlerRegistration, ...]
    output_root: Path

    @classmethod
    def from_values(
        cls,
        registrations: Iterable[HandlerRegistration],
        output_root: Path,
    ) -> "ExecutionService":
        values = tuple(
            sorted(
                registrations,
                key=lambda item: _canonical_bytes(handler_reference(item.descriptor)),
            )
        )
        return cls(values, Path(output_root))

    def descriptor_for_locator(self, stable_id: str, revision: int) -> dict[str, Any]:
        matches = [
            item.descriptor
            for item in self.registrations
            if item.descriptor["build_handler_id"] == stable_id
            and item.descriptor["revision"] == revision
        ]
        if len(matches) != 1:
            raise ValueError("handler locator does not resolve exactly once")
        return copy.deepcopy(matches[0])


class ExecutionFailure(RuntimeError):
    def __init__(self, code: str, stage: str, subject: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.stage = stage
        self.subject = subject


def _diagnostic(code: str, stage: str, subject: str, message: str) -> dict[str, str]:
    return {
        "code": code,
        "severity": "error",
        "stage": stage,
        "subject": subject,
        "message": message,
    }


def _progress(values: list[dict[str, Any]], event: str, subject: str, callback: ProgressCallback | None) -> None:
    if event not in PROGRESS_EVENTS:
        raise ValueError(f"unknown build progress event {event!r}")
    value = {"ordinal": len(values) + 1, "event": event, "subject": subject}
    values.append(value)
    if callback is not None:
        callback(copy.deepcopy(value))


def _evidence(passed_through: int) -> list[dict[str, Any]]:
    return [
        {"level": level, "status": "passed" if level <= passed_through else "not-run"}
        for level in range(1, 9)
    ]


def _base_result(
    *,
    status: str,
    request_reference: Mapping[str, Any],
    plan_sha256: str,
    requested_handler_reference: Mapping[str, Any],
    cache_key: str,
    progress: list[dict[str, Any]],
    stages: list[dict[str, str]],
    diagnostics: list[dict[str, str]],
    artifacts: list[dict[str, Any]] | None = None,
    evidence_level: int = 0,
    publication: str = "not-published",
) -> dict[str, Any]:
    execution_identity = _sha256(
        {
            "request_reference": dict(request_reference),
            "plan_sha256": plan_sha256,
            "handler_reference": dict(requested_handler_reference),
            "cache_key": cache_key,
            "policy": EXECUTION_POLICY,
        }
    ).removeprefix("sha256:")[:16]
    return {
        "schema_version": "build-execution-result-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "execution_id": f"schuss-build-execution-{execution_identity}",
        "status": status,
        "build_request_reference": copy.deepcopy(dict(request_reference)),
        "plan_sha256": plan_sha256,
        "handler_reference": copy.deepcopy(dict(requested_handler_reference)),
        "cache": {"policy": "disabled", "lookup": "miss", "key": cache_key},
        "progress": copy.deepcopy(progress),
        "stage_outcomes": copy.deepcopy(stages),
        "artifacts": sorted(copy.deepcopy(artifacts or []), key=lambda item: item["artifact_kind"]),
        "evidence_levels": _evidence(evidence_level),
        "output_publication": publication,
        "diagnostics": sorted(copy.deepcopy(diagnostics), key=lambda item: (item["stage"], item["code"], item["subject"], item["message"])),
        "authoritative_records_mutated": False,
        "device_actions_performed": False,
    }


def _cancelled(
    *,
    request_reference: Mapping[str, Any],
    plan_sha256: str,
    handler_ref: Mapping[str, Any],
    cache_key: str,
    progress: list[dict[str, Any]],
    stages: list[dict[str, str]],
    stage: str,
    evidence_level: int = 0,
) -> dict[str, Any]:
    return _base_result(
        status="cancelled",
        request_reference=request_reference,
        plan_sha256=plan_sha256,
        requested_handler_reference=handler_ref,
        cache_key=cache_key,
        progress=progress,
        stages=stages,
        diagnostics=[_diagnostic("BUILD_EXECUTION_CANCELLED", stage, request_reference["build_request_id"], "execution was cancelled at a shared boundary")],
        evidence_level=evidence_level,
    )


def _select_handler(
    service: ExecutionService,
    reference: Mapping[str, Any],
    plan: Mapping[str, Any],
    compilation_context: CompilationContext,
) -> HandlerRegistration:
    request_reference = plan["input_closure"]["build_request_reference"]
    requests = [
        item
        for item in compilation_context.records()["request"]
        if all(item.get(key) == value for key, value in request_reference.items())
    ]
    if len(requests) != 1:
        raise ExecutionFailure(
            "BUILD_REQUEST_NOT_EXACT",
            "handler-selection",
            request_reference["build_request_id"],
            f"expected one exact planned build request, found {len(requests)}",
        )
    backend_reference = requests[0]["backend_reference"]
    matches = [
        item
        for item in service.registrations
        if handler_reference(item.descriptor) == dict(reference)
        and item.descriptor["supported_build_request_reference"] == request_reference
        and item.descriptor["backend_reference"] == backend_reference
    ]
    if len(matches) != 1:
        raise ExecutionFailure(
            "BUILD_HANDLER_NOT_EXACT",
            "handler-selection",
            str(reference.get("build_handler_id", "build-handler")),
            f"expected exactly one exact registered handler, found {len(matches)}",
        )
    return matches[0]


def execute_build(
    compilation_context: CompilationContext,
    requested_handler_reference: Mapping[str, Any],
    service: ExecutionService,
    *,
    execution_intent: bool,
    cancellation_token: CancellationToken | None = None,
    progress_callback: ProgressCallback | None = None,
    plan_function: Callable[[CompilationContext], dict[str, Any]] = plan_build,
) -> dict[str, Any]:
    """Plan once, dispatch one exact handler, and atomically publish success."""

    token = cancellation_token or CancellationToken()
    request_reference = compilation_context.build_request_reference()
    handler_ref = copy.deepcopy(dict(requested_handler_reference))
    progress: list[dict[str, Any]] = []
    stages: list[dict[str, str]] = []
    empty_hash = "sha256:" + "0" * 64
    if not execution_intent:
        return _base_result(
            status="invalid",
            request_reference=request_reference,
            plan_sha256=empty_hash,
            requested_handler_reference=handler_ref,
            cache_key=empty_hash,
            progress=progress,
            stages=stages,
            diagnostics=[_diagnostic("BUILD_EXECUTION_INTENT_REQUIRED", "execution-preflight", request_reference.get("build_request_id", "build-request"), "explicit execution intent is required")],
        )
    if token.cancelled:
        return _cancelled(request_reference=request_reference, plan_sha256=empty_hash, handler_ref=handler_ref, cache_key=empty_hash, progress=progress, stages=stages, stage="planning")
    _progress(progress, "planning-started", request_reference["build_request_id"], progress_callback)
    plan = plan_function(compilation_context)
    plan_hash = _sha256(plan)
    stages.extend(copy.deepcopy(plan["stages"]))
    _progress(progress, "planning-completed", request_reference["build_request_id"], progress_callback)
    cache_key = _sha256({"plan_sha256": plan_hash, "handler_reference": handler_ref, "policy": EXECUTION_POLICY})
    if plan["status"] != "success":
        passed_level = max(
            (item["level"] for item in plan["evidence_levels"] if item["status"] == "passed"),
            default=0,
        )
        return _base_result(
            status=plan["status"], request_reference=request_reference,
            plan_sha256=plan_hash, requested_handler_reference=handler_ref,
            cache_key=cache_key, progress=progress, stages=stages,
            diagnostics=[_diagnostic("BUILD_PLAN_NOT_EXECUTABLE", "planning", request_reference["build_request_id"], f"compiler plan status is {plan['status']}")],
            evidence_level=passed_level,
        )
    if token.cancelled:
        return _cancelled(request_reference=request_reference, plan_sha256=plan_hash, handler_ref=handler_ref, cache_key=cache_key, progress=progress, stages=stages, stage="handler-selection", evidence_level=2)
    try:
        registration = _select_handler(service, handler_ref, plan, compilation_context)
        _progress(progress, "handler-selected", handler_ref["build_handler_id"], progress_callback)
        final_root = service.output_root
        absolute = final_root.absolute()
        if final_root != absolute:
            final_root = absolute
        if os.path.lexists(final_root):
            raise ExecutionFailure("BUILD_OUTPUT_ROOT_EXISTS", "execution-preflight", "output-root", "final output root must not exist")
        parent = final_root.parent
        if not parent.is_dir() or parent.is_symlink():
            raise ExecutionFailure("BUILD_OUTPUT_PARENT_INVALID", "execution-preflight", "output-root", "output parent must be an existing non-symlink directory")
        staging = parent / f".{final_root.name}.schuss-staging-{cache_key.removeprefix('sha256:')[:16]}"
        if os.path.lexists(staging):
            raise ExecutionFailure("BUILD_STAGING_ROOT_EXISTS", "execution-preflight", "output-root", "deterministic staging root already exists")
        if token.cancelled:
            return _cancelled(request_reference=request_reference, plan_sha256=plan_hash, handler_ref=handler_ref, cache_key=cache_key, progress=progress, stages=stages, stage="handler-dispatch", evidence_level=2)
        _progress(progress, "handler-started", handler_ref["build_handler_id"], progress_callback)
        try:
            outcome = registration.handler(HandlerRequest(copy.deepcopy(plan), compilation_context, staging))
        except Exception as exc:
            if os.path.lexists(staging) and staging.is_dir() and not staging.is_symlink():
                shutil.rmtree(staging)
            code = getattr(exc, "code", "BUILD_HANDLER_FAILED")
            stage = getattr(exc, "stage", "backend-lowering")
            subject = getattr(exc, "subject", handler_ref["build_handler_id"])
            raise ExecutionFailure(str(code), str(stage), str(subject), str(exc)) from exc
        if outcome.get("status") != "success":
            if os.path.lexists(staging) and staging.is_dir() and not staging.is_symlink():
                shutil.rmtree(staging)
            raise ExecutionFailure("BUILD_HANDLER_NON_SUCCESS", "backend-lowering", handler_ref["build_handler_id"], "handler returned a non-success outcome")
        _progress(progress, "handler-completed", handler_ref["build_handler_id"], progress_callback)
        stages.extend(copy.deepcopy(outcome["stage_outcomes"]))
        if token.cancelled:
            if staging.is_dir() and not staging.is_symlink():
                shutil.rmtree(staging)
            return _cancelled(request_reference=request_reference, plan_sha256=plan_hash, handler_ref=handler_ref, cache_key=cache_key, progress=progress, stages=stages, stage="output-publication", evidence_level=2)
        if not staging.is_dir() or staging.is_symlink() or os.path.lexists(final_root):
            if staging.is_dir() and not staging.is_symlink():
                shutil.rmtree(staging)
            raise ExecutionFailure("BUILD_OUTPUT_PUBLICATION_INVALID", "output-publication", "output-root", "handler staging root is not publishable")
        try:
            staging.rename(final_root)
        except OSError as exc:
            if staging.is_dir() and not staging.is_symlink():
                shutil.rmtree(staging)
            raise ExecutionFailure("BUILD_OUTPUT_PUBLICATION_FAILED", "output-publication", "output-root", "atomic output publication failed") from exc
        _progress(progress, "output-published", request_reference["build_request_id"], progress_callback)
        return _base_result(
            status="success", request_reference=request_reference,
            plan_sha256=plan_hash, requested_handler_reference=handler_ref,
            cache_key=cache_key, progress=progress, stages=stages,
            diagnostics=[], artifacts=outcome["artifacts"], evidence_level=int(outcome["evidence_level"]),
            publication="published",
        )
    except ExecutionFailure as exc:
        return _base_result(
            status="unavailable" if exc.code == "BUILD_HANDLER_NOT_EXACT" else "failed",
            request_reference=request_reference, plan_sha256=plan_hash,
            requested_handler_reference=handler_ref, cache_key=cache_key,
            progress=progress, stages=stages,
            diagnostics=[_diagnostic(exc.code, exc.stage, exc.subject, str(exc))],
            evidence_level=2,
        )
