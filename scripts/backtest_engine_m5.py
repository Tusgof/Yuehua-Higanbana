from __future__ import annotations

import json
import sys
from datetime import datetime, time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_m2_contracts import load_schema, validate_record


SCHEMA_VERSION = "m2.0"
OPTION_MULTIPLIER = 100
FORCED_CLOSE_TIME = time(15, 45)


class BacktestEngineError(ValueError):
    pass


def leg_fill_price(quote: dict[str, Any], side: str, fill_model: str = "mid") -> float:
    bid = quote["bid"]
    ask = quote["ask"]
    mid = (bid + ask) / 2
    spread = ask - bid
    if fill_model == "mid":
        return round(mid, 4)
    if fill_model == "half_spread":
        return round(ask if side == "buy" else bid, 4)
    if fill_model == "full_spread_stress":
        return round(ask + spread if side == "buy" else max(0.0, bid - spread), 4)
    raise BacktestEngineError(f"unknown fill model: {fill_model}")


def create_fill(
    fill_id: str,
    filled_at_et: str,
    intent_id: str,
    leg: dict[str, Any],
    quote: dict[str, Any],
    fill_model: str,
) -> dict[str, Any]:
    fill = {
        "record_type": "fill",
        "schema_version": SCHEMA_VERSION,
        "fill_id": fill_id,
        "filled_at_et": filled_at_et,
        "intent_id": intent_id,
        "leg_id": leg["leg_id"],
        "side": leg["side"],
        "quantity": leg["quantity"],
        "price": leg_fill_price(quote, leg["side"], fill_model),
        "fill_model": fill_model,
    }
    _raise_if_invalid(fill)
    return fill


def calculate_trade_pnl(
    opening_fills: list[dict[str, Any]],
    closing_prices_by_leg_id: dict[str, float],
) -> float:
    pnl = 0.0
    for fill in opening_fills:
        close_price = closing_prices_by_leg_id[fill["leg_id"]]
        quantity = fill["quantity"]
        if fill["side"] == "buy":
            pnl += (close_price - fill["price"]) * quantity * OPTION_MULTIPLIER
        else:
            pnl += (fill["price"] - close_price) * quantity * OPTION_MULTIPLIER
    return round(pnl, 2)


def subsystem_a_exit_reason(entry_debit: float, current_value: float, timestamp_et: str) -> str:
    if is_forced_close_time(timestamp_et):
        return "forced_close_1545"
    if current_value >= entry_debit * 1.25:
        return "profit_target_25pct"
    if current_value <= entry_debit * 0.50:
        return "stop_loss_50pct"
    return "hold"


def subsystem_b_exit_reason(entry_credit: float, current_loss: float, timestamp_et: str, stop_multiple: float | None = None) -> str:
    if is_forced_close_time(timestamp_et):
        return "forced_close_1545"
    if stop_multiple is not None and current_loss >= abs(entry_credit) * stop_multiple:
        return "ratio_stop_loss"
    return "hold"


def is_forced_close_time(timestamp_et: str) -> bool:
    return datetime.fromisoformat(timestamp_et).time() >= FORCED_CLOSE_TIME


def max_contract_quantity(equity: float, risk_fraction: float, max_loss_per_contract: float) -> int:
    if equity <= 0 or risk_fraction <= 0 or max_loss_per_contract <= 0:
        return 0
    return int((equity * risk_fraction) // max_loss_per_contract)


def benchmark_return(start_price: float, end_price: float) -> float:
    if start_price <= 0:
        raise BacktestEngineError("start_price must be positive")
    return round((end_price / start_price) - 1, 8)


def create_trade_record(
    trade_id: str,
    strategy_id: str,
    opened_at_et: str,
    closed_at_et: str,
    max_defined_loss: float,
    gross_pnl: float,
    fees: float,
    fills: list[dict[str, Any]],
) -> dict[str, Any]:
    trade = {
        "record_type": "trade",
        "schema_version": SCHEMA_VERSION,
        "trade_id": trade_id,
        "strategy_id": strategy_id,
        "opened_at_et": opened_at_et,
        "closed_at_et": closed_at_et,
        "status": "closed",
        "max_defined_loss": max_defined_loss,
        "gross_pnl": gross_pnl,
        "net_pnl": round(gross_pnl - fees, 2),
        "fills": [fill["fill_id"] for fill in fills],
    }
    _raise_if_invalid(trade)
    return trade


def create_daily_pnl_record(
    trade_date: str,
    starting_equity: float,
    net_pnl: float,
    trade_count: int,
    spy_start: float,
    spy_end: float,
) -> dict[str, Any]:
    daily = {
        "record_type": "daily_pnl",
        "schema_version": SCHEMA_VERSION,
        "date": trade_date,
        "starting_equity": starting_equity,
        "ending_equity": round(starting_equity + net_pnl, 2),
        "net_pnl": net_pnl,
        "trade_count": trade_count,
        "benchmark_return": benchmark_return(spy_start, spy_end),
    }
    _raise_if_invalid(daily)
    return daily


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def _raise_if_invalid(record: dict[str, Any]) -> None:
    errors = validate_record(record, load_schema())
    if errors:
        raise BacktestEngineError("\n".join(errors))
