#!/usr/bin/env python3
"""Generate the exact Task 016 direct semantic records and successor set."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/contracts")]

from packages.schuss_core.gills_direct_frontend import (  # noqa: E402
    CONTRACT_REFERENCES,
    DIRECT_BINDING_IDS,
    OPERATION_SPEC_IDS,
    semantic_goldens,
)

import record_set_rules  # noqa: E402
import validator_core as core  # noqa: E402


PARENT = ROOT / "contracts/record-sets/task015-minimal-direct-frontend-v1.json"
OUTPUT = ROOT / "contracts/record-sets/task016-complete-gills-direct-v1.json"
RECORD_ROOT = ROOT / "contracts/task016"
GOLDENS_PATH = ROOT / "evidence/task016-completion-v1/semantic-goldens.json"

PATCHER_COMMIT = "08d3e6e1e2b61230308c20a15ded58ffdaf4656c"
FACTORY_COMMIT = "25d2615ed5233546d617017666a4ab1e60a8c506"
CONTRIB_COMMIT = "2e994478c0ab15fb1daa3bb4b86c88e22952d99c"
SCHUSS_COMMIT = "ff835a09da8e3942aaea4affe6bd019f44ba08e8"
ORACLE_SHA256 = "7877897b3112dcbb7ee1239f3187f535d6113875cacbb49c76bd30a0321bcfd3"

TARGET_REFERENCE = {
    "compute_target_id": "schuss-compute-target-000001",
    "revision": 2,
    "content_hash": "sha256:d8a9652bd079d0f2a8806cc4922f2a380c8092549f267047d5a4a0360b4a6753",
}
CAPABILITY_REFERENCE = {
    "capability_vocabulary_id": "schuss-capability-vocabulary-000001",
    "revision": 1,
    "content_hash": "sha256:37770109d3aff88a67ab031a6ee21c49eb4d301e2933c4659efd38c4496cca92",
}
TOOLCHAIN_REFERENCE = {
    "build_environment_id": "schuss-build-environment-000001",
    "revision": 2,
    "content_hash": "sha256:d460d5414ec534c242f9b3146b1123cb04b35fcf9af9a02452c11ada84b97bff",
}
RUNTIME_REFERENCE = {
    "build_environment_id": "schuss-build-environment-000002",
    "revision": 2,
    "content_hash": "sha256:a656a898798cad529dfec7b02f0a881b61b93e150dd0788b7028ec8e5e4ce2df",
}

OPERATION_DATA = {
    "square-lfo-q31": {
        "slug": "lfo",
        "base": "contracts/task011c/implementation-binding-lfo-r2.json",
        "eligibility": "contracts/task011c/binding-eligibility-lfo-r2.json",
        "source": ("axoloti-factory", FACTORY_COMMIT, "objects/lfo/square.axo", "d417bd0e455e28c6af9988732f6406b2d3e3c94eea9338f76ab61df926463051"),
        "numeric": {"pitch": "signed-q21", "frequency": "mtof48k-ext-q31", "phase": "signed-32-wrap", "update": "frequency-arithmetic-right-shift-2"},
        "state": {"initial_phase": 0, "initial_reset_arm": 1, "reset": "rising-reset-zero-disarm-until-low"},
        "schedule": {"rate": "control-cycle", "output": "phase-greater-than-zero-after-update"},
    },
    "cyclic-counter-rising": {
        "slug": "counter",
        "base": "contracts/task011c/implementation-binding-counter-r2.json",
        "eligibility": "contracts/task011c/binding-eligibility-counter-r2.json",
        "source": ("axoloti-factory", FACTORY_COMMIT, "objects/logic/counter.axo", "fb61bbfeb9504cee015b093888fb8c6da237d12b760a5e6ebdb9b160447bd9e1"),
        "numeric": {"count": "signed-32", "wrap": "zero-when-count-greater-than-or-equal-maximum"},
        "state": {"initial_count": 0, "initial_trigger_history": 0, "initial_reset_history": 0},
        "schedule": {"rate": "control-cycle", "order": ["trigger-edge", "reset-edge", "output"]},
    },
    "four-step-select-q21": {
        "slug": "sequencer",
        "base": "contracts/task011c/implementation-binding-sequencer-r2.json",
        "eligibility": "contracts/task011c/binding-eligibility-sequencer-r2.json",
        "source": ("axoloti-contrib", CONTRIB_COMMIT, "objects/drj/seq/stepseq_16_pitch.axo", "45336e472f1e15a295617b0f4fd1e31e83203acf9ae37a067125459f66022b0f"),
        "numeric": {"step": "signed-32", "values": "signed-q21", "invalid_step_output": 0},
        "state": {"private_state": "none"},
        "schedule": {"rate": "control-cycle", "selection": "current-counter-output"},
    },
    "sine-oscillator-q31": {
        "slug": "sine",
        "base": "contracts/task011c/implementation-binding-sine-r2.json",
        "eligibility": "contracts/task011c/binding-eligibility-sine-r2.json",
        "source": ("axoloti-factory", FACTORY_COMMIT, "objects/osc/sine.axo", "bf865e647b2eea2ebe1ef852038994f2dea8f1e8b8e60e1133e1d580a3402a4b"),
        "numeric": {"pitch": "signed-q21", "frequency": "mtof48k-ext-q31", "phase": "unsigned-32-wrap", "waveform": "sin-q31-right-shift-4-to-q27"},
        "state": {"initial_phase": 0, "instances": "independent-state-per-node"},
        "schedule": {"rate": "sixteen-audio-samples-per-control-cycle", "sample_order": ["frequency-add", "phase-modulation-add", "sine-interpolate", "q27-output"]},
    },
    "linear-mix-q27": {
        "slug": "crossfader",
        "base": "contracts/task009/crossfader-mixed-legacy-v0-r2.json",
        "eligibility": "contracts/task011c/crossfader-mixed-eligibility-r3.json",
        "source": ("axoloti-factory", FACTORY_COMMIT, "objects/mix/xfade.axo", "8169f5ec39eabe8f76bf5025ab2c68df0bed531c0c8aeb8c51bba3307859e361"),
        "numeric": {"inputs": "signed-q27", "control": "unsigned-saturate-27", "formula": "arithmetic-right-shift-27-of-i2-times-c-plus-i1-times-two-to-27-minus-c"},
        "state": {"private_state": "none", "public_control": "previous-cycle-latch"},
        "schedule": {"rate": "sixteen-audio-samples-per-control-cycle", "second_input": "previous-sine-b-block"},
    },
    "state-variable-filter-q27": {
        "slug": "filter",
        "base": "contracts/task011c/implementation-binding-filter-r2.json",
        "eligibility": "contracts/task011c/binding-eligibility-filter-r2.json",
        "source": ("axoloti-factory", FACTORY_COMMIT, "objects/filter/multimode svf m.axo", "e73239cd072b9dc63debd2ec95a32ec0bf79ae1be1754336a1d5928d4e8af057"),
        "numeric": {"signal": "signed-q27", "pitch": "signed-q21", "resonance": "unsigned-q27", "intrinsics": ["mtof48k_ext_q31", "sin_q31", "___SMMUL", "__SSAT", "__USAT"]},
        "state": {"initial_low": 0, "initial_band": 0, "width": "signed-32-wrap"},
        "schedule": {"rate": "sixteen-audio-samples-per-control-cycle", "sample_order": ["notch", "low", "high", "band", "outputs"]},
    },
    "stereo-audio-output-q27": {
        "slug": "output",
        "base": "contracts/task011c/implementation-binding-output-r2.json",
        "eligibility": "contracts/task011c/binding-eligibility-output-r2.json",
        "source": ("axoloti-factory", FACTORY_COMMIT, "objects/audio/out stereo.axo", "d8392b522b54be3bdfa5e671975a2a675ac494e9d1dc8bee2586dcd1eaecc7e3"),
        "numeric": {"inputs": "signed-q27", "accumulation": "signed-saturate-28", "abi_output": "signed-saturate-28-left-shift-4"},
        "state": {"audio_accumulators": "cleared-each-control-cycle", "vu_displays": "first-sample"},
        "schedule": {"rate": "sixteen-audio-samples-per-control-cycle", "channels": "interleaved-stereo"},
    },
}


def _record(record: dict[str, Any], schema_name: str) -> dict[str, Any]:
    value = copy.deepcopy(record)
    value["content_hash"] = "sha256:" + "0" * 64
    schema = core.load_json(ROOT / "schemas" / schema_name)
    errors = core.schema_errors(value, schema, schema)
    if errors:
        raise ValueError(f"{schema_name}: " + "; ".join(errors))
    value["content_hash"] = core.record_content_hash(value, schema)
    return value


def _ref(record: dict[str, Any], id_field: str) -> dict[str, Any]:
    return {id_field: record[id_field], "revision": record["revision"], "content_hash": record["content_hash"]}


def _semantic_ref(record: dict[str, Any], id_field: str, input_kind: str = "semantic-record") -> dict[str, Any]:
    return {"input_kind": input_kind, "stable_id": record[id_field], "revision": record["revision"], "content_hash": record["content_hash"]}


def _source(source_id: str, commit: str, path: str, digest: str, license_declaration: str) -> dict[str, Any]:
    return {"source_id": source_id, "commit": commit, "portable_path": path, "byte_sha256": digest, "license_declaration": license_declaration}


def _semantic_lines(value: dict[str, Any]) -> list[str]:
    return [key + "=" + core.canonical_json(item) for key, item in value.items()]


def _operation_spec(opcode: str, data: dict[str, Any], golden_digest: str) -> dict[str, Any]:
    object_source = data["source"]
    sources = [
        _source(*object_source, "BSD"),
        _source("patcher", PATCHER_COMMIT, "firmware/axoloti_math.h", "95ccbdbea15078a6ef207e87749bb8defaa4662b6eebddfb40944f350b549191", "GPL-3.0-or-later"),
        _source("patcher", PATCHER_COMMIT, "firmware/patch.h", "fe64781fac09b82d6f45eafbb60efcfe7b1af655af5dcccaac232e29c31dad2c", "GPL-3.0-or-later"),
        _source("patcher", PATCHER_COMMIT, "firmware/xpatch.h", "85e4abc70123952e8f47217751f2b6f7299e7cb978b6c994acf7b383425379a0", "GPL-3.0-or-later"),
        _source("schuss", SCHUSS_COMMIT, "evidence/task-011c-v1/artifacts/sha256/" + ORACLE_SHA256, ORACLE_SHA256, "repository-declared"),
    ]
    if opcode in {"square-lfo-q31", "sine-oscillator-q31", "state-variable-filter-q27"}:
        sources.append(_source("patcher", PATCHER_COMMIT, "firmware/axoloti_math.c", "ba4e3146eb3e6cf436ee836d1f5c82d9b5c13606e3ab0f273ff43432ef3626c1", "GPL-3.0-or-later"))
    return _record({
        "schema_version": "direct-operation-spec-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "direct_operation_spec_id": OPERATION_SPEC_IDS[opcode],
        "revision": 1,
        "opcode": opcode,
        "compatibility_mode": "legacy-equivalent-task011c",
        "contract_reference": copy.deepcopy(CONTRACT_REFERENCES[opcode]),
        "source_authority": sources,
        "runtime_dependencies": ["authenticated-ksoloti-patch-abi", "authenticated-ksoloti-runtime-math", "task011c-generated-cpp-oracle"],
        "numeric_semantics": _semantic_lines(data["numeric"]),
        "state_semantics": _semantic_lines(data["state"]),
        "schedule_semantics": _semantic_lines(data["schedule"]),
        "golden_vector_set": {
            "schema_version": "task016-semantic-goldens-v1",
            "portable_path": "evidence/task016-completion-v1/semantic-goldens.json",
            "section": "operations." + opcode,
            "byte_sha256": golden_digest,
        },
    }, "direct-operation-spec-v0.schema.json")


def _direct_binding(opcode: str, base: dict[str, Any], revision: int, promoted: bool) -> dict[str, Any]:
    value = copy.deepcopy(base)
    value["schema_version"] = "implementation-binding-v1"
    value["implementation_id"] = DIRECT_BINDING_IDS[opcode]
    value["revision"] = revision
    value["realization"] = {"form": "native-cpp", "portable_symbol": "schuss_direct_" + opcode.replace("-", "_")}
    for mapping in value["facet_mappings"]:
        facet = mapping["contract_facet"]
        mapping["implementation_seam"] = {
            "seam_kind": "native-symbol",
            "symbol": "schuss_direct_" + opcode.replace("-", "_") + "_" + facet["facet_kind"] + "_" + facet["facet_id"].rsplit("-", 1)[-1],
        }
    if promoted:
        value["evidence_refs"] = sorted(set(value["evidence_refs"] + ["fixture:task016-semantic-goldens"]))
        value["selection_state"]["rationale"] = "Task 016 preserves the exact reviewed Task 011C integer semantics through a native C++ realization; eligibility remains separately explicit."
    else:
        value["selection_state"]["rationale"] = "Task 016 candidate native realization is not selectable until the operation and graph semantic vectors are recorded."
    return _record(value, "implementation-binding-v1.schema.json")


def _promotion_claim(opcode: str, candidate: dict[str, Any], spec: dict[str, Any], number: int) -> dict[str, Any]:
    return _record({
        "schema_version": "evidence-claim-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "evidence_claim_id": f"schuss-evidence-claim-{number:06d}",
        "revision": 1,
        "level": 2,
        "level_name": "component-graph-resolution",
        "subject_reference": {"subject_kind": "semantic-record", "stable_id": spec["direct_operation_spec_id"], "revision": 1, "content_hash": spec["content_hash"], "stage": "target-independent-graph-validation"},
        "method": "task016-exact-semantic-golden-vectors",
        "outcome": "passed",
        "evidence_inputs": [_semantic_ref(candidate, "implementation_id"), _semantic_ref(spec, "direct_operation_spec_id")],
        "limitations": ["It establishes no connected-device, real-time, or audible behavior.", "Runtime pitch and sine table values remain owned by the separately authenticated Ksoloti runtime boundary."],
        "producer_identity": {"producer_kind": "validator", "producer_id": "schuss-task016-validator", "version": "task016-v1", "content_hash": "sha256:af955131371266f4da38327b42e109090c5d46a6f53e21d75c967c63a435affd"},
    }, "evidence-claim-v0.schema.json")


def _backend() -> dict[str, Any]:
    template = core.load_json(ROOT / "contracts/task011c/legacy-ksoloti-r3.json")
    value = copy.deepcopy(template)
    value.update({
        "backend_id": "schuss-backend-000002",
        "revision": 1,
        "display_name": "Direct native Ksoloti runtime backend",
        "lowering_identity": {"backend_kind": "direct-ksoloti-runtime", "contract_version": "direct-gills-task016-v1"},
        "supported_realization_forms": ["native-cpp"],
        "bridge_boundary": {"kind": "direct-runtime-abi", "location": "packages/schuss_core", "legacy_boundary_artifact": "generated-cpp", "execution_status": "not-run"},
        "target_pairings": [{"target_reference": copy.deepcopy(TARGET_REFERENCE), "contract_state": "declared", "rationale": "Task 016 targets the authenticated existing Ksoloti runtime ABI without Java, AXP, legacy-object calls, or a hidden adapter."}],
        "artifact_declarations": [item for item in template["artifact_declarations"] if item["artifact_kind"] not in {"legacy-boundary-patch", "build-package"}],
    })
    return _record(value, "backend-v0.schema.json")


def _eligibility(opcode: str, promoted: dict[str, Any], claim: dict[str, Any], backend: dict[str, Any], base: dict[str, Any], number: int) -> dict[str, Any]:
    evidence = _ref(claim, "evidence_claim_id")
    return _record({
        "schema_version": "binding-eligibility-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "binding_eligibility_id": f"schuss-binding-eligibility-{number:06d}",
        "revision": 1,
        "binding_reference": _ref(promoted, "implementation_id"),
        "contract_reference": copy.deepcopy(CONTRACT_REFERENCES[opcode]),
        "allowed_pair": {"target_reference": copy.deepcopy(TARGET_REFERENCE), "backend_reference": _ref(backend, "backend_id"), "state": {"status": "supported", "evidence_level": 2, "evidence_refs": [evidence]}},
        "realization_form": "native-cpp",
        "capability_requirements": copy.deepcopy(base["capability_requirements"]),
        "dependency_requirements": [],
        "resource_requirements": [],
        "required_evidence_level": 2,
        "compatibility_evidence": [evidence],
        "selection_policy": {"policy_id": f"schuss-selection-policy-{number:06d}", "version": 1, "priority": 200, "ranking_rule": "higher-explicit-priority", "tie_behavior": "ambiguous", "implicit_fallback": False},
        "unresolved_questions": [],
    }, "binding-eligibility-v0.schema.json")


def _request(backend: dict[str, Any]) -> dict[str, Any]:
    value = core.load_json(ROOT / "contracts/task011c/four-step-dual-sine-build-request-r2.json")
    value["revision"] = 3
    value["backend_reference"] = _ref(backend, "backend_id")
    value["binding_overrides"] = []
    return _record(value, "build-request-v0.schema.json")


def generated() -> tuple[dict[str, bytes], bytes]:
    golden_bytes = core.canonical_json(semantic_goldens()).encode("utf-8") + b"\n"
    golden_digest = hashlib.sha256(golden_bytes).hexdigest()
    records: dict[str, tuple[str, dict[str, Any]]] = {}
    specs: dict[str, dict[str, Any]] = {}
    candidates: dict[str, dict[str, Any]] = {}
    promoted: dict[str, dict[str, Any]] = {}
    claims: dict[str, dict[str, Any]] = {}
    backend = _backend()
    records["direct-backend.json"] = ("backend", backend)
    for index, (opcode, data) in enumerate(OPERATION_DATA.items(), 1):
        spec = _operation_spec(opcode, data, golden_digest)
        base = core.load_json(ROOT / data["base"])
        candidate = _direct_binding(opcode, base, 1, False)
        claim = _promotion_claim(opcode, candidate, spec, 17 + index)
        final = _direct_binding(opcode, base, 2, True)
        eligibility_base = core.load_json(ROOT / data["eligibility"])
        eligibility = _eligibility(opcode, final, claim, backend, eligibility_base, 7 + index)
        specs[opcode], candidates[opcode], promoted[opcode], claims[opcode] = spec, candidate, final, claim
        slug = data["slug"]
        records[f"operation-spec-{slug}.json"] = ("direct-operation-spec", spec)
        records[f"implementation-binding-{slug}-candidate-r1.json"] = ("implementation-binding", candidate)
        records[f"promotion-evidence-{slug}.json"] = ("evidence", claim)
        records[f"implementation-binding-{slug}-r2.json"] = ("implementation-binding", final)
        records[f"binding-eligibility-{slug}.json"] = ("eligibility", eligibility)
    request = _request(backend)
    records["four-step-dual-sine-direct-build-request-r3.json"] = ("request", request)

    file_bytes = {
        "evidence/task016-completion-v1/semantic-goldens.json": golden_bytes,
        **{
            "contracts/task016/" + name: core.canonical_json(record).encode("utf-8") + b"\n"
            for name, (_, record) in records.items()
        },
    }
    parent = core.load_json(PARENT)
    schema_paths = (
        "schemas/direct-operation-spec-v0.schema.json",
        "schemas/normalized-dsp-module-v1.schema.json",
        "schemas/direct-frontend-result-v1.schema.json",
    )
    schema_members = copy.deepcopy(parent["schema_members"])
    for relative in schema_paths:
        schema = core.load_json(ROOT / relative)
        schema_members.append({"schema_version": schema["$id"].removesuffix(".schema.json"), "portable_path": relative, "byte_sha256": core.sha256_file(ROOT / relative)})
    record_members = copy.deepcopy(parent["record_members"])
    for name, (kind, record) in records.items():
        relative = "contracts/task016/" + name
        id_field = next(field for field in record_set_rules.ID_FIELDS if field in record)
        record_members.append({"record_kind": kind, "stable_id": record[id_field], "revision": record["revision"], "content_hash": record["content_hash"], "portable_path": relative, "byte_sha256": hashlib.sha256(file_bytes[relative]).hexdigest()})
    manifest = {
        "schema_version": "record-set-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "record_set_id": "schuss-record-set-000010",
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "purpose": "prospective-task",
        "parent_reference": {"status": "included", **{key: parent[key] for key in ("record_set_id", "revision", "content_hash")}},
        "schema_members": sorted(schema_members, key=lambda item: (item["schema_version"], item["portable_path"])),
        "record_members": sorted(record_members, key=lambda item: (item["byte_sha256"], item["portable_path"])),
        "enforced_directories": sorted(parent["enforced_directories"] + ["contracts/task016"]),
    }
    manifest_schema = core.load_json(ROOT / record_set_rules.RECORD_SET_SCHEMA)
    manifest["content_hash"] = core.record_content_hash(manifest, manifest_schema)
    manifest_bytes = core.canonical_json(manifest).encode("utf-8") + b"\n"
    return file_bytes, manifest_bytes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files, manifest = generated()
    files[OUTPUT.relative_to(ROOT).as_posix()] = manifest
    stale = [relative for relative, payload in files.items() if not (ROOT / relative).is_file() or (ROOT / relative).read_bytes() != payload]
    if args.check:
        if stale:
            print("Task 016 generated files are stale: " + ", ".join(sorted(stale)), file=sys.stderr)
            return 1
    else:
        for obsolete in RECORD_ROOT.glob("implementation-binding-*.json"):
            if "candidate-r3" in obsolete.name or obsolete.name.endswith("-r4.json"):
                obsolete.unlink()
        for relative, payload in files.items():
            path = ROOT / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
    print("Task 016 records " + ("passed" if args.check else "generated") + f": files={len(files)} manifest_sha256={hashlib.sha256(manifest).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
