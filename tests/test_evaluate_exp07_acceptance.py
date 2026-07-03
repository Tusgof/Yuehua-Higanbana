from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EVALUATOR_PATH = PROJECT_ROOT / "scripts" / "evaluate_exp07_acceptance.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Exp07AcceptanceEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.evaluator = load_module(EVALUATOR_PATH, "evaluate_exp07_acceptance")
        cls.criteria = cls.evaluator.load_json(PROJECT_ROOT / "tests" / "fixtures" / "exp07_acceptance_criteria_v1.json")
        cls.summary = cls.evaluator.load_json(PROJECT_ROOT / "reports" / "experiments" / "exp07_prompt_v12_summary.json")

    def test_v12_summary_passes_guarded_candidate_but_blocks_strategy_integration(self) -> None:
        result = self.evaluator.evaluate_acceptance(self.summary, self.criteria)

        self.assertEqual("fail", result["raw_llm_gate_status"])
        self.assertEqual("pass", result["guarded_policy_candidate_status"])
        self.assertEqual("blocked", result["strategy_integration_status"])
        self.assertIn("requires_real_strategy_backtest_ablation", result["strategy_integration_blockers"])
        self.assertEqual(13, result["metrics"]["unknown_policy_violation_count"])
        self.assertEqual(0, result["metrics"]["guarded_unknown_policy_violation_count"])

    def test_raw_gate_passes_only_when_raw_is_fully_stable_and_policy_clean(self) -> None:
        summary = json.loads(json.dumps(self.summary))
        summary["stable_case_count"] = summary["case_count"]
        summary["unknown_policy_violation_count"] = 0

        result = self.evaluator.evaluate_acceptance(summary, self.criteria)

        self.assertEqual("pass", result["raw_llm_gate_status"])

    def test_rejects_non_live_or_incomplete_matrix(self) -> None:
        summary = json.loads(json.dumps(self.summary))
        summary["mode"] = "dry_run_no_network"
        summary["assessment_count"] = summary["assessment_count"] - 1

        result = self.evaluator.evaluate_acceptance(summary, self.criteria)

        self.assertEqual("fail", result["raw_llm_gate_status"])
        self.assertEqual("fail", result["guarded_policy_candidate_status"])

    def test_main_writes_json_and_markdown_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            json_path = Path(tmp) / "evaluation.json"
            report_path = Path(tmp) / "evaluation.md"
            returncode = self.evaluator.main([
                "--json-output-path",
                str(json_path),
                "--report-path",
                str(report_path),
            ])

            payload = json.loads(json_path.read_text(encoding="utf-8"))
            report = report_path.read_text(encoding="utf-8")

        self.assertEqual(0, returncode)
        self.assertEqual("pass", payload["guarded_policy_candidate_status"])
        self.assertIn("Strategy integration status: `blocked`", report)


if __name__ == "__main__":
    unittest.main()
