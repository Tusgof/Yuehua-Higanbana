from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "validate_h_g1_post_ablation_decision.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_h_g1_post_ablation_decision", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load H-G1 post-ablation decision validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ValidateHG1PostAblationDecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator()

    def test_current_decision_artifact_passes(self) -> None:
        result = self.validator.validate_h_g1_post_ablation_decision()

        self.assertEqual("pass", result["status"])
        self.assertEqual("park_h_g1_pending_sample_expansion_plan", result["decision"])
        self.assertEqual("return_to_news_unblock_n7", result["selected_next_safe_action"])
        self.assertEqual(2, result["source_intersection_closed_trade_count"])

    def test_blocks_strategy_or_paper_trading_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decision_path = root / "decision.json"
            ablation_path = root / "ablation.json"
            decision = json.loads((PROJECT_ROOT / "experiments" / "h_g1_post_ablation_decision.json").read_text(encoding="utf-8"))
            ablation = json.loads((PROJECT_ROOT / "reports" / "experiments" / "h_g1_gamma_strategy_ablation_summary.json").read_text(encoding="utf-8"))
            decision["strategy_use_allowed"] = True
            decision["paper_trading_allowed"] = True
            decision_path.write_text(json.dumps(decision), encoding="utf-8")
            ablation_path.write_text(json.dumps(ablation), encoding="utf-8")

            result = self.validator.validate_h_g1_post_ablation_decision(decision_path, ablation_path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("strategy_use_allowed_must_be_false", result["blockers"])
        self.assertIn("paper_trading_allowed_must_be_false", result["blockers"])


if __name__ == "__main__":
    unittest.main()
