from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime, time
from pathlib import Path
from statistics import mean, pstdev
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from run_jan2024_pilot_pnl import big_day_dependency_check, sample_adequacy_labels


REPORT_ROOT = PROJECT_ROOT / "reports" / "baselines"
SUMMARY_PATH = REPORT_ROOT / "subsystem_b_put_ratio_feasibility_summary.json"
REPORT_PATH = REPORT_ROOT / "subsystem_b_put_ratio_feasibility_report.md"
FEE_PER_CONTRACT = 0.64
OPTION_MULTIPLIER = 100
STARTING_EQUITY = 1000.0
SUBSYSTEM_B_ALLOCATION = 300.0
RISK_FRACTION = 0.02
RISK_BUDGET = STARTING_EQUITY * RISK_FRACTION
ENTRY_TARGET = time(10, 0)
ENTRY_EARLIEST = time(9, 55)
CLOSE_TARGET = time(15, 45)
CLOSE_EARLIEST = time(15, 35)
NEAR_MONEYNESS = 1.0
SHORT_MONEYNESS = 0.99
WING_GAP = 10.0


DATASETS = [
    ("insample_2023_03", "in_sample", "insample_2023_03"),
    ("insample_2023_04", "in_sample", "insample_2023_04"),
    ("insample_2023_05", "in_sample", "insample_2023_05"),
    ("insample_2023_06", "in_sample", "insample_2023_06"),
    ("insample_2023_07", "in_sample", "insample_2023_07"),
    ("insample_2023_08", "in_sample", "insample_2023_08"),
    ("insample_2023_09", "in_sample", "insample_2023_09"),
    ("insample_2023_10", "in_sample", "insample_2023_10"),
    ("insample_2023_11", "in_sample", "insample_2023_11"),
    ("insample_2023_12", "in_sample", "insample_2023_12"),
    ("oos_2024_01", "oos", "one_month_pilot"),
    ("oos_2024_02", "oos", "oos_2024_2025"),
    ("oos_2024_03", "oos", "oos_2024_03"),
    ("oos_2024_04", "oos", "oos_2024_04"),
    ("oos_2024_05", "oos", "oos_2024_05"),
    ("oos_2024_06", "oos", "oos_2024_06"),
    ("oos_2024_07_partial", "oos", "oos_2024_07_partial"),
    ("oos_2024_07_chunk3", "oos", "oos_2024_07_intraday_exit_30m_chunk3"),
    ("oos_2024_07_chunk4", "oos", "oos_2024_07_intraday_exit_30m_chunk4"),
    ("oos_2024_07_chunk5", "oos", "oos_2024_07_intraday_exit_30m_chunk5"),
    ("oos_2024_08_chunk1", "oos", "oos_2024_08_intraday_exit_30m_chunk1"),
    ("oos_2024_08_chunk2", "oos", "oos_2024_08_intraday_exit_30m_chunk2"),
    ("oos_2024_08_chunk3", "oos", "oos_2024_08_intraday_exit_30m_chunk3"),
    ("oos_2024_08_chunk4", "oos", "oos_2024_08_intraday_exit_30m_chunk4"),
    ("oos_2024_08_chunk5", "oos", "oos_2024_08_intraday_exit_30m_chunk5"),
    ("oos_2024_09_chunk1", "oos", "oos_2024_09_intraday_exit_30m_chunk1"),
    ("oos_2024_09_chunk2", "oos", "oos_2024_09_intraday_exit_30m_chunk2"),
    ("oos_2024_09_chunk3", "oos", "oos_2024_09_intraday_exit_30m_chunk3"),
    ("oos_2024_09_remainder", "oos", "oos_2024_09_remainder_daily_union"),
    ("oos_2024_10", "oos", "oos_2024_10_daily_union"),
    ("oos_2024_11", "oos", "oos_2024_11_daily_union"),
    ("oos_2024_12", "oos", "oos_2024_12_daily_union"),
]


class SubsystemBFeasibilityError(ValueError):
    pass


def run_feasibility(summary_path: Path = SUMMARY_PATH, report_path: Path = REPORT_PATH) -> dict[str, Any]:
    dataset_results = []
    for label, split, normalized_name in DATASETS:
        normalized_root = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "databento" / normalized_name
        dataset_results.append(run_dataset(label, split, normalized_root))
    summary = aggregate_results(dataset_results)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(render_report(summary), encoding="utf-8")
    return summary


def run_dataset(label: str, split: str, normalized_root: Path) -> dict[str, Any]:
    bar_path = normalized_root / "spy_bar.jsonl"
    quote_path = normalized_root / "option_quote.jsonl"
    bars = load_bars_by_date(bar_path)
    snapshots = load_put_snapshots(quote_path)
    days = []
    for trade_date in sorted(bars):
        days.append(evaluate_day(label, split, trade_date, bars[trade_date], snapshots.get(trade_date, {})))
    return {
        "label": label,
        "split": split,
        "normalized_root": str(normalized_root),
        "bar_path": str(bar_path),
        "quote_path": str(quote_path),
        "coverage_start": min(bars) if bars else None,
        "coverage_end": max(bars) if bars else None,
        "trading_days": len(bars),
        "days": days,
    }


def evaluate_day(
    dataset: str,
    split: str,
    trade_date: str,
    bars: list[dict[str, Any]],
    snapshots: dict[str, dict[float, dict[str, Any]]],
) -> dict[str, Any]:
    entry_bar = nearest_bar_at_or_before(bars, ENTRY_TARGET)
    result: dict[str, Any] = {
        "date": trade_date,
        "dataset": dataset,
        "split": split,
        "status": "unknown",
        "reasons": [],
    }
    if entry_bar is None:
        result.update(status="missing_underlying_1000", reasons=["missing SPY 10:00 ET bar"])
        return result
    entry_timestamp = choose_entry_timestamp(snapshots)
    close_timestamp = choose_close_timestamp(snapshots)
    if entry_timestamp is None:
        result.update(status="missing_entry_quotes", reasons=["missing put snapshot between 09:55 and 10:00 ET"])
        return result
    if close_timestamp is None:
        result.update(status="missing_close_quotes", reasons=["missing put snapshot near forced close 15:45 ET"])
        return result

    entry_quotes = list(snapshots[entry_timestamp].values())
    try:
        legs = select_capped_put_ratio_legs(entry_quotes, float(entry_bar["close"]))
    except SubsystemBFeasibilityError as exc:
        result.update(
            status="structure_unavailable",
            underlying_1000=float(entry_bar["close"]),
            entry_timestamp_et=entry_timestamp,
            close_timestamp_et=close_timestamp,
            reasons=[str(exc)],
        )
        return result

    close_quotes = snapshots[close_timestamp]
    missing_close = [leg_key(leg) for leg in legs if float(leg["strike"]) not in close_quotes]
    if missing_close:
        result.update(
            status="missing_leg_close_quotes",
            underlying_1000=float(entry_bar["close"]),
            entry_timestamp_et=entry_timestamp,
            close_timestamp_et=close_timestamp,
            legs=legs,
            reasons=["missing close quotes: " + ", ".join(missing_close)],
        )
        return result

    entry_by_strike = snapshots[entry_timestamp]
    mid_pnl = strategy_pnl(legs, entry_by_strike, close_quotes, "mid", include_fees=False)
    gross_pnl = strategy_pnl(legs, entry_by_strike, close_quotes, "implementable", include_fees=False)
    fees = round(sum(leg["quantity"] for leg in legs) * FEE_PER_CONTRACT * 2, 2)
    implementable_pnl = round(gross_pnl - fees, 2)
    entry_cashflow = opening_cashflow(legs, entry_by_strike, "implementable")
    mid_entry_cashflow = opening_cashflow(legs, entry_by_strike, "mid")
    max_loss = max_defined_loss(legs, entry_cashflow)
    result.update(
        {
            "status": "closed_forced_1545",
            "underlying_1000": float(entry_bar["close"]),
            "entry_timestamp_et": entry_timestamp,
            "close_timestamp_et": close_timestamp,
            "legs": legs,
            "entry_cashflow": round(entry_cashflow, 4),
            "mid_entry_cashflow": round(mid_entry_cashflow, 4),
            "max_defined_loss": max_loss,
            "account_1000_feasible": max_loss <= STARTING_EQUITY,
            "allocation_300_feasible": max_loss <= SUBSYSTEM_B_ALLOCATION,
            "risk_budget_20_feasible": max_loss <= RISK_BUDGET,
            "max_contract_quantity_2pct": int(RISK_BUDGET // max_loss) if max_loss > 0 else 0,
            "mid_pnl": mid_pnl,
            "gross_pnl": gross_pnl,
            "fees": fees,
            "implementable_pnl": implementable_pnl,
            "net_pnl": implementable_pnl,
            "cost_drag": round(mid_pnl - implementable_pnl, 2),
            "reasons": [
                "entry uses nearest put snapshot at or before 10:00 ET",
                "exit uses forced close snapshot nearest 15:45 ET",
                "protective wing required and at least $10 below short strike when available",
            ],
        }
    )
    return result


def select_capped_put_ratio_legs(put_quotes: list[dict[str, Any]], underlying_price: float) -> list[dict[str, Any]]:
    puts = sorted([quote for quote in put_quotes if quote["right"] == "put"], key=lambda quote: float(quote["strike"]))
    if len(puts) < 3:
        raise SubsystemBFeasibilityError("not enough put strikes")
    near_target = underlying_price * NEAR_MONEYNESS
    near = min(puts, key=lambda quote: abs(float(quote["strike"]) - near_target))
    short_target = underlying_price * SHORT_MONEYNESS
    short_candidates = [quote for quote in puts if float(quote["strike"]) < float(near["strike"]) and float(quote["strike"]) <= short_target]
    if not short_candidates:
        raise SubsystemBFeasibilityError("no short put below 0.99 moneyness target")
    short = max(short_candidates, key=lambda quote: float(quote["strike"]))
    wing_target = float(short["strike"]) - WING_GAP
    wing_candidates = [quote for quote in puts if float(quote["strike"]) < float(short["strike"]) and float(quote["strike"]) <= wing_target]
    if not wing_candidates:
        raise SubsystemBFeasibilityError("no protective wing at least $10 below short strike")
    wing = max(wing_candidates, key=lambda quote: float(quote["strike"]))
    return [
        make_leg("sub_b_long_near", near, "buy", 1),
        make_leg("sub_b_short_ratio", short, "sell", 2),
        make_leg("sub_b_long_wing", wing, "buy", 1),
    ]


def make_leg(role: str, quote: dict[str, Any], side: str, quantity: int) -> dict[str, Any]:
    return {
        "role": role,
        "right": "put",
        "strike": float(quote["strike"]),
        "side": side,
        "quantity": quantity,
    }


def max_defined_loss(legs: list[dict[str, Any]], entry_cashflow: float) -> float:
    strikes = [float(leg["strike"]) for leg in legs]
    candidates = sorted({0.0, *strikes, max(strikes) * 1.25})
    worst = min(expiration_value(legs, spot) + entry_cashflow for spot in candidates)
    return round(max(0.0, -worst * OPTION_MULTIPLIER), 2)


def expiration_value(legs: list[dict[str, Any]], spot: float) -> float:
    value = 0.0
    for leg in legs:
        intrinsic = max(float(leg["strike"]) - spot, 0.0)
        value += intrinsic * leg_sign(leg) * int(leg["quantity"])
    return value


def strategy_pnl(
    legs: list[dict[str, Any]],
    entry_quotes_by_strike: dict[float, dict[str, Any]],
    close_quotes_by_strike: dict[float, dict[str, Any]],
    model: str,
    include_fees: bool,
) -> float:
    entry = opening_cashflow(legs, entry_quotes_by_strike, model)
    close = closing_cashflow(legs, close_quotes_by_strike, model)
    fees = sum(leg["quantity"] for leg in legs) * FEE_PER_CONTRACT * 2 if include_fees else 0.0
    return round((entry + close) * OPTION_MULTIPLIER - fees, 2)


def opening_cashflow(legs: list[dict[str, Any]], quotes_by_strike: dict[float, dict[str, Any]], model: str) -> float:
    total = 0.0
    for leg in legs:
        quote = quotes_by_strike[float(leg["strike"])]
        price = price_for_open(quote, leg["side"], model)
        total += -price * leg_sign(leg) * leg["quantity"]
    return total


def closing_cashflow(legs: list[dict[str, Any]], quotes_by_strike: dict[float, dict[str, Any]], model: str) -> float:
    total = 0.0
    for leg in legs:
        quote = quotes_by_strike[float(leg["strike"])]
        price = price_for_close(quote, leg["side"], model)
        total += price * leg_sign(leg) * leg["quantity"]
    return total


def leg_sign(leg: dict[str, Any]) -> int:
    return 1 if leg["side"] == "buy" else -1


def price_for_open(quote: dict[str, Any], side: str, model: str) -> float:
    if model == "mid":
        return mid_price(quote)
    return float(quote["ask"] if side == "buy" else quote["bid"])


def price_for_close(quote: dict[str, Any], side: str, model: str) -> float:
    if model == "mid":
        return mid_price(quote)
    return float(quote["bid"] if side == "buy" else quote["ask"])


def mid_price(quote: dict[str, Any]) -> float:
    return (float(quote["bid"]) + float(quote["ask"])) / 2


def aggregate_results(datasets: list[dict[str, Any]]) -> dict[str, Any]:
    days = [day for dataset in datasets for day in dataset["days"]]
    closed = [day for day in days if day["status"] == "closed_forced_1545"]
    metrics = metrics_for_closed_days(closed)
    return {
        "record_type": "baseline_experiment_summary",
        "schema_version": "m4_subsystem_b_feasibility_v1",
        "experiment_id": "m4_subsystem_b_put_ratio_feasibility",
        "strategy": "Sub-System B capped-risk put ratio spread",
        "status": "complete",
        "conclusion": "ไม่ผ่าน",
        "conclusion_reason": "The fixed capped-risk put ratio template does not fit the current $300 Sub-System B allocation or $20 risk budget on any closed trade. Edge evidence remains under-sampled and underpowered.",
        "research_log_required": True,
        "research_log_slug": "higanbana-put-ratio-feasibility-real-data",
        "methodology": {
            "entry_time": "10:00 ET or nearest available quote at/before 10:00",
            "exit_model": "forced_close_1545",
            "news_filter": "disabled",
            "llm_filter": "disabled",
            "near_moneyness": NEAR_MONEYNESS,
            "short_moneyness": SHORT_MONEYNESS,
            "protective_wing_gap": WING_GAP,
            "strike_mapping": "nearest discrete strike rounding; wing must be at least $10 below short strike",
            "fee_per_contract": FEE_PER_CONTRACT,
            "account_equity": STARTING_EQUITY,
            "subsystem_b_allocation": SUBSYSTEM_B_ALLOCATION,
            "risk_budget_2pct": RISK_BUDGET,
            "chronological_policy": "2023-03-01..2023-12-29 in-sample, 2024-01-02..2024-12-31 OOS; no OOS tuning from this report",
        },
        "sample_adequacy": sample_adequacy_labels(len(closed)),
        "dsr_assessment": {
            "status": "not_applicable",
            "reason": "This feasibility run uses one fixed template and does not select best parameters from a search grid.",
            "trial_count": 1,
        },
        "big_day_dependency": big_day_dependency_check(closed),
        "metrics": metrics,
        "feasibility": feasibility_summary(closed),
        "splits": {split: split_summary(split, datasets) for split in ("in_sample", "oos")},
        "status_counts": dict(Counter(day["status"] for day in days)),
        "daily_pnl": daily_pnl_rows(closed),
        "datasets": [dataset_summary(dataset) for dataset in datasets],
    }


def feasibility_summary(closed: list[dict[str, Any]]) -> dict[str, Any]:
    if not closed:
        return {}
    losses = [float(day["max_defined_loss"]) for day in closed]
    return {
        "checked_trades": len(closed),
        "min_defined_loss": round(min(losses), 2),
        "median_defined_loss": round(sorted(losses)[len(losses) // 2], 2),
        "max_defined_loss": round(max(losses), 2),
        "account_1000_feasible_count": sum(1 for day in closed if day["account_1000_feasible"]),
        "allocation_300_feasible_count": sum(1 for day in closed if day["allocation_300_feasible"]),
        "risk_budget_20_feasible_count": sum(1 for day in closed if day["risk_budget_20_feasible"]),
        "all_trades_fit_1000_account": all(day["account_1000_feasible"] for day in closed),
        "all_trades_fit_300_allocation": all(day["allocation_300_feasible"] for day in closed),
        "all_trades_fit_20_risk_budget": all(day["risk_budget_20_feasible"] for day in closed),
    }


def split_summary(split: str, datasets: list[dict[str, Any]]) -> dict[str, Any]:
    split_datasets = [dataset for dataset in datasets if dataset["split"] == split]
    days = [day for dataset in split_datasets for day in dataset["days"]]
    closed = [day for day in days if day["status"] == "closed_forced_1545"]
    return {
        "coverage_start": min(dataset["coverage_start"] for dataset in split_datasets if dataset["coverage_start"]),
        "coverage_end": max(dataset["coverage_end"] for dataset in split_datasets if dataset["coverage_end"]),
        "dataset_count": len(split_datasets),
        "trading_days": sum(dataset["trading_days"] for dataset in split_datasets),
        "closed_trades": len(closed),
        "status_counts": dict(Counter(day["status"] for day in days)),
        "metrics": metrics_for_closed_days(closed),
        "feasibility": feasibility_summary(closed),
        "sample_adequacy": sample_adequacy_labels(len(closed)),
    }


def metrics_for_closed_days(closed: list[dict[str, Any]]) -> dict[str, Any]:
    pnls = [float(day["implementable_pnl"]) for day in closed]
    mid_pnls = [float(day["mid_pnl"]) for day in closed]
    daily_values = [row["net_pnl"] for row in daily_pnl_rows(closed)]
    returns = [row["return_on_starting_equity"] for row in daily_pnl_rows(closed)]
    wins = [pnl for pnl in pnls if pnl > 0]
    losses = [pnl for pnl in pnls if pnl < 0]
    return {
        "trade_count": len(closed),
        "total_mid_pnl": round(sum(mid_pnls), 2),
        "total_implementable_pnl": round(sum(pnls), 2),
        "total_cost_drag": round(sum(day.get("cost_drag", 0.0) for day in closed), 2),
        "average_trade_pnl": round(mean(pnls), 4) if pnls else 0.0,
        "win_rate": round(len(wins) / len(pnls), 4) if pnls else 0.0,
        "payoff_ratio": round(mean(wins) / abs(mean(losses)), 4) if wins and losses else None,
        "sharpe_proxy": sharpe(returns),
        "sortino_proxy": sortino(returns),
        "max_drawdown": max_drawdown([STARTING_EQUITY, *[row["ending_equity"] for row in daily_pnl_rows(closed)]]),
        "es95": expected_shortfall(daily_values, 0.95),
        "es99": expected_shortfall(daily_values, 0.99),
        "worst_day_loss": min(daily_values) if daily_values else 0.0,
    }


def daily_pnl_rows(closed: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_date: dict[str, float] = defaultdict(float)
    for day in closed:
        by_date[day["date"]] += float(day["implementable_pnl"])
    equity = STARTING_EQUITY
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


def dataset_summary(dataset: dict[str, Any]) -> dict[str, Any]:
    days = dataset["days"]
    closed = [day for day in days if day["status"] == "closed_forced_1545"]
    return {
        "label": dataset["label"],
        "split": dataset["split"],
        "normalized_root": dataset["normalized_root"],
        "coverage_start": dataset["coverage_start"],
        "coverage_end": dataset["coverage_end"],
        "trading_days": dataset["trading_days"],
        "closed_trades": len(closed),
        "status_counts": dict(Counter(day["status"] for day in days)),
        "total_implementable_pnl": round(sum(float(day["implementable_pnl"]) for day in closed), 2),
    }


def load_bars_by_date(path: Path) -> dict[str, list[dict[str, Any]]]:
    bars: dict[str, list[dict[str, Any]]] = defaultdict(list)
    if not path.exists():
        return {}
    with path.open(encoding="utf-8-sig") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            bars[record["timestamp_et"][:10]].append(record)
    return dict(bars)


def load_put_snapshots(path: Path) -> dict[str, dict[str, dict[float, dict[str, Any]]]]:
    snapshots: dict[str, dict[str, dict[float, dict[str, Any]]]] = defaultdict(lambda: defaultdict(dict))
    if not path.exists():
        return {}
    with path.open(encoding="utf-8-sig") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("right") != "put":
                continue
            timestamp = record["quote_timestamp_et"]
            quote_time = datetime.fromisoformat(timestamp).time()
            if not (ENTRY_EARLIEST <= quote_time <= ENTRY_TARGET or CLOSE_EARLIEST <= quote_time <= CLOSE_TARGET):
                continue
            snapshots[record["expiration_date"]][timestamp][float(record["strike"])] = record
    return {date: dict(by_timestamp) for date, by_timestamp in snapshots.items()}


def nearest_bar_at_or_before(bars: list[dict[str, Any]], target: time) -> dict[str, Any] | None:
    candidates = [bar for bar in bars if datetime.fromisoformat(bar["timestamp_et"]).time() <= target]
    if not candidates:
        return None
    return max(candidates, key=lambda bar: bar["timestamp_et"])


def choose_entry_timestamp(snapshots: dict[str, dict[float, dict[str, Any]]]) -> str | None:
    candidates = []
    for timestamp in snapshots:
        quote_time = datetime.fromisoformat(timestamp).time()
        if ENTRY_EARLIEST <= quote_time <= ENTRY_TARGET:
            candidates.append(timestamp)
    return max(candidates) if candidates else None


def choose_close_timestamp(snapshots: dict[str, dict[float, dict[str, Any]]]) -> str | None:
    candidates = []
    for timestamp in snapshots:
        quote_time = datetime.fromisoformat(timestamp).time()
        if CLOSE_EARLIEST <= quote_time <= CLOSE_TARGET:
            target_dt = datetime.combine(datetime.fromisoformat(timestamp).date(), CLOSE_TARGET)
            actual_dt = datetime.combine(datetime.fromisoformat(timestamp).date(), quote_time)
            candidates.append((abs((target_dt - actual_dt).total_seconds()), timestamp))
    return min(candidates)[1] if candidates else None


def leg_key(leg: dict[str, Any]) -> str:
    return f"{leg['right']} {leg['strike']}"


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


def render_report(summary: dict[str, Any]) -> str:
    metrics = summary["metrics"]
    feasibility = summary["feasibility"]
    lines = [
        "# M4.2 Sub-System B Put Ratio Feasibility",
        "",
        "## Status",
        "- Conclusion: ไม่ผ่าน",
        "- Evidence type: real-data diagnostic feasibility and baseline, no news filter, no LLM filter.",
        f"- Closed trades: {metrics['trade_count']}",
        "- This is not acceptance-grade evidence.",
        "",
        "## Method",
        "```json",
        json.dumps(summary["methodology"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Feasibility",
        "```json",
        json.dumps(feasibility, ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Overall Metrics",
        "```json",
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Split Metrics",
        "",
        "| Split | Coverage | Closed | Net PnL | Mid PnL | Cost Drag | Sharpe Proxy | MDD | Fits $300 Allocation | Fits $20 Risk Budget | Labels |",
        "|:--|:--|--:|--:|--:|--:|--:|--:|--:|--:|:--|",
    ]
    for split, item in summary["splits"].items():
        split_metrics = item["metrics"]
        split_feas = item["feasibility"]
        labels = ", ".join(item["sample_adequacy"]["labels"])
        lines.append(
            f"| `{split}` | `{item['coverage_start']}` to `{item['coverage_end']}` | {item['closed_trades']} | "
            f"{split_metrics['total_implementable_pnl']} | {split_metrics['total_mid_pnl']} | {split_metrics['total_cost_drag']} | "
            f"{split_metrics['sharpe_proxy']} | {split_metrics['max_drawdown']} | "
            f"{split_feas.get('allocation_300_feasible_count', 0)}/{item['closed_trades']} | "
            f"{split_feas.get('risk_budget_20_feasible_count', 0)}/{item['closed_trades']} | {labels} |"
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
            "ข้อสรุป: ไม่ผ่าน",
            "",
            "- The fixed capped-risk put ratio template does not fit the current $300 Sub-System B allocation or $20 risk budget on any closed trade.",
            "- Edge remains under-sampled and underpowered, so this should be read as a feasibility failure, not a final proof that all Sub-System B variants are invalid.",
            "- The result must not be used as a tuned strategy because no logistic timing model or regime filter is active.",
            "- M4 should continue to forced-close versus target/stop diagnostics after this baseline/feasibility evidence is logged.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run M4.2 Sub-System B capped-risk put ratio feasibility on existing real-data artifacts.")
    parser.add_argument("--summary-path", type=Path, default=SUMMARY_PATH)
    parser.add_argument("--report-path", type=Path, default=REPORT_PATH)
    args = parser.parse_args(argv)
    result = run_feasibility(args.summary_path, args.report_path)
    print(json.dumps({key: value for key, value in result.items() if key not in {"daily_pnl", "datasets"}}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
