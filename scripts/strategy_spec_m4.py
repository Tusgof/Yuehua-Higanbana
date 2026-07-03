from __future__ import annotations

import hashlib
import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_m2_contracts import load_schema, validate_record


SCHEMA_VERSION = "m2.0"


class StrategySpecError(ValueError):
    pass


def compute_orb_signal(bars: list[dict[str, Any]], breakout_time_et: str = "09:35:00") -> dict[str, Any]:
    opening_bars = [bar for bar in bars if "09:30:00" <= _time_part(bar["timestamp_et"]) < breakout_time_et]
    breakout_bars = [bar for bar in bars if _time_part(bar["timestamp_et"]) >= breakout_time_et]
    if not opening_bars or not breakout_bars:
        raise StrategySpecError("ORB requires opening range bars and at least one breakout bar")

    opening_high = max(bar["high"] for bar in opening_bars)
    opening_low = min(bar["low"] for bar in opening_bars)
    first_breakout = sorted(breakout_bars, key=lambda bar: bar["timestamp_et"])[0]
    close = first_breakout["close"]
    if close > opening_high:
        decision = "call_breakout"
    elif close < opening_low:
        decision = "put_breakout"
    else:
        decision = "no_trade"

    return {
        "decision": decision,
        "opening_high": opening_high,
        "opening_low": opening_low,
        "breakout_timestamp_et": first_breakout["timestamp_et"],
        "breakout_close": close,
    }


def construct_subsystem_a_vertical(
    option_quotes: list[dict[str, Any]],
    direction: str,
    underlying_price: float,
    width: float = 2.0,
    min_long_gap: float = 0.96,
    max_long_gap: float = 2.0,
) -> list[dict[str, Any]]:
    if direction not in {"call", "put"}:
        raise StrategySpecError("Sub-System A direction must be call or put")
    if min_long_gap < 0 or max_long_gap < min_long_gap:
        raise StrategySpecError("Sub-System A long strike gap band is invalid")

    quotes = sorted(
        [quote for quote in option_quotes if quote["right"] == direction],
        key=lambda quote: quote["strike"],
    )
    if len(quotes) < 2:
        raise StrategySpecError("Sub-System A requires at least two strikes")

    if direction == "call":
        long_candidates = [q for q in quotes if min_long_gap <= q["strike"] - underlying_price <= max_long_gap]
        long_quote = min(long_candidates, key=lambda q: q["strike"], default=None)
        if long_quote is None:
            raise StrategySpecError("No call long strike inside configured breakout gap band")
        short_quote = _find_quote_by_strike(quotes, long_quote["strike"] + width)
        if short_quote is None:
            short_quote = next((q for q in quotes if q["strike"] > long_quote["strike"]), None)
    else:
        long_candidates = [q for q in quotes if min_long_gap <= underlying_price - q["strike"] <= max_long_gap]
        long_quote = max(long_candidates, key=lambda q: q["strike"], default=None)
        if long_quote is None:
            raise StrategySpecError("No put long strike inside configured breakout gap band")
        short_quote = _find_quote_by_strike(quotes, long_quote["strike"] - width)
        if short_quote is None:
            lower_quotes = [q for q in quotes if q["strike"] < long_quote["strike"]]
            short_quote = max(lower_quotes, key=lambda q: q["strike"], default=None)

    if short_quote is None:
        raise StrategySpecError("No valid short strike for vertical")

    return [
        make_option_leg("sub_a_long", long_quote, "buy", 1),
        make_option_leg("sub_a_short", short_quote, "sell", 1),
    ]


def construct_subsystem_b_capped_put_ratio(
    option_quotes: list[dict[str, Any]],
    underlying_price: float,
    short_moneyness: float = 0.99,
) -> list[dict[str, Any]]:
    puts = sorted([quote for quote in option_quotes if quote["right"] == "put"], key=lambda quote: quote["strike"])
    if len(puts) < 3:
        raise StrategySpecError("Sub-System B requires at least three put strikes")

    near_quote = min(puts, key=lambda quote: abs(quote["strike"] - underlying_price))
    target_short = underlying_price * short_moneyness
    short_candidates = [quote for quote in puts if quote["strike"] <= target_short]
    if not short_candidates:
        raise StrategySpecError("No far-OTM short put candidate")
    short_quote = max(short_candidates, key=lambda quote: quote["strike"])
    wing_candidates = [quote for quote in puts if quote["strike"] < short_quote["strike"]]
    if not wing_candidates:
        raise StrategySpecError("Protective wing is required for capped risk")
    wing_quote = max(wing_candidates, key=lambda quote: quote["strike"])

    return [
        make_option_leg("sub_b_long_near", near_quote, "buy", 1),
        make_option_leg("sub_b_short_ratio", short_quote, "sell", 2),
        make_option_leg("sub_b_long_wing", wing_quote, "buy", 1),
    ]


def evaluate_quant_filters(
    vix_vxv: dict[str, Any],
    macro_events: list[dict[str, Any]],
    trade_date: str,
    vix_range: tuple[float, float] = (15.0, 25.0),
) -> dict[str, Any]:
    reasons: list[str] = []
    allowed = True
    vix = vix_vxv["vix_close"]
    if not (vix_range[0] <= vix <= vix_range[1]):
        allowed = False
        reasons.append(f"VIX {vix} outside {vix_range[0]}-{vix_range[1]}")

    blocked_types = {"FOMC", "CPI", "NFP", "FED_CHAIR"}
    for event in macro_events:
        event_date = event["event_timestamp_et"].split("T")[0]
        if event_date == trade_date and event["event_type"] in blocked_types and event["importance"] == "high":
            allowed = False
            reasons.append(f"blocked macro event: {event['event_type']}")

    if not reasons:
        reasons.append("quant filters allow trade")
    return {"allowed": allowed, "reasons": reasons}


def evaluate_novi_proxy(volume_record: dict[str, Any] | None) -> dict[str, Any]:
    if not volume_record or "customer_buy_volume" not in volume_record or "customer_sell_volume" not in volume_record:
        return {"status": "unknown", "novi": None, "regime": "unknown", "reason": "NOVI inputs unavailable"}
    novi = volume_record["customer_buy_volume"] - volume_record["customer_sell_volume"]
    if novi < 0:
        regime = "positive_net_gamma_proxy"
    elif novi > 0:
        regime = "negative_net_gamma_proxy"
    else:
        regime = "neutral"
    return {"status": "available", "novi": novi, "regime": regime, "reason": "NOVI proxy computed"}


def dry_run_deepseek_assessment(
    news_items: list[dict[str, Any]],
    vix_vxv: dict[str, Any],
    created_at_et: str,
    model: str = "deepseek-dry-run",
) -> dict[str, Any]:
    prompt_text = "Assess SPY 0DTE volatility, directional bias, and tail-risk condition."
    input_blob = json.dumps({"news_items": news_items, "vix_vxv": vix_vxv}, ensure_ascii=False, sort_keys=True)
    panic_terms = {"panic", "war", "banking crisis", "emergency"}
    text = " ".join(item.get("headline", "").lower() for item in news_items)
    decision = "block" if vix_vxv["vix_close"] > 30 or any(term in text for term in panic_terms) else "allow"
    output_text = f"Dry-run DeepSeek assessment: decision={decision}; no live API call was made."
    return {
        "record_type": "llm_assessment",
        "schema_version": SCHEMA_VERSION,
        "assessment_id": _stable_id("llm", input_blob + created_at_et + model),
        "created_at_et": created_at_et,
        "provider": "DeepSeek",
        "model": model,
        "prompt_version": "m4-dry-run-v1",
        "input_hash": _sha256_text(input_blob),
        "prompt_text": prompt_text,
        "output_text": output_text,
        "decision": decision,
    }


def build_strategy_intent(
    strategy_id: str,
    decision: str,
    reasons: list[str],
    entry_time_et: str,
    legs: list[dict[str, Any]],
) -> dict[str, Any]:
    intent = {
        "record_type": "strategy_intent",
        "schema_version": SCHEMA_VERSION,
        "intent_id": _stable_id("intent", strategy_id + decision + entry_time_et + json.dumps(legs, sort_keys=True)),
        "created_at_et": entry_time_et,
        "strategy_id": strategy_id,
        "decision": decision,
        "reasons": reasons,
        "entry_time_et": entry_time_et,
        "legs": [leg["leg_id"] for leg in legs],
    }
    errors = validate_record(intent, load_schema())
    if errors:
        raise StrategySpecError("\n".join(errors))
    return intent


def make_option_leg(leg_id_seed: str, quote: dict[str, Any], side: str, quantity: int) -> dict[str, Any]:
    leg = {
        "record_type": "option_leg",
        "schema_version": SCHEMA_VERSION,
        "leg_id": _stable_id("leg", f"{leg_id_seed}-{quote['right']}-{quote['strike']}-{side}-{quantity}"),
        "underlying": quote["underlying"],
        "expiration_date": quote["expiration_date"],
        "right": quote["right"],
        "strike": quote["strike"],
        "side": side,
        "quantity": quantity,
    }
    errors = validate_record(leg, load_schema())
    if errors:
        raise StrategySpecError("\n".join(errors))
    return leg


def _find_quote_by_strike(quotes: list[dict[str, Any]], strike: float) -> dict[str, Any] | None:
    return next((quote for quote in quotes if quote["strike"] == strike), None)


def _time_part(timestamp_et: str) -> str:
    return datetime.fromisoformat(timestamp_et).time().isoformat()


def _stable_id(prefix: str, text: str) -> str:
    return f"{prefix}-{_sha256_text(text)[:16]}"


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
