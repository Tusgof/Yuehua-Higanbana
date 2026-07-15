from __future__ import annotations

from typing import Any


class StrikeSelectionError(ValueError):
    pass


def parse_databento_option_symbol(symbol: str) -> dict[str, Any]:
    compact = " ".join(symbol.split())
    parts = compact.split(" ")
    if len(parts) != 2 or len(parts[1]) != 15:
        raise ValueError(f"unsupported Databento option symbol: {symbol}")
    root, encoded = parts
    right_code = encoded[6]
    if right_code not in {"C", "P"}:
        raise ValueError(f"unsupported option right in symbol: {symbol}")
    yymmdd = encoded[:6]
    return {
        "underlying": root,
        "expiration_date": f"20{yymmdd[:2]}-{yymmdd[2:4]}-{yymmdd[4:6]}",
        "right": "call" if right_code == "C" else "put",
        "strike": int(encoded[7:]) / 1000.0,
    }


def select_vertical_legs(
    option_quotes: list[dict[str, Any]],
    *,
    direction: str,
    underlying_price: float,
    target_gap: float,
    width: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if direction not in {"call", "put"}:
        raise StrikeSelectionError("direction must be call or put")
    quotes = sorted(
        [quote for quote in option_quotes if quote["right"] == direction],
        key=lambda row: float(row["strike"]),
    )
    if len(quotes) < 2:
        raise StrikeSelectionError("at least two strikes are required")

    if direction == "call":
        long_candidates = [quote for quote in quotes if float(quote["strike"]) >= underlying_price]
        desired_long = underlying_price + target_gap
        long_quote = _nearest_quote(long_candidates, desired_long, prefer_higher=False)
        short_candidates = [quote for quote in quotes if float(quote["strike"]) > float(long_quote["strike"])]
        desired_short = float(long_quote["strike"]) + width
        short_quote = _nearest_quote(short_candidates, desired_short, prefer_higher=True)
    else:
        long_candidates = [quote for quote in quotes if float(quote["strike"]) <= underlying_price]
        desired_long = underlying_price - target_gap
        long_quote = _nearest_quote(long_candidates, desired_long, prefer_higher=True)
        short_candidates = [quote for quote in quotes if float(quote["strike"]) < float(long_quote["strike"])]
        desired_short = float(long_quote["strike"]) - width
        short_quote = _nearest_quote(short_candidates, desired_short, prefer_higher=False)

    long_strike = float(long_quote["strike"])
    short_strike = float(short_quote["strike"])
    mapping = {
        "mapping_method": "nearest_discrete_strike_rounding",
        "tie_breaker": "nearest_target_then_lower_spread_then_directional_strike",
        "interpolation_used": False,
        "direction": direction,
        "underlying_price": round(underlying_price, 4),
        "target_gap": target_gap,
        "desired_long_strike": round(desired_long, 4),
        "long_strike": long_strike,
        "short_strike": short_strike,
        "realized_long_gap": round(abs(long_strike - underlying_price), 4),
        "target_width": width,
        "realized_width": round(abs(short_strike - long_strike), 4),
        "long_moneyness": round(long_strike / underlying_price, 6),
        "spread_entry_mid_debit": round(_mid(long_quote) - _mid(short_quote), 4),
        "spread_entry_implementable_debit": round(float(long_quote["ask"]) - float(short_quote["bid"]), 4),
    }
    return [_leg(long_quote, "buy"), _leg(short_quote, "sell")], mapping


def replay_vertical(
    entry_quotes: list[dict[str, Any]],
    exit_quotes: list[dict[str, Any]],
    *,
    direction: str,
    underlying_price: float,
    target_gap: float,
    width: float,
    fee_per_leg_usd: float,
    contract_multiplier: int = 100,
) -> dict[str, Any]:
    legs, mapping = select_vertical_legs(
        entry_quotes,
        direction=direction,
        underlying_price=underlying_price,
        target_gap=target_gap,
        width=width,
    )
    entry_by_strike = {float(row["strike"]): row for row in entry_quotes}
    exit_by_strike = {float(row["strike"]): row for row in exit_quotes}
    selected_legs = []
    for leg in legs:
        strike = float(leg["strike"])
        entry = entry_by_strike.get(strike)
        exit_quote = exit_by_strike.get(strike)
        if entry is None or exit_quote is None:
            raise StrikeSelectionError(f"entry or forced-close quote missing for selected strike: {strike}")
        selected_legs.append({**leg, "entry": entry, "forced_close": exit_quote})

    long_leg = next(row for row in selected_legs if row["side"] == "buy")
    short_leg = next(row for row in selected_legs if row["side"] == "sell")
    entry_mid_debit = _mid(long_leg["entry"]) - _mid(short_leg["entry"])
    forced_mid_value = _mid(long_leg["forced_close"]) - _mid(short_leg["forced_close"])
    entry_implementable_debit = float(long_leg["entry"]["ask"]) - float(short_leg["entry"]["bid"])
    forced_implementable_credit = float(long_leg["forced_close"]["bid"]) - float(short_leg["forced_close"]["ask"])
    mid_pnl = (forced_mid_value - entry_mid_debit) * contract_multiplier
    gross_implementable = (forced_implementable_credit - entry_implementable_debit) * contract_multiplier
    total_fees = fee_per_leg_usd * 4
    implementable_pnl = gross_implementable - total_fees
    return {
        "mapping": mapping,
        "legs": selected_legs,
        "pnl": {
            "entry_mid_debit": round(entry_mid_debit, 4),
            "forced_close_mid_value": round(forced_mid_value, 4),
            "mid_pnl": round(mid_pnl, 2),
            "entry_implementable_debit": round(entry_implementable_debit, 4),
            "forced_close_implementable_credit": round(forced_implementable_credit, 4),
            "gross_implementable_pnl_before_fees": round(gross_implementable, 2),
            "fee_per_leg_usd": fee_per_leg_usd,
            "fee_leg_count": 4,
            "total_fees": round(total_fees, 2),
            "implementable_pnl": round(implementable_pnl, 2),
            "cost_drag_vs_mid": round(mid_pnl - implementable_pnl, 2),
        },
    }


def _nearest_quote(quotes: list[dict[str, Any]], target_strike: float, prefer_higher: bool) -> dict[str, Any]:
    if not quotes:
        raise StrikeSelectionError("no quote can satisfy requested strike mapping")
    return min(
        quotes,
        key=lambda quote: (
            abs(float(quote["strike"]) - target_strike),
            float(quote["ask"]) - float(quote["bid"]),
            -float(quote["strike"]) if prefer_higher else float(quote["strike"]),
        ),
    )


def _mid(quote: dict[str, Any]) -> float:
    return (float(quote["bid"]) + float(quote["ask"])) / 2


def _leg(quote: dict[str, Any], side: str) -> dict[str, Any]:
    return {
        "side": side,
        "quantity": 1,
        "underlying": quote["underlying"],
        "expiration_date": quote["expiration_date"],
        "right": quote["right"],
        "strike": float(quote["strike"]),
    }
