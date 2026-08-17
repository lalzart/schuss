from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/contracts")]

from packages.schuss_core.build_execution import ExecutionService, execute_build, handler_reference  # noqa: E402
from packages.schuss_core.compiler_front_half import CompilationContext  # noqa: E402
from packages.schuss_core.control_plane import load_repository_context  # noqa: E402
from packages.schuss_core.effects_profile_backend import registration  # noqa: E402

import validator_core as core  # noqa: E402


RECORD_SET = ROOT / "contracts/record-sets/task026a-executable-profile-v1.json"
EVIDENCE_ROOT = ROOT / "evidence/task026a-executable-profile-v1"


def exact(values, field: str, stable_id: str) -> dict:
    matches = [item for item in values if item[field] == stable_id]
    if len(matches) != 1:
        raise ValueError(f"{stable_id} does not resolve exactly")
    return matches[0]


def digest(value: object) -> str:
    return hashlib.sha256(core.canonical_json(value).encode("utf-8")).hexdigest()


def run_once(context, build_request: dict, ordinal: int) -> dict:
    request_reference = {key: build_request[key] for key in ("build_request_id", "revision", "content_hash")}
    compilation = CompilationContext.from_values(
        build_request_reference=request_reference,
        closure_source={"kind": "record-set", "record_set_reference": context.record_set_reference},
        records=context.records,
        schemas=context.schemas,
    )
    handler = registration()
    with tempfile.TemporaryDirectory(prefix=f"schuss-task026a-root-{ordinal}-") as temporary:
        final_root = Path(temporary) / "published"
        service = ExecutionService.from_values((handler,), final_root)
        result = execute_build(
            compilation,
            handler_reference(handler.descriptor),
            service,
            execution_intent=True,
        )
        if result["status"] != "success" or not final_root.is_dir():
            raise ValueError(f"Task 026A run {ordinal} failed: {result['diagnostics']}")
        files = {}
        for path in sorted(final_root.rglob("*")):
            if path.is_file():
                data = path.read_bytes()
                files[path.relative_to(final_root).as_posix()] = {
                    "byte_length": len(data),
                    "byte_sha256": hashlib.sha256(data).hexdigest(),
                }
        return {
            "result": result,
            "result_sha256": digest(result),
            "artifact_hashes": {
                item["artifact_kind"]: item["byte_sha256"]
                for item in result["artifacts"]
            },
            "published_files": files,
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    context = load_repository_context(record_set_path=RECORD_SET)
    request = exact(context.records["request"], "build_request_id", "schuss-build-request-000005")
    first = run_once(context, request, 1)
    second = run_once(context, request, 2)
    if first != second:
        raise ValueError("Task 026A fresh-root executions differ")
    handler = registration().descriptor
    artifacts = {
        "schema_version": "task026a-artifact-hashes-v1",
        "record_set_reference": context.record_set_reference,
        "build_request_reference": {key: request[key] for key in ("build_request_id", "revision", "content_hash")},
        "handler_reference": handler_reference(handler),
        "artifact_hashes": first["artifact_hashes"],
        "published_files": first["published_files"],
        "execution_result_sha256": first["result_sha256"],
    }
    summary = {
        "schema_version": "task026a-validation-summary-v1",
        "status": "passed",
        "fresh_output_root_runs": 2,
        "portable_operation_results_identical": True,
        "artifact_bytes_identical": True,
        "record_set_reference": context.record_set_reference,
        "build_request_reference": artifacts["build_request_reference"],
        "handler_reference": artifacts["handler_reference"],
        "artifact_hashes_sha256": digest(artifacts),
        "evidence_levels": [{"level": level, "status": "passed" if level <= 5 else "not-run"} for level in range(1, 9)],
        "java_used": False,
        "legacy_boundary_patch_used": False,
        "reverb_consumed": False,
        "device_actions_performed": False,
        "real_time_validation_performed": False,
        "audible_validation_performed": False,
        "git_publication_performed": False,
    }
    if args.write:
        EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)
        for name, value in (("artifact-hashes.json", artifacts), ("validation-summary.json", summary)):
            (EVIDENCE_ROOT / name).write_text(core.canonical_json(value) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
