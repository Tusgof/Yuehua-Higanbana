from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "run_m5_portfolio_construction_diagnostic.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("run_m5_portfolio_construction_diagnostic", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load M5.6 portfolio construction module")
    module = importlib.util.module_from_spec(spec)
    sys.modules["run_m5_portfolio_construction_diagnostic"] = module
    spec.loader.exec_module(module)
    return module


class M5PortfolioConstructionDiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = load_runner()

    def test_inverse_risk_weights_sum_to_one_and_favor_lower_risk(self) -> None:
        weights = self.runner.inverse_risk_weights({"subsystem_a": 0.10, "subsystem_b": 0.30})

        self.assertAlmostEqual(1.0, sum(weights.values()), places=6)
        self.assertGreater(weights["subsystem_a"], weights["subsystem_b"])

    def test_portfolio_daily_rows_use_union_dates_and_weighted_pnl(self) -> None:
        sleeves = {
            "subsystem_a": {
                "2023-12-29": {"date": "2023-12-29", "net_pnl": 100.0},
                "2024-01-02": {"date": "2024-01-02", "net_pnl": -20.0},
            },
            "subsystem_b": {
                "2024-01-02": {"date": "2024-01-02", "net_pnl": 40.0},
            },
        }

        rows = self.runner.portfolio_daily_rows(sleeves, {"subsystem_a": 0.5, "subsystem_b": 0.5})

        self.assertEqual(["2023-12-29", "2024-01-02"], [row["date"] for row in rows])
        self.assertEqual(50.0, rows[0]["net_pnl"])
        self.assertEqual(10.0, rows[1]["net_pnl"])
        self.assertEqual("oos", rows[1]["split"])

    def test_feasibility_blocks_fractional_subsystem_b_current_sizing(self) -> None:
        sub_b = {
            "feasibility": {
                "max_defined_loss": 773.0,
                "median_defined_loss": 566.0,
                "min_defined_loss": 366.0,
            }
        }

        result = self.runner.feasibility_assessment({"subsystem_a": 0.5, "subsystem_b": 0.5}, sub_b)

        self.assertEqual("blocked_current_sizing", result["status"])
        self.assertEqual(500.0, result["subsystem_b_allocation"])
        self.assertFalse(result["all_subsystem_b_trades_fit_allocation"])
        self.assertFalse(result["all_subsystem_b_trades_fit_20_risk_budget"])

    def test_default_scenarios_include_required_allocation_families(self) -> None:
        scenarios = self.runner.default_scenarios(
            {
                "inverse_volatility": {"subsystem_a": 0.8, "subsystem_b": 0.2},
                "inverse_es95": {"subsystem_a": 0.9, "subsystem_b": 0.1},
            }
        )
        scenario_ids = {row["scenario_id"] for row in scenarios}

        self.assertIn("subsystem_a_only_control", scenario_ids)
        self.assertIn("subsystem_b_only_diagnostic", scenario_ids)
        self.assertIn("equal_weight_fractional_diagnostic", scenario_ids)
        self.assertIn("risk_parity_inverse_vol_in_sample", scenario_ids)
        self.assertIn("es_parity_inverse_es95_in_sample", scenario_ids)

    def test_write_search_log_records_weights_and_feasibility(self) -> None:
        rows = [
            {
                "trial_index": 1,
                "scenario_id": "subsystem_a_only_control",
                "scenario_type": "control",
                "weights": {"subsystem_a": 1.0, "subsystem_b": 0.0},
                "weight_fit_policy": "fixed_or_fit_on_in_sample_only",
                "fractional_contract_warning": False,
                "metrics": {"total_pnl": 10.0},
                "splits": {"oos": {"metrics": {"total_pnl": 1.0}}},
                "feasibility": {"status": "account_feasible_without_subsystem_b"},
                "sample_adequacy": {"labels": ["under-sampled"]},
            }
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "search.jsonl"
            self.runner.write_search_log(rows, path)
            record = json.loads(path.read_text(encoding="utf-8").splitlines()[0])

        self.assertEqual("m5_portfolio_construction_diagnostic", record["experiment_id"])
        self.assertEqual(1.0, record["parameters"]["weights"]["subsystem_a"])
        self.assertEqual("account_feasible_without_subsystem_b", record["feasibility"]["status"])


if __name__ == "__main__":
    unittest.main()
