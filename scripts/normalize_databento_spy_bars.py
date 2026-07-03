from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_m2_contracts import load_schema, validate_record


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "spy_0dte" / "databento" / "spy_bars" / "jan_2024_spy_ohlcv_1m.dbn.zst"
OUTPUT_PATH = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "databento" / "one_month_pilot" / "spy_bar.jsonl"
REGISTRY_PATH = PROJECT_ROOT / "data" / "registry" / "datasets.jsonl"
SUMMARY_PATH = PROJECT_ROOT / "reports" / "data_cost" / "databento_spy_bars_normalization_summary.json"
ET = ZoneInfo("America/New_York")


def normalize_raw_file(raw_path: Path = RAW_PATH, output_path: Path = OUTPUT_PATH, registry_path: Path = REGISTRY_PATH) -> dict[str, Any]:
    if not raw_path.exists():
        raise ValueError(f"Databento SPY bar raw file not found: {raw_path}")

    import databento as db  # type: ignore

    frame = db.DBNStore.from_file(raw_path).to_df()
    result = normalize_frame(frame, raw_path, output_path)
    manifest = build_manifest(raw_path, result["coverage_start"], result["coverage_end"])
    schema = load_schema()
    errors = validate_record(manifest, schema)
    if errors:
        raise ValueError("\n".join(errors))

    registry_path.parent.mkdir(parents=True, exist_ok=True)
    if not registry_contains(registry_path, manifest):
        with registry_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(manifest, ensure_ascii=False, sort_keys=True) + "\n")
    result["registry_path"] = str(registry_path)
    result["manifest"] = manifest
    return result


def normalize_frame(frame: Any, raw_path: Path, output_path: Path) -> dict[str, Any]:
    required_columns = {"open", "high", "low", "close", "volume", "symbol"}
    missing = sorted(required_columns - set(frame.columns))
    if missing:
        raise ValueError(f"SPY bar frame is missing columns: {', '.join(missing)}")

    schema = load_schema()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_rows = 0
    skipped_non_spy = 0
    skipped_invalid_ohlc = 0
    coverage_dates: set[str] = set()
    sample_validated = False

    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in frame.sort_index().itertuples():
            if str(row.symbol).strip() != "SPY":
                skipped_non_spy += 1
                continue
            record = {
                "record_type": "spy_bar",
                "schema_version": "m2.0",
                "symbol": "SPY",
                "timestamp_et": ts_to_et_iso(row.Index),
                "open": float(row.open),
                "high": float(row.high),
                "low": float(row.low),
                "close": float(row.close),
                "volume": int(row.volume),
                "provider": "Databento",
                "source": str(raw_path),
            }
            errors = validate_record(record, schema)
            if errors:
                skipped_invalid_ohlc += 1
                continue
            if not sample_validated:
                sample_validated = True
            coverage_dates.add(record["timestamp_et"][:10])
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
            output_rows += 1

    if output_rows == 0:
        raise ValueError("normalization produced zero valid SPY bar rows")

    return {
        "provider": "Databento",
        "raw_path": str(raw_path),
        "output_path": str(output_path),
        "input_rows": int(len(frame)),
        "output_rows": output_rows,
        "skipped_non_spy": skipped_non_spy,
        "skipped_invalid_ohlc": skipped_invalid_ohlc,
        "coverage_start": min(coverage_dates),
        "coverage_end": max(coverage_dates),
    }


def ts_to_et_iso(value: Any) -> str:
    timestamp = value.to_pydatetime() if hasattr(value, "to_pydatetime") else value
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=ZoneInfo("UTC"))
    return timestamp.astimezone(ET).isoformat()


def build_manifest(raw_path: Path, coverage_start: str, coverage_end: str) -> dict[str, Any]:
    raw_hash = sha256(raw_path)
    coverage_label = f"{coverage_start}-to-{coverage_end}"
    return {
        "record_type": "data_registry_manifest",
        "schema_version": "m2.0",
        "dataset_id": f"databento-spy-bars-{coverage_label}-{raw_hash[:12]}",
        "provider": "Databento",
        "source_url": str(raw_path),
        "ingested_at_et": datetime.now(ET).isoformat(timespec="seconds"),
        "coverage_start": coverage_start,
        "coverage_end": coverage_end,
        "raw_sha256": raw_hash,
        "schema_name": "m2_contracts",
        "schema_version_applied": "m2.0",
        "license_notes": "Databento EQUS.MINI ohlcv-1m local cache. Low-cost SPY-only research pull approved by user.",
    }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
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
    parser = argparse.ArgumentParser(description="Normalize local Databento SPY OHLCV bars to canonical spy_bar JSONL.")
    parser.add_argument("--raw-path", type=Path, default=RAW_PATH)
    parser.add_argument("--output-path", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--registry-path", type=Path, default=REGISTRY_PATH)
    parser.add_argument("--summary-path", type=Path, default=SUMMARY_PATH)
    args = parser.parse_args()

    result = normalize_raw_file(args.raw_path, args.output_path, args.registry_path)
    args.summary_path.parent.mkdir(parents=True, exist_ok=True)
    args.summary_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
