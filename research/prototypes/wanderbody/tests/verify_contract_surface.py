#!/usr/bin/env python3
"""Exhaustively compare the frozen control map with compiled descriptors."""

from __future__ import annotations

import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "contract-r01" / "control-map.json"
SOURCE = ROOT / "src" / "control_surface.cpp"


def main() -> int:
    document = json.loads(MAP.read_text(encoding="utf-8"))
    expected = [entry["control"] for entry in document["semantic_bindings"]]
    source = SOURCE.read_text(encoding="utf-8")
    actual = re.findall(r'^\s*\{"([a-z]+)",\s*"[^"]+",\s*ControlKind::', source, re.M)
    if expected != actual:
        raise SystemExit(f"control surface drift: expected={expected!r} actual={actual!r}")
    if len(actual) != 21 or len(actual) != len(set(actual)):
        raise SystemExit("control surface must contain 21 unique bindings")
    if document["source_of_truth"]["strategy"] != "exhaustive-compare":
        raise SystemExit("control map must retain exhaustive-compare strategy")
    print("Wanderbody control surface: exact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
