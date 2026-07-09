from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUMMARY_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_revised_condition_robustness_summary.json"


def validate_h_a2_revised_condition_robustness(summary_path: Path = DEFAULT_SUMMARY_PATH) -> dict[str, Any]:
    summary = _load_json(summary_path)
    blockers: list[str] = []

    if summary.get("schema_version") != "h_a2_revised_condition_robustness_v1":
        blockers.append("unsupported_schema_version")
    if summary.get("record_type") != "experiment_summary":
        blockers.append("record_type_must_be_experiment_summary")
    if summary.get("experiment_id") != "h_a2_revised_condition_robustness":
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
    _validate_methodology(summary, blockers)
    _validate_counts_and_checks(summary, blockers)

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
    for field in ["local_artifacts_only", "chronological_split_required", "threshold_locked_before_audit"]:
        if methodology.get(field) is not True:
            blockers.append(f"{field}_must_be_true")
    for field in ["random_split_used", "oos_tuning_used", "threshold_search_used"]:
        if methodology.get(field) is not False:
            blockers.append(f"{field}_must_be_false")
    if methodology.get("locked_threshold") != 0.001:
        blockers.append("locked_threshold_must_be_0_001")

    trial_policy = summary.get("trial_policy", {})
    if trial_policy.get("threshold_search_allowed") is not False:
        blockers.append("threshold_search_allowed_must_be_false")
    if trial_policy.get("threshold_search_used") is not False:
        blockers.append("trial_threshold_search_used_must_be_false")
    if trial_policy.get("trial_count") != 0:
        blockers.append("trial_count_must_be_zero")
    search_log = trial_policy.get("search_log")
    if not search_log or not (PROJECT_ROOT / search_log).exists():
        blockers.append("search_log_missing_on_disk")
    if "no_new_threshold_search" not in str(trial_policy.get("dsr_status", "")):
        blockers.append("dsr_status_must_state_no_new_threshold_search")


def _validate_counts_and_checks(summary: dict[str, Any], blockers: list[str]) -> None:
    counts = summary.get("sample_counts", {})
    expected = {
        "baseline_oos_non_risk_trade_days": 34,
        "retained_oos_trade_days": 13,
        "skipped_oos_trade_days": 21,
    }
    for key, value in expected.items():
        if counts.get(key) != value:
            blockers.append(f"unexpected_sample_count:{key}")

    provenance = summary.get("threshold_provenance_audit", {})
    if provenance.get("provenance_clean") is not True:
        blockers.append("threshold_provenance_must_be_clean")
    if provenance.get("threshold_search_used_in_this_audit") is not False:
        blockers.append("threshold_search_used_in_this_audit_must_be_false")

    for section in [
        "big_day_dependency_check",
        "concentration_fragility_check",
        "skip_cost_tradeoff_check",
        "sample_adequacy_relabeling",
        "decision_rule_application",
    ]:
        if summary.get(section, {}).get("status") not in {"complete", "diagnostic_underpowered"}:
            blockers.append(f"{section}_must_be_complete_or_diagnostic")

    sample = summary.get("sample_adequacy_relabeling", {})
    if sample.get("under_sampled_label") is not True:
        blockers.append("under_sampled_label_must_be_true")
    if sample.get("underpowered_label") is not True:
        blockers.append("underpowered_label_must_be_true")
    if sample.get("evidence_tier_cap") != "E1":
        blockers.append("evidence_tier_cap_must_be_e1")

    decision = summary.get("decision_rule_application", {})
    if decision.get("evidence_tier") != "E1":
        blockers.append("decision_evidence_tier_must_be_e1")
    if decision.get("threshold_search_used") is not False:
        blockers.append("decision_threshold_search_used_must_be_false")
    if decision.get("oos_tuning_used") is not False:
        blockers.append("decision_oos_tuning_used_must_be_false")

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
    parser = argparse.ArgumentParser(description="Validate H-A2 revised condition robustness summary.")
    parser.add_argument("--summary-path", type=Path, default=DEFAULT_SUMMARY_PATH)
    args = parser.parse_args(argv)

    result = validate_h_a2_revised_condition_robustness(args.summary_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
