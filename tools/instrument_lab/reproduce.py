#!/usr/bin/env python3
"""Two-fresh-root and relocated-root Instrument Lab smoke reproduction."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from common import ContractError  # noqa: E402


def tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(relative + b"\0" + path.read_bytes() + b"\0")
    return digest.hexdigest()


def run(command: list[str], cwd: Path) -> None:
    environment = dict(os.environ)
    environment.update({"LC_ALL": "C", "LANG": "C", "TZ": "UTC"})
    completed = subprocess.run(
        command, cwd=cwd, env=environment, check=False,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    if completed.returncode != 0:
        raise ContractError("REPRODUCTION_COMMAND_FAILED", " ".join(command) + "\n" + completed.stdout)


def generate_and_build(root: Path, source_root: Path) -> tuple[str, str]:
    output = root / "generated"
    tool = source_root / "tools/instrument_lab/new_prototype.py"
    lab = source_root / "research/prototype_support/instrument_lab"
    run([
        sys.executable, str(tool), "--spec", str(lab / "fixtures/smoke-spec.json"),
        "--template-root", str(lab / "templates"), "--output", str(output), "--write",
    ], source_root)
    generated_hash = tree_hash(output)
    build = root / "build"
    run([
        "cmake", "-S", str(output), "-B", str(build),
        f"-DSCHUSS_INSTRUMENT_LAB_ROOT={lab}", "-DCMAKE_BUILD_TYPE=Release",
    ], source_root)
    run(["cmake", "--build", str(build), "--parallel"], source_root)
    run(["ctest", "--test-dir", str(build), "--output-on-failure"], source_root)
    artifact = build / "instrument_lab_smoke_tests"
    return generated_hash, hashlib.sha256(artifact.read_bytes()).hexdigest()


def reproduce(repo_root: Path) -> tuple[str, str]:
    with tempfile.TemporaryDirectory(prefix="schuss-task037-reproduction-") as temporary:
        base = Path(temporary)
        first = generate_and_build(base / "first", repo_root)
        second = generate_and_build(base / "second", repo_root)
        if first != second:
            raise ContractError("FRESH_ROOT_DRIFT", f"{first} != {second}")

        relocated = base / "relocated/repository"
        shutil.copytree(repo_root / "research/prototype_support/instrument_lab", relocated / "research/prototype_support/instrument_lab")
        shutil.copytree(repo_root / "tools/instrument_lab", relocated / "tools/instrument_lab")
        third = generate_and_build(base / "third", relocated)
        if first != third:
            raise ContractError("RELOCATED_ROOT_DRIFT", f"{first} != {third}")
        return first


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--reproduce", action="store_true", required=True)
    args = parser.parse_args()
    try:
        generated, binary = reproduce(args.repo_root.resolve())
    except (ContractError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(f"fresh/relocated generated tree sha256: {generated}")
    print(f"fresh/relocated test artifact sha256: {binary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
