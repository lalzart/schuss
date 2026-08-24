#!/usr/bin/env python3
"""Run one isolated relocated Pamplist Core and evidence reproduction."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
CONSUMER_RELATIVE = Path("research/prototypes/pamplist")
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


def main() -> int:
    source_verifier = ROOT / CONSUMER_RELATIVE / "tests/verify_source_authority.py"
    try:
        patcher_root = Path(
            run(
                [sys.executable, str(source_verifier), "--print-source-root"],
                ROOT,
                capture=True,
            )
        ).resolve()
        expected_tree = tree_hash(ROOT / CONSUMER_RELATIVE)
        with tempfile.TemporaryDirectory(prefix="pamplist-relocated-reproduction-") as temporary:
            temporary_root = Path(temporary)
            relocated = temporary_root / "repository"
            copy_relocated_repository(ROOT, relocated)
            relocated_catalog = relocated / "catalog"
            relocated_catalog.mkdir(parents=True)
            shutil.copy2(
                ROOT / "catalog/sources.lock.json",
                relocated_catalog / "sources.lock.json",
            )
            consumer = relocated / CONSUMER_RELATIVE
            if tree_hash(consumer) != expected_tree:
                raise RuntimeError("relocated Pamplist tree differs before validation")

            run(
                [
                    sys.executable,
                    str(relocated / "tools/instrument_lab/validate_prototype.py"),
                    "--repo-root",
                    str(relocated),
                    "--consumer-root",
                    str(consumer),
                    "--check",
                ],
                relocated,
            )
            run(
                [
                    sys.executable,
                    str(consumer / "tests/verify_source_authority.py"),
                    "--source-root",
                    str(patcher_root),
                ],
                relocated,
            )
            build = temporary_root / "build"
            run(
                [
                    "cmake",
                    "-S",
                    str(consumer),
                    "-B",
                    str(build),
                    "-DCMAKE_BUILD_TYPE=Release",
                    f"-DPAMPLIST_PATCHER_ROOT={patcher_root}",
                    "-DPAMPLIST_ENABLE_JUCE=OFF",
                ],
                relocated,
            )
            run(["cmake", "--build", str(build), "--parallel"], relocated)
            run(
                [
                    "ctest",
                    "--test-dir",
                    str(build),
                    "--output-on-failure",
                    "-R",
                    "^pamplist_",
                ],
                relocated,
            )
            run(
                [
                    sys.executable,
                    str(consumer / "tests/render_evidence.py"),
                    "--check",
                ],
                relocated,
            )
            if tree_hash(consumer) != expected_tree:
                raise RuntimeError("relocated validation mutated the Pamplist tree")
    except (OSError, RuntimeError) as error:
        print(f"Pamplist relocated reproduction failed: {error}", file=sys.stderr)
        return 1

    print(f"Pamplist relocated tree sha256: {expected_tree}")
    print("Pamplist relocated Core and retained-evidence reproduction passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
