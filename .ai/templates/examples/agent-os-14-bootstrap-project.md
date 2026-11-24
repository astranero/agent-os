# AGENT-OS-14 — Bootstrap a new product project

## User story

As the project manager, I want one safe bootstrap command, so that every new
product starts with the same roles, policies, validators, and GitHub templates
without copying vault-only history.

## Scope

Add a local `tools/bootstrap_project.py` command that copies the approved
`.ai/`, `.github/`, `tools/`, and framework tests into a new target, generates
a project-specific README, and excludes `.git`, `HANDOFF.md`, `.ai/KANBAN.md`,
`__pycache__`, and other vault-only files. Refuse a non-empty target and never
create or publish a GitHub repository.

## Non-goals

- Creating GitHub repositories or boards, pushing, or choosing visibility.
- Copying product code or changing the source framework.

## Acceptance criteria

```gherkin
Feature: Bootstrap a product project

  Scenario: A fresh target receives the project foundation
    Given an empty target directory and a project name
    When the bootstrap command runs
    Then it creates the framework files and project README

  @failure
  Scenario: A non-empty target is protected
    Given a target containing an existing file
    When the bootstrap command runs
    Then it fails before changing the target

  Scenario: Vault-only files are excluded
    Given the Agent OS source contains vault-only files and caches
    When the bootstrap command runs
    Then the generated target contains none of those files
```

## Contract

- The target is created only when absent or empty.
- The generated README contains the supplied project name and repository.
- The command performs local file operations only.

## Test plan

- Test fresh creation, non-empty protection, and vault-only exclusions.
- Run the generated target's constitution, template, and repository validators.

## Security impact

- No network, credential, GitHub, or shell execution is added.
- Existing source files are never modified.

## Dependencies

- Python standard library.

## Reuse and cost

Decision: existing
Alternatives checked: manual copying is error-prone; a hosted project
generator adds unnecessary cost and credentials.
Reason: Reuse the current framework files and Python standard library.

## Verification commands

```text
python3 -m unittest discover -s tests -v
python3 tools/validate_constitution.py
python3 tools/generate_github_templates.py --check
python3 tools/validate_card.py .ai/templates/examples/agent-os-14-bootstrap-project.md
python3 tools/validate_repository_rules.py
```

## Traceability

| Acceptance criterion | Test | Result |
|---|---|---|
| A fresh target receives the project foundation | `test_bootstraps_project` | Passed |
| A non-empty target is protected | `test_non_empty_target_fails_without_changes` | Passed |
| Vault-only files are excluded | `test_excludes_vault_only_files` | Passed |
