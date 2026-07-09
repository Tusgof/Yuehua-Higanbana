from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUMMARY_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_breakeven_aware_rule_train_diagnostic.json"
PREREG_PATH = PROJECT_ROOT / "experiments" / "h_a2_breakeven_aware_rule_preregistration.json"
REPORT_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_breakeven_aware_rule_train_diagnostic.md"
SEARCH_LOG_PATH = (
    PROJECT_ROOT
    / "reports"
    / "diagnostics"
    / "search_logs"
    / "h_a2_breakeven_aware_rule_train_diagnostic_search_log.jsonl"
)


def validate_h_a2_breakeven_aware_rule_train_diagnostic(
    summary_path: Path = DEFAULT_SUMMARY_PATH,
) -> dict[str, Any]:
    summary = _load_json(summary_path)
    blockers: list[str] = []

    if summary.get("schema_version") != "h_a2_breakeven_aware_rule_train_diagnostic_v1":
        blockers.append("unsupported_schema_version")
    if summary.get("record_type") != "experiment_summary":
        blockers.append("record_type_must_be_experiment_summary")
    if summary.get("experiment_id") != "h_a2_breakeven_aware_rule_train_diagnostic":
        blockers.append("experiment_id_must_match")
    if summary.get("hypothesis_id") != "H-A2":
        blockers.append("hypothesis_id_must_be_h_a2")
    if summary.get("status") != "complete":
        blockers.append("status_must_be_complete")
    if summary.get("evidence_tier") != "E1":
        blockers.append("evidence_tier_must_be_e1")
    if summary.get("conclusion") != "ยังสรุปไม่ได้":
        blockers.append("conclusion_must_be_inconclusive")

    _validate_sources(summary, blockers)
    _validate_guardrails(summary, blockers)
    _validate_feature_audit(summary, blockers)
    _validate_target(summary, blockers)
    _validate_trials(summary, blockers)
    _validate_decision(summary, blockers)
    _validate_logs(summary, blockers)

    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "summary_path": _relative(summary_path),
        "experiment_id": summary.get("experiment_id"),
        "evidence_tier": summary.get("evidence_tier"),
        "decision": summary.get("decision", {}).get("decision"),
        "next_safe_action": summary.get("next_safe_action"),
        "paid_data_used": summary.get("guardrails", {}).get("paid_data_used"),
        "paper_trading_allowed": summary.get("guardrails", {}).get("paper_trading_allowed"),
    }


def _validate_sources(summary: dict[str, Any], blockers: list[str]) -> None:
    for path in [PREREG_PATH, REPORT_PATH, SEARCH_LOG_PATH]:
        if not path.exists():
            blockers.append(f"required_source_missing:{_relative(path)}")
    prereg = _load_json(PREREG_PATH)
    planned = prereg.get("planned_next_diagnostic", {})
    if planned.get("experiment_id") != "h_a2_breakeven_aware_rule_train_diagnostic":
        blockers.append("preregistration_must_point_to_this_diagnostic")
    if summary.get("source_preregistration") != _relative(PREREG_PATH):
        blockers.append("source_preregistration_must_match")
    if "reports/experiments/h_a2_lower_resolution_proxy_summary.json" not in summary.get("source_artifacts", []):
        blockers.append("daily_source_artifact_must_be_recorded")
    if "reports/diagnostics/h_a2_mechanism_revision_audit.json" not in summary.get("source_artifacts", []):
        blockers.append("mechanism_audit_artifact_must_be_recorded")


def _validate_guardrails(summary: dict[str, Any], blockers: list[str]) -> None:
    guardrails = summary.get("guardrails", {})
    for field in [
        "network_used",
        "paid_data_used",
        "new_provider_used",
        "broker_request_used",
        "ibkr_request_used",
        "gdelt_live_retry_used",
        "llm_call_used",
        "exact_replay_expansion_used",
        "oos_filter_selection_used",
        "oos_tuning_used",
        "paper_trading_allowed",
        "operational_validation_allowed",
        "real_money_allowed",
        "strategy_use_allowed",
    ]:
        if guardrails.get(field) is not False:
            blockers.append(f"{field}_must_be_false")
    methodology = summary.get("methodology", {})
    if methodology.get("mode") != "local_no_paid_train_only_diagnostic":
        blockers.append("mode_must_be_local_no_paid_train_only")
    if methodology.get("oos_rows_used_for_rule_selection") is not False:
        blockers.append("oos_rows_used_for_rule_selection_must_be_false")
    if methodology.get("true_breakeven_rule_locked") is not False:
        blockers.append("true_breakeven_rule_locked_must_be_false")


def _validate_feature_audit(summary: dict[str, Any], blockers: list[str]) -> None:
    audit = summary.get("decision_time_feature_audit", {})
    if audit.get("status") != "blocked_true_breakeven_rule_lock":
        blockers.append("feature_audit_status_must_block_true_rule_lock")
    if audit.get("can_lock_true_breakeven_aware_rule_from_current_artifacts") is not False:
        blockers.append("must_not_lock_true_rule_from_current_artifacts")
    if audit.get("can_run_surrogate_train_trials") is not True:
        blockers.append("surrogate_train_trials_must_be_available")
    missing = set(audit.get("missing_fields_for_true_rule", []))
    required_missing = {
        "train_distribution_nearest_discrete_long_strike",
        "train_distribution_entry_implementable_debit",
        "train_distribution_entry_bid_ask_width",
        "train_distribution_cost_adjusted_strike_reachability_target",
    }
    for field in sorted(required_missing - missing):
        blockers.append(f"missing_required_missing_field:{field}")


def _validate_target(summary: dict[str, Any], blockers: list[str]) -> None:
    target = summary.get("cost_adjusted_strike_reachability_target", {})
    if target.get("status") != "defined_but_not_computable_for_train_distribution":
        blockers.append("target_status_must_be_defined_but_not_train_computable")
    if target.get("train_distribution_target_available") is not False:
        blockers.append("train_distribution_target_available_must_be_false")
    cases = target.get("exact_replay_target_cases", [])
    if len(cases) != 2:
        blockers.append("exact_replay_target_cases_must_be_2")
    if target.get("exact_replay_target_reached_count") != 0:
        blockers.append("exact_replay_target_reached_count_must_be_0")
    for case in cases:
        if case.get("target_reached") is not False:
            blockers.append(f"target_must_not_be_reached:{case.get('candidate_date')}")
        if case.get("implementable_pnl", 0) >= 0:
            blockers.append(f"case_implementable_pnl_must_be_negative:{case.get('candidate_date')}")


def _validate_trials(summary: dict[str, Any], blockers: list[str]) -> None:
    trials = summary.get("train_only_candidate_rule_trials", [])
    if len(trials) < 2:
        blockers.append("must_record_multiple_train_trials")
    for trial in trials:
        if trial.get("surrogate_only") is not True:
            blockers.append(f"trial_must_be_surrogate_only:{trial.get('trial_id')}")
        if trial.get("uses_true_breakeven_inputs") is not False:
            blockers.append(f"trial_must_not_use_true_breakeven_inputs:{trial.get('trial_id')}")
        if trial.get("selected_for_trading") is not False:
            blockers.append(f"trial_must_not_be_selected_for_trading:{trial.get('trial_id')}")
    policy = summary.get("selection_risk_control", {})
    if policy.get("trial_count") != len(trials):
        blockers.append("trial_count_must_equal_trials")
    if policy.get("all_trials_recorded") is not True:
        blockers.append("all_trials_recorded_must_be_true")
    if policy.get("best_trial_selected_for_trading") is not False:
        blockers.append("best_trial_selected_for_trading_must_be_false")
    if policy.get("dsr_status") != "blocked_no_acceptance_selection":
        blockers.append("dsr_status_must_be_blocked_no_acceptance_selection")


def _validate_decision(summary: dict[str, Any], blockers: list[str]) -> None:
    decision = summary.get("decision", {})
    if decision.get("decision") != "write_targeted_data_regime_expansion_plan":
        blockers.append("decision_must_write_targeted_data_regime_expansion_plan")
    if decision.get("paid_data_approved") is not False:
        blockers.append("paid_data_approved_must_be_false")
    if decision.get("paper_trading_allowed") is not False:
        blockers.append("paper_trading_allowed_must_be_false")
    next_safe = decision.get("next_safe_action", "")
    for phrase in ["H-A2.63", "targeted data/regime expansion plan", "entry strike mapping", "MinTRL/PSR"]:
        if phrase not in next_safe:
            blockers.append(f"next_safe_action_missing:{phrase}")
    forbidden = "\n".join(summary.get("forbidden_claims", []))
    for phrase in ["edge is validated", "selected for trading", "E2", "paper trading", "OOS tuning", "broad calendar data buying"]:
        if phrase not in forbidden:
            blockers.append(f"forbidden_claim_missing:{phrase}")


def _validate_logs(summary: dict[str, Any], blockers: list[str]) -> None:
    if summary.get("research_log_required") is not True:
        blockers.append("research_log_required_must_be_true")
    if summary.get("research_log_slug") != "higanbana-h-a2-breakeven-aware-train-diagnostic":
        blockers.append("research_log_slug_must_match")
    if SEARCH_LOG_PATH.exists():
        rows = [json.loads(line) for line in SEARCH_LOG_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
        if len(rows) != len(summary.get("train_only_candidate_rule_trials", [])):
            blockers.append("search_log_row_count_must_equal_trials")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate H-A2 breakeven-aware train diagnostic.")
    parser.add_argument("--summary-path", type=Path, default=DEFAULT_SUMMARY_PATH)
    args = parser.parse_args(argv)

    result = validate_h_a2_breakeven_aware_rule_train_diagnostic(args.summary_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
