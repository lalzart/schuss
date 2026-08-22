from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools/contracts"
sys.path[:0] = [str(ROOT), str(TOOLS)]

import generate_task033_phase3_registry as generator  # noqa: E402
import validate_task033_phase3 as validator  # noqa: E402


class Task033Phase3GeneratedRegistryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads((ROOT / generator.MANIFEST_PATH).read_text())

    def test_generation_and_validation_are_fresh(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(TOOLS / "generate_task033_phase3_registry.py"), "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual("valid", validator.validate(ROOT)["status"])

    def test_manifest_is_exact_seven_entry_provider_closure(self) -> None:
        result = validator.validate(ROOT)
        self.assertEqual(7, result["factory_count"])
        self.assertTrue(result["phase2_source_release_and_provider_preserved"])
        self.assertTrue(result["task031_task032_trees_preserved"])
        self.assertTrue(result["runtime_v1_cpp_byte_preserved"])
        self.assertFalse(result["semantic_record_provider_or_capability_allocated"])
        self.assertFalse(result["runtime_behavior_changed"])

    def test_duplicate_factory_identity_fails_closed(self) -> None:
        value = copy.deepcopy(self.manifest)
        value["factories"][1]["factory_id"] = value["factories"][0]["factory_id"]
        with self.assertRaisesRegex(
            ValueError, "NATIVE_REGISTRY_FACTORY_DUPLICATE"
        ):
            generator._validate_manifest(ROOT, value)

    def test_provider_binding_drift_fails_closed(self) -> None:
        value = copy.deepcopy(self.manifest)
        value["factories"][0]["factory_id"] = "schuss.rt.drift-q27-v0"
        with self.assertRaisesRegex(
            ValueError, "NATIVE_REGISTRY_PROVIDER_BINDING_MISMATCH"
        ):
            generator._validate_manifest(ROOT, value)

    def test_contract_facet_drift_fails_closed(self) -> None:
        value = copy.deepcopy(self.manifest)
        value["factories"][0]["inputs"][0]["fractional_bits"] = 27
        with self.assertRaisesRegex(
            ValueError, "NATIVE_REGISTRY_INPUT_FACET_MISMATCH"
        ):
            generator._validate_manifest(ROOT, value)

    def test_generated_python_is_the_only_lowerer_descriptor_source(self) -> None:
        source = (ROOT / "packages/schuss_core/variable_host_runtime.py").read_text()
        self.assertIn("FACTORY_DESCRIPTORS", source)
        self.assertNotIn("FACTORY_SPECS = (", source)
        for factory in self.manifest["factories"]:
            self.assertNotIn(factory["factory_id"], source)

    def test_schema_enums_are_derived_in_stable_order(self) -> None:
        expected = sorted(item["factory_id"] for item in self.manifest["factories"])
        package = json.loads((ROOT / generator.PACKAGE_SCHEMA).read_text())
        observation = json.loads((ROOT / generator.OBSERVATION_SCHEMA).read_text())
        self.assertEqual(expected, validator._factory_enum(package, observation=False))
        self.assertEqual(expected, validator._factory_enum(observation, observation=True))


if __name__ == "__main__":
    unittest.main()
