from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

from lib.environment import data_root
from tests.tiers import state_audit


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "run_h_g1_bucket_policy_comparison.py"


def load_module():
    spec = importlib.util.spec_from_file_location("run_h_g1_bucket_policy_comparison", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load H-G1 bucket-policy comparison module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@state_audit(("HIGANBANA_DATA_ROOT", data_root()))
class H_G1BucketPolicyComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()

    def test_current_manifest_v3_policy_comparison_is_review_only(self) -> None:
        result = self.module.run_comparison()

        self.assertEqual("policy_review_complete_h_g1_still_blocked", result["status"])
        self.assertFalse(result["network_used"])
        self.assertFalse(result["paid_data_used"])
        self.assertFalse(result["strategy_pnl_used"])
        self.assertFalse(result["recommendation"]["policy_adopted_now"])
        self.assertFalse(result["recommendation"]["strategy_use_allowed"])
        self.assertEqual(
            "candidate_b_side_aware_required_bucket",
            result["recommendation"]["recommended_for_separate_policy_adoption_review"],
        )

    def test_side_aware_candidate_passes_where_current_v2_is_blocked(self) -> None:
        result = self.module.run_comparison()
        current_v2 = result["candidate_results"]["candidate_a_current_v2_moneyness_only"]
        side_aware = result["candidate_results"]["candidate_b_side_aware_required_bucket"]

        self.assertEqual("policy_candidate_blocked", current_v2["status"])
        self.assertGreater(current_v2["failure_count"], 0)
        self.assertEqual("policy_candidate_passes_coverage_review", side_aware["status"])
        self.assertEqual(0, side_aware["failure_count"])

    def test_notional_candidate_preserves_economic_notional_blockers(self) -> None:
        result = self.module.run_comparison()
        notional = result["candidate_results"]["candidate_c_notional_weighted_coverage"]

        self.assertEqual("policy_candidate_blocked", notional["status"])
        self.assertTrue(any("oi_notional_share_below_floor" in failure for failure in notional["failures"]))
        self.assertGreater(len(notional["warnings"]), 0)


if __name__ == "__main__":
    unittest.main()
