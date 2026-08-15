"""Minimal Task 008 machine-process adapter for the shared dispatcher."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import BinaryIO, Callable, TextIO

from .control_plane import (
    OperationContext,
    canonical_result_bytes,
    dispatch_operation,
    load_repository_context,
)


class _UsageError(ValueError):
    pass


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise _UsageError(message)


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(prog="schuss", description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    operation = subcommands.add_parser("op", help="dispatch one canonical operation")
    operation.add_argument("--request", required=True, metavar="FILE_OR_STDIN")
    operation.add_argument("--json", action="store_true", required=True)
    return parser


def run(
    argv: list[str],
    stdin: BinaryIO,
    stdout: BinaryIO,
    stderr: TextIO,
    context_loader: Callable[[], OperationContext] = load_repository_context,
) -> int:
    try:
        args = _parser().parse_args(argv)
    except _UsageError as exc:
        print(f"schuss: usage error: {exc}", file=stderr)
        return 2

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
    except (OSError, ValueError) as exc:
        print(f"schuss: request input failed: {exc}", file=stderr)
        return 2

    try:
        context = context_loader()
        result = dispatch_operation(request, context)
        stdout.write(canonical_result_bytes(result, context) + b"\n")
        return 0 if result["status"] == "success" else 1
    except Exception as exc:  # Process boundary: stable containment of adapter faults.
        print(f"schuss: internal operation failure: {exc}", file=stderr)
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
