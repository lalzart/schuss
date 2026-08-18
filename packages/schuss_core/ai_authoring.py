"""Sonic-first project-local object authoring over shared Schuss contracts."""

from __future__ import annotations

import copy
import hashlib
import re
import time
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable, Iterable

from .control_plane import OperationContext
from .native_kernel import NativeKernelError, evaluate_program, validate_program
from .project_service import (
    ObjectChangeProposal,
    ProjectError,
    ProjectService,
    ProjectTransactionRejected,
    _project_reference,
    _schema_value_bytes,
)
from .control_plane import core


DRAFT_TTL_SECONDS = 3600.0


class AuthoringError(ValueError):
    """Stable process-local authoring failure surfaced by operation dispatch."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        status: str = "invalid",
        location: str = "$.payload",
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status = status
        self.location = location


@dataclass
class _Draft:
    draft_id: str
    project_reference: dict[str, Any]
    specification: dict[str, Any]
    object_definition: dict[str, Any]
    validation: dict[str, Any]
    created_at: float
    evaluation: dict[str, Any] | None = None


@dataclass
class _Preview:
    preview_id: str
    draft_id: str
    project_reference: dict[str, Any]
    confirmation_fingerprint: str
    proposal: ObjectChangeProposal
    created_at: float
    consumed: bool = False


def _tokens(values: Iterable[str]) -> set[str]:
    return {
        token
        for value in values
        for token in re.findall(r"[a-z0-9]+", value.lower())
        if len(token) > 1
    }


def plan_sonic_intent(
    payload: dict[str, Any],
    context: OperationContext,
    project_objects: Iterable[dict[str, Any]] = (),
) -> dict[str, Any]:
    """Return validity-gated catalog matches and unsuppressed creation lanes."""

    intent = payload["intent"]
    maximum = payload["maximum_existing_candidates"]
    query_tokens = _tokens(
        [
            intent["objective"],
            intent["function"],
            *intent["required_capabilities"],
            *intent["desired_character"],
        ]
    )
    ranked: list[tuple[int, str, str, dict[str, Any]]] = []
    for family in (context.catalog_projection or {}).get("families", []):
        if not family["contract_facets_available"]:
            continue
        contract_references = sorted(
            {
                core.canonical_json(reference): copy.deepcopy(reference)
                for implementation in family["implementations"]
                for reference in implementation["contract_references"]
            }.values(),
            key=core.canonical_json,
        )
        if not contract_references:
            continue
        candidate_tokens = _tokens(
            [
                family["display_name"],
                *family["aliases"],
                family["description"],
                family["primary_function"],
                *family["technique_tags"],
                *family["capability_keys"],
            ]
        )
        matched = sorted(query_tokens & candidate_tokens)
        function_exact = family["primary_function"] == intent["function"]
        capability_match = sorted(
            set(intent["required_capabilities"]) & set(family["capability_keys"])
        )
        score = len(matched) + 3 * function_exact + 2 * len(capability_match)
        summary = {
            "origin": "catalog",
            "family_reference": copy.deepcopy(family["family_reference"]),
            "display_name": family["display_name"],
            "primary_function": family["primary_function"],
            "contract_references": contract_references,
            "readiness_states": copy.deepcopy(family["readiness_states"]),
            "catalog_match": {
                "matched_terms": matched,
                "required_capability_matches": capability_match,
                "primary_function_exact": function_exact,
                "match_count": score,
            },
            "validity_gate": "passed-exact-component-contract",
            "sonic_fidelity": "not-evaluated",
            "sonic_interest": "not-evaluated",
            "sonic_quality": "not-evaluated",
            "unresolved_facts": copy.deepcopy(family["unresolved_facts"]),
        }
        ranked.append(
            (
                -score,
                family["display_name"].lower(),
                family["family_reference"]["family_id"],
                summary,
            )
        )
    for definition in project_objects:
        family = definition["family"]
        contract = definition["component_contract"]
        candidate_tokens = _tokens(
            [
                family["display_name"],
                *family["aliases"],
                family["function"],
                *family["desired_character"],
            ]
        )
        matched = sorted(query_tokens & candidate_tokens)
        function_exact = family["function"] == intent["function"]
        score = len(matched) + 3 * function_exact
        summary = {
            "origin": "project-local",
            "object_reference": _exact_reference(
                definition, "object_definition_id"
            ),
            "family_reference": _exact_reference(family, "family_id"),
            "display_name": family["display_name"],
            "primary_function": family["function"],
            "contract_references": [
                _exact_reference(contract, "component_contract_id")
            ],
            "project_evidence": copy.deepcopy(definition["evidence"]),
            "catalog_match": {
                "matched_terms": matched,
                "required_capability_matches": [],
                "primary_function_exact": function_exact,
                "match_count": score,
            },
            "validity_gate": "passed-exact-project-object-closure",
            "sonic_fidelity": "not-evaluated",
            "sonic_interest": "not-evaluated",
            "sonic_quality": "not-evaluated",
            "unresolved_facts": [
                "global-catalog-readiness-not-applicable",
                "target-lowering-not-established",
            ],
        }
        ranked.append(
            (
                -score,
                family["display_name"].lower(),
                definition["object_definition_id"],
                summary,
            )
        )
    candidates = [item[3] for item in sorted(ranked)[:maximum]]
    return {
        "intent": copy.deepcopy(intent),
        "optimization_policy": {
            "validity": "hard-gate",
            "objectives": ["sonic-accuracy", "sonic-interest", "sonic-quality"],
            "cost_objective": "absent",
            "existing-object-shortcut": "prohibited",
            "subjective_evidence": "not-evaluated",
        },
        "lanes": [
            {
                "lane": "existing-object",
                "status": "available",
                "candidates": candidates,
            },
            {
                "lane": "transparent-compound",
                "status": "available-with-explicit-project",
                "candidates": [],
            },
            {
                "lane": "native-kernel",
                "status": "available-with-explicit-project",
                "candidates": [],
            },
        ],
        "selection_boundary": (
            "catalog matches are factual retrieval aids, not claims of sonic fitness; "
            "compound and native creation remain available regardless of matches"
        ),
    }


def _exact_reference(record: dict[str, Any], id_field: str) -> dict[str, Any]:
    return {
        id_field: record[id_field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def _finish_record(record: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(record)
    value["content_hash"] = core.record_content_hash(value, schema)
    errors = core.schema_errors(value, schema, schema)
    if errors:
        raise AuthoringError(
            "AUTHORING_GENERATED_RECORD_INVALID",
            "; ".join(errors),
        )
    return core.canonicalize_with_schema(value, schema, schema)


def _family_schema(object_schema: dict[str, Any]) -> dict[str, Any]:
    schema = copy.deepcopy(object_schema["properties"]["family"])
    schema["$defs"] = copy.deepcopy(object_schema.get("$defs", {}))
    return schema


def _numeric_representation(unit: str) -> dict[str, Any]:
    if unit == "boolean":
        return {
            "kind": "boolean",
            "width_bits": 32,
            "encoding": "zero-false-nonzero-true",
        }
    if unit in {"hertz", "midi-note", "unitless"}:
        # The bounded host kernel has no target-lowering claim. A float seam is
        # therefore more truthful than inventing a fixed-point range that
        # cannot represent ordinary frequency or unbounded unitless values.
        return {"kind": "float", "width_bits": 32, "encoding": "ieee-754"}
    return {
        "kind": "fixed-point",
        "signed": True,
        "width_bits": 32,
        "fractional_bits": 21 if unit == "semitone-offset" else 27,
        "encoding": "twos-complement-binary",
    }


def _unit_range(unit: str, semantic_role: str) -> tuple[str, str]:
    if unit == "boolean":
        return "0", "1"
    if unit == "hertz":
        return "0", "24000"
    if unit == "midi-note":
        return "0", "127"
    if unit == "semitone-offset":
        return "-64", "63.999999523162841796875"
    if unit == "normalized" and semantic_role != "audio":
        return "0", "1"
    return "-1", "1"


def _native_port(source: dict[str, Any], index: int) -> dict[str, Any]:
    minimum, maximum = _unit_range(source["unit"], source["semantic_role"])
    event = source["rate"] == "event"
    inlet = source["direction"] == "inlet"
    if event:
        representation = {
            "kind": "boolean",
            "width_bits": 32,
            "encoding": "zero-false-nonzero-true",
        }
    else:
        representation = _numeric_representation(source["unit"])
    optionality = (
        {
            "status": "optional",
            "absence_behavior": "no-event" if event else "use-default",
            "default_value": "0",
        }
        if inlet
        else {"status": "not-applicable"}
    )
    return {
        "facet_id": f"component-port-{index:06d}",
        "semantic_key": source["key"],
        "display_label": source["display_label"],
        "direction": source["direction"],
        "port_type": {
            "domain": "event" if event else "stream",
            "rate": source["rate"],
            "channel_shape": {"kind": "fixed", "count": 1},
            "cardinality": {
                "minimum_connections": 0,
                "maximum_connections": 1 if inlet else "unbounded",
            },
            "semantic_role": source["semantic_role"],
            "representation": representation,
            "unit": source["unit"],
            "valid_range": {
                "status": "known",
                "minimum": minimum,
                "maximum": maximum,
                "minimum_inclusive": True,
                "maximum_inclusive": True,
                "overflow_policy": "reject",
            },
            "optionality": optionality,
            "ownership": {
                "status": "defined",
                "owner": "scheduler",
                "mutability": "immutable-to-consumer",
                "borrowing": "borrowed",
                "lifetime": "event-delivery"
                if event
                else "audio-block"
                if source["rate"] == "audio"
                else "control-cycle",
                "capacity": "rate-defined"
                if source["rate"] == "audio"
                else "single-value",
                "synchronization": "single-scheduler",
                "aliasing": "read-only-aliases-allowed",
            },
        },
    }


def _native_parameter(source: dict[str, Any], index: int) -> dict[str, Any]:
    minimum = Decimal(source["minimum"])
    maximum = Decimal(source["maximum"])
    default = Decimal(source["default"])
    if minimum > maximum or default < minimum or default > maximum:
        raise AuthoringError(
            "AUTHORING_PARAMETER_RANGE_INVALID",
            f"parameter {source['key']!r} default must be inside its ordered range",
            location="$.payload.interface.parameters",
        )
    return {
        "facet_id": f"component-parameter-{index:06d}",
        "semantic_key": source["key"],
        "display_label": source["display_label"],
        "representation": _numeric_representation(source["unit"]),
        "unit": source["unit"],
        "domain": {
            "status": "known",
            "minimum": source["minimum"],
            "maximum": source["maximum"],
            "minimum_inclusive": True,
            "maximum_inclusive": True,
            "overflow_policy": "reject",
        },
        "default": source["default"],
        "update_behavior": {"update_kind": "runtime", "stateful": True},
    }


class SonicAuthoringService:
    """Process-local drafts and exact project-object preview/accept lifecycle."""

    def __init__(
        self,
        project_service: ProjectService,
        *,
        clock: Callable[[], float] = time.monotonic,
        draft_ttl_seconds: float = DRAFT_TTL_SECONDS,
    ) -> None:
        if draft_ttl_seconds <= 0:
            raise ValueError("authoring draft TTL must be positive")
        self.project_service = project_service
        self.clock = clock
        self.draft_ttl_seconds = draft_ttl_seconds
        self._drafts: dict[str, _Draft] = {}
        self._previews: dict[str, _Preview] = {}
        self._draft_counter = 0
        self._preview_counter = 0

    def _candidate_draft_id(self) -> str:
        return f"authoring-draft-{self._draft_counter + 1:06d}"

    def _next_preview_id(self) -> str:
        self._preview_counter += 1
        return f"authoring-preview-{self._preview_counter:06d}"

    def _draft(self, draft_id: str) -> _Draft:
        draft = self._drafts.get(draft_id)
        if draft is None:
            raise AuthoringError(
                "AUTHORING_DRAFT_UNKNOWN",
                "authoring draft handle is absent from this process",
                status="unresolved",
            )
        if self.clock() - draft.created_at > self.draft_ttl_seconds:
            del self._drafts[draft_id]
            raise AuthoringError(
                "AUTHORING_DRAFT_EXPIRED",
                "authoring draft handle has expired",
                status="unresolved",
            )
        return draft

    @staticmethod
    def _assert_project(
        expected: dict[str, Any], loaded_reference: dict[str, Any]
    ) -> None:
        if expected != loaded_reference:
            raise AuthoringError(
                "AUTHORING_PROJECT_STALE",
                "authoring request expected a different accepted project revision",
                status="conflict",
                location="$.payload.expected_project_reference",
            )

    @staticmethod
    def _allocate_id(
        project_id: str,
        draft_id: str,
        kind: str,
        prefix: str,
        occupied: set[str],
    ) -> str:
        seed = hashlib.sha256(
            f"ai-sonic-authoring-v1:{project_id}:{draft_id}:{kind}".encode("utf-8")
        ).digest()
        candidate = int.from_bytes(seed[:8], "big") % 999999 + 1
        for _ in range(999999):
            value = f"{prefix}-{candidate:06d}"
            if value not in occupied:
                return value
            candidate = candidate % 999999 + 1
        raise AuthoringError(
            "AUTHORING_ID_ALLOCATION_EXHAUSTED",
            f"no project-local {kind} identity remains available",
        )

    def _occupied_ids(self, loaded: Any) -> dict[str, set[str]]:
        context = loaded.context
        families = {item["family_id"] for item in context.records["families"]}
        if context.catalog_projection is not None:
            families.update(
                item["family_reference"]["family_id"]
                for item in context.catalog_projection["families"]
            )
        definitions = loaded.project_records.get("object-definition", ())
        return {
            "object": {item["object_definition_id"] for item in definitions},
            "family": families
            | {item["family"]["family_id"] for item in definitions},
            "contract": {item["component_contract_id"] for item in context.records["contracts"]},
            "binding": {item["implementation_id"] for item in context.records["bindings"]},
            "graph": {item["graph_id"] for item in context.records["graphs"]},
            "kernel": {
                item["realization"]["kernel"]["native_kernel_id"]
                for item in definitions
                if item["realization"]["form"] == "native-kernel"
            },
        }

    @staticmethod
    def _contract_registry(context: OperationContext) -> dict[tuple[str, int, str], dict[str, Any]]:
        return {
            core.exact_key(item, "component_contract_id"): item
            for item in context.records["contracts"]
        }

    @staticmethod
    def _facet(contract: dict[str, Any], kind: str, facet_id: str) -> dict[str, Any]:
        collection = "ports" if kind == "port" else "parameters"
        matches = [item for item in contract[collection] if item["facet_id"] == facet_id]
        if len(matches) != 1:
            raise AuthoringError(
                "AUTHORING_COMPOUND_FACET_UNRESOLVED",
                f"compound mapping target {facet_id!r} is not one exact {kind}",
                location="$.payload.realization.mappings",
            )
        return matches[0]

    def _compound_records(
        self,
        specification: dict[str, Any],
        identifiers: dict[str, str],
        family_reference: dict[str, Any],
        context: OperationContext,
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
        interface = specification["interface"]
        realization = specification["realization"]
        registry = self._contract_registry(context)
        node_ids = {
            item["node_key"]: f"graph-node-{index:06d}"
            for index, item in enumerate(realization["nodes"], 1)
        }
        if len(node_ids) != len(realization["nodes"]):
            raise AuthoringError(
                "AUTHORING_COMPOUND_NODE_DUPLICATE",
                "compound node keys must be unique",
                location="$.payload.realization.nodes",
            )
        node_contracts: dict[str, dict[str, Any]] = {}
        nodes: list[dict[str, Any]] = []
        for item in realization["nodes"]:
            reference = item["contract_reference"]
            contract = registry.get(core.reference_key(reference, "component_contract_id"))
            if contract is None:
                raise AuthoringError(
                    "AUTHORING_COMPOUND_CONTRACT_UNRESOLVED",
                    "compound node contract is absent from the exact project closure",
                    location="$.payload.realization.nodes",
                )
            node_contracts[item["node_key"]] = contract
            nodes.append(
                {
                    "node_id": node_ids[item["node_key"]],
                    "contract_reference": copy.deepcopy(reference),
                    "parameter_values": copy.deepcopy(item["parameter_values"]),
                    "attribute_values": copy.deepcopy(item["attribute_values"]),
                }
            )

        interface_items = [
            *(('port', item) for item in interface["ports"]),
            *(('parameter', item) for item in interface["parameters"]),
        ]
        by_public = {
            (item["public_kind"], item["public_key"]): item
            for item in realization["mappings"]
        }
        if len(by_public) != len(realization["mappings"]):
            raise AuthoringError(
                "AUTHORING_COMPOUND_MAPPING_DUPLICATE",
                "compound public mappings must be unique",
                location="$.payload.realization.mappings",
            )
        if set(by_public) != {(kind, item["key"]) for kind, item in interface_items}:
            raise AuthoringError(
                "AUTHORING_COMPOUND_MAPPING_INCOMPLETE",
                "every public port and parameter must be mapped exactly once",
                location="$.payload.realization.mappings",
            )

        ports: list[dict[str, Any]] = []
        parameters: list[dict[str, Any]] = []
        mapping_keys: list[dict[str, Any]] = []
        graph_mappings: list[dict[str, Any]] = []
        binding_mappings: list[dict[str, Any]] = []
        for ordinal, (kind, public) in enumerate(interface_items, 1):
            mapping = by_public[(kind, public["key"])]
            target = mapping["target"]
            contract = node_contracts.get(target["node_key"])
            if contract is None:
                raise AuthoringError(
                    "AUTHORING_COMPOUND_MAPPING_TARGET_UNRESOLVED",
                    "compound mapping names an absent node key",
                    location="$.payload.realization.mappings",
                )
            facet = copy.deepcopy(self._facet(contract, kind, target["facet_id"]))
            facet_id = f"component-{kind}-{len(ports) + 1:06d}" if kind == "port" else f"component-parameter-{len(parameters) + 1:06d}"
            if kind == "port":
                if any(
                    (
                        public["direction"] != facet["direction"],
                        public["rate"] != facet["port_type"]["rate"],
                        public["semantic_role"] != facet["port_type"]["semantic_role"],
                        public["unit"] != facet["port_type"]["unit"],
                    )
                ):
                    raise AuthoringError(
                        "AUTHORING_COMPOUND_INTERFACE_MISMATCH",
                        f"public port {public['key']!r} disagrees with its exact mapped facet",
                        location="$.payload.interface.ports",
                    )
                facet["facet_id"] = facet_id
                facet["semantic_key"] = public["key"]
                facet["display_label"] = public["display_label"]
                ports.append(facet)
            else:
                domain = facet["domain"]
                if (
                    public["unit"] != facet["unit"]
                    or domain.get("status") != "known"
                    or public["minimum"] != domain["minimum"]
                    or public["maximum"] != domain["maximum"]
                    or public["default"] != facet["default"]
                ):
                    raise AuthoringError(
                        "AUTHORING_COMPOUND_INTERFACE_MISMATCH",
                        f"public parameter {public['key']!r} disagrees with its exact mapped facet",
                        location="$.payload.interface.parameters",
                    )
                facet["facet_id"] = facet_id
                facet["semantic_key"] = public["key"]
                facet["display_label"] = public["display_label"]
                parameters.append(facet)
            mapping_key = f"compound-mapping-key-{ordinal:06d}"
            mapping_keys.append(
                {"mapping_key": mapping_key, "facet_kind": kind, "facet_id": facet_id}
            )
            graph_mappings.append(
                {
                    "mapping_key": mapping_key,
                    "target": {
                        "node_id": node_ids[target["node_key"]],
                        "facet_kind": kind,
                        "facet_id": target["facet_id"],
                    },
                }
            )
            binding_mappings.append(
                {
                    "mapping_id": f"binding-map-{ordinal:06d}",
                    "contract_facet": {"facet_kind": kind, "facet_id": facet_id},
                    "implementation_seam": {
                        "seam_kind": "graph-mapping-key",
                        "mapping_key": mapping_key,
                    },
                }
            )

        connections: list[dict[str, Any]] = []
        for index, item in enumerate(realization["connections"], 1):
            source_node = node_ids.get(item["source"]["node_key"])
            destination_node = node_ids.get(item["destination"]["node_key"])
            if source_node is None or destination_node is None:
                raise AuthoringError(
                    "AUTHORING_COMPOUND_CONNECTION_NODE_UNRESOLVED",
                    "compound connections must name two declared node keys",
                    location="$.payload.realization.connections",
                )
            connections.append(
                {
                    "connection_id": f"graph-connection-{index:06d}",
                    "source": {
                        "node_id": source_node,
                        "facet_id": item["source"]["facet_id"],
                    },
                    "destination": {
                        "node_id": destination_node,
                        "facet_id": item["destination"]["facet_id"],
                    },
                }
            )
        graph_schema = context.schemas["graph"]
        graph = _finish_record(
            {
                "schema_version": "dsp-graph-v0",
                "canonical_profile": "schuss-canonical-json-v1",
                "graph_id": identifiers["graph"],
                "revision": 1,
                "content_hash": "sha256:" + "0" * 64,
                "display_name": specification["display_name"] + " internals",
                "public_ports": [],
                "public_parameters": [],
                "public_actions": [],
                "public_displays": [],
                "nodes": nodes,
                "connections": connections,
                "public_port_exposures": [],
                "public_facet_exposures": [],
                "parameter_bindings": [],
                "compound_interface_mappings": graph_mappings,
                "hierarchy_edges": [],
            },
            graph_schema,
        )
        contract_schema = context.schemas["contract_versions"]["component-contract-v1"]
        contract = _finish_record(
            {
                "schema_version": "component-contract-v1",
                "canonical_profile": "schuss-canonical-json-v1",
                "component_contract_id": identifiers["contract"],
                "revision": 1,
                "content_hash": "sha256:" + "0" * 64,
                "family_reference": family_reference,
                "display_name": specification["display_name"],
                "ports": ports,
                "parameters": parameters,
                "attributes": [],
                "actions": [],
                "displays": [],
                "state_declarations": [
                    {
                        "state_id": "component-state-000001",
                        "semantic_key": "internal-component-state",
                        "value_kind": "structured",
                        "ownership": "component-instance",
                        "persistence": "volatile",
                        "reset_policy": "default-on-start",
                    }
                ],
                "lifecycle": {
                    "state_model": "declared-state",
                    "initialization": "initialize-declared-state",
                    "reset_behavior": "declared-per-state",
                    "disposal": "release-owned-state",
                },
                "binding_capabilities": {
                    "parameter_input_ports": [],
                    "action_inputs": [],
                },
                "capability_requirements": [],
                "compound_interface": {
                    "kind": "transparent-compound",
                    "mapping_keys": mapping_keys,
                },
                "compatibility_claims": [],
                "behavior_rules": [],
            },
            contract_schema,
        )
        binding_schema = context.schemas["binding_versions"]["implementation-binding-v3"]
        binding = _finish_record(
            {
                "schema_version": "implementation-binding-v3",
                "canonical_profile": "schuss-canonical-json-v1",
                "implementation_id": identifiers["binding"],
                "revision": 1,
                "content_hash": "sha256:" + "0" * 64,
                "contract_reference": _exact_reference(contract, "component_contract_id"),
                "realization": {
                    "form": "transparent-compound",
                    "graph_reference": _exact_reference(graph, "graph_id"),
                },
                "facet_mappings": binding_mappings,
                "observed_dependencies": [],
                "private_state": [
                    {"state_key": "internal-component-state", "value_kind": "structured"}
                ],
                "selection_state": {
                    "status": "not-evaluated",
                    "owner": "task-007",
                    "reason": "target-backend-contracts-not-yet-implemented",
                    "rationale": (
                        "The project-local transparent wrapper is structurally valid; "
                        "selection still depends on exact eligible internal bindings."
                    ),
                },
                "evidence_refs": ["fixture:project-local-object"],
            },
            binding_schema,
        )
        validation = {
            "status": "valid",
            "form": "transparent-compound",
            "internal_node_count": len(nodes),
            "connection_count": len(connections),
            "public_mapping_count": len(mapping_keys),
            "host_audition": "not-applicable",
            "target_eligibility": "depends-on-exact-internal-bindings",
        }
        return contract, binding, graph, validation

    def _native_records(
        self,
        specification: dict[str, Any],
        identifiers: dict[str, str],
        family_reference: dict[str, Any],
        context: OperationContext,
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
        interface = specification["interface"]
        realization = specification["realization"]
        program = {
            "input_keys": sorted(
                item["key"] for item in interface["ports"] if item["direction"] == "inlet"
            ),
            "parameter_keys": sorted(item["key"] for item in interface["parameters"]),
            "instructions": copy.deepcopy(realization["instructions"]),
            "outputs": copy.deepcopy(realization["outputs"]),
        }
        validation = validate_program(program, interface)
        kernel_schema = context.schemas["native_kernel"]
        kernel = _finish_record(
            {
                "schema_version": "native-kernel-v0",
                "canonical_profile": "schuss-canonical-json-v1",
                "native_kernel_id": identifiers["kernel"],
                "revision": 1,
                "content_hash": "sha256:" + "0" * 64,
                **program,
                "limits": {
                    "maximum_instructions": 128,
                    "maximum_state_slots": 128,
                    "arbitrary_code": "prohibited",
                },
            },
            kernel_schema,
        )
        ports = [
            _native_port(item, index)
            for index, item in enumerate(interface["ports"], 1)
        ]
        parameters = [
            _native_parameter(item, index)
            for index, item in enumerate(interface["parameters"], 1)
        ]
        contract_schema = context.schemas["contract_versions"]["component-contract-v1"]
        contract = _finish_record(
            {
                "schema_version": "component-contract-v1",
                "canonical_profile": "schuss-canonical-json-v1",
                "component_contract_id": identifiers["contract"],
                "revision": 1,
                "content_hash": "sha256:" + "0" * 64,
                "family_reference": family_reference,
                "display_name": specification["display_name"],
                "ports": ports,
                "parameters": parameters,
                "attributes": [],
                "actions": [],
                "displays": [],
                "state_declarations": [
                    {
                        "state_id": "component-state-000001",
                        "semantic_key": "kernel-state",
                        "value_kind": "structured",
                        "ownership": "component-instance",
                        "persistence": "volatile",
                        "reset_policy": "default-on-start",
                    }
                ],
                "lifecycle": {
                    "state_model": "declared-state",
                    "initialization": "initialize-declared-state",
                    "reset_behavior": "declared-per-state",
                    "disposal": "release-owned-state",
                },
                "binding_capabilities": {
                    "parameter_input_ports": [],
                    "action_inputs": [],
                },
                "capability_requirements": [],
                "compound_interface": {"kind": "primitive", "mapping_keys": []},
                "compatibility_claims": [],
                "behavior_rules": [],
            },
            contract_schema,
        )
        binding_mappings = []
        for ordinal, (kind, facet) in enumerate(
            [*(('port', item) for item in ports), *(('parameter', item) for item in parameters)],
            1,
        ):
            binding_mappings.append(
                {
                    "mapping_id": f"binding-map-{ordinal:06d}",
                    "contract_facet": {"facet_kind": kind, "facet_id": facet["facet_id"]},
                    "implementation_seam": {
                        "seam_kind": "native-symbol",
                        "symbol": f"schuss_project_kernel_{identifiers['kernel'].rsplit('-', 1)[1]}_{facet['facet_id'].replace('-', '_')}",
                    },
                }
            )
        binding_schema = context.schemas["binding_versions"]["implementation-binding-v3"]
        binding = _finish_record(
            {
                "schema_version": "implementation-binding-v3",
                "canonical_profile": "schuss-canonical-json-v1",
                "implementation_id": identifiers["binding"],
                "revision": 1,
                "content_hash": "sha256:" + "0" * 64,
                "contract_reference": _exact_reference(contract, "component_contract_id"),
                "realization": {
                    "form": "native-kernel",
                    "kernel_reference": _exact_reference(kernel, "native_kernel_id"),
                    "portable_symbol": f"schuss_project_kernel_{identifiers['kernel'].rsplit('-', 1)[1]}",
                },
                "facet_mappings": binding_mappings,
                "observed_dependencies": [],
                "private_state": [
                    {"state_key": "kernel-state", "value_kind": "structured"}
                ],
                "selection_state": {
                    "status": "not-evaluated",
                    "owner": "task-007",
                    "reason": "target-backend-contracts-not-yet-implemented",
                    "rationale": (
                        "The bounded host interpreter does not establish target lowering "
                        "or implementation eligibility."
                    ),
                },
                "evidence_refs": ["fixture:project-local-object"],
            },
            binding_schema,
        )
        return contract, binding, kernel, {
            **validation.as_dict(),
            "form": "native-kernel",
            "host_audition": "available",
            "target_eligibility": "absent",
        }

    def _build_definition(
        self,
        specification: dict[str, Any],
        draft_id: str,
        loaded: Any,
        *,
        host_evaluation: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        interface_keys = [
            item["key"]
            for item in (*specification["interface"]["ports"], *specification["interface"]["parameters"])
        ]
        if len(interface_keys) != len(set(interface_keys)):
            raise AuthoringError(
                "AUTHORING_INTERFACE_DUPLICATE",
                "public port and parameter keys must be unique",
                location="$.payload.interface",
            )
        occupied = self._occupied_ids(loaded)
        project_id = loaded.manifest["project_id"]
        identifiers = {
            "object": self._allocate_id(project_id, draft_id, "object", "schuss-project-object", occupied["object"]),
            "family": self._allocate_id(project_id, draft_id, "family", "schuss-family", occupied["family"]),
            "contract": self._allocate_id(project_id, draft_id, "contract", "schuss-component-contract", occupied["contract"]),
            "binding": self._allocate_id(project_id, draft_id, "binding", "schuss-implementation", occupied["binding"]),
        }
        if specification["realization"]["form"] == "transparent-compound":
            identifiers["graph"] = self._allocate_id(
                project_id, draft_id, "graph", "schuss-graph", occupied["graph"]
            )
        else:
            identifiers["kernel"] = self._allocate_id(
                project_id, draft_id, "kernel", "schuss-native-kernel", occupied["kernel"]
            )
        object_schema = loaded.context.schemas["project_object_definition"]
        family = _finish_record(
            {
                "family_id": identifiers["family"],
                "revision": 1,
                "content_hash": "sha256:" + "0" * 64,
                "display_name": specification["display_name"],
                "aliases": copy.deepcopy(specification["aliases"]),
                "function": specification["intent"]["function"],
                "desired_character": copy.deepcopy(
                    specification["intent"]["desired_character"]
                ),
                "provenance": specification["provenance"],
            },
            _family_schema(object_schema),
        )
        family_reference = _exact_reference(family, "family_id")
        if specification["realization"]["form"] == "transparent-compound":
            contract, binding, realization_record, validation = self._compound_records(
                specification, identifiers, family_reference, loaded.context
            )
            realization = {"form": "transparent-compound", "graph": realization_record}
            host_state = {"status": "not-applicable"}
        else:
            contract, binding, realization_record, validation = self._native_records(
                specification, identifiers, family_reference, loaded.context
            )
            realization = {"form": "native-kernel", "kernel": realization_record}
            host_state = copy.deepcopy(
                host_evaluation
                if host_evaluation is not None
                else {"status": "not-run"}
            )
        definition = _finish_record(
            {
                "schema_version": "project-object-definition-v0",
                "canonical_profile": "schuss-canonical-json-v1",
                "object_definition_id": identifiers["object"],
                "revision": 1,
                "content_hash": "sha256:" + "0" * 64,
                "family": family,
                "component_contract": contract,
                "implementation_binding": binding,
                "realization": realization,
                "intent": copy.deepcopy(specification["intent"]),
                "evidence": {
                    "structural": "passed",
                    "host_evaluation": host_state,
                    "target_lowering": "not-run",
                    "arm_build": "not-run",
                    "connected_device": "not-run",
                    "real_time_resources": "not-evaluated",
                    "audible_listening": "not-run",
                },
            },
            object_schema,
        )
        return definition, validation

    def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        loaded = self.project_service.load()
        loaded_reference = _project_reference(loaded.manifest)
        self._assert_project(payload["expected_project_reference"], loaded_reference)
        draft_id = self._candidate_draft_id()
        specification = {
            key: copy.deepcopy(payload[key])
            for key in (
                "display_name",
                "aliases",
                "intent",
                "interface",
                "realization",
                "provenance",
            )
        }
        try:
            definition, validation = self._build_definition(
                specification, draft_id, loaded
            )
            # Exercise the same complete project semantic closure used at accept,
            # but retain no proposed bytes from this validation-only pass.
            self.project_service.preview_object_change(definition, None)
        except NativeKernelError as exc:
            raise AuthoringError(exc.code, str(exc), location=exc.location) from exc
        except ProjectTransactionRejected as exc:
            diagnostic = exc.result["diagnostics"][0]
            raise AuthoringError(
                diagnostic["code"], diagnostic["message"], location=diagnostic["location"]
            ) from exc
        except ProjectError as exc:
            raise AuthoringError(exc.code, str(exc), status=exc.status, location=exc.location) from exc
        draft = _Draft(
            draft_id=draft_id,
            project_reference=loaded_reference,
            specification=specification,
            object_definition=definition,
            validation=validation,
            created_at=self.clock(),
        )
        self._draft_counter += 1
        self._drafts[draft_id] = draft
        return {
            "draft_id": draft_id,
            "project_reference": copy.deepcopy(loaded_reference),
            "object_reference": _exact_reference(
                definition, "object_definition_id"
            ),
            "form": specification["realization"]["form"],
            "validation": copy.deepcopy(validation),
            "evidence": copy.deepcopy(definition["evidence"]),
            "persistence_status": "not-written",
        }

    def inspect(self, draft_id: str) -> dict[str, Any]:
        draft = self._draft(draft_id)
        return {
            "draft_id": draft.draft_id,
            "project_reference": copy.deepcopy(draft.project_reference),
            "specification": copy.deepcopy(draft.specification),
            "object_definition": copy.deepcopy(draft.object_definition),
            "validation": copy.deepcopy(draft.validation),
            "evaluation": copy.deepcopy(draft.evaluation),
            "persistence_status": "not-written",
        }

    def evaluate(self, payload: dict[str, Any]) -> dict[str, Any]:
        draft = self._draft(payload["draft_id"])
        if draft.specification["realization"]["form"] != "native-kernel":
            evaluation = {
                "status": "not-applicable",
                "reason": "transparent compounds require an executable exact internal closure; this slice performs no backend build",
                "artifact": None,
                "evidence": copy.deepcopy(draft.object_definition["evidence"]),
            }
            draft.evaluation = evaluation
            return copy.deepcopy(evaluation)
        loaded = self.project_service.load()
        self._assert_project(draft.project_reference, _project_reference(loaded.manifest))
        kernel = draft.object_definition["realization"]["kernel"]
        try:
            wav_bytes, facts = evaluate_program(
                kernel,
                draft.specification["interface"],
                payload["audition"],
            )
        except NativeKernelError as exc:
            raise AuthoringError(exc.code, str(exc), location=exc.location) from exc
        digest = facts["content_hash"].removeprefix("sha256:")
        locator = f".schuss/cache/ai-authoring/{digest}.wav"
        cache_root = self.project_service._safe_workspace_path(
            ".schuss/cache/ai-authoring"
        )
        self.project_service._mkdir(cache_root, "ai-authoring-cache")
        self.project_service._atomic_write(
            self.project_service._safe_workspace_path(locator),
            wav_bytes,
            label="ai-authoring-audition",
            replace_target=False,
            allow_identical=True,
        )
        definition, validation = self._build_definition(
            draft.specification,
            draft.draft_id,
            loaded,
            host_evaluation={
                "status": "passed",
                "kernel_content_hash": kernel["content_hash"],
                "audition_request_hash": "sha256:"
                + hashlib.sha256(
                    core.canonical_json(payload["audition"]).encode("utf-8")
                ).hexdigest(),
                "artifact": {
                    key: copy.deepcopy(facts[key])
                    for key in (
                        "sample_rate",
                        "frame_count",
                        "channel_count",
                        "sample_format",
                        "byte_length",
                        "content_hash",
                        "measurements",
                    )
                },
            },
        )
        draft.object_definition = definition
        draft.validation = validation
        evaluation = {
            "status": "success",
            "artifact": {**facts, "portable_cache_locator": locator},
            "evidence": copy.deepcopy(definition["evidence"]),
        }
        draft.evaluation = evaluation
        return copy.deepcopy(evaluation)

    @staticmethod
    def _node_for_placement(
        definition: dict[str, Any], placement: dict[str, Any], graph: dict[str, Any]
    ) -> dict[str, Any] | None:
        if placement["kind"] == "library-only":
            return None
        occupied = {item["node_id"] for item in graph["nodes"]}
        candidate = 1
        while f"graph-node-{candidate:06d}" in occupied:
            candidate += 1
        contract = definition["component_contract"]
        supplied = {
            item["parameter_key"]: item["value"]
            for item in placement["parameter_values"]
        }
        if len(supplied) != len(placement["parameter_values"]):
            raise AuthoringError(
                "AUTHORING_PLACEMENT_PARAMETER_DUPLICATE",
                "placement parameter keys must be unique",
                location="$.payload.placement.parameter_values",
            )
        parameters = {item["semantic_key"]: item for item in contract["parameters"]}
        if set(supplied) - set(parameters):
            raise AuthoringError(
                "AUTHORING_PLACEMENT_PARAMETER_UNKNOWN",
                "placement contains a parameter key absent from the new object",
                location="$.payload.placement.parameter_values",
            )
        return {
            "node_id": f"graph-node-{candidate:06d}",
            "contract_reference": _exact_reference(
                contract, "component_contract_id"
            ),
            "parameter_values": [
                {
                    "facet_id": parameter["facet_id"],
                    "value": supplied.get(key, parameter["default"]),
                }
                for key, parameter in sorted(parameters.items())
            ],
            "attribute_values": [],
        }

    def preview(self, payload: dict[str, Any]) -> dict[str, Any]:
        draft = self._draft(payload["draft_id"])
        loaded = self.project_service.load()
        loaded_reference = _project_reference(loaded.manifest)
        self._assert_project(payload["expected_project_reference"], loaded_reference)
        self._assert_project(draft.project_reference, loaded_reference)
        graph = next(
            (
                item
                for item in loaded.context.records["graphs"]
                if _exact_reference(item, "graph_id")
                == loaded.manifest["primary_graph_reference"]
            ),
            None,
        )
        if graph is None:
            raise AuthoringError(
                "AUTHORING_PRIMARY_GRAPH_UNRESOLVED",
                "accepted primary graph is unresolved",
            )
        graph_node = self._node_for_placement(
            draft.object_definition, payload["placement"], graph
        )
        try:
            proposal = self.project_service.preview_object_change(
                draft.object_definition, graph_node
            )
        except ProjectTransactionRejected as exc:
            diagnostic = exc.result["diagnostics"][0]
            raise AuthoringError(
                diagnostic["code"],
                diagnostic["message"],
                status=exc.result["status"],
                location=diagnostic["location"],
            ) from exc
        except ProjectError as exc:
            raise AuthoringError(exc.code, str(exc), status=exc.status, location=exc.location) from exc
        preview_id = self._next_preview_id()
        descriptor = {
            "preview_id": preview_id,
            "expected_project_reference": proposal.expected_project_reference,
            "object_reference": _exact_reference(
                proposal.object_definition, "object_definition_id"
            ),
            "project_successor_reference": _project_reference(proposal.manifest),
            "graph_successor_reference": None
            if proposal.graph is None
            else _exact_reference(proposal.graph, "graph_id"),
            "write_plan_content_hash": proposal.write_plan["content_hash"],
            "placement": copy.deepcopy(payload["placement"]),
        }
        fingerprint = "sha256:" + hashlib.sha256(
            core.canonical_json(descriptor).encode("utf-8")
        ).hexdigest()
        preview = _Preview(
            preview_id=preview_id,
            draft_id=draft.draft_id,
            project_reference=loaded_reference,
            confirmation_fingerprint=fingerprint,
            proposal=proposal,
            created_at=self.clock(),
        )
        self._previews[preview_id] = preview
        return {
            **descriptor,
            "confirmation_fingerprint": fingerprint,
            "object_definition": copy.deepcopy(proposal.object_definition),
            "proposed_graph": copy.deepcopy(proposal.graph),
            "write_plan": copy.deepcopy(proposal.write_plan),
            "persistence_status": "not-written",
            "acceptance_boundary": "requires-explicit-confirmed-accept",
        }

    def accept(self, payload: dict[str, Any]) -> dict[str, Any]:
        preview = self._previews.get(payload["preview_id"])
        if preview is None:
            raise AuthoringError(
                "AUTHORING_PREVIEW_UNKNOWN",
                "authoring preview handle is absent from this process",
                status="unresolved",
            )
        if preview.consumed:
            raise AuthoringError(
                "AUTHORING_PREVIEW_CONSUMED",
                "authoring preview has already been accepted",
                status="conflict",
            )
        if self.clock() - preview.created_at > self.draft_ttl_seconds:
            del self._previews[preview.preview_id]
            raise AuthoringError(
                "AUTHORING_PREVIEW_EXPIRED",
                "authoring preview has expired",
                status="unresolved",
            )
        if (
            payload["expected_project_reference"] != preview.project_reference
            or payload["confirmation_fingerprint"]
            != preview.confirmation_fingerprint
        ):
            raise AuthoringError(
                "AUTHORING_CONFIRMATION_MISMATCH",
                "preview project reference or confirmation fingerprint changed",
                status="conflict",
            )
        try:
            value = self.project_service.accept_object_change(preview.proposal)
        except ProjectError as exc:
            raise AuthoringError(exc.code, str(exc), status=exc.status, location=exc.location) from exc
        preview.consumed = True
        return {
            **value,
            "preview_id": preview.preview_id,
            "confirmation_fingerprint": preview.confirmation_fingerprint,
        }

    def list_objects(self) -> dict[str, Any]:
        loaded = self.project_service.load()
        definitions = loaded.project_records.get("object-definition", ())
        return {
            "project_reference": _project_reference(loaded.manifest),
            "object_count": len(definitions),
            "objects": [
                {
                    "object_reference": _exact_reference(
                        item, "object_definition_id"
                    ),
                    "display_name": item["family"]["display_name"],
                    "function": item["family"]["function"],
                    "form": item["realization"]["form"],
                    "evidence": copy.deepcopy(item["evidence"]),
                }
                for item in sorted(
                    definitions,
                    key=lambda item: (
                        item["family"]["display_name"].lower(),
                        item["object_definition_id"],
                    ),
                )
            ],
        }

    def planning_objects(self) -> tuple[dict[str, Any], ...]:
        """Return the exact accepted project objects for sonic retrieval."""

        loaded = self.project_service.load()
        return tuple(
            copy.deepcopy(item)
            for item in loaded.project_records.get("object-definition", ())
        )

    def inspect_object(self, reference: dict[str, Any]) -> dict[str, Any]:
        loaded = self.project_service.load()
        matches = [
            item
            for item in loaded.project_records.get("object-definition", ())
            if _exact_reference(item, "object_definition_id") == reference
        ]
        if len(matches) != 1:
            raise AuthoringError(
                "PROJECT_OBJECT_REFERENCE_UNRESOLVED",
                "project-local object reference does not resolve exactly",
                status="unresolved",
                location="$.payload.object_reference",
            )
        return {
            "project_reference": _project_reference(loaded.manifest),
            "object_definition": copy.deepcopy(matches[0]),
        }


def dispatch_authoring_operation(
    request: dict[str, Any],
    context: OperationContext,
    service: SonicAuthoringService | None,
) -> dict[str, Any]:
    """Dispatch one closed v13 request and return a canonical result value."""

    from .control_plane import _diagnostic, _result, canonical_result_bytes

    operation = request.get("operation") if isinstance(request, dict) else None
    allowed = {
        "sonic.intent.plan",
        "authoring.draft.create",
        "authoring.draft.inspect",
        "authoring.draft.evaluate",
        "authoring.change.preview",
        "authoring.change.accept",
        "project.objects.list",
        "project.object.inspect",
    }
    errors: list[str] = []
    try:
        core.assert_portable_json_value(request)
    except ValueError as exc:
        errors.append(str(exc))
    schema = context.schemas.get("operation_request_v13")
    if schema is None:
        errors.append(
            "$: operation schema 'schuss-operation-request-v13' is unavailable in the selected context"
        )
    elif isinstance(request, dict):
        errors.extend(core.schema_errors(request, schema, schema))
    else:
        errors.append("$: operation request must be an object")
    if operation != "sonic.intent.plan" and service is None:
        errors.append("$: an explicit project authoring service is required")
    if operation not in allowed:
        errors.append("$.operation: operation is not in the AI authoring surface")
    if errors:
        result = _result(
            operation if operation in allowed else "invalid-request",
            "invalid",
            None,
            [
                _diagnostic(
                    "OPERATION_REQUEST_INVALID",
                    operation if isinstance(operation, str) else "invalid-request",
                    "$",
                    error,
                )
                for error in sorted(set(errors))
            ],
            version=13,
        )
        canonical_result_bytes(result, context)
        return result
    payload = request["payload"]
    try:
        if operation == "sonic.intent.plan":
            value = plan_sonic_intent(
                payload,
                context,
                () if service is None else service.planning_objects(),
            )
        else:
            assert service is not None
            if operation == "authoring.draft.create":
                value = service.create(payload)
            elif operation == "authoring.draft.inspect":
                value = service.inspect(payload["draft_id"])
            elif operation == "authoring.draft.evaluate":
                value = service.evaluate(payload)
            elif operation == "authoring.change.preview":
                value = service.preview(payload)
            elif operation == "authoring.change.accept":
                value = service.accept(payload)
            elif operation == "project.objects.list":
                value = service.list_objects()
            else:
                value = service.inspect_object(payload["object_reference"])
        result = _result(str(operation), "success", value, version=13)
    except AuthoringError as exc:
        result = _result(
            str(operation),
            exc.status,
            None,
            [
                _diagnostic(
                    exc.code,
                    str(operation),
                    exc.location,
                    str(exc),
                )
            ],
            version=13,
        )
    canonical_result_bytes(result, context)
    return result
