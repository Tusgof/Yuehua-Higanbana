from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.io import load_json


DEFAULT_PATH = PROJECT_ROOT / "experiments" / "h_a2_orb_0936_paid_download_decision.json"
DEFAULT_PLAN = PROJECT_ROOT / "reports" / "data_cost" / "h_a2_orb_0936_cost_plan.json"


def validate(path: Path = DEFAULT_PATH, plan_path: Path = DEFAULT_PLAN) -> dict[str, Any]:
    payload = load_json(path)
    plan = load_json(plan_path)
    blockers: list[str] = []
    scope = payload.get("approved_scope") or {}
    guard = payload.get("cost_guard") or {}
    authorization = payload.get("authorization") or {}
    plan_dates = [str(row["date"]) for row in plan.get("target_dates", [])]

    if payload.get("status") != "approved":
        blockers.append("status_must_be_approved")
    if payload.get("decision") != "approve_exact_20_date_orb_0936_download_after_live_cost_pass":
        blockers.append("decision_must_match_bounded_download")
    if payload.get("hypothesis_id") != "H-A2":
        blockers.append("hypothesis_id_must_be_H-A2")
    if plan.get("status") != "awaiting_user_approval" or plan.get("mode") != "plan_only_no_network_no_purchase":
        blockers.append("source_cost_plan_must_be_unexecuted_plan")
    if scope.get("dates") != plan_dates or scope.get("date_count") != 20:
        blockers.append("approved_dates_must_match_cost_plan")
    if scope.get("request_count") != 41:
        blockers.append("request_count_must_include_40_intraday_plus_1_daily")
    if scope.get("broad_calendar_expansion_allowed") is not False:
        blockers.append("broad_calendar_expansion_must_be_forbidden")
    if guard.get("selected_key_env") != "DATABENTO_API_01":
        blockers.append("selected_key_env_must_be_DATABENTO_API_01")
    if guard.get("account_provenance") != "primary_existing_databento_account":
        blockers.append("account_provenance_must_be_primary_existing_account")
    if float(guard.get("selected_key_authorization_limit_usd", -1)) != 50.0:
        blockers.append("selected_key_limit_must_be_50")
    if float(guard.get("known_committed_selected_key_usage_usd", -1)) != 12.361983:
        blockers.append("known_selected_key_usage_must_match_ledger")
    if float(guard.get("approved_purchase_ceiling_usd", -1)) != 14.21628:
        blockers.append("purchase_ceiling_must_match_approved_plan")
    if guard.get("key_value_stored") is not False:
        blockers.append("key_value_must_not_be_stored")
    if guard.get("stop_if_live_estimate_exceeds_ceiling") is not True:
        blockers.append("live_estimate_ceiling_stop_required")
    if guard.get("stop_if_cumulative_selected_key_usage_exceeds_limit") is not True:
        blockers.append("cumulative_key_limit_stop_required")
    if authorization.get("user_approval_recorded") is not True:
        blockers.append("user_approval_must_be_recorded")
    if authorization.get("live_metadata_call_allowed") is not True:
        blockers.append("live_metadata_call_must_be_authorized")
    if authorization.get("download_allowed_after_cost_gate_pass") is not True:
        blockers.append("download_must_require_cost_gate_pass")
    if authorization.get("target_outcome_parse_allowed") is not False:
        blockers.append("target_outcome_parse_must_be_forbidden")
    if authorization.get("experiment_run_allowed") is not False:
        blockers.append("experiment_run_must_be_forbidden")

    return {"status": "pass" if not blockers else "blocked", "blockers": blockers}


if __name__ == "__main__":
    result = validate()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "pass" else 1)
