from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "run_m4_subsystem_a_baseline.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("run_m4_subsystem_a_baseline", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load M4 baseline runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class M4SubsystemABaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = load_runner()

    def test_metrics_separate_mid_and_implementable_pnl(self) -> None:
        trades = [
            {"date": "2024-01-03", "status": "closed_forced_1545", "mid_pnl": 12.0, "implementable_pnl": 10.0},
            {"date": "2024-01-04", "status": "closed_forced_1545", "mid_pnl": -2.0, "implementable_pnl": -5.0},
        ]

        metrics = self.runner.metrics_for_closed_trades(trades)

        self.assertEqual(2, metrics["trade_count"])
        self.assertEqual(10.0, metrics["total_mid_pnl"])
        self.assertEqual(5.0, metrics["total_implementable_pnl"])
        self.assertEqual(5.0, metrics["total_cost_drag"])
        self.assertEqual(-5.0, metrics["worst_day_loss"])

    def test_daily_pnl_compounds_equity_by_date(self) -> None:
        trades = [
            {"date": "2024-01-03", "status": "closed_forced_1545", "implementable_pnl": 10.0},
            {"date": "2024-01-03", "status": "closed_forced_1545", "implementable_pnl": 5.0},
            {"date": "2024-01-04", "status": "closed_forced_1545", "implementable_pnl": -20.0},
        ]

        rows = self.runner.daily_pnl_rows(trades)

        self.assertEqual(2, len(rows))
        self.assertEqual(15.0, rows[0]["net_pnl"])
        self.assertEqual(1015.0, rows[0]["ending_equity"])
        self.assertEqual(-20.0, rows[1]["net_pnl"])
        self.assertEqual(995.0, rows[1]["ending_equity"])

    def test_benchmark_for_bars_uses_first_and_last_close(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "spy_bar.jsonl"
            records = [
                {"timestamp_et": "2024-01-02T09:30:00-05:00", "close": 100.0},
                {"timestamp_et": "2024-01-31T16:00:00-05:00", "close": 110.0},
            ]
            path.write_text("\n".join(json.dumps(record) for record in records), encoding="utf-8")

            benchmark = self.runner.benchmark_for_bars(path)

        self.assertEqual(0.1, benchmark["return"])
        self.assertEqual(100.0, benchmark["pnl_on_1000"])

    def test_aggregate_marks_baseline_log_required_and_inconclusive(self) -> None:
        datasets = [
            {
                "label": "fixture_in",
                "split": "in_sample",
                "coverage_start": "2023-01-01",
                "coverage_end": "2023-01-31",
                "candidate_days": 1,
                "closed_trades": 1,
                "skipped_trades": 0,
                "total_mid_pnl": 12.0,
                "total_implementable_pnl": 10.0,
                "total_cost_drag": 2.0,
                "benchmark": {"return": 0.01},
                "trades": [{"date": "2023-01-03", "status": "closed_forced_1545", "mid_pnl": 12.0, "implementable_pnl": 10.0, "split": "in_sample"}],
            },
            {
                "label": "fixture_oos",
                "split": "oos",
                "coverage_start": "2024-01-01",
                "coverage_end": "2024-01-31",
                "candidate_days": 1,
                "closed_trades": 1,
                "skipped_trades": 0,
                "total_mid_pnl": -2.0,
                "total_implementable_pnl": -5.0,
                "total_cost_drag": 3.0,
                "benchmark": {"return": -0.02},
                "trades": [{"date": "2024-01-03", "status": "closed_forced_1545", "mid_pnl": -2.0, "implementable_pnl": -5.0, "split": "oos"}],
            },
        ]

        summary = self.runner.aggregate_baseline(datasets)

        self.assertEqual("complete", summary["status"])
        self.assertEqual("ยังสรุปไม่ได้", summary["conclusion"])
        self.assertTrue(summary["research_log_required"])
        self.assertEqual("higanbana-orb-baseline-real-data", summary["research_log_slug"])
        self.assertEqual(["under-sampled", "underpowered"], summary["sample_adequacy"]["labels"])


if __name__ == "__main__":
    unittest.main()
