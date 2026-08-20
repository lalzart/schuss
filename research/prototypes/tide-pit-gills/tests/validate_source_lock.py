#!/usr/bin/env python3
"""Validate vendored and optional authoritative Tide Pit source bytes."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


PROTOTYPE_ROOT = Path(__file__).resolve().parent.parent
LOCK_PATH = PROTOTYPE_ROOT / "third_party" / "SOURCE_LOCK.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def manifest_digest(files: list[dict[str, str]]) -> str:
    lines = [
        f"{entry['sha256']}  {entry['source_path']}\n".encode("utf-8")
        for entry in files
    ]
    return hashlib.sha256(b"".join(sorted(lines))).hexdigest()


def validate_group(
    *,
    name: str,
    group: dict[str, object],
    vendored_root: Path,
    source_root: Path | None,
    source_prefix,
    errors: list[str],
) -> None:
    raw_files = group.get("files")
    if not isinstance(raw_files, list) or not raw_files:
        fail(f"{name}: files must be a non-empty list", errors)
        return
    files: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, raw in enumerate(raw_files):
        if not isinstance(raw, dict):
            fail(f"{name}: files[{index}] must be an object", errors)
            continue
        path = raw.get("path")
        expected = raw.get("sha256")
        if not isinstance(path, str) or not path or Path(path).is_absolute():
            fail(f"{name}: files[{index}].path must be portable", errors)
            continue
        if path in seen:
            fail(f"{name}: duplicate path {path}", errors)
        seen.add(path)
        if (
            not isinstance(expected, str)
            or len(expected) != 64
            or any(character not in "0123456789abcdef" for character in expected)
        ):
            fail(f"{name}: invalid SHA-256 for {path}", errors)
            continue

        source_path = source_prefix(path)
        files.append({"sha256": expected, "source_path": source_path})
        relative_vendor = Path(path)
        vendor = (vendored_root / relative_vendor).resolve()
        try:
            vendor.relative_to(vendored_root.resolve())
        except ValueError:
            fail(f"{name}: vendored path escapes root: {path}", errors)
            continue
        if not vendor.is_file():
            fail(f"{name}: missing vendored file {path}", errors)
        elif sha256(vendor) != expected:
            fail(f"{name}: vendored fingerprint drifted: {path}", errors)

        if source_root is not None:
            source = (source_root / source_path).resolve()
            try:
                source.relative_to(source_root.resolve())
            except ValueError:
                fail(f"{name}: source path escapes root: {source_path}", errors)
                continue
            if not source.is_file():
                fail(f"{name}: missing authoritative file {source_path}", errors)
            elif sha256(source) != expected:
                fail(f"{name}: authoritative fingerprint drifted: {source_path}", errors)

    expected_manifest = group.get("canonical_manifest_sha256")
    actual_manifest = manifest_digest(files)
    if actual_manifest != expected_manifest:
        fail(
            f"{name}: manifest fingerprint mismatch "
            f"(expected {expected_manifest}, actual {actual_manifest})",
            errors,
        )

    actual_files = {
        path.relative_to(vendored_root).as_posix()
        for path in vendored_root.rglob("*")
        if path.is_file()
    }
    expected_files = {
        Path(entry["path"]).as_posix()
        for entry in raw_files
        if isinstance(entry, dict) and isinstance(entry.get("path"), str)
    }
    extras = sorted(actual_files - expected_files)
    if extras:
        fail(f"{name}: unexpected vendored files: {', '.join(extras)}", errors)


def validate_ported_voice(document: dict[str, object], errors: list[str]) -> None:
    overrides = document.get("port_overrides")
    if not isinstance(overrides, dict):
        fail("port_overrides must be an object", errors)
        return
    seam = overrides.get("defined_cpp_voice")
    if not isinstance(seam, dict):
        fail("port_overrides.defined_cpp_voice must be an object", errors)
        return

    source = (
        PROTOTYPE_ROOT
        / document["tide_pit"]["vendored_root"]
        / "tidepit_voice.h"
    )
    generator = PROTOTYPE_ROOT / str(seam.get("generator", ""))
    expected_source = seam.get("authoritative_sha256")
    expected_output = seam.get("generated_sha256")
    expected_replacements = seam.get("replacement_count")
    if not generator.is_file():
        fail(f"ported voice generator is missing: {generator}", errors)
        return
    if sha256(source) != expected_source:
        fail("ported voice authoritative fingerprint drifted", errors)
        return

    with tempfile.TemporaryDirectory(prefix="tide-pit-ported-voice-") as temporary:
        output = Path(temporary) / "tidepit_voice_ported.h"
        completed = subprocess.run(
            [
                sys.executable,
                str(generator),
                "--source",
                str(source),
                "--output",
                str(output),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            fail(
                "ported voice generator failed: "
                f"{completed.stdout}{completed.stderr}".strip(),
                errors,
            )
            return
        if not output.is_file() or sha256(output) != expected_output:
            fail("ported voice generated fingerprint drifted", errors)
            return

        source_lines = source.read_bytes().splitlines(keepends=True)
        output_lines = output.read_bytes().splitlines(keepends=True)
        if len(source_lines) != len(output_lines):
            fail("ported voice changed the source line count", errors)
            return
        changes = [
            (before, after)
            for before, after in zip(source_lines, output_lines)
            if before != after
        ]
        if len(changes) != expected_replacements or any(
            before.replace(b"<< 1;", b"* 2;") != after
            for before, after in changes
        ):
            fail("ported voice did not contain exactly the locked replacements", errors)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-root",
        type=Path,
        help="Optional authoritative gills-instruments repository root.",
    )
    parser.add_argument(
        "--mutable-root",
        type=Path,
        help="Optional authoritative Ksoloti repository root.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    document = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    errors: list[str] = []
    validate_group(
        name="tide_pit",
        group=document["tide_pit"],
        vendored_root=PROTOTYPE_ROOT / document["tide_pit"]["vendored_root"],
        source_root=args.source_root.resolve() if args.source_root else None,
        source_prefix=lambda path: f"projects/tide-pit-gills/{path}",
        errors=errors,
    )
    validate_ported_voice(document, errors)
    validate_group(
        name="mutable_instruments",
        group=document["mutable_instruments"],
        vendored_root=PROTOTYPE_ROOT / document["mutable_instruments"]["vendored_root"],
        source_root=args.mutable_root.resolve() if args.mutable_root else None,
        source_prefix=lambda path: path,
        errors=errors,
    )
    notices = PROTOTYPE_ROOT / "third_party" / "THIRD_PARTY_NOTICES.md"
    if not notices.is_file() or "Emilie Gillet" not in notices.read_text(encoding="utf-8"):
        fail("third-party notices are missing the Mutable attribution", errors)
    if errors:
        for error in errors:
            print(f"- {error}")
        return 1
    print("source lock: valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
