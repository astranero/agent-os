import json
import tempfile
import unittest
from pathlib import Path

from tools.coordinator import claim_card


CARD = """# Small card

## User story

As a developer, I want a bounded claim, so that I can work safely.

## Scope

Change one owned file.

## Non-goals

- Merging or changing policy.

## Acceptance criteria

```gherkin
Feature: Claim work

  Scenario: A valid card is claimed
    Given a Ready card
    When the coordinator claims it
    Then it writes a deterministic handoff

  @failure
  Scenario: A forbidden action is rejected
    Given a Ready card
    When the role requests merge access
    Then the claim fails closed
```

## Contract

The claim owns only the named file.

## Test plan

Run coordinator tests.

## Security impact

No credentials or merge access.

## Dependencies

None.

## Reuse and cost

Decision: existing
Alternatives checked: manual claims are not deterministic.
Reason: Reuse the card validator and role manifest.

## Verification commands

```text
python3 -m unittest discover -s tests -v
```

## Traceability

| Acceptance criterion | Test | Result |
|---|---|---|
| A valid card is claimed | `test_claim_writes_stable_record` | Passed |
| A forbidden action is rejected | `test_forbidden_role_fails` | Passed |
"""


class CoordinatorTests(unittest.TestCase):
    def test_claim_writes_stable_record(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            card = root / "card.md"
            output = root / "claim.json"
            card.write_text(CARD, encoding="utf-8")
            claim_card(
                card_path=card,
                role="backend-developer",
                claim_id="claim-001",
                owned_paths=["tools/example.py"],
                dependencies=[],
                claims_path=root / "claims.json",
                output_path=output,
            )
            record = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(record["claim_id"], "claim-001")
            self.assertEqual(record["owned_paths"], ["tools/example.py"])
            self.assertEqual(record["status"], "claimed")

    def test_forbidden_role_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            card = root / "card.md"
            card.write_text(CARD, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "cannot claim"):
                claim_card(
                    card_path=card,
                    role="reviewer",
                    claim_id="claim-002",
                    owned_paths=["tools/example.py"],
                    dependencies=[],
                    claims_path=root / "claims.json",
                    output_path=root / "claim.json",
                )


if __name__ == "__main__":
    unittest.main()
