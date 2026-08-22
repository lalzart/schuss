#!/usr/bin/env python3
"""Run and validate the frozen Wirefall revision 0.2 host-signal matrix."""

from __future__ import annotations

import argparse
import array
import cmath
import csv
import hashlib
import json
import math
import subprocess
import sys
import wave
from pathlib import Path


CONDITIONS = ("R02_ENERGY", "R02_SILENCE", "R02_TICK", "R02_CMP_TREMOLO")
PARTITIONS = (1, 16, 64, 257, 512)
CANONICAL_PARTITION = 64
FFT_SIZE = 65536
SAMPLE_RATE = 48000
RATES = (0.0, 0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0)


def canonical_json(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def run_renderer(renderer: Path, condition: str, output: Path, block: int) -> None:
    output.mkdir(parents=True, exist_ok=True)
    command = [
        str(renderer), "--condition", condition,
        "--output", str(output), "--block-frames", str(block),
    ]
    completed = subprocess.run(command, check=False, text=True, capture_output=True)
    if completed.returncode:
        raise ValueError(
            f"renderer failed ({completed.returncode}): {' '.join(command)}\n"
            f"{completed.stdout}{completed.stderr}"
        )


def decode_wav(path: Path) -> tuple[array.array[float], array.array[float]]:
    with wave.open(str(path), "rb") as stream:
        require(stream.getnchannels() == 2, f"{path.name}: expected stereo")
        require(stream.getsampwidth() == 3, f"{path.name}: expected 24-bit")
        require(stream.getframerate() == SAMPLE_RATE, f"{path.name}: expected 48 kHz")
        frames = stream.getnframes()
        raw = stream.readframes(frames)
    require(len(raw) == frames * 6, f"{path.name}: truncated payload")
    left = array.array("f")
    right = array.array("f")
    scale = 1.0 / 8388607.0
    for offset in range(0, len(raw), 6):
        l_value = raw[offset] | raw[offset + 1] << 8 | raw[offset + 2] << 16
        r_value = raw[offset + 3] | raw[offset + 4] << 8 | raw[offset + 5] << 16
        if l_value & 0x800000:
            l_value -= 0x1000000
        if r_value & 0x800000:
            r_value -= 0x1000000
        left.append(l_value * scale)
        right.append(r_value * scale)
    return left, right


def read_ledger(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def mono(left: array.array[float], right: array.array[float], start: int, count: int) -> list[float]:
    return [0.5 * (left[index] + right[index]) for index in range(start, start + count)]


def fft(values: list[complex]) -> None:
    size = len(values)
    require(size > 0 and size & (size - 1) == 0, "FFT size must be a power of two")
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
        half = length // 2
        for start in range(0, size, length):
            factor = 1.0 + 0.0j
            for index in range(start, start + half):
                even = values[index]
                odd = values[index + half] * factor
                values[index] = even + odd
                values[index + half] = even - odd
                factor *= rotation
        length *= 2


def spectrum(samples: list[float]) -> list[float]:
    size = len(samples)
    window = [0.5 - 0.5 * math.cos(2.0 * math.pi * index / (size - 1)) for index in range(size)]
    values = [complex(sample * window[index], 0.0) for index, sample in enumerate(samples)]
    fft(values)
    scale = 2.0 / math.fsum(window)
    return [abs(values[index]) * scale for index in range(size // 2 + 1)]


def quadratic_peak(magnitudes: list[float], index: int) -> float:
    if index <= 0 or index + 1 >= len(magnitudes):
        return float(index)
    left = math.log(max(magnitudes[index - 1], 1.0e-30))
    center = math.log(max(magnitudes[index], 1.0e-30))
    right = math.log(max(magnitudes[index + 1], 1.0e-30))
    denominator = left - 2.0 * center + right
    return float(index) if abs(denominator) < 1.0e-20 else index + 0.5 * (left - right) / denominator


def rms(values: list[float]) -> float:
    return math.sqrt(math.fsum(value * value for value in values) / max(1, len(values)))


def dbfs(value: float) -> float:
    return 20.0 * math.log10(max(abs(value), 1.0e-30))


def pulse_rows(rows: list[dict[str, str]], minimum_frame: int = 0) -> list[dict[str, str]]:
    return [row for row in rows if row["kind"] == "pulse_onset" and int(row["sample_index"]) >= minimum_frame]


def closed_windows(rows: list[dict[str, str]], *, after: int = 768000) -> list[tuple[int, int, int]]:
    result: list[tuple[int, int, int]] = []
    duty = 0.08 + 0.34 * 0.35
    edge_seconds = (1.5 + 10.5 * 0.34 * 0.34) * 0.001
    for row in pulse_rows(rows, after):
        onset = int(row["sample_index"])
        rate_hz = RATES[int(row["pulse_index"])] * 2.0
        if rate_hz <= 0:
            continue
        period = SAMPLE_RATE / rate_hz
        edge = min(edge_seconds * SAMPLE_RATE, 0.45 * duty * period)
        start = math.ceil(onset + edge + 8)
        end = math.floor(onset + duty * period - edge - 8)
        if end > start:
            result.append((start, end, onset))
    return result


def analyze_energy(canonical: Path, tolerances: dict[str, object]) -> tuple[dict[str, object], list[str]]:
    failures: list[str] = []
    left, right = decode_wav(canonical / "R02_ENERGY.wav")
    energies = (0.10, 0.30, 0.50, 0.70, 0.90)
    expected = [82.4069 * 2.0 ** ((36.0 * value ** 1.15) / 12.0) for value in energies]
    fundamentals: list[float] = []
    errors: list[float] = []
    centroids: list[float] = []
    segment_rms: list[float] = []
    spectra: list[list[float]] = []
    for index, frequency in enumerate(expected):
        segment_start = index * 96000
        samples = mono(left, right, segment_start + 30000, FFT_SIZE)
        magnitudes = spectrum(samples)
        spectra.append(magnitudes)
        lower = max(1, math.floor(frequency * 0.94 * FFT_SIZE / SAMPLE_RATE))
        upper = min(len(magnitudes) - 2, math.ceil(frequency * 1.06 * FFT_SIZE / SAMPLE_RATE))
        peak_bin = max(range(lower, upper + 1), key=magnitudes.__getitem__)
        measured = quadratic_peak(magnitudes, peak_bin) * SAMPLE_RATE / FFT_SIZE
        fundamentals.append(measured)
        errors.append(1200.0 * math.log2(measured / frequency))
        upper_bin = math.floor(20000.0 * FFT_SIZE / SAMPLE_RATE)
        total = math.fsum(magnitudes[1:upper_bin + 1])
        weighted = math.fsum(
            bin_index * SAMPLE_RATE / FFT_SIZE * magnitudes[bin_index]
            for bin_index in range(1, upper_bin + 1)
        )
        centroids.append(weighted / total)
        values = mono(left, right, segment_start + 24000, 72000)
        segment_rms.append(rms(values))

    step_cents = [1200.0 * math.log2(right_value / left_value)
                  for left_value, right_value in zip(fundamentals, fundamentals[1:])]
    centroid_positive = sum(right_value > left_value
                            for left_value, right_value in zip(centroids, centroids[1:]))
    centroid_ratio = centroids[-1] / centroids[0]
    rms_gain = dbfs(segment_rms[-1] / segment_rms[0])
    high = spectra[-1]
    upper_bin = math.floor(20000.0 * FFT_SIZE / SAMPLE_RATE)
    excluded: set[int] = set()
    harmonic = 1
    while harmonic * expected[-1] < 20000.0:
        center = round(harmonic * expected[-1] * FFT_SIZE / SAMPLE_RATE)
        excluded.update(range(max(1, center - 8), min(upper_bin, center + 8) + 1))
        harmonic += 1
    nonharmonic = max(high[index] for index in range(1, upper_bin + 1) if index not in excluded)
    nonharmonic_db = dbfs(nonharmonic)
    passed = (
        max(abs(value) for value in errors) <= float(tolerances["energy_fundamental_error_cents_max"])
        and min(step_cents) >= float(tolerances["energy_step_pitch_cents_min"])
        and max(step_cents) <= float(tolerances["energy_step_pitch_cents_max"])
        and centroid_positive >= int(tolerances["energy_centroid_positive_steps_min"])
        and centroid_ratio >= float(tolerances["energy_centroid_ratio_min"])
        and float(tolerances["energy_rms_gain_db_min"]) <= rms_gain <= float(tolerances["energy_rms_gain_db_max"])
        and nonharmonic_db <= float(tolerances["nonharmonic_below_20khz_dbfs_max"])
    )
    if not passed:
        failures.append("R02_ENERGY: pitch, centroid, RMS, or non-harmonic tolerance failed")
    return {
        "centroid_hz": centroids,
        "centroid_positive_steps": centroid_positive,
        "centroid_ratio": centroid_ratio,
        "fundamental_cents_error": errors,
        "fundamental_hz": fundamentals,
        "highest_nonharmonic_below_20khz_dbfs": nonharmonic_db,
        "rms_gain_db": rms_gain,
        "step_pitch_cents": step_cents,
        "passed": passed,
    }, failures


def analyze_interrupt(canonical: Path, tolerances: dict[str, object]) -> tuple[dict[str, object], list[str]]:
    failures: list[str] = []
    silence_left, silence_right = decode_wav(canonical / "R02_SILENCE.wav")
    tick_left, tick_right = decode_wav(canonical / "R02_TICK.wav")
    silence_rows = read_ledger(canonical / "R02_SILENCE.events.csv")
    tick_rows = read_ledger(canonical / "R02_TICK.events.csv")
    silence_schedule = [
        (row["sample_index"], row["kind"], row["control"], row["value"], row["pulse_index"])
        for row in silence_rows if row["kind"] == "pulse_onset"
        or (row["kind"] == "accepted_control" and row["control"] != "TICK")
    ]
    tick_schedule = [
        (row["sample_index"], row["kind"], row["control"], row["value"], row["pulse_index"])
        for row in tick_rows if row["kind"] == "pulse_onset"
        or (row["kind"] == "accepted_control" and row["control"] != "TICK")
    ]
    schedule_equal = silence_schedule == tick_schedule
    windows = closed_windows(silence_rows)
    require(bool(windows), "no full-break closed windows found")
    interior_peak = 0.0
    main_closed: list[float] = []
    main_open: list[float] = []
    tick_values: list[float] = []
    tick_peak = 0.0
    boundary_excess = 0.0
    for start, end, onset in windows:
        for index in range(start, end):
            interior_peak = max(interior_peak, abs(silence_left[index]), abs(silence_right[index]))
        tick_end = min(onset + 384, len(tick_left))
        for index in range(onset, tick_end):
            value = 0.5 * (tick_left[index] + tick_right[index])
            tick_values.append(value)
            tick_peak = max(tick_peak, abs(value))
        closed_start = max(start, tick_end + 8)
        main_closed.extend(mono(tick_left, tick_right, closed_start, max(0, end - closed_start)))
        open_start = min(len(tick_left) - 2048, end + 1024)
        if open_start >= 0:
            main_open.extend(mono(tick_left, tick_right, open_start, 2048))
        if 2 <= onset < len(silence_left) - 2:
            for channel in (silence_left, silence_right, tick_left, tick_right):
                delta = channel[onset] - channel[onset - 1]
                local = 0.5 * ((channel[onset - 1] - channel[onset - 2])
                               + (channel[onset + 1] - channel[onset]))
                boundary_excess = max(boundary_excess, abs(delta - local))
    tick_rms_db = dbfs(rms(tick_values))
    tick_peak_db = dbfs(tick_peak)
    suppression_db = dbfs(rms(main_open) / max(rms(main_closed), 1.0e-30))
    passed = (
        interior_peak <= float(tolerances["full_break_interior_peak_max"])
        and schedule_equal is bool(tolerances["silence_tick_schedule_exact"])
        and tick_rms_db >= float(tolerances["tick_interrupt_rms_dbfs_min"])
        and tick_peak_db <= float(tolerances["tick_peak_dbfs_max"])
        and suppression_db >= float(tolerances["main_band_suppression_db_min"])
        and boundary_excess <= float(tolerances["boundary_delta_max"])
    )
    if not passed:
        failures.append("R02_SILENCE/R02_TICK: residual, parity, tick, suppression, or boundary tolerance failed")
    return {
        "boundary_excess_max": boundary_excess,
        "full_break_interior_peak": interior_peak,
        "main_suppression_db": suppression_db,
        "schedule_exact": schedule_equal,
        "tick_interrupt_rms_dbfs": tick_rms_db,
        "tick_peak_dbfs": tick_peak_db,
        "passed": passed,
    }, failures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("renderer", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "contract" / "experiment.json",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    renderer = args.renderer.resolve()
    output = args.output.resolve()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    tolerances = contract["tolerances"]
    failures: list[str] = []
    hashes: dict[str, object] = {}
    for block in PARTITIONS:
        directory = output / f"block-{block}"
        for condition in CONDITIONS:
            run_renderer(renderer, condition, directory, block)
    repeat = output / "repeat-64"
    for condition in CONDITIONS:
        run_renderer(renderer, condition, repeat, CANONICAL_PARTITION)

    canonical = output / f"block-{CANONICAL_PARTITION}"
    exact = True
    for condition in CONDITIONS:
        canonical_wav = canonical / f"{condition}.wav"
        canonical_csv = canonical / f"{condition}.events.csv"
        condition_hashes: dict[str, object] = {
            "canonical_wav_sha256": digest(canonical_wav),
            "canonical_events_sha256": digest(canonical_csv),
            "partitions": {},
        }
        for block in PARTITIONS:
            directory = output / f"block-{block}"
            wav_equal = (directory / f"{condition}.wav").read_bytes() == canonical_wav.read_bytes()
            csv_equal = (directory / f"{condition}.events.csv").read_bytes() == canonical_csv.read_bytes()
            condition_hashes["partitions"][str(block)] = {
                "events_exact": csv_equal,
                "wav_exact": wav_equal,
            }
            exact = exact and wav_equal and csv_equal
        repeat_equal = (
            (repeat / f"{condition}.wav").read_bytes() == canonical_wav.read_bytes()
            and (repeat / f"{condition}.events.csv").read_bytes() == canonical_csv.read_bytes()
        )
        condition_hashes["repeat_exact"] = repeat_equal
        exact = exact and repeat_equal
        hashes[condition] = condition_hashes
    if not exact:
        failures.append("partition or repeat WAV/event byte equality failed")

    safety: dict[str, object] = {}
    for condition in CONDITIONS:
        metrics = json.loads((canonical / f"{condition}.metrics.json").read_text(encoding="utf-8"))
        diagnostics = metrics["diagnostics"]
        passed = (
            float(metrics["abs_peak"]) <= float(tolerances["sample_peak_max"])
            and max(abs(float(value)) for value in metrics["channel_dc_mean"]) <= float(tolerances["absolute_dc_max"])
            and int(diagnostics["dropped_events"]) <= int(tolerances["event_overrun_count_max"])
            and int(diagnostics["non_finite_samples"]) <= int(tolerances["nan_inf_count_max"])
            and int(diagnostics["safety_clamps"]) <= int(tolerances["normal_safety_clamp_count_max"])
        )
        safety[condition] = {
            "abs_peak": metrics["abs_peak"],
            "channel_dc_mean": metrics["channel_dc_mean"],
            "diagnostics": diagnostics,
            "passed": passed,
        }
        if not passed:
            failures.append(f"{condition}: safety, DC, or diagnostic tolerance failed")

    energy, energy_failures = analyze_energy(canonical, tolerances)
    interrupt, interrupt_failures = analyze_interrupt(canonical, tolerances)
    failures.extend(energy_failures)
    failures.extend(interrupt_failures)
    summary = {
        "artifact_hashes": hashes,
        "energy": energy,
        "failures": failures,
        "interrupt": interrupt,
        "passed": not failures,
        "safety": safety,
        "schema_version": "wirefall-r02-objective-summary-v1",
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "wirefall-r02-objective-summary.json").write_text(canonical_json(summary), encoding="utf-8")
    print(canonical_json(summary))
    return 0 if not failures else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"wirefall-r02 validation: {error}", file=sys.stderr)
        raise SystemExit(1)
