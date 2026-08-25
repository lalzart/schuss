#!/usr/bin/env python3
"""Inspect or authenticate the uninstalled Pamplist Release VST3 bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import subprocess
import sys
from typing import Any


VST3_ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE = VST3_ROOT.parent
REPO_ROOT = VST3_ROOT.parents[3]
DEFAULT_BUILD = REPO_ROOT / "build/pamplist-vst3-task047-release"
TASK047_CONTRACT = (
    REPO_ROOT / "research/prototypes/vst3-resampling/contract-r01"
)
RECEIPT = TASK047_CONTRACT / "pamplist-vst3-build.json"
JUCE_MANIFEST = (
    REPO_ROOT
    / "research/prototype_support/instrument_lab/juce-8.0.15-source-tree.json"
)
SOURCE_VERIFIER = PROTOTYPE / "tests/verify_source_authority.py"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(command: list[str]) -> str:
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(command)}\n"
            + completed.stdout.strip()
        )
    return completed.stdout.strip()


def source_receipt() -> dict[str, Any]:
    return json.loads(run([sys.executable, str(SOURCE_VERIFIER), "--json"]))


def input_paths() -> list[Path]:
    roots = [
        VST3_ROOT,
        PROTOTYPE / "CMakeLists.txt",
        PROTOTYPE / "include",
        PROTOTYPE / "src",
        PROTOTYPE / "source-dependencies.json",
        PROTOTYPE / "THIRD_PARTY_NOTICES.md",
        REPO_ROOT / "research/proposals/pamplist-vst3-local.md",
        REPO_ROOT / "research/proposals/tide-pit-pamplist-vst3-resampling.md",
        REPO_ROOT
        / "research/prototype_support/instrument_lab/include/schuss/instrument_lab/fixed_rate_resampler.hpp",
        PROTOTYPE / "contract-vst3-r01/implementation-contract.json",
        PROTOTYPE / "contract-vst3-r01/source-equivalence.json",
        PROTOTYPE / "contract-vst3-r01/control-map.json",
        PROTOTYPE / "contract-vst3-r01/experiment.json",
        PROTOTYPE / "contract-vst3-r01/state-matrix.md",
        PROTOTYPE / "contract-vst3-r01/validation-plan.json",
        TASK047_CONTRACT / "implementation-contract.json",
        TASK047_CONTRACT / "source-equivalence.json",
        TASK047_CONTRACT / "control-map.json",
        TASK047_CONTRACT / "experiment.json",
        TASK047_CONTRACT / "state-matrix.md",
        TASK047_CONTRACT / "validation-plan.json",
        TASK047_CONTRACT / "reuse-fingerprints.json",
        JUCE_MANIFEST,
    ]
    result: list[Path] = []
    for root in roots:
        if root.is_file():
            result.append(root)
            continue
        result.extend(
            path
            for path in root.rglob("*")
            if path.is_file()
            and "__pycache__" not in path.parts
            and path.suffix != ".pyc"
        )
    return sorted(
        set(result), key=lambda path: path.relative_to(REPO_ROOT).as_posix()
    )


def input_fingerprint() -> str:
    digest = hashlib.sha256()
    for path in input_paths():
        relative = path.relative_to(REPO_ROOT).as_posix().encode("utf-8")
        digest.update(relative + b"\0" + path.read_bytes() + b"\0")
    return digest.hexdigest()


def bundle_path(build: Path) -> Path:
    return build / "pamplist-vst3_artefacts/Release/VST3/Pamplist.vst3"


def bundle_file_receipts(bundle: Path) -> tuple[list[dict[str, Any]], str]:
    files = sorted(path for path in bundle.rglob("*") if path.is_file())
    digest = hashlib.sha256()
    receipts: list[dict[str, Any]] = []
    for path in files:
        relative = path.relative_to(bundle).as_posix()
        content_sha = sha256(path)
        digest.update(relative.encode("utf-8") + b"\0")
        digest.update(path.read_bytes() + b"\0")
        receipts.append(
            {"bytes": path.stat().st_size, "path": relative, "sha256": content_sha}
        )
    return receipts, digest.hexdigest()


def document(build: Path) -> dict[str, Any]:
    bundle = bundle_path(build)
    binary = bundle / "Contents/MacOS/Pamplist"
    info_path = bundle / "Contents/Info.plist"
    module_path = bundle / "Contents/Resources/moduleinfo.json"
    for required in (bundle, binary, info_path, module_path):
        if not required.exists():
            raise RuntimeError(f"Release VST3 artifact is missing: {required}")

    run(
        [
            "ctest",
            "--test-dir",
            str(build),
            "-C",
            "Release",
            "--output-on-failure",
            "-R",
            "^pamplist_vst3_",
        ]
    )
    run(["/usr/bin/codesign", "--verify", "--deep", "--strict", str(bundle)])
    architectures = run(["/usr/bin/lipo", "-archs", str(binary)]).split()
    if architectures != ["arm64"]:
        raise RuntimeError(f"expected one arm64 slice, observed {architectures}")
    binary_kind = run(["/usr/bin/file", "-b", str(binary)])
    if "Mach-O 64-bit bundle arm64" not in binary_kind:
        raise RuntimeError(f"unexpected VST3 binary kind: {binary_kind}")

    with info_path.open("rb") as stream:
        info = plistlib.load(stream)
    expected_info = {
        "CFBundleDisplayName": "Pamplist",
        "CFBundleExecutable": "Pamplist",
        "CFBundleIdentifier": "dev.schuss.pamplist.vst3.local",
        "CFBundlePackageType": "BNDL",
        "CFBundleShortVersionString": "0.6.0",
        "CFBundleVersion": "0.6.0",
    }
    for key, value in expected_info.items():
        if info.get(key) != value:
            raise RuntimeError(f"Info.plist drift for {key}: {info.get(key)!r}")

    module_text = module_path.read_text(encoding="utf-8")
    for required_text in (
        '"Name": "Pamplist"',
        '"Vendor": "Schuss"',
        '"Version": "0.6.0"',
        '"Category": "Audio Module Class"',
        '"Category": "Component Controller Class"',
        '"Instrument"',
        '"Synth"',
    ):
        if required_text not in module_text:
            raise RuntimeError(f"VST3 module metadata drift: {required_text}")
    if module_text.count('"Category": "Audio Module Class"') != 1:
        raise RuntimeError("VST3 module does not expose exactly one audio class")

    files, tree_sha = bundle_file_receipts(bundle)
    relative_bundle = bundle.relative_to(REPO_ROOT).as_posix()
    return {
        "artifact": {
            "architectures": architectures,
            "binary_kind": binary_kind,
            "bundle_path": relative_bundle,
            "bundle_tree_sha256": tree_sha,
            "files": files,
        },
        "claims": {
            "ableton_launched": False,
            "app_or_endpoint_opened": False,
            "bundle_installed": False,
            "codesign_kind": "local-ad-hoc-seal-only",
            "distribution_approved": False,
            "listening_performed": False,
            "module_host_offline_passed": True,
            "module_host_rates_hz": [44100, 48000, 96000],
            "target_built": True,
        },
        "input_fingerprint_sha256": input_fingerprint(),
        "juce_manifest": {
            "path": JUCE_MANIFEST.relative_to(REPO_ROOT).as_posix(),
            "sha256": sha256(JUCE_MANIFEST),
        },
        "parameter_contract": {
            "adapter_parameters": 179,
            "musical_parameters": 178,
            "schema": "schuss-pamplist-vst3-state-v1",
        },
        "resampling_contract": {
            "bypass_host_rate_hz": 48000,
            "core_rate_hz": 48000,
            "host_latency_frames": {
                "32000": 44,
                "44100": 60,
                "48000": 0,
                "88200": 120,
                "96000": 130,
                "176400": 239,
                "192000": 260,
            },
            "maximum_non_bypass_callback_frames": 8192,
            "supported_host_rates_hz": [
                32000,
                44100,
                48000,
                88200,
                96000,
                176400,
                192000,
            ],
        },
        "schema_version": "pamplist-fixed-rate-vst3-build-v1",
        "source_authority": source_receipt(),
        "status": "passed",
        "target": "pamplist-vst3_VST3",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--inspect", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--build-dir", type=Path, default=DEFAULT_BUILD)
    arguments = parser.parse_args()
    try:
        observed = document(arguments.build_dir.resolve())
        if arguments.inspect:
            print(json.dumps(observed, indent=2, sort_keys=True))
        else:
            retained = json.loads(RECEIPT.read_text(encoding="utf-8"))
            if retained != observed:
                raise RuntimeError("retained VST3 build receipt drifted")
            print(
                "Pamplist Release VST3 receipt passed; the bundle remains "
                "uninstalled and Ableton, endpoints, and listening were not opened"
            )
    except (OSError, RuntimeError, json.JSONDecodeError) as error:
        print(f"Pamplist VST3 build validation failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
