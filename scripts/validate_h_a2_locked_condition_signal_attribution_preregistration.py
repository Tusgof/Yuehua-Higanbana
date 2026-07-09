from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PREREG_PATH = PROJECT_ROOT / "experiments" / "h_a2_locked_condition_signal_attribution_preregistration.json"


def validate_h_a2_locked_condition_signal_attribution_preregistration(
    prereg_path: Path = DEFAULT_PREREG_PATH,
) -> dict[str, Any]:
    prereg = _load_json(prereg_path)
    blockers: list[str] = []

    if prereg.get("schema_version") != "h_a2_locked_condition_signal_attribution_preregistration_v1":
        blockers.append("unsupported_schema_version")
    if prereg.get("artifact_type") != "preregistration":
        blockers.append("artifact_type_must_be_preregistration")
    if prereg.get("hypothesis_id") != "H-A2":
        blockers.append("hypothesis_id_must_be_h_a2")
    if prereg.get("status") != "preregistered":
        blockers.append("status_must_be_preregistered")
    if prereg.get("evidence_tier") != "E0":
        blockers.append("evidence_tier_must_be_e0")
    if prereg.get("experiment_id") != "h_a2_locked_condition_signal_attribution":
        blockers.append("experiment_id_must_be_h_a2_locked_condition_signal_attribution")

    _validate_locked_condition(prereg, blockers)
    _validate_sources(prereg, blockers)
    _validate_tests(prereg, blockers)
    _validate_policies(prereg, blockers)
    _validate_claims_outputs_and_guardrails(prereg, blockers)

    guardrails = prereg.get("guardrails", {})
    locked = prereg.get("locked_condition", {})
    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "prereg_path": _relative(prereg_path),
        "hypothesis_id": prereg.get("hypothesis_id"),
        "evidence_tier": prereg.get("evidence_tier"),
        "experiment_id": prereg.get("experiment_id"),
        "locked_threshold": locked.get("opening_followthrough_threshold"),
        "network_allowed": guardrails.get("network_allowed"),
        "paid_data_allowed": guardrails.get("paid_data_allowed"),
        "broker_request_allowed": guardrails.get("broker_request_allowed"),
        "llm_call_allowed": guardrails.get("llm_call_allowed"),
        "threshold_search_allowed": guardrails.get("threshold_search_allowed_in_future_run"),
        "new_filter_allowed": guardrails.get("new_filter_allowed_in_future_run"),
        "planned_test_count": len(prereg.get("planned_future_tests", [])),
    }


def _validate_locked_condition(prereg: dict[str, Any], blockers: list[str]) -> None:
    locked = prereg.get("locked_condition", {})
    if locked.get("opening_followthrough_threshold") != 0.001:
        blockers.append("locked_threshold_must_be_0_001")
    for field in ["threshold_must_not_change", "threshold_search_allowed", "oos_tuning_allowed"]:
        expected = field == "threshold_must_not_change"
        if locked.get(field) is not expected:
            blockers.append(f"{field}_must_be_{str(expected).lower()}")


def _validate_sources(prereg: dict[str, Any], blockers: list[str]) -> None:
    if prereg.get("source_decision") != "reports/experiments/h_a2_revised_condition_robustness_summary.json":
        blockers.append("source_decision_must_be_h_a2_26_result")

    required = [
        "h_a2_revised_condition_robustness_summary",
        "h_a2_revised_condition_robustness_report",
        "h_a2_revised_condition_robustness_preregistration",
        "h_a2_revised_condition_summary",
        "h_a2_lower_resolution_proxy_summary",
        "h_a2_proxy_first_robustness_summary",
        "hypothesis_registry",
        "wiki_backtest_validation_protocol",
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
        "decision_timestamp_availability_audit",
        "entry_rule_classification",
        "outcome_proxy_leakage_audit",
        "fixed_threshold_no_search_reconciliation",
        "hypothesis_implication_review",
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
        "threshold_locked_before_audit",
        "result_must_report_split_counts",
    ]:
        if split.get(field) is not True:
            blockers.append(f"{field}_must_be_true")

    stats = prereg.get("statistical_policy", {})
    for field in [
        "sample_count_required_for_every_reported_group",
        "mintrl_psr_labels_must_be_preserved",
        "under_sampled_label_required",
        "underpowered_label_required",
        "dsr_not_recomputed_from_new_search",
        "search_log_reference_required",
        "acceptance_grade_claim_forbidden",
    ]:
        if stats.get(field) is not True:
            blockers.append(f"{field}_must_be_true")

    rules = prereg.get("decision_rules", {})
    for key in [
        "classify_as_deployable_entry_filter_only_if",
        "classify_as_delayed_entry_candidate_if",
        "classify_as_diagnostic_proxy_only_if",
    ]:
        if len(rules.get(key, [])) < 2:
            blockers.append(f"decision_rule_needs_two_conditions:{key}")


def _validate_claims_outputs_and_guardrails(prereg: dict[str, Any], blockers: list[str]) -> None:
    allowed = "\n".join(prereg.get("allowed_claims", []))
    for phrase in ["signal-attribution audit", "0.001", "deployable entry filter", "diagnostic proxy", "E1"]:
        if phrase not in allowed:
            blockers.append(f"missing_allowed_claim_phrase:{phrase}")

    forbidden = "\n".join(prereg.get("forbidden_claims", []))
    for phrase in ["edge is validated", "E2", "0.001", "post-decision", "paper trading", "IBKR", "new data", "GDELT"]:
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
    for phrase in ["decision timestamp", "deployable entry filter", "0.001", "under-sampled", "next action"]:
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
    parser = argparse.ArgumentParser(description="Validate H-A2 locked-condition signal-attribution preregistration.")
    parser.add_argument("--prereg-path", type=Path, default=DEFAULT_PREREG_PATH)
    args = parser.parse_args(argv)

    result = validate_h_a2_locked_condition_signal_attribution_preregistration(args.prereg_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
