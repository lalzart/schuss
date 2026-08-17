from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.schuss_core.product_cli import (  # noqa: E402
    application_describe_request,
    catalog_inspect_request,
    catalog_search_request,
)
from tools.contracts import validator_core as core  # noqa: E402


BRIDGE = ROOT / "apps/schuss_desktop/bridge/read_only_catalog_bridge.py"
RECORD_SET = ROOT / "contracts/record-sets/task028-direct-palette-v1.json"


class DesktopReadOnlyBridgeTest(unittest.TestCase):
    def test_live_bridge_is_canonical_allowlisted_current_and_read_only(self):
        before = (
            RECORD_SET.stat().st_mtime_ns,
            RECORD_SET.stat().st_size,
            hashlib.sha256(RECORD_SET.read_bytes()).hexdigest(),
        )
        forbidden = {
            "schema_version": "schuss-operation-request-v1",
            "canonical_profile": "schuss-canonical-json-v1",
            "operation": "graph.inspect",
            "payload": {},
        }
        mutable_search = catalog_search_request(
            "", {"provenance": ["mutable-instruments-derived"]}
        )
        bell_reference = {
            "family_id": "schuss-family-000038",
            "revision": 1,
            "content_hash": "sha256:af55d92c4b87e0fbd6387283d4a3b8235631e5bc1d0c0e850a92403e085677f0",
        }
        requests = (
            forbidden,
            application_describe_request(),
            mutable_search,
            catalog_inspect_request(bell_reference),
        )
        input_bytes = b"".join(
            core.canonical_json(request).encode("utf-8") + b"\n"
            for request in requests
        )
        completed = subprocess.run(
            [sys.executable, str(BRIDGE)],
            cwd=ROOT,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            input=input_bytes,
            capture_output=True,
            check=False,
            timeout=30,
        )
        self.assertEqual(0, completed.returncode, completed.stderr.decode("utf-8"))
        self.assertEqual(b"", completed.stderr)
        lines = completed.stdout.splitlines()
        self.assertEqual(4, len(lines))
        values = [json.loads(line) for line in lines]
        for line, value in zip(lines, values):
            self.assertEqual(core.canonical_json(value).encode("utf-8"), line)

        rejected, description, search, inspection = values
        self.assertEqual("schuss-desktop-bridge-error-v1", rejected["schema_version"])
        self.assertEqual("BRIDGE_OPERATION_FORBIDDEN", rejected["error"]["code"])

        self.assertEqual("application.describe", description["operation"])
        self.assertEqual("success", description["status"])
        capabilities = {
            item["operation"]: item for item in description["value"]["operations"]
        }
        for operation in (
            "application.describe",
            "catalog.search",
            "catalog.inspect",
        ):
            self.assertEqual("read-only", capabilities[operation]["effect_class"])
            self.assertEqual("available", capabilities[operation]["availability"])

        self.assertEqual("catalog.search", search["operation"])
        self.assertEqual("schuss-record-set-000021", search["value"]["record_set_reference"]["record_set_id"])
        self.assertEqual(5, search["value"]["total_matches"])
        self.assertEqual(
            ["mutable-instruments-derived"], search["value"]["filters"]["provenance"]
        )

        self.assertEqual("catalog.inspect", inspection["operation"])
        self.assertEqual(bell_reference, inspection["value"]["family"]["family_reference"])
        self.assertIn(
            "mutable-instruments-derived",
            inspection["value"]["family"]["provenance_facets"],
        )
        self.assertEqual(
            before,
            (
                RECORD_SET.stat().st_mtime_ns,
                RECORD_SET.stat().st_size,
                hashlib.sha256(RECORD_SET.read_bytes()).hexdigest(),
            ),
        )


if __name__ == "__main__":
    unittest.main()
