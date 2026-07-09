from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DECISION_PATH = PROJECT_ROOT / "experiments" / "h_g1_post_ablation_decision.json"
DEFAULT_ABLATION_SUMMARY_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_g1_gamma_strategy_ablation_summary.json"


def validate_h_g1_post_ablation_decision(
    decision_path: Path = DEFAULT_DECISION_PATH,
    ablation_summary_path: Path = DEFAULT_ABLATION_SUMMARY_PATH,
) -> dict[str, Any]:
    blockers: list[str] = []
    decision = _load_json(decision_path)
    ablation = _load_json(ablation_summary_path)

    if decision.get("schema_version") != "h_g1_post_ablation_decision_v1":
        blockers.append("unsupported_schema_version")
    if decision.get("hypothesis_id") != "H-G1":
        blockers.append("hypothesis_id_must_be_h_g1")
    if decision.get("evidence_tier") != "E1":
        blockers.append("evidence_tier_must_be_e1")
    if decision.get("status") != "decision_complete":
        blockers.append("status_must_be_decision_complete")
    if decision.get("decision") != "park_h_g1_pending_sample_expansion_plan":
        blockers.append("decision_must_park_h_g1_pending_sample_expansion_plan")
    if decision.get("selected_next_safe_action") != "return_to_news_unblock_n7":
        blockers.append("next_safe_action_must_return_to_news_unblock_n7")

    false_flags = [
        "network_used",
        "paid_data_used",
        "new_data_requested",
        "new_strategy_pnl_used",
        "strategy_use_allowed",
        "paper_trading_allowed",
        "paid_data_allowed_from_h_g1_22",
        "true_net_gamma_claim_allowed",
        "research_log_required",
    ]
    for field in false_flags:
        if decision.get(field) is not False:
            blockers.append(f"{field}_must_be_false")

    if decision.get("source_strategy_ablation_summary") != "reports/experiments/h_g1_gamma_strategy_ablation_summary.json":
        blockers.append("source_strategy_ablation_summary_mismatch")
    if ablation.get("status") != "complete_underpowered":
        blockers.append("source_ablation_must_be_complete_underpowered")
    if ablation.get("hypothesis_id") != "H-G1":
        blockers.append("source_ablation_must_reference_h_g1")
    if ablation.get("strategy_use_allowed") is not False:
        blockers.append("source_ablation_strategy_use_must_be_forbidden")
    if ablation.get("paper_trading_allowed") is not False:
        blockers.append("source_ablation_paper_trading_must_be_forbidden")

    coverage = ablation.get("coverage", {})
    if coverage.get("baseline_closed_trade_count") != 90:
        blockers.append("source_ablation_baseline_closed_trade_count_must_be_90")
    if coverage.get("intersection_closed_trade_count") != 2:
        blockers.append("source_ablation_intersection_closed_trade_count_must_be_2")

    active_by_filter = ablation.get("active_trade_count_by_filter", {})
    gamma_variants = [
        "positive_gamma_proxy_only",
        "skip_extreme_negative_gamma_proxy_days",
        "skip_negative_gamma_proxy_days",
    ]
    for variant in gamma_variants:
        if active_by_filter.get(variant) != 0:
            blockers.append(f"{variant}_active_trade_count_must_be_zero")

    required_blockers = {
        "intersection_sample_too_small",
        "under-sampled",
        "underpowered",
        "no_e2_acceptance",
        "signed_oi_gamma_proxy_is_not_true_market_maker_net_gamma",
    }
    tier_blockers = set(decision.get("tier_blockers", []))
    for blocker in sorted(required_blockers - tier_blockers):
        blockers.append(f"missing_tier_blocker:{blocker}")

    required_phrases = [
        "Do not use H-G1 as a trading filter",
        "Do not approve paper trading",
        "Do not buy paid data",
        "Do not claim true market-maker net gamma",
    ]
    forbidden_text = "\n".join(decision.get("forbidden_actions", []))
    for phrase in required_phrases:
        if phrase not in forbidden_text:
            blockers.append(f"missing_forbidden_action:{phrase}")

    reopen_conditions = decision.get("reopen_conditions", [])
    if not isinstance(reopen_conditions, list) or len(reopen_conditions) < 3:
        blockers.append("requires_explicit_reopen_conditions")

    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "decision_path": _relative(decision_path),
        "ablation_summary_path": _relative(ablation_summary_path),
        "decision": decision.get("decision"),
        "selected_next_safe_action": decision.get("selected_next_safe_action"),
        "source_ablation_status": ablation.get("status"),
        "source_intersection_closed_trade_count": coverage.get("intersection_closed_trade_count"),
    }


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the H-G1 post-ablation decision artifact.")
    parser.add_argument("--decision-path", type=Path, default=DEFAULT_DECISION_PATH)
    parser.add_argument("--ablation-summary-path", type=Path, default=DEFAULT_ABLATION_SUMMARY_PATH)
    args = parser.parse_args(argv)

    result = validate_h_g1_post_ablation_decision(args.decision_path, args.ablation_summary_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
