#!/usr/bin/env python3
"""Check the repository rules that protect `main` before they reach GitHub.

Checks, all offline:

* `.ai/policies/main-branch-ruleset.json` (a GitHub repository ruleset)
  targets only `main`, has no bypass actors, blocks force pushes and
  deletion, requires pull requests without requiring an independent approval,
  and requires exactly the job names in the quality-gates workflow as status
  checks from GitHub Actions;
* `.github/CODEOWNERS` gives `.ai/`, `tools/`, and `.github/` a real owner
  and has no ownerless line;
* `.github/dependabot.yml` updates GitHub Actions and pip dependencies.

Usage:
    python3 tools/validate_repository_rules.py [--root DIR]

Exit code 0 means valid; 1 means problems were printed.
"""

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

DEFAULT_ROOT = Path(__file__).resolve().parents[1]

RULESET_PATH = ".ai/policies/main-branch-ruleset.json"
CODEOWNERS_PATH = ".github/CODEOWNERS"
DEPENDABOT_PATH = ".github/dependabot.yml"
WORKFLOW_PATH = ".github/workflows/quality-gates.yml"

PROTECTED_BRANCH_REF = "refs/heads/main"

# GitHub's app ID for GitHub Actions. Pinning required checks to it stops
# another app or a personal token from posting a fake passing status with
# the same name.
GITHUB_ACTIONS_APP_ID = 15368

REQUIRED_RULE_TYPES = ("deletion", "non_fast_forward", "pull_request", "required_status_checks")

REQUIRED_REVIEW_SETTINGS = {
    "require_code_owner_review": False,
    "dismiss_stale_reviews_on_push": True,
    "require_last_push_approval": False,
}

CODE_OWNED_PATHS = ("/.ai/", "/tools/", "/.github/")

GITHUB_OWNER_PATTERN = re.compile(r"^@[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?(?:/[A-Za-z0-9_.-]+)?$")
PLACEHOLDER_OWNERS = {"@username", "@user", "@owner", "@todo", "@tbd", "@yourname", "@your-name", "@example"}

REQUIRED_DEPENDABOT_ECOSYSTEMS = ("github-actions", "pip")


# ---------------------------------------------------------------- ruleset


def rules_by_type(ruleset):
    return {rule.get("type"): rule for rule in ruleset.get("rules", [])}


def required_check_names(ruleset):
    checks = rules_by_type(ruleset).get("required_status_checks", {})
    entries = checks.get("parameters", {}).get("required_status_checks", [])
    return {entry.get("context") for entry in entries}


def find_ruleset_problems(ruleset, workflow_job_names):
    problems = []

    if ruleset.get("target") != "branch":
        problems.append("ruleset: target must be 'branch'")
    if ruleset.get("enforcement") != "active":
        problems.append("ruleset: enforcement must be 'active'")
    if ruleset.get("bypass_actors"):
        problems.append("ruleset: bypass_actors must be empty; nobody may bypass the gates")

    included_refs = ruleset.get("conditions", {}).get("ref_name", {}).get("include")
    if included_refs != [PROTECTED_BRANCH_REF]:
        problems.append(f"ruleset: conditions.ref_name.include must be ['{PROTECTED_BRANCH_REF}']")

    rules = rules_by_type(ruleset)
    for rule_type in REQUIRED_RULE_TYPES:
        if rule_type not in rules:
            problems.append(f"ruleset: missing rule '{rule_type}'")

    problems.extend(find_review_problems(rules.get("pull_request")))
    problems.extend(find_status_check_problems(rules.get("required_status_checks"), workflow_job_names))
    return problems


def find_review_problems(pull_request_rule):
    if pull_request_rule is None:
        return []
    parameters = pull_request_rule.get("parameters", {})
    problems = []
    if parameters.get("required_approving_review_count") != 0:
        problems.append("ruleset: required_approving_review_count must be 0 in single-maintainer mode")
    for setting, required_value in REQUIRED_REVIEW_SETTINGS.items():
        if parameters.get(setting) is not required_value:
            problems.append(f"ruleset: {setting} must be {str(required_value).lower()}")
    return problems


def find_status_check_problems(status_check_rule, workflow_job_names):
    if status_check_rule is None:
        return []
    parameters = status_check_rule.get("parameters", {})
    problems = []

    if parameters.get("strict_required_status_checks_policy") is not True:
        problems.append(
            "ruleset: strict_required_status_checks_policy must be true "
            "(checks must pass on a branch that is up to date with main)"
        )

    for entry in parameters.get("required_status_checks", []):
        if entry.get("integration_id") != GITHUB_ACTIONS_APP_ID:
            problems.append(
                f"ruleset: required check '{entry.get('context')}' must have "
                f"integration_id {GITHUB_ACTIONS_APP_ID} (GitHub Actions)"
            )

    required_names = {
        entry.get("context") for entry in parameters.get("required_status_checks", [])
    }
    for job_name in sorted(workflow_job_names - required_names):
        problems.append(f"ruleset: workflow job '{job_name}' is not a required check")
    for check_name in sorted(required_names - workflow_job_names):
        problems.append(
            f"ruleset: required check '{check_name}' matches no job in {WORKFLOW_PATH} "
            "(a renamed job would block every merge)"
        )
    return problems


def workflow_job_names(root):
    workflow = yaml.safe_load((Path(root) / WORKFLOW_PATH).read_text(encoding="utf-8"))
    # GitHub reports a job's check under its `name`, or its key if unnamed.
    return {job.get("name", key) for key, job in workflow["jobs"].items()}


# ------------------------------------------------------------- CODEOWNERS


def parse_codeowners(text):
    """Return [(pattern, [owners])] for every non-comment line."""
    entries = []
    for line in text.splitlines():
        content = line.split("#", 1)[0].strip()
        if content:
            pattern, *owners = content.split()
            entries.append((pattern, owners))
    return entries


def is_real_owner(owner):
    return bool(GITHUB_OWNER_PATTERN.match(owner)) and owner.lower() not in PLACEHOLDER_OWNERS


def find_codeowners_problems(text):
    entries = parse_codeowners(text)
    problems = []

    for pattern, owners in entries:
        if not owners:
            problems.append(f"CODEOWNERS: '{pattern}' has no owner, which removes review for it")
        for owner in owners:
            if not is_real_owner(owner):
                problems.append(f"CODEOWNERS: '{pattern}' has placeholder or invalid owner '{owner}'")

    owned_patterns = {pattern for pattern, owners in entries if owners}
    for path in CODE_OWNED_PATHS:
        if path not in owned_patterns:
            problems.append(f"CODEOWNERS: '{path}' must have an owner")
    return problems


# ------------------------------------------------------------- Dependabot


def find_dependabot_problems(config):
    problems = []
    if config.get("version") != 2:
        problems.append("dependabot.yml: version must be 2")

    watched = {
        update.get("package-ecosystem")
        for update in config.get("updates", [])
        if update.get("schedule", {}).get("interval")
    }
    for ecosystem in REQUIRED_DEPENDABOT_ECOSYSTEMS:
        if ecosystem not in watched:
            problems.append(f"dependabot.yml: must update '{ecosystem}' on a schedule")
    return problems


# -------------------------------------------------------------- whole tree


def read_required_file(root, relative_path, problems):
    path = Path(root) / relative_path
    if not path.is_file():
        problems.append(f"missing file: {relative_path}")
        return None
    return path.read_text(encoding="utf-8")


def validate_repository(root):
    problems = []
    ruleset_text = read_required_file(root, RULESET_PATH, problems)
    codeowners_text = read_required_file(root, CODEOWNERS_PATH, problems)
    dependabot_text = read_required_file(root, DEPENDABOT_PATH, problems)
    workflow_text = read_required_file(root, WORKFLOW_PATH, problems)

    if ruleset_text is not None and workflow_text is not None:
        problems.extend(find_ruleset_problems(json.loads(ruleset_text), workflow_job_names(root)))
    if codeowners_text is not None:
        problems.extend(find_codeowners_problems(codeowners_text))
    if dependabot_text is not None:
        problems.extend(find_dependabot_problems(yaml.safe_load(dependabot_text) or {}))
    return problems


def main(arguments):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    options = parser.parse_args(arguments)

    problems = validate_repository(options.root)
    for problem in problems:
        print(f"ERROR: {problem}")
    if not problems:
        print("OK: main-branch ruleset, CODEOWNERS, and Dependabot are valid")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
