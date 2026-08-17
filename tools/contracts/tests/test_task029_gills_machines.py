from __future__ import annotations

import copy
from dataclasses import replace
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools/contracts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from packages.schuss_core import application_capabilities as application
from packages.schuss_core.control_plane import (
    canonical_result_bytes,
    dispatch_operation,
    load_repository_context,
)

import generate_task029_records as generator
import generate_task029_viewer_fixtures as fixture_generator
import machine_rules
import validator_core as core


RECORD_SET = ROOT / "contracts/record-sets/task029-gills-machines-v1.json"
PARENT_SET = ROOT / "contracts/record-sets/task028-direct-palette-v1.json"
SCHEMA_PATHS = tuple(
    ROOT / "schemas" / name
    for name in (
        "application-capability-description-v2.schema.json",
        "machine-presentation-v0.schema.json",
        "machine-source-review-v0.schema.json",
        "machine-v0.schema.json",
        "operation-request-v9.schema.json",
        "operation-result-v9.schema.json",
        "panel-layout-v0.schema.json",
    )
)


def exact(values, field: str, identifier: str, revision: int = 1):
    matches = [
        value
        for value in values
        if value[field] == identifier and value["revision"] == revision
    ]
    if len(matches) != 1:
        raise AssertionError(f"{identifier}@{revision} did not resolve exactly")
    return matches[0]


def inspect_request(review: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": "schuss-operation-request-v9",
        "canonical_profile": "schuss-canonical-json-v1",
        "operation": "machine.inspect",
        "payload": {
            "source_review_reference": {
                key: review[key]
                for key in (
                    "machine_source_review_id",
                    "revision",
                    "content_hash",
                )
            }
        },
    }


class Task029GillsMachinesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = load_repository_context(record_set_path=RECORD_SET)
        cls.parent = load_repository_context(record_set_path=PARENT_SET)
        cls.reviews = {
            value["asserted_identity"]["display_name"]: value
            for value in cls.context.records["machine_source_reviews"]
        }
        cls.presentations = {
            value["machine_presentation_id"]: value
            for value in cls.context.records["machine_presentations"]
        }
        cls.panel = exact(
            cls.context.records["panel_layouts"],
            "panel_layout_id",
            "schuss-panel-layout-000001",
        )

    def test_exact_parent_and_layer_counts(self):
        manifest = core.load_json(RECORD_SET)
        parent = core.load_json(PARENT_SET)
        self.assertEqual("schuss-record-set-000022", manifest["record_set_id"])
        self.assertEqual(
            {
                "status": "included",
                **{
                    key: parent[key]
                    for key in ("record_set_id", "revision", "content_hash")
                },
            },
            manifest["parent_reference"],
        )
        self.assertEqual(len(parent["record_members"]) + 5, len(manifest["record_members"]))
        self.assertEqual(len(parent["schema_members"]) + 7, len(manifest["schema_members"]))
        self.assertEqual(
            {
                "machine_source_reviews": 2,
                "panel_layouts": 1,
                "machine_presentations": 2,
                "machines": 0,
            },
            self.context.machine_summary["record_counts"],
        )
        self.assertEqual("valid", self.context.machine_summary["status"])
        self.assertEqual(2, self.context.machine_summary["inspection_candidate_count"])
        self.assertEqual(0, self.context.machine_summary["accepted_machine_count"])
        self.assertEqual(0, self.context.machine_summary["palette_mutation_count"])

    def test_reference_machine_names_locations_and_exact_files(self):
        self.assertEqual({"Palimpsest", "Tide Pit"}, set(self.reviews))
        palimpsest = self.reviews["Palimpsest"]
        tide_pit = self.reviews["Tide Pit"]
        self.assertEqual("projects/palimpsest-gills", palimpsest["source_identity"]["project_root"])
        self.assertEqual("projects/tide-pit-gills", tide_pit["source_identity"]["project_root"])
        self.assertEqual(
            "53287e49e5bcc5fb0d73b546d88431f82467f969",
            palimpsest["source_identity"]["commit"],
        )
        self.assertEqual(
            palimpsest["source_identity"]["commit"],
            tide_pit["source_identity"]["commit"],
        )
        self.assertEqual(
            [{"input": "Pamulist", "disposition": "corrected-input-only", "correction": "Palimpsest"}],
            palimpsest["asserted_identity"]["aliases"],
        )
        self.assertEqual([], tide_pit["asserted_identity"]["aliases"])
        self.assertEqual(
            {
                "projects/palimpsest-gills/LICENSE.md",
                "projects/palimpsest-gills/README.md",
                "projects/palimpsest-gills/palimpsest-gills.axp",
                "projects/palimpsest-gills/palimpsest.axo",
                "projects/palimpsest-gills/palimpsest_dsp.h",
            },
            {item["portable_path"] for item in palimpsest["source_identity"]["files"]},
        )
        self.assertEqual(
            {
                "projects/tide-pit-gills/LICENSE.md",
                "projects/tide-pit-gills/README.md",
                "projects/tide-pit-gills/tidepit-gills.axp",
                "projects/tide-pit-gills/tidepit.axo",
                "projects/tide-pit-gills/tidepit_dsp.h",
                "projects/tide-pit-gills/tidepit_voice.h",
            },
            {item["portable_path"] for item in tide_pit["source_identity"]["files"]},
        )
        for name, review in self.reviews.items():
            shell = review["legacy_patch_shell"]
            with self.subTest(name=name):
                self.assertEqual(24, shell["object_count"])
                self.assertEqual(24, len(shell["object_instances"]))
                self.assertEqual(27, shell["connection_count"])
                self.assertEqual(10, sum(item["legacy_type"] == "ksoloti/gills/pot p" for item in shell["object_instances"]))
                self.assertEqual(4, sum(item["legacy_type"] == "ksoloti/gills/button" for item in shell["object_instances"]))
                self.assertIn("ksoloti/gills/encoder", {item["legacy_type"] for item in shell["object_instances"]})
                self.assertIn("ksoloti/gills/display", {item["legacy_type"] for item in shell["object_instances"]})

    def test_source_block_diagrams_are_explanatory_not_graph_claims(self):
        expected_labels = {
            "Palimpsest": (
                "Four-stage mutation engine",
                "Direct strike and trace events",
                "Fixed event scheduler",
                "Fixed modal voice pool",
                "Braids sine modal synthesis",
                "Direct and wake stereo mix",
                "CLEAN, FILT, or DRIVE",
                "Rational limiter and stereo output",
                "Gills feedback and OLED",
            ),
            "Tide Pit": (
                "Four-stage mutation engine",
                "Selectable excitation",
                "Sympathetic string and energy",
                "Eight-mode stereo body",
                "Granular record and six-grain engine",
                "Dry/wet and diffusion tail",
                "CLEAN, FILT, or DRIVE",
                "Soft clip and stereo output",
                "Gills feedback and OLED",
            ),
        }
        for name, review in self.reviews.items():
            with self.subTest(name=name):
                self.assertEqual(expected_labels[name], tuple(item["label"] for item in review["source_blocks"]))
                presentation = next(
                    value
                    for value in self.presentations.values()
                    if value["source_review_reference"]["machine_source_review_id"]
                    == review["machine_source_review_id"]
                )
                self.assertEqual("inspection-only", presentation["presentation_state"])
                self.assertTrue(all(not item["graph_node_references"] for item in presentation["blocks"]))
                self.assertEqual(len(review["source_blocks"]), len(presentation["blocks"]))
                self.assertEqual(len(review["source_edges"]), len(presentation["edges"]))

    def test_panel_asset_and_semantic_map_are_exact_and_separate(self):
        self.assertEqual(42, len(self.panel["semantic_regions"]))
        self.assertEqual(
            [{
                "semantic_slot_id": "device-input-000019",
                "slot_kind": "input-control",
                "reason": "The accepted power-switch slot has no qualified front-panel performance anchor in the pinned top-panel source and is not used by the inspected instruments.",
            }],
            self.panel["excluded_slots"],
        )
        self.assertEqual("assets/gills/gills-panel-v06.svg", self.panel["asset"]["portable_path"])
        self.assertEqual("CC-BY-4.0", self.panel["asset"]["license"])
        asset = ROOT / self.panel["asset"]["portable_path"]
        self.assertEqual(self.panel["asset"]["byte_sha256"], core.sha256_file(asset))
        self.assertEqual({"width": "158", "height": "100", "unit": "millimetres", "origin": "upper-left-outer-bounds", "x_direction": "right", "y_direction": "down"}, self.panel["coordinate_system"])
        by_slot = {item["semantic_slot_id"]: item for item in self.panel["semantic_regions"]}
        self.assertEqual(by_slot["device-display-000001"]["svg_element_id"], by_slot["device-display-000002"]["svg_element_id"])
        self.assertEqual(by_slot["device-feedback-000003"]["svg_element_id"], by_slot["device-feedback-000004"]["svg_element_id"])
        self.assertEqual(by_slot["device-feedback-000005"]["svg_element_id"], by_slot["device-feedback-000006"]["svg_element_id"])
        self.assertEqual("non-retained-visual-reference", self.panel["visual_verification"]["retention_state"])

        invalid_panel = copy.deepcopy(self.panel)
        graphics = next(
            item
            for item in invalid_panel["semantic_regions"]
            if item["semantic_slot_id"] == "device-display-000002"
        )
        graphics["svg_element_id"] = "led-01-region"
        graphics["highlight_element_id"] = "highlight-led-01"
        invalid_panel["content_hash"] = core.record_content_hash(
            invalid_panel, self.context.schemas["panel_layout"]
        )
        invalid = machine_rules.validate_values(
            {
                "machine_source_reviews": list(self.context.records["machine_source_reviews"]),
                "panel_layouts": [invalid_panel],
                "machine_presentations": list(self.context.records["machine_presentations"]),
                "machines": [],
            },
            {
                group: self.context.schemas[key]
                for group, key in (
                    ("machine_source_reviews", "machine_source_review"),
                    ("panel_layouts", "panel_layout"),
                    ("machine_presentations", "machine_presentation"),
                    ("machines", "machine"),
                )
            },
            {key: list(value) for key, value in self.context.records.items()},
            ROOT,
        )
        self.assertIn(
            "MACHINE_PANEL_SHARED_ANCHOR_INVALID",
            {item["code"] for item in invalid["diagnostics"]},
        )

    def test_all_controls_feedback_and_display_capabilities_are_accounted_for(self):
        expected_slots = machine_rules.EXPECTED_REVIEW_SLOTS
        for name, review in self.reviews.items():
            mappings = {item["semantic_slot_id"]: item for item in review["panel_mappings"]}
            with self.subTest(name=name):
                self.assertEqual(34, len(mappings))
                self.assertEqual(expected_slots, set(mappings))
                self.assertEqual("intentionally-unmapped", mappings["device-feedback-000004"]["mapping_state"])
                self.assertEqual("intentionally-unmapped", mappings["device-feedback-000006"]["mapping_state"])
                self.assertEqual("intentionally-unmapped", mappings["device-display-000002"]["mapping_state"])
        self.assertEqual(
            "intentionally-unmapped",
            {item["semantic_slot_id"]: item for item in self.reviews["Palimpsest"]["panel_mappings"]}["device-gesture-000016"]["mapping_state"],
        )
        self.assertEqual(
            "mapped",
            {item["semantic_slot_id"]: item for item in self.reviews["Tide Pit"]["panel_mappings"]}["device-gesture-000016"]["mapping_state"],
        )

    def test_dependencies_preserve_support_classes_and_tide_pit_resource_boundary(self):
        allowed = {
            "accepted-support",
            "catalogued-only",
            "observed-only",
            "absent",
            "private-helper",
            "non-object",
            "unsuitable-for-standalone-promotion",
            "unsupported",
        }
        for review in self.reviews.values():
            self.assertTrue({item["classification"] for item in review["dependency_assessments"]} <= allowed)
        tide = self.reviews["Tide Pit"]
        self.assertEqual(
            251408,
            sum(item["quantity"] for item in tide["resource_declarations"] if item["unit"] == "bytes"),
        )
        dependencies = {item["dependency_id"]: item for item in tide["dependency_assessments"]}
        self.assertEqual("catalogued-only", dependencies["clouds-granular-engine"]["classification"])
        self.assertEqual("private-helper", dependencies["clouds-diffusion-tail"]["classification"])
        self.assertFalse(dependencies["rings-reverb-non-dependency"]["required"])
        self.assertEqual("unsupported", dependencies["rings-reverb-non-dependency"]["classification"])

    def test_parent_palette_is_byte_for_byte_unchanged(self):
        current = exact(
            self.context.records["selection_packets"],
            "selection_packet_id",
            "schuss-core-selection-000003",
        )
        parent = exact(
            self.parent.records["selection_packets"],
            "selection_packet_id",
            "schuss-core-selection-000003",
        )
        self.assertEqual(parent, current)
        self.assertEqual(20, current["final_safe_selectable_total"])

    def test_machine_inspection_is_read_only_deterministic_and_fixture_exact(self):
        fixture_names = {
            "Palimpsest": "palimpsest-machine-inspect.json",
            "Tide Pit": "tide-pit-machine-inspect.json",
        }
        for name, review in self.reviews.items():
            request = inspect_request(review)
            first = dispatch_operation(copy.deepcopy(request), self.context)
            second = dispatch_operation(copy.deepcopy(request), self.context)
            self.assertEqual("success", first["status"])
            self.assertEqual(first, second)
            self.assertEqual("source-review", first["value"]["entry_kind"])
            self.assertEqual("inspection-only", first["value"]["inspection_state"])
            self.assertEqual(len(review["source_blocks"]), len(first["value"]["source_evidence"]["blocks"]))
            self.assertEqual(len(review["source_edges"]), len(first["value"]["source_evidence"]["edges"]))
            self.assertEqual(review["evidence_spans"], first["value"]["source_evidence"]["spans"])
            self.assertEqual(
                {"inspect": True, "build": False, "deploy": False, "edit": False, "play": False, "promote": False},
                first["value"]["affordances"],
            )
            expected = (ROOT / "apps/schuss_machine_viewer/fixtures" / fixture_names[name]).read_bytes()
            self.assertEqual(expected, canonical_result_bytes(first, self.context) + b"\n")

    def test_v9_fails_closed_on_malformed_stale_and_absent_machine_references(self):
        malformed = {
            "schema_version": "schuss-operation-request-v9",
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": "machine.inspect",
            "payload": {},
        }
        stale = inspect_request(self.reviews["Palimpsest"])
        stale["payload"]["source_review_reference"]["content_hash"] = "sha256:" + "0" * 64
        absent = {
            "schema_version": "schuss-operation-request-v9",
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": "machine.inspect",
            "payload": {
                "machine_reference": {
                    "machine_id": "schuss-machine-000001",
                    "revision": 1,
                    "content_hash": "sha256:" + "0" * 64,
                }
            },
        }
        expected = (
            (malformed, "OPERATION_REQUEST_INVALID"),
            (stale, "MACHINE_INSPECTION_REFERENCE_UNRESOLVED"),
            (absent, "MACHINE_INSPECTION_REFERENCE_UNRESOLVED"),
        )
        for request, code in expected:
            result = dispatch_operation(request, self.context)
            self.assertEqual("invalid", result["status"])
            self.assertEqual(code, result["diagnostics"][0]["code"])
            canonical_result_bytes(result, self.context)

        invalid_context = replace(
            self.context,
            machine_summary={
                **self.context.machine_summary,
                "status": "invalid",
                "diagnostics": [
                    {
                        "code": "SYNTHETIC_MACHINE_LAYER_INVALID",
                        "severity": "error",
                        "subject": "fixture",
                        "location": "$",
                        "message": "synthetic negative fixture",
                    }
                ],
            },
        )
        invalid_layer = dispatch_operation(
            inspect_request(self.reviews["Palimpsest"]), invalid_context
        )
        self.assertEqual("invalid", invalid_layer["status"])
        self.assertEqual("MACHINE_LAYER_INVALID", invalid_layer["diagnostics"][0]["code"])

    def test_completed_machine_requires_exact_graph_presentation_and_dependency_closure(self):
        review = self.reviews["Palimpsest"]
        presentation = exact(
            self.context.records["machine_presentations"],
            "machine_presentation_id",
            "schuss-machine-presentation-000001",
        )
        instrument = exact(
            self.context.records["instruments"],
            "instrument_id",
            "schuss-instrument-000002",
            3,
        )
        machine = {
            "schema_version": "machine-v0",
            "canonical_profile": "schuss-canonical-json-v1",
            "machine_id": "schuss-machine-000001",
            "revision": 1,
            "content_hash": "sha256:" + "0" * 64,
            "display_name": "Invalid Palimpsest closure",
            "summary": "Synthetic negative fixture.",
            "instrument_reference": {
                key: instrument[key]
                for key in ("instrument_id", "revision", "content_hash")
            },
            "source_review_reference": {
                key: review[key]
                for key in ("machine_source_review_id", "revision", "content_hash")
            },
            "presentation_reference": {
                key: presentation[key]
                for key in ("machine_presentation_id", "revision", "content_hash")
            },
        }
        machine["content_hash"] = core.record_content_hash(
            machine, self.context.schemas["machine"]
        )
        groups = {
            "machine_source_reviews": list(self.context.records["machine_source_reviews"]),
            "panel_layouts": list(self.context.records["panel_layouts"]),
            "machine_presentations": list(self.context.records["machine_presentations"]),
            "machines": [machine],
        }
        summary = machine_rules.validate_values(
            groups,
            {
                group: self.context.schemas[key]
                for group, key in (
                    ("machine_source_reviews", "machine_source_review"),
                    ("panel_layouts", "panel_layout"),
                    ("machine_presentations", "machine_presentation"),
                    ("machines", "machine"),
                )
            },
            {key: list(value) for key, value in self.context.records.items()},
            ROOT,
        )
        codes = {item["code"] for item in summary["diagnostics"]}
        self.assertEqual("invalid", summary["status"])
        self.assertIn("MACHINE_PRESENTATION_CLOSURE_INVALID", codes)
        self.assertIn("MACHINE_REQUIRED_DEPENDENCY_UNRESOLVED", codes)

        completed_presentation = copy.deepcopy(presentation)
        completed_presentation["presentation_state"] = "machine-complete"
        graph_reference = {
            key: instrument["graph_reference"][key]
            for key in ("graph_id", "revision", "content_hash")
        }
        for block in completed_presentation["blocks"]:
            block["graph_node_references"] = [
                {**graph_reference, "node_id": "graph-node-999999"}
            ]
        completed_presentation["content_hash"] = core.record_content_hash(
            completed_presentation,
            self.context.schemas["machine_presentation"],
        )
        machine["presentation_reference"] = {
            key: completed_presentation[key]
            for key in ("machine_presentation_id", "revision", "content_hash")
        }
        machine["content_hash"] = core.record_content_hash(
            machine, self.context.schemas["machine"]
        )
        groups["machine_presentations"] = [
            completed_presentation
            if item["machine_presentation_id"]
            == completed_presentation["machine_presentation_id"]
            else item
            for item in self.context.records["machine_presentations"]
        ]
        groups["machines"] = [machine]
        unresolved_nodes = machine_rules.validate_values(
            groups,
            {
                group: self.context.schemas[key]
                for group, key in (
                    ("machine_source_reviews", "machine_source_review"),
                    ("panel_layouts", "panel_layout"),
                    ("machine_presentations", "machine_presentation"),
                    ("machines", "machine"),
                )
            },
            {key: list(value) for key, value in self.context.records.items()},
            ROOT,
        )
        unresolved_codes = {item["code"] for item in unresolved_nodes["diagnostics"]}
        self.assertIn("MACHINE_PRESENTATION_GRAPH_NODE_UNRESOLVED", unresolved_codes)
        self.assertIn("MACHINE_PRESENTATION_GRAPH_NODE_DUPLICATE", unresolved_codes)

    def test_application_registry_and_additive_schemas_are_exact(self):
        for path in SCHEMA_PATHS:
            schema = core.load_json(path)
            self.assertEqual([], core.validate_schema_annotations(schema), path.name)
        request = {
            "schema_version": "schuss-operation-request-v7",
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": "application.describe",
            "payload": {"scope": "selected-context"},
        }
        result = dispatch_operation(request, self.context)
        self.assertEqual("success", result["status"])
        self.assertEqual("application-capability-description-v2", result["value"]["schema_version"])
        names = [item["operation"] for item in result["value"]["operations"]]
        self.assertEqual(list(application.EXPECTED_OPERATIONS_V2), names)
        self.assertEqual(19, len(names))
        machine = next(item for item in result["value"]["operations"] if item["operation"] == "machine.inspect")
        self.assertEqual("read-only", machine["effect_class"])
        self.assertEqual("available", machine["availability"])

    def test_generated_records_and_viewer_fixtures_are_fresh(self):
        files, manifest, first_summary = generator.generated()
        _, second_manifest, second_summary = generator.generated()
        self.assertEqual(manifest, second_manifest)
        self.assertEqual(first_summary, second_summary)
        for path, expected in files.items():
            self.assertEqual(expected, (ROOT / path).read_bytes(), path)
        self.assertEqual(manifest, RECORD_SET.read_bytes())
        for path, expected in fixture_generator.generated().items():
            self.assertEqual(expected, path.read_bytes(), path)
        requests = json.loads((ROOT / "tools/contracts/tests/fixtures/task029-machine-operation-requests.json").read_text(encoding="utf-8"))
        self.assertEqual(2, len(requests))

    def test_completion_evidence_matches_exact_boundary(self):
        evidence_root = ROOT / "evidence/task029-completion-v1"
        validation = core.load_json(evidence_root / "validation-summary.json")
        matrix = core.load_json(evidence_root / "acceptance-matrix.json")
        prerequisites = core.load_json(evidence_root / "remaining-prerequisites.json")
        self.assertEqual(self.context.record_set_reference, validation["record_set_reference"])
        self.assertEqual(self.context.record_set_reference, matrix["record_set_reference"])
        self.assertEqual(0, validation["accepted_machine_count"])
        self.assertEqual(20, validation["accepted_palette_count"])
        self.assertEqual(["passed"] + ["not-run"] * 7, [item["status"] for item in validation["evidence_levels"]])
        self.assertEqual([], prerequisites["catalog_policy"]["automatic_promotions"])
        self.assertEqual("inspection-only", prerequisites["palimpsest"]["state"])
        self.assertEqual("inspection-only", prerequisites["tide_pit"]["state"])


if __name__ == "__main__":
    unittest.main()
