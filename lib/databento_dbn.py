from __future__ import annotations

from datetime import date, datetime, time
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from lib.options import parse_databento_option_symbol


ET = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")


def load_spy_ohlcv_bars(path: Path, trade_date: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    import databento as db  # type: ignore

    records = db.DBNStore.from_file(path).to_ndarray()
    rows = []
    for item in records:
        ts_utc = datetime.fromtimestamp(int(item["ts_event"]) / 1_000_000_000, tz=UTC)
        ts_et = ts_utc.astimezone(ET)
        if ts_et.date().isoformat() != trade_date:
            continue
        rows.append(
            {
                "timestamp_utc": ts_utc.isoformat(),
                "timestamp_et": ts_et.isoformat(),
                "open": float(item["open"]) / 1_000_000_000,
                "high": float(item["high"]) / 1_000_000_000,
                "low": float(item["low"]) / 1_000_000_000,
                "close": float(item["close"]) / 1_000_000_000,
                "volume": int(item["volume"]),
            }
        )
    return rows, {
        "row_count": len(rows),
        "min_timestamp_et": rows[0]["timestamp_et"] if rows else None,
        "max_timestamp_et": rows[-1]["timestamp_et"] if rows else None,
        "has_0935_bar": any(row["timestamp_et"][11:19] == "09:35:00" for row in rows),
        "has_1545_bar": any(row["timestamp_et"][11:19] == "15:45:00" for row in rows),
    }


def load_option_snapshots(
    path: Path,
    trade_date: str,
    times_et: tuple[str, ...] = ("09:35:00", "15:45:00"),
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    import databento as db  # type: ignore
    import numpy as np  # type: ignore

    store = db.DBNStore.from_file(path)
    records = store.to_ndarray()
    trade_day = date.fromisoformat(trade_date)
    target_ns = {
        value: int(datetime.combine(trade_day, time.fromisoformat(value), tzinfo=ET).astimezone(UTC).timestamp() * 1_000_000_000)
        for value in times_et
    }
    snapshot_mask = np.isin(records["ts_recv"], list(target_ns.values()))
    snapshots = records[snapshot_mask]
    symbol_by_instrument = {
        int(mapping["symbol"]): raw_symbol
        for raw_symbol, mappings in store.mappings.items()
        for mapping in mappings
        if mapping["start_date"] <= trade_day < mapping["end_date"]
    }
    time_by_ns = {timestamp: value for value, timestamp in target_ns.items()}
    quotes_by_time: dict[str, list[dict[str, Any]]] = {value: [] for value in times_et}
    invalid_quote_count = 0
    non_zero_dte_count = 0
    parse_error_count = 0
    for item in snapshots:
        timestamp_ns = int(item["ts_recv"])
        time_et = time_by_ns[timestamp_ns]
        ts_et = datetime.fromtimestamp(timestamp_ns / 1_000_000_000, tz=UTC).astimezone(ET)
        symbol = symbol_by_instrument.get(int(item["instrument_id"]), "").strip()
        try:
            parsed = parse_databento_option_symbol(symbol)
        except ValueError:
            parse_error_count += 1
            continue
        if parsed["expiration_date"] != trade_date:
            non_zero_dte_count += 1
            continue
        bid = float(item["bid_px_00"]) / 1_000_000_000
        ask = float(item["ask_px_00"]) / 1_000_000_000
        if bid <= 0 or ask <= 0 or ask < bid:
            invalid_quote_count += 1
            continue
        quotes_by_time[time_et].append(
            {
                **parsed,
                "symbol": symbol,
                "quote_timestamp_et": ts_et.isoformat(),
                "bid": bid,
                "ask": ask,
                "mid": round((bid + ask) / 2, 4),
                "bid_size": int(item["bid_sz_00"]),
                "ask_size": int(item["ask_sz_00"]),
            }
        )
    return quotes_by_time, {
        "raw_row_count": int(len(records)),
        "snapshot_row_count": int(len(snapshots)),
        "valid_0dte_snapshot_count": sum(len(rows) for rows in quotes_by_time.values()),
        "valid_count_by_time": {key: len(rows) for key, rows in quotes_by_time.items()},
        "invalid_quote_count": invalid_quote_count,
        "non_zero_dte_snapshot_count": non_zero_dte_count,
        "symbol_parse_error_count": parse_error_count,
        "min_timestamp_et": _ns_to_et(int(records["ts_recv"].min())) if len(records) else None,
        "max_timestamp_et": _ns_to_et(int(records["ts_recv"].max())) if len(records) else None,
    }


def _ns_to_et(timestamp_ns: int) -> str:
    return datetime.fromtimestamp(timestamp_ns / 1_000_000_000, tz=UTC).astimezone(ET).isoformat()
