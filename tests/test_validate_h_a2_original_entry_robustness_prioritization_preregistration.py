from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_h_a2_original_entry_robustness_prioritization_preregistration import (
    DEFAULT_PREREG_PATH,
    validate_h_a2_original_entry_robustness_prioritization_preregistration,
)


class H_A2OriginalEntryRobustnessPrioritizationPreregistrationTests(unittest.TestCase):
    def test_current_preregistration_passes(self) -> None:
        result = validate_h_a2_original_entry_robustness_prioritization_preregistration()

        self.assertEqual("pass", result["status"])
        self.assertEqual([], result["blockers"])
        self.assertEqual("H-A2", result["hypothesis_id"])
        self.assertEqual("E0", result["evidence_tier"])
        self.assertEqual("h_a2_original_entry_robustness_prioritization", result["experiment_id"])
        self.assertEqual("09:35:00", result["candidate_decision_time_et"])
        self.assertEqual(0.001, result["locked_threshold"])
        self.assertFalse(result["fifteen_minute_component_allowed"])
        self.assertFalse(result["network_allowed"])
        self.assertFalse(result["paid_data_allowed"])
        self.assertFalse(result["ibkr_request_allowed"])
        self.assertFalse(result["llm_call_allowed"])
        self.assertFalse(result["paper_trading_allowed"])
        self.assertEqual(5, result["planned_test_count"])

    def test_rejects_threshold_change(self) -> None:
        prereg = json.loads(DEFAULT_PREREG_PATH.read_text(encoding="utf-8"))
        prereg["locked_rule_under_review"]["opening_followthrough_threshold"] = 0.002
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("locked_threshold_must_be_0_001", result["blockers"])

    def test_rejects_oos_tuning_permission(self) -> None:
        prereg = json.loads(DEFAULT_PREREG_PATH.read_text(encoding="utf-8"))
        prereg["locked_rule_under_review"]["oos_tuning_allowed"] = True
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("oos_tuning_allowed_must_be_false", result["blockers"])

    def test_rejects_paid_data_permission(self) -> None:
        prereg = json.loads(DEFAULT_PREREG_PATH.read_text(encoding="utf-8"))
        prereg["guardrails"]["paid_data_allowed"] = True
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("paid_data_allowed_must_be_false", result["blockers"])

    def test_rejects_wrong_research_log_number(self) -> None:
        prereg = json.loads(DEFAULT_PREREG_PATH.read_text(encoding="utf-8"))
        prereg["allowed_outputs_for_future_run"]["research_log_if_real_experiment_completes"] = (
            "research_log/031-higanbana-wrong.md"
        )
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn(
            "research_log_must_be_032_h_a2_original_entry_robustness_prioritization",
            result["blockers"],
        )

    @staticmethod
    def _validate_temp(payload: dict) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prereg.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            return validate_h_a2_original_entry_robustness_prioritization_preregistration(path)


if __name__ == "__main__":
    unittest.main()
