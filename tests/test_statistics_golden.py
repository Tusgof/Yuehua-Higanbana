from __future__ import annotations

import unittest

from lib.statistics import (
    black_scholes_price_delta_gamma,
    expected_shortfall,
    minimum_track_record_length,
    probabilistic_sharpe_ratio,
    raw_kurtosis_population,
    sharpe_ratio,
    skewness_population,
)


class StatisticsGoldenTests(unittest.TestCase):
    def test_fable_mintrl_anchor_uses_raw_kurtosis(self) -> None:
        mintrl = minimum_track_record_length(
            observed_sharpe=0.092203,
            skewness=1.221374,
            raw_kurtosis=3.09085,
            null_sharpe=0.0,
        )
        psr = probabilistic_sharpe_ratio(
            observed_sharpe=0.092203,
            sample_length=90,
            skewness=1.221374,
            raw_kurtosis=3.09085,
            null_sharpe=0.0,
        )

        self.assertEqual(285, mintrl)
        self.assertAlmostEqual(0.821497, psr, places=6)

    def test_distribution_convention_anchor(self) -> None:
        returns = [-0.03, -0.01, 0.00, 0.02, 0.08]

        self.assertAlmostEqual(0.318896, sharpe_ratio(returns), places=6)
        self.assertAlmostEqual(0.857597, skewness_population(returns), places=6)
        self.assertAlmostEqual(2.468974, raw_kurtosis_population(returns), places=6)

    def test_expected_shortfall_left_tail_anchor(self) -> None:
        values = [-10.0, -4.0, -1.0, 2.0, 8.0, 15.0]

        self.assertAlmostEqual(-10.0, expected_shortfall(values, 0.95), places=6)
        self.assertAlmostEqual(-7.0, expected_shortfall(values, 0.80), places=6)

    def test_black_scholes_bracket_anchor(self) -> None:
        call = black_scholes_price_delta_gamma(
            spot=100.0,
            strike=100.0,
            years_to_expiry=1.0,
            rate=0.05,
            dividend_yield=0.0,
            volatility=0.20,
            right="call",
        )
        put = black_scholes_price_delta_gamma(
            spot=100.0,
            strike=100.0,
            years_to_expiry=1.0,
            rate=0.05,
            dividend_yield=0.0,
            volatility=0.20,
            right="put",
        )

        self.assertAlmostEqual(10.450584, call["price"], places=6)
        self.assertAlmostEqual(0.636831, call["delta"], places=6)
        self.assertAlmostEqual(0.018762, call["gamma"], places=6)
        self.assertAlmostEqual(5.573526, put["price"], places=6)
        self.assertAlmostEqual(-0.363169, put["delta"], places=6)
        self.assertAlmostEqual(call["gamma"], put["gamma"], places=12)


if __name__ == "__main__":
    unittest.main()
