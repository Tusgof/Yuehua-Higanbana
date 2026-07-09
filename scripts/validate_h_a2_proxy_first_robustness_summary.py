from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUMMARY_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_proxy_first_robustness_summary.json"


def validate(path: Path = DEFAULT_SUMMARY_PATH) -> dict[str, Any]:
    summary = json.loads(path.read_text(encoding="utf-8"))
    errors: list[str] = []

    _expect(summary.get("record_type") == "experiment_summary", "record_type must be experiment_summary", errors)
    _expect(summary.get("schema_version") == "h_a2_proxy_first_robustness_v1", "unexpected schema_version", errors)
    _expect(summary.get("experiment_id") == "h_a2_proxy_first_robustness", "unexpected experiment_id", errors)
    _expect(summary.get("hypothesis_id") == "H-A2", "unexpected hypothesis_id", errors)
    _expect(summary.get("evidence_tier") == "E1", "evidence_tier must be E1", errors)
    _expect(summary.get("status") == "complete", "status must be complete", errors)
    _expect(summary.get("research_log_required") is True, "research_log_required must be true", errors)

    for key in [
        "network_used",
        "paid_data_used",
        "new_provider_used",
        "ibkr_request_used",
        "llm_call_used",
        "paper_trading_allowed",
        "operational_validation_allowed",
        "real_money_allowed",
        "exact_2022_orb_tested",
        "strategy_use_allowed",
    ]:
        _expect(summary.get(key) is False, f"{key} must be false", errors)

    trial_policy = summary.get("trial_policy") or {}
    search_log = PROJECT_ROOT / str(trial_policy.get("search_log", ""))
    _expect(trial_policy.get("trial_count") == 4, "trial_count must be 4", errors)
    _expect(trial_policy.get("all_trials_recorded") is True, "all_trials_recorded must be true", errors)
    _expect(search_log.exists(), "search_log must exist", errors)
    if search_log.exists():
        row_count = len([line for line in search_log.read_text(encoding="utf-8").splitlines() if line.strip()])
        _expect(row_count == trial_policy.get("trial_count"), "search_log row count must match trial_count", errors)

    _expect(isinstance(summary.get("tier_blockers"), list) and summary["tier_blockers"], "tier_blockers required", errors)
    _expect(summary.get("sample_policy", {}).get("under_sampled") is True, "under_sampled must be true", errors)
    _expect(summary.get("sample_policy", {}).get("underpowered") is True, "underpowered must be true", errors)
    _expect(isinstance(summary.get("resolution_monotonicity_check", {}).get("directionally_consistent"), bool), "directionally_consistent bool required", errors)

    groups = summary.get("macro_vix_separation_check", {}).get("groups", {})
    for bucket in ["macro_only", "vix_risk_only", "macro_plus_vix_risk", "no_macro_no_vix_risk"]:
        _expect(bucket in groups, f"missing bucket {bucket}", errors)
        if bucket in groups:
            _expect("sample_count" in groups[bucket], f"{bucket} sample_count required", errors)

    return {"status": "pass" if not errors else "fail", "errors": errors, "summary": str(path)}


def _expect(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


if __name__ == "__main__":
    result = validate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] != "pass":
        sys.exit(1)
