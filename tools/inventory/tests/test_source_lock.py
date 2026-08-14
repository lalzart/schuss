import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
VALIDATOR_SCRIPT = ROOT / "tools/inventory/validate_raw_inventory.py"
SPEC = importlib.util.spec_from_file_location("raw_inventory_validator", VALIDATOR_SCRIPT)
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class SourceLockTest(unittest.TestCase):
    def test_lock_matches_schema_and_retained_snapshot(self):
        lock = json.loads((ROOT / "catalog/sources.lock.json").read_text())
        schema = json.loads((ROOT / "schemas/source-lock-v1.schema.json").read_text())
        manifest = json.loads(
            (ROOT / "catalog/snapshots/legacy-catalog-v0/manifest.json").read_text()
        )

        VALIDATOR.validate_schema(lock, schema)
        locked = {
            source["id"]: (source["url"], source["commit"])
            for source in lock["sources"]
        }
        observed = {
            source["name"]: (source["remote_url"], source["commit"])
            for source in manifest["sources"]
        }
        self.assertEqual(len(locked), len(lock["sources"]))
        self.assertEqual(locked, observed)


if __name__ == "__main__":
    unittest.main()
