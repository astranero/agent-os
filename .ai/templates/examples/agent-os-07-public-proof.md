# AGENT-OS-07 — Reconcile public docs and prove the pull-request path

## User story

As the project manager, I want the public repository documentation to match
the live GitHub controls and a normal pull request to run both quality gates,
so that contributors have an accurate, reviewable operating contract.

## Scope

- Update `README.md` with the live repository, board, ruleset, publication
  exclusions, and review-identity limitation.
- Keep the vault `HANDOFF.md` local and remove it from the public repository.
- Create one linked GitHub issue and one small validation pull request.
- Prove the normal pull-request workflow, required checks, and review blocking
  without approving or merging.

## Non-goals

- Creating another repository or changing visibility.
- Changing the ruleset, adding bypass actors, approving, or merging.
- Creating a second GitHub identity.
- Implementing action pinning, security scanners, Storybook, or the review
  packet generator.

## Acceptance criteria

```gherkin
Feature: Keep the public Agent OS contract accurate

  Scenario: Public documentation matches live controls
    Given the public repository and project board exist
    When the README is reviewed against their live URLs and ruleset
    Then it names the public repository, board, publication exclusions, and review limitation

  Scenario: Vault-only handoff is not published
    Given the public repository is built from the project folder
    When the repository tree is inspected
    Then HANDOFF.md and Python cache directories are absent

  Scenario: A normal pull request runs both quality gates
    Given a linked implementation issue and branch exist
    When the pull request workflow completes
    Then both required quality-gate jobs pass

  @failure
  Scenario: The sole code owner cannot self-approve
    Given the pull request author and only code owner are the same account
    When the merge requirements are inspected
    Then GitHub requires an eligible review from another identity
```

## Contract

- The public README is an accurate operator-facing contract.
- The checked-in ruleset remains the only source of branch-protection policy.
- The validation pull request remains unmerged and unapproved.

## Test plan

- Run the full local baseline and template validators.
- Run the generated pull-request checker against the linked issue card.
- Read the live workflow jobs, ruleset, repository tree, and mergeability state.

## Security impact

- Removing `HANDOFF.md` reduces accidental publication of operator context.
- No credentials, bypass actors, or security controls are added.
- The existing ruleset and Dependabot configuration remain unchanged.

## Dependencies

- Public repository `astranero/agent-os`.
- GitHub Project 2 and the active `Protect main` ruleset.

## Reuse and cost

Decision: existing
Alternatives checked: open-source alternatives would not improve the existing
GitHub controls; building a new board or workflow would duplicate them; paid
services are unnecessary.
Reason: Reuse the current repository, board, workflows, and ruleset; add no
dependency or paid service.

## Verification commands

```text
python3 -m unittest discover -s tests -v
python3 tools/validate_constitution.py
python3 tools/generate_github_templates.py --check
python3 tools/validate_card.py .ai/templates/examples/agent-os-07-public-proof.md
python3 tools/validate_repository_rules.py
```

## Traceability

| Acceptance criterion | Test | Result |
| --- | --- | --- |
| Public documentation matches live controls | README review plus GitHub repository/project/ruleset API reads | Pending |
| Vault-only handoff is not published | GitHub repository tree API read | Pending |
| A normal pull request runs both quality gates | GitHub Actions workflow and job API read | Pending |
| The sole code owner cannot self-approve | GitHub pull-request review and mergeability API read | Pending |
