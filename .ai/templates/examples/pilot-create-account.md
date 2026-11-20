# PILOT-01 — A visitor creates an account and sees a welcome screen

## User story

As a first-time visitor,
I want to create an account with my email address and a password,
so that I can start using the product right away.

## Scope

Add the sign-up endpoint, the sign-up form, and the welcome screen shown
after a successful sign-up. Passwords are stored as salted hashes.

## Non-goals

Email verification, social login, password reset, and profile editing.

## Acceptance criteria

```gherkin
Feature: Account creation

  Background:
    Given I am not signed in

  Scenario: A visitor creates an account with valid details
    Given the email address "ada@example.com" is not registered
    When I submit the sign-up form with that email and a valid password
    Then I see a welcome screen that greets me by email
    And I am signed in

  @failure
  Scenario: A visitor cannot reuse a registered email address
    Given the email address "ada@example.com" is already registered
    When I submit the sign-up form with that email and a valid password
    Then I see the message "An account with this email already exists"
    And no second account is created

  @failure
  Scenario: A visitor cannot use a password that is too short
    When I submit the sign-up form with a password of 7 characters
    Then I see the message "Use at least 12 characters"
    And no account is created
```

## Contract

`POST /accounts` in `.ai/contracts/openapi/accounts.yaml`; responses 201,
409 (email taken), and 422 (validation error). UI: `SignUpForm` and
`WelcomeScreen` component contracts in `docs/components/`.

## Test plan

Acceptance scenarios run in Cucumber against the API. Unit tests cover
password-length validation and hashing. A Playwright test covers the full
browser journey. Storybook stories cover the form's default, error,
disabled, and loading states.

## Security impact

Adds an unauthenticated endpoint that creates accounts: rate limiting,
password hashing with a vetted library, no password in logs, and a
generic-enough error for existing emails are required. Threat model:
`.ai/quality/threat-models/account-creation.md`.

## Dependencies

Needs the accounts table migration from the architect's ADR for user
storage; no other card blocks this one.

## Reuse and cost

Decision: open-source
Alternatives checked: the project has no password hashing yet. The
open-source `argon2` library (MIT) is mature and maintained, so we do not
write our own hashing. Hosted identity services were not chosen because
they add a monthly cost and the open-source option fits the need. Cost: no
licence fee; only routine dependency updates.

## Verification commands

```
npm test -- accounts
npx cucumber-js features/account-creation.feature
npx playwright test sign-up.spec.ts
```

## Traceability

| Acceptance criterion | Test | Result |
|---|---|---|
| A visitor creates an account with valid details | features/account-creation.feature:7 | Pending |
| A visitor creates an account with valid details | e2e/sign-up.spec.ts:10 | Pending |
| A visitor cannot reuse a registered email address | features/account-creation.feature:14 | Pending |
| A visitor cannot use a password that is too short | features/account-creation.feature:21 | Pending |
| A visitor cannot use a password that is too short | src/accounts/password-policy.test.ts:5 | Pending |
