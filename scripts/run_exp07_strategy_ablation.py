from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAN_PATH = PROJECT_ROOT / "tests" / "fixtures" / "exp07_strategy_ablation_plan_v1.json"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "reports" / "experiments" / "exp07_strategy_ablation_status.json"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "reports" / "experiments" / "exp07_strategy_ablation_status.md"
DEFAULT_STRATEGY_DATA_AUDIT_PATH = PROJECT_ROOT / "reports" / "strategy_data_readiness_audit.json"


def load_plan(path: Path = DEFAULT_PLAN_PATH) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def load_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def evaluate_ablation_readiness(
    plan: dict[str, Any],
    strategy_data_audit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data_requirements = plan["data_requirements"]
    blockers = list(plan.get("blocked_until", []))
    strategy_totals = (strategy_data_audit or {}).get("totals", {})
    closed_trades = int(strategy_totals.get("closed_trades", 0))
    quote_rows = int(strategy_totals.get("quote_rows", 0))
    minimum_trade_count = int(data_requirements.get("minimum_trade_count", 0))

    if data_requirements.get("requires_bid_ask_quotes") is True and quote_rows <= 0:
        blockers.append("requires_bid_ask_quotes")
    if closed_trades < minimum_trade_count:
        blockers.append("requires_minimum_trade_count_500")

    variants = [
        {
            "variant_id": variant["variant_id"],
            "status": "blocked",
            "can_block_trade": bool(variant["can_block_trade"]),
            "uses_raw_llm_gate": bool(variant["uses_raw_llm_gate"]),
            "uses_guarded_policy": bool(variant["uses_guarded_policy"]),
        }
        for variant in plan["policy_variants"]
    ]
    return {
        "plan_version": plan["plan_version"],
        "experiment_id": plan["experiment_id"],
        "status": "blocked" if blockers else "ready",
        "reason": "Real strategy ablation is blocked until required data archives and sample size exist.",
        "blockers": sorted(set(blockers)),
        "variant_count": len(variants),
        "variants": variants,
        "required_metrics": plan["required_metrics"],
        "split_policy": plan["split_policy"],
        "acceptance_rules": plan["acceptance_rules"],
        "strategy_data_evidence": {
            "closed_trades": closed_trades,
            "minimum_trade_count": minimum_trade_count,
            "quote_rows": quote_rows,
            "source": str(DEFAULT_STRATEGY_DATA_AUDIT_PATH) if strategy_data_audit is not None else None,
        },
    }


def write_markdown_report(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# Exp07 Strategy Ablation Status",
        "",
        f"- Plan version: `{result['plan_version']}`",
        f"- Experiment id: `{result['experiment_id']}`",
        f"- Status: `{result['status']}`",
        f"- Reason: {result['reason']}",
        "",
        "## Variants",
        "",
        "| Variant | Status | Can Block Trade | Raw LLM Gate | Guarded Policy |",
        "|:--|:--|:--:|:--:|:--:|",
    ]
    for variant in result["variants"]:
        lines.append(
            "| {variant_id} | `{status}` | {can_block_trade} | {uses_raw_llm_gate} | {uses_guarded_policy} |".format(
                **variant
            )
        )
    lines.extend(["", "## Blockers", ""])
    for blocker in result["blockers"]:
        lines.append(f"- `{blocker}`")
    evidence = result["strategy_data_evidence"]
    lines.extend(
        [
            "",
            "## Strategy Data Evidence",
            "",
            f"- Closed trades: {evidence['closed_trades']} / {evidence['minimum_trade_count']}",
            f"- Quote rows: {evidence['quote_rows']}",
        ]
    )
    lines.extend(["", "## Required Metrics", ""])
    for metric in result["required_metrics"]:
        lines.append(f"- `{metric}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Exp07 strategy ablation readiness gate.")
    parser.add_argument("--plan-path", type=Path, default=DEFAULT_PLAN_PATH)
    parser.add_argument("--output-path", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--strategy-data-audit-path", type=Path, default=DEFAULT_STRATEGY_DATA_AUDIT_PATH)
    args = parser.parse_args(argv)

    plan = load_plan(args.plan_path)
    strategy_data_audit = load_optional_json(args.strategy_data_audit_path)
    result = evaluate_ablation_readiness(plan, strategy_data_audit=strategy_data_audit)
    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    args.output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown_report(args.report_path, result)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
