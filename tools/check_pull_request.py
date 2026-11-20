#!/usr/bin/env python3
"""Pull-request gate: one linked card, a complete description, a valid card.

A draft pull request is work in progress: its description must have every
section, and its linked card must pass the Ready stage. A pull request that is
ready for review must also have no template placeholders left, and its card
must pass the Review stage (every traceability result Passed).

Usage:
    python3 tools/check_pull_request.py linked-issue PR_BODY.md
        Print the linked card's issue number; exit 1 unless exactly one.
    python3 tools/check_pull_request.py check --pr-body PR_BODY.md \\
        --card CARD.md --draft true|false
        Exit 0 when the gate passes; 1 with one ERROR line per problem.
"""

import argparse
import re
import sys
from pathlib import Path

import validate_card
from generate_github_templates import REQUIRED_PULL_REQUEST_SECTIONS

# GitHub's closing keywords; only these link a pull request to an issue.
CLOSING_REFERENCE_PATTERN = re.compile(
    r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?):?\s+#(\d+)\b", re.IGNORECASE
)


def linked_issue_numbers(pull_request_body):
    visible_text = validate_card.COMMENT_PATTERN.sub("", pull_request_body)
    numbers = []
    for match in CLOSING_REFERENCE_PATTERN.finditer(visible_text):
        number = int(match.group(1))
        if number not in numbers:
            numbers.append(number)
    return numbers


def check_pull_request(pull_request_body, card_text, draft):
    """Return a list of errors; an empty list means the gate passes."""
    errors = check_linked_card(pull_request_body)
    errors.extend(check_description(pull_request_body, draft))
    card_stage = "ready" if draft else "review"
    errors.extend(
        f"card: {error}"
        for error in validate_card.validate_card(card_text, stage=card_stage)
    )
    return errors


def check_linked_card(pull_request_body):
    numbers = linked_issue_numbers(pull_request_body)
    if not numbers:
        return ["pull request: no linked card; add 'Closes #<issue>' to the Card section"]
    if len(numbers) > 1:
        listed = ", ".join(f"#{number}" for number in numbers)
        return [f"pull request: links {len(numbers)} cards ({listed}); link exactly one"]
    return []


def check_description(pull_request_body, draft):
    _, sections = validate_card.split_sections(pull_request_body)
    errors = []
    for name in REQUIRED_PULL_REQUEST_SECTIONS:
        if name not in sections:
            errors.append(f"pull request: missing section '{name}'")
            continue
        if draft:
            continue
        visible_text = validate_card.COMMENT_PATTERN.sub("", sections[name]).strip()
        if not visible_text:
            errors.append(f"pull request: section '{name}' is empty")
            continue
        prose = validate_card.CODE_PATTERN.sub("", visible_text)
        placeholder = validate_card.PLACEHOLDER_PATTERN.search(prose)
        if placeholder:
            errors.append(
                f"pull request: section '{name}' contains placeholder "
                f"'{placeholder.group(0)}'"
            )
    return errors


def parse_boolean(text):
    normalized = text.strip().lower()
    if normalized not in ("true", "false"):
        raise argparse.ArgumentTypeError("expected 'true' or 'false'")
    return normalized == "true"


def build_argument_parser():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)

    linked = commands.add_parser("linked-issue", help="print the linked issue number")
    linked.add_argument("pr_body", type=Path)

    check = commands.add_parser("check", help="run the pull-request gate")
    check.add_argument("--pr-body", type=Path, required=True)
    check.add_argument("--card", type=Path, required=True)
    check.add_argument("--draft", type=parse_boolean, required=True)
    return parser


def main(arguments):
    options = build_argument_parser().parse_args(arguments)

    if options.command == "linked-issue":
        body = options.pr_body.read_text(encoding="utf-8")
        problems = check_linked_card(body)
        if problems:
            print(f"ERROR: {problems[0]}", file=sys.stderr)
            return 1
        print(linked_issue_numbers(body)[0])
        return 0

    errors = check_pull_request(
        options.pr_body.read_text(encoding="utf-8"),
        options.card.read_text(encoding="utf-8"),
        draft=options.draft,
    )
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    stage = "Ready" if options.draft else "Review"
    print(f"OK: pull request and linked card pass the {stage} gate")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
