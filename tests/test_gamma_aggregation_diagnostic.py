from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "run_gamma_aggregation_diagnostic.py"


def load_module():
    spec = importlib.util.spec_from_file_location("run_gamma_aggregation_diagnostic", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load gamma aggregation diagnostic module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GammaAggregationDiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()

    def test_moneyness_bucket_boundaries_match_policy(self) -> None:
        bucket = self.module.moneyness_bucket
        self.assertEqual("deep_put", bucket(0.9699))
        self.assertEqual("otm_put", bucket(0.97))
        self.assertEqual("otm_put", bucket(0.9949))
        self.assertEqual("atm", bucket(0.995))
        self.assertEqual("atm", bucket(1.005))
        self.assertEqual("otm_call", bucket(1.0051))
        self.assertEqual("otm_call", bucket(1.03))
        self.assertEqual("deep_call", bucket(1.0301))

    def test_gamma_formula_and_sign_convention(self) -> None:
        call = {"gamma": 0.02, "open_interest": 10, "underlying_price": 500, "right": "call"}
        put = dict(call, right="put")
        self.assertEqual(10000.0, self.module.local_gamma_exposure(call))
        self.assertEqual(10000.0, self.module.signed_gamma_proxy(call))
        self.assertEqual(-10000.0, self.module.signed_gamma_proxy(put))

    def test_coverage_gate_blocks_when_computed_greeks_below_policy(self) -> None:
        gate = self.module._coverage_gate(quote_count=10, underlying_join_count=10, oi_join_count=10, computed_count=6)
        self.assertEqual("blocked", gate["status"])
        self.assertIn("computed_greeks_rate_below_70pct", gate["blockers"])

    def test_run_diagnostic_writes_blocked_summary_for_one_day_fixture(self) -> None:
        rows = [
            _row("call", 100, 100, "computed_with_caveats"),
            _row("put", 100, 100, "computed_with_caveats"),
            _row("call", 106, 100, "blocked_mid_outside_black_scholes_bracket"),
            _row("put", 94, 100, "blocked_mid_outside_black_scholes_bracket"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "input.jsonl"
            output_path = Path(tmp) / "summary.json"
            input_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

            result = self.module.run_diagnostic(input_path, output_path, "2024-01-03")
            written = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual("blocked", result["status"])
        self.assertEqual(result["status"], written["status"])
        self.assertIn("coverage_gate:blocked", result["blockers"])
        self.assertIn("stability_gate:blocked", result["blockers"])
        self.assertIn("economic_sign_gate:blocked", result["blockers"])
        self.assertEqual("diagnostic_only_blocked_by_policy_gates", result["strategy_use_status"])


def _row(right: str, strike: float, underlying_price: float, status: str) -> dict[str, object]:
    row: dict[str, object] = {
        "quote_timestamp_et": "2024-01-03T09:31:00-05:00",
        "underlying_price_timestamp_et": "2024-01-03T09:31:00-05:00",
        "open_interest_timestamp_utc": "2024-01-03T11:30:00+00:00",
        "right": right,
        "strike": strike,
        "underlying_price": underlying_price,
        "open_interest": 10,
        "greeks_status": status,
    }
    if status == "computed_with_caveats":
        row["gamma"] = 0.02
    return row


if __name__ == "__main__":
    unittest.main()
