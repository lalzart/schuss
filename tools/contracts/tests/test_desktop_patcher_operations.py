from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.schuss_core.control_plane import dispatch_operation, load_repository_context  # noqa: E402
from packages.schuss_core.project_service import ProjectService  # noqa: E402


RECORD_SET = ROOT / "contracts/record-sets/ui-desktop-patcher-authoring-v1.json"
GRAPH = {
    "graph_id": "schuss-graph-000006",
    "revision": 1,
    "content_hash": "sha256:1c3e3e66245cf497b507d60d21d3a8ebd8cdc5117f02eab8b793853a4bef5aa2",
}
INSTRUMENT = {
    "instrument_id": "schuss-instrument-000005",
    "revision": 1,
    "content_hash": "sha256:e4d8d801dba7f8c557295444d3de22ad212601b88d3bd4bf7dfa7f4025aa2679",
}
BUILD_REQUEST = {
    "build_request_id": "schuss-build-request-000005",
    "revision": 1,
    "content_hash": "sha256:8f40ac2f996f32f10f59b862da566f1d66f145cdf1780f29d786c9b2f42f03c2",
}


def request(version: int, operation: str, payload: dict) -> dict:
    return {
        "schema_version": f"schuss-operation-request-v{version}",
        "canonical_profile": "schuss-canonical-json-v1",
        "operation": operation,
        "payload": payload,
    }


def project_reference(project: dict) -> dict:
    return {
        "project_id": project["project_id"],
        "revision": project["revision"],
        "content_hash": project["content_hash"],
    }


def graph_reference(graph: dict) -> dict:
    return {
        "graph_id": graph["graph_id"],
        "revision": graph["revision"],
        "content_hash": graph["content_hash"],
    }


class DesktopPatcherOperationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = load_repository_context(
            repository_root=ROOT,
            record_set_path=RECORD_SET,
        )

    def test_generated_contracts_are_fresh_and_graph_rename_is_proposal_only(self):
        completed = subprocess.run(
            [sys.executable, "tools/contracts/generate_desktop_patcher_records.py", "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        result = dispatch_operation(
            request(
                11,
                "graph.transact",
                {
                    "graph_reference": GRAPH,
                    "base_content_hash": GRAPH["content_hash"],
                    "edits": [{"edit": "set-graph-display-name", "display_name": "Desktop proposal"}],
                },
            ),
            self.context,
        )
        self.assertEqual("success", result["status"])
        self.assertEqual(
            "Desktop proposal", result["value"]["proposed_graph"]["display_name"]
        )
        inspected = dispatch_operation(
            request(1, "graph.inspect", {"graph_reference": GRAPH}), self.context
        )
        self.assertNotEqual("Desktop proposal", inspected["value"]["graph"]["display_name"])

    def test_new_patch_fork_and_v11_rename_persist_as_immutable_revisions(self):
        with tempfile.TemporaryDirectory(prefix="schuss-desktop-patcher-") as temporary:
            service = ProjectService(
                Path(temporary) / "project",
                repository_root=ROOT,
                initial_context=self.context,
            )
            initialized = dispatch_operation(
                request(
                    3,
                    "project.init",
                    {
                        "project_id": "schuss-project-900001",
                        "base_record_set": {
                            "reference": self.context.record_set_reference,
                            "portable_locator": "contracts/record-sets/ui-desktop-patcher-authoring-v1.json",
                        },
                        "primary_graph_reference": GRAPH,
                        "instrument_references": [INSTRUMENT],
                        "build_request_references": [BUILD_REQUEST],
                        "asset_references": [],
                    },
                ),
                self.context,
                project_service=service,
            )
            self.assertEqual("success", initialized["status"])
            forked = dispatch_operation(
                request(
                    8,
                    "project.profile.fork",
                    {
                        "expected_project_reference": project_reference(initialized["value"]["project"]),
                        "template_graph_reference": GRAPH,
                        "template_instrument_reference": INSTRUMENT,
                        "template_build_request_reference": BUILD_REQUEST,
                        "write_intent": "explicit",
                    },
                ),
                self.context,
                project_service=service,
            )
            self.assertEqual("success", forked["status"])
            renamed = dispatch_operation(
                request(
                    11,
                    "project.profile.transact",
                    {
                        "expected_project_reference": project_reference(forked["value"]["project"]),
                        "graph_reference": graph_reference(forked["value"]["graph"]),
                        "base_content_hash": forked["value"]["graph"]["content_hash"],
                        "edits": [{"edit": "set-graph-display-name", "display_name": "Desktop patch"}],
                        "write_intent": "explicit",
                    },
                ),
                self.context,
                project_service=service,
            )
            self.assertEqual("success", renamed["status"])
            self.assertEqual("Desktop patch", renamed["value"]["graph"]["display_name"])
            self.assertEqual(3, renamed["value"]["project"]["revision"])
            inspected = dispatch_operation(
                request(3, "project.inspect", {"scope": "accepted-project"}),
                self.context,
                project_service=service,
            )
            self.assertEqual(renamed["value"]["project"]["content_hash"], inspected["value"]["project"]["content_hash"])
            graph_inspection = dispatch_operation(
                request(
                    1,
                    "graph.inspect",
                    {
                        "graph_reference": inspected["value"]["project"][
                            "primary_graph_reference"
                        ]
                    },
                ),
                self.context,
                project_service=service,
            )
            self.assertEqual("success", graph_inspection["status"])
            self.assertEqual(
                "Desktop patch",
                graph_inspection["value"]["graph"]["display_name"],
            )


if __name__ == "__main__":
    unittest.main()
