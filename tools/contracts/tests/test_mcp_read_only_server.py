from __future__ import annotations

import io
import json
import os
import unittest
from pathlib import Path

from packages.schuss_core.control_plane import (
    canonical_result_bytes,
    dispatch_operation,
    load_repository_context,
)
from packages.schuss_core.mcp_server import (
    CACHE_TTL_MS,
    CAPABILITY_RESOURCE_URI,
    CLIENT_CAPABILITIES_META_KEY,
    CLIENT_INFO_META_KEY,
    DEFAULT_RECORD_SET_PATH,
    EXPECTED_TOOL_NAMES,
    INVALID_PARAMS,
    INVALID_REQUEST,
    LEGACY_PROTOCOL_VERSION,
    MAX_REQUEST_BYTES,
    METHOD_NOT_FOUND,
    MODERN_PROTOCOL_VERSION,
    PARSE_ERROR,
    PROTOCOL_VERSION_META_KEY,
    SERVER_INFO_META_KEY,
    SUPPORTED_PROTOCOL_VERSIONS,
    TOOL_RATE_LIMITED,
    TOOL_BINDINGS,
    UNSUPPORTED_PROTOCOL_VERSION,
    McpProtocolConnection,
    SchussMcpAdapter,
    run,
    serve_stdio,
)


FILTER_NAMES = (
    "function",
    "abstraction",
    "form",
    "signal_domain",
    "signal_rate",
    "signal_role",
    "capability",
    "technique",
    "readiness",
    "provenance",
)


def _filters() -> dict[str, list[str]]:
    return {name: [] for name in FILTER_NAMES}


def _modern_meta(version: str = MODERN_PROTOCOL_VERSION) -> dict[str, object]:
    return {
        PROTOCOL_VERSION_META_KEY: version,
        CLIENT_CAPABILITIES_META_KEY: {},
        CLIENT_INFO_META_KEY: {"name": "schuss-mcp-test", "version": "1.0.0"},
    }


def _modern_request(
    request_id: int,
    method: str,
    **params: object,
) -> dict[str, object]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": {**params, "_meta": _modern_meta()},
    }


class McpReadOnlyServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = load_repository_context(record_set_path=DEFAULT_RECORD_SET_PATH)
        cls.adapter = SchussMcpAdapter(cls.context)
        family_result = dispatch_operation(
            {
                "schema_version": "schuss-operation-request-v2",
                "canonical_profile": "schuss-canonical-json-v1",
                "operation": "catalog.search",
                "payload": {"query": "", "filters": _filters()},
            },
            cls.context,
        )
        cls.family_reference = family_result["value"]["results"][0]["family_reference"]
        contract = cls.context.records["contracts"][0]
        cls.component_reference = {
            "component_contract_id": contract["component_contract_id"],
            "revision": contract["revision"],
            "content_hash": contract["content_hash"],
        }
        graph = cls.context.records["graphs"][0]
        cls.graph_reference = {
            "graph_id": graph["graph_id"],
            "revision": graph["revision"],
            "content_hash": graph["content_hash"],
        }

    def test_tool_registry_is_exact_read_only_and_schema_derived(self) -> None:
        tools = self.adapter.tools
        self.assertEqual(tuple(tool["name"] for tool in tools), EXPECTED_TOOL_NAMES)
        self.assertEqual(len(tools), 7)
        self.assertEqual(
            tuple(
                sorted(
                    binding.name
                    for binding in TOOL_BINDINGS
                    if not binding.requires_project
                )
            ),
            EXPECTED_TOOL_NAMES,
        )
        for tool in tools:
            self.assertEqual(tool["inputSchema"]["type"], "object")
            self.assertEqual(
                tool["inputSchema"]["$schema"],
                "https://json-schema.org/draft/2020-12/schema",
            )
            self.assertTrue(tool["outputSchema"]["$id"].startswith("operation-result-v"))
            self.assertEqual(
                tool["annotations"],
                {
                    "readOnlyHint": True,
                    "destructiveHint": False,
                    "idempotentHint": True,
                    "openWorldHint": False,
                },
            )
        names = " ".join(EXPECTED_TOOL_NAMES)
        for forbidden in ("project", "transact", "build", "device", "upload", "file"):
            self.assertNotIn(forbidden, names)

    def test_modern_discovery_and_per_request_metadata(self) -> None:
        connection = McpProtocolConnection(self.adapter)
        response = connection.handle(_modern_request(1, "server/discover"))
        assert response is not None
        result = response["result"]
        self.assertEqual(result["resultType"], "complete")
        self.assertEqual(result["supportedVersions"], list(SUPPORTED_PROTOCOL_VERSIONS))
        self.assertEqual(result["capabilities"], {"tools": {}, "resources": {}})
        self.assertEqual(result["ttlMs"], CACHE_TTL_MS)
        self.assertEqual(result["cacheScope"], "private")
        self.assertEqual(result["_meta"][SERVER_INFO_META_KEY]["name"], "schuss")
        self.assertNotIn("session", json.dumps(result).lower())

        missing = connection.handle(
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        )
        assert missing is not None
        self.assertEqual(missing["error"]["code"], INVALID_PARAMS)

        unsupported = McpProtocolConnection(self.adapter).handle(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "server/discover",
                "params": {"_meta": _modern_meta("1900-01-01")},
            }
        )
        assert unsupported is not None
        self.assertEqual(unsupported["error"]["code"], UNSUPPORTED_PROTOCOL_VERSION)
        self.assertEqual(
            unsupported["error"]["data"],
            {"supported": list(SUPPORTED_PROTOCOL_VERSIONS), "requested": "1900-01-01"},
        )

    def test_modern_tools_list_is_deterministic_and_all_tools_dispatch_once(self) -> None:
        connection = McpProtocolConnection(self.adapter)
        first = connection.handle(_modern_request(1, "tools/list"))
        second = connection.handle(_modern_request(2, "tools/list"))
        assert first is not None and second is not None
        self.assertEqual(first["result"]["tools"], second["result"]["tools"])
        self.assertEqual(
            tuple(tool["name"] for tool in first["result"]["tools"]),
            EXPECTED_TOOL_NAMES,
        )

        calls = {
            "schuss.application.describe": {"scope": "selected-context"},
            "schuss.catalog.implementations.search": {
                "query": "oscillator",
                "filters": _filters(),
            },
            "schuss.catalog.inspect": {
                "family_reference": self.family_reference,
            },
            "schuss.catalog.search": {
                "query": "oscillator",
                "filters": _filters(),
            },
            "schuss.component.inspect": {
                "component_contract_reference": self.component_reference,
            },
            "schuss.graph.inspect": {"graph_reference": self.graph_reference},
            "schuss.sonic.intent.plan": {
                "intent": {
                    "objective": "A precise but characterful oscillator",
                    "function": "sound-sources",
                    "required_capabilities": [],
                    "desired_character": ["characterful"],
                    "priorities": {"accuracy": 90, "interest": 85, "quality": 95},
                    "novelty_preference": "prefer-distinctive",
                },
                "maximum_existing_candidates": 5,
            },
        }
        bindings = {binding.name: binding for binding in TOOL_BINDINGS}
        for index, (name, arguments) in enumerate(sorted(calls.items()), start=10):
            response = connection.handle(
                _modern_request(
                    index,
                    "tools/call",
                    name=name,
                    arguments=arguments,
                )
            )
            assert response is not None
            result = response["result"]
            canonical = result["structuredContent"]
            self.assertEqual(canonical["operation"], bindings[name].operation)
            self.assertEqual(canonical["status"], "success")
            self.assertFalse(result["isError"])
            self.assertEqual(
                result["content"],
                [
                    {
                        "type": "text",
                        "text": canonical_result_bytes(canonical, self.context).decode("utf-8"),
                    }
                ],
            )

    def test_valid_tool_call_retains_canonical_operation_error(self) -> None:
        connection = McpProtocolConnection(self.adapter)
        response = connection.handle(
            _modern_request(
                1,
                "tools/call",
                name="schuss.catalog.search",
                arguments={"query": "oscillator", "filters": {}},
            )
        )
        assert response is not None
        result = response["result"]
        canonical = result["structuredContent"]
        self.assertTrue(result["isError"])
        self.assertEqual(canonical["operation"], "catalog.search")
        self.assertEqual(canonical["status"], "invalid")
        self.assertEqual(canonical["diagnostics"][0]["code"], "OPERATION_REQUEST_INVALID")
        self.assertEqual(
            result["content"][0]["text"],
            canonical_result_bytes(canonical, self.context).decode("utf-8"),
        )

    def test_unknown_tool_method_and_forbidden_surfaces_are_protocol_errors(self) -> None:
        for index, (method, params, code) in enumerate(
            (
                ("tools/call", {"name": "schuss.project.write", "arguments": {}}, INVALID_PARAMS),
                ("prompts/list", {}, METHOD_NOT_FOUND),
                ("sampling/createMessage", {}, METHOD_NOT_FOUND),
                ("roots/list", {}, METHOD_NOT_FOUND),
                ("device/upload", {}, METHOD_NOT_FOUND),
            ),
            start=1,
        ):
            response = McpProtocolConnection(self.adapter).handle(
                _modern_request(index, method, **params)
            )
            assert response is not None
            self.assertEqual(response["error"]["code"], code)
            self.assertNotIn("result", response)

    def test_tool_calls_are_locally_rate_limited(self) -> None:
        now = [100.0]
        connection = McpProtocolConnection(
            self.adapter,
            clock=lambda: now[0],
            tool_rate_limit=1,
            tool_rate_window_seconds=60.0,
        )
        first = connection.handle(
            _modern_request(
                1,
                "tools/call",
                name="schuss.application.describe",
                arguments={"scope": "selected-context"},
            )
        )
        assert first is not None
        self.assertEqual(first["result"]["structuredContent"]["status"], "success")
        limited = connection.handle(
            _modern_request(
                2,
                "tools/call",
                name="schuss.application.describe",
                arguments={"scope": "selected-context"},
            )
        )
        assert limited is not None
        self.assertEqual(limited["error"]["code"], TOOL_RATE_LIMITED)
        self.assertGreater(limited["error"]["data"]["retryAfterMs"], 0)
        now[0] += 60.0
        recovered = connection.handle(
            _modern_request(
                3,
                "tools/call",
                name="schuss.application.describe",
                arguments={"scope": "selected-context"},
            )
        )
        assert recovered is not None
        self.assertEqual(recovered["result"]["structuredContent"]["status"], "success")

    def test_resource_surface_is_one_pathless_canonical_operation_result(self) -> None:
        connection = McpProtocolConnection(self.adapter)
        listed = connection.handle(_modern_request(1, "resources/list"))
        assert listed is not None
        resources = listed["result"]["resources"]
        self.assertEqual([item["uri"] for item in resources], [CAPABILITY_RESOURCE_URI])
        self.assertNotIn("file:", json.dumps(resources))

        read = connection.handle(
            _modern_request(2, "resources/read", uri=CAPABILITY_RESOURCE_URI)
        )
        assert read is not None
        content = read["result"]["contents"][0]
        canonical = json.loads(content["text"])
        self.assertEqual(content["uri"], CAPABILITY_RESOURCE_URI)
        self.assertEqual(content["mimeType"], "application/json")
        self.assertEqual(canonical["operation"], "application.describe")
        self.assertEqual(canonical["status"], "success")
        self.assertNotIn(str(Path.cwd()), content["text"])

        missing = McpProtocolConnection(self.adapter).handle(
            _modern_request(3, "resources/read", uri="file:///etc/passwd")
        )
        assert missing is not None
        self.assertEqual(missing["error"]["code"], INVALID_PARAMS)

    def test_legacy_initialize_list_call_resource_and_ping(self) -> None:
        connection = McpProtocolConnection(self.adapter)
        initialize = connection.handle(
            {
                "jsonrpc": "2.0",
                "id": "init",
                "method": "initialize",
                "params": {
                    "protocolVersion": LEGACY_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "legacy-test", "version": "1.0.0"},
                },
            }
        )
        assert initialize is not None
        self.assertEqual(initialize["result"]["protocolVersion"], LEGACY_PROTOCOL_VERSION)
        self.assertNotIn("resultType", initialize["result"])
        self.assertNotIn("_meta", initialize["result"])

        premature = connection.handle(
            {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
        )
        assert premature is not None
        self.assertEqual(premature["error"]["code"], INVALID_REQUEST)
        self.assertIsNone(
            connection.handle(
                {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
            )
        )
        listed = connection.handle(
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        )
        assert listed is not None
        self.assertNotIn("resultType", listed["result"])
        self.assertNotIn("ttlMs", listed["result"])
        self.assertEqual(
            tuple(tool["name"] for tool in listed["result"]["tools"]),
            EXPECTED_TOOL_NAMES,
        )

        called = connection.handle(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "schuss.application.describe",
                    "arguments": {"scope": "selected-context"},
                },
            }
        )
        assert called is not None
        self.assertNotIn("resultType", called["result"])
        self.assertEqual(called["result"]["structuredContent"]["status"], "success")

        resource = connection.handle(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "resources/read",
                "params": {"uri": CAPABILITY_RESOURCE_URI},
            }
        )
        assert resource is not None
        self.assertNotIn("cacheScope", resource["result"])
        ping = connection.handle(
            {"jsonrpc": "2.0", "id": 5, "method": "ping", "params": {}}
        )
        self.assertEqual(ping, {"jsonrpc": "2.0", "id": 5, "result": {}})

    def test_stdio_is_protocol_only_rejects_bad_input_and_exits_on_eof(self) -> None:
        valid = json.dumps(
            _modern_request(1, "server/discover"), separators=(",", ":")
        ).encode("utf-8")
        duplicate = (
            b'{"jsonrpc":"2.0","id":2,"id":3,"method":"tools/list","params":{}}'
        )
        stdin = io.BytesIO(valid + b"\n" + duplicate + b"\n" + b"[]\n")
        stdout = io.BytesIO()
        stderr = io.StringIO()
        self.assertEqual(serve_stdio(self.adapter, stdin, stdout, stderr), 0)
        lines = stdout.getvalue().splitlines()
        self.assertEqual(len(lines), 3)
        messages = [json.loads(line) for line in lines]
        self.assertEqual(messages[0]["id"], 1)
        self.assertEqual(messages[1]["error"]["code"], PARSE_ERROR)
        self.assertEqual(messages[2]["error"]["code"], INVALID_REQUEST)
        self.assertEqual(stderr.getvalue(), "")
        self.assertTrue(all(b"\n" not in line for line in lines))

        oversized_stdout = io.BytesIO()
        oversized = b"x" * (MAX_REQUEST_BYTES + 1) + b"\n"
        self.assertEqual(
            serve_stdio(self.adapter, io.BytesIO(oversized), oversized_stdout, io.StringIO()),
            0,
        )
        oversized_result = json.loads(oversized_stdout.getvalue())
        self.assertEqual(oversized_result["error"]["code"], INVALID_REQUEST)

        unterminated_stdout = io.BytesIO()
        self.assertEqual(
            serve_stdio(
                self.adapter,
                io.BytesIO(b'{"jsonrpc":"2.0"}'),
                unterminated_stdout,
                io.StringIO(),
            ),
            0,
        )
        self.assertEqual(
            json.loads(unterminated_stdout.getvalue())["error"]["code"], PARSE_ERROR
        )

    def test_entry_point_configuration_is_closed_and_executable(self) -> None:
        stdout = io.BytesIO()
        stderr = io.StringIO()
        seen: list[Path] = []

        def loader(*, record_set_path: Path):
            seen.append(record_set_path)
            return self.context

        self.assertEqual(run([], io.BytesIO(), stdout, stderr, context_loader=loader), 0)
        self.assertEqual(seen, [DEFAULT_RECORD_SET_PATH.resolve()])
        self.assertEqual(stdout.getvalue(), b"")
        self.assertEqual(stderr.getvalue(), "")

        rejected_stderr = io.StringIO()
        self.assertEqual(
            run(
                ["--record-set", "/tmp/not-a-schuss-record-set.json"],
                io.BytesIO(),
                io.BytesIO(),
                rejected_stderr,
                context_loader=loader,
            ),
            2,
        )
        self.assertIn("inside contracts/record-sets", rejected_stderr.getvalue())
        self.assertEqual(len(seen), 1)

        help_stdout = io.BytesIO()
        self.assertEqual(
            run(["--help"], io.BytesIO(), help_stdout, io.StringIO()),
            0,
        )
        self.assertIn(b"--project /absolute/workspace", help_stdout.getvalue())

        relative_project_stderr = io.StringIO()
        self.assertEqual(
            run(
                ["--project", "relative/workspace"],
                io.BytesIO(),
                io.BytesIO(),
                relative_project_stderr,
                context_loader=loader,
            ),
            2,
        )
        self.assertIn(
            "project workspace must be an absolute path",
            relative_project_stderr.getvalue(),
        )
        self.assertEqual(len(seen), 1)

        entrypoint = Path(__file__).resolve().parents[3] / "bin/schuss-mcp"
        self.assertTrue(entrypoint.is_file())
        self.assertTrue(os.stat(entrypoint).st_mode & 0o111)


if __name__ == "__main__":
    unittest.main()
