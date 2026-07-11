from __future__ import annotations

from datetime import datetime
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
