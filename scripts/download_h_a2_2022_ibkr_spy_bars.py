from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.environment import data_root, interpreter_metadata
from lib.io import load_json, write_json, write_jsonl
from lib.integrity import sha256_file


ET = ZoneInfo("America/New_York")
COST_PLAN = PROJECT_ROOT / "reports" / "data_cost" / "h_a2_2022_h2_stress_decision_tree_cost_plan.json"
RESULT_PATH = PROJECT_ROOT / "reports" / "data_cost" / "h_a2_2022_ibkr_spy_bars_download_result.json"


def download(*, host: str, port: int, client_id: int) -> dict[str, Any]:
    from ib_insync import IB, Stock  # type: ignore

    plan = load_json(COST_PLAN)
    dates = list(plan["october_stress_dates"])
    root = data_root()
    raw_path = root / "raw" / "spy_0dte" / "ibkr" / "h_a2_2022_10_stress" / "spy_1m_raw.jsonl"
    canonical_path = root / "normalized" / "spy_0dte" / "ibkr" / "h_a2_2022_10_stress" / "spy_bar.jsonl"
    raw_rows: list[dict[str, Any]] = []
    canonical_rows: list[dict[str, Any]] = []
    day_results: list[dict[str, Any]] = []
    ib = IB()
    try:
        ib.connect(host, port, clientId=client_id, readonly=True, timeout=15)
        contract = Stock("SPY", "SMART", "USD", primaryExchange="ARCA")
        qualified = ib.qualifyContracts(contract)
        if not qualified:
            raise RuntimeError("IBKR could not qualify SPY")
        for trade_date in dates:
            bars = ib.reqHistoricalData(
                contract,
                endDateTime=f"{trade_date.replace('-', '')} 16:00:00 US/Eastern",
                durationStr="1 D",
                barSizeSetting="1 min",
                whatToShow="TRADES",
                useRTH=True,
                formatDate=2,
                keepUpToDate=False,
                timeout=60,
            )
            day_raw, day_canonical = normalize_bars(trade_date, bars)
            raw_rows.extend(day_raw)
            canonical_rows.extend(day_canonical)
            times = [row["timestamp_et"][11:16] for row in day_canonical]
            day_results.append(
                {
                    "date": trade_date,
                    "row_count": len(day_canonical),
                    "first_timestamp_et": day_canonical[0]["timestamp_et"] if day_canonical else None,
                    "last_timestamp_et": day_canonical[-1]["timestamp_et"] if day_canonical else None,
                    "has_0935": "09:35" in times,
                    "has_1545": "15:45" in times,
                    "coverage_pass": len(day_canonical) == 390 and "09:35" in times and "15:45" in times,
                }
            )
    finally:
        if ib.isConnected():
            ib.disconnect()

    write_jsonl(raw_path, raw_rows)
    write_jsonl(canonical_path, sorted(canonical_rows, key=lambda row: row["timestamp_utc"]))
    raw_sha256 = sha256_file(raw_path)
    canonical_sha256 = sha256_file(canonical_path)
    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    result = {
        "schema_version": "h_a2_2022_ibkr_spy_bars_download_v1",
        "status": "pass" if len(day_results) == 13 and all(row["coverage_pass"] for row in day_results) else "blocked",
        "generated_at_utc": generated,
        "hypothesis_id": "H-A2",
        "provider": "Interactive Brokers",
        "symbol": "SPY",
        "port": port,
        "readonly": True,
        "orders_transmitted": False,
        "historical_request_count": len(day_results),
        "target_date_count": 13,
        "total_row_count": len(canonical_rows),
        "raw_path": _project_or_data_path(raw_path, root),
        "canonical_path": _project_or_data_path(canonical_path, root),
        "sha256": raw_sha256,
        "canonical_content_sha256": canonical_sha256,
        "canonical_content_format": "sorted_canonical_jsonl_v1",
        "projected_subscription_cost_usd": 1.5,
        "actual_per_request_charge_usd": 0.0,
        "actual_subscription_charge_observable_via_api": False,
        "day_results": day_results,
        "interpreter": interpreter_metadata(),
    }
    write_json(RESULT_PATH, result)
    _append_registries(root, raw_path, canonical_path, result)
    return result


def normalize_bars(trade_date: str, bars: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    raw_rows: list[dict[str, Any]] = []
    canonical_rows: list[dict[str, Any]] = []
    for bar in bars:
        ts_utc = bar.date.astimezone(timezone.utc)
        ts_et = ts_utc.astimezone(ET)
        if ts_et.date().isoformat() != trade_date:
            continue
        raw_rows.append(
            {
                "date": trade_date,
                "timestamp_utc": ts_utc.isoformat(),
                "open": float(bar.open),
                "high": float(bar.high),
                "low": float(bar.low),
                "close": float(bar.close),
                "volume": int(bar.volume),
                "average": float(bar.average),
                "bar_count": int(bar.barCount),
            }
        )
        canonical_rows.append(
            {
                "record_type": "spy_bar",
                "schema_version": "m2.0",
                "symbol": "SPY",
                "timestamp_utc": ts_utc.isoformat(),
                "timestamp_et": ts_et.isoformat(),
                "open": float(bar.open),
                "high": float(bar.high),
                "low": float(bar.low),
                "close": float(bar.close),
                "volume": int(bar.volume),
                "provider": "Interactive Brokers",
                "source": "IBKR historical TRADES 1 min RTH",
            }
        )
    return raw_rows, canonical_rows


def _append_registries(root: Path, raw_path: Path, canonical_path: Path, result: dict[str, Any]) -> None:
    registry = root / "registry" / "datasets.jsonl"
    checksum_registry = root / "registry" / "paid_artifact_checksums.jsonl"
    dataset_id = f"ibkr-spy-bars-2022-10-stress-{result['sha256'][:12]}"
    dataset_row = {
        "record_type": "data_registry_manifest",
        "schema_name": "m2_contracts",
        "schema_version": "m2.0",
        "schema_version_applied": "m2.0",
        "dataset_id": dataset_id,
        "provider": "Interactive Brokers",
        "coverage_start": "2022-10-03",
        "coverage_end": "2022-10-31",
        "ingested_at_et": datetime.now(ET).replace(microsecond=0).isoformat(),
        "source_url": _project_or_data_path(raw_path, root),
        "raw_sha256": result["sha256"],
        "canonical_content_sha256": result["canonical_content_sha256"],
        "canonical_path": _project_or_data_path(canonical_path, root),
        "license_notes": "IBKR account historical market-data entitlement; SPY-only research use.",
    }
    checksum_row = {
        "record_type": "paid_artifact_checksum",
        "schema_version": "paid-artifact-checksum-v3",
        "provider": "Interactive Brokers",
        "path": raw_path.relative_to(root).as_posix(),
        "sha256": result["sha256"],
        "canonical_path": canonical_path.relative_to(root).as_posix(),
        "canonical_content_sha256": result["canonical_content_sha256"],
        "canonical_content_format": "sorted_canonical_jsonl_v1",
        "source_report": RESULT_PATH.relative_to(PROJECT_ROOT).as_posix(),
    }
    _append_unique(registry, dataset_row, "dataset_id")
    _append_unique(checksum_registry, checksum_row, "sha256")


def _append_unique(path: Path, row: dict[str, Any], key: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8-sig").splitlines() if path.exists() else []
    if any(json.loads(line).get(key) == row[key] for line in existing if line.strip()):
        return
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def _project_or_data_path(path: Path, root: Path) -> str:
    try:
        return "data/" + path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Download the approved 13-date H-A2 SPY bar block from IBKR.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7496)
    parser.add_argument("--client-id", type=int, default=72)
    args = parser.parse_args()
    result = download(host=args.host, port=args.port, client_id=args.client_id)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
