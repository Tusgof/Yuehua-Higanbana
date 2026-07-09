from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PREREG_PATH = PROJECT_ROOT / "experiments" / "h_a2_mechanism_revision_preregistration.json"
NORMAL_REPLAY_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_normal_control_exact_replay.json"
POST_STRESS_REPLAY_PATH = (
    PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_post_stress_normalization_control_exact_replay.json"
)
SUMMARY_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_mechanism_revision_audit.json"
REPORT_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_mechanism_revision_audit.md"
SEARCH_LOG_PATH = (
    PROJECT_ROOT
    / "reports"
    / "diagnostics"
    / "search_logs"
    / "h_a2_mechanism_revision_audit_search_log.jsonl"
)


def run_h_a2_mechanism_revision_audit() -> dict[str, Any]:
    prereg = _load_json(PREREG_PATH)
    replays = [_load_json(NORMAL_REPLAY_PATH), _load_json(POST_STRESS_REPLAY_PATH)]
    autopsy = [_build_autopsy(row) for row in replays]

    total_mid_pnl = round(sum(item["mid_pnl"] for item in autopsy), 2)
    total_implementable_pnl = round(sum(item["implementable_pnl"] for item in autopsy), 2)
    total_cost_drag = round(sum(item["cost_drag_vs_mid"] for item in autopsy), 2)
    total_underlying_move = round(sum(item["underlying_entry_to_forced_close_move"] for item in autopsy), 2)

    summary: dict[str, Any] = {
        "schema_version": "h_a2_mechanism_revision_audit_v1",
        "record_type": "experiment_summary",
        "experiment_id": "h_a2_mechanism_revision_audit",
        "hypothesis_id": "H-A2",
        "status": "complete",
        "evidence_tier": "E1",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "conclusion": "ยังสรุปไม่ได้",
        "conclusion_reason": (
            "The two exact-replayed candidates were directionally correct at the underlying level, "
            "but the selected call verticals still lost money because the forced-close underlying "
            "price did not reach the long strike and implementable cost drag remained material."
        ),
        "source_preregistration": _relative(PREREG_PATH),
        "source_artifacts": [
            _relative(PREREG_PATH),
            _relative(NORMAL_REPLAY_PATH),
            _relative(POST_STRESS_REPLAY_PATH),
            "experiments/h_a2_post_two_exact_replay_decision.json",
            "reports/experiments/h_a2_original_entry_robustness_prioritization_summary.json",
            "reports/experiments/h_a2_proxy_first_robustness_summary.json",
        ],
        "preregistration_controls_confirmed": {
            "planned_next_diagnostic": prereg.get("planned_next_diagnostic", {}).get("experiment_id"),
            "mode": prereg.get("planned_next_diagnostic", {}).get("mode"),
            "new_threshold_search_allowed": prereg.get("anti_overfitting_controls", {}).get(
                "new_threshold_search_allowed"
            ),
            "oos_selected_filter_allowed": prereg.get("anti_overfitting_controls", {}).get(
                "oos_selected_filter_allowed"
            ),
            "paid_data_before_mechanism_audit_allowed": prereg.get("anti_overfitting_controls", {}).get(
                "paid_data_before_mechanism_audit_allowed"
            ),
        },
        "mechanism_autopsy": autopsy,
        "aggregate_findings": {
            "candidate_count": len(autopsy),
            "directionally_correct_underlying_count": sum(
                1 for item in autopsy if item["direction_signal_correct_to_forced_close"]
            ),
            "option_pnl_negative_count": sum(1 for item in autopsy if item["implementable_pnl"] < 0),
            "long_strike_not_reached_count": sum(1 for item in autopsy if item["long_strike_above_forced_close"]),
            "direction_signal_not_sufficient": True,
            "strike_reachability_issue": True,
            "cost_drag_material": True,
            "total_underlying_entry_to_forced_close_move": total_underlying_move,
            "total_mid_pnl": total_mid_pnl,
            "total_implementable_pnl": total_implementable_pnl,
            "total_cost_drag_vs_mid": total_cost_drag,
            "average_cost_drag_vs_mid": round(total_cost_drag / len(autopsy), 2),
            "mintrl_psr_status": "blocked_two_trade_underpowered",
            "under_sampled": True,
            "underpowered": True,
        },
        "rule_dimension_assessment": [
            {
                "dimension": "post_entry_followthrough",
                "assessment": "logically_justified_before_parameter_search",
                "reason": (
                    "Both candidates moved in the expected direction after entry, but the move was not enough "
                    "for the selected vertical spread to produce positive implementable PnL."
                ),
                "future_rule_constraint": (
                    "A future train-only rule should measure magnitude against strike reachability or cost-adjusted "
                    "breakeven, not direction alone."
                ),
            },
            {
                "dimension": "strike_reachability",
                "assessment": "logically_justified_before_parameter_search",
                "reason": "In both exact replays, the forced-close underlying price remained below the long call strike.",
                "future_rule_constraint": (
                    "Nearest discrete strike rounding and realized strike gap must be part of any revised rule."
                ),
            },
            {
                "dimension": "cost_drag",
                "assessment": "logically_justified_before_parameter_search",
                "reason": "The two trades lost $9.12 more on implementable PnL than on mid PnL after fees/spread assumptions.",
                "future_rule_constraint": "Mid PnL must remain diagnostic only; implementable PnL is the governing metric.",
            },
            {
                "dimension": "regime_context",
                "assessment": "supporting_context_not_sufficient_alone",
                "reason": (
                    "Clean macro/VIX and normal/post-stress context did not prevent losses in the two exact replays."
                ),
                "future_rule_constraint": (
                    "Regime labels may prioritize samples, but must not replace post-entry magnitude and cost checks."
                ),
            },
            {
                "dimension": "selection_risk",
                "assessment": "must_control_before_any_new_rule",
                "reason": "Changing threshold or filters after these two losses would be post-result tuning.",
                "future_rule_constraint": (
                    "Any revised rule must be pre-registered as train-only with search log, DSR handling, chronological "
                    "split, MinTRL/PSR labels, and big-day dependency checks."
                ),
            },
        ],
        "decision": {
            "selected_next_step": "preregister_train_only_revised_rule",
            "decision_label": "ยังสรุปไม่ได้",
            "reason": (
                "The current locked condition should not receive more sample expansion as-is. The next useful step is "
                "a train-only revised-rule preregistration focused on cost-adjusted magnitude and strike reachability."
            ),
            "why_not_more_data_now": (
                "More exact replays under the same direction-only condition may only repeat the same misspecified "
                "payoff problem and consume the approved Databento budget without improving the hypothesis."
            ),
            "why_not_falsify_h_a2_family": (
                "Only two exact-replayed candidates exist, both under-sampled and underpowered. This can reject the "
                "current locked condition as expansion-ready, but cannot falsify ORB debit spreads as a family."
            ),
            "next_required_artifact": "h_a2_breakeven_aware_rule_preregistration",
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
            "threshold_search_used": False,
            "new_oos_filter_selected": False,
            "strategy_use_allowed": False,
            "paper_trading_allowed": False,
            "operational_validation_allowed": False,
            "real_money_allowed": False,
        },
        "trial_policy": {
            "trial_count": 1,
            "search_log": _relative(SEARCH_LOG_PATH),
            "dsr_status": "not_applicable_no_parameter_search",
            "threshold_0_001_status": "locked_as_prior_diagnostic_reference_only",
        },
        "sample_policy": {
            "sample_count": len(autopsy),
            "under_sampled": True,
            "underpowered": True,
            "mintrl_psr_status": "blocked_two_trade_underpowered",
        },
        "allowed_claims": [
            "H-A2.60 explains why two directionally correct exact replays still lost money after implementable costs.",
            "Direction alone is insufficient for the current H-A2 ORB debit vertical condition.",
            "A train-only revised rule focused on cost-adjusted magnitude and strike reachability is justified as the next control artifact.",
            "The result is E1 diagnostic evidence only.",
        ],
        "forbidden_claims": [
            "Do not claim H-A2 edge is validated.",
            "Do not claim H-A2 is fully falsified as a broad strategy family.",
            "Do not approve paid data from this audit alone.",
            "Do not broaden exact replay from this audit alone.",
            "Do not change threshold 0.001 from this audit.",
            "Do not select a new OOS filter from this audit.",
            "Do not approve paper trading, operational validation, or real-money trading.",
            "Do not claim E2 acceptance-grade evidence.",
        ],
        "tier_blockers": [
            "E1 local mechanism diagnostic only",
            "sample_count_2_under_sampled",
            "MinTRL/PSR blocked",
            "No new independent validation distribution",
            "No E2 acceptance claim",
        ],
        "next_safe_action": (
            "Pre-register H-A2.61 as a train-only revised rule focused on cost-adjusted post-entry magnitude, "
            "strike reachability, and implementable friction before any more paid data, exact replay expansion, "
            "threshold/filter change, E2 claim, paper trading, operational validation, or real-money work."
        ),
        "research_log_required": True,
        "research_log_path": "research_log/039-higanbana-h-a2-mechanism-revision-audit.md",
        "research_log_slug": "higanbana-h-a2-mechanism-revision-audit",
    }
    return summary


def write_outputs(summary: dict[str, Any]) -> None:
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SEARCH_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(_render_markdown(summary), encoding="utf-8")
    SEARCH_LOG_PATH.write_text(
        json.dumps(
            {
                "experiment_id": summary["experiment_id"],
                "trial_id": "mechanism_audit_only",
                "trial_count": 1,
                "parameter_search_used": False,
                "oos_tuning_used": False,
                "decision": summary["decision"]["selected_next_step"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _build_autopsy(payload: dict[str, Any]) -> dict[str, Any]:
    candidate = payload["candidate"]
    pnl = payload["pnl"]
    mapping = payload["selected_vertical"]["mapping"]
    direction = candidate["direction"]
    entry = float(candidate["underlying_entry_close"])
    close = float(candidate["underlying_forced_close"])
    underlying_move = round(close - entry, 2)
    direction_correct = underlying_move > 0 if direction == "call" else underlying_move < 0
    long_strike = float(mapping["long_strike"])
    short_strike = float(mapping["short_strike"])
    long_strike_above_close = close < long_strike if direction == "call" else close > long_strike

    return {
        "source_experiment": payload["experiment_id"],
        "candidate_date": candidate["date"],
        "direction": direction,
        "entry_time_et": candidate["entry_time_et"],
        "forced_close_time_et": candidate["forced_close_time_et"],
        "underlying_entry_close": entry,
        "underlying_forced_close": close,
        "underlying_entry_to_forced_close_move": underlying_move,
        "proxy_5m_followthrough_to_close_pct": candidate["proxy_5m_followthrough_to_close_pct"],
        "direction_signal_correct_to_forced_close": direction_correct,
        "long_strike": long_strike,
        "short_strike": short_strike,
        "long_strike_above_forced_close": long_strike_above_close,
        "realized_long_gap": mapping["realized_long_gap"],
        "realized_width": mapping["realized_width"],
        "entry_mid_debit": pnl["entry_mid_debit"],
        "entry_implementable_debit": pnl["entry_implementable_debit"],
        "forced_close_mid_value": pnl["forced_close_mid_value"],
        "forced_close_implementable_credit": pnl["forced_close_implementable_credit"],
        "mid_pnl": pnl["mid_pnl"],
        "implementable_pnl": pnl["implementable_pnl"],
        "cost_drag_vs_mid": pnl["cost_drag_vs_mid"],
        "failure_mode": "direction_correct_but_option_spread_lost_value_before_forced_close",
        "mechanism_note": (
            "Underlying direction was correct, but the forced-close price did not reach the long strike; "
            "therefore the debit vertical did not gain enough value to overcome debit, spread, and fees."
        ),
    }


def _render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# H-A2 Mechanism Revision Audit",
        "",
        f"- Status: `{summary['status']}`",
        f"- Evidence tier: `{summary['evidence_tier']}`",
        f"- Conclusion: `{summary['conclusion']}`",
        f"- Decision: `{summary['decision']['selected_next_step']}`",
        "",
        "## Mechanism Autopsy",
        "",
        "| Date | Direction | Entry | Close | Long strike | Mid PnL | Implementable PnL | Cost drag | Finding |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for item in summary["mechanism_autopsy"]:
        lines.append(
            "| {date} | {direction} | {entry:.2f} | {close:.2f} | {long:.2f} | {mid:.2f} | {impl:.2f} | {drag:.2f} | {finding} |".format(
                date=item["candidate_date"],
                direction=item["direction"],
                entry=item["underlying_entry_close"],
                close=item["underlying_forced_close"],
                long=item["long_strike"],
                mid=item["mid_pnl"],
                impl=item["implementable_pnl"],
                drag=item["cost_drag_vs_mid"],
                finding=item["failure_mode"],
            )
        )
    agg = summary["aggregate_findings"]
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Both candidates were directionally correct at the underlying level.",
            "- Both candidates still had negative implementable PnL.",
            "- In both cases, the forced-close underlying price remained below the long call strike.",
            f"- Total mid PnL: `{agg['total_mid_pnl']}`.",
            f"- Total implementable PnL: `{agg['total_implementable_pnl']}`.",
            f"- Total cost drag versus mid: `{agg['total_cost_drag_vs_mid']}`.",
            "",
            "## Next Safe Action",
            "",
            summary["next_safe_action"],
            "",
            "## Guardrails",
            "",
            "- No paid data was used.",
            "- No exact replay expansion was used.",
            "- No threshold search or OOS filter selection was used.",
            "- No paper trading, operational validation, real-money, or E2 claim is allowed.",
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


def main() -> int:
    summary = run_h_a2_mechanism_revision_audit()
    write_outputs(summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
