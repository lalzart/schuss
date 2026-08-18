from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
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
        values = (
            envelope(forbidden),
            envelope(relative_workspace, "relative/path"),
            envelope(session_without_workspace),
            envelope(describe),
            envelope(component),
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
        self.assertEqual(5, len(lines))
        results = [json.loads(line) for line in lines]
        for line, result in zip(lines, results):
            self.assertEqual(core.canonical_json(result).encode("utf-8"), line)

        self.assertEqual("BRIDGE_OPERATION_FORBIDDEN", results[0]["error"]["code"])
        self.assertEqual("BRIDGE_WORKSPACE_INVALID", results[1]["error"]["code"])
        self.assertEqual("BRIDGE_WORKSPACE_REQUIRED", results[2]["error"]["code"])
        self.assertEqual("success", results[3]["status"])
        capabilities = {
            item["operation"]: item for item in results[3]["value"]["operations"]
        }
        self.assertEqual(35, len(capabilities))
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
            results[4]["value"]["component_contract"]["display_name"],
        )


if __name__ == "__main__":
    unittest.main()
