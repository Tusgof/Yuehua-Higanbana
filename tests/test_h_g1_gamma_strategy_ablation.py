from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = PROJECT_ROOT / "scripts" / "run_h_g1_gamma_strategy_ablation.py"
VALIDATOR_PATH = PROJECT_ROOT / "scripts" / "validate_h_g1_gamma_strategy_ablation_summary.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class H_G1GammaStrategyAblationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = load_module(RUNNER_PATH, "run_h_g1_gamma_strategy_ablation")
        cls.validator = load_module(VALIDATOR_PATH, "validate_h_g1_gamma_strategy_ablation_summary")

    def test_ablation_runs_current_artifacts_without_strategy_approval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            summary_path = tmp_path / "summary.json"
            report_path = tmp_path / "summary.md"
            search_log_path = tmp_path / "search_log.jsonl"

            result = self.runner.run_ablation(
                summary_path=summary_path,
                report_path=report_path,
                search_log_path=search_log_path,
            )

            self.assertEqual("complete_underpowered", result["status"])
            self.assertEqual("H-G1", result["hypothesis_id"])
            self.assertEqual("E1", result["evidence_tier"])
            self.assertEqual("ยังสรุปไม่ได้", result["conclusion"])
            self.assertFalse(result["network_used"])
            self.assertFalse(result["paid_data_used"])
            self.assertFalse(result["new_data_requested"])
            self.assertTrue(result["strategy_pnl_used"])
            self.assertFalse(result["strategy_use_allowed"])
            self.assertFalse(result["paper_trading_allowed"])
            self.assertEqual(4, len(result["variant_results"]))
            self.assertEqual(2, result["coverage"]["intersection_closed_trade_count"])
            self.assertIn("intersection_sample_too_small", result["tier_blockers"])
            self.assertTrue(search_log_path.exists())
            self.assertIn("H-G1 Gamma Strategy Ablation Diagnostic", report_path.read_text(encoding="utf-8"))

    def test_validator_accepts_generated_temp_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            summary_path = tmp_path / "summary.json"
            report_path = tmp_path / "summary.md"
            search_log_path = tmp_path / "search_log.jsonl"
            self.runner.run_ablation(
                summary_path=summary_path,
                report_path=report_path,
                search_log_path=search_log_path,
            )
            result = self.validator.validate_summary(summary_path)

        self.assertEqual("pass", result["status"])
        self.assertEqual(4, result["variant_count"])
        self.assertEqual(4, result["search_log_rows"])

    def test_validator_rejects_acceptance_tier(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            summary_path = tmp_path / "summary.json"
            report_path = tmp_path / "summary.md"
            search_log_path = tmp_path / "search_log.jsonl"
            self.runner.run_ablation(
                summary_path=summary_path,
                report_path=report_path,
                search_log_path=search_log_path,
            )
            payload = json.loads(summary_path.read_text(encoding="utf-8"))
            payload["evidence_tier"] = "E2"
            summary_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            result = self.validator.validate_summary(summary_path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("evidence_tier_must_remain_E1", result["blockers"])

    def test_validator_rejects_strategy_use(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            summary_path = tmp_path / "summary.json"
            report_path = tmp_path / "summary.md"
            search_log_path = tmp_path / "search_log.jsonl"
            self.runner.run_ablation(
                summary_path=summary_path,
                report_path=report_path,
                search_log_path=search_log_path,
            )
            payload = json.loads(summary_path.read_text(encoding="utf-8"))
            payload["strategy_use_allowed"] = True
            summary_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            result = self.validator.validate_summary(summary_path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("strategy_use_allowed_must_be_false", result["blockers"])


if __name__ == "__main__":
    unittest.main()
