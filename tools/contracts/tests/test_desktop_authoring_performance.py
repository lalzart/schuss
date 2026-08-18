from __future__ import annotations

import copy
import hashlib
import shutil
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.schuss_core.control_plane import load_repository_context  # noqa: E402
from packages.schuss_core.project_service import (  # noqa: E402
    ProjectError,
    ProjectService,
    _record_value_bytes,
)
from tools.contracts import validator_core as core  # noqa: E402


RECORD_SET = ROOT / "contracts/record-sets/ui-desktop-patcher-authoring-v1.json"
RECORD_SET_LOCATOR = "contracts/record-sets/ui-desktop-patcher-authoring-v1.json"


def _reference(record: dict, id_field: str) -> dict:
    return {
        id_field: record[id_field],
        "revision": record["revision"],
        "content_hash": record["content_hash"],
    }


def _governed_hashes(workspace: Path) -> dict[str, str]:
    return {
        path.relative_to(workspace).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in sorted(workspace.rglob("*"))
        if path.is_file() and ".schuss" not in path.parts
    }


class DesktopAuthoringPerformanceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = load_repository_context(ROOT, record_set_path=RECORD_SET)
        cls.graph = next(
            item
            for item in cls.context.records["graphs"]
            if item["graph_id"] == "schuss-graph-000006"
            and item["revision"] == 1
        )
        cls.instrument = next(
            item
            for item in cls.context.records["instruments"]
            if item["instrument_id"] == "schuss-instrument-000005"
            and item["revision"] == 1
        )
        cls.build_request = next(
            item
            for item in cls.context.records["request"]
            if item["build_request_id"] == "schuss-build-request-000005"
            and item["revision"] == 1
        )
        cls.temporary = tempfile.TemporaryDirectory(
            prefix="schuss-desktop-cache-fixture-"
        )
        cls.template = Path(cls.temporary.name) / "template"
        service = ProjectService(cls.template, initial_context=cls.context)
        initialized = service.init(
            {
                "project_id": "schuss-project-900008",
                "base_record_set": {
                    "reference": copy.deepcopy(cls.context.record_set_reference),
                    "portable_locator": RECORD_SET_LOCATOR,
                },
                "primary_graph_reference": _reference(cls.graph, "graph_id"),
                "instrument_references": [
                    _reference(cls.instrument, "instrument_id")
                ],
                "build_request_references": [
                    _reference(cls.build_request, "build_request_id")
                ],
                "asset_references": [],
            }
        )
        service.fork_profile(
            {
                "expected_project_reference": _reference(
                    initialized["project"], "project_id"
                ),
                "template_graph_reference": _reference(cls.graph, "graph_id"),
                "template_instrument_reference": _reference(
                    cls.instrument, "instrument_id"
                ),
                "template_build_request_reference": _reference(
                    cls.build_request, "build_request_id"
                ),
                "write_intent": "explicit",
            }
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def copy_workspace(self, name: str) -> Path:
        workspace = Path(self.temporary.name) / name
        shutil.copytree(self.template, workspace)
        return workspace

    def test_exact_initial_context_is_reused_and_warm_load_still_reads_files(self):
        workspace = self.copy_workspace("warm-load")
        service = ProjectService(workspace, initial_context=self.context)

        with mock.patch(
            "packages.schuss_core.project_service.load_repository_context",
            side_effect=AssertionError("exact validated base was loaded again"),
        ), mock.patch.object(
            service,
            "_read_schema_value",
            wraps=service._read_schema_value,
        ) as read_value:
            first = service.load()
            reads_after_first = read_value.call_count
            second = service.load()

        self.assertEqual(first.manifest, second.manifest)
        self.assertGreater(reads_after_first, 0)
        self.assertGreater(read_value.call_count, reads_after_first)
        self.assertEqual(0, service.cache_metrics["base_loads"])
        self.assertEqual(2, service.cache_metrics["base_reuses"])
        self.assertEqual(1, service.cache_metrics["semantic_misses"])
        self.assertEqual(1, service.cache_metrics["semantic_hits"])
        self.assertEqual(1, service.cache_metrics["semantic_entries"])
        self.assertFalse(
            any("cache" in path.name.lower() for path in workspace.rglob("*"))
        )

    def test_owned_byte_tamper_fails_before_cached_semantics_can_be_reused(self):
        workspace = self.copy_workspace("tamper")
        service = ProjectService(workspace, initial_context=self.context)
        loaded = service.load()
        selected = loaded.manifest["primary_graph_reference"]
        member = next(
            item
            for item in loaded.manifest["owned_members"]
            if item["record_kind"] == "dsp-graph"
            and item["stable_id"] == selected["graph_id"]
            and item["revision"] == selected["revision"]
        )
        graph = copy.deepcopy(
            next(
                item
                for item in loaded.project_records["dsp-graph"]
                if item["graph_id"] == selected["graph_id"]
                and item["revision"] == selected["revision"]
            )
        )
        graph["display_name"] = graph["display_name"] + " tampered"
        data = _record_value_bytes(graph, loaded.context.schemas["graph"])
        (workspace / member["portable_locator"]).write_bytes(data)

        with self.assertRaises(ProjectError) as raised:
            service.load()

        self.assertEqual("PROJECT_OWNED_BYTE_HASH_MISMATCH", raised.exception.code)
        self.assertEqual(0, service.cache_metrics["semantic_hits"])

    def test_cache_enabled_and_disabled_transactions_are_byte_identical(self):
        enabled_workspace = self.copy_workspace("enabled")
        disabled_workspace = self.copy_workspace("disabled")
        enabled = ProjectService(
            enabled_workspace,
            initial_context=self.context,
            semantic_cache_size=1,
        )
        disabled = ProjectService(
            disabled_workspace,
            initial_context=self.context,
            semantic_cache_size=0,
        )

        self.assertEqual(enabled.inspect(), disabled.inspect())
        self.assertEqual(enabled.validate(), disabled.validate())
        self.assertEqual(enabled.history(), disabled.history())

        loaded = enabled.load()
        payload = {
            "expected_project_reference": _reference(
                loaded.manifest, "project_id"
            ),
            "graph_reference": copy.deepcopy(
                loaded.manifest["primary_graph_reference"]
            ),
            "base_content_hash": loaded.manifest["primary_graph_reference"][
                "content_hash"
            ],
            "edits": [
                {
                    "edit": "set-graph-display-name",
                    "display_name": "Cache parity patch",
                }
            ],
            "write_intent": "explicit",
        }
        enabled_result = enabled.transact_profile(copy.deepcopy(payload))
        disabled_result = disabled.transact_profile(copy.deepcopy(payload))

        self.assertEqual(
            core.canonical_json(enabled_result),
            core.canonical_json(disabled_result),
        )
        self.assertEqual(
            _governed_hashes(enabled_workspace),
            _governed_hashes(disabled_workspace),
        )

        enabled_history = enabled.history()
        disabled_history = disabled.history()
        self.assertEqual(enabled_history, disabled_history)
        target = enabled_history["ancestry"][-2]["project_reference"]
        enabled_revert = enabled.revert(
            {
                "expected_project_reference": _reference(
                    enabled_result["project"], "project_id"
                ),
                "target_project_reference": copy.deepcopy(target),
                "write_intent": "explicit",
            }
        )
        disabled_revert = disabled.revert(
            {
                "expected_project_reference": _reference(
                    disabled_result["project"], "project_id"
                ),
                "target_project_reference": copy.deepcopy(target),
                "write_intent": "explicit",
            }
        )
        self.assertEqual(
            core.canonical_json(enabled_revert),
            core.canonical_json(disabled_revert),
        )
        self.assertEqual(enabled.validate(), disabled.validate())
        self.assertEqual(
            _governed_hashes(enabled_workspace),
            _governed_hashes(disabled_workspace),
        )
        self.assertEqual(1, enabled.cache_metrics["semantic_capacity"])
        self.assertEqual(2, enabled.cache_metrics["semantic_misses"])
        self.assertGreaterEqual(enabled.cache_metrics["semantic_evictions"], 1)
        self.assertGreaterEqual(enabled.cache_metrics["semantic_hits"], 1)
        self.assertEqual(0, disabled.cache_metrics["semantic_entries"])
        self.assertEqual(0, disabled.cache_metrics["semantic_hits"])

    def test_base_reuse_requires_the_exact_validated_manifest_path_and_reference(self):
        wrong_path_context = replace(
            self.context,
            record_set_path=ROOT / "contracts/record-sets/not-the-selected-set.json",
        )
        service = ProjectService(
            self.copy_workspace("wrong-path"),
            initial_context=wrong_path_context,
        )
        base = {
            "reference": copy.deepcopy(self.context.record_set_reference),
            "portable_locator": RECORD_SET_LOCATOR,
        }
        with mock.patch(
            "packages.schuss_core.project_service.load_repository_context",
            return_value=self.context,
        ) as reload_context:
            loaded_context, loaded_record_set = service._load_base(base)

        reload_context.assert_called_once()
        self.assertEqual(self.context.record_set_reference, loaded_context.record_set_reference)
        self.assertEqual(self.context.loaded_record_set, loaded_record_set)
        self.assertEqual(1, service.cache_metrics["base_loads"])
        self.assertEqual(0, service.cache_metrics["base_reuses"])

    def test_semantic_cache_size_is_bounded_and_type_checked(self):
        with self.assertRaisesRegex(ValueError, "non-negative integer"):
            ProjectService(
                self.copy_workspace("bad-size"),
                initial_context=self.context,
                semantic_cache_size=True,
            )


if __name__ == "__main__":
    unittest.main()
