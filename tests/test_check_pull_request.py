"""Behavior tests for the pull-request gate and the CI workflow policy."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

import check_pull_request as gate  # noqa: E402

CHECK_SCRIPT = PROJECT_ROOT / "tools" / "check_pull_request.py"
WORKFLOW_PATH = PROJECT_ROOT / ".github" / "workflows" / "quality-gates.yml"
PILOT_CARD_PATH = PROJECT_ROOT / ".ai" / "templates" / "examples" / "pilot-create-account.md"
PULL_REQUEST_TEMPLATE_PATH = PROJECT_ROOT / ".ai" / "templates" / "pull-request.md"

# Reuse-first rule: only GitHub's own open-source actions, no third parties.
ALLOWED_ACTIONS = ("actions/checkout", "actions/setup-python")

FILLED_PULL_REQUEST = """\
## Card

Closes #12 — PILOT-01 A visitor creates an account

## Summary

Visitors can sign up and see a welcome screen.

## Scope check

- [x] The diff only contains what the card's Scope names.

## Reuse and cost

Decision: open-source
New dependencies: argon2 (MIT) for password hashing.

## Traceability

| Acceptance criterion | Test | Result |
|---|---|---|
| A visitor creates an account with valid details | features/account-creation.feature:7 | Passed |

## Test evidence

- Failing run before implementation: `npm test -- accounts` failed, 3 tests.
- Passing run after implementation: `npm test -- accounts` passed, 3 tests.

## Security

- Scanners run: CodeQL and dependency scan, no findings.

## Preview

https://preview.example.com/pr-12

## Residual risks

Rate limiting is basic; follow-up card PILOT-02.
"""


def pilot_card(result="Pending"):
    text = PILOT_CARD_PATH.read_text(encoding="utf-8")
    return text.replace("| Pending |", f"| {result} |")


class LinkedCardTests(unittest.TestCase):
    def test_closing_keywords_link_a_card(self):
        for keyword in ("Closes", "closes", "Fixes", "Resolves", "fixed", "resolve"):
            with self.subTest(keyword=keyword):
                self.assertEqual(gate.linked_issue_numbers(f"{keyword} #42"), [42])

    def test_plain_mention_does_not_link_a_card(self):
        self.assertEqual(gate.linked_issue_numbers("See #42 for context"), [])

    def test_link_inside_a_comment_is_ignored(self):
        self.assertEqual(gate.linked_issue_numbers("<!-- Closes #42 -->"), [])

    def test_same_card_linked_twice_counts_once(self):
        self.assertEqual(gate.linked_issue_numbers("Closes #42. Fixes #42."), [42])


class PullRequestGateTests(unittest.TestCase):
    def assertReports(self, errors, expected_fragment):
        matching = [error for error in errors if expected_fragment in error]
        self.assertTrue(
            matching, f"expected an error containing {expected_fragment!r}, got {errors!r}"
        )

    def test_complete_ready_pull_request_with_passed_card_passes(self):
        errors = gate.check_pull_request(
            FILLED_PULL_REQUEST, pilot_card("Passed"), draft=False
        )
        self.assertEqual(errors, [])

    def test_pull_request_without_linked_card_fails(self):
        body = FILLED_PULL_REQUEST.replace("Closes #12", "About #12")
        self.assertReports(
            gate.check_pull_request(body, pilot_card(), draft=True), "no linked card"
        )

    def test_pull_request_linking_two_cards_fails(self):
        body = FILLED_PULL_REQUEST.replace("Closes #12", "Closes #12, closes #13")
        self.assertReports(
            gate.check_pull_request(body, pilot_card(), draft=True),
            "links 2 cards (#12, #13)",
        )

    def test_missing_pull_request_section_fails(self):
        body = FILLED_PULL_REQUEST.replace("## Residual risks\n", "## Notes\n")
        self.assertReports(
            gate.check_pull_request(body, pilot_card(), draft=True),
            "pull request: missing section 'Residual risks'",
        )

    def test_placeholders_block_a_pull_request_that_is_ready_for_review(self):
        body = FILLED_PULL_REQUEST.replace(
            "https://preview.example.com/pr-12", "<preview URL>"
        )
        self.assertReports(
            gate.check_pull_request(body, pilot_card("Passed"), draft=False),
            "pull request: section 'Preview' contains placeholder",
        )

    def test_placeholders_are_allowed_while_the_pull_request_is_a_draft(self):
        body = FILLED_PULL_REQUEST.replace(
            "https://preview.example.com/pr-12", "<preview URL>"
        )
        self.assertEqual(gate.check_pull_request(body, pilot_card(), draft=True), [])

    def test_draft_pull_request_validates_the_card_at_ready_stage(self):
        self.assertEqual(
            gate.check_pull_request(FILLED_PULL_REQUEST, pilot_card("Pending"), draft=True),
            [],
        )

    def test_ready_pull_request_requires_every_card_result_passed(self):
        self.assertReports(
            gate.check_pull_request(FILLED_PULL_REQUEST, pilot_card("Pending"), draft=False),
            "card: traceability row",
        )

    def test_card_that_is_not_ready_fails_even_for_a_draft(self):
        broken_card = pilot_card().replace("  @failure\n", "")
        self.assertReports(
            gate.check_pull_request(FILLED_PULL_REQUEST, broken_card, draft=True),
            "card: Acceptance criteria: no scenario tagged @failure",
        )

    def test_unfilled_pull_request_template_fails_for_review(self):
        template = PULL_REQUEST_TEMPLATE_PATH.read_text(encoding="utf-8")
        errors = gate.check_pull_request(template, pilot_card("Passed"), draft=False)
        self.assertReports(errors, "no linked card")
        self.assertReports(errors, "contains placeholder")


class CommandLineTests(unittest.TestCase):
    def run_gate(self, *arguments):
        return subprocess.run(
            [sys.executable, str(CHECK_SCRIPT), *arguments],
            capture_output=True,
            text=True,
            check=False,
        )

    def write(self, directory, name, text):
        path = Path(directory) / name
        path.write_text(text, encoding="utf-8")
        return str(path)

    def test_linked_issue_command_prints_the_number(self):
        with tempfile.TemporaryDirectory() as directory:
            body = self.write(directory, "body.md", FILLED_PULL_REQUEST)
            completed = self.run_gate("linked-issue", body)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), "12")

    def test_linked_issue_command_fails_without_a_link(self):
        with tempfile.TemporaryDirectory() as directory:
            body = self.write(directory, "body.md", "No link here.")
            completed = self.run_gate("linked-issue", body)
        self.assertEqual(completed.returncode, 1)

    def test_check_command_exit_codes(self):
        with tempfile.TemporaryDirectory() as directory:
            body = self.write(directory, "body.md", FILLED_PULL_REQUEST)
            passed_card = self.write(directory, "passed.md", pilot_card("Passed"))
            pending_card = self.write(directory, "pending.md", pilot_card("Pending"))
            passing = self.run_gate(
                "check", "--pr-body", body, "--card", passed_card, "--draft", "false"
            )
            failing = self.run_gate(
                "check", "--pr-body", body, "--card", pending_card, "--draft", "false"
            )
        self.assertEqual(passing.returncode, 0, passing.stdout)
        self.assertEqual(failing.returncode, 1)
        self.assertIn("ERROR: card:", failing.stdout)


class WorkflowPolicyTests(unittest.TestCase):
    def setUp(self):
        self.workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
        self.steps = [
            step for job in self.workflow["jobs"].values() for step in job["steps"]
        ]
        self.run_scripts = [step["run"] for step in self.steps if "run" in step]

    def triggers(self):
        # PyYAML reads the bare key `on` as the boolean True.
        return self.workflow.get("on", self.workflow.get(True))

    def test_workflow_runs_on_pull_requests_and_pushes_to_main(self):
        triggers = self.triggers()
        self.assertIn("ready_for_review", triggers["pull_request"]["types"])
        self.assertIn("edited", triggers["pull_request"]["types"])
        self.assertEqual(triggers["push"]["branches"], ["main"])

    def test_workflow_grants_only_read_permissions(self):
        permissions = self.workflow["permissions"]
        self.assertEqual(set(permissions.values()), {"read"})
        for job in self.workflow["jobs"].values():
            with self.subTest(job=job.get("name")):
                self.assertEqual(set(job.get("permissions", {"x": "read"}).values()), {"read"})

    def test_workflow_uses_only_allowed_actions(self):
        for step in self.steps:
            if "uses" in step:
                with self.subTest(uses=step["uses"]):
                    action_name = step["uses"].split("@", 1)[0]
                    self.assertIn(action_name, ALLOWED_ACTIONS)

    def test_event_text_never_appears_directly_in_shell_commands(self):
        for script in self.run_scripts:
            with self.subTest(script=script.splitlines()[0]):
                self.assertNotIn("${{ github.event", script)
                self.assertNotIn("${{ github.head_ref", script)

    def test_workflow_runs_every_gate(self):
        all_commands = "\n".join(self.run_scripts)
        for command in (
            "python -m unittest discover -s tests",
            "python tools/validate_constitution.py",
            "python tools/generate_github_templates.py --check",
            "python tools/check_pull_request.py check",
        ):
            with self.subTest(command=command):
                self.assertIn(command, all_commands)


if __name__ == "__main__":
    unittest.main()
