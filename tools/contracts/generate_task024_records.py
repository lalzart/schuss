#!/usr/bin/env python3
"""Generate Task 024 coverage, catalog successor, and Task 025 selection."""

from __future__ import annotations

import argparse
import copy
import hashlib
import io
import json
import re
import subprocess
import sys
import tarfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/contracts")]

from packages.schuss_core.control_plane import load_repository_context  # noqa: E402

import record_set_rules  # noqa: E402
import validator_core as core  # noqa: E402


PARENT = ROOT / "contracts/record-sets/task023-application-spine-v1.json"
OUTPUT = ROOT / "contracts/record-sets/task024-catalog-coverage-v1.json"
RECORD_ROOT = ROOT / "contracts/task024"
REVIEW_ROOT = ROOT / "catalog/reviews/task024-catalog-coverage-v1"
CURRENT_REVIEW_ROOT = ROOT / "catalog/reviews/task024-current-ksoloti-v1"
EVIDENCE_ROOT = ROOT / "evidence/task024-completion-v1"
SNAPSHOT_ROOT = ROOT / "catalog/snapshots/legacy-resolved-catalog-v0"
OBJECTS = SNAPSHOT_ROOT / "resolved/objects.jsonl"
GRAPHS = SNAPSHOT_ROOT / "resolved/graphs.jsonl"
FROZEN_MANIFEST_SHA256 = "0e3f3cb763f634ce490195e2cd4665c2e1a41764cd54c6526e6e219f18e1e959"
CURRENT_CORPUS_ID = "schuss-current-ksoloti-corpus-000001"
CURRENT_CORPUS_LIBRARIES = ("axoloti-factory", "ksoloti-objects")
KSOLOTI_CONFIGURED_LIBRARIES = (
    "axoloti-factory",
    "axoloti-contrib",
    "ksoloti-objects",
    "ksoloti-contrib",
)
FUNCTION_CATEGORIES = (
    "input-output",
    "sound-sources",
    "sampling-buffers",
    "modulation-control",
    "filters-resonators",
    "shaping-dynamics",
    "delay-reverb",
    "spectral-analysis",
    "mixing-routing",
    "pitch-notes",
    "timing-sequencing",
    "data-math-logic",
    "interface-system",
)


FAMILIES: tuple[dict[str, Any], ...] = (
    {"variant": 663, "name": "Constant String", "aliases": ["Text Constant"], "category": "interface-system", "tags": ["message-construction"], "description": "Provides an exact constant text value to compatible message-oriented graph services.", "rationale": "The highest complete-graph reference count in the unreviewed population and an explicit constant-string interface justify catalog review without implying DSP support."},
    {"variant": 180, "name": "Analog Voltage Input", "aliases": ["GPIO Analog Input"], "category": "input-output", "tags": ["hardware-input"], "description": "Reads one externally selected analog-voltage input as a control value.", "rationale": "A frequently selected physical-input primitive with explicit source documentation; electrical and device validation remain separate."},
    {"variant": 382, "name": "Monophonic MIDI Note Input", "aliases": ["MIDI Keyboard Note"], "category": "pitch-notes", "tags": ["note-input", "midi"], "description": "Produces monophonic note, gate, velocity, and release-velocity values from MIDI input.", "rationale": "High graph usage and an explicit note/gate interface make this a central authoring source while runtime MIDI behavior remains unproved."},
    {"variant": 199, "name": "Control Low-pass Filter", "aliases": ["K-rate Lowpass"], "category": "filters-resonators", "tags": ["variable-filtering", "control-smoothing"], "description": "Applies a first-order low-pass response to a control-rate signal.", "rationale": "The observation is a compact high-use control smoother with an explicit rate and filter role."},
    {"variant": 23, "name": "Unipolar to Bipolar Converter", "aliases": ["Range Bipolarizer"], "category": "data-math-logic", "tags": ["range-conversion"], "description": "Maps a unipolar control range into a bipolar control range.", "rationale": "The exact converter is broadly reused and its functional role is explicit even though overload siblings remain separate."},
    {"variant": 269, "name": "Constant Multiplier", "aliases": ["Multiply by Constant"], "category": "data-math-logic", "tags": ["mathematical-arithmetic"], "description": "Multiplies one signal by a retained constant control value.", "rationale": "A high-use arithmetic primitive selected as one exact overload; sibling overload observations are not collapsed."},
    {"variant": 495, "name": "Eight-input Multiplexer", "aliases": ["8-way Signal Selector"], "category": "mixing-routing", "tags": ["signal-selection"], "description": "Selects one of eight input values using a control selector.", "rationale": "The exact eight-input overload is heavily reused and adds explicit routing breadth without merging its typed siblings."},
    {"variant": 223, "name": "Boolean Inverter", "aliases": ["Logic NOT"], "category": "data-math-logic", "tags": ["boolean-logic"], "description": "Inverts one Boolean input value.", "rationale": "A high-frequency, single-purpose Boolean primitive with an unambiguous reviewed interface."},
    {"variant": 123, "name": "Decay Envelope", "aliases": ["D Envelope"], "category": "modulation-control", "tags": ["envelope-generation"], "description": "Generates a decaying control contour from an incoming trigger.", "rationale": "A commonly reused envelope building block that broadens modulation coverage beyond the existing attack-decay family."},
    {"variant": 162, "name": "Control-rate Resonant Low-pass", "aliases": ["K-rate VCF"], "category": "filters-resonators", "tags": ["variable-filtering", "resonance"], "description": "Applies a two-pole resonant low-pass response updated at control rate.", "rationale": "The source explicitly identifies rate, topology, and filter role and has substantial complete-graph use."},
    {"variant": 611, "name": "Triggered Uniform Random", "aliases": ["Triggered White Random"], "category": "modulation-control", "tags": ["random-generation"], "description": "Produces a new uniformly distributed control value when triggered.", "rationale": "The observation is a high-use, explicit triggered modulation source; its random sequence semantics remain unproved."},
    {"variant": 11, "name": "Integer Constant", "aliases": ["Constant Integer"], "category": "data-math-logic", "tags": ["constant-value"], "description": "Provides one configured integer value to the graph.", "rationale": "A common support primitive whose exact integer role is directly stated by its source interface."},
    {"variant": 675, "name": "Pitched Table Player", "aliases": ["Sample Table Player"], "category": "sampling-buffers", "tags": ["sample-playback", "pitch-control"], "description": "Plays audio from a referenced table with position and pitch control.", "rationale": "A frequent sampling primitive that expands application browsing while asset and playback semantics remain separately gated."},
    {"variant": 224, "name": "Clocked Value Latch", "aliases": ["Triggered Latch"], "category": "data-math-logic", "tags": ["state", "sample-and-hold"], "description": "Copies its input to retained output on a rising trigger edge.", "rationale": "The explicit retained-state description and broad graph use support a distinct stateful utility family."},
    {"variant": 226, "name": "Two-input Boolean OR", "aliases": ["Logic OR"], "category": "data-math-logic", "tags": ["boolean-logic"], "description": "Computes the Boolean OR of two input values.", "rationale": "A high-use exact Boolean primitive needed for general graph authoring."},
    {"variant": 132, "name": "All-pass Reverb Section", "aliases": ["All-pass Delay Section"], "category": "delay-reverb", "tags": ["time-processing", "diffusion"], "description": "Applies one all-pass delay section suitable for reverb diffusion networks.", "rationale": "The source explicitly identifies a reusable reverb section; full-network and audible behavior are not inferred."},
    {"variant": 421, "name": "Two-input Audio Mixer", "aliases": ["2-channel Audio Mixer"], "category": "mixing-routing", "tags": ["mixing"], "description": "Combines two audio-rate inputs with independent gains.", "rationale": "A compact high-use routing primitive selected as one exact audio-rate overload."},
    {"variant": 318, "name": "Saturating Gain", "aliases": ["Saturated Amplifier"], "category": "shaping-dynamics", "tags": ["gain", "distortion"], "description": "Applies positive gain with retained saturation behavior.", "rationale": "The explicit gain-and-saturation role and complete-graph use justify a distinct shaping family."},
    {"variant": 44, "name": "Interpolated Delay Reader", "aliases": ["Linear Delay Tap"], "category": "delay-reverb", "tags": ["time-processing", "interpolation"], "description": "Reads a referenced delay line using linear interpolation.", "rationale": "A frequently reused exact delay-line consumer with explicit interpolation behavior at the source boundary."},
    {"variant": 47, "name": "SDRAM Delay Writer", "aliases": ["Delay Line Definition"], "category": "delay-reverb", "tags": ["time-processing", "buffer-recording"], "description": "Defines and writes an SDRAM-backed delay line for exact named readers.", "rationale": "This is the paired high-use delay-line owner needed to make delay authoring discoverable while dependency semantics remain unresolved."},
)


FAMILY_DECISIONS: dict[int, dict[str, Any]] = {
    663: {"treatment": "retain", "visibility": "advanced", "category": "data-math-logic"},
    180: {"treatment": "reconsider", "visibility": "review-only", "category": "interface-system"},
    382: {
        "treatment": "revise", "visibility": "default", "category": "input-output",
        "name": "Selected MIDI Note Gate/Input", "aliases": ["Configured MIDI Note Gate", "MIDI Keyboard Note"],
        "description": "Filters one configured MIDI note and exposes gate, velocity, and release-velocity values.",
        "rationale": "The current exact object filters one configured note and does not expose a note or pitch output; the revised name and Input & Output placement preserve that boundary.",
    },
    199: {"treatment": "retain", "visibility": "default"},
    23: {"treatment": "revise", "visibility": "default"},
    269: {"treatment": "revise", "visibility": "advanced"},
    495: {"treatment": "revise", "visibility": "default"},
    223: {"treatment": "retain", "visibility": "advanced"},
    123: {"treatment": "retain", "visibility": "default"},
    162: {
        "treatment": "revise", "visibility": "default",
        "name": "Two-pole Resonant Audio Low-pass", "aliases": ["VCF3", "K-rate-coefficient VCF"],
        "description": "Processes an audio-rate signal through a two-pole resonant low-pass whose coefficients update at control rate.",
        "rationale": "The current exact source has audio-buffer input and output; only coefficient calculation is control-rate, so the prior family name was misleading.",
    },
    611: {"treatment": "retain", "visibility": "default"},
    11: {"treatment": "retain", "visibility": "advanced"},
    675: {"treatment": "retain", "visibility": "default"},
    224: {
        "treatment": "revise", "visibility": "advanced",
        "name": "Triggered Value Latch", "aliases": ["Clocked Value Latch", "Triggered Latch"],
        "rationale": "The current base reference contains fractional and integer variants that copy input on a rising trigger; value type remains a form/contract distinction.",
    },
    226: {"treatment": "retain", "visibility": "advanced"},
    132: {"treatment": "retain", "visibility": "advanced"},
    421: {"treatment": "reconsider", "visibility": "review-only"},
    318: {"treatment": "revise", "visibility": "default"},
    44: {"treatment": "retain", "visibility": "advanced"},
    47: {"treatment": "retain", "visibility": "advanced"},
}


TASK025_IMPLEMENTATIONS = {
    "schuss-component-contract-000003": "schuss-implementation-000046",
    "schuss-component-contract-000009": "schuss-implementation-000048",
    "schuss-component-contract-000012": "schuss-implementation-000051",
    "schuss-component-contract-000013": "schuss-implementation-000052",
    "schuss-component-contract-000015": "schuss-implementation-000054",
    "schuss-component-contract-000016": "schuss-implementation-000055",
    "schuss-component-contract-000017": "schuss-implementation-000056",
    "schuss-component-contract-000020": "schuss-implementation-000059",
}


def _canonical_bytes(value: Any) -> bytes:
    return core.canonical_json(value).encode("utf-8") + b"\n"


def _child(value: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(value)
    result["content_hash"] = "sha256:" + hashlib.sha256(
        core.canonical_json({key: item for key, item in result.items() if key != "content_hash"}).encode("utf-8")
    ).hexdigest()
    return result


def _record(value: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(value)
    result["content_hash"] = "sha256:" + "0" * 64
    errors = core.schema_errors(result, schema, schema)
    if errors:
        raise ValueError("; ".join(errors))
    result["content_hash"] = core.record_content_hash(result, schema)
    return result


def _ref(record: dict[str, Any], id_field: str, *, generic: bool = False) -> dict[str, Any]:
    key = "stable_id" if generic else id_field
    return {key: record[id_field], "revision": record["revision"], "content_hash": record["content_hash"]}


def _merged_family_spec(spec: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(spec)
    merged.update(copy.deepcopy(FAMILY_DECISIONS[spec["variant"]]))
    return merged


def _local_sources() -> dict[str, Path]:
    path = ROOT / "catalog/sources.local.yml"
    if not path.is_file():
        raise ValueError("current Ksoloti generation requires ignored catalog/sources.local.yml")
    result: dict[str, Path] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^  ([a-z0-9-]+):\s+(.+?)\s*$", line)
        if match:
            result[match.group(1)] = Path(match.group(2))
    return result


def _git_bytes(checkout: Path, commit: str, source_path: str) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(checkout), "show", f"{commit}:{source_path}"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        raise ValueError(
            f"pinned source is unavailable: {checkout.name}@{commit}:{source_path}"
        )
    return completed.stdout


def _git_object_paths(checkout: Path, commit: str) -> list[str]:
    completed = subprocess.run(
        ["git", "-C", str(checkout), "ls-tree", "-r", "-z", "--name-only", commit, "--", "objects"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        raise ValueError(f"pinned source tree is unavailable: {checkout.name}@{commit}")
    return sorted(
        item.decode("utf-8")
        for item in completed.stdout.split(b"\0")
        if item
    )


def _git_object_files(checkout: Path, commit: str) -> dict[str, bytes]:
    completed = subprocess.run(
        ["git", "-C", str(checkout), "archive", "--format=tar", commit, "--", "objects"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        raise ValueError(f"pinned source archive is unavailable: {checkout.name}@{commit}")
    result: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(completed.stdout), mode="r:") as archive:
        for member in archive.getmembers():
            if not member.isfile():
                continue
            extracted = archive.extractfile(member)
            if extracted is None:
                raise ValueError(f"pinned source archive member is unreadable: {member.name}")
            result[member.name] = extracted.read()
    return result


def _xml_local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _xml_text(element: ET.Element, name: str) -> str:
    for child in element:
        if _xml_local_name(child.tag) == name:
            return (child.text or "").strip()
    return ""


def _xml_string_list(element: ET.Element, name: str) -> list[str]:
    for child in element:
        if _xml_local_name(child.tag) != name:
            continue
        return sorted(
            {
                (item.text or "").strip()
                for item in child.iter()
                if item is not child and (item.text or "").strip()
            }
        )
    return []


def _xml_signature(element: ET.Element) -> dict[str, list[dict[str, str]]]:
    result: dict[str, list[dict[str, str]]] = {}
    for source_name, output_name in (
        ("inlets", "inlets"),
        ("outlets", "outlets"),
        ("params", "parameters"),
        ("attribs", "attributes"),
    ):
        values: list[dict[str, str]] = []
        for child in element:
            if _xml_local_name(child.tag) != source_name:
                continue
            for item in child:
                values.append(
                    {
                        "name": item.attrib.get("name", ""),
                        "type": _xml_local_name(item.tag),
                    }
                )
        result[output_name] = values
    return result


def _lineage_indexes(observations: list[dict[str, Any]]) -> tuple[dict[tuple[str, str], list[str]], dict[tuple[str, str, str, str], list[str]], dict[tuple[str, str, str], list[str]]]:
    by_uuid: dict[tuple[str, str], list[str]] = defaultdict(list)
    by_definition: dict[tuple[str, str, str, str], list[str]] = defaultdict(list)
    by_source: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    for observation in observations:
        reference = f"legacy-resolved-catalog-v0:object:{observation['variant_index']}"
        origin = observation["origin"]
        if not {"source_id", "path", "sha256"} <= set(origin):
            continue
        durable = observation["uuid"].get("durable_value")
        if observation["uuid"].get("runtime_kind") == "explicit" and durable:
            by_uuid[(origin["source_id"], durable)].append(reference)
        by_definition[(origin["source_id"], origin["path"], origin["sha256"], observation["legacy_id"])].append(reference)
        by_source[(origin["source_id"], origin["path"], origin["sha256"])].append(reference)
    return by_uuid, by_definition, by_source


def _current_candidates(
    observations: list[dict[str, Any]],
    source_lock: dict[str, Any],
    local_sources: dict[str, Path],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    locked = {item["id"]: item for item in source_lock["sources"]}
    by_uuid, by_definition, by_source = _lineage_indexes(observations)
    grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
    library_summaries: list[dict[str, Any]] = []
    for library_id in KSOLOTI_CONFIGURED_LIBRARIES:
        lock = locked[library_id]
        checkout = local_sources.get(library_id)
        if checkout is None:
            raise ValueError(f"local source mapping is absent: {library_id}")
        paths = _git_object_paths(checkout, lock["commit"])
        axo_paths = [path for path in paths if path.endswith(".axo")]
        axs_paths = [path for path in paths if path.endswith(".axs")]
        primary = library_id in CURRENT_CORPUS_LIBRARIES
        library_summaries.append(
            {
                "library_id": library_id,
                "commit": lock["commit"],
                "ksoloti_default_enabled": True,
                "schuss_curation_role": "primary-first-party" if primary else "deferred-provenance-cohort",
                "candidate_indexed": primary,
                "axo_file_count": len(axo_paths),
                "axs_file_count": len(axs_paths),
            }
        )
        if not primary:
            continue
        object_files = _git_object_files(checkout, lock["commit"])
        for source_path in axo_paths:
            raw = object_files[source_path]
            source_sha256 = hashlib.sha256(raw).hexdigest()
            try:
                root = ET.fromstring(raw)
            except ET.ParseError as exc:
                raise ValueError(f"current Ksoloti object XML is invalid: {library_id}:{source_path}: {exc}") from exc
            relative_file = Path(source_path).relative_to("objects")
            for element in root:
                if _xml_local_name(element.tag) != "obj.normal":
                    continue
                local_id = element.attrib.get("id", "").strip()
                if not local_id:
                    raise ValueError(f"current Ksoloti normal definition has no local ID: {library_id}:{source_path}")
                folder = relative_file.parent.as_posix()
                canonical_id = local_id if folder == "." else f"{folder}/{local_id}"
                base_ref = f"{library_id}:{canonical_id}"
                legacy_uuid = element.attrib.get("uuid", "").strip()
                legacy_sha = element.attrib.get("sha", "").strip()
                legacy_hashes = sorted(
                    {
                        value
                        for value in (
                            legacy_sha,
                            *[
                                (child.text or "").strip()
                                for child in element
                                if _xml_local_name(child.tag) == "upgradeSha"
                            ],
                        )
                        if value
                    }
                )
                object_sha256 = hashlib.sha256(ET.tostring(element, encoding="utf-8")).hexdigest()
                variant_id = legacy_uuid or legacy_sha or object_sha256[:20]
                references = by_uuid.get((library_id, legacy_uuid), []) if legacy_uuid else []
                if not references:
                    references = by_definition.get((library_id, source_path, source_sha256, canonical_id), [])
                key = (library_id, canonical_id, "axo-normal-definition")
                candidate = grouped.setdefault(
                    key,
                    {
                        "schema_version": "current-ksoloti-candidate-v0",
                        "candidate_ref": f"{base_ref}#axo-normal-definition",
                        "base_ref": base_ref,
                        "library_id": library_id,
                        "canonical_id": canonical_id,
                        "path_root": canonical_id.split("/", 1)[0],
                        "import_form": "axo-normal-definition",
                        "variants": [],
                    },
                )
                candidate["variants"].append(
                    {
                        "variant_ref": f"{base_ref}@{variant_id}",
                        "variant_id": variant_id,
                        "identity_kind": "legacy-uuid" if legacy_uuid else ("legacy-sha" if legacy_sha else "object-content-hash"),
                        "legacy_uuid": legacy_uuid or None,
                        "legacy_hashes": legacy_hashes,
                        "source_path": source_path,
                        "source_sha256": source_sha256,
                        "object_sha256": object_sha256,
                        "description": _xml_text(element, "sDescription"),
                        "author": _xml_text(element, "author"),
                        "declared_license": _xml_text(element, "license"),
                        "signature": _xml_signature(element),
                        "declared_includes": _xml_string_list(element, "includes"),
                        "declared_dependencies": _xml_string_list(element, "depends"),
                        "frozen_lineage_refs": sorted(references),
                    }
                )
        for source_path in axs_paths:
            raw = object_files[source_path]
            source_sha256 = hashlib.sha256(raw).hexdigest()
            canonical_id = Path(source_path).relative_to("objects").with_suffix("").as_posix()
            base_ref = f"{library_id}:{canonical_id}"
            references = by_source.get((library_id, source_path, source_sha256), [])
            grouped[(library_id, canonical_id, "axs-unloaded-subpatch")] = {
                "schema_version": "current-ksoloti-candidate-v0",
                "candidate_ref": f"{base_ref}#axs-unloaded-subpatch",
                "base_ref": base_ref,
                "library_id": library_id,
                "canonical_id": canonical_id,
                "path_root": canonical_id.split("/", 1)[0],
                "import_form": "axs-unloaded-subpatch",
                "variants": [
                    {
                        "variant_ref": f"{base_ref}@source-sha256:{source_sha256}",
                        "variant_id": f"source-sha256:{source_sha256}",
                        "identity_kind": "source-file",
                        "legacy_uuid": None,
                        "legacy_hashes": [],
                        "source_path": source_path,
                        "source_sha256": source_sha256,
                        "object_sha256": source_sha256,
                        "description": "",
                        "author": "",
                        "declared_license": "",
                        "signature": {"inlets": [], "outlets": [], "parameters": [], "attributes": []},
                        "declared_includes": [],
                        "declared_dependencies": [],
                        "frozen_lineage_refs": sorted(references),
                    }
                ],
            }
    candidates: list[dict[str, Any]] = []
    for key in sorted(grouped):
        candidate = grouped[key]
        candidate["variants"].sort(key=lambda item: item["variant_ref"])
        lineage = [bool(item["frozen_lineage_refs"]) for item in candidate["variants"]]
        candidate["lineage_status"] = "complete" if all(lineage) else ("partial" if any(lineage) else "absent")
        candidates.append(candidate)
    return candidates, sorted(library_summaries, key=lambda item: item["library_id"])


def _schema_files() -> dict[str, dict[str, Any]]:
    corpus = copy.deepcopy(core.load_json(ROOT / "schemas/catalog-corpus-v2.schema.json"))
    corpus["$id"] = "catalog-corpus-v3.schema.json"
    corpus["title"] = "Schuss exact reviewed catalog corpus v3"
    corpus["properties"]["schema_version"] = {"const": "catalog-corpus-v3"}
    corpus["properties"]["revision"] = {"const": 3}
    corpus["properties"]["projection_version"] = {"const": "schuss-catalog-projection-v3"}
    corpus["properties"]["family_additions"].update({"minItems": 34, "maxItems": 34})
    corpus["properties"]["implementation_additions"].update({"minItems": 44, "maxItems": 44})
    corpus["$defs"]["catalogReference"]["properties"]["revision"] = {"const": 2}
    for definition in ("familyAddition", "implementationAddition"):
        enum = corpus["$defs"][definition]["properties"]["review_status"]["enum"]
        if "task024-reviewed" not in enum:
            enum.append("task024-reviewed")
    corpus["required"].append("coverage_review")
    corpus["properties"]["coverage_review"] = {
        "type": "object", "additionalProperties": False,
        "required": ["review_id", "frozen_observation_count", "additional_family_count", "frequency_policy", "disposition_policy"],
        "properties": {
            "review_id": {"const": "task024-catalog-coverage-v1"},
            "frozen_observation_count": {"const": 3602},
            "additional_family_count": {"const": 20},
            "frequency_policy": {"const": "prioritization-only"},
            "disposition_policy": {"const": "task024-disposition-precedence-v1"},
        },
    }
    corpus["required"].append("current_ksoloti_review")
    corpus["properties"]["current_ksoloti_review"] = {
        "type": "object", "additionalProperties": False,
        "required": ["source_corpus_reference", "authority_policy", "frozen_inventory_role", "family_treatments"],
        "properties": {
            "source_corpus_reference": {
                "type": "object", "additionalProperties": False,
                "required": ["current_ksoloti_corpus_id", "revision", "content_hash"],
                "properties": {
                    "current_ksoloti_corpus_id": {"const": CURRENT_CORPUS_ID},
                    "revision": {"const": 1},
                    "content_hash": {"$ref": "#/$defs/contentHash"},
                },
            },
            "authority_policy": {"const": "current-ksoloti-base-ref-cohorts-first-object-level-semantic-review-required"},
            "frozen_inventory_role": {"const": "immutable-provenance-lineage-and-gap-evidence-not-product-backlog"},
            "family_treatments": {
                "type": "array", "x-schuss-array-kind": "set", "uniqueItems": True,
                "minItems": 20, "maxItems": 20,
                "items": {
                    "type": "object", "additionalProperties": False,
                    "required": ["family_reference", "treatment", "drawer_visibility", "current_base_refs", "candidate_variant_count", "catalogued_variant_count", "implementation_ids", "rationale"],
                    "properties": {
                        "family_reference": {"$ref": "#/$defs/familyReference"},
                        "treatment": {"enum": ["retain", "revise", "reconsider"]},
                        "drawer_visibility": {"enum": ["default", "advanced", "review-only"]},
                        "current_base_refs": {"$ref": "#/$defs/stringSet"},
                        "candidate_variant_count": {"type": "integer", "minimum": 1},
                        "catalogued_variant_count": {"type": "integer", "minimum": 1},
                        "implementation_ids": {
                            "type": "array", "x-schuss-array-kind": "set", "uniqueItems": True,
                            "minItems": 1, "items": {"$ref": "#/$defs/implementationId"},
                        },
                        "rationale": {"type": "string", "minLength": 1},
                    },
                },
            },
        },
    }

    projection = copy.deepcopy(core.load_json(ROOT / "schemas/catalog-projection-v2.schema.json"))
    projection["$id"] = "catalog-projection-v3.schema.json"
    projection["title"] = "Schuss derived catalog projection v3"
    projection["properties"]["schema_version"] = {"const": "catalog-projection-v3"}
    projection["properties"]["projection_version"] = {"const": "schuss-catalog-projection-v3"}
    projection["properties"]["families"].update({"minItems": 60, "maxItems": 60})
    projection["$defs"]["catalogReference"]["properties"]["revision"] = {"const": 3}
    projection_family = projection["$defs"]["familyEntry"]
    projection_family["required"].extend(
        ["curation_treatment", "drawer_visibility", "current_ksoloti_base_refs", "current_variant_coverage"]
    )
    projection_family["properties"].update(
        {
            "curation_treatment": {"enum": ["accepted", "retain", "revise", "reconsider"]},
            "drawer_visibility": {"enum": ["default", "advanced", "review-only"]},
            "current_ksoloti_base_refs": {"$ref": "#/$defs/stringSet"},
            "current_variant_coverage": {
                "type": "object", "additionalProperties": False,
                "required": ["candidate_variant_count", "catalogued_variant_count"],
                "properties": {
                    "candidate_variant_count": {"type": "integer", "minimum": 0},
                    "catalogued_variant_count": {"type": "integer", "minimum": 0},
                },
            },
        }
    )

    content_hash = {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"}
    exact_reference = {
        "type": "object", "additionalProperties": False,
        "required": ["stable_id", "revision", "content_hash"],
        "properties": {
            "stable_id": {"type": "string", "pattern": "^schuss-[a-z0-9-]+-[0-9]{6}$"},
            "revision": {"type": "integer", "minimum": 1}, "content_hash": content_hash,
        },
    }
    evidence_level = {
        "type": "object", "additionalProperties": False,
        "required": ["level", "status"],
        "properties": {"level": {"type": "integer", "minimum": 1, "maximum": 8}, "status": {"enum": ["passed", "not-run"]}},
    }
    disposition_counts = {
        key: {"type": "integer", "minimum": 0}
        for key in ("reviewed-family", "implementation-variant", "overload-group", "duplicate", "editor-only-non-headless", "unresolved", "queued-human-review")
    }
    coverage = {
        "$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "catalog-coverage-v0.schema.json",
        "title": "Schuss frozen catalog coverage report v0", "type": "object", "additionalProperties": False,
        "required": ["schema_version", "canonical_profile", "coverage_report_id", "revision", "content_hash", "review_id", "snapshot", "total_observations", "disposition_policy", "disposition_counts", "reviewed_family_count", "additional_family_count", "review_queue_count", "frequency_policy", "evidence_levels"],
        "properties": {
            "schema_version": {"const": "catalog-coverage-v0"}, "canonical_profile": {"const": "schuss-canonical-json-v1"},
            "coverage_report_id": {"const": "schuss-coverage-report-000002"}, "revision": {"const": 1}, "content_hash": content_hash,
            "review_id": {"const": "task024-catalog-coverage-v1"},
            "snapshot": {"type": "object", "additionalProperties": False, "required": ["schema_version", "manifest_sha256"], "properties": {"schema_version": {"const": "legacy-resolved-catalog-v0"}, "manifest_sha256": {"const": FROZEN_MANIFEST_SHA256}}},
            "total_observations": {"const": 3602}, "disposition_policy": {"const": "task024-disposition-precedence-v1"},
            "disposition_counts": {"type": "object", "additionalProperties": False, "required": list(disposition_counts), "properties": disposition_counts},
            "reviewed_family_count": {"const": 60}, "additional_family_count": {"const": 20},
            "review_queue_count": {"type": "integer", "minimum": 0}, "frequency_policy": {"const": "prioritization-only"},
            "evidence_levels": {"type": "array", "x-schuss-array-kind": "sequence", "minItems": 8, "maxItems": 8, "items": evidence_level},
        },
    }
    subject = {
        "type": "object", "additionalProperties": False,
        "required": ["node_ids", "role", "family_reference", "implementation_reference", "contract_reference", "current_readiness"],
        "properties": {
            "node_ids": {"type": "array", "x-schuss-array-kind": "set", "uniqueItems": True, "minItems": 1, "items": {"type": "string", "pattern": "^graph-node-[0-9]{6}$"}},
            "role": {"type": "string", "minLength": 1}, "family_reference": exact_reference,
            "implementation_reference": exact_reference, "contract_reference": exact_reference,
            "current_readiness": {"type": "array", "x-schuss-array-kind": "set", "uniqueItems": True, "minItems": 1, "items": {"enum": ["catalogued-only", "contracted", "bound", "eligible", "compile-proven", "device-tested", "real-time-tested", "audible-tested", "unresolved"]}},
        },
    }
    task025 = {
        "$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "task025-selection-packet-v0.schema.json",
        "title": "Schuss Task 025 exact compiler selection packet v0", "type": "object", "additionalProperties": False,
        "required": ["schema_version", "canonical_profile", "selection_packet_id", "revision", "content_hash", "catalog_reference", "source_graph_reference", "selection_rule", "subjects", "evidence_levels", "prohibited_expansion"],
        "properties": {
            "schema_version": {"const": "task025-selection-packet-v0"}, "canonical_profile": {"const": "schuss-canonical-json-v1"},
            "selection_packet_id": {"const": "schuss-core-selection-000002"}, "revision": {"const": 1}, "content_hash": content_hash,
            "catalog_reference": exact_reference, "source_graph_reference": exact_reference,
            "selection_rule": {"const": "exact-distinct-contracts-in-schuss-graph-000004-r1"},
            "subjects": {"type": "array", "x-schuss-array-kind": "sequence", "minItems": 8, "maxItems": 8, "items": subject},
            "evidence_levels": {"type": "array", "x-schuss-array-kind": "sequence", "minItems": 8, "maxItems": 8, "items": evidence_level},
            "prohibited_expansion": {"type": "array", "x-schuss-array-kind": "set", "uniqueItems": True, "minItems": 4, "items": {"type": "string", "minLength": 1}},
        },
    }
    review_manifest = {
        "$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "catalog-review-manifest-v0.schema.json",
        "title": "Schuss deterministic catalog review artifact manifest v0", "type": "object", "additionalProperties": False,
        "required": ["schema_version", "review_id", "snapshot_manifest_sha256", "observation_count", "artifacts"],
        "properties": {
            "schema_version": {"const": "catalog-review-manifest-v0"}, "review_id": {"const": "task024-catalog-coverage-v1"},
            "snapshot_manifest_sha256": {"const": FROZEN_MANIFEST_SHA256}, "observation_count": {"const": 3602},
            "artifacts": {"type": "array", "x-schuss-array-kind": "sequence", "minItems": 3, "maxItems": 3, "items": {"type": "object", "additionalProperties": False, "required": ["portable_path", "byte_sha256", "record_count"], "properties": {"portable_path": {"type": "string", "pattern": "^(reports|packets)/[a-z0-9.-]+$"}, "byte_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"}, "record_count": {"type": "integer", "minimum": 1}}}},
        },
    }
    signature_atom = {
        "type": "object", "additionalProperties": False,
        "required": ["name", "type"],
        "properties": {"name": {"type": "string"}, "type": {"type": "string", "minLength": 1}},
    }
    candidate = {
        "$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "current-ksoloti-candidate-v0.schema.json",
        "title": "Current Ksoloti source candidate cohort v0", "type": "object", "additionalProperties": False,
        "required": ["schema_version", "candidate_ref", "base_ref", "library_id", "canonical_id", "path_root", "import_form", "variants", "lineage_status"],
        "properties": {
            "schema_version": {"const": "current-ksoloti-candidate-v0"},
            "candidate_ref": {"type": "string", "minLength": 1},
            "base_ref": {"type": "string", "minLength": 1},
            "library_id": {"enum": list(CURRENT_CORPUS_LIBRARIES)},
            "canonical_id": {"type": "string", "minLength": 1},
            "path_root": {"type": "string", "minLength": 1},
            "import_form": {"enum": ["axo-normal-definition", "axs-unloaded-subpatch"]},
            "lineage_status": {"enum": ["complete", "partial", "absent"]},
            "variants": {
                "type": "array", "x-schuss-array-kind": "sequence", "minItems": 1,
                "items": {
                    "type": "object", "additionalProperties": False,
                    "required": ["variant_ref", "variant_id", "identity_kind", "legacy_uuid", "legacy_hashes", "source_path", "source_sha256", "object_sha256", "description", "author", "declared_license", "signature", "declared_includes", "declared_dependencies", "frozen_lineage_refs"],
                    "properties": {
                        "variant_ref": {"type": "string", "minLength": 1},
                        "variant_id": {"type": "string", "minLength": 1},
                        "identity_kind": {"enum": ["legacy-uuid", "legacy-sha", "object-content-hash", "source-file"]},
                        "legacy_uuid": {"oneOf": [{"type": "null"}, {"type": "string", "minLength": 1}]},
                        "legacy_hashes": {"type": "array", "x-schuss-array-kind": "set", "uniqueItems": True, "items": {"type": "string", "minLength": 1}},
                        "source_path": {"type": "string", "pattern": "^objects/.+\\.(axo|axs)$"},
                        "source_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                        "object_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                        "description": {"type": "string"},
                        "author": {"type": "string"},
                        "declared_license": {"type": "string"},
                        "signature": {
                            "type": "object", "additionalProperties": False,
                            "required": ["inlets", "outlets", "parameters", "attributes"],
                            "properties": {
                                key: {"type": "array", "x-schuss-array-kind": "sequence", "items": signature_atom}
                                for key in ("inlets", "outlets", "parameters", "attributes")
                            },
                        },
                        "declared_includes": {"type": "array", "x-schuss-array-kind": "set", "uniqueItems": True, "items": {"type": "string", "minLength": 1}},
                        "declared_dependencies": {"type": "array", "x-schuss-array-kind": "set", "uniqueItems": True, "items": {"type": "string", "minLength": 1}},
                        "frozen_lineage_refs": {"type": "array", "x-schuss-array-kind": "set", "uniqueItems": True, "items": {"type": "string", "pattern": "^legacy-resolved-catalog-v0:object:[0-9]+$"}},
                    },
                },
            },
        },
    }
    portable_artifact = {
        "type": "object", "additionalProperties": False,
        "required": ["portable_path", "byte_sha256", "record_count"],
        "properties": {
            "portable_path": {"type": "string", "pattern": "^catalog/reviews/task024-current-ksoloti-v1/[a-z0-9.-]+$"},
            "byte_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            "record_count": {"type": "integer", "minimum": 1},
        },
    }
    source_evidence = {
        "type": "object", "additionalProperties": False,
        "required": ["source_id", "commit", "path", "byte_sha256", "role"],
        "properties": {
            "source_id": {"const": "patcher"},
            "commit": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
            "path": {"type": "string", "minLength": 1},
            "byte_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            "role": {"enum": ["default-library-configuration", "recursive-object-loader", "deterministic-base-reference-model"]},
        },
    }
    library_summary = {
        "type": "object", "additionalProperties": False,
        "required": ["library_id", "commit", "ksoloti_default_enabled", "schuss_curation_role", "candidate_indexed", "axo_file_count", "axs_file_count"],
        "properties": {
            "library_id": {"enum": list(KSOLOTI_CONFIGURED_LIBRARIES)},
            "commit": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
            "ksoloti_default_enabled": {"const": True},
            "schuss_curation_role": {"enum": ["primary-first-party", "deferred-provenance-cohort"]},
            "candidate_indexed": {"type": "boolean"},
            "axo_file_count": {"type": "integer", "minimum": 0},
            "axs_file_count": {"type": "integer", "minimum": 0},
        },
    }
    source_corpus = {
        "$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "current-ksoloti-corpus-v0.schema.json",
        "title": "Schuss current Ksoloti source corpus v0", "type": "object", "additionalProperties": False,
        "required": ["schema_version", "canonical_profile", "current_ksoloti_corpus_id", "revision", "content_hash", "decision_record", "model_authority", "configured_libraries", "primary_corpus", "functional_taxonomy", "dependency_model", "frozen_lineage", "evidence_levels"],
        "properties": {
            "schema_version": {"const": "current-ksoloti-corpus-v0"},
            "canonical_profile": {"const": "schuss-canonical-json-v1"},
            "current_ksoloti_corpus_id": {"const": CURRENT_CORPUS_ID},
            "revision": {"const": 1},
            "content_hash": content_hash,
            "decision_record": {
                "type": "object", "additionalProperties": False,
                "required": ["portable_path", "byte_sha256"],
                "properties": {
                    "portable_path": {"const": "contracts/task024/current-ksoloti-curation-decision.md"},
                    "byte_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                },
            },
            "model_authority": {"type": "array", "x-schuss-array-kind": "set", "uniqueItems": True, "minItems": 3, "maxItems": 3, "items": source_evidence},
            "configured_libraries": {"type": "array", "x-schuss-array-kind": "set", "uniqueItems": True, "minItems": 4, "maxItems": 4, "items": library_summary},
            "primary_corpus": {
                "type": "object", "additionalProperties": False,
                "required": ["library_ids", "axo_file_count", "normal_definition_count", "canonical_base_ref_count", "axs_compound_count", "candidate_count", "variant_count", "candidate_artifact"],
                "properties": {
                    "library_ids": {"type": "array", "x-schuss-array-kind": "set", "uniqueItems": True, "minItems": 2, "maxItems": 2, "items": {"enum": list(CURRENT_CORPUS_LIBRARIES)}},
                    "axo_file_count": {"const": 668},
                    "normal_definition_count": {"const": 835},
                    "canonical_base_ref_count": {"const": 666},
                    "axs_compound_count": {"const": 19},
                    "candidate_count": {"const": 685},
                    "variant_count": {"const": 854},
                    "candidate_artifact": portable_artifact,
                },
            },
            "functional_taxonomy": {
                "type": "object", "additionalProperties": False,
                "required": ["portable_path", "category_slugs", "path_policy"],
                "properties": {
                    "portable_path": {"const": "docs/TAXONOMY.md"},
                    "category_slugs": {"type": "array", "x-schuss-array-kind": "sequence", "minItems": 13, "maxItems": 13, "items": {"enum": list(FUNCTION_CATEGORIES)}},
                    "path_policy": {"const": "path-roots-are-candidate-crosswalk-evidence-object-review-is-required"},
                },
            },
            "dependency_model": {
                "type": "object", "additionalProperties": False,
                "required": ["policy", "declared_includes", "declared_dependencies"],
                "properties": {
                    "policy": {"const": "per-variant-declared-closure-facts-not-library-roots-or-families"},
                    "declared_includes": {"type": "array", "x-schuss-array-kind": "set", "uniqueItems": True, "items": {"type": "string", "minLength": 1}},
                    "declared_dependencies": {"type": "array", "x-schuss-array-kind": "set", "uniqueItems": True, "items": {"type": "string", "minLength": 1}},
                },
            },
            "frozen_lineage": {
                "type": "object", "additionalProperties": False,
                "required": ["schema_version", "manifest_sha256", "role", "known_traversal_limitations"],
                "properties": {
                    "schema_version": {"const": "legacy-resolved-catalog-v0"},
                    "manifest_sha256": {"const": FROZEN_MANIFEST_SHA256},
                    "role": {"const": "immutable-provenance-lineage-and-gap-evidence-not-product-backlog"},
                    "known_traversal_limitations": {"type": "array", "x-schuss-array-kind": "set", "uniqueItems": True, "minItems": 1, "items": {"type": "string", "minLength": 1}},
                },
            },
            "evidence_levels": {"type": "array", "x-schuss-array-kind": "sequence", "minItems": 8, "maxItems": 8, "items": evidence_level},
        },
    }
    return {
        "catalog-corpus-v3.schema.json": corpus,
        "catalog-projection-v3.schema.json": projection,
        "catalog-coverage-v0.schema.json": coverage,
        "task025-selection-packet-v0.schema.json": task025,
        "catalog-review-manifest-v0.schema.json": review_manifest,
        "current-ksoloti-candidate-v0.schema.json": candidate,
        "current-ksoloti-corpus-v0.schema.json": source_corpus,
    }


def _current_ksoloti_outputs(
    observations: list[dict[str, Any]],
    candidate_schema: dict[str, Any],
    corpus_schema: dict[str, Any],
) -> tuple[dict[str, bytes], dict[str, Any], list[dict[str, Any]]]:
    source_lock = core.load_json(ROOT / "catalog/sources.lock.json")
    locked = {item["id"]: item for item in source_lock["sources"]}
    local_sources = _local_sources()
    candidates, libraries = _current_candidates(observations, source_lock, local_sources)
    for candidate in candidates:
        errors = core.schema_errors(candidate, candidate_schema, candidate_schema)
        if errors:
            raise ValueError(
                f"current Ksoloti candidate schema invalid for {candidate['candidate_ref']}: "
                + "; ".join(errors)
            )
    normal_candidates = [item for item in candidates if item["import_form"] == "axo-normal-definition"]
    subpatch_candidates = [item for item in candidates if item["import_form"] == "axs-unloaded-subpatch"]
    normal_definitions = sum(len(item["variants"]) for item in normal_candidates)
    variant_count = sum(len(item["variants"]) for item in candidates)
    expected = {
        "normal_candidates": 666,
        "subpatch_candidates": 19,
        "normal_definitions": 835,
        "variant_count": 854,
    }
    actual = {
        "normal_candidates": len(normal_candidates),
        "subpatch_candidates": len(subpatch_candidates),
        "normal_definitions": normal_definitions,
        "variant_count": variant_count,
    }
    if actual != expected:
        raise ValueError(f"current Ksoloti primary census changed: expected {expected}, got {actual}")
    candidate_bytes = b"".join(_canonical_bytes(item) for item in candidates)
    artifact_path = "catalog/reviews/task024-current-ksoloti-v1/candidates.jsonl"
    model_paths = (
        ("src/main/java/axoloti/utils/Preferences.java", "default-library-configuration"),
        ("src/main/java/axoloti/object/AxoObjects.java", "recursive-object-loader"),
        ("ai/ksai.py", "deterministic-base-reference-model"),
    )
    patcher_lock = locked["patcher"]
    patcher_checkout = local_sources.get("patcher")
    if patcher_checkout is None:
        raise ValueError("local source mapping is absent: patcher")
    model_authority = []
    for source_path, role in model_paths:
        raw = _git_bytes(patcher_checkout, patcher_lock["commit"], source_path)
        model_authority.append(
            {
                "source_id": "patcher",
                "commit": patcher_lock["commit"],
                "path": source_path,
                "byte_sha256": hashlib.sha256(raw).hexdigest(),
                "role": role,
            }
        )
    declared_includes = sorted(
        {
            value
            for candidate in candidates
            for variant in candidate["variants"]
            for value in variant["declared_includes"]
        }
    )
    declared_dependencies = sorted(
        {
            value
            for candidate in candidates
            for variant in candidate["variants"]
            for value in variant["declared_dependencies"]
        }
    )
    decision_path = ROOT / "contracts/task024/current-ksoloti-curation-decision.md"
    if not decision_path.is_file():
        raise ValueError("Task 024 current-Ksoloti decision record is absent")
    source_corpus = _record(
        {
            "schema_version": "current-ksoloti-corpus-v0",
            "canonical_profile": "schuss-canonical-json-v1",
            "current_ksoloti_corpus_id": CURRENT_CORPUS_ID,
            "revision": 1,
            "decision_record": {
                "portable_path": decision_path.relative_to(ROOT).as_posix(),
                "byte_sha256": core.sha256_file(decision_path),
            },
            "model_authority": sorted(model_authority, key=core.canonical_json),
            "configured_libraries": libraries,
            "primary_corpus": {
                "library_ids": sorted(CURRENT_CORPUS_LIBRARIES),
                "axo_file_count": sum(item["axo_file_count"] for item in libraries if item["candidate_indexed"]),
                "normal_definition_count": normal_definitions,
                "canonical_base_ref_count": len(normal_candidates),
                "axs_compound_count": len(subpatch_candidates),
                "candidate_count": len(candidates),
                "variant_count": variant_count,
                "candidate_artifact": {
                    "portable_path": artifact_path,
                    "byte_sha256": hashlib.sha256(candidate_bytes).hexdigest(),
                    "record_count": len(candidates),
                },
            },
            "functional_taxonomy": {
                "portable_path": "docs/TAXONOMY.md",
                "category_slugs": list(FUNCTION_CATEGORIES),
                "path_policy": "path-roots-are-candidate-crosswalk-evidence-object-review-is-required",
            },
            "dependency_model": {
                "policy": "per-variant-declared-closure-facts-not-library-roots-or-families",
                "declared_includes": declared_includes,
                "declared_dependencies": declared_dependencies,
            },
            "frozen_lineage": {
                "schema_version": "legacy-resolved-catalog-v0",
                "manifest_sha256": FROZEN_MANIFEST_SHA256,
                "role": "immutable-provenance-lineage-and-gap-evidence-not-product-backlog",
                "known_traversal_limitations": sorted(
                    [
                        "The frozen raw traversal excludes directories named dist even when they contain legitimate Ksoloti objects.",
                        "The frozen raw traversal excludes directories named out even when they contain legitimate Ksoloti objects.",
                    ]
                ),
            },
            "evidence_levels": [
                {"level": level, "status": "passed" if level == 1 else "not-run"}
                for level in range(1, 9)
            ],
        },
        corpus_schema,
    )
    return {artifact_path: candidate_bytes}, source_corpus, candidates


def _source(observation: dict[str, Any]) -> dict[str, Any]:
    origin = observation["origin"]
    return {
        "evidence_ref": f"legacy-resolved-catalog-v0:object:{observation['variant_index']}",
        "canonical_observation_sha256": hashlib.sha256(core.canonical_json(observation).encode("utf-8")).hexdigest(),
        "source_id": origin["source_id"], "source_path": origin["path"], "source_sha256": origin["sha256"],
        "legacy_id": observation["legacy_id"],
        "legacy_uuid_sha256": "sha256:" + hashlib.sha256(observation["uuid"]["durable_value"].encode("utf-8")).hexdigest(),
    }


def _usage_counts(graphs: Iterable[dict[str, Any]]) -> Counter[int]:
    counts: Counter[int] = Counter()
    for graph in graphs:
        if graph["export_status"] != "complete":
            continue
        for instance in graph["instances"]:
            selected = instance.get("resolution", {}).get("legacy_selected")
            if isinstance(selected, dict) and selected.get("kind") == "catalog":
                counts[selected["variant_index"]] += 1
    return counts


def disposition_for(observation: dict[str, Any], *, reviewed: set[int], duplicate_uuids: set[str], overloaded_ids: set[str]) -> tuple[str, str]:
    runtime_kind = observation["uuid"]["runtime_kind"]
    if observation["export_status"] != "complete" or runtime_kind in {"sentinel", "unavailable"}:
        return "unresolved", "partial export or non-durable sentinel/unavailable identity"
    if observation["legacy_class"] in {"axoloti.object.AxoObjectComment", "axoloti.object.AxoObjectHyperlink", "axoloti.object.AxoObjectPatcher", "axoloti.object.AxoObjectPatcherObject"}:
        return "editor-only-non-headless", "explicit legacy editor/patcher class"
    if runtime_kind == "explicit" and observation["uuid"]["durable_value"] in duplicate_uuids:
        return "duplicate", "duplicate explicit durable UUID"
    if observation["variant_index"] in reviewed:
        return "reviewed-family", "exact accepted or Task 024 catalog source reference"
    if observation["legacy_id"] in overloaded_ids:
        return "overload-group", "legacy ID has multiple preserved observations"
    if observation["legacy_kind"] == "native_definition" and runtime_kind == "explicit":
        return "implementation-variant", "complete unique explicit-UUID native definition"
    return "queued-human-review", "complete observation requires durable identity or form review"


def _reviewed_indexes(parent_corpus: dict[str, Any], observations: list[dict[str, Any]]) -> set[int]:
    indexes: set[int] = {spec["variant"] for spec in FAMILIES}
    overlay = core.load_json(ROOT / "catalog/overlays/phase-4a-semantic-catalog-v0/catalog.json")
    for implementation in overlay["implementations"]:
        for reference in implementation.get("legacy_evidence_refs", ()):
            if reference.startswith("legacy-resolved-catalog-v0:object:"):
                indexes.add(int(reference.rsplit(":", 1)[1]))
    for implementation in parent_corpus["implementation_additions"]:
        authority = implementation.get("source_authority")
        source = implementation.get("source_observation")
        if authority and authority.get("kind") == "legacy-observation":
            source = authority["observation"]
        if source:
            indexes.add(int(source["evidence_ref"].rsplit(":", 1)[1]))
    if not indexes <= set(range(len(observations))):
        raise ValueError("reviewed observation reference is outside the frozen population")
    return indexes


def _coverage_outputs(observations: list[dict[str, Any]], graphs: list[dict[str, Any]], parent_corpus: dict[str, Any], coverage_schema: dict[str, Any], review_manifest_schema: dict[str, Any]) -> tuple[dict[str, bytes], dict[str, Any]]:
    by_id: dict[str, list[int]] = defaultdict(list)
    by_uuid: dict[str, list[int]] = defaultdict(list)
    for expected, observation in enumerate(observations):
        if observation["variant_index"] != expected:
            raise ValueError("frozen observation indexes are not consecutive")
        by_id[observation["legacy_id"]].append(expected)
        if observation["uuid"]["runtime_kind"] == "explicit":
            by_uuid[observation["uuid"]["durable_value"]].append(expected)
    overloaded_ids = {key for key, values in by_id.items() if len(values) > 1}
    duplicate_uuids = {key for key, values in by_uuid.items() if len(values) > 1}
    reviewed = _reviewed_indexes(parent_corpus, observations)
    usage = _usage_counts(graphs)
    disposition_records = []
    queue_records = []
    counts: Counter[str] = Counter()
    for observation in observations:
        disposition, rationale = disposition_for(observation, reviewed=reviewed, duplicate_uuids=duplicate_uuids, overloaded_ids=overloaded_ids)
        counts[disposition] += 1
        record = {
            "schema_version": "task024-observation-disposition-v0", "variant_index": observation["variant_index"],
            "evidence_ref": f"legacy-resolved-catalog-v0:object:{observation['variant_index']}",
            "canonical_observation_sha256": hashlib.sha256(core.canonical_json(observation).encode("utf-8")).hexdigest(),
            "legacy_id": observation["legacy_id"], "disposition": disposition, "rationale": rationale,
        }
        disposition_records.append(record)
        if disposition in {"implementation-variant", "overload-group", "queued-human-review"}:
            queue_records.append({
                "schema_version": "task024-review-queue-entry-v0", "variant_index": observation["variant_index"],
                "evidence_ref": record["evidence_ref"], "legacy_id": observation["legacy_id"],
                "primary_disposition": disposition, "complete_graph_reference_count": usage[observation["variant_index"]],
                "frequency_policy": "prioritization-only",
            })
    queue_records.sort(key=lambda item: (-item["complete_graph_reference_count"], item["variant_index"]))
    evidence_levels = [{"level": level, "status": "passed" if level <= 2 else "not-run"} for level in range(1, 9)]
    coverage = _record({
        "schema_version": "catalog-coverage-v0", "canonical_profile": "schuss-canonical-json-v1",
        "coverage_report_id": "schuss-coverage-report-000002", "revision": 1,
        "review_id": "task024-catalog-coverage-v1",
        "snapshot": {"schema_version": "legacy-resolved-catalog-v0", "manifest_sha256": FROZEN_MANIFEST_SHA256},
        "total_observations": len(observations), "disposition_policy": "task024-disposition-precedence-v1",
        "disposition_counts": {key: counts[key] for key in sorted(coverage_schema["properties"]["disposition_counts"]["properties"])},
        "reviewed_family_count": 60, "additional_family_count": len(FAMILIES), "review_queue_count": len(queue_records),
        "frequency_policy": "prioritization-only", "evidence_levels": evidence_levels,
    }, coverage_schema)
    disposition_bytes = b"".join(_canonical_bytes(item) for item in disposition_records)
    queue_bytes = b"".join(_canonical_bytes(item) for item in queue_records)
    coverage_bytes = _canonical_bytes(coverage)
    artifacts = [
        ("reports/coverage.json", coverage_bytes, 1),
        ("reports/dispositions.jsonl", disposition_bytes, len(disposition_records)),
        ("packets/review-queue.jsonl", queue_bytes, len(queue_records)),
    ]
    manifest = {
        "schema_version": "catalog-review-manifest-v0", "review_id": "task024-catalog-coverage-v1",
        "snapshot_manifest_sha256": FROZEN_MANIFEST_SHA256, "observation_count": len(observations),
        "artifacts": [{"portable_path": path, "byte_sha256": hashlib.sha256(payload).hexdigest(), "record_count": count} for path, payload, count in artifacts],
    }
    errors = core.schema_errors(manifest, review_manifest_schema, review_manifest_schema)
    if errors:
        raise ValueError("; ".join(errors))
    files = {path: payload for path, payload, _ in artifacts}
    files["manifest.json"] = _canonical_bytes(manifest)
    return files, coverage


def _catalog(
    parent_corpus: dict[str, Any],
    observations: list[dict[str, Any]],
    schema: dict[str, Any],
    source_corpus: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    corpus = copy.deepcopy(parent_corpus)
    corpus.update({
        "schema_version": "catalog-corpus-v3", "revision": 3, "projection_version": "schuss-catalog-projection-v3",
        "parent_corpus_reference": _ref(parent_corpus, "catalog_id"),
        "coverage_review": {"review_id": "task024-catalog-coverage-v1", "frozen_observation_count": 3602, "additional_family_count": 20, "frequency_policy": "prioritization-only", "disposition_policy": "task024-disposition-precedence-v1"},
    })
    candidate_by_base_ref = {
        item["base_ref"]: item
        for item in candidates
        if item["import_form"] == "axo-normal-definition"
    }
    observation_by_ref = {
        f"legacy-resolved-catalog-v0:object:{item['variant_index']}": item
        for item in observations
    }
    family_treatments: list[dict[str, Any]] = []
    additional_implementation_id = 81
    for offset, raw_spec in enumerate(FAMILIES):
        spec = _merged_family_spec(raw_spec)
        observation = observations[spec["variant"]]
        base_ref = f"{observation['origin']['source_id']}:{observation['legacy_id']}"
        candidate = candidate_by_base_ref.get(base_ref)
        if candidate is None:
            raise ValueError(f"reviewed family is absent from current Ksoloti primary corpus: {base_ref}")
        selected_uuid = observation["uuid"]["durable_value"]
        selected_variants = [item for item in candidate["variants"] if item["legacy_uuid"] == selected_uuid]
        if len(selected_variants) != 1:
            raise ValueError(f"reviewed family selected variant is ambiguous in current Ksoloti: {base_ref}")
        selected_variant = selected_variants[0]
        current_rationale = FAMILY_DECISIONS[spec["variant"]].get(
            "rationale",
            f"The pinned current Ksoloti base reference {base_ref} and its exact variant cohort establish the review subject; frozen graph frequency remains prioritization evidence only.",
        )
        source = {"kind": "legacy-observation", "observation": _source(observation)}
        family = _child({
            "family_id": f"schuss-family-{41 + offset:06d}", "revision": 1,
            "display_name": spec["name"], "aliases": spec["aliases"], "description": spec["description"],
            "primary_category": spec["category"], "secondary_function_tags": sorted(spec["tags"]),
            "abstraction_level": "primitive", "review_status": "task024-reviewed",
            "classification_confidence": "medium" if spec["treatment"] == "reconsider" else "high",
            "classification_rationale": current_rationale, "source_authority": source,
            "unresolved_questions": sorted(
                {
                    "Catalog review does not establish a component contract, binding, compiler support, target compatibility, device behavior, real-time behavior, or audible behavior.",
                    *(
                        ["Separate musician-facing family identity and default-drawer placement remain under serialized review."]
                        if spec["treatment"] == "reconsider"
                        else []
                    ),
                }
            ),
        })
        corpus["family_additions"].append(family)
        implementation_ids: list[str] = []
        ordered_variants = [selected_variant] + [
            item for item in candidate["variants"] if item is not selected_variant
        ]
        for variant_offset, variant in enumerate(ordered_variants):
            if variant_offset == 0:
                implementation_id = f"schuss-implementation-{61 + offset:06d}"
                variant_observation = observation
            else:
                implementation_id = f"schuss-implementation-{additional_implementation_id:06d}"
                additional_implementation_id += 1
                references = variant["frozen_lineage_refs"]
                if len(references) != 1:
                    raise ValueError(
                        f"reviewed current Ksoloti variant must have one exact frozen lineage reference: {variant['variant_ref']}"
                    )
                variant_observation = observation_by_ref[references[0]]
            variant_source = {"kind": "legacy-observation", "observation": _source(variant_observation)}
            implementation = _child({
                "implementation_id": implementation_id, "revision": 1,
                "family_reference": _ref(family, "family_id"),
                "display_name": spec["name"] + (
                    " implementation" if variant_offset == 0 else f" current variant {variant_offset + 1}"
                ),
                "form": "generated-object" if variant_observation["origin"].get("generated_by") else "native-object",
                "review_status": "task024-reviewed",
                "membership_confidence": "medium" if spec["treatment"] == "reconsider" else "high",
                "membership_rationale": current_rationale,
                "source_authority": variant_source, "compatibility_status": "not-evaluated",
                "unresolved_questions": sorted(
                    {
                        "No exact component contract, implementation seam map, backend eligibility, or execution evidence is established by Task 024.",
                        *(
                            ["Variant membership is retained under a family whose separate product identity remains under serialized review."]
                            if spec["treatment"] == "reconsider"
                            else []
                        ),
                    }
                ),
            })
            corpus["implementation_additions"].append(implementation)
            implementation_ids.append(implementation_id)
        treatment_rationale = current_rationale
        if spec["variant"] == 180:
            treatment_rationale = "Review this raw factory GPIO input with the accepted smoothed analog family and current Ksoloti raw, smoothed-unipolar, and smoothed-bipolar cohorts before fixing a separate default-drawer identity."
        elif spec["variant"] == 421:
            treatment_rationale = "Review this exact two-input cohort with the accepted four-input mixer before deciding whether mixer arity is a family or contract/form distinction."
        family_treatments.append(
            {
                "family_reference": _ref(family, "family_id"),
                "treatment": spec["treatment"],
                "drawer_visibility": spec["visibility"],
                "current_base_refs": [base_ref],
                "candidate_variant_count": len(candidate["variants"]),
                "catalogued_variant_count": len(implementation_ids),
                "implementation_ids": sorted(implementation_ids),
                "rationale": treatment_rationale,
            }
        )
    if additional_implementation_id != 90:
        raise ValueError(
            f"Task 024 current variant allocation changed: expected next implementation ID 90, got {additional_implementation_id}"
        )
    corpus["current_ksoloti_review"] = {
        "source_corpus_reference": _ref(source_corpus, "current_ksoloti_corpus_id"),
        "authority_policy": "current-ksoloti-base-ref-cohorts-first-object-level-semantic-review-required",
        "frozen_inventory_role": "immutable-provenance-lineage-and-gap-evidence-not-product-backlog",
        "family_treatments": sorted(family_treatments, key=lambda item: item["family_reference"]["family_id"]),
    }
    corpus["family_additions"].sort(key=lambda item: item["family_id"])
    corpus["implementation_additions"].sort(key=lambda item: item["implementation_id"])
    return _record(corpus, schema)


def _task025_packet(context: Any, catalog: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    graph = next(item for item in context.records["graphs"] if item["graph_id"] == "schuss-graph-000004" and item["revision"] == 1)
    contracts = {item["component_contract_id"]: item for item in context.records["contracts"]}
    node_ids: dict[str, list[str]] = defaultdict(list)
    for node in graph["nodes"]:
        node_ids[node["contract_reference"]["component_contract_id"]].append(node["node_id"])
    if set(node_ids) != set(TASK025_IMPLEMENTATIONS):
        raise ValueError("Task 025 selection no longer equals the eight distinct effects-graph contracts")
    roles = {
        "schuss-component-contract-000003": "crossfade and routing",
        "schuss-component-contract-000009": "audio output support",
        "schuss-component-contract-000012": "band-limited saw oscillator",
        "schuss-component-contract-000013": "band-limited PWM oscillator",
        "schuss-component-contract-000015": "exponential control smoothing",
        "schuss-component-contract-000016": "audio soft clipping",
        "schuss-component-contract-000017": "stereo reverb",
        "schuss-component-contract-000020": "interpolated audio VCA",
    }
    subjects = []
    for contract_id in sorted(node_ids):
        contract = contracts[contract_id]
        implementation_id = TASK025_IMPLEMENTATIONS[contract_id]
        bindings = [item for item in context.records["bindings"] if item["implementation_id"] == implementation_id and item["contract_reference"] == _ref(contract, "component_contract_id")]
        if not bindings:
            raise ValueError(f"Task 025 selected implementation has no exact binding: {implementation_id}")
        binding = max(bindings, key=lambda item: item["revision"])
        binding_reference = _ref(binding, "implementation_id")
        readiness = {"contracted", "bound"}
        eligibility = [
            item for item in context.records["eligibility"]
            if item["binding_reference"] == binding_reference
        ]
        if any(item["allowed_pair"]["state"]["status"] == "supported" for item in eligibility):
            readiness.add("eligible")
        else:
            readiness.add("unresolved")
        selected_results = [
            result for result in context.records["result"]
            if any(item["binding_reference"] == binding_reference for item in result.get("selected_bindings", ()))
        ]
        result_keys = {
            (item["build_result_id"], item["revision"], item["content_hash"])
            for item in selected_results
        }
        if any(
            evidence.get("level") == 5
            and evidence.get("outcome") == "passed"
            and (
                evidence.get("subject_reference", {}).get("stable_id"),
                evidence.get("subject_reference", {}).get("revision"),
                evidence.get("subject_reference", {}).get("content_hash"),
            ) in result_keys
            for evidence in context.records["evidence"]
        ):
            readiness.add("compile-proven")
        subjects.append({
            "node_ids": sorted(node_ids[contract_id]), "role": roles[contract_id],
            "family_reference": {"stable_id": contract["family_reference"]["family_id"], "revision": contract["family_reference"]["revision"], "content_hash": contract["family_reference"]["content_hash"]},
            "implementation_reference": _ref(binding, "implementation_id", generic=True),
            "contract_reference": _ref(contract, "component_contract_id", generic=True),
            "current_readiness": sorted(readiness),
        })
    return _record({
        "schema_version": "task025-selection-packet-v0", "canonical_profile": "schuss-canonical-json-v1",
        "selection_packet_id": "schuss-core-selection-000002", "revision": 1,
        "catalog_reference": _ref(catalog, "catalog_id", generic=True), "source_graph_reference": _ref(graph, "graph_id", generic=True),
        "selection_rule": "exact-distinct-contracts-in-schuss-graph-000004-r1", "subjects": subjects,
        "evidence_levels": [{"level": level, "status": "passed" if level <= 2 else "not-run"} for level in range(1, 9)],
        "prohibited_expansion": sorted(["ambient or latest record discovery", "compiler support inferred from catalog review", "families outside the exact source graph", "hardware real-time or audible evidence", "Java or legacy patch fallback"]),
    }, schema)


def generated() -> tuple[dict[str, bytes], bytes, dict[str, Any]]:
    if core.sha256_file(SNAPSHOT_ROOT / "manifest.json") != FROZEN_MANIFEST_SHA256:
        raise ValueError("frozen resolved-catalog manifest hash changed")
    observations = core.load_jsonl(OBJECTS)
    graphs = core.load_jsonl(GRAPHS)
    if len(observations) != 3602:
        raise ValueError("frozen observation count changed")
    parent = core.load_json(PARENT)
    context = load_repository_context(record_set_path=PARENT)
    parent_corpus = context.records["catalog"][0]
    if parent_corpus["schema_version"] != "catalog-corpus-v2" or parent_corpus["revision"] != 2:
        raise ValueError("Task 024 parent does not select the accepted catalog v2 corpus")

    schemas = _schema_files()
    for name, schema in schemas.items():
        annotations = core.validate_schema_annotations(schema)
        if annotations:
            raise ValueError(f"Task 024 schema annotations invalid for {name}: {annotations}")
    current_files, current_corpus, current_candidates = _current_ksoloti_outputs(
        observations,
        schemas["current-ksoloti-candidate-v0.schema.json"],
        schemas["current-ksoloti-corpus-v0.schema.json"],
    )
    review_files, coverage = _coverage_outputs(observations, graphs, parent_corpus, schemas["catalog-coverage-v0.schema.json"], schemas["catalog-review-manifest-v0.schema.json"])
    catalog = _catalog(
        parent_corpus,
        observations,
        schemas["catalog-corpus-v3.schema.json"],
        current_corpus,
        current_candidates,
    )
    selector = _record({
        "schema_version": "catalog-selection-v0", "canonical_profile": "schuss-canonical-json-v1",
        "catalog_selection_id": "schuss-catalog-selection-000001", "revision": 2,
        "corpus_reference": _ref(catalog, "catalog_id"),
        "rationale": "Select the exact Task 024 sixty-family catalog successor inside the exact Task 024 record set.",
    }, core.load_json(ROOT / "schemas/catalog-selection-v0.schema.json"))
    packet = _task025_packet(context, catalog, schemas["task025-selection-packet-v0.schema.json"])

    files: dict[str, bytes] = {f"schemas/{name}": _canonical_bytes(schema) for name, schema in schemas.items()}
    records = {
        "contracts/task024/catalog-corpus-v3.json": catalog,
        "contracts/task024/catalog-selection-r2.json": selector,
        "contracts/task024/coverage-report.json": coverage,
        "contracts/task024/current-ksoloti-corpus.json": current_corpus,
        "contracts/task024/task025-selection-packet.json": packet,
    }
    files.update({path: _canonical_bytes(record) for path, record in records.items()})
    files.update({f"catalog/reviews/task024-catalog-coverage-v1/{path}": payload for path, payload in review_files.items()})
    files.update(current_files)

    schema_members = copy.deepcopy(parent["schema_members"])
    existing_schemas = {item["schema_version"] for item in schema_members}
    for name in sorted(schemas):
        version = name.removesuffix(".schema.json")
        if version in existing_schemas:
            raise ValueError(f"Task 024 schema version collides with parent: {version}")
        path = f"schemas/{name}"
        schema_members.append({"schema_version": version, "portable_path": path, "byte_sha256": hashlib.sha256(files[path]).hexdigest()})

    record_members = copy.deepcopy(parent["record_members"])
    additions = (
        ("catalog-corpus", catalog, "catalog_id", "contracts/task024/catalog-corpus-v3.json"),
        ("catalog-selection", selector, "catalog_selection_id", "contracts/task024/catalog-selection-r2.json"),
        ("catalog-coverage", coverage, "coverage_report_id", "contracts/task024/coverage-report.json"),
        ("catalog-source-corpus", current_corpus, "current_ksoloti_corpus_id", "contracts/task024/current-ksoloti-corpus.json"),
        ("core-selection-packet", packet, "selection_packet_id", "contracts/task024/task025-selection-packet.json"),
    )
    for kind, record, field, path in additions:
        record_members.append({
            "record_kind": kind, "stable_id": record[field], "revision": record["revision"], "content_hash": record["content_hash"],
            "portable_path": path, "byte_sha256": hashlib.sha256(files[path]).hexdigest(),
        })
    manifest_schema = core.load_json(ROOT / record_set_rules.RECORD_SET_SCHEMA)
    manifest = {
        "schema_version": "record-set-v0", "canonical_profile": "schuss-canonical-json-v1",
        "record_set_id": "schuss-record-set-000016", "revision": 1, "content_hash": "sha256:" + "0" * 64,
        "purpose": "prospective-task", "parent_reference": {"status": "included", **{key: parent[key] for key in ("record_set_id", "revision", "content_hash")}},
        "schema_members": sorted(schema_members, key=lambda item: (item["byte_sha256"], item["portable_path"])),
        "record_members": sorted(record_members, key=lambda item: (item["byte_sha256"], item["portable_path"])),
        "enforced_directories": sorted(set(parent["enforced_directories"]) | {"contracts/task024"}),
    }
    errors = core.schema_errors(manifest, manifest_schema, manifest_schema)
    if errors:
        raise ValueError("; ".join(errors))
    manifest["content_hash"] = core.record_content_hash(manifest, manifest_schema)
    manifest_bytes = _canonical_bytes(manifest)
    summary = {
        "schema_version": "task024-generation-summary-v1", "status": "valid",
        "record_set_reference": {key: manifest[key] for key in ("record_set_id", "revision", "content_hash")},
        "frozen_observation_count": len(observations), "disposition_counts": coverage["disposition_counts"],
        "review_queue_count": coverage["review_queue_count"], "catalog_family_count": 60,
        "additional_family_count": len(FAMILIES),
        "current_ksoloti_candidate_count": current_corpus["primary_corpus"]["candidate_count"],
        "current_ksoloti_normal_definition_count": current_corpus["primary_corpus"]["normal_definition_count"],
        "current_ksoloti_compound_count": current_corpus["primary_corpus"]["axs_compound_count"],
        "complete_variant_implementation_count": sum(
            item["catalogued_variant_count"]
            for item in catalog["current_ksoloti_review"]["family_treatments"]
        ),
        "task025_subject_count": len(packet["subjects"]),
        "evidence_levels": coverage["evidence_levels"], "compiler_or_build_performed": False,
        "hardware_or_publication_performed": False,
    }
    files["evidence/task024-completion-v1/validation-summary.json"] = _canonical_bytes(summary)
    return files, manifest_bytes, summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        files, manifest, summary = generated()
        expected = {**files, OUTPUT.relative_to(ROOT).as_posix(): manifest}
        stale = [path for path, payload in expected.items() if not (ROOT / path).is_file() or (ROOT / path).read_bytes() != payload]
        if args.check and stale:
            raise ValueError("Task 024 generated outputs are stale: " + ", ".join(sorted(stale)))
        if not args.check:
            for relative, payload in expected.items():
                path = ROOT / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
    except (OSError, ValueError, KeyError, StopIteration) as exc:
        print("Task 024 generation failed: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
