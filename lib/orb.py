from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any


def opening_breakout(bars: list[dict[str, Any]], decision_time: str = "09:35:00") -> dict[str, Any]:
    opening = [row for row in bars if "09:30:00" <= row["timestamp_et"][11:19] < decision_time]
    decision = next((row for row in bars if row["timestamp_et"][11:19] == decision_time), None)
    if not opening or decision is None:
        return {"status": "missing_bars", "direction": None}
    opening_high = max(float(row["high"]) for row in opening)
    opening_low = min(float(row["low"]) for row in opening)
    decision_close = float(decision["close"])
    direction = "call" if decision_close > opening_high else "put" if decision_close < opening_low else None
    return {
        "status": "measured",
        "direction": direction,
        "opening_high": opening_high,
        "opening_low": opening_low,
        "decision_close": decision_close,
        "decision_timestamp_et": decision["timestamp_et"],
        "signal_available_timestamp_et": (
            datetime.fromisoformat(decision["timestamp_et"]) + timedelta(minutes=1)
        ).isoformat(),
        "bar_timestamp_semantics": "interval_start",
    }
