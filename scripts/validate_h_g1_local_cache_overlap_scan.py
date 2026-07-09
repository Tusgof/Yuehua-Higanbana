from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCAN_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_g1_local_cache_overlap_scan.json"


def validate_h_g1_local_cache_overlap_scan(scan_path: Path = DEFAULT_SCAN_PATH) -> dict[str, Any]:
    blockers: list[str] = []
    scan = _load_json(scan_path)

    if scan.get("schema_version") != "h_g1_local_cache_overlap_scan_v1":
        blockers.append("unsupported_schema_version")
    if scan.get("hypothesis_id") != "H-G1":
        blockers.append("hypothesis_id_must_be_h_g1")
    if scan.get("evidence_tier") != "E0":
        blockers.append("evidence_tier_must_be_e0")
    if scan.get("status") not in {"blocked_no_additional_no_paid_overlap", "complete_no_paid_scan"}:
        blockers.append("invalid_status")

    false_flags = [
        "network_used",
        "paid_data_used",
        "new_data_requested",
        "strategy_pnl_used",
        "strategy_use_allowed",
        "paper_trading_allowed",
        "paid_data_approved",
        "true_net_gamma_claim_allowed",
        "research_log_required",
    ]
    for field in false_flags:
        if scan.get(field) is not False:
            blockers.append(f"{field}_must_be_false")

    counts = scan.get("local_cache_counts", {})
    if counts.get("baseline_closed_trade_dates") != 90:
        blockers.append("baseline_closed_trade_dates_must_match_current_baseline")
    if counts.get("current_baseline_gamma_intersection") != 2:
        blockers.append("current_baseline_gamma_intersection_must_remain_2")
    if counts.get("projected_no_paid_gamma_ready_intersection", 0) < counts.get("current_baseline_gamma_intersection", 0):
        blockers.append("projected_intersection_cannot_be_less_than_current")

    current_dates = scan.get("current_covered_trade_dates", [])
    if sorted(current_dates) != ["2023-10-27", "2024-12-18"]:
        blockers.append("current_covered_trade_dates_must_match_h_g1_22")

    mintrl_gate = scan.get("mintrl_psr_feasibility_gate", {})
    if mintrl_gate.get("fixed_n_rule_used") is not False:
        blockers.append("fixed_n_rule_must_not_be_used")
    if "MinTRL" not in mintrl_gate.get("reason", "") or "PSR" not in mintrl_gate.get("reason", ""):
        blockers.append("mintrl_psr_reason_missing")

    regime_counts = scan.get("regime_counts", {})
    for key in ["current_intersection", "additional_no_paid_candidates", "projected_no_paid_candidates", "quote_bar_cached_but_missing_oi"]:
        value = regime_counts.get(key)
        if not isinstance(value, dict):
            blockers.append(f"missing_regime_counts:{key}")
            continue
        for subkey in ["by_split", "by_macro_flag", "by_volatility_bucket"]:
            if subkey not in value:
                blockers.append(f"missing_regime_counts:{key}:{subkey}")

    next_action = scan.get("next_safe_action", "")
    if "H-G1 parked" not in next_action and "MinTRL/PSR feasibility gate" not in next_action:
        blockers.append("next_safe_action_must_preserve_h_g1_guardrails")

    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "scan_path": _relative(scan_path),
        "scan_status": scan.get("status"),
        "additional_no_paid_gamma_ready_dates": counts.get("additional_no_paid_gamma_ready_dates"),
        "projected_no_paid_gamma_ready_intersection": counts.get("projected_no_paid_gamma_ready_intersection"),
        "strategy_use_allowed": scan.get("strategy_use_allowed"),
        "paid_data_approved": scan.get("paid_data_approved"),
    }


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the H-G1 no-paid local-cache overlap scan.")
    parser.add_argument("--scan-path", type=Path, default=DEFAULT_SCAN_PATH)
    args = parser.parse_args(argv)

    result = validate_h_g1_local_cache_overlap_scan(args.scan_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
