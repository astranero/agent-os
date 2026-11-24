"""Tests for creating a clean product-project foundation."""

import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

import bootstrap_project  # noqa: E402


class BootstrapProjectTests(unittest.TestCase):
    def test_bootstraps_project(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "product"
            bootstrap_project.bootstrap_project(
                PROJECT_ROOT, target, "Example Product", "astranero/example-product"
            )
            self.assertTrue((target / ".ai").is_dir())
            self.assertTrue((target / ".github").is_dir())
            self.assertTrue((target / "tools" / "validate_card.py").is_file())
            self.assertIn("# Example Product", (target / "README.md").read_text())
            self.assertIn(
                "astranero/example-product", (target / "README.md").read_text()
            )

    def test_non_empty_target_fails_without_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "product"
            target.mkdir()
            sentinel = target / "keep.txt"
            sentinel.write_text("keep")
            with self.assertRaisesRegex(bootstrap_project.BootstrapError, "must be empty"):
                bootstrap_project.bootstrap_project(
                    PROJECT_ROOT, target, "Example", "astranero/example"
                )
            self.assertEqual(sentinel.read_text(), "keep")

    def test_excludes_vault_only_files(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "product"
            bootstrap_project.bootstrap_project(
                PROJECT_ROOT, target, "Example", "astranero/example"
            )
            self.assertFalse((target / "HANDOFF.md").exists())
            self.assertFalse((target / ".ai" / "KANBAN.md").exists())
            self.assertFalse(any(target.rglob("__pycache__")))


if __name__ == "__main__":
    unittest.main()
