"""Safe reproduction of retained evidence from an immutable Git commit."""

from __future__ import annotations

import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from typing import Any


COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")


def reproduce_summary(
    *,
    repository_root: Path,
    completion_commit: str,
    runner_path: Path,
    retained_summary: dict[str, Any],
    report_schema_version: str,
    source_configuration: Path | None = None,
    runner_arguments: tuple[str, ...] = ("--check",),
    timeout: int = 600,
) -> dict[str, Any]:
    """Run one archived evidence runner read-only and match its anchored summary."""

    runner_path = Path(runner_path)
    if (
        not COMMIT_PATTERN.fullmatch(completion_commit)
        or runner_path.is_absolute()
        or ".." in runner_path.parts
        or not runner_path.parts
    ):
        raise ValueError("historical reproduction identity is invalid")
    archived = subprocess.run(
        [
            "git",
            "-C",
            str(repository_root),
            "archive",
            "--format=tar",
            completion_commit,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if archived.returncode:
        raise ValueError(
            "historical completion commit is unavailable: "
            + archived.stderr.decode("utf-8", errors="replace").strip()
        )
    archive_bytes = archived.stdout
    del archived

    try:
        with tempfile.TemporaryDirectory(
            prefix="schuss-historical-reproduction-"
        ) as raw:
            historical_root = Path(raw) / "repository"
            historical_root.mkdir()
            with tarfile.open(
                fileobj=io.BytesIO(archive_bytes), mode="r:"
            ) as archive:
                members = archive.getmembers()
                for member in members:
                    path = Path(member.name)
                    if (
                        path.is_absolute()
                        or ".." in path.parts
                        or member.issym()
                        or member.islnk()
                        or not (member.isfile() or member.isdir())
                    ):
                        raise ValueError(
                            "historical Git archive contains an unsafe member"
                        )
                archive.extractall(historical_root, members=members)
            del archive_bytes
            if source_configuration is not None:
                source_configuration = Path(source_configuration).resolve()
                if not source_configuration.is_file():
                    raise ValueError(
                        "historical reproduction source configuration is unavailable"
                    )
                target = historical_root / "catalog/sources.local.yml"
                if target.exists() or target.is_symlink():
                    raise ValueError(
                        "historical archive unexpectedly contains local source configuration"
                    )
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_configuration, target)
            if not (historical_root / runner_path).is_file():
                raise ValueError("historical evidence runner is absent")
            completed = subprocess.run(
                [sys.executable, runner_path.as_posix(), *runner_arguments],
                cwd=historical_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=timeout,
            )
    except (subprocess.SubprocessError, tarfile.TarError) as exc:
        raise ValueError("historical evidence reproduction could not run") from exc
    if completed.returncode:
        raise ValueError(
            "historical evidence reproduction failed: "
            + completed.stderr.decode("utf-8", errors="replace").strip()
        )
    try:
        historical_summary = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "historical evidence reproduction returned invalid JSON"
        ) from exc
    if historical_summary != retained_summary:
        raise ValueError(
            "historical summary differs from retained anchored bytes"
        )
    return {
        "schema_version": report_schema_version,
        "status": "passed",
        "historical_commit": completion_commit,
        "retained_bytes_matched": True,
        "validation_summary": historical_summary,
    }
