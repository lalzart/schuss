"""Deterministic Task 010 product-CLI parsing helpers and presentation.

This module does not dispatch operations or load domain records.  It resolves
the two product locator kinds against an already validated
``OperationContext``, constructs existing Task 008 requests, and renders
existing operation results without changing their semantics.
"""

from __future__ import annotations

import re
from typing import Any, Iterable

from .control_plane import OperationContext
from .build_execution import ExecutionService, handler_reference


LOCATOR_RE = re.compile(
    r"^(?P<stable_id>schuss-[a-z0-9-]+-[0-9]{6})@(?P<revision>[1-9][0-9]*)$"
)


class ProductInputError(ValueError):
    """A deterministic pre-dispatch product-input failure."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _locator_parts(locator: str) -> tuple[str, int]:
    match = LOCATOR_RE.fullmatch(locator)
    if match is None:
        raise ProductInputError(
            "CLI_LOCATOR_MALFORMED",
            "locator must be an exact stable ID followed by @ and a positive revision",
        )
    return match.group("stable_id"), int(match.group("revision"))


def resolve_locator(
    locator: str,
    *,
    expected_kind: str,
    context: OperationContext,
) -> dict[str, Any]:
    """Resolve one exact shorthand locator inside the selected record set."""

    stable_id, revision = _locator_parts(locator)
    specifications = {
        "graph": ("graphs", "graph_id", "schuss-graph-"),
        "build-request": ("request", "build_request_id", "schuss-build-request-"),
        "instrument": ("instruments", "instrument_id", "schuss-instrument-"),
        "family": ("catalog-projection", "family_id", "schuss-family-"),
    }
    if expected_kind not in specifications:
        raise ValueError(f"unknown product locator kind {expected_kind!r}")
    group, id_field, required_prefix = specifications[expected_kind]
    if not stable_id.startswith(required_prefix):
        raise ProductInputError(
            "CLI_LOCATOR_WRONG_KIND",
            f"locator is not a {expected_kind} identity",
        )
    if group == "catalog-projection":
        families = (
            context.catalog_projection["families"]
            if context.catalog_projection is not None
            else ()
        )
        candidates = [record["family_reference"] for record in families]
    else:
        candidates = context.records[group]
    matches = [
        record
        for record in candidates
        if record.get(id_field) == stable_id and record.get("revision") == revision
    ]
    if not matches:
        raise ProductInputError(
            "CLI_LOCATOR_NOT_FOUND",
            f"locator {locator!r} is absent from the selected record set",
        )
    if len(matches) != 1:
        raise ProductInputError(
            "CLI_LOCATOR_AMBIGUOUS",
            f"locator {locator!r} does not resolve exactly once",
        )
    record = matches[0]
    return {
        id_field: record[id_field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def records_validate_request() -> dict[str, Any]:
    return {
        "schema_version": "schuss-operation-request-v1",
        "canonical_profile": "schuss-canonical-json-v1",
        "operation": "records.validate",
        "payload": {"scope": "accepted-record-closure"},
    }


def graph_inspect_request(graph_reference: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "schuss-operation-request-v1",
        "canonical_profile": "schuss-canonical-json-v1",
        "operation": "graph.inspect",
        "payload": {"graph_reference": graph_reference},
    }


def graph_transact_request(
    graph_reference: dict[str, Any], edits: list[Any]
) -> dict[str, Any]:
    return {
        "schema_version": "schuss-operation-request-v1",
        "canonical_profile": "schuss-canonical-json-v1",
        "operation": "graph.transact",
        "payload": {
            "graph_reference": graph_reference,
            "base_content_hash": graph_reference["content_hash"],
            "edits": edits,
        },
    }


def build_resolve_request(
    build_request_reference: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "schuss-operation-request-v1",
        "canonical_profile": "schuss-canonical-json-v1",
        "operation": "build.resolve",
        "payload": {"build_request_reference": build_request_reference},
    }


def build_plan_request(build_request_reference: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "schuss-operation-request-v4",
        "canonical_profile": "schuss-canonical-json-v1",
        "operation": "build.plan",
        "payload": {"build_request_reference": build_request_reference},
    }


def resolve_build_handler_locator(
    locator: str, service: ExecutionService
) -> dict[str, Any]:
    stable_id, revision = _locator_parts(locator)
    if not stable_id.startswith("schuss-build-handler-"):
        raise ProductInputError(
            "CLI_LOCATOR_WRONG_KIND", "locator is not a build-handler identity"
        )
    try:
        descriptor = service.descriptor_for_locator(stable_id, revision)
    except ValueError as exc:
        raise ProductInputError("CLI_HANDLER_NOT_FOUND", str(exc)) from exc
    return handler_reference(descriptor)


def build_execute_request(
    build_request_reference: dict[str, Any],
    exact_handler_reference: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "schuss-operation-request-v5",
        "canonical_profile": "schuss-canonical-json-v1",
        "operation": "build.execute",
        "payload": {
            "build_request_reference": build_request_reference,
            "handler_reference": exact_handler_reference,
            "output_locator": "build-output",
            "execution_intent": True,
        },
    }


def catalog_search_request(
    query: str, filters: dict[str, list[str]]
) -> dict[str, Any]:
    filter_names = (
        "function",
        "abstraction",
        "form",
        "signal_domain",
        "signal_rate",
        "signal_role",
        "capability",
        "technique",
        "readiness",
        "provenance",
    )
    return {
        "schema_version": "schuss-operation-request-v2",
        "canonical_profile": "schuss-canonical-json-v1",
        "operation": "catalog.search",
        "payload": {
            "query": query,
            "filters": {
                name: sorted(set(filters.get(name, ()))) for name in filter_names
            },
        },
    }


def catalog_inspect_request(
    family_reference: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "schuss-operation-request-v2",
        "canonical_profile": "schuss-canonical-json-v1",
        "operation": "catalog.inspect",
        "payload": {"family_reference": family_reference},
    }


def gills_inspect_request(
    instrument_reference: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "schuss-operation-request-v6",
        "canonical_profile": "schuss-canonical-json-v1",
        "operation": "gills.inspect",
        "payload": {"instrument_reference": instrument_reference},
    }


def application_describe_request() -> dict[str, Any]:
    return {
        "schema_version": "schuss-operation-request-v7",
        "canonical_profile": "schuss-canonical-json-v1",
        "operation": "application.describe",
        "payload": {"scope": "selected-context"},
    }


def _safe_text(value: Any) -> str:
    if value is None:
        return "none"
    if value is True:
        return "true"
    if value is False:
        return "false"
    text = str(value)
    return "".join(
        character
        if character >= " " and character != "\x7f"
        else f"\\u{ord(character):04x}"
        for character in text
    )


REFERENCE_ID_FIELDS = (
    "artifact_id",
    "backend_id",
    "binding_eligibility_id",
    "build_environment_id",
    "build_handler_id",
    "build_request_id",
    "build_result_id",
    "catalog_id",
    "component_contract_id",
    "compute_target_id",
    "device_profile_id",
    "evidence_claim_id",
    "family_id",
    "graph_id",
    "implementation_id",
    "instrument_id",
    "coverage_report_id",
    "panel_evidence_packet_id",
    "resource_report_id",
    "runtime_realization_id",
    "stable_id",
)


def _reference_id_field(reference: dict[str, Any]) -> str:
    matches = [field for field in REFERENCE_ID_FIELDS if field in reference]
    if len(matches) != 1:
        raise ValueError("human renderer expected one exact-reference identity")
    return matches[0]


def _append_reference(
    lines: list[str], label: str, reference: dict[str, Any], indent: str = ""
) -> None:
    if reference.get("status") == "omitted":
        lines.append(f"{indent}{label}: omitted")
        return
    id_field = _reference_id_field(reference)
    lines.append(
        f"{indent}{label}: {_safe_text(reference[id_field])}@{reference['revision']}"
    )
    lines.append(
        f"{indent}{label}_content_hash: {_safe_text(reference['content_hash'])}"
    )


def _append_list(
    lines: list[str], label: str, values: Iterable[Any], indent: str
) -> None:
    materialized = list(values)
    lines.append(f"{indent}{label}:")
    if not materialized:
        lines.append(f"{indent}  none")
        return
    for value in materialized:
        lines.append(f"{indent}  - {_safe_text(value)}")


def _append_tree(lines: list[str], value: Any, indent: str = "") -> None:
    if isinstance(value, dict):
        if not value:
            lines.append(f"{indent}none")
            return
        for key, item in value.items():
            if isinstance(item, (dict, list)):
                lines.append(f"{indent}{_safe_text(key)}:")
                _append_tree(lines, item, indent + "  ")
            else:
                lines.append(
                    f"{indent}{_safe_text(key)}: {_safe_text(item)}"
                )
        return
    if isinstance(value, list):
        if not value:
            lines.append(f"{indent}none")
            return
        for item in value:
            if isinstance(item, (dict, list)):
                lines.append(f"{indent}-")
                _append_tree(lines, item, indent + "  ")
            else:
                lines.append(f"{indent}- {_safe_text(item)}")
        return
    lines.append(f"{indent}{_safe_text(value)}")


def _append_graph_summary(
    lines: list[str], graph: dict[str, Any], indent: str = ""
) -> None:
    _append_reference(
        lines,
        "graph",
        {
            "graph_id": graph["graph_id"],
            "revision": graph["revision"],
            "content_hash": graph["content_hash"],
        },
        indent,
    )
    lines.append(f"{indent}public_ports:")
    if not graph["public_ports"]:
        lines.append(f"{indent}  none")
    for port in graph["public_ports"]:
        lines.append(
            f"{indent}  - {port['facet_id']} {port['direction']} {port['semantic_key']}"
        )
    lines.append(f"{indent}public_parameters:")
    if not graph["public_parameters"]:
        lines.append(f"{indent}  none")
    for parameter in graph["public_parameters"]:
        lines.append(
            f"{indent}  - {parameter['facet_id']} {parameter['semantic_key']}"
        )
    lines.append(f"{indent}nodes:")
    if not graph["nodes"]:
        lines.append(f"{indent}  none")
    for node in graph["nodes"]:
        lines.append(f"{indent}  - node: {node['node_id']}")
        _append_reference(
            lines,
            "contract",
            node["contract_reference"],
            indent + "    ",
        )
    lines.append(f"{indent}connections:")
    if not graph["connections"]:
        lines.append(f"{indent}  none")
    for connection in graph["connections"]:
        source = connection["source"]
        destination = connection["destination"]
        lines.append(f"{indent}  - connection: {connection['connection_id']}")
        lines.append(
            f"{indent}    source: {source['node_id']}.{source['facet_id']}"
        )
        lines.append(
            f"{indent}    destination: {destination['node_id']}.{destination['facet_id']}"
        )
    lines.append(f"{indent}parameter_bindings:")
    if not graph["parameter_bindings"]:
        lines.append(f"{indent}  none")
    for binding in graph["parameter_bindings"]:
        destination = binding["destination"]
        lines.append(f"{indent}  - binding: {binding['binding_id']}")
        lines.append(
            f"{indent}    source: {binding['source_graph_parameter_id']}"
        )
        lines.append(
            f"{indent}    destination: {destination['node_id']}.{destination['facet_id']}"
        )


def _find_request(
    context: OperationContext, reference: dict[str, Any]
) -> dict[str, Any] | None:
    matches = [
        record
        for record in context.records["request"]
        if record.get("build_request_id") == reference.get("build_request_id")
        and record.get("revision") == reference.get("revision")
        and record.get("content_hash") == reference.get("content_hash")
    ]
    return matches[0] if len(matches) == 1 else None


def _append_records_validate(lines: list[str], result: dict[str, Any]) -> None:
    value = result.get("value")
    if value is None:
        return
    lines.append("summaries:")
    for name, summary in value["summaries"].items():
        lines.append(f"  {name}:")
        _append_tree(lines, summary, "    ")


def _append_graph_inspect(lines: list[str], result: dict[str, Any]) -> None:
    value = result.get("value")
    if value is None:
        return
    _append_graph_summary(lines, value["graph"])
    lines.append(f"selection_status: {value['selection_status']}")
    lines.append(f"lowering_status: {value['lowering_status']}")
    lines.append("component_contract_closure:")
    if not value["component_contract_closure"]:
        lines.append("  none")
    for contract in value["component_contract_closure"]:
        _append_reference(
            lines,
            "contract",
            {
                "component_contract_id": contract["component_contract_id"],
                "revision": contract["revision"],
                "content_hash": contract["content_hash"],
            },
            "  ",
        )


def _append_build_resolve(
    lines: list[str],
    result: dict[str, Any],
    context: OperationContext,
) -> None:
    value = result.get("value")
    if value is None:
        return
    request_reference = value["build_request_reference"]
    _append_reference(lines, "build_request", request_reference)
    request_record = _find_request(context, request_reference)
    if request_record is not None:
        _append_reference(lines, "graph", request_record["graph_reference"])
        _append_reference(lines, "instrument", request_record["instrument_reference"])
        _append_reference(
            lines, "compute_target", request_record["compute_target_reference"]
        )
        _append_reference(lines, "backend", request_record["backend_reference"])
        lines.append(
            f"requested_stopping_stage: {request_record['requested_stopping_stage']}"
        )
    lines.append("resolution_traces:")
    if not value["resolution_traces"]:
        lines.append("  none")
    for trace in value["resolution_traces"]:
        lines.append(f"  - node: {trace['node_id']}")
        _append_reference(lines, "contract", trace["contract_reference"], "    ")
        lines.append(f"    status: {trace['status']}")
        lines.append(
            f"    selection_policy_id: {_safe_text(trace['selection_policy_id'])}"
        )
        selected = trace["selected_binding_reference"]
        if selected is None:
            lines.append("    selected_binding: none")
        else:
            _append_reference(lines, "selected_binding", selected, "    ")
        lines.append("    candidates:")
        if not trace["candidates"]:
            lines.append("      none")
        for candidate in trace["candidates"]:
            lines.append("      -")
            _append_reference(
                lines, "binding", candidate["binding_reference"], "        "
            )
            _append_reference(
                lines,
                "eligibility",
                candidate["eligibility_reference"],
                "        ",
            )
            lines.append(f"        priority: {candidate['priority']}")
            lines.append(
                "        selection_policy_id: "
                + _safe_text(candidate["selection_policy_id"])
            )
            _append_list(
                lines,
                "exclusion_reasons",
                candidate["exclusion_reasons"],
                "        ",
            )
            _append_list(
                lines,
                "unresolved_reasons",
                candidate["unresolved_reasons"],
                "        ",
            )
    invocation = value["backend_invocation"]
    lines.append("backend_invocation:")
    if invocation is None:
        lines.append("  none")
    else:
        boundary = invocation["boundary"]
        lines.append(f"  status: {invocation['status']}")
        lines.append(f"  completed_stage: {boundary['completed_stage']}")
        lines.append(f"  next_stage: {boundary['next_stage']}")
        lines.append(f"  next_stage_status: {boundary['next_stage_status']}")
        lines.append(
            "  executable_handler_status: "
            + boundary["executable_handler_status"]
        )


def _append_graph_transact(
    lines: list[str], result: dict[str, Any], request: dict[str, Any]
) -> None:
    _append_reference(lines, "base_graph", request["payload"]["graph_reference"])
    value = result.get("value")
    if value is None:
        return
    lines.append("proposal_status: proposed-non-persisted")
    lines.append(f"persistence_status: {value['persistence_status']}")
    _append_graph_summary(lines, value["proposed_graph"])
    lines.append("validation:")
    lines.append(
        f"  component_graph: {value['validation']['component_graph']['status']}"
    )
    lines.append(
        f"  device_instrument: {value['validation']['device_instrument']['status']}"
    )


def _append_catalog_search(lines: list[str], result: dict[str, Any]) -> None:
    value = result.get("value")
    if value is None:
        return
    _append_reference(lines, "catalog", value["catalog_reference"])
    lines.append(f"projection_version: {_safe_text(value['projection_version'])}")
    lines.append(f"match_algorithm: {_safe_text(value['match_algorithm'])}")
    lines.append(f"input_closure_hash: {_safe_text(value['input_closure_hash'])}")
    lines.append(f"query: {_safe_text(value['query'])}")
    lines.append("filters:")
    _append_tree(lines, value["filters"], "  ")
    lines.append(f"total_matches: {value['total_matches']}")
    lines.append("results:")
    if not value["results"]:
        lines.append("  none")
    for item in value["results"]:
        lines.append("  -")
        _append_reference(lines, "family", item["family_reference"], "    ")
        lines.append(f"    display_name: {_safe_text(item['display_name'])}")
        lines.append(f"    primary_function: {_safe_text(item['primary_function'])}")
        lines.append(f"    abstraction_level: {_safe_text(item['abstraction_level'])}")
        _append_list(lines, "technique_tags", item["technique_tags"], "    ")
        _append_list(
            lines, "implementation_forms", item["implementation_forms"], "    "
        )
        _append_list(lines, "readiness_states", item["readiness_states"], "    ")
        lines.append(
            "    contract_facets_available: "
            + _safe_text(item["contract_facets_available"])
        )
        _append_list(
            lines, "provenance_facets", item["provenance_facets"], "    "
        )


def _append_catalog_inspect(lines: list[str], result: dict[str, Any]) -> None:
    value = result.get("value")
    if value is None:
        return
    _append_reference(lines, "catalog", value["catalog_reference"])
    lines.append(f"projection_version: {_safe_text(value['projection_version'])}")
    lines.append(f"input_closure_hash: {_safe_text(value['input_closure_hash'])}")
    family = value["family"]
    _append_reference(lines, "family", family["family_reference"])
    lines.append(f"display_name: {_safe_text(family['display_name'])}")
    lines.append(f"description: {_safe_text(family['description'])}")
    lines.append(f"primary_function: {_safe_text(family['primary_function'])}")
    lines.append(f"abstraction_level: {_safe_text(family['abstraction_level'])}")
    _append_list(lines, "aliases", family["aliases"], "")
    _append_list(lines, "technique_tags", family["technique_tags"], "")
    _append_list(lines, "implementation_forms", family["implementation_forms"], "")
    _append_list(lines, "contract_facet_names", family["contract_facet_names"], "")
    _append_list(lines, "capability_keys", family["capability_keys"], "")
    _append_list(lines, "readiness_states", family["readiness_states"], "")
    _append_list(lines, "provenance_facets", family["provenance_facets"], "")
    _append_list(lines, "unresolved_facts", family["unresolved_facts"], "")
    lines.append("implementations:")
    if not family["implementations"]:
        lines.append("  none")
    for implementation in family["implementations"]:
        lines.append(
            f"  - implementation_id: {_safe_text(implementation['implementation_id'])}"
        )
        if implementation["exact_reference"] is None:
            lines.append("    exact_reference: absent-in-phase-4a-overlay")
        else:
            _append_reference(
                lines,
                "exact_reference",
                implementation["exact_reference"],
                "    ",
            )
        lines.append(
            f"    display_name: {_safe_text(implementation['display_name'])}"
        )
        lines.append(f"    form: {_safe_text(implementation['form'])}")
        _append_list(
            lines,
            "observation_references",
            implementation["observation_references"],
            "    ",
        )
        _append_list(
            lines,
            "provenance_sources",
            implementation["provenance_sources"],
            "    ",
        )
        for label in (
            "contract_references",
            "binding_references",
            "eligibility_references",
            "target_references",
            "backend_references",
            "result_references",
            "artifact_references",
            "evidence_references",
        ):
            lines.append(f"    {label}:")
            if not implementation[label]:
                lines.append("      none")
            for reference in implementation[label]:
                _append_reference(lines, "reference", reference, "      ")
        _append_list(
            lines,
            "readiness_states",
            implementation["readiness_states"],
            "    ",
        )
        _append_list(
            lines,
            "unresolved_facts",
            implementation["unresolved_facts"],
            "    ",
        )


def _append_build_plan(lines: list[str], result: dict[str, Any]) -> None:
    value = result.get("value")
    if value is None:
        return
    lines.append(f"plan_status: {_safe_text(value['status'])}")
    lines.append(f"input_closure_hash: {_safe_text(value['input_closure']['hash'])}")
    lines.append("stages:")
    for stage in value["stages"]:
        lines.append(f"  - {stage['ordinal']} {stage['stage']}: {stage['status']}")
    lines.append("evidence_levels:")
    for item in value["evidence_levels"]:
        lines.append(f"  - {item['level']}: {item['status']}")


def _append_build_execute(lines: list[str], result: dict[str, Any]) -> None:
    value = result.get("value")
    if value is None:
        return
    lines.append(f"execution: {_safe_text(value['execution_id'])}")
    lines.append(f"plan_sha256: {_safe_text(value['plan_sha256'])}")
    _append_reference(lines, "handler", value["handler_reference"])
    lines.append(f"cache_policy: {_safe_text(value['cache']['policy'])}")
    lines.append(f"cache_lookup: {_safe_text(value['cache']['lookup'])}")
    lines.append(f"output_publication: {_safe_text(value['output_publication'])}")
    lines.append("artifacts:")
    if not value["artifacts"]:
        lines.append("  none")
    for item in value["artifacts"]:
        lines.append(f"  - kind: {_safe_text(item['artifact_kind'])}")
        lines.append(f"    byte_sha256: {_safe_text(item['byte_sha256'])}")
        lines.append(f"    byte_length: {item['byte_length']}")
        lines.append(f"    portable_locator: {_safe_text(item['portable_locator'])}")
    lines.append("evidence_levels:")
    for item in value["evidence_levels"]:
        lines.append(f"  - {item['level']}: {item['status']}")


def _append_application_describe(lines: list[str], result: dict[str, Any]) -> None:
    value = result.get("value")
    if value is None:
        return
    lines.append(f"description_version: {_safe_text(value['description_version'])}")
    lines.append("operations:")
    for item in value["operations"]:
        lines.append(f"  - operation: {_safe_text(item['operation'])}")
        lines.append(f"    domain_group: {_safe_text(item['domain_group'])}")
        lines.append(f"    effect_class: {_safe_text(item['effect_class'])}")
        lines.append(f"    availability: {_safe_text(item['availability'])}")
        lines.append(
            f"    request_schema: {_safe_text(item['request_schema_version'])}"
        )
        lines.append(
            f"    result_schema: {_safe_text(item['result_schema_version'])}"
        )
        _append_list(lines, "required_contexts", item["required_contexts"], "    ")
        _append_list(lines, "explicit_gates", item["explicit_gates"], "    ")
        lines.append(
            f"    evidence_boundary: {_safe_text(item['evidence_boundary'])}"
        )


def _append_gills_inspect(lines: list[str], result: dict[str, Any]) -> None:
    value = result.get("value")
    if value is None:
        return
    for label, record, id_field in (
        ("device_profile", value["device_profile"], "device_profile_id"),
        ("instrument", value["instrument"], "instrument_id"),
        ("panel_evidence", value["panel_evidence"], "panel_evidence_packet_id"),
        ("mapping_coverage", value["coverage_report"], "coverage_report_id"),
        (
            "runtime_realization",
            value["runtime_realization"],
            "runtime_realization_id",
        ),
    ):
        _append_reference(
            lines,
            label,
            {
                id_field: record[id_field],
                "revision": record["revision"],
                "content_hash": record["content_hash"],
            },
        )
    lines.append("build_support:")
    if not value["build_support"]:
        lines.append("  none")
    for supported in value["build_support"]:
        lines.append("  -")
        request = supported["build_request"]
        _append_reference(
            lines,
            "build_request",
            {
                "build_request_id": request["build_request_id"],
                "revision": request["revision"],
                "content_hash": request["content_hash"],
            },
            "    ",
        )
        _append_reference(lines, "handler", supported["handler"], "    ")


def _append_diagnostics(lines: list[str], result: dict[str, Any]) -> None:
    lines.append("diagnostics:")
    diagnostics = result["diagnostics"]
    if not diagnostics:
        lines.append("  none")
        return
    for diagnostic in diagnostics:
        lines.append(f"  - severity: {_safe_text(diagnostic['severity'])}")
        lines.append(f"    code: {_safe_text(diagnostic['code'])}")
        lines.append(f"    subject: {_safe_text(diagnostic['subject'])}")
        lines.append(f"    location: {_safe_text(diagnostic['location'])}")
        lines.append(f"    message: {_safe_text(diagnostic['message'])}")


def render_human_result(
    result: dict[str, Any],
    context: OperationContext,
    request: dict[str, Any],
) -> bytes:
    """Render one existing operation result as fixed deterministic plain text."""

    record_set = context.record_set_reference
    lines = [
        f"operation: {result['operation']}",
        f"status: {result['status']}",
        f"record_set: {record_set['record_set_id']}@{record_set['revision']}",
        f"record_set_content_hash: {record_set['content_hash']}",
    ]
    appenders = {
        "records.validate": lambda: _append_records_validate(lines, result),
        "graph.inspect": lambda: _append_graph_inspect(lines, result),
        "build.resolve": lambda: _append_build_resolve(lines, result, context),
        "build.plan": lambda: _append_build_plan(lines, result),
        "build.execute": lambda: _append_build_execute(lines, result),
        "graph.transact": lambda: _append_graph_transact(lines, result, request),
        "catalog.search": lambda: _append_catalog_search(lines, result),
        "catalog.inspect": lambda: _append_catalog_inspect(lines, result),
        "application.describe": lambda: _append_application_describe(lines, result),
        "gills.inspect": lambda: _append_gills_inspect(lines, result),
    }
    appender = appenders.get(result["operation"])
    if appender is not None:
        appender()
    _append_diagnostics(lines, result)
    return ("\n".join(lines) + "\n").encode("utf-8")


BASH_COMPLETION = """# Schuss CLI v2 completion for Bash
_schuss_complete() {
  local current="${COMP_WORDS[COMP_CWORD]}"
  local choices=""
  if [[ ${COMP_CWORD} -eq 1 ]]; then
    choices="validate application catalog project graph gills build completion op --help"
  else
    case "${COMP_WORDS[1]}" in
      validate) choices="--record-set --json --help" ;;
      application)
        if [[ ${COMP_CWORD} -eq 2 ]]; then choices="describe --help";
        else choices="--record-set --json --help"; fi
        ;;
      catalog)
        if [[ ${COMP_CWORD} -eq 2 ]]; then
          choices="search inspect --help"
        else
          case "${COMP_WORDS[2]}" in
            search) choices="--function --abstraction --form --signal-domain --signal-rate --signal-role --capability --technique --readiness --provenance --record-set --json --help" ;;
            inspect) choices="--record-set --json --help" ;;
          esac
        fi
        ;;
      project)
        if [[ ${COMP_CWORD} -eq 2 ]]; then
          choices="init inspect validate transact op completion --help"
        else
          case "${COMP_WORDS[2]}" in
            init) choices="--project --project-id --record-set --graph --instrument --build-request --json --help" ;;
            inspect|validate) choices="--project --json --help" ;;
            transact) choices="--project --expected-project --project-content-hash --graph-content-hash --edits --write --json --help" ;;
            op) choices="--project --request --json --help" ;;
            completion) choices="bash zsh fish --help" ;;
          esac
        fi
        ;;
      graph)
        if [[ ${COMP_CWORD} -eq 2 ]]; then
          choices="inspect transact --help"
        else
          case "${COMP_WORDS[2]}" in
            inspect) choices="--record-set --json --help" ;;
            transact) choices="--edits --record-set --json --help" ;;
          esac
        fi
        ;;
      gills)
        if [[ ${COMP_CWORD} -eq 2 ]]; then choices="inspect --help";
        else choices="--record-set --json --help"; fi
        ;;
      build)
        if [[ ${COMP_CWORD} -eq 2 ]]; then
          choices="resolve plan execute completion --help"
        else
          case "${COMP_WORDS[2]}" in
            resolve|plan) choices="--record-set --json --help" ;;
            execute) choices="--handler --output-root --execute --record-set --json --help" ;;
            completion) choices="bash zsh fish --help" ;;
          esac
        fi
        ;;
      completion) choices="bash zsh fish --help" ;;
      op) choices="--request --record-set --json --help" ;;
    esac
  fi
  COMPREPLY=( $(compgen -W "${choices}" -- "${current}") )
}
complete -F _schuss_complete schuss
"""


ZSH_COMPLETION = """#compdef schuss
# Schuss CLI v2 completion for Zsh
_schuss() {
  local -a root_commands application_commands catalog_commands project_commands graph_commands gills_commands build_commands shells
  root_commands=(validate application catalog project graph gills build completion op)
  application_commands=(describe)
  catalog_commands=(search inspect)
  project_commands=(init inspect validate transact op completion)
  graph_commands=(inspect transact)
  gills_commands=(inspect)
  build_commands=(resolve plan execute completion)
  shells=(bash zsh fish)
  if (( CURRENT == 2 )); then
    _describe 'command' root_commands
    return
  fi
  case ${words[2]} in
    validate) _values 'option' --record-set --json --help ;;
    application)
      if (( CURRENT == 3 )); then _describe 'application command' application_commands
      else _values 'option' --record-set --json --help; fi
      ;;
    catalog)
      if (( CURRENT == 3 )); then
        _describe 'catalog command' catalog_commands
      else
        case ${words[3]} in
          search) _values 'option' --function --abstraction --form --signal-domain --signal-rate --signal-role --capability --technique --readiness --provenance --record-set --json --help ;;
          inspect) _values 'option' --record-set --json --help ;;
        esac
      fi
      ;;
    project)
      if (( CURRENT == 3 )); then
        _describe 'project command' project_commands
      else
        case ${words[3]} in
          init) _values 'option' --project --project-id --record-set --graph --instrument --build-request --json --help ;;
          inspect|validate) _values 'option' --project --json --help ;;
          transact) _values 'option' --project --expected-project --project-content-hash --graph-content-hash --edits --write --json --help ;;
          op) _values 'option' --project --request --json --help ;;
          completion) _describe 'shell' shells ;;
        esac
      fi
      ;;
    graph)
      if (( CURRENT == 3 )); then
        _describe 'graph command' graph_commands
      else
        case ${words[3]} in
          inspect) _values 'option' --record-set --json --help ;;
          transact) _values 'option' --edits --record-set --json --help ;;
        esac
      fi
      ;;
    gills)
      if (( CURRENT == 3 )); then _describe 'gills command' gills_commands
      else _values 'option' --record-set --json --help; fi
      ;;
    build)
      if (( CURRENT == 3 )); then
        _describe 'build command' build_commands
      else
        case ${words[3]} in
          resolve|plan) _values 'option' --record-set --json --help ;;
          execute) _values 'option' --handler --output-root --execute --record-set --json --help ;;
          completion) _describe 'shell' shells ;;
        esac
      fi
      ;;
    completion) _describe 'shell' shells ;;
    op) _values 'option' --request --record-set --json --help ;;
  esac
}
_schuss "$@"
"""


FISH_COMPLETION = """# Schuss CLI v2 completion for Fish
complete -c schuss -f
complete -c schuss -n '__fish_use_subcommand' -a validate
complete -c schuss -n '__fish_use_subcommand' -a application
complete -c schuss -n '__fish_use_subcommand' -a catalog
complete -c schuss -n '__fish_use_subcommand' -a project
complete -c schuss -n '__fish_use_subcommand' -a graph
complete -c schuss -n '__fish_use_subcommand' -a gills
complete -c schuss -n '__fish_use_subcommand' -a build
complete -c schuss -n '__fish_use_subcommand' -a completion
complete -c schuss -n '__fish_use_subcommand' -a op
complete -c schuss -n '__fish_seen_subcommand_from application' -a describe
complete -c schuss -n '__fish_seen_subcommand_from catalog' -a 'search inspect'
complete -c schuss -n '__fish_seen_subcommand_from project' -a 'init inspect validate transact op completion'
complete -c schuss -n '__fish_seen_subcommand_from graph' -a 'inspect transact'
complete -c schuss -n '__fish_seen_subcommand_from gills' -a inspect
complete -c schuss -n '__fish_seen_subcommand_from build' -a 'resolve plan execute completion'
complete -c schuss -n '__fish_seen_subcommand_from completion' -a 'bash zsh fish'
complete -c schuss -n '__fish_seen_subcommand_from validate; and not __fish_seen_subcommand_from project' -l record-set -r
complete -c schuss -n '__fish_seen_subcommand_from application catalog graph gills build; and not __fish_seen_subcommand_from completion' -l record-set -r
complete -c schuss -n '__fish_seen_subcommand_from op; and not __fish_seen_subcommand_from project' -l record-set -r
complete -c schuss -n '__fish_seen_subcommand_from project; and __fish_seen_subcommand_from init' -l record-set -r
complete -c schuss -n '__fish_seen_subcommand_from validate; and not __fish_seen_subcommand_from project' -l json
complete -c schuss -n '__fish_seen_subcommand_from application catalog graph gills build; and not __fish_seen_subcommand_from completion' -l json
complete -c schuss -n '__fish_seen_subcommand_from op; and not __fish_seen_subcommand_from project' -l json
complete -c schuss -n '__fish_seen_subcommand_from project; and __fish_seen_subcommand_from init inspect validate transact op' -l json
complete -c schuss -n '__fish_seen_subcommand_from search' -l function -r
complete -c schuss -n '__fish_seen_subcommand_from search' -l abstraction -r
complete -c schuss -n '__fish_seen_subcommand_from search' -l form -r
complete -c schuss -n '__fish_seen_subcommand_from search' -l signal-domain -r
complete -c schuss -n '__fish_seen_subcommand_from search' -l signal-rate -r
complete -c schuss -n '__fish_seen_subcommand_from search' -l signal-role -r
complete -c schuss -n '__fish_seen_subcommand_from search' -l capability -r
complete -c schuss -n '__fish_seen_subcommand_from search' -l technique -r
complete -c schuss -n '__fish_seen_subcommand_from search' -l readiness -r
complete -c schuss -n '__fish_seen_subcommand_from search' -l provenance -r
complete -c schuss -n '__fish_seen_subcommand_from transact' -l edits -r
complete -c schuss -n '__fish_seen_subcommand_from op' -l request -r
complete -c schuss -n '__fish_seen_subcommand_from project; and __fish_seen_subcommand_from init inspect validate transact op' -l project -r
complete -c schuss -n '__fish_seen_subcommand_from project; and __fish_seen_subcommand_from init' -l project-id -r
complete -c schuss -n '__fish_seen_subcommand_from project; and __fish_seen_subcommand_from init' -l graph -r
complete -c schuss -n '__fish_seen_subcommand_from project; and __fish_seen_subcommand_from init' -l instrument -r
complete -c schuss -n '__fish_seen_subcommand_from project; and __fish_seen_subcommand_from init' -l build-request -r
complete -c schuss -n '__fish_seen_subcommand_from project; and __fish_seen_subcommand_from transact' -l expected-project -r
complete -c schuss -n '__fish_seen_subcommand_from project; and __fish_seen_subcommand_from transact' -l project-content-hash -r
complete -c schuss -n '__fish_seen_subcommand_from project; and __fish_seen_subcommand_from transact' -l graph-content-hash -r
complete -c schuss -n '__fish_seen_subcommand_from project; and __fish_seen_subcommand_from transact' -l write
complete -c schuss -n '__fish_seen_subcommand_from execute' -l handler -r
complete -c schuss -n '__fish_seen_subcommand_from execute' -l output-root -r
complete -c schuss -n '__fish_seen_subcommand_from execute' -l execute
complete -c schuss -l help
"""


COMPLETION_SCRIPTS = {
    "bash": BASH_COMPLETION,
    "zsh": ZSH_COMPLETION,
    "fish": FISH_COMPLETION,
}


BUILD_COMPLETION_SCRIPTS = {
    "bash": """# Schuss Task 014 build completion for Bash
_schuss_build_complete() {
  local current="${COMP_WORDS[COMP_CWORD]}"
  local choices=""
  if [[ ${COMP_CWORD} -eq 1 ]]; then
    choices="build"
  elif [[ ${COMP_CWORD} -eq 2 ]]; then
    choices="resolve plan execute completion --help"
  else
    case "${COMP_WORDS[2]}" in
      resolve|plan) choices="--record-set --json --help" ;;
      execute) choices="--handler --output-root --execute --record-set --json --help" ;;
      completion) choices="bash zsh fish --help" ;;
    esac
  fi
  COMPREPLY=( $(compgen -W "${choices}" -- "${current}") )
}
complete -F _schuss_build_complete schuss
""",
    "zsh": """#compdef schuss
# Schuss Task 014 build completion for Zsh
_schuss_build() {
  local -a build_commands shells
  build_commands=(resolve plan execute completion)
  shells=(bash zsh fish)
  if (( CURRENT == 2 )); then
    _values 'command' build
  elif (( CURRENT == 3 )); then
    _describe 'build command' build_commands
  else
    case ${words[3]} in
      resolve|plan) _values 'option' --record-set --json --help ;;
      execute) _values 'option' --handler --output-root --execute --record-set --json --help ;;
      completion) _describe 'shell' shells ;;
    esac
  fi
}
_schuss_build "$@"
""",
    "fish": """# Schuss Task 014 build completion for Fish
complete -c schuss -n '__fish_use_subcommand' -a build
complete -c schuss -n '__fish_seen_subcommand_from build' -a 'resolve plan execute completion'
complete -c schuss -n '__fish_seen_subcommand_from build; and __fish_seen_subcommand_from resolve plan execute' -l record-set -r
complete -c schuss -n '__fish_seen_subcommand_from build; and __fish_seen_subcommand_from resolve plan execute' -l json
complete -c schuss -n '__fish_seen_subcommand_from build; and __fish_seen_subcommand_from execute' -l handler -r
complete -c schuss -n '__fish_seen_subcommand_from build; and __fish_seen_subcommand_from execute' -l output-root -r
complete -c schuss -n '__fish_seen_subcommand_from build; and __fish_seen_subcommand_from execute' -l execute
complete -c schuss -n '__fish_seen_subcommand_from build; and __fish_seen_subcommand_from completion' -a 'bash zsh fish'
complete -c schuss -l help
""",
}


def build_completion_script(shell: str) -> bytes:
    try:
        value = BUILD_COMPLETION_SCRIPTS[shell]
    except KeyError as exc:
        raise ProductInputError(
            "CLI_COMPLETION_SHELL_UNSUPPORTED",
            f"unsupported completion shell {shell!r}",
        ) from exc
    return value.encode("utf-8")


def completion_script(shell: str) -> bytes:
    try:
        value = COMPLETION_SCRIPTS[shell]
    except KeyError as exc:
        raise ProductInputError(
            "CLI_COMPLETION_SHELL_UNSUPPORTED",
            f"unsupported completion shell {shell!r}",
        ) from exc
    return value.encode("utf-8")
