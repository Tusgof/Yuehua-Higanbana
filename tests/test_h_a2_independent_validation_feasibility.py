from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.run_h_a2_independent_validation_feasibility import run_h_a2_independent_validation_feasibility
from scripts.validate_h_a2_independent_validation_feasibility import (
    DEFAULT_SUMMARY_PATH,
    validate_h_a2_independent_validation_feasibility,
)


class H_A2IndependentValidationFeasibilityTests(unittest.TestCase):
    def test_runner_generates_expected_summary(self) -> None:
        summary = run_h_a2_independent_validation_feasibility()

        self.assertEqual("h_a2_independent_validation_feasibility", summary["experiment_id"])
        self.assertEqual("E1", summary["evidence_tier"])
        self.assertEqual("ยังสรุปไม่ได้", summary["conclusion"])
        self.assertEqual(14, summary["current_gap_inventory"]["retained_oos_trade_days"])
        self.assertEqual(90, summary["current_gap_inventory"]["current_total_closed_trades"])
        self.assertIn("vix_above_25", summary["current_gap_inventory"]["missing_regime_buckets"])
        self.assertEqual(
            "no_paid_can_plan_but_cannot_validate_edge",
            summary["no_paid_source_inventory"]["no_paid_feasibility_status"],
        )
        self.assertIn(
            summary["next_action_selection"]["decision"],
            {"draft_paid_cost_estimate_plan_only", "pause_paid_path_run_no_paid_gap_report_or_wait_for_topup"},
        )
        self.assertFalse(summary["paid_data_used"])
        self.assertFalse(summary["live_cost_estimate_used"])
        self.assertTrue(summary["research_log_required"])

    def test_current_summary_passes_validator(self) -> None:
        result = validate_h_a2_independent_validation_feasibility()

        self.assertEqual("pass", result["status"])
        self.assertEqual([], result["blockers"])
        self.assertEqual("H-A2", result["hypothesis_id"])
        self.assertEqual("E1", result["evidence_tier"])
        self.assertEqual(14, result["retained_oos_trade_days"])
        self.assertIn(
            result["decision"],
            {"draft_paid_cost_estimate_plan_only", "pause_paid_path_run_no_paid_gap_report_or_wait_for_topup"},
        )
        self.assertTrue(result["research_log_required"])

    def test_validator_rejects_paid_download_permission(self) -> None:
        payload = json.loads(DEFAULT_SUMMARY_PATH.read_text(encoding="utf-8"))
        payload["paid_data_decision_tree"]["cost_guard_preconditions"]["paid_download_allowed_by_this_run"] = True
        result = self._validate_temp(payload)

        self.assertEqual("blocked", result["status"])
        self.assertIn("paid_download_allowed_by_this_run_must_be_false", result["blockers"])

    def test_validator_rejects_e2_decision_cap(self) -> None:
        payload = json.loads(DEFAULT_SUMMARY_PATH.read_text(encoding="utf-8"))
        payload["next_action_selection"]["evidence_tier_cap"] = "E2"
        result = self._validate_temp(payload)

        self.assertEqual("blocked", result["status"])
        self.assertIn("evidence_tier_cap_must_be_e1", result["blockers"])

    @staticmethod
    def _validate_temp(payload: dict) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.json"
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            return validate_h_a2_independent_validation_feasibility(path)


if __name__ == "__main__":
    unittest.main()
