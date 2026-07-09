from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAN_PATH = PROJECT_ROOT / "experiments" / "h_g1_sample_expansion_plan.json"
DEFAULT_POST_ABLATION_PATH = PROJECT_ROOT / "experiments" / "h_g1_post_ablation_decision.json"
DEFAULT_ABLATION_SUMMARY_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_g1_gamma_strategy_ablation_summary.json"


def validate_h_g1_sample_expansion_plan(
    plan_path: Path = DEFAULT_PLAN_PATH,
    post_ablation_path: Path = DEFAULT_POST_ABLATION_PATH,
    ablation_summary_path: Path = DEFAULT_ABLATION_SUMMARY_PATH,
) -> dict[str, Any]:
    blockers: list[str] = []
    plan = _load_json(plan_path)
    post_ablation = _load_json(post_ablation_path)
    ablation = _load_json(ablation_summary_path)

    if plan.get("schema_version") != "h_g1_sample_expansion_plan_v1":
        blockers.append("unsupported_schema_version")
    if plan.get("hypothesis_id") != "H-G1":
        blockers.append("hypothesis_id_must_be_h_g1")
    if plan.get("evidence_tier") != "E0":
        blockers.append("evidence_tier_must_be_e0")
    if plan.get("status") != "plan_complete":
        blockers.append("status_must_be_plan_complete")
    if plan.get("decision") != "keep_h_g1_parked_with_preregistered_sample_expansion_requirements":
        blockers.append("decision_must_keep_h_g1_parked")

    false_flags = [
        "network_used",
        "paid_data_used",
        "new_data_requested",
        "strategy_pnl_used",
        "strategy_use_allowed",
        "paper_trading_allowed",
        "paid_data_approved",
        "true_net_gamma_claim_allowed",
        "research_log_required",
    ]
    for field in false_flags:
        if plan.get(field) is not False:
            blockers.append(f"{field}_must_be_false")

    if post_ablation.get("decision") != "park_h_g1_pending_sample_expansion_plan":
        blockers.append("source_post_ablation_must_park_h_g1")
    if ablation.get("status") != "complete_underpowered":
        blockers.append("source_ablation_must_be_complete_underpowered")
    if ablation.get("strategy_use_allowed") is not False:
        blockers.append("source_ablation_strategy_use_must_be_forbidden")
    coverage = ablation.get("coverage", {})
    if coverage.get("intersection_closed_trade_count") != 2:
        blockers.append("source_intersection_trade_count_must_be_2")

    steps = plan.get("sample_expansion_sequence", [])
    required_steps = {
        "h_g1_24_a": "no_paid_local_cache_overlap_scan",
        "h_g1_24_b": "mintrl_psr_feasibility_gate",
        "h_g1_24_c": "targeted_cost_gate_only_if_overlap_scan_passes",
        "h_g1_24_d": "new_preregistered_ablation_only_after_data_validity",
    }
    step_map = {item.get("step_id"): item for item in steps if isinstance(item, dict)}
    for step_id, expected_name in required_steps.items():
        step = step_map.get(step_id)
        if not step:
            blockers.append(f"missing_step:{step_id}")
            continue
        if step.get("name") != expected_name:
            blockers.append(f"step_name_mismatch:{step_id}")
        if not step.get("purpose"):
            blockers.append(f"step_purpose_missing:{step_id}")
        if not step.get("verification"):
            blockers.append(f"step_verification_missing:{step_id}")

    first_two = [step_map.get("h_g1_24_a", {}), step_map.get("h_g1_24_b", {})]
    for step in first_two:
        if step.get("network_allowed") is not False:
            blockers.append(f"{step.get('step_id')}_network_must_be_false")
        if step.get("paid_data_allowed") is not False:
            blockers.append(f"{step.get('step_id')}_paid_data_must_be_false")

    cost_policy = plan.get("cost_policy", {})
    if cost_policy.get("broad_calendar_buying_allowed") is not False:
        blockers.append("broad_calendar_buying_must_be_forbidden")
    if cost_policy.get("new_provider_requires_user_approval") is not True:
        blockers.append("new_provider_must_require_user_approval")
    if cost_policy.get("metadata_cost_check_required_before_download") is not True:
        blockers.append("metadata_cost_check_must_be_required")
    if cost_policy.get("paid_download_allowed_by_this_artifact") is not False:
        blockers.append("paid_download_must_not_be_allowed_by_plan")

    requirements = plan.get("minimum_evidence_requirements", {})
    sample_size_rule = requirements.get("sample_size_rule", "")
    if "No fixed N" not in sample_size_rule or "MinTRL/PSR" not in sample_size_rule:
        blockers.append("sample_size_rule_must_reject_fixed_n_and_require_mintrl_psr")
    if len(requirements.get("required_regime_coverage", [])) < 5:
        blockers.append("required_regime_coverage_too_sparse")
    if len(requirements.get("required_reporting", [])) < 6:
        blockers.append("required_reporting_too_sparse")

    forbidden_text = "\n".join(plan.get("forbidden_actions", []))
    for phrase in [
        "Do not use H-G1 as a trading filter",
        "Do not approve paper trading",
        "Do not buy paid data",
        "Do not claim true market-maker net gamma",
        "Do not buy broad calendar data",
    ]:
        if phrase not in forbidden_text:
            blockers.append(f"missing_forbidden_action:{phrase}")

    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "plan_path": _relative(plan_path),
        "post_ablation_path": _relative(post_ablation_path),
        "ablation_summary_path": _relative(ablation_summary_path),
        "decision": plan.get("decision"),
        "selected_next_safe_action": plan.get("selected_next_safe_action"),
        "step_count": len(steps) if isinstance(steps, list) else None,
        "source_intersection_closed_trade_count": coverage.get("intersection_closed_trade_count"),
        "paid_download_allowed_by_this_artifact": cost_policy.get("paid_download_allowed_by_this_artifact"),
    }


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the H-G1 sample-expansion planning artifact.")
    parser.add_argument("--plan-path", type=Path, default=DEFAULT_PLAN_PATH)
    parser.add_argument("--post-ablation-path", type=Path, default=DEFAULT_POST_ABLATION_PATH)
    parser.add_argument("--ablation-summary-path", type=Path, default=DEFAULT_ABLATION_SUMMARY_PATH)
    args = parser.parse_args(argv)

    result = validate_h_g1_sample_expansion_plan(args.plan_path, args.post_ablation_path, args.ablation_summary_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
