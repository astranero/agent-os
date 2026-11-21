"""Tests for the read-only GitHub evidence adapter."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "tools"))
sys.path.insert(0, str(PROJECT_ROOT / "tests"))

import github_evidence  # noqa: E402
import generate_review_packet  # noqa: E402
from test_generate_review_packet import CARD, PR_BODY  # noqa: E402


def response(payload, returncode=0, stderr=""):
    return SimpleNamespace(
        returncode=returncode,
        stdout=json.dumps(payload),
        stderr=stderr,
    )


class FakeGh:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.commands = []

    def __call__(self, command, capture_output, text):
        self.commands.append(command)
        return next(self.responses)


class GitHubEvidenceTests(unittest.TestCase):
    def test_collects_pr_card_and_checks(self):
        runner = FakeGh(
            [
                response({"body": "Closes #42\n", "head": {"sha": "abc123"}}),
                response({"body": "# Card\n"}),
                response({"check_runs": [{"name": "Quality gates", "status": "completed", "conclusion": "success"}]}),
            ]
        )

        result = github_evidence.collect_review_inputs("astranero/agent-os", 10, runner)

        self.assertEqual(result["card"], "# Card\n")
        self.assertEqual(result["check_runs"][0]["conclusion"], "success")
        self.assertEqual(runner.commands[0][:2], ["gh", "api"])
        self.assertTrue(all(command[1] == "api" for command in runner.commands))
        self.assertEqual(
            runner.commands[2][2], "repos/astranero/agent-os/commits/abc123/check-runs"
        )

    def test_api_and_linkage_failures(self):
        api_failure = FakeGh([response({}, returncode=1, stderr="not logged in")])
        with self.assertRaisesRegex(github_evidence.GitHubEvidenceError, "not logged in"):
            github_evidence.collect_review_inputs("astranero/agent-os", 10, api_failure)

        ambiguous = FakeGh([response({"body": "no linked card"})])
        with self.assertRaisesRegex(github_evidence.GitHubEvidenceError, "exactly one"):
            github_evidence.collect_review_inputs("astranero/agent-os", 10, ambiguous)

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "packet.md"
            with patch(
                "generate_review_packet.github_evidence.collect_review_inputs",
                side_effect=github_evidence.GitHubEvidenceError("api unavailable"),
            ):
                exit_code = generate_review_packet.main(
                    ["--repo", "astranero/agent-os", "--pr", "10", "--output", str(output)]
                )
            self.assertEqual(exit_code, 1)
            self.assertFalse(output.exists())

    def test_packet_includes_live_checks(self):
        packet = generate_review_packet.build_live_packet(
            {
                "pr_body": PR_BODY,
                "card": CARD,
                "check_runs": [
                    {"name": "Quality gates", "status": "completed", "conclusion": "success"}
                ],
            }
        )
        self.assertIn("## Live checks", packet)
        self.assertIn("| Quality gates | completed | success |", packet)


if __name__ == "__main__":
    unittest.main()
