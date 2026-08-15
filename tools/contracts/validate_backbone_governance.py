#!/usr/bin/env python3
"""Validate the current Schuss backbone routing without mutating the repository."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from typing import Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]

README = "README.md"
PROJECT_CONTEXT = "docs/PROJECT_CONTEXT.md"
ROADMAP = "docs/ROADMAP.md"
DECISIONS_INDEX = "docs/decisions/README.md"
ADR_0008 = "docs/decisions/0008-defer-ui-until-the-headless-backbone-is-ready.md"
ADR_0009 = "docs/decisions/0009-resume-task-012b-after-durable-project-authoring.md"
ADR_0010 = "docs/decisions/0010-restore-backend-first-sequence-and-retire-task-012b.md"
TASK_012B = "docs/tasks/012b-object-drawer-and-transparent-graph-canvas.md"
TASK_013 = "docs/tasks/013-reusable-compiler-front-half.md"
TASK_014 = "docs/tasks/014-shared-build-execution-and-product-cli.md"
TASK_015 = "docs/tasks/015-normalized-dsp-and-minimal-direct-frontend.md"
TASK_016 = "docs/tasks/016-complete-gills-slice-direct-frontend.md"
TASK_016_BRIEF = "docs/tasks/016-direct-semantics-decision-brief.md"
TASK_017 = "docs/tasks/017-curated-core-and-headless-reference-instruments.md"

DOCUMENT_PATHS = (
    README,
    PROJECT_CONTEXT,
    ROADMAP,
    DECISIONS_INDEX,
    ADR_0008,
    ADR_0009,
    ADR_0010,
    TASK_012B,
    TASK_013,
    TASK_014,
    TASK_015,
    TASK_016,
    TASK_016_BRIEF,
    TASK_017,
)

ACTIVE_SEQUENCE = tuple(f"{number:03d}" for number in range(13, 21))
LETTERED_ALIAS = re.compile(r"\bTasks?\s+(01[3-9]|020)[A-Z](?:-[A-Z])?\b", re.IGNORECASE)
INFORMAL_ALIAS = re.compile(r"(?<![A-Za-z0-9])B6(?![A-Za-z0-9])", re.IGNORECASE)
ALIASED_TASK_FILENAME = re.compile(r"^(01[3-9]|020)[a-z]+-", re.IGNORECASE)
TASK_012B_RESURRECTION = re.compile(
    r"\bTask 012B (?:is|becomes|remains) (?:an? )?"
    r"(?:active|deferred|planned|runnable|immediate)",
    re.IGNORECASE,
)


def _normalized(text: str) -> str:
    return " ".join(text.split())


def _metadata(text: str, field: str) -> str | None:
    match = re.search(rf"^- {re.escape(field)}:\s*(.+?)\s*$", text, re.MULTILINE)
    return match.group(1).strip() if match else None


def _leading_status(text: str, prefix: str = "Status:") -> str | None:
    lines = text.splitlines()
    for index, line in enumerate(lines[:12]):
        if not line.startswith(prefix):
            continue
        values = [line[len(prefix) :].strip()]
        for continuation in lines[index + 1 :]:
            if not continuation.strip():
                break
            values.append(continuation.strip())
        return _normalized(" ".join(values))
    return None


def _section(text: str, heading: str) -> str:
    start = text.find(heading)
    if start < 0:
        return ""
    body_start = start + len(heading)
    following = re.search(r"^##\s+", text[body_start:], re.MULTILINE)
    end = body_start + following.start() if following else len(text)
    return text[body_start:end]


def _contract_without_completion_report(text: str) -> str:
    marker = "## Completion report"
    return text.split(marker, 1)[0]


def _diagnostic(code: str, document: str, detail: str) -> dict[str, str]:
    return {"code": code, "detail": detail, "document": document}


def _roadmap_rows(text: str) -> dict[str, list[list[str]]]:
    rows: dict[str, list[list[str]]] = {}
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 3 or cells[0] in {"Phase", "---"}:
            continue
        rows.setdefault(cells[0], []).append(cells)
    return rows


def validate_documents(
    documents: Mapping[str, str], task_filenames: Sequence[str]
) -> dict[str, object]:
    """Return one deterministic validation summary for supplied document bytes."""

    diagnostics: list[dict[str, str]] = []
    for path in DOCUMENT_PATHS:
        if path not in documents:
            diagnostics.append(
                _diagnostic("GOVERNANCE_DOCUMENT_MISSING", path, "required document is absent")
            )

    adr8_status = _metadata(documents.get(ADR_0008, ""), "Status")
    adr9_status = _metadata(documents.get(ADR_0009, ""), "Status")
    adr10_status = _metadata(documents.get(ADR_0010, ""), "Status")
    if adr10_status != "accepted":
        diagnostics.append(
            _diagnostic("ADR_0010_NOT_ACCEPTED", ADR_0010, "Status must be accepted")
        )
    if _metadata(documents.get(ADR_0010, ""), "Supersedes") != "ADR 0009":
        diagnostics.append(
            _diagnostic(
                "ADR_0010_SUPERSESSION_INVALID",
                ADR_0010,
                "ADR 0010 must supersede ADR 0009",
            )
        )
    if adr9_status != "superseded by ADR 0010":
        diagnostics.append(
            _diagnostic(
                "ADR_0009_NOT_HISTORICAL",
                ADR_0009,
                "Status must be superseded by ADR 0010",
            )
        )
    if adr8_status != "accepted; reaffirmed by ADR 0010":
        diagnostics.append(
            _diagnostic(
                "ADR_0008_REAFFIRMATION_INVALID",
                ADR_0008,
                "Status must be accepted and reaffirmed by ADR 0010",
            )
        )

    index_rules = (
        (
            "`0008-defer-ui-until-the-headless-backbone-is-ready.md` - accepted; reaffirmed by ADR 0010",
            "ADR 0008 status/authority annotation is absent",
        ),
        (
            "`0009-resume-task-012b-after-durable-project-authoring.md` - superseded by ADR 0010; historical only",
            "ADR 0009 historical annotation is absent",
        ),
        (
            "`0010-restore-backend-first-sequence-and-retire-task-012b.md` - accepted; current task-routing authority",
            "ADR 0010 authority annotation is absent",
        ),
    )
    normalized_index = _normalized(documents.get(DECISIONS_INDEX, ""))
    for phrase, detail in index_rules:
        if phrase not in normalized_index:
            diagnostics.append(_diagnostic("DECISIONS_INDEX_AUTHORITY_DRIFT", DECISIONS_INDEX, detail))

    statuses = {
        "012B": _leading_status(documents.get(TASK_012B, "")),
        "013": _leading_status(documents.get(TASK_013, "")),
        "014": _leading_status(documents.get(TASK_014, "")),
        "015": _leading_status(documents.get(TASK_015, "")),
        "016": _leading_status(documents.get(TASK_016, "")),
        "016-decision": _leading_status(documents.get(TASK_016_BRIEF, ""), "Decision status:"),
        "017": _leading_status(documents.get(TASK_017, "")),
    }
    expected_status_fragments = {
        "013": ("complete on 2026-08-16", "accepted locally through compiler stage 6"),
        "014": ("complete on 2026-08-16", "accepted locally through evidence level 5"),
        "015": ("complete on 2026-08-16", "accepted locally through evidence level 4"),
        "016": (
            "contract and prerequisite evidence audit complete on 2026-08-16",
            "implementation not started because one explicit compatibility-mode decision is still required",
        ),
        "017": (
            "contract complete on 2026-08-16",
            "implementation not started because Task 016 is an unmet dependency",
        ),
    }
    for task, fragments in expected_status_fragments.items():
        status = statuses[task] or ""
        if any(fragment not in status for fragment in fragments):
            diagnostics.append(
                _diagnostic(
                    f"TASK_{task}_STATUS_DRIFT",
                    globals()[f"TASK_{task}"],
                    "live task status does not match current routing",
                )
            )
    if statuses["012B"] != "retired by ADR 0010; do not implement.":
        diagnostics.append(
            _diagnostic(
                "TASK_012B_UI_RESURRECTED",
                TASK_012B,
                "Task 012B must remain a non-runnable retirement notice",
            )
        )
    task12b = _normalized(documents.get(TASK_012B, ""))
    task12b_required = (
        "No UI implementation was accepted under this task.",
        "If asked to run Task 012B, stop and report that the identifier is retired.",
        "Do not reinterpret it as UI, compiler, backend, or any other implementation work.",
    )
    if TASK_012B_RESURRECTION.search(task12b) or any(
        phrase not in task12b for phrase in task12b_required
    ):
        diagnostics.append(
            _diagnostic(
                "TASK_012B_UI_RESURRECTED",
                TASK_012B,
                "Task 012B cannot carry runnable, deferred, or UI implementation semantics",
            )
        )
    if statuses["016-decision"] != "required. No option is accepted by this brief.":
        diagnostics.append(
            _diagnostic(
                "TASK_016_DECISION_STATUS_DRIFT",
                TASK_016_BRIEF,
                "compatibility-mode decision must remain required and unselected",
            )
        )

    task17_dependency = _normalized(_section(documents.get(TASK_017, ""), "## Dependency"))
    if (
        "Task 016 must be complete" not in task17_dependency
        or "Task 017 may not begin semantic promotion or implementation" not in task17_dependency
    ):
        diagnostics.append(
            _diagnostic(
                "TASK_017_DEPENDENCY_INVALID",
                TASK_017,
                "Task 017 must fail closed until Task 016 is complete",
            )
        )

    current_status_rules = {
        README: (
            "Tasks 013-015 are complete.",
            "ADR 0010 retires the misinterpreted Task 012B UI contract.",
            "Task 017 has a concrete contract and waits for Task 016.",
        ),
        PROJECT_CONTEXT: (
            "ADR 0010 retires the misinterpreted Task 012B UI contract.",
            "Task 013 now consumes either that exact project closure",
            "Task 014 now supplies the exact shared execution/CLI boundary",
            "Task 015 now proves the minimal normalized-DSP/direct-C++ path",
            "Task 017 waits for that dependency.",
        ),
        ROADMAP: (
            "Tasks 013-015 are complete.",
            "Task 012B is retired and must not be run.",
            "Task 017 waits for it.",
        ),
    }
    for document, phrases in current_status_rules.items():
        normalized = _normalized(documents.get(document, ""))
        for phrase in phrases:
            if phrase not in normalized:
                diagnostics.append(
                    _diagnostic(
                        "CURRENT_ROUTING_STATUS_DRIFT",
                        document,
                        f"missing current-routing assertion: {phrase}",
                    )
                )

    ui_scopes = {
        README: documents.get(README, ""),
        PROJECT_CONTEXT: documents.get(PROJECT_CONTEXT, ""),
        ROADMAP: documents.get(ROADMAP, ""),
        TASK_012B: documents.get(TASK_012B, ""),
        ADR_0010: _section(documents.get(ADR_0010, ""), "## Decision"),
    }
    for document, scope in ui_scopes.items():
        normalized = _normalized(scope).lower()
        if (
            "object drawer" not in normalized
            or "graph canvas" not in normalized
            or "unnumbered" not in normalized
            or "explicit" not in normalized
            or "authoriz" not in normalized
        ):
            diagnostics.append(
                _diagnostic(
                    "UI_MILESTONE_ROUTING_INVALID",
                    document,
                    "UI must remain unnumbered and require explicit authorization",
                )
            )
        if TASK_012B_RESURRECTION.search(_normalized(scope)):
            diagnostics.append(
                _diagnostic(
                    "TASK_012B_UI_RESURRECTED",
                    document,
                    "current routing resurrects Task 012B implementation semantics",
                )
            )

    roadmap_rows = _roadmap_rows(documents.get(ROADMAP, ""))
    for number in range(13, 21):
        label = str(number)
        rows = roadmap_rows.get(label, [])
        if len(rows) != 1:
            diagnostics.append(
                _diagnostic(
                    "BACKBONE_SEQUENCE_INVALID",
                    ROADMAP,
                    f"roadmap must contain exactly one ordinary Task {number:03d} row",
                )
            )
    expected_roadmap_status = {
        "13": "complete",
        "14": "complete",
        "15": "complete",
        "16": "awaits one compatibility-mode choice",
        "17": "waits for Task 016",
        "18": "deferred behind the backbone sequence",
        "19": "deferred behind the backbone sequence",
        "20": "deferred behind the backbone sequence",
    }
    for label, expected in expected_roadmap_status.items():
        rows = roadmap_rows.get(label, [])
        if len(rows) == 1 and expected.lower() not in rows[0][2].lower():
            diagnostics.append(
                _diagnostic(
                    "BACKBONE_SEQUENCE_STATUS_DRIFT",
                    ROADMAP,
                    f"Task {int(label):03d} roadmap status must contain: {expected}",
                )
            )
    deferred_ui = roadmap_rows.get("Deferred UI", [])
    if len(deferred_ui) != 1 or "unnumbered" not in deferred_ui[0][2].lower():
        diagnostics.append(
            _diagnostic(
                "UI_MILESTONE_NUMBERED",
                ROADMAP,
                "roadmap must contain one unnumbered Deferred UI row",
            )
        )

    adr10_decision = _normalized(_section(documents.get(ADR_0010, ""), "## Decision"))
    for number in range(13, 21):
        if f"Task {number:03d}:" not in adr10_decision:
            diagnostics.append(
                _diagnostic(
                    "ADR_0010_SEQUENCE_INCOMPLETE",
                    ADR_0010,
                    f"ADR 0010 decision must route Task {number:03d}",
                )
            )

    alias_scopes = {
        README: documents.get(README, ""),
        PROJECT_CONTEXT: documents.get(PROJECT_CONTEXT, ""),
        ROADMAP: documents.get(ROADMAP, ""),
        DECISIONS_INDEX: documents.get(DECISIONS_INDEX, ""),
        ADR_0010: _section(documents.get(ADR_0010, ""), "## Decision"),
        TASK_012B: documents.get(TASK_012B, ""),
        TASK_013: _contract_without_completion_report(documents.get(TASK_013, "")),
        TASK_014: _contract_without_completion_report(documents.get(TASK_014, "")),
        TASK_015: _contract_without_completion_report(documents.get(TASK_015, "")),
        TASK_016: documents.get(TASK_016, ""),
        TASK_016_BRIEF: documents.get(TASK_016_BRIEF, ""),
        TASK_017: documents.get(TASK_017, ""),
    }
    for document, scope in alias_scopes.items():
        matches = sorted(set(LETTERED_ALIAS.findall(scope)))
        if matches:
            diagnostics.append(
                _diagnostic(
                    "LETTERED_TASK_ALIAS_PRESENT",
                    document,
                    "current routing contains a lettered alias for Task " + ", ".join(matches),
                )
            )
        if INFORMAL_ALIAS.search(scope):
            diagnostics.append(
                _diagnostic(
                    "INFORMAL_TASK_ALIAS_PRESENT",
                    document,
                    "current routing contains informal alias B6",
                )
            )
    for filename in sorted(task_filenames):
        if ALIASED_TASK_FILENAME.match(filename) or filename.lower().startswith("b6-"):
            diagnostics.append(
                _diagnostic(
                    "ALIASED_TASK_FILENAME_PRESENT",
                    "docs/tasks",
                    f"current task filename is not an ordinary integer label: {filename}",
                )
            )

    diagnostics.sort(key=lambda item: (item["code"], item["document"], item["detail"]))
    task_statuses = {
        "012B": "retired",
        "013": "complete",
        "014": "complete",
        "015": "complete",
        "016": "awaiting-explicit-compatibility-mode-decision",
        "017": "blocked-by-task-016",
    }
    return {
        "active_task_sequence": list(ACTIVE_SEQUENCE),
        "authoritative_decision": "ADR 0010",
        "checked_documents": len([path for path in DOCUMENT_PATHS if path in documents]),
        "diagnostics": diagnostics,
        "historical_context_policy": "superseded-adrs-and-completion-reports-excluded-from-current-alias-scan",
        "schema_version": "backbone-governance-summary-v1",
        "status": "valid" if not diagnostics else "invalid",
        "task_statuses": task_statuses,
        "ui_milestone_status": "unnumbered-explicit-authorization-required",
    }


def load_repository_documents(root: Path) -> tuple[dict[str, str], list[str]]:
    documents: dict[str, str] = {}
    for path in DOCUMENT_PATHS:
        candidate = root / path
        try:
            documents[path] = candidate.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
    task_root = root / "docs/tasks"
    try:
        task_filenames = sorted(path.name for path in task_root.iterdir() if path.is_file())
    except OSError:
        task_filenames = []
    return documents, task_filenames


def validate_repository(root: Path = ROOT) -> dict[str, object]:
    documents, task_filenames = load_repository_documents(root)
    return validate_documents(documents, task_filenames)


def summary_bytes(summary: Mapping[str, object]) -> bytes:
    return json.dumps(summary, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode(
        "utf-8"
    ) + b"\n"


def main() -> int:
    summary = validate_repository()
    stream = sys.stdout.buffer if summary["status"] == "valid" else sys.stderr.buffer
    stream.write(summary_bytes(summary))
    return 0 if summary["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
