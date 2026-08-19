import copy
import hashlib
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools/contracts"
sys.path[:0] = [str(ROOT), str(TOOLS)]

from packages.schuss_core.application_capabilities import build_application_description
from packages.schuss_core.audio_sessions import (
    AudioSessionService,
    EngineProtocolError,
    dispatch_host_operation,
)
from packages.schuss_core.control_plane import dispatch_operation, load_repository_context
from packages.schuss_core.project_service import ProjectError, ProjectService
from tools.contracts import validator_core as core


RECORD_SET = ROOT / "contracts/record-sets/task031-desktop-host-runtime-v1.json"
FIXTURE_PROJECT = ROOT / "fixtures/task031/reference-project"


def _engine_state(package_hash, *, active):
    return {
        "active": active,
        "block_frames": 128,
        "callback_cpu_ratio_max": "0.010000",
        "callback_duration_us_max": 27,
        "device_name": "Fake CoreAudio",
        "midi_events_delivered": 1,
        "midi_inputs_open": 1,
        "package_content_hash": package_hash,
        "processed_frames": 256,
        "queue_overflows": 0,
        "sample_rate_hz": 48000,
        "xruns": 0,
    }


class FakeEngineTransport:
    def __init__(self, protocol_schema, *, failures=None, handshake=None):
        self.protocol_schema = protocol_schema
        self.failures = dict(failures or {})
        self.handshake = handshake
        self.messages = []
        self.package_hash = None
        self.active = False
        self.closed = False

    def request(self, message):
        self.assert_valid_message(message)
        self.messages.append(copy.deepcopy(message))
        kind = message["message_type"]
        failure = self.failures.get(kind)
        if failure is not None:
            if callable(failure):
                failure = failure()
            raise failure
        if kind == "hello":
            return copy.deepcopy(
                self.handshake
                or {
                    "package_schema_version": "host-runtime-package-v0",
                    "runtime_abi": "schuss-rt-abi-v0",
                }
            )
        if kind == "devices.inspect":
            return {
                "audio_devices": [
                    {"device_type": "CoreAudio", "name": "Fake CoreAudio"}
                ],
                "midi_inputs": [
                    {"identifier": "fake-midi-1", "name": "Fake MIDI"}
                ],
            }
        if kind == "package.prepare":
            self.package_hash = message["payload"]["package_content_hash"]
            return {
                "package_content_hash": self.package_hash,
                "runtime_abi": "schuss-rt-abi-v0",
            }
        if kind == "session.start":
            self.active = True
            return _engine_state(self.package_hash, active=True)
        if kind == "session.inspect":
            return _engine_state(self.package_hash, active=self.active)
        if kind in {"session.stop", "shutdown"}:
            self.active = False
            return _engine_state(self.package_hash or "", active=False)
        raise AssertionError(kind)

    def assert_valid_message(self, message):
        errors = core.schema_errors(message, self.protocol_schema, self.protocol_schema)
        if errors:
            raise AssertionError(errors)

    def close(self):
        self.closed = True
        self.active = False


class FakeFactory:
    def __init__(self, schema, specifications=None):
        self.schema = schema
        self.specifications = list(specifications or [{}])
        self.transports = []

    def __call__(self):
        specification = self.specifications.pop(0) if self.specifications else {}
        transport = FakeEngineTransport(self.schema, **specification)
        self.transports.append(transport)
        return transport


class Task031AudioSessionsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = load_repository_context(ROOT, record_set_path=RECORD_SET)
        cls.protocol_schema = cls.context.schemas["host_engine_protocol"]

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="schuss-task031-audio-test-")
        self.workspace = Path(self.temporary.name) / "project"
        shutil.copytree(FIXTURE_PROJECT, self.workspace)
        self.project_service = ProjectService(self.workspace, repository_root=ROOT)
        loaded = self.project_service.load()
        self.project_reference = {
            "project_id": loaded.manifest["project_id"],
            "revision": loaded.manifest["revision"],
            "content_hash": loaded.manifest["content_hash"],
        }

    def tearDown(self):
        self.temporary.cleanup()

    def _files(self):
        return {
            str(path.relative_to(self.workspace)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(self.workspace.rglob("*"))
            if path.is_file()
        }

    def _service(self, specifications=None):
        factory = FakeFactory(self.protocol_schema, specifications)
        return AudioSessionService(self.project_service, factory), factory

    def test_device_enumeration_requires_explicit_operation_and_exact_handshake(self):
        service, factory = self._service()
        self.assertEqual([], factory.transports)
        value = service.inspect_devices(
            inspection_intent="enumerate-local-audio-midi"
        )
        self.assertEqual("identity-enumeration-only", value["device_action_performed"])
        self.assertEqual("Fake CoreAudio", value["audio_devices"][0]["name"])
        self.assertEqual(
            ["hello", "devices.inspect"],
            [message["message_type"] for message in factory.transports[0].messages],
        )
        with self.assertRaisesRegex(ValueError, "explicit local audio/MIDI"):
            service.inspect_devices(inspection_intent="implicit")
        service.close()

    def test_start_inspect_stop_snapshots_project_and_never_mutates_it(self):
        before = self._files()
        service, factory = self._service()
        started = service.start(
            project_reference=self.project_reference,
            sample_rate_hz=48000,
            block_frames=128,
            start_intent="start-local-audio-session",
        )
        self.assertEqual("active", started["status"])
        self.assertEqual(self.project_reference, started["project_reference"])
        self.assertFalse(started["authoritative_records_mutated"])

        def forbidden_reload(*args, **kwargs):
            raise AssertionError("active session must not silently retarget")

        self.project_service.load = forbidden_reload
        inspected = service.inspect(started["audio_session_id"])
        stopped = service.stop(
            started["audio_session_id"],
            stop_intent="stop-local-audio-session",
        )
        self.assertEqual(started["package_content_hash"], inspected["package_content_hash"])
        self.assertEqual("stopped", stopped["status"])
        self.assertEqual(
            ["hello", "package.prepare", "session.start", "session.inspect", "session.stop"],
            [message["message_type"] for message in factory.transports[0].messages],
        )
        self.assertEqual(before, self._files())
        service.close()

    def test_exact_project_and_process_local_handle_boundaries_fail_closed(self):
        service, _ = self._service()
        wrong = {**self.project_reference, "revision": self.project_reference["revision"] + 1}
        with self.assertRaisesRegex(ValueError, "not the accepted workspace head"):
            service.start(
                project_reference=wrong,
                sample_rate_hz=48000,
                block_frames=128,
                start_intent="start-local-audio-session",
            )
        with self.assertRaisesRegex(ValueError, "absent or belongs to another"):
            service.inspect("audio-session-999999")
        other_service, _ = self._service()
        started = service.start(
            project_reference=self.project_reference,
            sample_rate_hz=48000,
            block_frames=128,
            start_intent="start-local-audio-session",
        )
        with self.assertRaisesRegex(ValueError, "absent or belongs to another"):
            other_service.inspect(started["audio_session_id"])
        service.close()
        other_service.close()

    def test_protocol_prepare_start_crash_and_stop_failures_are_contained(self):
        cases = {
            "handshake": [{"handshake": {"runtime_abi": "wrong", "package_schema_version": "host-runtime-package-v0"}}],
            "prepare": [{"failures": {"package.prepare": EngineProtocolError("ENGINE_PREPARE_FAILED", "prepare rejected")}}],
            "start": [{"failures": {"session.start": EngineProtocolError("ENGINE_START_FAILED", "start rejected")}}],
        }
        for name, specifications in cases.items():
            with self.subTest(name=name):
                before = self._files()
                service, factory = self._service(specifications)
                with self.assertRaises(EngineProtocolError):
                    service.start(
                        project_reference=self.project_reference,
                        sample_rate_hz=48000,
                        block_frames=128,
                        start_intent="start-local-audio-session",
                    )
                self.assertTrue(factory.transports[0].closed)
                self.assertEqual(before, self._files())
                service.close()

        crash = EngineProtocolError(
            "ENGINE_PROCESS_DISCONNECTED",
            "engine disconnected",
            status="unavailable",
        )
        service, factory = self._service([{"failures": {"session.inspect": crash}}, {}])
        started = service.start(
            project_reference=self.project_reference,
            sample_rate_hz=48000,
            block_frames=128,
            start_intent="start-local-audio-session",
        )
        with self.assertRaisesRegex(EngineProtocolError, "disconnected"):
            service.inspect(started["audio_session_id"])
        self.assertTrue(factory.transports[0].closed)
        restarted = service.start(
            project_reference=self.project_reference,
            sample_rate_hz=48000,
            block_frames=128,
            start_intent="start-local-audio-session",
        )
        self.assertNotEqual(started["engine_generation"], restarted["engine_generation"])
        with self.assertRaisesRegex(ValueError, "expired native engine generation"):
            service.inspect(started["audio_session_id"])
        service.close()

        stop_failure = EngineProtocolError("ENGINE_STOP_FAILED", "stop rejected")
        service, factory = self._service([{"failures": {"session.stop": stop_failure}}])
        started = service.start(
            project_reference=self.project_reference,
            sample_rate_hz=48000,
            block_frames=128,
            start_intent="start-local-audio-session",
        )
        with self.assertRaisesRegex(EngineProtocolError, "stop rejected"):
            service.stop(started["audio_session_id"], stop_intent="stop-local-audio-session")
        self.assertTrue(factory.transports[0].closed)
        service.close()

    def test_v14_dispatch_and_capability_availability(self):
        service, _ = self._service()
        request = {
            "schema_version": "schuss-operation-request-v14",
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": "audio.session.start",
            "payload": {
                "project_reference": self.project_reference,
                "sample_rate_hz": 48000,
                "block_frames": 128,
                "start_intent": "start-local-audio-session",
            },
        }
        result = dispatch_operation(
            request,
            self.context,
            audio_session_service=service,
        )
        self.assertEqual("success", result["status"])
        self.assertEqual([], core.schema_errors(result, self.context.schemas["operation_result_v14"], self.context.schemas["operation_result_v14"]))
        unavailable = dispatch_host_operation(request, self.context, None, None)
        self.assertEqual("unavailable", unavailable["status"])
        self.assertEqual("AUDIO_SESSION_SERVICE_UNAVAILABLE", unavailable["diagnostics"][0]["code"])
        service.close()
        malformed_service, _ = self._service()
        malformed = dispatch_host_operation(
            {**request, "payload": {**request["payload"], "block_frames": 513}},
            self.context,
            None,
            malformed_service,
        )
        self.assertEqual("invalid", malformed["status"])

        path_safe_service, _ = self._service()
        def failing_load():
            raise ProjectError(
                "PROJECT_LOAD_FAILED",
                "/private/workspace/path must not escape",
            )

        path_safe_service.project_service.load = failing_load
        path_safe = dispatch_host_operation(
            request,
            self.context,
            None,
            path_safe_service,
        )
        self.assertEqual("invalid", path_safe["status"])
        self.assertEqual("the accepted project could not be loaded", path_safe["diagnostics"][0]["message"])
        self.assertNotIn("/private/", core.canonical_json(path_safe))
        path_safe_service.close()

        description = build_application_description(
            record_set_reference=self.context.record_set_reference,
            schemas=self.context.schemas,
            host_runtime_service_available=True,
            audio_session_service_available=True,
        )
        operations = {value["operation"]: value for value in description["operations"]}
        self.assertEqual("available", operations["host.render.start"]["availability"])
        self.assertEqual("available", operations["audio.session.start"]["availability"])
        malformed_service.close()


if __name__ == "__main__":
    unittest.main()
