#!/usr/bin/env python3
"""Validate the Task 033 Phase 4 integration and follow-up handoff."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "tools/contracts") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools/contracts"))

from tools.contracts import validate_task033_phase3  # noqa: E402


TASK_CONTRACT = Path(
    "docs/tasks/033-object-collections-and-native-provider-architecture.md"
)
NEXT_TRANCHE = Path("docs/tasks/033-NEXT-TRANCHE.md")
UI_FOLLOWUP = Path("docs/tasks/033-UI-FOLLOWUP.md")
RESULTS = Path("docs/tasks/033-RESULTS.md")
GAPS = Path("docs/tasks/033-GAPS.md")
TASK040 = Path("docs/tasks/040-cinderwheel-canonical-vertical-slice.md")
STATE = Path("docs/governance/current-state.json")
MUTABLE_MANIFEST = Path(
    "catalog/reviews/task033-mutable-provider-audit-v1/manifest.json"
)
JUCE_MANIFEST = Path("catalog/reviews/task033-juce-dsp-audit-v1/manifest.json")

PROTOTYPE_AUTHORITIES = {
    Path("research/prototypes/cinderwheel/prototype-index.json"):
        "a15365efdbd731137a2d4b6d715114b920ecdf787086ba096b60b20dd341ab80",
    Path("research/prototypes/cinderwheel/PROMOTION_NEEDS.json"):
        "9abd9c3464885ab07541dfcdf6c65a5a8c19ee282d3299deb654762bce6e01fc",
    Path("research/prototypes/cinderwheel/dsp-topology.json"):
        "dff93dc5025be7280d2c565f9c388572acbe9707b13d967413cf471f21dc0b78",
    Path(
        "research/prototypes/cinderwheel/fixtures/launch-control-3-test-map-v0.json"
    ): "d5df5f569bf37ed0dbd3e356a9c2f42ac01ed8364c2dc2bc6b07da2243e390f8",
}


def _json(root: Path, path: Path) -> dict[str, Any]:
    value = json.loads((root / path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"TASK033_PHASE4_JSON_INVALID: {path.as_posix()}")
    return value


def _text(root: Path, path: Path) -> str:
    return (root / path).read_text(encoding="utf-8")


def _require(text: str, path: Path, phrases: tuple[str, ...]) -> None:
    normalized = " ".join(text.split())
    missing = [phrase for phrase in phrases if " ".join(phrase.split()) not in normalized]
    if missing:
        raise ValueError(
            f"TASK033_PHASE4_DOCUMENT_INCOMPLETE: {path.as_posix()}: {missing}"
        )


def validate(repository_root: Path = ROOT) -> dict[str, Any]:
    root = repository_root.resolve()
    phase3 = validate_task033_phase3.validate(root)
    if phase3["status"] != "valid":
        raise ValueError("TASK033_PHASE4_PHASE3_INVALID")

    mutable = _json(root, MUTABLE_MANIFEST)
    juce = _json(root, JUCE_MANIFEST)
    if mutable.get("counts", {}).get("total") != 56:
        raise ValueError("TASK033_PHASE4_MUTABLE_AUDIT_COUNT_CHANGED")
    if juce.get("counts", {}).get("total") != 39:
        raise ValueError("TASK033_PHASE4_JUCE_AUDIT_COUNT_CHANGED")
    if juce.get("counts", {}).get("recommendations") != {
        "defer": 19,
        "later-juce-host-provider": 8,
        "native-schuss-algorithm": 12,
    }:
        raise ValueError("TASK033_PHASE4_JUCE_DISPOSITION_CHANGED")

    next_tranche = _text(root, NEXT_TRANCHE)
    _require(
        next_tranche,
        NEXT_TRANCHE,
        (
            "Task 040, the Cinderwheel canonical\nvertical slice",
            "The tranche is intentionally one task wide.",
            "No Mutable-derived implementation and no JUCE `juce_dsp` class is selected",
            "permits a shortfall instead of inventing",
            "allocates no semantic identity and activates no task",
        ),
    )
    if next_tranche.count("| 1 | Cinderwheel canonical vertical slice |") != 1:
        raise ValueError("TASK033_PHASE4_TRANCHE_SELECTION_AMBIGUOUS")

    ui = _text(root, UI_FOLLOWUP)
    _require(
        ui,
        UI_FOLLOWUP,
        (
            "`collections.inspect`",
            "`implementation.availability.inspect`",
            "Phase 2\ndefines no mutation operation.",
            "Avoid a global “compatible” badge",
            "must not decide identity, selection priority,\ncompatibility",
        ),
    )

    task040 = _text(root, TASK040)
    task040_proposed = "Status: proposed and not activated." in task040
    task040_phase1_ready = (
        "Status: Phase 1 explicitly authorized and review-ready" in task040
    )
    if not (task040_proposed or task040_phase1_ready):
        raise ValueError("TASK040_STATUS_INVALID")
    _require(
        task040,
        TASK040,
        (
            "The lane is **new-design**.",
            "## Working artifact and evidence ceiling",
            "## In scope after activation",
            "## Out of scope",
            "## Inputs and deliverables",
            "## Acceptance tests",
            "## Decisions Task 040 may make after activation",
            "## Decisions Task 040 must not make",
        ),
    )
    if task040_proposed:
        _require(
            task040,
            TASK040,
            (
                "No stable ID, record-set\nsuccessor, provider successor, operation, build, device action, commit, or push",
            ),
        )
    else:
        _require(
            task040,
            TASK040,
            (
                "contracts/task040/phase1/allocation.json",
                "Phase 2\nis not activated",
                "schuss-record-set-000033@1",
            ),
        )
    for path, expected in PROTOTYPE_AUTHORITIES.items():
        actual = hashlib.sha256((root / path).read_bytes()).hexdigest()
        if actual != expected or expected not in task040:
            raise ValueError(
                f"TASK040_PROTOTYPE_AUTHORITY_CHANGED: {path.as_posix()}"
            )

    _require(
        _text(root, RESULTS),
        RESULTS,
        (
            "Status: complete and published at commit `0bf22b6`.",
            "runtime_v1.cpp` byte-for-byte",
        ),
    )
    _require(
        _text(root, GAPS),
        GAPS,
        (
            "Cinderwheel is noncanonical",
            "Performance-control execution",
            "Physical/device evidence",
            "Real-time/listening/release",
        ),
    )

    integration_documents = {
        Path("docs/ARCHITECTURE.md"): "native-provider-registry-v1.json",
        Path("docs/SEMANTIC_CATALOG.md"): "Source-neutral collections and target availability",
        Path("docs/COMPILER_FRONT_HALF.md"): "canonical native\nprovider manifest",
        Path("docs/TARGET_BACKEND_BUILD_CONTRACTS.md"): "Implementation-provider and runtime-descriptor boundary",
        Path("docs/OPERATION_CONTRACTS.md"): "Collection and implementation-availability inspection",
        Path("docs/CATALOG_OPERATIONS.md"): "implementation.availability.inspect",
    }
    for path, phrase in integration_documents.items():
        if phrase not in _text(root, path):
            raise ValueError(
                f"TASK033_PHASE4_INTEGRATION_DOCUMENT_STALE: {path.as_posix()}"
            )

    state = _json(root, STATE)
    active = state.get("active_task")
    next_candidate = state.get("next_candidate")
    milestones = state.get("recent_completed_milestones")
    completed = {
        (item.get("task_id"), item.get("phase"), item.get("status"), item.get("commit"))
        for item in milestones
        if isinstance(item, dict)
    } if isinstance(milestones, list) else set()
    required_completion = {
        ("033", 3, "complete-published", "0bf22b6"),
        ("033", 4, "complete-published", "0bf22b6"),
    }
    if not required_completion.issubset(completed):
        raise ValueError("TASK033_PHASE4_GOVERNANCE_COMPLETION_INVALID")
    if isinstance(active, dict) and active.get("task_id") == "033":
        raise ValueError("TASK033_PHASE4_GOVERNANCE_STILL_ACTIVE")
    if next_candidate not in (
        None,
        {"task_id": "040", "phase": None, "status": "not-activated"},
    ):
        raise ValueError("TASK033_PHASE4_GOVERNANCE_NEXT_STATE_INVALID")

    return {
        "schema_version": "task033-phase4-validation-summary-v1",
        "status": "valid",
        "phase3_status": phase3["status"],
        "factory_count": phase3["factory_count"],
        "mutable_audit_count": 56,
        "juce_audit_count": 39,
        "selected_tranche_count": 1,
        "selected_next_task": "040",
        "selected_lane": "new-design",
        "completion_commit": "0bf22b6",
        "ui_implemented": False,
        "semantic_record_provider_or_operation_allocated_in_phase4": False,
        "device_realtime_listening_or_publication_performed": False,
        "phase3_runtime_bytes_preserved": phase3[
            "runtime_v1_cpp_byte_preserved"
        ],
    }


def main() -> int:
    try:
        result = validate()
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
