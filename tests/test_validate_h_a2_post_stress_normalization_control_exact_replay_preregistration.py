from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from lib.environment import data_root, wiki_root
from tests.tiers import state_audit

from scripts.validate_h_a2_post_stress_normalization_control_exact_replay_preregistration import (
    DEFAULT_PREREG_PATH,
    validate_h_a2_post_stress_normalization_control_exact_replay_preregistration,
)


@state_audit(("HIGANBANA_DATA_ROOT", data_root()), ("HIGANBANA_WIKI_ROOT", wiki_root()))
class H_A2PostStressNormalizationControlExactReplayPreregistrationTests(unittest.TestCase):
    def test_current_preregistration_passes(self) -> None:
        result = validate_h_a2_post_stress_normalization_control_exact_replay_preregistration()

        self.assertEqual("pass", result["status"])
        self.assertEqual([], result["blockers"])
        self.assertEqual("H-A2", result["hypothesis_id"])
        self.assertEqual("E0", result["evidence_tier"])
        self.assertEqual("h_a2_post_stress_normalization_control_exact_replay", result["experiment_id"])
        self.assertEqual(["2025-05-05"], result["candidate_dates"])
        self.assertEqual(1, result["candidate_count"])
        self.assertEqual("call", result["candidate_direction"])
        self.assertTrue(result["exact_replay_allowed_after_preregistration"])
        self.assertTrue(result["candidate_trade_pnl_allowed_after_preregistration"])
        self.assertFalse(result["network_allowed"])
        self.assertFalse(result["paid_data_allowed"])
        self.assertFalse(result["paper_trading_allowed"])
        self.assertFalse(result["e2_claim_allowed"])

    def test_rejects_broader_candidate_dates(self) -> None:
        prereg = self._load_prereg()
        prereg["candidate_scope"]["candidate_dates"].append("2025-05-06")
        prereg["candidate_scope"]["candidate_count"] = 2
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("candidate_dates_must_match", result["blockers"])
        self.assertIn("candidate_count_must_match", result["blockers"])

    def test_rejects_threshold_change(self) -> None:
        prereg = self._load_prereg()
        prereg["locked_signal"]["opening_followthrough_threshold"] = 0.002
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("locked_threshold_must_be_0_001", result["blockers"])

    def test_rejects_download_permission(self) -> None:
        prereg = self._load_prereg()
        prereg["guardrails"]["additional_download_allowed"] = True
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("additional_download_allowed_must_be_false", result["blockers"])

    def test_rejects_non_candidate_replay_permission(self) -> None:
        prereg = self._load_prereg()
        prereg["guardrails"]["non_candidate_replay_allowed"] = True
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("non_candidate_replay_allowed_must_be_false", result["blockers"])

    def test_rejects_e2_claim_permission(self) -> None:
        prereg = self._load_prereg()
        prereg["guardrails"]["e2_claim_allowed"] = True
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("e2_claim_allowed_must_be_false", result["blockers"])

    def test_rejects_interpolation(self) -> None:
        prereg = self._load_prereg()
        prereg["exact_replay_design"]["strike_selection_rule"]["interpolation_allowed"] = True
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("interpolation_allowed_must_be_false", result["blockers"])

    @staticmethod
    def _load_prereg() -> dict:
        return json.loads(DEFAULT_PREREG_PATH.read_text(encoding="utf-8"))

    @staticmethod
    def _validate_temp(payload: dict) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prereg.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            return validate_h_a2_post_stress_normalization_control_exact_replay_preregistration(path)


if __name__ == "__main__":
    unittest.main()
