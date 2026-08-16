"""Task 021 DMA-safe successor to the exact Task 018 mapped-Gills handler."""

from __future__ import annotations

import copy
from typing import Any

from .build_execution import HandlerRegistration, HandlerRequest, descriptor_content_hash
from .gills_direct_backend import BACKEND_REFERENCE, DirectExecutionConfig
from .gills_mapped_backend import _run_handler_for_closure
from .gills_mapped_frontend import lower_gills_mapped_dma_safe


REQUEST_REFERENCE = {
    "build_request_id": "schuss-build-request-000002",
    "revision": 5,
    "content_hash": "sha256:0422c6873c2f49140f4e3649cf5ea0ca690ea1999aac41c94deb0c28da87b33d",
}
INSTRUMENT_REFERENCE = {
    "instrument_id": "schuss-instrument-000002",
    "revision": 3,
    "content_hash": "sha256:6b41e740ba7c4d098733d0f8fe462166ae553894b01c86a5db579d9aff38fc85",
}
RUNTIME_REFERENCE = {
    "runtime_realization_id": "schuss-runtime-realization-000001",
    "revision": 2,
    "content_hash": "sha256:3442be669cd24994c5cd8dec37fbbc724697f79dbfd7195975ec8b2a00bc1cc7",
}
COVERAGE_REFERENCE = {
    "coverage_report_id": "schuss-coverage-report-000001",
    "revision": 2,
    "content_hash": "sha256:6eb8f9a72df2a5f822d77c3b5a1b1f684fbd23846d72d227866de2191c47cb97",
}


def descriptor() -> dict[str, Any]:
    value = {
        "schema_version": "build-handler-descriptor-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "build_handler_id": "schuss-build-handler-000003",
        "revision": 2,
        "content_hash": "sha256:" + "0" * 64,
        "backend_reference": copy.deepcopy(BACKEND_REFERENCE),
        "supported_build_request_reference": copy.deepcopy(REQUEST_REFERENCE),
        "execution_policy": "exact-request-only",
        "adapter_kind": "direct",
        "mid_handler_cancellation": False,
    }
    value["content_hash"] = descriptor_content_hash(value)
    return value


def run_handler(
    request: HandlerRequest,
    config: DirectExecutionConfig | None = None,
) -> dict[str, Any]:
    return _run_handler_for_closure(
        request,
        config,
        request_reference=REQUEST_REFERENCE,
        instrument_reference=INSTRUMENT_REFERENCE,
        runtime_reference=RUNTIME_REFERENCE,
        coverage_reference=COVERAGE_REFERENCE,
        descriptor_value=descriptor(),
        lowerer=lower_gills_mapped_dma_safe,
        task_id="task021",
    )


def registration(
    config: DirectExecutionConfig | None = None,
) -> HandlerRegistration:
    return HandlerRegistration(
        descriptor(), lambda request: run_handler(request, config)
    )


__all__ = ["descriptor", "registration", "run_handler"]
