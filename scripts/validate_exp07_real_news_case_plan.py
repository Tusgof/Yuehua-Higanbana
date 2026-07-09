from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAN_PATH = PROJECT_ROOT / "reports" / "experiments" / "exp07_real_news_case_plan.json"

REQUIRED_NEWS_FIELDS = {
    "published_at",
    "fetched_at",
    "source",
    "url",
    "headline",
    "decision_time_et",
}
REQUIRED_CASE_GROUPS = {
    "normal_quiet_day",
    "scheduled_macro_day",
    "large_intraday_move_day",
    "volatility_spike_day",
    "geopolitical_shock_or_war_risk_day",
    "banking_or_liquidity_stress_day",
    "index_etf_futures_disruption_day",
    "false_alarm_day",
}
REQUIRED_PROMPT_FAMILIES = {
    "role_only_analyst",
    "structured_json_classifier",
    "few_shot_real_news_examples",
    "evidence_first_rubric",
    "scenario_branching_prompt",
    "self_consistency_ensemble",
}


def load_plan(path: Path = DEFAULT_PLAN_PATH) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def validate_plan(path: Path = DEFAULT_PLAN_PATH) -> list[str]:
    plan = load_plan(path)
    errors: list[str] = []

    if plan.get("plan_version") != "exp07-real-news-case-plan-v1":
        errors.append("plan_version must be exp07-real-news-case-plan-v1")

    acceptance_bar = plan.get("acceptance_bar", {})
    if acceptance_bar.get("synthetic_cases_allowed_for_research") is not False:
        errors.append("synthetic_cases_allowed_for_research must be false")
    for flag in ("requires_real_news_snapshots", "requires_timestamp_clean_inputs", "requires_costed_live_rows"):
        if acceptance_bar.get(flag) is not True:
            errors.append(f"acceptance_bar.{flag} must be true")

    required_news_fields = set(plan.get("required_news_fields", []))
    missing_news_fields = sorted(REQUIRED_NEWS_FIELDS.difference(required_news_fields))
    if missing_news_fields:
        errors.append(f"missing required news fields: {missing_news_fields}")

    required_case_groups = set(plan.get("required_case_groups", []))
    missing_case_groups = sorted(REQUIRED_CASE_GROUPS.difference(required_case_groups))
    if missing_case_groups:
        errors.append(f"missing required case groups: {missing_case_groups}")

    prompt_families = plan.get("prompt_template_families", [])
    if not isinstance(prompt_families, list) or not prompt_families:
        errors.append("prompt_template_families must be a non-empty list")
        prompt_families = []
    family_ids = [row.get("family_id") for row in prompt_families if isinstance(row, dict)]
    missing_families = sorted(REQUIRED_PROMPT_FAMILIES.difference(family_ids))
    if missing_families:
        errors.append(f"missing prompt template families: {missing_families}")
    duplicate_families = sorted({family_id for family_id in family_ids if family_ids.count(family_id) > 1})
    if duplicate_families:
        errors.append(f"duplicate prompt template families: {duplicate_families}")

    candidate_queue = plan.get("candidate_queue", [])
    if not isinstance(candidate_queue, list) or not candidate_queue:
        errors.append("candidate_queue must be a non-empty list")
        candidate_queue = []
    if int(plan.get("candidate_day_count", 0)) != len(candidate_queue):
        errors.append("candidate_day_count must match candidate_queue length")

    for index, candidate in enumerate(candidate_queue):
        if not isinstance(candidate, dict):
            errors.append(f"candidate_queue[{index}] must be an object")
            continue
        for field in ("trade_date", "decision_time_et", "split", "capture_status", "raw_output_path", "status_output_path"):
            if not str(candidate.get(field, "")).strip():
                errors.append(f"candidate_queue[{index}].{field} is required")
        planned_groups = set(candidate.get("planned_case_groups", []))
        missing_candidate_groups = sorted(REQUIRED_CASE_GROUPS.difference(planned_groups))
        if missing_candidate_groups:
            errors.append(f"candidate_queue[{index}] missing planned case groups: {missing_candidate_groups}")

    blockers = set(plan.get("blockers", []))
    captured_count = int(plan.get("captured_candidate_count", 0))
    if captured_count == 0 and "requires_real_timestamp_clean_news_cases" not in blockers:
        errors.append("0 captured candidates must keep requires_real_timestamp_clean_news_cases blocker")
    retry_pressure = plan.get("retry_pressure", {})
    if (
        isinstance(retry_pressure, dict)
        and retry_pressure.get("status") == "cooldown_recommended"
        and plan.get("collection_status") == "ready_to_collect"
    ):
        errors.append("cooldown_recommended retry pressure must not report collection_status ready_to_collect")
    if plan.get("gdelt_live_retry_allowed") is False and plan.get("collection_status") == "ready_to_collect":
        errors.append("gdelt_live_retry_allowed=false must not report collection_status ready_to_collect")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Exp07 real-news case collection plan.")
    parser.add_argument("--path", type=Path, default=DEFAULT_PLAN_PATH)
    args = parser.parse_args(argv)
    errors = validate_plan(args.path)
    if errors:
        for error in errors:
            print(error)
        return 1
    print(f"validated Exp07 real-news case plan from {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
