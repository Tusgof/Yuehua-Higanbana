from __future__ import annotations

from pathlib import Path
from typing import Any

from lib.io import load_json


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = PROJECT_ROOT / "schemas" / "opra_statistics_boundary.schema.json"


def load_opra_statistics_schema(path: Path = SCHEMA_PATH) -> dict[str, Any]:
    payload = load_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def validate_opra_statistics_summary(summary: dict[str, Any], schema: dict[str, Any] | None = None) -> list[str]:
    schema = schema or load_opra_statistics_schema()
    errors: list[str] = []
    for field in schema.get("required_summary_fields", []):
        if field not in summary:
            errors.append(f"summary.{field} is required")

    metadata = summary.get("metadata")
    if not isinstance(metadata, dict):
        errors.append("summary.metadata must be object")
        metadata = {}
    for field, expected in schema.get("metadata_requirements", {}).items():
        if metadata.get(field) != expected:
            errors.append(f"summary.metadata.{field} must be {expected}")

    if not isinstance(summary.get("row_count"), int) or summary.get("row_count", 0) <= 0:
        errors.append("summary.row_count must be positive integer")
    if summary.get("has_stat_type") is not True:
        errors.append("summary.has_stat_type must be true")
    if summary.get("has_quantity") is not True:
        errors.append("summary.has_quantity must be true")
    if not summary.get("ts_index_start") or not summary.get("ts_index_end"):
        errors.append("summary timestamp index range is required")
    if not isinstance(summary.get("unique_symbol_count"), int) or summary.get("unique_symbol_count", 0) <= 0:
        errors.append("summary.unique_symbol_count must be positive integer")

    stat_type_counts = summary.get("stat_type_counts")
    if not isinstance(stat_type_counts, dict):
        errors.append("summary.stat_type_counts must be object")
        stat_type_counts = {}
    for stat_type in schema.get("required_stat_types", []):
        if stat_type_counts.get(stat_type, 0) <= 0:
            errors.append(f"summary.stat_type_counts.{stat_type} must be positive")

    if not isinstance(summary.get("open_interest_record_count"), int) or summary.get("open_interest_record_count", 0) <= 0:
        errors.append("summary.open_interest_record_count must be positive integer")

    return errors
