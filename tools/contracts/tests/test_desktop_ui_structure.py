from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools/contracts"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import validate_desktop_ui_structure as desktop


VALIDATOR = TOOLS / "validate_desktop_ui_structure.py"


def copy_fixture_root(destination: Path) -> None:
    for relative in desktop.GOVERNED_PATHS:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)


class DesktopUiStructureTest(unittest.TestCase):
    def test_live_structure_is_valid_read_only_and_core_owned(self):
        summary = desktop.validate_structure(ROOT)
        self.assertEqual("valid", summary["status"], summary["diagnostics"])
        self.assertEqual([], summary["diagnostics"])
        self.assertEqual(
            "schuss-desktop-ui-structure-validation-v2", summary["schema_version"]
        )
        self.assertEqual(
            "schuss-desktop-core-boundary-v1", summary["boundary_schema_version"]
        )
        self.assertEqual(len(desktop.REQUIRED_APP_FILES), summary["file_count"])
        self.assertEqual(13, summary["planned_operation_count"])
        self.assertEqual(3, summary["runtime_capability_count"])
        self.assertEqual(0, summary["semantic_record_count"])

    def test_unreviewed_source_and_copied_semantic_record_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture_root = Path(temporary)
            copy_fixture_root(fixture_root)
            unexpected = fixture_root / desktop.APP_ROOT / "src/GraphEditor.tsx"
            unexpected.write_text("export const GraphEditor = () => null;\n", encoding="utf-8")
            record = fixture_root / desktop.APP_ROOT / "records/schuss-graph-999999-r1.json"
            record.parent.mkdir(parents=True)
            record.write_text("{}\n", encoding="utf-8")

            summary = desktop.validate_structure(fixture_root)
            codes = {item["code"] for item in summary["diagnostics"]}
            self.assertEqual("invalid", summary["status"])
            self.assertIn("DESKTOP_APP_PATH_UNEXPECTED", codes)
            self.assertIn("DESKTOP_SEMANTIC_RECORD_OWNERSHIP_INVALID", codes)
            self.assertEqual(1, summary["semantic_record_count"])

    def test_dependency_runtime_capability_and_tauri_permission_drift_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture_root = Path(temporary)
            copy_fixture_root(fixture_root)

            package_path = fixture_root / desktop.PACKAGE
            package = json.loads(package_path.read_bytes())
            package["dependencies"]["@mui/material"] = "9.0.0"
            package_path.write_bytes(desktop.stable_json_bytes(package))

            boundary_path = fixture_root / desktop.BOUNDARY
            boundary = json.loads(boundary_path.read_bytes())
            boundary["runtime_capabilities"].append(
                boundary["planned_capability_phases"][1]["operations"][0]
            )
            boundary_path.write_bytes(desktop.stable_json_bytes(boundary))

            capability_path = fixture_root / desktop.TAURI_CAPABILITY
            capability = json.loads(capability_path.read_bytes())
            capability["permissions"].append("shell:allow-execute")
            capability_path.write_bytes(desktop.stable_json_bytes(capability))

            summary = desktop.validate_structure(fixture_root)
            codes = {item["code"] for item in summary["diagnostics"]}
            self.assertEqual("invalid", summary["status"])
            self.assertIn("DESKTOP_PACKAGE_INVALID", codes)
            self.assertIn("DESKTOP_RUNTIME_CAPABILITY_INVALID", codes)
            self.assertIn("DESKTOP_TAURI_PERMISSION_INVALID", codes)

    def test_cli_is_cwd_independent_deterministic_and_read_only(self):
        governed = [ROOT / path for path in desktop.GOVERNED_PATHS]

        def snapshot():
            return {
                str(path.relative_to(ROOT)): (
                    path.stat().st_mtime_ns,
                    path.stat().st_size,
                    hashlib.sha256(path.read_bytes()).hexdigest(),
                )
                for path in governed
            }

        before = snapshot()
        environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        first = subprocess.run(
            [sys.executable, str(VALIDATOR)],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            check=False,
        )
        second = subprocess.run(
            [sys.executable, str(VALIDATOR)],
            cwd=ROOT.parent,
            env=environment,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, first.returncode, first.stderr.decode("utf-8"))
        self.assertEqual(b"", first.stderr)
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(1, first.stdout.count(b"\n"))
        self.assertEqual("valid", json.loads(first.stdout)["status"])
        self.assertEqual(before, snapshot())


if __name__ == "__main__":
    unittest.main()
