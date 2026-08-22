#!/usr/bin/env python3
"""Generate the Task 033 Phase 3 native registry language surfaces."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import pprint
import re
import sys
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "tools/contracts") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools/contracts"))

from tools.contracts import record_set_rules  # noqa: E402
from tools.contracts import validator_core as core  # noqa: E402


MANIFEST_PATH = Path("contracts/task033/phase3/native-provider-registry-v1.json")
MANIFEST_SCHEMA_PATH = Path("schemas/native-provider-registry-v1.schema.json")
RECORD_SET_PATH = Path(
    "contracts/record-sets/task033-phase2-collection-provider-v1.json"
)
PYTHON_OUTPUT = Path("packages/schuss_core/generated_native_registry.py")
CPP_OUTPUT = Path("packages/schuss_rt/src/runtime_v1.cpp")
PACKAGE_SCHEMA = Path("schemas/host-runtime-package-v1.schema.json")
OBSERVATION_SCHEMA = Path("schemas/host-runtime-observation-v1.schema.json")
RUNTIME_HEADER = Path("packages/schuss_rt/include/schuss_rt/runtime.hpp")


class RegistryGenerationError(ValueError):
    """Fail-closed canonical registry generation error."""


def _canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _load_json(root: Path, path: Path) -> dict[str, Any]:
    try:
        value = json.loads((root / path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RegistryGenerationError(
            f"NATIVE_REGISTRY_INPUT_INVALID: {path.as_posix()}: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise RegistryGenerationError(
            f"NATIVE_REGISTRY_INPUT_INVALID: {path.as_posix()} must be an object"
        )
    return value


def _reference(record: Mapping[str, Any], id_field: str) -> dict[str, Any]:
    return {
        id_field: record[id_field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def _exact_record(
    records: list[dict[str, Any]],
    reference: Mapping[str, Any],
    id_field: str,
    code: str,
) -> dict[str, Any]:
    matches = [item for item in records if _reference(item, id_field) == dict(reference)]
    if len(matches) != 1:
        raise RegistryGenerationError(f"{code}: expected one exact reference")
    return matches[0]


def _tree_hash(root: Path, relative: str) -> str:
    directory = root / relative
    if not directory.is_dir():
        raise RegistryGenerationError(
            f"NATIVE_REGISTRY_PRESERVED_TREE_MISSING: {relative}"
        )
    digest = hashlib.sha256()
    for path in sorted(item for item in directory.rglob("*") if item.is_file()):
        portable = path.relative_to(root).as_posix().encode("utf-8")
        payload = path.read_bytes()
        digest.update(len(portable).to_bytes(8, "big"))
        digest.update(portable)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def _facet_rows(contract: Mapping[str, Any], direction: str) -> list[dict[str, Any]]:
    return [
        {
            "facet_id": item["facet_id"],
            "fractional_bits": item["port_type"]["representation"]["fractional_bits"],
        }
        for item in contract["ports"]
        if item["direction"] == direction
    ]


def _validate_manifest(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    schema = _load_json(root, MANIFEST_SCHEMA_PATH)
    errors = core.schema_errors(manifest, schema, schema)
    if errors:
        raise RegistryGenerationError(
            "NATIVE_REGISTRY_SCHEMA_INVALID: " + "; ".join(errors)
        )

    factories = manifest["factories"]
    unique_fields = (
        "role",
        "provider_binding_id",
        "factory_id",
    )
    for field in unique_fields:
        values = [item[field] for item in factories]
        if len(values) != len(set(values)):
            raise RegistryGenerationError(
                f"NATIVE_REGISTRY_FACTORY_DUPLICATE: {field}"
            )
    implementation_ids = [
        item["implementation_binding_reference"]["implementation_id"]
        for item in factories
    ]
    if len(implementation_ids) != len(set(implementation_ids)):
        raise RegistryGenerationError(
            "NATIVE_REGISTRY_FACTORY_DUPLICATE: implementation_id"
        )

    selected = record_set_rules.load_record_set(root, RECORD_SET_PATH)
    providers = selected.records["implementation-provider"]
    provider = _exact_record(
        providers,
        manifest["provider_reference"],
        "implementation_provider_id",
        "NATIVE_REGISTRY_PROVIDER_REFERENCE_MISMATCH",
    )
    if provider["registry_version"] != manifest["registry_version"]:
        raise RegistryGenerationError("NATIVE_REGISTRY_VERSION_MISMATCH")
    if provider["provider_abi"] != manifest["runtime_abi"]:
        raise RegistryGenerationError("NATIVE_REGISTRY_ABI_MISMATCH")
    if sorted(provider["callback_constraints"]) != sorted(
        manifest["callback_constraints"]
    ):
        raise RegistryGenerationError("NATIVE_REGISTRY_CALLBACK_MISMATCH")

    provider_bindings = {
        item["provider_binding_id"]: item for item in provider["bindings"]
    }
    if set(provider_bindings) != {
        item["provider_binding_id"] for item in factories
    }:
        raise RegistryGenerationError("NATIVE_REGISTRY_PROVIDER_COVERAGE_MISMATCH")

    for factory in factories:
        binding = provider_bindings[factory["provider_binding_id"]]
        expected_provider_fields = {
            "component_contract_reference": factory["contract_reference"],
            "implementation_binding_reference": factory[
                "implementation_binding_reference"
            ],
            "target_reference": factory["target_reference"],
            "backend_reference": factory["backend_reference"],
            "runtime_factory_id": factory["factory_id"],
        }
        for field, expected in expected_provider_fields.items():
            if binding[field] != expected:
                raise RegistryGenerationError(
                    "NATIVE_REGISTRY_PROVIDER_BINDING_MISMATCH: "
                    f"{factory['provider_binding_id']} {field}"
                )

        contract = _exact_record(
            selected.records["component-contract"],
            factory["contract_reference"],
            "component_contract_id",
            "NATIVE_REGISTRY_CONTRACT_REFERENCE_MISMATCH",
        )
        implementation = _exact_record(
            selected.records["implementation-binding"],
            factory["implementation_binding_reference"],
            "implementation_id",
            "NATIVE_REGISTRY_IMPLEMENTATION_REFERENCE_MISMATCH",
        )
        if implementation["contract_reference"] != factory["contract_reference"]:
            raise RegistryGenerationError(
                "NATIVE_REGISTRY_IMPLEMENTATION_CONTRACT_MISMATCH"
            )
        if factory["inputs"] != _facet_rows(contract, "inlet"):
            raise RegistryGenerationError(
                f"NATIVE_REGISTRY_INPUT_FACET_MISMATCH: {factory['role']}"
            )
        if factory["outputs"] != _facet_rows(contract, "outlet"):
            raise RegistryGenerationError(
                f"NATIVE_REGISTRY_OUTPUT_FACET_MISMATCH: {factory['role']}"
            )
        if factory["parameter_facets"] != [
            item["facet_id"] for item in contract["parameters"]
        ]:
            raise RegistryGenerationError(
                f"NATIVE_REGISTRY_PARAMETER_FACET_MISMATCH: {factory['role']}"
            )

    runtime_header = (root / RUNTIME_HEADER).read_text(encoding="utf-8")
    match = re.search(r"enum class Role\s*:[^{]+\{([^}]+)\}", runtime_header)
    if match is None:
        raise RegistryGenerationError("NATIVE_REGISTRY_ROLE_ENUM_MISSING")
    runtime_roles = [item.strip() for item in match.group(1).split(",")]
    if runtime_roles != [item["role"] for item in factories]:
        raise RegistryGenerationError("NATIVE_REGISTRY_ROLE_ENUM_MISMATCH")

    for relative, expected in manifest["preserved_tree_hashes"].items():
        if _tree_hash(root, relative) != expected:
            raise RegistryGenerationError(
                f"NATIVE_REGISTRY_PRESERVED_TREE_DRIFT: {relative}"
            )
    return manifest


def _python_bytes(manifest: Mapping[str, Any]) -> bytes:
    descriptors = []
    for factory in manifest["factories"]:
        descriptors.append(
            {
                "binding_id": factory["implementation_binding_reference"][
                    "implementation_id"
                ],
                "contract_id": factory["contract_reference"][
                    "component_contract_id"
                ],
                "factory_id": factory["factory_id"],
                "input_facets": tuple(
                    item["facet_id"] for item in factory["inputs"]
                ),
                "output_facets": tuple(
                    item["facet_id"] for item in factory["outputs"]
                ),
                "parameter_facets": tuple(factory["parameter_facets"]),
                "role": factory["role"],
                "state_alignment": factory["state"]["alignment_bytes"],
                "state_size": factory["state"]["size_bytes"],
            }
        )
    rendered = pprint.pformat(tuple(descriptors), width=88, sort_dicts=True)
    manifest_sha = hashlib.sha256(_canonical_bytes(manifest)).hexdigest()
    return (
        '"""Generated by generate_task033_phase3_registry.py; do not edit."""\n\n'
        f'MANIFEST_SHA256 = "{manifest_sha}"\n'
        f'FACTORY_REGISTRY_VERSION = "{manifest["registry_version"]}"\n'
        f"FACTORY_DESCRIPTORS = {rendered}\n"
    ).encode("utf-8")


def _cpp_port(item: Mapping[str, Any]) -> str:
    return '{"' + item["facet_id"] + '", ' + str(item["fractional_bits"]) + "}"


def _cpp_array(values: list[str], capacity: int, empty: str) -> str:
    padded = values + [empty] * (capacity - len(values))
    return "{{" + ", ".join(padded) + "}}"


def _cpp_registry_text(manifest: Mapping[str, Any]) -> str:
    lines = [
        f"const std::array<FactoryDescriptor, {len(manifest['factories'])}> kFactories{{{{",
    ]
    for factory in manifest["factories"]:
        contract = factory["contract_reference"]
        binding = factory["implementation_binding_reference"]
        lifecycle = factory["lifecycle"]
        inputs = _cpp_array(
            [_cpp_port(item) for item in factory["inputs"]], 3, "no_port"
        )
        outputs = _cpp_array(
            [_cpp_port(item) for item in factory["outputs"]], 2, "no_port"
        )
        parameters = _cpp_array(
            ['"' + item + '"' for item in factory["parameter_facets"]],
            4,
            '""',
        )
        lines.extend(
            [
                "    {",
                f'        "{factory["role"]}", Role::{factory["role"]}, "{contract["component_contract_id"]}",',
                f'        "{contract["content_hash"]}",',
                f'        "{binding["implementation_id"]}",',
                f'        "{binding["content_hash"]}",',
                f'        "{factory["factory_id"]}",',
                f"        {inputs}, {len(factory['inputs'])},",
                f"        {outputs}, {len(factory['outputs'])},",
                f"        {parameters}, {len(factory['parameter_facets'])},",
                "        "
                f"{factory['state']['size_bytes']}, {factory['state']['alignment_bytes']}, "
                f"{lifecycle['prepare_symbol']}, {lifecycle['reset_symbol']}, "
                f"{lifecycle['event_symbol']}, {lifecycle['process_symbol']},",
                "    },",
            ]
        )
    lines.extend(["}};", ""])
    return "\n".join(lines)


def _cpp_source_bytes(root: Path, manifest: Mapping[str, Any]) -> bytes:
    source = (root / CPP_OUTPUT).read_text(encoding="utf-8")
    pattern = re.compile(
        r"const std::array<FactoryDescriptor, 7> kFactories\{\{.*?^\}\};\n"
        r'|#include "generated_native_registry_v1\.inc"\n',
        re.MULTILINE | re.DOTALL,
    )
    rendered, count = pattern.subn(_cpp_registry_text(manifest), source, count=1)
    if count != 1:
        raise RegistryGenerationError("NATIVE_REGISTRY_CPP_REGION_MISSING")
    return rendered.encode("utf-8")


def _schema_bytes(
    root: Path, path: Path, factory_ids: list[str], location: tuple[str, ...]
) -> bytes:
    value = copy.deepcopy(_load_json(root, path))
    cursor: Any = value
    for key in location:
        cursor = cursor[key]
    cursor["enum"] = sorted(factory_ids)
    return _canonical_bytes(value)


def generated(root: Path = ROOT) -> tuple[dict[Path, bytes], dict[str, Any]]:
    root = root.resolve()
    manifest = _validate_manifest(root, _load_json(root, MANIFEST_PATH))
    factory_ids = [item["factory_id"] for item in manifest["factories"]]
    outputs = {
        PYTHON_OUTPUT: _python_bytes(manifest),
        CPP_OUTPUT: _cpp_source_bytes(root, manifest),
        PACKAGE_SCHEMA: _schema_bytes(
            root,
            PACKAGE_SCHEMA,
            factory_ids,
            ("properties", "nodes", "items", "properties", "factory_id"),
        ),
        OBSERVATION_SCHEMA: _schema_bytes(
            root,
            OBSERVATION_SCHEMA,
            factory_ids,
            (
                "properties",
                "graph_execution",
                "properties",
                "factory_instance_counts",
                "items",
                "properties",
                "factory_id",
            ),
        ),
    }
    summary = {
        "schema_version": "task033-phase3-generation-summary-v1",
        "status": "valid",
        "registry_version": manifest["registry_version"],
        "provider_reference": manifest["provider_reference"],
        "factory_count": len(manifest["factories"]),
        "factory_ids": sorted(factory_ids),
        "generated_outputs": [item.as_posix() for item in sorted(outputs)],
        "semantic_record_or_provider_allocated": False,
        "runtime_behavior_changed": False,
        "device_ui_or_publication_performed": False,
    }
    return outputs, summary


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    arguments = parser.parse_args()
    try:
        outputs, summary = generated()
        stale = [
            path.as_posix()
            for path, expected in sorted(outputs.items())
            if not (ROOT / path).is_file() or (ROOT / path).read_bytes() != expected
        ]
        if arguments.check and stale:
            raise RegistryGenerationError(
                "NATIVE_REGISTRY_GENERATED_OUTPUT_STALE: " + ", ".join(stale)
            )
        if arguments.write:
            for path, payload in sorted(outputs.items()):
                destination = ROOT / path
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(payload)
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        return 0
    except (OSError, RegistryGenerationError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
