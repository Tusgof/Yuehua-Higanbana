from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "run_m5_structural_break_assessment.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("run_m5_structural_break_assessment", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load M5.7 structural-break module")
    module = importlib.util.module_from_spec(spec)
    sys.modules["run_m5_structural_break_assessment"] = module
    spec.loader.exec_module(module)
    return module


class M5StructuralBreakAssessmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = load_runner()

    def test_period_summary_separates_reference_train_and_oos(self) -> None:
        datasets = [
            dataset("pre", "2021-01-04", "2021-12-31", 10),
            dataset("train", "2023-03-01", "2023-12-29", 41),
            dataset("oos", "2024-01-02", "2024-12-31", 49),
        ]

        periods = self.runner.summarize_periods(datasets)

        self.assertEqual(10, periods["reference_pre_break"]["closed_trades"])
        self.assertEqual(41, periods["post_break_train"]["closed_trades"])
        self.assertEqual(49, periods["oos"]["closed_trades"])

    def test_current_missing_reference_pre_break_creates_blockers(self) -> None:
        datasets = [
            dataset("train", "2023-03-01", "2023-12-29", 41),
            dataset("oos", "2024-01-02", "2024-12-31", 49),
        ]
        periods = self.runner.summarize_periods(datasets)

        blockers = self.runner.structural_break_blockers(periods, {"blockers": ["requires_minimum_trade_count_500"]})

        self.assertIn("requires_reference_pre_break_option_coverage", blockers)
        self.assertIn("requires_reference_pre_break_closed_trades", blockers)
        self.assertIn("requires_minimum_trade_count_500", blockers)

    def test_run_assessment_writes_deferred_summary_and_report(self) -> None:
        readiness = {
            "blockers": ["requires_minimum_trade_count_500"],
            "sample_adequacy": {"evidence_labels": ["under-sampled", "underpowered"]},
            "totals": {"closed_trades": 90},
            "datasets": [
                dataset("train", "2023-03-01", "2023-12-29", 41),
                dataset("oos", "2024-01-02", "2024-12-31", 49),
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            readiness_path = root / "readiness.json"
            summary_path = root / "summary.json"
            report_path = root / "report.md"
            readiness_path.write_text(json.dumps(readiness), encoding="utf-8")

            result = self.runner.run_assessment(summary_path, report_path, readiness_path)

            self.assertEqual("deferred", result["status"])
            self.assertTrue(result["research_log_required"])
            self.assertTrue(summary_path.exists())
            self.assertTrue(report_path.exists())
            self.assertIn("requires_reference_pre_break_option_coverage", result["blockers"])


def dataset(label: str, start: str, end: str, closed_trades: int) -> dict[str, object]:
    return {
        "label": label,
        "split": "in_sample" if end < "2024-01-01" else "oos",
        "status": "present",
        "coverage_start": start,
        "coverage_end": end,
        "candidate_days": closed_trades,
        "closed_trades": closed_trades,
        "quote_rows": closed_trades * 100,
        "bar_rows": closed_trades * 10,
    }


if __name__ == "__main__":
    unittest.main()
