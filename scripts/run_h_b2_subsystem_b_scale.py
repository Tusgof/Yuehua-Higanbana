from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, pstdev
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
import run_m4_subsystem_b_feasibility as m4_b
from validate_h_b2_preregistration import DEFAULT_MANIFEST_PATH, validate_h_b2_preregistration


def run_h_b2_scale(
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    summary_path: Path | None = None,
    report_path: Path | None = None,
    search_log_path: Path | None = None,
) -> dict[str, Any]:
    validation = validate_h_b2_preregistration(manifest_path)
    if validation["status"] != "pass":
        raise ValueError("H-B2 pre-registration is blocked: " + ", ".join(validation["blockers"]))

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    output_paths = manifest["output_paths"]
    summary_path = summary_path or PROJECT_ROOT / output_paths["summary"]
    report_path = report_path or PROJECT_ROOT / output_paths["report"]
    search_log_path = search_log_path or PROJECT_ROOT / output_paths["search_log"]

    wing_gaps = manifest["strategy_template"]["protective_wing_gap_grid_usd"]
    account_sizes = manifest["account_sizes_usd"]
    risk_fraction = manifest["capital_rule"]["account_risk_fraction"]

    day_contexts = _load_day_contexts()
    wing_days = {float(gap): _run_wing_gap(day_contexts, float(gap)) for gap in wing_gaps}
    scenarios = []
    search_log = []
    for gap in wing_gaps:
        closed = [day for day in wing_days[float(gap)] if day["status"] == "closed_forced_1545"]
        for account_size in account_sizes:
            scenario = _scenario_summary(float(account_size), risk_fraction, float(gap), closed)
            scenarios.append(scenario)
            search_log.append(_search_log_row(scenario))

    summary = _summary(manifest, validation, scenarios, wing_days)
    _write_json(summary_path, summary)
    _write_json(search_log_path, search_log)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(_render_report(summary), encoding="utf-8")
    return summary


def _load_day_contexts() -> list[dict[str, Any]]:
    contexts: list[dict[str, Any]] = []
    for label, split, normalized_name in m4_b.DATASETS:
        normalized_root = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "databento" / normalized_name
        bars = m4_b.load_bars_by_date(normalized_root / "spy_bar.jsonl")
        snapshots = m4_b.load_put_snapshots(normalized_root / "option_quote.jsonl")
        for trade_date in sorted(bars):
            contexts.append(
                {
                    "label": label,
                    "split": split,
                    "trade_date": trade_date,
                    "bars": bars[trade_date],
                    "snapshots": snapshots.get(trade_date, {}),
                }
            )
    return contexts


def _run_wing_gap(day_contexts: list[dict[str, Any]], wing_gap: float) -> list[dict[str, Any]]:
    days: list[dict[str, Any]] = []
    for context in day_contexts:
        days.append(
            _evaluate_day(
                context["label"],
                context["split"],
                context["trade_date"],
                context["bars"],
                context["snapshots"],
                wing_gap,
            )
        )
    return days


def _evaluate_day(
    dataset: str,
    split: str,
    trade_date: str,
    bars: list[dict[str, Any]],
    snapshots: dict[str, dict[float, dict[str, Any]]],
    wing_gap: float,
) -> dict[str, Any]:
    entry_bar = m4_b.nearest_bar_at_or_before(bars, m4_b.ENTRY_TARGET)
    result: dict[str, Any] = {"date": trade_date, "dataset": dataset, "split": split, "status": "unknown", "reasons": []}
    if entry_bar is None:
        result.update(status="missing_underlying_1000", reasons=["missing SPY 10:00 ET bar"])
        return result

    entry_timestamp = m4_b.choose_entry_timestamp(snapshots)
    close_timestamp = m4_b.choose_close_timestamp(snapshots)
    if entry_timestamp is None:
        result.update(status="missing_entry_quotes", reasons=["missing put snapshot between 09:55 and 10:00 ET"])
        return result
    if close_timestamp is None:
        result.update(status="missing_close_quotes", reasons=["missing put snapshot near forced close 15:45 ET"])
        return result

    entry_quotes = list(snapshots[entry_timestamp].values())
    try:
        legs = select_capped_put_ratio_legs(entry_quotes, float(entry_bar["close"]), wing_gap)
    except m4_b.SubsystemBFeasibilityError as exc:
        result.update(
            status="structure_unavailable",
            underlying_1000=float(entry_bar["close"]),
            entry_timestamp_et=entry_timestamp,
            close_timestamp_et=close_timestamp,
            protective_wing_gap=wing_gap,
            reasons=[str(exc)],
        )
        return result

    close_quotes = snapshots[close_timestamp]
    missing_close = [m4_b.leg_key(leg) for leg in legs if float(leg["strike"]) not in close_quotes]
    if missing_close:
        result.update(
            status="missing_leg_close_quotes",
            underlying_1000=float(entry_bar["close"]),
            entry_timestamp_et=entry_timestamp,
            close_timestamp_et=close_timestamp,
            protective_wing_gap=wing_gap,
            legs=legs,
            reasons=["missing close quotes: " + ", ".join(missing_close)],
        )
        return result

    entry_by_strike = snapshots[entry_timestamp]
    mid_pnl = m4_b.strategy_pnl(legs, entry_by_strike, close_quotes, "mid", include_fees=False)
    gross_pnl = m4_b.strategy_pnl(legs, entry_by_strike, close_quotes, "implementable", include_fees=False)
    fees = round(sum(leg["quantity"] for leg in legs) * m4_b.FEE_PER_CONTRACT * 2, 2)
    implementable_pnl = round(gross_pnl - fees, 2)
    entry_cashflow = m4_b.opening_cashflow(legs, entry_by_strike, "implementable")
    max_loss = m4_b.max_defined_loss(legs, entry_cashflow)
    result.update(
        {
            "status": "closed_forced_1545",
            "underlying_1000": float(entry_bar["close"]),
            "entry_timestamp_et": entry_timestamp,
            "close_timestamp_et": close_timestamp,
            "protective_wing_gap": wing_gap,
            "legs": legs,
            "entry_cashflow": round(entry_cashflow, 4),
            "max_defined_loss": max_loss,
            "mid_pnl": mid_pnl,
            "gross_pnl": gross_pnl,
            "fees": fees,
            "implementable_pnl": implementable_pnl,
            "net_pnl": implementable_pnl,
            "cost_drag": round(mid_pnl - implementable_pnl, 2),
            "reasons": [
                "entry uses nearest put snapshot at or before 10:00 ET",
                "exit uses forced close snapshot nearest 15:45 ET",
                f"protective wing must be at least ${wing_gap:g} below short strike when available",
            ],
        }
    )
    return result


def select_capped_put_ratio_legs(
    put_quotes: list[dict[str, Any]],
    underlying_price: float,
    wing_gap: float,
) -> list[dict[str, Any]]:
    puts = sorted([quote for quote in put_quotes if quote["right"] == "put"], key=lambda quote: float(quote["strike"]))
    if len(puts) < 3:
        raise m4_b.SubsystemBFeasibilityError("not enough put strikes")
    near = min(puts, key=lambda quote: abs(float(quote["strike"]) - underlying_price * m4_b.NEAR_MONEYNESS))
    short_target = underlying_price * m4_b.SHORT_MONEYNESS
    short_candidates = [
        quote for quote in puts if float(quote["strike"]) < float(near["strike"]) and float(quote["strike"]) <= short_target
    ]
    if not short_candidates:
        raise m4_b.SubsystemBFeasibilityError("no short put below 0.99 moneyness target")
    short = max(short_candidates, key=lambda quote: float(quote["strike"]))
    wing_target = float(short["strike"]) - wing_gap
    wing_candidates = [quote for quote in puts if float(quote["strike"]) < float(short["strike"]) and float(quote["strike"]) <= wing_target]
    if not wing_candidates:
        raise m4_b.SubsystemBFeasibilityError(f"no protective wing at least ${wing_gap:g} below short strike")
    wing = max(wing_candidates, key=lambda quote: float(quote["strike"]))
    return [
        m4_b.make_leg("sub_b_long_near", near, "buy", 1),
        m4_b.make_leg("sub_b_short_ratio", short, "sell", 2),
        m4_b.make_leg("sub_b_long_wing", wing, "buy", 1),
    ]


def _scenario_summary(account_size: float, risk_fraction: float, wing_gap: float, closed: list[dict[str, Any]]) -> dict[str, Any]:
    risk_budget = round(account_size * risk_fraction, 2)
    eligible = [day for day in closed if float(day["max_defined_loss"]) <= risk_budget]
    return {
        "scenario_id": f"account_{int(account_size)}_wing_{_gap_slug(wing_gap)}",
        "account_size_usd": account_size,
        "risk_fraction": risk_fraction,
        "risk_budget_usd": risk_budget,
        "protective_wing_gap_usd": wing_gap,
        "closed_candidates": len(closed),
        "eligible_trades": len(eligible),
        "ineligible_trades": len(closed) - len(eligible),
        "metrics": _metrics_for_closed_days(eligible, account_size),
        "splits": {split: _split_summary(split, eligible, account_size) for split in ("in_sample", "oos")},
        "sample_adequacy": m4_b.sample_adequacy_labels(len(eligible)),
        "big_day_dependency": m4_b.big_day_dependency_check(eligible),
        "feasibility": _feasibility_summary(closed, eligible, risk_budget),
        "daily_pnl": _daily_pnl_rows(eligible, account_size),
    }


def _metrics_for_closed_days(closed: list[dict[str, Any]], account_size: float) -> dict[str, Any]:
    pnls = [float(day["implementable_pnl"]) for day in closed]
    mid_pnls = [float(day["mid_pnl"]) for day in closed]
    daily_rows = _daily_pnl_rows(closed, account_size)
    daily_values = [row["net_pnl"] for row in daily_rows]
    returns = [row["return_on_starting_equity"] for row in daily_rows]
    wins = [pnl for pnl in pnls if pnl > 0]
    losses = [pnl for pnl in pnls if pnl < 0]
    total_mid = round(sum(mid_pnls), 2)
    total_implementable = round(sum(pnls), 2)
    total_cost_drag = round(sum(day.get("cost_drag", 0.0) for day in closed), 2)
    return {
        "trade_count": len(closed),
        "total_mid_pnl": total_mid,
        "total_implementable_pnl": total_implementable,
        "total_cost_drag": total_cost_drag,
        "friction_drag_ratio": round(total_cost_drag / abs(total_mid), 6) if total_mid else None,
        "average_trade_pnl": round(mean(pnls), 4) if pnls else 0.0,
        "win_rate": round(len(wins) / len(pnls), 4) if pnls else 0.0,
        "payoff_ratio": round(mean(wins) / abs(mean(losses)), 4) if wins and losses else None,
        "sharpe_proxy": _sharpe(returns),
        "sortino_proxy": _sortino(returns),
        "max_drawdown": _max_drawdown([account_size, *[row["ending_equity"] for row in daily_rows]]),
        "es95": _expected_shortfall(daily_values, 0.95),
        "es99": _expected_shortfall(daily_values, 0.99),
        "worst_day_loss": min(daily_values) if daily_values else 0.0,
    }


def _split_summary(split: str, closed: list[dict[str, Any]], account_size: float) -> dict[str, Any]:
    split_closed = [day for day in closed if day["split"] == split]
    return {
        "trade_count": len(split_closed),
        "coverage_start": min((day["date"] for day in split_closed), default=None),
        "coverage_end": max((day["date"] for day in split_closed), default=None),
        "metrics": _metrics_for_closed_days(split_closed, account_size),
        "sample_adequacy": m4_b.sample_adequacy_labels(len(split_closed)),
    }


def _feasibility_summary(closed: list[dict[str, Any]], eligible: list[dict[str, Any]], risk_budget: float) -> dict[str, Any]:
    losses = [float(day["max_defined_loss"]) for day in closed]
    eligible_losses = [float(day["max_defined_loss"]) for day in eligible]
    return {
        "risk_budget_usd": risk_budget,
        "candidate_count": len(closed),
        "eligible_count": len(eligible),
        "eligible_rate": round(len(eligible) / len(closed), 6) if closed else 0.0,
        "min_defined_loss": round(min(losses), 2) if losses else None,
        "median_defined_loss": round(sorted(losses)[len(losses) // 2], 2) if losses else None,
        "max_defined_loss": round(max(losses), 2) if losses else None,
        "max_eligible_defined_loss": round(max(eligible_losses), 2) if eligible_losses else None,
    }


def _daily_pnl_rows(closed: list[dict[str, Any]], account_size: float) -> list[dict[str, Any]]:
    by_date: dict[str, float] = defaultdict(float)
    for day in closed:
        by_date[day["date"]] += float(day["implementable_pnl"])
    equity = account_size
    rows = []
    for trade_date in sorted(by_date):
        pnl = round(by_date[trade_date], 2)
        rows.append(
            {
                "date": trade_date,
                "starting_equity": round(equity, 2),
                "net_pnl": pnl,
                "ending_equity": round(equity + pnl, 2),
                "return_on_starting_equity": round(pnl / equity, 8) if equity else 0.0,
            }
        )
        equity = rows[-1]["ending_equity"]
    return rows


def _summary(
    manifest: dict[str, Any],
    validation: dict[str, Any],
    scenarios: list[dict[str, Any]],
    wing_days: dict[float, list[dict[str, Any]]],
) -> dict[str, Any]:
    positive_total_and_oos = [
        scenario["scenario_id"]
        for scenario in scenarios
        if scenario["metrics"]["total_implementable_pnl"] > 0
        and scenario["splits"]["oos"]["metrics"]["total_implementable_pnl"] > 0
    ]
    all_cost_drag_high_when_mid_positive = all(
        (
            scenario["metrics"]["total_mid_pnl"] <= 0
            or (
                scenario["metrics"]["friction_drag_ratio"] is not None
                and scenario["metrics"]["friction_drag_ratio"] >= 0.60
            )
        )
        for scenario in scenarios
    )
    conclusion = "ยังสรุปไม่ได้" if positive_total_and_oos else "ยังสรุปไม่ได้"
    recommendation = "keep_active_for_review" if positive_total_and_oos else "consider_falsification_after_mintrl_falsify_review"
    return {
        "record_type": "experiment_summary",
        "schema_version": "h_b2_subsystem_b_scale_v1",
        "experiment_id": "h_b2_subsystem_b_scale",
        "hypothesis_id": "H-B2",
        "evidence_tier": "E1",
        "tier_blockers": [
            "sample_adequacy_pending_mintrl_falsify",
            "grid_search_requires_dsr_or_fresh_validation_before_acceptance",
            "no_deployment_claim_allowed_from_simulated_scale_diagnostic",
        ],
        "status": "complete",
        "conclusion": conclusion,
        "recommendation": recommendation,
        "research_log_required": True,
        "research_log_slug": "higanbana-subsystem-b-scale-diagnostic",
        "preregistration": {
            "manifest_path": validation["manifest_path"],
            "validation_status": validation["status"],
            "registered_at": manifest["registered_at"],
            "trial_count": manifest["search_control"]["independent_trial_count"],
        },
        "methodology": {
            "data_policy": manifest["data_policy"],
            "capital_rule": manifest["capital_rule"],
            "chronological_policy": manifest["chronological_policy"],
            "entry_exit_policy": manifest["entry_exit_policy"],
            "strategy_template": manifest["strategy_template"],
        },
        "decision_rule": manifest["decision_rule"],
        "search_control": manifest["search_control"],
        "diagnostics": {
            "positive_total_and_oos_scenarios": positive_total_and_oos,
            "all_cost_drag_high_when_mid_positive": all_cost_drag_high_when_mid_positive,
            "wing_status_counts": {
                str(gap): dict(Counter(day["status"] for day in days)) for gap, days in sorted(wing_days.items())
            },
        },
        "scenarios": scenarios,
    }


def _search_log_row(scenario: dict[str, Any]) -> dict[str, Any]:
    metrics = scenario["metrics"]
    oos_metrics = scenario["splits"]["oos"]["metrics"]
    return {
        "scenario_id": scenario["scenario_id"],
        "account_size_usd": scenario["account_size_usd"],
        "protective_wing_gap_usd": scenario["protective_wing_gap_usd"],
        "risk_budget_usd": scenario["risk_budget_usd"],
        "eligible_trades": scenario["eligible_trades"],
        "total_implementable_pnl": metrics["total_implementable_pnl"],
        "oos_implementable_pnl": oos_metrics["total_implementable_pnl"],
        "total_mid_pnl": metrics["total_mid_pnl"],
        "total_cost_drag": metrics["total_cost_drag"],
        "friction_drag_ratio": metrics["friction_drag_ratio"],
        "es95": metrics["es95"],
        "max_drawdown": metrics["max_drawdown"],
        "sample_labels": scenario["sample_adequacy"]["labels"],
        "selected_for_deployment": False,
    }


def _render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# H-B2 Sub-System B Simulated-Scale Diagnostic",
        "",
        "## Status",
        f"- Hypothesis: `{summary['hypothesis_id']}`",
        f"- Evidence tier: `{summary['evidence_tier']}`",
        f"- Conclusion: {summary['conclusion']}",
        f"- Recommendation: `{summary['recommendation']}`",
        "- No new paid data was used.",
        "- This report does not allow deployment or paper-trading edge claims.",
        "",
        "## Pre-Registration",
        "```json",
        json.dumps(summary["preregistration"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Scenario Results",
        "",
        "| Scenario | Account | Wing | Eligible | Total PnL | OOS PnL | Mid PnL | Cost Drag | Drag Ratio | ES95 | MDD | Labels |",
        "|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|:--|",
    ]
    for scenario in summary["scenarios"]:
        metrics = scenario["metrics"]
        oos_metrics = scenario["splits"]["oos"]["metrics"]
        labels = ", ".join(scenario["sample_adequacy"]["labels"])
        lines.append(
            f"| `{scenario['scenario_id']}` | {scenario['account_size_usd']:.0f} | {scenario['protective_wing_gap_usd']:.0f} | "
            f"{scenario['eligible_trades']} | {metrics['total_implementable_pnl']} | {oos_metrics['total_implementable_pnl']} | "
            f"{metrics['total_mid_pnl']} | {metrics['total_cost_drag']} | {metrics['friction_drag_ratio']} | "
            f"{metrics['es95']} | {metrics['max_drawdown']} | {labels} |"
        )
    lines.extend(
        [
            "",
            "## Tier Blockers",
            "",
            *[f"- `{blocker}`" for blocker in summary["tier_blockers"]],
            "",
            "## Diagnostics",
            "```json",
            json.dumps(summary["diagnostics"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
        ]
    )
    return "\n".join(lines) + "\n"


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _gap_slug(gap: float) -> str:
    return str(int(gap)) if gap.is_integer() else str(gap).replace(".", "_")


def _sharpe(returns: list[float]) -> float | None:
    if len(returns) < 2:
        return None
    sd = pstdev(returns)
    return None if sd == 0 else round(mean(returns) / sd, 6)


def _sortino(returns: list[float]) -> float | None:
    downside = [value for value in returns if value < 0]
    if not downside:
        return None
    sd = pstdev(downside)
    return None if sd == 0 else round(mean(returns) / sd, 6)


def _max_drawdown(equity: list[float]) -> float:
    peak = equity[0] if equity else 0.0
    max_dd = 0.0
    for value in equity:
        peak = max(peak, value)
        if peak > 0:
            max_dd = min(max_dd, (value / peak) - 1)
    return round(max_dd, 6)


def _expected_shortfall(values: list[float], confidence: float) -> float | None:
    if not values:
        return None
    tail_count = max(1, math.ceil(len(values) * (1 - confidence)))
    return round(mean(sorted(values)[:tail_count]), 4)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run H-B2 Sub-System B simulated-scale diagnostic using cached data.")
    parser.add_argument("--manifest-path", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--summary-path", type=Path)
    parser.add_argument("--report-path", type=Path)
    parser.add_argument("--search-log-path", type=Path)
    args = parser.parse_args(argv)
    summary = run_h_b2_scale(args.manifest_path, args.summary_path, args.report_path, args.search_log_path)
    printable = {key: value for key, value in summary.items() if key != "scenarios"}
    print(json.dumps(printable, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
