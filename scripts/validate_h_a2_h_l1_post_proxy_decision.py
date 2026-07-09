from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DECISION_PATH = PROJECT_ROOT / "experiments" / "h_a2_h_l1_post_proxy_decision.json"


def validate_h_a2_h_l1_post_proxy_decision(decision_path: Path = DEFAULT_DECISION_PATH) -> dict[str, Any]:
    decision = _load_json(decision_path)
    blockers: list[str] = []

    if decision.get("schema_version") != "h_a2_h_l1_post_proxy_decision_v1":
        blockers.append("unsupported_schema_version")
    if decision.get("artifact_type") != "decision":
        blockers.append("artifact_type_must_be_decision")
    if decision.get("status") != "decision_complete":
        blockers.append("status_must_be_decision_complete")
    if decision.get("evidence_tier") != "E0":
        blockers.append("evidence_tier_must_be_e0")
    if decision.get("hypothesis_ids") != ["H-A2", "H-L1"]:
        blockers.append("hypothesis_ids_must_be_h_a2_h_l1")
    if decision.get("decision") != "continue_h_a2_local_residual_analysis_and_keep_h_l1_blocked_until_real_news":
        blockers.append("unexpected_decision")

    _validate_source_artifacts(decision, blockers)
    _validate_evidence_review(decision, blockers)
    _validate_selected_path(decision, blockers)
    _validate_rejected_paths(decision, blockers)
    _validate_next_requirements(decision, blockers)
    _validate_guardrails(decision, blockers)

    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "decision_path": _relative(decision_path),
        "decision": decision.get("decision"),
        "selected_path": decision.get("selected_next_path", {}).get("path_id"),
        "network_allowed": decision.get("guardrails", {}).get("network_allowed"),
        "paid_data_allowed": decision.get("guardrails", {}).get("paid_data_allowed"),
        "llm_call_allowed": decision.get("guardrails", {}).get("llm_call_allowed"),
        "paper_trading_allowed": decision.get("guardrails", {}).get("paper_trading_allowed"),
    }


def _validate_source_artifacts(decision: dict[str, Any], blockers: list[str]) -> None:
    required = [
        "h_a2_proxy_first_robustness_summary",
        "h_a2_proxy_first_robustness_report",
        "h_l1_macro_event_proxy_baseline_summary",
        "h_l1_macro_event_proxy_baseline_report",
        "research_readiness_audit",
        "hypothesis_registry",
    ]
    source_artifacts = decision.get("source_artifacts", {})
    for key in required:
        value = source_artifacts.get(key)
        if not value:
            blockers.append(f"missing_source_artifact:{key}")
        elif not _path_exists(value):
            blockers.append(f"source_artifact_does_not_exist:{key}")

    h_a2 = _load_json(PROJECT_ROOT / source_artifacts.get("h_a2_proxy_first_robustness_summary", "missing"))
    h_l1 = _load_json(PROJECT_ROOT / source_artifacts.get("h_l1_macro_event_proxy_baseline_summary", "missing"))
    if h_a2.get("status") != "complete" or h_a2.get("hypothesis_id") != "H-A2":
        blockers.append("h_a2_source_summary_must_be_complete_h_a2")
    if h_l1.get("status") != "complete" or h_l1.get("hypothesis_id") != "H-L1":
        blockers.append("h_l1_source_summary_must_be_complete_h_l1")
    if h_l1.get("not_llm_news_evidence") is not True:
        blockers.append("h_l1_source_must_be_marked_not_llm_news_evidence")
    if h_l1.get("llm_call_used") is not False or h_l1.get("real_news_tested") is not False:
        blockers.append("h_l1_source_must_not_use_llm_or_real_news")


def _validate_evidence_review(decision: dict[str, Any], blockers: list[str]) -> None:
    review = decision.get("evidence_review", {})
    h_a2 = review.get("h_a2", {})
    h_l1 = review.get("h_l1", {})

    expected_h_a2 = {
        "source_status": "complete",
        "source_evidence_tier": "E1",
        "daily_rows": 463,
        "measured_5m_days": 444,
        "measured_15m_days": 444,
        "trade_days": 90,
        "non_risk_trade_days": 64,
        "risk_trade_days": 26,
        "non_risk_minus_risk_5m_proxy": 0.001646,
        "non_risk_minus_risk_15m_proxy": 0.000669,
        "non_risk_minus_risk_trade_pnl": 23.375,
        "after_big_day_trim_non_risk_minus_risk_trade_pnl": 8.042741,
        "directionally_consistent": True,
        "exact_2022_orb_tested": False,
        "under_sampled": True,
        "underpowered": True,
    }
    for field, expected in expected_h_a2.items():
        if h_a2.get(field) != expected:
            blockers.append(f"h_a2_{field}_must_be_{expected}")

    expected_h_l1 = {
        "source_status": "complete",
        "source_evidence_tier": "E1",
        "not_llm_news_evidence": True,
        "llm_gate_tested": False,
        "real_news_tested": False,
        "timestamp_clean_news_cases_exist": False,
        "macro_only_avg_trade_pnl": -10.56,
        "clean_avg_trade_pnl": 12.815,
        "clean_minus_macro_only_avg_trade_pnl": 23.375,
    }
    for field, expected in expected_h_l1.items():
        if h_l1.get(field) != expected:
            blockers.append(f"h_l1_{field}_must_be_{expected}")
    if "residual adverse days" not in h_l1.get("future_llm_incremental_information_target", ""):
        blockers.append("h_l1_incremental_target_must_reference_residual_adverse_days")


def _validate_selected_path(decision: dict[str, Any], blockers: list[str]) -> None:
    selected = decision.get("selected_next_path", {})
    if selected.get("path_id") != "pre_register_h_a2_residual_adverse_day_analysis":
        blockers.append("selected_path_must_be_h_a2_residual_analysis")
    if selected.get("selected") is not True:
        blockers.append("selected_path_must_be_true")
    allowed_scope = "\n".join(selected.get("allowed_scope", []))
    for phrase in ["non-risk losing days", "deterministic macro/VIX labels", "narrower falsifiable condition"]:
        if phrase not in allowed_scope:
            blockers.append(f"missing_allowed_scope_phrase:{phrase}")
    forbidden_claims = "\n".join(selected.get("forbidden_claims", []))
    for phrase in [
        "H-A2 edge is validated",
        "L.7 is LLM or real-news evidence",
        "live LLM calls",
        "paper trading",
    ]:
        if phrase not in forbidden_claims:
            blockers.append(f"missing_forbidden_claim:{phrase}")


def _validate_rejected_paths(decision: dict[str, Any], blockers: list[str]) -> None:
    rejected = {item.get("path_id") for item in decision.get("rejected_paths", []) if isinstance(item, dict)}
    for path_id in [
        "paper_trading_now",
        "live_llm_prompt_research_now",
        "live_gdelt_retry_now",
        "buy_more_data_now",
        "exact_2022_orb_replay_now",
    ]:
        if path_id not in rejected:
            blockers.append(f"missing_rejected_path:{path_id}")


def _validate_next_requirements(decision: dict[str, Any], blockers: list[str]) -> None:
    requirements = decision.get("next_artifact_requirements", {})
    for field in [
        "must_be_preregistered_before_analysis",
        "must_use_local_artifacts_only",
        "must_not_use_network",
        "must_not_use_paid_data",
        "must_not_use_broker",
        "must_not_use_llm",
        "must_not_claim_e2",
        "must_report_sample_counts",
        "must_report_big_day_dependency_context",
        "must_explain_how_result_would_revise_or_park_h_a2",
        "must_keep_h_l1_incremental_baseline_rule",
    ]:
        if requirements.get(field) is not True:
            blockers.append(f"{field}_must_be_true")


def _validate_guardrails(decision: dict[str, Any], blockers: list[str]) -> None:
    guardrails = decision.get("guardrails", {})
    for field in [
        "network_allowed",
        "paid_data_allowed",
        "new_provider_allowed",
        "broker_request_allowed",
        "llm_call_allowed",
        "gdelt_live_retry_allowed",
        "strategy_pnl_allowed_in_this_artifact",
        "paper_trading_allowed",
        "operational_validation_allowed",
        "real_money_allowed",
        "research_log_required_for_this_decision",
    ]:
        if guardrails.get(field) is not False:
            blockers.append(f"{field}_must_be_false")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _path_exists(value: str) -> bool:
    path = Path(value)
    if path.is_absolute():
        return path.exists()
    return (PROJECT_ROOT / path).exists()


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate H-A2/H-L1 post-proxy decision.")
    parser.add_argument("--decision-path", type=Path, default=DEFAULT_DECISION_PATH)
    args = parser.parse_args(argv)

    result = validate_h_a2_h_l1_post_proxy_decision(args.decision_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
