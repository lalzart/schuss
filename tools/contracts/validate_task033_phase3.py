#!/usr/bin/env python3
"""Validate the Task 033 Phase 3 canonical generated native registry."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "tools/contracts") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools/contracts"))

from tools.contracts import generate_task033_phase3_registry as generator  # noqa: E402
from tools.contracts import validate_task033_phase2  # noqa: E402


def _load_json(root: Path, path: Path) -> dict[str, Any]:
    value = json.loads((root / path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Task 033 Phase 3 JSON is not an object: {path}")
    return value


def _generated_module(root: Path) -> Any:
    path = root / generator.PYTHON_OUTPUT
    spec = importlib.util.spec_from_file_location(
        "task033_generated_native_registry", path
    )
    if spec is None or spec.loader is None:
        raise ValueError("Task 033 generated Python registry could not be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _expected_python_descriptors(manifest: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "binding_id": item["implementation_binding_reference"][
                "implementation_id"
            ],
            "contract_id": item["contract_reference"]["component_contract_id"],
            "factory_id": item["factory_id"],
            "input_facets": tuple(value["facet_id"] for value in item["inputs"]),
            "output_facets": tuple(value["facet_id"] for value in item["outputs"]),
            "parameter_facets": tuple(item["parameter_facets"]),
            "role": item["role"],
            "state_alignment": item["state"]["alignment_bytes"],
            "state_size": item["state"]["size_bytes"],
        }
        for item in manifest["factories"]
    )


def _factory_enum(schema: dict[str, Any], *, observation: bool) -> list[str]:
    if not observation:
        return schema["properties"]["nodes"]["items"]["properties"]["factory_id"][
            "enum"
        ]
    return schema["properties"]["graph_execution"]["properties"][
        "factory_instance_counts"
    ]["items"]["properties"]["factory_id"]["enum"]


def validate(repository_root: Path = ROOT) -> dict[str, Any]:
    root = repository_root.resolve()
    outputs, generation = generator.generated(root)
    stale = [
        path.as_posix()
        for path, expected in sorted(outputs.items())
        if not (root / path).is_file() or (root / path).read_bytes() != expected
    ]
    if stale:
        raise ValueError(
            "NATIVE_REGISTRY_GENERATED_OUTPUT_STALE: " + ", ".join(stale)
        )

    phase2 = validate_task033_phase2.validate(root)
    if phase2["status"] != "valid" or not phase2["parent_members_preserved"]:
        raise ValueError("NATIVE_REGISTRY_PHASE2_AUTHORITY_INVALID")

    manifest = _load_json(root, generator.MANIFEST_PATH)
    module = _generated_module(root)
    expected_descriptors = _expected_python_descriptors(manifest)
    if module.FACTORY_DESCRIPTORS != expected_descriptors:
        raise ValueError("NATIVE_REGISTRY_PYTHON_DESCRIPTOR_MISMATCH")
    if module.FACTORY_REGISTRY_VERSION != manifest["registry_version"]:
        raise ValueError("NATIVE_REGISTRY_PYTHON_VERSION_MISMATCH")
    expected_manifest_hash = hashlib.sha256(
        generator._canonical_bytes(manifest)
    ).hexdigest()
    if module.MANIFEST_SHA256 != expected_manifest_hash:
        raise ValueError("NATIVE_REGISTRY_PYTHON_MANIFEST_HASH_MISMATCH")

    factory_ids = sorted(item["factory_id"] for item in manifest["factories"])
    package_schema = _load_json(root, generator.PACKAGE_SCHEMA)
    observation_schema = _load_json(root, generator.OBSERVATION_SCHEMA)
    if _factory_enum(package_schema, observation=False) != factory_ids:
        raise ValueError("NATIVE_REGISTRY_PACKAGE_SCHEMA_ENUM_MISMATCH")
    if _factory_enum(observation_schema, observation=True) != factory_ids:
        raise ValueError("NATIVE_REGISTRY_OBSERVATION_SCHEMA_ENUM_MISMATCH")

    lowering_source = (root / "packages/schuss_core/variable_host_runtime.py").read_text(
        encoding="utf-8"
    )
    if "FACTORY_SPECS = (" in lowering_source or any(
        factory_id in lowering_source for factory_id in factory_ids
    ):
        raise ValueError("NATIVE_REGISTRY_PYTHON_MANUAL_TABLE_REMAINS")

    runtime_source = (root / generator.CPP_OUTPUT).read_bytes()
    runtime_hash = hashlib.sha256(runtime_source).hexdigest()
    if runtime_hash != "d224c6bfd5c89ca369e6516058cb19a84ca00e600ad775482488a55858699122":
        raise ValueError("NATIVE_REGISTRY_CPP_ACCEPTED_BYTES_CHANGED")

    return {
        "schema_version": "task033-phase3-validation-summary-v1",
        "status": "valid",
        "record_set_reference": phase2["record_set_reference"],
        "provider_reference": manifest["provider_reference"],
        "registry_version": manifest["registry_version"],
        "factory_count": len(manifest["factories"]),
        "factory_ids": factory_ids,
        "manifest_sha256": expected_manifest_hash,
        "generated_output_sha256": {
            path.as_posix(): hashlib.sha256(payload).hexdigest()
            for path, payload in sorted(outputs.items())
        },
        "phase2_source_release_and_provider_preserved": True,
        "task031_task032_trees_preserved": True,
        "runtime_v1_cpp_byte_preserved": True,
        "semantic_record_provider_or_capability_allocated": False,
        "runtime_behavior_changed": False,
        "device_ui_or_publication_performed": False,
        "generation_summary": generation,
    }


def main() -> int:
    try:
        result = validate()
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
