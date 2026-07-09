from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from pathlib import Path
from typing import Any


sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_gamma_aggregation_diagnostic as gamma_v1


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_JSONL = PROJECT_ROOT / "data" / "derived" / "spy_0dte" / "h_g1_gamma_regime" / "option_quote_enriched_manifest_v3_snapshot.jsonl"
DIAGNOSTIC_SUMMARY = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_gamma_regime_diagnostic_summary_v3.json"
OUTPUT_JSON = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_manifest_v3_bucket_failure_diagnostic.json"
OUTPUT_REPORT = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_manifest_v3_bucket_failure_diagnostic.md"
COMPUTED_STATUS = "computed_with_caveats"


def run_diagnostic(input_jsonl: Path = INPUT_JSONL, diagnostic_summary: Path = DIAGNOSTIC_SUMMARY) -> dict[str, Any]:
    rows = _read_jsonl(input_jsonl)
    summary = _read_json(diagnostic_summary)
    failures = summary["validation_gates"]["coverage"]["bucket_weighted_coverage"]["required_bucket_failures"]
    failed_buckets = []
    for date, blockers in sorted(failures.items()):
        for blocker in blockers:
            bucket = _bucket_from_blocker(blocker)
            failed_buckets.append(_summarize_failed_bucket(date, bucket, rows))

    opposite_right_blocked_rows = sum(item["blocked_side_alignment_counts"].get("opposite_right_for_bucket", 0) for item in failed_buckets)
    blocked_rows = sum(item["blocked_count"] for item in failed_buckets)
    high_notional_failures = [
        item for item in failed_buckets
        if item["computed_oi_notional_share"] >= 0.80
    ]
    weak_notional_failures = [
        item for item in failed_buckets
        if item["computed_oi_notional_share"] < 0.80
    ]
    result = {
        "record_type": "h_g1_manifest_v3_bucket_failure_diagnostic",
        "schema_version": "h_g1_manifest_v3_bucket_failure_diagnostic_v1",
        "hypothesis_id": "H-G1",
        "evidence_tier": "E1",
        "research_log_required": True,
        "research_log_slug": "higanbana-gamma-oi-v3-bucket-policy-diagnostic",
        "research_log_path": "research_log/016-higanbana-gamma-oi-v3-bucket-policy-diagnostic.md",
        "source_input_jsonl": str(input_jsonl),
        "source_diagnostic_summary": str(diagnostic_summary),
        "paid_data_used": False,
        "network_used": False,
        "total_rows": len(rows),
        "failed_bucket_count": len(failed_buckets),
        "failed_buckets": failed_buckets,
        "summary": {
            "all_failed_buckets_are_bracket_blocks": all(
                set(item["blocked_status_counts"]) <= {"blocked_mid_outside_black_scholes_bracket"}
                for item in failed_buckets
            ),
            "blocked_rows_in_failed_buckets": blocked_rows,
            "opposite_right_blocked_rows": opposite_right_blocked_rows,
            "opposite_right_blocked_row_share": round(_safe_rate(opposite_right_blocked_rows, blocked_rows), 6),
            "high_notional_failure_count": len(high_notional_failures),
            "weak_notional_failure_count": len(weak_notional_failures),
            "minimum_failed_bucket_computed_oi_notional_share": min(
                (item["computed_oi_notional_share"] for item in failed_buckets),
                default=None,
            ),
            "minimum_failed_bucket_gamma_proxy_share": min(
                (item["retained_abs_gamma_proxy_share"] for item in failed_buckets if item["retained_abs_gamma_proxy_share"] is not None),
                default=None,
            ),
            "primary_diagnosis": _primary_diagnosis(failed_buckets, opposite_right_blocked_rows, blocked_rows),
        },
        "decision": {
            "status": "diagnostic_complete_h_g1_still_blocked",
            "conclusion": "ยังสรุปไม่ได้",
            "next_safe_action": (
                "Do not use NOVI/net-gamma as a strategy filter yet. Review the bucket policy because the failed row-rate "
                "cells are driven by opposite-right ITM rows inside moneyness-only buckets; then choose between a "
                "pre-registered side-aware bucket gate, an OI/gamma-notional gate, or another replacement/repair path."
            ),
        },
        "tier_blockers": [
            "E1 diagnostic only",
            "No strategy backtest acceptance",
            "H-G1 policy gate still blocked",
        ],
    }
    return result


def write_outputs(result: dict[str, Any], output_json: Path = OUTPUT_JSON, output_report: Path = OUTPUT_REPORT) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
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
    computed_abs_gamma_proxy = sum(abs(gamma_v1.local_gamma_exposure(row)) for row in computed_rows if _has_gamma_inputs(row))
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
        "computed_abs_gamma_proxy": round(computed_abs_gamma_proxy, 6),
        "retained_abs_gamma_proxy_share": 1.0 if computed_abs_gamma_proxy else None,
        "status_counts": dict(sorted(Counter(row.get("greeks_status", "missing") for row in bucket_rows).items())),
        "blocked_status_counts": dict(sorted(Counter(row.get("greeks_status", "missing") for row in blocked_rows).items())),
        "side_alignment_counts": _counts(_side_alignment(row, bucket) for row in bucket_rows),
        "blocked_side_alignment_counts": _counts(_side_alignment(row, bucket) for row in blocked_rows),
        "blocked_intrinsic_relation_counts": _counts(_intrinsic_relation(row) for row in blocked_rows),
        "snapshot_timestamp_counts": _counts(str(row.get("quote_timestamp_et")) for row in bucket_rows),
        "moneyness": _distribution(_moneyness(row) for row in bucket_rows),
        "blocked_moneyness": _distribution(_moneyness(row) for row in blocked_rows),
        "spread": _distribution(_spread(row) for row in bucket_rows),
        "blocked_spread": _distribution(_spread(row) for row in blocked_rows),
        "spread_pct_mid": _distribution(_spread_pct_mid(row) for row in bucket_rows),
        "blocked_spread_pct_mid": _distribution(_spread_pct_mid(row) for row in blocked_rows),
        "mid_minus_intrinsic": _distribution(_mid_minus_intrinsic(row) for row in bucket_rows),
        "blocked_mid_minus_intrinsic": _distribution(_mid_minus_intrinsic(row) for row in blocked_rows),
        "top_blocked_by_oi_notional": [
            _compact_row(row, bucket) for row in sorted(blocked_rows, key=_oi_notional, reverse=True)[:5]
        ],
    }


def _format_report(result: dict[str, Any]) -> str:
    lines = [
        "# H-G1 Manifest V3 Bucket Failure Diagnostic",
        "",
        f"- Status: `{result['decision']['status']}`",
        f"- Conclusion: {result['decision']['conclusion']}",
        f"- Evidence tier: `{result['evidence_tier']}`",
        f"- Paid data used: `{result['paid_data_used']}`",
        f"- Network used: `{result['network_used']}`",
        f"- Failed buckets reviewed: `{result['failed_bucket_count']}`",
        f"- Primary diagnosis: {result['summary']['primary_diagnosis']}",
        "",
        "## Summary",
        "",
        f"- Blocked rows in failed buckets: `{result['summary']['blocked_rows_in_failed_buckets']}`",
        f"- Opposite-right blocked rows: `{result['summary']['opposite_right_blocked_rows']}`",
        f"- Opposite-right blocked row share: `{result['summary']['opposite_right_blocked_row_share']}`",
        f"- Minimum computed OI-notional share among failed buckets: `{result['summary']['minimum_failed_bucket_computed_oi_notional_share']}`",
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
                f"- Blocked side alignment: `{json.dumps(item['blocked_side_alignment_counts'], sort_keys=True)}`",
                f"- Blocked spread pct/mid: `{json.dumps(item['blocked_spread_pct_mid'], sort_keys=True)}`",
                f"- Blocked mid minus intrinsic: `{json.dumps(item['blocked_mid_minus_intrinsic'], sort_keys=True)}`",
                "",
                "| right | strike | moneyness | mid | bid | ask | spread_pct_mid | mid_minus_intrinsic | open_interest | side_alignment | greeks_status |",
                "|:--|--:|--:|--:|--:|--:|--:|--:|--:|:--|:--|",
            ]
        )
        for row in item["top_blocked_by_oi_notional"]:
            lines.append(
                f"| {row['right']} | {row['strike']} | {row['moneyness']} | {row['mid']} | {row['bid']} | {row['ask']} | "
                f"{row['spread_pct_mid']} | {row['mid_minus_intrinsic']} | {row['open_interest']} | "
                f"{row['side_alignment']} | {row['greeks_status']} |"
            )
        lines.append("")
    lines.extend(["## Decision", "", result["decision"]["next_safe_action"], ""])
    return "\n".join(lines)


def _primary_diagnosis(failed_buckets: list[dict[str, Any]], opposite_right_blocked_rows: int, blocked_rows: int) -> str:
    if blocked_rows and opposite_right_blocked_rows == blocked_rows:
        return (
            "All blocked rows inside failed buckets are opposite-right ITM options created by moneyness-only buckets. "
            "The failure is primarily a bucket-definition/policy problem, not an OI join or timestamp problem."
        )
    if any(item["computed_oi_notional_share"] < 0.80 for item in failed_buckets):
        return "At least one failed bucket has weak OI-notional retention; replacement or repair remains preferable before policy relaxation."
    return "Failed row-rate cells retain high OI-notional coverage but need side-aware policy review before H-G1 can advance."


def _side_alignment(row: dict[str, Any], bucket: str) -> str:
    right = str(row.get("right", "")).lower()
    if bucket == "otm_call":
        return "expected_right_for_bucket" if right == "call" else "opposite_right_for_bucket"
    if bucket == "otm_put":
        return "expected_right_for_bucket" if right == "put" else "opposite_right_for_bucket"
    if bucket == "atm":
        return "atm_all_rights_allowed"
    return "non_required_bucket"


def _intrinsic_relation(row: dict[str, Any]) -> str:
    mid = _float_or_none(row.get("mid"))
    intrinsic = _intrinsic_value(row)
    if mid is None or intrinsic is None:
        return "missing"
    diff = mid - intrinsic
    if diff < -1e-6:
        return "below_intrinsic"
    if diff <= 0.05:
        return "near_intrinsic"
    return "above_intrinsic"


def _compact_row(row: dict[str, Any], bucket: str) -> dict[str, Any]:
    return {
        "quote_timestamp_et": row.get("quote_timestamp_et"),
        "right": row.get("right"),
        "strike": _round_or_none(_float_or_none(row.get("strike")), 6),
        "moneyness": _round_or_none(_moneyness(row), 6),
        "bid": _round_or_none(_float_or_none(row.get("bid")), 6),
        "ask": _round_or_none(_float_or_none(row.get("ask")), 6),
        "mid": _round_or_none(_float_or_none(row.get("mid")), 6),
        "spread_pct_mid": _round_or_none(_spread_pct_mid(row), 6),
        "mid_minus_intrinsic": _round_or_none(_mid_minus_intrinsic(row), 6),
        "open_interest": row.get("open_interest"),
        "oi_notional": round(_oi_notional(row), 6),
        "side_alignment": _side_alignment(row, bucket),
        "greeks_status": row.get("greeks_status"),
    }


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


def _has_gamma_inputs(row: dict[str, Any]) -> bool:
    return row.get("gamma") is not None and row.get("open_interest") is not None and row.get("underlying_price") is not None


def _oi_notional(row: dict[str, Any]) -> float:
    oi = _float_or_none(row.get("open_interest"))
    underlying = _float_or_none(row.get("underlying_price"))
    if oi is None or underlying is None:
        return 0.0
    return oi * underlying * gamma_v1.CONTRACT_MULTIPLIER


def _moneyness(row: dict[str, Any]) -> float | None:
    strike = _float_or_none(row.get("strike"))
    underlying = _float_or_none(row.get("underlying_price"))
    if strike is None or underlying in (None, 0.0):
        return None
    return strike / underlying


def _intrinsic_value(row: dict[str, Any]) -> float | None:
    strike = _float_or_none(row.get("strike"))
    underlying = _float_or_none(row.get("underlying_price"))
    if strike is None or underlying is None:
        return None
    right = str(row.get("right", "")).lower()
    if right == "call":
        return max(underlying - strike, 0.0)
    if right == "put":
        return max(strike - underlying, 0.0)
    return None


def _mid_minus_intrinsic(row: dict[str, Any]) -> float | None:
    mid = _float_or_none(row.get("mid"))
    intrinsic = _intrinsic_value(row)
    if mid is None or intrinsic is None:
        return None
    return mid - intrinsic


def _spread(row: dict[str, Any]) -> float | None:
    bid = _float_or_none(row.get("bid"))
    ask = _float_or_none(row.get("ask"))
    if bid is None or ask is None:
        return None
    return ask - bid


def _spread_pct_mid(row: dict[str, Any]) -> float | None:
    spread = _spread(row)
    mid = _float_or_none(row.get("mid"))
    if spread is None or mid in (None, 0.0):
        return None
    return spread / mid


def _distribution(values: Any) -> dict[str, float | None]:
    filtered = [value for value in values if value is not None]
    if not filtered:
        return {"min": None, "median": None, "max": None}
    return {
        "min": round(min(filtered), 6),
        "median": round(statistics.median(filtered), 6),
        "max": round(max(filtered), 6),
    }


def _counts(values: Any) -> dict[str, int]:
    return dict(sorted(Counter(values).items()))


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
    parser = argparse.ArgumentParser(description="Diagnose H-G1 manifest-v3 required-bucket coverage failures.")
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
