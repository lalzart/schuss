from __future__ import annotations

from collections import Counter
from contextlib import redirect_stdout
import copy
import importlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools/contracts"
sys.path[:0] = [str(ROOT), str(TOOLS)]

import record_set_rules  # noqa: E402
import retained_evidence  # noqa: E402
import compiler_determinism_matrix  # noqa: E402
import historical_reproduction  # noqa: E402
import run_task016  # noqa: E402
import run_task017  # noqa: E402
import run_task018  # noqa: E402
import run_task021  # noqa: E402
import run_task022  # noqa: E402
import run_task027_fresh_root  # noqa: E402
import run_task028_fresh_root  # noqa: E402
import run_task029_fresh_process  # noqa: E402
import run_task030_fresh_root  # noqa: E402
import run_task032_fresh_root  # noqa: E402
import run_task033_phase2_reproduction  # noqa: E402
import validator_core as core  # noqa: E402
from tools.validation import run as validation_run  # noqa: E402
from tools.validation import contract_suite, unittest_gate  # noqa: E402


LATEST = Path("contracts/record-sets/task033-phase2-collection-provider-v1.json")


def _copy_record_set_fixture(
    destination: Path, manifests: tuple[Path, ...]
) -> None:
    paths = {record_set_rules.RECORD_SET_SCHEMA, *manifests}
    for manifest_path in manifests:
        manifest = core.load_json(ROOT / manifest_path)
        paths.update(
            Path(item["portable_path"])
            for group in ("schema_members", "record_members")
            for item in manifest[group]
        )
        for directory in manifest["enforced_directories"]:
            (destination / directory).mkdir(parents=True, exist_ok=True)
    for relative in sorted(paths):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)


class Task035RecordSetLoadingTest(unittest.TestCase):
    def test_selected_union_and_each_manifest_are_validated_once(self) -> None:
        manifest = core.load_json(ROOT / LATEST)
        expected_paths = {
            (ROOT / item["portable_path"]).resolve()
            for group in ("schema_members", "record_members")
            for item in manifest[group]
        }
        original_hash = core.sha256_file
        original_content_hash = core.record_content_hash
        hashed_paths: list[Path] = []
        manifest_ids: list[str] = []

        def counted_hash(path: Path) -> str:
            hashed_paths.append(Path(path).resolve())
            return original_hash(path)

        def counted_content_hash(value, schema):
            if isinstance(value, dict) and value.get("schema_version") == "record-set-v0":
                manifest_ids.append(value["record_set_id"])
            return original_content_hash(value, schema)

        with mock.patch.object(core, "sha256_file", side_effect=counted_hash), mock.patch.object(
            core, "record_content_hash", side_effect=counted_content_hash
        ):
            loaded = record_set_rules.load_record_set(ROOT, LATEST)

        self.assertEqual(144, len(loaded.schemas))
        self.assertEqual(477, sum(len(values) for values in loaded.records.values()))
        self.assertEqual(expected_paths, set(hashed_paths))
        self.assertEqual(
            {path: 1 for path in expected_paths}, Counter(hashed_paths)
        )
        self.assertGreater(len(manifest_ids), 1)
        self.assertEqual(
            {identifier: 1 for identifier in manifest_ids}, Counter(manifest_ids)
        )

    def test_independent_loads_observe_members_again(self) -> None:
        manifest = core.load_json(ROOT / LATEST)
        watched = (ROOT / manifest["record_members"][0]["portable_path"]).resolve()
        original = core.sha256_file
        visits = 0

        def counted(path: Path) -> str:
            nonlocal visits
            if Path(path).resolve() == watched:
                visits += 1
            return original(path)

        with mock.patch.object(core, "sha256_file", side_effect=counted):
            record_set_rules.load_record_set(ROOT, LATEST)
            record_set_rules.load_record_set(ROOT, LATEST)
        self.assertEqual(2, visits)

    def test_cycle_and_stale_parent_override_still_fail_closed(self) -> None:
        with self.assertRaisesRegex(record_set_rules.RecordSetError, "parent cycle"):
            record_set_rules.load_record_set(
                ROOT, LATEST, accepted_manifest_path=ROOT / LATEST
            )
        wrong_parent = Path("contracts/record-sets/task032-variable-host-runtime-v1.json")
        with self.assertRaisesRegex(
            record_set_rules.RecordSetError, "parent reference mismatch"
        ):
            record_set_rules.load_record_set(
                ROOT, LATEST, accepted_manifest_path=ROOT / wrong_parent
            )

    def test_parent_cannot_omit_a_schema_used_by_its_own_record(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied_root = Path(temporary) / "repository"
            child_relative = Path("contracts/record-sets/task009-prospective-v0.json")
            _copy_record_set_fixture(
                copied_root,
                (record_set_rules.ACCEPTED_RECORD_SET, child_relative),
            )
            parent_path = copied_root / record_set_rules.ACCEPTED_RECORD_SET
            child_path = copied_root / child_relative
            parent = core.load_json(parent_path)
            child = core.load_json(child_path)
            first_record = core.load_json(
                copied_root / parent["record_members"][0]["portable_path"]
            )
            omitted_version = first_record["schema_version"]
            parent["schema_members"] = [
                item
                for item in parent["schema_members"]
                if item["schema_version"] != omitted_version
            ]
            record_set_schema = core.load_json(
                copied_root / record_set_rules.RECORD_SET_SCHEMA
            )
            parent["content_hash"] = core.record_content_hash(
                parent, record_set_schema
            )
            child["parent_reference"]["content_hash"] = parent["content_hash"]
            child["content_hash"] = core.record_content_hash(child, record_set_schema)
            parent_path.write_text(core.canonical_json(parent) + "\n", encoding="utf-8")
            child_path.write_text(core.canonical_json(child) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(
                record_set_rules.RecordSetError, "parent record schema is not listed"
            ):
                record_set_rules.load_record_set(copied_root, child_relative)

    def test_selected_and_overridden_parent_manifests_cannot_escape_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            external = Path(temporary) / "external.json"
            external.write_bytes((ROOT / LATEST).read_bytes())
            with self.assertRaisesRegex(
                record_set_rules.RecordSetError, "path escapes repository"
            ):
                record_set_rules.load_record_set(ROOT, external)
            external.write_bytes(
                (ROOT / record_set_rules.ACCEPTED_RECORD_SET).read_bytes()
            )
            with self.assertRaisesRegex(
                record_set_rules.RecordSetError, "path escapes repository"
            ):
                record_set_rules.load_record_set(
                    ROOT,
                    Path("contracts/record-sets/task009-prospective-v0.json"),
                    accepted_manifest_path=external,
                )

    def test_accepted_baseline_cannot_include_a_parent_reference(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied_root = Path(temporary) / "repository"
            _copy_record_set_fixture(
                copied_root, (record_set_rules.ACCEPTED_RECORD_SET,)
            )
            path = copied_root / record_set_rules.ACCEPTED_RECORD_SET
            manifest = core.load_json(path)
            manifest["parent_reference"] = {
                "status": "included",
                "record_set_id": "schuss-record-set-999999",
                "revision": 1,
                "content_hash": "sha256:" + "0" * 64,
            }
            schema = core.load_json(copied_root / record_set_rules.RECORD_SET_SCHEMA)
            manifest["content_hash"] = core.record_content_hash(manifest, schema)
            path.write_text(core.canonical_json(manifest) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(
                record_set_rules.RecordSetError, "must omit its parent reference"
            ):
                record_set_rules.load_record_set(
                    copied_root, record_set_rules.ACCEPTED_RECORD_SET
                )

    def test_enforced_directory_rejects_an_unlisted_symlink_alias(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied_root = Path(temporary) / "repository"
            _copy_record_set_fixture(
                copied_root, (record_set_rules.ACCEPTED_RECORD_SET,)
            )
            manifest = core.load_json(
                copied_root / record_set_rules.ACCEPTED_RECORD_SET
            )
            enforced = manifest["enforced_directories"][0]
            member = next(
                item
                for item in manifest["record_members"]
                if Path(item["portable_path"]).parent.as_posix() == enforced
            )
            target = copied_root / member["portable_path"]
            alias = target.parent / "unlisted-alias.json"
            alias.symlink_to(target.name)
            with self.assertRaisesRegex(
                record_set_rules.RecordSetError, "contains a symlink"
            ):
                record_set_rules.load_record_set(
                    copied_root, record_set_rules.ACCEPTED_RECORD_SET
                )


class Task035ValidationPlanTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = validation_run._load_manifest()

    def test_release_expansion_is_atomic_and_deduplicated(self) -> None:
        expanded = validation_run._expand_profiles(self.manifest, ["release"])
        self.assertEqual(len(expanded), len(set(expanded)))
        self.assertEqual(
            {
                item["id"]
                for item in self.manifest["checks"]
                if not item.get("explicit_only", False)
                and item["validation_profile"] != "configured-sources"
            },
            set(expanded),
        )

    def test_accepted_historical_governance_fixture_is_unchanged(self) -> None:
        fixture = (
            ROOT
            / "tools/contracts/tests/fixtures/backbone-governance-negative-fixtures.json"
        )
        self.assertEqual(
            "195ebe27e18902924126dd3828687563728ff468ef3e3ccbeacf4c25cfce76dd",
            core.sha256_file(fixture),
        )

    def test_current_profile_excludes_external_and_expensive_work(self) -> None:
        selected = validation_run._expand_profiles(self.manifest, ["current"])
        self.assertTrue(selected)
        self.assertFalse(
            any(
                identifier.startswith(("native.", "reproduction.", "configured."))
                for identifier in selected
            )
        )

    def test_native_execution_preflight_runs_before_native_work(self) -> None:
        selected = validation_run._expand_profiles(self.manifest, ["native"])
        self.assertEqual("native.execution-preflight", selected[0])
        by_id = {item["id"]: item for item in self.manifest["checks"]}
        for identifier in (
            "native.execution-preflight",
            "native.task016-handler",
            "native.task018-handler",
            "native.task021-handler",
        ):
            with self.subTest(identifier=identifier):
                self.assertEqual(
                    {"git", "/usr/bin/make"},
                    set(by_id[identifier]["tool_prerequisites"]),
                )
        self.assertEqual(
            ["native.execution-preflight", "native.task016-handler"],
            validation_run._resolve_check_dependencies(
                self.manifest, ["native.task016-handler"]
            ),
        )

    def test_preflight_incomplete_is_not_reported_as_a_skipped_test(self) -> None:
        preflight = next(
            item
            for item in self.manifest["checks"]
            if item["id"] == "native.execution-preflight"
        )
        completed = mock.Mock(
            returncode=3,
            stdout=b"",
            stderr=b'{"diagnostic_code":"NATIVE_EXECUTION_PREREQUISITE_UNAVAILABLE"}\n',
        )
        with mock.patch.object(
            validation_run.subprocess, "run", return_value=completed
        ):
            result = validation_run._run_check(preflight)
        self.assertEqual("incomplete", result["status"])
        self.assertEqual(
            "VALIDATION_PREFLIGHT_INCOMPLETE", result["diagnostic_code"]
        )

    def test_copied_root_checks_declare_git_and_the_copy_helper(self) -> None:
        by_id = {item["id"]: item for item in self.manifest["checks"]}
        helper = "tools/contracts/compiler_determinism_matrix.py"
        for identifier in (
            "reproduction.task023",
            "reproduction.task030",
            "reproduction.task032",
            "reproduction.task033-phase2",
        ):
            with self.subTest(identifier=identifier):
                self.assertIn("git", by_id[identifier]["tool_prerequisites"])
                self.assertIn(helper, by_id[identifier]["inputs"])
        self.assertIn(
            "git",
            by_id["reproduction.task027-historical"]["tool_prerequisites"],
        )
        historical_helper = "tools/contracts/historical_reproduction.py"
        historical = {
            "reproduction.task016": (
                run_task016,
                "b28c7b6bdc98a2e06e1a19180bc84ad01fab4ac7",
            ),
            "reproduction.task017": (
                run_task017,
                "b28c7b6bdc98a2e06e1a19180bc84ad01fab4ac7",
            ),
            "reproduction.task018": (
                run_task018,
                "0ee69391bc2d43f4caf2580a3f0db139249d2307",
            ),
            "reproduction.task021": (
                run_task021,
                "8ca4907e760951e59580e1f0c5916a7e717ff88c",
            ),
            "reproduction.task022": (
                run_task022,
                "a5fa3287d037a2eac9909fafe9ea1fb06aa7ce90",
            ),
            "reproduction.task028": (
                run_task028_fresh_root,
                "5e57d29d729af8af36e90745bec9188256558680",
            ),
        }
        retained_helper = "tools/contracts/retained_evidence.py"
        for identifier, (module, commit) in historical.items():
            with self.subTest(identifier=identifier):
                self.assertIn("git", by_id[identifier]["tool_prerequisites"])
                self.assertIn(historical_helper, by_id[identifier]["inputs"])
                self.assertIn(retained_helper, by_id[identifier]["inputs"])
                self.assertEqual(commit, module.HISTORICAL_COMMIT)
        for identifier in ("reproduction.task018", "reproduction.task021"):
            self.assertTrue(by_id[identifier]["explicit_only"])
            self.assertEqual(
                ["catalog/sources.local.yml"],
                by_id[identifier]["prerequisites"],
            )
        self.assertEqual(
            core.load_json(
                ROOT / "evidence/task029-completion-v1/validation-summary.json"
            ),
            run_task029_fresh_process.check_retained(),
        )

    def test_historical_archive_rejects_an_escaping_member(self) -> None:
        archive_bytes = io.BytesIO()
        with tarfile.open(fileobj=archive_bytes, mode="w") as archive:
            archive.addfile(tarfile.TarInfo("../escape"))
        archived = mock.Mock(
            returncode=0, stdout=archive_bytes.getvalue(), stderr=b""
        )
        with mock.patch.object(
            historical_reproduction.subprocess, "run", return_value=archived
        ), self.assertRaisesRegex(ValueError, "unsafe member"):
            historical_reproduction.reproduce_summary(
                repository_root=ROOT,
                completion_commit="0" * 40,
                runner_path=Path("tools/contracts/run_task017.py"),
                retained_summary={},
                report_schema_version="test-report-v1",
            )

    def test_every_declared_gated_method_is_skipped_in_current_profile(self) -> None:
        for item in self.manifest["gated_tests"]:
            module_name, class_name, method_name = item["test"].rsplit(".", 2)
            method = getattr(getattr(importlib.import_module(module_name), class_name), method_name)
            self.assertTrue(
                getattr(method, "__unittest_skip__", False), item["test"]
            )
            self.assertEqual(
                item["profile"],
                getattr(method, "__schuss_validation_profile__", None),
                item["test"],
            )

    def test_every_decorated_method_is_declared_in_the_plan(self) -> None:
        discovered = unittest.defaultTestLoader.discover(
            str(ROOT / "tools/contracts/tests"), pattern="test_*.py"
        )
        decorated: dict[str, str] = {}
        for test in contract_suite._leaf_tests(discovered):
            method_name = getattr(test, "_testMethodName", None)
            if method_name is None:
                continue
            method = getattr(test.__class__, method_name)
            profile = getattr(method, "__schuss_validation_profile__", None)
            if profile is None:
                continue
            identifier = test.id()
            if identifier.startswith("test_"):
                identifier = "tools.contracts.tests." + identifier
            decorated[identifier] = profile
        declared = {
            item["test"]: item["profile"] for item in self.manifest["gated_tests"]
        }
        self.assertEqual(declared, decorated)

    def test_duplicate_gated_classification_is_rejected(self) -> None:
        invalid = copy.deepcopy(self.manifest)
        invalid["gated_tests"].append(copy.deepcopy(invalid["gated_tests"][0]))
        with self.assertRaisesRegex(validation_run.ValidationPlanError, "declared twice"):
            validation_run._validate_manifest(invalid)

    def test_validation_dependency_cycles_are_rejected(self) -> None:
        invalid = copy.deepcopy(self.manifest)
        by_id = {item["id"]: item for item in invalid["checks"]}
        by_id["native.task016-handler"]["depends_on"] = [
            "native.task018-handler"
        ]
        by_id["native.task018-handler"]["depends_on"] = [
            "native.task016-handler"
        ]
        with self.assertRaisesRegex(
            validation_run.ValidationPlanError, "dependency cycle"
        ):
            validation_run._validate_manifest(invalid)

    def test_check_profile_mismatch_is_rejected(self) -> None:
        invalid = copy.deepcopy(self.manifest)
        invalid["checks"][0]["validation_profile"] = "compatibility"
        invalid["checks"][0]["cost_class"] = "semantic"
        with self.assertRaisesRegex(validation_run.ValidationPlanError, "profile mismatch"):
            validation_run._validate_manifest(invalid)

    def test_manifest_rejects_unknown_fields_costs_and_inputs(self) -> None:
        cases = []
        unknown_field = copy.deepcopy(self.manifest)
        unknown_field["checks"][0]["typo_field"] = True
        cases.append((unknown_field, "invalid validation check fields"))
        wrong_cost = copy.deepcopy(self.manifest)
        wrong_cost["checks"][0]["cost_class"] = "native"
        cases.append((wrong_cost, "profile/cost mismatch"))
        missing_input = copy.deepcopy(self.manifest)
        missing_input["checks"][0]["inputs"] = [
            "tools/task035-definitely-missing.py"
        ]
        cases.append((missing_input, "unknown validation inputs"))
        for manifest, diagnostic in cases:
            with self.subTest(diagnostic=diagnostic), self.assertRaisesRegex(
                validation_run.ValidationPlanError, diagnostic
            ):
                validation_run._validate_manifest(manifest)

    def test_partitions_load_their_modules_directly(self) -> None:
        compatibility = sorted(self.manifest["compatibility_test_modules"])
        with mock.patch.object(
            validation_run, "_load_manifest", return_value=self.manifest
        ), mock.patch.object(
            unittest.defaultTestLoader,
            "loadTestsFromNames",
            return_value=unittest.TestSuite(),
        ) as load:
            contract_suite.selected_suite("compatibility")
        self.assertEqual((compatibility,), load.call_args.args)

    def test_only_plans_an_atomic_expensive_check_without_running_it(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            code = validation_run.main(
                ["--plan", "--only", "native.runtime-cmake"]
            )
        self.assertEqual(0, code)
        plan = json.loads(output.getvalue())
        self.assertEqual(["native.runtime-cmake"], plan["selected_check_ids"])

    def test_custom_manifest_is_inspection_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "manifest.json"
            path.write_text(json.dumps(self.manifest), encoding="utf-8")
            with mock.patch.object(
                validation_run,
                "run_profiles",
                side_effect=AssertionError("custom manifest executed"),
            ), redirect_stdout(io.StringIO()), mock.patch(
                "sys.stderr", io.StringIO()
            ):
                code = validation_run.main(
                    ["--manifest", str(path), "--profile", "current"]
                )
        self.assertEqual(1, code)

    def test_missing_prerequisite_preflights_before_any_other_check(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        configured = next(
            item for item in manifest["checks"] if item["id"] == "configured.sources"
        )
        configured["prerequisites"] = ["catalog/task035-definitely-missing.yml"]
        configured["inputs"] = ["catalog/task035-definitely-missing.yml"]
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            code, report = validation_run.run_profiles(
                ["release"],
                requested_checks=["configured.sources"],
                manifest_path=path,
            )
        self.assertEqual(2, code)
        self.assertEqual("incomplete", report["summary"]["status"])
        self.assertEqual(["configured.sources"], [item["id"] for item in report["checks"]])
        self.assertGreater(report["summary"]["not_run"], 0)

    def test_missing_tool_preflights_before_any_other_check(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        native = next(
            item for item in manifest["checks"] if item["id"] == "native.runtime-cmake"
        )
        native["tool_prerequisites"] = ["task035-definitely-missing-tool"]
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            code, report = validation_run.run_profiles(
                ["current"],
                requested_checks=["native.runtime-cmake"],
                manifest_path=path,
            )
        self.assertEqual(2, code)
        self.assertEqual(
            ["native.runtime-cmake"], [item["id"] for item in report["checks"]]
        )
        self.assertEqual(
            "MISSING_VALIDATION_TOOL_PREREQUISITE",
            report["checks"][0]["diagnostic_code"],
        )
        self.assertGreater(report["summary"]["not_run"], 0)

    def test_explicit_unittest_skip_is_incomplete_not_passed(self) -> None:
        selected = self.manifest["gated_tests"][0]["test"]
        with redirect_stdout(io.StringIO()), mock.patch("sys.stderr", io.StringIO()):
            self.assertEqual(3, unittest_gate.main([selected]))

    def test_unittest_gate_script_resolves_repository_modules(self) -> None:
        selected = (
            "tools.contracts.tests.test_task035_validation_consolidation."
            "Task035ValidationPlanTest.test_release_expansion_is_atomic_and_deduplicated"
        )
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools/validation/unittest_gate.py"),
                selected,
            ],
            cwd=ROOT.parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(
            0,
            completed.returncode,
            completed.stderr.decode("utf-8", errors="replace"),
        )

    def test_legacy_check_modes_do_not_reproduce_evidence(self) -> None:
        for module in (
            run_task016,
            run_task017,
            run_task018,
            run_task021,
            run_task022,
            run_task028_fresh_root,
        ):
            with self.subTest(module=module.__name__), mock.patch.object(
                module,
                "reproduce_historical",
                side_effect=AssertionError("reproduction ran"),
            ), mock.patch.object(sys, "argv", [module.__file__, "--check"]), redirect_stdout(
                io.StringIO()
            ):
                self.assertEqual(0, module.main())
        with mock.patch.object(
            run_task029_fresh_process,
            "reproduce",
            side_effect=AssertionError("reproduction ran"),
        ), mock.patch.object(
            sys,
            "argv",
            [run_task029_fresh_process.__file__, "--check"],
        ), redirect_stdout(io.StringIO()):
            self.assertEqual(0, run_task029_fresh_process.main())

    def test_evidence_runners_require_an_explicit_mode(self) -> None:
        for module in (
            run_task016,
            run_task017,
            run_task018,
            run_task021,
            run_task022,
            run_task027_fresh_root,
            run_task028_fresh_root,
            run_task029_fresh_process,
            run_task030_fresh_root,
            run_task032_fresh_root,
            run_task033_phase2_reproduction,
        ):
            with self.subTest(module=module.__name__), mock.patch.object(
                sys, "argv", [module.__file__]
            ), redirect_stdout(
                io.StringIO()
            ), mock.patch("sys.stderr", io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    module.main()
                self.assertEqual(2, raised.exception.code)

    def test_fresh_root_runners_copy_only_repository_source_members(self) -> None:
        for module in (
            run_task030_fresh_root,
            run_task032_fresh_root,
            run_task033_phase2_reproduction,
        ):
            source = Path(module.__file__).read_text(encoding="utf-8")
            with self.subTest(module=module.__name__):
                self.assertIn("copy_current_tree(", source)
                self.assertNotIn("shutil.copytree(ROOT", source)

    def test_source_copy_fails_closed_without_git_membership(self) -> None:
        failed = mock.Mock(returncode=1, stdout=b"", stderr=b"unavailable")
        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(
            compiler_determinism_matrix.subprocess,
            "run",
            return_value=failed,
        ), self.assertRaisesRegex(
            compiler_determinism_matrix.MatrixFailure,
            "Git source membership is unavailable",
        ):
            compiler_determinism_matrix.copy_current_tree(
                ROOT,
                Path(temporary) / "copy",
                include_task009_capsule=False,
            )

    def test_retained_evidence_closure_rejects_mutation_extra_and_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            payload = b"retained\n"
            retained = root / "retained.json"
            retained.write_bytes(payload)
            expected = {
                "retained.json": retained_evidence._git_blob_id(payload, "sha1")
            }
            retained_evidence._check_exact_closure(root, expected, "sha1")
            retained.write_bytes(b"changed\n")
            with self.assertRaisesRegex(ValueError, "differs from its anchored commit"):
                retained_evidence._check_exact_closure(root, expected, "sha1")
            retained.write_bytes(payload)
            (root / "extra.json").write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "closure differs"):
                retained_evidence._check_exact_closure(root, expected, "sha1")
            (root / "extra.json").unlink()
            (root / "alias.json").symlink_to(retained.name)
            with self.assertRaisesRegex(ValueError, "contains a symlink"):
                retained_evidence._check_exact_closure(root, expected, "sha1")

    def test_retained_evidence_rejects_another_git_root_and_ancestor_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            expected_repository = base / "expected-repository"
            external_repository = base / "external-repository"
            expected_repository.mkdir()
            (external_repository / "evidence").mkdir(parents=True)
            evidence_link = expected_repository / "evidence"
            evidence_link.symlink_to(external_repository / "evidence")

            with mock.patch.object(
                retained_evidence,
                "_git",
                return_value=(str(external_repository) + "\n").encode("utf-8"),
            ), self.assertRaisesRegex(ValueError, "not the expected root"):
                retained_evidence._git_tracked_closure(
                    evidence_link, expected_repository, "completion-commit"
                )

            def expected_root_only(_repository, *arguments):
                if arguments == ("rev-parse", "--show-toplevel"):
                    return (str(expected_repository) + "\n").encode("utf-8")
                raise AssertionError("Git closure was queried before path rejection")

            with mock.patch.object(
                retained_evidence, "_git", side_effect=expected_root_only
            ), self.assertRaisesRegex(ValueError, "path contains a symlink"):
                retained_evidence._git_tracked_closure(
                    evidence_link, expected_repository, "completion-commit"
                )


if __name__ == "__main__":
    unittest.main()
