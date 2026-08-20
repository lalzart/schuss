#!/usr/bin/env python3
"""Run one explicit CMake/CTest or sanitizer boundary in a temporary build."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]


def _require_tools() -> None:
    missing = [name for name in ("cmake", "ctest") if shutil.which(name) is None]
    if missing:
        print("native prerequisite missing: " + ", ".join(missing), file=sys.stderr)
        raise SystemExit(3)


def _run(command: list[str], *, environment: dict[str, str] | None = None) -> None:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode:
        sys.stdout.write(completed.stdout)
        sys.stderr.write(completed.stderr)
        raise ValueError("native command failed: " + " ".join(command))


def _configure_build_test(
    source: Path,
    build: Path,
    *,
    cmake_arguments: tuple[str, ...] = (),
    test_environment: dict[str, str] | None = None,
) -> None:
    _run(
        [
            "cmake",
            "-S",
            str(source),
            "-B",
            str(build),
            "-DCMAKE_BUILD_TYPE=RelWithDebInfo",
            *cmake_arguments,
        ]
    )
    _run(["cmake", "--build", str(build), "--parallel"])
    _run(
        ["ctest", "--test-dir", str(build), "--output-on-failure"],
        environment=test_environment,
    )


def run(mode: str) -> None:
    _require_tools()
    with tempfile.TemporaryDirectory(prefix=f"schuss-native-{mode}-") as temporary:
        build = Path(temporary) / "build"
        if mode == "runtime":
            _configure_build_test(ROOT / "packages/schuss_rt", build)
            return
        if mode == "engine":
            _configure_build_test(
                ROOT / "apps/schuss_audio_engine",
                build,
                cmake_arguments=(
                    "-DSCHUSS_ENABLE_JUCE=OFF",
                    "-DSCHUSS_ENGINE_BUILD_TESTS=ON",
                ),
            )
            return
        if mode == "asan-ubsan":
            flags = "-fsanitize=address,undefined -fno-omit-frame-pointer"
            environment = os.environ.copy()
            environment.update(
                {
                    "ASAN_OPTIONS": "detect_leaks=0:halt_on_error=1",
                    "UBSAN_OPTIONS": "halt_on_error=1",
                }
            )
        else:
            flags = "-fsanitize=thread -fno-omit-frame-pointer"
            environment = os.environ.copy()
            environment["TSAN_OPTIONS"] = "halt_on_error=1"
        _configure_build_test(
            ROOT / "packages/schuss_rt",
            build,
            cmake_arguments=(
                f"-DCMAKE_CXX_FLAGS={flags}",
                f"-DCMAKE_EXE_LINKER_FLAGS={flags}",
            ),
            test_environment=environment,
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode", required=True, choices=("runtime", "engine", "asan-ubsan", "tsan")
    )
    arguments = parser.parse_args(argv)
    try:
        run(arguments.mode)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"native {arguments.mode} validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
