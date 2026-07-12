from __future__ import annotations

import unittest
from unittest.mock import patch

from lib.orb import opening_breakout
from scripts.run_h_a2_2022_10_stress_exact_replay import run
from scripts.validate_h_a2_2022_10_stress_exact_replay_preregistration import validate


class H_A2StressExactReplayTests(unittest.TestCase):
    def test_preregistration_passes_and_forbids_lookahead(self) -> None:
        self.assertEqual("pass", validate()["status"])

    def test_opening_breakout_uses_only_decision_time_rows(self) -> None:
        bars = [
            {"timestamp_et": "2022-10-03T09:30:00-04:00", "high": 100, "low": 99, "close": 99.5},
            {"timestamp_et": "2022-10-03T09:34:00-04:00", "high": 101, "low": 99.5, "close": 100},
            {"timestamp_et": "2022-10-03T09:35:00-04:00", "high": 102, "low": 101, "close": 101.5},
            {"timestamp_et": "2022-10-03T15:45:00-04:00", "high": 50, "low": 49, "close": 49.5},
        ]
        result = opening_breakout(bars)
        self.assertEqual("call", result["direction"])
        self.assertNotIn("15:45", result["decision_timestamp_et"])

    @patch("scripts.run_h_a2_2022_10_stress_exact_replay.write_jsonl")
    @patch("scripts.run_h_a2_2022_10_stress_exact_replay.REPORT")
    @patch("scripts.run_h_a2_2022_10_stress_exact_replay.write_json")
    @patch("scripts.run_h_a2_2022_10_stress_exact_replay.load_macro_events_by_date", return_value={})
    @patch("scripts.run_h_a2_2022_10_stress_exact_replay.load_vix_vxv", return_value=[])
    @patch("scripts.run_h_a2_2022_10_stress_exact_replay.load_jsonl", return_value=[])
    @patch("scripts.run_h_a2_2022_10_stress_exact_replay.load_json")
    def test_summary_names_required_research_log(self, load_json_mock, *_mocks) -> None:
        load_json_mock.side_effect = [
            {
                "trade_density_checkpoint": {
                    "minimum_candidate_trades_for_september_stage": 2,
                }
            },
            {"october_stress_dates": []},
        ]
        summary = run()
        self.assertTrue(summary["research_log_required"])
        self.assertEqual(
            "higanbana-h-a2-october-2022-stress-exact-replay",
            summary["research_log_slug"],
        )


if __name__ == "__main__":
    unittest.main()
