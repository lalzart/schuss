from __future__ import annotations

import argparse
import copy
import hashlib
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/contracts")]

from packages.schuss_core.effects_profile_frontend import ROLE_CONTRACTS  # noqa: E402
from packages.schuss_core.gills_direct_frontend import evaluate_linear_mix_block  # noqa: E402

import validator_core as core  # noqa: E402


PARENT = ROOT / "contracts/record-sets/task025-direct-core-v1.json"
MANIFEST = ROOT / "contracts/record-sets/task026a-executable-profile-v1.json"
TASK = "contracts/task026/"
EVIDENCE = "evidence/task026a-executable-profile-v1/"


def _record(value: dict[str, Any], schema_path: str) -> dict[str, Any]:
    result = copy.deepcopy(value)
    schema = core.load_json(ROOT / schema_path)
    result["content_hash"] = "sha256:" + "0" * 64
    errors = core.schema_errors(result, schema, schema)
    if errors:
        raise ValueError(f"{schema_path}: " + "; ".join(errors))
    result["content_hash"] = core.record_content_hash(result, schema)
    return result


def _ref(record: dict[str, Any], id_field: str) -> dict[str, Any]:
    return {id_field: record[id_field], "revision": record["revision"], "content_hash": record["content_hash"]}


def _semantic_ref(record: dict[str, Any], id_field: str) -> dict[str, Any]:
    return {"input_kind": "semantic-record", "stable_id": record[id_field], "revision": record["revision"], "content_hash": record["content_hash"]}


def _goldens() -> dict[str, Any]:
    first = tuple((index - 8) * (1 << 22) for index in range(16))
    second = tuple((8 - index) * (1 << 22) for index in range(16))
    return {
        "schema_version": "task026a-semantic-goldens-v1",
        "operations": {
            "linear-mix-current-block-q27": {
                "first": list(first),
                "second": list(second),
                "zero": list(evaluate_linear_mix_block(first, second, 0)),
                "half": list(evaluate_linear_mix_block(first, second, 1 << 26)),
                "full": list(evaluate_linear_mix_block(first, second, 1 << 27)),
                "input_schedule": "both-audio-inputs-current-block",
                "control_schedule": "previous-control-cycle-latch",
            }
        },
        "limitations": [
            "Vectors prove integer mixing and the declared application schedule only.",
            "They establish no reverb, device, real-time, resource-safety, or audible evidence.",
        ],
    }


def _crossfade_spec(golden_digest: str) -> dict[str, Any]:
    source = core.load_json(ROOT / "contracts/task016/operation-spec-crossfader.json")
    binding = core.load_json(ROOT / "contracts/task016/implementation-binding-crossfader-r2.json")
    return _record({
        "schema_version": "direct-operation-spec-v2",
        "canonical_profile": "schuss-canonical-json-v1",
        "direct_operation_spec_id": "schuss-direct-operation-spec-000014",
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "opcode": "linear-mix-current-block-q27",
        "compatibility_mode": "legacy-equivalent-task026a-v1",
        "contract_reference": copy.deepcopy(ROLE_CONTRACTS["crossfade"]),
        "source_binding_reference": _ref(binding, "implementation_id"),
        "source_authority": copy.deepcopy(source["source_authority"]),
        "runtime_dependencies": copy.deepcopy(source["runtime_dependencies"]),
        "numeric_semantics": copy.deepcopy(source["numeric_semantics"]),
        "state_semantics": ["private_state=\"none\"", "public_control=\"previous-control-cycle-latch\""],
        "schedule_semantics": ["rate=\"sixteen-audio-samples-per-control-cycle\"", "first_input=\"current-pwm-block\"", "second_input=\"current-soft-clipped-saw-block\""],
        "golden_vector_set": {
            "schema_version": "task026a-semantic-goldens-v1",
            "portable_path": EVIDENCE + "semantic-goldens.json",
            "section": "operations.linear-mix-current-block-q27",
            "byte_sha256": golden_digest,
        },
    }, "schemas/direct-operation-spec-v2.schema.json")


def _crossfade_evidence(spec: dict[str, Any], golden_digest: str) -> dict[str, Any]:
    binding = core.load_json(ROOT / "contracts/task016/implementation-binding-crossfader-r2.json")
    return _record({
        "schema_version": "evidence-claim-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "evidence_claim_id": "schuss-evidence-claim-000044",
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "level": 2,
        "level_name": "component-graph-resolution",
        "subject_reference": {"subject_kind": "semantic-record", "stable_id": spec["direct_operation_spec_id"], "revision": 1, "content_hash": spec["content_hash"], "stage": "target-independent-graph-validation"},
        "method": "task026a-current-block-crossfade-vectors",
        "outcome": "passed",
        "evidence_inputs": [_semantic_ref(binding, "implementation_id"), _semantic_ref(spec, "direct_operation_spec_id")],
        "limitations": ["No DSP arithmetic changes are introduced.", "The claim proves neither device execution, real-time suitability, nor audible behavior."],
        "producer_identity": {"producer_kind": "validator", "producer_id": "schuss-task026a-validator", "version": "task026a-v1", "content_hash": "sha256:" + golden_digest},
    }, "schemas/evidence-claim-v0.schema.json")


def _backend() -> dict[str, Any]:
    value = core.load_json(ROOT / "contracts/task025/direct-backend-r3.json")
    value["revision"] = 4
    value["display_name"] = "Reverb-free seven-node direct application profile backend"
    value["lowering_identity"] = {"backend_kind": "direct-ksoloti-runtime", "contract_version": "direct-effects-seven-profile-v1"}
    value["bridge_boundary"] = {"kind": "direct-runtime-abi-instrument-closure-only", "location": "packages/schuss_core", "legacy_boundary_artifact": "generated-cpp", "execution_status": "not-run"}
    value["target_pairings"][0]["rationale"] = "Task 026A permits one exact headless included-instrument semantic profile; no Gills panel runtime realization, Java, AXP, fallback, or reverb path is consumed."
    return _record(value, "schemas/backend-v0.schema.json")


def _eligibilities(backend: dict[str, Any], claim: dict[str, Any]) -> dict[str, dict[str, Any]]:
    paths = {
        "saw": ("contracts/task025/binding-eligibility-saw.json", 2),
        "pwm": ("contracts/task025/binding-eligibility-pwm.json", 2),
        "smooth": ("contracts/task025/binding-eligibility-smooth.json", 2),
        "soft": ("contracts/task025/binding-eligibility-soft-clip.json", 2),
        "vca": ("contracts/task025/binding-eligibility-vca.json", 2),
        "crossfade": ("contracts/task025/carried-crossfader-eligibility-r3.json", 4),
        "output": ("contracts/task025/carried-audio-output-eligibility-r3.json", 4),
    }
    values = {}
    for role, (path, revision) in paths.items():
        value = core.load_json(ROOT / path)
        value["revision"] = revision
        value["allowed_pair"]["backend_reference"] = _ref(backend, "backend_id")
        if role == "crossfade":
            reference = _ref(claim, "evidence_claim_id")
            value["allowed_pair"]["state"]["evidence_refs"] = [reference]
            value["compatibility_evidence"] = [reference]
        values[role] = _record(value, "schemas/binding-eligibility-v0.schema.json")
    return values


def _graph() -> dict[str, Any]:
    value = core.load_json(ROOT / "contracts/task017/graph-effects.json")
    value["graph_id"] = "schuss-graph-000006"
    value["display_name"] = "Reverb-free dual-oscillator effects executable profile"
    value["nodes"] = [item for item in value["nodes"] if item["node_id"] != "graph-node-000004"]
    value["connections"] = [item for item in value["connections"] if item["connection_id"] not in {"graph-connection-000003", "graph-connection-000004"}]
    for item in value["connections"]:
        if item["connection_id"] == "graph-connection-000002":
            item["source"] = {"node_id": "graph-node-000002", "facet_id": "component-port-000003"}
        if item["connection_id"] == "graph-connection-000005":
            item["source"] = {"node_id": "graph-node-000003", "facet_id": "component-port-000002"}
    value["revision"] = 1
    return _record(value, "schemas/dsp-graph-v0.schema.json")


def _instrument(graph: dict[str, Any]) -> dict[str, Any]:
    value = core.load_json(ROOT / "contracts/task018/instrument-effects-r2.json")
    value["instrument_id"] = "schuss-instrument-000005"
    value["revision"] = 1
    value["display_name"] = "Headless reverb-free effects executable profile"
    value["graph_reference"] = {"status": "resolved", **_ref(graph, "graph_id")}
    value["device_input_mappings"] = []
    value["device_feedback_mappings"] = []
    return _record(value, "schemas/instrument-v0.schema.json")


def _request(graph: dict[str, Any], instrument: dict[str, Any], backend: dict[str, Any]) -> dict[str, Any]:
    value = core.load_json(ROOT / "contracts/task025/build-request-effects-r3.json")
    value["build_request_id"] = "schuss-build-request-000005"
    value["revision"] = 1
    value["graph_reference"] = _ref(graph, "graph_id")
    value["instrument_reference"] = {"status": "included", **_ref(instrument, "instrument_id")}
    value["backend_reference"] = _ref(backend, "backend_id")
    return _record(value, "schemas/build-request-v0.schema.json")


def generated() -> tuple[dict[str, bytes], dict[str, Any]]:
    goldens = _goldens()
    golden_bytes = core.canonical_json(goldens).encode("utf-8") + b"\n"
    golden_digest = hashlib.sha256(golden_bytes).hexdigest()
    spec = _crossfade_spec(golden_digest)
    claim = _crossfade_evidence(spec, golden_digest)
    backend = _backend()
    eligibility = _eligibilities(backend, claim)
    graph = _graph()
    instrument = _instrument(graph)
    request = _request(graph, instrument, backend)
    records: dict[str, tuple[str, dict[str, Any]]] = {
        "direct-backend-r4.json": ("backend", backend),
        "operation-spec-crossfade-current-block.json": ("direct-operation-spec", spec),
        "promotion-evidence-crossfade-current-block.json": ("evidence", claim),
        "graph-effects-seven-profile.json": ("dsp-graph", graph),
        "instrument-effects-seven-profile.json": ("instrument", instrument),
        "build-request-effects-seven-profile.json": ("request", request),
        **{f"binding-eligibility-{role}.json": ("eligibility", value) for role, value in eligibility.items()},
    }
    files = {EVIDENCE + "semantic-goldens.json": golden_bytes}
    for name, (_, record) in records.items():
        files[TASK + name] = core.canonical_json(record).encode("utf-8") + b"\n"
    parent = core.load_json(PARENT)
    schema_members = copy.deepcopy(parent["schema_members"])
    for path in ("schemas/build-handler-descriptor-v1.schema.json", "schemas/direct-operation-spec-v2.schema.json"):
        schema = core.load_json(ROOT / path)
        schema_members.append({"schema_version": schema["$id"].removesuffix(".schema.json"), "portable_path": path, "byte_sha256": core.sha256_file(ROOT / path)})
    record_members = copy.deepcopy(parent["record_members"])
    for name, (kind, record) in records.items():
        path = TASK + name
        id_field = next(field for field in (
            "backend_id", "direct_operation_spec_id", "evidence_claim_id", "graph_id", "instrument_id", "build_request_id", "binding_eligibility_id"
        ) if field in record)
        record_members.append({"record_kind": kind, "stable_id": record[id_field], "revision": record["revision"], "content_hash": record["content_hash"], "portable_path": path, "byte_sha256": hashlib.sha256(files[path]).hexdigest()})
    manifest = {
        "schema_version": "record-set-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "record_set_id": "schuss-record-set-000018",
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "purpose": "prospective-task",
        "parent_reference": {"status": "included", **{key: parent[key] for key in ("record_set_id", "revision", "content_hash")}},
        "schema_members": sorted(schema_members, key=lambda item: item["portable_path"]),
        "record_members": sorted(record_members, key=lambda item: (item["portable_path"], item["stable_id"], item["revision"])),
        "enforced_directories": sorted([*parent["enforced_directories"], "contracts/task026"]),
    }
    schema = core.load_json(ROOT / "schemas/prerequisite/record-set-v0.schema.json")
    manifest["content_hash"] = core.record_content_hash(manifest, schema)
    return files, manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files, manifest = generated()
    expected = {**files, MANIFEST.relative_to(ROOT).as_posix(): core.canonical_json(manifest).encode("utf-8") + b"\n"}
    if args.check:
        stale = [path for path, data in expected.items() if not (ROOT / path).is_file() or (ROOT / path).read_bytes() != data]
        if stale:
            raise SystemExit("stale Task 026A generated files: " + ", ".join(stale))
        print("Task 026A generated records: fresh")
        return 0
    for path, data in expected.items():
        target = ROOT / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    print(f"wrote {len(expected)} Task 026A files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
