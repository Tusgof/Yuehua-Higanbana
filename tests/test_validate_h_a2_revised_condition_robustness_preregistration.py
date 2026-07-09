from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from scripts.validate_h_a2_revised_condition_robustness_preregistration import (
    DEFAULT_PREREG_PATH,
    validate_h_a2_revised_condition_robustness_preregistration,
)


class H_A2RevisedConditionRobustnessPreregistrationTests(unittest.TestCase):
    def test_current_preregistration_passes(self) -> None:
        result = validate_h_a2_revised_condition_robustness_preregistration()

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
        self.assertEqual(5, result["planned_test_count"])

    def test_rejects_threshold_change(self) -> None:
        prereg = json.loads(DEFAULT_PREREG_PATH.read_text(encoding="utf-8"))
        prereg["locked_condition"]["opening_followthrough_threshold"] = 0.002
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("locked_threshold_must_be_0_001", result["blockers"])

    def test_rejects_threshold_search_permission(self) -> None:
        prereg = json.loads(DEFAULT_PREREG_PATH.read_text(encoding="utf-8"))
        prereg["guardrails"]["threshold_search_allowed_in_future_run"] = True
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("threshold_search_allowed_in_future_run_must_be_false", result["blockers"])

    def test_rejects_oos_tuning_permission(self) -> None:
        prereg = json.loads(DEFAULT_PREREG_PATH.read_text(encoding="utf-8"))
        prereg["split_policy"]["oos_tuning_forbidden"] = False
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("oos_tuning_forbidden_must_be_true", result["blockers"])

    def test_rejects_missing_big_day_check(self) -> None:
        prereg = json.loads(DEFAULT_PREREG_PATH.read_text(encoding="utf-8"))
        edited = deepcopy(prereg)
        edited["planned_future_tests"] = [
            test for test in edited["planned_future_tests"] if test["test_id"] != "big_day_dependency_check"
        ]
        result = self._validate_temp(edited)

        self.assertEqual("blocked", result["status"])
        self.assertIn("missing_planned_future_test:big_day_dependency_check", result["blockers"])

    @staticmethod
    def _validate_temp(payload: dict) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prereg.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            return validate_h_a2_revised_condition_robustness_preregistration(path)


if __name__ == "__main__":
    unittest.main()
