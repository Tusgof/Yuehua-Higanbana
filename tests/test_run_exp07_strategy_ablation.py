from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "run_exp07_strategy_ablation.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("run_exp07_strategy_ablation", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load Exp07 ablation runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RunExp07StrategyAblationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = load_runner()
        cls.plan = cls.runner.load_plan()

    def test_default_plan_evaluates_as_blocked_until_real_data_exists(self) -> None:
        result = self.runner.evaluate_ablation_readiness(self.plan)

        self.assertEqual("blocked", result["status"])
        self.assertEqual(3, result["variant_count"])
        self.assertIn("requires_real_news_archive", result["blockers"])
        self.assertNotIn("requires_real_macro_calendar_archive", result["blockers"])
        self.assertIn("requires_wider_spy_0dte_data", result["blockers"])
        self.assertIn("requires_minimum_trade_count_500", result["blockers"])

    def test_raw_llm_variant_is_observation_only(self) -> None:
        result = self.runner.evaluate_ablation_readiness(self.plan)
        raw_variant = next(variant for variant in result["variants"] if variant["variant_id"] == "raw_llm_observation_only")

        self.assertTrue(raw_variant["uses_raw_llm_gate"])
        self.assertFalse(raw_variant["can_block_trade"])

    def test_strategy_data_audit_removes_bid_ask_blocker_when_quotes_exist(self) -> None:
        result = self.runner.evaluate_ablation_readiness(
            self.plan,
            strategy_data_audit={"totals": {"closed_trades": 23, "quote_rows": 3988315}},
        )

        self.assertNotIn("requires_bid_ask_quotes", result["blockers"])
        self.assertIn("requires_minimum_trade_count_500", result["blockers"])
        self.assertEqual(23, result["strategy_data_evidence"]["closed_trades"])
        self.assertEqual(3988315, result["strategy_data_evidence"]["quote_rows"])

    def test_main_writes_json_and_markdown_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "status.json"
            report_path = Path(tmp) / "status.md"

            returncode = self.runner.main(["--output-path", str(output_path), "--report-path", str(report_path)])

            self.assertEqual(0, returncode)
            result = json.loads(output_path.read_text(encoding="utf-8"))
            report = report_path.read_text(encoding="utf-8")
            self.assertEqual("blocked", result["status"])
            self.assertIn("Exp07 Strategy Ablation Status", report)
            self.assertIn("requires_real_news_archive", report)
            self.assertIn("Strategy Data Evidence", report)


if __name__ == "__main__":
    unittest.main()
