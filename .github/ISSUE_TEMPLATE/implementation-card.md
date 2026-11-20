---
name: "Implementation card"
about: "One small, test-first change. Must pass tools/validate_card.py before Ready."
title: "<CARD-ID> — <outcome>"
labels: ["card"]
---

<!-- Generated from .ai/templates/implementation-card.md by tools/generate_github_templates.py. Do not edit; change the source and regenerate. -->

# <CARD-ID> — <short outcome-focused title>

<!--
Fill in every section. A card is Ready only when
`python3 tools/validate_card.py <card>.md` exits 0, and can move to Review
only when `python3 tools/validate_card.py --stage review <card>.md` exits 0.
Comments like this one are ignored by the validator.
-->

## User story

As a <type of user>,
I want <capability>,
so that <value>.

## Scope

<What this card changes. One pull request, roughly 400 changed lines or fewer.>

## Non-goals

<Adjacent work that is deliberately excluded; put it in the Inbox instead.>

## Acceptance criteria

<!--
One Gherkin scenario per acceptance criterion. Each scenario needs at least
one Given (its own or from Background), exactly one When, and at least one
Then, in that order. Then steps describe observable results, never internal
calls. Tag at least one rejection or error scenario with @failure.
-->

```gherkin
Feature: <feature name>

  Scenario: <happy-path criterion>
    Given <context>
    When <single action>
    Then <observable result>

  @failure
  Scenario: <failure or rejection criterion>
    Given <context>
    When <single action>
    Then <observable error or unchanged state>
```

## Contract

<API path and OpenAPI file, data schema, or UI component contract this card
implements. Link to `.ai/contracts/`. Say "No contract change" with a reason
if none applies.>

## Test plan

<Which test levels cover which scenarios: unit, integration, contract,
acceptance, browser, component.>

## Security impact

<Trust boundaries touched, authorization rules, input validation, data
sensitivity. Say "None" with a reason if nothing changes.>

## Dependencies

<Cards, contracts, or services this card needs. Say "None" with a reason if
there are none.>

## Reuse and cost

<!--
Order of preference: existing code or dependency in this project, then a
viable open-source project, then building it ourselves, and a paid product
only when nothing else is possible. Viable means a compatible licence,
active maintenance, an acceptable security record, and a fit for the need.
Compare total cost: licence fees, hosting, and the effort to maintain it.
Decision must be one of: existing, open-source, build, paid.
-->

Decision: <existing | open-source | build | paid>
Alternatives checked: <what already exists here, which open-source projects
were considered and why they fit or not, and the expected cost>
Approved by: <only for paid: the human who approved the cost>

## Verification commands

```
<exact commands that run the tests for this card>
```

## Traceability

<!-- Result is Pending while Ready; every row must be Passed before Review. -->

| Acceptance criterion | Test | Result |
|---|---|---|
| <happy-path criterion> | <path/to/test:line> | Pending |
| <failure or rejection criterion> | <path/to/test:line> | Pending |
