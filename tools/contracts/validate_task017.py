#!/usr/bin/env python3
"""Read-only complete Task 017 curated-core validator."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/contracts")]

from packages.schuss_core.control_plane import dispatch_operation, load_repository_context  # noqa: E402

import generate_task017_records as generator  # noqa: E402
import run_task017 as runner  # noqa: E402
import validator_core as core  # noqa: E402


RECORD_SET = ROOT / "contracts/record-sets/task017-curated-core-v1.json"
EVIDENCE_ROOT = ROOT / "evidence/task017-completion-v1"


def _by_id(values: tuple[dict[str, Any], ...], field: str) -> dict[tuple[str, int], dict[str, Any]]:
    return {(item[field], item["revision"]): item for item in values}


def _plan(context: Any, number: int) -> dict[str, Any]:
    request = next(
        item for item in context.records["request"]
        if item["build_request_id"] == f"schuss-build-request-{number:06d}"
        and item["revision"] == 1
    )
    reference = {key: request[key] for key in ("build_request_id", "revision", "content_hash")}
    return dispatch_operation(
        {
            "schema_version": "schuss-operation-request-v4",
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": "build.plan",
            "payload": {"build_request_reference": reference},
        },
        context,
    )


def validate() -> dict[str, Any]:
    generated_files, manifest = generator.generated()
    generated_files[RECORD_SET.relative_to(ROOT).as_posix()] = manifest
    stale = [
        relative for relative, payload in generated_files.items()
        if not (ROOT / relative).is_file() or (ROOT / relative).read_bytes() != payload
    ]
    if stale:
        raise ValueError("generated Task 017 records are stale: " + ", ".join(sorted(stale)))

    context = load_repository_context(record_set_path=RECORD_SET)
    if context.task007_summary["status"] != "valid":
        raise ValueError("Task 017 structural/component closure is invalid")
    if [item["status"] for item in context.task007_summary["evidence_levels"]] != ["passed", "passed"] + ["not-run"] * 6:
        raise ValueError("Task 017 structural evidence levels are not separated")

    packet = core.load_json(ROOT / "contracts/task017/selection-packet.json")
    if len(packet["included_families"]) != 12:
        raise ValueError("Task 017 selection ceiling changed")
    if len(packet["reference_instruments"]) != 2:
        raise ValueError("Task 017 reference-instrument count changed")
    categories = Counter(item["primary_category"] for item in packet["included_families"])
    for required in ("timing-sequencing", "sound-sources", "modulation-control", "shaping-dynamics", "delay-reverb"):
        if not categories[required]:
            raise ValueError(f"balanced core category is absent: {required}")
    if not packet["excluded_candidates"]:
        raise ValueError("selection packet has no explicit exclusions")

    contracts = _by_id(context.records["contracts"], "component_contract_id")
    bindings = _by_id(context.records["bindings"], "implementation_id")
    eligibilities = {
        (item["binding_reference"]["implementation_id"], item["binding_reference"]["revision"]): item
        for item in context.records["eligibility"]
        if item["allowed_pair"]["backend_reference"]["revision"] == 2
    }
    evidence = _by_id(context.records["evidence"], "evidence_claim_id")
    for offset, item in enumerate(packet["included_families"]):
        contract_id = f"schuss-component-contract-{10 + offset:06d}"
        implementation_id = item["implementation_reference"]["stable_id"]
        if (contract_id, 1) not in contracts:
            raise ValueError(f"selected family lacks exact contract: {contract_id}")
        for revision in (1, 2):
            if (implementation_id, revision) not in bindings:
                raise ValueError(f"selected implementation binding is absent: {implementation_id}@{revision}")
        eligibility = eligibilities.get((implementation_id, 2))
        if eligibility is None:
            raise ValueError(f"selected implementation eligibility is absent: {implementation_id}@2")
        claim_reference = eligibility["compatibility_evidence"]
        if len(claim_reference) != 1 or (
            claim_reference[0]["evidence_claim_id"], claim_reference[0]["revision"]
        ) not in evidence:
            raise ValueError(f"selected implementation evidence join is absent: {implementation_id}")
        if not item["unresolved_facts"]:
            raise ValueError(f"selected family loses explicit unresolved facts: {implementation_id}")
        state = eligibility["allowed_pair"]["state"]
        expected = "supported" if implementation_id == "schuss-implementation-000060" else "not-evaluated"
        if state["status"] != expected:
            raise ValueError(f"direct support boundary changed: {implementation_id}")

    new_instruments = [
        item for item in context.records["instruments"]
        if item["instrument_id"] in {"schuss-instrument-000003", "schuss-instrument-000004"}
    ]
    if len(new_instruments) != 2:
        raise ValueError("exactly two Task 017 instruments must resolve")
    if any(item["displays"] or item["actions"] for item in new_instruments):
        raise ValueError("Task 017 reference instruments must remain headless")
    graphs = _by_id(context.records["graphs"], "graph_id")
    percussion = graphs[("schuss-graph-000003", 1)]
    effects = graphs[("schuss-graph-000004", 1)]
    compound = graphs[("schuss-graph-000005", 1)]
    if not compound["compound_interface_mappings"]:
        raise ValueError("transparent compound mappings are absent")
    if not percussion["parameter_bindings"] or not effects["parameter_bindings"]:
        raise ValueError("reference parameter mappings are absent")
    fanout = Counter(
        (connection["source"]["node_id"], connection["source"]["facet_id"])
        for graph in (percussion, effects, compound)
        for connection in graph["connections"]
    )
    if max(fanout.values()) < 2:
        raise ValueError("reference graphs no longer exercise fanout")
    contract_closure = {
        node["contract_reference"]["component_contract_id"]
        for graph in (percussion, effects, compound)
        for node in graph["nodes"]
    }
    if len(contract_closure) < 10:
        raise ValueError("reference graphs no longer exercise reusable breadth")

    percussion_plan = _plan(context, 3)
    effects_plan = _plan(context, 4)
    if percussion_plan["status"] != "invalid" or {item["code"] for item in percussion_plan["diagnostics"]} != {"COMPILER_COMPOUND_INTERNAL_BINDING_UNRESOLVED"}:
        raise ValueError("percussion compound did not fail closed deterministically")
    if effects_plan["status"] != "unsupported" or {item["code"] for item in effects_plan["diagnostics"]} != {"COMPILER_BINDING_UNSUPPORTED"}:
        raise ValueError("effects graph did not report deterministic unsupported diagnostics")

    live_summary = runner.check_retained()
    if live_summary["direct_execution_performed"]:
        raise ValueError("unsupported Task 017 elements must not enter direct execution")

    corpus = context.records["catalog"][0]
    if corpus["schema_version"] != "catalog-corpus-v2" or corpus["revision"] != 2:
        raise ValueError("Task 017 exact catalog corpus was not selected")
    if context.catalog_projection is None or context.catalog_projection["schema_version"] != "catalog-projection-v2":
        raise ValueError("Task 017 catalog projection v2 is absent")
    return {
        "schema_version": "task017-validator-result-v1",
        "status": "valid",
        "record_set_reference": context.record_set_reference,
        "manifest_byte_sha256": hashlib.sha256(RECORD_SET.read_bytes()).hexdigest(),
        "selected_family_count": len(packet["included_families"]),
        "reference_instrument_count": len(new_instruments),
        "catalog_family_count": len(context.catalog_projection["families"]),
        "reference_contract_closure_count": len(contract_closure),
        "percussion_plan_status": percussion_plan["status"],
        "effects_plan_status": effects_plan["status"],
        "evidence_levels": live_summary["evidence_levels"],
        "device_actions_performed": False,
        "real_time_validation_performed": False,
        "audible_validation_performed": False,
        "ui_validation_performed": False,
        "hardware_actions_performed": False,
        "publication_performed": False,
    }


def main() -> int:
    try:
        result = validate()
    except (OSError, ValueError) as exc:
        print("Task 017 validation failed: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
