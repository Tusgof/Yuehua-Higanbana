from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.run_h_a2_original_entry_robustness_prioritization import run_experiment
from scripts.validate_h_a2_original_entry_robustness_prioritization import (
    DEFAULT_SUMMARY_PATH,
    validate_h_a2_original_entry_robustness_prioritization,
)


class H_A2OriginalEntryRobustnessPrioritizationTests(unittest.TestCase):
    def test_run_experiment_outputs_e1_prioritization_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            result = run_experiment(
                summary_path=tmp_path / "summary.json",
                report_path=tmp_path / "report.md",
                search_log_path=tmp_path / "search_log.jsonl",
            )

        self.assertEqual("complete", result["status"])
        self.assertEqual("E1", result["evidence_tier"])
        self.assertEqual("prioritize_independent_validation_plan_under_e1", result["validation_priority_decision"]["decision"])
        self.assertEqual(14, result["sample_counts"]["retained_oos_trade_days"])
        self.assertEqual("pass_directional_but_underpowered", result["leave_one_and_big_day_dependency"]["big_day_dependency_status"])
        self.assertEqual("concentrated_underpowered", result["regime_and_calendar_concentration"]["concentration_status"])
        self.assertFalse(result["paid_data_used"])
        self.assertFalse(result["ibkr_request_used"])
        self.assertFalse(result["llm_call_used"])
        self.assertFalse(result["paper_trading_allowed"])

    def test_current_summary_validates_after_run(self) -> None:
        run_experiment()
        result = validate_h_a2_original_entry_robustness_prioritization()

        self.assertEqual("pass", result["status"])
        self.assertEqual([], result["blockers"])
        self.assertEqual("h_a2_original_entry_robustness_prioritization", result["experiment_id"])
        self.assertEqual("H-A2", result["hypothesis_id"])
        self.assertEqual("E1", result["evidence_tier"])
        self.assertEqual("prioritize_independent_validation_plan_under_e1", result["decision"])
        self.assertEqual(14, result["retained_oos_trade_days"])
        self.assertTrue(result["research_log_required"])

    def test_validator_rejects_e2_or_paid_claim(self) -> None:
        run_experiment()
        payload = json.loads(DEFAULT_SUMMARY_PATH.read_text(encoding="utf-8"))
        payload["evidence_tier"] = "E2"
        payload["paid_data_used"] = True
        result = self._validate_temp(payload)

        self.assertEqual("blocked", result["status"])
        self.assertIn("evidence_tier_must_be_e1", result["blockers"])
        self.assertIn("paid_data_used_must_be_false", result["blockers"])

    @staticmethod
    def _validate_temp(payload: dict) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            return validate_h_a2_original_entry_robustness_prioritization(path)


if __name__ == "__main__":
    unittest.main()
