# AGENT-OS-09 — Pin GitHub Actions to commit SHAs

## User story

As the project manager, I want every workflow action pinned to an immutable
commit, so that a moved tag cannot silently change the quality gates.

## Scope

- Resolve each currently used official action tag through GitHub.
- Replace each mutable action reference with its full 40-character commit SHA
  and retain the human-readable version as a trailing comment.
- Add a regression test that rejects mutable action references.

## Non-goals

- Changing workflow behavior or adding actions.
- Adding security scanners or changing branch protection.
- Pinning dependencies outside the GitHub Actions workflow.

## Acceptance criteria

```gherkin
Feature: Pin quality-gate actions

  Scenario: Every workflow action is immutable
    Given the quality-gates workflow uses official GitHub actions
    When each action reference is inspected
    Then every reference contains a full commit SHA and a version comment

  Scenario: The policy test rejects mutable action references
    Given a workflow action uses a tag or branch name
    When the workflow policy test runs
    Then the test fails and names the unpinned reference

  @failure
  Scenario: A workflow with no action pins cannot pass
    Given the workflow contains an action reference without a 40-character SHA
    When the repository quality gate runs
    Then the repository quality gate fails
```

## Contract

- The workflow behavior and required job names remain unchanged.
- Each `uses:` reference is reproducible from a Git commit.

## Test plan

- Run the new pinning regression test before and after pinning.
- Run the full local suite and repository validators.
- Run the live Quality gates workflow on the pull request.

## Security impact

- Reduces the risk of an action tag being moved to unreviewed code.
- No credentials or permissions change.

## Dependencies

- GitHub API access to resolve official action tags.

## Reuse and cost

Decision: existing
Alternatives checked: mutable tags are less reproducible; replacing the
official actions or adding a paid scanner is unnecessary.
Reason: Reuse the current official actions and workflow with immutable refs.

## Verification commands

```text
python3 -m unittest discover -s tests -v
python3 tools/validate_constitution.py
python3 tools/generate_github_templates.py --check
python3 tools/validate_card.py .ai/templates/examples/agent-os-09-pin-actions.md
python3 tools/validate_repository_rules.py
```

## Traceability

| Acceptance criterion | Test | Result |
| --- | --- | --- |
| Every workflow action is immutable | Workflow pinning policy test | Passed |
| The policy test rejects mutable action references | `test_workflow_actions_are_pinned_to_commit_shas` | Passed |
| A workflow with no action pins cannot pass | Same policy test with mutable-reference regression fixture | Passed |
