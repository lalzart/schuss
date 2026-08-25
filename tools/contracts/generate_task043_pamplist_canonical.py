#!/usr/bin/env python3
"""Generate Task 043 Pamplist canonical identity and audition-library linkage."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "tools/contracts") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools/contracts"))

from tools.contracts import record_set_rules  # noqa: E402
from tools.contracts import validator_core as core  # noqa: E402


PARENT = ROOT / "contracts/record-sets/ui-desktop-instrument-library-v1.json"
OUTPUT = ROOT / "contracts/record-sets/task043-pamplist-canonical-v1.json"
TASK_DIR = "contracts/task043"
LIBRARY_V1 = ROOT / "research/prototype_support/instrument_library/audition-library-v1.json"
LIBRARY_V2 = ROOT / "research/prototype_support/instrument_library/audition-library-v2.json"
RECORD_SET_ID = "schuss-record-set-000036"

FAMILY_ID = "schuss-family-000109"
IMPLEMENTATION_ID = "schuss-implementation-000170"
GRAPH_ID = "schuss-graph-000009"
INSTRUMENT_ID = "schuss-instrument-000007"
COMPONENT_IDS = tuple(
    f"schuss-component-contract-{number:06d}" for number in range(42, 49)
)

SCHEMA_NAMES = (
    "catalog-corpus-v7",
    "catalog-projection-v7",
    "instrument-audition-library-v2",
)

PAMPLIST_AUTHORITIES = {
    "proposal": "research/proposals/pamplist-r06.md",
    "prototype_index": "research/prototypes/pamplist/prototype-index.json",
    "topology": "research/prototypes/pamplist/dsp-topology.json",
    "control_map": "research/prototypes/pamplist/contract-r06/control-map.json",
    "results": "research/prototypes/pamplist/contract-r06/RESULTS.md",
    "source_dependencies": "research/prototypes/pamplist/source-dependencies.json",
    "juce_build": "research/prototypes/pamplist/contract-r06/juce-build.json",
}

ROLE_SPECS = (
    ("timeline", "Seven-lane Rational Timeline"),
    ("decisions", "Seven-lane Euclidean Decision Bank"),
    ("modulation", "Lane-local Voice Modulation"),
    ("voices", "Independent Macro Voice Bank"),
    ("mixer", "Independent Voice Dry Mixer"),
    ("cohesion", "Six-mode Cohesion Body"),
    ("output", "Bounded Stereo Final Output"),
)


def _canonical_bytes(value: object) -> bytes:
    return (core.canonical_json(value) + "\n").encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_path(relative: str) -> str:
    return core.sha256_file(ROOT / relative)


def _closed(required: Iterable[str], properties: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "type": "object",
        "required": list(required),
        "properties": dict(properties),
        "additionalProperties": False,
    }


def _set(items: dict[str, Any], *, minimum: int = 0, maximum: int | None = None) -> dict[str, Any]:
    value: dict[str, Any] = {
        "type": "array",
        "x-schuss-array-kind": "set",
        "minItems": minimum,
        "uniqueItems": True,
        "items": items,
    }
    if maximum is not None:
        value["maxItems"] = maximum
    return value


def _child_hash(value: Mapping[str, Any]) -> str:
    payload = copy.deepcopy(dict(value))
    payload.pop("content_hash", None)
    return "sha256:" + hashlib.sha256(
        core.canonical_json(payload).encode("utf-8")
    ).hexdigest()


def _record(value: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(value)
    result["content_hash"] = "sha256:" + "0" * 64
    result["content_hash"] = core.record_content_hash(result, schema)
    errors = core.schema_errors(result, schema, schema)
    if errors:
        raise ValueError("; ".join(errors))
    return result


def _exact_ref(value: Mapping[str, Any], id_field: str) -> dict[str, Any]:
    return {
        id_field: value[id_field],
        "revision": value["revision"],
        "content_hash": value["content_hash"],
    }


def _file_authority_schema() -> dict[str, Any]:
    return _closed(
        ("path", "sha256"),
        {
            "path": {"$ref": "#/$defs/portablePath"},
            "sha256": {"$ref": "#/$defs/rawSha256"},
        },
    )


def _prototype_source_authority_schema() -> dict[str, Any]:
    return _closed(
        (
            "kind",
            "prototype_id",
            "revision",
            "authorities",
            "source_release_references",
            "acceptance_reference",
            "runtime_boundary",
        ),
        {
            "kind": {"const": "schuss-instrument-prototype"},
            "prototype_id": {"const": "pamplist"},
            "revision": {"const": "0.6"},
            "authorities": _closed(
                tuple(PAMPLIST_AUTHORITIES),
                {name: _file_authority_schema() for name in PAMPLIST_AUTHORITIES},
            ),
            "source_release_references": _set(
                {"$ref": "#/$defs/sourceReleaseReference"}, minimum=2, maximum=2
            ),
            "acceptance_reference": {
                "const": "current-thread-user-audition-accepted-2026-08-24"
            },
            "runtime_boundary": {
                "const": "instrument-lab-host-evidence-not-canonical-provider"
            },
        },
    )


def _catalog_schemas() -> tuple[dict[str, Any], dict[str, Any]]:
    corpus = copy.deepcopy(core.load_json(ROOT / "schemas/catalog-corpus-v6.schema.json"))
    corpus["$id"] = "catalog-corpus-v7.schema.json"
    corpus["title"] = "Schuss catalog corpus with canonical Pamplist identity v7"
    corpus["properties"]["schema_version"] = {"const": "catalog-corpus-v7"}
    corpus["properties"]["revision"] = {"const": 7}
    corpus["properties"]["projection_version"] = {
        "const": "schuss-catalog-projection-v7"
    }
    corpus["properties"]["family_additions"].update(
        {"minItems": 82, "maxItems": 82}
    )
    corpus["properties"]["implementation_additions"].update(
        {"minItems": 103, "maxItems": 103}
    )
    corpus["$defs"]["catalogReference"]["properties"]["revision"] = {
        "const": 6
    }
    corpus["$defs"]["familyAddition"]["properties"]["abstraction_level"][
        "enum"
    ] = ["primitive", "compound", "instrument"]
    corpus["$defs"]["familyAddition"]["properties"]["review_status"][
        "enum"
    ] = sorted(
        set(
            corpus["$defs"]["familyAddition"]["properties"]["review_status"][
                "enum"
            ]
        )
        | {"task043-reviewed"}
    )
    corpus["$defs"]["implementationAddition"]["properties"]["review_status"][
        "enum"
    ] = sorted(
        set(
            corpus["$defs"]["implementationAddition"]["properties"][
                "review_status"
            ]["enum"]
        )
        | {"task043-reviewed"}
    )
    corpus["$defs"]["sourceAuthority"]["oneOf"].append(
        _prototype_source_authority_schema()
    )

    projection = copy.deepcopy(
        core.load_json(ROOT / "schemas/catalog-projection-v6.schema.json")
    )
    projection["$id"] = "catalog-projection-v7.schema.json"
    projection["title"] = "Schuss catalog projection with Pamplist identity v7"
    projection["properties"]["schema_version"] = {
        "const": "catalog-projection-v7"
    }
    projection["properties"]["projection_version"] = {
        "const": "schuss-catalog-projection-v7"
    }
    projection["properties"]["families"].update(
        {"minItems": 108, "maxItems": 108}
    )
    projection["$defs"]["catalogReference"]["properties"]["revision"] = {
        "const": 7
    }
    return corpus, projection


def _library_schema() -> dict[str, Any]:
    schema = copy.deepcopy(
        core.load_json(ROOT / "schemas/instrument-audition-library-v1.schema.json")
    )
    schema["$id"] = "instrument-audition-library-v2.schema.json"
    schema["title"] = "Schuss mixed canonical and prototype audition library v2"
    schema["properties"]["schema_version"] = {
        "const": "instrument-audition-library-v2"
    }
    schema["properties"]["revision"] = {"const": 2}
    schema["properties"]["claims"] = _closed(
        ("canonical_identity_count", "production_ready", "runtime_authority"),
        {
            "canonical_identity_count": {"const": 1},
            "production_ready": {"const": False},
            "runtime_authority": {"const": "prototype-build-only"},
        },
    )
    entries = schema["properties"]["entries"]
    entries.update({"minItems": 6, "maxItems": 6})
    entry = entries["items"]
    canonical = {
        "oneOf": [
            _closed(("status",), {"status": {"const": "not-promoted"}}),
            _closed(
                (
                    "status",
                    "instrument_reference",
                    "graph_reference",
                    "record_set_reference",
                ),
                {
                    "status": {"const": "canonical"},
                    "instrument_reference": _closed(
                        ("instrument_id", "revision", "content_hash"),
                        {
                            "instrument_id": {
                                "pattern": "^schuss-instrument-[0-9]{6}$",
                                "type": "string",
                            },
                            "revision": {"type": "integer", "minimum": 1},
                            "content_hash": {
                                "pattern": "^sha256:[0-9a-f]{64}$",
                                "type": "string",
                            },
                        },
                    ),
                    "graph_reference": _closed(
                        ("graph_id", "revision", "content_hash"),
                        {
                            "graph_id": {
                                "pattern": "^schuss-graph-[0-9]{6}$",
                                "type": "string",
                            },
                            "revision": {"type": "integer", "minimum": 1},
                            "content_hash": {
                                "pattern": "^sha256:[0-9a-f]{64}$",
                                "type": "string",
                            },
                        },
                    ),
                    "record_set_reference": _closed(
                        ("record_set_id", "revision", "content_hash"),
                        {
                            "record_set_id": {
                                "pattern": "^schuss-record-set-[0-9]{6}$",
                                "type": "string",
                            },
                            "revision": {"type": "integer", "minimum": 1},
                            "content_hash": {
                                "pattern": "^sha256:[0-9a-f]{64}$",
                                "type": "string",
                            },
                        },
                    ),
                },
            ),
        ]
    }
    entry["properties"]["canonical_identity"] = canonical
    entry["required"].append("canonical_identity")
    return schema


def _authority() -> dict[str, Any]:
    parent = record_set_rules.load_record_set(ROOT, PARENT)
    releases = {
        value["source_release_id"]: value
        for value in parent.records["source-release"]
    }
    return {
        "kind": "schuss-instrument-prototype",
        "prototype_id": "pamplist",
        "revision": "0.6",
        "authorities": {
            name: {"path": path, "sha256": _sha256_path(path)}
            for name, path in PAMPLIST_AUTHORITIES.items()
        },
        "source_release_references": [
            _exact_ref(releases[identifier], "source_release_id")
            for identifier in (
                "schuss-source-release-000008",
                "schuss-source-release-000009",
            )
        ],
        "acceptance_reference": "current-thread-user-audition-accepted-2026-08-24",
        "runtime_boundary": "instrument-lab-host-evidence-not-canonical-provider",
    }


def _catalog_records(
    schema: dict[str, Any],
    selector_schema: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    parent = record_set_rules.load_record_set(ROOT, PARENT)
    source = next(
        value
        for value in parent.records["catalog-corpus"]
        if value["catalog_id"] == "schuss-catalog-000001"
        and value["revision"] == 6
    )
    authority = _authority()
    family = {
        "family_id": FAMILY_ID,
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "display_name": "Pamplist",
        "aliases": ["Pamplist 0.6"],
        "description": (
            "Seven independent Euclidean macro-voice lanes feeding one exact-dry "
            "shared modal cohesion body and bounded stereo output."
        ),
        "primary_category": "timing-sequencing",
        "secondary_function_tags": [
            "algorithmic-sequencing",
            "macro-voice",
            "percussion",
            "performance-instrument",
            "resonant-body",
        ],
        "abstraction_level": "instrument",
        "review_status": "task043-reviewed",
        "classification_confidence": "high",
        "classification_rationale": (
            "The accepted Pamplist topology owns a complete seven-lane sequencer, "
            "voice bank, mix, cohesion body, output, and public performance identity."
        ),
        "unresolved_questions": [
            "Canonical provider/runtime, embedded target, distribution, and structured real-time evidence remain open."
        ],
        "source_authority": copy.deepcopy(authority),
    }
    family["content_hash"] = _child_hash(family)
    implementation = {
        "implementation_id": IMPLEMENTATION_ID,
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "family_reference": _exact_ref(family, "family_id"),
        "display_name": "Pamplist 0.6 transparent fused Core",
        "form": "transparent-compound",
        "review_status": "task043-reviewed",
        "membership_confidence": "high",
        "membership_rationale": (
            "The retained Core fuses exactly the seven separately inspectable graph "
            "roles while preserving their declared state and signal boundaries."
        ),
        "compatibility_status": "not-evaluated",
        "source_authority": copy.deepcopy(authority),
        "unresolved_questions": [
            "This catalog implementation has no canonical binding or provider; its executable evidence remains Instrument Lab authority."
        ],
    }
    implementation["content_hash"] = _child_hash(implementation)

    corpus = copy.deepcopy(source)
    corpus["schema_version"] = "catalog-corpus-v7"
    corpus["revision"] = 7
    corpus["projection_version"] = "schuss-catalog-projection-v7"
    corpus["parent_corpus_reference"] = _exact_ref(source, "catalog_id")
    corpus["family_additions"].append(family)
    corpus["family_additions"] = sorted(
        corpus["family_additions"], key=lambda item: item["family_id"]
    )
    corpus["implementation_additions"].append(implementation)
    corpus["implementation_additions"] = sorted(
        corpus["implementation_additions"], key=lambda item: item["implementation_id"]
    )
    corpus = _record(corpus, schema)

    selection_source = next(
        value
        for value in parent.records["catalog-selection"]
        if value["catalog_selection_id"] == "schuss-catalog-selection-000001"
        and value["revision"] == 5
    )
    selection = copy.deepcopy(selection_source)
    selection["revision"] = 6
    selection["corpus_reference"] = _exact_ref(corpus, "catalog_id")
    selection["rationale"] = (
        "Select the Task 043 corpus that preserves Task 033 Phase 2 and adds only "
        "the accepted canonical Pamplist 0.6 instrument family."
    )
    selection = _record(selection, selector_schema)
    return corpus, selection, family


def _q27() -> dict[str, Any]:
    return {
        "kind": "fixed-point",
        "signed": True,
        "width_bits": 32,
        "fractional_bits": 27,
        "encoding": "twos-complement-binary",
    }


def _boolean() -> dict[str, Any]:
    return {
        "kind": "boolean",
        "width_bits": 32,
        "encoding": "zero-false-nonzero-true",
    }


def _known_range(minimum: str, maximum: str, *, unit: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": "known",
        "minimum": minimum,
        "maximum": maximum,
        "minimum_inclusive": True,
        "maximum_inclusive": True,
        "overflow_policy": "clamp",
    }
    if unit is not None:
        result["unit"] = unit
    return result


def _port(
    facet: int,
    semantic_key: str,
    label: str,
    direction: str,
    *,
    channels: int,
    rate: str,
    semantic_role: str,
    representation: dict[str, Any] | None = None,
    unit: str = "normalized",
    minimum: str = "-1",
    maximum: str = "1",
) -> dict[str, Any]:
    outlet = direction == "outlet"
    return {
        "facet_id": f"component-port-{facet:06d}",
        "semantic_key": semantic_key,
        "display_label": label,
        "direction": direction,
        "port_type": {
            "domain": "stream" if rate != "event" else "event",
            "rate": rate,
            "channel_shape": {"kind": "fixed", "count": channels},
            "cardinality": {
                "minimum_connections": 0 if outlet else 1,
                "maximum_connections": "unbounded" if outlet else 1,
            },
            "semantic_role": semantic_role,
            "representation": copy.deepcopy(representation or _q27()),
            "unit": unit,
            "valid_range": _known_range(minimum, maximum),
            "optionality": (
                {"status": "not-applicable"}
                if outlet
                else {"status": "required", "absence_behavior": "invalid"}
            ),
            "ownership": {
                "status": "defined",
                "owner": "scheduler",
                "borrowing": "borrowed",
                "mutability": "immutable-to-consumer",
                "aliasing": "read-only-aliases-allowed",
                "lifetime": "audio-block" if rate == "audio" else "control-cycle",
                "capacity": "rate-defined" if rate == "audio" else "single-value",
                "synchronization": "single-scheduler",
            },
        },
    }


def _parameter(
    facet: int,
    semantic_key: str,
    label: str,
    default: str,
    *,
    minimum: str = "0",
    maximum: str = "1",
    unit: str = "normalized",
    representation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "facet_id": f"component-parameter-{facet:06d}",
        "semantic_key": semantic_key,
        "display_label": label,
        "representation": copy.deepcopy(representation or _q27()),
        "unit": unit,
        "domain": _known_range(minimum, maximum),
        "default": default,
        "update_behavior": {"update_kind": "runtime", "stateful": True},
    }


def _component(
    component_id: str,
    display_name: str,
    family: Mapping[str, Any],
    schema: dict[str, Any],
    *,
    ports: list[dict[str, Any]],
    parameters: list[dict[str, Any]],
    actions: list[dict[str, Any]] | None = None,
    displays: list[dict[str, Any]] | None = None,
    state_key: str | None = None,
    reset_policy: str = "default-on-start",
) -> dict[str, Any]:
    states = []
    if state_key is not None:
        states.append(
            {
                "state_id": "component-state-000001",
                "semantic_key": state_key,
                "value_kind": "structured",
                "ownership": "component-instance",
                "persistence": "volatile",
                "reset_policy": reset_policy,
            }
        )
    value = {
        "schema_version": "component-contract-v1",
        "canonical_profile": "schuss-canonical-json-v1",
        "component_contract_id": component_id,
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "family_reference": _exact_ref(family, "family_id"),
        "display_name": display_name,
        "ports": ports,
        "parameters": parameters,
        "attributes": [],
        "actions": actions or [],
        "displays": displays or [],
        "state_declarations": states,
        "lifecycle": (
            {
                "state_model": "declared-state",
                "initialization": "initialize-declared-state",
                "reset_behavior": "declared-per-state",
                "disposal": "none",
            }
            if states
            else {
                "state_model": "stateless",
                "initialization": "none",
                "reset_behavior": "not-applicable",
                "disposal": "none",
            }
        ),
        "binding_capabilities": {"parameter_input_ports": [], "action_inputs": []},
        "capability_requirements": [],
        "compound_interface": {"kind": "primitive", "mapping_keys": []},
        "compatibility_claims": [],
        "behavior_rules": [],
    }
    return _record(value, schema)


def _parameter_specs() -> dict[str, list[dict[str, str]]]:
    values: dict[str, list[dict[str, str]]] = {role: [] for role, _ in ROLE_SPECS}

    def add(
        role: str,
        key: str,
        label: str,
        default: str,
        minimum: str = "0",
        maximum: str = "1",
        domain_unit: str = "normalized",
    ) -> None:
        values[role].append(
            {
                "key": key,
                "label": label,
                "default": default,
                "minimum": minimum,
                "maximum": maximum,
                "domain_unit": domain_unit,
            }
        )

    add("timeline", "tempo", "Tempo", "0.3333333333333333")
    for lane in range(1, 8):
        add("timeline", f"lane-{lane}-rate", f"Lane {lane} Rate", "0.5333333333333333")
        add("timeline", f"lane-{lane}-phase", f"Lane {lane} Phase", "0")

    for lane in range(1, 8):
        add("decisions", f"lane-{lane}-shape", f"Lane {lane} Shape", "0.1428571428571429")
        add("decisions", f"lane-{lane}-hits", f"Lane {lane} Hits", "0.25")
        add("decisions", f"lane-{lane}-rotation", f"Lane {lane} Rotate", "0")
        add("decisions", f"lane-{lane}-chance", f"Lane {lane} Chance", "1")
        add("decisions", f"lane-{lane}-repeat", f"Lane {lane} Repeat", "0")
        add("decisions", f"lane-{lane}-depth", f"Lane {lane} Depth", "0")

    motion_names = (
        ("trigger", "Trigger", "0", "0", "1", "boolean"),
        ("pitch", "Pitch", "0", "-1", "1", "normalized"),
        ("model", "Model Sweep", "0", "-1", "1", "normalized"),
        ("harmonics", "Harmonics", "0", "-1", "1", "normalized"),
        ("timbre", "Timbre", "0", "-1", "1", "normalized"),
        ("morph", "Morph", "0", "-1", "1", "normalized"),
        ("decay", "Decay", "0", "-1", "1", "normalized"),
        ("level", "Level", "0", "-1", "1", "normalized"),
    )
    for lane in range(1, 8):
        for key, label, default, minimum, maximum, domain_unit in motion_names:
            add(
                "modulation",
                f"lane-{lane}-motion-{key}",
                f"Lane {lane} Motion {label}",
                default,
                minimum,
                maximum,
                domain_unit,
            )

    voice_names = (
        ("model", "Model", "0"),
        ("pitch", "Pitch", "0.3779527559055118"),
        ("harmonics", "Harmonics", "0.5"),
        ("timbre", "Timbre", "0.5"),
        ("morph", "Morph", "0.5"),
        ("decay", "Decay", "0.5"),
        ("colour", "Colour", "0.5"),
        ("level", "Level", "0.8"),
    )
    for lane in range(1, 8):
        for key, label, default in voice_names:
            add("voices", f"lane-{lane}-voice-{key}", f"Lane {lane} Voice {label}", default)

    for key, label, default in (
        ("drive", "Drive", "0"),
        ("cohere", "Cohere", "0"),
        ("root", "Root", "0.3779527559055118"),
        ("spread", "Spread", "0"),
        ("tail", "Tail", "0.5"),
        ("damping", "Damping", "0.5"),
        ("width", "Width", "0.5"),
        ("duck", "Duck", "0"),
    ):
        add("cohesion", f"global-{key}", f"Global {label}", default)
    add("output", "global-master", "Global Master", "0.65")
    return values


def _components(
    schema: dict[str, Any], family: Mapping[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, str]]]]:
    specs = _parameter_specs()
    params = {
        role: [
            _parameter(
                index,
                item["key"],
                item["label"],
                item["default"],
                minimum=item["minimum"],
                maximum=item["maximum"],
                representation=(
                    _boolean() if item["domain_unit"] == "boolean" else _q27()
                ),
                unit=("boolean" if item["domain_unit"] == "boolean" else "normalized"),
            )
            for index, item in enumerate(items, start=1)
        ]
        for role, items in specs.items()
    }
    components = [
        _component(
            COMPONENT_IDS[0],
            ROLE_SPECS[0][1],
            family,
            schema,
            ports=[
                _port(1, "lane-phases", "Lane Phases", "outlet", channels=7, rate="control", semantic_role="clock", minimum="0", maximum="1")
            ],
            parameters=params["timeline"],
            actions=[
                {
                    "facet_id": "component-action-000001",
                    "semantic_key": "run-stop",
                    "display_label": "Run or Stop",
                    "payload_kind": "none",
                }
            ],
            displays=[
                {
                    "facet_id": "component-display-000001",
                    "semantic_key": "timeline-state",
                    "display_label": "Timeline State",
                    "value_kind": "text",
                    "access": "read-only",
                }
            ],
            state_key="rational-timeline-state",
        ),
        _component(
            COMPONENT_IDS[1],
            ROLE_SPECS[1][1],
            family,
            schema,
            ports=[
                _port(1, "lane-phases", "Lane Phases", "inlet", channels=7, rate="control", semantic_role="clock", minimum="0", maximum="1"),
                _port(2, "lane-values", "Lane Values", "outlet", channels=7, rate="control", semantic_role="modulation", minimum="0", maximum="1"),
                _port(3, "lane-triggers", "Lane Triggers", "outlet", channels=7, rate="event", semantic_role="trigger", representation=_boolean(), unit="boolean", minimum="0", maximum="1"),
            ],
            parameters=params["decisions"],
            state_key="lane-decision-state",
        ),
        _component(
            COMPONENT_IDS[2],
            ROLE_SPECS[2][1],
            family,
            schema,
            ports=[
                _port(1, "lane-values", "Lane Values", "inlet", channels=7, rate="control", semantic_role="modulation", minimum="0", maximum="1"),
                _port(2, "lane-triggers", "Lane Triggers", "inlet", channels=7, rate="event", semantic_role="trigger", representation=_boolean(), unit="boolean", minimum="0", maximum="1"),
                _port(3, "resolved-controls", "Resolved Voice Controls", "outlet", channels=56, rate="control", semantic_role="modulation", minimum="-1", maximum="1"),
                _port(4, "resolved-triggers", "Resolved Triggers", "outlet", channels=7, rate="event", semantic_role="trigger", representation=_boolean(), unit="boolean", minimum="0", maximum="1"),
            ],
            parameters=params["modulation"],
        ),
        _component(
            COMPONENT_IDS[3],
            ROLE_SPECS[3][1],
            family,
            schema,
            ports=[
                _port(1, "resolved-controls", "Resolved Voice Controls", "inlet", channels=56, rate="control", semantic_role="modulation", minimum="-1", maximum="1"),
                _port(2, "resolved-triggers", "Resolved Triggers", "inlet", channels=7, rate="event", semantic_role="trigger", representation=_boolean(), unit="boolean", minimum="0", maximum="1"),
                _port(3, "voice-main", "Voice Main Outputs", "outlet", channels=7, rate="audio", semantic_role="audio"),
                _port(4, "voice-auxiliary", "Voice Auxiliary Outputs", "outlet", channels=7, rate="audio", semantic_role="audio"),
            ],
            parameters=params["voices"],
            displays=[
                {
                    "facet_id": "component-display-000001",
                    "semantic_key": "voice-state",
                    "display_label": "Accepted Voice State",
                    "value_kind": "text",
                    "access": "read-only",
                }
            ],
            state_key="seven-independent-voice-states",
        ),
        _component(
            COMPONENT_IDS[4],
            ROLE_SPECS[4][1],
            family,
            schema,
            ports=[
                _port(1, "voice-main", "Voice Main Inputs", "inlet", channels=7, rate="audio", semantic_role="audio"),
                _port(2, "voice-auxiliary", "Voice Auxiliary Inputs", "inlet", channels=7, rate="audio", semantic_role="audio"),
                _port(3, "resolved-controls", "Resolved Voice Controls", "inlet", channels=56, rate="control", semantic_role="modulation", minimum="-1", maximum="1"),
                _port(4, "dry-left", "Dry Left", "outlet", channels=1, rate="audio", semantic_role="audio"),
                _port(5, "dry-right", "Dry Right", "outlet", channels=1, rate="audio", semantic_role="audio"),
            ],
            parameters=[],
        ),
        _component(
            COMPONENT_IDS[5],
            ROLE_SPECS[5][1],
            family,
            schema,
            ports=[
                _port(1, "dry-left", "Dry Left", "inlet", channels=1, rate="audio", semantic_role="audio"),
                _port(2, "dry-right", "Dry Right", "inlet", channels=1, rate="audio", semantic_role="audio"),
                _port(3, "cohesion-left", "Cohesion Left", "outlet", channels=1, rate="audio", semantic_role="audio"),
                _port(4, "cohesion-right", "Cohesion Right", "outlet", channels=1, rate="audio", semantic_role="audio"),
            ],
            parameters=params["cohesion"],
            actions=[
                {
                    "facet_id": "component-action-000001",
                    "semantic_key": "clear-cohesion",
                    "display_label": "Clear Cohesion",
                    "payload_kind": "none",
                }
            ],
            displays=[
                {
                    "facet_id": "component-display-000001",
                    "semantic_key": "cohesion-state",
                    "display_label": "Accepted Cohesion State",
                    "value_kind": "text",
                    "access": "read-only",
                }
            ],
            state_key="six-mode-cohesion-state",
            reset_policy="explicit-action",
        ),
        _component(
            COMPONENT_IDS[6],
            ROLE_SPECS[6][1],
            family,
            schema,
            ports=[
                _port(1, "cohesion-left", "Cohesion Left", "inlet", channels=1, rate="audio", semantic_role="audio"),
                _port(2, "cohesion-right", "Cohesion Right", "inlet", channels=1, rate="audio", semantic_role="audio"),
                _port(3, "audio-left", "Audio Left", "outlet", channels=1, rate="audio", semantic_role="audio"),
                _port(4, "audio-right", "Audio Right", "outlet", channels=1, rate="audio", semantic_role="audio"),
            ],
            parameters=params["output"],
            displays=[
                {
                    "facet_id": "component-display-000001",
                    "semantic_key": "processing-diagnostics",
                    "display_label": "Processing Diagnostics",
                    "value_kind": "text",
                    "access": "read-only",
                }
            ],
        ),
    ]
    return components, specs


def _graph_domain(item: Mapping[str, str]) -> dict[str, Any]:
    unit = "boolean" if item["domain_unit"] == "boolean" else "normalized"
    return _known_range(item["minimum"], item["maximum"], unit=unit)


def _linear_transform(item: Mapping[str, str]) -> dict[str, Any]:
    return {
        "curve": "linear",
        "polarity": "direct",
        "points": [
            {"source": item["minimum"], "destination": item["minimum"]},
            {"source": item["maximum"], "destination": item["maximum"]},
        ],
    }


def _graph(
    schema: dict[str, Any],
    components: list[dict[str, Any]],
    specs: dict[str, list[dict[str, str]]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    role_nodes = {
        role: f"graph-node-{index:06d}"
        for index, (role, _label) in enumerate(ROLE_SPECS, start=1)
    }
    nodes = [
        {
            "node_id": role_nodes[role],
            "contract_reference": _exact_ref(component, "component_contract_id"),
            "parameter_values": [],
            "attribute_values": [],
        }
        for (role, _label), component in zip(ROLE_SPECS, components, strict=True)
    ]
    endpoints = {
        "timeline": role_nodes["timeline"],
        "decisions": role_nodes["decisions"],
        "modulation": role_nodes["modulation"],
        "voices": role_nodes["voices"],
        "mixer": role_nodes["mixer"],
        "cohesion": role_nodes["cohesion"],
        "output": role_nodes["output"],
    }
    connection_pairs = (
        ("timeline", 1, "decisions", 1),
        ("decisions", 2, "modulation", 1),
        ("decisions", 3, "modulation", 2),
        ("modulation", 3, "voices", 1),
        ("modulation", 4, "voices", 2),
        ("voices", 3, "mixer", 1),
        ("voices", 4, "mixer", 2),
        ("modulation", 3, "mixer", 3),
        ("mixer", 4, "cohesion", 1),
        ("mixer", 5, "cohesion", 2),
        ("cohesion", 3, "output", 1),
        ("cohesion", 4, "output", 2),
    )
    connections = [
        {
            "connection_id": f"graph-connection-{index:06d}",
            "source": {
                "node_id": endpoints[source_role],
                "facet_id": f"component-port-{source_port:06d}",
            },
            "destination": {
                "node_id": endpoints[destination_role],
                "facet_id": f"component-port-{destination_port:06d}",
            },
        }
        for index, (source_role, source_port, destination_role, destination_port) in enumerate(
            connection_pairs, start=1
        )
    ]

    public_parameters: list[dict[str, Any]] = []
    bindings: list[dict[str, Any]] = []
    ordered_specs: list[dict[str, Any]] = []
    for role, _label in ROLE_SPECS:
        for component_index, item in enumerate(specs[role], start=1):
            public_index = len(public_parameters) + 1
            graph_facet = f"graph-facet-{public_index:06d}"
            public_parameters.append(
                {
                    "facet_id": graph_facet,
                    "semantic_key": item["key"],
                    "display_label": item["label"],
                    "value_type": "exact-decimal",
                    "domain": _graph_domain(item),
                    "default": item["default"],
                    "update_behavior": {"update_kind": "runtime", "stateful": True},
                }
            )
            bindings.append(
                {
                    "binding_id": f"graph-binding-{public_index:06d}",
                    "binding_kind": "parameter-to-parameter",
                    "source_graph_parameter_id": graph_facet,
                    "destination": {
                        "node_id": role_nodes[role],
                        "facet_kind": "parameter",
                        "facet_id": f"component-parameter-{component_index:06d}",
                    },
                    "source_domain": _graph_domain(item),
                    "destination_domain": _graph_domain(item),
                    "transform": _linear_transform(item),
                    "update_boundary": "control-cycle",
                    "smoothing": {
                        "kind": "linear",
                        "responsibility": "graph",
                        "completion": "next-control-cycle",
                    },
                    "driver_policy": "exclusive",
                }
            )
            ordered_specs.append({"graph_facet_id": graph_facet, **item})

    next_facet = len(public_parameters) + 1
    public_actions = [
        {
            "facet_id": f"graph-facet-{next_facet:06d}",
            "semantic_key": "run-stop",
            "display_label": "Run or Stop",
            "payload_kind": "none",
        },
        {
            "facet_id": f"graph-facet-{next_facet + 1:06d}",
            "semantic_key": "clear-cohesion",
            "display_label": "Clear Cohesion",
            "payload_kind": "none",
        },
    ]
    display_specs = (
        ("timeline", "timeline-state", "Timeline State"),
        ("voices", "voice-state", "Accepted Voice State"),
        ("cohesion", "cohesion-state", "Accepted Cohesion State"),
        ("output", "processing-diagnostics", "Processing Diagnostics"),
    )
    public_displays = [
        {
            "facet_id": f"graph-facet-{next_facet + 2 + index:06d}",
            "semantic_key": key,
            "display_label": label,
            "value_kind": "text",
            "access": "read-only",
        }
        for index, (_role, key, label) in enumerate(display_specs)
    ]
    action_exposures = [
        {
            "exposure_id": "graph-exposure-000003",
            "graph_facet_kind": "action",
            "graph_facet_id": public_actions[0]["facet_id"],
            "target": {
                "node_id": role_nodes["timeline"],
                "facet_kind": "action",
                "facet_id": "component-action-000001",
            },
        },
        {
            "exposure_id": "graph-exposure-000004",
            "graph_facet_kind": "action",
            "graph_facet_id": public_actions[1]["facet_id"],
            "target": {
                "node_id": role_nodes["cohesion"],
                "facet_kind": "action",
                "facet_id": "component-action-000001",
            },
        },
    ]
    display_exposures = [
        {
            "exposure_id": f"graph-exposure-{5 + index:06d}",
            "graph_facet_kind": "display",
            "graph_facet_id": public_displays[index]["facet_id"],
            "target": {
                "node_id": role_nodes[role],
                "facet_kind": "display",
                "facet_id": "component-display-000001",
            },
        }
        for index, (role, _key, _label) in enumerate(display_specs)
    ]
    graph = {
        "schema_version": "dsp-graph-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "graph_id": GRAPH_ID,
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "display_name": "Pamplist 0.6 complete seven-role graph",
        "public_ports": [
            {
                "facet_id": f"graph-facet-{next_facet + 6:06d}",
                "semantic_key": "audio-left",
                "display_label": "Audio Left",
                "direction": "output",
            },
            {
                "facet_id": f"graph-facet-{next_facet + 7:06d}",
                "semantic_key": "audio-right",
                "display_label": "Audio Right",
                "direction": "output",
            },
        ],
        "public_parameters": public_parameters,
        "public_actions": public_actions,
        "public_displays": public_displays,
        "nodes": nodes,
        "connections": connections,
        "public_port_exposures": [
            {
                "exposure_id": "graph-exposure-000001",
                "graph_facet_id": f"graph-facet-{next_facet + 6:06d}",
                "node_port": {
                    "node_id": role_nodes["output"],
                    "facet_id": "component-port-000003",
                },
            },
            {
                "exposure_id": "graph-exposure-000002",
                "graph_facet_id": f"graph-facet-{next_facet + 7:06d}",
                "node_port": {
                    "node_id": role_nodes["output"],
                    "facet_id": "component-port-000004",
                },
            },
        ],
        "public_facet_exposures": action_exposures + display_exposures,
        "parameter_bindings": bindings,
        "compound_interface_mappings": [],
        "hierarchy_edges": [],
    }
    return _record(graph, schema), ordered_specs


def _instrument(
    schema: dict[str, Any],
    graph: Mapping[str, Any],
    ordered_specs: list[dict[str, Any]],
) -> dict[str, Any]:
    parameters = []
    mappings = []
    for index, item in enumerate(ordered_specs, start=1):
        facet = f"instrument-parameter-{index:06d}"
        domain = {
            "minimum": item["minimum"],
            "maximum": item["maximum"],
            "unit": "boolean" if item["domain_unit"] == "boolean" else "normalized",
        }
        parameters.append(
            {
                "facet_id": facet,
                "display_label": item["label"],
                "value_type": "exact-decimal",
                "domain": copy.deepcopy(domain),
                "default": item["default"],
                "update_behavior": {
                    "update_kind": "runtime",
                    "smoothing_responsibility": "graph",
                    "stateful": True,
                },
            }
        )
        mappings.append(
            {
                "mapping_id": f"graph-mapping-{index:06d}",
                "mapping_kind": "parameter-to-parameter",
                "direction": "instrument-to-graph",
                "source": {"facet_kind": "parameter", "facet_id": facet},
                "destination": {
                    "facet_kind": "parameter",
                    "facet_id": item["graph_facet_id"],
                },
                "source_domain": copy.deepcopy(domain),
                "destination_domain": copy.deepcopy(domain),
                "transform": _linear_transform(item),
            }
        )
    graph_actions = graph["public_actions"]
    actions = [
        {
            "facet_id": "instrument-action-000001",
            "display_label": "Run or Stop",
            "payload_kind": "none",
        },
        {
            "facet_id": "instrument-action-000002",
            "display_label": "Clear Cohesion",
            "payload_kind": "none",
        },
    ]
    for offset, (action, graph_action) in enumerate(
        zip(actions, graph_actions, strict=True), start=len(parameters) + 1
    ):
        mappings.append(
            {
                "mapping_id": f"graph-mapping-{offset:06d}",
                "mapping_kind": "action-to-action",
                "direction": "instrument-to-graph",
                "source": {
                    "facet_kind": "action",
                    "facet_id": action["facet_id"],
                },
                "destination": {
                    "facet_kind": "action",
                    "facet_id": graph_action["facet_id"],
                },
            }
        )
    displays = [
        {
            "facet_id": f"instrument-display-{index:06d}",
            "display_label": graph_display["display_label"],
            "value_kind": "text",
            "access": "read-only",
        }
        for index, graph_display in enumerate(graph["public_displays"], start=1)
    ]
    value = {
        "schema_version": "instrument-v1",
        "canonical_profile": "schuss-canonical-json-v1",
        "instrument_id": INSTRUMENT_ID,
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "display_name": "Pamplist",
        "lineage": {"status": "new"},
        "graph_reference": {"status": "resolved", **_exact_ref(graph, "graph_id")},
        "parameters": parameters,
        "actions": actions,
        "displays": displays,
        "state_declarations": [
            {
                "state_id": "instrument-state-000001",
                "display_label": "Seven Lane Programs",
                "value_kind": "text",
                "persistence": "persistent",
                "reset_policy": "default-on-start",
            },
            {
                "state_id": "instrument-state-000002",
                "display_label": "Independent Voice States",
                "value_kind": "text",
                "persistence": "volatile",
                "reset_policy": "default-on-start",
            },
            {
                "state_id": "instrument-state-000003",
                "display_label": "Cohesion History",
                "value_kind": "text",
                "persistence": "volatile",
                "reset_policy": "explicit-action",
            },
            {
                "state_id": "instrument-state-000004",
                "display_label": "Accepted Impact History",
                "value_kind": "text",
                "persistence": "volatile",
                "reset_policy": "default-on-start",
            },
        ],
        "event_inputs": [],
        "graph_mappings": mappings,
    }
    return _record(value, schema)


def _library(
    schema: dict[str, Any],
    graph: Mapping[str, Any],
    instrument: Mapping[str, Any],
    record_set_reference: Mapping[str, Any],
) -> dict[str, Any]:
    source = core.load_json(LIBRARY_V1)
    entries = copy.deepcopy(source["entries"])
    for entry in entries:
        entry["canonical_identity"] = {"status": "not-promoted"}

    index = core.load_json(ROOT / PAMPLIST_AUTHORITIES["prototype_index"])
    build = core.load_json(ROOT / PAMPLIST_AUTHORITIES["juce_build"])
    if index.get("prototype_id") != "pamplist" or index.get("revision") != "0.6":
        raise ValueError("Pamplist prototype index is not exact revision 0.6")
    artifact = build["artifact"]
    executable = artifact["path"]
    bundle = executable.split("/Contents/MacOS/", 1)[0]
    entries.append(
        {
            "prototype_id": "pamplist",
            "revision": index["revision"],
            "display_name": "Pamplist",
            "summary": (
                "Seven independent generative percussion voices with lane-local "
                "motion, a shared cohesion body, and persistent impact trails."
            ),
            "controller_label": "Launch Control 3",
            "prototype_index": {
                "path": PAMPLIST_AUTHORITIES["prototype_index"],
                "byte_sha256": _sha256_path(PAMPLIST_AUTHORITIES["prototype_index"]),
            },
            "result_evidence": {
                "path": PAMPLIST_AUTHORITIES["results"],
                "byte_sha256": _sha256_path(PAMPLIST_AUTHORITIES["results"]),
            },
            "launch": {
                "kind": "juce-standalone",
                "cmake_target": "pamplist",
                "product_name": "Pamplist",
                "bundle_path": bundle,
                "executable_path": executable,
                "expected_executable": {
                    "status": "frozen",
                    "sha256": artifact["sha256"],
                },
            },
            "canonical_identity": {
                "status": "canonical",
                "instrument_reference": _exact_ref(instrument, "instrument_id"),
                "graph_reference": _exact_ref(graph, "graph_id"),
                "record_set_reference": dict(record_set_reference),
            },
        }
    )
    entries.sort(
        key=lambda item: (
            item["display_name"].casefold(),
            item["prototype_id"],
            item["revision"],
        )
    )
    value = {
        "schema_version": "instrument-audition-library-v2",
        "canonical_profile": "schuss-canonical-json-v1",
        "library_id": "instrument-lab-audition-library",
        "revision": 2,
        "claims": {
            "canonical_identity_count": 1,
            "production_ready": False,
            "runtime_authority": "prototype-build-only",
        },
        "entries": entries,
    }
    errors = core.schema_errors(value, schema, schema)
    if errors:
        raise ValueError("; ".join(errors))
    return value


def _stable_id(value: Mapping[str, Any]) -> str:
    for field in record_set_rules.ID_FIELDS:
        if field in value:
            return str(value[field])
    raise ValueError("record has no stable ID")


def generated() -> tuple[dict[str, bytes], bytes, dict[str, Any]]:
    catalog_schema, projection_schema = _catalog_schemas()
    library_schema = _library_schema()
    schemas = {
        "catalog-corpus-v7": catalog_schema,
        "catalog-projection-v7": projection_schema,
        "instrument-audition-library-v2": library_schema,
    }
    files = {
        f"schemas/{name}.schema.json": _canonical_bytes(schema)
        for name, schema in schemas.items()
    }
    parent_loaded = record_set_rules.load_record_set(ROOT, PARENT)
    selector_schema = parent_loaded.schemas["catalog-selection-v0"]
    component_schema = parent_loaded.schemas["component-contract-v1"]
    graph_schema = parent_loaded.schemas["dsp-graph-v0"]
    instrument_schema = parent_loaded.schemas["instrument-v1"]

    catalog, selector, family = _catalog_records(catalog_schema, selector_schema)
    components, specs = _components(component_schema, family)
    graph, ordered_specs = _graph(graph_schema, components, specs)
    instrument = _instrument(instrument_schema, graph, ordered_specs)

    records: list[tuple[str, str, dict[str, Any]]] = [
        ("catalog-corpus", "catalog-corpus-v7.json", catalog),
        ("catalog-selection", "catalog-selection-r6.json", selector),
    ]
    records.extend(
        (
            "component-contract",
            f"component-contract-{number:06d}.json",
            component,
        )
        for number, component in zip(range(42, 49), components, strict=True)
    )
    records.extend(
        [
            ("dsp-graph", "pamplist-graph.json", graph),
            ("instrument", "pamplist-instrument.json", instrument),
        ]
    )
    schema_for_record = {
        "catalog-corpus-v7": catalog_schema,
        "catalog-selection-v0": selector_schema,
        "component-contract-v1": component_schema,
        "dsp-graph-v0": graph_schema,
        "instrument-v1": instrument_schema,
    }
    for _kind, filename, value in records:
        schema = schema_for_record[value["schema_version"]]
        errors = core.schema_errors(value, schema, schema)
        if errors:
            raise ValueError(f"{filename}: {'; '.join(errors)}")
        files[f"{TASK_DIR}/{filename}"] = _canonical_bytes(value)

    parent = parent_loaded.manifest
    schema_members = copy.deepcopy(parent["schema_members"])
    existing_schemas = {item["schema_version"] for item in schema_members}
    for name in SCHEMA_NAMES:
        if name in existing_schemas:
            raise ValueError(f"Task 043 schema collides with parent: {name}")
        path = f"schemas/{name}.schema.json"
        schema_members.append(
            {
                "schema_version": name,
                "portable_path": path,
                "byte_sha256": _sha256_bytes(files[path]),
            }
        )
    record_members = copy.deepcopy(parent["record_members"])
    for kind, filename, value in records:
        path = f"{TASK_DIR}/{filename}"
        record_members.append(
            {
                "record_kind": kind,
                "stable_id": _stable_id(value),
                "revision": value["revision"],
                "content_hash": value["content_hash"],
                "portable_path": path,
                "byte_sha256": _sha256_bytes(files[path]),
            }
        )
    manifest_schema = core.load_json(ROOT / record_set_rules.RECORD_SET_SCHEMA)
    manifest = {
        "schema_version": "record-set-v0",
        "canonical_profile": "schuss-canonical-json-v1",
        "record_set_id": RECORD_SET_ID,
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "purpose": "prospective-task",
        "parent_reference": {"status": "included", **parent_loaded.reference},
        "schema_members": sorted(
            schema_members,
            key=lambda item: (item["byte_sha256"], item["portable_path"]),
        ),
        "record_members": sorted(
            record_members,
            key=lambda item: (
                item["record_kind"],
                item["stable_id"],
                item["revision"],
                item["content_hash"],
            ),
        ),
        "enforced_directories": sorted(
            set(parent["enforced_directories"]) | {TASK_DIR}
        ),
    }
    errors = core.schema_errors(manifest, manifest_schema, manifest_schema)
    if errors:
        raise ValueError("; ".join(errors))
    manifest["content_hash"] = core.record_content_hash(manifest, manifest_schema)

    library = _library(
        library_schema,
        graph,
        instrument,
        {
            key: manifest[key]
            for key in ("record_set_id", "revision", "content_hash")
        },
    )
    files[LIBRARY_V2.relative_to(ROOT).as_posix()] = _canonical_bytes(library)
    summary = {
        "schema_version": "task043-pamplist-canonical-generation-summary-v1",
        "status": "valid",
        "record_set_reference": {
            key: manifest[key]
            for key in ("record_set_id", "revision", "content_hash")
        },
        "family_reference": _exact_ref(family, "family_id"),
        "graph_reference": _exact_ref(graph, "graph_id"),
        "instrument_reference": _exact_ref(instrument, "instrument_id"),
        "component_contract_count": len(components),
        "instrument_parameter_count": len(instrument["parameters"]),
        "library_entry_count": len(library["entries"]),
        "canonical_library_entry_count": 1,
        "prototype_dsp_or_source_changed": False,
        "application_or_endpoint_opened": False,
        "git_or_publication_performed": False,
    }
    return files, _canonical_bytes(manifest), summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files, manifest, summary = generated()
    stale: list[str] = []
    for relative, data in sorted(files.items()):
        destination = ROOT / relative
        if args.check:
            if not destination.is_file() or destination.read_bytes() != data:
                stale.append(relative)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_bytes() != manifest:
            stale.append(OUTPUT.relative_to(ROOT).as_posix())
        if stale:
            raise SystemExit("stale Task 043 files: " + ", ".join(stale))
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_bytes(manifest)
    print(core.canonical_json(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
