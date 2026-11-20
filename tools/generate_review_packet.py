#!/usr/bin/env python3
"""Generate a deterministic local review packet from a PR body and card."""

import argparse
import sys
from pathlib import Path

import check_pull_request
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


def build_argument_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pr-body", type=Path, required=True)
    parser.add_argument("--card", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(arguments):
    options = build_argument_parser().parse_args(arguments)
    try:
        packet = build_packet(
            options.pr_body.read_text(encoding="utf-8"),
            options.card.read_text(encoding="utf-8"),
        )
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    options.output.write_text(packet, encoding="utf-8")
    print(f"OK: wrote review packet to {options.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
