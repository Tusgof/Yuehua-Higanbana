from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAN_PATH = PROJECT_ROOT / "tests" / "fixtures" / "exp07_strategy_ablation_plan_v1.json"

REQUIRED_VARIANTS = {"baseline_quant_only", "guarded_policy_gate", "raw_llm_observation_only"}
REQUIRED_METRICS = {
    "trade_count",
    "skip_rate",
    "total_net_pnl",
    "sharpe",
    "sortino",
    "max_drawdown",
    "es95",
    "es99",
    "worst_day_loss",
    "win_rate",
    "payoff_ratio",
    "cost_drag",
    "benchmark_return",
}
REQUIRED_BLOCKERS = {
    "requires_wider_spy_0dte_data",
    "requires_real_news_archive",
}


def load_plan(path: Path = DEFAULT_PLAN_PATH) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def validate_plan(path: Path = DEFAULT_PLAN_PATH) -> list[str]:
    plan = load_plan(path)
    errors: list[str] = []

    if plan.get("plan_version") != "exp07-strategy-ablation-v1":
        errors.append("plan_version must be exp07-strategy-ablation-v1")
    if plan.get("experiment_id") != "exp07_cost_latency":
        errors.append("experiment_id must be exp07_cost_latency")

    data_requirements = plan.get("data_requirements", {})
    if int(data_requirements.get("minimum_trade_count", 0)) < 500:
        errors.append("minimum_trade_count must be at least 500")
    for required_flag in ("requires_wider_spy_0dte_data", "requires_real_news_archive", "requires_real_macro_calendar_archive", "requires_bid_ask_quotes"):
        if data_requirements.get(required_flag) is not True:
            errors.append(f"data_requirements.{required_flag} must be true")

    split_policy = plan.get("split_policy", {})
    if split_policy.get("parameters_locked_before_oos") is not True:
        errors.append("split_policy.parameters_locked_before_oos must be true")
    if split_policy.get("forbid_oos_tuning") is not True:
        errors.append("split_policy.forbid_oos_tuning must be true")

    variants = plan.get("policy_variants", [])
    if not isinstance(variants, list) or not variants:
        errors.append("policy_variants must be a non-empty list")
        variants = []
    variant_ids = [variant.get("variant_id") for variant in variants if isinstance(variant, dict)]
    missing_variants = sorted(REQUIRED_VARIANTS.difference(variant_ids))
    if missing_variants:
        errors.append(f"missing policy variants: {missing_variants}")
    duplicate_variants = sorted({variant_id for variant_id in variant_ids if variant_ids.count(variant_id) > 1})
    if duplicate_variants:
        errors.append(f"duplicate policy variants: {duplicate_variants}")

    variant_by_id = {variant.get("variant_id"): variant for variant in variants if isinstance(variant, dict)}
    raw_variant = variant_by_id.get("raw_llm_observation_only", {})
    if raw_variant.get("can_block_trade") is not False:
        errors.append("raw_llm_observation_only cannot block trades")
    guarded_variant = variant_by_id.get("guarded_policy_gate", {})
    if guarded_variant.get("uses_guarded_policy") is not True or guarded_variant.get("can_block_trade") is not True:
        errors.append("guarded_policy_gate must use guarded policy and be able to block trades")
    baseline_variant = variant_by_id.get("baseline_quant_only", {})
    if baseline_variant.get("uses_raw_llm_gate") or baseline_variant.get("uses_guarded_policy") or baseline_variant.get("can_block_trade"):
        errors.append("baseline_quant_only must not use LLM/guarded policy gates")

    metrics = plan.get("required_metrics", [])
    missing_metrics = sorted(REQUIRED_METRICS.difference(metrics if isinstance(metrics, list) else []))
    if missing_metrics:
        errors.append(f"missing required metrics: {missing_metrics}")

    acceptance_rules = plan.get("acceptance_rules", {})
    for rule in (
        "guarded_policy_must_not_reduce_trade_count_below_minimum",
        "guarded_policy_must_improve_es99_or_worst_day_loss",
        "guarded_policy_must_not_reduce_oos_sharpe_below_baseline",
        "raw_llm_variant_cannot_be_used_as_gate",
    ):
        if acceptance_rules.get(rule) is not True:
            errors.append(f"acceptance_rules.{rule} must be true")

    blockers = plan.get("blocked_until", [])
    missing_blockers = sorted(REQUIRED_BLOCKERS.difference(blockers if isinstance(blockers, list) else []))
    if missing_blockers:
        errors.append(f"missing blocked_until entries: {missing_blockers}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Exp07 guarded-policy strategy ablation plan.")
    parser.add_argument("--path", type=Path, default=DEFAULT_PLAN_PATH)
    args = parser.parse_args()
    errors = validate_plan(args.path)
    if errors:
        for error in errors:
            print(error)
        return 1
    print(f"validated Exp07 strategy ablation plan from {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
