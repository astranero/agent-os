---
version: 0.2.0
status: accepted
owner: architect
---

# Engineering principles

## Change size and scope

- A card should be implementable in one pull request of roughly 400 changed
  lines or fewer, excluding generated files and lockfiles. Larger work is
  split by the architect before it becomes Ready.
- A pull request changes only what its card names. Unrelated refactoring,
  formatting sweeps, and dependency bumps are separate cards.
- If work reveals the card is wrong or too large, stop, record what was
  learned on the card, and escalate. Do not silently widen the change.

## Readable code

- Identifiers, comments, and maintainer-facing text are in clear, plain
  English unless a domain convention requires otherwise.
- Prefer specific names, small single-purpose units, visible contracts, and
  linear control flow over clever compression.
- Comments explain why: a constraint, trade-off, invariant, or surprising
  edge case. They do not restate the next line. Stale comments are removed
  in the same change that makes them stale.

## Errors and input

- Validate all external input at the boundary where it enters the system.
- Every error is either handled with a defined behavior or propagated with
  context. Swallowed exceptions are review blockers.
- Error responses follow the contract's error schema and never leak stack
  traces, secrets, or internal identifiers.

## Reuse and cost

Do not reinvent the wheel. Before building anything, check what already
exists, and choose the first viable option in this order:

1. **Existing:** code, components, or dependencies already in the project,
   including the standard library.
2. **Open source:** a viable open-source project.
3. **Build:** write it ourselves, only when no viable existing or
   open-source option fits.
4. **Paid:** a commercial product, hosted service, or paid licence, only
   when nothing else is possible, and only with a named human approver.

An option is viable when its licence is compatible with the project, it is
actively maintained, its security record is acceptable, and it meets the
card's need without heavy modification.

Among viable options, choose the cheapest by total cost: licence and usage
fees, hosting, and the ongoing effort to integrate and maintain it. Building
something ourselves is not free; it is chosen over a viable open-source
option only when the card records why.

Every card records the result in its `Reuse and cost` section with
`Decision:` (existing, open-source, build, or paid) and `Alternatives
checked:`. A paid decision also needs `Approved by:`. The card validator
enforces this, and no agent role may commit to a paid service.

## Dependencies

- A new runtime dependency requires the architect's approval on the card and
  a licence check.
- Lockfiles are committed. Version ranges are pinned for applications.

## Documentation

- When behavior, a contract, or an operational procedure changes, the
  matching documentation changes in the same pull request.
- Each repository keeps its real test, lint, and build commands in one
  documented place so agents and CI run the same commands.

## Evidence

- "It works" is not evidence. Evidence is a command, its exit status, and
  the relevant output, captured by CI or attached to the review packet.
