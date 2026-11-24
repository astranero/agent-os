import json
import tempfile
import unittest
from pathlib import Path

from tools.validate_preview import validate_preview


class PreviewContractTests(unittest.TestCase):
    def test_ui_preview_requires_review_states_and_accessibility_notes(self):
        errors = validate_preview({
            "kind": "ui",
            "preview_url": "http://localhost:6006",
            "states": ["default", "loading", "error"],
            "accessibility_notes": "Keyboard and screen-reader behavior reviewed.",
        })
        self.assertEqual(errors, [])

    def test_non_ui_work_can_explicitly_skip_preview(self):
        self.assertEqual(
            validate_preview({"kind": "non-ui", "preview_not_applicable": True}),
            [],
        )

    def test_missing_ui_preview_fails_closed(self):
        errors = validate_preview({"kind": "ui", "states": ["default"]})
        self.assertIn("preview_url is required for UI work", errors)
        self.assertIn("accessibility_notes is required for UI work", errors)


if __name__ == "__main__":
    unittest.main()
