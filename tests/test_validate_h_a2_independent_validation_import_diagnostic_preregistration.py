from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_h_a2_independent_validation_import_diagnostic_preregistration import (
    DEFAULT_PREREG_PATH,
    validate_h_a2_independent_validation_import_diagnostic_preregistration,
)


class H_A2IndependentValidationImportDiagnosticPreregistrationTests(unittest.TestCase):
    def test_current_preregistration_passes(self) -> None:
        result = validate_h_a2_independent_validation_import_diagnostic_preregistration()

        self.assertEqual("pass", result["status"])
        self.assertEqual([], result["blockers"])
        self.assertEqual("H-A2", result["hypothesis_id"])
        self.assertEqual("E0", result["evidence_tier"])
        self.assertEqual("h_a2_independent_validation_import_diagnostic", result["experiment_id"])
        self.assertEqual("2025-04-08", result["target_date"])
        self.assertEqual(15, result["expected_request_count"])
        self.assertTrue(result["local_raw_dbn_parse_allowed_after_preregistration"])
        self.assertFalse(result["network_allowed"])
        self.assertFalse(result["paid_data_allowed"])
        self.assertFalse(result["exact_replay_allowed"])
        self.assertFalse(result["paper_trading_allowed"])

    def test_rejects_threshold_change(self) -> None:
        prereg = json.loads(DEFAULT_PREREG_PATH.read_text(encoding="utf-8"))
        prereg["locked_signal_under_validation"]["opening_followthrough_threshold"] = 0.002
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("locked_threshold_must_be_0_001", result["blockers"])

    def test_rejects_network_permission(self) -> None:
        prereg = json.loads(DEFAULT_PREREG_PATH.read_text(encoding="utf-8"))
        prereg["guardrails"]["network_allowed"] = True
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("network_allowed_must_be_false", result["blockers"])

    def test_rejects_exact_replay_permission(self) -> None:
        prereg = json.loads(DEFAULT_PREREG_PATH.read_text(encoding="utf-8"))
        prereg["guardrails"]["exact_replay_allowed"] = True
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("exact_replay_allowed_must_be_false", result["blockers"])

    def test_rejects_missing_planned_step(self) -> None:
        prereg = json.loads(DEFAULT_PREREG_PATH.read_text(encoding="utf-8"))
        prereg["planned_steps"] = [
            step for step in prereg["planned_steps"] if step["step_id"] != "timestamp_alignment_check"
        ]
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("planned_steps_must_follow_required_order", result["blockers"])

    @staticmethod
    def _validate_temp(payload: dict) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prereg.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            return validate_h_a2_independent_validation_import_diagnostic_preregistration(path)


if __name__ == "__main__":
    unittest.main()
