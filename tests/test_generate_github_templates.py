"""Behavior tests for generating GitHub templates from the `.ai/` sources."""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

import generate_github_templates as generator  # noqa: E402
import validate_card  # noqa: E402

GENERATOR_SCRIPT = PROJECT_ROOT / "tools" / "generate_github_templates.py"


def copy_sources_to(directory):
    """Copy only the canonical sources, so tests never touch real files."""
    target_root = Path(directory)
    shutil.copytree(PROJECT_ROOT / ".ai" / "templates", target_root / ".ai" / "templates")
    return target_root


class GeneratedContentTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = copy_sources_to(self.temporary_directory.name)
        generator.write_all(self.root)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def read(self, relative_path):
        return (self.root / relative_path).read_text(encoding="utf-8")

    def test_issue_template_body_is_the_canonical_card_template(self):
        canonical = self.read(".ai/templates/implementation-card.md")
        issue_template = self.read(".github/ISSUE_TEMPLATE/implementation-card.md")
        self.assertEqual(generator.strip_generated_header(issue_template), canonical)

    def test_issue_template_has_github_front_matter(self):
        issue_template = self.read(".github/ISSUE_TEMPLATE/implementation-card.md")
        self.assertTrue(issue_template.startswith("---\nname: "))
        for key in ("about:", "title:", "labels:"):
            with self.subTest(key=key):
                self.assertIn(f"\n{key}", issue_template.split("\n---\n", 1)[0])

    def test_generated_files_say_they_must_not_be_edited(self):
        for relative_path in (
            ".github/ISSUE_TEMPLATE/implementation-card.md",
            ".github/ISSUE_TEMPLATE/user-story.md",
            ".github/pull_request_template.md",
        ):
            with self.subTest(path=relative_path):
                self.assertIn("Do not edit", self.read(relative_path))

    def test_unfilled_issue_from_the_template_is_not_ready(self):
        issue_body = generator.strip_front_matter(
            self.read(".github/ISSUE_TEMPLATE/implementation-card.md")
        )
        errors = validate_card.validate_card(issue_body, stage="ready")
        self.assertTrue(any("placeholder" in error for error in errors), errors)
        self.assertFalse(any("missing section" in error for error in errors), errors)

    def test_blank_issues_are_disabled(self):
        self.assertIn(
            "blank_issues_enabled: false", self.read(".github/ISSUE_TEMPLATE/config.yml")
        )

    def test_user_story_template_has_the_inbox_sections(self):
        user_story = self.read(".github/ISSUE_TEMPLATE/user-story.md")
        for section in ("User story", "User outcome", "Non-goals"):
            with self.subTest(section=section):
                self.assertIn(f"\n## {section}\n", user_story)

    def test_pull_request_template_has_every_required_section(self):
        pull_request = self.read(".github/pull_request_template.md")
        for section in generator.REQUIRED_PULL_REQUEST_SECTIONS:
            with self.subTest(section=section):
                self.assertIn(f"\n## {section}\n", pull_request)


class SourceRuleTests(unittest.TestCase):
    def test_generation_fails_when_pull_request_source_lacks_a_section(self):
        with tempfile.TemporaryDirectory() as directory:
            root = copy_sources_to(directory)
            source = root / ".ai" / "templates" / "pull-request.md"
            source.write_text(
                source.read_text(encoding="utf-8").replace("## Reuse and cost\n", ""),
                encoding="utf-8",
            )
            with self.assertRaises(generator.TemplateSourceError) as raised:
                generator.write_all(root)
            self.assertIn("Reuse and cost", str(raised.exception))

    def test_required_pull_request_sections_cover_the_review_evidence(self):
        self.assertEqual(
            generator.REQUIRED_PULL_REQUEST_SECTIONS,
            (
                "Card",
                "Summary",
                "Scope check",
                "Reuse and cost",
                "Traceability",
                "Test evidence",
                "Security",
                "Preview",
                "Residual risks",
            ),
        )


class DriftCheckTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = copy_sources_to(self.temporary_directory.name)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_missing_generated_files_are_reported(self):
        stale = generator.find_stale_files(self.root)
        self.assertIn(".github/pull_request_template.md", stale)

    def test_current_files_are_not_reported(self):
        generator.write_all(self.root)
        self.assertEqual(generator.find_stale_files(self.root), [])

    def test_hand_edited_generated_file_is_reported(self):
        generator.write_all(self.root)
        edited = self.root / ".github" / "pull_request_template.md"
        edited.write_text(edited.read_text(encoding="utf-8") + "extra\n", encoding="utf-8")
        self.assertEqual(
            generator.find_stale_files(self.root), [".github/pull_request_template.md"]
        )

    def test_check_command_exit_codes(self):
        missing = subprocess.run(
            [sys.executable, str(GENERATOR_SCRIPT), "--check", "--root", str(self.root)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(missing.returncode, 1)
        self.assertIn("pull_request_template.md", missing.stdout)

        generator.write_all(self.root)
        current = subprocess.run(
            [sys.executable, str(GENERATOR_SCRIPT), "--check", "--root", str(self.root)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(current.returncode, 0, current.stdout + current.stderr)


class RealProjectTests(unittest.TestCase):
    def test_committed_github_templates_are_current(self):
        self.assertEqual(generator.find_stale_files(PROJECT_ROOT), [])


if __name__ == "__main__":
    unittest.main()
