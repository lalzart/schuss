from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from packages.schuss_core import instrument_library
from packages.schuss_core.control_plane import dispatch_operation, load_repository_context
from packages.schuss_core.instrument_library import InstrumentLibraryService


ROOT = Path(__file__).resolve().parents[3]
RECORD_SET = ROOT / "contracts/record-sets/ui-desktop-instrument-library-v1.json"


def request(operation: str, payload: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": "schuss-operation-request-v19",
        "canonical_profile": "schuss-canonical-json-v1",
        "operation": operation,
        "payload": payload,
    }


class FakeProcess:
    def __init__(self) -> None:
        self.return_code: int | None = None

    def poll(self) -> int | None:
        return self.return_code


class Task039InstrumentLibraryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = load_repository_context(ROOT, record_set_path=RECORD_SET)

    def test_generated_authority_is_fresh(self) -> None:
        completed = __import__("subprocess").run(
            [
                "python3",
                str(ROOT / "tools/contracts/generate_task039_instrument_library.py"),
                "--check",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        summary = json.loads(completed.stdout)
        self.assertEqual("valid", summary["status"])
        self.assertFalse(summary["application_or_device_launched"])

    def test_list_is_exact_and_never_discloses_launch_paths(self) -> None:
        service = InstrumentLibraryService(
            ROOT,
            context=self.context,
            process_factory=lambda _path: self.fail("list must not spawn"),
        )
        result = dispatch_operation(
            request("instrument.library.list", {}),
            self.context,
            instrument_library_service=service,
        )
        self.assertEqual("success", result["status"])
        self.assertEqual(5, result["value"]["instrument_count"])
        availability = {
            item["prototype_id"]: item["availability"]
            for item in result["value"]["instruments"]
        }
        self.assertEqual("build-required", availability["cinderwheel"])
        self.assertEqual(
            "verified-local-build", availability["generative-drum-machine"]
        )
        self.assertEqual("verified-local-build", availability["tide-pit-gills"])
        self.assertEqual("research-only", availability["wirefall"])
        self.assertEqual("verified-local-build", availability["wirefall-r02"])
        serialized = json.dumps(result, sort_keys=True)
        self.assertNotIn("bundle_path", serialized)
        self.assertNotIn("executable_path", serialized)
        self.assertNotIn(str(ROOT), serialized)

    def test_start_and_inspect_use_only_a_fake_process(self) -> None:
        spawned: list[Path] = []
        process = FakeProcess()

        def factory(path: Path) -> FakeProcess:
            spawned.append(path)
            return process

        service = InstrumentLibraryService(
            ROOT, context=self.context, process_factory=factory
        )
        start = dispatch_operation(
            request(
                "instrument.session.start",
                {
                    "prototype_id": "generative-drum-machine",
                    "revision": "0.6",
                    "launch_intent": "explicit-native-juce-audition",
                },
            ),
            self.context,
            instrument_library_service=service,
        )
        self.assertEqual("success", start["status"])
        self.assertEqual("instrument-session-000001", start["value"]["instrument_session_id"])
        self.assertEqual("running", start["value"]["status"])
        self.assertEqual(1, len(spawned))
        self.assertTrue(spawned[0].is_absolute())
        self.assertNotIn("path", json.dumps(start, sort_keys=True))

        duplicate = dispatch_operation(
            request(
                "instrument.session.start",
                {
                    "prototype_id": "generative-drum-machine",
                    "revision": "0.6",
                    "launch_intent": "explicit-native-juce-audition",
                },
            ),
            self.context,
            instrument_library_service=service,
        )
        self.assertEqual("conflict", duplicate["status"])
        self.assertEqual(1, len(spawned))

        process.return_code = 0
        inspect = dispatch_operation(
            request(
                "instrument.session.inspect",
                {"instrument_session_id": "instrument-session-000001"},
            ),
            self.context,
            instrument_library_service=service,
        )
        self.assertEqual("success", inspect["status"])
        self.assertEqual("exited", inspect["value"]["status"])
        self.assertEqual(0, inspect["value"]["exit_code"])

    def test_unavailable_and_invalid_launches_fail_closed(self) -> None:
        service = InstrumentLibraryService(
            ROOT,
            context=self.context,
            process_factory=lambda _path: self.fail("unavailable target must not spawn"),
        )
        unavailable = dispatch_operation(
            request(
                "instrument.session.start",
                {
                    "prototype_id": "cinderwheel",
                    "revision": "0.1",
                    "launch_intent": "explicit-native-juce-audition",
                },
            ),
            self.context,
            instrument_library_service=service,
        )
        self.assertEqual("unavailable", unavailable["status"])
        self.assertEqual(
            "INSTRUMENT_BUILD_UNAVAILABLE", unavailable["diagnostics"][0]["code"]
        )
        invalid = dispatch_operation(
            request(
                "instrument.session.start",
                {
                    "prototype_id": "cinderwheel",
                    "revision": "0.1",
                    "launch_intent": "anything-else",
                },
            ),
            self.context,
            instrument_library_service=service,
        )
        self.assertEqual("invalid", invalid["status"])
        self.assertEqual("OPERATION_REQUEST_INVALID", invalid["diagnostics"][0]["code"])

    def test_hash_drift_makes_frozen_builds_unlaunchable(self) -> None:
        actual_sha256 = instrument_library._sha256_file

        def changed_executable(path: Path) -> str:
            if "MacOS" in path.parts:
                return "0" * 64
            return actual_sha256(path)

        service = InstrumentLibraryService(ROOT, context=self.context)
        with mock.patch.object(
            instrument_library, "_sha256_file", side_effect=changed_executable
        ):
            result = service.list_instruments()
        availability = {
            item["prototype_id"]: item["availability"]
            for item in result["instruments"]
        }
        self.assertEqual("stale-build", availability["generative-drum-machine"])
        self.assertEqual("stale-build", availability["tide-pit-gills"])
        self.assertEqual("stale-build", availability["wirefall-r02"])

    def test_symlinked_library_authority_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "library.json").symlink_to(
                ROOT
                / "research/prototype_support/instrument_library/audition-library-v1.json"
            )
            service = InstrumentLibraryService(
                root,
                context=self.context,
                library_path=Path("library.json"),
            )
            result = dispatch_operation(
                request("instrument.library.list", {}),
                self.context,
                instrument_library_service=service,
            )
        self.assertEqual("invalid", result["status"])
        self.assertEqual(
            "INSTRUMENT_LIBRARY_SYMLINK_REJECTED",
            result["diagnostics"][0]["code"],
        )

    def test_capability_description_reports_service_gate(self) -> None:
        describe = {
            "schema_version": "schuss-operation-request-v7",
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": "application.describe",
            "payload": {"scope": "selected-context"},
        }
        without_service = dispatch_operation(describe, self.context)
        service = InstrumentLibraryService(ROOT, context=self.context)
        with_service = dispatch_operation(
            describe, self.context, instrument_library_service=service
        )
        self.assertEqual("success", without_service["status"])
        self.assertEqual("success", with_service["status"])
        self.assertEqual(
            "application-capability-description-v12",
            with_service["value"]["schema_version"],
        )
        self.assertEqual(50, len(with_service["value"]["operations"]))
        unavailable = {
            item["operation"]: item["availability"]
            for item in without_service["value"]["operations"]
        }
        available = {
            item["operation"]: item["availability"]
            for item in with_service["value"]["operations"]
        }
        for operation in (
            "instrument.library.list",
            "instrument.session.inspect",
            "instrument.session.start",
        ):
            self.assertEqual(
                "requires-instrument-library-service", unavailable[operation]
            )
            self.assertEqual("available", available[operation])


if __name__ == "__main__":
    unittest.main()
