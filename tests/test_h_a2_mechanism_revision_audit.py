from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.run_h_a2_mechanism_revision_audit import run_h_a2_mechanism_revision_audit
from scripts.validate_h_a2_mechanism_revision_audit import (
    DEFAULT_SUMMARY_PATH,
    validate_h_a2_mechanism_revision_audit,
)


class H_A2MechanismRevisionAuditTests(unittest.TestCase):
    def test_runner_builds_expected_mechanism_findings(self) -> None:
        summary = run_h_a2_mechanism_revision_audit()

        self.assertEqual("h_a2_mechanism_revision_audit", summary["experiment_id"])
        self.assertEqual("complete", summary["status"])
        self.assertEqual("E1", summary["evidence_tier"])
        self.assertEqual("ยังสรุปไม่ได้", summary["conclusion"])
        self.assertEqual("preregister_train_only_revised_rule", summary["decision"]["selected_next_step"])
        self.assertEqual(-50.0, summary["aggregate_findings"]["total_mid_pnl"])
        self.assertEqual(-59.12, summary["aggregate_findings"]["total_implementable_pnl"])
        self.assertEqual(9.12, summary["aggregate_findings"]["total_cost_drag_vs_mid"])
        self.assertEqual(2, summary["aggregate_findings"]["directionally_correct_underlying_count"])
        self.assertEqual(2, summary["aggregate_findings"]["long_strike_not_reached_count"])
        self.assertTrue(summary["aggregate_findings"]["direction_signal_not_sufficient"])
        self.assertTrue(summary["research_log_required"])
        self.assertFalse(summary["guardrails"]["paid_data_used"])
        self.assertFalse(summary["guardrails"]["exact_replay_expansion_used"])

    def test_current_audit_passes_validator(self) -> None:
        result = validate_h_a2_mechanism_revision_audit()

        self.assertEqual("pass", result["status"])
        self.assertEqual([], result["blockers"])
        self.assertEqual("h_a2_mechanism_revision_audit", result["experiment_id"])
        self.assertEqual("E1", result["evidence_tier"])
        self.assertEqual("preregister_train_only_revised_rule", result["decision"])
        self.assertFalse(result["paid_data_used"])
        self.assertFalse(result["exact_replay_expansion_used"])
        self.assertFalse(result["paper_trading_allowed"])

    def test_validator_rejects_paid_data_usage(self) -> None:
        payload = self._load_summary()
        payload["guardrails"]["paid_data_used"] = True
        result = self._validate_temp(payload)

        self.assertEqual("blocked", result["status"])
        self.assertIn("paid_data_used_must_be_false", result["blockers"])

    def test_validator_rejects_missing_strike_reachability(self) -> None:
        payload = self._load_summary()
        payload["aggregate_findings"]["long_strike_not_reached_count"] = 1
        result = self._validate_temp(payload)

        self.assertEqual("blocked", result["status"])
        self.assertIn("long_strike_not_reached_count_must_be_2", result["blockers"])

    @staticmethod
    def _load_summary() -> dict:
        return json.loads(DEFAULT_SUMMARY_PATH.read_text(encoding="utf-8-sig"))

    @staticmethod
    def _validate_temp(payload: dict) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.json"
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            return validate_h_a2_mechanism_revision_audit(path)


if __name__ == "__main__":
    unittest.main()
