import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools/inventory"
sys.path.insert(0, str(TOOLS))

VALIDATOR_SPEC = importlib.util.spec_from_file_location(
    "validate_resolved_inventory", TOOLS / "validate_resolved_inventory.py"
)
VALIDATOR = importlib.util.module_from_spec(VALIDATOR_SPEC)
sys.modules[VALIDATOR_SPEC.name] = VALIDATOR
VALIDATOR_SPEC.loader.exec_module(VALIDATOR)

EXPORTER_SPEC = importlib.util.spec_from_file_location(
    "export_resolved_inventory", TOOLS / "export_resolved_inventory.py"
)
EXPORTER = importlib.util.module_from_spec(EXPORTER_SPEC)
sys.modules[EXPORTER_SPEC.name] = EXPORTER
EXPORTER_SPEC.loader.exec_module(EXPORTER)

FIXTURE = (
    ROOT
    / "legacy/ksoloti-bridge/fixtures/resolved-inventory/axoloti-factory"
)


def omission_issue(source_id, path, file_type, sha256):
    return {
        "schema_version": "legacy-resolved-issue-v0",
        "issue_index": 0,
        "severity": "warning",
        "stage": "reconcile",
        "code": "RAW_BASELINE_OMISSION",
        "location": {
            "kind": "object" if file_type == "axo" else "graph",
            "source_id": source_id,
            "path": path,
            "variant_index": None,
            "graph_index": None,
            "instance_index": None,
            "net_index": None,
            "endpoint_role": None,
            "endpoint_index": None,
        },
        "message": "fixture omission",
        "processing_continued": True,
        "facts": [
            {"name": "file_type", "value_type": "string", "value": file_type},
            {"name": "sha256", "value_type": "string", "value": sha256},
        ],
        "candidate_variant_indexes": [],
    }


class ResolvedInventoryFixtureTest(unittest.TestCase):
    def test_fixture_matrix_is_well_formed_and_explicit(self):
        files = sorted(
            path for path in FIXTURE.rglob("*") if path.suffix in {".axo", ".axs", ".axp"}
        )
        for path in files:
            ET.parse(path)

        multi = ET.parse(FIXTURE / "objects/fixture/multi-overload.axo").getroot()
        definitions = list(multi)
        self.assertEqual(3, len(definitions))
        self.assertEqual(["overload", "overload"], [item.attrib["id"] for item in definitions[:2]])
        self.assertNotIn("uuid", definitions[2].attrib)

        overload_graph = ET.parse(
            FIXTURE / "patches/ambiguous-overload.axp"
        ).getroot()
        overload_instances = overload_graph.findall("obj")
        self.assertEqual("fixture-overload-buffer", overload_instances[0].attrib["uuid"])
        self.assertNotIn("uuid", overload_instances[1].attrib)
        self.assertEqual("promoted", overload_instances[1].attrib["name"])

        duplicates = [
            ET.parse(FIXTURE / f"objects/fixture/duplicate-{which}.axo")
            .getroot()[0]
            .attrib["uuid"]
            for which in ("first", "second")
        ]
        self.assertEqual(["fixture-shared-explicit-uuid"] * 2, duplicates)

        parent = ET.parse(FIXTURE / "patches/relative/relative-parent.axp").getroot()
        child = ET.parse(FIXTURE / "patches/relative/relative-child.axs").getroot()
        self.assertEqual("./relative-child", parent.find("obj").attrib["type"])
        self.assertEqual("./relative-leaf", child.find("obj").attrib["type"])

        zombies = ET.parse(FIXTURE / "patches/zombies.axp").getroot()
        self.assertIsNotNone(zombies.find("zombie"))
        self.assertEqual("fixture/not present", zombies.findall("obj")[2].attrib["type"])
        endpoints = [
            endpoint.attrib
            for net in zombies.find("nets")
            for endpoint in list(net)
        ]
        self.assertTrue(any(item.get("obj") == "missing-instance" for item in endpoints))
        self.assertTrue(any(item.get("outlet") == "missing-outlet" for item in endpoints))
        self.assertTrue(any(item.get("inlet") == "missing-inlet" for item in endpoints))

        unsupported = ET.parse(FIXTURE / "patches/unsupported-content.axp").getroot()
        self.assertIsNotNone(unsupported.find("future-object"))
        self.assertEqual("source-after", unsupported.find("obj").attrib["name"])


class ResolvedSchemaTest(unittest.TestCase):
    def valid_manifest(self):
        return {
            "schema_version": "legacy-resolved-catalog-v0",
            "exporter": {"name": "fixture", "version": 1},
            "legacy_runtime": {
                "source_id": "patcher",
                "commit": "0" * 40,
                "classpath_fingerprint_sha256": "1" * 64,
                "java_version": "openjdk version 21",
            },
            "raw_snapshot": {
                "schema_version": "legacy-catalog-v0",
                "manifest_sha256": "2" * 64,
                "files_jsonl_sha256": "3" * 64,
            },
            "sources": [
                {"id": "patcher", "url": "https://example.invalid", "commit": "0" * 40, "observed_dirty": False}
            ],
            "object_roots": [{"order": 0, "source_id": "patcher", "relative_path": "objects"}],
            "graph_input_types": ["axs", "axp"],
            "options": {
                "phase": "java-resolved",
                "timestamp_included": False,
                "preference_writes": False,
                "subpatch_interface_projection": True,
                "target_artifact_generation": False,
                "target_compilation": False,
                "device_access": False,
            },
        }

    def test_strict_schema_supports_refs_one_of_all_of_and_contains(self):
        schema = json.loads(
            (ROOT / "schemas/legacy-resolved-manifest-v0.schema.json").read_text()
        )
        manifest = self.valid_manifest()
        VALIDATOR.validate_schema(manifest, schema)

        invalid = json.loads(json.dumps(manifest))
        invalid["unexpected"] = True
        with self.assertRaisesRegex(VALIDATOR.InventoryValidationError, "unexpected"):
            VALIDATOR.validate_schema(invalid, schema)

        invalid = json.loads(json.dumps(manifest))
        invalid["graph_input_types"] = ["axs", "axs"]
        with self.assertRaises(VALIDATOR.InventoryValidationError):
            VALIDATOR.validate_schema(invalid, schema)

    def test_summary_names_raw_omissions_and_disabled_roots(self):
        sha = "a" * 64
        raw = [
            {"source_repository": "factory", "path": "objects/a.axo", "file_type": "axo"},
            {"source_repository": "factory", "path": "patches/not-enabled.axo", "file_type": "axo"},
            {"source_repository": "factory", "path": "objects/compound.axs", "file_type": "axs"},
            {"source_repository": "factory", "path": "patches/graph.axs", "file_type": "axs"},
            {"source_repository": "factory", "path": "patches/graph.axp", "file_type": "axp"},
        ]
        objects = [
            {
                "export_status": "complete",
                "legacy_kind": "native_definition",
                "legacy_class": "fixture.Native",
                "legacy_id": "fixture/a",
                "legacy_object_list_index": 0,
                "origin": {"kind": "file", "path": "objects/a.axo"},
                "uuid": {"runtime_kind": "explicit", "durable_value": "fixture-a"},
            },
            {
                "export_status": "complete",
                "legacy_kind": "native_definition",
                "legacy_class": "fixture.Native",
                "legacy_id": "fixture/omitted",
                "legacy_object_list_index": 1,
                "origin": {"kind": "file", "path": "objects/out/omitted.axo"},
                "uuid": {"runtime_kind": "generated-nondeterministic", "durable_value": None},
            },
            {
                "export_status": "complete",
                "legacy_kind": "subpatch_catalog_placeholder",
                "legacy_class": "fixture.Subpatch",
                "legacy_id": "fixture/compound",
                "legacy_object_list_index": 2,
                "origin": {"kind": "file", "path": "objects/compound.axs"},
                "uuid": {"runtime_kind": "sentinel", "durable_value": "subpatch-a"},
            },
            {
                "export_status": "complete",
                "legacy_kind": "subpatch_catalog_placeholder",
                "legacy_class": "fixture.Subpatch",
                "legacy_id": "fixture/omitted compound",
                "legacy_object_list_index": 3,
                "origin": {"kind": "file", "path": "objects/out/omitted.axs"},
                "uuid": {"runtime_kind": "sentinel", "durable_value": "subpatch-b"},
            },
            {
                "export_status": "partial",
                "legacy_kind": "native_definition",
                "legacy_class": "fixture.Generated",
                "legacy_id": "fixture/a",
                "legacy_object_list_index": None,
                "origin": {"kind": "provider"},
                "uuid": {
                    "runtime_kind": "generated-nondeterministic",
                    "durable_value": None,
                },
            },
        ]
        graphs = [
            {"export_status": "complete", "instances": [], "nets": []}
            for _ in range(4)
        ]
        issues = [
            omission_issue("factory", "objects/out/omitted.axo", "axo", sha),
            omission_issue("factory", "objects/out/omitted.axs", "axs", sha),
        ]
        summary = VALIDATOR.build_summary(
            raw,
            objects,
            graphs,
            issues,
            enabled_object_roots={("factory", "objects")},
        )
        summary_schema = json.loads(
            (ROOT / "schemas/legacy-resolved-summary-v0.schema.json").read_text()
        )
        VALIDATOR.validate_schema(summary, summary_schema)
        self.assertEqual(
            {
                "raw_candidates": 2,
                "attempted": 2,
                "not_enabled": 1,
                "not_in_raw_baseline": 1,
                "strict_loaded": 2,
                "relaxed_loaded": 0,
                "failed": 0,
                "zero_definition": 0,
            },
            summary["object_files"],
        )
        self.assertEqual(
            {
                "raw_candidates": 2,
                "not_enabled": 1,
                "not_in_raw_baseline": 1,
                "registered": 2,
            },
            summary["catalog_subpatch_files"],
        )
        self.assertEqual(3, summary["graphs"]["raw_candidates"])
        self.assertEqual(4, summary["graphs"]["candidates"])
        self.assertEqual(0, summary["objects"]["overloaded_name_groups"])
        self.assertEqual(
            [{"kind": "file", "count": 4}, {"kind": "provider", "count": 1}],
            summary["objects"]["by_origin_kind"],
        )


class ResolvedHarnessTest(unittest.TestCase):
    def git(self, root, *args):
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return result.stdout.strip()

    def test_archive_uses_locked_commit_and_status_guard_detects_change(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repository = root / "source"
            repository.mkdir()
            self.git(repository, "init", "-q")
            (repository / "value.txt").write_text("locked\n")
            self.git(repository, "add", "value.txt")
            self.git(
                repository,
                "-c", "user.name=Schuss Test",
                "-c", "user.email=schuss@example.invalid",
                "commit", "-q", "-m", "fixture",
            )
            commit = self.git(repository, "rev-parse", "HEAD")
            (repository / "value.txt").write_text("dirty live value\n")
            source = EXPORTER.LockedSource(
                source_id="fixture",
                url="https://example.invalid/fixture.git",
                commit=commit,
                path=repository.resolve(),
                status=EXPORTER.git_status(repository),
            )
            archive = root / "archive"
            EXPORTER.archive_commit(source, archive)
            self.assertEqual("locked\n", (archive / "value.txt").read_text())
            EXPORTER.verify_sources_unchanged([source])
            (repository / "new-untracked.txt").write_text("change\n")
            with self.assertRaisesRegex(EXPORTER.ExportError, "status changed"):
                EXPORTER.verify_sources_unchanged([source])

    def test_two_process_artifacts_are_byte_compared(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first, second = root / "first", root / "second"
            for output in (first, second):
                for artifact in EXPORTER.ARTIFACTS:
                    path = output / artifact
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text("{}\n")
            EXPORTER.compare_artifacts(first, second)
            (second / EXPORTER.ARTIFACTS[0]).write_text('{"different":true}\n')
            with self.assertRaisesRegex(EXPORTER.ExportError, "fresh JVM outputs differ"):
                EXPORTER.compare_artifacts(first, second)

    def test_omission_issue_is_deterministically_injected(self):
        with tempfile.TemporaryDirectory() as temp:
            stage = Path(temp)
            (stage / "resolved").mkdir()
            (stage / "resolved/issues.jsonl").write_text("")
            (stage / "resolved/graphs.jsonl").write_text("")
            eligible = {
                ("factory", "objects/a.axo"): {"file_type": "axo", "sha256": "a" * 64},
                ("factory", "objects/out/b.axo"): {"file_type": "axo", "sha256": "b" * 64},
            }
            raw = [{"source_repository": "factory", "path": "objects/a.axo"}]
            EXPORTER.add_baseline_omission_issues(stage, eligible, raw)
            first = (stage / "resolved/issues.jsonl").read_bytes()
            EXPORTER.add_baseline_omission_issues(stage, eligible, raw)
            self.assertEqual(first, (stage / "resolved/issues.jsonl").read_bytes())
            issues = VALIDATOR.load_jsonl(stage / "resolved/issues.jsonl")
            self.assertEqual("RAW_BASELINE_OMISSION", issues[0]["code"])
            self.assertEqual("b" * 64, issues[0]["facts"][1]["value"])


if __name__ == "__main__":
    unittest.main()
