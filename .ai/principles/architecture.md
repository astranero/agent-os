---
version: 0.2.0
status: accepted
owner: architect
---

# Architecture principles

## Decisions are recorded

- Any change to system boundaries, a published contract, the data model, a
  runtime dependency, or a cross-cutting pattern requires an architecture
  decision record in `.ai/architecture/adr/`.
- An ADR states context, decision, alternatives considered, consequences,
  and how the decision can be reversed. Status is `proposed`, `accepted`,
  `superseded`, or `rejected`.
- Superseded ADRs are kept and link to their replacement.
- An ADR that introduces a component, library, or service lists the existing
  and open-source alternatives considered and the total cost of each, and
  follows the order of preference in `engineering.md` (existing,
  open source, build, paid).

## Contracts first

- HTTP APIs are described in OpenAPI under `.ai/contracts/openapi/`; data
  shapes in JSON Schema under `.ai/contracts/schemas/`.
- A contract is reviewed and merged before or together with the first code
  that implements it, never after.
- Contract changes are classified as additive, deprecating, or breaking.
  Breaking changes need an ADR, a new version, and a migration plan.

## Boundaries

- Each module has one clear responsibility and a documented public surface.
  Callers depend on that surface, not on internals.
- Trust boundaries (user input, network, third-party services, file uploads,
  inter-service calls) are named in the design and in the threat model.
- Business rules live in code that can be tested without network, database,
  or UI.

## Non-functional requirements

- Every story that touches performance, availability, privacy, or cost names
  a measurable target on the card, or states explicitly that none applies.
- Data migrations are additive first (expand, migrate, contract) so that
  each step can be rolled back.

## Change control

- The architect does not change acceptance criteria after a card enters In
  Progress. If the criteria are wrong, the card returns to Ready with a
  recorded reason.
- Developer agents may not change architecture. They escalate with a short
  proposal and wait for an ADR.
