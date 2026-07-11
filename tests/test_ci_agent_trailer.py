from __future__ import annotations

import unittest
from pathlib import Path


WORKFLOW_PATH = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "hermetic-tests.yml"


class CiAgentTrailerTests(unittest.TestCase):
    def test_main_push_requires_agent_commit_trailer(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("Require engineering agent trailer", workflow)
        self.assertIn("github.event_name == 'push'", workflow)
        self.assertIn("^Agent: [^[:space:]].+$", workflow)
