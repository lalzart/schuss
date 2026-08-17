from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def require(path: str, fragments: tuple[str, ...]) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    missing = [value for value in fragments if value not in text]
    if missing:
        raise ValueError(f"{path}: missing contract fragments: {missing}")


def main() -> int:
    require(
        "contracts/task026/preflight-boundary.md",
        (
            "Status: accepted decision",
            "seven-node profile",
            "Rings-derived reverb",
            "deterministically unsupported",
            "child work package 026A",
        ),
    )
    require(
        "contracts/task026/executable-profile-prerequisite.md",
        (
            "Status: complete.",
            "## Goal and reason",
            "## In scope",
            "## Out of scope",
            "## Inputs and deliverables",
            "## Acceptance tests",
            "## Validation cadence",
            "## Decisions 026A may make",
            "## Decisions 026A must not make",
            "schuss-record-set-000017@1",
            "Reverb is not a profile member.",
            "Levels 6-8 remain `not-run`",
        ),
    )
    require(
        "docs/tasks/026-complete-authoring-operations-and-cli-workflow.md",
        (
            "Status: accepted and complete.",
            "Child 026A",
            "Child 026B",
            "no blank or invalid graph revision is ever persisted",
            "## Goal and why it exists",
            "## In scope",
            "## Out of scope",
            "## Inputs and deliverables",
            "## Acceptance tests",
            "## Validation cadence",
            "## Decisions Task 026 may make",
            "## Decisions Task 026 must not make",
        ),
    )
    print("Task 026 contract: valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
