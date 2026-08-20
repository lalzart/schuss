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

CONSUMERS = (
    "research/prototypes/cinderwheel",
    "research/prototypes/tide-pit-gills",
    "research/prototype_support/instrument_lab/fixtures/smoke",
)
SHARED_SOURCE_NAMES = {
    "bounded_midi.hpp", "host_bridge.hpp", "renderer_artifacts.hpp",
    "renderer_artifacts.cpp", "SchussInstrumentLab.cmake",
}


def validate_repository(root: Path) -> None:
    handoff_errors = validate_handoff(root / "docs/tasks/036-INSTRUMENT-LAB-HANDOFF.json")
    if handoff_errors:
        raise ContractError("TASK036_HANDOFF_INVALID", handoff_errors[0])
    for relative in CONSUMERS:
        validate_consumer(root, root / relative, write=False, check_derived=True)

    lab = root / "research/prototype_support/instrument_lab"
    spec = validate_spec(load_json(lab / "fixtures/smoke-spec.json"))
    expected = render_tree(lab / "templates", spec)
    compare_tree(lab / "fixtures/smoke/generated", expected)

    for prototype in (root / "research/prototypes/cinderwheel", root / "research/prototypes/tide-pit-gills"):
        duplicates = sorted(
            path.relative_to(root).as_posix()
            for path in prototype.rglob("*")
            if path.is_file() and path.name in SHARED_SOURCE_NAMES
        )
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
