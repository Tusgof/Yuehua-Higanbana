from __future__ import annotations

import argparse
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
from run_m5_strike_selection_sensitivity import select_vertical_legs  # noqa: E402
from validate_h_a2_normal_control_exact_replay_preregistration import (  # noqa: E402
    validate_h_a2_normal_control_exact_replay_preregistration,
)


ET = ZoneInfo("America/New_York")
CANDIDATE_DATE = "2025-02-11"
CANDIDATE_DIRECTION = "call"
ENTRY_TIME_ET = "09:35:00"
FORCED_CLOSE_TIME_ET = "15:45:00"
LOCKED_THRESHOLD = 0.001
TARGET_GAP = 1.48
WIDTH = 2.0
FEE_PER_LEG_USD = 0.64
CONTRACT_MULTIPLIER = 100

DEFAULT_PREREG_PATH = PROJECT_ROOT / "experiments" / "h_a2_normal_control_exact_replay_preregistration.json"
DEFAULT_SOURCE_IMPORT_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_normal_control_import_diagnostic.json"
DEFAULT_RAW_QUOTE_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "spy_0dte"
    / "databento"
    / "h_a2_normal_control_low_normal_vix_control_pack"
    / "2025-02-11_opra_grouped_0930_1550.dbn.zst"
)
DEFAULT_SUMMARY_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_normal_control_exact_replay.json"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_normal_control_exact_replay.md"
DEFAULT_SEARCH_LOG_PATH = (
    PROJECT_ROOT / "reports" / "diagnostics" / "search_logs" / "h_a2_normal_control_exact_replay_search_log.jsonl"
)


def run_h_a2_normal_control_exact_replay(
    prereg_path: Path = DEFAULT_PREREG_PATH,
    source_import_path: Path = DEFAULT_SOURCE_IMPORT_PATH,
    raw_quote_path: Path = DEFAULT_RAW_QUOTE_PATH,
    summary_path: Path = DEFAULT_SUMMARY_PATH,
    report_path: Path = DEFAULT_REPORT_PATH,
    search_log_path: Path = DEFAULT_SEARCH_LOG_PATH,
) -> dict[str, Any]:
    prereg_check = validate_h_a2_normal_control_exact_replay_preregistration(prereg_path)
    if prereg_check["status"] != "pass":
        raise RuntimeError(f"preregistration blocked: {prereg_check['blockers']}")

    source = _load_json(source_import_path)
    candidate = _candidate_diag(source)
    if not candidate:
        raise RuntimeError("candidate diagnostic for 2025-02-11 missing")

    signal = candidate["candidate_signal_reconstruction"]
    if signal.get("candidate_direction") != CANDIDATE_DIRECTION or signal.get("locked_signal_true") is not True:
        raise RuntimeError("candidate signal does not match locked preregistration")

    underlying_entry = float(signal["proxy_5m"]["decision_close"])
    underlying_forced_close = float(signal["proxy_5m"]["close"])
    entry_quotes, forced_close_quotes = _load_candidate_quotes(raw_quote_path)

    blockers: list[str] = []
    selected: dict[str, Any] | None = None
    pnl: dict[str, Any] | None = None
    try:
        legs, mapping = select_vertical_legs(
            entry_quotes,
            direction=CANDIDATE_DIRECTION,
            underlying_price=underlying_entry,
            target_gap=TARGET_GAP,
            width=WIDTH,
        )
        selected = _selected_trade(legs, mapping, entry_quotes, forced_close_quotes)
        pnl = _pnl(selected)
    except Exception as exc:  # noqa: BLE001 - recorded as diagnostic blocker, not hidden.
        blockers.append(str(exc))

    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    status = "complete" if not blockers else "blocked"
    summary = {
        "record_type": "experiment_summary",
        "schema_version": "h_a2_normal_control_exact_replay_v1",
        "experiment_id": "h_a2_normal_control_exact_replay",
        "hypothesis_id": "H-A2",
        "status": status,
        "evidence_tier": "E1",
        "conclusion": "ยังสรุปไม่ได้",
        "conclusion_reason": (
            "This is a single-candidate normal/control exact replay. It can report candidate-date PnL, "
            "but one trade is under-sampled and cannot validate H-A2."
        ),
        "generated_at_utc": generated_at,
        "source_preregistration": _relative(prereg_path),
        "source_import_diagnostic": _relative(source_import_path),
        "source_raw_quote_file": _relative(raw_quote_path),
        "candidate": {
            "date": CANDIDATE_DATE,
            "direction": CANDIDATE_DIRECTION,
            "entry_time_et": ENTRY_TIME_ET,
            "forced_close_time_et": FORCED_CLOSE_TIME_ET,
            "locked_threshold": LOCKED_THRESHOLD,
            "underlying_entry_close": underlying_entry,
            "underlying_forced_close": underlying_forced_close,
            "proxy_5m_followthrough_to_close_pct": signal["proxy_5m"]["directional_followthrough_to_close_pct"],
        },
        "methodology": {
            "scope": "single_candidate_date_only",
            "strategy_family": "Sub-System A ORB directional debit vertical spread",
            "strike_selection_method": "nearest_discrete_strike_rounding",
            "target_gap": TARGET_GAP,
            "width": WIDTH,
            "entry_order_assumption": "limit_at_mid_control",
            "exit_order_assumption": "forced_close_1545",
            "contract_multiplier": CONTRACT_MULTIPLIER,
            "fee_per_leg_usd": FEE_PER_LEG_USD,
            "fee_leg_count": 4,
            "threshold_search_used": False,
            "new_filter_search_used": False,
            "oos_tuning_used": False,
            "interpolation_used": False,
            "post_result_strike_selection_used": False,
        },
        "quote_availability": {
            "entry_valid_call_rows": len(entry_quotes),
            "forced_close_valid_call_rows": len(forced_close_quotes),
            "required_exit_symbols_available": selected["required_exit_symbols_available"] if selected else False,
        },
        "selected_vertical": selected,
        "pnl": pnl,
        "blockers": blockers,
        "network_used": False,
        "paid_data_used": False,
        "additional_download_used": False,
        "new_provider_used": False,
        "broker_request_used": False,
        "ibkr_request_used": False,
        "gdelt_live_retry_used": False,
        "llm_call_used": False,
        "exact_replay_used": status == "complete",
        "strategy_pnl_computed": status == "complete",
        "paper_trading_allowed": False,
        "operational_validation_allowed": False,
        "real_money_allowed": False,
        "strategy_use_allowed": False,
        "trial_policy": {
            "trial_count": 1,
            "threshold_search_used": False,
            "new_filter_search_used": False,
            "oos_tuning_used": False,
            "dsr_status": "not_applicable_single_preregistered_candidate_no_parameter_search",
            "search_log": _relative(search_log_path),
        },
        "sample_policy": {
            "sample_count": 1,
            "mintrl_psr_status": "blocked_single_trade_underpowered",
            "under_sampled": True,
            "underpowered": True,
        },
        "research_log_required": True,
        "research_log_slug": "higanbana-h-a2-normal-control-exact-replay",
        "research_log_path": "research_log/036-higanbana-h-a2-normal-control-exact-replay.md",
        "allowed_claims": [
            "The single normal/control candidate date can be exact-replayed locally.",
            "The run reports mid_pnl and implementable_pnl separately for 2025-02-11 only.",
            "The result is E1 single-candidate diagnostic evidence only.",
        ],
        "forbidden_claims": [
            "Do not claim H-A2 edge is validated.",
            "Do not claim E2 acceptance-grade evidence.",
            "Do not approve paper trading.",
            "Do not approve operational validation.",
            "Do not approve real-money trading.",
            "Do not broaden the replay beyond 2025-02-11.",
            "Do not change threshold 0.001.",
            "Do not add a new OOS-selected filter.",
        ],
        "next_safe_action": (
            "Treat H-A2.49 as E1 single-candidate diagnostic evidence only. "
            "Use it to decide the next pre-registered validation-data or sample-expansion step; "
            "do not claim E2 or paper-trading readiness."
        ),
        "tier_blockers": [
            "E1 single-candidate diagnostic evidence only",
            "sample_count_1_under_sampled",
            "MinTRL/PSR blocked",
            "No independent validation distribution",
            "No E2 acceptance claim",
        ],
    }

    _write_json(summary_path, summary)
    report_path.write_text(_render_report(summary), encoding="utf-8")
    _write_search_log(summary, search_log_path)
    return summary


def _load_candidate_quotes(raw_quote_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    import databento as db  # type: ignore

    frame = db.DBNStore.from_file(raw_quote_path).to_df()
    entry_rows: list[dict[str, Any]] = []
    forced_rows: list[dict[str, Any]] = []
    for item in frame.sort_index().itertuples():
        ts_et = item.Index.to_pydatetime().astimezone(ET)
        time_et = ts_et.strftime("%H:%M:%S")
        if time_et not in {ENTRY_TIME_ET, FORCED_CLOSE_TIME_ET}:
            continue
        symbol = str(item.symbol)
        try:
            parsed = parse_databento_option_symbol(symbol)
        except ValueError:
            continue
        if parsed["expiration_date"] != CANDIDATE_DATE or parsed["right"] != CANDIDATE_DIRECTION:
            continue
        bid = float(item.bid_px_00)
        ask = float(item.ask_px_00)
        if bid <= 0 or ask <= 0 or ask < bid:
            continue
        row = {
            "underlying": parsed["underlying"],
            "expiration_date": parsed["expiration_date"],
            "right": parsed["right"],
            "strike": float(parsed["strike"]),
            "symbol": symbol.strip(),
            "quote_timestamp_et": ts_et.isoformat(),
            "quote_time_et": time_et,
            "bid": bid,
            "ask": ask,
            "mid": round((bid + ask) / 2, 4),
            "bid_size": int(item.bid_sz_00),
            "ask_size": int(item.ask_sz_00),
        }
        if time_et == ENTRY_TIME_ET:
            entry_rows.append(row)
        else:
            forced_rows.append(row)
    return entry_rows, forced_rows


def _selected_trade(
    legs: list[dict[str, Any]],
    mapping: dict[str, Any],
    entry_quotes: list[dict[str, Any]],
    forced_close_quotes: list[dict[str, Any]],
) -> dict[str, Any]:
    entry_by_strike = {float(row["strike"]): row for row in entry_quotes}
    exit_by_strike = {float(row["strike"]): row for row in forced_close_quotes}
    leg_rows = []
    for leg in legs:
        strike = float(leg["strike"])
        entry = entry_by_strike.get(strike)
        exit_quote = exit_by_strike.get(strike)
        if entry is None:
            raise ValueError(f"selected entry strike missing: {strike}")
        if exit_quote is None:
            raise ValueError(f"forced-close quote missing for selected strike: {strike}")
        leg_rows.append(
            {
                "leg_id": leg["leg_id"],
                "side": leg["side"],
                "quantity": int(leg["quantity"]),
                "right": leg["right"],
                "strike": strike,
                "entry_symbol": entry["symbol"],
                "entry_bid": entry["bid"],
                "entry_ask": entry["ask"],
                "entry_mid": entry["mid"],
                "entry_bid_size": entry["bid_size"],
                "entry_ask_size": entry["ask_size"],
                "forced_close_symbol": exit_quote["symbol"],
                "forced_close_bid": exit_quote["bid"],
                "forced_close_ask": exit_quote["ask"],
                "forced_close_mid": exit_quote["mid"],
                "forced_close_bid_size": exit_quote["bid_size"],
                "forced_close_ask_size": exit_quote["ask_size"],
            }
        )
    return {
        "status": "selected",
        "required_exit_symbols_available": True,
        "mapping": mapping,
        "legs": leg_rows,
    }


def _pnl(selected: dict[str, Any]) -> dict[str, Any]:
    long_leg = next(row for row in selected["legs"] if row["side"] == "buy")
    short_leg = next(row for row in selected["legs"] if row["side"] == "sell")
    entry_mid_debit = long_leg["entry_mid"] - short_leg["entry_mid"]
    forced_mid_value = long_leg["forced_close_mid"] - short_leg["forced_close_mid"]
    entry_implementable_debit = long_leg["entry_ask"] - short_leg["entry_bid"]
    forced_implementable_credit = long_leg["forced_close_bid"] - short_leg["forced_close_ask"]
    gross_mid_pnl = (forced_mid_value - entry_mid_debit) * CONTRACT_MULTIPLIER
    gross_implementable_pnl = (forced_implementable_credit - entry_implementable_debit) * CONTRACT_MULTIPLIER
    total_fees = FEE_PER_LEG_USD * 4
    implementable_pnl = gross_implementable_pnl - total_fees
    return {
        "entry_mid_debit": round(entry_mid_debit, 4),
        "forced_close_mid_value": round(forced_mid_value, 4),
        "mid_pnl": round(gross_mid_pnl, 2),
        "entry_implementable_debit": round(entry_implementable_debit, 4),
        "forced_close_implementable_credit": round(forced_implementable_credit, 4),
        "gross_implementable_pnl_before_fees": round(gross_implementable_pnl, 2),
        "fee_per_leg_usd": FEE_PER_LEG_USD,
        "fee_leg_count": 4,
        "total_fees": round(total_fees, 2),
        "implementable_pnl": round(implementable_pnl, 2),
        "cost_drag_vs_mid": round(gross_mid_pnl - implementable_pnl, 2),
    }


def _candidate_diag(source: dict[str, Any]) -> dict[str, Any] | None:
    for row in source.get("date_diagnostics", []):
        if row.get("date") == CANDIDATE_DATE:
            return row
    return None


def _write_search_log(summary: dict[str, Any], path: Path) -> None:
    record = {
        "record_type": "h_a2_normal_control_exact_replay_trial",
        "experiment_id": summary["experiment_id"],
        "date": CANDIDATE_DATE,
        "direction": CANDIDATE_DIRECTION,
        "target_gap": TARGET_GAP,
        "width": WIDTH,
        "mapping_method": "nearest_discrete_strike_rounding",
        "threshold_search_used": False,
        "new_filter_search_used": False,
        "oos_tuning_used": False,
        "status": summary["status"],
        "blockers": summary["blockers"],
        "pnl": summary["pnl"],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def _render_report(summary: dict[str, Any]) -> str:
    selected = summary.get("selected_vertical") or {}
    pnl = summary.get("pnl") or {}
    lines = [
        "# H-A2 Normal/Control Exact Replay",
        "",
        f"- Status: `{summary['status']}`",
        f"- Conclusion: `{summary['conclusion']}`",
        f"- Evidence tier: `{summary['evidence_tier']}`",
        f"- Candidate date: `{CANDIDATE_DATE}`",
        f"- Direction: `{CANDIDATE_DIRECTION}`",
        f"- Entry: `{ENTRY_TIME_ET} ET`",
        f"- Forced close: `{FORCED_CLOSE_TIME_ET} ET`",
        "",
        "## Candidate And Strike Mapping",
        "",
        f"- Underlying at entry: `{summary['candidate']['underlying_entry_close']}`",
        f"- Underlying at forced close: `{summary['candidate']['underlying_forced_close']}`",
        f"- Target gap: `{TARGET_GAP}`",
        f"- Width: `{WIDTH}`",
        f"- Mapping method: `nearest_discrete_strike_rounding`",
    ]
    if selected:
        mapping = selected["mapping"]
        lines.extend(
            [
                f"- Long strike: `{mapping['long_strike']}`",
                f"- Short strike: `{mapping['short_strike']}`",
                f"- Realized long gap: `{mapping['realized_long_gap']}`",
                "",
                "## Legs",
                "",
                "| Side | Strike | Entry bid | Entry ask | Entry mid | Forced bid | Forced ask | Forced mid |",
                "|---|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for leg in selected["legs"]:
            lines.append(
                f"| `{leg['side']}` | `{leg['strike']}` | `{leg['entry_bid']}` | `{leg['entry_ask']}` | "
                f"`{leg['entry_mid']}` | `{leg['forced_close_bid']}` | `{leg['forced_close_ask']}` | "
                f"`{leg['forced_close_mid']}` |"
            )
    if pnl:
        lines.extend(
            [
                "",
                "## PnL",
                "",
                "| Metric | ค่า |",
                "|---|---:|",
                f"| Entry mid debit | `{pnl['entry_mid_debit']}` |",
                f"| Forced-close mid value | `{pnl['forced_close_mid_value']}` |",
                f"| Mid PnL | `{pnl['mid_pnl']}` |",
                f"| Entry implementable debit | `{pnl['entry_implementable_debit']}` |",
                f"| Forced-close implementable credit | `{pnl['forced_close_implementable_credit']}` |",
                f"| Gross implementable PnL before fees | `{pnl['gross_implementable_pnl_before_fees']}` |",
                f"| Total fees | `{pnl['total_fees']}` |",
                f"| Implementable PnL | `{pnl['implementable_pnl']}` |",
                f"| Cost drag vs mid | `{pnl['cost_drag_vs_mid']}` |",
            ]
        )
    if summary["blockers"]:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- `{item}`" for item in summary["blockers"])
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- Used only the already-downloaded normal/control candidate-date DBN file.",
            "- Did not download data, call IBKR, call LLMs, retry GDELT, or broaden beyond `2025-02-11`.",
            "- This is E1 single-candidate diagnostic evidence only, not E2 acceptance evidence.",
            "- Paper trading, operational validation, and real-money trading remain forbidden.",
            "",
            "## Next Safe Action",
            "",
            summary["next_safe_action"],
            "",
        ]
    )
    return "\n".join(lines)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run H-A2 normal/control bounded exact replay.")
    parser.add_argument("--summary-path", type=Path, default=DEFAULT_SUMMARY_PATH)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--search-log-path", type=Path, default=DEFAULT_SEARCH_LOG_PATH)
    args = parser.parse_args(argv)
    result = run_h_a2_normal_control_exact_replay(
        summary_path=args.summary_path,
        report_path=args.report_path,
        search_log_path=args.search_log_path,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
