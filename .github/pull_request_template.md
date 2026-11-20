<!-- Generated from .ai/templates/pull-request.md by tools/generate_github_templates.py. Do not edit; change the source and regenerate. -->

<!--
One pull request implements one Ready card. Fill in every section; write
"Not applicable" with a reason where a section does not apply. Merging needs
all required checks, the required reviews, and a human approver.
-->

## Card

Closes #<issue number> — <card title>

## Summary

<What changed, in two or three sentences, from the user's point of view.>

## Scope check

- [ ] The diff only contains what the card's Scope names.
- [ ] Nothing from the card's Non-goals was implemented.
- [ ] No acceptance criteria, contracts, or architecture were changed
      without an ADR or the architect's recorded approval.

## Reuse and cost

Decision: <existing | open-source | build | paid — same as the card>
New dependencies: <name, licence, and why — or "None">

## Traceability

| Acceptance criterion | Test | Result |
|---|---|---|
| <scenario name from the card> | <path/to/test:line> | <Passed> |

## Test evidence

- Failing run before implementation: <command and short output or CI link>
- Passing run after implementation: <command and short output or CI link>

## Security

- Scanners run (CodeQL, Semgrep, secret scan, dependency scan): <results or links>
- Findings and their severity: <list, or "None">
- Waivers: <approver, reason, and expiry — or "None">

## Preview

<Storybook or preview URL and screenshots for UI changes — or "Not
applicable: no UI change".>

## Residual risks

<What could still go wrong, and what follow-up card covers it.>
