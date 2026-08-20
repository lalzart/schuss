#!/usr/bin/env python3
"""Validate structured current routing without turning prose into a database."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]

STATE = "docs/governance/current-state.json"
STATUS = "docs/STATUS.md"
ROADMAP = "docs/ROADMAP.md"
HISTORY = "docs/HISTORY.md"
TASKS_INDEX = "docs/tasks/README.md"
DECISIONS_INDEX = "docs/decisions/README.md"
AGENTS = "AGENTS.md"
VALIDATION_MANIFEST = "tools/validation/manifest-v1.json"
TASK_012B = "docs/tasks/012b-object-drawer-and-transparent-graph-canvas.md"

REQUIRED_DOCUMENT_PATHS = (
    AGENTS,
    STATE,
    STATUS,
    ROADMAP,
    HISTORY,
    TASKS_INDEX,
    DECISIONS_INDEX,
    VALIDATION_MANIFEST,
    TASK_012B,
)
DOCUMENT_PATHS = REQUIRED_DOCUMENT_PATHS

STATE_KEYS = {
    "schema_version",
    "active_task",
    "next_candidate",
    "recent_completed_milestones",
    "deferred_tasks",
    "authoritative_decisions",
    "validation_profiles",
    "evidence_boundary",
}
ACTIVE_KEYS = {
    "task_id",
    "phase",
    "kind",
    "status",
    "contract",
    "baseline_commit",
}
NEXT_KEYS = {"task_id", "phase", "status"}
MILESTONE_KEYS = {"task_id", "phase", "status", "commit"}
EVIDENCE_KEYS = {
    "hardware_action_performed",
    "firmware_or_sd_mutation_performed",
    "real_time_level_7_promoted",
    "audible_level_8_promoted",
    "publication_performed",
}
TASK_ID = re.compile(r"^[0-9]{3}$")
DECISION_ID = re.compile(r"^[0-9]{4}$")
COMMIT = re.compile(r"^[0-9a-f]{7,40}$")
KIND = re.compile(r"^[a-z][a-z0-9-]*$")
LETTERED_ALIAS = re.compile(r"\bTasks?\s+(01[3-9]|02[01])[A-Z](?:-[A-Z])?\b", re.I)
INFORMAL_ALIAS = re.compile(r"(?<![A-Za-z0-9])B6(?![A-Za-z0-9])", re.I)
ALIASED_FILENAME = re.compile(r"^(01[3-9]|02[01])[a-z](?:-|\.)", re.I)
DECISION_PATH = re.compile(r"^docs/decisions/([0-9]{4})-[^/]+\.md$")


class _DuplicateMember(ValueError):
    pass


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise _DuplicateMember(key)
        value[key] = item
    return value


def _diagnostic(code: str, document: str, detail: str) -> dict[str, str]:
    return {"code": code, "detail": detail, "document": document}


def _metadata(text: str, field: str) -> str | None:
    match = re.search(rf"^- {re.escape(field)}:\s*(.+?)\s*$", text, re.MULTILINE)
    return match.group(1).strip() if match else None


def _leading_status(text: str) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines[:14]):
        if not line.startswith("Status:"):
            continue
        values = [line.removeprefix("Status:").strip()]
        for continuation in lines[index + 1 :]:
            if not continuation.strip():
                break
            values.append(continuation.strip())
        return " ".join(" ".join(values).split())
    return ""


def _require_headings(
    diagnostics: list[dict[str, str]], document: str, text: str
) -> None:
    headings = (
        "## Goal and why it exists",
        "## In scope",
        "## Out of scope",
        "## Inputs and deliverables",
        "## Acceptance tests",
        "## Decisions",
    )
    missing = [heading for heading in headings if heading not in text]
    if missing:
        diagnostics.append(
            _diagnostic(
                "TASK_CONTRACT_INCOMPLETE",
                document,
                "missing heading families: " + ", ".join(missing),
            )
        )


def _parse_json(
    documents: Mapping[str, str],
    path: str,
    code: str,
    diagnostics: list[dict[str, str]],
) -> Any | None:
    try:
        return json.loads(documents.get(path, ""), object_pairs_hook=_object)
    except (_DuplicateMember, json.JSONDecodeError, ValueError) as exc:
        diagnostics.append(_diagnostic(code, path, str(exc)))
        return None


def _parse_state(
    documents: Mapping[str, str], diagnostics: list[dict[str, str]]
) -> dict[str, Any] | None:
    value = _parse_json(documents, STATE, "GOVERNANCE_STATE_INVALID", diagnostics)
    if not isinstance(value, dict) or set(value) != STATE_KEYS:
        actual = sorted(value) if isinstance(value, dict) else type(value).__name__
        diagnostics.append(
            _diagnostic(
                "GOVERNANCE_STATE_INVALID",
                STATE,
                f"top-level keys must be exact; actual={actual}",
            )
        )
        return None
    if value.get("schema_version") != "schuss-governance-state-v1":
        diagnostics.append(
            _diagnostic("GOVERNANCE_STATE_INVALID", STATE, "unsupported schema_version")
        )
    return value


def _portable_contract(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    path = Path(value)
    return (
        not path.is_absolute()
        and ".." not in path.parts
        and path.parts[:2] == ("docs", "tasks")
        and path.suffix == ".md"
    )


def _task_label(value: Mapping[str, Any] | None) -> str:
    if value is None:
        return "none"
    if not isinstance(value, Mapping):
        return "invalid"
    task_id = value.get("task_id")
    status = value.get("status")
    if not isinstance(task_id, str) or not isinstance(status, str):
        return "invalid"
    phase = value.get("phase")
    suffix = f"-phase-{phase}" if phase is not None else ""
    return f"{task_id}{suffix}@{status}"


def routing_marker(state: Mapping[str, Any]) -> str:
    raw_active = state.get("active_task")
    active = (
        raw_active
        if isinstance(raw_active, dict)
        and isinstance(raw_active.get("task_id"), str)
        and raw_active.get("status") in {"in-progress", "review-ready"}
        and _valid_phase(raw_active.get("phase"))
        else None
    )
    return (
        "<!-- schuss-governance-routing: "
        f"active={_task_label(active)}; "
        f"next={_task_label(state.get('next_candidate'))} -->"
    )


def _prose_task_label(value: Mapping[str, Any]) -> str:
    phase = value.get("phase")
    return f"Task {value['task_id']}" + (
        f" Phase {phase}" if phase is not None else ""
    )


def _valid_phase(value: Any) -> bool:
    return value is None or (
        isinstance(value, int) and not isinstance(value, bool) and value > 0
    )


def _markdown_section(text: str, heading: str) -> str:
    marker = f"## {heading}"
    if marker not in text:
        return ""
    return text.split(marker, 1)[1].split("\n## ", 1)[0]


def _validate_state(
    state: dict[str, Any], documents: Mapping[str, str], diagnostics: list[dict[str, str]]
) -> None:
    active = state.get("active_task")
    if active is not None:
        valid = (
            isinstance(active, dict)
            and set(active) == ACTIVE_KEYS
            and isinstance(active.get("task_id"), str)
            and TASK_ID.fullmatch(active["task_id"])
            and _valid_phase(active.get("phase"))
            and isinstance(active.get("kind"), str)
            and KIND.fullmatch(active["kind"])
            and active.get("status") in {"in-progress", "review-ready"}
            and _portable_contract(active.get("contract"))
            and isinstance(active.get("baseline_commit"), str)
            and COMMIT.fullmatch(active["baseline_commit"])
        )
        if not valid:
            diagnostics.append(
                _diagnostic("ACTIVE_TASK_INVALID", STATE, "active task structure is invalid")
            )
        else:
            contract = active["contract"]
            text = documents.get(contract, "")
            if not text:
                diagnostics.append(
                    _diagnostic("ACTIVE_TASK_CONTRACT_MISSING", contract, "active contract is absent")
                )
            else:
                status = _leading_status(text).lower()
                expected_phrase = (
                    "in progress" if active["status"] == "in-progress" else "review-ready"
                )
                if "explicitly authorized" not in status or expected_phrase not in status:
                    diagnostics.append(
                        _diagnostic(
                            "ACTIVE_TASK_CONTRACT_INVALID",
                            contract,
                            "leading status does not match structured active state",
                        )
                    )
                _require_headings(diagnostics, contract, text)

    next_candidate = state.get("next_candidate")
    if next_candidate is not None:
        valid = (
            isinstance(next_candidate, dict)
            and set(next_candidate) == NEXT_KEYS
            and isinstance(next_candidate.get("task_id"), str)
            and TASK_ID.fullmatch(next_candidate["task_id"])
            and _valid_phase(next_candidate.get("phase"))
            and next_candidate.get("status") == "not-activated"
        )
        if not valid:
            diagnostics.append(
                _diagnostic("NEXT_TASK_INVALID", STATE, "next candidate structure is invalid")
            )

    milestones = state.get("recent_completed_milestones")
    milestone_keys: set[tuple[Any, ...]] = set()
    milestone_work_units: set[tuple[str, int | None]] = set()
    if not isinstance(milestones, list):
        diagnostics.append(_diagnostic("MILESTONE_STATE_INVALID", STATE, "must be a list"))
    else:
        for item in milestones:
            valid = (
                isinstance(item, dict)
                and set(item) == MILESTONE_KEYS
                and isinstance(item.get("task_id"), str)
                and TASK_ID.fullmatch(item["task_id"])
                and _valid_phase(item.get("phase"))
                and item.get("status") in {"complete-local", "complete-published"}
                and isinstance(item.get("commit"), str)
                and COMMIT.fullmatch(item["commit"])
            )
            if not valid:
                diagnostics.append(
                    _diagnostic("MILESTONE_STATE_INVALID", STATE, "milestone structure is invalid")
                )
                continue
            key = (item["task_id"], item["phase"], item["status"], item["commit"])
            work_unit = (item["task_id"], item["phase"])
            if key in milestone_keys or work_unit in milestone_work_units:
                diagnostics.append(
                    _diagnostic(
                        "MILESTONE_STATE_INVALID",
                        STATE,
                        "duplicate milestone work unit",
                    )
                )
            milestone_keys.add(key)
            milestone_work_units.add(work_unit)

    deferred = state.get("deferred_tasks")
    if (
        not isinstance(deferred, list)
        or not all(isinstance(item, str) and TASK_ID.fullmatch(item) for item in deferred)
        or len(deferred) != len(set(deferred))
    ):
        diagnostics.append(
            _diagnostic("DEFERRED_TASK_STATE_INVALID", STATE, "deferred task IDs are invalid")
        )

    active_work = (
        (active.get("task_id"), active.get("phase"))
        if isinstance(active, dict)
        and isinstance(active.get("task_id"), str)
        and _valid_phase(active.get("phase"))
        else None
    )
    next_work = (
        (next_candidate.get("task_id"), next_candidate.get("phase"))
        if isinstance(next_candidate, dict)
        and isinstance(next_candidate.get("task_id"), str)
        and _valid_phase(next_candidate.get("phase"))
        else None
    )
    if active_work is not None and active_work == next_work:
        diagnostics.append(
            _diagnostic(
                "WORK_UNIT_STATE_INVALID",
                STATE,
                "one task/phase cannot be both active and next",
            )
        )
    for label, work in (("active", active_work), ("next", next_work)):
        if work is not None and work in milestone_work_units:
            diagnostics.append(
                _diagnostic(
                    "WORK_UNIT_STATE_INVALID",
                    STATE,
                    f"{label} task/phase is already a completed milestone",
                )
            )
        if (
            work is not None
            and isinstance(deferred, list)
            and work[0] in deferred
        ):
            diagnostics.append(
                _diagnostic(
                    "WORK_UNIT_STATE_INVALID",
                    STATE,
                    f"{label} task is also deferred",
                )
            )

    decisions = state.get("authoritative_decisions")
    if (
        not isinstance(decisions, list)
        or not all(isinstance(item, str) and DECISION_ID.fullmatch(item) for item in decisions)
        or decisions != sorted(set(decisions))
    ):
        diagnostics.append(
            _diagnostic("DECISION_STATE_INVALID", STATE, "decision IDs are invalid")
        )
        decisions = []
    decision_paths: dict[str, list[str]] = {}
    for path in documents:
        match = DECISION_PATH.fullmatch(path)
        if match:
            decision_paths.setdefault(match.group(1), []).append(path)
    for identifier in decisions:
        paths = decision_paths.get(identifier, [])
        if len(paths) != 1:
            diagnostics.append(
                _diagnostic(
                    "AUTHORITATIVE_DECISION_INVALID",
                    STATE,
                    f"decision {identifier} must resolve exactly once",
                )
            )
            continue
        path = paths[0]
        if _metadata(documents[path], "Status") != "accepted":
            diagnostics.append(
                _diagnostic(
                    "AUTHORITATIVE_DECISION_INVALID", path, "authoritative decision is not accepted"
                )
            )
        if f"`{Path(path).name}`" not in documents.get(DECISIONS_INDEX, ""):
            diagnostics.append(
                _diagnostic("DECISIONS_INDEX_INVALID", DECISIONS_INDEX, f"missing {identifier}")
            )

    manifest = _parse_json(
        documents, VALIDATION_MANIFEST, "VALIDATION_MANIFEST_INVALID", diagnostics
    )
    manifest_profiles = list(manifest.get("profiles", {})) if isinstance(manifest, dict) else []
    if state.get("validation_profiles") != manifest_profiles:
        diagnostics.append(
            _diagnostic(
                "VALIDATION_PROFILE_STATE_INVALID",
                STATE,
                "profiles differ from the validation manifest",
            )
        )

    evidence = state.get("evidence_boundary")
    if (
        not isinstance(evidence, dict)
        or set(evidence) != EVIDENCE_KEYS
        or not all(isinstance(value, bool) for value in evidence.values())
    ):
        diagnostics.append(
            _diagnostic("EVIDENCE_BOUNDARY_INVALID", STATE, "evidence boundary is invalid")
        )
    elif isinstance(active, dict) and active.get("kind") == "maintenance" and any(evidence.values()):
        diagnostics.append(
            _diagnostic(
                "EVIDENCE_BOUNDARY_INVALID",
                STATE,
                "maintenance work cannot promote hardware, real-time, audible, or publication evidence",
            )
        )


def _validate_indexes(
    state: dict[str, Any], documents: Mapping[str, str], diagnostics: list[dict[str, str]]
) -> None:
    marker = routing_marker(state)
    for path in (STATUS, ROADMAP, TASKS_INDEX):
        if marker not in documents.get(path, ""):
            diagnostics.append(
                _diagnostic("GOVERNANCE_INDEX_INVALID", path, "routing marker differs")
            )
    raw_active = state.get("active_task")
    active = (
        raw_active
        if isinstance(raw_active, dict)
        and isinstance(raw_active.get("task_id"), str)
        and raw_active.get("status") in {"in-progress", "review-ready"}
        and _valid_phase(raw_active.get("phase"))
        else None
    )
    active_label = _prose_task_label(active) if active is not None else None
    status_text = documents.get(STATUS, "")
    declarations = re.findall(
        r"Task\s+([0-9]{3})(?:\s+Phase\s+([1-9][0-9]*))?\s+"
        r"is the only active task",
        status_text,
    )
    expected = [] if active_label is None else [
        (active["task_id"], "" if active.get("phase") is None else str(active["phase"]))
    ]
    if declarations != expected or (
        active_label is None and "There is no active task." not in status_text
    ):
        diagnostics.append(
            _diagnostic("GOVERNANCE_INDEX_INVALID", STATUS, "active-task prose differs")
        )
    active_sections = {
        STATUS: _markdown_section(status_text, "Current work"),
        ROADMAP: _markdown_section(documents.get(ROADMAP, ""), "Active maintenance"),
        TASKS_INDEX: _markdown_section(documents.get(TASKS_INDEX, ""), "Active"),
    }
    if active_label is not None:
        status_phrase = (
            "in progress" if active["status"] == "in-progress" else "review-ready"
        )
        for path, section in active_sections.items():
            if active_label not in section or status_phrase not in section.lower():
                diagnostics.append(
                    _diagnostic(
                        "GOVERNANCE_INDEX_INVALID",
                        path,
                        "active task or status differs",
                    )
                )
        if f"- {active_label}," not in active_sections[TASKS_INDEX]:
            diagnostics.append(
                _diagnostic(
                    "GOVERNANCE_INDEX_INVALID",
                    TASKS_INDEX,
                    "active task index entry differs",
                )
            )
    else:
        for path, section in active_sections.items():
            if "no active task" not in section.lower():
                diagnostics.append(
                    _diagnostic(
                        "GOVERNANCE_INDEX_INVALID",
                        path,
                        "no-active-task prose is missing",
                    )
                )

    next_candidate = state.get("next_candidate")
    if (
        isinstance(next_candidate, dict)
        and isinstance(next_candidate.get("task_id"), str)
        and _valid_phase(next_candidate.get("phase"))
    ):
        phase = next_candidate.get("phase")
        label = f"Task {next_candidate['task_id']}" + (
            f" Phase {phase}" if phase is not None else ""
        )
        for path in (STATUS, ROADMAP, TASKS_INDEX):
            if label not in documents.get(path, ""):
                diagnostics.append(
                    _diagnostic("GOVERNANCE_INDEX_INVALID", path, f"missing {label}")
                )

    for path in (STATUS, HISTORY, TASKS_INDEX):
        if "VH-001" not in documents.get(path, ""):
            diagnostics.append(
                _diagnostic("GOVERNANCE_INDEX_INVALID", path, "missing VH-001")
            )
    if STATE not in status_text:
        diagnostics.append(
            _diagnostic("GOVERNANCE_INDEX_INVALID", STATUS, "missing structured source link")
        )


def _derived_task_statuses(state: Mapping[str, Any]) -> dict[str, str]:
    values: dict[str, list[str]] = {}
    for item in state.get("recent_completed_milestones", []):
        if (
            not isinstance(item, Mapping)
            or not isinstance(item.get("task_id"), str)
            or not _valid_phase(item.get("phase"))
        ):
            continue
        suffix = "complete" if item["phase"] is None else f"phase{item['phase']}-complete"
        values.setdefault(item["task_id"], []).append(suffix)
    active = state.get("active_task")
    if (
        isinstance(active, Mapping)
        and isinstance(active.get("task_id"), str)
        and isinstance(active.get("status"), str)
        and _valid_phase(active.get("phase"))
    ):
        suffix = (
            active["status"]
            if active.get("phase") is None
            else f"phase{active['phase']}-{active['status']}"
        )
        values.setdefault(active["task_id"], []).append(suffix)
    next_candidate = state.get("next_candidate")
    if (
        isinstance(next_candidate, Mapping)
        and isinstance(next_candidate.get("task_id"), str)
        and isinstance(next_candidate.get("status"), str)
        and _valid_phase(next_candidate.get("phase"))
    ):
        phase = next_candidate.get("phase")
        suffix = next_candidate["status"] if phase is None else f"phase{phase}-{next_candidate['status']}"
        values.setdefault(next_candidate["task_id"], []).append(suffix)
    return {identifier: "+".join(statuses) for identifier, statuses in sorted(values.items())}


def validate_documents(
    documents: Mapping[str, str], task_filenames: Sequence[str]
) -> dict[str, object]:
    diagnostics: list[dict[str, str]] = []
    for path in REQUIRED_DOCUMENT_PATHS:
        if path not in documents:
            diagnostics.append(
                _diagnostic("GOVERNANCE_DOCUMENT_MISSING", path, "required document is absent")
            )

    state = _parse_state(documents, diagnostics)
    if state is not None:
        _validate_state(state, documents, diagnostics)
        _validate_indexes(state, documents, diagnostics)

    retired = " ".join(documents.get(TASK_012B, "").split()).lower()
    if (
        "status: retired by adr 0010; do not implement." not in retired
        or "no ui implementation was accepted" not in retired
    ):
        diagnostics.append(
            _diagnostic(
                "TASK_012B_RETIREMENT_INVALID", TASK_012B, "Task 012B retirement guard changed"
            )
        )

    scope_paths = [STATE, STATUS, ROADMAP, TASKS_INDEX]
    if state and isinstance(state.get("active_task"), dict):
        contract = state["active_task"].get("contract")
        if isinstance(contract, str):
            scope_paths.append(contract)
    current_scopes = "\n".join(documents.get(path, "") for path in scope_paths)
    if LETTERED_ALIAS.search(current_scopes) or INFORMAL_ALIAS.search(current_scopes):
        diagnostics.append(
            _diagnostic(
                "CURRENT_TASK_ALIAS_INVALID", "current governance", "retired task alias is present"
            )
        )
    aliased_files = sorted(name for name in task_filenames if ALIASED_FILENAME.search(name))
    if aliased_files:
        diagnostics.append(
            _diagnostic("TASK_FILENAME_INVALID", "docs/tasks", f"retired aliases: {aliased_files}")
        )
    if (
        state
        and isinstance(state.get("active_task"), dict)
        and isinstance(state["active_task"].get("contract"), str)
    ):
        active_name = Path(state["active_task"]["contract"]).name
        if active_name not in task_filenames:
            diagnostics.append(
                _diagnostic("ACTIVE_TASK_CONTRACT_MISSING", "docs/tasks", active_name)
            )

    diagnostics.sort(key=lambda item: (item["code"], item["document"], item["detail"]))
    state_for_summary = state or {}
    return {
        "schema_version": "backbone-governance-summary-v27",
        "status": "valid" if not diagnostics else "invalid",
        "current_status_source": STATE,
        "active_task": state_for_summary.get("active_task"),
        "next_candidate": state_for_summary.get("next_candidate"),
        "recent_completed_milestones": state_for_summary.get(
            "recent_completed_milestones", []
        ),
        "authoritative_decisions": state_for_summary.get("authoritative_decisions", []),
        "validation_profiles": state_for_summary.get("validation_profiles", []),
        "task_statuses": _derived_task_statuses(state_for_summary),
        "historical_context_policy": "history-and-git-not-live-routing",
        "promotion_gate": "explicit-contract-and-activation-required",
        "checked_documents": sum(path in documents for path in REQUIRED_DOCUMENT_PATHS),
        "diagnostics": diagnostics,
    }


def load_repository_documents(root: Path) -> tuple[dict[str, str], list[str]]:
    paths = set(REQUIRED_DOCUMENT_PATHS)
    for directory in (root / "docs/decisions", root / "docs/tasks"):
        try:
            paths.update(
                path.relative_to(root).as_posix()
                for path in directory.glob("*.md")
                if path.is_file()
            )
        except OSError:
            pass
    documents: dict[str, str] = {}
    for path in sorted(paths):
        try:
            documents[path] = (root / path).read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
    task_filenames = sorted(
        Path(path).name for path in documents if path.startswith("docs/tasks/")
    )
    return documents, task_filenames


def validate_repository(root: Path = ROOT) -> dict[str, object]:
    documents, task_filenames = load_repository_documents(root)
    return validate_documents(documents, task_filenames)


def summary_bytes(summary: Mapping[str, object]) -> bytes:
    return json.dumps(
        summary, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("utf-8") + b"\n"


def main() -> int:
    summary = validate_repository()
    stream = sys.stdout if summary["status"] == "valid" else sys.stderr
    stream.buffer.write(summary_bytes(summary))
    return 0 if summary["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
