from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.opra_statistics_schema import validate_opra_statistics_summary

LOGGER = logging.getLogger(__name__)
DEFAULT_API_KEY_ENV = "DATABENTO_API_KEY"
DATABENTO_API_KEY_ENV_ALIASES = ("DATABENTO_SPY0DTE_API", "DATABENTO_API_MO", "DATABENTO_API_AI")
DEFAULT_METADATA_REPORT = PROJECT_ROOT / "reports" / "data_cost" / "databento_opra_statistics_oi_probe_2024_01_03_schema.json"
DEFAULT_RAW_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "spy_0dte"
    / "databento"
    / "opra_statistics_oi_probe_2024_01_03"
    / "2024-01-03_full_utc_day_statistics.dbn.zst"
)
DEFAULT_JSON_REPORT = PROJECT_ROOT / "reports" / "data_cost" / "databento_opra_statistics_oi_download_probe_2024_01_03.json"
DEFAULT_MD_REPORT = PROJECT_ROOT / "reports" / "data_cost" / "databento_opra_statistics_oi_download_probe_2024_01_03.md"

DATASET = "OPRA.PILLAR"
SCHEMA = "statistics"
SYMBOLS = ["SPY.OPT"]
STYPE_IN = "parent"
START = "2024-01-03T00:00:00+00:00"
END = "2024-01-04T00:00:00+00:00"
WINDOW = "2024-01-03_full_utc_day_statistics"
STAT_TYPE_NAMES = {
    9: "OPEN_INTEREST",
    11: "CLOSE_PRICE",
}
STAT_UPDATE_ACTION_NAMES = {
    1: "NEW",
}
_ENUM_DRIFT_WARNED: set[tuple[str, int]] = set()


def build_probe_plan(metadata_report_path: Path = DEFAULT_METADATA_REPORT) -> dict[str, Any]:
    metadata = json.loads(metadata_report_path.read_text(encoding="utf-8"))
    estimate = metadata.get("full_day_cost_estimates_usd", {}).get("full_utc_day_2024_01_03")
    if estimate is None:
        raise ValueError(f"metadata report missing full-day cost estimate: {metadata_report_path}")
    return {
        "dataset": DATASET,
        "schema": SCHEMA,
        "symbols": SYMBOLS,
        "stype_in": STYPE_IN,
        "start": START,
        "end": END,
        "window": WINDOW,
        "estimated_cost_usd": float(estimate),
        "metadata_report": str(metadata_report_path),
    }


def execute_download(plan: dict[str, Any], raw_path: Path, api_key_env: str = DEFAULT_API_KEY_ENV) -> dict[str, Any]:
    api_key = _databento_api_key_from_env(api_key_env)
    if not api_key:
        raise RuntimeError(f"missing Databento API key environment variable: {_databento_env_names(api_key_env)}")
    import databento as db  # type: ignore

    raw_path.parent.mkdir(parents=True, exist_ok=True)
    source = "cache"
    if raw_path.exists() and raw_path.stat().st_size == 0:
        raw_path.unlink()
    if not raw_path.exists():
        temp_path = raw_path.with_name(f"{raw_path.name}.download")
        if temp_path.exists():
            temp_path.unlink()
        client = db.Historical(api_key)
        client.timeseries.get_range(
            dataset=plan["dataset"],
            symbols=plan["symbols"],
            schema=plan["schema"],
            stype_in=plan["stype_in"],
            start=plan["start"],
            end=plan["end"],
            path=temp_path,
        )
        temp_path.replace(raw_path)
        source = "downloaded"
    return {
        "source": source,
        "raw_path": str(raw_path),
        "bytes": raw_path.stat().st_size,
        "sha256": _sha256(raw_path),
    }


def inspect_statistics_file(raw_path: Path) -> dict[str, Any]:
    import databento as db  # type: ignore

    store = db.DBNStore.from_file(raw_path)
    frame = store.to_df()
    return summarize_statistics_frame(
        frame,
        raw_path,
        {
            "dataset": str(store.dataset),
            "schema": str(store.schema),
            "start": str(store.start),
            "end": str(store.end),
            "stype_in": str(store.stype_in),
            "symbols": list(store.symbols or []),
        },
    )


def summarize_statistics_frame(frame: Any, raw_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    row_count = int(len(frame))
    columns = list(frame.columns)
    stat_type_counts = _value_counts(frame, "stat_type", _stat_type_name)
    update_action_counts = _value_counts(frame, "update_action", _update_action_name)
    open_interest_rows = _rows_matching_stat_type(frame, "OPEN_INTEREST")
    open_interest_quantity = _numeric_summary(open_interest_rows, "quantity")
    open_interest_price = _numeric_summary(open_interest_rows, "price")
    unique_symbols = _unique_strings(frame, "symbol")

    ts_index_start = None
    ts_index_end = None
    if row_count and getattr(frame, "index", None) is not None:
        ts_index_start = str(frame.index.min())
        ts_index_end = str(frame.index.max())

    return {
        "raw_path": str(raw_path),
        "bytes": raw_path.stat().st_size if raw_path.exists() else 0,
        "metadata": metadata,
        "row_count": row_count,
        "columns": columns,
        "ts_index_start": ts_index_start,
        "ts_index_end": ts_index_end,
        "has_stat_type": "stat_type" in columns,
        "has_quantity": "quantity" in columns,
        "has_price": "price" in columns,
        "stat_type_counts": stat_type_counts,
        "update_action_counts": update_action_counts,
        "open_interest_record_count": int(len(open_interest_rows)),
        "open_interest_quantity": open_interest_quantity,
        "open_interest_price": open_interest_price,
        "unique_symbol_count": len(unique_symbols),
        "symbol_examples": unique_symbols[:5],
        "timestamp_semantics": {
            "index_name": str(getattr(frame.index, "name", "")) if getattr(frame, "index", None) is not None else None,
            "ts_event_column_present": "ts_event" in columns,
            "ts_ref_column_present": "ts_ref" in columns,
            "ts_recv_column_present": "ts_recv" in columns,
            "note": "Databento DBN dataframe index is used as the observed event/receive time for this probe; reports must not treat full-day statistics as intraday decision-time quotes without a later timestamp mapping rule.",
        },
    }


def build_result(plan: dict[str, Any], download: dict[str, Any] | None, inspection: dict[str, Any] | None) -> dict[str, Any]:
    blockers: list[str] = []
    schema_errors: list[str] = []
    status = "planned"
    if download is None or inspection is None:
        blockers.append("requires_download_and_inspection")
    else:
        status = "pass"
        schema_errors = validate_opra_statistics_summary(inspection)
        blockers.extend(f"opra_statistics_schema:{error}" for error in schema_errors)
        if inspection["row_count"] <= 0:
            blockers.append("requires_statistics_records")
        if not inspection["has_stat_type"]:
            blockers.append("requires_stat_type_field")
        if inspection["open_interest_record_count"] <= 0:
            blockers.append("requires_open_interest_records")
        if blockers:
            status = "blocked"
    return {
        "mode": "opra_statistics_oi_download_probe",
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "blockers": blockers,
        "plan": plan,
        "download": download,
        "inspection": inspection,
        "opra_statistics_schema_errors": schema_errors,
        "research_use_decision": _research_use_decision(status, blockers, inspection),
    }


def render_markdown(result: dict[str, Any]) -> str:
    plan = result["plan"]
    download = result.get("download") or {}
    inspection = result.get("inspection") or {}
    oi_quantity = inspection.get("open_interest_quantity") or {}
    stat_counts = inspection.get("stat_type_counts") or {}
    top_stats = ", ".join(f"`{name}`={count}" for name, count in sorted(stat_counts.items(), key=lambda item: item[1], reverse=True)[:8])
    blockers = ", ".join(f"`{item}`" for item in result["blockers"]) or "-"
    return "\n".join(
        [
            "# Databento OPRA Statistics/OI Download Probe",
            "",
            f"- **Created at UTC**: `{result['created_at_utc']}`",
            f"- **Status**: `{result['status']}`",
            f"- **Blockers**: {blockers}",
            f"- **Dataset/schema**: `{plan['dataset']}` / `{plan['schema']}`",
            f"- **Symbol**: `{', '.join(plan['symbols'])}`",
            f"- **Window**: `{plan['start']}` to `{plan['end']}`",
            f"- **Estimated cost logged before download**: `${plan['estimated_cost_usd']}`",
            f"- **Download source**: `{download.get('source', 'not_run')}`",
            f"- **Raw path**: `{download.get('raw_path', '')}`",
            f"- **Bytes**: {download.get('bytes', 0)}",
            f"- **SHA-256**: `{download.get('sha256', '')}`",
            "",
            "## Inspection",
            "",
            f"- **Rows**: {inspection.get('row_count', 0)}",
            f"- **Index timestamp range**: `{inspection.get('ts_index_start')}` to `{inspection.get('ts_index_end')}`",
            f"- **Columns**: `{', '.join(inspection.get('columns', []))}`",
            f"- **Top stat types**: {top_stats or '-'}",
            f"- **Open-interest records**: {inspection.get('open_interest_record_count', 0)}",
            f"- **Open-interest quantity min/mean/max**: `{oi_quantity.get('min')}` / `{oi_quantity.get('mean')}` / `{oi_quantity.get('max')}`",
            f"- **Unique symbols**: {inspection.get('unique_symbol_count', 0)}",
            "",
            "## Decision",
            "",
            f"- {result['research_use_decision']}",
            "- This is a data-source probe, not a strategy experiment. Do not write a research log for it.",
            "",
        ]
    )


def write_outputs(result: dict[str, Any], json_report: Path, md_report: Path) -> None:
    json_report.parent.mkdir(parents=True, exist_ok=True)
    json_report.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_report.parent.mkdir(parents=True, exist_ok=True)
    md_report.write_text(render_markdown(result), encoding="utf-8")


def _research_use_decision(status: str, blockers: list[str], inspection: dict[str, Any] | None) -> str:
    if status != "pass" or not inspection:
        return "Blocked: OPRA statistics cannot be used for gamma/OI research until the listed blockers are resolved."
    return (
        "Usable as a reference-style open-interest input for further feasibility work, with a timing caveat: "
        "full-day statistics must be mapped to a valid decision timestamp before any strategy test uses them."
    )


def _value_counts(frame: Any, column: str, normalizer: Any) -> dict[str, int]:
    if column not in frame:
        return {}
    counts: dict[str, int] = {}
    for value, count in frame[column].value_counts(dropna=False).items():
        counts[normalizer(value)] = int(count)
    return counts


def _rows_matching_stat_type(frame: Any, expected_name: str) -> Any:
    if "stat_type" not in frame:
        return frame.iloc[0:0]
    mask = frame["stat_type"].map(_stat_type_name) == expected_name
    return frame[mask]


def _numeric_summary(frame: Any, column: str) -> dict[str, float | int | None]:
    if column not in frame or len(frame) == 0:
        return {"count": 0, "min": None, "mean": None, "max": None}
    series = frame[column].dropna()
    if len(series) == 0:
        return {"count": 0, "min": None, "mean": None, "max": None}
    return {
        "count": int(len(series)),
        "min": float(series.min()),
        "mean": float(series.mean()),
        "max": float(series.max()),
    }


def _unique_strings(frame: Any, column: str) -> list[str]:
    if column not in frame:
        return []
    return sorted(str(value) for value in frame[column].dropna().unique())


def _stat_type_name(value: Any) -> str:
    return _enum_like_name(value, "StatType", STAT_TYPE_NAMES)


def _update_action_name(value: Any) -> str:
    return _enum_like_name(value, "StatUpdateAction", STAT_UPDATE_ACTION_NAMES)


def _enum_like_name(value: Any, enum_name: str, hermetic_names: dict[int, str] | None = None) -> str:
    name = getattr(value, "name", None)
    if isinstance(name, str):
        return name
    try:
        integer_value = int(value)
    except (TypeError, ValueError):
        integer_value = None
    vendor_name = _vendor_enum_name(value, enum_name)
    try:
        drift_key = (enum_name, int(value))
    except (TypeError, ValueError):
        drift_key = (enum_name, -1)
    if integer_value is not None and hermetic_names and integer_value in hermetic_names:
        embedded_name = hermetic_names[integer_value]
        if vendor_name is not None and vendor_name != embedded_name and drift_key not in _ENUM_DRIFT_WARNED:
            LOGGER.error(
                "Databento enum drift detected for %s(%s): embedded=%s vendored=%s",
                enum_name,
                integer_value,
                embedded_name,
                vendor_name,
            )
            _ENUM_DRIFT_WARNED.add(drift_key)
        return embedded_name
    if vendor_name is not None:
        return vendor_name
    return str(value)


def _vendor_enum_name(value: Any, enum_name: str) -> str | None:
    try:
        import databento as db  # type: ignore

        enum_type = getattr(db, enum_name)
        enum_value = enum_type(int(value))
        enum_value_name = getattr(enum_value, "name", None)
        if isinstance(enum_value_name, str):
            return enum_value_name
    except Exception:
        return None
    return None


def _databento_api_key_from_env(api_key_env: str = DEFAULT_API_KEY_ENV) -> str | None:
    api_key = os.environ.get(api_key_env)
    if api_key or api_key_env != DEFAULT_API_KEY_ENV:
        return api_key
    for alias in DATABENTO_API_KEY_ENV_ALIASES:
        api_key = os.environ.get(alias)
        if api_key:
            return api_key
    return None


def _databento_env_names(api_key_env: str = DEFAULT_API_KEY_ENV) -> str:
    if api_key_env != DEFAULT_API_KEY_ENV:
        return api_key_env
    return " or ".join((DEFAULT_API_KEY_ENV, *DATABENTO_API_KEY_ENV_ALIASES))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Download and inspect one full UTC day of Databento OPRA statistics for SPY.OPT.")
    parser.add_argument("--metadata-report", type=Path, default=DEFAULT_METADATA_REPORT)
    parser.add_argument("--raw-path", type=Path, default=DEFAULT_RAW_PATH)
    parser.add_argument("--json-report", type=Path, default=DEFAULT_JSON_REPORT)
    parser.add_argument("--md-report", type=Path, default=DEFAULT_MD_REPORT)
    parser.add_argument("--api-key-env", default=DEFAULT_API_KEY_ENV)
    parser.add_argument("--execute", action="store_true", help="Download if local raw file is missing, then inspect.")
    args = parser.parse_args()

    plan = build_probe_plan(args.metadata_report)
    download = execute_download(plan, args.raw_path, args.api_key_env) if args.execute else None
    inspection = inspect_statistics_file(args.raw_path) if args.execute else None
    result = build_result(plan, download, inspection)
    write_outputs(result, args.json_report, args.md_report)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
