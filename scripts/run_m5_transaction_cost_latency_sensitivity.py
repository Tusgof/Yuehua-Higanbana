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
SUMMARY_PATH = REPORT_ROOT / "m5_transaction_cost_latency_sensitivity_summary.json"
REPORT_PATH = REPORT_ROOT / "m5_transaction_cost_latency_sensitivity_report.md"
SEARCH_LOG_PATH = REPORT_ROOT / "search_logs" / "m5_transaction_cost_latency_sensitivity_search_log.jsonl"
COMPONENT_ROOT = REPORT_ROOT / "m5_transaction_cost_latency_components"


def default_scenarios() -> list[dict[str, Any]]:
    return [
        scenario("mid_fee_0_latency_0_control", "mid", 0.0, 0),
        scenario("mid_fee_0_latency_2_control", "mid", 0.0, 2),
        scenario("half_spread_fee_064_latency_0_baseline", "half_spread", 0.64, 0),
        scenario("half_spread_fee_064_latency_1", "half_spread", 0.64, 1),
        scenario("half_spread_fee_064_latency_2", "half_spread", 0.64, 2),
        scenario("half_spread_fee_100_latency_0", "half_spread", 1.0, 0),
        scenario("full_spread_stress_fee_064_latency_0", "full_spread_stress", 0.64, 0),
        scenario("full_spread_stress_fee_100_latency_1", "full_spread_stress", 1.0, 1),
    ]


def scenario(scenario_id: str, fill_model: str, fee_per_contract: float, entry_latency_minutes: int) -> dict[str, Any]:
    return {
        "scenario_id": scenario_id,
        "fill_model": fill_model,
        "fee_per_contract": fee_per_contract,
        "entry_latency_minutes": entry_latency_minutes,
        "close_fallback": "nearest_1545_window",
        "exit_model": "forced_close_only",
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
                evaluate_candidate_day(
                    day,
                    quotes_by_key,
                    item["fee_per_contract"],
                    item["fill_model"],
                    item["close_fallback"],
                    item["exit_model"],
                    item["entry_latency_minutes"],
                )
                for day in candidate_days
            ]
            pnl = summarize_pnl(
                rows,
                item["fee_per_contract"],
                item["fill_model"],
                item["close_fallback"],
                item["exit_model"],
                item["entry_latency_minutes"],
            )
            scenario_datasets[item["scenario_id"]].append(dataset_summary(label, split, adapter_path, quote_path, bar_path, pnl))

    scenario_results = [
        aggregate_scenario(item, scenario_datasets[item["scenario_id"]], trial_index)
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


def aggregate_scenario(scenario_def: dict[str, Any], datasets: list[dict[str, Any]], trial_index: int) -> dict[str, Any]:
    trades = sorted([trade for dataset in datasets for trade in dataset["trades"]], key=lambda row: (row.get("date", ""), row.get("dataset", "")))
    closed = [trade for trade in trades if str(trade.get("status", "")).startswith("closed_")]
    split_results = {split: split_summary(split, datasets, closed) for split in ("in_sample", "oos")}
    metrics = metrics_for_closed_trades(closed)
    metrics["friction_drag_ratio"] = friction_drag_ratio(metrics["total_mid_pnl"], metrics["total_cost_drag"])
    return {
        "trial_index": trial_index,
        **scenario_def,
        "candidate_days": sum(dataset["candidate_days"] for dataset in datasets),
        "closed_trades": len(closed),
        "skipped_trades": sum(dataset["skipped_trades"] for dataset in datasets),
        "status_counts": merge_counts(dataset["status_counts"] for dataset in datasets),
        "sample_adequacy": sample_adequacy_labels(len(closed)),
        "metrics": metrics,
        "splits": split_results,
        "big_day_dependency": summarize_pnl(
            closed,
            scenario_def["fee_per_contract"],
            scenario_def["fill_model"],
            scenario_def["close_fallback"],
            scenario_def["exit_model"],
            scenario_def["entry_latency_minutes"],
        )["big_day_dependency"],
        "daily_pnl": daily_pnl_rows(closed),
        "datasets": [{key: value for key, value in dataset.items() if key != "trades"} for dataset in datasets],
        "trades": closed,
    }


def split_summary(split: str, datasets: list[dict[str, Any]], closed: list[dict[str, Any]]) -> dict[str, Any]:
    split_datasets = [dataset for dataset in datasets if dataset["split"] == split]
    split_closed = [trade for trade in closed if trade.get("split") == split]
    metrics = metrics_for_closed_trades(split_closed)
    metrics["friction_drag_ratio"] = friction_drag_ratio(metrics["total_mid_pnl"], metrics["total_cost_drag"])
    return {
        "dataset_count": len(split_datasets),
        "candidate_days": sum(dataset["candidate_days"] for dataset in split_datasets),
        "closed_trades": len(split_closed),
        "skipped_trades": sum(dataset["skipped_trades"] for dataset in split_datasets),
        "metrics": metrics,
        "sample_adequacy": sample_adequacy_labels(len(split_closed)),
    }


def aggregate_experiment(
    scenario_results: list[dict[str, Any]],
    scenarios: list[dict[str, Any]],
    search_log_path: Path,
) -> dict[str, Any]:
    baseline = next(row for row in scenario_results if row["scenario_id"] == "half_spread_fee_064_latency_0_baseline")
    best = max(scenario_results, key=lambda row: row["metrics"]["total_implementable_pnl"])
    worst = min(scenario_results, key=lambda row: row["metrics"]["total_implementable_pnl"])
    return {
        "record_type": "experiment_summary",
        "schema_version": "m5_transaction_cost_latency_v1",
        "experiment_id": "m5_transaction_cost_latency_sensitivity",
        "status": "complete",
        "conclusion": "ยังสรุปไม่ได้",
        "conclusion_reason": "The sensitivity run is useful for diagnosing cost and latency fragility, but all scenarios remain under-sampled and underpowered.",
        "research_log_required": True,
        "research_log_slug": "higanbana-transaction-cost-latency-sensitivity-real-data",
        "methodology": {
            "scope": "Sub-System A ORB directional debit vertical on current real-data artifacts only.",
            "data_policy": "No new paid data was downloaded for this experiment.",
            "chronological_policy": "2023-03-01..2023-12-29 in-sample, 2024-01-02..2024-12-31 OOS; no OOS tuning from this report.",
            "entry_policy": "Entry market orders remain prohibited; latency scenarios require complete delayed-entry quotes or skip the trade.",
            "exit_policy": "Forced close only, nearest 15:45 fallback may use 15:44..15:40 quotes only and never after 15:45 ET.",
            "selection_policy": "No production scenario is selected from this grid; best/worst are diagnostic only.",
        },
        "scenario_count": len(scenario_results),
        "parameter_grid": parameter_grid(scenarios),
        "search_log": search_log_metadata(scenario_results, search_log_path),
        "dsr_assessment": dsr_assessment(scenario_results),
        "baseline_scenario": compact_scenario(baseline),
        "best_diagnostic_scenario": compact_scenario(best),
        "worst_diagnostic_scenario": compact_scenario(worst),
        "sample_adequacy": sample_adequacy_labels(max(row["closed_trades"] for row in scenario_results)),
        "scenarios": [strip_heavy_fields(row) for row in scenario_results],
    }


def parameter_grid(scenarios: list[dict[str, Any]]) -> dict[str, list[Any]]:
    return {
        "fill_model": sorted({scenario["fill_model"] for scenario in scenarios}),
        "fee_per_contract": sorted({scenario["fee_per_contract"] for scenario in scenarios}),
        "entry_latency_minutes": sorted({scenario["entry_latency_minutes"] for scenario in scenarios}),
        "close_fallback": sorted({scenario["close_fallback"] for scenario in scenarios}),
        "exit_model": sorted({scenario["exit_model"] for scenario in scenarios}),
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
        "experiment_id": "m5_transaction_cost_latency_sensitivity",
        "trial_index": row["trial_index"],
        "scenario_id": row["scenario_id"],
        "parameters": {
            "fill_model": row["fill_model"],
            "fee_per_contract": row["fee_per_contract"],
            "entry_latency_minutes": row["entry_latency_minutes"],
            "close_fallback": row["close_fallback"],
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
        "selection_bias_warning": "The grid is diagnostic. Do not select production parameters from this under-sampled output.",
    }


def dsr_assessment(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "status": "blocked_under_sampled",
        "reason": "DSR is recorded as a blocker because this is a multi-scenario diagnostic grid, all scenarios are under-sampled, and no production parameter is selected.",
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
        "fill_model": row["fill_model"],
        "fee_per_contract": row["fee_per_contract"],
        "entry_latency_minutes": row["entry_latency_minutes"],
        "closed_trades": row["closed_trades"],
        "skipped_trades": row["skipped_trades"],
        "metrics": row["metrics"],
    }


def strip_heavy_fields(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key not in {"trades", "daily_pnl"}}


def write_component_summaries(rows: list[dict[str, Any]]) -> None:
    COMPONENT_ROOT.mkdir(parents=True, exist_ok=True)
    for row in rows:
        path = COMPONENT_ROOT / f"{row['scenario_id']}_summary.json"
        path.write_text(json.dumps(strip_heavy_fields(row), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def merge_counts(items: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        for key, value in item.items():
            counts[key] = counts.get(key, 0) + int(value)
    return dict(sorted(counts.items()))


def friction_drag_ratio(mid_pnl: float, cost_drag: float) -> float | None:
    if mid_pnl == 0:
        return None
    return round(cost_drag / abs(mid_pnl), 6)


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# M5.1 Transaction Cost And Execution Latency Sensitivity",
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
        "| Scenario | Fill | Fee | Latency | Closed | Skipped | Mid PnL | Implementable PnL | Cost Drag | Drag Ratio | OOS PnL | MDD |",
        "|:--|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|",
    ]
    for row in result["scenarios"]:
        metrics = row["metrics"]
        oos = row["splits"]["oos"]["metrics"]
        lines.append(
            f"| `{row['scenario_id']}` | `{row['fill_model']}` | {row['fee_per_contract']} | {row['entry_latency_minutes']} | "
            f"{row['closed_trades']} | {row['skipped_trades']} | {metrics['total_mid_pnl']} | {metrics['total_implementable_pnl']} | "
            f"{metrics['total_cost_drag']} | {metrics['friction_drag_ratio']} | {oos['total_implementable_pnl']} | {metrics['max_drawdown']} |"
        )
    lines.extend(
        [
            "",
            "## Baseline Scenario",
            "```json",
            json.dumps(result["baseline_scenario"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Sample Adequacy",
            "```json",
            json.dumps(result["sample_adequacy"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Interpretation",
            "- Mid PnL is only a control. Deployable interpretation must use implementable PnL.",
            "- Latency scenarios skip trades when delayed-entry quotes are missing; they do not invent prices.",
            "- Best and worst scenarios are reported for diagnosis only, not parameter selection.",
            "- The current sample remains too small for acceptance-grade cost or latency conclusions.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run M5.1 transaction-cost and entry-latency sensitivity on current real-data artifacts.")
    parser.add_argument("--summary-path", type=Path, default=SUMMARY_PATH)
    parser.add_argument("--report-path", type=Path, default=REPORT_PATH)
    parser.add_argument("--search-log-path", type=Path, default=SEARCH_LOG_PATH)
    args = parser.parse_args(argv)
    result = run_experiment(args.summary_path, args.report_path, args.search_log_path)
    print(json.dumps({key: value for key, value in result.items() if key != "scenarios"}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
