from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "run_multimonth_pilot_summary.py"


def load_module():
    spec = importlib.util.spec_from_file_location("run_multimonth_pilot_summary", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load multimonth pilot summary module")
    module = importlib.util.module_from_spec(spec)
    sys.modules["run_multimonth_pilot_summary"] = module
    spec.loader.exec_module(module)
    return module


class MultimonthPilotSummaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()

    def test_build_summary_combines_adapter_and_pnl_by_model(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            scenarios = [
                write_scenario(temp_path, "sep_2023", "in_sample", 2, 10.0, "forced_close_only"),
                write_scenario(temp_path, "oct_2023", "in_sample", 1, -4.0, "forced_close_only"),
            ]

            summary = self.module.build_summary(scenarios)

        self.assertEqual("in_sample", summary["split"])
        self.assertEqual("ยังสรุปไม่ได้", summary["conclusion"])
        self.assertEqual(2, summary["month_count"])
        self.assertEqual(40, summary["adapter_totals"]["calendar_days"])
        self.assertEqual(3, summary["adapter_totals"]["candidate_ready_days"])
        model = summary["pnl_models"]["forced_close_only"]
        self.assertEqual(3, model["closed_trades"])
        self.assertEqual(6.0, model["total_net_pnl"])
        self.assertEqual({"closed_forced_1545": 3}, model["status_counts"])

    def test_build_summary_rejects_mixed_splits(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            scenarios = [
                write_scenario(temp_path, "dec_2023", "in_sample", 1, 5.0, "forced_close_only"),
                write_scenario(temp_path, "feb_2024", "oos", 1, -3.0, "forced_close_only"),
            ]

            with self.assertRaisesRegex(ValueError, "mixed train/OOS splits"):
                self.module.build_summary(scenarios)

    def test_run_multimonth_summary_writes_json_and_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            scenarios = [write_scenario(temp_path, "sep_2023", "in_sample", 1, 10.0, "target_stop_25_50")]
            summary_path = temp_path / "summary.json"
            report_path = temp_path / "report.md"

            summary = self.module.run_multimonth_summary(scenarios, summary_path, report_path)

            self.assertTrue(summary_path.exists())
            self.assertTrue(report_path.exists())
            self.assertEqual(summary, json.loads(summary_path.read_text(encoding="utf-8")))
            self.assertIn("ยังไม่ใช่หลักฐานยืนยัน edge", report_path.read_text(encoding="utf-8"))


def write_scenario(temp_path: Path, label: str, split: str, closed_trades: int, pnl: float, exit_model: str) -> dict:
    adapter_path = temp_path / f"{label}_adapter.json"
    pnl_path = temp_path / f"{label}_{exit_model}.json"
    adapter_path.write_text(
        json.dumps(
            {
                "coverage_start": "2023-09-01",
                "coverage_end": "2023-09-29",
                "calendar_days": 20,
                "candidate_ready_days": closed_trades,
                "bar_rows": 100,
                "quote_rows": 200,
                "status_counts": {"candidate_ready": closed_trades, "no_trade": 20 - closed_trades},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    trades = [
        {"date": f"2023-09-{day + 1:02d}", "status": "closed_forced_1545", "net_pnl": pnl / closed_trades}
        for day in range(closed_trades)
    ]
    pnl_path.write_text(
        json.dumps(
            {
                "exit_model": exit_model,
                "candidate_days": closed_trades,
                "closed_trades": closed_trades,
                "skipped_trades": 0,
                "total_net_pnl": pnl,
                "trades": trades,
                "status_counts": {"closed_forced_1545": closed_trades},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return {"label": label, "split": split, "adapter": adapter_path, "pnl": [pnl_path]}


if __name__ == "__main__":
    unittest.main()
