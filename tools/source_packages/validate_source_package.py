#!/usr/bin/env python3
"""Validate one physical source closure against Task 033 source authority."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from typing import Any, Iterable


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.contracts import validator_core as core  # noqa: E402


SCHEMA_VERSION = "physical-source-closure-manifest-v1"
TOP_LEVEL_FIELDS = frozenset(
    {
        "authority",
        "claims",
        "closure",
        "component_groups",
        "package_id",
        "package_revision",
        "schema_version",
        "transitive_support",
    }
)
AUTHORITY_FIELDS = frozenset({"source_release", "source_release_schema_path"})
SOURCE_RELEASE_REFERENCE_FIELDS = frozenset(
    {"content_hash", "path", "revision", "source_release_id"}
)
CLAIM_FIELDS = frozenset({"does_not_provide", "provides"})
CLOSURE_FIELDS = frozenset(
    {
        "files",
        "immutable_root",
        "manifest_algorithm",
        "manifest_sha256",
        "retained_notice_path",
    }
)
FILE_FIELDS = frozenset({"path", "sha256"})
COMPONENT_FIELDS = frozenset({"name", "paths"})
REQUIRED_PROVIDES = frozenset({"physical-build-closure"})
REQUIRED_EXCLUSIONS = frozenset(
    {
        "audible-evidence",
        "catalog-membership",
        "collection-membership",
        "device-evidence",
        "distribution-approval",
        "graph-identity",
        "implementation-identity",
        "license-authority",
        "provenance-authority",
        "provider-identity",
        "real-time-evidence",
        "runtime-support",
        "source-release-identity",
    }
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
CONTENT_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(frozen=True)
class Diagnostic:
    code: str
    message: str

    def line(self) -> str:
        return f"{self.code}: {self.message}"


def _diagnostic(errors: list[Diagnostic], code: str, message: str) -> None:
    errors.append(Diagnostic(code, message))


def _portable_path(value: object) -> bool:
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    path = PurePosixPath(value)
    return (
        not path.is_absolute()
        and value == path.as_posix()
        and "." not in path.parts
        and ".." not in path.parts
    )


def _resolve_repository_path(value: object) -> Path | None:
    if not _portable_path(value):
        return None
    resolved = (REPOSITORY_ROOT / str(value)).resolve()
    try:
        resolved.relative_to(REPOSITORY_ROOT.resolve())
    except ValueError:
        return None
    return resolved


def _canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key}")
        result[key] = value
    return result


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _sorted_unique_strings(
    value: object,
    *,
    field: str,
    code_prefix: str,
    errors: list[Diagnostic],
    allow_empty: bool = False,
) -> list[str]:
    if (
        not isinstance(value, list)
        or (not value and not allow_empty)
        or not all(isinstance(item, str) and item for item in value)
    ):
        _diagnostic(errors, f"INVALID_{code_prefix}", f"{field} must be a string list")
        return []
    if value != sorted(value):
        _diagnostic(errors, f"UNSORTED_{code_prefix}", f"{field} must be sorted")
    if len(value) != len(set(value)):
        _diagnostic(errors, f"DUPLICATE_{code_prefix}", f"{field} contains a duplicate")
    return list(value)


def _validate_exact_fields(
    value: object,
    expected: frozenset[str],
    *,
    label: str,
    code: str,
    errors: list[Diagnostic],
) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        _diagnostic(errors, code, f"{label} must be an object")
        return None
    if set(value) != expected:
        _diagnostic(errors, code, f"{label} fields are not the closed set")
        return None
    return value


def _load_manifest(package_root: Path, errors: list[Diagnostic]) -> dict[str, Any] | None:
    manifest = package_root / "SOURCE_PACKAGE.json"
    try:
        raw = manifest.read_bytes()
    except OSError:
        _diagnostic(errors, "MISSING_MANIFEST", "SOURCE_PACKAGE.json is not readable")
        return None
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        _diagnostic(errors, "MANIFEST_ENCODING", "SOURCE_PACKAGE.json is not UTF-8")
        return None
    try:
        document = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except (json.JSONDecodeError, ValueError):
        _diagnostic(errors, "MALFORMED_MANIFEST", "SOURCE_PACKAGE.json is not strict JSON")
        return None
    if not isinstance(document, dict):
        _diagnostic(errors, "INVALID_MANIFEST", "SOURCE_PACKAGE.json must be an object")
        return None
    if raw != _canonical_bytes(document):
        _diagnostic(
            errors,
            "NONCANONICAL_MANIFEST",
            "SOURCE_PACKAGE.json must be sorted UTF-8/LF canonical JSON",
        )
    return document


def _validate_source_release(
    authority: dict[str, Any],
    *,
    expected_source_release_id: str | None,
    expected_source_release_revision: int | None,
    expected_source_release_content_hash: str | None,
    errors: list[Diagnostic],
) -> dict[str, Any] | None:
    reference = _validate_exact_fields(
        authority.get("source_release"),
        SOURCE_RELEASE_REFERENCE_FIELDS,
        label="authority.source_release",
        code="INVALID_SOURCE_RELEASE_REFERENCE",
        errors=errors,
    )
    schema_path = _resolve_repository_path(authority.get("source_release_schema_path"))
    if schema_path is None:
        _diagnostic(errors, "NON_PORTABLE_AUTHORITY_PATH", "source-release schema path is not portable")
    if reference is None:
        return None
    record_path = _resolve_repository_path(reference.get("path"))
    if record_path is None:
        _diagnostic(errors, "NON_PORTABLE_AUTHORITY_PATH", "source-release record path is not portable")
        return None
    try:
        record = core.load_json(record_path)
        schema = core.load_json(schema_path) if schema_path is not None else None
    except (OSError, ValueError):
        _diagnostic(errors, "MISSING_SOURCE_RELEASE_AUTHORITY", "source-release authority is unreadable")
        return None
    if not isinstance(record, dict) or not isinstance(schema, dict):
        _diagnostic(errors, "INVALID_SOURCE_RELEASE_AUTHORITY", "source-release authority has the wrong shape")
        return None
    schema_errors = core.schema_errors(record, schema, schema)
    if schema_errors:
        _diagnostic(errors, "INVALID_SOURCE_RELEASE_AUTHORITY", "source-release authority fails its accepted schema")
        return record
    if core.record_content_hash(record, schema) != record.get("content_hash"):
        _diagnostic(errors, "SOURCE_RELEASE_CONTENT_DRIFT", "source-release authority content hash drifted")
    actual_reference = {
        "content_hash": record.get("content_hash"),
        "path": reference.get("path"),
        "revision": record.get("revision"),
        "source_release_id": record.get("source_release_id"),
    }
    if actual_reference != reference:
        _diagnostic(errors, "SOURCE_RELEASE_REFERENCE_DRIFT", "source-release reference does not match authority")
    if record.get("support_claim") != "source-identity-and-provenance-only":
        _diagnostic(errors, "SOURCE_RELEASE_SCOPE_DRIFT", "source-release support claim is not source-only")
    if expected_source_release_id is not None and record.get("source_release_id") != expected_source_release_id:
        _diagnostic(errors, "SOURCE_RELEASE_ID_MISMATCH", "source-release ID does not match the required authority")
    if expected_source_release_revision is not None and record.get("revision") != expected_source_release_revision:
        _diagnostic(errors, "SOURCE_RELEASE_REVISION_MISMATCH", "source-release revision does not match the required authority")
    if (
        expected_source_release_content_hash is not None
        and record.get("content_hash") != expected_source_release_content_hash
    ):
        _diagnostic(errors, "SOURCE_RELEASE_HASH_MISMATCH", "source-release hash does not match the required authority")
    return record


def validate_package(
    package_root: Path,
    *,
    source_root: Path | None = None,
    expected_package_id: str | None = None,
    expected_package_revision: str | None = None,
    expected_source_release_id: str | None = None,
    expected_source_release_revision: int | None = None,
    expected_source_release_content_hash: str | None = None,
    expected_closure_manifest_sha256: str | None = None,
    requested_components: Iterable[str] = (),
) -> tuple[dict[str, Any] | None, list[Diagnostic]]:
    errors: list[Diagnostic] = []
    package_root = package_root.resolve()
    document = _load_manifest(package_root, errors)
    if document is None:
        return None, errors
    if set(document) != TOP_LEVEL_FIELDS:
        _diagnostic(errors, "UNKNOWN_TOP_LEVEL_FIELDS", "physical-closure manifest fields are not the closed set")
        return document, errors

    if document.get("schema_version") != SCHEMA_VERSION:
        _diagnostic(errors, "WRONG_SCHEMA", "unsupported physical-closure schema")
    package_id = document.get("package_id")
    package_revision = document.get("package_revision")
    if not isinstance(package_id, str) or not NAME_RE.fullmatch(package_id):
        _diagnostic(errors, "INVALID_PACKAGE_ID", "package_id is invalid")
    if not isinstance(package_revision, str) or not package_revision:
        _diagnostic(errors, "INVALID_PACKAGE_REVISION", "package_revision is invalid")
    if expected_package_id is not None and package_id != expected_package_id:
        _diagnostic(errors, "PACKAGE_ID_MISMATCH", "package_id does not match the required package")
    if expected_package_revision is not None and package_revision != expected_package_revision:
        _diagnostic(errors, "PACKAGE_REVISION_MISMATCH", "package_revision does not match the required package")

    authority = _validate_exact_fields(
        document.get("authority"),
        AUTHORITY_FIELDS,
        label="authority",
        code="INVALID_AUTHORITY",
        errors=errors,
    )
    source_release: dict[str, Any] | None = None
    if authority is not None:
        source_release = _validate_source_release(
            authority,
            expected_source_release_id=expected_source_release_id,
            expected_source_release_revision=expected_source_release_revision,
            expected_source_release_content_hash=expected_source_release_content_hash,
            errors=errors,
        )

    claims = _validate_exact_fields(
        document.get("claims"),
        CLAIM_FIELDS,
        label="claims",
        code="INVALID_CLAIMS",
        errors=errors,
    )
    if claims is not None:
        provides = _sorted_unique_strings(
            claims.get("provides"), field="claims.provides", code_prefix="PROVIDED_CLAIM", errors=errors
        )
        exclusions = _sorted_unique_strings(
            claims.get("does_not_provide"),
            field="claims.does_not_provide",
            code_prefix="EXCLUDED_CLAIM",
            errors=errors,
        )
        if set(provides) != REQUIRED_PROVIDES:
            _diagnostic(errors, "INVALID_PROVIDED_CLAIM", "only physical-build-closure may be provided")
        if not REQUIRED_EXCLUSIONS <= set(exclusions):
            _diagnostic(errors, "MISSING_EXCLUDED_CLAIM", "authority and evidence exclusions are incomplete")
        if set(provides) & set(exclusions):
            _diagnostic(errors, "CONFLICTING_CLAIM", "a claim is both provided and excluded")

    closure = _validate_exact_fields(
        document.get("closure"),
        CLOSURE_FIELDS,
        label="closure",
        code="INVALID_CLOSURE",
        errors=errors,
    )
    immutable_root: object = None
    required_manifest: object = None
    raw_files: object = None
    if closure is not None:
        immutable_root = closure.get("immutable_root")
        required_manifest = closure.get("manifest_sha256")
        raw_files = closure.get("files")
        algorithm = closure.get("manifest_algorithm")
        notice_path = closure.get("retained_notice_path")
        if not _portable_path(immutable_root):
            _diagnostic(errors, "NON_PORTABLE_CLOSURE_ROOT", "closure.immutable_root is not portable")
        if not isinstance(required_manifest, str) or not SHA256_RE.fullmatch(required_manifest):
            _diagnostic(errors, "INVALID_CLOSURE_MANIFEST_SHA256", "closure.manifest_sha256 is invalid")
        if not isinstance(algorithm, str) or "two spaces" not in algorithm or "sorted" not in algorithm:
            _diagnostic(errors, "INVALID_MANIFEST_ALGORITHM", "closure.manifest_algorithm is invalid")
        if not _portable_path(notice_path):
            _diagnostic(errors, "NON_PORTABLE_NOTICE_PATH", "retained notice path is not portable")
        else:
            notice = (package_root / str(notice_path)).resolve()
            try:
                notice.relative_to(package_root)
                notice_text = notice.read_text(encoding="utf-8", errors="strict")
            except (ValueError, OSError, UnicodeError):
                _diagnostic(errors, "MISSING_NOTICE", "retained physical notice is absent")
            else:
                authority_id = source_release.get("source_release_id") if source_release else None
                normalized_notice = " ".join(notice_text.split())
                if (
                    authority_id not in normalized_notice
                    or "not a source-release licensing record" not in normalized_notice
                ):
                    _diagnostic(errors, "NOTICE_AUTHORITY_MISMATCH", "retained notice does not preserve the authority boundary")
        if expected_closure_manifest_sha256 is not None and required_manifest != expected_closure_manifest_sha256:
            _diagnostic(errors, "CLOSURE_MANIFEST_MISMATCH", "closure manifest does not match the required package")

    file_paths: list[str] = []
    manifest_lines: list[bytes] = []
    if not isinstance(raw_files, list) or not raw_files:
        _diagnostic(errors, "INVALID_FILES", "closure.files must be a non-empty list")
    else:
        for index, raw_entry in enumerate(raw_files):
            entry = _validate_exact_fields(
                raw_entry,
                FILE_FIELDS,
                label=f"closure.files[{index}]",
                code="UNKNOWN_FILE_FIELDS",
                errors=errors,
            )
            if entry is None:
                continue
            path = entry.get("path")
            expected_hash = entry.get("sha256")
            if not _portable_path(path):
                _diagnostic(errors, "NON_PORTABLE_FILE_PATH", f"closure.files[{index}].path is not portable")
                continue
            file_paths.append(path)
            if not isinstance(expected_hash, str) or not SHA256_RE.fullmatch(expected_hash):
                _diagnostic(errors, "INVALID_FILE_SHA256", f"invalid SHA-256 for {path}")
                continue
            manifest_lines.append(f"{expected_hash}  {path}\n".encode("utf-8"))
            if _portable_path(immutable_root):
                physical = (package_root / str(immutable_root) / path).resolve()
                closure_root = (package_root / str(immutable_root)).resolve()
                try:
                    physical.relative_to(closure_root)
                except ValueError:
                    _diagnostic(errors, "FILE_PATH_ESCAPE", f"closure path escapes for {path}")
                else:
                    if physical.is_symlink():
                        _diagnostic(errors, "CLOSURE_SYMLINK", f"closure file is a symlink: {path}")
                    elif not physical.is_file():
                        _diagnostic(errors, "MISSING_CLOSURE_FILE", f"closure file is missing: {path}")
                    elif _sha256(physical) != expected_hash:
                        _diagnostic(errors, "CLOSURE_FILE_DRIFT", f"closure file drifted: {path}")
            if source_root is not None:
                source_root_resolved = source_root.resolve()
                authoritative = (source_root_resolved / path).resolve()
                try:
                    authoritative.relative_to(source_root_resolved)
                except ValueError:
                    _diagnostic(errors, "AUTHORITATIVE_PATH_ESCAPE", f"source path escapes for {path}")
                else:
                    if not authoritative.is_file():
                        _diagnostic(errors, "MISSING_AUTHORITATIVE_FILE", f"authoritative file is missing: {path}")
                    elif _sha256(authoritative) != expected_hash:
                        _diagnostic(errors, "AUTHORITATIVE_FILE_DRIFT", f"authoritative file drifted: {path}")
        if file_paths != sorted(file_paths):
            _diagnostic(errors, "UNSORTED_FILE_PATHS", "closure.files must be sorted by path")
        duplicates = sorted({path for path in file_paths if file_paths.count(path) > 1})
        for path in duplicates:
            _diagnostic(errors, "DUPLICATE_FILE_PATH", f"duplicate file path: {path}")

    if source_root is not None and source_release is not None:
        commit = source_release.get("release_identity", {}).get("commit")
        completed = subprocess.run(
            ["git", "-C", str(source_root.resolve()), "rev-parse", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0 or completed.stdout.strip() != commit:
            _diagnostic(errors, "AUTHORITATIVE_REVISION_MISMATCH", "authoritative source root is not at the source-release commit")

    file_set = set(file_paths)
    if _portable_path(immutable_root):
        closure_root = package_root / str(immutable_root)
        actual_files = {
            path.relative_to(closure_root).as_posix()
            for path in closure_root.rglob("*")
            if path.is_file() or path.is_symlink()
        } if closure_root.is_dir() else set()
        for path in sorted(file_set - actual_files):
            _diagnostic(errors, "MISSING_CLOSURE_FILE", f"closure file is missing: {path}")
        for path in sorted(actual_files - file_set):
            _diagnostic(errors, "EXTRA_CLOSURE_FILE", f"unexpected closure file: {path}")

    actual_manifest = hashlib.sha256(b"".join(sorted(manifest_lines))).hexdigest()
    if isinstance(required_manifest, str) and actual_manifest != required_manifest:
        _diagnostic(errors, "CLOSURE_MANIFEST_DRIFT", "path-sensitive physical closure manifest drifted")

    raw_groups = document.get("component_groups")
    components: dict[str, list[str]] = {}
    group_names: list[str] = []
    grouped_paths: set[str] = set()
    if not isinstance(raw_groups, list) or not raw_groups:
        _diagnostic(errors, "INVALID_COMPONENT_GROUPS", "component_groups must be non-empty")
    else:
        for index, raw_group in enumerate(raw_groups):
            group = _validate_exact_fields(
                raw_group,
                COMPONENT_FIELDS,
                label=f"component_groups[{index}]",
                code="UNKNOWN_COMPONENT_FIELDS",
                errors=errors,
            )
            if group is None:
                continue
            name = group.get("name")
            if not isinstance(name, str) or not NAME_RE.fullmatch(name):
                _diagnostic(errors, "INVALID_COMPONENT_NAME", f"component_groups[{index}].name is invalid")
                continue
            group_names.append(name)
            paths = _sorted_unique_strings(
                group.get("paths"),
                field=f"component_groups[{index}].paths",
                code_prefix="COMPONENT_PATH",
                errors=errors,
            )
            components[name] = paths
            grouped_paths.update(paths)
            if any(path not in file_set for path in paths):
                _diagnostic(errors, "COMPONENT_PATH_OUTSIDE_CLOSURE", f"component {name} references outside the closure")
        if group_names != sorted(group_names):
            _diagnostic(errors, "UNSORTED_COMPONENT_GROUPS", "component_groups must be sorted by name")
        duplicates = sorted({name for name in group_names if group_names.count(name) > 1})
        for name in duplicates:
            _diagnostic(errors, "DUPLICATE_COMPONENT", f"duplicate component group: {name}")

    transitive = _sorted_unique_strings(
        document.get("transitive_support"),
        field="transitive_support",
        code_prefix="TRANSITIVE_PATH",
        errors=errors,
        allow_empty=True,
    )
    for path in transitive:
        if path not in file_set:
            _diagnostic(errors, "TRANSITIVE_PATH_OUTSIDE_CLOSURE", "transitive support is outside the closure")
        if path in grouped_paths:
            _diagnostic(errors, "TRANSITIVE_COMPONENT_OVERLAP", "transitive support is also in a component group")
    for path in sorted(file_set - grouped_paths - set(transitive)):
        _diagnostic(errors, "UNCLASSIFIED_FILE", f"file is not classified: {path}")
    for component in requested_components:
        if component not in components:
            _diagnostic(errors, "UNKNOWN_COMPONENT", f"unknown component: {component}")
    return document, errors


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("package_root", type=Path)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--expected-package-id")
    parser.add_argument("--expected-package-revision")
    parser.add_argument("--expected-source-release-id")
    parser.add_argument("--expected-source-release-revision", type=int)
    parser.add_argument("--expected-source-release-content-hash")
    parser.add_argument("--expected-closure-manifest-sha256")
    parser.add_argument("--component", action="append", default=[])
    parser.add_argument("--print-component-paths", action="append", default=[])
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    requested = [*args.component, *args.print_component_paths]
    document, errors = validate_package(
        args.package_root,
        source_root=args.source_root,
        expected_package_id=args.expected_package_id,
        expected_package_revision=args.expected_package_revision,
        expected_source_release_id=args.expected_source_release_id,
        expected_source_release_revision=args.expected_source_release_revision,
        expected_source_release_content_hash=args.expected_source_release_content_hash,
        expected_closure_manifest_sha256=args.expected_closure_manifest_sha256,
        requested_components=requested,
    )
    if errors:
        for error in errors:
            print(error.line())
        return 1
    if args.print_component_paths:
        assert document is not None
        components = {group["name"]: group["paths"] for group in document["component_groups"]}
        paths = sorted(
            {path for component in args.print_component_paths for path in components[component]}
        )
        for path in paths:
            print(path)
    else:
        print("source package: valid physical closure; Task 033 source release authoritative")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
