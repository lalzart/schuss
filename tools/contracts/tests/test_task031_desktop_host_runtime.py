import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools/contracts"
sys.path[:0] = [str(ROOT), str(TOOLS)]

from packages.schuss_core.application_capabilities import build_application_description
from packages.schuss_core.audio_sessions import HostRenderService
from packages.schuss_core.control_plane import load_repository_context, with_compiler_schemas
from packages.schuss_core.effects_profile_frontend import semantic_profile_signature
from packages.schuss_core.host_runtime import HostRuntimeError, lower_host_package
from packages.schuss_core.project_service import ProjectService, with_project_schemas
from tools.contracts import record_set_rules
from tools.contracts import validator_core as core


RECORD_SET = ROOT / "contracts/record-sets/task031-desktop-host-runtime-v1.json"
WORKSPACE_RECORD_SET = ROOT / "contracts/record-sets/ui-desktop-workspace-shell-v1.json"
FIXTURES = ROOT / "fixtures/task031"


class Task031DesktopHostRuntimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = with_compiler_schemas(
            with_project_schemas(
                load_repository_context(ROOT, record_set_path=RECORD_SET), ROOT
            ),
            ROOT,
        )
        cls.project = ProjectService(
            FIXTURES / "reference-project", repository_root=ROOT
        ).load()
        cls.project_reference = {
            "project_id": cls.project.manifest["project_id"],
            "revision": cls.project.manifest["revision"],
            "content_hash": cls.project.manifest["content_hash"],
        }

    def test_record_set_is_parent_preserving_and_allocations_are_exact(self):
        loaded = record_set_rules.load_record_set(ROOT, RECORD_SET)
        parent = record_set_rules.load_record_set(
            ROOT, ROOT / "contracts/record-sets/ai-sonic-authoring-v1.json"
        )
        self.assertEqual(
            {"status": "included", **parent.reference}, loaded.manifest["parent_reference"]
        )
        parent_members = {
            tuple(value[key] for key in ("record_kind", "stable_id", "revision", "content_hash", "portable_path", "byte_sha256"))
            for value in parent.manifest["record_members"]
        }
        current_members = {
            tuple(value[key] for key in ("record_kind", "stable_id", "revision", "content_hash", "portable_path", "byte_sha256"))
            for value in loaded.manifest["record_members"]
        }
        self.assertTrue(parent_members <= current_members)
        self.assertEqual(455, len(loaded.manifest["record_members"]))
        host_bindings = {
            value["implementation_id"]
            for value in self.context.records["bindings"]
            if value["implementation_id"] >= "schuss-implementation-000162"
        }
        self.assertEqual(
            {f"schuss-implementation-{value:06d}" for value in range(162, 169)},
            host_bindings,
        )
        host_eligibility = {
            value["binding_eligibility_id"]
            for value in self.context.records["eligibility"]
            if value["binding_eligibility_id"] >= "schuss-binding-eligibility-000048"
        }
        self.assertEqual(
            {f"schuss-binding-eligibility-{value:06d}" for value in range(48, 55)},
            host_eligibility,
        )

    def test_schemas_generators_and_workspace_successor_are_fresh(self):
        for command in (
            [sys.executable, "tools/contracts/generate_task031_records.py", "--check"],
            [sys.executable, "tools/contracts/generate_task031_fixtures.py", "--check"],
            [sys.executable, "tools/contracts/generate_desktop_workspace_shell_records.py", "--check"],
        ):
            completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(0, completed.returncode, completed.stderr)
        workspace = core.load_json(WORKSPACE_RECORD_SET)
        self.assertEqual("schuss-record-set-000028", workspace["record_set_id"])
        self.assertEqual(
            {"status": "included", **self.context.record_set_reference},
            workspace["parent_reference"],
        )
        for name in (
            "application_capability_description_v7",
            "compute_target_v1",
            "host_engine_protocol",
            "host_runtime_observation",
            "host_runtime_package",
            "operation_request_v14",
            "operation_result_v14",
            "third_party_source_lock",
        ):
            self.assertEqual([], core.validate_schema_annotations(self.context.schemas[name]))

    def test_application_description_has_exact_host_surface(self):
        description = build_application_description(
            record_set_reference=self.context.record_set_reference,
            schemas=self.context.schemas,
        )
        operations = {value["operation"]: value for value in description["operations"]}
        self.assertEqual("schuss-application-capability-description-v7", description["description_version"])
        self.assertEqual(41, len(operations))
        expected = {
            "host.render.start",
            "host.render.inspect",
            "audio.devices.inspect",
            "audio.session.start",
            "audio.session.inspect",
            "audio.session.stop",
        }
        self.assertEqual(expected, expected & operations.keys())
        self.assertEqual("requires-host-runtime-service", operations["host.render.start"]["availability"])
        self.assertEqual("requires-audio-session-service", operations["audio.session.start"]["availability"])

    def test_exact_project_lowers_deterministically_to_seven_host_bindings(self):
        first, first_plan = lower_host_package(
            self.context, project_reference=self.project_reference
        )
        second, second_plan = lower_host_package(
            self.context, project_reference=self.project_reference
        )
        self.assertEqual(first, second)
        self.assertEqual(first_plan, second_plan)
        self.assertEqual(
            core.load_json(FIXTURES / "reference-host-package.json"), first
        )
        self.assertEqual([], core.schema_errors(first, self.context.schemas["host_runtime_package"], self.context.schemas["host_runtime_package"]))
        self.assertEqual(first["content_hash"], core.record_content_hash(first, self.context.schemas["host_runtime_package"]))
        self.assertEqual(7, len(first["nodes"]))
        self.assertEqual(7, len(first["connections"]))
        self.assertEqual(
            [f"schuss-implementation-{value:06d}" for value in range(162, 169)],
            [value["binding_reference"]["implementation_id"] for value in first["nodes"]],
        )
        self.assertEqual([2] * 7, [value["binding_reference"]["revision"] for value in first["nodes"]])
        self.assertFalse(first["authoritative"])
        self.assertTrue(first["derived"])
        encoded = core.canonical_json(first)
        self.assertNotIn(str(ROOT), encoded)
        self.assertNotIn("/Users/", encoded)
        for forbidden_key in ("timestamp", "process_id", "ui_layout", "tauri_state", "python_object"):
            self.assertNotIn(f'"{forbidden_key}"', encoded)

    def test_lowering_fails_closed_for_missing_duplicate_and_unsupported_inputs(self):
        missing = self.context.with_records(
            bindings=[
                value
                for value in self.context.records["bindings"]
                if value["implementation_id"] != "schuss-implementation-000162"
            ]
        )
        with self.assertRaisesRegex(HostRuntimeError, "ELIGIBILITY_BINDING_REFERENCE_UNRESOLVED"):
            lower_host_package(missing, project_reference=self.project_reference)
        duplicate = self.context.with_records(
            bindings=[
                *self.context.records["bindings"],
                next(
                    value
                    for value in self.context.records["bindings"]
                    if value["implementation_id"] == "schuss-implementation-000162"
                ),
            ]
        )
        with self.assertRaisesRegex(HostRuntimeError, "COMPILER_ID_REVISION_DUPLICATE"):
            lower_host_package(duplicate, project_reference=self.project_reference)
        graph = copy.deepcopy(
            next(
                value
                for value in self.context.records["graphs"]
                if value["graph_id"] == "schuss-graph-000006"
                and value["revision"] == 1
            )
        )
        graph["connections"] = graph["connections"][:-1]
        with self.assertRaisesRegex(ValueError, "EFFECTS_PROFILE_CONNECTIONS_UNSUPPORTED"):
            semantic_profile_signature(graph)
        with self.assertRaises(HostRuntimeError) as captured:
            lower_host_package(self.context, project_reference={"project_id": "schuss-project-000031"})
        self.assertEqual("HOST_PROJECT_REFERENCE_INVALID", captured.exception.code)

    def test_retained_observation_and_wav_are_exact_and_bounded(self):
        observation = core.load_json(FIXTURES / "reference-offline-observation.json")
        schema = self.context.schemas["host_runtime_observation"]
        self.assertEqual([], core.schema_errors(observation, schema, schema))
        self.assertEqual(observation["content_hash"], core.record_content_hash(observation, schema))
        wav = (FIXTURES / "reference-output.wav").read_bytes()
        self.assertEqual(48000 * 4 + 44, len(wav))
        self.assertEqual(hashlib.sha256(wav).hexdigest(), observation["output"]["byte_sha256"])
        self.assertEqual("offline-render", observation["observation_kind"])
        self.assertEqual({"status": "not-opened"}, observation["device"])
        self.assertFalse(observation["evidence_boundary"]["real_time_level_7_promoted"])
        self.assertFalse(observation["evidence_boundary"]["audible_level_8_promoted"])

        smoke = core.load_json(FIXTURES / "local-mac-smoke-observation.json")
        package = core.load_json(FIXTURES / "reference-host-package.json")
        self.assertEqual([], core.schema_errors(smoke, schema, schema))
        self.assertEqual(smoke["content_hash"], core.record_content_hash(smoke, schema))
        self.assertEqual("local-real-time-smoke", smoke["observation_kind"])
        self.assertEqual("success", smoke["status"])
        self.assertEqual(package["content_hash"], smoke["package_content_hash"])
        self.assertEqual(48000, smoke["configuration"]["sample_rate_hz"])
        self.assertEqual(128, smoke["configuration"]["block_frames"])
        self.assertEqual("opened", smoke["device"]["status"])
        self.assertEqual(0, smoke["output"]["byte_length"])
        self.assertEqual(0, smoke["metrics"]["queue_overflows"])
        self.assertEqual(0, smoke["metrics"]["xruns"])
        self.assertFalse(smoke["evidence_boundary"]["real_time_level_7_promoted"])
        self.assertFalse(smoke["evidence_boundary"]["audible_level_8_promoted"])

    def test_native_runtime_build_and_offline_render_match_retained_bytes(self):
        clang = subprocess.run(
            ["/usr/bin/xcrun", "--find", "clang++"], text=True, capture_output=True
        )
        if clang.returncode:
            self.skipTest("Apple Clang is unavailable")
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "schuss-offline-render"
            command = [
                "/usr/bin/xcrun", "clang++", "-std=c++17", "-O2", "-Wall", "-Wextra",
                "-Wpedantic", "-Werror", "-I", str(ROOT / "packages/schuss_rt/include"),
                "-I", str(ROOT / "apps/schuss_audio_engine/src"),
                str(ROOT / "packages/schuss_rt/src/package_parser.cpp"),
                str(ROOT / "packages/schuss_rt/src/runtime.cpp"),
                str(ROOT / "packages/schuss_rt/src/sha256.cpp"),
                str(ROOT / "apps/schuss_audio_engine/src/offline_main.cpp"),
                "-o", str(output),
            ]
            compiled = subprocess.run(command, text=True, capture_output=True)
            self.assertEqual(0, compiled.returncode, compiled.stderr)
            package = core.load_json(FIXTURES / "reference-host-package.json")
            for block in (1, 16, 127, 512):
                wav = Path(temporary) / f"output-{block}.wav"
                observation = Path(temporary) / f"observation-{block}.json"
                rendered = subprocess.run(
                    [
                        str(output), "--package", str(FIXTURES / "reference-host-package.json"),
                        "--package-hash", package["content_hash"], "--output", str(wav),
                        "--observation", str(observation), "--frames", "48000", "--block", str(block),
                    ],
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(0, rendered.returncode, rendered.stderr)
                self.assertEqual((FIXTURES / "reference-output.wav").read_bytes(), wav.read_bytes())
                value = core.load_json(observation)
                self.assertEqual(
                    [],
                    core.schema_errors(
                        value,
                        self.context.schemas["host_runtime_observation"],
                        self.context.schemas["host_runtime_observation"],
                    ),
                )
                if block == 127:
                    self.assertEqual(
                        (FIXTURES / "reference-offline-observation.json").read_bytes(),
                        observation.read_bytes(),
                    )

            service = HostRenderService(
                ProjectService(FIXTURES / "reference-project", repository_root=ROOT),
                output,
            )
            session = service.start(
                project_reference=self.project_reference,
                render_frames=48000,
                block_frames=127,
                render_intent="offline-render",
            )
            self.assertEqual("success", session["status"])
            self.assertEqual(package["content_hash"], session["package_content_hash"])
            self.assertEqual(session, service.inspect(session["render_session_id"]))
            self.assertFalse(session["authoritative_records_mutated"])
            self.assertFalse(session["device_actions_performed"])
            service.close()


if __name__ == "__main__":
    unittest.main()
