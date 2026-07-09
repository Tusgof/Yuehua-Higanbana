from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = PROJECT_ROOT / "scripts" / "run_h_b2_falsification_review.py"
VALIDATOR_PATH = PROJECT_ROOT / "scripts" / "validate_h_b2_falsification_review.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HB2FalsificationReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = load_module(RUNNER_PATH, "run_h_b2_falsification_review")
        cls.validator = load_module(VALIDATOR_PATH, "validate_h_b2_falsification_review")

    def test_runner_keeps_current_grid_parked_without_deployment_claim(self) -> None:
        result = self.runner.run_review()

        self.assertEqual("review_complete", result["status"])
        self.assertEqual("keep_h_b2_parked_current_grid_not_resurrected", result["decision"])
        self.assertTrue(result["current_grid_failed_preregistered_keep_active_rule"])
        self.assertFalse(result["acceptance_grade_falsified"])
        self.assertFalse(result["paper_trading_allowed"])
        self.assertFalse(result["paid_data_used"])
        self.assertEqual([], result["positive_total_and_oos_scenarios"])
        self.assertEqual(8, len(result["scenario_reviews"]))

    def test_validator_accepts_current_review_after_write(self) -> None:
        result = self.runner.run_review()
        with tempfile.TemporaryDirectory() as tmp:
            review_path = Path(tmp) / "review.json"
            review_path.write_text(json.dumps(result), encoding="utf-8")

            validation = self.validator.validate_review(review_path)

        self.assertEqual("pass", validation["status"])
        self.assertEqual("keep_h_b2_parked_current_grid_not_resurrected", validation["decision"])

    def test_validator_rejects_paper_trading_or_overclaim(self) -> None:
        result = self.runner.run_review()
        result["paper_trading_allowed"] = True
        result["acceptance_grade_falsified"] = True

        with tempfile.TemporaryDirectory() as tmp:
            review_path = Path(tmp) / "review.json"
            review_path.write_text(json.dumps(result), encoding="utf-8")

            validation = self.validator.validate_review(review_path)

        self.assertEqual("blocked", validation["status"])
        self.assertIn("paper_trading_allowed_must_be_false", validation["blockers"])
        self.assertIn("acceptance_grade_falsified_must_remain_false", validation["blockers"])


if __name__ == "__main__":
    unittest.main()
