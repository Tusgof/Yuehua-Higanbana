from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from scripts.validate_h_a2_revised_opening_followthrough_preregistration import (
    DEFAULT_PREREG_PATH,
    validate_h_a2_revised_opening_followthrough_preregistration,
)


class H_A2RevisedOpeningFollowthroughPreregistrationTests(unittest.TestCase):
    def test_current_preregistration_passes(self) -> None:
        result = validate_h_a2_revised_opening_followthrough_preregistration()

        self.assertEqual("pass", result["status"])
        self.assertEqual([], result["blockers"])
        self.assertEqual("H-A2", result["hypothesis_id"])
        self.assertEqual("E0", result["evidence_tier"])
        self.assertFalse(result["network_allowed"])
        self.assertFalse(result["paid_data_allowed"])
        self.assertFalse(result["broker_request_allowed"])
        self.assertFalse(result["llm_call_allowed"])
        self.assertEqual(4, result["planned_test_count"])

    def test_rejects_oos_tuning_permission(self) -> None:
        prereg = json.loads(DEFAULT_PREREG_PATH.read_text(encoding="utf-8"))
        prereg["split_policy"]["oos_tuning_forbidden"] = False
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("oos_tuning_forbidden_must_be_true", result["blockers"])

    def test_rejects_paid_data_permission(self) -> None:
        prereg = json.loads(DEFAULT_PREREG_PATH.read_text(encoding="utf-8"))
        prereg["guardrails"]["paid_data_allowed"] = True
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("paid_data_allowed_must_be_false", result["blockers"])

    def test_rejects_missing_train_only_threshold_test(self) -> None:
        prereg = json.loads(DEFAULT_PREREG_PATH.read_text(encoding="utf-8"))
        edited = deepcopy(prereg)
        edited["planned_future_tests"] = [
            test for test in edited["planned_future_tests"] if test["test_id"] != "train_only_threshold_lock"
        ]
        result = self._validate_temp(edited)

        self.assertEqual("blocked", result["status"])
        self.assertIn("missing_planned_future_test:train_only_threshold_lock", result["blockers"])

    @staticmethod
    def _validate_temp(payload: dict) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prereg.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            return validate_h_a2_revised_opening_followthrough_preregistration(path)


if __name__ == "__main__":
    unittest.main()
