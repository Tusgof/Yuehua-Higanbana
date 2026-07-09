from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_h_a2_post_stress_normalization_control_import_diagnostic import (
    DEFAULT_SUMMARY_PATH,
    validate_h_a2_post_stress_normalization_control_import_diagnostic,
)


class H_A2PostStressNormalizationControlImportDiagnosticTests(unittest.TestCase):
    def test_current_summary_validates(self) -> None:
        self.assertTrue(DEFAULT_SUMMARY_PATH.exists(), "run the diagnostic before running this validator test")
        result = validate_h_a2_post_stress_normalization_control_import_diagnostic()

        self.assertEqual("pass", result["status"])
        self.assertEqual([], result["blockers"])
        self.assertEqual("h_a2_post_stress_normalization_control_import_diagnostic", result["experiment_id"])
        self.assertEqual("H-A2", result["hypothesis_id"])
        self.assertEqual("E1", result["evidence_tier"])
        self.assertEqual(10, result["date_count"])
        self.assertTrue(result["research_log_required"])

    def test_validator_rejects_e2_or_paper_claim(self) -> None:
        self.assertTrue(DEFAULT_SUMMARY_PATH.exists(), "run the diagnostic before running this validator test")
        payload = json.loads(DEFAULT_SUMMARY_PATH.read_text(encoding="utf-8"))
        payload["evidence_tier"] = "E2"
        payload["paper_trading_allowed"] = True
        payload["exact_replay_used"] = True
        result = self._validate_temp(payload)

        self.assertEqual("blocked", result["status"])
        self.assertIn("evidence_tier_must_be_e1", result["blockers"])
        self.assertIn("paper_trading_allowed_must_be_false", result["blockers"])
        self.assertIn("exact_replay_used_must_be_false", result["blockers"])

    @staticmethod
    def _validate_temp(payload: dict) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.json"
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            return validate_h_a2_post_stress_normalization_control_import_diagnostic(path)


if __name__ == "__main__":
    unittest.main()

