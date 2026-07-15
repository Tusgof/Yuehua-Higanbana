from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.environment import wiki_root
from lib.io import load_json, relative_to_root


DEFAULT_PATH = PROJECT_ROOT / "experiments" / "h_a2_orb_0936_preregistration.json"


def validate(path: Path = DEFAULT_PATH, *, verify_wiki: bool = True) -> dict[str, Any]:
    payload = load_json(path)
    blockers: list[str] = []
    expected_root = {
        "schema_version": "h_a2_orb_0936_preregistration_v1",
        "artifact_type": "preregistration",
        "status": "preregistered_design_only",
        "hypothesis_id": "H-A2",
        "experiment_id": "h_a2_orb_0936_validation",
        "evidence_tier": "E0",
        "research_question": "ภายใต้ prior-close VIX <25 และไม่มีข่าวมหภาคสำคัญ กลยุทธ์ SPY 0DTE ORB ที่ยืนยันสัญญาณเมื่อแท่งเวลา 09:35 ปิด และเข้าออปชันตั้งแต่ 09:36 สามารถสร้างผลตอบแทนเฉลี่ยหลังต้นทุนเป็นบวกบนข้อมูล OOS ที่ไม่เคยเปิดดูได้หรือไม่",
    }
    for field, expected in expected_root.items():
        if payload.get(field) != expected:
            blockers.append(f"{field}_must_equal_{expected}")

    chronological = payload.get("chronological_policy", {})
    for field, expected in {
        "development_outcomes_cutoff": "2026-04-24",
        "validation_dates_must_be_after": "2026-04-24",
        "random_split_allowed": False,
        "rolling_or_expanding_split_only": True,
        "oos_tuning_allowed": False,
        "viewed_checkpoint_dates_allowed_as_fresh_oos": False,
    }.items():
        if chronological.get(field) != expected:
            blockers.append(f"chronological_policy_invalid:{field}")

    signal = payload.get("signal_rule", {})
    for field, expected in {
        "bar_timestamp_semantics": "interval_start",
        "confirmation_bar_timestamp_et": "09:35:00",
        "signal_available_time_et": "09:36:00",
        "order_decision_time_et": "09:36:00",
        "numeric_breakout_threshold": None,
        "post_signal_feature_allowed": False,
    }.items():
        if signal.get(field) != expected:
            blockers.append(f"signal_rule_invalid:{field}")
    if signal.get("opening_range_bar_timestamps_et") != [
        "09:30:00", "09:31:00", "09:32:00", "09:33:00", "09:34:00"
    ]:
        blockers.append("opening_range_must_be_five_interval_start_bars")

    execution = payload.get("execution_rule", {})
    for field, expected in {
        "entry_order_type": "marketable_debit_limit",
        "entry_market_order_allowed": False,
        "execution_latency_seconds": 60,
        "earliest_entry_quote_time_et": "09:37:00",
        "missing_or_incomplete_entry_quote": "skip trade",
        "forced_close_time_et": "15:45:00",
        "additional_slippage_beyond_displayed_bid_ask": 0.0,
        "fee_per_leg_usd": 0.64,
        "fee_leg_count": 4,
    }.items():
        if execution.get(field) != expected:
            blockers.append(f"execution_rule_invalid:{field}")

    structure = payload.get("structure_rule", {})
    for field, expected in {
        "target_long_strike_gap_points": 1.48,
        "target_width_points": 2.0,
        "strike_mapping": "nearest_discrete_strike_rounding",
        "interpolation_allowed": False,
    }.items():
        if structure.get(field) != expected:
            blockers.append(f"structure_rule_invalid:{field}")

    timestamp_guardrail = payload.get("timestamp_guardrail", {})
    if timestamp_guardrail.get("required_order") != [
        "signal_available_timestamp <= order_decision_timestamp",
        "order_decision_timestamp <= entry_quote_timestamp",
    ]:
        blockers.append("timestamp_order_must_be_locked")
    if "Stop before" not in str(timestamp_guardrail.get("failure_action", "")):
        blockers.append("timestamp_failure_must_stop_before_pnl")

    sample_policy = payload.get("sample_adequacy_policy", {})
    if sample_policy.get("exact_mintrl_known_before_valid_returns") is not False:
        blockers.append("exact_mintrl_must_remain_unknown_before_valid_returns")
    if sample_policy.get("automatic_expansion_allowed") is not False:
        blockers.append("automatic_expansion_must_be_forbidden")

    multiple_testing = payload.get("multiple_testing_policy", {})
    if multiple_testing.get("minimum_trials_recorded_for_dsr") != 10:
        blockers.append("dsr_must_record_at_least_ten_trials")
    for field in ("parameter_search_allowed", "threshold_search_allowed", "selecting_the_best_latency_allowed"):
        if multiple_testing.get(field) is not False:
            blockers.append(f"multiple_testing_policy_invalid:{field}")

    guardrails = payload.get("guardrails", {})
    for field in (
        "network_allowed_in_design_session",
        "paid_data_allowed_in_design_session",
        "experiment_run_allowed_in_design_session",
        "target_outcome_parse_allowed_in_design_session",
        "llm_call_allowed",
        "broker_order_allowed",
        "paper_trading_allowed",
        "operational_validation_allowed",
        "real_money_allowed",
        "e2_claim_allowed",
    ):
        if guardrails.get(field) is not False:
            blockers.append(f"guardrail_must_be_false:{field}")

    for source in payload.get("source_artifacts", []):
        if not (PROJECT_ROOT / source).exists():
            blockers.append(f"source_artifact_missing:{source}")
    if verify_wiki:
        for citation in payload.get("wiki_citations", []):
            citation_path = wiki_root() / citation["path"]
            if not citation_path.exists():
                blockers.append(f"wiki_citation_missing:{citation['path']}")
                continue
            if hashlib.sha256(citation_path.read_bytes()).hexdigest() != citation.get("sha256"):
                blockers.append(f"wiki_citation_hash_mismatch:{citation['path']}")

    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "path": relative_to_root(path, PROJECT_ROOT),
        "signal_available_time_et": signal.get("signal_available_time_et"),
        "earliest_entry_quote_time_et": execution.get("earliest_entry_quote_time_et"),
        "execution_latency_seconds": execution.get("execution_latency_seconds"),
        "minimum_trials_recorded_for_dsr": multiple_testing.get("minimum_trials_recorded_for_dsr"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the H-A2 09:36 ORB preregistration.")
    parser.add_argument("--path", type=Path, default=DEFAULT_PATH)
    args = parser.parse_args(argv)
    result = validate(args.path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
