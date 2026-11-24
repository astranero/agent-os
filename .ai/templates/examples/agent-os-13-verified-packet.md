# AGENT-OS-13 — Add verified test reports to review packets

## User story

As the project manager, I want verified JUnit evidence in the packet, so that
reviewers can see both the claimed traceability and the test results that
prove it.

## Scope

Extend the existing packet generator with an optional JUnit XML input. Reuse
the AGENT-OS-12 validator, fail before writing when traceability is not
proven, and add a deterministic `Verified test report` section recording the
matched test name, qualified name, and passed result.

## Non-goals

- Running tests, changing GitHub checks, or parsing non-JUnit formats.
- Inventing results or changing the card validator.

## Acceptance criteria

```gherkin
Feature: Include verified test reports in review packets

  Scenario: Verified test evidence appears in the packet
    Given a valid card and JUnit report with passed traceability rows
    When the packet generator runs with the report
    Then it includes each matched test and its passed result

  @failure
  Scenario: Unverified test evidence blocks packet creation
    Given a card whose traceability is not proven by the report
    When the packet generator runs with the report
    Then it fails and does not write a packet

  Scenario: Offline packet output stays compatible
    Given the same PR body and card without a report
    When the packet generator runs in offline mode
    Then it produces the existing packet text unchanged
```

## Contract

- A report is optional; when supplied, every Passed traceability row must be
  proven before output is written.
- The verified section preserves the exact qualified test name and result.

## Test plan

- Test valid output, unverified output, and unchanged offline output.
- Run the full project suite and all validators.

## Security impact

- Reuses local XML parsing; no network, shell, or credential behavior changes.

## Dependencies

- Python standard library and the AGENT-OS-12 validator.

## Reuse and cost

Decision: existing
Alternatives checked: embedding raw XML is noisy and a new report service adds
cost without improving proof.
Reason: Reuse the existing parser, validator, and packet formatter.

## Verification commands

```text
python3 -m unittest discover -s tests -v
python3 tools/validate_constitution.py
python3 tools/generate_github_templates.py --check
python3 tools/validate_card.py .ai/templates/examples/agent-os-13-verified-packet.md
python3 tools/validate_repository_rules.py
```

## Traceability

| Acceptance criterion | Test | Result |
|---|---|---|
| Verified test evidence appears in the packet | `test_packet_includes_verified_report` | Passed |
| Unverified test evidence blocks packet creation | `test_unverified_report_blocks_packet` | Passed |
| Offline packet output stays compatible | `test_generates_stable_packet` | Passed |
