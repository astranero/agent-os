# Agent OS — agent-led engineering operating system

A controlled development system in which existing coding agents (Copilot
coding agent, Codex, Claude Code, Cursor, OpenHands) work inside defined
roles, use approved tools, produce evidence, and cannot bypass quality gates.
GitHub is the system of record; `.ai/` is the canonical, provider-neutral
source from which provider files are later generated.

## Status

Phase 0 (constitution) and the role capability part of Phase 1 are
`status: accepted`, approved by the project manager on 2026-11-20. The
public system of record is [astranero/agent-os](https://github.com/astranero/agent-os),
with a public [Agent OS Kanban project](https://github.com/users/astranero/projects/2).
The `Protect main` ruleset is active and the initial quality-gated push passed.
The repository also contains a controlled direct-push rejection as protection
evidence. The normal pull-request path is verified by the live validation PR.
This is single-maintainer mode: pull requests and all quality checks remain
required, but GitHub does not require an independent approval because the
project manager and agent currently use the same account. The project manager
should still review every agent PR before merging it.

The Ready-card schema and acceptance-criteria validation (AGENT-OS-02) and
the reuse-first, paid-last rule (AGENT-OS-02A, principles v0.2.0) are
accepted. Every card records whether it reuses existing code, uses open
source, builds, or pays; paid options need a named human approver.

## Parallel workstreams

Independent cards may be implemented and reviewed concurrently. Each active
card owns explicit files or interfaces and has its dependencies recorded.
Cards with overlapping ownership or dependent contracts are ordered and
rebased before merge; unrelated cards do not wait for one another. Every pull
request remains independently reviewable and must pass the same tests,
evidence, Quality gates, and maintainer review before it is merged.

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
pull request, dismisses stale reviews when new commits arrive, and requires
both quality-gate jobs to pass from GitHub Actions on an up-to-date branch.
Single-maintainer mode intentionally requires no independent approval. Nobody
can bypass the ruleset, including admins. `validate_repository_rules.py` fails
if a workflow job is renamed without updating the ruleset.

Dependabot (`.github/dependabot.yml`) opens weekly update PRs for the
actions and the pip requirements. Those PRs cannot link a card, so they skip
only the "Pull request and linked card" job; they still need the other check.

The ruleset is already applied to `astranero/agent-os`. To reproduce or update
it, use `gh` logged in as a repository administrator and keep the checked-in
JSON as the source of truth:

```
gh api --method POST repos/astranero/agent-os/rulesets \
  --input .ai/policies/main-branch-ruleset.json
```

To change it later, edit the JSON file in a reviewed PR, then update the
ruleset with `gh api --method PUT repos/OWNER/REPO/rulesets/RULESET_ID
--input ...`. On GitHub's free plan, rulesets are enforced only on public
repositories; a private repository needs a paid plan, which needs the
project manager's approval.

The repository deliberately keeps pull requests and required quality checks,
but does not require an independent approval in single-maintainer mode. The
project manager reviews the agent's PR and merges it from the same account.
Adding a second agent identity later would allow independent code-owner review
without changing the rest of the ruleset.

## Moving to GitHub

`projects/agent-os` remains inside the Magpie vault, while
`astranero/agent-os` is the public GitHub copy. `HANDOFF.md` is a vault-only
operator handoff and must not be published. The public copy is made by
starting from a fresh repository and excluding vault-only/generated files:

```
rsync -a --exclude='__pycache__/' --exclude='HANDOFF.md' \
  --exclude='.DS_Store' projects/agent-os/ /path/to/fresh/agent-os/
```

Commit and push the copy from its fresh repository. The workflow starts on the
push and on every later pull request. Do not copy the vault's `.git`, parent
vault files, or other files outside `projects/agent-os/`.

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

The remaining implementation cards (parallel-workstream documentation,
security analysis, Storybook preview, coordinator, agent factory, and the first
vertical slice) are tracked in the vault board at `.ai/KANBAN.md`. The board
is vault-only; this README documents the public operating rule.
