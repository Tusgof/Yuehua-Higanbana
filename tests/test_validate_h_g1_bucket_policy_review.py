from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "validate_h_g1_bucket_policy_review.py"
REVIEW_PATH = PROJECT_ROOT / "experiments" / "h_g1_bucket_policy_review_preregistration.json"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_h_g1_bucket_policy_review", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load H-G1 bucket-policy review validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class H_G1BucketPolicyReviewValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator()

    def test_current_review_passes(self) -> None:
        result = self.validator.validate_h_g1_bucket_policy_review(REVIEW_PATH)

        self.assertEqual("pass", result["status"])
        self.assertEqual("H-G1", result["hypothesis_id"])
        self.assertEqual(3, result["candidate_policy_count"])
        self.assertIn("candidate_b_side_aware_required_bucket", result["candidate_policy_ids"])

    def test_validator_rejects_paid_data_rerun(self) -> None:
        payload = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
        payload["rerun_policy"]["paid_data_allowed"] = True

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "review.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = self.validator.validate_h_g1_bucket_policy_review(path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("rerun_policy_paid_data_allowed_not_false", result["blockers"])

    def test_validator_rejects_missing_side_aware_candidate(self) -> None:
        payload = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
        payload["candidate_policies"] = [
            item
            for item in payload["candidate_policies"]
            if item["policy_id"] != "candidate_b_side_aware_required_bucket"
        ]

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "review.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = self.validator.validate_h_g1_bucket_policy_review(path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("missing_candidate_policy:candidate_b_side_aware_required_bucket", result["blockers"])

    def test_validator_rejects_strategy_pnl_selection(self) -> None:
        payload = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
        payload["rerun_policy"]["strategy_pnl_selection_allowed"] = True

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "review.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = self.validator.validate_h_g1_bucket_policy_review(path)

        self.assertEqual("blocked", result["status"])
        self.assertIn("rerun_policy_strategy_pnl_selection_allowed_not_false", result["blockers"])


if __name__ == "__main__":
    unittest.main()
