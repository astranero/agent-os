import json
import tempfile
import unittest
from pathlib import Path

from tools.agent_factory import create_agent_manifest


class AgentFactoryTests(unittest.TestCase):
    def test_security_reviewer_gets_scanner_tools_without_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "agent.json"
            create_agent_manifest(
                role="security-reviewer",
                project="demo",
                card="AGENT-OS-19",
                output_path=output,
            )
            manifest = json.loads(output.read_text(encoding="utf-8"))
            self.assertIn("run_codeql", manifest["required_tools"])
            self.assertIn("run_semgrep", manifest["required_tools"])
            self.assertNotIn("token", json.dumps(manifest).lower())

    def test_unknown_role_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "unknown role"):
                create_agent_manifest(
                    role="unknown",
                    project="demo",
                    card="AGENT-OS-19",
                    output_path=Path(directory) / "agent.json",
                )


if __name__ == "__main__":
    unittest.main()
