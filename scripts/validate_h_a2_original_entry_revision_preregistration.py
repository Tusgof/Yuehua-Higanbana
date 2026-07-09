from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PREREG_PATH = PROJECT_ROOT / "experiments" / "h_a2_original_entry_revision_preregistration.json"


def validate_h_a2_original_entry_revision_preregistration(
    prereg_path: Path = DEFAULT_PREREG_PATH,
) -> dict[str, Any]:
    prereg = _load_json(prereg_path)
    blockers: list[str] = []

    if prereg.get("schema_version") != "h_a2_original_entry_revision_preregistration_v1":
        blockers.append("unsupported_schema_version")
    if prereg.get("artifact_type") != "preregistration":
        blockers.append("artifact_type_must_be_preregistration")
    if prereg.get("hypothesis_id") != "H-A2":
        blockers.append("hypothesis_id_must_be_h_a2")
    if prereg.get("status") != "preregistered":
        blockers.append("status_must_be_preregistered")
    if prereg.get("evidence_tier") != "E0":
        blockers.append("evidence_tier_must_be_e0")
    if prereg.get("experiment_id") != "h_a2_original_entry_revision":
        blockers.append("experiment_id_must_match")

    _validate_original_entry_rule(prereg, blockers)
    _validate_features(prereg, blockers)
    _validate_sources(prereg, blockers)
    _validate_tests(prereg, blockers)
    _validate_policies(prereg, blockers)
    _validate_claims_outputs_and_guardrails(prereg, blockers)

    rule = prereg.get("original_entry_rule", {})
    guardrails = prereg.get("guardrails", {})
    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "prereg_path": _relative(prereg_path),
        "hypothesis_id": prereg.get("hypothesis_id"),
        "evidence_tier": prereg.get("evidence_tier"),
        "experiment_id": prereg.get("experiment_id"),
        "locked_threshold": rule.get("opening_followthrough_threshold"),
        "candidate_decision_time_et": rule.get("candidate_decision_time_et"),
        "fifteen_minute_component_allowed": rule.get("fifteen_minute_conflict_component_allowed"),
        "network_allowed": guardrails.get("network_allowed"),
        "paid_data_allowed": guardrails.get("paid_data_allowed"),
        "broker_request_allowed": guardrails.get("broker_request_allowed"),
        "llm_call_allowed": guardrails.get("llm_call_allowed"),
        "threshold_search_allowed": guardrails.get("threshold_search_allowed_in_future_run"),
        "new_filter_allowed": guardrails.get("new_filter_allowed_in_future_run"),
        "planned_test_count": len(prereg.get("planned_future_tests", [])),
    }


def _validate_original_entry_rule(prereg: dict[str, Any], blockers: list[str]) -> None:
    rule = prereg.get("original_entry_rule", {})
    if rule.get("baseline_original_entry_time_et") != "09:35:00":
        blockers.append("baseline_entry_time_must_be_0935")
    if rule.get("candidate_decision_time_et") != "09:35:00":
        blockers.append("candidate_decision_time_must_be_0935")
    if rule.get("earliest_candidate_entry_time_et") != "09:35:00":
        blockers.append("earliest_candidate_entry_time_must_be_0935")
    if rule.get("opening_followthrough_threshold") != 0.001:
        blockers.append("locked_threshold_must_be_0_001")
    for field in [
        "entry_time_must_be_at_or_after_feature_completion",
        "clean_macro_vix_condition_required",
        "threshold_must_not_change",
    ]:
        if rule.get(field) is not True:
            blockers.append(f"{field}_must_be_true")
    for field in [
        "threshold_search_allowed",
        "oos_tuning_allowed",
        "new_oos_selected_filter_allowed",
        "delayed_entry_component_allowed",
        "fifteen_minute_conflict_component_allowed",
    ]:
        if rule.get(field) is not False:
            blockers.append(f"{field}_must_be_false")


def _validate_features(prereg: dict[str, Any], blockers: list[str]) -> None:
    allowed = {item.get("feature"): item for item in prereg.get("allowed_features", [])}
    if allowed.get("clean_macro_vix_condition", {}).get("known_by_et") != "09:35:00":
        blockers.append("clean_macro_vix_must_be_known_by_0935")
    if allowed.get("proxy_5m_followthrough", {}).get("known_by_et") != "09:35:00":
        blockers.append("proxy_5m_followthrough_must_be_known_by_0935")

    forbidden = {item.get("feature"): item for item in prereg.get("forbidden_features", [])}
    if forbidden.get("no_adverse_measured_15m_conflict", {}).get("known_by_et") != "09:45:00":
        blockers.append("fifteen_minute_conflict_must_be_forbidden_as_0945_feature")
    if "oos_loss_blacklist_or_new_filter" not in forbidden:
        blockers.append("oos_selected_filter_must_be_forbidden")


def _validate_sources(prereg: dict[str, Any], blockers: list[str]) -> None:
    if prereg.get("source_decision") != "reports/experiments/h_a2_delayed_entry_condition_summary.json":
        blockers.append("source_decision_must_be_h_a2_30_result")
    required = [
        "delayed_entry_condition_summary",
        "delayed_entry_condition_report",
        "signal_attribution_summary",
        "revised_opening_followthrough_summary",
        "revised_condition_robustness_summary",
        "lower_resolution_proxy_summary",
        "hypothesis_registry",
        "wiki_backtest_validation_protocol",
        "wiki_lookahead_bias",
    ]
    source_artifacts = prereg.get("source_artifacts", {})
    for key in required:
        value = source_artifacts.get(key)
        if not value:
            blockers.append(f"missing_source_artifact:{key}")
            continue
        path = Path(value)
        if path.is_absolute():
            if not path.exists():
                blockers.append(f"source_artifact_does_not_exist:{key}")
        elif not (PROJECT_ROOT / path).exists():
            blockers.append(f"source_artifact_does_not_exist:{key}")


def _validate_tests(prereg: dict[str, Any], blockers: list[str]) -> None:
    tests = prereg.get("planned_future_tests", [])
    test_ids = {test.get("test_id") for test in tests}
    required_ids = {
        "original_entry_timestamp_cleanliness",
        "original_entry_sample_recount",
        "original_entry_implementable_pnl_check",
        "risk_and_sample_adequacy_check",
        "hypothesis_decision",
    }
    for test_id in sorted(required_ids - test_ids):
        blockers.append(f"missing_planned_future_test:{test_id}")
    for test in tests:
        if len(test.get("minimum_output", [])) < 5:
            blockers.append(f"planned_future_test_needs_minimum_outputs:{test.get('test_id')}")


def _validate_policies(prereg: dict[str, Any], blockers: list[str]) -> None:
    split = prereg.get("split_policy", {})
    for field in [
        "chronological_split_required",
        "random_split_forbidden",
        "oos_tuning_forbidden",
        "threshold_locked_before_future_run",
        "result_must_report_train_oos_counts",
    ]:
        if split.get(field) is not True:
            blockers.append(f"{field}_must_be_true")

    execution = prereg.get("execution_policy", {})
    if execution.get("future_run_scope") != "local_no_paid_diagnostic_only":
        blockers.append("future_run_scope_must_be_local_no_paid_diagnostic_only")
    for field in [
        "original_0935_pnl_allowed_for_original_entry_pnl",
        "original_0935_pnl_must_not_be_labeled_as_delayed_entry_pnl",
        "entry_market_order_forbidden",
        "implementable_pnl_required",
        "mid_pnl_may_be_reported_only_as_control",
    ]:
        if execution.get(field) is not True:
            blockers.append(f"{field}_must_be_true")

    stats = prereg.get("statistical_policy", {})
    for field in [
        "sample_count_required_for_every_reported_group",
        "mintrl_psr_labels_must_be_preserved",
        "under_sampled_label_required",
        "underpowered_label_required",
        "search_log_required",
        "dsr_required_if_any_parameter_search_occurs",
        "acceptance_grade_claim_forbidden",
    ]:
        if stats.get(field) is not True:
            blockers.append(f"{field}_must_be_true")

    rules = prereg.get("decision_rules", {})
    for key in ["continue_original_entry_revision_if", "return_to_delayed_quote_acquisition_if", "park_h_a2_if"]:
        if len(rules.get(key, [])) < 3:
            blockers.append(f"decision_rule_needs_three_conditions:{key}")


def _validate_claims_outputs_and_guardrails(prereg: dict[str, Any], blockers: list[str]) -> None:
    allowed = "\n".join(prereg.get("allowed_claims", []))
    for phrase in ["original-entry", "09:35", "E1", "0.001"]:
        if phrase not in allowed:
            blockers.append(f"missing_allowed_claim_phrase:{phrase}")

    forbidden = "\n".join(prereg.get("forbidden_claims", []))
    for phrase in ["edge is validated", "E2", "paper trading", "15-minute", "09:35 PnL", "0.001", "OOS-selected", "IBKR", "LLMs", "GDELT"]:
        if phrase not in forbidden:
            blockers.append(f"missing_forbidden_claim_phrase:{phrase}")

    guardrails = prereg.get("guardrails", {})
    for field in [
        "network_allowed",
        "paid_data_allowed",
        "new_provider_allowed",
        "broker_request_allowed",
        "ibkr_request_allowed",
        "gdelt_live_retry_allowed",
        "llm_call_allowed",
        "threshold_search_allowed_in_future_run",
        "new_filter_allowed_in_future_run",
        "paper_trading_allowed",
        "operational_validation_allowed",
        "real_money_allowed",
        "research_log_required_for_this_preregistration",
    ]:
        if guardrails.get(field) is not False:
            blockers.append(f"{field}_must_be_false")

    outputs = prereg.get("allowed_outputs_for_future_run", {})
    for key in ["summary_json", "summary_md", "search_log", "research_log_if_real_experiment_completes"]:
        if not outputs.get(key):
            blockers.append(f"missing_future_output:{key}")

    completion = "\n".join(prereg.get("future_run_completion_criteria", []))
    for phrase in ["09:35", "15-minute", "train/OOS", "0.001", "E1", "research log 031"]:
        if phrase not in completion:
            blockers.append(f"missing_completion_criterion_phrase:{phrase}")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate H-A2 original-entry revision preregistration.")
    parser.add_argument("--prereg-path", type=Path, default=DEFAULT_PREREG_PATH)
    args = parser.parse_args(argv)

    result = validate_h_a2_original_entry_revision_preregistration(args.prereg_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
