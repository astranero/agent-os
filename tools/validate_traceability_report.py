#!/usr/bin/env python3
"""Verify card traceability rows against a JUnit XML test report."""

import argparse
import sys
import xml.etree.ElementTree as ElementTree
from pathlib import Path

import validate_card


class ReportError(ValueError):
    """Raised when a JUnit report cannot safely prove test evidence."""


def read_test_cases(report_text):
    """Return test names and their observed result states from JUnit XML."""
    try:
        root = ElementTree.fromstring(report_text)
    except ElementTree.ParseError as error:
        raise ReportError(f"malformed JUnit XML: {error}") from error

    cases = {}
    for test_case in root.findall(".//testcase"):
        name = test_case.get("name")
        if not name:
            raise ReportError("test case has no name")
        class_name = test_case.get("classname")
        qualified_name = f"{class_name}.{name}" if class_name else name
        states = {child.tag.rsplit("}", 1)[-1] for child in test_case}
        unknown = states - {"failure", "error", "skipped"}
        if unknown:
            raise ReportError(
                f"test '{qualified_name}' has unknown result state: "
                f"{', '.join(sorted(unknown))}"
            )
        state = "passed"
        if "error" in states:
            state = "errored"
        elif "failure" in states:
            state = "failed"
        elif "skipped" in states:
            state = "skipped"
        cases.setdefault(name, []).append((qualified_name, state))
        if class_name:
            cases.setdefault(qualified_name, []).append((qualified_name, state))
    return cases


def verify_traceability(card_text, report_text):
    """Return named verification errors, or an empty list when proven."""
    sections = validate_card.split_sections(card_text)[1]
    rows, errors = validate_card.parse_traceability(sections.get("Traceability", ""))
    if errors:
        return errors
    cases = read_test_cases(report_text)
    verification_errors = []
    for row in rows:
        test_name = row["test"].strip().strip("`")
        matches = cases.get(test_name, [])
        if row["result"] != "Passed":
            verification_errors.append(
                f"traceability '{row['criterion']}': card result is {row['result']}"
            )
        elif not matches:
            verification_errors.append(
                f"traceability '{row['criterion']}': no test case '{test_name}'"
            )
        elif len(matches) > 1:
            verification_errors.append(
                f"traceability '{row['criterion']}': test case '{test_name}' is ambiguous"
            )
        elif matches[0][1] != "passed":
            verification_errors.append(
                f"traceability '{row['criterion']}': test case '{test_name}' "
                f"is {matches[0][1]}"
            )
    return verification_errors


def verified_traceability_rows(card_text, report_text):
    """Return the passed card rows with the exact report names that prove them."""
    errors = verify_traceability(card_text, report_text)
    if errors:
        raise ReportError("\n".join(errors))
    sections = validate_card.split_sections(card_text)[1]
    rows, _ = validate_card.parse_traceability(sections["Traceability"])
    cases = read_test_cases(report_text)
    return [
        {
            "criterion": row["criterion"],
            "test": row["test"].strip().strip("`"),
            "qualified_name": cases[row["test"].strip().strip("`")][0][0],
            "result": cases[row["test"].strip().strip("`")][0][1],
        }
        for row in rows
    ]


def build_argument_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--card", type=Path, required=True)
    parser.add_argument("--junit-xml", type=Path, required=True)
    return parser


def main(arguments):
    options = build_argument_parser().parse_args(arguments)
    try:
        errors = verify_traceability(
            options.card.read_text(encoding="utf-8"),
            options.junit_xml.read_text(encoding="utf-8"),
        )
    except (OSError, ReportError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    print("OK: traceability is backed by passed test cases")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
