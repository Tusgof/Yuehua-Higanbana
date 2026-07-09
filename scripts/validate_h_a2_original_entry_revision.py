from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUMMARY_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_original_entry_revision_summary.json"


def validate_h_a2_original_entry_revision(summary_path: Path = DEFAULT_SUMMARY_PATH) -> dict[str, Any]:
    summary = _load_json(summary_path)
    blockers: list[str] = []

    if summary.get("schema_version") != "h_a2_original_entry_revision_v1":
        blockers.append("unsupported_schema_version")
    if summary.get("record_type") != "experiment_summary":
        blockers.append("record_type_must_be_experiment_summary")
    if summary.get("experiment_id") != "h_a2_original_entry_revision":
        blockers.append("experiment_id_must_match")
    if summary.get("hypothesis_id") != "H-A2":
        blockers.append("hypothesis_id_must_be_h_a2")
    if summary.get("evidence_tier") != "E1":
        blockers.append("evidence_tier_must_be_e1")
    if summary.get("status") != "complete":
        blockers.append("status_must_be_complete")
    if summary.get("conclusion") not in {"ผ่าน", "ไม่ผ่าน", "ยังสรุปไม่ได้", "เธเนเธฒเธ", "เนเธกเนเธเนเธฒเธ", "เธขเธฑเธเธชเธฃเธธเธเนเธกเนเนเธ”เน"}:
        blockers.append("conclusion_must_use_project_label")
    if summary.get("research_log_required") is not True:
        blockers.append("research_log_required_must_be_true")

    _validate_guardrails(summary, blockers)
    _validate_methodology(summary, blockers)
    _validate_required_checks(summary, blockers)

    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "summary_path": _relative(summary_path),
        "hypothesis_id": summary.get("hypothesis_id"),
        "evidence_tier": summary.get("evidence_tier"),
        "experiment_id": summary.get("experiment_id"),
        "decision": summary.get("hypothesis_decision", {}).get("decision"),
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
        "paper_trading_allowed",
        "operational_validation_allowed",
        "real_money_allowed",
        "exact_2022_orb_tested",
        "strategy_use_allowed",
    ]:
        if summary.get(field) is not False:
            blockers.append(f"{field}_must_be_false")


def _validate_methodology(summary: dict[str, Any], blockers: list[str]) -> None:
    methodology = summary.get("methodology", {})
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
        "original_0935_pnl_labeled_as_delayed_entry_pnl",
    ]:
        if methodology.get(field) is not False:
            blockers.append(f"{field}_must_be_false")
    if methodology.get("locked_threshold") != 0.001:
        blockers.append("locked_threshold_must_be_0_001")
    if methodology.get("candidate_decision_time_et") != "09:35:00":
        blockers.append("candidate_decision_time_must_be_0935")
    if "no_adverse_measured_15m_conflict" in methodology.get("used_features", []):
        blockers.append("fifteen_minute_conflict_must_not_be_used")
    if methodology.get("used_features") != ["clean_macro_vix_condition", "proxy_5m_followthrough"]:
        blockers.append("used_features_must_be_0935_known_only")
    if methodology.get("result_type") != "timestamp_clean_original_entry_context":
        blockers.append("result_type_must_be_timestamp_clean_original_entry_context")

    trial_policy = summary.get("trial_policy", {})
    for field in ["threshold_search_allowed", "threshold_search_used", "new_filter_search_used", "oos_tuning_used"]:
        if trial_policy.get(field) is not False:
            blockers.append(f"trial_{field}_must_be_false")
    if trial_policy.get("trial_count") != 0:
        blockers.append("trial_count_must_be_zero")
    search_log = trial_policy.get("search_log")
    if not search_log or not (PROJECT_ROOT / search_log).exists():
        blockers.append("search_log_missing_on_disk")
    if "no_new_threshold_search" not in str(trial_policy.get("dsr_status", "")):
        blockers.append("dsr_status_must_state_no_new_threshold_search")


def _validate_required_checks(summary: dict[str, Any], blockers: list[str]) -> None:
    timestamp = summary.get("original_entry_timestamp_cleanliness", {})
    if timestamp.get("all_features_known_by_decision_time") is not True:
        blockers.append("all_features_must_be_known_by_0935")
    if timestamp.get("timestamp_cleanliness_status") != "pass_for_original_0935_decision":
        blockers.append("timestamp_cleanliness_status_must_pass")

    forbidden = summary.get("forbidden_feature_exclusion", {})
    if forbidden.get("all_forbidden_features_excluded") is not True:
        blockers.append("all_forbidden_features_excluded_must_be_true")
    for field in ["fifteen_minute_conflict_component_used", "delayed_entry_component_used", "new_oos_selected_filter_used"]:
        if forbidden.get(field) is not False:
            blockers.append(f"forbidden_{field}_must_be_false")

    counts = summary.get("sample_counts", {})
    expected = {
        "baseline_train_non_risk_trade_days": 30,
        "retained_train_trade_days": 16,
        "skipped_train_trade_days": 14,
        "baseline_oos_non_risk_trade_days": 34,
        "retained_oos_trade_days": 14,
        "skipped_oos_trade_days": 20,
    }
    for key, value in expected.items():
        if counts.get(key) != value:
            blockers.append(f"unexpected_sample_count:{key}")

    recount = summary.get("original_entry_sample_recount", {})
    if recount.get("under_sampled_label") is not True:
        blockers.append("under_sampled_label_must_be_true")
    if recount.get("underpowered_label") is not True:
        blockers.append("underpowered_label_must_be_true")

    pnl = summary.get("original_entry_implementable_pnl_check", {})
    if pnl.get("comparison_status") != "directionally_useful_but_underpowered":
        blockers.append("pnl_comparison_must_be_directionally_useful_but_underpowered")
    if pnl.get("retained_avg_implementable_pnl") is None:
        blockers.append("retained_avg_implementable_pnl_required")
    if pnl.get("retained_minus_skipped_avg_implementable_pnl") is None:
        blockers.append("retained_minus_skipped_avg_implementable_pnl_required")

    risk = summary.get("risk_and_sample_adequacy_check", {})
    if risk.get("evidence_tier_cap") != "E1":
        blockers.append("evidence_tier_cap_must_be_e1")
    if risk.get("mintrl_psr_status") != "blocked_underpowered_e1_diagnostic":
        blockers.append("mintrl_psr_status_must_be_blocked_underpowered")

    decision = summary.get("hypothesis_decision", {})
    if decision.get("evidence_tier") != "E1":
        blockers.append("decision_evidence_tier_must_be_e1")
    if decision.get("e2_status") != "forbidden":
        blockers.append("e2_status_must_be_forbidden")
    if decision.get("research_log_requirement") != "research_log/031-higanbana-h-a2-original-entry-revision.md":
        blockers.append("research_log_requirement_must_be_031")

    tier_blockers = "\n".join(summary.get("tier_blockers", []))
    for phrase in ["E1", "Under-sampled", "No exact 2022-10", "No E2"]:
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
    parser = argparse.ArgumentParser(description="Validate H-A2 original-entry revision summary.")
    parser.add_argument("--summary-path", type=Path, default=DEFAULT_SUMMARY_PATH)
    args = parser.parse_args(argv)

    result = validate_h_a2_original_entry_revision(args.summary_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
