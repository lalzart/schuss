from __future__ import annotations

import copy
import hashlib
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools/contracts"
sys.path[:0] = [str(ROOT), str(TOOLS)]

from packages.schuss_core.application_capabilities import build_application_description
from packages.schuss_core.audio_sessions import EngineProtocolError, HostSessionError
from packages.schuss_core.control_plane import dispatch_operation, load_repository_context
from packages.schuss_core.project_service import ProjectService
from packages.schuss_core.variable_audio_sessions import VariableAudioSessionService
from tools.contracts import validator_core as core


RECORD_SET = ROOT / "contracts/record-sets/task032-variable-host-runtime-v1.json"
FIXTURES = ROOT / "fixtures/task032"


def _project_reference(manifest):
    return {
        "project_id": manifest["project_id"],
        "revision": manifest["revision"],
        "content_hash": manifest["content_hash"],
    }


def _engine_state(package_hash, generation, *, active):
    return {
        "active": active,
        "block_frames": 128,
        "callback_cpu_ratio_max": "0.010000",
        "callback_duration_us_max": 27,
        "device_disconnects": 0,
        "device_name": "Fake CoreAudio",
        "engine_generation": generation,
        "midi_events_delivered": 1,
        "midi_inputs_open": 1,
        "package_content_hash": package_hash,
        "processed_frames": 256,
        "queue_overflows": 0,
        "sample_rate_hz": 48000,
        "xruns": 0,
    }


class FakeVariableEngineTransport:
    def __init__(self, protocol_schema, *, failures=None):
        self.protocol_schema = protocol_schema
        self.failures = dict(failures or {})
        self.messages = []
        self.package_hash = ""
        self.pending_hash = ""
        self.generation = 1
        self.active = False
        self.closed = False
        self.on_prepare = None

    def request(self, message):
        errors = core.schema_errors(message, self.protocol_schema, self.protocol_schema)
        if errors:
            raise AssertionError(errors)
        self.messages.append(copy.deepcopy(message))
        kind = message["message_type"]
        failure = self.failures.get(kind)
        if failure is not None:
            if callable(failure):
                failure = failure()
            raise failure
        payload = message["payload"]
        if kind == "hello":
            return {
                "package_schema_version": "host-runtime-package-v1",
                "runtime_abi": "schuss-rt-abi-v1",
            }
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
            self.package_hash = payload["package_content_hash"]
            return {
                "package_content_hash": self.package_hash,
                "runtime_abi": "schuss-rt-abi-v1",
            }
        if kind == "session.start":
            self.active = True
            return _engine_state(self.package_hash, self.generation, active=True)
        if kind == "session.inspect":
            return _engine_state(self.package_hash, self.generation, active=self.active)
        if kind in {"session.stop", "shutdown"}:
            self.active = False
            return _engine_state(self.package_hash, self.generation, active=False)
        if kind == "replacement.prepare":
            if self.on_prepare is not None:
                self.on_prepare()
            if payload["expected_engine_generation"] != self.generation:
                raise EngineProtocolError("ENGINE_GENERATION_STALE", "stale generation")
            if payload["expected_active_package_content_hash"] != self.package_hash:
                raise EngineProtocolError("ENGINE_ACTIVE_HASH_STALE", "stale active hash")
            if self.pending_hash:
                raise EngineProtocolError("ENGINE_REPLACEMENT_PENDING", "already pending")
            self.pending_hash = payload["successor_package_content_hash"]
            return {
                "active_package_content_hash": self.package_hash,
                "engine_generation": self.generation,
                "pending_package_content_hash": self.pending_hash,
                "runtime_abi": "schuss-rt-abi-v1",
            }
        if kind == "replacement.activate":
            if payload["expected_engine_generation"] != self.generation:
                raise EngineProtocolError("ENGINE_GENERATION_STALE", "stale generation")
            if payload["expected_active_package_content_hash"] != self.package_hash:
                raise EngineProtocolError("ENGINE_ACTIVE_HASH_STALE", "stale active hash")
            if payload["successor_package_content_hash"] != self.pending_hash:
                raise EngineProtocolError("ENGINE_SUCCESSOR_HASH_STALE", "stale successor")
            old_hash = self.package_hash
            self.package_hash = self.pending_hash
            self.pending_hash = ""
            self.generation += 1
            return {
                **_engine_state(self.package_hash, self.generation, active=True),
                "activation_boundary": "audio-block-boundary",
                "old_package_content_hash": old_hash,
                "reset_state": True,
                "retired_runtime_reclaimed_off_callback": True,
            }
        if kind == "replacement.cancel":
            self.pending_hash = ""
            return {
                "active_package_content_hash": self.package_hash,
                "engine_generation": self.generation,
                "pending": False,
            }
        raise AssertionError(kind)

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
        transport = FakeVariableEngineTransport(self.schema, **specification)
        self.transports.append(transport)
        return transport


class Task032VariableAudioSessionsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = load_repository_context(ROOT, record_set_path=RECORD_SET)
        cls.services = {
            name: ProjectService(
                FIXTURES / f"{name}-project",
                repository_root=ROOT,
                initial_context=cls.context,
            )
            for name in ("smaller", "reference", "larger")
        }
        cls.loaded = {name: service.load() for name, service in cls.services.items()}
        cls.project_references = {
            name: _project_reference(loaded.manifest)
            for name, loaded in cls.loaded.items()
        }
        cls.request_references = {
            name: loaded.manifest["build_request_references"][0]
            for name, loaded in cls.loaded.items()
        }
        cls.service_by_project = {
            reference["project_id"]: cls.services[name]
            for name, reference in cls.project_references.items()
        }
        cls.protocol_schema = cls.context.schemas["host_engine_protocol_v1"]

    @classmethod
    def _resolver(cls, reference):
        service = cls.service_by_project.get(reference.get("project_id"))
        if service is None:
            raise HostSessionError(
                "HOST_V1_PROJECT_UNKNOWN", "successor project is not available"
            )
        return service

    def _service(self, specifications=None):
        factory = FakeFactory(self.protocol_schema, specifications)
        service = VariableAudioSessionService(
            self.services["smaller"],
            factory,
            project_resolver=self._resolver,
        )
        return service, factory

    @staticmethod
    def _workspace_hashes(service):
        return {
            str(path.relative_to(service.workspace)): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in sorted(service.workspace.rglob("*"))
            if path.is_file()
        }

    def _start_smaller(self, service):
        return service.start(
            project_reference=self.project_references["smaller"],
            host_build_request_reference=self.request_references["smaller"],
            sample_rate_hz=48000,
            block_frames=128,
            start_intent="start-local-audio-session",
        )

    def test_devices_start_inspect_and_stop_use_v1_without_project_mutation(self):
        before = self._workspace_hashes(self.services["smaller"])
        service, factory = self._service()
        devices = service.inspect_devices(
            inspection_intent="enumerate-local-audio-midi"
        )
        self.assertEqual("identity-enumeration-only", devices["device_action_performed"])
        started = self._start_smaller(service)
        self.assertEqual("active", started["status"])
        self.assertEqual(1, started["engine_generation"])
        self.assertEqual(self.project_references["smaller"], started["project_reference"])
        inspected = service.inspect(started["audio_session_id"])
        stopped = service.stop(
            started["audio_session_id"], stop_intent="stop-local-audio-session"
        )
        self.assertEqual(started["package_content_hash"], inspected["package_content_hash"])
        self.assertEqual("stopped", stopped["status"])
        self.assertEqual(
            [
                "hello",
                "devices.inspect",
                "package.prepare",
                "session.start",
                "session.inspect",
                "session.stop",
            ],
            [message["message_type"] for message in factory.transports[0].messages],
        )
        self.assertEqual(before, self._workspace_hashes(self.services["smaller"]))
        service.close()

    def test_valid_successor_activates_once_with_reset_state_telemetry(self):
        before = {
            name: self._workspace_hashes(project_service)
            for name, project_service in self.services.items()
        }
        service, factory = self._service()
        started = self._start_smaller(service)
        replaced = service.replace(
            audio_session_id=started["audio_session_id"],
            expected_engine_generation=started["engine_generation"],
            expected_active_package_content_hash=started["package_content_hash"],
            successor_project_reference=self.project_references["larger"],
            successor_host_build_request_reference=self.request_references["larger"],
            replacement_intent="prepare-and-activate-next-block-reset-state",
        )
        self.assertEqual(2, replaced["engine_generation"])
        self.assertEqual(self.project_references["larger"], replaced["project_reference"])
        self.assertNotEqual(started["package_content_hash"], replaced["package_content_hash"])
        telemetry = replaced["last_replacement"]
        self.assertEqual(started["package_content_hash"], telemetry["old_package_content_hash"])
        self.assertEqual(replaced["package_content_hash"], telemetry["new_package_content_hash"])
        self.assertEqual("audio-block-boundary", telemetry["activation_boundary"])
        self.assertEqual("reset-state", telemetry["state_policy"])
        self.assertTrue(telemetry["retired_runtime_reclaimed_off_callback"])
        self.assertFalse(telemetry["authoritative_records_mutated"])
        self.assertEqual(
            ["replacement.prepare", "replacement.activate"],
            [
                message["message_type"]
                for message in factory.transports[0].messages[-2:]
            ],
        )
        for name, project_service in self.services.items():
            self.assertEqual(before[name], self._workspace_hashes(project_service))
        service.close()

    def test_stale_and_failed_replacements_preserve_the_active_graph(self):
        service, factory = self._service()
        started = self._start_smaller(service)
        cases = (
            {
                "expected_engine_generation": 2,
                "expected_active_package_content_hash": started["package_content_hash"],
                "code": "AUDIO_REPLACEMENT_GENERATION_STALE",
            },
            {
                "expected_engine_generation": 1,
                "expected_active_package_content_hash": "sha256:" + "0" * 64,
                "code": "AUDIO_REPLACEMENT_ACTIVE_HASH_STALE",
            },
        )
        for case in cases:
            with self.subTest(code=case["code"]):
                with self.assertRaises(HostSessionError) as captured:
                    service.replace(
                        audio_session_id=started["audio_session_id"],
                        expected_engine_generation=case["expected_engine_generation"],
                        expected_active_package_content_hash=case[
                            "expected_active_package_content_hash"
                        ],
                        successor_project_reference=self.project_references["larger"],
                        successor_host_build_request_reference=self.request_references[
                            "larger"
                        ],
                        replacement_intent="prepare-and-activate-next-block-reset-state",
                    )
                self.assertEqual(case["code"], captured.exception.code)

        activation_failure = EngineProtocolError(
            "ENGINE_ACTIVATION_REJECTED", "activation rejected"
        )
        factory.transports[0].failures["replacement.activate"] = activation_failure
        with self.assertRaises(EngineProtocolError):
            service.replace(
                audio_session_id=started["audio_session_id"],
                expected_engine_generation=1,
                expected_active_package_content_hash=started["package_content_hash"],
                successor_project_reference=self.project_references["larger"],
                successor_host_build_request_reference=self.request_references["larger"],
                replacement_intent="prepare-and-activate-next-block-reset-state",
            )
        inspected = service.inspect(started["audio_session_id"])
        self.assertEqual(1, inspected["engine_generation"])
        self.assertEqual(started["package_content_hash"], inspected["package_content_hash"])
        self.assertEqual("none", inspected["replacement_status"])
        self.assertEqual(
            "replacement.cancel", factory.transports[0].messages[-2]["message_type"]
            if factory.transports[0].messages[-1]["message_type"] == "session.inspect"
            else factory.transports[0].messages[-1]["message_type"],
        )
        service.close()

    def test_one_pending_successor_is_enforced_without_a_blocking_service_lock(self):
        service, factory = self._service()
        started = self._start_smaller(service)
        concurrent_error = []

        def attempt_concurrent():
            factory.transports[0].on_prepare = None
            try:
                service.replace(
                    audio_session_id=started["audio_session_id"],
                    expected_engine_generation=1,
                    expected_active_package_content_hash=started["package_content_hash"],
                    successor_project_reference=self.project_references["reference"],
                    successor_host_build_request_reference=self.request_references[
                        "reference"
                    ],
                    replacement_intent="prepare-and-activate-next-block-reset-state",
                )
            except HostSessionError as error:
                concurrent_error.append(error)

        factory.transports[0].on_prepare = attempt_concurrent
        replaced = service.replace(
            audio_session_id=started["audio_session_id"],
            expected_engine_generation=1,
            expected_active_package_content_hash=started["package_content_hash"],
            successor_project_reference=self.project_references["larger"],
            successor_host_build_request_reference=self.request_references["larger"],
            replacement_intent="prepare-and-activate-next-block-reset-state",
        )
        self.assertEqual(2, replaced["engine_generation"])
        self.assertEqual(1, len(concurrent_error))
        self.assertEqual(
            "AUDIO_REPLACEMENT_ALREADY_PENDING", concurrent_error[0].code
        )
        service.close()

    def test_v16_dispatch_is_schema_valid_and_reports_stable_failures(self):
        service, _ = self._service()
        request = {
            "schema_version": "schuss-operation-request-v16",
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": "audio.session.start",
            "payload": {
                "project_reference": self.project_references["smaller"],
                "host_build_request_reference": self.request_references["smaller"],
                "sample_rate_hz": 48000,
                "block_frames": 128,
                "start_intent": "start-local-audio-session",
            },
        }
        result = dispatch_operation(
            request, self.context, audio_session_service=service
        )
        schema = self.context.schemas["operation_result_v16"]
        self.assertEqual("success", result["status"])
        self.assertEqual([], core.schema_errors(result, schema, schema))
        unavailable = dispatch_operation(request, self.context)
        self.assertEqual("unavailable", unavailable["status"])
        self.assertEqual(
            "AUDIO_SESSION_SERVICE_UNAVAILABLE",
            unavailable["diagnostics"][0]["code"],
        )
        malformed = dispatch_operation(
            {
                **request,
                "payload": {**request["payload"], "block_frames": 513},
            },
            self.context,
            audio_session_service=service,
        )
        self.assertEqual("invalid", malformed["status"])
        self.assertEqual([], core.schema_errors(malformed, schema, schema))
        description = build_application_description(
            record_set_reference=self.context.record_set_reference,
            schemas=self.context.schemas,
            host_runtime_service_available=True,
            audio_session_service_available=True,
        )
        operations = {item["operation"]: item for item in description["operations"]}
        self.assertEqual("available", operations["audio.session.replace"]["availability"])
        service.close()


if __name__ == "__main__":
    unittest.main()
