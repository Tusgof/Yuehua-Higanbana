from __future__ import annotations

import unittest

from lib.options import parse_databento_option_symbol, replay_vertical, select_vertical_legs


def quote(strike: float, right: str, bid: float, ask: float) -> dict[str, object]:
    return {
        "underlying": "SPY",
        "expiration_date": "2026-04-13",
        "right": right,
        "strike": strike,
        "symbol": f"SPY-{right}-{strike}",
        "bid": bid,
        "ask": ask,
        "bid_size": 10,
        "ask_size": 10,
    }


class OptionHelpersTests(unittest.TestCase):
    def test_parses_databento_symbol(self) -> None:
        parsed = parse_databento_option_symbol("SPY   260413C00525000")
        self.assertEqual("SPY", parsed["underlying"])
        self.assertEqual("2026-04-13", parsed["expiration_date"])
        self.assertEqual("call", parsed["right"])
        self.assertEqual(525.0, parsed["strike"])

    def test_selects_nearest_discrete_call_vertical(self) -> None:
        quotes = [quote(524, "call", 2.0, 2.1), quote(525, "call", 1.5, 1.6), quote(527, "call", 0.7, 0.8)]
        legs, mapping = select_vertical_legs(
            quotes,
            direction="call",
            underlying_price=523.52,
            target_gap=1.48,
            width=2.0,
        )
        self.assertEqual([525.0, 527.0], [leg["strike"] for leg in legs])
        self.assertEqual("nearest_discrete_strike_rounding", mapping["mapping_method"])

    def test_replay_separates_mid_and_implementable_pnl(self) -> None:
        entry = [quote(525, "call", 1.5, 1.6), quote(527, "call", 0.7, 0.8)]
        close = [quote(525, "call", 2.0, 2.1), quote(527, "call", 1.0, 1.1)]
        result = replay_vertical(
            entry,
            close,
            direction="call",
            underlying_price=523.52,
            target_gap=1.48,
            width=2.0,
            fee_per_leg_usd=0.64,
        )
        self.assertEqual(20.0, result["pnl"]["mid_pnl"])
        self.assertEqual(-2.56, result["pnl"]["implementable_pnl"])
        self.assertEqual(22.56, result["pnl"]["cost_drag_vs_mid"])


if __name__ == "__main__":
    unittest.main()
