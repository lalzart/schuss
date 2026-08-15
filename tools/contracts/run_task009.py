#!/usr/bin/env python3
"""Execute or validate the bounded Task 009 deterministic backend proof."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools/contracts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from packages.schuss_core import (  # noqa: E402
    canonical_result_bytes,
    dispatch_operation,
    load_repository_context,
)

import record_set_rules  # noqa: E402
import target_backend_build_rules as target_rules  # noqa: E402
import task009_backend as backend  # noqa: E402
import task009_prerequisite_rules as prerequisite  # noqa: E402
import validator_core as core  # noqa: E402


TASK_RECORD_ROOT = ROOT / "contracts/task009"
EVIDENCE_ROOT = ROOT / "evidence/task-009-v1"
ARTIFACT_STORE = EVIDENCE_ROOT / "artifacts/sha256"
BUILD_ROOT = ROOT / "build/task009-v1-run5"
SUCCESSOR_MANIFEST = ROOT / "contracts/record-sets/task009-executed-prospective-v0.json"
PARENT_MANIFEST = ROOT / "contracts/record-sets/task009-prospective-v0.json"

JAVA = Path("/Applications/Ksoloti Local.app/Contents/Resources/jre/bin/java")
JAVAC = Path("/Applications/Ksoloti Local.app/Contents/Resources/jre/bin/javac")
ARM_BIN = Path("/Applications/Ksoloti Local.app/Contents/Resources/platform_mac_x64/bin")
PREREQUISITE_CONTENT_STORE = (
    ROOT / "build/task009-prerequisite-repair-v1/content-addressed"
)

SCHEMAS = {
    version: core.load_json(path)
    for path in sorted((ROOT / "schemas").glob("*.schema.json"))
    for version in [core.load_json(path)["$id"].removesuffix(".schema.json")]
}
SCHEMAS.update({
    version: core.load_json(path)
    for path in sorted((ROOT / "schemas/prerequisite").glob("*.schema.json"))
    for version in [core.load_json(path)["$id"].removesuffix(".schema.json")]
})

RECORD_FILES: dict[str, str] = {
    "probe-input": "authorized-probe-input-v0.json",
    "probe-result": "authorized-probe-result-v0.json",
    "probe-evidence": "authorized-probe-evidence-v0.json",
    "binding": "crossfader-mixed-legacy-v0-r2.json",
    "toolchain": "arm-none-eabi-v0-r2.json",
    "runtime": "ksoloti-runtime-abi-v0-r2.json",
    "target": "ksoloti-core-v0-r2.json",
    "backend": "legacy-ksoloti-v0-r2.json",
    "eligibility": "crossfader-mixed-legacy-eligibility-v0-r2.json",
    "request": "blend-validation-v0-r2.json",
    "resource": "blend-static-resource-v0.json",
    "result": "blend-build-result-v0.json",
}

ARTIFACT_KINDS = tuple(backend.ARTIFACT_ORDER)
PROBE_ARTIFACT_IDS = {
    kind: f"schuss-artifact-{index:06d}"
    for index, kind in enumerate(ARTIFACT_KINDS, 1)
}
PRODUCTION_ARTIFACT_IDS = {
    kind: f"schuss-artifact-{index:06d}"
    for index, kind in enumerate(ARTIFACT_KINDS, 8)
}

SOURCE_PATCHER = "08d3e6e1e2b61230308c20a15ded58ffdaf4656c"
SOURCE_FACTORY = "25d2615ed5233546d617017666a4ab1e60a8c506"


def _canonical_bytes(value: Any) -> bytes:
    return core.canonical_json(value).encode("utf-8")


def _write_exact(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != payload:
            raise ValueError(f"refusing to replace non-identical Task 009 output: {path}")
        return
    path.write_bytes(payload)


def _write_json(path: Path, value: Any) -> None:
    _write_exact(path, _canonical_bytes(value) + b"\n")


def _seal(record: dict[str, Any], schema_version: str) -> dict[str, Any]:
    schema = SCHEMAS[schema_version]
    result = copy.deepcopy(record)
    result["content_hash"] = core.record_content_hash(result, schema)
    errors = core.schema_errors(result, schema, schema)
    if errors:
        raise ValueError(f"{schema_version} record invalid: {errors}")
    return core.canonicalize_with_schema(result, schema, schema)


def _record_bytes(record: dict[str, Any]) -> bytes:
    schema = SCHEMAS[record["schema_version"]]
    value = core.canonicalize_with_schema(record, schema, schema)
    return _canonical_bytes(value) + b"\n"


def _reference(record: Mapping[str, Any], id_field: str) -> dict[str, Any]:
    return {
        id_field: record[id_field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def _generic_reference(
    record: Mapping[str, Any], id_field: str, record_kind: str | None = None
) -> dict[str, Any]:
    result = {
        "stable_id": record[id_field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }
    if record_kind is not None:
        result["record_kind"] = record_kind
    return result


def _closure_hash(references: Iterable[dict[str, Any]]) -> str:
    values = list(references)
    ordered = sorted(values, key=core.canonical_json)
    return "sha256:" + hashlib.sha256(_canonical_bytes(ordered)).hexdigest()


def _source(
    source_id: str, commit: str, path: str, digest: str, claim_kind: str
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "commit": commit,
        "path": path,
        "byte_sha256": digest,
        "claim_kind": claim_kind,
    }


def _producer_identity(kind: str, identifier: str, content_hash: str) -> dict[str, Any]:
    return {
        "producer_kind": kind,
        "producer_id": identifier,
        "version": "task009-v1",
        "content_hash": content_hash,
    }


def _execution_config() -> backend.ExecutionConfig:
    return backend.ExecutionConfig(
        ROOT,
        PREREQUISITE_CONTENT_STORE,
        JAVA,
        JAVAC,
        ARM_BIN,
    )


def _verify_preflight() -> dict[str, Any]:
    accepted = record_set_rules.load_record_set(
        ROOT, record_set_rules.ACCEPTED_RECORD_SET
    )
    parent = record_set_rules.load_record_set(ROOT, PARENT_MANIFEST)
    expected_accepted = {
        "record_set_id": "schuss-record-set-000001",
        "revision": 1,
        "content_hash": "sha256:f3fde23e7410a0a78c79ffdbcf3741995cedbf69f41c5a47e596ac39a2ac62f6",
    }
    expected_parent = {
        "record_set_id": "schuss-record-set-000002",
        "revision": 1,
        "content_hash": "sha256:6f2855c384ef8bab88991a6cabdd8416c7f3c59a010eed0c6cda1ac08651ecaf",
    }
    if accepted.reference != expected_accepted or parent.reference != expected_parent:
        raise ValueError("Task 009 record-set preflight identity mismatch")

    prerequisite_summary = prerequisite.validate_task009_prerequisite(ROOT)
    if prerequisite_summary["status"] != "valid":
        raise ValueError("Task 009 prerequisite validator is not valid")
    if prerequisite_summary["probe"]["overall_status"] != "not-run":
        raise ValueError("retained prerequisite probe is no longer not-run")

    repair_manifest = core.load_json(
        ROOT / "evidence/task-009-prerequisite-repair-v1/repair-evidence-manifest.json"
    )
    for member in repair_manifest["members"]:
        path = ROOT / member["portable_path"]
        if (
            not path.is_file()
            or path.stat().st_size != member["byte_length"]
            or core.sha256_file(path) != member["byte_sha256"]
        ):
            raise ValueError(f"repair evidence mismatch: {member['portable_path']}")
    retained = core.load_json(
        ROOT / "evidence/task-009-prerequisite-repair-v1/retained-products.json"
    )
    for product in retained["products"]:
        path = PREREQUISITE_CONTENT_STORE / "sha256" / product["byte_sha256"]
        if (
            not path.is_file()
            or path.stat().st_size != product["byte_length"]
            or core.sha256_file(path) != product["byte_sha256"]
        ):
            raise ValueError(f"retained product mismatch: {product['kind']}")
    backend.verify_execution_config(_execution_config())

    default_context = load_repository_context(ROOT)
    fixture = core.load_json(
        ROOT / "tools/contracts/tests/fixtures/task008-operation-requests.json"
    )["build_resolve"]
    unresolved = dispatch_operation(fixture, default_context)
    unresolved_bytes = canonical_result_bytes(unresolved, default_context)
    reasons = unresolved["value"]["resolution_traces"][0]["candidates"][0]
    actual_reasons = sorted(
        reasons["exclusion_reasons"] + reasons["unresolved_reasons"]
    )
    expected_reasons = sorted([
        "BINDING_TARGET_BACKEND_PAIR_NOT_EVALUATED",
        "CAPABILITY_UNRESOLVED:audio-stream-fixed-q27",
        "CAPABILITY_UNRESOLVED:control-stream-fixed-q27",
        "COMPATIBILITY_EVIDENCE_MISSING",
    ])
    if (
        unresolved["status"] != "unresolved"
        or unresolved["value"]["backend_invocation"] is not None
        or actual_reasons != expected_reasons
        or len(unresolved_bytes) != 1367
        or hashlib.sha256(unresolved_bytes).hexdigest()
        != "643a063d1553ff000a4776fd2a4eb5b7d300c0ba34ccbb977f3babd78abf7de9"
    ):
        raise ValueError("revision-1 production build trace changed before Task 009")

    report = {
        "schema_version": "task009-preflight-equality-v1",
        "status": "passed",
        "accepted_record_set": accepted.reference,
        "prerequisite_record_set": parent.reference,
        "prerequisite_environment": {
            "prerequisite_environment_id": backend.ENVIRONMENT_ID,
            "revision": 1,
            "content_hash": backend.ENVIRONMENT_HASH,
        },
        "prerequisite_validator": {
            "status": "valid",
            "probe_authorization": "not-authorized",
            "probe_status": "not-run",
        },
        "repair_evidence": {
            "member_count": repair_manifest["member_count"],
            "all_members_exact": True,
            "retained_product_count": len(retained["products"]),
            "all_retained_products_exact": True,
        },
        "revision_1_build_resolution": {
            "status": "unresolved",
            "backend_invocation_present": False,
            "canonical_byte_length": len(unresolved_bytes),
            "canonical_sha256": hashlib.sha256(unresolved_bytes).hexdigest(),
            "reasons": expected_reasons,
        },
        "execution_identities": {
            "java": backend.JAVA_SHA256,
            "javac": backend.JAVAC_SHA256,
            "arm_components": dict(sorted(backend.ARM_COMPONENTS.items())),
            "firmware_bin": backend.FIRMWARE_BIN_SHA256,
            "firmware_link_elf": backend.FIRMWARE_ELF_SHA256,
            "patcher_archive": backend.PATCHER_ARCHIVE_SHA256,
            "factory_archive": backend.FACTORY_ARCHIVE_SHA256,
            "compiled_classes": backend.CLASS_ARCHIVE_SHA256,
        },
        "prohibited_actions": {
            "device_access": False,
            "firmware_action": False,
            "network_access": False,
            "upstream_mutation": False,
        },
    }
    _write_json(EVIDENCE_ROOT / "preflight-equality.json", report)
    return report


def _authorized_probe() -> dict[str, Any]:
    value = core.load_json(ROOT / "contracts/prerequisite/task009/probe-input-v0.json")
    value["conformance_probe_id"] = "schuss-conformance-probe-000002"
    value["revision"] = 1
    value["execution_authorization"] = "task-009-authorized"
    value["content_hash"] = "sha256:" + "0" * 64
    return _seal(value, "conformance-probe-input-v0")


def _retain_artifacts(outcome: backend.ExecutionOutcome) -> None:
    for fact in outcome.artifacts:
        destination = ARTIFACT_STORE / fact.byte_sha256
        if destination.exists():
            if core.sha256_file(destination) != fact.byte_sha256:
                raise ValueError("Task 009 artifact store hash collision")
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(fact.retained_path, destination)
            destination.chmod(0o444)


def _artifact_descriptors(
    outcome: backend.ExecutionOutcome,
    artifact_ids: Mapping[str, str],
    input_closure_hash: str,
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
        "resolution-plan": (),
        "legacy-boundary-patch": (),
        "source-map": (),
        "generated-cpp": ("source-map",),
        "arm-object": ("source-map",),
        "target-executable": ("source-map",),
        "link-map": ("source-map",),
    }
    records: dict[str, dict[str, Any]] = {}
    for kind in ARTIFACT_KINDS:
        fact = facts[kind]
        record = {
            "schema_version": "artifact-descriptor-v0",
            "canonical_profile": "schuss-canonical-json-v1",
            "artifact_id": artifact_ids[kind],
            "revision": 1,
            "content_hash": "sha256:" + "0" * 64,
            "artifact_kind": kind,
            "media_type": fact.media_type,
            "byte_length": fact.byte_length,
            "byte_sha256": fact.byte_sha256,
            "producer_stage": fact.producer_stage,
            "producer_contract": {
                "producer_id": "schuss-task009-backend",
                "producer_version": "task009-v1",
            },
            "input_closure_hash": input_closure_hash,
            "portable_locator": fact.portable_locator,
            "parent_artifact_references": [
                _reference(records[parent], "artifact_id")
                for parent in parents[kind]
            ],
            "source_map_artifact_references": [
                _reference(records[source_map], "artifact_id")
                for source_map in source_maps[kind]
            ],
        }
        records[kind] = _seal(record, "artifact-descriptor-v0")
    return records


def _probe_result(
    probe: dict[str, Any],
    outcome: backend.ExecutionOutcome,
    artifacts: Mapping[str, dict[str, Any]],
) -> dict[str, Any]:
    by_stage = {
        "backend-lowering": ("resolution-plan",),
        "artifact-generation": (
            "legacy-boundary-patch", "source-map", "generated-cpp",
        ),
        "target-compile-link": (
            "arm-object", "target-executable", "link-map",
        ),
    }
    stage_outcomes = []
    for ordinal, (stage, status) in enumerate(outcome.stage_statuses, 1):
        stage_outcomes.append({
            "ordinal": ordinal,
            "stage": stage,
            "status": status,
            "diagnostic_ids": [
                item["diagnostic_id"]
                for item in outcome.diagnostics
                if item["stage"] == stage
            ],
            "artifact_references": [
                _reference(artifacts[kind], "artifact_id")
                for kind in by_stage[stage]
                if kind in artifacts and status == "success"
            ],
        })
    value = {
        "schema_version": "conformance-probe-result-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "conformance_probe_result_id": "schuss-conformance-probe-result-000002",
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "probe_reference": _reference(probe, "conformance_probe_id"),
        "candidate_state": "candidate-under-test",
        "binding_reference": copy.deepcopy(probe["binding_reference"]),
        "environment_reference": copy.deepcopy(probe["environment_reference"]),
        "stage_outcomes": stage_outcomes,
        "diagnostics": list(outcome.diagnostics),
        "artifact_references": [
            _reference(artifacts[kind], "artifact_id")
            for kind in ARTIFACT_KINDS
            if kind in artifacts
        ],
        "overall_status": outcome.status,
        "production_selection_authority": False,
    }
    return _seal(value, "conformance-probe-result-v0")


def _probe_evidence(
    probe: dict[str, Any], result: dict[str, Any]
) -> dict[str, Any]:
    value = {
        "schema_version": "conformance-probe-evidence-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "conformance_probe_evidence_id": "schuss-conformance-probe-evidence-000002",
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "probe_result_reference": _reference(
            result, "conformance_probe_result_id"
        ),
        "binding_reference": copy.deepcopy(probe["binding_reference"]),
        "procedure_reference": copy.deepcopy(probe["procedure_reference"]),
        "outcome": "passed" if result["overall_status"] == "success" else "failed",
        "evidence_level": 5 if result["overall_status"] == "success" else 1,
        "limitations": [
            "The probe grants no production selection authority by itself.",
            "No connected-device, real-time, or audible procedure ran.",
        ],
    }
    return _seal(value, "conformance-probe-evidence-v0")


def _promotion_claim(
    probe_evidence: dict[str, Any], producer_hash: str
) -> dict[str, Any]:
    value = {
        "schema_version": "evidence-claim-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "evidence_claim_id": "schuss-evidence-claim-000001",
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
            {
                "input_kind": "semantic-record",
                "stable_id": backend.BINDING_ID,
                "revision": 1,
                "content_hash": backend.BINDING_R1_HASH,
            },
            {
                "input_kind": "semantic-record",
                **_generic_reference(
                    probe_evidence, "conformance_probe_evidence_id"
                ),
            },
        ],
        "limitations": [
            "The claim is bounded to the exact one-node mixed Crossfader graph slice.",
            "It establishes no connected-device, real-time, or audible behavior.",
        ],
        "producer_identity": _producer_identity(
            "validator", "schuss-task009-probe-validator", producer_hash
        ),
    }
    return _seal(value, "evidence-claim-v0")


def _promoted_records(
    probe_evidence: dict[str, Any], promotion_claim: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    makefile = _source(
        "patcher", SOURCE_PATCHER, "firmware/Makefile.patch.mk",
        "ab99b15be913083220621a785077945e6b35fe56fc7c2691afe36569a8f29a70",
        "build-declared",
    )
    defines = _source(
        "patcher", SOURCE_PATCHER, "firmware/axoloti_defines.h",
        "325f034f77b83139eabb48c9712fac039773ebef1ccf99ec62c461c8a035cc70",
        "source-declared",
    )
    xpatch = _source(
        "patcher", SOURCE_PATCHER, "firmware/xpatch.h",
        "85e4abc70123952e8f47217751f2b6f7299e7cb978b6c994acf7b383425379a0",
        "source-declared",
    )
    ramlink = _source(
        "patcher", SOURCE_PATCHER, "firmware/ramlink_ksoloti.ld",
        "08ead427e297a4d66ea2b8d830563e7a2d8c683ad399c0809477b584eb70b1eb",
        "linker-declared",
    )
    arm_math = _source(
        "patcher", SOURCE_PATCHER, "CMSIS/DSP/Include/arm_math.h",
        "365cff31690de977e64597c385d28cce73edd1cbc5890943b537cf98fdbce4d0",
        "source-declared",
    )
    xfade = _source(
        "axoloti-factory", SOURCE_FACTORY, "objects/mix/xfade.axo",
        "8169f5ec39eabe8f76bf5025ab2c68df0bed531c0c8aeb8c51bba3307859e361",
        "source-declared",
    )

    binding = core.load_json(
        ROOT / "contracts/implementation-bindings/crossfader-mixed-legacy-v0.json"
    )
    binding["revision"] = 2
    binding["content_hash"] = "sha256:" + "0" * 64
    binding = _seal(binding, "implementation-binding-v0")

    toolchain = core.load_json(
        ROOT / "contracts/build-environments/arm-none-eabi-unresolved-v0.json"
    )
    toolchain["revision"] = 2
    toolchain["content_hash"] = "sha256:" + "0" * 64
    toolchain["identity"] = {
        "status": "supported",
        "identity_kind": "gnu-arm-embedded",
        "version": "9-2020-q2-update",
        "target_triple": "arm-none-eabi",
        "component_hashes": [
            {"component": "arm-assembler", "sha256": backend.ARM_COMPONENTS["arm-none-eabi-as"]},
            {"component": "arm-c-compiler", "sha256": backend.ARM_COMPONENTS["arm-none-eabi-gcc"]},
            {"component": "arm-cxx-compiler", "sha256": backend.ARM_COMPONENTS["arm-none-eabi-g++"]},
            {"component": "arm-linker", "sha256": backend.ARM_COMPONENTS["arm-none-eabi-ld"]},
            {"component": "arm-objcopy", "sha256": backend.ARM_COMPONENTS["arm-none-eabi-objcopy"]},
            {"component": "arm-objdump", "sha256": backend.ARM_COMPONENTS["arm-none-eabi-objdump"]},
            {"component": "arm-size", "sha256": backend.ARM_COMPONENTS["arm-none-eabi-size"]},
        ],
        "compatibility_boundary": (
            "Exact Cortex-M4 Thumb hard-float FPv4-SP-D16 compile and link "
            "closure used by the bounded Task 009 slice."
        ),
        "portable_locator": "sha256/" + backend.ARM_COMPONENTS["arm-none-eabi-as"],
        "evidence_refs": copy.deepcopy(
            core.load_json(
                ROOT / "contracts/build-environments/arm-none-eabi-unresolved-v0.json"
            )["identity"]["evidence_refs"]
        ),
    }
    toolchain = _seal(toolchain, "build-environment-v0")

    runtime = core.load_json(
        ROOT / "contracts/build-environments/ksoloti-runtime-abi-unresolved-v0.json"
    )
    runtime["revision"] = 2
    runtime["content_hash"] = "sha256:" + "0" * 64
    runtime["identity"] = {
        "status": "supported",
        "identity_kind": "ksoloti-firmware-runtime",
        "version": "1.1.0.0",
        "target_triple": "arm-none-eabi",
        "component_hashes": [
            {"component": "firmware-bin", "sha256": backend.FIRMWARE_BIN_SHA256},
            {"component": "firmware-link-elf", "sha256": backend.FIRMWARE_ELF_SHA256},
            {"component": "firmware-source-capsule", "sha256": backend.PATCHER_ARCHIVE_SHA256},
            {"component": "firmware-source-input-manifest", "sha256": "5383ff90ba44bc5540f48f3fffed38438f58ea81173feaea05608c94721d02aa"},
            {"component": "firmware-symbol-manifest", "sha256": "323589fbae0aa6600a417b14c3c764ff6c23c0eb41698e09172ced5419772366"},
            {"component": "runtime-defines-header", "sha256": defines["byte_sha256"]},
            {"component": "runtime-linker-script", "sha256": ramlink["byte_sha256"]},
            {"component": "runtime-makefile", "sha256": makefile["byte_sha256"]},
            {"component": "runtime-xpatch-header", "sha256": xpatch["byte_sha256"]},
        ],
        "compatibility_boundary": (
            "Exact stripped firmware link ELF, canonical firmware bytes, pinned "
            "headers, linker script, and source capsule used for Task 009 linking."
        ),
        "portable_locator": "sha256/" + backend.FIRMWARE_BIN_SHA256,
        "evidence_refs": [
            *copy.deepcopy(
                core.load_json(
                    ROOT / "contracts/build-environments/ksoloti-runtime-abi-unresolved-v0.json"
                )["identity"]["evidence_refs"]
            ),
            makefile,
            ramlink,
            xpatch,
        ],
    }
    runtime = _seal(runtime, "build-environment-v0")

    target = core.load_json(ROOT / "contracts/compute-targets/ksoloti-core-v0.json")
    target["revision"] = 2
    target["content_hash"] = "sha256:" + "0" * 64
    target["firmware_runtime_reference"] = _reference(
        runtime, "build_environment_id"
    )
    target["abi_constraints"]["endianness"] = {
        "status": "supported",
        "value": "little",
        "evidence_refs": [arm_math, makefile],
    }
    target["capability_declarations"] = [
        {
            "capability_key": key,
            "state": {
                "status": "supported",
                "value": True,
                "evidence_level": 5,
                "evidence_refs": [defines, xfade, xpatch],
            },
        }
        for key in (
            "audio-stream-fixed-q27",
            "control-stream-fixed-q27",
        )
    ]
    target = _seal(target, "compute-target-v0")

    backend_record = core.load_json(ROOT / "contracts/backends/legacy-ksoloti-v0.json")
    backend_record["revision"] = 2
    backend_record["content_hash"] = "sha256:" + "0" * 64
    backend_record["toolchain_reference"] = _reference(
        toolchain, "build_environment_id"
    )
    backend_record["firmware_runtime_reference"] = _reference(
        runtime, "build_environment_id"
    )
    backend_record["target_pairings"] = [{
        "target_reference": _reference(target, "compute_target_id"),
        "contract_state": "declared",
        "rationale": (
            "The authorized exact-slice probe established the bounded source "
            "generation and ARM compile/link path for this exact pairing."
        ),
    }]
    backend_record["permitted_stopping_stages"] = [
        *backend_record["permitted_stopping_stages"],
        "artifact-generation",
        "backend-lowering",
        "target-compile-link",
    ]
    backend_record = _seal(backend_record, "backend-v0")

    eligibility = core.load_json(
        ROOT / "contracts/binding-eligibility/crossfader-mixed-legacy-v0.json"
    )
    eligibility["revision"] = 2
    eligibility["content_hash"] = "sha256:" + "0" * 64
    eligibility["binding_reference"] = _reference(binding, "implementation_id")
    eligibility["allowed_pair"] = {
        "target_reference": _reference(target, "compute_target_id"),
        "backend_reference": _reference(backend_record, "backend_id"),
        "state": {
            "status": "supported",
            "evidence_level": 2,
            "evidence_refs": [_reference(promotion_claim, "evidence_claim_id")],
        },
    }
    eligibility["compatibility_evidence"] = [
        _reference(promotion_claim, "evidence_claim_id")
    ]
    eligibility["unresolved_questions"] = []
    eligibility = _seal(eligibility, "binding-eligibility-v0")

    request = core.load_json(ROOT / "contracts/build-requests/blend-validation-v0.json")
    request["revision"] = 2
    request["content_hash"] = "sha256:" + "0" * 64
    request["compute_target_reference"] = _reference(target, "compute_target_id")
    request["backend_reference"] = _reference(backend_record, "backend_id")
    request["requested_stopping_stage"] = "target-compile-link"
    request = _seal(request, "build-request-v0")

    return {
        "binding": binding,
        "toolchain": toolchain,
        "runtime": runtime,
        "target": target,
        "backend": backend_record,
        "eligibility": eligibility,
        "request": request,
        "probe-evidence": probe_evidence,
    }


def _stable_id(record: Mapping[str, Any]) -> str:
    values = [record[field] for field in record_set_rules.ID_FIELDS if field in record]
    if len(values) != 1:
        raise ValueError("Task 009 record must expose exactly one stable ID")
    return values[0]


def _schema_member(member: Mapping[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(dict(member))


def _record_member(
    kind: str, portable_path: str, record: Mapping[str, Any]
) -> dict[str, Any]:
    path = ROOT / portable_path
    return {
        "record_kind": kind,
        "stable_id": _stable_id(record),
        "revision": record["revision"],
        "content_hash": record["content_hash"],
        "portable_path": portable_path,
        "byte_sha256": core.sha256_file(path),
    }


def _record_set_manifest(
    record_set_id: str,
    parent: record_set_rules.LoadedRecordSet,
    new_members: Iterable[dict[str, Any]],
    enforced_task_directory: bool,
) -> dict[str, Any]:
    value = {
        "schema_version": "record-set-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "record_set_id": record_set_id,
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "purpose": "prospective-task",
        "parent_reference": {"status": "included", **parent.reference},
        "schema_members": [
            _schema_member(member) for member in parent.manifest["schema_members"]
        ],
        "record_members": [
            *copy.deepcopy(parent.manifest["record_members"]),
            *copy.deepcopy(list(new_members)),
        ],
        "enforced_directories": [
            *copy.deepcopy(parent.manifest["enforced_directories"]),
            *(["contracts/task009"] if enforced_task_directory else []),
        ],
    }
    return _seal(value, "record-set-v0")


def _write_records(
    records: Iterable[tuple[str, str, dict[str, Any]]]
) -> list[dict[str, Any]]:
    members = []
    for kind, filename, record in records:
        path = TASK_RECORD_ROOT / filename
        _write_exact(path, _record_bytes(record))
        members.append(
            _record_member(kind, path.relative_to(ROOT).as_posix(), record)
        )
    return members


def _input_closure(promoted: Mapping[str, dict[str, Any]]) -> list[dict[str, Any]]:
    records = [
        (
            "catalog-family",
            core.load_json(ROOT / "contracts/catalog-families/crossfader-v1.json"),
            "family_id",
        ),
        (
            "component-contract",
            core.load_json(
                ROOT / "contracts/component-contracts/crossfader-mixed-v0.json"
            ),
            "component_contract_id",
        ),
        ("implementation-binding", promoted["binding"], "implementation_id"),
        (
            "dsp-graph",
            core.load_json(ROOT / "contracts/graphs/blend-crossfader-v0.json"),
            "graph_id",
        ),
        (
            "device-profile",
            core.load_json(ROOT / "contracts/device-profiles/gills-minimal-v0.json"),
            "device_profile_id",
        ),
        (
            "instrument",
            core.load_json(ROOT / "contracts/instruments/blend-reference-v0-r2.json"),
            "instrument_id",
        ),
        (
            "capability-vocabulary",
            core.load_json(ROOT / "contracts/capabilities/task007-v0.json"),
            "capability_vocabulary_id",
        ),
        ("build-environment", promoted["toolchain"], "build_environment_id"),
        ("build-environment", promoted["runtime"], "build_environment_id"),
        ("compute-target", promoted["target"], "compute_target_id"),
        ("backend", promoted["backend"], "backend_id"),
        ("binding-eligibility", promoted["eligibility"], "binding_eligibility_id"),
        ("build-request", promoted["request"], "build_request_id"),
    ]
    return [
        _generic_reference(record, id_field, kind)
        for kind, record, id_field in records
    ]


def _resource_amounts(resource_facts: Mapping[str, Any]) -> dict[str, int]:
    amounts = {"code": 0, "read-only-data": 0, "data": 0}
    for line in resource_facts["size_output"]:
        parts = line.split()
        if len(parts) != 3 or not parts[1].startswith("0x") or not parts[2].startswith("0x"):
            continue
        name, size_text, address_text = parts
        size = int(size_text, 16)
        address = int(address_text, 16)
        if size == 0:
            continue
        if 0x10000000 <= address < 0x1000C800:
            amounts["data"] += size
        elif 0x00011000 <= address < 0x0001C000:
            amounts["code" if name.startswith(".text") else "read-only-data"] += size
    if not all(amounts.values()):
        raise ValueError(f"incomplete Task 009 static resource facts: {amounts}")
    return amounts


def _resource_report(
    promoted: Mapping[str, dict[str, Any]], resource_facts: Mapping[str, Any]
) -> dict[str, Any]:
    amounts = _resource_amounts(resource_facts)
    observations = [
        {
            "observation_id": "resource-observation-000001",
            "observation_kind": "compiler-link-map-observation",
            "resource_kind": "code",
            "region_id": "target-memory-region-000002",
            "amount_bytes": amounts["code"],
            "alignment_bytes": 4,
            "unit": "bytes",
            "method": "compiler-link-map",
            "evidence_level": 5,
        },
        {
            "observation_id": "resource-observation-000002",
            "observation_kind": "compiler-link-map-observation",
            "resource_kind": "read-only-data",
            "region_id": "target-memory-region-000002",
            "amount_bytes": amounts["read-only-data"],
            "alignment_bytes": 4,
            "unit": "bytes",
            "method": "compiler-link-map",
            "evidence_level": 5,
        },
        {
            "observation_id": "resource-observation-000003",
            "observation_kind": "compiler-link-map-observation",
            "resource_kind": "data",
            "region_id": "target-memory-region-000001",
            "amount_bytes": amounts["data"],
            "alignment_bytes": 4,
            "unit": "bytes",
            "method": "compiler-link-map",
            "evidence_level": 5,
        },
    ]
    value = {
        "schema_version": "resource-report-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "resource_report_id": "schuss-resource-report-000001",
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "subject_reference": {
            "subject_kind": "build-request",
            **_generic_reference(promoted["request"], "build_request_id"),
        },
        "compute_target_reference": _reference(
            promoted["target"], "compute_target_id"
        ),
        "observations": observations,
        "budget_comparisons": [
            {
                "comparison_id": "resource-comparison-000001",
                "observation_ids": [
                    "resource-observation-000001",
                    "resource-observation-000002",
                ],
                "region_id": "target-memory-region-000002",
                "budget_bytes": 45056,
                "total_aligned_amount_bytes": (
                    amounts["code"] + amounts["read-only-data"]
                ),
                "outcome": "within-budget",
            },
            {
                "comparison_id": "resource-comparison-000002",
                "observation_ids": ["resource-observation-000003"],
                "region_id": "target-memory-region-000001",
                "budget_bytes": 51200,
                "total_aligned_amount_bytes": amounts["data"],
                "outcome": "within-budget",
            },
        ],
    }
    return _seal(value, "resource-report-v0")


def _build_result(
    promoted: Mapping[str, dict[str, Any]],
    artifacts: Mapping[str, dict[str, Any]],
    resource: dict[str, Any],
) -> dict[str, Any]:
    closure = _input_closure(promoted)
    artifact_refs = [
        _reference(artifacts[kind], "artifact_id") for kind in ARTIFACT_KINDS
    ]
    resource_ref = _reference(resource, "resource_report_id")
    by_stage = {
        "implementation-resolution": ["resolution-plan"],
        "artifact-generation": [
            "legacy-boundary-patch", "source-map", "generated-cpp",
        ],
        "target-compile-link": [
            "arm-object", "target-executable", "link-map",
        ],
    }
    outcomes = []
    for ordinal, stage in enumerate(target_rules.STAGES, 1):
        before_or_at_stop = ordinal <= target_rules.STAGES.index(
            "target-compile-link"
        ) + 1
        outcomes.append({
            "ordinal": ordinal,
            "stage": stage,
            "status": "success" if before_or_at_stop else "not-run",
            "diagnostic_ids": [],
            "artifact_references": [
                _reference(artifacts[kind], "artifact_id")
                for kind in by_stage.get(stage, [])
            ] if before_or_at_stop else [],
            "resource_report_references": [resource_ref]
            if stage == "target-compile-link" else [],
        })
    value = {
        "schema_version": "build-result-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "build_result_id": "schuss-build-result-000001",
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "request_reference": _reference(promoted["request"], "build_request_id"),
        "input_closure": closure,
        "input_closure_hash": _closure_hash(closure),
        "selected_bindings": [{
            "node_id": "graph-node-000001",
            "binding_reference": _reference(promoted["binding"], "implementation_id"),
            "eligibility_reference": _reference(
                promoted["eligibility"], "binding_eligibility_id"
            ),
            "selection_policy_id": promoted["eligibility"]["selection_policy"]["policy_id"],
        }],
        "compute_target_reference": _reference(
            promoted["target"], "compute_target_id"
        ),
        "backend_reference": _reference(promoted["backend"], "backend_id"),
        "toolchain_reference": _reference(
            promoted["toolchain"], "build_environment_id"
        ),
        "firmware_runtime_reference": _reference(
            promoted["runtime"], "build_environment_id"
        ),
        "options_used": copy.deepcopy(promoted["request"]["options"]),
        "stage_outcomes": outcomes,
        "diagnostics": [],
        "artifact_references": artifact_refs,
        "resource_report_references": [resource_ref],
        "overall_status": "success",
    }
    return _seal(value, "build-result-v0")


def _production_evidence(
    result: dict[str, Any],
    promoted: Mapping[str, dict[str, Any]],
    artifacts: Mapping[str, dict[str, Any]],
    resource: dict[str, Any],
    producer_hash: str,
) -> list[dict[str, Any]]:
    result_input = {
        "input_kind": "build-result",
        **_generic_reference(result, "build_result_id"),
    }
    specifications = [
        (
            1, "structural-schema-validation", "schema-identity-validation",
            "validator", "schuss-task009-contract-validator",
            "closed-schema-and-exact-identity-validation", [result_input],
            ["Structural validity does not imply backend or device execution."],
        ),
        (
            2, "component-graph-resolution", "target-independent-graph-validation",
            "validator", "schuss-task009-resolution-validator",
            "ordinary-build-resolve-selection", [
                result_input,
                {
                    "input_kind": "semantic-record",
                    **_generic_reference(
                        promoted["probe-evidence"],
                        "conformance_probe_evidence_id",
                    ),
                },
            ],
            ["Resolution is bounded to the exact Blend graph and promoted pair."],
        ),
        (
            3, "backend-lowering", "backend-lowering",
            "backend", "schuss-task009-backend",
            "exact-slice-lowering", [
                result_input,
                {
                    "input_kind": "artifact",
                    **_generic_reference(
                        artifacts["resolution-plan"], "artifact_id"
                    ),
                },
            ],
            ["Lowering supports no graph other than the exact one-node Blend slice."],
        ),
        (
            4, "source-artifact-generation", "artifact-generation",
            "backend", "schuss-task009-backend",
            "isolated-legacy-source-generation", [
                result_input,
                *[
                    {
                        "input_kind": "artifact",
                        **_generic_reference(artifacts[kind], "artifact_id"),
                    }
                    for kind in (
                        "legacy-boundary-patch", "source-map", "generated-cpp",
                    )
                ],
            ],
            ["Generated source was not run on a connected device."],
        ),
        (
            5, "arm-compilation-linking", "target-compile-link",
            "toolchain", "gnu-arm-embedded-task009",
            "exact-arm-compile-link", [
                result_input,
                *[
                    {
                        "input_kind": "artifact",
                        **_generic_reference(artifacts[kind], "artifact_id"),
                    }
                    for kind in ("arm-object", "target-executable", "link-map")
                ],
                {
                    "input_kind": "resource-report",
                    **_generic_reference(resource, "resource_report_id"),
                },
            ],
            [
                "Compile and link success is not connected-device execution.",
                "Static linker observations are not real-time resource measurements.",
                "No audible procedure ran.",
            ],
        ),
    ]
    claims = []
    for level, name, stage, producer_kind, producer_id, method, inputs, limitations in specifications:
        value = {
            "schema_version": "evidence-claim-v0",
            "canonical_profile": "schuss-canonical-json-v1",
            "evidence_claim_id": f"schuss-evidence-claim-{level + 1:06d}",
            "revision": 1,
            "content_hash": "sha256:" + "0" * 64,
            "level": level,
            "level_name": name,
            "subject_reference": {
                "subject_kind": "build-result" if level == 1 else "build-stage",
                **_generic_reference(result, "build_result_id"),
                "stage": stage,
            },
            "method": method,
            "outcome": "passed",
            "evidence_inputs": copy.deepcopy(inputs),
            "limitations": limitations,
            "producer_identity": _producer_identity(
                producer_kind, producer_id, producer_hash
            ),
        }
        claims.append(_seal(value, "evidence-claim-v0"))
    return claims


def _record_plan(
    probe: dict[str, Any],
    probe_result: dict[str, Any],
    probe_evidence: dict[str, Any],
    probe_artifacts: Mapping[str, dict[str, Any]],
    promotion_claim: dict[str, Any],
    promoted: Mapping[str, dict[str, Any]],
    production_artifacts: Mapping[str, dict[str, Any]] | None = None,
    resource: dict[str, Any] | None = None,
    result: dict[str, Any] | None = None,
    production_claims: Iterable[dict[str, Any]] = (),
) -> list[tuple[str, str, dict[str, Any]]]:
    records: list[tuple[str, str, dict[str, Any]]] = [
        ("conformance-probe-input", RECORD_FILES["probe-input"], probe),
        ("conformance-probe-result", RECORD_FILES["probe-result"], probe_result),
        ("conformance-probe-evidence", RECORD_FILES["probe-evidence"], probe_evidence),
        ("implementation-binding", RECORD_FILES["binding"], promoted["binding"]),
        ("environment", RECORD_FILES["toolchain"], promoted["toolchain"]),
        ("environment", RECORD_FILES["runtime"], promoted["runtime"]),
        ("target", RECORD_FILES["target"], promoted["target"]),
        ("backend", RECORD_FILES["backend"], promoted["backend"]),
        ("eligibility", RECORD_FILES["eligibility"], promoted["eligibility"]),
        ("request", RECORD_FILES["request"], promoted["request"]),
        ("evidence", "probe-promotion-evidence-v0.json", promotion_claim),
    ]
    records.extend(
        (
            "artifact",
            f"probe-artifact-{index:02d}-{kind}.json",
            probe_artifacts[kind],
        )
        for index, kind in enumerate(ARTIFACT_KINDS, 1)
    )
    if production_artifacts is not None:
        records.extend(
            (
                "artifact",
                f"production-artifact-{index:02d}-{kind}.json",
                production_artifacts[kind],
            )
            for index, kind in enumerate(ARTIFACT_KINDS, 1)
        )
    if resource is not None:
        records.append(("resource", RECORD_FILES["resource"], resource))
    if result is not None:
        records.append(("result", RECORD_FILES["result"], result))
    records.extend(
        ("evidence", f"production-evidence-level-{claim['level']}.json", claim)
        for claim in production_claims
    )
    return records


def _probe_validation_registry(
    parent: record_set_rules.LoadedRecordSet,
    records: Iterable[dict[str, Any]],
) -> dict[tuple[str, int, str], dict[str, Any]]:
    values = [record for group in parent.records.values() for record in group]
    values.extend(records)
    registry = {}
    for record in values:
        stable = _stable_id(record)
        registry[(stable, record["revision"], record["content_hash"])] = record
    return registry


def _run_failure_injections(
    binding_reference: Mapping[str, Any], config: backend.ExecutionConfig
) -> dict[str, Any]:
    outcomes = []
    roots = {
        "backend-lowering": BUILD_ROOT / "failure-lowering",
        "artifact-generation": BUILD_ROOT / "failure-generation",
        "target-compile-link": BUILD_ROOT / "failure-arm",
    }
    for stage, root in roots.items():
        outcome = backend.execute_exact_slice(
            binding_reference, config, root, failure_stage=stage
        )
        statuses = dict(outcome.stage_statuses)
        if outcome.status != "failed" or statuses[stage] != "failed":
            raise ValueError(f"Task 009 failure injection did not fail at {stage}")
        terminal = False
        for name in backend.PROBE_STAGES:
            if name == stage:
                terminal = True
                continue
            if terminal and statuses[name] != "not-run":
                raise ValueError(f"Task 009 continued after injected {stage} failure")
        outcomes.append({
            "stage": stage,
            "overall_status": outcome.status,
            "stage_statuses": [list(item) for item in outcome.stage_statuses],
            "diagnostic_codes": [item["code"] for item in outcome.diagnostics],
        })
    report = {
        "schema_version": "task009-failure-injection-v1",
        "status": "passed",
        "outcomes": outcomes,
    }
    _write_json(EVIDENCE_ROOT / "failure-injection.json", report)
    return report


def _portable_outcome(outcome: backend.ExecutionOutcome) -> dict[str, Any]:
    return {
        "status": outcome.status,
        "artifacts": {
            fact.kind: {
                "byte_sha256": fact.byte_sha256,
                "byte_length": fact.byte_length,
                "portable_locator": fact.portable_locator,
            }
            for fact in outcome.artifacts
        },
        "stage_statuses": [list(item) for item in outcome.stage_statuses],
        "diagnostics": list(outcome.diagnostics),
        "bridge_result": copy.deepcopy(outcome.bridge_result),
        "command_vectors": list(outcome.command_vectors),
        "resource_facts": copy.deepcopy(outcome.resource_facts),
    }


def execute() -> dict[str, Any]:
    _verify_preflight()
    parent = record_set_rules.load_record_set(ROOT, PARENT_MANIFEST)
    config = _execution_config()
    producer_hash = "sha256:" + core.sha256_file(
        ROOT / "tools/contracts/task009_backend.py"
    )

    probe = _authorized_probe()
    backend.validate_probe_input(probe)
    probe_binding = copy.deepcopy(probe["binding_reference"])
    probe_first = backend.execute_exact_slice(
        probe_binding, config, BUILD_ROOT / "probe-a"
    )
    probe_second = backend.execute_exact_slice(
        probe_binding, config, BUILD_ROOT / "probe-root-with-longer-name-b"
    )
    probe_equality = backend.compare_deterministic_outcomes(
        probe_first, probe_second
    )
    if not all(
        probe_equality[key]
        for key in (
            "command_vectors_equal", "bridge_results_equal", "resource_facts_equal"
        )
    ):
        raise ValueError("probe non-artifact deterministic facts differ")
    _retain_artifacts(probe_first)
    probe_closure_hash = _closure_hash([
        _reference(probe, "conformance_probe_id"),
        copy.deepcopy(probe["binding_reference"]),
        copy.deepcopy(probe["contract_reference"]),
        copy.deepcopy(probe["graph_reference"]),
        copy.deepcopy(probe["environment_reference"]),
        copy.deepcopy(probe["procedure_reference"]),
    ])
    probe_artifacts = _artifact_descriptors(
        probe_first, PROBE_ARTIFACT_IDS, probe_closure_hash
    )
    probe_result = _probe_result(probe, probe_first, probe_artifacts)
    if probe_result["overall_status"] != "success":
        raise ValueError("authorized Task 009 probe did not pass")
    probe_evidence = _probe_evidence(probe, probe_result)
    promotion_claim = _promotion_claim(probe_evidence, producer_hash)
    promoted = _promoted_records(probe_evidence, promotion_claim)

    procedure = parent.records["conformance-probe-procedure"][0]
    environment = parent.records["prerequisite-environment"][0]
    probe_registry = _probe_validation_registry(
        parent,
        [probe, probe_result, probe_evidence, *probe_artifacts.values()],
    )
    probe_diagnostics = prerequisite.validate_probe_values(
        probe,
        probe_result,
        probe_evidence,
        procedure,
        environment,
        probe_registry,
    )
    if probe_diagnostics:
        raise ValueError(f"authorized probe records invalid: {probe_diagnostics}")

    preliminary_plan = _record_plan(
        probe,
        probe_result,
        probe_evidence,
        probe_artifacts,
        promotion_claim,
        promoted,
    )
    preliminary_members = _write_records(preliminary_plan)
    temporary_manifest = _record_set_manifest(
        "schuss-record-set-999999",
        parent,
        preliminary_members,
        enforced_task_directory=False,
    )
    temporary_manifest_path = BUILD_ROOT / "promotion-record-set.json"
    _write_exact(temporary_manifest_path, _record_bytes(temporary_manifest))

    promoted_context = load_repository_context(
        ROOT,
        record_set_path=temporary_manifest_path,
        parent_record_set_path=PARENT_MANIFEST,
    )
    if promoted_context.task007_summary["status"] != "valid":
        raise ValueError(
            "promoted Task 009 resolution context is invalid: "
            + core.canonical_json(promoted_context.task007_summary["diagnostics"])
        )
    operation_request = {
        "schema_version": "schuss-operation-request-v1",
        "canonical_profile": "schuss-canonical-json-v1",
        "operation": "build.resolve",
        "payload": {
            "build_request_reference": _reference(
                promoted["request"], "build_request_id"
            )
        },
    }
    resolution = dispatch_operation(operation_request, promoted_context)
    if resolution["status"] != "success":
        raise ValueError(
            "ordinary promoted build.resolve did not succeed: "
            + core.canonical_json(resolution)
        )
    trace = resolution["value"]["resolution_traces"][0]
    selected = [
        candidate
        for candidate in trace["candidates"]
        if candidate["binding_reference"]
        == _reference(promoted["binding"], "implementation_id")
    ]
    if (
        trace["status"] != "selected"
        or len(selected) != 1
        or selected[0]["exclusion_reasons"]
        or selected[0]["unresolved_reasons"]
    ):
        raise ValueError("promoted selected candidate retained uncertainty")
    invocation = resolution["value"]["backend_invocation"]
    if invocation is None:
        raise ValueError("successful build.resolve emitted no backend invocation")
    invocation_schema = SCHEMAS["backend-invocation-input-v1"]
    build_request_schema = SCHEMAS["build-request-v0"]
    backend.invocation_schema_closure(invocation_schema, build_request_schema)
    invocation_bytes = _canonical_bytes(invocation)
    _write_exact(EVIDENCE_ROOT / "backend-invocation-input.json", invocation_bytes + b"\n")

    stale = copy.deepcopy(invocation)
    stale["accepted_build_request"]["content_hash"] = "sha256:" + "0" * 64
    rejection_root = BUILD_ROOT / "rejected-stale-invocation"
    try:
        backend.run_backend_handler(
            stale,
            invocation_schema,
            build_request_schema,
            _reference(promoted["binding"], "implementation_id"),
            promoted["request"],
            config,
            rejection_root,
        )
    except backend.Task009BackendError as error:
        if error.code != "TASK009_BUILD_REQUEST_STALE" or rejection_root.exists():
            raise
        rejection = {
            "schema_version": "task009-handler-rejection-v1",
            "status": "passed",
            "diagnostic_code": error.code,
            "output_root_created": False,
        }
    else:
        raise ValueError("production handler accepted a stale build request")
    _write_json(EVIDENCE_ROOT / "handler-rejection.json", rejection)

    expected_binding = _reference(promoted["binding"], "implementation_id")
    production_first = backend.run_backend_handler(
        invocation,
        invocation_schema,
        build_request_schema,
        expected_binding,
        promoted["request"],
        config,
        BUILD_ROOT / "production-a",
    )
    production_second = backend.run_backend_handler(
        invocation,
        invocation_schema,
        build_request_schema,
        expected_binding,
        promoted["request"],
        config,
        BUILD_ROOT / "production-root-with-longer-name-b",
    )
    production_equality = backend.compare_deterministic_outcomes(
        production_first, production_second
    )
    if not all(
        production_equality[key]
        for key in (
            "command_vectors_equal", "bridge_results_equal", "resource_facts_equal"
        )
    ):
        raise ValueError("production non-artifact deterministic facts differ")
    if production_first.status != "success" or production_first.resource_facts is None:
        raise ValueError("production handler did not reach successful ARM compile/link")
    _retain_artifacts(production_first)

    closure = _input_closure(promoted)
    production_artifacts = _artifact_descriptors(
        production_first,
        PRODUCTION_ARTIFACT_IDS,
        _closure_hash(closure),
    )
    resource = _resource_report(promoted, production_first.resource_facts)
    result = _build_result(promoted, production_artifacts, resource)
    production_claims = _production_evidence(
        result,
        promoted,
        production_artifacts,
        resource,
        producer_hash,
    )

    final_plan = _record_plan(
        probe,
        probe_result,
        probe_evidence,
        probe_artifacts,
        promotion_claim,
        promoted,
        production_artifacts,
        resource,
        result,
        production_claims,
    )
    final_members = _write_records(final_plan)
    final_manifest = _record_set_manifest(
        "schuss-record-set-000003",
        parent,
        final_members,
        enforced_task_directory=True,
    )
    _write_exact(SUCCESSOR_MANIFEST, _record_bytes(final_manifest))

    _write_json(EVIDENCE_ROOT / "probe-fresh-root-equality.json", probe_equality)
    _write_json(
        EVIDENCE_ROOT / "production-fresh-root-equality.json",
        production_equality,
    )
    _write_json(EVIDENCE_ROOT / "probe-execution.json", _portable_outcome(probe_first))
    _write_json(
        EVIDENCE_ROOT / "production-execution.json",
        _portable_outcome(production_first),
    )
    _run_failure_injections(probe_binding, config)

    seam_report = {
        "schema_version": "task009-backend-invocation-seam-v1",
        "status": "passed",
        "operation_result_sha256": hashlib.sha256(
            canonical_result_bytes(resolution, promoted_context)
        ).hexdigest(),
        "invocation_byte_length": len(invocation_bytes),
        "invocation_sha256": hashlib.sha256(invocation_bytes).hexdigest(),
        "selected_binding_reference": expected_binding,
        "handler_received_exact_bytes": True,
    }
    _write_json(EVIDENCE_ROOT / "backend-invocation-seam.json", seam_report)
    level_status = {
        "schema_version": "task009-evidence-level-status-v1",
        "levels": [
            {"level": level, "status": "passed" if level <= 5 else "not-run"}
            for level in range(1, 9)
        ],
        "limitations": [
            "Level 6 connected-device execution was not run.",
            "Level 7 real-time resource validation was not run.",
            "Level 8 audible listening validation was not run.",
        ],
    }
    _write_json(EVIDENCE_ROOT / "evidence-level-status.json", level_status)

    completion = {
        "schema_version": "task009-completion-manifest-v1",
        "status": "passed",
        "record_set": final_manifest,
        "probe": {
            "input": _reference(probe, "conformance_probe_id"),
            "result": _reference(probe_result, "conformance_probe_result_id"),
            "evidence": _reference(
                probe_evidence, "conformance_probe_evidence_id"
            ),
            "artifacts": [
                _reference(probe_artifacts[kind], "artifact_id")
                for kind in ARTIFACT_KINDS
            ],
        },
        "strictly_earlier_chain": {
            "probe_binding": copy.deepcopy(probe["binding_reference"]),
            "promoted_binding": _reference(promoted["binding"], "implementation_id"),
            "eligibility": _reference(
                promoted["eligibility"], "binding_eligibility_id"
            ),
            "compatibility_evidence": _reference(
                promotion_claim, "evidence_claim_id"
            ),
        },
        "production": {
            "request": _reference(promoted["request"], "build_request_id"),
            "result": _reference(result, "build_result_id"),
            "resource_report": _reference(resource, "resource_report_id"),
            "artifacts": [
                _reference(production_artifacts[kind], "artifact_id")
                for kind in ARTIFACT_KINDS
            ],
            "evidence_claims": [
                _reference(claim, "evidence_claim_id")
                for claim in production_claims
            ],
        },
        "artifact_bytes": {
            kind: {
                "byte_sha256": production_artifacts[kind]["byte_sha256"],
                "byte_length": production_artifacts[kind]["byte_length"],
            }
            for kind in ARTIFACT_KINDS
        },
        "tool_identities": {
            "java": backend.JAVA_SHA256,
            "javac": backend.JAVAC_SHA256,
            "arm_components": dict(sorted(backend.ARM_COMPONENTS.items())),
            "firmware_bin": backend.FIRMWARE_BIN_SHA256,
            "firmware_link_elf": backend.FIRMWARE_ELF_SHA256,
        },
        "prohibited_actions": {
            "device_access": False,
            "firmware_installation": False,
            "real_time_measurement": False,
            "audible_procedure": False,
            "stage_commit_push": False,
            "upload_or_flash": False,
        },
    }
    _write_json(EVIDENCE_ROOT / "completion-manifest.json", completion)

    checked = validate()
    if checked["status"] != "valid":
        raise ValueError("Task 009 final validation did not pass")
    return checked


def validate() -> dict[str, Any]:
    if not SUCCESSOR_MANIFEST.is_file():
        raise ValueError("Task 009 successor record set is absent")
    selected = record_set_rules.load_record_set(ROOT, SUCCESSOR_MANIFEST)
    context = load_repository_context(ROOT, record_set_path=SUCCESSOR_MANIFEST)
    diagnostics: list[dict[str, Any]] = []
    if context.task007_summary["status"] != "valid":
        diagnostics.extend(context.task007_summary["diagnostics"])

    request = next(
        item
        for item in selected.records["request"]
        if item["build_request_id"] == "schuss-build-request-000001"
        and item["revision"] == 2
    )
    operation = {
        "schema_version": "schuss-operation-request-v1",
        "canonical_profile": "schuss-canonical-json-v1",
        "operation": "build.resolve",
        "payload": {
            "build_request_reference": _reference(request, "build_request_id")
        },
    }
    resolution = dispatch_operation(operation, context)
    if resolution["status"] != "success":
        diagnostics.append({
            "code": "TASK009_FINAL_RESOLUTION_INVALID",
            "severity": "error",
            "subject": request["build_request_id"],
            "location": "$.build.resolve",
            "message": "final ordinary build.resolve is not successful",
        })

    artifacts = list(selected.records.get("artifact", ()))
    for artifact in artifacts:
        path = ARTIFACT_STORE / artifact["byte_sha256"]
        if (
            not path.is_file()
            or path.stat().st_size != artifact["byte_length"]
            or core.sha256_file(path) != artifact["byte_sha256"]
        ):
            diagnostics.append({
                "code": "TASK009_RETAINED_ARTIFACT_MISMATCH",
                "severity": "error",
                "subject": artifact["artifact_id"],
                "location": artifact["portable_locator"],
                "message": "retained artifact bytes do not match the descriptor",
            })

    probe = next(
        item for item in selected.records["conformance-probe-input"]
        if item["conformance_probe_id"] == "schuss-conformance-probe-000002"
    )
    probe_result = next(
        item for item in selected.records["conformance-probe-result"]
        if item["conformance_probe_result_id"]
        == "schuss-conformance-probe-result-000002"
    )
    probe_evidence = next(
        item for item in selected.records["conformance-probe-evidence"]
        if item["conformance_probe_evidence_id"]
        == "schuss-conformance-probe-evidence-000002"
    )
    procedure = selected.records["conformance-probe-procedure"][0]
    environment = selected.records["prerequisite-environment"][0]
    registry = _probe_validation_registry(selected, [])
    diagnostics.extend(
        item.as_dict()
        for item in prerequisite.validate_probe_values(
            probe,
            probe_result,
            probe_evidence,
            procedure,
            environment,
            registry,
        )
    )

    evidence_levels = {
        claim["level"]
        for claim in selected.records.get("evidence", ())
        if claim["evidence_claim_id"] != "schuss-evidence-claim-000001"
    }
    if evidence_levels != {1, 2, 3, 4, 5}:
        diagnostics.append({
            "code": "TASK009_EVIDENCE_LEVEL_SET_INVALID",
            "severity": "error",
            "subject": "task-009",
            "location": "$.evidence",
            "message": "final evidence claims must represent exactly levels 1 through 5",
        })
    for path in sorted(EVIDENCE_ROOT.rglob("*")):
        if not path.is_file() or ARTIFACT_STORE in path.parents:
            continue
        payload = path.read_bytes()
        if any(fragment in payload for fragment in (b"/Users/", b"/private/", b"/tmp/")):
            diagnostics.append({
                "code": "TASK009_DURABLE_PATH_LEAK",
                "severity": "error",
                "subject": path.name,
                "location": path.relative_to(ROOT).as_posix(),
                "message": "durable evidence contains a machine-local absolute path",
            })

    summary = {
        "schema_version": "task009-validation-summary-v1",
        "status": "invalid" if diagnostics else "valid",
        "record_set_reference": selected.reference,
        "record_count": sum(len(values) for values in selected.records.values()),
        "task009_record_count": sum(
            1
            for member in selected.manifest["record_members"]
            if member["portable_path"].startswith("contracts/task009/")
        ),
        "artifact_count": len(artifacts),
        "build_resolution_status": resolution["status"],
        "build_result_status": selected.records["result"][0]["overall_status"],
        "evidence_levels_passed": sorted(evidence_levels),
        "evidence_levels_not_run": [6, 7, 8],
        "diagnostics": sorted(
            diagnostics,
            key=lambda item: (
                item["severity"], item["code"], item["subject"], item["location"]
            ),
        ),
    }
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate retained Task 009 records and evidence without executing tools",
    )
    arguments = parser.parse_args()
    try:
        summary = validate() if arguments.check else execute()
    except (
        OSError,
        ValueError,
        core.DuplicateJsonMemberError,
        record_set_rules.RecordSetError,
        backend.Task009BackendError,
    ) as error:
        print(f"Task 009 failed: {error}", file=sys.stderr)
        return 1
    print(core.canonical_json(summary))
    return 0 if summary["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
