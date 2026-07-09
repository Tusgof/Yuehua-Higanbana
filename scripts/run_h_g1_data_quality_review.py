from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "experiments" / "h_g1_gamma_regime_date_set_preregistration.json"
DEFAULT_BASELINE_SUMMARY_PATH = PROJECT_ROOT / "reports" / "baselines" / "subsystem_a_orb_baseline_summary.json"
DEFAULT_ENRICHMENT_SUMMARY_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_gamma_regime_enrichment_summary.json"
DEFAULT_DIAGNOSTIC_SUMMARY_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_gamma_regime_diagnostic_summary.json"
DEFAULT_JSON_OUTPUT = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_data_quality_review.json"
DEFAULT_REPORT_OUTPUT = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_data_quality_review.md"


def run_review(
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    baseline_summary_path: Path = DEFAULT_BASELINE_SUMMARY_PATH,
    enrichment_summary_path: Path = DEFAULT_ENRICHMENT_SUMMARY_PATH,
    diagnostic_summary_path: Path = DEFAULT_DIAGNOSTIC_SUMMARY_PATH,
) -> dict[str, Any]:
    manifest = _load_json(manifest_path)
    baseline = _load_json(baseline_summary_path)
    enrichment = _load_json(enrichment_summary_path)
    diagnostic = _load_json(diagnostic_summary_path)

    manifest_by_date = {item["date"]: item for item in manifest["selected_dates"]}
    enrichment_by_date = {item["date"]: item for item in enrichment["date_summaries"]}
    diagnostic_by_date = diagnostic["per_date"]

    dates: list[dict[str, Any]] = []
    for date, entry in sorted(manifest_by_date.items()):
        enriched = enrichment_by_date.get(date, {})
        diag = diagnostic_by_date.get(date, {})
        baseline_bar_rows = _count_baseline_rows_for_date(baseline, date, "bar_path")
        baseline_quote_rows = _count_baseline_rows_for_date(baseline, date, "quote_path")
        manifest_spy_bar_status = entry.get("local_spy_bar_cache_status")
        underlying_join_count = int(enriched.get("underlying_join_count") or 0)
        quote_snapshot_rows = int(enriched.get("quote_snapshot_rows") or 0)
        computed_greeks_count = int(enriched.get("computed_greeks_count") or 0)
        date_review = {
            "date": date,
            "split": entry.get("split"),
            "volatility_bucket": entry.get("volatility_bucket"),
            "high_importance_macro": entry.get("high_importance_macro"),
            "manifest_spy_bar_cache_status": manifest_spy_bar_status,
            "baseline_bar_rows_for_date": baseline_bar_rows,
            "baseline_quote_rows_for_date": baseline_quote_rows,
            "enrichment_bar_rows": int(enriched.get("bar_rows") or 0),
            "quote_snapshot_rows": quote_snapshot_rows,
            "underlying_join_count": underlying_join_count,
            "open_interest_join_count": int(enriched.get("open_interest_join_count") or 0),
            "computed_greeks_count": computed_greeks_count,
            "computed_greeks_rate": round(_safe_rate(computed_greeks_count, quote_snapshot_rows), 6),
            "required_bucket_blockers": list(diag.get("required_bucket_blockers", [])),
            "issue_class": _issue_class(manifest_spy_bar_status, baseline_bar_rows, underlying_join_count, diag),
        }
        dates.append(date_review)

    missing_underlying_dates = [item for item in dates if item["underlying_join_count"] == 0]
    manifest_mismatches = [
        item for item in dates
        if item["manifest_spy_bar_cache_status"] == "present" and item["baseline_bar_rows_for_date"] == 0
    ]
    bucket_failures_after_underlying = [
        item for item in dates
        if item["underlying_join_count"] > 0 and item["required_bucket_blockers"]
    ]
    original_quote_count = sum(item["quote_snapshot_rows"] for item in dates)
    original_computed_count = sum(item["computed_greeks_count"] for item in dates)
    original_underlying_count = sum(item["underlying_join_count"] for item in dates)
    repaired_candidate_dates = [item for item in dates if item["underlying_join_count"] > 0]
    repaired_quote_count = sum(item["quote_snapshot_rows"] for item in repaired_candidate_dates)
    repaired_computed_count = sum(item["computed_greeks_count"] for item in repaired_candidate_dates)
    repaired_underlying_count = sum(item["underlying_join_count"] for item in repaired_candidate_dates)

    result = {
        "record_type": "h_g1_data_quality_review",
        "schema_version": "h_g1_data_quality_review_v1",
        "hypothesis_id": "H-G1",
        "status": "complete_no_purchase_review",
        "paid_cost_usd": 0.0,
        "network_calls": 0,
        "manifest_path": str(manifest_path),
        "baseline_summary_path": str(baseline_summary_path),
        "enrichment_summary_path": str(enrichment_summary_path),
        "diagnostic_summary_path": str(diagnostic_summary_path),
        "summary": {
            "date_count": len(dates),
            "missing_underlying_date_count": len(missing_underlying_dates),
            "manifest_spy_bar_mismatch_count": len(manifest_mismatches),
            "bucket_failure_after_underlying_date_count": len(bucket_failures_after_underlying),
            "original_raw_row_coverage": {
                "quote_count": original_quote_count,
                "underlying_join_rate": round(_safe_rate(original_underlying_count, original_quote_count), 6),
                "computed_greeks_rate": round(_safe_rate(original_computed_count, original_quote_count), 6),
            },
            "excluding_missing_underlying_dates": {
                "date_count": len(repaired_candidate_dates),
                "quote_count": repaired_quote_count,
                "underlying_join_rate": round(_safe_rate(repaired_underlying_count, repaired_quote_count), 6),
                "computed_greeks_rate": round(_safe_rate(repaired_computed_count, repaired_quote_count), 6),
            },
        },
        "manifest_mismatches": manifest_mismatches,
        "missing_underlying_dates": missing_underlying_dates,
        "bucket_failures_after_underlying": bucket_failures_after_underlying,
        "date_reviews": dates,
        "decision": {
            "conclusion": "ยังสรุปไม่ได้",
            "reason": "H-G1 ยังเป็น data-quality blocker ไม่ใช่ strategy blocker; สองวัน March 2023 ไม่มี SPY bars จริงใน cache แม้ manifest ระบุ present และยังมี bucket-level IV/Greeks coverage failures หลังตัดวันดังกล่าวออก",
            "next_safe_action": "ทำ H-G1 manifest v2 หรือ repair cache เฉพาะ 2023-03-13 และ 2023-03-22 ก่อน rerun; จากนั้นตรวจ bucket failures ที่เหลือโดยไม่ใช้ signed-OI gamma proxy เป็น trading filter จนกว่า policy gate จะผ่าน",
            "forbidden_claims": [
                "do_not_claim_gamma_proxy_validity",
                "do_not_use_novi_or_net_gamma_strategy_filter",
                "do_not_buy_more_opra_oi_until_underlying_cache_issue_is_resolved",
            ],
        },
    }
    return result


def write_outputs(result: dict[str, Any], json_output: Path = DEFAULT_JSON_OUTPUT, report_output: Path = DEFAULT_REPORT_OUTPUT) -> None:
    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_output.write_text(_render_markdown(result), encoding="utf-8")


def _issue_class(
    manifest_spy_bar_status: str | None,
    baseline_bar_rows: int,
    underlying_join_count: int,
    diagnostic_item: dict[str, Any],
) -> str:
    if underlying_join_count == 0:
        if manifest_spy_bar_status == "present" and baseline_bar_rows == 0:
            return "manifest_cache_mismatch_missing_spy_bars"
        return "missing_underlying_join"
    if diagnostic_item.get("required_bucket_blockers"):
        return "bucket_computed_greeks_coverage_failure"
    return "passes_current_data_quality_review"


def _count_baseline_rows_for_date(baseline: dict[str, Any], date: str, path_field: str) -> int:
    total = 0
    for dataset in baseline.get("datasets", []):
        start = str(dataset.get("coverage_start", ""))
        end = str(dataset.get("coverage_end", ""))
        if start and end and not (start <= date <= end):
            continue
        path_value = dataset.get(path_field)
        if not path_value:
            continue
        path = Path(path_value)
        if not path.exists():
            continue
        total += _count_jsonl_date_rows(path, date)
    return total


def _count_jsonl_date_rows(path: Path, date: str) -> int:
    count = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if f'"{date}T' in line:
                count += 1
    return count


def _safe_rate(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def _render_markdown(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# H-G1 Data Quality Review",
        "",
        f"- Status: `{result['status']}`",
        f"- Paid cost: `${result['paid_cost_usd']}`",
        f"- Network calls: `{result['network_calls']}`",
        f"- Conclusion: {result['decision']['conclusion']}",
        "",
        "## Summary",
        "",
        f"- Dates reviewed: {summary['date_count']}",
        f"- Missing underlying dates: {summary['missing_underlying_date_count']}",
        f"- Manifest/cache mismatches: {summary['manifest_spy_bar_mismatch_count']}",
        f"- Bucket failures after underlying join exists: {summary['bucket_failure_after_underlying_date_count']}",
        f"- Original computed Greeks rate: `{summary['original_raw_row_coverage']['computed_greeks_rate']}`",
        f"- Computed Greeks rate excluding missing-underlying dates: `{summary['excluding_missing_underlying_dates']['computed_greeks_rate']}`",
        "",
        "## Missing Underlying Dates",
        "",
        "| Date | Manifest bar status | Baseline bar rows | Quote snapshot rows | Issue |",
        "|:--|:--|--:|--:|:--|",
    ]
    for item in result["missing_underlying_dates"]:
        lines.append(
            f"| {item['date']} | `{item['manifest_spy_bar_cache_status']}` | {item['baseline_bar_rows_for_date']} | "
            f"{item['quote_snapshot_rows']} | `{item['issue_class']}` |"
        )
    lines.extend(["", "## Remaining Bucket Failures", "", "| Date | Bucket blockers | Computed rate |", "|:--|:--|--:|"])
    for item in result["bucket_failures_after_underlying"]:
        blockers = ", ".join(f"`{blocker}`" for blocker in item["required_bucket_blockers"])
        lines.append(f"| {item['date']} | {blockers} | {item['computed_greeks_rate']} |")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            result["decision"]["reason"],
            "",
            "## Next Safe Action",
            "",
            result["decision"]["next_safe_action"],
            "",
        ]
    )
    return "\n".join(lines)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Review H-G1 data-quality blockers without paid data or network calls.")
    parser.add_argument("--manifest-path", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--baseline-summary-path", type=Path, default=DEFAULT_BASELINE_SUMMARY_PATH)
    parser.add_argument("--enrichment-summary-path", type=Path, default=DEFAULT_ENRICHMENT_SUMMARY_PATH)
    parser.add_argument("--diagnostic-summary-path", type=Path, default=DEFAULT_DIAGNOSTIC_SUMMARY_PATH)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    args = parser.parse_args(argv)

    result = run_review(
        manifest_path=args.manifest_path,
        baseline_summary_path=args.baseline_summary_path,
        enrichment_summary_path=args.enrichment_summary_path,
        diagnostic_summary_path=args.diagnostic_summary_path,
    )
    write_outputs(result, args.json_output, args.report_output)
    print(json.dumps({"status": result["status"], "summary": result["summary"]}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
