"""Behavior tests for the constitution and role-capability validator.

Each test builds a small, valid control tree in a temporary directory, breaks
exactly one rule, and checks that the validator reports that rule. The final
test runs the validator against the real `.ai/` tree in this project.
"""

import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

import validate_constitution as validator  # noqa: E402


def role_profile_text(role_name, omit_section=None):
    sections = [
        section
        for section in validator.REQUIRED_ROLE_SECTIONS
        if section != omit_section
    ]
    body = "\n\n".join(f"## {section}\n\nText." for section in sections)
    return f"---\nrole: {role_name}\nversion: 0.1.0\nstatus: proposed\n---\n\n# {role_name}\n\n{body}\n"


def principle_text(version="0.1.0", status="proposed"):
    front_matter = []
    if version is not None:
        front_matter.append(f"version: {version}")
    if status is not None:
        front_matter.append(f"status: {status}")
    joined = "\n".join(front_matter)
    return f"---\n{joined}\n---\n\n# Principles\n\nText.\n"


def valid_manifest():
    never_grantable = sorted(validator.NEVER_GRANTABLE_CAPABILITIES)
    capabilities = {name: "Never granted to any role." for name in never_grantable}
    capabilities.update(
        {
            "read_repository": "Read repository contents.",
            "run_tests": "Run the test suites.",
        }
    )
    return {
        "version": "0.1.0",
        "status": "proposed",
        "capabilities": capabilities,
        "roles": {
            "architect": {
                "profile": "roles/architect.md",
                "can": ["read_repository"],
                "cannot": list(never_grantable),
                "escalates_to": ["human"],
            },
            "backend-developer": {
                "profile": "roles/backend-developer.md",
                "can": ["read_repository", "run_tests"],
                "cannot": list(never_grantable),
                "escalates_to": ["architect", "human"],
            },
        },
    }


class ControlTree:
    """A temporary `.ai/` directory that a test can mutate before validating."""

    def __init__(self, directory):
        self.ai_root = Path(directory) / ".ai"
        (self.ai_root / "principles").mkdir(parents=True)
        (self.ai_root / "roles").mkdir()
        (self.ai_root / "policies").mkdir()
        for principle_name in validator.REQUIRED_PRINCIPLE_FILES:
            self.write(f"principles/{principle_name}", principle_text())
        self.manifest = valid_manifest()
        for role_name, role in self.manifest["roles"].items():
            self.write(role["profile"], role_profile_text(role_name))

    def write(self, relative_path, text):
        path = self.ai_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def validate(self):
        # JSON is a subset of YAML, so the manifest loader reads this file.
        self.write("policies/role-permissions.yaml", json.dumps(self.manifest))
        return validator.validate_control_tree(self.ai_root)


class ValidatorBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.tree = ControlTree(self.temporary_directory.name)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def assertReports(self, errors, expected_fragment):
        matching = [error for error in errors if expected_fragment in error]
        self.assertTrue(
            matching,
            f"expected an error containing {expected_fragment!r}, got {errors!r}",
        )

    def test_valid_tree_has_no_errors(self):
        self.assertEqual(self.tree.validate(), [])

    def test_unknown_capability_is_rejected(self):
        self.tree.manifest["roles"]["architect"]["can"].append("teleport")
        self.assertReports(self.tree.validate(), "unknown capability 'teleport'")

    def test_capability_in_both_can_and_cannot_is_rejected(self):
        self.tree.manifest["roles"]["architect"]["cannot"].append("read_repository")
        self.assertReports(self.tree.validate(), "both can and cannot")

    def test_no_role_may_hold_a_never_grantable_capability(self):
        for capability in sorted(validator.NEVER_GRANTABLE_CAPABILITIES):
            with self.subTest(capability=capability):
                manifest = valid_manifest()
                role = manifest["roles"]["backend-developer"]
                role["cannot"].remove(capability)
                role["can"].append(capability)
                self.tree.manifest = manifest
                self.assertReports(
                    self.tree.validate(), f"must never be granted '{capability}'"
                )

    def test_never_grantable_capability_must_be_denied_explicitly(self):
        self.tree.manifest["roles"]["architect"]["cannot"].remove(
            "merge_pull_request"
        )
        self.assertReports(
            self.tree.validate(), "must explicitly deny 'merge_pull_request'"
        )

    def test_missing_required_role_field_is_rejected(self):
        del self.tree.manifest["roles"]["architect"]["escalates_to"]
        self.assertReports(self.tree.validate(), "missing field 'escalates_to'")

    def test_escalation_to_unknown_role_is_rejected(self):
        self.tree.manifest["roles"]["architect"]["escalates_to"] = ["oracle"]
        self.assertReports(self.tree.validate(), "escalates to unknown role 'oracle'")

    def test_role_profile_missing_a_required_section_is_rejected(self):
        self.tree.write(
            "roles/architect.md",
            role_profile_text("architect", omit_section="Escalation rules"),
        )
        self.assertReports(self.tree.validate(), "missing section 'Escalation rules'")

    def test_manifest_role_without_profile_file_is_rejected(self):
        (self.tree.ai_root / "roles" / "architect.md").unlink()
        self.assertReports(self.tree.validate(), "profile file not found")

    def test_profile_file_without_manifest_entry_is_rejected(self):
        self.tree.write("roles/release-manager.md", role_profile_text("release-manager"))
        self.assertReports(
            self.tree.validate(), "release-manager.md has no entry in role-permissions"
        )

    def test_principle_without_version_is_rejected(self):
        self.tree.write("principles/security.md", principle_text(version=None))
        self.assertReports(self.tree.validate(), "security.md: missing 'version'")

    def test_principle_with_unknown_status_is_rejected(self):
        self.tree.write("principles/testing.md", principle_text(status="maybe"))
        self.assertReports(self.tree.validate(), "testing.md: status 'maybe'")

    def test_missing_principle_file_is_rejected(self):
        (self.tree.ai_root / "principles" / "frontend.md").unlink()
        self.assertReports(self.tree.validate(), "principles/frontend.md is missing")

    def test_manifest_version_must_be_semantic(self):
        self.tree.manifest["version"] = "first"
        self.assertReports(self.tree.validate(), "version 'first'")


class PaidServiceRuleTests(unittest.TestCase):
    def test_committing_to_a_paid_service_is_never_grantable(self):
        self.assertIn("commit_to_paid_service", validator.NEVER_GRANTABLE_CAPABILITIES)


class PublishedSchemaAgreementTests(unittest.TestCase):
    """The JSON Schema is the published contract; the validator must match it."""

    def setUp(self):
        schema_path = PROJECT_ROOT / ".ai" / "policies" / "role-capability.schema.json"
        self.schema = json.loads(schema_path.read_text(encoding="utf-8"))

    def test_schema_requires_the_same_role_fields_as_the_validator(self):
        role_schema = self.schema["$defs"]["role"]
        self.assertEqual(
            sorted(role_schema["required"]), sorted(validator.REQUIRED_ROLE_FIELDS)
        )

    def test_schema_status_values_match_the_validator(self):
        self.assertEqual(
            sorted(self.schema["properties"]["status"]["enum"]),
            sorted(validator.ALLOWED_STATUSES),
        )


class RealControlTreeTests(unittest.TestCase):
    def test_project_control_tree_is_valid(self):
        errors = validator.validate_control_tree(PROJECT_ROOT / ".ai")
        self.assertEqual(errors, [], "\n" + textwrap.indent("\n".join(errors), "  "))


if __name__ == "__main__":
    unittest.main()
