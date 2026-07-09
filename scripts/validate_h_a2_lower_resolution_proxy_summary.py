from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUMMARY_PATH = PROJECT_ROOT / "reports" / "experiments" / "h_a2_lower_resolution_proxy_summary.json"


def validate_h_a2_lower_resolution_proxy_summary(summary_path: Path = DEFAULT_SUMMARY_PATH) -> dict[str, Any]:
    summary = _load_json(summary_path)
    blockers: list[str] = []

    if summary.get("schema_version") != "h_a2_lower_resolution_proxy_v1":
        blockers.append("unsupported_schema_version")
    if summary.get("experiment_id") != "h_a2_lower_resolution_proxy":
        blockers.append("experiment_id_must_match")
    if summary.get("hypothesis_id") != "H-A2":
        blockers.append("hypothesis_id_must_be_h_a2")
    if summary.get("evidence_tier") != "E1":
        blockers.append("evidence_tier_must_be_e1")
    if summary.get("status") != "complete":
        blockers.append("status_must_be_complete")
    if summary.get("research_log_required") is not True:
        blockers.append("research_log_required_must_be_true")

    for field in [
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
        if summary.get(field) is not False:
            blockers.append(f"{field}_must_be_false")

    trial_policy = summary.get("trial_policy", {})
    search_log = trial_policy.get("search_log")
    if trial_policy.get("trial_count") != 7:
        blockers.append("trial_count_must_be_7")
    if trial_policy.get("all_trials_recorded") is not True:
        blockers.append("all_trials_recorded_must_be_true")
    if not search_log or not (PROJECT_ROOT / search_log).exists():
        blockers.append("search_log_missing")
    else:
        rows = [json.loads(line) for line in (PROJECT_ROOT / search_log).read_text(encoding="utf-8").splitlines() if line.strip()]
        if len(rows) != trial_policy.get("trial_count"):
            blockers.append("search_log_row_count_mismatch")

    for key in ["proxy_5m", "proxy_15m"]:
        proxy = summary.get(key, {})
        if proxy.get("measured_day_count", 0) <= 0:
            blockers.append(f"{key}_must_measure_days")
        for regime in ["combined_risk", "non_risk"]:
            if regime not in proxy.get("by_regime", {}):
                blockers.append(f"{key}_missing_regime:{regime}")

    trade = summary.get("existing_trade_reconciliation", {})
    if trade.get("all", {}).get("trade_day_count", 0) <= 0:
        blockers.append("existing_trade_reconciliation_must_have_trade_days")
    if "combined_risk" not in trade or "non_risk" not in trade:
        blockers.append("existing_trade_reconciliation_missing_required_groups")

    coherence = summary.get("coherence_assessment", {})
    for field in ["proxy_supports_non_risk", "existing_trades_support_non_risk", "directionally_coherent"]:
        if not isinstance(coherence.get(field), bool):
            blockers.append(f"coherence_field_must_be_bool:{field}")

    required_blockers = [
        "E1 lower-resolution proxy only",
        "No exact 2022-10 ORB entries/exits tested",
        "No E2 acceptance claim",
        "No paper trading, operational validation, or real-money approval",
    ]
    tier_blockers = "\n".join(summary.get("tier_blockers", []))
    for phrase in required_blockers:
        if phrase not in tier_blockers:
            blockers.append(f"missing_tier_blocker:{phrase}")

    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "summary_path": _relative(summary_path),
        "hypothesis_id": summary.get("hypothesis_id"),
        "evidence_tier": summary.get("evidence_tier"),
        "conclusion": summary.get("conclusion"),
        "trial_count": trial_policy.get("trial_count"),
        "daily_row_count": summary.get("daily_row_count"),
        "paper_trading_allowed": summary.get("paper_trading_allowed"),
    }


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate H-A2 lower-resolution proxy summary.")
    parser.add_argument("--summary-path", type=Path, default=DEFAULT_SUMMARY_PATH)
    args = parser.parse_args(argv)

    result = validate_h_a2_lower_resolution_proxy_summary(args.summary_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
