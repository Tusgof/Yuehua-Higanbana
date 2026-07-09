from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "validate_h_g1_sample_expansion_plan.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_h_g1_sample_expansion_plan", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load H-G1 sample-expansion plan validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ValidateHG1SampleExpansionPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator()

    def test_current_plan_artifact_passes(self) -> None:
        result = self.validator.validate_h_g1_sample_expansion_plan()

        self.assertEqual("pass", result["status"])
        self.assertEqual("keep_h_g1_parked_with_preregistered_sample_expansion_requirements", result["decision"])
        self.assertEqual("run_no_paid_local_cache_overlap_scan_or_return_to_news_unblock", result["selected_next_safe_action"])
        self.assertEqual(4, result["step_count"])
        self.assertEqual(2, result["source_intersection_closed_trade_count"])
        self.assertFalse(result["paid_download_allowed_by_this_artifact"])

    def test_blocks_paid_or_strategy_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_path = root / "plan.json"
            post_ablation_path = root / "post.json"
            ablation_path = root / "ablation.json"
            plan = json.loads((PROJECT_ROOT / "experiments" / "h_g1_sample_expansion_plan.json").read_text(encoding="utf-8"))
            post = json.loads((PROJECT_ROOT / "experiments" / "h_g1_post_ablation_decision.json").read_text(encoding="utf-8"))
            ablation = json.loads((PROJECT_ROOT / "reports" / "experiments" / "h_g1_gamma_strategy_ablation_summary.json").read_text(encoding="utf-8"))
            plan["paid_data_approved"] = True
            plan["strategy_use_allowed"] = True
            plan["cost_policy"]["paid_download_allowed_by_this_artifact"] = True
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            post_ablation_path.write_text(json.dumps(post), encoding="utf-8")
            ablation_path.write_text(json.dumps(ablation), encoding="utf-8")

            result = self.validator.validate_h_g1_sample_expansion_plan(plan_path, post_ablation_path, ablation_path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("paid_data_approved_must_be_false", result["blockers"])
        self.assertIn("strategy_use_allowed_must_be_false", result["blockers"])
        self.assertIn("paid_download_must_not_be_allowed_by_plan", result["blockers"])


if __name__ == "__main__":
    unittest.main()
