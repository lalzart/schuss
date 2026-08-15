#!/usr/bin/env python3
"""Read-only Task 012A project/workspace validator."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.schuss_core.project_service import (
    LOCK_LOCATOR,
    RECOVERY_LOCATOR,
    ProjectService,
)


DEFAULT_FIXTURE = ROOT / "fixtures/task012a/minimal-project"


def _tree_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def validate(workspace: Path) -> dict[str, object]:
    workspace = workspace.absolute()
    before = _tree_hashes(workspace)
    if (workspace / LOCK_LOCATOR).exists() or (workspace / RECOVERY_LOCATOR).exists():
        raise ValueError(
            "read-only validation refuses a workspace requiring lock/recovery mutation"
        )
    service = ProjectService(workspace)
    loaded = service.load(recover=False)
    after = _tree_hashes(workspace)
    if before != after:
        raise ValueError("read-only validation changed workspace bytes")
    schema_hashes = {
        name: hashlib.sha256(
            (ROOT / "schemas" / filename).read_bytes()
        ).hexdigest()
        for name, filename in (
            ("operation_request_v3", "operation-request-v3.schema.json"),
            ("operation_result_v3", "operation-result-v3.schema.json"),
            ("project_v0", "project-v0.schema.json"),
            ("project_write_plan_v0", "project-write-plan-v0.schema.json"),
            ("workspace_head_v0", "workspace-head-v0.schema.json"),
            ("workspace_lock_v0", "workspace-lock-v0.schema.json"),
            ("workspace_recovery_v0", "workspace-recovery-v0.schema.json"),
        )
    }
    return {
        "schema_version": "task012a-validation-summary-v0",
        "status": "valid",
        "project_reference": {
            "project_id": loaded.manifest["project_id"],
            "revision": loaded.manifest["revision"],
            "content_hash": loaded.manifest["content_hash"],
        },
        "base_record_set_reference": loaded.context.record_set_reference,
        "primary_graph_reference": loaded.manifest["primary_graph_reference"],
        "governed_file_count": loaded.validation["governed_file_count"],
        "owned_record_count": loaded.validation["owned_record_count"],
        "schema_byte_sha256": schema_hashes,
        "workspace_byte_sha256": before,
        "read_only_equality": True,
        "evidence_levels": {
            "structural": "passed",
            "persistent_authoring": "passed",
            "backend_lowering": "not-run",
            "artifact_generation": "not-run",
            "arm_compile_link": "not-run",
            "connected_device": "not-run",
            "real_time": "not-run",
            "audible": "not-run",
        },
    }


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if len(arguments) > 1:
        raise SystemExit("usage: validate_task012a.py [WORKSPACE]")
    workspace = Path(arguments[0]) if arguments else DEFAULT_FIXTURE
    print(json.dumps(validate(workspace), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
