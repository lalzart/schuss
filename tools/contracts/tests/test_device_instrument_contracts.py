import copy
import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

from tools.validation.profile import requires_profile


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools/contracts"
SPEC = importlib.util.spec_from_file_location(
    "validate_device_instrument_contracts",
    TOOLS / "validate_device_instrument_contracts.py",
)
VALIDATOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = VALIDATOR
SPEC.loader.exec_module(VALIDATOR)

SCHEMA_ROOT = ROOT / "schemas"
CONTRACT_ROOT = ROOT / "contracts"
FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures/negative-fixtures.json"


def _pointer_tokens(pointer):
    if not pointer.startswith("/"):
        raise ValueError(f"invalid JSON pointer {pointer!r}")
    return [token.replace("~1", "/").replace("~0", "~") for token in pointer[1:].split("/")]


def _resolve_parent(value, pointer):
    tokens = _pointer_tokens(pointer)
    parent = value
    for token in tokens[:-1]:
        parent = parent[int(token)] if isinstance(parent, list) else parent[token]
    final = tokens[-1]
    return parent, int(final) if isinstance(parent, list) else final


def _get_pointer(value, pointer):
    parent, final = _resolve_parent(value, pointer)
    return parent[final]


def _apply_mutation(value, mutation):
    operation = mutation["operation"]
    if operation in {"add", "replace"}:
        parent, final = _resolve_parent(value, mutation["pointer"])
        parent[final] = copy.deepcopy(mutation["value"])
    elif operation == "remove":
        parent, final = _resolve_parent(value, mutation["pointer"])
        del parent[final]
    elif operation == "duplicate-item":
        item = copy.deepcopy(_get_pointer(value, mutation["pointer"]))
        id_parent, id_final = _resolve_parent(item, mutation["id_pointer"])
        id_parent[id_final] = mutation["id_value"]
        parent, _ = _resolve_parent(value, mutation["pointer"])
        parent.append(item)
    else:
        raise ValueError(f"unsupported fixture mutation {operation!r}")


class DeviceInstrumentContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.device_schema = VALIDATOR.load_json(SCHEMA_ROOT / VALIDATOR.DEVICE_SCHEMA_NAME)
        cls.instrument_schema = VALIDATOR.load_json(
            SCHEMA_ROOT / VALIDATOR.INSTRUMENT_SCHEMA_NAME
        )
        cls.device = VALIDATOR.load_json(
            CONTRACT_ROOT / "device-profiles/gills-minimal-v0.json"
        )
        cls.instrument = VALIDATOR.load_json(
            CONTRACT_ROOT / "instruments/blend-reference-v0.json"
        )
        cls.negative_fixtures = VALIDATOR.load_json(FIXTURE_PATH)

    def validate(self, device=None, instrument=None, extra_devices=None, extra_instruments=None):
        devices = [copy.deepcopy(self.device if device is None else device)]
        instruments = [copy.deepcopy(self.instrument if instrument is None else instrument)]
        devices.extend(copy.deepcopy(extra_devices or []))
        instruments.extend(copy.deepcopy(extra_instruments or []))
        return VALIDATOR.validate_contract_values(
            devices,
            instruments,
            self.device_schema,
            self.instrument_schema,
        )

    def rehash(self, device, instrument, target):
        if target == "device":
            device["content_hash"] = VALIDATOR.record_content_hash(device, self.device_schema)
            instrument["device_profile_reference"]["content_hash"] = device["content_hash"]
        instrument["content_hash"] = VALIDATOR.record_content_hash(
            instrument, self.instrument_schema
        )

    def test_valid_minimal_pair_and_deferred_evidence_boundary(self):
        summary = self.validate()
        self.assertEqual("valid-with-deferred-graph", summary["status"])
        self.assertEqual(1, summary["reference_resolution"]["device_profiles_resolved"])
        self.assertEqual(1, summary["reference_resolution"]["graphs_deferred"])
        self.assertEqual(0, summary["reference_resolution"]["graphs_resolved"])
        self.assertEqual([], summary["diagnostics"])
        levels = {item["level"]: item["status"] for item in summary["evidence_levels"]}
        self.assertEqual("passed", levels["structural-schema"])
        self.assertEqual("deferred", levels["component-graph-resolution"])
        self.assertTrue(all(levels[name] == "not-run" for name in (
            "backend-lowering",
            "artifact-generation",
            "arm-compile-link",
            "connected-device",
            "real-time-resource",
            "audible-listening",
        )))

    def test_hash_round_trip_and_nested_reference_hash_is_not_omitted(self):
        self.assertEqual(
            self.device["content_hash"],
            VALIDATOR.record_content_hash(self.device, self.device_schema),
        )
        self.assertEqual(
            self.instrument["content_hash"],
            VALIDATOR.record_content_hash(self.instrument, self.instrument_schema),
        )
        changed = copy.deepcopy(self.instrument)
        changed["device_profile_reference"]["content_hash"] = "sha256:" + "f" * 64
        self.assertNotEqual(
            VALIDATOR.canonical_record_bytes(self.instrument, self.instrument_schema),
            VALIDATOR.canonical_record_bytes(changed, self.instrument_schema),
        )

    @requires_profile("reproduction")
    def test_two_fresh_processes_emit_identical_summary_and_canonical_bytes(self):
        validation_command = [
            sys.executable,
            str(TOOLS / "validate_device_instrument_contracts.py"),
            str(CONTRACT_ROOT),
            "--schema-root",
            str(SCHEMA_ROOT),
        ]
        first_summary = subprocess.check_output(validation_command)
        second_summary = subprocess.check_output(validation_command)
        self.assertEqual(first_summary, second_summary)

        for record_kind, path in (
            ("device-profile", CONTRACT_ROOT / "device-profiles/gills-minimal-v0.json"),
            ("instrument", CONTRACT_ROOT / "instruments/blend-reference-v0.json"),
        ):
            command = [
                sys.executable,
                str(TOOLS / "validate_device_instrument_contracts.py"),
                "--schema-root",
                str(SCHEMA_ROOT),
                "--canonical-record",
                str(path),
                "--record-kind",
                record_kind,
            ]
            self.assertEqual(subprocess.check_output(command), subprocess.check_output(command))

    def test_set_reordering_is_hash_invariant_and_sequence_reordering_is_rejected(self):
        first = copy.deepcopy(self.instrument)
        first["actions"] = [
            {
                "facet_id": "instrument-action-000002",
                "display_label": "Second",
                "payload_kind": "none",
            },
            {
                "facet_id": "instrument-action-000001",
                "display_label": "First",
                "payload_kind": "none",
            },
        ]
        second = copy.deepcopy(first)
        second["actions"].reverse()
        self.assertEqual(
            VALIDATOR.canonical_record_bytes(first, self.instrument_schema),
            VALIDATOR.canonical_record_bytes(second, self.instrument_schema),
        )

        reversed_points = copy.deepcopy(self.instrument)
        reversed_points["device_input_mappings"][0]["transform"]["points"].reverse()
        self.assertNotEqual(
            VALIDATOR.canonical_record_bytes(self.instrument, self.instrument_schema),
            VALIDATOR.canonical_record_bytes(reversed_points, self.instrument_schema),
        )
        reversed_points["content_hash"] = VALIDATOR.record_content_hash(
            reversed_points, self.instrument_schema
        )
        codes = {item["code"] for item in self.validate(instrument=reversed_points)["diagnostics"]}
        self.assertIn("MAPPING_TRANSFORM_INCOMPATIBLE", codes)

    def test_label_change_keeps_identity_but_requires_revision_and_hash(self):
        changed = copy.deepcopy(self.instrument)
        changed["display_name"] = "Renamed blend reference"
        self.assertEqual(self.instrument["instrument_id"], changed["instrument_id"])
        changed["content_hash"] = VALIDATOR.record_content_hash(changed, self.instrument_schema)
        collision = self.validate(extra_instruments=[changed])
        self.assertIn("ID_REVISION_COLLISION", {item["code"] for item in collision["diagnostics"]})

        changed["revision"] = 2
        changed["content_hash"] = VALIDATOR.record_content_hash(changed, self.instrument_schema)
        summary = self.validate(extra_instruments=[changed])
        self.assertEqual("valid-with-deferred-graph", summary["status"])

    def test_exact_device_reference_rejects_stale_hash(self):
        changed = copy.deepcopy(self.instrument)
        changed["device_profile_reference"]["content_hash"] = "sha256:" + "a" * 64
        changed["content_hash"] = VALIDATOR.record_content_hash(changed, self.instrument_schema)
        codes = {item["code"] for item in self.validate(instrument=changed)["diagnostics"]}
        self.assertIn("DEVICE_REFERENCE_UNRESOLVED", codes)

    def test_nonportable_numbers_fail_closed(self):
        changed = copy.deepcopy(self.instrument)
        changed["revision"] = 1.5
        summary = self.validate(instrument=changed)
        self.assertIn("NONPORTABLE_NUMBER", {item["code"] for item in summary["diagnostics"]})

    def test_schema_arrays_are_explicit_sets_or_sequences_and_objects_are_closed(self):
        self.assertEqual([], VALIDATOR.validate_schema_annotations(self.device_schema))
        self.assertEqual([], VALIDATOR.validate_schema_annotations(self.instrument_schema))

    def test_distinct_optional_slot_facet_and_mapping_kinds_validate_without_layer_collapse(self):
        device = copy.deepcopy(self.device)
        instrument = copy.deepcopy(self.instrument)
        fact = device["unresolved_facts"][0]
        unresolved = {
            "status": "unresolved",
            "unresolved_fact_id": fact["fact_id"],
        }
        device["input_controls"].append(
            {
                "slot_id": "device-input-000002",
                "display_label": "Reference button",
                "control_kind": "discrete",
                "physical_form": "button",
                "output_domain": "binary-state",
                "logical_range": {"minimum": "0", "maximum": "1", "unit": "boolean"},
                "physical_range": copy.deepcopy(unresolved),
                "resolution": copy.deepcopy(unresolved),
            }
        )
        device["input_controls"].append(
            {
                "slot_id": "device-input-000003",
                "display_label": "Reference encoder",
                "control_kind": "relative",
                "physical_form": "encoder",
                "output_domain": "relative-step",
                "logical_range": {"minimum": "-1", "maximum": "1", "unit": "steps"},
                "physical_range": copy.deepcopy(unresolved),
                "resolution": copy.deepcopy(unresolved),
            }
        )
        device["gestures"].append(
            {
                "gesture_id": "device-gesture-000001",
                "display_label": "Reference press",
                "gesture_kind": "press",
                "source_control_ids": ["device-input-000002"],
                "recognition": copy.deepcopy(unresolved),
            }
        )
        device["feedback_outputs"].append(
            {
                "slot_id": "device-feedback-000001",
                "display_label": "Reference indicator",
                "feedback_kind": "indicator",
                "direction": "instrument-to-device",
                "capability": copy.deepcopy(unresolved),
            }
        )
        device["displays"].append(
            {
                "slot_id": "device-display-000001",
                "display_label": "Reference display",
                "display_kind": "text",
                "direction": "instrument-to-device",
                "capability": copy.deepcopy(unresolved),
            }
        )
        device["physical_io"].append(
            {
                "slot_id": "device-physical-io-000001",
                "display_label": "Reference audio output",
                "io_kind": "audio",
                "direction": "output",
                "capability": copy.deepcopy(unresolved),
            }
        )
        fact["affected_subjects"].extend(
            [
                "input-control:device-input-000002",
                "input-control:device-input-000003",
                "gesture:device-gesture-000001",
                "feedback-output:device-feedback-000001",
                "display:device-display-000001",
                "physical-io:device-physical-io-000001",
            ]
        )

        instrument["actions"].append(
            {
                "facet_id": "instrument-action-000001",
                "display_label": "Reset",
                "payload_kind": "none",
            }
        )
        instrument["displays"].append(
            {
                "facet_id": "instrument-display-000001",
                "display_label": "Blend value",
                "value_kind": "text",
                "access": "read-only",
            }
        )
        instrument["state_declarations"].append(
            {
                "state_id": "instrument-state-000001",
                "display_label": "Latched mode",
                "value_kind": "boolean",
                "persistence": "volatile",
                "reset_policy": "explicit-action",
            }
        )
        instrument["device_input_mappings"].append(
            {
                "mapping_id": "device-mapping-000002",
                "mapping_kind": "action-trigger",
                "direction": "device-to-instrument",
                "source": {
                    "facet_kind": "gesture",
                    "gesture_id": "device-gesture-000001",
                },
                "destination": {
                    "facet_kind": "action",
                    "facet_id": "instrument-action-000001",
                },
            }
        )
        instrument["device_feedback_mappings"].extend(
            [
                {
                    "mapping_id": "feedback-mapping-000001",
                    "direction": "instrument-to-device",
                    "source": {
                        "facet_kind": "display",
                        "facet_id": "instrument-display-000001",
                    },
                    "destination": {
                        "slot_kind": "display",
                        "slot_id": "device-display-000001",
                    },
                    "update_responsibility": "instrument",
                },
                {
                    "mapping_id": "feedback-mapping-000002",
                    "direction": "instrument-to-device",
                    "source": {
                        "facet_kind": "state",
                        "facet_id": "instrument-state-000001",
                    },
                    "destination": {
                        "slot_kind": "feedback-output",
                        "slot_id": "device-feedback-000001",
                    },
                    "update_responsibility": "instrument",
                },
            ]
        )
        instrument["graph_reference"]["declared_targets"].extend(
            [
                {
                    "facet_id": "graph-facet-000002",
                    "facet_kind": "port",
                    "semantic_key": "blend-control",
                },
                {
                    "facet_id": "graph-facet-000003",
                    "facet_kind": "action",
                    "semantic_key": "reset",
                },
            ]
        )
        parameter_to_port = copy.deepcopy(instrument["graph_mappings"][0])
        parameter_to_port["mapping_id"] = "graph-mapping-000002"
        parameter_to_port["mapping_kind"] = "parameter-to-port"
        parameter_to_port["destination"] = {
            "facet_kind": "port",
            "facet_id": "graph-facet-000002",
        }
        instrument["graph_mappings"].extend(
            [
                parameter_to_port,
                {
                    "mapping_id": "graph-mapping-000003",
                    "mapping_kind": "action-to-action",
                    "direction": "instrument-to-graph",
                    "source": {
                        "facet_kind": "action",
                        "facet_id": "instrument-action-000001",
                    },
                    "destination": {
                        "facet_kind": "action",
                        "facet_id": "graph-facet-000003",
                    },
                },
            ]
        )
        self.rehash(device, instrument, "device")
        summary = self.validate(device=device, instrument=instrument)
        self.assertEqual("valid-with-deferred-graph", summary["status"])
        self.assertEqual([], summary["diagnostics"])

    def test_negative_fixture_matrix(self):
        self.assertEqual(
            "device-instrument-negative-fixtures-v0",
            self.negative_fixtures["schema_version"],
        )
        for case in self.negative_fixtures["cases"]:
            with self.subTest(case=case["case_id"]):
                device = copy.deepcopy(self.device)
                instrument = copy.deepcopy(self.instrument)
                target = device if case["target"] == "device" else instrument
                for mutation in case["mutations"]:
                    _apply_mutation(target, mutation)
                if case["rehash"]:
                    self.rehash(device, instrument, case["target"])
                summary = self.validate(device=device, instrument=instrument)
                codes = {item["code"] for item in summary["diagnostics"]}
                self.assertEqual("invalid", summary["status"])
                self.assertIn(case["expected_code"], codes)


if __name__ == "__main__":
    unittest.main()
