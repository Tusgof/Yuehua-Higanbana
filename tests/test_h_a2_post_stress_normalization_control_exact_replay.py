from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_h_a2_post_stress_normalization_control_exact_replay import (
    DEFAULT_SUMMARY_PATH,
    validate_h_a2_post_stress_normalization_control_exact_replay,
)


class H_A2PostStressNormalizationControlExactReplayTests(unittest.TestCase):
    def test_current_summary_validates(self) -> None:
        self.assertTrue(DEFAULT_SUMMARY_PATH.exists(), "run exact replay before this validator test")
        result = validate_h_a2_post_stress_normalization_control_exact_replay()

        self.assertEqual("pass", result["status"])
        self.assertEqual([], result["blockers"])
        self.assertEqual("h_a2_post_stress_normalization_control_exact_replay", result["experiment_id"])
        self.assertEqual("H-A2", result["hypothesis_id"])
        self.assertEqual("E1", result["evidence_tier"])
        self.assertEqual("2025-05-05", result["candidate_date"])
        self.assertEqual("call", result["direction"])
        self.assertIsNotNone(result["mid_pnl"])
        self.assertIsNotNone(result["implementable_pnl"])
        self.assertFalse(result["paper_trading_allowed"])
        self.assertTrue(result["research_log_required"])

    def test_validator_rejects_e2_or_paper_claim(self) -> None:
        payload = self._load_summary()
        payload["evidence_tier"] = "E2"
        payload["paper_trading_allowed"] = True
        payload["operational_validation_allowed"] = True
        result = self._validate_temp(payload)

        self.assertEqual("blocked", result["status"])
        self.assertIn("evidence_tier_must_be_e1", result["blockers"])
        self.assertIn("paper_trading_allowed_must_be_false", result["blockers"])
        self.assertIn("operational_validation_allowed_must_be_false", result["blockers"])

    def test_validator_rejects_broader_or_changed_candidate(self) -> None:
        payload = self._load_summary()
        payload["candidate"]["date"] = "2025-05-06"
        payload["candidate"]["direction"] = "put"
        result = self._validate_temp(payload)

        self.assertEqual("blocked", result["status"])
        self.assertIn("candidate_date_must_be_2025_05_05", result["blockers"])
        self.assertIn("candidate_direction_must_be_call", result["blockers"])

    def test_validator_rejects_missing_implementable_pnl(self) -> None:
        payload = self._load_summary()
        payload["pnl"].pop("implementable_pnl")
        result = self._validate_temp(payload)

        self.assertEqual("blocked", result["status"])
        self.assertIn("pnl_missing_implementable_pnl", result["blockers"])

    @staticmethod
    def _load_summary() -> dict:
        return json.loads(DEFAULT_SUMMARY_PATH.read_text(encoding="utf-8"))

    @staticmethod
    def _validate_temp(payload: dict) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.json"
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            return validate_h_a2_post_stress_normalization_control_exact_replay(path)


if __name__ == "__main__":
    unittest.main()
