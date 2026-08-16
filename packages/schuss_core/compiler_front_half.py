"""Backend-neutral Schuss compiler planning through compiler stage 6.

The module is deliberately pure.  It accepts an immutable snapshot of exact
records and schemas, reuses the accepted target/backend resolver, and returns
derived canonical planning data.  It performs no project I/O, backend
dispatch, lowering, code generation, tool invocation, or device action.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_TOOLS = REPOSITORY_ROOT / "tools/contracts"
if str(CONTRACT_TOOLS) not in sys.path:
    sys.path.insert(0, str(CONTRACT_TOOLS))

import component_graph_rules as component
import target_backend_build_rules as target
import validator_core as core


PLANNER_ID = "schuss-compiler-front-half-000001"
PLANNER_VERSION = 1
POLICY_VERSIONS = (
    "schuss-canonical-json-v1",
    "schuss-component-graph-rules-v1",
    "schuss-binding-selection-v1",
    "schuss-compound-elaboration-v1",
    "schuss-dependency-planning-v1",
    "schuss-resource-planning-v1",
)
FRONT_HALF_STAGES = target.STAGES[:6]
LATER_STAGES = target.STAGES[6:]
RELEVANT_GROUPS = (
    "families",
    "contracts",
    "bindings",
    "graphs",
    "devices",
    "instruments",
    "panel_evidence",
    "mapping_coverage",
    "runtime_realizations",
    "capability",
    "environment",
    "target",
    "backend",
    "eligibility",
    "request",
    "evidence",
    "dependency_facts",
    "direct_operation_specs",
)

ID_FIELDS = {
    "families": "family_id",
    "contracts": "component_contract_id",
    "bindings": "implementation_id",
    "graphs": "graph_id",
    "devices": "device_profile_id",
    "instruments": "instrument_id",
    "panel_evidence": "panel_evidence_packet_id",
    "mapping_coverage": "coverage_report_id",
    "runtime_realizations": "runtime_realization_id",
    "capability": "capability_vocabulary_id",
    "environment": "build_environment_id",
    "target": "compute_target_id",
    "backend": "backend_id",
    "eligibility": "binding_eligibility_id",
    "request": "build_request_id",
    "evidence": "evidence_claim_id",
    "dependency_facts": "compiler_dependency_facts_id",
    "direct_operation_specs": "direct_operation_spec_id",
}

SCHEMA_KEYS = {
    "families": "family",
    "graphs": "graph",
    "devices": "device",
    "instruments": "instrument",
    "panel_evidence": "panel_evidence",
    "mapping_coverage": "mapping_coverage",
    "runtime_realizations": "runtime_realizations",
    "capability": "capability",
    "environment": "environment",
    "target": "target",
    "backend": "backend",
    "eligibility": "eligibility",
    "request": "request",
    "evidence": "evidence",
    "dependency_facts": "compiler_dependency_facts",
    "direct_operation_specs": "direct_operation_spec",
}

PLANNING_SCHEMA_KEYS = {
    "compiler_plan": "compiler-plan-result-v0",
    "compiler_artifact": "compiler-artifact-descriptor-v0",
    "compiler_resolution": "compiler-resolution-plan-v0",
    "compiler_elaborated_graph": "compiler-elaborated-graph-v0",
    "compiler_dependency": "compiler-dependency-plan-v0",
    "compiler_resource": "compiler-resource-plan-v0",
    "compiler_origin_map": "compiler-origin-map-v0",
}


def _json_round_trip(value: Any) -> Any:
    return json.loads(core.canonical_json(value))


@dataclass(frozen=True)
class CompilationContext:
    """Immutable canonical snapshot consumed by :func:`plan_build`.

    Values are retained as canonical JSON strings instead of caller-owned
    dictionaries.  This prevents a caller from mutating the compiler input
    after construction while keeping the API entirely in-memory.
    """

    build_request_reference_json: str
    closure_source_json: str
    records_json: tuple[tuple[str, tuple[str, ...]], ...]
    schemas_json: tuple[tuple[str, str], ...]

    @classmethod
    def from_values(
        cls,
        *,
        build_request_reference: Mapping[str, Any],
        closure_source: Mapping[str, Any],
        records: Mapping[str, Iterable[Mapping[str, Any]]],
        schemas: Mapping[str, Any],
    ) -> "CompilationContext":
        record_values = []
        for group in sorted(set(records) & set(RELEVANT_GROUPS)):
            encoded = tuple(
                sorted(core.canonical_json(copy.deepcopy(value)) for value in records[group])
            )
            record_values.append((group, encoded))
        schema_values: list[tuple[str, str]] = []
        for key in sorted(schemas):
            value = schemas[key]
            if key in {"contract_versions", "binding_versions"}:
                for version, schema in sorted(value.items()):
                    schema_values.append((f"{key}:{version}", core.canonical_json(schema)))
            elif isinstance(value, dict) and "$id" in value:
                schema_values.append((key, core.canonical_json(value)))
        return cls(
            core.canonical_json(dict(build_request_reference)),
            core.canonical_json(dict(closure_source)),
            tuple(record_values),
            tuple(schema_values),
        )

    def build_request_reference(self) -> dict[str, Any]:
        return json.loads(self.build_request_reference_json)

    def closure_source(self) -> dict[str, Any]:
        return json.loads(self.closure_source_json)

    def records(self) -> dict[str, list[dict[str, Any]]]:
        result = {group: [] for group in RELEVANT_GROUPS}
        for group, values in self.records_json:
            result[group] = [json.loads(value) for value in values]
        return result

    def schemas(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in self.schemas_json:
            if key.startswith("contract_versions:"):
                result.setdefault("contract_versions", {})[key.split(":", 1)[1]] = json.loads(value)
            elif key.startswith("binding_versions:"):
                result.setdefault("binding_versions", {})[key.split(":", 1)[1]] = json.loads(value)
            else:
                result[key] = json.loads(value)
        return result


@dataclass(frozen=True)
class _PlanDiagnostic:
    code: str
    severity: str
    stage: str
    subject: dict[str, Any]
    location: str
    message: str
    related_subjects: tuple[dict[str, Any], ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "stage": self.stage,
            "subject": copy.deepcopy(self.subject),
            "location": self.location,
            "message": self.message,
            "related_subjects": [copy.deepcopy(value) for value in self.related_subjects],
        }


def _subject(kind: str, identifier: str, revision: int | None = None, **extra: Any) -> dict[str, Any]:
    value: dict[str, Any] = {"kind": kind, "id": identifier}
    if revision is not None:
        value["revision"] = revision
    value.update(extra)
    return value


def _diagnostic(
    diagnostics: list[_PlanDiagnostic],
    code: str,
    stage: str,
    subject: dict[str, Any],
    location: str,
    message: str,
    *,
    severity: str = "error",
    related_subjects: Iterable[dict[str, Any]] = (),
) -> None:
    diagnostics.append(
        _PlanDiagnostic(
            code,
            severity,
            stage,
            copy.deepcopy(subject),
            location,
            message,
            tuple(copy.deepcopy(list(related_subjects))),
        )
    )


def _diagnostic_key(value: _PlanDiagnostic | dict[str, Any]) -> tuple[str, ...]:
    item = value.as_dict() if isinstance(value, _PlanDiagnostic) else value
    return (
        str(FRONT_HALF_STAGES.index(item["stage"]) if item["stage"] in FRONT_HALF_STAGES else 99),
        item["severity"],
        item["code"],
        core.canonical_json(item["subject"]),
        item["location"],
        item["message"],
    )


def operation_diagnostics(plan: Mapping[str, Any]) -> list[dict[str, str]]:
    """Project compiler diagnostics into the stable operation envelope."""

    return [
        {
            "code": item["code"],
            "severity": item["severity"],
            "subject": core.canonical_json(item["subject"]),
            "location": item["location"],
            "message": item["message"],
        }
        for item in plan.get("diagnostics", [])
    ]


def _ref(record: Mapping[str, Any], id_field: str) -> dict[str, Any]:
    return {
        id_field: record[id_field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def _key(value: Mapping[str, Any], id_field: str) -> tuple[str, int, str]:
    return value[id_field], value["revision"], value["content_hash"]


def _registry(values: Iterable[dict[str, Any]], id_field: str) -> dict[tuple[str, int, str], dict[str, Any]]:
    return {_key(value, id_field): value for value in values}


def _schema_for(group: str, record: Mapping[str, Any], schemas: Mapping[str, Any]) -> dict[str, Any] | None:
    if group == "contracts":
        return schemas.get("contract_versions", {}).get(record.get("schema_version"))
    if group == "bindings":
        return schemas.get("binding_versions", {}).get(record.get("schema_version"))
    key = SCHEMA_KEYS.get(group)
    return schemas.get(key) if key is not None else None


def _closure_description(
    context: CompilationContext,
    records: Mapping[str, list[dict[str, Any]]],
    schemas: Mapping[str, Any],
) -> dict[str, Any]:
    record_members = []
    for group in RELEVANT_GROUPS:
        for record in records[group]:
            id_field = ID_FIELDS[group]
            record_members.append(
                {
                    "record_kind": group,
                    "stable_id": record.get(id_field, "<missing>"),
                    "revision": record.get("revision", 0),
                    "content_hash": record.get("content_hash", "sha256:" + "0" * 64),
                }
            )
    record_members.sort(key=core.canonical_json)
    schema_members = []
    seen_schema_ids: set[str] = set()
    for _, encoded in context.schemas_json:
        schema = json.loads(encoded)
        identity = schema.get("$id")
        if not isinstance(identity, str) or identity in seen_schema_ids:
            continue
        seen_schema_ids.add(identity)
        schema_members.append(
            {
                "schema_version": identity.removesuffix(".schema.json"),
                "byte_sha256": hashlib.sha256(encoded.encode("utf-8")).hexdigest(),
            }
        )
    schema_members.sort(key=core.canonical_json)
    material = {
        "build_request_reference": context.build_request_reference(),
        "closure_source": context.closure_source(),
        "policy_versions": list(POLICY_VERSIONS),
        "record_members": record_members,
        "schema_members": schema_members,
    }
    digest = hashlib.sha256(core.canonical_json(material).encode("utf-8")).hexdigest()
    return {"hash": f"sha256:{digest}", **material}


def _stage1(
    context: CompilationContext,
    records: dict[str, list[dict[str, Any]]],
    schemas: dict[str, Any],
    diagnostics: list[_PlanDiagnostic],
) -> dict[str, Any]:
    stage = FRONT_HALF_STAGES[0]
    for group in RELEVANT_GROUPS:
        id_field = ID_FIELDS[group]
        seen: dict[tuple[str, int], str] = {}
        for index, record in enumerate(records[group]):
            subject = _subject(
                group,
                str(record.get(id_field, "<missing>")),
                record.get("revision") if isinstance(record.get("revision"), int) else None,
            )
            schema = _schema_for(group, record, schemas)
            if schema is None:
                _diagnostic(
                    diagnostics,
                    "COMPILER_SCHEMA_UNAVAILABLE",
                    stage,
                    subject,
                    f"$.records.{group}[{index}]",
                    f"schema {record.get('schema_version')!r} is absent from the exact compiler context",
                )
                continue
            for error in core.schema_errors(record, schema, schema):
                _diagnostic(
                    diagnostics,
                    "COMPILER_SCHEMA_STRUCTURE_INVALID",
                    stage,
                    subject,
                    f"$.records.{group}[{index}]",
                    error,
                )
            portability: list[core.Diagnostic] = []
            core.scan_portability(record, core.canonical_json(subject), portability)
            for item in portability:
                _diagnostic(
                    diagnostics,
                    "COMPILER_INPUT_NONPORTABLE",
                    stage,
                    subject,
                    item.location,
                    item.message,
                )
            if "content_hash" in record:
                try:
                    expected = core.record_content_hash(record, schema)
                except (KeyError, TypeError, ValueError) as exc:
                    expected = None
                    _diagnostic(
                        diagnostics,
                        "COMPILER_CONTENT_HASH_UNCOMPUTABLE",
                        stage,
                        subject,
                        f"$.records.{group}[{index}].content_hash",
                        str(exc),
                    )
                if expected is not None and record.get("content_hash") != expected:
                    _diagnostic(
                        diagnostics,
                        "COMPILER_CONTENT_HASH_MISMATCH",
                        stage,
                        subject,
                        f"$.records.{group}[{index}].content_hash",
                        f"expected {expected}",
                    )
            if isinstance(record.get(id_field), str) and isinstance(record.get("revision"), int):
                revision_key = (record[id_field], record["revision"])
                if revision_key in seen:
                    if seen[revision_key] != record.get("content_hash"):
                        _diagnostic(
                            diagnostics,
                            "COMPILER_ID_REVISION_COLLISION",
                            stage,
                            subject,
                            f"$.records.{group}[{index}]",
                            "one stable-ID/revision resolves to more than one content hash",
                        )
                    else:
                        _diagnostic(
                            diagnostics,
                            "COMPILER_ID_REVISION_DUPLICATE",
                            stage,
                            subject,
                            f"$.records.{group}[{index}]",
                            "the exact compiler closure contains a duplicate stable-ID/revision record",
                        )
                else:
                    seen[revision_key] = record.get("content_hash", "")

    if any(value.stage == stage for value in diagnostics):
        return {}

    request_ref = context.build_request_reference()
    if (
        set(request_ref) != {"build_request_id", "revision", "content_hash"}
        or not isinstance(request_ref.get("build_request_id"), str)
        or not isinstance(request_ref.get("revision"), int)
        or request_ref.get("revision", 0) < 1
        or not isinstance(request_ref.get("content_hash"), str)
    ):
        _diagnostic(
            diagnostics,
            "COMPILER_BUILD_REQUEST_REFERENCE_INVALID",
            stage,
            _subject("build-request", str(request_ref.get("build_request_id", "<missing>"))),
            "$.build_request_reference",
            "the compiler entry point requires one closed exact build-request reference",
        )
        return {}
    request_registry = _registry(records["request"], "build_request_id")
    request = request_registry.get(_key(request_ref, "build_request_id"))
    if request is None:
        _diagnostic(
            diagnostics,
            "COMPILER_BUILD_REQUEST_UNRESOLVED",
            stage,
            _subject("build-request", request_ref.get("build_request_id", "<missing>"), request_ref.get("revision")),
            "$.build_request_reference",
            "the exact build request is absent from the validated compiler context",
        )
        return {}

    selected_runtime = None
    if records["runtime_realizations"]:
        matches = [
            value
            for value in records["runtime_realizations"]
            if any(
                build["build_request_reference"] == request_ref
                for build in value["supported_builds"]
            )
        ]
        if len(matches) != 1:
            _diagnostic(
                diagnostics,
                "COMPILER_RUNTIME_REALIZATION_NOT_EXACT",
                stage,
                _subject("build-request", request["build_request_id"], request["revision"]),
                "$.runtime_realizations",
                f"expected one exact runtime realization for the build request, found {len(matches)}",
            )
            return {}
        selected_runtime = matches[0]

    graph_registry = _registry(records["graphs"], "graph_id")
    contract_registry = _registry(records["contracts"], "component_contract_id")
    target_registry = _registry(records["target"], "compute_target_id")
    backend_registry = _registry(records["backend"], "backend_id")
    instrument_registry = _registry(records["instruments"], "instrument_id")
    graph = graph_registry.get(_key(request["graph_reference"], "graph_id"))
    target_record = target_registry.get(_key(request["compute_target_reference"], "compute_target_id"))
    backend = backend_registry.get(_key(request["backend_reference"], "backend_id"))
    for kind, reference, value in (
        ("graph", request["graph_reference"], graph),
        ("compute-target", request["compute_target_reference"], target_record),
        ("backend", request["backend_reference"], backend),
    ):
        if value is None:
            id_field = next(key for key in reference if key.endswith("_id"))
            _diagnostic(
                diagnostics,
                "COMPILER_EXACT_REFERENCE_UNRESOLVED",
                stage,
                _subject(kind, reference[id_field], reference["revision"]),
                f"$.build_request.{kind}_reference",
                f"the exact {kind} reference does not resolve",
            )
    instrument = None
    instrument_ref = request["instrument_reference"]
    if instrument_ref["status"] == "included":
        instrument = instrument_registry.get(_key(instrument_ref, "instrument_id"))
        if instrument is None:
            _diagnostic(
                diagnostics,
                "COMPILER_EXACT_REFERENCE_UNRESOLVED",
                stage,
                _subject("instrument", instrument_ref["instrument_id"], instrument_ref["revision"]),
                "$.build_request.instrument_reference",
                "the exact included instrument does not resolve",
            )
        elif graph is not None:
            graph_ref = instrument["graph_reference"]
            if graph_ref.get("status") != "resolved" or _key(graph_ref, "graph_id") != _key(graph, "graph_id"):
                _diagnostic(
                    diagnostics,
                    "COMPILER_INSTRUMENT_GRAPH_MISMATCH",
                    stage,
                    _subject("instrument", instrument["instrument_id"], instrument["revision"]),
                    "$.instrument.graph_reference",
                    "the instrument and build request do not name the same exact graph",
                )

    if graph is not None:
        for node in graph["nodes"]:
            reference = node["contract_reference"]
            if _key(reference, "component_contract_id") not in contract_registry:
                _diagnostic(
                    diagnostics,
                    "COMPILER_CONTRACT_REFERENCE_UNRESOLVED",
                    stage,
                    _subject("graph-node", node["node_id"], graph_id=graph["graph_id"]),
                    "$.graph.nodes.contract_reference",
                    "an exact node contract is absent",
                )
    for binding in records["bindings"]:
        realization = binding.get("realization", {})
        if realization.get("form") == "transparent-compound":
            reference = realization["graph_reference"]
            if _key(reference, "graph_id") not in graph_registry:
                _diagnostic(
                    diagnostics,
                    "COMPILER_TRANSPARENT_GRAPH_UNRESOLVED",
                    stage,
                    _subject("implementation-binding", binding["implementation_id"], binding["revision"]),
                    "$.realization.graph_reference",
                    "the transparent implementation graph is absent",
                )
    return {
        "request": request,
        "graph": graph,
        "instrument": instrument,
        "target": target_record,
        "backend": backend,
        "runtime_realization": selected_runtime,
        "contracts": contract_registry,
        "bindings": _registry(records["bindings"], "implementation_id"),
        "graphs": graph_registry,
    }


def _convert_core_diagnostics(
    values: Iterable[core.Diagnostic],
    stage: str,
) -> list[_PlanDiagnostic]:
    result = []
    for item in values:
        result.append(
            _PlanDiagnostic(
                item.code,
                item.severity,
                stage,
                _subject("semantic-record", item.subject),
                item.location,
                item.message,
            )
        )
    return result


def _stage2(
    selected: dict[str, Any],
    diagnostics: list[_PlanDiagnostic],
) -> None:
    stage = FRONT_HALF_STAGES[1]
    graph = selected["graph"]
    values: list[core.Diagnostic] = []
    component._validate_graphs([copy.deepcopy(graph)], selected["contracts"], values)
    diagnostics.extend(_convert_core_diagnostics(values, stage))


def _stage3(
    selected: dict[str, Any],
    records: dict[str, list[dict[str, Any]]],
    diagnostics: list[_PlanDiagnostic],
) -> dict[str, Any]:
    stage = FRONT_HALF_STAGES[2]
    values: list[core.Diagnostic] = []
    capability_registry, definitions = target._capability_definitions(records["capability"], values)
    environments = target._validate_environments(records["environment"], values)
    targets = target._validate_targets(
        records["target"], capability_registry, definitions, environments, values
    )
    backends = target._validate_backends(
        records["backend"], capability_registry, definitions, targets, environments, values
    )
    target._validate_build_requests(
        [selected["request"]],
        {target._exact(selected["graph"], "graph_id"): selected["graph"]},
        _registry(records["instruments"], "instrument_id"),
        targets,
        backends,
        values,
    )
    declarations = {
        item["capability_key"]: item["state"]
        for item in selected["target"]["capability_declarations"]
    }
    for requirement in selected["backend"]["required_target_capabilities"]:
        key = requirement["capability_key"]
        state = declarations.get(key)
        if state is None or state["status"] in {"unresolved", "not-evaluated"}:
            _diagnostic(
                diagnostics,
                f"COMPILER_TARGET_CAPABILITY_UNRESOLVED_{key.upper().replace('-', '_')}",
                stage,
                _subject("compute-target", selected["target"]["compute_target_id"], selected["target"]["revision"]),
                "$.target.capability_declarations",
                f"required target capability {key!r} is unresolved",
            )
        elif state["status"] == "unsupported" or not target._compare_capability(
            state["value"], requirement["value"], requirement["comparison_rule"]
        ):
            _diagnostic(
                diagnostics,
                f"COMPILER_TARGET_CAPABILITY_UNSUPPORTED_{key.upper().replace('-', '_')}",
                stage,
                _subject("compute-target", selected["target"]["compute_target_id"], selected["target"]["revision"]),
                "$.target.capability_declarations",
                f"required target capability {key!r} is unsupported",
            )
    diagnostics.extend(_convert_core_diagnostics(values, stage))
    return {"definitions": definitions, "targets": targets, "backends": backends}


def _resolution_status(traces: Iterable[Mapping[str, Any]]) -> str:
    statuses = {trace["status"] for trace in traces}
    if statuses == {"selected"}:
        return "success"
    if "invalid-override" in statuses:
        return "invalid"
    if "ambiguous" in statuses:
        return "ambiguous"
    if "unresolved" in statuses:
        return "unresolved"
    return "unsupported"


def _stage4(
    selected: dict[str, Any],
    records: dict[str, list[dict[str, Any]]],
    validated: dict[str, Any],
    diagnostics: list[_PlanDiagnostic],
) -> tuple[str, tuple[dict[str, Any], ...], dict[tuple[str, int, str], dict[str, Any]]]:
    stage = FRONT_HALF_STAGES[3]
    values: list[core.Diagnostic] = []
    evidence = _registry(records["evidence"], "evidence_claim_id")
    eligibility = target._validate_eligibility_records(
        records["eligibility"],
        selected["bindings"],
        selected["contracts"],
        validated["targets"],
        validated["backends"],
        validated["definitions"],
        evidence,
        values,
    )
    diagnostics.extend(_convert_core_diagnostics(values, stage))
    if values:
        return "invalid", (), eligibility
    graph = copy.deepcopy(selected["graph"])
    graph["nodes"] = sorted(graph["nodes"], key=lambda item: item["node_id"])
    traces = target.resolve_graph_bindings(
        graph,
        selected["target"],
        selected["backend"],
        eligibility.values(),
        selected["bindings"],
        validated["definitions"],
        selected["request"]["binding_overrides"],
    )
    status = _resolution_status(traces)
    if status != "success":
        for trace in traces:
            if trace["status"] == "selected":
                continue
            code = {
                "unsupported": "COMPILER_BINDING_UNSUPPORTED",
                "unresolved": "COMPILER_BINDING_UNRESOLVED",
                "ambiguous": "COMPILER_BINDING_AMBIGUOUS",
                "invalid-override": "COMPILER_BINDING_OVERRIDE_INVALID",
            }[trace["status"]]
            _diagnostic(
                diagnostics,
                code,
                stage,
                _subject("graph-node", trace["node_id"], graph_id=graph["graph_id"]),
                "$.resolution_traces",
                f"binding resolution ended {trace['status']} for the exact graph node",
            )
    return status, traces, eligibility


def _facet_type_compatible(kind: str, outer: dict[str, Any], inner: dict[str, Any]) -> bool:
    if kind == "port":
        return outer["direction"] == inner["direction"] and not component._port_type_mismatches(outer, inner)
    if kind == "parameter":
        return all(outer[field] == inner[field] for field in ("representation", "unit", "domain", "update_behavior"))
    if kind == "action":
        return outer["payload_kind"] == inner["payload_kind"]
    if kind == "display":
        return outer["value_kind"] == inner["value_kind"] and outer["access"] == inner["access"]
    return False


class _ElaborationFailure(RuntimeError):
    pass


def _elaborate(
    selected: dict[str, Any],
    eligibility: Mapping[tuple[str, int, str], dict[str, Any]],
    definitions: Mapping[str, dict[str, Any]],
    outer_traces: tuple[dict[str, Any], ...],
    diagnostics: list[_PlanDiagnostic],
    closure_hash: str,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]], list[dict[str, Any]]]:
    stage = FRONT_HALF_STAGES[4]
    bindings = selected["bindings"]
    contracts = selected["contracts"]
    graphs = selected["graphs"]
    trace_by_top_node = {trace["node_id"]: trace for trace in outer_traces}
    derived_nodes: list[dict[str, Any]] = []
    derived_connections: list[dict[str, Any]] = []
    hierarchy: list[dict[str, Any]] = []
    origin_entries: list[dict[str, Any]] = []
    expansion_bindings: list[dict[str, Any]] = []
    public_port_exposures: list[dict[str, Any]] = []
    public_facet_exposures: list[dict[str, Any]] = []
    parameter_bindings: list[dict[str, Any]] = []
    compound_interface_mappings: list[dict[str, Any]] = []

    def resolve_inner(graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
        traces = target.resolve_graph_bindings(
            {**copy.deepcopy(graph), "nodes": sorted(graph["nodes"], key=lambda item: item["node_id"])},
            selected["target"],
            selected["backend"],
            eligibility.values(),
            bindings,
            definitions,
            (),
        )
        status = _resolution_status(traces)
        if status != "success":
            for trace in traces:
                if trace["status"] != "selected":
                    _diagnostic(
                        diagnostics,
                        "COMPILER_COMPOUND_INTERNAL_BINDING_UNRESOLVED",
                        stage,
                        _subject("graph-node", trace["node_id"], graph_id=graph["graph_id"]),
                        "$.transparent_graph.nodes",
                        f"transparent internal binding resolution ended {trace['status']}",
                    )
            raise _ElaborationFailure
        return {trace["node_id"]: trace for trace in traces}

    def primitive(
        node: dict[str, Any],
        contract: dict[str, Any],
        binding: dict[str, Any],
        instance_path: tuple[str, ...],
        graph: dict[str, Any],
        compound_ancestors: tuple[dict[str, Any], ...],
    ) -> dict[tuple[str, str], dict[str, str]]:
        derived_id = "derived-node:" + "/".join(instance_path)
        origin = {
            "authoritative_graph_reference": _ref(selected["graph"], "graph_id"),
            "outer_node_id": instance_path[0],
            "instance_path": list(instance_path),
            "selected_binding_reference": _ref(binding, "implementation_id"),
            "implementation_graph_reference": (
                _ref(graph, "graph_id") if graph["graph_id"] != selected["graph"]["graph_id"] else None
            ),
            "internal_node_id": node["node_id"],
        }
        derived_nodes.append(
            {
                "derived_node_id": derived_id,
                "contract_reference": copy.deepcopy(node["contract_reference"]),
                "binding_reference": _ref(binding, "implementation_id"),
                "parameter_values": copy.deepcopy(node["parameter_values"]),
                "attribute_values": copy.deepcopy(node["attribute_values"]),
                "state_ownership": [
                    {
                        "state_id": value["state_id"],
                        "ownership": value["ownership"],
                        "persistence": value["persistence"],
                        "reset_policy": value["reset_policy"],
                    }
                    for value in sorted(contract["state_declarations"], key=core.canonical_json)
                ],
                "origin": origin,
            }
        )
        hierarchy.append(
            {
                "derived_node_id": derived_id,
                "instance_path": list(instance_path),
                "compound_ancestors": [copy.deepcopy(value) for value in compound_ancestors],
            }
        )
        origin_entries.append(
            {
                "derived_subject": {"kind": "node", "id": derived_id},
                "origin": copy.deepcopy(origin),
            }
        )
        endpoints: dict[tuple[str, str], dict[str, str]] = {}
        for kind, facets in component._facet_maps(contract).items():
            for facet_id in sorted(facets):
                endpoints[(kind, facet_id)] = {
                    "derived_node_id": derived_id,
                    "facet_kind": kind,
                    "facet_id": facet_id,
                }
                origin_entries.append(
                    {
                        "derived_subject": {
                            "kind": "facet",
                            "id": f"{derived_id}#{kind}:{facet_id}",
                        },
                        "origin": {**copy.deepcopy(origin), "internal_facet_kind": kind, "internal_facet_id": facet_id},
                    }
                )
        return endpoints

    def expand_node(
        node: dict[str, Any],
        trace: dict[str, Any],
        graph: dict[str, Any],
        instance_path: tuple[str, ...],
        definition_stack: tuple[tuple[str, int, str], ...],
        compound_ancestors: tuple[dict[str, Any], ...],
    ) -> dict[tuple[str, str], dict[str, str]]:
        binding = bindings[_key(trace["selected_binding_reference"], "implementation_id")]
        contract = contracts[_key(node["contract_reference"], "component_contract_id")]
        realization = binding["realization"]
        expansion_bindings.append(
            {
                "instance_path": list(instance_path),
                "node_id": node["node_id"],
                "binding_reference": _ref(binding, "implementation_id"),
            }
        )
        if realization["form"] != "transparent-compound":
            return primitive(node, contract, binding, instance_path, graph, compound_ancestors)

        binding_key = _key(binding, "implementation_id")
        if binding_key in definition_stack:
            _diagnostic(
                diagnostics,
                "COMPILER_COMPOUND_RECURSION",
                stage,
                _subject("implementation-binding", binding["implementation_id"], binding["revision"], instance_path=list(instance_path)),
                "$.realization.graph_reference",
                "transparent compound definition expansion is recursive",
            )
            raise _ElaborationFailure
        inner_graph = graphs.get(_key(realization["graph_reference"], "graph_id"))
        if inner_graph is None:
            _diagnostic(
                diagnostics,
                "COMPILER_TRANSPARENT_GRAPH_UNRESOLVED",
                stage,
                _subject("implementation-binding", binding["implementation_id"], binding["revision"]),
                "$.realization.graph_reference",
                "transparent implementation graph is absent",
            )
            raise _ElaborationFailure
        mapping_keys = contract["compound_interface"]["mapping_keys"]
        contract_by_key = {value["mapping_key"]: value for value in mapping_keys}
        binding_by_key = {
            value["implementation_seam"]["mapping_key"]: value
            for value in binding["facet_mappings"]
            if value["implementation_seam"].get("seam_kind") == "graph-mapping-key"
        }
        graph_by_key = {
            value["mapping_key"]: value for value in inner_graph["compound_interface_mappings"]
        }
        if set(contract_by_key) != set(binding_by_key) or set(contract_by_key) != set(graph_by_key):
            _diagnostic(
                diagnostics,
                "COMPILER_COMPOUND_MAPPING_INCOMPLETE",
                stage,
                _subject("implementation-binding", binding["implementation_id"], binding["revision"]),
                "$.facet_mappings",
                "contract, binding, and implementation graph mapping keys are not total and equal",
            )
            raise _ElaborationFailure

        inner_trace_by_node = resolve_inner(inner_graph)
        endpoint_by_inner_node: dict[str, dict[tuple[str, str], dict[str, str]]] = {}
        ancestor = {
            "instance_path": list(instance_path),
            "binding_reference": _ref(binding, "implementation_id"),
            "graph_reference": _ref(inner_graph, "graph_id"),
        }
        inner_nodes = {value["node_id"]: value for value in inner_graph["nodes"]}
        for inner_node_id in sorted(inner_nodes):
            inner_node = inner_nodes[inner_node_id]
            endpoint_by_inner_node[inner_node_id] = expand_node(
                inner_node,
                inner_trace_by_node[inner_node_id],
                inner_graph,
                (*instance_path, inner_node_id),
                (*definition_stack, binding_key),
                (*compound_ancestors, ancestor),
            )
        for connection in sorted(inner_graph["connections"], key=lambda value: value["connection_id"]):
            source = endpoint_by_inner_node[connection["source"]["node_id"]][("port", connection["source"]["facet_id"])]
            destination = endpoint_by_inner_node[connection["destination"]["node_id"]][("port", connection["destination"]["facet_id"])]
            connection_id = "derived-connection:" + "/".join((*instance_path, connection["connection_id"]))
            derived_connections.append(
                {
                    "derived_connection_id": connection_id,
                    "source": source,
                    "destination": destination,
                    "origin": {
                        "authoritative_graph_reference": _ref(selected["graph"], "graph_id"),
                        "outer_node_id": instance_path[0],
                        "instance_path": list(instance_path),
                        "implementation_graph_reference": _ref(inner_graph, "graph_id"),
                        "internal_connection_id": connection["connection_id"],
                    },
                }
            )
            origin_entries.append(
                {
                    "derived_subject": {"kind": "connection", "id": connection_id},
                    "origin": copy.deepcopy(derived_connections[-1]["origin"]),
                }
            )

        public_endpoints: dict[tuple[str, str], dict[str, str]] = {}
        outer_facets = component._facet_maps(contract)
        for mapping_key in sorted(contract_by_key):
            contract_mapping = contract_by_key[mapping_key]
            binding_mapping = binding_by_key[mapping_key]["contract_facet"]
            target_mapping = graph_by_key[mapping_key]["target"]
            if (
                binding_mapping["facet_kind"] != contract_mapping["facet_kind"]
                or binding_mapping["facet_id"] != contract_mapping["facet_id"]
                or target_mapping["facet_kind"] != contract_mapping["facet_kind"]
            ):
                _diagnostic(
                    diagnostics,
                    "COMPILER_COMPOUND_MAPPING_INCOMPATIBLE",
                    stage,
                    _subject("compound-mapping", mapping_key, instance_path=list(instance_path)),
                    "$.compound_interface_mappings",
                    "compound mapping kinds or public facets disagree",
                )
                raise _ElaborationFailure
            inner_contract = contracts[_key(inner_nodes[target_mapping["node_id"]]["contract_reference"], "component_contract_id")]
            outer_facet = outer_facets[contract_mapping["facet_kind"]].get(contract_mapping["facet_id"])
            inner_facet = component._facet_maps(inner_contract)[target_mapping["facet_kind"]].get(target_mapping["facet_id"])
            if outer_facet is None or inner_facet is None or not _facet_type_compatible(
                contract_mapping["facet_kind"], outer_facet, inner_facet
            ):
                _diagnostic(
                    diagnostics,
                    "COMPILER_COMPOUND_MAPPING_INCOMPATIBLE",
                    stage,
                    _subject("compound-mapping", mapping_key, instance_path=list(instance_path)),
                    "$.compound_interface_mappings",
                    "compound public and internal facet types disagree",
                )
                raise _ElaborationFailure
            public_endpoints[(contract_mapping["facet_kind"], contract_mapping["facet_id"])] = endpoint_by_inner_node[target_mapping["node_id"]][
                (target_mapping["facet_kind"], target_mapping["facet_id"])
            ]
        return public_endpoints

    try:
        top_endpoints: dict[str, dict[tuple[str, str], dict[str, str]]] = {}
        top_nodes = {node["node_id"]: node for node in selected["graph"]["nodes"]}
        for node_id in sorted(top_nodes):
            top_endpoints[node_id] = expand_node(
                top_nodes[node_id],
                trace_by_top_node[node_id],
                selected["graph"],
                (node_id,),
                (),
                (),
            )
        for connection in sorted(selected["graph"]["connections"], key=lambda value: value["connection_id"]):
            source = top_endpoints[connection["source"]["node_id"]][("port", connection["source"]["facet_id"])]
            destination = top_endpoints[connection["destination"]["node_id"]][("port", connection["destination"]["facet_id"])]
            connection_id = "derived-connection:" + connection["connection_id"]
            origin = {
                "authoritative_graph_reference": _ref(selected["graph"], "graph_id"),
                "authoritative_connection_id": connection["connection_id"],
            }
            derived_connections.append(
                {
                    "derived_connection_id": connection_id,
                    "source": source,
                    "destination": destination,
                    "origin": origin,
                }
            )
            origin_entries.append(
                {
                    "derived_subject": {"kind": "connection", "id": connection_id},
                    "origin": copy.deepcopy(origin),
                }
            )
        for exposure in sorted(selected["graph"]["public_port_exposures"], key=core.canonical_json):
            target_endpoint = top_endpoints[exposure["node_port"]["node_id"]][
                ("port", exposure["node_port"]["facet_id"])
            ]
            public_port_exposures.append(
                {
                    "exposure_id": exposure["exposure_id"],
                    "graph_facet_id": exposure["graph_facet_id"],
                    "derived_target": copy.deepcopy(target_endpoint),
                }
            )
            origin_entries.append(
                {
                    "derived_subject": {"kind": "public-port-exposure", "id": exposure["exposure_id"]},
                    "origin": {"authoritative_graph_reference": _ref(selected["graph"], "graph_id"), "authoritative_exposure": copy.deepcopy(exposure)},
                }
            )
        for exposure in sorted(selected["graph"]["public_facet_exposures"], key=core.canonical_json):
            target_endpoint = top_endpoints[exposure["target"]["node_id"]][
                (exposure["target"]["facet_kind"], exposure["target"]["facet_id"])
            ]
            public_facet_exposures.append(
                {
                    "exposure_id": exposure["exposure_id"],
                    "graph_facet_kind": exposure["graph_facet_kind"],
                    "graph_facet_id": exposure["graph_facet_id"],
                    "derived_target": copy.deepcopy(target_endpoint),
                }
            )
            origin_entries.append(
                {
                    "derived_subject": {"kind": "public-facet-exposure", "id": exposure["exposure_id"]},
                    "origin": {"authoritative_graph_reference": _ref(selected["graph"], "graph_id"), "authoritative_exposure": copy.deepcopy(exposure)},
                }
            )
        for binding in sorted(selected["graph"]["parameter_bindings"], key=core.canonical_json):
            destination = binding["destination"]
            target_endpoint = top_endpoints[destination["node_id"]][
                (destination["facet_kind"], destination["facet_id"])
            ]
            parameter_bindings.append(
                {
                    "binding_id": binding["binding_id"],
                    "source_graph_parameter_id": binding["source_graph_parameter_id"],
                    "binding": copy.deepcopy(binding),
                    "derived_destination": copy.deepcopy(target_endpoint),
                }
            )
            origin_entries.append(
                {
                    "derived_subject": {"kind": "parameter-binding", "id": binding["binding_id"]},
                    "origin": {"authoritative_graph_reference": _ref(selected["graph"], "graph_id"), "authoritative_binding": copy.deepcopy(binding)},
                }
            )
        for mapping in sorted(selected["graph"]["compound_interface_mappings"], key=core.canonical_json):
            target_value = mapping["target"]
            target_endpoint = top_endpoints[target_value["node_id"]][
                (target_value["facet_kind"], target_value["facet_id"])
            ]
            compound_interface_mappings.append(
                {
                    "mapping_key": mapping["mapping_key"],
                    "derived_target": copy.deepcopy(target_endpoint),
                }
            )
            origin_entries.append(
                {
                    "derived_subject": {"kind": "compound-interface-mapping", "id": mapping["mapping_key"]},
                    "origin": {"authoritative_graph_reference": _ref(selected["graph"], "graph_id"), "authoritative_mapping": copy.deepcopy(mapping)},
                }
            )
        for kind, declarations in (
            ("port", selected["graph"]["public_ports"]),
            ("parameter", selected["graph"]["public_parameters"]),
            ("action", selected["graph"]["public_actions"]),
            ("display", selected["graph"]["public_displays"]),
        ):
            for declaration in declarations:
                origin_entries.append(
                    {
                        "derived_subject": {"kind": "public-graph-facet", "id": f"{kind}:{declaration['facet_id']}"},
                        "origin": {"authoritative_graph_reference": _ref(selected["graph"], "graph_id"), "authoritative_declaration": copy.deepcopy(declaration)},
                    }
                )
    except (KeyError, _ElaborationFailure) as exc:
        if isinstance(exc, KeyError):
            _diagnostic(
                diagnostics,
                "COMPILER_COMPOUND_MAPPING_INCOMPLETE",
                stage,
                _subject("dsp-graph", selected["graph"]["graph_id"], selected["graph"]["revision"]),
                "$.compound_interface_mappings",
                f"compound expansion endpoint is absent: {exc}",
            )
        return None, origin_entries, expansion_bindings

    elaborated = {
        "schema_version": "compiler-elaborated-graph-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "derived": True,
        "authoritative": False,
        "input_closure_hash": closure_hash,
        "source_graph_reference": _ref(selected["graph"], "graph_id"),
        "nodes": sorted(derived_nodes, key=lambda value: value["derived_node_id"]),
        "connections": sorted(derived_connections, key=lambda value: value["derived_connection_id"]),
        "hierarchy": sorted(hierarchy, key=lambda value: value["derived_node_id"]),
        "public_interface": {
            "ports": copy.deepcopy(sorted(selected["graph"]["public_ports"], key=core.canonical_json)),
            "parameters": copy.deepcopy(sorted(selected["graph"]["public_parameters"], key=core.canonical_json)),
            "actions": copy.deepcopy(sorted(selected["graph"]["public_actions"], key=core.canonical_json)),
            "displays": copy.deepcopy(sorted(selected["graph"]["public_displays"], key=core.canonical_json)),
            "port_exposures": public_port_exposures,
            "facet_exposures": public_facet_exposures,
            "parameter_bindings": parameter_bindings,
            "compound_interface_mappings": compound_interface_mappings,
        },
    }
    return elaborated, origin_entries, expansion_bindings


def _aligned(amount: int, alignment: int) -> int:
    return ((amount + alignment - 1) // alignment) * alignment


def _stage6(
    selected: dict[str, Any],
    eligibility: Mapping[tuple[str, int, str], dict[str, Any]],
    expansion_bindings: list[dict[str, Any]],
    dependency_facts: list[dict[str, Any]],
    diagnostics: list[_PlanDiagnostic],
    closure_hash: str,
    origin_entries: list[dict[str, Any]],
) -> tuple[str, dict[str, Any], dict[str, Any], dict[str, Any]]:
    stage = FRONT_HALF_STAGES[5]
    eligibility_by_binding = {
        _key(value["binding_reference"], "implementation_id"): value
        for value in eligibility.values()
        if _key(value["allowed_pair"]["target_reference"], "compute_target_id")
        == _key(selected["target"], "compute_target_id")
        and _key(value["allowed_pair"]["backend_reference"], "backend_id")
        == _key(selected["backend"], "backend_id")
    }
    dependency_requirements: list[dict[str, Any]] = []
    resource_requirements: list[dict[str, Any]] = []
    for instance in sorted(expansion_bindings, key=core.canonical_json):
        binding_key = _key(instance["binding_reference"], "implementation_id")
        eligibility_record = eligibility_by_binding.get(binding_key)
        if eligibility_record is None:
            _diagnostic(
                diagnostics,
                "COMPILER_ELIGIBILITY_UNRESOLVED",
                stage,
                _subject("implementation-binding", binding_key[0], binding_key[1], instance_path=instance["instance_path"]),
                "$.dependency_resource_planning",
                "the selected binding has no exact eligibility companion for this target/backend pair",
            )
            continue
        for requirement in eligibility_record["dependency_requirements"]:
            dependency_requirements.append(
                {
                    "dependency_id": requirement["dependency_id"],
                    "portable_locator": requirement["portable_locator"],
                    "state": copy.deepcopy(requirement["state"]),
                    "consumer": {
                        "instance_path": copy.deepcopy(instance["instance_path"]),
                        "binding_reference": copy.deepcopy(instance["binding_reference"]),
                    },
                }
            )
        for requirement in eligibility_record["resource_requirements"]:
            resource_requirements.append(
                {
                    **copy.deepcopy(requirement),
                    "consumer": {
                        "instance_path": copy.deepcopy(instance["instance_path"]),
                        "binding_reference": copy.deepcopy(instance["binding_reference"]),
                    },
                }
            )

    dependencies_by_id: dict[str, dict[str, Any]] = {}
    groups: dict[str, list[dict[str, Any]]] = {}
    for requirement in dependency_requirements:
        groups.setdefault(requirement["dependency_id"], []).append(requirement)

    providers = sorted(
        [
            copy.deepcopy(provider)
            for facts in dependency_facts
            for provider in facts["providers"]
        ],
        key=core.canonical_json,
    )
    providers_by_dependency: dict[str, list[dict[str, Any]]] = {}
    for provider in providers:
        providers_by_dependency.setdefault(provider["dependency_id"], []).append(provider)
    explicit_provider_facts = bool(dependency_facts)
    selected_providers: dict[str, dict[str, Any]] = {}

    def add_dependency(dependency_id: str, members: list[dict[str, Any]]) -> None:
        supported = [value for value in members if value["state"]["status"] == "supported"]
        unresolved = [value for value in members if value["state"]["status"] in {"unresolved", "not-evaluated"}]
        unsupported = [value for value in members if value["state"]["status"] == "unsupported"]
        requested_locators = sorted({value["portable_locator"] for value in supported})
        candidates = [
            value
            for value in providers_by_dependency.get(dependency_id, [])
            if not requested_locators or value["portable_locator"] in requested_locators
        ]
        available = [value for value in candidates if value["availability"] == "available"]
        decision = "included"
        if unsupported:
            decision = "missing"
            _diagnostic(
                diagnostics,
                "COMPILER_DEPENDENCY_MISSING",
                stage,
                _subject("dependency", dependency_id),
                "$.dependency_requirements",
                "a required dependency is explicitly unsupported",
            )
        elif unresolved:
            decision = "unresolved"
            _diagnostic(
                diagnostics,
                "COMPILER_DEPENDENCY_UNRESOLVED",
                stage,
                _subject("dependency", dependency_id),
                "$.dependency_requirements",
                "a required dependency fact is unknown",
            )
        elif len(requested_locators) > 1:
            decision = "conflict"
            _diagnostic(
                diagnostics,
                "COMPILER_DEPENDENCY_HASH_CONFLICT",
                stage,
                _subject("dependency", dependency_id),
                "$.dependency_requirements",
                "one dependency identity resolves to multiple content-addressed providers",
                related_subjects=[_subject("provider", locator) for locator in requested_locators],
            )
        elif explicit_provider_facts and not available:
            decision = "missing"
            _diagnostic(
                diagnostics,
                "COMPILER_DEPENDENCY_MISSING",
                stage,
                _subject("dependency", dependency_id),
                "$.dependency_provider_facts",
                "no available provider matches the required dependency and content locator",
                related_subjects=[_subject("dependency-provider", value["provider_id"]) for value in candidates],
            )
        elif explicit_provider_facts and len(available) > 1:
            decision = "conflict"
            _diagnostic(
                diagnostics,
                "COMPILER_DEPENDENCY_PROVIDER_AMBIGUOUS",
                stage,
                _subject("dependency", dependency_id),
                "$.dependency_provider_facts",
                "more than one available provider matches the required dependency",
                related_subjects=[_subject("dependency-provider", value["provider_id"]) for value in available],
            )

        versions = sorted({value["version"] for value in available})
        available_locators = sorted({value["portable_locator"] for value in available})
        if len({(value["version"], value["portable_locator"]) for value in available}) > 1:
            decision = "conflict"
            _diagnostic(
                diagnostics,
                "COMPILER_DEPENDENCY_VERSION_HASH_CONFLICT",
                stage,
                _subject("dependency", dependency_id),
                "$.dependency_provider_facts",
                "available providers disagree on dependency version or content hash",
                related_subjects=[_subject("dependency-provider", value["provider_id"]) for value in available],
            )
        if decision == "included" and len(available) == 1:
            selected_providers[dependency_id] = available[0]

        locators = requested_locators or available_locators
        dependencies_by_id[dependency_id] = {
            "dependency_id": dependency_id,
            "portable_locators": locators,
            "decision": decision,
            "selected_provider_ids": (
                [available[0]["provider_id"]]
                if decision == "included" and len(available) == 1
                else []
            ),
            "versions": versions,
            "consumers": sorted(
                [copy.deepcopy(value["consumer"]) for value in members],
                key=core.canonical_json,
            ),
        }
        origin_entries.append(
            {
                "derived_subject": {"kind": "dependency", "id": dependency_id},
                "origin": {
                    "consumers": sorted(
                        [copy.deepcopy(value["consumer"]) for value in members],
                        key=core.canonical_json,
                    ),
                    "provider_ids": sorted(value["provider_id"] for value in available),
                },
            }
        )

    for dependency_id in sorted(groups):
        add_dependency(dependency_id, groups[dependency_id])

    # Explicit planning facts may introduce transitive dependencies. They stay
    # inside the immutable compiler closure and never become target or backend
    # semantic truth.
    pending = sorted(selected_providers)
    inspected: set[str] = set()
    while pending:
        dependency_id = pending.pop(0)
        if dependency_id in inspected:
            continue
        inspected.add(dependency_id)
        provider = selected_providers[dependency_id]
        for required_id in sorted(provider["requires"]):
            if required_id not in dependencies_by_id:
                add_dependency(required_id, [])
            if required_id in selected_providers and required_id not in inspected:
                pending.append(required_id)
        pending.sort()

    dependency_edges = {
        dependency_id: sorted(
            required_id
            for required_id in provider["requires"]
            if required_id in dependencies_by_id
        )
        for dependency_id, provider in selected_providers.items()
    }
    ordered_dependency_ids: list[str] = []
    visiting: list[str] = []
    visited: set[str] = set()
    cycle_sets: set[tuple[str, ...]] = set()

    def visit(dependency_id: str) -> None:
        if dependency_id in visiting:
            start = visiting.index(dependency_id)
            cycle_sets.add(tuple(sorted(set(visiting[start:]))))
            return
        if dependency_id in visited:
            return
        visiting.append(dependency_id)
        for required_id in dependency_edges.get(dependency_id, []):
            visit(required_id)
        visiting.pop()
        visited.add(dependency_id)
        ordered_dependency_ids.append(dependency_id)

    for dependency_id in sorted(dependencies_by_id):
        visit(dependency_id)

    cycles = [{"dependency_ids": list(value)} for value in sorted(cycle_sets)]
    for cycle in cycles:
        _diagnostic(
            diagnostics,
            "COMPILER_DEPENDENCY_CYCLE_PROHIBITED",
            stage,
            _subject("dependency-cycle", "+".join(cycle["dependency_ids"])),
            "$.dependency_provider_facts.providers.requires",
            "the dependency provider graph contains a prohibited cycle",
            related_subjects=[_subject("dependency", value) for value in cycle["dependency_ids"]],
        )

    services: dict[str, list[dict[str, Any]]] = {}
    for dependency_id, provider in selected_providers.items():
        service = provider["exclusive_service"]
        if service is not None:
            services.setdefault(service, []).append(
                {"dependency_id": dependency_id, "provider_id": provider["provider_id"]}
            )
    exclusive_services = []
    for service_id in sorted(services):
        claims = sorted(services[service_id], key=core.canonical_json)
        if len(claims) < 2:
            continue
        conflict = {
            "service_id": service_id,
            "dependency_ids": sorted(value["dependency_id"] for value in claims),
            "provider_ids": sorted(value["provider_id"] for value in claims),
        }
        exclusive_services.append(conflict)
        _diagnostic(
            diagnostics,
            "COMPILER_DEPENDENCY_EXCLUSIVE_SERVICE_CONFLICT",
            stage,
            _subject("exclusive-service", service_id),
            "$.dependency_provider_facts.providers.exclusive_service",
            "more than one selected dependency provider claims the same exclusive service",
            related_subjects=[_subject("dependency-provider", value) for value in conflict["provider_ids"]],
        )

    dependencies = [dependencies_by_id[value] for value in sorted(dependencies_by_id)]

    dependency_plan = {
        "schema_version": "compiler-dependency-plan-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "derived": True,
        "input_closure_hash": closure_hash,
        "ordering_policy": "dependency-topological-v1",
        "ordered_dependency_ids": ordered_dependency_ids,
        "dependencies": dependencies,
        "exclusive_services": exclusive_services,
        "cycles": cycles,
        "limitations": (
            []
            if explicit_provider_facts
            else ["no-explicit-dependency-provider-facts-in-input-closure"]
        ),
    }

    target_regions = {
        region["region_id"]: region for region in selected["target"]["memory_regions"]
    }
    normalized_resources: list[dict[str, Any]] = []
    totals: dict[str, int] = {region_id: 0 for region_id in target_regions}
    unknowns: list[dict[str, Any]] = []
    for requirement in sorted(resource_requirements, key=core.canonical_json):
        state = requirement["state"]
        region = target_regions.get(requirement["region_id"])
        aligned_amount = _aligned(requirement["amount_bytes"], requirement["alignment_bytes"])
        decision = "included"
        if state["status"] in {"unresolved", "not-evaluated"}:
            decision = "unresolved"
            unknown = {
                "requirement_id": requirement["requirement_id"],
                "code": state["code"],
                "consumer": copy.deepcopy(requirement["consumer"]),
            }
            unknowns.append(unknown)
            _diagnostic(
                diagnostics,
                "COMPILER_RESOURCE_REQUIRED_FACT_UNKNOWN",
                stage,
                _subject("resource-requirement", requirement["requirement_id"], instance_path=requirement["consumer"]["instance_path"]),
                "$.resource_requirements",
                "a resource fact required for safe planning is unknown",
            )
        elif state["status"] == "unsupported" or region is None:
            decision = "unsupported"
            _diagnostic(
                diagnostics,
                "COMPILER_RESOURCE_UNSUPPORTED",
                stage,
                _subject("resource-requirement", requirement["requirement_id"], instance_path=requirement["consumer"]["instance_path"]),
                "$.resource_requirements",
                "the required resource or target region is unsupported",
            )
        else:
            totals[requirement["region_id"]] += aligned_amount
        normalized = {
            "requirement_id": requirement["requirement_id"],
            "resource_kind": requirement["resource_kind"],
            "region_id": requirement["region_id"],
            "fact_kind": "hard-requirement",
            "amount_bytes": requirement["amount_bytes"],
            "alignment_bytes": requirement["alignment_bytes"],
            "aligned_amount_bytes": aligned_amount,
            "state": copy.deepcopy(state),
            "decision": decision,
            "consumer": copy.deepcopy(requirement["consumer"]),
        }
        normalized_resources.append(normalized)
        origin_entries.append(
            {
                "derived_subject": {"kind": "resource", "id": requirement["requirement_id"] + "@" + "/".join(requirement["consumer"]["instance_path"])},
                "origin": {"consumer": copy.deepcopy(requirement["consumer"])},
            }
        )

    budgets = []
    budget_failure = False
    for region_id in sorted(target_regions):
        region = target_regions[region_id]
        used = totals[region_id]
        status = "within-budget" if used <= region["length_bytes"] else "exceeded"
        if status == "exceeded":
            budget_failure = True
            _diagnostic(
                diagnostics,
                "COMPILER_RESOURCE_HARD_BUDGET_EXCEEDED",
                stage,
                _subject("target-memory-region", region_id),
                "$.target.memory_regions",
                f"aligned hard requirements total {used} bytes against {region['length_bytes']} bytes",
            )
        budgets.append(
            {
                "region_id": region_id,
                "budget_kind": region["budget_kind"],
                "declared_bytes": region["length_bytes"],
                "planned_hard_requirement_bytes": used,
                "decision": status,
            }
        )
    resource_plan = {
        "schema_version": "compiler-resource-plan-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "derived": True,
        "input_closure_hash": closure_hash,
        "requirements": normalized_resources,
        "declarations": [
            {
                "region_id": region_id,
                "fact_kind": "target-declaration",
                "length_bytes": target_regions[region_id]["length_bytes"],
                "alignment_bytes": target_regions[region_id]["alignment_bytes"],
                "budget_kind": target_regions[region_id]["budget_kind"],
            }
            for region_id in sorted(target_regions)
        ],
        "estimates": [],
        "measurements": [],
        "unknowns": unknowns,
        "budgets": budgets,
    }

    stage_diagnostics = [value for value in diagnostics if value.stage == stage]
    if budget_failure:
        status = "budget-failure"
    elif any(value.code.endswith("UNRESOLVED") or "UNKNOWN" in value.code for value in stage_diagnostics):
        status = "unresolved"
    elif stage_diagnostics:
        status = "invalid"
    else:
        status = "success"
    for index, value in enumerate(sorted(stage_diagnostics, key=_diagnostic_key), 1):
        origin_entries.append(
            {
                "derived_subject": {
                    "kind": "diagnostic",
                    "id": f"{value.code}:{index:06d}",
                },
                "origin": {
                    "stage": value.stage,
                    "subject": copy.deepcopy(value.subject),
                    "related_subjects": [
                        copy.deepcopy(item) for item in value.related_subjects
                    ],
                },
            }
        )
    origin_map = {
        "schema_version": "compiler-origin-map-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "derived": True,
        "input_closure_hash": closure_hash,
        "entries": sorted(origin_entries, key=lambda value: core.canonical_json(value["derived_subject"])),
    }
    return status, dependency_plan, resource_plan, origin_map


def _artifact(kind: str, stage: str, payload: dict[str, Any], closure_hash: str) -> dict[str, Any]:
    data = core.canonical_json(payload).encode("utf-8")
    digest = hashlib.sha256(data).hexdigest()
    media = {
        "resolution-plan": "application/vnd.schuss.compiler-resolution-plan+json",
        "elaborated-graph": "application/vnd.schuss.compiler-elaborated-graph+json",
        "dependency-plan": "application/vnd.schuss.compiler-dependency-plan+json",
        "resource-plan": "application/vnd.schuss.compiler-resource-plan+json",
        "origin-source-map": "application/vnd.schuss.compiler-origin-map+json",
    }[kind]
    return {
        "descriptor": {
            "schema_version": "compiler-artifact-descriptor-v0",
            "artifact_id": f"schuss-compiler-artifact-{digest[:16]}",
            "artifact_kind": kind,
            "producer": {"stage": stage, "version": 1},
            "input_closure_hash": closure_hash,
            "media_type": media,
            "byte_length": len(data),
            "byte_sha256": digest,
            "portable_locator": f"compiler-plans/sha256/{digest}.json",
        },
        "payload": payload,
    }


def _validate_planning_value(
    value: dict[str, Any], schema_key: str, schemas: Mapping[str, Any]
) -> None:
    schema = schemas.get(schema_key)
    if schema is None:
        raise ValueError(f"compiler planning schema {schema_key!r} is unavailable")
    errors = core.schema_errors(value, schema, schema)
    if errors:
        raise ValueError(f"compiler produced invalid {schema_key}: {errors}")


def _stage_record(
    ordinal: int,
    stage: str,
    status: str,
    artifacts: Iterable[str],
    diagnostics: Iterable[_PlanDiagnostic],
) -> dict[str, Any]:
    return {
        "ordinal": ordinal,
        "stage": stage,
        "status": status,
        "artifact_kinds": sorted(set(artifacts)),
        "diagnostic_codes": sorted({value.code for value in diagnostics if value.stage == stage}),
    }


def _not_run_stages(
    start: int,
    stage_statuses: Mapping[str, str],
    artifacts: Mapping[str, list[str]],
    diagnostics: Iterable[_PlanDiagnostic],
) -> list[dict[str, Any]]:
    result = []
    for ordinal, stage in enumerate(FRONT_HALF_STAGES, 1):
        status = stage_statuses.get(stage, "not-run" if ordinal >= start else "success")
        result.append(_stage_record(ordinal, stage, status, artifacts.get(stage, []), diagnostics))
    return result


def plan_build(context: CompilationContext) -> dict[str, Any]:
    """Plan one exact build request through compiler stage 6.

    This is the sole public compiler-front-half entry point.  Every exit marks
    stages 7-10 not-run and creates no build result or backend execution.
    """

    records = context.records()
    schemas = context.schemas()
    closure = _closure_description(context, records, schemas)
    diagnostics: list[_PlanDiagnostic] = []
    artifacts: list[dict[str, Any]] = []
    artifact_kinds: dict[str, list[str]] = {}
    stage_statuses: dict[str, str] = {}
    final_status = "invalid"

    selected = _stage1(context, records, schemas, diagnostics)
    stage1_diags = [value for value in diagnostics if value.stage == FRONT_HALF_STAGES[0]]
    if stage1_diags or not selected:
        stage_statuses[FRONT_HALF_STAGES[0]] = "invalid"
        stages = _not_run_stages(2, stage_statuses, artifact_kinds, diagnostics)
    else:
        stage_statuses[FRONT_HALF_STAGES[0]] = "success"
        _stage2(selected, diagnostics)
        stage2_diags = [value for value in diagnostics if value.stage == FRONT_HALF_STAGES[1]]
        if stage2_diags:
            stage_statuses[FRONT_HALF_STAGES[1]] = "invalid"
            stages = _not_run_stages(3, stage_statuses, artifact_kinds, diagnostics)
        else:
            stage_statuses[FRONT_HALF_STAGES[1]] = "success"
            validated = _stage3(selected, records, diagnostics)
            stage3_diags = [value for value in diagnostics if value.stage == FRONT_HALF_STAGES[2]]
            if stage3_diags:
                codes = {value.code for value in stage3_diags}
                if any("UNRESOLVED" in value for value in codes):
                    stage_statuses[FRONT_HALF_STAGES[2]] = "unresolved"
                elif any("UNSUPPORTED" in value for value in codes):
                    stage_statuses[FRONT_HALF_STAGES[2]] = "unsupported"
                else:
                    stage_statuses[FRONT_HALF_STAGES[2]] = "invalid"
                final_status = stage_statuses[FRONT_HALF_STAGES[2]]
                stages = _not_run_stages(4, stage_statuses, artifact_kinds, diagnostics)
            else:
                stage_statuses[FRONT_HALF_STAGES[2]] = "success"
                resolution_status, traces, eligibility = _stage4(
                    selected, records, validated, diagnostics
                )
                resolution_payload = {
                    "schema_version": "compiler-resolution-plan-v0",
                    "canonical_profile": "schuss-canonical-json-v1",
                    "derived": True,
                    "input_closure_hash": closure["hash"],
                    "build_request_reference": context.build_request_reference(),
                    "selection_policy_version": "schuss-binding-selection-v1",
                    "status": resolution_status,
                    "traces": list(traces),
                }
                if traces:
                    _validate_planning_value(resolution_payload, "compiler_resolution", schemas)
                    artifacts.append(_artifact("resolution-plan", FRONT_HALF_STAGES[3], resolution_payload, closure["hash"]))
                    artifact_kinds[FRONT_HALF_STAGES[3]] = ["resolution-plan"]
                stage_statuses[FRONT_HALF_STAGES[3]] = resolution_status
                if resolution_status != "success":
                    final_status = resolution_status
                    stages = _not_run_stages(5, stage_statuses, artifact_kinds, diagnostics)
                else:
                    elaborated, origins, expansion_bindings = _elaborate(
                        selected,
                        eligibility,
                        validated["definitions"],
                        traces,
                        diagnostics,
                        closure["hash"],
                    )
                    stage5_diags = [value for value in diagnostics if value.stage == FRONT_HALF_STAGES[4]]
                    if stage5_diags or elaborated is None:
                        stage_statuses[FRONT_HALF_STAGES[4]] = "invalid"
                        stages = _not_run_stages(6, stage_statuses, artifact_kinds, diagnostics)
                    else:
                        stage_statuses[FRONT_HALF_STAGES[4]] = "success"
                        _validate_planning_value(elaborated, "compiler_elaborated_graph", schemas)
                        artifacts.append(_artifact("elaborated-graph", FRONT_HALF_STAGES[4], elaborated, closure["hash"]))
                        artifact_kinds[FRONT_HALF_STAGES[4]] = ["elaborated-graph"]
                        planning_status, dependency_plan, resource_plan, origin_map = _stage6(
                            selected,
                            eligibility,
                            expansion_bindings,
                            records["dependency_facts"],
                            diagnostics,
                            closure["hash"],
                            origins,
                        )
                        for value, schema_key, kind in (
                            (dependency_plan, "compiler_dependency", "dependency-plan"),
                            (resource_plan, "compiler_resource", "resource-plan"),
                            (origin_map, "compiler_origin_map", "origin-source-map"),
                        ):
                            _validate_planning_value(value, schema_key, schemas)
                            artifacts.append(_artifact(kind, FRONT_HALF_STAGES[5], value, closure["hash"]))
                        artifact_kinds[FRONT_HALF_STAGES[5]] = [
                            "dependency-plan",
                            "origin-source-map",
                            "resource-plan",
                        ]
                        stage_statuses[FRONT_HALF_STAGES[5]] = planning_status
                        final_status = planning_status
                        stages = _not_run_stages(7, stage_statuses, artifact_kinds, diagnostics)

    if final_status == "invalid" and all(value == "success" for value in stage_statuses.values()):
        final_status = "success"
    elif final_status == "invalid":
        for stage in FRONT_HALF_STAGES:
            if stage_statuses.get(stage) not in {None, "success"}:
                final_status = stage_statuses[stage]
                break

    unique_diagnostics = {
        core.canonical_json(value.as_dict()): value for value in diagnostics
    }
    ordered_diagnostics = [
        value.as_dict()
        for value in sorted(unique_diagnostics.values(), key=_diagnostic_key)
    ]
    passed_level_1 = stage_statuses.get(FRONT_HALF_STAGES[0]) == "success"
    passed_level_2 = all(
        stage_statuses.get(stage) == "success"
        for stage in FRONT_HALF_STAGES[1:]
    )
    plan = {
        "schema_version": "compiler-plan-result-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "planner": {"planner_id": PLANNER_ID, "version": PLANNER_VERSION},
        "status": final_status,
        "input_closure": closure,
        "stages": stages,
        "artifacts": sorted(artifacts, key=lambda value: value["descriptor"]["artifact_kind"]),
        "diagnostics": ordered_diagnostics,
        "later_stages": [
            {"ordinal": ordinal, "stage": stage, "status": "not-run"}
            for ordinal, stage in enumerate(LATER_STAGES, 7)
        ],
        "evidence_levels": [
            {
                "level": level,
                "status": (
                    "passed"
                    if (level == 1 and passed_level_1) or (level == 2 and passed_level_2)
                    else ("failed" if level in {1, 2} and not (passed_level_1 if level == 1 else passed_level_2) else "not-run")
                ),
            }
            for level in range(1, 9)
        ],
        "build_result_status": "not-created",
        "backend_execution_status": "not-run",
        "authoritative_records_mutated": False,
    }
    _validate_planning_value(plan, "compiler_plan", schemas)
    for item in plan["artifacts"]:
        _validate_planning_value(item["descriptor"], "compiler_artifact", schemas)
    return plan


__all__ = ["CompilationContext", "plan_build"]
