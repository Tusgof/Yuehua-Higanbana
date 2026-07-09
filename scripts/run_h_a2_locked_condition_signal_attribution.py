from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PREREG_PATH = PROJECT_ROOT / "experiments" / "h_a2_locked_condition_signal_attribution_preregistration.json"
REVISED_SUMMARY_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_revised_opening_followthrough_condition_summary.json"
ROBUSTNESS_SUMMARY_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_revised_condition_robustness_summary.json"
SUMMARY_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_locked_condition_signal_attribution_summary.json"
REPORT_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_locked_condition_signal_attribution_report.md"
SEARCH_LOG_PATH = (
    PROJECT_ROOT
    / "reports"
    / "experiments"
    / "search_logs"
    / "h_a2_locked_condition_signal_attribution_search_log.jsonl"
)


def run_audit() -> dict[str, Any]:
    prereg = _load_json(PREREG_PATH)
    revised = _load_json(REVISED_SUMMARY_PATH)
    robustness = _load_json(ROBUSTNESS_SUMMARY_PATH)

    locked_threshold = prereg["locked_condition"]["opening_followthrough_threshold"]
    threshold_lock = revised.get("threshold_lock", {})
    sample_policy = revised.get("sample_policy", {})
    sample_counts = revised.get("sample_counts", {})

    decision_timestamp_audit = {
        "intended_decision_time_et": "09:35:00",
        "baseline_entry_time_et": "09:35:00",
        "feature_measurement_windows": [
            {
                "feature": "proxy_5m_followthrough",
                "window_et": "09:30:00-09:35:00",
                "known_by_decision_time": True,
                "timestamp_gap_minutes": 0,
            },
            {
                "feature": "no_adverse_measured_15m_conflict",
                "window_et": "09:30:00-09:45:00",
                "known_by_decision_time": False,
                "timestamp_gap_minutes": 10,
            },
        ],
        "classification": "full_condition_not_known_at_original_entry",
        "reason": "The locked full condition includes the 15-minute conflict check, which is not known at the 09:35 ET baseline entry decision.",
    }

    entry_rule_classification = {
        "baseline_entry_time_et": "09:35:00",
        "earliest_feature_completion_time_et": "09:45:00",
        "deployable_entry_filter_allowed": False,
        "delayed_entry_candidate_allowed": True,
        "diagnostic_proxy_only": True,
        "classification": "delayed_entry_candidate_and_diagnostic_proxy_only",
        "reason": "The 5-minute component may be known at 09:35 ET, but the full locked condition cannot be known until the 15-minute conflict window completes. A delayed-entry strategy would need a separate preregistered backtest with fills and costs.",
    }

    retained = robustness.get("retained_oos", {})
    skipped = robustness.get("skipped_oos", {})
    outcome_proxy_leakage_audit = {
        "proxy_return_field": "proxy_5m.directional_followthrough plus 15-minute conflict check",
        "pnl_field": "existing_implementable_pnl",
        "same_session_overlap_statement": "The proxy uses same-session opening movement and is directionally close to the mechanism that drives same-day option PnL.",
        "retained_oos_avg_implementable_pnl": retained.get("avg_implementable_pnl"),
        "skipped_oos_avg_implementable_pnl": skipped.get("avg_implementable_pnl"),
        "retained_minus_skipped_avg_implementable_pnl": robustness.get("skip_cost_tradeoff_check", {}).get(
            "retained_minus_skipped_avg_implementable_pnl"
        ),
        "leakage_risk_label": "high_for_original_entry_filter_claim",
        "interpretation": "The result is useful as mechanism evidence, but it must not be treated as a deployable original-entry filter until a timestamp-clean rule is tested.",
    }

    fixed_threshold_reconciliation = {
        "locked_threshold": locked_threshold,
        "threshold_source": prereg["locked_condition"]["threshold_source"],
        "threshold_lock_status": threshold_lock.get("status"),
        "oos_used_for_selection": threshold_lock.get("oos_used_for_selection"),
        "new_threshold_count": 0,
        "new_filter_count": 0,
        "search_log_statement": "This audit performs no threshold or filter search; it classifies the already locked condition.",
    }

    hypothesis_implication_review = {
        "allowed_future_claim": "H-A2.27 may only claim that the locked condition is a delayed-entry candidate and diagnostic proxy, not a validated entry filter.",
        "forbidden_future_claim": "Do not claim H-A2 edge validation, E2 evidence, paper trading approval, or original 09:35 entry deployability.",
        "recommended_next_hypothesis_form": "If pursued, pre-register a delayed-entry H-A2 variant where the decision time is after the 15-minute conflict window and fills/costs are modeled explicitly.",
        "exact_replay_priority": "deprioritize_original_entry_exact_replay_until_timestamp_clean_rule_exists",
        "research_log_requirement": "research_log/029-higanbana-h-a2-locked-condition-signal-attribution.md",
    }

    summary = {
        "schema_version": "h_a2_locked_condition_signal_attribution_v1",
        "record_type": "experiment_summary",
        "status": "complete",
        "experiment_id": "h_a2_locked_condition_signal_attribution",
        "hypothesis_id": "H-A2",
        "evidence_tier": "E1",
        "conclusion": "ยังสรุปไม่ได้",
        "conclusion_reason": "The locked threshold remains cleanly fixed, but the full condition is not known at the original 09:35 ET entry decision because it includes a 15-minute conflict check. Treat it as delayed-entry candidate and diagnostic proxy only.",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_preregistration": _relative(PREREG_PATH),
        "source_summary": _relative(REVISED_SUMMARY_PATH),
        "source_robustness_summary": _relative(ROBUSTNESS_SUMMARY_PATH),
        "locked_threshold": locked_threshold,
        "decision_timestamp_availability_audit": decision_timestamp_audit,
        "entry_rule_classification": entry_rule_classification,
        "outcome_proxy_leakage_audit": outcome_proxy_leakage_audit,
        "fixed_threshold_no_search_reconciliation": fixed_threshold_reconciliation,
        "hypothesis_implication_review": hypothesis_implication_review,
        "sample_counts": {
            "baseline_oos_non_risk_trade_days": sample_counts.get("baseline_oos_non_risk_trade_days"),
            "retained_oos_trade_days": sample_counts.get("revised_oos_trade_days"),
            "skipped_oos_trade_days": sample_counts.get("skipped_oos_trade_days"),
        },
        "sample_policy": {
            "under_sampled": sample_policy.get("under_sampled", True),
            "underpowered": sample_policy.get("underpowered", True),
            "mintrl_psr_status": sample_policy.get("mintrl_psr_status", "blocked_underpowered_e1_diagnostic"),
        },
        "trial_policy": {
            "threshold_search_used": False,
            "new_filter_search_used": False,
            "oos_tuning_used": False,
            "search_log": _relative(SEARCH_LOG_PATH),
        },
        "allowed_claims": [
            "The locked threshold 0.001 remains unchanged.",
            "The full locked condition is not a deployable original-entry filter because the 15-minute conflict component is known after 09:35 ET.",
            "The condition may be studied as a delayed-entry candidate or diagnostic proxy only.",
        ],
        "forbidden_claims": [
            "Do not claim H-A2 edge validation.",
            "Do not claim E2 acceptance-grade evidence.",
            "Do not claim original 09:35 ET entry deployability.",
            "Do not approve paper trading, operational validation, or real-money trading.",
        ],
        "network_used": False,
        "paid_data_used": False,
        "new_provider_used": False,
        "broker_request_used": False,
        "ibkr_request_used": False,
        "gdelt_live_retry_used": False,
        "llm_call_used": False,
        "exact_2022_orb_tested": False,
        "paper_trading_allowed": False,
        "operational_validation_allowed": False,
        "real_money_allowed": False,
        "strategy_use_allowed": False,
        "research_log_required": True,
        "research_log_slug": "higanbana-h-a2-locked-condition-signal-attribution",
        "next_safe_action": "Either run a separately pre-registered delayed-entry H-A2 test using local artifacts only, or revise H-A2 toward a timestamp-clean original-entry rule. Do not run exact replay, paid data, IBKR request, LLM call, paper trading, or E2 claim from H-A2.27.",
        "tier_blockers": [
            "under_sampled",
            "underpowered",
            "post_original_entry_feature_component",
            "no_exact_2022_orb_replay",
            "no_e2_acceptance_claim",
        ],
    }

    _write_outputs(summary)
    return summary


def _write_outputs(summary: dict[str, Any]) -> None:
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    SEARCH_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    search_row = {
        "trial_id": "signal_attribution_no_search",
        "locked_threshold": summary["locked_threshold"],
        "threshold_search_used": False,
        "new_filter_search_used": False,
        "classification": summary["entry_rule_classification"]["classification"],
    }
    SEARCH_LOG_PATH.write_text(json.dumps(search_row, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# H-A2 Locked-Condition Signal Attribution Report",
        "",
        f"- Status: `{summary['status']}`",
        f"- Hypothesis: `{summary['hypothesis_id']}`",
        f"- Evidence tier: `{summary['evidence_tier']}`",
        f"- Conclusion: `{summary['conclusion']}`",
        f"- Locked threshold: `{summary['locked_threshold']}`",
        "",
        "## Result",
        "",
        summary["conclusion_reason"],
        "",
        "## Classification",
        "",
        f"- Full-condition classification: `{summary['entry_rule_classification']['classification']}`",
        f"- Deployable original-entry filter allowed: `{summary['entry_rule_classification']['deployable_entry_filter_allowed']}`",
        f"- Delayed-entry candidate allowed: `{summary['entry_rule_classification']['delayed_entry_candidate_allowed']}`",
        f"- Diagnostic proxy only: `{summary['entry_rule_classification']['diagnostic_proxy_only']}`",
        "",
        "## Timestamp Audit",
        "",
        "| Feature | Window ET | Known by 09:35 ET | Gap minutes |",
        "|:--|:--|:--:|--:|",
    ]
    for item in summary["decision_timestamp_availability_audit"]["feature_measurement_windows"]:
        lines.append(
            f"| `{item['feature']}` | `{item['window_et']}` | `{item['known_by_decision_time']}` | {item['timestamp_gap_minutes']} |"
        )
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- No threshold search.",
            "- No new OOS-selected filter.",
            "- No network, paid data, IBKR request, GDELT retry, or LLM call.",
            "- No paper-trading, operational-validation, real-money, or E2 claim.",
            "",
            "## Next Safe Action",
            "",
            summary["next_safe_action"],
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT))


def main() -> int:
    summary = run_audit()
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
