from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ADOPTION_PATH = PROJECT_ROOT / "experiments" / "h_g1_side_aware_bucket_policy_adoption.json"
REQUIRED_SCHEMA_VERSION = "h_g1_side_aware_bucket_policy_adoption_v1"
REQUIRED_POLICY_ID = "h_g1_required_bucket_policy_v3_side_aware"
REQUIRED_CANDIDATE = "candidate_b_side_aware_required_bucket"


def validate_h_g1_side_aware_policy_adoption(adoption_path: Path = DEFAULT_ADOPTION_PATH) -> dict[str, Any]:
    adoption = json.loads(adoption_path.read_text(encoding="utf-8"))
    blockers: list[str] = []

    if adoption.get("schema_version") != REQUIRED_SCHEMA_VERSION:
        blockers.append(f"unsupported_schema_version:{adoption.get('schema_version')}")
    if adoption.get("hypothesis_id") != "H-G1":
        blockers.append(f"unexpected_hypothesis_id:{adoption.get('hypothesis_id')}")
    if adoption.get("status") != "adopted_for_next_diagnostic_only":
        blockers.append(f"unexpected_status:{adoption.get('status')}")
    if adoption.get("policy_id") != REQUIRED_POLICY_ID:
        blockers.append(f"unexpected_policy_id:{adoption.get('policy_id')}")
    if adoption.get("adopted_candidate") != REQUIRED_CANDIDATE:
        blockers.append(f"unexpected_adopted_candidate:{adoption.get('adopted_candidate')}")
    if adoption.get("controlling_doc") != "docs/H_G1_SIDE_AWARE_BUCKET_POLICY_ADOPTION.md":
        blockers.append("controlling_doc_not_locked")

    _require_source(blockers, adoption, "source_preregistration", "experiments/h_g1_bucket_policy_review_preregistration.json")
    _require_source(blockers, adoption, "source_comparison", "reports/diagnostics/h_g1_bucket_policy_comparison.json")
    _require_source(
        blockers,
        adoption,
        "source_bucket_failure_diagnostic",
        "reports/diagnostics/h_g1_manifest_v3_bucket_failure_diagnostic.json",
    )
    _require_source(
        blockers,
        adoption,
        "source_manifest_v3_summary",
        "reports/diagnostics/h_g1_gamma_regime_diagnostic_summary_v3.json",
    )

    scope = adoption.get("adoption_scope", {})
    if scope.get("diagnostic_rerun_allowed") is not True:
        blockers.append("diagnostic_rerun_not_allowed")
    for key in [
        "strategy_use_allowed",
        "network_allowed",
        "paid_data_allowed",
        "new_dates_allowed",
        "new_option_quotes_allowed",
        "new_oi_files_allowed",
        "strategy_pnl_selection_allowed",
    ]:
        if scope.get(key) is not False:
            blockers.append(f"adoption_scope_{key}_not_false")

    rules = adoption.get("required_bucket_rules", {})
    _require_rule(blockers, rules, "otm_put", "put", "<0.995")
    _require_rule(blockers, rules, "otm_call", "call", ">1.005")
    _require_rule(blockers, rules, "atm", "call_or_put", "0.995<=moneyness<=1.005")
    opposite = rules.get("opposite_right_itm_rows", {})
    if opposite.get("treatment") != "reported_separately_not_required_bucket_pass_fail":
        blockers.append(f"opposite_right_itm_treatment_invalid:{opposite.get('treatment')}")
    if opposite.get("must_remain_visible") is not True:
        blockers.append("opposite_right_itm_not_visible")

    thresholds = adoption.get("thresholds", {})
    _require_at_least(blockers, "computed_row_rate_floor", thresholds.get("computed_row_rate_floor"), 0.6)
    _require_at_least(
        blockers,
        "computed_oi_notional_share_floor",
        thresholds.get("computed_oi_notional_share_floor"),
        0.8,
    )
    _require_at_least(
        blockers,
        "retained_abs_gamma_proxy_share_floor",
        thresholds.get("retained_abs_gamma_proxy_share_floor"),
        0.8,
    )

    facts = adoption.get("preserved_locked_facts", {})
    if facts.get("candidate_b_passed_date_count") != 10:
        blockers.append(f"candidate_b_passed_date_count_not_locked:{facts.get('candidate_b_passed_date_count')}")
    if facts.get("candidate_b_failure_count") != 0:
        blockers.append(f"candidate_b_failure_count_not_zero:{facts.get('candidate_b_failure_count')}")
    if facts.get("h_g1_15_blocked_rows_in_failed_buckets") != 55:
        blockers.append("h_g1_15_blocked_rows_not_preserved")
    _require_at_least(
        blockers,
        "h_g1_15_minimum_failed_bucket_computed_oi_notional_share",
        facts.get("h_g1_15_minimum_failed_bucket_computed_oi_notional_share"),
        0.8,
    )

    if adoption.get("next_allowed_action") != "rerun_h_g1_gamma_diagnostic_manifest_v3_side_aware_policy":
        blockers.append(f"unexpected_next_allowed_action:{adoption.get('next_allowed_action')}")

    forbidden_claims = set(adoption.get("forbidden_claims", []))
    for claim in {
        "H-G1 pass",
        "strategy validation from coverage policy",
        "NOVI/net-gamma strategy filter readiness",
        "true market-maker net gamma",
        "paid data or new dates justified by this artifact",
        "policy superiority based on strategy PnL",
    }:
        if claim not in forbidden_claims:
            blockers.append(f"missing_forbidden_claim:{claim}")

    return {
        "status": "blocked" if blockers else "pass",
        "blockers": blockers,
        "adoption_path": _relative(adoption_path),
        "hypothesis_id": adoption.get("hypothesis_id"),
        "policy_id": adoption.get("policy_id"),
        "next_allowed_action": adoption.get("next_allowed_action"),
    }


def _require_source(blockers: list[str], adoption: dict[str, Any], key: str, expected: str) -> None:
    if adoption.get(key) != expected:
        blockers.append(f"source_not_locked:{key}:{adoption.get(key)}")


def _require_rule(blockers: list[str], rules: dict[str, Any], bucket: str, right: str, moneyness: str) -> None:
    rule = rules.get(bucket, {})
    if rule.get("option_right") != right:
        blockers.append(f"{bucket}_right_invalid:{rule.get('option_right')}")
    if rule.get("moneyness") != moneyness:
        blockers.append(f"{bucket}_moneyness_invalid:{rule.get('moneyness')}")
    if rule.get("controls_pass_fail") is not True:
        blockers.append(f"{bucket}_does_not_control_pass_fail")


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
    parser = argparse.ArgumentParser(description="Validate H-G1 side-aware bucket policy adoption.")
    parser.add_argument("--adoption-path", type=Path, default=DEFAULT_ADOPTION_PATH)
    args = parser.parse_args(argv)
    result = validate_h_g1_side_aware_policy_adoption(args.adoption_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

