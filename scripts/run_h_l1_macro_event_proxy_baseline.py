from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PREREGISTRATION_PATH = PROJECT_ROOT / "experiments" / "h_l1_macro_event_proxy_preregistration.json"
DEFAULT_SOURCE_SUMMARY_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_lower_resolution_proxy_summary.json"
DEFAULT_SUMMARY_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_l1_macro_event_proxy_baseline_summary.json"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_l1_macro_event_proxy_baseline_report.md"
DEFAULT_SEARCH_LOG_PATH = PROJECT_ROOT / "reports" / "experiments" / "search_logs" / "h_l1_macro_event_proxy_baseline_search_log.jsonl"


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
    result = _summary(prereg, rows, trials, preregistration_path, source_summary_path, search_log_path)

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(_render_report(result), encoding="utf-8")
    return result


def _summary(
    prereg: dict[str, Any],
    rows: list[dict[str, Any]],
    trials: list[dict[str, Any]],
    preregistration_path: Path,
    source_summary_path: Path,
    search_log_path: Path,
) -> dict[str, Any]:
    event_split = _event_vs_no_event(rows)
    vix_split = _vix_regime_split(rows)
    combined = _combined_baseline(rows)
    value_check = _future_news_collection_value(event_split, vix_split, combined)
    return {
        "record_type": "experiment_summary",
        "schema_version": "h_l1_macro_event_proxy_baseline_v1",
        "experiment_id": "h_l1_macro_event_proxy_baseline",
        "hypothesis_id": "H-L1",
        "evidence_tier": "E1",
        "status": "complete",
        "conclusion": "ยังสรุปไม่ได้",
        "conclusion_reason": (
            "Deterministic macro/VIX labels form a useful comparison baseline, but this is not real news or LLM evidence."
        ),
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "research_log_required": True,
        "research_log_slug": "higanbana-h-l1-macro-event-proxy-baseline",
        "source_preregistration": _relative(preregistration_path),
        "source_summary": _relative(source_summary_path),
        "not_llm_news_evidence": True,
        "network_used": False,
        "paid_data_used": False,
        "new_provider_used": False,
        "gdelt_retry_used": False,
        "llm_call_used": False,
        "broker_request_used": False,
        "paper_trading_allowed": False,
        "operational_validation_allowed": False,
        "real_money_allowed": False,
        "llm_gate_tested": False,
        "real_news_tested": False,
        "methodology": {
            "deterministic_labels_only": True,
            "chronological_split_required": True,
            "random_split_used": False,
            "oos_tuning_used": False,
            "decision_timestamp_policy": prereg.get("baseline_definition", {}).get("decision_timestamp_policy"),
        },
        "trial_policy": {
            "trial_count": len(trials),
            "all_trials_recorded": True,
            "search_log": _relative(search_log_path),
            "dsr_status": "diagnostic_not_acceptance",
            "dsr_reason": "No best Sharpe or best prompt is selected; this is a deterministic baseline.",
        },
        "sample_policy": {
            "mintrl_psr_status": "blocked_not_acceptance_return_series",
            "under_sampled": True,
            "underpowered": True,
            "reason": "Existing trade outcomes are sparse and proxy rows are not deployable return evidence.",
        },
        "event_vs_no_event_outcome_split": event_split,
        "vix_regime_outcome_split": vix_split,
        "combined_macro_vix_baseline": combined,
        "future_news_collection_value_check": value_check,
        "tier_blockers": [
            "E1 deterministic proxy only",
            "No real timestamp-clean news cases",
            "No LLM call or LLM gate test",
            "No prompt stability or contamination test",
            "No E2 acceptance claim",
            "No paper trading, operational validation, or real-money approval",
        ],
        "allowed_claims": prereg.get("allowed_claims", []),
        "forbidden_claims": prereg.get("forbidden_claims", []),
        "next_safe_action": value_check["news_collection_priority_decision"],
    }


def _event_vs_no_event(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups = {
        "high_importance_macro": [row for row in rows if row["regimes"]["high_importance_macro"]],
        "no_high_importance_macro": [row for row in rows if not row["regimes"]["high_importance_macro"]],
    }
    return {"status": "complete", "groups": {name: _baseline_group(group) for name, group in groups.items()}}


def _vix_regime_split(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups = {
        "prior_high_vix": [row for row in rows if row["regimes"]["prior_high_vix"]],
        "prior_not_high_vix": [row for row in rows if not row["regimes"]["prior_high_vix"]],
        "prior_stress_vix": [row for row in rows if row["regimes"]["prior_stress_vix"]],
        "prior_vix_vxv_inverted": [row for row in rows if row["regimes"]["prior_vix_vxv_inverted"]],
    }
    return {"status": "complete", "groups": {name: _baseline_group(group) for name, group in groups.items()}}


def _combined_baseline(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups = {
        "macro_event_only": [row for row in rows if row["regimes"]["high_importance_macro"] and not row["regimes"]["prior_high_vix"]],
        "vix_risk_only": [row for row in rows if row["regimes"]["prior_high_vix"] and not row["regimes"]["high_importance_macro"]],
        "macro_plus_vix_risk": [row for row in rows if row["regimes"]["high_importance_macro"] and row["regimes"]["prior_high_vix"]],
        "no_macro_no_vix_risk": [row for row in rows if not row["regimes"]["high_importance_macro"] and not row["regimes"]["prior_high_vix"]],
    }
    group_metrics = {name: _baseline_group(group) for name, group in groups.items()}
    clean = group_metrics["no_macro_no_vix_risk"]["trade_outcomes"]["avg_implementable_pnl"]
    macro_only = group_metrics["macro_event_only"]["trade_outcomes"]["avg_implementable_pnl"]
    macro_plus_vix = group_metrics["macro_plus_vix_risk"]["trade_outcomes"]["avg_implementable_pnl"]
    return {
        "status": "complete",
        "groups": group_metrics,
        "future_llm_incremental_information_target": (
            "Future H-L1 LLM/news scores must explain residual adverse days beyond these deterministic macro/VIX labels."
        ),
        "clean_minus_macro_only_avg_trade_pnl": _diff(clean, macro_only),
        "clean_minus_macro_plus_vix_avg_trade_pnl": _diff(clean, macro_plus_vix),
    }


def _future_news_collection_value(
    event_split: dict[str, Any],
    vix_split: dict[str, Any],
    combined: dict[str, Any],
) -> dict[str, Any]:
    clean_minus_risk = combined["clean_minus_macro_only_avg_trade_pnl"]
    deterministic_signal_present = clean_minus_risk is not None and clean_minus_risk > 0
    return {
        "status": "complete",
        "baseline_strength_note": (
            "Deterministic labels show useful risk separation." if deterministic_signal_present else "Deterministic labels are weak or under-sampled."
        ),
        "residual_risk_note": (
            "This baseline cannot read unscheduled news, wording, surprise severity, or market narrative; H-L1 still needs real timestamp-clean cases."
        ),
        "deterministic_signal_present": deterministic_signal_present,
        "news_collection_priority_decision": (
            "Keep live LLM research blocked, but continue timestamp-clean news collection when source cooldown/policy allows; future LLM scores must beat this deterministic baseline."
        ),
        "forbidden_claim_check": {
            "llm_gate_tested": False,
            "real_news_tested": False,
            "timestamp_clean_news_cases_exist": False,
        },
        "event_trade_day_count": event_split["groups"]["high_importance_macro"]["trade_outcomes"]["trade_day_count"],
        "vix_trade_day_count": vix_split["groups"]["prior_high_vix"]["trade_outcomes"]["trade_day_count"],
    }


def _baseline_group(rows: list[dict[str, Any]]) -> dict[str, Any]:
    trade_rows = [row for row in rows if row["existing_trade_count"] > 0]
    return {
        "sample_count": len(rows),
        "split_counts": _split_counts(rows),
        "proxy_5m": _proxy_group(rows, "proxy_5m"),
        "proxy_15m": _proxy_group(rows, "proxy_15m"),
        "trade_outcomes": _trade_group(trade_rows),
        "adverse_trade_day_rate": _adverse_rate(trade_rows),
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
    }


def _adverse_rate(rows: list[dict[str, Any]]) -> float | None:
    if not rows:
        return None
    return _round(sum(1 for row in rows if float(row["existing_implementable_pnl"]) < 0) / len(rows))


def _search_trials(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {"trial_id": "event_vs_no_event_outcome_split", "sample_count": len(rows), "selected_as_best": False},
        {"trial_id": "vix_regime_outcome_split", "sample_count": len(rows), "selected_as_best": False},
        {"trial_id": "combined_macro_vix_baseline", "sample_count": len(rows), "selected_as_best": False},
        {"trial_id": "future_news_collection_value_check", "sample_count": len(rows), "selected_as_best": False},
    ]


def _write_search_log(trials: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for trial in trials:
            handle.write(json.dumps(trial, ensure_ascii=False, sort_keys=True) + "\n")


def _render_report(result: dict[str, Any]) -> str:
    combined = result["combined_macro_vix_baseline"]["groups"]
    return "\n".join(
        [
            "# H-L1 Macro-Event Proxy Baseline Report",
            "",
            f"- Conclusion: {result['conclusion']} ({result['evidence_tier']})",
            f"- Not LLM/news evidence: {result['not_llm_news_evidence']}",
            f"- Deterministic signal present: {result['future_news_collection_value_check']['deterministic_signal_present']}",
            "",
            "## Combined Macro / VIX Baseline",
            "",
            "| Bucket | Days | 5m avg | 15m avg | Trade days | Avg implementable PnL | Adverse trade-day rate |",
            "|:--|--:|--:|--:|--:|--:|--:|",
            *[
                (
                    f"| {name} | {group['sample_count']} | "
                    f"{group['proxy_5m']['avg_directional_followthrough_to_close_pct']} | "
                    f"{group['proxy_15m']['avg_directional_followthrough_to_close_pct']} | "
                    f"{group['trade_outcomes']['trade_day_count']} | {group['trade_outcomes']['avg_implementable_pnl']} | "
                    f"{group['adverse_trade_day_rate']} |"
                )
                for name, group in combined.items()
            ],
            "",
            "## Guardrails",
            "",
            "- No network, paid data, GDELT retry, broker request, new provider, or LLM call was used.",
            "- This result cannot validate an LLM gate or real news sentiment.",
            f"- Next safe action: {result['next_safe_action']}",
            "",
        ]
    )


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
