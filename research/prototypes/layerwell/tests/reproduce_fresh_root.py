#!/usr/bin/env python3
"""Run one isolated relocated Layerwell reproduction with configured source."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
RELOCATED_ROOTS = (
    "contracts",
    "docs",
    "packages",
    "research",
    "schemas",
    "tools",
)


def tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(relative + b"\0" + path.read_bytes() + b"\0")
    return digest.hexdigest()


def run(command: list[str], cwd: Path) -> None:
    print("+", " ".join(command), flush=True)
    environment = dict(os.environ)
    environment.update({"LC_ALL": "C", "LANG": "C", "TZ": "UTC"})
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(command)}\n"
            + completed.stdout
        )


def pamplist_source_root() -> Path:
    completed = subprocess.run(
        [
            sys.executable,
            "research/prototypes/pamplist/tests/verify_source_authority.py",
            "--print-source-root",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "Pamplist source root unavailable")
    return Path(completed.stdout.strip()).resolve()


def copy_repository(destination: Path) -> None:
    destination.mkdir(parents=True)
    for relative in RELOCATED_ROOTS:
        shutil.copytree(
            ROOT / relative,
            destination / relative,
            ignore=shutil.ignore_patterns(
                "__pycache__", "*.pyc", ".DS_Store", "node_modules"
            ),
        )
    for relative in ("AGENTS.md", "CMakeLists.txt"):
        source = ROOT / relative
        if source.is_file():
            shutil.copy2(source, destination / relative)
    (destination / "catalog").mkdir()
    shutil.copy2(
        ROOT / "catalog/sources.lock.json",
        destination / "catalog/sources.lock.json",
    )


def main() -> int:
    try:
        configured_source = pamplist_source_root()
        source_consumer = ROOT / "research/prototypes/layerwell"
        expected_hash = tree_hash(source_consumer)
        with tempfile.TemporaryDirectory(
            prefix="schuss-layerwell-r02-reproduction-"
        ) as temporary:
            relocated = Path(temporary) / "repository"
            copy_repository(relocated)
            consumer = relocated / "research/prototypes/layerwell"
            if tree_hash(consumer) != expected_hash:
                raise RuntimeError("relocated Layerwell consumer tree drifted")
            run(
                [
                    sys.executable,
                    str(relocated / "tools/instrument_lab/validate_prototype.py"),
                    "--repo-root", str(relocated),
                    "--consumer-root", str(consumer),
                    "--check",
                ],
                relocated,
            )
            build = Path(temporary) / "build"
            run(
                [
                    "cmake", "-S", str(consumer), "-B", str(build),
                    "-DCMAKE_BUILD_TYPE=Release",
                    "-DLAYERWELL_ENABLE_JUCE=OFF",
                    f"-DPAMPLIST_PATCHER_ROOT={configured_source}",
                ],
                relocated,
            )
            run(["cmake", "--build", str(build), "--parallel"], relocated)
            run(
                [
                    "ctest", "--test-dir", str(build), "--output-on-failure",
                    "-R", "^layerwell_",
                ],
                relocated,
            )
    except (OSError, RuntimeError) as exc:
        print(f"Layerwell relocated reproduction failed: {exc}", file=sys.stderr)
        return 1
    print(f"Layerwell relocated Core reproduction passed: {expected_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
