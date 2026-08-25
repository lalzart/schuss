#!/usr/bin/env python3
"""Reproduce or cheaply authenticate Layerwell's retained host-signal evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[4]
PROTOTYPE = ROOT / "research/prototypes/layerwell"
DEFAULT_RENDERER = ROOT / "build/layerwell-focused/layerwell-render"
EVIDENCE = PROTOTYPE / "contract-r02/evidence"
RENDER_ARTIFACTS = (
    "layerwell.wav",
    "event-state-trace.json",
    "panel-trace.json",
    "controller-trace.json",
    "metrics.json",
)
ARTIFACTS = RENDER_ARTIFACTS + (
    "untrimmed.wav",
    "untrimmed-comparator.json",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check() -> None:
    manifest = EVIDENCE / "SHA256SUMS"
    if not manifest.is_file():
        raise SystemExit("missing retained Layerwell SHA256SUMS")
    expected: dict[str, str] = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        fingerprint, name = line.split("  ", 1)
        expected[name] = fingerprint
    if tuple(expected) != ARTIFACTS:
        raise SystemExit("Layerwell evidence manifest names or ordering drifted")
    for name in ARTIFACTS:
        path = EVIDENCE / name
        if not path.is_file() or sha256(path) != expected[name]:
            raise SystemExit(f"Layerwell retained evidence drifted: {name}")
    metrics = json.loads((EVIDENCE / "metrics.json").read_text(encoding="utf-8"))
    if metrics["finite_samples"] != metrics["frames"] * 2:
        raise SystemExit("Layerwell retained render is not fully finite")
    if metrics["peak_absolute"] > 1.0:
        raise SystemExit("Layerwell retained render exceeds output bound")
    if not metrics["untrimmed_comparator_diverged"]:
        raise SystemExit("Layerwell falsifying comparator did not diverge")
    comparator = json.loads(
        (EVIDENCE / "untrimmed-comparator.json").read_text(encoding="utf-8")
    )
    if comparator.get("schema") != "layerwell-untrimmed-comparator-v1":
        raise SystemExit("Layerwell comparator schema drifted")
    if comparator.get("sample_exact_wav_sha256") != sha256(EVIDENCE / "layerwell.wav"):
        raise SystemExit("Layerwell comparator reference binding drifted")
    if comparator.get("untrimmed_wav_sha256") != sha256(
        EVIDENCE / "untrimmed.wav"
    ):
        raise SystemExit("Layerwell comparator candidate binding drifted")
    if comparator["sample_exact_wav_sha256"] == comparator["untrimmed_wav_sha256"]:
        raise SystemExit("Layerwell comparator artifacts do not diverge")
    print("Layerwell retained render evidence: valid")


def reproduce(renderer: Path, destination: Path) -> None:
    if not renderer.is_file():
        raise SystemExit(f"Layerwell renderer does not exist: {renderer}")
    with tempfile.TemporaryDirectory(prefix="layerwell-render-") as temporary:
        temporary_root = Path(temporary)
        hashes: dict[int, dict[str, str]] = {}
        for block in (16, 64, 128, 512):
            output = temporary_root / str(block)
            subprocess.run(
                [str(renderer), "--block", str(block), "--output-dir", str(output)],
                check=True,
                cwd=ROOT,
            )
            hashes[block] = {
                name: sha256(output / name) for name in RENDER_ARTIFACTS
            }
        reference = hashes[16]
        for block in (64, 128, 512):
            if hashes[block] != reference:
                raise SystemExit(f"Layerwell partition evidence diverged at block {block}")

        comparator_output = temporary_root / "untrimmed"
        subprocess.run(
            [
                str(renderer), "--block", "128",
                "--output-dir", str(comparator_output),
                "--untrimmed",
            ],
            check=True,
            cwd=ROOT,
        )
        comparator_wav = comparator_output / "layerwell.wav"
        if sha256(comparator_wav) == reference["layerwell.wav"]:
            raise SystemExit("Layerwell untrimmed comparator did not diverge")

        destination.mkdir(parents=True, exist_ok=True)
        canonical = temporary_root / "128"
        for name in RENDER_ARTIFACTS:
            shutil.copyfile(canonical / name, destination / name)
        shutil.copyfile(comparator_wav, destination / "untrimmed.wav")
        metrics_path = destination / "metrics.json"
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        metrics["untrimmed_comparator_diverged"] = True
        metrics_path.write_text(
            json.dumps(metrics, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        comparator = {
            "candidate_block_frames": 128,
            "diverged": True,
            "sample_exact_wav_sha256": sha256(destination / "layerwell.wav"),
            "schema": "layerwell-untrimmed-comparator-v1",
            "timing_change": "ignore the accepted [4800, 43200) trim window",
            "untrimmed_wav_sha256": sha256(destination / "untrimmed.wav"),
        }
        (destination / "untrimmed-comparator.json").write_text(
            json.dumps(comparator, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        manifest = "".join(
            f"{sha256(destination / name)}  {name}\n" for name in ARTIFACTS
        )
        (destination / "SHA256SUMS").write_text(manifest, encoding="utf-8")
    print(f"Layerwell render evidence reproduced: {destination}")


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--reproduce", action="store_true")
    parser.add_argument("--renderer", type=Path, default=DEFAULT_RENDERER)
    parser.add_argument("--output", type=Path, default=EVIDENCE)
    args = parser.parse_args()
    if args.check:
        check()
    else:
        reproduce(args.renderer.resolve(), args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
