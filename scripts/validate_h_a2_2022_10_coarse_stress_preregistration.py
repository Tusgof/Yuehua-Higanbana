from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PREREG_PATH = PROJECT_ROOT / "experiments" / "h_a2_2022_10_coarse_stress_review_preregistration.json"


def validate_h_a2_2022_10_coarse_stress_preregistration(prereg_path: Path = DEFAULT_PREREG_PATH) -> dict[str, Any]:
    prereg = _load_json(prereg_path)
    blockers: list[str] = []

    if prereg.get("schema_version") != "h_a2_2022_10_coarse_stress_review_preregistration_v1":
        blockers.append("unsupported_schema_version")
    if prereg.get("hypothesis_id") != "H-A2":
        blockers.append("hypothesis_id_must_be_h_a2")
    if prereg.get("status") != "preregistered":
        blockers.append("status_must_be_preregistered")
    if prereg.get("evidence_tier") != "E0":
        blockers.append("evidence_tier_must_be_e0")

    method = prereg.get("method", {})
    window = method.get("window", {})
    if window.get("start") != "2022-10-03" or window.get("end") != "2022-10-31":
        blockers.append("window_must_be_2022_10_trading_month")
    if method.get("unit") != "trading_day":
        blockers.append("unit_must_be_trading_day")
    thresholds = method.get("volatility_thresholds", {})
    if thresholds.get("high_vix") != 25.0:
        blockers.append("high_vix_threshold_must_be_25")
    if thresholds.get("stress_vix") != 30.0:
        blockers.append("stress_vix_threshold_must_be_30")

    required_inputs = [
        "data_resolution_audit",
        "option_normalization_summary",
        "vix_vxv",
        "macro_calendar",
        "stress_purchase_estimate",
        "spy_bar_unavailable_report",
    ]
    inputs = prereg.get("input_paths", {})
    for key in required_inputs:
        value = inputs.get(key)
        if not value:
            blockers.append(f"missing_input_path:{key}")
        elif not (PROJECT_ROOT / value).exists():
            blockers.append(f"input_path_does_not_exist:{key}")

    metrics = set(method.get("metrics", []))
    required_metrics = {
        "trading_day_count",
        "0dte_quote_available_day_count",
        "0dte_quote_missing_day_count",
        "same_day_high_vix_day_count",
        "same_day_stress_vix_day_count",
        "prior_close_high_vix_day_count",
        "prior_close_stress_vix_day_count",
        "high_importance_macro_day_count",
        "overlap_between_0dte_quote_availability_and_vix_macro_regimes",
    }
    missing_metrics = sorted(required_metrics - metrics)
    blockers.extend(f"missing_metric:{metric}" for metric in missing_metrics)

    guardrails = prereg.get("guardrails", {})
    false_flags = [
        "network_allowed",
        "paid_data_allowed",
        "new_provider_allowed",
        "ibkr_request_allowed",
        "llm_call_allowed",
        "strategy_pnl_allowed",
        "paper_trading_allowed",
        "real_money_allowed",
        "research_log_required_for_this_preregistration",
    ]
    for field in false_flags:
        if guardrails.get(field) is not False:
            blockers.append(f"{field}_must_be_false")

    forbidden = "\n".join(prereg.get("decision_frame", {}).get("forbidden_claims", []))
    for phrase in ["H-A2 edge is validated", "exact ORB entries/exits", "paper trading", "real-money trading"]:
        if phrase not in forbidden:
            blockers.append(f"missing_forbidden_claim:{phrase}")

    outputs = prereg.get("planned_outputs", {})
    for key in ["summary_json", "summary_md", "next_research_log_if_diagnostic_runs"]:
        if not outputs.get(key):
            blockers.append(f"missing_planned_output:{key}")

    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "prereg_path": _relative(prereg_path),
        "hypothesis_id": prereg.get("hypothesis_id"),
        "evidence_tier": prereg.get("evidence_tier"),
        "window": window,
        "planned_summary_json": outputs.get("summary_json"),
        "research_log_required_for_this_preregistration": guardrails.get("research_log_required_for_this_preregistration"),
    }


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate H-A2 2022-10 coarse stress review preregistration.")
    parser.add_argument("--prereg-path", type=Path, default=DEFAULT_PREREG_PATH)
    args = parser.parse_args(argv)

    result = validate_h_a2_2022_10_coarse_stress_preregistration(args.prereg_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
