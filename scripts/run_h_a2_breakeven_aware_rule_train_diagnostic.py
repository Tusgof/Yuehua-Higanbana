from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PREREG_PATH = PROJECT_ROOT / "experiments" / "h_a2_breakeven_aware_rule_preregistration.json"
DAILY_SOURCE_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_lower_resolution_proxy_summary.json"
MECHANISM_AUDIT_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_mechanism_revision_audit.json"
SUMMARY_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_breakeven_aware_rule_train_diagnostic.json"
REPORT_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_breakeven_aware_rule_train_diagnostic.md"
SEARCH_LOG_PATH = (
    PROJECT_ROOT
    / "reports"
    / "diagnostics"
    / "search_logs"
    / "h_a2_breakeven_aware_rule_train_diagnostic_search_log.jsonl"
)

FOLLOWTHROUGH_THRESHOLDS = [0.0, 0.001, 0.002, 0.003, 0.005]


def run_h_a2_breakeven_aware_rule_train_diagnostic() -> dict[str, Any]:
    prereg = _load_json(PREREG_PATH)
    daily_source = _load_json(DAILY_SOURCE_PATH)
    mechanism_audit = _load_json(MECHANISM_AUDIT_PATH)

    rows = list(daily_source["daily_rows"])
    train_non_risk = _train_non_risk_trade_rows(rows)
    trials = _candidate_rule_trials(train_non_risk)
    feature_audit = _decision_time_feature_audit(train_non_risk, mechanism_audit)
    target = _cost_adjusted_strike_reachability_target(mechanism_audit, train_non_risk)
    exact_sanity = _exact_replay_sanity_check(mechanism_audit)
    decision = _decision(feature_audit, target, trials, exact_sanity)

    summary: dict[str, Any] = {
        "record_type": "experiment_summary",
        "schema_version": "h_a2_breakeven_aware_rule_train_diagnostic_v1",
        "experiment_id": "h_a2_breakeven_aware_rule_train_diagnostic",
        "hypothesis_id": "H-A2",
        "status": "complete",
        "evidence_tier": "E1",
        "conclusion": "ยังสรุปไม่ได้",
        "conclusion_reason": (
            "Train-only surrogate trials can describe directional followthrough behavior, but the local train rows do not contain "
            "the per-candidate entry strike mapping, implementable debit, bid/ask width, and liquidity fields needed to lock a true "
            "breakeven-aware option rule."
        ),
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "research_log_required": True,
        "research_log_slug": "higanbana-h-a2-breakeven-aware-train-diagnostic",
        "source_preregistration": _relative(PREREG_PATH),
        "source_artifacts": [
            _relative(PREREG_PATH),
            _relative(DAILY_SOURCE_PATH),
            _relative(MECHANISM_AUDIT_PATH),
        ],
        "source_experiment_ids": {
            "daily_source": daily_source.get("experiment_id"),
            "mechanism_audit": mechanism_audit.get("experiment_id"),
            "preregistration": prereg.get("experiment_id"),
        },
        "guardrails": {
            "network_used": False,
            "paid_data_used": False,
            "new_provider_used": False,
            "broker_request_used": False,
            "ibkr_request_used": False,
            "gdelt_live_retry_used": False,
            "llm_call_used": False,
            "exact_replay_expansion_used": False,
            "oos_filter_selection_used": False,
            "oos_tuning_used": False,
            "paper_trading_allowed": False,
            "operational_validation_allowed": False,
            "real_money_allowed": False,
            "strategy_use_allowed": False,
        },
        "methodology": {
            "mode": "local_no_paid_train_only_diagnostic",
            "local_artifacts_only": True,
            "chronological_split_required": True,
            "train_split_used_for_trials": "in_sample",
            "oos_rows_used_for_rule_selection": False,
            "random_split_used": False,
            "candidate_rule_trials_are_surrogates": True,
            "true_breakeven_rule_locked": False,
            "decision_time_inputs_tested_from_local_train_rows": [
                "clean_macro_vix_condition",
                "proxy_5m_directional_followthrough",
                "prior_vix_bucket_context",
            ],
            "future_inputs_excluded": [
                "future_underlying_close_as_live_input",
                "forced_close_option_quote_as_live_input",
                "same_day_realized_pnl_as_live_input",
                "oos_selected_filter",
            ],
        },
        "sample_counts": {
            "daily_rows": len(rows),
            "train_non_risk_trade_days": len(train_non_risk),
            "train_candidate_trial_count": len(trials),
            "exact_replay_sanity_candidate_count": exact_sanity["candidate_count"],
        },
        "decision_time_feature_audit": feature_audit,
        "cost_adjusted_strike_reachability_target": target,
        "train_only_candidate_rule_trials": trials,
        "exact_replay_mechanism_sanity_check": exact_sanity,
        "selection_risk_control": {
            "trial_count": len(trials),
            "all_trials_recorded": True,
            "search_log": _relative(SEARCH_LOG_PATH),
            "best_trial_selected_for_trading": False,
            "dsr_status": "blocked_no_acceptance_selection",
            "dsr_reason": "The diagnostic records train-only surrogate trials but does not select a deployable best-Sharpe or best-PnL rule.",
            "mintrl_psr_status": "blocked_underpowered_e1_diagnostic",
            "big_day_dependency_status": "not_claimed_no_acceptance_backtest",
        },
        "decision": decision,
        "tier_blockers": [
            "E1 train-only diagnostic only",
            "True breakeven-aware rule cannot be locked from current local train rows",
            "Per-candidate entry strike mapping is missing for the train distribution",
            "Per-candidate entry implementable debit and bid/ask/liquidity are missing for the train distribution",
            "Only two exact replay sanity candidates exist",
            "No OOS evaluation of a locked revised rule",
            "No MinTRL/PSR acceptance evidence",
            "No E2 acceptance claim",
        ],
        "allowed_claims": [
            "H-A2.62 defines the cost-adjusted strike-reachability target and checks whether current local train artifacts can support it.",
            "The current local train artifacts are insufficient to lock a true breakeven-aware option rule.",
            "A targeted data/regime expansion plan is justified before more broad data buying or OOS rule evaluation.",
        ],
        "forbidden_claims": [
            "Do not claim H-A2 edge is validated.",
            "Do not claim the breakeven-aware rule is selected for trading.",
            "Do not claim E2 acceptance-grade evidence.",
            "Do not approve paper trading, operational validation, or real-money trading.",
            "Do not use OOS tuning or an OOS-selected filter.",
            "Do not approve broad calendar data buying from this diagnostic alone.",
        ],
        "next_safe_action": decision["next_safe_action"],
    }

    _write_outputs(summary)
    return summary


def _train_non_risk_trade_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if row.get("split") == "in_sample"
        and int(row.get("existing_trade_count", 0)) > 0
        and not _is_risk(row)
    ]


def _candidate_rule_trials(train_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    trials: list[dict[str, Any]] = []
    baseline = _group_stats(train_rows)
    trials.append(
        {
            "trial_id": "train_baseline_non_risk",
            "rule": "non-risk train trade days only",
            "uses_true_breakeven_inputs": False,
            "surrogate_only": True,
            "threshold": None,
            "retained_train_trade_days": len(train_rows),
            "stats": baseline,
            "selected_for_trading": False,
            "selection_reason": "Baseline context only.",
        }
    )
    for threshold in FOLLOWTHROUGH_THRESHOLDS:
        kept = [row for row in train_rows if _passes_followthrough(row, threshold)]
        stats = _group_stats(kept)
        trials.append(
            {
                "trial_id": f"train_followthrough_ge_{threshold:g}",
                "rule": f"non-risk train trade days with proxy_5m directional followthrough >= {threshold:g}",
                "uses_true_breakeven_inputs": False,
                "surrogate_only": True,
                "threshold": threshold,
                "retained_train_trade_days": len(kept),
                "stats": stats,
                "selected_for_trading": False,
                "selection_reason": (
                    "Recorded as a train-only surrogate trial. It cannot be selected as a breakeven-aware rule "
                    "because strike/debit/liquidity inputs are missing for the train distribution."
                ),
            }
        )
    return trials


def _decision_time_feature_audit(
    train_rows: list[dict[str, Any]],
    mechanism_audit: dict[str, Any],
) -> dict[str, Any]:
    available = [
        {
            "field": "clean_macro_vix_condition",
            "scope": "train_daily_rows",
            "decision_time_status": "available_before_entry",
        },
        {
            "field": "proxy_5m_directional_followthrough",
            "scope": "train_daily_rows",
            "decision_time_status": "available_by_09_35_in_existing_proxy_design",
        },
        {
            "field": "existing_train_implementable_pnl",
            "scope": "train_daily_rows",
            "decision_time_status": "outcome_only_not_live_input",
        },
        {
            "field": "exact_replay_entry_strike_debit_liquidity",
            "scope": "two_exact_replay_sanity_cases_only",
            "decision_time_status": "available_for_autopsy_not_train_distribution",
        },
    ]
    missing = [
        "train_distribution_nearest_discrete_long_strike",
        "train_distribution_short_strike_width",
        "train_distribution_entry_mid_debit",
        "train_distribution_entry_implementable_debit",
        "train_distribution_entry_bid_ask_width",
        "train_distribution_entry_quote_size_or_liquidity",
        "train_distribution_cost_adjusted_strike_reachability_target",
    ]
    return {
        "status": "blocked_true_breakeven_rule_lock",
        "train_trade_days_checked": len(train_rows),
        "exact_replay_autopsy_count": len(mechanism_audit.get("mechanism_autopsy", [])),
        "available_fields": available,
        "missing_fields_for_true_rule": missing,
        "can_lock_true_breakeven_aware_rule_from_current_artifacts": False,
        "can_run_surrogate_train_trials": True,
        "interpretation": (
            "The current train artifact can test directional surrogate behavior, but it cannot compute the actual option payoff "
            "geometry needed for a breakeven-aware rule across the train distribution."
        ),
    }


def _cost_adjusted_strike_reachability_target(
    mechanism_audit: dict[str, Any],
    train_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    exact_cases = []
    for item in mechanism_audit.get("mechanism_autopsy", []):
        entry = float(item["underlying_entry_close"])
        close = float(item["underlying_forced_close"])
        long_strike = float(item["long_strike"])
        required_move_to_long = round(long_strike - entry, 2)
        realized_move = round(close - entry, 2)
        shortfall = round(long_strike - close, 2)
        exact_cases.append(
            {
                "candidate_date": item["candidate_date"],
                "direction": item["direction"],
                "entry_underlying": entry,
                "forced_close_underlying": close,
                "long_strike": long_strike,
                "required_move_to_long_strike": required_move_to_long,
                "realized_move_to_forced_close": realized_move,
                "strike_reachability_shortfall": shortfall,
                "entry_implementable_debit": item["entry_implementable_debit"],
                "implementable_pnl": item["implementable_pnl"],
                "target_reached": shortfall <= 0 and item["implementable_pnl"] > 0,
            }
        )
    return {
        "status": "defined_but_not_computable_for_train_distribution",
        "target_definition": (
            "For a call debit vertical, the post-entry underlying move must be large enough that the selected long strike is "
            "reached or nearly reached and the forced-close spread value can overcome entry implementable debit, bid/ask friction, "
            "and $0.64 per-leg fees. Implementable PnL, not mid PnL, governs the target."
        ),
        "train_distribution_target_available": False,
        "train_trade_days_with_surrogate_outcome": len(train_rows),
        "exact_replay_target_cases": exact_cases,
        "exact_replay_target_reached_count": sum(1 for item in exact_cases if item["target_reached"]),
    }


def _exact_replay_sanity_check(mechanism_audit: dict[str, Any]) -> dict[str, Any]:
    aggregate = mechanism_audit.get("aggregate_findings", {})
    return {
        "status": "pass_mechanism_problem_confirmed",
        "candidate_count": aggregate.get("candidate_count"),
        "directionally_correct_underlying_count": aggregate.get("directionally_correct_underlying_count"),
        "long_strike_not_reached_count": aggregate.get("long_strike_not_reached_count"),
        "option_pnl_negative_count": aggregate.get("option_pnl_negative_count"),
        "total_mid_pnl": aggregate.get("total_mid_pnl"),
        "total_implementable_pnl": aggregate.get("total_implementable_pnl"),
        "total_cost_drag_vs_mid": aggregate.get("total_cost_drag_vs_mid"),
        "interpretation": (
            "The exact replay autopsy confirms the revised target is necessary: direction was right, but payoff feasibility failed."
        ),
    }


def _decision(
    feature_audit: dict[str, Any],
    target: dict[str, Any],
    trials: list[dict[str, Any]],
    exact_sanity: dict[str, Any],
) -> dict[str, Any]:
    if not feature_audit["can_lock_true_breakeven_aware_rule_from_current_artifacts"]:
        decision = "write_targeted_data_regime_expansion_plan"
        next_safe_action = (
            "Pre-register H-A2.63 targeted data/regime expansion plan for breakeven-aware ORB evidence. The plan must name the "
            "minimum option-chain fields and windows needed to compute entry strike mapping, entry implementable debit, bid/ask "
            "width, liquidity, forced-close value, regime labels, and MinTRL/PSR coverage before any paid download or OOS rule "
            "evaluation."
        )
    else:
        decision = "preregister_oos_evaluation_of_one_locked_rule"
        next_safe_action = "Pre-register OOS evaluation of one train-locked breakeven-aware H-A2 rule."
    return {
        "status": "complete",
        "decision": decision,
        "evidence_tier_cap": "E1",
        "true_breakeven_rule_locked": False,
        "candidate_trial_count": len(trials),
        "exact_sanity_status": exact_sanity["status"],
        "target_status": target["status"],
        "oos_tuning_used": False,
        "paid_data_approved": False,
        "paper_trading_allowed": False,
        "next_safe_action": next_safe_action,
    }


def _passes_followthrough(row: dict[str, Any], threshold: float) -> bool:
    proxy_5m = row.get("proxy_5m", {})
    if proxy_5m.get("status") != "measured":
        return False
    value = proxy_5m.get("directional_followthrough_to_close_pct")
    return value is not None and float(value) >= threshold


def _group_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [float(row["existing_implementable_pnl"]) for row in rows]
    mid_values = [float(row["existing_mid_pnl"]) for row in rows]
    losses = [value for value in values if value < 0]
    return {
        "trade_day_count": len(rows),
        "loss_count": len(losses),
        "loss_rate": _round(len(losses) / len(values)) if values else None,
        "win_rate": _round(sum(1 for value in values if value > 0) / len(values)) if values else None,
        "total_implementable_pnl": _round(sum(values)),
        "avg_implementable_pnl": _round(mean(values)) if values else None,
        "total_mid_pnl": _round(sum(mid_values)),
        "total_cost_drag": _round(sum(mid_values) - sum(values)),
        "worst_day_pnl": min(values) if values else None,
        "best_day_pnl": max(values) if values else None,
    }


def _is_risk(row: dict[str, Any]) -> bool:
    regimes = row.get("regimes", {})
    return bool(regimes.get("high_importance_macro") or regimes.get("prior_high_vix"))


def _write_outputs(summary: dict[str, Any]) -> None:
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SEARCH_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(_render_report(summary), encoding="utf-8")
    SEARCH_LOG_PATH.write_text(
        "\n".join(json.dumps(trial, ensure_ascii=False, sort_keys=True) for trial in summary["train_only_candidate_rule_trials"])
        + "\n",
        encoding="utf-8",
    )


def _render_report(summary: dict[str, Any]) -> str:
    feature = summary["decision_time_feature_audit"]
    target = summary["cost_adjusted_strike_reachability_target"]
    decision = summary["decision"]
    lines = [
        "# H-A2 Breakeven-Aware Rule Train Diagnostic",
        "",
        f"- Status: `{summary['status']}`",
        f"- Evidence tier: `{summary['evidence_tier']}`",
        f"- Conclusion: `{summary['conclusion']}`",
        f"- Decision: `{decision['decision']}`",
        "",
        "## Main Finding",
        "",
        summary["conclusion_reason"],
        "",
        "## Feature Audit",
        "",
        f"- Train trade days checked: `{feature['train_trade_days_checked']}`",
        f"- Can lock true breakeven-aware rule: `{feature['can_lock_true_breakeven_aware_rule_from_current_artifacts']}`",
        "- Missing fields:",
    ]
    lines.extend(f"  - `{field}`" for field in feature["missing_fields_for_true_rule"])
    lines.extend(
        [
            "",
            "## Strike-Reachability Target",
            "",
            target["target_definition"],
            "",
            "| Date | Entry | Close | Long strike | Required move | Realized move | Shortfall | Implementable PnL |",
            "|:--|--:|--:|--:|--:|--:|--:|--:|",
        ]
    )
    for item in target["exact_replay_target_cases"]:
        lines.append(
            "| {date} | {entry:.2f} | {close:.2f} | {strike:.2f} | {required:.2f} | {realized:.2f} | {shortfall:.2f} | {pnl:.2f} |".format(
                date=item["candidate_date"],
                entry=item["entry_underlying"],
                close=item["forced_close_underlying"],
                strike=item["long_strike"],
                required=item["required_move_to_long_strike"],
                realized=item["realized_move_to_forced_close"],
                shortfall=item["strike_reachability_shortfall"],
                pnl=item["implementable_pnl"],
            )
        )
    lines.extend(
        [
            "",
            "## Train-Only Surrogate Trials",
            "",
            "| Trial | Retained train days | Avg implementable PnL | Loss rate | Selected for trading |",
            "|:--|--:|--:|--:|:--:|",
        ]
    )
    for trial in summary["train_only_candidate_rule_trials"]:
        stats = trial["stats"]
        lines.append(
            f"| `{trial['trial_id']}` | {trial['retained_train_trade_days']} | {stats['avg_implementable_pnl']} | {stats['loss_rate']} | {trial['selected_for_trading']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Next safe action: {decision['next_safe_action']}",
            "- This diagnostic does not approve paid data by itself. The next artifact must specify the data fields, windows, regimes, and cost gate.",
            "",
            "## Guardrails",
            "",
            "- No network, paid data, new provider, broker request, IBKR request, GDELT retry, or LLM call was used.",
            "- No OOS tuning, OOS-selected filter, exact replay expansion, E2 claim, paper trading, operational validation, or real-money trading is allowed.",
            "",
        ]
    )
    return "\n".join(lines)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def _round(value: float | None) -> float | None:
    return round(float(value), 6) if value is not None else None


def main() -> int:
    summary = run_h_a2_breakeven_aware_rule_train_diagnostic()
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
