from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_m2_contracts import load_schema, validate_record


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = PROJECT_ROOT / "experiments" / "h_a2_exact_2022_underlying_bar_plan.json"
OPTION_SUMMARY_PATH = PROJECT_ROOT / "reports" / "data_cost" / "databento_normalization_summary_h_a2_2022_10_stress.json"
DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "reports" / "data_cost" / "h_a2_2022_spy_bars_acquisition_manifest.json"
DEFAULT_COVERAGE_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_2022_spy_bars_coverage_audit.json"
DEFAULT_IMPORT_SUMMARY_PATH = PROJECT_ROOT / "reports" / "data_cost" / "h_a2_2022_spy_bars_import_summary.json"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_2022_spy_bars_coverage_audit.md"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "build" / "h_a2_2022_spy_bars_fixture" / "spy_bar.jsonl"
ET = ZoneInfo("America/New_York")
SESSION_START = time(9, 30)
SESSION_END = time(16, 0)
EXPECTED_FULL_DAY_MINUTES = 391


def run_acquisition_tool(
    *,
    mode: str,
    plan_path: Path = PLAN_PATH,
    option_summary_path: Path = OPTION_SUMMARY_PATH,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    coverage_path: Path = DEFAULT_COVERAGE_PATH,
    import_summary_path: Path = DEFAULT_IMPORT_SUMMARY_PATH,
    report_path: Path = DEFAULT_REPORT_PATH,
    output_path: Path = DEFAULT_OUTPUT_PATH,
) -> dict[str, Any]:
    if mode not in {"dry-run", "fixture"}:
        raise ValueError("mode must be dry-run or fixture")

    plan = _load_json(plan_path)
    option_summary = _load_json(option_summary_path)
    expected_dates = _date_range(plan["planned_scope"]["window_start"], plan["planned_scope"]["window_end"])
    quote_dates = _quote_available_dates(option_summary)

    rows: list[dict[str, Any]] = []
    if mode == "fixture":
        rows = _fixture_rows(expected_dates)
        _write_jsonl(output_path, rows)

    manifest = _build_manifest(mode, plan_path, option_summary_path, output_path, expected_dates, quote_dates)
    coverage = _build_coverage(mode, rows, expected_dates, quote_dates, output_path)
    import_summary = _build_import_summary(mode, manifest, coverage, output_path)

    _write_json(manifest_path, manifest)
    _write_json(coverage_path, coverage)
    _write_json(import_summary_path, import_summary)
    _write_report(report_path, manifest, coverage, import_summary)

    return {
        "manifest": manifest,
        "coverage": coverage,
        "import_summary": import_summary,
        "paths": {
            "manifest": _relative(manifest_path),
            "coverage": _relative(coverage_path),
            "import_summary": _relative(import_summary_path),
            "report": _relative(report_path),
            "output": _relative(output_path),
        },
    }


def _build_manifest(
    mode: str,
    plan_path: Path,
    option_summary_path: Path,
    output_path: Path,
    expected_dates: list[str],
    quote_dates: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": "h_a2_2022_spy_bars_acquisition_manifest_v1",
        "artifact_type": "bounded_data_tool_manifest",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "hypothesis_id": "H-A2",
        "evidence_tier": "E0",
        "tier_blockers": [
            "E0 tool/fixture artifact only",
            "No real SPY 2022-10 bars have been requested or imported",
            "Fixture bars cannot support strategy PnL, exact rerun, paper trading, or edge claims",
        ],
        "mode": mode,
        "status": "fixture_tool_pass" if mode == "fixture" else "dry_run_ready",
        "purpose": "Bound the SPY 2022-10 underlying-bar acquisition/import path before any live IBKR historical-bars request.",
        "source_plan": _relative(plan_path),
        "source_option_summary": _relative(option_summary_path),
        "symbol": "SPY",
        "bar_size": "1 minute",
        "timezone": "America/New_York",
        "session": "regular_trading_hours",
        "window_start": expected_dates[0],
        "window_end": expected_dates[-1],
        "expected_trading_day_count": len(expected_dates),
        "quote_available_day_count": len(quote_dates),
        "quote_available_dates": quote_dates,
        "canonical_output_path": _relative(output_path),
        "request_template": {
            "provider_candidate": "IBKR",
            "security_type": "STK",
            "exchange": "SMART",
            "currency": "USD",
            "what_to_show": "TRADES",
            "bar_size": "1 min",
            "use_rth": True,
            "orders_allowed": False,
            "transmit_allowed": False,
        },
        "license_notes_required_for_real_source": True,
        "real_source_license_notes": None,
        "guardrails": _guardrails(mode),
        "forbidden_actions_preserved": [
            "Do not request live IBKR historical bars from dry-run or fixture mode.",
            "Do not transmit orders.",
            "Do not buy data or introduce a new provider from this tool run.",
            "Do not rerun exact H-A2 stress diagnostics until real SPY bars pass coverage, timestamp, provenance, import, and option-join validation.",
            "Do not approve paper trading, operational validation, real-money trading, or an H-A2 edge claim from fixture data.",
        ],
    }


def _build_coverage(
    mode: str,
    rows: list[dict[str, Any]],
    expected_dates: list[str],
    quote_dates: list[str],
    output_path: Path,
) -> dict[str, Any]:
    by_date: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_date.setdefault(row["timestamp_et"][:10], []).append(row)

    day_checks = []
    for day in expected_dates:
        day_rows = sorted(by_date.get(day, []), key=lambda item: item["timestamp_et"])
        timestamps = [item["timestamp_et"][11:16] for item in day_rows]
        orb_required = ["09:30", "09:31", "09:32", "09:33", "09:34", "09:35"]
        day_checks.append(
            {
                "date": day,
                "row_count": len(day_rows),
                "first_timestamp_et": day_rows[0]["timestamp_et"] if day_rows else None,
                "last_timestamp_et": day_rows[-1]["timestamp_et"] if day_rows else None,
                "full_session_coverage": len(day_rows) >= EXPECTED_FULL_DAY_MINUTES
                and "09:30" in timestamps
                and "16:00" in timestamps,
                "orb_timestamp_coverage": all(value in timestamps for value in orb_required),
                "quote_available": day in quote_dates,
            }
        )

    actual_dates = sorted(by_date)
    missing_expected_dates = sorted(set(expected_dates) - set(actual_dates))
    option_join_missing_dates = sorted(set(quote_dates) - set(actual_dates))
    full_session_pass = mode == "fixture" and not missing_expected_dates and all(item["full_session_coverage"] for item in day_checks)
    orb_pass = mode == "fixture" and not missing_expected_dates and all(item["orb_timestamp_coverage"] for item in day_checks)
    option_join_pass = mode == "fixture" and not option_join_missing_dates
    canonical_pass = mode == "fixture" and len(rows) == len(expected_dates) * EXPECTED_FULL_DAY_MINUTES

    return {
        "schema_version": "h_a2_2022_spy_bars_coverage_audit_v1",
        "artifact_type": "coverage_audit",
        "hypothesis_id": "H-A2",
        "evidence_tier": "E0",
        "tier_blockers": [
            "E0 coverage gate test only",
            "Fixture or dry-run rows are not real market data",
            "Real source provenance, raw hash/request manifest, and license notes remain required before exact H-A2 rerun",
        ],
        "mode": mode,
        "status": "fixture_pass_real_data_not_imported" if mode == "fixture" else "dry_run_no_rows",
        "canonical_output_path": _relative(output_path),
        "expected_trading_day_count": len(expected_dates),
        "actual_trading_day_count": len(actual_dates),
        "expected_row_count_per_full_day": EXPECTED_FULL_DAY_MINUTES,
        "actual_row_count": len(rows),
        "missing_expected_dates": missing_expected_dates,
        "quote_available_dates": quote_dates,
        "option_join_missing_dates": option_join_missing_dates,
        "gates": {
            "canonical_import_pass": canonical_pass,
            "coverage_audit_pass": full_session_pass and orb_pass and option_join_pass,
            "timestamp_conversion_to_et_pass": mode == "fixture" and _timestamps_have_et_offset(rows),
            "orb_timestamp_coverage_pass": orb_pass,
            "full_session_coverage_pass": full_session_pass,
            "join_to_existing_2022_10_option_quotes_pass": option_join_pass,
            "no_lookahead_timestamp_rule_documented": True,
            "provenance_required_for_real_source": True,
            "raw_hash_or_request_manifest_required_for_real_source": True,
            "license_notes_required_for_real_source": True,
        },
        "ready_for_exact_rerun": False,
        "ready_for_exact_rerun_reason": "Fixture or dry-run output cannot approve exact H-A2 rerun; a real source import must pass the same gates first.",
        "guardrails": _guardrails(mode),
        "day_checks": day_checks,
    }


def _build_import_summary(
    mode: str,
    manifest: dict[str, Any],
    coverage: dict[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    return {
        "schema_version": "h_a2_2022_spy_bars_import_summary_v1",
        "artifact_type": "import_summary",
        "hypothesis_id": "H-A2",
        "evidence_tier": "E0",
        "tier_blockers": [
            "E0 import-shape validation only",
            "No real source data imported",
            "Exact H-A2 stress diagnostics remain blocked until real SPY bars pass the same gates",
        ],
        "mode": mode,
        "status": "fixture_import_pass" if mode == "fixture" else "dry_run_no_import",
        "provider": "synthetic_fixture" if mode == "fixture" else "none",
        "output_path": _relative(output_path),
        "output_rows": coverage["actual_row_count"],
        "coverage_status": coverage["status"],
        "manifest_status": manifest["status"],
        "ready_for_manual_data_probe": True,
        "ready_for_exact_rerun": False,
        "research_log_required": False,
        "paper_trading_allowed": False,
        "operational_validation_allowed": False,
        "real_money_allowed": False,
        "strategy_pnl_used": False,
        "guardrails": _guardrails(mode),
        "next_safe_action": (
            "Rerun the IBKR readiness probe. Execute a live historical-bars request only after readiness is ready_for_manual_data_probe; "
            "then import real bars through this bounded shape and rerun coverage validation."
        ),
    }


def _fixture_rows(expected_dates: list[str]) -> list[dict[str, Any]]:
    schema = load_schema()
    rows: list[dict[str, Any]] = []
    for day_index, day in enumerate(expected_dates):
        current = datetime.combine(date.fromisoformat(day), SESSION_START, tzinfo=ET)
        end = datetime.combine(date.fromisoformat(day), SESSION_END, tzinfo=ET)
        minute_index = 0
        while current <= end:
            base = 360.0 + day_index + minute_index * 0.01
            record = {
                "record_type": "spy_bar",
                "schema_version": "m2.0",
                "symbol": "SPY",
                "timestamp_et": current.isoformat(),
                "open": round(base, 4),
                "high": round(base + 0.08, 4),
                "low": round(base - 0.08, 4),
                "close": round(base + 0.02, 4),
                "volume": 100000 + minute_index,
                "provider": "synthetic_fixture",
                "source": "h_a2_2022_spy_bars_fixture",
            }
            errors = validate_record(record, schema)
            if errors:
                raise ValueError("; ".join(errors))
            rows.append(record)
            current += timedelta(minutes=1)
            minute_index += 1
    return rows


def _quote_available_dates(option_summary: dict[str, Any]) -> list[str]:
    return [
        item["trade_date"]
        for item in option_summary.get("files", [])
        if int(item.get("output_rows", 0)) > 0
    ]


def _date_range(start: str, end: str) -> list[str]:
    current = date.fromisoformat(start)
    end_date = date.fromisoformat(end)
    days: list[str] = []
    while current <= end_date:
        if current.weekday() < 5:
            days.append(current.isoformat())
        current += timedelta(days=1)
    return days


def _timestamps_have_et_offset(rows: list[dict[str, Any]]) -> bool:
    if not rows:
        return False
    return all(item["timestamp_et"].endswith("-04:00") or item["timestamp_et"].endswith("-05:00") for item in rows)


def _guardrails(mode: str) -> dict[str, bool]:
    return {
        "external_network_used": False,
        "paid_data_used": False,
        "new_provider_used": False,
        "ibkr_historical_request_used": False,
        "orders_transmitted": False,
        "broker_execution_enabled": False,
        "llm_call_used": False,
        "strategy_pnl_used": False,
        "real_source_data_imported": False,
        "fixture_data_imported": mode == "fixture",
    }


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _write_report(path: Path, manifest: dict[str, Any], coverage: dict[str, Any], import_summary: dict[str, Any]) -> None:
    lines = [
        "# H-A2 2022 SPY Bars Acquisition/Import Tool",
        "",
        f"- **Mode**: `{manifest['mode']}`",
        f"- **Manifest status**: `{manifest['status']}`",
        f"- **Coverage status**: `{coverage['status']}`",
        f"- **Import status**: `{import_summary['status']}`",
        f"- **Rows**: `{coverage['actual_row_count']}`",
        f"- **Expected trading days**: `{coverage['expected_trading_day_count']}`",
        f"- **Actual trading days**: `{coverage['actual_trading_day_count']}`",
        f"- **Ready for exact H-A2 rerun**: `{coverage['ready_for_exact_rerun']}`",
        f"- **Network used**: `{manifest['guardrails']['external_network_used']}`",
        f"- **Paid data used**: `{manifest['guardrails']['paid_data_used']}`",
        f"- **IBKR historical request used**: `{manifest['guardrails']['ibkr_historical_request_used']}`",
        f"- **Orders transmitted**: `{manifest['guardrails']['orders_transmitted']}`",
        "",
        "## Gates",
        "",
        "| Gate | Pass |",
        "|:--|:--:|",
    ]
    for name, value in coverage["gates"].items():
        lines.append(f"| `{name}` | `{value}` |")
    lines.extend(
        [
            "",
            "## Next Safe Action",
            "",
            import_summary["next_safe_action"],
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bound H-A2 2022-10 SPY bar acquisition/import before any live source execution.")
    parser.add_argument("--mode", choices=["dry-run", "fixture"], default="dry-run")
    parser.add_argument("--plan-path", type=Path, default=PLAN_PATH)
    parser.add_argument("--option-summary-path", type=Path, default=OPTION_SUMMARY_PATH)
    parser.add_argument("--manifest-path", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--coverage-path", type=Path, default=DEFAULT_COVERAGE_PATH)
    parser.add_argument("--import-summary-path", type=Path, default=DEFAULT_IMPORT_SUMMARY_PATH)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--output-path", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args(argv)

    result = run_acquisition_tool(
        mode=args.mode,
        plan_path=args.plan_path,
        option_summary_path=args.option_summary_path,
        manifest_path=args.manifest_path,
        coverage_path=args.coverage_path,
        import_summary_path=args.import_summary_path,
        report_path=args.report_path,
        output_path=args.output_path,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
