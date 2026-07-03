from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from run_jan2024_pilot_pnl import evaluate_candidate_day, index_quotes, load_jsonl, sample_adequacy_labels, summarize_pnl
from run_m4_subsystem_a_baseline import DATASETS, benchmark_for_bars, daily_pnl_rows, metrics_for_closed_trades


REPORT_ROOT = PROJECT_ROOT / "reports" / "experiments"
SUMMARY_PATH = REPORT_ROOT / "m5_strike_selection_sensitivity_summary.json"
REPORT_PATH = REPORT_ROOT / "m5_strike_selection_sensitivity_report.md"
SEARCH_LOG_PATH = REPORT_ROOT / "search_logs" / "m5_strike_selection_sensitivity_search_log.jsonl"
COMPONENT_ROOT = REPORT_ROOT / "m5_strike_selection_components"

FEE_PER_CONTRACT = 0.64
FILL_MODEL = "half_spread"
CLOSE_FALLBACK = "nearest_1545_window"
EXIT_MODEL = "forced_close_only"
WIDTH = 2.0
GAP_TOLERANCE = 0.25


class StrikeSelectionError(ValueError):
    pass


def default_scenarios() -> list[dict[str, Any]]:
    return [
        scenario("target_gap_0_25_width_2", 0.25),
        scenario("target_gap_0_75_width_2", 0.75),
        scenario("target_gap_1_25_width_2", 1.25),
        scenario("target_gap_1_75_width_2", 1.75),
        scenario("baseline_gap_1_48_width_2", 1.48),
    ]


def scenario(scenario_id: str, target_gap: float) -> dict[str, Any]:
    return {
        "scenario_id": scenario_id,
        "selection_family": "moneyness_target_gap",
        "target_gap": target_gap,
        "width": WIDTH,
        "fee_per_contract": FEE_PER_CONTRACT,
        "fill_model": FILL_MODEL,
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
    scenario_mapping_rows: dict[str, list[dict[str, Any]]] = {item["scenario_id"]: [] for item in scenarios}

    for label, split, adapter_name, normalized_name in DATASETS:
        adapter_path = PROJECT_ROOT / "reports" / "pilots" / adapter_name
        quote_path = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "databento" / normalized_name / "option_quote.jsonl"
        bar_path = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "databento" / normalized_name / "spy_bar.jsonl"
        adapter_summary = json.loads(adapter_path.read_text(encoding="utf-8"))
        quotes = load_jsonl(quote_path)
        quotes_by_key = index_quotes(quotes)
        quotes_by_timestamp = group_quotes_by_timestamp(quotes)
        candidate_days = [day for day in adapter_summary["days"] if day["status"] == "candidate_ready"]

        for item in scenarios:
            rows = []
            mapping_rows = []
            for day in candidate_days:
                mapped_day = remap_candidate_day(day, quotes_by_timestamp, item)
                mapping_rows.append(
                    {
                        "date": day["date"],
                        "dataset": label,
                        "split": split,
                        **mapped_day["strike_mapping"],
                    }
                )
                rows.append(
                    evaluate_candidate_day(
                        mapped_day,
                        quotes_by_key,
                        item["fee_per_contract"],
                        item["fill_model"],
                        item["close_fallback"],
                        item["exit_model"],
                    )
                )
            pnl = summarize_pnl(rows, item["fee_per_contract"], item["fill_model"], item["close_fallback"], item["exit_model"])
            scenario_datasets[item["scenario_id"]].append(dataset_summary(label, split, adapter_path, quote_path, bar_path, pnl))
            scenario_mapping_rows[item["scenario_id"]].extend(mapping_rows)

    scenario_results = [
        aggregate_scenario(item, scenario_datasets[item["scenario_id"]], scenario_mapping_rows[item["scenario_id"]], trial_index)
        for trial_index, item in enumerate(scenarios, start=1)
    ]
    write_component_summaries(scenario_results)
    write_search_log(scenario_results, search_log_path)
    result = aggregate_experiment(scenario_results, scenarios, search_log_path)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(result), encoding="utf-8")
    return result


def remap_candidate_day(
    day: dict[str, Any],
    quotes_by_timestamp: dict[str, list[dict[str, Any]]],
    scenario_def: dict[str, Any],
) -> dict[str, Any]:
    entry_ts = day["orb_signal"]["breakout_timestamp_et"]
    entry_quotes = quotes_by_timestamp.get(entry_ts, [])
    if not entry_quotes:
        raise StrikeSelectionError(f"missing entry quotes at {entry_ts}")
    legs, mapping = select_vertical_legs(
        entry_quotes,
        direction=day["direction"],
        underlying_price=float(day["orb_signal"]["breakout_close"]),
        target_gap=float(scenario_def["target_gap"]),
        width=float(scenario_def["width"]),
    )
    return {
        **day,
        "legs": legs,
        "strike_mapping": {
            **mapping,
            "selection_family": scenario_def["selection_family"],
            "scenario_id": scenario_def["scenario_id"],
            "gap_tolerance": GAP_TOLERANCE,
            "gap_tolerance_breached": abs(mapping["realized_long_gap"] - mapping["target_gap"]) > GAP_TOLERANCE,
        },
    }


def select_vertical_legs(
    option_quotes: list[dict[str, Any]],
    direction: str,
    underlying_price: float,
    target_gap: float,
    width: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if direction not in {"call", "put"}:
        raise StrikeSelectionError("direction must be call or put")
    quotes = sorted([quote for quote in option_quotes if quote["right"] == direction], key=lambda row: float(row["strike"]))
    if len(quotes) < 2:
        raise StrikeSelectionError("at least two strikes are required")

    if direction == "call":
        long_candidates = [quote for quote in quotes if float(quote["strike"]) >= underlying_price]
        desired_long = underlying_price + target_gap
        long_quote = nearest_quote(long_candidates, desired_long, prefer_higher=False)
        short_candidates = [quote for quote in quotes if float(quote["strike"]) > float(long_quote["strike"])]
        desired_short = float(long_quote["strike"]) + width
        short_quote = nearest_quote(short_candidates, desired_short, prefer_higher=True)
    else:
        long_candidates = [quote for quote in quotes if float(quote["strike"]) <= underlying_price]
        desired_long = underlying_price - target_gap
        long_quote = nearest_quote(long_candidates, desired_long, prefer_higher=True)
        short_candidates = [quote for quote in quotes if float(quote["strike"]) < float(long_quote["strike"])]
        desired_short = float(long_quote["strike"]) - width
        short_quote = nearest_quote(short_candidates, desired_short, prefer_higher=False)

    long_strike = float(long_quote["strike"])
    short_strike = float(short_quote["strike"])
    realized_gap = abs(long_strike - underlying_price)
    realized_width = abs(short_strike - long_strike)
    mapping = {
        "mapping_method": "nearest_discrete_strike_rounding",
        "tie_breaker": "nearest_target_then_lower_entry_debit_then_nearest_width",
        "interpolation_used": False,
        "direction": direction,
        "underlying_price": round(underlying_price, 4),
        "target_gap": target_gap,
        "desired_long_strike": round(desired_long, 4),
        "long_strike": long_strike,
        "short_strike": short_strike,
        "realized_long_gap": round(realized_gap, 4),
        "realized_gap_error": round(realized_gap - target_gap, 4),
        "target_width": width,
        "realized_width": round(realized_width, 4),
        "long_moneyness": round(long_strike / underlying_price, 6) if underlying_price else None,
        "spread_entry_mid_debit": round(mid_price(long_quote) - mid_price(short_quote), 4),
        "spread_entry_implementable_debit": round(float(long_quote["ask"]) - float(short_quote["bid"]), 4),
    }
    return [
        make_leg("m5_long", long_quote, "buy"),
        make_leg("m5_short", short_quote, "sell"),
    ], mapping


def nearest_quote(quotes: list[dict[str, Any]], target_strike: float, prefer_higher: bool) -> dict[str, Any]:
    if not quotes:
        raise StrikeSelectionError("no quote can satisfy requested strike mapping")
    return min(
        quotes,
        key=lambda quote: (
            abs(float(quote["strike"]) - target_strike),
            entry_debit_proxy(quote),
            -float(quote["strike"]) if prefer_higher else float(quote["strike"]),
        ),
    )


def entry_debit_proxy(quote: dict[str, Any]) -> float:
    return float(quote["ask"]) - float(quote["bid"])


def make_leg(seed: str, quote: dict[str, Any], side: str) -> dict[str, Any]:
    return {
        "leg_id": f"{seed}_{quote['right']}_{float(quote['strike']):.4f}".replace(".", "_"),
        "underlying": quote["underlying"],
        "expiration_date": quote["expiration_date"],
        "right": quote["right"],
        "strike": float(quote["strike"]),
        "side": side,
        "quantity": 1,
    }


def dataset_summary(
    label: str,
    split: str,
    adapter_path: Path,
    quote_path: Path,
    bar_path: Path,
    pnl: dict[str, Any],
) -> dict[str, Any]:
    trades = [{**trade, "dataset": label, "split": split} for trade in pnl.get("trades", [])]
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
        "status_counts": pnl.get("status_counts", {}),
        "benchmark": benchmark_for_bars(bar_path),
        "trades": trades,
    }


def aggregate_scenario(
    scenario_def: dict[str, Any],
    datasets: list[dict[str, Any]],
    mapping_rows: list[dict[str, Any]],
    trial_index: int,
) -> dict[str, Any]:
    trades = sorted([trade for dataset in datasets for trade in dataset["trades"]], key=lambda row: (row.get("date", ""), row.get("dataset", "")))
    closed = [trade for trade in trades if str(trade.get("status", "")).startswith("closed_")]
    metrics = metrics_for_closed_trades(closed)
    metrics["average_ev_per_trade"] = metrics["average_trade_pnl"]
    mapping_summary = summarize_mapping(mapping_rows)
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
        "mapping_summary": mapping_summary,
        "big_day_dependency": summarize_pnl(closed, scenario_def["fee_per_contract"], scenario_def["fill_model"], scenario_def["close_fallback"], scenario_def["exit_model"])["big_day_dependency"],
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


def summarize_mapping(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"mapped_candidate_days": 0, "gap_tolerance_breach_rate": None}
    return {
        "mapped_candidate_days": len(rows),
        "mapping_method": "nearest_discrete_strike_rounding",
        "interpolation_used": False,
        "average_realized_long_gap": round(sum(float(row["realized_long_gap"]) for row in rows) / len(rows), 6),
        "average_abs_gap_error": round(sum(abs(float(row["realized_gap_error"])) for row in rows) / len(rows), 6),
        "gap_tolerance": GAP_TOLERANCE,
        "gap_tolerance_breach_count": sum(1 for row in rows if row["gap_tolerance_breached"]),
        "gap_tolerance_breach_rate": round(sum(1 for row in rows if row["gap_tolerance_breached"]) / len(rows), 6),
        "average_realized_width": round(sum(float(row["realized_width"]) for row in rows) / len(rows), 6),
        "min_long_moneyness": min(row["long_moneyness"] for row in rows),
        "max_long_moneyness": max(row["long_moneyness"] for row in rows),
    }


def aggregate_experiment(
    scenario_results: list[dict[str, Any]],
    scenarios: list[dict[str, Any]],
    search_log_path: Path,
) -> dict[str, Any]:
    best = max(scenario_results, key=lambda row: row["metrics"]["total_implementable_pnl"])
    worst = min(scenario_results, key=lambda row: row["metrics"]["total_implementable_pnl"])
    return {
        "record_type": "experiment_summary",
        "schema_version": "m5_strike_selection_v1",
        "experiment_id": "m5_strike_selection_sensitivity",
        "status": "complete_with_delta_blocker",
        "conclusion": "ยังสรุปไม่ได้",
        "conclusion_reason": "Moneyness/target-gap scenarios can be evaluated on current real data, but delta-based selection is blocked because normalized option quotes do not contain Greeks.",
        "research_log_required": True,
        "research_log_slug": "higanbana-strike-selection-sensitivity-real-data",
        "methodology": {
            "scope": "Sub-System A ORB directional debit vertical on current real-data artifacts only.",
            "data_policy": "No new paid data was downloaded for this experiment.",
            "strike_mapping": "nearest_discrete_strike_rounding; no interpolation; long strike maps from target breakout-to-long gap to the nearest tradable SPY 0DTE strike in the breakout direction.",
            "delta_policy": "Delta selection is not run because the current normalized Databento option_quote records contain no delta, implied volatility, or Greeks fields. No proxy delta is substituted.",
            "chronological_policy": "2023-03-01..2023-12-29 in-sample, 2024-01-02..2024-12-31 OOS; no OOS tuning from this report.",
            "selection_policy": "Best/worst scenarios are diagnostic only. No production strike rule is selected from this under-sampled grid.",
        },
        "scenario_count": len(scenario_results),
        "parameter_grid": parameter_grid(scenarios),
        "search_log": search_log_metadata(scenario_results, search_log_path),
        "dsr_assessment": dsr_assessment(scenario_results),
        "delta_selection_assessment": delta_selection_assessment(),
        "best_diagnostic_scenario": compact_scenario(best),
        "worst_diagnostic_scenario": compact_scenario(worst),
        "sample_adequacy": sample_adequacy_labels(max(row["closed_trades"] for row in scenario_results)),
        "scenarios": [strip_heavy_fields(row) for row in scenario_results],
    }


def delta_selection_assessment() -> dict[str, Any]:
    return {
        "status": "blocked_missing_greeks",
        "reason": "Current normalized option_quote artifacts contain strike, bid, ask, sizes, timestamps, and symbols, but no delta, gamma, implied volatility, or model inputs needed for a defensible delta selection rule.",
        "proxy_used": False,
        "required_before_delta_experiment": [
            "provider Greeks at decision timestamp, or",
            "approved point-in-time implied-volatility model with documented inputs and validation",
        ],
    }


def parameter_grid(scenarios: list[dict[str, Any]]) -> dict[str, list[Any]]:
    return {
        "selection_family": sorted({scenario["selection_family"] for scenario in scenarios}),
        "target_gap": [scenario["target_gap"] for scenario in scenarios],
        "width": sorted({scenario["width"] for scenario in scenarios}),
        "fill_model": sorted({scenario["fill_model"] for scenario in scenarios}),
        "fee_per_contract": sorted({scenario["fee_per_contract"] for scenario in scenarios}),
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
        "experiment_id": "m5_strike_selection_sensitivity",
        "trial_index": row["trial_index"],
        "scenario_id": row["scenario_id"],
        "parameters": {
            "selection_family": row["selection_family"],
            "target_gap": row["target_gap"],
            "width": row["width"],
            "fee_per_contract": row["fee_per_contract"],
            "fill_model": row["fill_model"],
        },
        "metrics": row["metrics"],
        "mapping_summary": row["mapping_summary"],
        "sample_adequacy": row["sample_adequacy"],
    }


def search_log_metadata(rows: list[dict[str, Any]], path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "record_type": "parameter_search_trial",
        "trial_count": len(rows),
        "all_trials_recorded": True,
        "selection_bias_warning": "The grid is diagnostic. Do not select production strike rules from this under-sampled output.",
    }


def dsr_assessment(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "status": "blocked_under_sampled",
        "reason": "DSR is recorded as a blocker because this is a multi-scenario diagnostic grid, all scenarios are under-sampled, and no production strike rule is selected.",
        "trial_count": len(rows),
        "selected_metric": "total_implementable_pnl",
        "required_before_acceptance": [
            "acceptance-grade return distribution",
            "effective number of independent trials",
            "null Sharpe threshold",
            "skew/kurtosis/autocorrelation diagnostics",
        ],
    }


def compact_scenario(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "scenario_id": row["scenario_id"],
        "target_gap": row["target_gap"],
        "closed_trades": row["closed_trades"],
        "skipped_trades": row["skipped_trades"],
        "metrics": row["metrics"],
        "mapping_summary": row["mapping_summary"],
    }


def strip_heavy_fields(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key not in {"trades", "daily_pnl"}}


def write_component_summaries(rows: list[dict[str, Any]]) -> None:
    COMPONENT_ROOT.mkdir(parents=True, exist_ok=True)
    for row in rows:
        path = COMPONENT_ROOT / f"{row['scenario_id']}_summary.json"
        path.write_text(json.dumps(strip_heavy_fields(row), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def group_quotes_by_timestamp(quotes: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for quote in quotes:
        grouped.setdefault(quote["quote_timestamp_et"], []).append(quote)
    return grouped


def merge_counts(items: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        for key, value in item.items():
            counts[key] = counts.get(key, 0) + int(value)
    return dict(sorted(counts.items()))


def mid_price(quote: dict[str, Any]) -> float:
    return round((float(quote["bid"]) + float(quote["ask"])) / 2, 4)


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# M5.2 Strike Selection Sensitivity",
        "",
        "## Status",
        f"- Conclusion: {result['conclusion']}",
        f"- Reason: {result['conclusion_reason']}",
        "- Evidence type: real-data deterministic strike-selection sensitivity, diagnostic only.",
        "- No new paid data was downloaded.",
        "",
        "## Methodology",
        "```json",
        json.dumps(result["methodology"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Delta Selection Assessment",
        "```json",
        json.dumps(result["delta_selection_assessment"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Search Log And DSR",
        f"- Search log: `{result['search_log']['path']}`",
        f"- Trial count: {result['search_log']['trial_count']}",
        f"- DSR status: `{result['dsr_assessment']['status']}`",
        f"- DSR reason: {result['dsr_assessment']['reason']}",
        "",
        "## Scenario Summary",
        "| Scenario | Target gap | Closed | Skipped | EV/trade | Implementable PnL | Cost Drag | OOS PnL | MDD | Avg gap | Breach rate |",
        "|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|",
    ]
    for row in result["scenarios"]:
        metrics = row["metrics"]
        mapping = row["mapping_summary"]
        oos = row["splits"]["oos"]["metrics"]
        lines.append(
            f"| `{row['scenario_id']}` | {row['target_gap']} | {row['closed_trades']} | {row['skipped_trades']} | "
            f"{metrics['average_ev_per_trade']} | {metrics['total_implementable_pnl']} | {metrics['total_cost_drag']} | "
            f"{oos['total_implementable_pnl']} | {metrics['max_drawdown']} | {mapping['average_realized_long_gap']} | {mapping['gap_tolerance_breach_rate']} |"
        )
    lines.extend(
        [
            "",
            "## Best Diagnostic Scenario",
            "```json",
            json.dumps(result["best_diagnostic_scenario"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Sample Adequacy",
            "```json",
            json.dumps(result["sample_adequacy"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Interpretation",
            "- This report tests moneyness/target-gap mapping only. Delta selection is blocked, not approximated.",
            "- Nearest discrete strike rounding is explicit; no continuous moneyness interpolation is used.",
            "- Best and worst scenarios are reported for diagnosis only, not parameter selection.",
            "- The current sample remains too small for acceptance-grade strike-selection conclusions.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run M5.2 strike-selection sensitivity on current real-data artifacts.")
    parser.add_argument("--summary-path", type=Path, default=SUMMARY_PATH)
    parser.add_argument("--report-path", type=Path, default=REPORT_PATH)
    parser.add_argument("--search-log-path", type=Path, default=SEARCH_LOG_PATH)
    args = parser.parse_args(argv)
    result = run_experiment(args.summary_path, args.report_path, args.search_log_path)
    print(json.dumps({key: value for key, value in result.items() if key != "scenarios"}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
