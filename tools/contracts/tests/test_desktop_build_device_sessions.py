from __future__ import annotations

import hashlib
from pathlib import Path
import struct
import time
import subprocess
import sys
from threading import Event
from types import SimpleNamespace
import unittest


ROOT = Path(__file__).resolve().parents[3]

from packages.schuss_core.build_execution import (  # noqa: E402
    ExecutionService,
    HandlerRegistration,
    descriptor_content_hash,
)
from packages.schuss_core.build_sessions import (  # noqa: E402
    BuildSessionError,
    BuildSessionService,
)
from packages.schuss_core.compiler_front_half import CompilationContext  # noqa: E402
from packages.schuss_core.control_plane import (  # noqa: E402
    dispatch_operation,
    load_repository_context,
    with_compiler_schemas,
)
from packages.schuss_core.device_sessions import (  # noqa: E402
    DeviceSessionError,
    DeviceSessionService,
)
from packages.schuss_core.ksoloti_usb import (  # noqa: E402
    KSOLOTI_BULK_INTERFACES,
    PATCH_LOAD_ADDRESS,
    UPLOAD_CHUNK_SIZE,
    KsolotiUSBError,
    KsolotiUSBTransport,
)


REQUEST_REFERENCE = {
    "build_request_id": "schuss-build-request-000005",
    "revision": 1,
    "content_hash": "sha256:8f40ac2f996f32f10f59b862da566f1d66f145cdf1780f29d786c9b2f42f03c2",
}
PROJECT_REFERENCE = {
    "project_id": "schuss-project-900001",
    "revision": 1,
    "content_hash": "sha256:" + "9" * 64,
}


def _registration(backend_reference: dict) -> HandlerRegistration:
    descriptor = {
        "schema_version": "build-handler-descriptor-v1",
        "canonical_profile": "schuss-canonical-json-v1",
        "build_handler_id": "schuss-build-handler-900001",
        "revision": 1,
        "content_hash": "sha256:" + "0" * 64,
        "backend_reference": backend_reference,
        "adapter_kind": "direct",
        "execution_policy": "exact-semantic-profile",
        "supported_semantic_profile": {
            "profile_id": "schuss-semantic-profile-900001",
            "version": 1,
            "content_hash": "sha256:" + "8" * 64,
        },
        "mid_handler_cancellation": False,
    }
    descriptor["content_hash"] = descriptor_content_hash(descriptor)

    def handler(request):
        payload = b"desktop-session-test-elf"
        digest = hashlib.sha256(payload).hexdigest()
        destination = request.output_root / "artifacts/sha256" / digest
        destination.parent.mkdir(parents=True)
        destination.write_bytes(payload)
        return {
            "status": "success",
            "stage_outcomes": [
                {"stage": "backend-lowering", "status": "success"},
                {"stage": "target-compile-link", "status": "success"},
            ],
            "artifacts": [
                {
                    "artifact_kind": "target-executable",
                    "media_type": "application/x-elf",
                    "producer_stage": "target-compile-link",
                    "byte_sha256": digest,
                    "byte_length": len(payload),
                    "portable_locator": "sha256/" + digest,
                }
            ],
            "evidence_level": 5,
        }

    return HandlerRegistration(descriptor, handler)


class FakeTransport:
    def __init__(self, *, firmware_crc: str = "5021D42A", fail_upload: bool = False):
        self.firmware_crc = firmware_crc
        self.fail_upload = fail_upload
        self.uploads = []

    def discover(self):
        return [
            {
                "transport_locator": "usb:bus-001/ports-2.3",
                "vendor_id": 0x16C0,
                "product_id": 0x0444,
                "product": "Ksoloti Core",
                "usb_serial": "usb-core",
                "cpu_serial": "003D00363532511735393330",
                "firmware": {
                    "version": "1.1.0.0",
                    "crc": self.firmware_crc,
                    "patch_entrypoint": "0x20011000",
                },
                "identity_status": "complete",
            }
        ]

    def upload(self, *, locator, expected_cpu_serial, expected_firmware, payload, start_patch, progress):
        self.uploads.append(
            (locator, expected_cpu_serial, payload, start_patch)
        )
        if expected_firmware["crc"] != self.firmware_crc:
            raise AssertionError("upload did not retain the discovered firmware")
        progress("device-identity-confirmed", 0, len(payload))
        progress("write-started", 0, len(payload))
        progress("chunk-written", len(payload), len(payload))
        if self.fail_upload:
            error = RuntimeError("read-back differs")
            error.code = "DEVICE_UPLOAD_VERIFICATION_FAILED"
            raise error
        progress("readback-verified", len(payload), len(payload))
        if start_patch:
            progress("patch-started", len(payload), len(payload))
        return {
            "load_address": "0x20011000",
            "byte_length": len(payload),
            "readback": "byte-for-byte-match",
            "patch_started": start_patch,
            "persistent_install": False,
            "firmware_flash": False,
            "sd_card_write": False,
        }


class DesktopBuildDeviceSessionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base = load_repository_context(
            repository_root=ROOT,
            record_set_path=ROOT
            / "contracts/record-sets/ui-desktop-build-device-v1.json",
        )
        cls.context = with_compiler_schemas(base, ROOT)
        request = next(
            item
            for item in cls.context.records["request"]
            if all(item.get(key) == value for key, value in REQUEST_REFERENCE.items())
        )
        cls.backend_reference = request["backend_reference"]

    def setUp(self):
        registration = _registration(self.backend_reference)

        def factory(output_root):
            return ExecutionService.from_values((registration,), output_root)

        self.builds = BuildSessionService(execution_factory=factory)
        self.compilation = CompilationContext.from_values(
            build_request_reference=REQUEST_REFERENCE,
            closure_source={
                "kind": "record-set",
                "record_set_reference": self.context.record_set_reference,
            },
            records=self.context.records,
            schemas=self.context.schemas,
        )

    def tearDown(self):
        self.builds.close()

    def _completed_build(self, project_reference=None):
        project_reference = project_reference or PROJECT_REFERENCE
        started = self.builds.start(
            self.compilation,
            build_request_reference=REQUEST_REFERENCE,
            execution_intent=True,
            project_reference=project_reference,
        )
        self.assertEqual("queued", started["status"])
        for _ in range(200):
            value = self.builds.inspect(started["session_id"])
            if value["status"] not in {"queued", "running"}:
                return value
            time.sleep(0.01)
        self.fail("fake build session did not finish")

    def test_build_session_exposes_progress_and_portable_artifact_facts(self):
        value = self._completed_build()
        self.assertEqual("success", value["status"])
        self.assertEqual("completed", value["phase"])
        self.assertEqual("target-executable", value["artifacts"][0]["artifact_kind"])
        self.assertNotIn("output_root", value)
        self.assertEqual(
            [
                "planning-started",
                "planning-completed",
                "handler-selected",
                "handler-started",
                "handler-completed",
                "output-published",
            ],
            [item["event"] for item in value["progress"]],
        )

    def test_generated_v12_protocol_and_record_set_are_fresh(self):
        completed = subprocess.run(
            [
                sys.executable,
                "tools/contracts/generate_desktop_build_device_records.py",
                "--check",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)

    def test_v12_dispatch_validates_and_routes_through_shared_operations(self):
        calls = []

        class BuildStub:
            def start(stub, compilation_context, **values):
                calls.append((compilation_context.build_request_reference(), values))
                return {
                    "session_id": "build-session-000001",
                    "status": "queued",
                    "phase": "queued",
                    "progress": [],
                    "diagnostics": [],
                }

        class DeviceStub:
            pass

        project = SimpleNamespace(
            repository_root=ROOT,
            load=lambda: SimpleNamespace(
                context=self.context,
                manifest={
                    "project_id": PROJECT_REFERENCE["project_id"],
                    "revision": PROJECT_REFERENCE["revision"],
                    "content_hash": PROJECT_REFERENCE["content_hash"],
                },
            ),
        )
        result = dispatch_operation(
            {
                "schema_version": "schuss-operation-request-v12",
                "canonical_profile": "schuss-canonical-json-v1",
                "operation": "build.session.start",
                "payload": {
                    "build_request_reference": REQUEST_REFERENCE,
                    "execution_intent": True,
                },
            },
            self.context,
            project_service=project,
            build_session_service=BuildStub(),
            device_session_service=DeviceStub(),
        )
        self.assertEqual("success", result["status"])
        self.assertEqual("build-session-000001", result["value"]["session_id"])
        self.assertEqual(REQUEST_REFERENCE, calls[0][0])

        rejected = dispatch_operation(
            {
                "schema_version": "schuss-operation-request-v12",
                "canonical_profile": "schuss-canonical-json-v1",
                "operation": "build.session.start",
                "payload": {
                    "build_request_reference": REQUEST_REFERENCE,
                    "execution_intent": False,
                },
            },
            self.context,
            project_service=project,
            build_session_service=BuildStub(),
            device_session_service=DeviceStub(),
        )
        self.assertEqual("invalid", rejected["status"])
        self.assertEqual([], calls[1:])

    def test_handler_selection_fails_closed_before_a_job_starts(self):
        empty = BuildSessionService(
            execution_factory=lambda output: ExecutionService.from_values((), output)
        )
        try:
            with self.assertRaisesRegex(BuildSessionError, "found 0"):
                empty.start(
                    self.compilation,
                    build_request_reference=REQUEST_REFERENCE,
                    execution_intent=True,
                    project_reference=PROJECT_REFERENCE,
                )
        finally:
            empty.close()

    def test_discovery_and_verified_upload_are_explicit_and_session_bound(self):
        build = self._completed_build()
        artifact = build["artifacts"][0]
        transport = FakeTransport()
        devices = DeviceSessionService(
            self.builds,
            transport=transport,
            binary_deriver=lambda _: b"exact-device-binary",
        )
        discovery = devices.discover(
            records=self.context.records,
            build_request_reference=REQUEST_REFERENCE,
            project_reference=PROJECT_REFERENCE,
            discovery_intent=True,
        )
        self.assertTrue(discovery["discovery_was_explicit"])
        self.assertFalse(discovery["background_monitoring"])
        device = discovery["sessions"][0]
        self.assertEqual("compatible", device["compatibility"])
        started = devices.start_upload(
            device_session_id=device["session_id"],
            build_session_id=build["session_id"],
            artifact_sha256=artifact["byte_sha256"],
            upload_intent="explicit-volatile-ram",
            start_patch=True,
        )
        for _ in range(200):
            upload = devices.inspect_upload(started["session_id"])
            if upload["status"] not in {"queued", "running"}:
                break
            time.sleep(0.01)
        self.assertEqual("success", upload["status"])
        self.assertEqual("byte-for-byte-match", upload["verification"])
        self.assertEqual(
            [
                "device-identity-confirmed",
                "write-started",
                "chunk-written",
                "readback-verified",
                "patch-started",
            ],
            [item["event"] for item in upload["progress"]],
        )
        self.assertEqual(b"exact-device-binary", transport.uploads[0][2])
        self.assertFalse(upload["persistent_install"])
        self.assertFalse(upload["firmware_flash"])
        self.assertFalse(upload["sd_card_write"])

    def test_incompatible_firmware_and_failed_verification_never_report_success(self):
        build = self._completed_build()
        artifact = build["artifacts"][0]
        incompatible = DeviceSessionService(
            self.builds,
            transport=FakeTransport(firmware_crc="00000000"),
            binary_deriver=lambda _: b"binary",
        )
        discovery = incompatible.discover(
            records=self.context.records,
            build_request_reference=REQUEST_REFERENCE,
            project_reference=PROJECT_REFERENCE,
            discovery_intent=True,
        )
        self.assertEqual("incompatible", discovery["sessions"][0]["compatibility"])
        with self.assertRaises(DeviceSessionError):
            incompatible.start_upload(
                device_session_id=discovery["sessions"][0]["session_id"],
                build_session_id=build["session_id"],
                artifact_sha256=artifact["byte_sha256"],
                upload_intent="explicit-volatile-ram",
                start_patch=True,
            )

        failing_transport = FakeTransport(fail_upload=True)
        failing = DeviceSessionService(
            self.builds,
            transport=failing_transport,
            binary_deriver=lambda _: b"binary",
        )
        compatible = failing.discover(
            records=self.context.records,
            build_request_reference=REQUEST_REFERENCE,
            project_reference=PROJECT_REFERENCE,
            discovery_intent=True,
        )["sessions"][0]
        started = failing.start_upload(
            device_session_id=compatible["session_id"],
            build_session_id=build["session_id"],
            artifact_sha256=artifact["byte_sha256"],
            upload_intent="explicit-volatile-ram",
            start_patch=True,
        )
        for _ in range(200):
            upload = failing.inspect_upload(started["session_id"])
            if upload["status"] not in {"queued", "running"}:
                break
            time.sleep(0.01)
        self.assertEqual("failed", upload["status"])
        self.assertEqual("not-run", upload["verification"])
        self.assertEqual(
            "DEVICE_UPLOAD_VERIFICATION_FAILED", upload["diagnostics"][0]["code"]
        )

    def test_upload_rejects_a_build_from_another_project_session(self):
        build = self._completed_build(
            {
                "project_id": "schuss-project-900002",
                "revision": 1,
                "content_hash": "sha256:" + "7" * 64,
            }
        )
        transport = FakeTransport()
        devices = DeviceSessionService(
            self.builds,
            transport=transport,
            binary_deriver=lambda _: b"binary",
        )
        device = devices.discover(
            records=self.context.records,
            build_request_reference=REQUEST_REFERENCE,
            project_reference=PROJECT_REFERENCE,
            discovery_intent=True,
        )["sessions"][0]
        with self.assertRaisesRegex(
            DeviceSessionError, "same exact project request"
        ):
            devices.start_upload(
                device_session_id=device["session_id"],
                build_session_id=build["session_id"],
                artifact_sha256=build["artifacts"][0]["byte_sha256"],
                upload_intent="explicit-volatile-ram",
                start_patch=False,
            )
        self.assertEqual([], transport.uploads)

    def test_second_active_upload_to_one_device_is_rejected(self):
        build = self._completed_build()
        artifact = build["artifacts"][0]
        entered = Event()
        release = Event()

        class BlockingTransport(FakeTransport):
            def upload(transport, **values):
                entered.set()
                if not release.wait(2):
                    raise AssertionError("test upload was not released")
                return super().upload(**values)

        devices = DeviceSessionService(
            self.builds,
            transport=BlockingTransport(),
            binary_deriver=lambda _: b"binary",
        )
        device = devices.discover(
            records=self.context.records,
            build_request_reference=REQUEST_REFERENCE,
            project_reference=PROJECT_REFERENCE,
            discovery_intent=True,
        )["sessions"][0]
        first = devices.start_upload(
            device_session_id=device["session_id"],
            build_session_id=build["session_id"],
            artifact_sha256=artifact["byte_sha256"],
            upload_intent="explicit-volatile-ram",
            start_patch=True,
        )
        self.assertTrue(entered.wait(1))
        rediscovered = devices.discover(
            records=self.context.records,
            build_request_reference=REQUEST_REFERENCE,
            project_reference=PROJECT_REFERENCE,
            discovery_intent=True,
        )["sessions"][0]
        self.assertNotEqual(device["session_id"], rediscovered["session_id"])
        try:
            with self.assertRaisesRegex(DeviceSessionError, "already has an active"):
                devices.start_upload(
                    device_session_id=rediscovered["session_id"],
                    build_session_id=build["session_id"],
                    artifact_sha256=artifact["byte_sha256"],
                    upload_intent="explicit-volatile-ram",
                    start_patch=True,
                )
        finally:
            release.set()
        for _ in range(200):
            upload = devices.inspect_upload(first["session_id"])
            if upload["status"] not in {"queued", "running"}:
                break
            time.sleep(0.01)
        self.assertEqual("success", upload["status"])

    def test_transport_failures_retain_stable_stage_diagnostics(self):
        build = self._completed_build()
        artifact = build["artifacts"][0]
        cases = (
            ("write", "DEVICE_USB_WRITE_FAILED", ()),
            ("acknowledgement", "DEVICE_COMMAND_REJECTED", ("device-identity-confirmed",)),
            ("disconnect", "DEVICE_USB_READ_FAILED", ("device-identity-confirmed", "write-started")),
            ("start", "DEVICE_COMMAND_REJECTED", ("device-identity-confirmed", "readback-verified")),
        )

        for label, code, events in cases:
            with self.subTest(label=label):
                class FailingTransport(FakeTransport):
                    def upload(transport, *, payload, progress, **_):
                        for event in events:
                            progress(event, len(payload) if event == "readback-verified" else 0, len(payload))
                        raise KsolotiUSBError(code, f"{label} failed")

                devices = DeviceSessionService(
                    self.builds,
                    transport=FailingTransport(),
                    binary_deriver=lambda _: b"binary",
                )
                device = devices.discover(
                    records=self.context.records,
                    build_request_reference=REQUEST_REFERENCE,
                    project_reference=PROJECT_REFERENCE,
                    discovery_intent=True,
                )["sessions"][0]
                started = devices.start_upload(
                    device_session_id=device["session_id"],
                    build_session_id=build["session_id"],
                    artifact_sha256=artifact["byte_sha256"],
                    upload_intent="explicit-volatile-ram",
                    start_patch=True,
                )
                for _ in range(200):
                    upload = devices.inspect_upload(started["session_id"])
                    if upload["status"] not in {"queued", "running"}:
                        break
                    time.sleep(0.01)
                self.assertEqual("failed", upload["status"])
                self.assertEqual(code, upload["diagnostics"][0]["code"])
                self.assertEqual(list(events), [item["event"] for item in upload["progress"]])
                self.assertEqual(
                    "byte-for-byte-match" if label == "start" else "not-run",
                    upload["verification"],
                )
                self.assertFalse(upload["authoritative_records_mutated"])

    def test_concrete_transport_is_lazy_until_explicit_discovery(self):
        called = []

        def loader():
            called.append(True)
            raise AssertionError("USB loader should remain lazy")

        KsolotiUSBTransport(library_loader=loader)
        self.assertEqual([], called)
        self.assertEqual({0x0444: 2, 0x0446: 4}, KSOLOTI_BULK_INTERFACES)

    def test_concrete_upload_protocol_is_ordered_and_verified_before_start(self):
        payload = bytes(range(256)) * (UPLOAD_CHUNK_SIZE // 256) + b"tail"

        class Connection:
            def __init__(connection):
                connection.events = []

            def cpu_serial(connection):
                connection.events.append(("identity",))
                return "cpu-serial"

            def ping(connection):
                connection.events.append(("ping",))

            def firmware(connection):
                connection.events.append(("firmware",))
                return {
                    "version": "1.1.0.0",
                    "crc": "5021D42A",
                    "patch_entrypoint": "0x20011000",
                }

            def command(connection, value, acknowledgement):
                connection.events.append(("command", value, acknowledgement))

            def read_memory(connection, address, length):
                connection.events.append(("read", address, length))
                offset = address - PATCH_LOAD_ADDRESS
                return payload[offset : offset + length]

        connection = Connection()
        progress = []
        outcome = KsolotiUSBTransport._upload_connection(
            connection,
            expected_cpu_serial="cpu-serial",
            expected_firmware={
                "version": "1.1.0.0",
                "crc": "5021D42A",
                "patch_entrypoint": "0x20011000",
            },
            payload=payload,
            start_patch=True,
            progress=lambda event, completed, total: progress.append(
                (event, completed, total)
            ),
        )
        commands = [event for event in connection.events if event[0] == "command"]
        self.assertEqual(("command", b"AxoS", b"S"), commands[0])
        self.assertEqual(
            (
                "command",
                b"AxoW"
                + struct.pack("<II", PATCH_LOAD_ADDRESS, len(payload))
                + b"W",
                b"W",
            ),
            commands[1],
        )
        self.assertEqual(b"Axow", commands[2][1][:4])
        self.assertEqual(UPLOAD_CHUNK_SIZE, struct.unpack("<I", commands[2][1][4:8])[0])
        self.assertEqual(b"Axow", commands[3][1][:4])
        self.assertEqual(4, struct.unpack("<I", commands[3][1][4:8])[0])
        self.assertEqual(
            (
                "command",
                b"AxoW"
                + struct.pack("<II", PATCH_LOAD_ADDRESS, len(payload))
                + b"e",
                b"e",
            ),
            commands[4],
        )
        self.assertEqual(
            ("command", b"Axos" + struct.pack("<HB", 100, 200), b"s"),
            commands[5],
        )
        self.assertEqual(
            [
                ("read", PATCH_LOAD_ADDRESS, UPLOAD_CHUNK_SIZE),
                ("read", PATCH_LOAD_ADDRESS + UPLOAD_CHUNK_SIZE, 4),
            ],
            [event for event in connection.events if event[0] == "read"],
        )
        self.assertLess(
            connection.events.index(("read", PATCH_LOAD_ADDRESS + UPLOAD_CHUNK_SIZE, 4)),
            connection.events.index(commands[5]),
        )
        self.assertEqual("byte-for-byte-match", outcome["readback"])
        self.assertTrue(outcome["patch_started"])
        self.assertEqual("patch-started", progress[-1][0])
        self.assertEqual(
            [("ping",), ("identity",), ("firmware",)],
            connection.events[:3],
        )

        changed = Connection()
        changed.firmware = lambda: {
            "version": "1.1.0.0",
            "crc": "00000000",
            "patch_entrypoint": "0x20011000",
        }
        with self.assertRaisesRegex(KsolotiUSBError, "firmware identity changed"):
            KsolotiUSBTransport._upload_connection(
                changed,
                expected_cpu_serial="cpu-serial",
                expected_firmware={
                    "version": "1.1.0.0",
                    "crc": "5021D42A",
                    "patch_entrypoint": "0x20011000",
                },
                payload=payload,
                start_patch=True,
                progress=lambda *_: None,
            )
        self.assertFalse(any(event[0] == "command" for event in changed.events))


if __name__ == "__main__":
    unittest.main()
