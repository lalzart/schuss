#!/usr/bin/env python3
"""Validate and reconcile a Schuss Phase 2 legacy raw inventory."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path, PurePosixPath


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def validate_schema(value, schema: dict, location: str = "$") -> None:
    """Validate the small JSON Schema subset used by the raw inventory."""
    if "const" in schema:
        assert value == schema["const"], f"{location}: expected {schema['const']!r}"
    if "enum" in schema:
        assert value in schema["enum"], f"{location}: value outside enum"
    expected = schema.get("type")
    if expected:
        names = expected if isinstance(expected, list) else [expected]
        matches = {
            "object": isinstance(value, dict),
            "array": isinstance(value, list),
            "string": isinstance(value, str),
            "integer": isinstance(value, int) and not isinstance(value, bool),
            "boolean": isinstance(value, bool),
            "null": value is None,
        }
        assert any(matches[name] for name in names), f"{location}: wrong type"
    if isinstance(value, dict):
        required = set(schema.get("required", []))
        assert required <= set(value), f"{location}: missing {sorted(required - set(value))}"
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            assert set(value) <= set(properties), f"{location}: unexpected properties"
        for key, item in value.items():
            if key in properties:
                validate_schema(item, properties[key], f"{location}.{key}")
    if isinstance(value, list):
        if schema.get("uniqueItems"):
            serialized = [json.dumps(item, sort_keys=True) for item in value]
            assert len(serialized) == len(set(serialized)), f"{location}: duplicate items"
        if "items" in schema:
            for index, item in enumerate(value):
                validate_schema(item, schema["items"], f"{location}[{index}]")
    if isinstance(value, str):
        assert len(value) >= schema.get("minLength", 0), f"{location}: too short"
        if "pattern" in schema:
            assert re.search(schema["pattern"], value), f"{location}: pattern mismatch"
    if isinstance(value, int) and not isinstance(value, bool) and "minimum" in schema:
        assert value >= schema["minimum"], f"{location}: below minimum"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("inventory", type=Path)
    args = parser.parse_args()
    root = args.inventory
    manifest = json.loads((root / "manifest.json").read_text())
    files = load_jsonl(root / "raw/files.jsonl")
    issues = load_jsonl(root / "raw/issues.jsonl")
    summary = json.loads((root / "reports/summary.json").read_text())
    schema_root = Path(__file__).resolve().parents[2] / "schemas"
    manifest_schema = json.loads((schema_root / "legacy-catalog-manifest-v0.schema.json").read_text())
    file_schema = json.loads((schema_root / "legacy-catalog-file-v0.schema.json").read_text())
    issue_schema = json.loads((schema_root / "legacy-catalog-issue-v0.schema.json").read_text())
    validate_schema(manifest, manifest_schema)
    for item in files:
        validate_schema(item, file_schema)
    for item in issues:
        validate_schema(item, issue_schema)
    assert manifest["schema_version"] == "legacy-catalog-v0"
    required = {"source_repository", "path", "file_type", "size_bytes", "sha256", "detected_legacy_roles", "parse_status"}
    assert all(required <= set(item) for item in files)
    keys = [(item["source_repository"], item["path"]) for item in files]
    assert keys == sorted(keys) and len(keys) == len(set(keys))
    for item in files:
        path = item["path"]
        assert not Path(path).is_absolute() and ".." not in PurePosixPath(path).parts
        assert item["sha256"] is None or len(item["sha256"]) == 64
        assert item["parse_status"] in {"ok", "error", "not_applicable"}
    assert summary["candidate_file_count"] == len(files)
    assert summary["issue_count"] == len(issues)
    assert summary["candidate_files_by_type"] == dict(sorted(Counter(item["file_type"] for item in files).items()))
    expected_source_types = {
        source: dict(sorted(Counter(
            item["file_type"] for item in files if item["source_repository"] == source
        ).items()))
        for source in sorted({item["source_repository"] for item in files})
    }
    assert summary["candidate_files_by_source_and_type"] == expected_source_types
    assert summary["parse_status_counts"] == dict(sorted(Counter(item["parse_status"] for item in files).items()))
    print(json.dumps({"ok": True, "files": len(files), "issues": len(issues)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
