from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PREREGISTRATION_PATH = PROJECT_ROOT / "experiments" / "h_a2_proxy_first_robustness_preregistration.json"
DEFAULT_SOURCE_SUMMARY_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_lower_resolution_proxy_summary.json"
DEFAULT_SUMMARY_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_proxy_first_robustness_summary.json"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_proxy_first_robustness_report.md"
DEFAULT_SEARCH_LOG_PATH = PROJECT_ROOT / "reports" / "experiments" / "search_logs" / "h_a2_proxy_first_robustness_search_log.jsonl"


def run_experiment(
    preregistration_path: Path = DEFAULT_PREREGISTRATION_PATH,
    source_summary_path: Path = DEFAULT_SOURCE_SUMMARY_PATH,
    summary_path: Path = DEFAULT_SUMMARY_PATH,
    report_path: Path = DEFAULT_REPORT_PATH,
    search_log_path: Path = DEFAULT_SEARCH_LOG_PATH,
) -> dict[str, Any]:
    prereg = _load_json(preregistration_path)
    source = _load_json(source_summary_path)
    rows = list(source["daily_rows"])

    trials = _search_trials(rows)
    _write_search_log(trials, search_log_path)
    result = _summary(prereg, source, rows, trials, preregistration_path, source_summary_path, search_log_path)

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(_render_report(result), encoding="utf-8")
    return result


def _summary(
    prereg: dict[str, Any],
    source: dict[str, Any],
    rows: list[dict[str, Any]],
    trials: list[dict[str, Any]],
    preregistration_path: Path,
    source_summary_path: Path,
    search_log_path: Path,
) -> dict[str, Any]:
    resolution = _resolution_monotonicity(rows)
    separation = _macro_vix_separation(rows)
    reconciliation = _existing_trade_reconciliation(rows)
    fragility = _fragility_and_big_day(rows)
    coherent = bool(resolution["directionally_consistent"] and reconciliation["risk_non_risk_direction_consistent"])
    next_action = (
        "Use H-A2.19 as E1 prioritization evidence only: proxy evidence remains directionally coherent, but exact "
        "2022-10 ORB replay still requires real 2022 SPY bars before any E2 claim."
        if coherent
        else "Revise or park H-A2 before spending effort on exact 2022 SPY bars; proxy evidence is not directionally coherent."
    )
    return {
        "record_type": "experiment_summary",
        "schema_version": "h_a2_proxy_first_robustness_v1",
        "experiment_id": "h_a2_proxy_first_robustness",
        "hypothesis_id": "H-A2",
        "evidence_tier": "E1",
        "status": "complete",
        "conclusion": "ยังสรุปไม่ได้",
        "conclusion_reason": (
            "Proxy evidence is useful for prioritization, but it is not exact entry/exit replay and remains under-sampled for acceptance."
        ),
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "research_log_required": True,
        "research_log_slug": "higanbana-h-a2-proxy-first-robustness",
        "source_preregistration": _relative(preregistration_path),
        "source_summary": _relative(source_summary_path),
        "source_summary_experiment_id": source.get("experiment_id"),
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
            "proxy_scope": "Uses existing local H-A2.13 daily rows only; this is mechanism-level proxy evidence.",
            "chronological_split_required": True,
            "random_split_used": False,
            "oos_tuning_used": False,
            "one_minute_required_for_exact_replay": True,
            "one_minute_required_for_this_proxy_test": False,
        },
        "trial_policy": {
            "trial_count": len(trials),
            "all_trials_recorded": True,
            "search_log": _relative(search_log_path),
            "dsr_status": "diagnostic_not_acceptance",
            "dsr_reason": "All pre-registered checks are logged; no best Sharpe is selected as acceptance evidence.",
        },
        "sample_policy": {
            "mintrl_psr_status": "blocked_not_acceptance_return_series",
            "under_sampled": True,
            "underpowered": True,
            "reason": "Existing option-trade rows remain too sparse for E2 acceptance; proxy rows are not deployable returns.",
        },
        "sample_counts": {
            "daily_rows": len(rows),
            "measured_5m_days": _measured_count(rows, "proxy_5m"),
            "measured_15m_days": _measured_count(rows, "proxy_15m"),
            "trade_days": len([row for row in rows if row["existing_trade_count"] > 0]),
            "split_counts": _split_counts(rows),
        },
        "resolution_monotonicity_check": resolution,
        "macro_vix_separation_check": separation,
        "existing_trade_reconciliation_check": reconciliation,
        "fragility_and_big_day_check": fragility,
        "tier_blockers": [
            "E1 proxy evidence only",
            "No exact 2022-10 ORB replay",
            "No independent new data",
            "Existing option outcomes remain under-sampled and underpowered",
            "No E2 acceptance claim",
            "No paper trading, operational validation, or real-money approval",
        ],
        "allowed_claims": prereg.get("allowed_claims", []),
        "forbidden_claims": prereg.get("forbidden_claims", []),
        "next_safe_action": next_action,
    }


def _resolution_monotonicity(rows: list[dict[str, Any]]) -> dict[str, Any]:
    proxy_5m = _risk_vs_non_risk_proxy(rows, "proxy_5m")
    proxy_15m = _risk_vs_non_risk_proxy(rows, "proxy_15m")
    trades = _risk_vs_non_risk_trades(rows)
    comparisons = [proxy_5m["non_risk_minus_risk"], proxy_15m["non_risk_minus_risk"], trades["non_risk_minus_risk"]]
    return {
        "status": "complete",
        "proxy_5m": proxy_5m,
        "proxy_15m": proxy_15m,
        "existing_trade_outcomes": trades,
        "directionally_consistent": all(value is not None and value > 0 for value in comparisons),
        "directional_consistency_note": "Positive values mean non-risk days outperform combined macro/VIX risk days.",
    }


def _macro_vix_separation(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups = {
        "macro_only": [row for row in rows if row["regimes"]["high_importance_macro"] and not row["regimes"]["prior_high_vix"]],
        "vix_risk_only": [row for row in rows if row["regimes"]["prior_high_vix"] and not row["regimes"]["high_importance_macro"]],
        "macro_plus_vix_risk": [row for row in rows if row["regimes"]["high_importance_macro"] and row["regimes"]["prior_high_vix"]],
        "no_macro_no_vix_risk": [row for row in rows if not row["regimes"]["high_importance_macro"] and not row["regimes"]["prior_high_vix"]],
    }
    return {
        "status": "complete",
        "groups": {name: _combined_group(group) for name, group in groups.items()},
        "interpretation": "This separates macro labels from prior-close VIX risk instead of adding more policy rules.",
    }


def _existing_trade_reconciliation(rows: list[dict[str, Any]]) -> dict[str, Any]:
    trade_rows = [row for row in rows if row["existing_trade_count"] > 0]
    groups = {
        "all": trade_rows,
        "in_sample": [row for row in trade_rows if row["split"] == "in_sample"],
        "oos": [row for row in trade_rows if row["split"] == "oos"],
        "combined_risk": [row for row in trade_rows if _is_risk(row)],
        "non_risk": [row for row in trade_rows if not _is_risk(row)],
    }
    risk = _trade_group(groups["combined_risk"])["avg_implementable_pnl"]
    non = _trade_group(groups["non_risk"])["avg_implementable_pnl"]
    return {
        "status": "complete",
        "groups": {name: _trade_group(group) for name, group in groups.items()},
        "risk_non_risk_direction_consistent": risk is not None and non is not None and non > risk,
        "no_oos_tuning_statement": "No threshold or filter was tuned on OOS in this run; labels were inherited from preregistered source rows.",
    }


def _fragility_and_big_day(rows: list[dict[str, Any]]) -> dict[str, Any]:
    trade_rows = [row for row in rows if row["existing_trade_count"] > 0]
    ordered = sorted(trade_rows, key=lambda row: float(row["existing_implementable_pnl"]))
    trim_n = max(1, round(len(ordered) * 0.05)) if len(ordered) >= 20 else 0
    trimmed = ordered[trim_n : len(ordered) - trim_n] if trim_n else ordered
    before = _risk_vs_non_risk_trades(trade_rows)
    after = _risk_vs_non_risk_trades(trimmed)
    return {
        "status": "diagnostic_underpowered",
        "trade_day_count": len(trade_rows),
        "trimmed_each_tail_count": trim_n,
        "before_trim": before,
        "after_trim": after,
        "survives_extreme_trim": after["non_risk_minus_risk"] is not None and after["non_risk_minus_risk"] > 0,
        "under_sampled": True,
        "underpowered": True,
        "mintrl_psr_or_blocker": "Blocked for acceptance; trade sample is diagnostic only.",
    }


def _combined_group(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "sample_count": len(rows),
        "split_counts": _split_counts(rows),
        "proxy_5m": _proxy_group(rows, "proxy_5m"),
        "proxy_15m": _proxy_group(rows, "proxy_15m"),
        "trade_outcomes": _trade_group([row for row in rows if row["existing_trade_count"] > 0]),
    }


def _proxy_group(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    measured = [row for row in rows if row[field]["status"] == "measured"]
    signals = [row for row in measured if row[field]["signal"] != "none"]
    values = [float(row[field]["directional_followthrough_to_close_pct"]) for row in signals]
    return {
        "measured_day_count": len(measured),
        "signal_count": len(signals),
        "avg_directional_followthrough_to_close_pct": _round(mean(values)) if values else None,
        "positive_followthrough_rate": _round(sum(1 for value in values if value > 0) / len(values)) if values else None,
    }


def _trade_group(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [float(row["existing_implementable_pnl"]) for row in rows]
    mid_values = [float(row["existing_mid_pnl"]) for row in rows]
    return {
        "trade_day_count": len(rows),
        "total_implementable_pnl": _round(sum(values)),
        "avg_implementable_pnl": _round(mean(values)) if values else None,
        "win_rate": _round(sum(1 for value in values if value > 0) / len(values)) if values else None,
        "total_mid_pnl": _round(sum(mid_values)),
        "total_cost_drag": _round(sum(mid_values) - sum(values)),
        "worst_day_pnl": min(values) if values else None,
        "best_day_pnl": max(values) if values else None,
    }


def _risk_vs_non_risk_proxy(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    risk = _proxy_group([row for row in rows if _is_risk(row)], field)
    non = _proxy_group([row for row in rows if not _is_risk(row)], field)
    diff = _diff(non["avg_directional_followthrough_to_close_pct"], risk["avg_directional_followthrough_to_close_pct"])
    return {"risk": risk, "non_risk": non, "non_risk_minus_risk": diff}


def _risk_vs_non_risk_trades(rows: list[dict[str, Any]]) -> dict[str, Any]:
    trade_rows = [row for row in rows if row["existing_trade_count"] > 0]
    risk = _trade_group([row for row in trade_rows if _is_risk(row)])
    non = _trade_group([row for row in trade_rows if not _is_risk(row)])
    return {"risk": risk, "non_risk": non, "non_risk_minus_risk": _diff(non["avg_implementable_pnl"], risk["avg_implementable_pnl"])}


def _search_trials(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {"trial_id": "resolution_monotonicity_check", "sample_count": len(rows), "selected_as_best": False},
        {"trial_id": "macro_vix_separation_check", "sample_count": len(rows), "selected_as_best": False},
        {
            "trial_id": "existing_trade_reconciliation_check",
            "sample_count": len([row for row in rows if row["existing_trade_count"] > 0]),
            "selected_as_best": False,
        },
        {
            "trial_id": "fragility_and_big_day_check",
            "sample_count": len([row for row in rows if row["existing_trade_count"] > 0]),
            "selected_as_best": False,
        },
    ]


def _write_search_log(trials: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for trial in trials:
            handle.write(json.dumps(trial, ensure_ascii=False, sort_keys=True) + "\n")


def _render_report(result: dict[str, Any]) -> str:
    samples = result["sample_counts"]
    res = result["resolution_monotonicity_check"]
    sep = result["macro_vix_separation_check"]["groups"]
    return "\n".join(
        [
            "# H-A2 Proxy-First Robustness Report",
            "",
            f"- Conclusion: {result['conclusion']} ({result['evidence_tier']})",
            f"- Daily rows: {samples['daily_rows']}",
            f"- Measured 5m / 15m days: {samples['measured_5m_days']} / {samples['measured_15m_days']}",
            f"- Existing trade days: {samples['trade_days']}",
            f"- Directionally consistent: {res['directionally_consistent']}",
            f"- 5m non-risk minus risk: {res['proxy_5m']['non_risk_minus_risk']}",
            f"- 15m non-risk minus risk: {res['proxy_15m']['non_risk_minus_risk']}",
            f"- Existing trade non-risk minus risk: {res['existing_trade_outcomes']['non_risk_minus_risk']}",
            "",
            "## Macro / VIX Buckets",
            "",
            "| Bucket | Days | 5m avg | 15m avg | Trade days | Avg implementable PnL |",
            "|:--|--:|--:|--:|--:|--:|",
            *[
                (
                    f"| {name} | {group['sample_count']} | "
                    f"{group['proxy_5m']['avg_directional_followthrough_to_close_pct']} | "
                    f"{group['proxy_15m']['avg_directional_followthrough_to_close_pct']} | "
                    f"{group['trade_outcomes']['trade_day_count']} | {group['trade_outcomes']['avg_implementable_pnl']} |"
                )
                for name, group in sep.items()
            ],
            "",
            "## Guardrails",
            "",
            "- No network, paid data, broker request, new provider, or LLM call was used.",
            "- This is not exact 2022-10 ORB replay and does not approve paper trading.",
            f"- Next safe action: {result['next_safe_action']}",
            "",
        ]
    )


def _is_risk(row: dict[str, Any]) -> bool:
    return bool(row["regimes"]["prior_high_vix"] or row["regimes"]["high_importance_macro"])


def _measured_count(rows: list[dict[str, Any]], field: str) -> int:
    return len([row for row in rows if row[field]["status"] == "measured"])


def _split_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["split"]] = counts.get(row["split"], 0) + 1
    return counts


def _diff(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return _round(left - right)


def _round(value: float) -> float:
    return round(float(value), 6)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative(path: Path) -> str:
    return str(path.resolve().relative_to(PROJECT_ROOT)).replace("/", "\\")


if __name__ == "__main__":
    output = run_experiment()
    print(json.dumps({"status": output["status"], "conclusion": output["conclusion"]}, ensure_ascii=False))
