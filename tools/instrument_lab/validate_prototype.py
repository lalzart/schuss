#!/usr/bin/env python3
"""Validate one noncanonical Instrument Lab consumer and derived evidence."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

from common import (
    ContractError,
    canonical_json,
    exact_keys,
    load_json,
    relative_authority_path,
    sha256_file,
    string_list,
)

INDEX_KEYS = {
    "schema_version", "prototype_id", "revision", "lane", "claims",
    "authorities", "core_adapter", "evidence", "handoff",
}
AUTHORITY_KEYS = {
    "proposal", "implementation_contract", "state_matrix", "control_map",
    "dsp_topology", "experiment", "validation_plan", "results", "gaps",
    "controller_topology", "source_package_handoff",
}
REQUIRED_AUTHORITIES = AUTHORITY_KEYS - {"source_package_handoff"}
FILE_REF_KEYS = {"path", "sha256"}
CORE_KEYS = {
    "target", "sample_representation", "sample_rate_hz",
    "maximum_host_block", "internal_quantum", "conversion_owner",
    "semantic_event_capacity", "output_clearing",
}
EVIDENCE_KEYS = {"requested", "deferred"}
HANDOFF_KEYS = {
    "working_artifact", "allowed_edits", "reusable_entry_points",
    "required_commands", "stop_conditions", "open_decisions",
}
TOPOLOGY_KEYS = {
    "schema_version", "prototype_id", "claims", "public_facets", "nodes",
    "connections", "feedback_edges", "fusion_boundary",
}
FACET_KEYS = {"ports", "parameters", "actions", "displays"}
FACET_ITEM_KEYS = {"local_role", "name", "data_type", "direction"}
NODE_KEYS = {
    "local_role", "name", "origin", "responsibility", "state_owner",
    "internals", "unresolved_component_contract",
}
EDGE_KEYS = {"from", "to", "kind"}
FUSION_KEYS = {"local_role", "includes", "implementation_note"}
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
ID_RE = re.compile(r"^[a-z][a-z0-9-]*$")
ROLE_RE = re.compile(r"^role\.[a-z][a-z0-9_.-]*$")
CANONICAL_ID_RE = re.compile(r"^(schuss-|component:|graph:|provider:|runtime:|target:|backend:)")
FORBIDDEN_TOPOLOGY = re.compile(
    r"(^|[^a-z])(controller|midi[_ -]?cc|juce|provider|runtime[_ -]?factory|"
    r"target[_ -]?id|backend[_ -]?id|source[_ -]?path)([^a-z]|$)", re.IGNORECASE
)


def _prototype_id(value: Any, where: str) -> str:
    if not isinstance(value, str) or not ID_RE.fullmatch(value):
        raise ContractError("INVALID_PROTOTYPE_ID", where)
    if CANONICAL_ID_RE.search(value) or "@" in value or ":" in value:
        raise ContractError("CANONICAL_ID_FORBIDDEN", value)
    return value


def _local_role(value: Any, where: str) -> str:
    if not isinstance(value, str) or not ROLE_RE.fullmatch(value):
        raise ContractError("INVALID_LOCAL_ROLE", where)
    if CANONICAL_ID_RE.search(value):
        raise ContractError("CANONICAL_ID_FORBIDDEN", value)
    return value


def _validate_ref(repo_root: Path, value: Any, where: str) -> tuple[str, str]:
    ref = exact_keys(value, FILE_REF_KEYS, where)
    rel = relative_authority_path(ref["path"])
    digest = ref["sha256"]
    if not isinstance(digest, str) or not HASH_RE.fullmatch(digest):
        raise ContractError("INVALID_SHA256", where)
    candidate = repo_root.joinpath(*rel.parts)
    try:
        candidate.resolve().relative_to(repo_root.resolve())
    except ValueError as exc:
        raise ContractError("ESCAPING_AUTHORITY_PATH", str(rel)) from exc
    actual = sha256_file(candidate)
    if actual != digest:
        raise ContractError("AUTHORITY_HASH_MISMATCH", f"{rel}: {digest} != {actual}")
    return str(rel), digest


def validate_topology(path: Path, expected_id: str) -> dict[str, Any]:
    topology = exact_keys(load_json(path), TOPOLOGY_KEYS, "dsp-topology")
    if topology["schema_version"] != "schuss-instrument-lab-dsp-topology-v1":
        raise ContractError("SCHEMA_VERSION_MISMATCH", "dsp-topology")
    if _prototype_id(topology["prototype_id"], "topology.prototype_id") != expected_id:
        raise ContractError("PROTOTYPE_ID_MISMATCH", "topology")
    claims = exact_keys(
        topology["claims"], {"canonical_schuss_record", "executable_graph"},
        "topology.claims",
    )
    if claims != {"canonical_schuss_record": False, "executable_graph": False}:
        raise ContractError("FALSE_CLAIM_REQUIRED", "topology.claims")

    serialized = canonical_json(topology)
    match = FORBIDDEN_TOPOLOGY.search(serialized)
    if match:
        raise ContractError("FORBIDDEN_TOPOLOGY_LEAKAGE", match.group(0).strip())

    facets = exact_keys(topology["public_facets"], FACET_KEYS, "public_facets")
    roles: set[str] = set()
    for facet_name in sorted(FACET_KEYS):
        items = facets[facet_name]
        if not isinstance(items, list):
            raise ContractError("INVALID_FACET_LIST", facet_name)
        for index, item in enumerate(items):
            entry = exact_keys(item, FACET_ITEM_KEYS, f"{facet_name}[{index}]")
            role = _local_role(entry["local_role"], f"{facet_name}[{index}]")
            if role in roles:
                raise ContractError("DUPLICATE_LOCAL_ROLE", role)
            roles.add(role)
            if entry["direction"] not in {"input", "output", "bidirectional", "none"}:
                raise ContractError("INVALID_DIRECTION", role)

    nodes = topology["nodes"]
    if not isinstance(nodes, list) or not nodes:
        raise ContractError("MISSING_TOPOLOGY_NODES", "nodes")
    for index, item in enumerate(nodes):
        node = exact_keys(item, NODE_KEYS, f"nodes[{index}]")
        role = _local_role(node["local_role"], f"nodes[{index}]")
        if role in roles:
            raise ContractError("DUPLICATE_LOCAL_ROLE", role)
        roles.add(role)
        if node["origin"] not in {"newly-designed", "source-derived", "adapter", "fused-implementation"}:
            raise ContractError("INVALID_NODE_ORIGIN", role)
        if not isinstance(node["state_owner"], bool):
            raise ContractError("INVALID_STATE_OWNER", role)
        string_list(node["internals"], f"{role}.internals")
        string_list(node["unresolved_component_contract"], f"{role}.unresolved", allow_empty=True)

    for collection_name in ("connections", "feedback_edges"):
        collection = topology[collection_name]
        if not isinstance(collection, list):
            raise ContractError("INVALID_EDGE_LIST", collection_name)
        for index, item in enumerate(collection):
            edge = exact_keys(item, EDGE_KEYS, f"{collection_name}[{index}]")
            for endpoint in (edge["from"], edge["to"]):
                if not isinstance(endpoint, str) or not endpoint.startswith("role."):
                    raise ContractError("INVALID_EDGE_ENDPOINT", str(endpoint))

    fusion = exact_keys(topology["fusion_boundary"], FUSION_KEYS, "fusion_boundary")
    _local_role(fusion["local_role"], "fusion_boundary.local_role")
    string_list(fusion["includes"], "fusion_boundary.includes")
    return topology


def promotion_report(topology: dict[str, Any]) -> dict[str, Any]:
    needs: list[dict[str, Any]] = []
    for node in sorted(topology["nodes"], key=lambda item: item["local_role"]):
        for contract in sorted(node["unresolved_component_contract"]):
            needs.append({"local_role": node["local_role"], "required_contract": contract})
    return {
        "schema_version": "schuss-instrument-lab-promotion-needs-v1",
        "prototype_id": topology["prototype_id"],
        "claims": {
            "allocates_canonical_records": False,
            "executable_graph": False,
        },
        "needs": needs,
    }


def handoff_markdown(index_path: str, index_hash: str, index: dict[str, Any]) -> str:
    authorities = index["authorities"]
    lines = [
        "# Instrument Lab implementation handoff",
        "",
        "This compact noncanonical index does not replace the approved proposal or task.",
        "",
        f"- Prototype: `{index['prototype_id']}` revision `{index['revision']}`",
        f"- Lane: `{index['lane']}`",
        f"- Index: `{index_path}` (`{index_hash}`)",
        f"- Working artifact: {index['handoff']['working_artifact']}",
        "",
        "## Exact authorities",
        "",
    ]
    for name in sorted(authorities):
        ref = authorities[name]
        if ref is not None:
            lines.append(f"- `{name}`: `{ref['path']}` (`{ref['sha256']}`)")
    for title, key in (
        ("Allowed edits", "allowed_edits"),
        ("Reusable entry points", "reusable_entry_points"),
        ("Required commands", "required_commands"),
        ("Stop conditions", "stop_conditions"),
        ("Open decisions", "open_decisions"),
    ):
        lines.extend(["", f"## {title}", ""])
        for item in index["handoff"][key]:
            lines.append(f"- {item}")
    lines.extend(["", "No app launch, device, real-time, listening, distribution, or production claim is made.", ""])
    return "\n".join(lines)


def validate_consumer(repo_root: Path, consumer_root: Path, *, write: bool, check_derived: bool) -> None:
    index_path = consumer_root / "prototype-index.json"
    index = exact_keys(load_json(index_path), INDEX_KEYS, "prototype-index")
    if index["schema_version"] != "schuss-instrument-lab-prototype-index-v1":
        raise ContractError("SCHEMA_VERSION_MISMATCH", "prototype-index")
    prototype_id = _prototype_id(index["prototype_id"], "prototype-index.prototype_id")
    if not isinstance(index["revision"], str) or not re.fullmatch(r"[0-9]+\.[0-9]+", index["revision"]):
        raise ContractError("INVALID_REVISION", str(index["revision"]))
    if index["lane"] not in {"new-design", "source-reimplementation", "non-musical-smoke"}:
        raise ContractError("INVALID_LANE", str(index["lane"]))
    claims = exact_keys(index["claims"], {"canonical_schuss_record", "production_ready"}, "claims")
    if claims != {"canonical_schuss_record": False, "production_ready": False}:
        raise ContractError("FALSE_CLAIM_REQUIRED", "prototype-index.claims")

    authorities = index["authorities"]
    if not isinstance(authorities, dict):
        raise ContractError("INVALID_OBJECT", "authorities")
    unknown = sorted(set(authorities) - AUTHORITY_KEYS)
    missing = sorted(REQUIRED_AUTHORITIES - set(authorities))
    if unknown:
        raise ContractError("UNKNOWN_FIELD", "authorities: " + ", ".join(unknown))
    if missing:
        raise ContractError("MISSING_AUTHORITY", ", ".join(missing))
    for name in sorted(authorities):
        ref = authorities[name]
        if name == "source_package_handoff" and ref is None:
            continue
        _validate_ref(repo_root, ref, f"authorities.{name}")

    core = exact_keys(index["core_adapter"], CORE_KEYS, "core_adapter")
    if core["sample_representation"] not in {"float32", "q27"}:
        raise ContractError("UNSUPPORTED_SAMPLE_REPRESENTATION", str(core["sample_representation"]))
    for key in ("sample_rate_hz", "maximum_host_block", "semantic_event_capacity"):
        if not isinstance(core[key], int) or core[key] <= 0:
            raise ContractError("INVALID_HOST_PROFILE", key)
    if not isinstance(core["internal_quantum"], int) or core["internal_quantum"] < 0:
        raise ContractError("INVALID_HOST_PROFILE", "internal_quantum")
    evidence = exact_keys(index["evidence"], EVIDENCE_KEYS, "evidence")
    string_list(evidence["requested"], "evidence.requested")
    string_list(evidence["deferred"], "evidence.deferred")
    handoff = exact_keys(index["handoff"], HANDOFF_KEYS, "handoff")
    if not isinstance(handoff["working_artifact"], str) or not handoff["working_artifact"]:
        raise ContractError("INVALID_HANDOFF", "working_artifact")
    for key in HANDOFF_KEYS - {"working_artifact"}:
        string_list(handoff[key], f"handoff.{key}", allow_empty=key == "open_decisions")

    topology_ref = authorities["dsp_topology"]
    topology_path = repo_root / relative_authority_path(topology_ref["path"])
    topology = validate_topology(topology_path, prototype_id)
    expected_promotion = canonical_json(promotion_report(topology))
    promotion_path = consumer_root / "PROMOTION_NEEDS.json"
    index_rel = index_path.relative_to(repo_root).as_posix()
    expected_handoff = handoff_markdown(index_rel, sha256_file(index_path), index)
    handoff_path = consumer_root / "IMPLEMENTATION_HANDOFF.md"
    derived = ((promotion_path, expected_promotion), (handoff_path, expected_handoff))
    if write:
        for path, content in derived:
            path.write_text(content, encoding="utf-8")
    if check_derived:
        for path, content in derived:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                raise ContractError("STALE_DERIVED_ARTIFACT", str(path.relative_to(repo_root)))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--consumer-root", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write-derived", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        validate_consumer(
            args.repo_root.resolve(), args.consumer_root.resolve(),
            write=args.write_derived, check_derived=args.check,
        )
    except ContractError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(f"validated Instrument Lab consumer: {args.consumer_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
