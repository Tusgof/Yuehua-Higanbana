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
DEFAULT_PREREG_PATH = PROJECT_ROOT / "experiments" / "h_a2_breakeven_aware_rule_preregistration.json"
H_A2_60_AUDIT_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_mechanism_revision_audit.json"
DOC_PATH = PROJECT_ROOT / "docs" / "H_A2_BREAKEVEN_AWARE_RULE_PREREGISTRATION.md"


def validate_h_a2_breakeven_aware_rule_preregistration(
    prereg_path: Path = DEFAULT_PREREG_PATH,
) -> dict[str, Any]:
    prereg = _load_json(prereg_path)
    blockers: list[str] = []

    if prereg.get("schema_version") != "h_a2_breakeven_aware_rule_preregistration_v1":
        blockers.append("unsupported_schema_version")
    if prereg.get("artifact_type") != "preregistration":
        blockers.append("artifact_type_must_be_preregistration")
    if prereg.get("hypothesis_id") != "H-A2":
        blockers.append("hypothesis_id_must_be_h_a2")
    if prereg.get("experiment_id") != "h_a2_breakeven_aware_rule_preregistration":
        blockers.append("experiment_id_must_match")
    if prereg.get("status") != "preregistered":
        blockers.append("status_must_be_preregistered")
    if prereg.get("evidence_tier") != "E0":
        blockers.append("evidence_tier_must_be_e0")

    _validate_sources(prereg, blockers)
    _validate_h_a2_60(blockers)
    _validate_revised_hypothesis(prereg, blockers)
    _validate_rule_family(prereg, blockers)
    _validate_next_diagnostic(prereg, blockers)
    _validate_controls(prereg, blockers)
    _validate_guardrails_and_claims(prereg, blockers)

    diagnostic = prereg.get("planned_next_diagnostic", {})
    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "preregistration_path": _relative(prereg_path),
        "hypothesis_id": prereg.get("hypothesis_id"),
        "evidence_tier": prereg.get("evidence_tier"),
        "experiment_id": prereg.get("experiment_id"),
        "planned_next_diagnostic": diagnostic.get("experiment_id"),
        "planned_next_mode": diagnostic.get("mode"),
        "paid_data_allowed": prereg.get("guardrails", {}).get("paid_data_allowed"),
        "exact_replay_expansion_allowed": prereg.get("guardrails", {}).get(
            "exact_replay_expansion_allowed"
        ),
        "paper_trading_allowed": prereg.get("guardrails", {}).get("paper_trading_allowed"),
    }


def _validate_sources(prereg: dict[str, Any], blockers: list[str]) -> None:
    expected = [
        "reports/diagnostics/h_a2_mechanism_revision_audit.json",
        "reports/diagnostics/h_a2_normal_control_exact_replay.json",
        "reports/diagnostics/h_a2_post_stress_normalization_control_exact_replay.json",
    ]
    for source in expected:
        if source not in prereg.get("source_artifacts", []):
            blockers.append(f"source_artifact_missing:{source}")
    for source in prereg.get("source_artifacts", []):
        if not (PROJECT_ROOT / source).exists():
            blockers.append(f"source_artifact_file_missing:{source}")
    if not DOC_PATH.exists():
        blockers.append(f"required_doc_missing:{_relative(DOC_PATH)}")
    for item in prereg.get("wiki_basis", []):
        path = Path(str(item.get("path", "")))
        if not path.exists():
            blockers.append(f"wiki_basis_missing:{path}")
        if not item.get("use"):
            blockers.append(f"wiki_basis_missing_use:{path}")


def _validate_h_a2_60(blockers: list[str]) -> None:
    audit = _load_json(H_A2_60_AUDIT_PATH)
    if audit.get("status") != "complete":
        blockers.append("h_a2_60_must_be_complete")
    if audit.get("experiment_id") != "h_a2_mechanism_revision_audit":
        blockers.append("h_a2_60_experiment_id_must_match")
    if audit.get("decision", {}).get("selected_next_step") != "preregister_train_only_revised_rule":
        blockers.append("h_a2_60_must_select_train_only_revision")
    aggregate = audit.get("aggregate_findings", {})
    if aggregate.get("directionally_correct_underlying_count") != 2:
        blockers.append("h_a2_60_directionally_correct_count_must_be_2")
    if aggregate.get("long_strike_not_reached_count") != 2:
        blockers.append("h_a2_60_long_strike_not_reached_count_must_be_2")
    if aggregate.get("total_implementable_pnl") != -59.12:
        blockers.append("h_a2_60_total_implementable_pnl_mismatch")


def _validate_revised_hypothesis(prereg: dict[str, Any], blockers: list[str]) -> None:
    question = prereg.get("revised_research_question", "")
    for phrase in ["decision-time state", "cost-adjusted strike-reachability", "underlying direction"]:
        if phrase not in question:
            blockers.append(f"revised_question_missing:{phrase}")
    hypothesis = prereg.get("revised_hypothesis", {})
    if "breakeven-aware conditional continuation" not in hypothesis.get("claim", ""):
        blockers.append("claim_must_be_breakeven_aware_conditional_continuation")
    for phrase in ["long strike", "debit", "bid/ask spread", "per-leg fees"]:
        if phrase not in hypothesis.get("mechanism_target", ""):
            blockers.append(f"mechanism_target_missing:{phrase}")

    allowed_inputs = set(hypothesis.get("allowed_decision_time_inputs", []))
    for item in [
        "opening_range_geometry_available_at_09_35_et",
        "entry_mid_debit_and_implementable_debit",
        "nearest_discrete_strike_mapping_at_entry",
    ]:
        if item not in allowed_inputs:
            blockers.append(f"allowed_decision_time_input_missing:{item}")
    forbidden_inputs = set(hypothesis.get("forbidden_live_inputs", []))
    for item in [
        "future_underlying_close",
        "future_post_entry_followthrough_to_close",
        "forced_close_option_quote",
        "same_day_realized_pnl_after_entry",
        "oos_result_selected_filter",
    ]:
        if item not in forbidden_inputs:
            blockers.append(f"forbidden_live_input_missing:{item}")
    if "not more filter piling" not in prereg.get("purpose", "").lower() and "payoff feasibility" not in hypothesis.get(
        "why_this_is_not_more_filter_piling", ""
    ):
        blockers.append("must_explain_not_filter_piling")


def _validate_rule_family(prereg: dict[str, Any], blockers: list[str]) -> None:
    family = prereg.get("rule_family_to_preregister", {})
    if family.get("rule_family_id") != "breakeven_aware_orb_debit_vertical":
        blockers.append("rule_family_id_must_match")
    if family.get("entry_time_et") != "09:35:00":
        blockers.append("entry_time_must_be_0935")
    if family.get("forced_close_time_et") != "15:45:00":
        blockers.append("forced_close_must_be_1545")
    if family.get("strike_mapping_method") != "nearest_discrete_strike_rounding":
        blockers.append("strike_mapping_method_must_be_nearest_discrete")
    for field in ["cost_model_required", "mid_pnl_control_required", "implementable_pnl_governing_metric"]:
        if family.get(field) is not True:
            blockers.append(f"{field}_must_be_true")
    dimensions = {item.get("dimension"): item for item in family.get("candidate_rule_dimensions", [])}
    expected_roles = {
        "strike_reachability_margin": "payoff_feasibility_target",
        "entry_debit_and_cost_drag": "decision_time_input",
        "opening_range_strength": "decision_time_input",
        "regime_context": "decision_time_input",
        "selection_risk": "validation_control",
    }
    for name, role in expected_roles.items():
        if dimensions.get(name, {}).get("role") != role:
            blockers.append(f"rule_dimension_role_mismatch:{name}")


def _validate_next_diagnostic(prereg: dict[str, Any], blockers: list[str]) -> None:
    diagnostic = prereg.get("planned_next_diagnostic", {})
    if diagnostic.get("experiment_id") != "h_a2_breakeven_aware_rule_train_diagnostic":
        blockers.append("planned_next_diagnostic_id_must_match")
    if diagnostic.get("evidence_tier") != "E1":
        blockers.append("planned_next_diagnostic_tier_must_be_e1")
    if diagnostic.get("mode") != "local_no_paid_train_only_diagnostic":
        blockers.append("planned_next_mode_must_be_train_only_no_paid")
    allowed_scope = "\n".join(diagnostic.get("allowed_data_scope", []))
    if "training_split_rows_only_for_rule_selection" not in allowed_scope:
        blockers.append("allowed_scope_must_be_train_only")
    outputs = "\n".join(diagnostic.get("required_outputs", []))
    for phrase in [
        "Decision-time feature list",
        "future/leakage exclusion",
        "Train-only candidate rule trial table",
        "Cost-adjusted strike-reachability target",
        "cannot claim E2",
    ]:
        if phrase not in outputs:
            blockers.append(f"required_output_missing:{phrase}")
    forbidden = "\n".join(diagnostic.get("forbidden_outputs", []))
    for phrase in ["No OOS-selected filter", "No new paid data", "No exact replay", "No broker", "No live LLM", "No paper-trading", "No E2"]:
        if phrase not in forbidden:
            blockers.append(f"forbidden_output_missing:{phrase}")


def _validate_controls(prereg: dict[str, Any], blockers: list[str]) -> None:
    controls = prereg.get("anti_overfitting_controls", {})
    true_fields = [
        "train_only_rule_selection_required",
        "chronological_split_required",
        "search_log_required",
        "trial_count_required",
        "dsr_required_if_selecting_best_trial",
        "mintrl_psr_required_for_acceptance_claim",
        "big_day_dependency_required_for_backtest_claim",
    ]
    for field in true_fields:
        if controls.get(field) is not True:
            blockers.append(f"{field}_must_be_true")
    false_fields = [
        "random_split_allowed",
        "oos_tuning_allowed",
        "post_result_filter_addition_allowed",
        "future_outcome_as_live_input_allowed",
    ]
    for field in false_fields:
        if controls.get(field) is not False:
            blockers.append(f"{field}_must_be_false")
    if controls.get("threshold_0_001_status") != "locked_as_prior_diagnostic_reference_only":
        blockers.append("threshold_status_must_be_prior_reference")
    policy = prereg.get("sample_and_data_policy", {})
    if policy.get("paid_data_allowed_by_this_artifact") is not False:
        blockers.append("paid_data_allowed_by_this_artifact_must_be_false")
    if policy.get("exact_replay_expansion_allowed_by_this_artifact") is not False:
        blockers.append("exact_replay_expansion_allowed_by_this_artifact_must_be_false")
    must_report = "\n".join(policy.get("must_report_if_later_expanded", []))
    for phrase in ["MinTRL", "PSR", "DSR", "implementable_pnl", "cost_drag", "strike reachability", "regime coverage"]:
        if phrase not in must_report:
            blockers.append(f"future_must_report_missing:{phrase}")


def _validate_guardrails_and_claims(prereg: dict[str, Any], blockers: list[str]) -> None:
    guardrails = prereg.get("guardrails", {})
    for field in [
        "network_allowed",
        "paid_data_allowed",
        "new_provider_allowed",
        "broker_request_allowed",
        "ibkr_request_allowed",
        "gdelt_live_retry_allowed",
        "llm_call_allowed",
        "exact_replay_expansion_allowed",
        "oos_filter_selection_allowed",
        "paper_trading_allowed",
        "operational_validation_allowed",
        "real_money_allowed",
        "research_log_required_for_this_preregistration",
    ]:
        if guardrails.get(field) is not False:
            blockers.append(f"{field}_must_be_false")
    allowed = "\n".join(prereg.get("allowed_claims", []))
    for phrase in ["breakeven-aware", "decision-time inputs", "No paid data"]:
        if phrase not in allowed:
            blockers.append(f"allowed_claim_missing:{phrase}")
    forbidden = "\n".join(prereg.get("forbidden_claims", []))
    for phrase in ["edge is validated", "fully falsified", "selected for trading", "paid data", "exact replay", "0.001", "OOS filter", "paper trading", "E2"]:
        if phrase not in forbidden:
            blockers.append(f"forbidden_claim_missing:{phrase}")
    completion = "\n".join(prereg.get("completion_criteria", []))
    for phrase in ["H-A2.60", "payoff feasibility", "decision-time inputs", "local/no-paid/train-only", "validator passes"]:
        if phrase not in completion:
            blockers.append(f"completion_criterion_missing:{phrase}")
    if not prereg.get("next_safe_action", "").startswith("Run H-A2.62"):
        blockers.append("next_safe_action_must_start_h_a2_62")


def _load_json(path: Path) -> Any:
    return json.loads(expand_configured_tokens(path.read_text(encoding="utf-8-sig")))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate H-A2 breakeven-aware rule preregistration.")
    parser.add_argument("--prereg-path", type=Path, default=DEFAULT_PREREG_PATH)
    args = parser.parse_args(argv)

    result = validate_h_a2_breakeven_aware_rule_preregistration(args.prereg_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
