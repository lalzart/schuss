from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT), str(ROOT / "tools/contracts")]

from packages.schuss_core.build_execution import handler_reference  # noqa: E402
from packages.schuss_core.control_plane import (  # noqa: E402
    dispatch_operation,
    load_repository_context,
)
from packages.schuss_core.gills_mapped_backend_v2 import (  # noqa: E402
    COVERAGE_REFERENCE,
    INSTRUMENT_REFERENCE,
    REQUEST_REFERENCE,
    RUNTIME_REFERENCE,
    descriptor,
)
from packages.schuss_core.gills_mapped_frontend import (  # noqa: E402
    lower_gills_mapped_dma_safe,
)
from packages.schuss_core.gills_panel_runtime import (  # noqa: E402
    correct_mapped_cpp_dma_buffers,
)

import generate_task018_records as task018_generator  # noqa: E402
import generate_task021_records as generator  # noqa: E402
import validator_core as core  # noqa: E402


RECORD_SET = ROOT / "contracts/record-sets/task021-gills-dma-safe-v1.json"
EVIDENCE = ROOT / "evidence/task021-completion-v1"
TASK018_EVIDENCE = ROOT / "evidence/task018-completion-v1/validation-summary.json"


class Task021DmaSafeOledTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = load_repository_context(record_set_path=RECORD_SET)
        cls.instrument = next(
            value
            for value in cls.context.records["instruments"]
            if {
                key: value[key]
                for key in ("instrument_id", "revision", "content_hash")
            }
            == INSTRUMENT_REFERENCE
        )
        cls.coverage = next(
            value
            for value in cls.context.records["mapping_coverage"]
            if {
                key: value[key]
                for key in ("coverage_report_id", "revision", "content_hash")
            }
            == COVERAGE_REFERENCE
        )
        cls.runtime = next(
            value
            for value in cls.context.records["runtime_realizations"]
            if {
                key: value[key]
                for key in (
                    "runtime_realization_id",
                    "revision",
                    "content_hash",
                )
            }
            == RUNTIME_REFERENCE
        )
        cls.graph = next(
            value
            for value in cls.context.records["graphs"]
            if value["graph_id"] == "schuss-graph-000002"
        )
        cls.plan = dispatch_operation(
            {
                "schema_version": "schuss-operation-request-v4",
                "canonical_profile": "schuss-canonical-json-v1",
                "operation": "build.plan",
                "payload": {"build_request_reference": REQUEST_REFERENCE},
            },
            cls.context,
        )

    def test_generated_record_set_and_shared_validation_are_exact(self) -> None:
        files, manifest, _ = generator.generated()
        files[RECORD_SET.relative_to(ROOT).as_posix()] = manifest
        self.assertTrue(
            all(
                (ROOT / relative).read_bytes() == payload
                for relative, payload in files.items()
            )
        )
        self.assertEqual("valid", self.context.task018_summary["status"])
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
        self.assertEqual("success", self.plan["status"])

    def test_task018_and_task021_instrument_inspections_each_resolve_once(self) -> None:
        for revision in (2, 3):
            instrument = next(
                value
                for value in self.context.records["instruments"]
                if (value["instrument_id"], value["revision"])
                == ("schuss-instrument-000002", revision)
            )
            result = dispatch_operation(
                {
                    "schema_version": "schuss-operation-request-v6",
                    "canonical_profile": "schuss-canonical-json-v1",
                    "operation": "gills.inspect",
                    "payload": {
                        "instrument_reference": {
                            key: instrument[key]
                            for key in ("instrument_id", "revision", "content_hash")
                        }
                    },
                },
                self.context,
            )
            self.assertEqual("success", result["status"])
            self.assertEqual(
                revision - 1,
                result["value"]["runtime_realization"]["revision"],
            )

    def test_dma_safe_frontend_matches_the_connected_candidate(self) -> None:
        result = lower_gills_mapped_dma_safe(
            self.plan["value"],
            self.graph,
            self.context.records["contracts"],
            self.context.records["direct_operation_specs"],
            self.instrument,
            self.runtime,
            self.coverage,
            REQUEST_REFERENCE,
        )
        cpp = result["generated_cpp"]["text"]
        self.assertEqual(
            "e69155998e91c7c3af6b6e0aaebbac965f4cf822b67382f25de5776453af2928",
            hashlib.sha256(cpp.encode("utf-8")).hexdigest(),
        )
        self.assertIn('SchussOledCommand[2] __attribute__((section(".sram2")))', cpp)
        self.assertIn("SchussOledTx[0] = 0x40", cpp)
        self.assertIn("SchussOledCommand[0] = 0", cpp)
        self.assertNotIn("uint8_t bytes[2]", cpp)
        self.assertEqual(2, result["frontend"]["version"])

    def test_exact_handler_and_level6_claim_are_separate(self) -> None:
        self.assertEqual(
            {"status": "supported", **handler_reference(descriptor())},
            self.runtime["supported_builds"][0]["handler"],
        )
        claim = next(
            value
            for value in self.context.records["evidence"]
            if value["evidence_claim_id"] == "schuss-evidence-claim-000037"
        )
        self.assertEqual(6, claim["level"])
        self.assertEqual("connected-device-execution", claim["level_name"])
        self.assertEqual("passed", claim["outcome"])
        summary = core.load_json(EVIDENCE / "validation-summary.json")
        self.assertEqual(
            ["passed"] * 5 + ["not-run"] * 3,
            [item["status"] for item in summary["build_evidence_levels"]],
        )
        self.assertEqual(
            ["passed"] * 6 + ["not-run"] * 2,
            [item["status"] for item in summary["product_evidence_levels"]],
        )
        self.assertFalse(summary["runner_device_actions_performed"])
        self.assertFalse(summary["observed_firmware_flash"])
        self.assertFalse(summary["observed_sd_card_write"])

    def test_artifact_binds_acyclic_producer_input_closure(self) -> None:
        artifact = next(
            value
            for value in self.context.records["artifact"]
            if value["artifact_id"] == "schuss-artifact-000029"
        )
        device = next(
            value
            for value in self.context.records["devices"]
            if (value["device_profile_id"], value["revision"])
            == ("schuss-device-profile-000001", 2)
        )
        target = next(
            value
            for value in self.context.records["target"]
            if (value["compute_target_id"], value["revision"])
            == ("schuss-compute-target-000001", 2)
        )
        closure_identity = [
            REQUEST_REFERENCE,
            RUNTIME_REFERENCE,
            INSTRUMENT_REFERENCE,
            {
                key: device[key]
                for key in ("device_profile_id", "revision", "content_hash")
            },
            {
                key: target[key]
                for key in ("compute_target_id", "revision", "content_hash")
            },
            handler_reference(descriptor()),
        ]
        expected = "sha256:" + hashlib.sha256(
            core.canonical_json(closure_identity).encode("utf-8")
        ).hexdigest()
        self.assertEqual(expected, artifact["input_closure_hash"])
        self.assertNotEqual(
            artifact["input_closure_hash"],
            self.plan["value"]["input_closure"]["hash"],
        )

    def test_task018_generated_records_and_retained_boundary_are_unchanged(self) -> None:
        files, manifest, _ = task018_generator.generated()
        files[
            "contracts/record-sets/task018-full-gills-v1.json"
        ] = manifest
        self.assertTrue(
            all(
                (ROOT / relative).read_bytes() == payload
                for relative, payload in files.items()
            )
        )
        old = core.load_json(TASK018_EVIDENCE)
        self.assertEqual(
            ["passed"] * 5 + ["not-run"] * 3,
            [item["status"] for item in old["evidence_levels"]],
        )
        self.assertFalse(old["device_actions_performed"])

    def test_correction_anchors_fail_closed(self) -> None:
        with self.assertRaisesRegex(
            ValueError, "GILLS_PANEL_DMA_SAFE_ANCHOR_INVALID:declaration"
        ):
            correct_mapped_cpp_dma_buffers("void unrelated();\n")

    def test_product_cli_selects_only_the_exact_task021_handler(self) -> None:
        with tempfile.TemporaryDirectory(prefix="schuss-task021-cli-") as temporary:
            completed = subprocess.run(
                [
                    str(ROOT / "bin/schuss"),
                    "build",
                    "execute",
                    "schuss-build-request-000002@5",
                    "--handler",
                    "schuss-build-handler-000003@2",
                    "--output-root",
                    str(Path(temporary) / "published"),
                    "--execute",
                    "--record-set",
                    str(RECORD_SET),
                    "--json",
                ],
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=300,
            )
            self.assertEqual(
                0, completed.returncode, completed.stderr.decode("utf-8")
            )
            value = json.loads(completed.stdout)["value"]
            self.assertEqual("success", value["status"])
            self.assertEqual(handler_reference(descriptor()), value["handler_reference"])
            target = next(
                item
                for item in value["artifacts"]
                if item["artifact_kind"] == "target-executable"
            )
            self.assertEqual(generator.TARGET_ELF_SHA256, target["byte_sha256"])


if __name__ == "__main__":
    unittest.main()
