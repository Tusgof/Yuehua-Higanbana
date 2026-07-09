from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.run_h_a2_original_entry_revision import run_experiment
from scripts.validate_h_a2_original_entry_revision import validate_h_a2_original_entry_revision


class HA2OriginalEntryRevisionTests(unittest.TestCase):
    def test_run_experiment_outputs_0935_only_summary(self) -> None:
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
            self.assertEqual("09:35:00", result["methodology"]["candidate_decision_time_et"])
            self.assertEqual(0.001, result["methodology"]["locked_threshold"])
            self.assertEqual(["clean_macro_vix_condition", "proxy_5m_followthrough"], result["methodology"]["used_features"])
            self.assertFalse(result["methodology"]["fifteen_minute_conflict_component_used"])
            self.assertFalse(result["methodology"]["delayed_entry_component_used"])
            self.assertFalse(result["methodology"]["threshold_search_used"])
            self.assertFalse(result["methodology"]["new_oos_selected_filter_used"])
            self.assertTrue(result["original_entry_timestamp_cleanliness"]["all_features_known_by_decision_time"])
            self.assertTrue(result["forbidden_feature_exclusion"]["all_forbidden_features_excluded"])
            self.assertEqual(30, result["sample_counts"]["baseline_train_non_risk_trade_days"])
            self.assertEqual(16, result["sample_counts"]["retained_train_trade_days"])
            self.assertEqual(34, result["sample_counts"]["baseline_oos_non_risk_trade_days"])
            self.assertEqual(14, result["sample_counts"]["retained_oos_trade_days"])
            self.assertEqual("directionally_useful_but_underpowered", result["original_entry_implementable_pnl_check"]["comparison_status"])
            self.assertEqual("forbidden", result["hypothesis_decision"]["e2_status"])
            self.assertTrue(summary_path.exists())
            self.assertTrue(report_path.exists())
            self.assertEqual(6, len(search_log_path.read_text(encoding="utf-8").strip().splitlines()))

    def test_current_summary_validates_after_run(self) -> None:
        run_experiment()
        result = validate_h_a2_original_entry_revision()

        self.assertEqual("pass", result["status"], result["blockers"])
        self.assertEqual("H-A2", result["hypothesis_id"])
        self.assertEqual("E1", result["evidence_tier"])
        self.assertEqual("h_a2_original_entry_revision", result["experiment_id"])

    def test_validator_rejects_15m_component_and_e2_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary_path = root / "summary.json"
            report_path = root / "report.md"
            search_log_path = root / "search.jsonl"
            data = run_experiment(summary_path=summary_path, report_path=report_path, search_log_path=search_log_path)
            data["methodology"]["fifteen_minute_conflict_component_used"] = True
            data["hypothesis_decision"]["e2_status"] = "allowed"
            summary_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

            result = validate_h_a2_original_entry_revision(summary_path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("fifteen_minute_conflict_component_used_must_be_false", result["blockers"])
        self.assertIn("e2_status_must_be_forbidden", result["blockers"])


if __name__ == "__main__":
    unittest.main()
