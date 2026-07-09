from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PREREGISTRATION_PATH = PROJECT_ROOT / "experiments" / "h_a2_residual_adverse_day_analysis_preregistration.json"
DEFAULT_SOURCE_SUMMARY_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_lower_resolution_proxy_summary.json"
DEFAULT_SUMMARY_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_residual_adverse_day_analysis.json"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_residual_adverse_day_analysis.md"
DEFAULT_SEARCH_LOG_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "search_logs" / "h_a2_residual_adverse_day_analysis_search_log.jsonl"


def run_analysis(
    preregistration_path: Path = DEFAULT_PREREGISTRATION_PATH,
    source_summary_path: Path = DEFAULT_SOURCE_SUMMARY_PATH,
    summary_path: Path = DEFAULT_SUMMARY_PATH,
    report_path: Path = DEFAULT_REPORT_PATH,
    search_log_path: Path = DEFAULT_SEARCH_LOG_PATH,
) -> dict[str, Any]:
    prereg = _load_json(preregistration_path)
    source = _load_json(source_summary_path)
    rows = list(source["daily_rows"])
    trade_rows = [row for row in rows if row["existing_trade_count"] > 0]

    trials = _search_trials(rows, trade_rows)
    _write_search_log(trials, search_log_path)
    result = _summary(prereg, source, rows, trade_rows, preregistration_path, source_summary_path, search_log_path)

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(_render_report(result), encoding="utf-8")
    return result


def _summary(
    prereg: dict[str, Any],
    source: dict[str, Any],
    rows: list[dict[str, Any]],
    trade_rows: list[dict[str, Any]],
    preregistration_path: Path,
    source_summary_path: Path,
    search_log_path: Path,
) -> dict[str, Any]:
    non_risk = [row for row in trade_rows if not _is_risk(row)]
    macro_only = [
        row
        for row in trade_rows
        if row["regimes"]["high_importance_macro"] and not row["regimes"]["prior_high_vix"]
    ]
    non_risk_losers = [row for row in non_risk if row["existing_implementable_pnl"] < 0]
    macro_only_losers = [row for row in macro_only if row["existing_implementable_pnl"] < 0]

    residual_profile = _residual_profile(non_risk_losers, non_risk)
    macro_profile = _macro_only_profile(macro_only_losers, macro_only)
    failure_mode = _failure_mode(non_risk_losers, non_risk)
    decision = _decision_rules(residual_profile, macro_profile, failure_mode)

    return {
        "record_type": "experiment_summary",
        "schema_version": "h_a2_residual_adverse_day_analysis_v1",
        "experiment_id": "h_a2_residual_adverse_day_analysis",
        "hypothesis_id": "H-A2",
        "evidence_tier": "E1",
        "status": "complete",
        "conclusion": "ยังสรุปไม่ได้",
        "conclusion_reason": (
            "Residual losses are real and frequent, but local labels show enough structure to justify a narrower H-A2 revision "
            "before exact replay; the sample remains underpowered and cannot validate an edge."
        ),
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "research_log_required": True,
        "research_log_slug": "higanbana-h-a2-residual-adverse-day-analysis",
        "source_preregistration": _relative(preregistration_path),
        "source_summary": _relative(source_summary_path),
        "source_summary_experiment_id": source.get("experiment_id"),
        "network_used": False,
        "paid_data_used": False,
        "new_provider_used": False,
        "broker_request_used": False,
        "ibkr_request_used": False,
        "gdelt_live_retry_used": False,
        "llm_call_used": False,
        "paper_trading_allowed": False,
        "operational_validation_allowed": False,
        "real_money_allowed": False,
        "exact_2022_orb_tested": False,
        "strategy_use_allowed": False,
        "methodology": {
            "local_artifacts_only": True,
            "chronological_split_required": True,
            "random_split_used": False,
            "oos_tuning_used": False,
            "no_new_filter_selected": True,
            "analysis_scope": prereg.get("analysis_scope", {}).get("allowed_input_scope"),
        },
        "trial_policy": {
            "trial_count": len(_search_trials(rows, trade_rows)),
            "all_trials_recorded": True,
            "search_log": _relative(search_log_path),
            "dsr_status": "not_acceptance_no_best_sharpe_selected",
            "dsr_reason": "The analysis applies pre-registered diagnostic buckets; it does not select a best Sharpe or new deployable filter.",
        },
        "sample_policy": {
            "mintrl_psr_status": "blocked_underpowered_e1_diagnostic",
            "under_sampled": True,
            "underpowered": True,
            "reason": "Only 90 existing trade days are available, and residual buckets are smaller than the full trade sample.",
        },
        "sample_counts": {
            "daily_rows": len(rows),
            "trade_days": len(trade_rows),
            "non_risk_trade_days": len(non_risk),
            "non_risk_losing_trade_days": len(non_risk_losers),
            "macro_only_trade_days": len(macro_only),
            "macro_only_losing_trade_days": len(macro_only_losers),
            "split_counts": _split_counts(trade_rows),
        },
        "residual_loss_bucket_profile": residual_profile,
        "macro_only_loss_profile": macro_profile,
        "non_risk_failure_mode_check": failure_mode,
        "decision_rule_application": decision,
        "big_day_dependency_context": {
            "source": "reports/experiments/h_a2_proxy_first_robustness_summary.json",
            "survives_extreme_trim": True,
            "before_trim_non_risk_minus_risk_trade_pnl": 23.375,
            "after_trim_non_risk_minus_risk_trade_pnl": 8.042741,
            "interpretation": "The directional gap survives but weakens materially after trimming, so this remains diagnostic rather than acceptance-grade.",
        },
        "tier_blockers": [
            "E1 diagnostic only",
            "Residual buckets are under-sampled and underpowered",
            "No exact 2022-10 ORB replay",
            "No new independent validation data",
            "No E2 acceptance claim",
            "No paper trading, operational validation, or real-money approval",
        ],
        "allowed_claims": prereg.get("allowed_claims", []),
        "forbidden_claims": prereg.get("forbidden_claims", []),
        "next_safe_action": decision["next_safe_action"],
    }


def _residual_profile(losers: list[dict[str, Any]], reference: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "status": "complete",
        "reference_trade_days": len(reference),
        "losing_trade_days": len(losers),
        "loss_rate": _rate(len(losers), len(reference)),
        "avg_losing_implementable_pnl": _avg([row["existing_implementable_pnl"] for row in losers]),
        "worst_losing_days": _top_losses(losers, 8),
        "split_counts": _split_counts(losers),
        "day_of_week_counts": _weekday_counts(losers),
        "prior_vix_state_counts": _prior_vix_state_counts(losers),
        "proxy_signal_counts": {
            "proxy_5m": _proxy_signal_counts(losers, "proxy_5m"),
            "proxy_15m": _proxy_signal_counts(losers, "proxy_15m"),
        },
        "interpretation": "Non-risk losses remain common, so the current clean/risk split is too coarse by itself.",
    }


def _macro_only_profile(losers: list[dict[str, Any]], reference: list[dict[str, Any]]) -> dict[str, Any]:
    event_types = Counter()
    for row in losers:
        event_types.update(row["regimes"].get("high_importance_macro_event_types", []))
    return {
        "status": "complete",
        "reference_trade_days": len(reference),
        "losing_trade_days": len(losers),
        "loss_rate": _rate(len(losers), len(reference)),
        "avg_losing_implementable_pnl": _avg([row["existing_implementable_pnl"] for row in losers]),
        "worst_losing_days": _top_losses(losers, 8),
        "macro_event_type_counts": dict(sorted(event_types.items())),
        "split_counts": _split_counts(losers),
        "proxy_signal_counts": {
            "proxy_5m": _proxy_signal_counts(losers, "proxy_5m"),
            "proxy_15m": _proxy_signal_counts(losers, "proxy_15m"),
        },
        "interpretation": "Macro-only losses are frequent enough that future H-L1 news/LLM work must add information beyond this deterministic label.",
    }


def _failure_mode(losers: list[dict[str, Any]], reference: list[dict[str, Any]]) -> dict[str, Any]:
    oos_losses = [row for row in losers if row["split"] == "oos"]
    measured_5m = [row for row in losers if row["proxy_5m"]["status"] == "measured"]
    negative_5m = [
        row
        for row in measured_5m
        if row["proxy_5m"].get("directional_followthrough_to_close_pct") is not None
        and row["proxy_5m"]["directional_followthrough_to_close_pct"] < 0
    ]
    return {
        "status": "complete",
        "non_risk_reference_days": len(reference),
        "non_risk_loss_days": len(losers),
        "oos_loss_days": len(oos_losses),
        "oos_loss_share": _rate(len(oos_losses), len(losers)),
        "negative_5m_followthrough_loss_days": len(negative_5m),
        "negative_5m_followthrough_loss_share": _rate(len(negative_5m), len(measured_5m)),
        "features_not_available_locally": [
            "real timestamp-clean news text",
            "exact 2022-10 SPY 1-minute replay",
            "pre-entry order-book or liquidity microstructure beyond current quotes",
        ],
        "revision_candidate": (
            "Revise H-A2 to require a cleaner opening-followthrough condition and explicitly test whether non-risk OOS losses "
            "cluster around weak 5-minute/15-minute followthrough before exact replay."
        ),
    }


def _decision_rules(
    residual_profile: dict[str, Any],
    macro_profile: dict[str, Any],
    failure_mode: dict[str, Any],
) -> dict[str, Any]:
    revise = bool(
        residual_profile["loss_rate"] is not None
        and residual_profile["loss_rate"] >= 0.5
        and failure_mode["negative_5m_followthrough_loss_days"] > 0
    )
    park = bool(failure_mode["oos_loss_share"] is not None and failure_mode["oos_loss_share"] >= 0.8)
    prioritize_exact = bool(revise and not park)
    if revise:
        decision = "revise_h_a2_before_exact_replay"
        next_safe_action = (
            "Pre-register a revised H-A2 condition that adds opening-followthrough failure-mode checks before any exact replay, "
            "paid data, IBKR request, LLM call, or paper trading."
        )
    elif park:
        decision = "park_h_a2_pending_new_mechanism"
        next_safe_action = "Park H-A2 until a new mechanism explains residual adverse days without OOS tuning."
    else:
        decision = "prioritize_exact_replay_when_external_bar_blocker_clears"
        next_safe_action = "Keep H-A2 active at E1 and prioritize exact replay only after the 2022 SPY bar blocker clears."
    return {
        "status": "complete",
        "revise_h_a2_rule_result": revise,
        "park_h_a2_rule_result": park,
        "prioritize_exact_replay_rule_result": prioritize_exact,
        "decision": decision,
        "evidence_tier": "E1",
        "blockers": [
            "under_sampled",
            "underpowered",
            "no_exact_2022_orb_replay",
            "no_e2_acceptance_claim",
        ],
        "next_safe_action": next_safe_action,
    }


def _search_trials(rows: list[dict[str, Any]], trade_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    non_risk = [row for row in trade_rows if not _is_risk(row)]
    macro_only = [row for row in trade_rows if row["regimes"]["high_importance_macro"] and not row["regimes"]["prior_high_vix"]]
    return [
        {"trial_id": "residual_loss_bucket_profile", "sample_count": len(non_risk), "selected_as_best": False},
        {"trial_id": "macro_only_loss_profile", "sample_count": len(macro_only), "selected_as_best": False},
        {"trial_id": "non_risk_failure_mode_check", "sample_count": len(non_risk), "selected_as_best": False},
        {"trial_id": "decision_rule_application", "sample_count": len(rows), "selected_as_best": False},
    ]


def _render_report(result: dict[str, Any]) -> str:
    samples = result["sample_counts"]
    residual = result["residual_loss_bucket_profile"]
    macro = result["macro_only_loss_profile"]
    decision = result["decision_rule_application"]
    lines = [
        "# H-A2 Residual Adverse-Day Analysis",
        "",
        f"- Status: `{result['status']}`",
        f"- Conclusion: `{result['conclusion']}`",
        f"- Evidence tier: `{result['evidence_tier']}`",
        f"- Research log required: `{result['research_log_required']}`",
        f"- Source preregistration: `{result['source_preregistration']}`",
        f"- Source summary: `{result['source_summary']}`",
        f"- Search log: `{result['trial_policy']['search_log']}`",
        "",
        "## Sample Counts",
        "",
        "| Bucket | Count |",
        "|:--|--:|",
        f"| Daily rows | {samples['daily_rows']} |",
        f"| Trade days | {samples['trade_days']} |",
        f"| Non-risk trade days | {samples['non_risk_trade_days']} |",
        f"| Non-risk losing trade days | {samples['non_risk_losing_trade_days']} |",
        f"| Macro-only trade days | {samples['macro_only_trade_days']} |",
        f"| Macro-only losing trade days | {samples['macro_only_losing_trade_days']} |",
        "",
        "## Residual Loss Profile",
        "",
        f"- Non-risk loss rate: `{residual['loss_rate']}`",
        f"- Average non-risk losing implementable PnL: `{residual['avg_losing_implementable_pnl']}`",
        f"- OOS loss share inside non-risk losses: `{result['non_risk_failure_mode_check']['oos_loss_share']}`",
        f"- Negative 5-minute followthrough loss share: `{result['non_risk_failure_mode_check']['negative_5m_followthrough_loss_share']}`",
        "",
        "## Macro-Only Loss Profile",
        "",
        f"- Macro-only loss rate: `{macro['loss_rate']}`",
        f"- Average macro-only losing implementable PnL: `{macro['avg_losing_implementable_pnl']}`",
        f"- Macro event type counts: `{macro['macro_event_type_counts']}`",
        "",
        "## Decision",
        "",
        f"- Decision: `{decision['decision']}`",
        f"- Revise H-A2: `{decision['revise_h_a2_rule_result']}`",
        f"- Park H-A2: `{decision['park_h_a2_rule_result']}`",
        f"- Prioritize exact replay: `{decision['prioritize_exact_replay_rule_result']}`",
        f"- Next safe action: {decision['next_safe_action']}",
        "",
        "## Guardrails",
        "",
        "- No network, paid data, broker request, IBKR request, GDELT live retry, or LLM call was used.",
        "- No paper trading, operational validation, real-money launch, or E2 claim is allowed.",
        "- This analysis is E1 diagnostic evidence only.",
    ]
    return "\n".join(lines) + "\n"


def _top_losses(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    ordered = sorted(rows, key=lambda row: float(row["existing_implementable_pnl"]))
    return [
        {
            "date": row["date"],
            "split": row["split"],
            "implementable_pnl": row["existing_implementable_pnl"],
            "mid_pnl": row["existing_mid_pnl"],
            "cost_drag": row["existing_cost_drag"],
            "prior_vix_close": row["regimes"].get("prior_vix_close"),
            "macro_event_types": row["regimes"].get("high_importance_macro_event_types", []),
            "proxy_5m_signal": row["proxy_5m"].get("signal"),
            "proxy_15m_signal": row["proxy_15m"].get("signal"),
        }
        for row in ordered[:limit]
    ]


def _split_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(row["split"] for row in rows).items()))


def _weekday_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    counts = Counter(weekdays[datetime.fromisoformat(row["date"]).weekday()] for row in rows)
    return dict(sorted(counts.items()))


def _prior_vix_state_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    def state(row: dict[str, Any]) -> str:
        regimes = row["regimes"]
        if regimes.get("prior_stress_vix"):
            return "stress_vix"
        if regimes.get("prior_high_vix"):
            return "high_vix"
        return "normal_or_low_vix"

    return dict(sorted(Counter(state(row) for row in rows).items()))


def _proxy_signal_counts(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(row[field].get("signal", "missing") for row in rows).items()))


def _is_risk(row: dict[str, Any]) -> bool:
    regimes = row["regimes"]
    return bool(regimes["high_importance_macro"] or regimes["prior_high_vix"])


def _rate(numerator: int, denominator: int) -> float | None:
    return _round(numerator / denominator) if denominator else None


def _avg(values: list[float]) -> float | None:
    return _round(mean(values)) if values else None


def _round(value: float | None) -> float | None:
    return round(float(value), 6) if value is not None else None


def _write_search_log(trials: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(trial, ensure_ascii=False, sort_keys=True) for trial in trials) + "\n", encoding="utf-8")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main() -> int:
    result = run_analysis()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
