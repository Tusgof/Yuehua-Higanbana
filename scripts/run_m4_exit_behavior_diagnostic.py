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
from run_m4_subsystem_a_baseline import DATASETS, benchmark_for_bars, coverage_from_adapter


REPORT_ROOT = PROJECT_ROOT / "reports" / "baselines"
COMPONENT_ROOT = REPORT_ROOT / "m4_exit_behavior_components"
SUMMARY_PATH = REPORT_ROOT / "m4_exit_behavior_diagnostic_summary.json"
REPORT_PATH = REPORT_ROOT / "m4_exit_behavior_diagnostic_report.md"
FEE_PER_CONTRACT = 0.64
FILL_MODEL = "half_spread"
CLOSE_FALLBACK = "nearest_1545_window"
EXIT_MODELS = ["forced_close_only", "target_stop_25_50"]


def run_diagnostic(summary_path: Path = SUMMARY_PATH, report_path: Path = REPORT_PATH) -> dict[str, Any]:
    COMPONENT_ROOT.mkdir(parents=True, exist_ok=True)
    dataset_results = []
    for label, split, adapter_name, normalized_name in DATASETS:
        adapter_path = PROJECT_ROOT / "reports" / "pilots" / adapter_name
        quote_path = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "databento" / normalized_name / "option_quote.jsonl"
        bar_path = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "databento" / normalized_name / "spy_bar.jsonl"
        for exit_model in EXIT_MODELS:
            component_dir = COMPONENT_ROOT / exit_model
            pnl = run_pilot_pnl(
                adapter_summary_path=adapter_path,
                quote_path=quote_path,
                summary_path=component_dir / f"{label}_pnl_summary.json",
                report_path=component_dir / f"{label}_pnl_report.md",
                fee_per_contract=FEE_PER_CONTRACT,
                fill_model=FILL_MODEL,
                close_fallback=CLOSE_FALLBACK,
                exit_model=exit_model,
            )
            dataset_results.append(dataset_summary(label, split, exit_model, adapter_path, quote_path, bar_path, pnl))

    summary = aggregate_diagnostic(dataset_results)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(render_report(summary), encoding="utf-8")
    return summary


def dataset_summary(
    label: str,
    split: str,
    exit_model: str,
    adapter_path: Path,
    quote_path: Path,
    bar_path: Path,
    pnl: dict[str, Any],
) -> dict[str, Any]:
    trades = [{**trade, "dataset": label, "split": split, "exit_model": exit_model} for trade in pnl.get("trades", [])]
    return {
        "label": label,
        "split": split,
        "exit_model": exit_model,
        "adapter_path": str(adapter_path),
        "quote_path": str(quote_path),
        "bar_path": str(bar_path),
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


def aggregate_diagnostic(datasets: list[dict[str, Any]]) -> dict[str, Any]:
    variants = {}
    for exit_model in EXIT_MODELS:
        model_datasets = [dataset for dataset in datasets if dataset["exit_model"] == exit_model]
        variants[exit_model] = variant_summary(exit_model, model_datasets)
    comparison = compare_variants(variants["forced_close_only"], variants["target_stop_25_50"])
    conclusion = conclude(comparison)
    return {
        "record_type": "diagnostic_experiment_summary",
        "schema_version": "m4_exit_behavior_diagnostic_v1",
        "experiment_id": "m4_exit_behavior_diagnostic",
        "strategy": "Sub-System A ORB directional debit vertical",
        "status": "complete",
        "conclusion": conclusion["label"],
        "conclusion_reason": conclusion["reason"],
        "research_log_required": True,
        "research_log_slug": "higanbana-exit-behavior-diagnostic-real-data",
        "methodology": {
            "diagnostic_scope": "Compare two pre-existing exit behaviors on identical Sub-System A candidate days.",
            "not_parameter_optimization": True,
            "selection_policy": "Do not select a live exit model from this OOS diagnostic; use it to decide the next pre-registered hypothesis only.",
            "news_filter": "disabled",
            "llm_filter": "disabled",
            "entry_model": "limit-style entry priced by fill model; no entry market orders",
            "fill_model": FILL_MODEL,
            "close_fallback": CLOSE_FALLBACK,
            "fee_per_contract": FEE_PER_CONTRACT,
            "exit_models": EXIT_MODELS,
            "chronological_policy": "2023-03-01..2023-12-29 in-sample, 2024-01-02..2024-12-31 OOS; no OOS tuning from this diagnostic report",
            "strike_mapping": "nearest discrete strike selection inherited from generated strategy legs",
        },
        "sample_adequacy": sample_adequacy_labels(variants["forced_close_only"]["metrics"]["trade_count"]),
        "dsr_assessment": {
            "status": "not_applicable",
            "reason": "This diagnostic compares two pre-specified exit behaviors and does not select a best Sharpe for deployment.",
            "trial_count": len(EXIT_MODELS),
            "selected_for_deployment": None,
        },
        "variants": variants,
        "comparison": comparison,
    }


def variant_summary(exit_model: str, datasets: list[dict[str, Any]]) -> dict[str, Any]:
    trades = sorted([trade for dataset in datasets for trade in dataset["trades"]], key=lambda row: (row.get("date", ""), row.get("dataset", "")))
    closed = [trade for trade in trades if str(trade.get("status", "")).startswith("closed_")]
    return {
        "exit_model": exit_model,
        "coverage_start": min(dataset["coverage_start"] for dataset in datasets if dataset["coverage_start"]),
        "coverage_end": max(dataset["coverage_end"] for dataset in datasets if dataset["coverage_end"]),
        "dataset_count": len(datasets),
        "candidate_days": sum(dataset["candidate_days"] for dataset in datasets),
        "closed_trades": len(closed),
        "skipped_trades": sum(dataset["skipped_trades"] for dataset in datasets),
        "status_counts": sum_counts(dataset["status_counts"] for dataset in datasets),
        "metrics": metrics_for_closed_trades(closed),
        "splits": {split: split_summary(split, datasets, closed) for split in ("in_sample", "oos")},
        "sample_adequacy": sample_adequacy_labels(len(closed)),
        "big_day_dependency": big_day_dependency_check(closed),
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
        "status_counts": sum_counts(dataset["status_counts"] for dataset in split_datasets),
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
        "exit_reason_counts": sum_counts(({strip_closed_prefix(trade["status"]): 1} for trade in closed)),
    }


def compare_variants(forced: dict[str, Any], target_stop: dict[str, Any]) -> dict[str, Any]:
    forced_metrics = forced["metrics"]
    target_metrics = target_stop["metrics"]
    oos_forced = forced["splits"]["oos"]["metrics"]
    oos_target = target_stop["splits"]["oos"]["metrics"]
    return {
        "overall": delta_metrics(forced_metrics, target_metrics),
        "oos": delta_metrics(oos_forced, oos_target),
        "in_sample": delta_metrics(forced["splits"]["in_sample"]["metrics"], target_stop["splits"]["in_sample"]["metrics"]),
        "interpretation_policy": "Diagnostic only. Do not tune or select deployment behavior from OOS deltas.",
    }


def delta_metrics(base: dict[str, Any], challenger: dict[str, Any]) -> dict[str, Any]:
    return {
        "base_exit_model": "forced_close_only",
        "challenger_exit_model": "target_stop_25_50",
        "trade_count_delta": challenger["trade_count"] - base["trade_count"],
        "implementable_pnl_delta": round(challenger["total_implementable_pnl"] - base["total_implementable_pnl"], 2),
        "mid_pnl_delta": round(challenger["total_mid_pnl"] - base["total_mid_pnl"], 2),
        "cost_drag_delta": round(challenger["total_cost_drag"] - base["total_cost_drag"], 2),
        "worst_day_loss_delta": round(challenger["worst_day_loss"] - base["worst_day_loss"], 2),
        "max_drawdown_delta": none_safe_delta(challenger["max_drawdown"], base["max_drawdown"]),
        "sharpe_proxy_delta": none_safe_delta(challenger["sharpe_proxy"], base["sharpe_proxy"]),
    }


def conclude(comparison: dict[str, Any]) -> dict[str, str]:
    oos = comparison["oos"]
    if oos["implementable_pnl_delta"] > 0 and oos["worst_day_loss_delta"] >= 0:
        return {
            "label": "ยังสรุปไม่ได้",
            "reason": "Target/stop diagnostics improved some OOS metrics, but the report is under-sampled and OOS results are not allowed as tuning input.",
        }
    return {
        "label": "ยังสรุปไม่ได้",
        "reason": "The exit-behavior comparison is diagnostic only and remains under-sampled/underpowered; no exit model is selected for deployment.",
    }


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# M4.3 Exit Behavior Diagnostic",
        "",
        "## สถานะ",
        f"- ข้อสรุป: {summary['conclusion']}",
        "- ประเภทหลักฐาน: diagnostic บนข้อมูลจริง ไม่ใช่การเลือกพารามิเตอร์เพื่อใช้งานจริง",
        f"- เหตุผล: {summary['conclusion_reason']}",
        "",
        "## วิธีทดสอบ",
        "```json",
        json.dumps(summary["methodology"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## ผลรวม",
        "",
        "| Exit model | Closed | Implementable PnL | Mid PnL | Cost drag | Sharpe proxy | Max DD | Worst day | Exit reasons |",
        "|:--|--:|--:|--:|--:|--:|--:|--:|:--|",
    ]
    for exit_model in EXIT_MODELS:
        metrics = summary["variants"][exit_model]["metrics"]
        lines.append(
            f"| `{exit_model}` | {metrics['trade_count']} | {metrics['total_implementable_pnl']} | "
            f"{metrics['total_mid_pnl']} | {metrics['total_cost_drag']} | {metrics['sharpe_proxy']} | "
            f"{metrics['max_drawdown']} | {metrics['worst_day_loss']} | `{json.dumps(metrics['exit_reason_counts'], ensure_ascii=False, sort_keys=True)}` |"
        )
    lines.extend(
        [
            "",
            "## OOS Delta",
            "```json",
            json.dumps(summary["comparison"]["oos"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Split Metrics",
        ]
    )
    for exit_model in EXIT_MODELS:
        lines.extend([f"### `{exit_model}`", "", "| Split | Closed | PnL | Sharpe proxy | Max DD | Worst day | Labels |", "|:--|--:|--:|--:|--:|--:|:--|"])
        for split, item in summary["variants"][exit_model]["splits"].items():
            metrics = item["metrics"]
            labels = ", ".join(item["sample_adequacy"]["labels"])
            lines.append(
                f"| `{split}` | {metrics['trade_count']} | {metrics['total_implementable_pnl']} | "
                f"{metrics['sharpe_proxy']} | {metrics['max_drawdown']} | {metrics['worst_day_loss']} | {labels} |"
            )
        lines.append("")
    lines.extend(
        [
            "## Sample Adequacy",
            "```json",
            json.dumps(summary["sample_adequacy"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Big-Day Dependency",
        ]
    )
    for exit_model in EXIT_MODELS:
        lines.extend(
            [
                f"### `{exit_model}`",
                "```json",
                json.dumps(summary["variants"][exit_model]["big_day_dependency"], ensure_ascii=False, indent=2, sort_keys=True),
                "```",
            ]
        )
    lines.extend(
        [
            "",
            "## DSR",
            "```json",
            json.dumps(summary["dsr_assessment"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## ข้อจำกัด",
            "- ผลนี้ยัง `under-sampled` และ `underpowered` จึงห้ามใช้ยืนยัน edge หรือเลือก exit model สำหรับ live",
            "- OOS ใช้เป็นหลักฐานวินิจฉัยเท่านั้น ไม่ใช้ tune พารามิเตอร์",
            "- ถ้าจะทดสอบ target/stop ต่อ ต้องตั้งสมมติฐานใหม่ล่วงหน้าและมี search log/DSR discipline",
        ]
    )
    return "\n".join(lines) + "\n"


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


def sum_counts(counts: Any) -> dict[str, int]:
    summed: dict[str, int] = defaultdict(int)
    for count_map in counts:
        for key, value in count_map.items():
            summed[key] += int(value)
    return dict(sorted(summed.items()))


def strip_closed_prefix(status: str) -> str:
    return status.removeprefix("closed_")


def none_safe_delta(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return round(left - right, 6)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run M4.3 exit behavior diagnostic from existing normalized real-data artifacts.")
    parser.add_argument("--summary-path", type=Path, default=SUMMARY_PATH)
    parser.add_argument("--report-path", type=Path, default=REPORT_PATH)
    args = parser.parse_args(argv)
    result = run_diagnostic(args.summary_path, args.report_path)
    print(json.dumps({key: value for key, value in result.items() if key != "variants"}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
