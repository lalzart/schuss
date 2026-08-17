"""Pure exact selection and normalized lowering for the Task 028 palette.

This module deliberately stops at backend-lowering IR.  It performs no source
generation, compiler invocation, project write, Java/AXP bridge call, device
operation, realtime measurement, or audio evaluation.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_TOOLS = REPOSITORY_ROOT / "tools/contracts"
if str(CONTRACT_TOOLS) not in sys.path:
    sys.path.insert(0, str(CONTRACT_TOOLS))

import target_backend_build_rules as target  # noqa: E402
import validator_core as core  # noqa: E402


PACKET_ID = "schuss-core-selection-000003"
PROOF_ID = "schuss-palette-lowering-proof-000001"
TARGET_ID = "schuss-compute-target-000001"
TARGET_REVISION = 2
BACKEND_ID = "schuss-backend-000002"
BACKEND_REVISION = 4
FORBIDDEN_IMPLEMENTATIONS = {
    "schuss-implementation-000056",  # accepted catalog Rings reverb source
    "schuss-implementation-000094",  # deliberately unallocated native slot
    "schuss-implementation-000096",  # catalog-only extended resonator
}


def _reference(record: Mapping[str, Any], field: str) -> dict[str, Any]:
    return {
        field: record[field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def _registry(
    values: Iterable[dict[str, Any]], field: str
) -> dict[tuple[str, int, str], dict[str, Any]]:
    result: dict[tuple[str, int, str], dict[str, Any]] = {}
    for value in values:
        key = (value[field], value["revision"], value["content_hash"])
        if key in result:
            raise ValueError(f"TASK028_DUPLICATE_EXACT_RECORD:{field}:{value[field]}")
        result[key] = value
    return result


def _resolve(
    registry: Mapping[tuple[str, int, str], dict[str, Any]],
    reference: Mapping[str, Any],
    field: str,
    code: str,
) -> dict[str, Any]:
    key = (reference[field], reference["revision"], reference["content_hash"])
    value = registry.get(key)
    if value is None:
        raise ValueError(code)
    return value


def lower_palette(
    packet: dict[str, Any],
    operation_specs: Iterable[dict[str, Any]],
    contracts: Iterable[dict[str, Any]],
    bindings: Iterable[dict[str, Any]],
    eligibility_records: Iterable[dict[str, Any]],
    compute_target: dict[str, Any],
    backend: dict[str, Any],
    capability_definitions: Mapping[str, dict[str, Any]],
) -> dict[str, Any]:
    """Resolve each closed packet entry and emit canonical operation IR."""

    if packet.get("selection_packet_id") != PACKET_ID or packet.get("revision") != 1:
        raise ValueError("TASK028_SELECTION_PACKET_IDENTITY_MISMATCH")
    if (compute_target.get("compute_target_id"), compute_target.get("revision")) != (
        TARGET_ID,
        TARGET_REVISION,
    ):
        raise ValueError("TASK028_TARGET_IDENTITY_MISMATCH")
    if (backend.get("backend_id"), backend.get("revision")) != (
        BACKEND_ID,
        BACKEND_REVISION,
    ):
        raise ValueError("TASK028_BACKEND_IDENTITY_MISMATCH")
    if packet.get("target_reference") != _reference(compute_target, "compute_target_id"):
        raise ValueError("TASK028_PACKET_TARGET_REFERENCE_MISMATCH")
    if packet.get("backend_reference") != _reference(backend, "backend_id"):
        raise ValueError("TASK028_PACKET_BACKEND_REFERENCE_MISMATCH")

    additions = packet.get("additions", [])
    if len(additions) != 15:
        raise ValueError("TASK028_ADDITION_COUNT_MISMATCH")
    identities = [item["native_binding_reference"]["implementation_id"] for item in additions]
    if len(set(identities)) != 15 or FORBIDDEN_IMPLEMENTATIONS.intersection(identities):
        raise ValueError("TASK028_NATIVE_ALLOCATION_INVALID")

    contract_registry = _registry(contracts, "component_contract_id")
    binding_registry = _registry(bindings, "implementation_id")
    eligibility_registry = _registry(eligibility_records, "binding_eligibility_id")
    spec_registry = _registry(operation_specs, "direct_operation_spec_id")
    lowered: list[dict[str, Any]] = []

    for index, addition in enumerate(additions, start=1):
        contract = _resolve(
            contract_registry,
            addition["contract_reference"],
            "component_contract_id",
            "TASK028_CONTRACT_REFERENCE_UNRESOLVED",
        )
        binding = _resolve(
            binding_registry,
            addition["native_binding_reference"],
            "implementation_id",
            "TASK028_NATIVE_BINDING_REFERENCE_UNRESOLVED",
        )
        eligibility = _resolve(
            eligibility_registry,
            addition["eligibility_reference"],
            "binding_eligibility_id",
            "TASK028_ELIGIBILITY_REFERENCE_UNRESOLVED",
        )
        operation = _resolve(
            spec_registry,
            addition["operation_spec_reference"],
            "direct_operation_spec_id",
            "TASK028_OPERATION_REFERENCE_UNRESOLVED",
        )
        if binding["contract_reference"] != addition["contract_reference"]:
            raise ValueError("TASK028_BINDING_CONTRACT_MISMATCH")
        if eligibility["binding_reference"] != addition["native_binding_reference"]:
            raise ValueError("TASK028_ELIGIBILITY_BINDING_MISMATCH")
        if eligibility["contract_reference"] != addition["contract_reference"]:
            raise ValueError("TASK028_ELIGIBILITY_CONTRACT_MISMATCH")
        if operation["native_binding_reference"] != addition["native_binding_reference"]:
            raise ValueError("TASK028_OPERATION_BINDING_MISMATCH")
        if operation["contract_reference"] != addition["contract_reference"]:
            raise ValueError("TASK028_OPERATION_CONTRACT_MISMATCH")
        if operation["source_identity"] != addition["source_identity"]:
            raise ValueError("TASK028_SOURCE_IDENTITY_MISMATCH")

        graph = {
            "nodes": [
                {
                    "node_id": f"task028-candidate-node-{index:06d}",
                    "contract_reference": copy.deepcopy(addition["contract_reference"]),
                }
            ]
        }
        traces = target.resolve_graph_bindings(
            graph,
            compute_target,
            backend,
            eligibility_registry.values(),
            binding_registry,
            dict(capability_definitions),
        )
        if len(traces) != 1 or traces[0]["status"] != "selected":
            status = traces[0]["status"] if traces else "absent"
            raise ValueError(f"TASK028_BINDING_NOT_INDEPENDENTLY_SELECTED:{status}")
        if traces[0]["selected_binding_reference"] != addition["native_binding_reference"]:
            raise ValueError("TASK028_SELECTED_BINDING_MISMATCH")

        mapped_facets = sorted(
            [
                {
                    "facet_kind": item["contract_facet"]["facet_kind"],
                    "facet_id": item["contract_facet"]["facet_id"],
                    "native_symbol": item["implementation_seam"]["symbol"],
                }
                for item in binding["facet_mappings"]
            ],
            key=core.canonical_json,
        )
        lowered.append(
            {
                "candidate_id": addition["candidate_id"],
                "family_reference": copy.deepcopy(addition["family_reference"]),
                "source_identity": copy.deepcopy(addition["source_identity"]),
                "contract_reference": copy.deepcopy(addition["contract_reference"]),
                "native_binding_reference": copy.deepcopy(addition["native_binding_reference"]),
                "eligibility_reference": copy.deepcopy(addition["eligibility_reference"]),
                "operation_spec_reference": copy.deepcopy(addition["operation_spec_reference"]),
                "selection_status": "selected",
                "opcode": operation["opcode"],
                "rate_domain": operation["rate_domain"],
                "facet_lowering": mapped_facets,
                "runtime_dependencies": copy.deepcopy(operation["runtime_dependencies"]),
                "state_semantics": copy.deepcopy(operation["state_semantics"]),
                "schedule_semantics": copy.deepcopy(operation["schedule_semantics"]),
                "exclusions": copy.deepcopy(operation["exclusions"]),
            }
        )

    return {
        "schema_version": "palette-lowering-proof-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "palette_lowering_proof_id": PROOF_ID,
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "selection_packet_reference": _reference(packet, "selection_packet_id"),
        "target_reference": _reference(compute_target, "compute_target_id"),
        "backend_reference": _reference(backend, "backend_id"),
        "lowering_boundary": "normalized-operation-ir-only",
        "selection_count": 15,
        "operations": sorted(lowered, key=lambda item: item["candidate_id"]),
        "evidence_levels": [
            {"level": level, "status": "passed" if level <= 3 else "not-run"}
            for level in range(1, 9)
        ],
        "actions_performed": {
            "source_artifact_generation": False,
            "arm_compile_or_link": False,
            "java_or_legacy_axp": False,
            "device_or_hardware": False,
            "realtime_or_resource_measurement": False,
            "audible_listening": False,
            "git_or_publication": False,
        },
    }
