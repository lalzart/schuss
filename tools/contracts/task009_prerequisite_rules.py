#!/usr/bin/env python3
"""Fail-closed rules for the Task 009 prerequisite record and evidence boundary."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Iterable

import record_set_rules
import validator_core as core


PROSPECTIVE_RECORD_SET = Path("contracts/record-sets/task009-prospective-v0.json")
EVIDENCE_ROOT = Path("evidence/task-009-prerequisite-v0")
CAPTURE_SUMMARY = EVIDENCE_ROOT / "environment-capture-summary.json"
STRICTLY_EARLIER_FIXTURE = Path(
    "tools/contracts/tests/fixtures/task009-prerequisite-strictly-earlier.json"
)

STAGES = (
    "backend-lowering",
    "artifact-generation",
    "target-compile-link",
)
TERMINAL_STATUSES = {"failed", "unsupported", "unresolved"}


def _diagnostic(
    diagnostics: list[core.Diagnostic],
    code: str,
    subject: str,
    location: str,
    message: str,
) -> None:
    diagnostics.append(core.Diagnostic(code, "error", subject, location, message))


def _reference(record: dict[str, Any], id_field: str) -> dict[str, Any]:
    return {
        id_field: record[id_field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def _exact_key(reference: dict[str, Any], id_field: str) -> tuple[str, int, str]:
    return (
        reference[id_field],
        reference["revision"],
        reference["content_hash"],
    )


def _record_registry(record_set: record_set_rules.LoadedRecordSet) -> dict[tuple[str, int, str], dict[str, Any]]:
    result: dict[tuple[str, int, str], dict[str, Any]] = {}
    for values in record_set.records.values():
        for record in values:
            stable_id = next(record[field] for field in record_set_rules.ID_FIELDS if field in record)
            result[(stable_id, record["revision"], record["content_hash"])] = record
    return result


def _require_reference(
    reference: dict[str, Any],
    id_field: str,
    registry: dict[tuple[str, int, str], dict[str, Any]],
    diagnostics: list[core.Diagnostic],
    subject: str,
    location: str,
) -> dict[str, Any] | None:
    resolved = registry.get(_exact_key(reference, id_field))
    if resolved is None:
        _diagnostic(
            diagnostics,
            "PREREQUISITE_REFERENCE_UNRESOLVED",
            subject,
            location,
            "reference does not resolve exactly in the prospective record set",
        )
    return resolved


def validate_probe_values(
    probe: dict[str, Any],
    result: dict[str, Any],
    evidence: dict[str, Any],
    procedure: dict[str, Any],
    environment: dict[str, Any],
    registry: dict[tuple[str, int, str], dict[str, Any]],
) -> tuple[core.Diagnostic, ...]:
    """Validate reference direction, ordered outcomes, and non-production isolation."""

    diagnostics: list[core.Diagnostic] = []
    subject = f"{probe.get('conformance_probe_id', '<unknown>')}@{probe.get('revision', '?')}"

    expected_records = (
        (probe["binding_reference"], "implementation_id", "$.binding_reference"),
        (probe["contract_reference"], "component_contract_id", "$.contract_reference"),
        (probe["graph_reference"], "graph_id", "$.graph_reference"),
        (probe["environment_reference"], "prerequisite_environment_id", "$.environment_reference"),
        (probe["procedure_reference"], "procedure_id", "$.procedure_reference"),
    )
    for reference, id_field, location in expected_records:
        _require_reference(reference, id_field, registry, diagnostics, subject, location)

    if procedure["environment_reference"] != _reference(environment, "prerequisite_environment_id"):
        _diagnostic(diagnostics, "PROBE_ENVIRONMENT_MISMATCH", subject, "$.procedure_reference", "probe procedure and input must name the same exact environment")
    if probe["environment_reference"] != _reference(environment, "prerequisite_environment_id"):
        _diagnostic(diagnostics, "PROBE_ENVIRONMENT_MISMATCH", subject, "$.environment_reference", "probe input does not name the validated environment")
    if probe["procedure_reference"] != _reference(procedure, "procedure_id"):
        _diagnostic(diagnostics, "PROBE_PROCEDURE_MISMATCH", subject, "$.procedure_reference", "probe input does not name the validated procedure")
    if tuple(probe["requested_stages"]) != STAGES or tuple(procedure["stage_order"]) != STAGES:
        _diagnostic(diagnostics, "PROBE_STAGE_ORDER_INVALID", subject, "$.requested_stages", "probe and procedure must preserve the complete ordered stage sequence")

    result_subject = f"{result.get('conformance_probe_result_id', '<unknown>')}@{result.get('revision', '?')}"
    if result["probe_reference"] != _reference(probe, "conformance_probe_id"):
        _diagnostic(diagnostics, "PROBE_RESULT_INPUT_MISMATCH", result_subject, "$.probe_reference", "probe result does not name its exact input")
    if result["binding_reference"] != probe["binding_reference"]:
        _diagnostic(diagnostics, "PROBE_RESULT_BINDING_MISMATCH", result_subject, "$.binding_reference", "probe result changes the candidate binding")
    if result["environment_reference"] != probe["environment_reference"]:
        _diagnostic(diagnostics, "PROBE_RESULT_ENVIRONMENT_MISMATCH", result_subject, "$.environment_reference", "probe result changes the exact environment")

    outcomes = result["stage_outcomes"]
    if tuple((item["ordinal"], item["stage"]) for item in outcomes) != tuple(enumerate(STAGES, 1)):
        _diagnostic(diagnostics, "PROBE_RESULT_STAGE_ORDER_INVALID", result_subject, "$.stage_outcomes", "probe result outcomes are not the exact ordered stage sequence")

    terminal_seen = False
    expected_overall = "success"
    for index, outcome in enumerate(outcomes):
        status = outcome["status"]
        location = f"$.stage_outcomes[{index}]"
        if terminal_seen and status != "not-run":
            _diagnostic(diagnostics, "PROBE_RESULT_AFTER_TERMINAL", result_subject, location, "all stages after the first terminal outcome must be not-run")
        if status == "not-run":
            terminal_seen = True
            if expected_overall == "success":
                expected_overall = "not-run"
            if outcome["diagnostic_ids"] or outcome["artifact_references"]:
                _diagnostic(diagnostics, "PROBE_NOT_RUN_OUTPUT_INVALID", result_subject, location, "a not-run stage cannot own diagnostics or artifacts")
        elif status in TERMINAL_STATUSES:
            terminal_seen = True
            if expected_overall == "success":
                expected_overall = status
        elif status != "success":
            _diagnostic(diagnostics, "PROBE_RESULT_STATUS_INVALID", result_subject, location, "unknown probe stage status")

    if result["overall_status"] != expected_overall:
        _diagnostic(diagnostics, "PROBE_RESULT_OVERALL_STATUS_MISMATCH", result_subject, "$.overall_status", "overall status must equal the first terminal status or success")

    diagnostic_registry = {item["diagnostic_id"]: item for item in result["diagnostics"]}
    cited_diagnostics: list[str] = []
    for outcome in outcomes:
        for diagnostic_id in outcome["diagnostic_ids"]:
            cited_diagnostics.append(diagnostic_id)
            diagnostic = diagnostic_registry.get(diagnostic_id)
            if diagnostic is None or diagnostic["stage"] != outcome["stage"]:
                _diagnostic(diagnostics, "PROBE_DIAGNOSTIC_REFERENCE_INVALID", result_subject, "$.stage_outcomes", "stage diagnostic reference is missing or names another stage")
    if sorted(cited_diagnostics) != sorted(diagnostic_registry):
        _diagnostic(diagnostics, "PROBE_DIAGNOSTIC_CLOSURE_INVALID", result_subject, "$.diagnostics", "result diagnostics and stage references must be total and equal")

    top_artifacts = {core.canonical_json(item) for item in result["artifact_references"]}
    stage_artifacts = {
        core.canonical_json(item)
        for outcome in outcomes
        for item in outcome["artifact_references"]
    }
    if top_artifacts != stage_artifacts:
        _diagnostic(diagnostics, "PROBE_ARTIFACT_CLOSURE_INVALID", result_subject, "$.artifact_references", "result and stage artifact references must be total and equal")

    evidence_subject = f"{evidence.get('conformance_probe_evidence_id', '<unknown>')}@{evidence.get('revision', '?')}"
    if evidence["probe_result_reference"] != _reference(result, "conformance_probe_result_id"):
        _diagnostic(diagnostics, "PROBE_EVIDENCE_RESULT_MISMATCH", evidence_subject, "$.probe_result_reference", "evidence companion does not name the exact immutable probe result")
    if evidence["binding_reference"] != probe["binding_reference"]:
        _diagnostic(diagnostics, "PROBE_EVIDENCE_BINDING_MISMATCH", evidence_subject, "$.binding_reference", "evidence companion changes the candidate binding")
    if evidence["procedure_reference"] != probe["procedure_reference"]:
        _diagnostic(diagnostics, "PROBE_EVIDENCE_PROCEDURE_MISMATCH", evidence_subject, "$.procedure_reference", "evidence companion changes the procedure")
    expected_evidence_outcome = {
        "success": "passed",
        "not-run": "not-run",
    }.get(result["overall_status"], "failed")
    if evidence["outcome"] != expected_evidence_outcome:
        _diagnostic(
            diagnostics,
            "PROBE_EVIDENCE_OUTCOME_MISMATCH",
            evidence_subject,
            "$.outcome",
            "evidence outcome must faithfully summarize the immutable probe result status",
        )

    if any(item.get("production_selection_authority") is not False for item in (probe, result, procedure)):
        _diagnostic(diagnostics, "PROBE_SELECTION_AUTHORITY_INVALID", subject, "$", "probe records must grant no production selection authority")
    if "evidence" in result or "evidence_reference" in result or "evidence_references" in result:
        _diagnostic(diagnostics, "PROBE_EVIDENCE_CYCLE", result_subject, "$", "probe results cannot point back to evidence")

    return tuple(sorted(set(diagnostics), key=core.diagnostic_sort_key))


def validate_environment_artifacts(
    repository_root: Path,
    environment: dict[str, Any],
) -> tuple[core.Diagnostic, ...]:
    diagnostics: list[core.Diagnostic] = []
    subject = f"{environment['prerequisite_environment_id']}@{environment['revision']}"
    artifact_values = (
        environment["source_capsule"]["manifest"],
        environment["java_closure"]["classpath_manifest"],
        environment["java_closure"]["runtime_manifest"],
        environment["java_closure"]["explicit_configuration_smoke"],
        environment["arm_toolchain"]["toolchain_manifest"],
        environment["firmware_runtime"]["source_input_manifest"],
        environment["firmware_runtime"]["build_command_manifest"],
        environment["firmware_runtime"]["symbol_manifest"],
    )
    for artifact in artifact_values:
        path = repository_root / artifact["portable_path"]
        if (
            not path.is_file()
            or path.stat().st_size != artifact["byte_length"]
            or core.sha256_file(path) != artifact["byte_sha256"]
            or artifact["portable_locator"] != f"sha256/{artifact['byte_sha256']}"
        ):
            _diagnostic(diagnostics, "PREREQUISITE_ARTIFACT_MISMATCH", subject, artifact["portable_path"], "retained environment evidence is missing or byte-mismatched")

    summary_path = repository_root / CAPTURE_SUMMARY
    summary = core.load_json(summary_path)
    expected = {
        "source_archive": environment["source_capsule"]["archive_sha256"],
        "java_classpath": environment["java_closure"]["classpath_fingerprint_sha256"],
        "firmware_bin": environment["firmware_runtime"]["firmware_bin"]["byte_sha256"],
        "firmware_link": environment["firmware_runtime"]["link_elf"]["byte_sha256"],
        "firmware_commands": environment["firmware_runtime"]["build_command_manifest"]["byte_sha256"],
    }
    actual = {
        "source_archive": summary["source"]["archive_sha256"],
        "java_classpath": summary["java"]["classpath_fingerprint_sha256"],
        "firmware_bin": summary["firmware"]["bin_sha256"],
        "firmware_link": summary["firmware"]["link_elf_sha256"],
        "firmware_commands": summary["artifacts"]["firmware-build-commands.json"]["byte_sha256"],
    }
    if actual != expected or not summary["firmware"]["installed_bundle_match"]:
        _diagnostic(diagnostics, "PREREQUISITE_CAPTURE_SUMMARY_MISMATCH", subject, CAPTURE_SUMMARY.as_posix(), "capture summary does not match the semantic environment closure")

    forbidden_fragments = ("/Users/", "/private/", "/tmp/", "file://", "\\Users\\")
    for path in sorted((repository_root / EVIDENCE_ROOT).glob("*")):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if any(fragment in text for fragment in forbidden_fragments):
            _diagnostic(diagnostics, "PREREQUISITE_LOCAL_PATH_LEAK", subject, path.relative_to(repository_root).as_posix(), "retained evidence contains a machine-local absolute path")
    return tuple(sorted(set(diagnostics), key=core.diagnostic_sort_key))


def validate_strictly_earlier_fixture(repository_root: Path) -> tuple[core.Diagnostic, ...]:
    fixture = core.load_json(repository_root / STRICTLY_EARLIER_FIXTURE)
    later = fixture["later_eligibility_binding_reference"]
    named = fixture["evidence_closure_binding_reference"]
    diagnostics: list[core.Diagnostic] = []
    if later["implementation_id"] != named["implementation_id"] or not named["revision"] < later["revision"]:
        _diagnostic(diagnostics, "ELIGIBILITY_EVIDENCE_REVISION_NOT_EARLIER", "task009-prerequisite-strictly-earlier", "$.evidence_closure_binding_reference", "evidence closure must name the same strictly earlier binding revision")
    if fixture["expected_rule"] != "evidence-binding-revision-strictly-less-than-eligibility-binding-revision":
        _diagnostic(diagnostics, "STRICTLY_EARLIER_FIXTURE_INVALID", "task009-prerequisite-strictly-earlier", "$.expected_rule", "fixture does not name the accepted strictly-earlier rule")
    return tuple(diagnostics)


def validate_task009_prerequisite(repository_root: Path) -> dict[str, Any]:
    repository_root = repository_root.resolve()
    accepted = record_set_rules.load_record_set(repository_root, record_set_rules.ACCEPTED_RECORD_SET)
    prospective = record_set_rules.load_record_set(repository_root, PROSPECTIVE_RECORD_SET)
    registry = _record_registry(prospective)

    def only(kind: str) -> dict[str, Any]:
        values = prospective.records.get(kind, ())
        if len(values) != 1:
            raise ValueError(f"expected one prerequisite {kind} record, found {len(values)}")
        return copy.deepcopy(values[0])

    environment = only("prerequisite-environment")
    procedure = only("conformance-probe-procedure")
    probe = only("conformance-probe-input")
    result = only("conformance-probe-result")
    evidence = only("conformance-probe-evidence")

    diagnostics = [
        *validate_probe_values(probe, result, evidence, procedure, environment, registry),
        *validate_environment_artifacts(repository_root, environment),
        *validate_strictly_earlier_fixture(repository_root),
    ]

    build_request_schema = prospective.schemas["build-request-v0"]
    build_result_schema = prospective.schemas["build-result-v0"]
    isolation = {
        "probe_as_build_request_error_count": len(core.schema_errors(probe, build_request_schema, build_request_schema)),
        "probe_result_as_build_result_error_count": len(core.schema_errors(result, build_result_schema, build_result_schema)),
        "production_backend_handler": "absent",
        "production_selection_authority": False,
    }
    if isolation["probe_as_build_request_error_count"] == 0 or isolation["probe_result_as_build_result_error_count"] == 0:
        _diagnostic(diagnostics, "PROBE_PRODUCTION_BOUNDARY_LEAK", probe["conformance_probe_id"], "$", "probe values must fail the normal build request/result schemas")

    diagnostics = sorted(set(diagnostics), key=core.diagnostic_sort_key)
    return {
        "schema_version": "task009-prerequisite-validation-summary-v0",
        "status": "valid" if not diagnostics else "invalid",
        "accepted_record_set": accepted.reference,
        "prospective_record_set": prospective.reference,
        "record_counts": {
            "accepted_records": len(accepted.manifest["record_members"]),
            "accepted_schemas": len(accepted.manifest["schema_members"]),
            "prospective_records": len(prospective.manifest["record_members"]),
            "prospective_schemas": len(prospective.manifest["schema_members"]),
        },
        "probe": {
            "candidate_state": probe["candidate_state"],
            "execution_authorization": probe["execution_authorization"],
            "overall_status": result["overall_status"],
            "stage_outcomes": copy.deepcopy(result["stage_outcomes"]),
            "evidence_outcome": evidence["outcome"],
            "strictly_earlier_fixture": "passed" if not validate_strictly_earlier_fixture(repository_root) else "failed",
        },
        "isolation": isolation,
        "environment": {
            "status": environment["status"],
            "source_archive_sha256": environment["source_capsule"]["archive_sha256"],
            "java_classpath_sha256": environment["java_closure"]["classpath_fingerprint_sha256"],
            "firmware_bin_sha256": environment["firmware_runtime"]["firmware_bin"]["byte_sha256"],
            "firmware_link_elf_sha256": environment["firmware_runtime"]["link_elf"]["byte_sha256"],
            "task009_evidence_levels": copy.deepcopy(environment["task009_evidence_status"]),
        },
        "diagnostics": [item.as_dict() for item in diagnostics],
    }
