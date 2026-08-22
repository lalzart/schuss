#!/usr/bin/env python3
"""Focused Wirefall proposal, bundle, coefficient, and fixture checks."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import subprocess
import sys
from pathlib import Path


EXPECTED_PROPOSAL = "cf9b5f58e50856a9d38d754ee476ced58c52473bb9f9ff1216c75e7ca28707b8"
EXPECTED_FIR_BYTES = "a99f4e674be713a0b0f2405711cff20b6a0676a13f4af63380165c4984e70b1a"
EXPECTED_CONDITIONS = [
    "WF01_TENSION_OPEN",
    "WF02_VOID",
    "WF03_SHADOW",
    "CMP01_SQUARE",
    "CMP02_PARALLEL_LOW",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    prototype = root / "research/prototypes/wirefall"
    contract = prototype / "contract"
    try:
        ready = json.loads((contract / "READY_BUNDLE.json").read_text(encoding="utf-8"))
        for entry in ready["frozen_inputs"]:
            path = root / entry["path"]
            require(digest(path) == entry["sha256"], f"frozen authority drift: {entry['path']}")
        require(digest(root / "research/proposals/wirefall.md") == EXPECTED_PROPOSAL, "proposal fingerprint drift")

        implementation = json.loads((contract / "implementation-contract.json").read_text(encoding="utf-8"))
        require(implementation["status"] == "ready", "implementation contract not ready")
        require(implementation["proposal"]["approval"]["state"] == "approved", "proposal not approved")
        require(implementation["working_definition"]["evidence_level"] == "host-signal", "evidence ceiling drift")
        require(implementation["work_type"] == "new-design", "work lane drift")

        fir = json.loads((contract / "wirefall-fir-63.json").read_text(encoding="utf-8"))
        words = [int(value, 16) for value in fir["coefficient_words_hex"]]
        require(len(words) == 63, "FIR tap count drift")
        require(all(words[index] == words[-1 - index] for index in range(len(words))), "FIR symmetry drift")
        byte_stream = b"".join(struct.pack("<I", word) for word in words)
        require(hashlib.sha256(byte_stream).hexdigest() == EXPECTED_FIR_BYTES, "FIR byte fingerprint drift")

        experiment = json.loads((contract / "experiment.json").read_text(encoding="utf-8"))
        conditions = experiment["conditions"]
        require([item["id"] for item in conditions] == EXPECTED_CONDITIONS, "condition ID or order drift")
        require(experiment["supported_block_frames"] == [1, 16, 64, 257, 512], "block matrix drift")
        require(experiment["seed"] == 0x57495245, "seed drift")
        require(all(item["duration_frames"] == 1_536_000 for item in conditions), "condition duration drift")

        control = json.loads((contract / "control-map.json").read_text(encoding="utf-8"))
        selectors = [item["selector"] for item in control["surface_assignments"]]
        expected_selectors = [f"device-input-{index:06d}" for index in range(1, 17)]
        require(selectors == expected_selectors, "Gills selector coverage drift")
        require(len(control["semantic_bindings"]) == 19, "semantic control count drift")
        require(control["source_of_truth"]["strategy"] == "generate", "control source strategy drift")

        state = (contract / "state-matrix.md").read_text(encoding="utf-8")
        require("> Status: ready" in state and "UNRESOLVED" not in state, "state matrix not ready")

        command = [
            sys.executable,
            str(prototype / "tools/generate_fixtures.py"),
            "--repo-root",
            str(root),
            "--check",
        ]
        completed = subprocess.run(command, cwd=root, check=False, text=True, capture_output=True)
        require(completed.returncode == 0, completed.stdout + completed.stderr)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"Wirefall contract fixture validation failed: {error}", file=sys.stderr)
        return 2
    print("Wirefall contract fixtures: valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
