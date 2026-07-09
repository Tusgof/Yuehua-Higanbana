from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUMMARY_PATH = (
    PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_post_stress_normalization_control_exact_replay.json"
)
CANDIDATE_DATE = "2025-05-05"


def validate_h_a2_post_stress_normalization_control_exact_replay(
    summary_path: Path = DEFAULT_SUMMARY_PATH,
) -> dict[str, Any]:
    summary = _load_json(summary_path)
    blockers: list[str] = []

    if summary.get("schema_version") != "h_a2_post_stress_normalization_control_exact_replay_v1":
        blockers.append("unsupported_schema_version")
    if summary.get("record_type") != "experiment_summary":
        blockers.append("record_type_must_be_experiment_summary")
    if summary.get("experiment_id") != "h_a2_post_stress_normalization_control_exact_replay":
        blockers.append("experiment_id_must_match")
    if summary.get("hypothesis_id") != "H-A2":
        blockers.append("hypothesis_id_must_be_h_a2")
    if summary.get("status") != "complete":
        blockers.append("status_must_be_complete")
    if summary.get("evidence_tier") != "E1":
        blockers.append("evidence_tier_must_be_e1")

    _validate_candidate(summary, blockers)
    _validate_methodology(summary, blockers)
    _validate_selected_vertical(summary, blockers)
    _validate_pnl(summary, blockers)
    _validate_guardrails(summary, blockers)
    _validate_outputs(summary, blockers)

    candidate = summary.get("candidate", {})
    pnl = summary.get("pnl") or {}
    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "summary_path": _relative(summary_path),
        "experiment_id": summary.get("experiment_id"),
        "hypothesis_id": summary.get("hypothesis_id"),
        "evidence_tier": summary.get("evidence_tier"),
        "candidate_date": candidate.get("date"),
        "direction": candidate.get("direction"),
        "mid_pnl": pnl.get("mid_pnl"),
        "implementable_pnl": pnl.get("implementable_pnl"),
        "paper_trading_allowed": summary.get("paper_trading_allowed"),
        "research_log_required": summary.get("research_log_required"),
    }


def _validate_candidate(summary: dict[str, Any], blockers: list[str]) -> None:
    candidate = summary.get("candidate", {})
    if candidate.get("date") != CANDIDATE_DATE:
        blockers.append("candidate_date_must_be_2025_05_05")
    if candidate.get("direction") != "call":
        blockers.append("candidate_direction_must_be_call")
    if candidate.get("entry_time_et") != "09:35:00":
        blockers.append("entry_time_must_be_0935")
    if candidate.get("forced_close_time_et") != "15:45:00":
        blockers.append("forced_close_time_must_be_1545")
    if _round6(candidate.get("locked_threshold")) != 0.001:
        blockers.append("locked_threshold_must_be_0_001")
    if candidate.get("underlying_entry_close") is None:
        blockers.append("underlying_entry_close_required")
    if candidate.get("underlying_forced_close") is None:
        blockers.append("underlying_forced_close_required")


def _validate_methodology(summary: dict[str, Any], blockers: list[str]) -> None:
    methodology = summary.get("methodology", {})
    expected = {
        "scope": "single_candidate_date_only",
        "strike_selection_method": "nearest_discrete_strike_rounding",
        "entry_order_assumption": "limit_at_mid_control",
        "exit_order_assumption": "forced_close_1545",
        "target_gap": 1.48,
        "width": 2.0,
        "fee_per_leg_usd": 0.64,
        "fee_leg_count": 4,
        "contract_multiplier": 100,
    }
    for key, value in expected.items():
        actual = methodology.get(key)
        if isinstance(value, float):
            if _round6(actual) != value:
                blockers.append(f"{key}_must_be_{value}")
        elif actual != value:
            blockers.append(f"{key}_must_match")
    for field in [
        "threshold_search_used",
        "new_filter_search_used",
        "oos_tuning_used",
        "interpolation_used",
        "post_result_strike_selection_used",
    ]:
        if methodology.get(field) is not False:
            blockers.append(f"{field}_must_be_false")


def _validate_selected_vertical(summary: dict[str, Any], blockers: list[str]) -> None:
    selected = summary.get("selected_vertical")
    if not isinstance(selected, dict):
        blockers.append("selected_vertical_required")
        return
    if selected.get("status") != "selected":
        blockers.append("selected_vertical_status_must_be_selected")
    if selected.get("required_exit_symbols_available") is not True:
        blockers.append("required_exit_symbols_available_must_be_true")
    mapping = selected.get("mapping", {})
    if mapping.get("mapping_method") != "nearest_discrete_strike_rounding":
        blockers.append("mapping_method_must_be_nearest_discrete_strike_rounding")
    if mapping.get("interpolation_used") is not False:
        blockers.append("mapping_interpolation_used_must_be_false")
    if _round6(mapping.get("target_gap")) != 1.48:
        blockers.append("mapping_target_gap_must_be_1_48")
    if _round6(mapping.get("target_width")) != 2.0:
        blockers.append("mapping_target_width_must_be_2")
    if not isinstance(selected.get("legs"), list) or len(selected["legs"]) != 2:
        blockers.append("selected_vertical_must_have_two_legs")
        return
    if sorted(row.get("side") for row in selected["legs"]) != ["buy", "sell"]:
        blockers.append("selected_vertical_must_have_one_buy_one_sell_leg")
    for leg in selected["legs"]:
        for field in [
            "entry_bid",
            "entry_ask",
            "entry_mid",
            "forced_close_bid",
            "forced_close_ask",
            "forced_close_mid",
            "strike",
        ]:
            if leg.get(field) is None:
                blockers.append(f"leg_missing_{field}")


def _validate_pnl(summary: dict[str, Any], blockers: list[str]) -> None:
    pnl = summary.get("pnl")
    if not isinstance(pnl, dict):
        blockers.append("pnl_required")
        return
    for field in [
        "entry_mid_debit",
        "forced_close_mid_value",
        "mid_pnl",
        "entry_implementable_debit",
        "forced_close_implementable_credit",
        "gross_implementable_pnl_before_fees",
        "total_fees",
        "implementable_pnl",
        "cost_drag_vs_mid",
    ]:
        if pnl.get(field) is None:
            blockers.append(f"pnl_missing_{field}")
    if _round6(pnl.get("fee_per_leg_usd")) != 0.64:
        blockers.append("fee_per_leg_must_be_0_64")
    if pnl.get("fee_leg_count") != 4:
        blockers.append("fee_leg_count_must_be_4")
    if _round6(pnl.get("total_fees")) != 2.56:
        blockers.append("total_fees_must_be_2_56")


def _validate_guardrails(summary: dict[str, Any], blockers: list[str]) -> None:
    for field in [
        "network_used",
        "paid_data_used",
        "additional_download_used",
        "new_provider_used",
        "broker_request_used",
        "ibkr_request_used",
        "gdelt_live_retry_used",
        "llm_call_used",
        "paper_trading_allowed",
        "operational_validation_allowed",
        "real_money_allowed",
        "strategy_use_allowed",
    ]:
        if summary.get(field) is not False:
            blockers.append(f"{field}_must_be_false")
    if summary.get("exact_replay_used") is not True:
        blockers.append("exact_replay_used_must_be_true")
    if summary.get("strategy_pnl_computed") is not True:
        blockers.append("strategy_pnl_computed_must_be_true")
    sample = summary.get("sample_policy", {})
    if sample.get("sample_count") != 1:
        blockers.append("sample_count_must_be_1")
    if sample.get("under_sampled") is not True:
        blockers.append("under_sampled_must_be_true")
    if sample.get("underpowered") is not True:
        blockers.append("underpowered_must_be_true")
    if summary.get("blockers") != []:
        blockers.append("runtime_blockers_must_be_empty")


def _validate_outputs(summary: dict[str, Any], blockers: list[str]) -> None:
    if summary.get("research_log_required") is not True:
        blockers.append("research_log_required_must_be_true")
    if summary.get("research_log_slug") != "higanbana-h-a2-post-stress-normalization-control-exact-replay":
        blockers.append("research_log_slug_must_match")
    search_log = summary.get("trial_policy", {}).get("search_log")
    if not search_log or not (PROJECT_ROOT / search_log).exists():
        blockers.append("search_log_missing")
    if not (PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_post_stress_normalization_control_exact_replay.md").exists():
        blockers.append("markdown_report_missing")
    forbidden = "\n".join(summary.get("forbidden_claims", []))
    for phrase in ["edge is validated", "E2", "paper trading", "2025-05-05", "0.001"]:
        if phrase not in forbidden:
            blockers.append(f"missing_forbidden_claim_phrase:{phrase}")


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate H-A2 post-stress normalization/control exact replay summary."
    )
    parser.add_argument("--summary-path", type=Path, default=DEFAULT_SUMMARY_PATH)
    args = parser.parse_args(argv)
    result = validate_h_a2_post_stress_normalization_control_exact_replay(args.summary_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
