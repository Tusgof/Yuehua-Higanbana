from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUMMARY_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_normal_control_import_diagnostic.json"
EXPECTED_DATES = [
    "2025-02-03",
    "2025-02-04",
    "2025-02-05",
    "2025-02-06",
    "2025-02-07",
    "2025-02-10",
    "2025-02-11",
    "2025-02-12",
    "2025-02-13",
    "2025-02-14",
]


def validate_h_a2_normal_control_import_diagnostic(
    summary_path: Path = DEFAULT_SUMMARY_PATH,
) -> dict[str, Any]:
    summary = _load_json(summary_path)
    blockers: list[str] = []

    if summary.get("schema_version") != "h_a2_normal_control_import_diagnostic_v1":
        blockers.append("unsupported_schema_version")
    if summary.get("record_type") != "experiment_summary":
        blockers.append("record_type_must_be_experiment_summary")
    if summary.get("experiment_id") != "h_a2_normal_control_import_diagnostic":
        blockers.append("experiment_id_must_match")
    if summary.get("hypothesis_id") != "H-A2":
        blockers.append("hypothesis_id_must_be_h_a2")
    if summary.get("evidence_tier") != "E1":
        blockers.append("evidence_tier_must_be_e1")
    if summary.get("status") != "complete":
        blockers.append("status_must_be_complete")
    if summary.get("conclusion") != "ยังสรุปไม่ได้":
        blockers.append("conclusion_must_be_inconclusive")

    _validate_guardrails(summary, blockers)
    _validate_methodology(summary, blockers)
    _validate_imports(summary, blockers)
    _validate_date_diagnostics(summary, blockers)
    _validate_decision(summary, blockers)

    aggregate = summary.get("aggregate_diagnostic", {})
    decision = summary.get("diagnostic_decision", {})
    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "summary_path": _relative(summary_path),
        "experiment_id": summary.get("experiment_id"),
        "hypothesis_id": summary.get("hypothesis_id"),
        "evidence_tier": summary.get("evidence_tier"),
        "decision": decision.get("decision"),
        "date_count": aggregate.get("date_count"),
        "locked_signal_true_count": aggregate.get("locked_signal_true_count"),
        "candidate_trade_data_ready_count": aggregate.get("candidate_trade_data_ready_count"),
        "research_log_required": summary.get("research_log_required"),
        "next_safe_action": summary.get("next_safe_action"),
    }


def _validate_guardrails(summary: dict[str, Any], blockers: list[str]) -> None:
    for field in [
        "network_used",
        "paid_data_used",
        "additional_download_used",
        "new_provider_used",
        "broker_request_used",
        "ibkr_request_used",
        "gdelt_live_retry_used",
        "llm_call_used",
        "exact_replay_used",
        "strategy_pnl_computed",
        "paper_trading_allowed",
        "operational_validation_allowed",
        "real_money_allowed",
        "strategy_use_allowed",
    ]:
        if summary.get(field) is not False:
            blockers.append(f"{field}_must_be_false")


def _validate_methodology(summary: dict[str, Any], blockers: list[str]) -> None:
    methodology = summary.get("methodology", {})
    if methodology.get("local_raw_dbn_only") is not True:
        blockers.append("local_raw_dbn_only_must_be_true")
    if methodology.get("candidate_decision_time_et") != "09:35:00":
        blockers.append("candidate_decision_time_must_be_0935")
    if methodology.get("entry_time_et") != "09:35:00":
        blockers.append("entry_time_must_be_0935")
    if methodology.get("locked_threshold") != 0.001:
        blockers.append("locked_threshold_must_be_0_001")
    if methodology.get("used_features") != ["clean_macro_vix_condition", "proxy_5m_followthrough"]:
        blockers.append("used_features_must_match_locked_h_a2_rule")
    for field in [
        "threshold_search_used",
        "oos_tuning_used",
        "new_oos_selected_filter_used",
        "fifteen_minute_conflict_component_used",
        "delayed_entry_component_used",
        "exact_replay_used",
        "strategy_pnl_computed",
    ]:
        if methodology.get(field) is not False:
            blockers.append(f"{field}_must_be_false")


def _validate_imports(summary: dict[str, Any], blockers: list[str]) -> None:
    raw = summary.get("raw_file_inventory", {})
    if raw.get("status") != "pass":
        blockers.append("raw_file_inventory_must_pass")
    if raw.get("actual_file_count") != 20:
        blockers.append("raw_file_count_must_be_20")
    if raw.get("actual_dates") != EXPECTED_DATES:
        blockers.append("raw_file_dates_must_match_expected")
    if raw.get("total_actual_bytes") != 741157996:
        blockers.append("total_actual_bytes_must_match_download_result")

    spy = summary.get("spy_underlying_import", {})
    if spy.get("status") != "pass":
        blockers.append("spy_underlying_import_must_pass")
    if spy.get("date_count") != 10:
        blockers.append("spy_date_count_must_be_10")
    if spy.get("dates_with_0935_bar") != 10:
        blockers.append("all_spy_dates_must_have_0935")
    if spy.get("dates_with_1545_bar") != 10:
        blockers.append("all_spy_dates_must_have_1545")

    quotes = summary.get("opra_quote_import", {})
    if quotes.get("status") != "pass":
        blockers.append("opra_quote_import_must_pass")
    if quotes.get("date_count") != 10:
        blockers.append("quote_date_count_must_be_10")
    if not isinstance(quotes.get("total_row_count"), int) or quotes.get("total_row_count", 0) <= 0:
        blockers.append("quote_total_row_count_must_be_positive")
    if not isinstance(quotes.get("total_zero_dte_valid_mid_row_count"), int) or quotes.get("total_zero_dte_valid_mid_row_count", 0) <= 0:
        blockers.append("zero_dte_valid_mid_rows_must_be_positive")
    if quotes.get("dates_with_entry_0935_valid_mid") != 10:
        blockers.append("all_quote_dates_must_have_entry_0935_valid_mid")
    if quotes.get("dates_with_forced_close_1545_valid_mid") != 10:
        blockers.append("all_quote_dates_must_have_forced_close_1545_valid_mid")

    timestamp = summary.get("timestamp_alignment_check", {})
    if timestamp.get("status") != "pass":
        blockers.append("timestamp_alignment_must_pass")
    if timestamp.get("no_post_0935_features_used_for_signal") is not True:
        blockers.append("signal_must_not_use_post_0935_features")


def _validate_date_diagnostics(summary: dict[str, Any], blockers: list[str]) -> None:
    rows = summary.get("date_diagnostics", [])
    if [row.get("date") for row in rows] != EXPECTED_DATES:
        blockers.append("date_diagnostics_must_match_expected_dates")
    for row in rows:
        date_text = row.get("date", "unknown")
        signal = row.get("candidate_signal_reconstruction", {})
        availability = row.get("entry_exit_quote_availability", {})
        timestamp = row.get("timestamp_alignment_check", {})
        if signal.get("candidate_decision_time_et") != "09:35:00":
            blockers.append(f"signal_decision_time_must_be_0935:{date_text}")
        if signal.get("locked_threshold") != 0.001:
            blockers.append(f"signal_locked_threshold_must_be_0_001:{date_text}")
        if timestamp.get("status") != "pass":
            blockers.append(f"timestamp_alignment_must_pass:{date_text}")
        if availability.get("exact_replay_used") is not False or availability.get("strategy_pnl_computed") is not False:
            blockers.append(f"availability_must_not_use_exact_replay_or_pnl:{date_text}")


def _validate_decision(summary: dict[str, Any], blockers: list[str]) -> None:
    aggregate = summary.get("aggregate_diagnostic", {})
    if aggregate.get("date_count") != 10:
        blockers.append("aggregate_date_count_must_be_10")
    for field in [
        "locked_signal_true_count",
        "candidate_trade_data_ready_count",
        "candidate_trade_data_blocked_count",
        "no_candidate_trade_signal_count",
    ]:
        if not isinstance(aggregate.get(field), int):
            blockers.append(f"aggregate_{field}_must_be_int")

    ready = int(aggregate.get("candidate_trade_data_ready_count", 0))
    blocked = int(aggregate.get("candidate_trade_data_blocked_count", 0))
    no_signal = int(aggregate.get("no_candidate_trade_signal_count", 0))
    if ready + blocked + no_signal != 10:
        blockers.append("availability_counts_must_sum_to_10")

    decision = summary.get("diagnostic_decision", {})
    if decision.get("status") != "complete":
        blockers.append("diagnostic_decision_must_complete")
    if decision.get("evidence_tier_cap") != "E1":
        blockers.append("decision_evidence_tier_cap_must_be_e1")
    if decision.get("paper_trading_allowed") is not False:
        blockers.append("decision_paper_trading_allowed_must_be_false")
    if decision.get("e2_status") != "forbidden":
        blockers.append("decision_e2_status_must_be_forbidden")
    if summary.get("research_log_required") is not True:
        blockers.append("research_log_required_must_be_true")
    if "E2 acceptance claim" not in "\n".join(summary.get("tier_blockers", [])):
        blockers.append("tier_blockers_must_forbid_e2")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate H-A2 normal/control import diagnostic output.")
    parser.add_argument("--summary-path", type=Path, default=DEFAULT_SUMMARY_PATH)
    args = parser.parse_args(argv)
    result = validate_h_a2_normal_control_import_diagnostic(args.summary_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
