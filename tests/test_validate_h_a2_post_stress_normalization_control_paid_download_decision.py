from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_h_a2_post_stress_normalization_control_paid_download_decision import (
    DEFAULT_DECISION_PATH,
    DEFAULT_ESTIMATE_PATH,
    DEFAULT_PAID_COST_AUDIT_PATH,
    validate_h_a2_post_stress_normalization_control_paid_download_decision,
)


class HA2PostStressNormalizationControlPaidDownloadDecisionTests(unittest.TestCase):
    def test_current_decision_passes(self) -> None:
        result = validate_h_a2_post_stress_normalization_control_paid_download_decision()

        self.assertEqual("pass", result["status"])
        self.assertEqual([], result["blockers"])
        self.assertEqual("post_stress_normalization_control_pack", result["batch_id"])
        self.assertEqual("DATABENTO_API_AI", result["selected_key_env"])
        self.assertEqual(5.558642, result["estimated_download_cost_usd"])
        self.assertEqual(150, result["approved_required_request_count"])
        self.assertEqual(20, result["approved_metadata_group_count"])

    def test_rejects_threshold_change(self) -> None:
        decision = self._load_decision()
        decision["locked_signal_under_validation"]["opening_followthrough_threshold"] = 0.002

        result = self._validate_temp(decision=decision)

        self.assertEqual("blocked", result["status"])
        self.assertIn("threshold_must_remain_0_001", result["blockers"])

    def test_rejects_wrong_selected_key(self) -> None:
        decision = self._load_decision()
        decision["approved_download_scope"]["selected_key_env"] = "DATABENTO_API_MO"

        result = self._validate_temp(decision=decision)

        self.assertEqual("blocked", result["status"])
        self.assertIn("selected_key_env_must_be_databento_api_ai", result["blockers"])

    def test_rejects_source_estimate_mismatch(self) -> None:
        estimate = json.loads(DEFAULT_ESTIMATE_PATH.read_text(encoding="utf-8"))
        estimate["cost_result"]["total_estimated_cost_usd"] = 99.0

        result = self._validate_temp(estimate=estimate)

        self.assertEqual("blocked", result["status"])
        self.assertIn("source_estimated_cost_mismatch", result["blockers"])

    def test_rejects_failed_paid_cost_audit(self) -> None:
        paid_cost = json.loads(DEFAULT_PAID_COST_AUDIT_PATH.read_text(encoding="utf-8"))
        paid_cost["status"] = "blocked"

        result = self._validate_temp(paid_cost=paid_cost)

        self.assertEqual("blocked", result["status"])
        self.assertIn("paid_cost_audit_must_pass", result["blockers"])

    @staticmethod
    def _load_decision() -> dict:
        return json.loads(DEFAULT_DECISION_PATH.read_text(encoding="utf-8"))

    def _validate_temp(
        self,
        decision: dict | None = None,
        estimate: dict | None = None,
        paid_cost: dict | None = None,
    ) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            decision_path = tmp_path / "decision.json"
            estimate_path = tmp_path / "estimate.json"
            paid_cost_path = tmp_path / "paid_cost.json"
            decision_path.write_text(
                json.dumps(decision or self._load_decision(), ensure_ascii=False),
                encoding="utf-8",
            )
            estimate_path.write_text(
                json.dumps(
                    estimate or json.loads(DEFAULT_ESTIMATE_PATH.read_text(encoding="utf-8")),
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            paid_cost_path.write_text(
                json.dumps(
                    paid_cost or json.loads(DEFAULT_PAID_COST_AUDIT_PATH.read_text(encoding="utf-8")),
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            return validate_h_a2_post_stress_normalization_control_paid_download_decision(
                decision_path,
                estimate_path,
                paid_cost_path,
            )


if __name__ == "__main__":
    unittest.main()
