#!/usr/bin/env python3
"""Collect review inputs from GitHub through read-only gh API calls."""

import json
import subprocess

import check_pull_request


class GitHubEvidenceError(RuntimeError):
    """Raised when live GitHub evidence cannot be collected safely."""


def _run_api(endpoint, runner):
    command = [
        "gh",
        "api",
        endpoint,
        "--header",
        "Accept: application/vnd.github+json",
    ]
    result = runner(command, capture_output=True, text=True)
    if result.returncode != 0:
        message = result.stderr.strip() or "gh api returned a non-zero exit status"
        raise GitHubEvidenceError(f"GitHub API request failed: {message}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise GitHubEvidenceError(
            f"GitHub API returned invalid JSON for {endpoint}"
        ) from error


def collect_review_inputs(repo, pull_request_number, runner=subprocess.run):
    """Return PR body, linked card, and check runs without writing to GitHub."""
    pr_endpoint = f"repos/{repo}/pulls/{pull_request_number}"
    pull_request = _run_api(pr_endpoint, runner)
    body = pull_request.get("body") or ""
    linked_issues = check_pull_request.linked_issue_numbers(body)
    if len(linked_issues) != 1:
        raise GitHubEvidenceError(
            "linked-card error: expected exactly one linked issue, found "
            f"{len(linked_issues)}"
        )

    issue_endpoint = f"repos/{repo}/issues/{linked_issues[0]}"
    issue = _run_api(issue_endpoint, runner)
    head_sha = pull_request.get("head", {}).get("sha")
    if not head_sha:
        raise GitHubEvidenceError("GitHub PR response has no head commit SHA")

    checks_endpoint = f"repos/{repo}/commits/{head_sha}/check-runs"
    checks = _run_api(checks_endpoint, runner)
    check_runs = checks.get("check_runs")
    if not isinstance(check_runs, list):
        raise GitHubEvidenceError("GitHub check-runs response has no check_runs list")

    return {
        "pr_body": body,
        "card": issue.get("body") or "",
        "check_runs": check_runs,
    }
