from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUMMARY_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_locked_condition_signal_attribution_summary.json"


def validate_h_a2_locked_condition_signal_attribution(summary_path: Path = DEFAULT_SUMMARY_PATH) -> dict[str, Any]:
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    blockers: list[str] = []

    if summary.get("schema_version") != "h_a2_locked_condition_signal_attribution_v1":
        blockers.append("unsupported_schema_version")
    if summary.get("status") != "complete":
        blockers.append("status_must_be_complete")
    if summary.get("experiment_id") != "h_a2_locked_condition_signal_attribution":
        blockers.append("experiment_id_must_match")
    if summary.get("hypothesis_id") != "H-A2":
        blockers.append("hypothesis_id_must_be_h_a2")
    if summary.get("evidence_tier") != "E1":
        blockers.append("evidence_tier_must_be_e1")
    if summary.get("conclusion") != "ยังสรุปไม่ได้":
        blockers.append("conclusion_must_be_inconclusive")
    if summary.get("locked_threshold") != 0.001:
        blockers.append("locked_threshold_must_be_0_001")

    classification = summary.get("entry_rule_classification", {})
    if classification.get("deployable_entry_filter_allowed") is not False:
        blockers.append("deployable_entry_filter_must_be_false")
    if classification.get("delayed_entry_candidate_allowed") is not True:
        blockers.append("delayed_entry_candidate_must_be_true")
    if classification.get("diagnostic_proxy_only") is not True:
        blockers.append("diagnostic_proxy_only_must_be_true")

    timestamp_audit = summary.get("decision_timestamp_availability_audit", {})
    windows = timestamp_audit.get("feature_measurement_windows", [])
    if not any(item.get("known_by_decision_time") is False for item in windows):
        blockers.append("must_have_post_decision_feature_component")

    trial = summary.get("trial_policy", {})
    for field in ["threshold_search_used", "new_filter_search_used", "oos_tuning_used"]:
        if trial.get(field) is not False:
            blockers.append(f"{field}_must_be_false")

    sample = summary.get("sample_policy", {})
    if sample.get("under_sampled") is not True:
        blockers.append("under_sampled_must_be_true")
    if sample.get("underpowered") is not True:
        blockers.append("underpowered_must_be_true")

    false_fields = [
        "network_used",
        "paid_data_used",
        "new_provider_used",
        "broker_request_used",
        "ibkr_request_used",
        "gdelt_live_retry_used",
        "llm_call_used",
        "exact_2022_orb_tested",
        "paper_trading_allowed",
        "operational_validation_allowed",
        "real_money_allowed",
        "strategy_use_allowed",
    ]
    for field in false_fields:
        if summary.get(field) is not False:
            blockers.append(f"{field}_must_be_false")
    if summary.get("research_log_required") is not True:
        blockers.append("research_log_required_must_be_true")

    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "summary_path": _relative(summary_path),
        "classification": classification.get("classification"),
        "locked_threshold": summary.get("locked_threshold"),
        "evidence_tier": summary.get("evidence_tier"),
        "conclusion": summary.get("conclusion"),
    }


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate H-A2 locked-condition signal-attribution summary.")
    parser.add_argument("--summary-path", type=Path, default=DEFAULT_SUMMARY_PATH)
    args = parser.parse_args(argv)
    result = validate_h_a2_locked_condition_signal_attribution(args.summary_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
