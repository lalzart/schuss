"""Deterministic Schuss product CLI over the shared Task 008 operations."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import BinaryIO, Callable, TextIO

from .control_plane import (
    OperationContext,
    canonical_result_bytes,
    dispatch_operation,
    load_repository_context,
)
from .product_cli import (
    ProductInputError,
    build_resolve_request,
    completion_script,
    graph_inspect_request,
    graph_transact_request,
    records_validate_request,
    render_human_result,
    resolve_locator,
)


DEFAULT_RECORD_SET_REFERENCE = {
    "record_set_id": "schuss-record-set-000001",
    "revision": 1,
    "content_hash": "sha256:f3fde23e7410a0a78c79ffdbcf3741995cedbf69f41c5a47e596ac39a2ac62f6",
}

PRODUCT_HELP_EPILOG = (
    "Default output is deterministic plain text over schuss-record-set-000001@1. "
    "--record-set selects one exact validated parent-preserving manifest; --json "
    "emits the canonical operation result. Exit 0 is success, 1 is a dispatched "
    "non-success, 2 is usage/input failure, and 3 is unexpected internal failure."
)


class _UsageError(ValueError):
    def __init__(self, message: str, help_text: str) -> None:
        super().__init__(message)
        self.help_text = help_text


class _HelpRequested(Exception):
    def __init__(self, help_text: str) -> None:
        super().__init__()
        self.help_text = help_text


class _FixedHelpFormatter(argparse.HelpFormatter):
    def __init__(self, prog: str) -> None:
        super().__init__(prog, indent_increment=2, max_help_position=28, width=80)


class _HelpAction(argparse.Action):
    def __init__(self, option_strings, dest=argparse.SUPPRESS, default=argparse.SUPPRESS, **kwargs):
        super().__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            **kwargs,
        )

    def __call__(self, parser, namespace, values, option_string=None) -> None:
        raise _HelpRequested(parser.format_help())


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise _UsageError(message, self.format_help())


def _new_parser(*args, **kwargs) -> _Parser:
    return _Parser(
        *args,
        add_help=False,
        allow_abbrev=False,
        formatter_class=_FixedHelpFormatter,
        **kwargs,
    )


def _add_help(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--help",
        action=_HelpAction,
        help="show this deterministic help page and exit",
    )


def _add_product_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--record-set",
        metavar="MANIFEST",
        help="select one exact validated record-set manifest",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit the canonical operation-result bytes",
    )
    _add_help(parser)


def _parser() -> argparse.ArgumentParser:
    parser = _new_parser(
        prog="schuss",
        description=(
            "Deterministic Schuss product CLI over the shared validation, "
            "inspection, resolution, and in-memory transaction operations."
        ),
        epilog=(
            "Default operation output is deterministic plain text over "
            "schuss-record-set-000001@1. --record-set selects one exact validated "
            "parent-preserving manifest; --json emits the canonical operation result. "
            "Exit 0: success/help/completion. Exit 1: dispatched non-success or "
            "interruption. Exit 2: usage/input/record-set failure. Exit 3: unexpected "
            "internal failure. Progress presentation is intentionally absent."
        ),
    )
    _add_help(parser)
    subcommands = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    validate = subcommands.add_parser(
        "validate",
        add_help=False,
        allow_abbrev=False,
        formatter_class=_FixedHelpFormatter,
        help="validate the selected exact record closure",
        description="Dispatch records.validate over one exact record set.",
        epilog=PRODUCT_HELP_EPILOG,
    )
    _add_product_options(validate)

    graph = subcommands.add_parser(
        "graph",
        add_help=False,
        allow_abbrev=False,
        formatter_class=_FixedHelpFormatter,
        help="inspect or transact on an exact graph revision",
        description="Graph commands use exact ID@revision locators.",
        epilog="Choose inspect or transact; each child command documents record-set, output, and exit behavior.",
    )
    _add_help(graph)
    graph_commands = graph.add_subparsers(
        dest="graph_command", required=True, metavar="COMMAND"
    )
    inspect = graph_commands.add_parser(
        "inspect",
        add_help=False,
        allow_abbrev=False,
        formatter_class=_FixedHelpFormatter,
        help="inspect one exact graph and contract closure",
        description="Dispatch graph.inspect without selecting an implementation.",
        epilog=PRODUCT_HELP_EPILOG,
    )
    inspect.add_argument("locator", metavar="GRAPH_ID@REVISION")
    _add_product_options(inspect)

    transact = graph_commands.add_parser(
        "transact",
        add_help=False,
        allow_abbrev=False,
        formatter_class=_FixedHelpFormatter,
        help="propose one atomic in-memory graph transaction",
        description=(
            "Dispatch graph.transact with the existing ordered edit-array language. "
            "Successful proposals are not written."
        ),
        epilog=PRODUCT_HELP_EPILOG,
    )
    transact.add_argument("locator", metavar="GRAPH_ID@REVISION")
    transact.add_argument(
        "--edits", required=True, metavar="FILE_OR_STDIN", help="read an edit array from a JSON file or -"
    )
    _add_product_options(transact)

    build = subcommands.add_parser(
        "build",
        add_help=False,
        allow_abbrev=False,
        formatter_class=_FixedHelpFormatter,
        help="resolve an exact build request without executing a backend",
        description=(
            "Build commands expose resolution only. A plain build does not compile, "
            "generate artifacts, or invoke the Task 009 handler."
        ),
        epilog="Choose resolve; its child help documents record-set, output, and exit behavior.",
    )
    _add_help(build)
    build_commands = build.add_subparsers(
        dest="build_command", required=True, metavar="COMMAND"
    )
    resolve = build_commands.add_parser(
        "resolve",
        add_help=False,
        allow_abbrev=False,
        formatter_class=_FixedHelpFormatter,
        help="resolve one exact build request",
        description="Dispatch build.resolve and stop before backend lowering.",
        epilog=PRODUCT_HELP_EPILOG,
    )
    resolve.add_argument("locator", metavar="REQUEST_ID@REVISION")
    _add_product_options(resolve)

    completion = subcommands.add_parser(
        "completion",
        add_help=False,
        allow_abbrev=False,
        formatter_class=_FixedHelpFormatter,
        help="emit a static completion script",
        description=(
            "Emit deterministic fixed-grammar completion without reading records or "
            "modifying a shell profile."
        ),
        epilog="Exit 0 emits one static script; usage failure exits 2. No domain operation is dispatched.",
    )
    completion.add_argument("shell", choices=("bash", "zsh", "fish"))
    _add_help(completion)

    operation = subcommands.add_parser(
        "op",
        add_help=False,
        allow_abbrev=False,
        formatter_class=_FixedHelpFormatter,
        help="dispatch one canonical machine operation",
        description=(
            "Task 008 canonical-JSON machine adapter. The original invocation remains "
            "byte-compatible; --record-set only selects an explicit validated context."
        ),
        epilog=(
            "Default context is schuss-record-set-000001@1. Exit 0 is operation success, "
            "1 is dispatched non-success, 2 is usage/input failure, and 3 is unexpected "
            "internal failure. Stdout is canonical JSON plus one LF."
        ),
    )
    operation.add_argument("--request", required=True, metavar="FILE_OR_STDIN")
    operation.add_argument("--record-set", metavar="MANIFEST")
    operation.add_argument("--json", action="store_true", required=True)
    _add_help(operation)
    return parser


def _emit_bytes(stream: BinaryIO, data: bytes) -> None:
    written = stream.write(data)
    if written is not None and written != len(data):
        raise BrokenPipeError("short output write")
    flush = getattr(stream, "flush", None)
    if flush is not None:
        flush()


def _write_stderr(stderr: TextIO, text: str) -> None:
    try:
        stderr.write(text)
        stderr.flush()
    except (BrokenPipeError, OSError):
        pass


def _silence_broken_stdout(stdout: BinaryIO) -> None:
    try:
        descriptor = stdout.fileno()
        replacement = os.open(os.devnull, os.O_WRONLY)
        try:
            os.dup2(replacement, descriptor)
        finally:
            os.close(replacement)
    except (AttributeError, OSError, ValueError):
        pass


def _context(
    manifest: str | None,
    context_loader: Callable[..., OperationContext],
) -> OperationContext:
    if manifest is None:
        return context_loader()
    manifest_path = Path(manifest).resolve()
    context = context_loader(record_set_path=manifest_path)
    _verify_product_record_set_chain(manifest_path, context.record_set_reference)
    return context


def _manifest_reference(value) -> dict[str, object]:
    return {
        key: value.get(key)
        for key in ("record_set_id", "revision", "content_hash")
    }


def _verify_product_record_set_chain(
    selected_path: Path, selected_reference: dict[str, object]
) -> None:
    """Require every explicit selection to descend from the frozen default."""

    from .control_plane import core

    path = selected_path
    expected = dict(selected_reference)
    visited: set[tuple[str, int, str]] = set()
    while True:
        manifest = core.load_json(path)
        reference = _manifest_reference(manifest)
        if reference != expected:
            raise ValueError("selected record-set context does not match its manifest")
        key = (
            str(reference["record_set_id"]),
            int(reference["revision"]),
            str(reference["content_hash"]),
        )
        if key in visited:
            raise ValueError("selected record-set parent chain contains a cycle")
        visited.add(key)
        parent = manifest["parent_reference"]
        if parent["status"] == "omitted":
            if manifest["purpose"] != "accepted-baseline":
                raise ValueError("record-set root is not an accepted baseline")
            if reference != DEFAULT_RECORD_SET_REFERENCE:
                raise ValueError(
                    "record-set parent chain does not end at the frozen accepted default"
                )
            return
        if manifest["purpose"] != "prospective-task":
            raise ValueError("non-root record set is not a prospective parent-preserving view")
        expected = {
            key: parent[key]
            for key in ("record_set_id", "revision", "content_hash")
        }
        candidates = []
        for candidate in sorted(path.parent.glob("*.json")):
            if candidate.resolve() == path.resolve():
                continue
            try:
                value = core.load_json(candidate)
            except (OSError, ValueError):
                continue
            if _manifest_reference(value) == expected:
                candidates.append(candidate.resolve())
        if len(candidates) != 1:
            raise ValueError("record-set parent does not resolve exactly once")
        path = candidates[0]


def _safe_adapter_message(message: str, manifest: str | None = None) -> str:
    replacements = [str(Path.cwd())]
    if manifest is not None:
        replacements.append(str(Path(manifest).resolve()))
    result = message
    for value in sorted(set(replacements), key=len, reverse=True):
        if value:
            result = result.replace(value, "<local-path>")
    return result


def _load_context_or_report(
    manifest: str | None,
    context_loader: Callable[..., OperationContext],
    stderr: TextIO,
) -> tuple[OperationContext | None, int | None]:
    try:
        return _context(manifest, context_loader), None
    except (OSError, ValueError) as exc:
        message = _safe_adapter_message(str(exc), manifest)
        _write_stderr(
            stderr,
            f"schuss: CLI_RECORD_SET_INVALID: {message}\n",
        )
        return None, 2


def _read_operation_request(args, stdin: BinaryIO, stderr: TextIO):
    try:
        data = stdin.read() if args.request == "-" else Path(args.request).read_bytes()
        from .control_plane import core

        request = core.load_json_bytes(
            data,
            "stdin" if args.request == "-" else args.request,
            require_final_lf=True,
        )
        if not isinstance(request, dict):
            raise ValueError("operation request must be a JSON object")
        return request, None
    except (OSError, ValueError) as exc:
        _write_stderr(stderr, f"schuss: request input failed: {exc}\n")
        return None, 2


def _read_edits(args, stdin: BinaryIO, stderr: TextIO):
    try:
        data = stdin.read() if args.edits == "-" else Path(args.edits).read_bytes()
        from .control_plane import core

        edits = core.load_json_bytes(data, "edits", require_final_lf=False)
        if not isinstance(edits, list):
            raise ProductInputError(
                "CLI_EDITS_NOT_ARRAY", "--edits input must be one JSON array"
            )
        return edits, None
    except ProductInputError as exc:
        _write_stderr(stderr, f"schuss: {exc.code}: {exc}\n")
        return None, 2
    except (OSError, ValueError) as exc:
        _write_stderr(
            stderr,
            "schuss: CLI_EDITS_INPUT_INVALID: "
            + _safe_adapter_message(str(exc))
            + "\n",
        )
        return None, 2


def _product_request(args, context: OperationContext, stdin: BinaryIO, stderr: TextIO):
    if args.command == "validate":
        return records_validate_request(), None
    if args.command == "graph" and args.graph_command == "inspect":
        reference = resolve_locator(
            args.locator, expected_kind="graph", context=context
        )
        return graph_inspect_request(reference), None
    if args.command == "graph" and args.graph_command == "transact":
        reference = resolve_locator(
            args.locator, expected_kind="graph", context=context
        )
        edits, exit_code = _read_edits(args, stdin, stderr)
        if exit_code is not None:
            return None, exit_code
        return graph_transact_request(reference, edits), None
    if args.command == "build" and args.build_command == "resolve":
        reference = resolve_locator(
            args.locator, expected_kind="build-request", context=context
        )
        return build_resolve_request(reference), None
    raise ValueError("parsed command has no product operation mapping")


def run(
    argv: list[str],
    stdin: BinaryIO,
    stdout: BinaryIO,
    stderr: TextIO,
    context_loader: Callable[..., OperationContext] = load_repository_context,
) -> int:
    try:
        try:
            args = _parser().parse_args(argv)
        except _HelpRequested as exc:
            _emit_bytes(stdout, exc.help_text.encode("utf-8"))
            return 0
        except _UsageError as exc:
            _write_stderr(stderr, f"schuss: usage error: {exc}\n{exc.help_text}")
            return 2

        if args.command == "completion":
            _emit_bytes(stdout, completion_script(args.shell))
            return 0

        if args.command == "op":
            request, exit_code = _read_operation_request(args, stdin, stderr)
            if exit_code is not None:
                return exit_code
            context, exit_code = _load_context_or_report(
                args.record_set, context_loader, stderr
            )
            if exit_code is not None:
                return exit_code
            result = dispatch_operation(request, context)
            _emit_bytes(stdout, canonical_result_bytes(result, context) + b"\n")
            return 0 if result["status"] == "success" else 1

        context, exit_code = _load_context_or_report(
            args.record_set, context_loader, stderr
        )
        if exit_code is not None:
            return exit_code
        try:
            request, exit_code = _product_request(args, context, stdin, stderr)
        except ProductInputError as exc:
            _write_stderr(stderr, f"schuss: {exc.code}: {exc}\n")
            return 2
        if exit_code is not None:
            return exit_code
        result = dispatch_operation(request, context)
        output = (
            canonical_result_bytes(result, context) + b"\n"
            if args.json
            else render_human_result(result, context, request)
        )
        _emit_bytes(stdout, output)
        return 0 if result["status"] == "success" else 1
    except BrokenPipeError:
        _silence_broken_stdout(stdout)
        return 1
    except KeyboardInterrupt:
        _write_stderr(stderr, "schuss: interrupted\n")
        return 1
    except Exception as exc:  # Stable containment of unexpected adapter faults.
        message = _safe_adapter_message(str(exc))
        _write_stderr(
            stderr,
            f"schuss: internal operation failure: {type(exc).__name__}: {message}\n",
        )
        return 3


def main(argv: list[str] | None = None) -> int:
    return run(
        list(sys.argv[1:] if argv is None else argv),
        sys.stdin.buffer,
        sys.stdout.buffer,
        sys.stderr,
    )


if __name__ == "__main__":
    raise SystemExit(main())
