from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PREREG_PATH = PROJECT_ROOT / "experiments" / "h_a2_mechanism_revision_preregistration.json"
H_A2_58_DECISION_PATH = PROJECT_ROOT / "experiments" / "h_a2_post_two_exact_replay_decision.json"
DOC_PATH = PROJECT_ROOT / "docs" / "H_A2_MECHANISM_REVISION_PREREGISTRATION.md"


def validate_h_a2_mechanism_revision_preregistration(prereg_path: Path = DEFAULT_PREREG_PATH) -> dict[str, Any]:
    prereg = _load_json(prereg_path)
    blockers: list[str] = []

    if prereg.get("schema_version") != "h_a2_mechanism_revision_preregistration_v1":
        blockers.append("unsupported_schema_version")
    if prereg.get("artifact_type") != "preregistration":
        blockers.append("artifact_type_must_be_preregistration")
    if prereg.get("hypothesis_id") != "H-A2":
        blockers.append("hypothesis_id_must_be_h_a2")
    if prereg.get("status") != "preregistered":
        blockers.append("status_must_be_preregistered")
    if prereg.get("evidence_tier") != "E0":
        blockers.append("evidence_tier_must_be_e0")
    if prereg.get("experiment_id") != "h_a2_mechanism_revision_preregistration":
        blockers.append("experiment_id_must_match")

    _validate_sources(prereg, blockers)
    _validate_h_a2_58_decision(blockers)
    _validate_revised_hypothesis(prereg, blockers)
    _validate_mechanism_dimensions(prereg, blockers)
    _validate_planned_diagnostic(prereg, blockers)
    _validate_controls(prereg, blockers)
    _validate_sample_policy(prereg, blockers)
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
        "exact_replay_allowed": prereg.get("guardrails", {}).get("exact_replay_allowed"),
        "paper_trading_allowed": prereg.get("guardrails", {}).get("paper_trading_allowed"),
    }


def _validate_sources(prereg: dict[str, Any], blockers: list[str]) -> None:
    if "experiments/h_a2_post_two_exact_replay_decision.json" not in prereg.get("source_artifacts", []):
        blockers.append("source_artifact_missing:experiments/h_a2_post_two_exact_replay_decision.json")
    for source in prereg.get("source_artifacts", []):
        if not (PROJECT_ROOT / source).exists():
            blockers.append(f"source_artifact_missing:{source}")
    if not DOC_PATH.exists():
        blockers.append(f"required_doc_missing:{_relative(DOC_PATH)}")
    for item in prereg.get("wiki_basis", []):
        path = Path(str(item.get("path", "")))
        if not path.exists():
            blockers.append(f"wiki_basis_missing:{path}")
        if not item.get("use"):
            blockers.append(f"wiki_basis_missing_use:{path}")


def _validate_h_a2_58_decision(blockers: list[str]) -> None:
    decision = _load_json(H_A2_58_DECISION_PATH)
    if decision.get("status") != "decision_complete":
        blockers.append("h_a2_58_decision_must_be_complete")
    if decision.get("decision", {}).get("selected_next_step") != "revise_h_a2_mechanism_before_more_sample_expansion":
        blockers.append("h_a2_58_must_select_mechanism_revision")
    summary = decision.get("source_result_summary", {})
    if summary.get("total_implementable_pnl") != -59.12:
        blockers.append("h_a2_58_total_implementable_pnl_mismatch")
    if summary.get("all_candidates_negative_implementable_pnl") is not True:
        blockers.append("h_a2_58_must_have_negative_implementable_candidates")


def _validate_revised_hypothesis(prereg: dict[str, Any], blockers: list[str]) -> None:
    question = prereg.get("revised_research_question", "")
    for phrase in ["positive implementable expectancy", "early directional continuation", "option spread cost", "market regime"]:
        if phrase not in question:
            blockers.append(f"revised_question_missing:{phrase}")
    hypothesis = prereg.get("revised_hypothesis", {})
    if "conditional continuation hypothesis" not in hypothesis.get("claim", ""):
        blockers.append("claim_must_reframe_as_conditional_continuation")
    for phrase in ["overcome debit", "bid/ask spread", "per-leg fees"]:
        if phrase not in hypothesis.get("mechanism", ""):
            blockers.append(f"mechanism_missing:{phrase}")
    if "two exact-replayed losses" not in hypothesis.get("why_current_condition_may_be_wrong", ""):
        blockers.append("why_current_condition_may_be_wrong_must_reference_two_losses")
    if len(hypothesis.get("what_would_make_it_plausible", [])) < 4:
        blockers.append("plausibility_criteria_too_short")


def _validate_mechanism_dimensions(prereg: dict[str, Any], blockers: list[str]) -> None:
    dimensions = {item.get("dimension"): item for item in prereg.get("candidate_mechanism_dimensions", [])}
    for name in ["post_entry_followthrough", "cost_drag", "regime_context", "selection_risk"]:
        if name not in dimensions:
            blockers.append(f"missing_mechanism_dimension:{name}")
    for item in dimensions.values():
        if not item.get("question"):
            blockers.append(f"mechanism_dimension_missing_question:{item.get('dimension')}")
        if not item.get("allowed_local_inputs"):
            blockers.append(f"mechanism_dimension_missing_inputs:{item.get('dimension')}")


def _validate_planned_diagnostic(prereg: dict[str, Any], blockers: list[str]) -> None:
    diagnostic = prereg.get("planned_next_diagnostic", {})
    if diagnostic.get("experiment_id") != "h_a2_mechanism_revision_audit":
        blockers.append("planned_next_diagnostic_id_must_match")
    if diagnostic.get("evidence_tier") != "E1":
        blockers.append("planned_next_diagnostic_tier_must_be_e1")
    if diagnostic.get("mode") != "local_no_paid_diagnostic":
        blockers.append("planned_next_diagnostic_must_be_local_no_paid")
    outputs = "\n".join(diagnostic.get("required_outputs", []))
    for phrase in ["Mechanism autopsy", "post-entry magnitude", "cost drag", "park current locked condition", "cannot claim E2"]:
        if phrase not in outputs:
            blockers.append(f"planned_outputs_missing:{phrase}")
    forbidden = "\n".join(diagnostic.get("forbidden_outputs", []))
    for phrase in ["No new threshold", "No new paid data", "No exact replay", "No paper-trading", "No E2"]:
        if phrase not in forbidden:
            blockers.append(f"planned_forbidden_outputs_missing:{phrase}")


def _validate_controls(prereg: dict[str, Any], blockers: list[str]) -> None:
    controls = prereg.get("anti_overfitting_controls", {})
    if controls.get("threshold_0_001_status") != "locked_as_prior_diagnostic_reference_only":
        blockers.append("threshold_status_must_be_prior_diagnostic_reference")
    false_fields = [
        "new_threshold_search_allowed",
        "oos_selected_filter_allowed",
        "paid_data_before_mechanism_audit_allowed",
    ]
    for field in false_fields:
        if controls.get(field) is not False:
            blockers.append(f"{field}_must_be_false")
    true_fields = [
        "train_only_revision_required_before_any_new_rule",
        "search_log_required_for_future_trials",
        "dsr_required_if_selecting_best_trial",
        "chronological_split_required",
        "mintrl_psr_required_for_acceptance_claim",
        "big_day_dependency_required_for_backtest_claim",
    ]
    for field in true_fields:
        if controls.get(field) is not True:
            blockers.append(f"{field}_must_be_true")


def _validate_sample_policy(prereg: dict[str, Any], blockers: list[str]) -> None:
    policy = prereg.get("sample_expansion_policy", {})
    if policy.get("sample_expansion_allowed_by_this_artifact") is not False:
        blockers.append("sample_expansion_allowed_must_be_false")
    if "specific regime or inference gap" not in policy.get("future_sample_expansion_condition", ""):
        blockers.append("future_sample_expansion_condition_must_name_regime_or_gap")
    for phrase in ["normal VIX", "high VIX", "macro-event", "trend"]:
        if phrase not in "\n".join(policy.get("must_cover_regimes", [])):
            blockers.append(f"must_cover_regimes_missing:{phrase}")
    for metric in ["active trade count", "MinTRL", "PSR", "DSR", "mid_pnl", "implementable_pnl", "cost_drag", "big-day dependency"]:
        if metric not in "\n".join(policy.get("must_report", [])):
            blockers.append(f"must_report_missing:{metric}")


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
        "exact_replay_allowed",
        "threshold_search_allowed",
        "new_filter_selected_allowed",
        "paper_trading_allowed",
        "operational_validation_allowed",
        "real_money_allowed",
        "research_log_required_for_this_preregistration",
    ]:
        if guardrails.get(field) is not False:
            blockers.append(f"{field}_must_be_false")
    allowed = "\n".join(prereg.get("allowed_claims", []))
    for phrase in ["conditional continuation", "local/no-paid", "two exact replay losses", "No H-A2 edge"]:
        if phrase not in allowed:
            blockers.append(f"allowed_claim_missing:{phrase}")
    forbidden = "\n".join(prereg.get("forbidden_claims", []))
    for phrase in ["edge is validated", "fully falsified", "paid data", "exact replay", "0.001", "OOS filter", "paper trading", "E2"]:
        if phrase not in forbidden:
            blockers.append(f"forbidden_claim_missing:{phrase}")
    completion = "\n".join(prereg.get("completion_criteria", []))
    for phrase in ["H-A2.58", "conditional continuation", "implementable PnL", "MinTRL/PSR", "validator passes"]:
        if phrase not in completion:
            blockers.append(f"completion_criterion_missing:{phrase}")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate H-A2 mechanism revision preregistration.")
    parser.add_argument("--prereg-path", type=Path, default=DEFAULT_PREREG_PATH)
    args = parser.parse_args(argv)

    result = validate_h_a2_mechanism_revision_preregistration(args.prereg_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
