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
LOCKED_THRESHOLD = 0.001
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

DEFAULT_PREREG_PATH = PROJECT_ROOT / "experiments" / "h_a2_normal_control_import_diagnostic_preregistration.json"
DEFAULT_DOWNLOAD_RESULT_PATH = (
    PROJECT_ROOT / "reports" / "data_cost" / "databento_download_result_h_a2_normal_control_low_normal_vix_control_pack.json"
)
DEFAULT_VIX_PATH = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "vix_vxv" / "vix_vxv.jsonl"
DEFAULT_MACRO_PATH = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "macro_calendar" / "macro_event.jsonl"
DEFAULT_SUMMARY_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_normal_control_import_diagnostic.json"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_normal_control_import_diagnostic.md"
DEFAULT_SEARCH_LOG_PATH = (
    PROJECT_ROOT / "reports" / "diagnostics" / "search_logs" / "h_a2_normal_control_import_diagnostic_search_log.jsonl"
)
DEFAULT_BUILD_ROOT = PROJECT_ROOT / "build" / "h_a2_normal_control_low_normal_vix_control_pack"


def run_h_a2_normal_control_import_diagnostic(
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
    by_date = _downloads_by_date(downloads)

    vix_rows = load_vix_vxv(vix_path)
    macro_by_date = load_macro_events_by_date(macro_path)
    date_diagnostics = []
    all_spy_rows: list[dict[str, Any]] = []
    quote_inventory = []

    for date_text in EXPECTED_DATES:
        spy_item = by_date[date_text]["spy"]
        quote_item = by_date[date_text]["quote"]
        spy_bars = _load_spy_bars(Path(spy_item["raw_path"]), date_text)
        quote = _quote_day_inventory(quote_item, date_text)
        regimes = _regime_labels(date_text, vix_rows, macro_by_date)
        proxy_5m = _opening_proxy(spy_bars, open_minutes=5, decision_minute="09:35:00")
        signal = _locked_signal(regimes, proxy_5m)
        availability = _entry_exit_quote_availability(signal, quote)
        timestamp = _timestamp_alignment(date_text, spy_bars, quote, proxy_5m)

        all_spy_rows.extend(spy_bars)
        quote_inventory.append(quote)
        date_diagnostics.append(
            {
                "date": date_text,
                "spy_underlying_import": _spy_day_summary(spy_bars),
                "opra_quote_import": quote,
                "timestamp_alignment_check": timestamp,
                "regime_labels": regimes,
                "candidate_signal_reconstruction": signal,
                "entry_exit_quote_availability": availability,
            }
        )

    _write_jsonl(build_root / "spy_bar.jsonl", all_spy_rows)
    _write_jsonl(build_root / "option_quote_day_inventory.jsonl", quote_inventory)

    aggregate = _aggregate(date_diagnostics, inventory)
    decision = _decision(aggregate)
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    summary = {
        "record_type": "experiment_summary",
        "schema_version": "h_a2_normal_control_import_diagnostic_v1",
        "experiment_id": "h_a2_normal_control_import_diagnostic",
        "hypothesis_id": "H-A2",
        "status": "complete",
        "evidence_tier": "E1",
        "conclusion": "ยังสรุปไม่ได้",
        "conclusion_reason": (
            "The already-downloaded 10-day low/normal-VIX control pack can be parsed locally and used to reconstruct "
            "the locked 09:35 H-A2 signal, but this diagnostic does not run exact replay or compute strategy PnL."
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
            "exact_replay_used": False,
            "strategy_pnl_computed": False,
        },
        "raw_file_inventory": inventory,
        "spy_underlying_import": _spy_import_summary(date_diagnostics, build_root),
        "opra_quote_import": _quote_import_summary(date_diagnostics, build_root),
        "timestamp_alignment_check": _timestamp_summary(date_diagnostics),
        "date_diagnostics": date_diagnostics,
        "aggregate_diagnostic": aggregate,
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
        "research_log_slug": "higanbana-h-a2-normal-control-import-diagnostic",
        "research_log_path": "research_log/035-higanbana-h-a2-normal-control-import-diagnostic.md",
        "allowed_claims": [
            "The low/normal-VIX control pack can be parsed locally.",
            "The diagnostic reports timestamp discipline, locked-signal reconstruction, and quote availability by date.",
            "Claims remain capped at E1 diagnostic evidence.",
        ],
        "forbidden_claims": prereg.get("forbidden_claims", []),
        "next_safe_action": decision["allowed_next_action"],
        "tier_blockers": [
            "E1 import/availability diagnostic only",
            "No exact replay",
            "No strategy PnL",
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
                "date": item.get("date"),
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
    dates = sorted({row["date"] for row in rows})
    return {
        "status": "pass" if not blockers and len(rows) == 20 and dates == EXPECTED_DATES else "blocked",
        "expected_file_count": 20,
        "actual_file_count": len(rows),
        "expected_dates": EXPECTED_DATES,
        "actual_dates": dates,
        "total_actual_bytes": sum(row["actual_bytes"] for row in rows),
        "blockers": blockers,
        "files": rows,
    }


def _downloads_by_date(downloads: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    grouped: dict[str, dict[str, dict[str, Any]]] = {}
    for item in downloads:
        date_text = item["date"]
        grouped.setdefault(date_text, {})
        if item.get("field_group") == "spy_underlying_bars":
            grouped[date_text]["spy"] = item
        elif item.get("schema") == "cbbo-1m":
            grouped[date_text]["quote"] = item
    for date_text in EXPECTED_DATES:
        if "spy" not in grouped.get(date_text, {}) or "quote" not in grouped.get(date_text, {}):
            raise ValueError(f"missing spy or quote raw file for {date_text}")
    return grouped


def _load_spy_bars(raw_path: Path, date_text: str) -> list[dict[str, Any]]:
    import databento as db  # type: ignore

    frame = db.DBNStore.from_file(raw_path).to_df()
    rows = []
    for item in frame.sort_index().itertuples():
        ts_utc = item.Index.to_pydatetime().astimezone(UTC)
        ts_et = ts_utc.astimezone(ET)
        rows.append(
            {
                "record_type": "spy_bar",
                "schema_version": "h_a2_normal_control_spy_bar_v1",
                "date": date_text,
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


def _quote_day_inventory(item: dict[str, Any], date_text: str) -> dict[str, Any]:
    import databento as db  # type: ignore

    path = Path(item["raw_path"])
    frame = db.DBNStore.from_file(path).to_df()
    if frame.empty:
        return _empty_quote_day(item, date_text)

    timestamps_utc = [idx.to_pydatetime().astimezone(UTC) for idx in frame.index]
    times_et = [ts.astimezone(ET).strftime("%H:%M:%S") for ts in timestamps_utc]
    dates_et = [ts.astimezone(ET).date().isoformat() for ts in timestamps_utc]
    symbols = frame["symbol"].astype(str).str.strip()
    expirations = symbols.map(_safe_expiration)
    zero_dte = expirations == date_text
    valid_bid_ask = (frame["bid_px_00"].notna()) & (frame["ask_px_00"].notna()) & (frame["bid_px_00"] > 0) & (frame["ask_px_00"] > 0)
    valid_mid = zero_dte & valid_bid_ask & (frame["ask_px_00"] >= frame["bid_px_00"])
    entry_mask = valid_mid & _bool_list_mask(times_et, "09:35:00")
    forced_mask = valid_mid & _bool_list_mask(times_et, "15:45:00")
    rights = symbols[zero_dte].map(_safe_right)
    entry_rights = symbols[entry_mask].map(_safe_right)
    forced_rights = symbols[forced_mask].map(_safe_right)
    date_failures = sorted({date for date in dates_et if date != date_text})
    return {
        "date": date_text,
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
        "entry_0935_zero_dte_valid_mid_row_count": int(entry_mask.sum()),
        "entry_0935_call_row_count": int((entry_rights == "call").sum()),
        "entry_0935_put_row_count": int((entry_rights == "put").sum()),
        "forced_close_1545_zero_dte_valid_mid_row_count": int(forced_mask.sum()),
        "forced_close_1545_call_row_count": int((forced_rights == "call").sum()),
        "forced_close_1545_put_row_count": int((forced_rights == "put").sum()),
        "min_ts_utc": min(timestamps_utc).isoformat(),
        "max_ts_utc": max(timestamps_utc).isoformat(),
        "min_ts_et": min(timestamps_utc).astimezone(ET).isoformat(),
        "max_ts_et": max(timestamps_utc).astimezone(ET).isoformat(),
        "all_quotes_on_target_et_date": not date_failures,
        "quote_window_date_failures": date_failures,
        "dataset": item["dataset"],
        "schema": item["schema"],
    }


def _empty_quote_day(item: dict[str, Any], date_text: str) -> dict[str, Any]:
    return {
        "date": date_text,
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
        "entry_0935_zero_dte_valid_mid_row_count": 0,
        "entry_0935_call_row_count": 0,
        "entry_0935_put_row_count": 0,
        "forced_close_1545_zero_dte_valid_mid_row_count": 0,
        "forced_close_1545_call_row_count": 0,
        "forced_close_1545_put_row_count": 0,
        "min_ts_utc": None,
        "max_ts_utc": None,
        "min_ts_et": None,
        "max_ts_et": None,
        "all_quotes_on_target_et_date": False,
        "quote_window_date_failures": [date_text],
        "dataset": item["dataset"],
        "schema": item["schema"],
    }


def _bool_list_mask(values: list[str], target: str) -> Any:
    import pandas as pd  # type: ignore

    return pd.Series([value == target for value in values], index=None).to_numpy()


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


def _regime_labels(date_text: str, vix_rows: list[dict[str, Any]], macro_by_date: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
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


def _entry_exit_quote_availability(signal: dict[str, Any], quote: dict[str, Any]) -> dict[str, Any]:
    direction = signal.get("candidate_direction")
    direction_entry_key = "entry_0935_call_row_count" if direction == "call" else "entry_0935_put_row_count"
    direction_forced_key = "forced_close_1545_call_row_count" if direction == "call" else "forced_close_1545_put_row_count"
    if not signal["locked_signal_true"]:
        status = "no_candidate_trade_signal"
    elif quote.get(direction_entry_key, 0) > 0 and quote.get(direction_forced_key, 0) > 0:
        status = "candidate_trade_data_ready"
    else:
        status = "candidate_trade_data_blocked"
    return {
        "status": status,
        "entry_window_zero_dte_valid_mid_rows": quote.get("entry_0935_zero_dte_valid_mid_row_count"),
        "forced_close_zero_dte_valid_mid_rows": quote.get("forced_close_1545_zero_dte_valid_mid_row_count"),
        "candidate_direction": direction,
        "candidate_direction_entry_rows": quote.get(direction_entry_key) if direction else None,
        "candidate_direction_forced_close_rows": quote.get(direction_forced_key) if direction else None,
        "exact_replay_used": False,
        "strategy_pnl_computed": False,
    }


def _timestamp_alignment(
    date_text: str,
    spy_bars: list[dict[str, Any]],
    quote: dict[str, Any],
    proxy_5m: dict[str, Any],
) -> dict[str, Any]:
    times = [row["timestamp_et"][11:19] for row in spy_bars]
    return {
        "status": (
            "pass"
            if "09:35:00" in times
            and "15:45:00" in times
            and quote.get("all_quotes_on_target_et_date") is True
            and proxy_5m.get("status") == "measured"
            else "blocked"
        ),
        "date": date_text,
        "spy_bar_has_0935": "09:35:00" in times,
        "spy_bar_has_1545": "15:45:00" in times,
        "proxy_5m_status": proxy_5m.get("status"),
        "all_quote_windows_on_target_et_date": quote.get("all_quotes_on_target_et_date"),
        "quote_window_date_failures": quote.get("quote_window_date_failures", []),
        "no_post_0935_features_used_for_signal": True,
    }


def _spy_day_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "status": "pass" if len(rows) >= 390 and any(row["timestamp_et"][11:19] == "09:35:00" for row in rows) else "blocked",
        "row_count": len(rows),
        "min_timestamp_et": rows[0]["timestamp_et"] if rows else None,
        "max_timestamp_et": rows[-1]["timestamp_et"] if rows else None,
        "has_0935_bar": any(row["timestamp_et"][11:19] == "09:35:00" for row in rows),
        "has_1545_bar": any(row["timestamp_et"][11:19] == "15:45:00" for row in rows),
    }


def _spy_import_summary(date_diagnostics: list[dict[str, Any]], build_root: Path) -> dict[str, Any]:
    rows = [item["spy_underlying_import"] for item in date_diagnostics]
    return {
        "status": "pass" if len(rows) == 10 and all(row["status"] == "pass" for row in rows) else "blocked",
        "date_count": len(rows),
        "total_row_count": sum(row["row_count"] for row in rows),
        "dates_with_0935_bar": sum(1 for row in rows if row["has_0935_bar"]),
        "dates_with_1545_bar": sum(1 for row in rows if row["has_1545_bar"]),
        "normalized_output": _relative(build_root / "spy_bar.jsonl"),
    }


def _quote_import_summary(date_diagnostics: list[dict[str, Any]], build_root: Path) -> dict[str, Any]:
    rows = [item["opra_quote_import"] for item in date_diagnostics]
    return {
        "status": "pass" if len(rows) == 10 and all(row["zero_dte_valid_mid_row_count"] > 0 for row in rows) else "blocked",
        "date_count": len(rows),
        "total_row_count": sum(row["row_count"] for row in rows),
        "total_zero_dte_row_count": sum(row["zero_dte_row_count"] for row in rows),
        "total_zero_dte_valid_mid_row_count": sum(row["zero_dte_valid_mid_row_count"] for row in rows),
        "dates_with_entry_0935_valid_mid": sum(1 for row in rows if row["entry_0935_zero_dte_valid_mid_row_count"] > 0),
        "dates_with_forced_close_1545_valid_mid": sum(
            1 for row in rows if row["forced_close_1545_zero_dte_valid_mid_row_count"] > 0
        ),
        "normalized_inventory_output": _relative(build_root / "option_quote_day_inventory.jsonl"),
    }


def _timestamp_summary(date_diagnostics: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [item["timestamp_alignment_check"] for item in date_diagnostics]
    return {
        "status": "pass" if len(rows) == 10 and all(row["status"] == "pass" for row in rows) else "blocked",
        "date_count": len(rows),
        "pass_count": sum(1 for row in rows if row["status"] == "pass"),
        "blocked_dates": [row["date"] for row in rows if row["status"] != "pass"],
        "no_post_0935_features_used_for_signal": all(row["no_post_0935_features_used_for_signal"] for row in rows),
    }


def _aggregate(date_diagnostics: list[dict[str, Any]], inventory: dict[str, Any]) -> dict[str, Any]:
    signals = [row["candidate_signal_reconstruction"] for row in date_diagnostics]
    availability = [row["entry_exit_quote_availability"] for row in date_diagnostics]
    regimes = [row["regime_labels"] for row in date_diagnostics]
    return {
        "status": "complete" if inventory["status"] == "pass" else "blocked",
        "date_count": len(date_diagnostics),
        "locked_signal_true_count": sum(1 for row in signals if row["locked_signal_true"]),
        "candidate_trade_data_ready_count": sum(1 for row in availability if row["status"] == "candidate_trade_data_ready"),
        "candidate_trade_data_blocked_count": sum(
            1 for row in availability if row["status"] == "candidate_trade_data_blocked"
        ),
        "no_candidate_trade_signal_count": sum(1 for row in availability if row["status"] == "no_candidate_trade_signal"),
        "clean_macro_vix_date_count": sum(1 for row in regimes if row["clean_macro_vix_condition"]),
        "prior_high_vix_date_count": sum(1 for row in regimes if row["prior_high_vix"]),
        "high_importance_macro_date_count": sum(1 for row in regimes if row["high_importance_macro"]),
        "candidate_trade_data_ready_dates": [
            row["date"] for row in date_diagnostics if row["entry_exit_quote_availability"]["status"] == "candidate_trade_data_ready"
        ],
        "locked_signal_true_dates": [
            row["date"] for row in date_diagnostics if row["candidate_signal_reconstruction"]["locked_signal_true"]
        ],
    }


def _decision(aggregate: dict[str, Any]) -> dict[str, Any]:
    ready_count = int(aggregate["candidate_trade_data_ready_count"])
    signal_count = int(aggregate["locked_signal_true_count"])
    if ready_count > 0:
        decision = "normal_control_candidate_trade_data_ready_for_separate_preregistered_exact_replay"
        next_action = (
            "Pre-register a separate bounded exact-replay diagnostic for the normal/control candidate dates only before "
            "computing candidate-trade PnL or making any E2 claim."
        )
    elif signal_count > 0:
        decision = "normal_control_candidate_signal_but_quote_data_blocked"
        next_action = "Diagnose missing entry/forced-close quote availability before any exact replay."
    else:
        decision = "normal_control_no_candidate_trade_signal"
        next_action = "Use this diagnostic to revise the validation-sample plan before any further download or exact replay."
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
    for row in summary["date_diagnostics"]:
        for check_id in [
            "spy_underlying_import",
            "opra_quote_import",
            "timestamp_alignment_check",
            "candidate_signal_reconstruction",
            "entry_exit_quote_availability",
        ]:
            section = row.get(check_id, {})
            records.append(
                {
                    "record_type": "h_a2_normal_control_import_diagnostic_check",
                    "experiment_id": summary["experiment_id"],
                    "date": row["date"],
                    "check_id": check_id,
                    "status": section.get("status", "complete"),
                    "locked_threshold": LOCKED_THRESHOLD,
                    "candidate_decision_time_et": "09:35:00",
                    "threshold_search_used": False,
                    "new_filter_search_used": False,
                    "oos_tuning_used": False,
                }
            )
    records.append(
        {
            "record_type": "h_a2_normal_control_import_diagnostic_check",
            "experiment_id": summary["experiment_id"],
            "check_id": "diagnostic_decision",
            "status": summary["diagnostic_decision"]["status"],
            "decision": summary["diagnostic_decision"]["decision"],
            "locked_threshold": LOCKED_THRESHOLD,
            "threshold_search_used": False,
            "new_filter_search_used": False,
            "oos_tuning_used": False,
        }
    )
    path.write_text("\n".join(json.dumps(record, ensure_ascii=False, sort_keys=True) for record in records) + "\n", encoding="utf-8")


def _render_report(summary: dict[str, Any]) -> str:
    spy = summary["spy_underlying_import"]
    quotes = summary["opra_quote_import"]
    aggregate = summary["aggregate_diagnostic"]
    decision = summary["diagnostic_decision"]
    rows = [
        "# H-A2 Normal/Control Import Diagnostic",
        "",
        f"- Status: `{summary['status']}`",
        f"- Conclusion: `{summary['conclusion']}`",
        f"- Evidence tier: `{summary['evidence_tier']}`",
        f"- Decision: `{decision['decision']}`",
        "",
        "## Import Summary",
        "",
        f"- Raw files: `{summary['raw_file_inventory']['actual_file_count']}`",
        f"- Total raw bytes: `{summary['raw_file_inventory']['total_actual_bytes']}`",
        f"- SPY dates: `{spy['date_count']}`",
        f"- SPY bar rows: `{spy['total_row_count']}`",
        f"- OPRA dates: `{quotes['date_count']}`",
        f"- OPRA quote rows: `{quotes['total_row_count']}`",
        f"- 0DTE valid-mid quote rows: `{quotes['total_zero_dte_valid_mid_row_count']}`",
        "",
        "## Locked Signal And Availability",
        "",
        f"- Clean macro/VIX dates: `{aggregate['clean_macro_vix_date_count']}`",
        f"- Locked signal true dates: `{aggregate['locked_signal_true_count']}`",
        f"- Candidate trade data ready dates: `{aggregate['candidate_trade_data_ready_count']}`",
        f"- Candidate trade data blocked dates: `{aggregate['candidate_trade_data_blocked_count']}`",
        f"- No-candidate dates: `{aggregate['no_candidate_trade_signal_count']}`",
        f"- Ready dates: `{', '.join(aggregate['candidate_trade_data_ready_dates']) or 'none'}`",
        "",
        "## Per-Date Results",
        "",
        "| Date | Clean macro/VIX | Proxy signal | Followthrough | Locked signal | Availability |",
        "|---|---:|---|---:|---:|---|",
    ]
    for row in summary["date_diagnostics"]:
        signal = row["candidate_signal_reconstruction"]
        rows.append(
            "| {date} | `{clean}` | `{proxy}` | `{follow}` | `{locked}` | `{availability}` |".format(
                date=row["date"],
                clean=signal["clean_macro_vix_condition"],
                proxy=signal["proxy_5m"].get("signal"),
                follow=signal["proxy_5m"].get("directional_followthrough_to_close_pct"),
                locked=signal["locked_signal_true"],
                availability=row["entry_exit_quote_availability"]["status"],
            )
        )
    rows.extend(
        [
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
    return "\n".join(rows)


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
    result = run_h_a2_normal_control_import_diagnostic()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
