from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, time
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.databento import (
    append_paid_artifact_checksums,
    download_requests,
    estimate_requests,
    file_download_provider,
    metadata_cost_provider,
)
from lib.environment import data_root, interpreter_metadata
from lib.io import load_json, write_json
from lib.report import render_markdown_report
from scripts.validate_h_a2_orb_0936_paid_download_decision import DEFAULT_PATH as DEFAULT_DECISION, validate


DEFAULT_COST_JSON = PROJECT_ROOT / "reports" / "data_cost" / "h_a2_orb_0936_live_cost_estimate.json"
DEFAULT_COST_MD = PROJECT_ROOT / "reports" / "data_cost" / "h_a2_orb_0936_live_cost_estimate.md"
DEFAULT_DOWNLOAD_JSON = PROJECT_ROOT / "reports" / "data_cost" / "databento_download_result_h_a2_orb_0936.json"
DEFAULT_DOWNLOAD_MD = PROJECT_ROOT / "reports" / "data_cost" / "databento_download_result_h_a2_orb_0936.md"
DEFAULT_RAW_ROOT = data_root() / "raw" / "spy_0dte" / "databento" / "h_a2_orb_0936_fresh_oos"
DEFAULT_CHECKSUM_REGISTRY = data_root() / "registry" / "paid_artifact_checksums.jsonl"
SOURCE_REPORT = "reports/data_cost/databento_download_result_h_a2_orb_0936.json"
ET = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")


def build_requests(decision: dict[str, Any], raw_root: Path = DEFAULT_RAW_ROOT) -> list[dict[str, Any]]:
    requests: list[dict[str, Any]] = []
    for date_text in decision["approved_scope"]["dates"]:
        trade_date = date.fromisoformat(date_text)
        requests.extend(
            [
                {
                    "date": date_text,
                    "dataset": "OPRA.PILLAR",
                    "symbols": ["SPY.OPT"],
                    "schema": "cbbo-1m",
                    "stype_in": "parent",
                    "start": _et_to_utc(trade_date, time(9, 30)),
                    "end": _et_to_utc(trade_date, time(15, 50)),
                    "window": f"{date_text}_opra_grouped_0930_1550",
                    "raw_path": str(raw_root / f"{date_text}_opra_grouped_0930_1550.dbn.zst"),
                },
                {
                    "date": date_text,
                    "dataset": "EQUS.MINI",
                    "symbols": ["SPY"],
                    "schema": "ohlcv-1m",
                    "stype_in": "raw_symbol",
                    "start": _et_to_utc(trade_date, time(9, 30)),
                    "end": _et_to_utc(trade_date, time(16, 0)),
                    "window": f"{date_text}_spy_underlying_full_session",
                    "raw_path": str(raw_root / f"{date_text}_spy_underlying_full_session.dbn.zst"),
                },
            ]
        )
    requests.append(
        {
            "date": "2026-03-01/2026-06-04",
            "dataset": "EQUS.MINI",
            "symbols": ["SPY"],
            "schema": "ohlcv-1d",
            "stype_in": "raw_symbol",
            "start": "2026-03-01",
            "end": "2026-06-05",
            "window": "2026-03-01_2026-06-04_spy_daily_history",
            "raw_path": str(raw_root / "2026-03-01_2026-06-04_spy_daily_history.dbn.zst"),
        }
    )
    return requests


def evaluate_cost_gate(
    decision: dict[str, Any],
    total_cost: float,
    request_count: int,
    errors: list[dict[str, str]],
) -> dict[str, Any]:
    guard = decision["cost_guard"]
    blockers: list[str] = []
    projected_usage = float(guard["known_committed_selected_key_usage_usd"]) + total_cost
    if errors:
        blockers.append("metadata_cost_errors_present")
    if request_count != int(decision["approved_scope"]["request_count"]):
        blockers.append("request_count_mismatch")
    if total_cost > float(guard["approved_purchase_ceiling_usd"]):
        blockers.append("estimated_cost_exceeds_approved_ceiling")
    if projected_usage > float(guard["selected_key_authorization_limit_usd"]):
        blockers.append("projected_cumulative_usage_exceeds_selected_key_cap")
    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "projected_selected_key_usage_usd": round(projected_usage, 6),
    }


def build_cost_report(
    decision: dict[str, Any],
    requests: list[dict[str, Any]],
    errors: list[dict[str, str]],
) -> dict[str, Any]:
    total = round(sum(float(row.get("estimated_cost_usd") or 0.0) for row in requests), 6)
    gate = evaluate_cost_gate(decision, total, len(requests), errors)
    return {
        "schema_version": "h_a2_orb_0936_live_cost_estimate_v1",
        "mode": "live_metadata_cost",
        "status": gate["status"],
        "hypothesis_id": "H-A2",
        "scenario": "h_a2_orb_0936_fresh_oos",
        "source_decision": "experiments/h_a2_orb_0936_paid_download_decision.json",
        "selected_key_env": decision["cost_guard"]["selected_key_env"],
        "account_provenance": decision["cost_guard"]["account_provenance"],
        "approved_purchase_ceiling_usd": decision["cost_guard"]["approved_purchase_ceiling_usd"],
        "request_count": len(requests),
        "total_estimated_cost_usd": total,
        "projected_selected_key_usage_usd": gate["projected_selected_key_usage_usd"],
        "requests": requests,
        "errors": errors,
        "decision": gate,
        "download_performed": False,
        "target_outcomes_parsed": False,
        "key_value_stored": False,
        "interpreter": interpreter_metadata(),
    }


def build_download_report(
    decision: dict[str, Any],
    cost_report: dict[str, Any],
    downloads: list[dict[str, Any]],
    errors: list[dict[str, str]],
    registry: dict[str, Any] | None,
) -> dict[str, Any]:
    blockers: list[Any] = list(errors)
    if cost_report.get("status") != "pass":
        blockers.append({"error": "cost_gate_not_pass"})
    if len(downloads) != 41 or any(int(row.get("bytes", 0) or 0) <= 0 for row in downloads):
        blockers.append({"error": "download_file_count_or_size_invalid"})
    if registry is None or registry.get("status") != "pass":
        blockers.append({"error": "checksum_registry_not_pass"})
    return {
        "schema_version": "h_a2_orb_0936_download_result_v1",
        "mode": "download_complete" if not blockers else "download_incomplete",
        "status": "pass" if not blockers else "blocked",
        "hypothesis_id": "H-A2",
        "scenario": "h_a2_orb_0936_fresh_oos",
        "source_cost_report": "reports/data_cost/h_a2_orb_0936_live_cost_estimate.json",
        "selected_key_env": decision["cost_guard"]["selected_key_env"],
        "account_provenance": decision["cost_guard"]["account_provenance"],
        "selected_key_authorization_limit_usd": decision["cost_guard"]["selected_key_authorization_limit_usd"],
        "total_estimated_cost_usd": cost_report["total_estimated_cost_usd"],
        "actual_provider_charge_usd": None,
        "actual_provider_charge_note": "Databento Historical API does not expose account usage or the final charge; the live metadata estimate is the committed cost basis.",
        "request_count": len(downloads),
        "downloaded_count": sum(row.get("source") == "downloaded" for row in downloads),
        "cache_count": sum(row.get("source") == "cache" for row in downloads),
        "total_bytes": sum(int(row.get("bytes", 0) or 0) for row in downloads),
        "downloads": downloads,
        "checksum_registry": registry,
        "errors": errors,
        "blockers": blockers,
        "download_performed": True,
        "target_outcomes_parsed": False,
        "experiment_run": False,
        "evidence_tier": "E0",
        "forbidden_claims": decision["forbidden_claims"],
        "key_value_stored": False,
        "interpreter": interpreter_metadata(),
    }


def write_cost_report(report: dict[str, Any], json_path: Path, markdown_path: Path) -> None:
    write_json(json_path, report)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(
        render_markdown_report(
            "H-A2 ORB 09:36 Live Cost Gate",
            [
                ("ผลการตรวจ", f"- สถานะ: `{report['status']}`\n- Requests: `{report['request_count']}`\n- ราคาประเมิน: `${report['total_estimated_cost_usd']}`\n- การใช้ key หลังซื้อ: `${report['projected_selected_key_usage_usd']}`"),
                ("ข้อจำกัด", "เป็น metadata cost gate เท่านั้น ยังไม่อ่าน PnL และไม่ใช่หลักฐาน edge"),
            ],
        ),
        encoding="utf-8",
    )


def write_download_report(report: dict[str, Any], json_path: Path, markdown_path: Path) -> None:
    write_json(json_path, report)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(
        render_markdown_report(
            "H-A2 ORB 09:36 Download Result",
            [
                ("ผลการดาวน์โหลด", f"- สถานะ: `{report['status']}`\n- Requests: `{report['request_count']}`\n- ดาวน์โหลดใหม่: `{report['downloaded_count']}`\n- จาก cache: `{report['cache_count']}`\n- ขนาดรวม: `{report['total_bytes']}` bytes\n- ต้นทุนอ้างอิง: `${report['total_estimated_cost_usd']}`"),
                ("Integrity", f"Checksum registry: `{(report.get('checksum_registry') or {}).get('status')}`"),
                ("ข้อจำกัด", "นี่เป็น E0 data acquisition เท่านั้น ยังไม่ parse PnL ไม่รันการทดลอง และไม่อนุมัติ paper trading หรือ E2"),
            ],
        ),
        encoding="utf-8",
    )


def _et_to_utc(trade_date: date, value: time) -> str:
    return datetime.combine(trade_date, value, tzinfo=ET).astimezone(UTC).isoformat()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cost and download the approved H-A2 ORB 09:36 cohort.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--estimate", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--decision", type=Path, default=DEFAULT_DECISION)
    parser.add_argument("--cost-json", type=Path, default=DEFAULT_COST_JSON)
    parser.add_argument("--cost-md", type=Path, default=DEFAULT_COST_MD)
    parser.add_argument("--download-json", type=Path, default=DEFAULT_DOWNLOAD_JSON)
    parser.add_argument("--download-md", type=Path, default=DEFAULT_DOWNLOAD_MD)
    parser.add_argument("--api-key-env", default="DATABENTO_API_01")
    args = parser.parse_args(argv)

    validation = validate(args.decision)
    if validation["status"] != "pass":
        print(json.dumps(validation, indent=2))
        return 1
    decision = load_json(args.decision)
    if args.api_key_env != decision["cost_guard"]["selected_key_env"]:
        raise RuntimeError("api-key-env does not match the approved decision")
    requests = build_requests(decision)

    if args.estimate:
        estimated, errors = estimate_requests(requests, metadata_cost_provider(args.api_key_env))
        report = build_cost_report(decision, estimated, errors)
        write_cost_report(report, args.cost_json, args.cost_md)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["status"] == "pass" else 1

    cost_report = load_json(args.cost_json)
    gate = evaluate_cost_gate(
        decision,
        float(cost_report.get("total_estimated_cost_usd", 999999)),
        int(cost_report.get("request_count", 0)),
        cost_report.get("errors", []),
    )
    if cost_report.get("status") != "pass" or gate["status"] != "pass":
        raise RuntimeError("committed live cost report does not pass the approved gate")
    downloads, errors = download_requests(requests, file_download_provider(args.api_key_env))
    registry = (
        append_paid_artifact_checksums(
            downloads,
            data_root=data_root(),
            registry_path=DEFAULT_CHECKSUM_REGISTRY,
            source_report=SOURCE_REPORT,
        )
        if not errors
        else None
    )
    report = build_download_report(decision, cost_report, downloads, errors, registry)
    write_download_report(report, args.download_json, args.download_md)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
