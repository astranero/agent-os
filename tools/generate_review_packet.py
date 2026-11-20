#!/usr/bin/env python3
"""Generate a deterministic local review packet from a PR body and card."""

import argparse
import sys
from pathlib import Path

import check_pull_request
import github_evidence
import validate_card


PACKET_SECTIONS = (
    "Summary",
    "Test evidence",
    "Security",
    "Preview",
    "Residual risks",
)


def read_sections(text):
    """Return Markdown H2 sections using the project's existing parser."""
    _, sections = validate_card.split_sections(text)
    return sections


def card_title(card_text):
    for line in card_text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    raise ValueError("card: missing level-one title")


def build_packet(pr_body, card_text):
    """Validate inputs and return a stable review packet string."""
    errors = check_pull_request.check_pull_request(pr_body, card_text, draft=False)
    if errors:
        raise ValueError("\n".join(errors))

    card_sections = read_sections(card_text)
    pr_sections = read_sections(pr_body)
    lines = [
        f"# Review packet — {card_title(card_text)}",
        "",
        "## User story",
        "",
        card_sections["User story"].strip(),
        "",
        "## Scope",
        "",
        card_sections["Scope"].strip(),
        "",
        "## Acceptance traceability",
        "",
        card_sections["Traceability"].strip(),
    ]

    for section_name in PACKET_SECTIONS:
        lines.extend(("", f"## {section_name}", "", pr_sections[section_name].strip()))

    lines.append("")
    return "\n".join(lines)


def build_live_packet(review_inputs):
    """Build a packet from collected inputs and preserve live check values."""
    packet = build_packet(review_inputs["pr_body"], review_inputs["card"])
    lines = packet.rstrip("\n").splitlines()
    lines.extend(("", "## Live checks", "", "| Check | Status | Conclusion |", "|---|---|---|"))
    for check in review_inputs["check_runs"]:
        lines.append(
            f"| {check.get('name')} | {check.get('status')} | "
            f"{check.get('conclusion')} |"
        )
    lines.append("")
    return "\n".join(lines)


def build_argument_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--pr-body", type=Path)
    source.add_argument("--repo")
    parser.add_argument("--card", type=Path)
    parser.add_argument("--pr", type=int)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(arguments):
    options = build_argument_parser().parse_args(arguments)
    try:
        if options.repo:
            if options.pr is None or options.card is not None:
                raise ValueError("live mode requires --repo and --pr, without --card")
            packet = build_live_packet(
                github_evidence.collect_review_inputs(options.repo, options.pr)
            )
        else:
            if options.card is None or options.pr is not None:
                raise ValueError("offline mode requires --pr-body and --card")
            packet = build_packet(
                options.pr_body.read_text(encoding="utf-8"),
                options.card.read_text(encoding="utf-8"),
            )
    except (OSError, ValueError, github_evidence.GitHubEvidenceError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    options.output.write_text(packet, encoding="utf-8")
    print(f"OK: wrote review packet to {options.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
