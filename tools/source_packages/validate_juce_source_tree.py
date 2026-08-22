#!/usr/bin/env python3
"""Bind a JUCE extracted tree to the accepted Task 033 source release."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.contracts import validator_core as core  # noqa: E402


SOURCE_RELEASE_PATH = Path("contracts/task033/phase2/source-release-07.json")
MANIFEST_PATH = Path("research/prototype_support/instrument_lab/juce-8.0.15-source-tree.json")
EXPECTED_AUTHORITY = {
    "content_hash": "sha256:fe43e61c91a48b2e29dd24ad08118f21c656eae2b765cae1a5c96682121b4652",
    "path": SOURCE_RELEASE_PATH.as_posix(),
    "revision": 1,
    "source_release_id": "schuss-source-release-000007",
}
ALGORITHM = (
    "SHA-256 lines with digest, two spaces, extracted-tree-relative path, LF; "
    "Unicode code-point path sort; SHA-256 of complete line bytes"
)


def canonical_bytes(document: object) -> bytes:
    return (json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode()


def source_authority(repo_root: Path) -> dict[str, Any]:
    path = repo_root / SOURCE_RELEASE_PATH
    record = core.load_json(path)
    schema = core.load_json(repo_root / "schemas/source-release-v0.schema.json")
    errors = core.schema_errors(record, schema, schema)
    if errors:
        raise ValueError("invalid JUCE source release: " + "; ".join(errors))
    if core.record_content_hash(record, schema) != record.get("content_hash"):
        raise ValueError("JUCE source-release content hash is invalid")
    actual = {
        "content_hash": record.get("content_hash"),
        "path": SOURCE_RELEASE_PATH.as_posix(),
        "revision": record.get("revision"),
        "source_release_id": record.get("source_release_id"),
    }
    if actual != EXPECTED_AUTHORITY:
        raise ValueError("JUCE source-release authority drifted")
    return record


def tree_fingerprint(source_tree: Path) -> tuple[int, str]:
    if not source_tree.is_dir():
        raise ValueError(f"JUCE source tree is not a directory: {source_tree}")
    paths: list[Path] = []
    for path in source_tree.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"JUCE source tree contains a symlink: {path}")
        if path.is_file():
            paths.append(path)
        elif not path.is_dir():
            raise ValueError(f"JUCE source tree contains a special file: {path}")
    lines = []
    for path in sorted(paths, key=lambda item: item.relative_to(source_tree).as_posix()):
        relative = path.relative_to(source_tree).as_posix()
        lines.append(f"{core.sha256_file(path)}  {relative}\n")
    digest = hashlib.sha256("".join(lines).encode("utf-8")).hexdigest()
    return len(paths), digest


def generated_manifest(repo_root: Path, source_tree: Path, archive: Path | None) -> dict[str, Any]:
    authority = source_authority(repo_root)
    identity = authority["release_identity"]
    if archive is not None:
        if not archive.is_file():
            raise ValueError(f"JUCE archive is missing: {archive}")
        if core.sha256_file(archive) != identity["archive_sha256"]:
            raise ValueError("JUCE retained archive hash does not match source-release authority")
    count, digest = tree_fingerprint(source_tree)
    return {
        "authority": EXPECTED_AUTHORITY,
        "claims": {
            "catalog_membership": False,
            "distribution_approval": False,
            "implementation_identity": False,
            "provider_identity": False,
            "source_release_identity": False,
        },
        "schema_version": "authenticated-extracted-source-tree-v1",
        "tree": {
            "file_count": count,
            "manifest_algorithm": ALGORITHM,
            "manifest_sha256": digest,
        },
    }


def check_tree(repo_root: Path, source_tree: Path) -> dict[str, Any]:
    source_authority(repo_root)
    manifest_path = repo_root / MANIFEST_PATH
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_keys = {"authority", "claims", "schema_version", "tree"}
    if set(manifest) != expected_keys:
        raise ValueError("JUCE tree manifest fields drifted")
    if manifest["schema_version"] != "authenticated-extracted-source-tree-v1":
        raise ValueError("JUCE tree manifest schema version drifted")
    if manifest["authority"] != EXPECTED_AUTHORITY:
        raise ValueError("JUCE tree manifest authority drifted")
    if manifest["claims"] != {
        "catalog_membership": False,
        "distribution_approval": False,
        "implementation_identity": False,
        "provider_identity": False,
        "source_release_identity": False,
    }:
        raise ValueError("JUCE tree manifest claims drifted")
    count, digest = tree_fingerprint(source_tree)
    tree = manifest["tree"]
    if set(tree) != {"file_count", "manifest_algorithm", "manifest_sha256"}:
        raise ValueError("JUCE tree fingerprint fields drifted")
    if tree["manifest_algorithm"] != ALGORITHM:
        raise ValueError("JUCE tree fingerprint algorithm drifted")
    if tree["file_count"] != count or tree["manifest_sha256"] != digest:
        raise ValueError(
            "JUCE source tree fingerprint mismatch: "
            f"expected {tree['file_count']} files/{tree['manifest_sha256']}, "
            f"got {count} files/{digest}"
        )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--source-tree", type=Path)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--write-manifest", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--print-field",
        choices=("archive_url", "archive_sha256", "commit", "tag"),
    )
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    try:
        authority = source_authority(repo_root)
        if args.print_field:
            print(authority["release_identity"][args.print_field])
            return 0
        if args.source_tree is None:
            raise ValueError("--source-tree is required")
        if args.write_manifest == args.check:
            raise ValueError("select exactly one of --write-manifest or --check")
        if args.write_manifest:
            manifest = generated_manifest(repo_root, args.source_tree.resolve(), args.archive)
            destination = repo_root / MANIFEST_PATH
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(canonical_bytes(manifest))
            print(
                "JUCE extracted tree manifest: wrote "
                f"{manifest['tree']['file_count']} files/{manifest['tree']['manifest_sha256']}"
            )
        else:
            manifest = check_tree(repo_root, args.source_tree.resolve())
            print(
                "JUCE extracted tree: authenticated "
                f"{manifest['tree']['file_count']} files/{manifest['tree']['manifest_sha256']}"
            )
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"JUCE source authentication failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
