from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.environment import expand_configured_tokens
DEFAULT_PREREG_PATH = PROJECT_ROOT / "experiments" / "h_a2_residual_adverse_day_analysis_preregistration.json"


def validate_h_a2_residual_adverse_day_preregistration(
    prereg_path: Path = DEFAULT_PREREG_PATH,
) -> dict[str, Any]:
    prereg = _load_json(prereg_path)
    blockers: list[str] = []

    if prereg.get("schema_version") != "h_a2_residual_adverse_day_analysis_preregistration_v1":
        blockers.append("unsupported_schema_version")
    if prereg.get("artifact_type") != "preregistration":
        blockers.append("artifact_type_must_be_preregistration")
    if prereg.get("hypothesis_id") != "H-A2":
        blockers.append("hypothesis_id_must_be_h_a2")
    if prereg.get("status") != "preregistered":
        blockers.append("status_must_be_preregistered")
    if prereg.get("evidence_tier") != "E0":
        blockers.append("evidence_tier_must_be_e0")
    if prereg.get("experiment_id") != "h_a2_residual_adverse_day_analysis":
        blockers.append("experiment_id_must_be_h_a2_residual_adverse_day_analysis")

    _validate_source_artifacts(prereg, blockers)
    _validate_scope_and_tests(prereg, blockers)
    _validate_split_and_stats(prereg, blockers)
    _validate_decision_rules(prereg, blockers)
    _validate_claims_outputs_and_guardrails(prereg, blockers)

    guardrails = prereg.get("guardrails", {})
    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "prereg_path": _relative(prereg_path),
        "hypothesis_id": prereg.get("hypothesis_id"),
        "evidence_tier": prereg.get("evidence_tier"),
        "experiment_id": prereg.get("experiment_id"),
        "network_allowed": guardrails.get("network_allowed"),
        "paid_data_allowed": guardrails.get("paid_data_allowed"),
        "broker_request_allowed": guardrails.get("broker_request_allowed"),
        "llm_call_allowed": guardrails.get("llm_call_allowed"),
        "planned_test_count": len(prereg.get("planned_tests", [])),
    }


def _validate_source_artifacts(prereg: dict[str, Any], blockers: list[str]) -> None:
    source_artifacts = prereg.get("source_artifacts", {})
    required = [
        "post_proxy_decision",
        "post_proxy_decision_doc",
        "h_a2_proxy_first_robustness_summary",
        "h_l1_macro_event_proxy_baseline_summary",
        "baseline_summary",
        "macro_events",
        "vix_vxv",
        "spy_bars",
        "research_readiness_audit",
        "hypothesis_registry",
        "wiki_backtest_validation_protocol",
        "wiki_regime_filtering",
    ]
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

    if prereg.get("source_decision") != "experiments/h_a2_h_l1_post_proxy_decision.json":
        blockers.append("source_decision_must_be_post_proxy_decision")


def _validate_scope_and_tests(prereg: dict[str, Any], blockers: list[str]) -> None:
    scope = prereg.get("analysis_scope", {})
    target_groups = set(scope.get("target_groups", []))
    for group in ["non_risk_losing_trade_days", "macro_only_losing_trade_days", "oos_losing_trade_days"]:
        if group not in target_groups:
            blockers.append(f"missing_target_group:{group}")

    dimensions = "\n".join(scope.get("comparison_dimensions", []))
    for phrase in [
        "macro_event",
        "vix_vxv",
        "5_minute",
        "15_minute",
        "existing_implementable_trade_pnl",
        "big_day_dependency",
    ]:
        if phrase not in dimensions:
            blockers.append(f"missing_comparison_dimension:{phrase}")

    forbidden = "\n".join(scope.get("forbidden_inputs", []))
    for phrase in ["network", "paid data", "IBKR", "GDELT", "LLM", "paper trading"]:
        if phrase not in forbidden:
            blockers.append(f"missing_forbidden_input:{phrase}")

    tests = prereg.get("planned_tests", [])
    test_ids = {test.get("test_id") for test in tests}
    required_ids = {
        "residual_loss_bucket_profile",
        "macro_only_loss_profile",
        "non_risk_failure_mode_check",
        "decision_rule_application",
    }
    for test_id in sorted(required_ids - test_ids):
        blockers.append(f"missing_planned_test:{test_id}")
    for test in tests:
        if len(test.get("minimum_output", [])) < 3:
            blockers.append(f"planned_test_needs_minimum_outputs:{test.get('test_id')}")


def _validate_split_and_stats(prereg: dict[str, Any], blockers: list[str]) -> None:
    split = prereg.get("split_policy", {})
    for field in [
        "chronological_split_required",
        "random_split_forbidden",
        "oos_tuning_forbidden",
        "result_must_report_split_counts",
    ]:
        if split.get(field) is not True:
            blockers.append(f"{field}_must_be_true")

    stats = prereg.get("statistical_policy", {})
    for field in [
        "sample_count_required_for_every_bucket",
        "mintrl_psr_required_if_return_or_trade_series_exists",
        "under_sampled_label_required_below_mintrl",
        "underpowered_label_required_when_power_is_insufficient",
        "dsr_or_search_log_required_if_any_selection_or_best_bucket_is_reported",
        "big_day_dependency_context_required",
        "mid_vs_implementable_required_if_option_pnl_exists",
        "acceptance_grade_claim_forbidden",
    ]:
        if stats.get(field) is not True:
            blockers.append(f"{field}_must_be_true")


def _validate_decision_rules(prereg: dict[str, Any], blockers: list[str]) -> None:
    rules = prereg.get("decision_rules", {})
    for key in ["revise_h_a2_if", "park_h_a2_if", "prioritize_exact_replay_if"]:
        values = rules.get(key, [])
        if len(values) < 2:
            blockers.append(f"decision_rule_needs_two_conditions:{key}")

    combined = "\n".join(sum((rules.get(key, []) for key in rules), []))
    for phrase in ["Residual adverse days", "local feature", "exact 2022-10", "OOS"]:
        if phrase not in combined:
            blockers.append(f"missing_decision_rule_phrase:{phrase}")


def _validate_claims_outputs_and_guardrails(prereg: dict[str, Any], blockers: list[str]) -> None:
    allowed_claims = "\n".join(prereg.get("allowed_claims", []))
    for phrase in ["revised", "parked", "exact replay", "LLM scores"]:
        if phrase not in allowed_claims:
            blockers.append(f"missing_allowed_claim_phrase:{phrase}")

    forbidden_claims = "\n".join(prereg.get("forbidden_claims", []))
    for phrase in ["edge is validated", "exact 2022-10 ORB", "E2", "LLM", "paper trading", "IBKR", "new data", "GDELT"]:
        if phrase not in forbidden_claims:
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
        "paper_trading_allowed",
        "operational_validation_allowed",
        "real_money_allowed",
        "research_log_required_for_this_preregistration",
    ]
    for field in false_fields:
        if guardrails.get(field) is not False:
            blockers.append(f"{field}_must_be_false")
    if guardrails.get("strategy_pnl_allowed_in_future_run") is not True:
        blockers.append("strategy_pnl_allowed_in_future_run_must_be_true")

    outputs = prereg.get("allowed_outputs_for_future_run", {})
    for key in ["summary_json", "summary_md", "search_log", "research_log_if_real_experiment_completes"]:
        if not outputs.get(key):
            blockers.append(f"missing_future_output:{key}")

    completion = "\n".join(prereg.get("future_run_completion_criteria", []))
    for phrase in ["sample count", "MinTRL/PSR", "Conclusion", "revise H-A2", "park H-A2", "exact replay"]:
        if phrase not in completion:
            blockers.append(f"missing_completion_criterion_phrase:{phrase}")


def _load_json(path: Path) -> Any:
    return json.loads(expand_configured_tokens(path.read_text(encoding="utf-8")))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate H-A2 residual adverse-day preregistration.")
    parser.add_argument("--prereg-path", type=Path, default=DEFAULT_PREREG_PATH)
    args = parser.parse_args(argv)

    result = validate_h_a2_residual_adverse_day_preregistration(args.prereg_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
