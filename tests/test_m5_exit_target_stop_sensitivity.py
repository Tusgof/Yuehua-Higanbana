from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "run_m5_exit_target_stop_sensitivity.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("run_m5_exit_target_stop_sensitivity", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load M5.4 exit target/stop module")
    module = importlib.util.module_from_spec(spec)
    sys.modules["run_m5_exit_target_stop_sensitivity"] = module
    spec.loader.exec_module(module)
    return module


class M5ExitTargetStopSensitivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = load_runner()

    def test_default_scenarios_cover_forced_close_and_tp_sl_grid(self) -> None:
        scenarios = self.runner.default_scenarios()

        self.assertEqual(7, len(scenarios))
        self.assertEqual("forced_close_only_control", scenarios[0]["scenario_id"])
        self.assertIn(0.25, {row["profit_target_pct"] for row in scenarios})
        self.assertIn(0.50, {row["stop_loss_pct"] for row in scenarios})
        self.assertIn(1.00, {row["profit_target_pct"] for row in scenarios})

    def test_find_exit_hits_profit_target_before_forced_close(self) -> None:
        legs = vertical_legs()
        quotes_by_key = {}
        for timestamp, long_bid, long_ask, short_bid, short_ask in [
            ("2024-01-08T09:35:00-05:00", 1.00, 1.20, 0.40, 0.50),
            ("2024-01-08T09:36:00-05:00", 1.50, 1.60, 0.45, 0.55),
            ("2024-01-08T15:45:00-05:00", 0.10, 0.12, 0.01, 0.02),
        ]:
            quotes_by_key[(timestamp, "call", 100.0, "2024-01-08")] = quote(timestamp, "call", 100.0, long_bid, long_ask)
            quotes_by_key[(timestamp, "call", 102.0, "2024-01-08")] = quote(timestamp, "call", 102.0, short_bid, short_ask)

        result = self.runner.find_exit_with_thresholds(
            quotes_by_key,
            "2024-01-08",
            "2024-01-08T09:35:00-05:00",
            "2024-01-08T15:45:00-05:00",
            legs,
            entry_debit=0.70,
            scenario_def=self.runner.scenario("tp_25_stop_50_baseline", 0.25, 0.50),
        )

        self.assertEqual("profit_target_25pct", result["exit_reason"])
        self.assertEqual({"long": "2024-01-08T09:36:00-05:00", "short": "2024-01-08T09:36:00-05:00"}, result["close_timestamps_by_leg_id"])

    def test_search_log_record_preserves_tp_sl_parameters(self) -> None:
        row = {
            "trial_index": 2,
            "scenario_id": "tp_10_stop_25",
            "profit_target_pct": 0.10,
            "stop_loss_pct": 0.25,
            "fill_model": "half_spread",
            "fee_per_contract": 0.64,
            "close_fallback": "nearest_1545_window",
            "metrics": {"trade_count": 1, "total_implementable_pnl": 12.0},
            "sample_adequacy": {"labels": ["under-sampled"]},
        }

        record = self.runner.search_log_record(row)

        self.assertEqual("m5_exit_target_stop_sensitivity", record["experiment_id"])
        self.assertEqual(0.10, record["parameters"]["profit_target_pct"])
        self.assertEqual(0.25, record["parameters"]["stop_loss_pct"])

    def test_write_search_log_writes_all_trials(self) -> None:
        rows = [
            {
                "trial_index": 1,
                "scenario_id": "forced_close_only_control",
                "profit_target_pct": None,
                "stop_loss_pct": None,
                "fill_model": "half_spread",
                "fee_per_contract": 0.64,
                "close_fallback": "nearest_1545_window",
                "metrics": {"trade_count": 1},
                "sample_adequacy": {"labels": ["under-sampled"]},
            },
            {
                "trial_index": 2,
                "scenario_id": "tp_25_stop_50_baseline",
                "profit_target_pct": 0.25,
                "stop_loss_pct": 0.50,
                "fill_model": "half_spread",
                "fee_per_contract": 0.64,
                "close_fallback": "nearest_1545_window",
                "metrics": {"trade_count": 1},
                "sample_adequacy": {"labels": ["under-sampled"]},
            },
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "search.jsonl"
            self.runner.write_search_log(rows, path)
            lines = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(2, len(lines))
        self.assertIsNone(lines[0]["parameters"]["profit_target_pct"])
        self.assertEqual("tp_25_stop_50_baseline", lines[1]["scenario_id"])


def vertical_legs() -> list[dict]:
    return [
        {"leg_id": "long", "side": "buy", "quantity": 1, "right": "call", "strike": 100.0, "expiration_date": "2024-01-08"},
        {"leg_id": "short", "side": "sell", "quantity": 1, "right": "call", "strike": 102.0, "expiration_date": "2024-01-08"},
    ]


def quote(timestamp: str, right: str, strike: float, bid: float, ask: float) -> dict:
    return {
        "underlying": "SPY",
        "expiration_date": timestamp[:10],
        "quote_timestamp_et": timestamp,
        "right": right,
        "strike": strike,
        "bid": bid,
        "ask": ask,
    }


if __name__ == "__main__":
    unittest.main()
