import copy
import hashlib
import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools/contracts"

if "validate_device_instrument_contracts" not in sys.modules:
    BASE_SPEC = importlib.util.spec_from_file_location(
        "validate_device_instrument_contracts",
        TOOLS / "validate_device_instrument_contracts.py",
    )
    BASE = importlib.util.module_from_spec(BASE_SPEC)
    sys.modules[BASE_SPEC.name] = BASE
    BASE_SPEC.loader.exec_module(BASE)
else:
    BASE = sys.modules["validate_device_instrument_contracts"]

SPEC = importlib.util.spec_from_file_location(
    "validate_component_graph_contracts",
    TOOLS / "validate_component_graph_contracts.py",
)
VALIDATOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = VALIDATOR
SPEC.loader.exec_module(VALIDATOR)

SCHEMA_ROOT = ROOT / "schemas"
CONTRACT_ROOT = ROOT / "contracts"
FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures/component-graph-negative-fixtures.json"


def _ref(record, id_field):
    return {
        id_field: record[id_field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def _codes(result):
    diagnostics = result.diagnostics if hasattr(result, "diagnostics") else result["diagnostics"]
    return {
        item.code if hasattr(item, "code") else item["code"]
        for item in diagnostics
    }


def _set_pointer(value, pointer, replacement):
    tokens = [item.replace("~1", "/").replace("~0", "~") for item in pointer[1:].split("/")]
    parent = value
    for token in tokens[:-1]:
        parent = parent[int(token)] if isinstance(parent, list) else parent[token]
    final = int(tokens[-1]) if isinstance(parent, list) else tokens[-1]
    parent[final] = copy.deepcopy(replacement)


def _remove_pointer(value, pointer):
    tokens = [item.replace("~1", "/").replace("~0", "~") for item in pointer[1:].split("/")]
    parent = value
    for token in tokens[:-1]:
        parent = parent[int(token)] if isinstance(parent, list) else parent[token]
    final = int(tokens[-1]) if isinstance(parent, list) else tokens[-1]
    del parent[final]


class ComponentGraphContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schemas = VALIDATOR._schemas(SCHEMA_ROOT)
        cls.family = BASE.load_json(CONTRACT_ROOT / "catalog-families/crossfader-v1.json")
        cls.control = BASE.load_json(CONTRACT_ROOT / "component-contracts/crossfader-control-v0.json")
        cls.audio = BASE.load_json(CONTRACT_ROOT / "component-contracts/crossfader-audio-v0.json")
        cls.mixed = BASE.load_json(CONTRACT_ROOT / "component-contracts/crossfader-mixed-v0.json")
        cls.bind_control = BASE.load_json(CONTRACT_ROOT / "implementation-bindings/crossfader-control-legacy-v0.json")
        cls.bind_audio = BASE.load_json(CONTRACT_ROOT / "implementation-bindings/crossfader-audio-legacy-v0.json")
        cls.bind_mixed = BASE.load_json(CONTRACT_ROOT / "implementation-bindings/crossfader-mixed-legacy-v0.json")
        cls.graph = BASE.load_json(CONTRACT_ROOT / "graphs/blend-crossfader-v0.json")
        cls.device = BASE.load_json(CONTRACT_ROOT / "device-profiles/gills-minimal-v0.json")
        cls.instrument_r1 = BASE.load_json(CONTRACT_ROOT / "instruments/blend-reference-v0.json")
        cls.instrument_r2 = BASE.load_json(CONTRACT_ROOT / "instruments/blend-reference-v0-r2.json")
        cls.device_schema = BASE.load_json(SCHEMA_ROOT / BASE.DEVICE_SCHEMA_NAME)
        cls.instrument_schema = BASE.load_json(SCHEMA_ROOT / BASE.INSTRUMENT_SCHEMA_NAME)
        cls.overlay_path = ROOT / VALIDATOR.OVERLAY_RELATIVE_PATH
        cls.snapshot_root = ROOT / VALIDATOR.SNAPSHOT_RELATIVE_PATH
        cls.manifest_path = cls.snapshot_root / "manifest.json"
        cls.overlay = BASE.load_json(cls.overlay_path)
        cls.observations = VALIDATOR._observations(cls.snapshot_root)
        cls.negative_fixtures = BASE.load_json(FIXTURE_PATH)

    def core(
        self,
        families=None,
        contracts=None,
        bindings=None,
        graphs=None,
        overlay=None,
    ):
        return VALIDATOR.validate_component_graph_values(
            copy.deepcopy([self.family] if families is None else families),
            copy.deepcopy(
                [self.control, self.audio, self.mixed]
                if contracts is None
                else contracts
            ),
            copy.deepcopy(
                [self.bind_control, self.bind_audio, self.bind_mixed]
                if bindings is None
                else bindings
            ),
            copy.deepcopy([self.graph] if graphs is None else graphs),
            self.schemas,
            copy.deepcopy(self.overlay if overlay is None else overlay),
            VALIDATOR.sha256_file(self.overlay_path),
            VALIDATOR.sha256_file(self.manifest_path),
            self.observations,
        )

    def rehash(self, record, kind):
        record["content_hash"] = BASE.record_content_hash(record, self.schemas[kind])

    def make_contract(self, numeric_id, *, transparent=False):
        contract = copy.deepcopy(self.mixed)
        contract["component_contract_id"] = f"schuss-component-contract-{numeric_id:06d}"
        contract["display_name"] = f"Fixture contract {numeric_id:06d}"
        if transparent:
            contract["compound_interface"] = {
                "kind": "transparent-compound",
                "mapping_keys": [
                    {
                        "mapping_key": f"compound-mapping-key-{index:06d}",
                        "facet_kind": "port",
                        "facet_id": f"component-port-{index:06d}",
                    }
                    for index in range(1, 5)
                ],
            }
        self.rehash(contract, "contract")
        return contract

    def make_two_node_graph(self, source_contract, destination_contract, numeric_id=900010):
        graph = copy.deepcopy(self.graph)
        graph["graph_id"] = f"schuss-graph-{numeric_id:06d}"
        graph["display_name"] = f"Two node fixture {numeric_id:06d}"
        graph["public_ports"] = [
            {"facet_id": "graph-facet-900001", "semantic_key": "source-a", "display_label": "Source A", "direction": "input"},
            {"facet_id": "graph-facet-900002", "semantic_key": "source-b", "display_label": "Source B", "direction": "input"},
            {"facet_id": "graph-facet-900003", "semantic_key": "destination-b", "display_label": "Destination B", "direction": "input"},
            {"facet_id": "graph-facet-900004", "semantic_key": "out", "display_label": "Out", "direction": "output"},
        ]
        first_parameter = copy.deepcopy(self.graph["public_parameters"][0])
        first_parameter["facet_id"] = "graph-facet-900005"
        first_parameter["semantic_key"] = "source-blend"
        second_parameter = copy.deepcopy(first_parameter)
        second_parameter["facet_id"] = "graph-facet-900006"
        second_parameter["semantic_key"] = "destination-blend"
        graph["public_parameters"] = [first_parameter, second_parameter]
        graph["nodes"] = [
            {
                "node_id": "graph-node-900001",
                "contract_reference": _ref(source_contract, "component_contract_id"),
                "parameter_values": [],
                "attribute_values": [],
            },
            {
                "node_id": "graph-node-900002",
                "contract_reference": _ref(destination_contract, "component_contract_id"),
                "parameter_values": [],
                "attribute_values": [],
            },
        ]
        graph["connections"] = [
            {
                "connection_id": "graph-connection-900001",
                "source": {"node_id": "graph-node-900001", "facet_id": "component-port-000004"},
                "destination": {"node_id": "graph-node-900002", "facet_id": "component-port-000001"},
            }
        ]
        graph["public_port_exposures"] = [
            {"exposure_id": "graph-exposure-900001", "graph_facet_id": "graph-facet-900001", "node_port": {"node_id": "graph-node-900001", "facet_id": "component-port-000001"}},
            {"exposure_id": "graph-exposure-900002", "graph_facet_id": "graph-facet-900002", "node_port": {"node_id": "graph-node-900001", "facet_id": "component-port-000002"}},
            {"exposure_id": "graph-exposure-900003", "graph_facet_id": "graph-facet-900003", "node_port": {"node_id": "graph-node-900002", "facet_id": "component-port-000002"}},
            {"exposure_id": "graph-exposure-900004", "graph_facet_id": "graph-facet-900004", "node_port": {"node_id": "graph-node-900002", "facet_id": "component-port-000004"}},
        ]
        first_binding = copy.deepcopy(self.graph["parameter_bindings"][0])
        first_binding["binding_id"] = "graph-binding-900001"
        first_binding["source_graph_parameter_id"] = "graph-facet-900005"
        first_binding["destination"]["node_id"] = "graph-node-900001"
        second_binding = copy.deepcopy(first_binding)
        second_binding["binding_id"] = "graph-binding-900002"
        second_binding["source_graph_parameter_id"] = "graph-facet-900006"
        second_binding["destination"]["node_id"] = "graph-node-900002"
        graph["parameter_bindings"] = [first_binding, second_binding]
        graph["public_facet_exposures"] = []
        graph["compound_interface_mappings"] = []
        graph["hierarchy_edges"] = []
        self.rehash(graph, "graph")
        return graph

    def make_optional_graph(self, contract, numeric_id=900020):
        graph = copy.deepcopy(self.graph)
        graph["graph_id"] = f"schuss-graph-{numeric_id:06d}"
        graph["display_name"] = "Optional inlet fixture"
        graph["nodes"][0]["contract_reference"] = _ref(contract, "component_contract_id")
        graph["public_ports"] = [
            item for item in graph["public_ports"] if item["semantic_key"] != "a"
        ]
        graph["public_port_exposures"] = [
            item
            for item in graph["public_port_exposures"]
            if item["node_port"]["facet_id"] != "component-port-000001"
        ]
        self.rehash(graph, "graph")
        return graph

    def make_transparent_graph(self, outer_contract, inner_contract, numeric_id):
        graph = copy.deepcopy(self.graph)
        graph["graph_id"] = f"schuss-graph-{numeric_id:06d}"
        graph["display_name"] = f"Transparent fixture {numeric_id:06d}"
        graph["public_ports"] = [
            {"facet_id": f"graph-facet-{numeric_id + offset:06d}", "semantic_key": key, "display_label": key.upper(), "direction": direction}
            for offset, key, direction in (
                (0, "a", "input"),
                (1, "b", "input"),
                (2, "fade", "input"),
                (3, "out", "output"),
            )
        ]
        graph["public_parameters"] = []
        graph["nodes"] = [
            {
                "node_id": f"graph-node-{numeric_id:06d}",
                "contract_reference": _ref(inner_contract, "component_contract_id"),
                "parameter_values": [],
                "attribute_values": [],
            }
        ]
        graph["connections"] = []
        graph["public_port_exposures"] = [
            {
                "exposure_id": f"graph-exposure-{numeric_id + index - 1:06d}",
                "graph_facet_id": f"graph-facet-{numeric_id + index - 1:06d}",
                "node_port": {
                    "node_id": f"graph-node-{numeric_id:06d}",
                    "facet_id": f"component-port-{index:06d}",
                },
            }
            for index in range(1, 5)
        ]
        graph["public_facet_exposures"] = []
        graph["parameter_bindings"] = []
        graph["compound_interface_mappings"] = [
            {
                "mapping_key": f"compound-mapping-key-{index:06d}",
                "target": {
                    "node_id": f"graph-node-{numeric_id:06d}",
                    "facet_kind": "port",
                    "facet_id": f"component-port-{index:06d}",
                },
            }
            for index in range(1, 5)
        ]
        graph["hierarchy_edges"] = []
        self.rehash(graph, "graph")
        return graph

    def make_transparent_binding(self, contract, graph, numeric_id):
        binding = copy.deepcopy(self.bind_mixed)
        binding["implementation_id"] = f"schuss-implementation-{numeric_id:06d}"
        binding["contract_reference"] = _ref(contract, "component_contract_id")
        binding["realization"] = {
            "form": "transparent-compound",
            "graph_reference": _ref(graph, "graph_id"),
        }
        binding["facet_mappings"] = [
            {
                "mapping_id": f"binding-map-{numeric_id + index - 1:06d}",
                "contract_facet": {
                    "facet_kind": "port",
                    "facet_id": f"component-port-{index:06d}",
                },
                "implementation_seam": {
                    "seam_kind": "graph-mapping-key",
                    "mapping_key": f"compound-mapping-key-{index:06d}",
                },
            }
            for index in range(1, 5)
        ]
        binding["observed_dependencies"] = []
        binding["private_state"] = []
        binding["evidence_refs"] = ["fixture:transparent-compound"]
        self.rehash(binding, "binding")
        return binding

    def test_production_aggregate_is_valid_with_historical_deferred_revision(self):
        summary = VALIDATOR.validate_all_contracts(CONTRACT_ROOT, SCHEMA_ROOT, ROOT)
        self.assertEqual("valid-with-historical-deferred", summary["status"])
        self.assertEqual([], summary["diagnostics"])
        self.assertEqual(1, summary["reference_resolution"]["instrument_graphs_resolved"])
        self.assertEqual(1, summary["reference_resolution"]["instrument_graphs_deferred"])
        levels = {item["level"]: item["status"] for item in summary["evidence_levels"]}
        self.assertEqual("passed", levels["target-independent-contract-type"])
        self.assertEqual("passed", levels["implementation-seam-map"])
        self.assertEqual("passed-with-historical-deferred", levels["instrument-graph-target"])
        for level in (
            "backend-lowering",
            "artifact-generation",
            "arm-compile-link",
            "connected-device",
            "real-time-resource",
            "audible-listening",
        ):
            self.assertEqual("not-run", levels[level])

    def test_schema_contracts_are_closed_and_canonical_hashes_round_trip(self):
        for name, schema in self.schemas.items():
            with self.subTest(schema=name):
                self.assertEqual([], BASE.validate_schema_annotations(schema))
        for kind, records in (
            ("family", [self.family]),
            ("contract", [self.control, self.audio, self.mixed]),
            ("binding", [self.bind_control, self.bind_audio, self.bind_mixed]),
            ("graph", [self.graph]),
        ):
            for record in records:
                with self.subTest(record=VALIDATOR._subject(record)):
                    self.assertEqual(record["content_hash"], BASE.record_content_hash(record, self.schemas[kind]))
        self.assertEqual(self.instrument_r2["content_hash"], BASE.record_content_hash(self.instrument_r2, self.instrument_schema))

    def test_fresh_process_summary_and_all_production_canonical_bytes_are_deterministic(self):
        command = [sys.executable, str(TOOLS / "validate_component_graph_contracts.py"), str(CONTRACT_ROOT), "--schema-root", str(SCHEMA_ROOT)]
        self.assertEqual(subprocess.check_output(command), subprocess.check_output(command))
        records = [
            ("catalog-family-companion", CONTRACT_ROOT / "catalog-families/crossfader-v1.json"),
            *(('component-contract', path) for path in sorted((CONTRACT_ROOT / 'component-contracts').glob('*.json'))),
            *(('implementation-binding', path) for path in sorted((CONTRACT_ROOT / 'implementation-bindings').glob('*.json'))),
            ("dsp-graph", CONTRACT_ROOT / "graphs/blend-crossfader-v0.json"),
            ("instrument", CONTRACT_ROOT / "instruments/blend-reference-v0-r2.json"),
        ]
        for kind, path in records:
            with self.subTest(path=path.name):
                emit = [sys.executable, str(TOOLS / "validate_component_graph_contracts.py"), "--schema-root", str(SCHEMA_ROOT), "--canonical-record", str(path), "--record-kind", kind]
                self.assertEqual(subprocess.check_output(emit), subprocess.check_output(emit))

    def test_task005_records_and_schema_bytes_remain_frozen(self):
        expected_raw = {
            "schemas/device-profile-v0.schema.json": "5c81b6ced640165342a471edc19aa5523c1b9ba44e8d666adcf6e46cb6a13ccc",
            "schemas/instrument-v0.schema.json": "94a6f720647dd6b9099708a1f31d84790a9ec2b5254330334bd694c5ef31c5c8",
            "contracts/device-profiles/gills-minimal-v0.json": "2dd75c58ebea79be11abf8bbd8bb8ff320c77eb303d35388fc8baa6a49d3d855",
            "contracts/instruments/blend-reference-v0.json": "d88769280887ec54ee5e9cfbb631c4150d7c5a0878a8cd17e9bf7c7005216d0c",
        }
        for relative, expected in expected_raw.items():
            with self.subTest(path=relative):
                self.assertEqual(expected, hashlib.sha256((ROOT / relative).read_bytes()).hexdigest())
        self.assertEqual("sha256:d6ad487f5444b1e39667ed8b4e43dde32ce7f06accac0be4fd5930c9b7eb82fe", self.device["content_hash"])
        self.assertEqual("sha256:3543d631ceb32b17be95c84eccc07d38ad29f1dc71c5a267b40306f69711bc53", self.instrument_r1["content_hash"])

    def test_set_reordering_is_invariant_but_transform_point_sequence_is_semantic(self):
        reordered = copy.deepcopy(self.graph)
        reordered["public_ports"].reverse()
        self.assertEqual(
            BASE.canonical_record_bytes(self.graph, self.schemas["graph"]),
            BASE.canonical_record_bytes(reordered, self.schemas["graph"]),
        )
        sequence = copy.deepcopy(self.graph)
        sequence["parameter_bindings"][0]["transform"]["points"].reverse()
        self.assertNotEqual(
            BASE.canonical_record_bytes(self.graph, self.schemas["graph"]),
            BASE.canonical_record_bytes(sequence, self.schemas["graph"]),
        )
        self.rehash(sequence, "graph")
        self.assertIn("GRAPH_PARAMETER_TRANSFORM_INVALID", _codes(self.core(graphs=[sequence])))

    def test_negative_mutation_fixture_matrix(self):
        self.assertEqual("component-graph-negative-fixtures-v0", self.negative_fixtures["schema_version"])
        for case in self.negative_fixtures["cases"]:
            with self.subTest(case=case["case_id"]):
                family = copy.deepcopy(self.family)
                contract = copy.deepcopy(self.mixed)
                binding = copy.deepcopy(self.bind_control)
                graph = copy.deepcopy(self.graph)
                target_name = case["target"]
                target = {
                    "family": family,
                    "contract": contract,
                    "binding": binding,
                    "graph": graph,
                    "graph-remove": graph,
                }[target_name]
                if target_name == "graph-remove":
                    _remove_pointer(target, case["pointer"])
                else:
                    _set_pointer(target, case["pointer"], case["value"])
                if case["rehash"]:
                    self.rehash(target, {"family": "family", "contract": "contract", "binding": "binding", "graph": "graph"}[target_name])
                result = self.core(
                    families=[family],
                    contracts=[self.control, self.audio, contract],
                    bindings=[binding, self.bind_audio, self.bind_mixed],
                    graphs=[graph],
                )
                self.assertEqual("invalid", result.summary["status"])
                self.assertIn(case["expected_code"], _codes(result))

    def test_identity_collisions_family_ambiguity_and_signature_masquerade_fail(self):
        changed = copy.deepcopy(self.control)
        changed["display_name"] = "Changed label"
        self.rehash(changed, "contract")
        self.assertIn("ID_REVISION_COLLISION", _codes(self.core(contracts=[self.control, changed, self.audio, self.mixed])))

        masquerade = copy.deepcopy(self.audio)
        masquerade["component_contract_id"] = self.control["component_contract_id"]
        masquerade["revision"] = 2
        self.rehash(masquerade, "contract")
        self.assertIn("CONTRACT_SIGNATURE_REVISION_MISMATCH", _codes(self.core(contracts=[self.control, self.audio, self.mixed, masquerade])))

        overlay = copy.deepcopy(self.overlay)
        member = next(item for item in overlay["families"] if item["family_id"] == self.family["family_id"])
        overlay["families"].append(copy.deepcopy(member))
        self.assertIn("FAMILY_MEMBER_AMBIGUOUS", _codes(self.core(overlay=overlay)))

        overlay = copy.deepcopy(self.overlay)
        next(item for item in overlay["implementations"] if item["implementation_id"] == self.bind_control["implementation_id"])["family_id"] = "schuss-family-000019"
        self.assertIn("IMPLEMENTATION_FAMILY_MISMATCH", _codes(self.core(overlay=overlay)))

    def test_binding_total_unique_directional_seam_map_fails_closed(self):
        missing = copy.deepcopy(self.bind_control)
        missing["facet_mappings"].pop()
        self.rehash(missing, "binding")
        self.assertIn("BINDING_MAP_INCOMPLETE", _codes(self.core(bindings=[missing, self.bind_audio, self.bind_mixed])))

        duplicate = copy.deepcopy(self.bind_control)
        extra = copy.deepcopy(duplicate["facet_mappings"][0])
        extra["mapping_id"] = "binding-map-900001"
        extra["contract_facet"]["facet_id"] = "component-port-000002"
        duplicate["facet_mappings"].append(extra)
        self.rehash(duplicate, "binding")
        self.assertIn("BINDING_SEAM_DUPLICATE", _codes(self.core(bindings=[duplicate, self.bind_audio, self.bind_mixed])))

        wrong_direction = copy.deepcopy(self.bind_control)
        wrong_direction["facet_mappings"][0]["implementation_seam"] = copy.deepcopy(wrong_direction["facet_mappings"][3]["implementation_seam"])
        self.rehash(wrong_direction, "binding")
        codes = _codes(self.core(bindings=[wrong_direction, self.bind_audio, self.bind_mixed]))
        self.assertTrue({"BINDING_SEAM_DUPLICATE", "BINDING_TYPE_INCOMPATIBLE"} & codes)

        wrong_form = copy.deepcopy(self.bind_control)
        wrong_form["realization"]["form"] = "legacy-native-object"
        self.rehash(wrong_form, "binding")
        self.assertIn("IMPLEMENTATION_FORM_MISMATCH", _codes(self.core(bindings=[wrong_form, self.bind_audio, self.bind_mixed])))

    def test_all_public_facet_kinds_remain_distinct(self):
        cases = (
            ("parameter", "component-port-000001"),
            ("attribute", "component-port-000001"),
            ("action", "component-port-000001"),
            ("display", "component-port-000001"),
            ("port", "component-parameter-000001"),
        )
        for facet_kind, facet_id in cases:
            with self.subTest(facet_kind=facet_kind, facet_id=facet_id):
                binding = copy.deepcopy(self.bind_control)
                binding["facet_mappings"][0]["contract_facet"] = {
                    "facet_kind": facet_kind,
                    "facet_id": facet_id,
                }
                self.rehash(binding, "binding")
                result = self.core(bindings=[binding, self.bind_audio, self.bind_mixed])
                self.assertIn("BINDING_FACET_UNKNOWN", _codes(result))

    def test_exact_subset_and_optional_connection_cases_pass(self):
        source = self.make_contract(900010)
        destination = self.make_contract(900011)
        exact_graph = self.make_two_node_graph(source, destination)
        result = self.core(contracts=[self.control, self.audio, self.mixed, source, destination], graphs=[self.graph, exact_graph])
        self.assertEqual("valid", result.summary["status"])

        subset_source = self.make_contract(900012)
        subset_destination = self.make_contract(900013)
        subset_source["ports"][3]["port_type"]["valid_range"]["minimum"] = "-0.5"
        subset_source["ports"][3]["port_type"]["valid_range"]["maximum"] = "0.5"
        self.rehash(subset_source, "contract")
        subset_graph = self.make_two_node_graph(subset_source, subset_destination, 900012)
        result = self.core(contracts=[self.control, self.audio, self.mixed, subset_source, subset_destination], graphs=[self.graph, subset_graph])
        self.assertEqual("valid", result.summary["status"])

        optional = self.make_contract(900020)
        optional["ports"][0]["port_type"]["cardinality"]["minimum_connections"] = 0
        optional["ports"][0]["port_type"]["optionality"] = {"status": "optional", "absence_behavior": "silence", "default_value": "0"}
        self.rehash(optional, "contract")
        optional_graph = self.make_optional_graph(optional)
        result = self.core(contracts=[self.control, self.audio, self.mixed, optional], graphs=[self.graph, optional_graph])
        self.assertEqual("valid", result.summary["status"])

    def test_all_prohibited_direct_connection_conversions_fail(self):
        mutations = {
            "domain": lambda port: port["port_type"].__setitem__("domain", "message-data"),
            "rate": lambda port: (port["port_type"].__setitem__("rate", "control"), port["port_type"]["ownership"].__setitem__("lifetime", "control-cycle")),
            "channel": lambda port: port["port_type"]["channel_shape"].__setitem__("count", 2),
            "representation": lambda port: port["port_type"]["representation"].__setitem__("fractional_bits", 26),
            "semantic-role": lambda port: port["port_type"].__setitem__("semantic_role", "generic-signal"),
            "unit": lambda port: port["port_type"].__setitem__("unit", "unitless"),
            "range": lambda port: (port["port_type"]["valid_range"].__setitem__("minimum", "-0.5"), port["port_type"]["valid_range"].__setitem__("maximum", "0.5")),
            "ownership": lambda port: port["port_type"]["ownership"].__setitem__("capacity", "single-value"),
        }
        for index, (dimension, mutate) in enumerate(mutations.items(), 1):
            with self.subTest(dimension=dimension):
                source = self.make_contract(901000 + index * 2)
                destination = self.make_contract(901001 + index * 2)
                mutate(destination["ports"][0])
                self.rehash(destination, "contract")
                graph = self.make_two_node_graph(source, destination, 901000 + index)
                result = self.core(contracts=[self.control, self.audio, self.mixed, source, destination], graphs=[self.graph, graph])
                self.assertIn("GRAPH_CONNECTION_TYPE_INCOMPATIBLE", _codes(result))

    def test_payload_and_facet_kind_conversion_fail(self):
        contract = self.make_contract(902001)
        contract["actions"] = [{"facet_id": "component-action-000001", "semantic_key": "reset", "display_label": "Reset", "payload_kind": "none"}]
        self.rehash(contract, "contract")
        graph = copy.deepcopy(self.graph)
        graph["graph_id"] = "schuss-graph-902001"
        graph["nodes"][0]["contract_reference"] = _ref(contract, "component_contract_id")
        graph["public_actions"] = [{"facet_id": "graph-facet-902001", "semantic_key": "reset", "display_label": "Reset", "payload_kind": "exact-decimal"}]
        graph["public_facet_exposures"] = [{"exposure_id": "graph-exposure-902001", "graph_facet_kind": "action", "graph_facet_id": "graph-facet-902001", "target": {"node_id": "graph-node-000001", "facet_kind": "action", "facet_id": "component-action-000001"}}]
        self.rehash(graph, "graph")
        self.assertIn("GRAPH_EXPOSURE_TYPE_INCOMPATIBLE", _codes(self.core(contracts=[self.control, self.audio, self.mixed, contract], graphs=[self.graph, graph])))

        graph["public_actions"][0]["payload_kind"] = "none"
        graph["public_facet_exposures"][0]["target"] = {"node_id": "graph-node-000001", "facet_kind": "display", "facet_id": "component-display-000001"}
        self.rehash(graph, "graph")
        self.assertIn("GRAPH_EXPOSURE_UNRESOLVED", _codes(self.core(contracts=[self.control, self.audio, self.mixed, contract], graphs=[self.graph, graph])))

    def test_graph_parameter_binding_requires_every_explicit_policy(self):
        required = (
            "source_domain",
            "destination_domain",
            "transform",
            "update_boundary",
            "smoothing",
            "driver_policy",
        )
        for index, field in enumerate(required, 1):
            with self.subTest(field=field):
                graph = copy.deepcopy(self.graph)
                graph["graph_id"] = f"schuss-graph-{902100 + index:06d}"
                del graph["parameter_bindings"][0][field]
                result = self.core(graphs=[self.graph, graph])
                self.assertIn("SCHEMA_STRUCTURE_INVALID", _codes(result))

    def test_graph_endpoint_direction_driver_exposure_and_cycles_fail(self):
        cases = []
        unknown = copy.deepcopy(self.graph)
        unknown["connections"] = [{"connection_id": "graph-connection-900001", "source": {"node_id": "graph-node-999999", "facet_id": "component-port-000004"}, "destination": {"node_id": "graph-node-000001", "facet_id": "component-port-000001"}}]
        cases.append((unknown, "GRAPH_ENDPOINT_UNKNOWN"))
        inlet_to_inlet = copy.deepcopy(self.graph)
        inlet_to_inlet["connections"] = [{"connection_id": "graph-connection-900001", "source": {"node_id": "graph-node-000001", "facet_id": "component-port-000001"}, "destination": {"node_id": "graph-node-000001", "facet_id": "component-port-000002"}}]
        cases.append((inlet_to_inlet, "GRAPH_CONNECTION_DIRECTION_INVALID"))
        outlet_to_outlet = copy.deepcopy(self.graph)
        outlet_to_outlet["connections"] = [{"connection_id": "graph-connection-900001", "source": {"node_id": "graph-node-000001", "facet_id": "component-port-000004"}, "destination": {"node_id": "graph-node-000001", "facet_id": "component-port-000004"}}]
        cases.append((outlet_to_outlet, "GRAPH_CONNECTION_DIRECTION_INVALID"))
        duplicate_driver = copy.deepcopy(self.graph)
        duplicate_driver["connections"] = [{"connection_id": "graph-connection-900001", "source": {"node_id": "graph-node-000001", "facet_id": "component-port-000004"}, "destination": {"node_id": "graph-node-000001", "facet_id": "component-port-000001"}}]
        cases.append((duplicate_driver, "DUPLICATE_DRIVER"))
        duplicate_connection_id = copy.deepcopy(self.graph)
        duplicate_connection_id["connections"] = [
            {"connection_id": "graph-connection-900001", "source": {"node_id": "graph-node-000001", "facet_id": "component-port-000004"}, "destination": {"node_id": "graph-node-000001", "facet_id": "component-port-000001"}},
            {"connection_id": "graph-connection-900001", "source": {"node_id": "graph-node-000001", "facet_id": "component-port-000004"}, "destination": {"node_id": "graph-node-000001", "facet_id": "component-port-000002"}},
        ]
        cases.append((duplicate_connection_id, "DUPLICATE_LOCAL_ID"))
        dangling = copy.deepcopy(self.graph)
        dangling["public_port_exposures"][0]["node_port"]["facet_id"] = "component-port-999999"
        cases.append((dangling, "GRAPH_EXPOSURE_UNRESOLVED"))
        duplicate_exposure_id = copy.deepcopy(self.graph)
        duplicate_exposure_id["public_port_exposures"][1]["exposure_id"] = duplicate_exposure_id["public_port_exposures"][0]["exposure_id"]
        cases.append((duplicate_exposure_id, "DUPLICATE_LOCAL_ID"))
        missing = copy.deepcopy(self.graph)
        missing["public_port_exposures"].pop(0)
        cases.append((missing, "GRAPH_REQUIRED_INLET_UNDRIVEN"))
        hierarchy = copy.deepcopy(self.graph)
        hierarchy["hierarchy_edges"] = [{"parent_node_id": "graph-node-000001", "child_node_id": "graph-node-000001"}]
        cases.append((hierarchy, "GRAPH_HIERARCHY_CYCLE"))
        for index, (graph, expected) in enumerate(cases, 1):
            with self.subTest(expected=expected):
                graph["graph_id"] = f"schuss-graph-{903000 + index:06d}"
                self.rehash(graph, "graph")
                self.assertIn(expected, _codes(self.core(graphs=[self.graph, graph])))

    def test_transparent_compound_total_mapping_and_recursion_rules(self):
        outer = self.make_contract(904001, transparent=True)
        graph = self.make_transparent_graph(outer, self.mixed, 904001)
        binding = self.make_transparent_binding(outer, graph, 904001)
        contracts = [self.control, self.audio, self.mixed, outer]
        bindings = [self.bind_control, self.bind_audio, self.bind_mixed, binding]
        graphs = [self.graph, graph]
        self.assertEqual("valid", self.core(contracts=contracts, bindings=bindings, graphs=graphs).summary["status"])

        missing_graph = copy.deepcopy(graph)
        missing_graph["compound_interface_mappings"].pop()
        self.rehash(missing_graph, "graph")
        missing_binding = self.make_transparent_binding(outer, missing_graph, 904002)
        self.assertIn("COMPOUND_MAPPING_INCOMPLETE", _codes(self.core(contracts=contracts, bindings=[self.bind_control, self.bind_audio, self.bind_mixed, missing_binding], graphs=[self.graph, missing_graph])))

        duplicate_graph = copy.deepcopy(graph)
        duplicate_mapping = copy.deepcopy(duplicate_graph["compound_interface_mappings"][0])
        duplicate_mapping["target"]["facet_id"] = "component-port-000002"
        duplicate_graph["compound_interface_mappings"].append(duplicate_mapping)
        self.rehash(duplicate_graph, "graph")
        duplicate_binding = self.make_transparent_binding(outer, duplicate_graph, 904005)
        self.assertIn("COMPOUND_MAPPING_DUPLICATE", _codes(self.core(contracts=contracts, bindings=[self.bind_control, self.bind_audio, self.bind_mixed, duplicate_binding], graphs=[self.graph, duplicate_graph])))

        hidden = copy.deepcopy(outer)
        hidden["component_contract_id"] = "schuss-component-contract-904006"
        hidden["compound_interface"]["mapping_keys"].pop()
        self.rehash(hidden, "contract")
        hidden_graph = self.make_transparent_graph(hidden, self.mixed, 904006)
        hidden_binding = self.make_transparent_binding(hidden, hidden_graph, 904006)
        self.assertIn("COMPOUND_MAPPING_INCOMPLETE", _codes(self.core(contracts=[self.control, self.audio, self.mixed, hidden], bindings=[self.bind_control, self.bind_audio, self.bind_mixed, hidden_binding], graphs=[self.graph, hidden_graph])))

        incompatible_graph = copy.deepcopy(graph)
        incompatible_graph["compound_interface_mappings"][0]["target"]["facet_id"] = "component-port-000003"
        self.rehash(incompatible_graph, "graph")
        incompatible_binding = self.make_transparent_binding(outer, incompatible_graph, 904003)
        self.assertIn("COMPOUND_MAPPING_TYPE_INCOMPATIBLE", _codes(self.core(contracts=contracts, bindings=[self.bind_control, self.bind_audio, self.bind_mixed, incompatible_binding], graphs=[self.graph, incompatible_graph])))

        recursive_graph = self.make_transparent_graph(outer, outer, 904004)
        recursive_binding = self.make_transparent_binding(outer, recursive_graph, 904004)
        self.assertIn("COMPOUND_RECURSION", _codes(self.core(contracts=contracts, bindings=[self.bind_control, self.bind_audio, self.bind_mixed, recursive_binding], graphs=[self.graph, recursive_graph])))

        outer_a = self.make_contract(904010, transparent=True)
        outer_b = self.make_contract(904020, transparent=True)
        graph_a = self.make_transparent_graph(outer_a, outer_b, 904010)
        graph_b = self.make_transparent_graph(outer_b, outer_a, 904020)
        binding_a = self.make_transparent_binding(outer_a, graph_a, 904010)
        binding_b = self.make_transparent_binding(outer_b, graph_b, 904020)
        result = self.core(
            contracts=[self.control, self.audio, self.mixed, outer_a, outer_b],
            bindings=[self.bind_control, self.bind_audio, self.bind_mixed, binding_a, binding_b],
            graphs=[self.graph, graph_a, graph_b],
        )
        self.assertIn("COMPOUND_RECURSION", _codes(result))

    def test_instrument_r2_exact_resolution_and_fail_closed_near_misses(self):
        core = self.core()
        summary = BASE.validate_contract_values(
            [copy.deepcopy(self.device)],
            [copy.deepcopy(self.instrument_r1), copy.deepcopy(self.instrument_r2)],
            self.device_schema,
            self.instrument_schema,
            core.graph_targets,
        )
        self.assertEqual("valid-with-deferred-graph", summary["status"])
        self.assertEqual(1, summary["reference_resolution"]["graphs_resolved"])
        self.assertEqual(1, summary["reference_resolution"]["graphs_deferred"])

        cases = []
        stale = copy.deepcopy(self.instrument_r2)
        stale["graph_reference"]["content_hash"] = "sha256:" + "0" * 64
        cases.append((stale, "GRAPH_RESOLUTION_UNAVAILABLE"))
        unknown = copy.deepcopy(self.instrument_r2)
        unknown["graph_mappings"][0]["destination"]["facet_id"] = "graph-facet-999999"
        cases.append((unknown, "GRAPH_TARGET_NOT_DECLARED"))
        wrong_kind = copy.deepcopy(self.instrument_r2)
        wrong_kind["graph_mappings"][0]["destination"]["facet_id"] = "graph-facet-000002"
        cases.append((wrong_kind, "MAPPING_FACET_KIND_MISMATCH"))
        wrong_domain = copy.deepcopy(self.instrument_r2)
        wrong_domain["graph_mappings"][0]["destination_domain"]["maximum"] = "2"
        cases.append((wrong_domain, "MAPPING_DOMAIN_REDEFINITION"))
        for instrument, expected in cases:
            instrument["content_hash"] = BASE.record_content_hash(instrument, self.instrument_schema)
            result = BASE.validate_contract_values([self.device], [instrument], self.device_schema, self.instrument_schema, core.graph_targets)
            self.assertIn(expected, _codes(result))

        false_resolved = copy.deepcopy(self.instrument_r1)
        false_resolved["graph_reference"] = {"status": "resolved", "graph_id": "schuss-graph-000001", "revision": 1, "content_hash": "sha256:" + "f" * 64}
        false_resolved["content_hash"] = BASE.record_content_hash(false_resolved, self.instrument_schema)
        result = BASE.validate_contract_values([self.device], [false_resolved], self.device_schema, self.instrument_schema, core.graph_targets)
        self.assertIn("GRAPH_RESOLUTION_UNAVAILABLE", _codes(result))


if __name__ == "__main__":
    unittest.main()
