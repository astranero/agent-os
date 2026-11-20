---
version: 0.1.0
status: accepted
owner: security-reviewer
---

# Security principles

## Layered detection, human escalation

- No single scanner and no language model is the only security control.
  Every pull request runs independent tools: secret scanning, dependency
  scanning, static analysis (CodeQL and Semgrep), and container or
  infrastructure scanning where relevant.
- Tools are expected to miss things. High-risk changes, such as
  authentication, authorization, cryptography, payment, personal data, and
  file handling, always get a human security review in addition to scans.

## Severity policy

| Severity | Effect on merge | Who can waive |
|---|---|---|
| Critical | Blocked; human escalation immediately | Nobody; must be fixed |
| High | Blocked until fixed or waived | Named human approver, with expiry |
| Medium | Reviewer decision required | Reviewer, with recorded reason |
| Low | Tracked; optional fix | Not required |
| Informational | Recorded; not blocking | Not required |

- A finding is never suppressed, dismissed, or downgraded without a recorded
  authorization that names the approver, the reason, and an expiry date.
- No agent may disable, skip, or weaken a security workflow.

## Secure defaults

- Deny by default. Every endpoint and action has an explicit authorization
  rule and a test for the unauthorized case.
- Validate and encode all external input and output at trust boundaries.
- Secrets live in a secret manager or CI secrets, never in code, logs,
  fixtures, screenshots, or review packets.
- Use well-reviewed libraries for cryptography, sessions, and parsing.
- Agents run with least privilege: scoped tokens, no production credentials,
  sandboxed execution, and network egress limited to what the card needs.

## Threat models

- A story that adds or changes a trust boundary includes a threat model in
  `.ai/quality/threat-models/` before it becomes Ready.
- Every identified threat maps to a mitigation and to a test or a scanner
  rule that would detect regression.

## Supply chain

- New dependencies require a licence check and a vulnerability check.
- Dependency updates are separate, small pull requests with their own
  scan results.
