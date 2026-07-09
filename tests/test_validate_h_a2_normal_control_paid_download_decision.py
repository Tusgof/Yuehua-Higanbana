from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_h_a2_normal_control_paid_download_decision import (
    validate_h_a2_normal_control_paid_download_decision,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ValidateHA2NormalControlPaidDownloadDecisionTests(unittest.TestCase):
    def test_current_decision_artifact_passes(self) -> None:
        result = validate_h_a2_normal_control_paid_download_decision()

        self.assertEqual("pass", result["status"])
        self.assertEqual("low_normal_vix_control_pack", result["batch_id"])
        self.assertEqual(10, len(result["selected_dates"]))
        self.assertEqual(150, result["approved_required_request_count"])
        self.assertEqual(20, result["approved_metadata_group_count"])
        self.assertEqual(5.398913, result["estimated_download_cost_usd"])
        self.assertEqual(5.398913, result["projected_selected_key_usage_if_downloaded_usd"])

    def test_blocks_scope_expansion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            decision_path = Path(tmp) / "decision.json"
            decision = json.loads(
                (PROJECT_ROOT / "experiments" / "h_a2_normal_control_paid_download_decision.json").read_text(
                    encoding="utf-8"
                )
            )
            decision["selected_batch"]["dates"].append("2025-02-18")
            decision["approved_download_scope"]["planned_required_request_count"] = 165
            decision["forbidden_actions"] = []
            decision_path.write_text(json.dumps(decision), encoding="utf-8")

            result = validate_h_a2_normal_control_paid_download_decision(decision_path=decision_path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("selected_dates_must_match_low_normal_control_pack", result["blockers"])
        self.assertIn("approved_required_request_count_must_be_150", result["blockers"])
        self.assertIn(
            "missing_forbidden_action:Do not download any date outside 2025-02-03 through 2025-02-14",
            result["blockers"],
        )

    def test_blocks_threshold_change_or_e2_like_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            decision_path = Path(tmp) / "decision.json"
            decision = json.loads(
                (PROJECT_ROOT / "experiments" / "h_a2_normal_control_paid_download_decision.json").read_text(
                    encoding="utf-8"
                )
            )
            decision["locked_signal_under_validation"]["opening_followthrough_threshold"] = 0.002
            decision["guardrails"]["paper_trading_allowed"] = True
            decision["guardrails"]["real_money_allowed"] = True
            decision_path.write_text(json.dumps(decision), encoding="utf-8")

            result = validate_h_a2_normal_control_paid_download_decision(decision_path=decision_path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("threshold_must_remain_0_001", result["blockers"])
        self.assertIn("paper_trading_allowed_must_be_false", result["blockers"])
        self.assertIn("real_money_allowed_must_be_false", result["blockers"])

    def test_blocks_selected_key_pool_breach(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            decision_path = Path(tmp) / "decision.json"
            decision = json.loads(
                (PROJECT_ROOT / "experiments" / "h_a2_normal_control_paid_download_decision.json").read_text(
                    encoding="utf-8"
                )
            )
            decision["cost_guard"]["projected_selected_key_usage_if_downloaded_usd"] = 100.0
            decision_path.write_text(json.dumps(decision), encoding="utf-8")

            result = validate_h_a2_normal_control_paid_download_decision(decision_path=decision_path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("projected_selected_key_usage_must_remain_below_cap", result["blockers"])


if __name__ == "__main__":
    unittest.main()
