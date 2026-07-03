from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from math import ceil
from pathlib import Path
from statistics import mean, pstdev
from typing import Any


sys.path.insert(0, str(Path(__file__).resolve().parent))
from backtest_engine_m5 import OPTION_MULTIPLIER, calculate_trade_pnl, leg_fill_price


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ADAPTER_SUMMARY_PATH = PROJECT_ROOT / "reports" / "pilots" / "jan_2024_pilot_adapter_summary.json"
QUOTE_PATH = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "databento" / "one_month_pilot" / "option_quote.jsonl"
SUMMARY_PATH = PROJECT_ROOT / "reports" / "pilots" / "jan_2024_pilot_pnl_summary.json"
REPORT_PATH = PROJECT_ROOT / "reports" / "pilots" / "jan_2024_pilot_pnl_report.md"
FORCED_CLOSE_TIME = "15:45:00"


def run_pilot_pnl(
    adapter_summary_path: Path = ADAPTER_SUMMARY_PATH,
    quote_path: Path = QUOTE_PATH,
    summary_path: Path = SUMMARY_PATH,
    report_path: Path = REPORT_PATH,
    fee_per_contract: float = 0.0,
    fill_model: str = "mid",
    close_fallback: str = "strict_1545",
    exit_model: str = "forced_close_only",
    entry_latency_minutes: int = 0,
) -> dict[str, Any]:
    adapter_summary = json.loads(adapter_summary_path.read_text(encoding="utf-8"))
    quotes = load_jsonl(quote_path)
    quotes_by_key = index_quotes(quotes)
    daily_results = [
        evaluate_candidate_day(day, quotes_by_key, fee_per_contract, fill_model, close_fallback, exit_model, entry_latency_minutes)
        for day in adapter_summary["days"]
        if day["status"] == "candidate_ready"
    ]
    summary = summarize_pnl(daily_results, fee_per_contract, fill_model, close_fallback, exit_model, entry_latency_minutes)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(summary), encoding="utf-8")
    return summary


def evaluate_candidate_day(
    day: dict[str, Any],
    quotes_by_key: dict[tuple[str, str, float, str], dict[str, Any]],
    fee_per_contract: float,
    fill_model: str = "mid",
    close_fallback: str = "strict_1545",
    exit_model: str = "forced_close_only",
    entry_latency_minutes: int = 0,
) -> dict[str, Any]:
    if exit_model not in {"forced_close_only", "target_stop_25_50"}:
        raise ValueError(f"unknown exit_model: {exit_model}")
    trade_date = day["date"]
    signal_ts = day["orb_signal"]["breakout_timestamp_et"]
    entry_ts = apply_entry_latency(signal_ts, entry_latency_minutes)
    close_ts = f"{trade_date}T{FORCED_CLOSE_TIME}{entry_ts[-6:]}"
    result: dict[str, Any] = {
        "date": trade_date,
        "status": "unknown",
        "direction": day["direction"],
        "signal_time_et": signal_ts,
        "entry_time_et": entry_ts,
        "entry_latency_minutes": entry_latency_minutes,
        "close_time_et": close_ts,
        "legs": day["legs"],
        "reasons": [],
    }

    entry_fills = []
    missing: list[str] = []
    for leg in day["legs"]:
        entry_quote = quotes_by_key.get((entry_ts, leg["right"], float(leg["strike"]), leg["expiration_date"]))
        if entry_quote is None:
            missing.append(f"entry {leg['right']} {leg['strike']}")
            continue
        entry_fills.append(
            {
                "fill_id": f"pilot-{trade_date}-{leg['leg_id']}",
                "leg_id": leg["leg_id"],
                "side": leg["side"],
                "quantity": leg["quantity"],
                "price": leg_fill_price(entry_quote, leg["side"], fill_model),
                "fill_model": fill_model,
            }
        )

    if missing:
        result["status"] = "missing_quotes"
        result["reasons"].append("missing quotes: " + ", ".join(missing))
        return result

    entry_debit = round(sum(signed_cashflow(fill["side"], fill["price"], fill["quantity"]) for fill in entry_fills), 4)
    max_defined_loss = round(max(entry_debit, 0) * OPTION_MULTIPLIER, 2)
    exit_result = find_exit(quotes_by_key, trade_date, entry_ts, close_ts, day["legs"], entry_debit, close_fallback, exit_model)
    if exit_result["missing"]:
        result["status"] = "missing_quotes"
        result["reasons"].append("missing quotes: " + ", ".join(exit_result["missing"]))
        return result

    entry_mid_fills = build_entry_fills(day["legs"], quotes_by_key, entry_ts, trade_date, "mid")
    mid_pnl = calculate_trade_pnl(entry_mid_fills, exit_result["closing_mid_prices_by_leg_id"])
    gross_pnl = calculate_trade_pnl(entry_fills, exit_result["closing_prices_by_leg_id"])
    contracts = sum(fill["quantity"] for fill in entry_fills)
    fees = round(contracts * fee_per_contract * 2, 2)
    implementable_pnl = round(gross_pnl - fees, 2)
    result.update(
        {
            "status": f"closed_{exit_result['exit_reason']}",
            "entry_debit": entry_debit,
            "mid_pnl": mid_pnl,
            "gross_pnl": gross_pnl,
            "fees": fees,
            "implementable_pnl": implementable_pnl,
            "net_pnl": implementable_pnl,
            "cost_drag": round(mid_pnl - implementable_pnl, 2),
            "max_defined_loss": max_defined_loss,
            "entry_fills": entry_fills,
            "entry_mid_fills": entry_mid_fills,
            "closing_prices_by_leg_id": exit_result["closing_prices_by_leg_id"],
            "closing_mid_prices_by_leg_id": exit_result["closing_mid_prices_by_leg_id"],
            "close_timestamps_by_leg_id": exit_result["close_timestamps_by_leg_id"],
            "exit_value": exit_result["exit_value"],
            "mid_exit_value": exit_result["mid_exit_value"],
            "exit_model": exit_model,
            "reasons": [
                f"entry at {fill_model}; latency={entry_latency_minutes}m; exit={exit_result['exit_reason']}; close_fallback={close_fallback}"
            ],
        }
    )
    return result


def summarize_pnl(
    daily_results: list[dict[str, Any]],
    fee_per_contract: float,
    fill_model: str = "mid",
    close_fallback: str = "strict_1545",
    exit_model: str = "forced_close_only",
    entry_latency_minutes: int = 0,
) -> dict[str, Any]:
    closed = [row for row in daily_results if row["status"].startswith("closed_")]
    skipped = [row for row in daily_results if not row["status"].startswith("closed_")]
    pnls = [pnl_value(row, "implementable_pnl") for row in closed]
    mid_pnls = [pnl_value(row, "mid_pnl") for row in closed]
    equity_curve = []
    equity = 1000.0
    for pnl in pnls:
        equity = round(equity + pnl, 2)
        equity_curve.append(equity)
    return {
        "mode": "pilot_pnl_only",
        "evidence_warning": "This pilot evidence is under-sampled and must not be treated as strategy acceptance.",
        "fee_per_contract": fee_per_contract,
        "fill_model": fill_model,
        "close_fallback": close_fallback,
        "exit_model": exit_model,
        "entry_latency_minutes": entry_latency_minutes,
        "pnl_model": {
            "mid_pnl": "Entry and exit at mid price, with no fees; comparison control only.",
            "implementable_pnl": "Entry uses configured fill_model; exit liquidates longs at bid and shorts at ask; fees are subtracted.",
            "fee_per_contract_per_side": fee_per_contract,
            "entry_latency_minutes": entry_latency_minutes,
        },
        "candidate_days": len(daily_results),
        "closed_trades": len(closed),
        "skipped_trades": len(skipped),
        "total_mid_pnl": round(sum(mid_pnls), 2),
        "total_implementable_pnl": round(sum(pnls), 2),
        "total_net_pnl": round(sum(pnls), 2),
        "average_net_pnl": round(mean(pnls), 4) if pnls else 0.0,
        "win_rate": round(sum(1 for pnl in pnls if pnl > 0) / len(pnls), 4) if pnls else 0.0,
        "worst_trade": min(pnls) if pnls else 0.0,
        "best_trade": max(pnls) if pnls else 0.0,
        "total_cost_drag": round(sum(row.get("cost_drag", 0.0) for row in closed), 2),
        "sharpe_proxy": sharpe_proxy(pnls),
        "max_drawdown": max_drawdown([1000.0, *equity_curve]),
        "sample_adequacy": sample_adequacy_labels(len(closed)),
        "big_day_dependency": big_day_dependency_check(closed),
        "status_counts": status_counts(daily_results),
        "trades": daily_results,
    }

def render_report_m3(summary: dict[str, Any]) -> str:
    metric_keys = [
        "candidate_days",
        "closed_trades",
        "skipped_trades",
        "total_mid_pnl",
        "total_implementable_pnl",
        "total_cost_drag",
        "average_net_pnl",
        "win_rate",
        "worst_trade",
        "best_trade",
        "sharpe_proxy",
        "max_drawdown",
    ]
    metrics = {key: summary[key] for key in metric_keys}
    return "\n".join(
        [
            "# Databento Pilot PnL Report",
            "",
            "## Status",
            "- Conclusion: Inconclusive",
            "- Evidence type: real-data pilot PnL, still far below acceptance-grade trade count.",
            "- Entry: limit-at-mid model",
            "- Exit: forced close 15:45 ET uses bid/ask liquidation price for `implementable_pnl`",
            f"- Fee per contract: `{summary['fee_per_contract']}`",
            f"- Fill model: `{summary['fill_model']}`",
            f"- Close fallback: `{summary['close_fallback']}`",
            f"- Exit model: `{summary['exit_model']}`",
            "",
            "## Metrics",
            "```json",
            json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## PnL Model",
            "```json",
            json.dumps(summary["pnl_model"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Sample Adequacy",
            "```json",
            json.dumps(summary["sample_adequacy"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Big-Day Dependency Check",
            "```json",
            json.dumps(summary["big_day_dependency"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Status Counts",
            "```json",
            json.dumps(summary["status_counts"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Limitations",
            "- Uses only this pilot window, so it remains far below N >= 500.",
            "- MinTRL/PSR stay `pending` until a real experiment return distribution exists.",
            "- Does not yet include VIX/VXV, macro, news/LLM gate, target/stop intraday, or fill retry.",
            "- Days without complete close quotes are skipped rather than filled with invented prices.",
            "",
        ]
    )


def render_report(summary: dict[str, Any]) -> str:
    return render_report_m3(summary)
    metric_keys = [
        "candidate_days",
        "closed_trades",
        "skipped_trades",
        "total_mid_pnl",
        "total_implementable_pnl",
        "total_cost_drag",
        "average_net_pnl",
        "win_rate",
        "worst_trade",
        "best_trade",
        "sharpe_proxy",
        "max_drawdown",
    ]
    metrics = {key: summary[key] for key in metric_keys}
    return "\n".join(
        [
            "# Databento Pilot PnL Report",
            "",
            "## สถานะ",
            "- ข้อสรุป: ยังสรุปไม่ได้",
            "- ประเภทหลักฐาน: pilot PnL จากข้อมูลจริง แต่จำนวน trade ยังต่ำกว่าเกณฑ์รับรองมาก",
            "- Entry: limit-at-mid model",
            "- Exit: forced close 15:45 ET ใช้ bid/ask liquidation price สำหรับ `implementable_pnl`",
            f"- Fee per contract: `{summary['fee_per_contract']}`",
            f"- Fill model: `{summary['fill_model']}`",
            f"- Close fallback: `{summary['close_fallback']}`",
            f"- Exit model: `{summary['exit_model']}`",
            "",
            "## Metrics",
            "```json",
            json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## PnL Model",
            "```json",
            json.dumps(summary["pnl_model"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Sample Adequacy",
            "```json",
            json.dumps(summary["sample_adequacy"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Big-Day Dependency Check",
            "```json",
            json.dumps(summary["big_day_dependency"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Status Counts",
            "```json",
            json.dumps(summary["status_counts"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## ข้อจำกัด",
            "- ใช้ข้อมูล pilot window เท่านั้น จึงยังต่ำกว่าเกณฑ์ N >= 500 มาก",
            "- MinTRL/PSR ยังเป็น `pending` จนกว่าจะมี return distribution ของ experiment จริง",
            "- ยังไม่รวม VIX/VXV, macro, news/LLM gate, target/stop intraday และ fill retry",
            "- วันที่ไม่มี close quote ครบถูก skip ไม่เติมราคาแทนเอง",
            "",
        ]
    )

    metrics = {key: summary[key] for key in ["candidate_days", "closed_trades", "skipped_trades", "total_net_pnl", "average_net_pnl", "win_rate", "worst_trade", "best_trade", "sharpe_proxy", "max_drawdown"]}
    return "\n".join(
        [
            "# Databento Pilot PnL Report",
            "",
            "## สถานะ",
            "- ข้อสรุป: ยังสรุปไม่ได้",
            "- ประเภทหลักฐาน: pilot PnL หนึ่งเดือน จำนวน trade ต่ำมาก ยังไม่ใช่หลักฐานว่า strategy มี edge",
            "- Entry: limit-at-mid model",
            "- Exit: forced close 15:45 ET ใช้ bid/ask liquidation price",
            f"- Fee per contract: `{summary['fee_per_contract']}`",
            f"- Fill model: `{summary['fill_model']}`",
            f"- Close fallback: `{summary['close_fallback']}`",
            f"- Exit model: `{summary['exit_model']}`",
            "",
            "## Metrics",
            "```json",
            json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Status Counts",
            "```json",
            json.dumps(summary["status_counts"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## ข้อจำกัด",
            "- ใช้ข้อมูล pilot window เท่านั้น จึงต่ำกว่าเกณฑ์ N >= 500 มาก",
            "- ยังไม่รวม VIX/VXV, macro, news/LLM gate, target/stop intraday และ fill retry",
            "- วันที่ไม่มี close quote ครบถูก skip ไม่เติมราคาแทนเอง",
            "- ค่า commission ตั้งเป็น 0 ในรอบนี้เพื่อไม่แอบสมมติ broker fee; ต้องทำ sensitivity ต่อ",
            "",
        ]
    )


def build_entry_fills(
    legs: list[dict[str, Any]],
    quotes_by_key: dict[tuple[str, str, float, str], dict[str, Any]],
    entry_ts: str,
    trade_date: str,
    fill_model: str,
) -> list[dict[str, Any]]:
    fills = []
    for leg in legs:
        quote = quotes_by_key[(entry_ts, leg["right"], float(leg["strike"]), leg["expiration_date"])]
        fills.append(
            {
                "fill_id": f"pilot-{trade_date}-{leg['leg_id']}-{fill_model}",
                "leg_id": leg["leg_id"],
                "side": leg["side"],
                "quantity": leg["quantity"],
                "price": leg_fill_price(quote, leg["side"], fill_model),
                "fill_model": fill_model,
            }
        )
    return fills


def apply_entry_latency(timestamp_et: str, entry_latency_minutes: int) -> str:
    if entry_latency_minutes < 0:
        raise ValueError("entry_latency_minutes must be non-negative")
    if entry_latency_minutes == 0:
        return timestamp_et
    return (datetime.fromisoformat(timestamp_et) + timedelta(minutes=entry_latency_minutes)).isoformat()


def liquidation_price(quote: dict[str, Any], opening_side: str) -> float:
    if opening_side == "buy":
        return float(quote["bid"])
    if opening_side == "sell":
        return float(quote["ask"])
    raise ValueError(f"unknown side: {opening_side}")


def mid_price(quote: dict[str, Any]) -> float:
    return round((float(quote["bid"]) + float(quote["ask"])) / 2, 4)


def find_exit(
    quotes_by_key: dict[tuple[str, str, float, str], dict[str, Any]],
    trade_date: str,
    entry_ts: str,
    close_ts: str,
    legs: list[dict[str, Any]],
    entry_debit: float,
    close_fallback: str,
    exit_model: str,
) -> dict[str, Any]:
    if exit_model == "target_stop_25_50":
        for timestamp in candidate_exit_timestamps(quotes_by_key, trade_date, entry_ts, close_ts):
            quotes = quotes_for_legs_at_timestamp(quotes_by_key, timestamp, legs)
            if quotes is None:
                continue
            value = spread_liquidation_value(legs, quotes)
            if value >= entry_debit * 1.25:
                return exit_payload(legs, quotes, timestamp, value, "profit_target_25pct")
            if value <= entry_debit * 0.50:
                return exit_payload(legs, quotes, timestamp, value, "stop_loss_50pct")

    close_quotes: dict[str, dict[str, Any]] = {}
    close_timestamps: dict[str, str] = {}
    missing: list[str] = []
    for leg in legs:
        close_quote, actual_close_ts = find_close_quote(quotes_by_key, close_ts, leg, close_fallback)
        if close_quote is None:
            missing.append(f"close {leg['right']} {leg['strike']}")
            continue
        close_quotes[leg["leg_id"]] = close_quote
        close_timestamps[leg["leg_id"]] = actual_close_ts
    if missing:
        return {"missing": missing}
    value = spread_liquidation_value(legs, close_quotes)
    payload = exit_payload(legs, close_quotes, close_ts, value, "forced_1545")
    payload["close_timestamps_by_leg_id"] = close_timestamps
    return payload


def candidate_exit_timestamps(
    quotes_by_key: dict[tuple[str, str, float, str], dict[str, Any]],
    trade_date: str,
    entry_ts: str,
    close_ts: str,
) -> list[str]:
    return sorted(
        {
            timestamp
            for timestamp, _right, _strike, _expiration in quotes_by_key
            if timestamp[:10] == trade_date and entry_ts < timestamp <= close_ts
        }
    )


def quotes_for_legs_at_timestamp(
    quotes_by_key: dict[tuple[str, str, float, str], dict[str, Any]],
    timestamp: str,
    legs: list[dict[str, Any]],
) -> dict[str, dict[str, Any]] | None:
    quotes: dict[str, dict[str, Any]] = {}
    for leg in legs:
        quote = quotes_by_key.get((timestamp, leg["right"], float(leg["strike"]), leg["expiration_date"]))
        if quote is None:
            return None
        quotes[leg["leg_id"]] = quote
    return quotes


def spread_liquidation_value(legs: list[dict[str, Any]], quotes_by_leg_id: dict[str, dict[str, Any]]) -> float:
    value = 0.0
    for leg in legs:
        quote = quotes_by_leg_id[leg["leg_id"]]
        price = liquidation_price(quote, leg["side"])
        value += signed_cashflow(leg["side"], price, leg["quantity"])
    return round(value, 4)


def spread_mid_value(legs: list[dict[str, Any]], quotes_by_leg_id: dict[str, dict[str, Any]]) -> float:
    value = 0.0
    for leg in legs:
        quote = quotes_by_leg_id[leg["leg_id"]]
        value += signed_cashflow(leg["side"], mid_price(quote), leg["quantity"])
    return round(value, 4)


def exit_payload(
    legs: list[dict[str, Any]],
    quotes_by_leg_id: dict[str, dict[str, Any]],
    timestamp: str,
    value: float,
    exit_reason: str,
) -> dict[str, Any]:
    return {
        "missing": [],
        "exit_reason": exit_reason,
        "exit_value": value,
        "mid_exit_value": spread_mid_value(legs, quotes_by_leg_id),
        "closing_prices_by_leg_id": {
            leg["leg_id"]: liquidation_price(quotes_by_leg_id[leg["leg_id"]], leg["side"])
            for leg in legs
        },
        "closing_mid_prices_by_leg_id": {
            leg["leg_id"]: mid_price(quotes_by_leg_id[leg["leg_id"]])
            for leg in legs
        },
        "close_timestamps_by_leg_id": {leg["leg_id"]: timestamp for leg in legs},
    }


def find_close_quote(
    quotes_by_key: dict[tuple[str, str, float, str], dict[str, Any]],
    close_ts: str,
    leg: dict[str, Any],
    close_fallback: str,
) -> tuple[dict[str, Any] | None, str]:
    exact = quotes_by_key.get((close_ts, leg["right"], float(leg["strike"]), leg["expiration_date"]))
    if exact is not None or close_fallback == "strict_1545":
        return exact, close_ts
    if close_fallback != "nearest_1545_window":
        raise ValueError(f"unknown close_fallback: {close_fallback}")
    trade_date = close_ts[:10]
    offset = close_ts[-6:]
    for minute in ["15:44:00", "15:43:00", "15:42:00", "15:41:00", "15:40:00"]:
        candidate_ts = f"{trade_date}T{minute}{offset}"
        quote = quotes_by_key.get((candidate_ts, leg["right"], float(leg["strike"]), leg["expiration_date"]))
        if quote is not None:
            return quote, candidate_ts
    return None, close_ts


def signed_cashflow(side: str, price: float, quantity: int) -> float:
    if side == "buy":
        return price * quantity
    if side == "sell":
        return -price * quantity
    raise ValueError(f"unknown side: {side}")


def sharpe_proxy(pnls: list[float]) -> float | None:
    if len(pnls) < 2:
        return None
    sd = pstdev(pnls)
    if sd == 0:
        return None
    return round(mean(pnls) / sd, 6)


def pnl_value(row: dict[str, Any], key: str) -> float:
    if key in row:
        return float(row[key])
    return float(row.get("net_pnl", 0.0))


def sample_adequacy_labels(closed_trade_count: int, minimum_trade_count: int = 500) -> dict[str, Any]:
    labels = []
    if closed_trade_count < minimum_trade_count:
        labels.extend(["under-sampled", "underpowered"])
    return {
        "closed_trades": closed_trade_count,
        "minimum_trade_count_prior": minimum_trade_count,
        "labels": labels,
        "mintrl_status": "pending_return_distribution",
        "psr_status": "pending_return_distribution",
        "power_note": "Point Sharpe is diagnostic only until MinTRL/PSR are calculated on an experiment return distribution.",
    }


def big_day_dependency_check(closed_trades: list[dict[str, Any]]) -> dict[str, Any]:
    if len(closed_trades) < 3:
        return {
            "status": "insufficient_trades",
            "removed_trade_count": 0,
            "note": "Need at least 3 closed trades to remove both best and worst trades.",
        }
    remove_each_side = max(1, ceil(len(closed_trades) * 0.05))
    ranked = sorted(closed_trades, key=lambda row: pnl_value(row, "implementable_pnl"))
    remove_ids = {id(row) for row in ranked[:remove_each_side] + ranked[-remove_each_side:]}
    retained = [row for row in closed_trades if id(row) not in remove_ids]
    retained_pnls = [pnl_value(row, "implementable_pnl") for row in retained]
    original_pnls = [pnl_value(row, "implementable_pnl") for row in closed_trades]
    return {
        "status": "pass" if retained else "no_retained_trades",
        "method": "remove_top_and_bottom_5pct_by_implementable_pnl",
        "removed_each_side": remove_each_side,
        "removed_trade_count": len(closed_trades) - len(retained),
        "original_closed_trades": len(closed_trades),
        "retained_closed_trades": len(retained),
        "original_total_implementable_pnl": round(sum(original_pnls), 2),
        "retained_total_implementable_pnl": round(sum(retained_pnls), 2),
        "original_sharpe_proxy": sharpe_proxy(original_pnls),
        "retained_sharpe_proxy": sharpe_proxy(retained_pnls),
    }


def max_drawdown(equity: list[float]) -> float:
    peak = equity[0] if equity else 0.0
    max_dd = 0.0
    for value in equity:
        peak = max(peak, value)
        if peak > 0:
            max_dd = min(max_dd, (value / peak) - 1)
    return round(max_dd, 6)


def status_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        counts[row["status"]] += 1
    return dict(sorted(counts.items()))


def index_quotes(quotes: list[dict[str, Any]]) -> dict[tuple[str, str, float, str], dict[str, Any]]:
    indexed: dict[tuple[str, str, float, str], dict[str, Any]] = {}
    for quote in quotes:
        indexed[(quote["quote_timestamp_et"], quote["right"], float(quote["strike"]), quote["expiration_date"])] = quote
    return indexed


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise ValueError(f"missing input file: {path}")
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run pilot-only PnL for Databento Sub-System A candidates.")
    parser.add_argument("--adapter-summary-path", type=Path, default=ADAPTER_SUMMARY_PATH)
    parser.add_argument("--quote-path", type=Path, default=QUOTE_PATH)
    parser.add_argument("--summary-path", type=Path, default=SUMMARY_PATH)
    parser.add_argument("--report-path", type=Path, default=REPORT_PATH)
    parser.add_argument("--fee-per-contract", type=float, default=0.0)
    parser.add_argument("--fill-model", choices=["mid", "half_spread", "full_spread_stress"], default="mid")
    parser.add_argument("--close-fallback", choices=["strict_1545", "nearest_1545_window"], default="strict_1545")
    parser.add_argument("--exit-model", choices=["forced_close_only", "target_stop_25_50"], default="forced_close_only")
    parser.add_argument("--entry-latency-minutes", type=int, default=0)
    args = parser.parse_args()
    summary = run_pilot_pnl(
        args.adapter_summary_path,
        args.quote_path,
        args.summary_path,
        args.report_path,
        args.fee_per_contract,
        args.fill_model,
        args.close_fallback,
        args.exit_model,
        args.entry_latency_minutes,
    )
    print(json.dumps({key: value for key, value in summary.items() if key != "trades"}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
