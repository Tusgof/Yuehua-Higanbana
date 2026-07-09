from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DECISION_PATH = PROJECT_ROOT / "experiments" / "h_a2_post_exact_replay_sample_expansion_decision.json"
SOURCE_REPLAY_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_normal_control_exact_replay.json"
DOC_PATH = PROJECT_ROOT / "docs" / "H_A2_POST_EXACT_REPLAY_SAMPLE_EXPANSION_DECISION.md"
VIX_PATH = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "vix_vxv" / "vix_vxv.jsonl"
MACRO_PATH = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "macro_calendar" / "macro_event.jsonl"


def validate_h_a2_post_exact_replay_sample_expansion_decision(
    decision_path: Path = DEFAULT_DECISION_PATH,
) -> dict[str, Any]:
    decision = _load_json(decision_path)
    blockers: list[str] = []

    if decision.get("schema_version") != "h_a2_post_exact_replay_sample_expansion_decision_v1":
        blockers.append("unsupported_schema_version")
    if decision.get("artifact_type") != "decision_preregistration":
        blockers.append("artifact_type_must_be_decision_preregistration")
    if decision.get("hypothesis_id") != "H-A2":
        blockers.append("hypothesis_id_must_be_h_a2")
    if decision.get("status") != "preregistered":
        blockers.append("status_must_be_preregistered")
    if decision.get("evidence_tier") != "E0":
        blockers.append("evidence_tier_must_be_e0")
    if decision.get("experiment_id") != "h_a2_post_exact_replay_sample_expansion_decision":
        blockers.append("experiment_id_must_match")

    _validate_source_artifacts(decision, blockers)
    _validate_source_result(decision, blockers)
    _validate_decision(decision, blockers)
    _validate_locked_signal(decision, blockers)
    _validate_budget(decision, blockers)
    _validate_batches(decision, blockers)
    _validate_required_fields(decision, blockers)
    _validate_future_execution(decision, blockers)
    _validate_claims_and_guardrails(decision, blockers)

    batch = decision.get("candidate_estimate_batches", [{}])[0] if decision.get("candidate_estimate_batches") else {}
    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "decision_path": _relative(decision_path),
        "hypothesis_id": decision.get("hypothesis_id"),
        "evidence_tier": decision.get("evidence_tier"),
        "experiment_id": decision.get("experiment_id"),
        "selected_next_step": decision.get("decision", {}).get("selected_next_step"),
        "selected_key_env_for_next_metadata_estimate": decision.get("selected_key_env_for_next_metadata_estimate"),
        "candidate_batch_count": len(decision.get("candidate_estimate_batches", [])),
        "first_batch_id": batch.get("batch_id"),
        "first_batch_expected_trading_days": batch.get("expected_trading_days_from_local_vix"),
        "network_allowed": decision.get("guardrails", {}).get("network_allowed"),
        "paid_data_allowed": decision.get("guardrails", {}).get("paid_data_allowed"),
        "exact_replay_allowed": decision.get("guardrails", {}).get("exact_replay_allowed"),
        "paper_trading_allowed": decision.get("guardrails", {}).get("paper_trading_allowed"),
    }


def _validate_source_artifacts(decision: dict[str, Any], blockers: list[str]) -> None:
    for source in decision.get("source_artifacts", []):
        if not (PROJECT_ROOT / source).exists():
            blockers.append(f"source_artifact_missing:{source}")
    for path in [SOURCE_REPLAY_PATH, DOC_PATH, VIX_PATH, MACRO_PATH]:
        if not path.exists():
            blockers.append(f"required_source_missing:{_relative(path)}")


def _validate_source_result(decision: dict[str, Any], blockers: list[str]) -> None:
    source = _load_json(SOURCE_REPLAY_PATH)
    summary = decision.get("source_result_summary", {})
    expected = {
        "source_experiment": source.get("experiment_id"),
        "source_evidence_tier": source.get("evidence_tier"),
        "source_candidate_date": source.get("candidate", {}).get("date"),
        "source_direction": source.get("candidate", {}).get("direction"),
        "source_mid_pnl": source.get("pnl", {}).get("mid_pnl"),
        "source_implementable_pnl": source.get("pnl", {}).get("implementable_pnl"),
        "source_cost_drag_vs_mid": source.get("pnl", {}).get("cost_drag_vs_mid"),
        "source_sample_count": source.get("sample_policy", {}).get("sample_count"),
        "source_under_sampled": source.get("sample_policy", {}).get("under_sampled"),
        "source_underpowered": source.get("sample_policy", {}).get("underpowered"),
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            blockers.append(f"source_summary_mismatch:{key}")
    if source.get("status") != "complete":
        blockers.append("source_replay_must_be_complete")
    if source.get("paper_trading_allowed") is not False:
        blockers.append("source_paper_trading_must_be_false")
    if source.get("strategy_use_allowed") is not False:
        blockers.append("source_strategy_use_must_be_false")
    if summary.get("source_decision") != "continue_only_with_preregistered_sample_expansion":
        blockers.append("source_decision_must_continue_with_preregistered_sample_expansion")


def _validate_decision(decision: dict[str, Any], blockers: list[str]) -> None:
    body = decision.get("decision", {})
    if body.get("selected_next_step") != "metadata_estimate_post_stress_normalization_control_pack":
        blockers.append("selected_next_step_must_be_post_stress_metadata_estimate")
    reason = body.get("reason", "")
    for phrase in ["one candidate trade", "lost money", "does not falsify or validate", "metadata-only"]:
        if phrase not in reason:
            blockers.append(f"decision_reason_missing:{phrase}")
    if "separate download decision" not in body.get("why_not_download_now", ""):
        blockers.append("why_not_download_now_must_require_separate_decision")
    if "post-result tuning" not in body.get("why_not_change_threshold", ""):
        blockers.append("why_not_change_threshold_must_reference_post_result_tuning")
    if "normal/control" not in body.get("why_not_resume_high_vix_first", ""):
        blockers.append("why_not_resume_high_vix_first_must_reference_normal_control")


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
    if signal.get("threshold_must_remain_locked") is not True:
        blockers.append("threshold_must_remain_locked_must_be_true")
    for field in [
        "threshold_search_allowed",
        "oos_tuning_allowed",
        "new_oos_selected_filter_allowed",
        "fifteen_minute_conflict_component_allowed",
        "delayed_entry_component_allowed",
    ]:
        if signal.get(field) is not False:
            blockers.append(f"{field}_must_be_false")


def _validate_budget(decision: dict[str, Any], blockers: list[str]) -> None:
    if decision.get("selected_key_env_for_next_metadata_estimate") != "DATABENTO_API_AI":
        blockers.append("selected_key_env_must_be_databento_api_ai")
    budget = decision.get("budget_policy_snapshot", {})
    if budget.get("mo_ai_combined_pool_cap_usd") != 200.0:
        blockers.append("mo_ai_combined_pool_cap_must_be_200")
    if budget.get("selected_key_cap_usd") != 100.0:
        blockers.append("selected_key_cap_must_be_100")
    for field in ["selected_key_env_logged_without_value", "download_requires_separate_decision", "metadata_estimate_required_before_download"]:
        if budget.get(field) is not True:
            blockers.append(f"{field}_must_be_true")


def _validate_batches(decision: dict[str, Any], blockers: list[str]) -> None:
    batches = decision.get("candidate_estimate_batches", [])
    if len(batches) != 1:
        blockers.append("candidate_batch_count_must_be_1")
        return
    batch = batches[0]
    if batch.get("batch_id") != "post_stress_normalization_control_pack":
        blockers.append("batch_id_must_be_post_stress_normalization_control_pack")
    if batch.get("priority") != 1:
        blockers.append("batch_priority_must_be_1")
    if batch.get("estimate_only_next") is not True:
        blockers.append("batch_must_be_estimate_only_next")
    if batch.get("download_allowed_by_this_artifact") is not False:
        blockers.append("batch_download_must_be_false")
    dates = batch.get("dates", [])
    if len(dates) != batch.get("expected_trading_days_from_local_vix"):
        blockers.append("batch_date_count_mismatch")
    vix_by_date = _load_vix_by_date()
    high_macro_dates = _load_high_importance_macro_dates()
    local_vix_values: list[float] = []
    local_vxv_values: list[float] = []
    for date_text in dates:
        row = vix_by_date.get(str(date_text))
        if row is None:
            blockers.append(f"batch_date_missing_vix:{date_text}")
            continue
        vix = float(row["vix_close"])
        vxv = float(row["vxv_close"])
        local_vix_values.append(vix)
        local_vxv_values.append(vxv)
        if vix >= 25.0:
            blockers.append(f"batch_date_not_normal_control_vix:{date_text}")
        if str(date_text) in high_macro_dates:
            blockers.append(f"batch_date_has_high_importance_macro:{date_text}")
    if local_vix_values:
        expected_range = [round(min(local_vix_values), 2), round(max(local_vix_values), 2)]
        if batch.get("vix_context", {}).get("observed_vix_close_range") != expected_range:
            blockers.append("batch_vix_range_mismatch")
    if local_vxv_values:
        expected_range = [round(min(local_vxv_values), 2), round(max(local_vxv_values), 2)]
        if batch.get("vix_context", {}).get("observed_vxv_close_range") != expected_range:
            blockers.append("batch_vxv_range_mismatch")
    if batch.get("macro_context", {}).get("high_importance_macro_days_from_local_calendar") != 0:
        blockers.append("batch_high_macro_count_must_be_zero")


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
    next_step = future.get("next_step", "")
    if "metadata-only" not in next_step:
        blockers.append("future_next_step_must_be_metadata_only")
    if "post_stress_normalization_control_pack" not in next_step:
        blockers.append("future_next_step_must_name_batch")
    if "DATABENTO_API_AI" not in next_step:
        blockers.append("future_next_step_must_log_selected_key")
    if future.get("estimate_scope") != "metadata_only":
        blockers.append("estimate_scope_must_be_metadata_only")
    if future.get("estimate_batch_order") != ["post_stress_normalization_control_pack"]:
        blockers.append("estimate_batch_order_must_match")
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
    for phrase in ["E1 single-candidate", "metadata-only", "09:35-only", "0.001", "DATABENTO_API_AI"]:
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
        "sample-expansion planning",
    ]:
        if phrase not in forbidden:
            blockers.append(f"missing_forbidden_claim_phrase:{phrase}")
    completion = "\n".join(decision.get("completion_criteria", []))
    for phrase in ["H-A2.49", "exact normal/control sample dates", "VIX below 25", "selected Databento key", "09:35-only", "validator passes"]:
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
    parser = argparse.ArgumentParser(description="Validate H-A2 post exact-replay sample-expansion decision.")
    parser.add_argument("--decision-path", type=Path, default=DEFAULT_DECISION_PATH)
    args = parser.parse_args(argv)

    result = validate_h_a2_post_exact_replay_sample_expansion_decision(args.decision_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
