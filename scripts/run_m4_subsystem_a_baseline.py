from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean, pstdev
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from run_jan2024_pilot_pnl import big_day_dependency_check, run_pilot_pnl, sample_adequacy_labels


REPORT_ROOT = PROJECT_ROOT / "reports" / "baselines"
COMPONENT_ROOT = REPORT_ROOT / "subsystem_a_components"
SUMMARY_PATH = REPORT_ROOT / "subsystem_a_orb_baseline_summary.json"
REPORT_PATH = REPORT_ROOT / "subsystem_a_orb_baseline_report.md"
FEE_PER_CONTRACT = 0.64
FILL_MODEL = "half_spread"
CLOSE_FALLBACK = "nearest_1545_window"
EXIT_MODEL = "forced_close_only"


DATASETS = [
    ("insample_2023_03", "in_sample", "mar_2023_pilot_adapter_summary.json", "insample_2023_03"),
    ("insample_2023_04", "in_sample", "apr_2023_pilot_adapter_summary.json", "insample_2023_04"),
    ("insample_2023_05", "in_sample", "may_2023_pilot_adapter_summary.json", "insample_2023_05"),
    ("insample_2023_06", "in_sample", "jun_2023_pilot_adapter_summary.json", "insample_2023_06"),
    ("insample_2023_07", "in_sample", "jul_2023_pilot_adapter_summary.json", "insample_2023_07"),
    ("insample_2023_08", "in_sample", "aug_2023_pilot_adapter_summary.json", "insample_2023_08"),
    ("insample_2023_09", "in_sample", "sep_2023_pilot_adapter_summary.json", "insample_2023_09"),
    ("insample_2023_10", "in_sample", "oct_2023_pilot_adapter_summary.json", "insample_2023_10"),
    ("insample_2023_11", "in_sample", "nov_2023_pilot_adapter_summary.json", "insample_2023_11"),
    ("insample_2023_12", "in_sample", "dec_2023_pilot_adapter_summary.json", "insample_2023_12"),
    ("oos_2024_01", "oos", "jan_2024_pilot_adapter_summary.json", "one_month_pilot"),
    ("oos_2024_02", "oos", "feb_2024_pilot_adapter_summary.json", "oos_2024_2025"),
    ("oos_2024_03", "oos", "mar_2024_pilot_adapter_summary.json", "oos_2024_03"),
    ("oos_2024_04", "oos", "apr_2024_pilot_adapter_summary.json", "oos_2024_04"),
    ("oos_2024_05", "oos", "may_2024_pilot_adapter_summary.json", "oos_2024_05"),
    ("oos_2024_06", "oos", "jun_2024_pilot_adapter_summary.json", "oos_2024_06"),
    ("oos_2024_07_partial", "oos", "jul_2024_partial_pilot_adapter_summary.json", "oos_2024_07_partial"),
    ("oos_2024_07_chunk3", "oos", "jul_2024_chunk3_pilot_adapter_summary.json", "oos_2024_07_intraday_exit_30m_chunk3"),
    ("oos_2024_07_chunk4", "oos", "jul_2024_chunk4_pilot_adapter_summary.json", "oos_2024_07_intraday_exit_30m_chunk4"),
    ("oos_2024_07_chunk5", "oos", "jul_2024_chunk5_pilot_adapter_summary.json", "oos_2024_07_intraday_exit_30m_chunk5"),
    ("oos_2024_08_chunk1", "oos", "aug_2024_chunk1_pilot_adapter_summary.json", "oos_2024_08_intraday_exit_30m_chunk1"),
    ("oos_2024_08_chunk2", "oos", "aug_2024_chunk2_pilot_adapter_summary.json", "oos_2024_08_intraday_exit_30m_chunk2"),
    ("oos_2024_08_chunk3", "oos", "aug_2024_chunk3_pilot_adapter_summary.json", "oos_2024_08_intraday_exit_30m_chunk3"),
    ("oos_2024_08_chunk4", "oos", "aug_2024_chunk4_pilot_adapter_summary.json", "oos_2024_08_intraday_exit_30m_chunk4"),
    ("oos_2024_08_chunk5", "oos", "aug_2024_chunk5_pilot_adapter_summary.json", "oos_2024_08_intraday_exit_30m_chunk5"),
    ("oos_2024_09_chunk1", "oos", "sep_2024_chunk1_pilot_adapter_summary.json", "oos_2024_09_intraday_exit_30m_chunk1"),
    ("oos_2024_09_chunk2", "oos", "sep_2024_chunk2_pilot_adapter_summary.json", "oos_2024_09_intraday_exit_30m_chunk2"),
    ("oos_2024_09_chunk3", "oos", "sep_2024_chunk3_pilot_adapter_summary.json", "oos_2024_09_intraday_exit_30m_chunk3"),
    ("oos_2024_09_remainder", "oos", "sep_2024_remainder_daily_union_pilot_adapter_summary.json", "oos_2024_09_remainder_daily_union"),
    ("oos_2024_10", "oos", "oct_2024_daily_union_pilot_adapter_summary.json", "oos_2024_10_daily_union"),
    ("oos_2024_11", "oos", "nov_2024_daily_union_pilot_adapter_summary.json", "oos_2024_11_daily_union"),
    ("oos_2024_12", "oos", "dec_2024_daily_union_pilot_adapter_summary.json", "oos_2024_12_daily_union"),
]


def run_baseline(summary_path: Path = SUMMARY_PATH, report_path: Path = REPORT_PATH) -> dict[str, Any]:
    COMPONENT_ROOT.mkdir(parents=True, exist_ok=True)
    dataset_results = []
    for label, split, adapter_name, normalized_name in DATASETS:
        adapter_path = PROJECT_ROOT / "reports" / "pilots" / adapter_name
        quote_path = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "databento" / normalized_name / "option_quote.jsonl"
        bar_path = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "databento" / normalized_name / "spy_bar.jsonl"
        component_summary_path = COMPONENT_ROOT / f"{label}_pnl_summary.json"
        component_report_path = COMPONENT_ROOT / f"{label}_pnl_report.md"
        pnl = run_pilot_pnl(
            adapter_summary_path=adapter_path,
            quote_path=quote_path,
            summary_path=component_summary_path,
            report_path=component_report_path,
            fee_per_contract=FEE_PER_CONTRACT,
            fill_model=FILL_MODEL,
            close_fallback=CLOSE_FALLBACK,
            exit_model=EXIT_MODEL,
        )
        dataset_results.append(dataset_summary(label, split, adapter_path, quote_path, bar_path, component_summary_path, pnl))

    summary = aggregate_baseline(dataset_results)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(render_report(summary), encoding="utf-8")
    return summary


def dataset_summary(
    label: str,
    split: str,
    adapter_path: Path,
    quote_path: Path,
    bar_path: Path,
    component_summary_path: Path,
    pnl: dict[str, Any],
) -> dict[str, Any]:
    trades = [{**trade, "dataset": label, "split": split} for trade in pnl.get("trades", [])]
    return {
        "label": label,
        "split": split,
        "adapter_path": str(adapter_path),
        "quote_path": str(quote_path),
        "bar_path": str(bar_path),
        "component_summary_path": str(component_summary_path),
        "coverage_start": coverage_from_adapter(adapter_path, "coverage_start"),
        "coverage_end": coverage_from_adapter(adapter_path, "coverage_end"),
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


def aggregate_baseline(datasets: list[dict[str, Any]]) -> dict[str, Any]:
    trades = sorted([trade for dataset in datasets for trade in dataset["trades"]], key=lambda row: (row.get("date", ""), row.get("dataset", "")))
    closed = [trade for trade in trades if str(trade.get("status", "")).startswith("closed_")]
    daily_pnl = daily_pnl_rows(closed)
    by_split = {split: split_summary(split, datasets, closed) for split in ("in_sample", "oos")}
    overall_metrics = metrics_for_closed_trades(closed)
    return {
        "record_type": "baseline_experiment_summary",
        "schema_version": "m4_subsystem_a_baseline_v1",
        "experiment_id": "m4_subsystem_a_orb_baseline",
        "strategy": "Sub-System A ORB directional debit vertical",
        "status": "complete",
        "conclusion": "ยังสรุปไม่ได้",
        "conclusion_reason": "The available real-data baseline remains under-sampled and underpowered, so it cannot support strategy acceptance.",
        "research_log_required": True,
        "research_log_slug": "higanbana-orb-baseline-real-data",
        "methodology": {
            "news_filter": "disabled",
            "llm_filter": "disabled",
            "entry_model": "limit-style entry priced by fill model; no entry market orders",
            "exit_model": EXIT_MODEL,
            "fill_model": FILL_MODEL,
            "close_fallback": CLOSE_FALLBACK,
            "fee_per_contract": FEE_PER_CONTRACT,
            "chronological_policy": "2023-03-01..2023-12-29 in-sample, 2024-01-02..2024-12-31 OOS; no OOS tuning from this report",
            "strike_mapping": "nearest discrete strike selection inherited from generated strategy legs",
        },
        "sample_adequacy": sample_adequacy_labels(len(closed)),
        "dsr_assessment": {
            "status": "not_applicable",
            "reason": "This baseline run does not select best parameters from a search grid.",
            "trial_count": 1,
        },
        "big_day_dependency": big_day_dependency_check(closed),
        "metrics": overall_metrics,
        "splits": by_split,
        "daily_pnl": daily_pnl,
        "datasets": [{key: value for key, value in dataset.items() if key != "trades"} for dataset in datasets],
    }


def split_summary(split: str, datasets: list[dict[str, Any]], closed: list[dict[str, Any]]) -> dict[str, Any]:
    split_datasets = [dataset for dataset in datasets if dataset["split"] == split]
    split_closed = [trade for trade in closed if trade.get("split") == split]
    benchmark_return = compound_return([dataset["benchmark"]["return"] for dataset in split_datasets if dataset["benchmark"]["return"] is not None])
    metrics = metrics_for_closed_trades(split_closed)
    metrics["benchmark_return"] = benchmark_return
    metrics["benchmark_pnl_on_1000"] = round(1000.0 * benchmark_return, 2) if benchmark_return is not None else None
    return {
        "coverage_start": min(dataset["coverage_start"] for dataset in split_datasets if dataset["coverage_start"]),
        "coverage_end": max(dataset["coverage_end"] for dataset in split_datasets if dataset["coverage_end"]),
        "dataset_count": len(split_datasets),
        "candidate_days": sum(dataset["candidate_days"] for dataset in split_datasets),
        "closed_trades": len(split_closed),
        "skipped_trades": sum(dataset["skipped_trades"] for dataset in split_datasets),
        "metrics": metrics,
        "sample_adequacy": sample_adequacy_labels(len(split_closed)),
    }


def metrics_for_closed_trades(closed: list[dict[str, Any]]) -> dict[str, Any]:
    pnls = [pnl_value(trade, "implementable_pnl") for trade in closed]
    mid_pnls = [pnl_value(trade, "mid_pnl") for trade in closed]
    daily_rows = daily_pnl_rows(closed)
    daily_values = [row["net_pnl"] for row in daily_rows]
    returns = [row["return_on_starting_equity"] for row in daily_rows]
    wins = [pnl for pnl in pnls if pnl > 0]
    losses = [pnl for pnl in pnls if pnl < 0]
    return {
        "trade_count": len(closed),
        "total_mid_pnl": round(sum(mid_pnls), 2),
        "total_implementable_pnl": round(sum(pnls), 2),
        "total_cost_drag": round(sum(mid_pnls) - sum(pnls), 2),
        "average_trade_pnl": round(mean(pnls), 4) if pnls else 0.0,
        "win_rate": round(len(wins) / len(pnls), 4) if pnls else 0.0,
        "payoff_ratio": round(mean(wins) / abs(mean(losses)), 4) if wins and losses else None,
        "sharpe_proxy": sharpe(returns),
        "sortino_proxy": sortino(returns),
        "max_drawdown": max_drawdown([1000.0, *[row["ending_equity"] for row in daily_rows]]),
        "es95": expected_shortfall(daily_values, 0.95),
        "es99": expected_shortfall(daily_values, 0.99),
        "worst_day_loss": min(daily_values) if daily_values else 0.0,
    }


def daily_pnl_rows(closed: list[dict[str, Any]], starting_equity: float = 1000.0) -> list[dict[str, Any]]:
    by_date: dict[str, float] = defaultdict(float)
    for trade in closed:
        by_date[str(trade.get("date"))] += pnl_value(trade, "implementable_pnl")
    equity = starting_equity
    rows = []
    for trade_date in sorted(by_date):
        net_pnl = round(by_date[trade_date], 2)
        row = {
            "date": trade_date,
            "starting_equity": round(equity, 2),
            "net_pnl": net_pnl,
            "ending_equity": round(equity + net_pnl, 2),
            "return_on_starting_equity": round(net_pnl / equity, 8) if equity else 0.0,
        }
        rows.append(row)
        equity = row["ending_equity"]
    return rows


def benchmark_for_bars(bar_path: Path) -> dict[str, Any]:
    first = None
    last = None
    for line in bar_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        close = float(record["close"])
        timestamp = record["timestamp_et"]
        if first is None:
            first = {"timestamp_et": timestamp, "close": close}
        last = {"timestamp_et": timestamp, "close": close}
    if first is None or last is None or first["close"] == 0:
        return {"return": None, "pnl_on_1000": None, "first": first, "last": last}
    ret = round((last["close"] / first["close"]) - 1, 8)
    return {"return": ret, "pnl_on_1000": round(1000.0 * ret, 2), "first": first, "last": last}


def render_report(summary: dict[str, Any]) -> str:
    metrics = summary["metrics"]
    lines = [
        "# M4.1 Sub-System A ORB Baseline",
        "",
        "## Status",
        "- Conclusion: ยังสรุปไม่ได้",
        "- Evidence type: real-data baseline, no news filter, no LLM filter.",
        f"- Closed trades: {metrics['trade_count']}",
        "- This is a completed baseline experiment round, but not acceptance-grade evidence.",
        "",
        "## Method",
        "```json",
        json.dumps(summary["methodology"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Overall Metrics",
        "```json",
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Split Metrics",
        "",
        "| Split | Coverage | Closed | Net PnL | Mid PnL | Cost Drag | Sharpe Proxy | MDD | Benchmark PnL on $1000 | Labels |",
        "|:--|:--|--:|--:|--:|--:|--:|--:|--:|:--|",
    ]
    for split, item in summary["splits"].items():
        split_metrics = item["metrics"]
        labels = ", ".join(item["sample_adequacy"]["labels"])
        lines.append(
            f"| `{split}` | `{item['coverage_start']}` to `{item['coverage_end']}` | {item['closed_trades']} | "
            f"{split_metrics['total_implementable_pnl']} | {split_metrics['total_mid_pnl']} | {split_metrics['total_cost_drag']} | "
            f"{split_metrics['sharpe_proxy']} | {split_metrics['max_drawdown']} | {split_metrics['benchmark_pnl_on_1000']} | {labels} |"
        )
    lines.extend(
        [
            "",
            "## Sample Adequacy",
            "```json",
            json.dumps(summary["sample_adequacy"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Big-Day Dependency",
            "```json",
            json.dumps(summary["big_day_dependency"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## DSR",
            "```json",
            json.dumps(summary["dsr_assessment"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Conclusion",
            "ข้อสรุป: ยังสรุปไม่ได้",
            "",
            "- Closed trades remain far below the N >= 500 prior target and MinTRL/PSR remain pending.",
            "- OOS results are reported as evidence, not as tuning input.",
            "- M4 should continue to Sub-System B feasibility and baseline work before deterministic filters or LLM gates are tested.",
        ]
    )
    return "\n".join(lines) + "\n"


def coverage_from_adapter(adapter_path: Path, key: str) -> str | None:
    return json.loads(adapter_path.read_text(encoding="utf-8")).get(key)


def pnl_value(row: dict[str, Any], key: str) -> float:
    if key in row:
        return float(row[key])
    return float(row.get("net_pnl", 0.0))


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


def compound_return(returns: list[float]) -> float | None:
    if not returns:
        return None
    value = 1.0
    for ret in returns:
        value *= 1.0 + ret
    return round(value - 1.0, 8)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run M4.1 Sub-System A ORB baseline from existing normalized real-data artifacts.")
    parser.add_argument("--summary-path", type=Path, default=SUMMARY_PATH)
    parser.add_argument("--report-path", type=Path, default=REPORT_PATH)
    args = parser.parse_args(argv)
    result = run_baseline(args.summary_path, args.report_path)
    print(json.dumps({key: value for key, value in result.items() if key not in {"daily_pnl", "datasets"}}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
