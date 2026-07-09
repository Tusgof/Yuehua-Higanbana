from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REVIEW_PATH = PROJECT_ROOT / "experiments" / "h_g1_bucket_policy_review_preregistration.json"
REQUIRED_SCHEMA_VERSION = "h_g1_bucket_policy_review_preregistration_v1"
REQUIRED_POLICY_IDS = {
    "candidate_a_current_v2_moneyness_only",
    "candidate_b_side_aware_required_bucket",
    "candidate_c_notional_weighted_coverage",
}


def validate_h_g1_bucket_policy_review(review_path: Path = DEFAULT_REVIEW_PATH) -> dict[str, Any]:
    review = json.loads(review_path.read_text(encoding="utf-8"))
    blockers: list[str] = []

    if review.get("schema_version") != REQUIRED_SCHEMA_VERSION:
        blockers.append(f"unsupported_schema_version:{review.get('schema_version')}")
    if review.get("hypothesis_id") != "H-G1":
        blockers.append(f"unexpected_hypothesis_id:{review.get('hypothesis_id')}")
    if review.get("status") != "preregistered_review_only_not_adopted":
        blockers.append(f"unexpected_status:{review.get('status')}")
    if review.get("review_artifact") != "docs/H_G1_BUCKET_POLICY_REVIEW.md":
        blockers.append("review_artifact_not_locked")
    if review.get("controlling_policy") != "docs/GAMMA_AGGREGATION_VALIDATION_POLICY.md":
        blockers.append("controlling_policy_not_v2")

    source_evidence = review.get("source_evidence", {})
    expected_sources = {
        "manifest_v3_summary": "reports/diagnostics/h_g1_gamma_regime_diagnostic_summary_v3.json",
        "bucket_failure_diagnostic": "reports/diagnostics/h_g1_manifest_v3_bucket_failure_diagnostic.json",
        "manifest_v3_enriched_rows": "data/derived/spy_0dte/h_g1_gamma_regime/option_quote_enriched_manifest_v3_snapshot.jsonl",
    }
    for key, expected in expected_sources.items():
        if source_evidence.get(key) != expected:
            blockers.append(f"source_not_locked:{key}:{source_evidence.get(key)}")

    facts = review.get("locked_h_g1_15_facts", {})
    if facts.get("failed_bucket_count") != 5:
        blockers.append(f"failed_bucket_count_not_locked:{facts.get('failed_bucket_count')}")
    if facts.get("blocked_rows_in_failed_buckets") != 55:
        blockers.append(f"blocked_rows_not_locked:{facts.get('blocked_rows_in_failed_buckets')}")
    _require_equal(blockers, "opposite_right_blocked_row_share", facts.get("opposite_right_blocked_row_share"), 1.0)
    _require_at_least(
        blockers,
        "minimum_failed_bucket_computed_oi_notional_share",
        facts.get("minimum_failed_bucket_computed_oi_notional_share"),
        0.8,
    )
    _require_at_least(
        blockers,
        "minimum_failed_bucket_gamma_proxy_share",
        facts.get("minimum_failed_bucket_gamma_proxy_share"),
        0.8,
    )
    if facts.get("weak_notional_failure_count") != 0:
        blockers.append(f"weak_notional_failure_count_not_zero:{facts.get('weak_notional_failure_count')}")

    policies = review.get("candidate_policies", [])
    if not isinstance(policies, list):
        blockers.append("candidate_policies_not_list")
        policies = []
    policy_ids = {item.get("policy_id") for item in policies if isinstance(item, dict)}
    missing = REQUIRED_POLICY_IDS - policy_ids
    for policy_id in sorted(missing):
        blockers.append(f"missing_candidate_policy:{policy_id}")
    for item in policies:
        if not isinstance(item, dict):
            blockers.append("candidate_policy_not_object")
            continue
        _validate_candidate_policy(blockers, item)

    rerun_policy = review.get("rerun_policy", {})
    required_false = [
        "network_allowed",
        "paid_data_allowed",
        "new_dates_allowed",
        "new_option_quotes_allowed",
        "new_oi_files_allowed",
        "strategy_pnl_selection_allowed",
    ]
    for key in required_false:
        if rerun_policy.get(key) is not False:
            blockers.append(f"rerun_policy_{key}_not_false")
    if rerun_policy.get("allowed_output_status") != "policy_review_only":
        blockers.append(f"unexpected_allowed_output_status:{rerun_policy.get('allowed_output_status')}")
    if rerun_policy.get("research_log_required_if_diagnostic_result_completed") is not True:
        blockers.append("research_log_trigger_not_required")
    if rerun_policy.get("next_research_log_prefix") != "017-higanbana-":
        blockers.append(f"unexpected_next_research_log_prefix:{rerun_policy.get('next_research_log_prefix')}")

    acceptance = set(review.get("acceptance_criteria", []))
    for required in {
        "All candidate policies use manifest-v3 rows only.",
        "Opposite-right ITM rows are reported explicitly.",
        "Any selected candidate is justified by mechanism and data lineage, not by strategy PnL.",
    }:
        if required not in acceptance:
            blockers.append(f"missing_acceptance_criterion:{required}")

    forbidden_claims = set(review.get("forbidden_claims", []))
    for claim in {
        "H-G1 pass",
        "policy adopted by pre-registration alone",
        "NOVI/net-gamma strategy filter readiness",
        "true market-maker net gamma",
        "strategy validation from coverage policy",
    }:
        if claim not in forbidden_claims:
            blockers.append(f"missing_forbidden_claim:{claim}")

    return {
        "status": "blocked" if blockers else "pass",
        "blockers": blockers,
        "review_path": _relative(review_path),
        "hypothesis_id": review.get("hypothesis_id"),
        "candidate_policy_count": len(policies),
        "candidate_policy_ids": sorted(policy_ids),
        "next_safe_action": review.get("next_safe_action"),
    }


def _validate_candidate_policy(blockers: list[str], item: dict[str, Any]) -> None:
    policy_id = item.get("policy_id")
    gate = item.get("required_bucket_gate")
    expected_gates = {
        "candidate_a_current_v2_moneyness_only": "moneyness_only",
        "candidate_b_side_aware_required_bucket": "side_aware",
        "candidate_c_notional_weighted_coverage": "notional_weighted",
    }
    if policy_id in expected_gates and gate != expected_gates[policy_id]:
        blockers.append(f"unexpected_gate:{policy_id}:{gate}")
    _require_at_least(blockers, f"{policy_id}_row_rate_floor", item.get("row_rate_floor"), 0.6)
    _require_at_least(
        blockers,
        f"{policy_id}_computed_oi_notional_share_floor",
        item.get("computed_oi_notional_share_floor"),
        0.8,
    )
    _require_at_least(
        blockers,
        f"{policy_id}_retained_abs_gamma_proxy_share_floor",
        item.get("retained_abs_gamma_proxy_share_floor"),
        0.8,
    )
    treatment = item.get("opposite_right_itm_treatment")
    if policy_id != "candidate_a_current_v2_moneyness_only" and "reported" not in str(treatment):
        blockers.append(f"opposite_right_itm_not_reported:{policy_id}:{treatment}")


def _require_equal(blockers: list[str], name: str, observed: Any, expected: float) -> None:
    if not isinstance(observed, int | float):
        blockers.append(f"{name}_not_numeric:{observed}")
        return
    if float(observed) != expected:
        blockers.append(f"{name}_not_equal:{observed}!={expected}")


def _require_at_least(blockers: list[str], name: str, observed: Any, floor: float) -> None:
    if not isinstance(observed, int | float):
        blockers.append(f"{name}_not_numeric:{observed}")
        return
    if float(observed) < floor:
        blockers.append(f"{name}_below_floor:{observed}<{floor}")


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate H-G1 bucket-policy review pre-registration.")
    parser.add_argument("--review-path", type=Path, default=DEFAULT_REVIEW_PATH)
    args = parser.parse_args(argv)
    result = validate_h_g1_bucket_policy_review(args.review_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
