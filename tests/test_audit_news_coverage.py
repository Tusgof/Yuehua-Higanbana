from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "audit_news_coverage.py"
NEWS_PATH = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "news" / "news_item.jsonl"


def load_auditor():
    spec = importlib.util.spec_from_file_location("audit_news_coverage", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load news coverage auditor")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AuditNewsCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.auditor = load_auditor()

    def test_current_news_archive_is_blocked_until_real_archive_exists(self) -> None:
        result = self.auditor.audit_news_coverage(NEWS_PATH)

        self.assertEqual("blocked", result["status"])
        self.assertEqual(0, result["record_count"])
        self.assertIn("requires_real_news_archive", result["blockers"])
        self.assertIn("requires_news_archive_start_by_2022_05_11", result["blockers"])

    def test_write_reports_outputs_json_and_markdown(self) -> None:
        result = self.auditor.audit_news_coverage(NEWS_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            json_output = Path(tmp) / "coverage.json"
            report_output = Path(tmp) / "coverage.md"
            self.auditor.write_reports(result, json_output, report_output)

            payload = json.loads(json_output.read_text(encoding="utf-8"))
            report = report_output.read_text(encoding="utf-8")
            self.assertEqual("blocked", payload["status"])
            self.assertIn("News Coverage Audit", report)
            self.assertIn("requires_real_news_archive", report)


if __name__ == "__main__":
    unittest.main()
