from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PREREG_PATH = (
    PROJECT_ROOT / "experiments" / "h_a2_normal_control_exact_replay_preregistration.json"
)
SOURCE_SUMMARY_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_normal_control_import_diagnostic.json"
CANDIDATE_DATE = "2025-02-11"


def validate_h_a2_normal_control_exact_replay_preregistration(
    prereg_path: Path = DEFAULT_PREREG_PATH,
) -> dict[str, Any]:
    prereg = _load_json(prereg_path)
    blockers: list[str] = []

    if prereg.get("schema_version") != "h_a2_normal_control_exact_replay_preregistration_v1":
        blockers.append("unsupported_schema_version")
    if prereg.get("artifact_type") != "preregistration":
        blockers.append("artifact_type_must_be_preregistration")
    if prereg.get("hypothesis_id") != "H-A2":
        blockers.append("hypothesis_id_must_be_h_a2")
    if prereg.get("status") != "preregistered":
        blockers.append("status_must_be_preregistered")
    if prereg.get("evidence_tier") != "E0":
        blockers.append("evidence_tier_must_be_e0")
    if prereg.get("experiment_id") != "h_a2_normal_control_exact_replay":
        blockers.append("experiment_id_must_match")
    if prereg.get("source_import_diagnostic") != "reports/diagnostics/h_a2_normal_control_import_diagnostic.json":
        blockers.append("source_import_diagnostic_must_match_h_a2_48")

    _validate_source_import(prereg, blockers)
    _validate_candidate_scope(prereg, blockers)
    _validate_locked_signal(prereg, blockers)
    _validate_exact_replay_design(prereg, blockers)
    _validate_inputs(prereg, blockers)
    _validate_outputs_claims_guardrails(prereg, blockers)

    candidate_scope = prereg.get("candidate_scope", {})
    guardrails = prereg.get("guardrails", {})
    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "prereg_path": _relative(prereg_path),
        "hypothesis_id": prereg.get("hypothesis_id"),
        "evidence_tier": prereg.get("evidence_tier"),
        "experiment_id": prereg.get("experiment_id"),
        "candidate_dates": candidate_scope.get("candidate_dates"),
        "candidate_count": candidate_scope.get("candidate_count"),
        "candidate_direction": candidate_scope.get("candidate_direction_by_date", {}).get(CANDIDATE_DATE),
        "exact_replay_allowed_after_preregistration": guardrails.get(
            "candidate_date_exact_replay_allowed_after_preregistration"
        ),
        "candidate_trade_pnl_allowed_after_preregistration": guardrails.get(
            "candidate_trade_pnl_allowed_after_preregistration"
        ),
        "network_allowed": guardrails.get("network_allowed"),
        "paid_data_allowed": guardrails.get("paid_data_allowed"),
        "paper_trading_allowed": guardrails.get("paper_trading_allowed"),
        "e2_claim_allowed": guardrails.get("e2_claim_allowed"),
    }


def _validate_source_import(prereg: dict[str, Any], blockers: list[str]) -> None:
    source_path = PROJECT_ROOT / prereg.get("source_import_diagnostic", "")
    if source_path != SOURCE_SUMMARY_PATH:
        blockers.append("source_import_path_must_be_h_a2_48_summary")
    if not source_path.exists():
        blockers.append("source_import_diagnostic_missing")
        return

    summary = _load_json(source_path)
    if summary.get("status") != "complete":
        blockers.append("source_import_status_must_be_complete")
    if summary.get("experiment_id") != "h_a2_normal_control_import_diagnostic":
        blockers.append("source_import_experiment_id_must_match")
    if summary.get("evidence_tier") != "E1":
        blockers.append("source_import_evidence_tier_must_be_e1")
    if summary.get("conclusion") != "ยังสรุปไม่ได้":
        blockers.append("source_import_conclusion_must_be_inconclusive")
    if summary.get("exact_replay_used") is not False:
        blockers.append("source_import_must_not_have_exact_replay")
    if summary.get("strategy_pnl_computed") is not False:
        blockers.append("source_import_must_not_have_strategy_pnl")
    if summary.get("paper_trading_allowed") is not False:
        blockers.append("source_import_must_not_allow_paper_trading")
    if summary.get("diagnostic_decision", {}).get("decision") != (
        "normal_control_candidate_trade_data_ready_for_separate_preregistered_exact_replay"
    ):
        blockers.append("source_import_decision_must_require_separate_preregistered_exact_replay")

    aggregate = summary.get("aggregate_diagnostic", {})
    if aggregate.get("candidate_trade_data_ready_dates") != [CANDIDATE_DATE]:
        blockers.append("source_candidate_ready_dates_must_be_2025_02_11_only")
    if aggregate.get("candidate_trade_data_ready_count") != 1:
        blockers.append("source_candidate_ready_count_must_be_1")
    if aggregate.get("candidate_trade_data_blocked_count") != 0:
        blockers.append("source_candidate_blocked_count_must_be_0")
    if aggregate.get("no_candidate_trade_signal_count") != 9:
        blockers.append("source_no_signal_count_must_be_9")
    if summary.get("timestamp_alignment_check", {}).get("pass_count") != 10:
        blockers.append("source_timestamp_alignment_pass_count_must_be_10")

    candidate = _candidate_diag(summary)
    if not candidate:
        blockers.append("source_candidate_date_diagnostic_missing")
        return
    signal = candidate.get("candidate_signal_reconstruction", {})
    availability = candidate.get("entry_exit_quote_availability", {})
    if signal.get("candidate_direction") != "call":
        blockers.append("source_candidate_direction_must_be_call")
    if signal.get("locked_signal_true") is not True:
        blockers.append("source_candidate_locked_signal_must_be_true")
    if _round6(signal.get("locked_threshold")) != 0.001:
        blockers.append("source_candidate_threshold_must_be_0_001")
    if availability.get("status") != "candidate_trade_data_ready":
        blockers.append("source_candidate_availability_must_be_ready")
    if availability.get("candidate_direction_entry_rows", 0) <= 0:
        blockers.append("source_candidate_entry_rows_must_be_positive")
    if availability.get("candidate_direction_forced_close_rows", 0) <= 0:
        blockers.append("source_candidate_forced_close_rows_must_be_positive")


def _validate_candidate_scope(prereg: dict[str, Any], blockers: list[str]) -> None:
    scope = prereg.get("candidate_scope", {})
    if scope.get("batch_id") != "low_normal_vix_control_pack":
        blockers.append("candidate_batch_id_must_match")
    if scope.get("scenario") != "h_a2_normal_control_low_normal_vix_control_pack":
        blockers.append("candidate_scenario_must_match")
    if scope.get("candidate_dates") != [CANDIDATE_DATE]:
        blockers.append("candidate_dates_must_be_2025_02_11_only")
    if scope.get("candidate_count") != 1:
        blockers.append("candidate_count_must_be_1")
    if scope.get("candidate_direction_by_date") != {CANDIDATE_DATE: "call"}:
        blockers.append("candidate_direction_by_date_must_be_call")
    if scope.get("blocked_candidate_dates") != []:
        blockers.append("blocked_candidate_dates_must_be_empty")
    if scope.get("no_signal_dates_count") != 9:
        blockers.append("no_signal_dates_count_must_be_9")
    if scope.get("source_total_dates") != 10:
        blockers.append("source_total_dates_must_be_10")
    if scope.get("source_timestamp_alignment_pass_count") != 10:
        blockers.append("source_timestamp_alignment_pass_count_must_be_10")
    if scope.get("source_opra_quote_rows") != 35284142:
        blockers.append("source_opra_quote_rows_must_match")
    if scope.get("source_0dte_valid_mid_rows") != 557254:
        blockers.append("source_0dte_valid_mid_rows_must_match")


def _validate_locked_signal(prereg: dict[str, Any], blockers: list[str]) -> None:
    signal = prereg.get("locked_signal", {})
    if signal.get("candidate_decision_time_et") != "09:35:00":
        blockers.append("candidate_decision_time_must_be_0935")
    if signal.get("entry_time_et") != "09:35:00":
        blockers.append("entry_time_must_be_0935")
    if signal.get("forced_close_time_et") != "15:45:00":
        blockers.append("forced_close_time_must_be_1545")
    if signal.get("features") != ["clean_macro_vix_condition", "proxy_5m_followthrough"]:
        blockers.append("features_must_match_h_a2_locked_signal")
    if _round6(signal.get("opening_followthrough_threshold")) != 0.001:
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


def _validate_exact_replay_design(prereg: dict[str, Any], blockers: list[str]) -> None:
    design = prereg.get("exact_replay_design", {})
    if design.get("strategy_family") != "Sub-System A ORB directional debit vertical spread":
        blockers.append("strategy_family_must_be_subsystem_a_orb_debit_vertical")
    if design.get("scope") != "diagnostic replay for candidate date only":
        blockers.append("exact_replay_scope_must_be_candidate_date_only")
    if design.get("entry_order_assumption") != "limit_at_mid_control":
        blockers.append("entry_order_assumption_must_be_limit_at_mid_control")
    if design.get("exit_order_assumption") != "forced_close_1545":
        blockers.append("exit_order_assumption_must_be_forced_close_1545")
    if _round6(design.get("fees_per_leg_usd")) != 0.64:
        blockers.append("fees_per_leg_must_be_0_64")

    strike = design.get("strike_selection_rule", {})
    if strike.get("method") != "nearest_discrete_strike_rounding":
        blockers.append("strike_method_must_be_nearest_discrete_strike_rounding")
    if strike.get("interpolation_allowed") is not False:
        blockers.append("interpolation_allowed_must_be_false")
    if strike.get("post_result_strike_selection_allowed") is not False:
        blockers.append("post_result_strike_selection_allowed_must_be_false")
    if "existing baseline spread-width rule" not in strike.get("short_leg_rule", ""):
        blockers.append("short_leg_rule_must_reference_existing_baseline_width")

    requirements = "\n".join(design.get("reporting_requirements", []))
    for phrase in [
        "selected option symbols",
        "entry bid/ask/mid",
        "forced-close bid/ask/mid",
        "mid_pnl",
        "implementable_pnl",
        "fee and spread/cost drag",
        "E1 single-candidate diagnostic evidence",
    ]:
        if phrase not in requirements:
            blockers.append(f"missing_reporting_requirement:{phrase}")


def _validate_inputs(prereg: dict[str, Any], blockers: list[str]) -> None:
    for item in prereg.get("allowed_inputs", []):
        path = item.get("path")
        if not path:
            blockers.append(f"allowed_input_missing_path:{item.get('input')}")
            continue
        if not (PROJECT_ROOT / path).exists():
            blockers.append(f"allowed_input_path_missing:{item.get('input')}")

    forbidden_inputs = {item.get("input") for item in prereg.get("forbidden_inputs", [])}
    for required in [
        "additional_databento_download",
        "non_candidate_dates",
        "new_oos_selected_filter",
        "ibkr_historical_bars",
        "live_llm_outputs",
        "gdelt_live_retry",
    ]:
        if required not in forbidden_inputs:
            blockers.append(f"missing_forbidden_input:{required}")


def _validate_outputs_claims_guardrails(prereg: dict[str, Any], blockers: list[str]) -> None:
    outputs = prereg.get("planned_outputs", {})
    for key in ["future_summary_json", "future_summary_md", "future_search_log", "future_research_log_slug"]:
        if not outputs.get(key):
            blockers.append(f"missing_planned_output:{key}")

    allowed = "\n".join(prereg.get("allowed_claims", []))
    for phrase in ["2025-02-11", "mid_pnl", "implementable_pnl", "09:35", "0.001", "E1 diagnostic"]:
        if phrase not in allowed:
            blockers.append(f"missing_allowed_claim_phrase:{phrase}")

    forbidden = "\n".join(prereg.get("forbidden_claims", []))
    for phrase in [
        "edge is validated",
        "E2",
        "paper trading",
        "download more data",
        "0.001",
        "OOS-selected",
        "2025-02-11",
        "LLMs",
        "GDELT",
        "IBKR",
    ]:
        if phrase not in forbidden:
            blockers.append(f"missing_forbidden_claim_phrase:{phrase}")

    guardrails = prereg.get("guardrails", {})
    false_fields = [
        "network_allowed",
        "paid_data_allowed",
        "additional_download_allowed",
        "new_provider_allowed",
        "broker_request_allowed",
        "ibkr_request_allowed",
        "gdelt_live_retry_allowed",
        "llm_call_allowed",
        "non_candidate_replay_allowed",
        "threshold_search_allowed",
        "new_filter_allowed",
        "paper_trading_allowed",
        "operational_validation_allowed",
        "real_money_allowed",
        "e2_claim_allowed",
        "research_log_required_for_this_preregistration",
    ]
    for field in false_fields:
        if guardrails.get(field) is not False:
            blockers.append(f"{field}_must_be_false")

    true_fields = [
        "candidate_date_exact_replay_allowed_after_preregistration",
        "candidate_trade_pnl_allowed_after_preregistration",
        "research_log_required_for_future_run",
    ]
    for field in true_fields:
        if guardrails.get(field) is not True:
            blockers.append(f"{field}_must_be_true")

    completion = "\n".join(prereg.get("completion_criteria", []))
    for phrase in [
        "2025-02-11",
        "H-A2.48",
        "09:35",
        "15:45",
        "0.001",
        "mid_pnl",
        "implementable_pnl",
        "$0.64",
        "nearest discrete strike rounding",
        "validator passes",
    ]:
        if phrase not in completion:
            blockers.append(f"missing_completion_criterion_phrase:{phrase}")


def _candidate_diag(summary: dict[str, Any]) -> dict[str, Any] | None:
    for item in summary.get("date_diagnostics", []):
        if item.get("date") == CANDIDATE_DATE:
            return item
    return None


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
        description="Validate H-A2 normal/control exact replay preregistration."
    )
    parser.add_argument("--prereg-path", type=Path, default=DEFAULT_PREREG_PATH)
    args = parser.parse_args(argv)

    result = validate_h_a2_normal_control_exact_replay_preregistration(args.prereg_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
