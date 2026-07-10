from __future__ import annotations

import json
import unittest
from pathlib import Path

from lib.statistics import (
    autocorr_inflation,
    black_scholes_price_delta_gamma,
    effective_sample_length,
    expected_shortfall,
    generalized_sharpe_variance_term,
    minimum_track_record_length,
    probabilistic_sharpe_ratio,
    raw_kurtosis_population,
    sharpe_ratio,
    skewness_population,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "statistics_golden.json"
GOLDEN = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


class StatisticsGoldenTests(unittest.TestCase):
    def test_fixture_declares_sources_and_raw_kurtosis_convention(self) -> None:
        self.assertIn("how-to-use-the-sharpe-ratio.md", " ".join(GOLDEN["provenance"]["methodology_sources"]))
        self.assertIn("raw Pearson", GOLDEN["conventions"]["kurtosis"])
        self.assertIn("not excess", GOLDEN["conventions"]["kurtosis"])

    def test_psr_mintrl_anchor_uses_raw_kurtosis(self) -> None:
        inputs = GOLDEN["psr_mintrl"]["inputs"]
        expected = GOLDEN["psr_mintrl"]["expected"]
        mintrl = minimum_track_record_length(
            observed_sharpe=inputs["observed_sharpe"],
            skewness=inputs["skewness"],
            raw_kurtosis=inputs["raw_kurtosis"],
            null_sharpe=inputs["null_sharpe"],
        )
        psr = probabilistic_sharpe_ratio(
            observed_sharpe=inputs["observed_sharpe"],
            sample_length=inputs["sample_length"],
            skewness=inputs["skewness"],
            raw_kurtosis=inputs["raw_kurtosis"],
            null_sharpe=inputs["null_sharpe"],
        )

        self.assertEqual(expected["minimum_track_record_length"], mintrl)
        self.assertAlmostEqual(expected["probabilistic_sharpe_ratio"], psr, places=6)

    def test_generalized_variance_rejects_excess_kurtosis_convention_slip(self) -> None:
        inputs = GOLDEN["psr_mintrl"]["inputs"]
        raw_variance = generalized_sharpe_variance_term(
            inputs["observed_sharpe"], inputs["skewness"], inputs["raw_kurtosis"]
        )
        excess_variance = generalized_sharpe_variance_term(
            inputs["observed_sharpe"], inputs["skewness"], inputs["raw_kurtosis"] - 3.0
        )

        self.assertAlmostEqual(GOLDEN["psr_mintrl"]["expected"]["generalized_variance_term"], raw_variance, places=12)
        self.assertAlmostEqual(GOLDEN["psr_mintrl"]["wrong_excess_kurtosis_variance_term"], excess_variance, places=12)
        self.assertNotAlmostEqual(raw_variance, excess_variance, places=9)

    def test_autocorrelation_adjustment_anchor(self) -> None:
        anchor = GOLDEN["autocorrelation"]
        self.assertAlmostEqual(anchor["expected_inflation"], autocorr_inflation(anchor["input"]), places=12)
        self.assertAlmostEqual(
            anchor["expected_effective_sample_length"],
            effective_sample_length(anchor["sample_length"], anchor["input"]),
            places=12,
        )

    def test_distribution_convention_anchor(self) -> None:
        anchor = GOLDEN["distribution"]
        returns = anchor["returns"]

        self.assertAlmostEqual(anchor["expected_sharpe"], sharpe_ratio(returns), places=6)
        self.assertAlmostEqual(anchor["expected_skewness"], skewness_population(returns), places=6)
        self.assertAlmostEqual(anchor["expected_raw_kurtosis"], raw_kurtosis_population(returns), places=6)

    def test_expected_shortfall_left_tail_anchor(self) -> None:
        anchor = GOLDEN["expected_shortfall"]

        self.assertAlmostEqual(anchor["confidence_95"], expected_shortfall(anchor["values"], 0.95), places=6)
        self.assertAlmostEqual(anchor["confidence_80"], expected_shortfall(anchor["values"], 0.80), places=6)

    def test_black_scholes_bracket_anchor(self) -> None:
        anchor = GOLDEN["black_scholes"]
        call = black_scholes_price_delta_gamma(**anchor["inputs"], right="call")
        put = black_scholes_price_delta_gamma(**anchor["inputs"], right="put")

        self.assertAlmostEqual(anchor["call"]["price"], call["price"], places=6)
        self.assertAlmostEqual(anchor["call"]["delta"], call["delta"], places=6)
        self.assertAlmostEqual(anchor["call"]["gamma"], call["gamma"], places=6)
        self.assertAlmostEqual(anchor["put"]["price"], put["price"], places=6)
        self.assertAlmostEqual(anchor["put"]["delta"], put["delta"], places=6)
        self.assertAlmostEqual(call["gamma"], put["gamma"], places=12)


if __name__ == "__main__":
    unittest.main()
