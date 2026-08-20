#!/usr/bin/env python3
"""Run the source-bound Tide Pit render matrix without opening any devices."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


BLOCKS = (16, 64, 128, 512)
MANIFEST = "render-manifest.json"
EXPERIMENT = Path(__file__).resolve().parents[1] / "experiment.json"
EXPERIMENT_SHA256 = "f8baac381d1e83f2e5db6ee4b56988299d5ae7b3e5b1b2ff4bcdfd1a0459c9fd"
EXPERIMENT_DOCUMENT = json.loads(EXPERIMENT.read_text(encoding="utf-8"))
TOLERANCES = EXPERIMENT_DOCUMENT["tolerances"]
CANONICAL_SHA256 = TOLERANCES["canonical_clean_sha256"]
CANONICAL_BYTES = TOLERANCES["canonical_clean_bytes"]
CANONICAL_PEAK_Q27 = TOLERANCES["canonical_clean_peak_q27"]
CANONICAL_RMS_Q27 = TOLERANCES["canonical_clean_rms_q27"]
MAXIMUM_NORMALIZED_PEAK = TOLERANCES["normalized_peak_maximum"]
EXPECTED_ARTIFACTS = {
    "parameter-extremes.wav",
    "performance-state-trace.wav",
    "render-manifest.json",
    "source-bound-clean-reference.q27le",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_renderer(
    executable: Path,
    output: Path,
    block: int,
    *,
    experiment: Path = EXPERIMENT,
    expect_success: bool = True,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        [
            str(executable),
            "--output-dir",
            str(output),
            "--block",
            str(block),
            "--experiment",
            str(experiment),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if expect_success and completed.returncode != 0:
        raise AssertionError(
            f"renderer failed for block {block}:\n"
            f"{completed.stdout}{completed.stderr}"
        )
    if not expect_success and completed.returncode == 0:
        raise AssertionError(f"renderer unexpectedly succeeded for block {block}")
    return completed


def normalized_manifest(document: dict[str, object]) -> dict[str, object]:
    normalized = json.loads(json.dumps(document))
    normalized.pop("block_frames", None)
    return normalized


def validate_manifest(directory: Path, block: int) -> dict[str, object]:
    actual_artifacts = {path.name for path in directory.iterdir() if path.is_file()}
    require(actual_artifacts == EXPECTED_ARTIFACTS, "render artifact set drifted")

    document = json.loads((directory / MANIFEST).read_text(encoding="utf-8"))
    require(
        document["schema_version"] == "tide-pit-render-manifest-v1",
        "manifest schema drifted",
    )
    require(document["block_frames"] == block, "manifest block size drifted")
    require(document["sample_rate_hz"] == 48_000, "renderer must stay at 48 kHz")
    require(document["condition_count"] == 3, "renderer must enumerate three JSON conditions")
    require(
        document["experiment"]["sha256"] == EXPERIMENT_SHA256,
        "experiment fingerprint drifted",
    )
    require(
        document["canonical_reference"]["expected_sha256"] == CANONICAL_SHA256,
        "canonical expected hash drifted",
    )
    require(
        document["canonical_reference"]["matches"],
        "canonical source reference did not match",
    )
    require(
        document["evidence_boundary"]["offline_host_signal_only"],
        "renderer did not retain its evidence boundary",
    )
    require(
        not document["evidence_boundary"]["physical_device_opened"],
        "offline renderer claims a physical device",
    )

    results = {result["id"]: result for result in document["results"]}
    require(
        set(results)
        == {
            "parameter-extremes",
            "performance-state-trace",
            "source-bound-clean-reference",
        },
        "render condition IDs drifted",
    )
    canonical = results["source-bound-clean-reference"]
    require(canonical["q27"]["bytes"] == CANONICAL_BYTES, "canonical byte count drifted")
    require(canonical["q27"]["sha256"] == CANONICAL_SHA256, "canonical hash drifted")
    require(canonical["measurements"]["peak_q27"] == CANONICAL_PEAK_Q27, "canonical peak drifted")
    require(
        abs(canonical["measurements"]["rms_q27"] - CANONICAL_RMS_Q27) < 1.0e-6,
        "canonical RMS drifted",
    )
    require(
        sha256(directory / "source-bound-clean-reference.q27le") == CANONICAL_SHA256,
        "retained canonical file hash drifted",
    )

    for condition_id, result in results.items():
        measurements = result["measurements"]
        diagnostics = result["diagnostics"]
        require(measurements["finite"], f"non-finite output in {condition_id}")
        require(
            measurements["normalized_peak"] <= MAXIMUM_NORMALIZED_PEAK,
            f"normalized peak exceeded in {condition_id}",
        )
        require(
            isinstance(measurements["dc_mean_left"], (int, float))
            and isinstance(measurements["dc_mean_right"], (int, float)),
            f"raw DC measurement missing in {condition_id}",
        )
        require(diagnostics["events_dropped"] == 0, f"events dropped in {condition_id}")
        require(
            diagnostics["unsupported_process_calls"] == 0,
            f"unsupported process call in {condition_id}",
        )
        display = result["final_state"]["display_lines"]
        require(len(display) == 4, f"display line count drifted in {condition_id}")
        require(
            all(len(line.encode("utf-8")) == 21 for line in display),
            f"display width drifted in {condition_id}",
        )
    return document


def artifact_bytes(directory: Path) -> dict[str, bytes]:
    return {
        name: (directory / name).read_bytes()
        for name in sorted(EXPECTED_ARTIFACTS - {MANIFEST})
    }


def main() -> None:
    require(len(sys.argv) == 2, "usage: validate_render_matrix.py RENDERER")
    executable = Path(sys.argv[1]).resolve()
    require(executable.is_file(), f"renderer does not exist: {executable}")
    require(sha256(EXPERIMENT) == EXPERIMENT_SHA256, "checked-in experiment drifted")

    with tempfile.TemporaryDirectory(prefix="tide-pit-render-matrix-") as temporary:
        root = Path(temporary)
        outputs: dict[int, Path] = {}
        manifests: dict[int, dict[str, object]] = {}
        for block in BLOCKS:
            output = root / f"block-{block}"
            run_renderer(executable, output, block)
            manifests[block] = validate_manifest(output, block)
            outputs[block] = output

        reference_artifacts = artifact_bytes(outputs[16])
        reference_manifest = normalized_manifest(manifests[16])
        for block in BLOCKS[1:]:
            require(
                artifact_bytes(outputs[block]) == reference_artifacts,
                f"block-{block} audio artifacts differ from block-16",
            )
            require(
                normalized_manifest(manifests[block]) == reference_manifest,
                f"block-{block} normalized manifest differs from block-16",
            )

        repeated = root / "repeat-128"
        run_renderer(executable, repeated, 128)
        validate_manifest(repeated, 128)
        require(
            {
                path.name: path.read_bytes()
                for path in sorted(repeated.iterdir())
                if path.is_file()
            }
            == {
                path.name: path.read_bytes()
                for path in sorted(outputs[128].iterdir())
                if path.is_file()
            },
            "fresh-process block-128 repeat drifted",
        )

        overwrite = run_renderer(
            executable,
            outputs[128],
            128,
            expect_success=False,
        )
        require(
            "refusing to overwrite" in (overwrite.stdout + overwrite.stderr).lower(),
            "overwrite failure was not explicit",
        )

        tampered = root / "tampered-experiment.json"
        tampered.write_bytes(EXPERIMENT.read_bytes() + b"\n")
        drift = run_renderer(
            executable,
            root / "tampered-output",
            128,
            experiment=tampered,
            expect_success=False,
        )
        require(
            "experiment sha-256 mismatch" in (drift.stdout + drift.stderr).lower(),
            "experiment drift failure was not explicit",
        )

        manifest_sha = sha256(outputs[128] / MANIFEST)
        print(
            "validate_render_matrix: passed "
            f"(4 partitions, repeat, overwrite/drift negatives, manifest sha256 {manifest_sha})"
        )


if __name__ == "__main__":
    main()
