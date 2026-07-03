from __future__ import annotations

import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = PROJECT_ROOT / "schemas" / "m2_contracts.schema.json"


class ContractError(ValueError):
    pass


def load_schema(path: Path = SCHEMA_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_record(record: dict[str, Any], schema: dict[str, Any] | None = None) -> list[str]:
    schema = schema or load_schema()
    errors: list[str] = []
    record_type = record.get("record_type")
    specs = schema.get("records", {})
    spec = specs.get(record_type)
    if not spec:
        return [f"unknown record_type: {record_type!r}"]

    for field in spec.get("required", []):
        if field not in record:
            errors.append(f"{record_type}.{field} is required")

    for field, expected_type in spec.get("types", {}).items():
        if field in record and not _matches_type(record[field], expected_type):
            errors.append(f"{record_type}.{field} must be {expected_type}")

    for rule in spec.get("rules", []):
        errors.extend(_validate_rule(rule, record_type, record))

    return errors


def validate_records(records: list[dict[str, Any]], schema: dict[str, Any] | None = None) -> list[str]:
    schema = schema or load_schema()
    errors: list[str] = []
    for index, record in enumerate(records):
        for error in validate_record(record, schema):
            errors.append(f"record[{index}]: {error}")
    return errors


def validate_file(path: Path, schema: dict[str, Any] | None = None) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ContractError(f"{path} must contain a JSON array")
    return validate_records(payload, schema)


def _matches_type(value: Any, expected_type: str) -> bool:
    if expected_type == "string":
        return isinstance(value, str) and value != ""
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "datetime":
        return isinstance(value, str) and _parse_datetime(value) is not None
    if expected_type == "date":
        return isinstance(value, str) and _parse_date(value) is not None
    if expected_type == "sha256":
        return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None
    return False


def _parse_datetime(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _validate_rule(rule: str, record_type: str, record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if rule == "symbol_spy" and record.get("symbol") != "SPY":
        errors.append(f"{record_type}.symbol must be SPY")
    elif rule == "underlying_spy" and record.get("underlying") != "SPY":
        errors.append(f"{record_type}.underlying must be SPY")
    elif rule == "ohlc_consistent":
        o, h, l, c = (record.get("open"), record.get("high"), record.get("low"), record.get("close"))
        if all(isinstance(x, (int, float)) for x in [o, h, l, c]):
            if l > min(o, c) or h < max(o, c) or l > h:
                errors.append(f"{record_type}.OHLC is inconsistent")
    elif rule == "non_negative_volume" and record.get("volume", 0) < 0:
        errors.append(f"{record_type}.volume must be non-negative")
    elif rule == "right_call_or_put" and record.get("right") not in {"call", "put"}:
        errors.append(f"{record_type}.right must be call or put")
    elif rule == "bid_ask_valid":
        bid, ask = record.get("bid"), record.get("ask")
        if isinstance(bid, (int, float)) and isinstance(ask, (int, float)):
            if bid < 0 or ask < 0 or ask < bid:
                errors.append(f"{record_type}.bid/ask must be non-negative and ask >= bid")
    elif rule == "non_negative_sizes":
        for field in ("bid_size", "ask_size"):
            if record.get(field, 0) < 0:
                errors.append(f"{record_type}.{field} must be non-negative")
    elif rule == "positive_vol_indexes":
        for field in ("vix_close", "vxv_close"):
            if isinstance(record.get(field), (int, float)) and record[field] <= 0:
                errors.append(f"{record_type}.{field} must be positive")
    elif rule == "macro_importance_valid" and record.get("importance") not in {"low", "medium", "high"}:
        errors.append(f"{record_type}.importance must be low, medium, or high")
    elif rule == "llm_decision_valid" and record.get("decision") not in {"allow", "block", "unknown"}:
        errors.append(f"{record_type}.decision must be allow, block, or unknown")
    elif rule == "strategy_decision_valid" and record.get("decision") not in {"go", "no_go", "skip"}:
        errors.append(f"{record_type}.decision must be go, no_go, or skip")
    elif rule == "non_empty_reasons" and not record.get("reasons"):
        errors.append(f"{record_type}.reasons must not be empty")
    elif rule == "side_buy_or_sell" and record.get("side") not in {"buy", "sell"}:
        errors.append(f"{record_type}.side must be buy or sell")
    elif rule == "positive_quantity" and record.get("quantity", 0) <= 0:
        errors.append(f"{record_type}.quantity must be positive")
    elif rule == "non_negative_price" and record.get("price", 0) < 0:
        errors.append(f"{record_type}.price must be non-negative")
    elif rule == "trade_status_valid" and record.get("status") not in {"open", "closed", "skipped"}:
        errors.append(f"{record_type}.status must be open, closed, or skipped")
    elif rule == "defined_risk_non_negative" and record.get("max_defined_loss", 0) < 0:
        errors.append(f"{record_type}.max_defined_loss must be non-negative")
    elif rule == "non_negative_equity":
        for field in ("starting_equity", "ending_equity"):
            if record.get(field, 0) < 0:
                errors.append(f"{record_type}.{field} must be non-negative")
    elif rule == "non_negative_trade_count" and record.get("trade_count", 0) < 0:
        errors.append(f"{record_type}.trade_count must be non-negative")
    elif rule == "parameters_locked" and record.get("parameters_locked_before_oos") is not True:
        errors.append(f"{record_type}.parameters_locked_before_oos must be true")
    elif rule == "non_empty_metrics" and not record.get("metrics"):
        errors.append(f"{record_type}.metrics must not be empty")
    elif rule == "thai_report" and record.get("language") != "th":
        errors.append(f"{record_type}.language must be th")
    elif rule == "conclusion_valid" and record.get("conclusion") not in {"ผ่าน", "ไม่ผ่าน", "ยังสรุปไม่ได้"}:
        errors.append(f"{record_type}.conclusion is invalid")
    elif rule == "coverage_order":
        start = _parse_date(str(record.get("coverage_start", "")))
        end = _parse_date(str(record.get("coverage_end", "")))
        if start and end and start > end:
            errors.append(f"{record_type}.coverage_start must be <= coverage_end")
    return errors


if __name__ == "__main__":
    fixture = PROJECT_ROOT / "tests" / "fixtures" / "m2_valid_records.json"
    found_errors = validate_file(fixture)
    if found_errors:
        for found_error in found_errors:
            print(found_error)
        raise SystemExit(1)
    print(f"validated {fixture}")
