"""Behavior tests for the main-branch ruleset, CODEOWNERS, and Dependabot checks."""

import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

import validate_repository_rules as rules  # noqa: E402

CHECK_SCRIPT = PROJECT_ROOT / "tools" / "validate_repository_rules.py"

WORKFLOW_JOB_NAMES = {"Tests, constitution, and template drift", "Pull request and linked card"}

VALID_RULESET = {
    "name": "Protect main",
    "target": "branch",
    "enforcement": "active",
    "bypass_actors": [],
    "conditions": {"ref_name": {"include": ["refs/heads/main"], "exclude": []}},
    "rules": [
        {"type": "deletion"},
        {"type": "non_fast_forward"},
        {
            "type": "pull_request",
            "parameters": {
                "required_approving_review_count": 1,
                "require_code_owner_review": True,
                "dismiss_stale_reviews_on_push": True,
                "require_last_push_approval": True,
                "required_review_thread_resolution": True,
            },
        },
        {
            "type": "required_status_checks",
            "parameters": {
                "strict_required_status_checks_policy": True,
                "required_status_checks": [
                    {"context": "Tests, constitution, and template drift", "integration_id": 15368},
                    {"context": "Pull request and linked card", "integration_id": 15368},
                ],
            },
        },
    ],
}

VALID_CODEOWNERS = """\
# Changes to the control tree need the project manager's review.
/.ai/ @astranero
/tools/ @astranero
/.github/ @astranero
"""

VALID_DEPENDABOT = {
    "version": 2,
    "updates": [
        {"package-ecosystem": "github-actions", "directory": "/", "schedule": {"interval": "weekly"}},
        {"package-ecosystem": "pip", "directory": "/", "schedule": {"interval": "weekly"}},
    ],
}


def ruleset_with(change):
    ruleset = copy.deepcopy(VALID_RULESET)
    change(ruleset)
    return ruleset


def rule_of_type(ruleset, rule_type):
    return next(rule for rule in ruleset["rules"] if rule["type"] == rule_type)


class RulesetTests(unittest.TestCase):
    def problems(self, ruleset):
        return rules.find_ruleset_problems(ruleset, WORKFLOW_JOB_NAMES)

    def test_valid_ruleset_has_no_problems(self):
        self.assertEqual(self.problems(VALID_RULESET), [])

    def test_ruleset_must_target_main_only(self):
        ruleset = ruleset_with(
            lambda r: r["conditions"]["ref_name"].update(include=["refs/heads/develop"])
        )
        self.assertIn("refs/heads/main", "\n".join(self.problems(ruleset)))

    def test_ruleset_must_be_active(self):
        ruleset = ruleset_with(lambda r: r.update(enforcement="evaluate"))
        self.assertIn("enforcement", "\n".join(self.problems(ruleset)))

    def test_any_bypass_actor_fails(self):
        ruleset = ruleset_with(
            lambda r: r.update(bypass_actors=[{"actor_id": 5, "actor_type": "RepositoryRole"}])
        )
        self.assertIn("bypass", "\n".join(self.problems(ruleset)))

    def test_missing_force_push_or_deletion_block_fails(self):
        for rule_type in ("deletion", "non_fast_forward"):
            with self.subTest(rule_type=rule_type):
                ruleset = ruleset_with(
                    lambda r: r.update(rules=[x for x in r["rules"] if x["type"] != rule_type])
                )
                self.assertIn(rule_type, "\n".join(self.problems(ruleset)))

    def test_weakened_review_rule_fails(self):
        weakenings = {
            "required_approving_review_count": 0,
            "require_code_owner_review": False,
            "dismiss_stale_reviews_on_push": False,
            "require_last_push_approval": False,
        }
        for parameter, weak_value in weakenings.items():
            with self.subTest(parameter=parameter):
                ruleset = ruleset_with(
                    lambda r: rule_of_type(r, "pull_request")["parameters"].update(
                        {parameter: weak_value}
                    )
                )
                self.assertIn(parameter, "\n".join(self.problems(ruleset)))

    def test_renamed_workflow_job_without_ruleset_update_fails(self):
        renamed_jobs = {"Unit tests only", "Pull request and linked card"}
        problems = rules.find_ruleset_problems(VALID_RULESET, renamed_jobs)
        joined = "\n".join(problems)
        self.assertIn("Unit tests only", joined)
        self.assertIn("Tests, constitution, and template drift", joined)

    def test_required_check_from_another_app_fails(self):
        def use_other_app(ruleset):
            checks = rule_of_type(ruleset, "required_status_checks")["parameters"]
            checks["required_status_checks"][0]["integration_id"] = 999

        self.assertIn("integration_id", "\n".join(self.problems(ruleset_with(use_other_app))))

    def test_checks_must_run_against_an_up_to_date_branch(self):
        def make_loose(ruleset):
            rule_of_type(ruleset, "required_status_checks")["parameters"][
                "strict_required_status_checks_policy"
            ] = False

        self.assertIn("strict", "\n".join(self.problems(ruleset_with(make_loose))))


class CodeownersTests(unittest.TestCase):
    def test_valid_codeowners_has_no_problems(self):
        self.assertEqual(rules.find_codeowners_problems(VALID_CODEOWNERS), [])

    def test_missing_protected_path_fails(self):
        text = VALID_CODEOWNERS.replace("/tools/ @astranero\n", "")
        self.assertIn("/tools/", "\n".join(rules.find_codeowners_problems(text)))

    def test_placeholder_owner_fails(self):
        for placeholder in ("@username", "<owner>", "@TODO"):
            with self.subTest(placeholder=placeholder):
                text = VALID_CODEOWNERS.replace("/.ai/ @astranero", f"/.ai/ {placeholder}")
                self.assertIn("/.ai/", "\n".join(rules.find_codeowners_problems(text)))

    def test_later_line_without_owner_fails(self):
        # In CODEOWNERS the last matching line wins, so an ownerless line
        # silently removes review for the files it matches.
        text = VALID_CODEOWNERS + "/tools/validate_card.py\n"
        self.assertIn("validate_card.py", "\n".join(rules.find_codeowners_problems(text)))


class DependabotTests(unittest.TestCase):
    def test_valid_dependabot_has_no_problems(self):
        self.assertEqual(rules.find_dependabot_problems(VALID_DEPENDABOT), [])

    def test_missing_ecosystem_fails(self):
        for ecosystem in ("github-actions", "pip"):
            with self.subTest(ecosystem=ecosystem):
                config = copy.deepcopy(VALID_DEPENDABOT)
                config["updates"] = [
                    u for u in config["updates"] if u["package-ecosystem"] != ecosystem
                ]
                self.assertIn(ecosystem, "\n".join(rules.find_dependabot_problems(config)))

    def test_wrong_version_fails(self):
        config = dict(VALID_DEPENDABOT, version=1)
        self.assertIn("version", "\n".join(rules.find_dependabot_problems(config)))


class RealRepositoryTests(unittest.TestCase):
    def test_real_files_pass(self):
        self.assertEqual(rules.validate_repository(PROJECT_ROOT), [])

    def test_real_ruleset_is_valid_json_and_names_every_workflow_job(self):
        ruleset = json.loads(
            (PROJECT_ROOT / rules.RULESET_PATH).read_text(encoding="utf-8")
        )
        self.assertEqual(rules.required_check_names(ruleset), rules.workflow_job_names(PROJECT_ROOT))

    def test_real_codeowners_names_the_project_manager(self):
        text = (PROJECT_ROOT / rules.CODEOWNERS_PATH).read_text(encoding="utf-8")
        self.assertIn("@astranero", text)


class CommandLineTests(unittest.TestCase):
    def run_check(self, root):
        return subprocess.run(
            [sys.executable, str(CHECK_SCRIPT), "--root", str(root)],
            capture_output=True,
            text=True,
        )

    def copy_project(self, destination):
        for relative_path in (
            rules.RULESET_PATH,
            rules.CODEOWNERS_PATH,
            rules.DEPENDABOT_PATH,
            rules.WORKFLOW_PATH,
        ):
            target = destination / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(PROJECT_ROOT / relative_path, target)

    def test_real_project_exits_zero(self):
        result = self.run_check(PROJECT_ROOT)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("OK", result.stdout)

    def test_renamed_job_exits_one_and_names_the_job(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.copy_project(root)
            workflow_file = root / rules.WORKFLOW_PATH
            workflow_file.write_text(
                workflow_file.read_text(encoding="utf-8").replace(
                    "name: Pull request and linked card", "name: Card gate"
                ),
                encoding="utf-8",
            )
            result = self.run_check(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Card gate", result.stdout)

    def test_missing_file_exits_one(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.copy_project(root)
            (root / rules.DEPENDABOT_PATH).unlink()
            result = self.run_check(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("dependabot.yml", result.stdout)


class DependabotExceptionInWorkflowTests(unittest.TestCase):
    """The only gate Dependabot may skip is the linked-card job."""

    def setUp(self):
        workflow_text = (PROJECT_ROOT / rules.WORKFLOW_PATH).read_text(encoding="utf-8")
        self.jobs = yaml.safe_load(workflow_text)["jobs"]

    def test_linked_card_job_skips_only_for_dependabot_authored_pull_requests(self):
        condition = self.jobs["pull-request-gate"]["if"]
        self.assertIn("github.event_name == 'pull_request'", condition)
        # The PR author, not github.actor: a human re-running or editing the
        # PR must not inherit the exception, and only Dependabot can author
        # a PR as dependabot[bot].
        self.assertIn("github.event.pull_request.user.login != 'dependabot[bot]'", condition)
        self.assertNotIn("github.actor", condition)

    def test_repository_checks_always_run(self):
        self.assertNotIn("if", self.jobs["repository-checks"])

    def test_workflow_runs_the_repository_rules_check(self):
        commands = "\n".join(
            step.get("run", "") for step in self.jobs["repository-checks"]["steps"]
        )
        self.assertIn("python tools/validate_repository_rules.py", commands)


if __name__ == "__main__":
    unittest.main()
