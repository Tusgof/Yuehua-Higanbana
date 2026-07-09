from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_h_a2_original_entry_revision import (  # noqa: E402
    _apply_original_entry_revision,
    _is_risk,
    _non_risk_trades,
    _relative,
    _round,
    _skipped,
)
from scripts.run_h_a2_revised_opening_followthrough_condition import _group_stats  # noqa: E402


DEFAULT_PREREGISTRATION_PATH = (
    PROJECT_ROOT
    / "experiments"
    / "h_a2_original_entry_robustness_prioritization_preregistration.json"
)
DEFAULT_SOURCE_SUMMARY_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_original_entry_revision_summary.json"
DEFAULT_DAILY_SOURCE_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_lower_resolution_proxy_summary.json"
DEFAULT_SUMMARY_PATH = (
    PROJECT_ROOT / "reports" / "experiments" / "h_a2_original_entry_robustness_prioritization_summary.json"
)
DEFAULT_REPORT_PATH = (
    PROJECT_ROOT / "reports" / "experiments" / "h_a2_original_entry_robustness_prioritization_report.md"
)
DEFAULT_SEARCH_LOG_PATH = (
    PROJECT_ROOT
    / "reports"
    / "experiments"
    / "search_logs"
    / "h_a2_original_entry_robustness_prioritization_search_log.jsonl"
)


def run_experiment(
    preregistration_path: Path = DEFAULT_PREREGISTRATION_PATH,
    source_summary_path: Path = DEFAULT_SOURCE_SUMMARY_PATH,
    daily_source_path: Path = DEFAULT_DAILY_SOURCE_PATH,
    summary_path: Path = DEFAULT_SUMMARY_PATH,
    report_path: Path = DEFAULT_REPORT_PATH,
    search_log_path: Path = DEFAULT_SEARCH_LOG_PATH,
) -> dict[str, Any]:
    prereg = _load_json(preregistration_path)
    source_summary = _load_json(source_summary_path)
    daily_source = _load_json(daily_source_path)

    threshold = float(prereg["locked_rule_under_review"]["opening_followthrough_threshold"])
    rows = list(daily_source["daily_rows"])
    train_baseline = _non_risk_trades(rows, "in_sample")
    oos_baseline = _non_risk_trades(rows, "oos")
    train_retained = _apply_original_entry_revision(train_baseline, threshold)
    oos_retained = _apply_original_entry_revision(oos_baseline, threshold)
    train_skipped = _skipped(train_baseline, train_retained)
    oos_skipped = _skipped(oos_baseline, oos_retained)

    checks = {
        "source_rule_integrity": _source_rule_integrity(prereg, source_summary),
        "leave_one_and_big_day_dependency": _leave_one_and_big_day(oos_retained, oos_skipped),
        "regime_and_calendar_concentration": _regime_and_calendar_concentration(oos_retained),
        "skip_cost_tradeoff": _skip_cost_tradeoff(oos_baseline, oos_retained, oos_skipped),
    }
    decision = _decision(checks, oos_retained)
    result = _summary(
        prereg=prereg,
        source_summary=source_summary,
        daily_source=daily_source,
        threshold=threshold,
        train_baseline=train_baseline,
        train_retained=train_retained,
        train_skipped=train_skipped,
        oos_baseline=oos_baseline,
        oos_retained=oos_retained,
        oos_skipped=oos_skipped,
        checks=checks,
        decision=decision,
        preregistration_path=preregistration_path,
        source_summary_path=source_summary_path,
        daily_source_path=daily_source_path,
        search_log_path=search_log_path,
    )

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(_render_report(result), encoding="utf-8")
    _write_search_log(result, search_log_path)
    return result


def _summary(
    prereg: dict[str, Any],
    source_summary: dict[str, Any],
    daily_source: dict[str, Any],
    threshold: float,
    train_baseline: list[dict[str, Any]],
    train_retained: list[dict[str, Any]],
    train_skipped: list[dict[str, Any]],
    oos_baseline: list[dict[str, Any]],
    oos_retained: list[dict[str, Any]],
    oos_skipped: list[dict[str, Any]],
    checks: dict[str, Any],
    decision: dict[str, Any],
    preregistration_path: Path,
    source_summary_path: Path,
    daily_source_path: Path,
    search_log_path: Path,
) -> dict[str, Any]:
    return {
        "record_type": "experiment_summary",
        "schema_version": "h_a2_original_entry_robustness_prioritization_v1",
        "experiment_id": "h_a2_original_entry_robustness_prioritization",
        "hypothesis_id": "H-A2",
        "evidence_tier": "E1",
        "status": "complete",
        "conclusion": "ยังสรุปไม่ได้",
        "conclusion_reason": (
            "The H-A2.32 09:35-only rule remains directionally useful after local robustness checks, "
            "but retained OOS still has only 14 trade days and cannot support an E2 or paper-trading claim."
        ),
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "research_log_required": True,
        "research_log_slug": "higanbana-h-a2-original-entry-robustness-prioritization",
        "source_preregistration": _relative(preregistration_path),
        "source_summary": _relative(source_summary_path),
        "daily_source": _relative(daily_source_path),
        "source_experiment_ids": {
            "source_summary": source_summary.get("experiment_id"),
            "daily_source": daily_source.get("experiment_id"),
        },
        "network_used": False,
        "paid_data_used": False,
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
        "methodology": {
            "local_artifacts_only": True,
            "chronological_split_required": True,
            "random_split_used": False,
            "oos_tuning_used": False,
            "threshold_search_used": False,
            "new_oos_selected_filter_used": False,
            "locked_threshold": threshold,
            "candidate_decision_time_et": "09:35:00",
            "used_features": ["clean_macro_vix_condition", "proxy_5m_followthrough"],
            "fifteen_minute_conflict_component_used": False,
            "delayed_entry_component_used": False,
            "result_type": "original_entry_robustness_prioritization",
        },
        "sample_counts": {
            "daily_rows": len(daily_source.get("daily_rows", [])),
            "baseline_train_non_risk_trade_days": len(train_baseline),
            "retained_train_trade_days": len(train_retained),
            "skipped_train_trade_days": len(train_skipped),
            "baseline_oos_non_risk_trade_days": len(oos_baseline),
            "retained_oos_trade_days": len(oos_retained),
            "skipped_oos_trade_days": len(oos_skipped),
            "oos_retention_rate": _round(len(oos_retained) / len(oos_baseline)) if oos_baseline else None,
        },
        "baseline_condition": {"train": _group_stats(train_baseline), "oos": _group_stats(oos_baseline)},
        "retained_condition": {"train": _group_stats(train_retained), "oos": _group_stats(oos_retained)},
        "skipped_condition": {"train": _group_stats(train_skipped), "oos": _group_stats(oos_skipped)},
        **checks,
        "validation_priority_decision": decision,
        "trial_policy": {
            "threshold_search_used": False,
            "new_filter_search_used": False,
            "oos_tuning_used": False,
            "trial_count": 0,
            "search_log": _relative(search_log_path),
            "dsr_status": "not_recomputed_no_new_parameter_search",
            "dsr_reason": "The review preserves H-A2.32 and performs robustness diagnostics only.",
        },
        "allowed_claims": [
            "H-A2.32 survived this local robustness/prioritization review as E1 diagnostic evidence.",
            "Independent validation-data planning is worth considering, but not approved as a paid action by this run.",
        ],
        "forbidden_claims": prereg.get("forbidden_claims", []),
        "next_safe_action": decision["allowed_next_action"],
        "tier_blockers": [
            "E1 diagnostic/prioritization evidence only",
            "Retained OOS sample has 14 trade days",
            "MinTRL/PSR remains blocked by insufficient sample",
            "No independent validation data yet",
            "No exact 2022-10 ORB replay",
            "No E2 acceptance claim",
            "No paper trading, operational validation, or real-money approval",
        ],
    }


def _source_rule_integrity(prereg: dict[str, Any], source_summary: dict[str, Any]) -> dict[str, Any]:
    rule = prereg["locked_rule_under_review"]
    methodology = source_summary["methodology"]
    used_features = methodology.get("used_features", [])
    forbidden_absent = not any(
        [
            methodology.get("fifteen_minute_conflict_component_used"),
            methodology.get("delayed_entry_component_used"),
            methodology.get("new_oos_selected_filter_used"),
            methodology.get("threshold_search_used"),
            methodology.get("oos_tuning_used"),
        ]
    )
    return {
        "status": "pass" if forbidden_absent else "blocked",
        "candidate_decision_time_et": rule["candidate_decision_time_et"],
        "locked_threshold": rule["opening_followthrough_threshold"],
        "used_features": used_features,
        "forbidden_feature_absence": forbidden_absent,
        "rule_integrity_status": "pass_preserved_h_a2_32_rule" if forbidden_absent else "blocked_rule_changed",
    }


def _leave_one_and_big_day(oos_retained: list[dict[str, Any]], oos_skipped: list[dict[str, Any]]) -> dict[str, Any]:
    retained_pnls = _pnls(oos_retained)
    skipped_pnls = _pnls(oos_skipped)
    leave_one_avgs = [_round((sum(retained_pnls) - pnl) / (len(retained_pnls) - 1)) for pnl in retained_pnls] if len(retained_pnls) > 1 else []
    largest_day_share = _round(max(abs(pnl) for pnl in retained_pnls) / sum(abs(pnl) for pnl in retained_pnls)) if retained_pnls else None
    retained_trimmed = _remove_extremes(retained_pnls)
    skipped_trimmed = _remove_extremes(skipped_pnls)
    retained_trimmed_avg = _round(sum(retained_trimmed) / len(retained_trimmed)) if retained_trimmed else None
    skipped_trimmed_avg = _round(sum(skipped_trimmed) / len(skipped_trimmed)) if skipped_trimmed else None
    leave_one_min = min(leave_one_avgs) if leave_one_avgs else None
    status = "pass_directional_but_underpowered" if leave_one_min is not None and leave_one_min > 0 and retained_trimmed_avg and retained_trimmed_avg > 0 else "fragile_or_underpowered"
    return {
        "status": "complete",
        "retained_oos_count": len(oos_retained),
        "largest_day_share": largest_day_share,
        "leave_one_out_min_avg_pnl": leave_one_min,
        "retained_after_extreme_day_removal_avg_pnl": retained_trimmed_avg,
        "skipped_after_extreme_day_removal_avg_pnl": skipped_trimmed_avg,
        "extreme_day_removal_status": status,
        "big_day_dependency_status": status,
    }


def _regime_and_calendar_concentration(rows: list[dict[str, Any]]) -> dict[str, Any]:
    month_counts = _bucket_counts(rows, lambda row: row["date"][:7])
    weekday_counts = _bucket_counts(rows, lambda row: str(_weekday(row["date"])))
    vix_counts = _bucket_counts(rows, _vix_bucket)
    largest_bucket_share = max(
        [_largest_share(month_counts, len(rows)), _largest_share(weekday_counts, len(rows)), _largest_share(vix_counts, len(rows))]
    )
    empty_critical = [bucket for bucket in ["vix_below_15", "vix_15_to_25", "vix_above_25"] if vix_counts.get(bucket, 0) == 0]
    status = "concentrated_underpowered" if len(rows) < 30 or largest_bucket_share >= 0.5 else "not_concentrated"
    return {
        "status": "complete",
        "regime_bucket_counts": vix_counts,
        "calendar_bucket_counts": {"months": month_counts, "weekdays": weekday_counts},
        "largest_bucket_share": _round(largest_bucket_share),
        "empty_critical_buckets": empty_critical,
        "concentration_status": status,
    }


def _skip_cost_tradeoff(
    oos_baseline: list[dict[str, Any]],
    oos_retained: list[dict[str, Any]],
    oos_skipped: list[dict[str, Any]],
) -> dict[str, Any]:
    baseline = _group_stats(oos_baseline)
    retained = _group_stats(oos_retained)
    skipped = _group_stats(oos_skipped)
    retained_minus_skipped = _diff(retained["avg_implementable_pnl"], skipped["avg_implementable_pnl"])
    status = "directionally_useful_but_sample_reducing"
    if retained["avg_implementable_pnl"] is None or baseline["avg_implementable_pnl"] is None:
        status = "blocked_missing_pnl"
    elif retained["avg_implementable_pnl"] <= baseline["avg_implementable_pnl"]:
        status = "failed_retained_not_better_than_baseline"
    return {
        "status": "complete",
        "baseline_oos_count": len(oos_baseline),
        "retained_oos_count": len(oos_retained),
        "skipped_oos_count": len(oos_skipped),
        "baseline_avg_implementable_pnl": baseline["avg_implementable_pnl"],
        "retained_avg_implementable_pnl": retained["avg_implementable_pnl"],
        "skipped_avg_implementable_pnl": skipped["avg_implementable_pnl"],
        "retained_minus_skipped_avg_pnl": retained_minus_skipped,
        "skipped_total_implementable_pnl": skipped["total_implementable_pnl"],
        "skip_cost_status": status,
    }


def _decision(checks: dict[str, Any], oos_retained: list[dict[str, Any]]) -> dict[str, Any]:
    rule_ok = checks["source_rule_integrity"]["status"] == "pass"
    big_day_ok = checks["leave_one_and_big_day_dependency"]["big_day_dependency_status"] == "pass_directional_but_underpowered"
    skip_ok = checks["skip_cost_tradeoff"]["skip_cost_status"] == "directionally_useful_but_sample_reducing"
    if rule_ok and big_day_ok and skip_ok:
        decision = "prioritize_independent_validation_plan_under_e1"
        allowed_next_action = (
            "Pre-register an independent validation-data plan or no-paid validation feasibility plan before any paid data, "
            "IBKR request, exact replay, paper trading, or E2 claim."
        )
    elif rule_ok and len(oos_retained) >= 10:
        decision = "run_another_local_diagnostic_under_e1"
        allowed_next_action = "Pre-register a narrower local diagnostic that explains the robustness failure without changing threshold 0.001."
    else:
        decision = "park_original_entry_branch_or_return_to_delayed_quote_acquisition"
        allowed_next_action = "Do not pursue the current original-entry branch without a new preregistered mechanism or delayed-entry quote plan."
    return {
        "status": "complete",
        "decision": decision,
        "allowed_next_action": allowed_next_action,
        "forbidden_claims": [
            "No H-A2 edge validation.",
            "No E2 evidence.",
            "No exact replay, paid data, IBKR request, LLM call, paper trading, operational validation, or real-money approval.",
        ],
        "sample_adequacy_labels": ["under-sampled", "underpowered"],
        "evidence_tier_cap": "E1",
    }


def _write_search_log(result: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    records = []
    for check_id in [
        "source_rule_integrity",
        "leave_one_and_big_day_dependency",
        "regime_and_calendar_concentration",
        "skip_cost_tradeoff",
        "validation_priority_decision",
    ]:
        section = result.get(check_id, {})
        records.append(
            {
                "record_type": "original_entry_robustness_prioritization_check",
                "experiment_id": result["experiment_id"],
                "check_id": check_id,
                "locked_threshold": result["methodology"]["locked_threshold"],
                "candidate_decision_time_et": result["methodology"]["candidate_decision_time_et"],
                "threshold_search_used": False,
                "new_filter_search_used": False,
                "oos_tuning_used": False,
                "status": section.get("status"),
            }
        )
    path.write_text("\n".join(json.dumps(record, ensure_ascii=False, sort_keys=True) for record in records) + "\n", encoding="utf-8")


def _render_report(result: dict[str, Any]) -> str:
    counts = result["sample_counts"]
    big_day = result["leave_one_and_big_day_dependency"]
    concentration = result["regime_and_calendar_concentration"]
    skip = result["skip_cost_tradeoff"]
    decision = result["validation_priority_decision"]
    return "\n".join(
        [
            "# H-A2 Original-Entry Robustness And Prioritization Report",
            "",
            f"- Status: `{result['status']}`",
            f"- Conclusion: `{result['conclusion']}`",
            f"- Evidence tier: `{result['evidence_tier']}`",
            f"- Decision: `{decision['decision']}`",
            "",
            "## Locked Rule",
            "",
            f"- Candidate decision time ET: `{result['methodology']['candidate_decision_time_et']}`",
            f"- Threshold: `{result['methodology']['locked_threshold']}`",
            "- Features: `clean_macro_vix_condition`, `proxy_5m_followthrough`",
            "- Forbidden components stayed unused: 15-minute conflict, delayed-entry quote/fill, new OOS-selected filter.",
            "",
            "## Sample",
            "",
            "| Group | Train | OOS |",
            "|:--|--:|--:|",
            f"| Baseline non-risk | {counts['baseline_train_non_risk_trade_days']} | {counts['baseline_oos_non_risk_trade_days']} |",
            f"| Retained | {counts['retained_train_trade_days']} | {counts['retained_oos_trade_days']} |",
            f"| Skipped | {counts['skipped_train_trade_days']} | {counts['skipped_oos_trade_days']} |",
            "",
            "## Robustness Checks",
            "",
            f"- Leave-one-out min avg PnL: `{big_day['leave_one_out_min_avg_pnl']}`",
            f"- Largest retained day share: `{big_day['largest_day_share']}`",
            f"- Big-day status: `{big_day['big_day_dependency_status']}`",
            f"- Largest calendar/regime bucket share: `{concentration['largest_bucket_share']}`",
            f"- Concentration status: `{concentration['concentration_status']}`",
            f"- Retained minus skipped avg PnL: `{skip['retained_minus_skipped_avg_pnl']}`",
            f"- Skip-cost status: `{skip['skip_cost_status']}`",
            "",
            "## Decision",
            "",
            f"- Next safe action: {decision['allowed_next_action']}",
            "- Claims stay capped at E1. This does not approve paid data, exact replay, IBKR request, LLM call, paper trading, operational validation, or real-money trading.",
            "",
        ]
    )


def _pnls(rows: list[dict[str, Any]]) -> list[float]:
    return [float(row["existing_implementable_pnl"]) for row in rows]


def _remove_extremes(values: list[float]) -> list[float]:
    if len(values) < 4:
        return values[:]
    ordered = sorted(values)
    trim_count = max(1, round(len(values) * 0.05))
    if len(values) <= trim_count * 2:
        return values[:]
    return ordered[trim_count:-trim_count]


def _bucket_counts(rows: list[dict[str, Any]], bucket_fn) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        bucket = bucket_fn(row)
        counts[bucket] = counts.get(bucket, 0) + 1
    return dict(sorted(counts.items()))


def _weekday(date_text: str) -> int:
    return datetime.fromisoformat(date_text).weekday()


def _vix_bucket(row: dict[str, Any]) -> str:
    value = row.get("regimes", {}).get("prior_vix_close")
    if value is None:
        return "vix_missing"
    value = float(value)
    if value < 15:
        return "vix_below_15"
    if value <= 25:
        return "vix_15_to_25"
    return "vix_above_25"


def _largest_share(counts: dict[str, int], total: int) -> float:
    if not counts or total <= 0:
        return 0.0
    return max(counts.values()) / total


def _diff(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return _round(left - right)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    result = run_experiment()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
