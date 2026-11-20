# Agent OS — agent-led engineering operating system

A controlled development system in which existing coding agents (Copilot
coding agent, Codex, Claude Code, Cursor, OpenHands) work inside defined
roles, use approved tools, produce evidence, and cannot bypass quality gates.
GitHub is the system of record; `.ai/` is the canonical, provider-neutral
source from which provider files are later generated.

## Status

Phase 0 (constitution) and the role capability part of Phase 1 are
`status: accepted`, approved by the project manager on 2026-11-20. Nothing
here is enforced by GitHub yet.

The Ready-card schema and acceptance-criteria validation (AGENT-OS-02) and
the reuse-first, paid-last rule (AGENT-OS-02A, principles v0.2.0) are
accepted. Every card records whether it reuses existing code, uses open
source, builds, or pays; paid options need a named human approver.

## Layout

```
.ai/
  principles/   constitution, engineering, architecture, security, testing, frontend
  roles/        one profile per role, ten required sections each
  policies/     role-permissions.yaml, role-capability.schema.json,
                card-readiness.schema.json, main-branch-ruleset.json
  templates/    implementation-card.md, user-story.md, pull-request.md,
                examples/ (pilot card)
.github/        generated from .ai/templates/ — do not edit by hand
  ISSUE_TEMPLATE/  implementation-card.md, user-story.md, config.yml
  pull_request_template.md
  workflows/quality-gates.yml   hand-written CI, not generated
  CODEOWNERS, dependabot.yml    hand-written, checked by validate_repository_rules.py
tools/
  validate_constitution.py
  validate_card.py
  generate_github_templates.py
  check_pull_request.py
  validate_repository_rules.py
tests/
  test_validate_constitution.py
  test_validate_card.py
```

## Commands

```
pip install -r requirements.txt
python3 -m unittest discover -s tests -v
python3 tools/validate_constitution.py
python3 tools/validate_card.py path/to/card.md            # Ready stage
python3 tools/validate_card.py --stage review card.md     # all results Passed
python3 tools/validate_card.py --json card.md             # parsed card model
python3 tools/generate_github_templates.py                # regenerate .github/
python3 tools/generate_github_templates.py --check        # fail on drift
python3 tools/check_pull_request.py check --pr-body body.md --card card.md --draft false
python3 tools/validate_repository_rules.py                # ruleset, CODEOWNERS, Dependabot
```

## CI

`.github/workflows/quality-gates.yml` runs on every pull request and push to
`main`: unit tests, the constitution validator, and the template drift
check. For pull requests it also requires exactly one `Closes #N` link,
fetches that issue as the card, and validates it at the Ready stage while
the PR is a draft and at the Review stage once it is ready for review. It
uses a read-only token and only `actions/checkout` and `actions/setup-python`.

## Protecting `main`

`.ai/policies/main-branch-ruleset.json` is a GitHub repository ruleset kept
in version control. It blocks force pushes and deleting `main`, requires a
pull request approved by a code owner (`.github/CODEOWNERS`), dismisses
approvals when new commits arrive, requires someone other than the author
of the last push to approve, and requires both quality-gate jobs to pass
from GitHub Actions on an up-to-date branch. Nobody can bypass it, including
admins. `validate_repository_rules.py` fails if a workflow job is renamed
without updating the ruleset.

Dependabot (`.github/dependabot.yml`) opens weekly update PRs for the
actions and the pip requirements. Those PRs cannot link a card, so they skip
only the "Pull request and linked card" job; they still need the other
checks and a code-owner review.

Apply the ruleset once after the first push (needs `gh` logged in as a
repository admin; replace `astranero/agent-os` with the real repository):

```
gh api --method POST repos/astranero/agent-os/rulesets \
  --input .ai/policies/main-branch-ruleset.json
```

To change it later, edit the JSON file in a reviewed PR, then update the
ruleset with `gh api --method PUT repos/OWNER/REPO/rulesets/RULESET_ID
--input ...`. On GitHub's free plan, rulesets are enforced only on public
repositories; a private repository needs a paid plan, which needs the
project manager's approval.

Because the project manager is the only code owner and GitHub never lets a
PR author approve their own PR, PRs must be opened by agent accounts (or
another person) for the project manager to approve them.

## Moving to GitHub

`projects/agent-os` lives inside the Magpie vault, which is already a git
repository, so it is not a separate repo yet. To publish it, copy the folder
into a new repository (for example `agent-os`), commit, and push; the
workflow starts running on the first pull request.

A card is Ready when every section is filled in (no `TBD`, `TODO`, or
`<placeholder>`), the user story reads "As a …, I want …, so that …", every
Gherkin scenario has Given, exactly one When, and Then in that order with
observable Then steps, at least one scenario is tagged `@failure`, and every
scenario has a traceability row with a test location. A card can move to
Review only when every traceability result is `Passed`.

The validator checks that principles carry a version and status, every role
profile has the required sections, the manifest uses only known
capabilities, no capability is both granted and denied, and no role is ever
granted merging, self-approval, branch-protection changes, security-workflow
disabling, finding suppression, or critical-finding downgrades.

## Next cards

The remaining first-implementation cards (Ready-card schema, GitHub board,
templates, branch protection, CI gates, Gherkin traceability, CodeQL,
Semgrep, Storybook, review packet, coordinator, vertical slice) are tracked
in the vault board at `.ai/KANBAN.md`.
