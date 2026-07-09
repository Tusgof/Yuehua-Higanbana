from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_h_a2_breakeven_aware_rule_preregistration import (
    DEFAULT_PREREG_PATH,
    validate_h_a2_breakeven_aware_rule_preregistration,
)


class H_A2BreakevenAwareRulePreregistrationTests(unittest.TestCase):
    def test_current_preregistration_passes(self) -> None:
        result = validate_h_a2_breakeven_aware_rule_preregistration()

        self.assertEqual("pass", result["status"])
        self.assertEqual([], result["blockers"])
        self.assertEqual("H-A2", result["hypothesis_id"])
        self.assertEqual("E0", result["evidence_tier"])
        self.assertEqual("h_a2_breakeven_aware_rule_preregistration", result["experiment_id"])
        self.assertEqual("h_a2_breakeven_aware_rule_train_diagnostic", result["planned_next_diagnostic"])
        self.assertEqual("local_no_paid_train_only_diagnostic", result["planned_next_mode"])
        self.assertFalse(result["paid_data_allowed"])
        self.assertFalse(result["exact_replay_expansion_allowed"])
        self.assertFalse(result["paper_trading_allowed"])

    def test_rejects_future_followthrough_as_allowed_input(self) -> None:
        prereg = self._load_prereg()
        prereg["revised_hypothesis"]["allowed_decision_time_inputs"].append(
            "future_post_entry_followthrough_to_close"
        )
        prereg["revised_hypothesis"]["forbidden_live_inputs"].remove(
            "future_post_entry_followthrough_to_close"
        )
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("forbidden_live_input_missing:future_post_entry_followthrough_to_close", result["blockers"])

    def test_rejects_oos_tuning_permission(self) -> None:
        prereg = self._load_prereg()
        prereg["anti_overfitting_controls"]["oos_tuning_allowed"] = True
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("oos_tuning_allowed_must_be_false", result["blockers"])

    def test_rejects_paid_data_permission(self) -> None:
        prereg = self._load_prereg()
        prereg["guardrails"]["paid_data_allowed"] = True
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("paid_data_allowed_must_be_false", result["blockers"])

    def test_rejects_missing_strike_reachability_dimension(self) -> None:
        prereg = self._load_prereg()
        prereg["rule_family_to_preregister"]["candidate_rule_dimensions"] = [
            item
            for item in prereg["rule_family_to_preregister"]["candidate_rule_dimensions"]
            if item["dimension"] != "strike_reachability_margin"
        ]
        result = self._validate_temp(prereg)

        self.assertEqual("blocked", result["status"])
        self.assertIn("rule_dimension_role_mismatch:strike_reachability_margin", result["blockers"])

    @staticmethod
    def _load_prereg() -> dict:
        return json.loads(DEFAULT_PREREG_PATH.read_text(encoding="utf-8-sig"))

    @staticmethod
    def _validate_temp(payload: dict) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prereg.json"
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            return validate_h_a2_breakeven_aware_rule_preregistration(path)


if __name__ == "__main__":
    unittest.main()
