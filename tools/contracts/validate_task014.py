#!/usr/bin/env python3
"""Read-only validation for the completed Task 014 execution boundary."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools/contracts"
for value in (ROOT, TOOLS):
    if str(value) not in sys.path:
        sys.path.insert(0, str(value))

from packages.schuss_core.build_execution import descriptor_content_hash
from packages.schuss_core.control_plane import dispatch_operation, load_repository_context
import generate_task014_record_set as generator
import record_set_rules
import validator_core as core


RECORD_SET = ROOT / "contracts/record-sets/task014-build-execution-v1.json"
EVIDENCE = ROOT / "evidence/task014-completion-v1/validation-summary.json"


def _adapter():
    path = ROOT / "legacy/ksoloti-bridge/task011c_adapter.py"
    specification = importlib.util.spec_from_file_location("task014_validator_adapter", path)
    if specification is None or specification.loader is None:
        raise ValueError("Task 014 adapter cannot be loaded")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def validate() -> dict[str, object]:
    if RECORD_SET.read_bytes() != generator.generated_bytes():
        raise ValueError("Task 014 record set is stale")
    loaded = record_set_rules.load_record_set(ROOT, RECORD_SET)
    context = load_repository_context(record_set_path=RECORD_SET)
    descriptor = _adapter().descriptor()
    descriptor_schema = loaded.schemas["build-handler-descriptor-v0"]
    errors = core.schema_errors(descriptor, descriptor_schema, descriptor_schema)
    if errors or descriptor["content_hash"] != descriptor_content_hash(descriptor):
        raise ValueError("Task 014 handler descriptor is invalid: " + "; ".join(errors))
    if descriptor["content_hash"] != core.record_content_hash(descriptor, descriptor_schema):
        raise ValueError("Task 014 handler uses a nonstandard content hash")
    request = next(
        item for item in context.records["request"]
        if item["build_request_id"] == "schuss-build-request-000002"
        and item["revision"] == 2
    )
    reference = {key: request[key] for key in ("build_request_id", "revision", "content_hash")}
    plan = dispatch_operation({
        "schema_version": "schuss-operation-request-v4",
        "canonical_profile": "schuss-canonical-json-v1",
        "operation": "build.plan",
        "payload": {"build_request_reference": reference},
    }, context)
    if plan["status"] != "success" or any(item["status"] != "success" for item in plan["value"]["stages"]):
        raise ValueError("Task 014 exact input no longer plans successfully")
    evidence = core.load_json(EVIDENCE)
    expected_artifacts = {
        "arm-object": "c059b2ee38be7dbca6828dc06b1d5890bb0600ab606dd59786fb1dccbd308c1b",
        "generated-cpp": "7877897b3112dcbb7ee1239f3187f535d6113875cacbb49c76bd30a0321bcfd3",
        "legacy-boundary-patch": "84f875018cbbc859eecf5627ffab5c50ade66a369203d3a79fcb794dcb86865a",
        "link-map": "30357b886ca808d38a61b2ad624d3086e66babb0df169caa5af36eda8c15531f",
        "resolution-plan": "b9cb83cfb05ae29d9f0f37e5e04c6df6a17d1ce1cbe21395ffa31f0be4fea261",
        "source-map": "8992679f5d12c5f1d46d1ed0a30220b2ee8dd3511240c7bcaab80d3a95837d7c",
        "target-executable": "d04cc20d5dc0cfe195ce38ee850857c0b8af8675f7616898f50dd6e77372db2a",
    }
    actual_artifacts = {item["artifact_kind"]: item["byte_sha256"] for item in evidence["artifacts"]}
    if actual_artifacts != expected_artifacts:
        raise ValueError("Task 014 retained artifact identities differ")
    if (
        evidence["status"] != "valid"
        or evidence["record_set_reference"] != loaded.reference
        or evidence["handler_reference"]["content_hash"] != descriptor["content_hash"]
        or evidence["fresh_root_runs"] != 2
        or not evidence["canonical_results_equal"]
        or evidence["device_actions_performed"]
        or evidence["stage_commit_push_performed"]
        or [item["status"] for item in evidence["evidence_levels"]] != ["passed"] * 5 + ["not-run"] * 3
    ):
        raise ValueError("Task 014 retained completion evidence is inconsistent")
    for path in (ROOT / "packages/schuss_core/compiler_front_half.py", ROOT / "packages/schuss_core/build_execution.py"):
        text = path.read_text(encoding="utf-8")
        if "task011c_adapter" in text or "task011c_backend" in text or "Ksoloti Local.app" in text:
            raise ValueError(f"core compiler/execution module imports the legacy adapter: {path.name}")
    return {
        "schema_version": "task014-validator-result-v1",
        "status": "valid",
        "record_set_reference": loaded.reference,
        "manifest_byte_sha256": hashlib.sha256(RECORD_SET.read_bytes()).hexdigest(),
        "handler_reference": evidence["handler_reference"],
        "plan_sha256": evidence["plan_sha256"],
        "artifact_count": len(expected_artifacts),
        "focused_test_count": 14,
        "evidence_levels": evidence["evidence_levels"],
    }


def main() -> int:
    try:
        result = validate()
    except (OSError, ValueError) as exc:
        print(f"Task 014 validation failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
