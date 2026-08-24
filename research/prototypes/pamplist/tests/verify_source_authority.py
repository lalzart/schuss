#!/usr/bin/env python3
"""Fail-closed authentication for Pamplist's configured Macro Voice source."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


PROTOTYPE = Path(__file__).resolve().parents[1]
REPO_ROOT = PROTOTYPE.parents[2]
DEPENDENCIES = PROTOTYPE / "source-dependencies.json"
LOCAL_SOURCES = REPO_ROOT / "catalog" / "sources.local.yml"


class AuthorityError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise AuthorityError(f"git {' '.join(arguments)} failed: {detail}")
    return completed.stdout.strip()


def configured_patcher_root() -> Path:
    if not LOCAL_SOURCES.is_file():
        raise AuthorityError("MISSING_CONFIGURED_SOURCE_PREREQUISITE: catalog/sources.local.yml")
    for raw_line in LOCAL_SOURCES.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("patcher:"):
            value = stripped.split(":", 1)[1].strip()
            if not value:
                break
            return Path(value).expanduser().resolve()
    raise AuthorityError("MISSING_CONFIGURED_SOURCE_PREREQUISITE: patcher source mapping")


def verify(source_root: Path) -> dict[str, object]:
    document = json.loads(DEPENDENCIES.read_text(encoding="utf-8"))
    authority = document["authenticated_configured_sources"][0]
    expected_revision = authority["revision"]
    lock_document = json.loads((REPO_ROOT / authority["lock_path"]).read_text(encoding="utf-8"))
    lock_entries = [entry for entry in lock_document["sources"] if entry["id"] == authority["source_id"]]
    if len(lock_entries) != 1 or lock_entries[0]["commit"] != expected_revision:
        raise AuthorityError("patcher lock identity or revision does not match Pamplist authority")
    if not source_root.is_dir():
        raise AuthorityError(f"configured patcher source is not a directory: {source_root}")
    actual_revision = run_git(source_root, "rev-parse", "HEAD")
    if actual_revision != expected_revision:
        raise AuthorityError(
            f"patcher revision drift: expected {expected_revision}, observed {actual_revision}"
        )

    subtree = authority["subtree"]
    actual_tree = run_git(source_root, "rev-parse", f"HEAD:{subtree['path']}")
    if actual_tree != subtree["git_tree"]:
        raise AuthorityError(
            f"synthesis tree drift: expected {subtree['git_tree']}, observed {actual_tree}"
        )
    dirty = run_git(
        source_root,
        "status",
        "--short",
        "--untracked-files=all",
        "--",
        subtree["path"],
    )
    if dirty:
        raise AuthorityError(f"configured synthesis subtree is dirty:\n{dirty}")

    observed_files: list[dict[str, str]] = []
    for entry in authority["files"]:
        candidate = source_root / entry["path"]
        if not candidate.is_file():
            raise AuthorityError(f"required source file missing: {entry['path']}")
        actual_hash = sha256(candidate)
        if actual_hash != entry["sha256"]:
            raise AuthorityError(
                f"source file drift: {entry['path']} expected {entry['sha256']} observed {actual_hash}"
            )
        observed_files.append({"path": entry["path"], "sha256": actual_hash})

    for field in ("controller_authority",):
        entry = document[field]
        candidate = REPO_ROOT / entry["path"]
        if sha256(candidate) != entry["sha256"]:
            raise AuthorityError(f"repository authority drift: {entry['path']}")
    juce_manifest = document["authenticated_extracted_sources"][0]["manifest"]
    if sha256(REPO_ROOT / juce_manifest["path"]) != juce_manifest["sha256"]:
        raise AuthorityError(f"repository authority drift: {juce_manifest['path']}")

    return {
        "revision": actual_revision,
        "source_id": authority["source_id"],
        "subtree_git_tree": actual_tree,
        "subtree_path": subtree["path"],
        "files": observed_files,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--source-root", type=Path)
    result.add_argument("--print-source-root", action="store_true")
    result.add_argument("--json", action="store_true")
    return result


def main() -> int:
    arguments = parser().parse_args()
    try:
        source_root = (arguments.source_root or configured_patcher_root()).expanduser().resolve()
        if arguments.print_source_root:
            print(source_root)
            return 0
        receipt = verify(source_root)
    except (AuthorityError, OSError, KeyError, json.JSONDecodeError) as error:
        print(f"source authority failed: {error}", file=sys.stderr)
        return 1
    if arguments.json:
        print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    else:
        print(
            "Pamplist source authority: valid "
            f"({receipt['source_id']}@{receipt['revision']}, tree {receipt['subtree_git_tree']})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
