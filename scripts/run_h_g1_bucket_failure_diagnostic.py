from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_gamma_aggregation_diagnostic as gamma_v1


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_JSONL = PROJECT_ROOT / "data" / "derived" / "spy_0dte" / "h_g1_gamma_regime" / "option_quote_enriched_10_date_snapshot_v2.jsonl"
DIAGNOSTIC_SUMMARY = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_gamma_regime_diagnostic_summary_v2_10date.json"
OUTPUT_JSON = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_bucket_failure_diagnostic.json"
OUTPUT_REPORT = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_bucket_failure_diagnostic.md"
COMPUTED_STATUS = "computed_with_caveats"


def run_diagnostic(input_jsonl: Path = INPUT_JSONL, diagnostic_summary: Path = DIAGNOSTIC_SUMMARY) -> dict[str, Any]:
    rows = _read_jsonl(input_jsonl)
    summary = _read_json(diagnostic_summary)
    failures = summary["validation_gates"]["coverage"]["bucket_weighted_coverage"]["required_bucket_failures"]
    failed_items = []
    for date, blockers in sorted(failures.items()):
        for blocker in blockers:
            bucket = _bucket_from_blocker(blocker)
            failed_items.append(_summarize_failed_bucket(date, bucket, rows))

    high_notional_low_row_rate = [
        item for item in failed_items
        if item["computed_rate"] < 0.60 and item["computed_oi_notional_share"] >= 0.80
    ]
    low_notional_low_row_rate = [
        item for item in failed_items
        if item["computed_rate"] < 0.60 and item["computed_oi_notional_share"] < 0.80
    ]
    status_counts = Counter(row.get("greeks_status", "missing") for row in rows)
    result = {
        "record_type": "h_g1_bucket_failure_diagnostic",
        "schema_version": "h_g1_bucket_failure_diagnostic_v1",
        "hypothesis_id": "H-G1",
        "source_input_jsonl": str(input_jsonl),
        "source_diagnostic_summary": str(diagnostic_summary),
        "paid_data_used": False,
        "network_used": False,
        "total_rows": len(rows),
        "greeks_status_counts": dict(sorted(status_counts.items())),
        "failed_bucket_count": len(failed_items),
        "failed_buckets": failed_items,
        "summary": {
            "all_failures_are_black_scholes_bracket_blocks": all(
                set(item["blocked_status_counts"]) <= {"blocked_mid_outside_black_scholes_bracket"}
                for item in failed_items
            ),
            "high_notional_low_row_rate_failure_count": len(high_notional_low_row_rate),
            "low_notional_low_row_rate_failure_count": len(low_notional_low_row_rate),
            "minimum_failed_bucket_computed_oi_notional_share": min(
                (item["computed_oi_notional_share"] for item in failed_items),
                default=None,
            ),
            "maximum_failed_bucket_computed_oi_notional_share": max(
                (item["computed_oi_notional_share"] for item in failed_items),
                default=None,
            ),
            "interpretation": _interpretation(high_notional_low_row_rate, low_notional_low_row_rate),
        },
        "decision": {
            "status": "diagnostic_complete_h_g1_still_blocked",
            "next_safe_action": (
                "Review whether the v2 policy should use OI-notional coverage as the primary bucket gate, "
                "or replace the low-notional failed dates with a v3 pre-registered date set. Do not claim H-G1 pass yet."
            ),
        },
    }
    return result


def write_outputs(result: dict[str, Any], output_json: Path = OUTPUT_JSON, output_report: Path = OUTPUT_REPORT) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    output_report.parent.mkdir(parents=True, exist_ok=True)
    output_report.write_text(_format_report(result), encoding="utf-8")


def _summarize_failed_bucket(date: str, bucket: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    bucket_rows = [
        row for row in rows
        if _row_date(row) == date and gamma_v1._row_bucket(row) == bucket
    ]
    computed_rows = [row for row in bucket_rows if row.get("greeks_status") == COMPUTED_STATUS]
    blocked_rows = [row for row in bucket_rows if row.get("greeks_status") != COMPUTED_STATUS]
    total_notional = sum(_oi_notional(row) for row in bucket_rows)
    computed_notional = sum(_oi_notional(row) for row in computed_rows)
    return {
        "date": date,
        "bucket": bucket,
        "row_count": len(bucket_rows),
        "computed_count": len(computed_rows),
        "blocked_count": len(blocked_rows),
        "computed_rate": round(_safe_rate(len(computed_rows), len(bucket_rows)), 6),
        "oi_notional_sum": round(total_notional, 6),
        "computed_oi_notional_sum": round(computed_notional, 6),
        "computed_oi_notional_share": round(_safe_rate(computed_notional, total_notional), 6),
        "status_counts": dict(sorted(Counter(row.get("greeks_status", "missing") for row in bucket_rows).items())),
        "blocked_status_counts": dict(sorted(Counter(row.get("greeks_status", "missing") for row in blocked_rows).items())),
        "right_counts": dict(sorted(Counter(row.get("right", "missing") for row in bucket_rows).items())),
        "blocked_right_counts": dict(sorted(Counter(row.get("right", "missing") for row in blocked_rows).items())),
        "moneyness_range": _range(_moneyness(row) for row in bucket_rows),
        "mid_range": _range(_float_or_none(row.get("mid")) for row in bucket_rows),
        "blocked_mid_range": _range(_float_or_none(row.get("mid")) for row in blocked_rows),
        "top_blocked_by_oi_notional": [
            _compact_row(row) for row in sorted(blocked_rows, key=_oi_notional, reverse=True)[:5]
        ],
    }


def _format_report(result: dict[str, Any]) -> str:
    lines = [
        "# H-G1 Bucket Failure Diagnostic",
        "",
        f"- Status: `{result['decision']['status']}`",
        f"- Paid data used: `{result['paid_data_used']}`",
        f"- Network used: `{result['network_used']}`",
        f"- Total rows: `{result['total_rows']}`",
        f"- Failed buckets reviewed: `{result['failed_bucket_count']}`",
        f"- Interpretation: {result['summary']['interpretation']}",
        "",
        "## Failed Buckets",
        "",
    ]
    for item in result["failed_buckets"]:
        lines.extend(
            [
                f"### {item['date']} {item['bucket']}",
                "",
                f"- Rows: `{item['row_count']}`; computed: `{item['computed_count']}`; blocked: `{item['blocked_count']}`",
                f"- Computed row rate: `{item['computed_rate']}`",
                f"- Computed OI-notional share: `{item['computed_oi_notional_share']}`",
                f"- Blocked status counts: `{json.dumps(item['blocked_status_counts'], sort_keys=True)}`",
                f"- Moneyness range: `{json.dumps(item['moneyness_range'], sort_keys=True)}`",
                "",
                "| right | strike | moneyness | mid | open_interest | oi_notional | greeks_status |",
                "|:--|--:|--:|--:|--:|--:|:--|",
            ]
        )
        for row in item["top_blocked_by_oi_notional"]:
            lines.append(
                f"| {row['right']} | {row['strike']} | {row['moneyness']} | {row['mid']} | "
                f"{row['open_interest']} | {row['oi_notional']} | {row['greeks_status']} |"
            )
        lines.append("")
    lines.extend(
        [
            "## Next Safe Action",
            "",
            result["decision"]["next_safe_action"],
            "",
        ]
    )
    return "\n".join(lines)


def _interpretation(high_notional_low_row_rate: list[dict[str, Any]], low_notional_low_row_rate: list[dict[str, Any]]) -> str:
    if high_notional_low_row_rate and not low_notional_low_row_rate:
        return (
            "All failed buckets have row-rate failures but retain at least 80% computed OI-notional coverage; "
            "the v2 row-rate floor may be stricter than the trade-relevant notional coverage."
        )
    if high_notional_low_row_rate and low_notional_low_row_rate:
        return (
            "Most failures need policy review, but at least one failed bucket also has weak OI-notional coverage; "
            "H-G1 should remain blocked until that date/bucket is repaired or replaced."
        )
    return "Failed buckets have weak row-rate and weak OI-notional coverage; prefer repair or replacement before policy changes."


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _bucket_from_blocker(blocker: str) -> str:
    suffix = "_computed_rate_below_60pct"
    if not blocker.endswith(suffix):
        raise ValueError(f"Unsupported bucket blocker: {blocker}")
    return blocker.removesuffix(suffix)


def _row_date(row: dict[str, Any]) -> str:
    return str(row.get("quote_timestamp_et", ""))[:10]


def _oi_notional(row: dict[str, Any]) -> float:
    oi = _float_or_none(row.get("open_interest"))
    underlying = _float_or_none(row.get("underlying_price"))
    if oi is None or underlying is None:
        return 0.0
    return oi * underlying * 100.0


def _moneyness(row: dict[str, Any]) -> float | None:
    strike = _float_or_none(row.get("strike"))
    underlying = _float_or_none(row.get("underlying_price"))
    if strike is None or underlying in (None, 0.0):
        return None
    return strike / underlying


def _compact_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "quote_timestamp_et": row.get("quote_timestamp_et"),
        "right": row.get("right"),
        "strike": _float_or_none(row.get("strike")),
        "moneyness": _round_or_none(_moneyness(row), 6),
        "mid": _round_or_none(_float_or_none(row.get("mid")), 6),
        "open_interest": row.get("open_interest"),
        "oi_notional": round(_oi_notional(row), 6),
        "greeks_status": row.get("greeks_status"),
    }


def _range(values: Any) -> dict[str, float | None]:
    filtered = [value for value in values if value is not None]
    if not filtered:
        return {"min": None, "max": None}
    return {"min": round(min(filtered), 6), "max": round(max(filtered), 6)}


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _round_or_none(value: float | None, digits: int) -> float | None:
    if value is None:
        return None
    return round(value, digits)


def _safe_rate(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Diagnose H-G1 required-bucket coverage failures without paid data calls.")
    parser.add_argument("--input-jsonl", type=Path, default=INPUT_JSONL)
    parser.add_argument("--diagnostic-summary", type=Path, default=DIAGNOSTIC_SUMMARY)
    parser.add_argument("--output-json", type=Path, default=OUTPUT_JSON)
    parser.add_argument("--output-report", type=Path, default=OUTPUT_REPORT)
    args = parser.parse_args(argv)

    result = run_diagnostic(args.input_jsonl, args.diagnostic_summary)
    write_outputs(result, args.output_json, args.output_report)
    print(json.dumps({"status": result["decision"]["status"], "failed_bucket_count": result["failed_bucket_count"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
