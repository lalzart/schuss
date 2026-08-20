#!/usr/bin/env python3
"""Generate a deterministic linked Instrument Lab consumer."""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

from common import ContractError, canonical_json, exact_keys, load_json

SPEC_KEYS = {
    "project_id", "prototype_id", "namespace", "lane",
    "sample_representation", "sample_rate_hz", "maximum_host_block",
    "internal_quantum", "owns_conversion",
}
TEXT_TEMPLATES = {
    "CMakeLists.txt.in": "CMakeLists.txt",
    "smoke_adapter.hpp.in": "include/{namespace}/smoke_adapter.hpp",
    "smoke_adapter.cpp.in": "src/smoke_adapter.cpp",
    "smoke_tests.cpp.in": "tests/smoke_tests.cpp",
    "juce_probe.cpp.in": "src/juce_probe.cpp",
}


def validate_spec(value: Any) -> dict[str, Any]:
    spec = exact_keys(value, SPEC_KEYS, "generator-spec")
    for key in ("project_id", "namespace"):
        if not isinstance(spec[key], str) or not re.fullmatch(r"[a-z][a-z0-9_]*", spec[key]):
            raise ContractError("INVALID_GENERATOR_IDENTIFIER", key)
    if not isinstance(spec["prototype_id"], str) or not re.fullmatch(r"[a-z][a-z0-9-]*", spec["prototype_id"]):
        raise ContractError("INVALID_PROTOTYPE_ID", "generator-spec")
    if spec["lane"] not in {"new-design", "source-reimplementation", "non-musical-smoke"}:
        raise ContractError("INVALID_LANE", str(spec["lane"]))
    if spec["sample_representation"] not in {"float32", "q27"}:
        raise ContractError("UNSUPPORTED_SAMPLE_REPRESENTATION", str(spec["sample_representation"]))
    for key in ("sample_rate_hz", "maximum_host_block"):
        if not isinstance(spec[key], int) or spec[key] <= 0:
            raise ContractError("INVALID_HOST_PROFILE", key)
    if not isinstance(spec["internal_quantum"], int) or spec["internal_quantum"] < 0:
        raise ContractError("INVALID_HOST_PROFILE", "internal_quantum")
    if not isinstance(spec["owns_conversion"], bool):
        raise ContractError("INVALID_HOST_PROFILE", "owns_conversion")
    return spec


def substitutions(spec: dict[str, Any]) -> dict[str, str]:
    return {
        "@PROJECT_ID@": spec["project_id"],
        "@NAMESPACE@": spec["namespace"],
        "@SAMPLE_ENUM@": spec["sample_representation"],
        "@SAMPLE_RATE@": str(spec["sample_rate_hz"]),
        "@MAX_BLOCK@": str(spec["maximum_host_block"]),
        "@INTERNAL_QUANTUM@": str(spec["internal_quantum"]),
        "@OWNS_CONVERSION@": "true" if spec["owns_conversion"] else "false",
    }


def render_tree(template_root: Path, spec: dict[str, Any]) -> dict[str, bytes]:
    replacements = substitutions(spec)
    result: dict[str, bytes] = {}
    for template_name, destination_pattern in TEXT_TEMPLATES.items():
        content = (template_root / template_name).read_text(encoding="utf-8")
        for token, replacement in replacements.items():
            content = content.replace(token, replacement)
        if "@" in content:
            raise ContractError("UNRESOLVED_TEMPLATE_TOKEN", template_name)
        destination = destination_pattern.format(namespace=spec["namespace"])
        result[destination] = content.encode("utf-8")
    result["generation-spec.json"] = canonical_json(spec).encode("utf-8")
    result["control-map.json"] = canonical_json({
        "assignments": [{"bytes": [176, 1], "label": "Accepted value", "range": [0, 127]}],
        "claims": {"physical_controller_evidence": False},
        "schema_version": "instrument-lab-smoke-control-map-v1",
    }).encode("utf-8")
    result["experiment.json"] = canonical_json({
        "artifact": "deterministic in-memory smoke",
        "claims": {"musical_instrument": False, "listening_evidence": False},
        "schema_version": "instrument-lab-smoke-experiment-v1",
    }).encode("utf-8")
    return result


def compare_tree(destination: Path, expected: dict[str, bytes]) -> None:
    actual_paths = {
        path.relative_to(destination).as_posix()
        for path in destination.rglob("*") if path.is_file()
    }
    if actual_paths != set(expected):
        raise ContractError(
            "STALE_GENERATED_TREE",
            f"paths differ: expected={sorted(expected)} actual={sorted(actual_paths)}",
        )
    for rel, content in expected.items():
        if (destination / rel).read_bytes() != content:
            raise ContractError("STALE_GENERATED_FILE", rel)


def write_tree(destination: Path, expected: dict[str, bytes]) -> None:
    if destination.exists() and any(destination.iterdir()):
        raise ContractError("OUTPUT_NOT_EMPTY", str(destination))
    destination.mkdir(parents=True, exist_ok=True)
    for rel, content in expected.items():
        path = destination / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--template-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        spec = validate_spec(load_json(args.spec))
        expected = render_tree(args.template_root, spec)
        if args.write:
            write_tree(args.output, expected)
        else:
            compare_tree(args.output, expected)
    except (ContractError, OSError, UnicodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(f"Instrument Lab generated tree {'current' if args.check else 'written'}: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
