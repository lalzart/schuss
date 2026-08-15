import ast
import copy
import hashlib
import io
import json
import os
import pty
import shutil
import subprocess
import sys
import tempfile
import tty
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools/contracts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from packages.schuss_core import (
    canonical_result_bytes,
    dispatch_operation,
    load_repository_context,
)
from packages.schuss_core.cli import run as run_cli
from packages.schuss_core.product_cli import (
    build_resolve_request,
    graph_inspect_request,
    graph_transact_request,
    records_validate_request,
    render_human_result,
    resolve_locator,
)

import record_set_rules
import validator_core as core


CLI = ROOT / "bin/schuss"
SUCCESSOR = ROOT / "contracts/record-sets/task009-executed-prospective-v0.json"
ACCEPTED = ROOT / "contracts/record-sets/task005-008-accepted-v0.json"
PREREQUISITE = ROOT / "contracts/record-sets/task009-prospective-v0.json"
OPERATION_FIXTURES = (
    ROOT / "tools/contracts/tests/fixtures/task008-operation-requests.json"
)
GOLDEN_HASHES = (
    ROOT / "tools/contracts/tests/fixtures/task010-cli-golden-hashes.json"
)


def _process(arguments, *, input_bytes=b"", cwd=ROOT, environment=None):
    env = os.environ.copy()
    if environment:
        env.update(environment)
    return subprocess.run(
        [str(CLI), *arguments],
        cwd=cwd,
        env=env,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _digest(value):
    return {
        "byte_length": len(value),
        "byte_sha256": hashlib.sha256(value).hexdigest(),
    }


class _BrokenOutput:
    def write(self, data):
        raise BrokenPipeError("fixture closed pipe")

    def flush(self):
        return None


class Task010ProductCliTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.default_context = load_repository_context(ROOT)
        cls.successor_context = load_repository_context(
            ROOT, record_set_path=SUCCESSOR
        )
        cls.fixtures = core.load_json(OPERATION_FIXTURES)
        cls.edits = copy.deepcopy(
            cls.fixtures["graph_transact_noop"]["payload"]["edits"]
        )
        cls.edits_bytes = core.canonical_json(cls.edits).encode("utf-8")

    def test_every_product_command_dispatches_exactly_one_shared_operation(self):
        cases = (
            (["validate"], b"", "records.validate"),
            (
                ["graph", "inspect", "schuss-graph-000001@1"],
                b"",
                "graph.inspect",
            ),
            (
                [
                    "graph",
                    "transact",
                    "schuss-graph-000001@1",
                    "--edits",
                    "-",
                ],
                self.edits_bytes,
                "graph.transact",
            ),
            (
                ["build", "resolve", "schuss-build-request-000001@1"],
                b"",
                "build.resolve",
            ),
        )
        for arguments, input_bytes, operation in cases:
            with self.subTest(arguments=arguments):
                calls = []

                def counted(request, context):
                    calls.append(copy.deepcopy(request))
                    return dispatch_operation(request, context)

                with mock.patch(
                    "packages.schuss_core.cli.dispatch_operation", side_effect=counted
                ):
                    code = run_cli(
                        arguments,
                        io.BytesIO(input_bytes),
                        io.BytesIO(),
                        io.StringIO(),
                        lambda **kwargs: self.default_context,
                    )
                self.assertIn(code, (0, 1))
                self.assertEqual(1, len(calls))
                self.assertEqual(operation, calls[0]["operation"])

    def test_request_constructors_are_exact_existing_operation_envelopes(self):
        graph_reference = resolve_locator(
            "schuss-graph-000001@1",
            expected_kind="graph",
            context=self.default_context,
        )
        request_reference = resolve_locator(
            "schuss-build-request-000001@1",
            expected_kind="build-request",
            context=self.default_context,
        )
        self.assertEqual(
            self.fixtures["records_validate"], records_validate_request()
        )
        self.assertEqual(
            self.fixtures["graph_inspect"], graph_inspect_request(graph_reference)
        )
        self.assertEqual(
            self.fixtures["graph_transact_noop"],
            graph_transact_request(graph_reference, self.edits),
        )
        self.assertEqual(
            self.fixtures["build_resolve"],
            build_resolve_request(request_reference),
        )

    def test_default_json_matches_direct_api_and_frozen_op_bytes(self):
        cases = (
            (["validate", "--json"], "records_validate", b"", 0),
            (
                ["graph", "inspect", "schuss-graph-000001@1", "--json"],
                "graph_inspect",
                b"",
                0,
            ),
            (
                [
                    "graph",
                    "transact",
                    "schuss-graph-000001@1",
                    "--edits",
                    "-",
                    "--json",
                ],
                "graph_transact_noop",
                self.edits_bytes,
                0,
            ),
            (
                ["build", "resolve", "schuss-build-request-000001@1", "--json"],
                "build_resolve",
                b"",
                1,
            ),
        )
        for arguments, fixture_name, product_input, expected_exit in cases:
            with self.subTest(arguments=arguments):
                request = self.fixtures[fixture_name]
                direct = canonical_result_bytes(
                    dispatch_operation(copy.deepcopy(request), self.default_context),
                    self.default_context,
                ) + b"\n"
                product = _process(arguments, input_bytes=product_input)
                machine = _process(
                    ["op", "--request", "-", "--json"],
                    input_bytes=core.canonical_json(request).encode("utf-8") + b"\n",
                )
                self.assertEqual(expected_exit, product.returncode)
                self.assertEqual(expected_exit, machine.returncode)
                self.assertEqual(direct, product.stdout)
                self.assertEqual(direct, machine.stdout)
                self.assertEqual(b"", product.stderr)
                self.assertEqual(b"", machine.stderr)

    def test_successor_build_json_matches_direct_api_and_op_without_execution(self):
        reference = resolve_locator(
            "schuss-build-request-000001@2",
            expected_kind="build-request",
            context=self.successor_context,
        )
        request = build_resolve_request(reference)
        direct_result = dispatch_operation(copy.deepcopy(request), self.successor_context)
        direct = canonical_result_bytes(direct_result, self.successor_context) + b"\n"
        arguments = [
            "--record-set",
            str(SUCCESSOR),
            "--json",
        ]
        product = _process(
            ["build", "resolve", "schuss-build-request-000001@2", *arguments]
        )
        machine = _process(
            ["op", "--request", "-", "--record-set", str(SUCCESSOR), "--json"],
            input_bytes=core.canonical_json(request).encode("utf-8") + b"\n",
        )
        self.assertEqual("success", direct_result["status"])
        self.assertEqual(0, product.returncode)
        self.assertEqual(0, machine.returncode)
        self.assertEqual(direct, product.stdout)
        self.assertEqual(direct, machine.stdout)
        self.assertEqual(b"", product.stderr)
        self.assertEqual(b"", machine.stderr)
        self.assertEqual(
            "absent",
            direct_result["value"]["backend_invocation"]["boundary"][
                "executable_handler_status"
            ],
        )

    def test_default_never_selects_the_later_request_ambiently(self):
        default = _process(
            ["build", "resolve", "schuss-build-request-000001@1", "--json"]
        )
        implicit_latest = _process(
            ["build", "resolve", "schuss-build-request-000001@2", "--json"]
        )
        self.assertEqual(1, default.returncode)
        self.assertEqual("unresolved", json.loads(default.stdout)["status"])
        self.assertEqual(2, implicit_latest.returncode)
        self.assertEqual(b"", implicit_latest.stdout)
        self.assertIn(b"CLI_LOCATOR_NOT_FOUND", implicit_latest.stderr)

    def _human_cases(self):
        return {
            "validate-default": (["validate"], b""),
            "graph-inspect-default": (
                ["graph", "inspect", "schuss-graph-000001@1"],
                b"",
            ),
            "graph-transact-default": (
                [
                    "graph",
                    "transact",
                    "schuss-graph-000001@1",
                    "--edits",
                    "-",
                ],
                self.edits_bytes,
            ),
            "build-unresolved-default": (
                ["build", "resolve", "schuss-build-request-000001@1"],
                b"",
            ),
            "build-success-successor": (
                [
                    "build",
                    "resolve",
                    "schuss-build-request-000001@2",
                    "--record-set",
                    str(SUCCESSOR),
                ],
                b"",
            ),
        }

    def test_human_outputs_match_golden_hashes_and_keep_exact_statuses(self):
        golden = core.load_json(GOLDEN_HASHES)["human"]
        observed = {}
        for name, (arguments, input_bytes) in self._human_cases().items():
            process = _process(arguments, input_bytes=input_bytes)
            self.assertIn(process.returncode, (0, 1), name)
            self.assertEqual(b"", process.stderr, name)
            observed[name] = _digest(process.stdout)
            self.assertNotIn(b"\x1b", process.stdout)
            self.assertNotIn(b"\r", process.stdout)
            self.assertNotRegex(
                process.stdout,
                rb"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
            )
            self.assertNotRegex(
                process.stdout,
                rb"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
            )
            for forbidden in (
                str(ROOT).encode(),
                b"/Users/",
                b"/private/",
                b"/tmp/",
            ):
                self.assertNotIn(forbidden, process.stdout, name)
        self.assertEqual(golden, observed)
        self.assertIn(b"status: unresolved\n", _process(
            ["build", "resolve", "schuss-build-request-000001@1"]
        ).stdout)
        self.assertIn(b"status: success\n", _process(
            [
                "build",
                "resolve",
                "schuss-build-request-000001@2",
                "--record-set",
                str(SUCCESSOR),
            ]
        ).stdout)
        validation = _process(["validate"]).stdout
        for evidence_level in (
            b"structural-schema-validation",
            b"arm-compilation-linking",
            b"connected-device-execution",
            b"real-time-resource-validation",
            b"audible-listening-validation",
        ):
            self.assertIn(evidence_level, validation)

    def test_human_transaction_is_explicitly_non_persisted(self):
        graph = ROOT / "contracts/graphs/blend-crossfader-v0.json"
        before = graph.read_bytes()
        process = _process(
            [
                "graph",
                "transact",
                "schuss-graph-000001@1",
                "--edits",
                "-",
            ],
            input_bytes=self.edits_bytes,
        )
        self.assertEqual(0, process.returncode)
        self.assertIn(b"proposal_status: proposed-non-persisted\n", process.stdout)
        self.assertIn(b"persistence_status: not-written\n", process.stdout)
        self.assertEqual(before, graph.read_bytes())

    def test_human_renderer_preserves_conflict_and_diagnostic_order(self):
        request = copy.deepcopy(self.fixtures["graph_transact_noop"])
        request["payload"]["base_content_hash"] = "sha256:" + "0" * 64
        result = dispatch_operation(request, self.default_context)
        output = render_human_result(result, self.default_context, request)
        self.assertIn(b"status: conflict\n", output)
        positions = [
            output.index(field)
            for field in (
                b"severity:",
                b"code:",
                b"subject:",
                b"location:",
                b"message:",
            )
        ]
        self.assertEqual(sorted(positions), positions)

        invalid = _process(
            [
                "graph",
                "transact",
                "schuss-graph-000001@1",
                "--edits",
                "-",
            ],
            input_bytes=b"[]",
        )
        self.assertEqual(1, invalid.returncode)
        self.assertEqual(b"", invalid.stderr)
        self.assertIn(b"status: invalid\n", invalid.stdout)

    def test_human_output_is_fresh_process_cwd_locale_width_and_host_independent(self):
        arguments = ["graph", "inspect", "schuss-graph-000001@1"]
        outputs = []
        with (
            tempfile.TemporaryDirectory(prefix="task010-alpha-") as alpha,
            tempfile.TemporaryDirectory(prefix="task010-omega-") as omega,
            tempfile.TemporaryDirectory(
                prefix="task010-output-alpha-"
            ) as output_alpha,
            tempfile.TemporaryDirectory(
                prefix="task010-output-omega-"
            ) as output_omega,
        ):
            settings = (
                (
                    alpha,
                    output_alpha,
                    "C",
                    "31",
                    "fixture-user-a",
                    "fixture-host-a",
                ),
                (
                    omega,
                    output_omega,
                    "de_DE.UTF-8",
                    "211",
                    "fixture-user-b",
                    "fixture-host-b",
                ),
            )
            for cwd, output_root, locale_name, columns, user, host in settings:
                environment = os.environ.copy()
                environment.update(
                    {
                        "LC_ALL": locale_name,
                        "LANG": locale_name,
                        "COLUMNS": columns,
                        "USER": user,
                        "LOGNAME": user,
                        "HOSTNAME": host,
                    }
                )
                output_path = Path(output_root) / "result.txt"
                with output_path.open("wb") as output_file:
                    process = subprocess.run(
                        [str(CLI), *arguments],
                        cwd=Path(cwd),
                        env=environment,
                        stdin=subprocess.DEVNULL,
                        stdout=output_file,
                        stderr=subprocess.PIPE,
                        check=False,
                    )
                self.assertEqual(0, process.returncode)
                self.assertEqual(b"", process.stderr)
                output = output_path.read_bytes()
                outputs.append(output)
                for forbidden in (
                    str(ROOT).encode(),
                    str(cwd).encode(),
                    str(output_root).encode(),
                    user.encode(),
                    host.encode(),
                ):
                    self.assertNotIn(forbidden, output)
        self.assertEqual(outputs[0], outputs[1])

    def test_human_output_is_identical_for_raw_tty_and_pipe_capture(self):
        arguments = ["graph", "inspect", "schuss-graph-000001@1"]
        piped = _process(arguments)
        master, slave = pty.openpty()
        tty.setraw(slave)
        process = subprocess.Popen(
            [str(CLI), *arguments],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            stdout=slave,
            stderr=subprocess.PIPE,
        )
        os.close(slave)
        chunks = []
        while True:
            try:
                chunk = os.read(master, 65536)
            except OSError:
                break
            if not chunk:
                break
            chunks.append(chunk)
        os.close(master)
        stderr = process.stderr.read()
        process.stderr.close()
        returncode = process.wait()
        self.assertEqual(0, returncode)
        self.assertEqual(b"", stderr)
        self.assertEqual(piped.stdout, b"".join(chunks))

    def _help_cases(self):
        return {
            "validate": ["validate", "--help"],
            "graph": ["graph", "--help"],
            "graph-inspect": ["graph", "inspect", "--help"],
            "graph-transact": ["graph", "transact", "--help"],
            "build": ["build", "--help"],
            "build-resolve": ["build", "resolve", "--help"],
            "completion": ["completion", "--help"],
            "op": ["op", "--help"],
        }

    def test_all_help_pages_are_fixed_width_and_match_golden_hashes(self):
        historical = core.load_json(GOLDEN_HASHES)["help"]
        golden = {key: value for key, value in historical.items() if key != "root"}
        observed = {}
        for name, arguments in self._help_cases().items():
            narrow = _process(arguments, environment={"COLUMNS": "25"})
            wide = _process(arguments, environment={"COLUMNS": "240"})
            self.assertEqual(0, narrow.returncode, name)
            self.assertEqual(b"", narrow.stderr, name)
            self.assertEqual(narrow.stdout, wide.stdout, name)
            self.assertLessEqual(
                max(len(line) for line in narrow.stdout.splitlines()), 80, name
            )
            observed[name] = _digest(narrow.stdout)
        self.assertEqual(golden, observed)
        self.assertEqual(
            "2373c57ed53676470eb077b79156c4f7f44b1e21c4f1f3d6bd98393e8c2fc146",
            hashlib.sha256(GOLDEN_HASHES.read_bytes()).hexdigest(),
        )
        root = _process(["--help"]).stdout
        for unsupported in (b"upload", b"flash", b"hardware connection"):
            self.assertNotIn(unsupported, root.lower())

    def test_plain_build_and_abbreviations_are_deterministic_usage_failures(self):
        plain = _process(["build"])
        abbreviation = _process(["validate", "--j"])
        self.assertEqual(2, plain.returncode)
        self.assertEqual(b"", plain.stdout)
        self.assertIn(b"usage error", plain.stderr)
        self.assertIn(b"resolution only", plain.stderr)
        self.assertEqual(2, abbreviation.returncode)
        self.assertEqual(b"", abbreviation.stdout)

    def test_completion_is_static_loader_free_and_matches_golden_hashes(self):
        observed = {}

        def forbidden_loader(**kwargs):
            raise AssertionError("completion attempted to load records")

        for shell in ("bash", "zsh", "fish"):
            stdout = io.BytesIO()
            stderr = io.StringIO()
            code = run_cli(
                ["completion", shell],
                io.BytesIO(),
                stdout,
                stderr,
                forbidden_loader,
            )
            self.assertEqual(0, code)
            self.assertEqual("", stderr.getvalue())
            value = stdout.getvalue()
            observed[shell] = _digest(value)
            for forbidden in (
                b"contracts/",
                b"schuss-record-set-",
                b"schuss-graph-",
                b"curl ",
                b"git ",
                b".bashrc",
                b".zshrc",
                b"config/fish",
            ):
                self.assertNotIn(forbidden, value)
        self.assertEqual({"bash", "zsh", "fish"}, set(observed))
        self.assertEqual(
            "2373c57ed53676470eb077b79156c4f7f44b1e21c4f1f3d6bd98393e8c2fc146",
            hashlib.sha256(GOLDEN_HASHES.read_bytes()).hexdigest(),
        )
        bash = _process(["completion", "bash"])
        zsh = _process(["completion", "zsh"])
        self.assertEqual(0, subprocess.run(["bash", "-n"], input=bash.stdout).returncode)
        self.assertEqual(0, subprocess.run(["zsh", "-n"], input=zsh.stdout).returncode)

    def test_locator_positive_and_negative_matrix_fails_before_dispatch(self):
        valid_graph = _process(
            ["graph", "inspect", "schuss-graph-000001@1", "--json"]
        )
        valid_request = _process(
            ["build", "resolve", "schuss-build-request-000001@1", "--json"]
        )
        self.assertEqual(0, valid_graph.returncode)
        self.assertEqual(1, valid_request.returncode)
        cases = (
            ("graph", ["graph", "inspect", "schuss-graph-000001"]),
            ("graph", ["graph", "inspect", "schuss-graph-000001@0"]),
            ("graph", ["graph", "inspect", "schuss-graph-000001@01"]),
            ("latest", ["graph", "inspect", "schuss-graph-000001@latest"]),
            ("display-name", ["graph", "inspect", "Blend@1"]),
            ("graph", ["graph", "inspect", "schuss-graph-999999@1"]),
            (
                "wrong-kind",
                ["graph", "inspect", "schuss-build-request-000001@1"],
            ),
            (
                "wrong-kind",
                ["build", "resolve", "schuss-graph-000001@1"],
            ),
        )
        for name, arguments in cases:
            with self.subTest(name=name, arguments=arguments):
                process = _process(arguments)
                self.assertEqual(2, process.returncode)
                self.assertEqual(b"", process.stdout)
                self.assertIn(b"CLI_LOCATOR_", process.stderr)

        duplicated = self.default_context.with_records(
            graphs=(
                *self.default_context.records["graphs"],
                copy.deepcopy(self.default_context.records["graphs"][0]),
            )
        )
        stdout = io.BytesIO()
        stderr = io.StringIO()
        with mock.patch("packages.schuss_core.cli.dispatch_operation") as dispatch:
            code = run_cli(
                ["graph", "inspect", "schuss-graph-000001@1"],
                io.BytesIO(),
                stdout,
                stderr,
                lambda **kwargs: duplicated,
            )
        self.assertEqual(2, code)
        self.assertEqual(b"", stdout.getvalue())
        self.assertIn("CLI_LOCATOR_AMBIGUOUS", stderr.getvalue())
        dispatch.assert_not_called()

    def _copy_manifests(self, destination):
        for path in (ACCEPTED, PREREQUISITE, SUCCESSOR):
            shutil.copy2(path, destination / path.name)

    def _rewrite_manifest(self, path, mutation):
        value = core.load_json(path)
        mutation(value)
        schema = core.load_json(ROOT / record_set_rules.RECORD_SET_SCHEMA)
        value["content_hash"] = core.record_content_hash(value, schema)
        path.write_text(core.canonical_json(value) + "\n", encoding="utf-8")

    def test_record_set_failure_matrix_is_exit_two_and_pre_dispatch(self):
        def duplicate(value):
            value["record_members"].append(copy.deepcopy(value["record_members"][0]))

        def stale_raw(value):
            value["record_members"][0]["byte_sha256"] = "0" * 64

        def stale_schema(value):
            value["schema_members"][0]["byte_sha256"] = "0" * 64

        def stale_semantic(value):
            value["record_members"][0]["content_hash"] = "sha256:" + "0" * 64

        def unlisted(value):
            value["record_members"].pop()

        def missing(value):
            value["record_members"][0]["portable_path"] = "contracts/task009/missing.json"

        def absolute(value):
            value["record_members"][0]["portable_path"] = "/tmp/not-portable.json"

        def traversal(value):
            value["record_members"][0]["portable_path"] = "../not-portable.json"

        def wrong_parent(value):
            value["parent_reference"]["content_hash"] = "sha256:" + "0" * 64

        def false_root(value):
            value["purpose"] = "accepted-baseline"
            value["parent_reference"] = {"status": "omitted"}

        mutations = {
            "duplicate": duplicate,
            "raw-hash": stale_raw,
            "schema-hash": stale_schema,
            "semantic-hash": stale_semantic,
            "unlisted": unlisted,
            "missing": missing,
            "absolute": absolute,
            "traversal": traversal,
            "wrong-parent": wrong_parent,
            "false-root": false_root,
        }
        for name, mutation in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                self._copy_manifests(root)
                selected = root / SUCCESSOR.name
                self._rewrite_manifest(selected, mutation)
                process = _process(
                    ["validate", "--record-set", str(selected), "--json"]
                )
                self.assertEqual(2, process.returncode)
                self.assertEqual(b"", process.stdout)
                self.assertIn(b"CLI_RECORD_SET_INVALID", process.stderr)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._copy_manifests(root)
            selected = root / SUCCESSOR.name
            value = core.load_json(selected)
            value["content_hash"] = "sha256:" + "0" * 64
            selected.write_text(core.canonical_json(value) + "\n", encoding="utf-8")
            process = _process(
                ["validate", "--record-set", str(selected), "--json"]
            )
            self.assertEqual(2, process.returncode)
            self.assertEqual(b"", process.stdout)
            self.assertIn(b"CLI_RECORD_SET_INVALID", process.stderr)

        with tempfile.TemporaryDirectory() as temporary:
            missing_manifest = Path(temporary) / "absent.json"
            process = _process(
                ["validate", "--record-set", str(missing_manifest), "--json"]
            )
            self.assertEqual(2, process.returncode)
            self.assertEqual(b"", process.stdout)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._copy_manifests(root)
            selected = root / SUCCESSOR.name
            selected.write_bytes(b"{\n")
            process = _process(
                ["validate", "--record-set", str(selected), "--json"]
            )
            self.assertEqual(2, process.returncode)
            self.assertEqual(b"", process.stdout)

        explicit_default = _process(
            ["validate", "--record-set", str(ACCEPTED), "--json"]
        )
        implicit_default = _process(["validate", "--json"])
        self.assertEqual(0, explicit_default.returncode)
        self.assertEqual(implicit_default.stdout, explicit_default.stdout)

    def test_explicit_successor_identifies_only_its_exact_record_set(self):
        process = _process(
            [
                "build",
                "resolve",
                "schuss-build-request-000001@2",
                "--record-set",
                str(SUCCESSOR),
            ]
        )
        self.assertEqual(0, process.returncode)
        self.assertIn(b"record_set: schuss-record-set-000003@1\n", process.stdout)
        self.assertIn(
            b"record_set_content_hash: sha256:2f3706b7ccf08b59356bbfcadbdb37d0437b01857a9c50ba6e5d84e24a9b95c0\n",
            process.stdout,
        )
        self.assertNotIn(str(SUCCESSOR).encode(), process.stdout)

    def test_edits_file_stdin_and_malformed_input_boundaries(self):
        graph = ROOT / "contracts/graphs/blend-crossfader-v0.json"
        graph_before = graph.read_bytes()
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "edits.json"
            path.write_bytes(self.edits_bytes)
            file_input = _process(
                [
                    "graph",
                    "transact",
                    "schuss-graph-000001@1",
                    "--edits",
                    str(path),
                    "--json",
                ]
            )
            stdin_input = _process(
                [
                    "graph",
                    "transact",
                    "schuss-graph-000001@1",
                    "--edits",
                    "-",
                    "--json",
                ],
                input_bytes=self.edits_bytes,
            )
            self.assertEqual(file_input.stdout, stdin_input.stdout)
            self.assertEqual(0, file_input.returncode)

            missing_input = _process(
                [
                    "graph",
                    "transact",
                    "schuss-graph-000001@1",
                    "--edits",
                    str(Path(temporary) / "missing.json"),
                ]
            )
            self.assertEqual(2, missing_input.returncode)
            self.assertEqual(b"", missing_input.stdout)
            self.assertIn(b"CLI_EDITS_INPUT_INVALID", missing_input.stderr)

        for value in (b"{}", b"{", b"[1.25]"):
            with self.subTest(value=value):
                process = _process(
                    [
                        "graph",
                        "transact",
                        "schuss-graph-000001@1",
                        "--edits",
                        "-",
                    ],
                    input_bytes=value,
                )
                self.assertEqual(2, process.returncode)
                self.assertEqual(b"", process.stdout)
                self.assertIn(b"CLI_EDITS_", process.stderr)

        empty = _process(
            [
                "graph",
                "transact",
                "schuss-graph-000001@1",
                "--edits",
                "-",
                "--json",
            ],
            input_bytes=b"[]",
        )
        self.assertEqual(1, empty.returncode)
        self.assertEqual("invalid", json.loads(empty.stdout)["status"])

        invalid_edit = _process(
            [
                "graph",
                "transact",
                "schuss-graph-000001@1",
                "--edits",
                "-",
                "--json",
            ],
            input_bytes=b'[{"edit":"remove-node","node_id":"graph-node-000001"}]',
        )
        self.assertEqual(1, invalid_edit.returncode)
        self.assertEqual("invalid", json.loads(invalid_edit.stdout)["status"])
        self.assertEqual(graph_before, graph.read_bytes())

    def test_stdout_stderr_and_all_four_exit_classes(self):
        success = _process(["validate"])
        non_success = _process(
            ["build", "resolve", "schuss-build-request-000001@1"]
        )
        usage = _process(["graph", "inspect", "not-a-locator"])
        self.assertEqual((0, True, b""), (success.returncode, bool(success.stdout), success.stderr))
        self.assertEqual((1, True, b""), (non_success.returncode, bool(non_success.stdout), non_success.stderr))
        self.assertEqual(2, usage.returncode)
        self.assertEqual(b"", usage.stdout)
        self.assertTrue(usage.stderr)

        def internal_failure(**kwargs):
            raise RuntimeError("fixture internal failure")

        stdout = io.BytesIO()
        stderr = io.StringIO()
        code = run_cli(
            ["validate"], io.BytesIO(), stdout, stderr, internal_failure
        )
        self.assertEqual(3, code)
        self.assertEqual(b"", stdout.getvalue())
        self.assertIn("internal operation failure", stderr.getvalue())

    def test_broken_pipe_and_keyboard_interrupt_are_quiet_and_non_persistent(self):
        stderr = io.StringIO()
        code = run_cli(
            ["completion", "bash"],
            io.BytesIO(),
            _BrokenOutput(),
            stderr,
            lambda **kwargs: self.default_context,
        )
        self.assertEqual(1, code)
        self.assertEqual("", stderr.getvalue())

        def interrupted(**kwargs):
            raise KeyboardInterrupt()

        stdout = io.BytesIO()
        stderr = io.StringIO()
        graph = ROOT / "contracts/graphs/blend-crossfader-v0.json"
        before = graph.read_bytes()
        code = run_cli(["validate"], io.BytesIO(), stdout, stderr, interrupted)
        self.assertEqual(1, code)
        self.assertEqual(b"", stdout.getvalue())
        self.assertEqual("schuss: interrupted\n", stderr.getvalue())
        self.assertEqual(before, graph.read_bytes())

    def test_product_modules_do_not_import_domain_internals_or_task009_handler(self):
        forbidden = {
            "aggregate_validator",
            "component_graph_rules",
            "device_instrument_rules",
            "target_backend_build_rules",
            "task009_backend",
            "subprocess",
        }
        for relative in (
            "packages/schuss_core/cli.py",
            "packages/schuss_core/product_cli.py",
        ):
            tree = ast.parse((ROOT / relative).read_text(encoding="utf-8"))
            imports = {
                alias.name
                for node in ast.walk(tree)
                if isinstance(node, ast.Import)
                for alias in node.names
            }
            imports |= {
                node.module
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.module
            }
            self.assertFalse(forbidden & imports, relative)
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("run_task009", text)

    def test_all_task005_through_task009_inputs_and_outputs_are_preserved(self):
        raw_hashes = {
            ACCEPTED: "389b82834f41e4c8b1c2058cb7a9eccba348f7922f5de6abaeadb42bfd00e7a8",
            PREREQUISITE: "1ba2baf4affe2d0e1c08ec34f54659c89e4989d184df7421cd94c8bc72507553",
            SUCCESSOR: "0ca4ac25d76605c595ac56b68b4cd78b949467c057d9b97b56bdc96c3be6cf8a",
            OPERATION_FIXTURES: "cb21063005fdb18abd4362f3537b7286eb94db23d2c1d2963eac247616fac99a",
        }
        for path, digest in raw_hashes.items():
            self.assertEqual(digest, hashlib.sha256(path.read_bytes()).hexdigest())

        accepted = record_set_rules.load_record_set(ROOT, ACCEPTED)
        prerequisite = record_set_rules.load_record_set(ROOT, PREREQUISITE)
        successor = record_set_rules.load_record_set(ROOT, SUCCESSOR)
        self.assertEqual("schuss-record-set-000001", accepted.reference["record_set_id"])
        self.assertEqual("schuss-record-set-000002", prerequisite.reference["record_set_id"])
        self.assertEqual("schuss-record-set-000003", successor.reference["record_set_id"])

        immutable = {
            item["portable_path"]
            for item in successor.manifest["schema_members"]
            + successor.manifest["record_members"]
        }
        immutable |= {
            path.relative_to(ROOT).as_posix()
            for root in (
                ROOT / "evidence/task-009-prerequisite-v0",
                ROOT / "evidence/task-009-prerequisite-repair-v1",
                ROOT / "evidence/task-009-v1",
            )
            for path in root.rglob("*")
            if path.is_file()
        }
        immutable |= {
            ACCEPTED.relative_to(ROOT).as_posix(),
            PREREQUISITE.relative_to(ROOT).as_posix(),
            SUCCESSOR.relative_to(ROOT).as_posix(),
            OPERATION_FIXTURES.relative_to(ROOT).as_posix(),
        }
        comparison = subprocess.run(
            ["git", "diff", "--quiet", "HEAD", "--", *sorted(immutable)],
            cwd=ROOT,
            check=False,
        )
        self.assertEqual(0, comparison.returncode)

        operation_hashes = {
            "records_validate": "cb0735df54a0baade54c8cc16807a94771c1e7cbbc93a6710291084fcb656543",
            "graph_inspect": "88d5a4f52f4d3bfc31ff361ebe3a8835860e7b5890e9c9791be21cd86c179ee1",
            "build_resolve": "643a063d1553ff000a4776fd2a4eb5b7d300c0ba34ccbb977f3babd78abf7de9",
            "graph_transact_noop": "6def7986739604e807b3b95e26513fe6a9a41cd1d827ea4e417809b9027c48b8",
        }
        for name, digest in operation_hashes.items():
            result = canonical_result_bytes(
                dispatch_operation(copy.deepcopy(self.fixtures[name]), self.default_context),
                self.default_context,
            )
            self.assertEqual(digest, hashlib.sha256(result).hexdigest(), name)


if __name__ == "__main__":
    unittest.main()
