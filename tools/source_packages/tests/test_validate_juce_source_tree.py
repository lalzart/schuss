from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from tools.source_packages.validate_juce_source_tree import tree_fingerprint


class JuceSourceTreeFingerprintTests(unittest.TestCase):
    def test_fingerprint_is_path_and_byte_sensitive(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "modules").mkdir()
            target = root / "modules" / "example.h"
            target.write_text("#define JUCE_MAJOR_VERSION 8\n", encoding="utf-8")
            original = tree_fingerprint(root)
            target.write_text("#define JUCE_MAJOR_VERSION 8\n// drift\n", encoding="utf-8")
            self.assertNotEqual(original, tree_fingerprint(root))

    def test_symlink_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "target"
            target.write_text("bytes", encoding="utf-8")
            (root / "link").symlink_to(target)
            with self.assertRaisesRegex(ValueError, "symlink"):
                tree_fingerprint(root)


if __name__ == "__main__":
    unittest.main()
