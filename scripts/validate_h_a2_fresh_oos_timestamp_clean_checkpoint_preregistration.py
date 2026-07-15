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
from lib.io import load_json


DEFAULT_PATH = PROJECT_ROOT / "experiments" / "h_a2_fresh_oos_timestamp_clean_checkpoint_preregistration.json"


def validate(path: Path = DEFAULT_PATH, *, verify_wiki: bool = True) -> dict[str, Any]:
    payload = load_json(path)
    blockers: list[str] = []
    if payload.get("schema_version") != "h_a2_fresh_oos_timestamp_clean_checkpoint_preregistration_v1":
        blockers.append("unsupported_schema_version")
    for field, expected in {
        "artifact_type": "preregistration",
        "status": "preregistered",
        "hypothesis_id": "H-A2",
        "experiment_id": "h_a2_fresh_oos_timestamp_clean_checkpoint",
        "evidence_tier": "E0",
    }.items():
        if payload.get(field) != expected:
            blockers.append(f"{field}_must_equal_{expected}")

    dates = [date_text for values in payload.get("target_dates", {}).values() for date_text in values]
    if len(dates) != 20 or len(set(dates)) != 20:
        blockers.append("target_dates_must_contain_20_unique_dates")
    if set(payload.get("provider_quality_warning_dates", [])) - set(dates):
        blockers.append("quality_warning_dates_must_be_in_target_dates")

    correction = payload.get("lookahead_correction", {})
    if correction.get("fresh_outcomes_viewed_before_correction") is not False:
        blockers.append("fresh_outcomes_must_be_unviewed_before_correction")
    if correction.get("affected_feature") != "proxy_5m.directional_followthrough_to_close_pct":
        blockers.append("affected_lookahead_feature_must_be_explicit")

    rule = payload.get("candidate_rule", {})
    for field, expected in {
        "decision_time_et": "09:35:00",
        "decision_bar_et": "09:35:00",
        "numeric_breakout_threshold": None,
        "post_decision_feature_allowed": False,
    }.items():
        if rule.get(field) != expected:
            blockers.append(f"candidate_rule_invalid:{field}")
    if "09:30:00" not in str(rule.get("opening_range_et")) or "09:35:00" not in str(rule.get("opening_range_et")):
        blockers.append("opening_range_must_be_explicit")

    replay = payload.get("option_replay_rule", {})
    expected_replay = {
        "entry_time_et": "09:35:00",
        "forced_close_time_et": "15:45:00",
        "target_gap_points": 1.48,
        "width_points": 2.0,
        "strike_mapping": "nearest_discrete_strike_rounding",
        "interpolation_allowed": False,
        "fee_per_leg_usd": 0.64,
        "fee_leg_count": 4,
    }
    for field, expected in expected_replay.items():
        if replay.get(field) != expected:
            blockers.append(f"option_replay_rule_invalid:{field}")

    if payload.get("trial_policy", {}).get("trial_count") != 1:
        blockers.append("trial_count_must_be_one")
    for field in ("parameter_search_used", "threshold_search_used", "oos_tuning_used"):
        if payload.get("trial_policy", {}).get(field) is not False:
            blockers.append(f"{field}_must_be_false")

    guardrails = payload.get("guardrails", {})
    for field in (
        "network_allowed",
        "additional_paid_data_allowed",
        "new_provider_allowed",
        "ibkr_request_allowed",
        "llm_call_allowed",
        "gdelt_retry_allowed",
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
            actual = hashlib.sha256(citation_path.read_bytes()).hexdigest()
            if actual != citation.get("sha256"):
                blockers.append(f"wiki_citation_hash_mismatch:{citation['path']}")

    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "path": str(path),
        "target_date_count": len(dates),
        "lookahead_correction_locked": not any("lookahead" in blocker for blocker in blockers),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the timestamp-clean H-A2 fresh OOS checkpoint preregistration.")
    parser.add_argument("--path", type=Path, default=DEFAULT_PATH)
    args = parser.parse_args(argv)
    result = validate(args.path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
