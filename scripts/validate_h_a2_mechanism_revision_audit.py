from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUMMARY_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_mechanism_revision_audit.json"
NORMAL_REPLAY_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_normal_control_exact_replay.json"
POST_STRESS_REPLAY_PATH = (
    PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_post_stress_normalization_control_exact_replay.json"
)
PREREG_PATH = PROJECT_ROOT / "experiments" / "h_a2_mechanism_revision_preregistration.json"
REPORT_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_mechanism_revision_audit.md"
SEARCH_LOG_PATH = (
    PROJECT_ROOT
    / "reports"
    / "diagnostics"
    / "search_logs"
    / "h_a2_mechanism_revision_audit_search_log.jsonl"
)


def validate_h_a2_mechanism_revision_audit(summary_path: Path = DEFAULT_SUMMARY_PATH) -> dict[str, Any]:
    summary = _load_json(summary_path)
    blockers: list[str] = []

    if summary.get("schema_version") != "h_a2_mechanism_revision_audit_v1":
        blockers.append("unsupported_schema_version")
    if summary.get("record_type") != "experiment_summary":
        blockers.append("record_type_must_be_experiment_summary")
    if summary.get("experiment_id") != "h_a2_mechanism_revision_audit":
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
    _validate_autopsy(summary, blockers)
    _validate_aggregate_findings(summary, blockers)
    _validate_rule_dimensions(summary, blockers)
    _validate_decision(summary, blockers)
    _validate_guardrails(summary, blockers)
    _validate_logs(summary, blockers)

    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "summary_path": _relative(summary_path),
        "experiment_id": summary.get("experiment_id"),
        "evidence_tier": summary.get("evidence_tier"),
        "decision": summary.get("decision", {}).get("selected_next_step"),
        "research_log_path": summary.get("research_log_path"),
        "paid_data_used": summary.get("guardrails", {}).get("paid_data_used"),
        "exact_replay_expansion_used": summary.get("guardrails", {}).get("exact_replay_expansion_used"),
        "paper_trading_allowed": summary.get("guardrails", {}).get("paper_trading_allowed"),
    }


def _validate_sources(summary: dict[str, Any], blockers: list[str]) -> None:
    for path in [PREREG_PATH, NORMAL_REPLAY_PATH, POST_STRESS_REPLAY_PATH, REPORT_PATH, SEARCH_LOG_PATH]:
        if not path.exists():
            blockers.append(f"required_source_missing:{_relative(path)}")
    if summary.get("source_preregistration") != _relative(PREREG_PATH):
        blockers.append("source_preregistration_must_match")
    prereg = _load_json(PREREG_PATH)
    diagnostic = prereg.get("planned_next_diagnostic", {})
    controls = summary.get("preregistration_controls_confirmed", {})
    if diagnostic.get("experiment_id") != "h_a2_mechanism_revision_audit":
        blockers.append("source_preregistration_wrong_next_diagnostic")
    if controls.get("planned_next_diagnostic") != "h_a2_mechanism_revision_audit":
        blockers.append("confirmed_planned_next_diagnostic_must_match")
    if controls.get("mode") != "local_no_paid_diagnostic":
        blockers.append("confirmed_mode_must_be_local_no_paid")
    for field in [
        "new_threshold_search_allowed",
        "oos_selected_filter_allowed",
        "paid_data_before_mechanism_audit_allowed",
    ]:
        if controls.get(field) is not False:
            blockers.append(f"{field}_must_be_false")


def _validate_autopsy(summary: dict[str, Any], blockers: list[str]) -> None:
    autopsy = summary.get("mechanism_autopsy", [])
    if len(autopsy) != 2:
        blockers.append("mechanism_autopsy_count_must_be_2")
        return
    sources = [_load_json(NORMAL_REPLAY_PATH), _load_json(POST_STRESS_REPLAY_PATH)]
    for item, source in zip(autopsy, sources, strict=True):
        candidate = source.get("candidate", {})
        pnl = source.get("pnl", {})
        mapping = source.get("selected_vertical", {}).get("mapping", {})
        expected = {
            "source_experiment": source.get("experiment_id"),
            "candidate_date": candidate.get("date"),
            "direction": candidate.get("direction"),
            "underlying_entry_close": candidate.get("underlying_entry_close"),
            "underlying_forced_close": candidate.get("underlying_forced_close"),
            "long_strike": mapping.get("long_strike"),
            "short_strike": mapping.get("short_strike"),
            "mid_pnl": pnl.get("mid_pnl"),
            "implementable_pnl": pnl.get("implementable_pnl"),
            "cost_drag_vs_mid": pnl.get("cost_drag_vs_mid"),
        }
        for key, value in expected.items():
            if item.get(key) != value:
                blockers.append(f"autopsy_source_mismatch:{candidate.get('date')}:{key}")
        if item.get("direction_signal_correct_to_forced_close") is not True:
            blockers.append(f"direction_signal_must_be_correct:{candidate.get('date')}")
        if item.get("long_strike_above_forced_close") is not True:
            blockers.append(f"long_strike_must_not_be_reached:{candidate.get('date')}")
        if item.get("implementable_pnl", 0) >= 0:
            blockers.append(f"implementable_pnl_must_be_negative:{candidate.get('date')}")
        if item.get("failure_mode") != "direction_correct_but_option_spread_lost_value_before_forced_close":
            blockers.append(f"failure_mode_must_match:{candidate.get('date')}")


def _validate_aggregate_findings(summary: dict[str, Any], blockers: list[str]) -> None:
    agg = summary.get("aggregate_findings", {})
    if agg.get("candidate_count") != 2:
        blockers.append("candidate_count_must_be_2")
    if agg.get("directionally_correct_underlying_count") != 2:
        blockers.append("directionally_correct_count_must_be_2")
    if agg.get("option_pnl_negative_count") != 2:
        blockers.append("option_pnl_negative_count_must_be_2")
    if agg.get("long_strike_not_reached_count") != 2:
        blockers.append("long_strike_not_reached_count_must_be_2")
    for field in ["direction_signal_not_sufficient", "strike_reachability_issue", "cost_drag_material"]:
        if agg.get(field) is not True:
            blockers.append(f"{field}_must_be_true")
    if agg.get("total_mid_pnl") != -50.0:
        blockers.append("total_mid_pnl_must_be_minus_50")
    if agg.get("total_implementable_pnl") != -59.12:
        blockers.append("total_implementable_pnl_must_be_minus_59_12")
    if agg.get("total_cost_drag_vs_mid") != 9.12:
        blockers.append("total_cost_drag_must_be_9_12")
    if agg.get("mintrl_psr_status") != "blocked_two_trade_underpowered":
        blockers.append("mintrl_psr_status_must_be_blocked_two_trade_underpowered")
    if agg.get("under_sampled") is not True or agg.get("underpowered") is not True:
        blockers.append("aggregate_must_be_under_sampled_and_underpowered")


def _validate_rule_dimensions(summary: dict[str, Any], blockers: list[str]) -> None:
    dimensions = {item.get("dimension"): item for item in summary.get("rule_dimension_assessment", [])}
    for name in ["post_entry_followthrough", "strike_reachability", "cost_drag", "regime_context", "selection_risk"]:
        if name not in dimensions:
            blockers.append(f"missing_rule_dimension:{name}")
    for name in ["post_entry_followthrough", "strike_reachability", "cost_drag"]:
        if dimensions.get(name, {}).get("assessment") != "logically_justified_before_parameter_search":
            blockers.append(f"dimension_must_be_logically_justified:{name}")
    if dimensions.get("regime_context", {}).get("assessment") != "supporting_context_not_sufficient_alone":
        blockers.append("regime_context_must_be_supporting_not_sufficient")
    if dimensions.get("selection_risk", {}).get("assessment") != "must_control_before_any_new_rule":
        blockers.append("selection_risk_must_control_before_new_rule")


def _validate_decision(summary: dict[str, Any], blockers: list[str]) -> None:
    decision = summary.get("decision", {})
    if decision.get("selected_next_step") != "preregister_train_only_revised_rule":
        blockers.append("selected_next_step_must_preregister_train_only_revised_rule")
    if decision.get("decision_label") != "ยังสรุปไม่ได้":
        blockers.append("decision_label_must_be_inconclusive")
    for phrase in ["current locked condition", "train-only revised-rule", "cost-adjusted magnitude", "strike reachability"]:
        if phrase not in decision.get("reason", ""):
            blockers.append(f"decision_reason_missing:{phrase}")
    if "consume the approved Databento budget" not in decision.get("why_not_more_data_now", ""):
        blockers.append("why_not_more_data_now_must_reference_budget")
    if decision.get("next_required_artifact") != "h_a2_breakeven_aware_rule_preregistration":
        blockers.append("next_required_artifact_must_match")
    if "train-only revised rule" not in summary.get("next_safe_action", ""):
        blockers.append("next_safe_action_must_name_train_only_revised_rule")


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
        "threshold_search_used",
        "new_oos_filter_selected",
        "strategy_use_allowed",
        "paper_trading_allowed",
        "operational_validation_allowed",
        "real_money_allowed",
    ]:
        if guardrails.get(field) is not False:
            blockers.append(f"{field}_must_be_false")
    trial_policy = summary.get("trial_policy", {})
    if trial_policy.get("trial_count") != 1:
        blockers.append("trial_count_must_be_1")
    if trial_policy.get("dsr_status") != "not_applicable_no_parameter_search":
        blockers.append("dsr_status_must_be_not_applicable")
    if trial_policy.get("threshold_0_001_status") != "locked_as_prior_diagnostic_reference_only":
        blockers.append("threshold_status_must_be_locked_reference")
    forbidden = "\n".join(summary.get("forbidden_claims", []))
    for phrase in ["edge is validated", "fully falsified", "paid data", "exact replay", "0.001", "OOS filter", "paper trading", "E2"]:
        if phrase not in forbidden:
            blockers.append(f"forbidden_claim_missing:{phrase}")


def _validate_logs(summary: dict[str, Any], blockers: list[str]) -> None:
    if summary.get("research_log_required") is not True:
        blockers.append("research_log_required_must_be_true")
    if summary.get("research_log_path") != "research_log/039-higanbana-h-a2-mechanism-revision-audit.md":
        blockers.append("research_log_path_must_be_039")
    if summary.get("research_log_slug") != "higanbana-h-a2-mechanism-revision-audit":
        blockers.append("research_log_slug_must_match")
    if SEARCH_LOG_PATH.exists():
        rows = [json.loads(line) for line in SEARCH_LOG_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
        if len(rows) != 1:
            blockers.append("search_log_must_have_one_row")
        elif rows[0].get("parameter_search_used") is not False:
            blockers.append("search_log_parameter_search_must_be_false")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate H-A2 mechanism revision audit.")
    parser.add_argument("--summary-path", type=Path, default=DEFAULT_SUMMARY_PATH)
    args = parser.parse_args(argv)

    result = validate_h_a2_mechanism_revision_audit(args.summary_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
