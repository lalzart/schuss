from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.contracts import validator_core as core  # noqa: E402


BRIDGE = ROOT / "apps/schuss_desktop/bridge/desktop_core_bridge.py"


def envelope(request: dict, workspace: str | None = None) -> dict:
    return {"request": request, "workspace": workspace}


class DesktopPatcherBridgeTest(unittest.TestCase):
    def test_bridge_is_canonical_closed_versioned_and_workspace_scoped(self):
        forbidden = {
            "schema_version": "schuss-operation-request-v5",
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": "build.execute",
            "payload": {},
        }
        forbidden_authoring = {
            "schema_version": "schuss-operation-request-v13",
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": "authoring.draft.create",
            "payload": {},
        }
        relative_workspace = {
            "schema_version": "schuss-operation-request-v3",
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": "project.inspect",
            "payload": {"scope": "accepted-project"},
        }
        describe = {
            "schema_version": "schuss-operation-request-v7",
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": "application.describe",
            "payload": {"scope": "selected-context"},
        }
        component = {
            "schema_version": "schuss-operation-request-v11",
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": "component.inspect",
            "payload": {
                "component_contract_reference": {
                    "component_contract_id": "schuss-component-contract-000012",
                    "revision": 1,
                    "content_hash": "sha256:3f399547dbe7a1a76bdcedc1d1d886ccd49d0620fdbca3fbace6aac0a9d2292c",
                }
            },
        }
        session_without_workspace = {
            "schema_version": "schuss-operation-request-v12",
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": "build.session.inspect",
            "payload": {"build_session_id": "build-session-000001"},
        }
        objects_without_workspace = {
            "schema_version": "schuss-operation-request-v13",
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": "project.objects.list",
            "payload": {},
        }
        projects_without_root = {
            "schema_version": "schuss-operation-request-v14",
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": "workspace.projects.list",
            "payload": {},
        }
        with tempfile.TemporaryDirectory() as temporary:
            workspace = str(Path(temporary) / "project")
            historical_workspace = str(Path(temporary) / "historical-project")
            projects_root = str(Path(temporary) / "projects")
            project_init = {
                "schema_version": "schuss-operation-request-v3",
                "canonical_profile": "schuss-canonical-json-v1",
                "operation": "project.init",
                "payload": {
                    "project_id": "schuss-project-990123",
                    "base_record_set": {
                        "reference": {
                            "record_set_id": "schuss-record-set-000026",
                            "revision": 1,
                            "content_hash": "sha256:4ca86d5f870c7c70e39ead9b8793dde68a3f1cec9053f9bd34fb209ed619d67e",
                        },
                        "portable_locator": "contracts/record-sets/ai-sonic-authoring-v1.json",
                    },
                    "primary_graph_reference": {
                        "graph_id": "schuss-graph-000006",
                        "revision": 1,
                        "content_hash": "sha256:1c3e3e66245cf497b507d60d21d3a8ebd8cdc5117f02eab8b793853a4bef5aa2",
                    },
                    "instrument_references": [{
                        "instrument_id": "schuss-instrument-000005",
                        "revision": 1,
                        "content_hash": "sha256:e4d8d801dba7f8c557295444d3de22ad212601b88d3bd4bf7dfa7f4025aa2679",
                    }],
                    "build_request_references": [{
                        "build_request_id": "schuss-build-request-000005",
                        "revision": 1,
                        "content_hash": "sha256:8f40ac2f996f32f10f59b862da566f1d66f145cdf1780f29d786c9b2f42f03c2",
                    }],
                    "asset_references": [],
                },
            }
            historical_project_init = json.loads(json.dumps(project_init))
            historical_project_init["payload"]["project_id"] = "schuss-project-990124"
            historical_project_init["payload"]["base_record_set"] = {
                "reference": {
                    "record_set_id": "schuss-record-set-000025",
                    "revision": 1,
                    "content_hash": "sha256:dc360bb12c5d2272061431ce99f5e6476a41e7a3c92ae27db96c518abe7cfd39",
                },
                "portable_locator": "contracts/record-sets/ui-desktop-build-device-v1.json",
            }
            workspace_create = {
                "schema_version": "schuss-operation-request-v14",
                "canonical_profile": "schuss-canonical-json-v1",
                "operation": "workspace.project.create",
                "payload": {"display_name": "Bridge patch"},
            }
            values = (
                envelope(forbidden),
                envelope(forbidden_authoring, workspace),
                envelope(relative_workspace, "relative/path"),
                envelope(session_without_workspace),
                envelope(objects_without_workspace),
                envelope(projects_without_root),
                envelope(describe),
                envelope(component),
                envelope(project_init, workspace),
                envelope(objects_without_workspace, workspace),
                envelope(workspace_create, projects_root),
                envelope(projects_without_root, projects_root),
                envelope(historical_project_init, historical_workspace),
                envelope(objects_without_workspace, historical_workspace),
            )
            completed = subprocess.run(
                [sys.executable, str(BRIDGE)],
                cwd=ROOT,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                input=b"".join(
                    core.canonical_json(value).encode("utf-8") + b"\n"
                    for value in values
                ),
                capture_output=True,
                check=False,
                timeout=60,
            )
        self.assertEqual(0, completed.returncode, completed.stderr.decode("utf-8"))
        self.assertEqual(b"", completed.stderr)
        lines = completed.stdout.splitlines()
        self.assertEqual(14, len(lines))
        results = [json.loads(line) for line in lines]
        for line, result in zip(lines, results):
            self.assertEqual(core.canonical_json(result).encode("utf-8"), line)

        self.assertEqual("BRIDGE_OPERATION_FORBIDDEN", results[0]["error"]["code"])
        self.assertEqual("BRIDGE_OPERATION_FORBIDDEN", results[1]["error"]["code"])
        self.assertEqual("BRIDGE_WORKSPACE_INVALID", results[2]["error"]["code"])
        self.assertEqual("BRIDGE_WORKSPACE_REQUIRED", results[3]["error"]["code"])
        self.assertEqual("BRIDGE_WORKSPACE_REQUIRED", results[4]["error"]["code"])
        self.assertEqual("BRIDGE_WORKSPACE_REQUIRED", results[5]["error"]["code"])
        self.assertEqual("success", results[6]["status"])
        capabilities = {
            item["operation"]: item for item in results[6]["value"]["operations"]
        }
        self.assertEqual(37, len(capabilities))
        self.assertEqual(
            "requires-project-workspace",
            capabilities["authoring.draft.create"]["availability"],
        )
        self.assertEqual("workspace-write", capabilities["project.profile.transact"]["effect_class"])
        self.assertEqual(
            "requires-execution-service", capabilities["build.execute"]["availability"]
        )
        self.assertEqual("available", capabilities["build.session.start"]["availability"])
        self.assertEqual("device-volatile-write", capabilities["device.upload.start"]["effect_class"])
        self.assertEqual(
            "Band-limited Saw Oscillator",
            results[7]["value"]["component_contract"]["display_name"],
        )
        self.assertEqual("success", results[8]["status"])
        self.assertEqual("success", results[9]["status"])
        self.assertEqual(0, results[9]["value"]["object_count"])
        self.assertEqual([], results[9]["value"]["objects"])
        self.assertEqual("success", results[10]["status"])
        self.assertEqual("Bridge patch", results[10]["value"]["project"]["display_name"])
        self.assertEqual("success", results[11]["status"])
        self.assertEqual(1, results[11]["value"]["project_count"])
        self.assertEqual("success", results[12]["status"])
        self.assertEqual(
            "BRIDGE_PROJECT_OBJECTS_UNAVAILABLE", results[13]["error"]["code"]
        )


if __name__ == "__main__":
    unittest.main()
