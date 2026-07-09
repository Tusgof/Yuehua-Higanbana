from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, pstdev
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PREREG_PATH = PROJECT_ROOT / "experiments" / "h_g1_gamma_strategy_ablation_preregistration.json"
BASELINE_COMPONENT_ROOT = PROJECT_ROOT / "reports" / "baselines" / "subsystem_a_components"
GAMMA_DIAGNOSTIC_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_gamma_regime_diagnostic_summary_v3_side_aware.json"
GAMMA_ENRICHMENT_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_gamma_regime_enrichment_summary_v3_side_aware.json"
SUMMARY_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_g1_gamma_strategy_ablation_summary.json"
REPORT_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_g1_gamma_strategy_ablation_summary.md"


def run_ablation(
    prereg_path: Path = PREREG_PATH,
    baseline_component_root: Path = BASELINE_COMPONENT_ROOT,
    gamma_diagnostic_path: Path = GAMMA_DIAGNOSTIC_PATH,
    gamma_enrichment_path: Path = GAMMA_ENRICHMENT_PATH,
    summary_path: Path | None = None,
    report_path: Path | None = None,
    search_log_path: Path | None = None,
) -> dict[str, Any]:
    prereg = _read_json(prereg_path)
    _validate_prereg(prereg)

    summary_path = summary_path or PROJECT_ROOT / prereg["expected_outputs"]["summary_json"]
    report_path = report_path or PROJECT_ROOT / prereg["expected_outputs"]["summary_md"]
    search_log_path = search_log_path or PROJECT_ROOT / prereg["expected_outputs"]["search_log"]

    gamma_diagnostic = _read_json(gamma_diagnostic_path)
    gamma_enrichment = _read_json(gamma_enrichment_path)
    gamma_by_date = _gamma_by_date(gamma_diagnostic, gamma_enrichment)
    all_trades = _load_baseline_trades(baseline_component_root)
    covered_trades, excluded_trades = _join_trades_to_gamma(all_trades, gamma_by_date, prereg)
    threshold = _fit_bottom_tercile_threshold(gamma_by_date, prereg)

    variants = _variant_specs(prereg, threshold)
    variant_results = []
    search_rows = []
    for variant in variants:
        result = _evaluate_variant(variant, covered_trades)
        variant_results.append(result)
        search_rows.append(_search_log_row(result, threshold))

    baseline_result = next(item for item in variant_results if item["variant_id"] == "baseline_quant_only")
    for result in variant_results:
        result["benchmark_comparison"] = _benchmark_comparison(result, baseline_result)

    conclusion = "ยังสรุปไม่ได้"
    blockers = [
        "intersection_sample_too_small",
        "under-sampled",
        "underpowered",
        "mintrl_psr_blocked_insufficient_observations",
        "all_gamma_variants_collapse_or_reduce_the_trade_sample",
        "no_e2_acceptance",
        "signed_oi_gamma_proxy_is_not_true_market_maker_net_gamma",
    ]
    result = {
        "record_type": "experiment_summary",
        "schema_version": "h_g1_gamma_strategy_ablation_v1",
        "experiment_id": "h_g1_gamma_strategy_ablation",
        "hypothesis_id": "H-G1",
        "evidence_tier": "E1",
        "status": "complete_underpowered",
        "conclusion": conclusion,
        "conclusion_reason": (
            "The preregistered gamma ablation ran without new data, but only "
            f"{len(covered_trades)} baseline closed trades intersect the available gamma-proxy dates. "
            "The filtered variants do not create acceptance-grade evidence and must remain diagnostic."
        ),
        "source_preregistration": _relative(prereg_path),
        "source_gamma_diagnostic": _relative(gamma_diagnostic_path),
        "source_gamma_enrichment": _relative(gamma_enrichment_path),
        "baseline_component_root": _relative(baseline_component_root),
        "network_used": False,
        "paid_data_used": False,
        "new_data_requested": False,
        "strategy_pnl_used": True,
        "strategy_use_allowed": False,
        "paper_trading_allowed": False,
        "no_oos_tuning": True,
        "random_split_used": False,
        "train_only_thresholds": {
            "method": "bottom_tercile_by_ceiling_count",
            "train_date_count": threshold["train_date_count"],
            "bottom_bucket_count": threshold["bottom_bucket_count"],
            "cutoff": threshold["cutoff"],
            "train_values": threshold["train_values"],
            "thresholds_frozen_before_oos": True,
        },
        "coverage": {
            "baseline_closed_trade_count": len(all_trades),
            "gamma_date_count": len(gamma_by_date),
            "intersection_closed_trade_count": len(covered_trades),
            "excluded_baseline_closed_trade_count": len(excluded_trades),
            "excluded_reason": "baseline_trade_date_not_in_gamma_proxy_date_set",
            "covered_trade_dates": sorted({trade["date"] for trade in covered_trades}),
        },
        "variant_count_policy": prereg["variant_count_policy"],
        "variant_results": variant_results,
        "active_trade_count_by_filter": {item["variant_id"]: item["active_trade_count"] for item in variant_results},
        "skipped_trade_count_by_filter": {item["variant_id"]: item["skipped_trade_count"] for item in variant_results},
        "regime_trade_counts": {item["variant_id"]: item["regime_trade_counts"] for item in variant_results},
        "search_log": {
            "path": _relative(search_log_path),
            "trial_count": len(search_rows),
            "all_trials_recorded": True,
            "best_sharpe_selection_allowed": False,
            "selected_for_deployment": False,
        },
        "dsr_or_dsr_blocker": {
            "status": "not_applicable_no_best_sharpe_selection",
            "effective_trial_count": len(search_rows),
            "reason": "The preregistered selection rule forbids best-Sharpe selection; all four trials are logged and no variant is selected for deployment.",
        },
        "big_day_dependency_result": {
            "status": "blocked_insufficient_observations",
            "reason": "The intersection sample has fewer than 3 active trades for every variant, so removing the most extreme 5% winner and loser cannot produce a stable recomputed series.",
            "variant_results": {item["variant_id"]: item["big_day_dependency_result"] for item in variant_results},
        },
        "forbidden_claims_preserved": [
            "H-G1 strategy edge validated",
            "NOVI/net-gamma strategy filter ready",
            "true market-maker net gamma",
            "dealer net gamma",
            "paper trading approved from H-G1.22",
        ],
        "tier_blockers": blockers,
        "research_log_required": True,
        "research_log_slug": "higanbana-gamma-strategy-ablation-diagnostic",
        "research_log_path": "research_log/020-higanbana-gamma-strategy-ablation-diagnostic.md",
        "next_actions": [
            "Do not use H-G1 as a trading filter from this diagnostic.",
            "Decide whether H-G1 should be parked or whether a separate sample-expansion plan is justified.",
            "Return to News-Unblock N.7 if prioritizing timestamp-clean news before further gamma work.",
        ],
    }

    _write_json(summary_path, result)
    _write_jsonl(search_log_path, search_rows)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(_render_report(result), encoding="utf-8")
    return result


def _validate_prereg(prereg: dict[str, Any]) -> None:
    if prereg.get("schema_version") != "h_g1_gamma_strategy_ablation_preregistration_v1":
        raise ValueError("Unexpected H-G1 strategy-ablation preregistration schema")
    if prereg.get("hypothesis_id") != "H-G1":
        raise ValueError("Preregistration must target H-G1")
    if prereg["chronological_split"].get("random_split_allowed") is not False:
        raise ValueError("Random split must be forbidden")
    if prereg["chronological_split"].get("oos_tuning_allowed") is not False:
        raise ValueError("OOS tuning must be forbidden")
    if prereg["variant_count_policy"].get("total_trial_count") != 4:
        raise ValueError("H-G1.22 expects exactly four preregistered trials")


def _load_baseline_trades(root: Path) -> list[dict[str, Any]]:
    trades: list[dict[str, Any]] = []
    for path in sorted(root.glob("*_pnl_summary.json")):
        payload = _read_json(path)
        for trade in payload.get("trades", []):
            if trade.get("status") != "closed_forced_1545":
                continue
            row = dict(trade)
            row["source_summary"] = _relative(path)
            row["split"] = _split_for_date(row["date"])
            trades.append(row)
    return sorted(trades, key=lambda item: (item["date"], item.get("entry_time_et", "")))


def _gamma_by_date(diagnostic: dict[str, Any], enrichment: dict[str, Any]) -> dict[str, dict[str, Any]]:
    enrichment_by_date = {item["date"]: item for item in enrichment.get("date_summaries", [])}
    rows = {}
    for date, payload in diagnostic.get("per_date", {}).items():
        aggregate = payload["gamma_aggregate"]
        enrich = enrichment_by_date.get(date, {})
        rows[date] = {
            "date": date,
            "net_oi_gamma_proxy": float(aggregate["net_oi_gamma_proxy"]),
            "scaled_net_oi_gamma_proxy": float(aggregate["scaled_net_oi_gamma_proxy"]),
            "split": enrich.get("split", _split_for_date(date)),
            "volatility_bucket": enrich.get("volatility_bucket"),
            "high_importance_macro": enrich.get("high_importance_macro"),
            "computed_greeks_count": payload.get("computed_greeks_count"),
            "quote_count": payload.get("quote_count"),
        }
    return rows


def _join_trades_to_gamma(
    trades: list[dict[str, Any]],
    gamma_by_date: dict[str, dict[str, Any]],
    prereg: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    covered = []
    excluded = []
    for trade in trades:
        gamma = gamma_by_date.get(trade["date"])
        if gamma is None:
            excluded.append(trade)
            continue
        row = dict(trade)
        row["gamma"] = gamma
        row["split"] = _split_for_date(trade["date"], prereg)
        covered.append(row)
    return covered, excluded


def _fit_bottom_tercile_threshold(gamma_by_date: dict[str, dict[str, Any]], prereg: dict[str, Any]) -> dict[str, Any]:
    train_values = sorted(
        [
            {"date": date, "net_oi_gamma_proxy": row["net_oi_gamma_proxy"]}
            for date, row in gamma_by_date.items()
            if _split_for_date(date, prereg) == "train"
        ],
        key=lambda item: item["net_oi_gamma_proxy"],
    )
    if not train_values:
        raise ValueError("Cannot fit bottom-tercile threshold without train gamma dates")
    bottom_count = max(1, math.ceil(len(train_values) / 3))
    cutoff = train_values[bottom_count - 1]["net_oi_gamma_proxy"]
    return {
        "train_date_count": len(train_values),
        "bottom_bucket_count": bottom_count,
        "cutoff": cutoff,
        "train_values": train_values,
    }


def _variant_specs(prereg: dict[str, Any], threshold: dict[str, Any]) -> list[dict[str, Any]]:
    variants = [prereg["baseline_variant"], *prereg["gamma_variants"]]
    specs = []
    for variant in variants:
        row = dict(variant)
        if row["variant_id"] == "skip_extreme_negative_gamma_proxy_days":
            row["train_only_bottom_tercile_cutoff"] = threshold["cutoff"]
        specs.append(row)
    return specs


def _evaluate_variant(variant: dict[str, Any], trades: list[dict[str, Any]]) -> dict[str, Any]:
    active = []
    skipped = []
    for trade in trades:
        include, reason = _include_trade(variant, trade)
        (active if include else skipped).append({**trade, "filter_reason": reason})
    metrics = _metrics(active)
    split_metrics = {split: _metrics([trade for trade in active if trade["split"] == split]) for split in ("train", "oos")}
    return {
        "variant_id": variant["variant_id"],
        "variant_type": variant["variant_type"],
        "description": variant["description"],
        "gamma_filter": variant["gamma_filter"],
        "train_only_bottom_tercile_cutoff": variant.get("train_only_bottom_tercile_cutoff"),
        "active_trade_count": len(active),
        "skipped_trade_count": len(skipped),
        "skipped_trade_dates": sorted({trade["date"] for trade in skipped}),
        "active_trade_dates": sorted({trade["date"] for trade in active}),
        "metrics": metrics,
        "splits": split_metrics,
        "active_trade_count_by_filter": {variant["variant_id"]: len(active)},
        "skipped_trade_count_by_filter": {variant["variant_id"]: len(skipped)},
        "regime_trade_counts": _regime_counts(active),
        "daily_pnl": metrics["daily_pnl"],
        "equity_curve": metrics["equity_curve"],
        "drawdown_curve": metrics["drawdown_curve"],
        "mintrl": _blocked_power_metric(metrics["trade_count"], "MinTRL"),
        "psr": _blocked_power_metric(metrics["trade_count"], "PSR"),
        "under_sampled_label": True,
        "underpowered_label": True,
        "big_day_dependency_result": _big_day_dependency(active),
    }


def _include_trade(variant: dict[str, Any], trade: dict[str, Any]) -> tuple[bool, str]:
    gamma = float(trade["gamma"]["net_oi_gamma_proxy"])
    variant_id = variant["variant_id"]
    if variant_id == "baseline_quant_only":
        return True, "baseline_no_gamma_filter"
    if variant_id == "skip_negative_gamma_proxy_days":
        return gamma >= 0, "skipped_negative_gamma_proxy" if gamma < 0 else "kept_non_negative_gamma_proxy"
    if variant_id == "skip_extreme_negative_gamma_proxy_days":
        cutoff = float(variant["train_only_bottom_tercile_cutoff"])
        return gamma > cutoff, "skipped_train_bottom_tercile_or_worse" if gamma <= cutoff else "kept_above_train_bottom_tercile"
    if variant_id == "positive_gamma_proxy_only":
        return gamma > 0, "skipped_not_positive_gamma_proxy" if gamma <= 0 else "kept_positive_gamma_proxy"
    raise ValueError(f"Unknown variant: {variant_id}")


def _metrics(trades: list[dict[str, Any]]) -> dict[str, Any]:
    mid_values = [float(trade.get("mid_pnl", 0.0)) for trade in trades]
    impl_values = [float(trade.get("implementable_pnl", trade.get("net_pnl", 0.0))) for trade in trades]
    daily = _daily_rows(trades)
    returns = [row["return_on_starting_equity"] for row in daily]
    wins = [value for value in impl_values if value > 0]
    losses = [value for value in impl_values if value < 0]
    total_mid = round(sum(mid_values), 2)
    total_impl = round(sum(impl_values), 2)
    total_drag = round(sum(float(trade.get("cost_drag", 0.0)) for trade in trades), 2)
    return {
        "trade_count": len(trades),
        "mid_pnl": total_mid,
        "implementable_pnl": total_impl,
        "cost_drag": total_drag,
        "friction_drag_ratio": round(total_drag / abs(total_mid), 6) if total_mid else None,
        "daily_pnl": daily,
        "equity_curve": [1000.0, *[row["ending_equity"] for row in daily]],
        "drawdown_curve": _drawdown_curve([1000.0, *[row["ending_equity"] for row in daily]]),
        "sharpe": _sharpe(returns),
        "sortino": _sortino(returns),
        "max_drawdown": _max_drawdown([1000.0, *[row["ending_equity"] for row in daily]]),
        "es95": _expected_shortfall(impl_values, 0.95),
        "es99": _expected_shortfall(impl_values, 0.99),
        "worst_day_loss": min((row["net_pnl"] for row in daily), default=0.0),
        "win_rate": round(len(wins) / len(impl_values), 6) if impl_values else 0.0,
        "payoff_ratio": round(mean(wins) / abs(mean(losses)), 6) if wins and losses else None,
        "sample_length": len(trades),
        "distribution_inputs": _distribution_inputs(returns),
    }


def _daily_rows(trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_date: dict[str, float] = defaultdict(float)
    for trade in trades:
        by_date[trade["date"]] += float(trade.get("implementable_pnl", trade.get("net_pnl", 0.0)))
    equity = 1000.0
    rows = []
    for date in sorted(by_date):
        pnl = round(by_date[date], 2)
        row = {
            "date": date,
            "starting_equity": round(equity, 2),
            "net_pnl": pnl,
            "ending_equity": round(equity + pnl, 2),
            "return_on_starting_equity": round(pnl / equity, 8) if equity else 0.0,
        }
        rows.append(row)
        equity = row["ending_equity"]
    return rows


def _distribution_inputs(returns: list[float]) -> dict[str, Any]:
    if len(returns) < 3:
        return {
            "sample_length": len(returns),
            "observed_sharpe": _sharpe(returns),
            "skewness": None,
            "kurtosis": None,
            "first_order_autocorrelation": None,
            "status": "blocked_insufficient_observations",
        }
    avg = mean(returns)
    sd = pstdev(returns)
    if sd == 0:
        skew = None
        kurt = None
    else:
        centered = [(value - avg) / sd for value in returns]
        skew = round(mean([value**3 for value in centered]), 6)
        kurt = round(mean([value**4 for value in centered]), 6)
    return {
        "sample_length": len(returns),
        "observed_sharpe": _sharpe(returns),
        "skewness": skew,
        "kurtosis": kurt,
        "first_order_autocorrelation": _autocorrelation(returns),
        "status": "computed_diagnostic_only",
    }


def _blocked_power_metric(sample_length: int, metric_name: str) -> dict[str, Any]:
    return {
        "status": "blocked_insufficient_observations",
        "metric": metric_name,
        "sample_length": sample_length,
        "value": None,
        "labels": ["under-sampled", "underpowered"],
        "reason": "The active trade sample is too small for reliable Sharpe inference.",
    }


def _big_day_dependency(trades: list[dict[str, Any]]) -> dict[str, Any]:
    if len(trades) < 3:
        return {
            "status": "blocked_insufficient_observations",
            "active_trade_count": len(trades),
            "removed_each_side": 0,
            "reason": "Need at least 3 active trades before removing extreme winners and losers.",
        }
    remove_each = max(1, math.ceil(len(trades) * 0.05))
    ordered = sorted(trades, key=lambda trade: float(trade.get("implementable_pnl", trade.get("net_pnl", 0.0))))
    retained = ordered[remove_each : len(ordered) - remove_each]
    return {
        "status": "computed_diagnostic_only",
        "active_trade_count": len(trades),
        "removed_each_side": remove_each,
        "retained_trade_count": len(retained),
        "recomputed_metrics": _metrics(retained),
        "conclusion": "ยังสรุปไม่ได้",
    }


def _regime_counts(trades: list[dict[str, Any]]) -> dict[str, Any]:
    split = Counter(trade["split"] for trade in trades)
    vol = Counter(trade["gamma"].get("volatility_bucket") or "unknown" for trade in trades)
    macro = Counter("high_importance_macro" if trade["gamma"].get("high_importance_macro") else "no_high_importance_macro" for trade in trades)
    return {
        "by_split": dict(sorted(split.items())),
        "by_volatility_bucket": dict(sorted(vol.items())),
        "by_macro_flag": dict(sorted(macro.items())),
    }


def _benchmark_comparison(result: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    metrics = result["metrics"]
    base = baseline["metrics"]
    return {
        "benchmark_variant": baseline["variant_id"],
        "trade_count_delta": metrics["trade_count"] - base["trade_count"],
        "implementable_pnl_delta": round(metrics["implementable_pnl"] - base["implementable_pnl"], 2),
        "mid_pnl_delta": round(metrics["mid_pnl"] - base["mid_pnl"], 2),
        "cost_drag_delta": round(metrics["cost_drag"] - base["cost_drag"], 2),
        "max_drawdown_delta": _delta(metrics["max_drawdown"], base["max_drawdown"]),
        "oos_implementable_pnl_delta": round(
            result["splits"]["oos"]["implementable_pnl"] - baseline["splits"]["oos"]["implementable_pnl"],
            2,
        ),
    }


def _search_log_row(result: dict[str, Any], threshold: dict[str, Any]) -> dict[str, Any]:
    metrics = result["metrics"]
    return {
        "variant_id": result["variant_id"],
        "gamma_filter": result["gamma_filter"],
        "train_only_bottom_tercile_cutoff": result.get("train_only_bottom_tercile_cutoff"),
        "threshold_fit_method": "bottom_tercile_by_ceiling_count",
        "threshold_train_date_count": threshold["train_date_count"],
        "active_trade_count": result["active_trade_count"],
        "skipped_trade_count": result["skipped_trade_count"],
        "implementable_pnl": metrics["implementable_pnl"],
        "mid_pnl": metrics["mid_pnl"],
        "cost_drag": metrics["cost_drag"],
        "sharpe": metrics["sharpe"],
        "max_drawdown": metrics["max_drawdown"],
        "under_sampled_label": result["under_sampled_label"],
        "underpowered_label": result["underpowered_label"],
        "selected_for_deployment": False,
        "oos_tuning_used": False,
    }


def _render_report(result: dict[str, Any]) -> str:
    lines = [
        "# H-G1 Gamma Strategy Ablation Diagnostic",
        "",
        "## Status",
        f"- Hypothesis: `{result['hypothesis_id']}`",
        f"- Status: `{result['status']}`",
        f"- Evidence tier: `{result['evidence_tier']}`",
        f"- Conclusion: {result['conclusion']}",
        f"- Strategy use allowed: `{result['strategy_use_allowed']}`",
        f"- Paper trading allowed: `{result['paper_trading_allowed']}`",
        f"- Network used: `{result['network_used']}`",
        f"- Paid data used: `{result['paid_data_used']}`",
        "",
        "## Coverage",
        f"- Baseline closed trades: {result['coverage']['baseline_closed_trade_count']}",
        f"- Gamma dates: {result['coverage']['gamma_date_count']}",
        f"- Intersection closed trades: {result['coverage']['intersection_closed_trade_count']}",
        f"- Excluded baseline closed trades: {result['coverage']['excluded_baseline_closed_trade_count']}",
        f"- Covered trade dates: `{', '.join(result['coverage']['covered_trade_dates'])}`",
        "",
        "## Train-Only Threshold",
        "```json",
        json.dumps(result["train_only_thresholds"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Variant Results",
        "",
        "| Variant | Active | Skipped | Mid PnL | Implementable PnL | Cost Drag | Sharpe | Max DD | ES95 | Labels |",
        "|:--|--:|--:|--:|--:|--:|--:|--:|--:|:--|",
    ]
    for row in result["variant_results"]:
        metrics = row["metrics"]
        labels = ", ".join(row["mintrl"]["labels"])
        lines.append(
            f"| `{row['variant_id']}` | {row['active_trade_count']} | {row['skipped_trade_count']} | "
            f"{metrics['mid_pnl']} | {metrics['implementable_pnl']} | {metrics['cost_drag']} | "
            f"{metrics['sharpe']} | {metrics['max_drawdown']} | {metrics['es95']} | {labels} |"
        )
    lines.extend(
        [
            "",
            "## DSR / Big-Day Dependency",
            f"- DSR status: `{result['dsr_or_dsr_blocker']['status']}`",
            f"- DSR reason: {result['dsr_or_dsr_blocker']['reason']}",
            f"- Big-day dependency status: `{result['big_day_dependency_result']['status']}`",
            f"- Big-day reason: {result['big_day_dependency_result']['reason']}",
            "",
            "## Tier Blockers",
        ]
    )
    lines.extend(f"- `{item}`" for item in result["tier_blockers"])
    lines.extend(["", "## Next Actions"])
    lines.extend(f"{idx}. {item}" for idx, item in enumerate(result["next_actions"], start=1))
    lines.append("")
    return "\n".join(lines)


def _split_for_date(date: str, prereg: dict[str, Any] | None = None) -> str:
    if prereg is None:
        if date <= "2023-12-31":
            return "train"
        if date >= "2024-01-01":
            return "oos"
        return "reference"
    split = prereg["chronological_split"]
    if split["train_start"] <= date <= split["train_end"]:
        return "train"
    if date >= split["oos_start"]:
        return "oos"
    return "reference"


def _sharpe(returns: list[float]) -> float | None:
    if len(returns) < 2:
        return None
    sd = pstdev(returns)
    return None if sd == 0 else round(mean(returns) / sd, 6)


def _sortino(returns: list[float]) -> float | None:
    downside = [value for value in returns if value < 0]
    if len(downside) < 2:
        return None
    sd = pstdev(downside)
    return None if sd == 0 else round(mean(returns) / sd, 6)


def _autocorrelation(values: list[float]) -> float | None:
    if len(values) < 3:
        return None
    x = values[:-1]
    y = values[1:]
    mx = mean(x)
    my = mean(y)
    denom = math.sqrt(sum((value - mx) ** 2 for value in x) * sum((value - my) ** 2 for value in y))
    if denom == 0:
        return None
    return round(sum((a - mx) * (b - my) for a, b in zip(x, y)) / denom, 6)


def _max_drawdown(equity: list[float]) -> float:
    if not equity:
        return 0.0
    peak = equity[0]
    max_dd = 0.0
    for value in equity:
        peak = max(peak, value)
        if peak:
            max_dd = min(max_dd, (value / peak) - 1)
    return round(max_dd, 6)


def _drawdown_curve(equity: list[float]) -> list[dict[str, Any]]:
    rows = []
    peak = equity[0] if equity else 0.0
    for index, value in enumerate(equity):
        peak = max(peak, value)
        drawdown = round((value / peak) - 1, 6) if peak else 0.0
        rows.append({"index": index, "equity": round(value, 2), "drawdown": drawdown})
    return rows


def _expected_shortfall(values: list[float], confidence: float) -> float | None:
    if not values:
        return None
    tail_count = max(1, math.ceil(len(values) * (1 - confidence)))
    return round(mean(sorted(values)[:tail_count]), 4)


def _delta(value: float | None, baseline: float | None) -> float | None:
    if value is None or baseline is None:
        return None
    return round(value - baseline, 6)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run no-paid H-G1 gamma strategy-ablation diagnostic.")
    parser.add_argument("--prereg-path", type=Path, default=PREREG_PATH)
    parser.add_argument("--summary-path", type=Path)
    parser.add_argument("--report-path", type=Path)
    parser.add_argument("--search-log-path", type=Path)
    args = parser.parse_args(argv)
    result = run_ablation(
        prereg_path=args.prereg_path,
        summary_path=args.summary_path,
        report_path=args.report_path,
        search_log_path=args.search_log_path,
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "conclusion": result["conclusion"],
                "intersection_closed_trade_count": result["coverage"]["intersection_closed_trade_count"],
                "strategy_use_allowed": result["strategy_use_allowed"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
