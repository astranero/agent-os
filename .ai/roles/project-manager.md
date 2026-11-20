---
role: project-manager
version: 0.1.0
status: accepted
actor: human, optionally assisted by an agent
---

# Project manager

## Mission

Decide what is worth building and in which order, and accept work only when
evidence shows it delivers the intended user outcome.

## Responsibilities

- Own product goals, priorities, roadmap, and release goals.
- Write user stories in the form "As a [user], I want [capability], so that
  [value]".
- Make scope decisions and answer decision requests from other roles.
- Give final acceptance of completed cards.
- Approve changes to the constitution and principles.

## Non-responsibilities

- System design, contracts, and technical decomposition (architect).
- Writing implementation code or tests.
- Classifying security findings (security reviewer).

## Approved tools

- GitHub Projects board and issues
- Product brief, user-story, and decision-request templates
- Review packets and Storybook previews (read)

## Forbidden actions

- Approving its own implementation.
- Overriding or silently ignoring a security finding.
- Changing architecture without an ADR.
- Moving a card to Done without recorded evidence.
- Merging through the agent system; merges are a separate human approval.

## Required inputs

- User needs, feedback, and business constraints.
- Decision requests and escalations from other roles.
- Review packets for cards in Review.

## Required outputs

- Product brief and prioritized backlog.
- User stories with user outcome, scope, and non-goals.
- Recorded decisions on cards, with date and reason.
- Acceptance or rejection of completed cards.

## Review checklist

- Does the delivered behavior match the user outcome on the card?
- Is every acceptance criterion backed by passing evidence?
- Did scope stay within the card?
- Are residual risks acceptable and recorded?

## Escalation rules

- The project manager is the final escalation point for product and scope.
- Irreversible or high-risk decisions (security waivers, destructive
  migrations, production releases) are recorded with a named human approver.

## Evidence requirements

- Every acceptance or rejection is recorded on the card with the review
  packet it was based on.
- Every scope or priority change is recorded with a reason.
