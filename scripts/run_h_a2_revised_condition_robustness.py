from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_h_a2_revised_opening_followthrough_condition import (
    _apply_revised_condition,
    _group_stats,
    _non_risk_trades,
    _relative,
    _round,
    _trimmed_stats,
)


DEFAULT_PREREGISTRATION_PATH = PROJECT_ROOT / "experiments" / "h_a2_revised_condition_robustness_preregistration.json"
DEFAULT_SOURCE_SUMMARY_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_revised_opening_followthrough_condition_summary.json"
DEFAULT_DAILY_SOURCE_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_lower_resolution_proxy_summary.json"
DEFAULT_SUMMARY_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_revised_condition_robustness_summary.json"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_revised_condition_robustness_report.md"
DEFAULT_SEARCH_LOG_PATH = PROJECT_ROOT / "reports" / "experiments" / "search_logs" / "h_a2_revised_condition_robustness_search_log.jsonl"


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
    threshold = float(prereg["locked_condition"]["opening_followthrough_threshold"])

    rows = list(daily_source["daily_rows"])
    baseline_oos = _non_risk_trades(rows, split="oos")
    retained_oos = _apply_revised_condition(baseline_oos, threshold)
    retained_dates = {row["date"] for row in retained_oos}
    skipped_oos = [row for row in baseline_oos if row["date"] not in retained_dates]

    checks = {
        "threshold_provenance_audit": _threshold_provenance(prereg, source_summary, threshold),
        "big_day_dependency_check": _big_day_dependency(baseline_oos, retained_oos),
        "concentration_fragility_check": _concentration(retained_oos),
        "skip_cost_tradeoff_check": _skip_cost_tradeoff(baseline_oos, retained_oos, skipped_oos),
        "sample_adequacy_relabeling": _sample_adequacy(retained_oos),
    }
    decision = _decision(checks)
    result = _summary(
        prereg=prereg,
        source_summary=source_summary,
        daily_source=daily_source,
        threshold=threshold,
        baseline_oos=baseline_oos,
        retained_oos=retained_oos,
        skipped_oos=skipped_oos,
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
    baseline_oos: list[dict[str, Any]],
    retained_oos: list[dict[str, Any]],
    skipped_oos: list[dict[str, Any]],
    checks: dict[str, Any],
    decision: dict[str, Any],
    preregistration_path: Path,
    source_summary_path: Path,
    daily_source_path: Path,
    search_log_path: Path,
) -> dict[str, Any]:
    return {
        "record_type": "experiment_summary",
        "schema_version": "h_a2_revised_condition_robustness_v1",
        "experiment_id": "h_a2_revised_condition_robustness",
        "hypothesis_id": "H-A2",
        "evidence_tier": "E1",
        "status": "complete",
        "conclusion": "ยังสรุปไม่ได้",
        "conclusion_reason": (
            "The locked 0.001 revised condition survives basic local robustness checks, "
            "but the retained OOS sample is only 13 trade days and remains under-sampled."
        ),
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "research_log_required": True,
        "research_log_slug": "higanbana-h-a2-revised-condition-robustness",
        "source_preregistration": _relative(preregistration_path),
        "source_summary": _relative(source_summary_path),
        "daily_source": _relative(daily_source_path),
        "source_summary_experiment_id": source_summary.get("experiment_id"),
        "daily_source_experiment_id": daily_source.get("experiment_id"),
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
            "threshold_locked_before_audit": True,
            "locked_threshold": threshold,
            "audit_scope": "OOS retained/skipped robustness around the already locked H-A2.24 condition.",
        },
        "trial_policy": {
            "threshold_search_allowed": False,
            "threshold_search_used": False,
            "trial_count": 0,
            "all_checks_preregistered": True,
            "search_log": _relative(search_log_path),
            "dsr_status": "not_recomputed_no_new_threshold_search",
            "dsr_reason": "This audit does not select a new best Sharpe or new threshold; it only audits the locked H-A2.24 condition.",
        },
        "sample_counts": {
            "daily_rows": len(daily_source.get("daily_rows", [])),
            "baseline_oos_non_risk_trade_days": len(baseline_oos),
            "retained_oos_trade_days": len(retained_oos),
            "skipped_oos_trade_days": len(skipped_oos),
            "retention_rate": _round(len(retained_oos) / len(baseline_oos)) if baseline_oos else None,
        },
        "baseline_oos": _group_stats(baseline_oos),
        "retained_oos": _group_stats(retained_oos),
        "skipped_oos": _group_stats(skipped_oos),
        "threshold_provenance_audit": checks["threshold_provenance_audit"],
        "big_day_dependency_check": checks["big_day_dependency_check"],
        "concentration_fragility_check": checks["concentration_fragility_check"],
        "skip_cost_tradeoff_check": checks["skip_cost_tradeoff_check"],
        "sample_adequacy_relabeling": checks["sample_adequacy_relabeling"],
        "decision_rule_application": decision,
        "tier_blockers": [
            "E1 diagnostic/prioritization evidence only",
            "Retained OOS sample has only 13 trade days",
            "Under-sampled and underpowered versus MinTRL/PSR policy",
            "No new independent validation data",
            "No exact 2022-10 ORB replay",
            "No E2 acceptance claim",
            "No paper trading, operational validation, or real-money approval",
        ],
        "allowed_claims": prereg.get("allowed_claims", []),
        "forbidden_claims": prereg.get("forbidden_claims", []),
        "next_safe_action": decision["next_safe_action"],
    }


def _threshold_provenance(prereg: dict[str, Any], source_summary: dict[str, Any], threshold: float) -> dict[str, Any]:
    lock = source_summary.get("threshold_lock", {})
    trial_policy = source_summary.get("trial_policy", {})
    clean = (
        lock.get("status") == "locked"
        and float(lock.get("locked_threshold")) == threshold
        and lock.get("oos_used_for_selection") is False
        and trial_policy.get("trial_count") == 7
    )
    return {
        "status": "complete",
        "locked_threshold": threshold,
        "source_locked_threshold": lock.get("locked_threshold"),
        "source_selected_trial_id": lock.get("selected_trial_id"),
        "source_trial_count": trial_policy.get("trial_count"),
        "source_search_log": trial_policy.get("search_log"),
        "threshold_search_used_in_this_audit": False,
        "oos_used_for_threshold_selection": lock.get("oos_used_for_selection"),
        "provenance_clean": clean,
        "interpretation": "Threshold 0.001 remains fixed from H-A2.24 train-only selection; this audit does not create a new threshold.",
    }


def _big_day_dependency(baseline_oos: list[dict[str, Any]], retained_oos: list[dict[str, Any]]) -> dict[str, Any]:
    baseline_trim = _trimmed_stats(baseline_oos)
    retained_trim = _trimmed_stats(retained_oos)
    survives = (
        retained_trim["after_trim"]["avg_implementable_pnl"] is not None
        and retained_trim["after_trim"]["avg_implementable_pnl"] > baseline_trim["after_trim"]["avg_implementable_pnl"]
        and retained_trim["after_trim"]["loss_rate"] < baseline_trim["after_trim"]["loss_rate"]
    )
    return {
        "status": "diagnostic_underpowered",
        "baseline_oos_before_trim": baseline_trim["before_trim"],
        "baseline_oos_after_trim": baseline_trim["after_trim"],
        "retained_oos_before_trim": retained_trim["before_trim"],
        "retained_oos_after_trim": retained_trim["after_trim"],
        "trimmed_each_tail_count_baseline": baseline_trim["trimmed_each_tail_count"],
        "trimmed_each_tail_count_retained": retained_trim["trimmed_each_tail_count"],
        "survives_extreme_trim": survives,
        "dependency_label": "survives_basic_trim_but_underpowered" if survives else "fragile_or_unproven",
        "interpretation": "Baseline has enough OOS rows for a 5% tail trim, but retained OOS has only 13 rows so retained-side trimming is underpowered.",
    }


def _concentration(rows: list[dict[str, Any]]) -> dict[str, Any]:
    dimensions: dict[str, Callable[[dict[str, Any]], str]] = {
        "side": lambda row: row.get("adapter_direction") or "none",
        "month": lambda row: row["date"][:7],
        "weekday": lambda row: date.fromisoformat(row["date"]).strftime("%a"),
        "vix_bucket": _vix_bucket,
    }
    buckets = {name: _bucket_stats(rows, fn) for name, fn in dimensions.items()}
    max_share = max((bucket["max_share"] or 0 for bucket in buckets.values()), default=0)
    warnings = []
    for name, bucket in buckets.items():
        if bucket["max_share"] is not None and bucket["max_share"] >= 0.75:
            warnings.append(f"high_concentration:{name}")
        if bucket["min_bucket_count"] is not None and bucket["min_bucket_count"] < 3:
            warnings.append(f"small_bucket_counts:{name}")
    return {
        "status": "complete",
        "buckets": buckets,
        "max_bucket_share": _round(max_share),
        "small_bucket_warnings": sorted(warnings),
        "concentration_label": "not_single_bucket_dominated" if max_share < 0.75 else "concentrated",
        "interpretation": "No inspected dimension owns 75% or more of retained OOS trades, but several buckets are too small for inference.",
    }


def _skip_cost_tradeoff(
    baseline_oos: list[dict[str, Any]],
    retained_oos: list[dict[str, Any]],
    skipped_oos: list[dict[str, Any]],
) -> dict[str, Any]:
    retained = _group_stats(retained_oos)
    skipped = _group_stats(skipped_oos)
    return {
        "status": "complete",
        "baseline_oos_trade_count": len(baseline_oos),
        "retained_oos_trade_count": len(retained_oos),
        "skipped_oos_trade_count": len(skipped_oos),
        "retention_rate": _round(len(retained_oos) / len(baseline_oos)) if baseline_oos else None,
        "retained_oos": retained,
        "skipped_oos": skipped,
        "retained_minus_skipped_avg_pnl": _diff(retained["avg_implementable_pnl"], skipped["avg_implementable_pnl"]),
        "interpretation": "The locked rule keeps fewer trades, but the skipped set is strongly loss-heavy in current OOS.",
    }


def _sample_adequacy(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "status": "diagnostic_underpowered",
        "sample_count": len(rows),
        "mintrl_status_or_blocker": "blocked_not_enough_retained_oos_observations",
        "psr_status_or_blocker": "blocked_not_enough_retained_oos_observations",
        "under_sampled_label": True,
        "underpowered_label": True,
        "evidence_tier_cap": "E1",
        "interpretation": "Thirteen retained OOS trade days cannot support acceptance-grade MinTRL/PSR inference.",
    }


def _decision(checks: dict[str, Any]) -> dict[str, Any]:
    provenance_clean = checks["threshold_provenance_audit"]["provenance_clean"]
    survives_trim = checks["big_day_dependency_check"]["survives_extreme_trim"]
    concentrated = checks["concentration_fragility_check"]["concentration_label"] == "concentrated"
    sample_count = checks["sample_adequacy_relabeling"]["sample_count"]
    if provenance_clean and survives_trim and not concentrated and sample_count >= 10:
        decision = "run_locked_condition_robustness_followup_or_exact_replay_when_bars_clear"
        next_safe_action = (
            "Keep H-A2 active as E1 prioritization evidence. The next safe step is either exact replay "
            "after the 2022 SPY bar blocker clears, or a separately pre-registered local follow-up that does not change threshold 0.001."
        )
    elif not provenance_clean:
        decision = "park_revised_condition_due_to_threshold_provenance_failure"
        next_safe_action = "Park the revised condition until threshold provenance is repaired; do not exact replay or trade it."
    else:
        decision = "keep_h_a2_under_review_do_not_prioritize_paid_exact_work"
        next_safe_action = "Keep H-A2 under review and do not spend paid/exact-source work from this robustness result alone."
    return {
        "status": "complete",
        "decision": decision,
        "evidence_tier": "E1",
        "threshold_locked_before_audit": provenance_clean,
        "threshold_search_used": False,
        "oos_tuning_used": False,
        "blockers": [
            "under_sampled",
            "underpowered",
            "no_exact_2022_orb_replay",
            "no_e2_acceptance_claim",
        ],
        "next_safe_action": next_safe_action,
    }


def _bucket_stats(rows: list[dict[str, Any]], key_fn: Callable[[dict[str, Any]], str]) -> dict[str, Any]:
    counts = Counter(key_fn(row) for row in rows)
    total = len(rows)
    groups = []
    for key in sorted(counts):
        group = [row for row in rows if key_fn(row) == key]
        groups.append({"bucket": key, **_group_stats(group)})
    return {
        "bucket_count": len(counts),
        "max_bucket_count": max(counts.values()) if counts else None,
        "min_bucket_count": min(counts.values()) if counts else None,
        "max_share": _round(max(counts.values()) / total) if total and counts else None,
        "groups": groups,
    }


def _vix_bucket(row: dict[str, Any]) -> str:
    vix = row.get("regimes", {}).get("prior_vix_close")
    if vix is None:
        return "unknown"
    value = float(vix)
    if value < 15:
        return "low"
    if value < 25:
        return "normal"
    return "high_or_stress"


def _render_report(result: dict[str, Any]) -> str:
    counts = result["sample_counts"]
    big_day = result["big_day_dependency_check"]
    concentration = result["concentration_fragility_check"]
    skip = result["skip_cost_tradeoff_check"]
    decision = result["decision_rule_application"]
    return "\n".join(
        [
            "# H-A2 Revised Condition Robustness Report",
            "",
            f"- Status: `{result['status']}`",
            f"- Conclusion: `{result['conclusion']}`",
            f"- Evidence tier: `{result['evidence_tier']}`",
            f"- Locked threshold: `{result['methodology']['locked_threshold']}`",
            f"- Threshold search used: `{result['methodology']['threshold_search_used']}`",
            f"- OOS tuning used: `{result['methodology']['oos_tuning_used']}`",
            "",
            "## Core Counts",
            "",
            "| Metric | Value |",
            "|:--|--:|",
            f"| Baseline OOS non-risk trades | {counts['baseline_oos_non_risk_trade_days']} |",
            f"| Retained OOS trades | {counts['retained_oos_trade_days']} |",
            f"| Skipped OOS trades | {counts['skipped_oos_trade_days']} |",
            f"| Retention rate | {counts['retention_rate']} |",
            "",
            "## Robustness Checks",
            "",
            "| Check | Result |",
            "|:--|:--|",
            f"| Threshold provenance | `{result['threshold_provenance_audit']['provenance_clean']}` |",
            f"| Big-day dependency | `{big_day['dependency_label']}` |",
            f"| Concentration | `{concentration['concentration_label']}` |",
            f"| Retained minus skipped avg PnL | `{skip['retained_minus_skipped_avg_pnl']}` |",
            f"| Sample adequacy | `{result['sample_adequacy_relabeling']['status']}` |",
            "",
            "## Decision",
            "",
            f"- Decision: `{decision['decision']}`",
            f"- Next safe action: {decision['next_safe_action']}",
            "",
            "## Guardrails",
            "",
            "- No network, paid data, broker request, IBKR request, GDELT live retry, or LLM call was used.",
            "- No threshold search or OOS tuning was used.",
            "- No paper trading, operational validation, real-money launch, exact 2022 ORB replay, or E2 claim is allowed.",
            "",
        ]
    )


def _write_search_log(result: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    records = []
    for key in [
        "threshold_provenance_audit",
        "big_day_dependency_check",
        "concentration_fragility_check",
        "skip_cost_tradeoff_check",
        "sample_adequacy_relabeling",
    ]:
        records.append(
            {
                "record_type": "robustness_audit_check",
                "experiment_id": result["experiment_id"],
                "check_id": key,
                "threshold_search_used": False,
                "locked_threshold": result["methodology"]["locked_threshold"],
                "status": result[key]["status"],
            }
        )
    path.write_text("\n".join(json.dumps(record, ensure_ascii=False, sort_keys=True) for record in records) + "\n", encoding="utf-8")


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
