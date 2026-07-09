from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "plan_exp07_real_news_cases.py"


def load_planner():
    spec = importlib.util.spec_from_file_location("plan_exp07_real_news_cases", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load Exp07 real-news case planner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PlanExp07RealNewsCasesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.planner = load_planner()

    def test_current_project_plan_is_blocked_until_real_news_cases_exist(self) -> None:
        result = self.planner.build_plan()

        self.assertEqual("blocked", result["status"])
        self.assertEqual("blocked_cooldown", result["collection_status"])
        self.assertEqual("blocked_cooldown", result["gdelt_plan_status"])
        self.assertFalse(result["gdelt_live_retry_allowed"])
        self.assertEqual(71, result["candidate_day_count"])
        self.assertEqual(0, result["captured_candidate_count"])
        self.assertIn("requires_real_timestamp_clean_news_cases", result["blockers"])
        self.assertFalse(result["acceptance_bar"]["synthetic_cases_allowed_for_research"])
        self.assertIn("evidence_first_rubric", [row["family_id"] for row in result["prompt_template_families"]])
        self.assertIn("false_alarm_day", result["required_case_groups"])

    def test_captured_real_news_plan_can_be_ready_for_prompt_family_pre_experiment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            gdelt_plan_path = root / "gdelt_plan.json"
            news_audit_path = root / "news_audit.json"
            gdelt_plan_path.write_text(
                json.dumps(
                    {
                        "retry_pressure": {"status": "normal_retry"},
                        "retry_queue_summary": {"next_unattempted_trade_date": None},
                        "commands": [
                            {
                                "trade_date": "2023-09-01",
                                "decision_time_et": "2023-09-01T09:30:00-04:00",
                                "output_path": "data/raw/spy_0dte/news/gdelt/2023-09-01.csv",
                                "status_output_path": "reports/news_gdelt_capture_status/2023-09-01.json",
                                "latest_status": {"status": "captured"},
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            news_audit_path.write_text(json.dumps({"status": "pass", "blockers": []}), encoding="utf-8")

            result = self.planner.build_plan(gdelt_plan_path, news_audit_path)

        self.assertEqual("ready_for_prompt_family_pre_experiment", result["status"])
        self.assertEqual("ready_to_collect", result["collection_status"])
        self.assertEqual([], result["blockers"])
        self.assertEqual(1, result["captured_candidate_count"])
        self.assertEqual("in_sample", result["candidate_queue"][0]["split"])

    def test_main_writes_json_and_markdown_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "plan.json"
            report_path = Path(tmp) / "plan.md"

            returncode = self.planner.main(["--json-output", str(output_path), "--report-output", str(report_path)])

            self.assertEqual(0, returncode)
            result = json.loads(output_path.read_text(encoding="utf-8"))
            report = report_path.read_text(encoding="utf-8")
            self.assertEqual("blocked", result["status"])
            self.assertEqual("blocked_cooldown", result["collection_status"])
            self.assertIn("Exp07 Real News Case Plan", report)
            self.assertIn("Collection status: `blocked_cooldown`", report)
            self.assertIn("structured_json_classifier", report)
            self.assertIn("requires_real_timestamp_clean_news_cases", report)


if __name__ == "__main__":
    unittest.main()
