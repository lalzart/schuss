#!/usr/bin/env python3
"""Explicit native Core/sanitizer matrix for Instrument Lab consumers."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run(command: list[str]) -> None:
    completed = subprocess.run(command, cwd=ROOT, check=False)
    if completed.returncode != 0:
        raise RuntimeError("command failed: " + " ".join(command))


def configure_build_test(
    source: Path,
    build: Path,
    extra: list[str],
    ctest_regex: str | None = None,
) -> None:
    run(["cmake", "-S", str(source), "-B", str(build), "-DCMAKE_BUILD_TYPE=Release", *extra])
    run(["cmake", "--build", str(build), "--parallel"])
    command = ["ctest", "--test-dir", str(build), "--output-on-failure"]
    if ctest_regex is not None:
        command.extend(["-R", ctest_regex])
    run(command)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode", choices=("core", "juce", "task038-core", "task038-juce"), required=True
    )
    parser.add_argument("--juce-source-dir", type=Path)
    args = parser.parse_args()
    if args.mode in {"juce", "task038-juce"} and args.juce_source_dir is None:
        print("MISSING_AUTHENTICATED_JUCE_PREREQUISITE", file=sys.stderr)
        return 2
    try:
        with tempfile.TemporaryDirectory(prefix="schuss-task037-native-") as temporary:
            base = Path(temporary)
            lab = ROOT / "research/prototype_support/instrument_lab"
            smoke = lab / "fixtures/smoke/generated"
            configure_build_test(lab, base / "lab", [])
            configure_build_test(smoke, base / "smoke", [f"-DSCHUSS_INSTRUMENT_LAB_ROOT={lab}"])
            if args.mode == "core":
                configure_build_test(ROOT / "research/prototypes/cinderwheel", base / "cinder", [])
                configure_build_test(
                    ROOT / "research/prototypes/tide-pit-gills", base / "tide-sanitize",
                    ["-DTIDE_PIT_ENABLE_SANITIZERS=ON"],
                )
            elif args.mode == "juce":
                juce = args.juce_source_dir.resolve()
                configure_build_test(smoke, base / "smoke-juce", [
                    f"-DSCHUSS_INSTRUMENT_LAB_ROOT={lab}",
                    "-DINSTRUMENT_LAB_SMOKE_ENABLE_JUCE=ON",
                    f"-DINSTRUMENT_LAB_SMOKE_JUCE_SOURCE_DIR={juce}",
                ])
                configure_build_test(ROOT / "research/prototypes/cinderwheel", base / "cinder-juce", [
                    "-DCINDERWHEEL_ENABLE_JUCE=ON", f"-DCINDERWHEEL_JUCE_SOURCE_DIR={juce}",
                ])
                configure_build_test(ROOT / "research/prototypes/tide-pit-gills", base / "tide-juce", [
                    "-DTIDE_PIT_ENABLE_JUCE=ON", f"-DTIDE_PIT_JUCE_SOURCE_DIR={juce}",
                ])
            elif args.mode == "task038-core":
                configure_build_test(
                    ROOT / "research/prototypes/generative-drum-machine",
                    base / "generative-drum-machine",
                    ["-DGDM_ENABLE_JUCE=OFF"],
                )
                configure_build_test(
                    ROOT / "research/prototypes/wirefall",
                    base / "wirefall",
                    [],
                    "^wirefall_(core_tests|contract_fixtures)$",
                )
            else:
                juce = args.juce_source_dir.resolve()
                configure_build_test(
                    ROOT / "research/prototypes/generative-drum-machine",
                    base / "generative-drum-machine-juce",
                    [
                        "-DGDM_ENABLE_JUCE=ON",
                        f"-DGDM_JUCE_SOURCE_DIR={juce}",
                    ],
                )
    except (OSError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(f"Instrument Lab native {args.mode} matrix passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
