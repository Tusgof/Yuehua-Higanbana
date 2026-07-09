from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DECISION_PATH = PROJECT_ROOT / "experiments" / "h_a2_independent_validation_paid_download_decision.json"
DEFAULT_ESTIMATE_PATH = PROJECT_ROOT / "reports" / "data_cost" / "h_a2_independent_validation_paid_cost_estimate.json"
DEFAULT_PAID_COST_AUDIT_PATH = PROJECT_ROOT / "reports" / "data_cost" / "paid_cost_audit.json"


def validate_h_a2_independent_validation_paid_download_decision(
    decision_path: Path = DEFAULT_DECISION_PATH,
    estimate_path: Path = DEFAULT_ESTIMATE_PATH,
    paid_cost_audit_path: Path = DEFAULT_PAID_COST_AUDIT_PATH,
) -> dict[str, Any]:
    blockers: list[str] = []
    decision = _load_json(decision_path)
    estimate = _load_json(estimate_path)
    paid_cost = _load_json(paid_cost_audit_path)

    if decision.get("schema_version") != "h_a2_independent_validation_paid_download_decision_v1":
        blockers.append("unsupported_schema_version")
    if decision.get("hypothesis_id") != "H-A2":
        blockers.append("hypothesis_id_must_be_h_a2")
    if decision.get("evidence_tier") != "E0":
        blockers.append("evidence_tier_must_be_e0")
    if decision.get("status") != "decision_complete":
        blockers.append("status_must_be_decision_complete")
    if decision.get("decision") != "approve_sample_cost_probe_high_vix_one_day_download_after_paid_cost_audit_pass":
        blockers.append("decision_must_approve_only_one_day_after_audit")
    if decision.get("conclusion") != "ยังสรุปไม่ได้":
        blockers.append("conclusion_must_remain_inconclusive")

    selected_batch = decision.get("selected_batch", {})
    if selected_batch.get("batch_id") != "sample_cost_probe_high_vix_one_day":
        blockers.append("selected_batch_must_be_sample_cost_probe")
    if selected_batch.get("dates") != ["2025-04-08"]:
        blockers.append("selected_dates_must_be_2025_04_08_only")

    locked = decision.get("locked_signal_under_validation", {})
    if locked.get("candidate_decision_time_et") != "09:35:00":
        blockers.append("candidate_decision_time_must_remain_0935")
    if locked.get("entry_time_et") != "09:35:00":
        blockers.append("entry_time_must_remain_0935")
    if _round6(locked.get("opening_followthrough_threshold")) != 0.001:
        blockers.append("threshold_must_remain_0_001")
    for field in [
        "threshold_search_allowed",
        "oos_tuning_allowed",
        "new_oos_selected_filter_allowed",
        "fifteen_minute_conflict_component_allowed",
        "delayed_entry_component_allowed",
    ]:
        if locked.get(field) is not False:
            blockers.append(f"{field}_must_be_false")

    estimate_decision = estimate.get("decision", {})
    if estimate_decision.get("status") != "metadata_estimate_pass_next_download_decision_required":
        blockers.append("source_estimate_must_require_download_decision")
    if estimate.get("batch_id") != "sample_cost_probe_high_vix_one_day":
        blockers.append("source_estimate_batch_mismatch")
    if estimate.get("download_performed") is not False:
        blockers.append("source_estimate_must_not_have_downloaded")
    if estimate.get("planned_request_count") != 15:
        blockers.append("source_estimate_request_count_must_be_15")
    if _round6(estimate.get("cost_result", {}).get("total_estimated_cost_usd")) != 0.504662:
        blockers.append("source_estimated_cost_mismatch")
    if _round6(estimate.get("projected_usage_if_downloaded_usd")) != 120.494368:
        blockers.append("source_projected_usage_mismatch")

    scope = decision.get("approved_download_scope", {})
    if scope.get("request_count") != 15:
        blockers.append("approved_request_count_must_be_15")
    if scope.get("date") != "2025-04-08":
        blockers.append("approved_date_must_be_2025_04_08")
    if scope.get("provider") != "Databento":
        blockers.append("approved_provider_must_be_databento")
    if scope.get("symbol_scope") != "SPY only":
        blockers.append("symbol_scope_must_be_spy_only")
    if set(scope.get("datasets", [])) != {"OPRA.PILLAR", "EQUS.MINI"}:
        blockers.append("approved_datasets_mismatch")

    guard = decision.get("cost_guard", {})
    if paid_cost.get("status") != "pass":
        blockers.append("paid_cost_audit_must_pass")
    paid_cost_used = _round6(paid_cost.get("cost_guard_used_usd"))
    paid_cost_remaining = _round6(paid_cost.get("remaining_before_stop_usd"))
    decision_current_used = _round6(guard.get("current_used_usd"))
    decision_projected_used = _round6(guard.get("projected_used_after_download_usd"))
    decision_remaining = _round6(guard.get("remaining_before_stop_usd"))
    decision_projected_remaining = _round6(guard.get("projected_remaining_after_download_usd"))
    if paid_cost_used not in {decision_current_used, decision_projected_used}:
        blockers.append("paid_cost_used_must_match_decision_before_or_after_download")
    if paid_cost_remaining not in {decision_remaining, decision_projected_remaining}:
        blockers.append("paid_cost_remaining_must_match_decision_before_or_after_download")
    if _round6(guard.get("estimated_download_cost_usd")) != 0.504662:
        blockers.append("estimated_download_cost_mismatch")
    if _round6(guard.get("projected_used_after_download_usd")) != 120.494368:
        blockers.append("projected_used_after_download_mismatch")
    if _round6(guard.get("projected_remaining_after_download_usd")) != 4.505632:
        blockers.append("projected_remaining_after_download_mismatch")
    if float(guard.get("projected_used_after_download_usd", 999999)) >= float(guard.get("stop_threshold_usd", 0)):
        blockers.append("projected_usage_must_remain_below_stop_threshold")
    if guard.get("decision") != "pass":
        blockers.append("cost_guard_decision_must_pass")

    guardrails = decision.get("guardrails", {})
    for field in [
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
        "paid_data_downloaded_by_this_decision",
        "research_log_required_for_this_decision",
    ]:
        if guardrails.get(field) is not False:
            blockers.append(f"{field}_must_be_false")
    for field in [
        "network_allowed_for_download_after_paid_cost_audit_pass",
        "paid_data_allowed_after_paid_cost_audit_pass",
    ]:
        if guardrails.get(field) is not True:
            blockers.append(f"{field}_must_be_true")

    forbidden_text = "\n".join(decision.get("forbidden_actions", []))
    for phrase in [
        "Do not download any date other than 2025-04-08",
        "Do not estimate or download the broad 2025 calendar",
        "Do not download high_vix_validation_pack",
        "Do not change threshold 0.001",
        "Do not approve paper trading",
    ]:
        if phrase not in forbidden_text:
            blockers.append(f"missing_forbidden_action:{phrase}")

    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "decision_path": _relative(decision_path),
        "batch_id": selected_batch.get("batch_id"),
        "selected_dates": selected_batch.get("dates"),
        "estimated_download_cost_usd": guard.get("estimated_download_cost_usd"),
        "projected_used_after_download_usd": guard.get("projected_used_after_download_usd"),
        "projected_remaining_after_download_usd": guard.get("projected_remaining_after_download_usd"),
        "paid_cost_audit_used_usd": paid_cost.get("cost_guard_used_usd"),
        "paid_cost_audit_remaining_usd": paid_cost.get("remaining_before_stop_usd"),
        "approved_request_count": scope.get("request_count"),
    }


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _round6(value: Any) -> float | None:
    if value is None:
        return None
    return round(float(value), 6)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the H-A2 independent-validation paid download decision.")
    parser.add_argument("--decision-path", type=Path, default=DEFAULT_DECISION_PATH)
    parser.add_argument("--estimate-path", type=Path, default=DEFAULT_ESTIMATE_PATH)
    parser.add_argument("--paid-cost-audit-path", type=Path, default=DEFAULT_PAID_COST_AUDIT_PATH)
    args = parser.parse_args(argv)

    result = validate_h_a2_independent_validation_paid_download_decision(
        args.decision_path,
        args.estimate_path,
        args.paid_cost_audit_path,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
