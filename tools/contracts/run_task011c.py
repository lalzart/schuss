#!/usr/bin/env python3
"""Execute or validate the exact Task 011C Gills-slice proof."""

from __future__ import annotations

import argparse
import copy
import hashlib
from pathlib import Path
import shutil
import sys
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools/contracts"
for path in (ROOT, TOOLS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from packages.schuss_core import (  # noqa: E402
    canonical_result_bytes,
    dispatch_operation,
    load_repository_context,
)

import record_set_rules  # noqa: E402
import run_task009 as task009_run  # noqa: E402
import target_backend_build_rules as target_rules  # noqa: E402
import task009_backend as task009_backend  # noqa: E402
import task009_prerequisite_rules as prerequisite  # noqa: E402
import task011b_rules  # noqa: E402
import task011c_backend as backend  # noqa: E402
import validator_core as core  # noqa: E402


TASK_RECORD_ROOT = ROOT / "contracts/task011c"
EVIDENCE_ROOT = ROOT / "evidence/task-011c-v1"
ARTIFACT_STORE = EVIDENCE_ROOT / "artifacts/sha256"
BUILD_ROOT = ROOT / "build/task011c-v1-run1"
PARENT_MANIFEST = ROOT / "contracts/record-sets/task011b-vertical-slice-v1.json"
SUCCESSOR_MANIFEST = ROOT / "contracts/record-sets/task011c-executed-v1.json"

JAVA = Path("/Applications/Ksoloti Local.app/Contents/Resources/jre/bin/java")
JAVAC = Path("/Applications/Ksoloti Local.app/Contents/Resources/jre/bin/javac")
ARM_BIN = Path("/Applications/Ksoloti Local.app/Contents/Resources/platform_mac_x64/bin")
CONTENT_STORE = ROOT / "build/task009-prerequisite-repair-v1/content-addressed"
CONTRIB = Path("/Users/lanceship/ksoloti/1.1.0/axoloti-contrib")

SCHEMAS = {
    **task009_run.SCHEMAS,
    "conformance-probe-input-v1": core.load_json(
        ROOT / "schemas/prerequisite/conformance-probe-input-v1.schema.json"
    ),
}
ARTIFACT_KINDS = tuple(backend.ARTIFACT_ORDER)
CROSSFADER_BINDING_R2_HASH = (
    "sha256:7afa2bd29077c10c2f9e9313d7d803c0092c6e059aee89f7f4de2b230ed688cf"
)
PROBE_ARTIFACT_IDS = {
    kind: f"schuss-artifact-{index:06d}"
    for index, kind in enumerate(ARTIFACT_KINDS, 15)
}
PRODUCTION_ARTIFACT_IDS = {
    kind: f"schuss-artifact-{index:06d}"
    for index, kind in enumerate(ARTIFACT_KINDS, 22)
}

ROLE_NAMES = ("lfo", "counter", "sequencer", "sine", "filter", "output")
PROBE_IDS = {
    name: f"schuss-conformance-probe-{index:06d}"
    for index, name in enumerate(ROLE_NAMES, 3)
}
RESULT_IDS = {
    name: f"schuss-conformance-probe-result-{index:06d}"
    for index, name in enumerate(ROLE_NAMES, 3)
}
PROBE_EVIDENCE_IDS = {
    name: f"schuss-conformance-probe-evidence-{index:06d}"
    for index, name in enumerate(ROLE_NAMES, 3)
}
PROMOTION_CLAIM_IDS = {
    name: f"schuss-evidence-claim-{index:06d}"
    for index, name in enumerate(ROLE_NAMES, 7)
}


def _canonical_bytes(value: Any) -> bytes:
    return core.canonical_json(value).encode("utf-8")


def _write_exact(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() != payload:
        raise ValueError(f"refusing to replace differing Task 011C output: {path}")
    path.write_bytes(payload)


def _write_json(path: Path, value: Any) -> None:
    _write_exact(path, _canonical_bytes(value) + b"\n")


def _seal(record: dict[str, Any]) -> dict[str, Any]:
    return task009_run._seal(record, record["schema_version"])


def _reference(record: Mapping[str, Any], id_field: str) -> dict[str, Any]:
    return task009_run._reference(record, id_field)


def _generic_reference(
    record: Mapping[str, Any], id_field: str, kind: str | None = None
) -> dict[str, Any]:
    return task009_run._generic_reference(record, id_field, kind)


def _closure_hash(values: Iterable[dict[str, Any]]) -> str:
    return task009_run._closure_hash(values)


def _config() -> backend.ExecutionConfig:
    return backend.ExecutionConfig(
        ROOT, CONTENT_STORE, JAVA, JAVAC, ARM_BIN, CONTRIB
    )


def _preflight() -> dict[str, Any]:
    task009_summary = task009_run.validate()
    task011b_summary = task011b_rules.validate_task011b(ROOT, PARENT_MANIFEST)
    if task009_summary["status"] != "valid" or task011b_summary["status"] != "valid":
        raise ValueError("Task 009 or Task 011B prerequisite is invalid")
    config = backend.verify_execution_config(_config())
    parent = record_set_rules.load_record_set(ROOT, PARENT_MANIFEST)
    if parent.reference != {
        "record_set_id": "schuss-record-set-000005",
        "revision": 1,
        "content_hash": "sha256:b84ccbbb916560b4f46c8e5619d5c0f7ecf00f50d16ed8209c58461e19e87da3",
    }:
        raise ValueError("Task 011B parent identity differs")

    default_context = load_repository_context(ROOT, record_set_path=PARENT_MANIFEST)
    request = next(
        record for record in parent.records["request"]
        if record["build_request_id"] == "schuss-build-request-000002"
        and record["revision"] == 1
    )
    unresolved = dispatch_operation({
        "schema_version": "schuss-operation-request-v1",
        "canonical_profile": "schuss-canonical-json-v1",
        "operation": "build.resolve",
        "payload": {"build_request_reference": _reference(request, "build_request_id")},
    }, default_context)
    selected = [
        trace.get("selected_binding_reference")
        for trace in unresolved["value"]["resolution_traces"]
        if trace["status"] == "selected"
    ]
    if (
        unresolved["status"] != "unresolved"
        or unresolved["value"]["backend_invocation"] is not None
        or selected != [{
            "implementation_id": task009_backend.BINDING_ID,
            "revision": 2,
            "content_hash": CROSSFADER_BINDING_R2_HASH,
        }]
    ):
        raise ValueError("Task 011B unresolved baseline differs")

    report = {
        "schema_version": "task011c-preflight-v0",
        "status": "passed",
        "parent_record_set": parent.reference,
        "task009_validation": {
            "status": task009_summary["status"],
            "record_set_reference": task009_summary["record_set_reference"],
            "artifact_count": task009_summary["artifact_count"],
        },
        "task011b_validation": {
            "status": task011b_summary["status"],
            "record_set_reference": task011b_summary["record_set_reference"],
        },
        "task011b_resolution": {
            "status": unresolved["status"],
            "selected_binding_references": selected,
            "backend_invocation_present": False,
        },
        "source_identities": {
            "factory_commit": backend.FACTORY_COMMIT,
            "contrib_commit": backend.CONTRIB_COMMIT,
            "contrib_source_sha256": backend.CONTRIB_SOURCE_SHA256,
            "selected_source_sha256": {
                spec["binding_id"]: spec["source_sha256"]
                for spec in backend.NODE_SPECS
            },
        },
        "tool_identities": {
            "java": task009_backend.JAVA_SHA256,
            "javac": task009_backend.JAVAC_SHA256,
            "arm_components": dict(sorted(task009_backend.ARM_COMPONENTS.items())),
            "firmware_bin": task009_backend.FIRMWARE_BIN_SHA256,
            "firmware_link_elf": task009_backend.FIRMWARE_ELF_SHA256,
        },
        "execution_config_verified": bool(config),
    }
    return report


def _authorized_probes() -> dict[str, dict[str, Any]]:
    probes = {}
    for name in ROLE_NAMES:
        value = core.load_json(ROOT / f"contracts/task011b/probe-inputs/{name}.json")
        if value["conformance_probe_id"] != PROBE_IDS[name] or value["revision"] != 1:
            raise ValueError(f"Task 011B {name} probe identity differs")
        value["revision"] = 2
        value["schema_version"] = "conformance-probe-input-v1"
        value["execution_authorization"] = "task-011c-authorized"
        value["content_hash"] = "sha256:" + "0" * 64
        value = _seal(value)
        backend.validate_probe_input(value)
        probes[name] = value
    return probes


def _binding_refs(revision: int) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for spec in backend.NODE_SPECS:
        if spec["binding_id"] == task009_backend.BINDING_ID:
            result[spec["binding_id"]] = {
                "implementation_id": task009_backend.BINDING_ID,
                "revision": 2,
                "content_hash": CROSSFADER_BINDING_R2_HASH,
            }
        else:
            if revision != 1:
                raise ValueError("promoted binding references require records")
            result[spec["binding_id"]] = {
                "implementation_id": spec["binding_id"],
                "revision": 1,
                "content_hash": spec["binding_r1_hash"],
            }
    return result


def _retain_artifacts(outcome: task009_backend.ExecutionOutcome) -> None:
    for fact in outcome.artifacts:
        destination = ARTIFACT_STORE / fact.byte_sha256
        if destination.exists():
            if core.sha256_file(destination) != fact.byte_sha256:
                raise ValueError("Task 011C artifact-store hash collision")
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(fact.retained_path, destination)
            destination.chmod(0o444)


def _artifact_descriptors(
    outcome: task009_backend.ExecutionOutcome,
    ids: Mapping[str, str],
    input_hash: str,
) -> dict[str, dict[str, Any]]:
    facts = {fact.kind: fact for fact in outcome.artifacts}
    parents = {
        "resolution-plan": (),
        "legacy-boundary-patch": ("resolution-plan",),
        "source-map": ("resolution-plan", "legacy-boundary-patch"),
        "generated-cpp": ("legacy-boundary-patch",),
        "arm-object": ("generated-cpp",),
        "target-executable": ("arm-object",),
        "link-map": ("arm-object",),
    }
    source_maps = {
        "resolution-plan": (), "legacy-boundary-patch": (), "source-map": (),
        "generated-cpp": ("source-map",), "arm-object": ("source-map",),
        "target-executable": ("source-map",), "link-map": ("source-map",),
    }
    records: dict[str, dict[str, Any]] = {}
    for kind in ARTIFACT_KINDS:
        fact = facts[kind]
        records[kind] = _seal({
            "schema_version": "artifact-descriptor-v0",
            "canonical_profile": "schuss-canonical-json-v1",
            "artifact_id": ids[kind],
            "revision": 1,
            "content_hash": "sha256:" + "0" * 64,
            "artifact_kind": kind,
            "media_type": fact.media_type,
            "byte_length": fact.byte_length,
            "byte_sha256": fact.byte_sha256,
            "producer_stage": fact.producer_stage,
            "producer_contract": {
                "producer_id": "schuss-task011c-backend",
                "producer_version": "task011c-v1",
            },
            "input_closure_hash": input_hash,
            "portable_locator": fact.portable_locator,
            "parent_artifact_references": [
                _reference(records[parent], "artifact_id") for parent in parents[kind]
            ],
            "source_map_artifact_references": [
                _reference(records[item], "artifact_id") for item in source_maps[kind]
            ],
        })
    return records


def _probe_result(
    name: str,
    probe: dict[str, Any],
    outcome: task009_backend.ExecutionOutcome,
    artifacts: Mapping[str, dict[str, Any]],
) -> dict[str, Any]:
    by_stage = {
        "backend-lowering": ("resolution-plan",),
        "artifact-generation": ("legacy-boundary-patch", "source-map", "generated-cpp"),
        "target-compile-link": ("arm-object", "target-executable", "link-map"),
    }
    return _seal({
        "schema_version": "conformance-probe-result-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "conformance_probe_result_id": RESULT_IDS[name],
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "probe_reference": _reference(probe, "conformance_probe_id"),
        "candidate_state": "candidate-under-test",
        "binding_reference": copy.deepcopy(probe["binding_reference"]),
        "environment_reference": copy.deepcopy(probe["environment_reference"]),
        "stage_outcomes": [
            {
                "ordinal": ordinal,
                "stage": stage,
                "status": status,
                "diagnostic_ids": [
                    item["diagnostic_id"] for item in outcome.diagnostics
                    if item["stage"] == stage
                ],
                "artifact_references": [
                    _reference(artifacts[kind], "artifact_id")
                    for kind in by_stage[stage]
                    if status == "success"
                ],
            }
            for ordinal, (stage, status) in enumerate(outcome.stage_statuses, 1)
        ],
        "diagnostics": list(outcome.diagnostics),
        "artifact_references": [
            _reference(artifacts[kind], "artifact_id") for kind in ARTIFACT_KINDS
        ],
        "overall_status": outcome.status,
        "production_selection_authority": False,
    })


def _probe_evidence(
    name: str, probe: dict[str, Any], result: dict[str, Any]
) -> dict[str, Any]:
    return _seal({
        "schema_version": "conformance-probe-evidence-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "conformance_probe_evidence_id": PROBE_EVIDENCE_IDS[name],
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "probe_result_reference": _reference(result, "conformance_probe_result_id"),
        "binding_reference": copy.deepcopy(probe["binding_reference"]),
        "procedure_reference": copy.deepcopy(probe["procedure_reference"]),
        "outcome": "passed",
        "evidence_level": 5,
        "limitations": [
            "The probe grants no production selection authority by itself.",
            "No connected-device, real-time, or audible procedure ran.",
        ],
    })


def _promotion_claim(
    name: str, probe_evidence: dict[str, Any], producer_hash: str
) -> dict[str, Any]:
    binding = probe_evidence["binding_reference"]
    return _seal({
        "schema_version": "evidence-claim-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "evidence_claim_id": PROMOTION_CLAIM_IDS[name],
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "level": 2,
        "level_name": "component-graph-resolution",
        "subject_reference": {
            "subject_kind": "semantic-record",
            **_generic_reference(
                probe_evidence, "conformance_probe_evidence_id"
            ),
            "stage": "target-independent-graph-validation",
        },
        "method": "authorized-exact-binding-probe",
        "outcome": "passed",
        "evidence_inputs": [
            {"input_kind": "semantic-record", "stable_id": binding["implementation_id"],
             "revision": 1, "content_hash": binding["content_hash"]},
            {"input_kind": "semantic-record", **_generic_reference(
                probe_evidence, "conformance_probe_evidence_id")},
        ],
        "limitations": [
            "The claim is bounded to the exact Task 011B eight-node graph closure.",
            "It establishes no connected-device, real-time, or audible behavior.",
        ],
        "producer_identity": task009_run._producer_identity(
            "validator", "schuss-task011c-probe-validator", producer_hash
        ),
    })


def _promoted_records(
    probes: Mapping[str, dict[str, Any]],
    evidence: Mapping[str, dict[str, Any]],
    claims: Mapping[str, dict[str, Any]],
) -> dict[str, Any]:
    binding_files = {
        name: ROOT / f"contracts/task011b/implementation-bindings/{name}.json"
        for name in ROLE_NAMES
    }
    eligibility_files = {
        name: ROOT / f"contracts/task011b/binding-eligibility/{name}.json"
        for name in ROLE_NAMES
    }
    bindings: dict[str, dict[str, Any]] = {}
    for name, path in binding_files.items():
        value = core.load_json(path)
        value["revision"] = 2
        value["content_hash"] = "sha256:" + "0" * 64
        bindings[name] = _seal(value)

    backend_record = core.load_json(ROOT / "contracts/task009/legacy-ksoloti-v0-r2.json")
    backend_record["revision"] = 3
    backend_record["content_hash"] = "sha256:" + "0" * 64
    backend_record["supported_realization_forms"] = sorted({
        *backend_record["supported_realization_forms"], "legacy-native-object"
    })
    backend_record["target_pairings"][0]["rationale"] = (
        "Task 011C established the exact eight-node Gills-slice source-generation "
        "and ARM compile/link path, including its one pinned legacy-native object."
    )
    backend_record = _seal(backend_record)

    target = core.load_json(ROOT / "contracts/task009/ksoloti-core-v0-r2.json")
    toolchain = core.load_json(ROOT / "contracts/task009/arm-none-eabi-v0-r2.json")
    runtime = core.load_json(ROOT / "contracts/task009/ksoloti-runtime-abi-v0-r2.json")

    eligibilities: dict[str, dict[str, Any]] = {}
    for name, path in eligibility_files.items():
        value = core.load_json(path)
        value["revision"] = 2
        value["content_hash"] = "sha256:" + "0" * 64
        value["binding_reference"] = _reference(bindings[name], "implementation_id")
        claim_ref = _reference(claims[name], "evidence_claim_id")
        value["allowed_pair"] = {
            "target_reference": _reference(target, "compute_target_id"),
            "backend_reference": _reference(backend_record, "backend_id"),
            "state": {
                "status": "supported", "evidence_level": 2,
                "evidence_refs": [claim_ref],
            },
        }
        value["compatibility_evidence"] = [claim_ref]
        value["unresolved_questions"] = []
        eligibilities[name] = _seal(value)

    crossfader_eligibility = core.load_json(
        ROOT / "contracts/task009/crossfader-mixed-legacy-eligibility-v0-r2.json"
    )
    crossfader_eligibility["revision"] = 3
    crossfader_eligibility["content_hash"] = "sha256:" + "0" * 64
    crossfader_eligibility["allowed_pair"]["backend_reference"] = _reference(
        backend_record, "backend_id"
    )
    crossfader_eligibility = _seal(crossfader_eligibility)

    request = core.load_json(
        ROOT / "contracts/task011b/build-requests/four-step-dual-sine.json"
    )
    request["revision"] = 2
    request["content_hash"] = "sha256:" + "0" * 64
    request["backend_reference"] = _reference(backend_record, "backend_id")
    request["requested_stopping_stage"] = "target-compile-link"
    request = _seal(request)

    return {
        "bindings": bindings,
        "eligibilities": eligibilities,
        "crossfader-eligibility": crossfader_eligibility,
        "backend": backend_record,
        "target": target,
        "toolchain": toolchain,
        "runtime": runtime,
        "request": request,
        "probe-evidence": dict(evidence),
    }


def _stable_id(record: Mapping[str, Any]) -> str:
    return task009_run._stable_id(record)


def _record_member(kind: str, path: Path, record: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "record_kind": kind,
        "stable_id": _stable_id(record),
        "revision": record["revision"],
        "content_hash": record["content_hash"],
        "portable_path": path.relative_to(ROOT).as_posix(),
        "byte_sha256": core.sha256_file(path),
    }


def _write_records(
    records: Iterable[tuple[str, str, dict[str, Any]]]
) -> list[dict[str, Any]]:
    members = []
    for kind, filename, record in records:
        path = TASK_RECORD_ROOT / filename
        _write_exact(path, task009_run._record_bytes(record))
        members.append(_record_member(kind, path, record))
    return members


def _record_set_manifest(
    record_set_id: str,
    parent: record_set_rules.LoadedRecordSet,
    new_members: Iterable[dict[str, Any]],
    enforce: bool,
) -> dict[str, Any]:
    return _seal({
        "schema_version": "record-set-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "record_set_id": record_set_id,
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "purpose": "prospective-task",
        "parent_reference": {"status": "included", **parent.reference},
        "schema_members": [
            *copy.deepcopy(parent.manifest["schema_members"]),
            {
                "schema_version": "conformance-probe-input-v1",
                "portable_path": "schemas/prerequisite/conformance-probe-input-v1.schema.json",
                "byte_sha256": core.sha256_file(
                    ROOT / "schemas/prerequisite/conformance-probe-input-v1.schema.json"
                ),
            },
        ],
        "record_members": [
            *copy.deepcopy(parent.manifest["record_members"]),
            *copy.deepcopy(list(new_members)),
        ],
        "enforced_directories": [
            *copy.deepcopy(parent.manifest["enforced_directories"]),
            *(["contracts/task011c"] if enforce else []),
        ],
    })


def _preliminary_plan(
    probes: Mapping[str, dict[str, Any]],
    results: Mapping[str, dict[str, Any]],
    probe_evidence: Mapping[str, dict[str, Any]],
    artifacts: Mapping[str, dict[str, Any]],
    claims: Mapping[str, dict[str, Any]],
    promoted: Mapping[str, Any],
) -> list[tuple[str, str, dict[str, Any]]]:
    records: list[tuple[str, str, dict[str, Any]]] = []
    for name in ROLE_NAMES:
        records.extend([
            ("conformance-probe-input", f"authorized-probe-input-{name}.json", probes[name]),
            ("conformance-probe-result", f"authorized-probe-result-{name}.json", results[name]),
            ("conformance-probe-evidence", f"authorized-probe-evidence-{name}.json", probe_evidence[name]),
            ("evidence", f"probe-promotion-evidence-{name}.json", claims[name]),
            ("implementation-binding", f"implementation-binding-{name}-r2.json", promoted["bindings"][name]),
            ("eligibility", f"binding-eligibility-{name}-r2.json", promoted["eligibilities"][name]),
        ])
    records.extend([
        ("backend", "legacy-ksoloti-r3.json", promoted["backend"]),
        ("eligibility", "crossfader-mixed-eligibility-r3.json", promoted["crossfader-eligibility"]),
        ("request", "four-step-dual-sine-build-request-r2.json", promoted["request"]),
    ])
    records.extend(
        ("artifact", f"probe-artifact-{index:02d}-{kind}.json", artifacts[kind])
        for index, kind in enumerate(ARTIFACT_KINDS, 1)
    )
    return records


def _production_closure(promoted: Mapping[str, Any]) -> list[dict[str, Any]]:
    records: list[tuple[str, Mapping[str, Any], str]] = [
        ("dsp-graph", core.load_json(ROOT / "contracts/task011b/graphs/four-step-dual-sine.json"), "graph_id"),
        ("device-profile", next(record for record in record_set_rules.load_record_set(ROOT, PARENT_MANIFEST).records["device-profile"] if record["device_profile_id"] == "schuss-device-profile-000001"), "device_profile_id"),
        ("instrument", core.load_json(ROOT / "contracts/task011b/instruments/four-step-dual-sine.json"), "instrument_id"),
        ("capability-vocabulary", core.load_json(ROOT / "contracts/capabilities/task007-v0.json"), "capability_vocabulary_id"),
        ("build-environment", promoted["toolchain"], "build_environment_id"),
        ("build-environment", promoted["runtime"], "build_environment_id"),
        ("compute-target", promoted["target"], "compute_target_id"),
        ("backend", promoted["backend"], "backend_id"),
        ("build-request", promoted["request"], "build_request_id"),
    ]
    for name in ROLE_NAMES:
        contract = core.load_json(ROOT / f"contracts/task011b/component-contracts/{name}.json")
        records.extend([
            ("component-contract", contract, "component_contract_id"),
            ("implementation-binding", promoted["bindings"][name], "implementation_id"),
            ("binding-eligibility", promoted["eligibilities"][name], "binding_eligibility_id"),
        ])
    crossfader_binding = core.load_json(ROOT / "contracts/task009/crossfader-mixed-legacy-v0-r2.json")
    crossfader_eligibility = promoted["crossfader-eligibility"]
    crossfader_contract = core.load_json(ROOT / "contracts/component-contracts/crossfader-mixed-v0.json")
    records.extend([
        ("component-contract", crossfader_contract, "component_contract_id"),
        ("implementation-binding", crossfader_binding, "implementation_id"),
        ("binding-eligibility", crossfader_eligibility, "binding_eligibility_id"),
    ])
    return sorted(
        [_generic_reference(record, field, kind) for kind, record, field in records],
        key=core.canonical_json,
    )


def _resource_report(
    promoted: Mapping[str, Any], facts: Mapping[str, Any]
) -> dict[str, Any]:
    amounts = task009_run._resource_amounts(facts)
    observations = [
        {"observation_id": "resource-observation-000004", "observation_kind": "compiler-link-map-observation", "resource_kind": "code", "region_id": "target-memory-region-000002", "amount_bytes": amounts["code"], "alignment_bytes": 4, "unit": "bytes", "method": "compiler-link-map", "evidence_level": 5},
        {"observation_id": "resource-observation-000005", "observation_kind": "compiler-link-map-observation", "resource_kind": "read-only-data", "region_id": "target-memory-region-000002", "amount_bytes": amounts["read-only-data"], "alignment_bytes": 4, "unit": "bytes", "method": "compiler-link-map", "evidence_level": 5},
        {"observation_id": "resource-observation-000006", "observation_kind": "compiler-link-map-observation", "resource_kind": "data", "region_id": "target-memory-region-000001", "amount_bytes": amounts["data"], "alignment_bytes": 4, "unit": "bytes", "method": "compiler-link-map", "evidence_level": 5},
    ]
    return _seal({
        "schema_version": "resource-report-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "resource_report_id": "schuss-resource-report-000002",
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "subject_reference": {"subject_kind": "build-request", **_generic_reference(promoted["request"], "build_request_id")},
        "compute_target_reference": _reference(promoted["target"], "compute_target_id"),
        "observations": observations,
        "budget_comparisons": [
            {"comparison_id": "resource-comparison-000003", "observation_ids": ["resource-observation-000004", "resource-observation-000005"], "region_id": "target-memory-region-000002", "budget_bytes": 45056, "total_aligned_amount_bytes": amounts["code"] + amounts["read-only-data"], "outcome": "within-budget"},
            {"comparison_id": "resource-comparison-000004", "observation_ids": ["resource-observation-000006"], "region_id": "target-memory-region-000001", "budget_bytes": 51200, "total_aligned_amount_bytes": amounts["data"], "outcome": "within-budget"},
        ],
    })


def _selected_bindings(promoted: Mapping[str, Any]) -> list[dict[str, Any]]:
    by_id = {
        value["implementation_id"]: (value, promoted["eligibilities"][name])
        for name, value in promoted["bindings"].items()
    }
    cross_binding = core.load_json(ROOT / "contracts/task009/crossfader-mixed-legacy-v0-r2.json")
    cross_eligibility = promoted["crossfader-eligibility"]
    by_id[cross_binding["implementation_id"]] = (cross_binding, cross_eligibility)
    values = []
    for spec in backend.NODE_SPECS:
        binding, eligibility = by_id[spec["binding_id"]]
        values.append({
            "node_id": spec["node_id"],
            "binding_reference": _reference(binding, "implementation_id"),
            "eligibility_reference": _reference(eligibility, "binding_eligibility_id"),
            "selection_policy_id": eligibility["selection_policy"]["policy_id"],
        })
    return values


def _build_result(
    promoted: Mapping[str, Any], artifacts: Mapping[str, dict[str, Any]],
    resource: dict[str, Any]
) -> dict[str, Any]:
    closure = _production_closure(promoted)
    by_stage = {
        "implementation-resolution": ["resolution-plan"],
        "artifact-generation": ["legacy-boundary-patch", "source-map", "generated-cpp"],
        "target-compile-link": ["arm-object", "target-executable", "link-map"],
    }
    resource_ref = _reference(resource, "resource_report_id")
    stages = []
    stop = target_rules.STAGES.index("target-compile-link")
    for ordinal, stage in enumerate(target_rules.STAGES, 1):
        ran = ordinal <= stop + 1
        stages.append({
            "ordinal": ordinal, "stage": stage,
            "status": "success" if ran else "not-run", "diagnostic_ids": [],
            "artifact_references": [_reference(artifacts[k], "artifact_id") for k in by_stage.get(stage, [])] if ran else [],
            "resource_report_references": [resource_ref] if stage == "target-compile-link" else [],
        })
    return _seal({
        "schema_version": "build-result-v0", "canonical_profile": "schuss-canonical-json-v1",
        "build_result_id": "schuss-build-result-000002", "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "request_reference": _reference(promoted["request"], "build_request_id"),
        "input_closure": closure, "input_closure_hash": _closure_hash(closure),
        "selected_bindings": _selected_bindings(promoted),
        "compute_target_reference": _reference(promoted["target"], "compute_target_id"),
        "backend_reference": _reference(promoted["backend"], "backend_id"),
        "toolchain_reference": _reference(promoted["toolchain"], "build_environment_id"),
        "firmware_runtime_reference": _reference(promoted["runtime"], "build_environment_id"),
        "options_used": copy.deepcopy(promoted["request"]["options"]),
        "stage_outcomes": stages, "diagnostics": [],
        "artifact_references": [_reference(artifacts[k], "artifact_id") for k in ARTIFACT_KINDS],
        "resource_report_references": [resource_ref], "overall_status": "success",
    })


def _production_evidence(
    result: dict[str, Any], promoted: Mapping[str, Any],
    artifacts: Mapping[str, dict[str, Any]], resource: dict[str, Any],
    producer_hash: str,
) -> list[dict[str, Any]]:
    result_input = {"input_kind": "build-result", **_generic_reference(result, "build_result_id")}
    specs = [
        (1, "structural-schema-validation", "schema-identity-validation", "validator", "schuss-task011c-contract-validator", "closed-schema-and-exact-identity-validation", [result_input], ["Structural validity does not imply backend or device execution."]),
        (2, "component-graph-resolution", "target-independent-graph-validation", "validator", "schuss-task011c-resolution-validator", "ordinary-build-resolve-selection", [result_input, *[{"input_kind": "semantic-record", **_generic_reference(promoted["probe-evidence"][name], "conformance_probe_evidence_id")} for name in ROLE_NAMES]], ["Resolution is bounded to the exact Task 011B graph and promoted pair."]),
        (3, "backend-lowering", "backend-lowering", "backend", "schuss-task011c-backend", "exact-slice-lowering", [result_input, {"input_kind": "artifact", **_generic_reference(artifacts["resolution-plan"], "artifact_id")}], ["Lowering supports only the exact Task 011B Gills slice."]),
        (4, "source-artifact-generation", "artifact-generation", "backend", "schuss-task011c-backend", "isolated-legacy-source-generation", [result_input, *[{"input_kind": "artifact", **_generic_reference(artifacts[k], "artifact_id")} for k in ("legacy-boundary-patch", "source-map", "generated-cpp")]], ["Generated source was not run on a connected device."]),
        (5, "arm-compilation-linking", "target-compile-link", "toolchain", "gnu-arm-embedded-task011c", "exact-arm-compile-link", [result_input, *[{"input_kind": "artifact", **_generic_reference(artifacts[k], "artifact_id")} for k in ("arm-object", "target-executable", "link-map")], {"input_kind": "resource-report", **_generic_reference(resource, "resource_report_id")}], ["Compile and link success is not connected-device execution.", "Static linker observations are not real-time resource measurements.", "No audible procedure ran."]),
    ]
    claims = []
    for level, name, stage, producer_kind, producer_id, method, inputs, limitations in specs:
        claims.append(_seal({
            "schema_version": "evidence-claim-v0", "canonical_profile": "schuss-canonical-json-v1",
            "evidence_claim_id": f"schuss-evidence-claim-{level + 12:06d}",
            "revision": 1, "content_hash": "sha256:" + "0" * 64,
            "level": level, "level_name": name,
            "subject_reference": {"subject_kind": "build-result" if level == 1 else "build-stage", **_generic_reference(result, "build_result_id"), "stage": stage},
            "method": method, "outcome": "passed", "evidence_inputs": copy.deepcopy(inputs),
            "limitations": limitations,
            "producer_identity": task009_run._producer_identity(producer_kind, producer_id, producer_hash),
        }))
    return claims


def _portable_outcome(outcome: task009_backend.ExecutionOutcome) -> dict[str, Any]:
    return {
        "status": outcome.status,
        "artifacts": {fact.kind: {"byte_sha256": fact.byte_sha256, "byte_length": fact.byte_length, "portable_locator": fact.portable_locator} for fact in outcome.artifacts},
        "stage_statuses": [list(item) for item in outcome.stage_statuses],
        "diagnostics": list(outcome.diagnostics), "bridge_result": copy.deepcopy(outcome.bridge_result),
        "command_vectors": list(outcome.command_vectors), "resource_facts": copy.deepcopy(outcome.resource_facts),
    }


def _run_failures(refs: Mapping[str, Mapping[str, Any]], config: backend.ExecutionConfig) -> dict[str, Any]:
    values = []
    for stage, suffix in zip(backend.PROBE_STAGES, ("lowering", "generation", "arm")):
        outcome = backend.execute_exact_slice(refs, config, BUILD_ROOT / f"failure-{suffix}", failure_stage=stage)
        statuses = dict(outcome.stage_statuses)
        later = False
        for candidate in backend.PROBE_STAGES:
            if candidate == stage:
                later = True
            elif later and statuses[candidate] != "not-run":
                raise ValueError(f"Task 011C continued after injected {stage} failure")
        if outcome.status != "failed" or statuses[stage] != "failed":
            raise ValueError(f"Task 011C did not fail at injected {stage}")
        values.append({"stage": stage, "overall_status": outcome.status, "stage_statuses": [list(item) for item in outcome.stage_statuses], "diagnostic_codes": [item["code"] for item in outcome.diagnostics]})
    return {"schema_version": "task011c-failure-injection-v0", "status": "passed", "outcomes": values}


def execute() -> dict[str, Any]:
    if BUILD_ROOT.exists():
        raise ValueError("Task 011C execution root must be fresh")
    preflight = _preflight()
    _write_json(EVIDENCE_ROOT / "preflight.json", preflight)
    parent = record_set_rules.load_record_set(ROOT, PARENT_MANIFEST)
    config = _config()
    producer_hash = "sha256:" + core.sha256_file(ROOT / "tools/contracts/task011c_backend.py")

    probes = _authorized_probes()
    candidate_refs = _binding_refs(1)
    outcomes: dict[str, task009_backend.ExecutionOutcome] = {}
    for index, name in enumerate(ROLE_NAMES, 1):
        outcome = backend.execute_exact_slice(candidate_refs, config, BUILD_ROOT / f"probe-{index:02d}-{name}")
        if outcome.status != "success":
            raise ValueError(f"authorized {name} probe failed")
        outcomes[name] = outcome
    equalities = {
        name: backend.compare_deterministic_outcomes(outcomes[ROLE_NAMES[0]], outcomes[name])
        for name in ROLE_NAMES[1:]
    }
    if not all(all(value[key] for key in ("command_vectors_equal", "bridge_results_equal", "resource_facts_equal")) for value in equalities.values()):
        raise ValueError("candidate probe facts differ across fresh roots")
    first = outcomes[ROLE_NAMES[0]]
    _retain_artifacts(first)
    probe_closure = [
        *[_reference(probes[name], "conformance_probe_id") for name in ROLE_NAMES],
        *candidate_refs.values(),
        copy.deepcopy(probes[ROLE_NAMES[0]]["graph_reference"]),
        copy.deepcopy(probes[ROLE_NAMES[0]]["environment_reference"]),
        copy.deepcopy(probes[ROLE_NAMES[0]]["procedure_reference"]),
    ]
    probe_artifacts = _artifact_descriptors(first, PROBE_ARTIFACT_IDS, _closure_hash(probe_closure))
    results = {name: _probe_result(name, probes[name], outcomes[name], probe_artifacts) for name in ROLE_NAMES}
    probe_evidence = {name: _probe_evidence(name, probes[name], results[name]) for name in ROLE_NAMES}
    promotion_claims = {name: _promotion_claim(name, probe_evidence[name], producer_hash) for name in ROLE_NAMES}
    promoted = _promoted_records(probes, probe_evidence, promotion_claims)

    registry = task009_run._probe_validation_registry(parent, [
        *probes.values(), *results.values(), *probe_evidence.values(), *probe_artifacts.values()
    ])
    procedure = next(record for record in parent.records["conformance-probe-procedure"] if record["procedure_id"] == backend.PROCEDURE_ID)
    environment = parent.records["prerequisite-environment"][0]
    for name in ROLE_NAMES:
        diagnostics = prerequisite.validate_probe_values(probes[name], results[name], probe_evidence[name], procedure, environment, registry)
        if diagnostics:
            raise ValueError(f"authorized {name} probe records invalid: {diagnostics}")

    preliminary = _preliminary_plan(probes, results, probe_evidence, probe_artifacts, promotion_claims, promoted)
    preliminary_members = _write_records(preliminary)
    temporary_manifest = _record_set_manifest("schuss-record-set-999998", parent, preliminary_members, False)
    temporary_path = BUILD_ROOT / "promotion-record-set.json"
    _write_exact(temporary_path, task009_run._record_bytes(temporary_manifest))
    context = load_repository_context(ROOT, record_set_path=temporary_path, parent_record_set_path=PARENT_MANIFEST)
    if context.task007_summary["status"] != "valid":
        raise ValueError("promoted Task 011C context is invalid: " + core.canonical_json(context.task007_summary["diagnostics"]))
    operation = {"schema_version": "schuss-operation-request-v1", "canonical_profile": "schuss-canonical-json-v1", "operation": "build.resolve", "payload": {"build_request_reference": _reference(promoted["request"], "build_request_id")}}
    resolution = dispatch_operation(operation, context)
    if resolution["status"] != "success" or resolution["value"]["backend_invocation"] is None:
        raise ValueError("ordinary promoted Task 011C build.resolve failed")
    invocation = resolution["value"]["backend_invocation"]
    invocation_schema = SCHEMAS["backend-invocation-input-v1"]
    request_schema = SCHEMAS["build-request-v0"]
    promoted_refs = {
        value["implementation_id"]: _reference(value, "implementation_id")
        for value in promoted["bindings"].values()
    }
    cross = core.load_json(ROOT / "contracts/task009/crossfader-mixed-legacy-v0-r2.json")
    promoted_refs[cross["implementation_id"]] = _reference(cross, "implementation_id")
    backend.validate_invocation_input(invocation, invocation_schema, request_schema, promoted_refs, promoted["request"])
    invocation_bytes = _canonical_bytes(invocation)
    _write_exact(EVIDENCE_ROOT / "backend-invocation-input.json", invocation_bytes + b"\n")

    rejection_cases = {}
    mutations = {
        "stale": lambda value: value["accepted_build_request"].update({"content_hash": "sha256:" + "0" * 64}),
        "extra": lambda value: value["selected_bindings"].append(copy.deepcopy(value["selected_bindings"][0])),
        "missing": lambda value: value["selected_bindings"].pop(),
        "unselected": lambda value: value["resolution_traces"][0].update({"status": "unresolved"}),
        "unsupported": lambda value: value["accepted_build_request"]["graph_reference"].update({"graph_id": "schuss-graph-999999"}),
        "ambiguous": lambda value: value["resolution_traces"][0].update({"status": "ambiguous"}),
    }
    for name, mutate in mutations.items():
        changed = copy.deepcopy(invocation)
        mutate(changed)
        output = BUILD_ROOT / f"rejected-{name}"
        try:
            backend.run_backend_handler(changed, invocation_schema, request_schema, promoted_refs, promoted["request"], config, output)
        except task009_backend.Task009BackendError as error:
            if output.exists():
                raise ValueError(f"rejected {name} invocation created an output root")
            rejection_cases[name] = error.code
        else:
            raise ValueError(f"handler accepted {name} invocation")
    _write_json(EVIDENCE_ROOT / "handler-rejections.json", {"schema_version": "task011c-handler-rejections-v0", "status": "passed", "cases": rejection_cases, "all_output_roots_absent": True})

    production_first = backend.run_backend_handler(invocation, invocation_schema, request_schema, promoted_refs, promoted["request"], config, BUILD_ROOT / "production-a")
    production_second = backend.run_backend_handler(invocation, invocation_schema, request_schema, promoted_refs, promoted["request"], config, BUILD_ROOT / "production-root-with-longer-name-b")
    production_equality = backend.compare_deterministic_outcomes(production_first, production_second)
    if production_first.status != "success" or production_first.resource_facts is None or not all(production_equality[key] for key in ("command_vectors_equal", "bridge_results_equal", "resource_facts_equal")):
        raise ValueError("production Task 011C execution was not deterministic")
    _retain_artifacts(production_first)
    closure = _production_closure(promoted)
    production_artifacts = _artifact_descriptors(production_first, PRODUCTION_ARTIFACT_IDS, _closure_hash(closure))
    resource = _resource_report(promoted, production_first.resource_facts)
    result = _build_result(promoted, production_artifacts, resource)
    production_claims = _production_evidence(result, promoted, production_artifacts, resource, producer_hash)

    final_plan = [*preliminary]
    final_plan.extend(("artifact", f"production-artifact-{index:02d}-{kind}.json", production_artifacts[kind]) for index, kind in enumerate(ARTIFACT_KINDS, 1))
    final_plan.extend([("resource", "gills-slice-static-resource.json", resource), ("result", "gills-slice-build-result.json", result)])
    final_plan.extend(("evidence", f"production-evidence-level-{claim['level']}.json", claim) for claim in production_claims)
    final_members = _write_records(final_plan)
    final_manifest = _record_set_manifest("schuss-record-set-000006", parent, final_members, True)
    _write_exact(SUCCESSOR_MANIFEST, task009_run._record_bytes(final_manifest))

    probe_equality = {"schema_version": "task011c-probe-fresh-root-equality-v0", "status": "passed", "baseline_probe": PROBE_IDS[ROLE_NAMES[0]], "comparisons": equalities}
    _write_json(EVIDENCE_ROOT / "probe-fresh-root-equality.json", probe_equality)
    _write_json(EVIDENCE_ROOT / "production-fresh-root-equality.json", production_equality)
    _write_json(EVIDENCE_ROOT / "probe-execution.json", _portable_outcome(first))
    _write_json(EVIDENCE_ROOT / "production-execution.json", _portable_outcome(production_first))
    _write_json(EVIDENCE_ROOT / "failure-injection.json", _run_failures(candidate_refs, config))
    _write_json(EVIDENCE_ROOT / "backend-invocation-seam.json", {
        "schema_version": "task011c-backend-invocation-seam-v0", "status": "passed",
        "operation_result_sha256": hashlib.sha256(canonical_result_bytes(resolution, context)).hexdigest(),
        "invocation_byte_length": len(invocation_bytes), "invocation_sha256": hashlib.sha256(invocation_bytes).hexdigest(),
        "selected_binding_references": list(invocation["selected_bindings"]), "handler_received_exact_bytes": True,
    })
    _write_json(EVIDENCE_ROOT / "evidence-level-status.json", {
        "schema_version": "task011c-evidence-level-status-v0",
        "levels": [{"level": level, "status": "passed" if level <= 5 else "not-run"} for level in range(1, 9)],
        "limitations": ["Level 6 connected-device execution was not run.", "Level 7 real-time resource validation was not run.", "Level 8 audible listening validation was not run."],
    })
    _write_json(EVIDENCE_ROOT / "completion-manifest.json", {
        "schema_version": "task011c-completion-manifest-v0", "status": "passed",
        "record_set": final_manifest,
        "probes": [{"input": _reference(probes[name], "conformance_probe_id"), "result": _reference(results[name], "conformance_probe_result_id"), "evidence": _reference(probe_evidence[name], "conformance_probe_evidence_id"), "promotion_claim": _reference(promotion_claims[name], "evidence_claim_id"), "promoted_binding": _reference(promoted["bindings"][name], "implementation_id"), "eligibility": _reference(promoted["eligibilities"][name], "binding_eligibility_id")} for name in ROLE_NAMES],
        "backend": _reference(promoted["backend"], "backend_id"), "request": _reference(promoted["request"], "build_request_id"),
        "production": {"result": _reference(result, "build_result_id"), "resource_report": _reference(resource, "resource_report_id"), "artifacts": [_reference(production_artifacts[k], "artifact_id") for k in ARTIFACT_KINDS], "evidence_claims": [_reference(claim, "evidence_claim_id") for claim in production_claims]},
        "artifact_bytes": {kind: {"byte_sha256": production_artifacts[kind]["byte_sha256"], "byte_length": production_artifacts[kind]["byte_length"]} for kind in ARTIFACT_KINDS},
        "evidence_levels": {"passed": [1, 2, 3, 4, 5], "not_run": [6, 7, 8]},
        "prohibited_actions": {"device_access": False, "firmware_installation": False, "real_time_measurement": False, "audible_procedure": False, "stage_commit_push": False, "upload_or_flash": False},
    })
    summary = validate()
    if summary["status"] != "valid":
        raise ValueError("Task 011C final validation did not pass")
    return summary


def validate() -> dict[str, Any]:
    if not SUCCESSOR_MANIFEST.is_file():
        raise ValueError("Task 011C successor record set is absent")
    selected = record_set_rules.load_record_set(ROOT, SUCCESSOR_MANIFEST)
    context = load_repository_context(ROOT, record_set_path=SUCCESSOR_MANIFEST)
    diagnostics: list[dict[str, Any]] = []
    if context.task007_summary["status"] != "valid":
        diagnostics.extend(context.task007_summary["diagnostics"])
    request = next(record for record in selected.records["request"] if record["build_request_id"] == "schuss-build-request-000002" and record["revision"] == 2)
    resolution = dispatch_operation({"schema_version": "schuss-operation-request-v1", "canonical_profile": "schuss-canonical-json-v1", "operation": "build.resolve", "payload": {"build_request_reference": _reference(request, "build_request_id")}}, context)
    final_invocation = resolution["value"].get("backend_invocation")
    selected_node_count = (
        len(final_invocation["selected_bindings"])
        if isinstance(final_invocation, dict) else 0
    )
    if resolution["status"] != "success" or selected_node_count != 8:
        diagnostics.append({"code": "TASK011C_FINAL_RESOLUTION_INVALID", "severity": "error", "subject": request["build_request_id"], "location": "$.build.resolve", "message": "final ordinary build.resolve did not select all eight nodes"})
    task_artifacts = [record for record in selected.records["artifact"] if int(record["artifact_id"].rsplit("-", 1)[1]) >= 15]
    for artifact in task_artifacts:
        path = ARTIFACT_STORE / artifact["byte_sha256"]
        if not path.is_file() or path.stat().st_size != artifact["byte_length"] or core.sha256_file(path) != artifact["byte_sha256"]:
            diagnostics.append({"code": "TASK011C_RETAINED_ARTIFACT_MISMATCH", "severity": "error", "subject": artifact["artifact_id"], "location": artifact["portable_locator"], "message": "retained artifact bytes differ"})
    registry = task009_run._probe_validation_registry(selected, [])
    procedure = next(record for record in selected.records["conformance-probe-procedure"] if record["procedure_id"] == backend.PROCEDURE_ID)
    environment = selected.records["prerequisite-environment"][0]
    for name in ROLE_NAMES:
        probe = next(record for record in selected.records["conformance-probe-input"] if record["conformance_probe_id"] == PROBE_IDS[name] and record["revision"] == 2)
        result = next(record for record in selected.records["conformance-probe-result"] if record["conformance_probe_result_id"] == RESULT_IDS[name])
        evidence = next(record for record in selected.records["conformance-probe-evidence"] if record["conformance_probe_evidence_id"] == PROBE_EVIDENCE_IDS[name])
        diagnostics.extend(item.as_dict() for item in prerequisite.validate_probe_values(probe, result, evidence, procedure, environment, registry))
    levels = sorted(claim["level"] for claim in selected.records["evidence"] if 13 <= int(claim["evidence_claim_id"].rsplit("-", 1)[1]) <= 17)
    if levels != [1, 2, 3, 4, 5]:
        diagnostics.append({"code": "TASK011C_EVIDENCE_LEVEL_SET_INVALID", "severity": "error", "subject": "task-011c", "location": "$.evidence", "message": "production evidence must contain levels 1 through 5"})
    for path in sorted(EVIDENCE_ROOT.rglob("*")):
        if path.is_file() and ARTIFACT_STORE not in path.parents:
            payload = path.read_bytes()
            if any(fragment in payload for fragment in (b"/Users/", b"/private/", b"/tmp/")):
                diagnostics.append({"code": "TASK011C_DURABLE_PATH_LEAK", "severity": "error", "subject": path.name, "location": path.relative_to(ROOT).as_posix(), "message": "durable evidence contains a local absolute path"})
    return {
        "schema_version": "task011c-validation-summary-v0",
        "status": "invalid" if diagnostics else "valid",
        "record_set_reference": selected.reference,
        "record_count": sum(len(values) for values in selected.records.values()),
        "task011c_record_count": sum(1 for member in selected.manifest["record_members"] if member["portable_path"].startswith("contracts/task011c/")),
        "artifact_count": len(task_artifacts), "build_resolution_status": resolution["status"],
        "selected_node_count": selected_node_count,
        "build_result_status": next(record for record in selected.records["result"] if record["build_result_id"] == "schuss-build-result-000002")["overall_status"],
        "probe_count": len(ROLE_NAMES), "evidence_levels_passed": levels,
        "evidence_levels_not_run": [6, 7, 8],
        "diagnostics": sorted(diagnostics, key=lambda item: (item["severity"], item["code"], item["subject"], item["location"])),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate retained Task 011C outputs without executing tools")
    args = parser.parse_args()
    try:
        summary = validate() if args.check else execute()
    except (OSError, ValueError, core.DuplicateJsonMemberError, record_set_rules.RecordSetError, task009_backend.Task009BackendError) as error:
        print(f"Task 011C failed: {error}", file=sys.stderr)
        return 1
    print(core.canonical_json(summary))
    return 0 if summary["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
