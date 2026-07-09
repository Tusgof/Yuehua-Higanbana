from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUMMARY_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_revised_opening_followthrough_condition_summary.json"


def validate_h_a2_revised_opening_followthrough_condition(summary_path: Path = DEFAULT_SUMMARY_PATH) -> dict[str, Any]:
    summary = _load_json(summary_path)
    blockers: list[str] = []

    if summary.get("schema_version") != "h_a2_revised_opening_followthrough_condition_v1":
        blockers.append("unsupported_schema_version")
    if summary.get("record_type") != "experiment_summary":
        blockers.append("record_type_must_be_experiment_summary")
    if summary.get("experiment_id") != "h_a2_revised_opening_followthrough_condition":
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
    _validate_trials_and_threshold(summary, blockers)
    _validate_counts_and_decision(summary, blockers)

    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "summary_path": _relative(summary_path),
        "hypothesis_id": summary.get("hypothesis_id"),
        "evidence_tier": summary.get("evidence_tier"),
        "experiment_id": summary.get("experiment_id"),
        "decision": summary.get("decision_rule_application", {}).get("decision"),
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
    for field in ["local_artifacts_only", "chronological_split_required", "thresholds_fit_only_on_train"]:
        if methodology.get(field) is not True:
            blockers.append(f"{field}_must_be_true")
    if methodology.get("random_split_used") is not False:
        blockers.append("random_split_used_must_be_false")
    if methodology.get("oos_tuning_used") is not False:
        blockers.append("oos_tuning_used_must_be_false")


def _validate_trials_and_threshold(summary: dict[str, Any], blockers: list[str]) -> None:
    trials = summary.get("trial_policy", {})
    if trials.get("trial_count") != 7:
        blockers.append("trial_count_must_be_7")
    if trials.get("all_trials_recorded") is not True:
        blockers.append("all_trials_recorded_must_be_true")
    search_log = trials.get("search_log")
    if not search_log:
        blockers.append("missing_search_log")
    elif not (PROJECT_ROOT / search_log).exists():
        blockers.append("search_log_missing_on_disk")
    if "not_acceptance" not in str(trials.get("dsr_status", "")):
        blockers.append("dsr_status_must_block_acceptance")

    lock = summary.get("threshold_lock", {})
    if lock.get("status") != "locked":
        blockers.append("threshold_must_be_locked")
    if lock.get("oos_used_for_selection") is not False:
        blockers.append("oos_used_for_selection_must_be_false")
    if lock.get("locked_threshold") is None:
        blockers.append("locked_threshold_required")
    if not lock.get("selected_trial_id"):
        blockers.append("selected_trial_id_required")


def _validate_counts_and_decision(summary: dict[str, Any], blockers: list[str]) -> None:
    counts = summary.get("sample_counts", {})
    expected_counts = {
        "daily_rows": 463,
        "baseline_train_non_risk_trade_days": 30,
        "baseline_oos_non_risk_trade_days": 34,
    }
    for key, expected in expected_counts.items():
        if counts.get(key) != expected:
            blockers.append(f"unexpected_sample_count:{key}")
    if counts.get("revised_train_trade_days", 0) <= 0:
        blockers.append("revised_train_trade_days_must_be_positive")
    if counts.get("revised_oos_trade_days", 0) <= 0:
        blockers.append("revised_oos_trade_days_must_be_positive")
    if counts.get("skipped_oos_trade_days", 0) <= 0:
        blockers.append("skipped_oos_trade_days_must_be_positive")

    for section in [
        "residual_loss_reduction_check",
        "chronological_oos_holdout_check",
        "mechanism_consistency_check",
        "big_day_dependency_context",
        "decision_rule_application",
    ]:
        if summary.get(section, {}).get("status") not in {"complete", "diagnostic_underpowered"}:
            blockers.append(f"{section}_must_be_complete_or_diagnostic")

    holdout = summary.get("chronological_oos_holdout_check", {})
    if holdout.get("threshold_locked_before_oos") is not True:
        blockers.append("threshold_locked_before_oos_must_be_true")
    if holdout.get("oos_tuning_used") is not False:
        blockers.append("holdout_oos_tuning_used_must_be_false")

    decision = summary.get("decision_rule_application", {})
    if decision.get("evidence_tier") != "E1":
        blockers.append("decision_evidence_tier_must_be_e1")
    if decision.get("oos_tuning_used") is not False:
        blockers.append("decision_oos_tuning_used_must_be_false")
    if decision.get("decision") not in {
        "prioritize_exact_replay_when_external_bar_blocker_clears",
        "continue_local_revised_condition_research_underpowered",
        "revise_or_park_h_a2_before_exact_replay",
        "park_revised_condition_pending_new_train_rule",
    }:
        blockers.append("unsupported_decision")

    tier_blockers = "\n".join(summary.get("tier_blockers", []))
    for phrase in ["E1 diagnostic", "Under-sampled", "No exact 2022-10", "No E2"]:
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
    parser = argparse.ArgumentParser(description="Validate H-A2 revised opening-followthrough condition summary.")
    parser.add_argument("--summary-path", type=Path, default=DEFAULT_SUMMARY_PATH)
    args = parser.parse_args(argv)

    result = validate_h_a2_revised_opening_followthrough_condition(args.summary_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
