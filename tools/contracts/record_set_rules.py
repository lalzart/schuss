"""Exact accepted/prospective record-set loading.

One manifest is a cumulative snapshot.  Parent manifests authenticate the
snapshot's ancestry, but their members are already present byte-for-byte in the
selected snapshot.  A top-level load therefore validates the selected member
union once and validates every manifest/parent edge separately.  Load-scoped
caches only avoid duplicate filesystem work inside that one call; later calls
always observe the filesystem again.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

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
    "catalog_source_review_id",
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
    "implementation_availability_policy_id",
    "implementation_provider_id",
    "instrument_id",
    "machine_id",
    "machine_presentation_id",
    "machine_source_review_id",
    "panel_evidence_packet_id",
    "panel_layout_id",
    "object_collection_id",
    "palette_lowering_proof_id",
    "performance_configuration_id",
    "performance_control_contract_id",
    "performance_control_graph_id",
    "selection_packet_id",
    "third_party_source_lock_id",
    "prerequisite_environment_id",
    "procedure_id",
    "resource_report_id",
    "runtime_realization_id",
    "source_release_id",
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
    members: set[Path] = set()
    for path in directory.glob("*.json"):
        if path.is_symlink():
            raise RecordSetError(f"enforced record directory contains a symlink: {path}")
        if path.is_file():
            members.add(path.resolve())
    return members


@dataclass
class _LoadSession:
    repository_root: Path
    record_set_schema: dict[str, Any]
    resolved_paths: dict[str, Path]
    raw_manifests: dict[Path, dict[str, Any]]
    validated_manifests: dict[Path, dict[str, Any]]
    candidate_directories: dict[Path, tuple[tuple[Path, dict[str, Any]], ...]]
    directory_members: dict[Path, frozenset[Path]]

    @classmethod
    def create(cls, repository_root: Path) -> "_LoadSession":
        root = repository_root.resolve()
        schema = core.load_json(root / RECORD_SET_SCHEMA)
        return cls(root, schema, {}, {}, {}, {}, {})

    def repository_path(self, portable_path: str) -> Path:
        cached = self.resolved_paths.get(portable_path)
        if cached is not None:
            return cached
        resolved = self.contained_path(self.repository_root / portable_path)
        self.resolved_paths[portable_path] = resolved
        return resolved

    def contained_path(self, path: Path) -> Path:
        resolved = path.resolve()
        try:
            resolved.relative_to(self.repository_root)
        except ValueError as exc:
            raise RecordSetError(
                f"record-set path escapes repository: {path}"
            ) from exc
        return resolved

    def manifest(self, path: Path) -> dict[str, Any]:
        resolved = self.contained_path(path)
        cached = self.validated_manifests.get(resolved)
        if cached is not None:
            return cached
        value = self.raw_manifests.get(resolved)
        if value is None:
            value = core.load_json(resolved)
            if not isinstance(value, dict):
                raise RecordSetError("record-set manifest must be a JSON object")
            self.raw_manifests[resolved] = value
        errors = core.validate_schema_annotations(
            self.record_set_schema
        ) + core.schema_errors(value, self.record_set_schema, self.record_set_schema)
        if errors:
            raise RecordSetError(
                "record-set schema validation failed: " + "; ".join(errors)
            )
        expected_hash = core.record_content_hash(value, self.record_set_schema)
        if value["content_hash"] != expected_hash:
            raise RecordSetError("record-set content hash mismatch")
        self.validated_manifests[resolved] = value
        return value

    def candidates(self, directory: Path) -> tuple[tuple[Path, dict[str, Any]], ...]:
        resolved_directory = self.contained_path(directory)
        cached = self.candidate_directories.get(resolved_directory)
        if cached is not None:
            return cached
        values: list[tuple[Path, dict[str, Any]]] = []
        for candidate in sorted(resolved_directory.glob("*.json")):
            resolved = self.contained_path(candidate)
            try:
                value = core.load_json(resolved)
            except (OSError, core.DuplicateJsonMemberError, ValueError):
                continue
            if not isinstance(value, dict):
                continue
            self.raw_manifests.setdefault(resolved, value)
            values.append((resolved, value))
        result = tuple(values)
        self.candidate_directories[resolved_directory] = result
        return result

    def exact_directory_members(self, directory: Path) -> frozenset[Path]:
        resolved = self.contained_path(directory)
        cached = self.directory_members.get(resolved)
        if cached is not None:
            return cached
        members = frozenset(_exact_file_members(resolved))
        self.directory_members[resolved] = members
        return members


def _manifest_reference(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_set_id": manifest["record_set_id"],
        "revision": manifest["revision"],
        "content_hash": manifest["content_hash"],
    }


def _schema_member_keys(manifest: dict[str, Any]) -> set[tuple[str, str, str]]:
    return {
        (item["schema_version"], item["portable_path"], item["byte_sha256"])
        for item in manifest["schema_members"]
    }


def _record_member_keys(
    manifest: dict[str, Any],
) -> set[tuple[str, str, int, str, str, str]]:
    fields = (
        "record_kind",
        "stable_id",
        "revision",
        "content_hash",
        "portable_path",
        "byte_sha256",
    )
    return {tuple(item[key] for key in fields) for item in manifest["record_members"]}


def _record_member_key(member: dict[str, Any]) -> tuple[str, str, int, str, str, str]:
    fields = (
        "record_kind",
        "stable_id",
        "revision",
        "content_hash",
        "portable_path",
        "byte_sha256",
    )
    return tuple(member[key] for key in fields)


def _validate_enforced_directories(
    session: _LoadSession,
    manifest: dict[str, Any],
) -> None:
    listed_record_paths = {
        session.repository_path(member["portable_path"])
        for member in manifest["record_members"]
    }
    for portable_directory in manifest["enforced_directories"]:
        directory = session.repository_path(portable_directory)
        actual = session.exact_directory_members(directory)
        expected = {
            path for path in listed_record_paths if path.parent == directory
        }
        if actual != expected:
            missing = sorted(path.name for path in expected - actual)
            extra = sorted(path.name for path in actual - expected)
            raise RecordSetError(
                f"enforced directory membership mismatch: {portable_directory}; "
                f"missing={missing}; extra={extra}"
            )


def _resolve_parent_path(
    session: _LoadSession,
    manifest_path: Path,
    parent: dict[str, Any],
    override: Path | None,
) -> Path:
    if override is not None:
        return (
            override.resolve()
            if override.is_absolute()
            else (session.repository_root / override).resolve()
        )
    expected = {
        key: parent[key] for key in ("record_set_id", "revision", "content_hash")
    }
    candidates = [
        path
        for path, value in session.candidates(manifest_path.parent)
        if path != manifest_path.resolve()
        and {key: value.get(key) for key in expected} == expected
    ]
    if len(candidates) != 1:
        raise RecordSetError("prospective parent manifest must resolve exactly once")
    return candidates[0]


def _validate_parent_chain(
    session: _LoadSession,
    selected_path: Path,
    selected_manifest: dict[str, Any],
    accepted_manifest_path: Path | None,
    selected_record_schema_versions: dict[
        tuple[str, str, int, str, str, str], str
    ],
) -> None:
    path = selected_path.resolve()
    manifest = selected_manifest
    visited = {path}
    first = True
    while manifest["purpose"] == "prospective-task":
        parent = manifest["parent_reference"]
        if parent["status"] != "included":
            raise RecordSetError("prospective record set must name an accepted parent")
        parent_path = _resolve_parent_path(
            session,
            path,
            parent,
            accepted_manifest_path if first else None,
        )
        first = False
        if parent_path in visited:
            raise RecordSetError("record-set parent cycle")
        parent_manifest = session.manifest(parent_path)
        if parent != {"status": "included", **_manifest_reference(parent_manifest)}:
            raise RecordSetError("prospective parent reference mismatch")
        if not _schema_member_keys(parent_manifest) <= _schema_member_keys(manifest):
            raise RecordSetError(
                "prospective view changes or omits accepted parent members"
            )
        if not _record_member_keys(parent_manifest) <= _record_member_keys(manifest):
            raise RecordSetError(
                "prospective view changes or omits accepted parent members"
            )
        parent_schema_versions = {
            item["schema_version"] for item in parent_manifest["schema_members"]
        }
        for member in parent_manifest["record_members"]:
            record_version = selected_record_schema_versions[_record_member_key(member)]
            if record_version not in parent_schema_versions:
                raise RecordSetError(
                    f"parent record schema is not listed: {member['portable_path']}"
                )
        _validate_enforced_directories(session, parent_manifest)
        visited.add(parent_path)
        path = parent_path
        manifest = parent_manifest
    if manifest["parent_reference"] != {"status": "omitted"}:
        raise RecordSetError("accepted baseline must omit its parent reference")


def load_record_set(
    repository_root: Path,
    manifest_path: Path,
    *,
    accepted_manifest_path: Path | None = None,
) -> LoadedRecordSet:
    session = _LoadSession.create(repository_root)
    repository_root = session.repository_root
    manifest_path = session.contained_path(
        manifest_path.resolve()
        if manifest_path.is_absolute()
        else (repository_root / manifest_path).resolve()
    )
    manifest = session.manifest(manifest_path)

    schema_members: dict[str, dict[str, Any]] = {}
    schema_paths: dict[str, Path] = {}
    listed_paths: set[Path] = set()
    for member in manifest["schema_members"]:
        version = member["schema_version"]
        if version in schema_members:
            raise RecordSetError(f"duplicate schema member: {version}")
        path = session.repository_path(member["portable_path"])
        if path in listed_paths:
            raise RecordSetError(f"duplicate record-set path: {member['portable_path']}")
        listed_paths.add(path)
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
    selected_record_schema_versions: dict[
        tuple[str, str, int, str, str, str], str
    ] = {}
    for member in manifest["record_members"]:
        path = session.repository_path(member["portable_path"])
        if path in listed_paths:
            raise RecordSetError(f"duplicate record-set path: {member['portable_path']}")
        listed_paths.add(path)
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
        selected_record_schema_versions[_record_member_key(member)] = version
        if actual in exact_keys:
            raise RecordSetError(f"duplicate exact record key: {actual}")
        exact_keys.add(actual)
        revision_key = actual[:3]
        prior_hash = stable_revisions.setdefault(revision_key, actual[3])
        if prior_hash != actual[3]:
            raise RecordSetError(f"stable ID/revision collision: {revision_key}")
        records.setdefault(member["record_kind"], []).append(record)
        record_paths.setdefault(member["record_kind"], []).append(path)

    _validate_enforced_directories(session, manifest)
    _validate_parent_chain(
        session,
        manifest_path,
        manifest,
        accepted_manifest_path,
        selected_record_schema_versions,
    )

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
