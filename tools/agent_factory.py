"""Generate provider-neutral, least-privilege agent manifests."""

import argparse
import json
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PROJECT_ROOT / ".ai" / "policies" / "role-permissions.yaml"

REQUIRED_TOOLS = {
    "architect": {"read_repository", "write_adr", "write_contracts", "run_contract_validator"},
    "backend-developer": {"read_repository", "implement_feature_code", "run_tests", "run_static_analysis"},
    "frontend-developer": {"read_repository", "implement_feature_code", "run_storybook", "run_accessibility_checks", "run_visual_regression"},
    "test-engineer": {"read_repository", "write_acceptance_scenarios", "run_tests", "run_coverage"},
    "reviewer": {"read_repository", "comment_on_pull_request", "request_changes", "approve_pull_request"},
    "security-reviewer": {"read_repository", "run_static_analysis", "run_dependency_scan", "run_codeql", "run_semgrep", "run_secret_scan", "block_pull_request"},
}

FORBIDDEN_CAPABILITIES = {
    "merge_pull_request",
    "approve_own_pull_request",
    "modify_branch_protection",
    "disable_security_workflows",
    "suppress_security_finding",
    "downgrade_critical_finding",
    "commit_to_paid_service",
}


def create_agent_manifest(role, project, card, output_path):
    policy = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    role_definition = policy.get("roles", {}).get(role)
    if role_definition is None:
        raise ValueError(f"unknown role: {role}")
    if not project.strip() or not card.strip():
        raise ValueError("project and card are required")

    allowed = set(role_definition.get("can", []))
    forbidden = allowed.intersection(FORBIDDEN_CAPABILITIES)
    if forbidden:
        raise ValueError("role has forbidden capabilities: " + ", ".join(sorted(forbidden)))
    required = REQUIRED_TOOLS.get(role, set())
    missing = required.difference(allowed)
    if missing:
        raise ValueError("role is missing required tools: " + ", ".join(sorted(missing)))

    result = {
        "card": card,
        "project": project,
        "required_tools": sorted(required),
        "role": role,
        "version": policy["version"],
    }
    Path(output_path).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main(arguments=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--card", required=True)
    parser.add_argument("--output", required=True)
    options = parser.parse_args(arguments)
    create_agent_manifest(options.role, options.project, options.card, options.output)


if __name__ == "__main__":
    main()
