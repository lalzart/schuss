#!/usr/bin/env python3
"""Fresh/relocated Instrument Lab smoke and consumer reproduction."""

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


def copy_relocated_repository(repo_root: Path, destination: Path) -> None:
    destination.mkdir(parents=True)
    for relative in RELOCATED_ROOTS:
        source = repo_root / relative
        if source.is_dir():
            shutil.copytree(
                source,
                destination / relative,
                ignore=shutil.ignore_patterns(
                    "__pycache__", "*.pyc", ".DS_Store", "node_modules"
                ),
            )
    for relative in ("AGENTS.md", "CMakeLists.txt"):
        source = repo_root / relative
        if source.is_file():
            shutil.copy2(source, destination / relative)


def reproduce_consumer(
    repo_root: Path,
    consumer_relative: Path,
    *,
    cmake_args: list[str],
    ctest_regex: str | None,
) -> str:
    if consumer_relative.is_absolute() or ".." in consumer_relative.parts:
        raise ContractError("INVALID_CONSUMER_PATH", consumer_relative.as_posix())
    source_consumer = repo_root / consumer_relative
    if not (source_consumer / "prototype-index.json").is_file():
        raise ContractError("MISSING_CONSUMER", consumer_relative.as_posix())
    expected_tree_hash = tree_hash(source_consumer)
    with tempfile.TemporaryDirectory(prefix="schuss-instrument-consumer-reproduction-") as temporary:
        relocated = Path(temporary) / "repository"
        copy_relocated_repository(repo_root, relocated)
        consumer = relocated / consumer_relative
        if tree_hash(consumer) != expected_tree_hash:
            raise ContractError("RELOCATED_CONSUMER_DRIFT", consumer_relative.as_posix())
        run([
            sys.executable,
            str(relocated / "tools/instrument_lab/validate_prototype.py"),
            "--repo-root", str(relocated),
            "--consumer-root", str(consumer),
            "--check",
        ], relocated)
        build = Path(temporary) / "build"
        run([
            "cmake", "-S", str(consumer), "-B", str(build),
            "-DCMAKE_BUILD_TYPE=Release", *cmake_args,
        ], relocated)
        run(["cmake", "--build", str(build), "--parallel"], relocated)
        ctest = ["ctest", "--test-dir", str(build), "--output-on-failure"]
        if ctest_regex is not None:
            ctest.extend(["-R", ctest_regex])
        run(ctest, relocated)
    return expected_tree_hash


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--consumer-root", type=Path)
    parser.add_argument("--cmake-arg", action="append", default=[])
    parser.add_argument("--ctest-regex")
    parser.add_argument("--reproduce", action="store_true", required=True)
    args = parser.parse_args()
    try:
        if args.consumer_root is not None:
            consumer_hash = reproduce_consumer(
                args.repo_root.resolve(),
                args.consumer_root,
                cmake_args=args.cmake_arg,
                ctest_regex=args.ctest_regex,
            )
            print(f"relocated consumer tree sha256: {consumer_hash}")
            return 0
        generated, binary = reproduce(args.repo_root.resolve())
    except (ContractError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(f"fresh/relocated generated tree sha256: {generated}")
    print(f"fresh/relocated test artifact sha256: {binary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
