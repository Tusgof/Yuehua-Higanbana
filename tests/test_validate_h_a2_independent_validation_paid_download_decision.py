from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_h_a2_independent_validation_paid_download_decision import (
    validate_h_a2_independent_validation_paid_download_decision,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ValidateHA2IndependentValidationPaidDownloadDecisionTests(unittest.TestCase):
    def test_current_decision_artifact_passes(self) -> None:
        result = validate_h_a2_independent_validation_paid_download_decision()

        self.assertEqual("pass", result["status"])
        self.assertEqual("sample_cost_probe_high_vix_one_day", result["batch_id"])
        self.assertEqual(["2025-04-08"], result["selected_dates"])
        self.assertEqual(15, result["approved_request_count"])
        self.assertEqual(0.504662, result["estimated_download_cost_usd"])
        self.assertEqual(120.494368, result["projected_used_after_download_usd"])

    def test_blocks_scope_expansion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            decision_path = Path(tmp) / "decision.json"
            decision = json.loads(
                (PROJECT_ROOT / "experiments" / "h_a2_independent_validation_paid_download_decision.json").read_text(
                    encoding="utf-8"
                )
            )
            decision["selected_batch"]["dates"] = ["2025-04-08", "2025-04-09"]
            decision["approved_download_scope"]["request_count"] = 30
            decision["forbidden_actions"] = []
            decision_path.write_text(json.dumps(decision), encoding="utf-8")

            result = validate_h_a2_independent_validation_paid_download_decision(decision_path=decision_path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("selected_dates_must_be_2025_04_08_only", result["blockers"])
        self.assertIn("approved_request_count_must_be_15", result["blockers"])
        self.assertIn("missing_forbidden_action:Do not download any date other than 2025-04-08", result["blockers"])

    def test_blocks_threshold_change_or_e2_like_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            decision_path = Path(tmp) / "decision.json"
            decision = json.loads(
                (PROJECT_ROOT / "experiments" / "h_a2_independent_validation_paid_download_decision.json").read_text(
                    encoding="utf-8"
                )
            )
            decision["locked_signal_under_validation"]["opening_followthrough_threshold"] = 0.002
            decision["guardrails"]["paper_trading_allowed"] = True
            decision["guardrails"]["real_money_allowed"] = True
            decision_path.write_text(json.dumps(decision), encoding="utf-8")

            result = validate_h_a2_independent_validation_paid_download_decision(decision_path=decision_path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("threshold_must_remain_0_001", result["blockers"])
        self.assertIn("paper_trading_allowed_must_be_false", result["blockers"])
        self.assertIn("real_money_allowed_must_be_false", result["blockers"])


if __name__ == "__main__":
    unittest.main()
