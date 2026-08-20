from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from tools.source_packages.validate_task036_handoff import validate_handoff


ROOT = Path(__file__).resolve().parents[3]
HANDOFF = ROOT / "docs/tasks/036-INSTRUMENT-LAB-HANDOFF.json"


def _canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


class Task036HandoffValidatorTest(unittest.TestCase):
    def _document(self) -> dict[str, object]:
        return json.loads(HANDOFF.read_text("utf-8"))

    def _errors(self, document: dict[str, object]) -> list[str]:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "handoff.json"
            path.write_bytes(_canonical_bytes(document))
            return validate_handoff(path)

    def test_live_handoff_is_complete(self) -> None:
        self.assertEqual(validate_handoff(HANDOFF), [])

    def test_status_and_promoted_claim_fail_closed(self) -> None:
        document = self._document()
        document["status"] = "pending"
        document["negative_claims"]["provider_promoted"] = True
        errors = self._errors(document)
        self.assertTrue(any(error.startswith("INCOMPLETE:") for error in errors))
        self.assertTrue(any(error.startswith("PROMOTED_CLAIM:") for error in errors))

    def test_bound_hash_and_authority_fail_closed(self) -> None:
        document = self._document()
        document["task"]["contract"]["sha256"] = "0" * 64
        document["source_package"]["authority_source_release"]["content_hash"] = (
            "sha256:" + "0" * 64
        )
        errors = self._errors(document)
        self.assertTrue(any(error.startswith("FILE_HASH_DRIFT:") for error in errors))
        self.assertTrue(any(error.startswith("TASK_HASH_DRIFT:") for error in errors))
        self.assertTrue(any(error.startswith("AUTHORITY_DRIFT:") for error in errors))

    def test_absolute_and_mutable_latest_fail_closed(self) -> None:
        document = self._document()
        document["source_package"]["package_path"] = "/tmp/mutable_latest"
        errors = self._errors(document)
        self.assertTrue(any(error.startswith("ABSOLUTE_VALUE:") for error in errors))
        self.assertTrue(any(error.startswith("MUTABLE_LATEST:") for error in errors))

    def test_unknown_field_and_duplicate_key_fail_closed(self) -> None:
        document = self._document()
        document["unknown"] = copy.deepcopy(document["task"])
        errors = self._errors(document)
        self.assertTrue(any(error.startswith("INVALID_FIELDS:") for error in errors))
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "handoff.json"
            path.write_text('{"status":"complete","status":"pending"}\n', "utf-8")
            duplicate_errors = validate_handoff(path)
        self.assertTrue(
            any(error.startswith("MALFORMED_HANDOFF:") for error in duplicate_errors)
        )


if __name__ == "__main__":
    unittest.main()
