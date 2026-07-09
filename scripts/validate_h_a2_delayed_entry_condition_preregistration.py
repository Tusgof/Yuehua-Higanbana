from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PREREG_PATH = PROJECT_ROOT / "experiments" / "h_a2_delayed_entry_condition_preregistration.json"


def validate_h_a2_delayed_entry_condition_preregistration(
    prereg_path: Path = DEFAULT_PREREG_PATH,
) -> dict[str, Any]:
    prereg = _load_json(prereg_path)
    blockers: list[str] = []

    if prereg.get("schema_version") != "h_a2_delayed_entry_condition_preregistration_v1":
        blockers.append("unsupported_schema_version")
    if prereg.get("artifact_type") != "preregistration":
        blockers.append("artifact_type_must_be_preregistration")
    if prereg.get("hypothesis_id") != "H-A2":
        blockers.append("hypothesis_id_must_be_h_a2")
    if prereg.get("status") != "preregistered":
        blockers.append("status_must_be_preregistered")
    if prereg.get("evidence_tier") != "E0":
        blockers.append("evidence_tier_must_be_e0")
    if prereg.get("experiment_id") != "h_a2_delayed_entry_condition":
        blockers.append("experiment_id_must_match")

    _validate_delayed_entry_rule(prereg, blockers)
    _validate_sources(prereg, blockers)
    _validate_tests(prereg, blockers)
    _validate_policies(prereg, blockers)
    _validate_claims_outputs_and_guardrails(prereg, blockers)

    rule = prereg.get("delayed_entry_rule", {})
    guardrails = prereg.get("guardrails", {})
    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "prereg_path": _relative(prereg_path),
        "hypothesis_id": prereg.get("hypothesis_id"),
        "evidence_tier": prereg.get("evidence_tier"),
        "experiment_id": prereg.get("experiment_id"),
        "locked_threshold": rule.get("opening_followthrough_threshold"),
        "candidate_decision_time_et": rule.get("new_candidate_decision_time_et"),
        "network_allowed": guardrails.get("network_allowed"),
        "paid_data_allowed": guardrails.get("paid_data_allowed"),
        "broker_request_allowed": guardrails.get("broker_request_allowed"),
        "llm_call_allowed": guardrails.get("llm_call_allowed"),
        "threshold_search_allowed": guardrails.get("threshold_search_allowed_in_future_run"),
        "new_filter_allowed": guardrails.get("new_filter_allowed_in_future_run"),
        "planned_test_count": len(prereg.get("planned_future_tests", [])),
    }


def _validate_delayed_entry_rule(prereg: dict[str, Any], blockers: list[str]) -> None:
    rule = prereg.get("delayed_entry_rule", {})
    if rule.get("baseline_original_entry_time_et") != "09:35:00":
        blockers.append("baseline_entry_time_must_be_0935")
    if rule.get("new_candidate_decision_time_et") != "09:45:00":
        blockers.append("candidate_decision_time_must_be_0945")
    if rule.get("earliest_candidate_entry_time_et") != "09:45:00":
        blockers.append("earliest_candidate_entry_time_must_be_0945")
    if rule.get("opening_followthrough_threshold") != 0.001:
        blockers.append("locked_threshold_must_be_0_001")
    true_fields = [
        "entry_time_must_be_after_feature_completion",
        "clean_macro_vix_condition_required",
        "threshold_must_not_change",
    ]
    for field in true_fields:
        if rule.get(field) is not True:
            blockers.append(f"{field}_must_be_true")
    false_fields = [
        "threshold_search_allowed",
        "oos_tuning_allowed",
        "new_oos_selected_filter_allowed",
    ]
    for field in false_fields:
        if rule.get(field) is not False:
            blockers.append(f"{field}_must_be_false")


def _validate_sources(prereg: dict[str, Any], blockers: list[str]) -> None:
    if prereg.get("source_decision") != "reports/experiments/h_a2_locked_condition_signal_attribution_summary.json":
        blockers.append("source_decision_must_be_h_a2_28_result")
    required = [
        "signal_attribution_summary",
        "signal_attribution_report",
        "revised_opening_followthrough_summary",
        "revised_condition_robustness_summary",
        "lower_resolution_proxy_summary",
        "proxy_first_robustness_summary",
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
        "delayed_entry_timestamp_cleanliness",
        "delayed_entry_fill_and_cost_feasibility",
        "retained_sample_recount",
        "implementable_pnl_comparison",
        "risk_and_robustness_recheck",
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
        "original_0935_pnl_must_not_be_reused_as_delayed_entry_pnl",
        "delayed_entry_quote_or_explicit_proxy_required",
        "proxy_result_must_be_labeled_if_no_delayed_quote",
        "entry_market_order_forbidden",
        "implementable_pnl_required_if_quote_data_exists",
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
    for key in ["continue_delayed_entry_candidate_if", "revise_to_timestamp_clean_original_entry_if", "park_h_a2_if"]:
        if len(rules.get(key, [])) < 3:
            blockers.append(f"decision_rule_needs_three_conditions:{key}")


def _validate_claims_outputs_and_guardrails(prereg: dict[str, Any], blockers: list[str]) -> None:
    allowed = "\n".join(prereg.get("allowed_claims", []))
    for phrase in ["delayed-entry", "15-minute", "E1", "0.001"]:
        if phrase not in allowed:
            blockers.append(f"missing_allowed_claim_phrase:{phrase}")

    forbidden = "\n".join(prereg.get("forbidden_claims", []))
    for phrase in ["edge is validated", "E2", "paper trading", "09:35 PnL", "0.001", "OOS-selected", "IBKR", "LLMs", "GDELT"]:
        if phrase not in forbidden:
            blockers.append(f"missing_forbidden_claim_phrase:{phrase}")

    guardrails = prereg.get("guardrails", {})
    false_fields = [
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
    ]
    for field in false_fields:
        if guardrails.get(field) is not False:
            blockers.append(f"{field}_must_be_false")

    outputs = prereg.get("allowed_outputs_for_future_run", {})
    for key in ["summary_json", "summary_md", "search_log", "research_log_if_real_experiment_completes"]:
        if not outputs.get(key):
            blockers.append(f"missing_future_output:{key}")

    completion = "\n".join(prereg.get("future_run_completion_criteria", []))
    for phrase in ["timestamp cleanliness", "quote data", "train/OOS", "0.001", "E1", "research log 030"]:
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
    parser = argparse.ArgumentParser(description="Validate H-A2 delayed-entry condition preregistration.")
    parser.add_argument("--prereg-path", type=Path, default=DEFAULT_PREREG_PATH)
    args = parser.parse_args(argv)

    result = validate_h_a2_delayed_entry_condition_preregistration(args.prereg_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
