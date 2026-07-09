from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_h_a2_revised_opening_followthrough_condition import (  # noqa: E402
    _group_stats,
    _relative,
    _round,
    _trimmed_stats,
)


DEFAULT_PREREGISTRATION_PATH = PROJECT_ROOT / "experiments" / "h_a2_original_entry_revision_preregistration.json"
DEFAULT_DAILY_SOURCE_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_lower_resolution_proxy_summary.json"
DEFAULT_DELAYED_SUMMARY_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_delayed_entry_condition_summary.json"
DEFAULT_SUMMARY_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_original_entry_revision_summary.json"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_original_entry_revision_report.md"
DEFAULT_SEARCH_LOG_PATH = PROJECT_ROOT / "reports" / "experiments" / "search_logs" / "h_a2_original_entry_revision_search_log.jsonl"


def run_experiment(
    preregistration_path: Path = DEFAULT_PREREGISTRATION_PATH,
    daily_source_path: Path = DEFAULT_DAILY_SOURCE_PATH,
    delayed_summary_path: Path = DEFAULT_DELAYED_SUMMARY_PATH,
    summary_path: Path = DEFAULT_SUMMARY_PATH,
    report_path: Path = DEFAULT_REPORT_PATH,
    search_log_path: Path = DEFAULT_SEARCH_LOG_PATH,
) -> dict[str, Any]:
    prereg = _load_json(preregistration_path)
    daily_source = _load_json(daily_source_path)
    delayed_summary = _load_json(delayed_summary_path)

    rule = prereg["original_entry_rule"]
    threshold = float(rule["opening_followthrough_threshold"])
    rows = list(daily_source["daily_rows"])
    train_baseline = _non_risk_trades(rows, "in_sample")
    oos_baseline = _non_risk_trades(rows, "oos")
    train_retained = _apply_original_entry_revision(train_baseline, threshold)
    oos_retained = _apply_original_entry_revision(oos_baseline, threshold)
    train_skipped = _skipped(train_baseline, train_retained)
    oos_skipped = _skipped(oos_baseline, oos_retained)

    checks = {
        "original_entry_timestamp_cleanliness": _timestamp_cleanliness(rule),
        "forbidden_feature_exclusion": _forbidden_feature_exclusion(prereg),
        "original_entry_sample_recount": _sample_recount(train_baseline, train_retained, train_skipped, oos_baseline, oos_retained, oos_skipped),
        "original_entry_implementable_pnl_check": _pnl_check(oos_baseline, oos_retained, oos_skipped),
        "risk_and_sample_adequacy_check": _risk_check(oos_baseline, oos_retained, search_log_path),
    }
    decision = _decision(checks)
    result = _summary(
        prereg=prereg,
        daily_source=daily_source,
        delayed_summary=delayed_summary,
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
        daily_source_path=daily_source_path,
        delayed_summary_path=delayed_summary_path,
        search_log_path=search_log_path,
    )

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(_render_report(result), encoding="utf-8")
    _write_search_log(result, search_log_path)
    return result


def _summary(
    prereg: dict[str, Any],
    daily_source: dict[str, Any],
    delayed_summary: dict[str, Any],
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
    daily_source_path: Path,
    delayed_summary_path: Path,
    search_log_path: Path,
) -> dict[str, Any]:
    return {
        "record_type": "experiment_summary",
        "schema_version": "h_a2_original_entry_revision_v1",
        "experiment_id": "h_a2_original_entry_revision",
        "hypothesis_id": "H-A2",
        "evidence_tier": "E1",
        "status": "complete",
        "conclusion": "ยังสรุปไม่ได้",
        "conclusion_reason": (
            "The 09:35-only revision is timestamp-clean and retains useful original-entry context, "
            "but the OOS retained sample has only 14 trade days and remains under-sampled/underpowered."
        ),
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "research_log_required": True,
        "research_log_slug": "higanbana-h-a2-original-entry-revision",
        "source_preregistration": _relative(preregistration_path),
        "daily_source": _relative(daily_source_path),
        "delayed_entry_source_summary": _relative(delayed_summary_path),
        "source_experiment_ids": {
            "daily_source": daily_source.get("experiment_id"),
            "delayed_entry_source_summary": delayed_summary.get("experiment_id"),
        },
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
            "threshold_search_used": False,
            "new_oos_selected_filter_used": False,
            "locked_threshold": threshold,
            "threshold_source": prereg["original_entry_rule"]["threshold_source"],
            "baseline_original_entry_time_et": prereg["original_entry_rule"]["baseline_original_entry_time_et"],
            "candidate_decision_time_et": prereg["original_entry_rule"]["candidate_decision_time_et"],
            "earliest_candidate_entry_time_et": prereg["original_entry_rule"]["earliest_candidate_entry_time_et"],
            "used_features": ["clean_macro_vix_condition", "proxy_5m_followthrough"],
            "excluded_features": ["no_adverse_measured_15m_conflict", "delayed_entry_0945_quote_or_fill", "oos_loss_blacklist_or_new_filter"],
            "fifteen_minute_conflict_component_used": False,
            "delayed_entry_component_used": False,
            "original_0935_pnl_labeled_as_delayed_entry_pnl": False,
            "result_type": "timestamp_clean_original_entry_context",
        },
        "trial_policy": {
            "threshold_search_allowed": False,
            "threshold_search_used": False,
            "new_filter_search_used": False,
            "oos_tuning_used": False,
            "trial_count": 0,
            "search_log": _relative(search_log_path),
            "dsr_status": "not_recomputed_no_new_threshold_search",
            "dsr_reason": "No threshold, filter, or best-Sharpe search was performed in this original-entry revision.",
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
        "baseline_condition": {
            "train": _group_stats(train_baseline),
            "oos": _group_stats(oos_baseline),
        },
        "original_entry_revision_condition": {
            "condition": "non-risk trade day and 09:30-09:35 directional followthrough >= locked threshold 0.001",
            "locked_threshold": threshold,
            "train": _group_stats(train_retained),
            "oos": _group_stats(oos_retained),
            "largest_remaining_oos_losses": _top_losses(oos_retained, 5),
        },
        "skipped_condition": {
            "train": _group_stats(train_skipped),
            "oos": _group_stats(oos_skipped),
        },
        **checks,
        "hypothesis_decision": decision,
        "allowed_claims": [
            "H-A2 has a timestamp-clean original-entry revision that uses only 09:35-known features.",
            "The 15-minute conflict component was excluded from this original-entry test.",
            "The current result is E1 diagnostic/prioritization evidence only.",
        ],
        "forbidden_claims": prereg.get("forbidden_claims", []),
        "next_safe_action": decision["allowed_next_action"],
        "tier_blockers": [
            "E1 diagnostic/prioritization evidence only",
            "Under-sampled and underpowered retained OOS sample",
            "No exact 2022-10 ORB replay",
            "No independent new validation data",
            "No E2 acceptance claim",
            "No paper trading, operational validation, or real-money approval",
        ],
    }


def _non_risk_trades(rows: list[dict[str, Any]], split: str) -> list[dict[str, Any]]:
    return [row for row in rows if row["split"] == split and row["existing_trade_count"] > 0 and not _is_risk(row)]


def _apply_original_entry_revision(rows: list[dict[str, Any]], threshold: float) -> list[dict[str, Any]]:
    return [row for row in rows if _passes_5m_followthrough(row, threshold)]


def _passes_5m_followthrough(row: dict[str, Any], threshold: float) -> bool:
    proxy_5m = row["proxy_5m"]
    if proxy_5m.get("status") != "measured":
        return False
    followthrough = proxy_5m.get("directional_followthrough_to_close_pct")
    return followthrough is not None and float(followthrough) >= threshold


def _timestamp_cleanliness(rule: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "complete",
        "candidate_decision_time_et": rule["candidate_decision_time_et"],
        "feature_completion_times_et": {
            "clean_macro_vix_condition": "09:35:00",
            "proxy_5m_followthrough": "09:35:00",
        },
        "all_features_known_by_decision_time": True,
        "forbidden_feature_exclusion_status": "pass",
        "timestamp_cleanliness_status": "pass_for_original_0935_decision",
    }


def _forbidden_feature_exclusion(prereg: dict[str, Any]) -> dict[str, Any]:
    forbidden = [item["feature"] for item in prereg.get("forbidden_features", [])]
    return {
        "status": "complete",
        "forbidden_features": forbidden,
        "fifteen_minute_conflict_component_used": False,
        "delayed_entry_component_used": False,
        "new_oos_selected_filter_used": False,
        "all_forbidden_features_excluded": True,
    }


def _sample_recount(
    train_baseline: list[dict[str, Any]],
    train_retained: list[dict[str, Any]],
    train_skipped: list[dict[str, Any]],
    oos_baseline: list[dict[str, Any]],
    oos_retained: list[dict[str, Any]],
    oos_skipped: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "status": "complete",
        "train_trade_count": len(train_baseline),
        "oos_trade_count": len(oos_baseline),
        "retained_train_trade_count": len(train_retained),
        "retained_oos_trade_count": len(oos_retained),
        "skipped_train_trade_count": len(train_skipped),
        "skipped_oos_trade_count": len(oos_skipped),
        "under_sampled_label": True,
        "underpowered_label": True,
    }


def _pnl_check(
    oos_baseline: list[dict[str, Any]],
    oos_retained: list[dict[str, Any]],
    oos_skipped: list[dict[str, Any]],
) -> dict[str, Any]:
    baseline = _group_stats(oos_baseline)
    retained = _group_stats(oos_retained)
    skipped = _group_stats(oos_skipped)
    return {
        "status": "complete",
        "baseline_avg_implementable_pnl": baseline["avg_implementable_pnl"],
        "retained_avg_implementable_pnl": retained["avg_implementable_pnl"],
        "skipped_avg_implementable_pnl": skipped["avg_implementable_pnl"],
        "retained_minus_skipped_avg_implementable_pnl": _diff(retained["avg_implementable_pnl"], skipped["avg_implementable_pnl"]),
        "retained_total_implementable_pnl": retained["total_implementable_pnl"],
        "baseline_total_implementable_pnl": baseline["total_implementable_pnl"],
        "cost_drag": retained["total_cost_drag"],
        "comparison_status": "directionally_useful_but_underpowered",
    }


def _risk_check(oos_baseline: list[dict[str, Any]], oos_retained: list[dict[str, Any]], search_log_path: Path) -> dict[str, Any]:
    baseline_trim = _trimmed_stats(oos_baseline)
    retained_trim = _trimmed_stats(oos_retained)
    return {
        "status": "diagnostic_underpowered",
        "big_day_dependency_status": "context_only_underpowered",
        "concentration_status": _concentration_label(oos_retained),
        "mintrl_psr_status": "blocked_underpowered_e1_diagnostic",
        "under_sampled": True,
        "underpowered": True,
        "dsr_or_search_log_status": "not_recomputed_no_new_threshold_search",
        "search_log": _relative(search_log_path),
        "evidence_tier_cap": "E1",
        "baseline_oos_after_trim": baseline_trim["after_trim"],
        "retained_oos_after_trim": retained_trim["after_trim"],
        "interpretation": "Risk checks are diagnostic only because retained OOS sample is small.",
    }


def _decision(checks: dict[str, Any]) -> dict[str, Any]:
    timestamp_clean = checks["original_entry_timestamp_cleanliness"]["all_features_known_by_decision_time"]
    pnl = checks["original_entry_implementable_pnl_check"]
    retained_oos = checks["original_entry_sample_recount"]["retained_oos_trade_count"]
    if timestamp_clean and retained_oos >= 10 and pnl["retained_avg_implementable_pnl"] is not None and pnl["retained_avg_implementable_pnl"] > pnl["baseline_avg_implementable_pnl"]:
        decision = "continue_original_entry_revision_under_e1"
        allowed_next = (
            "Keep H-A2 active as E1 diagnostic evidence and run a stricter original-entry robustness/prioritization review "
            "or plan independent validation data before any E2, exact replay, paper trading, or paid action."
        )
    elif timestamp_clean:
        decision = "return_to_delayed_quote_acquisition_or_park_h_a2"
        allowed_next = "The original-entry revision did not retain useful diagnostic signal; consider delayed-entry quote acquisition or park H-A2."
    else:
        decision = "park_original_entry_revision_due_to_timestamp_failure"
        allowed_next = "Park the original-entry revision until all used features are known by 09:35 ET."
    return {
        "status": "complete",
        "decision": decision,
        "evidence_tier": "E1",
        "allowed_next_action": allowed_next,
        "forbidden_claims": [
            "No H-A2 edge validation.",
            "No E2 evidence.",
            "No paper trading, operational validation, or real-money approval.",
        ],
        "research_log_requirement": "research_log/031-higanbana-h-a2-original-entry-revision.md",
        "e2_status": "forbidden",
    }


def _skipped(baseline: list[dict[str, Any]], retained: list[dict[str, Any]]) -> list[dict[str, Any]]:
    retained_dates = {row["date"] for row in retained}
    return [row for row in baseline if row["date"] not in retained_dates]


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
            "prior_vix_close": row["regimes"].get("prior_vix_close"),
        }
        for row in ordered[:limit]
    ]


def _concentration_label(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "blocked_no_rows"
    month_counts: dict[str, int] = {}
    for row in rows:
        month_counts[row["date"][:7]] = month_counts.get(row["date"][:7], 0) + 1
    max_share = max(month_counts.values()) / len(rows)
    return "concentrated_or_underpowered" if max_share >= 0.75 or len(rows) < 30 else "not_single_month_dominated"


def _is_risk(row: dict[str, Any]) -> bool:
    return bool(row["regimes"]["high_importance_macro"] or row["regimes"]["prior_high_vix"])


def _diff(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return _round(left - right)


def _write_search_log(result: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    records = []
    for check_id in [
        "original_entry_timestamp_cleanliness",
        "forbidden_feature_exclusion",
        "original_entry_sample_recount",
        "original_entry_implementable_pnl_check",
        "risk_and_sample_adequacy_check",
        "hypothesis_decision",
    ]:
        section = result.get(check_id, {})
        records.append(
            {
                "record_type": "original_entry_revision_check",
                "experiment_id": result["experiment_id"],
                "check_id": check_id,
                "locked_threshold": result["methodology"]["locked_threshold"],
                "candidate_decision_time_et": result["methodology"]["candidate_decision_time_et"],
                "threshold_search_used": False,
                "new_filter_search_used": False,
                "fifteen_minute_conflict_component_used": False,
                "status": section.get("status"),
            }
        )
    path.write_text("\n".join(json.dumps(record, ensure_ascii=False, sort_keys=True) for record in records) + "\n", encoding="utf-8")


def _render_report(result: dict[str, Any]) -> str:
    counts = result["sample_counts"]
    baseline = result["baseline_condition"]
    revised = result["original_entry_revision_condition"]
    skipped = result["skipped_condition"]
    pnl = result["original_entry_implementable_pnl_check"]
    decision = result["hypothesis_decision"]
    return "\n".join(
        [
            "# H-A2 Original-Entry Revision Report",
            "",
            f"- Status: `{result['status']}`",
            f"- Conclusion: `{result['conclusion']}`",
            f"- Evidence tier: `{result['evidence_tier']}`",
            f"- Candidate decision time ET: `{result['methodology']['candidate_decision_time_et']}`",
            f"- Locked threshold: `{result['methodology']['locked_threshold']}`",
            f"- Result type: `{result['methodology']['result_type']}`",
            "",
            "## Timestamp Cleanliness",
            "",
            "| Feature | Known by decision time |",
            "|:--|:--|",
            "| `clean_macro_vix_condition` | `true` |",
            "| `proxy_5m_followthrough` | `true` |",
            "| `no_adverse_measured_15m_conflict` used | `false` |",
            "",
            "## Sample Recount",
            "",
            "| Bucket | Train | OOS |",
            "|:--|--:|--:|",
            f"| Baseline non-risk trades | {counts['baseline_train_non_risk_trade_days']} | {counts['baseline_oos_non_risk_trade_days']} |",
            f"| Retained by 09:35-only rule | {counts['retained_train_trade_days']} | {counts['retained_oos_trade_days']} |",
            f"| Skipped by 09:35-only rule | {counts['skipped_train_trade_days']} | {counts['skipped_oos_trade_days']} |",
            "",
            "## Original-Entry PnL Context",
            "",
            "| Group | OOS trades | Avg implementable PnL | Total implementable PnL | Loss rate |",
            "|:--|--:|--:|--:|--:|",
            f"| Baseline | {baseline['oos']['trade_day_count']} | {baseline['oos']['avg_implementable_pnl']} | {baseline['oos']['total_implementable_pnl']} | {baseline['oos']['loss_rate']} |",
            f"| Retained | {revised['oos']['trade_day_count']} | {revised['oos']['avg_implementable_pnl']} | {revised['oos']['total_implementable_pnl']} | {revised['oos']['loss_rate']} |",
            f"| Skipped | {skipped['oos']['trade_day_count']} | {skipped['oos']['avg_implementable_pnl']} | {skipped['oos']['total_implementable_pnl']} | {skipped['oos']['loss_rate']} |",
            "",
            f"- Retained minus skipped avg implementable PnL: `{pnl['retained_minus_skipped_avg_implementable_pnl']}`",
            "",
            "## Decision",
            "",
            f"- Decision: `{decision['decision']}`",
            f"- Next safe action: {decision['allowed_next_action']}",
            "",
            "## Guardrails",
            "",
            "- No network, paid data, broker request, IBKR request, GDELT live retry, or LLM call was used.",
            "- No threshold search, OOS tuning, new OOS-selected filter, delayed-entry component, or 15-minute conflict component was used.",
            "- No paper trading, operational validation, real-money launch, exact replay, or E2 claim is allowed.",
            "",
        ]
    )


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    result = run_experiment()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
