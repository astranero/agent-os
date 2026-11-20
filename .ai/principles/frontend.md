---
version: 0.1.0
status: accepted
owner: architect
---

# Frontend principles

## Reuse before creation

- Search the existing component library and design tokens before creating a
  component. The pull request states what was searched and why nothing fit.
- Create a new shared component only when a reusable behavior or visual
  pattern exists. One-off layout stays in the feature.
- Use design tokens for color, spacing, typography, radius, and motion.
  Hard-coded values are review findings.

## Component contract

Every shared component documents its props, events, slots or children,
accessibility role, keyboard behavior, and the states it supports before it
is implemented.

## Required states

A component or screen provides, where applicable: default, loading, empty,
error, disabled, long content, mobile/responsive, permission-limited, and
keyboard navigation. A state that does not apply is listed as "not
applicable" with a reason.

## Storybook and previews

- Each required state has a Storybook story. Stories are the review
  artifact, the visual-regression baseline, and the input for interaction
  and accessibility tests.
- Every frontend pull request includes a preview URL and screenshots or
  recordings of the changed states.
- A human accepts or rejects the preview before the card is Done.

## Accessibility

- Target WCAG 2.2 AA. Automated accessibility checks run on every story and
  block on serious or critical violations.
- All functionality is reachable by keyboard with a visible focus indicator.
- Use semantic HTML first; ARIA only where semantics are insufficient.
- Text and interactive elements meet contrast requirements; motion respects
  `prefers-reduced-motion`.

## Testing

- Interaction tests cover the component's behavior in Storybook.
- Browser tests in Playwright cover user journeys that cross components.
- Visual regression compares changed stories against the accepted baseline;
  intentional changes are approved in the review.
