#!/usr/bin/env python3
"""Validate one noncanonical Instrument Lab consumer and derived evidence."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from common import (
    ContractError,
    canonical_json,
    exact_keys,
    load_json,
    relative_authority_path,
    sha256_file,
    string_list,
)
from tools.source_packages.validate_source_package import validate_package

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


def _validate_source_release_reference(repo_root: Path, value: Any, where: str) -> None:
    fields = {"content_hash", "path", "revision", "source_release_id"}
    reference = exact_keys(value, fields, where)
    relative = relative_authority_path(reference["path"])
    record = load_json(repo_root / relative)
    if not isinstance(record, dict):
        raise ContractError("INVALID_SOURCE_RELEASE_REFERENCE", where)
    actual = {key: record.get(key) for key in fields - {"path"}}
    expected = {key: reference[key] for key in fields - {"path"}}
    if actual != expected:
        raise ContractError("SOURCE_RELEASE_REFERENCE_DRIFT", where)


def _validate_source_dependencies(
    repo_root: Path,
    handoff_path: Path,
    expected_prototype_id: str,
) -> None:
    document = load_json(handoff_path)
    if not isinstance(document, dict) or document.get("schema_version") != "instrument-lab-source-dependencies-v1":
        return
    exact_keys(
        document,
        {
            "adapter", "authenticated_extracted_sources", "claims", "consumer_id",
            "physical_packages", "schema_version",
        },
        "source-dependencies",
    )
    if document["consumer_id"] != expected_prototype_id:
        raise ContractError("PROTOTYPE_ID_MISMATCH", "source-dependencies")
    claims = exact_keys(
        document["claims"],
        {
            "catalog_membership", "graph_identity", "implementation_identity",
            "provider_identity", "runtime_support",
        },
        "source-dependencies.claims",
    )
    if any(claims.values()):
        raise ContractError("FALSE_CLAIM_REQUIRED", "source-dependencies.claims")

    packages = document["physical_packages"]
    if not isinstance(packages, list) or not packages:
        raise ContractError("MISSING_PHYSICAL_PACKAGES", "source-dependencies")
    package_ids: set[str] = set()
    for index, item in enumerate(packages):
        entry = exact_keys(
            item,
            {
                "manifest", "package_id", "package_revision", "required_components",
                "source_release",
            },
            f"source-dependencies.physical_packages[{index}]",
        )
        manifest_path, _ = _validate_ref(
            repo_root, entry["manifest"], f"physical_packages[{index}].manifest"
        )
        _validate_source_release_reference(
            repo_root, entry["source_release"], f"physical_packages[{index}].source_release"
        )
        components = string_list(
            entry["required_components"], f"physical_packages[{index}].required_components"
        )
        package_root = (repo_root / manifest_path).parent
        manifest, errors = validate_package(
            package_root,
            expected_package_id=entry["package_id"],
            expected_package_revision=entry["package_revision"],
            expected_source_release_id=entry["source_release"]["source_release_id"],
            expected_source_release_revision=entry["source_release"]["revision"],
            expected_source_release_content_hash=entry["source_release"]["content_hash"],
            requested_components=components,
        )
        if errors:
            raise ContractError("INVALID_PHYSICAL_PACKAGE", errors[0].line())
        if manifest is None or entry["package_id"] in package_ids:
            raise ContractError("DUPLICATE_PHYSICAL_PACKAGE", str(entry["package_id"]))
        package_ids.add(entry["package_id"])

    adapter = exact_keys(document["adapter"], {"interface", "manifest"}, "source-dependencies.adapter")
    adapter_path, _ = _validate_ref(repo_root, adapter["manifest"], "source-dependencies.adapter.manifest")
    adapter_document = load_json(repo_root / adapter_path)
    if not isinstance(adapter_document, dict) or adapter_document.get("interface") != adapter["interface"]:
        raise ContractError("ADAPTER_INTERFACE_DRIFT", str(adapter["interface"]))
    adapter_claims = adapter_document.get("claims")
    if not isinstance(adapter_claims, dict) or any(adapter_claims.values()):
        raise ContractError("FALSE_CLAIM_REQUIRED", "adapter.claims")

    extracted = document["authenticated_extracted_sources"]
    if not isinstance(extracted, list):
        raise ContractError("INVALID_EXTRACTED_SOURCE_LIST", "source-dependencies")
    for index, item in enumerate(extracted):
        entry = exact_keys(
            item, {"manifest", "prerequisite", "source_release"},
            f"authenticated_extracted_sources[{index}]",
        )
        _validate_ref(repo_root, entry["manifest"], f"extracted_sources[{index}].manifest")
        _validate_source_release_reference(
            repo_root, entry["source_release"], f"extracted_sources[{index}].source_release"
        )
        if not isinstance(entry["prerequisite"], str) or not entry["prerequisite"]:
            raise ContractError("INVALID_EXTRACTED_SOURCE_PREREQUISITE", str(index))


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


def _validate_v2_approval_binding(
    repo_root: Path,
    index: dict[str, Any],
    authority_paths: dict[str, str],
) -> None:
    contract_path = repo_root / authority_paths["implementation_contract"]
    if contract_path.suffix != ".json":
        return
    contract = load_json(contract_path)
    if not isinstance(contract, dict):
        raise ContractError("INVALID_IMPLEMENTATION_CONTRACT", str(contract_path))
    if contract.get("schema_version") != "sonic-research-lab-implementation-contract-v2":
        return
    if contract.get("status") != "ready":
        raise ContractError("IMPLEMENTATION_CONTRACT_NOT_READY", authority_paths["implementation_contract"])
    proposal = contract.get("proposal")
    if not isinstance(proposal, dict):
        raise ContractError("INVALID_APPROVAL_BINDING", "implementation-contract.proposal")
    approval = proposal.get("approval")
    if (
        not isinstance(approval, dict)
        or approval.get("state") != "approved"
        or not isinstance(approval.get("reference"), str)
        or not approval["reference"]
    ):
        raise ContractError("PROPOSAL_NOT_APPROVED", authority_paths["implementation_contract"])
    proposal_ref = index["authorities"]["proposal"]
    if proposal.get("path") != proposal_ref["path"] or proposal.get("sha256") != proposal_ref["sha256"]:
        raise ContractError("APPROVAL_PROPOSAL_MISMATCH", authority_paths["implementation_contract"])
    if contract.get("work_type") != index["lane"]:
        raise ContractError("APPROVAL_LANE_MISMATCH", authority_paths["implementation_contract"])


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
    authority_paths: dict[str, str] = {}
    for name in sorted(authorities):
        ref = authorities[name]
        if name == "source_package_handoff" and ref is None:
            continue
        authority_paths[name] = _validate_ref(repo_root, ref, f"authorities.{name}")[0]
    _validate_v2_approval_binding(repo_root, index, authority_paths)
    if "source_package_handoff" in authority_paths:
        _validate_source_dependencies(
            repo_root,
            repo_root / authority_paths["source_package_handoff"],
            prototype_id,
        )

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
