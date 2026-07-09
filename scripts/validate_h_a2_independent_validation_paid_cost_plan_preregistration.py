from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PREREG_PATH = (
    PROJECT_ROOT / "experiments" / "h_a2_independent_validation_paid_cost_plan_preregistration.json"
)
H_A2_DOWNLOAD_RESULT_PATH = (
    PROJECT_ROOT
    / "reports"
    / "data_cost"
    / "databento_download_result_h_a2_independent_validation_2025_04_08.json"
)


def validate_h_a2_independent_validation_paid_cost_plan_preregistration(
    prereg_path: Path = DEFAULT_PREREG_PATH,
) -> dict[str, Any]:
    prereg = _load_json(prereg_path)
    blockers: list[str] = []

    if prereg.get("schema_version") != "h_a2_independent_validation_paid_cost_plan_preregistration_v1":
        blockers.append("unsupported_schema_version")
    if prereg.get("artifact_type") != "preregistration":
        blockers.append("artifact_type_must_be_preregistration")
    if prereg.get("hypothesis_id") != "H-A2":
        blockers.append("hypothesis_id_must_be_h_a2")
    if prereg.get("status") != "preregistered":
        blockers.append("status_must_be_preregistered")
    if prereg.get("evidence_tier") != "E0":
        blockers.append("evidence_tier_must_be_e0")
    if prereg.get("experiment_id") != "h_a2_independent_validation_paid_cost_plan":
        blockers.append("experiment_id_must_match")
    if prereg.get("source_decision") != "reports/diagnostics/h_a2_independent_validation_feasibility.json":
        blockers.append("source_decision_must_be_h_a2_36_summary")

    _validate_source_paths(prereg, blockers)
    _validate_locked_signal(prereg, blockers)
    _validate_validation_gaps(prereg, blockers)
    _validate_batches(prereg, blockers)
    _validate_required_fields(prereg, blockers)
    _validate_cost_guard(prereg, blockers)
    _validate_claims_and_guardrails(prereg, blockers)

    batches = prereg.get("candidate_estimate_batches", [])
    cost_guard = prereg.get("cost_guard_preconditions", {})
    guardrails = prereg.get("guardrails", {})
    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "prereg_path": _relative(prereg_path),
        "hypothesis_id": prereg.get("hypothesis_id"),
        "evidence_tier": prereg.get("evidence_tier"),
        "experiment_id": prereg.get("experiment_id"),
        "candidate_batch_count": len(batches),
        "first_batch_id": batches[0].get("batch_id") if batches else None,
        "current_remaining_before_stop_usd": cost_guard.get("current_remaining_before_stop_usd"),
        "network_allowed": guardrails.get("network_allowed"),
        "paid_data_allowed": guardrails.get("paid_data_allowed"),
        "live_cost_estimate_allowed": guardrails.get("live_cost_estimate_allowed"),
        "ibkr_request_allowed": guardrails.get("ibkr_request_allowed"),
        "llm_call_allowed": guardrails.get("llm_call_allowed"),
        "paper_trading_allowed": guardrails.get("paper_trading_allowed"),
    }


def _validate_source_paths(prereg: dict[str, Any], blockers: list[str]) -> None:
    for item in prereg.get("allowed_inputs", []):
        path = item.get("path")
        if not path:
            blockers.append(f"allowed_input_missing_path:{item.get('input')}")
            continue
        if not (PROJECT_ROOT / path).exists():
            blockers.append(f"allowed_input_path_missing:{item.get('input')}")

    forbidden_inputs = {item.get("input") for item in prereg.get("forbidden_inputs", [])}
    for required in [
        "live_databento_estimate",
        "paid_databento_download",
        "new_paid_provider",
        "ibkr_historical_bars",
        "live_llm_outputs",
        "gdelt_live_retry",
        "new_oos_selected_filter",
    ]:
        if required not in forbidden_inputs:
            blockers.append(f"missing_forbidden_input:{required}")


def _validate_locked_signal(prereg: dict[str, Any], blockers: list[str]) -> None:
    signal = prereg.get("locked_signal_under_validation", {})
    if signal.get("candidate_decision_time_et") != "09:35:00":
        blockers.append("candidate_decision_time_must_be_0935")
    if signal.get("entry_time_et") != "09:35:00":
        blockers.append("entry_time_must_be_0935")
    if signal.get("features") != ["clean_macro_vix_condition", "proxy_5m_followthrough"]:
        blockers.append("features_must_match_locked_original_entry_signal")
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


def _validate_validation_gaps(prereg: dict[str, Any], blockers: list[str]) -> None:
    gap_ids = {gap.get("gap_id") for gap in prereg.get("named_validation_gaps", [])}
    for gap_id in ["independent_post_2024_sample", "high_vix_retained_bucket", "mintrl_psr_acceptance_path"]:
        if gap_id not in gap_ids:
            blockers.append(f"missing_validation_gap:{gap_id}")


def _validate_batches(prereg: dict[str, Any], blockers: list[str]) -> None:
    batches = prereg.get("candidate_estimate_batches", [])
    if len(batches) != 4:
        blockers.append("candidate_estimate_batch_count_must_be_4")
    batch_ids = [batch.get("batch_id") for batch in batches]
    required_order = [
        "sample_cost_probe_high_vix_one_day",
        "high_vix_validation_pack",
        "low_normal_vix_control_pack",
        "post_stress_normalization_control_pack",
    ]
    if batch_ids != required_order:
        blockers.append("candidate_estimate_batches_must_follow_required_order")
    for batch in batches:
        if batch.get("estimate_only") is not True:
            blockers.append(f"batch_must_be_estimate_only:{batch.get('batch_id')}")
        if batch.get("download_allowed") is not False:
            blockers.append(f"batch_download_must_be_false:{batch.get('batch_id')}")
        if not batch.get("vix_context", {}).get("source"):
            blockers.append(f"batch_missing_vix_source:{batch.get('batch_id')}")
    high_vix_dates = set(batches[1].get("dates", [])) if len(batches) > 1 else set()
    for required_date in ["2025-04-04", "2025-04-07", "2025-04-08", "2025-04-09", "2025-04-10", "2025-04-11"]:
        if required_date not in high_vix_dates:
            blockers.append(f"missing_high_vix_date:{required_date}")


def _validate_required_fields(prereg: dict[str, Any], blockers: list[str]) -> None:
    groups = {field.get("field_group"): field for field in prereg.get("required_fields", [])}
    for group in ["option_entry_quote", "option_exit_quotes", "spy_underlying_bars", "existing_regime_labels"]:
        if group not in groups:
            blockers.append(f"missing_required_field_group:{group}")
    if groups.get("option_entry_quote", {}).get("dataset") != "OPRA.PILLAR":
        blockers.append("option_entry_quote_dataset_must_be_opra")
    if groups.get("spy_underlying_bars", {}).get("dataset") != "EQUS.MINI":
        blockers.append("spy_underlying_bars_dataset_must_be_equs_mini")
    if "09:30-09:40" not in groups.get("option_entry_quote", {}).get("windows_et", []):
        blockers.append("entry_quote_window_must_include_0930_0940")
    if "15:45" not in groups.get("option_exit_quotes", {}).get("windows_et", []):
        blockers.append("exit_quote_windows_must_include_1545")


def _validate_cost_guard(prereg: dict[str, Any], blockers: list[str]) -> None:
    cost = prereg.get("cost_guard_preconditions", {})
    if cost.get("provider") != "Databento":
        blockers.append("provider_must_be_databento")
    if cost.get("symbol_scope") != "SPY only":
        blockers.append("symbol_scope_must_be_spy_only")
    if cost.get("stop_threshold_usd") != 125.0:
        blockers.append("stop_threshold_must_be_125")
    paid_audit_path = PROJECT_ROOT / "reports" / "data_cost" / "paid_cost_audit.json"
    if paid_audit_path.exists():
        paid = _load_json(paid_audit_path)
        accepted_cost_states = [
            {
                "current_cost_guard_used_usd": paid.get("cost_guard_used_usd"),
                "current_remaining_before_stop_usd": paid.get("remaining_before_stop_usd"),
                "stop_threshold_usd": paid.get("stop_threshold_usd"),
            }
        ]
        if H_A2_DOWNLOAD_RESULT_PATH.exists():
            download = _load_json(H_A2_DOWNLOAD_RESULT_PATH)
            before = download.get("paid_cost_audit_before_download", {})
            if before:
                accepted_cost_states.append(
                    {
                        "current_cost_guard_used_usd": before.get("cost_guard_used_usd"),
                        "current_remaining_before_stop_usd": before.get("remaining_before_stop_usd"),
                        "stop_threshold_usd": paid.get("stop_threshold_usd"),
                    }
                )
        prereg_cost_state = {
            "current_cost_guard_used_usd": cost.get("current_cost_guard_used_usd"),
            "current_remaining_before_stop_usd": cost.get("current_remaining_before_stop_usd"),
            "stop_threshold_usd": cost.get("stop_threshold_usd"),
        }
        if prereg_cost_state not in accepted_cost_states:
            blockers.append("cost_guard_mismatch:historical_or_current_guard")
    if cost.get("live_metadata_estimate_allowed_by_this_preregistration") is not False:
        blockers.append("live_metadata_estimate_allowed_by_this_preregistration_must_be_false")
    if cost.get("paid_download_allowed_by_this_preregistration") is not False:
        blockers.append("paid_download_allowed_by_this_preregistration_must_be_false")
    if len(cost.get("future_live_estimate_may_start_only_if", [])) < 5:
        blockers.append("future_live_estimate_preconditions_too_short")
    if len(cost.get("future_download_forbidden_until", [])) < 4:
        blockers.append("future_download_forbidden_until_too_short")


def _validate_claims_and_guardrails(prereg: dict[str, Any], blockers: list[str]) -> None:
    sequence = prereg.get("estimate_sequence_rules", {})
    if sequence.get("first_step") != "Estimate sample_cost_probe_high_vix_one_day only.":
        blockers.append("first_estimate_step_must_be_one_day_high_vix")
    for phrase in ["broad 2025 calendar", "non-SPY universe", "new paid provider", "download command"]:
        if phrase not in sequence.get("never_estimate", []):
            blockers.append(f"missing_never_estimate:{phrase}")

    outputs = prereg.get("future_outputs_if_estimate_runner_is_built", {})
    for key in ["cost_plan_json", "cost_plan_md", "live_estimate_json", "live_estimate_md"]:
        if not outputs.get(key):
            blockers.append(f"missing_future_output:{key}")

    allowed = "\n".join(prereg.get("allowed_claims", []))
    for phrase in ["pre-registered", "exact independent validation windows", "metadata-only cost estimate", "09:35-only", "0.001"]:
        if phrase not in allowed:
            blockers.append(f"missing_allowed_claim_phrase:{phrase}")

    forbidden = "\n".join(prereg.get("forbidden_claims", []))
    for phrase in [
        "edge is validated",
        "E2",
        "paper trading",
        "exact replay",
        "paid data",
        "live Databento estimates",
        "IBKR",
        "LLMs",
        "GDELT",
        "0.001",
        "OOS-selected",
        "cost-estimate planning",
    ]:
        if phrase not in forbidden:
            blockers.append(f"missing_forbidden_claim_phrase:{phrase}")

    guardrails = prereg.get("guardrails", {})
    for field in [
        "network_allowed",
        "paid_data_allowed",
        "live_cost_estimate_allowed",
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

    completion = "\n".join(prereg.get("completion_criteria", []))
    for phrase in ["exact windows", "required fields", "cost guard", "09:35-only", "0.001", "validator passes"]:
        if phrase not in completion:
            blockers.append(f"missing_completion_criterion_phrase:{phrase}")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate H-A2 independent-validation paid-cost plan preregistration."
    )
    parser.add_argument("--prereg-path", type=Path, default=DEFAULT_PREREG_PATH)
    args = parser.parse_args(argv)

    result = validate_h_a2_independent_validation_paid_cost_plan_preregistration(args.prereg_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
