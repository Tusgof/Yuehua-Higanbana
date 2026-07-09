from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_h_a2_lower_resolution_proxy_preregistration import (
    validate_h_a2_lower_resolution_proxy_preregistration,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PREREG_PATH = PROJECT_ROOT / "experiments" / "h_a2_lower_resolution_proxy_preregistration.json"


class ValidateHA2LowerResolutionProxyPreregistrationTests(unittest.TestCase):
    def test_current_preregistration_passes(self) -> None:
        result = validate_h_a2_lower_resolution_proxy_preregistration()

        self.assertEqual("pass", result["status"], result["blockers"])
        self.assertEqual("H-A2", result["hypothesis_id"])
        self.assertEqual("E0", result["evidence_tier"])
        self.assertEqual("h_a2_lower_resolution_proxy", result["experiment_id"])
        self.assertIs(False, result["network_allowed"])
        self.assertIs(False, result["paid_data_allowed"])
        self.assertIs(False, result["paper_trading_allowed"])
        self.assertEqual(3, result["planned_proxy_test_count"])

    def test_rejects_exact_backtest_without_1_minute_requirement(self) -> None:
        data = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
        data["minimum_data_resolution"]["exact_backtest"]["one_minute_required"] = False
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prereg.json"
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

            result = validate_h_a2_lower_resolution_proxy_preregistration(path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("exact_backtest_must_require_1_minute", result["blockers"])

    def test_rejects_random_split_or_oos_tuning(self) -> None:
        data = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
        data["split_policy"]["random_split_forbidden"] = False
        data["split_policy"]["oos_tuning_forbidden"] = False
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prereg.json"
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

            result = validate_h_a2_lower_resolution_proxy_preregistration(path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("random_split_forbidden_must_be_true", result["blockers"])
        self.assertIn("oos_tuning_forbidden_must_be_true", result["blockers"])

    def test_rejects_paid_data_or_paper_trading_permission(self) -> None:
        data = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
        data["guardrails"]["paid_data_allowed"] = True
        data["guardrails"]["paper_trading_allowed"] = True
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prereg.json"
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

            result = validate_h_a2_lower_resolution_proxy_preregistration(path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("paid_data_allowed_must_be_false", result["blockers"])
        self.assertIn("paper_trading_allowed_must_be_false", result["blockers"])


if __name__ == "__main__":
    unittest.main()
