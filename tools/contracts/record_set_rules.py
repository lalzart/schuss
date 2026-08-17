"""Exact accepted/prospective record-set loading for the Task 009 prerequisite."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import validator_core as core


RECORD_SET_SCHEMA = Path("schemas/prerequisite/record-set-v0.schema.json")
ACCEPTED_RECORD_SET = Path("contracts/record-sets/task005-008-accepted-v0.json")

ID_FIELDS = (
    "artifact_id",
    "backend_id",
    "binding_eligibility_id",
    "build_environment_id",
    "build_request_id",
    "build_result_id",
    "catalog_id",
    "catalog_selection_id",
    "capability_vocabulary_id",
    "component_contract_id",
    "compute_target_id",
    "conformance_probe_evidence_id",
    "conformance_probe_id",
    "conformance_probe_result_id",
    "coverage_report_id",
    "current_ksoloti_corpus_id",
    "device_profile_id",
    "direct_operation_spec_id",
    "evidence_claim_id",
    "family_id",
    "graph_id",
    "implementation_id",
    "instrument_id",
    "panel_evidence_packet_id",
    "selection_packet_id",
    "prerequisite_environment_id",
    "procedure_id",
    "resource_report_id",
    "runtime_realization_id",
)


class RecordSetError(ValueError):
    pass


@dataclass(frozen=True)
class LoadedRecordSet:
    manifest: dict[str, Any]
    schemas: dict[str, dict[str, Any]]
    records: dict[str, tuple[dict[str, Any], ...]]
    schema_paths: dict[str, Path]
    record_paths: dict[str, tuple[Path, ...]]

    @property
    def reference(self) -> dict[str, Any]:
        return {
            "record_set_id": self.manifest["record_set_id"],
            "revision": self.manifest["revision"],
            "content_hash": self.manifest["content_hash"],
        }


def _repository_path(repository_root: Path, portable_path: str) -> Path:
    path = repository_root / portable_path
    try:
        path.resolve().relative_to(repository_root.resolve())
    except ValueError as exc:
        raise RecordSetError(f"record-set path escapes repository: {portable_path}") from exc
    return path


def _schema_version(schema: dict[str, Any]) -> str:
    identity = schema.get("$id")
    if not isinstance(identity, str) or not identity.endswith(".schema.json"):
        raise RecordSetError("record-set schema member has no portable $id")
    return identity[: -len(".schema.json")]


def _stable_id(record: dict[str, Any]) -> str:
    matches = [record[field] for field in ID_FIELDS if field in record]
    if len(matches) != 1:
        raise RecordSetError("record-set member must contain exactly one stable ID field")
    return matches[0]


def _exact_file_members(directory: Path) -> set[Path]:
    if not directory.is_dir():
        raise RecordSetError(f"enforced record directory is missing: {directory}")
    return {path.resolve() for path in directory.glob("*.json") if path.is_file()}


def load_record_set(
    repository_root: Path,
    manifest_path: Path,
    *,
    accepted_manifest_path: Path | None = None,
) -> LoadedRecordSet:
    repository_root = repository_root.resolve()
    manifest_path = manifest_path if manifest_path.is_absolute() else repository_root / manifest_path
    schema_path = repository_root / RECORD_SET_SCHEMA
    schema = core.load_json(schema_path)
    manifest = core.load_json(manifest_path)
    errors = core.validate_schema_annotations(schema) + core.schema_errors(manifest, schema, schema)
    if errors:
        raise RecordSetError("record-set schema validation failed: " + "; ".join(errors))
    expected_hash = core.record_content_hash(manifest, schema)
    if manifest["content_hash"] != expected_hash:
        raise RecordSetError("record-set content hash mismatch")

    schema_members: dict[str, dict[str, Any]] = {}
    schema_paths: dict[str, Path] = {}
    listed_paths: set[Path] = set()
    for member in manifest["schema_members"]:
        version = member["schema_version"]
        if version in schema_members:
            raise RecordSetError(f"duplicate schema member: {version}")
        path = _repository_path(repository_root, member["portable_path"])
        if path.resolve() in listed_paths:
            raise RecordSetError(f"duplicate record-set path: {member['portable_path']}")
        listed_paths.add(path.resolve())
        if not path.is_file() or core.sha256_file(path) != member["byte_sha256"]:
            raise RecordSetError(f"schema member missing or hash-mismatched: {member['portable_path']}")
        value = core.load_json(path)
        if _schema_version(value) != version:
            raise RecordSetError(f"schema identity mismatch: {member['portable_path']}")
        annotations = core.validate_schema_annotations(value)
        if annotations:
            raise RecordSetError(f"schema annotations invalid: {member['portable_path']}: {annotations}")
        schema_members[version] = value
        schema_paths[version] = path

    records: dict[str, list[dict[str, Any]]] = {}
    record_paths: dict[str, list[Path]] = {}
    exact_keys: set[tuple[str, str, int, str]] = set()
    stable_revisions: dict[tuple[str, str, int], str] = {}
    for member in manifest["record_members"]:
        path = _repository_path(repository_root, member["portable_path"])
        if path.resolve() in listed_paths:
            raise RecordSetError(f"duplicate record-set path: {member['portable_path']}")
        listed_paths.add(path.resolve())
        if not path.is_file() or core.sha256_file(path) != member["byte_sha256"]:
            raise RecordSetError(f"record member missing or hash-mismatched: {member['portable_path']}")
        record = core.load_json(path)
        version = record.get("schema_version")
        record_schema = schema_members.get(version)
        if record_schema is None:
            raise RecordSetError(f"record schema is not listed: {member['portable_path']}")
        structural = core.schema_errors(record, record_schema, record_schema)
        if structural:
            raise RecordSetError(f"record structure invalid: {member['portable_path']}: {structural}")
        stable_id = _stable_id(record)
        expected = (
            member["record_kind"],
            member["stable_id"],
            member["revision"],
            member["content_hash"],
        )
        actual = (member["record_kind"], stable_id, record["revision"], record["content_hash"])
        if actual != expected:
            raise RecordSetError(f"record identity mismatch: {member['portable_path']}")
        if core.record_content_hash(record, record_schema) != record["content_hash"]:
            raise RecordSetError(f"record content hash mismatch: {member['portable_path']}")
        if actual in exact_keys:
            raise RecordSetError(f"duplicate exact record key: {actual}")
        exact_keys.add(actual)
        revision_key = actual[:3]
        prior_hash = stable_revisions.setdefault(revision_key, actual[3])
        if prior_hash != actual[3]:
            raise RecordSetError(f"stable ID/revision collision: {revision_key}")
        records.setdefault(member["record_kind"], []).append(record)
        record_paths.setdefault(member["record_kind"], []).append(path)

    listed_record_paths = {
        _repository_path(repository_root, member["portable_path"]).resolve()
        for member in manifest["record_members"]
    }
    for portable_directory in manifest["enforced_directories"]:
        directory = _repository_path(repository_root, portable_directory)
        actual = _exact_file_members(directory)
        expected = {path for path in listed_record_paths if path.parent == directory.resolve()}
        if actual != expected:
            missing = sorted(path.name for path in expected - actual)
            extra = sorted(path.name for path in actual - expected)
            raise RecordSetError(
                f"enforced directory membership mismatch: {portable_directory}; missing={missing}; extra={extra}"
            )

    if manifest["purpose"] == "prospective-task":
        parent = manifest["parent_reference"]
        if parent["status"] != "included":
            raise RecordSetError("prospective record set must name an accepted parent")
        if accepted_manifest_path is not None:
            parent_path = accepted_manifest_path
        else:
            candidates: list[Path] = []
            for candidate in sorted(manifest_path.parent.glob("*.json")):
                if candidate.resolve() == manifest_path.resolve():
                    continue
                try:
                    value = core.load_json(candidate)
                except (OSError, core.DuplicateJsonMemberError, ValueError):
                    continue
                reference = {
                    key: value.get(key)
                    for key in ("record_set_id", "revision", "content_hash")
                }
                if reference == {
                    key: parent[key]
                    for key in ("record_set_id", "revision", "content_hash")
                }:
                    candidates.append(candidate)
            if len(candidates) != 1:
                raise RecordSetError(
                    "prospective parent manifest must resolve exactly once"
                )
            parent_path = candidates[0]
        accepted = load_record_set(repository_root, parent_path)
        if parent != {"status": "included", **accepted.reference}:
            raise RecordSetError("prospective parent reference mismatch")
        accepted_schemas = {
            (item["schema_version"], item["portable_path"], item["byte_sha256"])
            for item in accepted.manifest["schema_members"]
        }
        current_schemas = {
            (item["schema_version"], item["portable_path"], item["byte_sha256"])
            for item in manifest["schema_members"]
        }
        accepted_records = {
            tuple(item[key] for key in ("record_kind", "stable_id", "revision", "content_hash", "portable_path", "byte_sha256"))
            for item in accepted.manifest["record_members"]
        }
        current_records = {
            tuple(item[key] for key in ("record_kind", "stable_id", "revision", "content_hash", "portable_path", "byte_sha256"))
            for item in manifest["record_members"]
        }
        if not accepted_schemas <= current_schemas or not accepted_records <= current_records:
            raise RecordSetError("prospective view changes or omits accepted parent members")

    return LoadedRecordSet(
        manifest=manifest,
        schemas=schema_members,
        records={kind: tuple(values) for kind, values in sorted(records.items())},
        schema_paths=schema_paths,
        record_paths={kind: tuple(paths) for kind, paths in sorted(record_paths.items())},
    )


def record_paths_by_directory(record_set: LoadedRecordSet, child: str) -> tuple[Path, ...]:
    suffix = f"contracts/{child}/"
    paths = []
    for member in record_set.manifest["record_members"]:
        if member["portable_path"].startswith(suffix):
            paths.append(record_set.record_paths[member["record_kind"]][
                next(
                    index
                    for index, candidate in enumerate(record_set.records[member["record_kind"]])
                    if _stable_id(candidate) == member["stable_id"]
                    and candidate["revision"] == member["revision"]
                    and candidate["content_hash"] == member["content_hash"]
                )
            ])
    return tuple(sorted(paths))
