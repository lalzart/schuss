from __future__ import annotations

import copy
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools/contracts"
for value in (ROOT, TOOLS):
    if str(value) not in sys.path:
        sys.path.insert(0, str(value))

from packages.schuss_core.cli import CATALOG_RECORD_SET_PATH, run as run_cli
from packages.schuss_core.control_plane import (
    canonical_result_bytes,
    dispatch_operation,
    load_repository_context,
)
from packages.schuss_core.product_cli import (
    application_describe_request,
    completion_script,
)
import validator_core as core


RECORD_SET = ROOT / "contracts/record-sets/task023-application-spine-v1.json"
GOLDEN = ROOT / "tools/contracts/tests/fixtures/task023-cli-v2-golden-hashes.json"
HISTORICAL_GOLDEN = (
    ROOT / "tools/contracts/tests/fixtures/task011a-cli-golden-hashes.json"
)


def _digest(value: bytes) -> dict[str, object]:
    return {
        "byte_length": len(value),
        "byte_sha256": hashlib.sha256(value).hexdigest(),
    }


class Task023CliV2Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = load_repository_context(record_set_path=RECORD_SET)
        cls.catalog_context = load_repository_context(
            record_set_path=CATALOG_RECORD_SET_PATH
        )

    def invoke(
        self,
        arguments: list[str],
        *,
        input_bytes: bytes = b"",
        context_loader=None,
    ) -> tuple[int, bytes, str]:
        stdout = io.BytesIO()
        stderr = io.StringIO()
        code = run_cli(
            arguments,
            io.BytesIO(input_bytes),
            stdout,
            stderr,
            context_loader or (lambda **kwargs: self.context),
        )
        return code, stdout.getvalue(), stderr.getvalue()

    def test_root_child_help_and_authoritative_completion_expose_cli_v2(self):
        code, root_help, error = self.invoke(["--help"])
        self.assertEqual((0, ""), (code, error))
        root_groups = (
            "validate",
            "application",
            "catalog",
            "project",
            "graph",
            "gills",
            "build",
            "completion",
            "op",
        )
        for group in root_groups:
            self.assertIn(group.encode("utf-8"), root_help)

        for arguments, commands in (
            (["build", "--help"], ("resolve", "plan", "execute", "completion")),
            (
                ["project", "--help"],
                ("init", "inspect", "validate", "transact", "op", "completion"),
            ),
            (["application", "--help"], ("describe",)),
            (["gills", "--help"], ("inspect",)),
        ):
            code, output, error = self.invoke(arguments)
            self.assertEqual((0, ""), (code, error))
            for command in commands:
                self.assertIn(command.encode("utf-8"), output)

        expected_tokens = set(root_groups) | {
            "describe",
            "search",
            "objects",
            "inspect",
            "init",
            "transact",
            "resolve",
            "plan",
            "execute",
        }
        for shell in ("bash", "zsh", "fish"):
            script = completion_script(shell)
            for token in expected_tokens:
                self.assertIn(token.encode("utf-8"), script, (shell, token))
            if shell == "fish":
                options = (
                    b"-l record-set",
                    b"-l json",
                    b"-l project",
                    b"-l handler",
                    b"-l output-root",
                    b"-l execute",
                )
            else:
                options = (
                    b"--record-set",
                    b"--json",
                    b"--project",
                    b"--handler",
                    b"--output-root",
                    b"--execute",
                )
            for option in options:
                self.assertIn(option, script, (shell, option))

    def test_default_nonproject_commands_select_one_application_context(self):
        cases = (
            (["validate", "--json"], "records.validate", RECORD_SET, self.context),
            (["application", "describe", "--json"], "application.describe", RECORD_SET, self.context),
            (["catalog", "search", "crossfade", "--json"], "catalog.search", CATALOG_RECORD_SET_PATH, self.catalog_context),
            (
                ["catalog", "inspect", "schuss-family-000018@1", "--json"],
                "catalog.inspect",
                CATALOG_RECORD_SET_PATH,
                self.catalog_context,
            ),
            (
                ["graph", "inspect", "schuss-graph-000002@1", "--json"],
                "graph.inspect",
                RECORD_SET,
                self.context,
            ),
            (
                ["build", "resolve", "schuss-build-request-000002@5", "--json"],
                "build.resolve",
                RECORD_SET,
                self.context,
            ),
            (
                ["build", "plan", "schuss-build-request-000002@5", "--json"],
                "build.plan",
                RECORD_SET,
                self.context,
            ),
            (
                ["gills", "inspect", "schuss-instrument-000002@3", "--json"],
                "gills.inspect",
                RECORD_SET,
                self.context,
            ),
        )
        for arguments, operation, manifest, selected_context in cases:
            with self.subTest(operation=operation):
                loaded = []

                def loader(**kwargs):
                    loaded.append(kwargs["record_set_path"])
                    return selected_context

                code, output, error = self.invoke(arguments, context_loader=loader)
                self.assertEqual("", error)
                self.assertIn(code, (0, 1))
                self.assertEqual([manifest.resolve()], loaded)
                value = json.loads(output)
                self.assertEqual(operation, value["operation"])

    def test_each_new_adapter_dispatches_the_existing_shared_operation(self):
        cases = (
            (["application", "describe", "--json"], "application.describe"),
            (
                ["gills", "inspect", "schuss-instrument-000002@3", "--json"],
                "gills.inspect",
            ),
        )
        for arguments, expected in cases:
            with self.subTest(operation=expected):
                requests = []

                def counted(request, context, **services):
                    requests.append(copy.deepcopy(request))
                    return dispatch_operation(request, context, **services)

                with mock.patch(
                    "packages.schuss_core.cli.dispatch_operation", side_effect=counted
                ):
                    code, output, error = self.invoke(arguments)
                self.assertEqual((0, ""), (code, error))
                self.assertTrue(output)
                self.assertEqual([expected], [item["operation"] for item in requests])

    def test_application_json_matches_direct_canonical_result(self):
        request = application_describe_request()
        expected = canonical_result_bytes(
            dispatch_operation(copy.deepcopy(request), self.context), self.context
        ) + b"\n"
        code, output, error = self.invoke(["application", "describe", "--json"])
        self.assertEqual((0, ""), (code, error))
        self.assertEqual(expected, output)

    def test_execute_requires_exact_handler_and_does_not_create_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            output_root = Path(temporary) / "must-not-exist"
            code, output, error = self.invoke(
                [
                    "build",
                    "execute",
                    "schuss-build-request-000002@5",
                    "--output-root",
                    str(output_root),
                    "--execute",
                    "--json",
                ]
            )
            self.assertEqual(2, code)
            self.assertEqual(b"", output)
            self.assertIn("--handler", error)
            self.assertFalse(output_root.exists())

    def test_cli_v2_and_task011a_historical_golden_identities_are_preserved(self):
        self.assertEqual(
            "f4530b7e13e1275df11fdb17a99abaf70758547db36d1025e666cb1aa8c94ed4",
            hashlib.sha256(HISTORICAL_GOLDEN.read_bytes()).hexdigest(),
        )
        retained = core.load_json(GOLDEN)
        self.assertEqual(
            "3a27c68ae935c42d5ac17606ed68da6e74b5e722d1c2a5a274398905a96c7d62",
            hashlib.sha256(GOLDEN.read_bytes()).hexdigest(),
        )
        self.assertEqual(
            {"help", "completion", "human", "json"}, set(retained)
        )
        for section in retained.values():
            self.assertTrue(section)
            for identity in section.values():
                self.assertGreater(identity["byte_length"], 0)
                self.assertRegex(identity["byte_sha256"], r"^[0-9a-f]{64}$")

    def test_completion_shell_syntax_is_valid_when_shell_is_available(self):
        for shell, command in (("bash", ["bash", "-n"]), ("zsh", ["zsh", "-n"])):
            with self.subTest(shell=shell):
                result = subprocess.run(
                    command,
                    input=completion_script(shell),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )
                self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
