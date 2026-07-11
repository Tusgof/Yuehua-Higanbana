from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON_OUTPUT = PROJECT_ROOT / "reports" / "research_readiness_audit.json"
DEFAULT_REPORT_OUTPUT = PROJECT_ROOT / "reports" / "research_readiness_audit.md"
NEW_SCRIPT_LIB_USAGE_AUDIT = PROJECT_ROOT / "reports" / "diagnostics" / "new_script_lib_usage_audit.json"
GREEKS_OI_ENRICHMENT_REPORT = PROJECT_ROOT / "reports" / "greeks_oi_enrichment_probe_summary.json"
GAMMA_AGGREGATION_POLICY_DOC = PROJECT_ROOT / "docs" / "GAMMA_AGGREGATION_VALIDATION_POLICY.md"
GAMMA_AGGREGATION_DIAGNOSTIC_SUMMARY = PROJECT_ROOT / "reports" / "diagnostics" / "gamma_aggregation_diagnostic_summary.json"
H_G1_DATA_QUALITY_REVIEW = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_data_quality_review.json"
H_G1_V2_DIAGNOSTIC_SUMMARY = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_gamma_regime_diagnostic_summary_v2_10date.json"
H_G1_BUCKET_FAILURE_DIAGNOSTIC = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_bucket_failure_diagnostic.json"
H_G1_POLICY_MANIFEST_DECISION = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_policy_manifest_decision.json"
H_G1_POLICY_V2_1_REVIEW = PROJECT_ROOT / "docs" / "H_G1_POLICY_V2_1_REVIEW.md"
H_G1_MANIFEST_V3_PLAN = PROJECT_ROOT / "experiments" / "h_g1_gamma_regime_date_set_preregistration_v3_plan.json"
H_G1_MANIFEST_V3 = PROJECT_ROOT / "experiments" / "h_g1_gamma_regime_date_set_preregistration_v3.json"
H_G1_V3_REPLACEMENT_COST_ESTIMATE = PROJECT_ROOT / "reports" / "data_cost" / "h_g1_gamma_oi_v3_replacement_cost_estimate.json"
H_G1_V3_REPLACEMENT_DOWNLOAD_RESULT = PROJECT_ROOT / "reports" / "data_cost" / "h_g1_gamma_oi_download_result_v3_replacement.json"
H_G1_V3_DIAGNOSTIC_SUMMARY = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_gamma_regime_diagnostic_summary_v3.json"
H_G1_V3_BUCKET_FAILURE_DIAGNOSTIC = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_manifest_v3_bucket_failure_diagnostic.json"
H_G1_BUCKET_POLICY_REVIEW_PREREGISTRATION = PROJECT_ROOT / "experiments" / "h_g1_bucket_policy_review_preregistration.json"
H_G1_BUCKET_POLICY_COMPARISON = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_bucket_policy_comparison.json"
H_G1_SIDE_AWARE_POLICY_ADOPTION = PROJECT_ROOT / "experiments" / "h_g1_side_aware_bucket_policy_adoption.json"
H_G1_V3_SIDE_AWARE_DIAGNOSTIC = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_gamma_regime_diagnostic_summary_v3_side_aware.json"
H_G1_ACCEPTANCE_BLOCKER_REVIEW = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_acceptance_blocker_review.json"
H_G1_STRATEGY_ABLATION_PREREGISTRATION = PROJECT_ROOT / "experiments" / "h_g1_gamma_strategy_ablation_preregistration.json"
H_G1_STRATEGY_ABLATION_SUMMARY = PROJECT_ROOT / "reports" / "experiments" / "h_g1_gamma_strategy_ablation_summary.json"
H_G1_POST_ABLATION_DECISION = PROJECT_ROOT / "experiments" / "h_g1_post_ablation_decision.json"
H_G1_SAMPLE_EXPANSION_PLAN = PROJECT_ROOT / "experiments" / "h_g1_sample_expansion_plan.json"
H_G1_LOCAL_CACHE_OVERLAP_SCAN = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_local_cache_overlap_scan.json"
H_A2_2022_10_SPY_BARS_UNAVAILABLE = PROJECT_ROOT / "reports" / "data_cost" / "databento_spy_bars_plan_h_a2_2022_10_unavailable.json"
H_A2_2022_SPY_BAR_SOURCE_DECISION = PROJECT_ROOT / "experiments" / "h_a2_2022_spy_bar_source_decision.json"
H_A2_IBKR_SPY_BARS_READINESS_PROBE = PROJECT_ROOT / "reports" / "diagnostics" / "ibkr_spy_bars_readiness_probe_h_a2_2022_10.json"
H_A2_EXACT_DATA_PRIORITIZATION_DECISION = PROJECT_ROOT / "experiments" / "h_a2_exact_data_prioritization_decision.json"
H_A2_EXACT_2022_UNDERLYING_BAR_PLAN = PROJECT_ROOT / "experiments" / "h_a2_exact_2022_underlying_bar_plan.json"
H_A2_2022_SPY_BARS_IMPORT_SUMMARY = PROJECT_ROOT / "reports" / "data_cost" / "h_a2_2022_spy_bars_import_summary.json"
H_A2_PROXY_FIRST_ROBUSTNESS_SUMMARY = PROJECT_ROOT / "reports" / "experiments" / "h_a2_proxy_first_robustness_summary.json"
H_L1_MACRO_EVENT_PROXY_BASELINE_SUMMARY = PROJECT_ROOT / "reports" / "experiments" / "h_l1_macro_event_proxy_baseline_summary.json"
H_A2_H_L1_POST_PROXY_DECISION = PROJECT_ROOT / "experiments" / "h_a2_h_l1_post_proxy_decision.json"
H_A2_RESIDUAL_ADVERSE_DAY_PREREGISTRATION = PROJECT_ROOT / "experiments" / "h_a2_residual_adverse_day_analysis_preregistration.json"
H_A2_RESIDUAL_ADVERSE_DAY_ANALYSIS = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_residual_adverse_day_analysis.json"
H_A2_REVISED_OPENING_FOLLOWTHROUGH_PREREGISTRATION = (
    PROJECT_ROOT / "experiments" / "h_a2_revised_opening_followthrough_condition_preregistration.json"
)
H_A2_REVISED_OPENING_FOLLOWTHROUGH_SUMMARY = (
    PROJECT_ROOT / "reports" / "experiments" / "h_a2_revised_opening_followthrough_condition_summary.json"
)
H_A2_REVISED_CONDITION_ROBUSTNESS_PREREGISTRATION = (
    PROJECT_ROOT / "experiments" / "h_a2_revised_condition_robustness_preregistration.json"
)
H_A2_REVISED_CONDITION_ROBUSTNESS_SUMMARY = (
    PROJECT_ROOT / "reports" / "experiments" / "h_a2_revised_condition_robustness_summary.json"
)
H_A2_LOCKED_CONDITION_SIGNAL_ATTRIBUTION_PREREGISTRATION = (
    PROJECT_ROOT / "experiments" / "h_a2_locked_condition_signal_attribution_preregistration.json"
)
H_A2_LOCKED_CONDITION_SIGNAL_ATTRIBUTION_SUMMARY = (
    PROJECT_ROOT / "reports" / "experiments" / "h_a2_locked_condition_signal_attribution_summary.json"
)
H_A2_DELAYED_ENTRY_CONDITION_PREREGISTRATION = (
    PROJECT_ROOT / "experiments" / "h_a2_delayed_entry_condition_preregistration.json"
)
H_A2_DELAYED_ENTRY_CONDITION_SUMMARY = (
    PROJECT_ROOT / "reports" / "experiments" / "h_a2_delayed_entry_condition_summary.json"
)
H_A2_ORIGINAL_ENTRY_ROBUSTNESS_PRIORITIZATION_SUMMARY = (
    PROJECT_ROOT / "reports" / "experiments" / "h_a2_original_entry_robustness_prioritization_summary.json"
)
H_A2_INDEPENDENT_VALIDATION_FEASIBILITY_SUMMARY = (
    PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_independent_validation_feasibility.json"
)
H_A2_INDEPENDENT_VALIDATION_PAID_COST_PLAN_PREREGISTRATION = (
    PROJECT_ROOT / "experiments" / "h_a2_independent_validation_paid_cost_plan_preregistration.json"
)
H_A2_INDEPENDENT_VALIDATION_PAID_COST_ESTIMATE = (
    PROJECT_ROOT / "reports" / "data_cost" / "h_a2_independent_validation_paid_cost_estimate.json"
)
H_A2_INDEPENDENT_VALIDATION_PAID_DOWNLOAD_DECISION = (
    PROJECT_ROOT / "experiments" / "h_a2_independent_validation_paid_download_decision.json"
)
H_A2_INDEPENDENT_VALIDATION_DOWNLOAD_RESULT = (
    PROJECT_ROOT
    / "reports"
    / "data_cost"
    / "databento_download_result_h_a2_independent_validation_2025_04_08.json"
)
H_A2_INDEPENDENT_VALIDATION_IMPORT_DIAGNOSTIC_PREREGISTRATION = (
    PROJECT_ROOT / "experiments" / "h_a2_independent_validation_import_diagnostic_preregistration.json"
)
H_A2_INDEPENDENT_VALIDATION_IMPORT_DIAGNOSTIC_SUMMARY = (
    PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_independent_validation_import_diagnostic.json"
)
H_A2_NORMAL_CONTROL_SAMPLE_DECISION = (
    PROJECT_ROOT / "experiments" / "h_a2_normal_control_sample_decision.json"
)
H_A2_NORMAL_CONTROL_COST_ESTIMATE = (
    PROJECT_ROOT
    / "reports"
    / "data_cost"
    / "h_a2_normal_control_low_normal_vix_control_pack_cost_estimate.json"
)
H_A2_NORMAL_CONTROL_PAID_DOWNLOAD_DECISION = (
    PROJECT_ROOT / "experiments" / "h_a2_normal_control_paid_download_decision.json"
)
H_A2_NORMAL_CONTROL_DOWNLOAD_RESULT = (
    PROJECT_ROOT
    / "reports"
    / "data_cost"
    / "databento_download_result_h_a2_normal_control_low_normal_vix_control_pack.json"
)
H_A2_NORMAL_CONTROL_IMPORT_DIAGNOSTIC_PREREGISTRATION = (
    PROJECT_ROOT / "experiments" / "h_a2_normal_control_import_diagnostic_preregistration.json"
)
H_A2_NORMAL_CONTROL_IMPORT_DIAGNOSTIC_SUMMARY = (
    PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_normal_control_import_diagnostic.json"
)
H_A2_NORMAL_CONTROL_EXACT_REPLAY_PREREGISTRATION = (
    PROJECT_ROOT / "experiments" / "h_a2_normal_control_exact_replay_preregistration.json"
)
H_A2_NORMAL_CONTROL_EXACT_REPLAY_SUMMARY = (
    PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_normal_control_exact_replay.json"
)
H_A2_POST_EXACT_REPLAY_SAMPLE_EXPANSION_DECISION = (
    PROJECT_ROOT / "experiments" / "h_a2_post_exact_replay_sample_expansion_decision.json"
)
H_A2_POST_STRESS_NORMALIZATION_CONTROL_COST_ESTIMATE = (
    PROJECT_ROOT
    / "reports"
    / "data_cost"
    / "h_a2_post_stress_normalization_control_pack_cost_estimate.json"
)
H_A2_POST_STRESS_NORMALIZATION_CONTROL_PAID_DOWNLOAD_DECISION = (
    PROJECT_ROOT / "experiments" / "h_a2_post_stress_normalization_control_paid_download_decision.json"
)
H_A2_POST_STRESS_NORMALIZATION_CONTROL_DOWNLOAD_RESULT = (
    PROJECT_ROOT
    / "reports"
    / "data_cost"
    / "databento_download_result_h_a2_post_stress_normalization_control_pack.json"
)
H_A2_POST_STRESS_NORMALIZATION_CONTROL_IMPORT_DIAGNOSTIC_PREREGISTRATION = (
    PROJECT_ROOT
    / "experiments"
    / "h_a2_post_stress_normalization_control_import_diagnostic_preregistration.json"
)
H_A2_POST_STRESS_NORMALIZATION_CONTROL_IMPORT_DIAGNOSTIC_SUMMARY = (
    PROJECT_ROOT
    / "reports"
    / "diagnostics"
    / "h_a2_post_stress_normalization_control_import_diagnostic.json"
)
H_A2_POST_STRESS_NORMALIZATION_CONTROL_EXACT_REPLAY_PREREGISTRATION = (
    PROJECT_ROOT
    / "experiments"
    / "h_a2_post_stress_normalization_control_exact_replay_preregistration.json"
)
H_A2_POST_STRESS_NORMALIZATION_CONTROL_EXACT_REPLAY_SUMMARY = (
    PROJECT_ROOT
    / "reports"
    / "diagnostics"
    / "h_a2_post_stress_normalization_control_exact_replay.json"
)
H_A2_POST_TWO_EXACT_REPLAY_DECISION = (
    PROJECT_ROOT / "experiments" / "h_a2_post_two_exact_replay_decision.json"
)
H_A2_MECHANISM_REVISION_PREREGISTRATION = (
    PROJECT_ROOT / "experiments" / "h_a2_mechanism_revision_preregistration.json"
)
H_A2_MECHANISM_REVISION_AUDIT = (
    PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_mechanism_revision_audit.json"
)
H_A2_BREAKEVEN_AWARE_RULE_PREREGISTRATION = (
    PROJECT_ROOT / "experiments" / "h_a2_breakeven_aware_rule_preregistration.json"
)
H_A2_BREAKEVEN_AWARE_RULE_TRAIN_DIAGNOSTIC = (
    PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_breakeven_aware_rule_train_diagnostic.json"
)
H_A2_TARGETED_DATA_REGIME_EXPANSION_PLAN = (
    PROJECT_ROOT / "experiments" / "h_a2_targeted_data_regime_expansion_plan.json"
)
H_A2_TARGETED_GEOMETRY_CACHE_INVENTORY = (
    PROJECT_ROOT / "reports" / "data_cost" / "h_a2_targeted_geometry_cache_inventory_and_cost_plan.json"
)
GDELT_BULK_SOURCE_DECISION_NOTE = PROJECT_ROOT / "docs" / "GDELT_BULK_RAW_SOURCE_DECISION_NOTE.md"
GDELT_BULK_MANIFEST_REPORT = PROJECT_ROOT / "reports" / "news_gdelt_bulk_raw_manifest.json"
GDELT_GKG_ONE_FILE_PROBE_REPORT = PROJECT_ROOT / "reports" / "news_gdelt_gkg_one_file_parser_probe.json"
GDELT_DOC_API_ENRICHMENT_SCAFFOLD_REPORT = PROJECT_ROOT / "reports" / "news_gdelt_doc_api_enrichment_scaffold.json"
DATABENTO_API_KEY_ENVS = ("DATABENTO_API_KEY", "DATABENTO_SPY0DTE_API", "DATABENTO_API_MO", "DATABENTO_API_AI")

REPORT_PATHS = {
    "macro_calendar": PROJECT_ROOT / "reports" / "macro_calendar_coverage_audit.json",
    "vix_vxv": PROJECT_ROOT / "reports" / "vix_vxv_coverage_audit.json",
    "news": PROJECT_ROOT / "reports" / "news_coverage_audit.json",
    "gdelt_capture_status": PROJECT_ROOT / "reports" / "news_gdelt_capture_status",
    "gdelt_command_plan": PROJECT_ROOT / "reports" / "news_gdelt_capture_command_plan.json",
    "paid_cost": PROJECT_ROOT / "reports" / "data_cost" / "paid_cost_audit.json",
    "research_logs": PROJECT_ROOT / "reports" / "research_log_audit.json",
    "strategy_data": PROJECT_ROOT / "reports" / "strategy_data_readiness_audit.json",
    "exp07_prompt_redesign": PROJECT_ROOT / "docs" / "EXP07_PROMPT_REDESIGN.md",
    "exp07_real_news_case_plan": PROJECT_ROOT / "reports" / "experiments" / "exp07_real_news_case_plan.json",
    "exp07_acceptance": PROJECT_ROOT / "reports" / "experiments" / "exp07_acceptance_evaluation.json",
    "new_script_lib_usage": NEW_SCRIPT_LIB_USAGE_AUDIT,
    "exp07_strategy_ablation": PROJECT_ROOT / "reports" / "experiments" / "exp07_strategy_ablation_status.json",
    "aug_2023_databento_dry_run": PROJECT_ROOT
    / "reports"
    / "data_cost"
    / "databento_cost_insample_2023_08_intraday_exit_30m_dryrun.json",
    "opra_statistics_oi_probe": PROJECT_ROOT
    / "reports"
    / "data_cost"
    / "databento_opra_statistics_oi_probe_2024_01_03_schema.json",
    "opra_statistics_oi_download_probe": PROJECT_ROOT
    / "reports"
    / "data_cost"
    / "databento_opra_statistics_oi_download_probe_2024_01_03.json",
}


def audit_research_readiness(
    report_paths: dict[str, Path] | None = None,
    process_env: dict[str, str] | None = None,
    user_env_getter: Callable[[str], str | None] | None = None,
    machine_env_getter: Callable[[str], str | None] | None = None,
) -> dict[str, Any]:
    paths = report_paths or REPORT_PATHS
    env = process_env if process_env is not None else os.environ
    get_user_env = user_env_getter or _get_user_env
    get_machine_env = machine_env_getter or _get_machine_env

    environment = {
        name: _env_status(name, env, get_user_env, get_machine_env)
        for name in DATABENTO_API_KEY_ENVS
    }
    environment.update({
        "HIGANBANA_OPENROUTER_API": _env_status("HIGANBANA_OPENROUTER_API", env, get_user_env, get_machine_env),
    })
    reports = {name: _load_report_artifact(path) for name, path in paths.items()}
    checks = _build_checks(reports, environment, paths)
    blockers = sorted({_normalize_blocker(blocker) for check in checks for blocker in check["blockers"]})

    return {
        "status": "blocked" if blockers else "ready",
        "blockers": blockers,
        "environment": environment,
        "checks": checks,
        "next_safe_actions": _next_safe_actions(blockers),
    }


def write_reports(result: dict[str, Any], json_output: Path = DEFAULT_JSON_OUTPUT, report_output: Path = DEFAULT_REPORT_OUTPUT) -> None:
    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Research Readiness Audit",
        "",
        f"- Status: `{result['status']}`",
        f"- Blocker count: {len(result['blockers'])}",
        "",
        "## Environment",
        "",
        "| Variable | Process env | User env | Machine env |",
        "|:--|:--:|:--:|:--:|",
    ]
    for name, status in result["environment"].items():
        lines.append(f"| `{name}` | {status['process']} | {status['user']} | {status['machine']} |")

    lines.extend(["", "## Checks", "", "| Check | Status | Details | Blockers |", "|:--|:--|:--|:--|"])
    for check in result["checks"]:
        blockers = ", ".join(f"`{blocker}`" for blocker in check["blockers"]) or "-"
        details = _check_details(check)
        lines.append(f"| {check['name']} | `{check['status']}` | {details} | {blockers} |")

    lines.extend(["", "## Next Safe Actions", ""])
    for action in result["next_safe_actions"]:
        lines.append(f"- {action}")

    report_output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _check_details(check: dict[str, Any]) -> str:
    details = []
    if "known_committed_estimated_cost_usd" in check:
        details.append(f"known cost `${check['known_committed_estimated_cost_usd']}`")
    if "cost_guard_used_usd" in check:
        details.append(f"guard used `${check['cost_guard_used_usd']}`")
    if "cost_guard_basis" in check:
        details.append(f"basis `{check['cost_guard_basis']}`")
    if "remaining_before_stop_usd" in check:
        details.append(f"remaining `${check['remaining_before_stop_usd']}`")
    if "closed_trades" in check:
        details.append(f"closed trades `{check['closed_trades']}`")
    if "candidate_days" in check:
        details.append(f"candidate days `{check['candidate_days']}`")
    if "bypassing_lib_count" in check:
        details.append(f"new scripts bypassing lib `{check['bypassing_lib_count']}`")
    if "request_count" in check:
        details.append(f"requests `{check['request_count']}`")
    if "full_day_record_count" in check:
        details.append(f"full-day records `{check['full_day_record_count']}`")
    if "intraday_record_count" in check:
        details.append(f"intraday records `{check['intraday_record_count']}`")
    if "open_interest_record_count" in check:
        details.append(f"open interest records `{check['open_interest_record_count']}`")
    if "file_count" in check:
        details.append(f"files `{check['file_count']}`")
    if "retry_pressure_status" in check:
        details.append(f"retry pressure `{check['retry_pressure_status']}`")
    if "next_unattempted_trade_date" in check and check["next_unattempted_trade_date"]:
        details.append(f"next retry `{check['next_unattempted_trade_date']}`")
    status_counts = check.get("status_counts")
    if isinstance(status_counts, dict) and status_counts:
        rendered_counts = ", ".join(f"{name}={count}" for name, count in sorted(status_counts.items()))
        details.append(f"status counts `{rendered_counts}`")
    return "<br>".join(details) if details else "-"


def _build_checks(reports: dict[str, dict[str, Any] | None], environment: dict[str, dict[str, bool]], paths: dict[str, Path]) -> list[dict[str, Any]]:
    checks = [
        _report_check("macro_calendar", reports["macro_calendar"], paths["macro_calendar"], "requires_macro_calendar_audit_report"),
        _report_check("vix_vxv", reports["vix_vxv"], paths["vix_vxv"], "requires_vix_vxv_audit_report"),
        _report_check("news", reports["news"], paths["news"], "requires_news_coverage_audit_report"),
        _gdelt_capture_status_check(reports["gdelt_capture_status"], paths["gdelt_capture_status"]),
        _gdelt_command_plan_check(reports["gdelt_command_plan"], paths["gdelt_command_plan"]),
        _paid_cost_check(reports["paid_cost"], paths["paid_cost"]),
        _report_check("research_logs", reports["research_logs"], paths["research_logs"], "requires_research_log_audit_report"),
        _strategy_data_check(reports["strategy_data"], paths["strategy_data"]),
        _exp07_prompt_redesign_check(
            reports.get("exp07_prompt_redesign") or _load_report_artifact(REPORT_PATHS["exp07_prompt_redesign"]),
            paths.get("exp07_prompt_redesign", REPORT_PATHS["exp07_prompt_redesign"]),
            reports["news"],
        ),
        _exp07_real_news_case_plan_check(
            reports.get("exp07_real_news_case_plan"),
            paths.get("exp07_real_news_case_plan", REPORT_PATHS["exp07_real_news_case_plan"]),
        ),
        _exp07_acceptance_check(reports["exp07_acceptance"], paths["exp07_acceptance"]),
        _exp07_ablation_check(reports["exp07_strategy_ablation"], paths["exp07_strategy_ablation"]),
        _databento_aug_2023_check(reports["aug_2023_databento_dry_run"], paths["aug_2023_databento_dry_run"], environment),
        _opra_statistics_oi_probe_check(
            reports.get("opra_statistics_oi_probe"),
            paths.get("opra_statistics_oi_probe", REPORT_PATHS["opra_statistics_oi_probe"]),
            reports.get("opra_statistics_oi_download_probe"),
            paths.get("opra_statistics_oi_download_probe", REPORT_PATHS["opra_statistics_oi_download_probe"]),
        ),
        _openrouter_check(environment),
    ]
    if "new_script_lib_usage" in paths:
        checks.insert(
            8,
            _new_script_lib_usage_check(
                reports.get("new_script_lib_usage"),
                paths["new_script_lib_usage"],
            ),
        )
    return checks


def _report_check(name: str, report: dict[str, Any] | None, path: Path, missing_blocker: str) -> dict[str, Any]:
    if report is None:
        return {"name": name, "status": "blocked", "source": str(path), "blockers": [missing_blocker]}
    blockers = list(report.get("blockers", []))
    status = "pass" if report.get("status") == "pass" and not blockers else "blocked"
    return {"name": name, "status": status, "source": str(path), "blockers": blockers}


def _gdelt_capture_status_check(report: dict[str, Any] | None, path: Path) -> dict[str, Any]:
    if report is None:
        return {
            "name": "gdelt_capture_status",
            "status": "blocked",
            "source": str(path),
            "blockers": ["requires_gdelt_capture_status_report"],
        }
    blockers = list(report.get("blockers", []))
    status = "pass" if report.get("status") == "pass" and not blockers else "blocked"
    return {
        "name": "gdelt_capture_status",
        "status": status,
        "source": str(path),
        "status_counts": report.get("status_counts", {}),
        "file_count": report.get("file_count", 0),
        "blockers": blockers,
    }


def _gdelt_command_plan_check(report: dict[str, Any] | None, path: Path) -> dict[str, Any]:
    if report is None:
        return {
            "name": "gdelt_command_plan",
            "status": "blocked",
            "source": str(path),
            "blockers": ["requires_gdelt_command_plan_report"],
        }
    retry_pressure = report.get("retry_pressure", {})
    retry_queue_summary = report.get("retry_queue_summary", {})
    pressure_status = str(retry_pressure.get("status", "unknown"))
    blockers = []
    if pressure_status == "cooldown_recommended":
        blockers.append("gdelt_retry_cooldown_recommended")
    elif pressure_status not in {"normal_retry", "unknown"}:
        blockers.append(f"gdelt_retry_pressure:{pressure_status}")
    return {
        "name": "gdelt_command_plan",
        "status": "pass" if not blockers else "blocked",
        "source": str(path),
        "retry_pressure_status": pressure_status,
        "next_unattempted_trade_date": retry_queue_summary.get("next_unattempted_trade_date"),
        "not_attempted_count": retry_queue_summary.get("not_attempted_count"),
        "blockers": blockers,
    }


def _paid_cost_check(report: dict[str, Any] | None, path: Path) -> dict[str, Any]:
    if report is None:
        return {
            "name": "paid_cost",
            "status": "blocked",
            "source": str(path),
            "blockers": ["requires_paid_cost_audit_report"],
        }
    blockers = list(report.get("blockers", []))
    status = "pass" if report.get("status") == "pass" and not blockers else "blocked"
    return {
        "name": "paid_cost",
        "status": status,
        "source": str(path),
        "known_committed_estimated_cost_usd": report.get("known_committed_estimated_cost_usd"),
        "user_reported_actual_usage": report.get("user_reported_actual_usage"),
        "cost_guard_basis": report.get("cost_guard_basis"),
        "cost_guard_used_usd": report.get("cost_guard_used_usd"),
        "remaining_before_stop_usd": report.get("remaining_before_stop_usd"),
        "blockers": blockers,
    }


def _strategy_data_check(report: dict[str, Any] | None, path: Path) -> dict[str, Any]:
    if report is None:
        return {
            "name": "strategy_data",
            "status": "blocked",
            "source": str(path),
            "blockers": ["requires_strategy_data_readiness_audit_report"],
        }
    blockers = [_normalize_blocker(blocker) for blocker in report.get("blockers", [])]
    status = "pass" if report.get("status") == "pass" and not blockers else "blocked"
    return {
        "name": "strategy_data",
        "status": status,
        "source": str(path),
        "closed_trades": report.get("totals", {}).get("closed_trades"),
        "candidate_days": report.get("totals", {}).get("candidate_days"),
        "blockers": blockers,
    }


def _new_script_lib_usage_check(report: dict[str, Any] | None, path: Path) -> dict[str, Any]:
    if report is None:
        return {
            "name": "new_script_lib_usage",
            "status": "blocked",
            "source": str(path),
            "bypassing_lib_count": None,
            "blockers": ["requires_new_script_lib_usage_audit"],
        }
    bypassing = int(report.get("bypassing_lib_count", 0))
    blockers = list(report.get("blockers", []))
    if bypassing:
        blockers.append(f"new_script_lib_bypass_count:{bypassing}")
    return {
        "name": "new_script_lib_usage",
        "status": "pass" if report.get("status") == "pass" and not blockers else "blocked",
        "source": str(path),
        "bypassing_lib_count": bypassing,
        "blockers": sorted(set(blockers)),
    }


def _opra_statistics_oi_probe_check(
    report: dict[str, Any] | None,
    path: Path,
    download_report: dict[str, Any] | None,
    download_path: Path,
) -> dict[str, Any]:
    if report is None:
        return {
            "name": "opra_statistics_oi_probe",
            "status": "blocked",
            "source": str(path),
            "blockers": ["requires_opra_statistics_oi_probe_report"],
        }

    checks = {
        item.get("label"): item.get("record_count")
        for item in report.get("record_count_checks", [])
        if isinstance(item, dict)
    }
    blockers: list[str] = []
    full_day_records = int(checks.get("full_utc_day") or 0)
    intraday_records = int(checks.get("intraday_research_window") or 0)
    if report.get("status") not in {"pass", "pass_with_timing_caveat"}:
        blockers.append("requires_opra_statistics_oi_probe_pass")
    if not report.get("has_stat_type_field"):
        blockers.append("requires_opra_statistics_stat_type_field")
    if full_day_records <= 0:
        blockers.append("requires_opra_statistics_full_day_records")
    if report.get("status") == "pass_with_timing_caveat" and full_day_records > 0 and intraday_records == 0:
        if download_report is None:
            blockers.append("requires_controlled_opra_statistics_download_import_probe")

    open_interest_record_count = None
    if download_report is not None:
        inspection = download_report.get("inspection", {})
        open_interest_record_count = inspection.get("open_interest_record_count") if isinstance(inspection, dict) else None
        if download_report.get("status") != "pass":
            blockers.append("requires_opra_statistics_download_probe_pass")
        if not isinstance(open_interest_record_count, int) or open_interest_record_count <= 0:
            blockers.append("requires_opra_statistics_open_interest_records")

    return {
        "name": "opra_statistics_oi_probe",
        "status": "pass" if not blockers else "blocked",
        "source": f"{path}; {download_path}",
        "full_day_record_count": full_day_records,
        "intraday_record_count": intraday_records,
        "open_interest_record_count": open_interest_record_count,
        "blockers": blockers,
    }


def _exp07_prompt_redesign_check(report: dict[str, Any] | None, path: Path, news_report: dict[str, Any] | None) -> dict[str, Any]:
    blockers = []
    if report is None:
        blockers.append("requires_exp07_prompt_redesign_doc")
    elif "real timestamp-clean news" not in str(report.get("text", "")).lower():
        blockers.append("requires_exp07_real_news_prompt_design")

    news_blockers = [] if news_report is None else list(news_report.get("blockers", []))
    if news_report is None or "requires_real_news_archive" in news_blockers:
        blockers.append("requires_real_timestamp_clean_news_cases_for_exp07_prompt_research")

    return {
        "name": "exp07_prompt_redesign",
        "status": "ready_for_real_news_prompt_design" if not blockers else "blocked",
        "source": str(path),
        "blockers": blockers,
        "note": "Synthetic/policy prompt matrices are infrastructure-only and must not be counted as Exp07 research evidence.",
    }


def _exp07_real_news_case_plan_check(report: dict[str, Any] | None, path: Path) -> dict[str, Any]:
    if report is None:
        return {
            "name": "exp07_real_news_case_plan",
            "status": "blocked",
            "source": str(path),
            "blockers": ["requires_exp07_real_news_case_plan"],
        }
    blockers = list(report.get("blockers", []))
    return {
        "name": "exp07_real_news_case_plan",
        "status": "ready_for_prompt_family_pre_experiment" if report.get("status") == "ready_for_prompt_family_pre_experiment" and not blockers else "blocked",
        "source": str(path),
        "candidate_days": report.get("candidate_day_count"),
        "captured_candidate_days": report.get("captured_candidate_count"),
        "blockers": blockers,
    }


def _exp07_acceptance_check(report: dict[str, Any] | None, path: Path) -> dict[str, Any]:
    if report is None:
        return {
            "name": "exp07_acceptance",
            "status": "blocked",
            "source": str(path),
            "blockers": ["requires_exp07_acceptance_report"],
        }
    blockers = list(report.get("strategy_integration_blockers", []))
    status = "pass" if report.get("strategy_integration_status") == "pass" and not blockers else "blocked"
    return {"name": "exp07_acceptance", "status": status, "source": str(path), "blockers": blockers}


def _exp07_ablation_check(report: dict[str, Any] | None, path: Path) -> dict[str, Any]:
    if report is None:
        return {
            "name": "exp07_strategy_ablation",
            "status": "blocked",
            "source": str(path),
            "blockers": ["requires_exp07_strategy_ablation_status_report"],
        }
    blockers = [_normalize_blocker(blocker) for blocker in report.get("blockers", [])]
    status = "ready" if report.get("status") == "ready" and not blockers else "blocked"
    return {"name": "exp07_strategy_ablation", "status": status, "source": str(path), "blockers": blockers}


def _databento_aug_2023_check(
    report: dict[str, Any] | None,
    path: Path,
    environment: dict[str, dict[str, bool]],
) -> dict[str, Any]:
    blockers = []
    if report is None:
        blockers.append("requires_aug_2023_databento_dry_run_plan")
    if not _has_any_databento_env(environment):
        blockers.append("requires_databento_api_key_for_aug_2023_live_cost")
    return {
        "name": "aug_2023_databento",
        "status": "blocked" if blockers else "ready_for_live_cost_estimate",
        "source": str(path),
        "request_count": _databento_request_count(report),
        "blockers": blockers,
    }


def _openrouter_check(environment: dict[str, dict[str, bool]]) -> dict[str, Any]:
    status = environment["HIGANBANA_OPENROUTER_API"]
    blockers = []
    if not _has_any_env_scope(status):
        blockers.append("requires_openrouter_api_key_for_live_llm_experiments")
    return {
        "name": "openrouter_llm",
        "status": "available" if not blockers else "blocked",
        "blockers": blockers,
        "note": "Only use for guarded smoke tests or approved prompt experiments.",
    }


def _databento_request_count(report: dict[str, Any] | None) -> int | None:
    if report is None:
        return None
    if isinstance(report.get("request_count"), int):
        return report["request_count"]
    if isinstance(report.get("total_request_count"), int):
        return report["total_request_count"]
    requests = report.get("requests")
    if isinstance(requests, list):
        return len(requests)
    return None


def _next_safe_actions(blockers: list[str]) -> list[str]:
    actions = []
    post_proxy_decision = _load_report_artifact(H_A2_H_L1_POST_PROXY_DECISION)
    residual_preregistration = _load_report_artifact(H_A2_RESIDUAL_ADVERSE_DAY_PREREGISTRATION)
    residual_analysis = _load_report_artifact(H_A2_RESIDUAL_ADVERSE_DAY_ANALYSIS)
    revised_opening_followthrough_preregistration = _load_report_artifact(
        H_A2_REVISED_OPENING_FOLLOWTHROUGH_PREREGISTRATION
    )
    revised_opening_followthrough_summary = _load_report_artifact(H_A2_REVISED_OPENING_FOLLOWTHROUGH_SUMMARY)
    revised_condition_robustness_preregistration = _load_report_artifact(
        H_A2_REVISED_CONDITION_ROBUSTNESS_PREREGISTRATION
    )
    revised_condition_robustness_summary = _load_report_artifact(H_A2_REVISED_CONDITION_ROBUSTNESS_SUMMARY)
    locked_condition_signal_attribution_preregistration = _load_report_artifact(
        H_A2_LOCKED_CONDITION_SIGNAL_ATTRIBUTION_PREREGISTRATION
    )
    locked_condition_signal_attribution_summary = _load_report_artifact(
        H_A2_LOCKED_CONDITION_SIGNAL_ATTRIBUTION_SUMMARY
    )
    delayed_entry_condition_preregistration = _load_report_artifact(H_A2_DELAYED_ENTRY_CONDITION_PREREGISTRATION)
    delayed_entry_condition_summary = _load_report_artifact(H_A2_DELAYED_ENTRY_CONDITION_SUMMARY)
    original_entry_robustness_prioritization_summary = _load_report_artifact(
        H_A2_ORIGINAL_ENTRY_ROBUSTNESS_PRIORITIZATION_SUMMARY
    )
    independent_validation_feasibility_summary = _load_report_artifact(
        H_A2_INDEPENDENT_VALIDATION_FEASIBILITY_SUMMARY
    )
    independent_validation_paid_cost_plan_preregistration = _load_report_artifact(
        H_A2_INDEPENDENT_VALIDATION_PAID_COST_PLAN_PREREGISTRATION
    )
    independent_validation_paid_cost_estimate = _load_report_artifact(
        H_A2_INDEPENDENT_VALIDATION_PAID_COST_ESTIMATE
    )
    independent_validation_paid_download_decision = _load_report_artifact(
        H_A2_INDEPENDENT_VALIDATION_PAID_DOWNLOAD_DECISION
    )
    independent_validation_download_result = _load_report_artifact(H_A2_INDEPENDENT_VALIDATION_DOWNLOAD_RESULT)
    independent_validation_import_diagnostic_preregistration = _load_report_artifact(
        H_A2_INDEPENDENT_VALIDATION_IMPORT_DIAGNOSTIC_PREREGISTRATION
    )
    independent_validation_import_diagnostic_summary = _load_report_artifact(
        H_A2_INDEPENDENT_VALIDATION_IMPORT_DIAGNOSTIC_SUMMARY
    )
    normal_control_sample_decision = _load_report_artifact(H_A2_NORMAL_CONTROL_SAMPLE_DECISION)
    normal_control_cost_estimate = _load_report_artifact(H_A2_NORMAL_CONTROL_COST_ESTIMATE)
    normal_control_paid_download_decision = _load_report_artifact(H_A2_NORMAL_CONTROL_PAID_DOWNLOAD_DECISION)
    normal_control_download_result = _load_report_artifact(H_A2_NORMAL_CONTROL_DOWNLOAD_RESULT)
    normal_control_import_diagnostic_preregistration = _load_report_artifact(
        H_A2_NORMAL_CONTROL_IMPORT_DIAGNOSTIC_PREREGISTRATION
    )
    normal_control_import_diagnostic_summary = _load_report_artifact(H_A2_NORMAL_CONTROL_IMPORT_DIAGNOSTIC_SUMMARY)
    normal_control_exact_replay_preregistration = _load_report_artifact(
        H_A2_NORMAL_CONTROL_EXACT_REPLAY_PREREGISTRATION
    )
    normal_control_exact_replay_summary = _load_report_artifact(H_A2_NORMAL_CONTROL_EXACT_REPLAY_SUMMARY)
    post_exact_replay_sample_expansion_decision = _load_report_artifact(
        H_A2_POST_EXACT_REPLAY_SAMPLE_EXPANSION_DECISION
    )
    post_stress_normalization_control_cost_estimate = _load_report_artifact(
        H_A2_POST_STRESS_NORMALIZATION_CONTROL_COST_ESTIMATE
    )
    post_stress_normalization_control_paid_download_decision = _load_report_artifact(
        H_A2_POST_STRESS_NORMALIZATION_CONTROL_PAID_DOWNLOAD_DECISION
    )
    post_stress_normalization_control_download_result = _load_report_artifact(
        H_A2_POST_STRESS_NORMALIZATION_CONTROL_DOWNLOAD_RESULT
    )
    post_stress_normalization_control_import_diagnostic_preregistration = _load_report_artifact(
        H_A2_POST_STRESS_NORMALIZATION_CONTROL_IMPORT_DIAGNOSTIC_PREREGISTRATION
    )
    post_stress_normalization_control_import_diagnostic_summary = _load_report_artifact(
        H_A2_POST_STRESS_NORMALIZATION_CONTROL_IMPORT_DIAGNOSTIC_SUMMARY
    )
    post_stress_normalization_control_exact_replay_preregistration = _load_report_artifact(
        H_A2_POST_STRESS_NORMALIZATION_CONTROL_EXACT_REPLAY_PREREGISTRATION
    )
    post_stress_normalization_control_exact_replay_summary = _load_report_artifact(
        H_A2_POST_STRESS_NORMALIZATION_CONTROL_EXACT_REPLAY_SUMMARY
    )
    post_two_exact_replay_decision = _load_report_artifact(H_A2_POST_TWO_EXACT_REPLAY_DECISION)
    h_a2_mechanism_revision_preregistration = _load_report_artifact(H_A2_MECHANISM_REVISION_PREREGISTRATION)
    h_a2_mechanism_revision_audit = _load_report_artifact(H_A2_MECHANISM_REVISION_AUDIT)
    h_a2_breakeven_aware_rule_preregistration = _load_report_artifact(
        H_A2_BREAKEVEN_AWARE_RULE_PREREGISTRATION
    )
    h_a2_breakeven_aware_rule_train_diagnostic = _load_report_artifact(
        H_A2_BREAKEVEN_AWARE_RULE_TRAIN_DIAGNOSTIC
    )
    h_a2_targeted_data_regime_expansion_plan = _load_report_artifact(
        H_A2_TARGETED_DATA_REGIME_EXPANSION_PLAN
    )
    h_a2_targeted_geometry_cache_inventory = _load_report_artifact(
        H_A2_TARGETED_GEOMETRY_CACHE_INVENTORY
    )
    h_a2_proxy_robustness = _load_report_artifact(H_A2_PROXY_FIRST_ROBUSTNESS_SUMMARY)
    h_l1_macro_proxy = _load_report_artifact(H_L1_MACRO_EVENT_PROXY_BASELINE_SUMMARY)
    if (
        h_a2_targeted_geometry_cache_inventory
        and h_a2_targeted_geometry_cache_inventory.get("status")
        == "complete_no_download_cost_estimate_deferred"
        and h_a2_targeted_geometry_cache_inventory.get("experiment_id")
        == "h_a2_targeted_geometry_cache_inventory_and_cost_estimate"
    ):
        target_sets = {
            item.get("target_set_id"): item
            for item in h_a2_targeted_geometry_cache_inventory.get("target_sets", [])
        }
        train = target_sets.get("train_candidate_geometry_backfill", {})
        normal = target_sets.get("normal_control_geometry_pack", {})
        stress = target_sets.get("stress_regime_geometry_pack", {})
        actions.append(f"H-A2.64 cache inventory is complete as E0 control evidence with no network, no live metadata call, and no paid download. Train geometry cache is ready for {train.get('ready_for_local_geometry_parser_count')}/{train.get('target_date_count')} target dates, normal/control has {normal.get('candidate_ready_count')} candidate-ready dates from existing downloaded packs, and stress geometry remains blocked by {stress.get('missing_underlying_bar_count')} missing real 2022 SPY underlying-bar dates despite local option quotes. Next safe H-A2 work is a local/no-paid train/control geometry parser preregistration or implementation using existing cached SPY bars and OPRA quotes. Do not call Databento metadata while Technical DD Workstream 1 remains open, do not download data, do not run OOS rule evaluation, do not select thresholds for trading, do not request broker/order work, do not approve paper trading, operational validation, real-money trading, or claim E2 from H-A2.64.")
    elif (
        h_a2_targeted_data_regime_expansion_plan
        and h_a2_targeted_data_regime_expansion_plan.get("status") == "preregistered"
        and h_a2_targeted_data_regime_expansion_plan.get("experiment_id")
        == "h_a2_targeted_data_regime_expansion_plan"
    ):
        next_artifact = h_a2_targeted_data_regime_expansion_plan.get("planned_next_artifact") or {}
        target_sets = [
            item.get("target_set_id")
            for item in h_a2_targeted_data_regime_expansion_plan.get("planned_target_sets", [])
        ]
        actions.append(f"H-A2.63 targeted data/regime expansion plan is pre-registered as E0 control evidence after H-A2.62. It converts the blocker from vague sample-size shortage into specific target sets {target_sets}: train candidate geometry backfill first, normal/control geometry pack, stress-regime geometry pack, and future OOS locked-rule evaluation pack. Next safe H-A2 work is {next_artifact.get('step_id')}: {next_artifact.get('name')} as cache inventory plus metadata/cost estimate only. Required missing fields include entry strike mapping, entry implementable debit, bid/ask width, quote size/liquidity, forced-close value, regime labels, and MinTRL/PSR coverage. Do not download data yet, do not broad-buy calendar data, do not run OOS rule evaluation, do not select thresholds, do not call LLMs/GDELT, do not request broker/order work, do not approve paper trading, operational validation, real-money trading, or claim E2 from H-A2.63.")
    elif (
        h_a2_breakeven_aware_rule_train_diagnostic
        and h_a2_breakeven_aware_rule_train_diagnostic.get("status") == "complete"
        and h_a2_breakeven_aware_rule_train_diagnostic.get("experiment_id")
        == "h_a2_breakeven_aware_rule_train_diagnostic"
    ):
        decision = h_a2_breakeven_aware_rule_train_diagnostic.get("decision") or {}
        feature_audit = h_a2_breakeven_aware_rule_train_diagnostic.get("decision_time_feature_audit") or {}
        actions.append(f"H-A2.62 breakeven-aware train-only diagnostic is complete as E1 evidence. It defines the cost-adjusted strike-reachability target and confirms current local train artifacts can run surrogate train-only trials but cannot lock a true breakeven-aware option rule because train rows lack entry strike mapping, implementable debit, bid/ask width, liquidity, and train-distribution strike-reachability targets. Decision is `{decision.get('decision')}`. Next safe H-A2 work is H-A2.63: pre-register a targeted data/regime expansion plan naming the minimum option-chain fields and windows needed for entry strike mapping, entry implementable debit, bid/ask width, liquidity, forced-close value, regime labels, and MinTRL/PSR coverage before any paid download or OOS rule evaluation. Do not treat surrogate train trials as a tradable rule, do not use OOS tuning, do not select an OOS filter, do not broad-buy calendar data, do not request IBKR/order work, do not call LLMs, do not retry GDELT, do not approve paper trading, operational validation, real-money trading, or claim E2 from H-A2.62. Current true-rule lock status: {feature_audit.get('can_lock_true_breakeven_aware_rule_from_current_artifacts')}.")
    elif (
        h_a2_breakeven_aware_rule_preregistration
        and h_a2_breakeven_aware_rule_preregistration.get("status") == "preregistered"
        and h_a2_breakeven_aware_rule_preregistration.get("experiment_id")
        == "h_a2_breakeven_aware_rule_preregistration"
    ):
        diagnostic = h_a2_breakeven_aware_rule_preregistration.get("planned_next_diagnostic") or {}
        actions.append(f"H-A2.61 breakeven-aware revised-rule preregistration is complete as E0 control evidence. It separates payoff-feasibility targets from decision-time inputs: future post-entry movement, forced-close quotes, same-day realized PnL, and OOS-selected filters are forbidden as live inputs. Next safe H-A2 work is H-A2.62: run `{diagnostic.get('experiment_id')}` as a local/no-paid/train-only E1 diagnostic using existing artifacts only. It must define the cost-adjusted strike-reachability target, record all train-only candidate rule trials in a search log, preserve DSR/MinTRL/PSR/big-day controls, and decide whether to park H-A2, preregister OOS evaluation of one locked rule, or write a targeted data/regime expansion plan. Do not use OOS tuning, download data, broaden exact replay, change threshold 0.001 as a tradable rule, select an OOS filter, request IBKR bars, call LLMs, retry GDELT, approve paper trading, operational validation, real-money trading, or claim E2 from H-A2.61.")
    elif (
        h_a2_mechanism_revision_audit
        and h_a2_mechanism_revision_audit.get("status") == "complete"
        and h_a2_mechanism_revision_audit.get("experiment_id") == "h_a2_mechanism_revision_audit"
    ):
        agg = h_a2_mechanism_revision_audit.get("aggregate_findings") or {}
        decision = h_a2_mechanism_revision_audit.get("decision") or {}
        actions.append(f"H-A2.60 mechanism-revision audit is complete as E1 diagnostic evidence. The two exact-replayed candidates were both directionally correct at the underlying level, but both option spreads still lost after implementable costs; total mid_pnl {agg.get('total_mid_pnl')}, total implementable_pnl {agg.get('total_implementable_pnl')}, total cost drag {agg.get('total_cost_drag_vs_mid')}, and the long strike was not reached in {agg.get('long_strike_not_reached_count')} of {agg.get('candidate_count')} candidates. Decision is `{decision.get('selected_next_step')}`. Next safe H-A2 work is H-A2.61: pre-register a train-only revised rule focused on cost-adjusted post-entry magnitude, strike reachability, and implementable friction before any more paid data, exact replay expansion, threshold/filter change, E2 claim, paper trading, operational validation, or real-money work.")
    elif (
        h_a2_mechanism_revision_preregistration
        and h_a2_mechanism_revision_preregistration.get("status") == "preregistered"
        and h_a2_mechanism_revision_preregistration.get("experiment_id")
        == "h_a2_mechanism_revision_preregistration"
    ):
        diagnostic = h_a2_mechanism_revision_preregistration.get("planned_next_diagnostic") or {}
        actions.append(f"H-A2.59 mechanism-revision preregistration is complete as E0 control evidence. H-A2 is reframed as a conditional continuation hypothesis: direction alone is not enough; post-entry magnitude, implementable cost drag, and regime context must explain when ORB debit spreads can beat friction. Next safe H-A2 work is to run `{diagnostic.get('experiment_id')}` as a local/no-paid E1 diagnostic using existing artifacts only. It must produce a mechanism autopsy for the two exact-replayed losing candidates, compare direction signal versus post-entry magnitude and cost drag, and choose whether to park the current locked condition, preregister a train-only revised rule, or write a targeted sample/regime expansion plan. Do not download data, run exact replay expansion, change threshold 0.001, select an OOS filter, request IBKR bars, call LLMs, retry GDELT, approve paper trading, operational validation, real-money trading, or claim E2 from H-A2.59.")
    elif (
        post_two_exact_replay_decision
        and post_two_exact_replay_decision.get("status") == "decision_complete"
        and post_two_exact_replay_decision.get("experiment_id") == "h_a2_post_two_exact_replay_decision"
    ):
        summary = post_two_exact_replay_decision.get("source_result_summary") or {}
        decision = post_two_exact_replay_decision.get("decision") or {}
        actions.append(f"H-A2.58 decision after two exact replays is complete as E0 decision evidence. The two exact-replayed candidates total mid_pnl {summary.get('total_mid_pnl')} and implementable_pnl {summary.get('total_implementable_pnl')}; both candidates are negative after implementable costs and remain under-sampled/underpowered. Selected next step is `{decision.get('selected_next_step')}`. Next safe H-A2 work is to pre-register `h_a2_mechanism_revision_preregistration`, defining the revised market mechanism, train-only rule-revision boundaries, anti-overfitting controls, sample/regime expansion criteria, and falsification criteria before any more paid data, exact replay expansion, threshold search, OOS-selected filter, IBKR request, LLM call, GDELT retry, paper trading, operational validation, real-money trading, or E2 claim.")
    elif (
        post_stress_normalization_control_exact_replay_summary
        and post_stress_normalization_control_exact_replay_summary.get("status") == "complete"
        and post_stress_normalization_control_exact_replay_summary.get("experiment_id")
        == "h_a2_post_stress_normalization_control_exact_replay"
    ):
        pnl = post_stress_normalization_control_exact_replay_summary.get("pnl") or {}
        actions.append(f"H-A2.57 post-stress normalization/control exact replay is complete as E1 single-candidate diagnostic evidence only. Candidate `2025-05-05` call produced mid_pnl {pnl.get('mid_pnl')} and implementable_pnl {pnl.get('implementable_pnl')} after cost treatment, with sample_count=1, under-sampled, and underpowered. Next safe H-A2 work is a separate pre-registered decision artifact that combines the two exact-replayed candidates (`2025-02-11` and `2025-05-05`) and chooses whether to revise the H-A2 hypothesis or run a targeted sample/regime expansion. Do not download more data, broaden replay, change threshold 0.001, add an OOS-selected filter, request IBKR bars, call LLMs, retry GDELT, approve paper trading, operational validation, real-money trading, or claim E2 from these two trades.")
    elif (
        post_stress_normalization_control_exact_replay_preregistration
        and post_stress_normalization_control_exact_replay_preregistration.get("status")
        == "preregistered"
        and post_stress_normalization_control_exact_replay_preregistration.get("experiment_id")
        == "h_a2_post_stress_normalization_control_exact_replay"
    ):
        scope = post_stress_normalization_control_exact_replay_preregistration.get("candidate_scope") or {}
        ready_dates = scope.get("candidate_dates") or []
        actions.append(f"H-A2.56 post-stress normalization/control exact replay is pre-registered as E0 control evidence only. Scope is {', '.join(ready_dates) or 'none'}, direction call, source data is already-downloaded `post_stress_normalization_control_pack`, locked 09:35 threshold 0.001, 15:45 forced close, nearest discrete strike rounding, separate mid_pnl and implementable_pnl, and $0.64 per-leg fees. Next safe H-A2 work is to run the bounded H-A2.57 exact replay for those candidate-ready date(s) only using already-downloaded local data, then validate the output and write/push the next Thai research log if the replay completes. Do not download more data, broaden dates, resume high-VIX-first acquisition, change threshold 0.001, add an OOS-selected filter, request IBKR bars, call LLMs, retry GDELT, approve paper trading, operational validation, real-money trading, or claim E2.")
    elif (
        post_stress_normalization_control_import_diagnostic_summary
        and post_stress_normalization_control_import_diagnostic_summary.get("status") == "complete"
        and post_stress_normalization_control_import_diagnostic_summary.get("experiment_id")
        == "h_a2_post_stress_normalization_control_import_diagnostic"
    ):
        aggregate = post_stress_normalization_control_import_diagnostic_summary.get("aggregate_diagnostic") or {}
        ready_dates = aggregate.get("candidate_trade_data_ready_dates") or []
        actions.append(f"H-A2.55 post-stress normalization/control import diagnostic is complete as E1 diagnostic evidence only. It parsed the already-downloaded `post_stress_normalization_control_pack`, found {aggregate.get('candidate_trade_data_ready_count')} candidate-ready date(s) ({', '.join(ready_dates) or 'none'}), preserved the locked 09:35 threshold 0.001 signal, and reports no exact replay/PnL or E2 claim. Next safe H-A2 work is to pre-register a separate bounded exact-replay diagnostic for those candidate-ready date(s) only before computing candidate-trade PnL. Do not download more data, broaden dates, resume high-VIX-first acquisition, change threshold 0.001, add an OOS-selected filter, request IBKR bars, call LLMs, retry GDELT, approve paper trading, operational validation, real-money trading, or claim E2.")
    elif (
        post_stress_normalization_control_import_diagnostic_preregistration
        and post_stress_normalization_control_import_diagnostic_preregistration.get("status")
        == "preregistered"
        and post_stress_normalization_control_import_diagnostic_preregistration.get("experiment_id")
        == "h_a2_post_stress_normalization_control_import_diagnostic"
    ):
        actions.append("H-A2.54 post-stress normalization/control import diagnostic is pre-registered as E0 control evidence. Next safe H-A2 work is to run the local import/normalization/diagnostic using only the already-downloaded `post_stress_normalization_control_pack` DBN files and local VIX/macro labels, then report raw-file inventory, SPY bar import, OPRA quote import, timestamp alignment, locked 09:35 threshold 0.001 signal reconstruction, candidate availability, and the 2025-05-06 reduced-quality data note. Do not download more data, broaden dates, resume high-VIX-first acquisition, change threshold 0.001, add an OOS-selected filter, request IBKR bars, call LLMs, retry GDELT, run exact replay/PnL, approve paper trading, operational validation, real-money trading, or claim E2.")
    elif (
        post_stress_normalization_control_download_result
        and post_stress_normalization_control_download_result.get("status") == "pass"
        and post_stress_normalization_control_download_result.get("scenario")
        == "h_a2_post_stress_normalization_control_pack"
    ):
        execution = post_stress_normalization_control_download_result.get("execution") or {}
        actions.append(f"H-A2.53 post-stress normalization/control download is complete as E0 data acquisition only: `post_stress_normalization_control_pack` downloaded/cache-confirmed {post_stress_normalization_control_download_result.get('request_count')} grouped files for 10 dates from 2025-05-05 to 2025-05-16 using selected key env `DATABENTO_API_AI`, estimated cost ${post_stress_normalization_control_download_result.get('total_estimated_cost_usd')}, total bytes {execution.get('total_bytes')}, and the locked 09:35 threshold 0.001 signal remains unchanged. Next safe H-A2 work is to pre-register the import/normalization/diagnostic step for this downloaded pack before parsing or replaying it. Do not run exact replay/PnL directly from the download result, broaden dates, resume high-VIX-first acquisition, change threshold 0.001, add an OOS-selected filter, request IBKR bars, call LLMs, retry GDELT, approve paper trading, operational validation, real-money trading, or claim E2.")
    elif (
        post_stress_normalization_control_paid_download_decision
        and post_stress_normalization_control_paid_download_decision.get("status") == "decision_complete"
        and post_stress_normalization_control_paid_download_decision.get("decision")
        == "approve_post_stress_normalization_control_pack_download_after_paid_cost_audit_pass"
    ):
        actions.append("H-A2.52 post-stress normalization/control paid download decision is complete as E0 control evidence for `post_stress_normalization_control_pack` only. It preserves the locked 09:35 threshold 0.001 signal, selected key env `DATABENTO_API_AI`, 10 dates from 2025-05-05 to 2025-05-16, 150 planned required windows, 20 grouped conservative metadata calls, and estimated cost $5.558642. Next safe H-A2 work is to rerun `python scripts\\audit_paid_costs.py`; if it still passes, execute only the approved post-stress normalization/control pack download and then write a separate download result artifact. Do not download from the metadata estimate alone, expand dates, download `low_normal_vix_control_pack`, resume high-VIX-first acquisition, change threshold 0.001, add an OOS-selected filter, request IBKR bars, call LLMs, retry GDELT, approve paper trading, run exact replay/PnL, or claim E2.")
    elif (
        post_stress_normalization_control_cost_estimate
        and (post_stress_normalization_control_cost_estimate.get("decision") or {}).get("status")
        == "metadata_estimate_pass_next_download_decision_required"
        and post_stress_normalization_control_cost_estimate.get("batch_id")
        == "post_stress_normalization_control_pack"
    ):
        actions.append("H-A2.51 post-stress normalization/control metadata estimate is complete as E0 cost-control evidence: `post_stress_normalization_control_pack` covers 2025-05-05 to 2025-05-16, 10 local-VIX trading days, VIX 17.24-24.76, and no high-importance macro days. The live grouped Databento metadata estimate used selected key env `DATABENTO_API_AI`, planned 150 required windows, grouped them into 20 conservative metadata calls, estimated $5.558642, projected selected-key usage $5.558642 against the $100 per-key cap and $200 MO/AI pool cap, and performed no download. Next safe H-A2 work is to create a separate download decision artifact for this post-stress normalization/control pack, then rerun paid-cost audit before any data pull. This is no exact replay/PnL/E2 claim evidence. Do not download from the estimate report alone, resume high-VIX-first acquisition, change threshold 0.001, add an OOS-selected filter, request IBKR bars, call LLMs, retry GDELT, approve paper trading, run exact replay/PnL, or claim E2.")
    elif (
        post_exact_replay_sample_expansion_decision
        and post_exact_replay_sample_expansion_decision.get("status") == "preregistered"
        and post_exact_replay_sample_expansion_decision.get("experiment_id")
        == "h_a2_post_exact_replay_sample_expansion_decision"
    ):
        actions.append("H-A2.50 post-exact-replay sample-expansion decision is pre-registered as E0 control evidence after H-A2.49. H-A2.49 remains E1 single-candidate evidence only: 2025-02-11, direction call, mid_pnl -$22.00, implementable_pnl -$26.56, sample count 1, MinTRL/PSR blocked, no E2 or paper-trading readiness. Next safe H-A2 work is a metadata-only Databento cost estimate for `post_stress_normalization_control_pack` using selected key env `DATABENTO_API_AI`, after `python scripts\\validate_h_a2_post_exact_replay_sample_expansion_decision.py` and `python scripts\\audit_paid_costs.py` pass. Use `python scripts\\estimate_h_a2_independent_validation_cost.py --prereg-path experiments\\h_a2_post_exact_replay_sample_expansion_decision.json --batch-id post_stress_normalization_control_pack --api-key-env DATABENTO_API_AI --live --group-live-requests --json-report reports\\data_cost\\h_a2_post_stress_normalization_control_pack_cost_estimate.json --md-report reports\\data_cost\\h_a2_post_stress_normalization_control_pack_cost_estimate.md`. Do not download data, broaden replay, change threshold 0.001, add an OOS-selected filter, request IBKR bars, call LLMs, retry GDELT, approve paper trading, or claim E2 from H-A2.50.")
    elif (
        normal_control_exact_replay_summary
        and normal_control_exact_replay_summary.get("status") == "complete"
        and normal_control_exact_replay_summary.get("experiment_id") == "h_a2_normal_control_exact_replay"
    ):
        actions.append("H-A2.49 bounded normal/control exact replay is complete as E1 single-candidate diagnostic evidence only. The only replayed candidate was 2025-02-11, direction call, using the locked 09:35 threshold 0.001 signal, 15:45 forced close, nearest discrete strike rounding, and $0.64 per-leg fees. The trade lost money: mid_pnl -$22.00 and implementable_pnl -$26.56, with cost drag $4.56 versus mid. Sample count is 1, so MinTRL/PSR remains blocked, H-A2 is not validated, and paper trading/operational validation/real-money/E2 claims remain forbidden. Next safe H-A2 work is to use this E1 result to pre-register the next validation-data or sample-expansion decision before any new download, broader replay, threshold change, OOS-selected filter, IBKR request, LLM call, GDELT retry, or edge claim.")
    elif (
        normal_control_exact_replay_preregistration
        and normal_control_exact_replay_preregistration.get("status") == "preregistered"
        and normal_control_exact_replay_preregistration.get("experiment_id")
        == "h_a2_normal_control_exact_replay"
    ):
        actions.append("H-A2.49 bounded normal/control exact replay is pre-registered as E0 control evidence for the single H-A2.48 candidate date, 2025-02-11, direction call. The future local run may compute candidate-date mid_pnl and implementable_pnl only for that date, using the locked 09:35 threshold 0.001 signal, 15:45 forced close, nearest discrete strike rounding, and $0.64 per-leg fees. This still cannot claim E2, edge validation, paper trading, operational validation, or real-money readiness. Next safe H-A2 work is to implement and run only this bounded local exact-replay diagnostic, then write research log 036 if the diagnostic completes. Do not download more data, broaden beyond 2025-02-11, change threshold 0.001, add an OOS-selected filter, request IBKR bars, call LLMs, retry GDELT, or claim E2.")
    elif (
        normal_control_import_diagnostic_summary
        and normal_control_import_diagnostic_summary.get("status") == "complete"
        and normal_control_import_diagnostic_summary.get("experiment_id") == "h_a2_normal_control_import_diagnostic"
    ):
        actions.append("H-A2.48 normal/control import diagnostic is complete as E1 import/availability evidence for `low_normal_vix_control_pack`. The already-downloaded 20 DBN/grouped files for 10 dates parse locally; SPY bars contain 3,900 rows; OPRA quote windows contain 35,284,142 rows and 557,254 0DTE valid-mid rows; timestamp alignment passes for 10/10 dates; the locked 09:35 threshold 0.001 signal finds exactly one candidate-ready date, 2025-02-11, with 0 data-blocked candidate dates. This is not PnL or edge evidence. Next safe H-A2 work is to pre-register a separate bounded exact-replay diagnostic for the candidate date only before computing candidate-trade PnL or making any E2 claim. Do not download more data, resume high-VIX-first acquisition, change threshold 0.001, add an OOS-selected filter, request IBKR bars, call LLMs, retry GDELT, approve paper trading, run unregistered PnL, or claim E2.")
    elif (
        normal_control_import_diagnostic_preregistration
        and normal_control_import_diagnostic_preregistration.get("status") == "preregistered"
        and normal_control_import_diagnostic_preregistration.get("experiment_id")
        == "h_a2_normal_control_import_diagnostic"
    ):
        actions.append("H-A2.47 normal/control import diagnostic is pre-registered as E0 control evidence for `low_normal_vix_control_pack`: the already-downloaded 20 DBN files / 20 grouped files for 10 dates from 2025-02-03 to 2025-02-14, total bytes 741,157,996, selected key env `DATABENTO_API_MO`, estimated cost $5.398913, may now be parsed locally after validator pass. Next safe H-A2 work is to run the local import/normalization/diagnostic step only: inventory raw files, import SPY bars, import OPRA quotes, verify timestamp alignment, reconstruct the locked 09:35 threshold 0.001 signal, and check entry/exit quote availability. Do not download more normal/control dates, resume high-VIX-first acquisition, change threshold 0.001, add an OOS-selected filter, request IBKR bars, call LLMs, retry GDELT, approve paper trading, run exact replay/PnL, or claim E2.")
    elif (
        normal_control_download_result
        and normal_control_download_result.get("status") == "pass"
        and normal_control_download_result.get("mode") == "download_complete"
        and normal_control_download_result.get("download_performed") is True
        and normal_control_download_result.get("scenario") == "h_a2_normal_control_low_normal_vix_control_pack"
        and normal_control_download_result.get("request_count") == 20
    ):
        actions.append("H-A2.46 normal/control download is complete as E0 data acquisition only for `low_normal_vix_control_pack`: 20 grouped files were downloaded/cache-confirmed for 10 dates from 2025-02-03 to 2025-02-14, total bytes 741,157,996, selected key env `DATABENTO_API_MO`, estimated cost $5.398913, and the locked 09:35 threshold 0.001 signal remains unchanged. Next safe H-A2 work is to pre-register the import/normalization/diagnostic step for this normal/control pack before parsing DBN, reconstructing the 09:35 signal, checking entry/exit quote availability, or deciding whether candidate trades exist. Do not download more normal/control dates, resume high-VIX-first acquisition, change threshold 0.001, add an OOS-selected filter, request IBKR bars, call LLMs, retry GDELT, approve paper trading, run exact replay/PnL, or claim E2.")
    elif (
        normal_control_paid_download_decision
        and normal_control_paid_download_decision.get("status") == "decision_complete"
        and normal_control_paid_download_decision.get("decision")
        == "approve_low_normal_vix_control_pack_download_after_paid_cost_audit_pass"
    ):
        actions.append("H-A2.45 normal/control paid download decision is complete as E0 control evidence for `low_normal_vix_control_pack` only. It preserves the locked 09:35 threshold 0.001 signal, selected key env `DATABENTO_API_MO`, 10 dates from 2025-02-03 to 2025-02-14, 150 planned required windows, 20 grouped conservative metadata calls, and estimated cost $5.398913. Next safe H-A2 work is to rerun `python scripts\\audit_paid_costs.py`; if it still passes, execute only the approved normal/control pack download and then write a separate download result artifact. Do not download from the metadata estimate alone, expand dates, download `post_stress_normalization_control_pack`, resume high-VIX-first acquisition, change threshold 0.001, add an OOS-selected filter, request IBKR bars, call LLMs, retry GDELT, approve paper trading, run exact replay/PnL, or claim E2.")
    elif (
        normal_control_cost_estimate
        and normal_control_cost_estimate.get("decision", {}).get("status")
        == "metadata_estimate_pass_next_download_decision_required"
        and normal_control_cost_estimate.get("batch_id") == "low_normal_vix_control_pack"
    ):
        actions.append("H-A2.44 normal/control independent-validation metadata estimate is complete as E0 cost-control evidence: `low_normal_vix_control_pack` covers 2025-02-03 to 2025-02-14, 10 local-VIX trading days, VIX 14.77-18.62, and no high-importance macro days. The live grouped Databento metadata estimate used selected key env `DATABENTO_API_MO`, planned 150 required windows, grouped them into 20 conservative metadata calls, estimated $5.398913, projected selected-key usage $5.398913 against the $100 per-key cap and $200 MO/AI pool cap, performed no download, and still sets download_allowed_under_current_guard=false. Next safe H-A2 work is to create a separate download decision artifact for this normal/control pack, then rerun paid-cost audit before any data pull. This is no exact replay/PnL/E2 claim evidence. Do not download from the estimate report alone, resume high-VIX-first acquisition, change threshold 0.001, add an OOS-selected filter, request IBKR bars, call LLMs, retry GDELT, approve paper trading, run exact replay/PnL, or claim E2.")
    elif (
        normal_control_sample_decision
        and normal_control_sample_decision.get("status") == "preregistered"
        and normal_control_sample_decision.get("experiment_id") == "h_a2_normal_control_sample_decision"
    ):
        actions.append("H-A2.43 normal/control independent-validation sample decision is pre-registered as E0 control evidence after H-A2.42. The 2025-04-08 high-VIX sample remains E1 import/availability evidence only: OPRA windows contain 1,686,591 quote rows and 43,965 0DTE valid-mid rows, but clean macro/VIX is false because prior VIX was 46.98, so there is no candidate trade signal and no exact replay/PnL/E2 claim. Next safe H-A2 work is to build or update the metadata-only cost-estimate runner for `low_normal_vix_control_pack` (2025-02-03 to 2025-02-14, 10 local-VIX trading days, VIX 14.77-18.62, no high-importance macro days), using selected key env `DATABENTO_API_MO` without storing the key value. Do not download data, resume high-VIX-first acquisition, change threshold 0.001, add an OOS-selected filter, request IBKR bars, call LLMs, retry GDELT, approve paper trading, or claim E2.")
    elif (
        independent_validation_import_diagnostic_summary
        and independent_validation_import_diagnostic_summary.get("status") == "complete"
        and independent_validation_import_diagnostic_summary.get("experiment_id")
        == "h_a2_independent_validation_import_diagnostic"
    ):
        actions.append("H-A2.42 one-day independent-validation import diagnostic is complete as E1 import/availability evidence for sample_cost_probe_high_vix_one_day (2025-04-08). All 15 raw DBN files parse locally; SPY bars cover 09:30-15:59 ET; OPRA windows contain 1,686,591 quote rows and 43,965 0DTE valid-mid rows; the 09:35 locked 5-minute put followthrough passes threshold 0.001, but the clean macro/VIX condition is false because prior VIX was 46.98, so there is no candidate trade signal and no exact replay/PnL/E2 claim. User selected normal/control samples as the next independent-validation priority, so next safe H-A2 work is to pre-register a normal/control sample decision or no-paid validation gap decision before any additional data pull, exact replay, IBKR request, LLM call, paper trading, or E2 claim.")
    elif (
        independent_validation_import_diagnostic_preregistration
        and independent_validation_import_diagnostic_preregistration.get("status") == "preregistered"
        and independent_validation_import_diagnostic_preregistration.get("experiment_id")
        == "h_a2_independent_validation_import_diagnostic"
    ):
        actions.append("H-A2.41 one-day independent-validation import/normalization/diagnostic is pre-registered as E0 control evidence for sample_cost_probe_high_vix_one_day (2025-04-08). The plan preserves the locked 09:35-only signal and threshold 0.001, allows only local parsing of the already-downloaded raw DBN files after validator pass, and requires raw-file inventory, SPY bar import, OPRA quote import, timestamp alignment, locked-signal reconstruction, and entry/exit quote availability checks. Next safe H-A2 work is to implement and run the local import diagnostic, writing `reports/diagnostics/h_a2_independent_validation_import_diagnostic.json` and `.md` plus its search log. Do not download more validation packs, run exact replay directly, change the threshold, add an OOS-selected filter, request IBKR bars, call LLMs, retry GDELT, approve paper trading, or claim E2.")
    elif (
        independent_validation_download_result
        and independent_validation_download_result.get("status") == "pass"
        and independent_validation_download_result.get("mode") == "download_complete"
        and independent_validation_download_result.get("download_performed") is True
        and independent_validation_download_result.get("request_count") == 15
    ):
        actions.append("H-A2.40 one-day independent-validation download is complete for sample_cost_probe_high_vix_one_day (2025-04-08): 15 Databento requests were downloaded/cache-confirmed, total bytes are 54,014,593, logged estimate is $0.504662, cost guard now uses $120.494368 with $4.505632 remaining under the $125 stop, threshold 0.001 and the 09:35-only signal remain locked, and this is data acquisition only. Next safe H-A2 work is to pre-register the import/normalization/diagnostic step for this one-day raw data before parsing DBN, reconstructing the 09:35 signal, checking entry/exit quote availability, or deciding whether any candidate trade exists. Do not download more validation packs, run exact replay directly, change the threshold, add an OOS-selected filter, request IBKR bars, call LLMs, retry GDELT, approve paper trading, or claim E2.")
    elif (
        independent_validation_paid_download_decision
        and independent_validation_paid_download_decision.get("status") == "decision_complete"
        and independent_validation_paid_download_decision.get("decision")
        == "approve_sample_cost_probe_high_vix_one_day_download_after_paid_cost_audit_pass"
    ):
        actions.append("H-A2.39 one-day paid download decision is complete for sample_cost_probe_high_vix_one_day (2025-04-08): scope is capped to the 15 Databento requests already metadata-estimated; Databento estimated $0.504662, projected usage after download is $120.494368 against the $125 guard, threshold 0.001 and the 09:35-only signal remain locked, and no research result or E2 claim exists yet. Next safe H-A2 work is to rerun `python scripts\\audit_paid_costs.py`; if it still passes, execute only this one-day download and write a download result report. Do not download broad 2025 data, other validation packs, change the threshold, add an OOS-selected filter, request IBKR bars, call LLMs, retry GDELT, approve paper trading, run exact replay directly, or claim E2.")
    elif (
        independent_validation_paid_cost_estimate
        and independent_validation_paid_cost_estimate.get("decision", {}).get("status")
        == "metadata_estimate_pass_next_download_decision_required"
    ):
        actions.append("H-A2.38 independent-validation metadata cost estimate passed for sample_cost_probe_high_vix_one_day (2025-04-08): Databento estimated $0.504662 for 15 metadata-costed requests, no download was performed, projected usage would be $120.494368 against the $125 guard, and the report still sets download_allowed_under_current_guard=false. Next safe H-A2 work is to create a separate download decision artifact for this one-day batch, then rerun paid-cost audit before any download. Do not download from the estimate report alone, estimate broad 2025 calendar data, change threshold 0.001, add an OOS-selected filter, request IBKR bars, call LLMs, retry GDELT, approve paper trading, or claim E2.")
    elif (
        independent_validation_paid_cost_plan_preregistration
        and independent_validation_paid_cost_plan_preregistration.get("status") == "preregistered"
    ):
        actions.append("H-A2.37 independent-validation paid-cost estimate plan is pre-registered as E0 control evidence: exact high-VIX/control windows and required OPRA/SPY/regime fields are named before any provider call. Next safe H-A2 work is to build or run a metadata-only cost-estimate plan/runner, starting with sample_cost_probe_high_vix_one_day (2025-04-08) only, after the H-A2.37 validator and paid-cost audit pass. Do not download data, estimate broad 2025 calendar data, change threshold 0.001, add an OOS-selected filter, request IBKR bars, call LLMs, retry GDELT, approve paper trading, or claim E2.")
    elif (
        independent_validation_feasibility_summary
        and independent_validation_feasibility_summary.get("status") == "complete"
    ):
        actions.append("H-A2.35 independent validation feasibility diagnostic is complete as E1 diagnostic evidence: no-paid sources can define the validation gap and regime requirements, but they cannot add independent implementable SPY 0DTE PnL days; retained OOS remains 14 trade days, high-VIX retained validation coverage is still missing, and MinTRL/PSR acceptance remains unproven. Next safe H-A2 work is to pre-register a narrow paid-cost estimate plan for independent validation windows before any live Databento estimate, paid download, IBKR request, exact replay, paper trading, or E2 claim. Do not change threshold 0.001, add an OOS-selected filter, call LLMs, retry GDELT, approve paper trading, or claim E2.")
    elif (
        original_entry_robustness_prioritization_summary
        and original_entry_robustness_prioritization_summary.get("status") == "complete"
    ):
        actions.append("H-A2.34 original-entry robustness/prioritization review is complete as E1 diagnostic evidence: the 09:35-only rule and threshold 0.001 were preserved, leave-one-out and skip-cost checks remain directionally useful, retained OOS still has 14 trade days, and high-VIX retained coverage is missing. Next safe H-A2 work is to pre-register an independent validation-data plan or no-paid validation feasibility plan before any paid data, IBKR request, exact replay, paper trading, or E2 claim. Do not claim delayed-entry edge, run exact replay, buy data, request IBKR bars, call LLMs, approve paper trading, or claim E2.")
    elif (
        delayed_entry_condition_summary
        and delayed_entry_condition_summary.get("status") == "complete"
    ):
        actions.append("H-A2.32 original-entry revision diagnostic is complete as E1 diagnostic evidence: the 09:35-only rule is timestamp-clean, excludes the 15-minute conflict component, keeps threshold 0.001 locked, and retains 14 OOS trade days, but remains under-sampled and underpowered. Next safe H-A2 work is to pre-register a stricter original-entry robustness/prioritization review or independent validation-data plan before any claim upgrade. Do not claim delayed-entry edge, run exact replay, buy data, request IBKR bars, call LLMs, approve paper trading, or claim E2.")
    elif (
        delayed_entry_condition_preregistration
        and delayed_entry_condition_preregistration.get("status") == "preregistered"
    ):
        actions.append("H-A2.29 delayed-entry condition is pre-registered as E0 control evidence: next safe in-plan work is to run a no-paid local delayed-entry diagnostic with candidate decision time 09:45 ET, threshold 0.001 locked, explicit delayed-entry fill/cost handling, train/OOS retained-count reporting, and sample-adequacy labels. Do not reuse original 09:35 PnL as delayed-entry PnL, change threshold 0.001 through OOS search, add a new OOS-selected filter, run exact replay, buy data, request IBKR bars, call LLMs, approve paper trading, or claim E2.")
    elif (
        locked_condition_signal_attribution_summary
        and locked_condition_signal_attribution_summary.get("status") == "complete"
    ):
        actions.append("H-A2.27 locked-condition signal-attribution audit is complete as E1 diagnostic evidence: threshold 0.001 stayed locked, no threshold or new OOS-selected filter search was used, and the full condition is not knowable at the original 09:35 ET entry because the 15-minute conflict component is only known around 09:45 ET. Treat it as delayed-entry candidate and diagnostic proxy only. Next safe H-A2 work is a separately pre-registered delayed-entry test or a timestamp-clean original-entry rule revision; do not run exact replay, buy data, request IBKR bars, call LLMs, approve paper trading, or claim E2 from H-A2.27.")
    elif (
        locked_condition_signal_attribution_preregistration
        and locked_condition_signal_attribution_preregistration.get("status") == "preregistered"
    ):
        actions.append("H-A2.27 locked-condition signal-attribution audit is pre-registered as E0 control evidence: next safe in-plan work is to run the no-paid local audit that classifies threshold 0.001 as deployable entry filter, delayed-entry candidate, or diagnostic proxy only. Do not change threshold 0.001, add a new OOS-selected filter, buy data, request IBKR bars, call LLMs, approve paper trading, or claim E2.")
    elif (
        revised_condition_robustness_summary
        and revised_condition_robustness_summary.get("status") == "complete"
    ):
        actions.append("H-A2.26 revised-condition robustness audit is complete as E1 diagnostic evidence: threshold 0.001 stayed locked, no threshold search or OOS tuning was used, retained OOS has 13 trade days, and the result remains under-sampled/underpowered. Keep H-A2 active only as prioritization evidence; next safe H-A2 work is exact replay after the 2022 SPY bar blocker clears, or a separately pre-registered local follow-up that does not change threshold 0.001. Do not buy data, request IBKR bars, call LLMs, approve paper trading, or claim E2 from this audit.")
    elif (
        revised_condition_robustness_preregistration
        and revised_condition_robustness_preregistration.get("status") == "preregistered"
    ):
        actions.append("H-A2.25 revised-condition robustness audit is pre-registered as E0 control evidence: next safe in-plan work is to run the no-paid local robustness audit against locked threshold 0.001. Do not search a new threshold, tune on OOS, run exact replay, buy data, request IBKR bars, call LLMs, approve paper trading, or claim E2.")
    elif (
        revised_opening_followthrough_summary
        and revised_opening_followthrough_summary.get("status") == "complete"
    ):
        actions.append("H-A2 revised opening-followthrough diagnostic is complete as E1 prioritization evidence: train-only threshold 0.001 improved local OOS residual-loss behavior, but the revised OOS sample has only 13 trade days. Keep this as under-sampled evidence only; do not use exact replay, paid data, IBKR requests, LLM calls, paper trading, or E2 claims from this result. Next safe H-A2 work is exact replay only after the external 2022 SPY bar blocker clears, or separately pre-registered no-paid robustness with train-only rules and no OOS tuning.")
    elif (
        revised_opening_followthrough_preregistration
        and revised_opening_followthrough_preregistration.get("status") == "preregistered"
    ):
        actions.append("H-A2 revised opening-followthrough condition is pre-registered as E0 control evidence: next safe in-plan work is to implement and run the local-only revised-condition diagnostic using existing artifacts only. Keep thresholds train-only, forbid OOS tuning, and do not use exact replay, paid data, IBKR requests, LLM calls, paper trading, or E2 claims.")
    elif residual_analysis and residual_analysis.get("status") == "complete":
        actions.append("H-A2 residual/adverse-day analysis is complete as E1 diagnostic evidence: next safe in-plan work is to pre-register a revised H-A2 condition that adds opening-followthrough failure-mode checks before any exact replay, paid data, IBKR request, LLM call, paper trading, or E2 claim.")
    elif residual_preregistration and residual_preregistration.get("status") == "preregistered":
        actions.append("H-A2.21 residual/adverse-day analysis is pre-registered: next safe in-plan work is to run the local-only analysis of non-risk losing days, macro-only losing days, and residual adverse buckets. Keep H-L1 live LLM/news research blocked until real timestamp-clean news cases exist; do not buy data, run GDELT live retry during cooldown, call LLMs, approve paper trading, or claim E2.")
    elif post_proxy_decision and post_proxy_decision.get("status") == "decision_complete":
        actions.append("H-A2/H-L1 post-proxy decision is complete: next safe in-plan work is to pre-register H-A2 residual/adverse-day analysis using local artifacts only. Keep H-L1 live LLM/news research blocked until real timestamp-clean news cases exist; do not buy data, run GDELT live retry during cooldown, call LLMs, approve paper trading, or claim E2.")
    elif h_a2_proxy_robustness and h_a2_proxy_robustness.get("status") == "complete":
        actions.append("H-A2.19 proxy-first robustness is complete as E1 evidence: non-risk days outperform risk-labeled days across 5-minute proxy, 15-minute proxy, and existing trade outcomes, but exact 2022-10 replay, E2 acceptance, paper trading, and operational validation remain blocked. Use it only to prioritize or revise H-A2; do not treat missing 2022 SPY 1-minute bars as blocking all mechanism-level proxy work.")
    if not (post_proxy_decision and post_proxy_decision.get("status") == "decision_complete") and h_l1_macro_proxy and h_l1_macro_proxy.get("status") == "complete":
        actions.append("L.7 macro-event proxy baseline is complete as E1 non-LLM evidence: scheduled macro/VIX labels are now the deterministic baseline that future real-news or LLM scores must beat. Keep live LLM research blocked until real timestamp-clean news cases exist, and do not call this result LLM/news evidence.")
    if "requires_databento_api_key_for_aug_2023_live_cost" in blockers:
        actions.append("Configure one supported Databento API key env (`DATABENTO_API_KEY`, `DATABENTO_SPY0DTE_API`, `DATABENTO_API_MO`, or `DATABENTO_API_AI`), then run the Aug 2023 chunked live cost estimate before any download.")
    gdelt_cooldown = "gdelt_retry_cooldown_recommended" in blockers
    news_archive_blocked = "requires_real_news_archive" in blockers or "requires_news_coverage_audit_report" in blockers
    if news_archive_blocked and GDELT_BULK_SOURCE_DECISION_NOTE.exists():
        bulk_manifest = _load_report_artifact(GDELT_BULK_MANIFEST_REPORT)
        gkg_probe = _load_report_artifact(GDELT_GKG_ONE_FILE_PROBE_REPORT)
        doc_api_scaffold = _load_report_artifact(GDELT_DOC_API_ENRICHMENT_SCAFFOLD_REPORT)
        if doc_api_scaffold and doc_api_scaffold.get("status") == "scaffold_pass_real_archive_blocked":
            actions.append("News-Unblock priority is now to evaluate alternative timestamp-clean real-news source paths instead of waiting only on GDELT. Use `reports\\news_gdelt_doc_api_enrichment_scaffold.md` as the current GDELT scaffold reference, but next write a source-decision artifact comparing feasible real headline/body, publication timestamp, fetch/availability timestamp, licensing, parser/import, and decision-time discipline paths before any live LLM research. Keep GKG as candidate index only; do not broad-download GKG or run LLM research yet.")
        elif gkg_probe and gkg_probe.get("status") == "blocked_requires_enrichment_or_policy":
            actions.append("Use `reports\\news_gdelt_gkg_one_file_parser_probe.md` and `docs\\GDELT_GKG_ENRICHMENT_DECISION_NOTE.md` to choose a timestamp-clean GKG enrichment or DOC API join path for verified headlines/publication timestamps/topic mapping; do not download broad GKG archives or run LLM research until canonical import audit passes.")
        elif bulk_manifest and bulk_manifest.get("status") == "ready_for_one_file_probe":
            actions.append("Use `reports\\news_gdelt_bulk_raw_manifest.md` to select one small GKG file for a controlled parser probe; do not download broad raw archives or run LLM research until timestamp/source/headline/url mapping passes canonical import audit.")
        else:
            actions.append("Implement a no-download GDELT bulk raw-file manifest/size probe from `docs\\GDELT_BULK_RAW_SOURCE_DECISION_NOTE.md`; map candidate decision windows to file URLs, file families, likely byte counts, timestamp fields, and parser blockers before any bulk data download.")
    if gdelt_cooldown:
        actions.append("Pause additional live GDELT `--execute` retries until HTTP 429 pressure clears; monitor the command plan before retrying one candidate day.")
    if not gdelt_cooldown and news_archive_blocked and not GDELT_BULK_SOURCE_DECISION_NOTE.exists():
        actions.append("Retry timestamp-safe GDELT capture after HTTP 429 pressure clears, then import and audit the real news archive.")
    if "requires_real_timestamp_clean_news_cases_for_exp07_prompt_research" in blockers:
        actions.append("Do not run another synthetic Exp07 prompt matrix as research; build real timestamp-clean news cases first.")
    if "requires_real_timestamp_clean_news_cases" in blockers:
        actions.append("Use `reports\\experiments\\exp07_real_news_case_plan.md` as the collection plan before any Exp07 prompt-family run.")
    if "requires_controlled_opra_statistics_download_import_probe" in blockers:
        actions.append("OPRA statistics/OI metadata probe passed with timing caveat; next run a controlled one-day full-day statistics download/import probe, inspect `stat_type` values and timestamp semantics, then decide whether Databento OI can support gamma-family research.")
    if "requires_mintrl_psr_sample_adequacy" in blockers or "requires_wider_spy_0dte_data" in blockers:
        h_a2_spy_bar_blocker = _load_report_artifact(H_A2_2022_10_SPY_BARS_UNAVAILABLE)
        if h_a2_spy_bar_blocker and h_a2_spy_bar_blocker.get("status") == "blocked":
            h_a2_exact_underlying_plan = _load_report_artifact(H_A2_EXACT_2022_UNDERLYING_BAR_PLAN)
            h_a2_exact_underlying_plan_done = False
            if (
                h_a2_exact_underlying_plan
                and h_a2_exact_underlying_plan.get("status") == "plan_complete"
                and h_a2_exact_underlying_plan.get("decision")
                == "build_bounded_acquisition_import_tool_before_any_source_execution"
            ):
                h_a2_spy_bars_import = _load_report_artifact(H_A2_2022_SPY_BARS_IMPORT_SUMMARY)
                if (
                    h_a2_spy_bars_import
                    and h_a2_spy_bars_import.get("status") == "fixture_import_pass"
                    and h_a2_spy_bars_import.get("ready_for_exact_rerun") is False
                ):
                    ibkr_readiness = _load_report_artifact(H_A2_IBKR_SPY_BARS_READINESS_PROBE)
                    if ibkr_readiness and ibkr_readiness.get("status") == "blocked_local_ibkr_unavailable":
                        available_packages = ", ".join(ibkr_readiness.get("available_packages") or [])
                        package_note = (
                            f" Python clients are available (`{available_packages}`),"
                            if available_packages
                            else " Python client availability is still unresolved,"
                        )
                        actions.append("H-A2.17 IBKR readiness gate rerun is complete and externally blocked:" + package_note + " but no local IBKR API port is listening on 7497/7496/4002/4001. No historical data was requested, no order was transmitted, no paid data was used, and no new provider was introduced. Next start local TWS/Gateway with API enabled and confirm market-data permission, then rerun the readiness probe. If local IBKR cannot be made available, stop for clear user direction before Alpaca or any new paid provider. Do not treat fixture bars as real data, rerun exact H-A2 stress diagnostics, approve paper trading, or claim H-A2 edge from H-A2.16/H-A2.17.")
                    elif ibkr_readiness and ibkr_readiness.get("status") == "ready_for_manual_data_probe":
                        actions.append("H-A2.17 IBKR readiness gate is ready for a separate explicit data-only historical-bars probe. Request only SPY 2022-10 1-minute bars, preserve pacing/timestamp/provenance checks, and do not transmit orders or rerun H-A2 until real bar coverage validation passes.")
                    else:
                        actions.append("H-A2.16 bounded SPY 2022-10 bar acquisition/import tool is complete in fixture mode: the canonical `spy_bar` shape, coverage audit, timestamp conversion, source manifest, and option-join gate are tested without network, paid data, IBKR requests, or orders. Next rerun/clear the IBKR readiness gate before any live data-only historical-bars request. Do not treat fixture bars as real data, rerun exact H-A2 stress diagnostics, buy data, introduce a new provider, approve paper trading, or claim H-A2 edge from this tool.")
                else:
                    actions.append("H-A2.15 exact 2022 underlying-bar plan is complete: next implement and test the bounded SPY 2022-10 bar acquisition/import tool in dry-run and fixture mode. Do not execute a live IBKR historical-bars request until the tool exists, readiness status is `ready_for_manual_data_probe`, and coverage/timestamp/import gates are defined. Do not buy data, introduce a new provider, buy 2022-09 option data, rerun exact stress diagnostics, approve paper trading, or claim H-A2 edge from this plan.")
                h_a2_exact_underlying_plan_done = True
            h_a2_exact_prioritization = _load_report_artifact(H_A2_EXACT_DATA_PRIORITIZATION_DECISION)
            h_a2_exact_prioritization_done = h_a2_exact_underlying_plan_done
            if (
                not h_a2_exact_underlying_plan_done
                and
                h_a2_exact_prioritization
                and h_a2_exact_prioritization.get("status") == "decision_complete"
                and h_a2_exact_prioritization.get("selected_next_path", {}).get("path_id")
                == "draft_narrow_exact_2022_underlying_bar_plan"
            ):
                actions.append("H-A2.14 exact-data prioritization decision is complete: H-A2.13 is directionally coherent enough to justify a separate narrow 2022-10 underlying-bar plan, but not source execution. Next draft that plan with hypothesis-first scope, coverage/timestamp/import validation, and explicit approval gates. Do not request IBKR bars, buy data, introduce a new provider, buy 2022-09 option data, run exact stress diagnostics, approve paper trading, or claim H-A2 edge from H-A2.14 alone.")
                h_a2_exact_prioritization_done = True
            h_a2_spy_bar_source_decision = _load_report_artifact(H_A2_2022_SPY_BAR_SOURCE_DECISION)
            if (
                not h_a2_exact_prioritization_done
                and h_a2_spy_bar_source_decision
                and h_a2_spy_bar_source_decision.get("status") == "decision_complete"
                and h_a2_spy_bar_source_decision.get("selected_next_action") == "run_no_paid_ibkr_data_only_probe_if_local_ibkr_setup_is_available"
            ):
                ibkr_readiness = _load_report_artifact(H_A2_IBKR_SPY_BARS_READINESS_PROBE)
                if ibkr_readiness and ibkr_readiness.get("status") == "blocked_local_ibkr_unavailable":
                    available_packages = ", ".join(ibkr_readiness.get("available_packages") or [])
                    package_note = (
                        f" IBKR Python clients are available in the venv (`{available_packages}`),"
                        if available_packages
                        else " IBKR Python clients are not available in the venv,"
                    )
                    actions.append("H-A2 2022-10 stress option quotes are downloaded and normalized, but the ORB rerun is blocked because Databento `EQUS.MINI` cannot supply 2022 SPY 1-minute bars." + package_note + " but no local IBKR API port is listening and no historical bars were requested. Start TWS/Gateway with API enabled and rerun the readiness probe, or stop for clear user direction before Alpaca or any new paid provider. Do not transmit orders, buy a new paid provider, or buy 2022-09 option data while this underlying-bar blocker remains active.")
                elif ibkr_readiness and ibkr_readiness.get("status") == "ready_for_manual_data_probe":
                    actions.append("H-A2 2022-10 stress option quotes are downloaded and normalized, but the ORB rerun is blocked because Databento `EQUS.MINI` cannot supply 2022 SPY 1-minute bars. The no-paid IBKR readiness probe is ready for a separate explicit data-only historical-bars probe. Request only SPY 2022-10 1-minute bars, preserve pacing/timestamp checks, and do not transmit orders or rerun H-A2 until coverage validation passes.")
                else:
                    actions.append("H-A2 2022-10 stress option quotes are downloaded and normalized, but the ORB rerun is blocked because Databento `EQUS.MINI` cannot supply 2022 SPY 1-minute bars. The source decision now selects a no-paid IBKR data-only historical-bars probe if local TWS/Gateway and data permissions are available; do not transmit orders, buy a new paid provider, or buy 2022-09 option data while this underlying-bar blocker remains active.")
            elif not h_a2_exact_prioritization_done:
                actions.append("H-A2 2022-10 stress option quotes are downloaded and normalized, but the ORB rerun is blocked because Databento `EQUS.MINI` cannot supply 2022 SPY 1-minute bars (`data_start_before_available_start`). Next create a 2022 SPY bar source decision; do not buy more 2022 option data, including 2022-09, while underlying bars are the active blocker.")
        if GREEKS_OI_ENRICHMENT_REPORT.exists() and GAMMA_AGGREGATION_POLICY_DOC.exists() and GAMMA_AGGREGATION_DIAGNOSTIC_SUMMARY.exists():
            if H_G1_MANIFEST_V3.exists():
                v3_cost = _load_report_artifact(H_G1_V3_REPLACEMENT_COST_ESTIMATE)
                side_aware_diagnostic = _load_report_artifact(H_G1_V3_SIDE_AWARE_DIAGNOSTIC)
                acceptance_review = _load_report_artifact(H_G1_ACCEPTANCE_BLOCKER_REVIEW)
                strategy_ablation = _load_report_artifact(H_G1_STRATEGY_ABLATION_SUMMARY)
                post_ablation_decision = _load_report_artifact(H_G1_POST_ABLATION_DECISION)
                sample_expansion_plan = _load_report_artifact(H_G1_SAMPLE_EXPANSION_PLAN)
                if (
                    sample_expansion_plan
                    and sample_expansion_plan.get("status") == "plan_complete"
                    and sample_expansion_plan.get("decision") == "keep_h_g1_parked_with_preregistered_sample_expansion_requirements"
                ):
                    overlap_scan = _load_report_artifact(H_G1_LOCAL_CACHE_OVERLAP_SCAN)
                    if overlap_scan and overlap_scan.get("status") == "blocked_no_additional_no_paid_overlap":
                        actions.append("H-G1.24a no-paid local-cache overlap scan is complete and blocked: no additional baseline trade dates have local quote, local SPY bar, and local OI files beyond the current 2-date gamma intersection. H-G1 remains parked; do not run a metadata cost check, paid data download, new gamma ablation, strategy use, paper trading, or true net-gamma claim from this scan. Active edge work should prefer News-Unblock N.7 or H-A2 once their external blockers clear.")
                    else:
                        actions.append("H-G1.24 sample-expansion plan is complete: H-G1 remains parked, but the next H-G1-only safe step is a no-paid local-cache overlap scan before any metadata cost check, paid data, new ablation, strategy use, paper trading, or true net-gamma claim. Active edge work should still prefer News-Unblock N.7 or H-A2 once their external blockers clear.")
                elif (
                    post_ablation_decision
                    and post_ablation_decision.get("decision") == "park_h_g1_pending_sample_expansion_plan"
                    and post_ablation_decision.get("selected_next_safe_action") == "return_to_news_unblock_n7"
                ):
                    actions.append("H-G1.23 decision is complete: H-G1 is parked pending a separate sample-expansion plan, because H-G1.22 had only 2 intersecting baseline trades and all gamma-filtered variants had 0 active trades. Return active implementation to News-Unblock N.7 for one narrow real DOC API retry/import/audit after GDELT cooldown clears. Do not use H-G1 as a trading filter, approve paper trading, buy paid data from H-G1.22 alone, or claim true market-maker net gamma.")
                elif strategy_ablation and strategy_ablation.get("status") == "complete_underpowered":
                    actions.append("H-G1.22 strategy-ablation diagnostic is complete and underpowered: only 2 baseline closed trades intersect the available gamma-proxy dates, all gamma variants collapse to 0 active trades, and H-G1 remains E1 with strategy use/paper trading forbidden. Next decide whether to park H-G1, draft a separate sample-expansion decision artifact, or return to News-Unblock N.7; do not rerun this ablation, add variants, buy data, or claim true market-maker net gamma without a new preregistered decision.")
                elif H_G1_STRATEGY_ABLATION_PREREGISTRATION.exists():
                    actions.append("H-G1.21 strategy-ablation pre-registration is complete: baseline and three gamma-filtered variants are locked with chronological split, search log/DSR, MinTRL/PSR, implementable PnL, big-day dependency, and signed-OI proxy caveats. Next implement the no-paid H-G1 gamma strategy-ablation runner against this artifact; do not add variants, tune OOS, buy data, approve paper trading, or claim true market-maker net gamma.")
                elif acceptance_review and acceptance_review.get("status") == "blocked_before_strategy_use":
                    actions.append("H-G1.20 acceptance blocker review is complete: H-G1 remains E1/proxy-validity only; strategy use, paper trading, and NOVI/net-gamma strategy filter remain forbidden. Next either pre-register H-G1 gamma strategy ablation with search log/DSR, MinTRL/PSR, implementable PnL, big-day dependency, and proxy caveats, or return to News-Unblock N.7 after GDELT cooldown clears.")
                elif side_aware_diagnostic and side_aware_diagnostic.get("status") == "pass_diagnostic_only":
                    actions.append("H-G1.19 side-aware data-validity diagnostic passed with status `pass_diagnostic_only` under policy id `h_g1_required_bucket_policy_v3_side_aware`: raw-row coverage, side-aware required-bucket coverage, timestamp, stability, economic-sign, and search-log gates pass using manifest-v3 rows only, with no paid data, no network, and no strategy PnL. H-G1 remains E1/proxy-validity only and strategy use still forbidden; next run a strategy-independent acceptance blocker review before any NOVI/net-gamma strategy filter.")
                elif H_G1_SIDE_AWARE_POLICY_ADOPTION.exists():
                    actions.append("H-G1.18 side-aware bucket policy adoption is complete for the next diagnostic only: policy id `h_g1_required_bucket_policy_v3_side_aware` is adopted from candidate B, with strategy use, paid data, new dates, and strategy-PnL selection still forbidden. Next rerun the H-G1 gamma diagnostic on manifest-v3 rows under this policy, preserving raw-row coverage, timestamp, stability, economic-sign, search-log, and opposite-right ITM reporting; do not use NOVI/net-gamma as a strategy filter.")
                elif H_G1_BUCKET_POLICY_COMPARISON.exists():
                    actions.append("H-G1.17 bucket-policy comparison is complete and H-G1 is still blocked: candidate B side-aware required-bucket passes coverage review across 10/10 dates, while current v2 remains blocked and notional-weighted remains blocked. Next draft an explicit side-aware policy-adoption artifact and then rerun the gamma diagnostic under that policy only after allowed/forbidden claims are stated; do not buy data, change dates, use strategy PnL for policy selection, or use NOVI/net-gamma as a strategy filter.")
                elif H_G1_BUCKET_POLICY_REVIEW_PREREGISTRATION.exists():
                    actions.append("H-G1.16 bucket-policy review pre-registration is complete and H-G1 is still blocked: candidate policies are locked as current v2 moneyness-only, side-aware required-bucket, and OI/gamma-notional coverage gates. Next run a no-paid policy-comparison diagnostic using manifest-v3 rows only; do not change dates, buy data, use strategy PnL for policy selection, or use NOVI/net-gamma as a strategy filter.")
                elif H_G1_V3_BUCKET_FAILURE_DIAGNOSTIC.exists():
                    actions.append("H-G1.15 manifest-v3 bucket-failure diagnostic is complete and H-G1 is still blocked: all 55 blocked rows inside the five failed buckets are opposite-right ITM rows created by moneyness-only buckets, while computed OI-notional share remains at least 0.880098. Next do a pre-registered bucket-policy review before any policy revision, replacement date, paid OI pull, or strategy-filter use. Do not use NOVI/net-gamma as a strategy filter.")
                elif H_G1_V3_DIAGNOSTIC_SUMMARY.exists():
                    actions.append("H-G1.14 manifest-v3 diagnostic is complete and still blocked: raw-row coverage and economic-sign gates pass, but bucket-weighted coverage fails on five date/bucket cells. Next diagnose the v3 bucket failures before any policy revision, replacement date, or strategy-filter use. Do not use NOVI/net-gamma as a strategy filter.")
                elif H_G1_V3_REPLACEMENT_DOWNLOAD_RESULT.exists():
                    actions.append("H-G1 v3 replacement OI download exists: next rerun H-G1 enrichment/diagnostic using manifest v3 and the `2023-09-13` replacement OI day. Do not use NOVI/net-gamma as a strategy filter until the diagnostic passes coverage, timestamp, stability, economic-sign, and search-log gates.")
                elif v3_cost and v3_cost.get("decision", {}).get("status") == "pass":
                    actions.append("H-G1.12 is complete: metadata cost gate passed for exactly one replacement OPRA statistics/OI day (`2023-09-13`) at `$0.384999`, with projected usage `$109.467226` under the `$125` guard. Next perform the controlled one-day OI download only; do not broaden scope or use NOVI/net-gamma as a strategy filter.")
                else:
                    actions.append("H-G1.11 is complete: concrete manifest v3 validates with `2023-09-13` replacing `2023-07-12` by locked macro/VIX/local-cache ranking rules. Next run a metadata cost check for exactly one replacement OPRA statistics/OI day before any download. Do not use NOVI/net-gamma as a strategy filter.")
            elif H_G1_POLICY_V2_1_REVIEW.exists() and H_G1_MANIFEST_V3_PLAN.exists():
                actions.append("H-G1.10 is complete: policy v2.1 exists only as a review artifact and the manifest v3 replacement plan is pre-registered. Next create the concrete manifest v3 by selecting one in-sample low-volatility high-importance-macro replacement for `2023-07-12` using only the locked ranking rules; validate it before any metadata cost check or paid OI pull. Do not use NOVI/net-gamma as a strategy filter.")
            elif H_G1_POLICY_MANIFEST_DECISION.exists():
                actions.append("H-G1 policy/manifest decision is complete: policy revision alone is rejected because `2023-07-12 otm_put` has only `0.662545` computed OI-notional coverage. Next draft policy v2.1 as a review artifact and create a manifest v3 replacement plan before any new paid OI pull. Do not use NOVI/net-gamma as a strategy filter.")
            elif H_G1_BUCKET_FAILURE_DIAGNOSTIC.exists():
                actions.append("H-G1 bucket-failure diagnostic is complete: all five v2 required-bucket failures are Black-Scholes bracket blocks; four failed buckets retain high computed OI-notional share, but `2023-07-12 otm_put` retains only `0.662545`. Use `reports\\diagnostics\\h_g1_bucket_failure_diagnostic.md` to choose a narrow policy revision review or a v3 replacement-date manifest before any new paid OI pull. Do not use NOVI/net-gamma as a strategy filter.")
            elif H_G1_V2_DIAGNOSTIC_SUMMARY.exists():
                actions.append("H-G1 manifest v2 repair diagnostic is complete: Databento EQUS.MINI cannot repair `2023-03-13`/`2023-03-22` because SPY bars start at `2023-03-28`; v2 raw-row coverage now passes, but required-bucket computed-Greeks coverage still blocks H-G1. Next investigate the five bucket failures in `reports\\diagnostics\\h_g1_gamma_regime_diagnostic_summary_v2_10date.json` or create a separate v3 replacement-date manifest before any new paid OI pull. Do not use NOVI/net-gamma as a strategy filter.")
            elif H_G1_DATA_QUALITY_REVIEW.exists():
                actions.append("Before any further broad Databento download, use `reports\\diagnostics\\h_g1_data_quality_review.md` and the H-G1 v2 diagnostic to either repair the missing `2023-03-13`/`2023-03-22` SPY bar cache or create a manifest v2 with replacement dates; then rerun H-G1 enrichment/diagnostic and only consider paid data after paid-cost/readiness audits confirm headroom.")
            else:
                actions.append("Before any further broad Databento download, use `reports\\risk_first_data_audit.md`, `reports\\greeks_oi_enrichment_probe_report.md`, `docs\\GAMMA_AGGREGATION_VALIDATION_POLICY.md`, and `reports\\diagnostics\\gamma_aggregation_diagnostic_summary.json` as the pre-purchase checkpoint: expand the pre-registered H-G1 gamma/OI regime date set, choose missing-regime H-A2 stress/pre-break coverage, or revise toward a higher-density strategy hypothesis; then re-run paid-cost/readiness audits and confirm actual provider usage remains below the stop threshold.")
        elif GREEKS_OI_ENRICHMENT_REPORT.exists() and GAMMA_AGGREGATION_POLICY_DOC.exists():
            actions.append("Before any further broad Databento download, use `reports\\risk_first_data_audit.md`, `reports\\greeks_oi_enrichment_probe_report.md`, and `docs\\GAMMA_AGGREGATION_VALIDATION_POLICY.md` as the pre-purchase checkpoint: run a diagnostic gamma aggregation against the policy gates, choose targeted pre-break/high-VIX/major-regime coverage, or revise toward a higher-density strategy hypothesis; then re-run paid-cost/readiness audits and confirm actual provider usage remains below the stop threshold.")
        elif GREEKS_OI_ENRICHMENT_REPORT.exists():
            actions.append("Before any further broad Databento download, use `reports\\risk_first_data_audit.md` and `reports\\greeks_oi_enrichment_probe_report.md` as the pre-purchase checkpoint: define gamma aggregation/scaling validation, choose targeted pre-break/high-VIX/major-regime coverage, or revise toward a higher-density strategy hypothesis; then re-run paid-cost/readiness audits and confirm actual provider usage remains below the stop threshold.")
        else:
            actions.append("Before any further broad Databento download, use `reports\\risk_first_data_audit.md` and `reports\\greeks_oi_feasibility_audit.md` as the pre-purchase checkpoint: choose normalized quote enrichment for gamma-family research, targeted pre-break/high-VIX/major-regime coverage, or a revised higher-density strategy hypothesis; then re-run paid-cost/readiness audits and confirm actual provider usage remains below the stop threshold.")
    if not actions:
        actions.append("Proceed to the next locked experiment gate.")
    return actions


def _normalize_blocker(blocker: str) -> str:
    if blocker == "requires_minimum_trade_count_500":
        return "requires_mintrl_psr_sample_adequacy"
    return blocker


def _load_report_artifact(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    if path.is_dir():
        return _load_gdelt_capture_status_dir(path)
    if path.suffix.lower() in {".md", ".txt"}:
        return {"status": "pass", "text": path.read_text(encoding="utf-8")}
    return json.loads(path.read_text(encoding="utf-8"))


def _load_gdelt_capture_status_dir(path: Path) -> dict[str, Any]:
    status_counts: dict[str, int] = {}
    blockers: set[str] = set()
    file_count = 0
    for status_path in sorted(path.glob("*.json")):
        payload = json.loads(status_path.read_text(encoding="utf-8"))
        file_count += 1
        status = str(payload.get("status", "missing"))
        status_counts[status] = status_counts.get(status, 0) + 1
        for blocker in payload.get("blockers", []):
            blockers.add(str(blocker))
        if status != "captured":
            blockers.add(f"gdelt_capture_not_captured:{status_path.stem}")
    if file_count == 0:
        blockers.add("requires_gdelt_capture_status_files")
    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": sorted(blockers),
        "file_count": file_count,
        "status_counts": status_counts,
    }


def _has_any_env_scope(status: dict[str, bool]) -> bool:
    return any(status.values())


def _has_any_databento_env(environment: dict[str, dict[str, bool]]) -> bool:
    return any(_has_any_env_scope(environment[name]) for name in DATABENTO_API_KEY_ENVS)


def _env_status(
    name: str,
    process_env: dict[str, str],
    user_env_getter: Callable[[str], str | None],
    machine_env_getter: Callable[[str], str | None],
) -> dict[str, bool]:
    return {
        "process": bool(process_env.get(name)),
        "user": bool(user_env_getter(name)),
        "machine": bool(machine_env_getter(name)),
    }


def _get_user_env(name: str) -> str | None:
    if os.name != "nt":
        return None
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            value, _ = winreg.QueryValueEx(key, name)
            return str(value)
    except OSError:
        return None


def _get_machine_env(name: str) -> str | None:
    if os.name != "nt":
        return None
    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
        ) as key:
            value, _ = winreg.QueryValueEx(key, name)
            return str(value)
    except OSError:
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit Higanbana research readiness without live API calls.")
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    args = parser.parse_args(argv)

    result = audit_research_readiness()
    write_reports(result, args.json_output, args.report_output)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
