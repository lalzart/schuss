"""Cheap exact checks for immutable, Git-anchored completion evidence."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess
from typing import Any

import validator_core as core


def _git(repository_root: Path, *arguments: str) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(repository_root), *arguments],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise ValueError(
            "retained evidence requires an authenticated Git anchor: "
            + completed.stderr.decode("utf-8", errors="replace").strip()
        )
    return completed.stdout


def _git_tracked_closure(
    evidence_root: Path, repository_root: Path, anchor_commit: str
) -> tuple[dict[str, str], str]:
    repository_absolute = Path(os.path.abspath(repository_root))
    expected_repository = repository_absolute.resolve()
    discovered_repository = Path(
        _git(expected_repository, "rev-parse", "--show-toplevel").decode().strip()
    ).resolve()
    if discovered_repository != expected_repository:
        raise ValueError("retained evidence Git repository is not the expected root")
    absolute_evidence = Path(os.path.abspath(evidence_root))
    try:
        relative_root = absolute_evidence.relative_to(repository_absolute)
    except ValueError as exc:
        raise ValueError("retained evidence root escapes its Git repository") from exc
    cursor = repository_absolute
    for component in relative_root.parts:
        cursor /= component
        if cursor.is_symlink():
            raise ValueError(
                f"retained evidence path contains a symlink: {component}"
            )
    resolved_evidence = absolute_evidence.resolve()
    try:
        resolved_evidence.relative_to(expected_repository)
    except ValueError as exc:
        raise ValueError("retained evidence root escapes its Git repository") from exc
    raw = _git(
        expected_repository,
        "ls-tree",
        "-rz",
        "--full-tree",
        anchor_commit,
        "--",
        relative_root.as_posix(),
    )
    expected: dict[str, str] = {}
    for entry in raw.split(b"\0"):
        if not entry:
            continue
        metadata, raw_path = entry.split(b"\t", 1)
        _mode, kind, object_id = metadata.decode("ascii").split()
        if kind != "blob":
            raise ValueError("retained evidence contains a non-blob Git object")
        relative = Path(raw_path.decode("utf-8")).relative_to(relative_root).as_posix()
        if relative in expected:
            raise ValueError(f"duplicate retained Git path: {relative}")
        expected[relative] = object_id
    if not expected:
        raise ValueError("retained evidence has no Git-anchored files")
    object_format = _git(
        expected_repository, "rev-parse", "--show-object-format"
    ).decode().strip()
    if object_format not in {"sha1", "sha256"}:
        raise ValueError(f"unsupported Git object format: {object_format}")
    return expected, object_format


def _git_blob_id(payload: bytes, object_format: str) -> str:
    digest = hashlib.new(object_format)
    digest.update(f"blob {len(payload)}\0".encode("ascii"))
    digest.update(payload)
    return digest.hexdigest()


def _check_exact_closure(
    evidence_root: Path, expected: dict[str, str], object_format: str
) -> None:
    actual: dict[str, Path] = {}
    for path in evidence_root.rglob("*"):
        relative = path.relative_to(evidence_root).as_posix()
        if path.is_symlink():
            raise ValueError(f"retained evidence contains a symlink: {relative}")
        if path.is_file():
            actual[relative] = path
    if set(actual) != set(expected):
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        raise ValueError(
            f"retained evidence closure differs; missing={missing}; extra={extra}"
        )
    for relative, path in actual.items():
        if _git_blob_id(path.read_bytes(), object_format) != expected[relative]:
            raise ValueError(
                f"retained evidence differs from its anchored commit: {relative}"
            )


def check_summary(
    evidence_root: Path,
    *,
    repository_root: Path,
    anchor_commit: str,
    schema_version: str,
) -> dict[str, Any]:
    check_closure(
        evidence_root,
        repository_root=repository_root,
        anchor_commit=anchor_commit,
    )

    summary_path = evidence_root / "validation-summary.json"
    summary = core.load_json(summary_path)
    expected_bytes = core.canonical_json(summary).encode("utf-8") + b"\n"
    if summary_path.read_bytes() != expected_bytes:
        raise ValueError("retained validation summary is not canonical")
    if summary.get("schema_version") != schema_version:
        raise ValueError("retained validation summary schema is stale")
    if summary.get("status") != "valid":
        raise ValueError("retained validation summary is not valid")

    descriptors = summary.get("artifacts", [])
    if not isinstance(descriptors, list):
        raise ValueError("retained artifact descriptors are invalid")
    locators: set[str] = set()
    for descriptor in descriptors:
        if not isinstance(descriptor, dict):
            raise ValueError("retained artifact descriptor is invalid")
        locator = descriptor.get("portable_locator", "")
        if not isinstance(locator, str):
            raise ValueError("retained artifact locator is invalid")
        portable = Path(locator)
        if (
            not locator
            or portable.is_absolute()
            or ".." in portable.parts
            or locator in locators
        ):
            raise ValueError(f"retained artifact locator is invalid: {locator}")
        locators.add(locator)
        path = (evidence_root / "artifacts" / portable).resolve()
        try:
            path.relative_to((evidence_root / "artifacts").resolve())
        except ValueError as exc:
            raise ValueError(f"retained artifact locator escapes: {locator}") from exc
        if not path.is_file():
            raise ValueError(f"retained artifact is missing: {locator}")
        payload = path.read_bytes()
        if len(payload) != descriptor.get("byte_length"):
            raise ValueError(f"retained artifact length is stale: {locator}")
        if hashlib.sha256(payload).hexdigest() != descriptor.get("byte_sha256"):
            raise ValueError(f"retained artifact hash is stale: {locator}")

    for child in ("artifacts/sha256", "device-artifacts/sha256"):
        directory = evidence_root / child
        if directory.is_dir():
            for path in sorted(directory.iterdir()):
                if path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() != path.name:
                    raise ValueError(f"content-addressed retained artifact is stale: {path.name}")
    return summary


def check_closure(
    evidence_root: Path,
    *,
    repository_root: Path,
    anchor_commit: str,
) -> int:
    """Authenticate one exact evidence directory against an immutable commit."""

    expected, object_format = _git_tracked_closure(
        evidence_root, repository_root, anchor_commit
    )
    _check_exact_closure(evidence_root, expected, object_format)
    return len(expected)


def check_files(
    portable_paths: tuple[Path, ...],
    *,
    repository_root: Path,
    anchor_commit: str,
) -> int:
    """Authenticate exact tracked files against an immutable commit."""

    repository_absolute = Path(os.path.abspath(repository_root))
    expected_repository = repository_absolute.resolve()
    discovered_repository = Path(
        _git(expected_repository, "rev-parse", "--show-toplevel").decode().strip()
    ).resolve()
    if discovered_repository != expected_repository:
        raise ValueError("retained files Git repository is not the expected root")
    requested: dict[str, Path] = {}
    for raw_path in portable_paths:
        portable = Path(raw_path)
        relative = portable.as_posix()
        if (
            not relative
            or portable.is_absolute()
            or ".." in portable.parts
            or relative in requested
        ):
            raise ValueError(f"retained file path is invalid: {relative}")
        cursor = repository_absolute
        for component in portable.parts:
            cursor /= component
            if cursor.is_symlink():
                raise ValueError(
                    f"retained file path contains a symlink: {relative}"
                )
        resolved = cursor.resolve()
        try:
            resolved.relative_to(expected_repository)
        except ValueError as exc:
            raise ValueError(f"retained file path escapes: {relative}") from exc
        if not cursor.is_file():
            raise ValueError(f"retained file is missing: {relative}")
        requested[relative] = cursor
    if not requested:
        raise ValueError("no retained files were requested")
    raw = _git(
        expected_repository,
        "ls-tree",
        "-rz",
        "--full-tree",
        anchor_commit,
        "--",
        *sorted(requested),
    )
    anchored: dict[str, str] = {}
    for entry in raw.split(b"\0"):
        if not entry:
            continue
        metadata, raw_path = entry.split(b"\t", 1)
        _mode, kind, object_id = metadata.decode("ascii").split()
        relative = raw_path.decode("utf-8")
        if kind != "blob" or relative in anchored:
            raise ValueError("retained file Git closure is invalid")
        anchored[relative] = object_id
    if set(anchored) != set(requested):
        raise ValueError("retained files differ from their anchored file set")
    object_format = _git(
        expected_repository, "rev-parse", "--show-object-format"
    ).decode().strip()
    if object_format not in {"sha1", "sha256"}:
        raise ValueError(f"unsupported Git object format: {object_format}")
    for relative, path in requested.items():
        if _git_blob_id(path.read_bytes(), object_format) != anchored[relative]:
            raise ValueError(
                f"retained file differs from its anchored commit: {relative}"
            )
    return len(requested)
