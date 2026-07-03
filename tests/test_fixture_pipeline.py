from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class FixturePipelineTests(unittest.TestCase):
    def test_fixture_pipeline_passes_and_preserves_blocked_final_review(self) -> None:
        if os.environ.get("SPY0DTE_FIXTURE_PIPELINE_CHILD") == "1":
            self.skipTest("avoid recursive pipeline execution")
        completed = subprocess.run(
            [sys.executable, "scripts/run_fixture_pipeline.py"],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        summary = json.loads(completed.stdout)
        self.assertEqual("pass", summary["status"])
        step_names = [step["name"] for step in summary["steps"]]
        for required_step in [
            "validate_m2_contracts",
            "validate_exp07_policy_cases",
            "evaluate_exp07_acceptance",
            "validate_exp07_strategy_ablation_plan",
            "run_exp07_strategy_ablation_status",
            "validate_macro_calendar_sources",
            "macro_calendar_capture_dry_run",
            "convert_macro_calendar_capture_check",
            "import_converted_macro_calendar_capture",
            "audit_macro_calendar_coverage",
            "plan_macro_calendar_capture_commands",
            "audit_macro_calendar_raw_archive",
            "validate_news_sources",
            "gdelt_news_capture_dry_run",
            "audit_news_coverage",
            "audit_paid_costs",
            "audit_research_readiness",
            "audit_research_logs",
            "import_macro_calendar_snapshot_fixture",
            "import_news_snapshot_fixture",
            "import_m3_fixture",
            "generate_m6_reports",
            "unit_tests",
        ]:
            self.assertIn(required_step, step_names)
        for step in summary["steps"]:
            self.assertEqual(0, step["returncode"], step["name"])

        final_review = (PROJECT_ROOT / "reports" / "final_research_review.md").read_text(encoding="utf-8")
        self.assertIn("Gate status: `blocked`", final_review)
        self.assertIn("ยังสรุปไม่ได้", final_review)


if __name__ == "__main__":
    unittest.main()
