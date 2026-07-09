from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUMMARY_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_independent_validation_import_diagnostic.json"


def validate_h_a2_independent_validation_import_diagnostic(
    summary_path: Path = DEFAULT_SUMMARY_PATH,
) -> dict[str, Any]:
    summary = _load_json(summary_path)
    blockers: list[str] = []

    if summary.get("schema_version") != "h_a2_independent_validation_import_diagnostic_v1":
        blockers.append("unsupported_schema_version")
    if summary.get("record_type") != "experiment_summary":
        blockers.append("record_type_must_be_experiment_summary")
    if summary.get("experiment_id") != "h_a2_independent_validation_import_diagnostic":
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
    _validate_signal_and_decision(summary, blockers)

    decision = summary.get("diagnostic_decision", {})
    signal = summary.get("candidate_signal_reconstruction", {})
    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "summary_path": _relative(summary_path),
        "experiment_id": summary.get("experiment_id"),
        "hypothesis_id": summary.get("hypothesis_id"),
        "evidence_tier": summary.get("evidence_tier"),
        "decision": decision.get("decision"),
        "locked_signal_true": signal.get("locked_signal_true"),
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
    ]:
        if methodology.get(field) is not False:
            blockers.append(f"{field}_must_be_false")


def _validate_imports(summary: dict[str, Any], blockers: list[str]) -> None:
    raw = summary.get("raw_file_inventory", {})
    if raw.get("status") != "pass":
        blockers.append("raw_file_inventory_must_pass")
    if raw.get("actual_file_count") != 15:
        blockers.append("raw_file_count_must_be_15")
    if raw.get("total_actual_bytes") != 54014593:
        blockers.append("total_actual_bytes_must_match_download_result")

    spy = summary.get("spy_underlying_import", {})
    if spy.get("status") != "pass":
        blockers.append("spy_underlying_import_must_pass")
    if spy.get("row_count") != 390:
        blockers.append("spy_bar_row_count_must_be_390")
    if spy.get("has_0935_bar") is not True:
        blockers.append("spy_bar_must_have_0935")
    if spy.get("has_1545_bar") is not True:
        blockers.append("spy_bar_must_have_1545")

    quotes = summary.get("opra_quote_import", {})
    if quotes.get("status") != "pass":
        blockers.append("opra_quote_import_must_pass")
    if quotes.get("window_count") != 14:
        blockers.append("quote_window_count_must_be_14")
    if not isinstance(quotes.get("total_row_count"), int) or quotes.get("total_row_count", 0) <= 0:
        blockers.append("quote_total_row_count_must_be_positive")
    if not isinstance(quotes.get("total_zero_dte_valid_mid_row_count"), int) or quotes.get("total_zero_dte_valid_mid_row_count", 0) <= 0:
        blockers.append("zero_dte_valid_mid_rows_must_be_positive")

    timestamp = summary.get("timestamp_alignment_check", {})
    if timestamp.get("status") != "pass":
        blockers.append("timestamp_alignment_must_pass")
    if timestamp.get("no_post_0935_features_used_for_signal") is not True:
        blockers.append("signal_must_not_use_post_0935_features")


def _validate_signal_and_decision(summary: dict[str, Any], blockers: list[str]) -> None:
    regimes = summary.get("regime_labels", {})
    if regimes.get("date") != "2025-04-08":
        blockers.append("regime_date_must_be_2025_04_08")
    if regimes.get("prior_high_vix") is not True:
        blockers.append("must_disclose_prior_high_vix_true")
    if regimes.get("clean_macro_vix_condition") is not False:
        blockers.append("clean_macro_vix_condition_must_be_false_for_high_vix_sample")

    signal = summary.get("candidate_signal_reconstruction", {})
    if signal.get("status") != "complete":
        blockers.append("signal_reconstruction_must_complete")
    if signal.get("candidate_decision_time_et") != "09:35:00":
        blockers.append("signal_decision_time_must_be_0935")
    if signal.get("locked_threshold") != 0.001:
        blockers.append("signal_locked_threshold_must_be_0_001")
    if signal.get("locked_signal_true") is not False:
        blockers.append("locked_signal_must_be_false_for_this_high_vix_sample")
    if "clean_macro_vix_condition_false" not in signal.get("blockers", []):
        blockers.append("signal_blockers_must_include_clean_macro_vix_condition_false")

    availability = summary.get("entry_exit_quote_availability", {})
    if availability.get("status") != "no_candidate_trade_signal":
        blockers.append("availability_must_be_no_candidate_trade_signal")
    if availability.get("exact_replay_used") is not False or availability.get("strategy_pnl_computed") is not False:
        blockers.append("availability_must_not_use_exact_replay_or_pnl")

    decision = summary.get("diagnostic_decision", {})
    if decision.get("decision") != "no_candidate_trade_signal_on_high_vix_sample":
        blockers.append("decision_must_be_no_candidate_trade_signal_on_high_vix_sample")
    if decision.get("evidence_tier_cap") != "E1":
        blockers.append("decision_evidence_tier_cap_must_be_e1")
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
    parser = argparse.ArgumentParser(description="Validate H-A2 independent-validation import diagnostic output.")
    parser.add_argument("--summary-path", type=Path, default=DEFAULT_SUMMARY_PATH)
    args = parser.parse_args(argv)
    result = validate_h_a2_independent_validation_import_diagnostic(args.summary_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
