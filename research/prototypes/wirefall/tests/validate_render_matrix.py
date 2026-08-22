#!/usr/bin/env python3
"""Render and validate the frozen Wirefall five-condition host-signal matrix."""

from __future__ import annotations

import argparse
import array
import cmath
import csv
import hashlib
import json
import math
import shutil
import struct
import subprocess
import sys
import wave
from pathlib import Path


CANONICAL_BLOCK = 64
PARTITIONS = (1, 16, 64, 257, 512)
FFT_SIZE = 65536
CONDITION_IDS = (
    "WF01_TENSION_OPEN",
    "WF02_VOID",
    "WF03_SHADOW",
    "CMP01_SQUARE",
    "CMP02_PARALLEL_LOW",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def run_renderer(
    renderer: Path,
    fixture: Path,
    output: Path,
    block_frames: int,
    *,
    oversample_factor: int = 4,
    parallel_gain: float | None = None,
    parallel_target_rms: float | None = None,
    output_prefix: str | None = None,
) -> dict[str, object]:
    command = [
        str(renderer),
        "--fixture", str(fixture),
        "--output-dir", str(output),
        "--block-frames", str(block_frames),
        "--oversample-factor", str(oversample_factor),
    ]
    if parallel_gain is not None:
        command.extend(("--parallel-gain", format(parallel_gain, ".17g")))
    if parallel_target_rms is not None:
        command.extend(("--parallel-target-rms", format(parallel_target_rms, ".17g")))
    if output_prefix is not None:
        command.extend(("--output-prefix", output_prefix))
    completed = subprocess.run(command, check=False, text=True, capture_output=True)
    if completed.returncode != 0:
        raise ValueError(
            f"renderer failed ({completed.returncode}): {' '.join(command)}\n"
            f"{completed.stdout}{completed.stderr}"
        )
    stem = output_prefix or fixture.stem
    metrics_path = output / f"{stem}.metrics.json"
    return json.loads(metrics_path.read_text(encoding="utf-8"))


def artifact_hashes(directory: Path, stem: str) -> dict[str, str]:
    return {
        "events_csv_sha256": digest(directory / f"{stem}.events.csv"),
        "metrics_json_sha256": digest(directory / f"{stem}.metrics.json"),
        "wav_sha256": digest(directory / f"{stem}.wav"),
    }


def decode_wav(path: Path) -> tuple[array.array[float], array.array[float]]:
    with wave.open(str(path), "rb") as stream:
        require(stream.getnchannels() == 2, f"{path.name}: expected stereo")
        require(stream.getsampwidth() == 3, f"{path.name}: expected 24-bit PCM")
        require(stream.getframerate() == 48000, f"{path.name}: expected 48 kHz")
        frames = stream.getnframes()
        raw = stream.readframes(frames)
    require(len(raw) == frames * 6, f"{path.name}: truncated PCM payload")
    left = array.array("f")
    right = array.array("f")
    left_extend = left.append
    right_extend = right.append
    scale = 1.0 / 8388607.0
    for offset in range(0, len(raw), 6):
        l_value = raw[offset] | (raw[offset + 1] << 8) | (raw[offset + 2] << 16)
        r_value = raw[offset + 3] | (raw[offset + 4] << 8) | (raw[offset + 5] << 16)
        if l_value & 0x800000:
            l_value -= 0x1000000
        if r_value & 0x800000:
            r_value -= 0x1000000
        left_extend(l_value * scale)
        right_extend(r_value * scale)
    return left, right


def mono(left: array.array[float], right: array.array[float], start: int, count: int) -> list[float]:
    return [0.5 * (left[index] + right[index]) for index in range(start, start + count)]


def fft(values: list[complex]) -> None:
    size = len(values)
    require(size > 0 and size & (size - 1) == 0, "FFT length must be a power of two")
    target = 0
    for index in range(1, size):
        bit = size >> 1
        while target & bit:
            target ^= bit
            bit >>= 1
        target ^= bit
        if index < target:
            values[index], values[target] = values[target], values[index]
    length = 2
    while length <= size:
        rotation = cmath.exp(-2j * math.pi / length)
        for start in range(0, size, length):
            factor = 1.0 + 0.0j
            half = length // 2
            for index in range(start, start + half):
                even = values[index]
                odd = values[index + half] * factor
                values[index] = even + odd
                values[index + half] = even - odd
                factor *= rotation
        length *= 2


def spectrum(samples: list[float]) -> list[float]:
    size = len(samples)
    windowed = [
        complex(samples[index] * (0.5 - 0.5 * math.cos(2.0 * math.pi * index / (size - 1))), 0.0)
        for index in range(size)
    ]
    fft(windowed)
    scale = 2.0 / sum(0.5 - 0.5 * math.cos(2.0 * math.pi * index / (size - 1)) for index in range(size))
    return [abs(windowed[index]) * scale for index in range(size // 2 + 1)]


def quadratic_peak(magnitudes: list[float], index: int) -> float:
    if index <= 0 or index + 1 >= len(magnitudes):
        return float(index)
    left = math.log(max(magnitudes[index - 1], 1.0e-30))
    center = math.log(max(magnitudes[index], 1.0e-30))
    right = math.log(max(magnitudes[index + 1], 1.0e-30))
    denominator = left - 2.0 * center + right
    if abs(denominator) < 1.0e-20:
        return float(index)
    return index + 0.5 * (left - right) / denominator


def sinc_interpolate(samples: array.array[float], coordinate: float, radius: int = 32) -> float:
    center = math.floor(coordinate)
    result = 0.0
    weight_sum = 0.0
    for index in range(center - radius + 1, center + radius + 1):
        if index < 0 or index >= len(samples):
            continue
        distance = coordinate - index
        sinc = 1.0 if distance == 0.0 else math.sin(math.pi * distance) / (math.pi * distance)
        normalized = abs(distance) / radius
        window = 0.42 + 0.5 * math.cos(math.pi * normalized) + 0.08 * math.cos(2.0 * math.pi * normalized)
        weight = sinc * window
        result += samples[index] * weight
        weight_sum += weight
    return result / weight_sum


def rms_dbfs(values: list[float]) -> float:
    if not values:
        return -math.inf
    rms = math.sqrt(math.fsum(value * value for value in values) / len(values))
    return 20.0 * math.log10(max(rms, 1.0e-30))


def read_ledger(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def cut_intervals(rows: list[dict[str, str]], duration: int) -> list[tuple[int, int, int]]:
    opportunities = [row for row in rows if row["kind"] == "opportunity"]
    intervals: list[tuple[int, int, int]] = []
    start: int | None = None
    edge = 0
    for row in opportunities:
        sample = int(row["sample_index"])
        cut = row["cut"] == "1"
        if cut and start is None:
            start = sample
            edge = int(row["effective_edge_frames"])
        elif not cut and start is not None:
            intervals.append((start, sample, edge))
            start = None
    if start is not None:
        intervals.append((start, duration, edge))
    return intervals


def open_intervals(rows: list[dict[str, str]], duration: int) -> list[tuple[int, int, int]]:
    opportunities = [row for row in rows if row["kind"] == "opportunity"]
    if not opportunities:
        return [(0, duration, 0)]
    intervals: list[tuple[int, int, int]] = []
    previous = 0
    previous_cut = False
    previous_edge = 0
    for row in opportunities:
        sample = int(row["sample_index"])
        if not previous_cut and sample > previous:
            intervals.append((previous, sample, previous_edge))
        previous = sample
        previous_cut = row["cut"] == "1"
        previous_edge = int(row["effective_edge_frames"])
    if not previous_cut and previous < duration:
        intervals.append((previous, duration, previous_edge))
    return intervals


def band_energy_windows(
    left: array.array[float],
    right: array.array[float],
    intervals: list[tuple[int, int, int]],
    lower_hz: float,
    upper_hz: float,
    window_size: int = 2048,
) -> float:
    powers: list[float] = []
    lower_bin = max(1, math.ceil(lower_hz * window_size / 48000.0))
    upper_bin = min(window_size // 2, math.floor(upper_hz * window_size / 48000.0))
    for start, end, edge in intervals:
        safe_start = start + edge + 8
        safe_end = end - edge - 8
        if safe_end - safe_start < window_size:
            continue
        position = safe_start + (safe_end - safe_start - window_size) // 2
        magnitudes = spectrum(mono(left, right, position, window_size))
        powers.append(math.fsum(value * value for value in magnitudes[lower_bin:upper_bin + 1]))
    require(bool(powers), f"no full {window_size}-frame analysis windows in selected intervals")
    return math.fsum(powers) / len(powers)


def normalized_schedule(rows: list[dict[str, str]]) -> list[tuple[str, ...]]:
    selected: list[tuple[str, ...]] = []
    for row in rows:
        if row["kind"] == "accepted_control" and row["control"] in {"TENSION", "CUT", "HOLES"}:
            selected.append(tuple(row[key] for key in (
                "sample_index", "kind", "control", "value",
            )))
        elif row["kind"] in {"beat_boundary", "rhythm_commit", "opportunity"}:
            selected.append(tuple(row[key] for key in (
                "sample_index", "kind", "active_rate_index", "active_holes",
                "scheduler_error", "effective_edge_frames", "cut",
            )))
    return selected


def analyze(
    canonical: Path,
    reference: Path,
    contract: dict[str, object],
) -> tuple[dict[str, object], list[str]]:
    tolerances = contract["tolerances"]
    assert isinstance(tolerances, dict)
    failures: list[str] = []
    observations: dict[str, object] = {}

    condition_metrics: dict[str, dict[str, object]] = {}
    ledgers: dict[str, list[dict[str, str]]] = {}
    for condition_id in CONDITION_IDS:
        condition_metrics[condition_id] = json.loads(
            (canonical / f"{condition_id}.metrics.json").read_text(encoding="utf-8")
        )
        ledgers[condition_id] = read_ledger(canonical / f"{condition_id}.events.csv")
    safety: dict[str, object] = {}
    for condition_id, metrics in condition_metrics.items():
        audio = metrics["audio"]
        diagnostics = metrics["diagnostics"]
        assert isinstance(audio, dict) and isinstance(diagnostics, dict)
        peak = float(audio["abs_peak"])
        dc = [abs(float(value)) for value in audio["channel_dc_mean"]]
        condition_pass = (
            peak <= float(tolerances["sample_abs_peak_max"])
            and max(dc) <= float(tolerances["channel_abs_dc_mean_max"])
            and int(diagnostics["dropped_events"]) == 0
            and int(diagnostics["non_finite_containments"]) == 0
            and int(diagnostics["output_non_finite_clears"]) == 0
        )
        safety[condition_id] = {"abs_peak": peak, "channel_abs_dc_mean": dc, "passed": condition_pass}
        if not condition_pass:
            failures.append(f"{condition_id}: safety/DC/diagnostic tolerance failed")
        boundaries = [int(row["sample_index"]) for row in ledgers[condition_id] if row["kind"] == "opportunity"]
        if len(boundaries) > 1:
            spacing = min(right - left for left, right in zip(boundaries, boundaries[1:]))
            safety[condition_id]["minimum_scheduler_boundary_spacing_frames"] = spacing
            if spacing < int(tolerances["minimum_scheduler_boundary_spacing_frames"]):
                failures.append(f"{condition_id}: scheduler boundary spacing {spacing} < 32")
    observations["safety"] = safety

    wf01_left, wf01_right = decode_wav(canonical / "WF01_TENSION_OPEN.wav")
    expected_tension = (0.1, 0.3, 0.5, 0.7, 0.9)
    expected_frequencies = [110.0 * 2.0 ** ((42.0 * value ** 1.35) / 12.0) for value in expected_tension]
    fundamentals: list[float] = []
    cents_errors: list[float] = []
    centroids: list[float] = []
    hold_rms: list[float] = []
    hold_spectra: list[list[float]] = []
    for hold_index, expected in enumerate(expected_frequencies):
        segment_start = hold_index * 96000
        start = segment_start + 30000
        samples = mono(wf01_left, wf01_right, start, FFT_SIZE)
        magnitudes = spectrum(samples)
        hold_spectra.append(magnitudes)
        lower = max(1, math.floor(expected * 0.94 * FFT_SIZE / 48000.0))
        upper = min(len(magnitudes) - 2, math.ceil(expected * 1.06 * FFT_SIZE / 48000.0))
        peak_bin = max(range(lower, upper + 1), key=magnitudes.__getitem__)
        fundamental = quadratic_peak(magnitudes, peak_bin) * 48000.0 / FFT_SIZE
        fundamentals.append(fundamental)
        cents_errors.append(1200.0 * math.log2(fundamental / expected))
        centroid_upper = math.floor(18000.0 * FFT_SIZE / 48000.0)
        weighted = math.fsum(index * 48000.0 / FFT_SIZE * magnitudes[index] for index in range(1, centroid_upper + 1))
        total = math.fsum(magnitudes[1:centroid_upper + 1])
        centroids.append(weighted / total)
        rms_start = segment_start + 24000
        rms_count = 72000
        power = math.fsum(
            wf01_left[index] ** 2 + wf01_right[index] ** 2
            for index in range(rms_start, rms_start + rms_count)
        ) / (2.0 * rms_count)
        hold_rms.append(math.sqrt(power))
    adjacent_positive = sum(right > left for left, right in zip(centroids, centroids[1:]))
    centroid_ratio = centroids[-1] / centroids[0]
    rms_gain_db = 20.0 * math.log10(hold_rms[-1] / hold_rms[0])
    tension_pass = (
        max(abs(value) for value in cents_errors) <= float(tolerances["tension_fundamental_error_cents_max_abs"])
        and adjacent_positive >= int(tolerances["tension_adjacent_centroid_positive_count_min"])
        and centroid_ratio >= float(tolerances["tension_final_to_first_centroid_ratio_min"])
        and float(tolerances["final_to_first_hold_rms_db_min_exclusive"]) < rms_gain_db
        <= float(tolerances["final_to_first_hold_rms_db_max"])
    )
    observations["tension"] = {
        "adjacent_centroid_positive_count": adjacent_positive,
        "centroid_hz": centroids,
        "final_to_first_centroid_ratio": centroid_ratio,
        "final_to_first_hold_rms_db": rms_gain_db,
        "fundamental_cents_error": cents_errors,
        "fundamental_hz": fundamentals,
        "passed": tension_pass,
    }
    if not tension_pass:
        failures.append("WF01: TENSION pitch/centroid/RMS escalation tolerance failed")

    high_spectrum = hold_spectra[-1]
    f0 = expected_frequencies[-1]
    upper_bin = math.floor(float(tolerances["narrow_alias_search_upper_hz"]) * FFT_SIZE / 48000.0)
    excluded: set[int] = set()
    harmonic = 1
    while harmonic * f0 < float(tolerances["narrow_alias_search_upper_hz"]):
        center = round(harmonic * f0 * FFT_SIZE / 48000.0)
        excluded.update(range(max(1, center - 8), min(upper_bin, center + 8) + 1))
        harmonic += 1
    alias_amplitude = max(high_spectrum[index] for index in range(1, upper_bin + 1) if index not in excluded)
    alias_dbfs = 20.0 * math.log10(max(alias_amplitude, 1.0e-30))

    ref_left, ref_right = decode_wav(reference / "WF01_TENSION_OPEN_8x.wav")
    null_values: list[float] = []
    null_start = 384000 + 30000
    null_count = 65536
    for index in range(null_start, null_start + null_count):
        aligned_left = sinc_interpolate(ref_left, index + 0.125)
        aligned_right = sinc_interpolate(ref_right, index + 0.125)
        null_values.append(wf01_left[index] - aligned_left)
        null_values.append(wf01_right[index] - aligned_right)
    null_dbfs = rms_dbfs(null_values)
    alias_pass = (
        alias_dbfs <= float(tolerances["alias_component_below_18khz_max_dbfs"])
        and null_dbfs <= float(tolerances["wire_4x_vs_8x_rms_null_dbfs_max"])
    )
    observations["alias_and_reference"] = {
        "aligned_4x_vs_8x_rms_null_dbfs": null_dbfs,
        "highest_nonharmonic_component_below_18khz_dbfs": alias_dbfs,
        "passed": alias_pass,
    }
    if not alias_pass:
        failures.append("WF01: alias or aligned 4x-versus-8x residual tolerance failed")
    del ref_left, ref_right, wf01_left, wf01_right, hold_spectra

    wf02_left, wf02_right = decode_wav(canonical / "WF02_VOID.wav")
    wf03_left, wf03_right = decode_wav(canonical / "WF03_SHADOW.wav")
    duration = int(contract["conditions"][0]["duration_frames"])
    void_intervals = cut_intervals(ledgers["WF02_VOID"], duration)
    interior_peak = 0.0
    interior_count = 0
    for start, end, edge in void_intervals:
        safe_start = start + edge + 8
        safe_end = end - edge - 8
        if safe_end <= safe_start:
            continue
        interior_count += 1
        for index in range(safe_start, safe_end):
            interior_peak = max(interior_peak, abs(wf02_left[index]), abs(wf02_right[index]))
    void_pass = interior_count > 0 and interior_peak <= float(tolerances["void_cut_interior_abs_peak_max"])
    observations["void"] = {
        "cut_interior_abs_peak": interior_peak,
        "cut_interior_count": interior_count,
        "passed": void_pass,
    }
    if not void_pass:
        failures.append("WF02: true-void cut-interior tolerance failed")

    shadow_intervals = cut_intervals(ledgers["WF03_SHADOW"], duration)
    shadow_open = open_intervals(ledgers["WF03_SHADOW"], duration)
    wf02_low = band_energy_windows(wf02_left, wf02_right, void_intervals, 55.0, 500.0)
    wf03_low = band_energy_windows(wf03_left, wf03_right, shadow_intervals, 55.0, 500.0)
    shadow_low_gain_db = 10.0 * math.log10(max(wf03_low, 1.0e-30) / max(wf02_low, 1.0e-30))
    wire_frequency = 110.0 * 2.0 ** ((42.0 * 0.72 ** 1.35) / 12.0)
    wire_lower = wire_frequency * 0.94
    wire_upper = wire_frequency * 1.06
    cut_wire = band_energy_windows(wf03_left, wf03_right, shadow_intervals, wire_lower, wire_upper)
    open_wire = band_energy_windows(wf03_left, wf03_right, shadow_open, wire_lower, wire_upper)
    wire_rejection_db = 10.0 * math.log10(max(open_wire, 1.0e-30) / max(cut_wire, 1.0e-30))
    shadow_pass = (
        shadow_low_gain_db >= float(tolerances["shadow_cut_interior_lowband_gain_over_void_db_min"])
        and wire_rejection_db >= float(tolerances["shadow_wire_band_rejection_vs_open_db_min"])
    )
    observations["shadow"] = {
        "cut_lowband_gain_over_void_db": shadow_low_gain_db,
        "cut_wire_band_rejection_vs_open_db": wire_rejection_db,
        "passed": shadow_pass,
    }
    if not shadow_pass:
        failures.append("WF03: complementary Shadow low-band/rejection tolerance failed")
    del wf02_left, wf02_right, wf03_left, wf03_right

    schedules = {
        condition_id: normalized_schedule(ledgers[condition_id])
        for condition_id in ("WF02_VOID", "WF03_SHADOW", "CMP02_PARALLEL_LOW")
    }
    schedule_pass = schedules["WF02_VOID"] == schedules["WF03_SHADOW"] == schedules["CMP02_PARALLEL_LOW"]
    observations["schedule_parity"] = {
        "normalized_row_count": len(schedules["WF02_VOID"]),
        "passed": schedule_pass,
    }
    if not schedule_pass:
        failures.append("WF02/WF03/CMP02: accepted Wire event and scheduler parity failed")
    return observations, failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--renderer", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeat-block-frames", type=int)
    args = parser.parse_args()
    renderer = args.renderer.resolve()
    contract_path = args.contract.resolve()
    output = args.output.resolve()
    prototype = contract_path.parent.parent
    fixture_root = prototype / "generated/conditions"
    try:
        require(renderer.is_file(), f"renderer missing: {renderer}")
        require(contract_path.is_file(), f"contract missing: {contract_path}")
        if output.exists():
            require(not any(output.iterdir()), f"output directory must be absent or empty: {output}")
        else:
            output.mkdir(parents=True)
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        require(tuple(item["id"] for item in contract["conditions"]) == CONDITION_IDS, "condition order drift")
        require(tuple(contract["supported_block_frames"]) == PARTITIONS, "partition matrix drift")
        canonical = output / "canonical-block-64"
        canonical.mkdir()
        wf03_metrics: dict[str, object] | None = None
        parallel_gain: float | None = None
        canonical_metrics: dict[str, dict[str, object]] = {}
        for condition_id in CONDITION_IDS:
            fixture = fixture_root / f"{condition_id}.fixture"
            if condition_id == "CMP02_PARALLEL_LOW":
                assert wf03_metrics is not None
                audio = wf03_metrics["audio"]
                assert isinstance(audio, dict)
                metrics = run_renderer(
                    renderer, fixture, canonical, CANONICAL_BLOCK,
                    parallel_target_rms=float(audio["rms"]),
                )
                parallel_gain = float(metrics["parallel_shadow_gain"])
            else:
                metrics = run_renderer(renderer, fixture, canonical, CANONICAL_BLOCK)
            canonical_metrics[condition_id] = metrics
            if condition_id == "WF03_SHADOW":
                wf03_metrics = metrics

        reference = output / "reference-8x"
        reference.mkdir()
        run_renderer(
            renderer,
            fixture_root / "WF01_TENSION_OPEN.fixture",
            reference,
            CANONICAL_BLOCK,
            oversample_factor=8,
            output_prefix="WF01_TENSION_OPEN_8x",
        )

        partition_hashes: dict[str, dict[str, dict[str, str]]] = {condition_id: {} for condition_id in CONDITION_IDS}
        repeat_block = args.repeat_block_frames
        if repeat_block is None:
            blocks_to_render = (1, 16, 257, 512)
        else:
            require(repeat_block in PARTITIONS, "repeat block size is outside the frozen matrix")
            blocks_to_render = ()
        for condition_id in CONDITION_IDS:
            partition_hashes[condition_id]["64"] = artifact_hashes(canonical, condition_id)
        for block_frames in blocks_to_render:
            partition_dir = output / f"partition-block-{block_frames}"
            partition_dir.mkdir()
            for condition_id in CONDITION_IDS:
                kwargs: dict[str, float] = {}
                if condition_id == "CMP02_PARALLEL_LOW":
                    assert parallel_gain is not None
                    kwargs["parallel_gain"] = parallel_gain
                run_renderer(
                    renderer,
                    fixture_root / f"{condition_id}.fixture",
                    partition_dir,
                    block_frames,
                    **kwargs,
                )
                hashes = artifact_hashes(partition_dir, condition_id)
                partition_hashes[condition_id][str(block_frames)] = hashes
                canonical_hash = partition_hashes[condition_id]["64"]
                require(hashes["wav_sha256"] == canonical_hash["wav_sha256"],
                    f"{condition_id}: WAV differs for block {block_frames}")
                require(hashes["events_csv_sha256"] == canonical_hash["events_csv_sha256"],
                    f"{condition_id}: ledger differs for block {block_frames}")

        repeat_dir = output / f"fresh-repeat-block-{repeat_block or CANONICAL_BLOCK}"
        repeat_dir.mkdir()
        for condition_id in CONDITION_IDS:
            kwargs = {}
            if condition_id == "CMP02_PARALLEL_LOW":
                assert parallel_gain is not None
                kwargs["parallel_gain"] = parallel_gain
            run_renderer(
                renderer,
                fixture_root / f"{condition_id}.fixture",
                repeat_dir,
                repeat_block or CANONICAL_BLOCK,
                **kwargs,
            )
            repeat_hash = artifact_hashes(repeat_dir, condition_id)
            canonical_hash = partition_hashes[condition_id]["64"]
            require(repeat_hash["wav_sha256"] == canonical_hash["wav_sha256"],
                f"{condition_id}: fresh-repeat WAV differs")
            require(repeat_hash["events_csv_sha256"] == canonical_hash["events_csv_sha256"],
                f"{condition_id}: fresh-repeat ledger differs")

        observations, failures = analyze(canonical, reference, contract)
        manifest = {
            "canonical_artifacts": {
                condition_id: artifact_hashes(canonical, condition_id)
                for condition_id in CONDITION_IDS
            },
            "condition_ids": list(CONDITION_IDS),
            "contract_sha256": digest(contract_path),
            "determinism": {
                "block_partitions": list(PARTITIONS if repeat_block is None else (CANONICAL_BLOCK,)),
                "fresh_repeat_block_frames": repeat_block or CANONICAL_BLOCK,
                "ledger_relation": "byte-identical",
                "passed": True,
                "wav_relation": "byte-identical",
            },
            "failures": failures,
            "fixture_hashes": {
                condition_id: digest(fixture_root / f"{condition_id}.fixture")
                for condition_id in CONDITION_IDS
            },
            "host_signal_passed": not failures,
            "observations": observations,
            "parallel_shadow_gain": parallel_gain,
            "partition_artifacts": partition_hashes,
            "reference_8x": artifact_hashes(reference, "WF01_TENSION_OPEN_8x"),
            "schema_version": "wirefall-observation-manifest-v1",
            "seed": int(contract["seed"]),
            "seed_used": False,
        }
        (output / "wirefall-observation-manifest.json").write_text(
            canonical_json(manifest), encoding="utf-8", newline="\n"
        )
        summary = {
            "failures": failures,
            "host_signal_passed": not failures,
            "observations": observations,
            "schema_version": "wirefall-objective-summary-v1",
        }
        (output / "wirefall-objective-summary.json").write_text(
            canonical_json(summary), encoding="utf-8", newline="\n"
        )
        if failures:
            for failure in failures:
                print(f"FAIL: {failure}", file=sys.stderr)
            print(f"Wirefall host-signal matrix: {len(failures)} objective failure(s)", file=sys.stderr)
            return 1
    except (OSError, ValueError, KeyError, json.JSONDecodeError, subprocess.SubprocessError, wave.Error) as error:
        print(f"Wirefall render validation failed: {error}", file=sys.stderr)
        return 2
    print("Wirefall host-signal matrix: valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
