#!/usr/bin/env python3
"""Cheap repository-wide Instrument Lab contract/freshness gate."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from common import ContractError, load_json  # noqa: E402
from new_prototype import compare_tree, render_tree, validate_spec  # noqa: E402
from validate_prototype import validate_consumer  # noqa: E402
from tools.source_packages.validate_task036_handoff import validate_handoff  # noqa: E402

SMOKE_CONSUMER = "research/prototype_support/instrument_lab/fixtures/smoke"
SHARED_SOURCE_NAMES = {
    "bounded_midi.hpp", "host_bridge.hpp", "renderer_artifacts.hpp",
    "renderer_artifacts.cpp", "SchussInstrumentLab.cmake",
}


def discover_consumers(root: Path) -> tuple[str, ...]:
    prototypes = root / "research/prototypes"
    if not prototypes.is_dir() or prototypes.is_symlink():
        raise ContractError("MISSING_CONSUMER_ROOT", "research/prototypes")
    consumers: list[str] = []
    for candidate in sorted(prototypes.iterdir(), key=lambda path: path.name):
        if candidate.is_symlink():
            raise ContractError("CONSUMER_SYMLINK", candidate.relative_to(root).as_posix())
        if candidate.is_dir() and (candidate / "prototype-index.json").is_file():
            consumers.append(candidate.relative_to(root).as_posix())
    smoke = root / SMOKE_CONSUMER
    if not (smoke / "prototype-index.json").is_file():
        raise ContractError("MISSING_SMOKE_CONSUMER", SMOKE_CONSUMER)
    consumers.append(SMOKE_CONSUMER)
    return tuple(consumers)


def shared_implementation_duplicates(root: Path, consumers: tuple[str, ...]) -> list[str]:
    duplicates: list[str] = []
    for relative in consumers:
        if relative == SMOKE_CONSUMER:
            continue
        prototype = root / relative
        duplicates.extend(
            path.relative_to(root).as_posix()
            for path in prototype.rglob("*")
            if path.is_file() and path.name in SHARED_SOURCE_NAMES
        )
    return sorted(duplicates)


def validate_repository(root: Path) -> None:
    handoff_errors = validate_handoff(root / "docs/tasks/036-INSTRUMENT-LAB-HANDOFF.json")
    if handoff_errors:
        raise ContractError("TASK036_HANDOFF_INVALID", handoff_errors[0])
    consumers = discover_consumers(root)
    prototype_ids: set[str] = set()
    for relative in consumers:
        validate_consumer(root, root / relative, write=False, check_derived=True)
        prototype_id = load_json(root / relative / "prototype-index.json")["prototype_id"]
        if prototype_id in prototype_ids:
            raise ContractError("DUPLICATE_PROTOTYPE_ID", prototype_id)
        prototype_ids.add(prototype_id)

    lab = root / "research/prototype_support/instrument_lab"
    spec = validate_spec(load_json(lab / "fixtures/smoke-spec.json"))
    expected = render_tree(lab / "templates", spec)
    compare_tree(lab / "fixtures/smoke/generated", expected)

    duplicates = shared_implementation_duplicates(root, consumers)
    if duplicates:
        raise ContractError("DUPLICATE_SHARED_IMPLEMENTATION", ", ".join(duplicates))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        validate_repository(args.repo_root.resolve())
    except ContractError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print("Instrument Lab repository contracts: current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
