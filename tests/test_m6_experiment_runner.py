from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = PROJECT_ROOT / "scripts" / "experiment_runner_m6.py"
VALIDATOR_PATH = PROJECT_ROOT / "scripts" / "validate_m2_contracts.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class M6ExperimentRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = load_module(RUNNER_PATH, "experiment_runner_m6")
        cls.validator = load_module(VALIDATOR_PATH, "validate_m2_contracts")
        cls.schema = cls.validator.load_schema()

    def test_loads_ten_valid_manifests(self) -> None:
        manifests = self.runner.load_manifests()
        self.assertEqual(10, len(manifests))
        for manifest in manifests:
            self.assertEqual([], self.validator.validate_record(manifest, self.schema))

    def test_split_validation_rejects_oos_leakage(self) -> None:
        manifest = dict(self.runner.load_manifests()[0])
        manifest["train_window"] = {"start": "2024-01-01", "end": "2024-12-31"}
        manifest["oos_window"] = {"start": "2024-01-01", "end": "2025-12-31"}
        with self.assertRaises(self.runner.ExperimentRunnerError):
            self.runner.validate_chronological_split(manifest)

    def test_metrics_include_tail_and_cost_fields(self) -> None:
        daily, trades = self.runner.fixture_daily_pnl_and_trades()
        metrics = self.runner.calculate_metrics(daily, trades)
        for field in ["sharpe", "sortino", "max_drawdown", "es95", "es99", "worst_day_loss", "cost_drag"]:
            self.assertIn(field, metrics)
        self.assertEqual(2, metrics["trade_count"])
        self.assertEqual(3.0, metrics["cost_drag"])

    def test_report_generator_writes_markdown_chart_and_metadata(self) -> None:
        manifest = self.runner.load_manifests()[0]
        daily, trades = self.runner.fixture_daily_pnl_and_trades()
        metrics = self.runner.calculate_metrics(daily, trades)
        with tempfile.TemporaryDirectory() as tmp:
            result = self.runner.generate_experiment_report(manifest, metrics, Path(tmp))
            report_path = Path(result["report_path"])
            self.assertTrue(report_path.exists())
            self.assertIn("ยังสรุปไม่ได้", report_path.read_text(encoding="utf-8"))
            chart_path = Path(result["metadata"]["chart_paths"][0])
            self.assertTrue(chart_path.exists())
            self.assertEqual([], self.validator.validate_record(result["metadata"], self.schema))

    def test_generate_all_reports_and_final_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self.runner.generate_all_fixture_reports(Path(tmp) / "experiments")
            self.assertEqual(10, result["report_count"])
            self.assertEqual("blocked", result["gate"]["status"])
            final_review = Path(result["final_review_path"])
            self.assertTrue(final_review.exists())
            text = final_review.read_text(encoding="utf-8")
            self.assertIn("ยังสรุปไม่ได้", text)
            self.assertIn("exp10_macro_filter", text)

    def test_acceptance_gate_blocks_fixture_scale_evidence(self) -> None:
        manifest = self.runner.load_manifests()[0]
        daily, trades = self.runner.fixture_daily_pnl_and_trades()
        metrics = self.runner.calculate_metrics(daily, trades)
        with tempfile.TemporaryDirectory() as tmp:
            result = self.runner.generate_experiment_report(manifest, metrics, Path(tmp))
            gate = self.runner.acceptance_gate([result["metadata"]])
            self.assertEqual("blocked", gate["status"])
            self.assertTrue(any("trade_count below 500" in reason for reason in gate["reasons"]))


if __name__ == "__main__":
    unittest.main()
