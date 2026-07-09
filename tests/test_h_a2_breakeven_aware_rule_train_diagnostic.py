from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.run_h_a2_breakeven_aware_rule_train_diagnostic import (
    run_h_a2_breakeven_aware_rule_train_diagnostic,
)
from scripts.validate_h_a2_breakeven_aware_rule_train_diagnostic import (
    DEFAULT_SUMMARY_PATH,
    validate_h_a2_breakeven_aware_rule_train_diagnostic,
)


class H_A2BreakevenAwareRuleTrainDiagnosticTests(unittest.TestCase):
    def test_runner_builds_expected_diagnostic(self) -> None:
        summary = run_h_a2_breakeven_aware_rule_train_diagnostic()

        self.assertEqual("h_a2_breakeven_aware_rule_train_diagnostic", summary["experiment_id"])
        self.assertEqual("complete", summary["status"])
        self.assertEqual("E1", summary["evidence_tier"])
        self.assertEqual("ยังสรุปไม่ได้", summary["conclusion"])
        self.assertEqual(
            "blocked_true_breakeven_rule_lock",
            summary["decision_time_feature_audit"]["status"],
        )
        self.assertFalse(
            summary["decision_time_feature_audit"]["can_lock_true_breakeven_aware_rule_from_current_artifacts"]
        )
        self.assertEqual(
            "defined_but_not_computable_for_train_distribution",
            summary["cost_adjusted_strike_reachability_target"]["status"],
        )
        self.assertEqual(0, summary["cost_adjusted_strike_reachability_target"]["exact_replay_target_reached_count"])
        self.assertGreaterEqual(len(summary["train_only_candidate_rule_trials"]), 2)
        self.assertEqual("write_targeted_data_regime_expansion_plan", summary["decision"]["decision"])
        self.assertFalse(summary["guardrails"]["paid_data_used"])
        self.assertFalse(summary["guardrails"]["oos_tuning_used"])
        self.assertFalse(summary["guardrails"]["paper_trading_allowed"])
        self.assertTrue(summary["research_log_required"])

    def test_current_summary_passes_validator(self) -> None:
        result = validate_h_a2_breakeven_aware_rule_train_diagnostic()

        self.assertEqual("pass", result["status"])
        self.assertEqual([], result["blockers"])
        self.assertEqual("h_a2_breakeven_aware_rule_train_diagnostic", result["experiment_id"])
        self.assertEqual("write_targeted_data_regime_expansion_plan", result["decision"])
        self.assertFalse(result["paid_data_used"])
        self.assertFalse(result["paper_trading_allowed"])

    def test_validator_rejects_paid_data(self) -> None:
        payload = self._load_summary()
        payload["guardrails"]["paid_data_used"] = True
        result = self._validate_temp(payload)

        self.assertEqual("blocked", result["status"])
        self.assertIn("paid_data_used_must_be_false", result["blockers"])

    def test_validator_rejects_true_rule_lock_from_current_artifacts(self) -> None:
        payload = self._load_summary()
        payload["decision_time_feature_audit"]["can_lock_true_breakeven_aware_rule_from_current_artifacts"] = True
        result = self._validate_temp(payload)

        self.assertEqual("blocked", result["status"])
        self.assertIn("must_not_lock_true_rule_from_current_artifacts", result["blockers"])

    def test_validator_rejects_selected_trial(self) -> None:
        payload = self._load_summary()
        payload["train_only_candidate_rule_trials"][0]["selected_for_trading"] = True
        result = self._validate_temp(payload)

        self.assertEqual("blocked", result["status"])
        self.assertIn("trial_must_not_be_selected_for_trading:train_baseline_non_risk", result["blockers"])

    @staticmethod
    def _load_summary() -> dict:
        return json.loads(DEFAULT_SUMMARY_PATH.read_text(encoding="utf-8-sig"))

    @staticmethod
    def _validate_temp(payload: dict) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.json"
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            return validate_h_a2_breakeven_aware_rule_train_diagnostic(path)


if __name__ == "__main__":
    unittest.main()
