from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.run_h_a2_locked_condition_signal_attribution import run_audit
from scripts.validate_h_a2_locked_condition_signal_attribution import (
    DEFAULT_SUMMARY_PATH,
    validate_h_a2_locked_condition_signal_attribution,
)


class H_A2LockedConditionSignalAttributionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        run_audit()

    def test_current_summary_passes(self) -> None:
        result = validate_h_a2_locked_condition_signal_attribution()

        self.assertEqual("pass", result["status"])
        self.assertEqual([], result["blockers"])
        self.assertEqual("E1", result["evidence_tier"])
        self.assertEqual("ยังสรุปไม่ได้", result["conclusion"])
        self.assertEqual(0.001, result["locked_threshold"])
        self.assertEqual("delayed_entry_candidate_and_diagnostic_proxy_only", result["classification"])

    def test_summary_preserves_no_search_guardrails(self) -> None:
        payload = json.loads(DEFAULT_SUMMARY_PATH.read_text(encoding="utf-8"))

        self.assertFalse(payload["trial_policy"]["threshold_search_used"])
        self.assertFalse(payload["trial_policy"]["new_filter_search_used"])
        self.assertFalse(payload["trial_policy"]["oos_tuning_used"])
        self.assertFalse(payload["paper_trading_allowed"])
        self.assertFalse(payload["real_money_allowed"])

    def test_rejects_deployable_entry_claim(self) -> None:
        payload = json.loads(DEFAULT_SUMMARY_PATH.read_text(encoding="utf-8"))
        payload["entry_rule_classification"]["deployable_entry_filter_allowed"] = True
        result = self._validate_temp(payload)

        self.assertEqual("blocked", result["status"])
        self.assertIn("deployable_entry_filter_must_be_false", result["blockers"])

    def test_rejects_threshold_change(self) -> None:
        payload = json.loads(DEFAULT_SUMMARY_PATH.read_text(encoding="utf-8"))
        payload["locked_threshold"] = 0.002
        result = self._validate_temp(payload)

        self.assertEqual("blocked", result["status"])
        self.assertIn("locked_threshold_must_be_0_001", result["blockers"])

    @staticmethod
    def _validate_temp(payload: dict) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            return validate_h_a2_locked_condition_signal_attribution(path)


if __name__ == "__main__":
    unittest.main()
