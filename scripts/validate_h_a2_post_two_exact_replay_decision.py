from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DECISION_PATH = PROJECT_ROOT / "experiments" / "h_a2_post_two_exact_replay_decision.json"
NORMAL_REPLAY_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_normal_control_exact_replay.json"
POST_STRESS_REPLAY_PATH = (
    PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_post_stress_normalization_control_exact_replay.json"
)
DOC_PATH = PROJECT_ROOT / "docs" / "H_A2_POST_TWO_EXACT_REPLAY_DECISION.md"


def validate_h_a2_post_two_exact_replay_decision(decision_path: Path = DEFAULT_DECISION_PATH) -> dict[str, Any]:
    decision = _load_json(decision_path)
    blockers: list[str] = []

    if decision.get("schema_version") != "h_a2_post_two_exact_replay_decision_v1":
        blockers.append("unsupported_schema_version")
    if decision.get("artifact_type") != "decision_artifact":
        blockers.append("artifact_type_must_be_decision_artifact")
    if decision.get("hypothesis_id") != "H-A2":
        blockers.append("hypothesis_id_must_be_h_a2")
    if decision.get("status") != "decision_complete":
        blockers.append("status_must_be_decision_complete")
    if decision.get("evidence_tier") != "E0":
        blockers.append("evidence_tier_must_be_e0")
    if decision.get("experiment_id") != "h_a2_post_two_exact_replay_decision":
        blockers.append("experiment_id_must_match")

    _validate_sources(decision, blockers)
    _validate_source_summary(decision, blockers)
    _validate_decision_body(decision, blockers)
    _validate_next_artifact(decision, blockers)
    _validate_guardrails(decision, blockers)
    _validate_claims(decision, blockers)

    summary = decision.get("source_result_summary", {})
    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "decision_path": _relative(decision_path),
        "hypothesis_id": decision.get("hypothesis_id"),
        "evidence_tier": decision.get("evidence_tier"),
        "experiment_id": decision.get("experiment_id"),
        "selected_next_step": decision.get("decision", {}).get("selected_next_step"),
        "candidate_count": summary.get("candidate_count"),
        "total_mid_pnl": summary.get("total_mid_pnl"),
        "total_implementable_pnl": summary.get("total_implementable_pnl"),
        "paid_data_allowed": decision.get("guardrails", {}).get("paid_data_allowed"),
        "exact_replay_allowed": decision.get("guardrails", {}).get("exact_replay_allowed"),
        "paper_trading_allowed": decision.get("guardrails", {}).get("paper_trading_allowed"),
    }


def _validate_sources(decision: dict[str, Any], blockers: list[str]) -> None:
    for source in decision.get("source_artifacts", []):
        if not (PROJECT_ROOT / source).exists():
            blockers.append(f"source_artifact_missing:{source}")
    for path in [NORMAL_REPLAY_PATH, POST_STRESS_REPLAY_PATH, DOC_PATH]:
        if not path.exists():
            blockers.append(f"required_source_missing:{_relative(path)}")


def _validate_source_summary(decision: dict[str, Any], blockers: list[str]) -> None:
    source_payloads = [_load_json(NORMAL_REPLAY_PATH), _load_json(POST_STRESS_REPLAY_PATH)]
    summary = decision.get("source_result_summary", {})
    candidate_results = summary.get("candidate_results", [])

    if len(candidate_results) != 2:
        blockers.append("candidate_results_count_must_be_2")
        return
    if summary.get("candidate_count") != 2:
        blockers.append("candidate_count_must_be_2")

    total_mid = 0.0
    total_impl = 0.0
    total_drag = 0.0
    for source, recorded in zip(source_payloads, candidate_results, strict=True):
        if source.get("status") != "complete":
            blockers.append(f"source_not_complete:{source.get('experiment_id')}")
        if source.get("evidence_tier") != "E1":
            blockers.append(f"source_not_e1:{source.get('experiment_id')}")
        expected = {
            "source_experiment": source.get("experiment_id"),
            "candidate_date": source.get("candidate", {}).get("date"),
            "direction": source.get("candidate", {}).get("direction"),
            "mid_pnl": source.get("pnl", {}).get("mid_pnl"),
            "implementable_pnl": source.get("pnl", {}).get("implementable_pnl"),
            "cost_drag_vs_mid": source.get("pnl", {}).get("cost_drag_vs_mid"),
            "sample_count": source.get("sample_policy", {}).get("sample_count"),
            "under_sampled": source.get("sample_policy", {}).get("under_sampled"),
            "underpowered": source.get("sample_policy", {}).get("underpowered"),
        }
        for key, value in expected.items():
            if recorded.get(key) != value:
                blockers.append(f"source_summary_mismatch:{source.get('experiment_id')}:{key}")
        if source.get("paper_trading_allowed") is not False:
            blockers.append(f"source_paper_trading_must_be_false:{source.get('experiment_id')}")
        if source.get("strategy_use_allowed") is not False:
            blockers.append(f"source_strategy_use_must_be_false:{source.get('experiment_id')}")
        total_mid += float(source.get("pnl", {}).get("mid_pnl", 0.0))
        total_impl += float(source.get("pnl", {}).get("implementable_pnl", 0.0))
        total_drag += float(source.get("pnl", {}).get("cost_drag_vs_mid", 0.0))

    if summary.get("total_mid_pnl") != round(total_mid, 2):
        blockers.append("total_mid_pnl_mismatch")
    if summary.get("total_implementable_pnl") != round(total_impl, 2):
        blockers.append("total_implementable_pnl_mismatch")
    if summary.get("total_cost_drag_vs_mid") != round(total_drag, 2):
        blockers.append("total_cost_drag_vs_mid_mismatch")
    if summary.get("all_candidates_negative_mid_pnl") is not True:
        blockers.append("all_candidates_negative_mid_pnl_must_be_true")
    if summary.get("all_candidates_negative_implementable_pnl") is not True:
        blockers.append("all_candidates_negative_implementable_pnl_must_be_true")
    if summary.get("all_candidates_under_sampled") is not True:
        blockers.append("all_candidates_under_sampled_must_be_true")
    if summary.get("all_candidates_underpowered") is not True:
        blockers.append("all_candidates_underpowered_must_be_true")
    if summary.get("mintrl_psr_status") != "blocked_two_trade_underpowered":
        blockers.append("mintrl_psr_status_must_be_blocked_two_trade_underpowered")


def _validate_decision_body(decision: dict[str, Any], blockers: list[str]) -> None:
    body = decision.get("decision", {})
    if body.get("selected_next_step") != "revise_h_a2_mechanism_before_more_sample_expansion":
        blockers.append("selected_next_step_must_be_mechanism_revision")
    if body.get("decision_label") != "ยังสรุปไม่ได้":
        blockers.append("decision_label_must_be_inconclusive")
    required_phrases = [
        "two exact-replayed candidates",
        "negative after implementable costs",
        "market mechanism",
        "incorrectly specified hypothesis",
    ]
    reason = body.get("reason", "")
    for phrase in required_phrases:
        if phrase not in reason:
            blockers.append(f"decision_reason_missing:{phrase}")
    if "More samples may still be needed later" not in body.get("why_not_continue_data_expansion_now", ""):
        blockers.append("why_not_continue_data_expansion_now_must_allow_later_samples")
    if "under-sampled and underpowered" not in body.get("why_not_falsify_h_a2_now", ""):
        blockers.append("why_not_falsify_h_a2_now_must_reference_sample_limit")
    if "no E2 acceptance gate" not in body.get("why_not_claim_edge", ""):
        blockers.append("why_not_claim_edge_must_reference_e2_gate")
    if "post-result tuning" not in body.get("why_not_change_threshold_directly", ""):
        blockers.append("why_not_change_threshold_directly_must_reference_post_result_tuning")


def _validate_next_artifact(decision: dict[str, Any], blockers: list[str]) -> None:
    artifact = decision.get("next_required_artifact", {})
    if artifact.get("experiment_id") != "h_a2_mechanism_revision_preregistration":
        blockers.append("next_required_artifact_experiment_id_must_match")
    if artifact.get("artifact_type") != "preregistration":
        blockers.append("next_required_artifact_must_be_preregistration")
    must_include = "\n".join(artifact.get("must_include", []))
    for phrase in [
        "market behavior",
        "regime-filtered conditional hypothesis",
        "Train-only",
        "anti-overfitting",
        "Sample/regime expansion",
        "Falsification criteria",
    ]:
        if phrase not in must_include:
            blockers.append(f"next_artifact_missing_include_phrase:{phrase}")
    must_not = "\n".join(artifact.get("must_not_include", []))
    for phrase in ["paid data", "Exact replay", "Threshold search", "Paper trading", "E2"]:
        if phrase not in must_not:
            blockers.append(f"next_artifact_missing_exclusion_phrase:{phrase}")


def _validate_guardrails(decision: dict[str, Any], blockers: list[str]) -> None:
    locked = decision.get("locked_signal_status", {})
    if locked.get("existing_threshold") != 0.001:
        blockers.append("existing_threshold_must_be_0_001")
    if locked.get("existing_entry_time_et") != "09:35:00":
        blockers.append("existing_entry_time_must_be_0935")
    if locked.get("status") != "diagnostic_only_pending_mechanism_revision":
        blockers.append("locked_signal_status_must_be_diagnostic_only")
    for field in ["can_be_used_for_new_trades", "can_be_used_for_paper_trading", "can_be_used_for_e2_claim"]:
        if locked.get(field) is not False:
            blockers.append(f"{field}_must_be_false")

    guardrails = decision.get("guardrails", {})
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
        "new_filter_allowed",
        "paper_trading_allowed",
        "operational_validation_allowed",
        "real_money_allowed",
        "research_log_required_for_this_decision",
    ]:
        if guardrails.get(field) is not False:
            blockers.append(f"{field}_must_be_false")


def _validate_claims(decision: dict[str, Any], blockers: list[str]) -> None:
    allowed = "\n".join(decision.get("allowed_claims", []))
    for phrase in ["two exact-replayed", "E1 diagnostic", "mechanism-revision", "not accepted for paper trading"]:
        if phrase not in allowed:
            blockers.append(f"missing_allowed_claim_phrase:{phrase}")
    forbidden = "\n".join(decision.get("forbidden_claims", []))
    for phrase in [
        "fully falsified",
        "edge is validated",
        "E2",
        "paper trading",
        "real-money",
        "buy more data",
        "broaden exact replay",
        "0.001",
        "OOS-selected",
    ]:
        if phrase not in forbidden:
            blockers.append(f"missing_forbidden_claim_phrase:{phrase}")
    completion = "\n".join(decision.get("completion_criteria", []))
    for phrase in ["both exact replay", "PnL values", "negative after implementable costs", "mechanism revision", "validator passes"]:
        if phrase not in completion:
            blockers.append(f"missing_completion_criterion_phrase:{phrase}")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate H-A2 decision after two exact replays.")
    parser.add_argument("--decision-path", type=Path, default=DEFAULT_DECISION_PATH)
    args = parser.parse_args(argv)

    result = validate_h_a2_post_two_exact_replay_decision(args.decision_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
