"""Lazy libusb transport for the bounded Ksoloti Core patch-RAM protocol.

The module deliberately exposes only identity inspection and one verified
volatile patch upload. It contains no flash, DFU, reset, SD, file, or arbitrary
memory operation surface.
"""

from __future__ import annotations

import ctypes
import ctypes.util
from contextlib import contextmanager
from pathlib import Path
import struct
from typing import Any, Callable, Iterator, Mapping


KSOLOTI_VENDOR_ID = 0x16C0
KSOLOTI_PRODUCT_IDS = (0x0444, 0x0446)
KSOLOTI_BULK_INTERFACES = {0x0444: 2, 0x0446: 4}
BULK_OUT = 0x02
BULK_IN = 0x82
PATCH_LOAD_ADDRESS = 0x20011000
CPU_SERIAL_ADDRESS = 0x1FFF7A10
CPU_SERIAL_LENGTH = 12
UPLOAD_CHUNK_SIZE = 32768
USB_TIMEOUT_MS = 3000
# Match Ksoloti Local's current "Normal" DSP safety policy. These are protocol
# values, not measured Schuss real-time or resource evidence.
START_UI_MIDI_COST = 100
START_DSP_LIMIT_200 = 200


class KsolotiUSBError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.stage = "device-transport"
        self.subject = "ksoloti-core"


class _DeviceDescriptor(ctypes.Structure):
    _fields_ = [
        ("bLength", ctypes.c_uint8),
        ("bDescriptorType", ctypes.c_uint8),
        ("bcdUSB", ctypes.c_uint16),
        ("bDeviceClass", ctypes.c_uint8),
        ("bDeviceSubClass", ctypes.c_uint8),
        ("bDeviceProtocol", ctypes.c_uint8),
        ("bMaxPacketSize0", ctypes.c_uint8),
        ("idVendor", ctypes.c_uint16),
        ("idProduct", ctypes.c_uint16),
        ("bcdDevice", ctypes.c_uint16),
        ("iManufacturer", ctypes.c_uint8),
        ("iProduct", ctypes.c_uint8),
        ("iSerialNumber", ctypes.c_uint8),
        ("bNumConfigurations", ctypes.c_uint8),
    ]


def _library_candidates() -> tuple[str, ...]:
    values = [
        ctypes.util.find_library("usb-1.0"),
        "/opt/homebrew/lib/libusb-1.0.dylib",
        "/Applications/Ksoloti Local.app/Contents/Resources/platform_mac_x64/bin/libusb-1.0.0.dylib",
    ]
    return tuple(value for value in values if value)


def _load_library() -> ctypes.CDLL:
    errors = []
    for candidate in _library_candidates():
        try:
            library = ctypes.CDLL(candidate)
            _configure_library(library)
            return library
        except (AttributeError, OSError) as error:
            errors.append(f"{Path(candidate).name}: {error}")
    raise KsolotiUSBError(
        "DEVICE_USB_LIBRARY_UNAVAILABLE",
        "libusb is unavailable to the Schuss core"
        + (": " + "; ".join(errors) if errors else ""),
    )


def _configure_library(library: ctypes.CDLL) -> None:
    device = ctypes.c_void_p
    handle = ctypes.c_void_p
    context = ctypes.c_void_p
    library.libusb_init.argtypes = [ctypes.POINTER(context)]
    library.libusb_init.restype = ctypes.c_int
    library.libusb_exit.argtypes = [context]
    library.libusb_get_device_list.argtypes = [
        context,
        ctypes.POINTER(ctypes.POINTER(device)),
    ]
    library.libusb_get_device_list.restype = ctypes.c_ssize_t
    library.libusb_free_device_list.argtypes = [ctypes.POINTER(device), ctypes.c_int]
    library.libusb_get_device_descriptor.argtypes = [
        device,
        ctypes.POINTER(_DeviceDescriptor),
    ]
    library.libusb_get_device_descriptor.restype = ctypes.c_int
    library.libusb_get_bus_number.argtypes = [device]
    library.libusb_get_bus_number.restype = ctypes.c_uint8
    library.libusb_get_port_numbers.argtypes = [
        device,
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_int,
    ]
    library.libusb_get_port_numbers.restype = ctypes.c_int
    library.libusb_open.argtypes = [device, ctypes.POINTER(handle)]
    library.libusb_open.restype = ctypes.c_int
    library.libusb_close.argtypes = [handle]
    library.libusb_claim_interface.argtypes = [handle, ctypes.c_int]
    library.libusb_claim_interface.restype = ctypes.c_int
    library.libusb_release_interface.argtypes = [handle, ctypes.c_int]
    library.libusb_release_interface.restype = ctypes.c_int
    if hasattr(library, "libusb_set_auto_detach_kernel_driver"):
        library.libusb_set_auto_detach_kernel_driver.argtypes = [
            handle,
            ctypes.c_int,
        ]
        library.libusb_set_auto_detach_kernel_driver.restype = ctypes.c_int
    library.libusb_get_string_descriptor_ascii.argtypes = [
        handle,
        ctypes.c_uint8,
        ctypes.POINTER(ctypes.c_ubyte),
        ctypes.c_int,
    ]
    library.libusb_get_string_descriptor_ascii.restype = ctypes.c_int
    library.libusb_bulk_transfer.argtypes = [
        handle,
        ctypes.c_ubyte,
        ctypes.POINTER(ctypes.c_ubyte),
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_uint,
    ]
    library.libusb_bulk_transfer.restype = ctypes.c_int


class _Connection:
    def __init__(self, library: ctypes.CDLL, handle: ctypes.c_void_p) -> None:
        self.library = library
        self.handle = handle
        self.pending = bytearray()

    def write(self, payload: bytes) -> None:
        if not payload:
            raise KsolotiUSBError("DEVICE_USB_WRITE_INVALID", "empty USB write")
        buffer = (ctypes.c_ubyte * len(payload)).from_buffer_copy(payload)
        transferred = ctypes.c_int()
        result = self.library.libusb_bulk_transfer(
            self.handle,
            BULK_OUT,
            buffer,
            len(payload),
            ctypes.byref(transferred),
            USB_TIMEOUT_MS,
        )
        if result != 0 or transferred.value != len(payload):
            raise KsolotiUSBError(
                "DEVICE_USB_WRITE_FAILED",
                f"bulk write failed with libusb status {result}",
            )

    def _read_transfer(self) -> None:
        capacity = 65536
        buffer = (ctypes.c_ubyte * capacity)()
        transferred = ctypes.c_int()
        result = self.library.libusb_bulk_transfer(
            self.handle,
            BULK_IN,
            buffer,
            capacity,
            ctypes.byref(transferred),
            USB_TIMEOUT_MS,
        )
        if result != 0 or transferred.value <= 0:
            raise KsolotiUSBError(
                "DEVICE_USB_READ_FAILED",
                f"bulk read failed with libusb status {result}",
            )
        self.pending.extend(bytes(buffer[: transferred.value]))

    def read_packet(self, prefix: bytes, total_length: int) -> bytes:
        if total_length < len(prefix):
            raise ValueError("packet length cannot be shorter than prefix")
        for _ in range(64):
            position = self.pending.find(prefix)
            if position >= 0 and len(self.pending) >= position + total_length:
                packet = bytes(self.pending[position : position + total_length])
                del self.pending[: position + total_length]
                return packet
            self._read_transfer()
        raise KsolotiUSBError(
            "DEVICE_USB_RESPONSE_TIMEOUT",
            f"expected {prefix.decode('ascii', 'replace')} response was not complete",
        )

    def command(self, payload: bytes, command: bytes) -> None:
        self.write(payload)
        packet = self.read_packet(b"AxoR", 6)
        if packet[4:5] != command or packet[5] != 0:
            raise KsolotiUSBError(
                "DEVICE_COMMAND_REJECTED",
                f"device rejected {command.decode('ascii', 'replace')} with status {packet[5]}",
            )

    def ping(self) -> None:
        self.write(b"AxoA")
        self.read_packet(b"AxoA", 28)

    def firmware(self) -> dict[str, Any]:
        self.write(b"AxoV")
        packet = self.read_packet(b"AxoV", 16)
        version = ".".join(str(value) for value in packet[4:8])
        crc, entrypoint = struct.unpack_from("<II", packet, 8)
        return {
            "version": version,
            "crc": f"{crc:08X}",
            "patch_entrypoint": f"0x{entrypoint:08X}",
        }

    def read_memory(self, address: int, length: int) -> bytes:
        if length < 1 or length > UPLOAD_CHUNK_SIZE:
            raise ValueError("bounded memory read length is invalid")
        self.write(b"Axor" + struct.pack("<II", address, length))
        packet = self.read_packet(b"Axor", 12 + length)
        observed_address, observed_length = struct.unpack_from("<II", packet, 4)
        if observed_address != address or observed_length != length:
            raise KsolotiUSBError(
                "DEVICE_MEMORY_RESPONSE_INVALID",
                "device memory response did not match the exact request",
            )
        return packet[12:]

    def cpu_serial(self) -> str:
        payload = self.read_memory(CPU_SERIAL_ADDRESS, CPU_SERIAL_LENGTH)
        return "".join(f"{value:08X}" for value in struct.unpack("<III", payload))


class KsolotiUSBTransport:
    """Lazy concrete transport. Construction performs no USB operation."""

    def __init__(self, *, library_loader: Callable[[], ctypes.CDLL] = _load_library):
        self._library_loader = library_loader

    @contextmanager
    def _device_list(
        self,
    ) -> Iterator[tuple[ctypes.CDLL, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p), int]]:
        library = self._library_loader()
        context = ctypes.c_void_p()
        result = library.libusb_init(ctypes.byref(context))
        if result != 0:
            raise KsolotiUSBError(
                "DEVICE_USB_INITIALIZATION_FAILED",
                f"libusb initialization failed with status {result}",
            )
        devices = ctypes.POINTER(ctypes.c_void_p)()
        count = library.libusb_get_device_list(context, ctypes.byref(devices))
        if count < 0:
            library.libusb_exit(context)
            raise KsolotiUSBError(
                "DEVICE_USB_ENUMERATION_FAILED",
                f"libusb enumeration failed with status {count}",
            )
        try:
            yield library, context, devices, int(count)
        finally:
            library.libusb_free_device_list(devices, 1)
            library.libusb_exit(context)

    @staticmethod
    def _facts(
        library: ctypes.CDLL, device: ctypes.c_void_p, descriptor: _DeviceDescriptor
    ) -> dict[str, Any]:
        ports = (ctypes.c_uint8 * 8)()
        count = library.libusb_get_port_numbers(device, ports, len(ports))
        port_path = tuple(int(ports[index]) for index in range(max(0, count)))
        bus = int(library.libusb_get_bus_number(device))
        suffix = ".".join(str(value) for value in port_path) or "root"
        return {
            "transport_locator": f"usb:bus-{bus:03d}/ports-{suffix}",
            "bus": bus,
            "port_path": port_path,
            "vendor_id": int(descriptor.idVendor),
            "product_id": int(descriptor.idProduct),
        }

    @contextmanager
    def _open(
        self,
        library: ctypes.CDLL,
        device: ctypes.c_void_p,
        descriptor: _DeviceDescriptor,
    ) -> Iterator[tuple[_Connection, str | None]]:
        handle = ctypes.c_void_p()
        result = library.libusb_open(device, ctypes.byref(handle))
        if result != 0:
            raise KsolotiUSBError(
                "DEVICE_USB_OPEN_FAILED",
                f"libusb open failed with status {result}",
            )
        claimed = False
        interface = KSOLOTI_BULK_INTERFACES.get(int(descriptor.idProduct))
        if interface is None:
            library.libusb_close(handle)
            raise KsolotiUSBError(
                "DEVICE_USB_INTERFACE_UNAVAILABLE",
                "USB product has no accepted Ksoloti bulk interface",
            )
        try:
            if hasattr(library, "libusb_set_auto_detach_kernel_driver"):
                library.libusb_set_auto_detach_kernel_driver(handle, 1)
            result = library.libusb_claim_interface(handle, interface)
            if result != 0:
                raise KsolotiUSBError(
                    "DEVICE_USB_INTERFACE_UNAVAILABLE",
                    f"bulk interface claim failed with status {result}",
                )
            claimed = True
            serial = None
            if descriptor.iSerialNumber:
                buffer = (ctypes.c_ubyte * 256)()
                length = library.libusb_get_string_descriptor_ascii(
                    handle, descriptor.iSerialNumber, buffer, len(buffer)
                )
                if length > 0:
                    serial = bytes(buffer[:length]).decode("ascii", "replace")
            yield _Connection(library, handle), serial
        finally:
            if claimed:
                library.libusb_release_interface(handle, interface)
            library.libusb_close(handle)

    def discover(self) -> list[dict[str, Any]]:
        discovered: list[dict[str, Any]] = []
        with self._device_list() as (library, _, devices, count):
            for index in range(count):
                device = devices[index]
                descriptor = _DeviceDescriptor()
                if library.libusb_get_device_descriptor(
                    device, ctypes.byref(descriptor)
                ) != 0:
                    continue
                if descriptor.idVendor != KSOLOTI_VENDOR_ID or descriptor.idProduct not in KSOLOTI_PRODUCT_IDS:
                    continue
                facts = self._facts(library, device, descriptor)
                try:
                    with self._open(library, device, descriptor) as (connection, usb_serial):
                        connection.ping()
                        firmware = connection.firmware()
                        cpu_serial = connection.cpu_serial()
                    discovered.append(
                        {
                            **facts,
                            "product": "Ksoloti Core",
                            "usb_serial": usb_serial,
                            "cpu_serial": cpu_serial,
                            "firmware": firmware,
                            "identity_status": "complete",
                        }
                    )
                except KsolotiUSBError as error:
                    discovered.append(
                        {
                            **facts,
                            "product": "Ksoloti Core",
                            "usb_serial": None,
                            "cpu_serial": None,
                            "firmware": None,
                            "identity_status": "incomplete",
                            "inspection_error": {
                                "code": error.code,
                                "message": str(error),
                            },
                        }
                    )
        return sorted(discovered, key=lambda item: item["transport_locator"])

    def _matching_device(
        self,
        library: ctypes.CDLL,
        devices: ctypes.POINTER(ctypes.c_void_p),
        count: int,
        locator: str,
    ) -> tuple[ctypes.c_void_p, _DeviceDescriptor]:
        matches = []
        for index in range(count):
            device = devices[index]
            descriptor = _DeviceDescriptor()
            if library.libusb_get_device_descriptor(device, ctypes.byref(descriptor)) != 0:
                continue
            if descriptor.idVendor != KSOLOTI_VENDOR_ID or descriptor.idProduct not in KSOLOTI_PRODUCT_IDS:
                continue
            if self._facts(library, device, descriptor)["transport_locator"] == locator:
                matches.append((device, descriptor))
        if len(matches) != 1:
            raise KsolotiUSBError(
                "DEVICE_SESSION_ENDPOINT_CHANGED",
                f"expected one exact USB endpoint, found {len(matches)}",
            )
        return matches[0]

    @staticmethod
    def _upload_connection(
        connection: _Connection,
        *,
        expected_cpu_serial: str,
        expected_firmware: Mapping[str, Any],
        payload: bytes,
        start_patch: bool,
        progress: Callable[[str, int, int], None],
    ) -> dict[str, Any]:
        connection.ping()
        if connection.cpu_serial() != expected_cpu_serial:
            raise KsolotiUSBError(
                "DEVICE_SESSION_IDENTITY_CHANGED",
                "CPU identity changed since discovery",
            )
        if connection.firmware() != dict(expected_firmware):
            raise KsolotiUSBError(
                "DEVICE_SESSION_FIRMWARE_CHANGED",
                "firmware identity changed since discovery",
            )
        progress("device-identity-confirmed", 0, len(payload))
        connection.command(b"AxoS", b"S")
        progress("patch-stopped", 0, len(payload))
        connection.command(
            b"AxoW"
            + struct.pack("<II", PATCH_LOAD_ADDRESS, len(payload))
            + b"W",
            b"W",
        )
        progress("write-started", 0, len(payload))
        completed = 0
        for offset in range(0, len(payload), UPLOAD_CHUNK_SIZE):
            chunk = payload[offset : offset + UPLOAD_CHUNK_SIZE]
            connection.command(
                b"Axow" + struct.pack("<I", len(chunk)) + chunk,
                b"w",
            )
            completed += len(chunk)
            progress("chunk-written", completed, len(payload))
        connection.command(
            b"AxoW"
            + struct.pack("<II", PATCH_LOAD_ADDRESS, len(payload))
            + b"e",
            b"e",
        )
        progress("write-closed", len(payload), len(payload))
        observed = bytearray()
        for offset in range(0, len(payload), UPLOAD_CHUNK_SIZE):
            length = min(UPLOAD_CHUNK_SIZE, len(payload) - offset)
            observed.extend(
                connection.read_memory(PATCH_LOAD_ADDRESS + offset, length)
            )
        if bytes(observed) != payload:
            raise KsolotiUSBError(
                "DEVICE_UPLOAD_VERIFICATION_FAILED",
                "volatile patch RAM read-back differs from uploaded bytes",
            )
        progress("readback-verified", len(payload), len(payload))
        started = False
        if start_patch:
            connection.command(
                b"Axos"
                + struct.pack("<HB", START_UI_MIDI_COST, START_DSP_LIMIT_200),
                b"s",
            )
            started = True
            progress("patch-started", len(payload), len(payload))
        return {
            "load_address": f"0x{PATCH_LOAD_ADDRESS:08X}",
            "byte_length": len(payload),
            "readback": "byte-for-byte-match",
            "patch_started": started,
            "persistent_install": False,
            "firmware_flash": False,
            "sd_card_write": False,
        }

    def upload(
        self,
        *,
        locator: str,
        expected_cpu_serial: str,
        expected_firmware: Mapping[str, Any],
        payload: bytes,
        start_patch: bool,
        progress: Callable[[str, int, int], None],
    ) -> dict[str, Any]:
        if not payload:
            raise KsolotiUSBError("DEVICE_UPLOAD_EMPTY", "device binary is empty")
        with self._device_list() as (library, _, devices, count):
            device, descriptor = self._matching_device(
                library, devices, count, locator
            )
            with self._open(library, device, descriptor) as (connection, _):
                return self._upload_connection(
                    connection,
                    expected_cpu_serial=expected_cpu_serial,
                    expected_firmware=expected_firmware,
                    payload=payload,
                    start_patch=start_patch,
                    progress=progress,
                )
