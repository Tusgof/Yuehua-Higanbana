from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_h_a2_post_exact_replay_sample_expansion_decision import (
    DEFAULT_DECISION_PATH,
    validate_h_a2_post_exact_replay_sample_expansion_decision,
)


class H_A2PostExactReplaySampleExpansionDecisionTests(unittest.TestCase):
    def test_current_decision_passes(self) -> None:
        result = validate_h_a2_post_exact_replay_sample_expansion_decision()

        self.assertEqual("pass", result["status"])
        self.assertEqual([], result["blockers"])
        self.assertEqual("H-A2", result["hypothesis_id"])
        self.assertEqual("E0", result["evidence_tier"])
        self.assertEqual("h_a2_post_exact_replay_sample_expansion_decision", result["experiment_id"])
        self.assertEqual("metadata_estimate_post_stress_normalization_control_pack", result["selected_next_step"])
        self.assertEqual("DATABENTO_API_AI", result["selected_key_env_for_next_metadata_estimate"])
        self.assertEqual(1, result["candidate_batch_count"])
        self.assertEqual("post_stress_normalization_control_pack", result["first_batch_id"])
        self.assertEqual(10, result["first_batch_expected_trading_days"])
        self.assertFalse(result["network_allowed"])
        self.assertFalse(result["paid_data_allowed"])
        self.assertFalse(result["exact_replay_allowed"])
        self.assertFalse(result["paper_trading_allowed"])

    def test_rejects_source_summary_mismatch(self) -> None:
        decision = self._load_decision()
        decision["source_result_summary"]["source_implementable_pnl"] = 100.0
        result = self._validate_temp(decision)

        self.assertEqual("blocked", result["status"])
        self.assertIn("source_summary_mismatch:source_implementable_pnl", result["blockers"])

    def test_rejects_threshold_change(self) -> None:
        decision = self._load_decision()
        decision["locked_signal_under_validation"]["opening_followthrough_threshold"] = 0.002
        result = self._validate_temp(decision)

        self.assertEqual("blocked", result["status"])
        self.assertIn("locked_threshold_must_be_0_001", result["blockers"])

    def test_rejects_wrong_selected_key(self) -> None:
        decision = self._load_decision()
        decision["selected_key_env_for_next_metadata_estimate"] = "DATABENTO_API_MO"
        result = self._validate_temp(decision)

        self.assertEqual("blocked", result["status"])
        self.assertIn("selected_key_env_must_be_databento_api_ai", result["blockers"])

    def test_rejects_paid_data_permission(self) -> None:
        decision = self._load_decision()
        decision["guardrails"]["paid_data_allowed"] = True
        result = self._validate_temp(decision)

        self.assertEqual("blocked", result["status"])
        self.assertIn("paid_data_allowed_must_be_false", result["blockers"])

    @staticmethod
    def _load_decision() -> dict:
        return json.loads(DEFAULT_DECISION_PATH.read_text(encoding="utf-8"))

    @staticmethod
    def _validate_temp(payload: dict) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "decision.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            return validate_h_a2_post_exact_replay_sample_expansion_decision(path)


if __name__ == "__main__":
    unittest.main()
