# Security analysis

Agent OS uses layered automated checks on pull requests and `main`:

- CodeQL analyzes Python source and uploads findings to GitHub code scanning.
- Dependency Review fails a pull request when a changed dependency introduces
  a vulnerability rated high or critical.
- The existing repository checks continue to validate permissions, templates,
  rules, and tests.

These tools are detection layers, not proof that the project is secure. They
do not replace human review for authentication, authorization, cryptography,
payments, personal data, file handling, or other trust-boundary changes. They
also cover only the languages and dependency manifests that GitHub can parse;
runtime configuration, design flaws, unsupported ecosystems, and unknown
vulnerabilities can remain undetected.

Critical findings are never waived or downgraded by an agent. High findings
require a named human decision with a reason and expiry before merge. The
workflow has no finding-suppression step and uses least-privilege permissions.
