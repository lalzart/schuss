"""Aggregate validator composing the three independent domain-rule modules."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import component_graph_rules as component
import device_instrument_rules as device
import record_set_rules
import target_backend_build_rules as target
import validator_core as core


def _component_record_set_validation(
    selected: record_set_rules.LoadedRecordSet,
    repository_root: Path,
) -> component.CoreValidation:
    overlay_path = repository_root / component.OVERLAY_RELATIVE_PATH
    snapshot_root = repository_root / component.SNAPSHOT_RELATIVE_PATH
    manifest_path = snapshot_root / "manifest.json"
    overlay = core.load_json(overlay_path)
    return component.validate_component_graph_values(
        list(selected.records.get("catalog-family", ())),
        list(selected.records.get("component-contract", ())),
        list(selected.records.get("implementation-binding", ())),
        list(selected.records.get("dsp-graph", ())),
        {
            "family": selected.schemas[component.FAMILY_SCHEMA_VERSION],
            "contract": selected.schemas[component.CONTRACT_SCHEMA_VERSION],
            "binding": selected.schemas[component.BINDING_SCHEMA_VERSION],
            "graph": selected.schemas[component.GRAPH_SCHEMA_VERSION],
        },
        overlay,
        core.sha256_file(overlay_path),
        core.sha256_file(manifest_path),
        component._observations(snapshot_root),
    )


def validate_device_instrument_record_set(
    selected: record_set_rules.LoadedRecordSet,
    repository_root: Path,
) -> dict[str, Any]:
    component_result = _component_record_set_validation(selected, repository_root)
    instruments = [
        record
        for record in selected.records.get("instrument", ())
        if record.get("schema_version") == device.INSTRUMENT_SCHEMA_VERSION
    ]
    return device.validate_contract_values(
        list(selected.records.get("device-profile", ())),
        instruments,
        selected.schemas[device.DEVICE_SCHEMA_VERSION],
        selected.schemas[device.INSTRUMENT_SCHEMA_VERSION],
        component_result.graph_targets,
    )


def validate_all_record_set(
    selected: record_set_rules.LoadedRecordSet,
    repository_root: Path,
) -> dict[str, Any]:
    component_result = _component_record_set_validation(selected, repository_root)
    devices = list(selected.records.get("device-profile", ()))
    instruments = [
        record
        for record in selected.records.get("instrument", ())
        if record.get("schema_version") == device.INSTRUMENT_SCHEMA_VERSION
    ]
    device_instrument = device.validate_contract_values(
        devices,
        instruments,
        selected.schemas[device.DEVICE_SCHEMA_VERSION],
        selected.schemas[device.INSTRUMENT_SCHEMA_VERSION],
        component_result.graph_targets,
    )
    return combine_task006_summaries(
        component_result.summary,
        device_instrument,
        len(devices),
        len(instruments),
    )


def validate_target_backend_build_record_set(
    selected: record_set_rules.LoadedRecordSet,
    repository_root: Path,
) -> target.Task007Validation:
    upstream_summary = validate_all_record_set(selected, repository_root)
    loaded = {
        kind: list(selected.records.get(kind, ()))
        for kind in target.SCHEMA_SPECS
    }
    upstream = {
        "families": list(selected.records.get("catalog-family", ())),
        "contracts": list(selected.records.get("component-contract", ())),
        "bindings": list(selected.records.get("implementation-binding", ())),
        "graphs": list(selected.records.get("dsp-graph", ())),
        "devices": list(selected.records.get("device-profile", ())),
        "instruments": [
            record
            for record in selected.records.get("instrument", ())
            if record.get("schema_version") == device.INSTRUMENT_SCHEMA_VERSION
        ],
    }
    schemas = {
        kind: selected.schemas[specification[1]]
        for kind, specification in target.SCHEMA_SPECS.items()
    }
    return target.validate_target_backend_build_values(
        loaded,
        schemas,
        upstream,
        repository_root,
        upstream_summary,
    )


def validate_device_instrument_directory(
    contract_root: Path,
    schema_root: Path,
    repository_root: Path,
) -> dict[str, Any]:
    device_schema = core.load_json(schema_root / device.DEVICE_SCHEMA_NAME)
    instrument_schema = core.load_json(schema_root / device.INSTRUMENT_SCHEMA_NAME)
    devices = [
        core.load_json(path)
        for path in core.record_files(contract_root, "device-profiles")
    ]
    instruments = [
        core.load_json(path)
        for path in core.record_files(contract_root, "instruments")
    ]
    graph_targets = None
    if (contract_root / "graphs").is_dir():
        graph_targets = component.get_validated_graph_target_registry(
            contract_root,
            schema_root,
            repository_root,
        )
    return device.validate_contract_values(
        devices,
        instruments,
        device_schema,
        instrument_schema,
        graph_targets,
    )


def validate_all_contracts(
    contract_root: Path,
    schema_root: Path,
    repository_root: Path,
) -> dict[str, Any]:
    """Return the byte-compatible aggregate Task 006 summary."""

    component_result = component.validate_component_graph_directory(
        contract_root,
        schema_root,
        repository_root,
    )
    device_schema = core.load_json(schema_root / device.DEVICE_SCHEMA_NAME)
    instrument_schema = core.load_json(schema_root / device.INSTRUMENT_SCHEMA_NAME)
    devices = [
        core.load_json(path)
        for path in core.record_files(contract_root, "device-profiles")
    ]
    instruments = [
        core.load_json(path)
        for path in core.record_files(contract_root, "instruments")
    ]
    device_instrument = device.validate_contract_values(
        devices,
        instruments,
        device_schema,
        instrument_schema,
        component_result.graph_targets,
    )
    return combine_task006_summaries(
        component_result.summary,
        device_instrument,
        len(devices),
        len(instruments),
    )


def combine_task006_summaries(
    component_summary: dict[str, Any],
    device_instrument: dict[str, Any],
    device_count: int,
    instrument_count: int,
) -> dict[str, Any]:
    """Compose byte-compatible Task 006 output from an explicit value closure."""

    combined_diagnostics = sorted(
        component_summary["diagnostics"] + device_instrument["diagnostics"],
        key=core.diagnostic_sort_key,
    )
    error_count = len(combined_diagnostics)
    deferred_count = device_instrument["reference_resolution"]["graphs_deferred"]
    resolved_count = device_instrument["reference_resolution"]["graphs_resolved"]
    gate_status = "failed" if error_count else "passed"
    return {
        "schema_version": "task-006-validation-summary-v0",
        "status": "invalid"
        if error_count
        else ("valid-with-historical-deferred" if deferred_count else "valid"),
        "record_counts": {
            **component_summary["record_counts"],
            "device_profiles": device_count,
            "instruments": instrument_count,
        },
        "reference_resolution": {
            **component_summary["reference_resolution"],
            "device_profiles": device_instrument["reference_resolution"][
                "device_profiles_resolved"
            ],
            "instrument_graphs_deferred": deferred_count,
            "instrument_graphs_resolved": resolved_count,
        },
        "evidence_levels": [
            {"level": "structural-schema", "status": gate_status},
            {"level": "exact-reference-closure", "status": gate_status},
            {"level": "target-independent-contract-type", "status": gate_status},
            {"level": "implementation-seam-map", "status": gate_status},
            {
                "level": "instrument-graph-target",
                "status": "failed"
                if error_count
                else (
                    "passed-with-historical-deferred" if deferred_count else "passed"
                ),
            },
            {"level": "backend-lowering", "status": "not-run"},
            {"level": "artifact-generation", "status": "not-run"},
            {"level": "arm-compile-link", "status": "not-run"},
            {"level": "connected-device", "status": "not-run"},
            {"level": "real-time-resource", "status": "not-run"},
            {"level": "audible-listening", "status": "not-run"},
        ],
        "diagnostics": combined_diagnostics,
    }


def validate_target_backend_build_directory(
    contract_root: Path,
    schema_root: Path,
    repository_root: Path,
) -> target.Task007Validation:
    """Compose all three domains and return the byte-compatible Task 007 result."""

    upstream_summary = validate_all_contracts(
        contract_root,
        schema_root,
        repository_root,
    )
    return target.validate_target_backend_build_directory(
        contract_root,
        schema_root,
        repository_root,
        upstream_summary,
    )
