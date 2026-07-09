from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from run_m4_subsystem_a_baseline import DATASETS
from run_m5_regime_filter_sensitivity import load_macro_events_by_date, load_vix_vxv, previous_vix_record


DEFAULT_PREREGISTRATION_PATH = PROJECT_ROOT / "experiments" / "h_a2_lower_resolution_proxy_preregistration.json"
DEFAULT_SUMMARY_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_lower_resolution_proxy_summary.json"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_lower_resolution_proxy_report.md"
DEFAULT_SEARCH_LOG_PATH = PROJECT_ROOT / "reports" / "experiments" / "search_logs" / "h_a2_lower_resolution_proxy_search_log.jsonl"
BASELINE_SUMMARY_PATH = PROJECT_ROOT / "reports" / "baselines" / "subsystem_a_orb_baseline_summary.json"
VIX_PATH = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "vix_vxv" / "vix_vxv.jsonl"
MACRO_PATH = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "macro_calendar" / "macro_event.jsonl"


def run_proxy(
    preregistration_path: Path = DEFAULT_PREREGISTRATION_PATH,
    summary_path: Path = DEFAULT_SUMMARY_PATH,
    report_path: Path = DEFAULT_REPORT_PATH,
    search_log_path: Path = DEFAULT_SEARCH_LOG_PATH,
) -> dict[str, Any]:
    prereg = _load_json(preregistration_path)
    vix_rows = load_vix_vxv(VIX_PATH)
    macro_by_date = load_macro_events_by_date(MACRO_PATH)
    existing_trades_by_date = _load_existing_trades_by_date(BASELINE_SUMMARY_PATH)

    daily_rows = []
    for dataset_label, split, adapter_name, normalized_name in DATASETS:
        adapter = _load_json(PROJECT_ROOT / "reports" / "pilots" / adapter_name)
        bar_path = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "databento" / normalized_name / "spy_bar.jsonl"
        bars_by_date = _load_bars_by_date(bar_path)
        for day in adapter["days"]:
            trade_date = day["date"]
            bars = bars_by_date.get(trade_date, [])
            regimes = _regime_labels(trade_date, vix_rows, macro_by_date)
            five = _opening_proxy(bars, open_minutes=5, decision_minute="09:35:00")
            fifteen = _opening_proxy(bars, open_minutes=15, decision_minute="09:45:00")
            existing_trades = existing_trades_by_date.get(trade_date, [])
            daily_rows.append(
                {
                    "date": trade_date,
                    "dataset": dataset_label,
                    "split": split,
                    "adapter_status": day.get("status"),
                    "adapter_direction": day.get("direction"),
                    "regimes": regimes,
                    "bar_count": len(bars),
                    "proxy_5m": five,
                    "proxy_15m": fifteen,
                    "existing_trade_count": len(existing_trades),
                    "existing_implementable_pnl": round(sum(_num(trade.get("implementable_pnl")) for trade in existing_trades), 6),
                    "existing_mid_pnl": round(sum(_num(trade.get("mid_pnl")) for trade in existing_trades), 6),
                    "existing_cost_drag": round(
                        sum(_num(trade.get("mid_pnl")) - _num(trade.get("implementable_pnl")) for trade in existing_trades),
                        6,
                    ),
                }
            )

    search_trials = _search_trials(daily_rows)
    _write_search_log(search_trials, search_log_path)
    result = _summary(prereg, daily_rows, search_trials, preregistration_path, search_log_path)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(_render_report(result), encoding="utf-8")
    return result


def _summary(
    prereg: dict[str, Any],
    daily_rows: list[dict[str, Any]],
    search_trials: list[dict[str, Any]],
    preregistration_path: Path,
    search_log_path: Path,
) -> dict[str, Any]:
    proxy_5m = _proxy_summary(daily_rows, "proxy_5m")
    proxy_15m = _proxy_summary(daily_rows, "proxy_15m")
    trade_reconciliation = _existing_trade_reconciliation(daily_rows)
    coherence = _coherence(proxy_5m, proxy_15m, trade_reconciliation)
    conclusion, reason, next_action = _decision(coherence)
    return {
        "record_type": "experiment_summary",
        "schema_version": "h_a2_lower_resolution_proxy_v1",
        "experiment_id": "h_a2_lower_resolution_proxy",
        "hypothesis_id": "H-A2",
        "evidence_tier": "E1",
        "status": "complete",
        "conclusion": conclusion,
        "conclusion_reason": reason,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "research_log_required": True,
        "research_log_slug": "higanbana-h-a2-lower-resolution-proxy",
        "source_preregistration": _relative(preregistration_path),
        "source_artifacts": prereg.get("source_artifacts", {}),
        "network_used": False,
        "paid_data_used": False,
        "new_provider_used": False,
        "ibkr_request_used": False,
        "llm_call_used": False,
        "paper_trading_allowed": False,
        "operational_validation_allowed": False,
        "real_money_allowed": False,
        "exact_2022_orb_tested": False,
        "strategy_use_allowed": False,
        "methodology": {
            "minimum_data_resolution": prereg.get("minimum_data_resolution"),
            "split_policy": prereg.get("split_policy"),
            "decision_timestamp_policy": (
                "Prior-close VIX/VXV is used for ex-ante volatility labels. Scheduled same-day macro labels are treated as "
                "known before entry. Same-day post-entry market data is not used to define a filter."
            ),
            "proxy_scope": "Mechanism proxy only; not an exact 2022 ORB backtest and not deployable evidence.",
        },
        "trial_policy": {
            "trial_count": len(search_trials),
            "all_trials_recorded": True,
            "search_log": _relative(search_log_path),
            "dsr_status": "diagnostic_not_acceptance",
            "dsr_reason": (
                "The run records all pre-registered proxy/regime trials, but it does not select a best Sharpe as acceptance evidence. "
                "DSR remains required for any future acceptance-grade Sharpe comparison."
            ),
        },
        "sample_policy": {
            "mintrl_psr_status": "not_acceptance_grade",
            "mintrl_psr_reason": (
                "The proxy rows are not treated as a deployable return series. Existing option outcomes remain under-sampled and "
                "must keep MinTRL/PSR labels from acceptance gates before any E2 claim."
            ),
            "under_sampled": True,
            "underpowered": True,
        },
        "big_day_dependency": _big_day_dependency(trade_reconciliation),
        "proxy_5m": proxy_5m,
        "proxy_15m": proxy_15m,
        "existing_trade_reconciliation": trade_reconciliation,
        "coherence_assessment": coherence,
        "tier_blockers": [
            "E1 lower-resolution proxy only",
            "No exact 2022-10 ORB entries/exits tested",
            "No new independent data",
            "Existing option outcomes remain under-sampled and underpowered",
            "No E2 acceptance claim",
            "No paper trading, operational validation, or real-money approval",
        ],
        "allowed_claims": [
            "H-A2 can be weakened, falsified at proxy level, or prioritized for exact-data work.",
            "This result may guide whether exact SPY 1-minute bar sourcing is worth revisiting.",
        ],
        "forbidden_claims": prereg.get("forbidden_claims", []),
        "next_safe_action": next_action,
        "daily_row_count": len(daily_rows),
        "daily_rows": daily_rows,
    }


def _proxy_summary(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    valid = [row for row in rows if row[field]["status"] == "measured"]
    by_split = {split: _proxy_group([row for row in valid if row["split"] == split], field) for split in ["in_sample", "oos"]}
    by_regime = {
        "prior_high_vix": _proxy_group([row for row in valid if row["regimes"]["prior_high_vix"]], field),
        "prior_not_high_vix": _proxy_group([row for row in valid if not row["regimes"]["prior_high_vix"]], field),
        "prior_stress_vix": _proxy_group([row for row in valid if row["regimes"]["prior_stress_vix"]], field),
        "high_importance_macro": _proxy_group([row for row in valid if row["regimes"]["high_importance_macro"]], field),
        "no_high_importance_macro": _proxy_group([row for row in valid if not row["regimes"]["high_importance_macro"]], field),
        "combined_risk": _proxy_group(
            [row for row in valid if row["regimes"]["prior_high_vix"] or row["regimes"]["high_importance_macro"]],
            field,
        ),
        "non_risk": _proxy_group(
            [row for row in valid if not row["regimes"]["prior_high_vix"] and not row["regimes"]["high_importance_macro"]],
            field,
        ),
    }
    return {
        "measured_day_count": len(valid),
        "missing_day_count": len(rows) - len(valid),
        "overall": _proxy_group(valid, field),
        "by_split": by_split,
        "by_regime": by_regime,
    }


def _proxy_group(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    signals = [row for row in rows if row[field]["signal"] != "none"]
    values = [float(row[field]["directional_followthrough_to_close_pct"]) for row in signals]
    positive = [value for value in values if value > 0]
    return {
        "day_count": len(rows),
        "signal_count": len(signals),
        "signal_rate": _round(len(signals) / len(rows)) if rows else 0.0,
        "positive_followthrough_count": len(positive),
        "positive_followthrough_rate": _round(len(positive) / len(values)) if values else None,
        "avg_directional_followthrough_to_close_pct": _round(mean(values)) if values else None,
        "avg_abs_opening_range_pct": _round(mean(float(row[field]["opening_range_pct"]) for row in rows)) if rows else None,
    }


def _existing_trade_reconciliation(rows: list[dict[str, Any]]) -> dict[str, Any]:
    trade_rows = [row for row in rows if row["existing_trade_count"] > 0]
    groups = {
        "all": trade_rows,
        "in_sample": [row for row in trade_rows if row["split"] == "in_sample"],
        "oos": [row for row in trade_rows if row["split"] == "oos"],
        "prior_high_vix": [row for row in trade_rows if row["regimes"]["prior_high_vix"]],
        "prior_not_high_vix": [row for row in trade_rows if not row["regimes"]["prior_high_vix"]],
        "high_importance_macro": [row for row in trade_rows if row["regimes"]["high_importance_macro"]],
        "no_high_importance_macro": [row for row in trade_rows if not row["regimes"]["high_importance_macro"]],
        "combined_risk": [
            row for row in trade_rows if row["regimes"]["prior_high_vix"] or row["regimes"]["high_importance_macro"]
        ],
        "non_risk": [
            row for row in trade_rows if not row["regimes"]["prior_high_vix"] and not row["regimes"]["high_importance_macro"]
        ],
    }
    return {name: _trade_group(group) for name, group in groups.items()}


def _trade_group(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [float(row["existing_implementable_pnl"]) for row in rows]
    mid_values = [float(row["existing_mid_pnl"]) for row in rows]
    return {
        "trade_day_count": len(rows),
        "total_implementable_pnl": _round(sum(values)),
        "total_mid_pnl": _round(sum(mid_values)),
        "total_cost_drag": _round(sum(mid_values) - sum(values)),
        "avg_implementable_pnl": _round(mean(values)) if values else None,
        "win_rate": _round(sum(1 for value in values if value > 0) / len(values)) if values else None,
        "worst_day_pnl": min(values) if values else None,
        "best_day_pnl": max(values) if values else None,
    }


def _coherence(proxy_5m: dict[str, Any], proxy_15m: dict[str, Any], trades: dict[str, Any]) -> dict[str, Any]:
    five_risk = proxy_5m["by_regime"]["combined_risk"]["avg_directional_followthrough_to_close_pct"]
    five_non = proxy_5m["by_regime"]["non_risk"]["avg_directional_followthrough_to_close_pct"]
    fifteen_risk = proxy_15m["by_regime"]["combined_risk"]["avg_directional_followthrough_to_close_pct"]
    fifteen_non = proxy_15m["by_regime"]["non_risk"]["avg_directional_followthrough_to_close_pct"]
    trade_risk = trades["combined_risk"]["avg_implementable_pnl"]
    trade_non = trades["non_risk"]["avg_implementable_pnl"]

    proxy_supports_non_risk = _less(five_risk, five_non) and _less(fifteen_risk, fifteen_non)
    trades_support_non_risk = _less(trade_risk, trade_non)
    return {
        "proxy_supports_non_risk": proxy_supports_non_risk,
        "existing_trades_support_non_risk": trades_support_non_risk,
        "directionally_coherent": proxy_supports_non_risk and trades_support_non_risk,
        "five_min_risk_minus_non_risk": _diff(five_risk, five_non),
        "fifteen_min_risk_minus_non_risk": _diff(fifteen_risk, fifteen_non),
        "trade_avg_pnl_risk_minus_non_risk": _diff(trade_risk, trade_non),
        "interpretation": (
            "Risk-labeled macro/VIX days underperform non-risk days in both lower-resolution proxies and existing trade outcomes."
            if proxy_supports_non_risk and trades_support_non_risk
            else "The lower-resolution proxy and existing trade outcomes are not fully directionally coherent."
        ),
    }


def _decision(coherence: dict[str, Any]) -> tuple[str, str, str]:
    if coherence["directionally_coherent"]:
        return (
            "ยังสรุปไม่ได้",
            (
                "The proxy and existing trade outcomes are directionally coherent with H-A2 risk-filter intuition, but the evidence is "
                "E1 only, under-sampled, and not an exact 2022 ORB test."
            ),
            (
                "Keep H-A2 active and implement the exact-data prioritization decision only after reviewing whether the proxy result "
                "justifies a narrowly scoped 2022 underlying-bar source plan."
            ),
        )
    return (
        "ยังสรุปไม่ได้",
        (
            "The proxy does not cleanly falsify H-A2, but it also does not provide enough coherent support to justify an exact-source "
            "chase as acceptance work."
        ),
        "Revise or narrow H-A2 before spending money or requesting IBKR bars.",
    )


def _search_trials(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    trials = []
    for index, (proxy_field, resolution) in enumerate([("proxy_5m", "5-minute"), ("proxy_15m", "15-minute")], start=1):
        summary = _proxy_summary(rows, proxy_field)
        for regime in ["prior_high_vix", "high_importance_macro", "combined_risk"]:
            group = summary["by_regime"][regime]
            trials.append(
                {
                    "trial_index": len(trials) + 1,
                    "test_id": f"{proxy_field}_{regime}",
                    "resolution": resolution,
                    "regime": regime,
                    "day_count": group["day_count"],
                    "signal_count": group["signal_count"],
                    "avg_directional_followthrough_to_close_pct": group["avg_directional_followthrough_to_close_pct"],
                    "selection_role": "pre_registered_proxy_trial",
                }
            )
    trades = _existing_trade_reconciliation(rows)
    trials.append(
        {
            "trial_index": len(trials) + 1,
            "test_id": "existing_trade_outcome_by_regime",
            "resolution": "existing exact-quote trade summaries",
            "regime": "combined_risk_vs_non_risk",
            "risk_avg_implementable_pnl": trades["combined_risk"]["avg_implementable_pnl"],
            "non_risk_avg_implementable_pnl": trades["non_risk"]["avg_implementable_pnl"],
            "selection_role": "pre_registered_reconciliation_trial",
        }
    )
    return trials


def _opening_proxy(bars: list[dict[str, Any]], open_minutes: int, decision_minute: str) -> dict[str, Any]:
    rth = [bar for bar in bars if "09:30:00" <= _time(bar) <= "15:45:00"]
    opening = [bar for bar in rth if "09:30:00" <= _time(bar) < _minute_after_open(open_minutes)]
    decision = _bar_at(rth, decision_minute)
    close_bar = _last_at_or_before(rth, "15:45:00")
    if not opening or decision is None or close_bar is None:
        return {"status": "missing_bars", "signal": "none"}
    opening_high = max(float(bar["high"]) for bar in opening)
    opening_low = min(float(bar["low"]) for bar in opening)
    opening_mid = (opening_high + opening_low) / 2
    decision_close = float(decision["close"])
    close_value = float(close_bar["close"])
    if decision_close > opening_high:
        signal = "call"
        directional = (close_value - decision_close) / decision_close
    elif decision_close < opening_low:
        signal = "put"
        directional = (decision_close - close_value) / decision_close
    else:
        signal = "none"
        directional = 0.0
    return {
        "status": "measured",
        "signal": signal,
        "opening_high": opening_high,
        "opening_low": opening_low,
        "opening_range_pct": _round((opening_high - opening_low) / opening_mid if opening_mid else 0.0),
        "decision_timestamp_et": decision["timestamp_et"],
        "decision_close": decision_close,
        "close_timestamp_et": close_bar["timestamp_et"],
        "close": close_value,
        "directional_followthrough_to_close_pct": _round(directional),
    }


def _regime_labels(trade_date: str, vix_rows: list[dict[str, Any]], macro_by_date: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    prior = previous_vix_record(trade_date, vix_rows)
    macro = macro_by_date.get(trade_date, [])
    high_macro = [event for event in macro if event.get("importance") == "high"]
    prior_vix = float(prior["vix_close"]) if prior else None
    prior_vxv = float(prior["vxv_close"]) if prior else None
    return {
        "prior_vix_date": prior.get("date") if prior else None,
        "prior_vix_close": prior_vix,
        "prior_vxv_close": prior_vxv,
        "prior_high_vix": prior_vix is not None and prior_vix >= 25.0,
        "prior_stress_vix": prior_vix is not None and prior_vix >= 30.0,
        "prior_vix_vxv_inverted": prior_vix is not None and prior_vxv is not None and prior_vix >= prior_vxv,
        "high_importance_macro": bool(high_macro),
        "high_importance_macro_event_types": sorted({event["event_type"] for event in high_macro}),
    }


def _big_day_dependency(trade_reconciliation: dict[str, Any]) -> dict[str, Any]:
    all_group = trade_reconciliation["all"]
    return {
        "status": "inherited_from_existing_baseline_required_for_acceptance",
        "trade_day_count": all_group["trade_day_count"],
        "reason": "This proxy run does not create a new deployable return series. Exact big-day dependency remains required for future acceptance evidence.",
    }


def _load_existing_trades_by_date(path: Path) -> dict[str, list[dict[str, Any]]]:
    summary = _load_json(path)
    trades: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for dataset in summary.get("datasets", []):
        component_path = Path(dataset.get("component_summary_path", ""))
        if not component_path.is_absolute():
            component_path = PROJECT_ROOT / component_path
        if not component_path.exists():
            continue
        component = _load_json(component_path)
        for trade in component.get("trades", []):
            if str(trade.get("status", "")).startswith("closed_"):
                trades[str(trade["date"])].append(trade)
    return trades


def _load_bars_by_date(path: Path) -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        rows[str(row["timestamp_et"])[:10]].append(row)
    return {day: sorted(values, key=lambda item: item["timestamp_et"]) for day, values in rows.items()}


def _write_search_log(trials: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in trials) + "\n", encoding="utf-8")


def _render_report(result: dict[str, Any]) -> str:
    lines = [
        "# H-A2 Lower-Resolution Proxy Test",
        "",
        "## Status",
        f"- Hypothesis: `{result['hypothesis_id']}`",
        f"- Evidence tier: `{result['evidence_tier']}`",
        f"- Conclusion: {result['conclusion']}",
        f"- Reason: {result['conclusion_reason']}",
        f"- Network used: `{result['network_used']}`",
        f"- Paid data used: `{result['paid_data_used']}`",
        f"- Paper trading allowed: `{result['paper_trading_allowed']}`",
        "",
        "## Proxy Summary",
        "| Proxy | Measured days | Signals | Signal rate | Risk avg follow-through | Non-risk avg follow-through |",
        "|:--|--:|--:|--:|--:|--:|",
    ]
    for label, key in [("5m", "proxy_5m"), ("15m", "proxy_15m")]:
        proxy = result[key]
        risk = proxy["by_regime"]["combined_risk"]
        non = proxy["by_regime"]["non_risk"]
        lines.append(
            f"| {label} | {proxy['measured_day_count']} | {proxy['overall']['signal_count']} | {proxy['overall']['signal_rate']} | "
            f"{risk['avg_directional_followthrough_to_close_pct']} | {non['avg_directional_followthrough_to_close_pct']} |"
        )
    trade = result["existing_trade_reconciliation"]
    lines.extend(
        [
            "",
            "## Existing Trade Reconciliation",
            "| Group | Trade days | Total implementable PnL | Avg implementable PnL | Win rate | Cost drag |",
            "|:--|--:|--:|--:|--:|--:|",
        ]
    )
    for group in ["all", "combined_risk", "non_risk", "high_importance_macro", "no_high_importance_macro"]:
        row = trade[group]
        lines.append(
            f"| `{group}` | {row['trade_day_count']} | {row['total_implementable_pnl']} | {row['avg_implementable_pnl']} | "
            f"{row['win_rate']} | {row['total_cost_drag']} |"
        )
    lines.extend(
        [
            "",
            "## Coherence Assessment",
            "```json",
            json.dumps(result["coherence_assessment"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Tier Blockers",
        ]
    )
    lines.extend(f"- `{item}`" for item in result["tier_blockers"])
    lines.extend(["", "## Next Safe Action", "", result["next_safe_action"], ""])
    return "\n".join(lines)


def _time(row: dict[str, Any]) -> str:
    return str(row["timestamp_et"])[11:19]


def _minute_after_open(minutes: int) -> str:
    total_minutes = 9 * 60 + 30 + minutes
    return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}:00"


def _bar_at(rows: list[dict[str, Any]], target_time: str) -> dict[str, Any] | None:
    for row in rows:
        if _time(row) == target_time:
            return row
    return None


def _last_at_or_before(rows: list[dict[str, Any]], target_time: str) -> dict[str, Any] | None:
    candidates = [row for row in rows if _time(row) <= target_time]
    return candidates[-1] if candidates else None


def _diff(left: float | None, right: float | None) -> float | None:
    return None if left is None or right is None else _round(left - right)


def _less(left: float | None, right: float | None) -> bool:
    return left is not None and right is not None and left < right


def _num(value: Any) -> float:
    return float(value) if isinstance(value, (int, float)) else 0.0


def _round(value: float) -> float:
    return round(float(value), 6)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run H-A2 lower-resolution proxy test using local data only.")
    parser.add_argument("--preregistration-path", type=Path, default=DEFAULT_PREREGISTRATION_PATH)
    parser.add_argument("--summary-path", type=Path, default=DEFAULT_SUMMARY_PATH)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--search-log-path", type=Path, default=DEFAULT_SEARCH_LOG_PATH)
    args = parser.parse_args(argv)

    result = run_proxy(
        preregistration_path=args.preregistration_path,
        summary_path=args.summary_path,
        report_path=args.report_path,
        search_log_path=args.search_log_path,
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "hypothesis_id": result["hypothesis_id"],
                "evidence_tier": result["evidence_tier"],
                "conclusion": result["conclusion"],
                "summary_path": _relative(args.summary_path),
                "report_path": _relative(args.report_path),
                "search_log_path": _relative(args.search_log_path),
                "daily_row_count": result["daily_row_count"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
