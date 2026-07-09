from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUMMARY_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_residual_adverse_day_analysis.json"


def validate_h_a2_residual_adverse_day_analysis(summary_path: Path = DEFAULT_SUMMARY_PATH) -> dict[str, Any]:
    summary = _load_json(summary_path)
    blockers: list[str] = []

    if summary.get("schema_version") != "h_a2_residual_adverse_day_analysis_v1":
        blockers.append("unsupported_schema_version")
    if summary.get("record_type") != "experiment_summary":
        blockers.append("record_type_must_be_experiment_summary")
    if summary.get("experiment_id") != "h_a2_residual_adverse_day_analysis":
        blockers.append("experiment_id_must_match")
    if summary.get("hypothesis_id") != "H-A2":
        blockers.append("hypothesis_id_must_be_h_a2")
    if summary.get("evidence_tier") != "E1":
        blockers.append("evidence_tier_must_be_e1")
    if summary.get("status") != "complete":
        blockers.append("status_must_be_complete")
    if summary.get("conclusion") not in {"ผ่าน", "ไม่ผ่าน", "ยังสรุปไม่ได้"}:
        blockers.append("conclusion_must_use_project_label")
    if summary.get("research_log_required") is not True:
        blockers.append("research_log_required_must_be_true")

    _validate_guardrails(summary, blockers)
    _validate_methodology_and_trials(summary, blockers)
    _validate_counts_profiles_and_decision(summary, blockers)

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


def _validate_methodology_and_trials(summary: dict[str, Any], blockers: list[str]) -> None:
    methodology = summary.get("methodology", {})
    for field in ["local_artifacts_only", "chronological_split_required", "no_new_filter_selected"]:
        if methodology.get(field) is not True:
            blockers.append(f"{field}_must_be_true")
    if methodology.get("random_split_used") is not False:
        blockers.append("random_split_used_must_be_false")
    if methodology.get("oos_tuning_used") is not False:
        blockers.append("oos_tuning_used_must_be_false")

    trials = summary.get("trial_policy", {})
    if trials.get("trial_count") != 4:
        blockers.append("trial_count_must_be_4")
    if trials.get("all_trials_recorded") is not True:
        blockers.append("all_trials_recorded_must_be_true")
    search_log = trials.get("search_log")
    if not search_log:
        blockers.append("missing_search_log")
    elif not (PROJECT_ROOT / search_log).exists():
        blockers.append("search_log_missing_on_disk")
    if "not_acceptance" not in str(trials.get("dsr_status", "")):
        blockers.append("dsr_status_must_block_acceptance")


def _validate_counts_profiles_and_decision(summary: dict[str, Any], blockers: list[str]) -> None:
    sample_counts = summary.get("sample_counts", {})
    expected_counts = {
        "daily_rows": 463,
        "trade_days": 90,
        "non_risk_trade_days": 64,
        "macro_only_trade_days": 26,
    }
    for key, expected in expected_counts.items():
        if sample_counts.get(key) != expected:
            blockers.append(f"unexpected_sample_count:{key}")
    if sample_counts.get("non_risk_losing_trade_days", 0) <= 0:
        blockers.append("non_risk_losing_trade_days_must_be_positive")
    if sample_counts.get("macro_only_losing_trade_days", 0) <= 0:
        blockers.append("macro_only_losing_trade_days_must_be_positive")

    for section in ["residual_loss_bucket_profile", "macro_only_loss_profile", "non_risk_failure_mode_check"]:
        profile = summary.get(section, {})
        if profile.get("status") != "complete":
            blockers.append(f"{section}_must_be_complete")

    decision = summary.get("decision_rule_application", {})
    if decision.get("status") != "complete":
        blockers.append("decision_rule_application_must_be_complete")
    if decision.get("evidence_tier") != "E1":
        blockers.append("decision_rule_evidence_tier_must_be_e1")
    if not decision.get("next_safe_action"):
        blockers.append("decision_next_safe_action_required")
    if decision.get("decision") not in {
        "revise_h_a2_before_exact_replay",
        "park_h_a2_pending_new_mechanism",
        "prioritize_exact_replay_when_external_bar_blocker_clears",
    }:
        blockers.append("unsupported_decision")

    tier_blockers = "\n".join(summary.get("tier_blockers", []))
    for phrase in ["E1 diagnostic", "under-sampled", "No exact 2022-10", "No E2"]:
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
    parser = argparse.ArgumentParser(description="Validate H-A2 residual adverse-day analysis summary.")
    parser.add_argument("--summary-path", type=Path, default=DEFAULT_SUMMARY_PATH)
    args = parser.parse_args(argv)

    result = validate_h_a2_residual_adverse_day_analysis(args.summary_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
