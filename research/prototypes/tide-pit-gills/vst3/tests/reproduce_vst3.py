#!/usr/bin/env python3
"""Build and host-test Tide Pit VST3 once from an isolated relocated root."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[5]
CONSUMER_RELATIVE = Path("research/prototypes/tide-pit-gills")
VST3_RELATIVE = CONSUMER_RELATIVE / "vst3"
SUPPORT_RELATIVE = Path("research/prototype_support/instrument_lab")
INSTRUMENT_LAB_TOOLS = ROOT / "tools/instrument_lab"
if str(INSTRUMENT_LAB_TOOLS) not in sys.path:
    sys.path.insert(0, str(INSTRUMENT_LAB_TOOLS))

from reproduce import copy_relocated_repository, tree_hash  # noqa: E402


def environment() -> dict[str, str]:
    result = dict(os.environ)
    result.update(
        {
            "LANG": "C",
            "LC_ALL": "C",
            "PYTHONDONTWRITEBYTECODE": "1",
            "TZ": "UTC",
        }
    )
    return result


def run(command: list[str], cwd: Path, *, capture: bool = False) -> str:
    print("+", " ".join(command), flush=True)
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=environment(),
        check=False,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
    )
    if completed.returncode != 0:
        if capture and completed.stdout:
            print(completed.stdout, file=sys.stderr, end="")
        raise RuntimeError(
            f"command failed with exit {completed.returncode}: {' '.join(command)}"
        )
    return (completed.stdout or "").strip()


def source_validation_command(
    validator: Path, gills_source: Path | None
) -> list[str]:
    command = [sys.executable, str(validator)]
    if gills_source is not None:
        command.extend(["--source-root", str(gills_source)])
    return command


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-type", choices=("Debug", "Release"), default="Release")
    parser.add_argument("--architecture", choices=("arm64",), default="arm64")
    parser.add_argument("--juce-source", type=Path, required=True)
    parser.add_argument("--gills-source", type=Path)
    arguments = parser.parse_args()
    juce_source = arguments.juce_source.resolve()
    gills_source = (
        arguments.gills_source.resolve() if arguments.gills_source else None
    )
    source_validator = ROOT / CONSUMER_RELATIVE / "tests/validate_source_lock.py"

    try:
        if not juce_source.is_dir():
            raise RuntimeError(f"JUCE source tree is missing: {juce_source}")
        if gills_source is not None and not gills_source.is_dir():
            raise RuntimeError(f"Gills source tree is missing: {gills_source}")
        run(
            [
                sys.executable,
                str(ROOT / "tools/source_packages/validate_juce_source_tree.py"),
                "--repo-root",
                str(ROOT),
                "--source-tree",
                str(juce_source),
                "--check",
            ],
            ROOT,
        )
        run(source_validation_command(source_validator, gills_source), ROOT)
        expected_tree = tree_hash(ROOT / CONSUMER_RELATIVE)
        expected_support_tree = tree_hash(ROOT / SUPPORT_RELATIVE)

        with tempfile.TemporaryDirectory(
            prefix="tide-pit-vst3-relocated-reproduction-"
        ) as temporary:
            temporary_root = Path(temporary)
            relocated = temporary_root / "repository"
            copy_relocated_repository(ROOT, relocated)
            consumer = relocated / CONSUMER_RELATIVE
            if tree_hash(consumer) != expected_tree:
                raise RuntimeError("relocated Tide Pit tree differs before build")
            if tree_hash(relocated / SUPPORT_RELATIVE) != expected_support_tree:
                raise RuntimeError(
                    "relocated Instrument Lab support tree differs before build"
                )

            relocated_validator = consumer / "tests/validate_source_lock.py"
            run(
                source_validation_command(relocated_validator, gills_source),
                relocated,
            )
            build = temporary_root / "build"
            run(
                [
                    "cmake",
                    "-S",
                    str(relocated / VST3_RELATIVE),
                    "-B",
                    str(build),
                    f"-DCMAKE_BUILD_TYPE={arguments.build_type}",
                    f"-DCMAKE_OSX_ARCHITECTURES={arguments.architecture}",
                    f"-DTIDE_PIT_JUCE_SOURCE_DIR={juce_source}",
                    "-DTIDE_PIT_ALLOW_JUCE_FETCH=OFF",
                ],
                relocated,
            )
            run(
                [
                    "cmake",
                    "--build",
                    str(build),
                    "--config",
                    arguments.build_type,
                    "--target",
                    "tide-pit-vst3-model-tests",
                    "tide-pit-vst3-processor-tests",
                    "tide-pit-vst3-allocation-tests",
                    "tide-pit-vst3-module-tests",
                    "--parallel",
                ],
                relocated,
            )
            run(
                [
                    "ctest",
                    "--test-dir",
                    str(build),
                    "-C",
                    arguments.build_type,
                    "--output-on-failure",
                    "-R",
                    "^tide_pit_vst3_",
                ],
                relocated,
            )
            bundle = (
                build
                / f"tide-pit-vst3_artefacts/{arguments.build_type}/VST3/Tide Pit.vst3"
            )
            binary = bundle / "Contents/MacOS/Tide Pit"
            run(
                ["/usr/bin/codesign", "--verify", "--deep", "--strict", str(bundle)],
                relocated,
            )
            slices = run(["/usr/bin/lipo", "-archs", str(binary)], relocated, capture=True)
            if slices != arguments.architecture:
                raise RuntimeError(
                    f"relocated VST3 architecture drift: expected "
                    f"{arguments.architecture}, observed {slices}"
                )
            if tree_hash(consumer) != expected_tree:
                raise RuntimeError("relocated build mutated the Tide Pit source tree")
            if tree_hash(relocated / SUPPORT_RELATIVE) != expected_support_tree:
                raise RuntimeError(
                    "relocated build mutated the Instrument Lab support tree"
                )

        run(source_validation_command(source_validator, gills_source), ROOT)
        run(
            [
                sys.executable,
                str(ROOT / "tools/source_packages/validate_juce_source_tree.py"),
                "--repo-root",
                str(ROOT),
                "--source-tree",
                str(juce_source),
                "--check",
            ],
            ROOT,
        )
    except (OSError, RuntimeError) as error:
        print(f"Tide Pit VST3 reproduction failed: {error}", file=sys.stderr)
        return 1

    print(f"Tide Pit relocated source tree sha256: {expected_tree}")
    print(f"Instrument Lab relocated support tree sha256: {expected_support_tree}")
    print(
        "Tide Pit relocated Release VST3 build, local seal, scan, instantiate, "
        "state, editor, allocation, and offline signal tests passed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
