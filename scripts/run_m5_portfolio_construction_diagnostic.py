from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import mean, pstdev
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_ROOT = PROJECT_ROOT / "reports" / "experiments"
SUMMARY_PATH = REPORT_ROOT / "m5_portfolio_construction_diagnostic_summary.json"
REPORT_PATH = REPORT_ROOT / "m5_portfolio_construction_diagnostic_report.md"
SEARCH_LOG_PATH = REPORT_ROOT / "search_logs" / "m5_portfolio_construction_diagnostic_search_log.jsonl"
COMPONENT_ROOT = REPORT_ROOT / "m5_portfolio_construction_components"
A_SUMMARY_PATH = PROJECT_ROOT / "reports" / "baselines" / "subsystem_a_orb_baseline_summary.json"
B_SUMMARY_PATH = PROJECT_ROOT / "reports" / "baselines" / "subsystem_b_put_ratio_feasibility_summary.json"

STARTING_EQUITY = 1000.0
SUBSYSTEM_B_CURRENT_ALLOCATION = 300.0
SUBSYSTEM_B_RISK_BUDGET = 20.0


def run_experiment(
    summary_path: Path = SUMMARY_PATH,
    report_path: Path = REPORT_PATH,
    search_log_path: Path = SEARCH_LOG_PATH,
) -> dict[str, Any]:
    sub_a = json.loads(A_SUMMARY_PATH.read_text(encoding="utf-8"))
    sub_b = json.loads(B_SUMMARY_PATH.read_text(encoding="utf-8"))
    sleeve_returns = {
        "subsystem_a": daily_map(sub_a["daily_pnl"]),
        "subsystem_b": daily_map(sub_b["daily_pnl"]),
    }
    fitted_weights = fit_weights(sleeve_returns)
    scenarios = default_scenarios(fitted_weights)
    rows = [evaluate_scenario(item, sleeve_returns, sub_b, index) for index, item in enumerate(scenarios, start=1)]
    write_component_summaries(rows)
    write_search_log(rows, search_log_path)
    result = aggregate_experiment(rows, sub_a, sub_b, search_log_path)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(render_report(result), encoding="utf-8")
    return result


def daily_map(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["date"]: row for row in rows}


def fit_weights(sleeves: dict[str, dict[str, dict[str, Any]]]) -> dict[str, dict[str, float]]:
    in_sample_a = split_values(sleeves["subsystem_a"], "in_sample", "return_on_starting_equity")
    in_sample_b = split_values(sleeves["subsystem_b"], "in_sample", "return_on_starting_equity")
    vol_weight = inverse_risk_weights(
        {
            "subsystem_a": pstdev(in_sample_a) if len(in_sample_a) > 1 else 0.0,
            "subsystem_b": pstdev(in_sample_b) if len(in_sample_b) > 1 else 0.0,
        }
    )
    es_weight = inverse_risk_weights(
        {
            "subsystem_a": abs(expected_shortfall(split_values(sleeves["subsystem_a"], "in_sample", "net_pnl"), 0.95) or 0.0),
            "subsystem_b": abs(expected_shortfall(split_values(sleeves["subsystem_b"], "in_sample", "net_pnl"), 0.95) or 0.0),
        }
    )
    return {"inverse_volatility": vol_weight, "inverse_es95": es_weight}


def default_scenarios(fitted_weights: dict[str, dict[str, float]]) -> list[dict[str, Any]]:
    return [
        scenario("subsystem_a_only_control", 1.0, 0.0, "control"),
        scenario("subsystem_b_only_diagnostic", 0.0, 1.0, "blocked_current_sizing"),
        scenario("equal_weight_fractional_diagnostic", 0.5, 0.5, "fractional_diagnostic"),
        scenario(
            "risk_parity_inverse_vol_in_sample",
            fitted_weights["inverse_volatility"]["subsystem_a"],
            fitted_weights["inverse_volatility"]["subsystem_b"],
            "in_sample_fitted_fractional_diagnostic",
        ),
        scenario(
            "es_parity_inverse_es95_in_sample",
            fitted_weights["inverse_es95"]["subsystem_a"],
            fitted_weights["inverse_es95"]["subsystem_b"],
            "in_sample_fitted_fractional_diagnostic",
        ),
    ]


def scenario(scenario_id: str, weight_a: float, weight_b: float, scenario_type: str) -> dict[str, Any]:
    return {
        "scenario_id": scenario_id,
        "scenario_type": scenario_type,
        "weights": {
            "subsystem_a": round(weight_a, 8),
            "subsystem_b": round(weight_b, 8),
        },
        "weight_fit_policy": "fixed_or_fit_on_in_sample_only",
        "fractional_contract_warning": weight_a not in {0.0, 1.0} or weight_b not in {0.0, 1.0},
    }


def evaluate_scenario(
    scenario_def: dict[str, Any],
    sleeves: dict[str, dict[str, dict[str, Any]]],
    sub_b_summary: dict[str, Any],
    trial_index: int,
) -> dict[str, Any]:
    daily_rows = portfolio_daily_rows(sleeves, scenario_def["weights"])
    in_sample_rows = [row for row in daily_rows if split_for_date(row["date"]) == "in_sample"]
    oos_rows = [row for row in daily_rows if split_for_date(row["date"]) == "oos"]
    feasibility = feasibility_assessment(scenario_def["weights"], sub_b_summary)
    return {
        "trial_index": trial_index,
        **scenario_def,
        "daily_count": len(daily_rows),
        "sample_adequacy": sample_adequacy_labels(len(daily_rows)),
        "metrics": metrics_for_daily_rows(daily_rows),
        "splits": {
            "in_sample": {
                "daily_count": len(in_sample_rows),
                "metrics": metrics_for_daily_rows(in_sample_rows),
                "sample_adequacy": sample_adequacy_labels(len(in_sample_rows)),
            },
            "oos": {
                "daily_count": len(oos_rows),
                "metrics": metrics_for_daily_rows(oos_rows),
                "sample_adequacy": sample_adequacy_labels(len(oos_rows)),
            },
        },
        "big_day_dependency": big_day_dependency_check(daily_rows),
        "feasibility": feasibility,
        "daily_pnl": daily_rows,
    }


def portfolio_daily_rows(sleeves: dict[str, dict[str, dict[str, Any]]], weights: dict[str, float]) -> list[dict[str, Any]]:
    dates = sorted(set(sleeves["subsystem_a"]) | set(sleeves["subsystem_b"]))
    equity = STARTING_EQUITY
    rows = []
    for day in dates:
        pnl_a = float(sleeves["subsystem_a"].get(day, {}).get("net_pnl", 0.0))
        pnl_b = float(sleeves["subsystem_b"].get(day, {}).get("net_pnl", 0.0))
        net_pnl = round((weights["subsystem_a"] * pnl_a) + (weights["subsystem_b"] * pnl_b), 2)
        row = {
            "date": day,
            "split": split_for_date(day),
            "starting_equity": round(equity, 2),
            "subsystem_a_pnl": round(weights["subsystem_a"] * pnl_a, 2),
            "subsystem_b_pnl": round(weights["subsystem_b"] * pnl_b, 2),
            "net_pnl": net_pnl,
            "ending_equity": round(equity + net_pnl, 2),
            "return_on_starting_equity": round(net_pnl / equity, 8) if equity else 0.0,
        }
        rows.append(row)
        equity = row["ending_equity"]
    return rows


def split_for_date(value: str) -> str:
    return "oos" if value >= "2024-01-01" else "in_sample"


def split_values(rows: dict[str, dict[str, Any]], split: str, key: str) -> list[float]:
    return [float(row[key]) for date_key, row in rows.items() if split_for_date(date_key) == split]


def inverse_risk_weights(risks: dict[str, float]) -> dict[str, float]:
    inverse = {key: (1.0 / value if value > 0 else 0.0) for key, value in risks.items()}
    total = sum(inverse.values())
    if total == 0:
        return {key: round(1.0 / len(risks), 8) for key in risks}
    return {key: round(value / total, 8) for key, value in inverse.items()}


def feasibility_assessment(weights: dict[str, float], sub_b_summary: dict[str, Any]) -> dict[str, Any]:
    b_weight = float(weights["subsystem_b"])
    b_allocation = round(STARTING_EQUITY * b_weight, 2)
    b_feasibility = sub_b_summary["feasibility"]
    if b_weight == 0:
        return {
            "status": "account_feasible_without_subsystem_b",
            "subsystem_b_allocation": 0.0,
            "all_subsystem_b_trades_fit_allocation": True,
            "all_subsystem_b_trades_fit_20_risk_budget": True,
            "notes": ["Sub-System B is not used in this scenario."],
        }
    all_fit_allocation = b_allocation >= float(b_feasibility["max_defined_loss"])
    all_fit_risk_budget = float(b_feasibility["max_defined_loss"]) <= SUBSYSTEM_B_RISK_BUDGET
    status = "blocked_current_sizing" if not all_fit_allocation or not all_fit_risk_budget else "account_feasible"
    return {
        "status": status,
        "subsystem_b_allocation": b_allocation,
        "subsystem_b_max_defined_loss": b_feasibility["max_defined_loss"],
        "subsystem_b_median_defined_loss": b_feasibility["median_defined_loss"],
        "subsystem_b_min_defined_loss": b_feasibility["min_defined_loss"],
        "all_subsystem_b_trades_fit_allocation": all_fit_allocation,
        "all_subsystem_b_trades_fit_20_risk_budget": all_fit_risk_budget,
        "current_project_subsystem_b_allocation": SUBSYSTEM_B_CURRENT_ALLOCATION,
        "current_project_risk_budget": SUBSYSTEM_B_RISK_BUDGET,
        "notes": [
            "Sub-System B baseline is already marked failed for current $300 allocation and $20 risk budget.",
            "Fractional portfolio weights are diagnostic only; options contracts cannot be traded fractionally.",
        ],
    }


def metrics_for_daily_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    pnls = [float(row["net_pnl"]) for row in rows]
    returns = [float(row["return_on_starting_equity"]) for row in rows]
    equity = [STARTING_EQUITY, *[float(row["ending_equity"]) for row in rows]]
    wins = [value for value in pnls if value > 0]
    losses = [value for value in pnls if value < 0]
    return {
        "day_count": len(rows),
        "total_pnl": round(sum(pnls), 2),
        "ending_equity": round(equity[-1], 2) if equity else STARTING_EQUITY,
        "average_day_pnl": round(mean(pnls), 4) if pnls else 0.0,
        "win_rate": round(len(wins) / len(pnls), 4) if pnls else 0.0,
        "payoff_ratio": round(mean(wins) / abs(mean(losses)), 4) if wins and losses else None,
        "sharpe_proxy": sharpe(returns),
        "sortino_proxy": sortino(returns),
        "max_drawdown": max_drawdown(equity),
        "es95": expected_shortfall(pnls, 0.95),
        "es99": expected_shortfall(pnls, 0.99),
        "worst_day_loss": min(pnls) if pnls else 0.0,
    }


def sharpe(returns: list[float]) -> float | None:
    if len(returns) < 2:
        return None
    sd = pstdev(returns)
    return None if sd == 0 else round(mean(returns) / sd, 6)


def sortino(returns: list[float]) -> float | None:
    downside = [value for value in returns if value < 0]
    if not downside:
        return None
    sd = pstdev(downside)
    return None if sd == 0 else round(mean(returns) / sd, 6)


def max_drawdown(equity: list[float]) -> float:
    peak = equity[0] if equity else 0.0
    max_dd = 0.0
    for value in equity:
        peak = max(peak, value)
        if peak > 0:
            max_dd = min(max_dd, (value / peak) - 1)
    return round(max_dd, 6)


def expected_shortfall(values: list[float], confidence: float) -> float | None:
    if not values:
        return None
    tail_count = max(1, math.ceil(len(values) * (1 - confidence)))
    return round(mean(sorted(values)[:tail_count]), 4)


def sample_adequacy_labels(observation_count: int) -> dict[str, Any]:
    labels = []
    if observation_count < 500:
        labels.extend(["under-sampled", "underpowered"])
    return {
        "observation_count": observation_count,
        "minimum_observation_count_prior": 500,
        "labels": labels,
        "mintrl_status": "pending_return_distribution",
        "psr_status": "pending_return_distribution",
        "power_note": "Portfolio metrics are diagnostic only until MinTRL/PSR are calculated on an acceptance-grade return distribution.",
    }


def big_day_dependency_check(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"status": "no_data"}
    remove_each_side = max(1, math.ceil(len(rows) * 0.05))
    ordered = sorted(rows, key=lambda row: float(row["net_pnl"]))
    retained = ordered[remove_each_side : len(ordered) - remove_each_side] if len(ordered) > remove_each_side * 2 else []
    return {
        "status": "pass" if retained else "insufficient_after_removal",
        "method": "remove_top_and_bottom_5pct_by_daily_net_pnl",
        "original_days": len(rows),
        "removed_each_side": remove_each_side,
        "removed_day_count": len(rows) - len(retained),
        "retained_days": len(retained),
        "original_total_pnl": round(sum(float(row["net_pnl"]) for row in rows), 2),
        "retained_total_pnl": round(sum(float(row["net_pnl"]) for row in retained), 2),
        "original_sharpe_proxy": metrics_for_daily_rows(rows)["sharpe_proxy"],
        "retained_sharpe_proxy": metrics_for_daily_rows(retained)["sharpe_proxy"],
    }


def aggregate_experiment(rows: list[dict[str, Any]], sub_a: dict[str, Any], sub_b: dict[str, Any], search_log_path: Path) -> dict[str, Any]:
    baseline = next(row for row in rows if row["scenario_id"] == "subsystem_a_only_control")
    best = max(rows, key=lambda row: row["metrics"]["total_pnl"])
    worst = min(rows, key=lambda row: row["metrics"]["total_pnl"])
    return {
        "record_type": "experiment_summary",
        "schema_version": "m5_portfolio_construction_diagnostic_v1",
        "experiment_id": "m5_portfolio_construction_diagnostic",
        "status": "complete",
        "conclusion": "ยังสรุปไม่ได้",
        "conclusion_reason": "Portfolio construction is mathematically testable, but Sub-System B is not current-sizing feasible and every blended portfolio remains under-sampled/underpowered.",
        "research_log_required": True,
        "research_log_slug": "higanbana-portfolio-construction-diagnostic-real-data",
        "methodology": {
            "scope": "Diagnostic allocation between Sub-System A ORB baseline and Sub-System B put-ratio baseline daily PnL.",
            "data_policy": "No new paid data was downloaded for this experiment.",
            "fit_policy": "Risk parity and ES parity weights are fit on in-sample returns only, then reported on OOS without OOS tuning.",
            "fractional_contract_policy": "Blended weights are fractional diagnostic portfolios only. They are not directly tradable option-contract portfolios.",
            "feasibility_policy": "Sub-System B allocation is checked against current $1,000 account, $300 Sub-System B allocation, and $20 risk budget constraints.",
        },
        "input_paths": {
            "subsystem_a": str(A_SUMMARY_PATH),
            "subsystem_b": str(B_SUMMARY_PATH),
        },
        "scenario_count": len(rows),
        "parameter_grid": {
            "scenario_ids": [row["scenario_id"] for row in rows],
            "weights": {row["scenario_id"]: row["weights"] for row in rows},
        },
        "search_log": search_log_metadata(rows, search_log_path),
        "dsr_assessment": dsr_assessment(rows),
        "baseline_scenario": compact_scenario(baseline),
        "best_diagnostic_scenario": compact_scenario(best),
        "worst_diagnostic_scenario": compact_scenario(worst),
        "subsystem_inputs": {
            "subsystem_a_conclusion": sub_a["conclusion"],
            "subsystem_a_trade_count": sub_a["metrics"]["trade_count"],
            "subsystem_b_conclusion": sub_b["conclusion"],
            "subsystem_b_trade_count": sub_b["metrics"]["trade_count"],
            "subsystem_b_feasibility": sub_b["feasibility"],
        },
        "sample_adequacy": sample_adequacy_labels(max(row["daily_count"] for row in rows)),
        "scenarios": [strip_heavy_fields(row) for row in rows],
    }


def compact_scenario(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "scenario_id": row["scenario_id"],
        "weights": row["weights"],
        "daily_count": row["daily_count"],
        "metrics": row["metrics"],
        "oos_metrics": row["splits"]["oos"]["metrics"],
        "feasibility": row["feasibility"],
    }


def strip_heavy_fields(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key != "daily_pnl"}


def write_component_summaries(rows: list[dict[str, Any]]) -> None:
    COMPONENT_ROOT.mkdir(parents=True, exist_ok=True)
    for row in rows:
        path = COMPONENT_ROOT / f"{row['scenario_id']}_summary.json"
        path.write_text(json.dumps(strip_heavy_fields(row), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_search_log(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(search_log_record(row), ensure_ascii=False, sort_keys=True) + "\n")


def search_log_record(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_type": "parameter_search_trial",
        "schema_version": "m5_search_log_v1",
        "experiment_id": "m5_portfolio_construction_diagnostic",
        "trial_index": row["trial_index"],
        "scenario_id": row["scenario_id"],
        "parameters": {
            "weights": row["weights"],
            "scenario_type": row["scenario_type"],
            "weight_fit_policy": row["weight_fit_policy"],
            "fractional_contract_warning": row["fractional_contract_warning"],
        },
        "metrics": row["metrics"],
        "oos_metrics": row["splits"]["oos"]["metrics"],
        "feasibility": row["feasibility"],
        "sample_adequacy": row["sample_adequacy"],
    }


def search_log_metadata(rows: list[dict[str, Any]], path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "record_type": "parameter_search_trial",
        "trial_count": len(rows),
        "all_trials_recorded": True,
        "selection_bias_warning": "Allocation scenarios are diagnostic. Do not select a production allocation from this under-sampled output.",
    }


def dsr_assessment(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "status": "blocked_under_sampled",
        "reason": "DSR is blocked because this is a multi-scenario allocation diagnostic, all scenarios are under-sampled, and Sub-System B is not current-sizing feasible.",
        "trial_count": len(rows),
        "selected_metric": "total_pnl",
        "required_before_acceptance": [
            "acceptance-grade daily return distribution",
            "effective number of independent allocation trials",
            "null Sharpe threshold",
            "skew/kurtosis/autocorrelation diagnostics",
            "implementable integer-contract sizing design",
        ],
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# M5.6 Portfolio Construction Diagnostic",
        "",
        "## Status",
        f"- Conclusion: {result['conclusion']}",
        f"- Reason: {result['conclusion_reason']}",
        "- Evidence type: real-data deterministic portfolio diagnostic, not an implementable allocation.",
        "- No new paid data was downloaded.",
        "",
        "## Methodology",
        "```json",
        json.dumps(result["methodology"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Search Log And DSR",
        f"- Search log: `{result['search_log']['path']}`",
        f"- Trial count: {result['search_log']['trial_count']}",
        f"- DSR status: `{result['dsr_assessment']['status']}`",
        f"- DSR reason: {result['dsr_assessment']['reason']}",
        "",
        "## Scenario Summary",
        "| Scenario | A weight | B weight | Days | Total PnL | OOS PnL | Sharpe | Sortino | MDD | ES95 | ES99 | Feasibility |",
        "|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|:--|",
    ]
    for row in result["scenarios"]:
        metrics = row["metrics"]
        oos = row["splits"]["oos"]["metrics"]
        lines.append(
            f"| `{row['scenario_id']}` | {row['weights']['subsystem_a']} | {row['weights']['subsystem_b']} | {row['daily_count']} | "
            f"{metrics['total_pnl']} | {oos['total_pnl']} | {metrics['sharpe_proxy']} | {metrics['sortino_proxy']} | "
            f"{metrics['max_drawdown']} | {metrics['es95']} | {metrics['es99']} | `{row['feasibility']['status']}` |"
        )
    lines.extend(
        [
            "",
            "## Baseline / Diagnostic Extremes",
            "```json",
            json.dumps(
                {
                    "baseline": result["baseline_scenario"],
                    "best": result["best_diagnostic_scenario"],
                    "worst": result["worst_diagnostic_scenario"],
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            "```",
            "",
            "## Interpretation",
            "- Sub-System A only remains the cleanest account-feasible diagnostic control.",
            "- Any allocation using Sub-System B is blocked for current sizing unless the strategy template, capital, or risk budget changes.",
            "- Risk parity and ES parity are fit on in-sample only, but they still use fractional option exposure and are not directly tradable.",
            "- Portfolio allocation cannot rescue a failed Sub-System B template without solving the underlying sizing and edge problems first.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run M5.6 portfolio construction diagnostics from Sub-System A/B baseline daily PnL.")
    parser.add_argument("--summary-path", type=Path, default=SUMMARY_PATH)
    parser.add_argument("--report-path", type=Path, default=REPORT_PATH)
    parser.add_argument("--search-log-path", type=Path, default=SEARCH_LOG_PATH)
    args = parser.parse_args(argv)
    result = run_experiment(args.summary_path, args.report_path, args.search_log_path)
    print(json.dumps({key: value for key, value in result.items() if key != "scenarios"}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
