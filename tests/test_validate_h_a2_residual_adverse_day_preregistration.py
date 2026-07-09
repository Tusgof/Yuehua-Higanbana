from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_h_a2_residual_adverse_day_preregistration import (
    validate_h_a2_residual_adverse_day_preregistration,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PREREG_PATH = PROJECT_ROOT / "experiments" / "h_a2_residual_adverse_day_analysis_preregistration.json"


class ValidateHA2ResidualAdverseDayPreregistrationTests(unittest.TestCase):
    def test_current_preregistration_passes(self) -> None:
        result = validate_h_a2_residual_adverse_day_preregistration()

        self.assertEqual("pass", result["status"], result["blockers"])
        self.assertEqual("H-A2", result["hypothesis_id"])
        self.assertEqual("E0", result["evidence_tier"])
        self.assertEqual("h_a2_residual_adverse_day_analysis", result["experiment_id"])
        self.assertIs(False, result["network_allowed"])
        self.assertIs(False, result["paid_data_allowed"])
        self.assertIs(False, result["broker_request_allowed"])
        self.assertIs(False, result["llm_call_allowed"])
        self.assertEqual(4, result["planned_test_count"])

    def test_rejects_paid_data_or_llm_permission(self) -> None:
        data = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
        data["guardrails"]["paid_data_allowed"] = True
        data["guardrails"]["llm_call_allowed"] = True
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prereg.json"
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

            result = validate_h_a2_residual_adverse_day_preregistration(path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("paid_data_allowed_must_be_false", result["blockers"])
        self.assertIn("llm_call_allowed_must_be_false", result["blockers"])

    def test_rejects_random_split_or_oos_tuning(self) -> None:
        data = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
        data["split_policy"]["random_split_forbidden"] = False
        data["split_policy"]["oos_tuning_forbidden"] = False
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prereg.json"
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

            result = validate_h_a2_residual_adverse_day_preregistration(path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("random_split_forbidden_must_be_true", result["blockers"])
        self.assertIn("oos_tuning_forbidden_must_be_true", result["blockers"])

    def test_rejects_missing_decision_rule(self) -> None:
        data = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
        data["decision_rules"]["park_h_a2_if"] = []
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prereg.json"
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

            result = validate_h_a2_residual_adverse_day_preregistration(path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("decision_rule_needs_two_conditions:park_h_a2_if", result["blockers"])


if __name__ == "__main__":
    unittest.main()
