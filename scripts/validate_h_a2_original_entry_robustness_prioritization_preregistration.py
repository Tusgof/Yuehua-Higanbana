from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PREREG_PATH = (
    PROJECT_ROOT
    / "experiments"
    / "h_a2_original_entry_robustness_prioritization_preregistration.json"
)


def validate_h_a2_original_entry_robustness_prioritization_preregistration(
    prereg_path: Path = DEFAULT_PREREG_PATH,
) -> dict[str, Any]:
    prereg = _load_json(prereg_path)
    blockers: list[str] = []

    if prereg.get("schema_version") != "h_a2_original_entry_robustness_prioritization_preregistration_v1":
        blockers.append("unsupported_schema_version")
    if prereg.get("artifact_type") != "preregistration":
        blockers.append("artifact_type_must_be_preregistration")
    if prereg.get("hypothesis_id") != "H-A2":
        blockers.append("hypothesis_id_must_be_h_a2")
    if prereg.get("status") != "preregistered":
        blockers.append("status_must_be_preregistered")
    if prereg.get("evidence_tier") != "E0":
        blockers.append("evidence_tier_must_be_e0")
    if prereg.get("experiment_id") != "h_a2_original_entry_robustness_prioritization":
        blockers.append("experiment_id_must_match")

    _validate_locked_rule(prereg, blockers)
    _validate_inputs(prereg, blockers)
    _validate_planned_tests(prereg, blockers)
    _validate_policies_and_decisions(prereg, blockers)
    _validate_outputs_claims_and_guardrails(prereg, blockers)

    rule = prereg.get("locked_rule_under_review", {})
    guardrails = prereg.get("guardrails", {})
    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "prereg_path": _relative(prereg_path),
        "hypothesis_id": prereg.get("hypothesis_id"),
        "evidence_tier": prereg.get("evidence_tier"),
        "experiment_id": prereg.get("experiment_id"),
        "candidate_decision_time_et": rule.get("candidate_decision_time_et"),
        "locked_threshold": rule.get("opening_followthrough_threshold"),
        "fifteen_minute_component_allowed": rule.get("fifteen_minute_conflict_component_allowed"),
        "network_allowed": guardrails.get("network_allowed"),
        "paid_data_allowed": guardrails.get("paid_data_allowed"),
        "ibkr_request_allowed": guardrails.get("ibkr_request_allowed"),
        "llm_call_allowed": guardrails.get("llm_call_allowed"),
        "paper_trading_allowed": guardrails.get("paper_trading_allowed"),
        "planned_test_count": len(prereg.get("planned_future_tests", [])),
    }


def _validate_locked_rule(prereg: dict[str, Any], blockers: list[str]) -> None:
    rule = prereg.get("locked_rule_under_review", {})
    if rule.get("candidate_decision_time_et") != "09:35:00":
        blockers.append("candidate_decision_time_must_be_0935")
    if rule.get("entry_time_et") != "09:35:00":
        blockers.append("entry_time_must_be_0935")
    if rule.get("opening_followthrough_threshold") != 0.001:
        blockers.append("locked_threshold_must_be_0_001")
    for field in ["clean_macro_vix_condition_required", "threshold_must_remain_locked"]:
        if rule.get(field) is not True:
            blockers.append(f"{field}_must_be_true")
    for field in [
        "threshold_search_allowed",
        "oos_tuning_allowed",
        "new_oos_selected_filter_allowed",
        "fifteen_minute_conflict_component_allowed",
        "delayed_entry_component_allowed",
    ]:
        if rule.get(field) is not False:
            blockers.append(f"{field}_must_be_false")


def _validate_inputs(prereg: dict[str, Any], blockers: list[str]) -> None:
    if prereg.get("source_decision") != "reports/experiments/h_a2_original_entry_revision_summary.json":
        blockers.append("source_decision_must_be_h_a2_32_summary")
    for item in prereg.get("allowed_inputs", []):
        path = item.get("path")
        if not path:
            blockers.append(f"allowed_input_missing_path:{item.get('input')}")
            continue
        if not (PROJECT_ROOT / path).exists():
            blockers.append(f"allowed_input_path_missing:{item.get('input')}")
    forbidden_inputs = {item.get("input") for item in prereg.get("forbidden_inputs", [])}
    for required in ["new_paid_data", "ibkr_historical_bars", "live_llm_outputs", "gdelt_live_retry", "new_oos_selected_filter"]:
        if required not in forbidden_inputs:
            blockers.append(f"missing_forbidden_input:{required}")


def _validate_planned_tests(prereg: dict[str, Any], blockers: list[str]) -> None:
    tests = prereg.get("planned_future_tests", [])
    test_ids = {test.get("test_id") for test in tests}
    required_ids = {
        "source_rule_integrity",
        "leave_one_and_big_day_dependency",
        "regime_and_calendar_concentration",
        "skip_cost_tradeoff",
        "validation_priority_decision",
    }
    for test_id in sorted(required_ids - test_ids):
        blockers.append(f"missing_planned_future_test:{test_id}")
    for test in tests:
        if len(test.get("minimum_output", [])) < 5:
            blockers.append(f"planned_future_test_needs_minimum_outputs:{test.get('test_id')}")


def _validate_policies_and_decisions(prereg: dict[str, Any], blockers: list[str]) -> None:
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
    for key in [
        "prioritize_independent_validation_plan_if",
        "run_another_local_diagnostic_if",
        "return_to_delayed_quote_acquisition_if",
        "park_h_a2_original_entry_branch_if",
    ]:
        if len(rules.get(key, [])) < 3:
            blockers.append(f"decision_rule_needs_three_conditions:{key}")


def _validate_outputs_claims_and_guardrails(prereg: dict[str, Any], blockers: list[str]) -> None:
    outputs = prereg.get("allowed_outputs_for_future_run", {})
    for key in ["summary_json", "summary_md", "search_log", "research_log_if_real_experiment_completes"]:
        if not outputs.get(key):
            blockers.append(f"missing_future_output:{key}")
    if outputs.get("research_log_if_real_experiment_completes") != (
        "research_log/032-higanbana-h-a2-original-entry-robustness-prioritization.md"
    ):
        blockers.append("research_log_must_be_032_h_a2_original_entry_robustness_prioritization")

    allowed = "\n".join(prereg.get("allowed_claims", []))
    for phrase in ["pre-registered", "09:35-only", "E1", "independent validation-data planning"]:
        if phrase not in allowed:
            blockers.append(f"missing_allowed_claim_phrase:{phrase}")

    forbidden = "\n".join(prereg.get("forbidden_claims", []))
    for phrase in ["edge is validated", "E2", "paper trading", "exact replay", "paid data", "IBKR", "LLMs", "GDELT", "0.001", "OOS-selected"]:
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
        "exact_replay_allowed",
        "threshold_search_allowed_in_future_run",
        "new_filter_allowed_in_future_run",
        "paper_trading_allowed",
        "operational_validation_allowed",
        "real_money_allowed",
        "research_log_required_for_this_preregistration",
    ]:
        if guardrails.get(field) is not False:
            blockers.append(f"{field}_must_be_false")

    completion = "\n".join(prereg.get("future_run_completion_criteria", []))
    for phrase in ["09:35-only", "0.001", "big-day", "regime/calendar", "skip-cost", "E1", "research log 032"]:
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
    parser = argparse.ArgumentParser(
        description="Validate H-A2 original-entry robustness/prioritization preregistration."
    )
    parser.add_argument("--prereg-path", type=Path, default=DEFAULT_PREREG_PATH)
    args = parser.parse_args(argv)

    result = validate_h_a2_original_entry_robustness_prioritization_preregistration(args.prereg_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
