from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "validate_h_a2_2022_10_single_month_decision.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_h_a2_2022_10_single_month_decision", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load H-A2 single-month decision validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ValidateHA2SingleMonthDecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator()

    def test_current_decision_artifact_passes(self) -> None:
        result = self.validator.validate_h_a2_2022_10_single_month_decision()

        self.assertEqual("pass", result["status"])
        self.assertEqual("2022-10", result["selected_month"])
        self.assertEqual("blocked", result["top2_gate_status"])
        self.assertEqual(10.52248, result["single_month_estimated_cost_usd"])
        self.assertEqual(119.989706, result["projected_used_after_download_usd"])

    def test_blocks_expanding_scope_to_2022_09_or_top2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decision_path = root / "decision.json"
            decision = json.loads(
                (PROJECT_ROOT / "experiments" / "h_a2_2022_10_single_month_stress_decision.json").read_text(encoding="utf-8")
            )
            decision["selected_month"] = "2022-09"
            decision["forbidden_actions"] = []
            decision_path.write_text(json.dumps(decision), encoding="utf-8")

            result = self.validator.validate_h_a2_2022_10_single_month_decision(
                decision_path=decision_path,
            )

        self.assertEqual("blocked", result["status"])
        self.assertIn("selected_month_must_be_2022_10", result["blockers"])
        self.assertIn("missing_forbidden_action:Do not download 2022-09", result["blockers"])

    def test_blocks_paper_trading_or_llm_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decision_path = root / "decision.json"
            decision = json.loads(
                (PROJECT_ROOT / "experiments" / "h_a2_2022_10_single_month_stress_decision.json").read_text(encoding="utf-8")
            )
            decision["paper_trading_allowed"] = True
            decision["llm_research_allowed"] = True
            decision_path.write_text(json.dumps(decision), encoding="utf-8")

            result = self.validator.validate_h_a2_2022_10_single_month_decision(
                decision_path=decision_path,
            )

        self.assertEqual("blocked", result["status"])
        self.assertIn("paper_trading_allowed_must_be_false", result["blockers"])
        self.assertIn("llm_research_allowed_must_be_false", result["blockers"])


if __name__ == "__main__":
    unittest.main()
