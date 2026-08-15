from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools/contracts"
for value in (ROOT, TOOLS):
    if str(value) not in sys.path:
        sys.path.insert(0, str(value))

from packages.schuss_core.control_plane import (
    canonical_result_bytes,
    dispatch_operation,
    load_repository_context,
)
from packages.schuss_core.product_cli import (
    build_completion_script,
    completion_script,
)
from packages.schuss_core.project_cli import project_completion_script
import validator_core as core


CLI = ROOT / "bin/schuss"
ACCEPTED = ROOT / "contracts/record-sets/task005-008-accepted-v0.json"
TASK014 = ROOT / "contracts/record-sets/task014-build-execution-v1.json"
PROJECT = ROOT / "fixtures/task012a/minimal-project"
OPERATION_FIXTURES = (
    ROOT / "tools/contracts/tests/fixtures/task008-operation-requests.json"
)


def _process(
    arguments: list[str],
    *,
    input_bytes: bytes | None = None,
    columns: str | None = None,
) -> subprocess.CompletedProcess[bytes]:
    environment = os.environ.copy()
    if columns is not None:
        environment["COLUMNS"] = columns
    return subprocess.run(
        [str(CLI), *arguments],
        cwd=ROOT,
        env=environment,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _canonical_stream(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )


class CliContractHardeningTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.default_context = load_repository_context()
        cls.task014_context = load_repository_context(record_set_path=TASK014)
        cls.request = next(
            item
            for item in cls.task014_context.records["request"]
            if item["build_request_id"] == "schuss-build-request-000002"
            and item["revision"] == 2
        )
        cls.request_reference = {
            key: cls.request[key]
            for key in ("build_request_id", "revision", "content_hash")
        }
        cls.handler_reference = {
            "build_handler_id": "schuss-build-handler-000001",
            "revision": 1,
            "content_hash": "sha256:31f74bb32eb8203262fd5867545f3ee9be8b75cad2fbcce3fb4434801293e360",
        }

    def test_v5_request_in_v1_context_uses_canonical_invalid_request_fallback(self):
        request = {
            "schema_version": "schuss-operation-request-v5",
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": "build.execute",
            "payload": {
                "build_request_reference": copy.deepcopy(self.request_reference),
                "handler_reference": copy.deepcopy(self.handler_reference),
                "output_locator": "build-output",
                "execution_intent": True,
            },
        }
        direct = dispatch_operation(copy.deepcopy(request), self.default_context)
        process = _process(
            ["op", "--request", "-", "--json"],
            input_bytes=core.canonical_json(request).encode("utf-8") + b"\n",
        )

        self.assertEqual(1, process.returncode)
        self.assertEqual(b"", process.stderr)
        self.assertEqual(
            canonical_result_bytes(direct, self.default_context) + b"\n",
            process.stdout,
        )
        self.assertEqual("schuss-operation-result-v1", direct["schema_version"])
        self.assertEqual("invalid-request", direct["operation"])
        self.assertEqual("invalid", direct["status"])
        self.assertEqual(
            ["OPERATION_REQUEST_INVALID"],
            [item["code"] for item in direct["diagnostics"]],
        )

    def test_human_renderer_preserves_incompatible_context_result(self):
        process = _process(
            [
                "build",
                "plan",
                "schuss-build-request-000001@1",
                "--record-set",
                str(ACCEPTED),
            ]
        )
        self.assertEqual(1, process.returncode)
        self.assertEqual(b"", process.stderr)
        self.assertIn(b"operation: invalid-request\n", process.stdout)
        self.assertIn(b"status: invalid\n", process.stdout)
        self.assertIn(b"code: OPERATION_REQUEST_INVALID\n", process.stdout)
        self.assertNotIn(b"internal operation failure", process.stdout)

    def test_complete_current_json_surface_is_canonical_and_stream_clean(self):
        fixtures = json.loads(OPERATION_FIXTURES.read_text(encoding="utf-8"))
        edits = fixtures["graph_transact_noop"]["payload"]["edits"]
        edits_bytes = core.canonical_json(edits).encode("utf-8") + b"\n"
        cases = (
            (
                "validate",
                ["validate", "--json"],
                None,
                0,
                "records.validate",
                "success",
                "schuss-operation-result-v1",
            ),
            (
                "catalog",
                ["catalog", "search", "crossfade", "--json"],
                None,
                0,
                "catalog.search",
                "success",
                "schuss-operation-result-v2",
            ),
            (
                "graph-inspect",
                ["graph", "inspect", "schuss-graph-000001@1", "--json"],
                None,
                0,
                "graph.inspect",
                "success",
                "schuss-operation-result-v1",
            ),
            (
                "graph-transact",
                [
                    "graph",
                    "transact",
                    "schuss-graph-000001@1",
                    "--edits",
                    "-",
                    "--json",
                ],
                edits_bytes,
                0,
                "graph.transact",
                "success",
                "schuss-operation-result-v1",
            ),
            (
                "project-inspect",
                ["project", "inspect", "--project", str(PROJECT), "--json"],
                None,
                0,
                "project.inspect",
                "success",
                "schuss-operation-result-v3",
            ),
            (
                "project-validate",
                ["project", "validate", "--project", str(PROJECT), "--json"],
                None,
                0,
                "project.validate",
                "success",
                "schuss-operation-result-v3",
            ),
            (
                "build-resolve",
                ["build", "resolve", "schuss-build-request-000001@1", "--json"],
                None,
                1,
                "build.resolve",
                "unresolved",
                "schuss-operation-result-v1",
            ),
            (
                "build-plan",
                ["build", "plan", "schuss-build-request-000002@2", "--json"],
                None,
                0,
                "build.plan",
                "success",
                "schuss-operation-result-v4",
            ),
        )
        for name, arguments, input_bytes, exit_code, operation, status, schema in cases:
            with self.subTest(name=name):
                process = _process(arguments, input_bytes=input_bytes)
                self.assertEqual(exit_code, process.returncode, process.stderr)
                self.assertEqual(b"", process.stderr)
                value = json.loads(process.stdout)
                self.assertEqual(_canonical_stream(value), process.stdout)
                self.assertEqual(operation, value["operation"])
                self.assertEqual(status, value["status"])
                self.assertEqual(schema, value["schema_version"])

    def test_negative_inputs_and_record_sets_are_predispatch_failures(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            invalid_manifest = root / "invalid-record-set.json"
            invalid_manifest.write_bytes(b"{bad}\n")
            missing_manifest = root / "missing-record-set.json"
            missing_request = root / "missing-request.json"
            output_root = root / "must-not-exist"
            cases = (
                (
                    ["graph", "inspect", "schuss-graph-000001@latest", "--json"],
                    None,
                    b"CLI_LOCATOR_MALFORMED",
                ),
                (
                    ["build", "plan", "schuss-build-request-000002@latest", "--json"],
                    None,
                    b"CLI_LOCATOR_MALFORMED",
                ),
                (
                    [
                        "build",
                        "execute",
                        "schuss-build-request-000002@latest",
                        "--output-root",
                        str(output_root),
                        "--execute",
                        "--json",
                    ],
                    None,
                    b"CLI_LOCATOR_MALFORMED",
                ),
                (
                    [
                        "build",
                        "execute",
                        "schuss-build-request-000002@2",
                        "--handler",
                        "schuss-graph-000001@1",
                        "--output-root",
                        str(output_root),
                        "--execute",
                        "--json",
                    ],
                    None,
                    b"CLI_LOCATOR_WRONG_KIND",
                ),
                (
                    ["validate", "--record-set", str(missing_manifest), "--json"],
                    None,
                    b"CLI_RECORD_SET_INVALID",
                ),
                (
                    [
                        "build",
                        "plan",
                        "schuss-build-request-000002@2",
                        "--record-set",
                        str(invalid_manifest),
                        "--json",
                    ],
                    None,
                    b"CLI_RECORD_SET_INVALID",
                ),
                (
                    ["op", "--request", "-", "--json"],
                    b"{bad}\n",
                    b"request input failed",
                ),
                (
                    ["op", "--request", "-", "--json"],
                    b"[]\n",
                    b"operation request must be a JSON object",
                ),
                (
                    ["op", "--request", str(missing_request), "--json"],
                    None,
                    b"request input failed",
                ),
            )
            for arguments, input_bytes, diagnostic in cases:
                with self.subTest(arguments=arguments):
                    process = _process(arguments, input_bytes=input_bytes)
                    self.assertEqual(2, process.returncode)
                    self.assertEqual(b"", process.stdout)
                    self.assertIn(diagnostic, process.stderr)
                    self.assertNotIn(b"Traceback", process.stderr)
            self.assertFalse(output_root.exists())

    def test_build_execution_intent_and_output_roots_fail_closed(self):
        absent_intent = _process(
            [
                "build",
                "execute",
                "schuss-build-request-000002@2",
                "--output-root",
                "unused",
                "--json",
            ]
        )
        self.assertEqual(2, absent_intent.returncode)
        self.assertEqual(b"", absent_intent.stdout)
        self.assertIn(b"--execute", absent_intent.stderr)

        no_intent_request = {
            "schema_version": "schuss-operation-request-v5",
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": "build.execute",
            "payload": {
                "build_request_reference": copy.deepcopy(self.request_reference),
                "handler_reference": copy.deepcopy(self.handler_reference),
                "output_locator": "build-output",
                "execution_intent": False,
            },
        }
        no_intent = _process(
            [
                "op",
                "--request",
                "-",
                "--record-set",
                str(TASK014),
                "--json",
            ],
            input_bytes=core.canonical_json(no_intent_request).encode("utf-8") + b"\n",
        )
        self.assertEqual(1, no_intent.returncode)
        self.assertEqual(b"", no_intent.stderr)
        no_intent_value = json.loads(no_intent.stdout)
        self.assertEqual("invalid", no_intent_value["status"])
        self.assertEqual(
            ["OPERATION_REQUEST_INVALID"],
            [item["code"] for item in no_intent_value["diagnostics"]],
        )

        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            occupied = temporary_path / "occupied"
            occupied.mkdir()
            marker = occupied / "marker"
            marker.write_text("keep", encoding="utf-8")
            existing = _process(
                [
                    "build",
                    "execute",
                    "schuss-build-request-000002@2",
                    "--output-root",
                    str(occupied),
                    "--execute",
                    "--json",
                ]
            )
            self.assertEqual(1, existing.returncode)
            self.assertEqual(b"", existing.stderr)
            existing_value = json.loads(existing.stdout)
            self.assertEqual("failed", existing_value["status"])
            self.assertEqual(
                ["BUILD_OUTPUT_ROOT_EXISTS"],
                [item["code"] for item in existing_value["diagnostics"]],
            )
            self.assertEqual("keep", marker.read_text(encoding="utf-8"))
            self.assertNotIn(str(occupied).encode("utf-8"), existing.stdout)

            missing_parent_root = temporary_path / "missing-parent" / "output"
            missing_parent = _process(
                [
                    "build",
                    "execute",
                    "schuss-build-request-000002@2",
                    "--output-root",
                    str(missing_parent_root),
                    "--execute",
                    "--json",
                ]
            )
            self.assertEqual(1, missing_parent.returncode)
            self.assertEqual(b"", missing_parent.stderr)
            missing_parent_value = json.loads(missing_parent.stdout)
            self.assertEqual(
                ["BUILD_OUTPUT_PARENT_INVALID"],
                [item["code"] for item in missing_parent_value["diagnostics"]],
            )
            self.assertFalse(missing_parent_root.parent.exists())

    def test_help_and_completion_preserve_history_and_cover_build_grammar(self):
        help_hashes = {
            "root": "f0cfe4c99ace639652c8d127c1def34055510cb8cfcf1990f86427728196aa93",
            "build": "2fbc0ab3be00cc5a142557f48e710db20b4b7b5ec0ec3087a1a09e2246ce8c89",
        }
        help_cases = {
            "root": ["--help"],
            "build": ["build", "--help"],
            "build-plan": ["build", "plan", "--help"],
            "build-execute": ["build", "execute", "--help"],
            "project": ["project", "--help"],
        }
        for name, arguments in help_cases.items():
            with self.subTest(help=name):
                narrow = _process(arguments, columns="29")
                wide = _process(arguments, columns="211")
                self.assertEqual(0, narrow.returncode)
                self.assertEqual(b"", narrow.stderr)
                self.assertEqual(narrow.stdout, wide.stdout)
                self.assertLessEqual(max(map(len, narrow.stdout.splitlines())), 80)
                if name in help_hashes:
                    self.assertEqual(
                        help_hashes[name], hashlib.sha256(narrow.stdout).hexdigest()
                    )
        execute_help = _process(help_cases["build-execute"]).stdout
        for option in (
            b"--handler",
            b"--output-root",
            b"--execute",
            b"--record-set",
            b"--json",
        ):
            self.assertIn(option, execute_help)

        legacy_hashes = {
            "bash": "54b604a3ca4cfd768bc20e21744eb19a175906767e4cdf2f46c2441468c94c51",
            "zsh": "32b548eb3b28b89c84c193bc9de32f1ef2c92ea3d7d1393471fb9fc5e1067f2c",
            "fish": "17cc15956e4a5b392e209e328badf7fd51fdcb0c1534610f00daf0dff6b1aeda",
        }
        project_hashes = {
            "bash": "f8c907c42387842d2beac1682f70d6de5a867e8e6537e7e768e90a10851795c2",
            "zsh": "5435f7e059f2693a596af4cf0afaab5f9bd2050d33d27033c9923c4121b2639f",
            "fish": "6b8bfec5d4f1f5e90b5b10892c1c7d01f48114b297192ba05da5946716f70e81",
        }
        build_hashes = {
            "bash": "fc7febb26170a49705d7542cac1ad6f9e091a96aca1c8e80f2f1a070b0d96ef0",
            "zsh": "28f2f9af61902eac9aa1b5f7eb6fe58261d105d6bef9345284408b26b508744e",
            "fish": "3b2fcc9684bcb287f5dbf6c644b7f4a6f322b98866f115b2198e4d3535125f2c",
        }
        for shell in ("bash", "zsh", "fish"):
            with self.subTest(completion=shell):
                self.assertEqual(
                    legacy_hashes[shell],
                    hashlib.sha256(completion_script(shell)).hexdigest(),
                )
                self.assertEqual(
                    project_hashes[shell],
                    hashlib.sha256(project_completion_script(shell)).hexdigest(),
                )
                build = build_completion_script(shell)
                self.assertEqual(
                    build_hashes[shell], hashlib.sha256(build).hexdigest()
                )
                process = _process(["build", "completion", shell])
                self.assertEqual(0, process.returncode)
                self.assertEqual(b"", process.stderr)
                self.assertEqual(build, process.stdout)
                for token in (
                    b"resolve",
                    b"plan",
                    b"execute",
                ):
                    self.assertIn(token, build)
                if shell == "fish":
                    option_tokens = (
                        b"-l record-set",
                        b"-l json",
                        b"-l handler",
                        b"-l output-root",
                        b"-l execute",
                    )
                else:
                    option_tokens = (
                        b"--record-set",
                        b"--json",
                        b"--handler",
                        b"--output-root",
                        b"--execute",
                    )
                for token in option_tokens:
                    self.assertIn(token, build)
                for forbidden in (b"contracts/", b"schuss-record-set-", b"curl ", b"git "):
                    self.assertNotIn(forbidden, build)

        for shell, syntax_command in (("bash", ["bash", "-n"]), ("zsh", ["zsh", "-n"])):
            for script in (
                completion_script(shell),
                project_completion_script(shell),
                build_completion_script(shell),
            ):
                syntax = subprocess.run(
                    syntax_command,
                    input=script,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )
                self.assertEqual(0, syntax.returncode, syntax.stderr)

        bash_probe = subprocess.run(
            ["bash"],
            input=(
                build_completion_script("bash")
                + b'COMP_WORDS=(schuss build execute "")\n'
                + b"COMP_CWORD=3\n"
                + b'_schuss_build_complete\n'
                + b'printf "%s\\n" "${COMPREPLY[@]}"\n'
            ),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(0, bash_probe.returncode, bash_probe.stderr)
        self.assertEqual(
            {
                b"--handler",
                b"--output-root",
                b"--execute",
                b"--record-set",
                b"--json",
                b"--help",
            },
            set(bash_probe.stdout.splitlines()),
        )


if __name__ == "__main__":
    unittest.main()
