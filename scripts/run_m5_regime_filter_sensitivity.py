from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from run_jan2024_pilot_pnl import evaluate_candidate_day, index_quotes, load_jsonl, sample_adequacy_labels, summarize_pnl
from run_m4_subsystem_a_baseline import DATASETS, benchmark_for_bars, daily_pnl_rows, metrics_for_closed_trades


REPORT_ROOT = PROJECT_ROOT / "reports" / "experiments"
SUMMARY_PATH = REPORT_ROOT / "m5_regime_filter_sensitivity_summary.json"
REPORT_PATH = REPORT_ROOT / "m5_regime_filter_sensitivity_report.md"
SEARCH_LOG_PATH = REPORT_ROOT / "search_logs" / "m5_regime_filter_sensitivity_search_log.jsonl"
COMPONENT_ROOT = REPORT_ROOT / "m5_regime_filter_components"
VIX_PATH = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "vix_vxv" / "vix_vxv.jsonl"
MACRO_PATH = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "macro_calendar" / "macro_event.jsonl"

FEE_PER_CONTRACT = 0.64
FILL_MODEL = "half_spread"
CLOSE_FALLBACK = "nearest_1545_window"
EXIT_MODEL = "forced_close_only"
MAJOR_MACRO_TYPES = {"CPI", "NFP", "PCE", "FOMC_DECISION", "FOMC_MINUTES"}


def default_scenarios() -> list[dict[str, Any]]:
    return [
        scenario("unfiltered_control"),
        scenario("vix_15_25_prev_close", vix_min=15.0, vix_max=25.0),
        scenario("vix_below_25_prev_close", vix_max=25.0),
        scenario("vix_below_30_prev_close", vix_max=30.0),
        scenario("term_structure_not_inverted_prev_close", require_non_inverted_term=True),
        scenario("vix_15_25_and_non_inverted_prev_close", vix_min=15.0, vix_max=25.0, require_non_inverted_term=True),
        scenario("exclude_high_importance_macro_same_day", exclude_high_importance_macro=True),
        scenario("exclude_major_macro_same_day", exclude_event_types=sorted(MAJOR_MACRO_TYPES)),
        scenario(
            "vix_15_25_non_inverted_exclude_major_macro",
            vix_min=15.0,
            vix_max=25.0,
            require_non_inverted_term=True,
            exclude_event_types=sorted(MAJOR_MACRO_TYPES),
        ),
    ]


def scenario(
    scenario_id: str,
    vix_min: float | None = None,
    vix_max: float | None = None,
    require_non_inverted_term: bool = False,
    exclude_high_importance_macro: bool = False,
    exclude_event_types: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "scenario_id": scenario_id,
        "vix_min": vix_min,
        "vix_max": vix_max,
        "require_non_inverted_term": require_non_inverted_term,
        "exclude_high_importance_macro": exclude_high_importance_macro,
        "exclude_event_types": exclude_event_types or [],
        "vix_timestamp_policy": "previous_available_close_before_trade_date",
        "macro_timestamp_policy": "scheduled_same_day_known_before_entry",
        "fill_model": FILL_MODEL,
        "fee_per_contract": FEE_PER_CONTRACT,
        "close_fallback": CLOSE_FALLBACK,
        "exit_model": EXIT_MODEL,
    }


def run_experiment(
    summary_path: Path = SUMMARY_PATH,
    report_path: Path = REPORT_PATH,
    search_log_path: Path = SEARCH_LOG_PATH,
    vix_path: Path = VIX_PATH,
    macro_path: Path = MACRO_PATH,
) -> dict[str, Any]:
    scenarios = default_scenarios()
    vix_rows = load_vix_vxv(vix_path)
    macro_by_date = load_macro_events_by_date(macro_path)
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
                evaluate_candidate_day_with_filter(day, quotes_by_key, item, vix_rows, macro_by_date)
                for day in candidate_days
            ]
            pnl = summarize_pnl(rows, FEE_PER_CONTRACT, FILL_MODEL, CLOSE_FALLBACK, EXIT_MODEL, 0)
            scenario_datasets[item["scenario_id"]].append(dataset_summary(label, split, adapter_path, quote_path, bar_path, pnl))

    scenario_results = [
        aggregate_scenario(item, scenario_datasets[item["scenario_id"]], trial_index)
        for trial_index, item in enumerate(scenarios, start=1)
    ]
    write_component_summaries(scenario_results)
    write_search_log(scenario_results, search_log_path)
    result = aggregate_experiment(scenario_results, search_log_path, vix_path, macro_path)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(render_report(result), encoding="utf-8")
    return result


def evaluate_candidate_day_with_filter(
    day: dict[str, Any],
    quotes_by_key: dict[tuple[str, str, float, str], dict[str, Any]],
    scenario_def: dict[str, Any],
    vix_rows: list[dict[str, Any]],
    macro_by_date: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    trade_date = day["date"]
    decision = filter_decision(trade_date, scenario_def, vix_rows, macro_by_date)
    if not decision["allow"]:
        return {
            "date": trade_date,
            "status": "filtered_out",
            "direction": day.get("direction"),
            "scenario_id": scenario_def["scenario_id"],
            "filter_decision": decision,
            "reasons": decision["reasons"],
        }
    row = evaluate_candidate_day(day, quotes_by_key, FEE_PER_CONTRACT, FILL_MODEL, CLOSE_FALLBACK, EXIT_MODEL, 0)
    row["scenario_id"] = scenario_def["scenario_id"]
    row["filter_decision"] = decision
    return row


def filter_decision(
    trade_date: str,
    scenario_def: dict[str, Any],
    vix_rows: list[dict[str, Any]],
    macro_by_date: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    reasons = []
    vix_record = previous_vix_record(trade_date, vix_rows)
    macro_events = macro_by_date.get(trade_date, [])
    allow = True

    if scenario_def["vix_min"] is not None or scenario_def["vix_max"] is not None or scenario_def["require_non_inverted_term"]:
        if vix_record is None:
            return {"allow": False, "reasons": ["missing previous VIX/VXV record"], "vix_record": None, "macro_events": macro_events}
        vix_close = float(vix_record["vix_close"])
        vxv_close = float(vix_record["vxv_close"])
        if scenario_def["vix_min"] is not None and vix_close < float(scenario_def["vix_min"]):
            allow = False
            reasons.append(f"previous VIX {vix_close} below {scenario_def['vix_min']}")
        if scenario_def["vix_max"] is not None and vix_close > float(scenario_def["vix_max"]):
            allow = False
            reasons.append(f"previous VIX {vix_close} above {scenario_def['vix_max']}")
        if scenario_def["require_non_inverted_term"] and vix_close >= vxv_close:
            allow = False
            reasons.append(f"previous VIX/VXV inverted: {vix_close}/{vxv_close}")

    if scenario_def["exclude_high_importance_macro"]:
        high_events = [event for event in macro_events if event.get("importance") == "high"]
        if high_events:
            allow = False
            reasons.append("same-day high-importance macro event: " + ",".join(sorted({event["event_type"] for event in high_events})))

    excluded_types = set(scenario_def["exclude_event_types"])
    excluded_events = [event for event in macro_events if event.get("event_type") in excluded_types]
    if excluded_events:
        allow = False
        reasons.append("same-day excluded macro event: " + ",".join(sorted({event["event_type"] for event in excluded_events})))

    if allow:
        reasons.append("filter allows trade")
    return {"allow": allow, "reasons": reasons, "vix_record": vix_record, "macro_events": macro_events}


def load_vix_vxv(path: Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return sorted(rows, key=lambda row: row["date"])


def previous_vix_record(trade_date: str, rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    target = date.fromisoformat(trade_date)
    candidates = [row for row in rows if date.fromisoformat(row["date"]) < target]
    return candidates[-1] if candidates else None


def load_macro_events_by_date(path: Path) -> dict[str, list[dict[str, Any]]]:
    events: dict[str, list[dict[str, Any]]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("record_type") != "macro_event":
            continue
        event_date = str(record["event_timestamp_et"])[:10]
        events.setdefault(event_date, []).append(record)
    return {key: sorted(value, key=lambda row: row["event_timestamp_et"]) for key, value in events.items()}


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
        "filtered_out_trades": sum(1 for row in trades if row.get("status") == "filtered_out"),
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
    metrics = metrics_for_closed_trades(closed)
    metrics["filter_retention_rate"] = round(len(closed) / sum(dataset["candidate_days"] for dataset in datasets), 6) if datasets else 0.0
    return {
        "trial_index": trial_index,
        **scenario_def,
        "candidate_days_before_filter": sum(dataset["candidate_days"] for dataset in datasets),
        "closed_trades": len(closed),
        "skipped_trades": sum(dataset["skipped_trades"] for dataset in datasets),
        "filtered_out_trades": sum(dataset["filtered_out_trades"] for dataset in datasets),
        "status_counts": merge_counts(dataset["status_counts"] for dataset in datasets),
        "sample_adequacy": sample_adequacy_labels(len(closed)),
        "metrics": metrics,
        "splits": {split: split_summary(split, datasets, closed) for split in ("in_sample", "oos")},
        "big_day_dependency": summarize_pnl(closed, FEE_PER_CONTRACT, FILL_MODEL, CLOSE_FALLBACK, EXIT_MODEL, 0)["big_day_dependency"],
        "daily_pnl": daily_pnl_rows(closed),
        "datasets": [{key: value for key, value in dataset.items() if key != "trades"} for dataset in datasets],
        "trades": closed,
    }


def split_summary(split: str, datasets: list[dict[str, Any]], closed: list[dict[str, Any]]) -> dict[str, Any]:
    split_datasets = [dataset for dataset in datasets if dataset["split"] == split]
    split_closed = [trade for trade in closed if trade.get("split") == split]
    candidate_count = sum(dataset["candidate_days"] for dataset in split_datasets)
    metrics = metrics_for_closed_trades(split_closed)
    metrics["filter_retention_rate"] = round(len(split_closed) / candidate_count, 6) if candidate_count else 0.0
    return {
        "dataset_count": len(split_datasets),
        "candidate_days_before_filter": candidate_count,
        "closed_trades": len(split_closed),
        "skipped_trades": sum(dataset["skipped_trades"] for dataset in split_datasets),
        "filtered_out_trades": sum(dataset["filtered_out_trades"] for dataset in split_datasets),
        "metrics": metrics,
        "sample_adequacy": sample_adequacy_labels(len(split_closed)),
    }


def aggregate_experiment(rows: list[dict[str, Any]], search_log_path: Path, vix_path: Path, macro_path: Path) -> dict[str, Any]:
    baseline = next(row for row in rows if row["scenario_id"] == "unfiltered_control")
    best = max(rows, key=lambda row: row["metrics"]["total_implementable_pnl"])
    worst = min(rows, key=lambda row: row["metrics"]["total_implementable_pnl"])
    return {
        "record_type": "experiment_summary",
        "schema_version": "m5_regime_filter_sensitivity_v1",
        "experiment_id": "m5_regime_filter_sensitivity",
        "status": "complete",
        "conclusion": "ยังสรุปไม่ได้",
        "conclusion_reason": "VIX/VXV and macro filters are measurable on current real data, but all filtered scenarios remain under-sampled and underpowered. NOVI/net-gamma remains blocked because required inputs are missing.",
        "research_log_required": True,
        "research_log_slug": "higanbana-regime-filter-sensitivity-real-data",
        "methodology": {
            "scope": "Sub-System A ORB directional debit vertical on current real-data artifacts only.",
            "data_policy": "No new paid data was downloaded for this experiment.",
            "chronological_policy": "2023-03-01..2023-12-29 in-sample, 2024-01-02..2024-12-31 OOS; no OOS tuning from this report.",
            "vix_policy": "Use previous available Cboe VIX/VIX3M close before the trade date, never same-day close before market open.",
            "macro_policy": "Use official scheduled same-day macro events as ex-ante known calendar blockers.",
            "novi_net_gamma_policy": "Blocked. Current normalized option quotes do not include Greeks, open interest, dealer inventory, or position reconstruction inputs.",
            "selection_policy": "Best/worst scenarios are diagnostic only. Do not select production filters from this under-sampled grid.",
        },
        "input_paths": {"vix_vxv": str(vix_path), "macro_calendar": str(macro_path)},
        "scenario_count": len(rows),
        "parameter_grid": parameter_grid(rows),
        "search_log": search_log_metadata(rows, search_log_path),
        "dsr_assessment": dsr_assessment(rows),
        "novi_net_gamma_blocker": novi_net_gamma_blocker(),
        "baseline_scenario": compact_scenario(baseline),
        "best_diagnostic_scenario": compact_scenario(best),
        "worst_diagnostic_scenario": compact_scenario(worst),
        "sample_adequacy": sample_adequacy_labels(max(row["closed_trades"] for row in rows)),
        "scenarios": [strip_heavy_fields(row) for row in rows],
    }


def parameter_grid(rows: list[dict[str, Any]]) -> dict[str, list[Any]]:
    return {
        "vix_min": sorted({row["vix_min"] for row in rows}, key=lambda value: (-999.0 if value is None else value)),
        "vix_max": sorted({row["vix_max"] for row in rows}, key=lambda value: (-999.0 if value is None else value)),
        "require_non_inverted_term": sorted({row["require_non_inverted_term"] for row in rows}),
        "exclude_high_importance_macro": sorted({row["exclude_high_importance_macro"] for row in rows}),
        "exclude_event_types": [row["exclude_event_types"] for row in rows],
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
        "experiment_id": "m5_regime_filter_sensitivity",
        "trial_index": row["trial_index"],
        "scenario_id": row["scenario_id"],
        "parameters": {
            "vix_min": row["vix_min"],
            "vix_max": row["vix_max"],
            "require_non_inverted_term": row["require_non_inverted_term"],
            "exclude_high_importance_macro": row["exclude_high_importance_macro"],
            "exclude_event_types": row["exclude_event_types"],
            "vix_timestamp_policy": row["vix_timestamp_policy"],
            "macro_timestamp_policy": row["macro_timestamp_policy"],
        },
        "candidate_days_before_filter": row["candidate_days_before_filter"],
        "filtered_out_trades": row["filtered_out_trades"],
        "closed_trades": row["closed_trades"],
        "metrics": row["metrics"],
        "sample_adequacy": row["sample_adequacy"],
    }


def search_log_metadata(rows: list[dict[str, Any]], path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "record_type": "parameter_search_trial",
        "trial_count": len(rows),
        "all_trials_recorded": True,
        "selection_bias_warning": "The filter grid is diagnostic. Do not select production filters from this under-sampled output.",
    }


def dsr_assessment(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "status": "blocked_under_sampled",
        "reason": "DSR is blocked because this is a multi-scenario filter grid, all scenarios are under-sampled, and no production regime filter is selected.",
        "trial_count": len(rows),
        "selected_metric": "total_implementable_pnl",
        "required_before_acceptance": [
            "acceptance-grade filtered return distribution",
            "effective number of independent filter trials",
            "null Sharpe threshold",
            "skew/kurtosis/autocorrelation diagnostics",
        ],
    }


def novi_net_gamma_blocker() -> dict[str, Any]:
    return {
        "status": "blocked_missing_inputs",
        "reason": "A defensible NOVI/net-gamma proxy needs option Greeks, open interest or position reconstruction, and a documented scaling convention. Current normalized option_quote artifacts contain bid/ask, sizes, timestamps, strikes, and rights, but not the required inventory/gamma inputs.",
        "required_inputs": ["gamma or model inputs to compute gamma", "open interest or position inventory", "contract multiplier/scaling convention", "decision-time availability policy"],
    }


def compact_scenario(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "scenario_id": row["scenario_id"],
        "candidate_days_before_filter": row["candidate_days_before_filter"],
        "filtered_out_trades": row["filtered_out_trades"],
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


def merge_counts(items: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        for key, value in item.items():
            counts[key] = counts.get(key, 0) + int(value)
    return dict(sorted(counts.items()))


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# M5.5 Regime Filter Sensitivity",
        "",
        "## Status",
        f"- Conclusion: {result['conclusion']}",
        f"- Reason: {result['conclusion_reason']}",
        "- Evidence type: real-data deterministic filter sensitivity, diagnostic only.",
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
        "## NOVI / Net-Gamma Blocker",
        "```json",
        json.dumps(result["novi_net_gamma_blocker"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Scenario Summary",
        "| Scenario | Candidates | Filtered | Closed | Retention | Mid PnL | Implementable PnL | Cost Drag | OOS PnL | ES95 | ES99 | MDD | Labels |",
        "|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|:--|",
    ]
    for row in result["scenarios"]:
        metrics = row["metrics"]
        oos = row["splits"]["oos"]["metrics"]
        labels = ",".join(row["sample_adequacy"]["labels"])
        lines.append(
            f"| `{row['scenario_id']}` | {row['candidate_days_before_filter']} | {row['filtered_out_trades']} | {row['closed_trades']} | "
            f"{metrics['filter_retention_rate']} | {metrics['total_mid_pnl']} | {metrics['total_implementable_pnl']} | "
            f"{metrics['total_cost_drag']} | {oos['total_implementable_pnl']} | {metrics['es95']} | {metrics['es99']} | "
            f"{metrics['max_drawdown']} | `{labels}` |"
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
            "- VIX/VXV filters use prior close only, so they are available before the entry decision.",
            "- Macro filters use scheduled same-day event dates, not realized post-event outcomes.",
            "- All filtered results shrink an already small sample, so they remain diagnostic.",
            "- NOVI/net-gamma is not tested because the current dataset lacks the inputs needed for a defensible proxy.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run M5.5 VIX/VXV and macro regime-filter sensitivity on current real-data artifacts.")
    parser.add_argument("--summary-path", type=Path, default=SUMMARY_PATH)
    parser.add_argument("--report-path", type=Path, default=REPORT_PATH)
    parser.add_argument("--search-log-path", type=Path, default=SEARCH_LOG_PATH)
    args = parser.parse_args(argv)
    result = run_experiment(args.summary_path, args.report_path, args.search_log_path)
    print(json.dumps({key: value for key, value in result.items() if key != "scenarios"}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
