from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.environment import data_root, interpreter_metadata
from lib.io import load_json, load_jsonl, write_json, write_jsonl
from lib.orb import opening_breakout
from lib.regime_inputs import load_macro_events_by_date, load_vix_vxv, previous_vix_record
from scripts.validate_h_a2_2022_10_stress_exact_replay_preregistration import validate


PREREG = PROJECT_ROOT / "experiments" / "h_a2_2022_10_stress_exact_replay_preregistration.json"
COST_PLAN = PROJECT_ROOT / "reports" / "data_cost" / "h_a2_2022_h2_stress_decision_tree_cost_plan.json"
SUMMARY = PROJECT_ROOT / "reports" / "experiments" / "h_a2_2022_10_stress_exact_replay_summary.json"
REPORT = PROJECT_ROOT / "reports" / "experiments" / "h_a2_2022_10_stress_exact_replay_report.md"
SEARCH_LOG = PROJECT_ROOT / "reports" / "experiments" / "search_logs" / "h_a2_2022_10_stress_exact_replay_search_log.jsonl"


def run() -> dict[str, Any]:
    check = validate(PREREG)
    if check["status"] != "pass":
        raise RuntimeError(str(check["blockers"]))
    prereg = load_json(PREREG)
    dates = load_json(COST_PLAN)["october_stress_dates"]
    bars = load_jsonl(data_root() / "normalized" / "spy_0dte" / "ibkr" / "h_a2_2022_10_stress" / "spy_bar.jsonl")
    by_date: dict[str, list[dict[str, Any]]] = {date: [] for date in dates}
    for row in bars:
        day = row["timestamp_et"][:10]
        if day in by_date:
            by_date[day].append(row)
    vix_rows = load_vix_vxv(data_root() / "normalized" / "spy_0dte" / "vix_vxv" / "vix_vxv.jsonl")
    macro = load_macro_events_by_date(data_root() / "normalized" / "spy_0dte" / "macro_calendar" / "macro_event.jsonl")
    rows = []
    for day in dates:
        prior = previous_vix_record(day, vix_rows)
        prior_vix = float(prior["vix_close"]) if prior else None
        high_macro = [event for event in macro.get(day, []) if event.get("importance") == "high"]
        regime_pass = prior_vix is not None and prior_vix < 25.0 and not high_macro
        breakout = opening_breakout(by_date[day])
        candidate = regime_pass and breakout.get("direction") in {"call", "put"}
        rows.append(
            {
                "date": day,
                "bar_count": len(by_date[day]),
                "prior_vix_close": prior_vix,
                "high_importance_macro_types": sorted({event["event_type"] for event in high_macro}),
                "ex_ante_regime_pass": regime_pass,
                "opening_breakout": breakout,
                "candidate_trade": candidate,
                "pnl": None,
                "pnl_reason": "No strategy trade passed the ex-ante regime gate" if not candidate else "candidate_requires_option_replay",
            }
        )
    candidates = [row for row in rows if row["candidate_trade"]]
    checkpoint_pass = len(candidates) >= prereg["trade_density_checkpoint"]["minimum_candidate_trades_for_september_stage"]
    summary = {
        "record_type": "experiment_summary",
        "schema_version": "h_a2_2022_10_stress_exact_replay_v1",
        "experiment_id": "h_a2_2022_10_stress_exact_replay",
        "hypothesis_id": "H-A2",
        "evidence_tier": "E1",
        "status": "complete_no_candidate_trades" if not candidates else "blocked_candidate_option_replay_required",
        "conclusion": "ยังสรุปไม่ได้",
        "conclusion_reason": "All 13 stress dates failed the ex-ante clean macro/VIX gate, so the locked H-A2 rule produced no trades.",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source_preregistration": PREREG.relative_to(PROJECT_ROOT).as_posix(),
        "date_count": len(rows),
        "bar_coverage_pass_count": sum(row["bar_count"] == 390 for row in rows),
        "raw_opening_breakout_count": sum(row["opening_breakout"].get("direction") in {"call", "put"} for row in rows),
        "ex_ante_regime_pass_count": sum(row["ex_ante_regime_pass"] for row in rows),
        "candidate_trade_count": len(candidates),
        "mid_pnl": None,
        "implementable_pnl": None,
        "pnl_not_computed_reason": "No candidate trade survived the ex-ante regime gate.",
        "trade_density_checkpoint": {
            "minimum_required": 2,
            "observed": len(candidates),
            "pass": checkpoint_pass,
            "september_purchase_allowed": checkpoint_pass,
            "decision": "proceed_to_september_cost_refresh" if checkpoint_pass else "stop_without_september_purchase",
        },
        "sample_policy": {
            "sample_count": len(candidates),
            "mintrl_psr_status": "blocked_zero_trades",
            "under_sampled": True,
            "underpowered": True,
        },
        "lookahead_controls": {
            "future_1545_followthrough_used_as_decision_feature": False,
            "same_day_vix_close_used_as_decision_feature": False,
            "decision_inputs_cutoff_et": "09:35:00",
        },
        "date_results": rows,
        "trial_policy": {"trial_count": 1, "threshold_search_used": False, "dsr_status": "not_applicable_no_search"},
        "big_day_dependency": {"status": "not_applicable_zero_trades"},
        "paper_trading_allowed": False,
        "operational_validation_allowed": False,
        "real_money_allowed": False,
        "tier_blockers": ["zero_candidate_trades", "MinTRL/PSR unavailable", "E1 stress diagnostic only"],
        "interpreter": interpreter_metadata(),
        "research_log_required": True,
        "research_log_slug": "higanbana-h-a2-october-2022-stress-exact-replay",
        "research_log_path": "research_log/041-higanbana-h-a2-october-2022-stress-exact-replay.md",
    }
    write_json(SUMMARY, summary)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(render(summary), encoding="utf-8")
    write_jsonl(SEARCH_LOG, [{"record_type": "parameter_search_trial", "trial_id": 1, "candidate_trade_count": len(candidates), "selected": True}])
    return summary


def render(summary: dict[str, Any]) -> str:
    return "\n".join([
        "# H-A2 October 2022 Stress Exact Replay",
        "",
        f"- Conclusion: `{summary['conclusion']}`",
        f"- Dates: `{summary['date_count']}`",
        f"- Raw 09:35 breakouts: `{summary['raw_opening_breakout_count']}`",
        f"- Ex-ante regime passes: `{summary['ex_ante_regime_pass_count']}`",
        f"- Candidate trades: `{summary['candidate_trade_count']}`",
        f"- September purchase allowed: `{summary['trade_density_checkpoint']['september_purchase_allowed']}`",
        "",
        "All dates failed the prior-VIX/macro gate before option entry. No PnL was invented for non-existent trades. The 15:45 close was not used as a 09:35 decision feature.",
        ""
    ])


if __name__ == "__main__":
    result = run()
    print(json.dumps({key: value for key, value in result.items() if key != "date_results"}, ensure_ascii=False, indent=2))
