from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_h_a2_normal_control_sample_decision import (
    DEFAULT_DECISION_PATH,
    validate_h_a2_normal_control_sample_decision,
)


class H_A2NormalControlSampleDecisionTests(unittest.TestCase):
    def test_current_decision_passes(self) -> None:
        result = validate_h_a2_normal_control_sample_decision()

        self.assertEqual("pass", result["status"])
        self.assertEqual([], result["blockers"])
        self.assertEqual("H-A2", result["hypothesis_id"])
        self.assertEqual("E0", result["evidence_tier"])
        self.assertEqual("h_a2_normal_control_sample_decision", result["experiment_id"])
        self.assertEqual("DATABENTO_API_MO", result["selected_key_env_for_next_metadata_estimate"])
        self.assertEqual(2, result["candidate_batch_count"])
        self.assertEqual("low_normal_vix_control_pack", result["first_batch_id"])
        self.assertEqual(10, result["first_batch_expected_trading_days"])
        self.assertFalse(result["network_allowed"])
        self.assertFalse(result["paid_data_allowed"])
        self.assertFalse(result["live_cost_estimate_allowed_by_this_artifact"])
        self.assertFalse(result["paper_trading_allowed"])

    def test_rejects_high_vix_first_sequence(self) -> None:
        decision = json.loads(DEFAULT_DECISION_PATH.read_text(encoding="utf-8"))
        decision["candidate_estimate_batches"].insert(
            0,
            {
                "batch_id": "sample_cost_probe_high_vix_one_day",
                "dates": ["2025-04-08"],
                "expected_trading_days_from_local_vix": 1,
                "estimate_only_next": True,
                "download_allowed_by_this_artifact": False,
                "vix_context": {"observed_vix_close_range": [52.33, 52.33], "observed_vxv_close_range": [36.88, 36.88]},
                "macro_context": {"high_importance_macro_days_from_local_calendar": 0},
            },
        )
        result = self._validate_temp(decision)

        self.assertEqual("blocked", result["status"])
        self.assertIn("candidate_batches_must_be_normal_control_first", result["blockers"])

    def test_rejects_threshold_change(self) -> None:
        decision = json.loads(DEFAULT_DECISION_PATH.read_text(encoding="utf-8"))
        decision["locked_signal_under_validation"]["opening_followthrough_threshold"] = 0.002
        result = self._validate_temp(decision)

        self.assertEqual("blocked", result["status"])
        self.assertIn("locked_threshold_must_be_0_001", result["blockers"])

    def test_rejects_download_permission(self) -> None:
        decision = json.loads(DEFAULT_DECISION_PATH.read_text(encoding="utf-8"))
        decision["candidate_estimate_batches"][0]["download_allowed_by_this_artifact"] = True
        result = self._validate_temp(decision)

        self.assertEqual("blocked", result["status"])
        self.assertIn("batch_download_must_be_false:low_normal_vix_control_pack", result["blockers"])

    def test_rejects_wrong_selected_key(self) -> None:
        decision = json.loads(DEFAULT_DECISION_PATH.read_text(encoding="utf-8"))
        decision["selected_key_env_for_next_metadata_estimate"] = "DATABENTO_API_AI"
        result = self._validate_temp(decision)

        self.assertEqual("blocked", result["status"])
        self.assertIn("selected_key_env_must_be_databento_api_mo", result["blockers"])

    @staticmethod
    def _validate_temp(payload: dict) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "decision.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            return validate_h_a2_normal_control_sample_decision(path)


if __name__ == "__main__":
    unittest.main()
