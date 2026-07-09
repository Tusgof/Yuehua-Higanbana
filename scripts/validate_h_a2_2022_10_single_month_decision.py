from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DECISION_PATH = PROJECT_ROOT / "experiments" / "h_a2_2022_10_single_month_stress_decision.json"
DEFAULT_TOP2_GATE_PATH = PROJECT_ROOT / "reports" / "data_cost" / "h_a2_2022_h2_top2_live_cost_gate.json"
DEFAULT_MONTH_COST_PATH = PROJECT_ROOT / "reports" / "data_cost" / "databento_cost_h_a2_2022_10_stress.json"
DEFAULT_STRESS_ESTIMATE_PATH = PROJECT_ROOT / "reports" / "data_cost" / "h_a2_2022_h2_stress_purchase_estimate.json"


def validate_h_a2_2022_10_single_month_decision(
    decision_path: Path = DEFAULT_DECISION_PATH,
    top2_gate_path: Path = DEFAULT_TOP2_GATE_PATH,
    month_cost_path: Path = DEFAULT_MONTH_COST_PATH,
    stress_estimate_path: Path = DEFAULT_STRESS_ESTIMATE_PATH,
) -> dict[str, Any]:
    blockers: list[str] = []
    decision = _load_json(decision_path)
    top2_gate = _load_json(top2_gate_path)
    month_cost = _load_json(month_cost_path)
    stress_estimate = _load_json(stress_estimate_path)

    if decision.get("schema_version") != "h_a2_2022_10_single_month_stress_decision_v1":
        blockers.append("unsupported_schema_version")
    if decision.get("hypothesis_id") != "H-A2":
        blockers.append("hypothesis_id_must_be_h_a2")
    if decision.get("evidence_tier") != "E0":
        blockers.append("evidence_tier_must_be_e0")
    if decision.get("status") != "decision_complete":
        blockers.append("status_must_be_decision_complete")
    if decision.get("decision") != "approve_2022_10_single_month_stress_download_under_current_guard":
        blockers.append("decision_must_approve_single_month_download")
    if decision.get("selected_month") != "2022-10":
        blockers.append("selected_month_must_be_2022_10")

    for field in [
        "network_used",
        "paid_data_downloaded_by_this_decision",
        "paper_trading_allowed",
        "live_trading_allowed",
        "llm_research_allowed",
        "research_log_required",
    ]:
        if decision.get(field) is not False:
            blockers.append(f"{field}_must_be_false")

    if top2_gate.get("status") != "blocked":
        blockers.append("top2_gate_must_be_blocked")
    top2 = top2_gate.get("top2", {})
    if top2.get("download_allowed_now") is not False:
        blockers.append("top2_download_must_be_forbidden")
    if _round6(top2.get("estimated_cost_usd")) != 20.748872:
        blockers.append("top2_estimated_cost_mismatch")

    if month_cost.get("decision", {}).get("status") != "pass":
        blockers.append("single_month_cost_report_must_pass")
    if _round6(month_cost.get("total_estimated_cost_usd")) != 10.52248:
        blockers.append("single_month_estimated_cost_mismatch")
    if month_cost.get("live_request_count") != 21:
        blockers.append("single_month_live_request_count_must_be_21")

    guard = decision.get("single_month_cost_guard", {})
    if _round6(guard.get("current_used_usd")) != 109.467226:
        blockers.append("current_used_usd_mismatch")
    if _round6(guard.get("selected_month_estimated_cost_usd")) != 10.52248:
        blockers.append("selected_month_cost_guard_mismatch")
    if _round6(guard.get("projected_used_after_download_usd")) != 119.989706:
        blockers.append("projected_used_after_download_mismatch")
    if _round6(guard.get("projected_remaining_after_download_usd")) != 5.010294:
        blockers.append("projected_remaining_after_download_mismatch")
    if guard.get("decision") != "pass":
        blockers.append("single_month_guard_decision_must_pass")
    if float(guard.get("projected_used_after_download_usd", 999999)) >= float(guard.get("stop_threshold_usd", 0)):
        blockers.append("projected_usage_must_remain_below_stop_threshold")

    selected = _find_month(stress_estimate.get("ranked_2022_h2_months", []), "2022-10")
    selection_reason = decision.get("selection_reason", {})
    if not selected:
        blockers.append("stress_estimate_must_include_2022_10")
    else:
        for key in ["rank", "trading_days", "high_vix_days", "stress_vix_days"]:
            if selection_reason.get(key) != selected.get(key):
                blockers.append(f"selection_reason_{key}_mismatch")
        for key in ["avg_vix", "max_vix"]:
            if _round4(selection_reason.get(key)) != _round4(selected.get(key)):
                blockers.append(f"selection_reason_{key}_mismatch")

    forbidden_text = "\n".join(decision.get("forbidden_actions", []))
    for phrase in [
        "Do not download 2022-09",
        "Do not download the original top2 bundle",
        "Do not download top3",
        "Do not make an E2 acceptance",
        "Do not run live LLM research",
    ]:
        if phrase not in forbidden_text:
            blockers.append(f"missing_forbidden_action:{phrase}")

    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "decision_path": _relative(decision_path),
        "selected_month": decision.get("selected_month"),
        "top2_gate_status": top2_gate.get("status"),
        "single_month_estimated_cost_usd": month_cost.get("total_estimated_cost_usd"),
        "projected_used_after_download_usd": guard.get("projected_used_after_download_usd"),
        "projected_remaining_after_download_usd": guard.get("projected_remaining_after_download_usd"),
    }


def _find_month(months: list[dict[str, Any]], month: str) -> dict[str, Any] | None:
    for item in months:
        if item.get("month") == month:
            return item
    return None


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _round6(value: Any) -> float | None:
    if value is None:
        return None
    return round(float(value), 6)


def _round4(value: Any) -> float | None:
    if value is None:
        return None
    return round(float(value), 4)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the H-A2 2022-10 single-month stress decision artifact.")
    parser.add_argument("--decision-path", type=Path, default=DEFAULT_DECISION_PATH)
    parser.add_argument("--top2-gate-path", type=Path, default=DEFAULT_TOP2_GATE_PATH)
    parser.add_argument("--month-cost-path", type=Path, default=DEFAULT_MONTH_COST_PATH)
    parser.add_argument("--stress-estimate-path", type=Path, default=DEFAULT_STRESS_ESTIMATE_PATH)
    args = parser.parse_args(argv)

    result = validate_h_a2_2022_10_single_month_decision(
        args.decision_path,
        args.top2_gate_path,
        args.month_cost_path,
        args.stress_estimate_path,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
