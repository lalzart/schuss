"""Core-owned discovery and verified volatile-upload sessions."""

from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import subprocess
import tempfile
from threading import Event, Lock, Thread
from typing import Any, Callable, Mapping, Protocol

from .build_sessions import BuildSessionError, BuildSessionService
from .gills_direct_backend import DirectExecutionConfig, TOOL_HASHES
from .gills_mapped_backend import DEVICE_REFERENCE as SUPPORTED_DEVICE_PROFILE_REFERENCE
from .ksoloti_usb import (
    KSOLOTI_PRODUCT_IDS,
    KSOLOTI_VENDOR_ID,
    PATCH_LOAD_ADDRESS,
    KsolotiUSBTransport,
)


SUPPORTED_FIRMWARE_VERSION = "1.1.0.0"
SUPPORTED_FIRMWARE_CRC = "5021D42A"
MAXIMUM_DEVICE_SESSIONS = 8
MAXIMUM_UPLOAD_SESSIONS = 8
UPLOAD_TERMINAL_STATUSES = {"success", "failed"}


class DeviceSessionError(ValueError):
    """Stable fail-closed device-session rejection."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class DeviceTransport(Protocol):
    def discover(self) -> list[dict[str, Any]]: ...

    def upload(
        self,
        *,
        locator: str,
        expected_cpu_serial: str,
        expected_firmware: Mapping[str, Any],
        payload: bytes,
        start_patch: bool,
        progress: Callable[[str, int, int], None],
    ) -> dict[str, Any]: ...


BinaryDeriver = Callable[[Path], bytes]


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def derive_device_binary(target_executable: Path) -> bytes:
    """Derive raw patch bytes with the same authenticated local ARM tool."""

    config = DirectExecutionConfig.local_default()
    objcopy = config.arm_bin / "arm-none-eabi-objcopy"
    if not objcopy.is_file() or _sha256_file(objcopy) != TOOL_HASHES["arm-none-eabi-objcopy"]:
        raise DeviceSessionError(
            "DEVICE_OBJCOPY_IDENTITY_INVALID",
            "authenticated arm-none-eabi-objcopy is unavailable or differs",
        )
    with tempfile.TemporaryDirectory(prefix="schuss-device-binary-") as raw:
        destination = Path(raw) / "patch.bin"
        completed = subprocess.run(
            [str(objcopy), "-O", "binary", str(target_executable), str(destination)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode or not destination.is_file() or destination.is_symlink():
            raise DeviceSessionError(
                "DEVICE_BINARY_DERIVATION_FAILED",
                "authenticated objcopy could not derive the volatile device binary",
            )
        payload = destination.read_bytes()
    if not payload:
        raise DeviceSessionError(
            "DEVICE_BINARY_EMPTY", "derived volatile device binary is empty"
        )
    return payload


def _diagnostic(code: str, stage: str, subject: str, message: str) -> dict[str, str]:
    return {
        "code": code,
        "severity": "error",
        "stage": stage,
        "subject": subject,
        "message": message,
    }


class DeviceSessionService:
    def __init__(
        self,
        build_sessions: BuildSessionService,
        *,
        transport: DeviceTransport | None = None,
        binary_deriver: BinaryDeriver = derive_device_binary,
    ) -> None:
        self._build_sessions = build_sessions
        self._transport = transport or KsolotiUSBTransport()
        self._binary_deriver = binary_deriver
        self._lock = Lock()
        self._next_device_id = 1
        self._next_upload_id = 1
        self._devices: dict[str, dict[str, Any]] = {}
        self._uploads: dict[str, dict[str, Any]] = {}

    @staticmethod
    def _device_public(session: Mapping[str, Any]) -> dict[str, Any]:
        return copy.deepcopy(
            {key: value for key, value in session.items() if key != "transport_locator"}
        )

    @staticmethod
    def _upload_public(session: Mapping[str, Any]) -> dict[str, Any]:
        return copy.deepcopy(
            {
                key: value
                for key, value in session.items()
                if key not in {"binary", "transport_locator"}
            }
        )

    @staticmethod
    def _profile_reference(
        records: Mapping[str, tuple[dict[str, Any], ...]],
        build_request_reference: Mapping[str, Any],
    ) -> dict[str, Any]:
        requests = [
            item
            for item in records["request"]
            if all(
                item.get(key) == value
                for key, value in build_request_reference.items()
            )
        ]
        if len(requests) != 1:
            raise DeviceSessionError(
                "DEVICE_BUILD_REQUEST_NOT_EXACT",
                f"expected one exact accepted build request, found {len(requests)}",
            )
        instrument_reference = requests[0]["instrument_reference"]
        instruments = [
            item
            for item in records["instruments"]
            if all(
                item.get(key) == value
                for key, value in instrument_reference.items()
                if key != "status"
            )
        ]
        if len(instruments) != 1:
            raise DeviceSessionError(
                "DEVICE_INSTRUMENT_NOT_EXACT",
                f"expected one exact accepted instrument, found {len(instruments)}",
            )
        return copy.deepcopy(instruments[0]["device_profile_reference"])

    @staticmethod
    def _compatibility(endpoint: Mapping[str, Any]) -> tuple[str, list[dict[str, str]]]:
        diagnostics = []
        if endpoint.get("identity_status") != "complete":
            error = endpoint.get("inspection_error") or {}
            diagnostics.append(
                _diagnostic(
                    str(error.get("code", "DEVICE_IDENTITY_INCOMPLETE")),
                    "device-identity",
                    str(endpoint.get("transport_locator", "usb-device")),
                    str(error.get("message", "device identity is incomplete")),
                )
            )
        elif (
            endpoint.get("vendor_id") != KSOLOTI_VENDOR_ID
            or endpoint.get("product_id") not in KSOLOTI_PRODUCT_IDS
            or endpoint.get("product") != "Ksoloti Core"
        ):
            diagnostics.append(
                _diagnostic(
                    "DEVICE_PRODUCT_UNSUPPORTED",
                    "device-compatibility",
                    str(endpoint.get("transport_locator", "usb-device")),
                    "USB product is not the accepted Ksoloti Core target",
                )
            )
        elif not endpoint.get("cpu_serial"):
            diagnostics.append(
                _diagnostic(
                    "DEVICE_CPU_IDENTITY_MISSING",
                    "device-identity",
                    str(endpoint.get("transport_locator", "usb-device")),
                    "Ksoloti CPU serial is unavailable",
                )
            )
        else:
            firmware = endpoint.get("firmware") or {}
            if (
                firmware.get("version") != SUPPORTED_FIRMWARE_VERSION
                or firmware.get("crc") != SUPPORTED_FIRMWARE_CRC
            ):
                diagnostics.append(
                    _diagnostic(
                        "DEVICE_FIRMWARE_UNSUPPORTED",
                        "device-compatibility",
                        str(endpoint.get("cpu_serial", "ksoloti-core")),
                        "firmware identity does not match the accepted Ksoloti 1.1.0.0 boundary",
                    )
                )
        return ("compatible" if not diagnostics else "incompatible", diagnostics)

    def discover(
        self,
        *,
        records: Mapping[str, tuple[dict[str, Any], ...]],
        build_request_reference: Mapping[str, Any],
        project_reference: Mapping[str, Any],
        discovery_intent: bool,
    ) -> dict[str, Any]:
        if discovery_intent is not True:
            raise DeviceSessionError(
                "DEVICE_DISCOVERY_INTENT_REQUIRED",
                "explicit device discovery intent is required",
            )
        profile_reference = self._profile_reference(records, build_request_reference)
        if profile_reference != SUPPORTED_DEVICE_PROFILE_REFERENCE:
            raise DeviceSessionError(
                "DEVICE_PROFILE_UNSUPPORTED",
                "device discovery supports only the exact accepted Gills profile",
            )
        endpoints = self._transport.discover()
        sessions = []
        with self._lock:
            self._devices.clear()
            for endpoint in endpoints:
                compatibility, diagnostics = self._compatibility(endpoint)
                identifier = f"device-session-{self._next_device_id:06d}"
                self._next_device_id += 1
                session = {
                    "session_id": identifier,
                    "status": "available",
                    "project_reference": copy.deepcopy(dict(project_reference)),
                    "build_request_reference": copy.deepcopy(
                        dict(build_request_reference)
                    ),
                    "device_profile_reference": profile_reference,
                    "transport": "usb-bulk-libusb",
                    "transport_location": endpoint.get("transport_locator"),
                    "usb_identity": {
                        "vendor_id": f"0x{int(endpoint['vendor_id']):04X}",
                        "product_id": f"0x{int(endpoint['product_id']):04X}",
                        "usb_serial": endpoint.get("usb_serial"),
                    },
                    "board_identity": {
                        "product": endpoint.get("product"),
                        "cpu_serial": endpoint.get("cpu_serial"),
                        "firmware": copy.deepcopy(endpoint.get("firmware")),
                    },
                    "identity_status": endpoint.get("identity_status"),
                    "compatibility": compatibility,
                    "diagnostics": diagnostics,
                    "transport_locator": endpoint.get("transport_locator"),
                    "hardware_action_performed": "identity-inspection",
                }
                self._devices[identifier] = session
                sessions.append(self._device_public(session))
            while len(self._devices) > MAXIMUM_DEVICE_SESSIONS:
                self._devices.pop(next(iter(self._devices)))
        return {
            "status": "complete",
            "device_profile_reference": profile_reference,
            "sessions": sessions,
            "device_count": len(sessions),
            "discovery_was_explicit": True,
            "background_monitoring": False,
        }

    def inspect(self, identifier: str) -> dict[str, Any]:
        with self._lock:
            session = self._devices.get(identifier)
            if session is None:
                raise DeviceSessionError(
                    "DEVICE_SESSION_NOT_FOUND",
                    "the process-local device session is absent or expired",
                )
            return self._device_public(session)

    def _evict_upload_if_needed(self) -> None:
        while len(self._uploads) >= MAXIMUM_UPLOAD_SESSIONS:
            terminal = [
                identifier
                for identifier, session in self._uploads.items()
                if session["status"] in UPLOAD_TERMINAL_STATUSES
            ]
            if not terminal:
                raise DeviceSessionError(
                    "DEVICE_UPLOAD_LIMIT_REACHED",
                    "all retained device uploads are still active",
                )
            self._uploads.pop(terminal[0])

    def start_upload(
        self,
        *,
        device_session_id: str,
        build_session_id: str,
        artifact_sha256: str,
        upload_intent: str,
        start_patch: bool,
    ) -> dict[str, Any]:
        if upload_intent != "explicit-volatile-ram":
            raise DeviceSessionError(
                "DEVICE_UPLOAD_INTENT_REQUIRED",
                "explicit volatile-RAM upload intent is required",
            )
        with self._lock:
            device = self._devices.get(device_session_id)
            if device is None:
                raise DeviceSessionError(
                    "DEVICE_SESSION_NOT_FOUND",
                    "the process-local device session is absent or expired",
                )
            if device["compatibility"] != "compatible":
                raise DeviceSessionError(
                    "DEVICE_SESSION_INCOMPATIBLE",
                    "upload requires one exact compatible device session",
                )
            device_snapshot = copy.deepcopy(device)
        try:
            build = self._build_sessions.inspect(build_session_id)
            if (
                build.get("project_reference") != device_snapshot["project_reference"]
                or build.get("build_request_reference")
                != device_snapshot["build_request_reference"]
            ):
                raise DeviceSessionError(
                    "DEVICE_UPLOAD_SESSION_CONTEXT_MISMATCH",
                    "device and build sessions do not belong to the same exact project request",
                )
            artifact, target_path = self._build_sessions.target_artifact(
                build_session_id, artifact_sha256
            )
        except BuildSessionError as error:
            raise DeviceSessionError(error.code, str(error)) from error
        binary = self._binary_deriver(target_path)
        binary_sha256 = hashlib.sha256(binary).hexdigest()
        with self._lock:
            if any(
                session["transport_locator"] == device_snapshot["transport_locator"]
                and session["status"] in {"queued", "running"}
                for session in self._uploads.values()
            ):
                raise DeviceSessionError(
                    "DEVICE_UPLOAD_ALREADY_ACTIVE",
                    "the selected device already has an active volatile upload",
                )
            self._evict_upload_if_needed()
            identifier = f"upload-session-{self._next_upload_id:06d}"
            self._next_upload_id += 1
            session = {
                "session_id": identifier,
                "status": "queued",
                "phase": "queued",
                "device_session_id": device_session_id,
                "transport_locator": device_snapshot["transport_locator"],
                "build_session_id": build_session_id,
                "artifact": artifact,
                "device_binary": {
                    "byte_sha256": binary_sha256,
                    "byte_length": len(binary),
                    "load_address": f"0x{PATCH_LOAD_ADDRESS:08X}",
                },
                "start_patch_requested": start_patch,
                "progress": [],
                "verification": "not-run",
                "outcome": None,
                "diagnostics": [],
                "persistent_install": False,
                "firmware_flash": False,
                "sd_card_write": False,
                "authoritative_records_mutated": False,
                "evidence_boundary": "session-observation-only-not-governed-evidence",
                "binary": binary,
            }
            self._uploads[identifier] = session
            initial = self._upload_public(session)
        begin = Event()
        thread = Thread(
            target=self._run_upload,
            args=(identifier, device_snapshot, begin),
            name=identifier,
            daemon=True,
        )
        thread.start()
        begin.set()
        return initial

    def _run_upload(
        self, identifier: str, device: Mapping[str, Any], begin: Event
    ) -> None:
        begin.wait()
        with self._lock:
            session = self._uploads[identifier]
            session["status"] = "running"
            session["phase"] = "device-identity-confirmation"
            binary = session["binary"]
            start_patch = session["start_patch_requested"]

        def progress(event: str, completed: int, total: int) -> None:
            with self._lock:
                current = self._uploads.get(identifier)
                if current is None:
                    return
                current["phase"] = event
                current["progress"].append(
                    {
                        "ordinal": len(current["progress"]) + 1,
                        "event": event,
                        "completed_bytes": completed,
                        "total_bytes": total,
                    }
                )
                if event == "readback-verified":
                    current["verification"] = "byte-for-byte-match"

        try:
            outcome = self._transport.upload(
                locator=str(device["transport_locator"]),
                expected_cpu_serial=str(device["board_identity"]["cpu_serial"]),
                expected_firmware=copy.deepcopy(device["board_identity"]["firmware"]),
                payload=binary,
                start_patch=start_patch,
                progress=progress,
            )
            with self._lock:
                current = self._uploads[identifier]
                current["status"] = "success"
                current["phase"] = "completed"
                current["verification"] = "byte-for-byte-match"
                current["outcome"] = copy.deepcopy(outcome)
        except Exception as error:
            code = str(getattr(error, "code", "DEVICE_UPLOAD_FAILED"))
            stage = str(getattr(error, "stage", "device-upload"))
            subject = str(getattr(error, "subject", identifier))
            with self._lock:
                current = self._uploads[identifier]
                current["status"] = "failed"
                current["phase"] = "failed"
                current["diagnostics"] = [
                    _diagnostic(code, stage, subject, str(error))
                ]

    def inspect_upload(self, identifier: str) -> dict[str, Any]:
        with self._lock:
            session = self._uploads.get(identifier)
            if session is None:
                raise DeviceSessionError(
                    "DEVICE_UPLOAD_NOT_FOUND",
                    "the process-local upload session is absent or expired",
                )
            return self._upload_public(session)
