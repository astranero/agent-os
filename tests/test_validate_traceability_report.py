"""Tests for JUnit-backed card traceability verification."""

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

import validate_traceability_report as validator  # noqa: E402


CARD = """\
## Traceability

| Acceptance criterion | Test | Result |
|---|---|---|
| First behavior works | `Example.test_first` | Passed |
| Second behavior works | `test_second` | Passed |
"""

VALID_REPORT = """\
<testsuite>
  <testcase classname="Example" name="test_first" />
  <testcase name="test_second" />
</testsuite>
"""


class TraceabilityReportTests(unittest.TestCase):
    def test_valid_report_verifies_rows(self):
        self.assertEqual(validator.verify_traceability(CARD, VALID_REPORT), [])

    def test_missing_failed_and_errored_cases_fail(self):
        report = """\
<testsuite>
  <testcase classname="Example" name="test_first"><failure /></testcase>
</testsuite>
"""
        errors = validator.verify_traceability(CARD, report)
        self.assertIn("is failed", errors[0])
        self.assertIn("no test case 'test_second'", errors[1])

    def test_malformed_and_unknown_reports_fail(self):
        with self.assertRaisesRegex(validator.ReportError, "malformed"):
            validator.verify_traceability(CARD, "<testsuite>")
        report = "<testsuite><testcase name='test_first'><flaky /></testcase></testsuite>"
        with self.assertRaisesRegex(validator.ReportError, "unknown result state"):
            validator.verify_traceability(CARD, report)

    def test_ambiguous_test_names_fail(self):
        report = """\
<testsuite>
  <testcase classname="First" name="same" />
  <testcase classname="Second" name="same" />
</testsuite>
"""
        card = CARD.replace("Example.test_first", "same")
        with self.assertRaisesRegex(validator.ReportError, "ambiguous"):
            validator.verified_traceability_rows(card, report)


if __name__ == "__main__":
    unittest.main()
