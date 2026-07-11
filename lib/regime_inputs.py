from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from lib.io import load_jsonl


def load_vix_vxv(path: Path) -> list[dict[str, Any]]:
    return sorted(load_jsonl(path), key=lambda row: str(row["date"]))


def previous_vix_record(trade_date: str, rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    target = date.fromisoformat(trade_date)
    candidates = [row for row in rows if date.fromisoformat(str(row["date"])) < target]
    return candidates[-1] if candidates else None


def load_macro_events_by_date(path: Path) -> dict[str, list[dict[str, Any]]]:
    events: dict[str, list[dict[str, Any]]] = {}
    for record in load_jsonl(path):
        if record.get("record_type") != "macro_event":
            continue
        event_date = str(record["event_timestamp_et"])[:10]
        events.setdefault(event_date, []).append(record)
    return {key: sorted(rows, key=lambda row: str(row["event_timestamp_et"])) for key, rows in events.items()}
