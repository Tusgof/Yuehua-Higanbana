from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "run_h_g1_acceptance_blocker_review.py"


def load_module():
    spec = importlib.util.spec_from_file_location("run_h_g1_acceptance_blocker_review", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load H-G1 acceptance blocker review module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class H_G1AcceptanceBlockerReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()

    def test_current_review_blocks_strategy_use_after_data_validity_pass(self) -> None:
        result = self.module.run_review()

        self.assertEqual("blocked_before_strategy_use", result["status"])
        self.assertEqual("H-G1", result["hypothesis_id"])
        self.assertEqual("E1", result["evidence_tier"])
        self.assertFalse(result["network_used"])
        self.assertFalse(result["paid_data_used"])
        self.assertFalse(result["strategy_pnl_used"])
        self.assertFalse(result["strategy_use_allowed"])
        self.assertFalse(result["paper_trading_allowed"])
        self.assertEqual("pass_diagnostic_only", result["passed_data_validity_facts"]["diagnostic_status"])
        self.assertEqual("h_g1_required_bucket_policy_v3_side_aware", result["passed_data_validity_facts"]["policy_id"])
        self.assertEqual(6, result["blocker_summary"]["hard_blocker_count"])
        self.assertIn("strategy_ablation_missing", result["blocker_summary"]["hard_blockers"])
        self.assertIn("mintrl_psr_missing", result["blocker_summary"]["hard_blockers"])
        self.assertIn("dsr_search_log_missing", result["blocker_summary"]["hard_blockers"])
        self.assertIn("implementable_pnl_missing", result["blocker_summary"]["hard_blockers"])
        self.assertIn("proxy_inventory_caveat", result["blocker_summary"]["hard_blockers"])
        self.assertIn("H-G1 strategy edge validated", result["forbidden_claims_preserved"])

    def test_write_outputs_persists_json_and_markdown(self) -> None:
        result = self.module.run_review()
        with tempfile.TemporaryDirectory() as tmp:
            output_json = Path(tmp) / "review.json"
            output_report = Path(tmp) / "review.md"
            self.module.write_outputs(result, output_json, output_report)

            written = json.loads(output_json.read_text(encoding="utf-8"))
            report = output_report.read_text(encoding="utf-8")

        self.assertEqual(result["status"], written["status"])
        self.assertIn("H-G1 Acceptance Blocker Review", report)
        self.assertIn("strategy_ablation_missing", report)
        self.assertIn("MinTRL", report)
        self.assertIn("Strategy PnL used: `False`", report)

    def test_rejects_diagnostic_that_already_allows_strategy_use(self) -> None:
        diagnostic = json.loads(self.module.H_G1_SIDE_AWARE_DIAGNOSTIC.read_text(encoding="utf-8"))
        diagnostic["strategy_use_allowed"] = True

        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "bad_diagnostic.json"
            input_path.write_text(json.dumps(diagnostic), encoding="utf-8")

            with self.assertRaises(ValueError):
                self.module.run_review(input_path)


if __name__ == "__main__":
    unittest.main()
