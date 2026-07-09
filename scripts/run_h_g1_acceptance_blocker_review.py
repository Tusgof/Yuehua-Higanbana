from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
H_G1_SIDE_AWARE_DIAGNOSTIC = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_gamma_regime_diagnostic_summary_v3_side_aware.json"
OUTPUT_JSON = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_acceptance_blocker_review.json"
OUTPUT_REPORT = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_acceptance_blocker_review.md"

REQUIRED_STATUS = "pass_diagnostic_only"
REQUIRED_POLICY_ID = "h_g1_required_bucket_policy_v3_side_aware"


def run_review(input_path: Path = H_G1_SIDE_AWARE_DIAGNOSTIC) -> dict[str, Any]:
    diagnostic = _read_json(input_path)
    _validate_input(diagnostic)

    gates = diagnostic["validation_gates"]
    coverage = gates["coverage"]
    bucket_coverage = coverage["bucket_weighted_coverage"]
    raw_coverage = coverage["raw_row_coverage"]
    economic_sign = gates["economic_sign"]
    stability = gates["stability"]

    passed_facts = {
        "diagnostic_status": diagnostic["status"],
        "policy_id": diagnostic["policy_version"],
        "date_count": diagnostic["date_count"],
        "quote_count": diagnostic["quote_count"],
        "computed_greeks_count": diagnostic["computed_greeks_count"],
        "raw_computed_greeks_rate": raw_coverage["computed_greeks_rate"],
        "open_interest_join_rate": raw_coverage["open_interest_join_rate"],
        "underlying_join_rate": raw_coverage["underlying_join_rate"],
        "side_aware_required_bucket_oi_notional_share": bucket_coverage["computed_required_bucket_oi_notional_share"],
        "retained_abs_gamma_proxy_share": bucket_coverage["retained_abs_gamma_proxy_share"],
        "economic_sign_correlation": economic_sign["full_day_volatility_correlation"],
        "economic_sign_observation_count": economic_sign["observation_count"],
        "in_sample_dates": stability["regime_counts"]["in_sample"],
        "oos_dates": stability["regime_counts"]["oos"],
        "network_used": diagnostic["network_used"],
        "paid_data_used": diagnostic["paid_data_used"],
        "strategy_pnl_used": diagnostic["strategy_pnl_used"],
        "strategy_use_allowed": diagnostic["strategy_use_allowed"],
    }

    blocker_groups = [
        _blocker(
            blocker_id="strategy_ablation_missing",
            category="strategy_evidence",
            severity="hard_blocker",
            status="blocked",
            why="H-G1.19 validates a proxy data pipeline, not a trading rule. No backtest compares baseline strategy versus NOVI/net-gamma-filtered strategy.",
            required_evidence=[
                "Pre-registered strategy rule that states how the gamma proxy affects entry, skip, sizing, or exit.",
                "Baseline versus gamma-filtered implementable PnL on chronological train/OOS splits.",
                "Ablation showing whether improvements come from fewer trades, better average return, lower tail loss, or hidden exposure changes.",
            ],
            next_action="Design a separate H-G1 strategy-ablation preregistration before any NOVI/net-gamma filter can be used.",
        ),
        _blocker(
            blocker_id="mintrl_psr_missing",
            category="statistical_power",
            severity="hard_blocker",
            status="blocked",
            why="There is no strategy-return series for the gamma rule, so Sharpe, PSR, and MinTRL cannot yet be computed for a deployable claim.",
            required_evidence=[
                "Trade-level or day-level return distribution for a pre-registered gamma-filtered strategy.",
                "Observed Sharpe, sample length, skewness, kurtosis, and first-order autocorrelation.",
                "MinTRL and PSR against explicit Sharpe null thresholds, with under-sampled or underpowered labels where needed.",
            ],
            next_action="Compute MinTRL/PSR only after strategy-ablation returns exist.",
        ),
        _blocker(
            blocker_id="dsr_search_log_missing",
            category="multiple_testing",
            severity="hard_blocker",
            status="blocked",
            why="Future gamma thresholds, sign buckets, moneyness buckets, or regime filters can create selection bias if the best result is chosen after many trials.",
            required_evidence=[
                "Pre-registered parameter grid and complete trial log before strategy testing.",
                "Effective trial count and DSR or a documented DSR blocker if a best Sharpe is selected.",
                "No OOS tuning after viewing validation results.",
            ],
            next_action="Require a search log and DSR policy in the next gamma strategy-ablation preregistration.",
        ),
        _blocker(
            blocker_id="big_day_dependency_missing",
            category="robustness",
            severity="hard_blocker",
            status="blocked",
            why="The diagnostic has only proxy-volatility association evidence. It does not show whether strategy performance survives removing extreme winning or losing days.",
            required_evidence=[
                "Remove the most extreme 5% winning/losing trades or close days from the gamma-filtered strategy.",
                "Report whether Sharpe, drawdown, ES95/ES99, and conclusion survive.",
            ],
            next_action="Add big-day dependency checks to the gamma strategy-ablation report template.",
        ),
        _blocker(
            blocker_id="implementable_pnl_missing",
            category="execution_realism",
            severity="hard_blocker",
            status="blocked",
            why="No strategy PnL was used in H-G1.19, so there is no mid PnL versus implementable PnL split or cost-drag measurement.",
            required_evidence=[
                "Mid PnL and implementable PnL reported separately.",
                "Bid/ask spread treatment, per-leg fees, slippage, and forced-close assumptions disclosed.",
                "Cost drag quantified for the gamma-filtered strategy.",
            ],
            next_action="Use project option-backtest reporting rules before any acceptance claim.",
        ),
        _blocker(
            blocker_id="proxy_inventory_caveat",
            category="data_semantics",
            severity="hard_blocker",
            status="blocked",
            why="The signal is signed-OI gamma proxy from OPRA open interest and self-computed Greeks. It is not true dealer/customer inventory or true market-maker net gamma.",
            required_evidence=[
                "Report wording must use signed-OI gamma proxy unless true inventory data is acquired.",
                "Any future true net-gamma claim must identify a source that distinguishes dealer/customer positioning.",
            ],
            next_action="Preserve forbidden claims in all H-G1 reports and strategy docs.",
        ),
        _blocker(
            blocker_id="regime_sample_depth_limited",
            category="regime_coverage",
            severity="soft_blocker",
            status="blocked",
            why="H-G1.19 covers 10 pre-registered diagnostic dates, enough for data-validity diagnostics but not enough to prove stable strategy behavior across market regimes.",
            required_evidence=[
                "Strategy evidence across train/OOS, low/normal/high volatility, macro/no-macro, and stress regimes.",
                "Explicit labels when any filtered regime remains under-sampled.",
            ],
            next_action="Let strategy-ablation sample planning determine whether more data is justified; do not buy broad data from this artifact alone.",
        ),
    ]

    result = {
        "record_type": "h_g1_acceptance_blocker_review",
        "schema_version": "h_g1_acceptance_blocker_review_v1",
        "hypothesis_id": "H-G1",
        "evidence_tier": "E1",
        "status": "blocked_before_strategy_use",
        "conclusion": "ยังสรุปไม่ได้",
        "source_diagnostic": _relative(input_path),
        "network_used": False,
        "paid_data_used": False,
        "strategy_pnl_used": False,
        "new_data_requested": False,
        "strategy_use_allowed": False,
        "paper_trading_allowed": False,
        "allowed_next_action": "preregister_h_g1_strategy_ablation_or_return_to_news_unblock",
        "passed_data_validity_facts": passed_facts,
        "acceptance_blockers": blocker_groups,
        "blocker_summary": _summarize_blockers(blocker_groups),
        "forbidden_claims_preserved": [
            "H-G1 strategy edge validated",
            "NOVI/net-gamma strategy filter ready",
            "true market-maker net gamma",
            "paper trading approved from H-G1.19",
            "paid data justified solely by H-G1.20",
        ],
        "tier_blockers": [
            "E1 acceptance blocker review only",
            "No gamma-filtered strategy-return series",
            "No MinTRL/PSR/DSR for a trading rule",
            "No implementable PnL or big-day dependency test",
            "No true dealer/customer inventory data",
        ],
        "references": [
            "wiki/concepts/backtest-validation-protocol.md",
            "wiki/concepts/minimum-track-record-length.md",
            "wiki/concepts/probabilistic-sharpe-ratio.md",
            "wiki/concepts/deflated-sharpe-ratio.md",
            "wiki/concepts/implementable-option-pnl.md",
        ],
        "research_log_required": True,
        "research_log_slug": "higanbana-gamma-acceptance-blocker-review",
        "research_log_path": "research_log/019-higanbana-gamma-acceptance-blocker-review.md",
    }
    return result


def write_outputs(result: dict[str, Any], output_json: Path = OUTPUT_JSON, output_report: Path = OUTPUT_REPORT) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_report.parent.mkdir(parents=True, exist_ok=True)
    output_report.write_text(_format_report(result), encoding="utf-8")


def _validate_input(diagnostic: dict[str, Any]) -> None:
    if diagnostic.get("status") != REQUIRED_STATUS:
        raise ValueError(f"H-G1 side-aware diagnostic must have status {REQUIRED_STATUS!r}")
    if diagnostic.get("policy_version") != REQUIRED_POLICY_ID:
        raise ValueError(f"H-G1 side-aware diagnostic must use policy {REQUIRED_POLICY_ID!r}")
    if diagnostic.get("strategy_use_allowed") is not False:
        raise ValueError("H-G1 side-aware diagnostic must keep strategy_use_allowed=false")
    for flag in ("network_used", "paid_data_used", "strategy_pnl_used"):
        if diagnostic.get(flag) is not False:
            raise ValueError(f"H-G1 side-aware diagnostic must keep {flag}=false")
    required_gate_statuses = {
        "coverage": diagnostic["validation_gates"]["coverage"]["status"],
        "timestamp_discipline": diagnostic["validation_gates"]["timestamp_discipline"]["status"],
        "stability": diagnostic["validation_gates"]["stability"]["status"],
        "economic_sign": diagnostic["validation_gates"]["economic_sign"]["status"],
        "search_log": diagnostic["validation_gates"]["search_log"]["status"],
    }
    failed = {name: status for name, status in required_gate_statuses.items() if status != "pass"}
    if failed:
        raise ValueError(f"H-G1 side-aware diagnostic has non-pass gates: {failed}")


def _blocker(
    blocker_id: str,
    category: str,
    severity: str,
    status: str,
    why: str,
    required_evidence: list[str],
    next_action: str,
) -> dict[str, Any]:
    return {
        "blocker_id": blocker_id,
        "category": category,
        "severity": severity,
        "status": status,
        "why_it_blocks_acceptance": why,
        "required_evidence_to_clear": required_evidence,
        "next_action": next_action,
    }


def _summarize_blockers(blockers: list[dict[str, Any]]) -> dict[str, Any]:
    hard = [item["blocker_id"] for item in blockers if item["severity"] == "hard_blocker"]
    soft = [item["blocker_id"] for item in blockers if item["severity"] == "soft_blocker"]
    return {
        "total_blockers": len(blockers),
        "hard_blocker_count": len(hard),
        "soft_blocker_count": len(soft),
        "hard_blockers": hard,
        "soft_blockers": soft,
        "strategy_use_allowed": False,
    }


def _format_report(result: dict[str, Any]) -> str:
    facts = result["passed_data_validity_facts"]
    summary = result["blocker_summary"]
    lines = [
        "# H-G1 Acceptance Blocker Review",
        "",
        f"- Status: `{result['status']}`",
        f"- Conclusion: `{result['conclusion']}`",
        f"- Evidence tier: `{result['evidence_tier']}`",
        f"- Source diagnostic: `{result['source_diagnostic']}`",
        f"- Network used: `{result['network_used']}`",
        f"- Paid data used: `{result['paid_data_used']}`",
        f"- Strategy PnL used: `{result['strategy_pnl_used']}`",
        f"- Strategy use allowed: `{result['strategy_use_allowed']}`",
        f"- Paper trading allowed: `{result['paper_trading_allowed']}`",
        "",
        "## Data-Validity Facts That Passed",
        "",
        "| Fact | Value |",
        "|:--|--:|",
        f"| Diagnostic status | `{facts['diagnostic_status']}` |",
        f"| Policy id | `{facts['policy_id']}` |",
        f"| Dates | {facts['date_count']} |",
        f"| Quote rows | {facts['quote_count']} |",
        f"| Computed Greeks rows | {facts['computed_greeks_count']} |",
        f"| Raw computed Greeks rate | {facts['raw_computed_greeks_rate']} |",
        f"| Side-aware required-bucket OI-notional share | {facts['side_aware_required_bucket_oi_notional_share']} |",
        f"| Retained abs gamma proxy share | {facts['retained_abs_gamma_proxy_share']} |",
        f"| Economic-sign correlation | {facts['economic_sign_correlation']} |",
        f"| Economic-sign observations | {facts['economic_sign_observation_count']} |",
        "",
        "## Blocker Summary",
        "",
        f"- Total blockers: `{summary['total_blockers']}`",
        f"- Hard blockers: `{summary['hard_blocker_count']}`",
        f"- Soft blockers: `{summary['soft_blocker_count']}`",
        "",
        "| Blocker | Category | Severity | Status |",
        "|:--|:--|:--|:--|",
    ]
    for blocker in result["acceptance_blockers"]:
        lines.append(
            f"| `{blocker['blocker_id']}` | `{blocker['category']}` | `{blocker['severity']}` | `{blocker['status']}` |"
        )
    lines.extend(["", "## Required Evidence To Clear", ""])
    for blocker in result["acceptance_blockers"]:
        lines.extend([
            f"### {blocker['blocker_id']}",
            "",
            blocker["why_it_blocks_acceptance"],
            "",
            "Required evidence:",
        ])
        lines.extend(f"- {item}" for item in blocker["required_evidence_to_clear"])
        lines.extend(["", f"Next action: {blocker['next_action']}", ""])
    lines.extend(["## Forbidden Claims Preserved", ""])
    lines.extend(f"- {item}" for item in result["forbidden_claims_preserved"])
    lines.extend(["", "## References", ""])
    lines.extend(f"- `{item}`" for item in result["references"])
    lines.append("")
    return "\n".join(lines)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run H-G1 strategy-independent acceptance blocker review.")
    parser.add_argument("--input", type=Path, default=H_G1_SIDE_AWARE_DIAGNOSTIC)
    parser.add_argument("--output-json", type=Path, default=OUTPUT_JSON)
    parser.add_argument("--output-report", type=Path, default=OUTPUT_REPORT)
    args = parser.parse_args(argv)

    result = run_review(args.input)
    write_outputs(result, args.output_json, args.output_report)
    print(json.dumps({
        "status": result["status"],
        "hard_blocker_count": result["blocker_summary"]["hard_blocker_count"],
        "strategy_use_allowed": result["strategy_use_allowed"],
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
