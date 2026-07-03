from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, time
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from run_jan2024_pilot_adapter import is_rth
from run_jan2024_pilot_pnl import evaluate_candidate_day, index_quotes, load_jsonl, sample_adequacy_labels, summarize_pnl
from run_m4_subsystem_a_baseline import DATASETS as SUBSYSTEM_A_DATASETS
from run_m4_subsystem_a_baseline import benchmark_for_bars, daily_pnl_rows, metrics_for_closed_trades
from run_m4_subsystem_b_feasibility import (
    CLOSE_TARGET,
    FEE_PER_CONTRACT,
    RISK_BUDGET,
    STARTING_EQUITY,
    SUBSYSTEM_B_ALLOCATION,
    choose_close_timestamp,
    daily_pnl_rows as subsystem_b_daily_pnl_rows,
    load_bars_by_date,
    max_defined_loss,
    metrics_for_closed_days,
    opening_cashflow,
    select_capped_put_ratio_legs,
    strategy_pnl,
)
from strategy_spec_m4 import StrategySpecError, compute_orb_signal, construct_subsystem_a_vertical


REPORT_ROOT = PROJECT_ROOT / "reports" / "experiments"
SUMMARY_PATH = REPORT_ROOT / "m5_entry_timing_sensitivity_summary.json"
REPORT_PATH = REPORT_ROOT / "m5_entry_timing_sensitivity_report.md"
SEARCH_LOG_PATH = REPORT_ROOT / "search_logs" / "m5_entry_timing_sensitivity_search_log.jsonl"
COMPONENT_ROOT = REPORT_ROOT / "m5_entry_timing_components"

SUBSYSTEM_B_DATASETS = [(label, split, normalized_name) for label, split, _adapter_name, normalized_name in SUBSYSTEM_A_DATASETS]
ENTRY_TIMES_A = ["09:35:00", "09:36:00", "09:37:00", "09:38:00", "09:39:00", "10:00:00"]
ENTRY_TIMES_B = ["09:55:00", "09:56:00", "09:57:00", "09:58:00", "09:59:00", "10:00:00"]
FILL_MODEL = "half_spread"
CLOSE_FALLBACK = "nearest_1545_window"
EXIT_MODEL = "forced_close_only"


def default_scenarios() -> list[dict[str, Any]]:
    rows = [
        scenario("sub_a", f"sub_a_orb_breakout_{time_id(item)}", item, "orb_breakout_time")
        for item in ENTRY_TIMES_A
    ]
    rows.extend(
        scenario("sub_b", f"sub_b_put_ratio_entry_{time_id(item)}", item, "entry_snapshot_time")
        for item in ENTRY_TIMES_B
    )
    return rows


def scenario(subsystem: str, scenario_id: str, entry_time: str, timing_axis: str) -> dict[str, Any]:
    return {
        "subsystem": subsystem,
        "scenario_id": scenario_id,
        "entry_time": entry_time,
        "timing_axis": timing_axis,
        "fill_model": FILL_MODEL,
        "fee_per_contract": FEE_PER_CONTRACT,
        "close_fallback": CLOSE_FALLBACK,
        "exit_model": EXIT_MODEL,
    }


def run_experiment(
    summary_path: Path = SUMMARY_PATH,
    report_path: Path = REPORT_PATH,
    search_log_path: Path = SEARCH_LOG_PATH,
) -> dict[str, Any]:
    scenarios = default_scenarios()
    scenario_datasets: dict[str, list[dict[str, Any]]] = {item["scenario_id"]: [] for item in scenarios}
    scenario_by_id = {item["scenario_id"]: item for item in scenarios}
    sub_a_scenarios = [item for item in scenarios if item["subsystem"] == "sub_a"]
    sub_b_scenarios = [item for item in scenarios if item["subsystem"] == "sub_b"]

    for label, split, _adapter_name, normalized_name in SUBSYSTEM_A_DATASETS:
        normalized_root = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "databento" / normalized_name
        bar_path = normalized_root / "spy_bar.jsonl"
        quote_path = normalized_root / "option_quote.jsonl"
        bars = load_jsonl(bar_path)
        quotes = load_jsonl(quote_path)
        bars_by_date = group_by_date(bars, "timestamp_et")
        quotes_by_key = index_quotes(quotes)
        quotes_by_timestamp = group_by_date_and_timestamp(quotes, "quote_timestamp_et")
        put_snapshots = put_snapshots_from_quotes(quotes, ENTRY_TIMES_B)

        for item in sub_a_scenarios:
            rows = []
            for trade_date in sorted(bars_by_date):
                day = build_subsystem_a_day(trade_date, bars_by_date[trade_date], quotes_by_timestamp.get(trade_date, {}), item["entry_time"])
                if day["status"] == "candidate_ready":
                    rows.append(
                        evaluate_candidate_day(
                            day,
                            quotes_by_key,
                            item["fee_per_contract"],
                            item["fill_model"],
                            item["close_fallback"],
                            item["exit_model"],
                            0,
                        )
                    )
                else:
                    rows.append(day)
            pnl = summarize_pnl(rows, item["fee_per_contract"], item["fill_model"], item["close_fallback"], item["exit_model"], 0)
            scenario_datasets[item["scenario_id"]].append(dataset_summary_a(label, split, bar_path, quote_path, pnl))

        for item in sub_b_scenarios:
            target = parse_time(item["entry_time"])
            days = [
                evaluate_subsystem_b_day(label, split, trade_date, bars_by_date[trade_date], put_snapshots.get(trade_date, {}), target)
                for trade_date in sorted(bars_by_date)
            ]
            scenario_datasets[item["scenario_id"]].append(dataset_summary_b(label, split, bar_path, quote_path, days))

    scenario_results = [
        aggregate_subsystem_a(scenario_by_id[scenario_id], datasets, trial_index)
        if scenario_by_id[scenario_id]["subsystem"] == "sub_a"
        else aggregate_subsystem_b(scenario_by_id[scenario_id], datasets, trial_index)
        for trial_index, (scenario_id, datasets) in enumerate(scenario_datasets.items(), start=1)
    ]
    write_component_summaries(scenario_results)
    write_search_log(scenario_results, search_log_path)
    result = aggregate_experiment(scenario_results, search_log_path)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(render_report(result), encoding="utf-8")
    return result


def run_subsystem_a_scenario(item: dict[str, Any], trial_index: int) -> dict[str, Any]:
    datasets = []
    for label, split, _adapter_name, normalized_name in SUBSYSTEM_A_DATASETS:
        normalized_root = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "databento" / normalized_name
        bar_path = normalized_root / "spy_bar.jsonl"
        quote_path = normalized_root / "option_quote.jsonl"
        bars_by_date = group_by_date(load_jsonl(bar_path), "timestamp_et")
        quotes = load_jsonl(quote_path)
        quotes_by_key = index_quotes(quotes)
        quotes_by_timestamp = group_by_date_and_timestamp(quotes, "quote_timestamp_et")
        rows = []
        for trade_date in sorted(bars_by_date):
            day = build_subsystem_a_day(trade_date, bars_by_date[trade_date], quotes_by_timestamp.get(trade_date, {}), item["entry_time"])
            if day["status"] == "candidate_ready":
                rows.append(
                    evaluate_candidate_day(
                        day,
                        quotes_by_key,
                        item["fee_per_contract"],
                        item["fill_model"],
                        item["close_fallback"],
                        item["exit_model"],
                        0,
                    )
                )
            else:
                rows.append(day)
        pnl = summarize_pnl(rows, item["fee_per_contract"], item["fill_model"], item["close_fallback"], item["exit_model"], 0)
        datasets.append(dataset_summary_a(label, split, bar_path, quote_path, pnl))
    return aggregate_subsystem_a(item, datasets, trial_index)


def build_subsystem_a_day(
    trade_date: str,
    bars: list[dict[str, Any]],
    quotes_by_timestamp: dict[str, list[dict[str, Any]]],
    breakout_time: str,
) -> dict[str, Any]:
    rth_bars = [bar for bar in bars if is_rth(bar["timestamp_et"])]
    result: dict[str, Any] = {"date": trade_date, "status": "unknown", "reasons": []}
    if not rth_bars:
        result.update(status="missing_bars", reasons=["no RTH SPY bars"])
        return result
    try:
        signal = compute_orb_signal(rth_bars, breakout_time)
    except StrategySpecError as exc:
        result.update(status="signal_error", reasons=[str(exc)])
        return result
    result["orb_signal"] = signal
    result["entry_timing_rule"] = f"opening_range_until_{breakout_time}"
    if signal["decision"] == "no_trade":
        result.update(status="no_trade", reasons=["ORB close did not break opening range"])
        return result
    entry_ts = signal["breakout_timestamp_et"]
    entry_quotes = quotes_by_timestamp.get(entry_ts, [])
    if not entry_quotes:
        result.update(status="missing_entry_quotes", reasons=[f"no option quotes at {entry_ts}"])
        return result
    direction = "call" if signal["decision"] == "call_breakout" else "put"
    try:
        legs = construct_subsystem_a_vertical(entry_quotes, direction=direction, underlying_price=signal["breakout_close"])
    except StrategySpecError as exc:
        result.update(status="construction_error", reasons=[str(exc)])
        return result
    result.update(status="candidate_ready", direction=direction, legs=legs, reasons=["ORB signal and entry option quotes are available"])
    return result


def run_subsystem_b_scenario(item: dict[str, Any], trial_index: int) -> dict[str, Any]:
    datasets = []
    target = parse_time(item["entry_time"])
    for label, split, normalized_name in SUBSYSTEM_B_DATASETS:
        normalized_root = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "databento" / normalized_name
        bar_path = normalized_root / "spy_bar.jsonl"
        quote_path = normalized_root / "option_quote.jsonl"
        bars = load_bars_by_date(bar_path)
        snapshots = load_put_snapshots_for_times(quote_path, ENTRY_TIMES_B)
        days = [
            evaluate_subsystem_b_day(label, split, trade_date, bars[trade_date], snapshots.get(trade_date, {}), target)
            for trade_date in sorted(bars)
        ]
        datasets.append(dataset_summary_b(label, split, bar_path, quote_path, days))
    return aggregate_subsystem_b(item, datasets, trial_index)


def evaluate_subsystem_b_day(
    dataset: str,
    split: str,
    trade_date: str,
    bars: list[dict[str, Any]],
    snapshots: dict[str, dict[float, dict[str, Any]]],
    target: time,
) -> dict[str, Any]:
    result: dict[str, Any] = {"date": trade_date, "dataset": dataset, "split": split, "status": "unknown", "reasons": []}
    entry_bar = nearest_bar_at_or_before(bars, target)
    if entry_bar is None:
        result.update(status="missing_underlying_entry", reasons=[f"missing SPY bar at or before {target.isoformat()} ET"])
        return result
    entry_timestamp = exact_snapshot_timestamp(snapshots, target)
    close_timestamp = choose_close_timestamp(snapshots)
    if entry_timestamp is None:
        result.update(status="missing_entry_quotes", reasons=[f"missing put snapshot exactly at {target.isoformat()} ET"])
        return result
    if close_timestamp is None:
        result.update(status="missing_close_quotes", reasons=["missing put snapshot near forced close 15:45 ET"])
        return result
    entry_quotes = list(snapshots[entry_timestamp].values())
    try:
        legs = select_capped_put_ratio_legs(entry_quotes, float(entry_bar["close"]))
    except Exception as exc:
        result.update(
            status="structure_unavailable",
            underlying_entry=float(entry_bar["close"]),
            entry_timestamp_et=entry_timestamp,
            close_timestamp_et=close_timestamp,
            reasons=[str(exc)],
        )
        return result
    close_quotes = snapshots[close_timestamp]
    missing_close = [f"{leg['right']} {leg['strike']}" for leg in legs if float(leg["strike"]) not in close_quotes]
    if missing_close:
        result.update(status="missing_leg_close_quotes", legs=legs, reasons=["missing close quotes: " + ", ".join(missing_close)])
        return result
    entry_by_strike = snapshots[entry_timestamp]
    mid_pnl = strategy_pnl(legs, entry_by_strike, close_quotes, "mid", include_fees=False)
    gross_pnl = strategy_pnl(legs, entry_by_strike, close_quotes, "implementable", include_fees=False)
    fees = round(sum(leg["quantity"] for leg in legs) * FEE_PER_CONTRACT * 2, 2)
    implementable_pnl = round(gross_pnl - fees, 2)
    entry_cashflow = opening_cashflow(legs, entry_by_strike, "implementable")
    max_loss = max_defined_loss(legs, entry_cashflow)
    result.update(
        {
            "status": "closed_forced_1545",
            "underlying_entry": float(entry_bar["close"]),
            "entry_timestamp_et": entry_timestamp,
            "close_timestamp_et": close_timestamp,
            "legs": legs,
            "entry_cashflow": round(entry_cashflow, 4),
            "max_defined_loss": max_loss,
            "account_1000_feasible": max_loss <= STARTING_EQUITY,
            "allocation_300_feasible": max_loss <= SUBSYSTEM_B_ALLOCATION,
            "risk_budget_20_feasible": max_loss <= RISK_BUDGET,
            "mid_pnl": mid_pnl,
            "gross_pnl": gross_pnl,
            "fees": fees,
            "implementable_pnl": implementable_pnl,
            "net_pnl": implementable_pnl,
            "cost_drag": round(mid_pnl - implementable_pnl, 2),
            "reasons": [f"entry uses exact put snapshot at {target.isoformat()} ET", "exit uses forced close snapshot nearest 15:45 ET"],
        }
    )
    return result


def dataset_summary_a(label: str, split: str, bar_path: Path, quote_path: Path, pnl: dict[str, Any]) -> dict[str, Any]:
    trades = [{**trade, "dataset": label, "split": split} for trade in pnl.get("trades", [])]
    return {
        "label": label,
        "split": split,
        "bar_path": str(bar_path),
        "quote_path": str(quote_path),
        "candidate_days": pnl["candidate_days"],
        "closed_trades": pnl["closed_trades"],
        "skipped_trades": pnl["skipped_trades"],
        "total_mid_pnl": pnl["total_mid_pnl"],
        "total_implementable_pnl": pnl["total_implementable_pnl"],
        "total_cost_drag": pnl["total_cost_drag"],
        "status_counts": pnl.get("status_counts", {}),
        "benchmark": benchmark_for_bars(bar_path),
        "trades": trades,
    }


def dataset_summary_b(label: str, split: str, bar_path: Path, quote_path: Path, days: list[dict[str, Any]]) -> dict[str, Any]:
    closed = [day for day in days if day["status"] == "closed_forced_1545"]
    return {
        "label": label,
        "split": split,
        "bar_path": str(bar_path),
        "quote_path": str(quote_path),
        "trading_days": len(days),
        "closed_trades": len(closed),
        "status_counts": dict(Counter(day["status"] for day in days)),
        "total_mid_pnl": round(sum(float(day["mid_pnl"]) for day in closed), 2),
        "total_implementable_pnl": round(sum(float(day["implementable_pnl"]) for day in closed), 2),
        "total_cost_drag": round(sum(float(day["cost_drag"]) for day in closed), 2),
        "trades": days,
    }


def aggregate_subsystem_a(item: dict[str, Any], datasets: list[dict[str, Any]], trial_index: int) -> dict[str, Any]:
    trades = sorted([trade for dataset in datasets for trade in dataset["trades"]], key=lambda row: (row.get("date", ""), row.get("dataset", "")))
    closed = [trade for trade in trades if str(trade.get("status", "")).startswith("closed_")]
    metrics = metrics_for_closed_trades(closed)
    return aggregate_common(item, datasets, closed, metrics, daily_pnl_rows(closed), trial_index)


def aggregate_subsystem_b(item: dict[str, Any], datasets: list[dict[str, Any]], trial_index: int) -> dict[str, Any]:
    days = sorted([day for dataset in datasets for day in dataset["trades"]], key=lambda row: (row.get("date", ""), row.get("dataset", "")))
    closed = [day for day in days if day["status"] == "closed_forced_1545"]
    metrics = metrics_for_closed_days(closed)
    result = aggregate_common(item, datasets, closed, metrics, subsystem_b_daily_pnl_rows(closed), trial_index)
    result["feasibility"] = feasibility_summary(closed)
    return result


def aggregate_common(
    item: dict[str, Any],
    datasets: list[dict[str, Any]],
    closed: list[dict[str, Any]],
    metrics: dict[str, Any],
    daily_rows: list[dict[str, Any]],
    trial_index: int,
) -> dict[str, Any]:
    return {
        "trial_index": trial_index,
        **item,
        "dataset_count": len(datasets),
        "candidate_days": sum(dataset.get("candidate_days", dataset.get("trading_days", 0)) for dataset in datasets),
        "closed_trades": len(closed),
        "skipped_trades": sum(dataset.get("skipped_trades", 0) for dataset in datasets),
        "status_counts": merge_counts(dataset["status_counts"] for dataset in datasets),
        "sample_adequacy": sample_adequacy_labels(len(closed)),
        "metrics": metrics,
        "splits": {split: split_summary(split, datasets, closed, item["subsystem"]) for split in ("in_sample", "oos")},
        "big_day_dependency": big_day_dependency_from_closed(closed, item),
        "daily_pnl": daily_rows,
        "datasets": [{key: value for key, value in dataset.items() if key != "trades"} for dataset in datasets],
        "trades": closed,
    }


def split_summary(split: str, datasets: list[dict[str, Any]], closed: list[dict[str, Any]], subsystem: str) -> dict[str, Any]:
    split_datasets = [dataset for dataset in datasets if dataset["split"] == split]
    split_closed = [trade for trade in closed if trade.get("split") == split]
    metrics = metrics_for_closed_trades(split_closed) if subsystem == "sub_a" else metrics_for_closed_days(split_closed)
    return {
        "dataset_count": len(split_datasets),
        "candidate_days": sum(dataset.get("candidate_days", dataset.get("trading_days", 0)) for dataset in split_datasets),
        "closed_trades": len(split_closed),
        "status_counts": merge_counts(dataset["status_counts"] for dataset in split_datasets),
        "metrics": metrics,
        "sample_adequacy": sample_adequacy_labels(len(split_closed)),
    }


def aggregate_experiment(rows: list[dict[str, Any]], search_log_path: Path) -> dict[str, Any]:
    best_by_subsystem = {
        subsystem: compact_scenario(max([row for row in rows if row["subsystem"] == subsystem], key=lambda row: row["metrics"]["total_implementable_pnl"]))
        for subsystem in ("sub_a", "sub_b")
    }
    baseline_a = next(row for row in rows if row["scenario_id"] == "sub_a_orb_breakout_0935")
    baseline_b = next(row for row in rows if row["scenario_id"] == "sub_b_put_ratio_entry_1000")
    return {
        "record_type": "experiment_summary",
        "schema_version": "m5_entry_timing_sensitivity_v1",
        "experiment_id": "m5_entry_timing_sensitivity",
        "status": "complete",
        "conclusion": "ยังสรุปไม่ได้",
        "conclusion_reason": "Entry timing can be compared on current real artifacts, but all scenarios remain under-sampled and underpowered.",
        "research_log_required": True,
        "research_log_slug": "higanbana-entry-timing-sensitivity-real-data",
        "methodology": {
            "scope": "Sub-System A ORB breakout-time sensitivity and Sub-System B fixed put-ratio entry-snapshot sensitivity.",
            "data_policy": "No new paid data was downloaded for this experiment.",
            "chronological_policy": "2023-03-01..2023-12-29 in-sample, 2024-01-02..2024-12-31 OOS; no OOS tuning from this report.",
            "subsystem_a_policy": "Recompute opening range and breakout decision for each candidate breakout timestamp.",
            "subsystem_b_policy": "Use exact 09:55..10:00 put snapshots for the existing capped put-ratio feasibility template.",
            "selection_policy": "Best scenarios are diagnostic only. No production entry time is selected from this under-sampled grid.",
        },
        "scenario_count": len(rows),
        "parameter_grid": parameter_grid(rows),
        "search_log": search_log_metadata(rows, search_log_path),
        "dsr_assessment": dsr_assessment(rows),
        "baseline_scenarios": {"sub_a": compact_scenario(baseline_a), "sub_b": compact_scenario(baseline_b)},
        "best_diagnostic_scenarios": best_by_subsystem,
        "sample_adequacy": sample_adequacy_labels(max(row["closed_trades"] for row in rows)),
        "scenarios": [strip_heavy_fields(row) for row in rows],
    }


def parameter_grid(rows: list[dict[str, Any]]) -> dict[str, list[Any]]:
    return {
        "subsystem": sorted({row["subsystem"] for row in rows}),
        "entry_time": sorted({row["entry_time"] for row in rows}),
        "fill_model": sorted({row["fill_model"] for row in rows}),
        "fee_per_contract": sorted({row["fee_per_contract"] for row in rows}),
        "exit_model": sorted({row["exit_model"] for row in rows}),
    }


def write_search_log(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(search_log_record(row), ensure_ascii=False, sort_keys=True) + "\n")


def search_log_record(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_type": "parameter_search_trial",
        "schema_version": "m5_search_log_v1",
        "experiment_id": "m5_entry_timing_sensitivity",
        "trial_index": row["trial_index"],
        "scenario_id": row["scenario_id"],
        "parameters": {
            "subsystem": row["subsystem"],
            "entry_time": row["entry_time"],
            "timing_axis": row["timing_axis"],
            "fill_model": row["fill_model"],
            "fee_per_contract": row["fee_per_contract"],
            "exit_model": row["exit_model"],
        },
        "metrics": row["metrics"],
        "sample_adequacy": row["sample_adequacy"],
    }


def search_log_metadata(rows: list[dict[str, Any]], path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "record_type": "parameter_search_trial",
        "trial_count": len(rows),
        "all_trials_recorded": True,
        "selection_bias_warning": "The grid is diagnostic. Do not select production entry timing from this under-sampled output.",
    }


def dsr_assessment(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "status": "blocked_under_sampled",
        "reason": "DSR is blocked because this is a multi-scenario timing grid, all scenarios are under-sampled, and no production timing rule is selected.",
        "trial_count": len(rows),
        "selected_metric": "total_implementable_pnl",
        "required_before_acceptance": [
            "acceptance-grade return distribution",
            "effective number of independent timing trials",
            "null Sharpe threshold",
            "skew/kurtosis/autocorrelation diagnostics",
        ],
    }


def compact_scenario(row: dict[str, Any]) -> dict[str, Any]:
    item = {
        "scenario_id": row["scenario_id"],
        "subsystem": row["subsystem"],
        "entry_time": row["entry_time"],
        "closed_trades": row["closed_trades"],
        "metrics": row["metrics"],
        "oos_metrics": row["splits"]["oos"]["metrics"],
    }
    if "feasibility" in row:
        item["feasibility"] = row["feasibility"]
    return item


def strip_heavy_fields(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key not in {"trades", "daily_pnl"}}


def write_component_summaries(rows: list[dict[str, Any]]) -> None:
    COMPONENT_ROOT.mkdir(parents=True, exist_ok=True)
    for row in rows:
        path = COMPONENT_ROOT / f"{row['scenario_id']}_summary.json"
        path.write_text(json.dumps(strip_heavy_fields(row), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# M5.3 Entry Timing Sensitivity",
        "",
        "## Status",
        f"- Conclusion: {result['conclusion']}",
        f"- Reason: {result['conclusion_reason']}",
        "- Evidence type: real-data deterministic sensitivity, diagnostic only.",
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
        "| Scenario | Sub-System | Entry | Closed | Net PnL | Mid PnL | Cost Drag | OOS PnL | MDD | Labels |",
        "|:--|:--|:--|--:|--:|--:|--:|--:|--:|:--|",
    ]
    for row in result["scenarios"]:
        metrics = row["metrics"]
        oos = row["splits"]["oos"]["metrics"]
        labels = ", ".join(row["sample_adequacy"]["labels"])
        lines.append(
            f"| `{row['scenario_id']}` | `{row['subsystem']}` | `{row['entry_time']}` | {row['closed_trades']} | "
            f"{metrics['total_implementable_pnl']} | {metrics['total_mid_pnl']} | {metrics['total_cost_drag']} | "
            f"{oos['total_implementable_pnl']} | {metrics['max_drawdown']} | {labels} |"
        )
    lines.extend(
        [
            "",
            "## Baseline Scenarios",
            "```json",
            json.dumps(result["baseline_scenarios"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Best Diagnostic Scenarios",
            "```json",
            json.dumps(result["best_diagnostic_scenarios"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Interpretation",
            "- Entry-time variants are search trials; they must not be selected as production rules from this under-sampled result.",
            "- Sub-System A variants recompute the ORB range at each timestamp, so this is not just latency replay.",
            "- Sub-System B variants use the existing fixed put-ratio template and still need separate capital/structure research before feasibility can pass.",
            "",
        ]
    )
    return "\n".join(lines)


def big_day_dependency_from_closed(closed: list[dict[str, Any]], item: dict[str, Any]) -> dict[str, Any]:
    if item["subsystem"] == "sub_a":
        return summarize_pnl(
            closed,
            item["fee_per_contract"],
            item["fill_model"],
            item["close_fallback"],
            item["exit_model"],
            0,
        )["big_day_dependency"]
    from run_jan2024_pilot_pnl import big_day_dependency_check

    return big_day_dependency_check(closed)


def feasibility_summary(closed: list[dict[str, Any]]) -> dict[str, Any]:
    if not closed:
        return {}
    return {
        "checked_trades": len(closed),
        "allocation_300_feasible_count": sum(1 for day in closed if day.get("allocation_300_feasible")),
        "risk_budget_20_feasible_count": sum(1 for day in closed if day.get("risk_budget_20_feasible")),
        "all_trades_fit_300_allocation": all(day.get("allocation_300_feasible") for day in closed),
        "all_trades_fit_20_risk_budget": all(day.get("risk_budget_20_feasible") for day in closed),
    }


def load_put_snapshots_for_times(path: Path, entry_times: list[str]) -> dict[str, dict[str, dict[float, dict[str, Any]]]]:
    if not path.exists():
        return {}
    return put_snapshots_from_quotes(load_jsonl(path), entry_times)


def put_snapshots_from_quotes(records: list[dict[str, Any]], entry_times: list[str]) -> dict[str, dict[str, dict[float, dict[str, Any]]]]:
    allowed_times = set(entry_times) | {"15:35:00", "15:36:00", "15:37:00", "15:38:00", "15:39:00", "15:40:00", "15:41:00", "15:42:00", "15:43:00", "15:44:00", "15:45:00"}
    snapshots: dict[str, dict[str, dict[float, dict[str, Any]]]] = defaultdict(lambda: defaultdict(dict))
    for record in records:
        if record.get("right") != "put":
            continue
        timestamp = record["quote_timestamp_et"]
        if timestamp[11:19] not in allowed_times:
            continue
        snapshots[record["expiration_date"]][timestamp][float(record["strike"])] = record
    return {trade_date: dict(by_timestamp) for trade_date, by_timestamp in snapshots.items()}


def nearest_bar_at_or_before(bars: list[dict[str, Any]], target: time) -> dict[str, Any] | None:
    candidates = [bar for bar in bars if datetime.fromisoformat(bar["timestamp_et"]).time() <= target]
    return max(candidates, key=lambda row: row["timestamp_et"], default=None)


def exact_snapshot_timestamp(snapshots: dict[str, dict[float, dict[str, Any]]], target: time) -> str | None:
    candidates = [timestamp for timestamp in snapshots if datetime.fromisoformat(timestamp).time() == target]
    return max(candidates) if candidates else None


def group_by_date(records: list[dict[str, Any]], timestamp_field: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[record[timestamp_field][:10]].append(record)
    return dict(grouped)


def group_by_date_and_timestamp(records: list[dict[str, Any]], timestamp_field: str) -> dict[str, dict[str, list[dict[str, Any]]]]:
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for record in records:
        timestamp = record[timestamp_field]
        grouped[timestamp[:10]][timestamp].append(record)
    return {date_key: dict(by_timestamp) for date_key, by_timestamp in grouped.items()}


def merge_counts(items: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        for key, value in item.items():
            counts[key] = counts.get(key, 0) + int(value)
    return dict(sorted(counts.items()))


def parse_time(value: str) -> time:
    return datetime.strptime(value, "%H:%M:%S").time()


def time_id(value: str) -> str:
    return value.replace(":", "")[:4]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run M5.3 entry-timing sensitivity on current real-data artifacts.")
    parser.add_argument("--summary-path", type=Path, default=SUMMARY_PATH)
    parser.add_argument("--report-path", type=Path, default=REPORT_PATH)
    parser.add_argument("--search-log-path", type=Path, default=SEARCH_LOG_PATH)
    args = parser.parse_args(argv)
    result = run_experiment(args.summary_path, args.report_path, args.search_log_path)
    print(json.dumps({key: value for key, value in result.items() if key != "scenarios"}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
