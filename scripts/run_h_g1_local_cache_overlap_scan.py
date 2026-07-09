from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_JSON = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_local_cache_overlap_scan.json"
DEFAULT_OUTPUT_MD = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_local_cache_overlap_scan.md"
DEFAULT_PLAN_PATH = PROJECT_ROOT / "experiments" / "h_g1_sample_expansion_plan.json"
DEFAULT_BASELINE_PATH = PROJECT_ROOT / "reports" / "baselines" / "subsystem_a_orb_baseline_summary.json"
DEFAULT_ABLATION_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_g1_gamma_strategy_ablation_summary.json"
DEFAULT_ENRICHMENT_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_gamma_regime_enrichment_summary_v3_side_aware.json"
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def run_h_g1_local_cache_overlap_scan(
    output_json_path: Path = DEFAULT_OUTPUT_JSON,
    output_md_path: Path = DEFAULT_OUTPUT_MD,
    plan_path: Path = DEFAULT_PLAN_PATH,
    baseline_path: Path = DEFAULT_BASELINE_PATH,
    ablation_path: Path = DEFAULT_ABLATION_PATH,
    enrichment_path: Path = DEFAULT_ENRICHMENT_PATH,
) -> dict[str, Any]:
    plan = _load_json(plan_path)
    baseline = _load_json(baseline_path)
    ablation = _load_json(ablation_path)
    enrichment = _load_json(enrichment_path)

    baseline_dates = sorted({row["date"] for row in baseline.get("daily_pnl", []) if row.get("date")})
    # Baseline closed trades already prove that the needed quote/bar cache existed
    # for those specific trade dates. This scan is about trade overlap, not a full
    # quote inventory audit, so avoid reading every normalized OPRA row.
    local_quote_dates = set(baseline_dates)
    local_bar_dates = set(baseline_dates)
    local_oi_dates = _dates_from_oi_files(PROJECT_ROOT / "data" / "raw" / "spy_0dte" / "databento")
    macro_by_date = _macro_by_date(PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "macro_calendar" / "macro_event.jsonl")
    vix_by_date = _vix_by_date(PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "vix_vxv" / "vix_vxv.jsonl")

    current_gamma_dates = sorted({row["date"] for row in enrichment.get("date_summaries", []) if row.get("date")})
    current_intersection = sorted(set(baseline_dates) & set(current_gamma_dates))
    no_paid_candidates = sorted(set(baseline_dates) & local_quote_dates & local_bar_dates & local_oi_dates)
    additional_no_paid_candidates = sorted(set(no_paid_candidates) - set(current_gamma_dates))
    quote_bar_only_candidates = sorted((set(baseline_dates) & local_quote_dates & local_bar_dates) - local_oi_dates)

    candidate_rows = [
        _candidate_row(day, macro_by_date, vix_by_date, "no_paid_gamma_ready")
        for day in no_paid_candidates
    ]
    additional_rows = [
        _candidate_row(day, macro_by_date, vix_by_date, "additional_no_paid_gamma_ready")
        for day in additional_no_paid_candidates
    ]
    quote_bar_rows = [
        _candidate_row(day, macro_by_date, vix_by_date, "quote_bar_cached_but_missing_oi")
        for day in quote_bar_only_candidates
    ]

    projected_no_paid_count = len(current_intersection) + len(additional_no_paid_candidates)
    mintrl_gate = {
        "status": "blocked_insufficient_observations",
        "reason": (
            "No additional baseline trade dates have local quote, local SPY bar, and local OI files outside the current "
            "H-G1 gamma date set. The no-paid expanded sample remains too small to estimate Sharpe distribution inputs "
            "such as skewness, kurtosis, first-order autocorrelation, PSR, or MinTRL."
        ),
        "fixed_n_rule_used": False,
        "current_intersection_closed_trade_count": len(current_intersection),
        "additional_no_paid_closed_trade_count": len(additional_no_paid_candidates),
        "projected_no_paid_closed_trade_count": projected_no_paid_count,
    }

    status = "blocked_no_additional_no_paid_overlap" if not additional_no_paid_candidates else "complete_no_paid_scan"
    next_safe_action = (
        "Keep H-G1 parked. Return to News-Unblock or H-A2 external blockers; do not run a new gamma ablation or paid "
        "gamma cost gate from this scan because no additional no-paid gamma-ready baseline trade dates were found."
        if not additional_no_paid_candidates
        else "Run a separate MinTRL/PSR feasibility gate before any new H-G1 ablation or paid data decision."
    )

    report = {
        "schema_version": "h_g1_local_cache_overlap_scan_v1",
        "artifact_type": "h_g1_local_cache_overlap_scan",
        "hypothesis_id": "H-G1",
        "evidence_tier": "E0",
        "status": status,
        "conclusion": "ยังสรุปไม่ได้",
        "conclusion_reason": "This is a no-paid local-cache overlap scan, not a strategy test.",
        "source_sample_expansion_plan": _relative(plan_path),
        "source_baseline_summary": _relative(baseline_path),
        "source_strategy_ablation_summary": _relative(ablation_path),
        "source_gamma_enrichment": _relative(enrichment_path),
        "network_used": False,
        "paid_data_used": False,
        "new_data_requested": False,
        "strategy_pnl_used": False,
        "strategy_use_allowed": False,
        "paper_trading_allowed": False,
        "paid_data_approved": False,
        "true_net_gamma_claim_allowed": False,
        "research_log_required": False,
        "current_ablation_coverage": ablation.get("coverage", {}),
        "local_cache_counts": {
            "baseline_closed_trade_dates": len(baseline_dates),
            "local_option_quote_dates": len(local_quote_dates),
            "local_spy_bar_dates": len(local_bar_dates),
            "local_oi_dates": len(local_oi_dates),
            "current_gamma_dates": len(current_gamma_dates),
            "current_baseline_gamma_intersection": len(current_intersection),
            "additional_no_paid_gamma_ready_dates": len(additional_no_paid_candidates),
            "quote_bar_cached_baseline_dates_missing_oi": len(quote_bar_only_candidates),
            "projected_no_paid_gamma_ready_intersection": projected_no_paid_count,
        },
        "current_covered_trade_dates": current_intersection,
        "additional_no_paid_candidate_dates": additional_no_paid_candidates,
        "candidate_dates_no_paid_gamma_ready": candidate_rows,
        "quote_bar_cached_but_missing_oi_dates": quote_bar_rows,
        "quote_bar_cached_but_missing_oi_date_sample": quote_bar_rows[:25],
        "regime_counts": {
            "current_intersection": _regime_counts(current_intersection, macro_by_date, vix_by_date),
            "additional_no_paid_candidates": _regime_counts(additional_no_paid_candidates, macro_by_date, vix_by_date),
            "projected_no_paid_candidates": _regime_counts(sorted(set(current_intersection) | set(additional_no_paid_candidates)), macro_by_date, vix_by_date),
            "quote_bar_cached_but_missing_oi": _regime_counts(quote_bar_only_candidates, macro_by_date, vix_by_date),
        },
        "mintrl_psr_feasibility_gate": mintrl_gate,
        "next_safe_action": next_safe_action,
        "forbidden_actions_preserved": plan.get("forbidden_actions", []),
        "tier_blockers": [
            "E0 scan only",
            "no additional no-paid gamma-ready baseline trade dates",
            "MinTRL/PSR not computable for expanded sample",
            "no strategy PnL reviewed",
            "no paid cost gate passed",
            "H-G1 remains parked",
        ],
    }
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_md_path.write_text(_markdown(report), encoding="utf-8")
    return report


def _dates_from_oi_files(root: Path) -> set[str]:
    if not root.exists():
        return set()
    dates: set[str] = set()
    for path in root.rglob("*full_utc_day_statistics.dbn.zst"):
        match = DATE_RE.search(path.name)
        if match:
            dates.add(match.group(0))
    return dates


def _macro_by_date(path: Path) -> dict[str, list[str]]:
    events: dict[str, list[str]] = defaultdict(list)
    if not path.exists():
        return events
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("importance") != "high":
                continue
            timestamp = row.get("event_timestamp_et", "")
            day = timestamp[:10]
            if DATE_RE.fullmatch(day):
                events[day].append(row.get("event_type", "UNKNOWN"))
    return dict(events)


def _vix_by_date(path: Path) -> dict[str, float]:
    values: dict[str, float] = {}
    if not path.exists():
        return values
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            day = row.get("date")
            value = row.get("vix_close")
            if isinstance(day, str) and isinstance(value, (int, float)):
                values[day] = float(value)
    return values


def _candidate_row(day: str, macro_by_date: dict[str, list[str]], vix_by_date: dict[str, float], source: str) -> dict[str, Any]:
    vix = vix_by_date.get(day)
    return {
        "date": day,
        "source": source,
        "split": _split(day),
        "volatility_bucket": _volatility_bucket(vix),
        "vix_close": vix,
        "high_importance_macro": day in macro_by_date,
        "macro_events": macro_by_date.get(day, []),
    }


def _regime_counts(days: list[str], macro_by_date: dict[str, list[str]], vix_by_date: dict[str, float]) -> dict[str, dict[str, int]]:
    split = Counter()
    macro = Counter()
    vol = Counter()
    for day in days:
        split[_split(day)] += 1
        macro["high_importance_macro" if day in macro_by_date else "no_high_importance_macro"] += 1
        vol[_volatility_bucket(vix_by_date.get(day))] += 1
    return {
        "by_split": dict(sorted(split.items())),
        "by_macro_flag": dict(sorted(macro.items())),
        "by_volatility_bucket": dict(sorted(vol.items())),
    }


def _split(day: str) -> str:
    parsed = date.fromisoformat(day)
    if parsed <= date(2023, 12, 31):
        return "train"
    return "oos"


def _volatility_bucket(vix: float | None) -> str:
    if vix is None:
        return "unknown"
    if vix < 15:
        return "low"
    if vix <= 25:
        return "normal"
    return "high"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _markdown(report: dict[str, Any]) -> str:
    counts = report["local_cache_counts"]
    mintrl = report["mintrl_psr_feasibility_gate"]
    return "\n".join(
        [
            "# H-G1 Local Cache Overlap Scan",
            "",
            f"- **Status**: `{report['status']}`",
            f"- **Evidence tier**: `{report['evidence_tier']}`",
            f"- **Conclusion**: {report['conclusion']}",
            f"- **Network used**: `{report['network_used']}`",
            f"- **Paid data used**: `{report['paid_data_used']}`",
            f"- **Strategy PnL used**: `{report['strategy_pnl_used']}`",
            f"- **Strategy use allowed**: `{report['strategy_use_allowed']}`",
            "",
            "## Counts",
            "",
            f"- Baseline closed trade dates: `{counts['baseline_closed_trade_dates']}`",
            f"- Current gamma dates: `{counts['current_gamma_dates']}`",
            f"- Current baseline/gamma intersection: `{counts['current_baseline_gamma_intersection']}`",
            f"- Additional no-paid gamma-ready dates: `{counts['additional_no_paid_gamma_ready_dates']}`",
            f"- Projected no-paid gamma-ready intersection: `{counts['projected_no_paid_gamma_ready_intersection']}`",
            f"- Quote/bar cached baseline dates missing OI: `{counts['quote_bar_cached_baseline_dates_missing_oi']}`",
            "",
            "## Current Covered Trade Dates",
            "",
            ", ".join(report["current_covered_trade_dates"]) or "None",
            "",
            "## MinTRL / PSR Gate",
            "",
            f"- **Status**: `{mintrl['status']}`",
            f"- **Reason**: {mintrl['reason']}",
            "",
            "## Next Safe Action",
            "",
            report["next_safe_action"],
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the H-G1 no-paid local-cache overlap scan.")
    parser.add_argument("--output-json-path", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md-path", type=Path, default=DEFAULT_OUTPUT_MD)
    args = parser.parse_args(argv)
    report = run_h_g1_local_cache_overlap_scan(args.output_json_path, args.output_md_path)
    print(json.dumps({"status": report["status"], "output_json": _relative(args.output_json_path), "output_md": _relative(args.output_md_path)}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
