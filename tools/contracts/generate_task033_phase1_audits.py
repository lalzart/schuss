#!/usr/bin/env python3
"""Generate the deterministic Task 033 Mutable and pinned-JUCE audit packets."""

from __future__ import annotations

import argparse
import copy
import hashlib
import re
import sys
import tarfile
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/contracts")]

from packages.schuss_core.control_plane import load_repository_context  # noqa: E402

import validator_core as core  # noqa: E402


BASELINE = ROOT / "contracts/record-sets/task032-variable-host-runtime-v1.json"
MUTABLE_SOURCE = ROOT / "catalog/reviews/task030-mutable-catalog-v1/entries.jsonl"
MUTABLE_OUTPUT = ROOT / "catalog/reviews/task033-mutable-provider-audit-v1"
JUCE_OUTPUT = ROOT / "catalog/reviews/task033-juce-dsp-audit-v1"
JUCE_LOCK = ROOT / "contracts/task031/juce-source-lock.json"
MUTABLE_TAG = "mutable-instruments-derived"

EXPECTED_BASELINE = {
    "record_set_id": "schuss-record-set-000029",
    "revision": 1,
    "content_hash": "sha256:8d6d8e5b0c3a90862f1e7c9ddab9c054a7b5908f268db9fa356c131bdc37c55c",
}
KSOLOTI_TARGET = "schuss-compute-target-000001"
KSOLOTI_BACKEND = "schuss-backend-000002"
HOST_TARGET = "schuss-compute-target-000002"
HOST_BACKEND = "schuss-backend-000003"


def _juce_spec(
    path: str,
    classification: str,
    recommendation: str,
    candidate_function: str | None,
    *,
    numeric: str = "template-or-caller-defined; exact supported scalar types require a provider review",
    channels: str = "caller/context-defined; no Schuss channel contract is implied",
    lifecycle: str = "header-specific construction/use; no Schuss lifecycle is implied",
    concerns: tuple[str, ...] = (),
    secondary: tuple[str, ...] = (),
) -> dict[str, Any]:
    return {
        "portable_path": f"modules/juce_dsp/{path}",
        "audit_classification": classification,
        "secondary_classifications": list(secondary),
        "architecture_recommendation": recommendation,
        "candidate_function": candidate_function,
        "numeric_semantics": numeric,
        "channel_semantics": channels,
        "lifecycle_semantics": lifecycle,
        "callback_concerns": list(concerns),
    }


UTILITY_CONCERN = (
    "This is not a standalone Schuss node; any use inherits the containing provider's allocation and real-time audit.",
)
PROCESSOR_CONCERN = (
    "Construction, prepare/reset, storage changes, and non-atomic parameter reconfiguration must remain outside the audio callback until explicitly proved safe.",
)


# Order is the exact include order in the pinned juce_dsp umbrella header.
JUCE_HEADER_SPECS: tuple[dict[str, Any], ...] = (
    _juce_spec("maths/juce_SpecialFunctions.h", "implementation-utility", "defer", None, concerns=UTILITY_CONCERN),
    _juce_spec("maths/juce_Matrix.h", "implementation-utility", "defer", None, concerns=UTILITY_CONCERN),
    _juce_spec("maths/juce_Phase.h", "implementation-utility", "defer", None, lifecycle="stateful phase accumulation with explicit reset", concerns=UTILITY_CONCERN),
    _juce_spec("maths/juce_Polynomial.h", "implementation-utility", "defer", None, concerns=UTILITY_CONCERN),
    _juce_spec("maths/juce_FastMathApproximations.h", "implementation-utility", "defer", None, concerns=UTILITY_CONCERN),
    _juce_spec("maths/juce_LookupTable.h", "implementation-utility", "defer", None, lifecycle="table initialisation precedes lookup use", concerns=("Table creation/storage work must be completed outside the audio callback.",)),
    _juce_spec("maths/juce_LogRampedValue.h", "implementation-utility", "defer", None, lifecycle="stateful ramp configuration and advancement", concerns=UTILITY_CONCERN),
    _juce_spec("containers/juce_AudioBlock.h", "implementation-utility", "defer", None, channels="non-owning caller-defined multichannel block view", lifecycle="view construction over caller-owned storage", concerns=UTILITY_CONCERN),
    _juce_spec("processors/juce_ProcessContext.h", "implementation-utility", "defer", None, channels="caller-defined replacing or non-replacing process context", concerns=UTILITY_CONCERN),
    _juce_spec("processors/juce_ProcessorWrapper.h", "composition-helper", "defer", None, lifecycle="forwards prepare/process/reset to a wrapped processor", concerns=UTILITY_CONCERN),
    _juce_spec("processors/juce_ProcessorChain.h", "composition-helper", "defer", None, channels="inherits the contained processors' channel rules", lifecycle="compile-time processor composition with forwarded prepare/process/reset", concerns=UTILITY_CONCERN),
    _juce_spec("processors/juce_ProcessorDuplicator.h", "composition-helper", "defer", None, channels="duplicates a mono processor/state across context channels", lifecycle="allocates/configures duplicated processors during prepare", concerns=PROCESSOR_CONCERN),
    _juce_spec("processors/juce_IIRFilter.h", "musical-node-candidate", "native-schuss-algorithm", "recursive-filter", channels="one filter instance per channel unless explicitly duplicated", lifecycle="coefficient/state setup plus prepare/process/reset", concerns=PROCESSOR_CONCERN),
    _juce_spec("processors/juce_IIRFilter_Impl.h", "deferred-or-unsuitable", "defer", None, lifecycle="implementation detail for the public IIR filter surface", concerns=UTILITY_CONCERN),
    _juce_spec("processors/juce_FIRFilter.h", "musical-node-candidate", "native-schuss-algorithm", "finite-impulse-response-filter", channels="one filter instance per channel unless explicitly duplicated", lifecycle="coefficient/state setup plus prepare/process/reset", concerns=PROCESSOR_CONCERN),
    _juce_spec("processors/juce_StateVariableFilter.h", "musical-node-candidate", "defer", "state-variable-filter", channels="mono processor; multichannel use requires explicit duplication", lifecycle="shared parameters plus prepare/process/reset", concerns=PROCESSOR_CONCERN),
    _juce_spec("processors/juce_FirstOrderTPTFilter.h", "musical-node-candidate", "native-schuss-algorithm", "first-order-tpt-filter", channels="prepared multichannel processor", lifecycle="type/cutoff setup plus prepare/process/reset", concerns=PROCESSOR_CONCERN),
    _juce_spec("processors/juce_Panner.h", "musical-node-candidate", "native-schuss-algorithm", "stereo-panner", channels="stereo output processor with explicit mono/stereo contract work required", lifecycle="rule/pan setup plus prepare/process/reset", concerns=PROCESSOR_CONCERN),
    _juce_spec("processors/juce_DelayLine.h", "musical-node-candidate", "native-schuss-algorithm", "delay-line", channels="prepared multichannel delay storage", lifecycle="maximum delay/storage setup plus prepare/process/reset", concerns=("Changing maximum delay may allocate and is explicitly unsuitable for the audio thread.",)),
    _juce_spec("processors/juce_Oversampling.h", "composition-helper", "defer", None, channels="explicitly configured multichannel up/down-sampling helper", lifecycle="stage construction and processing-storage initialisation precede callback use", concerns=("Stage/storage construction and latency configuration belong outside the audio callback.",)),
    _juce_spec("processors/juce_BallisticsFilter.h", "musical-node-candidate", "native-schuss-algorithm", "level-envelope-follower", channels="prepared multichannel detector", lifecycle="attack/release/mode setup plus prepare/process/reset", concerns=PROCESSOR_CONCERN),
    _juce_spec("processors/juce_LinkwitzRileyFilter.h", "musical-node-candidate", "native-schuss-algorithm", "linkwitz-riley-crossover", channels="prepared multichannel processor with paired low/high outputs", lifecycle="type/cutoff setup plus prepare/process/reset", concerns=PROCESSOR_CONCERN),
    _juce_spec("processors/juce_DryWetMixer.h", "composition-helper", "defer", None, channels="prepared multichannel mixing helper", lifecycle="mix/latency setup plus prepare/reset and push/mix calls", concerns=("Wet-latency compensation storage must be configured outside the audio callback.",)),
    _juce_spec("processors/juce_StateVariableTPTFilter.h", "musical-node-candidate", "native-schuss-algorithm", "state-variable-tpt-filter", channels="prepared multichannel processor", lifecycle="type/cutoff/resonance setup plus prepare/process/reset", concerns=PROCESSOR_CONCERN),
    _juce_spec("frequency/juce_FFT.h", "implementation-utility", "defer", None, numeric="single-precision transform API with backend-specific implementation choices", channels="not an audio-channel processor; caller supplies transform arrays", lifecycle="fixed-order transform plan construction followed by transform calls", concerns=("Plan/backend construction and scratch ownership require a containing-provider real-time audit.",)),
    _juce_spec("frequency/juce_Convolution.h", "asset-dependent-processor", "later-juce-host-provider", "impulse-response-convolution", numeric="floating-point JUCE processor; no Q27 equivalence is established", channels="documented stereo partitioned convolution with explicit mono/stereo contract work required", lifecycle="message queue, prepare/reset, and impulse-response load lifecycle", concerns=("Impulse assets, decoding/resampling, partition storage, latency, and optional background queue ownership require a host-provider contract.", "Wait-free impulse-response update claims do not prove Schuss callback safety or bounded resource use."), secondary=("host-service",)),
    _juce_spec("frequency/juce_Windowing.h", "implementation-utility", "defer", None, numeric="floating-point window-table generation/application", channels="not an audio-channel processor; caller supplies sample arrays", lifecycle="window table construction followed by array application", concerns=("Window-table construction belongs outside the audio callback.",)),
    _juce_spec("filter_design/juce_FilterDesign.h", "implementation-utility", "defer", None, numeric="floating-point coefficient/design utility", channels="not a runtime channel processor", lifecycle="coefficient design precedes runtime processing", concerns=("Filter design and coefficient allocation belong outside the audio callback.",)),
    _juce_spec("widgets/juce_Reverb.h", "musical-node-candidate", "later-juce-host-provider", "reverberation", numeric="floating-point JUCE processor; no Q27 equivalence is established", channels="mono or stereo only", lifecycle="parameter setup plus prepare/process/reset", concerns=PROCESSOR_CONCERN),
    _juce_spec("widgets/juce_Bias.h", "musical-node-candidate", "native-schuss-algorithm", "dc-bias", channels="prepared multichannel processor", lifecycle="bias/ramp setup plus prepare/process/reset", concerns=PROCESSOR_CONCERN),
    _juce_spec("widgets/juce_Gain.h", "musical-node-candidate", "native-schuss-algorithm", "gain", channels="prepared multichannel processor", lifecycle="gain/ramp setup plus prepare/process/reset", concerns=PROCESSOR_CONCERN),
    _juce_spec("widgets/juce_WaveShaper.h", "musical-node-candidate", "native-schuss-algorithm", "waveshaping", channels="context-defined channels with per-sample function application", lifecycle="callable/function setup before process; prepare/reset are otherwise trivial", concerns=("The chosen shaping function and any captured state require an exact no-allocation callback contract.",)),
    _juce_spec("widgets/juce_Oscillator.h", "musical-node-candidate", "native-schuss-algorithm", "oscillator", channels="prepared multichannel processor", lifecycle="waveform/table initialisation plus frequency/ramp setup and prepare/process/reset", concerns=("Lookup-table or callable initialisation must occur outside the audio callback.",)),
    _juce_spec("widgets/juce_LadderFilter.h", "musical-node-candidate", "later-juce-host-provider", "ladder-filter", numeric="floating-point JUCE processor; no Q27 equivalence is established", channels="prepared multichannel processor", lifecycle="mode/cutoff/resonance/drive setup plus prepare/process/reset", concerns=PROCESSOR_CONCERN),
    _juce_spec("widgets/juce_Compressor.h", "musical-node-candidate", "later-juce-host-provider", "compressor", numeric="floating-point JUCE processor; exact detector and gain semantics need a contract", channels="prepared multichannel processor", lifecycle="threshold/ratio/attack/release setup plus prepare/process/reset", concerns=PROCESSOR_CONCERN),
    _juce_spec("widgets/juce_NoiseGate.h", "musical-node-candidate", "later-juce-host-provider", "noise-gate", numeric="floating-point JUCE processor; exact detector and gain semantics need a contract", channels="prepared multichannel processor", lifecycle="threshold/ratio/attack/release setup plus prepare/process/reset", concerns=PROCESSOR_CONCERN),
    _juce_spec("widgets/juce_Limiter.h", "musical-node-candidate", "later-juce-host-provider", "limiter", numeric="floating-point JUCE processor; exact staged dynamics semantics need a contract", channels="prepared multichannel processor", lifecycle="threshold/release setup plus prepare/process/reset", concerns=PROCESSOR_CONCERN),
    _juce_spec("widgets/juce_Phaser.h", "musical-node-candidate", "later-juce-host-provider", "phaser", numeric="floating-point JUCE processor; no Q27 equivalence is established", channels="prepared multichannel processor", lifecycle="rate/depth/frequency/feedback/mix setup plus prepare/process/reset", concerns=PROCESSOR_CONCERN),
    _juce_spec("widgets/juce_Chorus.h", "musical-node-candidate", "later-juce-host-provider", "chorus", numeric="floating-point JUCE processor; no Q27 equivalence is established", channels="prepared multichannel processor", lifecycle="rate/depth/delay/feedback/mix setup plus prepare/process/reset", concerns=PROCESSOR_CONCERN),
)


def _canonical_bytes(value: Any) -> bytes:
    return core.canonical_json(value).encode("utf-8") + b"\n"


def _jsonl_bytes(values: list[dict[str, Any]]) -> bytes:
    return b"".join(_canonical_bytes(value) for value in values)


def _fact(data: bytes) -> dict[str, Any]:
    return {"byte_length": len(data), "byte_sha256": hashlib.sha256(data).hexdigest()}


def _path_fact(path: Path) -> dict[str, Any]:
    return _fact(path.read_bytes())


def _audited_entry(value: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(value)
    result["entry_sha256"] = hashlib.sha256(_canonical_bytes(result)).hexdigest()
    return result


def _write_or_check(path: Path, data: bytes, check: bool) -> None:
    if check:
        if not path.is_file() or path.read_bytes() != data:
            raise ValueError(f"stale Task 033 audit output: {path.relative_to(ROOT)}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _record_reference(record: dict[str, Any], id_field: str) -> dict[str, Any]:
    return {
        "stable_id": record[id_field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def _eligibility_summary(record: dict[str, Any]) -> dict[str, Any]:
    state = record["allowed_pair"]["state"]
    return {
        "eligibility_reference": _record_reference(record, "binding_eligibility_id"),
        "binding_reference": copy.deepcopy(record["binding_reference"]),
        "target_reference": copy.deepcopy(record["allowed_pair"]["target_reference"]),
        "backend_reference": copy.deepcopy(record["allowed_pair"]["backend_reference"]),
        "status": state["status"],
        "code": state.get("code"),
        "resource_states": [item["state"]["status"] for item in record["resource_requirements"]],
    }


def _target_row(
    eligibility: list[dict[str, Any]],
    *,
    label: str,
    target_id: str,
    backend_id: str,
) -> dict[str, Any]:
    matching = [
        _eligibility_summary(item)
        for item in eligibility
        if item["allowed_pair"]["target_reference"]["compute_target_id"] == target_id
        and item["allowed_pair"]["backend_reference"]["backend_id"] == backend_id
    ]
    states = {item["status"] for item in matching}
    if "supported" in states:
        availability = "eligible"
    elif "unsupported" in states:
        availability = "unsupported"
    elif matching:
        availability = "not-evaluated"
    else:
        availability = "no-binding-or-eligibility"
    return {
        "target": label,
        "compute_target_id": target_id,
        "backend_id": backend_id,
        "availability": availability,
        "eligibility": matching,
    }


def _mutable_disposition(entry: dict[str, Any], implementation_id: str) -> dict[str, str]:
    if implementation_id == "schuss-implementation-000056":
        return {
            "disposition": "defer-retained-unsupported",
            "promotion_lane": "separate-reverb-allocation-and-runtime-boundary-task",
            "rationale": "The exact direct Ksoloti eligibility is unsupported and retains unresolved allocation ownership; source/catalog presence cannot override it.",
        }
    if implementation_id in {"schuss-implementation-000057", "schuss-implementation-000058"}:
        return {
            "disposition": "resolve-existing-contract-first",
            "promotion_lane": "ksoloti-direct-eligibility-and-runtime-evidence",
            "rationale": "An exact component contract and Ksoloti binding exist, but eligibility remains not-evaluated and no desktop-host binding exists.",
        }
    limitations = " ".join(entry["known_source_limitations"]).lower()
    status = (entry.get("source_manifest_metadata") or {}).get("build_status")
    if status == "build-failed" or "will not currently link" in limitations:
        return {
            "disposition": "defer-known-source-failure",
            "promotion_lane": "source-repair-and-authenticated-reproduction-before-contract",
            "rationale": "Retained source evidence records a build or link failure; Task 033 does not repair or promote it.",
        }
    return {
        "disposition": "contract-first-candidate",
        "promotion_lane": "exact-component-contract-then-target-specific-binding",
        "rationale": "The implementation has reviewed source provenance and catalog placement only; exact semantics and per-target realization must be authored before promotion.",
    }


def _mutable_gaps(implementation: dict[str, Any], disposition: str) -> list[str]:
    gaps: list[str] = []
    if implementation["exact_reference"] is None:
        gaps.append("exact-implementation-record-reference")
    if not implementation["contract_references"]:
        gaps.append("exact-component-contract")
    if not implementation["binding_references"]:
        gaps.append("target-specific-implementation-binding")
    if not implementation["eligibility_references"]:
        gaps.append("target-backend-eligibility")
    gaps.extend(
        [
            "desktop-host-binding-and-eligibility",
            "numeric-channel-state-lifecycle-closure",
            "resource-and-real-time-evidence",
            "compile-device-and-audible-evidence-kept-separate",
        ]
    )
    if disposition == "defer-known-source-failure":
        gaps.insert(0, "retained-source-build-or-link-failure")
    if disposition == "defer-retained-unsupported":
        gaps.insert(0, "retained-unsupported-resource-allocation")
    return gaps


def generate_mutable() -> tuple[bytes, bytes]:
    baseline = core.load_json(BASELINE)
    for key, expected in EXPECTED_BASELINE.items():
        if baseline.get(key) != expected:
            raise ValueError(f"Task 033 baseline drift: {key}")
    context = load_repository_context(record_set_path=BASELINE)
    source_entries = [
        item
        for item in core.load_jsonl(MUTABLE_SOURCE)
        if MUTABLE_TAG in item["provenance_tags"]
    ]
    if len(source_entries) != 56:
        raise ValueError("Task 033 Mutable source cohort must contain exactly 56 entries")

    projection: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    for family in context.catalog_projection["families"]:
        for implementation in family["implementations"]:
            if MUTABLE_TAG in implementation["provenance_tags"]:
                projection[implementation["implementation_id"]] = (family, implementation)
    expected_ids = {item["catalog_implementation_id"] for item in source_entries}
    if set(projection) != expected_ids or None in expected_ids:
        raise ValueError("Task 033 Mutable catalog/source identity closure drift")

    eligibility_by_implementation: dict[str, list[dict[str, Any]]] = {}
    for record in context.records["eligibility"]:
        implementation_id = record["binding_reference"]["implementation_id"]
        eligibility_by_implementation.setdefault(implementation_id, []).append(record)

    values: list[dict[str, Any]] = []
    for source in sorted(source_entries, key=lambda item: item["catalog_implementation_id"]):
        implementation_id = source["catalog_implementation_id"]
        family, implementation = projection[implementation_id]
        disposition = _mutable_disposition(source, implementation_id)
        eligibility = eligibility_by_implementation.get(implementation_id, [])
        value = {
            "format_version": "task033-mutable-provider-audit-v1",
            "implementation_id": implementation_id,
            "implementation_reference": copy.deepcopy(implementation["exact_reference"]),
            "display_name": implementation["display_name"],
            "family_reference": copy.deepcopy(family["family_reference"]),
            "family_display_name": family["display_name"],
            "primary_function": family["primary_function"],
            "form": implementation["form"],
            "provenance_sources": copy.deepcopy(implementation["provenance_sources"]),
            "provenance_tags": copy.deepcopy(implementation["provenance_tags"]),
            "readiness_states": copy.deepcopy(implementation["readiness_states"]),
            "contract_references": copy.deepcopy(implementation["contract_references"]),
            "binding_references": copy.deepcopy(implementation["binding_references"]),
            "eligibility_references": copy.deepcopy(implementation["eligibility_references"]),
            "target_matrix": [
                _target_row(
                    eligibility,
                    label="desktop-host",
                    target_id=HOST_TARGET,
                    backend_id=HOST_BACKEND,
                ),
                _target_row(
                    eligibility,
                    label="ksoloti-core",
                    target_id=KSOLOTI_TARGET,
                    backend_id=KSOLOTI_BACKEND,
                ),
            ],
            "source_review": {
                key: copy.deepcopy(source[key])
                for key in (
                    "entry_id",
                    "stable_source_id",
                    "candidate_ref",
                    "source_id",
                    "source_kind",
                    "commit",
                    "author",
                    "declared_license",
                    "description",
                    "source_paths",
                    "known_source_limitations",
                    "source_manifest_metadata",
                )
            },
            **disposition,
        }
        value["required_gaps"] = _mutable_gaps(implementation, value["disposition"])
        values.append(_audited_entry(value))

    disposition_counts = Counter(item["disposition"] for item in values)
    readiness_counts = Counter(
        "contracted-bound" if "contracted" in item["readiness_states"] else "catalogued-only"
        for item in values
    )
    target_counts = {
        target: dict(
            sorted(
                Counter(
                    next(row for row in item["target_matrix"] if row["target"] == target)["availability"]
                    for item in values
                ).items()
            )
        )
        for target in ("desktop-host", "ksoloti-core")
    }
    entries_bytes = _jsonl_bytes(values)
    manifest = {
        "format_version": "task033-mutable-provider-audit-manifest-v1",
        "canonical_profile": "schuss-canonical-json-v1",
        "baseline_record_set_reference": EXPECTED_BASELINE,
        "source_review": {
            "portable_path": str(MUTABLE_SOURCE.relative_to(ROOT)),
            **_path_fact(MUTABLE_SOURCE),
        },
        "entries": {
            "portable_path": "catalog/reviews/task033-mutable-provider-audit-v1/entries.jsonl",
            **_fact(entries_bytes),
        },
        "counts": {
            "total": len(values),
            "dispositions": dict(sorted(disposition_counts.items())),
            "readiness": dict(sorted(readiness_counts.items())),
            "targets": target_counts,
        },
        "evidence_boundary": "Catalog/source facts and audit dispositions only; no target support, build, device, real-time, audible, or release promotion is created.",
    }
    return entries_bytes, _canonical_bytes(manifest)


def _module_value(text: str, field: str) -> str:
    match = re.search(rf"^\s*{re.escape(field)}:\s*(.+?)\s*$", text, re.MULTILINE)
    if match is None:
        raise ValueError(f"pinned juce_dsp module field is absent: {field}")
    return match.group(1)


def generate_juce(juce_root: Path, archive: Path) -> tuple[bytes, bytes]:
    lock = core.load_json(JUCE_LOCK)
    archive_fact = _path_fact(archive)
    expected_archive = lock["source"]["archive_sha256"]
    if archive_fact["byte_sha256"] != expected_archive:
        raise ValueError("pinned JUCE archive SHA-256 mismatch")
    module_root = juce_root / "modules/juce_dsp"
    umbrella = module_root / "juce_dsp.h"
    implementation = module_root / "juce_dsp.cpp"
    if not umbrella.is_file() or not implementation.is_file():
        raise ValueError("JUCE root does not contain the pinned juce_dsp module")
    text = umbrella.read_text(encoding="utf-8")
    module = {
        "version": _module_value(text, "version"),
        "license": _module_value(text, "license"),
        "minimum_cpp_standard": _module_value(text, "minimumCppStandard"),
        "dependencies": _module_value(text, "dependencies").split(),
    }
    if module != {
        "version": "8.0.15",
        "license": "AGPLv3/Commercial",
        "minimum_cpp_standard": "17",
        "dependencies": ["juce_audio_formats"],
    }:
        raise ValueError("pinned juce_dsp module declaration drift")

    include_rows: list[tuple[int, str]] = []
    include_pattern = re.compile(
        r'^#include "((?:maths|containers|processors|frequency|filter_design|widgets)/[^\"]+\.h)"$'
    )
    for line_number, line in enumerate(text.splitlines(), start=1):
        match = include_pattern.match(line)
        if match is not None:
            include_rows.append((line_number, match.group(1)))
    expected_paths = [item["portable_path"].removeprefix("modules/juce_dsp/") for item in JUCE_HEADER_SPECS]
    if [path for _, path in include_rows] != expected_paths or len(include_rows) != 39:
        raise ValueError("pinned juce_dsp public umbrella header census drift")

    reviewed_paths = [
        "modules/juce_dsp/juce_dsp.h",
        "modules/juce_dsp/juce_dsp.cpp",
        *(f"modules/juce_dsp/{path}" for path in expected_paths),
    ]
    with tarfile.open(archive, mode="r:gz") as source_archive:
        archived: dict[str, bytes] = {}
        for member in source_archive.getmembers():
            relative = member.name.split("/", 1)[1] if "/" in member.name else ""
            if relative not in reviewed_paths:
                continue
            stream = source_archive.extractfile(member)
            if stream is None or relative in archived:
                raise ValueError(f"ambiguous pinned JUCE archive member: {relative}")
            archived[relative] = stream.read()
    if set(archived) != set(reviewed_paths):
        raise ValueError("pinned JUCE archive lacks the exact reviewed module files")
    for relative in reviewed_paths:
        if (juce_root / relative).read_bytes() != archived[relative]:
            raise ValueError(f"JUCE review root does not match pinned archive: {relative}")

    values: list[dict[str, Any]] = []
    for spec, (line_number, relative_path) in zip(JUCE_HEADER_SPECS, include_rows, strict=True):
        path = module_root / relative_path
        if not path.is_file():
            raise ValueError(f"pinned juce_dsp header is absent: {relative_path}")
        source_bytes = path.read_bytes()
        value = {
            "format_version": "task033-juce-dsp-audit-v1",
            "subject": Path(relative_path).stem.removeprefix("juce_"),
            "source": {
                "portable_path": spec["portable_path"],
                "byte_sha256": hashlib.sha256(source_bytes).hexdigest(),
                "byte_length": len(source_bytes),
                "line_count": len(source_bytes.decode("utf-8").splitlines()),
                "umbrella_include_line": line_number,
            },
            "module_requirements": {
                **module,
                "current_schuss_source_lock_includes_module": "juce_dsp" in lock["modules"],
            },
            "audit_classification": spec["audit_classification"],
            "secondary_classifications": spec["secondary_classifications"],
            "candidate_function": spec["candidate_function"],
            "numeric_semantics": spec["numeric_semantics"],
            "channel_semantics": spec["channel_semantics"],
            "lifecycle_semantics": spec["lifecycle_semantics"],
            "callback_concerns": spec["callback_concerns"],
            "architecture_recommendation": spec["architecture_recommendation"],
            "required_schuss_work": (
                [
                    "exact-family-and-component-contract",
                    "parameter-state-unit-channel-and-lifecycle-contract",
                    "explicit-desktop-float-target-backend-if-using-juce",
                    "static-provider-binding-and-fail-closed-eligibility",
                    "dependency-license-resource-and-real-time-review",
                ]
                if spec["candidate_function"] is not None
                else ["keep-internal-to-an-explicitly-reviewed-provider-or-defer"]
            ),
            "promotion_state": "candidate-only-not-imported-not-linked-not-eligible",
        }
        values.append(_audited_entry(value))

    entries_bytes = _jsonl_bytes(values)
    classification_counts = Counter(item["audit_classification"] for item in values)
    recommendation_counts = Counter(item["architecture_recommendation"] for item in values)
    manifest = {
        "format_version": "task033-juce-dsp-audit-manifest-v1",
        "canonical_profile": "schuss-canonical-json-v1",
        "source_lock": {
            "portable_path": str(JUCE_LOCK.relative_to(ROOT)),
            **_path_fact(JUCE_LOCK),
            "source": copy.deepcopy(lock["source"]),
            "locked_modules": copy.deepcopy(lock["modules"]),
        },
        "authenticated_archive": {
            "byte_sha256": archive_fact["byte_sha256"],
            "byte_length": archive_fact["byte_length"],
            "matches_source_lock": True,
            "reviewed_files_match_archive": True,
        },
        "module": {
            **module,
            "umbrella": {
                "portable_path": "modules/juce_dsp/juce_dsp.h",
                **_path_fact(umbrella),
            },
            "implementation": {
                "portable_path": "modules/juce_dsp/juce_dsp.cpp",
                **_path_fact(implementation),
            },
            "public_umbrella_header_count": len(values),
            "present_in_current_schuss_source_lock": "juce_dsp" in lock["modules"],
        },
        "entries": {
            "portable_path": "catalog/reviews/task033-juce-dsp-audit-v1/headers.jsonl",
            **_fact(entries_bytes),
        },
        "counts": {
            "total": len(values),
            "classifications": dict(sorted(classification_counts.items())),
            "recommendations": dict(sorted(recommendation_counts.items())),
        },
        "decision": "Do not import juce_dsp in Task 033. Keep simple selected semantics JUCE-independent; consider richer candidates only in a later static JUCE host provider with an explicit desktop-float target/backend; defer utilities and unresolved subjects.",
        "evidence_boundary": "Authenticated source and architecture audit only; no catalog object, graph contract, provider, link, runtime, real-time, audible, or distribution approval is created.",
    }
    return entries_bytes, _canonical_bytes(manifest)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--juce-root", type=Path, required=True)
    parser.add_argument("--juce-archive", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    mutable_entries, mutable_manifest = generate_mutable()
    juce_entries, juce_manifest = generate_juce(args.juce_root, args.juce_archive)
    outputs = {
        MUTABLE_OUTPUT / "entries.jsonl": mutable_entries,
        MUTABLE_OUTPUT / "manifest.json": mutable_manifest,
        JUCE_OUTPUT / "headers.jsonl": juce_entries,
        JUCE_OUTPUT / "manifest.json": juce_manifest,
    }
    for path, data in outputs.items():
        _write_or_check(path, data, args.check)
    print("Task 033 Phase 1 audits: fresh" if args.check else "wrote Task 033 Phase 1 audits")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
