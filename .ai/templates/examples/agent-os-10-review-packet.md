# AGENT-OS-10 — Generate a deterministic review packet

## User story

As the project manager, I want a generated review packet for each PR, so that
acceptance criteria, tests, security findings, reuse choice, and residual risk
are easy to inspect before merging.

## Scope

- Add a local command that reads a completed PR body and linked card.
- Validate their required review sections.
- Write a deterministic Markdown packet containing the user story, scope,
  traceability, test evidence, security, reuse/cost, preview, and residual
  risk sections.

## Non-goals

- Calling GitHub APIs, inventing test results, or running security scanners.
- Changing PRs or replacing the existing PR gate.

## Acceptance criteria

```gherkin
Feature: Generate review packets

  Scenario: A valid review produces a deterministic packet
    Given a completed PR body and a Review-stage card with evidence
    When the review-packet command runs
    Then it writes the same structured Markdown packet for the same inputs

  Scenario: Missing evidence blocks packet generation
    Given a PR body with an incomplete test-evidence section
    When the review-packet command runs
    Then it fails and names the missing evidence

  @failure
  Scenario: Pending traceability cannot be presented as complete
    Given a Review-stage card containing a Pending traceability result
    When the review-packet command runs
    Then it fails without writing a completed packet
```

## Contract

- Identical inputs produce byte-identical Markdown.
- The command copies evidence; it never changes a result or fills a missing
  result with an assumption.

## Test plan

- Test valid generation and byte stability.
- Test missing evidence and pending traceability failures.
- Run the full project suite and validators.

## Security impact

- The command is local and read-only with respect to its inputs.
- It does not call GitHub or handle credentials.

## Dependencies

- Existing card and PR validation code.

## Reuse and cost

Decision: existing
Alternatives checked: a hosted dashboard is unnecessary for the first local
review slice; manually copying sections is error-prone.
Reason: Reuse the current parsers and Python standard library; add no
dependency or paid service.

## Verification commands

```text
python3 -m unittest discover -s tests -v
python3 tools/validate_constitution.py
python3 tools/generate_github_templates.py --check
python3 tools/validate_card.py .ai/templates/examples/agent-os-10-review-packet.md
python3 tools/validate_repository_rules.py
```

## Traceability

| Acceptance criterion | Test | Result |
| --- | --- | --- |
| A valid review produces a deterministic packet | `test_generates_stable_packet` | Passed |
| Missing evidence blocks packet generation | `test_missing_evidence_fails` | Passed |
| Pending traceability cannot be presented as complete | `test_pending_traceability_fails` | Passed |
