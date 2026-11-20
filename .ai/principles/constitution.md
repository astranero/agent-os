---
version: 0.2.0
status: accepted
owner: project-manager
approved_by: Kozheen Taher Esa (project manager)
approved_on: 2026-11-20
---

# Project constitution

This constitution governs every human and agent working in a repository that
uses the agent-led engineering operating system. The `.ai/` directory is the
canonical, provider-neutral source. Provider files such as `AGENTS.md`,
`CLAUDE.md`, and `.github/agents/*.md` are generated from it and must never be
edited by hand.

## Purpose

The system is a controlled development process, not a set of chat personas.
Existing coding agents work inside defined roles, use approved tools, produce
evidence, and cannot bypass quality gates. Humans remain responsible for
product, architecture, security exceptions, and release decisions.

## Core rules

1. **Small, independently reviewable changes.** One card produces one pull
   request that a reviewer can understand in one sitting.
2. **No unrequested scope expansion.** Adjacent ideas go to the Inbox; they do
   not ride along in the current change.
3. **Contracts before implementation.** API, data, and component contracts
   exist and are reviewed before code depends on them.
4. **Tests before implementation.** Every behavior change starts with a test
   that fails for the right reason.
5. **Observable behavior over implementation details.** Acceptance criteria
   and tests describe what a user or caller can observe.
6. **Explicit error handling.** Every failure path is designed, named, and
   tested; nothing fails silently.
7. **Secure defaults.** Deny by default, least privilege, validated input,
   no secrets in code or logs.
8. **Accessibility by default.** User interfaces meet WCAG 2.2 AA unless the
   project manager records a documented exception.
9. **Backward compatibility.** Breaking a published contract requires an ADR,
   a version change, and a migration path.
10. **Reversible decisions where possible.** Prefer feature flags, additive
    migrations, and adapters over one-way changes.
11. **Human approval for irreversible decisions.** Data deletion, destructive
    migrations, production releases, security exceptions, and merges require
    a named human approver.
12. **Evidence before completion.** A card is not Done until its recorded
    evidence (test results, scan results, previews, review approvals) shows
    every acceptance criterion is met.
13. **Reuse first, pay last.** Do not rebuild what already exists. Prefer,
    in order: what the project already has, a viable open-source solution,
    building it ourselves, and a paid product only when nothing else is
    possible. Among viable options, choose the lowest total cost. Every card
    records this decision (see `engineering.md`).

## Decision rights

| Decision | Owner | Requires |
|---|---|---|
| Product goals, priority, scope, final acceptance | Project manager (human) | Recorded decision on the card |
| System boundaries, contracts, dependencies | Architect | ADR for anything non-trivial |
| Security exceptions and waivers | Human approver | Written waiver with expiry |
| Any paid product, service, or licence | Human approver | Recorded cost and the open-source options ruled out |
| Merge to a protected branch | Human approver | All required checks and reviews |
| Changes to this constitution | Project manager (human) | Pull request reviewed like code |

No agent role may merge, approve its own work, modify branch protection,
disable security workflows, suppress a security finding, downgrade a
critical finding, or commit to a paid service. These capabilities are hard-coded as never grantable in
`tools/validate_constitution.py`, so editing the manifest alone cannot grant
them.

## Precedence when principles conflict

When two rules conflict, the higher item wins and the conflict is recorded on
the card or in an ADR:

1. Law, licences, and user safety
2. Security principles (`security.md`)
3. This constitution
4. Accepted architecture decision records
5. Architecture principles (`architecture.md`)
6. Testing principles (`testing.md`)
7. Engineering and frontend principles (`engineering.md`, `frontend.md`)
8. Role profiles (`../roles/*.md`)
9. Card-level instructions

A lower-precedence document may tighten a higher one but never loosen it. If
a conflict cannot be resolved by this order, the agent stops and escalates to
the project manager.

## Escalation

An agent escalates instead of guessing when it meets: ambiguous acceptance
criteria, a needed contract or architecture change, a security finding it
cannot classify, a need for a forbidden capability, a dependency with an
unknown licence, or any irreversible action. Escalation is a comment on the
card or pull request that names the decision needed, the options, and the
recommended option.

## Versioning and approval

Every principle file and role profile carries `version` and `status` front
matter. Status is `proposed`, `accepted`, or `superseded`. Versions follow
MAJOR.MINOR.PATCH: MAJOR for a rule that removes or reverses an obligation,
MINOR for a new obligation, PATCH for wording. Changes land through a pull
request, are validated by `tools/validate_constitution.py`, and move to
`accepted` only when the project manager records `approved_by` and
`approved_on`.

## Change history

| Version | Date | Change | Approved by |
|---|---|---|---|
| 0.1.0 | 2026-11-20 | Initial constitution | Kozheen Taher Esa |
| 0.2.0 | 2026-11-20 | Rule 13: reuse first, open source before building, paid last | Kozheen Taher Esa |
