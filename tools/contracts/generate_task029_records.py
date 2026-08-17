#!/usr/bin/env python3
"""Generate the deterministic Task 029 Gills machine inspection layer."""

from __future__ import annotations

import argparse
import copy
import hashlib
import sys
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/contracts")]

from packages.schuss_core.control_plane import load_repository_context  # noqa: E402

import validator_core as core  # noqa: E402


PARENT = ROOT / "contracts/record-sets/task028-direct-palette-v1.json"
OUTPUT = ROOT / "contracts/record-sets/task029-gills-machines-v1.json"
ASSET = ROOT / "assets/gills/gills-panel-v06.svg"
TASK_ROOT = "contracts/task029"

SCHEMA_PATHS = {
    "machine-source-review-v0": "schemas/machine-source-review-v0.schema.json",
    "panel-layout-v0": "schemas/panel-layout-v0.schema.json",
    "machine-presentation-v0": "schemas/machine-presentation-v0.schema.json",
    "machine-v0": "schemas/machine-v0.schema.json",
    "operation-request-v9": "schemas/operation-request-v9.schema.json",
    "operation-result-v9": "schemas/operation-result-v9.schema.json",
    "application-capability-description-v2": "schemas/application-capability-description-v2.schema.json",
}

SOURCE_REVIEW_PATHS = {
    "palimpsest": f"{TASK_ROOT}/palimpsest-source-review-r1.json",
    "tide-pit": f"{TASK_ROOT}/tide-pit-source-review-r1.json",
}
PRESENTATION_PATHS = {
    "palimpsest": f"{TASK_ROOT}/palimpsest-presentation-r1.json",
    "tide-pit": f"{TASK_ROOT}/tide-pit-presentation-r1.json",
}
PANEL_PATH = f"{TASK_ROOT}/gills-panel-layout-r1.json"

GILLS_SOURCE_URL = "https://github.com/lalzart/gills-instruments"
GILLS_SOURCE_COMMIT = "53287e49e5bcc5fb0d73b546d88431f82467f969"
PANEL_SOURCE_URL = "https://github.com/ksoloti/ksoloti-gills"
PANEL_SOURCE_COMMIT = "280503036aee95e6c6ef91a1f1357443f4768faa"
PHOTO_SHA256 = "725fc22a21d5fe78118ad865e36eb9626eb9f74aa003309144b48614c1801674"

FILE_FACTS = {
    "palimpsest": (
        ("license", "projects/palimpsest-gills/LICENSE.md", "3ed2c3d7e2d88af7320354f51bcfd5748408145ecae1fabb7092ddc7f736acbc", "license"),
        ("readme", "projects/palimpsest-gills/README.md", "5371ebc7e5e53cf0db2c92e9db90151b4c67f2581c6730178e3dde4f85a369e6", "readme"),
        ("patch", "projects/palimpsest-gills/palimpsest-gills.axp", "95f92e4634353f4629677b1430041aa4d71238acf4bfcbadf236def46d81cfed", "legacy-patch"),
        ("object", "projects/palimpsest-gills/palimpsest.axo", "52dd0f13611620852c78afd5761f26835dbea138a498ddfa136f0a632ab3e9cd", "legacy-object"),
        ("dsp", "projects/palimpsest-gills/palimpsest_dsp.h", "28bf741f4841c98b8059574a7dcfe941b024d3f0bde9608bc2c7fec86d8ebb05", "dsp-source"),
    ),
    "tide-pit": (
        ("license", "projects/tide-pit-gills/LICENSE.md", "2701d4f24dfe91723d1d43103daa123e8be61e53ad09f142735c91f58a06baac", "license"),
        ("readme", "projects/tide-pit-gills/README.md", "be3a5174d13f03fc02faff57b9afa3275faf34b3210850c7f50b219fdad7b52a", "readme"),
        ("patch", "projects/tide-pit-gills/tidepit-gills.axp", "35b8df83ffc06bacca1890d936525c75758b193bcf7ef7edd69082acdb7e963c", "legacy-patch"),
        ("object", "projects/tide-pit-gills/tidepit.axo", "8e62fdfd1f6b101cb5b6f876d3d54538af8be9a04a46cddba2711eaabc3b9009", "legacy-object"),
        ("dsp", "projects/tide-pit-gills/tidepit_dsp.h", "3f75a3aa337109e7de270cb4a4aa7281f71ba4de443f057b4e37299e3bd7b32e", "dsp-source"),
        ("voice", "projects/tide-pit-gills/tidepit_voice.h", "e6cd224160df87afbfda5743c5124a4600c5f3c6fe4c02df272c41916cd6566c", "dsp-source"),
    ),
}

EVIDENCE_NAMES = (
    "schema-and-source-identity",
    "graph-and-instrument-closure",
    "compiler-lowering",
    "artifact-generation",
    "arm-compile-link",
    "connected-device",
    "realtime-and-resource",
    "audible-behavior",
)


def _json_bytes(value: Any) -> bytes:
    return core.canonical_json(value).encode("utf-8") + b"\n"


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _record(value: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(value)
    result["content_hash"] = "sha256:" + "0" * 64
    errors = core.schema_errors(result, schema, schema)
    if errors:
        raise ValueError("; ".join(errors))
    result["content_hash"] = core.record_content_hash(result, schema)
    return result


def _ref(record: dict[str, Any], field: str) -> dict[str, Any]:
    return {
        field: record[field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def _exact_ref_schema(field: str, pattern: str) -> dict[str, Any]:
    return {
        "type": "object",
        "required": [field, "revision", "content_hash"],
        "properties": {
            field: {"type": "string", "pattern": pattern},
            "revision": {"type": "integer", "minimum": 1},
            "content_hash": {"$ref": "#/$defs/contentHash"},
        },
        "additionalProperties": False,
    }


def _string_set(*, min_items: int = 0) -> dict[str, Any]:
    result: dict[str, Any] = {
        "type": "array",
        "x-schuss-array-kind": "set",
        "uniqueItems": True,
        "items": {"type": "string", "minLength": 1},
    }
    if min_items:
        result["minItems"] = min_items
    return result


def _evidence_level_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["level", "name", "status", "limitation"],
        "properties": {
            "level": {"type": "integer", "minimum": 1},
            "name": {"type": "string", "minLength": 1},
            "status": {"enum": ["passed", "not-run", "failed", "unsupported"]},
            "limitation": {"type": "string", "minLength": 1},
        },
        "additionalProperties": False,
    }


def _source_review_schema() -> dict[str, Any]:
    exact_source_ref = {
        "type": "object",
        "required": ["source_file_id", "line_start", "line_end", "claim"],
        "properties": {
            "source_file_id": {"type": "string", "pattern": "^source-file-[0-9]{6}$"},
            "line_start": {"type": "integer", "minimum": 1},
            "line_end": {"type": "integer", "minimum": 1},
            "claim": {"type": "string", "minLength": 1},
        },
        "additionalProperties": False,
    }
    source_file = {
        "type": "object",
        "required": ["source_file_id", "portable_path", "byte_sha256", "role"],
        "properties": {
            "source_file_id": {"type": "string", "pattern": "^source-file-[0-9]{6}$"},
            "portable_path": {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9._ -]*(?:/[A-Za-z0-9][A-Za-z0-9._ -]*)*$"},
            "byte_sha256": {"$ref": "#/$defs/rawSha256"},
            "role": {"enum": ["license", "readme", "legacy-patch", "legacy-object", "dsp-source"]},
        },
        "additionalProperties": False,
    }
    source_block = {
        "type": "object",
        "required": ["source_block_id", "label", "kind", "summary", "evidence_span_ids"],
        "properties": {
            "source_block_id": {"type": "string", "pattern": "^source-block-[0-9]{6}$"},
            "label": {"type": "string", "minLength": 1},
            "kind": {"enum": ["control", "event", "source", "audio", "state", "effect", "output", "display"]},
            "summary": {"type": "string", "minLength": 1},
            "evidence_span_ids": _string_set(min_items=1),
        },
        "additionalProperties": False,
    }
    source_edge = {
        "type": "object",
        "required": ["source_edge_id", "source_block_id", "destination_block_id", "signal_kind", "summary", "evidence_span_ids"],
        "properties": {
            "source_edge_id": {"type": "string", "pattern": "^source-edge-[0-9]{6}$"},
            "source_block_id": {"type": "string", "pattern": "^source-block-[0-9]{6}$"},
            "destination_block_id": {"type": "string", "pattern": "^source-block-[0-9]{6}$"},
            "signal_kind": {"enum": ["audio", "control", "event", "state", "display"]},
            "summary": {"type": "string", "minLength": 1},
            "evidence_span_ids": _string_set(min_items=1),
        },
        "additionalProperties": False,
    }
    mapping_meaning = {
        "type": "object",
        "required": ["mode", "meaning"],
        "properties": {
            "mode": {"type": "string", "pattern": "^[A-Z0-9-]+$"},
            "meaning": {"type": "string", "minLength": 1},
        },
        "additionalProperties": False,
    }
    panel_mapping = {
        "type": "object",
        "required": ["mapping_id", "semantic_slot_id", "mapping_state", "meanings", "evidence_span_ids"],
        "properties": {
            "mapping_id": {"type": "string", "pattern": "^source-mapping-[0-9]{6}$"},
            "semantic_slot_id": {"type": "string", "pattern": "^device-(input|gesture|feedback|display)-[0-9]{6}$"},
            "mapping_state": {"enum": ["mapped", "intentionally-unmapped"]},
            "meanings": {
                "type": "array",
                "x-schuss-array-kind": "sequence",
                "minItems": 1,
                "items": mapping_meaning,
            },
            "evidence_span_ids": _string_set(min_items=1),
        },
        "additionalProperties": False,
    }
    semantic_match = {
        "type": "object",
        "required": ["record_kind", "stable_id", "revision", "content_hash", "match_state"],
        "properties": {
            "record_kind": {"enum": ["component-contract", "implementation-binding", "device-profile", "binding-eligibility"]},
            "stable_id": {"type": "string", "pattern": "^schuss-[a-z0-9-]+-[0-9]{6}$"},
            "revision": {"type": "integer", "minimum": 1},
            "content_hash": {"$ref": "#/$defs/contentHash"},
            "match_state": {"enum": ["selectable", "accepted-support", "unsupported"]},
        },
        "additionalProperties": False,
    }
    catalog_observation = {
        "type": "object",
        "required": ["stable_id", "catalog_reference", "observation_state"],
        "properties": {
            "stable_id": {"type": "string", "pattern": "^schuss-(family|implementation)-[0-9]{6}$"},
            "catalog_reference": _exact_ref_schema("catalog_id", "^schuss-catalog-[0-9]{6}$"),
            "observation_state": {"enum": ["catalogued-only", "observed-only"]},
        },
        "additionalProperties": False,
    }
    dependency = {
        "type": "object",
        "required": [
            "dependency_id", "label", "required", "classification", "reason",
            "evidence_level", "evidence_status", "first_proof_gap",
            "schuss_matches", "catalog_observations", "evidence_span_ids",
        ],
        "properties": {
            "dependency_id": {"type": "string", "pattern": "^[a-z][a-z0-9-]*$"},
            "label": {"type": "string", "minLength": 1},
            "required": {"type": "boolean"},
            "classification": {"enum": [
                "selectable", "accepted-support", "catalogued-only", "observed-only",
                "absent", "private-helper", "non-object",
                "unsuitable-for-standalone-promotion", "unsupported",
            ]},
            "reason": {"type": "string", "minLength": 1},
            "evidence_level": {"type": "integer", "minimum": 1},
            "evidence_status": {"enum": ["passed", "not-run", "failed", "unsupported"]},
            "first_proof_gap": {"type": "string", "minLength": 1},
            "schuss_matches": {
                "type": "array", "x-schuss-array-kind": "set", "uniqueItems": True,
                "items": semantic_match,
            },
            "catalog_observations": {
                "type": "array", "x-schuss-array-kind": "set", "uniqueItems": True,
                "items": catalog_observation,
            },
            "evidence_span_ids": _string_set(min_items=1),
        },
        "additionalProperties": False,
    }
    patch_object = {
        "type": "object",
        "required": ["instance_name", "legacy_type", "role", "attributes"],
        "properties": {
            "instance_name": {"type": "string", "pattern": "^[a-z][a-z0-9_]*$"},
            "legacy_type": {"type": "string", "minLength": 1},
            "role": {"enum": ["configuration", "constant", "device-input", "machine-wrapper", "audio-output", "device-feedback", "device-display"]},
            "attributes": _string_set(),
        },
        "additionalProperties": False,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "machine-source-review-v0.schema.json",
        "title": "Schuss inspection-only machine source review v0",
        "type": "object",
        "required": [
            "schema_version", "canonical_profile", "machine_source_review_id", "revision",
            "content_hash", "inspection_state", "source_identity", "asserted_identity",
            "legacy_patch_shell", "evidence_spans", "source_blocks", "source_edges",
            "panel_mappings", "dependency_assessments", "resource_declarations", "evidence_levels",
        ],
        "properties": {
            "schema_version": {"const": "machine-source-review-v0"},
            "canonical_profile": {"const": "schuss-canonical-json-v1"},
            "machine_source_review_id": {"type": "string", "pattern": "^schuss-machine-source-review-[0-9]{6}$"},
            "revision": {"type": "integer", "minimum": 1},
            "content_hash": {"$ref": "#/$defs/contentHash"},
            "inspection_state": {"const": "inspection-only"},
            "source_identity": {
                "type": "object",
                "required": ["source_id", "repository_url", "commit", "project_root", "files"],
                "properties": {
                    "source_id": {"type": "string", "pattern": "^[a-z][a-z0-9-]*$"},
                    "repository_url": {"type": "string", "pattern": "^https://github\\.com/[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$"},
                    "commit": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
                    "project_root": {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9._ -]*(?:/[A-Za-z0-9][A-Za-z0-9._ -]*)*$"},
                    "files": {
                        "type": "array", "x-schuss-array-kind": "set", "minItems": 1,
                        "uniqueItems": True, "items": source_file,
                    },
                },
                "additionalProperties": False,
            },
            "asserted_identity": {
                "type": "object",
                "required": ["display_name", "summary", "aliases"],
                "properties": {
                    "display_name": {"type": "string", "minLength": 1},
                    "summary": {"type": "string", "minLength": 1},
                    "aliases": {
                        "type": "array", "x-schuss-array-kind": "set", "uniqueItems": True,
                        "items": {
                            "type": "object",
                            "required": ["input", "disposition", "correction"],
                            "properties": {
                                "input": {"type": "string", "minLength": 1},
                                "disposition": {"const": "corrected-input-only"},
                                "correction": {"type": "string", "minLength": 1},
                            },
                            "additionalProperties": False,
                        },
                    },
                },
                "additionalProperties": False,
            },
            "legacy_patch_shell": {
                "type": "object",
                "required": ["format", "application_version", "object_count", "connection_count", "object_instances", "configuration_facts", "evidence_span_ids"],
                "properties": {
                    "format": {"const": "legacy-axp"},
                    "application_version": {"const": "1.0.12"},
                    "object_count": {"const": 24},
                    "connection_count": {"const": 27},
                    "object_instances": {
                        "type": "array", "x-schuss-array-kind": "sequence", "minItems": 24,
                        "maxItems": 24, "items": patch_object,
                    },
                    "configuration_facts": _string_set(min_items=1),
                    "evidence_span_ids": _string_set(min_items=1),
                },
                "additionalProperties": False,
            },
            "evidence_spans": {
                "type": "array", "x-schuss-array-kind": "set", "minItems": 1,
                "uniqueItems": True,
                "items": {
                    "type": "object",
                    "required": ["evidence_span_id", "source"],
                    "properties": {
                        "evidence_span_id": {"type": "string", "pattern": "^source-span-[0-9]{6}$"},
                        "source": exact_source_ref,
                    },
                    "additionalProperties": False,
                },
            },
            "source_blocks": {
                "type": "array", "x-schuss-array-kind": "sequence", "minItems": 1,
                "items": source_block,
            },
            "source_edges": {
                "type": "array", "x-schuss-array-kind": "sequence", "items": source_edge,
            },
            "panel_mappings": {
                "type": "array", "x-schuss-array-kind": "set", "minItems": 34,
                "maxItems": 34, "uniqueItems": True, "items": panel_mapping,
            },
            "dependency_assessments": {
                "type": "array", "x-schuss-array-kind": "set", "minItems": 1,
                "uniqueItems": True, "items": dependency,
            },
            "resource_declarations": {
                "type": "array", "x-schuss-array-kind": "set", "uniqueItems": True,
                "items": {
                    "type": "object",
                    "required": ["resource_id", "label", "quantity", "unit", "declaration_kind", "evidence_span_ids"],
                    "properties": {
                        "resource_id": {"type": "string", "pattern": "^[a-z][a-z0-9-]*$"},
                        "label": {"type": "string", "minLength": 1},
                        "quantity": {"type": "integer", "minimum": 0},
                        "unit": {"enum": ["bytes", "items"]},
                        "declaration_kind": {"enum": ["source-declared-allocation", "source-structure"]},
                        "evidence_span_ids": _string_set(min_items=1),
                    },
                    "additionalProperties": False,
                },
            },
            "evidence_levels": {
                "type": "array", "x-schuss-array-kind": "sequence", "minItems": 8,
                "maxItems": 8, "items": _evidence_level_schema(),
            },
        },
        "additionalProperties": False,
        "$defs": {
            "contentHash": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
            "rawSha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        },
    }


def _panel_layout_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "panel-layout-v0.schema.json",
        "title": "Schuss authenticated semantic panel layout v0",
        "type": "object",
        "required": [
            "schema_version", "canonical_profile", "panel_layout_id", "revision", "content_hash",
            "device_profile_reference", "asset", "coordinate_system", "semantic_regions",
            "excluded_slots", "source_assets", "visual_verification", "evidence_levels",
        ],
        "properties": {
            "schema_version": {"const": "panel-layout-v0"},
            "canonical_profile": {"const": "schuss-canonical-json-v1"},
            "panel_layout_id": {"type": "string", "pattern": "^schuss-panel-layout-[0-9]{6}$"},
            "revision": {"type": "integer", "minimum": 1},
            "content_hash": {"$ref": "#/$defs/contentHash"},
            "device_profile_reference": _exact_ref_schema("device_profile_id", "^schuss-device-profile-[0-9]{6}$"),
            "asset": {
                "type": "object",
                "required": ["portable_path", "byte_sha256", "media_type", "license", "attribution", "adaptation_notice"],
                "properties": {
                    "portable_path": {"const": "assets/gills/gills-panel-v06.svg"},
                    "byte_sha256": {"$ref": "#/$defs/rawSha256"},
                    "media_type": {"const": "image/svg+xml"},
                    "license": {"const": "CC-BY-4.0"},
                    "attribution": {"type": "string", "minLength": 1},
                    "adaptation_notice": {"type": "string", "minLength": 1},
                },
                "additionalProperties": False,
            },
            "coordinate_system": {
                "type": "object",
                "required": ["origin", "x_direction", "y_direction", "unit", "width", "height"],
                "properties": {
                    "origin": {"const": "upper-left-outer-bounds"},
                    "x_direction": {"const": "right"},
                    "y_direction": {"const": "down"},
                    "unit": {"const": "millimetres"},
                    "width": {"const": "158"},
                    "height": {"const": "100"},
                },
                "additionalProperties": False,
            },
            "semantic_regions": {
                "type": "array", "x-schuss-array-kind": "set", "minItems": 42,
                "maxItems": 42, "uniqueItems": True,
                "items": {
                    "type": "object",
                    "required": ["semantic_slot_id", "slot_kind", "physical_label", "svg_element_id", "highlight_element_id", "anchor"],
                    "properties": {
                        "semantic_slot_id": {"type": "string", "pattern": "^device-(input|gesture|feedback|display)-[0-9]{6}$"},
                        "slot_kind": {"enum": ["input-control", "gesture", "feedback-output", "display"]},
                        "physical_label": {"type": "string", "minLength": 1},
                        "svg_element_id": {"type": "string", "pattern": "^[a-z][a-z0-9-]*$"},
                        "highlight_element_id": {"type": "string", "pattern": "^highlight-[a-z0-9-]+$"},
                        "anchor": {
                            "type": "object",
                            "required": ["x", "y"],
                            "properties": {
                                "x": {"$ref": "#/$defs/exactDecimal"},
                                "y": {"$ref": "#/$defs/exactDecimal"},
                            },
                            "additionalProperties": False,
                        },
                    },
                    "additionalProperties": False,
                },
            },
            "excluded_slots": {
                "type": "array", "x-schuss-array-kind": "set", "minItems": 1,
                "uniqueItems": True,
                "items": {
                    "type": "object",
                    "required": ["semantic_slot_id", "slot_kind", "reason"],
                    "properties": {
                        "semantic_slot_id": {"type": "string", "pattern": "^device-input-[0-9]{6}$"},
                        "slot_kind": {"const": "input-control"},
                        "reason": {"type": "string", "minLength": 1},
                    },
                    "additionalProperties": False,
                },
            },
            "source_assets": {
                "type": "array", "x-schuss-array-kind": "set", "minItems": 1,
                "uniqueItems": True,
                "items": {
                    "type": "object",
                    "required": ["repository_url", "commit", "portable_path", "byte_sha256", "authority", "license"],
                    "properties": {
                        "repository_url": {"type": "string", "pattern": "^https://github\\.com/[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$"},
                        "commit": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
                        "portable_path": {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9._ -]*(?:/[A-Za-z0-9][A-Za-z0-9._ -]*)*$"},
                        "byte_sha256": {"$ref": "#/$defs/rawSha256"},
                        "authority": {"enum": ["editable-layout-source", "metric-cad-source", "repository-license"]},
                        "license": {"const": "CC-BY-4.0"},
                    },
                    "additionalProperties": False,
                },
            },
            "visual_verification": {
                "type": "object",
                "required": ["reference_sha256", "retention_state", "result", "limitations"],
                "properties": {
                    "reference_sha256": {"$ref": "#/$defs/rawSha256"},
                    "retention_state": {"const": "non-retained-visual-reference"},
                    "result": {"const": "strong-v06-topology-and-appearance-match"},
                    "limitations": _string_set(min_items=1),
                },
                "additionalProperties": False,
            },
            "evidence_levels": {
                "type": "array", "x-schuss-array-kind": "sequence", "minItems": 8,
                "maxItems": 8, "items": _evidence_level_schema(),
            },
        },
        "additionalProperties": False,
        "$defs": {
            "contentHash": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
            "rawSha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            "exactDecimal": {"type": "string", "pattern": "^(?:0|-?(?:0\\.[0-9]*[1-9]|[1-9][0-9]*(?:\\.[0-9]*[1-9])?))$"},
        },
    }


def _presentation_schema() -> dict[str, Any]:
    graph_ref = _exact_ref_schema("graph_id", "^schuss-graph-[0-9]{6}$")
    graph_node_ref = copy.deepcopy(graph_ref)
    graph_node_ref["required"].append("node_id")
    graph_node_ref["properties"]["node_id"] = {"type": "string", "pattern": "^graph-node-[0-9]{6}$"}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "machine-presentation-v0.schema.json",
        "title": "Schuss machine presentation overlay v0",
        "type": "object",
        "required": [
            "schema_version", "canonical_profile", "machine_presentation_id", "revision",
            "content_hash", "presentation_state", "source_review_reference",
            "panel_layout_reference", "blocks", "edges", "panel_links",
        ],
        "properties": {
            "schema_version": {"const": "machine-presentation-v0"},
            "canonical_profile": {"const": "schuss-canonical-json-v1"},
            "machine_presentation_id": {"type": "string", "pattern": "^schuss-machine-presentation-[0-9]{6}$"},
            "revision": {"type": "integer", "minimum": 1},
            "content_hash": {"$ref": "#/$defs/contentHash"},
            "presentation_state": {"enum": ["inspection-only", "machine-complete"]},
            "source_review_reference": _exact_ref_schema("machine_source_review_id", "^schuss-machine-source-review-[0-9]{6}$"),
            "panel_layout_reference": _exact_ref_schema("panel_layout_id", "^schuss-panel-layout-[0-9]{6}$"),
            "blocks": {
                "type": "array", "x-schuss-array-kind": "sequence", "minItems": 1,
                "items": {
                    "type": "object",
                    "required": ["presentation_block_id", "label", "kind", "source_block_ids", "graph_node_references", "geometry"],
                    "properties": {
                        "presentation_block_id": {"type": "string", "pattern": "^presentation-block-[0-9]{6}$"},
                        "label": {"type": "string", "minLength": 1},
                        "kind": {"enum": ["control", "event", "source", "audio", "state", "effect", "output", "display"]},
                        "source_block_ids": _string_set(min_items=1),
                        "graph_node_references": {
                            "type": "array", "x-schuss-array-kind": "set", "uniqueItems": True,
                            "items": graph_node_ref,
                        },
                        "geometry": {
                            "type": "object",
                            "required": ["x", "y", "width", "height"],
                            "properties": {
                                "x": {"type": "integer", "minimum": 0},
                                "y": {"type": "integer", "minimum": 0},
                                "width": {"type": "integer", "minimum": 1},
                                "height": {"type": "integer", "minimum": 1},
                            },
                            "additionalProperties": False,
                        },
                    },
                    "additionalProperties": False,
                },
            },
            "edges": {
                "type": "array", "x-schuss-array-kind": "sequence",
                "items": {
                    "type": "object",
                    "required": ["presentation_edge_id", "source_block_id", "destination_block_id", "signal_kind", "source_edge_ids"],
                    "properties": {
                        "presentation_edge_id": {"type": "string", "pattern": "^presentation-edge-[0-9]{6}$"},
                        "source_block_id": {"type": "string", "pattern": "^presentation-block-[0-9]{6}$"},
                        "destination_block_id": {"type": "string", "pattern": "^presentation-block-[0-9]{6}$"},
                        "signal_kind": {"enum": ["audio", "control", "event", "state", "display"]},
                        "source_edge_ids": _string_set(min_items=1),
                    },
                    "additionalProperties": False,
                },
            },
            "panel_links": {
                "type": "array", "x-schuss-array-kind": "set", "uniqueItems": True,
                "items": {
                    "type": "object",
                    "required": ["source_mapping_id", "presentation_block_id", "semantic_slot_id", "modes"],
                    "properties": {
                        "source_mapping_id": {"type": "string", "pattern": "^source-mapping-[0-9]{6}$"},
                        "presentation_block_id": {"type": "string", "pattern": "^presentation-block-[0-9]{6}$"},
                        "semantic_slot_id": {"type": "string", "pattern": "^device-(input|gesture|feedback|display)-[0-9]{6}$"},
                        "modes": _string_set(min_items=1),
                    },
                    "additionalProperties": False,
                },
            },
        },
        "additionalProperties": False,
        "$defs": {"contentHash": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"}},
    }


def _machine_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "machine-v0.schema.json",
        "title": "Schuss completed machine identity v0",
        "type": "object",
        "required": [
            "schema_version", "canonical_profile", "machine_id", "revision", "content_hash",
            "display_name", "summary", "instrument_reference", "source_review_reference",
            "presentation_reference",
        ],
        "properties": {
            "schema_version": {"const": "machine-v0"},
            "canonical_profile": {"const": "schuss-canonical-json-v1"},
            "machine_id": {"type": "string", "pattern": "^schuss-machine-[0-9]{6}$"},
            "revision": {"type": "integer", "minimum": 1},
            "content_hash": {"$ref": "#/$defs/contentHash"},
            "display_name": {"type": "string", "minLength": 1},
            "summary": {"type": "string", "minLength": 1},
            "instrument_reference": _exact_ref_schema("instrument_id", "^schuss-instrument-[0-9]{6}$"),
            "source_review_reference": _exact_ref_schema("machine_source_review_id", "^schuss-machine-source-review-[0-9]{6}$"),
            "presentation_reference": _exact_ref_schema("machine_presentation_id", "^schuss-machine-presentation-[0-9]{6}$"),
        },
        "additionalProperties": False,
        "$defs": {"contentHash": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"}},
    }


def _operation_schemas() -> tuple[dict[str, Any], dict[str, Any]]:
    content_hash = {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"}
    def request_branch(kind: str) -> dict[str, Any]:
        if kind == "source-review":
            reference = {
                "type": "object", "additionalProperties": False,
                "required": ["machine_source_review_id", "revision", "content_hash"],
                "properties": {
                    "machine_source_review_id": {"type": "string", "pattern": "^schuss-machine-source-review-[0-9]{6}$"},
                    "revision": {"type": "integer", "minimum": 1}, "content_hash": content_hash,
                },
            }
            property_name = "source_review_reference"
        else:
            reference = {
                "type": "object", "additionalProperties": False,
                "required": ["machine_id", "revision", "content_hash"],
                "properties": {
                    "machine_id": {"type": "string", "pattern": "^schuss-machine-[0-9]{6}$"},
                    "revision": {"type": "integer", "minimum": 1}, "content_hash": content_hash,
                },
            }
            property_name = "machine_reference"
        return {
            "type": "object", "additionalProperties": False,
            "required": ["schema_version", "canonical_profile", "operation", "payload"],
            "properties": {
                "schema_version": {"const": "schuss-operation-request-v9"},
                "canonical_profile": {"const": "schuss-canonical-json-v1"},
                "operation": {"const": "machine.inspect"},
                "payload": {
                    "type": "object", "additionalProperties": False,
                    "required": [property_name], "properties": {property_name: reference},
                },
            },
        }
    request = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "operation-request-v9.schema.json",
        "title": "Schuss read-only machine inspection request v9",
        "oneOf": [request_branch("source-review"), request_branch("machine")],
    }
    result = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "operation-result-v9.schema.json",
        "title": "Schuss read-only machine inspection result v9",
        "type": "object",
        "required": ["schema_version", "canonical_profile", "operation", "status", "value", "diagnostics"],
        "properties": {
            "schema_version": {"const": "schuss-operation-result-v9"},
            "canonical_profile": {"const": "schuss-canonical-json-v1"},
            "operation": {"enum": ["machine.inspect", "invalid-request"]},
            "status": {"enum": ["success", "invalid", "unresolved", "unsupported", "ambiguous", "conflict"]},
            "value": {"oneOf": [{"type": "null"}, {"type": "object", "x-schuss-domain-value": True}]},
            "diagnostics": {
                "type": "array", "x-schuss-array-kind": "sequence",
                "items": {"$ref": "#/$defs/diagnostic"},
            },
        },
        "additionalProperties": False,
        "$defs": {
            "diagnostic": {
                "type": "object", "additionalProperties": False,
                "required": ["code", "severity", "subject", "location", "message"],
                "properties": {
                    "code": {"type": "string", "pattern": "^[A-Z][A-Z0-9_]*$"},
                    "severity": {"enum": ["error", "warning", "info"]},
                    "subject": {"type": "string", "minLength": 1},
                    "location": {"type": "string", "minLength": 1},
                    "message": {"type": "string", "minLength": 1},
                },
            },
        },
    }
    return request, result


def _application_schema() -> dict[str, Any]:
    schema = copy.deepcopy(core.load_json(ROOT / "schemas/application-capability-description-v1.schema.json"))
    schema["$id"] = "application-capability-description-v2.schema.json"
    schema["title"] = "Schuss application capability description v2"
    schema["properties"]["schema_version"]["const"] = "application-capability-description-v2"
    schema["properties"]["description_version"]["const"] = "schuss-application-capability-description-v2"
    operations = schema["properties"]["operations"]
    operations["minItems"] = 19
    operations["maxItems"] = 19
    capability = schema["$defs"]["operationCapability"]["properties"]
    capability["operation"]["enum"].append("machine.inspect")
    capability["operation"]["enum"].sort()
    capability["domain_group"]["enum"].append("machine")
    capability["domain_group"]["enum"].sort()
    capability["request_schema_version"]["pattern"] = "^schuss-operation-request-v[1-9]$"
    capability["result_schema_version"]["pattern"] = "^schuss-operation-result-v[1-9]$"
    return schema


def schemas() -> dict[str, dict[str, Any]]:
    request, result = _operation_schemas()
    return {
        "machine-source-review-v0": _source_review_schema(),
        "panel-layout-v0": _panel_layout_schema(),
        "machine-presentation-v0": _presentation_schema(),
        "machine-v0": _machine_schema(),
        "operation-request-v9": request,
        "operation-result-v9": result,
        "application-capability-description-v2": _application_schema(),
    }


def _levels(structural_limitation: str) -> list[dict[str, Any]]:
    limitations = (
        structural_limitation,
        "No authoritative Schuss graph or accepted instrument closure is established.",
        "No compiler lowering was run.",
        "No source or firmware artifact was generated.",
        "No ARM compiler or linker was invoked.",
        "No connected device action was performed.",
        "Source declarations are not resource or real-time measurements.",
        "No listening or audible-equivalence evaluation was performed.",
    )
    return [
        {
            "level": index,
            "name": name,
            "status": "passed" if index == 1 else "not-run",
            "limitation": limitations[index - 1],
        }
        for index, name in enumerate(EVIDENCE_NAMES, 1)
    ]


def _find_exact(context: Any, group: str, field: str, stable_id: str, revision: int) -> dict[str, Any]:
    matches = [
        value for value in context.records[group]
        if value.get(field) == stable_id and value.get("revision") == revision
    ]
    if len(matches) != 1:
        raise ValueError(f"{stable_id}@{revision} must resolve exactly once")
    return matches[0]


def _semantic_match(record: dict[str, Any], record_kind: str, id_field: str, state: str) -> dict[str, Any]:
    return {
        "record_kind": record_kind,
        "stable_id": record[id_field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
        "match_state": state,
    }


def _catalog_observation(catalog: dict[str, Any], stable_id: str, state: str) -> dict[str, Any]:
    return {
        "stable_id": stable_id,
        "catalog_reference": _ref(catalog, "catalog_id"),
        "observation_state": state,
    }


def _span(number: int, file_id: int, start: int, end: int, claim: str) -> dict[str, Any]:
    return {
        "evidence_span_id": f"source-span-{number:06d}",
        "source": {
            "source_file_id": f"source-file-{file_id:06d}",
            "line_start": start,
            "line_end": end,
            "claim": claim,
        },
    }


def _patch_objects(wrapper: str, pot_names: Iterable[str], button_name: str) -> list[dict[str, Any]]:
    result = [
        {"instance_name": "audio_config", "legacy_type": "audio/outconfig", "role": "configuration", "attributes": ["headphones=-24dB", "mode=Stereo"]},
        {"instance_name": "root_init", "legacy_type": "const/i", "role": "constant", "attributes": ["value=60"]},
        {"instance_name": "root", "legacy_type": "ksoloti/gills/encoder", "role": "device-input", "attributes": ["min=36", "max=72"]},
    ]
    for number, name in enumerate(pot_names, 1):
        result.append({"instance_name": name, "legacy_type": "ksoloti/gills/pot p", "role": "device-input", "attributes": [f"pot={number}"]})
    for number, name in enumerate((button_name, "mutate", "lock", "effect"), 1):
        result.append({"instance_name": name, "legacy_type": "ksoloti/gills/button", "role": "device-input", "attributes": [f"button={number}"]})
    result.extend(
        [
            {"instance_name": wrapper, "legacy_type": f"./{wrapper}", "role": "machine-wrapper", "attributes": []},
            {"instance_name": "audio_out", "legacy_type": "audio/out stereo", "role": "audio-output", "attributes": []},
        ]
    )
    for number in range(1, 5):
        selection = str(number) if number < 3 else f"{number} blue"
        result.append({"instance_name": f"led{number}", "legacy_type": "ksoloti/gills/led", "role": "device-feedback", "attributes": [f"led={selection}"]})
    result.append({"instance_name": "display", "legacy_type": "ksoloti/gills/display", "role": "device-display", "attributes": ["narrowFont=on", "useScope=off"]})
    if len(result) != 24:
        raise ValueError("legacy patch object inventory must remain exactly 24")
    return result


def _mapping(
    number: int,
    slot: str,
    meanings: Iterable[tuple[str, str]],
    span_id: str,
    *,
    mapped: bool = True,
) -> dict[str, Any]:
    return {
        "mapping_id": f"source-mapping-{number:06d}",
        "semantic_slot_id": slot,
        "mapping_state": "mapped" if mapped else "intentionally-unmapped",
        "meanings": [{"mode": mode, "meaning": meaning} for mode, meaning in meanings],
        "evidence_span_ids": [span_id],
    }


def _panel_mappings(kind: str, control_span: str, display_span: str) -> list[dict[str, Any]]:
    tide = kind == "tide-pit"
    base = [
        ("device-input-000001", [("ALL", "Stage 1 pitch value")]),
        ("device-input-000002", [("ALL", "Stage 2 pitch value")]),
        ("device-input-000003", [("ALL", "Stage 3 pitch value")]),
        ("device-input-000004", [("ALL", "Stage 4 pitch value")]),
        ("device-input-000005", [("ALL", "Cycle rate")]),
        ("device-input-000006", [("ALL", "Memory and mutation amount")]),
        ("device-input-000007", [("ALL", "Timbre and material") if tide else ("ALL", "Harmonic-to-inharmonic material")]),
        ("device-input-000008", [("ALL", "Grain position") if tide else ("ALL", "Trace spacing")]),
        ("device-input-000009", [
            ("CLEAN", "Grain size" if tide else "Modal decay"),
            ("FILT", "Filter cutoff"),
            ("DRIVE", "Drive tone"),
        ]),
        ("device-input-000010", [
            ("CLEAN", "Depth, spread, and tail" if tide else "Activity and wake mix"),
            ("FILT", "Filter resonance"),
            ("DRIVE", "Drive amount"),
        ]),
    ]
    result = [_mapping(index, slot, meanings, control_span) for index, (slot, meanings) in enumerate(base, 1)]
    gesture_specs = (
        ("device-gesture-000001", [("ALL", "Cycle REED, RND, and FOLD source" if tide else "Cycle TRACE, KNOCK, SKIN, and SHARD recipe")], True),
        ("device-gesture-000002", [("ALL", "No release action in the inspected source")], False),
        ("device-gesture-000003", [("ALL", "No hold action in the inspected source")], False),
        ("device-gesture-000004", [("ALL", "Mutate once")], True),
        ("device-gesture-000005", [("ALL", "No release action in the inspected source")], False),
        ("device-gesture-000006", [("ALL", "No hold action in the inspected source")], False),
        ("device-gesture-000007", [("ALL", "Toggle automatic mutation lock")], True),
        ("device-gesture-000008", [("ALL", "No release action in the inspected source")], False),
        ("device-gesture-000009", [("ALL", "No hold action in the inspected source")], False),
        ("device-gesture-000010", [("ALL", "Begin Button 4 tap-or-hold timing")], True),
        ("device-gesture-000011", [("ALL", "Cycle CLEAN, FILT, and DRIVE when released before hold threshold")], True),
        ("device-gesture-000012", [("ALL", "Capture or freeze granular buffer" if tide else "Clear voices and scheduled events")], True),
        ("device-gesture-000013", [("ALL", "Set root from C2 through C5")], True),
        ("device-gesture-000014", [("ALL", "Cycle scale")], True),
        ("device-gesture-000015", [("ALL", "No separate release action in the inspected source")], False),
        ("device-gesture-000016", [("ALL", "Cycle pitch, body, grain, and all-wave destination" if tide else "No encoder-hold mapping in the inspected source")], tide),
    )
    for offset, (slot, meanings, mapped) in enumerate(gesture_specs, 11):
        result.append(_mapping(offset, slot, meanings, control_span, mapped=mapped))
    feedback = (
        ("device-feedback-000001", "Active stage 1", True),
        ("device-feedback-000002", "Active stage 2", True),
        ("device-feedback-000003", "Active stage 3 on LED3 color-A channel", True),
        ("device-feedback-000004", "LED3 red channel is not driven by this patch", False),
        ("device-feedback-000005", "Active stage 4 on LED4 color-A channel", True),
        ("device-feedback-000006", "LED4 red channel is not driven by this patch", False),
    )
    for offset, (slot, meaning, mapped) in enumerate(feedback, 27):
        result.append(_mapping(offset, slot, [("ALL", meaning)], display_span, mapped=mapped))
    display_meaning = (
        "Four OLED text lines: identity/root, stages, memory/effects, and status"
        if tide
        else "Four OLED text lines: identity/recipe/root, stage form, memory/effects, and status"
    )
    result.append(_mapping(33, "device-display-000001", [("ALL", display_meaning)], display_span))
    result.append(_mapping(34, "device-display-000002", [("ALL", "OLED graphics capability is not used by the inspected patch")], display_span, mapped=False))
    return result


def _dependency(
    dependency_id: str,
    label: str,
    classification: str,
    reason: str,
    first_gap: str,
    span_id: str,
    *,
    required: bool = True,
    status: str = "not-run",
    matches: Iterable[dict[str, Any]] = (),
    observations: Iterable[dict[str, Any]] = (),
) -> dict[str, Any]:
    return {
        "dependency_id": dependency_id,
        "label": label,
        "required": required,
        "classification": classification,
        "reason": reason,
        "evidence_level": 1,
        "evidence_status": status,
        "first_proof_gap": first_gap,
        "schuss_matches": list(matches),
        "catalog_observations": list(observations),
        "evidence_span_ids": [span_id],
    }


def _source_blocks(kind: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    tide = kind == "tide-pit"
    if tide:
        specs = (
            ("Four-stage mutation engine", "control", "Pitch cycle, memory mutation, root, scale, source, effect, and destination state.", "source-span-000004"),
            ("Selectable excitation", "source", "REED waveguide, RND sine/triangle, or Braids-derived FOLD excitation.", "source-span-000006"),
            ("Sympathetic string and energy", "audio", "Sympathetic feedback string followed by energy and LPG shaping.", "source-span-000006"),
            ("Eight-mode stereo body", "audio", "Stereo body resonator with eight response modes.", "source-span-000006"),
            ("Granular record and six-grain engine", "audio", "Clouds-derived 16-bit record buffer and six-grain processor.", "source-span-000004"),
            ("Dry/wet and diffusion tail", "effect", "Dry/wet mix followed by a Clouds diffusion reverb tail.", "source-span-000004"),
            ("CLEAN, FILT, or DRIVE", "effect", "Mode-specific clean path, resonant filter, or tone-shaped drive.", "source-span-000004"),
            ("Soft clip and stereo output", "output", "stmlib soft clipping followed by stereo output.", "source-span-000004"),
            ("Gills feedback and OLED", "display", "Four stage LEDs and four source-rendered OLED text lines.", "source-span-000005"),
        )
        signals = ("control", "audio", "audio", "audio", "audio", "audio", "audio", "display")
    else:
        specs = (
            ("Four-stage mutation engine", "control", "Pitch cycle, memory mutation, root, scale, voice recipe, and effect state.", "source-span-000004"),
            ("Direct strike and trace events", "event", "One direct modal strike and three scale-aware delayed trace events.", "source-span-000004"),
            ("Fixed event scheduler", "state", "Fixed 16-event scheduler coordinates delayed traces.", "source-span-000005"),
            ("Fixed modal voice pool", "audio", "Fixed 16-voice pool with quietest-voice stealing and three partials per voice.", "source-span-000003"),
            ("Braids sine modal synthesis", "source", "Braids sine-table resources excite recipe-controlled modal partials.", "source-span-000003"),
            ("Direct and wake stereo mix", "audio", "Panned direct voices and wake activity combine in stereo.", "source-span-000004"),
            ("CLEAN, FILT, or DRIVE", "effect", "Mode-specific clean path, custom resonant filter, or asymmetric drive.", "source-span-000004"),
            ("Rational limiter and stereo output", "output", "The rational x/(1+abs(x)) limiter feeds stereo output.", "source-span-000004"),
            ("Gills feedback and OLED", "display", "Four stage LEDs and four source-rendered OLED text lines.", "source-span-000006"),
        )
        signals = ("event", "event", "event", "audio", "audio", "audio", "audio", "display")
    blocks = [
        {
            "source_block_id": f"source-block-{index:06d}",
            "label": label,
            "kind": block_kind,
            "summary": summary,
            "evidence_span_ids": [span_id],
        }
        for index, (label, block_kind, summary, span_id) in enumerate(specs, 1)
    ]
    edges = [
        {
            "source_edge_id": f"source-edge-{index:06d}",
            "source_block_id": f"source-block-{index:06d}",
            "destination_block_id": f"source-block-{index + 1:06d}",
            "signal_kind": signal,
            "summary": f"{specs[index - 1][0]} feeds {specs[index][0]}.",
            "evidence_span_ids": sorted({specs[index - 1][3], specs[index][3]}),
        }
        for index, signal in enumerate(signals, 1)
    ]
    return blocks, edges


def _review(kind: str, schema: dict[str, Any], context: Any) -> dict[str, Any]:
    tide = kind == "tide-pit"
    number = 2 if tide else 1
    display_name = "Tide Pit" if tide else "Palimpsest"
    project_root = "projects/tide-pit-gills" if tide else "projects/palimpsest-gills"
    wrapper = "tidepit" if tide else "palimpsest"
    files = [
        {
            "source_file_id": f"source-file-{index:06d}",
            "portable_path": path,
            "byte_sha256": digest,
            "role": role,
        }
        for index, (_, path, digest, role) in enumerate(FILE_FACTS[kind], 1)
    ]
    if tide:
        spans = [
            _span(1, 3, 6, 132, "The legacy patch contains 24 objects, 27 nets, and the complete Gills shell."),
            _span(2, 4, 6, 73, "The local object owns the public inlet, outlet, and embedded-code seam."),
            _span(3, 5, 30, 203, "Main oscillator and granular engine structures are declared here."),
            _span(4, 5, 206, 805, "Instrument control, effects, allocation, processing, and OLED behavior are declared here."),
            _span(5, 5, 734, 805, "LED stage feedback and OLED text formatting are declared here."),
            _span(6, 6, 40, 388, "Waveguide, sympathetic string, body, and diffusion-tail helpers are declared here."),
            _span(7, 1, 1, 21, "Project-local license terms are recorded without inferring third-party file licenses."),
        ]
        pot_names = ("stage1", "stage2", "stage3", "stage4", "rate", "memory", "material", "grain_position", "grain_size", "depth")
        summary = "A four-stage generative physical-model and granular instrument with selectable excitation, sympathetic string, stereo body, freeze buffer, diffusion tail, and three output modes."
    else:
        spans = [
            _span(1, 3, 6, 132, "The legacy patch contains 24 objects, 27 nets, and the complete Gills shell."),
            _span(2, 4, 6, 73, "The local object owns the public inlet, outlet, and embedded-code seam."),
            _span(3, 5, 38, 203, "The three-partial modal voice, recipe, transient, decay, and panning behavior are declared here."),
            _span(4, 5, 205, 590, "Instrument processing, stage controls, mix, effects, and limiter behavior are declared here."),
            _span(5, 5, 594, 738, "The fixed event scheduler and fixed voice allocator are declared here."),
            _span(6, 5, 771, 838, "LED stage feedback and OLED text formatting are declared here."),
            _span(7, 1, 1, 5, "Project-local license terms are recorded without inferring third-party file licenses."),
        ]
        pot_names = ("stage1", "stage2", "stage3", "stage4", "rate", "memory", "material", "spacing", "decay", "wake")
        summary = "A four-stage generative modal instrument that schedules delayed traces into a fixed voice pool, then shapes a stereo wake through clean, filtered, or asymmetric-drive modes."
    blocks, edges = _source_blocks(kind)
    output_binding = _find_exact(context, "bindings", "implementation_id", "schuss-implementation-000048", 2)
    output_contract = _find_exact(context, "contracts", "component_contract_id", "schuss-component-contract-000009", 1)
    device = _find_exact(context, "devices", "device_profile_id", "schuss-device-profile-000001", 2)
    rings = _find_exact(context, "eligibility", "binding_eligibility_id", "schuss-binding-eligibility-000031", 1)
    catalog = context.records["catalog"][0]
    shared = [
        _dependency(
            "stereo-audio-output", "Stereo audio output", "accepted-support",
            "The exact stereo output contract and native binding are accepted support, but source equivalence to the legacy wrapper is not inferred.",
            "Exact wrapper-to-contract semantic equivalence and later build evidence are not established.", "source-span-000001",
            status="passed",
            matches=(
                _semantic_match(output_contract, "component-contract", "component_contract_id", "accepted-support"),
                _semantic_match(output_binding, "implementation-binding", "implementation_id", "accepted-support"),
            ),
        ),
        _dependency(
            "audio-output-configuration", "Headphone and stereo output configuration", "observed-only",
            "audio/outconfig is an observed Ksoloti shell facility, not a reviewed public machine object.",
            "Machine/runtime configuration ownership has not been accepted.", "source-span-000001",
        ),
        _dependency(
            "root-constant", "Initial MIDI root constant", "catalogued-only",
            "The root default is machine state; catalog identities do not establish required support.",
            "An exact instrument state/default contract is absent.", "source-span-000001",
            observations=(
                _catalog_observation(catalog, "schuss-family-000052", "catalogued-only"),
                _catalog_observation(catalog, "schuss-implementation-000072", "catalogued-only"),
            ),
        ),
        _dependency(
            "gills-device-services", "Gills controls, gestures, indicators, and display", "non-object",
            "These are physical device-profile slots and runtime services, never DSP palette objects.",
            "No exact accepted instrument mapping or machine runtime exists for this source review.", "source-span-000001",
            status="passed",
            matches=(_semantic_match(device, "device-profile", "device_profile_id", "accepted-support"),),
        ),
        _dependency(
            "gills-oled-service", "Gills OLED text service", "catalogued-only",
            "The catalogued legacy display identity and Task 021 evidence do not generalize to this source closure.",
            "An exact accepted display binding/runtime for this machine is absent.", "source-span-000001",
            observations=(
                _catalog_observation(catalog, "schuss-family-000025", "catalogued-only"),
                _catalog_observation(catalog, "schuss-implementation-000037", "catalogued-only"),
            ),
        ),
        _dependency(
            "local-machine-wrapper", f"Local ./{wrapper} wrapper", "unsuitable-for-standalone-promotion",
            "The wrapper contains the complete instrument seam and would hide the transparent machine graph if promoted as one drawer object.",
            "Authoritative component contracts, graph, and instrument mappings are absent.", "source-span-000002",
        ),
    ]
    if tide:
        specific = [
            _dependency("reed-waveguide", "High-resolution REED feedback waveguide", "private-helper", "The waveguide is a modified local helper and is not semantically interchangeable with similarly named catalog candidates.", "Exact transparent graph decomposition and host vectors are absent.", "source-span-000006"),
            _dependency("source-oscillators", "RND and Braids-derived FOLD excitation", "private-helper", "Local math and Braids resources implement the excitation paths; name similarity proves no catalog substitution.", "Exact contracts, resource identities, and semantic vectors are absent.", "source-span-000003"),
            _dependency("string-lpg-body", "Sympathetic string, energy/LPG, and eight-mode body", "private-helper", "These source-local implementation units form the physical-model closure.", "Exact graph nodes, types, and resource evidence are absent.", "source-span-000006"),
            _dependency("clouds-granular-engine", "Clouds-derived record buffer and six-grain engine", "catalogued-only", "A Clouds-like catalog observation exists, but no exact accepted contract or binding proves this six-grain closure.", "Exact code/resource/parameter semantics and resource qualification are absent.", "source-span-000004", observations=(_catalog_observation(catalog, "schuss-implementation-000010", "catalogued-only"),)),
            _dependency("clouds-diffusion-tail", "Clouds diffusion reverb tail", "private-helper", "This embedded FxEngine<16384, FORMAT_16_BIT> closure is not the separately unsupported Rings wrapper.", "Exact graph/resource contract and later resource measurement are absent.", "source-span-000006"),
            _dependency("output-effects", "Resonant filter, tone drive, and stmlib soft clip", "private-helper", "Selectable analogues do not establish exact transfer functions or state semantics.", "Exact semantic vectors and graph contracts are absent.", "source-span-000004"),
            _dependency("braids-clouds-stmlib-resources", "Braids, Clouds, and stmlib code resources", "non-object", "Headers, tables, and helper code are linked resources, not browsable DSP objects.", "Content-addressed resource descriptors and per-file license closure are absent.", "source-span-000003"),
            _dependency("ksoloti-sdram-services", "Ksoloti SDRAM allocation services", "non-object", "sdram_malloc and BUFSIZE are target/runtime facilities; source allocation is not resource proof.", "Target-specific allocation success, peak usage, and real-time margins are not measured.", "source-span-000004"),
            _dependency("rings-reverb-non-dependency", "Unsupported Rings reverb binding", "unsupported", "Tide Pit does not use this binding; it remains independently unsupported and cannot resolve the Clouds diffusion tail.", "The retained allocation contradiction remains failed closed.", "source-span-000006", required=False, status="unsupported", matches=(_semantic_match(rings, "binding-eligibility", "binding_eligibility_id", "unsupported"),)),
        ]
        resources = [
            {"resource_id": "waveguide-buffers", "label": "Feedback waveguide buffers", "quantity": 10240, "unit": "bytes", "declaration_kind": "source-declared-allocation", "evidence_span_ids": ["source-span-000006"]},
            {"resource_id": "sympathetic-string-buffers", "label": "Sympathetic string buffers", "quantity": 16384, "unit": "bytes", "declaration_kind": "source-declared-allocation", "evidence_span_ids": ["source-span-000006"]},
            {"resource_id": "granular-record-buffer", "label": "Granular record buffer", "quantity": 192016, "unit": "bytes", "declaration_kind": "source-declared-allocation", "evidence_span_ids": ["source-span-000004"]},
            {"resource_id": "diffusion-reverb-buffer", "label": "Clouds diffusion reverb buffer", "quantity": 32768, "unit": "bytes", "declaration_kind": "source-declared-allocation", "evidence_span_ids": ["source-span-000004"]},
        ]
    else:
        specific = [
            _dependency("stage-mutation-scale-engine", "Stage, mutation, and scale engine", "private-helper", "Related catalog names do not establish the exact local state transition behavior.", "Exact state contract, graph nodes, and host vectors are absent.", "source-span-000004"),
            _dependency("event-scheduler", "Fixed delayed-event scheduler", "unsuitable-for-standalone-promotion", "The fixed scheduler is private machine coordination rather than a palette import requirement.", "Exact event timing/state contracts and real-time proof are absent.", "source-span-000005"),
            _dependency("voice-allocator", "Fixed quietest-voice allocator", "private-helper", "The source-local allocator owns 16 voices and is part of the machine closure.", "Exact voice state, stealing vectors, and graph representation are absent.", "source-span-000005"),
            _dependency("modal-voice-recipes", "Three-partial modal voice and recipes", "private-helper", "The modal recipe ratios, gains, decay, transients, and panning are one private synthesis closure.", "Exact component contracts and semantic vectors are absent.", "source-span-000003"),
            _dependency("braids-sine-table", "Braids sine resource table", "non-object", "The table is a linked source resource, not a selectable oscillator object.", "A content-addressed resource descriptor and license closure are absent.", "source-span-000003"),
            _dependency("panner-and-wake-mixer", "Panner and direct/wake stereo mixer", "private-helper", "Apparent mixer similarity is insufficient to establish the exact panning and wake behavior.", "Exact transfer vectors and graph contracts are absent.", "source-span-000004"),
            _dependency("custom-filter-and-drive", "Custom resonant filter and asymmetric drive", "private-helper", "Current selectable filter/gain objects are unproved analogues with different semantic commitments.", "Exact transfer/state vectors and component contracts are absent.", "source-span-000004"),
            _dependency("rational-limiter", "Rational x/(1+abs(x)) limiter", "private-helper", "The current selectable soft clip has different semantics and cannot be substituted.", "Exact component contract and host vector are absent.", "source-span-000004"),
            _dependency("stmlib-and-cpp", "stmlib and standard C/C++ facilities", "non-object", "These are source/toolchain dependencies, not catalog objects.", "Pinned resource/license and backend dependency descriptors are absent.", "source-span-000003"),
        ]
        resources = [
            {"resource_id": "event-pool", "label": "Fixed event pool", "quantity": 16, "unit": "items", "declaration_kind": "source-structure", "evidence_span_ids": ["source-span-000005"]},
            {"resource_id": "voice-pool", "label": "Fixed voice pool", "quantity": 16, "unit": "items", "declaration_kind": "source-structure", "evidence_span_ids": ["source-span-000005"]},
        ]
    aliases = (
        [{"input": "Pamulist", "disposition": "corrected-input-only", "correction": "Palimpsest"}]
        if not tide else []
    )
    return _record(
        {
            "schema_version": "machine-source-review-v0",
            "canonical_profile": "schuss-canonical-json-v1",
            "machine_source_review_id": f"schuss-machine-source-review-{number:06d}",
            "revision": 1,
            "inspection_state": "inspection-only",
            "source_identity": {
                "source_id": f"gills-instruments-{kind}",
                "repository_url": GILLS_SOURCE_URL,
                "commit": GILLS_SOURCE_COMMIT,
                "project_root": project_root,
                "files": files,
            },
            "asserted_identity": {"display_name": display_name, "summary": summary, "aliases": aliases},
            "legacy_patch_shell": {
                "format": "legacy-axp",
                "application_version": "1.0.12",
                "object_count": 24,
                "connection_count": 27,
                "object_instances": _patch_objects(wrapper, pot_names, "oscillator" if tide else "voice"),
                "configuration_facts": [
                    "Root initializes to MIDI note 60 and the encoder is bounded from 36 through 72.",
                    "Stereo headphone output is configured at -24 dB.",
                    "The display uses narrow font with scope disabled.",
                ],
                "evidence_span_ids": ["source-span-000001"],
            },
            "evidence_spans": spans,
            "source_blocks": blocks,
            "source_edges": edges,
            "panel_mappings": _panel_mappings(kind, "source-span-000004", "source-span-000005" if tide else "source-span-000006"),
            "dependency_assessments": shared + specific,
            "resource_declarations": resources,
            "evidence_levels": _levels("Exact source bytes, portable identity, panel mappings, dependencies, and explanatory structure pass local structural validation."),
        },
        schema,
    )


def _panel_regions() -> list[dict[str, Any]]:
    coordinates = {
        **{f"device-input-{index:06d}": (f"P{index} / performance pot {index}", f"pot-{index:02d}-region", f"highlight-pot-{index:02d}", (29.002 + 25 * ((index - 1) % 5), 58.242 + 25 * ((index - 1) // 5))) for index in range(1, 11)},
        "device-input-000011": ("S1 / button 1", "button-01-region", "highlight-button-01", (54.002, 42.242)),
        "device-input-000012": ("S2 / button 2", "button-02-region", "highlight-button-02", (79.002, 42.242)),
        "device-input-000013": ("S3 / button 3", "button-03-region", "highlight-button-03", (66.502, 70.742)),
        "device-input-000014": ("S4 / button 4", "button-04-region", "highlight-button-04", (91.502, 70.742)),
        "device-input-000015": ("ENC1 / encoder turn", "encoder-region", "highlight-encoder", (94.002, 34.142)),
        "device-input-000016": ("ENC1 / encoder push", "encoder-region", "highlight-encoder", (94.002, 34.142)),
        "device-input-000017": ("RV11 / input volume", "input-volume-region", "highlight-input-volume", (29.002, 33.242)),
        "device-input-000018": ("RV12 / output volume", "output-volume-region", "highlight-output-volume", (129.002, 33.242)),
        "device-feedback-000001": ("LED1", "led-01-region", "highlight-led-01", (113.460, 21.192)),
        "device-feedback-000002": ("LED2", "led-02-region", "highlight-led-02", (113.460, 29.192)),
        "device-feedback-000003": ("LED3 color A", "led-03-region", "highlight-led-03", (63.382, 54.422)),
        "device-feedback-000004": ("LED3 red", "led-03-region", "highlight-led-03", (63.382, 54.422)),
        "device-feedback-000005": ("LED4 color A", "led-04-region", "highlight-led-04", (88.410, 54.422)),
        "device-feedback-000006": ("LED4 red", "led-04-region", "highlight-led-04", (88.410, 54.422)),
        "device-display-000001": ("OLED text", "oled-region", "highlight-oled", (66.500, 19.890)),
        "device-display-000002": ("OLED graphics", "oled-region", "highlight-oled", (66.500, 19.890)),
    }
    gesture_controls = {
        **{index: 1 for index in range(1, 4)},
        **{index: 2 for index in range(4, 7)},
        **{index: 3 for index in range(7, 10)},
        **{index: 4 for index in range(10, 13)},
    }
    for index, button in gesture_controls.items():
        source = coordinates[f"device-input-{10 + button:06d}"]
        coordinates[f"device-gesture-{index:06d}"] = (f"S{button} gesture", source[1], source[2], source[3])
    for index in range(13, 17):
        source = coordinates["device-input-000015" if index == 13 else "device-input-000016"]
        coordinates[f"device-gesture-{index:06d}"] = ("ENC1 turn gesture" if index == 13 else "ENC1 switch gesture", source[1], source[2], source[3])
    regions = []
    for slot_id, (label, element, highlight, (x, y)) in sorted(coordinates.items()):
        slot_kind = (
            "input-control" if slot_id.startswith("device-input-")
            else "gesture" if slot_id.startswith("device-gesture-")
            else "feedback-output" if slot_id.startswith("device-feedback-")
            else "display"
        )
        regions.append(
            {
                "semantic_slot_id": slot_id,
                "slot_kind": slot_kind,
                "physical_label": label,
                "svg_element_id": element,
                "highlight_element_id": highlight,
                "anchor": {"x": f"{x:.3f}".rstrip("0").rstrip("."), "y": f"{y:.3f}".rstrip("0").rstrip(".")},
            }
        )
    if len(regions) != 42:
        raise ValueError("Gills panel semantic map must contain 42 represented slots")
    return regions


def _panel_layout(schema: dict[str, Any], device: dict[str, Any]) -> dict[str, Any]:
    return _record(
        {
            "schema_version": "panel-layout-v0",
            "canonical_profile": "schuss-canonical-json-v1",
            "panel_layout_id": "schuss-panel-layout-000001",
            "revision": 1,
            "device_profile_reference": _ref(device, "device_profile_id"),
            "asset": {
                "portable_path": "assets/gills/gills-panel-v06.svg",
                "byte_sha256": core.sha256_file(ASSET),
                "media_type": "image/svg+xml",
                "license": "CC-BY-4.0",
                "attribution": "Ksoloti Gills hardware design contributors.",
                "adaptation_notice": "Normalized Schuss technical silhouette derived from pinned v0.6 CAD and editable board SVG; not manufacturing artwork.",
            },
            "coordinate_system": {
                "origin": "upper-left-outer-bounds", "x_direction": "right", "y_direction": "down",
                "unit": "millimetres", "width": "158", "height": "100",
            },
            "semantic_regions": _panel_regions(),
            "excluded_slots": [
                {
                    "semantic_slot_id": "device-input-000019",
                    "slot_kind": "input-control",
                    "reason": "The accepted power-switch slot has no qualified front-panel performance anchor in the pinned top-panel source and is not used by the inspected instruments.",
                }
            ],
            "source_assets": [
                {"repository_url": PANEL_SOURCE_URL, "commit": PANEL_SOURCE_COMMIT, "portable_path": "ksoloti-gills_panel/ksoloti-gills_panel-brd.svg", "byte_sha256": "bd0c9b33298f5bfa91ee13939d96048882d5bd7c32ca99819781b9b8fd5ec833", "authority": "editable-layout-source", "license": "CC-BY-4.0"},
                {"repository_url": PANEL_SOURCE_URL, "commit": PANEL_SOURCE_COMMIT, "portable_path": "ksoloti-gills_panel/ksoloti-gills_panel.kicad_pcb", "byte_sha256": "348e22c25b7b54bd9db989c581408ed7429b9d7c2df65f19e8beb6a99b0368c4", "authority": "metric-cad-source", "license": "CC-BY-4.0"},
                {"repository_url": PANEL_SOURCE_URL, "commit": PANEL_SOURCE_COMMIT, "portable_path": "LICENSE", "byte_sha256": "9e5f1b3c610b9c2da5c313bf81d577a7d1acec686bdb0384edefa6df0f90cd94", "authority": "repository-license", "license": "CC-BY-4.0"},
            ],
            "visual_verification": {
                "reference_sha256": PHOTO_SHA256,
                "retention_state": "non-retained-visual-reference",
                "result": "strong-v06-topology-and-appearance-match",
                "limitations": [
                    "The oblique photograph is not metric geometry or serial-number evidence.",
                    "The OLED is unlit, so rendered display appearance is not evidenced.",
                    "The LEDs are unlit, so populated LED colors are not evidenced.",
                    "No photograph pixels are copied, embedded, or traced into the SVG.",
                ],
            },
            "evidence_levels": _levels("Pinned CAD, editable source SVG, exact anchors, deterministic SVG bytes, semantic slot coverage, and non-retained photo comparison pass local structural validation."),
        },
        schema,
    )


def _presentation(
    kind: str,
    schema: dict[str, Any],
    review: dict[str, Any],
    panel: dict[str, Any],
) -> dict[str, Any]:
    number = 2 if kind == "tide-pit" else 1
    blocks = []
    for index, source in enumerate(review["source_blocks"], 1):
        blocks.append(
            {
                "presentation_block_id": f"presentation-block-{index:06d}",
                "label": source["label"],
                "kind": source["kind"],
                "source_block_ids": [source["source_block_id"]],
                "graph_node_references": [],
                "geometry": {"x": 20 + (index - 1) * 190, "y": 42, "width": 160, "height": 88},
            }
        )
    edges = [
        {
            "presentation_edge_id": f"presentation-edge-{index:06d}",
            "source_block_id": f"presentation-block-{index:06d}",
            "destination_block_id": f"presentation-block-{index + 1:06d}",
            "signal_kind": edge["signal_kind"],
            "source_edge_ids": [edge["source_edge_id"]],
        }
        for index, edge in enumerate(review["source_edges"], 1)
    ]
    panel_links = []
    for mapping in review["panel_mappings"]:
        if mapping["mapping_state"] != "mapped":
            continue
        slot = mapping["semantic_slot_id"]
        block_index = len(blocks) if slot.startswith(("device-feedback-", "device-display-")) else 1
        panel_links.append(
            {
                "source_mapping_id": mapping["mapping_id"],
                "presentation_block_id": f"presentation-block-{block_index:06d}",
                "semantic_slot_id": slot,
                "modes": sorted({item["mode"] for item in mapping["meanings"]}),
            }
        )
    return _record(
        {
            "schema_version": "machine-presentation-v0",
            "canonical_profile": "schuss-canonical-json-v1",
            "machine_presentation_id": f"schuss-machine-presentation-{number:06d}",
            "revision": 1,
            "presentation_state": "inspection-only",
            "source_review_reference": _ref(review, "machine_source_review_id"),
            "panel_layout_reference": _ref(panel, "panel_layout_id"),
            "blocks": blocks,
            "edges": edges,
            "panel_links": panel_links,
        },
        schema,
    )


def generated() -> tuple[dict[str, bytes], bytes, dict[str, Any]]:
    schema_values = schemas()
    for version, schema in schema_values.items():
        annotations = core.validate_schema_annotations(schema)
        if annotations:
            raise ValueError(f"{version}: {annotations}")
    context = load_repository_context(record_set_path=PARENT)
    device = _find_exact(context, "devices", "device_profile_id", "schuss-device-profile-000001", 2)
    panel = _panel_layout(schema_values["panel-layout-v0"], device)
    palimpsest = _review("palimpsest", schema_values["machine-source-review-v0"], context)
    tide_pit = _review("tide-pit", schema_values["machine-source-review-v0"], context)
    palimpsest_presentation = _presentation("palimpsest", schema_values["machine-presentation-v0"], palimpsest, panel)
    tide_pit_presentation = _presentation("tide-pit", schema_values["machine-presentation-v0"], tide_pit, panel)

    files: dict[str, bytes] = {
        SCHEMA_PATHS[version]: _json_bytes(value)
        for version, value in schema_values.items()
    }
    records = (
        ("panel-layout", panel, PANEL_PATH, "panel_layout_id"),
        ("machine-source-review", palimpsest, SOURCE_REVIEW_PATHS["palimpsest"], "machine_source_review_id"),
        ("machine-source-review", tide_pit, SOURCE_REVIEW_PATHS["tide-pit"], "machine_source_review_id"),
        ("machine-presentation", palimpsest_presentation, PRESENTATION_PATHS["palimpsest"], "machine_presentation_id"),
        ("machine-presentation", tide_pit_presentation, PRESENTATION_PATHS["tide-pit"], "machine_presentation_id"),
    )
    for _, value, path, _ in records:
        files[path] = _json_bytes(value)

    parent = core.load_json(PARENT)
    schema_members = copy.deepcopy(parent["schema_members"])
    for version, path in SCHEMA_PATHS.items():
        schema_members.append({"schema_version": version, "portable_path": path, "byte_sha256": _sha256_bytes(files[path])})
    record_members = copy.deepcopy(parent["record_members"])
    for kind, value, path, id_field in records:
        record_members.append(
            {
                "record_kind": kind,
                "stable_id": value[id_field],
                "revision": value["revision"],
                "content_hash": value["content_hash"],
                "portable_path": path,
                "byte_sha256": _sha256_bytes(files[path]),
            }
        )
    manifest_schema = core.load_json(ROOT / "schemas/prerequisite/record-set-v0.schema.json")
    manifest = _record(
        {
            "schema_version": "record-set-v0",
            "canonical_profile": "schuss-canonical-json-v1",
            "record_set_id": "schuss-record-set-000022",
            "revision": 1,
            "purpose": "prospective-task",
            "parent_reference": {
                "status": "included",
                "record_set_id": parent["record_set_id"],
                "revision": parent["revision"],
                "content_hash": parent["content_hash"],
            },
            "schema_members": schema_members,
            "record_members": record_members,
            "enforced_directories": [*parent["enforced_directories"], TASK_ROOT],
        },
        manifest_schema,
    )
    summary = {
        "record_set_reference": _ref(manifest, "record_set_id"),
        "machine_record_count": 0,
        "source_review_count": 2,
        "presentation_count": 2,
        "panel_layout_count": 1,
        "accepted_palette_count": 20,
        "tide_pit_source_declared_sdram_bytes": sum(
            item["quantity"] for item in tide_pit["resource_declarations"] if item["unit"] == "bytes"
        ),
        "evidence_levels": ["passed", *(["not-run"] * 7)],
    }
    return files, _json_bytes(manifest), summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files, manifest, summary = generated()
    expected = {**files, OUTPUT.relative_to(ROOT).as_posix(): manifest}
    if args.check:
        stale = [path for path, data in expected.items() if not (ROOT / path).is_file() or (ROOT / path).read_bytes() != data]
        if stale:
            raise SystemExit("stale Task 029 generated artifacts: " + ", ".join(sorted(stale)))
    else:
        for path, data in expected.items():
            target = ROOT / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    print(core.canonical_json(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
