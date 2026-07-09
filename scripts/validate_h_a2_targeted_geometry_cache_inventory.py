from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_PATH = (
    PROJECT_ROOT / "reports" / "data_cost" / "h_a2_targeted_geometry_cache_inventory_and_cost_plan.json"
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_h_a2_targeted_geometry_cache_inventory(report_path: Path = DEFAULT_REPORT_PATH) -> dict[str, Any]:
    blockers: list[str] = []
    if not report_path.exists():
        return {"status": "blocked", "blockers": [f"missing_report:{report_path}"]}
    report = load_json(report_path)
    if report.get("schema_version") != "h_a2_targeted_geometry_cache_inventory_v1":
        blockers.append("schema_version_mismatch")
    if report.get("hypothesis_id") != "H-A2":
        blockers.append("hypothesis_id_must_be_H-A2")
    if report.get("step_id") != "H-A2.64":
        blockers.append("step_id_must_be_H-A2.64")
    if report.get("evidence_tier") != "E0":
        blockers.append("evidence_tier_must_be_E0")
    if report.get("status") != "complete_no_download_cost_estimate_deferred":
        blockers.append("status_must_be_complete_no_download_cost_estimate_deferred")

    target_sets = {item.get("target_set_id"): item for item in report.get("target_sets", [])}
    required_sets = {
        "train_candidate_geometry_backfill",
        "normal_control_geometry_pack",
        "stress_regime_geometry_pack",
        "oos_locked_rule_evaluation_pack",
    }
    missing_sets = required_sets - set(target_sets)
    if missing_sets:
        blockers.append(f"missing_target_sets:{','.join(sorted(missing_sets))}")

    train = target_sets.get("train_candidate_geometry_backfill", {})
    if train.get("target_date_count") != 30:
        blockers.append("train_target_date_count_must_be_30")
    if train.get("ready_for_local_geometry_parser_count") != train.get("target_date_count"):
        blockers.append("train_cache_must_be_ready_for_all_target_dates")

    normal = target_sets.get("normal_control_geometry_pack", {})
    if normal.get("candidate_ready_count") != 2:
        blockers.append("normal_control_candidate_ready_count_must_be_2")
    if normal.get("request_count_needed_now") != 0:
        blockers.append("normal_control_request_count_must_be_0")

    stress = target_sets.get("stress_regime_geometry_pack", {})
    if stress.get("missing_underlying_bar_count") != 13:
        blockers.append("stress_missing_underlying_bar_count_must_be_13")
    if stress.get("request_count_needed_now") != 0:
        blockers.append("stress_request_count_must_be_0_while_source_blocked")

    cost = report.get("cost_estimate", {})
    if cost.get("status") != "deferred_by_technical_dd_workstream_1_freeze":
        blockers.append("cost_estimate_must_be_deferred_by_dd_freeze")
    if cost.get("live_metadata_call_used") is not False:
        blockers.append("live_metadata_call_must_be_false")
    if cost.get("selected_key_env") is not None:
        blockers.append("selected_key_env_must_be_null_without_live_estimate")

    grouped = report.get("grouped_request_plan", {})
    if grouped.get("status") != "no_download":
        blockers.append("grouped_request_plan_status_must_be_no_download")
    if grouped.get("download_request_count_now") != 0:
        blockers.append("download_request_count_now_must_be_0")

    guardrails = report.get("guardrails", {})
    for field in [
        "network_used",
        "paid_data_used",
        "live_metadata_cost_call_used",
        "paid_download_allowed",
        "new_provider_used",
        "broker_request_used",
        "ibkr_request_used",
        "llm_call_used",
        "oos_rule_evaluation_used",
        "paper_trading_allowed",
        "operational_validation_allowed",
        "real_money_allowed",
    ]:
        if guardrails.get(field) is not False:
            blockers.append(f"guardrail_must_be_false:{field}")

    next_safe_action = report.get("next_safe_action", "")
    if "local H-A2 train/control geometry parser" not in next_safe_action:
        blockers.append("next_safe_action_must_point_to_local_geometry_parser")

    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "report_path": str(report_path),
        "target_set_count": len(target_sets),
        "train_target_date_count": train.get("target_date_count"),
        "normal_control_candidate_ready_count": normal.get("candidate_ready_count"),
        "stress_missing_underlying_bar_count": stress.get("missing_underlying_bar_count"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate H-A2.64 cache inventory and cost-plan report.")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT_PATH)
    args = parser.parse_args()
    result = validate_h_a2_targeted_geometry_cache_inventory(args.report_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

