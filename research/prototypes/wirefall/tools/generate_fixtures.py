#!/usr/bin/env python3
"""Generate Wirefall control descriptors and literal condition fixtures."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


CONDITION_ORDER = (
    "WF01_TENSION_OPEN",
    "WF02_VOID",
    "WF03_SHADOW",
    "CMP01_SQUARE",
    "CMP02_PARALLEL_LOW",
)

CPP_KEYWORDS = {
    "alignas", "alignof", "and", "and_eq", "asm", "auto", "bitand",
    "bitor", "bool", "break", "case", "catch", "char", "char16_t",
    "char32_t", "class", "compl", "concept", "const", "consteval",
    "constexpr", "constinit", "const_cast", "continue", "co_await",
    "co_return", "co_yield", "decltype", "default", "delete", "do",
    "double", "dynamic_cast", "else", "enum", "explicit", "export",
    "extern", "false", "float", "for", "friend", "goto", "if", "inline",
    "int", "long", "mutable", "namespace", "new", "noexcept", "not",
    "not_eq", "nullptr", "operator", "or", "or_eq", "private", "protected",
    "public", "register", "reinterpret_cast", "requires", "return", "short",
    "signed", "sizeof", "static", "static_assert", "static_cast", "struct",
    "switch", "template", "this", "thread_local", "throw", "true", "try",
    "typedef", "typeid", "typename", "union", "unsigned", "using", "virtual",
    "void", "volatile", "wchar_t", "while", "xor", "xor_eq",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def identifier(name: str) -> str:
    result = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    if not result or result[0].isdigit():
        raise ValueError(f"invalid generated identifier: {name}")
    if result in CPP_KEYWORDS:
        result += "_control"
    return result


def cpp_string(value: object) -> str:
    return json.dumps(str(value), ensure_ascii=True)


def selector_for(control: str, assignments: list[dict[str, object]]) -> str:
    for assignment in assignments:
        controls = str(assignment["public_control"]).split(" and ")
        if control in controls:
            return str(assignment["selector"])
    raise ValueError(f"no surface selector for {control}")


def render_header(control_map: dict[str, object], control_hash: str) -> str:
    bindings = control_map["semantic_bindings"]
    assignments = control_map["surface_assignments"]
    if not isinstance(bindings, list) or not isinstance(assignments, list):
        raise ValueError("invalid control-map collections")
    rows: list[tuple[str, str, str, str, str]] = []
    seen: set[str] = set()
    for binding in bindings:
        if not isinstance(binding, dict):
            raise ValueError("invalid semantic binding")
        name = str(binding["public_control"])
        enum_name = identifier(name)
        if enum_name in seen:
            raise ValueError(f"duplicate control: {name}")
        seen.add(enum_name)
        default = binding.get("default", binding.get("default_ms", binding.get("default_percent", binding.get("default_bpm", "action"))))
        rows.append((enum_name, name, selector_for(name, assignments), str(default), str(binding["semantic_transform"])))

    lines = [
        "#pragma once",
        "",
        "#include <array>",
        "#include <cstddef>",
        "#include <string_view>",
        "",
        "namespace wirefall {",
        "",
        f'inline constexpr std::string_view kControlMapSha256{{"{control_hash}"}};',
        "",
        "enum class PublicControl : std::size_t {",
    ]
    lines.extend(f"    {row[0]}," for row in rows)
    lines.extend(["    count,", "};", "", "struct PublicControlDescriptor {", "    PublicControl id;", "    std::string_view name;", "    std::string_view selector;", "    std::string_view default_value;", "    std::string_view semantic_transform;", "};", "", f"inline constexpr std::array<PublicControlDescriptor, {len(rows)}> kPublicControlDescriptors{{{{"])
    for enum_name, name, selector, default, transform in rows:
        lines.append(f"    {{PublicControl::{enum_name}, {cpp_string(name)}, {cpp_string(selector)}, {cpp_string(default)}, {cpp_string(transform)}}},")
    lines.extend(["}};", "", "static_assert(kPublicControlDescriptors.size() == static_cast<std::size_t>(PublicControl::count));", "", "}  // namespace wirefall", ""])
    return "\n".join(lines)


def fixture_value(event: dict[str, object], key: str) -> str:
    value = event.get("start_value", "") if key == "value" and key not in event else event.get(key, "")
    if isinstance(value, float):
        return format(value, ".17g")
    return str(value)


def render_condition(condition: dict[str, object]) -> str:
    lines = [
        "schema_version=wirefall-condition-v1",
        f"id={condition['id']}",
        f"mechanism={condition['mechanism']}",
        f"duration_frames={condition['duration_frames']}",
        "events=sample_index|ingress_sequence|action|control|value|end_sample_index|end_value",
    ]
    events = condition.get("events")
    if not isinstance(events, list):
        raise ValueError(f"invalid events for {condition['id']}")
    for event in events:
        if not isinstance(event, dict):
            raise ValueError("invalid event")
        lines.append("|".join((
            fixture_value(event, "sample_index"),
            fixture_value(event, "ingress_sequence"),
            fixture_value(event, "action"),
            fixture_value(event, "control"),
            fixture_value(event, "value"),
            fixture_value(event, "end_sample_index"),
            fixture_value(event, "end_value"),
        )))
    return "\n".join(lines) + "\n"


def expected_tree(repo_root: Path) -> dict[Path, str]:
    prototype = repo_root / "research/prototypes/wirefall"
    control_path = prototype / "contract/control-map.json"
    experiment_path = prototype / "contract/experiment.json"
    control_map = json.loads(control_path.read_text(encoding="utf-8"))
    experiment = json.loads(experiment_path.read_text(encoding="utf-8"))
    conditions = experiment.get("conditions")
    if not isinstance(conditions, list):
        raise ValueError("experiment conditions missing")
    by_id = {str(item["id"]): item for item in conditions if isinstance(item, dict)}
    if tuple(by_id) != CONDITION_ORDER:
        raise ValueError("condition order or IDs drifted")
    output = prototype / "generated"
    tree: dict[Path, str] = {
        output / "include/wirefall/control_descriptor.hpp": render_header(control_map, sha256(control_path)),
    }
    for condition_id in CONDITION_ORDER:
        tree[output / f"conditions/{condition_id}.fixture"] = render_condition(by_id[condition_id])
    generation = {
        "condition_ids": list(CONDITION_ORDER),
        "control_map": {"path": "research/prototypes/wirefall/contract/control-map.json", "sha256": sha256(control_path)},
        "experiment": {"path": "research/prototypes/wirefall/contract/experiment.json", "sha256": sha256(experiment_path)},
        "schema_version": "wirefall-generated-fixtures-v1",
    }
    tree[output / "generation.json"] = canonical_json(generation)
    return tree


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = args.repo_root.resolve()
    try:
        tree = expected_tree(root)
        for path, content in tree.items():
            if args.write:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8", newline="\n")
            elif not path.is_file() or path.read_text(encoding="utf-8") != content:
                raise ValueError(f"stale generated artifact: {path.relative_to(root)}")
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"WIREfall fixture generation failed: {error}", file=sys.stderr)
        return 2
    print("Wirefall generated fixtures: current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
