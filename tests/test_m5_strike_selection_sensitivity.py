from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "run_m5_strike_selection_sensitivity.py"


def load_m5_strike():
    spec = importlib.util.spec_from_file_location("run_m5_strike_selection_sensitivity", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load M5 strike selection module")
    module = importlib.util.module_from_spec(spec)
    sys.modules["run_m5_strike_selection_sensitivity"] = module
    spec.loader.exec_module(module)
    return module


class M5StrikeSelectionSensitivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = load_m5_strike()

    def test_default_scenarios_cover_target_gap_axis(self) -> None:
        scenarios = self.runner.default_scenarios()
        self.assertEqual([0.25, 0.75, 1.25, 1.75, 1.48], [row["target_gap"] for row in scenarios])
        self.assertTrue(all(row["selection_family"] == "moneyness_target_gap" for row in scenarios))

    def test_select_call_vertical_uses_nearest_discrete_strikes(self) -> None:
        legs, mapping = self.runner.select_vertical_legs(option_chain("call"), "call", underlying_price=470.2, target_gap=1.25, width=2.0)
        self.assertEqual([472.0, 474.0], [leg["strike"] for leg in legs])
        self.assertEqual("nearest_discrete_strike_rounding", mapping["mapping_method"])
        self.assertFalse(mapping["interpolation_used"])
        self.assertEqual(1.8, mapping["realized_long_gap"])

    def test_select_put_vertical_uses_nearest_discrete_strikes(self) -> None:
        legs, mapping = self.runner.select_vertical_legs(option_chain("put"), "put", underlying_price=470.8, target_gap=1.25, width=2.0)
        self.assertEqual([470.0, 468.0], [leg["strike"] for leg in legs])
        self.assertEqual(0.8, mapping["realized_long_gap"])

    def test_remap_candidate_day_records_gap_tolerance_breach(self) -> None:
        day = {
            "date": "2024-01-08",
            "direction": "call",
            "orb_signal": {"breakout_close": 470.2, "breakout_timestamp_et": "2024-01-08T09:35:00-05:00"},
            "legs": [],
        }
        quotes = {"2024-01-08T09:35:00-05:00": option_chain("call", timestamp="2024-01-08T09:35:00-05:00")}
        mapped = self.runner.remap_candidate_day(day, quotes, self.runner.scenario("target_gap_1_25_width_2", 1.25))
        self.assertEqual(2, len(mapped["legs"]))
        self.assertTrue(mapped["strike_mapping"]["gap_tolerance_breached"])

    def test_delta_selection_assessment_blocks_missing_greeks(self) -> None:
        assessment = self.runner.delta_selection_assessment()
        self.assertEqual("blocked_missing_greeks", assessment["status"])
        self.assertFalse(assessment["proxy_used"])
        self.assertIn("provider Greeks at decision timestamp, or", assessment["required_before_delta_experiment"])

    def test_search_log_record_preserves_mapping_summary(self) -> None:
        row = {
            "trial_index": 1,
            "scenario_id": "target_gap_0_75_width_2",
            "selection_family": "moneyness_target_gap",
            "target_gap": 0.75,
            "width": 2.0,
            "fee_per_contract": 0.64,
            "fill_model": "half_spread",
            "metrics": {"trade_count": 1, "total_implementable_pnl": 12.0},
            "mapping_summary": {"gap_tolerance_breach_rate": 0.2},
            "sample_adequacy": {"labels": ["under-sampled"]},
        }
        record = self.runner.search_log_record(row)
        self.assertEqual("parameter_search_trial", record["record_type"])
        self.assertEqual(0.75, record["parameters"]["target_gap"])
        self.assertEqual(0.2, record["mapping_summary"]["gap_tolerance_breach_rate"])

    def test_write_search_log_writes_jsonl(self) -> None:
        rows = [
            {
                "trial_index": 1,
                "scenario_id": "target_gap_0_25_width_2",
                "selection_family": "moneyness_target_gap",
                "target_gap": 0.25,
                "width": 2.0,
                "fee_per_contract": 0.64,
                "fill_model": "half_spread",
                "metrics": {"trade_count": 1},
                "mapping_summary": {"gap_tolerance_breach_rate": 0.0},
                "sample_adequacy": {"labels": ["under-sampled"]},
            }
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "search.jsonl"
            self.runner.write_search_log(rows, path)
            lines = path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(1, len(lines))
        self.assertEqual("target_gap_0_25_width_2", json.loads(lines[0])["scenario_id"])


def option_chain(right: str, timestamp: str = "2024-01-03T09:35:00-05:00") -> list[dict]:
    quotes = []
    for strike in [466.0, 468.0, 470.0, 472.0, 474.0]:
        quotes.append(
            {
                "underlying": "SPY",
                "quote_timestamp_et": timestamp,
                "expiration_date": timestamp[:10],
                "right": right,
                "strike": strike,
                "bid": max(0.01, 5.0 - abs(strike - 470.0) * 0.4),
                "ask": max(0.02, 5.2 - abs(strike - 470.0) * 0.4),
            }
        )
    return quotes


if __name__ == "__main__":
    unittest.main()
