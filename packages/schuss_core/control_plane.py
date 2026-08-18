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
import gills_mapping_rules as gills
import machine_rules as machine
import record_set_rules
import target_backend_build_rules as target
import validator_core as core

from . import catalog_projection as catalog
from . import compiler_front_half as compiler
from . import build_execution as execution
from . import application_capabilities as application


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

TASK026A_SCHEMA_NAMES = {
    "build_handler_descriptor_v1": "build-handler-descriptor-v1.schema.json",
}

TASK026B_SCHEMA_NAMES = {
    "application_capability_description_v1": "application-capability-description-v1.schema.json",
    "operation_request_v8": "operation-request-v8.schema.json",
    "operation_result_v8": "operation-result-v8.schema.json",
}

TASK029_SCHEMA_NAMES = {
    "machine_source_review": "machine-source-review-v0.schema.json",
    "panel_layout": "panel-layout-v0.schema.json",
    "machine_presentation": "machine-presentation-v0.schema.json",
    "machine": "machine-v0.schema.json",
    "application_capability_description_v2": "application-capability-description-v2.schema.json",
    "operation_request_v9": "operation-request-v9.schema.json",
    "operation_result_v9": "operation-result-v9.schema.json",
}

TASK030_SCHEMA_NAMES = {
    "application_capability_description_v3": "application-capability-description-v3.schema.json",
    "operation_request_v10": "operation-request-v10.schema.json",
    "operation_result_v10": "operation-result-v10.schema.json",
}

DESKTOP_PATCHER_SCHEMA_NAMES = {
    "application_capability_description_v4": "application-capability-description-v4.schema.json",
    "operation_request_v11": "operation-request-v11.schema.json",
    "operation_result_v11": "operation-result-v11.schema.json",
}

DESKTOP_SESSION_SCHEMA_NAMES = {
    "application_capability_description_v5": "application-capability-description-v5.schema.json",
    "operation_request_v12": "operation-request-v12.schema.json",
    "operation_result_v12": "operation-result-v12.schema.json",
}

AI_SONIC_AUTHORING_SCHEMA_NAMES = {
    "application_capability_description_v6": "application-capability-description-v6.schema.json",
    "implementation_binding_v3": "implementation-binding-v3.schema.json",
    "native_kernel": "native-kernel-v0.schema.json",
    "operation_request_v13": "operation-request-v13.schema.json",
    "operation_result_v13": "operation-result-v13.schema.json",
    "project_object_definition": "project-object-definition-v0.schema.json",
    "project_v1": "project-v1.schema.json",
}

DESKTOP_WORKSPACE_SCHEMA_NAMES = {
    "application_capability_description_v7": "application-capability-description-v7.schema.json",
    "operation_request_v14": "operation-request-v14.schema.json",
    "operation_result_v14": "operation-result-v14.schema.json",
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

TASK018_SCHEMA_NAMES = {
    "panel_evidence": "gills-panel-evidence-v0.schema.json",
    "mapping_coverage": "gills-mapping-coverage-v0.schema.json",
    "runtime_realizations": "gills-runtime-realization-v0.schema.json",
    "operation_request_v6": "operation-request-v6.schema.json",
    "operation_result_v6": "operation-result-v6.schema.json",
}

TASK023_SCHEMA_NAMES = {
    "application_capability_description": "application-capability-description-v0.schema.json",
    "operation_request_v7": "operation-request-v7.schema.json",
    "operation_result_v7": "operation-result-v7.schema.json",
}

DOMAIN_GROUPS = (
    "catalog",
    "catalog_source_reviews",
    "families",
    "contracts",
    "bindings",
    "graphs",
    "devices",
    "instruments",
    "panel_evidence",
    "mapping_coverage",
    "runtime_realizations",
    "machine_source_reviews",
    "panel_layouts",
    "machine_presentations",
    "machines",
    "direct_operation_specs",
    "selection_packets",
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
    task018_summary: dict[str, Any]
    machine_summary: dict[str, Any]
    record_set_reference: dict[str, Any]
    catalog_projection: dict[str, Any] | None
    loaded_record_set: record_set_rules.LoadedRecordSet
    record_set_path: Path
    additional_family_references: tuple[dict[str, Any], ...] = ()

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
        selector_ids = {item["catalog_selection_id"] for item in catalog_selectors}
        if len(selector_ids) != 1:
            raise ValueError("selected record set contains competing catalog selectors")
        selected_revision = max(item["revision"] for item in catalog_selectors)
        current_selectors = [
            item for item in catalog_selectors if item["revision"] == selected_revision
        ]
        if len(current_selectors) != 1:
            raise ValueError("selected record set has an ambiguous catalog selector revision")
        reference = current_selectors[0]["corpus_reference"]
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
        "panel_evidence": _stable_records(selected.records.get("gills-panel-evidence", ())),
        "mapping_coverage": _stable_records(selected.records.get("gills-mapping-coverage", ())),
        "runtime_realizations": _stable_records(selected.records.get("gills-runtime-realization", ())),
        "machine_source_reviews": _stable_records(selected.records.get("machine-source-review", ())),
        "panel_layouts": _stable_records(selected.records.get("panel-layout", ())),
        "machine_presentations": _stable_records(selected.records.get("machine-presentation", ())),
        "machines": _stable_records(selected.records.get("machine", ())),
        "selection_packets": _stable_records(selected.records.get("core-selection-packet", ())),
    }
    if selected.records.get("catalog-source-review"):
        records["catalog_source_reviews"] = _stable_records(
            selected.records["catalog-source-review"]
        )
    if selected.records.get("palette-lowering-proof"):
        records["palette_lowering_proofs"] = _stable_records(
            selected.records["palette-lowering-proof"]
        )
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
    direct_operation_spec_versions = {
        version: selected.schemas[version]
        for version in ("direct-operation-spec-v0", "direct-operation-spec-v1", "direct-operation-spec-v2", "direct-operation-spec-v3")
        if version in selected.schemas
    }
    if direct_operation_spec_versions:
        schemas["direct_operation_spec_versions"] = direct_operation_spec_versions
    selection_packet_versions = {
        version: selected.schemas[version]
        for version in ("core-selection-packet-v0", "task025-selection-packet-v0", "task028-selection-packet-v0")
        if version in selected.schemas
    }
    if selection_packet_versions:
        schemas["selection_packet_versions"] = selection_packet_versions
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
        projection_versions = {
            "catalog-corpus-v2": "catalog-projection-v2",
            "catalog-corpus-v3": "catalog-projection-v3",
            "catalog-corpus-v4": "catalog-projection-v4",
            "catalog-corpus-v5": "catalog-projection-v5",
        }
        projection_version = projection_versions.get(catalog_schema_version)
        if projection_version is not None:
            if projection_version not in selected.schemas:
                raise ValueError(
                    f"selected {catalog_schema_version} requires {projection_version}"
                )
            schemas["catalog_projection"] = selected.schemas[projection_version]
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
    for key, filename in TASK018_SCHEMA_NAMES.items():
        version = filename.removesuffix(".schema.json")
        if version in selected.schemas:
            schemas[key] = selected.schemas[version]
    for key, filename in TASK023_SCHEMA_NAMES.items():
        version = filename.removesuffix(".schema.json")
        if version in selected.schemas:
            schemas[key] = selected.schemas[version]
    for key, filename in TASK026A_SCHEMA_NAMES.items():
        version = filename.removesuffix(".schema.json")
        if version in selected.schemas:
            schemas[key] = selected.schemas[version]
    for key, filename in TASK026B_SCHEMA_NAMES.items():
        version = filename.removesuffix(".schema.json")
        if version in selected.schemas:
            schemas[key] = selected.schemas[version]
    for key, filename in TASK029_SCHEMA_NAMES.items():
        version = filename.removesuffix(".schema.json")
        if version in selected.schemas:
            schemas[key] = selected.schemas[version]
    for key, filename in TASK030_SCHEMA_NAMES.items():
        version = filename.removesuffix(".schema.json")
        if version in selected.schemas:
            schemas[key] = selected.schemas[version]
    for key, filename in DESKTOP_PATCHER_SCHEMA_NAMES.items():
        version = filename.removesuffix(".schema.json")
        if version in selected.schemas:
            schemas[key] = selected.schemas[version]
    for key, filename in DESKTOP_SESSION_SCHEMA_NAMES.items():
        version = filename.removesuffix(".schema.json")
        if version in selected.schemas:
            schemas[key] = selected.schemas[version]
    for key, filename in AI_SONIC_AUTHORING_SCHEMA_NAMES.items():
        version = filename.removesuffix(".schema.json")
        if version in selected.schemas:
            schemas[key] = selected.schemas[version]
    for key, filename in DESKTOP_WORKSPACE_SCHEMA_NAMES.items():
        version = filename.removesuffix(".schema.json")
        if version in selected.schemas:
            schemas[key] = selected.schemas[version]
    if "application_capability_description_v7" in schemas:
        schemas["application_capability_description"] = schemas[
            "application_capability_description_v7"
        ]
    elif "application_capability_description_v6" in schemas:
        schemas["application_capability_description"] = schemas[
            "application_capability_description_v6"
        ]
    elif "application_capability_description_v5" in schemas:
        schemas["application_capability_description"] = schemas[
            "application_capability_description_v5"
        ]
    elif "application_capability_description_v4" in schemas:
        schemas["application_capability_description"] = schemas[
            "application_capability_description_v4"
        ]
    elif "application_capability_description_v3" in schemas:
        schemas["application_capability_description"] = schemas[
            "application_capability_description_v3"
        ]
    elif "application_capability_description_v2" in schemas:
        schemas["application_capability_description"] = schemas[
            "application_capability_description_v2"
        ]
    elif "application_capability_description_v1" in schemas:
        schemas["application_capability_description"] = schemas[
            "application_capability_description_v1"
        ]

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
                "gills-panel-evidence",
                "gills-mapping-coverage",
                "gills-runtime-realization",
            )
            for record in selected.records.get(kind, ())
        ],
    )
    task018_summary = gills.validate_values(
        {
            "panel_evidence": list(records["panel_evidence"]),
            "mapping_coverage": list(records["mapping_coverage"]),
            "runtime_realizations": list(records["runtime_realizations"]),
        },
        {
            key: schemas[key]
            for key in ("panel_evidence", "mapping_coverage", "runtime_realizations")
            if key in schemas
        },
        {
            "devices": list(records["devices"]),
            "instruments": list(records["instruments"]),
            "request": list(records["request"]),
            "target": list(records["target"]),
            "backend": list(records["backend"]),
            "environment": list(records["environment"]),
        },
    )
    machine_summary = machine.validate_values(
        {
            "machine_source_reviews": list(records["machine_source_reviews"]),
            "panel_layouts": list(records["panel_layouts"]),
            "machine_presentations": list(records["machine_presentations"]),
            "machines": list(records["machines"]),
        },
        {
            group: schemas[key]
            for group, key in (
                ("machine_source_reviews", "machine_source_review"),
                ("panel_layouts", "panel_layout"),
                ("machine_presentations", "machine_presentation"),
                ("machines", "machine"),
            )
            if key in schemas
        },
        {
            "catalog": list(records["catalog"]),
            "catalog_projection": [copy.deepcopy(derived_catalog)] if derived_catalog else [],
            "contracts": list(records["contracts"]),
            "bindings": list(records["bindings"]),
            "graphs": list(records["graphs"]),
            "devices": list(records["devices"]),
            "instruments": list(records["instruments"]),
            "eligibility": list(records["eligibility"]),
        },
        repository_root,
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
        task018_summary=copy.deepcopy(task018_summary),
        machine_summary=copy.deepcopy(machine_summary),
        record_set_reference=copy.deepcopy(selected.reference),
        catalog_projection=derived_catalog,
        loaded_record_set=selected,
        record_set_path=(
            record_set_path.resolve()
            if record_set_path.is_absolute()
            else (repository_root / record_set_path).resolve()
        ),
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
        "schuss-operation-result-v6": "operation_result_v6",
        "schuss-operation-result-v7": "operation_result_v7",
        "schuss-operation-result-v8": "operation_result_v8",
        "schuss-operation-result-v9": "operation_result_v9",
        "schuss-operation-result-v10": "operation_result_v10",
        "schuss-operation-result-v11": "operation_result_v11",
        "schuss-operation-result-v12": "operation_result_v12",
        "schuss-operation-result-v13": "operation_result_v13",
        "schuss-operation-result-v14": "operation_result_v14",
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


def _dispatch_application_operation(
    request: dict[str, Any],
    context: OperationContext,
    *,
    project_workspace_available: bool = False,
    execution_service_available: bool = False,
    session_services_available: bool = False,
    authoring_service_available: bool = False,
    workspace_library_available: bool = False,
) -> dict[str, Any]:
    operation = request.get("operation") if isinstance(request, dict) else None
    required_schemas = (
        "application_capability_description",
        "operation_request_v7",
        "operation_result_v7",
    )
    missing_schemas = sorted(
        name for name in required_schemas if name not in context.schemas
    )
    if missing_schemas:
        result_version = 7 if "operation_result_v7" in context.schemas else 1
        result = _result(
            "application.describe" if result_version == 7 else "invalid-request",
            "invalid",
            None,
            [
                _diagnostic(
                    "APPLICATION_SCHEMA_UNAVAILABLE",
                    operation if isinstance(operation, str) else "invalid-request",
                    "$",
                    "the selected context is missing application schema keys: "
                    + ", ".join(missing_schemas),
                )
            ],
            version=result_version,
        )
        canonical_result_bytes(result, context)
        return result
    errors: list[str] = []
    try:
        core.assert_portable_json_value(request)
    except ValueError as exc:
        errors.append(str(exc))
    request_schema = context.schemas["operation_request_v7"]
    if isinstance(request, dict):
        errors.extend(core.schema_errors(request, request_schema, request_schema))
    else:
        errors.append("$: operation request must be an object")
    if errors:
        result_version = 7 if "operation_result_v7" in context.schemas else 1
        result = _result(
            (
                operation
                if result_version == 7 and operation == "application.describe"
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
    try:
        value = application.build_application_description(
            record_set_reference=context.record_set_reference,
            schemas=context.schemas,
            project_workspace_available=project_workspace_available,
            execution_service_available=execution_service_available,
            session_services_available=session_services_available,
            authoring_service_available=authoring_service_available,
            workspace_library_available=workspace_library_available,
        )
        value_schema = context.schemas["application_capability_description"]
        value_errors = core.schema_errors(value, value_schema, value_schema)
        if value_errors:
            raise application.CapabilityRegistryError("; ".join(value_errors))
    except application.CapabilityRegistryError as exc:
        result = _result(
            "application.describe",
            "invalid",
            None,
            [
                _diagnostic(
                    "APPLICATION_CAPABILITY_REGISTRY_INVALID",
                    "application.describe",
                    "$.value.operations",
                    str(exc),
                )
            ],
            version=7,
        )
        canonical_result_bytes(result, context)
        return result
    result = _result("application.describe", "success", value, version=7)
    canonical_result_bytes(result, context)
    return result


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


def _catalog_implementation_search(
    payload: dict[str, Any], context: OperationContext
) -> dict[str, Any]:
    projection = context.catalog_projection
    if projection is None:
        return _result(
            "catalog.implementations.search",
            "invalid",
            None,
            [
                _diagnostic(
                    "CATALOG_CONTEXT_UNAVAILABLE",
                    "catalog.implementations.search",
                    "$",
                    "the selected record set contains no exact catalog projection",
                )
            ],
            version=10,
        )
    normalized_filters = catalog.canonical_filters(payload["filters"])
    invalid = catalog.validate_implementation_filter_values(
        projection, normalized_filters
    )
    if invalid:
        return _result(
            "catalog.implementations.search",
            "invalid",
            None,
            [
                _diagnostic(
                    "CATALOG_FILTER_VALUE_UNSUPPORTED",
                    f"{name}:{value}",
                    f"$.payload.filters.{name}",
                    "the filter value is absent from the exact selected implementation projection",
                )
                for name, value in invalid
            ],
            version=10,
        )
    query, filters, results = catalog.search_implementations(
        projection, payload["query"], normalized_filters
    )
    return _result(
        "catalog.implementations.search",
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
        version=10,
    )


def _dispatch_catalog_implementation_operation(
    request: dict[str, Any], context: OperationContext
) -> dict[str, Any]:
    operation = request.get("operation") if isinstance(request, dict) else None
    errors: list[str] = []
    try:
        core.assert_portable_json_value(request)
    except ValueError as exc:
        errors.append(str(exc))
    schema = context.schemas.get("operation_request_v10")
    if schema is None:
        errors.append(
            "$: operation schema 'schuss-operation-request-v10' is unavailable in the selected context"
        )
    elif isinstance(request, dict):
        errors.extend(core.schema_errors(request, schema, schema))
    else:
        errors.append("$: operation request must be an object")
    if errors:
        version = 10 if "operation_result_v10" in context.schemas else 1
        result = _result(
            (
                operation
                if version == 10
                and operation == "catalog.implementations.search"
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
            version=version,
        )
        canonical_result_bytes(result, context)
        return result
    result = _catalog_implementation_search(request["payload"], context)
    canonical_result_bytes(result, context)
    return result


def _component_inspect(
    payload: dict[str, Any], context: OperationContext
) -> dict[str, Any]:
    reference = payload["component_contract_reference"]
    contracts = _exact_registry(
        context.records["contracts"], "component_contract_id"
    )
    contract = contracts.get(
        core.reference_key(reference, "component_contract_id")
    )
    if contract is None:
        return _result(
            "component.inspect",
            "invalid",
            None,
            [
                _diagnostic(
                    "OPERATION_REFERENCE_UNRESOLVED",
                    f"{reference['component_contract_id']}@{reference['revision']}",
                    "$.payload.component_contract_reference",
                    "the exact component contract is absent from the selected context",
                )
            ],
            version=11,
        )
    return _result(
        "component.inspect",
        "success",
        {"component_contract": copy.deepcopy(contract)},
        version=11,
    )


def _dispatch_desktop_patcher_operation(
    request: dict[str, Any], context: OperationContext
) -> dict[str, Any]:
    operation = request.get("operation") if isinstance(request, dict) else None
    errors: list[str] = []
    try:
        core.assert_portable_json_value(request)
    except ValueError as exc:
        errors.append(str(exc))
    schema = context.schemas.get("operation_request_v11")
    if schema is None:
        errors.append(
            "$: operation schema 'schuss-operation-request-v11' is unavailable in the selected context"
        )
    elif isinstance(request, dict):
        errors.extend(core.schema_errors(request, schema, schema))
    else:
        errors.append("$: operation request must be an object")
    allowed = {"component.inspect", "graph.transact"}
    if errors:
        version = 11 if "operation_result_v11" in context.schemas else 1
        result = _result(
            operation if version == 11 and operation in allowed else "invalid-request",
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
            version=version,
        )
        canonical_result_bytes(result, context)
        return result
    if operation == "component.inspect":
        result = _component_inspect(request["payload"], context)
    elif operation == "graph.transact":
        result = _graph_transact(request["payload"], context, version=11)
    else:
        result = _result(
            "invalid-request",
            "invalid",
            None,
            [
                _diagnostic(
                    "OPERATION_REQUEST_INVALID",
                    operation if isinstance(operation, str) else "invalid-request",
                    "$.operation",
                    "the v11 operation is not available without a project workspace",
                )
            ],
            version=11,
        )
    canonical_result_bytes(result, context)
    return result


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
    if context.task018_summary.get("status") != "not-applicable":
        summaries["gills_mapping_rules"] = copy.deepcopy(context.task018_summary)
    if context.machine_summary.get("status") != "not-applicable":
        summaries["machine_rules"] = copy.deepcopy(context.machine_summary)
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


def _gills_inspect(payload: dict[str, Any], context: OperationContext) -> dict[str, Any]:
    instrument_reference = payload["instrument_reference"]
    instruments = _exact_registry(context.records["instruments"], "instrument_id")
    instrument = instruments.get(core.reference_key(instrument_reference, "instrument_id"))
    if instrument is None:
        return _result(
            "gills.inspect", "invalid", None,
            [_diagnostic("OPERATION_REFERENCE_UNRESOLVED", f"{instrument_reference['instrument_id']}@{instrument_reference['revision']}", "$.payload.instrument_reference", "the exact instrument is absent from the selected record set")],
            version=6,
        )
    device_reference = instrument["device_profile_reference"]
    devices = _exact_registry(context.records["devices"], "device_profile_id")
    device = devices.get(core.reference_key(device_reference, "device_profile_id"))
    coverages = [
        copy.deepcopy(value)
        for value in context.records["mapping_coverage"]
        if value["instrument_reference"] == instrument_reference
    ]
    runtimes = [
        copy.deepcopy(value)
        for value in context.records["runtime_realizations"]
        if any(item["instrument_reference"] == instrument_reference for item in value["supported_builds"])
    ]
    if device is None or len(coverages) != 1 or len(runtimes) != 1:
        return _result(
            "gills.inspect", "invalid", None,
            [_diagnostic("GILLS_INSPECTION_CLOSURE_NOT_EXACT", f"{instrument['instrument_id']}@{instrument['revision']}", "$", "device, coverage, and runtime realization must each resolve exactly once")],
            version=6,
        )
    panel_reference = coverages[0]["panel_evidence_reference"]
    panels = _exact_registry(context.records["panel_evidence"], "panel_evidence_packet_id")
    panel = panels.get(core.reference_key(panel_reference, "panel_evidence_packet_id"))
    if panel is None:
        return _result(
            "gills.inspect", "invalid", None,
            [_diagnostic("GILLS_INSPECTION_EVIDENCE_UNRESOLVED", f"{instrument['instrument_id']}@{instrument['revision']}", "$.panel_evidence_reference", "the exact panel evidence packet is absent")],
            version=6,
        )
    requests = _exact_registry(context.records["request"], "build_request_id")
    builds = []
    for supported in runtimes[0]["supported_builds"]:
        if supported["instrument_reference"] != instrument_reference:
            continue
        request = requests.get(core.reference_key(supported["build_request_reference"], "build_request_id"))
        if request is None:
            return _result(
                "gills.inspect", "invalid", None,
                [_diagnostic("GILLS_INSPECTION_BUILD_UNRESOLVED", f"{instrument['instrument_id']}@{instrument['revision']}", "$.supported_builds", "the runtime build request is absent")],
                version=6,
            )
        builds.append({"build_request": copy.deepcopy(request), "handler": copy.deepcopy(supported["handler"])})
    return _result(
        "gills.inspect", "success",
        {
            "record_set_reference": copy.deepcopy(context.record_set_reference),
            "device_profile": copy.deepcopy(device),
            "instrument": copy.deepcopy(instrument),
            "panel_evidence": copy.deepcopy(panel),
            "coverage_report": coverages[0],
            "runtime_realization": runtimes[0],
            "build_support": builds,
            "validation": copy.deepcopy(context.task018_summary),
        },
        version=6,
    )


def _dispatch_gills_operation(request: dict[str, Any], context: OperationContext) -> dict[str, Any]:
    operation = request.get("operation") if isinstance(request, dict) else None
    errors: list[str] = []
    try:
        core.assert_portable_json_value(request)
    except ValueError as exc:
        errors.append(str(exc))
    schema = context.schemas.get("operation_request_v6")
    if schema is None:
        errors.append("$: operation schema 'schuss-operation-request-v6' is unavailable in the selected context")
    elif isinstance(request, dict):
        errors.extend(core.schema_errors(request, schema, schema))
    else:
        errors.append("$: operation request must be an object")
    if errors:
        result_version = 6 if "operation_result_v6" in context.schemas else 1
        result = _result(
            operation if result_version == 6 and operation == "gills.inspect" else "invalid-request",
            "invalid", None,
            [_diagnostic("OPERATION_REQUEST_INVALID", operation if isinstance(operation, str) else "invalid-request", "$", error) for error in sorted(set(errors))],
            version=result_version,
        )
        canonical_result_bytes(result, context)
        return result
    result = _gills_inspect(request["payload"], context)
    canonical_result_bytes(result, context)
    return result


def _machine_inspect(payload: dict[str, Any], context: OperationContext) -> dict[str, Any]:
    if context.machine_summary.get("status") != "valid":
        return _result(
            "machine.inspect",
            "invalid",
            None,
            [
                _diagnostic(
                    "MACHINE_LAYER_INVALID",
                    f"{context.record_set_reference['record_set_id']}@{context.record_set_reference['revision']}",
                    "$",
                    "the selected machine-layer closure is not valid",
                )
            ],
            version=9,
        )
    reviews = _exact_registry(
        context.records["machine_source_reviews"], "machine_source_review_id"
    )
    presentations = _exact_registry(
        context.records["machine_presentations"], "machine_presentation_id"
    )
    panels = _exact_registry(context.records["panel_layouts"], "panel_layout_id")
    machines = _exact_registry(context.records["machines"], "machine_id")
    instruments = _exact_registry(context.records["instruments"], "instrument_id")

    machine_record = None
    instrument = None
    if "source_review_reference" in payload:
        review_reference = payload["source_review_reference"]
        review = reviews.get(
            core.reference_key(review_reference, "machine_source_review_id")
        )
        location = "$.payload.source_review_reference"
        subject = f"{review_reference['machine_source_review_id']}@{review_reference['revision']}"
    else:
        machine_reference = payload["machine_reference"]
        machine_record = machines.get(
            core.reference_key(machine_reference, "machine_id")
        )
        if machine_record is None:
            return _result(
                "machine.inspect",
                "invalid",
                None,
                [
                    _diagnostic(
                        "MACHINE_INSPECTION_REFERENCE_UNRESOLVED",
                        f"{machine_reference['machine_id']}@{machine_reference['revision']}",
                        "$.payload.machine_reference",
                        "the exact completed machine is absent from the selected record set",
                    )
                ],
                version=9,
            )
        review_reference = machine_record["source_review_reference"]
        review = reviews.get(
            core.reference_key(review_reference, "machine_source_review_id")
        )
        instrument = instruments.get(
            core.reference_key(machine_record["instrument_reference"], "instrument_id")
        )
        location = "$.machine.source_review_reference"
        subject = f"{machine_record['machine_id']}@{machine_record['revision']}"
    if review is None:
        return _result(
            "machine.inspect",
            "invalid",
            None,
            [
                _diagnostic(
                    "MACHINE_INSPECTION_REFERENCE_UNRESOLVED",
                    subject,
                    location,
                    "the exact machine source review is absent from the selected record set",
                )
            ],
            version=9,
        )
    candidates = [
        value
        for value in presentations.values()
        if value["source_review_reference"] == review_reference
        and (
            machine_record is None
            or value["machine_presentation_id"]
            == machine_record["presentation_reference"]["machine_presentation_id"]
        )
    ]
    if machine_record is not None:
        candidates = [
            value
            for value in candidates
            if core.exact_key(value, "machine_presentation_id")
            == core.reference_key(
                machine_record["presentation_reference"], "machine_presentation_id"
            )
        ]
    if len(candidates) != 1:
        return _result(
            "machine.inspect",
            "invalid",
            None,
            [
                _diagnostic(
                    "MACHINE_INSPECTION_PRESENTATION_NOT_EXACT",
                    subject,
                    "$.presentation_reference",
                    "the source review must resolve exactly one applicable machine presentation",
                )
            ],
            version=9,
        )
    presentation = candidates[0]
    panel = panels.get(
        core.reference_key(presentation["panel_layout_reference"], "panel_layout_id")
    )
    if panel is None or (machine_record is not None and instrument is None):
        return _result(
            "machine.inspect",
            "invalid",
            None,
            [
                _diagnostic(
                    "MACHINE_INSPECTION_CLOSURE_UNRESOLVED",
                    subject,
                    "$",
                    "the exact panel layout and completed-machine instrument closure must resolve",
                )
            ],
            version=9,
        )
    value = machine.inspection_value(
        review,
        presentation,
        panel,
        context.record_set_reference,
        context.machine_summary,
        machine=machine_record,
        instrument=instrument,
    )
    return _result("machine.inspect", "success", value, version=9)


def _dispatch_machine_operation(
    request: dict[str, Any], context: OperationContext
) -> dict[str, Any]:
    operation = request.get("operation") if isinstance(request, dict) else None
    errors: list[str] = []
    try:
        core.assert_portable_json_value(request)
    except ValueError as exc:
        errors.append(str(exc))
    schema = context.schemas.get("operation_request_v9")
    if schema is None:
        errors.append(
            "$: operation schema 'schuss-operation-request-v9' is unavailable in the selected context"
        )
    elif isinstance(request, dict):
        errors.extend(core.schema_errors(request, schema, schema))
    else:
        errors.append("$: operation request must be an object")
    if errors:
        version = 9 if "operation_result_v9" in context.schemas else 1
        result = _result(
            operation if version == 9 and operation == "machine.inspect" else "invalid-request",
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
            version=version,
        )
        canonical_result_bytes(result, context)
        return result
    result = _machine_inspect(request["payload"], context)
    canonical_result_bytes(result, context)
    return result


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
    if kind == "set-graph-display-name":
        graph["display_name"] = edit["display_name"]
    elif kind == "add-node":
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
    elif kind == "set-public-parameter-default":
        parameter = _find_unique(
            graph["public_parameters"], "facet_id", edit["facet_id"]
        )
        parameter["default"] = edit["value"]
    elif kind == "set-parameter-binding-point":
        binding = _find_unique(
            graph["parameter_bindings"], "binding_id", edit["binding_id"]
        )
        points = binding["transform"]["points"]
        index = edit["point_index"]
        if index >= len(points):
            raise _TransactionEditError(
                f"binding point index {index} is outside the exact point sequence"
            )
        points[index] = {
            "source": edit["source"],
            "destination": edit["destination"],
        }
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
    additional_family_references.extend(
        copy.deepcopy(context.additional_family_references)
    )
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


def _graph_transact(
    payload: dict[str, Any],
    context: OperationContext,
    *,
    version: int = 1,
) -> dict[str, Any]:
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
            version=version,
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
            version=version,
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
            version=version,
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
        version=version,
    )


def transact_graph_payload(
    payload: dict[str, Any], context: OperationContext
) -> dict[str, Any]:
    """Apply an already schema-validated shared graph transaction payload."""

    return _graph_transact(payload, context)


def _dispatch_desktop_session_operation(
    request: dict[str, Any],
    application_context: OperationContext,
    project_service: Any,
    build_session_service: Any | None,
    device_session_service: Any | None,
) -> dict[str, Any]:
    """Dispatch the bounded process-local build and device session surface."""

    loaded = project_service.load()
    project_context = with_compiler_schemas(
        loaded.context, project_service.repository_root
    )
    operation = request.get("operation") if isinstance(request, dict) else None
    errors: list[str] = []
    try:
        core.assert_portable_json_value(request)
    except ValueError as exc:
        errors.append(str(exc))
    schema = application_context.schemas.get("operation_request_v12")
    if schema is None:
        errors.append(
            "$: operation schema 'schuss-operation-request-v12' is unavailable in the selected context"
        )
    elif isinstance(request, dict):
        errors.extend(core.schema_errors(request, schema, schema))
    else:
        errors.append("$: operation request must be an object")
    allowed = {
        "build.session.start",
        "build.session.inspect",
        "device.session.discover",
        "device.session.inspect",
        "device.upload.start",
        "device.upload.inspect",
    }
    if operation not in allowed:
        errors.append("$.operation: operation is not in the desktop session surface")
    if build_session_service is None or device_session_service is None:
        errors.append("$: process-local build and device session services are required")
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
            version=12,
        )
        canonical_result_bytes(result, application_context)
        return result

    assert build_session_service is not None
    assert device_session_service is not None
    payload = request["payload"]
    project_reference = {
        "project_id": loaded.manifest["project_id"],
        "revision": loaded.manifest["revision"],
        "content_hash": loaded.manifest["content_hash"],
    }
    try:
        if operation == "build.session.start":
            compilation_context = compiler.CompilationContext.from_values(
                build_request_reference=payload["build_request_reference"],
                closure_source={
                    "kind": "project",
                    "project_reference": copy.deepcopy(project_reference),
                    "base_record_set_reference": copy.deepcopy(
                        project_context.record_set_reference
                    ),
                },
                records=project_context.records,
                schemas=project_context.schemas,
            )
            value = build_session_service.start(
                compilation_context,
                build_request_reference=payload["build_request_reference"],
                execution_intent=payload["execution_intent"],
                project_reference=project_reference,
            )
        elif operation == "build.session.inspect":
            value = build_session_service.inspect(payload["build_session_id"])
        elif operation == "device.session.discover":
            value = device_session_service.discover(
                records=project_context.records,
                build_request_reference=payload["build_request_reference"],
                project_reference=project_reference,
                discovery_intent=payload["discovery_intent"],
            )
        elif operation == "device.session.inspect":
            value = device_session_service.inspect(payload["device_session_id"])
        elif operation == "device.upload.start":
            value = device_session_service.start_upload(
                device_session_id=payload["device_session_id"],
                build_session_id=payload["build_session_id"],
                artifact_sha256=payload["artifact_sha256"],
                upload_intent=payload["upload_intent"],
                start_patch=payload["start_patch"],
            )
        else:
            value = device_session_service.inspect_upload(
                payload["upload_session_id"]
            )
    except Exception as exc:
        code = str(getattr(exc, "code", "DESKTOP_SESSION_OPERATION_FAILED"))
        status = (
            "unavailable"
            if code.startswith("DEVICE_USB_")
            or code in {
                "DEVICE_SESSION_ENDPOINT_CHANGED",
                "DEVICE_SESSION_IDENTITY_CHANGED",
            }
            else "invalid"
        )
        result = _result(
            str(operation),
            status,
            None,
            [
                _diagnostic(
                    code,
                    str(operation),
                    "$.payload",
                    str(exc),
                )
            ],
            version=12,
        )
        canonical_result_bytes(result, application_context)
        return result
    result = _result(str(operation), "success", value, version=12)
    canonical_result_bytes(result, application_context)
    return result


def dispatch_operation(
    request: dict[str, Any],
    context: OperationContext,
    *,
    project_service: Any | None = None,
    execution_service: execution.ExecutionService | None = None,
    build_session_service: Any | None = None,
    device_session_service: Any | None = None,
    authoring_service: Any | None = None,
    workspace_service: Any | None = None,
) -> dict[str, Any]:
    """Dispatch one parsed request through the public pure operation API."""

    if (
        isinstance(request, dict)
        and request.get("schema_version") == "schuss-operation-request-v14"
    ):
        from .workspace_library import dispatch_workspace_operation

        return dispatch_workspace_operation(request, context, workspace_service)

    if (
        isinstance(request, dict)
        and request.get("schema_version") == "schuss-operation-request-v13"
    ):
        from .ai_authoring import dispatch_authoring_operation

        active_context = context
        if authoring_service is not None:
            active_context = authoring_service.project_service.load().context
        return dispatch_authoring_operation(
            request, active_context, authoring_service
        )

    if (
        isinstance(request, dict)
        and request.get("schema_version") == "schuss-operation-request-v12"
    ):
        if project_service is None:
            raise ValueError("v12 desktop session operations require an explicit project service")
        return _dispatch_desktop_session_operation(
            request,
            context,
            project_service,
            build_session_service,
            device_session_service,
        )

    if (
        isinstance(request, dict)
        and request.get("schema_version") == "schuss-operation-request-v11"
    ):
        operation = request.get("operation")
        if operation == "project.profile.transact":
            if project_service is None:
                raise ValueError(
                    "v11 project operations require an explicit project service"
                )
            from .project_service import dispatch_project_operation

            return dispatch_project_operation(request, project_service)
        if project_service is not None:
            loaded = project_service.load()
            return _dispatch_desktop_patcher_operation(request, loaded.context)
        return _dispatch_desktop_patcher_operation(request, context)

    if (
        isinstance(request, dict)
        and request.get("schema_version") == "schuss-operation-request-v10"
    ):
        if project_service is not None:
            loaded = project_service.load()
            return _dispatch_catalog_implementation_operation(
                request, loaded.context
            )
        return _dispatch_catalog_implementation_operation(request, context)

    if (
        isinstance(request, dict)
        and request.get("schema_version") == "schuss-operation-request-v9"
    ):
        if project_service is not None:
            loaded = project_service.load()
            return _dispatch_machine_operation(request, loaded.context)
        return _dispatch_machine_operation(request, context)

    if (
        isinstance(request, dict)
        and request.get("schema_version") == "schuss-operation-request-v8"
    ):
        if project_service is None:
            raise ValueError("v8 project operations require an explicit project service")
        from .project_service import dispatch_project_operation

        return dispatch_project_operation(request, project_service)

    if (
        isinstance(request, dict)
        and request.get("schema_version") == "schuss-operation-request-v7"
    ):
        if project_service is not None:
            loaded = project_service.load()
            description_context = (
                context
                if "application_capability_description_v5" in context.schemas
                else loaded.context
            )
            return _dispatch_application_operation(
                request,
                description_context,
                project_workspace_available=True,
                execution_service_available=execution_service is not None,
                session_services_available=(
                    build_session_service is not None
                    and device_session_service is not None
                ),
                authoring_service_available=authoring_service is not None,
                workspace_library_available=workspace_service is not None,
            )
        return _dispatch_application_operation(
            request,
            context,
            execution_service_available=execution_service is not None,
            session_services_available=(
                build_session_service is not None
                and device_session_service is not None
            ),
            authoring_service_available=authoring_service is not None,
            workspace_library_available=workspace_service is not None,
        )

    if (
        isinstance(request, dict)
        and request.get("schema_version") == "schuss-operation-request-v6"
    ):
        if project_service is not None:
            loaded = project_service.load()
            return _dispatch_gills_operation(request, loaded.context)
        return _dispatch_gills_operation(request, context)

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

    if project_service is not None:
        loaded = project_service.load()
        context = loaded.context

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
