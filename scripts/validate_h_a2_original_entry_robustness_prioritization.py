from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUMMARY_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_original_entry_robustness_prioritization_summary.json"


def validate_h_a2_original_entry_robustness_prioritization(
    summary_path: Path = DEFAULT_SUMMARY_PATH,
) -> dict[str, Any]:
    summary = _load_json(summary_path)
    blockers: list[str] = []

    if summary.get("schema_version") != "h_a2_original_entry_robustness_prioritization_v1":
        blockers.append("unsupported_schema_version")
    if summary.get("record_type") != "experiment_summary":
        blockers.append("record_type_must_be_experiment_summary")
    if summary.get("experiment_id") != "h_a2_original_entry_robustness_prioritization":
        blockers.append("experiment_id_must_match")
    if summary.get("hypothesis_id") != "H-A2":
        blockers.append("hypothesis_id_must_be_h_a2")
    if summary.get("evidence_tier") != "E1":
        blockers.append("evidence_tier_must_be_e1")
    if summary.get("status") != "complete":
        blockers.append("status_must_be_complete")
    if summary.get("conclusion") not in {"ยังสรุปไม่ได้", "เธขเธฑเธเธชเธฃเธธเธเนเธกเนเนเธ”เน"}:
        blockers.append("conclusion_must_be_inconclusive")

    _validate_guardrails(summary, blockers)
    _validate_methodology(summary, blockers)
    _validate_checks(summary, blockers)
    _validate_decision_and_log(summary, blockers)

    decision = summary.get("validation_priority_decision", {})
    counts = summary.get("sample_counts", {})
    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "summary_path": _relative(summary_path),
        "experiment_id": summary.get("experiment_id"),
        "hypothesis_id": summary.get("hypothesis_id"),
        "evidence_tier": summary.get("evidence_tier"),
        "decision": decision.get("decision"),
        "retained_oos_trade_days": counts.get("retained_oos_trade_days"),
        "research_log_required": summary.get("research_log_required"),
        "next_safe_action": summary.get("next_safe_action"),
    }


def _validate_guardrails(summary: dict[str, Any], blockers: list[str]) -> None:
    for field in [
        "network_used",
        "paid_data_used",
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
        blockers.append("used_features_must_be_h_a2_32_features")
    for field in [
        "local_artifacts_only",
        "chronological_split_required",
    ]:
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


def _validate_checks(summary: dict[str, Any], blockers: list[str]) -> None:
    counts = summary.get("sample_counts", {})
    expected_counts = {
        "baseline_oos_non_risk_trade_days": 34,
        "retained_oos_trade_days": 14,
        "skipped_oos_trade_days": 20,
        "retained_train_trade_days": 16,
    }
    for key, expected in expected_counts.items():
        if counts.get(key) != expected:
            blockers.append(f"{key}_must_be_{expected}")

    rule = summary.get("source_rule_integrity", {})
    if rule.get("status") != "pass" or rule.get("rule_integrity_status") != "pass_preserved_h_a2_32_rule":
        blockers.append("source_rule_integrity_must_pass")

    big_day = summary.get("leave_one_and_big_day_dependency", {})
    if big_day.get("big_day_dependency_status") != "pass_directional_but_underpowered":
        blockers.append("big_day_dependency_status_must_be_directional_underpowered_pass")
    if big_day.get("leave_one_out_min_avg_pnl") is None or big_day.get("leave_one_out_min_avg_pnl") <= 0:
        blockers.append("leave_one_out_min_avg_pnl_must_be_positive")

    concentration = summary.get("regime_and_calendar_concentration", {})
    if concentration.get("concentration_status") != "concentrated_underpowered":
        blockers.append("concentration_status_must_be_concentrated_underpowered")
    if "vix_above_25" not in concentration.get("empty_critical_buckets", []):
        blockers.append("must_disclose_missing_high_vix_retained_bucket")

    skip = summary.get("skip_cost_tradeoff", {})
    if skip.get("skip_cost_status") != "directionally_useful_but_sample_reducing":
        blockers.append("skip_cost_status_must_be_directionally_useful_but_sample_reducing")
    if skip.get("retained_minus_skipped_avg_pnl") != 106.0:
        blockers.append("retained_minus_skipped_avg_pnl_must_match_h_a2_32")


def _validate_decision_and_log(summary: dict[str, Any], blockers: list[str]) -> None:
    decision = summary.get("validation_priority_decision", {})
    if decision.get("decision") != "prioritize_independent_validation_plan_under_e1":
        blockers.append("decision_must_prioritize_independent_validation_plan_under_e1")
    if decision.get("evidence_tier_cap") != "E1":
        blockers.append("evidence_tier_cap_must_be_e1")
    labels = set(decision.get("sample_adequacy_labels", []))
    if not {"under-sampled", "underpowered"}.issubset(labels):
        blockers.append("sample_adequacy_labels_must_include_under_sampled_and_underpowered")
    if summary.get("research_log_required") is not True:
        blockers.append("research_log_required_must_be_true")
    if summary.get("research_log_slug") != "higanbana-h-a2-original-entry-robustness-prioritization":
        blockers.append("research_log_slug_must_match_032_topic")
    if "E2 acceptance claim" not in "\n".join(summary.get("tier_blockers", [])):
        blockers.append("tier_blockers_must_forbid_e2")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate H-A2 original-entry robustness/prioritization output.")
    parser.add_argument("--summary-path", type=Path, default=DEFAULT_SUMMARY_PATH)
    args = parser.parse_args(argv)

    result = validate_h_a2_original_entry_robustness_prioritization(args.summary_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
