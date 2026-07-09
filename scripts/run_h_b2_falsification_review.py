from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import mean, pstdev
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUMMARY_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_b2_subsystem_b_scale_summary.json"
DEFAULT_OUTPUT_JSON = PROJECT_ROOT / "reports" / "experiments" / "h_b2_falsification_review.json"
DEFAULT_OUTPUT_MD = PROJECT_ROOT / "reports" / "experiments" / "h_b2_falsification_review.md"


def run_review(summary_path: Path = DEFAULT_SUMMARY_PATH) -> dict[str, Any]:
    source = _read_json(summary_path)
    scenarios = [_scenario_review(item) for item in source["scenarios"]]

    positive_total_and_oos = [
        item["scenario_id"]
        for item in scenarios
        if item["total_implementable_pnl"] > 0 and item["oos_implementable_pnl"] > 0
    ]
    active_trade_scenarios = [item for item in scenarios if item["trade_count"] > 0]
    strong_negative_psr = [
        item["scenario_id"]
        for item in active_trade_scenarios
        if item["psr_probability_sharpe_gt_0"] is not None and item["psr_probability_sharpe_gt_0"] <= 0.05
    ]
    underpowered = [
        item["scenario_id"]
        for item in scenarios
        if "underpowered" in item["sample_labels"] or "under-sampled" in item["sample_labels"]
    ]
    current_grid_failed = not positive_total_and_oos
    acceptance_grade_falsified = current_grid_failed and len(strong_negative_psr) == len(active_trade_scenarios) and not underpowered

    result = {
        "record_type": "h_b2_falsification_review",
        "schema_version": "h_b2_falsification_review_v1",
        "hypothesis_id": "H-B2",
        "source_summary": _relative(summary_path),
        "source_experiment_status": source.get("status"),
        "source_evidence_tier": source.get("evidence_tier"),
        "evidence_tier": "E1",
        "status": "review_complete",
        "conclusion": "ไม่ผ่าน",
        "decision": "keep_h_b2_parked_current_grid_not_resurrected",
        "current_grid_failed_preregistered_keep_active_rule": current_grid_failed,
        "acceptance_grade_falsified": acceptance_grade_falsified,
        "positive_total_and_oos_scenarios": positive_total_and_oos,
        "active_trade_scenario_count": len(active_trade_scenarios),
        "strong_negative_psr_scenarios": strong_negative_psr,
        "underpowered_scenarios": underpowered,
        "scenario_reviews": scenarios,
        "network_used": False,
        "paid_data_used": False,
        "ibkr_requested": False,
        "llm_called": False,
        "new_strategy_pnl_run": False,
        "paper_trading_allowed": False,
        "operational_validation_allowed": False,
        "real_money_allowed": False,
        "allowed_next_action": "do_not_spend_more_h_b2_work_without_new_mechanism_or_user_directed_revision",
        "forbidden_actions": [
            "Do not use H-B2 current grid for paper trading.",
            "Do not claim Sub-System B is deployable from this review.",
            "Do not buy new data for H-B2 from this review alone.",
            "Do not delete Sub-System B from project scope solely because this grid failed.",
        ],
        "tier_blockers": [
            "E1 falsification review only",
            "No E2 acceptance-grade validation",
            "Some scenarios remain under-sampled or underpowered",
            "Grid search remains diagnostic and cannot support deployment selection",
            "Current grid failure does not falsify all possible Sub-System B mechanisms",
        ],
        "references": [
            "wiki/concepts/minimum-track-record-length.md",
            "wiki/concepts/probabilistic-sharpe-ratio.md",
            "reports/experiments/h_b2_subsystem_b_scale_summary.json",
            "experiments/h_b2_subsystem_b_scale_preregistration.json",
        ],
        "research_log_required": True,
        "research_log_slug": "higanbana-h-b2-falsification-review",
        "research_log_path": "research_log/023-higanbana-h-b2-falsification-review.md",
    }
    return result


def write_outputs(result: dict[str, Any], output_json: Path = DEFAULT_OUTPUT_JSON, output_md: Path = DEFAULT_OUTPUT_MD) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(_format_report(result), encoding="utf-8")


def _scenario_review(scenario: dict[str, Any]) -> dict[str, Any]:
    metrics = scenario["metrics"]
    oos_metrics = scenario["splits"]["oos"]["metrics"]
    returns = [float(row["return_on_starting_equity"]) for row in scenario.get("daily_pnl", [])]
    sample = scenario["sample_adequacy"]
    psr = _psr_probability_sharpe_gt_null(returns, null_sharpe=0.0)
    return {
        "scenario_id": scenario["scenario_id"],
        "account_size_usd": scenario["account_size_usd"],
        "protective_wing_gap_usd": scenario["protective_wing_gap_usd"],
        "trade_count": metrics["trade_count"],
        "oos_trade_count": oos_metrics["trade_count"],
        "total_mid_pnl": metrics["total_mid_pnl"],
        "total_implementable_pnl": metrics["total_implementable_pnl"],
        "oos_implementable_pnl": oos_metrics["total_implementable_pnl"],
        "friction_drag_ratio": metrics["friction_drag_ratio"],
        "sharpe_proxy": metrics["sharpe_proxy"],
        "psr_probability_sharpe_gt_0": psr["probability"],
        "psr_status": psr["status"],
        "return_skewness": psr["skewness"],
        "return_kurtosis": psr["kurtosis"],
        "return_autocorrelation_lag1": psr["autocorrelation_lag1"],
        "sample_labels": sample.get("labels", []),
        "mintrl_status": sample.get("mintrl_status"),
        "big_day_dependency_status": scenario["big_day_dependency"]["status"],
        "passes_keep_active_rule": metrics["total_implementable_pnl"] > 0 and oos_metrics["total_implementable_pnl"] > 0,
    }


def _psr_probability_sharpe_gt_null(returns: list[float], null_sharpe: float) -> dict[str, Any]:
    if len(returns) < 2:
        return _empty_psr("insufficient_observations")
    sigma = pstdev(returns)
    if sigma == 0:
        return _empty_psr("zero_variance")
    observed = mean(returns) / sigma
    skewness = _skewness(returns)
    kurtosis = _kurtosis(returns)
    autocorr = _autocorr_lag1(returns)
    denominator = 1.0 - skewness * observed + ((kurtosis - 1.0) / 4.0) * observed * observed
    if denominator <= 0:
        return _empty_psr("invalid_generalized_variance")
    z_score = (observed - null_sharpe) * math.sqrt(len(returns) - 1) / math.sqrt(denominator)
    probability = _normal_cdf(z_score)
    return {
        "status": "computed",
        "probability": round(probability, 6),
        "observed_sharpe": round(observed, 6),
        "skewness": round(skewness, 6),
        "kurtosis": round(kurtosis, 6),
        "autocorrelation_lag1": None if autocorr is None else round(autocorr, 6),
        "null_sharpe": null_sharpe,
    }


def _empty_psr(status: str) -> dict[str, Any]:
    return {
        "status": status,
        "probability": None,
        "observed_sharpe": None,
        "skewness": None,
        "kurtosis": None,
        "autocorrelation_lag1": None,
        "null_sharpe": 0.0,
    }


def _skewness(values: list[float]) -> float:
    mu = mean(values)
    sigma = pstdev(values)
    if sigma == 0:
        return 0.0
    return sum(((value - mu) / sigma) ** 3 for value in values) / len(values)


def _kurtosis(values: list[float]) -> float:
    mu = mean(values)
    sigma = pstdev(values)
    if sigma == 0:
        return 0.0
    return sum(((value - mu) / sigma) ** 4 for value in values) / len(values)


def _autocorr_lag1(values: list[float]) -> float | None:
    if len(values) < 3:
        return None
    head = values[:-1]
    tail = values[1:]
    mu_head = mean(head)
    mu_tail = mean(tail)
    denom = math.sqrt(sum((value - mu_head) ** 2 for value in head) * sum((value - mu_tail) ** 2 for value in tail))
    if denom == 0:
        return None
    return sum((left - mu_head) * (right - mu_tail) for left, right in zip(head, tail)) / denom


def _normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def _format_report(result: dict[str, Any]) -> str:
    lines = [
        "# H-B2 Falsification Review",
        "",
        f"- Status: `{result['status']}`",
        f"- Conclusion: `{result['conclusion']}`",
        f"- Decision: `{result['decision']}`",
        f"- Evidence tier: `{result['evidence_tier']}`",
        f"- Source summary: `{result['source_summary']}`",
        f"- Current grid failed keep-active rule: `{result['current_grid_failed_preregistered_keep_active_rule']}`",
        f"- Acceptance-grade falsified: `{result['acceptance_grade_falsified']}`",
        f"- Network used: `{result['network_used']}`",
        f"- Paid data used: `{result['paid_data_used']}`",
        f"- LLM called: `{result['llm_called']}`",
        f"- Paper trading allowed: `{result['paper_trading_allowed']}`",
        "",
        "## Scenario Review",
        "",
        "| Scenario | Trades | Total impl PnL | OOS impl PnL | Sharpe proxy | PSR(SR>0) | Labels | Big-day |",
        "|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for item in result["scenario_reviews"]:
        labels = ", ".join(item["sample_labels"]) if item["sample_labels"] else "-"
        psr = "-" if item["psr_probability_sharpe_gt_0"] is None else f"{item['psr_probability_sharpe_gt_0']:.6f}"
        sharpe = "-" if item["sharpe_proxy"] is None else f"{item['sharpe_proxy']:.6f}"
        lines.append(
            "| {scenario_id} | {trade_count} | {total:.2f} | {oos:.2f} | {sharpe} | {psr} | {labels} | {big} |".format(
                scenario_id=item["scenario_id"],
                trade_count=item["trade_count"],
                total=item["total_implementable_pnl"],
                oos=item["oos_implementable_pnl"],
                sharpe=sharpe,
                psr=psr,
                labels=labels,
                big=item["big_day_dependency_status"],
            )
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "The current H-B2 grid fails the pre-registered keep-active rule because no scenario has both positive total implementable PnL and positive OOS implementable PnL.",
            "This review keeps H-B2 parked rather than deleting Sub-System B from scope: the current grid/mechanism failed, but other Sub-System B mechanisms require a separate revised hypothesis.",
            "",
            "## Forbidden Actions",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in result["forbidden_actions"])
    lines.extend(["", "## Tier Blockers", ""])
    lines.extend(f"- {item}" for item in result["tier_blockers"])
    return "\n".join(lines) + "\n"


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the H-B2 falsification review from the existing scale diagnostic.")
    parser.add_argument("--summary-path", type=Path, default=DEFAULT_SUMMARY_PATH)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    args = parser.parse_args(argv)

    result = run_review(args.summary_path)
    write_outputs(result, args.output_json, args.output_md)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
