from __future__ import annotations

import sys
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/contracts")]

from packages.schuss_core.control_plane import (  # noqa: E402
    dispatch_operation,
    load_repository_context,
)
from packages.schuss_core.gills_direct_frontend import (  # noqa: E402
    lower_gills_direct_successor,
)
from packages.schuss_core.gills_mapped_backend_v2 import (  # noqa: E402
    REQUEST_REFERENCE as PARENT_REQUEST_REFERENCE,
    descriptor as task021_descriptor,
)
from packages.schuss_core.gills_panel_diagnostic import (  # noqa: E402
    DiagnosticState,
    POT_MOVE_THRESHOLD_RAW,
    STARTUP_UPDATES,
    diagnostic_cpp,
    diagnostic_host_vectors,
    evaluate_diagnostic_update,
    pot_zone,
)

import generate_task021_records as task021_generator  # noqa: E402
import generate_task022_records as task022_generator  # noqa: E402
import task022_connected_observation as connected_observation  # noqa: E402
from run_task022 import diagnostic_identity, diagnostic_procedure  # noqa: E402


RECORD_SET = ROOT / "contracts/record-sets/task021-gills-dma-safe-v1.json"


class Task022PanelDiagnosticTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = load_repository_context(record_set_path=RECORD_SET)
        cls.plan = dispatch_operation(
            {
                "schema_version": "schuss-operation-request-v4",
                "canonical_profile": "schuss-canonical-json-v1",
                "operation": "build.plan",
                "payload": {"build_request_reference": PARENT_REQUEST_REFERENCE},
            },
            cls.context,
        )
        cls.graph = next(
            value
            for value in cls.context.records["graphs"]
            if value["graph_id"] == "schuss-graph-000002"
        )

    def test_parent_record_set_and_plan_are_exact(self) -> None:
        self.assertEqual("success", self.plan["status"])
        self.assertEqual(
            {
                "record_set_id": "schuss-record-set-000013",
                "revision": 1,
                "content_hash": "sha256:6e2b1f63abc999ab3067541f6dc0095ed338fb4b3f5c55898a58cdd3397bc8d3",
            },
            self.context.record_set_reference,
        )
        result = dispatch_operation(
            {
                "schema_version": "schuss-operation-request-v1",
                "canonical_profile": "schuss-canonical-json-v1",
                "operation": "records.validate",
                "payload": {"scope": "accepted-record-closure"},
            },
            self.context,
        )
        self.assertEqual("success", result["status"])

    def test_artifact_successor_record_set_is_exact_and_valid(self) -> None:
        files, manifest, _ = task022_generator.generated()
        files[
            "contracts/record-sets/task022-gills-panel-diagnostic-v1.json"
        ] = manifest
        self.assertTrue(
            all((ROOT / relative).read_bytes() == payload for relative, payload in files.items())
        )
        context = load_repository_context(
            record_set_path=ROOT
            / "contracts/record-sets/task022-gills-panel-diagnostic-v1.json"
        )
        result = dispatch_operation(
            {
                "schema_version": "schuss-operation-request-v1",
                "canonical_profile": "schuss-canonical-json-v1",
                "operation": "records.validate",
                "payload": {"scope": "accepted-record-closure"},
            },
            context,
        )
        self.assertEqual("success", result["status"])

    def test_diagnostic_identity_is_non_product_and_has_no_handler(self) -> None:
        self.assertEqual("schuss-panel-diagnostic-000001", diagnostic_identity()["stable_id"])
        self.assertEqual(2, diagnostic_procedure()["upload_count"])
        self.assertEqual(5, task021_descriptor()["supported_build_request_reference"]["revision"])
        self.assertNotIn("build_request_reference", diagnostic_identity())
        self.assertNotIn("build_handler_id", diagnostic_identity())

    def test_product_cli_cannot_select_a_diagnostic_handler(self) -> None:
        with tempfile.TemporaryDirectory(prefix="schuss-task022-cli-rejection-") as raw:
            completed = subprocess.run(
                [
                    str(ROOT / "bin/schuss"),
                    "build",
                    "execute",
                    "schuss-build-request-000002@5",
                    "--handler",
                    "schuss-build-handler-999999@1",
                    "--output-root",
                    str(Path(raw) / "must-not-exist"),
                    "--execute",
                    "--record-set",
                    str(RECORD_SET),
                    "--json",
                ],
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
        self.assertEqual(2, completed.returncode)
        self.assertIn(b"CLI_HANDLER_NOT_FOUND", completed.stderr)

    def test_all_pot_zones_and_monotonic_sessions_are_covered(self) -> None:
        self.assertEqual("low", pot_zone(0))
        self.assertEqual("low", pot_zone(512))
        self.assertEqual("transition", pot_zone(513))
        self.assertEqual("middle", pot_zone(1536))
        self.assertEqual("middle", pot_zone(2559))
        self.assertEqual("transition", pot_zone(2560))
        self.assertEqual("high", pot_zone(3583))
        self.assertEqual("high", pot_zone(4095))
        state = DiagnosticState()
        for raw in (0, 2048, 4095):
            state, output = evaluate_diagnostic_update(
                state, [raw] * 10, [False] * 4, True, True, False
            )
        self.assertEqual([3] * 10, [item["monotonic_stage"] for item in output["pot_states"]])
        self.assertEqual([7] * 10, [item["zone_mask"] for item in output["pot_states"]])
        self.assertFalse(any(item["discontinuity"] for item in output["pot_states"]))

    def test_connected_failed_observation_is_exact_and_not_promoted(self) -> None:
        path = ROOT / "evidence/task022-completion-v1/connected-device-observation.json"
        self.assertEqual(connected_observation.expected_bytes(), path.read_bytes())
        result = connected_observation.observed_failure()
        self.assertEqual("failed", result["status"])
        self.assertFalse(result["promotion_eligible"])
        self.assertEqual("POT_EVENT_FOCUS_UNSTABLE", result["failure"]["code"])
        self.assertEqual(1, result["write_boundaries"]["volatile_ram_uploads_performed"])
        self.assertFalse(result["write_boundaries"]["second_upload_performed"])

    def test_stationary_adc_jitter_can_steal_last_moved_focus(self) -> None:
        self.assertEqual(4, POT_MOVE_THRESHOLD_RAW)
        state = DiagnosticState(control_updates=STARTUP_UPDATES)
        state, _ = evaluate_diagnostic_update(
            state, [1000] * 10, [False] * 4, True, True, False
        )
        state, _ = evaluate_diagnostic_update(
            state, [1000, 2000, *([1000] * 8)], [False] * 4, True, True, False
        )
        self.assertTrue(state.last_event.startswith("P02 2000"))
        state, _ = evaluate_diagnostic_update(
            state, [1005, 2000, *([1000] * 8)], [False] * 4, True, True, False
        )
        self.assertTrue(state.last_event.startswith("P01 1005"))

    def test_all_buttons_and_encoder_push_emit_press_release_hold(self) -> None:
        vectors = diagnostic_host_vectors()["gesture_vectors"]
        self.assertEqual(5, len(vectors))
        for item in vectors:
            self.assertEqual(7, item["event_mask"])
            self.assertEqual(
                [
                    item["control"] + "-press",
                    item["control"] + "-hold",
                    item["control"] + "-release",
                ],
                item["events"],
            )

    def test_encoder_directions_and_six_led_channels_are_deterministic(self) -> None:
        state = DiagnosticState(control_updates=STARTUP_UPDATES)
        for direction_b in (False, False, False, True, True, True):
            state.encoder_a_last = True
            state.encoder_scan_counter = 0
            state, output = evaluate_diagnostic_update(
                state, [0] * 10, [False] * 4, False, direction_b, False
            )
        self.assertEqual(3, output["encoder_positive"])
        self.assertEqual(-3, output["encoder_negative"])
        observed = {output["active_led_channel"]}
        for _ in range(1500 * 5 + 1):
            state, output = evaluate_diagnostic_update(
                state, [0] * 10, [False] * 4, True, True, False
            )
            observed.add(output["active_led_channel"])
        self.assertEqual({1, 2, 3, 4, 5, 6}, observed)
        self.assertEqual(0x3F, output["led_scan_mask"])

    def test_source_has_dma_safe_telemetry_and_silent_audio_policy(self) -> None:
        direct = lower_gills_direct_successor(
            self.plan["value"],
            self.graph,
            self.context.records["contracts"],
            self.context.records["direct_operation_specs"],
            PARENT_REQUEST_REFERENCE,
        )
        cpp = diagnostic_cpp(direct["generated_cpp"]["text"])
        self.assertIn("SchussDiagnosticOledCommand[2]", cpp)
        self.assertIn("SchussDiagnosticOledTx[129]", cpp)
        self.assertIn("SchussDiagnosticOledTx[0] = 0x40", cpp)
        self.assertIn("process_gills_diagnostic();", cpp)
        self.assertNotIn("process_gills_panel();", cpp)
        self.assertNotIn('"PICKUP ARM"', cpp)
        self.assertNotIn('"TASK018"', cpp)
        self.assertNotIn("uint8_t bytes[2]", cpp)

    def test_task021_generated_records_remain_byte_exact(self) -> None:
        files, manifest, _ = task021_generator.generated()
        files["contracts/record-sets/task021-gills-dma-safe-v1.json"] = manifest
        self.assertTrue(
            all((ROOT / relative).read_bytes() == payload for relative, payload in files.items())
        )

    def test_transform_anchors_fail_closed(self) -> None:
        with self.assertRaisesRegex(
            ValueError, "GILLS_DIAGNOSTIC_CPP_ANCHOR_INVALID:declaration"
        ):
            diagnostic_cpp("void unrelated();\n")


if __name__ == "__main__":
    unittest.main()
