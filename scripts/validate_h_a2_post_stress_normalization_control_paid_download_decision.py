from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DECISION_PATH = (
    PROJECT_ROOT / "experiments" / "h_a2_post_stress_normalization_control_paid_download_decision.json"
)
DEFAULT_ESTIMATE_PATH = (
    PROJECT_ROOT
    / "reports"
    / "data_cost"
    / "h_a2_post_stress_normalization_control_pack_cost_estimate.json"
)
DEFAULT_PAID_COST_AUDIT_PATH = PROJECT_ROOT / "reports" / "data_cost" / "paid_cost_audit.json"


EXPECTED_DATES = [
    "2025-05-05",
    "2025-05-06",
    "2025-05-07",
    "2025-05-08",
    "2025-05-09",
    "2025-05-12",
    "2025-05-13",
    "2025-05-14",
    "2025-05-15",
    "2025-05-16",
]


def validate_h_a2_post_stress_normalization_control_paid_download_decision(
    decision_path: Path = DEFAULT_DECISION_PATH,
    estimate_path: Path = DEFAULT_ESTIMATE_PATH,
    paid_cost_audit_path: Path = DEFAULT_PAID_COST_AUDIT_PATH,
) -> dict[str, Any]:
    blockers: list[str] = []
    decision = _load_json(decision_path)
    estimate = _load_json(estimate_path)
    paid_cost = _load_json(paid_cost_audit_path)

    if decision.get("schema_version") != "h_a2_post_stress_normalization_control_paid_download_decision_v1":
        blockers.append("unsupported_schema_version")
    if decision.get("artifact_type") != "download_decision":
        blockers.append("artifact_type_must_be_download_decision")
    if decision.get("hypothesis_id") != "H-A2":
        blockers.append("hypothesis_id_must_be_h_a2")
    if decision.get("evidence_tier") != "E0":
        blockers.append("evidence_tier_must_be_e0")
    if decision.get("status") != "decision_complete":
        blockers.append("status_must_be_decision_complete")
    if decision.get("decision") != "approve_post_stress_normalization_control_pack_download_after_paid_cost_audit_pass":
        blockers.append("decision_must_approve_post_stress_pack_after_audit")
    if decision.get("conclusion") != "ยังสรุปไม่ได้":
        blockers.append("conclusion_must_remain_inconclusive")

    selected_batch = decision.get("selected_batch", {})
    if selected_batch.get("batch_id") != "post_stress_normalization_control_pack":
        blockers.append("selected_batch_must_be_post_stress_normalization_control_pack")
    if selected_batch.get("dates") != EXPECTED_DATES:
        blockers.append("selected_dates_must_match_post_stress_pack")
    if selected_batch.get("macro_context", {}).get("high_importance_macro_days_from_local_calendar") != 0:
        blockers.append("selected_batch_must_have_zero_high_importance_macro_days")
    if selected_batch.get("vix_context", {}).get("bucket") != "vix_15_to_25":
        blockers.append("selected_batch_must_be_normal_vix_15_to_25")

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
    if estimate.get("batch_id") != "post_stress_normalization_control_pack":
        blockers.append("source_estimate_batch_mismatch")
    if estimate_decision.get("status") != "metadata_estimate_pass_next_download_decision_required":
        blockers.append("source_estimate_must_require_download_decision")
    if estimate.get("download_performed") is not False:
        blockers.append("source_estimate_must_not_have_downloaded")
    if estimate.get("planned_request_count") != 150:
        blockers.append("source_estimate_request_count_must_be_150")
    if estimate.get("cost_result", {}).get("live_request_count") != 20:
        blockers.append("source_estimate_live_metadata_call_count_must_be_20")
    if _round6(estimate.get("cost_result", {}).get("total_estimated_cost_usd")) != 5.558642:
        blockers.append("source_estimated_cost_mismatch")
    if _round6(estimate.get("projected_selected_key_usage_if_downloaded_usd")) != 5.558642:
        blockers.append("source_projected_selected_key_usage_mismatch")
    if estimate.get("selected_key_env_for_metadata_estimate") != "DATABENTO_API_AI":
        blockers.append("source_selected_key_env_must_be_databento_api_ai")

    scope = decision.get("approved_download_scope", {})
    if scope.get("selected_key_env") != "DATABENTO_API_AI":
        blockers.append("selected_key_env_must_be_databento_api_ai")
    if scope.get("planned_required_request_count") != 150:
        blockers.append("approved_required_request_count_must_be_150")
    if scope.get("metadata_grouped_request_count") != 20:
        blockers.append("approved_metadata_group_count_must_be_20")
    if scope.get("dates") != EXPECTED_DATES:
        blockers.append("approved_dates_must_match_post_stress_pack")
    if scope.get("provider") != "Databento":
        blockers.append("approved_provider_must_be_databento")
    if scope.get("symbol_scope") != "SPY only":
        blockers.append("symbol_scope_must_be_spy_only")
    if set(scope.get("datasets", [])) != {"OPRA.PILLAR", "EQUS.MINI"}:
        blockers.append("approved_datasets_mismatch")

    guard = decision.get("cost_guard", {})
    if paid_cost.get("status") != "pass":
        blockers.append("paid_cost_audit_must_pass")
    if guard.get("basis") != "selected_key_mo_ai_pool":
        blockers.append("cost_guard_basis_must_be_selected_key_pool")
    if guard.get("selected_key_env") != "DATABENTO_API_AI":
        blockers.append("cost_guard_selected_key_must_be_databento_api_ai")
    if _round6(guard.get("estimated_download_cost_usd")) != 5.558642:
        blockers.append("estimated_download_cost_mismatch")
    if _round6(guard.get("projected_selected_key_usage_if_downloaded_usd")) != 5.558642:
        blockers.append("projected_selected_key_usage_mismatch")
    if float(guard.get("projected_selected_key_usage_if_downloaded_usd", 999999)) >= float(
        guard.get("selected_key_cap_usd", 0)
    ):
        blockers.append("projected_selected_key_usage_must_remain_below_cap")
    if float(guard.get("projected_mo_ai_pool_usage_if_downloaded_usd", 999999)) >= float(
        guard.get("mo_ai_combined_pool_cap_usd", 0)
    ):
        blockers.append("projected_mo_ai_pool_usage_must_remain_below_cap")
    if guard.get("legacy_guard_would_be_exceeded") is not True:
        blockers.append("legacy_guard_exceedance_must_be_disclosed")
    if guard.get("decision") != "pass_under_selected_key_and_mo_ai_pool_caps":
        blockers.append("cost_guard_decision_must_use_selected_key_pool")

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
        "Do not download any date outside 2025-05-05 through 2025-05-16",
        "Do not download low_normal_vix_control_pack",
        "Do not resume the high-VIX-first acquisition sequence",
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
        "projected_selected_key_usage_if_downloaded_usd": guard.get(
            "projected_selected_key_usage_if_downloaded_usd"
        ),
        "approved_required_request_count": scope.get("planned_required_request_count"),
        "approved_metadata_group_count": scope.get("metadata_grouped_request_count"),
        "selected_key_env": scope.get("selected_key_env"),
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
    parser = argparse.ArgumentParser(
        description="Validate the H-A2 post-stress normalization/control paid download decision."
    )
    parser.add_argument("--decision-path", type=Path, default=DEFAULT_DECISION_PATH)
    parser.add_argument("--estimate-path", type=Path, default=DEFAULT_ESTIMATE_PATH)
    parser.add_argument("--paid-cost-audit-path", type=Path, default=DEFAULT_PAID_COST_AUDIT_PATH)
    args = parser.parse_args(argv)

    result = validate_h_a2_post_stress_normalization_control_paid_download_decision(
        args.decision_path,
        args.estimate_path,
        args.paid_cost_audit_path,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
