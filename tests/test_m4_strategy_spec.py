from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = PROJECT_ROOT / "scripts" / "strategy_spec_m4.py"
VALIDATOR_PATH = PROJECT_ROOT / "scripts" / "validate_m2_contracts.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class M4StrategySpecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.spec = load_module(SPEC_PATH, "strategy_spec_m4")
        cls.validator = load_module(VALIDATOR_PATH, "validate_m2_contracts")
        cls.schema = cls.validator.load_schema()

    def test_orb_signal_detects_call_put_and_no_trade(self) -> None:
        base = [
            bar("2024-01-03T09:30:00-05:00", 100, 101, 99, 100),
            bar("2024-01-03T09:31:00-05:00", 100, 101.5, 99.5, 101),
            bar("2024-01-03T09:34:00-05:00", 101, 102, 100, 101.5),
        ]
        self.assertEqual("call_breakout", self.spec.compute_orb_signal(base + [bar("2024-01-03T09:35:00-05:00", 102, 103, 101, 102.5)])["decision"])
        self.assertEqual("put_breakout", self.spec.compute_orb_signal(base + [bar("2024-01-03T09:35:00-05:00", 100, 101, 98, 98.5)])["decision"])
        self.assertEqual("no_trade", self.spec.compute_orb_signal(base + [bar("2024-01-03T09:35:00-05:00", 101, 101.5, 100, 101)])["decision"])

    def test_subsystem_a_vertical_outputs_defined_risk_legs(self) -> None:
        legs = self.spec.construct_subsystem_a_vertical(option_chain(), "call", underlying_price=470, width=2)
        self.assertEqual(["buy", "sell"], [leg["side"] for leg in legs])
        self.assertEqual(["call", "call"], [leg["right"] for leg in legs])
        self.assertLess(legs[0]["strike"], legs[1]["strike"])
        for leg in legs:
            self.assertEqual([], self.validator.validate_record(leg, self.schema))

    def test_subsystem_a_uses_configured_breakout_gap_band(self) -> None:
        call_legs = self.spec.construct_subsystem_a_vertical(option_chain(), "call", underlying_price=470.5, width=2)
        put_legs = self.spec.construct_subsystem_a_vertical(option_chain(), "put", underlying_price=471.5, width=2)

        self.assertEqual(472, call_legs[0]["strike"])
        self.assertEqual(470, put_legs[0]["strike"])

    def test_subsystem_a_rejects_when_no_long_strike_in_gap_band(self) -> None:
        with self.assertRaises(self.spec.StrategySpecError):
            self.spec.construct_subsystem_a_vertical(option_chain(strikes=[470, 471, 473]), "call", underlying_price=470.2, width=2)

    def test_subsystem_b_ratio_requires_protective_wing(self) -> None:
        legs = self.spec.construct_subsystem_b_capped_put_ratio(option_chain(), underlying_price=470)
        self.assertEqual(["buy", "sell", "buy"], [leg["side"] for leg in legs])
        self.assertEqual([1, 2, 1], [leg["quantity"] for leg in legs])
        self.assertLess(legs[2]["strike"], legs[1]["strike"])
        for leg in legs:
            self.assertEqual([], self.validator.validate_record(leg, self.schema))

        with self.assertRaises(self.spec.StrategySpecError):
            self.spec.construct_subsystem_b_capped_put_ratio(option_chain(min_put_strike=466), underlying_price=470)

    def test_filters_and_novi_proxy_are_explicit(self) -> None:
        allowed = self.spec.evaluate_quant_filters(
            {"vix_close": 18.0, "vxv_close": 19.0},
            [],
            "2024-01-03",
        )
        self.assertTrue(allowed["allowed"])

        blocked = self.spec.evaluate_quant_filters(
            {"vix_close": 30.0, "vxv_close": 26.0},
            [{"event_type": "FOMC", "event_timestamp_et": "2024-01-03T14:00:00-05:00", "importance": "high"}],
            "2024-01-03",
        )
        self.assertFalse(blocked["allowed"])
        self.assertEqual("unknown", self.spec.evaluate_novi_proxy(None)["status"])
        self.assertEqual("positive_net_gamma_proxy", self.spec.evaluate_novi_proxy({"customer_buy_volume": 10, "customer_sell_volume": 20})["regime"])

    def test_deepseek_dry_run_and_strategy_intent_validate(self) -> None:
        assessment = self.spec.dry_run_deepseek_assessment(
            [{"headline": "Quiet market before open"}],
            {"vix_close": 18.0, "vxv_close": 19.0},
            "2024-01-03T09:20:00-05:00",
        )
        self.assertEqual("DeepSeek", assessment["provider"])
        self.assertEqual("allow", assessment["decision"])
        self.assertEqual([], self.validator.validate_record(assessment, self.schema))

        legs = self.spec.construct_subsystem_a_vertical(option_chain(), "put", underlying_price=470, width=2)
        intent = self.spec.build_strategy_intent(
            "subsystem_a_orb_put_vertical",
            "go",
            ["put breakout", "quant filters allow trade", f"llm={assessment['decision']}"],
            "2024-01-03T09:35:00-05:00",
            legs,
        )
        self.assertEqual([], self.validator.validate_record(intent, self.schema))
        self.assertEqual([leg["leg_id"] for leg in legs], intent["legs"])


def bar(timestamp_et: str, open_: float, high: float, low: float, close: float) -> dict:
    return {
        "record_type": "spy_bar",
        "schema_version": "m2.0",
        "symbol": "SPY",
        "timestamp_et": timestamp_et,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": 1000,
        "source": "fixture",
        "provider": "synthetic",
    }


def option_chain(min_put_strike: float = 460, strikes: list[float] | None = None) -> list[dict]:
    strikes = strikes or [460, 464, 466, 468, 470, 472, 474]
    quotes = []
    for right in ["call", "put"]:
        for strike in strikes:
            if right == "put" and strike < min_put_strike:
                continue
            quotes.append({
                "record_type": "option_quote",
                "schema_version": "m2.0",
                "underlying": "SPY",
                "quote_timestamp_et": "2024-01-03T10:00:00-05:00",
                "expiration_date": "2024-01-03",
                "dte": 0.25,
                "right": right,
                "strike": strike,
                "bid": 1.0,
                "ask": 1.05,
                "bid_size": 100,
                "ask_size": 100,
                "provider": "synthetic",
                "source": "fixture",
            })
    return quotes


if __name__ == "__main__":
    unittest.main()
