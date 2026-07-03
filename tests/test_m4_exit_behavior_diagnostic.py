from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "run_m4_exit_behavior_diagnostic.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("run_m4_exit_behavior_diagnostic", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load M4 exit diagnostic runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class M4ExitBehaviorDiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = load_runner()

    def test_delta_metrics_compare_target_stop_against_forced_close(self) -> None:
        forced = {
            "trade_count": 2,
            "total_implementable_pnl": 10.0,
            "total_mid_pnl": 15.0,
            "total_cost_drag": 5.0,
            "worst_day_loss": -20.0,
            "max_drawdown": -0.1,
            "sharpe_proxy": 0.2,
        }
        target = {
            "trade_count": 2,
            "total_implementable_pnl": 25.0,
            "total_mid_pnl": 31.0,
            "total_cost_drag": 6.0,
            "worst_day_loss": -12.0,
            "max_drawdown": -0.08,
            "sharpe_proxy": 0.3,
        }

        delta = self.runner.delta_metrics(forced, target)

        self.assertEqual(15.0, delta["implementable_pnl_delta"])
        self.assertEqual(8.0, delta["worst_day_loss_delta"])
        self.assertEqual(0.02, delta["max_drawdown_delta"])
        self.assertEqual(0.1, delta["sharpe_proxy_delta"])

    def test_variant_summary_marks_sample_adequacy_and_exit_reason_counts(self) -> None:
        datasets = [
            {
                "label": "fixture_in",
                "split": "in_sample",
                "coverage_start": "2023-01-01",
                "coverage_end": "2023-01-31",
                "candidate_days": 2,
                "closed_trades": 2,
                "skipped_trades": 0,
                "status_counts": {"closed_forced_1545": 1, "closed_profit_target_25pct": 1},
                "benchmark": {"return": 0.01},
                "trades": [
                    {"date": "2023-01-03", "status": "closed_forced_1545", "mid_pnl": 12.0, "implementable_pnl": 10.0, "split": "in_sample"},
                    {"date": "2023-01-04", "status": "closed_profit_target_25pct", "mid_pnl": 7.0, "implementable_pnl": 5.0, "split": "in_sample"},
                ],
            },
            {
                "label": "fixture_oos",
                "split": "oos",
                "coverage_start": "2024-01-01",
                "coverage_end": "2024-01-31",
                "candidate_days": 1,
                "closed_trades": 1,
                "skipped_trades": 0,
                "status_counts": {"closed_stop_loss_50pct": 1},
                "benchmark": {"return": -0.02},
                "trades": [
                    {"date": "2024-01-03", "status": "closed_stop_loss_50pct", "mid_pnl": -4.0, "implementable_pnl": -6.0, "split": "oos"}
                ],
            },
        ]

        summary = self.runner.variant_summary("target_stop_25_50", datasets)

        self.assertEqual(3, summary["metrics"]["trade_count"])
        self.assertEqual(["under-sampled", "underpowered"], summary["sample_adequacy"]["labels"])
        self.assertEqual({"forced_1545": 1, "profit_target_25pct": 1, "stop_loss_50pct": 1}, summary["metrics"]["exit_reason_counts"])

    def test_aggregate_sets_research_log_and_no_deployment_selection(self) -> None:
        datasets = []
        for exit_model in self.runner.EXIT_MODELS:
            for split, date in [("in_sample", "2023-01-03"), ("oos", "2024-01-03")]:
                datasets.append(
                    {
                        "label": f"{exit_model}_{split}",
                        "split": split,
                        "exit_model": exit_model,
                        "coverage_start": date,
                        "coverage_end": date,
                        "candidate_days": 1,
                        "closed_trades": 1,
                        "skipped_trades": 0,
                        "status_counts": {"closed_forced_1545": 1},
                        "benchmark": {"return": 0.0},
                        "trades": [
                            {
                                "date": date,
                                "status": "closed_forced_1545",
                                "mid_pnl": 1.0,
                                "implementable_pnl": 1.0,
                                "split": split,
                                "exit_model": exit_model,
                            }
                        ],
                    }
                )

        summary = self.runner.aggregate_diagnostic(datasets)

        self.assertEqual("complete", summary["status"])
        self.assertTrue(summary["research_log_required"])
        self.assertEqual("higanbana-exit-behavior-diagnostic-real-data", summary["research_log_slug"])
        self.assertIsNone(summary["dsr_assessment"]["selected_for_deployment"])
        self.assertTrue(summary["methodology"]["not_parameter_optimization"])


if __name__ == "__main__":
    unittest.main()
