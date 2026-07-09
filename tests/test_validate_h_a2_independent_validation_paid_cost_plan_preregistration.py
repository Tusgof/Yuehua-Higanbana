from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_h_a2_independent_validation_paid_cost_plan_preregistration import (
    DEFAULT_PREREG_PATH,
    validate_h_a2_independent_validation_paid_cost_plan_preregistration,
)


class H_A2IndependentValidationPaidCostPlanPreregistrationTests(unittest.TestCase):
    def test_current_preregistration_passes(self) -> None:
        result = validate_h_a2_independent_validation_paid_cost_plan_preregistration()

        self.assertEqual("pass", result["status"])
        self.assertEqual([], result["blockers"])
        self.assertEqual("H-A2", result["hypothesis_id"])
        self.assertEqual("E0", result["evidence_tier"])
        self.assertEqual("h_a2_independent_validation_paid_cost_plan", result["experiment_id"])
        self.assertEqual(4, result["candidate_batch_count"])
        self.assertEqual("sample_cost_probe_high_vix_one_day", result["first_batch_id"])
        self.assertEqual(5.010294, result["current_remaining_before_stop_usd"])
        self.assertFalse(result["network_allowed"])
        self.assertFalse(result["paid_data_allowed"])
        self.assertFalse(result["live_cost_estimate_allowed"])
        self.assertFalse(result["ibkr_request_allowed"])
        self.assertFalse(result["llm_call_allowed"])
        self.assertFalse(result["paper_trading_allowed"])

    def test_rejects_live_cost_estimate_permission(self) -> None:
        prereg = json.loads(DEFAULT_PREREG_PATH.read_text(encoding="utf-8"))
        prereg["guardrails"]["live_cost_estimate_allowed"] = True
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("live_cost_estimate_allowed_must_be_false", result["blockers"])

    def test_rejects_download_permission(self) -> None:
        prereg = json.loads(DEFAULT_PREREG_PATH.read_text(encoding="utf-8"))
        prereg["candidate_estimate_batches"][0]["download_allowed"] = True
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("batch_download_must_be_false:sample_cost_probe_high_vix_one_day", result["blockers"])

    def test_rejects_threshold_change(self) -> None:
        prereg = json.loads(DEFAULT_PREREG_PATH.read_text(encoding="utf-8"))
        prereg["locked_signal_under_validation"]["opening_followthrough_threshold"] = 0.002
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("locked_threshold_must_be_0_001", result["blockers"])

    def test_rejects_missing_high_vix_date(self) -> None:
        prereg = json.loads(DEFAULT_PREREG_PATH.read_text(encoding="utf-8"))
        prereg["candidate_estimate_batches"][1]["dates"].remove("2025-04-08")
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("missing_high_vix_date:2025-04-08", result["blockers"])

    @staticmethod
    def _validate_temp(payload: dict) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prereg.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            return validate_h_a2_independent_validation_paid_cost_plan_preregistration(path)


if __name__ == "__main__":
    unittest.main()
