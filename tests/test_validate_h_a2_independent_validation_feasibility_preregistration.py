from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_h_a2_independent_validation_feasibility_preregistration import (
    DEFAULT_PREREG_PATH,
    validate_h_a2_independent_validation_feasibility_preregistration,
)


class H_A2IndependentValidationFeasibilityPreregistrationTests(unittest.TestCase):
    def test_current_preregistration_passes(self) -> None:
        result = validate_h_a2_independent_validation_feasibility_preregistration()

        self.assertEqual("pass", result["status"])
        self.assertEqual([], result["blockers"])
        self.assertEqual("H-A2", result["hypothesis_id"])
        self.assertEqual("E0", result["evidence_tier"])
        self.assertEqual("h_a2_independent_validation_feasibility", result["experiment_id"])
        self.assertEqual("09:35:00", result["candidate_decision_time_et"])
        self.assertEqual(0.001, result["locked_threshold"])
        self.assertEqual(2, result["feature_count"])
        self.assertEqual(5, result["planned_check_count"])
        self.assertFalse(result["network_allowed"])
        self.assertFalse(result["paid_data_allowed"])
        self.assertFalse(result["live_cost_estimate_allowed"])
        self.assertFalse(result["ibkr_request_allowed"])
        self.assertFalse(result["llm_call_allowed"])
        self.assertFalse(result["paper_trading_allowed"])

    def test_rejects_threshold_change(self) -> None:
        prereg = json.loads(DEFAULT_PREREG_PATH.read_text(encoding="utf-8"))
        prereg["locked_signal_under_validation"]["opening_followthrough_threshold"] = 0.002
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("locked_threshold_must_be_0_001", result["blockers"])

    def test_rejects_live_cost_estimate_permission(self) -> None:
        prereg = json.loads(DEFAULT_PREREG_PATH.read_text(encoding="utf-8"))
        prereg["guardrails"]["live_cost_estimate_allowed"] = True
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("live_cost_estimate_allowed_must_be_false", result["blockers"])

    def test_rejects_missing_no_paid_source_inventory_check(self) -> None:
        prereg = json.loads(DEFAULT_PREREG_PATH.read_text(encoding="utf-8"))
        prereg["planned_future_checks"] = [
            check for check in prereg["planned_future_checks"] if check["check_id"] != "no_paid_source_inventory"
        ]
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("missing_planned_future_check:no_paid_source_inventory", result["blockers"])

    def test_rejects_wrong_research_log_number(self) -> None:
        prereg = json.loads(DEFAULT_PREREG_PATH.read_text(encoding="utf-8"))
        prereg["allowed_outputs_for_future_run"]["research_log_if_real_experiment_completes"] = (
            "research_log/032-higanbana-wrong.md"
        )
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("research_log_must_be_033_h_a2_independent_validation_feasibility", result["blockers"])

    @staticmethod
    def _validate_temp(payload: dict) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prereg.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            return validate_h_a2_independent_validation_feasibility_preregistration(path)


if __name__ == "__main__":
    unittest.main()
