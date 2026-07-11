from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from lib.io import load_json
from lib.report import render_markdown_report, write_report_pair


class ReportTests(unittest.TestCase):
    def test_writes_json_with_interpreter_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            markdown = render_markdown_report("Test report", [("Result", "- Status: `pass`")])
            stored = write_report_pair({"status": "pass"}, root / "report.json", root / "report.md", markdown)
            loaded = load_json(root / "report.json")

            self.assertEqual("pass", stored["status"])
            self.assertIn("interpreter", loaded)
            self.assertEqual("# Test report\n\n## Result\n\n- Status: `pass`\n", (root / "report.md").read_text(encoding="utf-8"))
