from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DECISION_PATH = PROJECT_ROOT / "experiments" / "h_a2_normal_control_sample_decision.json"
VIX_PATH = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "vix_vxv" / "vix_vxv.jsonl"
MACRO_PATH = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "macro_calendar" / "macro_event.jsonl"


def validate_h_a2_normal_control_sample_decision(
    decision_path: Path = DEFAULT_DECISION_PATH,
) -> dict[str, Any]:
    decision = _load_json(decision_path)
    blockers: list[str] = []

    if decision.get("schema_version") != "h_a2_normal_control_sample_decision_v1":
        blockers.append("unsupported_schema_version")
    if decision.get("artifact_type") != "decision_preregistration":
        blockers.append("artifact_type_must_be_decision_preregistration")
    if decision.get("hypothesis_id") != "H-A2":
        blockers.append("hypothesis_id_must_be_h_a2")
    if decision.get("status") != "preregistered":
        blockers.append("status_must_be_preregistered")
    if decision.get("evidence_tier") != "E0":
        blockers.append("evidence_tier_must_be_e0")
    if decision.get("experiment_id") != "h_a2_normal_control_sample_decision":
        blockers.append("experiment_id_must_match")

    _validate_source_paths(decision, blockers)
    _validate_user_decision(decision, blockers)
    _validate_superseded_sequence(decision, blockers)
    _validate_locked_signal(decision, blockers)
    _validate_budget(decision, blockers)
    _validate_batches(decision, blockers)
    _validate_required_fields(decision, blockers)
    _validate_future_execution(decision, blockers)
    _validate_claims_and_guardrails(decision, blockers)

    batches = decision.get("candidate_estimate_batches", [])
    first_batch = batches[0] if batches else {}
    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "decision_path": _relative(decision_path),
        "hypothesis_id": decision.get("hypothesis_id"),
        "evidence_tier": decision.get("evidence_tier"),
        "experiment_id": decision.get("experiment_id"),
        "selected_key_env_for_next_metadata_estimate": decision.get("selected_key_env_for_next_metadata_estimate"),
        "candidate_batch_count": len(batches),
        "first_batch_id": first_batch.get("batch_id"),
        "first_batch_dates": first_batch.get("dates", []),
        "first_batch_expected_trading_days": first_batch.get("expected_trading_days_from_local_vix"),
        "network_allowed": decision.get("guardrails", {}).get("network_allowed"),
        "paid_data_allowed": decision.get("guardrails", {}).get("paid_data_allowed"),
        "live_cost_estimate_allowed_by_this_artifact": decision.get("guardrails", {}).get(
            "live_cost_estimate_allowed_by_this_artifact"
        ),
        "paper_trading_allowed": decision.get("guardrails", {}).get("paper_trading_allowed"),
    }


def _validate_source_paths(decision: dict[str, Any], blockers: list[str]) -> None:
    for source in decision.get("source_decisions", []):
        if not (PROJECT_ROOT / source).exists():
            blockers.append(f"source_decision_missing:{source}")
    for path in [VIX_PATH, MACRO_PATH]:
        if not path.exists():
            blockers.append(f"required_local_source_missing:{_relative(path)}")


def _validate_user_decision(decision: dict[str, Any], blockers: list[str]) -> None:
    record = decision.get("user_decision_record", {})
    if record.get("decision") != "normal_control_samples_next":
        blockers.append("user_decision_must_be_normal_control_samples_next")
    if "normal/control" not in record.get("reason", ""):
        blockers.append("user_decision_reason_must_reference_normal_control")


def _validate_superseded_sequence(decision: dict[str, Any], blockers: list[str]) -> None:
    supersedes = decision.get("supersedes_sequence", {})
    if supersedes.get("old_first_batch") != "sample_cost_probe_high_vix_one_day":
        blockers.append("old_first_batch_must_be_high_vix_one_day")
    if supersedes.get("new_first_batch") != "low_normal_vix_control_pack":
        blockers.append("new_first_batch_must_be_low_normal_control")
    if supersedes.get("high_vix_path_status") != "paused_until_normal_control_evidence_exists":
        blockers.append("high_vix_path_status_must_be_paused")


def _validate_locked_signal(decision: dict[str, Any], blockers: list[str]) -> None:
    signal = decision.get("locked_signal_under_validation", {})
    if signal.get("candidate_decision_time_et") != "09:35:00":
        blockers.append("candidate_decision_time_must_be_0935")
    if signal.get("entry_time_et") != "09:35:00":
        blockers.append("entry_time_must_be_0935")
    if signal.get("features") != ["clean_macro_vix_condition", "proxy_5m_followthrough"]:
        blockers.append("features_must_match_locked_signal")
    if signal.get("opening_followthrough_threshold") != 0.001:
        blockers.append("locked_threshold_must_be_0_001")
    for field in [
        "threshold_search_allowed",
        "oos_tuning_allowed",
        "new_oos_selected_filter_allowed",
        "fifteen_minute_conflict_component_allowed",
        "delayed_entry_component_allowed",
    ]:
        if signal.get(field) is not False:
            blockers.append(f"{field}_must_be_false")
    if signal.get("threshold_must_remain_locked") is not True:
        blockers.append("threshold_must_remain_locked_must_be_true")


def _validate_budget(decision: dict[str, Any], blockers: list[str]) -> None:
    if decision.get("selected_key_env_for_next_metadata_estimate") != "DATABENTO_API_MO":
        blockers.append("selected_key_env_must_be_databento_api_mo")
    budget = decision.get("budget_policy_snapshot", {})
    if budget.get("mo_ai_combined_pool_cap_usd") != 200.0:
        blockers.append("mo_ai_combined_pool_cap_must_be_200")
    if budget.get("selected_key_cap_usd") != 100.0:
        blockers.append("selected_key_cap_must_be_100")
    if budget.get("selected_key_env_logged_without_value") is not True:
        blockers.append("selected_key_env_logged_without_value_must_be_true")
    if budget.get("download_requires_separate_decision") is not True:
        blockers.append("download_requires_separate_decision_must_be_true")


def _validate_batches(decision: dict[str, Any], blockers: list[str]) -> None:
    batches = decision.get("candidate_estimate_batches", [])
    expected_ids = ["low_normal_vix_control_pack", "post_stress_normalization_control_pack"]
    if [batch.get("batch_id") for batch in batches] != expected_ids:
        blockers.append("candidate_batches_must_be_normal_control_first")
    if len(batches) != 2:
        blockers.append("candidate_batch_count_must_be_2")
    vix_by_date = _load_vix_by_date()
    high_macro_dates = _load_high_importance_macro_dates()
    for batch in batches:
        dates = batch.get("dates", [])
        if len(dates) != batch.get("expected_trading_days_from_local_vix"):
            blockers.append(f"batch_date_count_mismatch:{batch.get('batch_id')}")
        if batch.get("estimate_only_next") is not True:
            blockers.append(f"batch_must_be_estimate_only_next:{batch.get('batch_id')}")
        if batch.get("download_allowed_by_this_artifact") is not False:
            blockers.append(f"batch_download_must_be_false:{batch.get('batch_id')}")
        local_vix_values = []
        local_vxv_values = []
        for date_text in dates:
            row = vix_by_date.get(date_text)
            if row is None:
                blockers.append(f"batch_date_missing_vix:{batch.get('batch_id')}:{date_text}")
                continue
            vix = float(row["vix_close"])
            vxv = float(row["vxv_close"])
            local_vix_values.append(vix)
            local_vxv_values.append(vxv)
            if vix >= 25.0:
                blockers.append(f"batch_date_not_normal_control_vix:{batch.get('batch_id')}:{date_text}")
            if date_text in high_macro_dates:
                blockers.append(f"batch_date_has_high_importance_macro:{batch.get('batch_id')}:{date_text}")
        if local_vix_values:
            expected_range = [round(min(local_vix_values), 2), round(max(local_vix_values), 2)]
            if batch.get("vix_context", {}).get("observed_vix_close_range") != expected_range:
                blockers.append(f"batch_vix_range_mismatch:{batch.get('batch_id')}")
        if local_vxv_values:
            expected_range = [round(min(local_vxv_values), 2), round(max(local_vxv_values), 2)]
            if batch.get("vix_context", {}).get("observed_vxv_close_range") != expected_range:
                blockers.append(f"batch_vxv_range_mismatch:{batch.get('batch_id')}")
        if batch.get("macro_context", {}).get("high_importance_macro_days_from_local_calendar") != 0:
            blockers.append(f"batch_high_macro_count_must_be_zero:{batch.get('batch_id')}")


def _validate_required_fields(decision: dict[str, Any], blockers: list[str]) -> None:
    groups = {field.get("field_group"): field for field in decision.get("required_fields", [])}
    for group in ["option_entry_quote", "option_exit_quotes", "spy_underlying_bars", "existing_regime_labels"]:
        if group not in groups:
            blockers.append(f"missing_required_field_group:{group}")
    if groups.get("option_entry_quote", {}).get("dataset") != "OPRA.PILLAR":
        blockers.append("option_entry_quote_dataset_must_be_opra")
    if groups.get("option_exit_quotes", {}).get("schema") != "cbbo-1m":
        blockers.append("option_exit_quotes_schema_must_be_cbbo_1m")
    if groups.get("spy_underlying_bars", {}).get("dataset") != "EQUS.MINI":
        blockers.append("spy_underlying_bars_dataset_must_be_equs_mini")
    if "09:30-09:40" not in groups.get("option_entry_quote", {}).get("windows_et", []):
        blockers.append("entry_quote_window_must_include_0930_0940")
    if "15:45" not in groups.get("option_exit_quotes", {}).get("windows_et", []):
        blockers.append("exit_quote_windows_must_include_1545")


def _validate_future_execution(decision: dict[str, Any], blockers: list[str]) -> None:
    future = decision.get("future_execution_sequence", {})
    if "metadata-only" not in future.get("next_step", ""):
        blockers.append("future_next_step_must_be_metadata_only")
    if "DATABENTO_API_MO" not in future.get("next_step", ""):
        blockers.append("future_next_step_must_log_selected_key")
    if future.get("estimate_scope") != "metadata_only":
        blockers.append("estimate_scope_must_be_metadata_only")
    if future.get("estimate_batch_order") != [
        "low_normal_vix_control_pack",
        "post_stress_normalization_control_pack",
    ]:
        blockers.append("estimate_batch_order_must_be_normal_control_first")
    if len(future.get("download_forbidden_until", [])) < 4:
        blockers.append("download_forbidden_until_too_short")
    forbidden = "\n".join(future.get("do_not_do", []))
    for phrase in ["broad 2025 calendar", "high-VIX-first", "0.001", "OOS-selected", "paper trading"]:
        if phrase not in forbidden:
            blockers.append(f"missing_future_do_not_do_phrase:{phrase}")


def _validate_claims_and_guardrails(decision: dict[str, Any], blockers: list[str]) -> None:
    guardrails = decision.get("guardrails", {})
    for field in [
        "network_allowed",
        "paid_data_allowed",
        "live_cost_estimate_allowed_by_this_artifact",
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
        "research_log_required_for_this_preregistration",
    ]:
        if guardrails.get(field) is not False:
            blockers.append(f"{field}_must_be_false")

    allowed = "\n".join(decision.get("allowed_claims", []))
    for phrase in ["normal/control", "high-VIX-first", "metadata-only", "09:35-only", "0.001"]:
        if phrase not in allowed:
            blockers.append(f"missing_allowed_claim_phrase:{phrase}")
    forbidden = "\n".join(decision.get("forbidden_claims", []))
    for phrase in [
        "edge is validated",
        "E2",
        "paper trading",
        "paid data",
        "live Databento",
        "IBKR",
        "LLMs",
        "GDELT",
        "0.001",
        "OOS-selected",
        "sample-decision planning",
    ]:
        if phrase not in forbidden:
            blockers.append(f"missing_forbidden_claim_phrase:{phrase}")
    completion = "\n".join(decision.get("completion_criteria", []))
    for phrase in ["exact normal/control sample dates", "VIX below 25", "selected Databento key", "09:35-only", "validator passes"]:
        if phrase not in completion:
            blockers.append(f"missing_completion_criterion_phrase:{phrase}")


def _load_vix_by_date() -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for line in VIX_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        rows[str(row["date"])] = row
    return rows


def _load_high_importance_macro_dates() -> set[str]:
    dates: set[str] = set()
    for line in MACRO_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("importance") != "high":
            continue
        date_text = row.get("event_date") or row.get("date") or str(row.get("timestamp_et", ""))[:10]
        if date_text:
            dates.add(str(date_text))
    return dates


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate H-A2 normal/control sample decision.")
    parser.add_argument("--decision-path", type=Path, default=DEFAULT_DECISION_PATH)
    args = parser.parse_args(argv)

    result = validate_h_a2_normal_control_sample_decision(args.decision_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
