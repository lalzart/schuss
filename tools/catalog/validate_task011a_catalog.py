#!/usr/bin/env python3
"""Validate the exact Task 011A catalog corpus and derived projection."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.schuss_core.control_plane import load_repository_context


RECORD_SET = ROOT / "contracts/record-sets/task011a-catalog-v1.json"
OVERLAY = ROOT / "catalog/overlays/phase-4a-semantic-catalog-v0/catalog.json"
PROJECTION_SCHEMA = ROOT / "schemas/catalog-projection-v1.schema.json"
CORPUS_SCHEMA = ROOT / "schemas/catalog-corpus-v1.schema.json"
REQUEST_SCHEMA = ROOT / "schemas/operation-request-v2.schema.json"
RESULT_SCHEMA = ROOT / "schemas/operation-result-v2.schema.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate() -> dict[str, Any]:
    context = load_repository_context(ROOT, record_set_path=RECORD_SET)
    projection = context.catalog_projection
    if projection is None:
        raise ValueError("Task 011A catalog projection is absent")
    family_by_id = {
        value["family_reference"]["family_id"]: value
        for value in projection["families"]
    }
    expected_pilot = {f"schuss-family-{index:06d}" for index in range(1, 27)}
    if not expected_pilot <= set(family_by_id):
        raise ValueError("not every Phase 4A pilot family is projected")
    if set(family_by_id) != expected_pilot | {
        "schuss-family-000027",
        "schuss-family-000028",
    }:
        raise ValueError("catalog family scope exceeds the approved pilot and slice")

    implementations = {
        item["implementation_id"]: (family_id, item)
        for family_id, family in family_by_id.items()
        for item in family["implementations"]
    }
    if len(implementations) != 41:
        raise ValueError("catalog implementation count is not 41")
    expected_slice = {
        "schuss-implementation-000004": ("schuss-family-000002", "legacy-resolved-catalog-v0:object:9"),
        "schuss-implementation-000007": ("schuss-family-000003", "legacy-resolved-catalog-v0:object:549"),
        "schuss-implementation-000015": ("schuss-family-000009", "legacy-resolved-catalog-v0:object:159"),
        "schuss-implementation-000028": ("schuss-family-000018", "legacy-resolved-catalog-v0:object:460"),
        "schuss-implementation-000039": ("schuss-family-000027", "legacy-resolved-catalog-v0:object:209"),
        "schuss-implementation-000040": ("schuss-family-000028", "legacy-resolved-catalog-v0:object:215"),
        "schuss-implementation-000041": ("schuss-family-000022", "legacy-resolved-catalog-v0:object:918"),
    }
    for implementation_id, (family_id, observation) in expected_slice.items():
        actual_family, implementation = implementations[implementation_id]
        if actual_family != family_id or implementation["observation_references"] != [observation]:
            raise ValueError(f"slice identity closure is wrong for {implementation_id}")
    if "legacy-resolved-catalog-v0:object:920" in implementations[
        "schuss-implementation-000041"
    ][1]["observation_references"]:
        raise ValueError("the four-step realization reused observation 920")
    if implementations["schuss-implementation-000032"][1][
        "observation_references"
    ] != ["legacy-resolved-catalog-v0:object:920"]:
        raise ValueError("the accepted sixteen-step realization changed identity")

    crossfader = implementations["schuss-implementation-000028"][1]
    expected_readiness = [
        "contracted",
        "bound",
        "eligible",
        "compile-proven",
        "unresolved",
    ]
    if crossfader["readiness_states"] != expected_readiness:
        raise ValueError("Crossfader readiness is not derived at the accepted levels")
    forbidden_levels = {"device-tested", "real-time-tested", "audible-tested"}
    if forbidden_levels & set(crossfader["readiness_states"]):
        raise ValueError("Crossfader was promoted beyond accepted evidence")
    for implementation_id in (
        "schuss-implementation-000039",
        "schuss-implementation-000040",
        "schuss-implementation-000041",
    ):
        readiness = implementations[implementation_id][1]["readiness_states"]
        if readiness != ["catalogued-only", "unresolved"]:
            raise ValueError(f"catalog-only candidate was promoted: {implementation_id}")

    material = copy.deepcopy(projection)
    projection_hash = hashlib.sha256(
        json.dumps(material, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        .encode("utf-8")
    ).hexdigest()
    return {
        "status": "valid",
        "record_set_reference": context.record_set_reference,
        "projection_version": projection["projection_version"],
        "match_algorithm": projection["match_algorithm"],
        "input_closure_hash": projection["input_closure_hash"],
        "projection_byte_sha256": projection_hash,
        "phase4a_overlay_byte_sha256": _sha256(OVERLAY),
        "schema_byte_sha256": {
            "catalog_corpus_v1": _sha256(CORPUS_SCHEMA),
            "catalog_projection_v1": _sha256(PROJECTION_SCHEMA),
            "operation_request_v2": _sha256(REQUEST_SCHEMA),
            "operation_result_v2": _sha256(RESULT_SCHEMA),
        },
        "family_count": len(family_by_id),
        "phase4a_family_count": len(expected_pilot),
        "implementation_count": len(implementations),
        "slice_role_count": len(expected_slice),
        "crossfader_readiness": crossfader["readiness_states"],
        "later_evidence_levels_present": sorted(
            forbidden_levels
            & {
                state
                for _, implementation in implementations.values()
                for state in implementation["readiness_states"]
            }
        ),
    }


def main() -> int:
    print(json.dumps(validate(), ensure_ascii=False, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
