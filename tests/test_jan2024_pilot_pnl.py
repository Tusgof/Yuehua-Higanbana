from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "run_jan2024_pilot_pnl.py"


def load_pnl():
    spec = importlib.util.spec_from_file_location("run_jan2024_pilot_pnl", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load pilot PnL module")
    module = importlib.util.module_from_spec(spec)
    sys.modules["run_jan2024_pilot_pnl"] = module
    spec.loader.exec_module(module)
    return module


class Jan2024PilotPnlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pnl = load_pnl()

    def test_liquidation_price_uses_bid_for_long_and_ask_for_short(self) -> None:
        quote = {"bid": 1.2, "ask": 1.4}
        self.assertEqual(1.2, self.pnl.liquidation_price(quote, "buy"))
        self.assertEqual(1.4, self.pnl.liquidation_price(quote, "sell"))

    def test_candidate_day_skips_when_close_quote_missing(self) -> None:
        day = candidate_day()
        quotes = self.pnl.index_quotes(
            [
                quote("2024-01-08T09:35:00-05:00", "call", 470.0, 1.0, 1.2),
                quote("2024-01-08T09:35:00-05:00", "call", 472.0, 0.4, 0.6),
            ]
        )
        result = self.pnl.evaluate_candidate_day(day, quotes, fee_per_contract=0.0)
        self.assertEqual("missing_quotes", result["status"])
        self.assertIn("close call 470.0", result["reasons"][0])

    def test_candidate_day_skips_when_entry_quote_missing(self) -> None:
        day = candidate_day()
        quotes = self.pnl.index_quotes(
            [
                quote("2024-01-08T09:35:00-05:00", "call", 470.0, 1.0, 1.2),
                quote("2024-01-08T15:45:00-05:00", "call", 470.0, 2.0, 2.2),
                quote("2024-01-08T15:45:00-05:00", "call", 472.0, 0.9, 1.1),
            ]
        )
        result = self.pnl.evaluate_candidate_day(day, quotes, fee_per_contract=0.0)
        self.assertEqual("missing_quotes", result["status"])
        self.assertIn("entry call 472.0", result["reasons"][0])

    def test_candidate_day_calculates_forced_close_pnl(self) -> None:
        day = candidate_day()
        quotes = self.pnl.index_quotes(
            [
                quote("2024-01-08T09:35:00-05:00", "call", 470.0, 1.0, 1.2),
                quote("2024-01-08T09:35:00-05:00", "call", 472.0, 0.4, 0.6),
                quote("2024-01-08T15:45:00-05:00", "call", 470.0, 2.0, 2.2),
                quote("2024-01-08T15:45:00-05:00", "call", 472.0, 0.9, 1.1),
            ]
        )
        result = self.pnl.evaluate_candidate_day(day, quotes, fee_per_contract=0.0)
        self.assertEqual("closed_forced_1545", result["status"])
        self.assertEqual(30.0, result["gross_pnl"])
        self.assertEqual(50.0, result["mid_pnl"])
        self.assertEqual(30.0, result["implementable_pnl"])
        self.assertEqual(20.0, result["cost_drag"])
        self.assertEqual(60.0, result["max_defined_loss"])

    def test_fill_stress_changes_entry_price(self) -> None:
        day = candidate_day()
        quotes = self.pnl.index_quotes(
            [
                quote("2024-01-08T09:35:00-05:00", "call", 470.0, 1.0, 1.2),
                quote("2024-01-08T09:35:00-05:00", "call", 472.0, 0.4, 0.6),
                quote("2024-01-08T15:45:00-05:00", "call", 470.0, 2.0, 2.2),
                quote("2024-01-08T15:45:00-05:00", "call", 472.0, 0.9, 1.1),
            ]
        )
        result = self.pnl.evaluate_candidate_day(day, quotes, fee_per_contract=0.0, fill_model="half_spread")
        self.assertEqual("closed_forced_1545", result["status"])
        self.assertEqual(10.0, result["gross_pnl"])
        self.assertEqual(80.0, result["max_defined_loss"])

    def test_entry_latency_uses_shifted_entry_quote(self) -> None:
        day = candidate_day()
        quotes = self.pnl.index_quotes(
            [
                quote("2024-01-08T09:35:00-05:00", "call", 470.0, 1.0, 1.2),
                quote("2024-01-08T09:35:00-05:00", "call", 472.0, 0.4, 0.6),
                quote("2024-01-08T09:36:00-05:00", "call", 470.0, 1.2, 1.4),
                quote("2024-01-08T09:36:00-05:00", "call", 472.0, 0.5, 0.7),
                quote("2024-01-08T15:45:00-05:00", "call", 470.0, 2.0, 2.2),
                quote("2024-01-08T15:45:00-05:00", "call", 472.0, 0.9, 1.1),
            ]
        )
        result = self.pnl.evaluate_candidate_day(day, quotes, fee_per_contract=0.0, entry_latency_minutes=1)
        self.assertEqual("closed_forced_1545", result["status"])
        self.assertEqual("2024-01-08T09:35:00-05:00", result["signal_time_et"])
        self.assertEqual("2024-01-08T09:36:00-05:00", result["entry_time_et"])
        self.assertEqual(1, result["entry_latency_minutes"])
        self.assertEqual(20.0, result["gross_pnl"])

    def test_entry_latency_skips_when_shifted_quote_missing(self) -> None:
        day = candidate_day()
        quotes = self.pnl.index_quotes(
            [
                quote("2024-01-08T09:35:00-05:00", "call", 470.0, 1.0, 1.2),
                quote("2024-01-08T09:35:00-05:00", "call", 472.0, 0.4, 0.6),
                quote("2024-01-08T15:45:00-05:00", "call", 470.0, 2.0, 2.2),
                quote("2024-01-08T15:45:00-05:00", "call", 472.0, 0.9, 1.1),
            ]
        )
        result = self.pnl.evaluate_candidate_day(day, quotes, fee_per_contract=0.0, entry_latency_minutes=1)
        self.assertEqual("missing_quotes", result["status"])
        self.assertIn("entry call 470.0", result["reasons"][0])

    def test_nearest_close_fallback_uses_neighbor_quote(self) -> None:
        day = candidate_day()
        quotes = self.pnl.index_quotes(
            [
                quote("2024-01-08T09:35:00-05:00", "call", 470.0, 1.0, 1.2),
                quote("2024-01-08T09:35:00-05:00", "call", 472.0, 0.4, 0.6),
                quote("2024-01-08T15:44:00-05:00", "call", 470.0, 2.0, 2.2),
                quote("2024-01-08T15:44:00-05:00", "call", 472.0, 0.9, 1.1),
            ]
        )
        result = self.pnl.evaluate_candidate_day(day, quotes, fee_per_contract=0.0, close_fallback="nearest_1545_window")
        self.assertEqual("closed_forced_1545", result["status"])
        self.assertEqual("2024-01-08T15:44:00-05:00", result["close_timestamps_by_leg_id"]["long"])

    def test_nearest_close_fallback_never_uses_quote_after_1545(self) -> None:
        day = candidate_day()
        quotes = self.pnl.index_quotes(
            [
                quote("2024-01-08T09:35:00-05:00", "call", 470.0, 1.0, 1.2),
                quote("2024-01-08T09:35:00-05:00", "call", 472.0, 0.4, 0.6),
                quote("2024-01-08T15:46:00-05:00", "call", 470.0, 2.0, 2.2),
                quote("2024-01-08T15:46:00-05:00", "call", 472.0, 0.9, 1.1),
            ]
        )
        result = self.pnl.evaluate_candidate_day(day, quotes, fee_per_contract=0.0, close_fallback="nearest_1545_window")
        self.assertEqual("missing_quotes", result["status"])
        self.assertIn("close call 470.0", result["reasons"][0])

    def test_target_stop_exit_model_closes_on_profit_target(self) -> None:
        day = candidate_day()
        quotes = self.pnl.index_quotes(
            [
                quote("2024-01-08T09:35:00-05:00", "call", 470.0, 1.0, 1.2),
                quote("2024-01-08T09:35:00-05:00", "call", 472.0, 0.4, 0.6),
                quote("2024-01-08T10:30:00-05:00", "call", 470.0, 1.4, 1.6),
                quote("2024-01-08T10:30:00-05:00", "call", 472.0, 0.4, 0.5),
                quote("2024-01-08T15:45:00-05:00", "call", 470.0, 0.0, 0.1),
                quote("2024-01-08T15:45:00-05:00", "call", 472.0, 0.0, 0.1),
            ]
        )

        result = self.pnl.evaluate_candidate_day(day, quotes, fee_per_contract=0.0, exit_model="target_stop_25_50")

        self.assertEqual("closed_profit_target_25pct", result["status"])
        self.assertEqual("2024-01-08T10:30:00-05:00", result["close_timestamps_by_leg_id"]["long"])
        self.assertEqual(0.9, result["exit_value"])
        self.assertEqual(30.0, result["gross_pnl"])

    def test_target_stop_exit_model_closes_on_stop_loss(self) -> None:
        day = candidate_day()
        quotes = self.pnl.index_quotes(
            [
                quote("2024-01-08T09:35:00-05:00", "call", 470.0, 1.0, 1.2),
                quote("2024-01-08T09:35:00-05:00", "call", 472.0, 0.4, 0.6),
                quote("2024-01-08T10:30:00-05:00", "call", 470.0, 0.3, 0.4),
                quote("2024-01-08T10:30:00-05:00", "call", 472.0, 0.0, 0.1),
                quote("2024-01-08T15:45:00-05:00", "call", 470.0, 2.0, 2.2),
                quote("2024-01-08T15:45:00-05:00", "call", 472.0, 0.9, 1.1),
            ]
        )

        result = self.pnl.evaluate_candidate_day(day, quotes, fee_per_contract=0.0, exit_model="target_stop_25_50")

        self.assertEqual("closed_stop_loss_50pct", result["status"])
        self.assertEqual("2024-01-08T10:30:00-05:00", result["close_timestamps_by_leg_id"]["long"])
        self.assertEqual(0.2, result["exit_value"])
        self.assertEqual(-40.0, result["gross_pnl"])

    def test_summarize_pnl_counts_closed_and_skipped(self) -> None:
        rows = [
            {"status": "closed_forced_1545", "net_pnl": 10.0},
            {"status": "closed_profit_target_25pct", "net_pnl": -5.0},
            {"status": "missing_quotes"},
        ]
        summary = self.pnl.summarize_pnl(rows, fee_per_contract=0.0)
        self.assertEqual(2, summary["closed_trades"])
        self.assertEqual(1, summary["skipped_trades"])
        self.assertEqual(5.0, summary["total_net_pnl"])
        self.assertEqual(["under-sampled", "underpowered"], summary["sample_adequacy"]["labels"])

    def test_big_day_dependency_removes_best_and_worst_trade(self) -> None:
        rows = [
            {"status": "closed_forced_1545", "implementable_pnl": -100.0, "mid_pnl": -90.0},
            {"status": "closed_forced_1545", "implementable_pnl": 10.0, "mid_pnl": 20.0},
            {"status": "closed_forced_1545", "implementable_pnl": 200.0, "mid_pnl": 210.0},
        ]

        summary = self.pnl.summarize_pnl(rows, fee_per_contract=0.0)

        self.assertEqual(3, summary["closed_trades"])
        self.assertEqual(110.0, summary["total_implementable_pnl"])
        self.assertEqual(2, summary["big_day_dependency"]["removed_trade_count"])
        self.assertEqual(10.0, summary["big_day_dependency"]["retained_total_implementable_pnl"])

    def test_render_report_contains_m3_sections_without_mojibake(self) -> None:
        summary = self.pnl.summarize_pnl(
            [{"status": "closed_forced_1545", "implementable_pnl": 10.0, "mid_pnl": 12.0, "cost_drag": 2.0}],
            fee_per_contract=0.64,
        )

        report = self.pnl.render_report(summary)

        self.assertIn("## PnL Model", report)
        self.assertIn("## Sample Adequacy", report)
        self.assertIn("## Big-Day Dependency Check", report)
        self.assertNotIn("เธ", report)


def candidate_day() -> dict:
    return {
        "date": "2024-01-08",
        "direction": "call",
        "orb_signal": {"breakout_timestamp_et": "2024-01-08T09:35:00-05:00"},
        "legs": [
            leg("long", "buy", 470.0),
            leg("short", "sell", 472.0),
        ],
    }


def leg(leg_id: str, side: str, strike: float) -> dict:
    return {
        "leg_id": leg_id,
        "side": side,
        "quantity": 1,
        "right": "call",
        "strike": strike,
        "expiration_date": "2024-01-08",
    }


def quote(timestamp: str, right: str, strike: float, bid: float, ask: float) -> dict:
    return {
        "quote_timestamp_et": timestamp,
        "right": right,
        "strike": strike,
        "expiration_date": timestamp[:10],
        "bid": bid,
        "ask": ask,
    }


if __name__ == "__main__":
    unittest.main()
