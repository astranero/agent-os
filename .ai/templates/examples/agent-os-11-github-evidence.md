# AGENT-OS-11 — Collect live GitHub evidence for review packets

## User story

As the project manager, I want the packet generator to read GitHub evidence
through a read-only interface, so that review decisions use current evidence
and never rely on invented or stale results.

## Scope

Add a small `gh api`-backed read-only adapter that fetches one PR, resolves
its single linked implementation-card issue, fetches the PR's check runs, and
feeds those values into the existing deterministic packet generator. Use
argument lists rather than a shell and expose clear errors for unavailable
authentication, API failures, or ambiguous card linkage.

## Non-goals

- Writing to GitHub, approving or merging PRs, or changing the ruleset.
- Running scanners or replacing the local card and PR validators.
- Treating a non-success check as passed.

## Acceptance criteria

```gherkin
Feature: Collect live GitHub review evidence

  Scenario: A live PR produces a packet with check evidence
    Given an authenticated GitHub PR linked to exactly one implementation card
    When the live review-packet command runs
    Then the packet contains the PR's card evidence and each check's name,
    status, and conclusion

  @failure
  Scenario: GitHub API failure blocks packet generation
    Given the read-only GitHub API returns an error
    When the live review-packet command runs
    Then it fails with the API error and writes no packet

  @failure
  Scenario: Ambiguous card linkage blocks packet generation
    Given a PR body links zero or more than one implementation card
    When the live review-packet command runs
    Then it fails with a linked-card error and writes no packet

  Scenario: Offline packet generation remains deterministic
    Given the same saved PR body and card are provided twice
    When the offline review-packet command runs
    Then it produces identical packet text both times
```

## Contract

- Live mode performs only read-only `gh api` calls and writes a packet only
  after all inputs validate.
- Check name, status, and conclusion are copied without reinterpretation.

## Test plan

- Fake the `gh` runner and assert exact read-only arguments.
- Test API failure, missing linkage, and multiple linkage.
- Preserve the existing offline deterministic-output test.

## Security impact

- No shell evaluation and no token handling in project files.
- The adapter relies on `gh`'s existing local authentication.

## Dependencies

- Existing `gh` CLI and Python standard library.

## Reuse and cost

Decision: existing
Alternatives checked: a GitHub SDK adds dependency and credential surface;
manual copying is not reproducible.
Reason: Reuse the installed `gh` CLI, existing linked-card parser, packet
formatter, and Python standard library.

## Verification commands

```text
python3 -m unittest discover -s tests -v
python3 tools/validate_constitution.py
python3 tools/generate_github_templates.py --check
python3 tools/validate_card.py .ai/templates/examples/agent-os-11-github-evidence.md
python3 tools/validate_repository_rules.py
```

## Traceability

| Acceptance criterion | Test | Result |
|---|---|---|
| A live PR produces a packet with check evidence | `test_collects_pr_card_and_checks` | Passed |
| GitHub API failure blocks packet generation | `test_api_and_linkage_failures` | Passed |
| Ambiguous card linkage blocks packet generation | `test_api_and_linkage_failures` | Passed |
| Offline packet generation remains deterministic | `test_generates_stable_packet` | Passed |
