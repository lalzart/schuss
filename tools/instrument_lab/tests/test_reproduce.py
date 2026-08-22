from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from common import ContractError  # noqa: E402
from reproduce import copy_relocated_repository, reproduce_consumer  # noqa: E402


class RelocatedConsumerReproductionTests(unittest.TestCase):
    def test_copy_is_an_explicit_repository_closure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "source"
            destination = Path(temporary) / "relocated"
            (root / "research/prototypes/example").mkdir(parents=True)
            (root / "research/prototypes/example/prototype-index.json").write_text("{}\n")
            (root / "tools").mkdir()
            (root / "tools/kept.py").write_text("pass\n")
            (root / "build").mkdir()
            (root / "build/not-copied").write_text("artifact\n")
            copy_relocated_repository(root, destination)
            self.assertTrue((destination / "research/prototypes/example/prototype-index.json").is_file())
            self.assertTrue((destination / "tools/kept.py").is_file())
            self.assertFalse((destination / "build").exists())

    def test_consumer_path_cannot_escape(self) -> None:
        with self.assertRaisesRegex(ContractError, "INVALID_CONSUMER_PATH"):
            reproduce_consumer(
                Path("/tmp"), Path("../outside"), cmake_args=[], ctest_regex=None
            )


if __name__ == "__main__":
    unittest.main()
