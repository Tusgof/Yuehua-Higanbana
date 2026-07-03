from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "run_jan2024_pilot_sensitivity.py"


def load_sensitivity():
    spec = importlib.util.spec_from_file_location("run_jan2024_pilot_sensitivity", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load pilot sensitivity module")
    module = importlib.util.module_from_spec(spec)
    sys.modules["run_jan2024_pilot_sensitivity"] = module
    spec.loader.exec_module(module)
    return module


class Jan2024PilotSensitivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sensitivity = load_sensitivity()

    def test_default_scenarios_cover_fill_fee_and_close_fallback(self) -> None:
        scenarios = self.sensitivity.default_scenarios()
        self.assertEqual(10, len(scenarios))
        self.assertIn("full_spread_stress", {scenario["fill_model"] for scenario in scenarios})
        self.assertIn("nearest_1545_window", {scenario["close_fallback"] for scenario in scenarios})
        self.assertIn(1.0, {scenario["fee_per_contract"] for scenario in scenarios})

    def test_compact_result_keeps_metrics_needed_for_report(self) -> None:
        row = self.sensitivity.compact_result(
            {"scenario_id": "s1", "fill_model": "mid", "fee_per_contract": 0.0, "close_fallback": "strict_1545"},
            {
                "candidate_days": 6,
                "closed_trades": 4,
                "skipped_trades": 2,
                "total_net_pnl": 10.0,
                "average_net_pnl": 2.5,
                "win_rate": 0.5,
                "worst_trade": -1.0,
                "best_trade": 5.0,
                "max_drawdown": -0.01,
                "sharpe_proxy": 0.2,
                "status_counts": {"closed_forced_1545": 4},
            },
        )
        self.assertEqual("s1", row["scenario_id"])
        self.assertEqual(1, row["trial_index"])
        self.assertEqual(10.0, row["total_net_pnl"])

    def test_search_log_record_keeps_parameters_and_metrics(self) -> None:
        row = result("mid", 0.65, 12.0, 1)
        row.update(
            {
                "trial_index": 2,
                "candidate_days": 6,
                "closed_trades": 5,
                "average_net_pnl": 2.4,
                "win_rate": 0.6,
                "worst_trade": -3.0,
                "best_trade": 9.0,
                "max_drawdown": -0.01,
                "sharpe_proxy": 0.5,
            }
        )

        record = self.sensitivity.search_log_record(row)

        self.assertEqual("parameter_search_trial", record["record_type"])
        self.assertEqual(2, record["trial_index"])
        self.assertEqual("mid", record["parameters"]["fill_model"])
        self.assertEqual(12.0, record["metrics"]["total_net_pnl"])

    def test_write_search_log_writes_one_jsonl_row_per_trial(self) -> None:
        rows = [
            {
                **result("mid", 0.0, 10.0, 0),
                "trial_index": 1,
                "candidate_days": 2,
                "closed_trades": 2,
                "average_net_pnl": 5.0,
                "win_rate": 1.0,
                "worst_trade": 1.0,
                "best_trade": 9.0,
                "max_drawdown": 0.0,
                "sharpe_proxy": 1.0,
            },
            {
                **result("half_spread", 0.65, 6.0, 1),
                "trial_index": 2,
                "candidate_days": 2,
                "closed_trades": 1,
                "average_net_pnl": 6.0,
                "win_rate": 1.0,
                "worst_trade": 6.0,
                "best_trade": 6.0,
                "max_drawdown": 0.0,
                "sharpe_proxy": 0.5,
            },
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "search_log.jsonl"
            self.sensitivity.write_search_log(rows, path)
            records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(2, len(records))
        self.assertEqual([1, 2], [record["trial_index"] for record in records])
        self.assertTrue(all(record["parameters"] for record in records))

    def test_dsr_assessment_blocks_pilot_output(self) -> None:
        assessment = self.sensitivity.dsr_assessment([result("mid", 0.0, 10.0, 0)])

        self.assertEqual("blocked", assessment["status"])
        self.assertEqual(1, assessment["trial_count"])
        self.assertIn("effective number of trials", assessment["required_before_acceptance"])

    def test_pilot_decision_allows_wider_pilot_when_stress_positive(self) -> None:
        rows = [
            result("full_spread_stress", 0.0, 20.0, 2),
            result("full_spread_stress", 1.0, 12.0, 2),
            result("mid", 0.0, 100.0, 2),
        ]
        decision = self.sensitivity.pilot_decision(rows)
        self.assertEqual("healthy_enough_for_wider_data_pilot", decision["status"])

    def test_pilot_decision_blocks_when_stress_negative(self) -> None:
        rows = [
            result("full_spread_stress", 0.0, -1.0, 2),
            result("mid", 0.0, 100.0, 2),
        ]
        decision = self.sensitivity.pilot_decision(rows)
        self.assertEqual("needs_design_review_before_wider_data", decision["status"])


def result(fill_model: str, fee: float, pnl: float, skipped: int) -> dict:
    return {
        "trial_index": 1,
        "scenario_id": f"{fill_model}-{fee}",
        "fill_model": fill_model,
        "fee_per_contract": fee,
        "close_fallback": "strict_1545",
        "total_net_pnl": pnl,
        "skipped_trades": skipped,
        "candidate_days": 1,
        "closed_trades": 1,
        "average_net_pnl": pnl,
        "win_rate": 1.0 if pnl > 0 else 0.0,
        "worst_trade": pnl,
        "best_trade": pnl,
        "max_drawdown": min(0.0, pnl),
        "sharpe_proxy": 0.0,
        "status_counts": {"closed_forced_1545": 1},
    }


if __name__ == "__main__":
    unittest.main()
