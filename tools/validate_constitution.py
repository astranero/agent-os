#!/usr/bin/env python3
"""Validate the engineering constitution and role capability manifest.

Checks the `.ai/` control tree:

* every required principle file exists and declares a version and status;
* every role profile contains the required sections;
* the capability manifest only uses known capabilities, never grants a
  capability that no agent role may hold, and denies those explicitly;
* role profiles and manifest entries correspond one to one.

Usage:
    python3 tools/validate_constitution.py [path/to/.ai]

Exit code 0 means valid; 1 means errors were printed; 2 means bad usage.
"""

import re
import sys
from pathlib import Path

import yaml

REQUIRED_PRINCIPLE_FILES = (
    "constitution.md",
    "engineering.md",
    "architecture.md",
    "security.md",
    "testing.md",
    "frontend.md",
)

REQUIRED_ROLE_SECTIONS = (
    "Mission",
    "Responsibilities",
    "Non-responsibilities",
    "Approved tools",
    "Forbidden actions",
    "Required inputs",
    "Required outputs",
    "Review checklist",
    "Escalation rules",
    "Evidence requirements",
)

REQUIRED_ROLE_FIELDS = ("profile", "can", "cannot", "escalates_to")

ALLOWED_STATUSES = ("proposed", "accepted", "superseded")

# These stay in code rather than in the manifest so that editing the manifest
# alone can never grant them. Merging, exceptions, and spending money are
# human decisions.
NEVER_GRANTABLE_CAPABILITIES = frozenset(
    {
        "merge_pull_request",
        "approve_own_pull_request",
        "modify_branch_protection",
        "disable_security_workflows",
        "suppress_security_finding",
        "downgrade_critical_finding",
        "commit_to_paid_service",
    }
)

HUMAN_ESCALATION_TARGET = "human"
MANIFEST_RELATIVE_PATH = Path("policies") / "role-permissions.yaml"
SEMANTIC_VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
FRONT_MATTER_PATTERN = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
SECTION_HEADING_PATTERN = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)


def validate_control_tree(ai_root):
    """Return a list of human-readable errors; an empty list means valid."""
    ai_root = Path(ai_root)
    errors = []
    errors.extend(validate_principles(ai_root / "principles"))

    manifest, manifest_errors = load_manifest(ai_root / MANIFEST_RELATIVE_PATH)
    errors.extend(manifest_errors)
    if manifest is None:
        return errors

    errors.extend(validate_manifest(manifest, ai_root))
    errors.extend(find_profiles_without_manifest_entry(manifest, ai_root / "roles"))
    return errors


def validate_principles(principles_directory):
    errors = []
    for file_name in REQUIRED_PRINCIPLE_FILES:
        path = principles_directory / file_name
        if not path.is_file():
            errors.append(f"principles/{file_name} is missing")
            continue
        front_matter = read_front_matter(path)
        errors.extend(validate_version_and_status(file_name, front_matter))
    return errors


def validate_version_and_status(label, fields):
    errors = []
    version = fields.get("version")
    status = fields.get("status")
    if version is None:
        errors.append(f"{label}: missing 'version'")
    elif not SEMANTIC_VERSION_PATTERN.match(str(version)):
        errors.append(f"{label}: version '{version}' is not MAJOR.MINOR.PATCH")
    if status is None:
        errors.append(f"{label}: missing 'status'")
    elif status not in ALLOWED_STATUSES:
        errors.append(
            f"{label}: status '{status}' is not one of {', '.join(ALLOWED_STATUSES)}"
        )
    return errors


def read_front_matter(path):
    """Read simple `key: value` front matter; nested YAML is not expected."""
    match = FRONT_MATTER_PATTERN.match(path.read_text(encoding="utf-8"))
    if not match:
        return {}
    parsed = yaml.safe_load(match.group(1))
    return parsed if isinstance(parsed, dict) else {}


def load_manifest(manifest_path):
    if not manifest_path.is_file():
        return None, [f"{MANIFEST_RELATIVE_PATH} is missing"]
    try:
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as parse_error:
        return None, [f"{MANIFEST_RELATIVE_PATH}: cannot parse YAML: {parse_error}"]
    if not isinstance(manifest, dict):
        return None, [f"{MANIFEST_RELATIVE_PATH}: top level must be a mapping"]
    return manifest, []


def validate_manifest(manifest, ai_root):
    label = str(MANIFEST_RELATIVE_PATH)
    errors = validate_version_and_status(label, manifest)

    capabilities = manifest.get("capabilities")
    roles = manifest.get("roles")
    if not isinstance(capabilities, dict) or not capabilities:
        errors.append(f"{label}: 'capabilities' must be a non-empty mapping")
        capabilities = {}
    if not isinstance(roles, dict) or not roles:
        errors.append(f"{label}: 'roles' must be a non-empty mapping")
        return errors

    missing_never_grantable = NEVER_GRANTABLE_CAPABILITIES - set(capabilities)
    for capability in sorted(missing_never_grantable):
        errors.append(
            f"{label}: never-grantable capability '{capability}' must be defined "
            "in 'capabilities' so roles can deny it"
        )

    known_capabilities = set(capabilities)
    escalation_targets = set(roles) | {HUMAN_ESCALATION_TARGET}
    for role_name, role in roles.items():
        errors.extend(
            validate_role(role_name, role, known_capabilities, escalation_targets, ai_root)
        )
    return errors


def validate_role(role_name, role, known_capabilities, escalation_targets, ai_root):
    prefix = f"role '{role_name}'"
    if not isinstance(role, dict):
        return [f"{prefix}: must be a mapping"]

    errors = [
        f"{prefix}: missing field '{field}'"
        for field in REQUIRED_ROLE_FIELDS
        if field not in role
    ]
    granted = set(role.get("can") or [])
    denied = set(role.get("cannot") or [])

    for capability in sorted((granted | denied) - known_capabilities):
        errors.append(f"{prefix}: unknown capability '{capability}'")
    for capability in sorted(granted & denied):
        errors.append(f"{prefix}: '{capability}' is in both can and cannot")
    for capability in sorted(granted & NEVER_GRANTABLE_CAPABILITIES):
        errors.append(f"{prefix}: must never be granted '{capability}'")
    for capability in sorted(NEVER_GRANTABLE_CAPABILITIES - denied - granted):
        errors.append(f"{prefix}: must explicitly deny '{capability}'")

    for target in role.get("escalates_to") or []:
        if target not in escalation_targets:
            errors.append(f"{prefix}: escalates to unknown role '{target}'")

    profile = role.get("profile")
    if profile:
        errors.extend(validate_role_profile(prefix, ai_root / profile))
    return errors


def validate_role_profile(prefix, profile_path):
    if not profile_path.is_file():
        return [f"{prefix}: profile file not found: {profile_path.name}"]
    text = profile_path.read_text(encoding="utf-8")
    present_sections = set(SECTION_HEADING_PATTERN.findall(text))
    errors = [
        f"{prefix}: {profile_path.name} missing section '{section}'"
        for section in REQUIRED_ROLE_SECTIONS
        if section not in present_sections
    ]
    errors.extend(
        validate_version_and_status(profile_path.name, read_front_matter(profile_path))
    )
    return errors


def find_profiles_without_manifest_entry(manifest, roles_directory):
    if not roles_directory.is_dir():
        return ["roles/ directory is missing"]
    referenced = {
        Path(role.get("profile", "")).name
        for role in (manifest.get("roles") or {}).values()
        if isinstance(role, dict)
    }
    return [
        f"roles/{path.name} has no entry in role-permissions.yaml"
        for path in sorted(roles_directory.glob("*.md"))
        if path.name not in referenced
    ]


def main(arguments):
    if len(arguments) > 1:
        print(__doc__, file=sys.stderr)
        return 2
    default_root = Path(__file__).resolve().parents[1] / ".ai"
    ai_root = Path(arguments[0]) if arguments else default_root
    errors = validate_control_tree(ai_root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"\n{len(errors)} error(s) in {ai_root}")
        return 1
    print(f"OK: constitution and role capabilities are valid ({ai_root})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
