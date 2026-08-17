#!/usr/bin/env python3
"""Validate current Schuss routing and repository-history policy read-only."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from typing import Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]

README = "README.md"
PROJECT_CONTEXT = "docs/PROJECT_CONTEXT.md"
STATUS = "docs/STATUS.md"
ROADMAP = "docs/ROADMAP.md"
APPLICATION_SPINE_PLAN = "docs/APPLICATION_SPINE_PLAN.md"
HISTORY = "docs/HISTORY.md"
TASKS_INDEX = "docs/tasks/README.md"
DECISIONS_INDEX = "docs/decisions/README.md"
ADR_0008 = "docs/decisions/0008-defer-ui-until-the-headless-backbone-is-ready.md"
ADR_0009 = "docs/decisions/0009-resume-task-012b-after-durable-project-authoring.md"
ADR_0010 = "docs/decisions/0010-restore-backend-first-sequence-and-retire-task-012b.md"
ADR_0011 = "docs/decisions/0011-preserve-legacy-equivalent-direct-semantics.md"
ADR_0012 = "docs/decisions/0012-require-executable-gills-promotion.md"
ADR_0013 = "docs/decisions/0013-version-gills-runtime-correction-and-level6-evidence.md"
ADR_0014 = "docs/decisions/0014-sequence-application-spine-and-authorize-ui-architecture.md"
ADR_0015 = "docs/decisions/0015-retarget-task-027-to-mutable-catalog-provenance.md"
TASK_012B = "docs/tasks/012b-object-drawer-and-transparent-graph-canvas.md"
TASK_018 = "docs/tasks/018-full-gills-implementation-and-parameter-control-mapping.md"
TASK_021 = "docs/tasks/021-gills-dma-safe-oled-and-connected-device-evidence.md"
TASK_022 = "docs/tasks/022-connected-gills-control-panel-evidence.md"
TASK_023 = "docs/tasks/023-cli-v2-and-application-surface-consolidation.md"
TASK_024 = "docs/tasks/024-complete-catalog-coverage-and-deterministic-curation.md"
TASK_025 = "docs/tasks/025-direct-compiler-core-library-tranche.md"
TASK_026 = "docs/tasks/026-complete-authoring-operations-and-cli-workflow.md"
TASK_027 = "docs/tasks/027-mutable-instruments-catalog-provenance.md"
TASK_028 = "docs/tasks/028-twenty-item-direct-palette.md"

DOCUMENT_PATHS = (
    README,
    PROJECT_CONTEXT,
    STATUS,
    ROADMAP,
    APPLICATION_SPINE_PLAN,
    HISTORY,
    TASKS_INDEX,
    DECISIONS_INDEX,
    ADR_0008,
    ADR_0009,
    ADR_0010,
    ADR_0011,
    ADR_0012,
    ADR_0013,
    ADR_0014,
    ADR_0015,
    TASK_012B,
    TASK_018,
    TASK_021,
    TASK_022,
    TASK_023,
    TASK_024,
    TASK_025,
    TASK_026,
    TASK_027,
    TASK_028,
)

ACTIVE_SEQUENCE = tuple(f"{number:03d}" for number in range(13, 29))
PLANNED_SEQUENCE: tuple[str, ...] = ()
EXPECTED_TASK_FILENAMES = {
    "README.md",
    "012b-object-drawer-and-transparent-graph-canvas.md",
    "018-full-gills-implementation-and-parameter-control-mapping.md",
    "021-gills-dma-safe-oled-and-connected-device-evidence.md",
    "022-connected-gills-control-panel-evidence.md",
    "023-cli-v2-and-application-surface-consolidation.md",
    "024-complete-catalog-coverage-and-deterministic-curation.md",
    "025-direct-compiler-core-library-tranche.md",
    "026-complete-authoring-operations-and-cli-workflow.md",
    "027-mutable-instruments-catalog-provenance.md",
    "028-twenty-item-direct-palette.md",
}
LETTERED_ALIAS = re.compile(r"\bTasks?\s+(01[3-9]|02[01])[A-Z](?:-[A-Z])?\b", re.IGNORECASE)
INFORMAL_ALIAS = re.compile(r"(?<![A-Za-z0-9])B6(?![A-Za-z0-9])", re.IGNORECASE)
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


def _require_phrases(
    diagnostics: list[dict[str, str]],
    *,
    code: str,
    document: str,
    scope: str,
    phrases: Sequence[str],
) -> None:
    normalized = _normalized(scope)
    for phrase in phrases:
        if phrase not in normalized:
            diagnostics.append(
                _diagnostic(code, document, f"missing governance assertion: {phrase}")
            )


def validate_documents(
    documents: Mapping[str, str], task_filenames: Sequence[str]
) -> dict[str, object]:
    """Return a deterministic validation summary for supplied document bytes."""

    diagnostics: list[dict[str, str]] = []
    for path in DOCUMENT_PATHS:
        if path not in documents:
            diagnostics.append(
                _diagnostic("GOVERNANCE_DOCUMENT_MISSING", path, "required document is absent")
            )

    expected_adr_statuses = {
        ADR_0008: "accepted; reaffirmed by ADR 0010",
        ADR_0009: "superseded by ADR 0010",
        ADR_0010: "accepted",
        ADR_0011: "accepted",
        ADR_0012: "accepted",
        ADR_0013: "accepted",
        ADR_0014: "accepted",
        ADR_0015: "accepted",
    }
    for path, expected in expected_adr_statuses.items():
        if _metadata(documents.get(path, ""), "Status") != expected:
            code = f"ADR_{Path(path).name[:4]}_NOT_ACCEPTED"
            if path == ADR_0009:
                code = "ADR_0009_NOT_HISTORICAL"
            elif path == ADR_0008:
                code = "ADR_0008_REAFFIRMATION_INVALID"
            diagnostics.append(_diagnostic(code, path, f"Status must be: {expected}"))

    if _metadata(documents.get(ADR_0010, ""), "Supersedes") != "ADR 0009":
        diagnostics.append(
            _diagnostic(
                "ADR_0010_SUPERSESSION_INVALID",
                ADR_0010,
                "ADR 0010 must supersede ADR 0009",
            )
        )

    index_rules = (
        "`0008-defer-ui-until-the-headless-backbone-is-ready.md` - accepted; reaffirmed by ADR 0010",
        "`0009-resume-task-012b-after-durable-project-authoring.md` - superseded by ADR 0010; historical only",
        "`0010-restore-backend-first-sequence-and-retire-task-012b.md` - accepted; current task-routing authority",
        "`0011-preserve-legacy-equivalent-direct-semantics.md` - accepted; current direct-semantics authority",
        "`0012-require-executable-gills-promotion.md` - accepted; current Task 018 promotion authority",
        "`0013-version-gills-runtime-correction-and-level6-evidence.md` - accepted; current Task 021 corrective and level-6 authority",
        "`0014-sequence-application-spine-and-authorize-ui-architecture.md` - accepted; application-spine and UI-architecture authority, amended by ADR 0015 for Task 027 only",
        "`0015-retarget-task-027-to-mutable-catalog-provenance.md` - accepted; current Task 027 retarget and Mutable-provenance authority",
    )
    _require_phrases(
        diagnostics,
        code="DECISIONS_INDEX_AUTHORITY_DRIFT",
        document=DECISIONS_INDEX,
        scope=documents.get(DECISIONS_INDEX, ""),
        phrases=index_rules,
    )

    task12_status = _leading_status(documents.get(TASK_012B, ""))
    task12 = _normalized(documents.get(TASK_012B, ""))
    task12_required = (
        "No UI implementation was accepted under this task.",
        "If asked to run Task 012B, stop and report that the identifier is retired.",
        "Do not reinterpret it as UI, compiler, backend, or any other implementation work.",
    )
    if (
        task12_status != "retired by ADR 0010; do not implement."
        or TASK_012B_RESURRECTION.search(task12)
        or any(phrase not in task12 for phrase in task12_required)
    ):
        diagnostics.append(
            _diagnostic(
                "TASK_012B_UI_RESURRECTED",
                TASK_012B,
                "Task 012B must remain a non-runnable retirement notice",
            )
        )

    task18_status = _leading_status(documents.get(TASK_018, "")) or ""
    for fragment in (
        "completed on 2026-08-16",
        "Tasks 016 and 017 remain exact dependencies",
        "deterministic local evidence level 5",
        "ADR 0012",
    ):
        if fragment not in task18_status:
            diagnostics.append(
                _diagnostic(
                    "TASK_018_STATUS_DRIFT",
                    TASK_018,
                    f"live task status must contain: {fragment}",
                )
            )

    task18_dependencies = _section(documents.get(TASK_018, ""), "## Dependencies")
    _require_phrases(
        diagnostics,
        code="TASK_018_DEPENDENCY_INVALID",
        document=TASK_018,
        scope=task18_dependencies,
        phrases=(
            "Task 017 must be complete before Task 018 may create",
            "Task 017 itself depends on Task 016",
            "Task 018 may not bypass either dependency",
        ),
    )

    task18 = documents.get(TASK_018, "")
    _require_phrases(
        diagnostics,
        code="TASK_018_EXECUTABLE_GATE_INVALID",
        document=TASK_018,
        scope=task18,
        phrases=(
            "At least one exact mapped Gills reference",
            "evidence level 5",
            "A graph-only build",
            "does not satisfy this executable promotion gate",
        ),
    )

    task21_status = _leading_status(documents.get(TASK_021, "")) or ""
    for fragment in (
        "completed on 2026-08-16",
        "deterministic local evidence level 5",
        "separately retained connected-device evidence level 6",
        "ADR 0013",
    ):
        if fragment not in task21_status:
            diagnostics.append(
                _diagnostic(
                    "TASK_021_STATUS_DRIFT",
                    TASK_021,
                    f"live task status must contain: {fragment}",
                )
            )
    _require_phrases(
        diagnostics,
        code="TASK_021_CORRECTIVE_BOUNDARY_INVALID",
        document=TASK_021,
        scope=documents.get(TASK_021, ""),
        phrases=(
            "Preserve every Task 018 record",
            "dedicated two-byte `.sram2` buffer",
            "mechanical instrument/coverage successors",
            "No implicit fallback",
            "Levels 7 and 8 remain `not-run`",
            "firmware flash, SD-card write",
        ),
    )

    task22_status = _leading_status(documents.get(TASK_022, "")) or ""
    for fragment in (
        "Phase A completed on 2026-08-16",
        "deterministic local evidence level 5",
        "Phase B stopped after exactly one approved diagnostic volatile-RAM upload",
        "POT_EVENT_FOCUS_UNSTABLE",
        "Approval gate 2 is closed",
    ):
        if fragment not in task22_status:
            diagnostics.append(
                _diagnostic(
                    "TASK_022_STATUS_DRIFT",
                    TASK_022,
                    f"live task status must contain: {fragment}",
                )
            )
    _require_phrases(
        diagnostics,
        code="TASK_022_APPROVAL_BOUNDARY_INVALID",
        document=TASK_022,
        scope=documents.get(TASK_022, ""),
        phrases=(
            "No device command is permitted in Phase A.",
            "Approval gate 1: diagnostic volatile-RAM upload",
            "Approval gate 2: immutable Task 021 product-binary upload",
            "exactly one approved diagnostic volatile-RAM upload",
            "POT_EVENT_FOCUS_UNSTABLE",
            "Approval gate 2 is closed",
            "A partial panel sweep is not complete level-6 panel evidence.",
            "Levels 7 and 8 remain `not-run`",
        ),
    )

    task23_status = _leading_status(documents.get(TASK_023, "")) or ""
    for fragment in (
        "accepted by the user and completed on 2026-08-16",
        "passed all sixteen acceptance tests",
        "ADR 0014",
    ):
        if fragment not in task23_status:
            diagnostics.append(
                _diagnostic(
                    "TASK_023_CONTRACT_INVALID",
                    TASK_023,
                    f"Task 023 contract status must contain: {fragment}",
                )
            )
    _require_phrases(
        diagnostics,
        code="TASK_023_CONTRACT_INVALID",
        document=TASK_023,
        scope=documents.get(TASK_023, ""),
        phrases=(
            "application.describe",
            "application-capability-description-v0",
            "operation-request-v7",
            "operation-result-v7",
            "schuss-record-set-000015@1",
            "schuss-record-set-000014@1",
            "Task 011A golden fixture remains byte-identical",
            "Task 023A",
            "Task 023B",
            "Task 023C",
            "Tasks 023A and 023B may proceed as two implementation lanes",
            "Task 023C waits for both",
            "passed all sixteen acceptance tests",
            "Task 024 still requires its own complete accepted contract",
            "UI-architecture milestone is now eligible to begin as a separate planning lane",
            "Staging, commit, push",
        ),
    )

    task24_status = _leading_status(documents.get(TASK_024, "")) or ""
    for fragment in (
        "accepted by the user and completed under the resumed overnight Tasks 024-026 goal",
        "passed all fifteen revised acceptance tests",
    ):
        if fragment not in task24_status:
            diagnostics.append(
                _diagnostic(
                    "TASK_024_CONTRACT_INVALID",
                    TASK_024,
                    f"Task 024 contract status must contain: {fragment}",
                )
            )
    _require_phrases(
        diagnostics,
        code="TASK_024_CONTRACT_INVALID",
        document=TASK_024,
        scope=documents.get(TASK_024, ""),
        phrases=(
            "primary candidate reference for Schuss catalog curation",
            "immutable provenance, lineage, and gap evidence",
            "668 `.axo` files, 835 normal definitions, 666 canonical base references, and 19 `.axs` compounds",
            "Twenty reviewed family records",
            "schuss-record-set-000016@1",
            "schuss-record-set-000015@1",
            "schuss-current-ksoloti-corpus-000001@1",
            "schuss-core-selection-000002@1",
            "exactly the eight contract references",
            "not the presumed product-review backlog",
            "Levels 3-8 remain `not-run`",
            "passed all fifteen revised acceptance tests",
            "Staging, commit, push, release",
        ),
    )

    task25_status = _leading_status(documents.get(TASK_025, "")) or ""
    for fragment in (
        "accepted revised contract and completed under the resumed overnight goal on 2026-08-17",
        "All fifteen revised acceptance tests passed",
    ):
        if fragment not in task25_status:
            diagnostics.append(
                _diagnostic(
                    "TASK_025_CONTRACT_INVALID",
                    TASK_025,
                    f"Task 025 contract status must contain: {fragment}",
                )
            )
    _require_phrases(
        diagnostics,
        code="TASK_025_CONTRACT_INVALID",
        document=TASK_025,
        scope=documents.get(TASK_025, ""),
        phrases=(
            "schuss-core-selection-000002@1",
            "schuss-record-set-000016@1",
            "schuss-record-set-000017@1",
            "schuss-implementation-000090",
            "schuss-implementation-000095",
            "Two fresh roots",
            "Levels 3-8 remain `not-run`",
            "staging, commit, push",
        ),
    )

    task26_status = _leading_status(documents.get(TASK_026, "")) or ""
    for fragment in (
        "accepted and complete",
        "Child 026A established the reverb-free level-5 executable profile",
        "Child 026B completed the authoring operations",
    ):
        if fragment not in task26_status:
            diagnostics.append(
                _diagnostic(
                    "TASK_026_CONTRACT_INVALID",
                    TASK_026,
                    f"Task 026 contract status must contain: {fragment}",
                )
            )
    _require_phrases(
        diagnostics,
        code="TASK_026_CONTRACT_INVALID",
        document=TASK_026,
        scope=documents.get(TASK_026, ""),
        phrases=(
            "## Goal and why it exists",
            "## In scope",
            "## Out of scope",
            "## Inputs and deliverables",
            "## Acceptance tests",
            "## Decisions Task 026 may make",
            "## Decisions Task 026 must not make",
            "identity-independent semantic profile",
            "schuss-record-set-000019@1",
            "no blank or invalid graph revision is ever persisted",
            "levels 6-8 remain `not-run`",
            "staging, commit, push",
        ),
    )

    task27_status = _leading_status(documents.get(TASK_027, "")) or ""
    for fragment in (
        "accepted and complete on 2026-08-17",
        "All fifteen acceptance tests passed",
        "catalog structural/provenance boundary",
    ):
        if fragment not in task27_status:
            diagnostics.append(
                _diagnostic(
                    "TASK_027_CONTRACT_INVALID",
                    TASK_027,
                    f"Task 027 contract status must contain: {fragment}",
                )
            )
    _require_phrases(
        diagnostics,
        code="TASK_027_CONTRACT_INVALID",
        document=TASK_027,
        scope=documents.get(TASK_027, ""),
        phrases=(
            "## Goal and why it exists",
            "## In scope",
            "## Out of scope",
            "## Inputs and deliverables",
            "## Acceptance tests",
            "## Decisions Task 027 may make",
            "## Decisions Task 027 must not make",
            "schuss-record-set-000020@1",
            "schuss-implementation-000096@1",
            "mutable-instruments-derived",
            "sixty reviewed catalog families",
            "levels 3-8 are `not-run`",
            "staging, commit, push",
        ),
    )

    task28_status = _leading_status(documents.get(TASK_028, "")) or ""
    for fragment in (
        "accepted and complete on 2026-08-17",
        "All fifteen acceptance tests pass",
        "exact local selection and normalized backend-lowering boundary",
    ):
        if fragment not in task28_status:
            diagnostics.append(
                _diagnostic(
                    "TASK_028_CONTRACT_INVALID",
                    TASK_028,
                    f"Task 028 contract status must contain: {fragment}",
                )
            )
    _require_phrases(
        diagnostics,
        code="TASK_028_CONTRACT_INVALID",
        document=TASK_028,
        scope=documents.get(TASK_028, ""),
        phrases=(
            "## Goal and why it exists", "## In scope", "## Out of scope",
            "## Inputs and deliverables", "## Acceptance tests",
            "## Decisions Task 028 may make", "## Decisions Task 028 must not make",
            "schuss-record-set-000021@1", "exactly twenty", "fifteen safe promotions",
            "levels 1-3 as `passed`", "levels 4-8 remain `not-run`",
            "Rings reverb", "000094", "staging, commit, or push",
        ),
    )

    status_rules = (
        "This document is the single authority for Schuss's current development state.",
        "Task 018 is complete for exact record set `schuss-record-set-000012@1`.",
        "No product task is automatically active after this completion.",
        "reaches evidence level 5 through the exact mapped handler",
        "levels 6-8 remain `not-run`",
        "Tasks 019 and 020 are deferred and not automatically activated",
        "Task 021 is complete for exact record set `schuss-record-set-000013@1`.",
        "dedicated DMA-visible command buffer",
        "volatile-RAM connected-device observation at level 6",
        "Real-time/resource and audible evidence levels 7-8 remain `not-run`",
        "Task 022 Phase A is complete for exact artifact successor record set `schuss-record-set-000014@1`.",
        "Exactly one approved diagnostic volatile-RAM upload was performed",
        "The retained result is `POT_EVENT_FOCUS_UNSTABLE`",
        "promotion stopped before a complete sweep and level 6 was not earned",
        "Approval gate 2 is closed",
        "ADR 0014 accepts the application-spine sequence",
        "Task 023 was explicitly accepted and completed on 2026-08-16",
        "`schuss-record-set-000015@1`",
        "`application.describe` operation inventories fourteen accepted public operations",
        "The read-only Task 023 smoke passes in two copied fresh roots",
        "backend execution, project writes, and hardware access were `not-run`",
        "Task 024 is accepted complete for exact record set",
        "`schuss-record-set-000016@1`",
        "four configured source libraries",
        "668 `.axo` files, 835 normal definitions, 666 canonical base references",
        "all 3,602 frozen resolved observations one factual disposition",
        "not readiness, quality, or a product backlog",
        "eleven retain, seven revise, and two reconsider",
        "29 Task 024 implementation records",
        "`schuss-core-selection-000002@1`",
        "Task 024 reproduced levels 1-2 only",
        "Task 025 is accepted complete for exact record set",
        "`schuss-record-set-000017@1`",
        "allocates 32,768 bytes while its exact",
        "engine clears 65,536 bytes",
        "complete-graph level 2 fails",
        "Two fresh roots reproduced identical record-set",
        "Task 026 is accepted complete for exact schema successor record set",
        "`schuss-record-set-000019@1`",
        "identity-independent seven-node, reverb-free semantic profile",
        "The Task 026 application-capability successor describes eighteen operations",
        "historical fourteen-operation Task 023 description remains byte-exact",
        "Two fresh workspaces reproduced byte-identical history, plan, generated source, and ELF",
        "Reverb is still explicitly unsupported",
        "Task 027 is accepted complete for exact record set `schuss-record-set-000020@1`",
        "does not change any of the sixty reviewed families or thirteen functional categories",
        "The review retains seventy-two exact source entries",
        "Six catalogued implementations across five ordinary families carry the tag",
        "The other sixteen extended objects remain inventory-only",
        "Task 028 is accepted complete for exact record set `schuss-record-set-000021@1`",
        "exactly fifteen independently selectable native bindings",
        "counted total of twenty",
        "passes levels 1-3 only",
        "twenty source implementations back counted promotions and sixty-three remain outside this bounded palette",
        "physical resonator 000096 remains catalogued-only",
        "No numbered implementation task is automatically active after Task 028 completion",
        "UI architecture planning is now explicitly authorized by ADR 0014",
        "UI implementation remains separately gated",
    )
    _require_phrases(
        diagnostics,
        code="CURRENT_STATUS_DRIFT",
        document=STATUS,
        scope=documents.get(STATUS, ""),
        phrases=status_rules,
    )

    _require_phrases(
        diagnostics,
        code="APPLICATION_SPINE_PLAN_INVALID",
        document=APPLICATION_SPINE_PLAN,
        scope=documents.get(APPLICATION_SPINE_PLAN, ""),
        phrases=(
            "Status: accepted planning authority under ADR 0014 and amended by ADR 0015 for Task 027 only.",
            "Task 023: CLI v2 and application-surface consolidation",
            "Task 024: Current-Ksoloti-first catalog structure and deterministic lineage",
            "Task 025: Direct-compiler core-library tranche",
            "Task 026: Complete authoring operations and CLI workflow",
            "Task 027: Mutable-related catalog provenance and extended-source review",
            "Task 028: Twenty-item direct selectable palette",
            "UI architecture is explicitly authorized now.",
            "UI implementation remains separately gated.",
            "`023A`, `023B`, and `023C`",
            "The default concurrency ceiling is two implementation lanes plus one read-only/design lane.",
            "operation and schema version allocation",
            "stable semantic IDs, record-set revisions, and manifest publication",
            "This plan did not itself start Task 023 or create any numbered task contract",
            "Tasks 023-028 are accepted complete",
            "Task 028's bounded twenty-item palette is now complete",
            "no numbered implementation task is active",
            "sessions/jobs/diagnostics outcome is deferred without a replacement task number",
            "Task 026B then completed exact project-owned creation/versioning",
            "Tasks 019 and 020 remain deferred.",
        ),
    )

    history_rules = (
        "Completed task contracts are not live scheduling authority",
        "Git retains their exact bytes",
        "no later product task is automatically active.",
    )
    _require_phrases(
        diagnostics,
        code="HISTORY_POLICY_DRIFT",
        document=HISTORY,
        scope=documents.get(HISTORY, ""),
        phrases=history_rules,
    )

    ui_scopes = {
        STATUS: documents.get(STATUS, ""),
        TASK_012B: documents.get(TASK_012B, ""),
        ADR_0010: _section(documents.get(ADR_0010, ""), "## Decision"),
    }
    for document, scope in ui_scopes.items():
        normalized = _normalized(scope).lower()
        if any(
            phrase not in normalized
            for phrase in ("object drawer", "transparent graph canvas", "unnumbered", "explicit")
        ) or "authoriz" not in normalized:
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
    for number in range(13, 29):
        label = str(number)
        if len(roadmap_rows.get(label, [])) != 1:
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
        "16": "complete",
        "17": "complete",
        "18": "complete; mapped local level 5",
        "19": "deferred; not scheduled",
        "20": "deferred; not scheduled",
        "21": "complete; corrected level 6",
        "22": "stopped; failed before level 6",
        "23": "complete; shared capability surface and cli v2",
        "24": "complete; 685 current first-party candidates, frozen lineage coverage, and 60-family level-2 catalog",
        "25": "complete fail-closed partial tranche",
        "26": "complete; project-owned create/edit/history/revert and two-root reverb-free authored elf reach local level 5",
        "27": "complete; 72 exact source entries, 60 families preserved, one catalogued-only implementation, levels 1-2",
        "28": "complete; fifteen additions lower locally at levels 1-3, no build",
    }
    for label, expected in expected_roadmap_status.items():
        rows = roadmap_rows.get(label, [])
        if len(rows) == 1 and expected not in rows[0][2].lower():
            diagnostics.append(
                _diagnostic(
                    "BACKBONE_SEQUENCE_STATUS_DRIFT",
                    ROADMAP,
                    f"Task {int(label):03d} roadmap status must contain: {expected}",
                )
            )
    deferred_ui = roadmap_rows.get("Deferred UI", [])
    if (
        len(deferred_ui) != 1
        or "unnumbered" not in deferred_ui[0][2].lower()
        or "architecture authorized" not in deferred_ui[0][2].lower()
        or "implementation separately gated" not in deferred_ui[0][2].lower()
    ):
        diagnostics.append(
            _diagnostic(
                "UI_MILESTONE_NUMBERED",
                ROADMAP,
                "roadmap must contain one unnumbered architecture-authorized, implementation-gated Deferred UI row",
            )
        )

    _require_phrases(
        diagnostics,
        code="ROADMAP_PROMOTION_GATE_DRIFT",
        document=ROADMAP,
        scope=documents.get(ROADMAP, ""),
        phrases=(
            "Executable promotion",
            "reach evidence level 5",
            "Tasks 019 and 020 remain deferred.",
            "Tasks 023-028 are accepted complete.",
            "Task 026 consumes the independently accepted reverb-free seven-node executable profile",
            "UI-architecture milestone is eligible but not started",
            "No numbered implementation lane is currently planned",
            "sessions/jobs/diagnostics outcome is deferred without a replacement number",
            "two implementation lanes plus one",
        ),
    )
    _require_phrases(
        diagnostics,
        code="ADR_0013_CORRECTIVE_GATE_DRIFT",
        document=ADR_0013,
        scope=_section(documents.get(ADR_0013, ""), "## Decision"),
        phrases=(
            "Task 021 is a separately authorized corrective successor",
            "preserves every Task 018 v1 byte",
            "dedicated two-byte command buffer in `.sram2`",
            "separate exact evidence claim",
            "does not activate Task 019, Task 020, or UI work",
        ),
    )
    _require_phrases(
        diagnostics,
        code="ADR_0014_APPLICATION_SPINE_DRIFT",
        document=ADR_0014,
        scope=_section(documents.get(ADR_0014, ""), "## Decision"),
        phrases=(
            "Task 023: CLI v2 and application-surface consolidation",
            "Task 028: second catalog/compiler tranche and transparent compounds",
            "Task 023 is the next planned task",
            "UI architecture is explicitly authorized as an unnumbered planning milestone",
            "UI implementation remains separately gated",
            "does not revive retired Task 012B",
            "`023A`, `023B`, and `023C`",
            "two implementation lanes plus one read-only or design lane",
            "Tasks 019 and 020 remain deferred",
        ),
    )
    _require_phrases(
        diagnostics,
        code="ADR_0015_TASK027_RETARGET_DRIFT",
        document=ADR_0015,
        scope=_section(documents.get(ADR_0015, ""), "## Decision"),
        phrases=(
            "Task 027 is retargeted to Mutable-related catalog provenance",
            "sessions, jobs, and diagnostics outcome is deferred",
            "preserve the sixty reviewed catalog families",
            "additive provenance tag",
            "Ambient working-tree changes are excluded",
        ),
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

    _require_phrases(
        diagnostics,
        code="ADR_0011_SEMANTICS_DRIFT",
        document=ADR_0011,
        scope=_section(documents.get(ADR_0011, ""), "## Decision"),
        phrases=(
            "legacy-equivalent semantics",
            "may not silently substitute Schuss-native behavior",
            "may never fall back invisibly",
            "levels 6-8 are independent and remain `not-run`",
        ),
    )
    _require_phrases(
        diagnostics,
        code="ADR_0012_PROMOTION_GATE_DRIFT",
        document=ADR_0012,
        scope=_section(documents.get(ADR_0012, ""), "## Decision"),
        phrases=(
            "at least one exact mapped Gills reference instrument must reach evidence level 5",
            "do not satisfy this executable promotion gate",
            "does not automatically activate Task 019, Task 020, or UI work",
        ),
    )

    alias_scopes = {
        README: documents.get(README, ""),
        PROJECT_CONTEXT: documents.get(PROJECT_CONTEXT, ""),
        STATUS: documents.get(STATUS, ""),
        ROADMAP: documents.get(ROADMAP, ""),
        DECISIONS_INDEX: documents.get(DECISIONS_INDEX, ""),
        ADR_0010: _section(documents.get(ADR_0010, ""), "## Decision"),
        ADR_0011: documents.get(ADR_0011, ""),
        ADR_0012: documents.get(ADR_0012, ""),
        ADR_0013: documents.get(ADR_0013, ""),
        ADR_0014: documents.get(ADR_0014, ""),
        ADR_0015: documents.get(ADR_0015, ""),
        APPLICATION_SPINE_PLAN: documents.get(APPLICATION_SPINE_PLAN, ""),
        TASK_012B: documents.get(TASK_012B, ""),
        TASK_018: documents.get(TASK_018, ""),
        TASK_021: documents.get(TASK_021, ""),
        TASK_022: documents.get(TASK_022, ""),
        TASK_023: documents.get(TASK_023, ""),
        TASK_024: documents.get(TASK_024, ""),
        TASK_025: documents.get(TASK_025, ""),
        TASK_026: documents.get(TASK_026, ""),
        TASK_027: documents.get(TASK_027, ""),
        TASK_028: documents.get(TASK_028, ""),
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

    actual_task_filenames = set(task_filenames)
    if actual_task_filenames != EXPECTED_TASK_FILENAMES:
        missing = sorted(EXPECTED_TASK_FILENAMES - actual_task_filenames)
        unexpected = sorted(actual_task_filenames - EXPECTED_TASK_FILENAMES)
        diagnostics.append(
            _diagnostic(
                "TASK_ARCHIVE_POLICY_VIOLATION",
                "docs/tasks",
                f"missing={missing}; unexpected={unexpected}",
            )
        )

    diagnostics.sort(key=lambda item: (item["code"], item["document"], item["detail"]))
    return {
        "active_product_task": "none-task028-complete-next-task-requires-contract",
        "active_evidence_task": "022-failed-diagnostic-promotion-stopped",
        "active_task_sequence": list(ACTIVE_SEQUENCE),
        "authoritative_decisions": [
            "ADR 0010", "ADR 0011", "ADR 0012", "ADR 0013", "ADR 0014", "ADR 0015"
        ],
        "checked_documents": len([path for path in DOCUMENT_PATHS if path in documents]),
        "current_status_source": STATUS,
        "diagnostics": diagnostics,
        "historical_context_policy": "completed-task-contracts-indexed-in-history-and-git",
        "next_planned_task": "none-task028-complete",
        "planned_task_sequence": list(PLANNED_SEQUENCE),
        "promotion_gate": "task028-complete-level-3-reverb-unsupported",
        "schema_version": "backbone-governance-summary-v17",
        "status": "valid" if not diagnostics else "invalid",
        "task_statuses": {
            "012B": "retired",
            "013": "complete",
            "014": "complete",
            "015": "complete",
            "016": "complete-legacy-equivalent-level-5",
            "017": "complete-level-2",
            "018": "complete-mapped-local-level-5",
            "019": "deferred-not-scheduled",
            "020": "deferred-not-scheduled",
            "021": "complete-corrected-connected-level-6",
            "022": "failed-connected-diagnostic-level-6-not-earned",
            "023": "complete-application-surface-cli-v2",
            "024": "complete-current-ksoloti-catalog-lineage-level-2",
            "025": "complete-fail-closed-partial-level-2",
            "026": "complete-reverb-free-authoring-level-5",
            "027": "complete-mutable-catalog-provenance-level-2",
            "028": "complete-twenty-item-direct-palette-level-3",
        },
        "ui_milestone_status": "unnumbered-architecture-eligible-not-started-implementation-gated",
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
        task_filenames = sorted(
            path.name for path in task_root.iterdir() if path.is_file() and path.suffix == ".md"
        )
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
