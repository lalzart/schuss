#!/usr/bin/env python3
"""Component, implementation-binding, and graph domain rules."""

from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

import validator_core as core

# Retain the historic local name while binding it only to shared mechanisms.
base = core


FAMILY_SCHEMA_NAME = "catalog-family-companion-v0.schema.json"
CONTRACT_SCHEMA_NAME = "component-contract-v0.schema.json"
BINDING_SCHEMA_NAME = "implementation-binding-v0.schema.json"
GRAPH_SCHEMA_NAME = "dsp-graph-v0.schema.json"

FAMILY_SCHEMA_VERSION = "catalog-family-companion-v0"
CONTRACT_SCHEMA_VERSION = "component-contract-v0"
BINDING_SCHEMA_VERSION = "implementation-binding-v0"
GRAPH_SCHEMA_VERSION = "dsp-graph-v0"

OVERLAY_RELATIVE_PATH = Path("catalog/overlays/phase-4a-semantic-catalog-v0/catalog.json")
SNAPSHOT_RELATIVE_PATH = Path("catalog/snapshots/legacy-resolved-catalog-v0")


@dataclass(frozen=True)
class CoreValidation:
    summary: dict[str, Any]
    graph_targets: dict[tuple[str, int, str], dict[str, dict[str, Any]]]
    diagnostics: tuple[core.Diagnostic, ...]


sha256_file = core.sha256_file
load_jsonl = core.load_jsonl
_subject = core.record_subject
_exact_key = core.exact_key
_reference_key = core.reference_key
_record_files = core.record_files
_validate_structural_records = core.validate_structural_records
_canonical_member_hash = core.canonical_member_hash
_cycle_nodes = core.cycle_nodes


def _diagnostic(
    diagnostics: list[core.Diagnostic],
    code: str,
    subject: str,
    location: str,
    message: str,
) -> None:
    core.add_diagnostic(diagnostics, code, subject, location, message)


def _validate_family_companions(
    records: list[dict[str, Any]],
    overlay: dict[str, Any],
    overlay_sha256: str,
    manifest_sha256: str,
    diagnostics: list[base.Diagnostic],
) -> dict[tuple[str, int, str], dict[str, Any]]:
    families_by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for family in overlay["families"]:
        families_by_id[family["family_id"]].append(family)

    resolved: dict[tuple[str, int, str], dict[str, Any]] = {}
    for record in records:
        subject = _subject(record)
        source = record["source_member"]
        candidates = families_by_id.get(record["family_id"], [])
        if len(candidates) != 1:
            _diagnostic(
                diagnostics,
                "FAMILY_MEMBER_AMBIGUOUS",
                subject,
                "$.source_member.family_id",
                "the source overlay must contain exactly one member with this family ID",
            )
            continue
        family = candidates[0]
        if source["family_id"] != record["family_id"]:
            _diagnostic(
                diagnostics,
                "FAMILY_SOURCE_UNRESOLVED",
                subject,
                "$.source_member.family_id",
                "companion and source family identities disagree",
            )
        if source["overlay_id"] != overlay["overlay_id"] or source[
            "overlay_schema_version"
        ] != overlay["schema_version"]:
            _diagnostic(
                diagnostics,
                "FAMILY_SOURCE_UNRESOLVED",
                subject,
                "$.source_member",
                "the exact overlay identity or schema version did not resolve",
            )
        if source["overlay_sha256"] != overlay_sha256:
            _diagnostic(
                diagnostics,
                "FAMILY_SOURCE_HASH_MISMATCH",
                subject,
                "$.source_member.overlay_sha256",
                f"expected {overlay_sha256}",
            )
        if source["legacy_manifest_sha256"] != manifest_sha256 or overlay[
            "legacy_evidence"
        ]["manifest_sha256"] != manifest_sha256:
            _diagnostic(
                diagnostics,
                "FAMILY_SOURCE_HASH_MISMATCH",
                subject,
                "$.source_member.legacy_manifest_sha256",
                "companion and overlay must bind the same exact frozen manifest",
            )
        member_hash = _canonical_member_hash(family)
        if source["canonical_member_sha256"] != member_hash:
            _diagnostic(
                diagnostics,
                "FAMILY_MEMBER_HASH_MISMATCH",
                subject,
                "$.source_member.canonical_member_sha256",
                f"expected {member_hash}",
            )
        if source["family_schema_version"] != family["schema_version"]:
            _diagnostic(
                diagnostics,
                "FAMILY_SOURCE_UNRESOLVED",
                subject,
                "$.source_member.family_schema_version",
                "source member schema version disagrees with the exact overlay member",
            )
        resolved[_exact_key(record, "family_id")] = record
    return resolved


def _facet_maps(contract: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    return {
        "port": {item["facet_id"]: item for item in contract["ports"]},
        "parameter": {item["facet_id"]: item for item in contract["parameters"]},
        "attribute": {item["facet_id"]: item for item in contract["attributes"]},
        "action": {item["facet_id"]: item for item in contract["actions"]},
        "display": {item["facet_id"]: item for item in contract["displays"]},
    }


def _all_contract_facets(contract: dict[str, Any]) -> set[tuple[str, str]]:
    return {
        (kind, facet_id)
        for kind, facets in _facet_maps(contract).items()
        for facet_id in facets
    }


def _public_signature(contract: dict[str, Any]) -> str:
    """Return the stable public type signature, excluding mutable labels."""

    public: dict[str, list[dict[str, Any]]] = {}
    for collection in ("ports", "parameters", "attributes", "actions", "displays"):
        public[collection] = [
            {key: value for key, value in facet.items() if key != "display_label"}
            for facet in contract[collection]
        ]
    return base.canonical_json(public)


def _range_decimal(value: dict[str, Any]) -> tuple[Decimal, Decimal]:
    return Decimal(value["minimum"]), Decimal(value["maximum"])


def _project_port_domain(port: dict[str, Any]) -> dict[str, Any] | None:
    value = port["port_type"]["valid_range"]
    if value["status"] != "known":
        return None
    return {
        "minimum": value["minimum"],
        "maximum": value["maximum"],
        "unit": port["port_type"]["unit"],
    }


def _graph_range_to_instrument_domain(value: dict[str, Any]) -> dict[str, str]:
    return {
        "minimum": value["minimum"],
        "maximum": value["maximum"],
        "unit": value["unit"],
    }


def _validate_contracts(
    records: list[dict[str, Any]],
    families_by_ref: dict[tuple[str, int, str], dict[str, Any]],
    diagnostics: list[base.Diagnostic],
) -> dict[tuple[str, int, str], dict[str, Any]]:
    resolved: dict[tuple[str, int, str], dict[str, Any]] = {}
    signatures_by_id: dict[str, str] = {}
    for contract in records:
        subject = _subject(contract)
        signature = _public_signature(contract)
        prior_signature = signatures_by_id.get(contract["component_contract_id"])
        if prior_signature is not None and prior_signature != signature:
            _diagnostic(
                diagnostics,
                "CONTRACT_SIGNATURE_REVISION_MISMATCH",
                subject,
                "$",
                "one component contract ID cannot masquerade a different public signature as a revision",
            )
        else:
            signatures_by_id[contract["component_contract_id"]] = signature
        family_key = _reference_key(contract["family_reference"], "family_id")
        if family_key not in families_by_ref:
            _diagnostic(
                diagnostics,
                "FAMILY_REFERENCE_UNRESOLVED",
                subject,
                "$.family_reference",
                "the exact catalog-family companion tuple did not resolve",
            )

        local_ids: list[tuple[str, str]] = []
        for kind, facets in _facet_maps(contract).items():
            local_ids.extend((kind, facet_id) for facet_id in facets)
        local_ids.extend(("state", item["state_id"]) for item in contract["state_declarations"])
        seen_ids: dict[str, str] = {}
        for kind, identifier in local_ids:
            if identifier in seen_ids:
                _diagnostic(
                    diagnostics,
                    "DUPLICATE_LOCAL_ID",
                    subject,
                    "$",
                    f"{identifier!r} is reused by {seen_ids[identifier]} and {kind}",
                )
            seen_ids[identifier] = kind

        semantic_keys = [
            item["semantic_key"]
            for collection in ("ports", "parameters", "attributes", "actions", "displays")
            for item in contract[collection]
        ]
        if len(semantic_keys) != len(set(semantic_keys)):
            _diagnostic(
                diagnostics,
                "DUPLICATE_SEMANTIC_KEY",
                subject,
                "$",
                "public facet semantic keys must be unique within a contract",
            )

        port_ids = {item["facet_id"] for item in contract["ports"]}
        for port_id in contract["binding_capabilities"]["parameter_input_ports"]:
            port = next((item for item in contract["ports"] if item["facet_id"] == port_id), None)
            if port is None or port["direction"] != "inlet":
                _diagnostic(
                    diagnostics,
                    "BINDING_CAPABILITY_INVALID",
                    subject,
                    "$.binding_capabilities.parameter_input_ports",
                    "parameter input capability must name an inlet port",
                )
        action_ids = {item["facet_id"] for item in contract["actions"]}
        if not set(contract["binding_capabilities"]["action_inputs"]) <= action_ids:
            _diagnostic(
                diagnostics,
                "BINDING_CAPABILITY_INVALID",
                subject,
                "$.binding_capabilities.action_inputs",
                "action capability names an undeclared action",
            )

        for index, port in enumerate(contract["ports"]):
            location = f"$.ports[{index}].port_type"
            port_type = port["port_type"]
            valid_range = port_type["valid_range"]
            if valid_range["status"] != "known":
                _diagnostic(
                    diagnostics,
                    "TYPE_REQUIRED_FACT_UNRESOLVED",
                    subject,
                    f"{location}.valid_range",
                    "authoritative connection typing requires a known valid range",
                )
            else:
                minimum, maximum = _range_decimal(valid_range)
                if minimum >= maximum:
                    _diagnostic(
                        diagnostics,
                        "TYPE_RANGE_INVALID",
                        subject,
                        f"{location}.valid_range",
                        "range minimum must be less than maximum",
                    )
            representation = port_type["representation"]
            if representation["kind"] == "fixed-point" and representation[
                "fractional_bits"
            ] >= representation["width_bits"]:
                _diagnostic(
                    diagnostics,
                    "TYPE_REPRESENTATION_INVALID",
                    subject,
                    f"{location}.representation",
                    "fractional bits must be less than fixed-point width",
                )
            cardinality = port_type["cardinality"]
            maximum_connections = cardinality["maximum_connections"]
            if (
                isinstance(maximum_connections, int)
                and cardinality["minimum_connections"] > maximum_connections
            ):
                _diagnostic(
                    diagnostics,
                    "TYPE_CARDINALITY_INVALID",
                    subject,
                    f"{location}.cardinality",
                    "minimum connections exceed maximum connections",
                )
            optionality = port_type["optionality"]
            if port["direction"] == "outlet" and optionality["status"] != "not-applicable":
                _diagnostic(
                    diagnostics,
                    "TYPE_OPTIONALITY_INVALID",
                    subject,
                    f"{location}.optionality",
                    "outlet optionality must be explicitly not applicable",
                )
            if port["direction"] == "inlet" and optionality["status"] == "not-applicable":
                _diagnostic(
                    diagnostics,
                    "TYPE_OPTIONALITY_INVALID",
                    subject,
                    f"{location}.optionality",
                    "inlet optionality must be required or carry exact absence behavior",
                )
            expected_lifetime = "audio-block" if port_type["rate"] == "audio" else (
                "control-cycle" if port_type["rate"] == "control" else None
            )
            ownership = port_type["ownership"]
            if expected_lifetime is not None and (
                ownership["status"] != "defined"
                or ownership["lifetime"] != expected_lifetime
            ):
                _diagnostic(
                    diagnostics,
                    "TYPE_OWNERSHIP_INVALID",
                    subject,
                    f"{location}.ownership",
                    "stream rate and declared payload lifetime disagree",
                )

        state_model = contract["lifecycle"]["state_model"]
        if (state_model == "stateless") != (not contract["state_declarations"]):
            _diagnostic(
                diagnostics,
                "LIFECYCLE_STATE_MISMATCH",
                subject,
                "$.lifecycle.state_model",
                "stateless lifecycle and state declarations disagree",
            )

        compound = contract["compound_interface"]
        mapping_keys = compound["mapping_keys"]
        mapping_key_ids = [item["mapping_key"] for item in mapping_keys]
        if len(mapping_key_ids) != len(set(mapping_key_ids)):
            _diagnostic(
                diagnostics,
                "COMPOUND_MAPPING_DUPLICATE",
                subject,
                "$.compound_interface.mapping_keys",
                "compound mapping keys must be unique",
            )
        if compound["kind"] == "primitive" and mapping_keys:
            _diagnostic(
                diagnostics,
                "COMPOUND_MAPPING_INVALID",
                subject,
                "$.compound_interface",
                "primitive contracts cannot declare compound mapping keys",
            )
        if compound["kind"] == "transparent-compound":
            expected = {
                (kind, facet_id)
                for kind, facets in _facet_maps(contract).items()
                if kind != "attribute"
                for facet_id in facets
            }
            actual = {(item["facet_kind"], item["facet_id"]) for item in mapping_keys}
            if actual != expected:
                _diagnostic(
                    diagnostics,
                    "COMPOUND_MAPPING_INCOMPLETE",
                    subject,
                    "$.compound_interface.mapping_keys",
                    "transparent compound mapping keys must cover every public runtime facet exactly once",
                )
        resolved[_exact_key(contract, "component_contract_id")] = contract
    return resolved


def _port_type_mismatches(source: dict[str, Any], destination: dict[str, Any]) -> list[str]:
    source_type = source["port_type"]
    destination_type = destination["port_type"]
    mismatches: list[str] = []
    for dimension in (
        "domain",
        "rate",
        "channel_shape",
        "semantic_role",
        "representation",
        "unit",
        "ownership",
    ):
        if source_type[dimension] != destination_type[dimension]:
            mismatches.append(dimension)
    source_range = source_type["valid_range"]
    destination_range = destination_type["valid_range"]
    if source_range["status"] != "known" or destination_range["status"] != "known":
        mismatches.append("valid_range_unresolved")
    else:
        source_min, source_max = _range_decimal(source_range)
        destination_min, destination_max = _range_decimal(destination_range)
        subset = destination_min <= source_min and source_max <= destination_max
        if source_min == destination_min and source_range["minimum_inclusive"] and not destination_range[
            "minimum_inclusive"
        ]:
            subset = False
        if source_max == destination_max and source_range["maximum_inclusive"] and not destination_range[
            "maximum_inclusive"
        ]:
            subset = False
        if not subset or source_range["overflow_policy"] != destination_range["overflow_policy"]:
            mismatches.append("valid_range")
    return mismatches


def _resolve_node_facet(
    node_contracts: dict[str, dict[str, Any]],
    node_id: str,
    facet_kind: str,
    facet_id: str,
) -> dict[str, Any] | None:
    contract = node_contracts.get(node_id)
    if contract is None:
        return None
    return _facet_maps(contract).get(facet_kind, {}).get(facet_id)


def _validate_transform(
    source_domain: dict[str, Any],
    destination_domain: dict[str, Any],
    transform: dict[str, Any],
) -> bool:
    points = transform["points"]
    source_points = [Decimal(item["source"]) for item in points]
    destination_points = [Decimal(item["destination"]) for item in points]
    source_limits = [Decimal(source_domain["minimum"]), Decimal(source_domain["maximum"])]
    destination_limits = [
        Decimal(destination_domain["minimum"]),
        Decimal(destination_domain["maximum"]),
    ]
    if transform["polarity"] == "inverted":
        destination_limits.reverse()
    return source_points == source_limits and destination_points == destination_limits


def _validate_graphs(
    records: list[dict[str, Any]],
    contracts_by_ref: dict[tuple[str, int, str], dict[str, Any]],
    diagnostics: list[base.Diagnostic],
) -> tuple[
    dict[tuple[str, int, str], dict[str, Any]],
    dict[tuple[str, int, str], dict[str, dict[str, Any]]],
    dict[tuple[str, int, str], dict[str, dict[str, Any]]],
]:
    graphs_by_ref: dict[tuple[str, int, str], dict[str, Any]] = {}
    targets_by_ref: dict[tuple[str, int, str], dict[str, dict[str, Any]]] = {}
    graph_runtime: dict[tuple[str, int, str], dict[str, dict[str, Any]]] = {}
    for graph in records:
        subject = _subject(graph)
        graph_key = _exact_key(graph, "graph_id")
        node_ids = [item["node_id"] for item in graph["nodes"]]
        if len(node_ids) != len(set(node_ids)):
            _diagnostic(diagnostics, "DUPLICATE_LOCAL_ID", subject, "$.nodes", "node IDs must be unique")
        node_contracts: dict[str, dict[str, Any]] = {}
        for index, node in enumerate(graph["nodes"]):
            contract_key = _reference_key(node["contract_reference"], "component_contract_id")
            contract = contracts_by_ref.get(contract_key)
            if contract is None:
                _diagnostic(
                    diagnostics,
                    "CONTRACT_REFERENCE_UNRESOLVED",
                    subject,
                    f"$.nodes[{index}].contract_reference",
                    "the exact component-contract tuple did not resolve",
                )
                continue
            node_contracts[node["node_id"]] = contract
            facets = _facet_maps(contract)
            for collection, facet_kind in (("parameter_values", "parameter"), ("attribute_values", "attribute")):
                values = node[collection]
                value_ids = [item["facet_id"] for item in values]
                if len(value_ids) != len(set(value_ids)):
                    _diagnostic(
                        diagnostics,
                        "DUPLICATE_LOCAL_ID",
                        subject,
                        f"$.nodes[{index}].{collection}",
                        "node facet values must be unique",
                    )
                for value in values:
                    if value["facet_id"] not in facets[facet_kind]:
                        _diagnostic(
                            diagnostics,
                            "GRAPH_FACET_UNKNOWN",
                            subject,
                            f"$.nodes[{index}].{collection}",
                            f"{value['facet_id']!r} is not a contract {facet_kind}",
                        )

        graph_facets: dict[str, tuple[str, dict[str, Any]]] = {}
        for collection, kind in (
            ("public_ports", "port"),
            ("public_parameters", "parameter"),
            ("public_actions", "action"),
            ("public_displays", "display"),
        ):
            for item in graph[collection]:
                facet_id = item["facet_id"]
                if facet_id in graph_facets:
                    _diagnostic(
                        diagnostics,
                        "DUPLICATE_LOCAL_ID",
                        subject,
                        f"$.{collection}",
                        f"graph facet ID {facet_id!r} is reused",
                    )
                graph_facets[facet_id] = (kind, item)
        semantic_keys = [item[1]["semantic_key"] for item in graph_facets.values()]
        if len(semantic_keys) != len(set(semantic_keys)):
            _diagnostic(
                diagnostics,
                "DUPLICATE_SEMANTIC_KEY",
                subject,
                "$",
                "public graph semantic keys must be unique",
            )

        driver_counts: Counter[tuple[str, str]] = Counter()
        signal_edges: dict[str, set[str]] = defaultdict(set)
        connection_ids: set[str] = set()
        for index, connection in enumerate(graph["connections"]):
            if connection["connection_id"] in connection_ids:
                _diagnostic(
                    diagnostics,
                    "DUPLICATE_LOCAL_ID",
                    subject,
                    "$.connections",
                    "connection IDs must be unique",
                )
            connection_ids.add(connection["connection_id"])
            source = connection["source"]
            destination = connection["destination"]
            source_port = _resolve_node_facet(
                node_contracts, source["node_id"], "port", source["facet_id"]
            )
            destination_port = _resolve_node_facet(
                node_contracts,
                destination["node_id"],
                "port",
                destination["facet_id"],
            )
            if source_port is None or destination_port is None:
                _diagnostic(
                    diagnostics,
                    "GRAPH_ENDPOINT_UNKNOWN",
                    subject,
                    f"$.connections[{index}]",
                    "connection endpoint did not resolve to a node port",
                )
                continue
            if source_port["direction"] != "outlet" or destination_port["direction"] != "inlet":
                _diagnostic(
                    diagnostics,
                    "GRAPH_CONNECTION_DIRECTION_INVALID",
                    subject,
                    f"$.connections[{index}]",
                    "direct connections must run from outlet to inlet",
                )
            mismatches = _port_type_mismatches(source_port, destination_port)
            if mismatches:
                _diagnostic(
                    diagnostics,
                    "GRAPH_CONNECTION_TYPE_INCOMPATIBLE",
                    subject,
                    f"$.connections[{index}]",
                    f"implicit conversion is prohibited; mismatched dimensions: {','.join(mismatches)}",
                )
            destination_key = (destination["node_id"], destination["facet_id"])
            driver_counts[destination_key] += 1
            if source["node_id"] == destination["node_id"]:
                _diagnostic(
                    diagnostics,
                    "GRAPH_DIRECT_SELF_CONNECTION",
                    subject,
                    f"$.connections[{index}]",
                    "v0 does not admit a direct self-connection without an explicit state/delay contract",
                )
            signal_edges[source["node_id"]].add(destination["node_id"])
        if _cycle_nodes(signal_edges):
            _diagnostic(
                diagnostics,
                "GRAPH_SIGNAL_CYCLE_UNSUPPORTED",
                subject,
                "$.connections",
                "v0 requires an explicit later state/delay model before accepting signal-flow cycles",
            )

        public_ports = {item["facet_id"]: item for item in graph["public_ports"]}
        exposure_counts: Counter[str] = Counter()
        resolved_public_port_types: dict[str, dict[str, Any]] = {}
        exposure_ids: set[str] = set()
        for index, exposure in enumerate(graph["public_port_exposures"]):
            if exposure["exposure_id"] in exposure_ids:
                _diagnostic(diagnostics, "DUPLICATE_LOCAL_ID", subject, "$.public_port_exposures", "exposure IDs must be unique")
            exposure_ids.add(exposure["exposure_id"])
            public_port = public_ports.get(exposure["graph_facet_id"])
            endpoint = exposure["node_port"]
            node_port = _resolve_node_facet(
                node_contracts, endpoint["node_id"], "port", endpoint["facet_id"]
            )
            if public_port is None or node_port is None:
                _diagnostic(
                    diagnostics,
                    "GRAPH_EXPOSURE_UNRESOLVED",
                    subject,
                    f"$.public_port_exposures[{index}]",
                    "public port exposure did not resolve both endpoints",
                )
                continue
            expected_direction = "inlet" if public_port["direction"] == "input" else "outlet"
            if node_port["direction"] != expected_direction:
                _diagnostic(
                    diagnostics,
                    "GRAPH_EXPOSURE_DIRECTION_INVALID",
                    subject,
                    f"$.public_port_exposures[{index}]",
                    "public and internal port directions disagree",
                )
            exposure_counts[exposure["graph_facet_id"]] += 1
            resolved_public_port_types[exposure["graph_facet_id"]] = node_port
            if public_port["direction"] == "input":
                driver_counts[(endpoint["node_id"], endpoint["facet_id"])] += 1
        for facet_id in public_ports:
            if exposure_counts[facet_id] != 1:
                _diagnostic(
                    diagnostics,
                    "GRAPH_EXPOSURE_INCOMPLETE",
                    subject,
                    "$.public_port_exposures",
                    f"public port {facet_id!r} must have exactly one internal exposure",
                )

        public_parameters = {item["facet_id"]: item for item in graph["public_parameters"]}
        binding_counts: Counter[str] = Counter()
        binding_ids: set[str] = set()
        for index, binding in enumerate(graph["parameter_bindings"]):
            if binding["binding_id"] in binding_ids:
                _diagnostic(diagnostics, "DUPLICATE_LOCAL_ID", subject, "$.parameter_bindings", "parameter binding IDs must be unique")
            binding_ids.add(binding["binding_id"])
            parameter = public_parameters.get(binding["source_graph_parameter_id"])
            destination = binding["destination"]
            destination_facet = _resolve_node_facet(
                node_contracts,
                destination["node_id"],
                destination["facet_kind"],
                destination["facet_id"],
            )
            if parameter is None or destination_facet is None:
                _diagnostic(
                    diagnostics,
                    "GRAPH_PARAMETER_BINDING_UNRESOLVED",
                    subject,
                    f"$.parameter_bindings[{index}]",
                    "parameter binding source or destination did not resolve",
                )
                continue
            expected_kind = "port" if binding["binding_kind"] == "parameter-to-port" else "parameter"
            if destination["facet_kind"] != expected_kind:
                _diagnostic(
                    diagnostics,
                    "GRAPH_PARAMETER_BINDING_KIND_INVALID",
                    subject,
                    f"$.parameter_bindings[{index}].destination",
                    f"{binding['binding_kind']} must target a component {expected_kind}",
                )
            source_domain = parameter["domain"]
            if binding["source_domain"] != source_domain:
                _diagnostic(
                    diagnostics,
                    "GRAPH_PARAMETER_DOMAIN_MISMATCH",
                    subject,
                    f"$.parameter_bindings[{index}].source_domain",
                    "binding source domain redefines the public graph parameter",
                )
            if expected_kind == "port":
                contract = node_contracts[destination["node_id"]]
                if destination["facet_id"] not in contract["binding_capabilities"]["parameter_input_ports"]:
                    _diagnostic(
                        diagnostics,
                        "GRAPH_PARAMETER_BINDING_NOT_ALLOWED",
                        subject,
                        f"$.parameter_bindings[{index}].destination",
                        "component contract does not admit parameter binding to this port",
                    )
                if destination_facet["direction"] != "inlet" or destination_facet["port_type"]["rate"] != "control":
                    _diagnostic(
                        diagnostics,
                        "GRAPH_PARAMETER_BINDING_TYPE_INCOMPATIBLE",
                        subject,
                        f"$.parameter_bindings[{index}].destination",
                        "v0 parameter promotion may target only an explicitly allowed control-rate inlet",
                    )
                port_range = destination_facet["port_type"]["valid_range"]
                expected_destination_domain = {
                    **port_range,
                    "unit": destination_facet["port_type"]["unit"],
                }
            else:
                expected_destination_domain = {
                    **destination_facet["domain"],
                    "unit": destination_facet["unit"],
                }
            if binding["destination_domain"] != expected_destination_domain:
                _diagnostic(
                    diagnostics,
                    "GRAPH_PARAMETER_DOMAIN_MISMATCH",
                    subject,
                    f"$.parameter_bindings[{index}].destination_domain",
                    "binding destination domain disagrees with the exact component facet",
                )
            if not _validate_transform(
                binding["source_domain"], binding["destination_domain"], binding["transform"]
            ):
                _diagnostic(
                    diagnostics,
                    "GRAPH_PARAMETER_TRANSFORM_INVALID",
                    subject,
                    f"$.parameter_bindings[{index}].transform",
                    "ordered transform endpoints must cover both exact domains",
                )
            binding_counts[binding["source_graph_parameter_id"]] += 1
            if destination["facet_kind"] == "port":
                driver_counts[(destination["node_id"], destination["facet_id"])] += 1
        for facet_id in public_parameters:
            if binding_counts[facet_id] != 1:
                _diagnostic(
                    diagnostics,
                    "GRAPH_PARAMETER_BINDING_INCOMPLETE",
                    subject,
                    "$.parameter_bindings",
                    f"public graph parameter {facet_id!r} must have exactly one binding",
                )

        public_runtime = {
            "action": {item["facet_id"]: item for item in graph["public_actions"]},
            "display": {item["facet_id"]: item for item in graph["public_displays"]},
        }
        runtime_exposure_counts: Counter[tuple[str, str]] = Counter()
        for index, exposure in enumerate(graph["public_facet_exposures"]):
            if exposure["exposure_id"] in exposure_ids:
                _diagnostic(
                    diagnostics,
                    "DUPLICATE_LOCAL_ID",
                    subject,
                    "$.public_facet_exposures",
                    "exposure IDs must be unique across public exposure kinds",
                )
            exposure_ids.add(exposure["exposure_id"])
            graph_kind = exposure["graph_facet_kind"]
            public_facet = public_runtime[graph_kind].get(exposure["graph_facet_id"])
            target = exposure["target"]
            internal = _resolve_node_facet(
                node_contracts, target["node_id"], target["facet_kind"], target["facet_id"]
            )
            if public_facet is None or internal is None or target["facet_kind"] != graph_kind:
                _diagnostic(
                    diagnostics,
                    "GRAPH_EXPOSURE_UNRESOLVED",
                    subject,
                    f"$.public_facet_exposures[{index}]",
                    "public action/display exposure did not resolve a same-kind internal facet",
                )
            elif graph_kind == "action" and public_facet["payload_kind"] != internal["payload_kind"]:
                _diagnostic(diagnostics, "GRAPH_EXPOSURE_TYPE_INCOMPATIBLE", subject, f"$.public_facet_exposures[{index}]", "action payload kinds disagree")
            elif graph_kind == "display" and public_facet["value_kind"] != internal["value_kind"]:
                _diagnostic(diagnostics, "GRAPH_EXPOSURE_TYPE_INCOMPATIBLE", subject, f"$.public_facet_exposures[{index}]", "display value kinds disagree")
            runtime_exposure_counts[(graph_kind, exposure["graph_facet_id"])] += 1
        for kind, facets in public_runtime.items():
            for facet_id in facets:
                if runtime_exposure_counts[(kind, facet_id)] != 1:
                    _diagnostic(diagnostics, "GRAPH_EXPOSURE_INCOMPLETE", subject, "$.public_facet_exposures", f"public {kind} {facet_id!r} must have exactly one exposure")

        for node_id, contract in node_contracts.items():
            for port in contract["ports"]:
                if port["direction"] != "inlet":
                    continue
                key = (node_id, port["facet_id"])
                count = driver_counts[key]
                minimum = port["port_type"]["cardinality"]["minimum_connections"]
                maximum = port["port_type"]["cardinality"]["maximum_connections"]
                optional = port["port_type"]["optionality"]["status"] == "optional"
                if count < minimum and not optional:
                    _diagnostic(
                        diagnostics,
                        "GRAPH_REQUIRED_INLET_UNDRIVEN",
                        subject,
                        "$.nodes",
                        f"required inlet {node_id}:{port['facet_id']} has no driver",
                    )
                if isinstance(maximum, int) and count > maximum:
                    _diagnostic(
                        diagnostics,
                        "DUPLICATE_DRIVER",
                        subject,
                        "$.nodes",
                        f"inlet {node_id}:{port['facet_id']} exceeds its driver cardinality",
                    )

        hierarchy_edges: dict[str, set[str]] = defaultdict(set)
        for index, edge in enumerate(graph["hierarchy_edges"]):
            if edge["parent_node_id"] not in node_contracts or edge["child_node_id"] not in node_contracts:
                _diagnostic(diagnostics, "GRAPH_HIERARCHY_UNRESOLVED", subject, f"$.hierarchy_edges[{index}]", "hierarchy edge names an unknown node")
            hierarchy_edges[edge["parent_node_id"]].add(edge["child_node_id"])
        if _cycle_nodes(hierarchy_edges):
            _diagnostic(diagnostics, "GRAPH_HIERARCHY_CYCLE", subject, "$.hierarchy_edges", "graph hierarchy must be acyclic")

        compound_mappings: dict[str, dict[str, Any]] = {}
        for index, mapping in enumerate(graph["compound_interface_mappings"]):
            key = mapping["mapping_key"]
            if key in compound_mappings:
                _diagnostic(diagnostics, "COMPOUND_MAPPING_DUPLICATE", subject, "$.compound_interface_mappings", f"mapping key {key!r} is duplicated")
            target = mapping["target"]
            internal = _resolve_node_facet(
                node_contracts, target["node_id"], target["facet_kind"], target["facet_id"]
            )
            if internal is None:
                _diagnostic(diagnostics, "COMPOUND_MAPPING_UNRESOLVED", subject, f"$.compound_interface_mappings[{index}]", "compound mapping target did not resolve")
            compound_mappings[key] = mapping

        targets: dict[str, dict[str, Any]] = {}
        for facet_id, port in public_ports.items():
            target: dict[str, Any] = {
                "facet_kind": "port",
                "semantic_key": port["semantic_key"],
            }
            resolved_port = resolved_public_port_types.get(facet_id)
            if resolved_port is not None:
                domain = _project_port_domain(resolved_port)
                if domain is not None:
                    target["domain"] = domain
            targets[facet_id] = target
        for facet_id, parameter in public_parameters.items():
            targets[facet_id] = {
                "facet_kind": "parameter",
                "semantic_key": parameter["semantic_key"],
                "domain": _graph_range_to_instrument_domain(parameter["domain"]),
            }
        for kind, facets in public_runtime.items():
            for facet_id, item in facets.items():
                targets[facet_id] = {"facet_kind": kind, "semantic_key": item["semantic_key"]}

        graphs_by_ref[graph_key] = graph
        targets_by_ref[graph_key] = targets
        graph_runtime[graph_key] = {
            "node_contracts": node_contracts,
            "compound_mappings": compound_mappings,
        }
    return graphs_by_ref, targets_by_ref, graph_runtime


def _source_id(observation: dict[str, Any]) -> str | None:
    origin = observation["origin"]
    if origin["kind"] == "file":
        return origin["source_id"]
    if origin["kind"] == "provider":
        return origin["provider"]["source_id"]
    return None


def _source_sha256(observation: dict[str, Any]) -> str | None:
    origin = observation["origin"]
    return origin.get("sha256") if origin["kind"] == "file" else None


def _validate_bindings(
    records: list[dict[str, Any]],
    contracts_by_ref: dict[tuple[str, int, str], dict[str, Any]],
    graphs_by_ref: dict[tuple[str, int, str], dict[str, Any]],
    graph_runtime: dict[tuple[str, int, str], dict[str, dict[str, Any]]],
    overlay: dict[str, Any],
    manifest_sha256: str,
    observations: dict[str, dict[str, Any]],
    diagnostics: list[base.Diagnostic],
) -> None:
    overlay_implementations = {
        item["implementation_id"]: item for item in overlay["implementations"]
    }
    transparent_edges: dict[tuple[str, int, str], set[tuple[str, int, str]]] = defaultdict(set)
    transparent_subjects: dict[tuple[str, int, str], str] = {}
    for binding in records:
        subject = _subject(binding)
        contract_key = _reference_key(binding["contract_reference"], "component_contract_id")
        contract = contracts_by_ref.get(contract_key)
        if contract is None:
            _diagnostic(diagnostics, "CONTRACT_REFERENCE_UNRESOLVED", subject, "$.contract_reference", "the exact component-contract tuple did not resolve")
            continue
        expected_facets = _all_contract_facets(contract)
        mapped_facets: Counter[tuple[str, str]] = Counter()
        seam_keys: Counter[str] = Counter()
        mapping_ids: set[str] = set()
        for index, mapping in enumerate(binding["facet_mappings"]):
            if mapping["mapping_id"] in mapping_ids:
                _diagnostic(diagnostics, "DUPLICATE_LOCAL_ID", subject, "$.facet_mappings", "binding mapping IDs must be unique")
            mapping_ids.add(mapping["mapping_id"])
            facet = mapping["contract_facet"]
            facet_key = (facet["facet_kind"], facet["facet_id"])
            mapped_facets[facet_key] += 1
            seam_keys[base.canonical_json(mapping["implementation_seam"])] += 1
            if facet_key not in expected_facets:
                _diagnostic(diagnostics, "BINDING_FACET_UNKNOWN", subject, f"$.facet_mappings[{index}].contract_facet", "binding maps a facet absent from the exact contract")
        if set(mapped_facets) != expected_facets or any(count != 1 for count in mapped_facets.values()):
            _diagnostic(diagnostics, "BINDING_MAP_INCOMPLETE", subject, "$.facet_mappings", "every public contract facet must be mapped exactly once")
        if any(count != 1 for count in seam_keys.values()):
            _diagnostic(diagnostics, "BINDING_SEAM_DUPLICATE", subject, "$.facet_mappings", "one implementation seam cannot realize several public facets")

        realization = binding["realization"]
        if realization["form"] in {"generated-legacy-object", "legacy-native-object", "legacy-subpatch"}:
            overlay_entry = overlay_implementations.get(binding["implementation_id"])
            if overlay_entry is None:
                _diagnostic(diagnostics, "IMPLEMENTATION_MEMBERSHIP_UNRESOLVED", subject, "$.implementation_id", "legacy companion identity is absent from Phase 4A")
            elif overlay_entry["family_id"] != contract["family_reference"]["family_id"]:
                _diagnostic(diagnostics, "IMPLEMENTATION_FAMILY_MISMATCH", subject, "$.contract_reference", "contract family disagrees with Phase 4A implementation membership")
            expected_form = {
                "generated-object": "generated-legacy-object",
                "native-object": "legacy-native-object",
                "legacy-subpatch": "legacy-subpatch",
            }.get(overlay_entry["form"] if overlay_entry is not None else "")
            if expected_form != realization["form"]:
                _diagnostic(diagnostics, "IMPLEMENTATION_FORM_MISMATCH", subject, "$.realization.form", "binding realization form disagrees with Phase 4A")
            observation_ref = realization["observation"]["evidence_ref"]
            observation = observations.get(observation_ref)
            if observation is None:
                _diagnostic(diagnostics, "LEGACY_OBSERVATION_UNRESOLVED", subject, "$.realization.observation.evidence_ref", "frozen legacy observation did not resolve")
                continue
            locator = realization["observation"]
            if locator["manifest_sha256"] != manifest_sha256:
                _diagnostic(diagnostics, "LEGACY_OBSERVATION_HASH_MISMATCH", subject, "$.realization.observation.manifest_sha256", "binding cites the wrong frozen manifest")
            expected_locator = {
                "variant_index": observation["variant_index"],
                "legacy_uuid": observation["uuid"]["durable_value"],
                "source_id": _source_id(observation),
                "source_sha256": _source_sha256(observation),
            }
            for field, expected in expected_locator.items():
                if locator[field] != expected:
                    _diagnostic(diagnostics, "LEGACY_OBSERVATION_MISMATCH", subject, f"$.realization.observation.{field}", f"expected {expected!r}")
            if set(binding["evidence_refs"]) != {observation_ref}:
                _diagnostic(diagnostics, "BINDING_EVIDENCE_MISMATCH", subject, "$.evidence_refs", "legacy binding evidence must name exactly its frozen observation")

            collection_by_seam = {
                "legacy-inlet": "inlets",
                "legacy-outlet": "outlets",
                "legacy-parameter": "parameters",
                "legacy-attribute": "attributes",
                "legacy-display": "displays",
            }
            for index, mapping in enumerate(binding["facet_mappings"]):
                seam = mapping["implementation_seam"]
                collection_name = collection_by_seam.get(seam["seam_kind"])
                if collection_name is None:
                    _diagnostic(diagnostics, "BINDING_SEAM_KIND_INVALID", subject, f"$.facet_mappings[{index}].implementation_seam", "legacy realization requires a legacy seam")
                    continue
                candidates = observation["facets"].get(collection_name, [])
                observed = next((item for item in candidates if item["index"] == seam["index"]), None)
                if observed is None or any(
                    seam[field] != observed[field]
                    for field in ("name", "legacy_type", "data_type")
                ):
                    _diagnostic(diagnostics, "BINDING_SEAM_MISMATCH", subject, f"$.facet_mappings[{index}].implementation_seam", "seam locator disagrees with the frozen observation")
                    continue
                facet = mapping["contract_facet"]
                contract_facet = _facet_maps(contract)[facet["facet_kind"]].get(
                    facet["facet_id"]
                )
                if contract_facet is None:
                    # The total-map pass already emitted BINDING_FACET_UNKNOWN;
                    # keep validation fail-closed without dereferencing it.
                    continue
                if facet["facet_kind"] == "port":
                    expected_seam_kind = "legacy-inlet" if contract_facet["direction"] == "inlet" else "legacy-outlet"
                    expected_data_type = "axoloti.datatypes.Frac32buffer" if contract_facet["port_type"]["rate"] == "audio" else "axoloti.datatypes.Frac32"
                    representation = contract_facet["port_type"]["representation"]
                    if seam["seam_kind"] != expected_seam_kind or seam["data_type"] != expected_data_type:
                        _diagnostic(diagnostics, "BINDING_TYPE_INCOMPATIBLE", subject, f"$.facet_mappings[{index}]", "contract direction/rate disagrees with the observed legacy seam")
                    if representation != {"kind": "fixed-point", "signed": True, "width_bits": 32, "fractional_bits": 27, "encoding": "twos-complement-binary"}:
                        _diagnostic(diagnostics, "BINDING_TYPE_INCOMPATIBLE", subject, f"$.facet_mappings[{index}]", "Frac32 seam requires the curated signed 32-bit Q27 representation")
                    if contract_facet["semantic_key"] == "fade" and "Pos" not in seam["legacy_type"]:
                        _diagnostic(diagnostics, "BINDING_TYPE_INCOMPATIBLE", subject, f"$.facet_mappings[{index}]", "normalized fade mapping requires the positive legacy inlet seam")
        elif realization["form"] == "transparent-compound":
            graph_key = _reference_key(realization["graph_reference"], "graph_id")
            graph = graphs_by_ref.get(graph_key)
            runtime = graph_runtime.get(graph_key)
            if graph is None or runtime is None:
                _diagnostic(diagnostics, "TRANSPARENT_GRAPH_UNRESOLVED", subject, "$.realization.graph_reference", "transparent compound graph did not resolve exactly")
                continue
            if contract["compound_interface"]["kind"] != "transparent-compound":
                _diagnostic(diagnostics, "TRANSPARENT_CONTRACT_INVALID", subject, "$.contract_reference", "transparent realization requires a transparent-compound contract")
            expected_keys = {item["mapping_key"] for item in contract["compound_interface"]["mapping_keys"]}
            mapped_keys = {
                mapping["implementation_seam"]["mapping_key"]
                for mapping in binding["facet_mappings"]
                if mapping["implementation_seam"]["seam_kind"] == "graph-mapping-key"
            }
            graph_keys = set(runtime["compound_mappings"])
            if expected_keys != mapped_keys or expected_keys != graph_keys:
                _diagnostic(diagnostics, "COMPOUND_MAPPING_INCOMPLETE", subject, "$.facet_mappings", "contract, binding, and graph mapping-key sets must be total and equal")
            contract_key_for_edge = contract_key
            transparent_subjects[contract_key_for_edge] = subject
            for node_contract in runtime["node_contracts"].values():
                transparent_edges[contract_key_for_edge].add(_exact_key(node_contract, "component_contract_id"))

            compound_by_key = {
                item["mapping_key"]: item for item in contract["compound_interface"]["mapping_keys"]
            }
            for index, mapping in enumerate(binding["facet_mappings"]):
                seam = mapping["implementation_seam"]
                if seam["seam_kind"] != "graph-mapping-key":
                    _diagnostic(diagnostics, "BINDING_SEAM_KIND_INVALID", subject, f"$.facet_mappings[{index}]", "transparent realization requires graph mapping-key seams")
                    continue
                graph_mapping = runtime["compound_mappings"].get(seam["mapping_key"])
                contract_mapping = compound_by_key.get(seam["mapping_key"])
                if graph_mapping is None or contract_mapping is None:
                    continue
                outer = _facet_maps(contract)[contract_mapping["facet_kind"]].get(contract_mapping["facet_id"])
                target = graph_mapping["target"]
                inner = _resolve_node_facet(runtime["node_contracts"], target["node_id"], target["facet_kind"], target["facet_id"])
                if outer is None or inner is None or contract_mapping["facet_kind"] != target["facet_kind"]:
                    _diagnostic(diagnostics, "COMPOUND_MAPPING_TYPE_INCOMPATIBLE", subject, f"$.facet_mappings[{index}]", "compound mapping kinds or targets disagree")
                elif contract_mapping["facet_kind"] == "port" and (
                    outer["direction"] != inner["direction"]
                    or _port_type_mismatches(outer, inner)
                ):
                    _diagnostic(diagnostics, "COMPOUND_MAPPING_TYPE_INCOMPATIBLE", subject, f"$.facet_mappings[{index}]", "compound public and internal port types disagree")
                elif contract_mapping["facet_kind"] == "parameter" and any(
                    outer[field] != inner[field]
                    for field in ("representation", "unit", "domain", "update_behavior")
                ):
                    _diagnostic(diagnostics, "COMPOUND_MAPPING_TYPE_INCOMPATIBLE", subject, f"$.facet_mappings[{index}]", "compound public and internal parameter types disagree")
                elif contract_mapping["facet_kind"] == "action" and outer["payload_kind"] != inner["payload_kind"]:
                    _diagnostic(diagnostics, "COMPOUND_MAPPING_TYPE_INCOMPATIBLE", subject, f"$.facet_mappings[{index}]", "compound public and internal action payloads disagree")
                elif contract_mapping["facet_kind"] == "display" and (
                    outer["value_kind"] != inner["value_kind"]
                    or outer["access"] != inner["access"]
                ):
                    _diagnostic(diagnostics, "COMPOUND_MAPPING_TYPE_INCOMPATIBLE", subject, f"$.facet_mappings[{index}]", "compound public and internal display types disagree")
        else:
            if binding["implementation_id"] in overlay_implementations:
                _diagnostic(diagnostics, "IMPLEMENTATION_FORM_MISMATCH", subject, "$.realization.form", "new native/service realization cannot silently reuse a Phase 4A legacy implementation")

    recursion_nodes = _cycle_nodes(transparent_edges)
    for key in sorted(recursion_nodes):
        _diagnostic(diagnostics, "COMPOUND_RECURSION", transparent_subjects.get(key, str(key)), "$.realization.graph_reference", "transparent compound expansion is directly or indirectly recursive")


def validate_component_graph_values(
    family_records: list[dict[str, Any]],
    contract_records: list[dict[str, Any]],
    binding_records: list[dict[str, Any]],
    graph_records: list[dict[str, Any]],
    schemas: dict[str, dict[str, Any]],
    overlay: dict[str, Any],
    overlay_sha256: str,
    manifest_sha256: str,
    observations: dict[str, dict[str, Any]],
) -> CoreValidation:
    diagnostics: list[base.Diagnostic] = []
    valid_families = _validate_structural_records(family_records, schemas["family"], FAMILY_SCHEMA_NAME, FAMILY_SCHEMA_VERSION, "family_id", diagnostics)
    valid_contracts = _validate_structural_records(contract_records, schemas["contract"], CONTRACT_SCHEMA_NAME, CONTRACT_SCHEMA_VERSION, "component_contract_id", diagnostics)
    valid_bindings = _validate_structural_records(binding_records, schemas["binding"], BINDING_SCHEMA_NAME, BINDING_SCHEMA_VERSION, "implementation_id", diagnostics)
    valid_graphs = _validate_structural_records(graph_records, schemas["graph"], GRAPH_SCHEMA_NAME, GRAPH_SCHEMA_VERSION, "graph_id", diagnostics)

    families_by_ref = _validate_family_companions(valid_families, overlay, overlay_sha256, manifest_sha256, diagnostics)
    contracts_by_ref = _validate_contracts(valid_contracts, families_by_ref, diagnostics)
    graphs_by_ref, graph_targets, graph_runtime = _validate_graphs(valid_graphs, contracts_by_ref, diagnostics)
    _validate_bindings(valid_bindings, contracts_by_ref, graphs_by_ref, graph_runtime, overlay, manifest_sha256, observations, diagnostics)

    diagnostics = sorted(set(diagnostics), key=lambda item: (item.severity, item.code, item.subject, item.location, item.message))
    status = "invalid" if diagnostics else "valid"
    summary = {
        "schema_version": "component-graph-validation-summary-v0",
        "status": status,
        "record_counts": {
            "catalog_family_companions": len(family_records),
            "component_contracts": len(contract_records),
            "implementation_bindings": len(binding_records),
            "dsp_graphs": len(graph_records),
        },
        "reference_resolution": {
            "catalog_families": len(families_by_ref),
            "component_contracts": len(contracts_by_ref),
            "implementation_bindings": len(valid_bindings),
            "dsp_graphs": len(graphs_by_ref),
        },
        "diagnostics": [item.as_dict() for item in diagnostics],
    }
    return CoreValidation(summary, graph_targets, tuple(diagnostics))


def _schemas(schema_root: Path) -> dict[str, dict[str, Any]]:
    return {
        "family": base.load_json(schema_root / FAMILY_SCHEMA_NAME),
        "contract": base.load_json(schema_root / CONTRACT_SCHEMA_NAME),
        "binding": base.load_json(schema_root / BINDING_SCHEMA_NAME),
        "graph": base.load_json(schema_root / GRAPH_SCHEMA_NAME),
    }


def _observations(snapshot_root: Path) -> dict[str, dict[str, Any]]:
    return {
        f"legacy-resolved-catalog-v0:object:{record['variant_index']}": record
        for record in load_jsonl(snapshot_root / "resolved/objects.jsonl")
    }


def validate_component_graph_directory(
    contract_root: Path,
    schema_root: Path,
    repository_root: Path,
) -> CoreValidation:
    overlay_path = repository_root / OVERLAY_RELATIVE_PATH
    snapshot_root = repository_root / SNAPSHOT_RELATIVE_PATH
    manifest_path = snapshot_root / "manifest.json"
    overlay = base.load_json(overlay_path)
    return validate_component_graph_values(
        [base.load_json(path) for path in _record_files(contract_root, "catalog-families")],
        [base.load_json(path) for path in _record_files(contract_root, "component-contracts")],
        [base.load_json(path) for path in _record_files(contract_root, "implementation-bindings")],
        [base.load_json(path) for path in _record_files(contract_root, "graphs")],
        _schemas(schema_root),
        overlay,
        sha256_file(overlay_path),
        sha256_file(manifest_path),
        _observations(snapshot_root),
    )


def get_validated_graph_target_registry(
    contract_root: Path,
    schema_root: Path,
    repository_root: Path | None = None,
) -> dict[tuple[str, int, str], dict[str, dict[str, Any]]]:
    repository_root = repository_root or Path(__file__).resolve().parents[2]
    result = validate_component_graph_directory(contract_root, schema_root, repository_root)
    if result.summary["status"] != "valid":
        codes = sorted({item.code for item in result.diagnostics})
        raise ValueError(f"Task 006 graph registry is invalid: {codes}")
    return result.graph_targets

