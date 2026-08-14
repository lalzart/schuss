#!/usr/bin/env python3
"""Deterministic Schuss Phase 2 inventory of legacy Ksoloti source files."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "legacy-catalog-v0"
EXTENSIONS = {".axo": "native-object", ".axs": "subpatch", ".axp": "patch"}
EXCLUDED_DIRECTORY_NAMES = {
    ".git", ".gradle", "__pycache__", "build", "dist", "out", "target"
}


def run_git(root: Path, *args: str) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else None


def repository_record(name: str, root: Path) -> dict[str, Any]:
    top_text = run_git(root, "rev-parse", "--show-toplevel")
    top = Path(top_text) if top_text else None
    remote = run_git(root, "remote", "get-url", "origin") if top else None
    status = run_git(root, "status", "--porcelain") if top else None
    licenses = []
    if top:
        for candidate in sorted(top.iterdir(), key=lambda p: p.name.lower()):
            if candidate.is_file() and candidate.name.lower().startswith(
                ("license", "copying")
            ):
                licenses.append(candidate.name)
    return {
        "name": name,
        "repository": top.name if top else None,
        "remote_url": remote,
        "commit": run_git(root, "rev-parse", "HEAD") if top else None,
        "branch": run_git(root, "branch", "--show-current") if top else None,
        "dirty": bool(status) if status is not None else None,
        "license_files": licenses,
    }


def roles(path: Path, kind: str) -> list[str]:
    found = [kind]
    parts = {part.lower() for part in path.parts}
    for directories, role in (
        (("help",), "help"), (("example", "examples"), "example"),
        (("patches",), "library-patch"), (("demo", "demos"), "demo"),
    ):
        if any(directory in parts for directory in directories):
            found.append(role)
    filename_tokens = {
        token for token in re.split(r"[^a-z0-9]+", path.stem.casefold()) if token
    }
    for token, role in (("help", "help"), ("example", "example"), ("demo", "demo")):
        if token in filename_tokens:
            found.append(role)
    return sorted(set(found))


def candidates(root: Path, output: Path, issues: list[dict[str, Any]], source: str):
    output_resolved = output.resolve()

    def walk_error(exc: OSError) -> None:
        filename = Path(exc.filename) if exc.filename else root
        try:
            relative = filename.relative_to(root).as_posix()
        except ValueError:
            relative = "."
        issues.append({
            "source": source,
            "severity": "error",
            "stage": "raw-read",
            "error_code": "E_DIRECTORY_READ",
            "message": str(exc),
            "related_path": relative,
            "processing_continued": True,
        })

    for directory, directory_names, file_names in os.walk(
        root, topdown=True, followlinks=False, onerror=walk_error
    ):
        current = Path(directory)
        kept_directories = []
        for name in sorted(directory_names, key=str.casefold):
            candidate = current / name
            if name.casefold() in EXCLUDED_DIRECTORY_NAMES or candidate.is_symlink():
                continue
            try:
                if candidate.resolve() == output_resolved:
                    continue
            except OSError:
                pass
            kept_directories.append(name)
        directory_names[:] = kept_directories
        for name in sorted(file_names, key=str.casefold):
            path = current / name
            if path.is_symlink():
                continue
            suffix = path.suffix.lower()
            if suffix in EXTENSIONS:
                yield path, EXTENSIONS[suffix]
            elif (
                suffix == ".java"
                and "generatedobjects" in {part.casefold() for part in path.parts}
                and "src" in {part.casefold() for part in path.parts}
            ):
                yield path, "java-generated-source"


def json_line(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def write_jsonl(path: Path, values: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json_line(value) + "\n" for value in values))


def export(output: Path, sources: list[tuple[str, Path]]) -> int:
    names = [name for name, _ in sources]
    if len(names) != len(set(names)):
        raise ValueError("source names must be unique")
    records: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    repositories = []
    for name, root in sorted(sources):
        repositories.append(repository_record(name, root))
        for path, kind in candidates(root, output, issues, name):
            relative = path.relative_to(root).as_posix()
            parse_status = "not_applicable"
            root_element = None
            warnings: list[str] = []
            errors: list[str] = []
            try:
                data = path.read_bytes()
                size_bytes = len(data)
                sha256 = hashlib.sha256(data).hexdigest()
            except OSError as exc:
                data = None
                size_bytes = None
                sha256 = None
                parse_status = "error"
                errors.append(str(exc))
                issues.append({
                    "source": name,
                    "severity": "error",
                    "stage": "raw-read",
                    "error_code": "E_FILE_READ",
                    "message": str(exc),
                    "related_path": relative,
                    "processing_continued": True,
                })
            if data is not None and path.suffix.lower() in EXTENSIONS:
                try:
                    root_element = ET.fromstring(data).tag
                    parse_status = "ok"
                except (ET.ParseError, UnicodeError) as exc:
                    parse_status = "error"
                    errors.append(str(exc))
                    issues.append({
                        "source": name,
                        "severity": "error",
                        "stage": "raw-parse",
                        "error_code": "E_XML_PARSE",
                        "message": str(exc),
                        "related_path": relative,
                        "processing_continued": True,
                    })
            records.append({
                "source_repository": name,
                "source_commit": repositories[-1]["commit"],
                "library_name": name,
                "path": relative,
                "file_type": path.suffix.lower().lstrip(".") or "java",
                "size_bytes": size_bytes,
                "sha256": sha256,
                "detected_legacy_roles": roles(Path(relative), kind),
                "parse_status": parse_status,
                "root_element": root_element,
                "parse_warnings": warnings,
                "parse_errors": errors,
            })
    records.sort(key=lambda item: (item["source_repository"], item["path"]))
    issues.sort(key=lambda item: (item["source"], item["related_path"], item["error_code"]))
    type_counts = dict(sorted(Counter(row["file_type"] for row in records).items()))
    status_counts = dict(sorted(Counter(row["parse_status"] for row in records).items()))
    source_type_counts = {
        source: dict(sorted(Counter(
            row["file_type"] for row in records if row["source_repository"] == source
        ).items()))
        for source in sorted(names)
    }
    path_sources: dict[str, list[str]] = {}
    for row in records:
        path_sources.setdefault(row["path"], []).append(row["source_repository"])
    duplicate_paths = [
        {"path": path, "sources": sorted(sources_for_path)}
        for path, sources_for_path in sorted(path_sources.items())
        if len(sources_for_path) > 1
    ]
    summary = {
        "schema_version": SCHEMA_VERSION,
        "candidate_file_count": len(records),
        "candidate_files_by_type": type_counts,
        "candidate_files_by_source_and_type": source_type_counts,
        "duplicate_source_relative_paths": duplicate_paths,
        "parse_status_counts": status_counts,
        "issue_count": len(issues),
    }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "exporter": {"name": "export_raw_inventory.py", "version": 1},
        "sources": repositories,
        "enabled_library_roots": [name for name, _ in sorted(sources)],
        "options": {"phase": "raw-files", "timestamp_included": False},
    }
    write_json(output / "manifest.json", manifest)
    write_jsonl(output / "raw/files.jsonl", records)
    write_jsonl(output / "raw/issues.jsonl", issues)
    write_json(output / "reports/summary.json", summary)
    lines = ["# Raw legacy inventory summary", "", f"Candidate files: {len(records)}", "", "## By type", ""]
    lines += [f"- `{key}`: {value}" for key, value in type_counts.items()]
    lines += ["", "## By source and type", ""]
    for source, counts in source_type_counts.items():
        lines.append(f"- `{source}`: " + ", ".join(
            f"`{kind}` {count}" for kind, count in counts.items()
        ))
    lines += ["", "## Parse status", ""]
    lines += [f"- `{key}`: {value}" for key, value in status_counts.items()]
    lines += ["", f"Duplicate source-relative paths across sources: {len(duplicate_paths)}"]
    lines += ["", f"Issues: {len(issues)}", ""]
    (output / "reports/summary.md").write_text("\n".join(lines))
    return 0


def parse_source(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("source must be NAME=PATH")
    name, raw_path = value.split("=", 1)
    path = Path(raw_path).expanduser()
    if not name or not path.is_dir():
        raise argparse.ArgumentTypeError(f"invalid source: {value}")
    return name, path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--source", action="append", required=True, type=parse_source)
    args = parser.parse_args()
    names = [name for name, _ in args.source]
    if len(names) != len(set(names)):
        parser.error("source names must be unique")
    print("scanning explicit legacy sources", file=sys.stderr)
    return export(args.output, args.source)


if __name__ == "__main__":
    raise SystemExit(main())
