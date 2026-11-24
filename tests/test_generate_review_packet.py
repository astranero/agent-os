"""Tests for deterministic review-packet generation."""

import unittest
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

import generate_review_packet as packet  # noqa: E402


CARD = """\
# CARD-01 — Example change

## User story

As a maintainer, I want a packet, so that I can review evidence.

## Scope

- Generate one local packet.

## Non-goals

- Calling GitHub.

## Acceptance criteria

```gherkin
Feature: Review packet

  Scenario: Packet is generated
    Given a complete review
    When the generator runs
    Then a packet is written

  @failure
  Scenario: Pending evidence is rejected
    Given pending evidence
    When the generator runs
    Then generation fails
```

## Contract

- Output is deterministic.

## Test plan

- Run unit tests.

## Security impact

- No network access.

## Dependencies

- Python standard library.

## Reuse and cost

Decision: existing
Alternatives checked: building a hosted dashboard is unnecessary; manual copying is error-prone.
Reason: Reuse the current parser and standard library.

## Verification commands

```text
python3 -m unittest
```

## Traceability

| Acceptance criterion | Test | Result |
| --- | --- | --- |
| Packet is generated | test | Passed |
| Pending evidence is rejected | test | Passed |
"""


PR_BODY = """\
## Card

Closes #1 — CARD-01 — Example change

## Summary

Generated a deterministic review packet from the card and review evidence.

## Scope check

- [x] The diff only contains what the card's Scope names.
- [x] Nothing from the card's Non-goals was implemented.
- [x] No acceptance criteria, contracts, or architecture were changed without approval.

## Reuse and cost

Decision: existing
New dependencies: None

## Traceability

| Acceptance criterion | Test | Result |
|---|---|---|
| Packet is generated | test | Passed |
| Pending evidence is rejected | test | Passed |

## Test evidence

- Failing run before implementation: The pending-input test failed before implementation.
- Passing run after implementation: 120 tests passed.

## Security

- Scanners run: None required for this local formatter.
- Findings and their severity: None.
- Waivers: None.

## Preview

Not applicable: no UI change.

## Residual risks

The packet is local and does not collect live GitHub evidence.
"""


class ReviewPacketTests(unittest.TestCase):
    def test_generates_stable_packet(self):
        first = packet.build_packet(PR_BODY, CARD)
        second = packet.build_packet(PR_BODY, CARD)
        self.assertEqual(first, second)
        self.assertIn("# Review packet — CARD-01 — Example change", first)
        self.assertIn("| Packet is generated | test | Passed |", first)

    def test_missing_evidence_fails(self):
        incomplete = PR_BODY.replace("## Security", "## Security removed")
        with self.assertRaisesRegex(ValueError, "missing section 'Security'"):
            packet.build_packet(incomplete, CARD)

    def test_pending_traceability_fails(self):
        pending_card = CARD.replace("| Packet is generated | test | Passed |", "| Packet is generated | test | Pending |")
        with self.assertRaisesRegex(ValueError, "traceability row 'Packet is generated': result is Pending"):
            packet.build_packet(PR_BODY, pending_card)

    def test_packet_includes_verified_report(self):
        verified_card = CARD.replace("| Packet is generated | test | Passed |", "| Packet is generated | Example.test_packet | Passed |")
        verified_card = verified_card.replace("| Pending evidence is rejected | test | Passed |", "| Pending evidence is rejected | Example.test_pending | Passed |")
        report = """\
<testsuite>
  <testcase classname="Example" name="test_packet" />
  <testcase classname="Example" name="test_pending" />
</testsuite>
"""
        result = packet.build_packet(PR_BODY, verified_card, report)
        self.assertIn("## Verified test report", result)
        self.assertIn("| Packet is generated | Example.test_packet | Example.test_packet | passed |", result)

    def test_unverified_report_blocks_packet(self):
        with self.assertRaisesRegex(ValueError, "no test case"):
            packet.build_packet(PR_BODY, CARD, "<testsuite />")


if __name__ == "__main__":
    unittest.main()
