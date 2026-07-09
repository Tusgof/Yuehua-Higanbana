from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.run_h_a2_residual_adverse_day_analysis import run_analysis
from scripts.validate_h_a2_residual_adverse_day_analysis import validate_h_a2_residual_adverse_day_analysis


class HA2ResidualAdverseDayAnalysisTests(unittest.TestCase):
    def test_run_analysis_outputs_expected_local_only_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary_path = root / "summary.json"
            report_path = root / "report.md"
            search_log_path = root / "search.jsonl"

            result = run_analysis(summary_path=summary_path, report_path=report_path, search_log_path=search_log_path)

            self.assertEqual("complete", result["status"])
            self.assertEqual("H-A2", result["hypothesis_id"])
            self.assertEqual("E1", result["evidence_tier"])
            self.assertEqual("ยังสรุปไม่ได้", result["conclusion"])
            self.assertTrue(result["research_log_required"])
            self.assertFalse(result["network_used"])
            self.assertFalse(result["paid_data_used"])
            self.assertFalse(result["llm_call_used"])
            self.assertFalse(result["paper_trading_allowed"])
            self.assertEqual(463, result["sample_counts"]["daily_rows"])
            self.assertEqual(90, result["sample_counts"]["trade_days"])
            self.assertEqual(64, result["sample_counts"]["non_risk_trade_days"])
            self.assertEqual(26, result["sample_counts"]["macro_only_trade_days"])
            self.assertGreater(result["sample_counts"]["non_risk_losing_trade_days"], 0)
            self.assertGreater(result["sample_counts"]["macro_only_losing_trade_days"], 0)
            self.assertTrue(summary_path.exists())
            self.assertTrue(report_path.exists())
            self.assertEqual(4, len(search_log_path.read_text(encoding="utf-8").strip().splitlines()))

    def test_current_summary_validates_after_run(self) -> None:
        run_analysis()
        result = validate_h_a2_residual_adverse_day_analysis()

        self.assertEqual("pass", result["status"], result["blockers"])
        self.assertEqual("H-A2", result["hypothesis_id"])
        self.assertEqual("E1", result["evidence_tier"])
        self.assertEqual("h_a2_residual_adverse_day_analysis", result["experiment_id"])

    def test_validator_rejects_paid_data_and_bad_conclusion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary_path = root / "summary.json"
            report_path = root / "report.md"
            search_log_path = root / "search.jsonl"
            data = run_analysis(summary_path=summary_path, report_path=report_path, search_log_path=search_log_path)
            data["paid_data_used"] = True
            data["conclusion"] = "approved"
            summary_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

            result = validate_h_a2_residual_adverse_day_analysis(summary_path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("paid_data_used_must_be_false", result["blockers"])
        self.assertIn("conclusion_must_use_project_label", result["blockers"])


if __name__ == "__main__":
    unittest.main()
