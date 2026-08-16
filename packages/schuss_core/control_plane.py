"""Pure Task 008 Schuss operation dispatcher.

Repository loading is an adapter concern. Once an :class:`OperationContext`
exists, dispatch reads only its in-memory snapshot and never writes files,
invokes a compiler/backend, or accesses hardware.
"""

from __future__ import annotations

import copy
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_TOOLS = REPOSITORY_ROOT / "tools/contracts"
if str(CONTRACT_TOOLS) not in sys.path:
    sys.path.insert(0, str(CONTRACT_TOOLS))

import aggregate_validator as aggregate
import component_graph_rules as component
import device_instrument_rules as device
import record_set_rules
import target_backend_build_rules as target
import validator_core as core

from . import catalog_projection as catalog
from . import compiler_front_half as compiler
from . import build_execution as execution


REQUEST_SCHEMA_NAME = "operation-request-v1.schema.json"
RESULT_SCHEMA_NAME = "operation-result-v1.schema.json"
GRAPH_SCHEMA_NAME = component.GRAPH_SCHEMA_NAME

TASK013_SCHEMA_NAMES = {
    "compiler_plan": "compiler-plan-result-v0.schema.json",
    "compiler_artifact": "compiler-artifact-descriptor-v0.schema.json",
    "compiler_resolution": "compiler-resolution-plan-v0.schema.json",
    "compiler_elaborated_graph": "compiler-elaborated-graph-v0.schema.json",
    "compiler_dependency": "compiler-dependency-plan-v0.schema.json",
    "compiler_resource": "compiler-resource-plan-v0.schema.json",
    "compiler_origin_map": "compiler-origin-map-v0.schema.json",
    "compiler_dependency_facts": "compiler-dependency-facts-v0.schema.json",
    "operation_request_v4": "operation-request-v4.schema.json",
    "operation_result_v4": "operation-result-v4.schema.json",
}

TASK014_SCHEMA_NAMES = {
    "build_handler_descriptor": "build-handler-descriptor-v0.schema.json",
    "build_execution_result": "build-execution-result-v0.schema.json",
    "operation_request_v5": "operation-request-v5.schema.json",
    "operation_result_v5": "operation-result-v5.schema.json",
}

TASK015_SCHEMA_NAMES = {
    "normalized_dsp_module": "normalized-dsp-module-v0.schema.json",
    "direct_frontend_result": "direct-frontend-result-v0.schema.json",
}

TASK016_SCHEMA_NAMES = {
    "direct_operation_spec": "direct-operation-spec-v0.schema.json",
    "normalized_dsp_module_v1": "normalized-dsp-module-v1.schema.json",
    "direct_frontend_result_v1": "direct-frontend-result-v1.schema.json",
}

DOMAIN_GROUPS = (
    "catalog",
    "families",
    "contracts",
    "bindings",
    "graphs",
    "devices",
    "instruments",
    "direct_operation_specs",
    *tuple(target.SCHEMA_SPECS),
)


def _stable_records(values: Iterable[dict[str, Any]]) -> tuple[dict[str, Any], ...]:
    return tuple(
        copy.deepcopy(item)
        for item in sorted(values, key=lambda item: core.canonical_json(item))
    )


@dataclass(frozen=True)
class OperationContext:
    """Immutable-by-contract in-memory snapshot used by every Task 008 client."""

    records: Mapping[str, tuple[dict[str, Any], ...]]
    schemas: Mapping[str, dict[str, Any]]
    overlay: dict[str, Any]
    overlay_sha256: str
    manifest_sha256: str
    observations: Mapping[str, dict[str, Any]]
    device_summary: dict[str, Any]
    component_summary: dict[str, Any]
    task006_summary: dict[str, Any]
    task007_summary: dict[str, Any]
    record_set_reference: dict[str, Any]
    catalog_projection: dict[str, Any] | None

    def with_records(
        self, **groups: Iterable[dict[str, Any]]
    ) -> "OperationContext":
        """Return an isolated fixture context; cached summaries remain explicit inputs."""

        unknown = sorted(set(groups) - set(DOMAIN_GROUPS))
        if unknown:
            raise ValueError(f"unknown operation-context record groups {unknown}")
        updated = {
            name: _stable_records(values)
            for name, values in self.records.items()
        }
        for name, values in groups.items():
            updated[name] = _stable_records(values)
        return replace(self, records=updated)


def load_repository_context(
    repository_root: Path = REPOSITORY_ROOT,
    record_enumerator: Callable[[Path, str], Iterable[Path]] | None = None,
    record_set_path: Path = record_set_rules.ACCEPTED_RECORD_SET,
    parent_record_set_path: Path | None = None,
) -> OperationContext:
    """Read and validate one accepted repository snapshot before dispatch."""

    repository_root = repository_root.resolve()
    schema_root = repository_root / "schemas"
    contract_root = repository_root / "contracts"
    overlay_path = repository_root / component.OVERLAY_RELATIVE_PATH
    snapshot_root = repository_root / component.SNAPSHOT_RELATIVE_PATH
    manifest_path = snapshot_root / "manifest.json"

    selected = record_set_rules.load_record_set(
        repository_root,
        record_set_path,
        accepted_manifest_path=parent_record_set_path,
    )

    catalog_records = _stable_records(selected.records.get("catalog-corpus", ()))
    catalog_selectors = _stable_records(selected.records.get("catalog-selection", ()))
    if catalog_selectors:
        if len(catalog_selectors) != 1:
            raise ValueError("selected record set must contain exactly one catalog selector")
        reference = catalog_selectors[0]["corpus_reference"]
        matches = [
            record
            for record in catalog_records
            if record["catalog_id"] == reference["catalog_id"]
            and record["revision"] == reference["revision"]
            and record["content_hash"] == reference["content_hash"]
        ]
        if len(matches) != 1:
            raise ValueError("catalog selector must resolve exactly one corpus")
        catalog_records = _stable_records(matches)
    elif len(catalog_records) > 1:
        raise ValueError("multiple catalog corpora require one exact catalog selector")
    if record_enumerator is not None:
        known_directories = {
            member["portable_path"].split("/")[1]
            for member in selected.manifest["record_members"]
            if member["portable_path"].startswith("contracts/")
            and len(member["portable_path"].split("/")) == 3
        }
        for child in sorted(known_directories):
            actual = {
                Path(path).resolve()
                for path in record_enumerator(contract_root, child)
            }
            expected = {
                (repository_root / member["portable_path"]).resolve()
                for member in selected.manifest["record_members"]
                if member["portable_path"].startswith(f"contracts/{child}/")
            }
            if actual != expected:
                raise ValueError(
                    f"custom record enumerator changes explicit record-set membership for {child}"
                )

    records: dict[str, tuple[dict[str, Any], ...]] = {
        "catalog": catalog_records,
        "families": _stable_records(selected.records.get("catalog-family", ())),
        "contracts": _stable_records(selected.records.get("component-contract", ())),
        "bindings": _stable_records(selected.records.get("implementation-binding", ())),
        "graphs": _stable_records(selected.records.get("dsp-graph", ())),
        "devices": _stable_records(selected.records.get("device-profile", ())),
        "instruments": _stable_records(selected.records.get("instrument", ())),
    }
    target_records = {
        kind: list(selected.records.get(kind, ()))
        for kind in target.SCHEMA_SPECS
    }
    records.update(
        {name: _stable_records(values) for name, values in target_records.items()}
    )
    if selected.records.get("direct-operation-spec"):
        records["direct_operation_specs"] = _stable_records(
            selected.records["direct-operation-spec"]
        )

    schemas: dict[str, dict[str, Any]] = {
        "operation_request": selected.schemas["operation-request-v1"],
        "operation_result": selected.schemas["operation-result-v1"],
        "operation_request_v1": selected.schemas["operation-request-v1"],
        "operation_result_v1": selected.schemas["operation-result-v1"],
        "device": selected.schemas[device.DEVICE_SCHEMA_VERSION],
        "instrument": selected.schemas[device.INSTRUMENT_SCHEMA_VERSION],
        "family": selected.schemas[component.FAMILY_SCHEMA_VERSION],
        "contract": selected.schemas[component.CONTRACT_SCHEMA_VERSION],
        "binding": selected.schemas[component.BINDING_SCHEMA_VERSION],
        "graph": selected.schemas[component.GRAPH_SCHEMA_VERSION],
        **{
            kind: selected.schemas[specification[1]]
            for kind, specification in target.SCHEMA_SPECS.items()
        },
    }
    contract_versions = {
        version: selected.schemas[version]
        for version in component.CONTRACT_SCHEMA_VERSIONS
        if version in selected.schemas
    }
    schemas["contract_versions"] = contract_versions
    binding_versions = {
        version: selected.schemas[version]
        for version in component.BINDING_SCHEMA_VERSIONS
        if version in selected.schemas
    }
    schemas["binding_versions"] = binding_versions
    for version, name in (
        ("operation-request-v2", "operation_request_v2"),
        ("operation-result-v2", "operation_result_v2"),
        ("catalog-corpus-v1", "catalog_corpus"),
        ("catalog-projection-v1", "catalog_projection"),
    ):
        if version in selected.schemas:
            schemas[name] = selected.schemas[version]
    if records["catalog"]:
        catalog_schema_version = records["catalog"][0]["schema_version"]
        if catalog_schema_version not in selected.schemas:
            raise ValueError("selected catalog corpus schema is absent")
        schemas["catalog_corpus"] = selected.schemas[catalog_schema_version]
        if catalog_schema_version == "catalog-corpus-v2":
            if "catalog-projection-v2" not in selected.schemas:
                raise ValueError("selected catalog corpus v2 requires projection schema v2")
            schemas["catalog_projection"] = selected.schemas["catalog-projection-v2"]
    for key, filename in TASK013_SCHEMA_NAMES.items():
        version = filename.removesuffix(".schema.json")
        if version in selected.schemas:
            schemas[key] = selected.schemas[version]
    for key, filename in TASK014_SCHEMA_NAMES.items():
        version = filename.removesuffix(".schema.json")
        if version in selected.schemas:
            schemas[key] = selected.schemas[version]
    for key, filename in TASK015_SCHEMA_NAMES.items():
        version = filename.removesuffix(".schema.json")
        if version in selected.schemas:
            schemas[key] = selected.schemas[version]
    for key, filename in TASK016_SCHEMA_NAMES.items():
        version = filename.removesuffix(".schema.json")
        if version in selected.schemas:
            schemas[key] = selected.schemas[version]

    overlay = core.load_json(overlay_path)
    observations = component._observations(snapshot_root)

    derived_catalog = None
    catalog_family_references: list[dict[str, Any]] = []
    catalog_implementations: list[dict[str, Any]] = []
    if records["catalog"]:
        if len(records["catalog"]) != 1:
            raise ValueError("selected record set must contain exactly one catalog corpus")
        required_catalog_schemas = {
            "catalog_corpus",
            "catalog_projection",
            "operation_request_v2",
            "operation_result_v2",
        }
        missing = sorted(required_catalog_schemas - set(schemas))
        if missing:
            raise ValueError(f"catalog record set is missing schemas {missing}")
        corpus = records["catalog"][0]
        derived_catalog = catalog.build_catalog_projection(
            corpus=copy.deepcopy(corpus),
            corpus_schema=schemas["catalog_corpus"],
            projection_schema=schemas["catalog_projection"],
            overlay=copy.deepcopy(overlay),
            overlay_sha256=core.sha256_file(overlay_path),
            observations=copy.deepcopy(observations),
            records=records,
            record_set_reference=copy.deepcopy(selected.reference),
            core=core,
        )
        exact_family_ids = {family["family_id"] for family in records["families"]}
        referenced_family_ids = {
            contract["family_reference"]["family_id"]
            for contract in records["contracts"]
        }
        catalog_family_references = [
            copy.deepcopy(entry["family_reference"])
            for entry in derived_catalog["families"]
            if entry["family_reference"]["family_id"] in referenced_family_ids
            and entry["family_reference"]["family_id"] not in exact_family_ids
        ]
        overlay_implementation_ids = {
            item["implementation_id"] for item in overlay["implementations"]
        }
        bound_implementation_ids = {
            binding["implementation_id"] for binding in records["bindings"]
        }
        catalog_implementations = [
            copy.deepcopy(item)
            for item in corpus["implementation_additions"]
            if item["implementation_id"] in bound_implementation_ids
            and item["implementation_id"] not in overlay_implementation_ids
        ]

    component_result = component.validate_component_graph_values(
        list(records["families"]),
        list(records["contracts"]),
        list(records["bindings"]),
        list(records["graphs"]),
        {
            kind: schemas[kind]
            for kind in (
                "family",
                "contract",
                "contract_versions",
                "binding",
                "binding_versions",
                "graph",
            )
        },
        overlay,
        core.sha256_file(overlay_path),
        core.sha256_file(manifest_path),
        observations,
        additional_family_references=catalog_family_references,
        additional_implementations=catalog_implementations,
    )
    device_summary = device.validate_contract_values(
        list(records["devices"]),
        list(records["instruments"]),
        schemas["device"],
        schemas["instrument"],
        component_result.graph_targets,
    )
    task006_summary = aggregate.combine_task006_summaries(
        component_result.summary,
        device_summary,
        len(records["devices"]),
        len(records["instruments"]),
    )
    task007_result = target.validate_target_backend_build_values(
        {kind: list(records[kind]) for kind in target.SCHEMA_SPECS},
        {kind: schemas[kind] for kind in target.SCHEMA_SPECS},
        {
            "families": list(records["families"]),
            "contracts": list(records["contracts"]),
            "bindings": list(records["bindings"]),
            "graphs": list(records["graphs"]),
            "devices": list(records["devices"]),
            "instruments": list(records["instruments"]),
        },
        repository_root,
        task006_summary,
        additional_semantic_records=[
            copy.deepcopy(record)
            for kind in (
                "conformance-probe-evidence",
                "conformance-probe-input",
                "conformance-probe-result",
                "conformance-probe-procedure",
                "prerequisite-environment",
                "direct-operation-spec",
            )
            for record in selected.records.get(kind, ())
        ],
    )
    return OperationContext(
        records=records,
        schemas=schemas,
        overlay=overlay,
        overlay_sha256=core.sha256_file(overlay_path),
        manifest_sha256=core.sha256_file(manifest_path),
        observations=observations,
        device_summary=copy.deepcopy(device_summary),
        component_summary=copy.deepcopy(component_result.summary),
        task006_summary=copy.deepcopy(task006_summary),
        task007_summary=copy.deepcopy(task007_result.summary),
        record_set_reference=copy.deepcopy(selected.reference),
        catalog_projection=derived_catalog,
    )


def with_compiler_schemas(
    context: OperationContext,
    repository_root: Path = REPOSITORY_ROOT,
) -> OperationContext:
    """Add the Task 013 protocol/artifact schemas without changing records."""

    schemas = dict(context.schemas)
    schema_root = Path(repository_root) / "schemas"
    for key, filename in TASK013_SCHEMA_NAMES.items():
        if key in schemas:
            continue
        schema = core.load_json(schema_root / filename)
        annotations = core.validate_schema_annotations(schema)
        if annotations:
            raise ValueError(f"Task 013 schema {filename} is invalid: {annotations}")
        schemas[key] = schema
    return replace(context, schemas=schemas)


def _diagnostic(
    code: str,
    subject: str,
    location: str,
    message: str,
) -> dict[str, str]:
    return core.Diagnostic(code, "error", subject, location, message).as_dict()


def _result(
    operation: str,
    status: str,
    value: dict[str, Any] | None,
    diagnostics: Iterable[dict[str, str] | core.Diagnostic] = (),
    *,
    version: int = 1,
) -> dict[str, Any]:
    normalized = [
        item.as_dict() if isinstance(item, core.Diagnostic) else copy.deepcopy(item)
        for item in diagnostics
    ]
    normalized.sort(key=core.diagnostic_sort_key)
    return {
        "schema_version": f"schuss-operation-result-v{version}",
        "canonical_profile": "schuss-canonical-json-v1",
        "operation": operation,
        "status": status,
        "value": copy.deepcopy(value),
        "diagnostics": normalized,
    }


def canonical_result_bytes(
    result: dict[str, Any], context: OperationContext
) -> bytes:
    result_schema_name = {
        "schuss-operation-result-v1": "operation_result_v1",
        "schuss-operation-result-v2": "operation_result_v2",
        "schuss-operation-result-v3": "operation_result_v3",
        "schuss-operation-result-v4": "operation_result_v4",
        "schuss-operation-result-v5": "operation_result_v5",
    }.get(result.get("schema_version"))
    if result_schema_name is None or result_schema_name not in context.schemas:
        raise ValueError("operation result uses an unavailable public schema")
    result_schema = context.schemas[result_schema_name]
    errors = core.schema_errors(
        result,
        result_schema,
        result_schema,
    )
    if errors:
        raise ValueError(f"operation result violates its public schema: {errors}")
    return core.canonical_json(result).encode("utf-8")


def _catalog_unavailable(operation: str) -> dict[str, Any]:
    return _result(
        operation,
        "invalid",
        None,
        [
            _diagnostic(
                "CATALOG_CONTEXT_UNAVAILABLE",
                operation,
                "$",
                "the selected record set contains no exact Task 011A catalog corpus",
            )
        ],
        version=2,
    )


def _catalog_search(
    payload: dict[str, Any], context: OperationContext
) -> dict[str, Any]:
    projection = context.catalog_projection
    if projection is None:
        return _catalog_unavailable("catalog.search")
    normalized_filters = catalog.canonical_filters(payload["filters"])
    invalid = catalog.validate_filter_values(projection, normalized_filters)
    if invalid:
        return _result(
            "catalog.search",
            "invalid",
            None,
            [
                _diagnostic(
                    "CATALOG_FILTER_VALUE_UNSUPPORTED",
                    f"{name}:{value}",
                    f"$.payload.filters.{name}",
                    "the filter value is absent from the exact selected catalog projection",
                )
                for name, value in invalid
            ],
            version=2,
        )
    query, filters, results = catalog.search_catalog(
        projection, payload["query"], normalized_filters
    )
    return _result(
        "catalog.search",
        "success",
        {
            "record_set_reference": copy.deepcopy(
                projection["record_set_reference"]
            ),
            "catalog_reference": copy.deepcopy(projection["catalog_reference"]),
            "projection_version": projection["projection_version"],
            "match_algorithm": projection["match_algorithm"],
            "input_closure_hash": projection["input_closure_hash"],
            "query": query,
            "filters": filters,
            "total_matches": len(results),
            "results": results,
        },
        version=2,
    )


def _catalog_inspect(
    payload: dict[str, Any], context: OperationContext
) -> dict[str, Any]:
    projection = context.catalog_projection
    if projection is None:
        return _catalog_unavailable("catalog.inspect")
    family = catalog.inspect_family(projection, payload["family_reference"])
    if family is None:
        reference = payload["family_reference"]
        return _result(
            "catalog.inspect",
            "invalid",
            None,
            [
                _diagnostic(
                    "OPERATION_REFERENCE_UNRESOLVED",
                    f"{reference['family_id']}@{reference['revision']}",
                    "$.payload.family_reference",
                    "the exact family reference is absent from the selected catalog projection",
                )
            ],
            version=2,
        )
    return _result(
        "catalog.inspect",
        "success",
        {
            "record_set_reference": copy.deepcopy(
                projection["record_set_reference"]
            ),
            "catalog_reference": copy.deepcopy(projection["catalog_reference"]),
            "projection_version": projection["projection_version"],
            "match_algorithm": projection["match_algorithm"],
            "input_closure_hash": projection["input_closure_hash"],
            "family": family,
        },
        version=2,
    )


def _exact_registry(
    values: Iterable[dict[str, Any]], id_field: str
) -> dict[tuple[str, int, str], dict[str, Any]]:
    return {
        core.exact_key(item, id_field): item
        for item in sorted(values, key=lambda item: core.canonical_json(item))
    }


def _records_validate(context: OperationContext) -> dict[str, Any]:
    summaries = {
        "device_instrument_rules": copy.deepcopy(context.device_summary),
        "component_graph_rules": copy.deepcopy(context.component_summary),
        "target_backend_build_rules": copy.deepcopy(context.task007_summary),
        "aggregate_validator": copy.deepcopy(context.task006_summary),
    }
    invalid = any(
        summary.get("status") == "invalid" for summary in summaries.values()
    )
    diagnostics: list[dict[str, str]] = []
    for summary in summaries.values():
        diagnostics.extend(summary.get("diagnostics", []))
    return _result(
        "records.validate",
        "invalid" if invalid else "success",
        {"summaries": summaries},
        diagnostics,
    )


def _graph_inspect(payload: dict[str, Any], context: OperationContext) -> dict[str, Any]:
    graph_ref = payload["graph_reference"]
    graphs = _exact_registry(context.records["graphs"], "graph_id")
    graph = graphs.get(core.reference_key(graph_ref, "graph_id"))
    if graph is None:
        return _result(
            "graph.inspect",
            "invalid",
            None,
            [
                _diagnostic(
                    "OPERATION_REFERENCE_UNRESOLVED",
                    f"{graph_ref['graph_id']}@{graph_ref['revision']}",
                    "$.payload.graph_reference",
                    "the exact graph reference is absent from the operation context",
                )
            ],
        )

    contracts = _exact_registry(
        context.records["contracts"], "component_contract_id"
    )
    closure: list[dict[str, Any]] = []
    diagnostics: list[dict[str, str]] = []
    for node in sorted(graph["nodes"], key=lambda item: item["node_id"]):
        reference = node["contract_reference"]
        contract = contracts.get(
            core.reference_key(reference, "component_contract_id")
        )
        if contract is None:
            diagnostics.append(
                _diagnostic(
                    "OPERATION_REFERENCE_UNRESOLVED",
                    f"{graph['graph_id']}@{graph['revision']}",
                    f"$.nodes.{node['node_id']}.contract_reference",
                    "the node's exact component contract is absent",
                )
            )
        else:
            closure.append(copy.deepcopy(contract))
    if diagnostics:
        return _result("graph.inspect", "invalid", None, diagnostics)

    unique_contracts = {
        core.exact_key(item, "component_contract_id"): item for item in closure
    }
    value = {
        "graph": copy.deepcopy(graph),
        "component_contract_closure": [
            copy.deepcopy(unique_contracts[key]) for key in sorted(unique_contracts)
        ],
        "selection_status": "not-evaluated",
        "lowering_status": "not-run",
    }
    return _result("graph.inspect", "success", value)


def _validate_build_resolution_context(
    context: OperationContext,
) -> tuple[
    dict[str, list[dict[str, Any]]],
    dict[str, dict[tuple[str, int, str], dict[str, Any]]],
    dict[str, dict[str, Any]],
    tuple[core.Diagnostic, ...],
]:
    loaded = {
        kind: [copy.deepcopy(item) for item in context.records[kind]]
        for kind in target.SCHEMA_SPECS
    }
    diagnostics: list[core.Diagnostic] = []
    target_schemas = {
        kind: context.schemas[kind] for kind in target.SCHEMA_SPECS
    }
    valid = target._validate_structural(loaded, target_schemas, diagnostics)

    contracts = _exact_registry(
        context.records["contracts"], "component_contract_id"
    )
    bindings = _exact_registry(context.records["bindings"], "implementation_id")
    graphs = _exact_registry(context.records["graphs"], "graph_id")
    instruments = _exact_registry(context.records["instruments"], "instrument_id")
    capability_registry, definitions = target._capability_definitions(
        valid["capability"], diagnostics
    )
    environments = target._validate_environments(valid["environment"], diagnostics)
    targets = target._validate_targets(
        valid["target"],
        capability_registry,
        definitions,
        environments,
        diagnostics,
    )
    backends = target._validate_backends(
        valid["backend"],
        capability_registry,
        definitions,
        targets,
        environments,
        diagnostics,
    )
    evidence = _exact_registry(valid["evidence"], "evidence_claim_id")
    eligibility = target._validate_eligibility_records(
        valid["eligibility"],
        bindings,
        contracts,
        targets,
        backends,
        definitions,
        evidence,
        diagnostics,
    )
    requests = target._validate_build_requests(
        valid["request"],
        graphs,
        instruments,
        targets,
        backends,
        diagnostics,
    )
    registries = {
        "bindings": bindings,
        "graphs": graphs,
        "targets": targets,
        "backends": backends,
        "eligibility": eligibility,
        "requests": requests,
    }
    ordered = tuple(sorted(set(diagnostics), key=core.diagnostic_sort_key))
    return valid, registries, definitions, ordered


def _prepare_backend_invocation(
    request: dict[str, Any], traces: tuple[dict[str, Any], ...]
) -> dict[str, Any]:
    """Create the Task 009 data seam; no executable handler exists here."""

    return {
        "schema_version": "schuss-backend-invocation-input-v1",
        "status": "ready-for-backend-invocation",
        "accepted_build_request": copy.deepcopy(request),
        "resolution_traces": copy.deepcopy(list(traces)),
        "selected_bindings": [
            {
                "node_id": trace["node_id"],
                "binding_reference": copy.deepcopy(
                    trace["selected_binding_reference"]
                ),
            }
            for trace in traces
        ],
        "boundary": {
            "completed_stage": "implementation-resolution",
            "next_stage": "backend-lowering",
            "next_stage_status": "not-run",
            "executable_handler_status": "absent",
        },
    }


def _build_resolve(payload: dict[str, Any], context: OperationContext) -> dict[str, Any]:
    _, registries, definitions, diagnostics = _validate_build_resolution_context(
        context
    )
    request_ref = payload["build_request_reference"]
    request = registries["requests"].get(
        core.reference_key(request_ref, "build_request_id")
    )
    if diagnostics or request is None:
        values = list(diagnostics)
        if request is None:
            values.append(
                core.Diagnostic(
                    "OPERATION_REFERENCE_UNRESOLVED",
                    f"{request_ref['build_request_id']}@{request_ref['revision']}",
                    "$.payload.build_request_reference",
                    "the exact accepted build request is absent",
                )
            )
        return _result("build.resolve", "invalid", None, values)

    graph = registries["graphs"][
        core.reference_key(request["graph_reference"], "graph_id")
    ]
    target_record = registries["targets"][
        core.reference_key(request["compute_target_reference"], "compute_target_id")
    ]
    backend = registries["backends"][
        core.reference_key(request["backend_reference"], "backend_id")
    ]
    graph_for_resolution = copy.deepcopy(graph)
    graph_for_resolution["nodes"] = sorted(
        graph_for_resolution["nodes"], key=lambda item: item["node_id"]
    )
    traces = target.resolve_graph_bindings(
        graph_for_resolution,
        target_record,
        backend,
        registries["eligibility"].values(),
        registries["bindings"],
        definitions,
        request["binding_overrides"],
    )
    statuses = {trace["status"] for trace in traces}
    if statuses == {"selected"}:
        status = "success"
    elif "invalid-override" in statuses:
        status = "invalid"
    elif "ambiguous" in statuses:
        status = "ambiguous"
    elif "unresolved" in statuses:
        status = "unresolved"
    else:
        status = "unsupported"

    value = {
        "build_request_reference": copy.deepcopy(request_ref),
        "resolution_traces": copy.deepcopy(list(traces)),
        "backend_invocation": (
            _prepare_backend_invocation(request, traces)
            if status == "success"
            else None
        ),
    }
    return _result("build.resolve", status, value)


def _build_plan(
    payload: dict[str, Any],
    context: OperationContext,
    closure_source: dict[str, Any],
) -> dict[str, Any]:
    compilation_context = compiler.CompilationContext.from_values(
        build_request_reference=payload["build_request_reference"],
        closure_source=closure_source,
        records=context.records,
        schemas=context.schemas,
    )
    plan = compiler.plan_build(compilation_context)
    return _result(
        "build.plan",
        plan["status"],
        plan,
        compiler.operation_diagnostics(plan),
        version=4,
    )


def _dispatch_compiler_operation(
    request: dict[str, Any],
    context: OperationContext,
    closure_source: dict[str, Any],
) -> dict[str, Any]:
    operation = request.get("operation") if isinstance(request, dict) else None
    errors: list[str] = []
    try:
        core.assert_portable_json_value(request)
    except ValueError as exc:
        errors.append(str(exc))
    schema = context.schemas.get("operation_request_v4")
    if schema is None:
        errors.append("$: operation schema 'schuss-operation-request-v4' is unavailable in the selected context")
    elif isinstance(request, dict):
        errors.extend(core.schema_errors(request, schema, schema))
    else:
        errors.append("$: operation request must be an object")
    if errors:
        result_version = 4 if "operation_result_v4" in context.schemas else 1
        result = _result(
            (
                operation
                if result_version == 4 and operation == "build.plan"
                else "invalid-request"
            ),
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
            version=result_version,
        )
        canonical_result_bytes(result, context)
        return result
    result = _build_plan(request["payload"], context, closure_source)
    canonical_result_bytes(result, context)
    return result


def _dispatch_execution_operation(
    request: dict[str, Any],
    context: OperationContext,
    closure_source: dict[str, Any],
    execution_service: execution.ExecutionService | None,
) -> dict[str, Any]:
    operation = request.get("operation") if isinstance(request, dict) else None
    errors: list[str] = []
    try:
        core.assert_portable_json_value(request)
    except ValueError as exc:
        errors.append(str(exc))
    schema = context.schemas.get("operation_request_v5")
    if schema is None:
        errors.append("$: operation schema 'schuss-operation-request-v5' is unavailable in the selected context")
    elif isinstance(request, dict):
        errors.extend(core.schema_errors(request, schema, schema))
    else:
        errors.append("$: operation request must be an object")
    if errors:
        result_version = 5 if "operation_result_v5" in context.schemas else 1
        result = _result(
            (
                operation
                if result_version == 5 and operation == "build.execute"
                else "invalid-request"
            ),
            "invalid",
            None,
            [_diagnostic("OPERATION_REQUEST_INVALID", operation if isinstance(operation, str) else "invalid-request", "$", error) for error in sorted(set(errors))],
            version=result_version,
        )
        canonical_result_bytes(result, context)
        return result
    compilation_context = compiler.CompilationContext.from_values(
        build_request_reference=request["payload"]["build_request_reference"],
        closure_source=closure_source,
        records=context.records,
        schemas=context.schemas,
    )
    service = execution_service or execution.ExecutionService.from_values((), Path("."))
    value = execution.execute_build(
        compilation_context,
        request["payload"]["handler_reference"],
        service,
        execution_intent=request["payload"]["execution_intent"],
    )
    value_schema = context.schemas["build_execution_result"]
    value_errors = core.schema_errors(value, value_schema, value_schema)
    if value_errors:
        raise ValueError(f"build execution result violates its public schema: {value_errors}")
    diagnostics = [
        _diagnostic(
            item["code"], item["subject"], f"$.value.{item['stage']}", item["message"]
        )
        for item in value["diagnostics"]
    ]
    result = _result("build.execute", value["status"], value, diagnostics, version=5)
    canonical_result_bytes(result, context)
    return result


class _TransactionEditError(ValueError):
    pass


def _find_unique(
    values: list[dict[str, Any]], field: str, identifier: str
) -> dict[str, Any]:
    matches = [item for item in values if item.get(field) == identifier]
    if len(matches) != 1:
        raise _TransactionEditError(
            f"expected exactly one {field}={identifier!r}, found {len(matches)}"
        )
    return matches[0]


def _apply_edit(graph: dict[str, Any], edit: dict[str, Any]) -> None:
    kind = edit["edit"]
    if kind == "add-node":
        identifier = edit["node"]["node_id"]
        if any(item["node_id"] == identifier for item in graph["nodes"]):
            raise _TransactionEditError(f"node {identifier!r} already exists")
        graph["nodes"].append(copy.deepcopy(edit["node"]))
    elif kind == "remove-node":
        node = _find_unique(graph["nodes"], "node_id", edit["node_id"])
        graph["nodes"].remove(node)
    elif kind == "add-connection":
        identifier = edit["connection"]["connection_id"]
        if any(
            item["connection_id"] == identifier for item in graph["connections"]
        ):
            raise _TransactionEditError(f"connection {identifier!r} already exists")
        graph["connections"].append(copy.deepcopy(edit["connection"]))
    elif kind == "remove-connection":
        connection = _find_unique(
            graph["connections"], "connection_id", edit["connection_id"]
        )
        graph["connections"].remove(connection)
    elif kind in {"set-node-parameter", "set-node-attribute"}:
        node = _find_unique(graph["nodes"], "node_id", edit["node_id"])
        values_key = (
            "parameter_values"
            if kind == "set-node-parameter"
            else "attribute_values"
        )
        values = node[values_key]
        matches = [item for item in values if item["facet_id"] == edit["facet_id"]]
        if len(matches) > 1:
            raise _TransactionEditError(
                f"facet {edit['facet_id']!r} is not unique on node {edit['node_id']!r}"
            )
        replacement = {"facet_id": edit["facet_id"], "value": edit["value"]}
        if matches:
            values[values.index(matches[0])] = replacement
        else:
            values.append(replacement)
    else:
        raise _TransactionEditError(f"unsupported graph edit {kind!r}")


def _validate_transacted_graph(
    candidate: dict[str, Any], context: OperationContext
) -> tuple[component.CoreValidation, dict[str, Any]]:
    graphs = [copy.deepcopy(item) for item in context.records["graphs"]]
    graphs.append(copy.deepcopy(candidate))
    additional_family_references: list[dict[str, Any]] = []
    additional_implementations: list[dict[str, Any]] = []
    if context.catalog_projection is not None:
        exact_family_ids = {
            item["family_id"] for item in context.records["families"]
        }
        referenced_family_ids = {
            item["family_reference"]["family_id"]
            for item in context.records["contracts"]
        }
        additional_family_references = [
            copy.deepcopy(item["family_reference"])
            for item in context.catalog_projection["families"]
            if item["family_reference"]["family_id"] in referenced_family_ids
            and item["family_reference"]["family_id"] not in exact_family_ids
        ]
        overlay_implementation_ids = {
            item["implementation_id"] for item in context.overlay["implementations"]
        }
        bound_implementation_ids = {
            item["implementation_id"] for item in context.records["bindings"]
        }
        corpus = context.records["catalog"][0]
        additional_implementations = [
            copy.deepcopy(item)
            for item in corpus["implementation_additions"]
            if item["implementation_id"] in bound_implementation_ids
            and item["implementation_id"] not in overlay_implementation_ids
        ]
    component_result = component.validate_component_graph_values(
        list(copy.deepcopy(context.records["families"])),
        list(copy.deepcopy(context.records["contracts"])),
        list(copy.deepcopy(context.records["bindings"])),
        graphs,
        {
            "family": context.schemas["family"],
            "contract": context.schemas["contract"],
            "contract_versions": context.schemas["contract_versions"],
            "binding": context.schemas["binding"],
            "binding_versions": context.schemas["binding_versions"],
            "graph": context.schemas["graph"],
        },
        copy.deepcopy(context.overlay),
        context.overlay_sha256,
        context.manifest_sha256,
        copy.deepcopy(dict(context.observations)),
        additional_family_references=additional_family_references,
        additional_implementations=additional_implementations,
    )
    device_summary = device.validate_contract_values(
        list(copy.deepcopy(context.records["devices"])),
        list(copy.deepcopy(context.records["instruments"])),
        context.schemas["device"],
        context.schemas["instrument"],
        component_result.graph_targets,
    )
    return component_result, device_summary


def _graph_transact(payload: dict[str, Any], context: OperationContext) -> dict[str, Any]:
    graph_ref = payload["graph_reference"]
    graph = _exact_registry(context.records["graphs"], "graph_id").get(
        core.reference_key(graph_ref, "graph_id")
    )
    if graph is None or payload["base_content_hash"] != graph.get("content_hash"):
        return _result(
            "graph.transact",
            "conflict",
            None,
            [
                _diagnostic(
                    "OPERATION_BASE_HASH_STALE",
                    f"{graph_ref['graph_id']}@{graph_ref['revision']}",
                    "$.payload.base_content_hash",
                    "the transaction base does not match the exact current graph",
                )
            ],
        )

    candidate = copy.deepcopy(graph)
    try:
        for index, edit in enumerate(payload["edits"]):
            try:
                _apply_edit(candidate, edit)
            except _TransactionEditError as exc:
                raise _TransactionEditError(f"edit {index}: {exc}") from exc
    except _TransactionEditError as exc:
        return _result(
            "graph.transact",
            "invalid",
            None,
            [
                _diagnostic(
                    "OPERATION_EDIT_INVALID",
                    f"{graph_ref['graph_id']}@{graph_ref['revision']}",
                    "$.payload.edits",
                    str(exc),
                )
            ],
        )

    candidate["revision"] = graph["revision"] + 1
    candidate["content_hash"] = core.record_content_hash(
        candidate, context.schemas["graph"]
    )
    component_result, device_summary = _validate_transacted_graph(candidate, context)
    diagnostics = list(component_result.summary["diagnostics"]) + list(
        device_summary["diagnostics"]
    )
    if diagnostics:
        return _result(
            "graph.transact",
            "invalid",
            None,
            diagnostics,
        )
    return _result(
        "graph.transact",
        "success",
        {
            "proposed_graph": candidate,
            "validation": {
                "component_graph": component_result.summary,
                "device_instrument": device_summary,
            },
            "persistence_status": "not-written",
        },
    )


def dispatch_operation(
    request: dict[str, Any],
    context: OperationContext,
    *,
    project_service: Any | None = None,
    execution_service: execution.ExecutionService | None = None,
) -> dict[str, Any]:
    """Dispatch one parsed request through the public pure operation API."""

    if (
        isinstance(request, dict)
        and request.get("schema_version") == "schuss-operation-request-v5"
    ):
        if project_service is not None:
            loaded = project_service.load()
            project_context = with_compiler_schemas(
                loaded.context, project_service.repository_root
            )
            return _dispatch_execution_operation(
                request,
                project_context,
                {
                    "kind": "project",
                    "project_reference": {
                        "project_id": loaded.manifest["project_id"],
                        "revision": loaded.manifest["revision"],
                        "content_hash": loaded.manifest["content_hash"],
                    },
                    "base_record_set_reference": copy.deepcopy(
                        loaded.context.record_set_reference
                    ),
                },
                execution_service,
            )
        return _dispatch_execution_operation(
            request,
            context,
            {
                "kind": "record-set",
                "record_set_reference": copy.deepcopy(context.record_set_reference),
            },
            execution_service,
        )

    if (
        isinstance(request, dict)
        and request.get("schema_version") == "schuss-operation-request-v4"
    ):
        if project_service is not None:
            loaded = project_service.load()
            project_context = with_compiler_schemas(
                loaded.context, project_service.repository_root
            )
            return _dispatch_compiler_operation(
                request,
                project_context,
                {
                    "kind": "project",
                    "project_reference": {
                        "project_id": loaded.manifest["project_id"],
                        "revision": loaded.manifest["revision"],
                        "content_hash": loaded.manifest["content_hash"],
                    },
                    "base_record_set_reference": copy.deepcopy(
                        loaded.context.record_set_reference
                    ),
                },
            )
        return _dispatch_compiler_operation(
            request,
            context,
            {
                "kind": "record-set",
                "record_set_reference": copy.deepcopy(
                    context.record_set_reference
                ),
            },
        )

    if (
        isinstance(request, dict)
        and request.get("schema_version") == "schuss-operation-request-v3"
    ):
        if project_service is None:
            raise ValueError("v3 project operations require an explicit project service")
        from .project_service import dispatch_project_operation

        return dispatch_project_operation(request, project_service)

    operation = request.get("operation") if isinstance(request, dict) else None
    request_version = (
        request.get("schema_version") if isinstance(request, dict) else None
    )
    is_v2 = request_version == "schuss-operation-request-v2"
    request_schema_name = "operation_request_v2" if is_v2 else "operation_request_v1"
    request_errors: list[str] = []
    try:
        core.assert_portable_json_value(request)
    except ValueError as exc:
        request_errors.append(str(exc))
    if isinstance(request, dict):
        if request_schema_name not in context.schemas:
            request_errors.append(
                f"$: operation schema {request_version!r} is unavailable in the selected context"
            )
        else:
            request_schema = context.schemas[request_schema_name]
            request_errors.extend(
                core.schema_errors(request, request_schema, request_schema)
            )
            if is_v2 and operation in {
                "records.validate",
                "graph.inspect",
                "build.resolve",
                "graph.transact",
            }:
                v1_request = copy.deepcopy(request)
                v1_request["schema_version"] = "schuss-operation-request-v1"
                request_errors.extend(
                    core.schema_errors(
                        v1_request,
                        context.schemas["operation_request_v1"],
                        context.schemas["operation_request_v1"],
                    )
                )
    else:
        request_errors.append("$: operation request must be an object")
    if request_errors:
        subject = operation if isinstance(operation, str) else "invalid-request"
        result_version = (
            2 if is_v2 and "operation_result_v2" in context.schemas else 1
        )
        result_operations = {
            "records.validate",
            "graph.inspect",
            "build.resolve",
            "graph.transact",
        }
        if result_version == 2:
            result_operations |= {"catalog.search", "catalog.inspect"}
        result = _result(
            operation if operation in result_operations else "invalid-request",
            "invalid",
            None,
            [
                _diagnostic(
                    "OPERATION_REQUEST_INVALID",
                    subject,
                    "$",
                    error,
                )
                for error in sorted(set(request_errors))
            ],
            version=result_version,
        )
        if result["schema_version"] == "schuss-operation-result-v2":
            canonical_result_bytes(result, context)
        return result

    handlers = {
        "records.validate": lambda payload: _records_validate(context),
        "graph.inspect": lambda payload: _graph_inspect(payload, context),
        "build.resolve": lambda payload: _build_resolve(payload, context),
        "graph.transact": lambda payload: _graph_transact(payload, context),
        "catalog.search": lambda payload: _catalog_search(payload, context),
        "catalog.inspect": lambda payload: _catalog_inspect(payload, context),
    }
    result = handlers[operation](request["payload"])
    if is_v2 and result["schema_version"] == "schuss-operation-result-v1":
        result["schema_version"] = "schuss-operation-result-v2"
    canonical_result_bytes(result, context)
    return result
