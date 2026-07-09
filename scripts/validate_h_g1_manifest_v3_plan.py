from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAN_PATH = PROJECT_ROOT / "experiments" / "h_g1_gamma_regime_date_set_preregistration_v3_plan.json"
REQUIRED_SCHEMA_VERSION = "h_g1_gamma_regime_date_set_preregistration_v3_plan"


def validate_h_g1_manifest_v3_plan(plan_path: Path = DEFAULT_PLAN_PATH) -> dict[str, Any]:
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    blockers: list[str] = []

    if plan.get("schema_version") != REQUIRED_SCHEMA_VERSION:
        blockers.append(f"unsupported_schema_version:{plan.get('schema_version')}")
    if plan.get("hypothesis_id") != "H-G1":
        blockers.append(f"unexpected_hypothesis_id:{plan.get('hypothesis_id')}")
    if plan.get("status") != "plan_only_no_paid_data":
        blockers.append(f"unexpected_status:{plan.get('status')}")
    if plan.get("source_decision") != "reports/diagnostics/h_g1_policy_manifest_decision.json":
        blockers.append("source_decision_not_locked_to_h_g1_9")
    if plan.get("policy_review_artifact") != "docs/H_G1_POLICY_V2_1_REVIEW.md":
        blockers.append("policy_review_artifact_not_locked")

    data_policy = plan.get("data_policy", {})
    if data_policy.get("symbol_universe") != ["SPY"]:
        blockers.append(f"symbol_universe_not_spy_only:{data_policy.get('symbol_universe')}")
    if data_policy.get("network_used_to_create_plan") is not False:
        blockers.append("network_used_to_create_plan_not_false")
    if data_policy.get("paid_data_used_to_create_plan") is not False:
        blockers.append("paid_data_used_to_create_plan_not_false")
    if data_policy.get("paid_action_before_concrete_manifest_validation") != "forbidden":
        blockers.append("paid_action_before_concrete_manifest_validation_not_forbidden")
    if data_policy.get("broad_calendar_purchase") != "forbidden":
        blockers.append("broad_calendar_purchase_not_forbidden")
    if data_policy.get("requires_metadata_cost_check_before_download") is not True:
        blockers.append("metadata_cost_check_not_required")

    blocked_bucket = plan.get("blocked_bucket_to_repair", {})
    if blocked_bucket.get("date") != "2023-07-12":
        blockers.append(f"unexpected_blocked_bucket_date:{blocked_bucket.get('date')}")
    if blocked_bucket.get("bucket") != "otm_put":
        blockers.append(f"unexpected_blocked_bucket:{blocked_bucket.get('bucket')}")
    if blocked_bucket.get("replacement_required") is not True:
        blockers.append("replacement_required_not_true")
    _require_at_least(blockers, "blocked_bucket_notional_floor", blocked_bucket.get("minimum_required_computed_oi_notional_share"), 0.8)
    _require_below(blockers, "blocked_bucket_computed_oi_notional_share", blocked_bucket.get("computed_oi_notional_share"), 0.8)

    replacement = plan.get("replacement_objective", {})
    expected_replacement = {
        "remove_date": "2023-07-12",
        "replacement_count": 1,
        "target_split": "in_sample",
        "target_volatility_bucket": "low",
        "target_high_importance_macro": True,
    }
    for key, expected in expected_replacement.items():
        if replacement.get(key) != expected:
            blockers.append(f"unexpected_replacement_{key}:{replacement.get(key)}")

    selection_rules = plan.get("candidate_selection_rules", {})
    forbidden_inputs = set(selection_rules.get("forbidden_selection_inputs", []))
    for required in {"computed gamma proxy", "strategy PnL", "post-decision realized volatility"}:
        if required not in forbidden_inputs:
            blockers.append(f"missing_forbidden_selection_input:{required}")
    required_pre_checks = set(selection_rules.get("must_have_before_metadata_cost_check", []))
    for required in {"local option quote cache present", "local SPY 1-minute bar cache present", "no gamma/OI result viewed for the candidate date"}:
        if required not in required_pre_checks:
            blockers.append(f"missing_candidate_precheck:{required}")

    concrete = plan.get("concrete_manifest_requirements", {})
    if concrete.get("schema_version") != "h_g1_gamma_regime_date_set_preregistration_v3":
        blockers.append("concrete_manifest_schema_not_locked_to_v3")
    if concrete.get("total_dates") != 10:
        blockers.append(f"concrete_total_dates_not_10:{concrete.get('total_dates')}")
    if concrete.get("must_validate_before_paid_oi") is not True:
        blockers.append("concrete_manifest_validation_not_required")
    min_counts = concrete.get("minimum_regime_counts", {})
    expected_minimums = {
        "low_volatility": 3,
        "normal_volatility": 3,
        "high_volatility": 3,
        "high_importance_macro": 4,
        "no_high_importance_macro": 4,
        "in_sample": 4,
        "oos": 4,
        "unique_calendar_months": 6,
    }
    for key, expected in expected_minimums.items():
        if min_counts.get(key) != expected:
            blockers.append(f"minimum_count_not_locked:{key}:{min_counts.get(key)}")

    forbidden_claims = set(plan.get("forbidden_claims", []))
    for claim in {"H-G1 coverage pass", "NOVI/net-gamma strategy filter readiness", "v2.1 policy adoption"}:
        if claim not in forbidden_claims:
            blockers.append(f"missing_forbidden_claim:{claim}")

    return {
        "status": "blocked" if blockers else "pass",
        "blockers": blockers,
        "plan_path": _relative(plan_path),
        "hypothesis_id": plan.get("hypothesis_id"),
        "blocked_bucket": {
            "date": blocked_bucket.get("date"),
            "bucket": blocked_bucket.get("bucket"),
            "computed_oi_notional_share": blocked_bucket.get("computed_oi_notional_share"),
        },
        "replacement_objective": replacement,
    }


def _require_at_least(blockers: list[str], name: str, observed: Any, floor: float) -> None:
    if not isinstance(observed, int | float):
        blockers.append(f"{name}_not_numeric:{observed}")
        return
    if observed < floor:
        blockers.append(f"{name}_below_floor:{observed}<{floor}")


def _require_below(blockers: list[str], name: str, observed: Any, ceiling: float) -> None:
    if not isinstance(observed, int | float):
        blockers.append(f"{name}_not_numeric:{observed}")
        return
    if observed >= ceiling:
        blockers.append(f"{name}_not_below_ceiling:{observed}>={ceiling}")


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate H-G1 manifest v3 replacement plan.")
    parser.add_argument("--plan-path", type=Path, default=DEFAULT_PLAN_PATH)
    args = parser.parse_args(argv)
    result = validate_h_g1_manifest_v3_plan(args.plan_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
