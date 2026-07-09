from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.environment import ibkr_python


def run_step(name: str, args: list[str]) -> dict[str, object]:
    env = os.environ.copy()
    if name == "unit_tests":
        env["SPY0DTE_FIXTURE_PIPELINE_CHILD"] = "1"
    step_args = args
    package_python = ibkr_python()
    if name == "probe_ibkr_spy_bars_readiness" and package_python is not None and package_python.exists():
        step_args = [*args, "--package-python", str(package_python)]
    completed = subprocess.run(
        [sys.executable, *step_args],
        cwd=PROJECT_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "name": name,
        "command": " ".join([Path(sys.executable).name, *step_args]),
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def main() -> int:
    steps = [
        ("validate_m2_contracts", ["scripts/validate_m2_contracts.py"]),
        ("validate_exp07_policy_cases", ["scripts/validate_exp07_policy_cases.py"]),
        ("evaluate_exp07_acceptance", ["scripts/evaluate_exp07_acceptance.py"]),
        ("validate_exp07_strategy_ablation_plan", ["scripts/validate_exp07_strategy_ablation_plan.py"]),
        ("run_exp07_strategy_ablation_status", ["scripts/run_exp07_strategy_ablation.py"]),
        ("validate_m3_experiment_guardrails", ["scripts/validate_m3_experiment_guardrails.py"]),
        ("audit_m3_backtest_reporting_hardening", ["scripts/audit_m3_backtest_reporting_hardening.py"]),
        ("validate_macro_calendar_sources", ["scripts/validate_macro_calendar_sources.py"]),
        (
            "macro_calendar_capture_dry_run",
            [
                "scripts/capture_macro_calendar_snapshots.py",
                "--as-of-date",
                "2024-01-03",
            ],
        ),
        (
            "convert_macro_calendar_capture_check",
            [
                "scripts/convert_macro_calendar_capture.py",
                "--capture-root",
                "data/raw/spy_0dte/macro_calendar/2026-06-30",
                "--output-path",
                "build/macro_calendar_capture_convert/official_macro_calendar_2026-06-30.csv",
            ],
        ),
        (
            "import_converted_macro_calendar_capture",
            [
                "scripts/import_macro_calendar_snapshots.py",
                "--snapshot-path",
                "build/macro_calendar_capture_convert/official_macro_calendar_2026-06-30.csv",
                "--output-root",
                "build/macro_calendar_capture_import",
            ],
        ),
        ("audit_macro_calendar_coverage", ["scripts/audit_macro_calendar_coverage.py"]),
        (
            "plan_macro_calendar_capture_commands",
            [
                "scripts/plan_macro_calendar_capture_commands.py",
                "--start-year",
                "2022",
                "--end-year",
                "2025",
            ],
        ),
        (
            "audit_macro_calendar_raw_archive",
            [
                "scripts/audit_macro_calendar_raw_archive.py",
                "--start-year",
                "2022",
                "--end-year",
                "2025",
            ],
        ),
        (
            "vix_vxv_capture_dry_run",
            [
                "scripts/capture_vix_vxv_cboe.py",
                "--as-of-date",
                "2026-06-30",
            ],
        ),
        (
            "import_vix_vxv_cboe",
            [
                "scripts/import_vix_vxv_cboe.py",
                "--capture-root",
                "data/raw/spy_0dte/vix_vxv/2026-06-30",
                "--start-date",
                "2022-01-01",
                "--end-date",
                "2026-06-30",
            ],
        ),
        (
            "audit_vix_vxv_coverage",
            [
                "scripts/audit_vix_vxv_coverage.py",
                "--as-of-date",
                "2026-06-30",
            ],
        ),
        ("validate_news_sources", ["scripts/validate_news_sources.py"]),
        (
            "gdelt_news_capture_dry_run",
            [
                "scripts/capture_gdelt_news_snapshots.py",
                "--decision-time-et",
                "2024-01-03T09:30:00-05:00",
                "--max-records",
                "5",
            ],
        ),
        ("plan_gdelt_news_capture_commands", ["scripts/plan_gdelt_news_capture_commands.py"]),
        ("plan_exp07_real_news_cases", ["scripts/plan_exp07_real_news_cases.py"]),
        ("validate_exp07_real_news_case_plan", ["scripts/validate_exp07_real_news_case_plan.py"]),
        ("audit_news_coverage", ["scripts/audit_news_coverage.py"]),
        ("audit_paid_costs", ["scripts/audit_paid_costs.py"]),
        ("audit_strategy_data_readiness", ["scripts/audit_strategy_data_readiness.py"]),
        ("validate_hypothesis_registry", ["scripts/validate_hypothesis_registry.py"]),
        ("validate_evidence_tiers", ["scripts/validate_evidence_tiers.py"]),
        ("run_h_b2_falsification_review", ["scripts/run_h_b2_falsification_review.py"]),
        ("validate_h_b2_falsification_review", ["scripts/validate_h_b2_falsification_review.py"]),
        ("validate_h_g1_regime_date_set", ["scripts/validate_h_g1_regime_date_set.py"]),
        ("validate_h_g1_manifest_v3_plan", ["scripts/validate_h_g1_manifest_v3_plan.py"]),
        ("select_h_g1_manifest_v3_replacement", ["scripts/select_h_g1_manifest_v3_replacement.py"]),
        ("validate_h_g1_gamma_strategy_ablation_preregistration", ["scripts/validate_h_g1_gamma_strategy_ablation_preregistration.py"]),
        ("validate_h_g1_gamma_strategy_ablation_summary", ["scripts/validate_h_g1_gamma_strategy_ablation_summary.py"]),
        ("validate_h_g1_post_ablation_decision", ["scripts/validate_h_g1_post_ablation_decision.py"]),
        ("validate_h_g1_sample_expansion_plan", ["scripts/validate_h_g1_sample_expansion_plan.py"]),
        ("run_h_g1_local_cache_overlap_scan", ["scripts/run_h_g1_local_cache_overlap_scan.py"]),
        ("validate_h_g1_local_cache_overlap_scan", ["scripts/validate_h_g1_local_cache_overlap_scan.py"]),
        ("validate_h_a2_2022_10_single_month_decision", ["scripts/validate_h_a2_2022_10_single_month_decision.py"]),
        ("validate_h_a2_2022_spy_bar_source_decision", ["scripts/validate_h_a2_2022_spy_bar_source_decision.py"]),
        (
            "validate_h_a2_2022_10_coarse_stress_preregistration",
            ["scripts/validate_h_a2_2022_10_coarse_stress_preregistration.py"],
        ),
        ("run_h_a2_2022_10_coarse_stress_review", ["scripts/run_h_a2_2022_10_coarse_stress_review.py"]),
        ("validate_h_a2_2022_10_coarse_stress_review", ["scripts/validate_h_a2_2022_10_coarse_stress_review.py"]),
        ("validate_h_a2_followup_resolution_preregistration", ["scripts/validate_h_a2_followup_resolution_preregistration.py"]),
        (
            "validate_h_a2_lower_resolution_proxy_preregistration",
            ["scripts/validate_h_a2_lower_resolution_proxy_preregistration.py"],
        ),
        ("run_h_a2_lower_resolution_proxy", ["scripts/run_h_a2_lower_resolution_proxy.py"]),
        ("validate_h_a2_lower_resolution_proxy_summary", ["scripts/validate_h_a2_lower_resolution_proxy_summary.py"]),
        ("run_h_a2_proxy_first_robustness", ["scripts/run_h_a2_proxy_first_robustness.py"]),
        ("validate_h_a2_proxy_first_robustness_summary", ["scripts/validate_h_a2_proxy_first_robustness_summary.py"]),
        ("validate_h_a2_exact_data_prioritization_decision", ["scripts/validate_h_a2_exact_data_prioritization_decision.py"]),
        ("validate_h_a2_exact_2022_underlying_bar_plan", ["scripts/validate_h_a2_exact_2022_underlying_bar_plan.py"]),
        ("acquire_h_a2_2022_spy_bars_fixture", ["scripts/acquire_h_a2_2022_spy_bars.py", "--mode", "fixture"]),
        ("probe_ibkr_spy_bars_readiness", ["scripts/probe_ibkr_spy_bars_readiness.py"]),
        ("run_h_l1_macro_event_proxy_baseline", ["scripts/run_h_l1_macro_event_proxy_baseline.py"]),
        ("validate_h_l1_macro_event_proxy_baseline_summary", ["scripts/validate_h_l1_macro_event_proxy_baseline_summary.py"]),
        ("validate_h_a2_h_l1_post_proxy_decision", ["scripts/validate_h_a2_h_l1_post_proxy_decision.py"]),
        (
            "validate_h_a2_residual_adverse_day_preregistration",
            ["scripts/validate_h_a2_residual_adverse_day_preregistration.py"],
        ),
        ("run_h_a2_residual_adverse_day_analysis", ["scripts/run_h_a2_residual_adverse_day_analysis.py"]),
        ("validate_h_a2_residual_adverse_day_analysis", ["scripts/validate_h_a2_residual_adverse_day_analysis.py"]),
        (
            "validate_h_a2_revised_opening_followthrough_preregistration",
            ["scripts/validate_h_a2_revised_opening_followthrough_preregistration.py"],
        ),
        (
            "run_h_a2_revised_opening_followthrough_condition",
            ["scripts/run_h_a2_revised_opening_followthrough_condition.py"],
        ),
        (
            "validate_h_a2_revised_opening_followthrough_condition",
            ["scripts/validate_h_a2_revised_opening_followthrough_condition.py"],
        ),
        (
            "validate_h_a2_revised_condition_robustness_preregistration",
            ["scripts/validate_h_a2_revised_condition_robustness_preregistration.py"],
        ),
        (
            "run_h_a2_revised_condition_robustness",
            ["scripts/run_h_a2_revised_condition_robustness.py"],
        ),
        (
            "validate_h_a2_revised_condition_robustness",
            ["scripts/validate_h_a2_revised_condition_robustness.py"],
        ),
        (
            "validate_h_a2_locked_condition_signal_attribution_preregistration",
            ["scripts/validate_h_a2_locked_condition_signal_attribution_preregistration.py"],
        ),
        (
            "run_h_a2_locked_condition_signal_attribution",
            ["scripts/run_h_a2_locked_condition_signal_attribution.py"],
        ),
        (
            "validate_h_a2_locked_condition_signal_attribution",
            ["scripts/validate_h_a2_locked_condition_signal_attribution.py"],
        ),
        (
            "validate_h_a2_delayed_entry_condition_preregistration",
            ["scripts/validate_h_a2_delayed_entry_condition_preregistration.py"],
        ),
        (
            "run_h_a2_delayed_entry_condition",
            ["scripts/run_h_a2_delayed_entry_condition.py"],
        ),
        (
            "validate_h_a2_delayed_entry_condition",
            ["scripts/validate_h_a2_delayed_entry_condition.py"],
        ),
        (
            "validate_h_a2_original_entry_revision_preregistration",
            ["scripts/validate_h_a2_original_entry_revision_preregistration.py"],
        ),
        (
            "run_h_a2_original_entry_revision",
            ["scripts/run_h_a2_original_entry_revision.py"],
        ),
        (
            "validate_h_a2_original_entry_revision",
            ["scripts/validate_h_a2_original_entry_revision.py"],
        ),
        (
            "validate_h_a2_original_entry_robustness_prioritization_preregistration",
            ["scripts/validate_h_a2_original_entry_robustness_prioritization_preregistration.py"],
        ),
        (
            "run_h_a2_original_entry_robustness_prioritization",
            ["scripts/run_h_a2_original_entry_robustness_prioritization.py"],
        ),
        (
            "validate_h_a2_original_entry_robustness_prioritization",
            ["scripts/validate_h_a2_original_entry_robustness_prioritization.py"],
        ),
        (
            "validate_h_a2_independent_validation_feasibility_preregistration",
            ["scripts/validate_h_a2_independent_validation_feasibility_preregistration.py"],
        ),
        (
            "run_h_a2_independent_validation_feasibility",
            ["scripts/run_h_a2_independent_validation_feasibility.py"],
        ),
        (
            "validate_h_a2_independent_validation_feasibility",
            ["scripts/validate_h_a2_independent_validation_feasibility.py"],
        ),
        (
            "validate_h_a2_independent_validation_paid_cost_plan_preregistration",
            ["scripts/validate_h_a2_independent_validation_paid_cost_plan_preregistration.py"],
        ),
        (
            "validate_h_a2_independent_validation_paid_download_decision",
            ["scripts/validate_h_a2_independent_validation_paid_download_decision.py"],
        ),
        (
            "validate_h_a2_normal_control_paid_download_decision",
            ["scripts/validate_h_a2_normal_control_paid_download_decision.py"],
        ),
        (
            "validate_h_a2_normal_control_download_result",
            ["scripts/validate_h_a2_normal_control_download_result.py"],
        ),
        (
            "validate_h_a2_normal_control_import_diagnostic_preregistration",
            ["scripts/validate_h_a2_normal_control_import_diagnostic_preregistration.py"],
        ),
        (
            "validate_h_a2_normal_control_import_diagnostic",
            ["scripts/validate_h_a2_normal_control_import_diagnostic.py"],
        ),
        (
            "validate_h_a2_normal_control_exact_replay_preregistration",
            ["scripts/validate_h_a2_normal_control_exact_replay_preregistration.py"],
        ),
        (
            "validate_h_a2_normal_control_exact_replay",
            ["scripts/validate_h_a2_normal_control_exact_replay.py"],
        ),
        (
            "validate_h_a2_post_exact_replay_sample_expansion_decision",
            ["scripts/validate_h_a2_post_exact_replay_sample_expansion_decision.py"],
        ),
        (
            "validate_h_a2_post_stress_normalization_control_paid_download_decision",
            ["scripts/validate_h_a2_post_stress_normalization_control_paid_download_decision.py"],
        ),
        (
            "validate_h_a2_post_stress_normalization_control_import_diagnostic_preregistration",
            [
                "scripts/validate_h_a2_post_stress_normalization_control_import_diagnostic_preregistration.py"
            ],
        ),
        (
            "validate_h_a2_post_stress_normalization_control_import_diagnostic",
            ["scripts/validate_h_a2_post_stress_normalization_control_import_diagnostic.py"],
        ),
        (
            "validate_h_a2_post_stress_normalization_control_exact_replay_preregistration",
            [
                "scripts/validate_h_a2_post_stress_normalization_control_exact_replay_preregistration.py"
            ],
        ),
        (
            "validate_h_a2_post_stress_normalization_control_exact_replay",
            ["scripts/validate_h_a2_post_stress_normalization_control_exact_replay.py"],
        ),
        (
            "validate_h_a2_post_two_exact_replay_decision",
            ["scripts/validate_h_a2_post_two_exact_replay_decision.py"],
        ),
        (
            "validate_h_a2_mechanism_revision_preregistration",
            ["scripts/validate_h_a2_mechanism_revision_preregistration.py"],
        ),
        (
            "validate_h_a2_mechanism_revision_audit",
            ["scripts/validate_h_a2_mechanism_revision_audit.py"],
        ),
        (
            "validate_h_a2_breakeven_aware_rule_preregistration",
            ["scripts/validate_h_a2_breakeven_aware_rule_preregistration.py"],
        ),
        (
            "validate_h_a2_breakeven_aware_rule_train_diagnostic",
            ["scripts/validate_h_a2_breakeven_aware_rule_train_diagnostic.py"],
        ),
        (
            "validate_h_a2_targeted_data_regime_expansion_plan",
            ["scripts/validate_h_a2_targeted_data_regime_expansion_plan.py"],
        ),
        (
            "validate_h_a2_independent_validation_download_result",
            ["scripts/validate_h_a2_independent_validation_download_result.py"],
        ),
        (
            "validate_h_a2_independent_validation_import_diagnostic_preregistration",
            ["scripts/validate_h_a2_independent_validation_import_diagnostic_preregistration.py"],
        ),
        (
            "run_h_a2_independent_validation_import_diagnostic",
            ["scripts/run_h_a2_independent_validation_import_diagnostic.py"],
        ),
        (
            "validate_h_a2_independent_validation_import_diagnostic",
            ["scripts/validate_h_a2_independent_validation_import_diagnostic.py"],
        ),
        (
            "validate_h_g1_regime_date_set_v3",
            [
                "scripts/validate_h_g1_regime_date_set.py",
                "--manifest-path",
                "experiments/h_g1_gamma_regime_date_set_preregistration_v3.json",
            ],
        ),
        ("audit_research_readiness", ["scripts/audit_research_readiness.py"]),
        ("evaluate_research_acceptance", ["scripts/evaluate_research_acceptance.py"]),
        ("audit_real_money_launch_gate", ["scripts/audit_real_money_launch_gate.py"]),
        ("audit_research_logs", ["scripts/audit_research_logs.py"]),
        (
            "import_macro_calendar_snapshot_fixture",
            [
                "scripts/import_macro_calendar_snapshots.py",
                "--output-root",
                "build/macro_calendar_fixture",
            ],
        ),
        (
            "import_news_snapshot_fixture",
            [
                "scripts/import_news_snapshots.py",
                "--output-root",
                "build/news_fixture",
            ],
        ),
        (
            "import_gdelt_news_capture_directory_fixture",
            [
                "scripts/import_gdelt_news_capture_directory.py",
                "--input-dir",
                "tests/fixtures/news_snapshots",
                "--pattern",
                "gdelt_news_sample.csv",
                "--output-root",
                "build/news_gdelt_capture_import",
            ],
        ),
        ("validate_provider_samples", ["scripts/provider_adapters.py"]),
        (
            "databento_cost_dry_run",
            [
                "scripts/estimate_databento_cost.py",
                "--scenario",
                "one_day_sample",
                "--report-path",
                "reports/data_cost/databento_cost_dry_run.md",
            ],
        ),
        (
            "databento_cache_audit",
            [
                "scripts/audit_databento_cache.py",
                "--plan-path",
                "reports/data_cost/databento_download_plan.json",
                "--report-path",
                "reports/data_cost/databento_cache_audit.md",
                "--json-report-path",
                "reports/data_cost/databento_cache_audit.json",
            ],
        ),
        (
            "import_provider_sample_fixture",
            [
                "scripts/import_provider_sample.py",
                "--provider",
                "optionsdx",
                "--raw-path",
                "tests/fixtures/provider_samples/optionsdx_option_quote_sample.csv",
                "--output-root",
                "build/provider_sample_fixture",
            ],
        ),
        ("import_m3_fixture", ["scripts/import_m3_fixture.py"]),
        ("generate_m6_reports", ["scripts/experiment_runner_m6.py"]),
        ("unit_tests", ["-m", "unittest", "discover", "-s", "tests"]),
    ]
    results = [run_step(name, args) for name, args in steps]
    failed = [result for result in results if result["returncode"] != 0]
    summary = {
        "status": "fail" if failed else "pass",
        "project_root": str(PROJECT_ROOT),
        "steps": results,
        "important_outputs": {
            "final_review": str(PROJECT_ROOT / "reports" / "final_research_review.md"),
            "user_inputs": str(PROJECT_ROOT / "docs" / "NEXT_USER_INPUTS.md"),
            "paid_cost": str(PROJECT_ROOT / "reports" / "data_cost" / "paid_cost_audit.md"),
            "strategy_data_readiness": str(PROJECT_ROOT / "reports" / "strategy_data_readiness_audit.md"),
            "hypothesis_registry": str(PROJECT_ROOT / "reports" / "hypothesis_registry_audit.md"),
            "evidence_tiers": str(PROJECT_ROOT / "reports" / "evidence_tier_audit.md"),
            "h_g1_regime_date_set": str(PROJECT_ROOT / "experiments" / "h_g1_gamma_regime_date_set_preregistration.json"),
            "h_g1_manifest_v3_plan": str(PROJECT_ROOT / "experiments" / "h_g1_gamma_regime_date_set_preregistration_v3_plan.json"),
            "h_g1_manifest_v3": str(PROJECT_ROOT / "experiments" / "h_g1_gamma_regime_date_set_preregistration_v3.json"),
            "h_g1_gamma_strategy_ablation_preregistration": str(
                PROJECT_ROOT / "experiments" / "h_g1_gamma_strategy_ablation_preregistration.json"
            ),
            "h_g1_sample_expansion_plan": str(PROJECT_ROOT / "experiments" / "h_g1_sample_expansion_plan.json"),
            "h_g1_manifest_v3_candidate_selection": str(PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_manifest_v3_candidate_selection.md"),
            "h_a2_lower_resolution_proxy_preregistration": str(
                PROJECT_ROOT / "docs" / "H_A2_LOWER_RESOLUTION_PROXY_PREREGISTRATION.md"
            ),
            "h_a2_exact_data_prioritization_decision": str(
                PROJECT_ROOT / "docs" / "H_A2_EXACT_DATA_PRIORITIZATION_DECISION.md"
            ),
            "h_a2_exact_2022_underlying_bar_plan": str(
                PROJECT_ROOT / "docs" / "H_A2_EXACT_2022_UNDERLYING_BAR_PLAN.md"
            ),
            "h_a2_proxy_first_robustness": str(
                PROJECT_ROOT / "reports" / "experiments" / "h_a2_proxy_first_robustness_report.md"
            ),
            "h_l1_macro_event_proxy_baseline": str(
                PROJECT_ROOT / "reports" / "experiments" / "h_l1_macro_event_proxy_baseline_report.md"
            ),
            "h_a2_h_l1_post_proxy_decision": str(PROJECT_ROOT / "docs" / "H_A2_H_L1_POST_PROXY_DECISION.md"),
            "h_a2_residual_adverse_day_preregistration": str(
                PROJECT_ROOT / "docs" / "H_A2_RESIDUAL_ADVERSE_DAY_ANALYSIS_PREREGISTRATION.md"
            ),
            "h_a2_residual_adverse_day_analysis": str(
                PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_residual_adverse_day_analysis.md"
            ),
            "h_a2_revised_opening_followthrough_preregistration": str(
                PROJECT_ROOT / "docs" / "H_A2_REVISED_OPENING_FOLLOWTHROUGH_CONDITION_PREREGISTRATION.md"
            ),
            "h_a2_revised_opening_followthrough_condition": str(
                PROJECT_ROOT / "reports" / "experiments" / "h_a2_revised_opening_followthrough_condition_report.md"
            ),
            "h_a2_revised_condition_robustness_preregistration": str(
                PROJECT_ROOT / "docs" / "H_A2_REVISED_CONDITION_ROBUSTNESS_PREREGISTRATION.md"
            ),
            "h_a2_revised_condition_robustness": str(
                PROJECT_ROOT / "reports" / "experiments" / "h_a2_revised_condition_robustness_report.md"
            ),
            "h_a2_locked_condition_signal_attribution_preregistration": str(
                PROJECT_ROOT / "docs" / "H_A2_LOCKED_CONDITION_SIGNAL_ATTRIBUTION_PREREGISTRATION.md"
            ),
            "h_a2_locked_condition_signal_attribution": str(
                PROJECT_ROOT / "reports" / "experiments" / "h_a2_locked_condition_signal_attribution_report.md"
            ),
            "h_a2_delayed_entry_condition_preregistration": str(
                PROJECT_ROOT / "docs" / "H_A2_DELAYED_ENTRY_CONDITION_PREREGISTRATION.md"
            ),
            "h_a2_delayed_entry_condition": str(
                PROJECT_ROOT / "reports" / "experiments" / "h_a2_delayed_entry_condition_report.md"
            ),
            "h_a2_original_entry_robustness_prioritization_preregistration": str(
                PROJECT_ROOT / "docs" / "H_A2_ORIGINAL_ENTRY_ROBUSTNESS_PRIORITIZATION_PREREGISTRATION.md"
            ),
            "h_a2_original_entry_robustness_prioritization": str(
                PROJECT_ROOT / "reports" / "experiments" / "h_a2_original_entry_robustness_prioritization_report.md"
            ),
            "h_a2_2022_spy_bars_acquisition_manifest": str(
                PROJECT_ROOT / "reports" / "data_cost" / "h_a2_2022_spy_bars_acquisition_manifest.json"
            ),
            "h_a2_2022_spy_bars_coverage_audit": str(
                PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_2022_spy_bars_coverage_audit.md"
            ),
            "research_readiness": str(PROJECT_ROOT / "reports" / "research_readiness_audit.md"),
            "research_acceptance": str(PROJECT_ROOT / "reports" / "research_acceptance_evaluation.md"),
            "real_money_launch_gate": str(PROJECT_ROOT / "reports" / "real_money_launch_gate_audit.md"),
            "research_logs": str(PROJECT_ROOT / "reports" / "research_log_audit.md"),
        },
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
