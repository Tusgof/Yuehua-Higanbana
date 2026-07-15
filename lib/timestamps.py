from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


EASTERN = ZoneInfo("America/New_York")


def parse_timestamp_et(value: str | datetime) -> datetime:
    """Parse an aware timestamp and normalize it to America/New_York."""
    timestamp = value if isinstance(value, datetime) else datetime.fromisoformat(value.replace("Z", "+00:00"))
    if timestamp.tzinfo is None:
        raise ValueError("timestamp must include a timezone offset")
    return timestamp.astimezone(EASTERN)


def timestamp_et_iso(value: str | datetime) -> str:
    return parse_timestamp_et(value).isoformat()


def is_available_by(value: str | datetime, decision_time: str | datetime) -> bool:
    return parse_timestamp_et(value) <= parse_timestamp_et(decision_time)


def require_available_by(value: str | datetime, decision_time: str | datetime, *, label: str = "input") -> None:
    if not is_available_by(value, decision_time):
        raise ValueError(f"{label} is not available by the decision timestamp")


def interval_close_available_at(interval_start: str | datetime, *, interval_minutes: int = 1) -> datetime:
    if interval_minutes <= 0:
        raise ValueError("interval_minutes must be positive")
    return parse_timestamp_et(interval_start) + timedelta(minutes=interval_minutes)


def require_interval_close_available_by(
    interval_start: str | datetime,
    decision_time: str | datetime,
    *,
    interval_minutes: int = 1,
    label: str = "bar close",
) -> None:
    available_at = interval_close_available_at(interval_start, interval_minutes=interval_minutes)
    if available_at > parse_timestamp_et(decision_time):
        raise ValueError(f"{label} is not available before the interval ends")


def require_execution_timeline(
    *,
    signal_available_timestamp: str | datetime,
    order_decision_timestamp: str | datetime,
    entry_quote_timestamp: str | datetime,
) -> None:
    signal = parse_timestamp_et(signal_available_timestamp)
    decision = parse_timestamp_et(order_decision_timestamp)
    entry = parse_timestamp_et(entry_quote_timestamp)
    if signal > decision:
        raise ValueError("signal is not available by the order decision timestamp")
    if decision > entry:
        raise ValueError("entry quote precedes the order decision timestamp")
