from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_h_a2_post_two_exact_replay_decision import (
    DEFAULT_DECISION_PATH,
    validate_h_a2_post_two_exact_replay_decision,
)


class H_A2PostTwoExactReplayDecisionTests(unittest.TestCase):
    def test_current_decision_passes(self) -> None:
        result = validate_h_a2_post_two_exact_replay_decision()

        self.assertEqual("pass", result["status"])
        self.assertEqual([], result["blockers"])
        self.assertEqual("H-A2", result["hypothesis_id"])
        self.assertEqual("E0", result["evidence_tier"])
        self.assertEqual("h_a2_post_two_exact_replay_decision", result["experiment_id"])
        self.assertEqual("revise_h_a2_mechanism_before_more_sample_expansion", result["selected_next_step"])
        self.assertEqual(2, result["candidate_count"])
        self.assertEqual(-50.0, result["total_mid_pnl"])
        self.assertEqual(-59.12, result["total_implementable_pnl"])
        self.assertFalse(result["paid_data_allowed"])
        self.assertFalse(result["exact_replay_allowed"])
        self.assertFalse(result["paper_trading_allowed"])

    def test_rejects_source_pnl_mismatch(self) -> None:
        decision = self._load_decision()
        decision["source_result_summary"]["candidate_results"][1]["implementable_pnl"] = 10.0
        result = self._validate_temp(decision)

        self.assertEqual("blocked", result["status"])
        self.assertIn(
            "source_summary_mismatch:h_a2_post_stress_normalization_control_exact_replay:implementable_pnl",
            result["blockers"],
        )

    def test_rejects_data_expansion_as_next_step(self) -> None:
        decision = self._load_decision()
        decision["decision"]["selected_next_step"] = "buy_more_data"
        result = self._validate_temp(decision)

        self.assertEqual("blocked", result["status"])
        self.assertIn("selected_next_step_must_be_mechanism_revision", result["blockers"])

    def test_rejects_threshold_search_permission(self) -> None:
        decision = self._load_decision()
        decision["guardrails"]["threshold_search_allowed"] = True
        result = self._validate_temp(decision)

        self.assertEqual("blocked", result["status"])
        self.assertIn("threshold_search_allowed_must_be_false", result["blockers"])

    def test_rejects_paper_trading_permission(self) -> None:
        decision = self._load_decision()
        decision["guardrails"]["paper_trading_allowed"] = True
        result = self._validate_temp(decision)

        self.assertEqual("blocked", result["status"])
        self.assertIn("paper_trading_allowed_must_be_false", result["blockers"])

    @staticmethod
    def _load_decision() -> dict:
        return json.loads(DEFAULT_DECISION_PATH.read_text(encoding="utf-8-sig"))

    @staticmethod
    def _validate_temp(payload: dict) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "decision.json"
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            return validate_h_a2_post_two_exact_replay_decision(path)


if __name__ == "__main__":
    unittest.main()
