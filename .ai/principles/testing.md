---
version: 0.1.0
status: accepted
owner: test-engineer
---

# Testing principles

## Test-driven development

For each implementation card:

1. The architect defines behavior and contracts.
2. The test engineer writes or confirms the acceptance scenarios.
3. The developer writes a test and shows it failing for the expected reason.
4. The developer implements the smallest change that makes it pass.
5. The developer refactors while the tests stay green.
6. The test engineer checks coverage of criteria, edge cases, and errors.
7. CI repeats every check independently of the developer's environment.
8. The review packet records the results.

The failing-test run is evidence and is recorded on the pull request.

## Acceptance criteria

- Behavior-level criteria are written as Given/When/Then scenarios.
- Each scenario has at least one Given, exactly one When, and at least one
  Then. Each Then describes an observable result, not an internal call.
- Every story has at least one failure or rejection scenario.
- Every acceptance criterion maps to one or more tests in a traceability
  table on the card:

  | Acceptance criterion | Test | Result |
  |---|---|---|
  | Example: duplicate email is rejected | invite-user.feature:24 | Passed |

- A card cannot move to Review while any criterion lacks a passing test.

## Test quality

- Tests assert observable outcomes: responses, persisted state, rendered
  output, emitted events. Tests that only verify that an internal method was
  called are rejected unless that call is the contract.
- Include boundary values, empty and maximum inputs, invalid input, and
  authorization failures.
- Every bug fix starts with a regression test that reproduces the bug.
- Tests are deterministic: no reliance on wall-clock time, test order,
  shared mutable state, or the public network.

## Levels

| Level | Purpose | Typical tools |
|---|---|---|
| Unit | Business rules in isolation | Project's unit framework |
| Integration | Real database, queue, or adapter | Project's framework plus containers |
| Contract | Implementation matches OpenAPI/JSON Schema | Contract validators |
| Acceptance | Given/When/Then scenarios | Gherkin/Cucumber |
| Browser | User journeys in a real browser | Playwright |
| Component | UI component states and interactions | Storybook interaction tests |

Coverage is reported but is not a target by itself; untested criteria and
untested error paths are what block review. Mutation testing is used where
the test engineer judges that business-rule risk justifies it.
