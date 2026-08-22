from __future__ import annotations

import unittest

from tools.contracts.validate_task038_source_records import validate


class Task038SourceRecordTest(unittest.TestCase):
    def test_exact_source_only_successor_is_current(self) -> None:
        result = validate()
        self.assertEqual(result["status"], "valid")
        self.assertEqual(
            result["added_source_release_ids"],
            ["schuss-source-release-000008", "schuss-source-release-000009"],
        )
        self.assertFalse(result["catalog_collection_provider_mutation"])


if __name__ == "__main__":
    unittest.main()
