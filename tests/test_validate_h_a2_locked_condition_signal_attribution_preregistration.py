from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_h_a2_locked_condition_signal_attribution_preregistration import (
    DEFAULT_PREREG_PATH,
    validate_h_a2_locked_condition_signal_attribution_preregistration,
)


class H_A2LockedConditionSignalAttributionPreregistrationTests(unittest.TestCase):
    def test_current_preregistration_passes(self) -> None:
        result = validate_h_a2_locked_condition_signal_attribution_preregistration()

        self.assertEqual("pass", result["status"])
        self.assertEqual([], result["blockers"])
        self.assertEqual("H-A2", result["hypothesis_id"])
        self.assertEqual("E0", result["evidence_tier"])
        self.assertEqual(0.001, result["locked_threshold"])
        self.assertFalse(result["network_allowed"])
        self.assertFalse(result["paid_data_allowed"])
        self.assertFalse(result["broker_request_allowed"])
        self.assertFalse(result["llm_call_allowed"])
        self.assertFalse(result["threshold_search_allowed"])
        self.assertFalse(result["new_filter_allowed"])
        self.assertEqual(5, result["planned_test_count"])

    def test_rejects_threshold_change(self) -> None:
        prereg = json.loads(DEFAULT_PREREG_PATH.read_text(encoding="utf-8"))
        prereg["locked_condition"]["opening_followthrough_threshold"] = 0.002
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("locked_threshold_must_be_0_001", result["blockers"])

    def test_rejects_new_filter_permission(self) -> None:
        prereg = json.loads(DEFAULT_PREREG_PATH.read_text(encoding="utf-8"))
        prereg["guardrails"]["new_filter_allowed_in_future_run"] = True
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("new_filter_allowed_in_future_run_must_be_false", result["blockers"])

    def test_rejects_missing_timestamp_availability_audit(self) -> None:
        prereg = json.loads(DEFAULT_PREREG_PATH.read_text(encoding="utf-8"))
        prereg["planned_future_tests"] = [
            test for test in prereg["planned_future_tests"] if test["test_id"] != "decision_timestamp_availability_audit"
        ]
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("missing_planned_future_test:decision_timestamp_availability_audit", result["blockers"])

    def test_rejects_broker_request_permission(self) -> None:
        prereg = json.loads(DEFAULT_PREREG_PATH.read_text(encoding="utf-8"))
        prereg["guardrails"]["broker_request_allowed"] = True
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("broker_request_allowed_must_be_false", result["blockers"])

    @staticmethod
    def _validate_temp(payload: dict) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prereg.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            return validate_h_a2_locked_condition_signal_attribution_preregistration(path)


if __name__ == "__main__":
    unittest.main()
