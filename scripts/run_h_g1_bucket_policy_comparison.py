from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_gamma_aggregation_diagnostic as gamma_v1


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PREREGISTRATION = PROJECT_ROOT / "experiments" / "h_g1_bucket_policy_review_preregistration.json"
INPUT_JSONL = PROJECT_ROOT / "data" / "derived" / "spy_0dte" / "h_g1_gamma_regime" / "option_quote_enriched_manifest_v3_snapshot.jsonl"
V3_SUMMARY = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_gamma_regime_diagnostic_summary_v3.json"
BUCKET_FAILURE_DIAGNOSTIC = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_manifest_v3_bucket_failure_diagnostic.json"
OUTPUT_JSON = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_bucket_policy_comparison.json"
OUTPUT_REPORT = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_bucket_policy_comparison.md"
COMPUTED_STATUS = "computed_with_caveats"
REQUIRED_BUCKETS = ("otm_put", "atm", "otm_call")


def run_comparison(
    preregistration_path: Path = PREREGISTRATION,
    input_jsonl: Path = INPUT_JSONL,
    v3_summary_path: Path = V3_SUMMARY,
    bucket_failure_path: Path = BUCKET_FAILURE_DIAGNOSTIC,
) -> dict[str, Any]:
    prereg = _read_json(preregistration_path)
    rows = _read_jsonl(input_jsonl)
    v3_summary = _read_json(v3_summary_path)
    bucket_failure = _read_json(bucket_failure_path)
    policies = {item["policy_id"]: item for item in prereg["candidate_policies"]}

    per_date = sorted({_row_date(row) for row in rows})
    candidate_a = _evaluate_candidate_a(rows, per_date, policies["candidate_a_current_v2_moneyness_only"], v3_summary)
    candidate_b = _evaluate_candidate_b(rows, per_date, policies["candidate_b_side_aware_required_bucket"])
    candidate_c = _evaluate_candidate_c(rows, per_date, policies["candidate_c_notional_weighted_coverage"])
    candidates = {
        candidate_a["policy_id"]: candidate_a,
        candidate_b["policy_id"]: candidate_b,
        candidate_c["policy_id"]: candidate_c,
    }
    recommendation = _recommend_candidate(candidates, bucket_failure)

    return {
        "record_type": "h_g1_bucket_policy_comparison",
        "schema_version": "h_g1_bucket_policy_comparison_v1",
        "hypothesis_id": "H-G1",
        "evidence_tier": "E1",
        "status": "policy_review_complete_h_g1_still_blocked",
        "conclusion": "ยังสรุปไม่ได้",
        "allowed_output_status": prereg["rerun_policy"]["allowed_output_status"],
        "research_log_required": True,
        "research_log_slug": "higanbana-gamma-bucket-policy-comparison",
        "research_log_path": "research_log/017-higanbana-gamma-bucket-policy-comparison.md",
        "network_used": False,
        "paid_data_used": False,
        "strategy_pnl_used": False,
        "source_preregistration": _relative(preregistration_path),
        "source_input_jsonl": _relative(input_jsonl),
        "source_v3_summary": _relative(v3_summary_path),
        "source_bucket_failure_diagnostic": _relative(bucket_failure_path),
        "date_count": len(per_date),
        "quote_count": len(rows),
        "h_g1_15_locked_facts": prereg["locked_h_g1_15_facts"],
        "candidate_results": candidates,
        "recommendation": recommendation,
        "decision": {
            "status": "h_g1_still_blocked_policy_review_only",
            "next_safe_action": (
                "If continuing H-G1, draft an explicit policy adoption artifact for the side-aware required-bucket "
                "gate and rerun the gamma diagnostic under that policy. Do not treat this comparison as strategy "
                "validation, do not use strategy PnL for policy selection, and do not use NOVI/net-gamma as a strategy filter."
            ),
        },
        "tier_blockers": [
            "E1 policy-review diagnostic only",
            "No strategy backtest acceptance",
            "No MinTRL/PSR acceptance evidence for a trading rule",
            "Policy is not adopted by this comparison alone",
        ],
        "forbidden_claims_preserved": prereg["forbidden_claims"],
    }


def write_outputs(result: dict[str, Any], output_json: Path = OUTPUT_JSON, output_report: Path = OUTPUT_REPORT) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_report.parent.mkdir(parents=True, exist_ok=True)
    output_report.write_text(_format_report(result), encoding="utf-8")


def _evaluate_candidate_a(
    rows: list[dict[str, Any]],
    dates: list[str],
    policy: dict[str, Any],
    v3_summary: dict[str, Any],
) -> dict[str, Any]:
    per_date = {}
    failures = []
    for date in dates:
        date_rows = [row for row in rows if _row_date(row) == date]
        bucket_metrics = {
            bucket: _bucket_metrics([row for row in date_rows if gamma_v1._row_bucket(row) == bucket])
            for bucket in REQUIRED_BUCKETS
        }
        blockers = [
            f"{bucket}_computed_rate_below_60pct"
            for bucket, metrics in bucket_metrics.items()
            if metrics["row_count"] == 0 or metrics["computed_rate"] < policy["row_rate_floor"]
        ]
        combined = _combined_metrics(bucket_metrics)
        if combined["computed_oi_notional_share"] < policy["computed_oi_notional_share_floor"]:
            blockers.append("combined_required_bucket_oi_notional_share_below_floor")
        if combined["retained_abs_gamma_proxy_share"] < policy["retained_abs_gamma_proxy_share_floor"]:
            blockers.append("combined_required_bucket_gamma_proxy_share_below_floor")
        per_date[date] = {
            "status": "pass" if not blockers else "blocked",
            "blockers": blockers,
            "bucket_metrics": bucket_metrics,
            "combined_required_bucket_metrics": combined,
        }
        failures.extend(f"{date}:{blocker}" for blocker in blockers)

    source_failures = v3_summary["validation_gates"]["coverage"]["bucket_weighted_coverage"]["required_bucket_failures"]
    return _candidate_result(
        policy,
        per_date,
        failures,
        notes=[
            "Baseline current-v2 policy keeps moneyness-only pass/fail.",
            f"Source v3 required-bucket failures: {source_failures}",
        ],
    )


def _evaluate_candidate_b(rows: list[dict[str, Any]], dates: list[str], policy: dict[str, Any]) -> dict[str, Any]:
    per_date = {}
    failures = []
    for date in dates:
        date_rows = [row for row in rows if _row_date(row) == date]
        bucket_rows = {
            "otm_put": [
                row for row in date_rows
                if gamma_v1._row_bucket(row) == "otm_put" and str(row.get("right", "")).lower() == "put"
            ],
            "atm": [row for row in date_rows if gamma_v1._row_bucket(row) == "atm"],
            "otm_call": [
                row for row in date_rows
                if gamma_v1._row_bucket(row) == "otm_call" and str(row.get("right", "")).lower() == "call"
            ],
        }
        bucket_metrics = {bucket: _bucket_metrics(items) for bucket, items in bucket_rows.items()}
        opposite_right_counts = _opposite_right_counts(date_rows)
        blockers = []
        for bucket, metrics in bucket_metrics.items():
            if metrics["row_count"] == 0:
                blockers.append(f"{bucket}_missing")
            if metrics["computed_rate"] < policy["row_rate_floor"]:
                blockers.append(f"{bucket}_side_aware_computed_rate_below_floor")
            if metrics["computed_oi_notional_share"] < policy["computed_oi_notional_share_floor"]:
                blockers.append(f"{bucket}_side_aware_oi_notional_share_below_floor")
            if metrics["retained_abs_gamma_proxy_share"] < policy["retained_abs_gamma_proxy_share_floor"]:
                blockers.append(f"{bucket}_side_aware_gamma_proxy_share_below_floor")
        per_date[date] = {
            "status": "pass" if not blockers else "blocked",
            "blockers": blockers,
            "bucket_metrics": bucket_metrics,
            "reported_opposite_right_itm_rows": opposite_right_counts,
        }
        failures.extend(f"{date}:{blocker}" for blocker in blockers)

    return _candidate_result(
        policy,
        per_date,
        failures,
        notes=[
            "Side-aware policy directly separates opposite-right ITM rows from otm_put/otm_call pass-fail gates.",
            "Opposite-right ITM rows remain reportable and are not hidden.",
        ],
    )


def _evaluate_candidate_c(rows: list[dict[str, Any]], dates: list[str], policy: dict[str, Any]) -> dict[str, Any]:
    per_date = {}
    failures = []
    warnings = []
    for date in dates:
        date_rows = [row for row in rows if _row_date(row) == date]
        bucket_metrics = {
            bucket: _bucket_metrics([row for row in date_rows if gamma_v1._row_bucket(row) == bucket])
            for bucket in REQUIRED_BUCKETS
        }
        blockers = []
        row_rate_warnings = []
        for bucket, metrics in bucket_metrics.items():
            if metrics["row_count"] == 0:
                blockers.append(f"{bucket}_missing")
            if metrics["computed_oi_notional_share"] < policy["computed_oi_notional_share_floor"]:
                blockers.append(f"{bucket}_oi_notional_share_below_floor")
            if metrics["retained_abs_gamma_proxy_share"] < policy["retained_abs_gamma_proxy_share_floor"]:
                blockers.append(f"{bucket}_gamma_proxy_share_below_floor")
            if metrics["computed_rate"] < policy["row_rate_floor"]:
                row_rate_warnings.append(f"{bucket}_row_rate_warning")
        per_date[date] = {
            "status": "pass" if not blockers else "blocked",
            "blockers": blockers,
            "warnings": row_rate_warnings,
            "bucket_metrics": bucket_metrics,
            "reported_opposite_right_itm_rows": _opposite_right_counts(date_rows),
        }
        failures.extend(f"{date}:{blocker}" for blocker in blockers)
        warnings.extend(f"{date}:{warning}" for warning in row_rate_warnings)

    result = _candidate_result(
        policy,
        per_date,
        failures,
        notes=[
            "Notional-weighted policy treats low row-rate as a warning only when OI-notional and observable gamma-proxy representation pass.",
            "This candidate is more permissive on row count but still blocks economically weak notional coverage.",
        ],
    )
    result["warnings"] = warnings
    return result


def _candidate_result(
    policy: dict[str, Any],
    per_date: dict[str, Any],
    failures: list[str],
    notes: list[str],
) -> dict[str, Any]:
    passed_dates = sum(1 for item in per_date.values() if item["status"] == "pass")
    return {
        "policy_id": policy["policy_id"],
        "required_bucket_gate": policy["required_bucket_gate"],
        "status": "policy_candidate_passes_coverage_review" if not failures else "policy_candidate_blocked",
        "date_count": len(per_date),
        "passed_date_count": passed_dates,
        "blocked_date_count": len(per_date) - passed_dates,
        "failure_count": len(failures),
        "failures": failures,
        "per_date": per_date,
        "notes": notes,
    }


def _recommend_candidate(candidates: dict[str, Any], bucket_failure: dict[str, Any]) -> dict[str, Any]:
    side_aware = candidates["candidate_b_side_aware_required_bucket"]
    notional = candidates["candidate_c_notional_weighted_coverage"]
    if side_aware["status"] == "policy_candidate_passes_coverage_review":
        candidate = "candidate_b_side_aware_required_bucket"
        reason = (
            "Side-aware buckets target the diagnosed mechanism: H-G1.15 found all blocked failed-bucket rows were "
            "opposite-right ITM rows caused by moneyness-only buckets. This candidate passes coverage review without "
            "using strategy PnL, new dates, or paid data."
        )
    elif notional["status"] == "policy_candidate_passes_coverage_review":
        candidate = "candidate_c_notional_weighted_coverage"
        reason = "Notional-weighted coverage passes, but it is less mechanism-specific than side-aware buckets."
    else:
        candidate = None
        reason = "No candidate passes the policy-review gates; H-G1 should remain blocked pending a new pre-registration."
    return {
        "recommended_for_separate_policy_adoption_review": candidate,
        "reason": reason,
        "policy_adopted_now": False,
        "strategy_use_allowed": False,
        "h_g1_15_primary_diagnosis": bucket_failure["summary"]["primary_diagnosis"],
    }


def _bucket_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    computed_rows = [row for row in rows if row.get("greeks_status") == COMPUTED_STATUS]
    total_notional = sum(_oi_notional(row) for row in rows)
    computed_notional = sum(_oi_notional(row) for row in computed_rows)
    computed_gamma = sum(abs(gamma_v1.local_gamma_exposure(row)) for row in computed_rows if _has_gamma_inputs(row))
    return {
        "row_count": len(rows),
        "computed_count": len(computed_rows),
        "computed_rate": round(_safe_rate(len(computed_rows), len(rows)), 6),
        "oi_notional_sum": round(total_notional, 6),
        "computed_oi_notional_sum": round(computed_notional, 6),
        "computed_oi_notional_share": round(_safe_rate(computed_notional, total_notional), 6),
        "observable_abs_gamma_proxy_sum": round(computed_gamma, 6),
        "retained_abs_gamma_proxy_share": 1.0 if computed_gamma > 0 else 0.0,
        "blocked_count": len(rows) - len(computed_rows),
        "blocked_status_counts": dict(sorted(_count(row.get("greeks_status", "missing") for row in rows if row.get("greeks_status") != COMPUTED_STATUS).items())),
    }


def _combined_metrics(bucket_metrics: dict[str, dict[str, Any]]) -> dict[str, Any]:
    total_notional = sum(item["oi_notional_sum"] for item in bucket_metrics.values())
    computed_notional = sum(item["computed_oi_notional_sum"] for item in bucket_metrics.values())
    gamma_sum = sum(item["observable_abs_gamma_proxy_sum"] for item in bucket_metrics.values())
    return {
        "oi_notional_sum": round(total_notional, 6),
        "computed_oi_notional_sum": round(computed_notional, 6),
        "computed_oi_notional_share": round(_safe_rate(computed_notional, total_notional), 6),
        "observable_abs_gamma_proxy_sum": round(gamma_sum, 6),
        "retained_abs_gamma_proxy_share": 1.0 if gamma_sum > 0 else 0.0,
    }


def _opposite_right_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: defaultdict[str, int] = defaultdict(int)
    for row in rows:
        bucket = gamma_v1._row_bucket(row)
        right = str(row.get("right", "")).lower()
        if bucket == "otm_put" and right == "call":
            counts["otm_put_opposite_right_call_rows"] += 1
        if bucket == "otm_call" and right == "put":
            counts["otm_call_opposite_right_put_rows"] += 1
    return dict(sorted(counts.items()))


def _format_report(result: dict[str, Any]) -> str:
    lines = [
        "# H-G1 Bucket Policy Comparison",
        "",
        f"- Status: `{result['status']}`",
        f"- Conclusion: `{result['conclusion']}`",
        f"- Evidence tier: `{result['evidence_tier']}`",
        f"- Allowed output status: `{result['allowed_output_status']}`",
        f"- Network used: `{result['network_used']}`",
        f"- Paid data used: `{result['paid_data_used']}`",
        f"- Strategy PnL used: `{result['strategy_pnl_used']}`",
        f"- Source rows: `{result['quote_count']}` across `{result['date_count']}` dates",
        "",
        "## Candidate Summary",
        "",
        "| Candidate | Gate | Status | Passed dates | Blocked dates | Failures |",
        "|:--|:--|:--|--:|--:|--:|",
    ]
    for candidate in result["candidate_results"].values():
        lines.append(
            f"| `{candidate['policy_id']}` | `{candidate['required_bucket_gate']}` | `{candidate['status']}` | "
            f"{candidate['passed_date_count']} | {candidate['blocked_date_count']} | {candidate['failure_count']} |"
        )
    lines.extend([
        "",
        "## Recommendation",
        "",
        f"- Recommended candidate for a separate policy-adoption review: `{result['recommendation']['recommended_for_separate_policy_adoption_review']}`",
        f"- Policy adopted now: `{result['recommendation']['policy_adopted_now']}`",
        f"- Strategy use allowed: `{result['recommendation']['strategy_use_allowed']}`",
        f"- Reason: {result['recommendation']['reason']}",
        "",
        "## Candidate Details",
        "",
    ])
    for candidate in result["candidate_results"].values():
        lines.extend([
            f"### {candidate['policy_id']}",
            "",
            f"- Status: `{candidate['status']}`",
            f"- Failures: `{candidate['failure_count']}`",
        ])
        if candidate.get("warnings"):
            lines.append(f"- Warnings: `{len(candidate['warnings'])}`")
        lines.extend(["", "| Date | Status | Blockers | Warnings |", "|:--|:--|:--|:--|"])
        for date, item in candidate["per_date"].items():
            warnings = item.get("warnings", [])
            lines.append(
                f"| `{date}` | `{item['status']}` | `{', '.join(item['blockers']) or 'none'}` | `{', '.join(warnings) or 'none'}` |"
            )
        lines.append("")
    lines.extend([
        "## Decision",
        "",
        result["decision"]["next_safe_action"],
        "",
    ])
    return "\n".join(lines)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


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


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_rate(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def _count(values: Any) -> dict[str, int]:
    counts: defaultdict[str, int] = defaultdict(int)
    for value in values:
        counts[str(value)] += 1
    return counts


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run H-G1 bucket-policy comparison using manifest-v3 rows only.")
    parser.add_argument("--preregistration", type=Path, default=PREREGISTRATION)
    parser.add_argument("--input-jsonl", type=Path, default=INPUT_JSONL)
    parser.add_argument("--v3-summary", type=Path, default=V3_SUMMARY)
    parser.add_argument("--bucket-failure", type=Path, default=BUCKET_FAILURE_DIAGNOSTIC)
    parser.add_argument("--output-json", type=Path, default=OUTPUT_JSON)
    parser.add_argument("--output-report", type=Path, default=OUTPUT_REPORT)
    args = parser.parse_args(argv)

    result = run_comparison(args.preregistration, args.input_jsonl, args.v3_summary, args.bucket_failure)
    write_outputs(result, args.output_json, args.output_report)
    print(json.dumps({
        "status": result["status"],
        "recommended_candidate": result["recommendation"]["recommended_for_separate_policy_adoption_review"],
        "strategy_use_allowed": result["recommendation"]["strategy_use_allowed"],
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
