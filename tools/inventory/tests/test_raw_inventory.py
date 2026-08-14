import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).parents[1] / "export_raw_inventory.py"
SPEC = importlib.util.spec_from_file_location("raw_inventory", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RawInventoryTest(unittest.TestCase):
    def test_deterministic_multi_object_source_and_parse_issue(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            source.mkdir()
            (source / "multi.axo").write_text("<objdefs><objdef id='a'/><objdef id='b'/></objdefs>")
            (source / "broken.axp").write_text("<patch>")
            first = root / "first"
            second = root / "second"
            MODULE.export(first, [("fixture", source)])
            MODULE.export(second, [("fixture", source)])
            for relative in ("manifest.json", "raw/files.jsonl", "raw/issues.jsonl", "reports/summary.json", "reports/summary.md"):
                self.assertEqual((first / relative).read_bytes(), (second / relative).read_bytes())
            records = [json.loads(line) for line in (first / "raw/files.jsonl").read_text().splitlines()]
            self.assertEqual([row["path"] for row in records], ["broken.axp", "multi.axo"])
            self.assertEqual(records[0]["parse_status"], "error")
            self.assertEqual(records[1]["root_element"], "objdefs")

    def test_excludes_output_build_artifacts_and_symlinks(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source"
            source.mkdir()
            (source / "kept.AXO").write_text("<objdefs/>")
            (source / "Voice_HELP.AXP").write_text("<patch/>")
            for excluded in ("build", "DIST", ".git", "target"):
                directory = source / excluded
                directory.mkdir()
                (directory / "ignored.axp").write_text("<patch/>")
            output = source / "inventory"
            output.mkdir()
            (output / "previous.axs").write_text("<patch/>")
            (source / "linked.axo").symlink_to(source / "kept.AXO")
            MODULE.export(output, [("fixture", source)])
            records = [json.loads(line) for line in (output / "raw/files.jsonl").read_text().splitlines()]
            self.assertEqual([row["path"] for row in records], ["Voice_HELP.AXP", "kept.AXO"])
            self.assertIn("help", records[0]["detected_legacy_roles"])
            self.assertEqual(records[1]["detected_legacy_roles"], ["native-object"])

    def test_unreadable_candidate_is_an_issue_and_scan_continues(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            source.mkdir()
            unreadable = source / "a.axo"
            readable = source / "b.axo"
            unreadable.write_text("<objdefs/>")
            readable.write_text("<objdefs/>")
            original = Path.read_bytes

            def read_bytes(path):
                if path == unreadable:
                    raise PermissionError("fixture unreadable")
                return original(path)

            with mock.patch.object(Path, "read_bytes", read_bytes):
                MODULE.export(root / "output", [("fixture", source)])
            records = [json.loads(line) for line in (root / "output/raw/files.jsonl").read_text().splitlines()]
            self.assertEqual([row["parse_status"] for row in records], ["error", "ok"])
            issues = [json.loads(line) for line in (root / "output/raw/issues.jsonl").read_text().splitlines()]
            self.assertEqual(issues[0]["error_code"], "E_FILE_READ")

    def test_duplicate_source_names_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaisesRegex(ValueError, "source names must be unique"):
                MODULE.export(root / "output", [("same", root), ("same", root)])


if __name__ == "__main__":
    unittest.main()
