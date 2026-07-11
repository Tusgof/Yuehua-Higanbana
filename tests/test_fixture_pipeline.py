from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from unittest import mock
from pathlib import Path

from lib.environment import data_root, wiki_root
from tests.tiers import state_audit


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class FixturePipelineTests(unittest.TestCase):
    @state_audit(
        ("HIGANBANA_DATA_ROOT", data_root()),
        ("HIGANBANA_WIKI_ROOT", wiki_root()),
        ("research_log", PROJECT_ROOT / "research_log"),
    )
    def test_fixture_pipeline_preserves_expected_gates(self) -> None:
        if os.environ.get("SPY0DTE_FIXTURE_PIPELINE_CHILD") == "1":
            self.skipTest("avoid recursive pipeline execution")
        completed = subprocess.run(
            [sys.executable, "scripts/run_fixture_pipeline.py"],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        summary = json.loads(completed.stdout)
        failing_steps = [step for step in summary["steps"] if step["returncode"] != 0]
        if failing_steps:
            self.assertEqual(1, completed.returncode, completed.stderr)
            self.assertEqual(["audit_research_logs"], [step["name"] for step in failing_steps])
            self.assertIn("research_log_worktree_not_clean", failing_steps[0]["stdout"])
            self.assertEqual("fail", summary["status"])
        else:
            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual("pass", summary["status"])
        step_names = [step["name"] for step in summary["steps"]]
        for required_step in [
            "validate_m2_contracts",
            "validate_exp07_policy_cases",
            "evaluate_exp07_acceptance",
            "validate_exp07_strategy_ablation_plan",
            "run_exp07_strategy_ablation_status",
            "validate_macro_calendar_sources",
            "macro_calendar_capture_dry_run",
            "convert_macro_calendar_capture_check",
            "import_converted_macro_calendar_capture",
            "audit_macro_calendar_coverage",
            "plan_macro_calendar_capture_commands",
            "audit_macro_calendar_raw_archive",
            "validate_news_sources",
            "gdelt_news_capture_dry_run",
            "audit_news_coverage",
            "audit_paid_costs",
            "validate_hypothesis_registry",
            "validate_evidence_tiers",
            "validate_locked_gates",
            "audit_helper_drift",
            "audit_new_script_lib_usage",
            "validate_h_g1_regime_date_set",
            "validate_h_g1_manifest_v3_plan",
            "select_h_g1_manifest_v3_replacement",
            "validate_h_g1_gamma_strategy_ablation_preregistration",
            "validate_h_g1_gamma_strategy_ablation_summary",
            "validate_h_g1_post_ablation_decision",
            "validate_h_g1_sample_expansion_plan",
            "run_h_g1_local_cache_overlap_scan",
            "validate_h_g1_local_cache_overlap_scan",
            "validate_h_a2_2022_10_single_month_decision",
            "validate_h_a2_2022_spy_bar_source_decision",
            "validate_h_a2_2022_10_coarse_stress_preregistration",
            "run_h_a2_2022_10_coarse_stress_review",
            "validate_h_a2_2022_10_coarse_stress_review",
            "validate_h_a2_followup_resolution_preregistration",
            "validate_h_a2_lower_resolution_proxy_preregistration",
            "run_h_a2_lower_resolution_proxy",
            "validate_h_a2_lower_resolution_proxy_summary",
            "validate_h_a2_exact_data_prioritization_decision",
            "validate_h_a2_exact_2022_underlying_bar_plan",
            "acquire_h_a2_2022_spy_bars_fixture",
            "validate_h_a2_h_l1_post_proxy_decision",
            "validate_h_a2_residual_adverse_day_preregistration",
            "run_h_a2_residual_adverse_day_analysis",
            "validate_h_a2_residual_adverse_day_analysis",
            "validate_h_a2_revised_opening_followthrough_preregistration",
            "run_h_a2_revised_opening_followthrough_condition",
            "validate_h_a2_revised_opening_followthrough_condition",
            "validate_h_a2_revised_condition_robustness_preregistration",
            "run_h_a2_revised_condition_robustness",
            "validate_h_a2_revised_condition_robustness",
            "validate_h_a2_locked_condition_signal_attribution_preregistration",
            "run_h_a2_locked_condition_signal_attribution",
            "validate_h_a2_locked_condition_signal_attribution",
            "validate_h_a2_delayed_entry_condition_preregistration",
            "run_h_a2_delayed_entry_condition",
            "validate_h_a2_delayed_entry_condition",
            "validate_h_a2_original_entry_revision_preregistration",
            "run_h_a2_original_entry_revision",
            "validate_h_a2_original_entry_revision",
            "validate_h_a2_original_entry_robustness_prioritization_preregistration",
            "run_h_a2_original_entry_robustness_prioritization",
            "validate_h_a2_original_entry_robustness_prioritization",
            "validate_h_a2_independent_validation_feasibility_preregistration",
            "run_h_a2_independent_validation_feasibility",
            "validate_h_a2_independent_validation_feasibility",
            "validate_h_a2_independent_validation_paid_cost_plan_preregistration",
            "validate_h_a2_independent_validation_paid_download_decision",
            "validate_h_a2_normal_control_paid_download_decision",
            "validate_h_a2_normal_control_download_result",
            "validate_h_a2_normal_control_import_diagnostic_preregistration",
            "validate_h_a2_normal_control_import_diagnostic",
            "validate_h_a2_normal_control_exact_replay_preregistration",
            "validate_h_a2_normal_control_exact_replay",
            "validate_h_a2_post_exact_replay_sample_expansion_decision",
            "validate_h_a2_post_stress_normalization_control_paid_download_decision",
            "validate_h_a2_post_stress_normalization_control_import_diagnostic_preregistration",
            "validate_h_a2_post_stress_normalization_control_import_diagnostic",
            "validate_h_a2_post_stress_normalization_control_exact_replay_preregistration",
            "validate_h_a2_post_stress_normalization_control_exact_replay",
            "validate_h_a2_post_two_exact_replay_decision",
            "validate_h_a2_mechanism_revision_preregistration",
            "validate_h_a2_mechanism_revision_audit",
            "validate_h_a2_breakeven_aware_rule_preregistration",
            "validate_h_a2_breakeven_aware_rule_train_diagnostic",
            "validate_h_a2_targeted_data_regime_expansion_plan",
            "validate_h_a2_independent_validation_download_result",
            "validate_h_a2_independent_validation_import_diagnostic_preregistration",
            "run_h_a2_independent_validation_import_diagnostic",
            "validate_h_a2_independent_validation_import_diagnostic",
            "validate_h_g1_regime_date_set_v3",
            "audit_research_readiness",
            "evaluate_research_acceptance",
            "audit_real_money_launch_gate",
            "audit_research_logs",
            "import_macro_calendar_snapshot_fixture",
            "import_news_snapshot_fixture",
            "import_m3_fixture",
            "generate_m6_reports",
            "unit_tests",
        ]:
            self.assertIn(required_step, step_names)
        for step in summary["steps"]:
            if step["name"] == "audit_research_logs" and failing_steps:
                continue
            self.assertEqual(0, step["returncode"], step["name"])

        final_review = (PROJECT_ROOT / "reports" / "final_research_review.md").read_text(encoding="utf-8")
        self.assertIn("Gate status: `blocked`", final_review)
        self.assertIn("ยังสรุปไม่ได้", final_review)

    def test_ibkr_probe_step_uses_package_python_when_available(self) -> None:
        import scripts.run_fixture_pipeline as pipeline

        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout='{"status":"blocked_local_ibkr_unavailable"}',
            stderr="",
        )
        package_python = Path(sys.executable)
        with mock.patch.object(pipeline, "ibkr_python", return_value=package_python), mock.patch(
            "scripts.run_fixture_pipeline.subprocess.run",
            return_value=completed,
        ) as run:
            result = pipeline.run_step("probe_ibkr_spy_bars_readiness", ["scripts/probe_ibkr_spy_bars_readiness.py"])

        command_args = run.call_args.args[0]
        self.assertIn("--package-python", command_args)
        self.assertIn(str(package_python), command_args)
        self.assertIn("--package-python", result["command"])


if __name__ == "__main__":
    unittest.main()
