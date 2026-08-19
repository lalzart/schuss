from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools/contracts"
sys.path[:0] = [str(ROOT), str(TOOLS)]

from packages.schuss_core.application_capabilities import build_application_description
from packages.schuss_core.control_plane import load_repository_context
from packages.schuss_core.host_runtime import HostRuntimeError
from packages.schuss_core.project_service import ProjectService
from packages.schuss_core.variable_host_runtime import lower_variable_host_package
from tools.contracts import record_set_rules
from tools.contracts import validator_core as core


RECORD_SET = ROOT / "contracts/record-sets/task032-variable-host-runtime-v1.json"
PARENT_RECORD_SET = ROOT / "contracts/record-sets/ui-desktop-workspace-shell-v1.json"
TASK031_FIXTURES = ROOT / "fixtures/task031"
FIXTURES = ROOT / "fixtures/task032"
NAMES = ("smaller", "reference", "larger")


def _reference(record, identifier):
    return {
        identifier: record[identifier],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


class Task032VariableHostRuntimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = load_repository_context(ROOT, record_set_path=RECORD_SET)
        cls.loaded_projects = {}
        cls.packages = {}
        for name in NAMES:
            loaded = ProjectService(
                FIXTURES / f"{name}-project", repository_root=ROOT
            ).load()
            cls.loaded_projects[name] = loaded
            request_reference = loaded.manifest["build_request_references"][0]
            package, plan = lower_variable_host_package(
                loaded.context,
                project_manifest=loaded.manifest,
                host_build_request_reference=request_reference,
            )
            cls.packages[name] = (package, plan)

    def test_record_set_is_one_exact_additive_successor(self):
        current = record_set_rules.load_record_set(ROOT, RECORD_SET)
        parent = record_set_rules.load_record_set(ROOT, PARENT_RECORD_SET)
        self.assertEqual(
            {"status": "included", **parent.reference},
            current.manifest["parent_reference"],
        )
        parent_records = {
            (item["record_kind"], item["stable_id"], item["revision"])
            for item in parent.manifest["record_members"]
        }
        current_records = {
            (item["record_kind"], item["stable_id"], item["revision"])
            for item in current.manifest["record_members"]
        }
        self.assertEqual(
            {("request", "schuss-build-request-000007", 1)},
            current_records - parent_records,
        )
        parent_schemas = {
            item["schema_version"] for item in parent.manifest["schema_members"]
        }
        current_schemas = {
            item["schema_version"] for item in current.manifest["schema_members"]
        }
        self.assertEqual(
            {
                "application-capability-description-v9",
                "host-engine-protocol-v1",
                "host-runtime-observation-v1",
                "host-runtime-package-v1",
                "operation-request-v16",
                "operation-result-v16",
            },
            current_schemas - parent_schemas,
        )
        self.assertEqual(456, len(current.manifest["record_members"]))
        self.assertEqual(127, len(current.manifest["schema_members"]))

    def test_generators_and_all_additive_schemas_are_fresh(self):
        for command in (
            [sys.executable, "tools/contracts/generate_task032_records.py", "--check"],
            [sys.executable, "tools/contracts/generate_task032_fixtures.py", "--check"],
            [sys.executable, "tools/contracts/run_task032_fresh_root.py", "--check"],
        ):
            completed = subprocess.run(
                command, cwd=ROOT, text=True, capture_output=True
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
        for name in (
            "application_capability_description_v9",
            "host_engine_protocol_v1",
            "host_runtime_observation_v1",
            "host_runtime_package_v1",
            "operation_request_v16",
            "operation_result_v16",
        ):
            self.assertEqual(
                [], core.validate_schema_annotations(self.context.schemas[name]), name
            )

    def test_capability_surface_is_client_neutral_and_v16(self):
        description = build_application_description(
            record_set_reference=self.context.record_set_reference,
            schemas=self.context.schemas,
        )
        schema = self.context.schemas["application_capability_description_v9"]
        self.assertEqual([], core.schema_errors(description, schema, schema))
        self.assertEqual(
            "schuss-application-capability-description-v9",
            description["description_version"],
        )
        operations = {item["operation"]: item for item in description["operations"]}
        self.assertEqual(44, len(operations))
        expected = {
            "audio.devices.inspect",
            "audio.session.inspect",
            "audio.session.replace",
            "audio.session.start",
            "audio.session.stop",
            "host.render.inspect",
            "host.render.start",
        }
        self.assertEqual(expected, expected & operations.keys())
        for operation in expected:
            self.assertEqual(
                "schuss-operation-request-v16",
                operations[operation]["request_schema_version"],
            )
            self.assertEqual(
                "schuss-operation-result-v16",
                operations[operation]["result_schema_version"],
            )
        encoded = core.canonical_json(description)
        for private_client in ("React", "Tauri", "MCP", "JUCE graph"):
            self.assertNotIn(private_client, encoded)

    def test_three_exact_projects_lower_through_one_variable_path(self):
        expected_counts = {
            "smaller": (3, 3, 2, 16),
            "reference": (7, 7, 4, 48),
            "larger": (8, 8, 4, 48),
        }
        for name in NAMES:
            with self.subTest(name=name):
                loaded = self.loaded_projects[name]
                package, plan = self.packages[name]
                retained = core.load_json(FIXTURES / f"{name}-host-package.json")
                retained_lowering = core.load_json(
                    FIXTURES / f"{name}-host-lowering.json"
                )
                self.assertEqual(retained, package)
                self.assertEqual("success", plan["status"])
                self.assertEqual(package["content_hash"], retained_lowering["package_content_hash"])
                self.assertEqual(package["source_plan_sha256"], retained_lowering["source_plan_sha256"])
                self.assertEqual(package["schedule"], retained_lowering["schedule"])
                self.assertEqual(len(package["nodes"]), retained_lowering["node_count"])
                self.assertEqual(
                    len(package["connections"]), retained_lowering["connection_count"]
                )
                self.assertEqual(
                    package["memory_plan"]["buffer_count"],
                    retained_lowering["buffer_count"],
                )
                schema = loaded.context.schemas["host_runtime_package_v1"]
                self.assertEqual([], core.schema_errors(package, schema, schema))
                self.assertEqual(
                    package["content_hash"], core.record_content_hash(package, schema)
                )
                node_count, connection_count, buffers, state_bytes = expected_counts[name]
                self.assertEqual(node_count, len(package["nodes"]))
                self.assertEqual(connection_count, len(package["connections"]))
                self.assertEqual(buffers, package["memory_plan"]["buffer_count"])
                self.assertEqual(state_bytes, package["memory_plan"]["state_bytes"])
                self.assertEqual(
                    sorted(package["schedule"]),
                    sorted(node["node_id"] for node in package["nodes"]),
                )
                self.assertEqual(
                    package["schedule"], [node["node_id"] for node in package["nodes"]]
                )
                self.assertEqual(64, package["limits"]["node_count"])
                self.assertEqual(192, package["limits"]["connection_count"])
                self.assertEqual(128, package["limits"]["buffer_count"])
                self.assertEqual(65536, package["limits"]["state_bytes"])
                self.assertEqual(256, package["limits"]["parameter_count"])
                self.assertEqual(1024, package["limits"]["event_count"])
                self.assertFalse(package["authoritative"])
                self.assertTrue(package["derived"])
                encoded = core.canonical_json(package)
                self.assertNotIn(str(ROOT), encoded)
                self.assertNotIn("/Users/", encoded)

        larger_factories = [
            node["factory_id"] for node in self.packages["larger"][0]["nodes"]
        ]
        self.assertEqual(2, larger_factories.count("schuss.rt.soft-q27-v0"))
        self.assertNotEqual(
            self.packages["smaller"][0]["schedule"],
            self.packages["reference"][0]["schedule"],
        )

    def test_lowering_fails_closed_before_publication(self):
        loaded = self.loaded_projects["larger"]
        request_reference = loaded.manifest["build_request_references"][0]
        graph = copy.deepcopy(
            next(
                value
                for value in loaded.context.records["graphs"]
                if value["graph_id"] == "schuss-graph-667107"
            )
        )

        multiple = copy.deepcopy(graph)
        duplicate = copy.deepcopy(multiple["connections"][0])
        duplicate["connection_id"] = "graph-connection-000299"
        multiple["connections"].append(duplicate)
        with self.assertRaises(HostRuntimeError) as captured:
            lower_variable_host_package(
                loaded.context.with_records(graphs=[multiple]),
                project_manifest=loaded.manifest,
                host_build_request_reference=request_reference,
            )
        self.assertEqual("HOST_V1_INPUT_MULTIPLE_DRIVERS", captured.exception.code)

        cyclic = copy.deepcopy(graph)
        cyclic["nodes"] = [
            node
            for node in cyclic["nodes"]
            if node["node_id"] not in {"graph-node-000201", "graph-node-000202"}
        ]
        cyclic["connections"][0]["source"] = {
            "node_id": "graph-node-000204",
            "facet_id": "component-port-000002",
        }
        cyclic["connections"][0]["destination"] = {
            "node_id": "graph-node-000203",
            "facet_id": "component-port-000001",
        }
        cyclic["connections"][1]["source"] = {
            "node_id": "graph-node-000203",
            "facet_id": "component-port-000002",
        }
        cyclic["connections"][1]["destination"] = {
            "node_id": "graph-node-000204",
            "facet_id": "component-port-000001",
        }
        with self.assertRaises(HostRuntimeError) as captured:
            lower_variable_host_package(
                loaded.context.with_records(graphs=[cyclic]),
                project_manifest=loaded.manifest,
                host_build_request_reference=request_reference,
            )
        self.assertEqual("HOST_V1_GRAPH_CYCLE", captured.exception.code)

        wrong_request = {**request_reference, "revision": 2}
        with self.assertRaises(HostRuntimeError) as captured:
            lower_variable_host_package(
                loaded.context,
                project_manifest=loaded.manifest,
                host_build_request_reference=wrong_request,
            )
        self.assertEqual("HOST_V1_BUILD_REQUEST_NOT_SELECTED", captured.exception.code)

    def test_retained_wavs_observations_and_v0_authority_are_exact(self):
        expected_wavs = {
            "smaller": "99388ceb670412a46c6932619ab97e14e80558989adaa83ba01880884b25ef7c",
            "reference": "ae2b8eff76d079b85c74f4d33d555699f8812cb0b72ea459014ee9a90e9ead7c",
            "larger": "586199d4773cb84941752eb6265b525f442e4840a3cbb85346446b677f25b363",
        }
        for name in NAMES:
            with self.subTest(name=name):
                package = self.packages[name][0]
                observation = core.load_json(
                    FIXTURES / f"{name}-offline-observation.json"
                )
                schema = self.context.schemas["host_runtime_observation_v1"]
                self.assertEqual([], core.schema_errors(observation, schema, schema))
                self.assertEqual(
                    observation["content_hash"],
                    core.record_content_hash(observation, schema),
                )
                self.assertEqual(package["content_hash"], observation["package_content_hash"])
                wav = (FIXTURES / f"{name}-output.wav").read_bytes()
                self.assertEqual(48000 * 4 + 44, len(wav))
                self.assertEqual(expected_wavs[name], hashlib.sha256(wav).hexdigest())
                self.assertEqual(expected_wavs[name], observation["output"]["byte_sha256"])
                self.assertFalse(
                    observation["evidence_boundary"]["real_time_level_7_promoted"]
                )
                self.assertFalse(
                    observation["evidence_boundary"]["audible_level_8_promoted"]
                )

        v0_package = (TASK031_FIXTURES / "reference-host-package.json").read_bytes()
        v0_observation = (
            TASK031_FIXTURES / "reference-offline-observation.json"
        ).read_bytes()
        v0_wav = (TASK031_FIXTURES / "reference-output.wav").read_bytes()
        self.assertEqual(
            "d1a67a03c5d064ccdbc8f3d5441224c81afa6e212c800e0affc1a423c07154ae",
            hashlib.sha256(v0_package).hexdigest(),
        )
        self.assertEqual(
            "193af4d22c2c171f1a673c755314ade1f8b3c7ac614dd24d2e5feb42e0a2cb5a",
            hashlib.sha256(v0_observation).hexdigest(),
        )
        self.assertEqual(
            "ae2b8eff76d079b85c74f4d33d555699f8812cb0b72ea459014ee9a90e9ead7c",
            hashlib.sha256(v0_wav).hexdigest(),
        )

    def test_native_offline_renderer_is_block_equivalent_for_every_fixture(self):
        clang = subprocess.run(
            ["/usr/bin/xcrun", "--find", "clang++"], text=True, capture_output=True
        )
        if clang.returncode:
            self.skipTest("Apple Clang is unavailable")
        with tempfile.TemporaryDirectory(prefix="schuss-task032-native-test-") as temporary:
            output = Path(temporary) / "schuss-offline-render"
            sources = [
                "package_parser.cpp",
                "package_parser_v1.cpp",
                "runtime.cpp",
                "runtime_v1.cpp",
                "sha256.cpp",
            ]
            command = [
                "/usr/bin/xcrun", "clang++", "-std=c++17", "-O2", "-Wall",
                "-Wextra", "-Wpedantic", "-Werror", "-I",
                str(ROOT / "packages/schuss_rt/include"),
                *[str(ROOT / "packages/schuss_rt/src" / source) for source in sources],
                str(ROOT / "apps/schuss_audio_engine/src/offline_main.cpp"),
                "-o", str(output),
            ]
            compiled = subprocess.run(command, text=True, capture_output=True)
            self.assertEqual(0, compiled.returncode, compiled.stderr)
            for name in NAMES:
                package = self.packages[name][0]
                retained_wav = (FIXTURES / f"{name}-output.wav").read_bytes()
                for block in (1, 16, 127, 512):
                    wav = Path(temporary) / f"{name}-{block}.wav"
                    observation = Path(temporary) / f"{name}-{block}.json"
                    rendered = subprocess.run(
                        [
                            str(output),
                            "--package", str(FIXTURES / f"{name}-host-package.json"),
                            "--package-hash", package["content_hash"],
                            "--output", str(wav),
                            "--observation", str(observation),
                            "--frames", "48000",
                            "--block", str(block),
                        ],
                        text=True,
                        capture_output=True,
                    )
                    self.assertEqual(0, rendered.returncode, rendered.stderr)
                    self.assertEqual(retained_wav, wav.read_bytes())
                    value = core.load_json(observation)
                    schema = self.context.schemas["host_runtime_observation_v1"]
                    self.assertEqual([], core.schema_errors(value, schema, schema))
                    self.assertEqual(
                        value["content_hash"], core.record_content_hash(value, schema)
                    )


if __name__ == "__main__":
    unittest.main()
