from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_ROOT = PROJECT_ROOT / "reports" / "experiments"
SOURCE_SUMMARY = REPORT_ROOT / "m5_regime_filter_sensitivity_summary.json"
SOURCE_SEARCH_LOG = REPORT_ROOT / "search_logs" / "m5_regime_filter_sensitivity_search_log.jsonl"
SUMMARY_PATH = REPORT_ROOT / "h_a2_macro_conditioned_reanalysis_summary.json"
REPORT_PATH = REPORT_ROOT / "h_a2_macro_conditioned_reanalysis_report.md"


def run_reanalysis(
    source_summary_path: Path = SOURCE_SUMMARY,
    source_search_log_path: Path = SOURCE_SEARCH_LOG,
    summary_path: Path = SUMMARY_PATH,
    report_path: Path = REPORT_PATH,
) -> dict[str, Any]:
    source = _load_json(source_summary_path)
    search_trials = _load_jsonl(source_search_log_path)
    baseline = source["baseline_scenario"]
    high_importance = _scenario_by_id(source, "exclude_high_importance_macro_same_day")
    major_macro = _scenario_by_id(source, "exclude_major_macro_same_day")

    result = {
        "record_type": "experiment_summary",
        "schema_version": "h_a2_macro_conditioned_reanalysis_v1",
        "experiment_id": "h_a2_macro_conditioned_reanalysis",
        "hypothesis_id": "H-A2",
        "evidence_tier": "E1",
        "tier_blockers": [
            "under-sampled",
            "underpowered",
            "inherited_9_trial_search_contamination",
            "dsr_blocked_until_acceptance_grade_return_distribution",
            "missing_reference_pre_break_coverage",
            "missing_high_vix_trade_coverage",
        ],
        "research_log_required": True,
        "research_log_slug": "higanbana-macro-conditioned-orb-reanalysis",
        "status": "complete",
        "conclusion": "ยังสรุปไม่ได้",
        "conclusion_reason": (
            "Existing M5.5 evidence supports H-A2 only as a diagnostic clue: excluding high-importance macro days improved "
            "current implementable PnL and OOS PnL, but the result inherits a 9-trial search, remains under-sampled/underpowered, "
            "and cannot be treated as E2 acceptance evidence."
        ),
        "source_artifacts": {
            "summary": _relative(source_summary_path),
            "search_log": _relative(source_search_log_path),
        },
        "no_new_paid_data": True,
        "source_trial_count": len(search_trials),
        "search_contamination": {
            "inherited_trial_count": source.get("search_log", {}).get("trial_count", len(search_trials)),
            "all_trials_recorded": source.get("search_log", {}).get("all_trials_recorded", False),
            "selection_policy": source.get("methodology", {}).get("selection_policy"),
            "selected_metric_in_source": source.get("dsr_assessment", {}).get("selected_metric"),
            "dsr_status": "blocked",
            "dsr_reason": (
                "The candidate macro filter was identified inside the M5.5 9-trial diagnostic grid. "
                "DSR cannot be used as acceptance evidence until a fresh/pre-registered return distribution, "
                "effective independent trial count, null Sharpe threshold, skew/kurtosis, and autocorrelation diagnostics exist."
            ),
        },
        "scenario_comparison": {
            "baseline": _compact(baseline),
            "exclude_high_importance_macro_same_day": _compact(high_importance),
            "exclude_major_macro_same_day": _compact(major_macro),
            "deltas_vs_baseline": {
                "exclude_high_importance_macro_same_day": _deltas(high_importance, baseline),
                "exclude_major_macro_same_day": _deltas(major_macro, baseline),
            },
        },
        "h_a2_interpretation": {
            "diagnostic_supporting_points": [
                "High-importance macro exclusion retained 64 closed trades and improved total implementable PnL versus the unfiltered control.",
                "The same scenario improved OOS implementable PnL from negative to positive on current cached data.",
                "The rule is ex-ante because scheduled macro event dates are known before entry.",
            ],
            "reasons_not_acceptance_grade": [
                "The rule was selected after inspecting a 9-trial grid.",
                "The retained sample has only 64 closed trades overall and 34 OOS closed trades.",
                "The source report labels all scenarios under-sampled and underpowered.",
                "Reference/pre-break coverage and high-VIX coverage remain missing.",
            ],
            "evidence_would_overturn_h_a2": [
                "Fresh retained no-macro trades have implementable PnL <= 0 after reaching MinTRL_falsify.",
                "Macro-day exclusion stops improving risk-adjusted results after DSR accounting and untouched validation data.",
                "The apparent effect is explained by one or two extreme days and fails the big-day dependency check in fresh data.",
            ],
        },
        "next_actions": [
            "Run H-A2.3 to investigate whether the cached Aug 2024 high-VIX window has a labeling gap or genuine ORB silence.",
            "Only after H-A2.3, decide whether estimating 2022 H2 top VIX months is justified.",
            "Do not claim E2 or operational validation from this re-analysis.",
        ],
    }

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(render_report(result), encoding="utf-8")
    return result


def render_report(result: dict[str, Any]) -> str:
    comparison = result["scenario_comparison"]
    lines = [
        "# H-A2 Macro-Conditioned ORB Re-Analysis",
        "",
        "## Status",
        f"- Hypothesis: `{result['hypothesis_id']}`",
        f"- Evidence tier: `{result['evidence_tier']}`",
        f"- Conclusion: {result['conclusion']}",
        f"- Reason: {result['conclusion_reason']}",
        f"- No new paid data: `{result['no_new_paid_data']}`",
        "",
        "## Source Artifacts",
        f"- Source summary: `{result['source_artifacts']['summary']}`",
        f"- Source search log: `{result['source_artifacts']['search_log']}`",
        "",
        "## Scenario Comparison",
        "| Scenario | Closed trades | Total PnL | OOS PnL | Sharpe proxy | OOS Sharpe proxy | Cost drag | ES95 | Max drawdown |",
        "|:--|--:|--:|--:|--:|--:|--:|--:|--:|",
    ]
    for key in ("baseline", "exclude_high_importance_macro_same_day", "exclude_major_macro_same_day"):
        row = comparison[key]
        lines.append(
            f"| `{key}` | {row['closed_trades']} | {row['total_implementable_pnl']} | {row['oos_implementable_pnl']} | "
            f"{row['sharpe_proxy']} | {row['oos_sharpe_proxy']} | {row['total_cost_drag']} | {row['es95']} | {row['max_drawdown']} |"
        )
    lines.extend(
        [
            "",
            "## Delta Versus Baseline",
            "| Scenario | Closed-trade delta | Total PnL delta | OOS PnL delta | Sharpe delta | OOS Sharpe delta |",
            "|:--|--:|--:|--:|--:|--:|",
        ]
    )
    for key, row in comparison["deltas_vs_baseline"].items():
        lines.append(
            f"| `{key}` | {row['closed_trade_delta']} | {row['total_implementable_pnl_delta']} | "
            f"{row['oos_implementable_pnl_delta']} | {row['sharpe_proxy_delta']} | {row['oos_sharpe_proxy_delta']} |"
        )
    lines.extend(
        [
            "",
            "## Search Contamination And DSR",
            f"- Inherited trial count: {result['search_contamination']['inherited_trial_count']}",
            f"- All trials recorded: `{result['search_contamination']['all_trials_recorded']}`",
            f"- DSR status: `{result['search_contamination']['dsr_status']}`",
            f"- DSR reason: {result['search_contamination']['dsr_reason']}",
            "",
            "## Tier Blockers",
        ]
    )
    lines.extend(f"- `{item}`" for item in result["tier_blockers"])
    lines.extend(["", "## Interpretation"])
    lines.extend(f"- {item}" for item in result["h_a2_interpretation"]["diagnostic_supporting_points"])
    lines.extend(["", "## Why This Is Not Acceptance Evidence"])
    lines.extend(f"- {item}" for item in result["h_a2_interpretation"]["reasons_not_acceptance_grade"])
    lines.extend(["", "## Next Actions"])
    lines.extend(f"{index}. {item}" for index, item in enumerate(result["next_actions"], start=1))
    lines.append("")
    return "\n".join(lines)


def _scenario_by_id(source: dict[str, Any], scenario_id: str) -> dict[str, Any]:
    for key in ("baseline_scenario", "best_diagnostic_scenario", "worst_diagnostic_scenario"):
        row = source.get(key, {})
        if row.get("scenario_id") == scenario_id:
            return row
    for row in source.get("scenarios", []):
        if row.get("scenario_id") == scenario_id:
            return row
    raise ValueError(f"Scenario not found: {scenario_id}")


def _compact(row: dict[str, Any]) -> dict[str, Any]:
    metrics = row["metrics"]
    oos = row.get("oos_metrics") or row.get("splits", {}).get("oos", {}).get("metrics", {})
    return {
        "scenario_id": row["scenario_id"],
        "closed_trades": row["closed_trades"],
        "filtered_out_trades": row["filtered_out_trades"],
        "total_implementable_pnl": metrics["total_implementable_pnl"],
        "oos_implementable_pnl": oos.get("total_implementable_pnl"),
        "sharpe_proxy": metrics["sharpe_proxy"],
        "oos_sharpe_proxy": oos.get("sharpe_proxy"),
        "sortino_proxy": metrics["sortino_proxy"],
        "total_cost_drag": metrics["total_cost_drag"],
        "es95": metrics["es95"],
        "max_drawdown": metrics["max_drawdown"],
    }


def _deltas(row: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    left = _compact(row)
    right = _compact(baseline)
    return {
        "closed_trade_delta": left["closed_trades"] - right["closed_trades"],
        "total_implementable_pnl_delta": round(left["total_implementable_pnl"] - right["total_implementable_pnl"], 6),
        "oos_implementable_pnl_delta": round(left["oos_implementable_pnl"] - right["oos_implementable_pnl"], 6),
        "sharpe_proxy_delta": round(left["sharpe_proxy"] - right["sharpe_proxy"], 6),
        "oos_sharpe_proxy_delta": round(left["oos_sharpe_proxy"] - right["oos_sharpe_proxy"], 6),
    }


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Re-analyze existing M5.5 evidence under H-A2 without new data.")
    parser.add_argument("--source-summary-path", type=Path, default=SOURCE_SUMMARY)
    parser.add_argument("--source-search-log-path", type=Path, default=SOURCE_SEARCH_LOG)
    parser.add_argument("--summary-path", type=Path, default=SUMMARY_PATH)
    parser.add_argument("--report-path", type=Path, default=REPORT_PATH)
    args = parser.parse_args(argv)

    result = run_reanalysis(
        source_summary_path=args.source_summary_path,
        source_search_log_path=args.source_search_log_path,
        summary_path=args.summary_path,
        report_path=args.report_path,
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "hypothesis_id": result["hypothesis_id"],
                "evidence_tier": result["evidence_tier"],
                "conclusion": result["conclusion"],
                "tier_blockers": result["tier_blockers"],
                "summary_path": _relative(args.summary_path),
                "report_path": _relative(args.report_path),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
