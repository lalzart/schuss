from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from tools.source_packages.validate_source_package import validate_package


ROOT = Path(__file__).resolve().parents[3]
PACKAGE = ROOT / "packages" / "dsp_sources" / "mutable_ksoloti_v1"
VALIDATOR = ROOT / "tools" / "source_packages" / "validate_source_package.py"
GENERATOR = ROOT / "tools" / "source_packages" / "generate_mutable_ksoloti_v1.py"
EXPECTED_SOURCE_RELEASE_ID = "schuss-source-release-000005"
EXPECTED_SOURCE_RELEASE_REVISION = 1
EXPECTED_SOURCE_RELEASE_HASH = "sha256:51750a00f07f98c783cfc1972580c9399ac64690eaf3d40ad6e1d736698c972c"
EXPECTED_CLOSURE_MANIFEST = "0903f25038f0116422a8512b15f1c3531e7b22371da8ad393b130a16d821508f"


class SourcePackageValidatorTest(unittest.TestCase):
    def _copy_package(self, temporary: str) -> Path:
        destination = Path(temporary) / "package"
        shutil.copytree(PACKAGE, destination)
        return destination

    def _load(self, package: Path) -> dict[str, object]:
        return json.loads((package / "SOURCE_PACKAGE.json").read_text(encoding="utf-8"))

    def _write(self, package: Path, document: dict[str, object]) -> None:
        (package / "SOURCE_PACKAGE.json").write_text(
            json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    def _codes(self, package: Path, **kwargs: object) -> set[str]:
        _, errors = validate_package(
            package,
            expected_package_id="mutable-ksoloti-v1",
            expected_package_revision="1",
            expected_source_release_id=EXPECTED_SOURCE_RELEASE_ID,
            expected_source_release_revision=EXPECTED_SOURCE_RELEASE_REVISION,
            expected_source_release_content_hash=EXPECTED_SOURCE_RELEASE_HASH,
            expected_closure_manifest_sha256=EXPECTED_CLOSURE_MANIFEST,
            **kwargs,
        )
        return {error.code for error in errors}

    def test_live_package_is_exact_and_output_is_portable(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(VALIDATOR),
                str(PACKAGE),
                "--expected-package-id",
                "mutable-ksoloti-v1",
                "--expected-package-revision",
                "1",
                "--expected-source-release-id",
                EXPECTED_SOURCE_RELEASE_ID,
                "--expected-source-release-revision",
                str(EXPECTED_SOURCE_RELEASE_REVISION),
                "--expected-source-release-content-hash",
                EXPECTED_SOURCE_RELEASE_HASH,
                "--expected-closure-manifest-sha256",
                EXPECTED_CLOSURE_MANIFEST,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(
            completed.stdout,
            "source package: valid physical closure; Task 033 source release authoritative\n",
        )
        self.assertNotIn(str(ROOT), completed.stdout + completed.stderr)

    def test_manifest_is_generated_from_authority_without_parallel_catalog_metadata(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(GENERATOR), "--check"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        document = self._load(PACKAGE)
        encoded = json.dumps(document, sort_keys=True)
        self.assertNotIn("repository_url", encoded)
        self.assertNotIn("declared_license_evidence", encoded)
        self.assertNotIn("license_expression", encoded)
        self.assertEqual(
            document["authority"]["source_release"]["source_release_id"],
            EXPECTED_SOURCE_RELEASE_ID,
        )
        self.assertEqual(document["claims"]["provides"], ["physical-build-closure"])
        self.assertIn("collection-membership", document["claims"]["does_not_provide"])
        self.assertIn("provider-identity", document["claims"]["does_not_provide"])

    def test_modified_missing_and_extra_upstream_files_fail_closed(self) -> None:
        for case in ("modified", "missing", "extra"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                package = self._copy_package(temporary)
                upstream = package / "upstream" / "firmware" / "mutable_instruments"
                target = upstream / "stmlib" / "stmlib.h"
                if case == "modified":
                    target.write_bytes(target.read_bytes() + b"\n")
                    expected = "CLOSURE_FILE_DRIFT"
                elif case == "missing":
                    target.unlink()
                    expected = "MISSING_CLOSURE_FILE"
                else:
                    (upstream / "extra.h").write_text("extra\n", encoding="utf-8")
                    expected = "EXTRA_CLOSURE_FILE"
                self.assertIn(expected, self._codes(package))

    def test_duplicate_unsorted_and_nonportable_paths_fail_closed(self) -> None:
        cases = {
            "duplicate_file": "DUPLICATE_FILE_PATH",
            "unsorted_component": "UNSORTED_COMPONENT_PATH",
            "duplicate_component_path": "DUPLICATE_COMPONENT_PATH",
            "absolute_file": "NON_PORTABLE_FILE_PATH",
            "escaping_file": "NON_PORTABLE_FILE_PATH",
            "component_outside": "COMPONENT_PATH_OUTSIDE_CLOSURE",
        }
        for case, expected in cases.items():
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                package = self._copy_package(temporary)
                document = self._load(package)
                files = document["closure"]["files"]
                groups = document["component_groups"]
                if case == "duplicate_file":
                    files.append(copy.deepcopy(files[-1]))
                elif case == "unsorted_component":
                    groups[0]["paths"] = list(reversed(groups[0]["paths"]))
                elif case == "duplicate_component_path":
                    groups[0]["paths"].append(groups[0]["paths"][-1])
                elif case == "absolute_file":
                    files[0]["path"] = "/absolute.cpp"
                elif case == "escaping_file":
                    files[0]["path"] = "../escape.cpp"
                else:
                    groups[0]["paths"].append("firmware/mutable_instruments/missing.h")
                    groups[0]["paths"].sort()
                self._write(package, document)
                self.assertIn(expected, self._codes(package))

    def test_wrong_identity_hash_and_unknown_component_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package = self._copy_package(temporary)
            document = self._load(package)
            document["authority"]["source_release"]["content_hash"] = "sha256:" + "0" * 64
            document["closure"]["manifest_sha256"] = "0" * 64
            self._write(package, document)
            codes = self._codes(package, requested_components=["unknown-component"])
            self.assertIn("SOURCE_RELEASE_REFERENCE_DRIFT", codes)
            self.assertIn("CLOSURE_MANIFEST_MISMATCH", codes)
            self.assertIn("UNKNOWN_COMPONENT", codes)

    def test_notice_encoding_and_unknown_fields_fail_closed(self) -> None:
        cases = {
            "notice": "MISSING_NOTICE",
            "encoding": "MANIFEST_ENCODING",
            "unknown_field": "UNKNOWN_TOP_LEVEL_FIELDS",
        }
        for case, expected in cases.items():
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                package = self._copy_package(temporary)
                if case == "notice":
                    (package / "THIRD_PARTY_NOTICES.md").unlink()
                elif case == "encoding":
                    (package / "SOURCE_PACKAGE.json").write_bytes(b"\xff")
                else:
                    document = self._load(package)
                    document["unknown"] = True
                    self._write(package, document)
                self.assertIn(expected, self._codes(package))

    def test_cmake_helper_rejects_unknown_component(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            completed = subprocess.run(
                [
                    "cmake",
                    "-S",
                    str(PACKAGE / "smoke"),
                    "-B",
                    str(Path(temporary) / "build"),
                    "-DMUTABLE_KSOLOTI_V1_SMOKE_COMPONENTS=unknown-component",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("UNKNOWN_COMPONENT", completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
