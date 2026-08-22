#!/usr/bin/env python3
"""Generate Task 039's noncanonical audition library and operation surface."""

from __future__ import annotations

import argparse
import copy
import hashlib
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


PARENT = ROOT / "contracts/record-sets/task038-instrument-source-dependencies-v1.json"
OUTPUT = ROOT / "contracts/record-sets/ui-desktop-instrument-library-v1.json"
LIBRARY_OUTPUT = (
    ROOT / "research/prototype_support/instrument_library/audition-library-v1.json"
)
RECORD_SET_ID = "schuss-record-set-000033"
SCHEMA_NAMES = (
    "application-capability-description-v12",
    "instrument-audition-library-v1",
    "operation-request-v19",
    "operation-result-v19",
)


ENTRY_SPECS = (
    {
        "prototype_id": "cinderwheel",
        "revision": "0.1",
        "display_name": "Cinderwheel",
        "summary": "Resonant counterpoint instrument with Wake, Ember, Bloom, and Undertow performance behavior.",
        "controller_label": "Launch Control 3",
        "evidence_path": "research/prototypes/cinderwheel/RESULTS.md",
        "launch": {
            "cmake_target": "cinderwheel-instrument",
            "product_name": "Cinderwheel",
            "bundle_path": "build/cinderwheel-juce-trial/cinderwheel-instrument_artefacts/Release/Cinderwheel.app",
            "executable_path": "build/cinderwheel-juce-trial/cinderwheel-instrument_artefacts/Release/Cinderwheel.app/Contents/MacOS/Cinderwheel",
            "expected_executable": {"status": "unresolved"},
        },
    },
    {
        "prototype_id": "generative-drum-machine",
        "revision": "0.6",
        "display_name": "Schuss Generative Drums",
        "summary": "Six-lane generative rhythm instrument with fifteen studies and persistent per-lane voice shaping.",
        "controller_label": "Launch Control 3",
        "evidence_path": "research/prototypes/generative-drum-machine/contract/RESULTS.md",
        "launch": {
            "cmake_target": "schuss-generative-drums",
            "product_name": "Schuss Generative Drums",
            "bundle_path": "build/generative-drum-machine-juce/schuss-generative-drums_artefacts/Release/Schuss Generative Drums.app",
            "executable_path": "build/generative-drum-machine-juce/schuss-generative-drums_artefacts/Release/Schuss Generative Drums.app/Contents/MacOS/Schuss Generative Drums",
            "expected_executable": {
                "status": "frozen",
                "sha256": "5078176a25650e545c3e607f777d7e6fc8fb0ac62b25b0411c6cb1c9566790cd",
            },
        },
    },
    {
        "prototype_id": "tide-pit-gills",
        "revision": "0.1",
        "display_name": "Tide Pit Gills",
        "summary": "Source-authenticated Tide Pit port with generative mutation, scale, target, freeze, and performance controls.",
        "controller_label": "Launch Control 3",
        "evidence_path": "research/prototypes/tide-pit-gills/RESULTS.md",
        "launch": {
            "cmake_target": "tide-pit-gills-instrument",
            "product_name": "Tide Pit Gills",
            "bundle_path": "build/tide-pit-juce/tide-pit-gills-instrument_artefacts/Release/Tide Pit Gills.app",
            "executable_path": "build/tide-pit-juce/tide-pit-gills-instrument_artefacts/Release/Tide Pit Gills.app/Contents/MacOS/Tide Pit Gills",
            "expected_executable": {
                "status": "frozen",
                "sha256": "44f9f1e50fa04083f750d8385642f81631dc95588564fd9fd9c9d1a8c591052d",
            },
        },
    },
    {
        "prototype_id": "wirefall",
        "revision": "0.1",
        "display_name": "Wirefall 0.1",
        "summary": "Retained first Wirefall experiment with failed host-signal evidence.",
        "controller_label": "Gills panel",
        "evidence_path": "research/prototypes/wirefall/contract/RESULTS.md",
        "launch": None,
    },
    {
        "prototype_id": "wirefall-r02",
        "revision": "0.2",
        "display_name": "Wirefall 0.2",
        "summary": "Gated drone instrument built around Energy, Break, Pulse, Tick, and Wire/Shadow behavior.",
        "controller_label": "Gills panel",
        "evidence_path": "research/prototypes/wirefall-r02/contract/RESULTS.md",
        "launch": {
            "cmake_target": "wirefall-r02-instrument",
            "product_name": "Wirefall 0.2",
            "bundle_path": "build/wirefall-r02-juce/wirefall-r02-instrument_artefacts/Wirefall 0.2.app",
            "executable_path": "build/wirefall-r02-juce/wirefall-r02-instrument_artefacts/Wirefall 0.2.app/Contents/MacOS/Wirefall 0.2",
            "expected_executable": {
                "status": "frozen",
                "sha256": "7ef1332c2d211a7a0f2795663b040ac92c35fbf3defef35a4464ff70b93e6513",
            },
        },
    },
)


def _canonical_bytes(value: object) -> bytes:
    return (core.canonical_json(value) + "\n").encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _closed(required: Iterable[str], properties: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "type": "object",
        "required": list(required),
        "properties": dict(properties),
        "additionalProperties": False,
    }


def _portable_path() -> dict[str, Any]:
    return {
        "type": "string",
        "minLength": 1,
        "pattern": r"^(?!/)(?!.*(?:^|/)\.\.(?:/|$))(?!.*\\).+$",
    }


def _file_reference() -> dict[str, Any]:
    return _closed(
        ("path", "byte_sha256"),
        {
            "path": _portable_path(),
            "byte_sha256": {"type": "string", "pattern": r"^[0-9a-f]{64}$"},
        },
    )


def _library_schema() -> dict[str, Any]:
    expected = {
        "oneOf": [
            _closed(("status",), {"status": {"const": "unresolved"}}),
            _closed(
                ("status", "sha256"),
                {
                    "status": {"const": "frozen"},
                    "sha256": {"type": "string", "pattern": r"^[0-9a-f]{64}$"},
                },
            ),
        ]
    }
    launch = {
        "oneOf": [
            {"type": "null"},
            _closed(
                (
                    "kind",
                    "cmake_target",
                    "product_name",
                    "bundle_path",
                    "executable_path",
                    "expected_executable",
                ),
                {
                    "kind": {"const": "juce-standalone"},
                    "cmake_target": {
                        "type": "string",
                        "pattern": r"^[a-z][a-z0-9-]*$",
                    },
                    "product_name": {"type": "string", "minLength": 1},
                    "bundle_path": _portable_path(),
                    "executable_path": _portable_path(),
                    "expected_executable": expected,
                },
            ),
        ]
    }
    entry = _closed(
        (
            "prototype_id",
            "revision",
            "display_name",
            "summary",
            "controller_label",
            "prototype_index",
            "result_evidence",
            "launch",
        ),
        {
            "prototype_id": {"type": "string", "pattern": r"^[a-z][a-z0-9-]*$"},
            "revision": {"type": "string", "pattern": r"^[0-9]+(?:\.[0-9]+)?$"},
            "display_name": {"type": "string", "minLength": 1, "maxLength": 80},
            "summary": {"type": "string", "minLength": 1, "maxLength": 240},
            "controller_label": {"type": "string", "minLength": 1, "maxLength": 80},
            "prototype_index": _file_reference(),
            "result_evidence": _file_reference(),
            "launch": launch,
        },
    )
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "instrument-audition-library-v1.schema.json",
        "title": "Schuss noncanonical Instrument Lab audition library v1",
        **_closed(
            (
                "schema_version",
                "canonical_profile",
                "library_id",
                "revision",
                "claims",
                "entries",
            ),
            {
                "schema_version": {"const": "instrument-audition-library-v1"},
                "canonical_profile": {"const": "schuss-canonical-json-v1"},
                "library_id": {"const": "instrument-lab-audition-library"},
                "revision": {"const": 1},
                "claims": _closed(
                    ("canonical_schuss_records", "production_ready"),
                    {
                        "canonical_schuss_records": {"const": False},
                        "production_ready": {"const": False},
                    },
                ),
                "entries": {
                    "type": "array",
                    "x-schuss-array-kind": "sequence",
                    "minItems": len(ENTRY_SPECS),
                    "maxItems": len(ENTRY_SPECS),
                    "uniqueItems": True,
                    "items": entry,
                },
            },
        ),
    }


def _request_schema() -> dict[str, Any]:
    common = {
        "schema_version": {"const": "schuss-operation-request-v19"},
        "canonical_profile": {"const": "schuss-canonical-json-v1"},
    }
    identity = {
        "prototype_id": {"type": "string", "pattern": r"^[a-z][a-z0-9-]*$"},
        "revision": {"type": "string", "pattern": r"^[0-9]+(?:\.[0-9]+)?$"},
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "operation-request-v19.schema.json",
        "title": "Schuss instrument audition operation request v19",
        "oneOf": [
            _closed(
                ("schema_version", "canonical_profile", "operation", "payload"),
                {
                    **common,
                    "operation": {"const": "instrument.library.list"},
                    "payload": _closed((), {}),
                },
            ),
            _closed(
                ("schema_version", "canonical_profile", "operation", "payload"),
                {
                    **common,
                    "operation": {"const": "instrument.session.start"},
                    "payload": _closed(
                        ("prototype_id", "revision", "launch_intent"),
                        {
                            **identity,
                            "launch_intent": {
                                "const": "explicit-native-juce-audition"
                            },
                        },
                    ),
                },
            ),
            _closed(
                ("schema_version", "canonical_profile", "operation", "payload"),
                {
                    **common,
                    "operation": {"const": "instrument.session.inspect"},
                    "payload": _closed(
                        ("instrument_session_id",),
                        {
                            "instrument_session_id": {
                                "type": "string",
                                "pattern": r"^instrument-session-[0-9]{6}$",
                            }
                        },
                    ),
                },
            ),
        ],
    }


def _result_schema() -> dict[str, Any]:
    source = core.load_json(ROOT / "schemas/operation-result-v18.schema.json")
    source["$id"] = "operation-result-v19.schema.json"
    source["title"] = "Schuss instrument audition operation result v19"
    source["properties"]["schema_version"] = {
        "const": "schuss-operation-result-v19"
    }
    source["properties"]["operation"]["enum"] = [
        "instrument.library.list",
        "instrument.session.inspect",
        "instrument.session.start",
        "invalid-request",
    ]
    return source


def _application_schema() -> dict[str, Any]:
    source = core.load_json(
        ROOT / "schemas/application-capability-description-v11.schema.json"
    )
    source["$id"] = "application-capability-description-v12.schema.json"
    source["title"] = "Schuss application capability description v12"
    source["properties"]["schema_version"] = {
        "const": "application-capability-description-v12"
    }
    source["properties"]["description_version"] = {
        "const": "schuss-application-capability-description-v12"
    }
    operation = source["$defs"]["operationCapability"]["properties"]
    operation["operation"]["enum"] = sorted(
        set(operation["operation"]["enum"])
        | {
            "instrument.library.list",
            "instrument.session.inspect",
            "instrument.session.start",
        }
    )
    operation["domain_group"]["enum"] = sorted(
        set(operation["domain_group"]["enum"]) | {"instrument"}
    )
    operation["effect_class"]["enum"] = sorted(
        set(operation["effect_class"]["enum"]) | {"native-application-launch"}
    )
    operation["availability"]["enum"] = sorted(
        set(operation["availability"]["enum"])
        | {"requires-instrument-library-service"}
    )
    operation["request_schema_version"]["pattern"] = (
        r"^schuss-operation-request-v(?:[1-9]|1[0-9])$"
    )
    operation["result_schema_version"]["pattern"] = (
        r"^schuss-operation-result-v(?:[1-9]|1[0-9])$"
    )
    contexts = source["$defs"]["contextSet"]["items"]["enum"]
    source["$defs"]["contextSet"]["items"]["enum"] = sorted(
        set(contexts)
        | {
            "process-local-instrument-session-service",
            "repository-instrument-library",
        }
    )
    gates = source["$defs"]["gateSet"]["items"]["enum"]
    source["$defs"]["gateSet"]["items"]["enum"] = sorted(
        set(gates)
        | {
            "exact-prototype-revision",
            "native-application-launch-intent",
            "verified-executable",
        }
    )
    source["properties"]["operations"]["minItems"] = 50
    source["properties"]["operations"]["maxItems"] = 50
    return source


def _library_document(schema: dict[str, Any]) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    identities: set[tuple[str, str]] = set()
    for spec in ENTRY_SPECS:
        identity = (str(spec["prototype_id"]), str(spec["revision"]))
        if identity in identities:
            raise ValueError(f"duplicate audition-library identity: {identity}")
        identities.add(identity)
        prototype_path = (
            Path("research/prototypes") / identity[0] / "prototype-index.json"
        )
        prototype_bytes = (ROOT / prototype_path).read_bytes()
        prototype = core.load_json(ROOT / prototype_path)
        if (
            prototype.get("prototype_id") != identity[0]
            or prototype.get("revision") != identity[1]
            or prototype.get("claims")
            != {"canonical_schuss_record": False, "production_ready": False}
        ):
            raise ValueError(f"prototype authority mismatch: {identity}")
        evidence_path = Path(str(spec["evidence_path"]))
        evidence_bytes = (ROOT / evidence_path).read_bytes()
        launch = copy.deepcopy(spec["launch"])
        if isinstance(launch, dict):
            launch = {"kind": "juce-standalone", **launch}
        entries.append(
            {
                "prototype_id": identity[0],
                "revision": identity[1],
                "display_name": spec["display_name"],
                "summary": spec["summary"],
                "controller_label": spec["controller_label"],
                "prototype_index": {
                    "path": prototype_path.as_posix(),
                    "byte_sha256": _sha256_bytes(prototype_bytes),
                },
                "result_evidence": {
                    "path": evidence_path.as_posix(),
                    "byte_sha256": _sha256_bytes(evidence_bytes),
                },
                "launch": launch,
            }
        )
    entries.sort(key=lambda item: (item["display_name"].casefold(), item["prototype_id"]))
    document = {
        "schema_version": "instrument-audition-library-v1",
        "canonical_profile": "schuss-canonical-json-v1",
        "library_id": "instrument-lab-audition-library",
        "revision": 1,
        "claims": {"canonical_schuss_records": False, "production_ready": False},
        "entries": entries,
    }
    errors = core.schema_errors(document, schema, schema)
    if errors:
        raise ValueError("; ".join(errors))
    return document


def generated() -> tuple[dict[str, bytes], bytes, dict[str, Any]]:
    schemas = {
        "application-capability-description-v12": _application_schema(),
        "instrument-audition-library-v1": _library_schema(),
        "operation-request-v19": _request_schema(),
        "operation-result-v19": _result_schema(),
    }
    library = _library_document(schemas["instrument-audition-library-v1"])
    files = {
        f"schemas/{name}.schema.json": _canonical_bytes(schema)
        for name, schema in schemas.items()
    }
    files[LIBRARY_OUTPUT.relative_to(ROOT).as_posix()] = _canonical_bytes(library)

    parent = core.load_json(PARENT)
    schema_members = copy.deepcopy(parent["schema_members"])
    existing = {item["schema_version"] for item in schema_members}
    for name in SCHEMA_NAMES:
        if name in existing:
            raise ValueError(f"Task 039 schema collides with parent: {name}")
        path = f"schemas/{name}.schema.json"
        schema_members.append(
            {
                "schema_version": name,
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
        "parent_reference": {
            "status": "included",
            **{key: parent[key] for key in ("record_set_id", "revision", "content_hash")},
        },
        "schema_members": sorted(
            schema_members,
            key=lambda item: (item["byte_sha256"], item["portable_path"]),
        ),
        "record_members": copy.deepcopy(parent["record_members"]),
        "enforced_directories": copy.deepcopy(parent["enforced_directories"]),
    }
    errors = core.schema_errors(manifest, manifest_schema, manifest_schema)
    if errors:
        raise ValueError("; ".join(errors))
    manifest["content_hash"] = core.record_content_hash(manifest, manifest_schema)
    summary = {
        "schema_version": "task039-instrument-library-generation-summary-v1",
        "status": "valid",
        "record_set_reference": {
            key: manifest[key] for key in ("record_set_id", "revision", "content_hash")
        },
        "entry_count": len(library["entries"]),
        "launch_targets_with_frozen_hashes": sum(
            1
            for entry in library["entries"]
            if isinstance(entry["launch"], dict)
            and entry["launch"]["expected_executable"]["status"] == "frozen"
        ),
        "semantic_records_added": 0,
        "application_or_device_launched": False,
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
            raise SystemExit("stale Task 039 instrument-library files: " + ", ".join(stale))
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_bytes(manifest)
    print(core.canonical_json(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
