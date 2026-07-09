from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "run_h_g1_gamma_regime_diagnostic.py"


def load_module():
    spec = importlib.util.spec_from_file_location("run_h_g1_gamma_regime_diagnostic", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load H-G1 diagnostic module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class H_G1GammaRegimeDiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()

    def test_required_bucket_blockers_require_all_policy_buckets(self) -> None:
        stats = {
            "otm_put": {"computed_rate": 0.6},
            "atm": {"computed_rate": 0.59},
        }

        blockers = self.module._required_bucket_blockers(stats)

        self.assertIn("atm_computed_rate_below_60pct", blockers)
        self.assertIn("otm_call_missing", blockers)
        self.assertNotIn("otm_put_computed_rate_below_60pct", blockers)

    def test_stability_gate_uses_preregistered_regime_counts(self) -> None:
        manifest = {
            "minimum_regime_counts": {
                "total_dates": 2,
                "low_volatility": 1,
                "normal_volatility": 0,
                "high_volatility": 1,
                "high_importance_macro": 1,
                "no_high_importance_macro": 1,
                "in_sample": 1,
                "oos": 1,
            },
            "selected_dates": [
                {"date": "2023-01-03", "volatility_bucket": "low", "high_importance_macro": True, "split": "in_sample"},
                {"date": "2024-01-03", "volatility_bucket": "high", "high_importance_macro": False, "split": "oos"},
            ],
        }

        gate = self.module._stability_gate_v2(manifest, {"2023-01-03": [{}], "2024-01-03": [{}]})

        self.assertEqual("pass", gate["status"])
        self.assertEqual("pre_registered_regime_set_covered", gate["label"])

    def test_coverage_gate_blocks_when_required_bucket_fails(self) -> None:
        rows = [
            _row("put", 98.0, "computed_with_caveats"),
            _row("call", 100.0, "computed_with_caveats"),
            _row("call", 102.0, "blocked_mid_outside_black_scholes_bracket"),
        ]
        per_date = {"2024-01-03": self.module._per_date_diagnostic("2024-01-03", rows)}

        gate = self.module._coverage_gate_v2(rows, per_date)

        self.assertEqual("blocked", gate["status"])
        self.assertIn("bucket_weighted_coverage_gate_failed", gate["blockers"])

    def test_side_aware_policy_excludes_opposite_right_itm_rows_from_required_gate(self) -> None:
        rows = [
            _row("put", 98.0, "computed_with_caveats"),
            _row("call", 98.0, "blocked_mid_outside_black_scholes_bracket"),
            _row("call", 100.0, "computed_with_caveats"),
            _row("put", 100.0, "computed_with_caveats"),
            _row("call", 102.0, "computed_with_caveats"),
            _row("put", 102.0, "blocked_mid_outside_black_scholes_bracket"),
        ]
        policy = {
            "policy_id": "h_g1_required_bucket_policy_v3_side_aware",
            "thresholds": {
                "computed_row_rate_floor": 0.6,
                "computed_oi_notional_share_floor": 0.8,
                "retained_abs_gamma_proxy_share_floor": 0.8,
            },
            "forbidden_claims": [],
        }
        per_date = {"2024-01-03": self.module._per_date_diagnostic("2024-01-03", rows, policy)}

        gate = self.module._coverage_gate_v2(rows, per_date, policy)

        self.assertEqual("pass", gate["bucket_weighted_coverage"]["status"])
        self.assertIn("raw_row_coverage_gate_failed", gate["blockers"])
        self.assertEqual([], per_date["2024-01-03"]["required_bucket_blockers"])
        self.assertEqual(
            {"otm_call_opposite_right_put_rows": 1, "otm_put_opposite_right_call_rows": 1},
            per_date["2024-01-03"]["reported_opposite_right_itm_rows"],
        )

    def test_aggregate_gamma_ignores_rows_without_open_interest(self) -> None:
        rows = [
            _row("call", 100.0, "computed_with_caveats"),
            {**_row("put", 100.0, "computed_with_caveats"), "open_interest": None},
        ]

        aggregate = self.module._aggregate_gamma(rows)

        self.assertEqual(1, aggregate["gamma_proxy_row_count"])
        self.assertIsNotNone(aggregate["net_oi_gamma_proxy"])

    def test_oi_raw_paths_merge_primary_and_additional_download_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            primary = root / "primary.json"
            additional = root / "additional.json"
            existing = root / "missing_existing_probe.json"
            primary.write_text(json.dumps(_download_result("2023-08-09", "primary.dbn.zst")), encoding="utf-8")
            additional.write_text(json.dumps(_download_result("2023-09-13", "replacement.dbn.zst")), encoding="utf-8")

            paths = self.module._oi_raw_paths_by_date(primary, existing, [additional])

        self.assertEqual(Path("primary.dbn.zst"), paths["2023-08-09"])
        self.assertEqual(Path("replacement.dbn.zst"), paths["2023-09-13"])


def _row(right: str, strike: float, status: str) -> dict[str, object]:
    row: dict[str, object] = {
        "quote_timestamp_et": "2024-01-03T09:35:00-05:00",
        "underlying_price_timestamp_et": "2024-01-03T09:35:00-05:00",
        "open_interest_timestamp_utc": "2024-01-03T11:30:00+00:00",
        "right": right,
        "strike": strike,
        "underlying_price": 100.0,
        "open_interest": 10,
        "greeks_status": status,
    }
    if status == "computed_with_caveats":
        row["gamma"] = 0.01
    return row


def _download_result(date: str, raw_path: str) -> dict[str, object]:
    return {"execution": {"downloads": [{"date": date, "raw_path": raw_path}]}}


if __name__ == "__main__":
    unittest.main()
