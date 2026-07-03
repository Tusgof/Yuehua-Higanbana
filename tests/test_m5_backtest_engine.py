from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENGINE_PATH = PROJECT_ROOT / "scripts" / "backtest_engine_m5.py"
VALIDATOR_PATH = PROJECT_ROOT / "scripts" / "validate_m2_contracts.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class M5BacktestEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = load_module(ENGINE_PATH, "backtest_engine_m5")
        cls.validator = load_module(VALIDATOR_PATH, "validate_m2_contracts")
        cls.schema = cls.validator.load_schema()

    def test_fill_models_price_buy_and_sell_legs(self) -> None:
        quote = quote_record(bid=1.00, ask=1.10)
        self.assertEqual(1.05, self.engine.leg_fill_price(quote, "buy", "mid"))
        self.assertEqual(1.10, self.engine.leg_fill_price(quote, "buy", "half_spread"))
        self.assertEqual(1.00, self.engine.leg_fill_price(quote, "sell", "half_spread"))
        self.assertEqual(1.20, self.engine.leg_fill_price(quote, "buy", "full_spread_stress"))
        self.assertEqual(0.90, self.engine.leg_fill_price(quote, "sell", "full_spread_stress"))

    def test_fill_trade_and_daily_pnl_records_validate(self) -> None:
        leg = option_leg("leg-001", "buy", 1)
        fill = self.engine.create_fill(
            "fill-001",
            "2024-01-03T10:00:00-05:00",
            "intent-001",
            leg,
            quote_record(bid=1.00, ask=1.10),
            "mid",
        )
        self.assertEqual([], self.validator.validate_record(fill, self.schema))

        gross_pnl = self.engine.calculate_trade_pnl([fill], {"leg-001": 1.30})
        self.assertEqual(25.0, gross_pnl)
        trade = self.engine.create_trade_record(
            "trade-001",
            "subsystem_a_orb_call_vertical",
            "2024-01-03T10:00:00-05:00",
            "2024-01-03T15:45:00-05:00",
            50.0,
            gross_pnl,
            fees=1.0,
            fills=[fill],
        )
        daily = self.engine.create_daily_pnl_record("2024-01-03", 1000.0, trade["net_pnl"], 1, 470.0, 471.0)
        self.assertEqual([], self.validator.validate_record(trade, self.schema))
        self.assertEqual([], self.validator.validate_record(daily, self.schema))
        self.assertAlmostEqual(0.00212766, daily["benchmark_return"])

    def test_exit_rules_and_forced_close(self) -> None:
        self.assertEqual("profit_target_25pct", self.engine.subsystem_a_exit_reason(1.00, 1.25, "2024-01-03T10:15:00-05:00"))
        self.assertEqual("stop_loss_50pct", self.engine.subsystem_a_exit_reason(1.00, 0.50, "2024-01-03T10:15:00-05:00"))
        self.assertEqual("hold", self.engine.subsystem_a_exit_reason(1.00, 0.90, "2024-01-03T10:15:00-05:00"))
        self.assertEqual("forced_close_1545", self.engine.subsystem_a_exit_reason(1.00, 0.90, "2024-01-03T15:45:00-05:00"))
        self.assertEqual("ratio_stop_loss", self.engine.subsystem_b_exit_reason(0.50, 1.50, "2024-01-03T11:00:00-05:00", stop_multiple=3))

    def test_sizing_rejects_too_large_defined_loss_for_small_account(self) -> None:
        self.assertEqual(1, self.engine.max_contract_quantity(1000.0, 0.02, 20.0))
        self.assertEqual(0, self.engine.max_contract_quantity(1000.0, 0.02, 50.0))

    def test_append_jsonl_is_append_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "journal.jsonl"
            self.engine.append_jsonl(path, {"record_type": "example", "n": 1})
            self.engine.append_jsonl(path, {"record_type": "example", "n": 2})
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual([1, 2], [row["n"] for row in rows])


def quote_record(bid: float, ask: float) -> dict:
    return {
        "record_type": "option_quote",
        "schema_version": "m2.0",
        "underlying": "SPY",
        "quote_timestamp_et": "2024-01-03T10:00:00-05:00",
        "expiration_date": "2024-01-03",
        "dte": 0.25,
        "right": "call",
        "strike": 470,
        "bid": bid,
        "ask": ask,
        "bid_size": 100,
        "ask_size": 100,
        "provider": "synthetic",
        "source": "fixture",
    }


def option_leg(leg_id: str, side: str, quantity: int) -> dict:
    return {
        "record_type": "option_leg",
        "schema_version": "m2.0",
        "leg_id": leg_id,
        "underlying": "SPY",
        "expiration_date": "2024-01-03",
        "right": "call",
        "strike": 470,
        "side": side,
        "quantity": quantity,
    }


if __name__ == "__main__":
    unittest.main()
