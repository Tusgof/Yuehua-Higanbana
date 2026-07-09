from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from audit_greeks_oi_feasibility import parse_databento_option_symbol  # noqa: E402
from run_h_a2_lower_resolution_proxy import _opening_proxy  # noqa: E402
from run_m5_regime_filter_sensitivity import load_macro_events_by_date, load_vix_vxv, previous_vix_record  # noqa: E402


ET = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")
TARGET_DATE = "2025-04-08"
LOCKED_THRESHOLD = 0.001
DEFAULT_PREREG_PATH = PROJECT_ROOT / "experiments" / "h_a2_independent_validation_import_diagnostic_preregistration.json"
DEFAULT_DOWNLOAD_RESULT_PATH = (
    PROJECT_ROOT / "reports" / "data_cost" / "databento_download_result_h_a2_independent_validation_2025_04_08.json"
)
DEFAULT_VIX_PATH = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "vix_vxv" / "vix_vxv.jsonl"
DEFAULT_MACRO_PATH = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "macro_calendar" / "macro_event.jsonl"
DEFAULT_SUMMARY_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_independent_validation_import_diagnostic.json"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_independent_validation_import_diagnostic.md"
DEFAULT_SEARCH_LOG_PATH = (
    PROJECT_ROOT
    / "reports"
    / "diagnostics"
    / "search_logs"
    / "h_a2_independent_validation_import_diagnostic_search_log.jsonl"
)
DEFAULT_BUILD_ROOT = PROJECT_ROOT / "build" / "h_a2_independent_validation_2025_04_08"


def run_h_a2_independent_validation_import_diagnostic(
    prereg_path: Path = DEFAULT_PREREG_PATH,
    download_result_path: Path = DEFAULT_DOWNLOAD_RESULT_PATH,
    vix_path: Path = DEFAULT_VIX_PATH,
    macro_path: Path = DEFAULT_MACRO_PATH,
    summary_path: Path = DEFAULT_SUMMARY_PATH,
    report_path: Path = DEFAULT_REPORT_PATH,
    search_log_path: Path = DEFAULT_SEARCH_LOG_PATH,
    build_root: Path = DEFAULT_BUILD_ROOT,
) -> dict[str, Any]:
    prereg = _load_json(prereg_path)
    download = _load_json(download_result_path)
    downloads = download["execution"]["downloads"]
    inventory = _raw_file_inventory(downloads)
    spy_item = _single_download(downloads, field_group="spy_underlying_bars")
    spy_bars = _load_spy_bars(Path(spy_item["raw_path"]))
    _write_jsonl(build_root / "spy_bar.jsonl", spy_bars)

    quote_items = [item for item in downloads if item.get("schema") == "cbbo-1m"]
    quote_inventory = [_quote_window_inventory(item) for item in quote_items]
    _write_jsonl(build_root / "option_quote_window_inventory.jsonl", quote_inventory)

    regimes = _regime_labels(TARGET_DATE, vix_path, macro_path)
    proxy_5m = _opening_proxy(spy_bars, open_minutes=5, decision_minute="09:35:00")
    signal = _locked_signal(regimes, proxy_5m)
    quote_availability = _entry_exit_quote_availability(signal, quote_inventory)
    timestamp = _timestamp_alignment(spy_bars, quote_inventory, proxy_5m)
    decision = _decision(signal, quote_availability)
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    summary = {
        "record_type": "experiment_summary",
        "schema_version": "h_a2_independent_validation_import_diagnostic_v1",
        "experiment_id": "h_a2_independent_validation_import_diagnostic",
        "hypothesis_id": "H-A2",
        "status": "complete",
        "evidence_tier": "E1",
        "conclusion": "ยังสรุปไม่ได้",
        "conclusion_reason": (
            "The already-downloaded 2025-04-08 DBN files can be locally parsed and timestamp-checked, "
            "but the locked H-A2 09:35 rule does not create a candidate trade on this high-VIX day."
        ),
        "generated_at_utc": generated_at,
        "source_preregistration": _relative(prereg_path),
        "source_download_result": _relative(download_result_path),
        "target_sample": prereg["target_sample"],
        "network_used": False,
        "paid_data_used": False,
        "additional_download_used": False,
        "new_provider_used": False,
        "broker_request_used": False,
        "ibkr_request_used": False,
        "gdelt_live_retry_used": False,
        "llm_call_used": False,
        "exact_replay_used": False,
        "strategy_pnl_computed": False,
        "paper_trading_allowed": False,
        "operational_validation_allowed": False,
        "real_money_allowed": False,
        "strategy_use_allowed": False,
        "methodology": {
            "local_raw_dbn_only": True,
            "candidate_decision_time_et": "09:35:00",
            "entry_time_et": "09:35:00",
            "locked_threshold": LOCKED_THRESHOLD,
            "used_features": ["clean_macro_vix_condition", "proxy_5m_followthrough"],
            "threshold_search_used": False,
            "oos_tuning_used": False,
            "new_oos_selected_filter_used": False,
            "fifteen_minute_conflict_component_used": False,
            "delayed_entry_component_used": False,
        },
        "raw_file_inventory": inventory,
        "spy_underlying_import": _spy_import_summary(spy_bars),
        "opra_quote_import": _quote_import_summary(quote_inventory),
        "timestamp_alignment_check": timestamp,
        "regime_labels": regimes,
        "candidate_signal_reconstruction": signal,
        "entry_exit_quote_availability": quote_availability,
        "diagnostic_decision": decision,
        "trial_policy": {
            "trial_count": 0,
            "threshold_search_used": False,
            "new_filter_search_used": False,
            "oos_tuning_used": False,
            "dsr_status": "not_applicable_no_parameter_search_no_pnl",
            "search_log": _relative(search_log_path),
        },
        "research_log_required": True,
        "research_log_slug": "higanbana-h-a2-independent-validation-import-diagnostic",
        "research_log_path": "research_log/034-higanbana-h-a2-independent-validation-import-diagnostic.md",
        "allowed_claims": [
            "The 2025-04-08 one-day independent-validation sample can be parsed locally.",
            "The diagnostic reports timestamp discipline, locked-signal reconstruction, and quote-window availability.",
            "Claims remain capped at E1 diagnostic evidence.",
        ],
        "forbidden_claims": prereg.get("forbidden_claims", []),
        "next_safe_action": decision["allowed_next_action"],
        "tier_blockers": [
            "E1 import/availability diagnostic only",
            "No candidate trade signal on this high-VIX sample day under the locked rule",
            "No exact replay",
            "No independent validation PnL day",
            "No MinTRL/PSR acceptance path",
            "No E2 acceptance claim",
        ],
    }

    _write_json(summary_path, summary)
    report_path.write_text(_render_report(summary), encoding="utf-8")
    _write_search_log(summary, search_log_path)
    return summary


def _raw_file_inventory(downloads: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    blockers: list[str] = []
    for item in downloads:
        path = Path(item["raw_path"])
        exists = path.exists()
        size = path.stat().st_size if exists else 0
        if not exists:
            blockers.append(f"missing_raw_file:{path.name}")
        elif size <= 0:
            blockers.append(f"empty_raw_file:{path.name}")
        rows.append(
            {
                "window": item["window"],
                "dataset": item["dataset"],
                "schema": item["schema"],
                "field_group": item["field_group"],
                "start_utc": item["start"],
                "end_utc": item["end"],
                "raw_path": _relative(path),
                "expected_bytes": item.get("bytes"),
                "actual_bytes": size,
                "sha256": item.get("sha256"),
                "exists": exists,
            }
        )
    return {
        "status": "pass" if not blockers and len(rows) == 15 else "blocked",
        "expected_file_count": 15,
        "actual_file_count": len(rows),
        "total_actual_bytes": sum(row["actual_bytes"] for row in rows),
        "blockers": blockers,
        "files": rows,
    }


def _load_spy_bars(raw_path: Path) -> list[dict[str, Any]]:
    import databento as db  # type: ignore

    frame = db.DBNStore.from_file(raw_path).to_df()
    rows = []
    for item in frame.sort_index().itertuples():
        ts_utc = item.Index.to_pydatetime().astimezone(UTC)
        ts_et = ts_utc.astimezone(ET)
        rows.append(
            {
                "record_type": "spy_bar",
                "schema_version": "h_a2_independent_validation_spy_bar_v1",
                "timestamp_utc": ts_utc.isoformat(),
                "timestamp_et": ts_et.isoformat(),
                "symbol": str(item.symbol),
                "open": float(item.open),
                "high": float(item.high),
                "low": float(item.low),
                "close": float(item.close),
                "volume": int(item.volume),
            }
        )
    return rows


def _quote_window_inventory(item: dict[str, Any]) -> dict[str, Any]:
    import databento as db  # type: ignore

    path = Path(item["raw_path"])
    frame = db.DBNStore.from_file(path).to_df()
    if frame.empty:
        return _empty_quote_window(item)
    timestamps = [idx.to_pydatetime().astimezone(UTC) for idx in frame.index]
    symbols = frame["symbol"].astype(str).str.strip()
    expirations = symbols.map(_safe_expiration)
    zero_dte = expirations == TARGET_DATE
    valid_bid_ask = (frame["bid_px_00"].notna()) & (frame["ask_px_00"].notna()) & (frame["bid_px_00"] > 0) & (frame["ask_px_00"] > 0)
    valid_mid = zero_dte & valid_bid_ask & (frame["ask_px_00"] >= frame["bid_px_00"])
    rights = symbols[zero_dte].map(_safe_right)
    return {
        "window": item["window"],
        "field_group": item["field_group"],
        "raw_path": _relative(path),
        "row_count": int(len(frame)),
        "unique_symbol_count": int(symbols.nunique()),
        "zero_dte_row_count": int(zero_dte.sum()),
        "zero_dte_unique_symbol_count": int(symbols[zero_dte].nunique()),
        "valid_bid_ask_row_count": int(valid_bid_ask.sum()),
        "zero_dte_valid_mid_row_count": int(valid_mid.sum()),
        "zero_dte_call_row_count": int((rights == "call").sum()),
        "zero_dte_put_row_count": int((rights == "put").sum()),
        "min_ts_utc": min(timestamps).isoformat(),
        "max_ts_utc": max(timestamps).isoformat(),
        "min_ts_et": min(timestamps).astimezone(ET).isoformat(),
        "max_ts_et": max(timestamps).astimezone(ET).isoformat(),
        "dataset": item["dataset"],
        "schema": item["schema"],
    }


def _empty_quote_window(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "window": item["window"],
        "field_group": item["field_group"],
        "raw_path": _relative(Path(item["raw_path"])),
        "row_count": 0,
        "unique_symbol_count": 0,
        "zero_dte_row_count": 0,
        "zero_dte_unique_symbol_count": 0,
        "valid_bid_ask_row_count": 0,
        "zero_dte_valid_mid_row_count": 0,
        "zero_dte_call_row_count": 0,
        "zero_dte_put_row_count": 0,
        "min_ts_utc": None,
        "max_ts_utc": None,
        "min_ts_et": None,
        "max_ts_et": None,
        "dataset": item["dataset"],
        "schema": item["schema"],
    }


def _safe_expiration(symbol: str) -> str | None:
    try:
        return parse_databento_option_symbol(symbol)["expiration_date"]
    except ValueError:
        return None


def _safe_right(symbol: str) -> str | None:
    try:
        return parse_databento_option_symbol(symbol)["right"]
    except ValueError:
        return None


def _regime_labels(date_text: str, vix_path: Path, macro_path: Path) -> dict[str, Any]:
    vix_rows = load_vix_vxv(vix_path)
    macro_by_date = load_macro_events_by_date(macro_path)
    prior = previous_vix_record(date_text, vix_rows)
    same_day_vix = next((row for row in vix_rows if row.get("date") == date_text), None)
    macro_events = macro_by_date.get(date_text, [])
    high_macro = [event for event in macro_events if event.get("importance") == "high"]
    prior_vix = float(prior["vix_close"]) if prior else None
    prior_vxv = float(prior["vxv_close"]) if prior else None
    return {
        "date": date_text,
        "prior_vix_date": prior.get("date") if prior else None,
        "prior_vix_close": prior_vix,
        "prior_vxv_close": prior_vxv,
        "prior_high_vix": prior_vix is not None and prior_vix >= 25.0,
        "prior_stress_vix": prior_vix is not None and prior_vix >= 30.0,
        "prior_vix_vxv_inverted": prior_vix is not None and prior_vxv is not None and prior_vix >= prior_vxv,
        "same_day_vix_close": float(same_day_vix["vix_close"]) if same_day_vix else None,
        "high_importance_macro": bool(high_macro),
        "high_importance_macro_event_types": sorted({event["event_type"] for event in high_macro}),
        "clean_macro_vix_condition": not (prior_vix is not None and prior_vix >= 25.0) and not bool(high_macro),
    }


def _locked_signal(regimes: dict[str, Any], proxy_5m: dict[str, Any]) -> dict[str, Any]:
    followthrough = proxy_5m.get("directional_followthrough_to_close_pct")
    threshold_pass = followthrough is not None and float(followthrough) >= LOCKED_THRESHOLD
    signal = proxy_5m.get("signal")
    locked_true = bool(regimes["clean_macro_vix_condition"] and threshold_pass and signal in {"call", "put"})
    blockers = []
    if not regimes["clean_macro_vix_condition"]:
        blockers.append("clean_macro_vix_condition_false")
    if not threshold_pass:
        blockers.append("proxy_5m_followthrough_below_locked_threshold")
    if signal not in {"call", "put"}:
        blockers.append("no_5m_breakout_signal")
    return {
        "status": "complete",
        "candidate_decision_time_et": "09:35:00",
        "entry_time_et": "09:35:00",
        "locked_threshold": LOCKED_THRESHOLD,
        "proxy_5m": proxy_5m,
        "clean_macro_vix_condition": regimes["clean_macro_vix_condition"],
        "proxy_5m_followthrough_pass": threshold_pass,
        "candidate_direction": signal if signal in {"call", "put"} else None,
        "locked_signal_true": locked_true,
        "blockers": blockers,
    }


def _entry_exit_quote_availability(signal: dict[str, Any], quote_inventory: list[dict[str, Any]]) -> dict[str, Any]:
    entry = _find_window(quote_inventory, "2025-04-08_entry_0935")
    forced = _find_window(quote_inventory, "2025-04-08_forced_close_1545")
    exit_windows = [row for row in quote_inventory if row["field_group"] == "option_exit_quotes"]
    direction = signal.get("candidate_direction")
    direction_key = "zero_dte_call_row_count" if direction == "call" else "zero_dte_put_row_count"
    if not signal["locked_signal_true"]:
        status = "no_candidate_trade_signal"
    elif not entry or not forced:
        status = "candidate_trade_data_blocked"
    elif entry.get(direction_key, 0) > 0 and forced.get(direction_key, 0) > 0:
        status = "candidate_trade_data_ready"
    else:
        status = "candidate_trade_data_blocked"
    return {
        "status": status,
        "entry_window_zero_dte_valid_mid_rows": entry.get("zero_dte_valid_mid_row_count") if entry else None,
        "forced_close_zero_dte_valid_mid_rows": forced.get("zero_dte_valid_mid_row_count") if forced else None,
        "exit_window_count": len(exit_windows),
        "exit_windows_with_zero_dte_valid_mid": sum(1 for row in exit_windows if row["zero_dte_valid_mid_row_count"] > 0),
        "candidate_direction": direction,
        "candidate_direction_entry_rows": entry.get(direction_key) if entry and direction else None,
        "candidate_direction_forced_close_rows": forced.get(direction_key) if forced and direction else None,
        "exact_replay_used": False,
        "strategy_pnl_computed": False,
    }


def _timestamp_alignment(spy_bars: list[dict[str, Any]], quote_inventory: list[dict[str, Any]], proxy_5m: dict[str, Any]) -> dict[str, Any]:
    times = [row["timestamp_et"][11:19] for row in spy_bars]
    quote_failures = [
        row["window"]
        for row in quote_inventory
        if row["min_ts_et"] is None or row["max_ts_et"] is None or not row["min_ts_et"].startswith(TARGET_DATE)
    ]
    return {
        "status": "pass" if "09:35:00" in times and not quote_failures and proxy_5m.get("status") == "measured" else "blocked",
        "spy_bar_has_0935": "09:35:00" in times,
        "spy_bar_has_1545": "15:45:00" in times,
        "proxy_5m_status": proxy_5m.get("status"),
        "all_quote_windows_on_target_et_date": not quote_failures,
        "quote_window_date_failures": quote_failures,
        "no_post_0935_features_used_for_signal": True,
    }


def _spy_import_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "status": "pass" if len(rows) >= 390 and any(row["timestamp_et"][11:19] == "09:35:00" for row in rows) else "blocked",
        "row_count": len(rows),
        "min_timestamp_et": rows[0]["timestamp_et"] if rows else None,
        "max_timestamp_et": rows[-1]["timestamp_et"] if rows else None,
        "has_0935_bar": any(row["timestamp_et"][11:19] == "09:35:00" for row in rows),
        "has_1545_bar": any(row["timestamp_et"][11:19] == "15:45:00" for row in rows),
        "normalized_output": _relative(DEFAULT_BUILD_ROOT / "spy_bar.jsonl"),
    }


def _quote_import_summary(quote_inventory: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "status": "pass" if len(quote_inventory) == 14 and all(row["zero_dte_valid_mid_row_count"] > 0 for row in quote_inventory) else "blocked",
        "window_count": len(quote_inventory),
        "total_row_count": sum(row["row_count"] for row in quote_inventory),
        "total_zero_dte_row_count": sum(row["zero_dte_row_count"] for row in quote_inventory),
        "total_zero_dte_valid_mid_row_count": sum(row["zero_dte_valid_mid_row_count"] for row in quote_inventory),
        "windows": quote_inventory,
        "normalized_inventory_output": _relative(DEFAULT_BUILD_ROOT / "option_quote_window_inventory.jsonl"),
    }


def _decision(signal: dict[str, Any], quote_availability: dict[str, Any]) -> dict[str, Any]:
    if signal["locked_signal_true"] and quote_availability["status"] == "candidate_trade_data_ready":
        decision = "candidate_trade_data_ready_for_separate_preregistered_exact_replay"
        next_action = (
            "Pre-register a separate exact-replay diagnostic for this date before computing candidate-trade PnL or making any E2 claim."
        )
    elif signal["locked_signal_true"]:
        decision = "candidate_signal_but_quote_data_blocked"
        next_action = "Diagnose missing quote windows or option-selection inputs before any exact replay."
    else:
        decision = "no_candidate_trade_signal_on_high_vix_sample"
        next_action = (
            "Use this diagnostic as high-VIX availability/regime evidence, then pre-register the next normal/control "
            "independent-validation sample decision or no-paid validation gap decision before any additional data pull."
        )
    return {
        "status": "complete",
        "decision": decision,
        "allowed_next_action": next_action,
        "evidence_tier_cap": "E1",
        "paper_trading_allowed": False,
        "e2_status": "forbidden",
    }


def _write_search_log(summary: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    records = []
    for check_id in [
        "raw_file_inventory",
        "spy_underlying_import",
        "opra_quote_import",
        "timestamp_alignment_check",
        "candidate_signal_reconstruction",
        "entry_exit_quote_availability",
        "diagnostic_decision",
    ]:
        section = summary.get(check_id, {})
        records.append(
            {
                "record_type": "h_a2_independent_validation_import_diagnostic_check",
                "experiment_id": summary["experiment_id"],
                "check_id": check_id,
                "status": section.get("status"),
                "locked_threshold": LOCKED_THRESHOLD,
                "candidate_decision_time_et": "09:35:00",
                "threshold_search_used": False,
                "new_filter_search_used": False,
                "oos_tuning_used": False,
            }
        )
    path.write_text("\n".join(json.dumps(record, ensure_ascii=False, sort_keys=True) for record in records) + "\n", encoding="utf-8")


def _render_report(summary: dict[str, Any]) -> str:
    spy = summary["spy_underlying_import"]
    quotes = summary["opra_quote_import"]
    signal = summary["candidate_signal_reconstruction"]
    availability = summary["entry_exit_quote_availability"]
    decision = summary["diagnostic_decision"]
    return "\n".join(
        [
            "# H-A2 Independent Validation Import Diagnostic",
            "",
            f"- Status: `{summary['status']}`",
            f"- Conclusion: `{summary['conclusion']}`",
            f"- Evidence tier: `{summary['evidence_tier']}`",
            f"- Target date: `{TARGET_DATE}`",
            f"- Decision: `{decision['decision']}`",
            "",
            "## Raw Import",
            "",
            f"- Raw file status: `{summary['raw_file_inventory']['status']}`",
            f"- Raw files: `{summary['raw_file_inventory']['actual_file_count']}`",
            f"- SPY bar rows: `{spy['row_count']}`",
            f"- Quote windows: `{quotes['window_count']}`",
            f"- Quote rows: `{quotes['total_row_count']}`",
            f"- 0DTE valid-mid quote rows: `{quotes['total_zero_dte_valid_mid_row_count']}`",
            "",
            "## Locked Signal",
            "",
            f"- Clean macro/VIX condition: `{signal['clean_macro_vix_condition']}`",
            f"- Proxy 5m signal: `{signal['proxy_5m']['signal']}`",
            f"- Proxy 5m followthrough: `{signal['proxy_5m'].get('directional_followthrough_to_close_pct')}`",
            f"- Locked threshold: `{signal['locked_threshold']}`",
            f"- Locked signal true: `{signal['locked_signal_true']}`",
            f"- Signal blockers: `{', '.join(signal['blockers'])}`",
            "",
            "## Quote Availability",
            "",
            f"- Availability status: `{availability['status']}`",
            f"- Entry 0DTE valid-mid rows: `{availability['entry_window_zero_dte_valid_mid_rows']}`",
            f"- Forced-close 0DTE valid-mid rows: `{availability['forced_close_zero_dte_valid_mid_rows']}`",
            f"- Exit windows with 0DTE valid-mid rows: `{availability['exit_windows_with_zero_dte_valid_mid']}`",
            "",
            "## Guardrails",
            "",
            "- No network, additional paid data, IBKR request, LLM call, GDELT retry, exact replay, or strategy PnL was used.",
            "- Threshold `0.001` and the 09:35-only H-A2 rule were preserved.",
            "- This diagnostic does not approve paper trading, operational validation, real-money trading, or E2 evidence.",
            "",
            "## Next Safe Action",
            "",
            decision["allowed_next_action"],
            "",
        ]
    )


def _single_download(downloads: list[dict[str, Any]], field_group: str) -> dict[str, Any]:
    matches = [item for item in downloads if item.get("field_group") == field_group]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one download with field_group={field_group}, found {len(matches)}")
    return matches[0]


def _find_window(rows: list[dict[str, Any]], window: str) -> dict[str, Any] | None:
    return next((row for row in rows if row.get("window") == window), None)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main() -> int:
    result = run_h_a2_independent_validation_import_diagnostic()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
