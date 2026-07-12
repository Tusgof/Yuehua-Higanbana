from __future__ import annotations

import json
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class RetentionAndStressCostPlanTests(unittest.TestCase):
    def test_retention_dry_run_records_approval_without_archiving(self) -> None:
        policy = (PROJECT_ROOT / "docs" / "REPORT_RETENTION_POLICY_PROPOSAL.md").read_text(encoding="utf-8")
        manifest = json.loads(
            (PROJECT_ROOT / "reports" / "diagnostics" / "report_retention_dry_run_2026_07_12.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn("**User-approved**: `true`", policy)
        self.assertEqual("dry_run_no_changes", manifest["mode"])
        self.assertEqual([], manifest["entries"])
        self.assertEqual(0, manifest["operations"]["files_moved"])
        self.assertEqual(0, manifest["operations"]["files_deleted"])
        self.assertTrue(manifest["scan_evidence"]["cutoff_predates_all_tracked_report_history"])

    def test_stress_cost_plan_is_staged_and_does_not_purchase(self) -> None:
        plan = json.loads(
            (PROJECT_ROOT / "reports" / "data_cost" / "h_a2_2022_h2_stress_decision_tree_cost_plan.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(13, len(plan["october_stress_dates"]))
        self.assertAlmostEqual(11.726392, plan["cost_summary"]["total_projected_new_cash_cost_usd"])
        self.assertLessEqual(
            plan["cost_summary"]["total_projected_new_cash_cost_usd"],
            plan["decision_tree"]["Q2_falsification_cost_guard"]["effective_plan_guard_usd"],
        )
        self.assertFalse(plan["cost_summary"]["purchase_executed"])
        self.assertFalse(plan["guardrails"]["paid_download_executed"])
        self.assertEqual("not_applicable", plan["decision_tree"]["Q4_field_unlock"]["result"])
        self.assertEqual(2, plan["trade_density_checkpoint"]["minimum_candidate_ready_trades_to_consider_stage_2"])


if __name__ == "__main__":
    unittest.main()
