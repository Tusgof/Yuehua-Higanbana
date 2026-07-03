from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "run_h_b2_subsystem_b_scale.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("run_h_b2_subsystem_b_scale", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load H-B2 scale runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class H_B2SubsystemBScaleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = load_runner()

    def test_wing_gap_selection_uses_pre_registered_gap(self) -> None:
        legs = self.runner.select_capped_put_ratio_legs(option_chain(), underlying_price=470.0, wing_gap=15.0)

        self.assertEqual(["buy", "sell", "buy"], [leg["side"] for leg in legs])
        self.assertLessEqual(legs[2]["strike"], legs[1]["strike"] - 15.0)

    def test_scenario_summary_filters_by_account_risk_budget(self) -> None:
        closed = [
            closed_day("2024-01-03", "oos", 10.0, 20.0, 10.0, 400.0),
            closed_day("2024-01-04", "oos", -5.0, 5.0, 10.0, 600.0),
        ]

        summary = self.runner._scenario_summary(10000.0, 0.05, 10.0, closed)

        self.assertEqual(1, summary["eligible_trades"])
        self.assertEqual(1, summary["ineligible_trades"])
        self.assertEqual(10.0, summary["metrics"]["total_implementable_pnl"])
        self.assertEqual(500.0, summary["risk_budget_usd"])


def quote(strike: float, bid: float = 1.0, ask: float = 1.1) -> dict:
    return {"bid": bid, "ask": ask, "right": "put", "strike": strike}


def option_chain() -> list[dict]:
    return [quote(strike) for strike in [435, 440, 445, 450, 455, 460, 465, 470, 475]]


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
    }


if __name__ == "__main__":
    unittest.main()
