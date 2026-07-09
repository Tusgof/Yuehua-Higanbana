from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_h_a2_exact_data_prioritization_decision import (
    validate_h_a2_exact_data_prioritization_decision,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DECISION_PATH = PROJECT_ROOT / "experiments" / "h_a2_exact_data_prioritization_decision.json"


class ValidateHA2ExactDataPrioritizationDecisionTests(unittest.TestCase):
    def test_current_decision_passes(self) -> None:
        result = validate_h_a2_exact_data_prioritization_decision()

        self.assertEqual("pass", result["status"], result["blockers"])
        self.assertEqual("H-A2", result["hypothesis_id"])
        self.assertEqual("E0", result["evidence_tier"])
        self.assertEqual("draft_narrow_exact_2022_underlying_bar_plan", result["selected_path"])
        self.assertIs(False, result["ibkr_request_allowed"])
        self.assertIs(False, result["paid_data_allowed"])
        self.assertIs(False, result["paper_trading_allowed"])

    def test_rejects_execution_permissions(self) -> None:
        data = json.loads(DECISION_PATH.read_text(encoding="utf-8"))
        data["guardrails"]["ibkr_request_allowed"] = True
        data["guardrails"]["paid_data_allowed"] = True
        data["guardrails"]["paper_trading_allowed"] = True

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "decision.json"
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

            result = validate_h_a2_exact_data_prioritization_decision(path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("ibkr_request_allowed_must_be_false", result["blockers"])
        self.assertIn("paid_data_allowed_must_be_false", result["blockers"])
        self.assertIn("paper_trading_allowed_must_be_false", result["blockers"])

    def test_rejects_missing_hypothesis_first_resolution_logic(self) -> None:
        data = json.loads(DECISION_PATH.read_text(encoding="utf-8"))
        data["data_resolution_logic"]["hypothesis_first_rule"] = "SPY 1-minute bars are mandatory for every H-A2 question."
        data["data_resolution_logic"]["one_minute_bars_not_required_for"] = []

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "decision.json"
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

            result = validate_h_a2_exact_data_prioritization_decision(path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("hypothesis_first_rule_must_demote_data_resolution", result["blockers"])
        self.assertIn("one_minute_bars_not_required_for_must_be_nonempty_list", result["blockers"])


if __name__ == "__main__":
    unittest.main()
