from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.io import load_json


DEFAULT_PATH = (
    PROJECT_ROOT
    / "reports"
    / "data_cost"
    / "h_a2_fresh_oos_2025_2026_decision_tree_cost_plan.json"
)


def validate(path: Path = DEFAULT_PATH) -> dict[str, Any]:
    payload = load_json(path)
    blockers: list[str] = []
    authorization = payload.get("authorization") or {}
    cost = payload.get("cost_basis") or {}
    windows = payload.get("target_windows") or []

    if payload.get("hypothesis_id") != "H-A2":
        blockers.append("hypothesis_id_must_be_H-A2")
    if payload.get("status") != "awaiting_user_approval":
        blockers.append("status_must_await_user_approval")
    if payload.get("mode") != "plan_only_no_network_no_purchase":
        blockers.append("mode_must_be_plan_only")
    if authorization.get("user_approval_recorded") is not False:
        blockers.append("user_approval_must_not_be_recorded")
    if authorization.get("metadata_call_performed") is not False:
        blockers.append("metadata_call_must_not_be_performed")
    if authorization.get("download_performed") is not False:
        blockers.append("download_must_not_be_performed")
    if authorization.get("purchase_allowed_by_this_artifact") is not False:
        blockers.append("plan_must_not_authorize_purchase")
    if len(windows) != 2 or sum(int(item.get("date_count", 0)) for item in windows) != 20:
        blockers.append("target_scope_must_be_two_windows_and_20_dates")
    buckets = {item.get("vix_bucket") for item in windows}
    if buckets != {"prior_vix_below_15", "prior_vix_15_to_25"}:
        blockers.append("both_in_scope_vix_buckets_required")
    if any(item.get("high_importance_macro_date_count") != 0 for item in windows):
        blockers.append("high_importance_macro_dates_forbidden")
    if any(item.get("raw_cache_match_count") != 0 for item in windows):
        blockers.append("target_dates_must_be_uncached")

    base = float(cost.get("base_projected_cost_usd", -1))
    contingency = float(cost.get("contingency_usd", -1))
    ceiling = float(cost.get("user_approval_ceiling_usd", -1))
    if round(base + contingency, 6) != round(ceiling, 6):
        blockers.append("approval_ceiling_math_mismatch")
    if ceiling > 15.0:
        blockers.append("approval_ceiling_exceeds_bounded_pilot_cap")
    if cost.get("live_metadata_refresh_required_after_approval") is not True:
        blockers.append("live_metadata_refresh_must_be_required")

    return {"status": "pass" if not blockers else "blocked", "blockers": blockers}


if __name__ == "__main__":
    result = validate()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "pass" else 1)
