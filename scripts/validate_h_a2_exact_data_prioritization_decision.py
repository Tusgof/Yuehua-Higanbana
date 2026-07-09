from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DECISION_PATH = PROJECT_ROOT / "experiments" / "h_a2_exact_data_prioritization_decision.json"


def validate_h_a2_exact_data_prioritization_decision(decision_path: Path = DEFAULT_DECISION_PATH) -> dict[str, Any]:
    decision = _load_json(decision_path)
    blockers: list[str] = []

    if decision.get("schema_version") != "h_a2_exact_data_prioritization_decision_v1":
        blockers.append("unsupported_schema_version")
    if decision.get("hypothesis_id") != "H-A2":
        blockers.append("hypothesis_id_must_be_h_a2")
    if decision.get("status") != "decision_complete":
        blockers.append("status_must_be_decision_complete")
    if decision.get("evidence_tier") != "E0":
        blockers.append("evidence_tier_must_be_e0")
    if decision.get("decision") != "narrow_exact_data_plan_is_justified_but_not_approved_for_execution":
        blockers.append("decision_must_not_approve_execution")

    source_artifacts = decision.get("source_artifacts", {})
    for key in [
        "h_a2_lower_resolution_proxy_summary",
        "h_a2_lower_resolution_proxy_report",
        "h_a2_lower_resolution_proxy_preregistration",
        "h_a2_followup_resolution_preregistration",
        "h_a2_2022_spy_bar_source_decision",
        "h_a2_2022_spy_bar_source_decision_doc",
        "hypothesis_data_resolution_audit",
        "wiki_orb_concept",
        "wiki_backtest_validation_protocol",
    ]:
        value = source_artifacts.get(key)
        if not value:
            blockers.append(f"missing_source_artifact:{key}")
        elif not _path_exists(value):
            blockers.append(f"source_artifact_does_not_exist:{key}")

    evidence = decision.get("evidence_review", {})
    expected_values = {
        "proxy_result_status": "complete",
        "proxy_evidence_tier": "E1",
        "proxy_conclusion": "ยังสรุปไม่ได้",
        "directionally_coherent": True,
        "measured_proxy_days": 444,
        "daily_row_count": 463,
        "trial_count": 7,
        "existing_trade_days": 90,
        "exact_2022_orb_tested": False,
        "under_sampled": True,
        "underpowered": True,
    }
    for field, expected in expected_values.items():
        if evidence.get(field) != expected:
            blockers.append(f"evidence_{field}_must_be_{expected}")

    resolution = decision.get("data_resolution_logic", {})
    if "SPY 1-minute bars are only one method" not in resolution.get("hypothesis_first_rule", ""):
        blockers.append("hypothesis_first_rule_must_demote_data_resolution")
    for field in ["one_minute_bars_required_for", "one_minute_bars_not_required_for"]:
        values = resolution.get(field, [])
        if not isinstance(values, list) or not values:
            blockers.append(f"{field}_must_be_nonempty_list")
    if "exact 2022-10 ORB entry timing" not in "\n".join(resolution.get("one_minute_bars_required_for", [])):
        blockers.append("must_state_exact_orb_requires_one_minute_bars")
    if "mechanism proxy review" not in "\n".join(resolution.get("one_minute_bars_not_required_for", [])):
        blockers.append("must_state_proxy_does_not_require_one_minute_bars")

    selected = decision.get("selected_next_path", {})
    if selected.get("path_id") != "draft_narrow_exact_2022_underlying_bar_plan":
        blockers.append("selected_path_must_be_narrow_exact_plan")
    if selected.get("selected") is not True:
        blockers.append("selected_path_must_be_true")
    forbidden_claims = "\n".join(selected.get("forbidden_claims", []))
    for phrase in ["edge is validated", "IBKR historical-bar requests", "paid data", "paper trading"]:
        if phrase not in forbidden_claims:
            blockers.append(f"missing_forbidden_claim:{phrase}")

    rejected_paths = {item.get("path_id") for item in decision.get("rejected_paths", [])}
    for path_id in ["request_ibkr_bars_now", "buy_new_provider_now", "paper_trading_or_operational_validation"]:
        if path_id not in rejected_paths:
            blockers.append(f"missing_rejected_path:{path_id}")

    requirements = decision.get("next_plan_requirements", {})
    for field in [
        "must_state_hypothesis_first",
        "must_name_exact_inference_gap",
        "must_limit_scope_to_2022_10_underlying_bars_before_any_2022_09_option_data",
        "must_explain_why_1_minute_bars_are_required_for_exact_rerun",
        "must_preserve_no_order_transmission",
        "must_preserve_no_paper_trading",
        "must_require_coverage_timestamp_import_validation_before_rerun",
        "must_require_user_approval_for_new_provider_or_paid_source",
        "must_not_use_proxy_result_as_e2_evidence",
    ]:
        if requirements.get(field) is not True:
            blockers.append(f"{field}_must_be_true")

    guardrails = decision.get("guardrails", {})
    for field in [
        "network_allowed",
        "paid_data_allowed",
        "new_provider_allowed",
        "ibkr_request_allowed",
        "llm_call_allowed",
        "strategy_pnl_allowed_in_this_artifact",
        "paper_trading_allowed",
        "operational_validation_allowed",
        "real_money_allowed",
        "research_log_required_for_this_decision",
    ]:
        if guardrails.get(field) is not False:
            blockers.append(f"{field}_must_be_false")

    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "decision_path": _relative(decision_path),
        "hypothesis_id": decision.get("hypothesis_id"),
        "evidence_tier": decision.get("evidence_tier"),
        "decision": decision.get("decision"),
        "selected_path": selected.get("path_id"),
        "ibkr_request_allowed": guardrails.get("ibkr_request_allowed"),
        "paid_data_allowed": guardrails.get("paid_data_allowed"),
        "paper_trading_allowed": guardrails.get("paper_trading_allowed"),
    }


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
    parser = argparse.ArgumentParser(description="Validate H-A2 exact-data prioritization decision.")
    parser.add_argument("--decision-path", type=Path, default=DEFAULT_DECISION_PATH)
    args = parser.parse_args(argv)

    result = validate_h_a2_exact_data_prioritization_decision(args.decision_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
