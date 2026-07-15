from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime, time
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.environment import data_root, interpreter_metadata
from lib.integrity import dbn_record_body_hashes, sha256_file
from lib.io import load_json, load_jsonl, write_json, write_jsonl
from scripts.validate_h_a2_fresh_oos_paid_download_decision import DEFAULT_PATH as DEFAULT_DECISION_PATH, validate


DEFAULT_COST_REPORT = PROJECT_ROOT / "reports" / "data_cost" / "h_a2_fresh_oos_2025_2026_live_cost_estimate.json"
DEFAULT_DOWNLOAD_REPORT = PROJECT_ROOT / "reports" / "data_cost" / "databento_download_result_h_a2_fresh_oos_2025_2026.json"
DEFAULT_DOWNLOAD_MD = PROJECT_ROOT / "reports" / "data_cost" / "databento_download_result_h_a2_fresh_oos_2025_2026.md"
DEFAULT_RAW_ROOT = data_root() / "raw" / "spy_0dte" / "databento" / "h_a2_fresh_oos_2025_2026"
DEFAULT_CHECKSUM_REGISTRY = data_root() / "registry" / "paid_artifact_checksums.jsonl"
ET = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")
PROVIDER_REDUCED_QUALITY_DATES = ("2025-08-13", "2025-08-19", "2025-08-25", "2025-09-12")


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
    return requests


def estimate_costs(
    requests: list[dict[str, Any]],
    cost_provider: Callable[[dict[str, Any]], float],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for request in requests:
        row = dict(request)
        try:
            row["estimated_cost_usd"] = float(cost_provider(request))
        except Exception as exc:
            row["estimated_cost_usd"] = None
            row["error"] = str(exc)
            errors.append({"window": request["window"], "error": str(exc)})
        rows.append(row)
    return rows, errors


def evaluate_cost_gate(decision: dict[str, Any], total_cost: float, errors: list[dict[str, str]]) -> dict[str, Any]:
    guard = decision["cost_guard"]
    blockers: list[str] = []
    if errors:
        blockers.append("metadata_cost_errors_present")
    if total_cost > float(guard["approved_purchase_ceiling_usd"]):
        blockers.append("estimated_cost_exceeds_approved_ceiling")
    if total_cost > float(guard["selected_key_authorization_limit_usd"]):
        blockers.append("estimated_cost_exceeds_selected_key_cap")
    return {"status": "pass" if not blockers else "blocked", "blockers": blockers}


def build_cost_report(decision: dict[str, Any], requests: list[dict[str, Any]], errors: list[dict[str, str]]) -> dict[str, Any]:
    total = round(sum(float(row["estimated_cost_usd"] or 0.0) for row in requests), 6)
    gate = evaluate_cost_gate(decision, total, errors)
    return {
        "schema_version": "h_a2_fresh_oos_live_cost_estimate_v1",
        "mode": "live_metadata_cost",
        "status": gate["status"],
        "hypothesis_id": "H-A2",
        "scenario": "h_a2_fresh_oos_2025_2026",
        "selected_key_env": decision["cost_guard"]["selected_key_env"],
        "account_provenance": decision["cost_guard"]["account_provenance"],
        "selected_key_authorization_limit_usd": decision["cost_guard"]["selected_key_authorization_limit_usd"],
        "approved_purchase_ceiling_usd": decision["cost_guard"]["approved_purchase_ceiling_usd"],
        "request_count": len(requests),
        "total_estimated_cost_usd": total,
        "requests": requests,
        "errors": errors,
        "decision": gate,
        "download_performed": False,
        "key_value_stored": False,
        "interpreter": interpreter_metadata(),
    }


def execute_downloads(
    requests: list[dict[str, Any]],
    downloader: Callable[[dict[str, Any]], dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for request in requests:
        try:
            rows.append(downloader(request))
        except Exception as exc:
            rows.append({**request, "source": "error", "error": str(exc)})
            errors.append({"window": request["window"], "error": str(exc)})
    return rows, errors


def register_checksums(downloads: list[dict[str, Any]], registry_path: Path = DEFAULT_CHECKSUM_REGISTRY) -> dict[str, Any]:
    existing = load_jsonl(registry_path) if registry_path.exists() else []
    by_path = {str(row["path"]): row for row in existing}
    added = 0
    for row in downloads:
        path = Path(row["raw_path"])
        relative = path.relative_to(data_root()).as_posix()
        canonical = dbn_record_body_hashes(path)
        candidate = {
            "record_type": "paid_artifact_checksum",
            "schema_version": "paid-artifact-checksum-v2",
            "provider": "Databento",
            "path": relative,
            "sha256": row["sha256"],
            "canonical_content_sha256": canonical["sha256"],
            "canonical_content_bytes": canonical["bytes"],
            "canonical_content_format": "dbn_record_body_after_metadata_v1",
            "source_report": "reports/data_cost/databento_download_result_h_a2_fresh_oos_2025_2026.json",
        }
        previous = by_path.get(relative)
        if previous and (
            previous.get("sha256") != candidate["sha256"]
            or previous.get("canonical_content_sha256") != candidate["canonical_content_sha256"]
        ):
            raise RuntimeError(f"checksum registry conflict: {relative}")
        if not previous:
            by_path[relative] = candidate
            added += 1
    write_jsonl(registry_path, [by_path[key] for key in sorted(by_path)])
    return {"status": "pass", "registry_path": str(registry_path), "added_count": added}


def build_download_report(
    decision: dict[str, Any],
    cost_report: dict[str, Any],
    downloads: list[dict[str, Any]],
    errors: list[dict[str, str]],
    registry: dict[str, Any] | None,
) -> dict[str, Any]:
    blockers = list(errors)
    if cost_report.get("status") != "pass":
        blockers.append({"error": "cost_gate_not_pass"})
    if len(downloads) != 40 or any(int(row.get("bytes", 0) or 0) <= 0 for row in downloads):
        blockers.append({"error": "download_file_count_or_size_invalid"})
    if registry is None or registry.get("status") != "pass":
        blockers.append({"error": "checksum_registry_not_pass"})
    downloaded_dates = {str(row.get("date")) for row in downloads}
    quality_warnings = [
        {
            "date": date_text,
            "warning": "Databento emitted a reduced-quality warning during the approved download.",
            "handling": "Retain the data, validate coverage during import, and report results with and without warned dates when candidate counts permit.",
        }
        for date_text in PROVIDER_REDUCED_QUALITY_DATES
        if date_text in downloaded_dates
    ]
    return {
        "schema_version": "h_a2_fresh_oos_download_result_v1",
        "mode": "download_complete" if not blockers else "download_incomplete",
        "status": "pass" if not blockers else "blocked",
        "hypothesis_id": "H-A2",
        "scenario": "h_a2_fresh_oos_2025_2026",
        "selected_key_env": decision["cost_guard"]["selected_key_env"],
        "account_provenance": decision["cost_guard"]["account_provenance"],
        "selected_key_authorization_limit_usd": decision["cost_guard"]["selected_key_authorization_limit_usd"],
        "total_estimated_cost_usd": cost_report["total_estimated_cost_usd"],
        "actual_provider_charge_usd": None,
        "actual_provider_charge_note": "Databento Historical API does not expose account usage/actual charge; the live metadata estimate is retained as the committed cost basis.",
        "request_count": len(downloads),
        "downloaded_count": sum(row.get("source") == "downloaded" for row in downloads),
        "cache_count": sum(row.get("source") == "cache" for row in downloads),
        "total_bytes": sum(int(row.get("bytes", 0) or 0) for row in downloads),
        "downloads": downloads,
        "checksum_registry": registry,
        "errors": errors,
        "blockers": blockers,
        "provider_quality_warnings": quality_warnings,
        "quality_warning_dates": [item["date"] for item in quality_warnings],
        "download_performed": True,
        "key_value_stored": False,
        "evidence_tier": "E0",
        "forbidden_claims": decision["forbidden_claims"],
        "interpreter": interpreter_metadata(),
    }


def render_download_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# H-A2 Fresh OOS 2025-2026 Download Result",
        "",
        f"- Status: `{report['status']}`",
        f"- Selected key: `{report['selected_key_env']}`",
        f"- Account provenance: `{report['account_provenance']}`",
        f"- Estimated committed cost: `${report['total_estimated_cost_usd']}`",
        f"- Requests: `{report['request_count']}`",
        f"- Downloaded: `{report['downloaded_count']}`; cache: `{report['cache_count']}`",
        f"- Total bytes: `{report['total_bytes']}`",
        f"- Checksum registry: `{(report.get('checksum_registry') or {}).get('status')}`",
        f"- Provider reduced-quality warning dates: `{report.get('quality_warning_dates', [])}`",
        "",
        "This is E0 data acquisition only. Candidate density and strategy evidence require a separate preregistered replay.",
    ]
    if report.get("provider_quality_warnings"):
        lines.extend(["", "## Provider Quality Warnings", ""])
        for item in report["provider_quality_warnings"]:
            lines.append(f"- `{item['date']}`: {item['warning']} {item['handling']}")
    if report["blockers"]:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- `{item}`" for item in report["blockers"])
    return "\n".join(lines) + "\n"


def _metadata_provider(api_key_env: str) -> Callable[[dict[str, Any]], float]:
    api_key = os.environ.get(api_key_env)
    if not api_key:
        raise RuntimeError(f"missing Databento API key environment variable: {api_key_env}")
    import databento as db  # type: ignore

    client = db.Historical(api_key)

    def provider(request: dict[str, Any]) -> float:
        return float(client.metadata.get_cost(**_provider_args(request)))

    return provider


def _downloader(api_key_env: str) -> Callable[[dict[str, Any]], dict[str, Any]]:
    api_key = os.environ.get(api_key_env)
    if not api_key:
        raise RuntimeError(f"missing Databento API key environment variable: {api_key_env}")
    import databento as db  # type: ignore

    client = db.Historical(api_key)

    def download(request: dict[str, Any]) -> dict[str, Any]:
        raw_path = Path(request["raw_path"])
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        source = "cache"
        if raw_path.exists() and raw_path.stat().st_size == 0:
            raw_path.unlink()
        if not raw_path.exists():
            temp_path = raw_path.with_name(f"{raw_path.name}.download")
            if temp_path.exists():
                temp_path.unlink()
            client.timeseries.get_range(path=temp_path, **_provider_args(request))
            temp_path.replace(raw_path)
            source = "downloaded"
        return {
            **request,
            "source": source,
            "bytes": raw_path.stat().st_size,
            "sha256": sha256_file(raw_path),
        }

    return download


def _provider_args(request: dict[str, Any]) -> dict[str, Any]:
    return {
        "dataset": request["dataset"],
        "symbols": request["symbols"],
        "schema": request["schema"],
        "stype_in": request["stype_in"],
        "start": request["start"],
        "end": request["end"],
    }


def _et_to_utc(trade_date: date, value: time) -> str:
    return datetime.combine(trade_date, value, tzinfo=ET).astimezone(UTC).isoformat()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Estimate or execute the approved H-A2 fresh OOS Databento download.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--estimate", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--decision", type=Path, default=DEFAULT_DECISION_PATH)
    parser.add_argument("--cost-report", type=Path, default=DEFAULT_COST_REPORT)
    parser.add_argument("--download-report", type=Path, default=DEFAULT_DOWNLOAD_REPORT)
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
        estimated, errors = estimate_costs(requests, _metadata_provider(args.api_key_env))
        report = build_cost_report(decision, estimated, errors)
        write_json(args.cost_report, report)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["status"] == "pass" else 1

    cost_report = load_json(args.cost_report)
    gate = evaluate_cost_gate(decision, float(cost_report.get("total_estimated_cost_usd", 999999)), cost_report.get("errors", []))
    if cost_report.get("status") != "pass" or gate["status"] != "pass" or cost_report.get("request_count") != 40:
        raise RuntimeError("committed live cost report does not pass the approved gate")
    downloads, errors = execute_downloads(requests, _downloader(args.api_key_env))
    registry = register_checksums(downloads) if not errors else None
    report = build_download_report(decision, cost_report, downloads, errors, registry)
    write_json(args.download_report, report)
    args.download_md.write_text(render_download_markdown(report), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
