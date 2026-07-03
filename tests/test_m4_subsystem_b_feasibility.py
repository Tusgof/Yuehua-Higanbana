from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "run_m4_subsystem_b_feasibility.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("run_m4_subsystem_b_feasibility", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load M4 Sub-System B runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class M4SubsystemBFeasibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = load_runner()

    def test_select_put_ratio_requires_deep_protective_wing(self) -> None:
        legs = self.runner.select_capped_put_ratio_legs(option_chain(), underlying_price=470.0)

        self.assertEqual(["buy", "sell", "buy"], [leg["side"] for leg in legs])
        self.assertEqual([1, 2, 1], [leg["quantity"] for leg in legs])
        self.assertGreater(legs[0]["strike"], legs[1]["strike"])
        self.assertLessEqual(legs[2]["strike"], legs[1]["strike"] - 10.0)

    def test_select_put_ratio_rejects_missing_deep_wing(self) -> None:
        with self.assertRaises(self.runner.SubsystemBFeasibilityError):
            self.runner.select_capped_put_ratio_legs(option_chain(strikes=[460, 465, 468, 470]), underlying_price=470.0)

    def test_max_defined_loss_uses_expiration_payoff_and_entry_cashflow(self) -> None:
        legs = [
            {"side": "buy", "right": "put", "strike": 470.0, "quantity": 1},
            {"side": "sell", "right": "put", "strike": 465.0, "quantity": 2},
            {"side": "buy", "right": "put", "strike": 455.0, "quantity": 1},
        ]

        max_loss = self.runner.max_defined_loss(legs, entry_cashflow=1.0)

        self.assertEqual(400.0, max_loss)

    def test_strategy_pnl_separates_mid_and_implementable_cost_drag(self) -> None:
        legs = [
            {"side": "buy", "right": "put", "strike": 470.0, "quantity": 1},
            {"side": "sell", "right": "put", "strike": 465.0, "quantity": 2},
            {"side": "buy", "right": "put", "strike": 455.0, "quantity": 1},
        ]
        entry_quotes = {
            470.0: quote(1.00, 1.10),
            465.0: quote(0.50, 0.60),
            455.0: quote(0.10, 0.20),
        }
        close_quotes = {
            470.0: quote(2.00, 2.10),
            465.0: quote(1.00, 1.10),
            455.0: quote(0.20, 0.30),
        }

        mid = self.runner.strategy_pnl(legs, entry_quotes, close_quotes, "mid", include_fees=False)
        implementable_gross = self.runner.strategy_pnl(legs, entry_quotes, close_quotes, "implementable", include_fees=False)

        self.assertEqual(10.0, mid)
        self.assertEqual(-30.0, implementable_gross)

    def test_aggregate_marks_feasibility_log_required_and_inconclusive(self) -> None:
        datasets = [
            {
                "label": "fixture",
                "split": "in_sample",
                "normalized_root": "fixture",
                "coverage_start": "2023-01-01",
                "coverage_end": "2023-01-31",
                "trading_days": 1,
                "days": [closed_day("2023-01-03", "in_sample", 10.0, 12.0, 2.0, 400.0)],
            },
            {
                "label": "fixture_oos",
                "split": "oos",
                "normalized_root": "fixture",
                "coverage_start": "2024-01-01",
                "coverage_end": "2024-01-31",
                "trading_days": 1,
                "days": [closed_day("2024-01-03", "oos", -5.0, -2.0, 3.0, 600.0)],
            },
        ]

        summary = self.runner.aggregate_results(datasets)

        self.assertEqual("complete", summary["status"])
        self.assertEqual("ไม่ผ่าน", summary["conclusion"])
        self.assertTrue(summary["research_log_required"])
        self.assertEqual("higanbana-put-ratio-feasibility-real-data", summary["research_log_slug"])
        self.assertEqual(["under-sampled", "underpowered"], summary["sample_adequacy"]["labels"])
        self.assertFalse(summary["feasibility"]["all_trades_fit_300_allocation"])


def quote(bid: float, ask: float) -> dict:
    return {"bid": bid, "ask": ask, "right": "put", "strike": 0.0}


def option_chain(strikes: list[float] | None = None) -> list[dict]:
    strikes = strikes or [450, 455, 460, 465, 470, 475]
    return [
        {
            "record_type": "option_quote",
            "schema_version": "m2.0",
            "underlying": "SPY",
            "quote_timestamp_et": "2024-01-03T10:00:00-05:00",
            "expiration_date": "2024-01-03",
            "dte": 0,
            "right": "put",
            "strike": strike,
            "bid": 1.0,
            "ask": 1.1,
            "bid_size": 100,
            "ask_size": 100,
            "provider": "synthetic",
            "source": "fixture",
        }
        for strike in strikes
    ]


def closed_day(date: str, split: str, pnl: float, mid_pnl: float, cost_drag: float, max_loss: float) -> dict:
    return {
        "date": date,
        "dataset": "fixture",
        "split": split,
        "status": "closed_forced_1545",
        "implementable_pnl": pnl,
        "net_pnl": pnl,
        "mid_pnl": mid_pnl,
        "cost_drag": cost_drag,
        "max_defined_loss": max_loss,
        "account_1000_feasible": max_loss <= 1000,
        "allocation_300_feasible": max_loss <= 300,
        "risk_budget_20_feasible": max_loss <= 20,
    }


if __name__ == "__main__":
    unittest.main()
