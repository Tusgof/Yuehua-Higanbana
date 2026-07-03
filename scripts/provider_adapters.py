from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_m2_contracts import validate_record


SCHEMA_VERSION = "m2.0"


def parse_optionsdx_quote_csv(path: Path) -> list[dict]:
    """Parse an OptionsDX-like sample CSV into canonical option_quote records."""
    return _parse_quote_csv(
        path=path,
        provider="OptionsDX",
        source_prefix="optionsdx-like-csv",
        mapping={
            "quote_timestamp_et": "quote_time_et",
            "expiration_date": "expiration",
            "right": "option_type",
            "strike": "strike",
            "bid": "bid",
            "ask": "ask",
            "bid_size": "bid_size",
            "ask_size": "ask_size",
            "volume": "volume",
            "open_interest": "open_interest",
            "underlying_price": "underlying_price",
        },
        right_parser=_parse_right_text,
    )


def parse_thetadata_quote_csv(path: Path) -> list[dict]:
    """Parse a ThetaData-like sample CSV into canonical option_quote records."""
    return _parse_quote_csv(
        path=path,
        provider="ThetaData",
        source_prefix="thetadata-like-csv",
        mapping={
            "quote_timestamp_et": "timestamp",
            "expiration_date": "expiration",
            "right": "right",
            "strike": "strike",
            "bid": "bid",
            "ask": "ask",
            "bid_size": "bid_size",
            "ask_size": "ask_size",
            "volume": "volume",
            "open_interest": "open_interest",
            "underlying_price": "underlying_price",
        },
        right_parser=_parse_right_code,
    )


def validate_option_quotes(records: list[dict]) -> None:
    errors: list[str] = []
    for index, record in enumerate(records):
        for error in validate_record(record):
            errors.append(f"record[{index}]: {error}")
    if errors:
        raise ValueError("\n".join(errors))


def _parse_quote_csv(
    path: Path,
    provider: str,
    source_prefix: str,
    mapping: dict[str, str],
    right_parser: Callable[[str], str],
) -> list[dict]:
    rows = list(csv.DictReader(path.read_text(encoding="utf-8").splitlines()))
    records: list[dict] = []
    for row in rows:
        quote_timestamp = _required(row, mapping["quote_timestamp_et"])
        expiration_date = _required(row, mapping["expiration_date"])
        records.append(
            {
                "record_type": "option_quote",
                "schema_version": SCHEMA_VERSION,
                "underlying": "SPY",
                "quote_timestamp_et": quote_timestamp,
                "expiration_date": expiration_date,
                "dte": _same_day_dte(quote_timestamp, expiration_date),
                "right": right_parser(_required(row, mapping["right"])),
                "strike": _float(row, mapping["strike"]),
                "bid": _float(row, mapping["bid"]),
                "ask": _float(row, mapping["ask"]),
                "bid_size": _int(row, mapping["bid_size"]),
                "ask_size": _int(row, mapping["ask_size"]),
                "volume": _optional_int(row, mapping.get("volume")),
                "open_interest": _optional_int(row, mapping.get("open_interest")),
                "underlying_price": _optional_float(row, mapping.get("underlying_price")),
                "provider": provider,
                "source": f"{source_prefix}:{path.name}",
            }
        )
    validate_option_quotes(records)
    return records


def _required(row: dict[str, str], field: str) -> str:
    value = row.get(field, "").strip()
    if not value:
        raise ValueError(f"missing required column value: {field}")
    return value


def _float(row: dict[str, str], field: str) -> float:
    return float(_required(row, field))


def _int(row: dict[str, str], field: str) -> int:
    return int(float(_required(row, field)))


def _optional_float(row: dict[str, str], field: str | None) -> float | None:
    if not field or not row.get(field, "").strip():
        return None
    return float(row[field])


def _optional_int(row: dict[str, str], field: str | None) -> int | None:
    if not field or not row.get(field, "").strip():
        return None
    return int(float(row[field]))


def _parse_right_text(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"call", "c"}:
        return "call"
    if normalized in {"put", "p"}:
        return "put"
    raise ValueError(f"unknown option right: {value}")


def _parse_right_code(value: str) -> str:
    normalized = value.strip().upper()
    if normalized == "C":
        return "call"
    if normalized == "P":
        return "put"
    return _parse_right_text(value)


def _same_day_dte(quote_timestamp: str, expiration_date: str) -> float:
    quote_date = quote_timestamp[:10]
    if quote_date == expiration_date:
        return 0.0
    return 1.0


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]
    fixture_dir = project_root / "tests" / "fixtures" / "provider_samples"
    records = parse_optionsdx_quote_csv(fixture_dir / "optionsdx_option_quote_sample.csv")
    records.extend(parse_thetadata_quote_csv(fixture_dir / "thetadata_option_quote_sample.csv"))
    print(f"validated {len(records)} provider sample records")
