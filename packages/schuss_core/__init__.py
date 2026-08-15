"""Public Task 008 headless control-plane API."""

from .control_plane import (
    OperationContext,
    canonical_result_bytes,
    dispatch_operation,
    load_repository_context,
)
from .project_service import ProjectService, dispatch_project_operation
from .compiler_front_half import CompilationContext, plan_build
from .build_execution import (
    CancellationToken,
    ExecutionService,
    HandlerRegistration,
    execute_build,
    handler_reference,
)

__all__ = [
    "OperationContext",
    "canonical_result_bytes",
    "dispatch_operation",
    "load_repository_context",
    "ProjectService",
    "dispatch_project_operation",
    "CompilationContext",
    "plan_build",
    "CancellationToken",
    "ExecutionService",
    "HandlerRegistration",
    "execute_build",
    "handler_reference",
]
