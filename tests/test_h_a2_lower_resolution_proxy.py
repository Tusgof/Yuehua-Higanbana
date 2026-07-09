from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.run_h_a2_lower_resolution_proxy import run_proxy
from scripts.validate_h_a2_lower_resolution_proxy_summary import validate_h_a2_lower_resolution_proxy_summary


class HA2LowerResolutionProxyTests(unittest.TestCase):
    def test_runner_writes_valid_summary_report_and_search_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary_path = root / "summary.json"
            report_path = root / "report.md"
            search_log_path = root / "search.jsonl"

            result = run_proxy(summary_path=summary_path, report_path=report_path, search_log_path=search_log_path)
            validation = validate_h_a2_lower_resolution_proxy_summary(summary_path)

        self.assertEqual("complete", result["status"])
        self.assertEqual("E1", result["evidence_tier"])
        self.assertEqual("pass", validation["status"], validation["blockers"])
        self.assertFalse(result["paid_data_used"])
        self.assertFalse(result["paper_trading_allowed"])
        self.assertEqual(7, result["trial_policy"]["trial_count"])
        self.assertGreater(result["proxy_5m"]["measured_day_count"], 0)
        self.assertGreater(result["proxy_15m"]["measured_day_count"], 0)
        self.assertGreater(result["existing_trade_reconciliation"]["all"]["trade_day_count"], 0)

    def test_validator_rejects_paper_trading_permission(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.json"
            result = run_proxy(summary_path=path, report_path=Path(tmp) / "report.md", search_log_path=Path(tmp) / "search.jsonl")
            result["paper_trading_allowed"] = True
            path.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")

            validation = validate_h_a2_lower_resolution_proxy_summary(path)

        self.assertEqual("blocked", validation["status"])
        self.assertIn("paper_trading_allowed_must_be_false", validation["blockers"])


if __name__ == "__main__":
    unittest.main()
