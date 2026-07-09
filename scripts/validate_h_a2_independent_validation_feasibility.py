from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUMMARY_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_independent_validation_feasibility.json"


def validate_h_a2_independent_validation_feasibility(summary_path: Path = DEFAULT_SUMMARY_PATH) -> dict[str, Any]:
    summary = _load_json(summary_path)
    blockers: list[str] = []

    if summary.get("schema_version") != "h_a2_independent_validation_feasibility_v1":
        blockers.append("unsupported_schema_version")
    if summary.get("record_type") != "experiment_summary":
        blockers.append("record_type_must_be_experiment_summary")
    if summary.get("experiment_id") != "h_a2_independent_validation_feasibility":
        blockers.append("experiment_id_must_match")
    if summary.get("hypothesis_id") != "H-A2":
        blockers.append("hypothesis_id_must_be_h_a2")
    if summary.get("status") != "complete":
        blockers.append("status_must_be_complete")
    if summary.get("evidence_tier") != "E1":
        blockers.append("evidence_tier_must_be_e1")
    if summary.get("conclusion") != "ยังสรุปไม่ได้":
        blockers.append("conclusion_must_be_inconclusive")

    _validate_guardrails(summary, blockers)
    _validate_methodology(summary, blockers)
    _validate_required_sections(summary, blockers)
    _validate_decision_and_claims(summary, blockers)

    gap = summary.get("current_gap_inventory", {})
    decision = summary.get("next_action_selection", {})
    no_paid = summary.get("no_paid_source_inventory", {})
    paid = summary.get("paid_data_decision_tree", {})
    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "summary_path": _relative(summary_path),
        "experiment_id": summary.get("experiment_id"),
        "hypothesis_id": summary.get("hypothesis_id"),
        "evidence_tier": summary.get("evidence_tier"),
        "retained_oos_trade_days": gap.get("retained_oos_trade_days"),
        "current_total_closed_trades": gap.get("current_total_closed_trades"),
        "no_paid_feasibility_status": no_paid.get("no_paid_feasibility_status"),
        "decision": decision.get("decision"),
        "remaining_before_stop_usd": paid.get("cost_guard_preconditions", {}).get("current_remaining_before_stop_usd"),
        "research_log_required": summary.get("research_log_required"),
    }


def _validate_guardrails(summary: dict[str, Any], blockers: list[str]) -> None:
    for field in [
        "network_used",
        "paid_data_used",
        "live_cost_estimate_used",
        "new_provider_used",
        "broker_request_used",
        "ibkr_request_used",
        "gdelt_live_retry_used",
        "llm_call_used",
        "exact_replay_used",
        "paper_trading_allowed",
        "operational_validation_allowed",
        "real_money_allowed",
        "strategy_use_allowed",
    ]:
        if summary.get(field) is not False:
            blockers.append(f"{field}_must_be_false")


def _validate_methodology(summary: dict[str, Any], blockers: list[str]) -> None:
    methodology = summary.get("methodology", {})
    if methodology.get("candidate_decision_time_et") != "09:35:00":
        blockers.append("candidate_decision_time_must_be_0935")
    if methodology.get("locked_threshold") != 0.001:
        blockers.append("locked_threshold_must_be_0_001")
    if methodology.get("used_features") != ["clean_macro_vix_condition", "proxy_5m_followthrough"]:
        blockers.append("used_features_must_match_locked_signal")
    for field in ["local_artifacts_only", "chronological_split_required"]:
        if methodology.get(field) is not True:
            blockers.append(f"{field}_must_be_true")
    for field in [
        "random_split_used",
        "oos_tuning_used",
        "threshold_search_used",
        "new_oos_selected_filter_used",
        "fifteen_minute_conflict_component_used",
        "delayed_entry_component_used",
    ]:
        if methodology.get(field) is not False:
            blockers.append(f"{field}_must_be_false")


def _validate_required_sections(summary: dict[str, Any], blockers: list[str]) -> None:
    for key in [
        "current_gap_inventory",
        "validation_target_definition",
        "no_paid_source_inventory",
        "paid_data_decision_tree",
        "next_action_selection",
    ]:
        if summary.get(key, {}).get("status") != "complete":
            blockers.append(f"{key}_status_must_be_complete")

    gap = summary.get("current_gap_inventory", {})
    if gap.get("retained_oos_trade_days") != 14:
        blockers.append("retained_oos_trade_days_must_be_14")
    if "vix_above_25" not in gap.get("missing_regime_buckets", []):
        blockers.append("missing_regime_buckets_must_include_vix_above_25")
    for blocker in [
        "retained_oos_trade_days_below_independent_validation_need",
        "high_vix_retained_bucket_missing",
        "mintrl_psr_not_computed_for_acceptance",
    ]:
        if blocker not in gap.get("claim_upgrade_blockers", []):
            blockers.append(f"missing_claim_upgrade_blocker:{blocker}")

    no_paid = summary.get("no_paid_source_inventory", {})
    if no_paid.get("no_paid_feasibility_status") != "no_paid_can_plan_but_cannot_validate_edge":
        blockers.append("no_paid_feasibility_status_unexpected")
    if no_paid.get("usable_no_paid_dates") != []:
        blockers.append("usable_no_paid_dates_must_be_empty")

    paid = summary.get("paid_data_decision_tree", {})
    preconditions = paid.get("cost_guard_preconditions", {})
    if preconditions.get("live_cost_estimate_allowed_by_this_run") is not False:
        blockers.append("live_cost_estimate_allowed_by_this_run_must_be_false")
    if preconditions.get("paid_download_allowed_by_this_run") is not False:
        blockers.append("paid_download_allowed_by_this_run_must_be_false")
    if preconditions.get("requires_new_preregistration_before_cost_or_download") is not True:
        blockers.append("requires_new_preregistration_before_cost_or_download_must_be_true")


def _validate_decision_and_claims(summary: dict[str, Any], blockers: list[str]) -> None:
    decision = summary.get("next_action_selection", {})
    if decision.get("decision") not in {
        "draft_paid_cost_estimate_plan_only",
        "pause_paid_path_run_no_paid_gap_report_or_wait_for_topup",
    }:
        blockers.append("decision_must_be_valid_h_a2_independent_validation_next_action")
    if decision.get("evidence_tier_cap") != "E1":
        blockers.append("evidence_tier_cap_must_be_e1")
    if decision.get("research_log_requirement") != "research_log/033-higanbana-h-a2-independent-validation-feasibility.md":
        blockers.append("research_log_requirement_must_be_033")
    if summary.get("research_log_required") is not True:
        blockers.append("research_log_required_must_be_true")

    trial = summary.get("trial_policy", {})
    if trial.get("trial_count") != 0:
        blockers.append("trial_count_must_be_zero")
    for field in ["threshold_search_used", "new_filter_search_used", "oos_tuning_used"]:
        if trial.get(field) is not False:
            blockers.append(f"trial_policy_{field}_must_be_false")

    forbidden = "\n".join(summary.get("forbidden_claims", []))
    for phrase in ["edge is validated", "E2", "paper trading", "paid data", "live Databento estimates", "IBKR", "LLMs", "GDELT"]:
        if phrase not in forbidden:
            blockers.append(f"missing_forbidden_claim_phrase:{phrase}")

    tier_blockers = "\n".join(summary.get("tier_blockers", []))
    for phrase in ["No independent validation PnL days added", "No high-VIX retained validation coverage yet", "No E2 acceptance claim"]:
        if phrase not in tier_blockers:
            blockers.append(f"missing_tier_blocker_phrase:{phrase}")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate H-A2 independent validation feasibility diagnostic.")
    parser.add_argument("--summary-path", type=Path, default=DEFAULT_SUMMARY_PATH)
    args = parser.parse_args(argv)

    result = validate_h_a2_independent_validation_feasibility(args.summary_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
