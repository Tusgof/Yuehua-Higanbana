from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "run_m5_transaction_cost_latency_sensitivity.py"


def load_m5():
    spec = importlib.util.spec_from_file_location("run_m5_transaction_cost_latency_sensitivity", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load M5 sensitivity module")
    module = importlib.util.module_from_spec(spec)
    sys.modules["run_m5_transaction_cost_latency_sensitivity"] = module
    spec.loader.exec_module(module)
    return module


class M5TransactionCostLatencySensitivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.m5 = load_m5()

    def test_default_scenarios_include_cost_and_latency_axes(self) -> None:
        scenarios = self.m5.default_scenarios()
        self.assertEqual(8, len(scenarios))
        self.assertIn("mid", {row["fill_model"] for row in scenarios})
        self.assertIn("half_spread", {row["fill_model"] for row in scenarios})
        self.assertIn("full_spread_stress", {row["fill_model"] for row in scenarios})
        self.assertIn(0, {row["entry_latency_minutes"] for row in scenarios})
        self.assertIn(1, {row["entry_latency_minutes"] for row in scenarios})
        self.assertIn(2, {row["entry_latency_minutes"] for row in scenarios})

    def test_search_log_record_preserves_trial_parameters(self) -> None:
        row = {
            "trial_index": 3,
            "scenario_id": "half_spread_fee_064_latency_1",
            "fill_model": "half_spread",
            "fee_per_contract": 0.64,
            "entry_latency_minutes": 1,
            "close_fallback": "nearest_1545_window",
            "exit_model": "forced_close_only",
            "metrics": {"trade_count": 2, "total_implementable_pnl": 10.0},
            "sample_adequacy": {"labels": ["under-sampled"]},
        }
        record = self.m5.search_log_record(row)
        self.assertEqual("parameter_search_trial", record["record_type"])
        self.assertEqual(3, record["trial_index"])
        self.assertEqual(1, record["parameters"]["entry_latency_minutes"])
        self.assertEqual(0.64, record["parameters"]["fee_per_contract"])

    def test_write_search_log_writes_one_json_object_per_trial(self) -> None:
        rows = [
            {
                "trial_index": 1,
                "scenario_id": "mid_fee_0_latency_0_control",
                "fill_model": "mid",
                "fee_per_contract": 0.0,
                "entry_latency_minutes": 0,
                "close_fallback": "nearest_1545_window",
                "exit_model": "forced_close_only",
                "metrics": {"trade_count": 1},
                "sample_adequacy": {"labels": ["under-sampled"]},
            }
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "search.jsonl"
            self.m5.write_search_log(rows, path)
            lines = path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(1, len(lines))
        self.assertEqual("mid_fee_0_latency_0_control", json.loads(lines[0])["scenario_id"])

    def test_friction_drag_ratio_uses_absolute_mid_pnl(self) -> None:
        self.assertEqual(0.25, self.m5.friction_drag_ratio(-100.0, 25.0))
        self.assertIsNone(self.m5.friction_drag_ratio(0.0, 25.0))


if __name__ == "__main__":
    unittest.main()
