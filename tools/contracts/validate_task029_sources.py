#!/usr/bin/env python3
"""Verify Task 029 pinned source blobs from explicitly selected local checkouts."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/contracts"))

import validator_core as core  # noqa: E402


REVIEW_PATHS = (
    ROOT / "contracts/task029/palimpsest-source-review-r1.json",
    ROOT / "contracts/task029/tide-pit-source-review-r1.json",
)
PANEL_PATH = ROOT / "contracts/task029/gills-panel-layout-r1.json"


def _git(root: Path, *arguments: str) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(root), *arguments],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise ValueError(
            f"git {' '.join(arguments)} failed for {root}: "
            + completed.stderr.decode("utf-8", errors="replace").strip()
        )
    return completed.stdout


def _verify_blobs(root: Path, commit: str, files: list[dict]) -> dict[str, bytes]:
    _git(root, "cat-file", "-e", f"{commit}^{{commit}}")
    verified = {}
    for item in files:
        data = _git(root, "show", f'{commit}:{item["portable_path"]}')
        digest = hashlib.sha256(data).hexdigest()
        if digest != item["byte_sha256"]:
            raise ValueError(
                f'pinned blob differs for {item["portable_path"]}: {digest}'
            )
        verified[item["portable_path"]] = data
    return verified


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--panel-root", type=Path, required=True)
    parser.add_argument("--photo", type=Path)
    args = parser.parse_args()

    source_root = args.source_root.resolve()
    panel_root = args.panel_root.resolve()
    if not source_root.is_dir() or not panel_root.is_dir():
        raise ValueError("explicit source and panel roots must both be directories")

    reviews = [core.load_json(path) for path in REVIEW_PATHS]
    source_commits = {item["source_identity"]["commit"] for item in reviews}
    source_file_count = 0
    source_span_count = 0
    for review in reviews:
        blobs = _verify_blobs(
            source_root,
            review["source_identity"]["commit"],
            review["source_identity"]["files"],
        )
        source_file_count += len(blobs)
        file_paths = {
            item["source_file_id"]: item["portable_path"]
            for item in review["source_identity"]["files"]
        }
        for span in review["evidence_spans"]:
            source = span["source"]
            path = file_paths[source["source_file_id"]]
            line_count = len(blobs[path].splitlines())
            if source["line_start"] < 1 or source["line_end"] > line_count:
                raise ValueError(
                    f'evidence span {span["evidence_span_id"]} exceeds {path}'
                )
            source_span_count += 1

    panel = core.load_json(PANEL_PATH)
    panel_commits = {item["commit"] for item in panel["source_assets"]}
    panel_file_count = 0
    for commit in sorted(panel_commits):
        files = [item for item in panel["source_assets"] if item["commit"] == commit]
        panel_file_count += len(_verify_blobs(panel_root, commit, files))

    photo_state = "not-supplied"
    if args.photo is not None:
        photo = args.photo.resolve()
        if not photo.is_file():
            raise ValueError("explicit visual-reference photo is absent")
        digest = hashlib.sha256(photo.read_bytes()).hexdigest()
        if digest != panel["visual_verification"]["reference_sha256"]:
            raise ValueError("visual-reference photo hash differs")
        photo_state = "hash-matched-non-retained-reference"

    result = {
        "schema_version": "task029-source-verification-result-v0",
        "status": "passed",
        "reference_machines": [
            item["asserted_identity"]["display_name"] for item in reviews
        ],
        "source_commits": sorted(source_commits),
        "source_blob_count": source_file_count,
        "source_span_count": source_span_count,
        "panel_commits": sorted(panel_commits),
        "panel_source_blob_count": panel_file_count,
        "visual_reference": photo_state,
        "verification_method": "read-only-git-object-database-and-explicit-photo-hash",
        "proof_boundary": {
            "source_identity": "passed",
            "structural_level_1": "passed",
            "working_tree_identity": "not-claimed",
            "build_or_runtime": "not-run",
            "connected_device": "not-run",
            "audible_behavior": "not-run",
        },
    }
    print(core.canonical_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
