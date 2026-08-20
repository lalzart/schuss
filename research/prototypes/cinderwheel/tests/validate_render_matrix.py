#!/usr/bin/env python3
"""Run and verify the deterministic Cinderwheel reference-render matrix."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


BLOCKS = (64, 128, 512)
MANIFEST = "cinderwheel-observation-manifest.json"
CEILING = 0.891250938
MAXIMUM_ABSOLUTE_DC = 1.0e-4


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_renderer(executable: Path, output: Path, block: int) -> None:
    completed = subprocess.run(
        [str(executable), "--output-dir", str(output), "--block", str(block)],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise AssertionError(
            f"renderer failed for block {block}:\n{completed.stdout}{completed.stderr}"
        )


def bytes_for(directory: Path, suffixes: tuple[str, ...]) -> dict[str, bytes]:
    return {
        path.name: path.read_bytes()
        for path in sorted(directory.iterdir())
        if path.name.endswith(suffixes)
    }


def validate_manifest(directory: Path, block: int) -> dict[str, object]:
    document = json.loads((directory / MANIFEST).read_text(encoding="utf-8"))
    require(document["block_frames"] == block, "manifest block size drifted")
    require(document["condition_count"] == 6, "renderer must enumerate six literal conditions")
    require(document["cycle_count"] == 32, "reference gesture must contain 32 cycles")
    require(document["sample_rate_hz"] == 48000, "reference render must be 48 kHz")
    require(
        document["determinism"]["clean_corroded_ledger_bytes_equal"],
        "clean/corroded ledgers differ",
    )
    require(
        document["determinism"]["clean_corroded_audio_distinct"],
        "clean/corroded audio is not distinct",
    )
    for result in document["results"]:
        measurements = result["measurements"]
        diagnostics = result["diagnostics"]
        require(measurements["finite"], f"non-finite output in {result['stem']}")
        require(measurements["peak"] <= CEILING, f"ceiling exceeded in {result['stem']}")
        require(
            abs(measurements["dc_mean_left"]) < MAXIMUM_ABSOLUTE_DC
            and abs(measurements["dc_mean_right"]) < MAXIMUM_ABSOLUTE_DC,
            f"DC criterion failed in {result['stem']}",
        )
        require(diagnostics["midi_events_dropped"] == 0, "reference MIDI was dropped")
        require(diagnostics["non_finite_clears"] == 0, "reference DSP state was cleared")
        require(diagnostics["event_sink_overflows"] == 0, "reference event sink overflowed")
    ember_zero = document["results"][2]
    require(ember_zero["diagnostics"]["afterstrikes"] == 0, "Ember zero emitted afterstrikes")
    require(
        document["results"][4]["diagnostics"]["event_cap_hits"] > 0,
        "high-Ember Bloom condition did not exercise cap saturation",
    )
    return document


def main() -> None:
    require(len(sys.argv) == 2, "usage: validate_render_matrix.py RENDERER")
    executable = Path(sys.argv[1]).resolve()
    require(executable.is_file(), f"renderer does not exist: {executable}")

    with tempfile.TemporaryDirectory(prefix="cinderwheel-render-matrix-") as temporary:
        root = Path(temporary)
        outputs: dict[int, Path] = {}
        for block in BLOCKS:
            output = root / f"block-{block}"
            run_renderer(executable, output, block)
            validate_manifest(output, block)
            outputs[block] = output

        reference = bytes_for(outputs[128], (".wav", ".ledger.csv"))
        require(len(reference) == 12, "expected six WAV and six ledger artifacts")
        for block in (64, 512):
            require(
                bytes_for(outputs[block], (".wav", ".ledger.csv")) == reference,
                f"block-{block} artifacts differ from block-128",
            )

        repeated = root / "repeat-128"
        run_renderer(executable, repeated, 128)
        validate_manifest(repeated, 128)
        require(
            bytes_for(repeated, (".wav", ".ledger.csv", ".json"))
            == bytes_for(outputs[128], (".wav", ".ledger.csv", ".json")),
            "fresh-process block-128 repeat drifted",
        )
        manifest_sha = hashlib.sha256((outputs[128] / MANIFEST).read_bytes()).hexdigest()
        print(
            "validate_render_matrix: passed "
            f"(4 runs, 12 cross-block artifacts, manifest sha256 {manifest_sha})"
        )


if __name__ == "__main__":
    main()
