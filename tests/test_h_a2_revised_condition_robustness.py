from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.run_h_a2_revised_condition_robustness import run_experiment
from scripts.validate_h_a2_revised_condition_robustness import validate_h_a2_revised_condition_robustness


class HA2RevisedConditionRobustnessTests(unittest.TestCase):
    def test_run_experiment_outputs_expected_no_search_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary_path = root / "summary.json"
            report_path = root / "report.md"
            search_log_path = root / "search.jsonl"

            result = run_experiment(summary_path=summary_path, report_path=report_path, search_log_path=search_log_path)

            self.assertEqual("complete", result["status"])
            self.assertEqual("H-A2", result["hypothesis_id"])
            self.assertEqual("E1", result["evidence_tier"])
            self.assertEqual("ยังสรุปไม่ได้", result["conclusion"])
            self.assertTrue(result["research_log_required"])
            self.assertFalse(result["network_used"])
            self.assertFalse(result["paid_data_used"])
            self.assertFalse(result["ibkr_request_used"])
            self.assertFalse(result["llm_call_used"])
            self.assertFalse(result["paper_trading_allowed"])
            self.assertFalse(result["methodology"]["threshold_search_used"])
            self.assertFalse(result["methodology"]["oos_tuning_used"])
            self.assertEqual(0.001, result["methodology"]["locked_threshold"])
            self.assertEqual(34, result["sample_counts"]["baseline_oos_non_risk_trade_days"])
            self.assertEqual(13, result["sample_counts"]["retained_oos_trade_days"])
            self.assertEqual(21, result["sample_counts"]["skipped_oos_trade_days"])
            self.assertTrue(result["threshold_provenance_audit"]["provenance_clean"])
            self.assertEqual("diagnostic_underpowered", result["sample_adequacy_relabeling"]["status"])
            self.assertTrue(summary_path.exists())
            self.assertTrue(report_path.exists())
            self.assertEqual(5, len(search_log_path.read_text(encoding="utf-8").strip().splitlines()))

    def test_current_summary_validates_after_run(self) -> None:
        run_experiment()
        result = validate_h_a2_revised_condition_robustness()

        self.assertEqual("pass", result["status"], result["blockers"])
        self.assertEqual("H-A2", result["hypothesis_id"])
        self.assertEqual("E1", result["evidence_tier"])
        self.assertEqual("h_a2_revised_condition_robustness", result["experiment_id"])

    def test_validator_rejects_threshold_search_and_paid_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary_path = root / "summary.json"
            report_path = root / "report.md"
            search_log_path = root / "search.jsonl"
            data = run_experiment(summary_path=summary_path, report_path=report_path, search_log_path=search_log_path)
            data["paid_data_used"] = True
            data["methodology"]["threshold_search_used"] = True
            data["trial_policy"]["threshold_search_used"] = True
            summary_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

            result = validate_h_a2_revised_condition_robustness(summary_path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("paid_data_used_must_be_false", result["blockers"])
        self.assertIn("threshold_search_used_must_be_false", result["blockers"])
        self.assertIn("trial_threshold_search_used_must_be_false", result["blockers"])


if __name__ == "__main__":
    unittest.main()
