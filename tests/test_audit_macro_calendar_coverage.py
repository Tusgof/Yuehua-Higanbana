from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "audit_macro_calendar_coverage.py"
MACRO_PATH = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "macro_calendar" / "macro_event.jsonl"


def load_auditor():
    spec = importlib.util.spec_from_file_location("audit_macro_calendar_coverage", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load macro calendar coverage auditor")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AuditMacroCalendarCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.auditor = load_auditor()

    def test_current_macro_archive_passes_train_oos_coverage(self) -> None:
        result = self.auditor.audit_macro_calendar_coverage(MACRO_PATH)

        self.assertEqual("pass", result["status"])
        self.assertEqual(481, result["record_count"])
        self.assertEqual([], result["blockers"])
        self.assertTrue(all(not item["missing_event_types"] for item in result["years"]))

    def test_write_reports_outputs_json_and_markdown(self) -> None:
        result = self.auditor.audit_macro_calendar_coverage(MACRO_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            json_output = Path(tmp) / "coverage.json"
            report_output = Path(tmp) / "coverage.md"
            self.auditor.write_reports(result, json_output, report_output)

            payload = json.loads(json_output.read_text(encoding="utf-8"))
            report = report_output.read_text(encoding="utf-8")
            self.assertEqual("pass", payload["status"])
            self.assertIn("Macro Calendar Coverage Audit", report)
            self.assertIn("Status: `pass`", report)


if __name__ == "__main__":
    unittest.main()
