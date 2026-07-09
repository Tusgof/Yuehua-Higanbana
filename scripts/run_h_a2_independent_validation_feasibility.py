from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PREREG_PATH = PROJECT_ROOT / "experiments" / "h_a2_independent_validation_feasibility_preregistration.json"
H_A2_34_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_original_entry_robustness_prioritization_summary.json"
STRATEGY_READINESS_PATH = PROJECT_ROOT / "reports" / "strategy_data_readiness_audit.json"
PAID_COST_PATH = PROJECT_ROOT / "reports" / "data_cost" / "paid_cost_audit.json"
MACRO_COVERAGE_PATH = PROJECT_ROOT / "reports" / "macro_calendar_coverage_audit.json"
VIX_COVERAGE_PATH = PROJECT_ROOT / "reports" / "vix_vxv_coverage_audit.json"
Q4_DRYRUN_PATH = PROJECT_ROOT / "reports" / "data_cost" / "databento_cost_oos_2024_q4_completion_intraday_exit_30m_dryrun.json"

SUMMARY_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_independent_validation_feasibility.json"
REPORT_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_independent_validation_feasibility.md"
SEARCH_LOG_PATH = (
    PROJECT_ROOT / "reports" / "diagnostics" / "search_logs" / "h_a2_independent_validation_feasibility_search_log.jsonl"
)


def run_h_a2_independent_validation_feasibility() -> dict[str, Any]:
    prereg = _load_json(PREREG_PATH)
    h_a2_34 = _load_json(H_A2_34_PATH)
    strategy = _load_json(STRATEGY_READINESS_PATH)
    paid_cost = _load_json(PAID_COST_PATH)
    macro = _load_json(MACRO_COVERAGE_PATH)
    vix = _load_json(VIX_COVERAGE_PATH)
    q4_dryrun = _load_json(Q4_DRYRUN_PATH) if Q4_DRYRUN_PATH.exists() else None

    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    retained_oos = h_a2_34["sample_counts"]["retained_oos_trade_days"]
    closed_trades = strategy["totals"]["closed_trades"]
    candidate_days = strategy["totals"]["candidate_days"]
    oos_closed_trades = strategy["totals"]["splits"]["oos"]["closed_trades"]
    missing_regime_buckets = h_a2_34["regime_and_calendar_concentration"]["empty_critical_buckets"]
    cost_remaining = paid_cost.get("remaining_before_stop_usd")
    q4_request_count = len(q4_dryrun.get("requests", [])) if q4_dryrun else 0
    q4_review_cost = q4_dryrun.get("decision", {}).get("review_cost_usd") if q4_dryrun else None

    current_gap_inventory = {
        "status": "complete",
        "retained_oos_trade_days": retained_oos,
        "current_total_closed_trades": closed_trades,
        "current_oos_closed_trades": oos_closed_trades,
        "current_candidate_days": candidate_days,
        "missing_regime_buckets": missing_regime_buckets,
        "sample_adequacy": strategy.get("sample_adequacy", {}),
        "mintrl_psr_status": {
            "mintrl_status": strategy.get("sample_adequacy", {}).get("mintrl_status"),
            "psr_status": strategy.get("sample_adequacy", {}).get("psr_status"),
            "power_status": strategy.get("sample_adequacy", {}).get("power_status"),
        },
        "claim_upgrade_blockers": [
            "retained_oos_trade_days_below_independent_validation_need",
            "high_vix_retained_bucket_missing",
            "mintrl_psr_not_computed_for_acceptance",
            "independent_validation_data_not_defined_yet",
        ],
    }

    validation_target = {
        "status": "complete",
        "validation_period_candidates": [
            {
                "period": "future_or_unseen_oos_after_current_2024_12_31",
                "role": "preferred_independent_validation",
                "reason": "Separates validation from the current H-A2.32/H-A2.34 OOS evidence already inspected.",
            },
            {
                "period": "reference_pre_break_2019_01_01_to_2022_05_10",
                "role": "structural-break context only unless exact option data is available",
                "reason": "Useful for regime context, but 0DTE structure and data availability may differ before the post-2022 regime.",
            },
            {
                "period": "targeted_high_vix_windows_not_used_in_threshold_selection",
                "role": "missing-regime validation",
                "reason": "H-A2.34 has no retained high-VIX bucket, so any validation plan must explicitly cover high-VIX or state a scoped hypothesis.",
            },
        ],
        "required_trade_count_or_mintrl_method": (
            "Compute MinTRL from the future validation return distribution; until then retain under-sampled/underpowered labels."
        ),
        "required_regime_buckets": ["vix_below_15", "vix_15_to_25", "vix_above_25", "scheduled_macro", "non_macro"],
        "high_vix_requirement": "Validation plan must either include retained high-VIX trade opportunities or explicitly scope H-A2 away from high-VIX conditions before testing.",
        "chronological_embargo_rule": "Do not use current OOS diagnostics to tune new filters; future validation must be chronologically later or separately justified and pre-registered.",
    }

    no_paid_source_inventory = {
        "status": "complete",
        "local_source_inventory": [
            {
                "source": "reports/strategy_data_readiness_audit.json",
                "usable_for": "current trade count and split inventory",
                "adds_independent_trade_days": False,
            },
            {
                "source": "reports/macro_calendar_coverage_audit.json",
                "usable_for": "macro-event regime labels through 2026",
                "adds_independent_trade_days": False,
            },
            {
                "source": "reports/vix_vxv_coverage_audit.json",
                "usable_for": "volatility-regime labels through 2026-06-29",
                "adds_independent_trade_days": False,
            },
            {
                "source": "reports/data_cost/databento_cost_oos_2024_q4_completion_intraday_exit_30m_dryrun.json",
                "usable_for": "already-written request map for later cost planning",
                "adds_independent_trade_days": False,
            },
        ],
        "free_source_inventory": [
            {
                "source": "Cboe VIX/VIX3M history and official macro calendar",
                "usable_for": "regime labels only",
                "adds_option_trade_pnl": False,
            },
            {
                "source": "IBKR historical bars",
                "usable_for": "possible SPY underlying bars only after local TWS/Gateway is available",
                "adds_option_trade_pnl": False,
                "status": "externally_blocked_local_api_unavailable",
            },
        ],
        "usable_no_paid_dates": [],
        "unusable_no_paid_dates": [
            "No currently identified no-paid source adds independent SPY 0DTE option quote/fill PnL days.",
            "Existing local sources can support regime planning and gap inventory but not new independent implementable PnL.",
        ],
        "no_paid_feasibility_status": "no_paid_can_plan_but_cannot_validate_edge",
    }

    paid_data_decision_tree = {
        "status": "complete",
        "named_hypothesis_gap": "H-A2 retained original-entry signal lacks independent validation sample and high-VIX retained coverage.",
        "minimum_required_fields": [
            "SPY 0DTE option bid/ask around 09:35 ET",
            "SPY 0DTE option bid/ask at exit or defined intraday exit checks",
            "SPY underlying bars sufficient for 09:35 signal reconstruction",
            "VIX/VIX3M and macro-event labels for every candidate day",
        ],
        "candidate_provider_scope": {
            "preferred_scope": "SPY only, narrow validation windows, month-by-month or regime-targeted batches",
            "avoid": "broad calendar buying without MinTRL/regime rationale",
            "existing_dryrun_request_count": q4_request_count,
            "existing_dryrun_review_cost_usd": q4_review_cost,
        },
        "cost_guard_preconditions": {
            "current_remaining_before_stop_usd": cost_remaining,
            "live_cost_estimate_allowed_by_this_run": False,
            "paid_download_allowed_by_this_run": False,
            "requires_new_preregistration_before_cost_or_download": True,
        },
        "purchase_forbidden_until": [
            "A separate paid-cost estimate plan names exact periods, fields, and regime gaps.",
            "The active cost guard has enough headroom or the user tops up by real payment on the existing Databento account.",
            "A live estimate passes the project cost guard before any download.",
        ],
    }

    if no_paid_source_inventory["usable_no_paid_dates"]:
        decision = "run_no_paid_validation_scan"
        allowed_next_action = "Pre-register and run a no-paid validation scan over identified local/free dates."
    elif cost_remaining is not None and cost_remaining < 5.0:
        decision = "pause_paid_path_run_no_paid_gap_report_or_wait_for_topup"
        allowed_next_action = (
            "Run a no-paid validation gap report or wait for real top-up before any live estimate or paid acquisition plan."
        )
    else:
        decision = "draft_paid_cost_estimate_plan_only"
        allowed_next_action = (
            "Draft a separate paid-cost estimate plan for narrow independent validation windows; do not call a provider yet."
        )

    next_action_selection = {
        "status": "complete",
        "decision": decision,
        "allowed_next_action": allowed_next_action,
        "forbidden_next_actions": [
            "No paid data download.",
            "No live Databento estimate from this run.",
            "No IBKR historical request.",
            "No exact replay.",
            "No LLM call.",
            "No GDELT retry.",
            "No paper trading.",
            "No E2 claim.",
        ],
        "evidence_tier_cap": "E1",
        "research_log_requirement": "research_log/033-higanbana-h-a2-independent-validation-feasibility.md",
    }

    summary = {
        "schema_version": "h_a2_independent_validation_feasibility_v1",
        "record_type": "experiment_summary",
        "experiment_id": "h_a2_independent_validation_feasibility",
        "hypothesis_id": "H-A2",
        "status": "complete",
        "evidence_tier": "E1",
        "conclusion": "ยังสรุปไม่ได้",
        "conclusion_reason": (
            "No-paid sources can define the validation gap and regime requirements, but they cannot add independent "
            "implementable SPY 0DTE PnL days. H-A2 remains active but validation requires a separate no-paid gap report "
            "or a future paid-cost estimate plan after cost-guard review."
        ),
        "generated_at_utc": generated_at,
        "source_preregistration": _relative(PREREG_PATH),
        "source_summary": _relative(H_A2_34_PATH),
        "methodology": {
            "candidate_decision_time_et": "09:35:00",
            "locked_threshold": 0.001,
            "used_features": ["clean_macro_vix_condition", "proxy_5m_followthrough"],
            "local_artifacts_only": True,
            "chronological_split_required": True,
            "random_split_used": False,
            "oos_tuning_used": False,
            "threshold_search_used": False,
            "new_oos_selected_filter_used": False,
            "fifteen_minute_conflict_component_used": False,
            "delayed_entry_component_used": False,
        },
        "current_gap_inventory": current_gap_inventory,
        "validation_target_definition": validation_target,
        "no_paid_source_inventory": no_paid_source_inventory,
        "paid_data_decision_tree": paid_data_decision_tree,
        "next_action_selection": next_action_selection,
        "coverage_context": {
            "macro_calendar_status": macro.get("status"),
            "vix_vxv_status": vix.get("status"),
            "strategy_data_status": strategy.get("status"),
            "paid_cost_status": paid_cost.get("status"),
        },
        "trial_policy": {
            "trial_count": 0,
            "threshold_search_used": False,
            "new_filter_search_used": False,
            "oos_tuning_used": False,
            "dsr_status": "not_recomputed_no_parameter_search",
            "search_log": _relative(SEARCH_LOG_PATH),
        },
        "allowed_claims": [
            "H-A2 independent validation requirements are now defined as E1 diagnostic evidence.",
            "No-paid sources can support gap planning but cannot validate the edge without new implementable PnL days.",
        ],
        "forbidden_claims": [
            "Do not claim H-A2 edge is validated.",
            "Do not claim E2 acceptance-grade evidence.",
            "Do not approve paper trading.",
            "Do not approve operational validation.",
            "Do not approve real-money trading.",
            "Do not run exact replay from this diagnostic.",
            "Do not buy paid data from this diagnostic.",
            "Do not call live Databento estimates from this diagnostic.",
            "Do not request IBKR bars from this diagnostic.",
            "Do not call LLMs from this diagnostic.",
            "Do not retry GDELT from this diagnostic.",
            "Do not change threshold 0.001.",
            "Do not add a new OOS-selected filter.",
        ],
        "network_used": False,
        "paid_data_used": False,
        "live_cost_estimate_used": False,
        "new_provider_used": False,
        "broker_request_used": False,
        "ibkr_request_used": False,
        "gdelt_live_retry_used": False,
        "llm_call_used": False,
        "exact_replay_used": False,
        "paper_trading_allowed": False,
        "operational_validation_allowed": False,
        "real_money_allowed": False,
        "strategy_use_allowed": False,
        "research_log_required": True,
        "research_log_slug": "higanbana-h-a2-independent-validation-feasibility",
        "next_safe_action": allowed_next_action,
        "tier_blockers": [
            "E1 diagnostic feasibility evidence only",
            "No independent validation PnL days added",
            "No high-VIX retained validation coverage yet",
            "MinTRL/PSR acceptance path remains unproven",
            "No paid data or live cost estimate used",
            "No exact replay",
            "No E2 acceptance claim",
        ],
    }

    _write_json(SUMMARY_PATH, summary)
    REPORT_PATH.write_text(_render_report(summary), encoding="utf-8")
    _write_search_log(generated_at)
    return summary


def _render_report(summary: dict[str, Any]) -> str:
    gap = summary["current_gap_inventory"]
    no_paid = summary["no_paid_source_inventory"]
    paid = summary["paid_data_decision_tree"]
    decision = summary["next_action_selection"]
    lines = [
        "# H-A2 Independent Validation Feasibility",
        "",
        f"- **Status**: `{summary['status']}`",
        f"- **Conclusion**: `{summary['conclusion']}`",
        f"- **Evidence tier**: `{summary['evidence_tier']}`",
        f"- **Retained OOS trade days**: `{gap['retained_oos_trade_days']}`",
        f"- **Total closed trades**: `{gap['current_total_closed_trades']}`",
        f"- **Missing regime buckets**: `{', '.join(gap['missing_regime_buckets'])}`",
        f"- **No-paid feasibility**: `{no_paid['no_paid_feasibility_status']}`",
        f"- **Cost headroom**: `${paid['cost_guard_preconditions']['current_remaining_before_stop_usd']}`",
        f"- **Decision**: `{decision['decision']}`",
        "",
        "## Conclusion",
        summary["conclusion_reason"],
        "",
        "## Next Safe Action",
        decision["allowed_next_action"],
        "",
        "## Forbidden",
        "- No paid data, live Databento estimate, IBKR request, exact replay, LLM call, GDELT retry, paper trading, or E2 claim is approved by this run.",
    ]
    return "\n".join(lines) + "\n"


def _write_search_log(generated_at: str) -> None:
    SEARCH_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "generated_at_utc": generated_at,
        "experiment_id": "h_a2_independent_validation_feasibility",
        "trial_count": 0,
        "parameter_search_used": False,
        "oos_tuning_used": False,
        "note": "Feasibility diagnostic only; no parameter or threshold search.",
    }
    SEARCH_LOG_PATH.write_text(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main() -> int:
    summary = run_h_a2_independent_validation_feasibility()
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
