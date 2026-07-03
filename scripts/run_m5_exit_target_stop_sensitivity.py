from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from run_jan2024_pilot_pnl import (
    FORCED_CLOSE_TIME,
    apply_entry_latency,
    big_day_dependency_check,
    build_entry_fills,
    calculate_trade_pnl,
    candidate_exit_timestamps,
    find_close_quote,
    index_quotes,
    leg_fill_price,
    load_jsonl,
    liquidation_price,
    mid_price,
    sample_adequacy_labels,
    signed_cashflow,
)
from run_m4_subsystem_a_baseline import DATASETS, benchmark_for_bars, daily_pnl_rows, metrics_for_closed_trades


REPORT_ROOT = PROJECT_ROOT / "reports" / "experiments"
SUMMARY_PATH = REPORT_ROOT / "m5_exit_target_stop_sensitivity_summary.json"
REPORT_PATH = REPORT_ROOT / "m5_exit_target_stop_sensitivity_report.md"
SEARCH_LOG_PATH = REPORT_ROOT / "search_logs" / "m5_exit_target_stop_sensitivity_search_log.jsonl"
COMPONENT_ROOT = REPORT_ROOT / "m5_exit_target_stop_components"

FILL_MODEL = "half_spread"
FEE_PER_CONTRACT = 0.64
CLOSE_FALLBACK = "nearest_1545_window"


def default_scenarios() -> list[dict[str, Any]]:
    return [
        scenario("forced_close_only_control", None, None),
        scenario("tp_10_stop_25", 0.10, 0.25),
        scenario("tp_25_stop_50_baseline", 0.25, 0.50),
        scenario("tp_50_stop_50", 0.50, 0.50),
        scenario("tp_50_stop_75", 0.50, 0.75),
        scenario("tp_100_stop_50", 1.00, 0.50),
        scenario("tp_100_stop_100", 1.00, 1.00),
    ]


def scenario(scenario_id: str, profit_target_pct: float | None, stop_loss_pct: float | None) -> dict[str, Any]:
    return {
        "scenario_id": scenario_id,
        "profit_target_pct": profit_target_pct,
        "stop_loss_pct": stop_loss_pct,
        "fill_model": FILL_MODEL,
        "fee_per_contract": FEE_PER_CONTRACT,
        "close_fallback": CLOSE_FALLBACK,
        "entry_latency_minutes": 0,
    }


def run_experiment(
    summary_path: Path = SUMMARY_PATH,
    report_path: Path = REPORT_PATH,
    search_log_path: Path = SEARCH_LOG_PATH,
) -> dict[str, Any]:
    scenarios = default_scenarios()
    scenario_datasets: dict[str, list[dict[str, Any]]] = {item["scenario_id"]: [] for item in scenarios}

    for label, split, adapter_name, normalized_name in DATASETS:
        adapter_path = PROJECT_ROOT / "reports" / "pilots" / adapter_name
        quote_path = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "databento" / normalized_name / "option_quote.jsonl"
        bar_path = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "databento" / normalized_name / "spy_bar.jsonl"
        adapter_summary = json.loads(adapter_path.read_text(encoding="utf-8"))
        quotes_by_key = index_quotes(load_jsonl(quote_path))
        candidate_days = [day for day in adapter_summary["days"] if day["status"] == "candidate_ready"]
        for item in scenarios:
            rows = [
                evaluate_candidate_day_with_thresholds(day, quotes_by_key, item)
                for day in candidate_days
            ]
            pnl = summarize_rows(rows)
            scenario_datasets[item["scenario_id"]].append(dataset_summary(label, split, adapter_path, quote_path, bar_path, pnl))

    scenario_results = [
        aggregate_scenario(item, scenario_datasets[item["scenario_id"]], trial_index)
        for trial_index, item in enumerate(scenarios, start=1)
    ]
    write_component_summaries(scenario_results)
    write_search_log(scenario_results, search_log_path)
    result = aggregate_experiment(scenario_results, search_log_path)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(render_report(result), encoding="utf-8")
    return result


def evaluate_candidate_day_with_thresholds(
    day: dict[str, Any],
    quotes_by_key: dict[tuple[str, str, float, str], dict[str, Any]],
    scenario_def: dict[str, Any],
) -> dict[str, Any]:
    trade_date = day["date"]
    signal_ts = day["orb_signal"]["breakout_timestamp_et"]
    entry_ts = apply_entry_latency(signal_ts, int(scenario_def["entry_latency_minutes"]))
    close_ts = f"{trade_date}T{FORCED_CLOSE_TIME}{entry_ts[-6:]}"
    result: dict[str, Any] = {
        "date": trade_date,
        "status": "unknown",
        "direction": day["direction"],
        "signal_time_et": signal_ts,
        "entry_time_et": entry_ts,
        "close_time_et": close_ts,
        "legs": day["legs"],
        "scenario_id": scenario_def["scenario_id"],
        "reasons": [],
    }

    entry_fills = []
    missing = []
    for leg in day["legs"]:
        entry_quote = quotes_by_key.get((entry_ts, leg["right"], float(leg["strike"]), leg["expiration_date"]))
        if entry_quote is None:
            missing.append(f"entry {leg['right']} {leg['strike']}")
            continue
        entry_fills.append(
            {
                "fill_id": f"m5-exit-{trade_date}-{leg['leg_id']}",
                "leg_id": leg["leg_id"],
                "side": leg["side"],
                "quantity": leg["quantity"],
                "price": leg_fill_price(entry_quote, leg["side"], scenario_def["fill_model"]),
                "fill_model": scenario_def["fill_model"],
            }
        )
    if missing:
        result.update(status="missing_quotes", reasons=["missing quotes: " + ", ".join(missing)])
        return result

    entry_debit = round(sum(signed_cashflow(fill["side"], fill["price"], fill["quantity"]) for fill in entry_fills), 4)
    exit_result = find_exit_with_thresholds(quotes_by_key, trade_date, entry_ts, close_ts, day["legs"], entry_debit, scenario_def)
    if exit_result["missing"]:
        result.update(status="missing_quotes", reasons=["missing quotes: " + ", ".join(exit_result["missing"])])
        return result

    entry_mid_fills = build_entry_fills(day["legs"], quotes_by_key, entry_ts, trade_date, "mid")
    mid_pnl = calculate_trade_pnl(entry_mid_fills, exit_result["closing_mid_prices_by_leg_id"])
    gross_pnl = calculate_trade_pnl(entry_fills, exit_result["closing_prices_by_leg_id"])
    contracts = sum(fill["quantity"] for fill in entry_fills)
    fees = round(contracts * float(scenario_def["fee_per_contract"]) * 2, 2)
    implementable_pnl = round(gross_pnl - fees, 2)
    result.update(
        {
            "status": f"closed_{exit_result['exit_reason']}",
            "entry_debit": entry_debit,
            "mid_pnl": mid_pnl,
            "gross_pnl": gross_pnl,
            "fees": fees,
            "implementable_pnl": implementable_pnl,
            "net_pnl": implementable_pnl,
            "cost_drag": round(mid_pnl - implementable_pnl, 2),
            "entry_fills": entry_fills,
            "entry_mid_fills": entry_mid_fills,
            "closing_prices_by_leg_id": exit_result["closing_prices_by_leg_id"],
            "closing_mid_prices_by_leg_id": exit_result["closing_mid_prices_by_leg_id"],
            "close_timestamps_by_leg_id": exit_result["close_timestamps_by_leg_id"],
            "exit_value": exit_result["exit_value"],
            "mid_exit_value": exit_result["mid_exit_value"],
            "exit_model": "target_stop_grid" if scenario_def["profit_target_pct"] is not None else "forced_close_only",
            "profit_target_pct": scenario_def["profit_target_pct"],
            "stop_loss_pct": scenario_def["stop_loss_pct"],
            "reasons": [
                f"entry at {scenario_def['fill_model']}; exit={exit_result['exit_reason']}; close_fallback={scenario_def['close_fallback']}"
            ],
        }
    )
    return result


def find_exit_with_thresholds(
    quotes_by_key: dict[tuple[str, str, float, str], dict[str, Any]],
    trade_date: str,
    entry_ts: str,
    close_ts: str,
    legs: list[dict[str, Any]],
    entry_debit: float,
    scenario_def: dict[str, Any],
) -> dict[str, Any]:
    profit_target_pct = scenario_def["profit_target_pct"]
    stop_loss_pct = scenario_def["stop_loss_pct"]
    if profit_target_pct is not None and stop_loss_pct is not None:
        profit_value = entry_debit * (1.0 + float(profit_target_pct))
        stop_value = entry_debit * max(0.0, 1.0 - float(stop_loss_pct))
        for timestamp in candidate_exit_timestamps(quotes_by_key, trade_date, entry_ts, close_ts):
            quotes = quotes_for_legs_at_timestamp(quotes_by_key, timestamp, legs)
            if quotes is None:
                continue
            value = spread_liquidation_value(legs, quotes)
            if value >= profit_value:
                return exit_payload(legs, quotes, timestamp, value, f"profit_target_{pct_id(profit_target_pct)}")
            if value <= stop_value:
                return exit_payload(legs, quotes, timestamp, value, f"stop_loss_{pct_id(stop_loss_pct)}")

    close_quotes: dict[str, dict[str, Any]] = {}
    close_timestamps: dict[str, str] = {}
    missing = []
    for leg in legs:
        close_quote, actual_close_ts = find_close_quote(quotes_by_key, close_ts, leg, scenario_def["close_fallback"])
        if close_quote is None:
            missing.append(f"close {leg['right']} {leg['strike']}")
            continue
        close_quotes[leg["leg_id"]] = close_quote
        close_timestamps[leg["leg_id"]] = actual_close_ts
    if missing:
        return {"missing": missing}
    value = spread_liquidation_value(legs, close_quotes)
    payload = exit_payload(legs, close_quotes, close_ts, value, "forced_1545")
    payload["close_timestamps_by_leg_id"] = close_timestamps
    return payload


def quotes_for_legs_at_timestamp(
    quotes_by_key: dict[tuple[str, str, float, str], dict[str, Any]],
    timestamp: str,
    legs: list[dict[str, Any]],
) -> dict[str, dict[str, Any]] | None:
    quotes = {}
    for leg in legs:
        quote = quotes_by_key.get((timestamp, leg["right"], float(leg["strike"]), leg["expiration_date"]))
        if quote is None:
            return None
        quotes[leg["leg_id"]] = quote
    return quotes


def spread_liquidation_value(legs: list[dict[str, Any]], quotes_by_leg_id: dict[str, dict[str, Any]]) -> float:
    value = 0.0
    for leg in legs:
        value += signed_cashflow(leg["side"], liquidation_price(quotes_by_leg_id[leg["leg_id"]], leg["side"]), leg["quantity"])
    return round(value, 4)


def spread_mid_value(legs: list[dict[str, Any]], quotes_by_leg_id: dict[str, dict[str, Any]]) -> float:
    value = 0.0
    for leg in legs:
        value += signed_cashflow(leg["side"], mid_price(quotes_by_leg_id[leg["leg_id"]]), leg["quantity"])
    return round(value, 4)


def exit_payload(
    legs: list[dict[str, Any]],
    quotes_by_leg_id: dict[str, dict[str, Any]],
    timestamp: str,
    value: float,
    exit_reason: str,
) -> dict[str, Any]:
    return {
        "missing": [],
        "exit_reason": exit_reason,
        "exit_value": value,
        "mid_exit_value": spread_mid_value(legs, quotes_by_leg_id),
        "closing_prices_by_leg_id": {
            leg["leg_id"]: liquidation_price(quotes_by_leg_id[leg["leg_id"]], leg["side"])
            for leg in legs
        },
        "closing_mid_prices_by_leg_id": {
            leg["leg_id"]: mid_price(quotes_by_leg_id[leg["leg_id"]])
            for leg in legs
        },
        "close_timestamps_by_leg_id": {leg["leg_id"]: timestamp for leg in legs},
    }


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    closed = [row for row in rows if row["status"].startswith("closed_")]
    skipped = [row for row in rows if not row["status"].startswith("closed_")]
    return {
        "candidate_days": len(rows),
        "closed_trades": len(closed),
        "skipped_trades": len(skipped),
        "total_mid_pnl": round(sum(float(row["mid_pnl"]) for row in closed), 2),
        "total_implementable_pnl": round(sum(float(row["implementable_pnl"]) for row in closed), 2),
        "total_cost_drag": round(sum(float(row["cost_drag"]) for row in closed), 2),
        "status_counts": status_counts(rows),
        "big_day_dependency": big_day_dependency_check(closed),
        "trades": rows,
    }


def dataset_summary(
    label: str,
    split: str,
    adapter_path: Path,
    quote_path: Path,
    bar_path: Path,
    pnl: dict[str, Any],
) -> dict[str, Any]:
    trades = [{**trade, "dataset": label, "split": split} for trade in pnl["trades"]]
    return {
        "label": label,
        "split": split,
        "adapter_path": str(adapter_path),
        "quote_path": str(quote_path),
        "bar_path": str(bar_path),
        "candidate_days": pnl["candidate_days"],
        "closed_trades": pnl["closed_trades"],
        "skipped_trades": pnl["skipped_trades"],
        "total_mid_pnl": pnl["total_mid_pnl"],
        "total_implementable_pnl": pnl["total_implementable_pnl"],
        "total_cost_drag": pnl["total_cost_drag"],
        "status_counts": pnl["status_counts"],
        "benchmark": benchmark_for_bars(bar_path),
        "trades": trades,
    }


def aggregate_scenario(scenario_def: dict[str, Any], datasets: list[dict[str, Any]], trial_index: int) -> dict[str, Any]:
    trades = sorted([trade for dataset in datasets for trade in dataset["trades"]], key=lambda row: (row.get("date", ""), row.get("dataset", "")))
    closed = [trade for trade in trades if str(trade.get("status", "")).startswith("closed_")]
    metrics = metrics_for_closed_trades(closed)
    metrics["exit_reason_counts"] = exit_reason_counts(closed)
    return {
        "trial_index": trial_index,
        **scenario_def,
        "candidate_days": sum(dataset["candidate_days"] for dataset in datasets),
        "closed_trades": len(closed),
        "skipped_trades": sum(dataset["skipped_trades"] for dataset in datasets),
        "status_counts": merge_counts(dataset["status_counts"] for dataset in datasets),
        "sample_adequacy": sample_adequacy_labels(len(closed)),
        "metrics": metrics,
        "splits": {split: split_summary(split, datasets, closed) for split in ("in_sample", "oos")},
        "big_day_dependency": big_day_dependency_check(closed),
        "daily_pnl": daily_pnl_rows(closed),
        "datasets": [{key: value for key, value in dataset.items() if key != "trades"} for dataset in datasets],
        "trades": closed,
    }


def split_summary(split: str, datasets: list[dict[str, Any]], closed: list[dict[str, Any]]) -> dict[str, Any]:
    split_datasets = [dataset for dataset in datasets if dataset["split"] == split]
    split_closed = [trade for trade in closed if trade.get("split") == split]
    return {
        "dataset_count": len(split_datasets),
        "candidate_days": sum(dataset["candidate_days"] for dataset in split_datasets),
        "closed_trades": len(split_closed),
        "skipped_trades": sum(dataset["skipped_trades"] for dataset in split_datasets),
        "metrics": metrics_for_closed_trades(split_closed),
        "sample_adequacy": sample_adequacy_labels(len(split_closed)),
    }


def aggregate_experiment(rows: list[dict[str, Any]], search_log_path: Path) -> dict[str, Any]:
    baseline = next(row for row in rows if row["scenario_id"] == "forced_close_only_control")
    best = max(rows, key=lambda row: row["metrics"]["total_implementable_pnl"])
    worst = min(rows, key=lambda row: row["metrics"]["total_implementable_pnl"])
    return {
        "record_type": "experiment_summary",
        "schema_version": "m5_exit_target_stop_sensitivity_v1",
        "experiment_id": "m5_exit_target_stop_sensitivity",
        "status": "complete",
        "conclusion": "ยังสรุปไม่ได้",
        "conclusion_reason": "Exit target/stop grid is useful diagnostically, but all scenarios remain under-sampled and underpowered; no production TP/SL is selected.",
        "research_log_required": True,
        "research_log_slug": "higanbana-exit-target-stop-sensitivity-real-data",
        "methodology": {
            "scope": "Sub-System A ORB directional debit vertical on current real-data artifacts only.",
            "data_policy": "No new paid data was downloaded for this experiment.",
            "chronological_policy": "2023-03-01..2023-12-29 in-sample, 2024-01-02..2024-12-31 OOS; no OOS tuning from this report.",
            "entry_policy": "Entry market orders remain prohibited; baseline entry uses half-spread fill and skips missing quotes.",
            "exit_policy": "Grid tests profit-target and stop-loss thresholds using available intraday quotes; unresolved trades force-close by 15:45 ET fallback.",
            "selection_policy": "Best/worst scenarios are diagnostic only. Do not select production TP/SL from this under-sampled grid.",
        },
        "scenario_count": len(rows),
        "parameter_grid": parameter_grid(rows),
        "search_log": search_log_metadata(rows, search_log_path),
        "dsr_assessment": dsr_assessment(rows),
        "baseline_scenario": compact_scenario(baseline),
        "best_diagnostic_scenario": compact_scenario(best),
        "worst_diagnostic_scenario": compact_scenario(worst),
        "sample_adequacy": sample_adequacy_labels(max(row["closed_trades"] for row in rows)),
        "scenarios": [strip_heavy_fields(row) for row in rows],
    }


def parameter_grid(rows: list[dict[str, Any]]) -> dict[str, list[Any]]:
    return {
        "profit_target_pct": sorted({row["profit_target_pct"] for row in rows}, key=lambda value: (-1 if value is None else value)),
        "stop_loss_pct": sorted({row["stop_loss_pct"] for row in rows}, key=lambda value: (-1 if value is None else value)),
        "fill_model": sorted({row["fill_model"] for row in rows}),
        "fee_per_contract": sorted({row["fee_per_contract"] for row in rows}),
        "close_fallback": sorted({row["close_fallback"] for row in rows}),
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
        "experiment_id": "m5_exit_target_stop_sensitivity",
        "trial_index": row["trial_index"],
        "scenario_id": row["scenario_id"],
        "parameters": {
            "profit_target_pct": row["profit_target_pct"],
            "stop_loss_pct": row["stop_loss_pct"],
            "fill_model": row["fill_model"],
            "fee_per_contract": row["fee_per_contract"],
            "close_fallback": row["close_fallback"],
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
        "selection_bias_warning": "The TP/SL grid is diagnostic. Do not select production exit parameters from this under-sampled output.",
    }


def dsr_assessment(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "status": "blocked_under_sampled",
        "reason": "DSR is blocked because this is a multi-scenario TP/SL grid, all scenarios are under-sampled, and no production exit rule is selected.",
        "trial_count": len(rows),
        "selected_metric": "total_implementable_pnl",
        "required_before_acceptance": [
            "acceptance-grade return distribution",
            "effective number of independent TP/SL trials",
            "null Sharpe threshold",
            "skew/kurtosis/autocorrelation diagnostics",
        ],
    }


def compact_scenario(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "scenario_id": row["scenario_id"],
        "profit_target_pct": row["profit_target_pct"],
        "stop_loss_pct": row["stop_loss_pct"],
        "closed_trades": row["closed_trades"],
        "metrics": row["metrics"],
        "oos_metrics": row["splits"]["oos"]["metrics"],
    }


def strip_heavy_fields(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key not in {"trades", "daily_pnl"}}


def write_component_summaries(rows: list[dict[str, Any]]) -> None:
    COMPONENT_ROOT.mkdir(parents=True, exist_ok=True)
    for row in rows:
        path = COMPONENT_ROOT / f"{row['scenario_id']}_summary.json"
        path.write_text(json.dumps(strip_heavy_fields(row), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# M5.4 Exit Target/Stop Sensitivity",
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
        "| Scenario | TP | SL | Closed | Mid PnL | Implementable PnL | Cost Drag | OOS PnL | ES95 | ES99 | MDD | Exit reasons |",
        "|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|:--|",
    ]
    for row in result["scenarios"]:
        metrics = row["metrics"]
        oos = row["splits"]["oos"]["metrics"]
        lines.append(
            f"| `{row['scenario_id']}` | {row['profit_target_pct']} | {row['stop_loss_pct']} | {row['closed_trades']} | "
            f"{metrics['total_mid_pnl']} | {metrics['total_implementable_pnl']} | {metrics['total_cost_drag']} | "
            f"{oos['total_implementable_pnl']} | {metrics['es95']} | {metrics['es99']} | {metrics['max_drawdown']} | "
            f"`{json.dumps(metrics['exit_reason_counts'], ensure_ascii=False, sort_keys=True)}` |"
        )
    lines.extend(
        [
            "",
            "## Baseline Scenario",
            "```json",
            json.dumps(result["baseline_scenario"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Best/Worst Diagnostic Scenarios",
            "```json",
            json.dumps(
                {
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
            "- TP/SL variants are search trials; they must not be selected as production rules from this under-sampled result.",
            "- OOS deltas are reported for diagnosis only and are not tuning input.",
            "- Implementable PnL is the deployable reference; Mid PnL is a control.",
            "",
        ]
    )
    return "\n".join(lines)


def status_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    return dict(sorted(counts.items()))


def merge_counts(items: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        for key, value in item.items():
            counts[key] = counts.get(key, 0) + int(value)
    return dict(sorted(counts.items()))


def exit_reason_counts(closed: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in closed:
        reason = str(row["status"]).removeprefix("closed_")
        counts[reason] = counts.get(reason, 0) + 1
    return dict(sorted(counts.items()))


def pct_id(value: float) -> str:
    return f"{int(round(value * 100))}pct"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run M5.4 exit target/stop sensitivity on current real-data artifacts.")
    parser.add_argument("--summary-path", type=Path, default=SUMMARY_PATH)
    parser.add_argument("--report-path", type=Path, default=REPORT_PATH)
    parser.add_argument("--search-log-path", type=Path, default=SEARCH_LOG_PATH)
    args = parser.parse_args(argv)
    result = run_experiment(args.summary_path, args.report_path, args.search_log_path)
    print(json.dumps({key: value for key, value in result.items() if key != "scenarios"}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
