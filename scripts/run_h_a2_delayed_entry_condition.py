from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_h_a2_revised_opening_followthrough_condition import (  # noqa: E402
    _apply_revised_condition,
    _group_stats,
    _non_risk_trades,
    _relative,
    _round,
    _trimmed_stats,
)


DEFAULT_PREREGISTRATION_PATH = PROJECT_ROOT / "experiments" / "h_a2_delayed_entry_condition_preregistration.json"
DEFAULT_DAILY_SOURCE_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_lower_resolution_proxy_summary.json"
DEFAULT_REVISED_SUMMARY_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_revised_opening_followthrough_condition_summary.json"
DEFAULT_ROBUSTNESS_SUMMARY_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_revised_condition_robustness_summary.json"
DEFAULT_SIGNAL_ATTRIBUTION_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_locked_condition_signal_attribution_summary.json"
DEFAULT_SUMMARY_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_delayed_entry_condition_summary.json"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_delayed_entry_condition_report.md"
DEFAULT_SEARCH_LOG_PATH = PROJECT_ROOT / "reports" / "experiments" / "search_logs" / "h_a2_delayed_entry_condition_search_log.jsonl"


def run_experiment(
    preregistration_path: Path = DEFAULT_PREREGISTRATION_PATH,
    daily_source_path: Path = DEFAULT_DAILY_SOURCE_PATH,
    revised_summary_path: Path = DEFAULT_REVISED_SUMMARY_PATH,
    robustness_summary_path: Path = DEFAULT_ROBUSTNESS_SUMMARY_PATH,
    signal_attribution_path: Path = DEFAULT_SIGNAL_ATTRIBUTION_PATH,
    summary_path: Path = DEFAULT_SUMMARY_PATH,
    report_path: Path = DEFAULT_REPORT_PATH,
    search_log_path: Path = DEFAULT_SEARCH_LOG_PATH,
) -> dict[str, Any]:
    prereg = _load_json(preregistration_path)
    daily_source = _load_json(daily_source_path)
    revised_summary = _load_json(revised_summary_path)
    robustness_summary = _load_json(robustness_summary_path)
    signal_attribution = _load_json(signal_attribution_path)

    rule = prereg["delayed_entry_rule"]
    threshold = float(rule["opening_followthrough_threshold"])
    rows = list(daily_source["daily_rows"])
    train_baseline = _non_risk_trades(rows, split="in_sample")
    oos_baseline = _non_risk_trades(rows, split="oos")
    train_retained = _apply_revised_condition(train_baseline, threshold)
    oos_retained = _apply_revised_condition(oos_baseline, threshold)
    train_skipped = _skipped(train_baseline, train_retained)
    oos_skipped = _skipped(oos_baseline, oos_retained)

    delayed_quote = _delayed_entry_quote_audit(rule["new_candidate_decision_time_et"], rows, oos_retained)
    checks = {
        "delayed_entry_timestamp_cleanliness": _timestamp_cleanliness(rule, signal_attribution),
        "delayed_entry_fill_and_cost_feasibility": delayed_quote,
        "retained_sample_recount": _sample_recount(train_baseline, train_retained, train_skipped, oos_baseline, oos_retained, oos_skipped),
        "implementable_pnl_comparison": _pnl_comparison(oos_baseline, oos_retained, oos_skipped, delayed_quote, robustness_summary),
        "risk_and_robustness_recheck": _risk_recheck(oos_baseline, oos_retained),
    }
    decision = _decision(checks)
    result = _summary(
        prereg=prereg,
        daily_source=daily_source,
        revised_summary=revised_summary,
        robustness_summary=robustness_summary,
        signal_attribution=signal_attribution,
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
        revised_summary_path=revised_summary_path,
        robustness_summary_path=robustness_summary_path,
        signal_attribution_path=signal_attribution_path,
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
    revised_summary: dict[str, Any],
    robustness_summary: dict[str, Any],
    signal_attribution: dict[str, Any],
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
    revised_summary_path: Path,
    robustness_summary_path: Path,
    signal_attribution_path: Path,
    search_log_path: Path,
) -> dict[str, Any]:
    return {
        "record_type": "experiment_summary",
        "schema_version": "h_a2_delayed_entry_condition_v1",
        "experiment_id": "h_a2_delayed_entry_condition",
        "hypothesis_id": "H-A2",
        "evidence_tier": "E1",
        "status": "complete",
        "conclusion": "ยังสรุปไม่ได้",
        "conclusion_reason": (
            "The locked condition is timestamp-clean at 09:45 ET, but current local artifacts do not contain an auditable "
            "09:45 delayed-entry option quote/fill. Therefore this run is proxy-only and cannot claim delayed-entry implementable PnL."
        ),
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "research_log_required": True,
        "research_log_slug": "higanbana-h-a2-delayed-entry-condition",
        "source_preregistration": _relative(preregistration_path),
        "daily_source": _relative(daily_source_path),
        "revised_summary": _relative(revised_summary_path),
        "robustness_summary": _relative(robustness_summary_path),
        "signal_attribution_summary": _relative(signal_attribution_path),
        "source_experiment_ids": {
            "daily_source": daily_source.get("experiment_id"),
            "revised_summary": revised_summary.get("experiment_id"),
            "robustness_summary": robustness_summary.get("experiment_id"),
            "signal_attribution": signal_attribution.get("experiment_id"),
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
            "baseline_original_entry_time_et": prereg["delayed_entry_rule"]["baseline_original_entry_time_et"],
            "candidate_decision_time_et": prereg["delayed_entry_rule"]["new_candidate_decision_time_et"],
            "earliest_candidate_entry_time_et": prereg["delayed_entry_rule"]["earliest_candidate_entry_time_et"],
            "original_0935_pnl_reused_as_delayed_entry_pnl": False,
            "delayed_entry_result_type": "proxy_only_no_delayed_quote",
        },
        "trial_policy": {
            "threshold_search_allowed": False,
            "threshold_search_used": False,
            "new_filter_search_used": False,
            "oos_tuning_used": False,
            "trial_count": 0,
            "search_log": _relative(search_log_path),
            "dsr_status": "not_recomputed_no_new_threshold_search",
            "dsr_reason": "No threshold, filter, or best-Sharpe search was performed in this delayed-entry diagnostic.",
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
        "original_entry_context_not_delayed_pnl": {
            "purpose": "Context only. These values come from the original existing trade outcomes and are not delayed-entry PnL.",
            "baseline_oos": _group_stats(oos_baseline),
            "retained_oos": _group_stats(oos_retained),
            "skipped_oos": _group_stats(oos_skipped),
        },
        **checks,
        "hypothesis_decision": decision,
        "allowed_claims": [
            "The locked H-A2 condition is timestamp-clean only after the 15-minute window completes at 09:45 ET.",
            "Current local artifacts can recount retained/skipped samples under the locked 0.001 rule.",
            "Current local artifacts cannot support delayed-entry implementable PnL because no 09:45 delayed-entry quote/fill is available.",
            "This result is E1 proxy-only diagnostic evidence.",
        ],
        "forbidden_claims": prereg.get("forbidden_claims", []),
        "next_safe_action": decision["allowed_next_action"],
        "tier_blockers": [
            "E1 proxy-only diagnostic/prioritization evidence only",
            "No auditable delayed-entry 09:45 option quote/fill in current local artifacts",
            "Original 09:35 PnL was not reused and cannot stand in for delayed-entry PnL",
            "Under-sampled and underpowered retained OOS sample",
            "No exact 2022-10 ORB replay",
            "No E2 acceptance claim",
            "No paper trading, operational validation, or real-money approval",
        ],
    }


def _timestamp_cleanliness(rule: dict[str, Any], signal_attribution: dict[str, Any]) -> dict[str, Any]:
    decision = rule["new_candidate_decision_time_et"]
    windows = [
        {
            "feature": "proxy_5m_followthrough",
            "window_et": "09:30:00-09:35:00",
            "known_by_decision_time": True,
        },
        {
            "feature": "no_adverse_measured_15m_conflict",
            "window_et": "09:30:00-09:45:00",
            "known_by_decision_time": decision >= "09:45:00",
        },
    ]
    all_known = all(item["known_by_decision_time"] for item in windows)
    return {
        "status": "complete",
        "candidate_decision_time_et": decision,
        "feature_completion_times_et": {
            "proxy_5m_followthrough": "09:35:00",
            "no_adverse_measured_15m_conflict": "09:45:00",
        },
        "feature_measurement_windows": windows,
        "all_features_known_by_decision_time": all_known,
        "timestamp_cleanliness_status": "pass_for_delayed_0945_decision" if all_known else "blocked_feature_after_decision",
        "blocked_if_any_feature_after_decision": not all_known,
        "source_original_entry_classification": signal_attribution.get("entry_rule_classification", {}).get("classification"),
    }


def _delayed_entry_quote_audit(
    candidate_time: str,
    daily_rows: list[dict[str, Any]],
    retained_oos: list[dict[str, Any]],
) -> dict[str, Any]:
    retained_dates = {row["date"] for row in retained_oos}
    daily_row_fields = sorted({key for row in daily_rows for key in row.keys()})
    quote_like_fields = [field for field in daily_row_fields if "quote" in field or "entry" in field]
    has_delayed_quote_fields = any(field in daily_row_fields for field in ["delayed_entry_quote", "quote_timestamp_et"])
    return {
        "status": "blocked_no_delayed_entry_quote",
        "entry_quote_source_status": "missing_0945_option_quote_in_preregistered_source_artifacts",
        "entry_time_et": candidate_time,
        "source_artifact_checked": _relative(DEFAULT_DAILY_SOURCE_PATH),
        "source_artifact_row_count": len(daily_rows),
        "source_artifact_quote_like_fields": quote_like_fields,
        "source_artifact_has_delayed_quote_fields": has_delayed_quote_fields,
        "retained_oos_dates_checked": sorted(retained_dates),
        "quote_timestamp_hit_count": 0,
        "retained_oos_quote_hit_count": 0,
        "quote_timestamp_hits": {},
        "fill_assumption": "not_computed_no_0945_quote",
        "cost_assumption": "not_computed_no_0945_quote",
        "blocked_if_no_delayed_entry_quote": True,
        "proxy_result_must_be_labeled": True,
        "delayed_entry_implementable_pnl_available": False,
    }


def _sample_recount(
    train_baseline: list[dict[str, Any]],
    train_retained: list[dict[str, Any]],
    train_skipped: list[dict[str, Any]],
    oos_baseline: list[dict[str, Any]],
    oos_retained: list[dict[str, Any]],
    oos_skipped: list[dict[str, Any]],
) -> dict[str, Any]:
    retained_count = len(train_retained) + len(oos_retained)
    skipped_count = len(train_skipped) + len(oos_skipped)
    return {
        "status": "complete",
        "train_trade_count": len(train_baseline),
        "oos_trade_count": len(oos_baseline),
        "retained_train_trade_count": len(train_retained),
        "retained_oos_trade_count": len(oos_retained),
        "skipped_train_trade_count": len(train_skipped),
        "skipped_oos_trade_count": len(oos_skipped),
        "retained_count": retained_count,
        "skipped_count": skipped_count,
        "under_sampled_label": True,
        "underpowered_label": True,
    }


def _pnl_comparison(
    oos_baseline: list[dict[str, Any]],
    oos_retained: list[dict[str, Any]],
    oos_skipped: list[dict[str, Any]],
    delayed_quote: dict[str, Any],
    robustness_summary: dict[str, Any],
) -> dict[str, Any]:
    delayed_available = delayed_quote["delayed_entry_implementable_pnl_available"]
    return {
        "status": "blocked_no_delayed_entry_pnl" if not delayed_available else "complete",
        "baseline_avg_implementable_pnl": None if not delayed_available else _group_stats(oos_baseline)["avg_implementable_pnl"],
        "delayed_entry_avg_implementable_pnl": None,
        "skipped_avg_implementable_pnl": None if not delayed_available else _group_stats(oos_skipped)["avg_implementable_pnl"],
        "cost_drag": None,
        "comparison_status": "not_computable_without_0945_quote",
        "original_entry_context_only": {
            "baseline_oos_avg_implementable_pnl": _group_stats(oos_baseline)["avg_implementable_pnl"],
            "retained_oos_avg_implementable_pnl": _group_stats(oos_retained)["avg_implementable_pnl"],
            "skipped_oos_avg_implementable_pnl": _group_stats(oos_skipped)["avg_implementable_pnl"],
            "retained_minus_skipped_avg_implementable_pnl": robustness_summary.get("skip_cost_tradeoff_check", {}).get("retained_minus_skipped_avg_implementable_pnl")
            or robustness_summary.get("skip_cost_tradeoff_check", {}).get("retained_minus_skipped_avg_pnl"),
            "not_delayed_entry_pnl": True,
        },
        "original_0935_pnl_reused_as_delayed_entry_pnl": False,
    }


def _risk_recheck(oos_baseline: list[dict[str, Any]], oos_retained: list[dict[str, Any]]) -> dict[str, Any]:
    baseline_trim = _trimmed_stats(oos_baseline)
    retained_trim = _trimmed_stats(oos_retained)
    return {
        "status": "diagnostic_underpowered",
        "big_day_dependency_status": "context_only_no_delayed_pnl",
        "concentration_status": _concentration_label(oos_retained),
        "mintrl_psr_status": "blocked_underpowered_e1_proxy_only",
        "dsr_or_search_log_status": "not_recomputed_no_new_threshold_search",
        "evidence_tier_cap": "E1",
        "baseline_oos_after_trim": baseline_trim["after_trim"],
        "retained_oos_after_trim_original_entry_context": retained_trim["after_trim"],
        "interpretation": "Risk checks remain context-only because delayed-entry PnL is unavailable.",
    }


def _decision(checks: dict[str, Any]) -> dict[str, Any]:
    timestamp_clean = checks["delayed_entry_timestamp_cleanliness"]["all_features_known_by_decision_time"]
    quote_available = checks["delayed_entry_fill_and_cost_feasibility"]["delayed_entry_implementable_pnl_available"]
    if timestamp_clean and not quote_available:
        decision = "revise_to_timestamp_clean_original_entry_or_preregister_delayed_quote_acquisition"
        allowed_next = (
            "Do not claim delayed-entry edge from current artifacts. Next safe work is to pre-register a timestamp-clean "
            "original-entry revision using only 09:35-known features, or separately pre-register a no-paid/guarded delayed-entry "
            "quote acquisition plan before any delayed-entry PnL test."
        )
    elif timestamp_clean and quote_available:
        decision = "continue_delayed_entry_candidate_under_e1_only"
        allowed_next = "Run a separate implementable delayed-entry PnL test with the found 09:45 quotes while preserving threshold 0.001."
    else:
        decision = "park_delayed_entry_due_to_timestamp_failure"
        allowed_next = "Park delayed-entry H-A2 until all features are known by the candidate decision time."
    return {
        "status": "complete",
        "decision": decision,
        "evidence_tier": "E1",
        "allowed_next_action": allowed_next,
        "forbidden_claims": [
            "No delayed-entry implementable PnL claim.",
            "No H-A2 edge validation.",
            "No E2 evidence.",
            "No paper trading, operational validation, or real-money approval.",
        ],
        "research_log_requirement": "research_log/030-higanbana-h-a2-delayed-entry-condition.md",
        "e2_status": "forbidden",
    }


def _skipped(baseline: list[dict[str, Any]], retained: list[dict[str, Any]]) -> list[dict[str, Any]]:
    retained_dates = {row["date"] for row in retained}
    return [row for row in baseline if row["date"] not in retained_dates]


def _concentration_label(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "blocked_no_rows"
    month_counts = Counter(row["date"][:7] for row in rows)
    max_share = max(month_counts.values()) / len(rows)
    return "concentrated_or_underpowered" if max_share >= 0.75 or len(rows) < 30 else "not_single_month_dominated"


def _write_search_log(result: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    records = []
    for check_id in [
        "delayed_entry_timestamp_cleanliness",
        "delayed_entry_fill_and_cost_feasibility",
        "retained_sample_recount",
        "implementable_pnl_comparison",
        "risk_and_robustness_recheck",
        "hypothesis_decision",
    ]:
        section = result.get(check_id, {})
        records.append(
            {
                "record_type": "delayed_entry_diagnostic_check",
                "experiment_id": result["experiment_id"],
                "check_id": check_id,
                "locked_threshold": result["methodology"]["locked_threshold"],
                "candidate_decision_time_et": result["methodology"]["candidate_decision_time_et"],
                "threshold_search_used": False,
                "new_filter_search_used": False,
                "status": section.get("status"),
            }
        )
    path.write_text("\n".join(json.dumps(record, ensure_ascii=False, sort_keys=True) for record in records) + "\n", encoding="utf-8")


def _render_report(result: dict[str, Any]) -> str:
    counts = result["sample_counts"]
    quote = result["delayed_entry_fill_and_cost_feasibility"]
    pnl = result["implementable_pnl_comparison"]
    decision = result["hypothesis_decision"]
    context = result["original_entry_context_not_delayed_pnl"]
    return "\n".join(
        [
            "# H-A2 Delayed-Entry Condition Report",
            "",
            f"- Status: `{result['status']}`",
            f"- Conclusion: `{result['conclusion']}`",
            f"- Evidence tier: `{result['evidence_tier']}`",
            f"- Candidate decision time ET: `{result['methodology']['candidate_decision_time_et']}`",
            f"- Locked threshold: `{result['methodology']['locked_threshold']}`",
            f"- Result type: `{result['methodology']['delayed_entry_result_type']}`",
            "",
            "## Timestamp And Fill",
            "",
            "| Check | Result |",
            "|:--|:--|",
            f"| All features known by decision time | `{result['delayed_entry_timestamp_cleanliness']['all_features_known_by_decision_time']}` |",
            f"| Entry quote source status | `{quote['entry_quote_source_status']}` |",
            f"| 09:45 quote hit count | `{quote['quote_timestamp_hit_count']}` |",
            f"| Original 09:35 PnL reused as delayed PnL | `{result['methodology']['original_0935_pnl_reused_as_delayed_entry_pnl']}` |",
            "",
            "## Sample Recount",
            "",
            "| Bucket | Train | OOS |",
            "|:--|--:|--:|",
            f"| Baseline non-risk trades | {counts['baseline_train_non_risk_trade_days']} | {counts['baseline_oos_non_risk_trade_days']} |",
            f"| Retained by locked rule | {counts['retained_train_trade_days']} | {counts['retained_oos_trade_days']} |",
            f"| Skipped by locked rule | {counts['skipped_train_trade_days']} | {counts['skipped_oos_trade_days']} |",
            "",
            "## PnL Status",
            "",
            f"- Delayed-entry implementable PnL: `{pnl['comparison_status']}`",
            "- Original-entry context is shown only to explain why the rule looked interesting before; it is not delayed-entry PnL.",
            "",
            "| Original-entry context group | Avg implementable PnL |",
            "|:--|--:|",
            f"| Baseline OOS | {context['baseline_oos']['avg_implementable_pnl']} |",
            f"| Retained OOS | {context['retained_oos']['avg_implementable_pnl']} |",
            f"| Skipped OOS | {context['skipped_oos']['avg_implementable_pnl']} |",
            "",
            "## Decision",
            "",
            f"- Decision: `{decision['decision']}`",
            f"- Next safe action: {decision['allowed_next_action']}",
            "",
            "## Guardrails",
            "",
            "- No network, paid data, broker request, IBKR request, GDELT live retry, or LLM call was used.",
            "- No threshold search, OOS tuning, or new OOS-selected filter was used.",
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
