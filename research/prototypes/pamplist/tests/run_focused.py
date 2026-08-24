#!/usr/bin/env python3
"""Build and run Pamplist's focused Release and sanitizer closures."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys


PROTOTYPE = Path(__file__).resolve().parents[1]
REPO_ROOT = PROTOTYPE.parents[2]
RELEASE_BUILD = REPO_ROOT / "build" / "pamplist-focused"
SANITIZER_BUILD = REPO_ROOT / "build" / "pamplist-sanitizers"
SOURCE_VERIFIER = PROTOTYPE / "tests" / "verify_source_authority.py"


def run(command: list[str], *, environment: dict[str, str] | None = None) -> None:
    print("+ " + " ".join(command), flush=True)
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=False,
        env=environment,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(command)}"
        )


def configure_and_test(build: Path, sanitizers: bool) -> None:
    run([
        "cmake", "-S", str(PROTOTYPE), "-B", str(build),
        "-DCMAKE_BUILD_TYPE=RelWithDebInfo" if sanitizers else "-DCMAKE_BUILD_TYPE=Release",
        f"-DPAMPLIST_ENABLE_SANITIZERS={'ON' if sanitizers else 'OFF'}",
        "-DPAMPLIST_ENABLE_JUCE=OFF",
    ])
    run(["cmake", "--build", str(build), "--parallel"])
    run(["ctest", "--test-dir", str(build), "--output-on-failure"])


def main() -> int:
    try:
        run([sys.executable, str(SOURCE_VERIFIER)])
        configure_and_test(RELEASE_BUILD, False)
        configure_and_test(SANITIZER_BUILD, True)
    except (OSError, RuntimeError) as error:
        print(f"Pamplist focused validation failed: {error}", file=sys.stderr)
        return 1
    print("Pamplist focused Release and sanitizer validation: passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
