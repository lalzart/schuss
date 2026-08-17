#!/usr/bin/env python3
"""Generate the revised fail-closed Task 025 record set and goldens."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/contracts")]

from packages.schuss_core.effects_direct_semantics import (  # noqa: E402
    DIRECT_BINDING_IDS,
    OPERATION_SPEC_IDS,
    SOURCE_BINDING_IDS,
    semantic_goldens,
)

import record_set_rules  # noqa: E402
import validator_core as core  # noqa: E402


FACTORY_COMMIT = "25d2615ed5233546d617017666a4ab1e60a8c506"
PATCHER_COMMIT = "08d3e6e1e2b61230308c20a15ded58ffdaf4656c"
PARENT_PATH = ROOT / "contracts/record-sets/task024-catalog-coverage-v1.json"
OUTPUT = ROOT / "contracts/record-sets/task025-direct-core-v1.json"
EVIDENCE_ROOT = ROOT / "evidence/task025-completion-v1"

SOURCE_DATA: dict[str, dict[str, Any]] = {
    "blep-saw-q27": {
        "slug": "saw",
        "contract": "schuss-component-contract-000012",
        "source_path": "objects/osc/saw.axo",
        "source_sha256": "8f225df94b7528c3e5b9a6b90e471f5e195f4e6e15afb6468871294ab80388b0",
        "runtime_dependencies": ["ksoloti-blep-runtime", "ksoloti-pitch-runtime"],
        "numeric": [
            "frequency=\"MTOFEXTENDED(parameter-plus-control-pitch)\"",
            "phase=\"signed-32-bit-wrap\"",
            "blep_dispatch=\"phase-crossing-with-signed-division-by-frequency-shift-6\"",
            "output=\"unsigned-phase-ramp-plus-four-voice-blep-correction-q27\"",
        ],
        "state": [
            "initial=\"static-storage-zero-phase-next-voice\"",
            "blep_voices=\"four-pointers-initialized-to-table-tail\"",
        ],
        "schedule": ["rate=\"one-control-call-producing-sixteen-audio-samples\""],
    },
    "blep-pwm-q27": {
        "slug": "pwm",
        "contract": "schuss-component-contract-000013",
        "source_path": "objects/osc/pwm.axo",
        "source_sha256": "92162c00b235967c46c43928786e004a9e1fa3d6429523208fdd37d8b591e3b0",
        "runtime_dependencies": ["ksoloti-blep-runtime", "ksoloti-pitch-runtime"],
        "numeric": [
            "frequency=\"unsigned-MTOFEXTENDED(parameter-plus-control-pitch)\"",
            "phase=\"signed-storage-with-32-bit-wrap\"",
            "division=\"two-source-branches-selected-by-frequency-bit-24\"",
            "output=\"eight-alternating-blep-voices-q27\"",
        ],
        "state": [
            "initial=\"static-storage-zero-phase-width-next-voice\"",
            "pulse_width=\"latched-only-at-phase-wrap\"",
        ],
        "schedule": [
            "rate=\"one-control-call-producing-sixteen-audio-samples\"",
            "crossing_order=\"exact-source-branch-order\"",
        ],
    },
    "exponential-smooth-q27": {
        "slug": "smooth",
        "contract": "schuss-component-contract-000015",
        "source_path": "objects/math/smooth.axo",
        "source_sha256": "f4c2bfbfc6f9748393bfe62af39e095ca184f9a5cc0ada21414b22a396e73fb0",
        "runtime_dependencies": ["arm-fixed-point-runtime"],
        "numeric": [
            "formula=\"___SMMLA(value-input,(-1<<26)+(time>>1),value)\"",
            "multiply=\"signed-high-word-plus-wrapping-accumulator\"",
        ],
        "state": ["value=\"explicit-zero-initialization\""],
        "schedule": [
            "rate=\"one-control-update-per-block\"",
            "authoring_transfer=\"unresolved-outside-fixed-graph-value\"",
        ],
    },
    "soft-clip-q27": {
        "slug": "soft-clip",
        "contract": "schuss-component-contract-000016",
        "source_path": "objects/dist/soft.axo",
        "source_sha256": "c6d4ec99987b8d324a4fc8628b056ff3b6f45eb7d2f1785dec5be7b1414b00f1",
        "runtime_dependencies": ["arm-fixed-point-runtime"],
        "numeric": [
            "selected_overload=\"audio-buffer-uuid-e680d76a805e4866027cdf654c7efd8b2e54622\"",
            "input=\"signed-saturate-28\"",
            "formula=\"x-plus-arithmetic-shift-1-minus-nested-signed-high-word-cubic\"",
            "final_saturation=\"none\"",
        ],
        "state": ["private_state=\"none\""],
        "schedule": ["rate=\"once-per-audio-sample\""],
    },
    "interpolated-vca-q27": {
        "slug": "vca",
        "contract": "schuss-component-contract-000020",
        "source_path": "objects/gain/vca.axo",
        "source_sha256": "0fc7ff51ec5ca878375540cb7764651884a2286ff7699ed05c6a103b565cb3b7",
        "runtime_dependencies": ["arm-fixed-point-runtime"],
        "numeric": [
            "step=\"arithmetic-shift-right-4-of-gain-minus-previous\"",
            "sample=\"___SMMUL(audio,interpolated-gain)<<5\"",
            "remainder=\"discarded-after-sixteen-samples\"",
        ],
        "state": [
            "previous_gain=\"static-storage-zero-initialization\"",
            "previous_gain_update=\"before-audio-loop-after-local-copy\"",
        ],
        "schedule": ["rate=\"one-control-step-plus-sixteen-audio-samples\""],
    },
}

RUNTIME_HASHES = {
    "firmware/axoloti_math.h": "95ccbdbea15078a6ef207e87749bb8defaa4662b6eebddfb40944f350b549191",
    "firmware/axoloti_oscs.h": "d147bbea3595004af52e046edff3bd0a64dea96a6e1762b7648044069495c123",
    "firmware/axoloti_oscs.c": "ef6402083da6c0673bc42ca8ca27dcfd4dc64c7e564bc338c424b8475855aa32",
    "firmware/axoloti_memory.c": "9ce97221ad40f5828a6d7cb731b3e587ada0291b91c148da8ee34de96559f05e",
}

CLAIM_NUMBERS = {
    "blep-saw-q27": 38,
    "blep-pwm-q27": 39,
    "exponential-smooth-q27": 40,
    "soft-clip-q27": 41,
    "interpolated-vca-q27": 43,
}

ELIGIBILITY_NUMBERS = {
    "blep-saw-q27": 27,
    "blep-pwm-q27": 28,
    "exponential-smooth-q27": 29,
    "soft-clip-q27": 30,
    "interpolated-vca-q27": 32,
}


def _load_local_sources() -> dict[str, Path]:
    path = ROOT / "catalog/sources.local.yml"
    if not path.is_file():
        raise ValueError("Task 025 generation requires ignored catalog/sources.local.yml")
    values: dict[str, Path] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("  ") or ":" not in line:
            continue
        key, raw = line.strip().split(":", 1)
        values[key] = Path(raw.strip())
    for required in ("axoloti-factory", "patcher"):
        if required not in values:
            raise ValueError(f"Task 025 source root is absent: {required}")
    return values


def _pinned_bytes(checkout: Path, commit: str, path: str) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(checkout), "show", f"{commit}:{path}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode:
        raise ValueError(f"pinned source unavailable: {checkout.name}@{commit}:{path}")
    return completed.stdout


def _verify_source_authority() -> dict[str, str]:
    roots = _load_local_sources()
    observed: dict[str, str] = {}
    for data in SOURCE_DATA.values():
        payload = _pinned_bytes(roots["axoloti-factory"], FACTORY_COMMIT, data["source_path"])
        digest = hashlib.sha256(payload).hexdigest()
        if digest != data["source_sha256"]:
            raise ValueError(f"factory source hash differs: {data['source_path']}")
        observed[data["source_path"]] = digest
    for path, expected in RUNTIME_HASHES.items():
        payload = _pinned_bytes(roots["patcher"], PATCHER_COMMIT, path)
        digest = hashlib.sha256(payload).hexdigest()
        if digest != expected:
            raise ValueError(f"patcher source hash differs: {path}")
        observed[path] = digest
    reverb_path = "objects/fx/rngs/reverb.axo"
    header_path = "objects/fx/rngs/rings_fx.h"
    reverb = _pinned_bytes(roots["axoloti-factory"], FACTORY_COMMIT, reverb_path)
    header = _pinned_bytes(roots["axoloti-factory"], FACTORY_COMMIT, header_path)
    expected = {
        reverb_path: "944fa85fd56fda21d207174b236e54d7f9e511dab923a8e648b1e37e0c2d51cd",
        header_path: "3da1acbf013cd4d7c2a105c95d99e19b0b1c173addc24dc2f79af85523d0a55b",
    }
    for path, payload in ((reverb_path, reverb), (header_path, header)):
        digest = hashlib.sha256(payload).hexdigest()
        if digest != expected[path]:
            raise ValueError(f"reverb source hash differs: {path}")
        observed[path] = digest
    if b"sdram_malloc(32768)" not in reverb:
        raise ValueError("reverb wrapper allocation expression differs")
    for required in (
        b"typedef uint16_t T;",
        b"std::fill(&buffer_[0], &buffer_[size], 0);",
        b"typedef FxEngine<32768, FORMAT_16_BIT> E;",
    ):
        if required not in header:
            raise ValueError("reverb header allocation evidence differs")
    memory = _pinned_bytes(roots["patcher"], PATCHER_COMMIT, "firmware/axoloti_memory.c")
    for required in (b"sdram_total_remaining -= size;", b"sdram_current_addr += size;"):
        if required not in memory:
            raise ValueError("pinned SDRAM allocator byte semantics differ")
    return observed


def _record(value: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(value)
    result["content_hash"] = "sha256:" + "0" * 64
    errors = core.schema_errors(result, schema, schema)
    if errors:
        raise ValueError(f"{result.get('schema_version')}: " + "; ".join(errors))
    result["content_hash"] = core.record_content_hash(result, schema)
    return result


def _ref(record: dict[str, Any], id_field: str) -> dict[str, Any]:
    return {
        id_field: record[id_field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def _semantic_ref(record: dict[str, Any], id_field: str) -> dict[str, Any]:
    return {
        "input_kind": "semantic-record",
        "stable_id": record[id_field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def _direct_schema() -> dict[str, Any]:
    schema = core.load_json(ROOT / "schemas/direct-operation-spec-v0.schema.json")
    schema["$id"] = "direct-operation-spec-v1.schema.json"
    schema["title"] = "Schuss exact Task 025 direct operation specification v1"
    schema["required"].insert(schema["required"].index("source_authority"), "source_binding_reference")
    schema["properties"]["schema_version"] = {"const": "direct-operation-spec-v1"}
    schema["properties"]["opcode"] = {"enum": list(OPERATION_SPEC_IDS)}
    schema["properties"]["compatibility_mode"] = {"const": "legacy-equivalent-task025-v1"}
    schema["properties"]["source_binding_reference"] = {"$ref": "#/$defs/implementationReference"}
    golden = schema["properties"]["golden_vector_set"]["properties"]
    golden["schema_version"] = {"const": "task025-semantic-goldens-v1"}
    golden["portable_path"] = {"const": "evidence/task025-completion-v1/semantic-goldens.json"}
    schema["$defs"]["implementationReference"] = {
        "type": "object",
        "required": ["implementation_id", "revision", "content_hash"],
        "properties": {
            "implementation_id": {
                "type": "string",
                "pattern": "^schuss-implementation-[0-9]{6}$",
            },
            "revision": {"type": "integer", "minimum": 1},
            "content_hash": {"$ref": "#/$defs/contentHash"},
        },
        "additionalProperties": False,
    }
    annotations = core.validate_schema_annotations(schema)
    if annotations:
        raise ValueError("direct operation schema annotations invalid: " + "; ".join(annotations))
    return schema


def _source(source_id: str, commit: str, path: str, digest: str, license_name: str) -> dict[str, str]:
    return {
        "source_id": source_id,
        "commit": commit,
        "portable_path": path,
        "byte_sha256": digest,
        "license_declaration": license_name,
    }


def _operation_spec(
    opcode: str,
    source_binding: dict[str, Any],
    contract: dict[str, Any],
    schema: dict[str, Any],
    golden_digest: str,
) -> dict[str, Any]:
    data = SOURCE_DATA[opcode]
    authorities = [
        _source("axoloti-factory", FACTORY_COMMIT, data["source_path"], data["source_sha256"], "BSD"),
        _source("patcher", PATCHER_COMMIT, "firmware/axoloti_math.h", RUNTIME_HASHES["firmware/axoloti_math.h"], "GPL-3.0-or-later"),
    ]
    if opcode in {"blep-saw-q27", "blep-pwm-q27"}:
        authorities.extend([
            _source("patcher", PATCHER_COMMIT, "firmware/axoloti_oscs.h", RUNTIME_HASHES["firmware/axoloti_oscs.h"], "GPL-3.0-or-later"),
            _source("patcher", PATCHER_COMMIT, "firmware/axoloti_oscs.c", RUNTIME_HASHES["firmware/axoloti_oscs.c"], "GPL-3.0-or-later"),
        ])
    return _record({
        "schema_version": "direct-operation-spec-v1",
        "canonical_profile": "schuss-canonical-json-v1",
        "direct_operation_spec_id": OPERATION_SPEC_IDS[opcode],
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "opcode": opcode,
        "compatibility_mode": "legacy-equivalent-task025-v1",
        "contract_reference": _ref(contract, "component_contract_id"),
        "source_binding_reference": _ref(source_binding, "implementation_id"),
        "source_authority": authorities,
        "runtime_dependencies": data["runtime_dependencies"],
        "numeric_semantics": data["numeric"],
        "state_semantics": data["state"],
        "schedule_semantics": data["schedule"],
        "golden_vector_set": {
            "schema_version": "task025-semantic-goldens-v1",
            "portable_path": "evidence/task025-completion-v1/semantic-goldens.json",
            "section": "operations." + opcode,
            "byte_sha256": golden_digest,
        },
    }, schema)


def _facet_mappings(opcode: str, contract: dict[str, Any]) -> list[dict[str, Any]]:
    mappings = []
    number = 0
    for collection, kind, id_field in (
        ("ports", "port", "facet_id"),
        ("parameters", "parameter", "facet_id"),
        ("attributes", "attribute", "facet_id"),
        ("actions", "action", "facet_id"),
        ("displays", "display", "facet_id"),
    ):
        for facet in contract.get(collection, []):
            number += 1
            facet_id = facet[id_field]
            mappings.append({
                "mapping_id": f"binding-map-{int(DIRECT_BINDING_IDS[opcode][-6:]):04d}{number:02d}",
                "contract_facet": {"facet_kind": kind, "facet_id": facet_id},
                "implementation_seam": {
                    "seam_kind": "native-symbol",
                    "symbol": f"schuss_direct_{opcode.replace('-', '_')}_{facet_id.replace('-', '_')}",
                },
            })
    return mappings


def _native_binding(
    opcode: str,
    source_binding: dict[str, Any],
    contract: dict[str, Any],
    schema: dict[str, Any],
) -> dict[str, Any]:
    return _record({
        "schema_version": "implementation-binding-v1",
        "canonical_profile": "schuss-canonical-json-v1",
        "implementation_id": DIRECT_BINDING_IDS[opcode],
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "contract_reference": _ref(contract, "component_contract_id"),
        "realization": {
            "form": "native-cpp",
            "portable_symbol": "schuss_direct_" + opcode.replace("-", "_"),
        },
        "facet_mappings": _facet_mappings(opcode, contract),
        "observed_dependencies": copy.deepcopy(source_binding.get("observed_dependencies", [])),
        "private_state": copy.deepcopy(source_binding.get("private_state", [])),
        "evidence_refs": sorted(set(source_binding["evidence_refs"] + ["fixture:task025-semantic-goldens"])),
        "selection_state": {
            "status": "not-evaluated",
            "owner": "task-007",
            "reason": "target-backend-contracts-not-yet-implemented",
            "rationale": "Task 025 records an exact native semantic identity; target/backend eligibility remains a separate explicit record.",
        },
    }, schema)


def _claim(
    number: int,
    native: dict[str, Any],
    source_binding: dict[str, Any],
    spec: dict[str, Any],
    schema: dict[str, Any],
) -> dict[str, Any]:
    return _record({
        "schema_version": "evidence-claim-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "evidence_claim_id": f"schuss-evidence-claim-{number:06d}",
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "level": 2,
        "level_name": "component-graph-resolution",
        "subject_reference": {
            "subject_kind": "semantic-record",
            "stable_id": native["implementation_id"],
            "revision": 1,
            "content_hash": native["content_hash"],
            "stage": "target-independent-graph-validation",
        },
        "outcome": "passed",
        "method": "task025-exact-source-arithmetic-state-and-host-vector-review",
        "producer_identity": {
            "producer_kind": "validator",
            "producer_id": "schuss-task025-validator",
            "version": "task025-v2",
            "content_hash": "sha256:" + hashlib.sha256(b"schuss-task025-validator-v2").hexdigest(),
        },
        "evidence_inputs": [
            _semantic_ref(source_binding, "implementation_id"),
            _semantic_ref(spec, "direct_operation_spec_id"),
        ],
        "limitations": [
            "Host vectors use injected pitch and BLEP fixtures where required.",
            "No backend lowering, ARM, device, real-time, audible, UI, or publication evidence is established.",
        ],
    }, schema)


def _reverb_claim(source_binding: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    return _record({
        "schema_version": "evidence-claim-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "evidence_claim_id": "schuss-evidence-claim-000042",
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "level": 2,
        "level_name": "component-graph-resolution",
        "subject_reference": {
            "subject_kind": "semantic-record",
            "stable_id": source_binding["implementation_id"],
            "revision": source_binding["revision"],
            "content_hash": source_binding["content_hash"],
            "stage": "target-independent-graph-validation",
        },
        "outcome": "failed",
        "method": "task025-pinned-wrapper-header-and-byte-allocator-static-audit",
        "producer_identity": {
            "producer_kind": "validator",
            "producer_id": "schuss-task025-validator",
            "version": "task025-v2",
            "content_hash": "sha256:" + hashlib.sha256(b"schuss-task025-validator-v2").hexdigest(),
        },
        "evidence_inputs": [_semantic_ref(source_binding, "implementation_id")],
        "limitations": [
            "The wrapper reserves 32768 bytes while the exact uint16 engine clears 65536 bytes.",
            "This is static negative compatibility evidence, not a device failure, corruption, timing, or audible observation.",
        ],
    }, schema)


def _backend(base: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(base)
    value["revision"] = 3
    value["display_name"] = "Partial direct Ksoloti effects semantic backend"
    value["lowering_identity"]["contract_version"] = "direct-effects-task025-partial-v1"
    value["bridge_boundary"]["execution_status"] = "not-run"
    value["target_pairings"][0]["rationale"] = (
        "Task 025 promotes five exact native operation semantics while the selected reverb remains explicitly unsupported; no full-graph handler exists."
    )
    return _record(value, schema)


def _eligibility(
    number: int,
    base: dict[str, Any],
    binding: dict[str, Any],
    claim: dict[str, Any],
    backend: dict[str, Any],
    schema: dict[str, Any],
) -> dict[str, Any]:
    value = copy.deepcopy(base)
    value["binding_eligibility_id"] = f"schuss-binding-eligibility-{number:06d}"
    value["revision"] = 1
    value["binding_reference"] = _ref(binding, "implementation_id")
    value["contract_reference"] = copy.deepcopy(binding["contract_reference"])
    evidence = _ref(claim, "evidence_claim_id")
    value["compatibility_evidence"] = [evidence]
    value["allowed_pair"]["backend_reference"] = _ref(backend, "backend_id")
    value["allowed_pair"]["state"] = {
        "status": "supported",
        "evidence_level": 2,
        "evidence_refs": [evidence],
    }
    value["realization_form"] = "native-cpp"
    value["selection_policy"] = {
        "policy_id": f"schuss-selection-policy-{number:06d}",
        "version": 1,
        "priority": 300,
        "ranking_rule": "higher-explicit-priority",
        "tie_behavior": "ambiguous",
        "implicit_fallback": False,
    }
    value["unresolved_questions"] = []
    return _record(value, schema)


def _reverb_eligibility(
    base: dict[str, Any],
    source_binding: dict[str, Any],
    claim: dict[str, Any],
    backend: dict[str, Any],
    schema: dict[str, Any],
) -> dict[str, Any]:
    value = copy.deepcopy(base)
    value["binding_eligibility_id"] = "schuss-binding-eligibility-000031"
    value["revision"] = 1
    value["binding_reference"] = _ref(source_binding, "implementation_id")
    evidence = _ref(claim, "evidence_claim_id")
    value["compatibility_evidence"] = [evidence]
    value["allowed_pair"]["backend_reference"] = _ref(backend, "backend_id")
    value["allowed_pair"]["state"] = {
        "status": "unsupported",
        "evidence_level": 2,
        "evidence_refs": [evidence],
    }
    value["selection_policy"] = {
        "policy_id": "schuss-selection-policy-000031",
        "version": 1,
        "priority": 0,
        "ranking_rule": "higher-explicit-priority",
        "tie_behavior": "ambiguous",
        "implicit_fallback": False,
    }
    value["resource_requirements"][0]["state"] = {
        "status": "unsupported",
        "evidence_refs": ["contracts/task025/reverb-allocation-boundary.md"],
    }
    value["unresolved_questions"] = [{
        "question_id": "eligibility-question-000031",
        "code": "REVERB_ALLOCATION_OWNERSHIP_UNRESOLVED",
        "question": "What independently authorized allocation and ownership contract can safely realize the exact retained reverb algorithm?",
        "owner": "backend-owner",
        "earliest_task": "task-026",
        "rationale": "The pinned wrapper byte count and exact header element span are inconsistent.",
    }]
    return _record(value, schema)


def _carry_eligibility(
    base: dict[str, Any], backend: dict[str, Any], schema: dict[str, Any]
) -> dict[str, Any]:
    value = copy.deepcopy(base)
    value["revision"] = 3
    value["allowed_pair"]["backend_reference"] = _ref(backend, "backend_id")
    return _record(value, schema)


def _request(base: dict[str, Any], backend: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(base)
    value["revision"] = 3
    value["backend_reference"] = _ref(backend, "backend_id")
    value["instrument_reference"] = {"status": "omitted"}
    return _record(value, schema)


def _exact(records: list[dict[str, Any]], id_field: str, stable_id: str, revision: int) -> dict[str, Any]:
    matches = [value for value in records if value[id_field] == stable_id and value["revision"] == revision]
    if len(matches) != 1:
        raise ValueError(f"exact parent record does not resolve once: {stable_id}@{revision}")
    return matches[0]


def generated() -> tuple[dict[str, bytes], bytes, dict[str, Any]]:
    observed_sources = _verify_source_authority()
    parent_loaded = record_set_rules.load_record_set(ROOT, PARENT_PATH)
    parent = parent_loaded.manifest
    if parent_loaded.reference != {
        "record_set_id": "schuss-record-set-000016",
        "revision": 1,
        "content_hash": "sha256:753c7a8a17c4080e117f3eef21424d3047283bbc55511aaad65e363b107ee78c",
    }:
        raise ValueError("Task 025 parent record set differs from the accepted Task 024 output")
    packet = _exact(list(parent_loaded.records["core-selection-packet"]), "selection_packet_id", "schuss-core-selection-000002", 1)
    if len(packet["subjects"]) != 8 or packet["source_graph_reference"]["stable_id"] != "schuss-graph-000004":
        raise ValueError("Task 024 selection packet differs")

    schemas = parent_loaded.schemas
    direct_schema = _direct_schema()
    binding_schema = schemas["implementation-binding-v1"]
    evidence_schema = schemas["evidence-claim-v0"]
    eligibility_schema = schemas["binding-eligibility-v0"]
    backend_schema = schemas["backend-v0"]
    request_schema = schemas["build-request-v0"]
    contract_records = list(parent_loaded.records["component-contract"])
    binding_records = list(parent_loaded.records["implementation-binding"])
    eligibility_records = list(parent_loaded.records["eligibility"])

    goldens = semantic_goldens()
    golden_bytes = core.canonical_json(goldens).encode("utf-8") + b"\n"
    golden_digest = hashlib.sha256(golden_bytes).hexdigest()
    records: dict[str, tuple[str, dict[str, Any]]] = {}
    generated_values: dict[str, dict[str, Any]] = {}

    for index, opcode in enumerate(OPERATION_SPEC_IDS):
        data = SOURCE_DATA[opcode]
        source_binding = _exact(binding_records, "implementation_id", SOURCE_BINDING_IDS[opcode], 2)
        contract = _exact(contract_records, "component_contract_id", data["contract"], 1)
        packet_subjects = [
            value for value in packet["subjects"]
            if value["contract_reference"]["stable_id"] == contract["component_contract_id"]
            and value["implementation_reference"]["stable_id"] == source_binding["implementation_id"]
        ]
        if len(packet_subjects) != 1:
            raise ValueError(f"Task 025 supported subject is absent from exact packet: {opcode}")
        spec = _operation_spec(opcode, source_binding, contract, direct_schema, golden_digest)
        native = _native_binding(opcode, source_binding, contract, binding_schema)
        claim = _claim(
            CLAIM_NUMBERS[opcode], native, source_binding, spec, evidence_schema
        )
        old_eligibility = _exact(
            eligibility_records,
            "binding_eligibility_id",
            {
                "blep-saw-q27": "schuss-binding-eligibility-000017",
                "blep-pwm-q27": "schuss-binding-eligibility-000018",
                "exponential-smooth-q27": "schuss-binding-eligibility-000020",
                "soft-clip-q27": "schuss-binding-eligibility-000021",
                "interpolated-vca-q27": "schuss-binding-eligibility-000025",
            }[opcode],
            1,
        )
        generated_values[opcode] = {
            "spec": spec,
            "native": native,
            "claim": claim,
            "old_eligibility": old_eligibility,
        }
        slug = data["slug"]
        records[f"operation-spec-{slug}.json"] = ("direct-operation-spec", spec)
        records[f"implementation-binding-{slug}.json"] = ("implementation-binding", native)
        records[f"promotion-evidence-{slug}.json"] = ("evidence", claim)

    backend_base = _exact(list(parent_loaded.records["backend"]), "backend_id", "schuss-backend-000002", 2)
    backend = _backend(backend_base, backend_schema)
    records["direct-backend-r3.json"] = ("backend", backend)
    for index, opcode in enumerate(OPERATION_SPEC_IDS):
        values = generated_values[opcode]
        eligibility = _eligibility(
            ELIGIBILITY_NUMBERS[opcode],
            values["old_eligibility"],
            values["native"],
            values["claim"],
            backend,
            eligibility_schema,
        )
        records[f"binding-eligibility-{SOURCE_DATA[opcode]['slug']}.json"] = ("eligibility", eligibility)

    reverb_binding = _exact(binding_records, "implementation_id", "schuss-implementation-000056", 2)
    reverb_claim = _reverb_claim(reverb_binding, evidence_schema)
    reverb_base = _exact(eligibility_records, "binding_eligibility_id", "schuss-binding-eligibility-000022", 1)
    reverb_eligibility = _reverb_eligibility(
        reverb_base, reverb_binding, reverb_claim, backend, eligibility_schema
    )
    records["promotion-evidence-rings-reverb-unsupported.json"] = ("evidence", reverb_claim)
    records["binding-eligibility-rings-reverb-unsupported.json"] = ("eligibility", reverb_eligibility)

    for stable_id, slug in (
        ("schuss-binding-eligibility-000012", "crossfader"),
        ("schuss-binding-eligibility-000014", "audio-output"),
    ):
        carried_base = _exact(eligibility_records, "binding_eligibility_id", stable_id, 2)
        carried = _carry_eligibility(carried_base, backend, eligibility_schema)
        records[f"carried-{slug}-eligibility-r3.json"] = ("eligibility", carried)

    request_base = _exact(list(parent_loaded.records["request"]), "build_request_id", "schuss-build-request-000004", 2)
    request = _request(request_base, backend, request_schema)
    records["build-request-effects-r3.json"] = ("request", request)

    files: dict[str, bytes] = {
        "schemas/direct-operation-spec-v1.schema.json": core.canonical_json(direct_schema).encode("utf-8") + b"\n",
        "evidence/task025-completion-v1/semantic-goldens.json": golden_bytes,
    }
    for name, (_, record) in records.items():
        files[f"contracts/task025/{name}"] = core.canonical_json(record).encode("utf-8") + b"\n"

    schema_members = copy.deepcopy(parent["schema_members"])
    schema_members.append({
        "schema_version": "direct-operation-spec-v1",
        "portable_path": "schemas/direct-operation-spec-v1.schema.json",
        "byte_sha256": hashlib.sha256(files["schemas/direct-operation-spec-v1.schema.json"]).hexdigest(),
    })
    record_members = copy.deepcopy(parent["record_members"])
    for name, (kind, record) in records.items():
        relative = f"contracts/task025/{name}"
        id_field = next(field for field in record_set_rules.ID_FIELDS if field in record)
        record_members.append({
            "record_kind": kind,
            "stable_id": record[id_field],
            "revision": record["revision"],
            "content_hash": record["content_hash"],
            "portable_path": relative,
            "byte_sha256": hashlib.sha256(files[relative]).hexdigest(),
        })
    manifest_schema = core.load_json(ROOT / record_set_rules.RECORD_SET_SCHEMA)
    manifest = {
        "schema_version": "record-set-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "record_set_id": "schuss-record-set-000017",
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "purpose": "prospective-task",
        "parent_reference": {"status": "included", **parent_loaded.reference},
        "schema_members": sorted(schema_members, key=lambda value: (value["schema_version"], value["portable_path"])),
        "record_members": sorted(record_members, key=lambda value: (value["byte_sha256"], value["portable_path"])),
        "enforced_directories": sorted(parent["enforced_directories"] + ["contracts/task025"]),
    }
    manifest["content_hash"] = core.record_content_hash(manifest, manifest_schema)
    manifest_bytes = core.canonical_json(manifest).encode("utf-8") + b"\n"
    summary = {
        "schema_version": "task025-generation-summary-v2",
        "status": "valid",
        "record_set_reference": {
            "record_set_id": manifest["record_set_id"],
            "revision": manifest["revision"],
            "content_hash": manifest["content_hash"],
        },
        "selected_subject_count": 8,
        "supported_subject_count": 7,
        "unsupported_subject_count": 1,
        "new_direct_operation_count": 5,
        "new_native_binding_count": 5,
        "new_supported_eligibility_count": 5,
        "carried_supported_eligibility_count": 2,
        "unsupported_eligibility_count": 1,
        "semantic_transition_count": 2,
        "source_authority_count": len(observed_sources),
        "highest_evidence_level": 2,
        "build_handler_created": False,
        "arm_build_performed": False,
        "hardware_or_publication_performed": False,
    }
    return files, manifest_bytes, summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        files, manifest, summary = generated()
        expected = {ROOT / relative for relative in files}
        stale = [
            relative for relative, payload in files.items()
            if not (ROOT / relative).is_file() or (ROOT / relative).read_bytes() != payload
        ]
        if not OUTPUT.is_file() or OUTPUT.read_bytes() != manifest:
            stale.append(OUTPUT.relative_to(ROOT).as_posix())
        if args.check and stale:
            raise ValueError("generated Task 025 records are stale: " + ", ".join(sorted(stale)))
        if not args.check:
            generated_directory = ROOT / "contracts/task025"
            if generated_directory.is_dir():
                for path in generated_directory.glob("*.json"):
                    if path not in expected:
                        path.unlink()
            for relative, payload in files.items():
                path = ROOT / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
            OUTPUT.parent.mkdir(parents=True, exist_ok=True)
            OUTPUT.write_bytes(manifest)
    except (OSError, ValueError) as exc:
        print("Task 025 generation failed: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
