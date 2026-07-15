from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from lib.databento import estimate_requests, provider_args
from scripts.run_h_a2_orb_0936_download import build_cost_report, build_requests, evaluate_cost_gate
from scripts.validate_h_a2_orb_0936_paid_download_decision import DEFAULT_PATH, validate


class HA2ORB0936PaidDownloadTests(unittest.TestCase):
    def test_committed_decision_passes(self) -> None:
        result = validate()

        self.assertEqual("pass", result["status"], result["blockers"])

    def test_rejects_scope_or_approval_drift(self) -> None:
        payload = json.loads(DEFAULT_PATH.read_text(encoding="utf-8"))
        payload["approved_scope"]["dates"] = payload["approved_scope"]["dates"][:-1]
        payload["authorization"]["user_approval_recorded"] = False
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "decision.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = validate(path)

        self.assertIn("approved_dates_must_match_cost_plan", result["blockers"])
        self.assertIn("user_approval_must_be_recorded", result["blockers"])

    def test_build_requests_locks_40_intraday_and_one_daily_request(self) -> None:
        decision = json.loads(DEFAULT_PATH.read_text(encoding="utf-8"))
        requests = build_requests(decision, Path("raw"))

        self.assertEqual(41, len(requests))
        self.assertEqual(20, sum(row["schema"] == "cbbo-1m" for row in requests))
        self.assertEqual(20, sum(row["schema"] == "ohlcv-1m" for row in requests))
        self.assertEqual(1, sum(row["schema"] == "ohlcv-1d" for row in requests))
        self.assertEqual("2026-04-27T13:30:00+00:00", requests[0]["start"])
        self.assertEqual("2026-03-01", requests[-1]["start"])
        self.assertEqual("2026-06-05", requests[-1]["end"])

    def test_cost_gate_checks_ceiling_and_cumulative_key_cap(self) -> None:
        decision = json.loads(DEFAULT_PATH.read_text(encoding="utf-8"))

        self.assertEqual("pass", evaluate_cost_gate(decision, 10.0, 41, [])["status"])
        self.assertIn(
            "estimated_cost_exceeds_approved_ceiling",
            evaluate_cost_gate(decision, 15.0, 41, [])["blockers"],
        )
        decision["cost_guard"]["known_committed_selected_key_usage_usd"] = 45.0
        self.assertIn(
            "projected_cumulative_usage_exceeds_selected_key_cap",
            evaluate_cost_gate(decision, 10.0, 41, [])["blockers"],
        )

    def test_cost_helpers_are_hermetic(self) -> None:
        request = {
            "dataset": "EQUS.MINI",
            "symbols": ["SPY"],
            "schema": "ohlcv-1d",
            "stype_in": "raw_symbol",
            "start": "2026-03-01",
            "end": "2026-06-05",
            "window": "daily",
        }
        rows, errors = estimate_requests([request], lambda _: 0.01)
        decision = json.loads(DEFAULT_PATH.read_text(encoding="utf-8"))
        decision["approved_scope"]["request_count"] = 1
        report = build_cost_report(decision, rows, errors)

        self.assertEqual("pass", report["status"])
        self.assertEqual(0.01, report["total_estimated_cost_usd"])
        self.assertNotIn("raw_path", provider_args(request))


if __name__ == "__main__":
    unittest.main()
