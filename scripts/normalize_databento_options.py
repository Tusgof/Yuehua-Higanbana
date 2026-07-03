from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_m2_contracts import load_schema, validate_record


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = PROJECT_ROOT / "data" / "raw" / "spy_0dte" / "databento" / "one_month_pilot"
OUTPUT_PATH = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "databento" / "one_month_pilot" / "option_quote.jsonl"
REGISTRY_PATH = PROJECT_ROOT / "data" / "registry" / "datasets.jsonl"
SUMMARY_PATH = PROJECT_ROOT / "reports" / "data_cost" / "databento_normalization_summary.json"
ET = ZoneInfo("America/New_York")
SYMBOL_RE = re.compile(r"^([A-Z]+)\s+(\d{6})([CP])(\d{8})$")


def normalize_raw_root(raw_root: Path = RAW_ROOT, output_path: Path = OUTPUT_PATH, registry_path: Path = REGISTRY_PATH) -> dict[str, Any]:
    files = sorted(raw_root.glob("*.dbn.zst"))
    if not files:
        raise ValueError(f"no Databento raw files found under {raw_root}")

    schema = load_schema()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.parent.mkdir(parents=True, exist_ok=True)

    total_input_rows = 0
    total_output_rows = 0
    skipped_non_0dte = 0
    skipped_invalid_quote = 0
    coverage_dates: set[str] = set()
    file_summaries: list[dict[str, Any]] = []

    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        for path in files:
            file_result = normalize_raw_file(path, handle, schema)
            total_input_rows += file_result["input_rows"]
            total_output_rows += file_result["output_rows"]
            skipped_non_0dte += file_result["skipped_non_0dte"]
            skipped_invalid_quote += file_result["skipped_invalid_quote"]
            coverage_dates.add(file_result["trade_date"])
            file_summaries.append(file_result)

    manifest = build_manifest(raw_root, files, sorted(coverage_dates))
    errors = validate_record(manifest, schema)
    if errors:
        raise ValueError("\n".join(errors))
    if not registry_contains(registry_path, manifest):
        with registry_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(manifest, ensure_ascii=False, sort_keys=True) + "\n")

    return {
        "provider": "Databento",
        "raw_root": str(raw_root),
        "output_path": str(output_path),
        "registry_path": str(registry_path),
        "file_count": len(files),
        "input_rows": total_input_rows,
        "output_rows": total_output_rows,
        "skipped_non_0dte": skipped_non_0dte,
        "skipped_invalid_quote": skipped_invalid_quote,
        "coverage_start": min(coverage_dates),
        "coverage_end": max(coverage_dates),
        "manifest": manifest,
        "files": file_summaries,
    }


def normalize_raw_file(path: Path, handle: Any, schema: dict[str, Any]) -> dict[str, Any]:
    import databento as db  # type: ignore

    trade_date = trade_date_from_window_name(path.name)
    frame = db.DBNStore.from_file(path).to_df()
    input_rows = int(len(frame))
    if input_rows == 0:
        return {
            "file": str(path),
            "trade_date": trade_date,
            "input_rows": 0,
            "output_rows": 0,
            "skipped_non_0dte": 0,
            "skipped_invalid_quote": 0,
        }

    symbol_parts = frame["symbol"].astype(str).str.strip().str.extract(SYMBOL_RE)
    yy = symbol_parts[1].str.slice(0, 2)
    mm = symbol_parts[1].str.slice(2, 4)
    dd = symbol_parts[1].str.slice(4, 6)
    expiration = "20" + yy + "-" + mm + "-" + dd
    is_0dte = (symbol_parts[0] == "SPY") & (expiration == trade_date)
    valid_quote = valid_quote_mask(frame)
    selected = frame[is_0dte & valid_quote].copy()
    selected["expiration_date"] = expiration[is_0dte & valid_quote]
    selected["right"] = symbol_parts[2][is_0dte & valid_quote].map({"C": "call", "P": "put"})
    selected["strike"] = symbol_parts[3][is_0dte & valid_quote].astype(int) / 1000

    skipped_non_0dte = int((~is_0dte).sum())
    skipped_invalid_quote = int((is_0dte & ~valid_quote).sum())
    output_rows = int(len(selected))
    sample_validated = False

    for row in selected.itertuples():
        record = {
            "record_type": "option_quote",
            "schema_version": "m2.0",
            "underlying": "SPY",
            "quote_timestamp_et": ts_to_et_iso(row.Index),
            "expiration_date": row.expiration_date,
            "dte": 0,
            "right": row.right,
            "strike": float(row.strike),
            "bid": float(row.bid_px_00),
            "ask": float(row.ask_px_00),
            "bid_size": int(row.bid_sz_00),
            "ask_size": int(row.ask_sz_00),
            "provider": "Databento",
            "source": str(path),
            "databento_symbol": str(row.symbol).strip(),
            "databento_window": path.stem.replace(".dbn", ""),
        }
        if not sample_validated:
            errors = validate_record(record, schema)
            if errors:
                raise ValueError(f"{path.name}: invalid normalized record: {'; '.join(errors)}")
            sample_validated = True
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    return {
        "file": str(path),
        "trade_date": trade_date,
        "input_rows": input_rows,
        "output_rows": output_rows,
        "skipped_non_0dte": skipped_non_0dte,
        "skipped_invalid_quote": skipped_invalid_quote,
    }


def valid_quote_mask(frame: Any) -> Any:
    return (frame["bid_px_00"] >= 0) & (frame["ask_px_00"] > 0) & (frame["ask_px_00"] >= frame["bid_px_00"])


def trade_date_from_window_name(name: str) -> str:
    return name[:10]


def ts_to_et_iso(value: Any) -> str:
    timestamp = value.to_pydatetime() if hasattr(value, "to_pydatetime") else value
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=ZoneInfo("UTC"))
    return timestamp.astimezone(ET).isoformat()


def build_manifest(raw_root: Path, files: list[Path], coverage_dates: list[str]) -> dict[str, Any]:
    raw_hash = combined_raw_hash(files)
    return {
        "record_type": "data_registry_manifest",
        "schema_version": "m2.0",
        "dataset_id": f"databento-one-month-pilot-{raw_hash[:12]}",
        "provider": "Databento",
        "source_url": str(raw_root),
        "ingested_at_et": datetime.now(ET).isoformat(timespec="seconds"),
        "coverage_start": coverage_dates[0],
        "coverage_end": coverage_dates[-1],
        "raw_sha256": raw_hash,
        "schema_name": "m2_contracts",
        "schema_version_applied": "m2.0",
        "license_notes": "Databento OPRA.PILLAR cbbo-1m local cache. User-approved one-month pilot download.",
    }


def combined_raw_hash(files: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(files):
        digest.update(path.name.encode("utf-8"))
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()


def registry_contains(path: Path, manifest: dict[str, Any]) -> bool:
    if not path.exists():
        return False
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        existing = json.loads(line)
        if existing.get("dataset_id") == manifest["dataset_id"] and existing.get("raw_sha256") == manifest["raw_sha256"]:
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize local Databento SPY 0DTE CBBO files to canonical option_quote JSONL.")
    parser.add_argument("--raw-root", type=Path, default=RAW_ROOT)
    parser.add_argument("--output-path", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--registry-path", type=Path, default=REGISTRY_PATH)
    parser.add_argument("--summary-path", type=Path, default=SUMMARY_PATH)
    args = parser.parse_args()

    result = normalize_raw_root(args.raw_root, args.output_path, args.registry_path)
    args.summary_path.parent.mkdir(parents=True, exist_ok=True)
    args.summary_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({key: result[key] for key in result if key != "files"}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
