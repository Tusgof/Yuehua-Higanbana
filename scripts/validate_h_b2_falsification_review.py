from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REVIEW_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_b2_falsification_review.json"
DEFAULT_SUMMARY_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_b2_subsystem_b_scale_summary.json"


def validate_review(review_path: Path = DEFAULT_REVIEW_PATH, summary_path: Path = DEFAULT_SUMMARY_PATH) -> dict[str, Any]:
    blockers: list[str] = []
    review = _read_json(review_path)
    summary = _read_json(summary_path)

    if review.get("schema_version") != "h_b2_falsification_review_v1":
        blockers.append("unsupported_schema_version")
    if review.get("hypothesis_id") != "H-B2":
        blockers.append("hypothesis_id_must_be_h_b2")
    if review.get("evidence_tier") != "E1":
        blockers.append("evidence_tier_must_be_e1")
    if review.get("status") != "review_complete":
        blockers.append("status_must_be_review_complete")
    if review.get("decision") != "keep_h_b2_parked_current_grid_not_resurrected":
        blockers.append("decision_must_keep_h_b2_parked")
    if review.get("current_grid_failed_preregistered_keep_active_rule") is not True:
        blockers.append("current_grid_must_fail_keep_active_rule")
    if review.get("acceptance_grade_falsified") is not False:
        blockers.append("acceptance_grade_falsified_must_remain_false")

    false_flags = [
        "network_used",
        "paid_data_used",
        "ibkr_requested",
        "llm_called",
        "new_strategy_pnl_run",
        "paper_trading_allowed",
        "operational_validation_allowed",
        "real_money_allowed",
    ]
    for field in false_flags:
        if review.get(field) is not False:
            blockers.append(f"{field}_must_be_false")

    if review.get("source_experiment_status") != summary.get("status"):
        blockers.append("source_experiment_status_mismatch")
    if review.get("source_evidence_tier") != summary.get("evidence_tier"):
        blockers.append("source_evidence_tier_mismatch")
    if summary.get("hypothesis_id") != "H-B2":
        blockers.append("source_summary_must_reference_h_b2")

    source_positive = summary.get("diagnostics", {}).get("positive_total_and_oos_scenarios", [])
    if review.get("positive_total_and_oos_scenarios") != source_positive:
        blockers.append("positive_total_and_oos_scenarios_mismatch")
    if source_positive:
        blockers.append("source_summary_has_positive_total_and_oos_scenarios")

    scenario_reviews = review.get("scenario_reviews", [])
    source_scenarios = summary.get("scenarios", [])
    if len(scenario_reviews) != len(source_scenarios):
        blockers.append("scenario_review_count_mismatch")
    for item in scenario_reviews:
        if item.get("passes_keep_active_rule") is not False:
            blockers.append(f"scenario_passes_keep_active_rule:{item.get('scenario_id')}")
        if item.get("total_implementable_pnl", 0) > 0 and item.get("oos_implementable_pnl", 0) > 0:
            blockers.append(f"scenario_positive_total_and_oos:{item.get('scenario_id')}")

    required_tier_blockers = {
        "E1 falsification review only",
        "No E2 acceptance-grade validation",
        "Some scenarios remain under-sampled or underpowered",
        "Current grid failure does not falsify all possible Sub-System B mechanisms",
    }
    tier_blockers = set(review.get("tier_blockers", []))
    for missing in sorted(required_tier_blockers - tier_blockers):
        blockers.append(f"missing_tier_blocker:{missing}")

    forbidden = "\n".join(review.get("forbidden_actions", []))
    required_phrases = [
        "Do not use H-B2 current grid for paper trading.",
        "Do not buy new data for H-B2 from this review alone.",
        "Do not delete Sub-System B from project scope solely because this grid failed.",
    ]
    for phrase in required_phrases:
        if phrase not in forbidden:
            blockers.append(f"missing_forbidden_action:{phrase}")

    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "review_path": _relative(review_path),
        "summary_path": _relative(summary_path),
        "decision": review.get("decision"),
        "scenario_count": len(scenario_reviews),
        "positive_total_and_oos_scenarios": review.get("positive_total_and_oos_scenarios"),
        "acceptance_grade_falsified": review.get("acceptance_grade_falsified"),
    }


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the H-B2 falsification review artifact.")
    parser.add_argument("--review-path", type=Path, default=DEFAULT_REVIEW_PATH)
    parser.add_argument("--summary-path", type=Path, default=DEFAULT_SUMMARY_PATH)
    args = parser.parse_args(argv)

    result = validate_review(args.review_path, args.summary_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
