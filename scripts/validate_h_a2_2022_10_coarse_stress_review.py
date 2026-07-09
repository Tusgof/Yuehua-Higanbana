from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_PATH = PROJECT_ROOT / "reports" / "diagnostics" / "h_a2_2022_10_coarse_stress_review.json"


def validate_h_a2_2022_10_coarse_stress_review(report_path: Path = DEFAULT_REPORT_PATH) -> dict[str, Any]:
    blockers: list[str] = []
    report = _load_json(report_path)

    if report.get("schema_version") != "h_a2_2022_10_coarse_stress_review_v1":
        blockers.append("unsupported_schema_version")
    if report.get("hypothesis_id") != "H-A2":
        blockers.append("hypothesis_id_must_be_h_a2")
    if report.get("evidence_tier") != "E1":
        blockers.append("evidence_tier_must_be_e1")
    if report.get("status") not in {"continue_exact_rerun_research", "deprioritize_exact_rerun_research", "blocked_input_missing"}:
        blockers.append("invalid_status")
    if report.get("conclusion") != "ยังสรุปไม่ได้":
        blockers.append("conclusion_must_remain_inconclusive")

    false_flags = [
        "network_used",
        "paid_data_used",
        "new_data_requested",
        "ibkr_request_used",
        "llm_call_used",
        "strategy_pnl_used",
        "strategy_use_allowed",
        "paper_trading_allowed",
        "operational_validation_allowed",
        "real_money_allowed",
        "exact_orb_tested",
        "exact_rerun_approved",
    ]
    for field in false_flags:
        if report.get(field) is not False:
            blockers.append(f"{field}_must_be_false")

    if report.get("research_log_required") is not True:
        blockers.append("research_log_required_must_be_true")
    if report.get("research_log_slug") != "higanbana-h-a2-2022-10-coarse-stress-review":
        blockers.append("research_log_slug_mismatch")

    counts = report.get("counts", {})
    if counts.get("trading_day_count") != 21:
        blockers.append("trading_day_count_must_be_21")
    quote_available = counts.get("0dte_quote_available_day_count")
    quote_missing = counts.get("0dte_quote_missing_day_count")
    if quote_available is None or quote_missing is None or quote_available + quote_missing != counts.get("trading_day_count"):
        blockers.append("quote_counts_must_sum_to_trading_days")
    if counts.get("quote_available_and_any_high_or_stress_vix_count", 0) <= 0:
        blockers.append("must_have_quote_available_vix_overlap")

    rule = report.get("decision_rule_evaluation", {})
    if rule.get("fixed_n_rule_used") is not False:
        blockers.append("fixed_n_rule_must_not_be_used")

    days = report.get("trading_days", [])
    if len(days) != counts.get("trading_day_count"):
        blockers.append("trading_days_length_must_match_count")
    for day in days:
        if not isinstance(day.get("date"), str):
            blockers.append("trading_day_missing_date")
        if "same_day_vix_close" not in day or "prior_close_vix" not in day:
            blockers.append("trading_day_missing_vix_fields")
        if "high_importance_macro_events" not in day:
            blockers.append("trading_day_missing_macro_events")

    blockers_text = " ".join(report.get("tier_blockers", []))
    for required in ["SPY 1-minute bars", "strategy PnL", "paper trading"]:
        if required not in blockers_text:
            blockers.append(f"tier_blockers_missing:{required}")

    return {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "report_path": _relative(report_path),
        "report_status": report.get("status"),
        "evidence_tier": report.get("evidence_tier"),
        "trading_day_count": counts.get("trading_day_count"),
        "quote_available_day_count": counts.get("0dte_quote_available_day_count"),
        "quote_available_vix_overlap_count": counts.get("quote_available_and_any_high_or_stress_vix_count"),
        "paper_trading_allowed": report.get("paper_trading_allowed"),
    }


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the H-A2 no-paid 2022-10 coarse stress/regime review.")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT_PATH)
    args = parser.parse_args(argv)
    result = validate_h_a2_2022_10_coarse_stress_review(args.report_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
