from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_h_a2_exact_2022_underlying_bar_plan import (
    validate_h_a2_exact_2022_underlying_bar_plan,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = PROJECT_ROOT / "experiments" / "h_a2_exact_2022_underlying_bar_plan.json"


class ValidateHA2Exact2022UnderlyingBarPlanTests(unittest.TestCase):
    def test_current_plan_passes(self) -> None:
        result = validate_h_a2_exact_2022_underlying_bar_plan()

        self.assertEqual("pass", result["status"], result["blockers"])
        self.assertEqual("H-A2", result["hypothesis_id"])
        self.assertEqual("E0", result["evidence_tier"])
        self.assertEqual("build_bounded_acquisition_import_tool_before_any_source_execution", result["decision"])
        self.assertIs(False, result["paper_trading_allowed"])
        self.assertIs(False, result["real_money_allowed"])

    def test_rejects_missing_bounded_tool_step(self) -> None:
        data = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        data["source_execution_order"] = [
            item for item in data["source_execution_order"] if item["step_id"] != "build_bounded_data_only_tool"
        ]

        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "plan.json"
            plan_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            result = validate_h_a2_exact_2022_underlying_bar_plan(plan_path=plan_path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("missing_execution_step:build_bounded_data_only_tool", result["blockers"])

    def test_rejects_execution_or_trading_permissions(self) -> None:
        data = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        data["guardrails"]["ibkr_request_used_by_this_artifact"] = True
        data["guardrails"]["paper_trading_allowed"] = True
        data["guardrails"]["real_money_allowed"] = True

        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "plan.json"
            plan_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            result = validate_h_a2_exact_2022_underlying_bar_plan(plan_path=plan_path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("ibkr_request_used_by_this_artifact_must_be_false", result["blockers"])
        self.assertIn("paper_trading_allowed_must_be_false", result["blockers"])
        self.assertIn("real_money_allowed_must_be_false", result["blockers"])

    def test_rejects_incomplete_validation_gates(self) -> None:
        data = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        data["validation_gates_before_exact_rerun"]["join_to_existing_2022_10_option_quotes_required"] = False
        data["validation_gates_before_exact_rerun"]["rerun_allowed_only_after_all_gates_pass"] = False

        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "plan.json"
            plan_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            result = validate_h_a2_exact_2022_underlying_bar_plan(plan_path=plan_path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("join_to_existing_2022_10_option_quotes_required_must_be_true", result["blockers"])
        self.assertIn("rerun_allowed_only_after_all_gates_pass_must_be_true", result["blockers"])


if __name__ == "__main__":
    unittest.main()
