"""Local Model Context Protocol adapter over canonical Schuss operations.

The adapter implements the local stdio binding for MCP 2026-07-28 and the
immediately preceding 2025-11-25 initialization era.  It deliberately owns no
catalog, graph, project, build, or device semantics: every tool call constructs
one existing operation request and dispatches it through the shared control
plane exactly once.
"""

from __future__ import annotations

import copy
import json
import sys
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO, Callable, Mapping, TextIO

from .control_plane import (
    REPOSITORY_ROOT,
    OperationContext,
    canonical_result_bytes,
    dispatch_operation,
    load_repository_context,
)
from .project_service import ProjectService
from .ai_authoring import SonicAuthoringService


MODERN_PROTOCOL_VERSION = "2026-07-28"
LEGACY_PROTOCOL_VERSION = "2025-11-25"
SUPPORTED_PROTOCOL_VERSIONS = (
    MODERN_PROTOCOL_VERSION,
    LEGACY_PROTOCOL_VERSION,
)
SERVER_INFO = {"name": "schuss", "version": "0.1.0"}
SERVER_INFO_META_KEY = "io.modelcontextprotocol/serverInfo"
PROTOCOL_VERSION_META_KEY = "io.modelcontextprotocol/protocolVersion"
CLIENT_INFO_META_KEY = "io.modelcontextprotocol/clientInfo"
CLIENT_CAPABILITIES_META_KEY = "io.modelcontextprotocol/clientCapabilities"
CAPABILITY_RESOURCE_URI = "schuss://application/capabilities"
DEFAULT_RECORD_SET_PATH = (
    REPOSITORY_ROOT / "contracts/record-sets/ai-sonic-authoring-v1.json"
)
MAX_REQUEST_BYTES = 1_048_576
CACHE_TTL_MS = 300_000
TOOL_RATE_LIMIT = 120
TOOL_RATE_WINDOW_SECONDS = 60.0

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603
UNSUPPORTED_PROTOCOL_VERSION = -32022
TOOL_RATE_LIMITED = -31000

_MISSING = object()


@dataclass(frozen=True)
class McpToolBinding:
    """One stable MCP presentation of one existing Schuss operation."""

    name: str
    title: str
    description: str
    operation: str
    request_version: int
    requires_project: bool = False
    read_only: bool = True
    destructive: bool = False
    idempotent: bool = True

    @property
    def request_schema_key(self) -> str:
        return f"operation_request_v{self.request_version}"

    @property
    def result_schema_key(self) -> str:
        return f"operation_result_v{self.request_version}"

    @property
    def request_schema_version(self) -> str:
        return f"schuss-operation-request-v{self.request_version}"


READ_ONLY_TOOL_BINDINGS = (
    McpToolBinding(
        "schuss.application.describe",
        "Describe Schuss capabilities",
        "Describe the exact client-neutral Schuss operation surface for the selected record set.",
        "application.describe",
        7,
    ),
    McpToolBinding(
        "schuss.catalog.implementations.search",
        "Search catalog objects",
        "Search individual catalog implementations using the exact function-first catalog projection and closed facet filters.",
        "catalog.implementations.search",
        10,
    ),
    McpToolBinding(
        "schuss.catalog.inspect",
        "Inspect a catalog family",
        "Inspect one exact catalog family reference, including its presentation and implementation closure.",
        "catalog.inspect",
        2,
    ),
    McpToolBinding(
        "schuss.catalog.search",
        "Search catalog families",
        "Search musician-facing catalog families using a query and the exact closed facet-filter object.",
        "catalog.search",
        2,
    ),
    McpToolBinding(
        "schuss.component.inspect",
        "Inspect a component contract",
        "Inspect one exact governed component contract for ports, parameters, attributes, actions, and displays.",
        "component.inspect",
        11,
    ),
    McpToolBinding(
        "schuss.graph.inspect",
        "Inspect a DSP graph",
        "Inspect one exact DSP graph and its exact component-contract closure without selecting an implementation or building it.",
        "graph.inspect",
        1,
    ),
)

SONIC_PLANNING_TOOL_BINDINGS = (
    McpToolBinding(
        "schuss.sonic.intent.plan",
        "Plan sonic intent",
        "Retrieve validity-gated existing candidates while keeping transparent-compound and native-kernel creation lanes open; no cost objective is used.",
        "sonic.intent.plan",
        13,
    ),
)

PROJECT_AUTHORING_TOOL_BINDINGS = (
    McpToolBinding(
        "schuss.authoring.change.accept",
        "Accept an authoring preview",
        "Atomically accept one exact preview after matching the project reference, confirmation fingerprint, and explicit write intent.",
        "authoring.change.accept",
        13,
        requires_project=True,
        read_only=False,
        idempotent=False,
    ),
    McpToolBinding(
        "schuss.authoring.change.preview",
        "Preview an object and patch change",
        "Prepare exact project-local object and optional graph successor bytes without changing accepted project state.",
        "authoring.change.preview",
        13,
        requires_project=True,
        read_only=False,
        idempotent=False,
    ),
    McpToolBinding(
        "schuss.authoring.draft.create",
        "Create a project-local object draft",
        "Create one bounded transparent-compound or native-kernel draft scoped to an exact project revision.",
        "authoring.draft.create",
        13,
        requires_project=True,
        read_only=False,
        idempotent=False,
    ),
    McpToolBinding(
        "schuss.authoring.draft.evaluate",
        "Evaluate an object draft",
        "Run bounded structural evaluation or deterministic native-kernel host audition and cache a content-addressed WAV artifact.",
        "authoring.draft.evaluate",
        13,
        requires_project=True,
        read_only=False,
    ),
    McpToolBinding(
        "schuss.authoring.draft.inspect",
        "Inspect an object draft",
        "Inspect one process-local project-scoped object draft and its separated evidence states.",
        "authoring.draft.inspect",
        13,
        requires_project=True,
    ),
    McpToolBinding(
        "schuss.project.object.inspect",
        "Inspect a project-local object",
        "Inspect one exact accepted project-local object definition.",
        "project.object.inspect",
        13,
        requires_project=True,
    ),
    McpToolBinding(
        "schuss.project.objects.list",
        "List project-local objects",
        "List the exact project-local object definitions in the accepted project closure.",
        "project.objects.list",
        13,
        requires_project=True,
    ),
)

TOOL_BINDINGS = tuple(
    sorted(
        (*READ_ONLY_TOOL_BINDINGS, *SONIC_PLANNING_TOOL_BINDINGS, *PROJECT_AUTHORING_TOOL_BINDINGS),
        key=lambda binding: binding.name,
    )
)
EXPECTED_TOOL_NAMES = tuple(
    binding.name
    for binding in TOOL_BINDINGS
    if not binding.requires_project
)
EXPECTED_PROJECT_TOOL_NAMES = tuple(binding.name for binding in TOOL_BINDINGS)
SERVER_INSTRUCTIONS = (
    "Use exact ID/revision/content-hash references throughout. Plan sonic intent "
    "with validity as a hard gate and keep existing, compound, and native lanes "
    "open; catalog matches are not sonic-quality judgments. Project mutation "
    "requires a preview, the unchanged confirmation fingerprint, and explicit "
    "acceptance. Host measurements do not imply target, device, real-time, or audible support."
)


class McpConfigurationError(ValueError):
    """The selected context cannot provide the closed MCP surface."""


class _ProtocolFault(Exception):
    def __init__(
        self,
        code: int,
        message: str,
        data: Any = _MISSING,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data


class _DuplicateJsonMember(ValueError):
    pass


def _reject_duplicate_members(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJsonMember(f"duplicate JSON member {key!r}")
        result[key] = value
    return result


def _reject_non_json_constant(value: str) -> None:
    raise ValueError(f"non-JSON numeric constant {value!r}")


def _compact_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _schema_operation(node: Any) -> str | None:
    if not isinstance(node, dict):
        return None
    operation = node.get("properties", {}).get("operation")
    if not isinstance(operation, dict):
        return None
    value = operation.get("const")
    return value if isinstance(value, str) else None


def _operation_request_branch(
    schema: Mapping[str, Any], operation: str
) -> dict[str, Any]:
    candidates: list[Mapping[str, Any]] = []
    visited: set[int] = set()

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            if id(value) in visited:
                return
            visited.add(id(value))
            candidates.append(value)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(schema)
    matches = [candidate for candidate in candidates if _schema_operation(candidate) == operation]
    if len(matches) != 1:
        raise McpConfigurationError(
            f"operation {operation!r} must resolve exactly one request-schema branch"
        )
    return copy.deepcopy(dict(matches[0]))


def _referenced_definition_names(value: Any) -> set[str]:
    result: set[str] = set()
    if isinstance(value, dict):
        reference = value.get("$ref")
        if isinstance(reference, str) and reference.startswith("#/$defs/"):
            result.add(reference.removeprefix("#/$defs/"))
        for child in value.values():
            result.update(_referenced_definition_names(child))
    elif isinstance(value, list):
        for child in value:
            result.update(_referenced_definition_names(child))
    return result


def _standalone_subschema(
    schema: Mapping[str, Any], node: Mapping[str, Any]
) -> dict[str, Any]:
    """Copy a schema node and the transitive local definitions it references."""

    result = copy.deepcopy(dict(node))
    source_definitions = schema.get("$defs", {})
    if not isinstance(source_definitions, dict):
        source_definitions = {}
    pending = sorted(_referenced_definition_names(result))
    selected: dict[str, Any] = {}
    while pending:
        name = pending.pop(0)
        if name in selected:
            continue
        definition = source_definitions.get(name)
        if not isinstance(definition, dict):
            raise McpConfigurationError(
                f"schema reference #/$defs/{name} does not resolve exactly"
            )
        selected[name] = copy.deepcopy(definition)
        pending.extend(
            sorted(_referenced_definition_names(definition) - set(selected) - set(pending))
        )
    if selected:
        result["$defs"] = {name: selected[name] for name in sorted(selected)}
    dialect = schema.get("$schema")
    if isinstance(dialect, str):
        result["$schema"] = dialect
    return result


class SchussMcpAdapter:
    """Deterministic tool/resource registry for one exact Schuss context."""

    def __init__(
        self,
        context: OperationContext,
        *,
        project_service: ProjectService | None = None,
        authoring_service: SonicAuthoringService | None = None,
    ) -> None:
        self.context = context
        self.project_service = project_service
        self.authoring_service = authoring_service
        selected = [
            binding
            for binding in TOOL_BINDINGS
            if not binding.requires_project or authoring_service is not None
        ]
        # Intent planning is additive and appears only in v13 contexts. The six
        # historical read-only tools remain byte-for-byte available in v12 sets.
        selected = [
            binding
            for binding in selected
            if binding.request_schema_key in context.schemas
        ]
        self._bindings = {binding.name: binding for binding in selected}
        expected = tuple(sorted(binding.name for binding in selected))
        if tuple(sorted(self._bindings)) != expected:
            raise McpConfigurationError("MCP tool names are duplicate or unstable")
        self._tools = tuple(
            self._build_tool(binding)
            for binding in sorted(selected, key=lambda item: item.name)
        )
        if tuple(tool["name"] for tool in self._tools) != expected:
            raise McpConfigurationError("MCP tools must be deterministically ordered")

    @property
    def tools(self) -> tuple[dict[str, Any], ...]:
        return tuple(copy.deepcopy(tool) for tool in self._tools)

    @property
    def resources(self) -> tuple[dict[str, Any], ...]:
        return (
            {
                "uri": CAPABILITY_RESOURCE_URI,
                "name": "schuss-application-capabilities",
                "title": "Schuss application capabilities",
                "description": (
                    "Canonical application.describe result for the exact selected "
                    "Schuss record-set context."
                ),
                "mimeType": "application/json",
                "annotations": {"audience": ["assistant"], "priority": 1.0},
            },
        )

    def _build_tool(self, binding: McpToolBinding) -> dict[str, Any]:
        request_schema = self.context.schemas.get(binding.request_schema_key)
        result_schema = self.context.schemas.get(binding.result_schema_key)
        if not isinstance(request_schema, dict) or not isinstance(result_schema, dict):
            raise McpConfigurationError(
                f"selected context lacks exact schemas for {binding.operation}"
            )
        branch = _operation_request_branch(request_schema, binding.operation)
        schema_version = branch.get("properties", {}).get("schema_version", {}).get("const")
        if schema_version != binding.request_schema_version:
            raise McpConfigurationError(
                f"operation {binding.operation!r} has an unexpected request schema version"
            )
        payload = branch.get("properties", {}).get("payload")
        if not isinstance(payload, dict) or payload.get("type") != "object":
            raise McpConfigurationError(
                f"operation {binding.operation!r} must have one object payload schema"
            )
        return {
            "name": binding.name,
            "title": binding.title,
            "description": binding.description,
            "inputSchema": _standalone_subschema(request_schema, payload),
            "outputSchema": copy.deepcopy(result_schema),
            "annotations": {
                "readOnlyHint": binding.read_only,
                "destructiveHint": binding.destructive,
                "idempotentHint": binding.idempotent,
                "openWorldHint": False,
            },
        }

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        binding = self._bindings.get(name)
        if binding is None:
            raise _ProtocolFault(INVALID_PARAMS, f"Unknown tool: {name}")
        request = {
            "schema_version": binding.request_schema_version,
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": binding.operation,
            "payload": copy.deepcopy(arguments),
        }
        result = dispatch_operation(
            request,
            self.context,
            project_service=self.project_service,
            authoring_service=self.authoring_service,
        )
        canonical = canonical_result_bytes(result, self.context).decode("utf-8")
        return {
            "content": [{"type": "text", "text": canonical}],
            "structuredContent": copy.deepcopy(result),
            "isError": result["status"] != "success",
        }

    def read_resource(self, uri: str) -> dict[str, Any]:
        if uri != CAPABILITY_RESOURCE_URI:
            raise _ProtocolFault(INVALID_PARAMS, f"Unknown resource URI: {uri}")
        request = {
            "schema_version": "schuss-operation-request-v7",
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": "application.describe",
            "payload": {"scope": "selected-context"},
        }
        result = dispatch_operation(
            request,
            self.context,
            project_service=self.project_service,
            authoring_service=self.authoring_service,
        )
        canonical = canonical_result_bytes(result, self.context).decode("utf-8")
        return {
            "contents": [
                {
                    "uri": CAPABILITY_RESOURCE_URI,
                    "mimeType": "application/json",
                    "text": canonical,
                }
            ]
        }


def _server_capabilities() -> dict[str, Any]:
    return {"tools": {}, "resources": {}}


def _server_meta() -> dict[str, Any]:
    return {SERVER_INFO_META_KEY: copy.deepcopy(SERVER_INFO)}


def _request_identifier(message: Mapping[str, Any]) -> Any:
    value = message.get("id", _MISSING)
    if value is _MISSING:
        return _MISSING
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        return None
    return value


def _error_response(
    request_id: Any,
    code: int,
    message: str,
    data: Any = _MISSING,
) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if data is not _MISSING:
        error["data"] = copy.deepcopy(data)
    return {"jsonrpc": "2.0", "id": request_id, "error": error}


class McpProtocolConnection:
    """One stdio connection with explicit modern/legacy era selection."""

    def __init__(
        self,
        adapter: SchussMcpAdapter,
        *,
        clock: Callable[[], float] = time.monotonic,
        tool_rate_limit: int = TOOL_RATE_LIMIT,
        tool_rate_window_seconds: float = TOOL_RATE_WINDOW_SECONDS,
    ) -> None:
        if tool_rate_limit < 1 or tool_rate_window_seconds <= 0:
            raise ValueError("MCP tool rate-limit configuration must be positive")
        self.adapter = adapter
        self._era: str | None = None
        self._legacy_initialized = False
        self._clock = clock
        self._tool_rate_limit = tool_rate_limit
        self._tool_rate_window_seconds = tool_rate_window_seconds
        self._tool_call_times: deque[float] = deque()

    @property
    def era(self) -> str | None:
        return self._era

    def handle(self, message: Any) -> dict[str, Any] | None:
        if not isinstance(message, dict):
            return _error_response(None, INVALID_REQUEST, "Request must be a JSON object")
        request_id = _request_identifier(message)
        is_notification = request_id is _MISSING
        try:
            return self._handle(message, request_id, is_notification)
        except _ProtocolFault as exc:
            if is_notification:
                return None
            return _error_response(request_id, exc.code, exc.message, exc.data)
        except Exception:
            if is_notification:
                return None
            return _error_response(request_id, INTERNAL_ERROR, "Internal MCP server error")

    def _handle(
        self,
        message: dict[str, Any],
        request_id: Any,
        is_notification: bool,
    ) -> dict[str, Any] | None:
        if message.get("jsonrpc") != "2.0":
            raise _ProtocolFault(INVALID_REQUEST, "jsonrpc must equal '2.0'")
        if not is_notification and request_id is None:
            raise _ProtocolFault(INVALID_REQUEST, "request id must be a string or integer")
        method = message.get("method")
        if not isinstance(method, str) or not method:
            raise _ProtocolFault(INVALID_REQUEST, "method must be a non-empty string")
        params = message.get("params", {})
        if not isinstance(params, dict):
            raise _ProtocolFault(INVALID_PARAMS, "params must be an object")

        if is_notification:
            self._handle_notification(method)
            return None

        if method == "initialize":
            return self._handle_initialize(request_id, params)

        has_modern_meta = isinstance(params.get("_meta"), dict) and (
            PROTOCOL_VERSION_META_KEY in params["_meta"]
        )
        if self._era is None:
            if not has_modern_meta:
                raise _ProtocolFault(
                    INVALID_REQUEST,
                    "initialize or modern per-request metadata is required before ordinary calls",
                )
            self._era = "modern"

        if self._era == "modern":
            self._validate_modern_metadata(params)
            result = self._handle_rpc(method, params, modern=True)
            return self._success_response(request_id, result, modern=True)

        if has_modern_meta:
            raise _ProtocolFault(
                INVALID_REQUEST,
                "modern requests cannot be mixed into an initialized legacy connection",
            )
        if not self._legacy_initialized:
            raise _ProtocolFault(
                INVALID_REQUEST,
                "notifications/initialized is required before legacy ordinary calls",
            )
        result = self._handle_rpc(method, params, modern=False)
        return self._success_response(request_id, result, modern=False)

    def _handle_notification(self, method: str) -> None:
        if method == "notifications/initialized" and self._era == "legacy":
            self._legacy_initialized = True
        # Unknown notifications and cancellation are intentionally ignored. The
        # read-only operations are synchronous and bounded, and notifications do
        # not receive JSON-RPC responses.

    def _handle_initialize(
        self, request_id: Any, params: dict[str, Any]
    ) -> dict[str, Any]:
        if self._era is not None:
            raise _ProtocolFault(INVALID_REQUEST, "initialize must be the first request")
        if set(params) - {"protocolVersion", "capabilities", "clientInfo"}:
            raise _ProtocolFault(INVALID_PARAMS, "initialize contains unknown parameters")
        version = params.get("protocolVersion")
        if version != LEGACY_PROTOCOL_VERSION:
            raise _ProtocolFault(
                INVALID_PARAMS,
                f"unsupported legacy protocol version; supported: {LEGACY_PROTOCOL_VERSION}",
            )
        if not isinstance(params.get("capabilities"), dict):
            raise _ProtocolFault(INVALID_PARAMS, "initialize capabilities must be an object")
        self._validate_implementation(params.get("clientInfo"), "initialize clientInfo")
        self._era = "legacy"
        result = {
            "protocolVersion": LEGACY_PROTOCOL_VERSION,
            "capabilities": _server_capabilities(),
            "serverInfo": copy.deepcopy(SERVER_INFO),
            "instructions": SERVER_INSTRUCTIONS,
        }
        return self._success_response(request_id, result, modern=False)

    @staticmethod
    def _validate_implementation(value: Any, label: str) -> None:
        if not isinstance(value, dict):
            raise _ProtocolFault(INVALID_PARAMS, f"{label} must be an object")
        if not isinstance(value.get("name"), str) or not value["name"]:
            raise _ProtocolFault(INVALID_PARAMS, f"{label}.name must be a non-empty string")
        if not isinstance(value.get("version"), str) or not value["version"]:
            raise _ProtocolFault(INVALID_PARAMS, f"{label}.version must be a non-empty string")

    def _validate_modern_metadata(self, params: dict[str, Any]) -> None:
        metadata = params.get("_meta")
        if not isinstance(metadata, dict):
            raise _ProtocolFault(INVALID_PARAMS, "modern requests require params._meta")
        version = metadata.get(PROTOCOL_VERSION_META_KEY)
        if not isinstance(version, str):
            raise _ProtocolFault(
                INVALID_PARAMS,
                f"params._meta.{PROTOCOL_VERSION_META_KEY} is required",
            )
        if version != MODERN_PROTOCOL_VERSION:
            raise _ProtocolFault(
                UNSUPPORTED_PROTOCOL_VERSION,
                "Unsupported protocol version",
                {
                    "supported": list(SUPPORTED_PROTOCOL_VERSIONS),
                    "requested": version,
                },
            )
        capabilities = metadata.get(CLIENT_CAPABILITIES_META_KEY)
        if not isinstance(capabilities, dict):
            raise _ProtocolFault(
                INVALID_PARAMS,
                f"params._meta.{CLIENT_CAPABILITIES_META_KEY} must be an object",
            )
        client_info = metadata.get(CLIENT_INFO_META_KEY, _MISSING)
        if client_info is not _MISSING:
            self._validate_implementation(client_info, f"params._meta.{CLIENT_INFO_META_KEY}")

    @staticmethod
    def _without_meta(params: dict[str, Any]) -> dict[str, Any]:
        return {key: copy.deepcopy(value) for key, value in params.items() if key != "_meta"}

    @staticmethod
    def _require_keys(
        params: Mapping[str, Any], allowed: set[str], required: set[str] = frozenset()
    ) -> None:
        unknown = sorted(set(params) - allowed)
        missing = sorted(required - set(params))
        if unknown:
            raise _ProtocolFault(
                INVALID_PARAMS, "unknown parameters: " + ", ".join(unknown)
            )
        if missing:
            raise _ProtocolFault(
                INVALID_PARAMS, "missing parameters: " + ", ".join(missing)
            )

    def _handle_rpc(
        self, method: str, params: dict[str, Any], *, modern: bool
    ) -> dict[str, Any]:
        values = self._without_meta(params) if modern else copy.deepcopy(params)
        if method == "server/discover":
            if not modern:
                raise _ProtocolFault(METHOD_NOT_FOUND, "Method not found: server/discover")
            self._require_keys(values, set())
            return self._cacheable(
                {
                    "supportedVersions": list(SUPPORTED_PROTOCOL_VERSIONS),
                    "capabilities": _server_capabilities(),
                    "instructions": SERVER_INSTRUCTIONS,
                },
                modern=True,
            )
        if method == "tools/list":
            self._require_keys(values, {"cursor"})
            if values.get("cursor") is not None:
                raise _ProtocolFault(INVALID_PARAMS, "tool pagination cursor is unsupported")
            return self._cacheable(
                {"tools": [copy.deepcopy(tool) for tool in self.adapter.tools]},
                modern=modern,
            )
        if method == "tools/call":
            self._require_keys(values, {"name", "arguments"}, {"name"})
            name = values.get("name")
            arguments = values.get("arguments", {})
            if not isinstance(name, str) or not name:
                raise _ProtocolFault(INVALID_PARAMS, "tool name must be a non-empty string")
            if not isinstance(arguments, dict):
                raise _ProtocolFault(INVALID_PARAMS, "tool arguments must be an object")
            self._consume_tool_rate_limit()
            return self.adapter.call_tool(name, arguments)
        if method == "resources/list":
            self._require_keys(values, {"cursor"})
            if values.get("cursor") is not None:
                raise _ProtocolFault(INVALID_PARAMS, "resource pagination cursor is unsupported")
            return self._cacheable(
                {
                    "resources": [
                        copy.deepcopy(resource) for resource in self.adapter.resources
                    ]
                },
                modern=modern,
            )
        if method == "resources/templates/list":
            self._require_keys(values, {"cursor"})
            if values.get("cursor") is not None:
                raise _ProtocolFault(
                    INVALID_PARAMS, "resource-template pagination cursor is unsupported"
                )
            return self._cacheable({"resourceTemplates": []}, modern=modern)
        if method == "resources/read":
            self._require_keys(values, {"uri"}, {"uri"})
            uri = values.get("uri")
            if not isinstance(uri, str) or not uri:
                raise _ProtocolFault(INVALID_PARAMS, "resource uri must be a non-empty string")
            return self._cacheable(self.adapter.read_resource(uri), modern=modern)
        if method == "ping" and not modern:
            self._require_keys(values, set())
            return {}
        raise _ProtocolFault(METHOD_NOT_FOUND, f"Method not found: {method}")

    def _consume_tool_rate_limit(self) -> None:
        now = self._clock()
        cutoff = now - self._tool_rate_window_seconds
        while self._tool_call_times and self._tool_call_times[0] <= cutoff:
            self._tool_call_times.popleft()
        if len(self._tool_call_times) >= self._tool_rate_limit:
            retry_after = max(
                0.0,
                self._tool_call_times[0] + self._tool_rate_window_seconds - now,
            )
            raise _ProtocolFault(
                TOOL_RATE_LIMITED,
                "MCP tool invocation rate limit exceeded",
                {"retryAfterMs": max(1, int(retry_after * 1000))},
            )
        self._tool_call_times.append(now)

    @staticmethod
    def _cacheable(value: dict[str, Any], *, modern: bool) -> dict[str, Any]:
        result = copy.deepcopy(value)
        if modern:
            result["ttlMs"] = CACHE_TTL_MS
            result["cacheScope"] = "private"
        return result

    @staticmethod
    def _success_response(
        request_id: Any, result: dict[str, Any], *, modern: bool
    ) -> dict[str, Any]:
        value = copy.deepcopy(result)
        if modern:
            value["resultType"] = "complete"
            value["_meta"] = _server_meta()
        return {"jsonrpc": "2.0", "id": request_id, "result": value}


def _parse_message(data: bytes) -> Any:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise _ProtocolFault(PARSE_ERROR, "Message is not valid UTF-8") from exc
    try:
        return json.loads(
            text,
            object_pairs_hook=_reject_duplicate_members,
            parse_constant=_reject_non_json_constant,
        )
    except (json.JSONDecodeError, _DuplicateJsonMember, ValueError, RecursionError) as exc:
        raise _ProtocolFault(PARSE_ERROR, "Message is not valid JSON") from exc


def _write_message(stdout: BinaryIO, value: dict[str, Any]) -> None:
    data = _compact_json(value) + b"\n"
    written = stdout.write(data)
    if written is not None and written != len(data):
        raise BrokenPipeError("short MCP stdout write")
    flush = getattr(stdout, "flush", None)
    if flush is not None:
        flush()


def _drain_oversized_line(stdin: BinaryIO, initial: bytes) -> None:
    current = initial
    while current and not current.endswith(b"\n"):
        current = stdin.readline(MAX_REQUEST_BYTES + 2)


def serve_stdio(
    adapter: SchussMcpAdapter,
    stdin: BinaryIO,
    stdout: BinaryIO,
    stderr: TextIO,
) -> int:
    """Serve newline-delimited MCP until the client closes stdin."""

    connection = McpProtocolConnection(adapter)
    while True:
        line = stdin.readline(MAX_REQUEST_BYTES + 2)
        if line == b"":
            return 0
        if len(line) > MAX_REQUEST_BYTES:
            _drain_oversized_line(stdin, line)
            _write_message(
                stdout,
                _error_response(
                    None,
                    INVALID_REQUEST,
                    f"MCP message exceeds {MAX_REQUEST_BYTES} bytes",
                ),
            )
            continue
        if not line.endswith(b"\n"):
            _write_message(
                stdout,
                _error_response(None, PARSE_ERROR, "MCP message is not newline-delimited"),
            )
            continue
        payload = line[:-1]
        if payload.endswith(b"\r"):
            payload = payload[:-1]
        try:
            message = _parse_message(payload)
        except _ProtocolFault as exc:
            _write_message(stdout, _error_response(None, exc.code, exc.message))
            continue
        response = connection.handle(message)
        if response is not None:
            _write_message(stdout, response)


def _write_stderr(stderr: TextIO, value: str) -> None:
    try:
        stderr.write(value)
        stderr.flush()
    except (BrokenPipeError, OSError):
        pass


def _record_set_path(value: str | None) -> Path:
    root = REPOSITORY_ROOT.resolve()
    record_set_root = (root / "contracts/record-sets").resolve()
    if value is None:
        supplied = DEFAULT_RECORD_SET_PATH
    else:
        requested = Path(value)
        supplied = requested if requested.is_absolute() else root / requested
    if supplied.is_symlink():
        raise McpConfigurationError("record-set manifest is missing or is a symlink")
    candidate = supplied.resolve()
    try:
        candidate.relative_to(record_set_root)
    except ValueError as exc:
        raise McpConfigurationError(
            "record-set manifest must be inside contracts/record-sets"
        ) from exc
    if not candidate.is_file():
        raise McpConfigurationError("record-set manifest is missing or is a symlink")
    return candidate


def _usage() -> bytes:
    return (
        b"usage: schuss-mcp [--record-set contracts/record-sets/MANIFEST.json] [--project /absolute/workspace]\n"
        b"Serve Schuss discovery over stdio; an explicit project enables preview/accept authoring tools.\n"
    )


def run(
    argv: list[str],
    stdin: BinaryIO,
    stdout: BinaryIO,
    stderr: TextIO,
    *,
    context_loader: Callable[..., OperationContext] = load_repository_context,
) -> int:
    """Parse the human-owned startup configuration, then enter MCP stdio."""

    if argv == ["--help"]:
        data = _usage()
        written = stdout.write(data)
        if written is not None and written != len(data):
            raise BrokenPipeError("short help write")
        return 0
    record_set_value: str | None = None
    project_value: str | None = None
    if len(argv) % 2 != 0:
        _write_stderr(stderr, "schuss-mcp: usage error\n")
        return 2
    for index in range(0, len(argv), 2):
        option, value = argv[index : index + 2]
        if option == "--record-set" and record_set_value is None:
            record_set_value = value
        elif option == "--project" and project_value is None:
            project_value = value
        else:
            _write_stderr(stderr, "schuss-mcp: usage error\n")
            return 2
    try:
        project_service: ProjectService | None = None
        authoring_service: SonicAuthoringService | None = None
        if project_value is None:
            record_set_path = _record_set_path(record_set_value)
            context = context_loader(record_set_path=record_set_path)
        else:
            project_path = Path(project_value)
            if not project_path.is_absolute():
                raise McpConfigurationError("project workspace must be an absolute path")
            if record_set_value is None:
                project_service = ProjectService(project_path)
                loaded = project_service.load()
                context = loaded.context
            else:
                record_set_path = _record_set_path(record_set_value)
                context = context_loader(record_set_path=record_set_path)
                project_service = ProjectService(
                    project_path, initial_context=context
                )
                loaded = project_service.load()
                if loaded.context.record_set_reference != context.record_set_reference:
                    raise McpConfigurationError(
                        "explicit record set does not equal the project's immutable base"
                    )
            if "operation_request_v13" not in context.schemas:
                raise McpConfigurationError(
                    "project base does not include the AI sonic authoring contract"
                )
            authoring_service = SonicAuthoringService(project_service)
        adapter = SchussMcpAdapter(
            context,
            project_service=project_service,
            authoring_service=authoring_service,
        )
    except (OSError, ValueError) as exc:
        message = str(exc)
        message = message.replace(str(REPOSITORY_ROOT.resolve()), "<schuss-root>")
        if record_set_value:
            message = message.replace(str(Path(record_set_value).expanduser()), "<record-set>")
        if project_value:
            message = message.replace(str(Path(project_value).expanduser()), "<project>")
        _write_stderr(stderr, f"schuss-mcp: configuration error: {message}\n")
        return 2
    try:
        return serve_stdio(adapter, stdin, stdout, stderr)
    except BrokenPipeError:
        return 1
    except KeyboardInterrupt:
        _write_stderr(stderr, "schuss-mcp: interrupted\n")
        return 1


def main(argv: list[str] | None = None) -> int:
    return run(
        list(sys.argv[1:] if argv is None else argv),
        sys.stdin.buffer,
        sys.stdout.buffer,
        sys.stderr,
    )


if __name__ == "__main__":
    raise SystemExit(main())
