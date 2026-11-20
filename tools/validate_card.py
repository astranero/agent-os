#!/usr/bin/env python3
"""Validate implementation cards for the Ready and Review stages.

A card is a Markdown document with a `# ID — Title` heading and the `##`
sections listed in REQUIRED_CARD_SECTIONS. Acceptance criteria are Gherkin
scenarios inside a ```gherkin block; the Traceability section maps every
scenario to a test.

Ready stage: every section is present and filled in, the user story has the
standard form, every scenario is well formed, at least one scenario is tagged
@failure, and every scenario has a traceability row with a test location, and the Reuse
and cost section records the decision (existing, open-source, build, or paid)
and the alternatives checked; a paid decision also names its human approver.

Review stage: everything above, and every traceability result is Passed.

Usage:
    python3 tools/validate_card.py [--stage ready|review] [--json] CARD.md...

Exit code 0 means every card is valid; 1 means errors; 2 means bad usage.
"""

import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED_CARD_SECTIONS = (
    "User story",
    "Scope",
    "Non-goals",
    "Acceptance criteria",
    "Contract",
    "Test plan",
    "Security impact",
    "Dependencies",
    "Reuse and cost",
    "Verification commands",
    "Traceability",
)

STAGES = ("ready", "review")

# Order of preference from engineering.md: reuse what the project already
# has, then a viable open-source project, then build, and pay only last.
REUSE_DECISIONS = ("existing", "open-source", "build", "paid")
PAID_DECISION = "paid"
RESULT_VALUES = ("Pending", "Passed", "Failed")
PASSED_RESULT = "Passed"
FAILURE_TAG = "@failure"
TRACEABILITY_HEADER = ("Acceptance criterion", "Test", "Result")

STEP_RANK = {"Given": 0, "When": 1, "Then": 2}
CONTINUATION_KEYWORDS = ("And", "But")

TITLE_PATTERN = re.compile(r"^#\s+(.+?)\s*$")
SECTION_PATTERN = re.compile(r"^##\s+(.+?)\s*$")
FENCE_PATTERN = re.compile(r"^\s*```")
GHERKIN_BLOCK_PATTERN = re.compile(r"```gherkin[^\n]*\n(.*?)```", re.DOTALL)
CODE_PATTERN = re.compile(r"```.*?```|`[^`\n]+`", re.DOTALL)
COMMENT_PATTERN = re.compile(r"<!--.*?-->", re.DOTALL)
# Template placeholders may wrap across lines, so `<...>` may contain newlines.
PLACEHOLDER_PATTERN = re.compile(r"\bTBD\b|\bTODO\b|<[^<>]+>")
SEPARATOR_CELL_PATTERN = re.compile(r"^:?-+:?$")
USER_STORY_PATTERN = re.compile(
    r"^As (an? .+?|the .+?),?\s+I want (.+?),?\s+so that (.+?)\.?$",
    re.IGNORECASE | re.DOTALL,
)
SCENARIO_PATTERN = re.compile(r"^(?:Scenario|Scenario Outline|Example):\s*(.+)$")
STEP_PATTERN = re.compile(r"^(Given|When|Then|And|But)\s+(.+)$")
REUSE_FIELD_PATTERN = re.compile(
    r"^(Decision|Alternatives checked|Approved by):[ \t]*(.*)$", re.MULTILINE
)

# A heuristic, not proof: Then steps should describe what a user or caller
# observes, so wording about calls and code structure is rejected.
IMPLEMENTATION_DETAIL_PATTERN = re.compile(
    r"\b(is called|was called|are called|gets called|calls|invokes?|invoked|"
    r"method|function|private|mock(?:ed)?|stub(?:bed)?)\b",
    re.IGNORECASE,
)


def parse_card(card_text):
    """Return the card model described by card-readiness.schema.json."""
    model, _ = parse_card_with_step_order_problems(card_text)
    return model


def validate_card(card_text, stage="ready"):
    """Return a list of human-readable errors; an empty list means valid."""
    if stage not in STAGES:
        raise ValueError(f"stage must be one of {', '.join(STAGES)}, not {stage!r}")

    model, step_order_problems = parse_card_with_step_order_problems(card_text)
    errors = []
    if model["title"] is None:
        errors.append("card has no '# ID — Title' heading")
    elif PLACEHOLDER_PATTERN.search(model["title"]):
        errors.append(f"title contains placeholder: {model['title']}")
    errors.extend(validate_sections(model["sections"]))
    if "User story" in model["sections"] and model["user_story"] is None:
        errors.append("User story: must read 'As a ..., I want ..., so that ...'")
    if "Reuse and cost" in model["sections"]:
        errors.extend(validate_reuse(model["reuse"]))
    errors.extend(validate_scenarios(model, step_order_problems))
    errors.extend(validate_traceability(model, stage))
    return errors


def parse_card_with_step_order_problems(card_text):
    title, sections = split_sections(card_text)
    scenarios, background, step_order_problems = parse_gherkin(
        sections.get("Acceptance criteria", "")
    )
    model = {
        "title": title,
        "sections": sections,
        "user_story": parse_user_story(sections.get("User story", "")),
        "background": background,
        "scenarios": scenarios,
        "traceability": parse_traceability(sections.get("Traceability", ""))[0],
        "reuse": parse_reuse(sections.get("Reuse and cost", "")),
    }
    return model, step_order_problems


def split_sections(card_text):
    """Split on `#` and `##` headings that are outside code fences."""
    title = None
    sections = {}
    current_section = None
    current_lines = []
    inside_fence = False

    for line in card_text.splitlines():
        if FENCE_PATTERN.match(line):
            inside_fence = not inside_fence
        section_match = None if inside_fence else SECTION_PATTERN.match(line)
        title_match = None if inside_fence else TITLE_PATTERN.match(line)

        if section_match:
            if current_section is not None:
                sections[current_section] = "\n".join(current_lines).strip()
            current_section = section_match.group(1)
            current_lines = []
        elif title_match and title is None and current_section is None:
            title = title_match.group(1)
        elif current_section is not None:
            current_lines.append(line)

    if current_section is not None:
        sections[current_section] = "\n".join(current_lines).strip()
    return title, sections


def parse_user_story(text):
    normalized = " ".join(COMMENT_PATTERN.sub("", text).split())
    match = USER_STORY_PATTERN.match(normalized)
    if not match:
        return None
    role, capability, value = (part.strip() for part in match.groups())
    return {"role": role, "capability": capability, "value": value}


def parse_reuse(text):
    """Read the `Decision:`, `Alternatives checked:`, `Approved by:` lines.

    A field's value continues on following lines until the next field.
    """
    fields = {"decision": None, "alternatives_checked": None, "approved_by": None}
    matches = list(REUSE_FIELD_PATTERN.finditer(COMMENT_PATTERN.sub("", text)))
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else None
        continuation = match.string[match.end():end]
        value = " ".join((match.group(2) + " " + continuation).split())
        key = match.group(1).lower().replace(" ", "_")
        fields[key] = value or None
    return fields


def validate_reuse(reuse):
    errors = []
    decision = reuse["decision"]
    if decision is None:
        errors.append(
            "Reuse and cost: missing 'Decision:' "
            f"(one of {', '.join(REUSE_DECISIONS)})"
        )
    elif decision not in REUSE_DECISIONS:
        errors.append(
            f"Reuse and cost: Decision '{decision}' is not one of "
            f"{', '.join(REUSE_DECISIONS)}"
        )
    if reuse["alternatives_checked"] is None:
        errors.append(
            "Reuse and cost: missing 'Alternatives checked:' "
            "(existing code and open-source options considered, with cost)"
        )
    if decision == PAID_DECISION and reuse["approved_by"] is None:
        errors.append(
            "Reuse and cost: a paid option needs 'Approved by:' naming the human "
            "who approved the cost"
        )
    return errors


def parse_gherkin(acceptance_text):
    """Parse scenarios from ```gherkin blocks.

    Returns (scenarios, background_given_steps, step_order_problems), where
    step_order_problems maps a scenario name to its ordering errors.
    """
    scenarios = []
    background = []
    step_order_problems = {}
    pending_tags = []
    current = None
    current_steps = None
    highest_rank = -1
    previous_keyword = None

    lines = []
    for block in GHERKIN_BLOCK_PATTERN.findall(acceptance_text):
        lines.extend(block.splitlines())

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("|"):
            continue
        if line.startswith("@"):
            pending_tags.extend(line.split())
            continue
        if line.startswith("Feature:") or line.startswith("Examples:"):
            continue
        if line.startswith("Background:"):
            current, current_steps = None, "background"
            highest_rank, previous_keyword = -1, None
            continue

        scenario_match = SCENARIO_PATTERN.match(line)
        if scenario_match:
            current = {
                "name": scenario_match.group(1).strip(),
                "tags": pending_tags,
                "given": [],
                "when": [],
                "then": [],
            }
            scenarios.append(current)
            current_steps = "scenario"
            pending_tags = []
            highest_rank, previous_keyword = -1, None
            continue

        step_match = STEP_PATTERN.match(line)
        if not step_match or current_steps is None:
            continue
        keyword, step_text = step_match.groups()
        if keyword in CONTINUATION_KEYWORDS:
            keyword = previous_keyword or "Given"
        previous_keyword = keyword

        if current_steps == "background":
            background.append(step_text)
            continue

        rank = STEP_RANK[keyword]
        if rank < highest_rank:
            problem = (
                "Given after When or Then" if keyword == "Given" else "When after Then"
            )
            step_order_problems.setdefault(current["name"], []).append(problem)
        highest_rank = max(highest_rank, rank)
        current[keyword.lower()].append(step_text)

    return scenarios, background, step_order_problems


def parse_traceability(text):
    """Return (rows, errors) for the first Markdown table in the section."""
    table_lines = [line.strip() for line in text.splitlines() if line.strip().startswith("|")]
    expected_header = " | ".join(TRACEABILITY_HEADER)
    if not table_lines:
        return [], [f"Traceability: no table found; expected header '{expected_header}'"]

    header = split_table_row(table_lines[0])
    if tuple(header) != TRACEABILITY_HEADER:
        return [], [f"Traceability: header must be '{expected_header}'"]

    rows = []
    errors = []
    for line in table_lines[1:]:
        cells = split_table_row(line)
        if all(SEPARATOR_CELL_PATTERN.match(cell) for cell in cells if cell):
            continue
        if len(cells) != len(TRACEABILITY_HEADER):
            errors.append(f"Traceability: row has {len(cells)} cells, expected 3: {line}")
            continue
        criterion, test_location, result = cells
        rows.append({"criterion": criterion, "test": test_location, "result": result})
    return rows, errors


def split_table_row(line):
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def validate_sections(sections):
    errors = []
    for name in REQUIRED_CARD_SECTIONS:
        if name not in sections:
            errors.append(f"missing section '{name}'")
            continue
        visible_text = COMMENT_PATTERN.sub("", sections[name]).strip()
        if not visible_text:
            errors.append(f"section '{name}' is empty")
            continue
        prose = CODE_PATTERN.sub("", visible_text)
        placeholder = PLACEHOLDER_PATTERN.search(prose)
        if placeholder:
            errors.append(
                f"section '{name}' contains placeholder '{placeholder.group(0)}'"
            )

    commands = sections.get("Verification commands", "")
    if commands and not CODE_PATTERN.search(commands):
        errors.append("Verification commands: no command in a code span or block")
    return errors


def validate_scenarios(model, step_order_problems):
    scenarios = model["scenarios"]
    if not scenarios:
        return ["Acceptance criteria: no Gherkin scenarios found in a ```gherkin block"]

    errors = []
    seen_names = set()
    for scenario in scenarios:
        name = scenario["name"]
        prefix = f"scenario '{name}'"
        if name in seen_names:
            errors.append(f"{prefix}: duplicate scenario name")
        seen_names.add(name)

        if not scenario["given"] and not model["background"]:
            errors.append(f"{prefix} has no Given")
        when_count = len(scenario["when"])
        if when_count != 1:
            errors.append(f"{prefix} has {when_count} When steps; expected exactly 1")
        if not scenario["then"]:
            errors.append(f"{prefix} has no Then")
        for problem in step_order_problems.get(name, []):
            errors.append(f"{prefix}: step out of order ({problem})")
        for then_step in scenario["then"]:
            if IMPLEMENTATION_DETAIL_PATTERN.search(then_step):
                errors.append(
                    f"{prefix}: Then '{then_step}' describes an implementation "
                    "detail instead of an observable result"
                )

    if not any(FAILURE_TAG in scenario["tags"] for scenario in scenarios):
        errors.append(f"Acceptance criteria: no scenario tagged {FAILURE_TAG}")
    return errors


def validate_traceability(model, stage):
    rows, errors = parse_traceability(model["sections"].get("Traceability", ""))
    if "Traceability" not in model["sections"]:
        return []

    scenario_names = {scenario["name"] for scenario in model["scenarios"]}
    traced_names = {row["criterion"] for row in rows}

    for name in sorted(scenario_names - traced_names):
        errors.append(f"scenario '{name}' has no traceability row")
    for row in rows:
        prefix = f"traceability row '{row['criterion']}'"
        if row["criterion"] not in scenario_names:
            errors.append(f"{prefix}: unknown scenario '{row['criterion']}'")
        if not row["test"]:
            errors.append(f"{prefix} has no test location")
        if row["result"] not in RESULT_VALUES:
            errors.append(
                f"{prefix}: result '{row['result']}' is not one of "
                f"{', '.join(RESULT_VALUES)}"
            )
        elif stage == "review" and row["result"] != PASSED_RESULT:
            errors.append(f"{prefix}: result is {row['result']}, not Passed")
    return errors


def build_argument_parser():
    parser = argparse.ArgumentParser(
        description="Validate implementation cards for the Ready or Review stage."
    )
    parser.add_argument("cards", nargs="+", type=Path, help="Markdown card files")
    parser.add_argument("--stage", choices=STAGES, default="ready")
    parser.add_argument(
        "--json", action="store_true", help="print the parsed card model and errors"
    )
    return parser


def main(arguments):
    options = build_argument_parser().parse_args(arguments)
    reports = []
    for card_path in options.cards:
        card_text = card_path.read_text(encoding="utf-8")
        reports.append(
            {
                "path": str(card_path),
                "card": parse_card(card_text),
                "errors": validate_card(card_text, stage=options.stage),
            }
        )

    if options.json:
        print(json.dumps(reports, ensure_ascii=False, indent=2))
    else:
        for report in reports:
            if report["errors"]:
                for error in report["errors"]:
                    print(f"ERROR: {report['path']}: {error}")
            else:
                print(f"OK: {report['path']} is valid for stage '{options.stage}'")

    return 1 if any(report["errors"] for report in reports) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
