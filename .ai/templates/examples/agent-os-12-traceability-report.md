# AGENT-OS-12 — Validate traceability against real test reports

## User story

As the project manager, I want traceability checked against machine-readable
test results, so that a PR cannot claim coverage using a test name that was
never executed successfully.

## Scope

Add a standard-library JUnit XML reader and a validator command that compares
a card's Traceability rows with passed test cases. Support exact test-name or
`classname.testname` matching, report missing/failed cases clearly, and keep
the existing packet generator unchanged until this evidence validator is
proven.

## Non-goals

- Running tests, installing a test framework, or changing card criteria.
- Inventing results or blocking GitHub merges directly.

## Acceptance criteria

```gherkin
Feature: Verify card traceability from test reports

  Scenario: Passed traceability is backed by a passed test case
    Given a card row and a JUnit test case with the same qualified name
    When the traceability validator runs
    Then it reports the row as verified

  @failure
  Scenario: Missing or unsuccessful test evidence blocks verification
    Given a card row with no passed matching test case
    When the traceability validator runs
    Then it fails and names the unmatched or unsuccessful test

  @failure
  Scenario: Invalid test report blocks verification
    Given malformed XML or an unknown test result state
    When the traceability validator runs
    Then it fails closed with a report error
```

## Contract

- The command reads the card and report, does not run tests, and exits non-zero
  unless every Passed row is backed by one passed test case.
- Qualified and unqualified test names are matched exactly; ambiguous matches
  fail closed.

## Test plan

- Test valid, missing, failed, errored, malformed, unknown, and ambiguous input.
- Run the full project suite and all repository validators.

## Security impact

- Standard-library XML parsing only; no network or shell execution.
- No secrets or external writes.

## Dependencies

- Python standard library.

## Reuse and cost

Decision: existing
Alternatives checked: a new test-report service adds cost and a
framework-specific parser reduces portability.
Reason: Reuse Python's XML parser, the current card validator, and standard
library CLI patterns.

## Verification commands

```text
python3 -m unittest discover -s tests -v
python3 tools/validate_constitution.py
python3 tools/generate_github_templates.py --check
python3 tools/validate_card.py .ai/templates/examples/agent-os-12-traceability-report.md
python3 tools/validate_repository_rules.py
```

## Traceability

| Acceptance criterion | Test | Result |
|---|---|---|
| Passed traceability is backed by a passed test case | `test_valid_report_verifies_rows` | Passed |
| Missing or unsuccessful test evidence blocks verification | `test_missing_failed_and_errored_cases_fail` | Passed |
| Invalid test report blocks verification | `test_malformed_and_unknown_reports_fail` | Passed |
