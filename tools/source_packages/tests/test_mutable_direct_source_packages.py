from __future__ import annotations

import json
from pathlib import Path
import unittest

from tools.source_packages import generate_mutable_direct_v1 as generator
from tools.source_packages.validate_source_package import validate_package


ROOT = Path(__file__).resolve().parents[3]


class MutableDirectSourcePackageTests(unittest.TestCase):
    def test_generated_manifests_are_fresh_and_authority_sparse(self) -> None:
        expected_counts = {
            "mutable-eurorack-braids-v1": 12,
            "mutable-stmlib-v1": 5,
        }
        forbidden = {"archive_sha256", "archive_url", "commit", "declared_license_evidence", "repository_url"}
        for package_id, spec in generator.PACKAGES.items():
            generated = generator.generate_one(package_id, spec)
            retained = json.loads(
                (ROOT / spec["root"] / "SOURCE_PACKAGE.json").read_text(encoding="utf-8")
            )
            self.assertEqual(generated, retained)
            self.assertEqual(len(retained["closure"]["files"]), expected_counts[package_id])
            self.assertTrue(forbidden.isdisjoint(retained))
            self.assertTrue(forbidden.isdisjoint(retained["authority"]))

    def test_live_packages_pass_the_shared_validator(self) -> None:
        for package_id, spec in generator.PACKAGES.items():
            document, errors = validate_package(
                ROOT / spec["root"],
                expected_package_id=package_id,
                expected_package_revision="1",
                expected_source_release_id=spec["source_release_id"],
                expected_source_release_revision=1,
                expected_closure_manifest_sha256=spec["expected_manifest"],
            )
            self.assertIsNotNone(document)
            self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
