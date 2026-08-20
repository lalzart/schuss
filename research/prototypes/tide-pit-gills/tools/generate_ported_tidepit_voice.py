#!/usr/bin/env python3
"""Generate the minimal defined-C++ Tide Pit voice overlay.

The authoritative vendored source remains byte-identical to Gills. Two signed
left shifts have the intended two's-complement result but are undefined in C++
when the interpolated sample is negative. Multiplication by two is defined for
the proven int16-derived range and preserves the canonical Q27 stream.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


EXPECTED_SOURCE_SHA256 = (
    "e6cd224160df87afbfda5743c5124a4600c5f3c6fe4c02df272c41916cd6566c"
)
EXPECTED_OUTPUT_SHA256 = (
    "d076fa8df10eab0fdbac0ce1cd846e54fd1fa3896bba8ad7608a0ca5202b59ea"
)
REPLACEMENTS = (
    (
        b"static_cast<int32_t>(stmlib::Mix(\n"
        b"              bore_a, bore_b, bore_fractional)) << 1;",
        b"static_cast<int32_t>(stmlib::Mix(\n"
        b"              bore_a, bore_b, bore_fractional)) * 2;",
    ),
    (
        b"static_cast<int32_t>(stmlib::Mix(\n"
        b"              jet_a, jet_b, jet_fractional)) << 1;",
        b"static_cast<int32_t>(stmlib::Mix(\n"
        b"              jet_a, jet_b, jet_fractional)) * 2;",
    ),
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def generate(source: Path) -> bytes:
    source_bytes = source.read_bytes()
    actual = sha256(source_bytes)
    if actual != EXPECTED_SOURCE_SHA256:
        raise SystemExit(
            "authoritative tidepit_voice.h fingerprint drifted: "
            f"expected {EXPECTED_SOURCE_SHA256}, actual {actual}"
        )
    result = source_bytes
    for original, replacement in REPLACEMENTS:
        if result.count(original) != 1:
            raise SystemExit("signed-shift source seam was not found exactly once")
        result = result.replace(original, replacement)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()

    generated = generate(arguments.source)
    generated_sha256 = sha256(generated)
    if generated_sha256 != EXPECTED_OUTPUT_SHA256:
        raise SystemExit(
            "ported tidepit_voice.h fingerprint drifted: "
            f"expected {EXPECTED_OUTPUT_SHA256}, actual {generated_sha256}"
        )
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    if not arguments.output.exists() or arguments.output.read_bytes() != generated:
        arguments.output.write_bytes(generated)
    else:
        # Keep build systems from rerunning an unchanged custom command because
        # its output timestamp still predates this generator.
        arguments.output.touch()
    print(
        "ported Tide Pit voice generated: "
        f"source={EXPECTED_SOURCE_SHA256} output={generated_sha256}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
