"""Behavior tests for the Ready-card and acceptance-criteria validator.

Each test starts from one valid card, breaks exactly one rule, and checks that
the validator reports it. The last tests check the published schema, the
template, and the example cards shipped in `.ai/templates/examples/`.
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

import validate_card as validator  # noqa: E402

SCHEMA_PATH = PROJECT_ROOT / ".ai" / "policies" / "card-readiness.schema.json"
TEMPLATE_PATH = PROJECT_ROOT / ".ai" / "templates" / "implementation-card.md"
EXAMPLES_DIRECTORY = PROJECT_ROOT / ".ai" / "templates" / "examples"
VALIDATOR_SCRIPT = PROJECT_ROOT / "tools" / "validate_card.py"

VALID_CARD = """\
# INV-01 — Administrator invites a user

## User story

As an administrator,
I want to invite a colleague by email,
so that they can join the workspace without manual setup.

## Scope

Add the invitation endpoint and the invitation email.

## Non-goals

Bulk invitations and custom expiry per invitation.

## Acceptance criteria

```gherkin
Feature: User invitation

  Background:
    Given I am an authenticated administrator

  Scenario: An administrator invites a valid user
    Given the email address is not already registered
    When I invite the user
    Then the user receives an invitation
    And the invitation expires after the configured period

  @failure
  Scenario: A duplicate email is rejected
    Given the email address is already registered
    When I invite the user
    Then I see the error "already registered"
    But no invitation is sent
```

## Contract

`POST /invitations` as defined in `contracts/openapi/invitations.yaml`.

## Test plan

Acceptance scenarios in Cucumber; unit tests for expiry calculation.

## Security impact

Adds an authenticated endpoint; only administrators may invite.

## Dependencies

None: the email adapter already exists.

## Reuse and cost

Decision: existing
Alternatives checked: the existing email adapter already sends mail, so no
new library or paid service is needed.

## Verification commands

```
npm test -- invitations
```

## Traceability

| Acceptance criterion | Test | Result |
|---|---|---|
| An administrator invites a valid user | invite-user.feature:12 | Pending |
| A duplicate email is rejected | invite-user.feature:24 | Pending |
"""


def all_results_passed(card_text):
    return card_text.replace("| Pending |", "| Passed |")


class CardValidatorTests(unittest.TestCase):
    def assertReports(self, card_text, expected_fragment, stage="ready"):
        errors = validator.validate_card(card_text, stage=stage)
        matching = [error for error in errors if expected_fragment in error]
        self.assertTrue(
            matching,
            f"expected an error containing {expected_fragment!r}, got {errors!r}",
        )

    def test_valid_card_is_ready(self):
        self.assertEqual(validator.validate_card(VALID_CARD, stage="ready"), [])

    def test_each_missing_required_section_is_reported(self):
        for section in validator.REQUIRED_CARD_SECTIONS:
            with self.subTest(section=section):
                broken = VALID_CARD.replace(f"## {section}\n", "## Notes\n", 1)
                self.assertReports(broken, f"missing section '{section}'")

    def test_empty_section_is_rejected(self):
        broken = VALID_CARD.replace(
            "Bulk invitations and custom expiry per invitation.\n", ""
        )
        self.assertReports(broken, "section 'Non-goals' is empty")

    def test_placeholders_are_rejected(self):
        for placeholder in ("TBD", "TODO", "<describe the scope>"):
            with self.subTest(placeholder=placeholder):
                broken = VALID_CARD.replace(
                    "Add the invitation endpoint and the invitation email.",
                    placeholder,
                )
                self.assertReports(broken, "section 'Scope' contains placeholder")

    def test_placeholder_spanning_lines_is_rejected(self):
        broken = VALID_CARD.replace(
            "Add the invitation endpoint and the invitation email.",
            "<What this card changes,\nin one pull request.>",
        )
        self.assertReports(broken, "section 'Scope' contains placeholder")

    def test_title_placeholder_is_rejected(self):
        broken = VALID_CARD.replace(
            "# INV-01 — Administrator invites a user", "# <CARD-ID> — <title>"
        )
        self.assertReports(broken, "title contains placeholder")

    def test_reuse_section_needs_a_decision(self):
        broken = VALID_CARD.replace("Decision: existing\n", "")
        self.assertReports(broken, "Reuse and cost: missing 'Decision:'")

    def test_reuse_decision_must_be_a_known_option(self):
        broken = VALID_CARD.replace("Decision: existing", "Decision: cheap")
        self.assertReports(broken, "Decision 'cheap' is not one of")

    def test_reuse_section_needs_alternatives_checked(self):
        broken = VALID_CARD.replace("Alternatives checked:", "Notes:")
        self.assertReports(broken, "Reuse and cost: missing 'Alternatives checked:'")

    def test_paid_option_needs_a_named_human_approver(self):
        broken = VALID_CARD.replace("Decision: existing", "Decision: paid")
        self.assertReports(broken, "paid option needs 'Approved by:'")

    def test_paid_option_with_approver_is_ready(self):
        card = VALID_CARD.replace(
            "Decision: existing",
            "Decision: paid\nApproved by: Project manager, 2026-11-20",
        )
        self.assertEqual(validator.validate_card(card, stage="ready"), [])

    def test_reuse_decision_options_are_in_preference_order(self):
        self.assertEqual(
            validator.REUSE_DECISIONS, ("existing", "open-source", "build", "paid")
        )

    def test_user_story_must_follow_the_standard_form(self):
        broken = VALID_CARD.replace("so that they can join", "because they can join")
        self.assertReports(broken, "As a ..., I want ..., so that ...")

    def test_acceptance_criteria_need_a_gherkin_block(self):
        start = VALID_CARD.index("```gherkin")
        end = VALID_CARD.index("```\n", start + 3) + 4
        broken = VALID_CARD[:start] + "Users can be invited.\n" + VALID_CARD[end:]
        self.assertReports(broken, "no Gherkin scenarios")

    def test_scenario_without_then_is_rejected(self):
        broken = VALID_CARD.replace(
            "    Then the user receives an invitation\n"
            "    And the invitation expires after the configured period\n",
            "",
        )
        self.assertReports(broken, "'An administrator invites a valid user' has no Then")

    def test_scenario_without_given_is_rejected_when_there_is_no_background(self):
        broken = VALID_CARD.replace(
            "  Background:\n    Given I am an authenticated administrator\n\n", ""
        ).replace("    Given the email address is already registered\n", "")
        self.assertReports(broken, "'A duplicate email is rejected' has no Given")

    def test_background_given_counts_for_every_scenario(self):
        card = VALID_CARD.replace(
            "    Given the email address is already registered\n", ""
        )
        self.assertEqual(validator.validate_card(card, stage="ready"), [])

    def test_scenario_with_two_whens_is_rejected(self):
        broken = VALID_CARD.replace(
            "    When I invite the user\n    Then the user receives",
            "    When I invite the user\n    And I invite the user again\n"
            "    Then the user receives",
            1,
        )
        self.assertReports(broken, "has 2 When steps; expected exactly 1")

    def test_steps_out_of_order_are_rejected(self):
        broken = VALID_CARD.replace(
            "    Then I see the error \"already registered\"\n",
            "    Then I see the error \"already registered\"\n"
            "    Given the moon is full\n",
        )
        self.assertReports(broken, "Given after When or Then")

    def test_then_describing_implementation_detail_is_rejected(self):
        broken = VALID_CARD.replace(
            "Then the user receives an invitation",
            "Then the sendInvite method is called",
        )
        self.assertReports(broken, "describes an implementation detail")

    def test_card_needs_a_failure_scenario(self):
        broken = VALID_CARD.replace("  @failure\n", "")
        self.assertReports(broken, "no scenario tagged @failure")

    def test_duplicate_scenario_names_are_rejected(self):
        broken = VALID_CARD.replace(
            "Scenario: A duplicate email is rejected",
            "Scenario: An administrator invites a valid user",
        )
        self.assertReports(broken, "duplicate scenario name")

    def test_scenario_missing_from_traceability_is_rejected(self):
        broken = VALID_CARD.replace(
            "| A duplicate email is rejected | invite-user.feature:24 | Pending |\n", ""
        )
        self.assertReports(
            broken, "scenario 'A duplicate email is rejected' has no traceability row"
        )

    def test_traceability_row_for_unknown_scenario_is_rejected(self):
        broken = VALID_CARD + "| Nobody can log in | login.feature:3 | Pending |\n"
        self.assertReports(broken, "unknown scenario 'Nobody can log in'")

    def test_traceability_row_needs_a_test_location(self):
        broken = VALID_CARD.replace("| invite-user.feature:24 |", "|  |")
        self.assertReports(broken, "has no test location")

    def test_traceability_result_must_be_a_known_value(self):
        broken = VALID_CARD.replace("| invite-user.feature:24 | Pending |", "| invite-user.feature:24 | Maybe |")
        self.assertReports(broken, "result 'Maybe'")

    def test_traceability_table_needs_the_standard_header(self):
        broken = VALID_CARD.replace(
            "| Acceptance criterion | Test | Result |", "| Criterion | Where |"
        )
        self.assertReports(broken, "Acceptance criterion | Test | Result")

    def test_verification_commands_must_contain_code(self):
        broken = VALID_CARD.replace("```\nnpm test -- invitations\n```", "Run the tests.")
        self.assertReports(broken, "no command in a code span or block")

    def test_review_stage_requires_every_result_passed(self):
        self.assertReports(VALID_CARD, "not Passed", stage="review")

    def test_review_stage_accepts_all_passed_results(self):
        self.assertEqual(
            validator.validate_card(all_results_passed(VALID_CARD), stage="review"), []
        )

    def test_unknown_stage_is_rejected(self):
        with self.assertRaises(ValueError):
            validator.validate_card(VALID_CARD, stage="done")


class CardModelTests(unittest.TestCase):
    def test_parsed_model_contains_story_scenarios_and_traceability(self):
        model = validator.parse_card(VALID_CARD)
        self.assertEqual(model["title"], "INV-01 — Administrator invites a user")
        self.assertEqual(model["user_story"]["role"], "an administrator")
        self.assertEqual(
            [scenario["name"] for scenario in model["scenarios"]],
            ["An administrator invites a valid user", "A duplicate email is rejected"],
        )
        failure_scenario = model["scenarios"][1]
        self.assertEqual(failure_scenario["tags"], ["@failure"])
        self.assertEqual(failure_scenario["when"], ["I invite the user"])
        self.assertEqual(
            failure_scenario["then"],
            ['I see the error "already registered"', "no invitation is sent"],
        )
        self.assertEqual(len(model["traceability"]), 2)
        self.assertEqual(model["reuse"]["decision"], "existing")
        self.assertIsNone(model["reuse"]["approved_by"])

    def test_model_conforms_to_published_schema(self):
        try:
            import jsonschema
        except ImportError:
            self.skipTest("jsonschema is not installed")
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        jsonschema.Draft7Validator.check_schema(schema)
        jsonschema.Draft7Validator(schema).validate(validator.parse_card(VALID_CARD))

    def test_schema_lists_the_same_sections_and_results_as_the_validator(self):
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            sorted(schema["properties"]["sections"]["required"]),
            sorted(validator.REQUIRED_CARD_SECTIONS),
        )
        result_enum = schema["definitions"]["traceabilityRow"]["properties"]["result"]["enum"]
        self.assertEqual(sorted(result_enum), sorted(validator.RESULT_VALUES))


class ShippedFilesTests(unittest.TestCase):
    def test_template_has_every_required_section(self):
        template = TEMPLATE_PATH.read_text(encoding="utf-8")
        for section in validator.REQUIRED_CARD_SECTIONS:
            with self.subTest(section=section):
                self.assertIn(f"\n## {section}\n", template)

    def test_unfilled_template_is_not_ready(self):
        template = TEMPLATE_PATH.read_text(encoding="utf-8")
        self.assertNotEqual(validator.validate_card(template, stage="ready"), [])

    def test_example_cards_are_ready(self):
        example_paths = sorted(EXAMPLES_DIRECTORY.glob("*.md"))
        self.assertTrue(example_paths, "expected at least one example card")
        for path in example_paths:
            with self.subTest(card=path.name):
                errors = validator.validate_card(
                    path.read_text(encoding="utf-8"), stage="ready"
                )
                self.assertEqual(errors, [])


class CommandLineTests(unittest.TestCase):
    def run_validator(self, *arguments):
        return subprocess.run(
            [sys.executable, str(VALIDATOR_SCRIPT), *arguments],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_exit_code_is_zero_for_a_ready_card(self):
        example = sorted(EXAMPLES_DIRECTORY.glob("*.md"))[0]
        completed = self.run_validator(str(example))
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_exit_code_is_one_for_an_invalid_card(self):
        completed = self.run_validator(str(TEMPLATE_PATH))
        self.assertEqual(completed.returncode, 1)
        self.assertIn("ERROR", completed.stdout)

    def test_json_output_is_the_parsed_model(self):
        example = sorted(EXAMPLES_DIRECTORY.glob("*.md"))[0]
        completed = self.run_validator("--json", str(example))
        parsed = json.loads(completed.stdout)
        self.assertEqual(parsed[0]["path"], str(example))
        self.assertIn("scenarios", parsed[0]["card"])
        self.assertEqual(parsed[0]["errors"], [])


if __name__ == "__main__":
    unittest.main()
