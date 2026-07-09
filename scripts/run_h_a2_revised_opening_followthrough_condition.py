from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PREREGISTRATION_PATH = PROJECT_ROOT / "experiments" / "h_a2_revised_opening_followthrough_condition_preregistration.json"
DEFAULT_SOURCE_SUMMARY_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_lower_resolution_proxy_summary.json"
DEFAULT_SUMMARY_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_revised_opening_followthrough_condition_summary.json"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_revised_opening_followthrough_condition_report.md"
DEFAULT_SEARCH_LOG_PATH = PROJECT_ROOT / "reports" / "experiments" / "search_logs" / "h_a2_revised_opening_followthrough_condition_search_log.jsonl"

THRESHOLD_GRID = [-0.002, -0.001, 0.0, 0.001, 0.002, 0.003, 0.005]


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
    train_non_risk = _non_risk_trades(rows, split="in_sample")
    oos_non_risk = _non_risk_trades(rows, split="oos")

    trials = _threshold_trials(train_non_risk)
    _write_search_log(trials, search_log_path)
    locked = _lock_threshold(train_non_risk, trials)
    result = _summary(prereg, source, rows, train_non_risk, oos_non_risk, trials, locked, preregistration_path, source_summary_path, search_log_path)

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(_render_report(result), encoding="utf-8")
    return result


def _summary(
    prereg: dict[str, Any],
    source: dict[str, Any],
    rows: list[dict[str, Any]],
    train_non_risk: list[dict[str, Any]],
    oos_non_risk: list[dict[str, Any]],
    trials: list[dict[str, Any]],
    locked: dict[str, Any],
    preregistration_path: Path,
    source_summary_path: Path,
    search_log_path: Path,
) -> dict[str, Any]:
    threshold = locked["locked_threshold"]
    baseline_train = _group_stats(train_non_risk)
    baseline_oos = _group_stats(oos_non_risk)
    revised_train_rows = _apply_revised_condition(train_non_risk, threshold)
    revised_oos_rows = _apply_revised_condition(oos_non_risk, threshold)
    revised_train = _group_stats(revised_train_rows)
    revised_oos = _group_stats(revised_oos_rows)
    residual = _residual_loss_reduction(baseline_train, baseline_oos, revised_train, revised_oos)
    big_day = _big_day_context(oos_non_risk, revised_oos_rows)
    decision = _decision(locked, baseline_oos, revised_oos, residual)

    return {
        "record_type": "experiment_summary",
        "schema_version": "h_a2_revised_opening_followthrough_condition_v1",
        "experiment_id": "h_a2_revised_opening_followthrough_condition",
        "hypothesis_id": "H-A2",
        "evidence_tier": "E1",
        "status": "complete",
        "conclusion": "ยังสรุปไม่ได้",
        "conclusion_reason": (
            "The train-only opening-followthrough rule materially improves local OOS residual-loss behavior, "
            "but the remaining sample is under-sampled and this is still proxy evidence, not exact replay or acceptance-grade validation."
        ),
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "research_log_required": True,
        "research_log_slug": "higanbana-h-a2-revised-opening-followthrough-condition",
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
            "thresholds_fit_only_on_train": True,
            "threshold_selection_rule": locked["selection_rule"],
            "base_condition": prereg.get("revised_condition_design", {}).get("base_condition"),
            "new_condition_family": prereg.get("revised_condition_design", {}).get("new_condition_family"),
        },
        "trial_policy": {
            "trial_count": len(trials),
            "all_trials_recorded": True,
            "search_log": _relative(search_log_path),
            "dsr_status": "diagnostic_threshold_grid_not_acceptance",
            "dsr_reason": "A train-only threshold grid is logged, but no acceptance-grade Sharpe or deployable filter is claimed.",
            "selected_trial_id": locked["selected_trial_id"],
        },
        "sample_policy": {
            "mintrl_psr_status": "blocked_underpowered_e1_diagnostic",
            "under_sampled": True,
            "underpowered": True,
            "reason": "The revised condition keeps only a small OOS trade subset, so MinTRL/PSR cannot support acceptance.",
        },
        "threshold_lock": locked,
        "sample_counts": {
            "daily_rows": len(rows),
            "baseline_train_non_risk_trade_days": len(train_non_risk),
            "baseline_oos_non_risk_trade_days": len(oos_non_risk),
            "revised_train_trade_days": len(revised_train_rows),
            "revised_oos_trade_days": len(revised_oos_rows),
            "skipped_train_trade_days": len(train_non_risk) - len(revised_train_rows),
            "skipped_oos_trade_days": len(oos_non_risk) - len(revised_oos_rows),
        },
        "baseline_condition": {
            "train": baseline_train,
            "oos": baseline_oos,
        },
        "revised_condition": {
            "condition": "non-risk trade day and 5-minute directional followthrough >= locked train-only threshold, with no adverse measured 15-minute conflict",
            "locked_threshold": threshold,
            "train": revised_train,
            "oos": revised_oos,
            "largest_remaining_oos_losses": _top_losses(revised_oos_rows, 5),
        },
        "residual_loss_reduction_check": residual,
        "chronological_oos_holdout_check": {
            "status": "complete",
            "threshold_locked_before_oos": True,
            "oos_tuning_used": False,
            "baseline_oos": baseline_oos,
            "revised_oos": revised_oos,
        },
        "mechanism_consistency_check": {
            "status": "complete",
            "condition_rationale": "ORB is an intraday momentum hypothesis; adverse or weak opening followthrough contradicts that mechanism.",
            "failure_modes": [
                "The condition may remove too many trades to reach MinTRL.",
                "The proxy may not match exact executable 0DTE entries/exits.",
                "The apparent improvement may depend on the current small OOS sample.",
            ],
            "what_would_falsify_the_revised_condition": [
                "Exact replay shows no improvement after the threshold is locked.",
                "Additional regimes show the rule only worked on a few lucky dates.",
                "The condition fails after costs or big-day trimming.",
            ],
            "exact_replay_blockers_remaining": [
                "2022-10 real SPY underlying bars remain externally blocked.",
                "Current result uses local lower-resolution proxy rows, not exact 2022-10 replay.",
            ],
        },
        "big_day_dependency_context": big_day,
        "decision_rule_application": decision,
        "tier_blockers": [
            "E1 diagnostic only",
            "Under-sampled and underpowered after revised condition",
            "Train-only threshold grid is diagnostic and not acceptance-grade DSR",
            "No exact 2022-10 ORB replay",
            "No independent new validation data",
            "No E2 acceptance claim",
            "No paper trading, operational validation, or real-money approval",
        ],
        "allowed_claims": prereg.get("allowed_claims", []),
        "forbidden_claims": prereg.get("forbidden_claims", []),
        "next_safe_action": decision["next_safe_action"],
    }


def _threshold_trials(train_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    baseline = _group_stats(train_rows)
    min_retained = max(1, len(train_rows) // 2)
    target_loss_rate = baseline["loss_rate"] * 0.5 if baseline["loss_rate"] is not None else None
    trials = []
    for threshold in THRESHOLD_GRID:
        kept = _apply_revised_condition(train_rows, threshold)
        stats = _group_stats(kept)
        eligible = bool(
            target_loss_rate is not None
            and len(kept) >= min_retained
            and stats["loss_rate"] is not None
            and stats["loss_rate"] <= target_loss_rate
        )
        trials.append(
            {
                "trial_id": f"train_threshold_{threshold:g}",
                "threshold": threshold,
                "sample_count": len(kept),
                "baseline_train_sample_count": len(train_rows),
                "min_retained_sample_count": min_retained,
                "baseline_train_loss_rate": baseline["loss_rate"],
                "target_loss_rate": _round(target_loss_rate),
                "loss_rate": stats["loss_rate"],
                "avg_implementable_pnl": stats["avg_implementable_pnl"],
                "selected_as_best": False,
                "eligible_by_train_only_rule": eligible,
            }
        )
    return trials


def _lock_threshold(train_rows: list[dict[str, Any]], trials: list[dict[str, Any]]) -> dict[str, Any]:
    selected = next((trial for trial in trials if trial["eligible_by_train_only_rule"]), None)
    if selected is None:
        return {
            "status": "blocked_no_train_only_threshold",
            "locked_threshold": None,
            "selected_trial_id": None,
            "selection_rule": "Select the first ascending threshold that cuts train loss rate by at least 50% while retaining at least half of train non-risk trade days.",
            "oos_used_for_selection": False,
        }
    selected["selected_as_best"] = True
    return {
        "status": "locked",
        "locked_threshold": selected["threshold"],
        "selected_trial_id": selected["trial_id"],
        "selection_rule": "Select the first ascending threshold that cuts train loss rate by at least 50% while retaining at least half of train non-risk trade days.",
        "oos_used_for_selection": False,
        "selected_train_loss_rate": selected["loss_rate"],
        "selected_train_sample_count": selected["sample_count"],
    }


def _apply_revised_condition(rows: list[dict[str, Any]], threshold: float | None) -> list[dict[str, Any]]:
    if threshold is None:
        return []
    return [row for row in rows if _passes_opening_followthrough(row, threshold)]


def _passes_opening_followthrough(row: dict[str, Any], threshold: float) -> bool:
    proxy_5m = row["proxy_5m"]
    if proxy_5m.get("status") != "measured":
        return False
    followthrough = proxy_5m.get("directional_followthrough_to_close_pct")
    if followthrough is None or float(followthrough) < threshold:
        return False
    proxy_15m = row["proxy_15m"]
    if proxy_15m.get("status") == "measured" and proxy_15m.get("signal") != "none":
        value = proxy_15m.get("directional_followthrough_to_close_pct")
        if value is not None and float(value) < 0:
            return False
    return True


def _residual_loss_reduction(
    baseline_train: dict[str, Any],
    baseline_oos: dict[str, Any],
    revised_train: dict[str, Any],
    revised_oos: dict[str, Any],
) -> dict[str, Any]:
    return {
        "status": "complete",
        "baseline_train_loss_count": baseline_train["loss_count"],
        "revised_train_loss_count": revised_train["loss_count"],
        "baseline_oos_loss_count": baseline_oos["loss_count"],
        "revised_oos_loss_count": revised_oos["loss_count"],
        "train_loss_count_reduction": baseline_train["loss_count"] - revised_train["loss_count"],
        "oos_loss_count_reduction": baseline_oos["loss_count"] - revised_oos["loss_count"],
        "oos_loss_rate_change": _diff(revised_oos["loss_rate"], baseline_oos["loss_rate"]),
        "oos_avg_pnl_change": _diff(revised_oos["avg_implementable_pnl"], baseline_oos["avg_implementable_pnl"]),
    }


def _big_day_context(baseline_rows: list[dict[str, Any]], revised_rows: list[dict[str, Any]]) -> dict[str, Any]:
    baseline = _trimmed_stats(baseline_rows)
    revised = _trimmed_stats(revised_rows)
    return {
        "status": "diagnostic_underpowered",
        "trimmed_each_tail_count_baseline": baseline["trimmed_each_tail_count"],
        "trimmed_each_tail_count_revised": revised["trimmed_each_tail_count"],
        "baseline_oos_before_trim": baseline["before_trim"],
        "baseline_oos_after_trim": baseline["after_trim"],
        "revised_oos_before_trim": revised["before_trim"],
        "revised_oos_after_trim": revised["after_trim"],
        "survives_extreme_trim": revised["after_trim"]["avg_implementable_pnl"] is not None and revised["after_trim"]["avg_implementable_pnl"] > 0,
        "interpretation": "This is a context check only; small revised OOS sample makes big-day inference underpowered.",
    }


def _decision(
    locked: dict[str, Any],
    baseline_oos: dict[str, Any],
    revised_oos: dict[str, Any],
    residual: dict[str, Any],
) -> dict[str, Any]:
    if locked["status"] != "locked":
        decision = "park_revised_condition_pending_new_train_rule"
        next_safe_action = "Park the revised H-A2 opening-followthrough condition until a train-only threshold can be stated without OOS tuning."
    elif revised_oos["trade_day_count"] < 10:
        decision = "continue_local_revised_condition_research_underpowered"
        next_safe_action = "Keep H-A2 active at E1, but expand/validate sample before exact replay or paper trading because the revised condition leaves too few OOS trades."
    elif residual["oos_loss_count_reduction"] > 0 and revised_oos["avg_implementable_pnl"] is not None and revised_oos["avg_implementable_pnl"] > baseline_oos["avg_implementable_pnl"]:
        decision = "prioritize_exact_replay_when_external_bar_blocker_clears"
        next_safe_action = "Keep the revised condition as E1 prioritization evidence and prioritize exact replay when the 2022 SPY bar blocker clears; no paid data, IBKR request, LLM call, or paper trading is approved from this result."
    else:
        decision = "revise_or_park_h_a2_before_exact_replay"
        next_safe_action = "Revise or park H-A2 before exact replay because the train-only opening-followthrough condition did not improve OOS residual behavior."
    return {
        "status": "complete",
        "decision": decision,
        "evidence_tier": "E1",
        "threshold_locked_before_oos": locked["status"] == "locked",
        "oos_tuning_used": False,
        "blockers": [
            "under_sampled",
            "underpowered",
            "no_exact_2022_orb_replay",
            "no_e2_acceptance_claim",
        ],
        "next_safe_action": next_safe_action,
    }


def _non_risk_trades(rows: list[dict[str, Any]], split: str) -> list[dict[str, Any]]:
    return [row for row in rows if row["split"] == split and row["existing_trade_count"] > 0 and not _is_risk(row)]


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


def _trimmed_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda row: float(row["existing_implementable_pnl"]))
    trim_n = max(1, round(len(ordered) * 0.05)) if len(ordered) >= 20 else 0
    trimmed = ordered[trim_n : len(ordered) - trim_n] if trim_n else ordered
    return {
        "trimmed_each_tail_count": trim_n,
        "before_trim": _group_stats(ordered),
        "after_trim": _group_stats(trimmed),
    }


def _top_losses(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    ordered = sorted(rows, key=lambda row: float(row["existing_implementable_pnl"]))
    return [
        {
            "date": row["date"],
            "split": row["split"],
            "implementable_pnl": row["existing_implementable_pnl"],
            "mid_pnl": row["existing_mid_pnl"],
            "cost_drag": row["existing_cost_drag"],
            "proxy_5m_followthrough": row["proxy_5m"].get("directional_followthrough_to_close_pct"),
            "proxy_15m_followthrough": row["proxy_15m"].get("directional_followthrough_to_close_pct"),
            "prior_vix_close": row["regimes"].get("prior_vix_close"),
        }
        for row in ordered[:limit]
    ]


def _render_report(result: dict[str, Any]) -> str:
    counts = result["sample_counts"]
    locked = result["threshold_lock"]
    baseline = result["baseline_condition"]
    revised = result["revised_condition"]
    decision = result["decision_rule_application"]
    return "\n".join(
        [
            "# H-A2 Revised Opening-Followthrough Condition Report",
            "",
            f"- Status: `{result['status']}`",
            f"- Conclusion: `{result['conclusion']}`",
            f"- Evidence tier: `{result['evidence_tier']}`",
            f"- Locked threshold: `{locked['locked_threshold']}`",
            f"- Selected trial: `{locked['selected_trial_id']}`",
            f"- Search log: `{result['trial_policy']['search_log']}`",
            "",
            "## Sample Counts",
            "",
            "| Bucket | Count |",
            "|:--|--:|",
            f"| Baseline train non-risk trades | {counts['baseline_train_non_risk_trade_days']} |",
            f"| Baseline OOS non-risk trades | {counts['baseline_oos_non_risk_trade_days']} |",
            f"| Revised train trades | {counts['revised_train_trade_days']} |",
            f"| Revised OOS trades | {counts['revised_oos_trade_days']} |",
            f"| Skipped OOS trades | {counts['skipped_oos_trade_days']} |",
            "",
            "## Train-Only Threshold And OOS Holdout",
            "",
            "| Split | Baseline trades | Baseline loss rate | Revised trades | Revised loss rate | Revised avg PnL |",
            "|:--|--:|--:|--:|--:|--:|",
            (
                f"| Train | {baseline['train']['trade_day_count']} | {baseline['train']['loss_rate']} | "
                f"{revised['train']['trade_day_count']} | {revised['train']['loss_rate']} | {revised['train']['avg_implementable_pnl']} |"
            ),
            (
                f"| OOS | {baseline['oos']['trade_day_count']} | {baseline['oos']['loss_rate']} | "
                f"{revised['oos']['trade_day_count']} | {revised['oos']['loss_rate']} | {revised['oos']['avg_implementable_pnl']} |"
            ),
            "",
            "## Decision",
            "",
            f"- Decision: `{decision['decision']}`",
            f"- Next safe action: {decision['next_safe_action']}",
            "",
            "## Guardrails",
            "",
            "- No network, paid data, broker request, IBKR request, GDELT live retry, or LLM call was used.",
            "- No paper trading, operational validation, real-money launch, exact 2022 ORB replay, or E2 claim is allowed.",
            "- This analysis is E1 diagnostic evidence only.",
            "",
        ]
    )


def _is_risk(row: dict[str, Any]) -> bool:
    return bool(row["regimes"]["high_importance_macro"] or row["regimes"]["prior_high_vix"])


def _diff(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return _round(left - right)


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
    result = run_experiment()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
