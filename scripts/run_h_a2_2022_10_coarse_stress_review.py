from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PREREGISTRATION_PATH = PROJECT_ROOT / "experiments" / "h_a2_2022_10_coarse_stress_review_preregistration.json"
DEFAULT_OUTPUT_JSON = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_2022_10_coarse_stress_review.json"
DEFAULT_OUTPUT_MD = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_2022_10_coarse_stress_review.md"


def run_h_a2_2022_10_coarse_stress_review(
    preregistration_path: Path = DEFAULT_PREREGISTRATION_PATH,
    output_json_path: Path = DEFAULT_OUTPUT_JSON,
    output_md_path: Path = DEFAULT_OUTPUT_MD,
) -> dict[str, Any]:
    prereg = _load_json(preregistration_path)
    inputs = prereg["input_paths"]
    summary = _load_json(PROJECT_ROOT / inputs["option_normalization_summary"])
    vix_by_date = _load_vix(PROJECT_ROOT / inputs["vix_vxv"])
    macro_by_date = _load_high_importance_macro(PROJECT_ROOT / inputs["macro_calendar"])
    start = prereg["method"]["window"]["start"]
    end = prereg["method"]["window"]["end"]

    days = []
    sorted_vix_dates = sorted(vix_by_date)
    for item in summary.get("files", []):
        trade_date = item["trade_date"]
        if not start <= trade_date <= end:
            continue
        same_day_vix = vix_by_date.get(trade_date)
        prior_date = _prior_vix_date(trade_date, sorted_vix_dates)
        prior_vix = vix_by_date.get(prior_date) if prior_date else None
        high_events = macro_by_date.get(trade_date, [])
        quote_rows = int(item.get("output_rows", 0))
        days.append(
            {
                "date": trade_date,
                "day_of_week": date.fromisoformat(trade_date).strftime("%A"),
                "0dte_quote_available": quote_rows > 0,
                "0dte_quote_rows": quote_rows,
                "input_rows": int(item.get("input_rows", 0)),
                "same_day_vix_close": same_day_vix,
                "same_day_high_vix": _gte(same_day_vix, 25.0),
                "same_day_stress_vix": _gte(same_day_vix, 30.0),
                "prior_vix_date": prior_date,
                "prior_close_vix": prior_vix,
                "prior_close_high_vix": _gte(prior_vix, 25.0),
                "prior_close_stress_vix": _gte(prior_vix, 30.0),
                "high_importance_macro": bool(high_events),
                "high_importance_macro_events": high_events,
            }
        )

    days = sorted(days, key=lambda row: row["date"])
    counts = _counts(days)
    decision = _decision(counts)
    report = {
        "schema_version": "h_a2_2022_10_coarse_stress_review_v1",
        "artifact_type": "diagnostic",
        "hypothesis_id": "H-A2",
        "evidence_tier": "E1",
        "status": decision["status"],
        "conclusion": "ยังสรุปไม่ได้",
        "conclusion_reason": decision["reason"],
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source_preregistration": _relative(preregistration_path),
        "source_input_paths": inputs,
        "window": {"start": start, "end": end, "unit": "trading_day"},
        "allowed_claim": prereg["decision_frame"]["allowed_claim"],
        "forbidden_claims": prereg["decision_frame"]["forbidden_claims"],
        "network_used": False,
        "paid_data_used": False,
        "new_data_requested": False,
        "ibkr_request_used": False,
        "llm_call_used": False,
        "strategy_pnl_used": False,
        "strategy_use_allowed": False,
        "paper_trading_allowed": False,
        "operational_validation_allowed": False,
        "real_money_allowed": False,
        "exact_orb_tested": False,
        "exact_rerun_approved": False,
        "research_log_required": True,
        "research_log_slug": "higanbana-h-a2-2022-10-coarse-stress-review",
        "volatility_thresholds": prereg["method"]["volatility_thresholds"],
        "lookahead_policy": prereg["method"]["lookahead_policy"],
        "counts": counts,
        "decision_rule_evaluation": decision["rule_evaluation"],
        "trading_days": days,
        "tier_blockers": [
            "E1 coarse stress/regime diagnostic only",
            "No SPY 1-minute bars were used, so exact ORB entries/exits were not tested",
            "No strategy PnL, Sharpe, PSR, DSR, MinTRL, or big-day dependency can be computed from this review",
            "Same-day VIX close is diagnostic-only and not an ex-ante trading input",
            "Macro calendar flags are event-risk proxies, not timestamp-clean news or LLM evidence",
            "This artifact cannot approve paper trading, operational validation, or real-money trading",
        ],
        "next_safe_action": decision["next_safe_action"],
    }
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_md_path.write_text(_markdown(report), encoding="utf-8")
    return report


def _counts(days: list[dict[str, Any]]) -> dict[str, Any]:
    quote_days = [row for row in days if row["0dte_quote_available"]]
    high_macro_quote_days = [row for row in quote_days if row["high_importance_macro"]]
    any_vix_quote_days = [
        row
        for row in quote_days
        if row["same_day_high_vix"] or row["same_day_stress_vix"] or row["prior_close_high_vix"] or row["prior_close_stress_vix"]
    ]
    non_macro_high_vix_quote_days = [
        row
        for row in quote_days
        if not row["high_importance_macro"] and (row["same_day_high_vix"] or row["prior_close_high_vix"])
    ]
    return {
        "trading_day_count": len(days),
        "0dte_quote_available_day_count": len(quote_days),
        "0dte_quote_missing_day_count": len(days) - len(quote_days),
        "same_day_high_vix_day_count": sum(1 for row in days if row["same_day_high_vix"]),
        "same_day_stress_vix_day_count": sum(1 for row in days if row["same_day_stress_vix"]),
        "prior_close_high_vix_day_count": sum(1 for row in days if row["prior_close_high_vix"]),
        "prior_close_stress_vix_day_count": sum(1 for row in days if row["prior_close_stress_vix"]),
        "high_importance_macro_day_count": sum(1 for row in days if row["high_importance_macro"]),
        "quote_available_and_same_day_high_vix_count": sum(1 for row in quote_days if row["same_day_high_vix"]),
        "quote_available_and_same_day_stress_vix_count": sum(1 for row in quote_days if row["same_day_stress_vix"]),
        "quote_available_and_prior_high_vix_count": sum(1 for row in quote_days if row["prior_close_high_vix"]),
        "quote_available_and_prior_stress_vix_count": sum(1 for row in quote_days if row["prior_close_stress_vix"]),
        "quote_available_and_high_importance_macro_count": len(high_macro_quote_days),
        "quote_available_and_no_high_importance_macro_count": len(quote_days) - len(high_macro_quote_days),
        "quote_available_and_any_high_or_stress_vix_count": len(any_vix_quote_days),
        "quote_available_and_non_macro_high_vix_count": len(non_macro_high_vix_quote_days),
        "quote_available_dates": [row["date"] for row in quote_days],
        "quote_missing_dates": [row["date"] for row in days if not row["0dte_quote_available"]],
        "quote_available_high_importance_macro_dates": [row["date"] for row in high_macro_quote_days],
        "quote_available_any_high_or_stress_vix_dates": [row["date"] for row in any_vix_quote_days],
        "quote_available_non_macro_high_vix_dates": [row["date"] for row in non_macro_high_vix_quote_days],
        "by_day_of_week": _count_by(days, "day_of_week"),
    }


def _decision(counts: dict[str, Any]) -> dict[str, Any]:
    has_vix_overlap = counts["quote_available_and_any_high_or_stress_vix_count"] > 0
    has_macro_or_non_macro_stress = (
        counts["quote_available_and_high_importance_macro_count"] > 0
        or counts["quote_available_and_non_macro_high_vix_count"] > 0
    )
    if counts["trading_day_count"] == 0:
        status = "blocked_input_missing"
        reason = "No October 2022 trading days were found in the normalization summary."
    elif has_vix_overlap and has_macro_or_non_macro_stress:
        status = "continue_exact_rerun_research"
        reason = (
            "The local October 2022 cache has enough coarse stress/regime overlap to keep H-A2 exact-rerun research alive, "
            "but only as prioritization evidence."
        )
    else:
        status = "deprioritize_exact_rerun_research"
        reason = (
            "The local October 2022 cache does not show enough quote/regime overlap to justify chasing exact-resolution "
            "H-A2 rerun work from this month alone."
        )
    return {
        "status": status,
        "reason": reason,
        "rule_evaluation": {
            "has_quote_available_high_or_stress_vix_overlap": has_vix_overlap,
            "has_quote_available_macro_or_non_macro_high_vix_overlap": has_macro_or_non_macro_stress,
            "fixed_n_rule_used": False,
        },
        "next_safe_action": (
            "Do not request IBKR bars from this artifact alone. Use this E1 result to decide whether a separate, explicitly "
            "pre-registered lower-resolution proxy or exact SPY bar source plan is worth drafting for H-A2."
            if status == "continue_exact_rerun_research"
            else "Do not chase exact October 2022 H-A2 bars from this month alone; revise the H-A2 data target or mechanism first."
        ),
    }


def _load_vix(path: Path) -> dict[str, float]:
    values: dict[str, float] = {}
    for row in _load_jsonl(path):
        if isinstance(row.get("date"), str) and isinstance(row.get("vix_close"), (int, float)):
            values[row["date"]] = float(row["vix_close"])
    return values


def _load_high_importance_macro(path: Path) -> dict[str, list[str]]:
    events: dict[str, list[str]] = defaultdict(list)
    for row in _load_jsonl(path):
        if row.get("importance") != "high":
            continue
        timestamp = row.get("event_timestamp_et", "")
        day = timestamp[:10]
        if day:
            events[day].append(row.get("event_type", "UNKNOWN"))
    return {day: sorted(values) for day, values in events.items()}


def _prior_vix_date(day: str, sorted_vix_dates: list[str]) -> str | None:
    candidates = [item for item in sorted_vix_dates if item < day]
    return candidates[-1] if candidates else None


def _gte(value: float | None, threshold: float) -> bool:
    return value is not None and value >= threshold


def _count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = row[key]
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _markdown(report: dict[str, Any]) -> str:
    counts = report["counts"]
    return "\n".join(
        [
            "# H-A2 2022-10 Coarse Stress Review",
            "",
            f"- **Status**: `{report['status']}`",
            f"- **Evidence tier**: `{report['evidence_tier']}`",
            f"- **Conclusion**: {report['conclusion']}",
            f"- **Reason**: {report['conclusion_reason']}",
            f"- **Network used**: `{report['network_used']}`",
            f"- **Paid data used**: `{report['paid_data_used']}`",
            f"- **IBKR request used**: `{report['ibkr_request_used']}`",
            f"- **LLM call used**: `{report['llm_call_used']}`",
            f"- **Strategy PnL used**: `{report['strategy_pnl_used']}`",
            f"- **Paper trading allowed**: `{report['paper_trading_allowed']}`",
            "",
            "## Counts",
            "",
            f"- Trading days: `{counts['trading_day_count']}`",
            f"- 0DTE quote-available days: `{counts['0dte_quote_available_day_count']}`",
            f"- 0DTE quote-missing days: `{counts['0dte_quote_missing_day_count']}`",
            f"- Same-day high VIX days: `{counts['same_day_high_vix_day_count']}`",
            f"- Same-day stress VIX days: `{counts['same_day_stress_vix_day_count']}`",
            f"- Prior-close high VIX days: `{counts['prior_close_high_vix_day_count']}`",
            f"- Prior-close stress VIX days: `{counts['prior_close_stress_vix_day_count']}`",
            f"- High-importance macro days: `{counts['high_importance_macro_day_count']}`",
            f"- Quote-available + high/stress VIX days: `{counts['quote_available_and_any_high_or_stress_vix_count']}`",
            f"- Quote-available + high-importance macro days: `{counts['quote_available_and_high_importance_macro_count']}`",
            f"- Quote-available + non-macro high VIX days: `{counts['quote_available_and_non_macro_high_vix_count']}`",
            "",
            "## Quote-Available Dates",
            "",
            ", ".join(counts["quote_available_dates"]) or "None",
            "",
            "## Next Safe Action",
            "",
            report["next_safe_action"],
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the H-A2 no-paid 2022-10 coarse stress/regime review.")
    parser.add_argument("--preregistration-path", type=Path, default=DEFAULT_PREREGISTRATION_PATH)
    parser.add_argument("--output-json-path", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md-path", type=Path, default=DEFAULT_OUTPUT_MD)
    args = parser.parse_args(argv)
    report = run_h_a2_2022_10_coarse_stress_review(args.preregistration_path, args.output_json_path, args.output_md_path)
    print(
        json.dumps(
            {"status": report["status"], "output_json": _relative(args.output_json_path), "output_md": _relative(args.output_md_path)},
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
